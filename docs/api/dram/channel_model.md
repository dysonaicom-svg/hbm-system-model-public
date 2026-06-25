# HBM4ChannelModel API

Channel model with independent timing domains and enhanced bank state tracking.

## Class: HBM4Channel

```python
from model.dram.hbm4_channel_model import HBM4Channel
```

### Constructor

```python
def __init__(
    self,
    channel_id: int,
    spec: Optional[HBM4Spec] = None,
    timing: Optional[HBM4Timing] = None,
    use_enhanced_banks: bool = True,
)
```

**Parameters:**
- `channel_id`: Channel index (0-31)
- `spec`: HBM4 specification (uses default if None)
- `timing`: HBM4 timing parameters (uses default if None)
- `use_enhanced_banks`: Use enhanced HBM4BankStateMachine if True

### Factory Method

```python
@classmethod
def create_with_speed_grade(
    cls,
    channel_id: int,
    speed_grade: str = "8Gbps",
    timing: Optional[HBM4Timing] = None,
    use_enhanced_banks: bool = True,
) -> "HBM4Channel"
```

Create channel configured for specific speed grade.

**Parameters:**
- `speed_grade`: One of "8Gbps", "12Gbps", "16Gbps"

---

## Command Interface

### issue_command()

Issue a command to this channel with performance tracking.

```python
def issue_command(
    self,
    cmd: str,
    pseudo_channel: int,
    bank: int,
    row: int,
    col: int = 0,
) -> bool
```

**Parameters:**
- `cmd`: Command name ('ACT', 'PRE', 'RD', 'WR', etc.)
- `pseudo_channel`: Pseudo-channel index (0 or 1)
- `bank`: Bank index (0-15)
- `row`: Row index
- `col`: Column index

**Returns:** True if command succeeded

**Example:**
```python
channel = HBM4Channel.create_with_speed_grade(0, "16Gbps")

# Activate a row
channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0x100)

# Read from the row
channel.issue_command('RD', pseudo_channel=0, bank=0, row=0x100)

# Precharge
channel.issue_command('PRE', pseudo_channel=0, bank=0, row=0)
```

### issue_numeric_command()

Issue command using numeric encoding (RTL interface).

```python
def issue_numeric_command(
    self,
    cmd: HBM4Command,
    pseudo_channel: int,
    bank: int,
    row: int,
    col: int = 0,
) -> bool
```

### issue_command_with_bank_group()

Issue command with explicit bank group targeting.

```python
def issue_command_with_bank_group(
    self,
    cmd: str,
    pseudo_channel: int,
    bank_group: int,
    bank_in_group: int,
    row: int,
    col: int = 0,
) -> bool
```

---

## Timing Methods

### tick()

Advance channel time by one cycle and update statistics.

```python
def tick(self)
```

### set_time()

Set current simulation cycle and propagate to pseudo-channels.

```python
def set_time(self, current_cycle: int) -> None
```

### validate_timing()

Validate timing for all banks in this channel.

```python
def validate_timing(self) -> List[TimingViolation]
```

**Returns:** List of timing violations

---

## State Query Methods

### get_bank()

Get a specific bank state machine.

```python
def get_bank(self, pseudo_channel: int, bank: int)
```

**Parameters:**
- `pseudo_channel`: Pseudo-channel index (0 or 1)
- `bank`: Bank index (0-15)

**Returns:** Bank state machine or None if invalid

### get_bank_group()

Get a specific bank group.

```python
def get_bank_group(
    self,
    pseudo_channel: int,
    bank_group: int,
) -> Optional[BankGroup]
```

### is_row_hit()

Check if row is currently open.

```python
def is_row_hit(self, pseudo_channel: int, row: int) -> bool
```

### can_schedule_command()

Check if a command can be scheduled respecting timing constraints.

```python
def can_schedule_command(
    self,
    cmd: str,
    pseudo_channel: int,
    bank_group: int,
) -> bool
```

### get_scheduler_state()

Get scheduler state for a pseudo-channel.

```python
def get_scheduler_state(self, pseudo_channel: int) -> Dict
```

### get_timing_domain_state()

Get timing domain state for a pseudo-channel.

```python
def get_timing_domain_state(self, pseudo_channel: int) -> Dict
```

---

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `peak_bandwidth_gbs` | float | Peak bandwidth per channel in GB/s |
| `peak_bandwidth_tbs` | float | Peak bandwidth per channel in TB/s |
| `total_pseudo_channels` | int | Total pseudo-channels (32 x 2) |
| `total_bank_groups` | int | Total bank groups per channel |

**Peak Bandwidth Calculation:**
- 16 GT/s x 64-bit / 8 = 128 GB/s per channel
- 32 channels x 128 GB/s = 4.096 TB/s total

---

## Performance Statistics

### get_performance_stats()

Get performance statistics for this channel.

```python
def get_performance_stats(self) -> ChannelPerformanceStats
```

**Returns:** ChannelPerformanceStats object

### get_state_summary()

Get channel state summary with performance statistics.

```python
def get_state_summary(self) -> dict
```

**Returns:**
```python
{
    'channel_id': int,
    'state': str,
    'pseudo_channels': [
        {
            'id': int,
            'state': str,
            'open_row': int,
            'active_banks': int,
            'bank_groups': [...],
            'stats': {...},
        }
    ],
    'current_cycle': int,
    'timing_violations': int,
    'performance': {...},
}
```

---

## Statistics Class: ChannelPerformanceStats

```python
@dataclass
class ChannelPerformanceStats:
    # Command counts
    act_count: int = 0
    read_count: int = 0
    write_count: int = 0
    precharge_count: int = 0
    refresh_count: int = 0

    # Data transferred (bytes)
    read_bytes: int = 0
    write_bytes: int = 0

    # Latency tracking
    total_read_latency: int = 0
    total_write_latency: int = 0

    # Row hit/miss tracking
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0
```

**Computed Properties:**

| Property | Description |
|----------|-------------|
| `average_read_latency` | Average read latency in cycles |
| `average_write_latency` | Average write latency in cycles |
| `row_hit_rate` | Row hit rate as percentage |
| `total_cycles` | Total simulation cycles |

**Methods:**

```python
def get_bandwidth_gbs(self) -> Tuple[float, float]
# Returns: (read_bandwidth, write_bandwidth) in GB/s

def get_summary(self) -> Dict
# Returns: Full performance summary dictionary
```

---

## PseudoChannel Class

```python
class PseudoChannel
```

Each physical channel has 2 pseudo-channels for doubled parallelism.

### Key Methods

```python
def activate_row(
    self,
    row: int,
    bank_group: Optional[int] = None,
    bank_id: Optional[int] = None,
) -> bool

def activate_row_in_bank_group(
    self,
    bank_group: int,
    index_in_group: int,
    row: int,
) -> bool

def precharge_all(self) -> bool
def precharge_bank(self, bank_id: int) -> bool

def can_read(self) -> bool
def can_write(self) -> bool

def refresh(self, bank_id: Optional[int] = None) -> bool
```

### State Properties

```python
state: PseudoChannelState  # IDLE, ACTIVE, REFRESHING, READING, WRITING
open_row: int              # Currently open row (-1 if none)
```

---

## BankGroup Class

```python
class BankGroup
```

HBM4 Bank Group with 2 banks each.

### Properties

```python
group_id: int              # 0-7
num_banks: int             # Number of banks (2)
last_act_cycle: int        # Last activation cycle
```

### Methods

```python
def can_activate_bank_group(self, current_cycle: Optional[int] = None) -> bool
def record_activation(self, current_cycle: Optional[int] = None)
```

---

## Command Reference

| Command | Description | Timing Constraints |
|---------|-------------|-------------------|
| ACT | Activate row | tRCD before RD/WR |
| PRE | Precharge bank | tRP before next ACT |
| PREA | Precharge all banks | Closes all banks |
| RD | Read | Row must be open |
| WR | Write | Row must be open |
| RDA | Read with auto-precharge | Precharges after RD |
| WRA | Write with auto-precharge | Precharges after WR |
| REFab | All-bank refresh | All banks must be idle |
| REFsb | Per-bank refresh | Single bank idle |

---

## Timing Parameters

### HBM4Timing (16 GT/s)

```python
tCK: 62.5 ps
tRCD: 12 cycles (750 ps)
tCL: 16 cycles (1000 ps)
tCWL: 12 cycles (750 ps)
tRP: 12 cycles (750 ps)
tRAS: 28 cycles (1750 ps)
tRC: 40 cycles (2500 ps)
tRRDS: 3 cycles
tRRDL: 4 cycles
tFAW: 16 cycles
```

---

## Usage Example

```python
from model.dram.hbm4_channel_model import HBM4Channel, HBM4ChannelArray

# Create a single channel
channel = HBM4Channel.create_with_speed_grade(0, "16Gbps")

# Basic command sequence
channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0x100)
channel.tick()  # Advance time
channel.tick()

channel.issue_command('RD', pseudo_channel=0, bank=0, row=0x100)
channel.tick()

# Get performance stats
stats = channel.get_performance_stats()
print(f"Row hit rate: {stats.row_hit_rate:.1f}%")
print(f"Average latency: {stats.average_read_latency:.1f} cycles")

# Create full channel array
channel_array = HBM4ChannelArray()

# Access specific channel
ch7 = channel_array.get_channel(7)

# System-level statistics
summary = channel_array.get_system_performance_summary()
print(f"Total reads: {summary['total_reads']}")
print(f"Total writes: {summary['total_writes']}")
```

---

## Channel Array Class

```python
class HBM4ChannelArray
```

Array of 32 HBM4 channels for system-level simulation.

### Constructor

```python
def __init__(
    self,
    spec: Optional[HBM4Spec] = None,
    timing: Optional[HBM4Timing] = None,
    use_enhanced_banks: bool = True,
)
```

### Methods

```python
def get_channel(self, channel_id: int) -> Optional[HBM4Channel]
def get_pseudo_channel(self, channel_id: int, pch_id: int) -> Optional[PseudoChannel]
def tick(self)
def validate_all_timing(self) -> List[TimingViolation]
def reset_all(self)
```

### Properties

```python
num_channels: int              # 32
total_bandwidth_gbs: float     # System bandwidth in GB/s
total_bandwidth_tbs: float     # System bandwidth in TB/s
total_banks: int               # Total banks (32 x 32 = 1024)
```

### Statistics Methods

```python
def get_system_performance_summary(self) -> Dict
def get_channel_performance(self, channel_id: int) -> Optional[Dict]
def get_system_state_summary(self) -> dict
```
