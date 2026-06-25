# API Documentation

This directory contains API documentation for the HBM4 System Modeling Platform.

## Structure

```
api/
├── controller/    # Controller API
│   ├── README.md
│   └── hbm4_controller.md
├── dram/          # DRAM model API
│   ├── README.md
│   ├── channel_model.md
│   └── dfi_interface.md
├── phy/           # PHY API
├── sim/           # Simulator API
│   ├── README.md
│   ├── simulator.md
│   └── unified_simulator.md
└── README.md      # This file
```

## Components

### Controller API
- [HBM4Controller](controller/hbm4_controller.md) - Main controller API

### DRAM API
- [HBM4Channel](dram/channel_model.md) - Channel model API
- [DFI 5.0 Interface](dram/dfi_interface.md) - DFI protocol API

### Simulator API
- [HBMSimulator](sim/simulator.md) - Basic simulator API
- [HBM4UnifiedSimulator](sim/unified_simulator.md) - Unified simulator API

## Quick Reference

### Controller
```python
from model.controller.hbm4_controller import HBM4Controller

controller = HBM4Controller(spec=spec)
controller.submit_request(addr=0x1000, is_read=True)
controller.tick()
```

### Channel Model
```python
from model.dram.hbm4_channel_model import HBM4Channel

channel = HBM4Channel.create_with_speed_grade(0, "16Gbps")
channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0x100)
```

### DFI Interface
```python
from model.dram.dfi_interface import DFI5Interface

dfi = DFI5Interface()
dfi.encode_command('ACT', {'row': 0x100, 'bank': 0})
```

### Unified Simulator
```python
from sim.hbm4_unified_simulator import HBM4UnifiedSimulator, SimulationConfig

config = SimulationConfig(mode=SimulationMode.FULL, num_channels=32)
simulator = HBM4UnifiedSimulator(config)
simulator.run()
```

## Related Documentation

- [Architecture](../architecture/) - System architecture
- [User Guide](../user-guide/) - Usage guide
- [Quick Reference](../QUICKREF.md) - Command reference
