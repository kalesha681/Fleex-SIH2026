import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    rviz_config_dir = os.path.join(
        get_package_share_directory('fleex_navigation'),
        'rviz',
        'fleex_navigation.rviz')

    nodes = []

    # RViz node
    nodes.append(Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_dir],
        output='screen'
    ))

    # Custom relay script to merge namespaced TFs into global TF for visualization
    nodes.append(Node(
        package='fleex_navigation',
        executable='tf_relay.py',
        name='fleet_tf_relay',
        output='screen'
    ))

    return LaunchDescription(nodes)
