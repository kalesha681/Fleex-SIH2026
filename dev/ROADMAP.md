# FLEEX — Development Roadmap

## Project

FLEEX — Edge-AI Based Distributed Fleet Coordination for AMRs in Smart Warehouses

---

## 0. Roadmap Principle

The primary goal is to build a **working FLEEX MVP** quickly and reliably.

The roadmap is divided into:

1. **MVP** — required for the first working demonstration
2. **Post-MVP** — advanced protocol hardening and additional capabilities
3. **Evaluation** — research-grade benchmarking and experiments

Post-MVP and Evaluation work must **not block the MVP**.

The development approach is bottom-up:

```text
Simulation
    ↓
ROS 2 foundation
    ↓
Multi-robot system
    ↓
Zenoh communication
    ↓
Task allocation
    ↓
Navigation
    ↓
Traffic coordination
    ↓
Failure recovery
    ↓
Edge AI
    ↓
Safety
    ↓
Full MVP integration
```

Every major MVP phase should end with a working test.

---

## MVP BOUNDARY

The MVP ends at:

```text
Phase 16 — Full MVP Integration
```

Everything after Phase 16 is optional post-MVP or evaluation work.

## MVP must demonstrate

1. Existing warehouse simulation running
2. 2–3 AMRs operating together
3. Peer-to-peer communication through Zenoh
4. Robot heartbeat and failure detection
5. Distributed task allocation
6. Basic task recovery after robot failure
7. Basic chokepoint/zone reservation
8. LightGBM edge inference
9. Nav2 navigation
10. Basic ORCA local collision avoidance
11. Basic independent software safety shield
12. Central server failure without complete fleet shutdown

## MVP priorities

The MVP prioritizes **working end-to-end behavior** over advanced
distributed-systems features.

Do not block the MVP on:

- Full CRDT implementation
- Advanced multi-zone atomic transactions
- Complex partition reconciliation
- Advanced lease semantics
- Large-scale benchmarking
- Statistical analysis
- Hardware safety certification

---

## PART A — MVP

## Phase 0 — Project Foundation

## Phase 0 Goal

Prepare the repository and development memory system.

### Phase 0 Tasks

- [x] Create FLEEX repository
- [x] Create `dev/` memory system
- [x] Define FLEEX architecture
- [x] Define MVP
- [x] Identify existing warehouse world
- [x] Identify existing AMR model
- [x] Create `CURRENT_STATE.md`
- [ ] Complete development memory documentation
- [ ] Create architecture decision records

### Phase 0 Exit Condition

The project structure, MVP boundary, and architecture constraints are
documented.

---

## Phase 1 — Simulation Foundation

## Phase 1 Goal

Get one AMR running reliably inside the existing warehouse simulation.

### Phase 1 Existing Assets

Primary world:

```text
simulation/worlds/large_warehouse.world
```

Primary AMR:

```text
simulation/urdf/amr1.xacro
```

### Phase 1 Tasks

- [x] Verify ROS 2 Jazzy
- [x] Verify Gazebo Harmonic
- [x] Launch `large_warehouse.world`
- [x] Spawn `amr1`
- [x] Verify robot TF
- [x] Verify odometry
- [x] Verify LiDAR
- [x] Verify `/cmd_vel`
- [x] Verify robot movement

### Phase 1 Tests

```text
T01 — Warehouse launches
T02 — AMR spawns
T03 — Sensors publish
T04 — AMR responds to velocity commands
```

### Phase 1 Exit Condition

One AMR can spawn, sense, move, and publish the required robot state.

---

## Phase 2 — FLEEX ROS 2 Package Foundation

## Phase 2 Goal

Create the software structure for FLEEX.

### Phase 2 Packages

```text
fleex_msgs
fleex_communication
fleex_coordination
fleex_edge_ai
fleex_navigation
fleex_safety
```

### Phase 2 Tasks

- [ ] Create ROS 2 workspace structure
- [ ] Create `fleex_msgs`
- [ ] Create `fleex_communication`
- [ ] Create `fleex_coordination`
- [ ] Create `fleex_edge_ai`
- [ ] Create `fleex_navigation`
- [ ] Create `fleex_safety`
- [ ] Verify clean `colcon build`

### Phase 2 Exit Condition

All FLEEX packages build successfully and can be sourced.

---

## Phase 3 — FLEEX Message Definitions

## Phase 3 Goal

Define the minimum data interfaces required by the MVP.

### Phase 3 Initial Messages

```text
RobotState
Task
TaskBid
ZoneState
Lease
```

### Phase 3 Initial Services

```text
RequestZone
AssignTask
```

### Phase 3 Tasks

- [ ] Define robot state
- [ ] Define task
- [ ] Define task bid
- [ ] Define zone state
- [ ] Define lease
- [ ] Define zone request
- [ ] Define task assignment
- [ ] Build and verify messages

### Phase 3 Exit Condition

FLEEX nodes can communicate using the required ROS 2 interfaces.

---

## Phase 4 — Multi-Robot Simulation

## Phase 4 Goal

Run multiple AMRs in the same warehouse.

### Phase 4 Initial Fleet

```text
AMR 1
AMR 2
AMR 3
```

### Phase 4 Tasks

- [ ] Spawn multiple AMRs
- [ ] Give each robot a unique namespace
- [ ] Verify unique TF trees
- [ ] Verify unique sensor topics
- [ ] Verify unique command topics
- [ ] Verify independent robot control

### Phase 4 Exit Condition

2–3 AMRs can operate independently in the same simulation.

---

## Phase 5 — Zenoh Communication

## Phase 5 Goal

Establish peer-to-peer communication between AMRs.

### Phase 5 Technology

```text
Zenoh
ROS 2
rmw_zenoh_cpp
```

### Phase 5 MVP Functions

- [x] Configure Zenoh
- [x] Verify peer discovery
- [x] Implement robot heartbeat
- [x] Exchange robot state
- [x] Detect missing heartbeat
- [x] Implement heartbeat TTL
- [x] Verify communication without a central coordinator

### Phase 5 Tests

```text
T05 — Peer discovery
T06 — Heartbeat
T07 — Peer failure detection
```

### Phase 5 Exit Condition

AMRs can exchange essential state directly through the edge network.

---

## Phase 6 — Minimal Task Generator

## Phase 6 Goal

Create a lightweight WMS/task-source simulator.

This is not a complete WMS.

It only generates warehouse tasks required to demonstrate FLEEX.

### Phase 6 Tasks

- [ ] Generate pickup/drop tasks
- [ ] Assign unique task IDs
- [ ] Publish tasks to FLEEX
- [ ] Track task state
- [ ] Simulate central server availability
- [ ] Simulate central server failure

### Phase 6 Exit Condition

FLEEX receives realistic warehouse tasks without requiring a real WMS.

---

## Phase 7 — Distributed Task Allocation

## Phase 7 Goal

Implement decentralized task allocation.

### Phase 7 Mechanism

```text
Contract-Net / distributed auction
```

### Phase 7 Flow

```text
Task announced
      ↓
Robots calculate local cost
      ↓
Robots submit bids
      ↓
Winner selected
      ↓
Task assigned
      ↓
Robot executes task
```

### Phase 7 Initial Cost Factors

```text
Distance
Traversal time
Battery penalty
Congestion penalty
Reassignment penalty
```

### Phase 7 MVP Tasks

- [ ] Implement task announcement
- [ ] Implement bid generation
- [ ] Implement bid collection
- [ ] Implement deterministic winner selection
- [ ] Implement task assignment
- [ ] Implement task state transitions
- [ ] Verify multiple tasks
- [ ] Verify no single fleet coordinator is required

### Phase 7 Exit Condition

Multiple robots can allocate tasks without a central fleet coordinator.

---

## Phase 8 — Navigation

## Phase 8 Goal

Make AMRs navigate autonomously through the warehouse.

### Phase 8 Navigation Stack

```text
Nav2
├── SMAC 2D
└── RPP
```

### Phase 8 Tasks

- [x] Create/verify warehouse map
- [x] Configure localization (bypassed with static TF for MVP)
- [x] Configure Nav2
- [x] Configure SMAC 2D
- [x] Configure RPP
- [ ] Send navigation goals
- [ ] Verify successful navigation

### Phase 8 Exit Condition

A robot can autonomously navigate between defined warehouse locations.

---

## Phase 9 — Multi-Robot Traffic

## Phase 9 Goal

Create meaningful traffic scenarios.

### Phase 9 Scenarios

- [ ] Crossing paths
- [ ] Opposing traffic
- [ ] Following traffic
- [ ] Shared aisle
- [ ] Chokepoint approach

### Phase 9 Exit Condition

2–3 AMRs can generate realistic multi-robot traffic inside the warehouse.

---

## Phase 10 — Basic ORCA

## Phase 10 Goal

Add local multi-robot collision avoidance.

### Phase 10 Primary Inputs

```text
LiDAR
Robot position
Robot velocity
Nearby-agent state
```

Zenoh intent/state may be used as advisory information but must not be
the sole basis for immediate safety decisions.

### Phase 10 Tasks

- [ ] Implement ORCA interface
- [ ] Connect ORCA to local velocity control
- [ ] Test two-robot encounter
- [ ] Test crossing paths
- [ ] Test multiple robots
- [ ] Verify velocity limiting

### Phase 10 Important

ORCA is used for:

```text
Local collision avoidance
```

ORCA is not used as:

```text
Safety certification
Primary deadlock prevention
```

### Phase 10 Exit Condition

Robots can locally avoid each other in normal encounters.

---

## Phase 11 — Basic Zone Reservation

## Phase 11 Goal

Coordinate access to narrow warehouse zones.

### Phase 11 Initial MVP Protocol

Start simple:

```text
Robot requests zone
        ↓
Zone authority checks availability
        ↓
Lease granted
        ↓
Robot enters zone
        ↓
Robot traverses
        ↓
Robot completely exits
        ↓
Lease released
```

### Phase 11 MVP Tasks

- [ ] Define zone representation
- [ ] Define zone authority
- [ ] Implement zone request
- [ ] Implement lease grant
- [ ] Implement lease release
- [ ] Implement basic lease TTL
- [ ] Test two robots competing for one zone
- [ ] Test robot waiting for occupied zone

### Phase 11 Important

For the MVP, implement the simplest reliable single-zone case first.

Advanced multi-zone acquisition is post-MVP.

### Phase 11 Exit Condition

Two robots cannot simultaneously enter the same controlled chokepoint
under normal operation.

---

## Phase 12 — Basic Task Recovery

## Phase 12 Goal

Recover a task when its assigned robot fails.

### Phase 12 MVP Flow

```text
Robot owns task
      ↓
Robot becomes unavailable
      ↓
Heartbeat expires
      ↓
Task recovery becomes possible
      ↓
Another robot claims task
      ↓
Task continues
```

### Phase 12 Tasks

- [x] Detect robot failure
- [x] Associate active task with robot
- [x] Add task recovery timeout
- [x] Make another robot eligible for recovery
- [x] Reassign task
- [ ] Test robot failure during execution
- [x] Prevent obvious duplicate execution

### Phase 12 Important

Do not implement the complete CRDT/partition reconciliation system yet.

The MVP only needs deterministic and safe-enough task recovery for the
demonstration scenario.

### Phase 12 Exit Condition

A task does not remain permanently stranded after the assigned robot
fails.

---

## Phase 13 — Central Server Failure

## Phase 13 Goal

Demonstrate the main FLEEX value proposition.

### Phase 13 Scenario

```text
Normal operation
      ↓
Central server available
      ↓
Tasks loaded at edge
      ↓
Central server fails
      ↓
Robots continue peer-to-peer
      ↓
Tasks continue
```

### Phase 13 Tasks

- [ ] Run normal operation
- [ ] Kill central task server
- [ ] Verify existing tasks remain available
- [ ] Verify Zenoh communication continues
- [ ] Verify task allocation continues
- [ ] Verify navigation continues
- [ ] Restore server
- [ ] Verify basic state reconciliation

### Phase 13 Exit Condition

Central server failure does not completely stop local fleet operation.

---

## Phase 14 — LightGBM Edge AI

## Phase 14 Goal

Use local AI inference to account for warehouse congestion during
task allocation.

### Phase 14 Target

Predict expected traversal time/delay through warehouse zones.

### Phase 14 Initial Features

```text
Zone occupancy
Mean/min velocity
Queue length
Inflow rate
Outflow rate
Recent traversal time
Recent congestion trend
Task demand
Zone geometry
```

### Phase 14 Tasks

- [ ] Generate simulation traffic data
- [ ] Build training dataset
- [ ] Define prediction target
- [ ] Train LightGBM model
- [ ] Validate using held-out simulation runs
- [ ] Export model
- [ ] Implement local feature extraction
- [ ] Implement inference node
- [ ] Integrate prediction into task-bid cost
- [ ] Verify inference latency

### Phase 14 MVP Simplification

Training is offline.

Inference runs locally at the edge.

The first model does not need to be highly sophisticated. It must
demonstrate that local AI predictions influence task allocation.

### Phase 14 Exit Condition

A robot can locally predict congestion/traversal delay and use the
prediction in its task bid.

---

## Phase 15 — Basic Safety Shield

## Phase 15 Goal

Add an independent software safety demonstration.

### Phase 15 Flow

```text
LiDAR
   ↓
Safety monitor
   ↓
Protective field
   ↓
Velocity override
   ↓
STOP
```

### Phase 15 Tasks

- [ ] Implement protective field
- [ ] Implement speed-dependent stopping logic
- [ ] Implement velocity override
- [ ] Verify safety node can override navigation
- [ ] Test static obstacle
- [ ] Test moving obstacle

### Phase 15 Important

The software safety shield is a simulation/architecture demonstration.

Do not claim industrial safety certification.

Actual industrial deployment would require the appropriate certified
safety scanner, controller, and hardware safety chain.

### Phase 15 Exit Condition

The independent software safety layer can stop the simulated robot
when a protective condition is violated.

---

## Phase 16 — Full MVP Integration

## Phase 16 Goal

Run the complete MVP as one reproducible system.

### Phase 16 Complete MVP Flow

```text
WMS / Task Generator
        ↓
Thin VDA 5050 / FastAPI boundary
        ↓
Edge Task State
        ↓
Contract-Net Auction
        ↓
AMRs
        │
        ├──── Zenoh P2P ────┐
        │                   │
        ├── Heartbeats      │
        ├── Task Recovery   │
        └── Zone Requests   │
                            │
        LightGBM ───────────┘
             ↓
           Nav2
             ↓
         SMAC 2D
             ↓
            RPP
             ↓
           ORCA
             ↓
       Safety Shield
```

### Phase 16 Final MVP Demonstrations

The system must demonstrate:

#### Demo 1 — Normal Operation

```text
Tasks arrive
↓
Robots bid
↓
Tasks assigned
↓
Robots navigate
↓
Tasks complete
```

#### Demo 2 — Central Server Failure

```text
Central server fails
↓
Robots remain connected through Zenoh
↓
Existing tasks continue
↓
New local allocation continues
```

#### Demo 3 — Robot Failure

```text
Robot fails
↓
Heartbeat expires
↓
Task becomes recoverable
↓
Another robot claims task
↓
Task continues
```

#### Demo 4 — Chokepoint

```text
Two robots approach same narrow zone
↓
Zone reservation
↓
One robot enters
↓
Other waits
↓
First exits
↓
Second enters
```

#### Demo 5 — Edge AI

```text
Congestion changes
↓
LightGBM predicts traversal delay
↓
Prediction affects bid cost
↓
Task allocation accounts for congestion
```

### Phase 16 MVP Exit Condition

FLEEX can demonstrate decentralized task coordination and recovery
during central-server failure while robots continue navigating and
coordinating in the warehouse.

---

## PART B — POST-MVP

Post-MVP features are **not required to demonstrate the initial FLEEX MVP**.

They can be implemented after the core system is stable.

---

## Phase 17 — Advanced Distributed Task Registry

## Phase 17 Goal

Strengthen replicated task state across the fleet.

### Phase 17 Possible Features

- [ ] CRDT-based task registry
- [ ] Replicated task existence
- [ ] Replicated task metadata
- [ ] Replicated task state
- [ ] Deterministic ownership conflict resolution
- [ ] Merge testing

### Phase 17 Constraint

CRDTs remain limited to task-state convergence.

They do not become authoritative zone lease mechanisms.

---

## Phase 18 — Advanced Zone Lease Protocol

## Phase 18 Goal

Harden the zone coordination protocol.

### Phase 18 Features

- [ ] Deterministic zone arbiter
- [ ] Membership-derived arbiter selection
- [ ] Monotonic lease epochs
- [ ] Lease acknowledgement
- [ ] Multi-zone acquisition
- [ ] Ascending zone ordering
- [ ] Provisional grants
- [ ] Commit
- [ ] Rollback
- [ ] Lease TTL recovery
- [ ] Egress-based release
- [ ] Wait-for graph for diagnostics/priority

### Phase 18 Important

Ascending acquisition order is the primary structural mechanism for
preventing circular wait.

The wait-for graph is primarily for diagnostics, telemetry, and
priority/aging.

---

## Phase 19 — Advanced Failure and Partition Handling

## Phase 19 Goal

Improve behavior under difficult network conditions.

### Phase 19 Features

- [ ] Temporary partition handling
- [ ] Task recovery grace periods
- [ ] Deterministic ghost-task claims
- [ ] Claimant/view epochs
- [ ] Partition reconciliation
- [ ] Lease epoch conflict handling
- [ ] Recovery testing after network healing

---

## PART C — EVALUATION / RESEARCH

These phases are performed only after the MVP is stable.

---

## Phase 20 — Baselines

Compare FLEEX against:

```text
Baseline 1:
Centralized VDA 5050-style dispatcher

Baseline 2:
Decentralized greedy nearest-robot allocation
```

Use comparable simulation conditions.

---

## Phase 21 — Large-Scale Evaluation

## Simulation

```text
Gazebo Harmonic
ROS 2 Jazzy
```

## Evaluation

Target:

```text
100 randomized seeds
```

### Phase 21 Metrics

- Makespan
- Throughput
- Collision rate
- Deadlock-recovery time
- Messages / robot / second
- Edge CPU usage
- Edge latency

### Phase 21 Reporting

Use:

- Median
- IQR
- 95% bootstrap percentile confidence intervals

For paired comparisons, use matched simulation seeds.

---

## Phase 22 — Ablation Studies

## Lease TTL

Example sweep:

```text
1 s
5 s
15 s
```

Values should be evaluated experimentally rather than assumed optimal.

## Network Conditions

Run:

```text
Link-loss / network-partition sweep
```

Measure the effect of communication degradation on:

- Task completion
- Recovery time
- Coordination
- Throughput
- Safety-related behavior

---

## Phase 23 — Performance Optimization

After functionality is stable:

- [ ] Measure CPU usage
- [ ] Measure memory usage
- [ ] Measure communication rate
- [ ] Measure inference latency
- [ ] Optimize unnecessary traffic
- [ ] Optimize edge inference
- [ ] Optimize ROS 2/Zenoh configuration
- [ ] Test larger fleet sizes

Optimization should be driven by measurements, not premature guesses.

---

## Phase 24 — Final Demonstration

The final demonstration should communicate one simple story:

```text
Central server works
        ↓
AMRs coordinate normally
        ↓
Central server fails
        ↓
AMRs continue peer-to-peer
        ↓
Tasks continue
        ↓
Robot failure occurs
        ↓
Another robot recovers the task
        ↓
AMRs coordinate a narrow zone
        ↓
Edge AI accounts for congestion
        ↓
Navigation + avoidance + safety continue
```

The demonstration should prioritize the actual failure-resilience
behavior rather than displaying a large number of disconnected features.

---

## Roadmap Status

## MVP

```text
Phase 0   Project Foundation          [IN PROGRESS]
Phase 1   Simulation Foundation       [NOT STARTED]
Phase 2   ROS 2 Packages              [NOT STARTED]
Phase 3   Message Definitions         [NOT STARTED]
Phase 4   Multi-Robot Simulation      [NOT STARTED]
Phase 5   Zenoh + Heartbeat           [NOT STARTED]
Phase 6   Task Generator              [NOT STARTED]
Phase 7   Distributed Allocation      [IMPLEMENTING]
Phase 8   Navigation                  [NOT STARTED]
Phase 9   Multi-Robot Traffic         [NOT STARTED]
Phase 10  Basic ORCA                  [NOT STARTED]
Phase 11  Basic Zone Reservation      [NOT STARTED]
Phase 12  Basic Task Recovery         [NOT STARTED]
Phase 13  Central Server Failure      [NOT STARTED]
Phase 14  LightGBM Edge AI            [NOT STARTED]
Phase 15  Basic Safety Shield         [NOT STARTED]
Phase 16  Full MVP Integration         [NOT STARTED]
```

## Post-MVP

```text
Phase 17  Advanced Task Registry       [NOT STARTED]
Phase 18  Advanced Zone Leases         [NOT STARTED]
Phase 19  Partition/Failure Handling   [NOT STARTED]
```

## Part C — Evaluation

```text
Phase 20  Baselines                   [NOT STARTED]
Phase 21  Large-Scale Evaluation      [NOT STARTED]
Phase 22  Ablation Studies             [NOT STARTED]
Phase 23  Performance Optimization     [NOT STARTED]
Phase 24  Final Demonstration          [NOT STARTED]
```

---

## Definition of MVP Done

FLEEX MVP is complete when all of the following are working:

- [ ] 2–3 AMRs operate in the warehouse
- [ ] AMRs communicate peer-to-peer through Zenoh
- [ ] Heartbeats detect robot failure
- [ ] Tasks can be allocated without a central fleet coordinator
- [ ] Failed-robot tasks can be recovered
- [ ] Robots coordinate a basic narrow/chokepoint zone
- [ ] LightGBM runs locally at the edge
- [ ] LightGBM prediction influences task allocation
- [ ] Robots navigate autonomously using Nav2
- [ ] ORCA provides local multi-robot collision avoidance
- [ ] Independent software safety logic can stop a robot in simulation
- [ ] Central server failure does not completely stop local fleet
  coordination
- [ ] The complete demonstration can be reproduced reliably

**MVP first. Hardening second. Research evaluation third.**
