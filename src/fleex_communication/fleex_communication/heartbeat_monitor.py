import rclpy
from rclpy.node import Node
from fleex_msgs.msg import Heartbeat

class HeartbeatMonitor(Node):
    def __init__(self):
        super().__init__('fleex_heartbeat_monitor')

        # Parameters
        self.declare_parameter('heartbeat_timeout', 2.0)
        self.declare_parameter('monitor_period', 1.0)

        self.heartbeat_timeout = self.get_parameter('heartbeat_timeout').value
        self.monitor_period = self.get_parameter('monitor_period').value

        # Subscription
        self.subscription_ = self.create_subscription(
            Heartbeat,
            'heartbeat',
            self.heartbeat_callback,
            10
        )

        # State tracking dictionary
        # Key: robot_id (str)
        # Value: dict {'state': 'ALIVE' | 'TIMED_OUT', 'last_seq': int, 'last_recv_time': rclpy.time.Time}
        self.peer_states = {}

        # Timer to check for timeouts
        self.timer_ = self.create_timer(self.monitor_period, self.timer_callback)

        self.get_logger().info(
            f'Heartbeat monitor initialized. '
            f'Timeout: {self.heartbeat_timeout}s, Check Period: {self.monitor_period}s.'
        )

    def heartbeat_callback(self, msg):
        robot_id = msg.robot_id
        seq = msg.sequence
        now = self.get_clock().now()

        if robot_id not in self.peer_states:
            # First time seeing this robot
            self.peer_states[robot_id] = {
                'state': 'ALIVE',
                'last_seq': seq,
                'last_recv_time': now
            }
            self.get_logger().info(f'[STATE TRANSITION] {robot_id} is now ALIVE (New Peer Detected).')
        else:
            peer = self.peer_states[robot_id]
            current_state = peer['state']

            # Check sequence monotonic progression (informational only)
            if seq <= peer['last_seq']:
                self.get_logger().warn(
                    f'Non-monotonic sequence from {robot_id}: received {seq}, expected > {peer["last_seq"]}'
                )

            if current_state == 'TIMED_OUT':
                # Robot has recovered
                peer['state'] = 'ALIVE'
                self.get_logger().info(f'[STATE TRANSITION] {robot_id} has RECOVERED (Heartbeats resumed).')
                self.get_logger().info(f'[STATE TRANSITION] {robot_id} is now ALIVE.')

            # Update tracking information
            peer['last_seq'] = seq
            peer['last_recv_time'] = now

    def timer_callback(self):
        now = self.get_clock().now()

        for robot_id, peer in self.peer_states.items():
            if peer['state'] == 'ALIVE':
                time_since_last_msg = (now - peer['last_recv_time']).nanoseconds / 1e9
                if time_since_last_msg > self.heartbeat_timeout:
                    peer['state'] = 'TIMED_OUT'
                    self.get_logger().warn(
                        f'[STATE TRANSITION] {robot_id} is now TIMED_OUT (No heartbeat for {time_since_last_msg:.2f}s).'
                    )


def main(args=None):
    rclpy.init(args=args)
    node = HeartbeatMonitor()

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
