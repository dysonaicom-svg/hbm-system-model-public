# DRAM Model API Reference

This directory contains API documentation for the HBM DRAM model module.

## Overview

The DRAM model module provides:
- Channel-level DRAM modeling (HBM3/HBM4)
- Bank state machine with full timing compliance
- DFI 5.0 interface for controller-PHY communication
- ECC/CRC error detection and correction
- Lane repair for redundancy

## Key Classes

### DRAMModel

Complete HBM DRAM model integrating stack, channel, and bank structure.

```python
from model.dram.dram_model import DRAMModel

# Create model
dram = DRAMModel(
    hbm_version="hbm4",
    stack_count=2,
    banks_per_channel=16,
)

# Execute commands
resp = dram.execute_activate(
    stack_id=0, channel_id=0, bank_id=0,
    row_id=0x100, current_time=0
)
```

### HBM4ChannelArray

Array of 32 independent HBM4 channels.

```python
from model.dram.hbm4_channel_model import HBM4ChannelArray, HBM4Channel

channels = HBM4ChannelArray(spec=HBM4Spec())

# Get specific channel
ch = channels.get_channel(channel_id=0)

# Issue command
ch.issue_command('ACT', pseudo_channel=0, bank=0, row=0x100)
```

### HBM4Channel

Single HBM4 channel with 2 pseudo-channels.

```python
from model.dram.hbm4_channel_model import HBM4Channel

channel = HBM4Channel(channel_id=0, spec=HBM4Spec())

# Issue commands
channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0x100)
channel.issue_command('RD', pseudo_channel=0, bank=0, row=0x100, col=0)
```

### DFI5Interface

DFI 5.0/5.1 interface for controller-PHY communication.

```python
from model.dram.dfi_interface import DFI5Interface, DFICommand, DFILowPowerState

dfi = DFI5Interface()

# Queue request
dfi_req = dfi.encode_command('ACT', {'row': 0x100, 'bank': 0}, priority=8)
dfi.queue_request(dfi_req)

# Check status
ready = dfi.is_ready()
stats = dfi.get_statistics()
```

---

## File Structure

```
docs/api/dram/
├── README.md              # This file
├── dram_model.md          # DRAMModel API
├── hbm4_channel_model.md  # Channel model API
└── dfi_interface.md       # DFI interface API
```