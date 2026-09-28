# To-Do

- [x] Phase 0: Verify ROS 2 and Gazebo environment.
- [x] Phase 0: Test loading `simulation/worlds/large_warehouse.world`.
- [x] Phase 0: Test spawning `simulation/urdf/amr1.xacro`.
- [x] Phase 0: Test Gazebo transport topics (`/cmd_vel`, `/odom`).
- [x] Phase 1: Implement ROS-Gazebo bridge (`ros_gz_bridge`).
- [x] Phase 1: Create a core launch file (`simulation/launch/bringup.launch.py` or similar).

## Phase 1: 3-AMR Simulation Foundation

- [x] amr1 spawns
- [x] amr2 spawns
- [x] amr3 spawns
- [x] amr1 has independent command interface
- [x] amr2 has independent command interface
- [x] amr3 has independent command interface
- [x] amr1 command does not move amr2/amr3
- [x] amr2 command does not move amr1/amr3
- [x] amr3 command does not move amr1/amr2
- [x] amr1 odometry is independent
- [x] amr2 odometry is independent
- [x] amr3 odometry is independent
- [x] TF frames are unique
- [x] all three robots operate simultaneously
- [x] no unexpected topic collisions# Changelog

- **Phase 0 Verification**:
  - Replaced `$(find fleex_simulation)` in `simulation/urdf/amr1.xacro` with absolute workspace path `/home/cp-lab/sih_fleex_workspace` to allow xacro generation without an active ROS package.
  - Sourced ROS 2 Jazzy and verified Gazebo Harmonic 8.15.0 works.
  - Confirmed `simulation/worlds/large_warehouse.world` loads (using `GZ_SIM_RESOURCE_PATH`).
  - Successfully ran `ros_gz_sim create` to spawn `amr1`.
  - Passed Gazebo-native movement tests via `gz topic`.
- **Phase 1 (Bridge Implementation)**:
  - Created `simulation/launch/bridge.launch.py` to launch `ros_gz_bridge`.
  - Successfully bridged `/cmd_vel` (ROS->GZ), `/odom` (GZ->ROS), `/model/amr1/tf` (GZ->ROS as `/tf`), and `/clock` (GZ->ROS).
  - Verified end-to-end command path from ROS 2 `/cmd_vel` -> Gazebo -> ROS 2 `/odom`.
- **Phase 1 (Three-AMR Simulation Foundation)**:
  - Parameterized `simulation/urdf/gz.xacro` to support unique `robot_namespace` parameters.
  - Developed `simulation/launch/bringup.launch.py` to synchronously spawn `amr1`, `amr2`, and `amr3`.
  - Configured `ros_gz_bridge` to bridge and remap isolated namespaces (`/amr1/cmd_vel`, `/amr1/odom`, `/amr1/tf`).
  - Human testing confirmed complete namespace, command, and odometry isolation for the 3-robot cluster.
  
## Phase 2: Zenoh P2P + Heartbeat

- [x] Create ROS 2 workspace structure.
- [x] Create `fleex_msgs` and define `Heartbeat.msg`.
- [x] Create `fleex_communication`.
- [ ] Create `fleex_coordination`.
- [ ] Create `fleex_edge_ai`.
- [ ] Create `fleex_navigation`.
- [ ] Create `fleex_safety`.
- [x] Verify clean `colcon build` for `fleex_msgs`.
