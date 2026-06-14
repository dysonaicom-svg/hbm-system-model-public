# HBM4 Logic Base Die Requirements Capture

Date: 2026-06-15
Last Updated: 2026-06-15 (Multi-agent research synthesis)

## Research Status

- [x] Phase 1: Public source deep dive (5 sources, 34 high-confidence facts)
- [x] Phase 2: Requirements analysis (7 open questions answered)
- [x] Phase 3: Architecture design (5-layer model with interfaces)
- [ ] Phase 4: Implementation planning (pending user review)

## Target Object

The target is the **logic base die inside the HBM4 stack**, not the host AI
accelerator die and not an external active interposer.

The model should help reason about:

- which controller and PHY functions belong in the HBM4 logic base die;
- how channel, pseudo-channel, TSV, and PHY partitioning affect throughput,
  latency, power, and thermal behavior;
- which RAS, repair, test, and maintenance features affect area and latency;
- how much public information is enough for early architecture exploration, and
  where NDA/vendor/JEDEC details become mandatory.

## Requirements From Public Sources

### Standard-Level Requirements

- Model HBM4 as a distributed, 32-channel memory system (doubled from HBM3's 16).
- Treat channels as independent and potentially non-synchronous.
- Represent each channel interface as a 64-bit DDR data path (32 channels × 64-bit = 2048-bit).
- Parameterize number of channels, pseudo-channels, stack height, die density,
  speed bin, burst behavior, timing values, and voltage/power points.
- Track JESD271-4 bump mapping as a separate physical-interface input.
- Keep SPHBM4 separate from baseline HBM4.
- **HBM4 simplifies power delivery: VDDQ removed, single power rail architecture**.

### Controller And Scheduling Requirements

- Include per-channel and per-pseudo-channel request queues (64 pseudo-channels total).
- Include a command scheduler with at least:
  - row-hit awareness (FR-FCFS at L2, CAM-based at L4);
  - age/fairness control with **anti-starvation guarantees**;
  - **16 QoS priority classes**;
  - read/write turnaround modeling;
  - refresh and refresh-management interactions.
- Include controller register configuration via **AMBA APB v2.0 interface**.
- Support both standard controller placement and **cHBM4** placement where more
  memory-controller logic moves into the base die.
- **CAM-based dynamic scheduling** for bit-accurate modeling (L4 enhancement).

### PHY, TSV, And D2D Requirements

- Model a **TSV PHY** boundary between base die logic and stacked DRAM dies.
- Model a D2D/host-facing PHY boundary between HBM stack and host accelerator.
- Represent PHY initialization, training, **lane repair**, loopback, and memory BIST
  at an abstract state-machine level.
- Include **DFI 5.1** controller/PHY separation (mandatory for HBM4).
- Include **DFI PHY Independent Mode** for initialization/training.
- Include per-slice or per-channel clocking domains to support independent
  channels and non-synchronous operation.
- **Low-voltage TSV I/O** design for reduced power consumption.

### RAS, ECC, And Maintenance Requirements

- Include **DQ parity** (read/write data protection).
- Include **CA parity** (command/address protection).
- Include **SEC-DED ECC** for memory data protection.
- Include **CRC16** for data integrity.
- Include **CRC15+KBD** for command/address protection.
- Include **refresh management / direct refresh management** (DRFM) as a first-class
  model object (row-hammer mitigation).
- Include **per-bank and all-bank refresh** with autonomous management.
- Include **spare/lane/channel repair states** at architectural level.
- Include **lane repair** as a configurable feature (CRITICAL per research).
- Include error counters and service events so system software/firmware impact
  can be estimated later.
- Include **DBI (Data Bus Inversion)** for I/O power reduction.

### Power, Thermal, And PDN Requirements

- Track dynamic energy per command class: ACT, PRE, RD, WR, refresh, training,
  repair/test, and idle/power-down transitions.
- Track PHY/D2D energy separately from DRAM-array command energy.
- Track **~40% power efficiency improvement** vs HBM3 baseline.
- Track **thermal throttling policy** and its effect on effective bandwidth.
- Track PDN/voltage operating point as a model parameter rather than a constant.
- Track base-die hotspot proxies: controller cluster, D2D PHY, TSV PHY, ECC/RAS
  logic, and clocking.
- **Advanced PDN optimization** with multi-phase power delivery.

### Package And Physical Awareness Requirements

- Include a logical-to-physical mapping layer for channel, pseudo-channel, TSV
  group, PHY slice, and bump region.
- Keep the early model abstract; do not attempt signoff SI/PI.
- Leave hooks for bump map, interposer/package parasitics, skew budget,
  thermal resistance, and PDN limits.
- Support **configurable stack heights**: 4/8/12/18 layers.
- Support **die densities**: 24Gb or 32Gb per die.
- **Heterogeneous stacking**: 4nm base die + 1c DRAM (~10nm) process nodes.

## Questions The Model Should Answer

- What is the effective sustained bandwidth per stack after refresh, RAS,
  read/write turnaround, throttling, and queue conflicts?
- How much latency is introduced by controller placement, PHY training/retry,
  ECC/CRC, and base-die arbitration?
- How should channels and pseudo-channels be grouped into controller clusters?
- How deep should request, command, retry, and response queues be?
- Which address-mapping policy reduces bank conflicts for AI training and
  inference traffic?
- Which base-die blocks dominate power and thermal pressure at JEDEC baseline
  speed and at vendor over-speed bins?
- What minimal register and firmware model is needed to exercise training,
  repair, refresh management, and power-state transitions?

## Recommended Model Boundaries

### First Boundary (Phase A Focus)

```text
host traffic model
  -> host-facing D2D interface abstraction
  -> logic base die controller clusters
  -> channel / pseudo-channel schedulers
  -> TSV PHY abstraction
  -> HBM4 DRAM bank-state/timing abstraction
  -> power / thermal / RAS observers
```

### Layer Architecture

| Layer | Name | Focus |
|-------|------|-------|
| Layer 0 | Traffic Generator | AI training/inference/synthetic patterns |
| Layer 1 | Interconnect | Request routing, crossbar arbitration |
| Layer 2 | HBM Controller ⭐ | Request-to-command, QoS, refresh, DFI |
| Layer 3 | DRAM Model | Bank timing, lane repair, power |
| Layer 4 | PHY Interface | DFI 5.1, training, MBIST, loopback |

**Recommended Start**: Layer 2 (HBM Controller) - aligned with Phase A priorities.

## Critical Architecture Decisions

### 1. Channel Count Configuration

| Option | Recommendation |
|--------|----------------|
| Hard-code 32 channels | Simpler, HBM4-only |
| **Runtime configurable** | Flexible, supports both HBM3/HBM4 |
| Compile-time template | Optimal performance, less flexible |

**Recommended**: Runtime configurable via HBMConfig with automatic bit field recalculation.

### 2. Pseudo-Channel Demultiplexing

| Option | Recommendation |
|--------|----------------|
| Ignore pseudo-channel | Treat as single logical channel |
| Shared bank pool | 2 pseudo-ch per channel |
| **First-class support** | Separate queues, accurate conflict modeling |

**Recommended**: First-class pseudo-channel with separate command queues per pseudo-channel.

### 3. Data Rate Extensibility

| Option | Recommendation |
|--------|----------------|
| Fixed 8 GT/s | JEDEC baseline only |
| **Configurable rate** | 8/12.8/16 GT/s with precomputed timing |
| Dynamic recalculation | Complex, timing accuracy risk |

**Recommended**: Configurable data_rate parameter with precomputed timing parameter scaling.

### 4. DFI 5.1 Interface Compliance

| Option | Recommendation |
|--------|----------------|
| Internal command only | No DFI abstraction |
| DFI 4.0 compliance | Legacy, simpler |
| **DFI 5.1 compliance** | Full feature set, HBM4 requirement |

**Recommended**: DFI 5.1 compliance from Layer 2 - controller emits DFI-compliant commands.

### 5. Lane Repair Integration

| Option | Recommendation |
|--------|----------------|
| Omit lane repair | Simpler, less accurate |
| **Configurable Layer 3** | repair_map, failed_lane tracking |
| Full lane repair | Complex, all features |

**Recommended**: Lane repair as configurable Layer 3 component (marked CRITICAL by research).

## Open Questions - Resolved

| # | Question | Resolution | Rationale |
|---|----------|------------|-----------|
| Q1 | Operating point baseline | **JEDEC 8 GT/s** | Broadest validation, compliance, clear extension path |
| Q2 | Traffic optimization | **AI training primary** | Well-characterized patterns, pseudo-channel reduces conflicts |
| Q3 | Base die controller | **PHY-only + repair/RAS** | Maximum flexibility, supports both discrete and integrated |
| Q4 | HBM4E inclusion | **Extension layer** | Avoids rework, configurable rate parameter |
| Q5 | Accuracy target | **Cycle-aware** | Needed for controller evaluation (QoS, refresh, scheduling) |
| Q6 | Output priority | **Throughput > Power > RAS** | Primary evaluation metrics for architecture exploration |
| Q7 | Implementation language | **Python first** | Faster iteration, easier parameter sweeps; SystemVerilog for Phase B/C |

## Non-Goals For The First Requirement Phase

- No transistor-level base-die design.
- No exact JEDEC timing table reconstruction from public snippets.
- No vendor-specific confidential feature modeling.
- No final area/power/timing signoff.
- No RTL yet (Python modeling for Phase A/B).
- No replacement for commercial HBM4 VIP, PHY IP, or vendor memory model.

## Initial Success Criteria

The requirement phase is successful when we have:

- [x] a confirmed model boundary for the logic base die (5-layer architecture);
- [x] a public-source-backed feature checklist (34 high-confidence facts);
- [x] a list of assumptions requiring JEDEC/vendor validation (documented);
- [x] 5 critical architecture decisions with recommendations;
- [x] an agreed first operating point (8 GT/s) and workload class (AI training).
- [x] 7 open questions answered with rationale.

## Critical Assumptions

1. JEDEC HBM4 base spec is 8 GT/s - vendors may prioritize higher rates.
2. Python modeling remains sufficient for Phase A/B exploration.
3. Lane repair is CRITICAL per research - may be optional if yield targets are relaxed.
4. cHBM4 integrated controller is a near-term requirement - may be deferred if discrete controller remains primary.
5. Synopsys/Cadence vendor simulators available for calibration in Phase B/C.

## Source Attribution

This requirements capture is based on multi-agent research of 5 public sources:

| Source | Agent Findings | Key Insights |
|--------|----------------|--------------|
| Synopsys HBM4 Controller | 13 High-confidence | DFI 5.1, APB, ECC/CRC, CAM scheduling, cHBM4 |
| Cadence HBM4E PHY | 9 High-confidence | 32 channels, pseudo-channel, lane repair, MBIST |
| Samsung HBM4 | 7 High-confidence | PDN, TSV I/O, 4nm process, thermal |
| SK Hynix HBM4 | 8 High-confidence | 2048 I/O, >10 Gbps, 40% efficiency, MR-MUF |
| JEDEC HBM4 | 6 High-confidence | 2 TB/s, 32 channels, single power rail |

Total: 34 high-confidence facts across 7 agents, 630k tokens processed.

## Next Steps

1. **User Review**: Confirm 5 critical architecture decisions.
2. **Implementation Plan**: Create detailed Phase A/B implementation tasks.
3. **HBMConfig**: Define configuration parameter schema for 8/12.8/16 GT/s.
4. **Layer 2 Development**: Start with HBM Controller as recommended.
5. **Testbench Setup**: Prepare Python test infrastructure for controller model.