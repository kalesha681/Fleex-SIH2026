# KNOWN_ISSUES

## Purpose

This file records known limitations, unresolved technical concerns, and expected rough edges in FLEEX.

A known issue is different from a blocker:

- **Blocker:** prevents the next planned milestone.
- **Known issue:** exists or may exist, but does not currently prevent the planned MVP path.

Do not turn speculative concerns into confirmed issues.

---

## Current Known Issues

### KI-001 — Simulation foundation has not yet been verified in this session

**Status:** FIXED

**Impact:** Medium

The existing warehouse world and AMR have been identified, and the simulation foundation (including ROS 2 Jazzy, Gazebo Harmonic, and `ros_gz_bridge`) has been fully verified and bridged in this session.

---

### KI-002 — Existing AMR sensor configuration may require enabling

**Status:** FIXED

**Impact:** Medium

The AMR model's 2D LiDAR was disabled by default but has been fully enabled and bridged via `bringup.launch.py`.

---

### KI-003 — Software safety shield is not a certified safety system

**Status:** ACCEPTED LIMITATION

**Impact:** High for real-world deployment, not an MVP simulation blocker

The MVP software safety shield is intended for simulation and architecture demonstration. It must not be described as a certified industrial safety system. The eventual real-hardware safety architecture requires an appropriate certified safety scanner/controller and hardware safety chain.

---

### KI-004 — Advanced distributed protocols are intentionally deferred

**Status:** ACCEPTED

**Impact:** None for MVP

The current MVP implements and verifies the following distributed behaviors:
- Distributed task ownership and Contract-Net auction recovery.
- Minimal chokepoint reservation via `ZoneManager`.
- TTL-based zone lease recovery.
- Deterministic heartbeat-aware task zombie resolution.

However, the following advanced distributed protocols are intentionally outside the first MVP and are deferred to post-MVP/evaluation work:
- Advanced CRDT convergence mechanisms.
- Atomic multi-zone lease protocol.
- True partition reconciliation.
- Advanced lease epochs/CAS semantics.
- Large-scale evaluation and baseline comparison.
- Full ablation studies.

---

### KI-005 — LightGBM training is not an online MVP requirement

**Status:** ACCEPTED

**Impact:** None for MVP

The intended MVP approach is:

```text
Gazebo logs
    ↓
offline dataset
    ↓
LightGBM training
    ↓
export model
    ↓
local edge inference
```

The model does not need to retrain continuously during simulation.

---

### KI-006 — ORCA is not a safety or deadlock mechanism

**Status:** ACCEPTED DESIGN CONSTRAINT

ORCA handles local reciprocal collision avoidance.

It does not provide:

- certified safety,
- zone mutual exclusion,
- protocol-level deadlock prevention,
- task recovery.

Those responsibilities belong to separate FLEEX components.

---

## Issue Recording Rules

When a new issue is discovered:

1. Give it a unique `KI-XXX` ID.
2. Describe the observed behavior.
3. State whether it is confirmed or still being investigated.
4. Identify the affected component.
5. Record the impact.
6. Link related debugging information through `DEBUG_LOG.md` where appropriate.
7. Move the issue to `BLOCKERS.md` if it prevents the next milestone.
8. Close the issue only after a real verification test.

---

## Status Values

Use one of:

```text
OPEN
TO VERIFY
INVESTIGATING
ACCEPTED
FIXED
CLOSED
```

Do not mark an issue `FIXED` merely because a code change was made. It must be verified.
