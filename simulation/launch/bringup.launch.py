import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import Node

def generate_launch_description():
    robots = [
        {'name': 'amr1', 'x': '0.0', 'y': '0.0'},
        {'name': 'amr2', 'x': '0.0', 'y': '2.0'},
        {'name': 'amr3', 'x': '0.0', 'y': '-2.0'},
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
        xacro_cmd = f"xacro /home/cp-lab/sih_fleex_workspace/simulation/urdf/amr1.xacro sim_gz:=true robot_namespace:={ns} > {urdf_file}"
        os.system(xacro_cmd)

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

        # 3. Add to bridge
        bridge_args.extend([
            f'/model/{name}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            f'/model/{name}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            f'/model/{name}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ])
        
        # Remap Gazebo topics to ROS namespaces
        remappings.extend([
            (f'/model/{name}/cmd_vel', f'/{name}/cmd_vel'),
            (f'/model/{name}/odom', f'/{name}/odom'),
            (f'/model/{name}/tf', f'/{name}/tf'),
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
