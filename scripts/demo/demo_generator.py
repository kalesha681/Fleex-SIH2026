#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from fleex_msgs.msg import Task
import sys

class DemoTaskGenerator(Node):
    def __init__(self):
        super().__init__('fleex_demo_generator')
        self.publisher_ = self.create_publisher(Task, '/fleex/tasks', 10)
        self.timer = self.create_timer(3.0, self.timer_callback)
        self.fired = False
        self.get_logger().info('Demo Generator started. Firing tasks in 3 seconds...')

    def timer_callback(self):
        if self.fired:
            return
            
        self.fired = True
        
        # TASK 001: Static obstacle intensive route
        # From left side to charging station
        msg1 = Task()
        msg1.task_id = "demo_task_001"
        msg1.pickup_location = "shelff_01_001" 
        msg1.dropoff_location = "charging_station"
        msg1.state = Task.STATE_UNASSIGNED
        msg1.owner_id = ""
        self.publisher_.publish(msg1)
        self.get_logger().info(f"Fired {msg1.task_id}: {msg1.pickup_location} -> {msg1.dropoff_location}")
        
        # TASK 002: Chokepoint crosser (Right to Left)
        msg2 = Task()
        msg2.task_id = "demo_task_002"
        msg2.pickup_location = "shelfe_01_001"
        msg2.dropoff_location = "station_02"
        msg2.state = Task.STATE_UNASSIGNED
        msg2.owner_id = ""
        self.publisher_.publish(msg2)
        self.get_logger().info(f"Fired {msg2.task_id}: {msg2.pickup_location} -> {msg2.dropoff_location}")
        
        # TASK 003: Chokepoint crosser (Bottom Right to Top Left)
        msg3 = Task()
        msg3.task_id = "demo_task_003"
        msg3.pickup_location = "shelfe_01_002"
        msg3.dropoff_location = "station_01"
        msg3.state = Task.STATE_UNASSIGNED
        msg3.owner_id = ""
        self.publisher_.publish(msg3)
        self.get_logger().info(f"Fired {msg3.task_id}: {msg3.pickup_location} -> {msg3.dropoff_location}")
        
        self.get_logger().info('Demo tasks fired. Shutting down generator in 2 seconds...')
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
