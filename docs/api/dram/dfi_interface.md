# DFI 5.0 Interface API

DFI (DDR PHY Interface) 5.0/5.1 implementation for HBM4 controller-PHY communication.

## Class: DFI5Interface

```python
from model.dram.dfi_interface import DFI5Interface
```

### Constructor

```python
def __init__(
    self,
    config=None,
    timing_params: Optional[DFITimingParameters] = None,
    queue_config: Optional[DFIRequestQueueConfig] = None,
)
```

**Parameters:**
- `config`: Optional configuration object
- `timing_params`: Optional DFI timing parameters
- `queue_config`: Optional request queue configuration

### Timing Parameters

```python
@dataclass
class DFITimingParameters:
    tPHY_wrlAT: int = 5       # PHY write data ready time (cycles)
    tPHY_rdLat: int = 5        # PHY read data delay (cycles)
    tFC_LATENCY: int = 8       # Frequency change latency (cycles)
    tFC_EXIT: int = 4          # Exit frequency change (cycles)
    tLP_CTRL_ENTER: int = 2     # LP_CTRL entry latency (cycles)
    tLP_CTRL_EXIT: int = 2      # LP_CTRL exit latency (cycles)
    tLP_DATA_ENTER: int = 4     # LP_DATA entry latency (cycles)
    tLP_DATA_EXIT: int = 4      # LP_DATA exit latency (cycles)
    tCTRLUPD_LATENCY: int = 4   # Control update latency
    tTRAINING: int = 1000       # Training duration (cycles)
    tPWR_UP: int = 2            # Power-up latency
    tPWR_DOWN: int = 2           # Power-down latency
```

---

## Command Interface

### encode_command()

Encode a command into DFI request format.

```python
def encode_command(
    self,
    cmd: str,
    addr_vec: Dict[str, int],
    priority: int = 0,
) -> DFIRequest
```

**Parameters:**
- `cmd`: Command name ('ACT', 'PRE', 'RD', 'WR', etc.)
- `addr_vec`: Dictionary with address components
- `priority`: Request priority (higher = more urgent)

**Returns:** DFIRequest object

**Example:**
```python
dfi_req = dfi.encode_command(
    cmd='ACT',
    addr_vec={'row': 0x100, 'bank': 0, 'pseudo_channel': 0, 'channel': 0},
    priority=8,
)
```

### Supported Commands

| Command | DFI Code | Description |
|---------|----------|-------------|
| 'ACT' | 0b0000 | Activate |
| 'PRE' | 0b0001 | Precharge |
| 'PREA' | 0b0010 | Precharge all |
| 'RD' | 0b0011 | Read |
| 'WR' | 0b0100 | Write |
| 'RDA' | 0b0101 | Read with auto-precharge |
| 'WRA' | 0b0110 | Write with auto-precharge |
| 'REFab' | 0b0111 | All-bank refresh |
| 'REFsb' | 0b1000 | Per-bank refresh |
| 'RFMab' | 0b1001 | All-bank row flash memory refresh |
| 'RFMsb' | 0b1010 | Per-bank row flash memory refresh |

---

## Request Queue Management

### queue_request()

Add request to queue.

```python
def queue_request(self, request: DFIRequest) -> bool
```

### get_next_request()

Get next request from queue.

```python
def get_next_request(self) -> Optional[DFIRequest]
```

### peek_request()

View next request without removing.

```python
def peek_request(self) -> Optional[DFIRequest]
```

### clear_requests()

Clear all pending requests.

```python
def clear_requests(self)
```

### Queue Properties

| Property | Type | Description |
|----------|------|-------------|
| `pending_request_count` | int | Number of pending requests |
| `queue_available_capacity` | int | Available slots |
| `is_queue_full` | bool | Check if queue is full |

---

## Low Power State Management

### request_low_power()

Request entry to low power state.

```python
def request_low_power(self, state: DFILowPowerState) -> bool
```

### wakeup_from_low_power()

Wakeup from low power state.

```python
def wakeup_from_low_power(self)
```

### Low Power States

```python
class DFILowPowerState(Enum):
    LP_IDLE = 0          # Normal operation
    LP_CTRL = 1          # Controller in low-power
    LP_DATA = 2          # Data path in low-power
    LP_FREQ_CHANGE = 3   # Frequency change in progress
```

---

## Frequency Change Protocol

### request_freq_change()

Request a frequency change.

```python
def request_freq_change(self, target_freq_mhz: int) -> bool
```

### enter_freq_change()

Enter frequency change sequence.

```python
def enter_freq_change(self) -> bool
```

### exit_freq_change()

Exit frequency change sequence.

```python
def exit_freq_change(self) -> bool
```

### Frequency Change States

```python
class DFI5FreqChangeState(Enum):
    FC_IDLE = auto()           # Normal operation
    FC_REQUESTED = auto()      # Frequency change requested
    FC_ENTERING = auto()       # Entering frequency change
    FC_ACTIVE = auto()         # In frequency change
    FC_EXITING = auto()        # Exiting frequency change
    FC_LOCKING = auto()        # PLL/DLL re-locking
    FC_COMPLETE = auto()       # Frequency change complete
```

---

## Control Update Handshake

### request_ctrlupd()

Request a control update (dfi_ctrlupd_req).

```python
def request_ctrlupd(self) -> bool
```

### acknowledge_ctrlupd()

Acknowledge a control update (dfi_ctrlupd_ack).

```python
def acknowledge_ctrlupd(self) -> bool
```

---

## Power Management

### request_pwr_down()

Request power down.

```python
def request_pwr_down(self) -> bool
```

### set_pwr_up_done()

Set power-up completion indicator.

```python
def set_pwr_up_done(self, done: bool)
```

---

## Training

### start_training()

Initiate PHY training sequence.

```python
def start_training(self)
```

### complete_training()

Mark training as complete.

```python
def complete_training(self)
```

---

## Utility Methods

### get_response()

Get response from PHY.

```python
def get_response(self, response_id: int = 0) -> DFIResponse
```

### get_statistics()

Get interface statistics.

```python
def get_statistics(self) -> Dict[str, Any]
```

**Returns:**
```python
{
    "commands_sent": int,
    "commands_completed": int,
    "freq_changes": int,
    "lp_transitions": int,
    "errors": int,
    "ctrl_updates": int,
    "power_cycles": int,
    "current_size": int,
    "max_size": int,
    "dropped_count": int,
    "processed_count": int,
    "queue_utilization_pct": float,
}
```

### get_dfi_signals()

Get current state of all DFI signals.

```python
def get_dfi_signals(self) -> DFISignals
```

### is_ready()

Check if interface is ready for commands.

```python
def is_ready(self) -> bool
```

**Returns:** True if ready (not in LP_DATA or LP_FREQ_CHANGE)

---

## Usage Example

```python
from model.dram.dfi_interface import DFI5Interface, DFICommand, DFILowPowerState

# Create DFI interface
dfi = DFI5Interface()

# Queue memory commands
commands = [
    ('ACT', {'row': 0x100, 'bank': 0, 'channel': 0, 'pseudo_channel': 0}),
    ('RD', {'col': 0, 'bank': 0, 'channel': 0, 'pseudo_channel': 0}),
    ('PRE', {'bank': 0, 'channel': 0, 'pseudo_channel': 0}),
]

for cmd, addr in commands:
    dfi_req = dfi.encode_command(cmd, addr, priority=8)
    dfi.queue_request(dfi_req)

# Process commands
while not dfi.is_queue_full:
    req = dfi.get_next_request()
    if req:
        # Process request on PHY
        dfi.tick()

# Check statistics
stats = dfi.get_statistics()
print(f"Commands sent: {stats['commands_sent']}")
print(f"Queue utilization: {stats['queue_utilization_pct']:.1f}%")
```