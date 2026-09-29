# FLEEX Project State

## Phase 7.4 Status: Distributed Task Lifecycle (COMPLETE & RUNTIME VERIFIED)

### Phase 7.4 Completed

- Decided to retain the current `Task.msg` untouched, utilizing the existing standard task topic (`/fleex/tasks`) as a distributed CRDT event bus for lifecycle progression without bloating the interfaces.
- Implemented logical execution lifecycle (`ASSIGNED` -> `IN_PROGRESS` -> `COMPLETED`) directly on the winning bidder using asynchronous ROS 2 timers.
- Added strict transition validity checks ensuring tasks can only move sequentially forward, blocking any backward state regression or illegal state jumps.
- Enforced task ownership rules: non-owners natively reject lifecycle mutation commands unless they match the locally evaluated initial owner of that task epoch.
- Handled idempotency: receipt of identical state transitions (via self-echoing or duplicates) are safely absorbed without duplicating timers or physical effects.
- Passed static and build validations.
- **Human-in-the-loop runtime verified** that the winning AMR autonomously advances the task state through the complete `0 -> 1 -> 2 -> 3` sequence, publishing each localized physical progression strictly back to the distributed network ledger.

## Phase 7.5 Status: Heartbeat-Aware Task Recovery Foundation (COMPLETE & RUNTIME VERIFIED)

### Phase 7.5 Completed

- Modified `HeartbeatMonitor` to publish standard peer liveness events to `/fleex/peer_liveness`.
- Integrated `TaskBidder` to observe liveness events and track peer timeouts.
- Implemented configurable `recovery_grace_period` (default 5.0s).
- Added logic where owner heartbeat timeout begins a "recovery pending" state but DOES NOT immediately reassign or alter task state.
- If owner remains disconnected past grace period, ASSIGNED/IN_PROGRESS tasks are marked internally as `ELIGIBLE` for recovery.
- Terminal tasks (COMPLETED/FAILED) remain terminal and are ignored for recovery.
- Original `owner_id` is retained until actual recovery assignment occurs (Phase 7.6).
- Passed Python syntax, build validation, and non-Gazebo node-level logic tests.
- **Human-in-the-loop runtime verified** that task timeouts correctly mark active tasks as `ELIGIBLE` after the grace period.
- **Identified Zombie Node Edge Case**: During simulation, we observed that simulating a failure via killing only the `fleex_heartbeat_publisher` leaves the `fleex_task_bidder` running (a "one-way network partition" or "Zombie Node"). This Zombie Node continues to blindly bid on new tasks and progress its assigned tasks even after the network declares it dead. This edgecase requires explicit conflict resolution and yielding logic in Phase 7.6.

## Phase 7.6 Status: Task Recovery Auction & Zombie Resolution (COMPLETE & RUNTIME VERIFIED)

### Phase 7.6 Completed

- Upgraded `Task.msg` with `epoch` field to act as a CRDT ownership conflict resolution vector.
- Allowed `task_bidder` to initiate secondary Contract-Net auctions for tasks that reach `ELIGIBLE` status.
- Implemented **Zombie Bidding Protection**: Nodes that track themselves as `TIMED_OUT` (via their local heartbeat monitor) structurally block themselves from participating in any task auctions.
- Implemented **Zombie Task Yielding**: Nodes automatically cancel local execution timelines and abandon ownership if they receive a task state update containing a strictly higher epoch number.
- Passed local Python logic verification, syntax static analysis, and build validation.
- **Human-in-the-loop runtime verified** using automated test script, confirming successful zombie yield and epoch incrementing.

## Phase 8.1 Status: Nav2 Navigation Foundation (COMPLETE & RUNTIME VERIFIED)

### Phase 8.1 Completed

- Created `fleex_navigation` package with `package.xml`, `CMakeLists.txt`.
- Authored `nav2_params.yaml` with all 10 Jazzy lifecycle nodes configured for `amr1` namespace:
  `controller_server`, `smoother_server`, `planner_server`, `route_server`, `behavior_server`,
  `velocity_smoother`, `collision_monitor`, `bt_navigator`, `waypoint_follower`, `docking_server`.
- Configured SMAC 2D as the global planner and Regulated Pure Pursuit (RPP) as the local controller.
- Set up synthetic warehouse map (`warehouse.pgm` 1000x1000 @ 0.05m/cell + `warehouse.yaml`).
- Created `navigation.launch.py` using `GroupAction + PushROSNamespace` to wrap `nav2_bringup/navigation_launch.py`.
- Static TF publisher: `map → amr1/odom` (bypasses AMCL for MVP).
- Standalone `map_server` + `lifecycle_manager_map` for map serving.
- Robot footprint: `0.9m x 0.64m` from URDF source of truth.
- All costmap scan topics point to `/amr1/scan`.
- Resolved TF Namespacing Issues:
  - `bringup.launch.py` now explicitly launches `robot_state_publisher` for each robot.
  - Added `frame_prefix` to prepend the robot namespace to all URDF frames (e.g., `amr1/base_footprint`).
  - Remapped `tf` and `tf_static` globally to the `/{name}/tf` namespaces in `bringup.launch.py` so Nav2 successfully receives the static transform tree.
- **Human-in-the-loop runtime verified** that AMR1 successfully executes a `navigate_to_pose` action in Gazebo.

## Phase 8.2 Status: Multi-Robot Nav2 Bringup (COMPLETE & RUNTIME VERIFIED)

### Phase 8.2 Completed
- The existing `navigation.launch.py` is fully parameterized to support any robot `namespace`.
- Identified and fixed a major TF tree conflict in `simulation/urdf/gz.xacro` where both `DiffDrive` (from `(0,0)`) and `OdometryPublisher` (from world coordinates) were simultaneously publishing `/odom` to `/base_footprint` TF data to the global TF tree.
- Configured `DiffDrive` to sink its Odometry and TF publishers to dummy topics when `odometry_source == 'world'`, ensuring a clean, single source of truth for the Nav2 local costmap.
- **Human-in-the-loop runtime verified** that `amr2` successfully navigates simultaneously without dropping lidar scans due to costmap bounds errors.

## Phase 8.5 Status: Task → Navigation Integration (COMPLETE & RUNTIME VERIFIED)

### Phase 8.5 Completed
- Created `fleex_task_executor.py` to bridge distributed Task CRDTs to physical Nav2 execution.
- Replaced timer-based lifecycle from `task_bidder.py` with physical state machine in `task_executor.py`.
- Developed string-to-PoseStamped coordinate mapping for standard warehouse locations.
- Nav2 goal requests are perfectly namespaced to the robot's local action server (`/{robot_id}/navigate_to_pose`).
- Task state ownership is rigidly maintained. Stale execution timelines are aborted natively when higher epochs dictate recovery/theft by a peer.
- Built and statically validated with zero errors. Wait for human-in-the-loop Gazebo test.

## Phase 8.6 Status: FLEEX RViz Visualization (IMPLEMENTED — NOT VERIFIED)

### Phase 8.6 Completed
- Added `fleex_navigation.rviz` configuration file to `fleex_navigation` package.
- Duplicated and adapted display arrays for AMR-1, AMR-2, and AMR-3 with distinct visual colors for LiDAR and Paths.
- Configured Global Costmap, Local Costmap, RobotModel, LaserScan, Global Plan, and Local Plan displays.
- Set fixed frame to `map` for top-down warehouse visualization.
- Deferred custom FLEEX Status Panel (cannot natively render `fleex_msgs/msg/Task` in standard RViz).
- Created `rviz.launch.py` to cleanly launch RViz without Gazebo.

## Phase 8.7 Status: Offset Math & Fleet Load Balancing (COMPLETE & RUNTIME VERIFIED)

### Phase 8.7 Completed
- Developed automated Python tools to parse 3D `.DAE` COLLADA meshes directly from Gazebo models to mathematically derive bounding box dimensions.
- Redefined all `locations.yaml` navigation goals to respect a precise `0.6m` safety clearance from the specific front face of each unique static shelf model, eliminating `status 6` collisions against inflation layers.
- Relocated `station_01` out of a physically trapped box of `ClutteringC_01` pallets.
- Implemented **Workload Penalty** in `fleex_task_bidder.py`. Bidders now add a massive `+1000.0` penalty for each currently owned active task, shifting the system from naive deterministic hashing to intelligent, autonomous fleet load balancing.
- Implemented a **Task Queue** in `fleex_task_executor.py` so a robot successfully sequences simultaneously assigned tasks instead of discarding them.
- **Human-in-the-loop runtime verified** that multiple tasks fired concurrently distribute successfully across the fleet. This surface-tested the limits of basic Nav2 and uncovered physical traffic contention (robots parking on top of each other's global paths), directly gating the entrance to Phase 9.

## Phase 9 Status: Minimal Zone Reservation / Chokepoint Coordination (COMPLETE & RUNTIME VERIFIED)

### Phase 9 Completed
- Designed MVP Central Chokepoint (`choke_01`) at `(x=0, y=0)` with 2.0m radius, covering the primary warehouse crossing corridor.
- Implemented `ZoneManager` node to manage requests (`RequestZone.srv`), releases (`ReleaseZone.srv`), TTL expiration, and publish `ZoneState.msg`.
- Integrated `zone_manager` into `fleet_coordination.launch.py`.
- Rewrote `TaskExecutor` to perform mathematical circle-line intersection testing against the chokepoint boundaries before ever requesting a Nav2 goal.
- Updated `TaskExecutor` to use an asynchronous retry timer for zone lease requests instead of thread-blocking or task-abandonment.
- Validated Python syntax and successfully built package `fleex_coordination`.
- **Human-in-the-loop runtime verified** that the logic perfectly evaluates straight-line path intersection. `amr1` was correctly denied a lease and waited safely. After lease expiration, `amr1` gained the lease, completed the navigation through the corridor, requested the lease again for its drop-off route, and successfully completed the task.
- **Human-in-the-loop runtime verified (Recovery Integration)**: `amr2` gained the lease first but its local Nav2 aborted path planning (due to costmap geometry). `amr2` successfully aborted execution, explicitly threw the task back to the distributed fleet for recovery (Phase 6), and cleanly released its zone lease, proving the full resilience of the FLEEX architecture!
