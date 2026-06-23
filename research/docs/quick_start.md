# HBM4 Logic Base Die - Quick Start Guide

Quick reference for setting up and running the HBM4 logic-base-die simulation platform.

## Prerequisites

- Python 3.8+
- pip package manager

## Installation

```bash
# Navigate to the research directory
cd /home/ic/JXTF/HBM/research/hbm4-logic-base-die

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
hbm4-logic-base-die/
├── model/
│   ├── controller/      # HBM4 controller, address decoder, schedulers
│   ├── dram/           # DRAM timing model, DFI interface, channel model
│   └── hbm4/           # Power/Thermal estimation, TSV PHY
├── tests/
│   ├── controller/      # Controller unit tests
│   ├── dram/           # DRAM model tests
│   └── hbm4/           # Integration tests
├── docs/               # Architecture, workload analysis, migration plans
└── implementation/     # Implementation roadmap
```

## Quick Test Commands

### Run All Tests

```bash
python -m pytest tests/hbm4/ -v
```

### Run Specific Test Suites

```bash
# Controller tests
python -m pytest tests/controller/test_hbm4*.py -v

# DRAM model tests
python -m pytest tests/dram/test_hbm4*.py -v

# DFI interface tests
python -m pytest tests/dram/test_dfi_interface.py -v

# Lane repair tests
python -m pytest tests/hbm4/test_lane_repair.py -v

# Power estimator tests
python -m pytest tests/hbm4/test_power_estimator.py -v

# Thermal model tests
python -m pytest tests/hbm4/test_thermal_model.py -v

# TSV PHY tests
python -m pytest tests/hbm4/test_tsv_phy.py -v
```

### Run Quick Smoke Test

```bash
python -m pytest tests/hbm4/ tests/controller/test_hbm4*.py tests/dram/test_hbm4*.py tests/dram/test_dfi_interface.py -v
```

## Key Modules

### Core Models

| Module | Purpose |
|--------|---------|
| `HBM4Spec` | HBM4 specification constants, speed bins |
| `HBM4AddressDecoder` | Address mapping across 32 channels |
| `HBM4Controller` | Memory controller implementation |
| `HBM4QoSScheduler` | QoS-aware command scheduling |
| `HBM4RefreshScheduler` | Refresh scheduling for reliability |

### DRAM Models

| Module | Purpose |
|--------|---------|
| `DFIInterface` | DFI protocol interface |
| `HBM4ChannelModel` | Per-channel DRAM timing |
| `LaneRepair` | Lane repair mapping |
| `TSVPHY` | TSV PHY modeling |

### Power/Thermal

| Module | Purpose |
|--------|---------|
| `PowerEstimator` | Power consumption estimation |
| `ThermalModel` | Thermal simulation |

## Usage Examples

### Basic Controller Usage

```python
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_channel_model import HBM4ChannelModel

# Create channel model
channel = HBM4ChannelModel(channel_id=0)

# Create controller
controller = HBM4Controller(channels=[channel])

# Issue request
request = {
    'address': 0x1000,
    'command': 'READ',
    'length': 64,
    'qos': 7
}
response = controller.submit_request(request)
```

### Address Decoding

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

decoder = HBM4AddressDecoder()
result = decoder.decode(address=0xDEADBEEF)

# Access decoded fields
channel_id = result['channel']
pseudo_channel = result['pseudo_channel']
bank_group = result['bank_group']
bank = result['bank']
row = result['row']
column = result['column']
```

## Workload Profiles

| Profile | Use Case | Read/Write Ratio | Row Hit Rate |
|---------|----------|------------------|--------------|
| A | AI Training | 60:40 | 45% |
| B | AI Inference | 90:10 | 75% |
| C | Synthetic | 50:50 | 25% |

## Key Parameters (8 Gb/s Speed Bin)

| Parameter | Value |
|-----------|-------|
| Peak bandwidth per channel | 32 GB/s |
| Total bandwidth (32 channels) | 1024 GB/s |
| DQ width per pseudo-channel | 64 bits |
| tCK | 1.25 ns |
| tRRD_S | 4 cycles |
| tRRD_L | 6 cycles |
| tFAW | 16 cycles |

## Architecture Overview

See [architecture.md](architecture.md) for detailed system architecture.

## Migration to RTL/UVM

See [sv_uvm_migration_plan.md](sv_uvm_migration_plan.md) for RTL migration roadmap.

## Troubleshooting

### Import Errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Test Failures

Run tests with verbose output to identify issues:
```bash
python -m pytest tests/ -v --tb=short
```

### Performance Issues

For large simulations, consider running tests in parallel:
```bash
python -m pytest tests/ -v -n auto
```

## References

- [JEDEC HBM4 (JESD270-4A)](https://www.jedec.org/standards-documents/docs/jesd270-4a)
- [Synopsys HBM4 Controller IP](https://www.synopsys.com/designware-ip/interface-ip/hbm/hbm4-controller.html)
- [Cadence HBM4E PHY](https://www.cadence.com/en_US/home/tools/silicon-solutions/design-ip/memory-interface-and-storage-ip/hbm-phy/hbm4e.html)