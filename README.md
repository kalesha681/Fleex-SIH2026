# FLEEX: Edge-AI Based Distributed Fleet Coordination for Autonomous Mobile Robots in Smart Warehouses

> **Smart India Hackathon 2026**

---

## Abstract

The rapid adoption of Autonomous Mobile Robots (AMRs) in warehouse logistics has exposed a fundamental architectural vulnerability in contemporary fleet management systems: centralized coordination servers constitute a single point of failure (SPOF) whose disruption can halt entire warehouse operations [[1]](#ref-1), [[2]](#ref-2). This paper presents **FLEEX** (*Fleet-Level Edge Execution*), a decentralized fleet coordination framework in which each AMR operates as an independent decision-making agent capable of peer-to-peer task allocation, autonomous failure detection, and distributed task recovery — without continuous dependence on a central coordinator. FLEEX employs the Zenoh protocol [[3]](#ref-3) for broker-free peer discovery, the Contract-Net Protocol [[4]](#ref-4) for distributed task auctions, epoch-tagged state vectors inspired by Conflict-Free Replicated Data Types (CRDTs) [[5]](#ref-5) for ownership conflict resolution, and a zone-lease mechanism for chokepoint mutual exclusion. The framework is validated through physics-accurate simulation in Gazebo Harmonic using three differential-drive AMRs navigating the AWS RoboMaker Small Warehouse environment with the Nav2 navigation stack [[6]](#ref-6). Human-in-the-loop runtime experiments demonstrate successful distributed task allocation, heartbeat-based failure detection, autonomous task recovery with zombie-node suppression, and chokepoint lease coordination across all verified scenarios.

**Keywords:** Autonomous Mobile Robots, Decentralized Fleet Management, Multi-Robot Systems, Peer-to-Peer Coordination, Contract-Net Protocol, Fault Tolerance, Warehouse Automation, ROS 2, Zenoh, Nav2.

---

## 1. Introduction

### 1.1 Problem Statement

Modern smart warehouses increasingly depend on fleets of AMRs for material transport, order picking, and inventory management. Industry-standard fleet management systems — including those conforming to the VDA 5050 specification — typically employ a centralized master controller that maintains global state, computes optimal assignments, and dispatches commands to individual robots [[1]](#ref-1). While this architecture simplifies coordination logic, it introduces several well-documented limitations:

1. **Single Point of Failure.** If the central server crashes or becomes unreachable, the entire fleet loses its coordination authority and halts [[2]](#ref-2).
2. **Scalability Bottleneck.** As fleet size grows, the central server must process an increasing volume of state updates, path computations, and conflict resolutions, creating a computational bottleneck [[7]](#ref-7).
3. **Network Fragility.** Robots that temporarily lose connectivity to the central server cannot receive new assignments or report task progress, even if they remain fully operational [[3]](#ref-3).

These limitations are particularly acute in real-world warehouse environments where network disruptions, hardware failures, and dynamic operational conditions are not exceptions but routine occurrences.

### 1.2 Proposed Approach

FLEEX addresses these limitations by restructuring fleet coordination as a **peer-to-peer system** in which each AMR is an autonomous agent equipped with:

- A **heartbeat subsystem** for distributed liveness detection (Section 4.1).
- A **Contract-Net auction engine** for decentralized task allocation without a central auctioneer (Section 4.2).
- An **epoch-based CRDT ownership model** for conflict resolution and task recovery (Section 4.3).
- A **zone-lease protocol** for chokepoint mutual exclusion with TTL-based deadlock prevention (Section 4.4).
- A **physical task executor** that bridges distributed state to Nav2 autonomous navigation (Section 4.5).

The central thesis is that **warehouse fleet coordination can operate without a continuously available central coordinator** if each robot independently participates in distributed allocation, monitors peer health, and recovers orphaned tasks upon detecting failures.

### 1.3 Contributions

This work makes the following contributions:

1. A complete decentralized fleet coordination architecture validated end-to-end in physics-accurate multi-robot simulation.
2. A distributed task recovery mechanism using epoch-tagged state vectors with explicit zombie-node suppression.
3. A zone-lease protocol for chokepoint mutual exclusion that integrates with Nav2 path planning through geometric intersection testing.
4. A reproducible open-source implementation built on ROS 2 Jazzy, Gazebo Harmonic, Zenoh, and Nav2.

---

## 2. Related Work

### 2.1 Centralized Fleet Management

The dominant paradigm in industrial AMR fleet management employs a centralized Fleet Management System (FMS) that acts as a global optimizer [[1]](#ref-1). Le-Anh and De Koster [[2]](#ref-2) provide a comprehensive survey of such systems, noting that centralized dispatching achieves near-optimal assignment quality but suffers from the single-point-of-failure problem. The VDA 5050 standard [[8]](#ref-8) — widely adopted in European intralogistics — formalizes a master–slave communication architecture in which a central "Master Control" issues orders to vehicles that report state updates. While effective in controlled environments, this architecture implicitly assumes continuous server availability.

### 2.2 Multi-Robot Task Allocation

The Multi-Robot Task Allocation (MRTA) problem has been extensively studied in the robotics literature. Gerkey and Matarić [[9]](#ref-9) provide a foundational taxonomy classifying MRTA problems along three axes: single-task vs. multi-task robots, single-robot vs. multi-robot tasks, and instantaneous vs. time-extended assignment. FLEEX addresses the simplest configuration (ST-SR-IA: single-task robots, single-robot tasks, instantaneous assignment), which is amenable to auction-based solutions.

Smith's Contract-Net Protocol [[4]](#ref-4) remains one of the most widely deployed distributed task allocation mechanisms. In Contract-Net, a manager announces a task, potential contractors submit bids based on local cost evaluations, and the manager selects the best bid. FLEEX adapts this protocol by **eliminating the centralized manager role**: every robot simultaneously acts as both a potential contractor and a local evaluator, independently arriving at the same winner through deterministic bid comparison.

### 2.3 Conflict-Free Replicated Data Types

CRDTs [[5]](#ref-5) provide a theoretical foundation for eventually consistent replicated state in distributed systems. Shapiro et al. [[5]](#ref-5) define two classes — state-based (CvRDTs) and operation-based (CmRDTs) — both guaranteeing convergence without coordination. FLEEX uses an epoch-tagged ownership model inspired by operation-based CRDTs: task state updates are idempotent, monotonically increasing epoch numbers resolve conflicts, and convergence is guaranteed as long as all updates are eventually delivered.

However, as Lamport [[10]](#ref-10) established, achieving strong consistency (e.g., mutual exclusion) in asynchronous distributed systems requires coordination primitives beyond eventual convergence. FLEEX therefore **deliberately separates convergent state (task ownership) from authoritative state (zone leases)**, using the appropriate consistency model for each concern.

### 2.4 Failure Detection

The FLP impossibility result [[11]](#ref-11) demonstrates that deterministic consensus is impossible in asynchronous systems with even one faulty process. Practical failure detectors, as formalized by Chandra and Toueg [[12]](#ref-12), provide probabilistic guarantees through heartbeat-based timeout mechanisms. FLEEX employs an unreliable failure detector in the ◇P (eventually perfect) class: heartbeat timeouts may produce false positives, but the epoch-based recovery mechanism ensures that erroneously recovered tasks are safely resolved through zombie yielding.

### 2.5 Multi-Robot Navigation

The Nav2 framework [[6]](#ref-6) provides a complete autonomous navigation stack for ROS 2, including global path planning (SMAC Planner [[13]](#ref-13)), local trajectory tracking (Regulated Pure Pursuit [[14]](#ref-14)), behavior trees, and lifecycle management. FLEEX leverages Nav2 without modification, treating it as an execution substrate for physically realizing the decisions made by the distributed coordination layer.

---

## 3. System Design

### 3.1 Architecture Overview

FLEEX follows a layered architecture in which each AMR runs identical software composed of three functional layers:

```text
┌─────────────────────────────────────────────────────────┐
│                  Communication Layer                     │
│         Zenoh P2P (rmw_zenoh_cpp) — No Broker           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Heartbeat   │  │  Heartbeat   │  │  Heartbeat   │    │
│  │  Publisher    │  │  Monitor     │  │  Liveness    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                  Coordination Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Task        │  │  Task        │  │  Zone        │    │
│  │  Bidder      │  │  Executor    │  │  Manager     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                  Execution Layer                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │     Nav2 (SMAC 2D + Regulated Pure Pursuit)      │    │
│  │     Costmaps · LiDAR · Static TF · Map Server    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Communication Model

All inter-robot communication occurs over the Zenoh middleware [[3]](#ref-3) via the `rmw_zenoh_cpp` ROS 2 middleware implementation. Zenoh provides:

- **Broker-free peer discovery** through multicast scouting, eliminating the DDS discovery server as a potential SPOF.
- **Wire-efficient pub/sub** with zero-copy data paths on shared-memory transports.
- **Router-based bridging** for multi-segment network topologies (validated in Phase 5.2 with explicit port-offset router configurations).

The choice of Zenoh over standard DDS is motivated by the architectural requirement that **no single network component should be necessary for local fleet operation**. If the optional Zenoh router fails, robots on the same network segment continue communicating via multicast.

### 3.3 Message Definitions

FLEEX defines the following ROS 2 interface types (package: `fleex_msgs`):

| Type | Name | Purpose |
| --- | --- | --- |
| Message | `Heartbeat.msg` | Liveness beacon: `robot_id`, `sequence`, `stamp` |
| Message | `Task.msg` | Distributed task state: `task_id`, `pickup_location`, `dropoff_location`, `state`, `owner_id`, `epoch` |
| Message | `TaskBid.msg` | Auction bid: robot ID, task ID, scalar cost |
| Message | `ZoneState.msg` | Zone occupancy state for observability |
| Message | `Lease.msg` | Zone lease grant with expiration time |
| Message | `RobotState.msg` | Operational status and current task |
| Service | `RequestZone.srv` | Zone lease request → grant/deny response |
| Service | `ReleaseZone.srv` | Explicit zone lease release |
| Service | `AssignTask.srv` | Reserved for WMS integration (not used in P2P allocation) |

---

## 4. Methodology

### 4.1 Heartbeat-Based Failure Detection

Each robot broadcasts a `Heartbeat.msg` at a configurable frequency (default: 1 Hz) containing a monotonically increasing sequence number and a timestamp. The `HeartbeatMonitor` node tracks the most recent heartbeat from each known peer and classifies peers as:

- **ALIVE:** Heartbeat received within the TTL window.
- **TIMED_OUT:** No heartbeat received for a duration exceeding the TTL.
- **RECOVERED:** A previously timed-out peer resumes heartbeat transmission.

Liveness transitions are published on `/fleex/peer_liveness` for consumption by the coordination layer. This failure detector corresponds to the ◇P (eventually perfect) class defined by Chandra and Toueg [[12]](#ref-12): it may temporarily suspect a correct process, but eventually only suspects genuinely failed processes.

### 4.2 Distributed Task Allocation

FLEEX implements a modified Contract-Net Protocol [[4]](#ref-4) with the following distinguishing characteristics:

1. **No Central Manager.** In the original Contract-Net, a designated manager announces tasks and selects winners. In FLEEX, tasks are broadcast on the `/fleex/tasks` topic by an external generator (simulating a WMS), and **every robot independently evaluates bids to determine the same winner**.

2. **Deterministic Winner Selection.** Each bidder computes a scalar cost based on:
   - A deterministic hash of (`robot_id`, `task_id`) providing a stable pseudo-distance.
   - A workload penalty of +1000.0 per currently owned active task, achieving autonomous load balancing.

   After a configurable `bid_collection_window` (default: 1.0s), each bidder sorts all received bids by cost (ascending), then by `robot_id` (lexicographic ascending) for tie-breaking. Because the bid function is deterministic and the input set is identical (all bids are broadcast), **all robots converge on the same winner without requiring a consensus protocol**.

3. **Distributed Ownership Commit.** The winning bidder publishes an `ASSIGNED` state update on `/fleex/tasks`. Other bidders validate this claim against their local auction records and accept it if consistent, establishing replicated ownership without a centralized database.

### 4.3 Task Recovery and Zombie Resolution

When the heartbeat monitor detects an owner timeout, the affected task enters a recovery pipeline:

```text
Owner heartbeat timeout
        ↓
Recovery grace period (5.0s)
        ↓
Task marked ELIGIBLE
        ↓
Secondary Contract-Net auction
        ↓
New owner selected (epoch incremented)
        ↓
Physical execution resumed
```

The `epoch` field in `Task.msg` serves as a **monotonic conflict-resolution vector** inspired by vector clocks and operation-based CRDTs [[5]](#ref-5). When a new owner claims a recovered task, it increments the epoch to `epoch + 1`. This provides two critical safety properties:

- **Zombie Bidding Protection.** A node that detects its own timeout (via its local heartbeat monitor observing the absence of its own heartbeats in peer acknowledgments) structurally blocks itself from participating in any future auctions.
- **Zombie Task Yielding.** If a partially failed node (zombie) receives a task update with a strictly higher epoch than its local copy, it immediately cancels its execution timeline and relinquishes ownership.

These mechanisms ensure that at most one robot physically executes a task at any given time, even under partial failure conditions.

### 4.4 Chokepoint Zone Reservation

Warehouse environments frequently contain narrow corridors and chokepoints where simultaneous traversal by multiple AMRs is physically impossible or hazardous. FLEEX addresses this through a zone-lease protocol:

1. **Zone Definition.** Chokepoints are defined in `config/warehouse/zones.yaml` as circular regions with center coordinates and entry/exit distances. The MVP defines one primary chokepoint (`choke_01`) at the warehouse's central corridor intersection at coordinates `(0, 0)` with a 2.0 m entry radius.

2. **Geometric Pre-Check.** Before issuing a Nav2 goal, the `TaskExecutor` performs a **circle-line intersection test** between the straight-line path segment (current position → goal) and each defined chokepoint circle. If intersection is detected, a lease request is issued before navigation begins.

3. **Lease Grant Semantics.** The `ZoneManager` maintains exclusive lease ownership. If a zone is unoccupied, the request is granted with a `Lease.msg` containing an expiration timestamp. If occupied, the request is denied. The executor retries asynchronously at configurable intervals.

4. **TTL-Based Expiration.** To prevent deadlocks from crashed leaseholders, leases automatically expire after a configurable TTL. This ensures that a robot failure during zone traversal does not permanently block the chokepoint.

5. **Explicit Release.** Upon completing zone traversal, the executor explicitly releases the lease via `ReleaseZone.srv`, making the zone immediately available to waiting robots.

### 4.5 Physical Task Execution

The `TaskExecutor` node orchestrates the physical realization of distributed task assignments:

```text
Task ASSIGNED (from bidder)
        ↓
Resolve pickup_location → PoseStamped (from locations.yaml)
        ↓
Check chokepoint intersection
        ↓
[If intersection] Request zone lease → Wait if denied
        ↓
Send Nav2 navigate_to_pose action goal
        ↓
Monitor Nav2 feedback (abort on epoch conflict)
        ↓
On arrival: release lease → advance to dropoff
        ↓
Navigate to dropoff (same intersection/lease logic)
        ↓
Publish COMPLETED state update
```

All 40+ semantic locations are defined in [`config/warehouse/locations.yaml`](config/warehouse/locations.yaml) with coordinates and approach headings extracted from the Gazebo world geometry. Navigation goals respect a 0.6 m safety clearance from static shelf faces, derived by parsing the original `.DAE` mesh bounding boxes from the Gazebo model library.

---

## 5. Experimental Setup

### 5.1 Simulation Environment

| Parameter | Value |
| --- | --- |
| Simulator | Gazebo Harmonic 8.15.0 |
| World | AWS RoboMaker Small Warehouse (`large_warehouse.world`) |
| Map Resolution | 0.05 m/cell (1000 × 1000 px = 50 × 50 m) |
| Physics | ODE, real-time factor ≈ 1.0 |
| Robot Model | Custom differential-drive AMR (`amr1.xacro`) |
| Footprint | 0.9 m × 0.64 m |
| Sensors | 2D GPU LiDAR (360°, bridged to ROS 2 `sensor_msgs/LaserScan`) |
| Fleet Size | 3 AMRs (`amr1`, `amr2`, `amr3`) |
| Spawn Positions | `(0, 0)`, `(0, 2)`, `(0, −2)` in map frame |

### 5.2 Software Configuration

| Component | Configuration |
| --- | --- |
| ROS 2 | Jazzy Jalisco |
| RMW | `rmw_zenoh_cpp` |
| Global Planner | SMAC 2D [[13]](#ref-13) |
| Local Controller | Regulated Pure Pursuit (RPP) [[14]](#ref-14) |
| Costmap Inflation | 0.55 m radius, exponential decay |
| Heartbeat TTL | Configurable (default: 3.0s) |
| Recovery Grace Period | 5.0s |
| Bid Collection Window | 1.0s |
| Workload Penalty | +1000.0 per active task |
| Zone Lease TTL | Configurable (per `zones.yaml`) |

### 5.3 Verification Methodology

All experiments follow a **human-in-the-loop** verification protocol. The AI development assistant is structurally prohibited from launching Gazebo simulations; all runtime behavior is observed and reported by the human operator. Results are classified as:

- **PASS:** Expected behavior observed and confirmed by human operator.
- **FAIL:** Unexpected behavior observed; root cause analyzed.
- **NOT VERIFIED:** Code implemented but runtime behavior not yet confirmed.

Complete verification records are maintained in [`dev/TEST_MATRIX.md`](dev/TEST_MATRIX.md).

---

## 6. Results

### 6.1 Summary of Verified Behaviors

| # | Capability | Verification Phase | Status |
| --- | --- | --- | --- |
| 1 | 3-AMR namespace isolation (cmd_vel, odom, TF, LiDAR) | Phase 1 | **PASS** |
| 2 | Zenoh P2P message flow across explicit router links | Phase 5.2 | **PASS** |
| 3 | Heartbeat timeout detection upon publisher failure | Phase 7.5 | **PASS** |
| 4 | Distributed Contract-Net winner convergence (no central auctioneer) | Phase 7.2 | **PASS** |
| 5 | Task lifecycle progression (UNASSIGNED → ASSIGNED → IN_PROGRESS → COMPLETED) | Phase 7.4 | **PASS** |
| 6 | Recovery auction with epoch increment after owner timeout | Phase 7.6 | **PASS** |
| 7 | Zombie node bidding suppression | Phase 7.6 | **PASS** |
| 8 | Zombie task yielding on higher epoch detection | Phase 7.6 | **PASS** |
| 9 | Single-robot Nav2 goal execution (SMAC 2D + RPP) | Phase 8.1 | **PASS** |
| 10 | Multi-robot simultaneous Nav2 navigation without TF conflicts | Phase 8.2 | **PASS** |
| 11 | Physical task execution (pickup → dropoff → COMPLETED) | Phase 8.5 | **PASS** |
| 12 | Fleet load balancing via workload penalty | Phase 8.7 | **PASS** |
| 13 | Zone lease grant and physical traversal | Phase 9 | **PASS** |
| 14 | Zone lease denial and safe waiting | Phase 9 | **PASS** |
| 15 | Zone lease TTL expiration and handoff | Phase 9 | **PASS** |
| 16 | Navigation failure → lease release → task recovery integration | Phase 9 | **PASS** |

### 6.2 Key Observations

**Distributed Winner Convergence.** In Phase 7.2 verification, both `amr1` and `amr2` independently computed the identical auction winner after receiving all bids over the Zenoh network. No central auctioneer or consensus protocol was required. This confirms that deterministic bid evaluation with a total ordering function is sufficient for consistent distributed allocation in small fleet sizes.

**Zombie Node Resolution.** During Phase 7.5 testing, an important edge case was discovered: killing only the `heartbeat_publisher` process while leaving the `task_bidder` running simulates a "one-way network partition" (zombie node). The zombie continued bidding on new tasks and progressing its assigned tasks despite being declared dead by the network. The epoch-based yielding mechanism introduced in Phase 7.6 successfully resolved this: zombie nodes abandon execution upon receiving a task update with a higher epoch number.

**Chokepoint Coordination Under Failure.** In Phase 9 testing, `amr2` obtained a zone lease for `choke_01` but subsequently experienced a Nav2 planning failure (SMAC 2D returned status 6 due to costmap geometry). The executor correctly: (a) aborted the navigation goal, (b) released the zone lease via `ReleaseZone.srv`, and (c) published the task back to the distributed network for recovery. This demonstrates that the lease and recovery mechanisms compose correctly under failure conditions.

### 6.3 Limitations and Unimplemented Features

The following capabilities are defined in the project roadmap but are **not implemented** in the current version:

| Feature | Status | Rationale for Deferral |
| --- | --- | --- |
| ORCA dynamic obstacle avoidance | Not implemented | Requires velocity-obstacle computation layer [[15]](#ref-15); Nav2's local planner provides basic obstacle avoidance |
| LightGBM edge inference | Not implemented | Requires offline training dataset from simulation logs; planned for congestion delay prediction |
| Independent software safety shield | Not implemented | Requires dedicated LiDAR processing node with velocity override authority |
| Central-server failure demonstration | Not implemented | Architecture supports it (fleet operates P2P); formal demo scenario not yet authored |
| Reproducible complete MVP demonstration | Implemented, not verified | Demo scripts authored (`scripts/demo/`); awaiting human runtime verification |

---

## 7. Discussion

### 7.1 Decentralization Trade-offs

FLEEX demonstrates that functional decentralized coordination is achievable for small warehouse fleets (3 robots) using relatively simple distributed protocols. However, the current implementation makes pragmatic architectural compromises:

- **Zone leases are centralized.** The `ZoneManager` is a single node that grants or denies zone access. While this is a deliberate design choice (mutual exclusion requires authoritative semantics that eventual consistency cannot provide [[10]](#ref-10)), it introduces a localized SPOF for the zone subsystem. Future work could replicate the `ZoneManager` across multiple robots using a lightweight consensus protocol.

- **Winner determination assumes reliable broadcast.** The Contract-Net convergence property relies on all bidders receiving all bids within the collection window. In the presence of network partitions, different subsets of robots may compute different winners. The epoch-based recovery mechanism provides eventual correctness but does not prevent temporary duplicate assignments.

### 7.2 Scalability Considerations

The current implementation has been validated with 3 robots. The broadcast-based communication model (all tasks and bids published to all robots) generates O(n²) message traffic per auction round, which may become prohibitive for large fleets. Potential mitigations include spatial partitioning of the task namespace, hierarchical auction structures, or gossip-based dissemination protocols.

### 7.3 Safety Disclaimer

The software safety mechanisms in FLEEX are intended for **simulation and architectural demonstration only**. They must not be characterized as certified industrial safety systems. Real-world deployment of AMRs requires certified safety scanners, hardware emergency-stop circuits, and compliance with applicable safety standards (e.g., ISO 3691-4).

---

## 8. Reproduction Guide

### 8.1 Prerequisites

| Dependency | Version |
| --- | --- |
| Ubuntu | 24.04 LTS |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic (8.x) |
| `rmw_zenoh_cpp` | Jazzy-compatible |
| Nav2 | Jazzy release |
| `ros_gz_bridge` | Jazzy release |
| Python | 3.12+ |

### 8.2 Build

```bash
cd ~/sih_fleex_workspace
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source env.sh
```

### 8.3 Running the Demonstration

A complete operator guide is provided in [`scripts/demo/README.md`](scripts/demo/README.md). The demonstration requires 6 terminals, each sourcing `env.sh`:

```bash
# Terminal 1 — Simulation
ros2 launch simulation bringup.launch.py

# Terminal 2 — Visualization
ros2 launch fleex_navigation rviz.launch.py

# Terminal 3 — Navigation (3× Nav2)
ros2 launch fleex_navigation fleet_navigation.launch.py

# Terminal 4 — Coordination (Heartbeats + Bidders + Executors + ZoneManager)
ros2 launch fleex_coordination fleet_coordination.launch.py

# Terminal 5 — Demo Tasks
python3 scripts/demo/demo_generator.py

# Terminal 6 — Trigger Failure (manual, after observing task execution)
ps aux | grep fleex_heartbeat_publisher | grep amr2
kill -9 <PID>
```

---

## 9. Repository Structure

```text
sih_fleex_workspace/
├── config/
│   ├── navigation/          # Nav2 parameters, maps, costmap configuration
│   ├── warehouse/           # Semantic locations (locations.yaml), zones (zones.yaml)
│   └── zenoh/               # Zenoh router and session configurations
├── dev/                     # Development memory (state, changelog, test matrix, roadmap)
├── docs/
│   ├── media/               # Demo recordings, architecture diagrams
│   ├── presentations/       # SIH pitch decks
│   └── references/          # Research papers and citations
├── scripts/demo/            # Reproducible MVP demonstration scripts
├── simulation/
│   ├── launch/              # Gazebo bringup and ROS-Gazebo bridge
│   ├── models/              # Gazebo model assets
│   ├── urdf/                # AMR robot description (Xacro)
│   └── worlds/              # large_warehouse.world
├── src/
│   ├── fleex_msgs/          # ROS 2 message and service definitions
│   ├── fleex_communication/ # Heartbeat publisher, monitor, peer liveness
│   ├── fleex_coordination/  # Task bidder, executor, generator, zone manager
│   └── fleex_navigation/    # Nav2 launch, parameters, RViz configuration
├── env.sh                   # One-command environment setup
└── README.md                # This document
```

---

## 10. Conclusion

This work presents FLEEX, a decentralized fleet coordination framework for warehouse AMRs that eliminates the single-point-of-failure inherent in centralized fleet management architectures. Through a combination of Zenoh peer-to-peer communication, distributed Contract-Net auctions, epoch-based CRDT ownership resolution, heartbeat failure detection, and zone-lease chokepoint coordination, FLEEX enables three AMRs to autonomously allocate tasks, navigate a realistic warehouse environment, coordinate access to narrow corridors, and recover from robot failures — all without a continuously available central coordinator.

The framework is validated through 16 distinct runtime experiments (all PASS) conducted in a physics-accurate Gazebo simulation with human-in-the-loop verification. Future work will incorporate LightGBM edge inference for congestion-aware bid cost adjustment, ORCA-based local collision avoidance [[15]](#ref-15), and formal central-server failure demonstration scenarios.

---

## References

<a id="ref-1"></a>**[1]** M. De Ryck, M. Versteyhe, and F. Debrouwere, "Automated guided vehicle systems, state-of-the-art control algorithms and techniques," *Journal of Manufacturing Systems*, vol. 54, pp. 152–173, 2020.

<a id="ref-2"></a>**[2]** T. Le-Anh and M. B. M. De Koster, "A review of design and control of automated guided vehicle systems," *European Journal of Operational Research*, vol. 171, no. 1, pp. 1–23, 2006.

<a id="ref-3"></a>**[3]** Eclipse Zenoh Contributors, "Zenoh: Zero Overhead Pub/Sub, Store/Query and Compute," Eclipse Foundation, 2024. Available: [https://zenoh.io](https://zenoh.io)

<a id="ref-4"></a>**[4]** R. G. Smith, "The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver," *IEEE Transactions on Computers*, vol. C-29, no. 12, pp. 1104–1113, 1980.

<a id="ref-5"></a>**[5]** M. Shapiro, N. Preguiça, C. Baquero, and M. Zawirski, "Conflict-Free Replicated Data Types," in *Proc. 13th International Symposium on Stabilization, Safety, and Security of Distributed Systems (SSS)*, Springer, 2011, pp. 386–400.

<a id="ref-6"></a>**[6]** S. Macenski, F. Martín, R. White, and J. G. Clavero, "The Marathon 2: A Navigation System," in *Proc. IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*, 2020.

<a id="ref-7"></a>**[7]** G. A. Korsah, A. Stentz, and M. B. Dias, "A comprehensive taxonomy for multi-robot task allocation," *The International Journal of Robotics Research*, vol. 32, no. 12, pp. 1495–1512, 2013.

<a id="ref-8"></a>**[8]** VDA (Verband der Automobilindustrie), "VDA 5050 — Interface for the Communication between Automated Guided Vehicles (AGV) and a Master Control," Version 2.0, 2020.

<a id="ref-9"></a>**[9]** B. P. Gerkey and M. J. Matarić, "A Formal Analysis and Taxonomy of Task Allocation in Multi-Robot Systems," *The International Journal of Robotics Research*, vol. 23, no. 9, pp. 939–954, 2004.

<a id="ref-10"></a>**[10]** L. Lamport, "The Part-Time Parliament," *ACM Transactions on Computer Systems*, vol. 16, no. 2, pp. 133–169, 1998.

<a id="ref-11"></a>**[11]** M. J. Fischer, N. A. Lynch, and M. S. Paterson, "Impossibility of Distributed Consensus with One Faulty Process," *Journal of the ACM*, vol. 32, no. 2, pp. 374–382, 1985.

<a id="ref-12"></a>**[12]** T. D. Chandra and S. Toueg, "Unreliable Failure Detectors for Reliable Distributed Systems," *Journal of the ACM*, vol. 43, no. 2, pp. 225–267, 1996.

<a id="ref-13"></a>**[13]** S. Macenski, T. Moore, D. Lu, and A. Matz, "SMAC Planner," Nav2 Documentation, 2021. Available: [https://docs.nav2.org](https://docs.nav2.org)

<a id="ref-14"></a>**[14]** R. C. Coulter, "Implementation of the Pure Pursuit Path Tracking Algorithm," Carnegie Mellon University, Robotics Institute, Technical Report CMU-RI-TR-92-01, 1992.

<a id="ref-15"></a>**[15]** J. van den Berg, S. J. Guy, M. Lin, and D. Manocha, "Reciprocal n-Body Collision Avoidance," in *Proc. International Symposium on Robotics Research (ISRR)*, Springer, 2011, pp. 3–19.

---

## Team

**Team FLEEX** — Smart India Hackathon 2026

---

## License

This project is developed for the Smart India Hackathon 2026 competition. Licensing terms to be determined upon completion.
