# HBM4 System Modeling Platform - User Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Configuration](#configuration)
5. [Simulation Modes](#simulation-modes)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 5-Minute Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/dysonaicom-svg/hbm-system-model-public.git
cd hbm-system-model-public

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run a quick simulation
python -m sim.hbm4_unified_simulator --mode quick --channels 8

# 4. Run tests
pytest tests/ -v

# 5. Run benchmark
python -m sim.benchmark
```

---

## Installation

### Prerequisites

- Python 3.8+
- pip
- (Optional) Verilator for RTL simulation

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Optional: RTL Simulation Setup

```bash
# Install Verilator
sudo apt-get install verilator

# Build RTL modules
cd rtl
verilator --cc --trace \
    --top-module hbm_controller_tb \
    hbm_controller_tb.sv hbm_controller.sv hbm_types.svh hbm_pkg.sv \
    -CFLAGS "-DVM_TRACE_FMT_VCD"
```

---

## Basic Usage

### Running Simulations

#### Quick Functional Test

```bash
python -m sim.hbm4_unified_simulator --mode quick
```

#### Full Timing Simulation

```bash
python -m sim.hbm4_unified_simulator --mode full --channels 32 --cycles 10000
```

#### Performance Benchmark

```bash
python -m sim.benchmark
```

### Using the Python API

#### Basic Controller Usage

```python
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import HBM4Spec

# Create controller
spec = HBM4Spec()
controller = HBM4Controller(spec=spec, enable_qos=True)

# Submit requests
request_id = controller.submit_request(
    addr=0x0001_0000_0000_0000,
    is_read=True,
    qos_level=8,
    size_bytes=64,
)

# Run simulation
for _ in range(10000):
    responses = controller.tick()
    for resp in responses:
        print(f"Completed: {resp.request_id}")
```

#### Channel Model Usage

```python
from model.dram.hbm4_channel_model import HBM4Channel

# Create channel
channel = HBM4Channel.create_with_speed_grade(0, "16Gbps")

# Issue commands
channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0x100)
channel.tick()
channel.issue_command('RD', pseudo_channel=0, bank=0, row=0x100)

# Get statistics
stats = channel.get_performance_stats()
print(f"Row hit rate: {stats.row_hit_rate:.1f}%")
```

#### DFI Interface Usage

```python
from model.dram.dfi_interface import DFI5Interface

# Create DFI interface
dfi = DFI5Interface()

# Encode and queue commands
dfi_req = dfi.encode_command(
    cmd='ACT',
    addr_vec={'row': 0x100, 'bank': 0, 'channel': 0},
    priority=8,
)
dfi.queue_request(dfi_req)

# Process commands
for _ in range(1000):
    dfi.tick()
```

---

## Configuration

### Simulation Configuration

```python
@dataclass
class SimulationConfig:
    mode: SimulationMode = SimulationMode.QUICK
    num_channels: int = 32
    cycles: int = 1000
    enable_pam3: bool = True
    enable_ecc: bool = True
    enable_lane_repair: bool = True
    trace_commands: bool = False
    verbose: bool = False
    speed_grade: str = "8Gbps"
```

### HBM4 Speed Grades

| Speed Grade | Data Rate | Peak Bandwidth/Channel | Peak Bandwidth/Stack |
|-------------|-----------|----------------------|---------------------|
| 8 Gbps | 8 GT/s | 64 GB/s | 2.048 TB/s |
| 12 Gbps | 12 GT/s | 96 GB/s | 3.072 TB/s |
| 16 Gbps | 16 GT/s | 128 GB/s | 4.096 TB/s |

### QoS Configuration

```python
from model.controller.qos_scheduler import QoSLevel

# QoS levels: 0-15 (higher = higher priority)
request_id = controller.submit_request(
    addr=0x1000,
    is_read=True,
    qos_level=15,  # Maximum priority
)
```

### Traffic Patterns

```python
from sim.simulator import TrafficPattern

config = SimulationConfig(
    traffic_pattern=TrafficPattern.RANDOM,  # Random access
    traffic_pattern=TrafficPattern.SEQUENTIAL,  # Sequential access
    traffic_pattern=TrafficPattern.STRIDE,  # Strided access
    traffic_pattern=TrafficPattern.HOT_SPOT,  # 80% hot spot
)
```

---

## Simulation Modes

### Mode Comparison

| Mode | Description | Use Case |
|------|-------------|----------|
| QUICK | Fast functional test | Smoke testing |
| FULL | Complete timing simulation | Performance analysis |
| STRESS | All channels at maximum load | Stress testing |
| BENCHMARK | Performance measurement | Throughput/latency |

### Choosing a Mode

**QUICK Mode:**
- 1000 cycles
- 4 channels
- Fast validation

**FULL Mode:**
- Configurable cycles (default 1000)
- All 32 channels
- Complete timing model

**STRESS Mode:**
- Maximum channel utilization
- Parallel activation
- Queue depth testing

**BENCHMARK Mode:**
- PAM3 encoding benchmark
- Channel operation benchmark
- Performance metrics

---

## Examples

### Example 1: Basic Read/Write

```python
from model.controller.hbm4_controller import HBM4Controller

controller = HBM4Controller()

# Submit write
controller.submit_request(
    addr=0x1000,
    is_read=False,
    data=0xDEADBEEF,
)

# Submit read
request_id = controller.submit_request(
    addr=0x1000,
    is_read=True,
)

# Run until completion
for _ in range(1000):
    responses = controller.tick()
    for resp in responses:
        if resp.request_id == request_id:
            print(f"Read completed: {resp.data}")
```

### Example 2: Multi-Channel Traffic

```python
from sim.hbm4_unified_simulator import (
    HBM4UnifiedSimulator,
    SimulationConfig,
    SimulationMode,
)

config = SimulationConfig(
    mode=SimulationMode.FULL,
    num_channels=32,
    cycles=10000,
)

simulator = HBM4UnifiedSimulator(config)
simulator.initialize()

# Distribute traffic across channels
for i in range(32):
    simulator.process_command(
        channel=i,
        command='ACT',
        address=0x1000 + i,
    )

# Run simulation
stats = simulator.run()

print(f"Total commands: {stats.commands_processed}")
print(f"Throughput: {stats.throughput:.0f} cmd/s")
```

### Example 3: RTL Co-Simulation

```python
from sim.hbm4_unified_simulator import (
    HBM4UnifiedSimulator,
    SimulationConfig,
)

config = SimulationConfig(mode=SimulationMode.FULL)
simulator = HBM4UnifiedSimulator(config)

# Enable RTL co-simulation
simulator.enable_rtl_cosimulation(
    enable_rtl=True,
    compare_results=True,
)

# Run with RTL comparison
stats = simulator.run()

print(f"RTL match rate: {stats.rtl_match_rate:.2%}")
```

### Example 4: Performance Analysis

```python
from sim.benchmark import run_benchmark

# Run comprehensive benchmark
results = run_benchmark(
    patterns=['random', 'sequential', 'stride'],
    channels=[8, 16, 32],
)

# Analyze results
for pattern, pattern_results in results.items():
    for channels, stats in pattern_results.items():
        print(f"{pattern} @ {channels}ch: "
              f"{stats.throughput:.1f} GB/s, "
              f"{stats.latency:.1f} ns")
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:** `ModuleNotFoundError: No module named 'model'`

**Solution:** Ensure you're running from the project root:
```bash
cd /path/to/HBM4
python -m sim.hbm4_unified_simulator
```

#### 2. Test Failures

**Problem:** Tests failing with assertion errors

**Solution:** Run tests with verbose output:
```bash
pytest tests/ -v --tb=short
```

#### 3. RTL Simulation Issues

**Problem:** Verilator build fails

**Solution:** Check Verilator installation and build:
```bash
verilator --version
cd rtl && verilator --cc --trace hbm_controller.sv
```

#### 4. Performance Issues

**Problem:** Simulation is slow

**Solution:** Use QUICK mode or reduce channels:
```bash
python -m sim.hbm4_unified_simulator --mode quick --channels 8
```

### Debug Mode

Enable verbose output for debugging:
```bash
python -m sim.hbm4_unified_simulator --mode full --verbose --trace
```

### Getting Help

- Check `docs/QUICKREF.md` for command reference
- Check `docs/API.md` for API documentation
- Run `python -m sim.hbm4_unified_simulator --help`
