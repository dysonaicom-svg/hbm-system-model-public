# HBM System Model

HBM System Model 是一个面向芯片架构探索的 High Bandwidth Memory 系统建模项目。当前仓库包含两条主线：

- Python 事务级/时序近似模型：覆盖 HBM controller、DRAM bank/channel/stack 结构、refresh、调度和地址解码
- Ramulator2 trace-driven baseline：使用 CMU-SAFARI Ramulator2 子模块运行 HBM3 访问模式实验，用于校准和对比

## 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| Controller model | Complete | HBM4 32-channel, FR-FCFS/QoS, refresh scheduler |
| DRAM model | Complete | HBM3/HBM4 timing, bank state machine, PHY training, MBIST |
| Ramulator2 baseline | Complete | 顺序、stride、随机访问 HBM3 trace 实验 |
| RTL | Complete | hbm_types, hbm_pkg, hbm_controller, dram_model |
| UVM | Complete | Environment, tests, reference models |
| Tests | Active | 730+ test cases collected |

## 目录结构

```text
.
├── model/
│   ├── controller/          # HBM controller 事务级模型
│   │   ├── controller.py     # 主控制器
│   │   ├── hbm4_controller.py  # HBM4 增强控制器
│   │   ├── address_decoder.py  # 地址解码
│   │   ├── hbm4_address_decoder.py  # HBM4 32-ch 解码
│   │   ├── scheduler.py     # FR-FCFS 调度
│   │   ├── qos_scheduler.py   # QoS 调度
│   │   ├── hbm4_qos_scheduler.py  # HBM4 QoS
│   │   ├── refresh_scheduler.py  # Refresh 调度
│   │   ├── hbm4_refresh_scheduler.py  # HBM4 Refresh
│   │   ├── queue.py         # 请求队列
│   │   └── request.py       # 请求定义
│   ├── dram/                # DRAM timing、bank/channel 模型
│   │   ├── dram_model.py    # DRAM 模型
│   │   ├── hbm4_channel_model.py  # HBM4 channel
│   │   ├── hbm4_spec.py     # HBM4 规格
│   │   ├── timing.py        # 时序参数
│   │   ├── bank_state_machine.py  # Bank FSM
│   │   ├── phy_training.py  # PHY 训练
│   │   ├── mbist_controller.py  # MBIST
│   │   ├── power_estimator.py  # 功耗估算
│   │   ├── ecc_crc.py       # ECC/CRC
│   │   ├── lane_repair.py   # Lane repair
│   │   └── dfi_interface.py # DFI 接口
│   ├── interconnect/        # NoC/AXI 互联模型占位
│   └── phy/                 # PHY 模型占位
├── rtl/                      # RTL 实现
│   ├── hbm_types.svh        # 类型定义
│   ├── hbm_pkg.sv           # UVM package
│   ├── hbm_controller.sv   # Controller RTL
│   ├── dram_model.sv        # DRAM model RTL
│   └── hbm_controller_tb.cpp  # C++ testbench
├── verification/
│   ├── reference_model/     # 参考模型
│   └── uvm/                  # UVM 验证环境
├── research/
│   ├── hbm-modeling/         # Ramulator2 HBM3 baseline
│   ├── hbm4-logic-base-die/ # HBM4 logic base die 参考
│   ├── ramulator2/           # CMU-SAFARI Ramulator2
│   └── hbm3_spec.md          # HBM3 参数
├── tests/                    # Python 测试
│   ├── controller/           # Controller 测试
│   ├── dram/                 # DRAM 测试
│   ├── hbm4/                 # HBM4 测试
│   ├── sim/                  # 仿真测试
│   └── integration/          # 集成测试
├── tb/                       # Testbench
│   └── hbm_controller_tb.cpp # C++ testbench
└── sim/                      # 仿真输出
```

## 环境要求

Python 模型：

```bash
python3 -m pip install -r requirements.txt
```

Ramulator2 baseline：

- CMake 3.14+
- C++20 编译器
- 当前机器验证可用：`/usr/bin/clang++-18`

初始化子模块：

```bash
git submodule update --init --recursive
```

构建 Ramulator2：

```bash
cd research/ramulator2
cmake -S . -B build -DCMAKE_CXX_COMPILER=/usr/bin/clang++-18
cmake --build build -j
```

## 运行测试

```bash
python3 -m pytest tests -q
```

当前验证结果：

- 730+ test cases collected
- 7 collection errors (regression tests need HBM3Timing fix)

## 运行 HBM3 Baseline

```bash
research/hbm-modeling/scripts/run_baseline.sh
```

实验输入：

- `research/hbm-modeling/traces/seq_rd.trace`
- `research/hbm-modeling/traces/stride_rd.trace`
- `research/hbm-modeling/traces/random_rdwr.trace`

实验配置：

- DRAM model：HBM3
- Organization：`HBM3_2Gb`
- Timing：`HBM3_2Gbps`
- Scheduler：FRFCFS
- Row policy：OpenRowPolicy
- Frontend：SimpleO3 + RandomTranslation

结果汇总见：

```text
research/hbm-modeling/results/summary.md
```

当前 baseline 摘要：

| Pattern | Row hit rate | Avg read latency |
|---------|--------------|------------------|
| Sequential 64B | 87.5% | 30.95 cycles |
| Stride 4KB | 0.02% | 83.13 cycles |
| Random | 0.01% | 42.46 cycles |

## RTL/UVM 实现

### 目录结构
```text
rtl/
├── hbm_types.svh          # HBM 类型定义 (addr_t, req_type_t, bank_state_t, cmd_t, timing_t, req_t)
├── hbm_pkg.sv             # UVM package (hbm_configuration, hbm_transaction)
├── dram_model.sv          # DRAM behavioral model (bank FSM, memory array, timing)
├── hbm_controller.sv      # HBM controller RTL (addr decoder, queue, FR-FCFS, FSM)
└── hbm_controller_tb.cpp   # C++ testbench

verification/
├── reference_model/       # 参考模型
│   ├── dram_ref_model.sv  # DRAM 性能参考模型
│   ├── addr_decoder_ref.sv # 地址解码器参考 (6 种映射模式)
│   ├── bandwidth_calc.sv  # 带宽计算
│   └── timing_checker.sv  # 时序检查
└── uvm/                   # UVM 验证环境
    ├── hbm_env_pkg.sv     # Environment package
    ├── hbm_test_pkg.sv    # Test package (sequences + tests)
    ├── hbm_tb.sv          # Testbench top
    ├── Makefile           # Verilator 构建系统
    └── uvm.f              # 文件列表
```

### 运行 UVM 测试
```bash
cd verification/uvm
make
```

### 编译 RTL
```bash
cd rtl
verilator --cc --trace hbm_controller.sv hbm_types.svh
```

## Python 模型入口

主要组件：

- `model/controller/config.py`：HBM 配置、理论带宽计算
- `model/controller/address_decoder.py`：地址映射和解码
- `model/controller/hbm4_address_decoder.py`：HBM4 32-channel 地址解码
- `model/controller/scheduler.py`：FR-FCFS 调度
- `model/controller/hbm4_qos_scheduler.py`：HBM4 QoS 调度
- `model/controller/refresh_scheduler.py`：refresh 调度
- `model/controller/hbm4_controller.py`：HBM4 增强控制器
- `model/dram/timing.py`：HBM2/HBM3/HBM4 timing 参数
- `model/dram/bank_state_machine.py`：bank 状态机
- `model/dram/hbm4_channel_model.py`：HBM4 channel/pseudo-channel/bank-group 模型
- `model/dram/hbm4_spec.py`：HBM4 规格参数
- `model/dram/phy_training.py`：PHY 训练序列
- `model/dram/mbist_controller.py`：MBIST 控制器

示例：

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

controller = HBMController(HBM3_DEFAULT)
request = HBMRequest(addr=0x1000, length=64, is_read=True)
controller.submit_request(request)

for _ in range(100):
    controller.tick()

print(controller.get_stats())
```

## HBM4 支持

| Feature | Status |
|---------|--------|
| 32-channel architecture | Complete |
| Speed grades (8/12/16 Gbps) | Complete |
| Pseudo-channel support | Complete |
| Bank group organization | Complete |
| ECC/CRC error detection | Complete |
| Lane repair capabilities | Complete |
| PHY training sequences | Complete |
| MBIST support | Complete |
| DFI interface | Complete |

## 设计文档

- `docs/design/2026-06-15-hbm-system-model-design.md`
- `docs/superpowers/plans/2026-06-15-hbm-modeling-baseline.md`
- `research/hbm3_spec.md`
- `research/hbm-modeling/README.md`

## 已知约束

- HBM3 baseline 当前使用 Ramulator2 的公开 HBM3 preset，适合架构探索，不等价于供应商精确模型
- Ramulator2 HBM3 配置使用 OpenRowPolicy；ClosedRowPolicy 依赖 rank 层级，不适配当前 HBM3 层级
- `research/hbm-modeling/results/*.log` 是可再生输出，默认由 `.gitignore` 忽略；提交的是 `summary.md`
- 7 个 regression 测试有 collection error（HBM3Timing 未定义），需要修复

## 后续方向

- 修复 regression 测试中的 HBM3Timing 错误
- 增加 trace parser 和自动 summary 生成
- 将 Python controller model 和 DRAM model 接入统一仿真 loop
- 增加 AXI/NoC interconnect 模型和多 traffic source
- 引入 gem5 或 DRAMSys 做系统级联动仿真
- 将关键协议约束下沉到 SystemVerilog/UVM 验证环境