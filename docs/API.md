# HBM4 System API Documentation

Complete API reference for the HBM4 System Modeling Platform covering HBM3 and HBM4 specifications with comprehensive usage examples.

## Table of Contents

1. [Configuration Classes](#1-configuration-classes)
2. [Controller Classes](#2-controller-classes)
3. [Request/Response Classes](#3-requestresponse-classes)
4. [Address Decoder Classes](#4-address-decoder-classes)
5. [Scheduler Classes](#5-scheduler-classes)
6. [Refresh Scheduler Classes](#6-refresh-scheduler-classes)
7. [DRAM Model Classes](#7-dram-model-classes)
8. [Interconnect Classes](#8-interconnect-classes)
9. [Traffic Generator Classes](#9-traffic-generator-classes)
10. [Simulation Classes](#10-simulation-classes)
11. [Benchmark Classes](#11-benchmark-classes)
12. [Complete Usage Examples](#12-complete-usage-examples)
13. [Migration from HBM3](#13-migration-from-hbm3)
14. [Performance Tuning](#14-performance-tuning)

---

## 1. Configuration Classes

### HBMConfig

Configuration class for HBM controller. All parameters have defaults and can be loaded from YAML.

**File:** `model/controller/config.py`

#### Constructor

```python
HBMConfig(
    stack_count: int = 2,                    # HBM stack count (1-8)
    channels_per_stack: int = 8,             # Channels per stack (4-16)
    pseudo_channels_per_channel: int = 2,   # Pseudo-channels per channel
    banks_per_pseudo_channel: int = 16,      # Banks per pseudo-channel
    bank_groups_per_channel: int = 8,        # Bank groups per channel
    row_size: int = 2048,                    # Row size in bytes
    burst_length: int = 32,                  # FLINE burst length
    data_rate: float = 6.4e9,               # Data rate in bits/s per pin
    io_width: int = 1024,                    # Interface width in bits
    read_latency_base: int = 30,            # Base read latency in cycles
    write_latency_base: int = 10,           # Base write latency in cycles
    phy_latency: int = 20,                   # PHY latency in cycles
    queue_depth: int = 32,                   # Maximum request queue depth
    max_outstanding: int = 16,               # Maximum outstanding requests
    address_mapping: str = "rbc",            # Address mapping scheme
    scheduler_mode: str = "fr-fcfs",         # Scheduler mode
    write_drain_policy: str = "threshold",    # Write drain policy
    refresh_interval: float = 3.9e-6,       # Refresh interval (tREFI)
    refresh_penalty: float = 230e-9,         # Refresh penalty (tRFC)
    timing: HBM3Timing = field(default_factory=HBM3Timing),
)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `from_yaml(path: str)` | `HBMConfig` | Load config from YAML file |
| `from_dict(data: Dict)` | `HBMConfig` | Load config from dictionary |
| `to_dict()` | `Dict[str, Any]` | Export config as dictionary |
| `copy()` | `HBMConfig` | Create deep copy |
| `calc_bandwidth()` | `float` | Calculate peak bandwidth per stack (GB/s) |
| `calc_bandwidth_total()` | `float` | Calculate total bandwidth for all stacks (GB/s) |

#### Examples

```python
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT

# Use default HBM3 config
config = HBM3_DEFAULT

# Use default HBM4 config
config = HBM4_DEFAULT

# Create custom HBM4 config
custom = HBMConfig(
    stack_count=4,
    channels_per_stack=32,
    data_rate=12.8e9,  # HBM4 speed
)

# Calculate bandwidth
peak_bw = config.calc_bandwidth()  # 819.2 GB/s for HBM3
total_bw = config.calc_bandwidth_total()  # 1638.4 GB/s for 2 stacks
```

---

### HBM4Spec

HBM4 DRAM specification constants based on JEDEC JESD270-4A.

**File:** `model/dram/hbm4_spec.py`

#### Constructor

```python
HBM4Spec(
    channels: int = 32,                      # 32 channels
    pseudo_channels_per_channel: int = 2,    # 2 pseudo-channels
    banks_per_pseudo_channel: int = 16,      # 16 banks
    bank_groups_per_channel: int = 8,        # 8 bank groups
    io_width: int = 2048,                    # 2048-bit interface
    data_rate_gtps: float = 8.0,            # GT/s
    burst_length: int = 4,                  # FLINE burst length
    row_size: int = 2048,                    # bytes
    # Timing parameters...
)
```

#### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `pseudo_channels` | `int` | Total pseudo-channels (channels x 2) |
| `total_banks` | `int` | Total banks across all channels |
| `bandwidth` | `float` | Peak bandwidth in TB/s |
| `bandwidth_gbs` | `float` | Peak bandwidth in GB/s |

#### Timing Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tCK_ps` | 125.0 | Clock period in ps |
| `nCL` | 8 | CAS latency |
| `nRCDRD` | 8 | RAS to CAS delay (read) |
| `nRCDWR` | 8 | RAS to CAS delay (write) |
| `nRP` | 8 | Precharge time |
| `nRAS` | 20 | Row active time |
| `nRFC` | 180 | Refresh cycle time |
| `nREFI` | 3900 | Refresh interval |

#### Speed Grade Presets

```python
from model.dram.hbm4_spec import create_hbm4_spec_from_speed_grade, HBM4_SPEED_GRADES

# Available speed grades
print(HBM4_SPEED_GRADES.keys())  # ['8Gbps', '12Gbps', '16Gbps']

# Create spec for specific speed grade
spec = create_hbm4_spec_from_speed_grade("8Gbps")
spec = create_hbm4_spec_from_speed_grade("12Gbps")
spec = create_hbm4_spec_from_speed_grade("16Gbps")
```

---

### TrafficConfig

Traffic generation configuration.

**File:** `model/traffic/traffic_generator.py`

```python
TrafficConfig(
    read_write_ratio: float = 0.7,           # 70% reads, 30% writes
    request_rate: float = 1e6,              # requests/second
    burst_size: int = 32,                    # requests per burst
    base_address: int = 0x100000000,
    address_range: int = 0x10000000000,      # 256 GB range
    address_stride: int = 64,                # 64-byte stride
    qos_distribution: Dict[int, float] = {...},
    channels: int = 32,
    pseudo_channels: int = 64,
    banks_per_channel: int = 16,
)
```

---

## 2. Controller Classes

### HBMController

Main controller integrating all Phase A components.

**File:** `model/controller/controller.py`

#### Constructor

```python
HBMController(config: Optional[HBMConfig] = None)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `submit_request(request: HBMRequest)` | `bool` | Submit memory request |
| `tick()` | `Tuple[Optional[HBMRequest], Optional[HBMResponse]]` | Execute one cycle |
| `get_bandwidth()` | `float` | Calculate effective bandwidth (GB/s) |
| `get_stats()` | `dict` | Get controller statistics |
| `reset()` | `None` | Reset controller state |

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `config` | `HBMConfig` | Controller configuration |
| `decoder` | `AddressDecoder` | Address decoder instance |
| `queue_manager` | `QueueManager` | Request queue manager |
| `scheduler` | `HBMScheduler` | Request scheduler |
| `refresh_manager` | `RefreshManager` | Refresh scheduler |
| `bank_states` | `Dict` | Bank state tracking |
| `stats` | `dict` | Statistics dictionary |

#### Example

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

controller = HBMController(HBM3_DEFAULT)

# Submit requests
for i in range(10):
    request = HBMRequest(addr=0x1000 + i * 64, length=64, is_read=True)
    controller.submit_request(request)

# Run simulation
for _ in range(1000):
    scheduled, response = controller.tick()
    if response:
        print(f"Completed request {response.request_id}")

# Get statistics
stats = controller.get_stats()
print(f"Total requests: {stats['controller']['total_requests']}")
print(f"Row hit rate: {stats['scheduler']['row_hit_rate']:.2%}")
```

---

### HBM4Controller

HBM4-specific controller with 32-channel support.

**File:** `model/controller/hbm4_controller.py`

#### Constructor

```python
HBM4Controller(
    spec: Optional[HBM4Spec] = None,
    config: Optional[HBMConfig] = None,
    enable_qos: bool = True,
    enable_refresh: bool = True,
    enable_dfi: bool = True,
)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `submit_request(addr, is_read, qos_level, size_bytes)` | `Optional[str]` | Submit request |
| `tick()` | `List[HBMResponse]` | Execute one cycle |
| `get_bandwidth_gbs()` | `float` | Effective bandwidth in GB/s |
| `get_effective_bandwidth_tbps()` | `float` | Effective bandwidth in TB/s |
| `get_stats()` | `Dict` | Comprehensive statistics |
| `dfi_request_ctrlupd()` | `None` | Request DFI control update |
| `dfi_set_frequency(freq_mhz)` | `None` | Set DFI frequency |
| `dfi_set_low_power(state)` | `None` | Set DFI low power state |
| `dfi_wakeup()` | `None` | Wakeup from low power |
| `dfi_get_signals()` | `DFISignals` | Get DFI signal states |
| `dfi_get_statistics()` | `Dict` | Get DFI statistics |
| `trigger_training(channel_id)` | `None` | Trigger PHY training |
| `trigger_repair(channel_id, lane_mask)` | `None` | Trigger lane repair |

#### Example

```python
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import create_hbm4_spec_from_speed_grade

# Create HBM4 controller with 16 Gbps spec
spec = create_hbm4_spec_from_speed_grade("16Gbps")
controller = HBM4Controller(
    spec=spec,
    enable_qos=True,
    enable_refresh=True,
    enable_dfi=True
)

# Submit read requests with QoS
request_id = controller.submit_request(
    addr=0x1_0000_0000,
    is_read=True,
    qos_level=12,  # HIGH priority
    size_bytes=64
)

# Submit write request
controller.submit_request(
    addr=0x2_0000_0000,
    is_read=False,
    qos_level=8,   # NORMAL priority
    size_bytes=64
)

# Run simulation cycle
responses = controller.tick()
for resp in responses:
    print(f"Completed: {resp.request_id}, latency={resp.latency}")

# Get performance metrics
bandwidth = controller.get_bandwidth_gbs()
print(f"Effective bandwidth: {bandwidth:.2f} GB/s")

stats = controller.get_stats()
print(f"Total requests: {stats['controller']['total_requests']}")
```

---

## 3. Request/Response Classes

### HBMRequest

Memory request data structure.

**File:** `model/controller/request.py`

#### Constructor

```python
HBMRequest(
    addr: int,                               # 64-bit address
    length: int,                            # Request length in bytes
    is_read: bool,                           # True=read, False=write
    qos: int = 8,                            # QoS priority (0-15)
    burst_length: int = 32,                  # Burst size
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `addr` | `int` | 64-bit physical address |
| `length` | `int` | Request length in bytes |
| `is_read` | `bool` | True=read, False=write |
| `qos` | `int` | QoS priority (0-15, 15 highest) |
| `request_id` | `int` | Unique request ID |
| `stack_id` | `int` | Decoded stack ID |
| `channel_id` | `int` | Decoded channel ID |
| `pseudo_channel_id` | `int` | Decoded pseudo-channel ID |
| `bank_group_id` | `int` | Decoded bank group ID |
| `bank_id` | `int` | Decoded bank ID |
| `row_id` | `int` | Decoded row ID |
| `col_id` | `int` | Decoded column ID |
| `row_hit` | `bool` | Whether this is a row hit |
| `state` | `RequestState` | Current state |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `set_arrival_time(cycle: float)` | `None` | Set arrival time |
| `get_latency_cycles()` | `float` | Get latency in cycles |
| `mark_scheduled(timestamp: float)` | `None` | Mark as scheduled |
| `mark_completed(timestamp: float)` | `None` | Mark as completed |
| `mark_failed()` | `None` | Mark as failed |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `latency` | `float` | Latency in seconds |
| `is_completed` | `bool` | Whether request is completed |
| `is_failed` | `bool` | Whether request failed |

### RequestState

Request state enumeration.

```python
class RequestState(IntEnum):
    PENDING = 0      # Waiting for scheduling
    SCHEDULED = 1    # Scheduled, waiting execution
    IN_PROGRESS = 2 # In execution
    COMPLETED = 3    # Completed successfully
    FAILED = 4       # Failed
```

---

### HBMResponse

Response data structure for completed requests.

**File:** `model/controller/request.py`

#### Constructor

```python
HBMResponse(
    request_id: int,
    status: str = "OK",
    latency: float = 0.0,
    channel_id: int = 0,
    bank_id: int = 0,
    data: Optional[bytes] = None,
)
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_success` | `bool` | Whether response indicates success |

---

## 4. Address Decoder Classes

### HBM4AddressDecoder

HBM4-specific address decoder with 32-channel support.

**File:** `model/controller/hbm4_address_decoder.py`

#### Constructor

```python
HBM4AddressDecoder(
    spec: Optional[HBM4Spec] = None,
    mapping_scheme: str = "rbc"  # "rbc", "bcr", "crb", "hbm4"
)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `decode(addr: int)` | `DecodedAddress` | Decode address to fields |
| `get_channel_id(addr: int)` | `int` | Extract channel ID (0-31) |
| `get_pseudo_channel_id(addr: int)` | `int` | Extract pseudo-channel ID |
| `get_bank_id(addr: int)` | `int` | Extract bank ID (0-15) |
| `get_bank_group_id(addr: int)` | `int` | Extract bank group ID (0-7) |
| `get_row_id(addr: int)` | `int` | Extract row ID (0-65535) |
| `get_column_id(addr: int)` | `int` | Extract column ID (0-63) |
| `get_stack_id(addr: int)` | `int` | Extract stack ID (0-3) |
| `validate_address(addr: int)` | `bool` | Validate address format |
| `get_address_range(channel)` | `Tuple[int, int]` | Get address range |

#### Address Mapping Schemes

| Scheme | Description | Best for |
|--------|-------------|----------|
| `rbc` (default) | Row-Bank-Channel | Sequential access |
| `bcr` | Bank-Channel-Row | Maximize parallelism |
| `crb` | Channel-Row-Bank | Cross-channel random |
| `hbm4` | HBM4 RBC variant | Same as RBC |

#### Address Bit Fields (RBC Default)

```
Addr[47:46] = Stack ID (2-bit, 4 stacks)
Addr[45:41] = Channel (5-bit, 32 channels)
Addr[40]    = Pseudo-channel (1-bit, 2 pseudo-channels)
Addr[39:37] = Bank group (3-bit, 8 bank groups)
Addr[36:33] = Bank within group (4-bit, 16 banks)
Addr[32:17] = Row (16-bit, 64K rows)
Addr[16:11] = Column (6-bit, 64 columns)
Addr[10:9]  = Burst beat (2-bit, 4-beat burst)
Addr[8:6]   = Byte offset (3-bit, 8-byte offset)
```

#### Example

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

decoder = HBM4AddressDecoder(mapping_scheme="rbc")

# Decode address
addr = 0x0001_2345_6789_ABC0
decoded = decoder.decode(addr)
print(f"Channel: {decoded.channel_id}")  # 0-31
print(f"Bank: {decoded.bank_id}")        # 0-15
print(f"Row: 0x{decoded.row_id:x}")      # 0x0-0xFFFF

# Quick field extraction
channel = decoder.get_channel_id(addr)
row = decoder.get_row_id(addr)
```

---

### DecodedAddress

Decoded address fields.

**File:** `model/controller/address_decoder.py`

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `stack_id` | `int` | Stack ID (0-3) |
| `channel_id` | `int` | Channel ID (0-31 for HBM4) |
| `pseudo_channel_id` | `int` | Pseudo-channel ID (0-1) |
| `bank_group_id` | `int` | Bank group ID (0-7) |
| `bank_id` | `int` | Bank ID (0-15) |
| `row_id` | `int` | Row ID (0-65535) |
| `col_id` | `int` | Column ID (0-63) |

---

## 5. Scheduler Classes

### HBM4QoSScheduler

HBM4 QoS Scheduler with anti-starvation.

**File:** `model/controller/hbm4_qos_scheduler.py`

#### Constructor

```python
HBM4QoSScheduler(config: Optional[HBM4Spec] = None)
```

#### Priority Levels

| Level | Name | Typical Use |
|-------|------|-------------|
| 15 | CRITICAL | Real-time/critical |
| 12 | HIGH | High priority |
| 8 | NORMAL | Normal traffic |
| 4 | LOW | Background/batch |
| 0 | IDLE | Idle/probe |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `submit_request(...)` | `bool` | Submit request to scheduler |
| `schedule()` | `Optional[QueuedRequest]` | Schedule next request |
| `select_next(requests: List)` | `Optional[HBMRequest]` | Select from list |
| `get_queue_size(qos_level: int)` | `int` | Queue size for level |
| `get_total_queue_size()` | `int` | Total queued requests |
| `get_stats()` | `Dict[str, Any]` | Scheduler statistics |
| `set_bandwidth_guarantee(qos_level, gbs)` | `None` | Set BW guarantee |
| `set_bandwidth_cap(qos_level, gbs)` | `None` | Set BW cap |
| `clear_queue(qos_level)` | `None` | Clear specific queue |
| `clear_all_queues()` | `None` | Clear all queues |

#### Bandwidth Guarantees (GB/s per stack)

```python
self.bw_guarantee = {
    QOS_CRITICAL: 200.0,
    QOS_HIGH: 300.0,
    QOS_NORMAL: 200.0,
    QOS_LOW: 100.0,
    QOS_IDLE: 0,
}
```

#### Example

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler

scheduler = HBM4QoSScheduler()

# Submit requests with different priorities
scheduler.submit_request(
    request_id=1, addr=0x1000, qos=15, is_read=True, row_hit=True
)
scheduler.submit_request(
    request_id=2, addr=0x2000, qos=8, is_read=True, row_hit=False
)

# Schedule highest priority, row-hit first
next_req = scheduler.schedule()
print(f"Scheduled: {next_req.request_id}, qos={next_req.qos}")
```

---

### FRFCFSScheduler

First-Ready First-Come-First-Serve scheduler.

**File:** `model/controller/scheduler.py`

#### Constructor

```python
FRFCFSScheduler(
    config: HBMConfig,
    rd_priority: float = 1.0,
    wr_priority: float = 1.0,
)
```

#### Scheduling Policy

1. Prefer requests that hit open rows (row-hit priority)
2. Among same priority, select oldest by arrival time
3. Read/write arbitration with configurable priorities
4. Turnaround penalty for READ/WRITE switching

---

## 6. Refresh Scheduler Classes

### HBM4RefreshScheduler

HBM4 Refresh Scheduler with autonomous per-bank refresh.

**File:** `model/controller/hbm4_refresh_scheduler.py`

#### Constructor

```python
HBM4RefreshScheduler(config: Optional[HBM4Spec] = None)
```

#### Refresh Modes

```python
class RefreshMode(Enum):
    ALL_BANKS = "all"         # Refresh all banks at once
    PER_BANK = "per_bank"     # Staggered per-bank refresh
    BANK_GROUP = "bank_group"  # Refresh by bank group
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `tick()` | `None` | Advance refresh timer |
| `can_refresh()` | `bool` | Check if refresh is needed |
| `get_refresh_command()` | `Optional[tuple]` | Get next refresh command |
| `get_next_refresh_bank()` | `Optional[Tuple[int,int,int]]` | Next bank to refresh |
| `set_mode(mode: RefreshMode)` | `None` | Set refresh mode |
| `mark_bank_refreshed(ch, bank, cycle)` | `None` | Mark bank refreshed |
| `enable_drfm(enabled, threshold)` | `None` | Enable DRFM |
| `get_banks_needing_refresh()` | `List[int]` | Get banks needing refresh |
| `get_stats()` | `Dict[str, Any]` | Refresh statistics |
| `set_refresh_interval(cycles)` | `None` | Set tREFI interval |
| `reset()` | `None` | Reset scheduler |

#### Example

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

scheduler = HBM4RefreshScheduler()

# Use per-bank refresh (default for HBM4)
scheduler.set_mode(RefreshMode.PER_BANK)

# Enable row-hammer mitigation
scheduler.enable_drfm(enabled=True, threshold=1000)

# Check for refresh needs
for _ in range(10000):
    scheduler.tick()
    cmd = scheduler.get_refresh_command()
    if cmd:
        print(f"Refresh command: {cmd}")
```

---

## 7. DRAM Model Classes

### HBM4Channel

HBM4 Channel Model with 32 independent channels.

**File:** `model/dram/hbm4_channel_model.py`

#### Command Encoding

```python
class HBM4Command(IntEnum):
    NOP = 0      # No operation
    ACT = 1      # Activate command
    READ = 2     # Read command
    WRITE = 3    # Write command
    PRE = 4      # Precharge single bank
    PREA = 5     # Precharge all banks
    REF = 6      # Refresh (all banks)
    RFM = 7      # Row flash memory refresh
```

#### Constructor

```python
HBM4Channel(channel_id: int, spec: Optional[HBM4Spec] = None, timing: Optional[HBM4Timing] = None)
```

#### Factory Method

```python
HBM4Channel.create_with_speed_grade(channel_id: int, speed_grade: str = "8Gbps")
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `issue_command(cmd, pch, bank, row, col)` | `bool` | Issue command |
| `issue_numeric_command(cmd, pch, bank, row, col)` | `bool` | Issue with numeric encoding |
| `tick()` | `None` | Advance channel time |
| `get_bank(pch, bank)` | `Optional[BankStateMachine]` | Get bank state machine |
| `is_row_hit(pch, row)` | `bool` | Check if row is open |
| `get_state_summary()` | `dict` | Get channel state |
| `reset()` | `None` | Reset channel |

#### Example

```python
from model.dram.hbm4_channel_model import HBM4Channel, HBM4Command

# Create channel with 8Gbps speed grade
channel = HBM4Channel.create_with_speed_grade(0, "8Gbps")

# Issue commands
channel.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
channel.issue_command('RD', pseudo_channel=0, bank=0, row=100)

# Or use numeric encoding (RTL interface)
channel.issue_numeric_command(HBM4Command.ACT, 0, 0, 100)
channel.issue_numeric_command(HBM4Command.READ, 0, 0, 100)

# Advance time
channel.tick()

# Check state
state = channel.get_state_summary()
print(f"Channel {state['channel_id']} state: {state['state']}")
```

---

### HBM4ChannelArray

Array of HBM4 channels for system-level simulation.

**File:** `model/dram/hbm4_channel_model.py`

#### Constructor

```python
HBM4ChannelArray(
    spec: Optional[HBM4Spec] = None,
    timing: Optional[HBM4Timing] = None
)
```

#### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `total_bandwidth_gbs` | `float` | Total bandwidth in GB/s |
| `total_bandwidth_tbs` | `float` | Total bandwidth in TB/s |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_channel(channel_id: int)` | `Optional[HBM4Channel]` | Get specific channel |
| `get_pseudo_channel(channel_id, pch_id)` | `Optional[PseudoChannel]` | Get pseudo-channel |
| `tick()` | `None` | Advance all channels |
| `get_system_state_summary()` | `dict` | System-wide state |
| `reset()` | `None` | Reset all channels |

---

### BankStateMachine

Bank state machine (IDLE/ACTIVATING/ACTIVE/PRECHARGING).

**File:** `model/dram/bank_state_machine.py`

#### Bank States

```python
class BankStateEnum(IntEnum):
    IDLE = 0
    ACTIVATING = 1
    ACTIVE = 2
    PRECHARGING = 3
    REFRESHING = 4
    POWER_DOWN = 5
    SELF_REFRESH = 6
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `activate(row: int)` | `bool` | Activate row |
| `precharge()` | `bool` | Precharge bank |
| `read()` | `bool` | Read from open row |
| `write()` | `bool` | Write to open row |
| `refresh()` | `bool` | Refresh bank |
| `can_activate()` | `bool` | Check if activation allowed |
| `can_precharge()` | `bool` | Check if precharge allowed |
| `can_read()` | `bool` | Check if read allowed |
| `can_write()` | `bool` | Check if write allowed |
| `is_row_hit(row: int)` | `bool` | Check row hit |
| `set_time(current_time: float)` | `None` | Update time |

---

### DRAMModel

Complete DRAM model integrating stack, channel, and bank structures.

**File:** `model/dram/dram_model.py`

#### Constructor

```python
DRAMModel(
    hbm_version: str = "hbm3",
    stack_count: int = 2,
    banks_per_channel: int = 16,
    rows_per_bank: int = 262144,
    cols_per_row: int = 128,
    bus_width: int = 64,
    burst_length: int = 4,
)
```

#### Factory Methods

```python
# Create model from configuration
model = create_dram_model(config)

# Create HBM4 model
model = DRAMModel(hbm_version="hbm4", stack_count=4)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_bank(stack_id, channel_id, bank_id)` | `BankStateMachine` | Get bank state machine |
| `check_bank_available(...)` | `Tuple[bool, str]` | Check bank availability |
| `execute_activate(...)` | `DRAMResponse` | Execute ACT command |
| `execute_read(...)` | `DRAMResponse` | Execute READ command |
| `execute_write(...)` | `DRAMResponse` | Execute WRITE command |
| `execute_precharge(...)` | `DRAMResponse` | Execute PRE command |
| `execute_refresh(...)` | `DRAMResponse` | Execute REF command |
| `execute_request(...)` | `bool` | Unified request interface |
| `tick(current_time)` | `None` | Update all bank states |
| `get_utilization(window=10000)` | `float` | Calculate bank utilization |
| `reset()` | `None` | Reset DRAM model |
| `get_all_channel_stats()` | `Dict[int, Dict]` | Per-channel statistics |

---

### DFI5Interface

DFI 5.1 interface for controller-PHY communication.

**File:** `model/dram/dfi_interface.py`

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `encode_command(cmd, addr_vec, priority)` | `DFIRequest` | Encode command |
| `queue_request(request)` | `bool` | Add request to queue |
| `get_next_request()` | `Optional[DFIRequest]` | Get next request |
| `peek_request()` | `Optional[DFIRequest]` | View next request |
| `clear_requests()` | `None` | Clear all pending requests |
| `request_freq_change(target_freq_mhz)` | `None` | Request frequency change |
| `enter_freq_change()` | `None` | Enter frequency change sequence |
| `exit_freq_change()` | `None` | Exit frequency change sequence |
| `is_freq_change_complete()` | `bool` | Check if frequency change done |
| `request_low_power(state)` | `None` | Request low power state |
| `wakeup_from_low_power()` | `None` | Wakeup from low power |
| `request_ctrlupd()` | `None` | Request control update |
| `get_dfi_signals()` | `DFISignals` | Get current DFI signals |
| `get_statistics()` | `Dict` | Get interface statistics |
| `is_ready()` | `bool` | Check if ready for commands |
| `reset()` | `None` | Reset interface |

---

## 8. Interconnect Classes

### CrossbarInterconnect

Full N x M crossbar switch interconnect.

**File:** `model/interconnect/interconnect.py`

#### Constructor

```python
CrossbarInterconnect(
    num_ports: int,                          # Number of input ports
    stack_count: int = 1,                    # HBM4 stacks (1-8)
    channels_per_stack: int = 32,            # Channels per stack
    routing_mode: RoutingMode = RoutingMode.ADDRESS_BASED,
    arbitration_mode: ArbitrationMode = ArbitrationMode.ROUND_ROBIN,
)
```

### MeshInterconnect

2D mesh interconnect.

```python
MeshInterconnect(
    rows: int,                               # Number of rows
    cols: int,                               # Number of columns
    stack_count: int = 1,
    channels_per_stack: int = 32,
    routing_mode: RoutingMode = RoutingMode.SHORTEST_PATH,
    arbitration_mode: ArbitrationMode = ArbitrationMode.ROUND_ROBIN,
)
```

### BinaryTreeInterconnect

Hierarchical binary tree interconnect.

```python
BinaryTreeInterconnect(
    num_leaves: int,                         # Number of leaf nodes
    stack_count: int = 1,
    channels_per_stack: int = 32,
    routing_mode: RoutingMode = RoutingMode.SHORTEST_PATH,
    arbitration_mode: ArbitrationMode = ArbitrationMode.ROUND_ROBIN,
)
```

#### Common Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `route_request(request: InterconnectRequest)` | `InterconnectResponse` | Route request |
| `tick()` | `None` | Advance simulation |
| `get_stats()` | `Dict[str, Any]` | Get statistics |
| `reset()` | `None` | Reset interconnect |

### InterconnectFactory

Factory for creating interconnect instances.

```python
from model.interconnect.interconnect import InterconnectFactory, TopologyType

# Create crossbar
ic = InterconnectFactory.create_crossbar(32, stack_count=4)

# Create mesh
ic = InterconnectFactory.create_mesh(rows=4, cols=8, stack_count=4)

# Create tree
ic = InterconnectFactory.create_tree(num_leaves=32, stack_count=4)

# Generic create
ic = InterconnectFactory.create(TopologyType.CROSSBAR, num_ports=32)
```

---

## 9. Traffic Generator Classes

### TrafficGenerator

HBM4 Traffic Generator with AI and synthetic patterns.

**File:** `model/traffic/traffic_generator.py`

#### Constructor

```python
TrafficGenerator(config: Optional[TrafficConfig] = None)
```

#### Traffic Patterns

```python
class TrafficPattern(IntEnum):
    # AI Training Patterns
    TRAINING_WEIGHT_UPDATE = 1
    TRAINING_GRADIENT = 2
    TRAINING_FEATURE_MAP = 3

    # AI Inference Patterns
    INFERENCE_BURST_READ = 10
    INFERENCE_WEIGHT_REUSE = 11
    INFERENCE_MIXED_PRECISION = 12

    # Synthetic Patterns
    SYNTHETIC_FIXED_RATE = 20
    SYNTHETIC_BURST = 21
    SYNTHETIC_RANDOM = 22
    SYNTHETIC_RAMP_UP = 23
    SYNTHETIC_RAMP_DOWN = 24
    SYNTHETIC_SINUSOIDAL = 25
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `generate(count: int, pattern: TrafficPattern)` | `List[HBMRequest]` | Generate requests |
| `set_pattern(pattern: TrafficPattern)` | `None` | Set traffic pattern |
| `generate_stream(pattern, batch_size)` | `Iterator` | Generate as stream |
| `get_stats()` | `Dict` | Get statistics |
| `reset()` | `None` | Reset generator |

#### Example

```python
from model.traffic.traffic_generator import TrafficGenerator, TrafficConfig, TrafficPattern

# Create generator
config = TrafficConfig(request_rate=1e6, read_write_ratio=0.7)
tg = TrafficGenerator(config)

# Generate synthetic traffic
requests = tg.generate(count=100, pattern=TrafficPattern.SYNTHETIC_RANDOM)

# Generate AI training traffic
tg.set_pattern(TrafficPattern.TRAINING_WEIGHT_UPDATE)
requests = tg.generate(count=100)

# Submit to controller
for req in requests:
    controller.submit_request(req)
```

---

### AddressGenerator

Configurable address generator.

```python
AddressGenerator(
    base_address: int = 0x100000000,
    address_range: int = 0x10000000000,
    stride: int = 64,
)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `sequential(count)` | `List[int]` | Sequential addresses |
| `random(count)` | `List[int]` | Random addresses |
| `stride_access(count, stride)` | `List[int]` | Strided addresses |
| `bank_round_robin(num_banks, count)` | `List[int]` | Bank round-robin |
| `channel_round_robin(num_channels, count)` | `List[int]` | Channel round-robin |

---

## 10. Simulation Classes

### HBMSimulator

Cycle-accurate simulation framework.

**File:** `sim/simulator.py`

#### Constructor

```python
HBMSimulator(sim_config: SimulationConfig)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `step()` | `Optional[HBMResponse]` | Execute one cycle |
| `run()` | `SimulationStats` | Run simulation |
| `run_verbose()` | `SimulationStats` | Run with detailed output |
| `get_completion_jitter()` | `Dict[str, float]` | Jitter statistics |
| `get_channel_stats()` | `Dict[int, ChannelStats]` | Per-channel stats |
| `get_load_balance_score()` | `float` | Channel balance |
| `get_stats()` | `SimulationStats` | Get statistics |
| `reset()` | `None` | Reset simulator |

### SimulationStats

Simulation statistics.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `total_cycles` | `int` | Total simulation cycles |
| `total_requests` | `int` | Total requests submitted |
| `completed_requests` | `int` | Completed requests |
| `row_hits` | `int` | Row hits |
| `row_misses` | `int` | Row misses |
| `total_latency_cycles` | `int` | Total latency sum |
| `refresh_count` | `int` | Refresh operations |

#### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `avg_latency` | `float` | Average latency in cycles |
| `row_hit_rate` | `float` | Row hit rate (0-1) |
| `throughput_gbps` | `float` | Throughput in GB/s |
| `efficiency` | `float` | Bus efficiency (0-1) |
| `bandwidth_efficiency` | `float` | Actual/Peak bandwidth ratio |
| `queue_utilization` | `float` | Queue usage |
| `queue_overflow` | `bool` | Whether overflow occurred |

---

## 11. Benchmark Classes

### BenchmarkConfig

Master configuration for all benchmarks.

**File:** `model/benchmark/benchmark_config.py`

```python
BenchmarkConfig(
    # Enable/disable specific benchmarks
    run_bandwidth: bool = True,
    run_latency: bool = True,
    run_scheduler: bool = True,
    run_comparison: bool = True,
    
    # Individual configurations
    bandwidth: BandwidthConfig = BandwidthConfig(),
    latency: LatencyConfig = LatencyConfig(),
    scheduler: SchedulerConfig = SchedulerConfig(),
    comparison: ComparisonConfig = ComparisonConfig(),
    
    # Output configuration
    verbose: bool = True,
    output_file: Optional[str] = None,
    generate_plots: bool = False,
    
    # Random seed
    random_seed: int = 42,
)
```

#### Preset Configurations

```python
# Quick benchmark for fast testing
config = BenchmarkConfig.quick()

# Comprehensive benchmark
config = BenchmarkConfig.comprehensive()
```

### SpeedGrade

HBM speed grade presets.

```python
class SpeedGrade(Enum):
    HBM3_6_4 = ("hbm3", 6.4, 1024)
    HBM4_8 = ("hbm4", 8.0, 2048)
    HBM4_12 = ("hbm4", 12.0, 2048)
    HBM4_16 = ("hbm4", 16.0, 2048)
```

### BandwidthBenchmark

Bandwidth performance testing.

```python
from model.benchmark.bandwidth_benchmark import BandwidthBenchmark

benchmark = BandwidthBenchmark(config=BandwidthConfig())
results = benchmark.run()
print(f"Peak bandwidth: {results['peak_gbs']:.2f} GB/s")
print(f"Sustained bandwidth: {results['sustained_gbs']:.2f} GB/s")
```

### LatencyBenchmark

Latency performance testing.

```python
from model.benchmark.latency_benchmark import LatencyBenchmark

benchmark = LatencyBenchmark(config=LatencyConfig())
results = benchmark.run()
print(f"Average latency: {results['avg_latency']:.2f} cycles")
print(f"P99 latency: {results['p99_latency']:.2f} cycles")
```

---

## 12. Complete Usage Examples

### Example 1: Basic HBM4 Controller Setup

```python
"""
Basic HBM4 Controller Setup and Usage
"""
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import create_hbm4_spec_from_speed_grade

# Create HBM4 controller with 16 Gbps specification
spec = create_hbm4_spec_from_speed_grade("16Gbps")
controller = HBM4Controller(
    spec=spec,
    enable_qos=True,
    enable_refresh=True,
    enable_dfi=True
)

# Submit some memory requests
for i in range(100):
    addr = 0x1000_0000 + i * 64
    is_read = (i % 2 == 0)
    qos = 12 if is_read else 8  # Reads get higher priority
    
    request_id = controller.submit_request(
        addr=addr,
        is_read=is_read,
        qos_level=qos,
        size_bytes=64
    )
    
# Run simulation for 1000 cycles
completed = []
for _ in range(1000):
    responses = controller.tick()
    completed.extend(responses)

# Get performance metrics
stats = controller.get_stats()
print(f"Total requests: {stats['controller']['total_requests']}")
print(f"Completed: {stats['controller']['completed_requests']}")
print(f"Bandwidth: {controller.get_bandwidth_gbs():.2f} GB/s")
```

### Example 2: Traffic Generator with Multiple Patterns

```python
"""
Traffic Generator with Multiple Patterns
"""
from model.traffic.traffic_generator import (
    TrafficGenerator,
    TrafficConfig,
    TrafficPattern
)
from model.controller.hbm4_controller import HBM4Controller

# Configure traffic generator
config = TrafficConfig(
    read_write_ratio=0.7,
    request_rate=1e6,
    burst_size=32,
    address_range=0x100_0000_0000  # 1TB range
)

tg = TrafficGenerator(config)
controller = HBM4Controller()

# Generate and submit sequential traffic
tg.set_pattern(TrafficPattern.SYNTHETIC_SEQUENTIAL)
requests = tg.generate(count=1000)
for req in requests:
    controller.submit_request(req)

# Run simulation
for _ in range(5000):
    controller.tick()

# Generate AI training traffic
tg.set_pattern(TrafficPattern.TRAINING_WEIGHT_UPDATE)
requests = tg.generate(count=1000)
for req in requests:
    controller.submit_request(req)

# Continue simulation
for _ in range(5000):
    controller.tick()

# Get combined statistics
stats = controller.get_stats()
print(f"Total throughput: {stats['throughput']:.2f} GB/s")
```

### Example 3: QoS Scheduling with Priority Levels

```python
"""
QoS Scheduling with Multiple Priority Levels
"""
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel
from model.controller.request import HBMRequest

scheduler = HBM4QoSScheduler()

# Submit requests with different QoS levels
requests = [
    # Critical real-time traffic
    HBMRequest(addr=0x1000, length=64, is_read=True, qos=QoSLevel.CRITICAL),
    
    # High priority reads
    HBMRequest(addr=0x2000, length=64, is_read=True, qos=QoSLevel.HIGH),
    
    # Normal traffic
    HBMRequest(addr=0x3000, length=64, is_read=True, qos=QoSLevel.NORMAL),
    
    # Background batch traffic
    HBMRequest(addr=0x4000, length=64, is_read=False, qos=QoSLevel.LOW),
]

for req in requests:
    scheduler.submit_request(
        request_id=req.request_id,
        addr=req.addr,
        qos=req.qos,
        is_read=req.is_read,
        row_hit=False
    )

# Schedule with QoS priority
scheduled = []
while True:
    next_req = scheduler.schedule()
    if next_req is None:
        break
    scheduled.append(next_req)
    print(f"Scheduled: req={next_req.request_id}, QoS={next_req.qos}")

# Verify QoS ordering
assert scheduled[0].qos == QoSLevel.CRITICAL, "Critical should be first"
print(f"QoS scheduling verified: {len(scheduled)} requests ordered by priority")

# Configure bandwidth guarantees
scheduler.set_bandwidth_guarantee(QoSLevel.CRITICAL, 200.0)  # 200 GB/s
scheduler.set_bandwidth_cap(QoSLevel.LOW, 50.0)               # Max 50 GB/s

# Get queue status
for level in [QoSLevel.CRITICAL, QoSLevel.HIGH, QoSLevel.NORMAL, QoSLevel.LOW]:
    size = scheduler.get_queue_size(level)
    print(f"Queue {level.name}: {size} requests")
```

### Example 4: Refresh Scheduler Configuration

```python
"""
Refresh Scheduler Configuration
"""
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.dram.hbm4_spec import create_hbm4_spec_from_speed_grade

# Create refresh scheduler for HBM4
spec = create_hbm4_spec_from_speed_grade("8Gbps")
scheduler = HBM4RefreshScheduler(spec)

# Configure refresh mode
scheduler.set_mode(RefreshMode.PER_BANK)  # Staggered refresh

# Enable row hammer mitigation (DRFM)
scheduler.enable_drfm(enabled=True, threshold=1000)

# Set custom refresh interval (tREFI)
scheduler.set_refresh_interval(cycles=3900)  # 3.9 us @ 8 GT/s

# Simulate refresh operations
for cycle in range(100000):
    scheduler.tick()
    
    if scheduler.can_refresh():
        cmd = scheduler.get_refresh_command()
        if cmd:
            print(f"Cycle {cycle}: {cmd}")
            
            # Get next bank to refresh
            bank_info = scheduler.get_next_refresh_bank()
            if bank_info:
                channel, pch, bank = bank_info
                scheduler.mark_bank_refreshed(channel, pch, bank, cycle)

# Check banks needing refresh (DRFM mode)
banks_needing = scheduler.get_banks_needing_refresh()
print(f"Banks needing refresh: {len(banks_needing)}")

# Get statistics
stats = scheduler.get_stats()
print(f"Total refreshes: {stats['refresh_count']}")
print(f"DRFM activations: {stats.get('drfm_count', 0)}")
```

### Example 5: Running Full Simulation with Statistics

```python
"""
Running Full Simulation with Statistics
"""
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
from model.controller.config import HBM4_DEFAULT

# Create simulation configuration
sim_config = SimulationConfig(
    clock_freq_hz=1.6e9,           # 16 GT/s
    simulation_time_us=100.0,     # 100 us simulation
    traffic_pattern=TrafficPattern.RANDOM,
    request_rate=0.8,             # 80% utilization
    read_ratio=0.7,               # 70% reads
    burst_size=64,
    hbm_config=HBM4_DEFAULT,
    queue_depth=256,
    enable_stats=True,
    seed=42
)

# Create and run simulator
simulator = HBMSimulator(sim_config)

# Run with verbose output
print("Running simulation...")
stats = simulator.run_verbose()

# Print results
print(f"\n=== Simulation Results ===")
print(f"Total cycles: {stats.total_cycles:,}")
print(f"Completed requests: {stats.completed_requests:,}")
print(f"Average latency: {stats.avg_latency:.2f} cycles")
print(f"Row hit rate: {stats.row_hit_rate:.2%}")
print(f"Throughput: {stats.throughput_gbps:.2f} GB/s")
print(f"Efficiency: {stats.efficiency:.2%}")
print(f"Queue overflow: {stats.queue_overflow}")

# Get per-channel statistics
channel_stats = simulator.get_channel_stats()
print(f"\n=== Channel Statistics ===")
for ch_id, ch_stats in sorted(channel_stats.items()):
    print(f"Channel {ch_id}: {ch_stats.total_requests} requests, "
          f"{ch_stats.hit_rate:.2%} hit rate")
```

---

## 13. Migration from HBM3

### Key Differences

| Feature | HBM3 | HBM4 |
|---------|------|------|
| Channels per stack | 8 | 32 |
| Interface width | 1024-bit | 2048-bit |
| Pseudo-channels | 16 | 64 |
| Data rate | 6.4 GT/s | 8/12/16 GT/s |
| Peak bandwidth | 819.2 GB/s | 2.048 TB/s |
| Burst length | 32 bytes | 4 beats |
| Address bits | 42 | 48 |

### Configuration Migration

```python
# HBM3 Configuration (OLD)
from model.controller.config import HBMConfig, HBM3_DEFAULT

config = HBMConfig(
    stack_count=2,
    channels_per_stack=8,
    io_width=1024,
    data_rate=6.4e9,
)

# HBM4 Configuration (NEW)
from model.controller.config import HBMConfig, HBM4_DEFAULT
from model.dram.hbm4_spec import HBM4Spec

# Option 1: Use default HBM4 config
config = HBM4_DEFAULT

# Option 2: Create custom HBM4 config
config = HBMConfig(
    stack_count=4,
    channels_per_stack=32,      # Changed from 8
    io_width=2048,              # Changed from 1024
    data_rate=8.0e9,            # Changed from 6.4e9
    burst_length=4,             # Changed from 32
)

# Option 3: Use HBM4Spec directly
spec = HBM4Spec(
    channels=32,
    data_rate_gtps=8.0,
    io_width=2048,
)
```

### Controller Migration

```python
# HBM3 Controller (OLD)
from model.controller.controller import HBMController

controller = HBMController(hbm_config)

# HBM4 Controller (NEW)
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import create_hbm4_spec_from_speed_grade

spec = create_hbm4_spec_from_speed_grade("16Gbps")
controller = HBM4Controller(
    spec=spec,
    config=hbm_config,
    enable_qos=True,
    enable_refresh=True,
    enable_dfi=True
)
```

### Speed Grade Selection

```python
from model.dram.hbm4_spec import create_hbm4_spec_from_speed_grade

# 8 GT/s (JEDEC baseline)
spec_8g = create_hbm4_spec_from_speed_grade("8Gbps")
print(f"8Gbps bandwidth: {spec_8g.bandwidth:.3f} TB/s")

# 12 GT/s (Extended rate)
spec_12g = create_hbm4_spec_from_speed_grade("12Gbps")
print(f"12Gbps bandwidth: {spec_12g.bandwidth:.3f} TB/s")

# 16 GT/s (Maximum rate)
spec_16g = create_hbm4_spec_from_speed_grade("16Gbps")
print(f"16Gbps bandwidth: {spec_16g.bandwidth:.3f} TB/s")
```

---

## 14. Performance Tuning

### Address Mapping Selection

Choose the right mapping for your workload:

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

# Sequential/streaming workloads - RBC (Row-Bank-Channel)
decoder = HBM4AddressDecoder(mapping_scheme="rbc")

# Random access with bank parallelism - BCR (Bank-Channel-Row)
decoder = HBM4AddressDecoder(mapping_scheme="bcr")

# Cross-channel random access - CRB (Channel-Row-Bank)
decoder = HBM4AddressDecoder(mapping_scheme="crb")
```

### Queue Depth Configuration

```python
from model.controller.config import HBMConfig

# Low latency requirements
config_low_latency = HBMConfig(
    queue_depth=32,
    max_outstanding=16,
)

# High throughput (batch processing)
config_high_throughput = HBMConfig(
    queue_depth=256,
    max_outstanding=128,
)

# Balanced
config_balanced = HBMConfig(
    queue_depth=64,
    max_outstanding=32,
)
```

### Performance Checklist

1. **Row Locality**: Aim for >60% row hit rate
2. **Queue Sizing**: Keep utilization below 80%
3. **Channel Balance**: Monitor load balance score >0.8
4. **Refresh Overhead**: Target <5% overhead
5. **QoS Guarantees**: Ensure critical traffic meets latency SLAs
6. **Bandwidth Efficiency**: Target >20% of peak

---

## Quick Reference

### Import All Core Classes

```python
# Configuration
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT

# Controller
from model.controller.controller import HBMController
from model.controller.hbm4_controller import HBM4Controller

# Requests
from model.controller.request import HBMRequest, HBMResponse, RequestState

# Address Decoder
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

# Scheduler
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler

# Refresh
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

# DRAM Model
from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.hbm4_channel_model import HBM4Channel, HBM4Command

# Interconnect
from model.interconnect.interconnect import CrossbarInterconnect, MeshInterconnect

# Traffic Generator
from model.traffic.traffic_generator import TrafficGenerator, TrafficConfig, TrafficPattern

# Simulation
from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats
```

### Common Patterns

```python
# Basic simulation loop
controller = HBMController(HBM3_DEFAULT)
for i in range(1000):
    scheduled, response = controller.tick()
    if response:
        print(f"Completed: {response.request_id}")

# HBM4 with traffic generator
config = TrafficConfig(request_rate=1e6)
tg = TrafficGenerator(config)
requests = tg.generate(100, TrafficPattern.SYNTHETIC_RANDOM)
for req in requests:
    controller.submit_request(req)

# Address decoding
decoder = HBM4AddressDecoder()
decoded = decoder.decode(0x123456789ABC)
print(f"Ch={decoded.channel_id}, Row=0x{decoded.row_id:x}")
```

---

## See Also

- [Architecture Documentation](ARCHITECTURE.md)
- [Quick Start Guide](QUICKSTART.md)
- [Design Document](design/2026-06-15-hbm-system-model-design.md)
- [HBM3 Specification Reference](specs/hbm3_spec.md)
- [API Reference](API_REFERENCE.md) - Complete API documentation