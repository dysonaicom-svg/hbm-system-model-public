# HBM System Modeling Platform - Release Notes

## Version 1.0.0

**Release Date:** June 16, 2026

Welcome to HBM System Modeling Platform v1.0.0! This release represents a complete, production-ready HBM4 memory system modeling platform with full Python/RTL co-simulation capabilities.

---

## What's New in 1.0.0

### Core Architecture
- **32-channel architecture** (2x HBM3 channel count)
- **Pseudo-channel support** (64 total pseudo-channels)
- **Speed grades:** 8 Gbps, 12 Gbps, 16 Gbps
- **2048-bit I/O width** with 2 TB/s peak bandwidth
- **8 bank groups, 16 banks per group** organization

### Controller Components (Phase A)
- Complete HBM4 controller with integrated components
- Multi-scheme address decoder (RBC/BCR/CRB mapping)
- 16-level QoS scheduler with anti-starvation
- Flexible refresh scheduler (all-bank, per-bank, DRFM)
- Request queue management

### DRAM Model (Phase B)
- Complete HBM4 specification implementation
- Per-bank state machine with full timing compliance
- DFI 5.0/5.1 interface protocol
- PHY training and calibration sequences
- Lane repair and ECC/CRC error handling
- Power estimation and MBIST support

### RTL & Verification (Phase C-D)
- Complete SystemVerilog RTL implementation
- UVM verification environment
- Python-RTL co-simulation framework
- Functional coverage collection

### Testing & Quality
- **2,849 tests** across all categories - all passing
- CI/CD pipeline with GitHub Actions
- Comprehensive benchmark suite
- 9 example scripts for common use cases

---

## Installation Instructions

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Standard Installation
```bash
pip install hbm
```

### Development Installation
```bash
git clone https://github.com/anthropic/hbm.git
cd hbm
pip install -e .
```

### From Source
```bash
python3 -m pip install -e .
```

---

## Quick Example

### Basic Controller Usage
```python
from model.controller.hbm4_controller import HBM4Controller
from model.controller.request import Request, RequestType

# Create controller
controller = HBM4Controller()

# Submit a read request
request = Request(
    request_id=1,
    request_type=RequestType.READ,
    address=0x1000,
    size=64,
    priority=8
)
controller.submit_request(request)

# Process cycles and get response
controller.process_cycles(100)
response = controller.get_completed_response(1)
print(f"Response status: {response.status}")
```

### Address Decoding
```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

decoder = HBM4AddressDecoder(mapping_scheme="rbc")
decoded = decoder.decode_address(0x10000)
print(f"Channel: {decoded.channel}, Bank: {decoded.bank}")
```

### Multi-Channel Simulation
```python
from model.multi_channel import HBM4MultiChannel

mcp = HBM4MultiChannel(num_channels=32)
mcp.submit_request(channel=0, address=0x1000, size=64)
mcp.process_cycles(100)
```

---

## Requirements

### Python Dependencies
```
- numpy >= 1.21.0
- scipy >= 1.7.0
- matplotlib >= 3.5.0 (optional, for visualization)
```

### System Requirements
- Python 3.10+
- Linux/macOS/Windows
- 4GB RAM minimum
- 100MB disk space

### Optional Dependencies
- verilator (for RTL simulation)
- iverilog (for Verilog linting)
- pytest (for running tests)

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Peak Bandwidth | 2 TB/s |
| Channels | 32 |
| Speed Grades | 8/12/16 Gbps |
| Row Buffer | 2KB |
| Test Coverage | 2,849 tests |

---

## Known Limitations

1. **Lane repair** requires calibration data to be set before operation
2. **DRAM initialization** must be completed before requests are processed
3. **RTL simulation** requires verilator or compatible SystemVerilog simulator

---

## Documentation

- [README.md](README.md) - Complete project documentation
- [EXAMPLES.md](EXAMPLES.md) - 9 comprehensive usage examples
- [docs/design/](docs/design/) - Design specifications
- [docs/specs/](docs/specs/) - Memory specifications

---

## Support

### Reporting Issues
Please report bugs via GitHub Issues with:
- Python/RTL version
- Minimal reproduction case
- Expected vs actual behavior

### Getting Help
- Check [EXAMPLES.md](EXAMPLES.md) for usage patterns
- Review [docs/design/](docs/design/) for architecture details
- Run `pytest tests/ -v` to verify installation

---

## License

Copyright 2026 Anthropic. All rights reserved.

---

## Release History

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | 2026-06-16 | Current |
| 0.9.0 | 2026-06-15 | Previous |