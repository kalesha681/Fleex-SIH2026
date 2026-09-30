import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import Node

def generate_launch_description():
    robots = [
        {'name': 'amr1', 'x': '1.0', 'y': '3.0'},
        {'name': 'amr2', 'x': '-4.145', 'y': '-0.957'},
        {'name': 'amr3', 'x': '2.173', 'y': '-4.827'},
    ]

    nodes = []

    # Bridge arguments
    bridge_args = ['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock']
    remappings = []

    for robot in robots:
        name = robot['name']
        ns = name + '/'
        
        # 1. Generate URDF synchronously
        urdf_file = f"/tmp/{name}.urdf"
        xacro_cmd = f"xacro /home/cp-lab/sih_fleex_workspace/simulation/urdf/amr1.xacro sim_gz:=true two_d_lidar_enabled:=true robot_namespace:={ns}"
        urdf_content = os.popen(xacro_cmd).read()
        with open(urdf_file, 'w') as f:
            f.write(urdf_content)

        # 2. Spawn robot
        nodes.append(Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-world', 'default',
                '-name', name,
                '-file', urdf_file,
                '-x', robot['x'],
                '-y', robot['y'],
                '-z', '0.1'
            ],
            output='screen'
        ))

        # 2.5 Robot State Publisher
        nodes.append(Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace=name,
            output='screen',
            parameters=[{
                'robot_description': urdf_content, 
                'use_sim_time': True,
                'frame_prefix': ns
            }],
            remappings=[
                ('/tf', f'/{name}/tf'),
                ('/tf_static', f'/{name}/tf_static')
            ]
        ))

        # 3. Add to bridge
        bridge_args.extend([
            f'/model/{name}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            f'/model/{name}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            f'/model/{name}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            f'/model/{name}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            f'/world/default/model/{name}/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
        ])
        
        # Remap Gazebo topics to ROS namespaces
        remappings.extend([
            (f'/model/{name}/cmd_vel', f'/{name}/cmd_vel'),
            (f'/model/{name}/odom', f'/{name}/odom'),
            (f'/model/{name}/tf', f'/{name}/tf'),
            (f'/model/{name}/scan', f'/{name}/scan'),
            (f'/world/default/model/{name}/joint_state', f'/{name}/joint_states'),
        ])

    # 4. Bridge node
    nodes.append(Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        arguments=bridge_args,
        remappings=remappings,
        output='screen'
    ))

    return LaunchDescription(nodes)
