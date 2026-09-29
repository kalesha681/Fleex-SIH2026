import rclpy
from rclpy.node import Node
import yaml
import os
from fleex_msgs.msg import Lease, ZoneState
from fleex_msgs.srv import RequestZone, ReleaseZone
from builtin_interfaces.msg import Time
import time

class ZoneManager(Node):
    def __init__(self):
        super().__init__('fleex_zone_manager')
        
        # Declare parameters
        self.declare_parameter('zones_config_file', 'config/warehouse/zones.yaml')
        self.declare_parameter('zone_lease_ttl', 10.0)  # seconds
        
        # Get parameters
        zones_config_file = self.get_parameter('zones_config_file').value
        self.zone_lease_ttl = self.get_parameter('zone_lease_ttl').value
        
        # Load zones configuration
        self.zones = {}  # zone_id -> {center_x, center_y, radius, holder_id, expiration_time}
        self.load_zones(zones_config_file)
        
        # Service for requesting zone lease
        self.request_zone_service = self.create_service(
            RequestZone,
            '/fleex/request_zone',
            self.request_zone_callback
        )
        
        # Service for releasing zone lease
        self.release_zone_service = self.create_service(
            ReleaseZone,
            '/fleex/release_zone',
            self.release_zone_callback
        )
        
        # Publisher for zone state
        self.zone_state_pub = self.create_publisher(ZoneState, '/fleex/zone_state', 10)
        
        # Timer to periodically publish zone state and check for expired leases
        self.timer = self.create_timer(1.0, self.timer_callback)
        
        self.get_logger().info('[ZONE_MANAGER] Zone Manager initialized')
        self.get_logger().info(f'[ZONE_MANAGER] Loaded zones: {list(self.zones.keys())}')

    def load_zones(self, config_file):
        # Convert relative path to absolute if needed
        if not os.path.isabs(config_file):
            # Assume relative to the workspace root? We'll get the current working directory.
            # But note: the node might be launched from a different directory.
            # We'll try to find the file relative to the package share directory.
            # For simplicity, we'll assume the file is relative to the current working directory.
            # In a launch file, we can set the working directory or use an absolute path.
            pass
        
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            
            for zone_id, zone_config in data.get('zones', {}).items():
                center = zone_config.get('center', {'x': 0.0, 'y': 0.0})
                entry_dist = zone_config.get('entry_distance', 2.0)
                exit_dist = zone_config.get('exit_distance', 2.5)
                self.zones[zone_id] = {
                    'center_x': center.get('x', 0.0),
                    'center_y': center.get('y', 0.0),
                    'entry_distance': entry_dist,
                    'exit_distance': exit_dist,
                    'holder_id': None,
                    'expiration_time': None  # timestamp when lease expires
                }
                self.get_logger().info(f'[ZONE_MANAGER] Loaded zone {zone_id}: center=({center.get("x")}, {center.get("y")}), entry={entry_dist}, exit={exit_dist}')
        except Exception as e:
            self.get_logger().error(f'[ZONE_MANAGER] Failed to load zones config: {e}')
            # We'll still run but with no zones

    def request_zone_callback(self, request, response):
        robot_id = request.robot_id
        zone_id = request.zone_id
        
        self.get_logger().info(f'[ZONE_MANAGER] Received zone request from {robot_id} for zone {zone_id}')
        
        if zone_id not in self.zones:
            response.granted = False
            response.message = f'Zone {zone_id} not known'
            self.get_logger().warn(f'[ZONE_MANAGER] {response.message}')
            return response
        
        zone = self.zones[zone_id]
        now = time.time()
        
        # Check if the current lease has expired
        if zone['holder_id'] is not None and zone['expiration_time'] is not None:
            if now > zone['expiration_time']:
                self.get_logger().info(f'[ZONE_MANAGER] Lease for zone {zone_id} held by {zone["holder_id"]} has expired')
                zone['holder_id'] = None
                zone['expiration_time'] = None
        
        # Check if zone is free
        if zone['holder_id'] is None:
            # Grant lease
            zone['holder_id'] = robot_id
            zone['expiration_time'] = now + self.zone_lease_ttl
            response.granted = True
            response.message = f'Lease granted for {self.zone_lease_ttl} seconds'
            
            # Prepare lease message for response
            lease_msg = Lease()
            lease_msg.zone_id = zone_id
            lease_msg.holder_id = robot_id
            lease_msg.expiration = Time(sec=int(zone['expiration_time']), nanosec=int((zone['expiration_time'] % 1) * 1e9))
            response.lease = lease_msg
            
            self.get_logger().info(f'[ZONE_MANAGER] Granted lease for zone {zone_id} to {robot_id} (expires at {zone["expiration_time"]})')
        else:
            # Zone is occupied
            response.granted = False
            response.message = f'Zone {zone_id} is occupied by {zone["holder_id"]}'
            self.get_logger().info(f'[ZONE_MANAGER] {response.message}')
        
        return response

    def release_zone_callback(self, request, response):
        robot_id = request.robot_id
        zone_id = request.zone_id
        
        self.get_logger().info(f'[ZONE_MANAGER] Received zone release request from {robot_id} for zone {zone_id}')
        
        if zone_id not in self.zones:
            response.success = False
            response.message = f'Zone {zone_id} not known'
            return response
        
        zone = self.zones[zone_id]
        
        # Check if the requesting robot is the current holder
        if zone['holder_id'] == robot_id:
            zone['holder_id'] = None
            zone['expiration_time'] = None
            response.success = True
            response.message = f'Lease released for zone {zone_id}'
            self.get_logger().info(f'[ZONE_MANAGER] {response.message}')
        else:
            response.success = False
            if zone['holder_id'] is None:
                response.message = f'Zone {zone_id} is already free'
            else:
                response.message = f'Zone {zone_id} is held by {zone["holder_id"]}, not {robot_id}'
            self.get_logger().info(f'[ZONE_MANAGER] {response.message}')
        
        return response

    def timer_callback(self):
        now = time.time()
        # Check for expired leases and reclaim zones
        for zone_id, zone in self.zones.items():
            if zone['holder_id'] is not None and zone['expiration_time'] is not None:
                if now > zone['expiration_time']:
                    self.get_logger().info(f'[ZONE_MANAGER] Lease for zone {zone_id} held by {zone["holder_id"]} has expired (reclaiming)')
                    zone['holder_id'] = None
                    zone['expiration_time'] = None
        
        # Publish zone state
        zone_state_msg = ZoneState()
        # We need to publish a ZoneState message for each zone? Or one message per zone?
        # The ZoneState.msg has fields: zone_id, is_occupied, current_holder
        # We'll publish one message per zone on the same topic? Or we can have a topic per zone?
        # Let's publish one message per zone, but we need to differentiate them.
        # We can use the topic '/fleex/zone_state/<zone_id>' but that requires dynamic publishers.
        # Alternatively, we can publish a list of ZoneState messages? But the message definition is for a single zone.
        #
        # Let's change: we'll publish on '/fleex/zone_state' and the message will be for a single zone.
        # But then we need to publish multiple messages. We can publish in a loop and the subscriber will receive multiple messages.
        # However, the subscriber might not know which zone the message is for without the zone_id.
        # The ZoneState.msg already has zone_id, so we can publish one message per zone.
        #
        # We'll do: for each zone, create a ZoneState message and publish it.
        # But note: publishing multiple messages on the same topic in quick succession is okay.
        #
        # We'll break after publishing one message per timer call to avoid flooding? Or we can publish all zones in one timer call.
        # We'll publish all zones in the timer callback.
        #
        # However, note that the timer is set to 1.0 second, so publishing 1 message per zone per second is acceptable.
        #
        # Let's do:
        for zone_id, zone in self.zones.items():
            zone_state_msg = ZoneState()
            zone_state_msg.zone_id = zone_id
            zone_state_msg.is_occupied = zone['holder_id'] is not None
            zone_state_msg.current_holder = zone['holder_id'] if zone['holder_id'] is not None else ""
            self.zone_state_pub.publish(zone_state_msg)
        
        # We can also log the state for debugging
        # self.get_logger().debug(f'[ZONE_MANAGER] Published zone states')

def main(args=None):
    rclpy.init(args=args)
    node = ZoneManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
