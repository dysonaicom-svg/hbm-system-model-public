# HBM4 Logic Base Die 建模仿真完整实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 建立完整的HBM4 Logic Base Die建模仿真平台，支持芯片设计探索和验证对齐。

**Architecture:** 
- 采用模块化分层架构：Traffic Generator → Interconnect → HBM Controller → DFI Interface → PHY → DRAM Model
- Logic Base Die 包含：Controller、Address Decoder、QoS Scheduler、Refresh Scheduler、DFI Interface
- 支持32通道、2048-bit接口、8 GT/s传输速率

**Tech Stack:** Python 3.8+, pytest, SystemVerilog/UVM, Verilator

---

## Phase 1: 核心模型完善

### Task 1.1: 完善 Logic Base Die 核心模块

**Files:**
- Modify: `model/dram/logic_base_die.py`
- Test: `tests/hbm4/test_logic_base_die.py`

**Step 1: 增强 Logic Base Die 模型**

Logic Base Die 是HBM4的核心逻辑层，需要包含：
- DFI 5.0 接口控制器
- 32通道地址解码器
- Bank状态管理
- 命令调度器接口

```python
# model/dram/logic_base_die.py 扩展
class LogicBaseDie:
    """HBM4 Logic Base Die 核心模型
    
    包含:
    - DFI 5.0 接口
    - 命令缓冲区
    - 地址解码
    - Bank状态追踪
    """
    
    def __init__(self, num_channels=32, speed_grade="8Gbps"):
        self.num_channels = num_channels
        self.dfi = DFI5Interface()
        self.bank_states = [BankStateMachine() for _ in range(num_channels * 16)]
        self.command_buffer = CommandBuffer(depth=64)
        
    def process_command(self, cmd: DFICommand) -> DFIResponse:
        """处理DFI命令"""
        pass
        
    def tick(self):
        """推进一个时钟周期"""
        self.dfi.tick()
        self.command_buffer.tick()
```

**Step 2: 运行测试验证**

```bash
pytest tests/hbm4/test_logic_base_die.py -v
```

---

### Task 1.2: 完善 HBM4 Channel Model

**Files:**
- Modify: `model/dram/hbm4_channel_model.py`
- Test: `tests/hbm4/test_hbm4_channel.py`

**Step 1: 增强Channel模型**

```python
class HBM4ChannelModel:
    """HBM4 通道模型
    
    支持:
    - 64 pseudo-channels (32 channels × 2)
    - Bank group组织
    - 精确时序
    """
    
    def __init__(self, channel_id, spec: HBM4Spec):
        self.channel_id = channel_id
        self.spec = spec
        self.pseudo_channels = [
            PseudoChannel(i) for i in range(spec.pseudo_channels_per_channel)
        ]
        self.bank_groups = [
            BankGroup(g) for g in range(spec.bank_groups_per_channel)
        ]
```

---

### Task 1.3: 完善 DFI 5.0 接口

**Files:**
- Modify: `model/dram/dfi_interface.py`
- Test: `tests/hbm4/test_dfi_interface.py`

**Step 1: 实现DFI 5.0完整功能**

```python
class DFI5Interface:
    """DFI 5.0/5.1 完整实现
    
    DFI 5.0关键特性:
    - 频率变更协议
    - 低功耗状态管理
    - PHY训练接口
    - 错误报告
    """
    
    # DFI 5.0 新增信号
    FREQ_CHANGE_PROTOCOL = True
    PHY_INDEPENDENT_MODE = True
    
    def handle_freq_change(self, freq_req: FrequencyChangeRequest):
        """处理频率变更请求"""
        pass
        
    def enter_low_power(self, lp_state: DFILowPowerState):
        """进入低功耗状态"""
        pass
```

---

## Phase 2: 控制器集成

### Task 2.1: 集成 HBM4 Controller

**Files:**
- Modify: `model/controller/hbm4_controller.py`
- Test: `tests/controller/test_hbm4_controller.py`

**Step 1: 实现完整控制器**

```python
class HBM4Controller:
    """HBM4 控制器模型
    
    功能:
    - 命令生成和调度
    - 地址解码
    - QoS调度
    - 刷新调度
    - DFI接口
    """
    
    def __init__(self, config: HBM4ControllerConfig):
        self.address_decoder = HBM4AddressDecoder(config)
        self.qos_scheduler = HBM4QoSScheduler(config.qos_config)
        self.refresh_scheduler = HBM4RefreshScheduler(config.refresh_config)
        self.dfi = DFI5Interface()
        
    def tick(self):
        """推进控制器一个周期"""
        # 处理请求队列
        request = self.qos_scheduler.get_next_request()
        if request:
            commands = self.address_decoder.decode(request)
            for cmd in commands:
                self.dfi.submit_command(cmd)
        
        self.refresh_scheduler.tick()
        self.dfi.tick()
```

---

### Task 2.2: 完善地址解码器

**Files:**
- Modify: `model/controller/hbm4_address_decoder.py`
- Test: `tests/controller/test_hbm4_address_decoder.py`

**Step 1: 实现HBM4地址映射**

```python
class HBM4AddressDecoder:
    """HBM4 地址解码器
    
    地址格式: [Stack][Channel][Pch][Bg][Bank][Row][Col][Burst]
    - Stack: 2 bits (4 stacks)
    - Channel: 5 bits (32 channels)
    - Pch: 1 bit (2 pseudo-channels)
    - Bg: 3 bits (8 bank groups)
    - Bank: 4 bits (16 banks)
    - Row: 16 bits (64K rows)
    - Col: 6 bits (64 columns)
    - Burst: 2 bits (4-beat burst)
    """
    
    def decode(self, address: int) -> AddressFields:
        """解码地址为各字段"""
        pass
        
    def encode(self, fields: AddressFields) -> int:
        """编码字段为地址"""
        pass
```

---

### Task 2.3: 完善 QoS 调度器

**Files:**
- Modify: `model/controller/hbm4_qos_scheduler.py`
- Test: `tests/controller/test_hbm4_qos_scheduler.py`

---

## Phase 3: 仿真器集成

### Task 3.1: 完善统一仿真器

**Files:**
- Modify: `sim/hbm4_unified_simulator.py`
- Test: `tests/simulation/test_unified_simulator.py`

**Step 1: 增强仿真器功能**

```python
class HBM4UnifiedSimulator:
    """HBM4 统一仿真器
    
    支持:
    - 多种 traffic pattern
    - RTL 协同仿真
    - 性能统计
    - 功耗估算
    """
    
    def run_benchmark(self, pattern: TrafficPattern) -> BenchmarkResults:
        """运行性能基准测试"""
        pass
        
    def compare_with_rtl(self, rtl_trace: RTLTrace) -> ComparisonResults:
        """与RTL仿真结果对比"""
        pass
```

---

### Task 3.2: 添加性能分析

**Files:**
- Create: `model/benchmark/hbm4_bandwidth_analysis.py`
- Create: `model/benchmark/hbm4_latency_analysis.py`
- Test: `tests/benchmark/test_bandwidth.py`

---

## Phase 4: 验证基础设施

### Task 4.1: 完善UVM测试环境

**Files:**
- Modify: `verification/uvm/hbm_env_pkg.sv`
- Modify: `verification/uvm/hbm_test_pkg.sv`
- Create: `verification/uvm/tests/hbm4_base_test.sv`

---

### Task 4.2: 添加覆盖率模型

**Files:**
- Modify: `verification/uvm/hbm_coverage.sv`
- Test: `tests/verification/test_coverage.py`

---

## Phase 5: 参考模型对比

### Task 5.1: Ramulator2 对比

**Files:**
- Create: `scripts/compare_ramulator.py`
- Test: `tests/performance/test_ramulator_comparison.py`

---

## Phase 6: 文档和示例

### Task 6.1: 更新文档

**Files:**
- Modify: `docs/design/2026-06-15-hbm4-system-model-design.md`
- Create: `docs/api/hbm4_api_reference.md`

---

### Task 6.2: 添加示例

**Files:**
- Create: `examples/hbm4_basic_usage.py`
- Create: `examples/hbm4_performance_test.py`

---

## 验证命令

```bash
# Python 测试
PYTHONPATH=. pytest tests/ -x -q

# 单元测试
pytest tests/hbm4/ -v
pytest tests/controller/ -v
pytest tests/dram/ -v

# 仿真器测试
python -m sim.hbm4_unified_simulator --mode quick --channels 32

# 性能基准
python -m sim.benchmark --pattern sequential --channels 32

# UVM 编译
cd verification/uvm && make compile
```

---

## 依赖关系

```
Task 1.1 → Task 2.1 → Task 3.1 → Task 4.1
Task 1.2 ↗                    ↓
Task 1.3 ↗                 Task 5.1
                            ↓
Task 2.2 → Task 2.3        Task 6.1
                            ↓
                          Task 6.2
```

---

## 估计工作量

| Phase | Tasks | 估计时间 |
|-------|-------|----------|
| Phase 1 | 3 | 4-6 小时 |
| Phase 2 | 3 | 6-8 小时 |
| Phase 3 | 2 | 3-4 小时 |
| Phase 4 | 2 | 4-6 小时 |
| Phase 5 | 1 | 2-3 小时 |
| Phase 6 | 2 | 2-3 小时 |
| **总计** | **13** | **21-30 小时** |

---

## 执行选项

**计划完成，已保存至 `docs/plans/2026-06-16-hbm4-logic-base-die-implementation.md`**

**执行方式:**

**1. Subagent-Driven (推荐)** - 在本会话中使用多Agent并行开发，快速迭代

**2. Parallel Session** - 在新会话中使用 executing-plans，批量执行带检查点

**选择哪种方式？**