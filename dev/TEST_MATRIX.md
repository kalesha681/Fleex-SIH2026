# Test Matrix

| Component | Sub-component | Test Command/Scenario | Expected Result | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Environment | ROS 2 Jazzy | `ros2 daemon start` | Daemon starts, CLI works | **PASS** | |
| Environment | Gazebo Harmonic | `gz sim --version` | Version 8.15.0 displayed | **PASS** | |
| Environment | Gazebo Launch | `gz sim simulation/worlds/large_warehouse.world` | World loads without crash | **PASS** | Requires `GZ_SIM_RESOURCE_PATH` |
| AMR | Spawn | `ros_gz_sim create` | AMR mesh and collision spawn | **PASS** | `simulation/urdf/amr1.xacro` verified |
| Bridge | `/cmd_vel` | `ros2 topic pub /cmd_vel` | Command forwarded to Gazebo | **PASS** | Single-robot verify |
| Bridge | `/odom` | `ros2 topic echo /odom` | Odometry published to ROS 2 | **PASS** | Single-robot verify |
| Fleet (Phase 1) | Spawn 3 AMRs | `simulation/launch/bringup.launch.py` | 3 robots spawn without collisions | **PASS** | Spawned at x=0, y=0, 2, -2 |
| Fleet (Phase 1) | Command Isolation | `ros2 topic pub /amr1/cmd_vel` | ONLY `amr1` moves | **PASS** | Verified dynamically |
| Fleet (Phase 1) | Odometry Isolation | `ros2 topic echo /amr1/odom` | `/amr1/odom` updates accurately | **PASS** | Verified dynamically |
| Fleet (Phase 1) | TF Isolation | `ros2 topic echo /amr1/tf` | Publishes `amr1/odom` -> `amr1/base_footprint` | **PASS** | Verified dynamically |
| Workspace (Phase 2) | fleex_msgs | `colcon build` | Package compiles successfully | **PASS** | Build successful |
| Interface (Phase 2) | Heartbeat.msg | `ros2 interface show` | Message fields render accurately | **PASS** | Build verified |
| Task Recovery (Phase 7.5) | Eligibility Logic | `python3 test_recovery_logic.py` | Task becomes ELIGIBLE after timeout | **PASS** | Automated node-level logic test |
| Task Recovery (Phase 7.5) | Liveness Integration | Simulation: kill heartbeat node of owner | `task_bidder` detects timeout and marks ELIGIBLE | **PASS** | Verified during physical runtime test |
| Task Recovery (Phase 7.6) | Recovery Auction | Simulation: surviving node recovers task | New owner resumes task at epoch+1 | **PENDING** | Requires human verification |
| Task Recovery (Phase 7.6) | Zombie Yield | Simulation: Zombie node yields to new owner | Zombie stops execution upon seeing newer epoch | **PASS** | Automated script `auto_test_7_6.sh` |
| Navigation (Phase 8.1) | Nav2 Foundation | `ros2 launch fleex_navigation navigation.launch.py namespace:=amr1` | Nav2 initializes with SMAC 2D and RPP | **PASS** | Successfully verified by human |
| Navigation (Phase 8.2) | Multi-Robot Nav2 | `ros2 action send_goal /amrX/...` simultaneously | All 3 AMRs navigate without TF conflicts | **PASS** | Successfully verified by human |
| Task Integration (Phase 8.5) | Physical Task Execution | WMS generates task -> Node bids/wins -> Drives to Pickup -> Drives to Dropoff -> COMPLETED | Task transitions natively based on physical completion | **PASS** | Successfully verified by human |
| Visualization (Phase 8.6) | RViz Fleet Configuration | `ros2 launch fleex_navigation rviz.launch.py` | RViz loads Map, TF, and 3 distinct AMR displays without clutter | **PASS** | Successfully verified by human |
| Zone Management (Phase 9) | Lease Request & Grant | Simulation: send cross-zone task to one robot | Robot stops before center corridor, requests zone, gets lease, crosses. | **PASS** | Successfully verified by human |
| Zone Management (Phase 9) | Lease Exclusion | Simulation: send cross-zone task to two robots | Robot 1 gets lease. Robot 2 waits safely outside until Robot 1 finishes crossing. | **PASS** | Successfully verified by human |
