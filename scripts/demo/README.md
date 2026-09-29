# FLEEX MVP Final Demonstration

This guide outlines the steps to perform a reproducible human-in-the-loop demonstration of the FLEEX MVP.

## Demo Storyline

1. **Fleet Startup:** 3 AMRs spawn in the `large_warehouse.world`.
2. **Distributed Allocation:** `demo_generator.py` fires 3 tasks into the Zenoh network. The 3 AMRs bid using Contract-Net and resolve ownership completely decentralized.
3. **Simultaneous Navigation:** The 3 AMRs begin navigating. SMAC 2D and Regulated Pure Pursuit dynamically route them around static warehouse obstacles.
4. **Chokepoint Contention:** Tasks are engineered so paths cross `choke_01`. One AMR successfully obtains the lease; another AMR requests the lease, is denied, and waits safely.
5. **Robot Failure & Task Recovery:** The operator manually kills the heartbeat node of the robot executing a task. The network detects the timeout. The task enters the `ELIGIBLE` state. The remaining robots run a recovery auction, and the task is cleanly reassigned and completed.

*NOTE: ORCA DYNAMIC OBSTACLE AVOIDANCE — NOT YET IMPLEMENTED.*

## Prerequisites

Open **6 separate terminals**.
In EVERY terminal, ensure you source the workspace and the Zenoh environment script:

```bash
source install/setup.bash
source env.sh
```

## Execution Sequence

### Terminal 1: Simulation

```bash
# Load Gazebo and spawn 3 AMRs
ros2 launch simulation bringup.launch.py
```

### Terminal 2: RViz Visualization

Wait until Gazebo loads the warehouse.

```bash
ros2 launch fleex_navigation rviz.launch.py
```

*RViz Instructions:*

- Ensure `Global Map` is checked.
- Expand `AMR1`, `AMR2`, `AMR3` groups to verify RobotModel, LaserScan, and Path displays are checked.

### Terminal 3: Navigation Stack

Wait for RViz to initialize TF.

```bash
ros2 launch fleex_navigation fleet_navigation.launch.py
```

### Terminal 4: Distributed Coordination

```bash
ros2 launch fleex_coordination fleet_coordination.launch.py
```

### Terminal 5: Task Generation

Wait for the navigation map to fully load and the coordination nodes to initialize.

```bash
python3 scripts/demo/demo_generator.py
```

*Expected Behavior:*

- 3 demo tasks are published.
- Terminal 4 (Coordination) shows auction bids and assignments.
- Terminal 3 (Navigation) shows Nav2 action requests being accepted.
- In RViz, global paths will instantly calculate.
- If multiple robots cross `(0,0)`, you will see the `ZoneManager` grant a lease to one and deny the other. The denied robot will pause in RViz until the first one clears the chokepoint.

### Terminal 6: Triggering Failure & Recovery

Wait until an AMR (e.g., AMR2) is actively executing its task.
Locate its heartbeat process ID:

```bash
ps aux | grep fleex_heartbeat_publisher | grep amr2
```

Copy the PID (e.g., `12345`), and kill it:

```bash
kill -9 <PID>
```

*Expected Behavior:*

- Terminal 4 (Coordination) logs a `Heartbeat Timeout` for AMR2.
- The task belonging to AMR2 waits out the 5.0s `recovery_grace_period`.
- The task becomes `ELIGIBLE`.
- AMR1 and AMR3 detect the eligible task and conduct a recovery auction.
- The winner increments the task's epoch and assumes ownership.
- The winning AMR continues the physical execution to completion.
