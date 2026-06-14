# HBM System Model

HBM System Model 是一个面向芯片架构探索的 High Bandwidth Memory 系统建模项目。当前仓库包含两条主线：

- Python 事务级/时序近似模型：覆盖 HBM controller、DRAM bank/channel/stack 结构、refresh、调度和地址解码。
- Ramulator2 trace-driven baseline：使用 CMU-SAFARI Ramulator2 子模块运行 HBM3 访问模式实验，用于校准和对比。

## 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| Controller model | 可运行 | 地址解码、请求队列、FR-FCFS/QoS 调度、refresh scheduler |
| DRAM model | 可运行 | HBM3 timing、bank state machine、channel、stack、row-hit 行为 |
| Ramulator2 baseline | 可运行 | 顺序、stride、随机访问三组 HBM3 trace 实验 |
| Tests | 通过 | 当前项目测试 `57 passed` |
| RTL/UVM | 占位 | `verification/uvm/` 目录已预留 |

## 目录结构

```text
.
├── model/
│   ├── controller/          # HBM controller 事务级模型
│   ├── dram/                # DRAM timing、bank/channel/stack 模型
│   ├── interconnect/        # NoC/AXI 互联模型占位
│   └── phy/                 # PHY 模型占位
├── research/
│   ├── hbm-modeling/        # Ramulator2 HBM3 baseline 配置、trace、结果
│   ├── hbm3_spec.md         # HBM3 参数整理
│   └── ramulator2/          # CMU-SAFARI Ramulator2 子模块
├── tests/
│   ├── controller/          # Controller 集成测试
│   └── dram/                # DRAM model 集成测试
├── docs/
│   ├── design/              # 系统设计文档
│   └── superpowers/plans/   # 执行计划
├── verification/            # reference model / UVM 验证占位
└── .claude/skills/          # Claude Code 本项目技能说明
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

```text
57 passed
```

说明：不要在仓库根目录直接运行无限定的 `pytest`，否则可能收集到 Ramulator2 第三方依赖中的上游测试。使用 `pytest tests` 限定本项目测试范围。

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

## Python 模型入口

主要组件：

- `model/controller/config.py`：HBM 配置、理论带宽计算
- `model/controller/address_decoder.py`：地址映射和解码
- `model/controller/scheduler.py`：FR-FCFS 调度
- `model/controller/qos_scheduler.py`：QoS 调度
- `model/controller/refresh_scheduler.py`：refresh 调度
- `model/controller/controller.py`：controller 集成模型
- `model/dram/timing.py`：HBM2/HBM3/HBM4 timing 参数
- `model/dram/bank_state_machine.py`：bank 状态机
- `model/dram/channel_model.py`：channel/pseudo-channel/bank-group 模型
- `model/dram/stack_model.py`：stack 和 DRAMModel 高层接口

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

## 设计文档

- `docs/design/2026-06-15-hbm-system-model-design.md`
- `docs/superpowers/plans/2026-06-15-hbm-modeling-baseline.md`
- `research/hbm3_spec.md`
- `research/hbm-modeling/README.md`

## 已知约束

- HBM3 baseline 当前使用 Ramulator2 的公开 HBM3 preset，适合架构探索，不等价于供应商精确模型。
- Ramulator2 HBM3 配置使用 OpenRowPolicy；ClosedRowPolicy 依赖 rank 层级，不适配当前 HBM3 层级。
- `research/hbm-modeling/results/*.log` 是可再生输出，默认由 `.gitignore` 忽略；提交的是 `summary.md`。
- HBM4 目前只有计划/参数占位，尚未建立经过验证的 baseline。

## 后续方向

- 增加 trace parser 和自动 summary 生成，避免手工维护结果表。
- 将 Python controller model 和 DRAM model 接入统一仿真 loop。
- 增加 AXI/NoC interconnect 模型和多 traffic source。
- 引入 gem5 或 DRAMSys 做系统级联动仿真。
- 将关键协议约束下沉到 SystemVerilog/UVM 验证环境。
