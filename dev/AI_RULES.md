# FLEEX — AI Coding Rules

## Purpose

These rules apply to any AI coding assistant working on the FLEEX
repository.

The AI must preserve the existing architecture and continue from the
current project state instead of repeatedly redesigning the system.

---

## 1. Read Project State First

Before modifying code, always read:

```text
dev/CURRENT_STATE.md
dev/ROADMAP.md
dev/TODO.md
dev/HANDOFF.md
dev/AI_RULES.md
```

Then inspect the relevant source files before making changes.

Do not assume that a file, package, node, topic, service, or feature
exists just because it appears in the roadmap.

---

## 2. Current Source of Truth

The current simulation assets are:

```text
World:
simulation/worlds/large_warehouse.world

AMR:
simulation/urdf/amr1.xacro
```

Supporting Xacro files:

```text
simulation/urdf/gz.xacro
simulation/urdf/macros.xacro
simulation/urdf/materials.xacro
```

Do not replace these assets unless explicitly instructed.

---

## 3. MVP Comes First

The immediate goal is the FLEEX MVP.

Prioritize:

1. Working simulation
2. Multiple AMRs
3. Zenoh peer-to-peer communication
4. Heartbeat/failure detection
5. Distributed task allocation
6. Basic task recovery
7. Basic zone reservation
8. LightGBM edge inference
9. Nav2 navigation
10. Basic ORCA
11. Basic software safety shield
12. Central-server failure demonstration

Do not implement advanced post-MVP features before the MVP requires them.

---

## 4. Do Not Redesign the Architecture

Do not replace the decentralized architecture with a centralized
architecture because it appears easier.
## SIMULATION EXECUTION POLICY — HUMAN-IN-THE-LOOP

## Core Rule

The coding AI MUST NOT run Gazebo simulations itself.

The coding AI may inspect, modify, build, lint, and statically validate simulation-related code, but it MUST NOT launch or execute an interactive Gazebo simulation.

The human developer is responsible for running Gazebo simulations.

This rule exists because Gazebo simulation execution is resource-intensive, may require GUI interaction, may run indefinitely, and requires direct observation of the simulated environment.

---

## When the AI Must Stop

Whenever the next implementation step requires an actual simulation run, the AI MUST STOP implementation at that point.

It must NOT:

- launch `gz sim`
- launch Gazebo through ROS 2
- start a simulation launch file
- spawn robots into a running simulation
- run simulation scenarios
- send movement commands to simulated robots
- run simulation-based integration tests
- claim that a simulation test passed without the human running it
- start Gazebo in the background
- use `nohup`, `&`, `screen`, `tmux`, or similar methods to bypass this rule
- create an automated script whose purpose is to secretly execute Gazebo during the current implementation task

---

## Required Human-Test Handoff

When implementation reaches a point where simulation verification is required, stop implementation and provide a clear test handoff.

The handoff MUST contain:

1. Why the simulation is required.
2. What implementation has been completed.
3. Exact commands for the human to run.
4. Expected result for each command.
5. What information the human must report back.
6. Which project-memory files should NOT be marked PASS until the test is confirmed.

Example:

```text
SIMULATION CHECK REQUIRED

Implementation completed:
- Added AMR2 namespace support.
- Updated bridge configuration.
- Build completed successfully.

I cannot verify the runtime behavior without a simulation.

Please run these commands:

COMMAND 1:
...

Expected:
...

COMMAND 2:
...

Expected:
...

After running them, report:
- PASS/FAIL
- terminal output
- observed robot behavior
- any errors

STOP HERE.

Do not continue implementation until the simulation result is provided.
AI Resume Rule

After providing simulation commands, the AI MUST stop its implementation.

The AI may resume only after the human explicitly reports the simulation result.

Examples of valid human responses:

Ran the commands. Everything passed.
2 robots spawned, but amr2/cmd_vel does not work.
The simulation failed with this error:
...

The AI must then use the reported result as the basis for the next action.

Simulation Result Interpretation
If the human reports PASS

The AI may:

Record the verified result.
Update the appropriate project-memory files.
Continue to the next implementation step.
Stop again when another simulation test becomes necessary.
If the human reports FAIL

The AI must:

Stop advancing to unrelated implementation.
Inspect the reported error.
Diagnose the smallest relevant cause.
Modify the necessary code/configuration.
Build or perform static validation.
Provide a new simulation command sequence.
Stop again.
If the human reports partial success

Treat each verified component separately.

For example:

amr1 spawn: PASS
amr2 spawn: PASS
amr1 movement: PASS
amr2 movement: FAIL

Do not mark the entire phase as PASS.

Fix only the failing component before proceeding.

Build vs Simulation

A successful build is NOT a successful simulation.

These are separate verification levels:

Source code exists
        ↓
Build succeeds
        ↓
Node starts
        ↓
Simulation starts
        ↓
Runtime behavior works
        ↓
Integration test passes

The AI may perform the first build/static stages where appropriate.

The human must perform the actual simulation stages.

Commands the AI MAY Run

The AI may use commands for:

inspecting files
searching the repository
reading configuration
checking package structure
checking installed package availability
compiling/building code
running linters
static validation
syntax checks
generating configuration
checking non-runtime metadata

Examples:

grep
find
cat
sed
awk
git diff
colcon build
python syntax checks
CMake configuration
package dependency inspection

These are allowed unless they indirectly launch or execute a Gazebo simulation.

Commands the AI MUST NOT Run

The AI must not execute commands whose purpose is to run the simulation.

Examples include:

gz sim ...
ros2 launch ...gazebo...
ros2 launch ...simulation...
ros_gz_sim create ...

The AI must also not execute commands that spawn or control simulated robots during runtime.

Examples:

gz topic ...
ros2 topic pub .../cmd_vel ...
ros2 service call ...spawn...

when these commands interact with a running Gazebo simulation.

Existing Simulation State

The AI must assume that simulation results are UNKNOWN until the human explicitly reports them.

Do not infer:

robot movement
sensor availability
TF correctness
topic connectivity
collision behavior
navigation success
multi-robot behavior
failure recovery

from source code alone.

Memory File Rule

Simulation-related status must only be marked:

PASS
VERIFIED
COMPLETE

after the human has actually executed the relevant simulation test and reported the result.

If the code is ready but the simulation has not been run, use:

IMPLEMENTED — NOT VERIFIED

or:

READY FOR SIMULATION TEST

Do not convert implementation readiness into test success.

One Test Boundary at a Time

Do not provide a massive simulation checklist when only one component needs testing.

Prefer:

Implement
   ↓
Build
   ↓
Human simulation test
   ↓
Result
   ↓
Continue

Keep the test boundary small enough that a failure can be localized.

No Background Simulation

The AI must never attempt to bypass the simulation handoff by:

running Gazebo in the background
starting Gazebo through another process
using detached terminals
using terminal multiplexers
using scripts that automatically start Gazebo
waiting for a GUI simulation to finish unattended

If runtime simulation is required, stop and hand the test to the human.
Do not introduce a permanent central:

```text
FleetManager
Coordinator
Master
Dispatcher
GlobalPlanner
```

that becomes a single point of failure for fleet coordination.

A small simulator or task generator is allowed to represent the WMS or
central server.

It must not become the FLEEX coordination authority.

---

## 5. Zenoh

Zenoh is the peer-to-peer communication layer.

Use Zenoh for:

- Peer discovery
- Robot state exchange
- Heartbeats
- Distributed coordination communication
- Task-related communication where appropriate

Do not claim that Zenoh itself creates decentralization.

Decentralization comes from robots making coordination decisions locally.

---

## 6. CRDT Rules

CRDTs may be used for replicated task state.

They may represent:

- Task existence
- Task metadata
- Task state
- Advisory task ownership
- Advisory zone information

CRDTs must NOT become the authoritative mechanism for:

- Zone lease ownership
- Safety decisions
- Physical collision prevention

Do not implement a CRDT-based zone lock merely because it is convenient.

---

## 7. Zone Lease Rules

Zone leases are responsible for controlling access to narrow/chokepoint
areas.

Basic flow:

```text
Request
   ↓
Grant
   ↓
Enter
   ↓
Traverse
   ↓
Complete egress
   ↓
Release
```

Do not release a zone merely because the robot reached the next waypoint.

A robot should release the zone after its physical footprint has
completely exited the controlled area.

For the MVP, start with a simple single-zone implementation.

Do not immediately implement the complete multi-zone protocol unless
the current task requires it.

---

## 8. Deadlock Rules

Do not claim that ORCA solves fleet-level deadlock.

ORCA is for local collision avoidance.

The intended protocol-level deadlock mechanism is:

```text
Deterministic zone acquisition order
+
Zone leases
```

For advanced multi-zone coordination:

```text
Ascending zone ID order
```

should be used to prevent circular wait.

A wait-for graph may be used later for:

- Diagnostics
- Telemetry
- Priority
- Aging

Do not treat it as the primary deadlock-prevention mechanism.

---

## 9. ORCA Rules

ORCA is:

```text
Local multi-robot collision avoidance
```

ORCA is NOT:

```text
Safety certification
Fleet-level deadlock prevention
Replacement for a safety scanner
```

Use local sensing such as LiDAR and robot state as the primary basis
for immediate collision avoidance.

Network information may be advisory.

Do not make immediate safety dependent on network availability.

---

## 10. Safety Rules

The MVP safety layer is a simulation/architecture demonstration.

It may use:

```text
LiDAR
↓
Safety monitor
↓
Velocity override
↓
Stop
```

The software safety node must have the ability to override normal
navigation commands.

Never describe the simulation safety node as:

```text
ISO certified
Safety certified
Industrial safety certified
```

Actual industrial deployment would require the appropriate certified
safety hardware and controller.

---

## 11. Navigation Rules

Use existing Nav2 components.

Target:

```text
SMAC 2D
RPP
```

Do not reimplement:

```text
SMAC
RPP
Nav2
```

unless explicitly required.

Do not introduce MPPI into the MVP.

---

## 12. LightGBM Rules

LightGBM is required in the MVP because Edge AI is part of the problem
statement.

The first model should remain simple.

Target:

```text
Predict expected traversal time/delay through a warehouse zone.
```

Potential inputs include:

```text
Zone occupancy
Robot velocity
Queue length
Inflow/outflow
Recent traversal time
Congestion trend
Task demand
Zone geometry
```

Training should initially happen offline.

Inference must run locally at the edge.

Do not build an unnecessarily complicated neural network when a simple
LightGBM model satisfies the MVP requirement.

---

## 13. Task Allocation Rules

Use:

```text
Contract-Net / distributed auction
```

The initial bid can consider:

```text
Distance
Traversal time
Battery
Congestion prediction
Reassignment penalty
```

Hard feasibility checks should be performed before selecting a winner.

Do not create a central optimizer that calculates every robot's bid.

Each robot should calculate its own local bid.

---

## 14. Task Recovery Rules

Task recovery should happen when an assigned robot becomes unavailable.

Initial MVP flow:

```text
Heartbeat lost
     ↓
Failure detected
     ↓
Task becomes recoverable
     ↓
Another robot claims task
     ↓
Task continues
```

Do not immediately implement complicated distributed consensus unless
the MVP requires it.

Do not use "lowest robot ID" as a generic shortcut for every distributed
decision.

When deterministic selection is required, document what is being
selected and why.

---

## 15. WMS / Central Server Rules

The WMS or central server represents the upper warehouse/business layer.

It may:

- Generate tasks
- Send tasks
- Monitor fleet state
- Provide VDA 5050 interoperability

FLEEX must not depend on it for continuous local coordination.

The central server may fail during the demonstration.

The fleet should continue local operation using information already
available at the edge.

---

## 16. VDA 5050 Rules

VDA 5050 is the interoperability boundary.

Treat it as:

```text
Interoperability
+
Advisory task/state interface
```

Do not make VDA 5050 the internal FLEEX coordination mechanism.

Do not redesign FLEEX around a centralized VDA 5050 master.

---

## 17. Existing Warehouse Rules

Use:

```text
simulation/worlds/large_warehouse.world
```

as the primary warehouse simulation.

Do not rebuild the warehouse unnecessarily.

Do not replace the existing warehouse with a tiny custom world merely
because it is easier to code.

A simplified test world may be created later for isolated unit tests,
but the primary MVP demonstration should use the existing warehouse.

---

## 18. AMR Rules

Use:

```text
simulation/urdf/amr1.xacro
```

as the base AMR model.

Do not replace the robot model unnecessarily.

Before modifying the AMR model:

1. Inspect the existing Xacro.
2. Understand its existing sensors/controllers.
3. Determine whether the required change can be made externally.
4. Only modify the model when necessary.

---

## 19. Package Rules

Expected FLEEX packages:

```text
fleex_msgs
fleex_communication
fleex_coordination
fleex_edge_ai
fleex_navigation
fleex_safety
```

Keep responsibilities separated.

### fleex_msgs

Interfaces only.

### fleex_communication

Zenoh, discovery, heartbeat, peer state.

### fleex_coordination

Tasks, auction, recovery, zones, leases.

### fleex_edge_ai

Feature extraction, LightGBM inference, model handling.

### fleex_navigation

Nav2 integration/configuration.

Do not reimplement Nav2 planners/controllers.

### fleex_safety

Safety monitor and velocity override.

---

## 20. Coding Style

Prefer:

```text
Small change
↓
Build
↓
Run
↓
Test
```

Do not make huge multi-file changes without testing.

When possible, modify one logical component at a time.

Avoid unnecessary dependencies.

Avoid unnecessary abstractions.

Avoid premature optimization.

---

## 21. Before Creating New Code

Before creating a new file or node:

1. Search the repository.
2. Check whether an equivalent component already exists.
3. Check the package responsibility.
4. Check the current TODO.
5. Check the relevant architecture documentation.

Do not create duplicate nodes with different names that perform the
same job.

---

## 22. Before Changing Architecture

If a requested change conflicts with an existing architectural decision:

STOP.

Do not silently change the architecture.

Instead:

1. Identify the conflict.
2. Explain the affected component.
3. Identify the architectural decision involved.
4. Propose the smallest change necessary.
5. Record the decision if the architecture is intentionally changed.

---

## 23. Testing Rules

Never mark a feature as working because:

```text
The code compiles.
```

Compilation proves only that the code can compile.

A feature is working only after its relevant behavior has been tested.

Use:

```text
dev/TEST_MATRIX.md
```

to record verified behavior.

---

## 24. Failure Handling

If something fails:

Do NOT repeatedly make random changes.

Instead:

```text
Observe error
    ↓
Record exact error
    ↓
Check recent change
    ↓
Form hypothesis
    ↓
Test hypothesis
    ↓
Apply smallest fix
    ↓
Retest
```

Use:

```text
dev/BLOCKERS.md
dev/DEBUG_LOG.md
```

for persistent problems.

---

## 25. Debugging Rules

When debugging:

- Preserve the original error message.
- Record the command that produced it.
- Record the expected behavior.
- Record the actual behavior.
- Record attempted fixes.
- Do not delete useful logs.
- Do not claim a fix without reproducing the original test.

---

## 26. Vibe-Coding Safety Rules

The AI should assume that the human developer may not remember every
implementation detail.

Therefore:

- Explain what a change does before making a large architectural change.
- Keep code structure predictable.
- Use descriptive names.
- Avoid magic behavior.
- Avoid hidden background processes.
- Avoid unnecessary configuration complexity.
- Keep launch procedures documented.
- Keep important commands reproducible.

The AI must leave the project in a state that another AI can understand.

---

## 27. Documentation Rules

When a significant decision is made, document it.

Use:

```text
docs/architecture.md
docs/protocol.md
docs/scenarios.md
docs/decisions/
```

Do not bury important architectural decisions only inside source code.

---

## 28. State Management

After meaningful progress:

Update:

```text
dev/CURRENT_STATE.md
dev/TODO.md
dev/TEST_MATRIX.md
dev/HANDOFF.md
```

When appropriate also update:

```text
dev/CHANGELOG.md
dev/BLOCKERS.md
dev/DEBUG_LOG.md
```

---

## 29. Handoff Rule

Before stopping work for the day, update `HANDOFF.md` with:

```text
What was completed
What is currently being worked on
Last successful test
Last failed test
Current error
Files changed
Next exact action
```

The next AI session should be able to continue without reconstructing
the entire project history.

---

## 30. Scope Control

When implementing the MVP:

DO:

```text
Simple
Working
Testable
Demonstrable
```

Avoid:

```text
Over-engineered
Prematurely distributed
Unnecessary abstractions
Research-grade protocol complexity
```

The first objective is to finish the FLEEX MVP.

Hardening comes after the MVP works.

---

## 31. Absolute Don'ts

Do NOT:

- Replace decentralization with a central coordinator.
- Use CRDTs as authoritative zone locks.
- Treat ORCA as a safety system.
- Treat ORCA as the primary deadlock solution.
- Claim simulation safety is certified.
- Replace the warehouse without reason.
- Replace `amr1.xacro` without reason.
- Add MPPI to the MVP.
- Build camera processing before the core MVP works.
- Implement advanced distributed protocols before the basic MVP works.
- Mark features complete without testing.
- Randomly modify multiple subsystems while debugging.
- Rewrite working code just for stylistic reasons.
- Invent files or functionality that do not exist.
- Assume roadmap items are already implemented.

---

## 32. Preferred AI Workflow

Use this workflow for every coding session:

```text
Read CURRENT_STATE.md
        ↓
Read HANDOFF.md
        ↓
Read AI_RULES.md
        ↓
Read TODO.md
        ↓
Inspect relevant code
        ↓
Choose ONE small task
        ↓
Implement
        ↓
Build
        ↓
Test
        ↓
PASS ──────────────→ Update state
  │
  └── FAIL ────────→ BLOCKERS / DEBUG_LOG
```

---

## SIMULATION EXECUTION POLICY — HUMAN-IN-THE-LOOP

## Core Rule

The coding AI MUST NOT run Gazebo simulations itself.

The coding AI may inspect, modify, build, lint, and statically validate simulation-related code, but it MUST NOT launch or execute an interactive Gazebo simulation.

The human developer is responsible for running Gazebo simulations.

This rule exists because Gazebo simulation execution is resource-intensive, may require GUI interaction, may run indefinitely, and requires direct observation of the simulated environment.

---

## When the AI Must Stop

Whenever the next implementation step requires an actual simulation run, the AI MUST STOP implementation at that point.

It must NOT:

- launch `gz sim`
- launch Gazebo through ROS 2
- start a simulation launch file
- spawn robots into a running simulation
- run simulation scenarios
- send movement commands to simulated robots
- run simulation-based integration tests
- claim that a simulation test passed without the human running it
- start Gazebo in the background
- use `nohup`, `&`, `screen`, `tmux`, or similar methods to bypass this rule
- create an automated script whose purpose is to secretly execute Gazebo during the current implementation task

---

## Required Human-Test Handoff

When implementation reaches a point where simulation verification is required, stop implementation and provide a clear test handoff.

The handoff MUST contain:

1. Why the simulation is required.
2. What implementation has been completed.
3. Exact commands for the human to run.
4. Expected result for each command.
5. What information the human must report back.
6. Which project-memory files should NOT be marked PASS until the test is confirmed.

Example:

```text
SIMULATION CHECK REQUIRED

Implementation completed:
- Added AMR2 namespace support.
- Updated bridge configuration.
- Build completed successfully.

I cannot verify the runtime behavior without a simulation.

Please run these commands:

COMMAND 1:
...

Expected:
...

COMMAND 2:
...

Expected:
...

After running them, report:
- PASS/FAIL
- terminal output
- observed robot behavior
- any errors

STOP HERE.

Do not continue implementation until the simulation result is provided.
AI Resume Rule

After providing simulation commands, the AI MUST stop its implementation.

The AI may resume only after the human explicitly reports the simulation result.

Examples of valid human responses:

Ran the commands. Everything passed.
2 robots spawned, but amr2/cmd_vel does not work.
The simulation failed with this error:
...

The AI must then use the reported result as the basis for the next action.

Simulation Result Interpretation
If the human reports PASS

The AI may:

Record the verified result.
Update the appropriate project-memory files.
Continue to the next implementation step.
Stop again when another simulation test becomes necessary.
If the human reports FAIL

The AI must:

Stop advancing to unrelated implementation.
Inspect the reported error.
Diagnose the smallest relevant cause.
Modify the necessary code/configuration.
Build or perform static validation.
Provide a new simulation command sequence.
Stop again.
If the human reports partial success

Treat each verified component separately.

For example:

amr1 spawn: PASS
amr2 spawn: PASS
amr1 movement: PASS
amr2 movement: FAIL

Do not mark the entire phase as PASS.

Fix only the failing component before proceeding.

Build vs Simulation

A successful build is NOT a successful simulation.

These are separate verification levels:

Source code exists
        ↓
Build succeeds
        ↓
Node starts
        ↓
Simulation starts
        ↓
Runtime behavior works
        ↓
Integration test passes

The AI may perform the first build/static stages where appropriate.

The human must perform the actual simulation stages.

Commands the AI MAY Run

The AI may use commands for:

inspecting files
searching the repository
reading configuration
checking package structure
checking installed package availability
compiling/building code
running linters
static validation
syntax checks
generating configuration
checking non-runtime metadata

Examples:

grep
find
cat
sed
awk
git diff
colcon build
python syntax checks
CMake configuration
package dependency inspection

These are allowed unless they indirectly launch or execute a Gazebo simulation.

Commands the AI MUST NOT Run

The AI must not execute commands whose purpose is to run the simulation.

Examples include:

gz sim ...
ros2 launch ...gazebo...
ros2 launch ...simulation...
ros_gz_sim create ...

The AI must also not execute commands that spawn or control simulated robots during runtime.

Examples:

gz topic ...
ros2 topic pub .../cmd_vel ...
ros2 service call ...spawn...

when these commands interact with a running Gazebo simulation.

Existing Simulation State

The AI must assume that simulation results are UNKNOWN until the human explicitly reports them.

Do not infer:

robot movement
sensor availability
TF correctness
topic connectivity
collision behavior
navigation success
multi-robot behavior
failure recovery

from source code alone.

Memory File Rule

Simulation-related status must only be marked:

PASS
VERIFIED
COMPLETE

after the human has actually executed the relevant simulation test and reported the result.

If the code is ready but the simulation has not been run, use:

IMPLEMENTED — NOT VERIFIED

or:

READY FOR SIMULATION TEST

Do not convert implementation readiness into test success.

One Test Boundary at a Time

Do not provide a massive simulation checklist when only one component needs testing.

Prefer:

Implement
   ↓
Build
   ↓
Human simulation test
   ↓
Result
   ↓
Continue

Keep the test boundary small enough that a failure can be localized.

No Background Simulation

The AI must never attempt to bypass the simulation handoff by:

running Gazebo in the background
starting Gazebo through another process
using detached terminals
using terminal multiplexers
using scripts that automatically start Gazebo
waiting for a GUI simulation to finish unattended

If runtime simulation is required, stop and hand the test to the human.

---

## 33. Final Rule

Do not optimize for the amount of code written.

Optimize for:

```text
Working system
+
Understandable code
+
Reproducible tests
+
Recoverable development state
```

The goal is to finish FLEEX, not to produce the largest repository.
