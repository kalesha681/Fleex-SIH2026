# FLEEX MVP TODO

## CURRENT OBJECTIVE

Prepare a reliable FLEEX MVP demonstration.

## COMPLETED

- **Simulation Foundation (Phases 0-4):** ROS 2 environment, Gazebo Harmonic, custom AMR models, multiple unique namespaces, localized TF/LiDAR configured successfully.
- **Peer-to-Peer Communication (Phase 5):** Distributed Zenoh infrastructure built, `rmw_zenoh_cpp` utilized, eliminating central coordinator requirement. Heartbeat lifecycle verified.
- **Distributed Task Management (Phases 6-7):** Task generator running. Contract-Net auctioning, deterministic tie-breaking, task ownership CRDTs, and heartbeat-aware zombie recovery successfully implemented and proven in runtime.
- **Physical Navigation (Phase 8):** Nav2 with SMAC 2D and RPP integrated, offset math for bounds safety, and load-balancing task queues implemented.
- **Chokepoint Coordination (Phase 9):** Localized collision prediction via circle-line math. TTL-based zone reservation with `ZoneManager` working end-to-end with dynamic wait and task recovery integration.

## NEXT

- **Phase 10: Edge AI (LightGBM)**
  - Implement congestion/delay prediction model.
  - Integrate Edge AI inference into local `TaskBidder` cost calculation.
- **Phase 11: Safety Shield**
  - Implement protective velocity override layer processing raw LiDAR data.
- **Phase 12: WMS/VDA 5050 Integration**
  - Wrap WMS with minimal VDA 5050 boundary to bridge real-world standard.
- **MVP Integration & Demo Prep (Phase 16)**
  - Audit current MVP completeness and polish end-to-end demonstrations (Central server failure, network partition, hardware failure scenarios).

## BLOCKED / WAITING

- None. Ready for next phase.

## RULES

- Do not mark tasks complete before human runtime verification.
- MVP comes first. Do not add research-grade complexity until MVP demonstration works natively.
