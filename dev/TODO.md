# To-Do

## Completed Phases
- [x] Phase 0: Project Foundation
- [x] Phase 1: Simulation Foundation (3 AMRs)
- [x] Phase 2: ROS 2 Packages
- [x] Phase 3: Message Definitions
- [x] Phase 4: Multi-Robot Simulation
- [x] Phase 5: Zenoh Communication + Heartbeats
- [x] Phase 6: Minimal Task Generator
- [x] Phase 7: Distributed Task Allocation & Recovery
- [x] Phase 8: Multi-Robot Nav2 Navigation
- [x] Phase 9: Multi-Robot Traffic / Chokepoint Coordination

## In Progress / Next

### Phase 10: Edge AI (LightGBM)
- [ ] Create `fleex_edge_ai` package.
- [ ] Generate offline traffic dataset.
- [ ] Train LightGBM inference model for congestion delay prediction.
- [ ] Implement inference node to run locally at the edge.
- [ ] Integrate predicted delay into `TaskBidder` bidding logic.

### Phase 11: Safety Shield
- [ ] Create `fleex_safety` package.
- [ ] Implement software protective field scanning from LiDAR.
- [ ] Implement velocity override to forcefully stop Nav2.

### Phase 12: VDA 5050 / Central Server Integration
- [ ] Wrap the `TaskGenerator` in a thin FastAPI/VDA 5050 bridge.
- [ ] Test system behavior during simulated WMS network failure.

### Phase 16: MVP Integration
- [ ] Complete end-to-end WMS -> Edge AI -> Nav2 -> Zone Reservation -> Task Recovery demonstration.
- [ ] Finalize documentation for repository pushing.
- [ ] Record video and prepare PPT.
