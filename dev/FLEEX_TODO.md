# FLEEX — TODO

## Current Objective

Complete the simulation foundation and verify that the existing warehouse
and AMR work correctly before implementing FLEEX logic.

---

## NOW

## Simulation Foundation

- [ ] Verify ROS 2 Jazzy installation
- [ ] Verify Gazebo Harmonic installation
- [ ] Launch `worlds/large_warehouse.world`
- [ ] Verify warehouse loads without errors
- [ ] Spawn `urdf/amr1.xacro`
- [ ] Verify `amr1` appears correctly
- [ ] Verify TF tree
- [ ] Verify odometry
- [ ] Verify LiDAR
- [ ] Verify `/cmd_vel`
- [ ] Verify AMR movement

---

## NEXT

After the simulation foundation passes:

- [ ] Create FLEEX ROS 2 workspace
- [ ] Create `fleex_msgs`
- [ ] Create `fleex_communication`
- [ ] Create `fleex_coordination`
- [ ] Create `fleex_edge_ai`
- [ ] Create `fleex_navigation`
- [ ] Create `fleex_safety`
- [ ] Verify clean `colcon build`

---

## THEN

## Communication

- [ ] Configure Zenoh
- [ ] Spawn 2–3 AMRs
- [ ] Verify peer discovery
- [ ] Implement heartbeat
- [ ] Test robot failure detection

## Task Allocation

- [ ] Create minimal task generator
- [ ] Implement task message
- [ ] Implement Contract-Net bidding
- [ ] Implement deterministic winner selection
- [ ] Execute assigned task

## Navigation

- [ ] Create/verify warehouse map
- [ ] Configure Nav2
- [ ] Configure SMAC 2D
- [ ] Configure RPP
- [ ] Verify autonomous navigation

## Multi-Robot Coordination

- [ ] Create traffic scenarios
- [ ] Add basic ORCA
- [ ] Add basic zone reservation
- [ ] Test chokepoint conflict

## Failure Recovery

- [ ] Implement task ownership timeout
- [ ] Detect failed robot
- [ ] Recover failed robot's task
- [ ] Test robot failure during task execution

## Edge AI

- [ ] Generate traffic data
- [ ] Create LightGBM training dataset
- [ ] Train first LightGBM model
- [ ] Implement local inference
- [ ] Add congestion prediction to task cost

## Safety

- [ ] Implement basic LiDAR safety monitor
- [ ] Implement velocity override
- [ ] Test emergency stop behavior

---

## MVP INTEGRATION

Only start this section after the individual components work.

- [ ] Run normal fleet operation
- [ ] Simulate central server failure
- [ ] Verify local coordination continues
- [ ] Simulate robot failure
- [ ] Verify task recovery
- [ ] Simulate chokepoint conflict
- [ ] Verify zone reservation
- [ ] Verify LightGBM affects task allocation
- [ ] Verify navigation + ORCA + safety together
- [ ] Run complete MVP demonstration

---

## BLOCKED / WAITING

Nothing currently.

If something cannot proceed because another component is incomplete,
move it here and record the reason.

---

## COMPLETED

Move completed tasks here only after they have actually been tested.

Example:

- [x] Gazebo launches `large_warehouse.world`
- [x] `amr1` spawns successfully
- [x] LiDAR verified

Do not mark something complete merely because the code exists.

---

## Rules for This File

1. Keep the active list small.
2. Do not put the entire roadmap here.
3. Do not add speculative features.
4. Finish `NOW` before moving to `NEXT`.
5. A task is complete only after testing.
6. If blocked, move it to `BLOCKED / WAITING`.
7. After a meaningful milestone, update:
   - `CURRENT_STATE.md`
   - `TEST_MATRIX.md`
   - `HANDOFF.md`
   - `CHANGELOG.md` when appropriate

---

## Current Priority

```text
SIMULATION FOUNDATION
        ↓
ONE WORKING AMR
        ↓
MULTIPLE AMRs
        ↓
ZENOH
        ↓
TASK ALLOCATION
```

Do not jump ahead unless there is a specific reason.
