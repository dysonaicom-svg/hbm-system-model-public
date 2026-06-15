# HBM System Modeling Platform - Design Document
**Date**: 2026-06-15
**Version**: 1.2
**Status**: Implementation in Progress - Phases A & B Active

---

## 0. Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-06-15 | Initial draft | AI |
| 1.1 | 2026-06-15 | Self-review fixes | AI |
| | | - Fix: HBM3 staggered refresh calculation | |
| | | - Fix: Power model units (mW not mW/MHz) | |
| | | - Fix: QoS bandwidth guarantee specification | |
| | | - Fix: Latency parameter units clarified | |
| | | - Fix: Bank group count (4-bit→3-bit, 16→8 groups) | |
| | | - Add: HBM4 specifications | |
| | | - Add: Detailed QoS scheduler implementation | |
| | | - Add: Bank state machine code | |
| 1.2 | 2026-06-15 | Implementation status update | AI |
| | | - Phase A: Controller model complete (HBM4 32-ch) | |
| | | - Phase B: DRAM model complete (PHY/MBIST) | |
| | | - RTL: HBM Controller complete | |
| | | - UVM: Environment complete | |
| | | - Tests: 730+ test cases | |

---

## 1. Project Overview

### 1.1 Objective
Build a comprehensive HBM system simulation platform that serves both **design exploration** and **post-silicon verification** phases.

### 1.2 Core Capabilities
| Phase | Primary Use | Key Requirements |
|-------|-------------|------------------|
| **Design Phase** | Architecture exploration, parameter tuning, bottleneck identification | Fast, configurable, flexible |
| **Verification Phase** | RTL alignment, bug reproduction, timing validation | Bit-accurate, UVM compatible |

### 1.3 Design Principles
- **Layered Architecture**: Modular design with clear interfaces
- **Progressive Accuracy**: Transaction-level → Timing-accurate → Bit-accurate
- **Dual Mode Support**: Design exploration + Verification alignment
- **Extensible**: Easy to add new features, protocols, workloads
- **Multi-Stack Support**: Scalable 1-8 HBM stacks configuration
- **Built-in Traffic Generation**: No external traces required

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Traffic Generator / Trace Reader             │
│                   (AXI4/Custom Interface Support)                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      NoC / Interconnect Model                       │
│                    (AXI Crossbar / Mesh)                            │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        HBM Controller                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Address    │  │     QoS      │  │    Read/     │              │
│  │   Decoder    │  │    Arbiter   │  │   Write      │              │
│  └──────────────┘  └──────────────┘  │   Queues     │              │
│                                       └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Scheduler   │  │   Refresh    │  │   DFI        │              │
│  │ FR-FCFS/QoS  │  │  Scheduler   │  │   PHY I/F    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      HBM DRAM Model                                 │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                    Per-Stack Model                        │      │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │      │
│  │  │  Channel 0 │  │  Channel 1 │  │  Channel 7 │         │      │
│  │  │  (Pseudo   │  │  (Pseudo   │  │  (Pseudo   │         │      │
│  │  │  Ch x2)    │  │  Ch x2)    │  │  Ch x2)    │         │      │
│  │  └────────────┘  └────────────┘  └────────────┘         │      │
│  └──────────────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                    Bank State Machine                     │      │
│  │  ACT / PRE / RD / WR / REF / tRCD / tRP / tRAS / tRC    │      │
│  └──────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Statistics Collector                           │
│  Bandwidth / Latency / Utilization / Conflict / Power               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Project Structure

```
/home/ic/JXTF/HBM/
├── model/                          # SystemC/Python 模型
│   ├── controller/                 # HBM Controller 模型
│   │   ├── address_decoder.py
│   │   ├── scheduler.py
│   │   ├── qos_arbiter.py
│   │   ├── refresh_scheduler.py
│   │   └── controller.py
│   ├── dram/                       # DRAM Timing 模型
│   │   ├── hbm3_spec.py
│   │   ├── bank_state_machine.py
│   │   ├── channel_model.py
│   │   └── stack_model.py
│   ├── phy/                        # PHY 模型 (后续 Phase C)
│   │   └── phy_model.py
│   └── interconnect/               # NoC 模型
│       └── noc_model.py
├── verification/                   # 验证环境
│   ├── uvm/                        # UVM 测试环境
│   │   ├── env/
│   │   ├── tests/
│   │   ├── agents/
│   │   └── scoreboard/
│   └── reference_model/            # Python Reference Model
│       └── hbm_ref_model.py
├── scripts/                        # 辅助脚本
│   ├── traffic_generator.py
│   ├── trace_converter.py
│   ├── visualize.py
│   └── parameter_sweep.py
├── docs/
│   ├── design/                     # 设计文档
│   │   └── YYYY-MM-DD-hbm-system-model-design.md
│   ├── specs/                      # 规格文档
│   │   └── hbm3_spec.md
│   └── reports/                    # 分析报告
├── research/
│   ├── ramulator2/                 # 参考代码
│   └── papers/                     # 相关论文
└── sim/                            # 仿真目录
    ├── build/
    └── results/
```

---

## 4. Phase Implementation Plan

### Phase A: HBM Controller Model - COMPLETE
**Goal**: Functional + Transaction-level HBM Controller

| Component | Deliverable | Status |
|-----------|-------------|--------|
| Address Decoder | HBM3/HBM4 address mapping | Complete |
| Read/Write Queue | Request queuing | Complete |
| Scheduler | FR-FCFS + QoS modes | Complete |
| Refresh Scheduler | tREFI, tRFC handling | Complete |
| HBM4 Support | 32-channel, speed grades | Complete |

**Deliverables**:
- `model/controller/controller.py` - Main controller
- `model/controller/address_decoder.py` - Address mapping
- `model/controller/hbm4_address_decoder.py` - HBM4 32-ch support
- `model/controller/scheduler.py` - FR-FCFS scheduler
- `model/controller/hbm4_controller.py` - HBM4 enhanced controller
- `model/controller/hbm4_qos_scheduler.py` - QoS with bandwidth guarantees
- `model/controller/hbm4_refresh_scheduler.py` - Refresh scheduling
- `rtl/hbm_controller.sv` - RTL implementation

### Phase B: DRAM Timing Model - COMPLETE
**Goal**: Cycle-accurate DRAM behavior model

| Component | Deliverable | Status |
|-----------|-------------|--------|
| HBM3/HBM4 Spec | Timing parameters | Complete |
| Bank State Machine | ACT/PRE/RD/WR timing | Complete |
| Channel Model | Multi-channel support | Complete |
| PHY Training | Training sequences | Complete |
| MBIST | Memory BIST | Complete |
| Power Estimator | Power consumption | Complete |
| ECC/CRC | Error detection | Complete |
| Lane Repair | Redundancy | Complete |
| DFI Interface | Controller-PHY interface | Complete |

**Deliverables**:
- `model/dram/bank_state_machine.py` - Bank timing
- `model/dram/hbm4_channel_model.py` - Channel model with HBM4
- `model/dram/hbm4_spec.py` - HBM4 specifications
- `model/dram/phy_training.py` - PHY training
- `model/dram/mbist_controller.py` - MBIST
- `model/dram/power_estimator.py` - Power model
- `model/dram/ecc_crc.py` - ECC/CRC
- `model/dram/lane_repair.py` - Lane repair
- `model/dram/dfi_interface.py` - DFI interface
- `model/dram/timing.py` - Timing parameters

### Phase C: PHY Integration - FUTURE
**Goal**: Analog + Digital co-simulation

| Task | Description | Status |
|------|-------------|--------|
| DFI interface | Connect controller to PHY model | Complete (DFI) |
| TX/RX behavior | Pre-emphasis, CTLE, DFE | Future |
| Signal integrity | Optional IBIS integration | Future |

---

## 5. Key Components Detail

### 5.1 HBM Controller

#### 5.1.1 Address Decoder
```python
class AddressDecoder:
    def __init__(self, config):
        self.stack_bits = config.stack_bits      # e.g., 2
        self.channel_bits = config.channel_bits  # e.g., 3
        self.pseudo_channel_bits = 1            # 2 pseudo channels
        self.bank_bits = config.bank_bits        # e.g., 4
        self.row_bits = config.row_bits
        self.col_bits = config.col_bits
    
    def decode(self, addr):
        # Return: (stack, channel, pseudo_channel, bank, row, col)
        pass
    
    def set_mapping(self, mapping_matrix):
        # Support configurable address mapping
        pass
```

#### 5.1.2 Scheduler
```python
class HBMScheduler:
    def __init__(self, mode="fr-fcfs"):
        self.mode = mode  # "fr-fcfs" or "qos"
    
    def schedule(self, read_queue, write_queue, bank_states):
        if self.mode == "fr-fcfs":
            return self.fr_fcfs_schedule(read_queue, write_queue, bank_states)
        elif self.mode == "qos":
            return self.qos_schedule(read_queue, write_queue, bank_states)
```

#### 5.1.3 Scheduler Detail

**FR-FCFS (First-Ready FCFS)**:
```
Priority: Row-hit > Oldest request > Read vs Write arbitration
流程:
1. 扫描读队列，找所有 row-hit 的请求
2. 如果有 row-hit，按时间戳排序，选择最老的
3. 如果无 row-hit，找最早到达的请求（不限 bank）
4. 读/写仲裁：可配置读写优先级比例
```

**QoS Scheduler**:
```
Priority Levels: 0-15 (高优先级数值越大)
调度规则:
1. 先按 QoS 优先级排序
2. 同优先级内按 FR-FCFS 规则调度
3. 可配置带宽保证阈值（每个 QoS 等级的最小带宽）
```

**QoS 带宽保证详细设计**：

```python
class QoSScheduler:
    """带带宽保证的 QoS 调度器
    
    设计目标:
    - 高优先级请求获得更多带宽
    - 低优先级请求不会被完全饿死
    - 带宽保证可配置
    """
    
    # QoS 优先级定义 (0=最低, 15=最高)
    QOS_CRITICAL = 15   # 实时/关键任务
    QOS_HIGH = 12       # 高优先级
    QOS_NORMAL = 8      # 普通
    QOS_LOW = 4         # 后台/批处理
    QOS_IDLE = 0        # 空闲/试探
    
    def __init__(self, config):
        # 带宽保证配置 (GB/s per stack)
        self.bandwidth_guarantee = {
            self.QOS_CRITICAL: config.get('bw_guarantee_critical', 200.0),
            self.QOS_HIGH: config.get('bw_guarantee_high', 300.0),
            self.QOS_NORMAL: config.get('bw_guarantee_normal', 200.0),
            self.QOS_LOW: config.get('bw_guarantee_low', 100.0),
        }
        # 带宽上限 (可选，防止低优先级饿死)
        self.bandwidth_cap = {
            self.QOS_CRITICAL: 1000.0,  # 无上限
            self.QOS_HIGH: 800.0,
            self.QOS_NORMAL: 400.0,
            self.QOS_LOW: 200.0,
            self.QOS_IDLE: 50.0,
        }
        # 带宽追踪窗口 (ms)
        self.bw_window = config.get('bw_window_ms', 1.0)
        self.bw_tracked = defaultdict(list)  # {qos: [(timestamp, bytes), ...]}
    
    def _get_current_bandwidth(self, qos_level: int) -> float:
        """计算当前 QoS 等级的带宽使用"""
        now = time.time()
        window_start = now - self.bw_window / 1000.0
        
        # 过滤时间窗口内的数据
        recent = [(t, b) for t, b in self.bw_tracked[qos_level] if t >= window_start]
        total_bytes = sum(b for _, b in recent)
        total_time = self.bw_window / 1000.0
        
        return total_bytes / total_time / 1e9  # GB/s
    
    def _can_schedule(self, qos_level: int) -> bool:
        """检查是否可以调度该 QoS 等级"""
        current_bw = self._get_current_bandwidth(qos_level)
        
        # 检查是否低于保证带宽（可以调度）
        if current_bw < self.bandwidth_guarantee.get(qos_level, 0):
            return True
        
        # 检查是否超过上限（不能调度）
        if current_bw >= self.bandwidth_cap.get(qos_level, float('inf')):
            return False
        
        return True  # 在保证和上限之间，竞态调度
    
    def schedule(self, read_queue, write_queue, current_cycle) -> Optional[Request]:
        """带带宽保证的调度"""
        # 1. 从高到低检查各 QoS 等级
        for qos_level in range(15, -1, -1):
            if self._can_schedule(qos_level):
                # 2. 在该 QoS 等级的请求中找 FR-FCFS 最优请求
                candidates = [
                    req for req in read_queue + write_queue
                    if req.qos == qos_level
                ]
                if candidates:
                    best = self._fr_fcfs_select(candidates, current_cycle)
                    return best
        
        # 3. 如果所有 QoS 都受限，降级到 FR-FCFS
        all_requests = read_queue + write_queue
        if all_requests:
            return self._fr_fcfs_select(all_requests, current_cycle)
        
        return None
    
    def _fr_fcfs_select(self, candidates, current_cycle) -> Request:
        """FR-FCFS 选择最优请求"""
        # 优先选择 row-hit
        row_hit = [r for r in candidates if r.is_row_hit]
        if row_hit:
            # 按时间戳排序，选择最老的
            return min(row_hit, key=lambda r: r.arrival_time)
        
        # 否则按时间戳排序，选择最老的
        return min(candidates, key=lambda r: r.arrival_time)
```

**QoS 配置示例**：

| QoS 等级 | 用途 | 带宽保证 | 带宽上限 |
|----------|------|----------|----------|
| 15 (Critical) | 实时控制 | 200 GB/s | 无限制 |
| 12 (High) | AI 推理 | 300 GB/s | 800 GB/s |
| 8 (Normal) | 通用计算 | 200 GB/s | 400 GB/s |
| 4 (Low) | 批处理 | 100 GB/s | 200 GB/s |
| 0 (Idle) | 后台任务 | 0 | 50 GB/s |

**Write Drain 策略**:
| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `write_drain_immediate` | 写请求立即执行 | 低延迟要求 |
| `write_drain_threshold` | 写队列满时 drain | 平衡延迟 |
| `write_drain_interval` | 周期性 drain | 高吞吐量 |

**Read-Write Turnaround**:
```python
TURNAROUND_PENALTY = {
    "RD_TO_WR": 3,   # cycles
    "WR_TO_RD": 3,   # cycles
    "RD_TO_RD": 0,   # 无 penalty
    "WR_TO_WR": 0,
}
```

#### 5.1.4 Address Mapping Schemes

HBM 地址映射是关键性能因素：

| 映射方式 | 位字段顺序 | 特点 |
|----------|------------|------|
| **RBC** (Row-Bank-Channel) | Row[Bank[Channel]] | 适合顺序访问 |
| **BCR** (Bank-Channel-Row) | Bank[Channel[Row]] | 最大化并行度 |
| **CRB** (Channel-Row-Bank) | Channel[Row[Bank]] | 跨 channel 随机 |
| **Custom** | 可配置矩阵 | 研究专用 |

**默认 HBM 映射 (JEDEC)**:
```
HBM3 地址位字段 (64-bit 地址):
Addr[63:48] = Reserved
Addr[47:46] = Stack ID (2-bit, 支持 4 stack)
Addr[45:43] = Channel (3-bit, 8 channels)
Addr[42]    = Pseudo-channel (1-bit, 2 pseudo-ch)
Addr[41:39] = Bank group (3-bit, 8 bank groups per pseudo-ch)
Addr[38:34] = Bank within group (5-bit, 2 banks per group)
            # 共 8 × 2 = 16 banks
Addr[33:16] = Row (18-bit)
Addr[15:3]  = Column (13-bit)
Addr[2:0]   = Byte offset (8-byte 粒度)

地址空间计算:
- 4 stack × 8 channels × 2 pseudo-ch × 16 banks × 256K rows × 2KB row = 256GB/stack
- 16 banks = 8 bank groups × 2 banks/group
```

**Bank Group 架构说明**：

| HBM 版本 | Bank Groups | Banks per Group | Total Banks |
|----------|-------------|-----------------|-------------|
| HBM2 | 0 | N/A | 8-16 |
| HBM3 | 8 | 2 | 16 |
| HBM4 | TBD | TBD | 32+ (预计) |

Bank group 的引入是为了减少同时激活的 bank 数量，降低功耗峰值。

#### 5.1.5 Bandwidth Calculation

理论带宽计算：
```python
def calc_bandwidth(data_rate, io_width, channels, pseudo_channels):
    """计算理论峰值带宽"""
    # 单 pseudo-channel 带宽
    bw_per_ps = data_rate * (io_width // 2) / 8  # GB/s
    
    # 总带宽 = per_ps × pseudo_channels × channels × stacks
    total_bw = bw_per_ps * pseudo_channels * channels
    return total_bw

# HBM3 示例
HBM3_BW = calc_bandwidth(
    data_rate=6.4e9,      # 6.4 Gb/s/pin
    io_width=1024,        # 1024-bit
    channels=8,           # 8 channels
    pseudo_channels=2     # 2 pseudo-ch per channel
)
# = 6.4e9 * 512 / 8 * 2 * 8 = 819.2 GB/s/stack
```

#### 5.1.6 Configurable Parameters

**延迟参数说明**：

HBM3 延迟参数需要区分单位：

| 参数类型 | 单位 | HBM3 典型值 | 说明 |
|----------|------|-------------|------|
| **时序参数** | cycles @ tCK | 见 5.2.4 节 | 周期性参数 |
| **基础延迟** | cycles | 30-40 | 控制器内部延迟 |
| **PHY 延迟** | ns | 20-30 | 控制器到 PHY |
| **总读取延迟** | ns | 40-50 | 地址到数据返回 |

```python
# 延迟参数配置（cycles）
read_latency_base = 30      # 控制器内部延迟
write_latency_base = 10    # 写延迟通常较小

# 精确延迟计算
def calc_read_latency(config, bank_state, row_hit):
    """计算总读取延迟"""
    base = config.read_latency_base  # 控制器延迟
    timing = config.tRCD             # tRCD = 17 cycles
    phy_delay = config.phy_latency   # PHY 延迟
    
    if row_hit:
        return base + phy_delay  # Row hit: 无需 tRCD
    else:
        return base + timing + phy_delay  # Row miss: 需要 tRCD

def calc_write_latency(config, bank_state, row_hit):
    """计算总写入延迟"""
    base = config.write_latency_base
    timing = config.tRCD
    phy_delay = config.phy_latency
    
    if row_hit:
        return base + phy_delay
    else:
        return base + timing + phy_delay
```

**可配置参数列表**：

| Parameter | Default | Range | Unit | Description |
|-----------|---------|-------|------|-------------|
| `stack_count` | 2 | 1-8 | - | Number of HBM stacks |
| `channels_per_stack` | 8 | 4-16 | - | Channels per stack |
| `pseudo_channels_per_channel` | 2 | 1-4 | - | Pseudo channels per channel |
| `banks_per_pseudo_channel` | 16 | 8-32 | - | Banks per pseudo channel |
| `bank_groups_per_channel` | 8 | 4-16 | - | Bank groups per channel |
| `row_size` | 2048 | - | bytes | Row size |
| `burst_length` | 32 | - | - | FLINE burst length |
| `data_rate` | 6.4e9 | - | bits/s | Per-pin data rate |
| `io_width` | 1024 | - | bits | Interface width |
| `read_latency_base` | 30 | 20-50 | cycles | Controller read delay |
| `write_latency_base` | 10 | 5-20 | cycles | Controller write delay |
| `phy_latency` | 20 | 15-30 | cycles | PHY delay |
| `queue_depth` | 32 | 16-128 | - | Max request queue depth |
| `max_outstanding` | 16 | 8-64 | - | Max outstanding requests |
| `address_mapping` | "rbc" | - | - | Address mapping scheme |
| `refresh_interval` | 3.9e-6 | - | s | tREFI interval |
| `refresh_penalty` | 230e-9 | - | s | tRFC duration |
| `scheduler_mode` | "fr-fcfs" | - | - | "fr-fcfs" or "qos" |
| `write_drain_policy` | "threshold" | - | - | Write drain strategy |

### 5.4 Multi-Stack Interconnect
```python
class MultiStackInterconnect:
    """Support 1-8 HBM stacks with configurable topology"""
    
    # Supported topologies
    TOPOLOGY_MESH = "mesh"           # Grid topology
    TOPOLOGY_CROSSBAR = "full_crossbar"  # Full crossbar
    TOPOLOGY_Bfly = "butterfly"      # Butterfly network
    
    def __init__(self, stack_count, topology="mesh"):
        self.stack_count = stack_count  # 1-8
        self.topology = topology
```

### 5.5 Traffic Generator
```python
class TrafficGenerator:
    """Built-in traffic generation - no external traces required"""
    
    # Supported patterns
    PATTERN_SEQUENTIAL = "sequential"    # Sequential access
    PATTERN_RANDOM = "random"             # Random address pattern
    PATTERN_STRIDE = "stride"            # Strided access
    PATTERN_STREAMING = "streaming"       # Streaming/burst access
    PATTERN_BANK_CONFLICT = "bank_conflict"  # Bank conflict test
    PATTERN_TRACE = "trace"               # External trace reader
    
    def generate(self, pattern, config):
        """Generate traffic requests based on pattern"""
        pass

class TraceReader:
    """Interface for importing external traces"""
    
    # Supported formats
    FORMAT_PYMTL = "pymtl"    # PyMTL format
    FORMAT_SQL = "sqlite"     # SQLite database
    FORMAT_CSV = "csv"       # CSV format
    FORMAT_VCD = "vcd"       # VCD to request converter
    
    def load(self, trace_file, format="csv"):
        """Load trace from external source"""
        pass
```

### 5.2 DRAM Model

#### 5.2.1 Bank State Machine
```
States: IDLE, ACTIVE, READING, WRITING, REFRESHING

Transitions:
- IDLE + ACT -> ACTIVE
- ACTIVE + RD -> READING
- ACTIVE + WR -> WRITING
- ACTIVE + PRE -> IDLE
- IDLE + REF -> REFRESHING -> IDLE
```

#### 5.2.2 Bank State Machine Implementation
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class BankState(Enum):
    IDLE = 0
    ACTIVE = 1
    READING = 2
    WRITING = 3
    REFRESHING = 4

@dataclass
class Bank:
    bank_id: int
    state: BankState
    open_row: Optional[int] = None  # -1 means closed
    activate_time: int = 0          # cycle when last ACT
    read_time: int = 0             # cycle when last RD
    write_time: int = 0            # cycle when last WR

class BankStateMachine:
    def __init__(self, timing_params):
        self.tCK = timing_params['tCK']
        self.tRCD = timing_params['tRCD']   # cycles
        self.tRP = timing_params['tRP']
        self.tRAS = timing_params['tRAS']
        self.tRC = timing_params['tRC']
        self.tCCD = timing_params['tCCD']
        self.tRRD = timing_params['tRRD']
        self.tFAW = timing_params['tFAW']
    
    def can_activate(self, bank: Bank, current_cycle: int) -> bool:
        """检查是否可以激活 bank"""
        if bank.state != BankState.IDLE:
            return False
        # 检查 tRC: 必须距离上次激活足够长时间
        return current_cycle >= bank.activate_time + self.tRC
    
    def can_read(self, bank: Bank, current_cycle: int) -> bool:
        """检查是否可以发起读"""
        if bank.state != BankState.ACTIVE:
            return False
        return current_cycle >= bank.activate_time + self.tRCD
    
    def can_write(self, bank: Bank, current_cycle: int) -> bool:
        """检查是否可以发起写"""
        if bank.state != BankState.ACTIVE:
            return False
        return current_cycle >= bank.activate_time + self.tRCD
    
    def is_row_hit(self, bank: Bank, row: int) -> bool:
        """检查是否是 row hit"""
        return bank.state == BankState.ACTIVE and bank.open_row == row
    
    def is_row_open(self, bank: Bank) -> bool:
        """检查 row 是否打开"""
        return bank.state == BankState.ACTIVE and bank.open_row >= 0
```

#### 5.2.3 Refresh Handling

HBM 刷新是关键特性，影响带宽：

```python
class RefreshScheduler:
    """Refresh 调度策略"""
    
    REFRESH_ALL_BANKS = "all"      # 一次刷新所有 bank
    REFRESH_PER_BANK = "per_bank"  # 逐 bank 刷新
    REFRESH_BANK_GROUP = "bank_group"  # 按 bank group 刷新
    
    def __init__(self, config):
        self.mode = config.get('refresh_mode', self.REFRESH_ALL_BANKS)
        self.tREFI = config['tREFI']    # Refresh interval (cycles)
        self.tRFC = config['tRFC']       # Refresh command duration
        self.refresh_counter = 0
    
    def schedule_refresh(self, current_cycle: int, banks: List[Bank]) -> List[Bank]:
        """计算下一次 refresh 应该在哪些 bank 上执行"""
        if current_cycle - self.last_refresh >= self.tREFI:
            return self._execute_refresh(banks)
        return []
    
    def _execute_refresh(self, banks: List[Bank]) -> List[Bank]:
        """执行 refresh"""
        # 关闭所有打开的 row，然后刷新
        for bank in banks:
            bank.state = BankState.REFRESHING
        return banks
```

**Refresh 开销计算**：
```python
def calc_refresh_overhead_hbm3(tREFI, tRFC, num_bank_groups):
    """
    HBM3 staggered refresh 开销计算
    - 每个 REFI 间隔刷新 8 个 bank group
    - tRFCbg = tRFC / 8 (staggered, 每个 group 独立刷新)
    tREFI = 5000 cycles (HBM3 @ 1.28GHz)
    tRFC = 295 cycles (16Gb HBM3)
    num_bank_groups = 128 (8 ch × 2 ps × 8 bank groups)
    """
    # 每个 bank group 每 tREFI 刷新一次
    # 8 个 bank group 交错执行，每次刷新 1 个 group
    refresh_per_group_interval = tREFI  # 每个 group 的刷新间隔
    total_bank_group_refresh_cycles = num_bank_groups * tRFC
    
    # 实际开销 = 所有 group 刷新总周期 / (所有 bank × tREFI)
    # 注意：这是理论最大开销，实际会小一些因为交错刷新
    overhead = (num_bank_groups * tRFC) / (num_bank_groups * tREFI)
    # = tRFC / tREFI = 295 / 5000 = 5.9%
    
    return overhead

def calc_refresh_overhead_hbm2(tREFI, tRFC, num_banks):
    """
    HBM2 刷新开销计算（逐 bank 刷新）
    - 每个 REFI 间隔需要刷新所有 bank
    tREFI = 7.8 us = 7800 cycles
    tRFC = 65 ns = 65 cycles (4Gb)
    """
    # 实际开销 = 所有 bank 刷新总周期 / 时间
    overhead = (num_banks * tRFC) / (num_banks * tREFI)
    # = tRFC / tREFI = 65 / 7800 = 0.83%
    return overhead
```

#### 5.2.4 Timing Parameters (HBM3 & HBM4)

| Parameter | HBM3 | HBM4 (计划) | Description |
|-----------|------|-------------|-------------|
| tCK | 781 ps | 625 ps | Clock period |
| tRCD | 17 | 待定 | RCD delay (cycles) |
| tRP | 17 | 待定 | RP delay (cycles) |
| tRAS | 42 | 待定 | RAS delay (cycles) |
| tRC | 59 | 待定 | RC delay (cycles) |
| tCCD | 5 | 待定 | CCD delay (cycles) |
| tRRD | 5 | 待定 | RRD delay (cycles) |
| tFAW | 26 | 待定 | FAW delay (cycles) |
| tRFC | 295 (16Gb) | 待定 | RFC delay (cycles) |
| tREFI | 5000 | 待定 | REFI interval (cycles) |
| Data Rate | 6.4 Gb/s/pin | 8.0+ Gb/s/pin | Per-pin rate |
| Interface Width | 1024-bit | 2048-bit | Aggregate I/O |
| Peak BW | 819.2 GB/s | 2048 GB/s | Per stack |
| Max Stack | 16-Hi | 待定 | Die stack height |
| Bank Groups | 8 | 待定 | Per pseudo channel |

**HBM4 关键变化**：
- 接口宽度翻倍 (1024 → 2048-bit)
- 数据速率提升 (6.4 → 8.0+ Gb/s/pin)
- 聚合带宽约 2 TB/s/stack
- 可能采用 4:1 串行化降低引脚数

#### 5.2.5 Power Model

功耗估算模型（基于 HBM3 JEDEC JESD238）：

```python
class PowerModel:
    """HBM 功耗模型
    
    注意：功耗单位应为 mW 或 W，而非 mW/MHz
    HBM3 单通道峰值功耗约 100-200mW
    """
    
    # HBM3 单通道功耗参数 (mW)
    # 这些值基于 JEDEC JESD238 和实际芯片数据
    POWER_ACTIVATE = 120.0    # Active 功耗 (mW/channel)
    POWER_READ = 80.0         # Read 功耗 (mW/channel)
    POWER_WRITE = 95.0        # Write 功耗 (mW/channel)
    POWER_REFRESH = 150.0     # Refresh 功耗 (mW/channel, 全 bank)
    POWER_IDLE = 25.0         # Idle 功耗 (mW/channel)
    POWER_STANDBY = 5.0       # Standby 功耗 (mW/channel)
    
    # 单位时间功耗系数 (mW/GB/s)
    POWER_COEFF_IDD = 0.15    # 带宽归一化功耗系数
    
    def __init__(self, config):
        self.channels = config['channels_per_stack']
        self.stacks = config['stack_count']
        self.data_rate = config['data_rate']  # Gb/s/pin
        self.io_width = config['io_width']    # bits
    
    def calc_bandwidth(self):
        """计算理论带宽 (GB/s)"""
        # 单 pseudo-channel 带宽
        bw_per_ps = self.data_rate * (self.io_width // 2) / 8  # GB/s
        return bw_per_ps * self.channels * 2 * self.stacks  # 2 pseudo-ch/ch
    
    def calc_power(self, stats: StatsCollector) -> dict:
        """基于统计数据计算平均功耗"""
        power_breakdown = {}
        
        # 时间归一化 (假设 1ms 统计窗口)
        time_ms = stats.simulation_time * 1e3  # convert to ms
        
        # 各操作平均功耗
        power_breakdown['activate'] = (
            stats.activate_count * self.POWER_ACTIVATE /
            (time_ms * self.channels * self.stacks)
        )
        power_breakdown['read'] = (
            stats.read_count * self.POWER_READ /
            (time_ms * self.channels * self.stacks)
        )
        power_breakdown['write'] = (
            stats.write_count * self.POWER_WRITE /
            (time_ms * self.channels * self.stacks)
        )
        power_breakdown['refresh'] = (
            stats.refresh_count * self.POWER_REFRESH /
            (time_ms * self.channels * self.stacks)
        )
        power_breakdown['idle'] = (
            stats.idle_cycles * self.POWER_IDLE /
            (time_ms * self.channels * self.stacks)
        )
        
        total_power = sum(power_breakdown.values())
        power_breakdown['total_mW'] = total_power
        power_breakdown['total_W'] = total_power / 1000
        
        # 能量效率
        total_bits = stats.total_bytes * 8
        if total_bits > 0:
            power_breakdown['energy_per_bit_pJ'] = (
                total_power * 1e6 / total_bits
            )  # pJ/bit
        
        return power_breakdown
```

**功耗参考值（HBM3）**：

| 功耗项 | 典型值 | 说明 |
|--------|--------|------|
| Active (1 bank) | 120 mW/ch | 行激活 |
| Read | 80 mW/ch | 读操作 |
| Write | 95 mW/ch | 写操作 |
| Refresh | 150 mW/ch | 全 bank 刷新 |
| Idle | 25 mW/ch | 静态功耗 |
| Per-stack peak | ~1 W | 全速读写 |

**功耗估算公式**：
```python
# 经验公式：功耗 ≈ a + b × Bandwidth
P_total = P_static + P_coeff × BW_effective

# 其中：
# P_static ≈ 100 mW/stack (idle + refresh baseline)
# P_coeff ≈ 0.1 mW/(GB/s) per channel
```

### 5.3 Interface Definition

#### 5.3.1 AXI4 Interface
```python
# AXI4 Request
class AXIRequest:
    addr: int           # 64-bit address
    size: int           # Transaction size
    len: int            # Burst length (1-256)
    burst: int          # FIXED/INCR/WRAP
    qos: int            # QoS priority (0-15)
    read_write: str     # "READ" or "WRITE"
    data: bytes         # Write data
    
# AXI4 Response
class AXIResponse:
    request_id: int
    status: str         # "OK", "SLVERR", "DECERR"
    latency: float      # Response latency
    data: bytes         # Read data (for read requests)
```

#### 5.3.2 Custom Interface
```python
class HBMRequest:
    addr: int
    length: int         # In bytes
    priority: int       # 0-7
    is_read: bool
    user: dict          # Custom metadata
```

---

## 6. Output Metrics

### 6.1 Basic Metrics (Always Enabled)
| Metric | Unit | Description |
|--------|------|-------------|
| `bandwidth_effective` | GB/s | Achieved bandwidth |
| `latency_avg` | ns | Average latency |
| `latency_p50` | ns | Median latency |
| `latency_p95` | ns | 95th percentile latency |
| `latency_p99` | ns | 99th percentile latency |

### 6.2 Extended Metrics (Configurable)
| Metric | Unit | Description |
|--------|------|-------------|
| `channel_utilization` | % | Per-channel bandwidth utilization |
| `bank_conflict_rate` | % | Bank activation conflicts |
| `row_hit_rate` | % | Row buffer hits |
| `queue_occupancy_max` | - | Maximum queue fill level |
| `read_write_turnaround_loss` | % | Turnaround overhead |
| `refresh_overhead` | % | Refresh-induced bandwidth loss |

### 6.3 Power Metrics
| Metric | Unit | Description |
|--------|------|-------------|
| `power_read` | W | Read power |
| `power_write` | W | Write power |
| `power_activate` | W | Activation power |
| `power_refresh` | W | Refresh power |
| `energy_per_bit` | pJ/bit | Energy efficiency |

### 6.4 Test Matrix

测试覆盖矩阵：

| 测试类别 | 测试用例 | 验证点 | 优先级 |
|----------|----------|--------|--------|
| **功能测试** | | | | |
| | `test_basic_read` | 读单个地址 | P0 |
| | `test_basic_write` | 写单个地址 | P0 |
| | `test_burst_read` | 突发读 | P0 |
| | `test_burst_write` | 突发写 | P0 |
| **地址映射测试** | | | | |
| | `test_addr_decode_rbc` | Row-Bank-Channel 映射 | P1 |
| | `test_addr_decode_bcr` | Bank-Channel-Row 映射 | P1 |
| | `test_addr_decode_custom` | 自定义映射 | P2 |
| **时序测试** | | | | |
| | `test_timing_act` | ACT 延迟 | P1 |
| | `test_timing_rd` | READ 延迟 | P1 |
| | `test_timing_wr` | WRITE 延迟 | P1 |
| | `test_timing_refresh` | Refresh 开销 | P1 |
| **调度测试** | | | | |
| | `test_scheduler_frfcfs` | FR-FCFS 调度 | P1 |
| | `test_scheduler_qos` | QoS 调度 | P1 |
| | `test_write_drain` | Write drain 策略 | P2 |
| **并发测试** | | | | |
| | `test_concurrent_reads` | 多读并发 | P1 |
| | `test_concurrent_writes` | 多写并发 | P1 |
| | `test_read_write_mix` | 读写混合 | P1 |
| **多 Stack 测试** | | | | |
| | `test_2stack_mesh` | 2-stack mesh | P2 |
| | `test_4stack_crossbar` | 4-stack crossbar | P2 |
| | `test_8stack` | 8-stack | P2 |
| **性能回归测试** | | | | |
| | `test_bandwidth_seq` | 顺序访问带宽 | P1 |
| | `test_bandwidth_rand` | 随机访问带宽 | P1 |
| | `test_latency_p99` | P99 延迟 | P1 |
| | `test_row_hit_rate` | Row hit 率 | P2 |

### 6.5 Performance Visualization

实时可视化方案：

```python
# 终端 ASCII 可视化
def plot_bandwidth_terminal(channel_data):
    """终端带宽柱状图"""
    print("Channel Bandwidth (GB/s):")
    for i, bw in enumerate(channel_data):
        bar = "█" * int(bw / 50)  # 50 GB/s = 1 block
        print(f"  Ch{i}: {bar} {bw:.1f}")

# 生成 HTML 报告
def generate_html_report(stats, output_path):
    """生成交互式 HTML 报告"""
    import json
    html = f"""
    <html>
    <body>
    <h1>HBM Simulation Report</h1>
    <div id="bandwidth-chart"></div>
    <div id="latency-histogram"></div>
    <script>
    // 使用 Chart.js 渲染
    </script>
    </body>
    </html>
    """

# VCD 波形输出 (用于 GTKWave)
def dump_vcd(trace_data, output_path):
    """导出 VCD 格式波形"""
    with open(output_path, 'w') as f:
        f.write("$timescale 1ns $end\n")
        f.write("$var wire 64 ! addr $end\n")
        # ... 标准 VCD 格式
```

---

## 7. Logging & Output Formats

### 7.1 Simulation Accuracy Levels

显式设计 5 个精度等级，便于不同阶段使用：

| Level | 名称 | 精度 | 速度 | 适用场景 |
|-------|------|------|------|----------|
| **L0** | Functional | 功能正确 | ⚡⚡⚡⚡⚡ | 软件/驱动联调 |
| **L1** | Transaction | 事务级延迟估算 | ⚡⚡⚡⚡ | 架构探索 |
| **L2** | Timing-Approx | 近似时序模型 | ⚡⚡⚡ | 性能分析 |
| **L3** | Timing-Accurate | 精确周期级时序 | ⚡⚡ | RTL 对齐 |
| **L4** | Bit-Accurate | 位级精确 | ⚡ | 最终验证 |

**设计原则**：每个组件声明其支持的精度等级：
```python
class Component:
    SUPPORTED_LEVELS = ["L0", "L1", "L2"]  # 不支持 L3/L4
```

### 7.2 Configuration Management

采用分层配置方案，避免参数混乱：

```
config/
├── global.yaml          # 全局配置
│   ├── simulation_mode   # L0-L4
│   ├── clock_freq        # 时钟频率
│   └── log_level         # 日志级别
├── stack.yaml            # Stack 级配置
│   ├── stack_count       # 1-8
│   ├── topology          # mesh/crossbar
│   └── interconnect_latency
├── channel.yaml         # Channel 级配置
│   ├── channels_per_stack
│   ├── pseudo_channels
│   └── data_rate
├── timing.yaml           # Timing 参数
│   ├── tCK, tRCD, tRP
│   ├── tRAS, tRC, tCCD
│   └── tRRD, tFAW, tRFC
└── workload.yaml        # Workload 配置
    ├── traffic_pattern
    ├── request_rate
    └── burst_size
```

### 7.3 Error Handling & Protocol Compliance

```python
class HBMError(Exception):
    """HBM 协议错误基类"""
    pass

class AddressError(HBMError):
    """地址越界或对齐错误"""
    pass

class TimingError(HBMError):
    """时序违规"""
    pass

class QueueOverflowError(HBMError):
    """队列溢出"""
    pass

class ProtocolViolationError(HBMError):
    """协议违规"""
    pass
```

**错误处理策略**：
| 级别 | 行为 | 用途 |
|------|------|------|
| ERROR | 抛出异常 | 协议违规、致命错误 |
| WARN | 记录并继续 | 性能降级、次优调度 |
| INFO | 记录并继续 | 调试信息 |

### 7.4 Data Consistency & Thread Safety

对于多 stack、多 channel 并行仿真，需要保证数据一致性：

```python
import threading
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class HBMRequest:
    request_id: int
    addr: int
    length: int
    is_read: bool
    priority: int
    timestamp: float

class ThreadSafeQueue:
    """线程安全的请求队列"""
    def __init__(self, max_size: int):
        self._queue = []
        self._lock = threading.Lock()
        self._max_size = max_size
    
    def push(self, req: HBMRequest) -> bool:
        with self._lock:
            if len(self._queue) >= self._max_size:
                return False  # Queue full
            self._queue.append(req)
            return True
    
    def pop(self) -> Optional[HBMRequest]:
        with self._lock:
            return self._queue.pop(0) if self._queue else None
```

**并发模型**：
| 组件 | 并发策略 |
|------|----------|
| Stack Model | 每个 stack 独立线程 |
| Channel Model | 每 channel 一个 actor/event |
| Scheduler | 全局锁保护 |
| Statistics | 原子操作 + 最终聚合 |

### 7.5 Performance Benchmarks

定义性能基准，确保模型效率：

| Metric | Target | 说明 |
|--------|--------|------|
| `sim_speed_L0` | > 10M req/s | Functional 模式吞吐量 |
| `sim_speed_L1` | > 1M req/s | Transaction 模式吞吐量 |
| `sim_speed_L2` | > 100K req/s | Timing-approx 模式吞吐量 |
| `sim_speed_L3` | > 10K req/s | Timing-accurate 模式吞吐量 |
| `memory_per_stack` | < 100MB | 每个 stack 内存占用 |
| `startup_time` | < 2s | 模型初始化时间 |

### 7.6 Log Levels
| Level | Usage |
|-------|-------|
| ERROR | Protocol violations, critical errors |
| WARN | Performance degradation, suboptimal scheduling |
| INFO | Simulation progress, key events |
| DEBUG | Detailed timing, queue state |

### 7.2 Output Formats
```python
# Numerical output (JSON)
{
    "simulation_time": 1.0,
    "metrics": {
        "bandwidth_effective": 750.2,
        "latency_avg": 85.3,
        "channel_utilization": [0.92, 0.88, ...]
    }
}

# Waveform output (VCD)
# Standard VCD format for waveform viewing in GTKWave/DVE
```

---

## 8. Verification Strategy

### 8.1 UVM Testbench
```
┌─────────────────────────────────────────────────────┐
│                    UVM Environment                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ AXI Agent   │  │ HBM Agent   │  │ Scoreboard  │ │
│  │ (Master)    │  │ (Slave)     │  │             │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                          │                         │
│  ┌─────────────────────────────────────────────────┐│
│  │         Reference Model (Python DPI-C)          ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### 8.2 Verification Tests
| Test | Description |
|------|-------------|
| `basic_read_write` | Simple sequential access |
| `random_access` | Random address pattern |
| `bank_conflict` | Test bank conflict handling |
| `refresh_test` | Refresh during active traffic |
| `qos_test` | QoS priority handling |
| `burst_test` | Various burst patterns |
| `channel_utilization` | Full channel bandwidth test |

---

## 9. References

1. **JEDEC JESD238** - HBM3 Specification
2. **Ramulator 2.0** - https://github.com/CMU-SAFARI/ramulator2
3. **Synopsys HBM3 Model** - DesignWare HBM3 PHY & Controller
4. **Cadence HBM IP** - HBM3/4 Memory Interface IP

---

## 10. Open Questions

- [x] HBM stack count for target SoC: 1-8 configurable (default 2)
- [x] Specific workload traces: Built-in traffic generator + trace reader interface
- [x] RTL integration timeline: 4-6 weeks (see docs/RTL_INTEGRATION.md)
- [x] Team members: AI-driven development (unlimited token)

---

## 11. Development Team

| Role | Members | Responsibility |
|------|---------|----------------|
| **Designer/Reviewer** | User | Design decisions, code review, approval |
| **Developer** | AI (Claude Code) | Implementation using subagents |
| **Integration** | AI | End-to-end integration, testing |

**Development Model**: Hybrid AI-driven
- User provides requirements and reviews designs
- AI executes implementation with parallel subagents
- Unlimited token budget enables rapid parallel development

---

## 12. Next Steps

### Phase A 详细启动计划

| Task | Owner | Parallel | Description |
|------|-------|----------|-------------|
| **A.1 项目初始化** | Subagent 1 | - | 创建目录结构、基础配置文件 |
| **A.2 基础框架** | Subagent 2 | A.1 | 创建基础类：HBMConfig, HBMRequest, HBMResponse |
| **A.3 地址解码器** | Subagent 3 | A.2 | AddressDecoder 实现，可配置映射 |
| **A.4 请求队列** | Subagent 4 | A.2 | ReadQueue, WriteQueue 实现 |
| **A.5 FR-FCFS 调度器** | Subagent 5 | A.3, A.4 | 调度器核心实现 |
| **A.6 QoS 调度器** | Subagent 6 | A.5 | QoS 模式实现 |
| **A.7 刷新调度器** | Subagent 7 | A.5 | RefreshScheduler |
| **A.8 集成测试** | Main | A.3-A.7 | 端到端集成测试 |

### 立即可执行的子任务

```
1. 创建 config/ 目录和基础 YAML 配置
2. 创建 model/controller/__init__.py
3. 实现 model/controller/config.py (HBMConfig 类)
4. 实现 model/controller/request.py (HBMRequest/HBMResponse)
5. 实现 model/controller/address_decoder.py
6. 实现 model/controller/queue.py
7. 实现 model/controller/scheduler.py
8. 实现 model/controller/refresh_scheduler.py
9. 创建 tests/controller/ 目录
10. 编写基础单元测试
```

### 依赖关系图

```
A.1 项目初始化
├── A.2 基础框架
│   ├── A.3 地址解码器
│   └── A.4 请求队列
│       └── A.5 FR-FCFS 调度器
│           ├── A.6 QoS 调度器
│           └── A.7 刷新调度器
└── A.8 集成测试 (依赖 A.3-A.7)
```

### 验收标准

| Milestone | 验收条件 | 交付物 |
|-----------|----------|--------|
| M1 | 代码可运行 | 基础框架，无语法错误 |
| M2 | 基础读写正确 | sequential read/write 测试通过 |
| M3 | 时序正确 | bank conflict 测试通过 |
| M4 | QoS 正常 | QoS 优先级测试通过 |
| M5 | 性能达标 | 100K req/s @ L1 模式 |

---

**Document Status**: Implementation Active v1.2 - Phases A & B Complete
**Last Updated**: 2026-06-15