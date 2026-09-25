import rclpy
from rclpy.node import Node
from fleex_msgs.msg import Task
import random

class TaskGenerator(Node):
    def __init__(self):
        super().__init__('fleex_task_generator')

        # Declare parameters
        self.declare_parameter('task_rate', 0.2)  # Tasks per second
        self.declare_parameter('start_task_id', 1)
        self.declare_parameter('pickup_locations', ['shelf_A_01', 'shelf_A_02', 'shelf_B_01', 'charging_station'])
        self.declare_parameter('dropoff_locations', ['station_01', 'station_02', 'packing_area'])

        # Get parameter values
        self.task_rate = self.get_parameter('task_rate').value
        self.current_task_id = self.get_parameter('start_task_id').value
        self.pickup_locations = self.get_parameter('pickup_locations').value
        self.dropoff_locations = self.get_parameter('dropoff_locations').value

        # Publisher
        self.publisher_ = self.create_publisher(Task, '/fleex/tasks', 10)

        # Timer
        timer_period = 1.0 / self.task_rate if self.task_rate > 0 else 5.0
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info(f'Minimal Task Generator initialized (rate: {self.task_rate} tasks/sec)')

    def timer_callback(self):
        msg = Task()
        
        # Unique task ID
        msg.task_id = f"task_{self.current_task_id:04d}"
        
        # Select random locations
        msg.pickup_location = random.choice(self.pickup_locations)
        msg.dropoff_location = random.choice(self.dropoff_locations)
        
        # Initial unassigned state
        msg.state = Task.STATE_UNASSIGNED
        msg.owner_id = ""

        # Publish
        self.publisher_.publish(msg)
        self.get_logger().info(
            f"Generated Task: {msg.task_id} "
            f"({msg.pickup_location} -> {msg.dropoff_location})"
        )

        self.current_task_id += 1


def main(args=None):
    rclpy.init(args=args)
    node = TaskGenerator()
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
