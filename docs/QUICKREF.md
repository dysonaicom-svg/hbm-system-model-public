# HBM 项目快速参考

> 简洁的项目状态和命令速查

---

## 📊 一、项目状态

| 项目 | 值 |
|------|-----|
| 分支 | `hbm4-phase-cd` |
| 测试数 | **3,761** ✅ |
| Python 文件 | 85 |
| RTL 文件 | 6 |
| 开发阶段 | Phase A-F ✅ 完成 |
| 最新提交 | `f537ef2` |

---

## 🚀 二、快速命令

```bash
# 安装
pip install -r requirements.txt
pip install -e .

# 仿真
python -m sim.simulator --mode functional
python -m sim.unified_simulator
python -m sim.benchmark

# 测试
pytest tests/ -v                    # 所有测试
pytest tests/controller/ -v          # 控制器
pytest tests/dram/ -v                # DRAM
pytest tests/hbm4/ -v                # HBM4

# RTL
cd rtl && verilator --cc --trace hbm_controller.sv hbm_types.svh
```

---

## 📁 三、核心文件

```
model/
├── controller/
│   ├── hbm4_controller.py      # 主控制器
│   ├── hbm4_address_decoder.py  # 地址解码
│   ├── hbm4_qos_scheduler.py     # QoS 调度
│   └── queue.py                  # 请求队列
├── dram/
│   ├── hbm4_spec.py             # 规格定义
│   ├── hbm4_channel_model.py     # 通道模型
│   ├── bank_state_machine.py     # 银行状态机
│   └── dfi_interface.py         # DFI 接口
└── phy/
    ├── phy_training.py           # 训练序列
    └── signal_integrity.py       # 信号完整性

sim/
├── simulator.py                  # HBMSimulator
├── unified_simulator.py          # 统一仿真器
└── benchmark.py                  # 基准测试

rtl/
├── hbm_controller.sv           # RTL 控制器
├── dram_model.sv              # DRAM 模型
└── hbm_types.svh              # 类型定义
```

---

## 📈 四、性能基准

| 模式 | 吞吐量 | 延迟 | 行命中率 |
|------|--------|------|----------|
| Sequential | ~164 GB/s | 12.93 cyc | 62.5% |
| Random | ~82 GB/s | 29.89 cyc | 0% |
| Stride | ~82 GB/s | 12.66 cyc | 0% |

**峰值带宽**: 2.048 TB/s (HBM4 @ 16 GT/s)

---

## 🔧 五、配置参数

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

## 📚 六、关键文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 项目说明 | `docs/README.md` | 完整项目文档 |
| 项目状态 | `docs/PROJECT_STATUS.md` | 状态报告 |
| 设计规范 | `docs/design/2026-06-15-hbm-system-model-design.md` | 设计文档 |
| AI 指南 | `CLAUDE.md` | AI 开发指南 |
| 主 README | `README.md` | 外部文档 |

---

## 🧪 七、测试类别

```
tests/
├── controller/    # 控制器测试 (98+)
├── dram/         # DRAM 测试 (22+)
├── hbm4/         # HBM4 测试 (225+)
├── coverage/     # 覆盖率测试 (150+)
├── simulation/   # 仿真测试 (72+)
└── integration/  # 集成测试 (46+)
```

---

## ⚠️ 八、常见问题

### Q: 队列满
```python
stats = controller.get_stats()
if stats['queues']['read_depth'] < 256:
    controller.submit_request(...)
```

### Q: 地址对齐
```python
addr = original_addr & ~0x7  # 8-byte aligned
```

### Q: RTL 编译
```bash
verilator --cc --trace --top-module hbm_controller_tb \
    hbm_controller_tb.sv hbm_controller.sv hbm_types.svh
```

---

## 📋 九、任务清单

- [ ] 提交清理更改 (.gitignore, CLAUDE.md)
- [ ] 推送 public_release 到 GitHub
- [ ] 完善外部 README
- [ ] (可选) gem5 集成
- [ ] (可选) PyPI 发布

---

*快速参考 - 2026-06-16*