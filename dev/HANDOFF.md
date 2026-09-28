# HANDOFF

## What Was Completed

- Added `AGENTS.md` to `.gitignore`.
- Extracted exact 3D bounding boxes from Gazebo COLLADA meshes to compute mathematically precise approach offsets (0.6m from face) for all shelves in `locations.yaml`.
- Fixed `station_01` pose, which was previously trapped inside a closed square of static pallets.
- Discovered and fixed a distributed race condition where `fleex_task_executor` dropped assigned tasks if it was already busy. Implemented a Task Queue.
- Implemented Workload Penalty in `fleex_task_bidder` (adding +1000 per active task) to force autonomous load balancing across the fleet.

## What Is Currently Being Worked On

- Phase 9: Multi-Robot Traffic and Contention Resolution.

## Last Successful Test

- `test_4` (station_01 -> packing_area) executed cleanly by AMR1.

## Last Failed Test

- `test_12` (packing_area -> shelf_A_02) aborted with Nav2 `status 6` for AMR2. AMR2 crashed into the parked physical bodies of AMR1 and AMR3 because standard Nav2 cannot resolve fleet-level dynamic blockages.

## Current Error

- Fleet collisions require protocol-level zone management or ORCA.

## Files Changed (This Session)

- `config/warehouse/locations.yaml` - Standardized and corrected all navigation poses.
- `src/fleex_coordination/fleex_coordination/task_bidder.py` - Added workload penalty to bid calculation.
- `src/fleex_coordination/fleex_coordination/task_executor.py` - Added task execution queueing.
- `.gitignore` - Added AI customizations.

## Next Exact Action

1. Implement `ZoneManager` (CRDT-based zone leases) to lock down chokepoints.
2. Ensure robots wait at a safe distance before entering a zone occupied by a peer.
