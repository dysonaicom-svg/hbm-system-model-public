# HBM System Modeling Platform

## Project Overview

HBM (High Bandwidth Memory) 系统仿真平台，支持芯片设计探索和验证对齐。

**Current Branch**: `feat/hbm4-logic-base-die-phase2` (→ `master`)
**Main Branch**: `master`
**Current Version**: 2.2.0 | **Development Phase**: Phase G-J ✅ Complete | **Tests**: 4,409+ Passing

## Architecture

```
Traffic Generator / Trace Reader
        ↓
Interconnect (NoC / AXI)
        ↓
HBM Controller (Phase A-J ✅)
        ↓
HBM DRAM Model (Phase B ✅)
        ↓
DFI 5.0 Interface (Phase C ✅)
        ↓
Logic Base Die (Phase G ✅)
        ↓
Statistics Collector
```

**Verified**: RTL-Python alignment < 1% error | 100% test pass rate | v2.2.0

## Key Phases

| Phase | Goal | Status |
|-------|------|--------|
| 0 | Project Initialization | ✅ **Complete** |
| A | HBM Controller Model | ✅ **Complete** |
| B | DRAM Timing Model | ✅ **Complete** |
| C | PHY Integration | ✅ **Complete** |
| D | RTL-Python Integration | ✅ **Complete** |
| E | Documentation & Delivery | ✅ **Complete** |
| F | Verification & Validation | ✅ **Complete** |
| G | Logic Base Die Core | ✅ **Complete** |
| H | Unified Simulator | ✅ **Complete** |
| I | Performance Optimization | ✅ **Complete** |
| J | Controller Integration | ✅ **Complete** |

### Phase 3 Highlights (Unified Simulator)

| Feature | Status |
|---------|--------|
| Python-RTL Co-simulation | ✅ Complete |
| Performance Benchmark Suite | ✅ Complete |
| Result Comparison Analysis | ✅ Complete |
| Visualization Tools | ✅ Complete |

**Key Files Added:**
- `sim/rtl_interface.py` - RTL co-simulation interface
- `sim/benchmark_suite.py` - Performance benchmark suite
- `sim/result_comparison.py` - Result comparison analysis
- `sim/visualization/advanced_charts.py` - ASCII visualization

## Key Components

### Python Models

| Component | Files | Status |
|-----------|-------|--------|
| Controller | `controller.py`, `HBM4_controller.py` | ✅ Complete |
| Address Decoder | `address_decoder.py`, `HBM4_address_decoder.py` | ✅ Complete |
| QoS Scheduler | `qos_scheduler.py`, `HBM4_qos_scheduler.py` | ✅ Complete |
| Refresh Scheduler | `refresh_scheduler.py`, `HBM4_refresh_scheduler.py` | ✅ Complete |
| Request Queue | `queue.py`, `request.py` | ✅ Complete |
| DRAM Timing | `timing.py`, `HBM4_spec.py` | ✅ Complete |
| Channel Model | `channel_model.py`, `HBM4_channel_model.py` | ✅ Complete |
| Bank State Machine | `bank_state_machine.py`, `HBM4_bank_state_machine.py` | ✅ Complete |
| PHY Training | `phy_training.py` | ✅ Complete |
| MBIST Controller | `mbist_controller.py` | ✅ Complete |
| Power Estimator | `power_estimator.py` | ✅ Complete |
| ECC/CRC | `ecc_crc.py` | ✅ Complete |
| Lane Repair | `lane_repair.py` | ✅ Complete |
| DFI Interface | `dfi_interface.py` | ✅ Complete |
| Logic Base Die | `logic_base_die.py` | ✅ Complete |
| Thermal Model | `thermal_model.py` | ✅ Complete |
| Compliance | `HBM4_compliance.py` | ✅ Complete |
| Validation | `HBM4_validation.py` | ✅ Complete |

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

### Simulation Tools

| Component | Files | Status |
|-----------|-------|--------|
| Trace Replayer | `trace_replayer.py` | ✅ Complete |
| RTL Interface | `rtl_interface.py` | ✅ Complete |
| Unified Simulator | `hbm4_unified_simulator.py` | ✅ Complete |
| Result Comparison | `result_comparison.py` | ✅ Complete |
| Advanced Visualization | `visualization/advanced_charts.py` | ✅ Complete |
| Benchmark Suite | `benchmark_suite.py` | ✅ Complete |

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

# Run HBM4 unified simulator
python -m sim.hbm4_unified_simulator --mode full --channels 32

# Run benchmark
python -m sim.benchmark

# Trace replay (requires Ramulator2 traces)
python -m sim.trace_replayer --trace traces/ld_st.trace --format ramulator_ld_st

# Result comparison (Python vs RTL)
python -m sim.result_comparison --python results.json --rtl rtl_results.json

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
| Controller Tests | 411+ | ✅ Passing |
| DRAM Tests | 1000+ | ✅ Passing |
| HBM4 Tests | 700+ | ✅ Passing |
| Integration Tests | 100+ | ✅ Passing |
| Simulation Tests | 64+ | ✅ Passing |
| Verification Tests | 62+ | ✅ Passing |
| Benchmark Tests | 200+ | ✅ Passing |
| Traffic Tests | 117+ | ✅ Passing |
| Interconnect Tests | 129+ | ✅ Passing |
| PHY Tests | 178+ | ✅ Passing |
| Coverage Tests | 362+ | ✅ Passing |
| Performance Tests | 61+ | ✅ Passing |
| RTL Verification | 146+ | ✅ Passing |
| Sim Tests | 190+ | ✅ Passing |
| **Total** | **4,409+** | ✅ **All Passing** |

**Test Files**: 120+ test files with comprehensive coverage
**Pass Rate**: 100%

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
- PAM3 encoding for signal integrity
- Per-channel independent timing (JEDEC requirement)
- DFI 5.0/5.1 interface support

## HBM4 Specifications

| Parameter | Value |
|-----------|-------|
| Data Rate | 8-16 GT/s |
| Interface Width | 2048-bit |
| Channels | 32 |
| Peak Bandwidth | 4.096 TB/s |
| Stacks | 1-8 configurable |

## Development Model

- AI-driven development with subagent parallelization
- User reviews designs, AI implements
- Phased approach: Design → Phase 0 → A → B → C → D → E → F → G → H → I → J
- Multi-agent parallel execution (4-6 agents simultaneously)
- ~5 min total execution time for parallel phases
- **Current**: Phase G-J Complete (Ready for merge to master)

## Performance Benchmarks

| Pattern | Completed | Avg Latency | Row Hit Rate |
|---------|-----------|-------------|--------------|
| Sequential | 64,506 | 9.83 cycles | 62.5% |
| Random | 76,858 | 29.94 cycles | 0% |
| Hotspot | 76,790 | 27.83 cycles | 10% |

*Peak Bandwidth: 4.096 TB/s (HBM4 @ 16 GT/s) | Achieved: ~160 GB/s (16 channels)*

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
JXTF/HBM4/
├── model/           # Python 模型
│   ├── controller/  # HBM 控制器
│   ├── dram/        # DRAM 模型
│   ├── phy/         # PHY 模型
│   ├── interconnect/  # AXI/NoC 互联
│   └── benchmark/    # 基准测试
├── sim/              # 仿真器
│   ├── simulator.py              # HBMSimulator
│   ├── hbm4_unified_simulator.py # HBM4 统一仿真器
│   ├── trace_replayer.py         # Trace 回放
│   ├── rtl_interface.py         # RTL 协同仿真
│   ├── result_comparison.py      # 结果对比
│   ├── visualization/            # 可视化
│   │   └── advanced_charts.py
│   └── benchmark_suite.py       # 基准测试套件
├── rtl/              # RTL 实现
│   ├── hbm_controller.sv
│   ├── dram_model.sv
│   └── hbm_types.svh
├── verification/     # 验证环境
│   ├── uvm/          # UVM 测试
│   └── reference_model/
├── tests/            # 测试套件 (4,409+ 测试, 120+ 文件)
├── public_release/   # 发布包 (Git Submodule)
└── research/        # 研究资料
    └── ramulator2/    # 参考模拟器
```

## Key Files

| File | Description |
|------|-------------|
| `model/controller/HBM4_controller.py` | HBM4 Controller Core |
| `model/dram/HBM4_channel_model.py` | HBM4 Channel Model |
| `model/dram/logic_base_die.py` | Logic Base Die (Unified Control Die) |
| `model/dram/HBM4_bank_state_machine.py` | HBM4 Bank State Machine |
| `model/dram/phy_training.py` | PHY Training Sequences |
| `model/dram/dfi_interface.py` | DFI 5.0/5.1 Interface |
| `sim/simulator.py` | Transaction-level Simulator |
| `sim/hbm4_unified_simulator.py` | HBM4 Unified Simulator (32-channel) |
| `sim/trace_replayer.py` | Trace Replayer for Ramulator2 |
| `sim/rtl_interface.py` | RTL Co-simulation Interface |
| `sim/result_comparison.py` | Python vs RTL Result Comparison |
| `rtl/hbm_controller.sv` | RTL Controller Implementation |

## Ramulator2 Integration

The project includes [Ramulator2](https://github.com/CMU-SAFARI/ramulator2) as a git submodule for reference simulation and trace generation.

```bash
# Clone with submodules
git clone --recursive https://github.com/dysonaicom-svg/hbm-system-model-public.git

# Update submodule
git submodule update --init research/ramulator2
```

### Trace Replay Workflow

1. Generate traces with Ramulator2:
   ```bash
   cd research/ramulator2
   ./ramulator configs/HBM4.cfg --mode=trace ... > trace.ldst
   ```

2. Replay traces with Python model:
   ```bash
   python -m sim.trace_replayer --trace trace.ldst --format ramulator_ld_st
   ```

3. Compare results:
   ```bash
   python -m sim.result_comparison --python model.json --rtl rtl.json
   ```