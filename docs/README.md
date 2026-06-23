# HBM System Modeling Platform

> **Version**: 2.2 | **Status**: Phase 2 Complete | **Tests**: 4,409 Passing
> **Branch**: `feat/hbm4-logic-base-die-phase2`
> **Last Updated**: 2026-06-23

---

## Architecture

```
                    +------------------------------------------+
                    |           Traffic Generator             |
                    |     (Sequential / Random / Stride)       |
                    +-------------------+----------------------+
                                        |
                                        v
                    +------------------------------------------+
                    |           AXI4 / NoC Interconnect        |
                    +-------------------+----------------------+
                                        |
                                        v
+------------------------------------------------------------------------------+
|                          HBM CONTROLLER (Phase A)                            |
|  +-------------+  +---------------+  +--------------+  +------------------+  |
|  |   Address   |  |    QoS       |  |   Refresh   |  |    Command       |  |
|  |   Decoder   |  |   Scheduler  |  |   Scheduler |  |    Sequencer     |  |
|  |  (6 modes)  |  |  (16 levels) |  | (All/Per)   |  |    Pipeline      |  |
|  +-------------+  +---------------+  +--------------+  +------------------+  |
+------------------------------------------------------------------------------+
                                        |
                                        v
+------------------------------------------------------------------------------+
|                      DFI 5.0/5.1 INTERFACE                                   |
|                    (Address / Control / Write Data / Read Data)               |
+------------------------------------------------------------------------------+
                                        |
                                        v
+------------------------------------------------------------------------------+
|                          DRAM MODEL (Phase B)                                 |
|  +-------------+  +---------------+  +--------------+  +------------------+  |
|  |   Channel   |  |     Bank      |  |   Power      |  |    Thermal       |  |
|  |   Model     |  |  State Machine|  |   Estimator  |  |     Model        |  |
|  +-------------+  +---------------+  +--------------+  +------------------+  |
|  +-------------+  +---------------+  +--------------+  +------------------+  |
|  |    ECC      |  |   Lane        |  |   TSV        |  |    Logic         |  |
|  |   / CRC     |  |   Repair      |  |   Model      |  |    Base Die      |  |
|  +-------------+  +---------------+  +--------------+  +------------------+  |
+------------------------------------------------------------------------------+
                                        |
                                        v
+------------------------------------------------------------------------------+
|                          PHY MODEL (Phase C)                                 |
|  +-------------+  +---------------+  +--------------+  +------------------+  |
|  |   PHY       |  |   Signal     |  |    Eye      |  |     IBIS         |  |
|  |   Training  |  |   Integrity  |  |   Analyzer  |  |    Parser        |  |
|  +-------------+  +---------------+  +--------------+  +------------------+  |
+------------------------------------------------------------------------------+
                                        |
                                        v
                    +------------------------------------------+
                    |         Statistics Collector             |
                    |     (Bandwidth / Latency / Efficiency)   |
                    +-----------------------------------------+
```

---

## Key Features

| Category | Capabilities |
|----------|--------------|
| **HBM3/HBM4 Support** | 32 channels, 64 pseudo-channels, 8-16 GT/s data rates |
| **Controller** | FR-FCFS scheduling, 16-level QoS, 6 address mapping modes |
| **DRAM Timing** | Full bank state machine, ACT/PRE/RD/WR timing, refresh scheduling |
| **PHY** | Training sequences, TX/RX equalization, eye diagram analysis |
| **Reliability** | ECC/CRC error detection, lane repair, thermal management |
| **RTL Integration** | Verilog RTL with UVM verification environment |
| **Simulation** | Transaction-level, unified Python+RTL co-simulation |

---

## Quick Start

```bash
# Installation
pip install -r requirements.txt
pip install -e .

# Basic Simulation
python -m sim.simulator --mode functional

# Unified Simulation (Python + RTL)
python -m sim.unified_simulator

# Performance Benchmark
python -m sim.benchmark

# Run Tests
pytest tests/ -v                    # All tests
pytest tests/controller/ -v         # Controller tests
pytest tests/dram/ -v                # DRAM tests
pytest tests/hbm4/ -v                # HBM4 tests
pytest tests/integration/ -v         # Integration tests

# RTL Simulation
cd rtl && verilator --cc --trace --top-module hbm_controller_tb \
    hbm_controller_tb.sv hbm_controller.sv hbm_types.svh hbm_pkg.sv
```

---

## Project Overview

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Design Exploration** | Evaluate architecture schemes before RTL implementation |
| **Performance Analysis** | Analyze bandwidth, latency, efficiency across traffic patterns |
| **Verification Alignment** | Ensure Python model and RTL implementation consistency |
| **Protocol Verification** | Validate HBM protocol timing and signal integrity |

### HBM4 Specifications

| Parameter | Value |
|-----------|-------|
| Data Rate | 8-16 GT/s |
| Interface Width | 2048-bit |
| Channels | 32 (2x HBM3) |
| Pseudo-channels | 64 |
| Peak Bandwidth | 2.048 TB/s |
| Banks | 16 per pseudo-channel |
| Rows | 262K per bank |
| Speed Grades | 8 GT/s / 12 GT/s / 16 GT/s |

---

## Test Status

| Category | Tests | Status |
|----------|-------|--------|
| Controller Tests | 360+ | Pass |
| DRAM Tests | 1009+ | Pass |
| HBM4 Tests | 650+ | Pass |
| Simulation Tests | 190+ | Pass |
| Integration Tests | 827+ | Pass |
| Coverage Tests | 362+ | Pass |
| Performance Tests | 61+ | Pass |
| Benchmark Tests | 184+ | Pass |
| Verification Tests | 62+ | Pass |
| RTL Tests | 146+ | Pass |
| Traffic Tests | 117+ | Pass |
| Interconnect Tests | 129+ | Pass |
| PHY Tests | 178+ | Pass |
| **Total** | **4,409+** | **100% Pass** |

---

## Performance Benchmarks

### Achieved Performance

| Pattern | Throughput | Avg Latency | Row Hit Rate |
|---------|------------|-------------|--------------|
| Sequential | ~164 GB/s | 12.93 cycles | 62.5% |
| Stride (4KB) | ~82 GB/s | 12.66 cycles | 0% |
| Random | ~82 GB/s | 29.89 cycles | 0% |
| Hotspot | ~82 GB/s | 29.25 cycles | 0% |

### Theoretical Bandwidth

| Configuration | Bandwidth |
|---------------|-----------|
| HBM4 Single Channel | 64-128 GB/s |
| HBM4 32 Channels | 2.048 TB/s |
| HBM4 8 Stacks | 16.4 TB/s |

---

---

## Key Achievements

- **Complete HBM3/HBM4 modeling** with full controller, DRAM timing, and PHY support
- **4,409+ tests passing** with comprehensive coverage
- **RTL-Python co-simulation** capability for verification alignment
- **UVM verification environment** with reference models
- **6 address mapping modes** and 16-level QoS scheduling
- **ECC/CRC error detection** and lane repair capabilities
- **Thermal management** and power estimation
- **Logic Base Die integration** with per-channel independence
- **PAM3 encoding support** for HBM4 signal integrity
- **Public release package** ready for distribution

---

## Development Phases

| Phase | Goal | Status |
|-------|------|--------|
| A | HBM Controller Model | Complete |
| B | DRAM Timing Model | Complete |
| C | PHY Integration | Complete |
| D | RTL-Python Integration | Complete |
| E | Documentation & Delivery | Complete |
| F | Verification & Validation | Complete |

---

## Code Metrics

| Category | Count | Size |
|----------|-------|------|
| Python Files | 85+ | 3.5 MB |
| RTL Files | 6 | 2.3 MB |
| Test Files | 120+ | 6.5 MB |
| Documentation | 52 | 750 KB |
| **Total** | **1,300+** | **14 MB** |

---

## Recent Commits

| Commit | Description |
|--------|-------------|
| `ab9d1f0` | fix: add missing List import and enhance address decoder |
| `2408575` | docs: Complete final verification report for HBM3 Python vs Ramulator2 comparison |
| `8f8827e` | fix: correct trace replay timing and add BankState import |
| `4600e4f` | feat: add HBM3 comparison framework for Ramulator2 validation |
| `7a3a1d3` | feat: update DRAM models and benchmark suite |

---

---

## Development Phases

| Phase | Goal | Status |
|-------|------|--------|
| A | HBM Controller Model | Complete |
| B | DRAM Timing Model | Complete |
| C | PHY Integration | Complete |
| D | RTL-Python Integration | Complete |
| E | Documentation & Delivery | Complete |
| F | Verification & Validation | Complete |
| **2** | **Logic Base Die Enhancement** | **Complete** |

---

## Logic Base Die Features (Phase 2)

| Feature | Description |
|---------|-------------|
| Per-Channel Independence | JEDEC-compliant independent timing per channel |
| PAM3 Encoding | 3-level pulse amplitude modulation |
| Calibration Manager | Comprehensive calibration procedures |
| Command Buffering | Advanced command scheduling |
| Channel Timing Context | Independent timing domains |

---

## Code Metrics

| Category | Count | Size |
|----------|-------|------|
| Python Files | 150+ | 5+ MB |
| RTL Files | 7 | 2.5+ MB |
| Test Files | 120+ | 7+ MB |
| Documentation | 52+ | 800+ KB |
| **Total** | **1,400+** | **16+ MB** |

---

## Additional Resources

| Document | Description |
|----------|-------------|
| [Design Document](design/2026-06-15-hbm-system-model-design.md) | Complete design specification |
| [Quick Reference](QUICKREF.md) | Command reference |
| [Phase 2 Plan](plans/2026-06-17-phase3-development-plan.md) | Development plan |
| [HBM3 Spec](specs/hbm3_spec.md) | HBM3 parameter reference |
| [Ramulator2](../research/ramulator2/) | Reference simulator |

---

*Document generated: 2026-06-23*