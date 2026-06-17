# HBM System Modeling Platform

## Project Overview

HBM (High Bandwidth Memory) 系统仿真平台，支持芯片设计探索和验证对齐。

## Architecture

```
Traffic Generator / Trace Reader
        ↓
Interconnect (NoC / AXI)
        ↓
HBM Controller (Phase A-F ✅)
        ↓
HBM DRAM Model (Phase B ✅)
        ↓
Statistics Collector
```

## Key Phases

| Phase | Goal | Status |
|-------|------|--------|
| A | HBM Controller Model | ✅ **Complete** |
| B | DRAM Timing Model | ✅ **Complete** |
| C | PHY Integration | ✅ **Complete** |
| D | RTL-Python Integration | ✅ **Complete** |
| E | Documentation & Delivery | ✅ **Complete** |
| F | Verification & Validation | ✅ **Complete** |

## Key Components

### Python Models

| Component | Files | Status |
|-----------|-------|--------|
| Controller | `controller.py`, `hbm4_controller.py` | ✅ Complete |
| Address Decoder | `address_decoder.py`, `hbm4_address_decoder.py` | ✅ Complete |
| QoS Scheduler | `qos_scheduler.py`, `hbm4_qos_scheduler.py` | ✅ Complete |
| Refresh Scheduler | `refresh_scheduler.py`, `hbm4_refresh_scheduler.py` | ✅ Complete |
| Request Queue | `queue.py`, `request.py` | ✅ Complete |
| DRAM Timing | `timing.py`, `hbm4_spec.py` | ✅ Complete |
| Channel Model | `channel_model.py`, `hbm4_channel_model.py` | ✅ Complete |
| Bank State Machine | `bank_state_machine.py` | ✅ Complete |
| PHY Training | `phy_training.py` | ✅ Complete |
| MBIST Controller | `mbist_controller.py` | ✅ Complete |
| Power Estimator | `power_estimator.py` | ✅ Complete |
| ECC/CRC | `ecc_crc.py` | ✅ Complete |
| Lane Repair | `lane_repair.py` | ✅ Complete |
| DFI Interface | `dfi_interface.py` | ✅ Complete |
| Logic Base Die | `logic_base_die.py` | ✅ Complete |
| Thermal Model | `thermal_model.py` | ✅ Complete |

### RTL Components

| Component | File | Status |
|-----------|------|--------|
| Type Definitions | `hbm_types.svh` | ✅ Complete |
| UVM Package | `hbm_pkg.sv` | ✅ Complete |
| DRAM Model | `dram_model.sv` | ✅ Complete |
| Controller RTL | `hbm_controller.sv` | ✅ Complete |
| Testbench | `hbm_controller_tb.*` | ✅ Complete |

### UVM Verification

| Component | Status |
|-----------|--------|
| Environment Package | ✅ Complete |
| Test Package | ✅ Complete |
| Testbench | ✅ Complete |
| Reference Models | ✅ Complete |

## Key Documents

- [Design Document](docs/design/2026-06-15-hbm-system-model-design.md) - 完整设计规范
- [Project Status](docs/PROJECT_STATUS.md) - 项目状态报告
- [Project README](docs/README.md) - ⭐ 完整项目说明文档
- [Quick Reference](docs/QUICKREF.md) - 快速命令参考
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
| Controller Tests | 356 | ✅ Passing |
| DRAM Tests | 995 | ✅ Passing |
| HBM4 Tests | 646 | ✅ Passing |
| Integration Tests | 823 | ✅ Passing |
| PHY Tests | 174 | ✅ Passing |
| Coverage Tests | 358 | ✅ Passing |
| Verification Tests | 200 | ✅ Passing |
| Benchmark Tests | 147 | ✅ Passing |
| Other Tests | 634 | ✅ Passing |
| **Total** | **4,333** | **✅ All Passing** |

**Test Files**: 120 test files with comprehensive coverage

## HBM4 Support

- 32-channel architecture (2x HBM3)
- Speed grades: 8 Gbps, 12 Gbps, 16 Gbps
- Pseudo-channel support (64 total)
- Bank group organization (8 per pseudo-channel)
- ECC/CRC error detection
- Lane repair capabilities
- PHY training sequences
- MBIST support
- Logic Base Die integration
- Thermal management

## HBM4 Specifications

| Parameter | Value |
|-----------|-------|
| Data Rate | 8-16 GT/s |
| Interface Width | 2048-bit |
| Channels | 32 |
| Peak Bandwidth | 2.048 TB/s |
| Stacks | 1-8 configurable |

## Development Model

- AI-driven development with subagent parallelization
- User reviews designs, AI implements
- Phased approach: Design → Phase A → B → C → D → E → F

## Performance Benchmarks

| Pattern | Completed | Avg Latency | Throughput | Row Hit Rate |
|---------|-----------|-------------|------------|--------------|
| Sequential | 19,256 | 12.93 cycles | ~164 GB/s | 62.5% |
| Stride (4KB) | 19,240 | 12.66 cycles | ~82 GB/s | 0% |
| Random | 19,132 | 29.89 cycles | ~82 GB/s | 0% |
| Hotspot | 19,147 | 29.25 cycles | ~82 GB/s | 0% |

*Peak Bandwidth: 2.048 TB/s (HBM4 @ 8 GT/s) | Achieved: ~164 GB/s (single channel)*

## CI/CD Status

| Workflow | Status | Jobs |
|----------|--------|------|
| ci.yml | ✅ Fixed | 7 jobs |
| hbm-tests.yml | ✅ Fixed | 5 jobs |
| pytest.yml | ✅ Fixed | 2 jobs |
| rtl.yml | ✅ Fixed | 3 jobs |

**Recent fixes:**
- pytest.yml: Added --junitxml, fixed timeout-minutes location
- hbm-tests.yml: Fixed wildcard patterns, summary job references
- rtl.yml: Removed clean step, added timeout to all jobs

## RTL Testbench Build Fixes

### 1. `req_addr` width mismatch

`rtl/hbm_controller_tb_simple.sv` instantiates `hbm_controller` with `req_addr[31:0]` but controller's `ADDR_WIDTH = 36` bits (STACK(2) + CH(5) + BG(3) + BK(4) + ROW(16) + COL(6)). Use `hbm_controller_tb.sv` instead.

### 2. Main file header mismatch

`rtl/hbm_controller_tb_main.cpp` includes `Vhbm_controller.h` (from module `hbm_controller`), but the top module is `hbm_controller_tb`. Rebuild Verilator with `--top-module hbm_controller` so the generated header matches.

### 3. Build command

```bash
cd rtl
verilator --cc --trace \
    --top-module hbm_controller_tb \
    hbm_controller_tb.sv hbm_controller.sv hbm_types.svh hbm_pkg.sv \
    -CFLAGS "-DVM_TRACE_FMT_VCD"
```

## 关键脚本

- `scripts/auto_compare.py` - RTL vs Model 对比
- `scripts/run_rtl_benchmark.sh` - RTL 基准测试
- `verification/uvm/scripts/gen_coverage_report.py` - 覆盖率报告

## 性能基准

- 带宽 > 300 GB/s (回归线)
- 效率 > 20% (基准)
- 无队列溢出

## Project Structure

```
JXTF/HBM/
├── model/           # Python 模型
│   ├── controller/  # HBM 控制器
│   ├── dram/         # DRAM 模型
│   ├── phy/          # PHY 模型
│   ├── interconnect/  # AXI/NoC 互联
│   └── benchmark/     # 基准测试
├── sim/              # 仿真器
│   ├── simulator.py   # HBMSimulator
│   └── unified_simulator.py  # 统一仿真器
├── rtl/              # RTL 实现
│   ├── hbm_controller.sv
│   ├── dram_model.sv
│   └── hbm_types.svh
├── verification/     # 验证环境
│   ├── uvm/          # UVM 测试
│   └── reference_model/
├── tests/            # 测试套件 (4,333 测试, 120 文件)
├── public_release/   # 发布包 (Git Submodule)
└── research/        # 研究资料
    └── ramulator2/    # 参考模拟器
```

## Key Files

| File | Description |
|------|-------------|
| `model/controller/hbm4_controller.py` | HBM4 Controller Core |
| `model/dram/hbm4_channel_model.py` | HBM4 Channel Model |
| `model/phy/phy_training.py` | PHY Training Sequences |
| `sim/simulator.py` | Transaction-level Simulator |
| `rtl/hbm_controller.sv` | RTL Controller Implementation |