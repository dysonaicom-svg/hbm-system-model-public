# Controller API Reference

This directory contains API documentation for the HBM Controller module.

## Overview

The controller module provides the HBM memory controller functionality including:
- Address decoding (HBM3 and HBM4)
- Request queuing and scheduling
- QoS-based priority management
- Refresh scheduling

## Key Classes

### HBM4Controller

Main controller integration class for HBM4 memory systems.

```python
from model.controller.hbm4_controller import HBM4Controller

# Create controller
controller = HBM4Controller()

# Submit a request
request_id = controller.submit_request(
    addr=0x0001_0000_0000_0000,
    is_read=True,
    qos_level=8,
    size_bytes=64,
)

# Run simulation cycles
responses = controller.tick()

# Get statistics
stats = controller.get_stats()
```

#### Methods

| Method | Description |
|--------|-------------|
| `submit_request(addr, is_read, qos_level, size_bytes)` | Submit a memory request |
| `tick()` | Execute one simulation cycle |
| `get_stats()` | Get controller statistics |
| `get_bandwidth_gbs()` | Get current bandwidth in GB/s |
| `trigger_training(channel_id)` | Trigger PHY training |

#### Statistics

The `get_stats()` method returns a dictionary with:
- `controller`: Request counts, row hit rate, average latency
- `spec`: HBM4 specification parameters
- `queues`: Queue depth information
- `qos`: QoS configuration (if enabled)
- `refresh`: Refresh mode and status
- `dfi`: DFI interface status

### HBM4AddressDecoder

32-channel address decoder for HBM4.

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

decoder = HBM4AddressDecoder(spec=HBM4Spec())
decoded = decoder.decode(0x0001_0000_0000_0000)
```

#### Methods

| Method | Description |
|--------|-------------|
| `decode(addr)` | Decode 64-bit address to channel/bank/row |
| `encode(stack_id, channel_id, pseudo_channel, bank_id, row_id, col_id)` | Encode components to address |
| `get_channel(addr)` | Extract channel from address |
| `get_bank(addr)` | Extract bank from address |

### HBM4QoSScheduler

16-level QoS scheduler with bandwidth guarantees.

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel

scheduler = HBM4QoSScheduler(config=spec)

# Select next request based on priority
selected = scheduler.select_next(request_list)
```

#### QoS Levels

| Level | Name | Use Case |
|-------|------|---------|
| 15 | CRITICAL | Real-time/critical tasks |
| 12 | HIGH | AI inference |
| 8 | NORMAL | General compute |
| 4 | LOW | Batch processing |
| 0 | IDLE | Background tasks |

### HBM4RefreshScheduler

Refresh scheduling for HBM4 with multiple modes.

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

scheduler = HBM4RefreshScheduler(config=spec)
scheduler.set_mode(RefreshMode.ALL_BANK)

# Check if refresh needed
if scheduler.can_refresh():
    cmd = scheduler.get_refresh_command()
```

#### Refresh Modes

| Mode | Description |
|------|-------------|
| `ALL_BANK` | Refresh all banks each interval |
| `PER_BANK` | Staggered per-bank refresh |
| `AUTONOMOUS` | Hardware-controlled refresh |
| `DRFM` | Direct Refresh Management for row-hammer |

### QueueManager

Request queue management with per-channel queuing.

```python
from model.controller.queue import QueueManager

queue_mgr = QueueManager.create(queue_depth=256)

# Push requests
queue_mgr.push_read(request)
queue_mgr.push_write(request)

# Get queue status
stats = queue_mgr.get_stats()
```

---

## Configuration

### HBMConfig

```python
from model.controller.config import HBMConfig, HBM4_DEFAULT

config = HBMConfig(
    stack_count=2,
    channels_per_stack=32,
    banks_per_channel=16,
    queue_depth=256,
    scheduler_mode="qos",
)
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `stack_count` | 2 | Number of HBM stacks |
| `channels_per_stack` | 32 (HBM4), 8 (HBM3) | Channels per stack |
| `pseudo_channels_per_channel` | 2 | Pseudo-channels per channel |
| `banks_per_channel` | 16 | Banks per channel |
| `queue_depth` | 256 | Maximum queue depth |
| `scheduler_mode` | "qos" | "qos" or "fr-fcfs" |

---

## File Structure

```
docs/api/controller/
├── README.md           # This file
├── hbm4_controller.md  # HBM4Controller API
├── address_decoder.md  # Address decoder API
├── qos_scheduler.md    # QoS scheduler API
└── refresh_scheduler.md # Refresh scheduler API
```