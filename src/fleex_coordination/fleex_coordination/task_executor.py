import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus

from fleex_msgs.msg import Task
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from fleex_msgs.srv import RequestZone, ReleaseZone

import math
import os
import yaml
import time

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
            self.get_logger().info(f'[TASK_EXEC] Loaded {len(self.location_registry)} locations from {locations_file}')
        except Exception as e:
            self.get_logger().error(f'[TASK_EXEC] Failed to load location registry: {e}')
            self.location_registry = {}
        
        # Current location (unknown initially)
        self.current_location = None
        
        # Zone management
        self.zone_id = 'choke_01'  # assuming only one zone for MVP
        self.zone_lease_pending = False  # True when we have requested lease and waiting for grant before sending Nav2 goal
        self.zone_lease_held = False     # True when we currently hold the lease
        
        # Service clients for zone request and release
        self.zone_request_client = self.create_client(RequestZone, '/fleex/request_zone')
        self.zone_release_client = self.create_client(ReleaseZone, '/fleex/release_zone')
        
        # Wait for services to be available
        while not self.zone_request_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('[TASK_EXEC] Zone request service not available, waiting again...')
        while not self.zone_release_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('[TASK_EXEC] Zone release service not available, waiting again...')
        
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
        
        self.get_logger().info(f'[TASK_EXEC] TaskExecutor initialized for {self.robot_id}')
        self.get_logger().info(f'[TASK_EXEC] Connecting to Nav2 Action Server: {action_name}')

    def task_callback(self, msg):
        # Ignore terminal tasks
        if msg.state in [Task.STATE_COMPLETED, Task.STATE_FAILED]:
            if self.current_task_msg and self.current_task_msg.task_id == msg.task_id:
                self.get_logger().info(f'[TASK_EXEC] Task {msg.task_id} reached terminal state.')
                self.cancel_current_goal()
                self.reset_execution_state()
            return

        # If it's not our task, check if it was stolen/recovered from us
        if msg.owner_id != self.robot_id:
            if self.current_task_msg and self.current_task_msg.task_id == msg.task_id:
                if msg.epoch > self.current_epoch:
                    self.get_logger().error(f'[TASK_EXEC] task={msg.task_id} STOLEN/RECOVERED by {msg.owner_id} at epoch {msg.epoch}! Canceling execution.')
                    self.cancel_current_goal()
                    self.reset_execution_state()
            return

        # It IS our task
        if self.current_task_msg and self.current_task_msg.task_id == msg.task_id:
            # We are already processing this task
            if msg.epoch > self.current_epoch:
                self.get_logger().info(f'[TASK_EXEC] task={msg.task_id} Epoch updated {self.current_epoch} -> {msg.epoch}')
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
                    self.get_logger().info(f'[TASK_EXEC] Queued task {msg.task_id}. Queue size: {len(self.task_queue)}')
                return
                
            self.current_task_msg = msg
            self.current_epoch = msg.epoch
            self.start_pickup()

    def start_pickup(self):
        self.navigation_state = 'PICKUP'
        self.get_logger().info(f'[TASK_EXEC] task={self.current_task_msg.task_id} pickup navigation started')
        
        # Publish IN_PROGRESS
        if self.current_task_msg.state != Task.STATE_IN_PROGRESS:
            self.current_task_msg.state = Task.STATE_IN_PROGRESS
            self.task_pub.publish(self.current_task_msg)
            
        loc = self.location_registry.get(self.current_task_msg.pickup_location)
        if not loc:
            self.get_logger().error(f'[TASK_EXEC] Unknown pickup location: {self.current_task_msg.pickup_location}')
            self.reset_execution_state()
            return
            
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} pickup_location={self.current_task_msg.pickup_location} resolved_model={loc.get('model_id')} goal_frame={loc.get('frame')} goal_x={loc['approach']['x']} goal_y={loc['approach']['y']} goal_yaw={loc['approach']['yaw']}")
        self.send_nav_goal(loc, self.pickup_done_callback)

    def pickup_done_callback(self):
        self.get_logger().info(f'[TASK_EXEC] task={self.current_task_msg.task_id} pickup reached')
        self.get_logger().info(f'[TASK_EXEC] task={self.current_task_msg.task_id} pickup event complete')
        
        # Update current location and set
        self.update_current_location(self.current_task_msg.pickup_location)
        
        # If we held a lease for this crossing, release it now that we have crossed
        if self.zone_lease_held:
            self.release_zone_lease()
            self.zone_lease_held = False
        
        self.navigation_state = 'DROPOFF'
        self.get_logger().info(f'[TASK_EXEC] task={self.current_task_msg.task_id} dropoff navigation started')
        
        loc = self.location_registry.get(self.current_task_msg.dropoff_location)
        if not loc:
            self.get_logger().error(f'[TASK_EXEC] Unknown dropoff location: {self.current_task_msg.dropoff_location}')
            self.reset_execution_state()
            return
            
        self.get_logger().info(f"[TASK_EXEC] task={self.current_task_msg.task_id} dropoff_location={self.current_task_msg.dropoff_location} resolved_model={loc.get('model_id')} goal_frame={loc.get('frame')} goal_x={loc['approach']['x']} goal_y={loc['approach']['y']} goal_yaw={loc['approach']['yaw']}")
        self.send_nav_goal(loc, self.dropoff_done_callback)
        
    def dropoff_done_callback(self):
        self.get_logger().info(f'[TASK_EXEC] task={self.current_task_msg.task_id} dropoff reached')
        self.get_logger().info(f'[TASK_EXEC] task={self.current_task_msg.task_id} dropoff event complete')
        
        # Update current location and set
        self.update_current_location(self.current_task_msg.dropoff_location)
        
        # If we held a lease for this crossing, release it now that we have crossed
        if self.zone_lease_held:
            self.release_zone_lease()
            self.zone_lease_held = False
        
        self.current_task_msg.state = Task.STATE_COMPLETED
        self.task_pub.publish(self.current_task_msg)
        self.get_logger().info(f'[TASK_EXEC] task={self.current_task_msg.task_id} COMPLETED')
        
        self.reset_execution_state()

    def update_current_location(self, location_key):
        """Update the current location."""
        self.current_location = location_key

    def line_intersects_circle(self, x1, y1, x2, y2, cx, cy, r):
        import math
        dx = x2 - x1
        dy = y2 - y1
        fx = x1 - cx
        fy = y1 - cy
        
        a = dx*dx + dy*dy
        b = 2 * (fx*dx + fy*dy)
        c = (fx*fx + fy*fy) - r*r
        
        discriminant = b*b - 4*a*c
        if discriminant < 0:
            return False
            
        discriminant = math.sqrt(discriminant)
        t1 = (-b - discriminant) / (2*a) if a != 0 else -1
        t2 = (-b + discriminant) / (2*a) if a != 0 else -1
        
        if (0 <= t1 <= 1) or (0 <= t2 <= 1):
            return True
            
        if (x1-cx)**2 + (y1-cy)**2 <= r*r:
            return True
        if (x2-cx)**2 + (y2-cy)**2 <= r*r:
            return True
            
        return False

    def send_nav_goal(self, loc, done_callback):
        self.pending_nav_loc = loc
        self.current_done_callback = done_callback
        
        # Get start coordinates
        if self.current_location is None:
            if self.robot_id == 'amr2':
                start_x, start_y = 0.0, 2.0
            elif self.robot_id == 'amr3':
                start_x, start_y = 0.0, -2.0
            else:
                start_x, start_y = 0.0, 0.0
        else:
            start_loc = self.location_registry.get(self.current_location)
            start_x = float(start_loc['approach']['x'])
            start_y = float(start_loc['approach']['y'])
            
        goal_x = float(loc['approach']['x'])
        goal_y = float(loc['approach']['y'])
        
        need_to_cross = self.line_intersects_circle(start_x, start_y, goal_x, goal_y, 0.0, 0.0, 2.0)
        
        if need_to_cross:
            self.get_logger().info(f'[ZONE] Path from ({start_x:.1f},{start_y:.1f}) to ({goal_x:.1f},{goal_y:.1f}) crosses chokepoint. Requesting zone lease.')
            # Start retry timer
            self.zone_retry_timer = self.create_timer(1.0, self.try_acquire_zone)
            self.try_acquire_zone() # fire immediately
        else:
            self.get_logger().debug(f'[TASK_EXEC] No chokepoint crossing needed (current set: {self.current_set}, goal set: {goal_set})')
            self.execute_nav_goal()
            
    def try_acquire_zone(self):
        if self.zone_lease_held:
            return
            
        if self.zone_lease_pending:
            return
            
        self.zone_lease_pending = True
        self.get_logger().info(f'[ZONE] {self.robot_id} requesting {self.zone_id}')
        request = RequestZone.Request()
        request.robot_id = self.robot_id
        request.zone_id = self.zone_id
        
        future = self.zone_request_client.call_async(request)
        future.add_done_callback(self.zone_request_response_callback)

    def zone_request_response_callback(self, future):
        self.zone_lease_pending = False
        try:
            response = future.result()
            if response.granted:
                self.get_logger().info(f'[ZONE] {self.zone_id} granted to {self.robot_id}')
                self.zone_lease_held = True
                if hasattr(self, 'zone_retry_timer') and self.zone_retry_timer:
                    self.zone_retry_timer.cancel()
                    self.zone_retry_timer = None
                self.execute_nav_goal()
            else:
                self.get_logger().info(f'[ZONE] {self.zone_id} occupied. {self.robot_id} waiting outside {self.zone_id}')
        except Exception as e:
            self.get_logger().error(f'[TASK_EXEC] Service call failed: {e}')

    def execute_nav_goal(self):
        loc = self.pending_nav_loc
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(f'[TASK_EXEC] Nav2 Action server not available!')
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
        
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)



    def release_zone_lease(self):
        """Release the zone lease."""
        request = ReleaseZone.Request()
        request.robot_id = self.robot_id
        request.zone_id = self.zone_id
        
        future = self.zone_release_client.call_async(request)
        future.add_done_callback(self.zone_release_response_callback)

    def zone_release_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info(f'[TASK_EXEC] Zone lease released: {response.message}')
                self.zone_lease_held = False
            else:
                self.get_logger().warn(f'[TASK_EXEC] Failed to release zone lease: {response.message}')
        except Exception as e:
            self.get_logger().error(f'[TASK_EXEC] Service call failed: {e}')

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f'[TASK_EXEC] task={self.current_task_msg.task_id} Navigation goal rejected by Nav2!')
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
            self.get_logger().error(f'[TASK_EXEC] task={self.current_task_msg.task_id} Navigation failed/aborted with status {status}. Leaving task for recovery.')
            self.reset_execution_state()

    def cancel_current_goal(self):
        if self.goal_handle:
            self.get_logger().info('[TASK_EXEC] Canceling current Nav2 goal...')
            self.goal_handle.cancel_goal_async()
            self.goal_handle = None

    def reset_execution_state(self):
        self.current_task_msg = None
        self.current_epoch = -1
        self.navigation_state = 'IDLE'
        self.goal_handle = None
        self.current_done_callback = None
        self.zone_lease_pending = False
        
        if hasattr(self, 'zone_retry_timer') and self.zone_retry_timer:
            self.zone_retry_timer.cancel()
            self.zone_retry_timer = None
            
        # Note: we do not reset zone_lease_held here because we might still hold the lease if we were interrupted.
        # However, if we are resetting the execution state, we should release the lease if we hold it.
        if self.zone_lease_held:
            self.get_logger().info('[TASK_EXEC] Releasing zone lease due to execution state reset.')
            self.release_zone_lease()
            self.zone_lease_held = False
        
        if getattr(self, 'task_queue', None) and len(self.task_queue) > 0:
            next_task = self.task_queue.pop(0)
            self.get_logger().info(f'[TASK_EXEC] Dequeued task {next_task.task_id} for execution. Remaining in queue: {len(self.task_queue)}')
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
