import rclpy
from rclpy.node import Node
import hashlib
from fleex_msgs.msg import Task, TaskBid

class TaskBidder(Node):
    def __init__(self):
        super().__init__('fleex_task_bidder')

        # Declare parameters
        self.declare_parameter('robot_id', 'amr_1')
        self.declare_parameter('bid_collection_window', 1.0)
        
        self.robot_id = self.get_parameter('robot_id').value
        self.bid_collection_window = self.get_parameter('bid_collection_window').value

        # Publishers and Subscribers
        self.task_sub = self.create_subscription(Task, '/fleex/tasks', self.task_callback, 10)
        self.task_pub = self.create_publisher(Task, '/fleex/tasks', 10)
        
        self.bid_sub = self.create_subscription(TaskBid, '/fleex/task_bids', self.bid_callback, 10)
        self.bid_pub = self.create_publisher(TaskBid, '/fleex/task_bids', 10)

        # Internal state tracking
        self.processed_tasks = set()
        self.completed_auctions = {}  # { task_id: winner_id }
        
        # Track known task states logically
        self.local_tasks = {} # { task_id: { 'state': int, 'msg': Task, 'timer': Timer } }
        
        # Structure: { task_id: { 'bids': { robot_id: bid_value }, 'timer': Timer, 'msg': Task } }
        self.active_auctions = {}

        self.get_logger().info(f'Task Bidder initialized for robot: {self.robot_id}')
        self.get_logger().info(f'Auction window set to: {self.bid_collection_window}s')

    def task_callback(self, msg):
        # ----------------------------------------------------
        # TASK LIFECYCLE & OWNERSHIP VALIDATION (PHASE 7.4)
        # ----------------------------------------------------
        if msg.state in [Task.STATE_ASSIGNED, Task.STATE_IN_PROGRESS, Task.STATE_COMPLETED, Task.STATE_FAILED]:
            
            # Idempotency & State Machine rules
            if msg.task_id in self.local_tasks:
                current_state = self.local_tasks[msg.task_id]['state']
                
                if msg.state == current_state:
                    return # Idempotent receipt, ignore
                    
                # Validate state transition rules (No backward transitions allowed)
                # Exception: FAILED is an end state, but numerically it is 4.
                if msg.state < current_state:
                    self.get_logger().warn(f"[{msg.task_id}] Rejecting invalid backward transition: {current_state} -> {msg.state}.")
                    return
                
                if current_state in [Task.STATE_COMPLETED, Task.STATE_FAILED]:
                    self.get_logger().warn(f"[{msg.task_id}] Rejecting mutation on terminal state: {current_state} -> {msg.state}.")
                    return

            # Auction Validation Check
            if msg.task_id not in self.completed_auctions:
                self.get_logger().warn(f"[{msg.task_id}] Received ownership/lifecycle commit for unknown auction. Dropping.")
                return
                
            expected_winner = self.completed_auctions[msg.task_id]
            if msg.owner_id != expected_winner:
                self.get_logger().error(f"[{msg.task_id}] INVALID MUTATION! {msg.owner_id} modified task, but {expected_winner} owns it. Rejecting.")
                return
                
            # Valid Transition Accepted
            if msg.task_id not in self.local_tasks:
                self.local_tasks[msg.task_id] = {'state': msg.state, 'msg': msg, 'timer': None}
            else:
                self.local_tasks[msg.task_id]['state'] = msg.state
                self.local_tasks[msg.task_id]['msg'] = msg
                
            if msg.owner_id != self.robot_id:
                state_names = {1: "ASSIGNED", 2: "IN_PROGRESS", 3: "COMPLETED", 4: "FAILED"}
                self.get_logger().info(f"[{msg.task_id}] Observed transition to {state_names.get(msg.state)} by owner {msg.owner_id}.")
            return


        # ----------------------------------------------------
        # UNASSIGNED TASK AUCTION INITIATION
        # ----------------------------------------------------
        # ELIGIBILITY RULE 1 & 2: Task must be unassigned and have no owner
        if msg.state != Task.STATE_UNASSIGNED or msg.owner_id != "":
            return
            
        # Ensure we only process and auction this unique task ID once
        if msg.task_id in self.processed_tasks or msg.task_id in self.active_auctions:
            return

        if not msg.task_id or not msg.pickup_location:
            self.get_logger().warn("Received unassigned task with missing core data.")
            return

        # CALCULATE DETERMINISTIC BID
        stable_string = f"{msg.task_id}_{msg.pickup_location}_{self.robot_id}"
        hash_val = int(hashlib.md5(stable_string.encode()).hexdigest(), 16)
        
        normalized_distance = (hash_val % 100) / 100.0
        normalized_time = ((hash_val >> 8) % 100) / 100.0
        bid_value = float(normalized_distance + normalized_time)

        # Initialize auction tracking
        timer = self.create_timer(
            self.bid_collection_window, 
            lambda tid=msg.task_id: self.auction_timeout(tid)
        )
        self.active_auctions[msg.task_id] = {
            'bids': {self.robot_id: bid_value},
            'timer': timer,
            'msg': msg 
        }
        self.processed_tasks.add(msg.task_id)

        # Publish bid to network
        bid_msg = TaskBid()
        bid_msg.task_id = msg.task_id
        bid_msg.robot_id = self.robot_id
        bid_msg.bid_value = bid_value

        self.bid_pub.publish(bid_msg)
        self.get_logger().info(f"[{msg.task_id}] Auction Opened. Published local bid: {bid_value:.3f}")

    def bid_callback(self, msg):
        if msg.task_id not in self.active_auctions:
            return
            
        auction = self.active_auctions[msg.task_id]
        
        if msg.robot_id in auction['bids']:
            return
            
        auction['bids'][msg.robot_id] = msg.bid_value

    def auction_timeout(self, task_id):
        if task_id not in self.active_auctions:
            return
            
        auction = self.active_auctions.pop(task_id)
        auction['timer'].cancel()
        
        bids = auction['bids']
        if not bids:
            self.get_logger().warn(f"[{task_id}] Auction closed with no bids?!")
            return

        # WINNER SELECTION ALGORITHM
        sorted_bids = sorted(bids.items(), key=lambda item: (item[1], item[0]))
        winner_id, winning_bid = sorted_bids[0]
        self.completed_auctions[task_id] = winner_id

        self.get_logger().info(f"[{task_id}] Auction Closed. Winner determined: {winner_id} with bid {winning_bid:.3f}")

        # ----------------------------------------------------
        # OWNERSHIP MUTATION COMMIT
        # ----------------------------------------------------
        if winner_id == self.robot_id:
            self.get_logger().info(f"[{task_id}] I WON! Mutating state and committing ownership to network.")
            
            task_msg = auction['msg']
            task_msg.owner_id = self.robot_id
            task_msg.state = Task.STATE_ASSIGNED
            
            # Record locally immediately
            self.local_tasks[task_id] = {'state': Task.STATE_ASSIGNED, 'msg': task_msg, 'timer': None}
            self.task_pub.publish(task_msg)
            
            # Kick off simulated execution lifecycle
            timer = self.create_timer(3.0, lambda tid=task_id: self.simulate_in_progress(tid))
            self.local_tasks[task_id]['timer'] = timer
            
    def simulate_in_progress(self, task_id):
        if task_id not in self.local_tasks:
            return
            
        task_data = self.local_tasks[task_id]
        if task_data['timer']:
            task_data['timer'].cancel()
            
        if task_data['state'] != Task.STATE_ASSIGNED:
            return
            
        task_msg = task_data['msg']
        task_msg.state = Task.STATE_IN_PROGRESS
        task_data['state'] = Task.STATE_IN_PROGRESS
        
        self.get_logger().info(f"[{task_id}] Simulated execution: Transitioning to IN_PROGRESS.")
        self.task_pub.publish(task_msg)
        
        # Proceed to completed
        timer = self.create_timer(3.0, lambda tid=task_id: self.simulate_completed(tid))
        task_data['timer'] = timer
        
    def simulate_completed(self, task_id):
        if task_id not in self.local_tasks:
            return
            
        task_data = self.local_tasks[task_id]
        if task_data['timer']:
            task_data['timer'].cancel()
            task_data['timer'] = None
            
        if task_data['state'] != Task.STATE_IN_PROGRESS:
            return
            
        task_msg = task_data['msg']
        task_msg.state = Task.STATE_COMPLETED
        task_data['state'] = Task.STATE_COMPLETED
        
        self.get_logger().info(f"[{task_id}] Simulated execution: Transitioning to COMPLETED.")
        self.task_pub.publish(task_msg)


def main(args=None):
    rclpy.init(args=args)
    node = TaskBidder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()
