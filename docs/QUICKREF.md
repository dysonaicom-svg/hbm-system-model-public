# HBM 项目快速参考

> 简洁的项目状态和命令速查

*Last Updated: 2026-06-25*

---

## 一、项目状态

| 项目 | 值 |
|------|-----|
| 分支 | `feat/hbm4-logic-base-die-phase2` |
| 版本 | 2.5.0 |
| 测试数 | **4,409+** ✅ |
| Python 文件 | 150+ |
| RTL 文件 | 7 |
| 开发阶段 | Phase 0-8/A-J 全部完成 |
| 最新提交 | `84584f7` |

---

## 🚀 二、快速命令

```bash
# 安装
pip install -r requirements.txt
pip install -e .

# 仿真
python -m sim.simulator --mode functional
python -m sim.hbm4_unified_simulator --mode full --channels 32
python -m sim.benchmark

# 测试
pytest tests/ -v                    # 所有测试
pytest tests/controller/ -v          # 控制器
pytest tests/dram/ -v               # DRAM
pytest tests/hbm4/ -v               # HBM4
pytest tests/integration/ -v         # 集成
pytest tests/sim/ -v                # 仿真

# RTL
cd rtl && verilator --cc --trace --top-module hbm_controller_tb \
    hbm_controller_tb.sv hbm_controller.sv hbm_types.svh hbm_pkg.sv
```

---

## 🎯 三、5分钟入门指南

详细的入门指南请参考: [QUICKSTART.md](./QUICKSTART.md)

### 快速开始 (5行代码)

```python
from sim.simulator import HBMSimulator

sim = HBMSimulator(channels=32, data_rate_gbps=16)
sim.submit_request(addr=0x1000, size=64, is_write=False)
sim.run(cycles=100)
stats = sim.get_stats()
print(f"Bandwidth: {stats['bandwidth_gbps']:.2f} GB/s")
```

### 常用模式

```python
# 顺序访问 (高行命中率)
TrafficGenerator(pattern="sequential")

# 随机访问
TrafficGenerator(pattern="random")

# 跨步访问 (向量处理)
TrafficGenerator(pattern="stride")
```

---

## 📁 四、核心文件

```
model/
├── controller/
│   ├── HBM4_controller.py          # 主控制器
│   ├── HBM4_address_decoder.py     # 地址解码
│   ├── HBM4_qos_scheduler.py       # QoS 调度
│   ├── HBM4_refresh_scheduler.py    # 刷新调度
│   ├── queue.py                    # 请求队列
│   ├── scheduler.py               # 调度器
│   └── dfi_encoder.py             # DFI 编码器
├── dram/
│   ├── HBM4_spec.py               # 规格定义
│   ├── HBM4_channel_model.py       # 通道模型
│   ├── HBM4_bank_state_machine.py  # 银行状态机
│   ├── logic_base_die.py          # Logic Base Die (统一控制芯片)
│   ├── dfi_interface.py           # DFI 接口
│   ├── phy_training.py            # PHY 训练
│   ├── lane_repair.py             # Lane 修复
│   ├── ecc_crc.py                 # ECC/CRC
│   ├── power_estimator.py         # 功耗估算
│   └── thermal_model.py          # 热模型
└── phy/
    ├── signal_integrity.py         # 信号完整性
    └── eye_analyzer.py            # 眼图分析

sim/
├── simulator.py                    # HBMSimulator
├── hbm4_unified_simulator.py      # HBM4统一仿真器
├── benchmark_suite.py             # 性能基准测试套件
├── trace_replayer.py              # Trace回放
├── rtl_interface.py               # RTL协同仿真
└── result_comparison.py           # 结果对比

rtl/
├── hbm_controller.sv              # RTL 控制器
├── dram_model.sv                  # DRAM 模型
├── hbm_types.svh                  # 类型定义
└── hbm_pkg.sv                     # UVM 包
```

---

## 📈 五、性能基准

| 模式 | 吞吐量 | 延迟 | 行命中率 |
|------|--------|------|----------|
| Sequential | ~164 GB/s | 12.93 cyc | 62.5% |
| Random | ~82 GB/s | 29.89 cyc | 0% |
| Stride | ~82 GB/s | 12.66 cyc | 0% |
| Hotspot | ~82 GB/s | 29.25 cyc | 0% |

**峰值带宽**: 4.096 TB/s (HBM4 @ 16 GT/s, 32 channels)

---

## 🔧 六、配置参数

### HBM4 配置

```python
# 速度等级
8 GT/s:   tCK = 125 ps
12 GT/s:  tCK = 83.33 ps
16 GT/s:  tCK = 62.5 ps

# 架构
Channels:     32
Pseudo-Ch:    64
Bank Groups:   8 per pseudo-channel
Banks:        16 per pseudo-channel
Interface:    2048-bit
```

---

## 📚 七、关键文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 项目说明 | `README.md` | 完整项目文档 |
| AI 指南 | `CLAUDE.md` | AI 开发指南 |
| 项目状态 | `docs/README.md` | 内部文档 |
| 设计规范 | `docs/design/2026-06-15-hbm-system-model-design.md` | 设计文档 |
| 快速参考 | `docs/QUICKREF.md` | 命令速查 |
| Phase 3 计划 | `docs/plans/2026-06-17-phase3-development-plan.md` | 开发计划 |

---

## 🧪 八、测试类别

```
tests/
├── controller/    # 控制器测试 (360+)
├── dram/         # DRAM 测试 (1009+)
├── hbm4/         # HBM4 测试 (650+)
├── sim/          # 仿真测试 (190+)
├── integration/  # 集成测试 (827+)
├── coverage/     # 覆盖率测试 (362+)
├── performance/  # 性能测试 (61+)
├── benchmark/    # 基准测试 (184+)
├── verification/  # 验证测试 (62+)
└── rtl/          # RTL 测试 (146+)
```

**总计**: 4,409+ 测试用例

---

## ⚠️ 九、常见问题

### Q: 队列满
```python
# 增加队列深度
from model.controller.config import HBMConfig
config = HBMConfig(queue_depth=512)
controller = HBMController(config)

# 或使用节流
sim.set_throttle(requests_per_cycle=0.8)
```

### Q: 地址对齐错误
```python
addr = original_addr & ~0x7  # 8-byte aligned
addr = original_addr & ~0x3F  # 64-byte aligned (cache line)
```

### Q: 导入错误
```bash
pip uninstall hbm4-platform
pip install -e .
```

### Q: 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)
sim = HBMSimulator(debug=True)
```

### Q: RTL 编译
```bash
verilator --cc --trace --top-module hbm_controller_tb \
    hbm_controller_tb.sv hbm_controller.sv hbm_types.svh
```

### Q: 性能分析
```python
sim = HBMSimulator(profile=True)
sim.run(cycles=10000)
profile = sim.get_profile()
for comp, cycles in sorted(profile.items(), key=lambda x: -x[1]):
    print(f"{comp}: {cycles} cycles")
```

---

## 📋 十、任务清单

- [x] Phase 0 Project Initialization
- [x] Phase A-J HBM Controller/DRAM/PHY
- [x] Phase G Logic Base Die 核心功能
- [x] Phase H Unified Simulator
- [x] Phase I Performance Optimization
- [x] Phase J Controller Integration
- [x] Phase 5 HBM4 Controller Integration
- [x] Phase 6 Performance, Features, Verification
- [x] Phase 7 Performance Optimization (BankStateCache, Prefetch, ErrorRecovery)
- [x] Phase 8 RTL Auto-Sync Tool
- [ ] 合并到 master 分支
- [ ] (可选) gem5 集成
- [ ] (可选) PyPI 发布

---

*快速参考 - 2026-06-23*