import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_nav = get_package_share_directory('fleex_navigation')
    nav_launch_file = os.path.join(pkg_nav, 'launch', 'navigation.launch.py')
    
    nodes = []
    
    for amr in ['amr1', 'amr2', 'amr3']:
        nodes.append(GroupAction([
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav_launch_file),
                launch_arguments={'namespace': amr}.items()
            )
        ]))
        
    return LaunchDescription(nodes)
