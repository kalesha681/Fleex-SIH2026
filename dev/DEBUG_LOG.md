# Debug Log

- `simulation/urdf/amr1.xacro` contained `$(find fleex_simulation)`. Since the `fleex_simulation` package was removed during cleanup, Xacro failed to process the file.
  - **Fix**: Used absolute paths (`/home/cp-lab/sih_fleex_workspace/simulation`) inside `amr1.xacro` to restore xacro compilation without recreating an unnecessary package.
- Gazebo initially failed to find warehouse models (`[Err] ... Unable to find uri[model://aws_robomaker...]`).
  - **Fix**: Exported `GZ_SIM_RESOURCE_PATH=/home/cp-lab/sih_fleex_workspace/simulation/models` before launching Gazebo.
- ROS 2 topics are not visible in `ros2 topic list`.
  - **Diagnosis**: No `ros_gz_bridge` is running. All topics (`/cmd_vel`, `/odom`, `/model/amr1/tf`) are strictly within the Gazebo domain (`gz topic -l`).
- Nav2 fails to activate with: `Failed to get "amrX/two_d_lidar"->"amrX/base_footprint" frame transform`.
  - **Diagnosis**: `robot_state_publisher` was completely missing from `bringup.launch.py`. When added, it published the non-namespaced URDF frame names to the global `/tf_static` topic, but Nav2 was configured to look for namespaced frames (`amr1/two_d_lidar`) on the local `/amr1/tf_static` topic.
  - **Fix**: Modified `bringup.launch.py` to: 1) Run `robot_state_publisher` for each robot, 2) Set `frame_prefix: ns` parameter to prepend namespaces to URDF frames, 3) Add remappings `('/tf', f'/{name}/tf')` and `('/tf_static', f'/{name}/tf_static')` so it targets the correct namespaced TF topics.
- Multi-robot Nav2 brings up successfully but local costmap continuously drops `amr2/scan` lidar rays claiming `Sensor origin at (-0.00, 1.92) is out of map bounds`. Controller aborts `navigate_to_pose`.
  - **Diagnosis**: Gazebo was running two conflicting odometry plugins simultaneously. `DiffDrive` was integrating from start `(0,0)` while `OdometryPublisher` tracked true world coords `(0, 2.0)`. The `tf_buffer` would grab `(0,0)` when updating the rolling costmap bounds (TimePointZero), but projected the lidar scan using the sensor timestamp matching `(0, 2.0)`.
  - **Fix**: Modified `simulation/urdf/gz.xacro` so that `DiffDrive` publishes Odometry and TF to `/dummy_odom` and `/dummy_tf` when `odometry_source == 'world'`. This ensures a single source of truth for the local costmap bounds in `amr2/odom`.
