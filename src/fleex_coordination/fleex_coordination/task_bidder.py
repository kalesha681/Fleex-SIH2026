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
        self.task_sub = self.create_subscription(
            Task,
            '/fleex/tasks',
            self.task_callback,
            10
        )
        self.bid_sub = self.create_subscription(
            TaskBid,
            '/fleex/task_bids',
            self.bid_callback,
            10
        )
        self.publisher_ = self.create_publisher(TaskBid, '/fleex/task_bids', 10)

        # Internal state tracking
        self.processed_tasks = set()
        
        # Structure: { task_id: { 'bids': { robot_id: bid_value }, 'timer': Timer } }
        self.active_auctions = {}

        self.get_logger().info(f'Task Bidder initialized for robot: {self.robot_id}')
        self.get_logger().info(f'Auction window set to: {self.bid_collection_window}s')

    def task_callback(self, msg):
        # ELIGIBILITY RULE 1 & 2: Task must be unassigned and have no owner
        if msg.state != Task.STATE_UNASSIGNED or msg.owner_id != "":
            return
            
        # Ensure we only process and auction this unique task ID once
        if msg.task_id in self.processed_tasks or msg.task_id in self.active_auctions:
            return

        # ELIGIBILITY RULE 3: Required basic information exists
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
            'bids': {self.robot_id: bid_value}, # Immediately insert our own bid
            'timer': timer
        }
        self.processed_tasks.add(msg.task_id)

        # Publish bid to network
        bid_msg = TaskBid()
        bid_msg.task_id = msg.task_id
        bid_msg.robot_id = self.robot_id
        bid_msg.bid_value = bid_value

        self.publisher_.publish(bid_msg)
        
        self.get_logger().info(
            f"[{msg.task_id}] Auction Opened. Published local bid: {bid_value:.3f}"
        )

    def bid_callback(self, msg):
        # STALE/UNKNOWN BID HANDLING:
        # If the task_id is not in our active auctions, the window has closed or it's unknown.
        if msg.task_id not in self.active_auctions:
            return
            
        auction = self.active_auctions[msg.task_id]
        
        # DUPLICATE BID HANDLING:
        # We process strictly the first bid received from a peer and ignore subsequent duplicates.
        if msg.robot_id in auction['bids']:
            return
            
        auction['bids'][msg.robot_id] = msg.bid_value
        self.get_logger().debug(f"[{msg.task_id}] Received bid {msg.bid_value:.3f} from {msg.robot_id}")

    def auction_timeout(self, task_id):
        # Retrieve and close the auction
        if task_id not in self.active_auctions:
            return
            
        auction = self.active_auctions.pop(task_id)
        
        # Clean up the ROS timer so it doesn't fire again
        auction['timer'].cancel()
        
        bids = auction['bids']
        if not bids:
            self.get_logger().warn(f"[{task_id}] Auction closed with no bids?!")
            return

        # WINNER SELECTION ALGORITHM
        # Lowest bid wins.
        # Tie-breaker: If bids are identical, lowest robot_id string wins deterministically.
        # Sorting by (bid_value, robot_id) inherently satisfies this perfectly.
        sorted_bids = sorted(bids.items(), key=lambda item: (item[1], item[0]))
        winner_id, winning_bid = sorted_bids[0]

        self.get_logger().info(
            f"[{task_id}] Auction Closed. Winner determined: {winner_id} with bid {winning_bid:.3f} "
            f"(Total bids received: {len(bids)})"
        )


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
