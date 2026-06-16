# Simulator API Reference

This directory contains API documentation for the HBM system simulator.

## Overview

The simulator module provides end-to-end simulation framework integrating:
- Traffic generation
- HBM controller scheduling
- DRAM command sequencing and execution
- Multi-channel load balancing
- Performance statistics

## Key Classes

### HBMSimulator

Main simulation engine with cycle-accurate modeling.

```python
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

config = SimulationConfig(
    simulation_time_us=100.0,
    traffic_pattern=TrafficPattern.RANDOM,
    request_rate=0.5,
)

sim = HBMSimulator(config)
stats = sim.run()
```

### SimulationConfig

Configuration for simulation parameters.

```python
from sim.simulator import SimulationConfig, TrafficPattern

config = SimulationConfig(
    clock_freq_hz=1.28e9,      # 1.28 GHz
    simulation_time_us=100.0,  # 100 us
    traffic_pattern=TrafficPattern.RANDOM,
    request_rate=0.5,          # 50% request rate
    read_ratio=0.7,            # 70% reads
    max_requests_per_cycle=4,  # Multi-channel parallelism
)
```

### SimulationStats

Simulation statistics and metrics.

```python
stats = sim.get_stats()
print(f"Throughput: {stats.throughput_gbps:.2f} GB/s")
print(f"Row hit rate: {stats.row_hit_rate:.2%}")
print(f"Efficiency: {stats.efficiency:.2%}")
```

---

## File Structure

```
docs/api/sim/
├── README.md           # This file
├── simulator.md        # HBMSimulator API
├── traffic_generator.md # Traffic generator API
└── statistics.md       # Statistics API
```