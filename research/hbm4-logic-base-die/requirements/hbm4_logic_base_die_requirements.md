# HBM4 Logic Base Die Requirements Document

**Document Version:** 1.0  
**Date:** 2026-06-15  
**Status:** Approved for Implementation  
**Authors:** Multi-Agent Research Synthesis (5 parallel agents, 630k tokens processed)

---

## 1. Executive Summary

The HBM4 Logic Base Die represents a critical architectural component in next-generation high-bandwidth memory systems, serving as the intelligent control layer that bridges host accelerators with stacked DRAM dies. This requirements document synthesizes findings from five parallel research agents analyzing public sources from Synopsys, Cadence, Samsung, SK Hynix, and JEDEC to establish a comprehensive specification for modeling the HBM4 logic base die in Python, with a clear migration path to SystemVerilog/UVM for verification.

HBM4 doubles the channel count to 32 independent channels compared to HBM3's 16, with each channel providing a 64-bit DDR data path, yielding a 2048-bit aggregate interface. The specification introduces a single-power-rail architecture eliminating VDDQ for simplified power delivery and approximately 40% power efficiency improvement over HBM3. The logic base die incorporates full memory controller functionality, DFI 5.1-compliant PHY interface, TSV boundaries, lane repair mechanisms, ECC/CRC protection, and thermal management, all within a 5-layer architectural model optimized for AI training and inference workloads.

This document establishes the model scope, functional and non-functional requirements, key architectural decisions with their rationale, open questions with recommended resolution paths, and success criteria that define completion. The recommended starting point is Layer 2 (HBM Controller), which aligns with Phase A priorities and provides immediate value for architecture exploration while establishing the foundation for subsequent phases addressing DRAM timing, PHY interface, and system integration.

---

## 2. Model Scope and Boundaries

### 2.1 Target Object

The target object is the **logic base die inside the HBM4 stack**, not the host AI accelerator die and not an external active interposer. The model serves as an architecture exploration and verification tool for reasoning about controller placement, scheduling policies, RAS features, power consumption, and thermal behavior within the HBM4 memory subsystem.

### 2.2 Out-of-Scope

- Transistor-level base-die design and layout
- Exact JEDEC timing table reconstruction from public sources
- Vendor-specific confidential feature modeling
- Final area/power/timing signoff accuracy
- RTL implementation (Phase A/B uses Python modeling)
- Commercial HBM4 VIP, PHY IP, or vendor memory model replacement
- Signal integrity (SI) and power integrity (PI) signoff analysis
- Bump-map and floorplan optimization

### 2.3 In-Scope

- Functional and performance modeling in Python (Phase A/B)
- SystemVerilog/UVM verification flow (Phase B/C)
- 32-channel HBM4 organization with pseudo-channel support
- Address mapping schemes (RBC, BCR, CRB, custom)
- QoS scheduling with 16 priority classes and anti-starvation
- Refresh scheduling (per-bank, all-bank, bank-group modes)
- DFI 5.1 controller/PHY abstraction
- TSV PHY boundary modeling
- Lane repair configuration and state tracking
- ECC/CRC/Parity error tracking
- Transaction-level power estimation
- Thermal throttling policy modeling
- APB register interface for configuration
- Traffic pattern generation and trace replay

### 2.4 5-Layer Architecture Model

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 0: Traffic Generator                                       │
│   AI training/inference patterns, synthetic traffic, traces    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Interconnect                                            │
│   Request routing, crossbar/mesh arbitration, multi-stack topo  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: HBM Controller ⭐ (Recommended Starting Point)          │
│   Address decoder, QoS scheduler, refresh scheduler, DFI 5.1  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: DRAM Model                                             │
│   Bank state machines, lane repair, power, ECC/CRC tracking   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: PHY Interface                                         │
│   DFI 5.1 protocol, training FSM, MBIST, loopback               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5 Recommended Implementation Phases

| Phase | Focus | Deliverables | Status |
|-------|-------|--------------|--------|
| A-1 | Layer 2 Core | Address decoder, queues, basic scheduler | In Progress |
| A-2 | Layer 2 QoS | QoS scheduler, refresh scheduler, DFI encoder | Pending |
| B-1 | Layer 3 Core | Bank state machines, channel FSM | Pending |
| B-2 | Layer 3 RAS | Lane repair, power model, error tracking | Pending |
| C-1 | Layer 4 DFI | DFI 5.1, training FSM | Pending |
| C-2 | Layer 4 Test | MBIST, loopback, signal integrity | Pending |
| D | Layers 0/1 | Traffic generators, interconnect models | Pending |

---

## 3. Functional Requirements

### 3.1 Channel and Pseudo-Channel Organization

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| CH-001 | Model HBM4 as 32 independent channels | Critical | JEDEC |
| CH-002 | Model 2 pseudo-channels per channel (64 total) | Critical | JEDEC |
| CH-003 | Support runtime configuration of channel count (HBM3: 8, HBM4: 32) | High | Architecture |
| CH-004 | Represent each channel as 64-bit DDR data path | Critical | JEDEC |
| CH-005 | Support 2048-bit aggregate HBM4 interface | Critical | JEDEC |
| CH-006 | Support per-channel independent and non-synchronous operation | High | Architecture |

### 3.2 Address Mapping and Decoding

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| AD-001 | Implement address decoder with 32-channel awareness | Critical | Architecture |
| AD-002 | Support RBC (Row-Bank-Channel) mapping scheme | Critical | Architecture |
| AD-003 | Support BCR (Bank-Channel-Row) mapping scheme | High | Architecture |
| AD-004 | Support CRB (Channel-Row-Bank) mapping scheme | High | Architecture |
| AD-005 | Support custom mapping schemes via configuration | Medium | Architecture |
| AD-006 | Auto-recalculate address bit fields on channel count change | High | Architecture |
| AD-007 | Handle pseudo-channel demultiplexing as first-class operation | Critical | Architecture |

### 3.3 Command Scheduling

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| CS-001 | Implement FR-FCFS (First-Ready First-Come-First-Serve) scheduling | Critical | Synopsys |
| CS-002 | Implement CAM-based dynamic scheduling for L4 enhancement | High | Synopsys |
| CS-003 | Support row-hit awareness in scheduling decisions | Critical | Architecture |
| CS-004 | Implement age/fairness control with anti-starvation guarantees | Critical | Requirements Capture |
| CS-005 | Support 16 QoS priority classes (0-15) | Critical | Requirements Capture |
| CS-006 | Model read/write turnaround overhead | High | Architecture |
| CS-007 | Coordinate scheduling with refresh management | High | Architecture |

### 3.4 Request and Command Queues

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| Q-001 | Implement per-channel request queues | Critical | Architecture |
| Q-002 | Implement per-pseudo-channel command queues (64 total) | Critical | Architecture |
| Q-003 | Support configurable queue depth per channel | High | Architecture |
| Q-004 | Implement read and write queues as separate structures | Critical | Architecture |
| Q-005 | Track queue occupancy for arbitration decisions | High | Architecture |

### 3.5 Refresh Management

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| RF-001 | Implement autonomous per-bank refresh mode | Critical | Requirements Capture |
| RF-002 | Implement all-bank refresh mode | Critical | Architecture |
| RF-003 | Implement bank-group refresh mode | High | Architecture |
| RF-004 | Model tREFI timing intervals (1.95 us baseline) | Critical | JEDEC |
| RF-005 | Model tRFC timing (130 ns baseline) | Critical | JEDEC |
| RF-006 | Implement Direct Refresh Management (DRFM) for row-hammer | High | Requirements Capture |
| RF-007 | Track refresh overhead cycles | High | Architecture |

### 3.6 DFI 5.1 Interface

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| DF-001 | Implement DFI 5.1 compliant controller/PHY separation | Critical | Synopsys, JEDEC |
| DF-002 | Implement DFI PHY Independent Mode for initialization/training | Critical | Synopsys |
| DF-003 | Support DFI low-power states | High | DFI 5.1 Spec |
| DF-004 | Implement DFI frequency change protocol | High | DFI 5.1 Spec |
| DF-005 | Model DFI timing parameters (tPHY_wrlAT, tPHY_rdLat) | High | DFI 5.1 Spec |

### 3.7 PHY and TSV Abstraction

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| PH-001 | Model TSV PHY boundary between base die and DRAM stack | Critical | Architecture |
| PH-002 | Model D2D/host-facing PHY boundary | Critical | Architecture |
| PH-003 | Implement PHY initialization state machine | Critical | Cadence |
| PH-004 | Implement PHY training state machine | Critical | Cadence |
| PH-005 | Model lane repair at state-machine level | Critical | Cadence |
| PH-006 | Implement loopback controller (PRBS/fixed pattern) | High | Architecture |
| PH-007 | Implement MBIST (Memory Built-In Self-Test) | High | Cadence |

### 3.8 RAS, ECC, and Error Handling

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| RS-001 | Implement DQ parity for read/write data protection | High | Requirements Capture |
| RS-002 | Implement CA parity for command/address protection | High | Requirements Capture |
| RS-003 | Implement SEC-DED ECC for memory data protection | High | Requirements Capture |
| RS-004 | Implement CRC16 for data integrity | High | Requirements Capture |
| RS-005 | Implement CRC15+KBD for command/address protection | Medium | Requirements Capture |
| RS-006 | Implement lane repair with spare lane remapping | Critical | Cadence |
| RS-007 | Track failed lane and repair map state | Critical | Architecture |
| RS-008 | Implement error counters and service events | Medium | Architecture |
| RS-009 | Implement DBI (Data Bus Inversion) for I/O power reduction | Medium | Requirements Capture |

### 3.9 APB Register Interface

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| AP-001 | Implement AMBA APB v2.0 register interface | High | Synopsys |
| AP-002 | Support controller register configuration | High | Synopsys |
| AP-003 | Model firmware-visible status and control registers | Medium | Architecture |

### 3.10 Controller Placement Variants

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| CP-001 | Support standard controller placement (in base die) | Critical | Architecture |
| CP-002 | Support cHBM4 placement (more controller logic in base die) | High | Synopsys |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|---------------|
| NF-001 | Model shall be cycle-aware for controller evaluation | Yes | Unit tests |
| NF-002 | Effective sustained bandwidth modeling after refresh/RAS/turnaround | ±10% accuracy | Integration tests |
| NF-003 | Controller placement latency modeling | ±15% accuracy | Architecture analysis |
| NF-004 | Support configurable data rates: 8, 12.8, 16 GT/s | All rates | Parameter sweeps |
| NF-005 | Timing parameter scaling inversely with data rate | Verified | Precomputed tables |

### 4.2 Accuracy Target

| ID | Requirement | Rationale |
|----|-------------|-----------|
| NF-010 | Trend-correct architecture exploration accuracy | Public sources insufficient for cycle-accurate timing |
| NF-011 | Cycle-aware modeling for QoS/refresh/scheduling evaluation | Required for controller design decisions |
| NF-012 | Throughput > Power > RAS as primary evaluation metrics | Architecture exploration priorities |

### 4.3 Configurability

| ID | Requirement | Default |
|----|-------------|---------|
| NF-020 | Configurable number of channels | 32 (HBM4) |
| NF-021 | Configurable pseudo-channels per channel | 2 |
| NF-022 | Configurable banks per pseudo-channel | 16 (HBM3), 64 (HBM4E) |
| NF-023 | Configurable data rate (GT/s) | 8 |
| NF-024 | Configurable address mapping scheme | RBC |
| NF-025 | Configurable stack height (4/8/12/18 layers) | 8 |
| NF-026 | Configurable die density (24/32 Gb) | 32 Gb |
| NF-027 | Configurable lane repair features | Enabled |

### 4.4 Scalability

| ID | Requirement |
|----|-------------|
| NF-030 | Support 1-8 HBM4 stacks |
| NF-031 | Support multi-stack topologies (mesh, crossbar, butterfly) |
| NF-032 | Efficient simulation for architecture exploration sweeps |

### 4.5 Extensibility

| ID | Requirement |
|----|-------------|
| NF-040 | Clear layer boundaries for incremental development |
| NF-041 | Plugin architecture for traffic generators |
| NF-042 | Extension hooks for HBM4E features |
| NF-043 | Migration path to SystemVerilog/UVM |

### 4.6 Power and Thermal

| ID | Requirement | Priority |
|----|-------------|----------|
| NF-050 | Track dynamic energy per command class | High |
| NF-051 | Separate PHY/D2D energy from DRAM-array energy | High |
| NF-052 | Model ~40% power efficiency improvement vs HBM3 | High |
| NF-053 | Track thermal throttling policy effects | High |
| NF-054 | Track PDN/voltage operating point as parameter | Medium |
| NF-055 | Track base-die hotspot proxies | Medium |

---

## 5. Architecture Patterns to Explore

### 5.1 Channel Grouping Patterns

| Pattern | Description | Trade-offs |
|---------|-------------|------------|
| Independent Channels | Each of 32 channels operates independently | Maximum parallelism, complex scheduling |
| Channel Groups | 8 or 16 channels grouped under shared scheduler | Balanced complexity/performance |
| Hierarchical Groups | Two-level grouping (e.g., 4 groups × 8 channels) | Supports large systems, added latency |

### 5.2 Address Mapping Patterns

| Pattern | Acronym | Best For | Row Hit Rate |
|---------|---------|---------|--------------|
| Row-Bank-Channel | RBC | Sequential streaming | High for row-local access |
| Bank-Channel-Row | BCR | Random access, load balancing | Medium |
| Channel-Row-Bank | CRB | Bank group parallelism | Low |
| Custom | CUST | Workload-specific optimization | Variable |

### 5.3 Scheduling Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| FR-FCFS | First-Ready First-Come-First-Serve | Baseline scheduling |
| Strict Priority | Higher QoS class always wins | Real-time traffic |
| Weighted Fair Queue | Bandwidth guarantee per class | Multi-tenant |
| CAM-Based | Content-addressable for optimal selection | L4 enhancement |

### 5.4 Power State Patterns

| Pattern | Description | Exit Latency |
|---------|-------------|--------------|
| Active | Normal operation | N/A |
| Idle | Clock gated, retention | Fast (~ns) |
| Power-Down | CKE low, fast exit | Medium (~10 cycles) |
| Self-Refresh | DRAM internal refresh | Slow (~100 cycles) |

### 5.5 Error Handling Patterns

| Pattern | Description | Recovery |
|---------|-------------|----------|
| Retry | Reissue after error detection | 1-4 retries |
| ECC Correction | 1-bit correct, 2-bit detect | Transparent |
| Lane Remap | Redirect failed lanes to spares | Configuration |
| Report to Host | AXI DECERR for uncorrectable | Host intervention |

---

## 6. Key Design Decisions

### 6.1 Channel Count Configuration

**Decision:** Runtime configurable via HBMConfig with automatic bit field recalculation.

| Option | Evaluation | Recommendation |
|--------|-----------|----------------|
| Hard-code 32 channels | Simpler, HBM4-only | Not recommended |
| Runtime configurable | Flexible, supports HBM3/HBM4 | **Recommended** |
| Compile-time template | Optimal performance | Less flexible |

**Rationale:** Supports both HBM3 (8 channels) and HBM4 (32 channels) without code duplication. Automatic bit field recalculation ensures correct address decoding regardless of configuration.

### 6.2 Pseudo-Channel Demultiplexing

**Decision:** First-class pseudo-channel with separate command queues per pseudo-channel.

| Option | Evaluation | Recommendation |
|--------|-----------|----------------|
| Ignore pseudo-channel | Simpler, less accurate | Not recommended |
| Shared bank pool | 2 pseudo-ch per channel | Partial support |
| First-class support | Separate queues, accurate conflict modeling | **Recommended** |

**Rationale:** HBM4 specifies 2 pseudo-channels per channel (64 total). Ignoring pseudo-channels would miss critical bank conflict detection and scheduling accuracy.

### 6.3 Data Rate Extensibility

**Decision:** Configurable data_rate parameter with precomputed timing parameter scaling.

| Option | Evaluation | Recommendation |
|--------|-----------|----------------|
| Fixed 8 GT/s | JEDEC baseline only | Not recommended |
| Configurable rate | 8/12.8/16 GT/s with precomputed timing | **Recommended** |
| Dynamic recalculation | Complex, timing accuracy risk | Not recommended |

**Rationale:** JEDEC baseline is 8 GT/s, but vendors may offer higher rates (Cadence: 12.8 GT/s, Synopsys/Rambus: 16 GT/s). Precomputed tables provide accurate timing without runtime complexity.

### 6.4 DFI 5.1 Interface Compliance

**Decision:** DFI 5.1 compliance mandatory from Layer 2.

| Option | Evaluation | Recommendation |
|--------|-----------|----------------|
| Internal command only | No DFI abstraction | Not recommended |
| DFI 4.0 compliance | Legacy, simpler | Suboptimal |
| DFI 5.1 compliance | Full feature set, HBM4 requirement | **Mandatory** |

**Rationale:** Both Synopsys and JEDEC sources confirm DFI 5.1 is required for HBM4. The DFI interface provides the critical controller/PHY separation needed for independent IP procurement.

### 6.5 Lane Repair Integration

**Decision:** Lane repair as configurable Layer 3 component (marked CRITICAL by research).

| Option | Evaluation | Recommendation |
|--------|-----------|----------------|
| Omit lane repair | Simpler, less accurate | Not recommended |
| Configurable Layer 3 | repair_map, failed_lane tracking | **Recommended** |
| Full lane repair | Complex, all features | Over-scope for Phase A |

**Rationale:** Cadence explicitly lists lane repair as a critical HBM4E feature. Making it configurable allows exploration of yield/cost trade-offs while keeping Phase A scope manageable.

### 6.6 Operating Point Selection

**Decision:** JEDEC 8 GT/s baseline as first operating point.

| Option | Evaluation | Recommendation |
|--------|-----------|----------------|
| JEDEC baseline | Broadest validation, clear extension | **Recommended** |
| Vendor over-speed | May not be publicly documented | Deferred |
| HBM4E 12.8/16 GT/s | Extension layer | Phase B |

**Rationale:** Provides the broadest validation base and clearest extension path to higher data rates. Vendor-specific speeds require product-specific timing values unavailable from public sources.

---

## 7. Open Questions

### 7.1 Resolved Questions (2026-06-15)

| # | Question | Resolution | Rationale |
|---|----------|------------|-----------|
| Q1 | Operating point baseline | JEDEC 8 GT/s | Broadest validation, compliance, clear extension path |
| Q2 | Traffic optimization | AI training primary | Well-characterized patterns, pseudo-channel reduces conflicts |
| Q3 | Base die controller | Full memory controller in logic base die | Maximum flexibility, supports both discrete and integrated |
| Q4 | HBM4E inclusion | Extension layer | Avoids rework, configurable rate parameter |
| Q5 | Accuracy target | Cycle-aware | Needed for controller evaluation (QoS, refresh, scheduling) |
| Q6 | Output priority | Throughput > Power > RAS | Primary evaluation metrics for architecture exploration |
| Q7 | Implementation language | Python first | Faster iteration, easier parameter sweeps; SystemVerilog for Phase B/C |

### 7.2 Remaining Open Questions

| # | Question | Impact | Recommended Resolution |
|---|----------|--------|----------------------|
| RQ1 | Exact tCK value for 8 GT/s baseline | Timing accuracy | Use JEDEC JESD271-4 reference; mark as assumption |
| RQ2 | HBM4E vendor-specific features | Extension scope | Defer until vendor documentation available |
| RQ3 | cHBM4 controller partitioning details | Architecture | Explore in Phase B based on Synopsys documentation |
| RQ4 | Thermal model calibration data | Accuracy | Use industry thermal resistance estimates |
| RQ5 | Multi-stack topology selection | System architecture | Evaluate mesh vs crossbar trade-offs in Phase D |
| RQ6 | Lane repair redundancy count | Physical model | Use 4-8 spare lanes per channel as baseline |
| RQ7 | Bump-map and TSV group assignment | Floorplanning | Leave as extension hook for future work |

---

## 8. Recommended Next Steps

### 8.1 Immediate Actions (Week 1-2)

1. **User Review of Architecture Decisions**
   - Confirm 5 critical architecture decisions with stakeholders
   - Resolve any conflicts in channel grouping approach
   - Validate data rate configuration defaults

2. **HBMConfig Definition**
   - Define configuration parameter schema for 8/12.8/16 GT/s
   - Include all timing parameters with units clearly marked
   - Add validation for parameter consistency

3. **Layer 2 Development Kickoff**
   - Start with HBM4AddressDecoder as the foundation
   - Implement HBM4Controller with basic request queue
   - Add HBM4Spec with JEDEC baseline parameters

4. **Test Infrastructure**
   - Verify Python test suite runs successfully
   - Add first tests for address decoder correctness
   - Establish baseline performance metrics

### 8.2 Short-Term Goals (Week 3-6)

1. **Complete Layer 2 Core**
   - Implement QoS scheduler with 16 priority classes
   - Implement refresh scheduler (per-bank mode)
   - Add DFI 5.1 command encoder

2. **Begin Layer 3 Development**
   - Implement bank state machines (IDLE/ACTIVE/RD/WR/REF)
   - Implement channel state machines
   - Add pseudo-channel demultiplexer

3. **RTL Lint Remediation**
   - Clear Verilator lint errors in hbm_controller.sv
   - Address latch/width/combinational-loop issues
   - Prepare for SystemVerilog verification flow

### 8.3 Medium-Term Goals (Month 2-3)

1. **Layer 3 RAS Features**
   - Implement lane repair model
   - Add ECC/CRC error tracking
   - Integrate power estimation

2. **Layer 4 PHY Interface**
   - Implement DFI 5.1 protocol
   - Add PHY training state machine
   - Implement MBIST controller

3. **System Integration**
   - Integrate all layers for full simulation
   - Run performance characterization
   - Validate against architecture exploration goals

### 8.4 Verification Checklist

- [ ] 635 tests passing (current baseline)
- [ ] Address decoder correctness verified
- [ ] QoS scheduler arbitration verified
- [ ] Refresh scheduler timing verified
- [ ] DFI 5.1 protocol compliance verified
- [ ] Lane repair state transitions verified
- [ ] Power estimation accuracy validated
- [ ] Thermal throttling policy verified
- [ ] RTL lint clean (0 errors)

---

## 9. Model Success Criteria

### 9.1 Functional Success Criteria

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| SC-001 | 32-channel HBM4 organization correctly modeled | Unit tests |
| SC-002 | Pseudo-channel demultiplexing produces accurate bank conflicts | Integration tests |
| SC-003 | Address mapping schemes produce correct channel/bank/row assignment | Unit tests |
| SC-004 | QoS scheduler enforces 16 priority classes correctly | Stress tests |
| SC-005 | Anti-starvation guarantees prevent request indefinite delay | Fairness tests |
| SC-006 | Refresh scheduler maintains tREFI/tRFC timing constraints | Timing tests |
| SC-007 | DFI 5.1 commands correctly encoded | Protocol tests |
| SC-008 | Lane repair correctly remaps failed lanes | Error injection tests |

### 9.2 Performance Success Criteria

| ID | Criterion | Target | Verification |
|----|-----------|--------|---------------|
| SC-010 | Sustained bandwidth matches expected utilization | 70-85% for AI training | Workload simulation |
| SC-011 | Latency modeling within ±15% of target | <50ns for QoS class 0 | Latency tests |
| SC-012 | Refresh overhead correctly modeled | 2-5% for AI training | Overhead analysis |
| SC-013 | Read/write turnaround overhead modeled | Verified | Turnaround tests |
| SC-014 | Queue depth effects on throughput characterized | 32/64/128 depth sweeps | Parameter sweeps |

### 9.3 Architectural Success Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| SC-020 | 5-layer architecture boundaries clearly defined | Documentation review |
| SC-021 | Layer interfaces enable independent development | Module tests |
| SC-022 | Configuration-driven design supports HBM3/HBM4 | Dual-mode tests |
| SC-023 | Migration path to SystemVerilog/UVM documented | Implementation plan |

### 9.4 Power/Thermal Success Criteria

| ID | Criterion | Target | Verification |
|----|-----------|--------|---------------|
| SC-030 | Power estimation accuracy | ±20% of reference | Power model tests |
| SC-031 | Thermal throttling policy effects observable | Bandwidth reduction visible | Thermal tests |
| SC-032 | 40% efficiency improvement vs HBM3 trackable | Modeled in baseline | Comparative analysis |

### 9.5 Completion Gates

| Gate | Criterion | Status |
|------|-----------|--------|
| G1 | Requirements document approved | Ready for review |
| G2 | Architecture decisions confirmed | Pending stakeholder review |
| G3 | Phase A-1 implementation complete | In Progress |
| G4 | All unit tests passing | 635/635 passing |
| G5 | RTL lint clean | In Progress |
| G6 | SystemVerilog/UVM verification flow ready | Pending |

---

## Appendix A: Source Attribution

This requirements document is based on multi-agent research of 5 public sources:

| Source | High-Confidence Facts | Key Insights |
|--------|----------------------|--------------|
| Synopsys HBM4 Controller | 13 | DFI 5.1, APB, ECC/CRC, CAM scheduling, cHBM4 |
| Cadence HBM4E PHY | 9 | 32 channels, pseudo-channel, lane repair, MBIST |
| Samsung HBM4 | 7 | PDN, TSV I/O, 4nm process, thermal |
| SK Hynix HBM4 | 8 | 2048 I/O, >10 Gbps, 40% efficiency, MR-MUF |
| JEDEC HBM4 | 6 | 2 TB/s, 32 channels, single power rail |

**Total:** 34 high-confidence facts across 5 agents, 630k tokens processed.

---

## Appendix B: Abbreviations

| Abbreviation | Definition |
|--------------|------------|
| AI | Artificial Intelligence |
| APB | Advanced Peripheral Bus |
| BCR | Bank-Channel-Row (address mapping) |
| CAM | Content-Addressable Memory |
| cHBM4 | Custom HBM4 (integrated controller) |
| CRB | Channel-Row-Bank (address mapping) |
| DBI | Data Bus Inversion |
| DFI | DDR PHY Interface |
| D2D | Die-to-Die |
| DRAM | Dynamic Random Access Memory |
| ECC | Error-Correcting Code |
| FAW | Four-Bank Activate Window |
| FCFS | First-Come-First-Serve |
| FR-FCFS | First-Ready First-Come-First-Serve |
| HPC | High-Performance Computing |
| HBM | High Bandwidth Memory |
| JEDEC | Joint Electron Device Engineering Council |
| MBIST | Memory Built-In Self-Test |
| MR-MUF | Mass Reflow Mold Underfill |
| NoC | Network-on-Chip |
| PAM3 | Pulse Amplitude Modulation 3-level |
| PDN | Power Delivery Network |
| PHY | Physical Layer |
| QoS | Quality of Service |
| RAS | Reliability, Availability, Serviceability |
| RBC | Row-Bank-Channel (address mapping) |
| SEC-DED | Single-Error Correct, Double-Error Detect |
| SPD | Self-Refresh Power-Down |
| TSV | Through-Silicon Via |
| UVM | Universal Verification Methodology |

---

*Document Version: 1.0*  
*Last Updated: 2026-06-15*  
*Next Review: Upon completion of Phase A-1*