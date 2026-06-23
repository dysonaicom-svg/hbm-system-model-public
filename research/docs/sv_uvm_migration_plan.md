# HBM4 SystemVerilog/UVM Migration Plan

**Date:** 2026-06-15
**Purpose:** Path from Python system modeling to SystemVerilog/UVM implementation

## 1. Migration Strategy Overview

### Why Separate Python and SV/UVM Phases?

| Aspect | Python Model | SV/UVM Implementation |
|--------|--------------|----------------------|
| **Purpose** | Architecture exploration, algorithm validation | RTL verification, signoff |
| **Accuracy** | Trend-correct | Cycle-accurate |
| **Speed** | Fast (100K+ cycles/sec) | Slow (100s cycles/sec) |
| **Scope** | Full system | DUT + testbench |
| **Coverage** | Architectural | Functional + code |

### What Can Be Reused from Python Model

1. **Algorithm specifications** - Scheduling algorithms, state machines
2. **Parameter definitions** - Timing parameters, queue depths
3. **Test vectors** - Traffic patterns, corner cases
4. **Reference model structure** - HBM4ChannelModel as scoreboard reference

### What Needs Re-Implementation

1. **RTL implementation** - All controller modules
2. **Cycle-accurate timing** - Not trend-correct
3. **Bus protocols** - AXI/AHB, DFI interfaces
4. **Synthesis constraints** - Timing, area, power

## 2. Python Model to RTL Mapping

| Python Module | SV/UVM Component | File | Priority |
|---------------|------------------|------|----------|
| `HBM4Controller` | hbm4_controller | hbm4_controller.sv | P0 |
| `HBM4AddressDecoder` | hbm4_addr_decode | hbm4_addr_decode.sv | P0 |
| `HBM4QoSScheduler` | hbm4_qos_arb | hbm4_qos_arb.sv | P1 |
| `HBM4RefreshScheduler` | hbm4_refresh | hbm4_refresh.sv | P1 |
| `HBM4ChannelModel` | hbm4_dram_model | hbm4_dram_model.sv | P0 |
| `DFI Interface` | hbm4_dfi | hbm4_dfi.sv | P0 |
| `PowerEstimator` | Power monitor | hbm4_power.sv | P2 |
| `ThermalModel` | Thermal monitor | hbm4_thermal.sv | P2 |
| `TSV PHY` | TSV PHY model | hbm4_tsv_phy.sv | P1 |
| `LaneRepair` | Lane repair FSM | hbm4_lane_repair.sv | P1 |

## 3. UVM Verification Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        hbm4_test                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     hbm4_env                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐   │  │
│  │  │ hbm4_agent  │  │hbm4_mem_model│  │ hbm4_scoreboard │   │  │
│  │  │  (master)   │  │  (reference) │  │                 │   │  │
│  │  │┌──────────┐│  │┌───────────┐│  │┌───────────────┐│   │  │
│  │  ││ hbm4_driver│  ││ HBM4 model ││  ││ Comparator   ││   │  │
│  │  │└──────────┘│  │└───────────┘│  │└───────────────┘│   │  │
│  │  │┌──────────┐│  │┌───────────┐│  │┌───────────────┐│   │  │
│  │  ││hbm4_monitor│ ││            ││  ││ Coverage      ││   │  │
│  │  │└──────────┘│  │└───────────┘│  │└───────────────┘│   │  │
│  │  │┌──────────┐│  └─────────────┘  └───────────────────┘   │  │
│  │  ││hbm4_seqr  ││  ┌─────────────┐  ┌───────────────────┐   │  │
│  │  │└──────────┘│  │hbm4_predictor│  │ hbm4_coverage    │   │  │
│  │  └─────────────┘  └─────────────┘  └───────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     DUT: hbm4_controller                   │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │  │
│  │  │ addr_decode│ │ qos_arb    │ │ refresh           │   │  │
│  │  └────────────┘ └────────────┘ └────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key UVM Components

#### hbm4_agent (master)
- **Purpose:** Drive stimulus to DUT
- **Components:**
  - `hbm4_driver`: Convert transactions to pin-level protocol
  - `hbm4_monitor`: Observe DUT outputs
  - `hbm4_sequencer`: Queue sequences

#### hbm4_mem_model (reference)
- **Purpose:** Generate expected responses
- **Implementation:** Python HBM4ChannelModel ported to SystemVerilog
- **Features:**
  - DRAM timing compliance
  - Bank state tracking
  - Command sequencing

#### hbm4_scoreboard
- **Purpose:** Compare DUT vs reference
- **Checks:**
  - Data integrity
  - Timing compliance
  - Command validity

#### hbm4_coverage
- **Purpose:** Measure functional coverage
- **Covergroups:**
  - Command types
  - Address patterns
  - State transitions
  - Error scenarios

## 4. Implementation Order

### Phase 1: RTL Core (Week 1-2)
```
Priority 0 (Must Have):
├── hbm4_types.svh       - Type definitions
├── hbm4_pkg.sv          - Package
├── hbm4_addr_decode.sv  - Address decoder
└── hbm4_dfi.sv          - DFI interface
```

### Phase 2: RTL Controller (Week 3-4)
```
Priority 1 (Should Have):
├── hbm4_controller.sv   - Main controller
├── hbm4_qos_arb.sv      - QoS arbiter
└── hbm4_refresh.sv     - Refresh scheduler
```

### Phase 3: RTL Support (Week 5-6)
```
Priority 2 (Nice to Have):
├── hbm4_dram_model.sv   - DRAM model
├── hbm4_tsv_phy.sv      - TSV PHY
└── hbm4_lane_repair.sv  - Lane repair
```

### Phase 4: UVM Testbench (Week 7-8)
```
├── hbm4_env.sv          - Environment
├── hbm4_base_test.sv    - Base test
├── hbm4_agent.sv        - Agent
├── hbm4_driver.sv       - Driver
├── hbm4_monitor.sv      - Monitor
└── hbm4_sequencer.sv   - Sequencer
```

### Phase 5: UVM Sequences (Week 9-10)
```
├── hbm4_seq_lib.sv      - Sequence library
├── hbm4_basic_seq.sv    - Basic sequences
├── hbm4_stress_seq.sv   - Stress sequences
└── hbm4_ai_train_seq.sv - AI training sequences
```

### Phase 6: UVM Verification (Week 11-12)
```
├── hbm4_ref_model.sv    - Reference model
├── hbm4_scoreboard.sv  - Scoreboard
└── hbm4_coverage.sv    - Coverage model
```

## 5. Directory Structure

```
rtl/hbm4/
├── hbm4_controller.sv       # Main controller (top-level)
├── hbm4_addr_decode.sv      # Address decoder
├── hbm4_qos_arb.sv          # QoS arbiter
├── hbm4_refresh.sv         # Refresh scheduler
├── hbm4_dram_model.sv       # DRAM timing model
├── hbm4_dfi.sv             # DFI interface
├── hbm4_tsv_phy.sv         # TSV PHY abstraction
├── hbm4_lane_repair.sv     # Lane repair FSM
├── hbm4_power.sv           # Power monitor
├── hbm4_thermal.sv        # Thermal monitor
├── hbm4_types.svh          # Type definitions
└── hbm4_pkg.sv             # Package

uvm/hbm4/
├── hbm4_env.sv              # UVM environment
├── hbm4_base_test.sv        # Base test class
├── hbm4_agent.sv            # Master agent
├── hbm4_driver.sv           # Sequence driver
├── hbm4_monitor.sv          # Protocol monitor
├── hbm4_sequencer.sv        # Sequence sequencer
├── hbm4_seq_lib.sv          # Sequence library
├── hbm4_basic_seq.sv        # Basic test sequences
├── hbm4_stress_seq.sv       # Stress test sequences
├── hbm4_ai_seq.sv          # AI workload sequences
├── hbm4_ref_model.sv        # Reference model
├── hbm4_scoreboard.sv       # Scoreboard
├── hbm4_coverage.sv         # Coverage model
├── hbm4_assertions.sv       # Protocol assertions
└── Makefile                  # Build automation

tb/hbm4/
└── hbm4_tb.sv              # Top-level testbench
```

## 6. Verification Plan Outline

### 6.1 Functional Coverage Points

| Category | Coverage Points |
|----------|-----------------|
| Commands | ACT, PRE, RD, WR, REF, MRS, NOP |
| Address | Channel, pseudo-channel, bank, row, column |
| State | All controller FSM states |
| Errors | ECC, CRC, parity, timeout |
| Power | All power-down modes |

### 6.2 Protocol Compliance Checks

| Protocol | Checks |
|----------|--------|
| DFI 5.1 | Timing, control, PHY state |
| HBM4 | Command ordering, timing |
| AXI/AHB | Burst protocol |

### 6.3 Performance Metrics

| Metric | Measurement |
|--------|-------------|
| Bandwidth | Peak and sustained |
| Latency | Read/write average and P99 |
| Queueing | Queue fill levels |
| Utilization | Channel and bank |

### 6.4 Error Injection Scenarios

| Error Type | Scenario |
|------------|----------|
| ECC | Single/double bit errors |
| CRC | Data corruption |
| Parity | CA parity errors |
| Timeout | Bank conflict timeout |
| Training | Training failure |

## 7. Key Decisions Required

1. **Bus Protocol:** AXI4 or AHB for host interface?
2. **DFI Version:** DFI 5.1 or custom extension?
3. **Reference Model:** Port Python or rewrite?
4. **Coverage Strategy:** Automatic or manual covergroups?
5. **Verification IP:** Commercial VIP or custom?

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Timing accuracy | Cross-validate with vendor models |
| Coverage gaps | Add assertions for corner cases |
| Reference mismatch | Keep Python model as golden reference |
| Schedule slip | Prioritize P0 modules first |

## 9. Success Criteria

- [ ] All P0 RTL modules synthesized
- [ ] 90%+ functional coverage
- [ ] All sequences pass
- [ ] Protocol assertions clean
- [ ] Performance metrics within 10% of Python model