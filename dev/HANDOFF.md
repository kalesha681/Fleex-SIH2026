# Handoff

## Status
- **Phase 8.2** (Multi-Robot Nav2 Bringup): IMPLEMENTED — READY FOR HUMAN RUNTIME TEST
- **Previous**: Phase 8.1 (Nav2 Navigation Foundation): FULLY VERIFIED

## What Was Completed
- Added `robot_state_publisher` to `simulation/launch/bringup.launch.py`.
- Added `frame_prefix` to correctly namespace all URDF-derived frames (`amr1/base_footprint`, etc).
- Remapped `/tf` and `/tf_static` in the `robot_state_publisher` to isolate each robot's TF tree.
- Successfully verified that AMR1 can navigate.

## Architecture
```
map (static TF) → amrX/odom (Gazebo bridge) → amrX/base_footprint
                                                  ↓
                                           Nav2 Stack (amrX)
                                      ┌──────────────────┐
                                      │ SMAC 2D (global)  │
                                      │ RPP (local)       │
                                      │ collision_monitor  │
                                      │ behavior_server    │
                                      │ bt_navigator       │
                                      └──────────────────┘
                                                  ↓
                                          /amrX/cmd_vel
```

## Required Human Runtime Test

Since Phase 8.1 successfully proved the Nav2 stack works for `amr1`, we now need to verify that we can bring up Nav2 for `amr2` and `amr3` and navigate them simultaneously.

### IMPORTANT: Keep Gazebo Running!
If `./run_sim.sh` is already running in Terminal 1, you can keep it running.

### Terminal 2: Start Nav2 for AMR2
```bash
cd ~/sih_fleex_workspace
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch fleex_navigation navigation.launch.py namespace:=amr2
```
Wait for `Managed nodes are active`.

### Terminal 3: Send Goal to AMR2
```bash
source /opt/ros/jazzy/setup.bash
ros2 action send_goal /amr2/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 2.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

### Terminal 4: Send Goal to AMR1 (Simultaneously)
```bash
source /opt/ros/jazzy/setup.bash
ros2 action send_goal /amr1/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: 'map'}, pose: {position: {x: -2.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

### After Running, Report
- PASS/FAIL
- Did `amr2` successfully accept the goal and move to (2.0, 2.0)?
- Did `amr1` and `amr2` navigate independently without TF interference?

## Next Action
- If PASS: Mark Phase 8.2 VERIFIED, proceed to Phase 14 (Distributed Dispatch).
- If FAIL: Report terminal output for diagnosis.
