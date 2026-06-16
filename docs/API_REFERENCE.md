# HBM4 API Reference

Complete API documentation for the HBM4 System Modeling Platform.

## Table of Contents

- [HBM4Spec](#hbm4spec)
- [HBM4Controller](#hbm4controller)
- [HBM4AddressDecoder](#hbm4addressdecoder)
- [HBM4QoSScheduler](#hbm4qosscheduler)
- [HBM4RefreshScheduler](#hbm4refreshscheduler)
- [DFI5Interface](#dfi5interface)
- [HBM4ChannelArray](#hbm4channelarray)
- [HBMRequest/HBMResponse](#hbmrequesthbmresponse)
- [Queue Classes](#queue-classes)

---

## HBM4Spec

HBM4 DRAM specification constants and timing parameters.

### Class Definition

```python
from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
```

### Constructor

```python
HBM4Spec(
    channels: int = 32,
    pseudo_channels_per_channel: int = 2,
    banks_per_pseudo_channel: int = 16,
    bank_groups_per_channel: int = 8,
    io_width: int = 2048,
    data_rate_gtps: float = 8.0,
    burst_length: int = 4,
    row_size: int = 2048,
    # ... timing parameters
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `channels` | int | Number of channels (32 for HBM4) |
| `pseudo_channels` | int | Total pseudo-channels (channels * pseudo_channels_per_channel) |
| `total_banks` | int | Total banks across all channels |
| `bandwidth` | float | Peak bandwidth in TB/s |
| `bandwidth_gbs` | float | Peak bandwidth in GB/s |

### Timing Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `tCK_ps` | float | Clock period in ps (125.0 @ 8 GT/s) |
| `nBL` | int | Burst length (4) |
| `nCL` | int | CAS latency (8) |
| `nRCDRD` | int | RAS to CAS delay - read (8) |
| `nRCDWR` | int | RAS to CAS delay - write (8) |
| `nRP` | int | Precharge command period (8) |
| `nRAS` | int | Row active time (20) |
| `nRC` | int | Row cycle time (22) |
| `nWR` | int | Write recovery (8) |
| `nCWL` | int | CAS write latency (3) |
| `nCCDS` | int | Column-to-column delay, same BG (2) |
| `nCCDL` | int | Column-to-column delay, diff BG (3) |
| `nRRDS` | int | RAS-to-RAS delay, same BG (3) |
| `nRRDL` | int | RAS-to-RAS delay, diff BG (4) |
| `nFAW` | int | Four-activate window (16) |
| `nRFC` | int | Refresh command duration (180) |
| `nREFI` | int | Refresh interval (3900) |

### Address Bit Fields

| Parameter | Type | Description |
|-----------|------|-------------|
| `ADDR_STACK_BITS` | int | Stack ID bits (2) |
| `ADDR_CHANNEL_BITS` | int | Channel bits (5 for 32 channels) |
| `ADDR_PCH_BITS` | int | Pseudo-channel bits (1) |
| `ADDR_BG_BITS` | int | Bank group bits (3) |
| `ADDR_BANK_BITS` | int | Bank bits (4) |
| `ADDR_ROW_BITS` | int | Row bits (19) |
| `ADDR_COL_BITS` | int | Column bits (6) |
| `ADDR_BURST_BITS` | int | Burst alignment bits (2) |

### Methods

#### get_channel_bits() -> Tuple[int, int]

```python
spec = HBM4Spec()
start, num_bits = spec.get_channel_bits()  # (0, 5)
```

Returns `(start_bit, num_bits)` for channel field.

#### create_hbm4_spec_from_speed_grade(speed_grade: str) -> HBM4Spec

```python
spec = create_hbm4_spec_from_speed_grade("16Gbps")
# Creates spec with 16 GT/s data rate
```

Supported grades: `"8Gbps"`, `"12Gbps"`, `"16Gbps"`.

---

## HBM4Controller

Main HBM4 memory controller integrating address decoding, QoS scheduling, refresh management, and DFI interface.

### Class Definition

```python
from model.controller.hbm4_controller import HBM4Controller
```

### Constructor

```python
controller = HBM4Controller(
    spec: Optional[HBM4Spec] = None,
    config: Optional[HBMConfig] = None,
    enable_qos: bool = True,
    enable_refresh: bool = True,
    enable_dfi: bool = True,
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `channels` | int | Number of HBM4 channels (32) |
| `pseudo_channels` | int | Total pseudo-channels (64) |
| `dfi_ready` | bool | DFI interface ready state |

### Core Methods

#### submit_request()

```python
request_id = controller.submit_request(
    addr: int,           # 64-bit physical address
    is_read: bool,       # True for read, False for write
    qos_level: int = 8,  # Priority (0-15, higher = higher priority)
    size_bytes: int = 64 # Request size
) -> Optional[str]       # Request ID or None if queue full
```

#### tick()

```python
responses = controller.tick() -> List[HBMResponse]
```

Execute one simulation cycle. Returns list of completed responses.

#### get_stats()

```python
stats = controller.get_stats() -> Dict
```

Returns comprehensive statistics including controller, spec, queues, QoS, refresh, and DFI stats.

#### get_bandwidth_gbs()

```python
bandwidth = controller.get_bandwidth_gbs() -> float
```

Calculate effective bandwidth in GB/s.

#### get_effective_bandwidth_tbps()

```python
bandwidth = controller.get_effective_bandwidth_tbps() -> float
```

Calculate effective bandwidth in TB/s.

### DFI Interface Methods

| Method | Description |
|--------|-------------|
| `dfi_request_ctrlupd()` | Request DFI control update |
| `dfi_set_frequency(freq_mhz)` | Set DFI frequency |
| `dfi_enter_freq_change()` | Enter frequency change sequence |
| `dfi_exit_freq_change()` | Exit frequency change sequence |
| `dfi_set_low_power(state)` | Set DFI low power state |
| `dfi_wakeup()` | Wakeup from low power |
| `dfi_get_signals()` | Get current DFI signal states |
| `dfi_get_statistics()` | Get DFI statistics |

### Training and Repair Methods

| Method | Description |
|--------|-------------|
| `trigger_training(channel_id)` | Trigger training for channel |
| `trigger_repair(channel_id, lane_mask)` | Trigger lane repair |

---

## HBM4AddressDecoder

HBM4-specific address decoder with 32-channel support and multiple mapping schemes.

### Class Definition

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
```

### Constructor

```python
decoder = HBM4AddressDecoder(
    spec: Optional[HBM4Spec] = None,
    mapping_scheme: str = "rbc"  # "rbc", "bcr", "crb", "hbm4"
)
```

### Mapping Schemes

| Scheme | Description | Best For |
|--------|-------------|----------|
| `"rbc"` / `"hbm4"` | Row-Bank-Channel (default) | Sequential access, streaming |
| `"bcr"` | Bank-Channel-Row | Maximizing bank parallelism |
| `"crb"` | Channel-Row-Bank | Cross-channel random access |

### Methods

#### decode()

```python
decoded = decoder.decode(addr: int) -> DecodedAddress
```

Decode 64-bit address into components.

**Returns DecodedAddress with:**
- `stack_id`: Stack identifier (0-3)
- `channel_id`: Channel identifier (0-31)
- `pseudo_channel_id`: Pseudo-channel (0-1)
- `bank_group_id`: Bank group (0-7)
- `bank_id`: Bank within group (0-15)
- `row_id`: Row address (0-65535)
- `col_id`: Column address (0-63)
- `burst_id`: Burst beat index (0-3)
- `byte_offset`: Byte offset (0-7)

#### get_channel_id()

```python
channel = decoder.get_channel_id(addr: int) -> int
```

Extract channel ID from address (0-31).

#### get_pseudo_channel_id()

```python
pch = decoder.get_pseudo_channel_id(addr: int) -> int
```

Extract pseudo-channel ID (0 or 1).

#### get_row_id()

```python
row = decoder.get_row_id(addr: int) -> int
```

Extract row ID (0-65535).

#### get_bank_id()

```python
bank = decoder.get_bank_id(addr: int) -> int
```

Extract bank ID (0-15).

#### get_bank_group_id()

```python
bg = decoder.get_bank_group_id(addr: int) -> int
```

Extract bank group ID (0-7).

#### get_column_id()

```python
col = decoder.get_column_id(addr: int) -> int
```

Extract column ID (0-63).

#### get_stack_id()

```python
stack = decoder.get_stack_id(addr: int) -> int
```

Extract stack ID (0-3).

#### validate_address()

```python
is_valid = decoder.validate_address(addr: int) -> bool
```

Validate that address is properly formatted for HBM4 (8-byte aligned, valid field ranges).

#### get_address_range()

```python
start, end = decoder.get_address_range(channel: Optional[int] = None) -> Tuple[int, int]
```

Calculate address range for a channel or full memory.

---

## HBM4QoSScheduler

HBM4 QoS scheduler with 16-level priority and anti-starvation.

### Class Definition

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel
```

### QoSLevel Enum

```python
class QoSLevel(IntEnum):
    CRITICAL = 15  # Real-time/critical
    HIGH = 12      # High priority
    NORMAL = 8     # Normal traffic
    LOW = 4        # Background/batch
    IDLE = 0       # Idle/probe
```

### Constructor

```python
scheduler = HBM4QoSScheduler(config: Optional[HBM4Spec] = None)
```

### Methods

#### submit_request()

```python
success = scheduler.submit_request(
    request_id: int,
    addr: int = 0,
    qos: int = 8,
    is_read: bool = True,
    channel: int = 0,
    pseudo_channel: int = 0,
    bank: int = 0,
    row: int = 0,
    col: int = 0,
    row_hit: bool = False,
    length: int = 64
) -> bool
```

Submit a request to the QoS scheduler queue.

#### schedule()

```python
next_req = scheduler.schedule() -> Optional[QueuedRequest]
```

Schedule the next request using QoS + FR-FCFS.

#### select_next()

```python
selected = scheduler.select_next(requests: List['HBMRequest']) -> Optional['HBMRequest']
```

Select next request from a list using QoS priority + FR-FCFS.

#### get_queue_size()

```python
size = scheduler.get_queue_size(qos_level: int) -> int
```

Get number of requests in a specific queue.

#### get_total_queue_size()

```python
total = scheduler.get_total_queue_size() -> int
```

Get total queued requests across all priorities.

#### clear_queue() / clear_all_queues()

```python
scheduler.clear_queue(qos_level: int)
scheduler.clear_all_queues()
```

Clear requests from queues.

#### get_stats()

```python
stats = scheduler.get_stats() -> Dict[str, Any]
```

Get scheduler statistics.

#### set_bandwidth_guarantee() / set_bandwidth_cap()

```python
scheduler.set_bandwidth_guarantee(qos_level: int, guarantee_gbs: float)
scheduler.set_bandwidth_cap(qos_level: int, cap_gbs: float)
```

Configure bandwidth parameters for QoS levels.

---

## HBM4RefreshScheduler

HBM4 refresh scheduler with all-bank, per-bank, and DRFM modes.

### Class Definition

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
```

### RefreshMode Enum

```python
class RefreshMode(Enum):
    ALL_BANKS = "all"         # Refresh all banks at once
    PER_BANK = "per_bank"     # Staggered per-bank refresh (default)
    BANK_GROUP = "bank_group"  # Refresh by bank group
```

### Constructor

```python
scheduler = HBM4RefreshScheduler(config: Optional[HBM4Spec] = None)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `mode` | RefreshMode | Current refresh mode |

### Methods

#### tick()

```python
scheduler.tick()
```

Advance refresh timer by one cycle.

#### can_refresh()

```python
can_refresh = scheduler.can_refresh() -> bool
```

Check if refresh is needed (enough cycles since last refresh).

#### get_refresh_command()

```python
cmd = scheduler.get_refresh_command() -> Optional[tuple]
```

Get the next refresh command to execute.

**Returns:** `('REFab', None, None, None)` for all-bank or `('REFsb', channel_id, pseudo_channel_id, bank_id)` for per-bank.

#### get_next_refresh_bank()

```python
channel, pch, bank = scheduler.get_next_refresh_bank() -> Optional[Tuple[int, int, int]]
```

Get next bank to refresh (convenience wrapper).

#### set_mode()

```python
scheduler.set_mode(mode: RefreshMode)
```

Set refresh operating mode.

#### mark_bank_refreshed()

```python
scheduler.mark_bank_refreshed(
    channel_id: int,
    pseudo_channel_id: int,
    bank_id: int,
    cycle: int
)
```

Mark a specific bank as refreshed.

#### enable_drfm()

```python
scheduler.enable_drfm(enabled: bool = True, threshold: int = None)
```

Enable/disable DRFM (Direct Refresh Management) for row-hammer mitigation.

#### get_banks_needing_refresh()

```python
banks = scheduler.get_banks_needing_refresh() -> List[int]
```

Get list of banks needing refresh (DRFM mode).

#### get_stats()

```python
stats = scheduler.get_stats() -> Dict[str, Any]
```

Get refresh scheduler statistics.

#### set_refresh_interval()

```python
scheduler.set_refresh_interval(cycles: int)
```

Set refresh interval (tREFI).

#### reset()

```python
scheduler.reset()
```

Reset scheduler state.

---

## DFI5Interface

DFI 5.0/5.1 interface implementation for controller-PHY communication.

### Class Definition

```python
from model.dram.dfi_interface import (
    DFI5Interface,
    DFICommand,
    DFILowPowerState,
    DFITimingParameters,
    DFISignals,
    DFIRequest,
    DFIResponse
)
```

### DFICommand Enum

```python
class DFICommand(Enum):
    ACT = 0b0000     # Activate
    PRE = 0b0001     # Precharge
    PREA = 0b0010    # Precharge all
    RD = 0b0011      # Read
    WR = 0b0100      # Write
    RDA = 0b0101     # Read with auto-precharge
    WRA = 0b0110     # Write with auto-precharge
    REFab = 0b0111   # All-bank refresh
    REFsb = 0b1000   # Per-bank refresh
    RFMab = 0b1001   # All-bank row flash memory refresh
    RFMsb = 0b1010   # Per-bank row flash memory refresh
```

### DFILowPowerState Enum

```python
class DFILowPowerState(Enum):
    LP_IDLE = 0          # Normal operation
    LP_CTRL = 1          # Controller in low-power
    LP_DATA = 2          # Data path in low-power
    LP_FREQ_CHANGE = 3   # Frequency change in progress
```

### Constructor

```python
dfi = DFI5Interface(
    config=None,
    timing_params: Optional[DFITimingParameters] = None,
    queue_config: Optional[DFIRequestQueueConfig] = None
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `cycle` | int | Current simulation cycle |
| `lp_state` | DFILowPowerState | Current low power state |
| `freq_change_en` | bool | Frequency change enable signal |
| `ctrlupd_req` | bool | Control update request signal |
| `pending_request_count` | int | Number of pending requests |
| `queue_available_capacity` | int | Available queue slots |
| `is_queue_full` | bool | Queue full status |

### Methods

#### tick()

```python
dfi.tick()
```

Advance simulation by one cycle.

#### encode_command()

```python
request = dfi.encode_command(
    cmd: str,              # 'ACT', 'PRE', 'RD', 'WR', etc.
    addr_vec: Dict[str, int],  # {'row': 100, 'bank': 0, 'channel': 0, ...}
    priority: int = 0
) -> DFIRequest
```

Encode a command into DFI request format.

#### queue_request()

```python
success = dfi.queue_request(request: DFIRequest) -> bool
```

Add request to queue.

#### get_next_request()

```python
request = dfi.get_next_request() -> Optional[DFIRequest]
```

Get next request from queue.

#### peek_request()

```python
request = dfi.peek_request() -> Optional[DFIRequest]
```

View next request without removing.

#### clear_requests()

```python
dfi.clear_requests()
```

Clear all pending requests.

#### Frequency Change Methods

| Method | Description |
|--------|-------------|
| `request_freq_change(target_freq_mhz)` | Request frequency change |
| `enter_freq_change()` | Enter frequency change sequence |
| `exit_freq_change()` | Exit frequency change sequence |
| `is_freq_change_complete()` | Check if frequency change complete |
| `get_freq_change_latency_remaining()` | Get remaining cycles |

#### Low Power Methods

| Method | Description |
|--------|-------------|
| `request_low_power(state)` | Request entry to low power state |
| `wakeup_from_low_power()` | Wakeup from low power |
| `set_low_power_state(state)` | Set low power state directly |

#### Control Update Methods

| Method | Description |
|--------|-------------|
| `request_ctrlupd()` | Request control update |
| `acknowledge_ctrlupd()` | Acknowledge control update |

#### Training Methods

| Method | Description |
|--------|-------------|
| `start_training()` | Initiate PHY training |
| `complete_training()` | Mark training complete |

#### Utility Methods

| Method | Description |
|--------|-------------|
| `get_dfi_signals()` | Get current DFI signal states |
| `get_statistics()` | Get interface statistics |
| `get_write_latency_ps()` | Get write latency in ps |
| `get_read_latency_ps()` | Get read latency in ps |
| `is_ready()` | Check if interface ready for commands |
| `can_accept_request()` | Check if can accept new requests |
| `reset()` | Reset interface to initial state |

---

## HBM4ChannelArray

Array of HBM4 channels for system-level simulation.

### Class Definition

```python
from model.dram.hbm4_channel_model import HBM4ChannelArray, HBM4Channel, PseudoChannel
```

### Constructor

```python
channel_array = HBM4ChannelArray(
    spec: Optional[HBM4Spec] = None,
    timing: Optional[HBM4Timing] = None
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `total_bandwidth_gbs` | float | Total system bandwidth in GB/s |
| `total_bandwidth_tbs` | float | Total system bandwidth in TB/s |

### Methods

#### get_channel()

```python
channel = channel_array.get_channel(channel_id: int) -> Optional[HBM4Channel]
```

Get a specific channel (0-31).

#### get_pseudo_channel()

```python
pc = channel_array.get_pseudo_channel(channel_id: int, pch_id: int) -> Optional[PseudoChannel]
```

Get a specific pseudo-channel.

#### tick()

```python
channel_array.tick()
```

Advance all channels by one cycle.

#### get_system_state_summary()

```python
summary = channel_array.get_system_state_summary() -> dict
```

Get system-wide state summary.

---

## HBMRequest/HBMResponse

Request and response classes for HBM transactions.

### HBMRequest

```python
from model.controller.request import HBMRequest, HBMResponse, RequestState
```

#### Constructor

```python
request = HBMRequest(
    addr: int,
    length: int,
    is_read: bool,
    qos: int = 8,
    burst_length: int = 32,
    request_id: int = 0,      # Auto-generated if 0
    arrival_time: float = 0.0,
    stack_id: int = 0,
    channel_id: int = 0,
    pseudo_channel_id: int = 0,
    bank_group_id: int = 0,
    bank_id: int = 0,
    row_id: int = 0,
    col_id: int = 0,
    row_hit: bool = False,
    state: RequestState = RequestState.PENDING,
    data: Optional[bytes] = None
)
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `latency` | float | Request latency in seconds |
| `is_completed` | bool | Completion status |
| `is_failed` | bool | Failure status |
| `is_pending` | bool | Pending status |

#### Methods

| Method | Description |
|--------|-------------|
| `mark_scheduled(timestamp)` | Mark as scheduled |
| `mark_in_progress()` | Mark as in progress |
| `mark_completed(timestamp)` | Mark as completed |
| `mark_failed()` | Mark as failed |
| `set_write_data(data)` | Set write data |
| `get_write_data()` | Get write data |
| `get_latency_cycles()` | Get latency in cycles |

### RequestState Enum

```python
class RequestState(IntEnum):
    PENDING = 0      # Waiting for scheduling
    SCHEDULED = 1    # Scheduled, waiting for execution
    IN_PROGRESS = 2  # In execution
    COMPLETED = 3    # Completed
    FAILED = 4       # Failed
```

### HBMResponse

```python
response = HBMResponse(
    request_id: int,
    status: str = "OK",
    latency: float = 0.0,
    channel_id: int = 0,
    bank_id: int = 0,
    data: Optional[bytes] = None
)
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_success` | bool | Success status |

---

## Queue Classes

Thread-safe request queues for HBM transactions.

### Class Definition

```python
from model.controller.queue import RequestQueue, ReadQueue, WriteQueue, QueueManager
```

### RequestQueue

Base thread-safe request queue.

#### Constructor

```python
queue = RequestQueue(max_depth: int = 32, name: str = "Queue")
```

#### Methods

| Method | Description |
|--------|-------------|
| `push(request, timeout=0)` | Add request to queue |
| `pop(timeout=0)` | Remove and return next request |
| `peek()` | View next request without removing |
| `remove(request_id)` | Remove specific request |
| `size()` | Get current queue size |
| `is_empty()` | Check if queue empty |
| `is_full()` | Check if queue full |
| `clear()` | Clear all requests |
| `get_stats()` | Get queue statistics |

### ReadQueue

Read request queue with FR-FCFS support.

#### Additional Methods

| Method | Description |
|--------|-------------|
| `get_row_hit_requests()` | Get all row-hit requests |
| `get_oldest_request()` | Get oldest request (FCFS) |
| `get_best_request()` | Get best request (FR-FCFS) |

### WriteQueue

Write request queue with drain support.

#### Additional Methods

| Method | Description |
|--------|-------------|
| `should_drain()` | Check if write drain needed |
| `get_oldest_request()` | Get oldest write request |
| `get_pending_bytes()` | Get total pending bytes |

### QueueManager

Manages read/write queues and scheduling decisions.

#### Constructor

```python
manager = QueueManager.create(queue_depth: int = 32)
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `read_queue` | ReadQueue | Read request queue |
| `write_queue` | WriteQueue | Write request queue |

#### Methods

| Method | Description |
|--------|-------------|
| `push_read(request)` | Add read request |
| `push_write(request)` | Add write request |
| `remove_read(request_id)` | Remove read request |
| `remove_write(request_id)` | Remove write request |
| `total_size()` | Total queue size |
| `is_full()` | Check if any queue full |
| `get_stats()` | Get all queue statistics |

---

## Error Classes

```python
from model.controller.exceptions import (
    QueueOverflowError,
    AddressError,
    TimingError,
    ControllerError
)
```

| Exception | Description |
|-----------|-------------|
| `QueueOverflowError` | Queue has reached maximum depth |
| `AddressError` | Invalid or misaligned address |
| `TimingError` | Timing constraint violation |
| `ControllerError` | General controller error |