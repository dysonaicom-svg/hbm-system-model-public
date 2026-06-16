# HBM4 Library Separation

This document defines the separation between public libraries and internal components for the HBM4 project.

---

## Public Library 1: hbm4-model

**Purpose:** Core HBM4 memory modeling library

### Contents

| Directory | Description |
|-----------|-------------|
| `model/dram/` | DRAM models (spec, timing, channel, bank, power, ecc, crc, repair) |
| `model/controller/` | Controller models (address decoder, QoS scheduler, refresh scheduler, sequencer) |
| `model/phy/` | PHY models (training, signals, DFI interface) |
| `model/traffic/` | Traffic generator |
| `model/interconnect/` | Interconnect models (AXI bridge) |
| `model/hbm4/` | HBM4 specific implementations |
| `model/__init__.py` | Public API only (exports only public interfaces) |

### Excluded from hbm4-model

| File/Directory | Reason |
|----------------|--------|
| `model/multi_channel.py` | Project-specific multi-channel aggregation |
| `model/rtl_verification.py` | Project-specific RTL verification integration |

---

## Public Library 2: hbm4-sim

**Purpose:** HBM4 simulation and benchmarking framework

### Contents

| Directory | Description |
|-----------|-------------|
| `sim/` | Core simulator, unified simulator, benchmark runner |
| `sim/interconnect/` | AXI bridge, gem5 bridge |
| `sim/trace/` | Trace parser and reader |
| `sim/visualization/` | Charts, histograms, performance visualization |
| `examples/` | All usage examples (bandwidth benchmark, QoS scheduling, etc.) |

### Key Files

| File | Description |
|------|-------------|
| `sim/simulator.py` | Core simulation engine |
| `sim/unified_simulator.py` | RTL-Python co-simulation |
| `sim/benchmark.py` | Performance benchmarking |
| `sim/trace/parser.py` | Memory trace parsing |
| `sim/visualization/` | Result visualization tools |

---

## Internal (Private)

The following components are internal to the HBM4 project and are not intended for public distribution.

| Directory | Purpose |
|-----------|---------|
| `rtl/` | RTL source code (SystemVerilog) |
| `verification/` | UVM verification environment |
| `tests/` | Complete test suite |
| `integration/` | gem5 integration |
| `config/` | Configuration files |
| `scripts/` | Utility scripts |
| `docs/` | Documentation |
| `research/` | Research materials (ramulator2) |

### Internal Details

| Component | Description |
|-----------|-------------|
| `rtl/` | HBM controller RTL, types, testbench |
| `verification/uvm/` | UVM environment, tests, coverage |
| `tests/` | Unit tests, integration tests, regression |
| `config/` | Project configuration |
| `scripts/` | Build, run, comparison scripts |

---

## Distribution Structure

```
hbm4-model/           hbm4-sim/            (Internal - Not Distributed)
├── model/            ├── sim/             ├── rtl/
│   ├── dram/        │   ├── interconnect/ ├── verification/
│   ├── controller/  │   ├── trace/        ├── tests/
│   ├── phy/         │   ├── visualization/ ├── integration/
│   ├── traffic/     │   └── examples/    ├── config/
│   ├── interconnect/├── __init__.py       ├── scripts/
│   ├── hbm4/        └── README.md         ├── docs/
│   └── __init__.py                      └── research/
└── README.md
```

---

## Version Compatibility

| Library | Min Python | Dependencies |
|---------|------------|---------------|
| hbm4-model | 3.10 | numpy, scipy |
| hbm4-sim | 3.10 | hbm4-model, matplotlib, pandas |

---

## Usage Example

```python
# hbm4-model usage
from hbm4_model import HBM4Controller, HBM4Channel, HBM4TimingSpec

# hbm4-sim usage
from hbm4_sim import Simulator, Benchmark, TraceParser
```