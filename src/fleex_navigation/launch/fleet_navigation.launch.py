import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_nav = get_package_share_directory('fleex_navigation')
    nav_launch_file = os.path.join(pkg_nav, 'launch', 'navigation.launch.py')
    
    nodes = []
    
    # Global map server
    map_yaml_file = os.path.join(pkg_nav, 'maps', 'warehouse.yaml')
    
    global_map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'yaml_filename': map_yaml_file, 'use_sim_time': True}],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')]
    )
    
    global_lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{'use_sim_time': True},
                    {'autostart': True},
                    {'node_names': ['map_server']}]
    )
    
    tf_relay_node = Node(
        package='fleex_navigation',
        executable='tf_relay.py',
        name='fleet_tf_relay',
        output='screen'
    )
    
    nodes.extend([global_map_server, global_lifecycle_manager, tf_relay_node])
    
    rviz_launch_file = os.path.join(pkg_nav, 'launch', 'rviz.launch.py')
    nodes.append(IncludeLaunchDescription(PythonLaunchDescriptionSource(rviz_launch_file)))
    
    for amr in ['amr1', 'amr2', 'amr3']:
        nodes.append(GroupAction([
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav_launch_file),
                launch_arguments={'namespace': amr}.items()
            )
        ]))
        
    return LaunchDescription(nodes)
