# HBM System API Documentation

This document provides API reference for key classes in the HBM System Modeling Platform.

## Table of Contents

1. [HBMConfig](#hbmconfig)
2. [HBMController](#hbmcontroller)
3. [HBMRequest](#hbmrequest)
4. [HBMResponse](#hbmresponse)
5. [AddressDecoder](#addressdecoder)
6. [DecodedAddress](#decodedaddress)
7. [FRFCFSScheduler](#frfcFsscheduler)
8. [DRAMModel](#drammodel)
9. [DRAMCommand](#dramcommand)
10. [DRAMResponse](#dramresponse)
11. [HBMSimulator](#hbmsimulator)
12. [SimulationConfig](#simulationconfig)
13. [SimulationStats](#simulationstats)

---

## HBMConfig

Configuration class for HBM controller. All parameters have defaults and can be loaded from YAML.

**File:** `model/controller/config.py`

### Constructor

```python
HBMConfig(
    stack_count: int = 2,
    channels_per_stack: int = 8,
    pseudo_channels_per_channel: int = 2,
    banks_per_pseudo_channel: int = 16,
    bank_groups_per_channel: int = 8,
    row_size: int = 2048,
    burst_length: int = 32,
    data_rate: float = 6.4e9,
    io_width: int = 1024,
    read_latency_base: int = 30,
    write_latency_base: int = 10,
    phy_latency: int = 20,
    queue_depth: int = 32,
    max_outstanding: int = 16,
    address_mapping: str = "rbc",
    scheduler_mode: str = "fr-fcfs",
    write_drain_policy: str = "threshold",
    refresh_interval: float = 3.9e-6,
    refresh_penalty: float = 230e-9,
    timing: HBM3Timing = field(default_factory=HBM3Timing),
)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `from_yaml(path: str)` | `HBMConfig` | Load config from YAML file |
| `from_dict(data: Dict)` | `HBMConfig` | Load config from dictionary |
| `to_dict()` | `Dict[str, Any]` | Export config as dictionary |
| `calc_bandwidth()` | `float` | Calculate peak bandwidth per stack (GB/s) |
| `calc_bandwidth_total()` | `float` | Calculate total bandwidth for all stacks (GB/s) |

### Example

```python
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT

# Use default HBM3 config
config = HBM3_DEFAULT

# Create custom config
custom = HBMConfig(
    stack_count=4,
    channels_per_stack=16,
    data_rate=12.8e9,  # HBM4 speed
)

# Calculate bandwidth
peak_bw = config.calc_bandwidth()  # 819.2 GB/s for HBM3
```

---

## HBMController

Main controller integrating all Phase A components.

**File:** `model/controller/controller.py`

### Constructor

```python
HBMController(config: Optional[HBMConfig] = None)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `submit_request(request: HBMRequest)` | `bool` | Submit memory request, returns True if successful |
| `tick()` | `Tuple[Optional[HBMRequest], Optional[HBMResponse]]` | Execute one cycle, returns scheduled request and response |
| `get_bandwidth()` | `float` | Calculate effective bandwidth (GB/s) |
| `get_stats()` | `dict` | Get controller statistics |

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `config` | `HBMConfig` | Controller configuration |
| `decoder` | `AddressDecoder` | Address decoder instance |
| `queue_manager` | `QueueManager` | Request queue manager |
| `scheduler` | `HBMScheduler` | Request scheduler (FR-FCFS or QoS) |
| `refresh_manager` | `RefreshManager` | Refresh scheduler |
| `bank_states` | `Dict` | Bank state tracking |
| `stats` | `dict` | Statistics dictionary |

### Example

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
        print(f"Completed request {response.request_id}, latency={response.latency:.2f}ns")

# Get statistics
stats = controller.get_stats()
print(f"Total requests: {stats['controller']['total_requests']}")
print(f"Row hit rate: {stats['scheduler']['row_hit_rate']:.2%}")
```

---

## HBMRequest

Memory request data structure.

**File:** `model/controller/request.py`

### Constructor

```python
HBMRequest(
    addr: int,
    length: int,
    is_read: bool,
    qos: int = 8,
    burst_length: int = 32,
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `addr` | `int` | 64-bit physical address |
| `length` | `int` | Request length in bytes |
| `is_read` | `bool` | True=read, False=write |
| `qos` | `int` | QoS priority (0-15, 15 highest) |
| `request_id` | `int` | Unique request ID (auto-generated) |
| `stack_id` | `int` | Decoded stack ID |
| `channel_id` | `int` | Decoded channel ID |
| `pseudo_channel_id` | `int` | Decoded pseudo-channel ID |
| `bank_group_id` | `int` | Decoded bank group ID |
| `bank_id` | `int` | Decoded bank ID |
| `row_id` | `int` | Decoded row ID |
| `col_id` | `int` | Decoded column ID |
| `state` | `RequestState` | Current state |
| `row_hit` | `bool` | Whether this is a row hit |
| `arrival_time` | `float` | Arrival timestamp |
| `completion_time` | `float` | Completion timestamp |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `set_arrival_time(cycle: float)` | `None` | Set arrival time |
| `get_latency_cycles()` | `float` | Get latency in cycles |
| `mark_scheduled(timestamp: float)` | `None` | Mark as scheduled |
| `mark_completed(timestamp: float)` | `None` | Mark as completed |
| `mark_failed()` | `None` | Mark as failed |
| `set_write_data(data: bytes)` | `None` | Set write data |
| `get_write_data()` | `Optional[bytes]` | Get write data |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `latency` | `float` | Latency in seconds |
| `is_completed` | `bool` | Whether request is completed |
| `is_failed` | `bool` | Whether request failed |
| `is_pending` | `bool` | Whether request is pending |

---

## HBMResponse

Response data structure for completed requests.

**File:** `model/controller/request.py`

### Constructor

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

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `request_id` | `int` | Associated request ID |
| `status` | `str` | Status ("OK", "SLVERR", "DECERR") |
| `latency` | `float` | Response latency in nanoseconds |
| `channel_id` | `int` | Channel ID (HBM4) |
| `bank_id` | `int` | Bank ID |
| `data` | `Optional[bytes]` | Read data (for read requests) |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_success` | `bool` | Whether response indicates success |

---

## AddressDecoder

Address mapping and decoding for HBM.

**File:** `model/controller/address_decoder.py`

### Constructor

```python
AddressDecoder(config: HBMConfig, custom_mapping: Optional[Dict] = None)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `decode(addr: int)` | `DecodedAddress` | Decode 64-bit address to fields |
| `encode(decoded: DecodedAddress)` | `int` | Encode fields back to address |
| `get_bank_key(decoded: DecodedAddress)` | `Tuple` | Get unique bank identifier |
| `get_row_key(decoded: DecodedAddress)` | `Tuple` | Get unique row identifier |
| `get_channel_id_from_addr(addr: int)` | `int` | Fast channel extraction |
| `get_total_channels()` | `int` | Total channel count |

### Address Mapping Schemes

| Scheme | Description |
|--------|-------------|
| `rbc` | Row-Bank-Channel (default, best for sequential) |
| `bcr` | Bank-Channel-Row (maximizes parallelism) |
| `crb` | Channel-Row-Bank (cross-channel random) |
| `custom` | Configurable matrix |

### Example

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.address_decoder import AddressDecoder

decoder = AddressDecoder(HBM3_DEFAULT)

# Decode address
decoded = decoder.decode(0x1_0000_0000)
print(f"Channel: {decoded.channel_id}")
print(f"Bank: {decoded.bank_id}")
print(f"Row: 0x{decoded.row_id:x}")

# Get channel quickly
ch = decoder.get_channel_id_from_addr(0x1_0000_0000)
```

---

## DecodedAddress

Decoded address fields.

**File:** `model/controller/address_decoder.py`

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `stack_id` | `int` | Stack ID (Addr[47:46]) |
| `channel_id` | `int` | Channel ID (Addr[45:43]) |
| `pseudo_channel_id` | `int` | Pseudo-channel ID (Addr[42]) |
| `bank_group_id` | `int` | Bank group ID (Addr[41:39]) |
| `bank_id` | `int` | Bank ID (Addr[38:34]) |
| `row_id` | `int` | Row ID (Addr[33:16]) |
| `col_id` | `int` | Column ID (Addr[15:3]) |
| `byte_offset` | `int` | Byte offset (Addr[2:0]) |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_channel_key()` | `Tuple[int, int, int]` | (stack, channel, pseudo_channel) |
| `get_bank_key()` | `Tuple[int, int, int, int]` | (stack, channel, pseudo_channel, bank) |

---

## FRFCFSScheduler

First-Ready First-Come-First-Serve scheduler.

**File:** `model/controller/scheduler.py`

### Constructor

```python
FRFCFSScheduler(
    config: HBMConfig,
    rd_priority: float = 1.0,
    wr_priority: float = 1.0,
)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `schedule(read_queue, write_queue, bank_states, current_time, last_cmd_type)` | `Optional[HBMRequest]` | Schedule next request |

### Scheduling Policy

1. Prefer requests that hit open rows (row-hit priority)
2. Among same priority, select oldest by arrival time
3. Read/write arbitration with configurable priorities
4. Turnaround penalty for READ/WRITE switching

### Example

```python
from model.controller.scheduler import FRFCFSScheduler, BankState

scheduler = FRFCFSScheduler(config)

# Schedule from queues
bank_states = {
    (0, 0, 0): BankState(bank_id=0, is_open=True, open_row=100),
}

selected = scheduler.schedule(
    read_queue,
    write_queue,
    bank_states,
    current_time=1000.0,
    last_cmd_type="READ"
)
```

---

## DRAMModel

Complete DRAM model integrating stack, channel, and bank structures.

**File:** `model/dram/dram_model.py`

### Constructor

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

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_bank(stack_id, channel_id, bank_id)` | `BankStateMachine` | Get bank state machine |
| `check_bank_available(stack_id, channel_id, bank_id, current_time)` | `Tuple[bool, str]` | Check bank availability |
| `execute_activate(stack_id, channel_id, bank_id, row_id, current_time)` | `DRAMResponse` | Execute ACT command |
| `execute_read(stack_id, channel_id, bank_id, col_id, current_time, length)` | `DRAMResponse` | Execute READ command |
| `execute_write(stack_id, channel_id, bank_id, col_id, data, current_time)` | `DRAMResponse` | Execute WRITE command |
| `execute_precharge(stack_id, channel_id, bank_id, current_time)` | `DRAMResponse` | Execute PRE command |
| `execute_refresh(stack_id, channel_id, bank_id, current_time)` | `DRAMResponse` | Execute REF command |
| `execute_request(stack_id, ch_id, ps_id, bg_id, bank_id, row, cmd, ...)` | `bool` | Unified request interface |
| `tick(current_time)` | `None` | Update all bank states |
| `get_utilization(window=10000)` | `float` | Calculate bank utilization |
| `enable_memory_model()` | `None` | Enable full memory model |
| `reset()` | `None` | Reset DRAM model |
| `get_all_channel_stats()` | `Dict[int, Dict]` | Per-channel statistics |
| `get_channel_utilization(channel_id, window)` | `float` | Per-channel utilization |

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `config` | `Dict` | DRAM configuration |
| `timing` | `HBM*Timing` | Timing parameters |
| `stacks` | `List[Stack]` | Stack models |
| `stats` | `DRAMStats` | Statistics |

### Example

```python
from model.dram.dram_model import DRAMModel

dram = DRAMModel(hbm_version="hbm3", stack_count=2)

# Execute commands
resp = dram.execute_activate(
    stack_id=0, channel_id=0, bank_id=0,
    row_id=100, current_time=0
)

resp = dram.execute_read(
    stack_id=0, channel_id=0, bank_id=0,
    col_id=0, current_time=14, length=32
)

print(f"Read succeeded: {resp.success}")
print(f"Latency: {resp.latency_cycles} cycles")

# Get statistics
print(f"Total activations: {dram.stats.total_activations}")
print(f"Row hit rate: {dram.stats.row_hits / (dram.stats.row_hits + dram.stats.row_misses):.2%}")
```

---

## DRAMCommand

DRAM command enumeration.

**File:** `model/dram/dram_model.py`

### Values

| Command | Value | Description |
|---------|-------|-------------|
| `NOP` | 0 | No operation |
| `ACT` | 1 | Activate |
| `READ` / `RD` | 2 | Read |
| `WRITE` / `WR` | 3 | Write |
| `PRE` | 4 | Precharge |
| `REF` | 5 | Refresh |
| `MRS` | 6 | Mode Register Set |
| `ZQ` | 7 | ZQ calibration |

### Aliases

- `RD` = `READ`
- `WR` = `WRITE`

---

## DRAMResponse

DRAM command response.

**File:** `model/dram/dram_model.py`

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `success` | `bool` | Whether command succeeded |
| `data` | `Optional[bytes]` | Read data |
| `latency_cycles` | `int` | Latency in cycles |
| `error` | `Optional[str]` | Error message |

---

## HBMSimulator

Cycle-accurate simulation framework integrating all components.

**File:** `sim/simulator.py`

### Constructor

```python
HBMSimulator(sim_config: SimulationConfig)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `step()` | `Optional[HBMResponse]` | Execute one cycle, returns response if completed |
| `run()` | `SimulationStats` | Run simulation to completion |
| `run_verbose()` | `SimulationStats` | Run with detailed output |
| `get_completion_jitter()` | `Dict[str, float]` | Jitter statistics |
| `get_channel_stats()` | `Dict[int, ChannelStats]` | Per-channel statistics |
| `get_load_balance_score()` | `float` | Channel load balance (0-1) |
| `get_stats()` | `SimulationStats` | Get current statistics |

### Pipeline Integration

```
1. TrafficGenerator → generates requests
2. HBMController → schedules requests (FR-FCFS/QoS)
3. CommandSequencer → generates DRAM command sequences
4. CommandPipeline → executes commands with timing
5. DRAMModel → full DRAM timing model
```

### Example

```python
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

config = SimulationConfig(
    simulation_time_us=100.0,
    traffic_pattern=TrafficPattern.SEQUENTIAL,
    request_rate=0.5,
    read_ratio=0.7,
)

sim = HBMSimulator(config)
stats = sim.run()

print(f"Row hit rate: {stats.row_hit_rate:.2%}")
print(f"Throughput: {stats.throughput_gbps:.2f} GB/s")
print(f"Efficiency: {stats.efficiency:.2%}")
```

---

## SimulationConfig

Simulation configuration.

**File:** `sim/simulator.py`

### Constructor

```python
SimulationConfig(
    clock_freq_hz: float = 1.28e9,
    simulation_time_us: float = 100.0,
    traffic_pattern: TrafficPattern = TrafficPattern.RANDOM,
    request_rate: float = 0.5,
    read_ratio: float = 0.7,
    burst_size: int = 64,
    address_range: int = 0x100_0000,
    stride_value: int = 4096,
    hbm_config: HBMConfig = field(default_factory=lambda: HBM3_DEFAULT),
    enable_logging: bool = False,
    enable_stats: bool = True,
    seed: Optional[int] = None,
)
```

### Traffic Patterns

| Pattern | Description |
|---------|-------------|
| `RANDOM` | Random address access |
| `SEQUENTIAL` | Sequential address access |
| `STRIDE` | Fixed stride access |
| `HOT_SPOT` | 80% hot spot, 20% random |
| `ADDR_SCATTER` | Scattered address access |

---

## SimulationStats

Simulation statistics.

**File:** `sim/simulator.py`

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `total_cycles` | `int` | Total simulation cycles |
| `total_requests` | `int` | Total requests submitted |
| `completed_requests` | `int` | Completed requests |
| `read_requests` | `int` | Read requests |
| `write_requests` | `int` | Write requests |
| `row_hits` | `int` | Row hits |
| `row_misses` | `int` | Row misses |
| `row_conflicts` | `int` | Row conflicts |
| `total_latency_cycles` | `int` | Total latency sum |
| `refresh_count` | `int` | Refresh operations |
| `max_latency_cycles` | `int` | Maximum latency |
| `min_latency_cycles` | `int` | Minimum latency |
| `total_dram_activations` | `int` | Total DRAM activations |
| `idle_cycles` | `int` | Idle cycles |
| `busy_cycles` | `int` | Busy cycles |
| `per_channel_stats` | `Dict` | Per-channel statistics |

### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `avg_latency` | `float` | Average latency in cycles |
| `row_hit_rate` | `float` | Row hit rate (0-1) |
| `throughput_gbps` | `float` | Throughput in GB/s |
| `efficiency` | `float` | Bus efficiency (0-1) |
| `bandwidth_efficiency` | `float` | Bandwidth efficiency vs peak |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, Any]` | Export as dictionary |

---

## Quick Start Example

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

# Create controller with default HBM3 config
controller = HBMController(HBM3_DEFAULT)

# Submit requests
for i in range(10):
    request = HBMRequest(
        addr=0x1000 + i * 64,
        length=64,
        is_read=(i % 2 == 0)
    )
    controller.submit_request(request)

# Run simulation for 1000 cycles
for _ in range(1000):
    scheduled, response = controller.tick()
    if response:
        print(f"Request {response.request_id} completed, latency={response.latency:.2f}ns")

# Print statistics
stats = controller.get_stats()
print(f"Total requests: {stats['controller']['total_requests']}")
print(f"Read requests: {stats['controller']['read_requests']}")
print(f"Row hit rate: {stats['scheduler']['row_hit_rate']:.2%}")
```

## See Also

- [Architecture Documentation](ARCHITECTURE.md)
- [Design Document](design/2026-06-15-hbm-system-model-design.md)