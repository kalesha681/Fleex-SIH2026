import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus

from fleex_msgs.msg import Task
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped

import math
import os
import yaml
class TaskExecutor(Node):
    def __init__(self):
        super().__init__('fleex_task_executor')
        
        self.declare_parameter('robot_id', 'amr1')
        self.robot_id = self.get_parameter('robot_id').value
        
        # Load location registry
        locations_file = os.path.join(os.getcwd(), 'config/warehouse/locations.yaml')
        try:
            with open(locations_file, 'r') as f:
                self.location_registry = yaml.safe_load(f).get('locations', {})
            self.get_logger().info(f"[TASK_EXEC] Loaded {len(self.location_registry)} locations from {locations_file}")
        except Exception as e:
            self.get_logger().error(f"[TASK_EXEC] Failed to load location registry: {e}")
            self.location_registry = {}
        
        # Subscribe and publish tasks
        self.task_sub = self.create_subscription(Task, '/fleex/tasks', self.task_callback, 10)
        self.task_pub = self.create_publisher(Task, '/fleex/tasks', 10)
        
        # Action client for Nav2
        action_name = f'/{self.robot_id}/navigate_to_pose'
        self.nav_client = ActionClient(self, NavigateToPose, action_name)
        
        self.current_task_msg = None
        self.current_epoch = -1
        self.navigation_state = 'IDLE' # IDLE, PICKUP, DROPOFF
        self.goal_handle = None
        
        self.get_logger().info(f"[TASK_EXEC] TaskExecutor initialized for {self.robot_id}")
        self.get_logger().info(f"[TASK_EXEC] Connecting to Nav2 Action Server: {action_name}")

    def task_callback(self, msg):
        # Ignore terminal tasks
        if msg.state in [Task.STATE_COMPLETED, Task.STATE_FAILED]:
            if self.current_task_msg and self.current_task_msg.task_id == msg.task_id:
                self.get_logger().info(f"[TASK_EXEC] Task {msg.task_id} reached terminal state.")
                self.cancel_current_goal()
                self.reset_execution_state()
            return

        # If it's not our task, check if it was stolen/recovered from us
        if msg.owner_id != self.robot_id:
            if self.current_task_msg and self.current_task_msg.task_id == msg.task_id:
                if msg.epoch > self.current_epoch:
                    self.get_logger().error(f"[TASK_EXEC] task={msg.task_id} STOLEN/RECOVERED by {msg.owner_id} at epoch {msg.epoch}! Canceling execution.")
                    self.cancel_current_goal()
                    self.reset_execution_state()
            return

        # It IS our task
        if self.current_task_msg and self.current_task_msg.task_id == msg.task_id:
            # We are already processing this task
            if msg.epoch > self.current_epoch:
                self.get_logger().info(f"[TASK_EXEC] task={msg.task_id} Epoch updated {self.current_epoch} -> {msg.epoch}")
                self.current_epoch = msg.epoch
                self.current_task_msg = msg
            return
            
        # We are assigned a new task (or recovered one)
        if msg.state in [Task.STATE_ASSIGNED, Task.STATE_IN_PROGRESS]:
            if getattr(self, 'task_queue', None) is None:
                self.task_queue = []
                
            if self.navigation_state != 'IDLE':
                if msg.task_id not in [t.task_id for t in self.task_queue]:
                    self.task_queue.append(msg)
                    self.get_logger().info(f"[TASK_EXEC] Queued task {msg.task_id}. Queue size: {len(self.task_queue)}")
                return
                
            self.current_task_msg = msg
            self.current_epoch = msg.epoch
            self.start_pickup()

    def start_pickup(self):
        self.navigation_state = 'PICKUP'
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} pickup navigation started")
        
        # Publish IN_PROGRESS
        if self.current_task_msg.state != Task.STATE_IN_PROGRESS:
            self.current_task_msg.state = Task.STATE_IN_PROGRESS
            self.task_pub.publish(self.current_task_msg)
            
        loc = self.location_registry.get(self.current_task_msg.pickup_location)
        if not loc:
            self.get_logger().error(f"[TASK_EXEC] Unknown pickup location: {self.current_task_msg.pickup_location}")
            self.reset_execution_state()
            return
            
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} pickup_location={self.current_task_msg.pickup_location} resolved_model={loc.get('model_id')} goal_frame={loc.get('frame')} goal_x={loc['approach']['x']} goal_y={loc['approach']['y']} goal_yaw={loc['approach']['yaw']}")
        self.send_nav_goal(loc, self.pickup_done_callback)

    def pickup_done_callback(self):
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} pickup reached")
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} pickup event complete")
        
        self.navigation_state = 'DROPOFF'
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} dropoff navigation started")
        
        loc = self.location_registry.get(self.current_task_msg.dropoff_location)
        if not loc:
            self.get_logger().error(f"[TASK_EXEC] Unknown dropoff location: {self.current_task_msg.dropoff_location}")
            self.reset_execution_state()
            return
            
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} dropoff_location={self.current_task_msg.dropoff_location} resolved_model={loc.get('model_id')} goal_frame={loc.get('frame')} goal_x={loc['approach']['x']} goal_y={loc['approach']['y']} goal_yaw={loc['approach']['yaw']}")
        self.send_nav_goal(loc, self.dropoff_done_callback)
        
    def dropoff_done_callback(self):
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} dropoff reached")
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} dropoff event complete")
        
        self.current_task_msg.state = Task.STATE_COMPLETED
        self.task_pub.publish(self.current_task_msg)
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} COMPLETED")
        
        self.reset_execution_state()

    def send_nav_goal(self, loc, done_callback):
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(f"[TASK_EXEC] Nav2 Action server not available!")
            self.reset_execution_state()
            return
            
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = loc.get('frame', 'map')
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(loc['approach']['x'])
        goal_msg.pose.pose.position.y = float(loc['approach']['y'])
        goal_msg.pose.pose.position.z = 0.0
        
        yaw = float(loc['approach']['yaw'])
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        self.current_done_callback = done_callback
        
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f"[TASK_EXEC] task={self.current_task_msg.task_id} Navigation goal rejected by Nav2!")
            self.reset_execution_state()
            return
            
        self.goal_handle = goal_handle
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        if not self.current_task_msg:
            return # Was cancelled/stolen

        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            if self.current_done_callback:
                self.current_done_callback()
        else:
            self.get_logger().error(f"[TASK_EXEC] task={self.current_task_msg.task_id} Navigation failed/aborted with status {status}. Leaving task for recovery.")
            self.reset_execution_state()

    def cancel_current_goal(self):
        if self.goal_handle:
            self.get_logger().info("[TASK_EXEC] Canceling current Nav2 goal...")
            self.goal_handle.cancel_goal_async()
            self.goal_handle = None

    def reset_execution_state(self):
        self.current_task_msg = None
        self.current_epoch = -1
        self.navigation_state = 'IDLE'
        self.goal_handle = None
        self.current_done_callback = None
        
        if getattr(self, 'task_queue', None) and len(self.task_queue) > 0:
            next_task = self.task_queue.pop(0)
            self.get_logger().info(f"[TASK_EXEC] Dequeued task {next_task.task_id} for execution. Remaining in queue: {len(self.task_queue)}")
            self.task_callback(next_task)

def main(args=None):
    rclpy.init(args=args)
    node = TaskExecutor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cancel_current_goal()
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
