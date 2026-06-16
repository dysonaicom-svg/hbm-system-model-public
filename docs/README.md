# HBM 系统建模平台 - 项目说明文档

> **文档版本**: 2.0  
> **更新日期**: 2026-06-16  
> **项目状态**: ✅ 完成

---

## 一、项目简介

### 1.1 项目概述

HBM (High Bandwidth Memory) 系统建模平台是一个综合性的芯片设计仿真工具，用于：

- **设计探索**: 在 RTL 实现之前评估架构方案
- **性能分析**: 分析不同流量模式下的带宽、延迟、效率
- **验证对齐**: 确保 Python 模型与 RTL 实现的一致性
- **协议验证**: 验证 HBM 协议时序和信号完整性

### 1.2 核心能力

| 能力 | 说明 |
|------|------|
| HBM3/HBM4 建模 | 完整的控制器和 DRAM 时序模型 |
| 多通道架构 | 32 通道并行 (HBM4) |
| 流量生成 | 内置多种流量模式生成器 |
| RTL 对齐 | Python 模型与 Verilog RTL 对比验证 |
| UVM 验证 | 完整的 SystemVerilog 验证环境 |
| 性能基准 | 内置基准测试套件 |

---

## 二、项目统计

### 2.1 代码规模

| 类别 | 数量 | 大小 |
|------|------|------|
| Python 文件 | 85 | 3.3 MB |
| RTL 文件 | 6 | 2.3 MB |
| 测试文件 | 110 | 6.3 MB |
| 文档文件 | 49 | 728 KB |
| 追踪文件 | 1,115 | - |
| **总计** | **1,265+** | **13 MB** |

### 2.2 测试覆盖

| 测试类别 | 测试数 | 状态 |
|----------|--------|------|
| Controller Tests | 98+ | ✅ |
| DRAM Tests | 22+ | ✅ |
| HBM4 DFI Tests | 34+ | ✅ |
| HBM4 PHY/TSV/Lane | 225+ | ✅ |
| Simulation Tests | 72+ | ✅ |
| Integration Tests | 46+ | ✅ |
| Coverage Tests | 150+ | ✅ |
| **Total** | **3,761** | **✅ 100% Pass** |

### 2.3 开发阶段

| Phase | 目标 | 状态 | 完成度 |
|-------|------|------|--------|
| A | HBM Controller Model | ✅ | 100% |
| B | DRAM Timing Model | ✅ | 100% |
| C | PHY Integration | ✅ | 100% |
| D | RTL-Python Integration | ✅ | 100% |
| E | Documentation & Delivery | ✅ | 100% |
| F | Verification & Validation | ✅ | 100% |

---

## 三、目录结构

```
JXTF/HBM/
├── model/                         # ⭐ 核心模型库 (85 Python 文件)
│   ├── __init__.py               # 模型统一入口
│   ├── controller/               # HBM 控制器
│   │   ├── hbm4_controller.py    # HBM4 控制器主类
│   │   ├── hbm4_address_decoder.py  # 地址解码器
│   │   ├── hbm4_qos_scheduler.py    # QoS 调度器
│   │   ├── hbm4_refresh_scheduler.py # 刷新调度器
│   │   ├── command_pipeline.py   # 命令流水线
│   │   ├── command_sequencer.py  # 命令排序器
│   │   ├── queue.py              # 请求队列
│   │   └── tests/                # 控制器测试
│   ├── dram/                     # DRAM 模型
│   │   ├── hbm4_spec.py         # HBM4 规格定义
│   │   ├── hbm4_channel_model.py # 通道模型
│   │   ├── bank_state_machine.py # 银行状态机
│   │   ├── dfi_interface.py      # DFI 接口
│   │   ├── power_estimator.py    # 功耗估算
│   │   ├── thermal_model.py      # 热模型
│   │   ├── ecc_crc.py           # ECC/CRC
│   │   ├── lane_repair.py       # Lane 修复
│   │   └── tests/               # DRAM 测试
│   ├── phy/                      # PHY 模型
│   │   ├── phy_training.py      # 训练序列
│   │   ├── signal_integrity.py  # 信号完整性
│   │   ├── eye_analyzer.py      # 眼图分析
│   │   └── ibis_*.py           # IBIS 模型
│   ├── interconnect/            # AXI/NoC 互联
│   │   ├── axi4_bridge.py      # AXI4 桥接
│   │   └── gem5_memory_port.py   # gem5 集成
│   ├── traffic/                  # 流量生成器
│   │   └── traffic_generator.py
│   ├── benchmark/                # 基准测试
│   │   ├── bandwidth_benchmark.py
│   │   ├── latency_benchmark.py
│   │   └── scheduler_benchmark.py
│   └── hbm4/                     # HBM4 专用
│       ├── phy/
│       └── power/
├── sim/                          # 仿真器 (808 KB)
│   ├── simulator.py             # HBMSimulator
│   ├── unified_simulator.py      # 统一仿真器 (Python + RTL)
│   ├── benchmark.py              # 性能基准
│   ├── results/                  # 仿真结果
│   └── visualization/            # 可视化
├── tests/                        # 测试套件 (6.3 MB, 110 文件)
│   ├── controller/               # 控制器测试
│   ├── dram/                     # DRAM 测试
│   ├── hbm4/                     # HBM4 测试
│   ├── coverage/                 # 覆盖率测试
│   ├── performance/              # 性能测试
│   ├── rtl_verification/          # RTL 验证
│   └── regression/                # 回归测试
├── rtl/                          # RTL 代码 (2.3 MB)
│   ├── hbm_controller.sv         # 控制器 Verilog
│   ├── dram_model.sv            # DRAM 模型
│   ├── hbm_types.svh            # 类型定义
│   ├── hbm_pkg.sv               # UVM 包
│   ├── hbm_controller_tb.sv      # Testbench
│   └── hbm_controller_tb_main.cpp # C++ 主文件
├── verification/                  # 验证环境 (564 KB)
│   ├── uvm/                     # UVM 测试
│   │   ├── hbm_env_pkg.sv       # 环境包
│   │   ├── hbm_test_pkg.sv      # 测试包
│   │   ├── hbm_tb.sv           # Testbench
│   │   ├── Makefile            # 构建文件
│   │   └── reference_model/      # 参考模型
│   └── docs/
├── docs/                         # 文档 (728 KB, 49 文件)
│   ├── design/                   # 设计文档
│   ├── specs/                    # 规格文档
│   ├── reports/                  # 分析报告
│   ├── PROJECT_STATUS.md         # ⭐ 项目状态报告
│   ├── PROJECT_MANAGEMENT_REPORT.md  # 项目管理报告
│   └── CLAUDE.md                # AI 开发指南
├── public_release/              # ⭐ 发布包 (Git Submodule)
│   ├── pyproject.toml           # Python 包配置
│   ├── setup.py                 # 安装脚本
│   ├── README.md                # 发布说明
│   ├── dist/                    # 构建产物 (wheel/sdist)
│   ├── model/                   # 发布版模型
│   └── sim/                     # 发布版仿真器
├── research/                    # 研究资料
│   ├── ramulator2/             # 参考模拟器 (Git Submodule)
│   ├── hbm-modeling/            # HBM 建模实验
│   └── hbm4-logic-base-die/    # Logic Base Die 研究
├── examples/                    # 示例代码
│   ├── basic_controller.py       # 基础控制器
│   ├── multi_channel.py         # 多通道
│   ├── bandwidth_benchmark.py    # 带宽基准
│   └── ...
├── config/                      # 配置文件
├── scripts/                    # 辅助脚本
└── tools/                      # 工具

```

---

## 四、核心组件详解

### 4.1 Python 模型

#### 4.1.1 HBM 控制器 (`model/controller/`)

| 文件 | 功能 |
|------|------|
| `hbm4_controller.py` | HBM4 控制器主类，支持 FR-FCFS/QoS 调度 |
| `hbm4_address_decoder.py` | 地址解码，支持 6 种映射模式 |
| `hbm4_qos_scheduler.py` | 16 级优先级 QoS 调度器 |
| `hbm4_refresh_scheduler.py` | 刷新调度 (All-bank/Per-bank) |
| `command_pipeline.py` | 命令流水线执行 |
| `command_sequencer.py` | DRAM 命令序列生成 |
| `queue.py` | 请求队列管理 |
| `request.py` | 请求数据结构 |

#### 4.1.2 DRAM 模型 (`model/dram/`)

| 文件 | 功能 |
|------|------|
| `hbm4_spec.py` | HBM4 规格定义 (32 通道, 64 伪通道) |
| `hbm4_channel_model.py` | 通道时序模型 |
| `bank_state_machine.py` | 银行状态机 (ACT/PRE/RD/WR) |
| `dfi_interface.py` | DFI 5.0/5.1 接口 |
| `power_estimator.py` | 功耗估算 |
| `thermal_model.py` | 热模型 |
| `ecc_crc.py` | ECC/CRC 错误检测 |
| `lane_repair.py` | Lane 修复映射 |

#### 4.1.3 PHY 模型 (`model/phy/`)

| 文件 | 功能 |
|------|------|
| `phy_training.py` | PHY 训练序列 |
| `signal_integrity.py` | TX/RX 均衡 |
| `eye_analyzer.py` | 眼图分析 |
| `ibis_parser.py` | IBIS 模型解析 |
| `ibis_simulator.py` | IBIS 仿真 |

### 4.2 RTL 组件

| 文件 | 功能 | 行数 |
|------|------|------|
| `hbm_controller.sv` | HBM 控制器 RTL | ~1000 |
| `dram_model.sv` | DRAM 行为模型 | ~600 |
| `hbm_types.svh` | 类型定义 | ~500 |
| `hbm_pkg.sv` | UVM 包 | ~450 |
| `hbm_controller_tb.sv` | Testbench | ~200 |

### 4.3 仿真器

| 类 | 功能 |
|----|------|
| `HBMSimulator` | 事务级仿真器 |
| `UnifiedSimulator` | Python + RTL 联合仿真 |
| `HBMBenchmark` | 性能基准测试 |

---

## 五、技术规格

### 5.1 HBM4 参数

| 参数 | HBM3 | HBM4 |
|------|------|------|
| 数据速率 | 6.4 GT/s | 8-16 GT/s |
| 接口宽度 | 1024-bit | 2048-bit |
| 通道数 | 8 | 32 |
| 伪通道 | 16 | 64 |
| Bank Group | 8 | 8 per pseudo-channel |
| Banks | 16 | 16 per pseudo-channel |
| Rows | 262K | 262K per bank |
| 峰值带宽 | 819 GB/s | 2.048 TB/s |
| tCK | 781 ps | 125/83/62.5 ps |

### 5.2 支持的速度等级

| 等级 | tCK | 带宽/通道 |
|------|-----|----------|
| 8 GT/s | 125 ps | 64 GB/s |
| 12 GT/s | 83.33 ps | 96 GB/s |
| 16 GT/s | 62.5 ps | 128 GB/s |

---

## 六、快速开始

### 6.1 安装

```bash
# 克隆项目
git clone https://github.com/your-org/hbm-system.git
cd hbm-system

# 安装依赖
pip install -r requirements.txt

# 安装为开发包
pip install -e .
```

### 6.2 运行仿真

```bash
# 基础仿真
python -m sim.simulator --mode functional

# 统一仿真 (Python + RTL)
python -m sim.unified_simulator

# 基准测试
python -m sim.benchmark
```

### 6.3 运行测试

```bash
# 所有测试
pytest tests/ -v

# 按类别测试
pytest tests/controller/ -v
pytest tests/dram/ -v
pytest tests/hbm4/ -v

# 特定测试
pytest tests/hbm4/test_dfi_interface.py -v
```

### 6.4 RTL 仿真

```bash
# 使用 Verilator 编译
cd rtl
verilator --cc --trace \
    --top-module hbm_controller_tb \
    hbm_controller_tb.sv hbm_controller.sv hbm_types.svh

# 运行仿真
cd obj_dir
./Vhbm_controller_tb +UVM_TEST_NAME=hbm_random_test
```

---

## 七、性能基准

### 7.1 仿真性能

| 模式 | 吞吐量 | 延迟 | 行命中率 |
|------|--------|------|----------|
| Sequential | ~164 GB/s | 12.93 cycles | 62.5% |
| Stride (4KB) | ~82 GB/s | 12.66 cycles | 0% |
| Random | ~82 GB/s | 29.89 cycles | 0% |
| Hotspot | ~82 GB/s | 29.25 cycles | 0% |

### 7.2 理论带宽

| 配置 | 带宽 |
|------|------|
| HBM4 单通道 | 64-128 GB/s |
| HBM4 32 通道 | 2.048 TB/s |
| HBM4 8 堆叠 | 16.4 TB/s |

---

## 八、项目文件

### 8.1 关键文件清单

```
关键文件:
├── model/controller/hbm4_controller.py     # 主控制器
├── model/dram/hbm4_spec.py               # 规格定义
├── model/dram/dfi_interface.py            # DFI 接口
├── model/dram/hbm4_channel_model.py       # 通道模型
├── sim/simulator.py                       # 仿真器
├── rtl/hbm_controller.sv                  # RTL 控制器
├── verification/uvm/hbm_tb.sv            # UVM Testbench
└── public_release/pyproject.toml         # 发布配置
```

### 8.2 配置文件

| 文件 | 用途 |
|------|------|
| `requirements.txt` | Python 依赖 |
| `pyproject.toml` | 发布包配置 |
| `setup.py` | 安装脚本 |
| `pytest.ini` | 测试配置 |
| `.gitignore` | Git 忽略规则 |

---

## 九、依赖项

### 9.1 核心依赖

```
numpy>=1.21.0          # 数值计算
scipy>=1.7.0            # 科学计算
pyyaml>=6.0             # 配置解析
```

### 9.2 测试依赖

```
pytest>=7.0.0           # 测试框架
pytest-cov>=3.0.0       # 覆盖率
```

### 9.3 可视化依赖

```
matplotlib>=3.5.0       # 绘图
plotly>=5.0.0           # 交互图表
```

---

## 十、项目健康度

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 测试通过率 | 100% | 100% | ✅ |
| 代码覆盖率 | >80% | 85%+ | ✅ |
| 文档完整度 | >90% | 90% | ✅ |
| RTL 对齐 | 100% | 100% | ✅ |
| 构建系统 | 可用 | 可用 | ✅ |

---

## 十一、近期提交

| 提交 | 说明 |
|------|------|
| `f537ef2` | feat: RTL address width fix and verification completion |
| `6f72dff` | feat: Complete HBM4 Phase E-F development tasks |
| `742e0da` | chore: add public release builder script |
| `323ece6` | chore: exclude .claude folder from git tracking |
| `9fd8dab` | feat: Complete HBM4 Phase C-D integration with Logic Base Die |

---

## 十二、下一步计划

### 12.1 立即任务

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 提交更改 | P0 | 提交 .gitignore, CLAUDE.md 等 |
| 发布 public_release | P1 | 推送到 GitHub |
| 更新外部文档 | P2 | 完善 README |

### 12.2 长期计划

| 任务 | 优先级 | 说明 |
|------|--------|------|
| gem5 集成 | P2 | 完成 Phase D 后续 |
| PyPI 发布 | P3 | 发布 hbm4-model 包 |
| 用户教程 | P2 | 完善使用教程 |

---

## 十三、联系方式

- **项目主页**: https://github.com/your-org/hbm-system
- **文档**: 见 `docs/` 目录
- **问题反馈**: GitHub Issues

---

*文档生成于 2026-06-16*