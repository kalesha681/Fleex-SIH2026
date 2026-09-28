#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage

from rclpy.qos import QoSProfile, QoSDurabilityPolicy

class TFRelay(Node):
    def __init__(self):
        super().__init__('tf_relay')
        
        # QoS for tf_static needs to be TransientLocal
        qos_static = QoSProfile(depth=10, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        
        self.pub = self.create_publisher(TFMessage, '/tf', 10)
        self.pub_static = self.create_publisher(TFMessage, '/tf_static', qos_static)
        
        # Subscribe to all namespaced TF topics
        for i in range(1, 4):
            self.create_subscription(TFMessage, f'/amr{i}/tf', self.cb, 10)
            self.create_subscription(TFMessage, f'/amr{i}/tf_static', self.cb_static, qos_static)
            
    def cb(self, msg):
        self.pub.publish(msg)
        
    def cb_static(self, msg):
        self.pub_static.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = TFRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
