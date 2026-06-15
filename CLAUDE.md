# HBM System Modeling Platform

## Project Overview

HBM (High Bandwidth Memory) 系统仿真平台，支持芯片设计探索和验证对齐。

## Architecture

```
Traffic Generator / Trace Reader
        ↓
Interconnect (NoC / AXI)
        ↓
HBM Controller (Phase A - Complete)
        ↓
HBM DRAM Model (Phase B - Complete)
        ↓
Statistics Collector
```

## Key Phases

| Phase | Goal | Status |
|-------|------|--------|
| A | HBM Controller Model | **Complete** |
| B | DRAM Timing Model | **Complete** |
| C | PHY Integration | **Complete** (~92%) |

## Key Components

### Python Models

| Component | Files | Status |
|-----------|-------|--------|
| Controller | `controller.py`, `hbm4_controller.py` | Complete |
| Address Decoder | `address_decoder.py`, `hbm4_address_decoder.py` | Complete |
| QoS Scheduler | `qos_scheduler.py`, `hbm4_qos_scheduler.py` | Complete |
| Refresh Scheduler | `refresh_scheduler.py`, `hbm4_refresh_scheduler.py` | Complete |
| Request Queue | `queue.py`, `request.py` | Complete |
| DRAM Timing | `timing.py`, `hbm4_spec.py` | Complete |
| Channel Model | `channel_model.py`, `hbm4_channel_model.py` | Complete |
| Bank State Machine | `bank_state_machine.py` | Complete |
| PHY Training | `phy_training.py` | Complete |
| MBIST Controller | `mbist_controller.py` | Complete |
| Power Estimator | `power_estimator.py` | Complete |
| ECC/CRC | `ecc_crc.py` | Complete |
| Lane Repair | `lane_repair.py` | Complete |
| DFI Interface | `dfi_interface.py` | Complete |

### RTL Components

| Component | File | Status |
|-----------|------|--------|
| Type Definitions | `hbm_types.svh` | Complete |
| UVM Package | `hbm_pkg.sv` | Complete |
| DRAM Model | `dram_model.sv` | Complete |
| Controller RTL | `hbm_controller.sv` | Complete |
| Testbench | `hbm_controller_tb.cpp` | Complete |

### UVM Verification

| Component | Status |
|-----------|--------|
| Environment Package | Complete |
| Test Package | Complete |
| Testbench | Complete |
| Reference Models | Complete |

## Key Documents

- [Design Document](docs/design/2026-06-15-hbm-system-model-design.md) - 完整设计规范
- [HBM3 Spec](docs/specs/hbm3_spec.md) - HBM3 参数参考
- [Ramulator2](research/ramulator2/) - 参考模拟器

## Quick Start

```bash
# Setup
pip install -r requirements.txt

# Run simulation
python -m sim.simulator --mode functional

# Run unified simulation (Python + RTL)
python -m sim.unified_simulator

# Run benchmark
python -m sim.benchmark

# Run tests by category
pytest tests/controller/ -v
pytest tests/dram/ -v
pytest tests/hbm4/ -v

# Run all tests
pytest tests/ -v

# Run RTL simulation
cd rtl && verilator --cc --trace hbm_controller.sv hbm_types.svh
```

## Test Status

| Category | Tests | Status |
|----------|-------|--------|
| Controller Tests | 98 | ✅ Passing |
| DRAM Tests | 22 | ✅ Passing |
| HBM4 DFI Tests | 34 | ✅ Passing |
| HBM4 PHY/TSV/Lane | 225+ | ✅ Passing |
| Simulation Tests | 72 | ✅ Passing |
| Integration Tests | 46 | ✅ Passing |
| **Total** | **497** | **All Passing** |

## HBM4 Support

- 32-channel architecture (2x HBM3)
- Speed grades: 8 Gbps, 12 Gbps, 16 Gbps
- Pseudo-channel support
- Bank group organization
- ECC/CRC error detection
- Lane repair capabilities
- PHY training sequences
- MBIST support

## Development Model

- AI-driven development with subagent parallelization
- User reviews designs, AI implements
- Phased approach: Design → Phase A → Phase B → Phase C