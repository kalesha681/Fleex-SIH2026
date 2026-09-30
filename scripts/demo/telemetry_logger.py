#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from fleex_msgs.msg import Task
import csv
import os
import time
from datetime import datetime

class TelemetryLogger(Node):
    def __init__(self):
        super().__init__('fleex_telemetry_logger')
        
        # Ensure data directory exists
        self.data_dir = os.path.join(os.path.expanduser('~'), 'sih_fleex_workspace', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.csv_file = os.path.join(self.data_dir, 'task_metrics.csv')
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize CSV if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'run_id', 'task_id', 'owner_id', 'pickup_location', 
                    'dropoff_location', 'created_ts', 'assigned_ts', 
                    'completed_ts', 'allocation_latency_sec', 
                    'execution_time_sec', 'total_time_sec', 'final_state'
                ])
                
        self.task_history = {}
        
        self.subscription = self.create_subscription(
            Task,
            '/fleex/tasks',
            self.task_callback,
            10
        )
        self.get_logger().info(f"Telemetry Logger started. Logging to {self.csv_file}")

    def task_callback(self, msg):
        current_time = time.time()
        
        if msg.task_id not in self.task_history:
            self.task_history[msg.task_id] = {
                'created_ts': current_time,
                'assigned_ts': None,
                'completed_ts': None,
                'owner_id': msg.owner_id,
                'pickup_location': msg.pickup_location,
                'dropoff_location': msg.dropoff_location,
                'final_state': 'UNKNOWN'
            }
            
        task_record = self.task_history[msg.task_id]
        
        # Update owner if it changed (e.g. recovery)
        if msg.owner_id and msg.owner_id != "":
            task_record['owner_id'] = msg.owner_id
            
        # State Machine Tracking
        if msg.state == Task.STATE_ASSIGNED or msg.state == Task.STATE_IN_PROGRESS:
            if task_record['assigned_ts'] is None:
                task_record['assigned_ts'] = current_time
                
        elif msg.state == Task.STATE_COMPLETED or msg.state == Task.STATE_FAILED:
            if task_record['completed_ts'] is None:
                task_record['completed_ts'] = current_time
                task_record['final_state'] = 'COMPLETED' if msg.state == Task.STATE_COMPLETED else 'FAILED'
                
                self.write_to_csv(msg.task_id, task_record)
                self.get_logger().info(f"Logged completed task metrics for {msg.task_id}")

    def write_to_csv(self, task_id, record):
        created = record['created_ts']
        assigned = record['assigned_ts'] or created
        completed = record['completed_ts']
        
        allocation_latency = assigned - created
        execution_time = completed - assigned
        total_time = completed - created
        
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.run_id,
                task_id,
                record['owner_id'],
                record['pickup_location'],
                record['dropoff_location'],
                f"{created:.3f}",
                f"{assigned:.3f}",
                f"{completed:.3f}",
                f"{allocation_latency:.3f}",
                f"{execution_time:.3f}",
                f"{total_time:.3f}",
                record['final_state']
            ])

def main(args=None):
    rclpy.init(args=args)
    node = TelemetryLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
