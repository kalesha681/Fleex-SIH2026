import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    nodes = []

    # Launch Zone Manager (for zone reservation)
    nodes.append(
        Node(
            package='fleex_coordination',
            executable='fleex_zone_manager',
            name='fleex_zone_manager',
            output='screen',
        )
    )

    # Launch Task Generator
    # nodes.append(
    #     Node(
    #         package='fleex_coordination',
    #         executable='fleex_task_generator',
    #         name='fleex_task_generator',
    #         output='screen',
    #         parameters=[{'task_rate': 0.15}] # 1 task every ~6.6 seconds
    #     )
    # )

    # Launch Bidder and Executor for each AMR
    for amr in ['amr1', 'amr2', 'amr3']:
        nodes.append(
            Node(
                package='fleex_coordination',
                executable='fleex_task_bidder',
                name=f'task_bidder_{amr}',
                output='screen',
                parameters=[{'robot_id': amr}]
            )
        )
        nodes.append(
            Node(
                package='fleex_coordination',
                executable='fleex_task_executor',
                name=f'task_executor_{amr}',
                output='screen',
                parameters=[{'robot_id': amr}]
            )
        )

    return LaunchDescription(nodes)
