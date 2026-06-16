# HBM4 建模仿真详细实施计划

> 生成日期: 2026-06-15
> 预计总工期: 12周

---

## 一、项目概述

### 1.1 目标
为HBM4 Logic Base Die建立完整的建模仿真平台，对齐JEDEC JESD270-4标准。

### 1.2 范围
- 规格对齐与验证
- Logic Base Die功能模型
- DFI 5.0接口集成
- 验证与性能测试

---

## 二、详细任务分解

### Phase 1: 规格对齐 (2周)

| 任务ID | 描述 | 文件 | 优先级 |
|--------|------|------|--------|
| spec-1.1 | 验证32通道架构对齐 | model/controller/hbm4_address_decoder.py | High |
| spec-1.2 | 确认256-bit通道宽度实现 | model/dram/hbm4_spec.py | High |
| spec-1.3 | 更新HBM4规格常量 | model/dram/hbm4_spec.py | Medium |
| spec-1.4 | 添加JEDEC JESD270-4合规检查 | tests/hbm4/test_jedec_compliance.py | Medium |

**spec-1.1: 验证32通道架构对齐**
- 输入: JEDEC JESD270-4标准文档, 当前项目架构
- 输出: 架构对齐报告, 差异分析文档
- 步骤:
  1. 解析JEDEC JESD270-4通道架构定义
  2. 对比项目当前32通道实现
  3. 识别任何不一致之处
  4. 生成对齐报告

---

### Phase 2: Logic Base Die模型 (4周)

| 任务ID | 描述 | 文件 | 优先级 | 估计工时 |
|--------|------|------|--------|----------|
| lbd-2.1 | 实现PAM3信号模型 | model/dram/phy_signal.py | High | 2 weeks |
| lbd-2.2 | 实现PHY训练序列 | model/dram/phy_training.py | High | 1 week |
| lbd-2.3 | 实现Lane Repair逻辑 | model/dram/lane_repair.py | Medium | 1 week |
| lbd-2.4 | 实现ECC/CRC引擎 | model/dram/ecc_crc.py | Medium | 1 week |
| lbd-2.5 | 创建Logic Base Die包装器 | model/dram/logic_base_die.py | High | 1 week |

**lbd-2.1: PAM3信号模型**

```python
class PAM3SignalModel:
    """
    PAM3 (3-level Pulse Amplitude Modulation) 信号模型

    HBM4引入PAM3技术，相比NRZ:
    - 3个信号电平: -1, 0, +1
    - 每个符号编码1.58 bits
    - 支持更高数据率
    """

    LEVELS = [-1, 0, 1]

    def encode(self, data_bits):
        """将数据位编码为PAM3符号"""
        pass

    def decode(self, pam3_symbols):
        """将PAM3符号解码为数据位"""
        pass

    def compute_eye_diagram(self, sample_count=1000):
        """计算眼图用于信号完整性分析"""
        pass
```

**lbd-2.2: PHY训练序列**

```python
class PHYTrainingSequence:
    """
    PHY训练序列执行器

    HBM4训练序列包括:
    - WRLVL (Write Leveling)
    - RDLVL (Read Gate Training)
    - MRW (Mode Register Write)
    - DQ Calibration
    """

    TRAINING_SEQUENCES = ['wrlvl', 'rdlvl', 'dq_cal', 'vref_cal']

    def execute_sequence(self, sequence_name):
        """执行指定的训练序列"""
        pass

    def verify_training_result(self):
        """验证训练结果是否满足眼图要求"""
        pass
```

**lbd-2.5: Logic Base Die包装器**

```python
class LogicBaseDieModel:
    """
    Logic Base Die综合模型

    整合以下子模块:
    - PAM3SignalModel
    - PHYTrainingSequence
    - LaneRepairLogic
    - ECCCRCEngine
    """

    def __init__(self, config):
        self.channels = config['channels']  # 32
        self.channel_width = config['channel_width']  # 64
        self.pam3_enabled = config.get('pam3_enabled', True)
        self.ecc_enabled = config.get('ecc_enabled', True)

        # 子模块初始化
        self.phy_signal = PAM3SignalModel()
        self.training = PHYTrainingSequence()
        self.lane_repair = LaneRepairLogic()
        self.ecc_crc = ECCCRCEngine()

    def process_command(self, cmd):
        """处理来自控制器的命令"""
        pass

    def get_channel_state(self, channel_id):
        """获取指定通道状态"""
        pass
```

---

### Phase 3: DFI 5.0集成 (3周)

| 任务ID | 描述 | 文件 | 优先级 | 估计工时 |
|--------|------|------|--------|----------|
| dfi-3.1 | 更新DFI接口支持HBM4 | model/dram/dfi_interface.py | High | 1 week |
| dfi-3.2 | 实现独立通道时序 | model/dram/channel_timing.py | High | 2 weeks |
| dfi-3.3 | 验证通道异步操作 | tests/dram/test_channel_async.py | High | 1 week |
| dfi-3.4 | 添加DFI 5.0信号定义 | rtl/hbm_types.svh | Medium | 1 week |

**dfi-3.1: DFI 5.0 HBM4新增信号**

```systemverilog
// DFI 5.0 HBM4新增信号
typedef struct packed {
    logic [7:0]   dfi_t_phyupd_resp;    // PHY更新响应时间
    logic         dfi_self_refresh_n;    // 自刷新指示
    logic         dfi_parity_in;         // 奇偶校验输入
    logic [1:0]   dfi_pwr_good;          // 电源良好指示
    logic         dfi_mem_pwr_good;      // 内存电源良好
} dfi_hbm4_ext_signals;
```

**dfi-3.2: 独立通道时序模型**

```python
class IndependentChannelTiming:
    """
    独立通道时序模型

    JEDEC JESD270-4明确要求:
    "Each channel is completely independent of one another.
     Channels are not necessarily synchronous to each other."
    """

    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.local_clock = ClockDomain(f"ch{channel_id}_clk")
        self.bank_states = [BankState() for _ in range(16)]
        self.timing_params = TimingParameters()

    def check_timing_constraints(self, cmd):
        """检查命令时序约束"""
        pass

    def execute_with_independent_timing(self, cmd, timing_params):
        """使用通道本地时序参数执行"""
        pass
```

---

### Phase 4: 验证与优化 (3周)

| 任务ID | 描述 | 文件 | 优先级 | 估计工时 |
|--------|------|------|--------|----------|
| verify-4.1 | 创建UVM验证环境 | verification/uvm/hbm4_env_pkg.sv | High | 2 weeks |
| verify-4.2 | 添加性能基准测试 | sim/benchmark.py | Medium | 1 week |
| verify-4.3 | 对比Ramulator2参考 | research/ramulator2/ | Medium | 1 week |
| verify-4.4 | RTL仿真集成 | sim/unified_simulator.py | High | 2 weeks |

---

## 三、依赖关系

### 3.1 任务依赖图

```
Phase 1 (规格对齐)
    |
    v
Phase 2 (Logic Base Die) <-----+
    |                          |
    +-----> Phase 3 (DFI 5.0) --+
    |                          |
    v                          v
Phase 4 (验证与优化) <---------+
```

### 3.2 关键路径

| 路径 | 任务 | 预计时间 |
|------|------|----------|
| 关键路径1 | spec-1.1 -> lbd-2.1 -> dfi-3.1 -> verify-4.1 | 8 weeks |
| 关键路径2 | spec-1.2 -> lbd-2.2 -> dfi-3.2 -> verify-4.2 | 7 weeks |

---

## 四、资源需求

### 4.1 人力需求

| 角色 | 人数 | 职责 |
|------|------|------|
| 架构师 | 1 | 规格对齐、架构设计 |
| Python开发 | 2 | Python模型实现 |
| RTL开发 | 1 | RTL实现、DFI接口 |
| 验证工程师 | 1 | UVM环境、测试 |

### 4.2 工具需求

| 工具 | 用途 | 来源 |
|------|------|------|
| Python 3.9+ | 仿真框架 | 开源 |
| SystemC | 系统级建模 | 开源 |
| Verilator | RTL仿真 | 开源 |
| UVM | 功能验证 | 开源 |
| Ramulator2 | 参考模型 | 开源 |

---

## 五、里程碑

| 里程碑 | 日期 | 交付物 |
|--------|------|--------|
| M1: 规格对齐完成 | Week 2 | 对齐报告、差异文档 |
| M2: PAOpus 模型完成 | Week 4 | 信号模型代码 |
| M3: Logic Base Die完成 | Week 6 | 综合模型 |
| M4: DFI 5.0集成完成 | Week 9 | 接口集成 |
| M5: 验证完成 | Week 12 | 验证报告、性能基准 |

---

## 六、风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| JEDEC标准更新 | 中 | 高 | 保持与标准组织联系，预留设计裕量 |
| 验证工具缺失 | 高 | 中 | 准备多套工具方案 |
| 性能不达标 | 中 | 中 | 早期性能建模，及时调整架构 |

---

## 七、验收标准

### 7.1 功能验收
- [ ] 32通道独立操作验证通过
- [ ] PAM3信号编解码验证通过
- [ ] PHY训练序列执行验证通过
- [ ] DFI 5.0接口符合规范

### 7.2 性能验收
- [ ] 仿真速度 >= 100K cycles/sec
- [ ] 带宽计算与理论值偏差 < 5%
- [ ] 时序精度满足cycle-accurate要求

### 7.3 验证验收
- [ ] UVM测试覆盖率达到80%
- [ ] 与Ramulator2对比偏差 < 10%
- [ ] RTL联合仿真验证通过

---

*本计划由Claude Code生成*
*生成日期: 2026-06-15*