import rclpy
from rclpy.node import Node
import hashlib
from fleex_msgs.msg import Task, TaskBid

class TaskBidder(Node):
    def __init__(self):
        super().__init__('fleex_task_bidder')

        # Declare parameters
        self.declare_parameter('robot_id', 'amr_1')
        self.robot_id = self.get_parameter('robot_id').value

        # Publishers and Subscribers
        self.subscription = self.create_subscription(
            Task,
            '/fleex/tasks',
            self.task_callback,
            10
        )
        self.publisher_ = self.create_publisher(TaskBid, '/fleex/task_bids', 10)

        # Internal state tracking
        self.bidded_tasks = set()

        self.get_logger().info(f'Task Bidder initialized for robot: {self.robot_id}')

    def task_callback(self, msg):
        # ELIGIBILITY RULE 1: Task must be unassigned
        if msg.state != Task.STATE_UNASSIGNED:
            return
        
        # ELIGIBILITY RULE 2: Task must not already have an owner
        if msg.owner_id != "":
            return
            
        # Ensure we only bid once per unassigned task broadcast
        if msg.task_id in self.bidded_tasks:
            return

        # ELIGIBILITY RULE 3: Required basic information exists
        if not msg.task_id or not msg.pickup_location:
            self.get_logger().warn("Received unassigned task with missing core data.")
            return

        # CALCULATE DETERMINISTIC BID
        # MVP Placeholder: bid = normalized_distance + normalized_time
        # We use a stable hash to guarantee deterministic pseudo-random values 
        # that can be reproduced identically across identical simulation states.
        stable_string = f"{msg.task_id}_{msg.pickup_location}_{self.robot_id}"
        hash_val = int(hashlib.md5(stable_string.encode()).hexdigest(), 16)
        
        normalized_distance = (hash_val % 100) / 100.0
        normalized_time = ((hash_val >> 8) % 100) / 100.0
        
        bid_value = normalized_distance + normalized_time

        # Create and publish bid
        bid_msg = TaskBid()
        bid_msg.task_id = msg.task_id
        bid_msg.robot_id = self.robot_id
        bid_msg.bid_value = float(bid_value)

        self.publisher_.publish(bid_msg)
        self.bidded_tasks.add(msg.task_id)

        self.get_logger().info(
            f"Published Bid for {msg.task_id}: {bid_value:.3f} "
            f"(dist: {normalized_distance:.2f}, time: {normalized_time:.2f})"
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
