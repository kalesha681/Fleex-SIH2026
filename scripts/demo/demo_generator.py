#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from fleex_msgs.msg import Task
import sys

class DemoTaskGenerator(Node):
    def __init__(self):
        super().__init__('fleex_demo_generator')
        self.publisher_ = self.create_publisher(Task, '/fleex/tasks', 10)
        self.timer = self.create_timer(6.0, self.timer_callback)
        self.task_count = 0
        self.get_logger().info('Demo Generator started. Firing tasks sequentially...')

    def timer_callback(self):
        self.task_count += 1
        
        if self.task_count == 1:
            # TASK 001: Top to Bottom (Crosses Center Chokepoint)
            msg1 = Task()
            msg1.task_id = "demo_task_001"
            msg1.pickup_location = "station_01" 
            msg1.dropoff_location = "packing_area"
            msg1.state = Task.STATE_UNASSIGNED
            msg1.owner_id = ""
            self.publisher_.publish(msg1)
            self.get_logger().info(f"Fired {msg1.task_id}: {msg1.pickup_location} -> {msg1.dropoff_location}")
            
        elif self.task_count == 2:
            # TASK 002: Left to Right (Crosses Center Chokepoint)
            msg2 = Task()
            msg2.task_id = "demo_task_002"
            msg2.pickup_location = "shelff_01_001"
            msg2.dropoff_location = "shelfe_01_001"
            msg2.state = Task.STATE_UNASSIGNED
            msg2.owner_id = ""
            self.publisher_.publish(msg2)
            self.get_logger().info(f"Fired {msg2.task_id}: {msg2.pickup_location} -> {msg2.dropoff_location}")
            
        elif self.task_count == 3:
            # TASK 003: Bottom Right to Middle Right (Stays out of the way)
            msg3 = Task()
            msg3.task_id = "demo_task_003"
            msg3.pickup_location = "shelfe_01_002"
            msg3.dropoff_location = "shelfd_01_001"
            msg3.state = Task.STATE_UNASSIGNED
            msg3.owner_id = ""
            self.publisher_.publish(msg3)
            self.get_logger().info(f"Fired {msg3.task_id}: {msg3.pickup_location} -> {msg3.dropoff_location}")
            
        elif self.task_count == 4:
            self.get_logger().info('All demo tasks fired. Shutting down generator in 2 seconds...')
            self.shutdown_timer = self.create_timer(2.0, self.shutdown_callback)

    def shutdown_callback(self):
        sys.exit(0)

def main(args=None):
    rclpy.init(args=args)
    node = DemoTaskGenerator()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
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
