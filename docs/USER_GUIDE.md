# HBM4 User Guide

Complete user guide for the HBM4 System Modeling Platform.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Working with Channels](#working-with-channels)
- [Address Mapping](#address-mapping)
- [QoS Scheduling](#qos-scheduling)
- [Refresh Management](#refresh-management)
- [DFI Interface](#dfi-interface)
- [Performance Benchmarking](#performance-benchmarking)
- [Troubleshooting](#troubleshooting)
- [Common Patterns](#common-patterns)

---

## Quick Start

### Minimal Example

```python
from model.controller.hbm4_controller import HBM4Controller

# Create controller
controller = HBM4Controller()

# Submit a read request
request_id = controller.submit_request(
    addr=0x0001_0000_0000_0000,
    is_read=True,
    qos_level=8,  # Normal priority
)

# Run simulation
for _ in range(100):
    responses = controller.tick()
    for resp in responses:
        print(f"Completed: {resp.request_id}, latency={resp.latency}ns")

# Get statistics
stats = controller.get_stats()
print(f"Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
```

---

## Installation

### Requirements

- Python 3.8+
- NumPy (optional, for numerical operations)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/HBM.git
cd HBM

# Install dependencies
pip install -r requirements.txt

# Install as editable package (recommended)
pip install -e .

# Set PYTHONPATH (if not using editable install)
export PYTHONPATH=/path/to/HBM:$PYTHONPATH
```

### Verify Installation

```bash
# Run basic tests
pytest tests/ -v --tb=short
```

---

## Basic Usage

### Creating a Controller

```python
from model.dram.hbm4_spec import HBM4Spec
from model.controller.hbm4_controller import HBM4Controller

# Default controller (8 GT/s, 32 channels)
controller = HBM4Controller()

# Custom specification
spec = HBM4Spec(
    channels=32,
    pseudo_channels_per_channel=2,
    data_rate_gtps=16.0,  # 16 GT/s for HBM4E
)
controller = HBM4Controller(spec=spec)

# Or use speed grade presets
from model.dram.hbm4_spec import create_hbm4_spec_from_speed_grade
spec = create_hbm4_spec_from_speed_grade("16Gbps")
controller = HBM4Controller(spec=spec)
```

### Submitting Requests

```python
# Read request
request_id = controller.submit_request(
    addr=0x0001_0000_0000_0000,
    is_read=True,
    qos_level=8,  # 0-15, higher = higher priority
    size_bytes=64,
)

# Write request
request_id = controller.submit_request(
    addr=0x0002_0000_0000_0000,
    is_read=False,
    qos_level=12,  # High priority write
    size_bytes=64,
)
```

### Running Simulation

```python
# Run for fixed cycles
for _ in range(1000):
    responses = controller.tick()
    for resp in responses:
        print(f"Request {resp.request_id} completed in {resp.latency}ns")

# Run until all requests complete
while len(controller._pending_requests) > 0:
    controller.tick()

# Run with cycle limit
max_cycles = 10000
for cycle in range(max_cycles):
    controller.tick()
    if len(controller._pending_requests) == 0:
        print(f"All requests completed at cycle {cycle}")
        break
```

### Getting Statistics

```python
# Comprehensive statistics
stats = controller.get_stats()

# Controller stats
print(f"Total requests: {stats['controller']['total_requests']}")
print(f"Read/Write: {stats['controller']['read_requests']}/{stats['controller']['write_requests']}")
print(f"Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
print(f"Average latency: {stats['controller']['average_latency_ns']:.1f}ns")

# Queue stats
print(f"Read queue depth: {stats['queues']['read_depth']}")
print(f"Write queue depth: {stats['queues']['write_depth']}")

# Bandwidth
bandwidth = controller.get_bandwidth_gbs()
print(f"Effective bandwidth: {bandwidth:.2f} GB/s")
```

---

## Working with Channels

### Channel Architecture

HBM4 has 32 independent channels, each with 2 pseudo-channels:

```
HBM4 Stack
├── Channel 0
│   ├── Pseudo-channel 0 (banks 0-15)
│   └── Pseudo-channel 1 (banks 0-15)
├── Channel 1
│   ├── Pseudo-channel 0
│   └── Pseudo-channel 1
...
└── Channel 31
    ├── Pseudo-channel 0
    └── Pseudo-channel 1
```

### Direct Channel Operations

```python
from model.dram.hbm4_channel_model import HBM4ChannelArray

# Create channel array
channel_array = HBM4ChannelArray()

# Get specific channel
ch0 = channel_array.get_channel(0)

# Issue commands directly
ch0.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
ch0.tick()  # Advance time
ch0.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

# Get channel state
state = ch0.get_state_summary()
print(f"Channel state: {state['state']}")
```

### Channel-Level Statistics

```python
# Get all channel states
summary = channel_array.get_system_state_summary()
print(f"Total bandwidth: {summary['peak_bandwidth_tbs']:.2f} TB/s")

# Per-channel bandwidth
for ch in channel_array.channels[:4]:  # First 4 channels
    print(f"Channel {ch.channel_id}: {ch.peak_bandwidth_gbs:.1f} GB/s")
```

---

## Address Mapping

### Default Address Format (RBC)

HBM4 uses Row-Bank-Channel (RBC) mapping by default:

```
Address Bit Layout (48-bit):
Addr[47:46] = Stack ID (2 bits, 4 stacks)
Addr[45:41] = Channel (5 bits, 32 channels)
Addr[40]    = Pseudo-channel (1 bit, 2 per channel)
Addr[39:37] = Bank group (3 bits, 8 per pseudo-channel)
Addr[36:33] = Bank within group (4 bits, 16 per group)
Addr[32:17] = Row (16 bits, 64K per bank)
Addr[16:11] = Column (6 bits, 64 per row)
Addr[10:9]  = Burst beat (2 bits, 4-beat alignment)
Addr[8:6]   = Byte offset (3 bits, 8-byte offset)
```

### Using Address Decoder

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

# Create decoder with default RBC mapping
decoder = HBM4AddressDecoder()

# Decode an address
addr = 0x0001_2345_6789_ABC0
decoded = decoder.decode(addr)

print(f"Channel: {decoded.channel_id}")           # 0-31
print(f"Pseudo-channel: {decoded.pseudo_channel_id}")  # 0-1
print(f"Bank group: {decoded.bank_group_id}")     # 0-7
print(f"Bank: {decoded.bank_id}")                 # 0-15
print(f"Row: 0x{decoded.row_id:04X}")             # 0-65535
print(f"Column: {decoded.col_id}")                # 0-63

# Or extract individual fields directly
channel = decoder.get_channel_id(addr)
row = decoder.get_row_id(addr)
```

### Alternative Mapping Schemes

```python
# Bank-Channel-Row (maximizes bank parallelism)
decoder_bcr = HBM4AddressDecoder(mapping_scheme="bcr")

# Channel-Row-Bank (for cross-channel random access)
decoder_crb = HBM4AddressDecoder(mapping_scheme="crb")
```

### Validating Addresses

```python
# Check if address is valid
addr = 0x0001_0000_0000_0008  # Not 8-byte aligned
is_valid = decoder.validate_address(addr)  # False

addr = 0x0001_0000_0000_0000  # Properly aligned
is_valid = decoder.validate_address(addr)  # True

# Auto-alignment (decoder fixes misaligned addresses)
decoded = decoder.decode(addr)  # Automatically masks to 8-byte boundary
```

---

## QoS Scheduling

### QoS Priority Levels

| Level | Constant | Use Case |
|-------|----------|----------|
| 15 | CRITICAL | Real-time, latency-sensitive |
| 12 | HIGH | High priority traffic |
| 8 | NORMAL | Default for most traffic |
| 4 | LOW | Background, batch processing |
| 0 | IDLE | Idle/probe traffic |

### Using QoS Scheduler

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel

# Scheduler is integrated into HBM4Controller by default
controller = HBM4Controller(enable_qos=True)

# Submit requests with different priorities
controller.submit_request(addr=0x1000, is_read=True, qos_level=QoSLevel.CRITICAL)
controller.submit_request(addr=0x2000, is_read=True, qos_level=QoSLevel.LOW)
controller.submit_request(addr=0x3000, is_read=True, qos_level=QoSLevel.HIGH)

# Run - critical requests will be processed first
for _ in range(100):
    controller.tick()
```

### Configuring Bandwidth Guarantees

```python
scheduler = controller.qos_scheduler

# Set bandwidth guarantees (GB/s)
scheduler.set_bandwidth_guarantee(QoSLevel.CRITICAL, 200.0)
scheduler.set_bandwidth_guarantee(QoSLevel.HIGH, 300.0)

# Set bandwidth caps (prevents starvation)
scheduler.set_bandwidth_cap(QoSLevel.HIGH, 800.0)

# Get queue status
for level in [15, 12, 8, 4, 0]:
    size = scheduler.get_queue_size(level)
    print(f"QoS {level}: {size} requests")
```

### FR-FCFS Scheduling

Within the same QoS level, requests are scheduled using First-Ready FCFS:

1. Row hit requests first (better performance)
2. Oldest request among row misses

---

## Refresh Management

### Refresh Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| PER_BANK | Staggered per-bank refresh (default) | HBM3/HBM4 typical |
| ALL_BANKS | All banks refreshed together | Legacy compatibility |
| BANK_GROUP | Refresh by bank group | Power-sensitive |

### Using Refresh Scheduler

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

# Scheduler is integrated into HBM4Controller by default
controller = HBM4Controller(enable_refresh=True)

# Change refresh mode
controller.refresh_scheduler.set_mode(RefreshMode.PER_BANK)

# Check if refresh needed
if controller.refresh_scheduler.can_refresh():
    cmd = controller.refresh_scheduler.get_refresh_command()
    if cmd:
        cmd_name, ch, pch, bank = cmd
        print(f"Refresh: {cmd_name} ch={ch} pch={pch} bank={bank}")

# Get refresh statistics
stats = controller.refresh_scheduler.get_stats()
print(f"Total refreshes: {stats['total_refreshes']}")
```

### DRFM (Row Hammer Protection)

```python
# Enable DRFM for row-hammer mitigation
controller.refresh_scheduler.enable_drfm(enabled=True, threshold=500)

# Get banks needing refresh
at_risk_banks = controller.refresh_scheduler.get_banks_needing_refresh()
print(f"Banks at risk: {at_risk_banks}")
```

---

## DFI Interface

### DFI 5.0 Features

- Command encoding (ACT, PRE, RD, WR, REFab, REFsb)
- Control update handshake
- Frequency change protocol
- Low power state management
- Power management signals

### Basic DFI Usage

```python
from model.dram.dfi_interface import DFI5Interface, DFILowPowerState

# DFI interface is integrated into HBM4Controller by default
controller = HBM4Controller(enable_dfi=True)

# Access DFI interface directly
dfi = controller.dfi

# Encode and queue commands
req = dfi.encode_command(
    'ACT',
    {'row': 100, 'bank': 0, 'channel': 0, 'pseudo_channel': 0},
    priority=8
)
dfi.queue_request(req)

# Check DFI status
signals = dfi.get_dfi_signals()
print(f"LP state: {signals.lp_state}")
print(f"Ready: {signals.phy_ready}")
```

### Frequency Change

```python
# Request frequency change
dfi.request_freq_change(1200)  # 1.2 GHz
dfi.enter_freq_change()

# Poll for completion
while not dfi.is_freq_change_complete():
    dfi.tick()

dfi.exit_freq_change()
```

### Low Power States

```python
# Enter low power state
dfi.request_low_power(DFILowPowerState.LP_CTRL)

# Or directly
dfi.set_low_power_state(DFILowPowerState.LP_DATA)

# Wakeup
dfi.wakeup_from_low_power()
```

---

## Performance Benchmarking

### Basic Bandwidth Measurement

```python
controller = HBM4Controller()

# Submit batch of sequential requests
base_addr = 0x1000
for i in range(1000):
    addr = base_addr + (i * 64)  # 64-byte aligned
    controller.submit_request(addr=addr, is_read=True)

# Run until complete
while len(controller._pending_requests) > 0:
    controller.tick()

# Measure bandwidth
bandwidth = controller.get_bandwidth_gbs()
print(f"Effective bandwidth: {bandwidth:.2f} GB/s")
print(f"Peak bandwidth: {controller.spec.bandwidth_gbs:.0f} GB/s")
```

### Row Hit Rate Optimization

```python
# Submit requests to same row (row hits)
row_addr = 0x0001_0000_0000_0000
for i in range(100):
    addr = row_addr + (i * 64)  # Same row, different column
    controller.submit_request(addr=addr, is_read=True)

# Run simulation
while len(controller._pending_requests) > 0:
    controller.tick()

stats = controller.get_stats()
print(f"Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
```

### Multi-Channel Parallelism

```python
# Submit to different channels for parallel access
for ch in range(32):
    # Each channel gets independent requests
    addr = ((ch & 0x1F) << 41) | 0x8
    for i in range(10):
        controller.submit_request(addr=addr + (i * 64), is_read=True)

# Run - all channels operate in parallel
while len(controller._pending_requests) > 0:
    controller.tick()
```

---

## Troubleshooting

### Common Issues

#### 1. Queue Full Errors

**Symptom:** `submit_request()` returns `None`

**Cause:** Request queue is full

**Solution:**
```python
# Check queue depth before submitting
stats = controller.get_stats()
if stats['queues']['read_depth'] < 256:  # Your max depth
    controller.submit_request(...)
```

#### 2. Address Alignment Errors

**Symptom:** Address decoding returns unexpected values

**Cause:** Address not 8-byte aligned

**Solution:**
```python
# Align address to 8-byte boundary
addr = original_addr & ~0x7
controller.submit_request(addr=addr, ...)
```

#### 3. Timing Violations

**Symptom:** `can_activate()` returns `False`

**Cause:** Timing constraints not satisfied

**Solution:**
```python
# Wait for timing to resolve
while not bank.can_activate():
    channel.tick()
```

#### 4. Refresh Blocking Commands

**Symptom:** Commands not executing during refresh

**Cause:** Refresh takes priority

**Solution:**
```python
# Check refresh status before issuing commands
if not refresh_scheduler.can_refresh():
    # Safe to issue commands
    channel.issue_command(...)
```

#### 5. DFI Not Ready

**Symptom:** `dfi_ready` returns `False`

**Cause:** DFI in low power or frequency change state

**Solution:**
```python
# Wait for DFI to be ready
while not controller.dfi_ready:
    controller.tick()
```

### Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('hbm4.controller')
logger.setLevel(logging.DEBUG)

# Run simulation - detailed traces will be printed
controller = HBM4Controller()
controller.submit_request(...)
```

### Checking System State

```python
# Get comprehensive state
stats = controller.get_stats()

# Check individual components
print("Controller:", stats['controller'])
print("DFI:", stats['dfi'])
print("Refresh:", stats['refresh'])
print("QoS:", stats['qos'])

# Direct component inspection
print("Queue depth:", controller.queue_manager.read_queue.size())
print("DFI state:", controller.dfi.lp_state)
print("Refresh pending:", controller.refresh_scheduler.can_refresh())
```

---

## Common Patterns

### Pattern 1: Sequential Access (Row Hits)

```python
# Access consecutive addresses in same row
base_addr = 0x0001_0000_0000_0000
for i in range(100):
    addr = base_addr + (i * 64)
    controller.submit_request(addr=addr, is_read=True)
```

### Pattern 2: Random Access (Row Misses)

```python
import random

# Random addresses across many rows
for i in range(100):
    row = random.randint(0, 65535)
    addr = ((row & 0xFFFF) << 17) | ((i % 32) << 41)
    controller.submit_request(addr=addr, is_read=True)
```

### Pattern 3: Priority Traffic

```python
# Critical request interrupts normal traffic
controller.submit_request(addr=0x1000, is_read=True, qos_level=4)  # Low first
controller.submit_request(addr=0x2000, is_read=True, qos_level=8)  # Normal

# Critical request inserted
controller.submit_request(addr=0x3000, is_read=True, qos_level=15)  # Critical

controller.submit_request(addr=0x4000, is_read=True, qos_level=4)  # Low
# Critical (0x3000) will be processed first!
```

### Pattern 4: Write-Back Cache

```python
# Batch writes with high priority
write_buffer = []
for i in range(1000):
    addr = 0x1000 + (i * 64)
    request_id = controller.submit_request(
        addr=addr,
        is_read=False,
        qos_level=12  # High priority for writes
    )
    write_buffer.append(request_id)

# Wait for all writes to complete
while len(controller._pending_requests) > 0:
    controller.tick()
```

### Pattern 5: Channel Striping

```python
# Distribute requests across channels evenly
num_requests = 1000
for i in range(num_requests):
    channel = i % 32
    addr = ((channel & 0x1F) << 41) | ((i // 32) << 6)
    controller.submit_request(addr=addr, is_read=True)
```

---

## Performance Tips

1. **Batch requests** - Submit multiple requests before running simulation
2. **Use row hits** - Organize addresses to maximize row buffer hits
3. **Parallel channels** - Distribute traffic across all 32 channels
4. **QoS for critical traffic** - Use high QoS for latency-sensitive requests
5. **Disable unused features** - Turn off QoS/refresh/DFI if not needed:

```python
controller = HBM4Controller(
    enable_qos=False,     # Faster if no priority needed
    enable_refresh=False,  # Faster if no refresh simulation
    enable_dfi=False,     # Faster if no DFI interface needed
)
```

---

## Examples

See the `examples/` directory for working examples:

- `basic_controller.py` - Simple read/write operations
- `multi_channel.py` - Multi-channel parallelism
- `qos_scheduling.py` - Priority-based scheduling
- `refresh_scheduling.py` - Refresh management
- `bandwidth_benchmark.py` - Performance benchmarking
- `dfi_interface.py` - DFI protocol usage
- `address_decoding.py` - Address mapping examples
- `dram_features.py` - DRAM timing and features