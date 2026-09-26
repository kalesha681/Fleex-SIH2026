import rclpy
from rclpy.node import Node
import hashlib
import json
from fleex_msgs.msg import Task, TaskBid
from std_msgs.msg import String

class TaskBidder(Node):
    def __init__(self):
        super().__init__('fleex_task_bidder')

        # Declare parameters
        self.declare_parameter('robot_id', 'amr_1')
        self.declare_parameter('bid_collection_window', 1.0)
        self.declare_parameter('recovery_grace_period', 5.0)
        
        self.robot_id = self.get_parameter('robot_id').value
        self.bid_collection_window = self.get_parameter('bid_collection_window').value
        self.recovery_grace_period = self.get_parameter('recovery_grace_period').value

        # Publishers and Subscribers
        self.task_sub = self.create_subscription(Task, '/fleex/tasks', self.task_callback, 10)
        self.task_pub = self.create_publisher(Task, '/fleex/tasks', 10)
        
        self.bid_sub = self.create_subscription(TaskBid, '/fleex/task_bids', self.bid_callback, 10)
        self.bid_pub = self.create_publisher(TaskBid, '/fleex/task_bids', 10)

        # Peer liveness subscriber
        self.liveness_sub = self.create_subscription(String, '/fleex/peer_liveness', self.liveness_callback, 10)

        # Internal state tracking
        self.processed_tasks = set()
        self.completed_auctions = {}  # { task_id: winner_id }
        
        # Track known task states logically
        self.local_tasks = {} # { task_id: { 'state': int, 'msg': Task, 'timer': Timer, 'recovery_status': str|None } }
        
        # Structure: { task_id: { 'bids': { robot_id: bid_value }, 'timer': Timer, 'msg': Task } }
        self.active_auctions = {}

        # Recovery tracking
        self.peer_liveness = {} # { robot_id: 'ALIVE' | 'TIMED_OUT' }
        self.recovery_timers = {} # { task_id: Timer }

        self.get_logger().info(f'Task Bidder initialized for robot: {self.robot_id}')
        self.get_logger().info(f'Auction window set to: {self.bid_collection_window}s')

    def task_callback(self, msg):
        # ----------------------------------------------------
        # ZOMBIE YIELDING & EPOCH VALIDATION (PHASE 7.6)
        # ----------------------------------------------------
        is_new_task = (msg.task_id not in self.local_tasks)
        if not is_new_task:
            current_task_data = self.local_tasks[msg.task_id]
            current_msg = current_task_data['msg']
            current_state = current_task_data['state']

            if msg.epoch > current_msg.epoch:
                if current_msg.owner_id == self.robot_id:
                    self.get_logger().error(f"[{msg.task_id}] STALE OWNERSHIP DETECTED! Incoming epoch {msg.epoch} > local {current_msg.epoch}. Yielding task to {msg.owner_id}.")
                else:
                    self.get_logger().info(f"[{msg.task_id}] Task recovered by {msg.owner_id} at epoch {msg.epoch}.")
                
                if current_task_data.get('timer'):
                    current_task_data['timer'].cancel()
                    current_task_data['timer'] = None
                if msg.task_id in self.recovery_timers:
                    self.recovery_timers[msg.task_id].cancel()
                    del self.recovery_timers[msg.task_id]
                    
                self.local_tasks[msg.task_id] = {'state': msg.state, 'msg': msg, 'timer': None, 'recovery_status': None}
                return
                
            elif msg.epoch < current_msg.epoch:
                self.get_logger().debug(f"[{msg.task_id}] Ignoring stale message (epoch {msg.epoch} < local {current_msg.epoch}).")
                return

            if msg.state == current_state:
                return # Idempotent receipt

            if msg.state < current_state:
                self.get_logger().warn(f"[{msg.task_id}] Rejecting backward transition: {current_state} -> {msg.state}.")
                return
            
            if current_state in [Task.STATE_COMPLETED, Task.STATE_FAILED]:
                self.get_logger().warn(f"[{msg.task_id}] Rejecting mutation on terminal state.")
                return
        
        # ----------------------------------------------------
        # TASK LIFECYCLE & OWNERSHIP VALIDATION
        # ----------------------------------------------------
        if msg.state in [Task.STATE_ASSIGNED, Task.STATE_IN_PROGRESS, Task.STATE_COMPLETED, Task.STATE_FAILED]:
            auction_key = f"{msg.task_id}_epoch_{msg.epoch}"
            if auction_key in self.completed_auctions:
                expected_winner = self.completed_auctions[auction_key]
                if msg.owner_id != expected_winner:
                    self.get_logger().error(f"[{msg.task_id}] INVALID MUTATION! {msg.owner_id} modified task, but {expected_winner} owns it.")
                    return
            
            self.local_tasks[msg.task_id] = {'state': msg.state, 'msg': msg, 'timer': self.local_tasks.get(msg.task_id, {}).get('timer'), 'recovery_status': None}
            
            if msg.state in [Task.STATE_COMPLETED, Task.STATE_FAILED]:
                if msg.task_id in self.recovery_timers:
                    self.recovery_timers[msg.task_id].cancel()
                    del self.recovery_timers[msg.task_id]
            
            if msg.state in [Task.STATE_ASSIGNED, Task.STATE_IN_PROGRESS]:
                if self.peer_liveness.get(msg.owner_id) == 'TIMED_OUT':
                    if msg.task_id not in self.recovery_timers and self.local_tasks[msg.task_id].get('recovery_status') != 'ELIGIBLE':
                        self.get_logger().warn(f"[{msg.task_id}] Owner {msg.owner_id} already TIMED_OUT. Recovery pending immediately.")
                        self.local_tasks[msg.task_id]['recovery_status'] = 'PENDING'
                        timer = self.create_timer(self.recovery_grace_period, lambda tid=msg.task_id: self.recovery_grace_expired(tid))
                        self.recovery_timers[msg.task_id] = timer

            if msg.owner_id != self.robot_id:
                state_names = {1: "ASSIGNED", 2: "IN_PROGRESS", 3: "COMPLETED", 4: "FAILED"}
                self.get_logger().info(f"[{msg.task_id}] Observed transition to {state_names.get(msg.state)} by owner {msg.owner_id}.")
            return

        # ----------------------------------------------------
        # UNASSIGNED TASK AUCTION INITIATION
        # ----------------------------------------------------
        if msg.state == Task.STATE_UNASSIGNED and msg.owner_id == "":
            self.initiate_auction(msg)

    def initiate_auction(self, msg):
        # ----------------------------------------------------
        # ZOMBIE NODE PROTECTION (PHASE 7.6)
        # ----------------------------------------------------
        if self.peer_liveness.get(self.robot_id, 'ALIVE') == 'TIMED_OUT':
            self.get_logger().warn(f"[{msg.task_id}] I am TIMED_OUT on the network. Blocking auction participation.")
            return

        auction_key = f"{msg.task_id}_epoch_{msg.epoch}"
        if auction_key in self.active_auctions or auction_key in self.completed_auctions:
            return

        if not msg.task_id or not msg.pickup_location:
            self.get_logger().warn("Received task with missing core data.")
            return

        # CALCULATE DETERMINISTIC BID
        stable_string = f"{msg.task_id}_{msg.pickup_location}_{self.robot_id}_{msg.epoch}"
        hash_val = int(hashlib.md5(stable_string.encode()).hexdigest(), 16)
        
        normalized_distance = (hash_val % 100) / 100.0
        normalized_time = ((hash_val >> 8) % 100) / 100.0
        bid_value = float(normalized_distance + normalized_time)

        timer = self.create_timer(
            self.bid_collection_window, 
            lambda ak=auction_key: self.auction_timeout(ak)
        )
        self.active_auctions[auction_key] = {
            'bids': {self.robot_id: bid_value},
            'timer': timer,
            'msg': msg 
        }

        # Publish bid to network
        bid_msg = TaskBid()
        bid_msg.task_id = auction_key
        bid_msg.robot_id = self.robot_id
        bid_msg.bid_value = bid_value

        self.bid_pub.publish(bid_msg)
        is_rec = "Recovery" if msg.owner_id != "" else "New"
        self.get_logger().info(f"[{msg.task_id}] {is_rec} Auction Opened (Epoch {msg.epoch}). Published local bid: {bid_value:.3f}")

    def bid_callback(self, msg):
        if msg.task_id not in self.active_auctions:
            return
            
        auction = self.active_auctions[msg.task_id]
        
        if msg.robot_id in auction['bids']:
            return
            
        auction['bids'][msg.robot_id] = msg.bid_value

    def auction_timeout(self, auction_key):
        if auction_key not in self.active_auctions:
            return
            
        auction = self.active_auctions.pop(auction_key)
        auction['timer'].cancel()
        
        bids = auction['bids']
        if not bids:
            self.get_logger().warn(f"[{auction_key}] Auction closed with no bids?!")
            return

        # WINNER SELECTION ALGORITHM
        sorted_bids = sorted(bids.items(), key=lambda item: (item[1], item[0]))
        winner_id, winning_bid = sorted_bids[0]
        self.completed_auctions[auction_key] = winner_id

        task_msg = auction['msg']
        self.get_logger().info(f"[{task_msg.task_id}] Auction Closed (Epoch {task_msg.epoch}). Winner determined: {winner_id} with bid {winning_bid:.3f}")

        # ----------------------------------------------------
        # OWNERSHIP MUTATION COMMIT
        # ----------------------------------------------------
        if winner_id == self.robot_id:
            self.get_logger().info(f"[{task_msg.task_id}] I WON! Mutating state and committing ownership to network.")
            
            task_msg.owner_id = self.robot_id
            if task_msg.state == Task.STATE_UNASSIGNED:
                task_msg.state = Task.STATE_ASSIGNED
            
            # Record locally immediately
            self.local_tasks[task_msg.task_id] = {'state': task_msg.state, 'msg': task_msg, 'timer': None, 'recovery_status': None}
            self.task_pub.publish(task_msg)
            
            # Kick off simulated execution lifecycle
            timer = self.create_timer(10.0, lambda tid=task_msg.task_id: self.simulate_in_progress(tid))
            self.local_tasks[task_msg.task_id]['timer'] = timer
            
    def simulate_in_progress(self, task_id):
        if task_id not in self.local_tasks:
            return
            
        task_data = self.local_tasks[task_id]
        if task_data.get('timer'):
            task_data['timer'].cancel()
            
        if task_data['state'] == Task.STATE_ASSIGNED:
            task_msg = task_data['msg']
            task_msg.state = Task.STATE_IN_PROGRESS
            task_data['state'] = Task.STATE_IN_PROGRESS
            self.get_logger().info(f"[{task_id}] Simulated execution: Transitioning to IN_PROGRESS.")
            self.task_pub.publish(task_msg)
        
        # Proceed to completed
        timer = self.create_timer(10.0, lambda tid=task_id: self.simulate_completed(tid))
        task_data['timer'] = timer
        
    def simulate_completed(self, task_id):
        if task_id not in self.local_tasks:
            return
            
        task_data = self.local_tasks[task_id]
        if task_data.get('timer'):
            task_data['timer'].cancel()
            task_data['timer'] = None
            
        if task_data['state'] != Task.STATE_IN_PROGRESS:
            return
            
        task_msg = task_data['msg']
        task_msg.state = Task.STATE_COMPLETED
        task_data['state'] = Task.STATE_COMPLETED
        
        self.get_logger().info(f"[{task_id}] Simulated execution: Transitioning to COMPLETED.")
        self.task_pub.publish(task_msg)

    # ----------------------------------------------------
    # PHASE 7.5: TASK RECOVERY LOGIC
    # ----------------------------------------------------
    def liveness_callback(self, msg):
        try:
            data = json.loads(msg.data)
            peer_id = data.get('robot_id')
            status = data.get('status')
            
            if not peer_id or not status:
                return

            self.peer_liveness[peer_id] = status
            
            if status == 'TIMED_OUT':
                self.handle_peer_timeout(peer_id)
            elif status == 'ALIVE':
                self.handle_peer_recovery(peer_id)
        except json.JSONDecodeError:
            self.get_logger().error("Failed to parse peer liveness message.")

    def handle_peer_timeout(self, peer_id):
        # Identify all tasks owned by this timed-out peer that are ASSIGNED/IN_PROGRESS
        for task_id, task_data in self.local_tasks.items():
            task_msg = task_data['msg']
            if task_msg.owner_id == peer_id and task_msg.state in [Task.STATE_ASSIGNED, Task.STATE_IN_PROGRESS]:
                if task_id not in self.recovery_timers:
                    self.get_logger().warn(f"[{task_id}] Owner {peer_id} timed out. Recovery pending (grace {self.recovery_grace_period}s).")
                    task_data['recovery_status'] = 'PENDING'
                    
                    timer = self.create_timer(
                        self.recovery_grace_period, 
                        lambda tid=task_id: self.recovery_grace_expired(tid)
                    )
                    self.recovery_timers[task_id] = timer

    def handle_peer_recovery(self, peer_id):
        # Cancel any pending recoveries if the peer comes back before grace expires
        for task_id, task_data in self.local_tasks.items():
            task_msg = task_data['msg']
            if task_msg.owner_id == peer_id and task_id in self.recovery_timers:
                self.get_logger().info(f"[{task_id}] Owner {peer_id} recovered. Canceling recovery pending state.")
                timer = self.recovery_timers.pop(task_id)
                timer.cancel()
                task_data['recovery_status'] = None

    def recovery_grace_expired(self, task_id):
        if task_id not in self.recovery_timers:
            return
            
        timer = self.recovery_timers.pop(task_id)
        timer.cancel()
        
        if task_id not in self.local_tasks:
            return
            
        task_data = self.local_tasks[task_id]
        task_msg = task_data['msg']
        
        # Verify conditions are still met
        if task_msg.state in [Task.STATE_ASSIGNED, Task.STATE_IN_PROGRESS]:
            peer_status = self.peer_liveness.get(task_msg.owner_id, 'ALIVE')
            if peer_status == 'TIMED_OUT':
                task_data['recovery_status'] = 'ELIGIBLE'
                self.get_logger().error(
                    f"[{task_id}] Recovery grace expired! Task owned by {task_msg.owner_id} is now ELIGIBLE for recovery."
                )
                
                # ----------------------------------------------------
                # PHASE 7.6: INITIATE RECOVERY AUCTION
                # ----------------------------------------------------
                recovery_msg = Task()
                recovery_msg.task_id = task_msg.task_id
                recovery_msg.pickup_location = task_msg.pickup_location
                recovery_msg.dropoff_location = task_msg.dropoff_location
                recovery_msg.state = task_msg.state
                recovery_msg.owner_id = task_msg.owner_id
                recovery_msg.epoch = task_msg.epoch + 1
                
                self.initiate_auction(recovery_msg)


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
