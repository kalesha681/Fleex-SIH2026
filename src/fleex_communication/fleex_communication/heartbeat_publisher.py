import rclpy
from rclpy.node import Node
from fleex_msgs.msg import Heartbeat


class HeartbeatPublisher(Node):
    def __init__(self):
        super().__init__('fleex_heartbeat_publisher')

        # Parameters
        self.declare_parameter('robot_id', 'unknown_robot')
        self.declare_parameter('heartbeat_period', 1.0)

        self.robot_id = self.get_parameter('robot_id').value
        self.heartbeat_period = self.get_parameter('heartbeat_period').value

        # Publisher
        # Topic name: 'heartbeat' (will be resolved relative to namespace if any)
        self.publisher_ = self.create_publisher(Heartbeat, 'heartbeat', 10)

        # State
        self.sequence_ = 0

        # Timer
        self.timer_ = self.create_timer(self.heartbeat_period, self.timer_callback)

        self.get_logger().info(
            f'Heartbeat publisher initialized for {self.robot_id} '
            f'with period {self.heartbeat_period}s.'
        )

    def timer_callback(self):
        msg = Heartbeat()
        msg.robot_id = self.robot_id
        msg.sequence = self.sequence_
        
        # Populate timestamp using ROS clock
        msg.stamp = self.get_clock().now().to_msg()
        
        self.publisher_.publish(msg)

        # Log at reasonable rate (every 10 messages)
        if self.sequence_ % 10 == 0:
            self.get_logger().info(
                f'Published heartbeat {self.sequence_} for {self.robot_id}'
            )

        self.sequence_ += 1


def main(args=None):
    rclpy.init(args=args)
    node = HeartbeatPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
