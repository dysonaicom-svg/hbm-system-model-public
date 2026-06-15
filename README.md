# HBM System Modeling Platform

## Project Overview

HBM (High Bandwidth Memory) 系统仿真平台，支持芯片设计探索和验证对齐。项目包含两条主线：

- **Python 事务级/时序近似模型**：覆盖 HBM controller、DRAM bank/channel/stack 结构、refresh、调度和地址解码
- **Ramulator2 trace-driven baseline**：使用 CMU-SAFARI Ramulator2 子模块运行 HBM3 访问模式实验

## Project Status

All phases are now **Complete** :

| Phase | Goal | Status |
|-------|------|--------|
| A | HBM Controller Model | **Complete** |
| B | DRAM Timing Model | **Complete** |
| C | PHY Integration | **Complete** |
| D | RTL-Python Integration | **Active** |

## Architecture

```
                    ┌─────────────────────────────┐
                    │   Traffic Generator /       │
                    │   Trace Reader              │
                    └─────────────┬───────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │   Interconnect              │
                    │   (NoC / AXI)               │
                    └─────────────┬───────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │   HBM Controller             │
                    │   - Address Decoder         │
                    │   - Request Queue           │
                    │   - FR-FCFS / QoS Scheduler │
                    │   - Refresh Scheduler       │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────┴───────────────┐
                    │          DFI Interface        │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────────────────────┐
                    │   HBM DRAM Model             │
                    │   - Channel Model            │
                    │   - Bank State Machine       │
                    │   - PHY Training             │
                    │   - ECC/CRC                  │
                    │   - Lane Repair             │
                    └─────────────┬───────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │   Statistics Collector      │
                    └─────────────────────────────┘
```

## Quick Start

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize submodules
git submodule update --init --recursive
```

### Run Simulations

```bash
# Functional simulation
python -m sim.simulator --mode functional

# Unified simulation (Python + RTL)
python -m sim.unified_simulator

# Run benchmark
python -m sim.benchmark
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# By category
pytest tests/controller/ -v    # Controller tests
pytest tests/dram/ -v          # DRAM tests
pytest tests/hbm4/ -v          # HBM4 tests
pytest tests/integration/ -v    # Integration tests
pytest tests/coverage/ -v       # Coverage tests
```

### RTL Simulation

```bash
# Compile RTL with Verilator
cd rtl && verilator --cc --trace hbm_controller.sv hbm_types.svh

# Run UVM verification
cd verification/uvm && make
```

### Ramulator2 Baseline (Optional)

```bash
# Build Ramulator2
cd research/ramulator2
cmake -S . -B build -DCMAKE_CXX_COMPILER=/usr/bin/clang++-18
cmake --build build -j

# Run HBM3 baseline experiments
research/hbm-modeling/scripts/run_baseline.sh
```

## Test Results Summary

| Category | Tests | Status |
|----------|-------|--------|
| Controller Tests | 98 | Passing |
| DRAM Tests | 22 | Passing |
| HBM4 DFI Tests | 34 | Passing |
| HBM4 PHY/TSV/Lane | 225+ | Passing |
| Simulation Tests | 72 | Passing |
| Integration Tests | 46 | Passing |
| **Total** | **463** | **All Passing** |

## HBM4 Support

| Feature | Status |
|---------|--------|
| 32-channel architecture (2x HBM3) | Complete |
| Speed grades: 8 Gbps, 12 Gbps, 16 Gbps | Complete |
| Pseudo-channel support | Complete |
| Bank group organization | Complete |
| ECC/CRC error detection | Complete |
| Lane repair capabilities | Complete |
| PHY training sequences | Complete |
| MBIST support | Complete |
| DFI interface | Complete |

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

## Directory Structure

```
.
├── model/
│   ├── controller/          # HBM controller 事务级模型
│   │   ├── controller.py
│   │   ├── hbm4_controller.py
│   │   ├── address_decoder.py
│   │   ├── hbm4_address_decoder.py
│   │   ├── qos_scheduler.py
│   │   ├── hbm4_qos_scheduler.py
│   │   ├── refresh_scheduler.py
│   │   ├── hbm4_refresh_scheduler.py
│   │   ├── queue.py
│   │   └── request.py
│   ├── dram/                # DRAM timing、bank/channel 模型
│   │   ├── dram_model.py
│   │   ├── hbm4_channel_model.py
│   │   ├── hbm4_spec.py
│   │   ├── timing.py
│   │   ├── bank_state_machine.py
│   │   ├── phy_training.py
│   │   ├── mbist_controller.py
│   │   ├── power_estimator.py
│   │   ├── ecc_crc.py
│   │   ├── lane_repair.py
│   │   └── dfi_interface.py
│   └── interconnect/        # NoC/AXI 互联模型占位
├── rtl/                      # RTL 实现
│   ├── hbm_types.svh
│   ├── hbm_pkg.sv
│   ├── hbm_controller.sv
│   ├── dram_model.sv
│   └── hbm_controller_tb.cpp
├── verification/
│   ├── reference_model/     # 参考模型
│   └── uvm/                  # UVM 验证环境
├── research/
│   ├── hbm-modeling/         # Ramulator2 HBM3 baseline
│   ├── hbm4-logic-base-die/ # HBM4 logic base die 参考
│   └── ramulator2/           # CMU-SAFARI Ramulator2
├── tests/                    # Python 测试
│   ├── controller/
│   ├── dram/
│   ├── hbm4/
│   ├── sim/
│   ├── coverage/
│   └── integration/
├── docs/                     # 设计文档
├── sim/                       # 仿真输出
│   ├── unified_simulator.py  # Python + RTL 联合仿真
│   ├── interconnect/         # 互联模型
│   └── trace/               # Trace 解析器
└── scripts/                   # 工具脚本
```

## Key Documents

- [Design Document](docs/design/2026-06-15-hbm-system-model-design.md) - 完整设计规范
- [HBM3 Spec](docs/specs/hbm3_spec.md) - HBM3 参数参考
- [Ramulator2](research/ramulator2/) - 参考模拟器

## Example Usage

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

# Create controller
controller = HBMController(HBM3_DEFAULT)

# Submit request
request = HBMRequest(addr=0x1000, length=64, is_read=True)
controller.submit_request(request)

# Run simulation
for _ in range(100):
    controller.tick()

# Get statistics
print(controller.get_stats())
```

## Development Model

- AI-driven development with subagent parallelization
- User reviews designs, AI implements
- Phased approach: Design -> Phase A -> Phase B -> Phase C

## Future Directions

- Add trace parser and automatic summary generation
- Connect Python controller and DRAM models in unified simulation loop
- Add AXI/NoC interconnect model and multiple traffic sources
- Integrate with gem5 or DRAMSys for system-level simulation
- Push key protocol constraints to SystemVerilog/UVM verification environment