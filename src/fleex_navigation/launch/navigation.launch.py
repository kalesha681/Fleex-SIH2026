import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushROSNamespace

def launch_setup(context, *args, **kwargs):
    pkg_nav = get_package_share_directory('fleex_navigation')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    
    # Evaluate launch configurations
    namespace = LaunchConfiguration('namespace').perform(context)
    params_file = LaunchConfiguration('params_file').perform(context)
    map_yaml_file = LaunchConfiguration('map').perform(context)
    
    # 1. Dynamically rewrite the params file to replace 'amr1' with the target namespace
    with open(params_file, 'r') as f:
        params_content = f.read()
        
    params_content = params_content.replace('amr1', namespace)
    
    rewritten_params_file = f'/tmp/nav2_params_{namespace}.yaml'
    with open(rewritten_params_file, 'w') as f:
        f.write(params_content)

    # 2. Static transform: map -> namespace/odom
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        namespace=namespace,
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'map',
            '--child-frame-id', f'{namespace}/odom'
        ],
        output='screen',
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')]
    )
    
    # 3. Nav2 navigation stack
    nav2_navigation = GroupAction([
        PushROSNamespace(namespace),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_nav2_bringup, 'launch', 'navigation_launch.py')
            ),
            launch_arguments={
                'namespace': namespace,
                'use_sim_time': 'True',
                'params_file': rewritten_params_file,
                'autostart': 'True',
                'use_composition': 'False'
            }.items()
        )
    ])
    
    # 4. Map server
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        namespace=namespace,
        output='screen',
        parameters=[{'yaml_filename': map_yaml_file, 'use_sim_time': True}],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')]
    )
    
    # 5. Lifecycle manager for map server
    lifecycle_manager_map = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        namespace=namespace,
        output='screen',
        parameters=[{'use_sim_time': True},
                    {'autostart': True},
                    {'node_names': ['map_server']}]
    )
    
    return [static_tf_node, nav2_navigation, map_server_node, lifecycle_manager_map]

def generate_launch_description():
    pkg_nav = get_package_share_directory('fleex_navigation')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(pkg_nav, 'config', 'navigation', 'nav2_params.yaml'),
            description='Full path to the ROS2 parameters file to use for all launched nodes'),
            
        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(pkg_nav, 'maps', 'warehouse.yaml'),
            description='Full path to map yaml file to load'),
            
        DeclareLaunchArgument(
            'namespace',
            default_value='amr1',
            description='Top-level namespace'),
            
        OpaqueFunction(function=launch_setup)
    ])
