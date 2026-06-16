# Getting Started with HBM Simulation

This tutorial covers the basics of using the HBM System Modeling Platform.

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Basic Concepts

### HBM Architecture Overview

The HBM System Modeling Platform simulates High Bandwidth Memory (HBM) with:

- **HBM3**: 8 channels per stack, 64 pseudo-channels total
- **HBM4**: 32 channels per stack, 64 pseudo-channels total
- **Pseudo-channels**: 2 per channel, share data bus
- **Bank Groups**: 4 (HBM3) or 8 (HBM4) per pseudo-channel
- **Banks**: 16 per pseudo-channel

### Address Mapping

HBM uses a fixed address mapping:
```
Address = [Stack:bits][Channel:bits][BankGroup:bits][Bank:bits][Row:bits][Col:bits]
```

## Quick Start Examples

### Example 1: Simple Read/Write

```python
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import HBM4Spec

# Create HBM4 specification
spec = HBM4Spec()

# Create controller
controller = HBM4Controller(spec=spec)

# Submit a read request
request_id = controller.submit_request(
    addr=0x0001_0000_0000_0000,
    is_read=True,
    qos_level=8,
    size_bytes=64,
)

# Run simulation for 1000 cycles
for cycle in range(1000):
    responses = controller.tick()
    for resp in responses:
        print(f"Request {resp.request_id} completed in {resp.latency_ns} ns")

# Get statistics
stats = controller.get_stats()
print(f"Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
```

### Example 2: Multi-Channel Traffic

```python
from model.multi_channel import ChannelSelector, MultiChannelTrafficGenerator

# Create channel selector
selector = ChannelSelector(
    num_channels=32,
    strategy=ChannelSelector.ROUND_ROBIN
)

# Create traffic generator
traffic_gen = MultiChannelTrafficGenerator(
    config=config,
    num_channels=32,
    channel_selector=selector
)

# Generate burst of requests
requests = traffic_gen.generate_burst(count=100)

# Process requests
for req in requests:
    controller.submit_request(
        addr=req.address,
        is_read=req.is_read,
        qos_level=req.qos,
    )
```

### Example 3: Using the Simulator

```python
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

# Create simulation configuration
config = SimulationConfig(
    clock_freq_hz=1.28e9,
    simulation_time_us=100.0,
    traffic_pattern=TrafficPattern.RANDOM,
    request_rate=0.5,
    read_ratio=0.7,
    max_requests_per_cycle=4,
)

# Create and run simulator
sim = HBMSimulator(config)
stats = sim.run()

# Print results
print(f"Throughput: {stats.throughput_gbps:.2f} GB/s")
print(f"Average latency: {stats.avg_latency_ns:.2f} ns")
print(f"Row hit rate: {stats.row_hit_rate:.2%}")
print(f"Efficiency: {stats.efficiency:.2%}")
```

## Understanding Simulation Output

### Response Object

When requests complete, you receive `HBMResponse` objects:

```python
@dataclass
class HBMResponse:
    request_id: int
    is_read: bool
    completion_time: int
    latency_ns: float
    data: Optional[bytes] = None
    error: Optional[str] = None
```

### Statistics Dictionary

The `get_stats()` method returns:

```python
{
    'controller': {
        'total_requests': 1000,
        'read_requests': 700,
        'write_requests': 300,
        'row_hit_rate': 0.75,
        'average_latency_ns': 50.5,
    },
    'queues': {
        'read_queue_depth': 5,
        'write_queue_depth': 3,
    },
    'spec': { ... },  # HBM specification parameters
}
```

## Common Use Cases

### Use Case 1: Performance Benchmarking

```python
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

results = {}

for pattern in [TrafficPattern.SEQUENTIAL, TrafficPattern.RANDOM, TrafficPattern.STRIDE]:
    config = SimulationConfig(
        traffic_pattern=pattern,
        request_rate=0.8,
    )
    sim = HBMSimulator(config)
    stats = sim.run()
    results[pattern.value] = stats.throughput_gbps

# Compare results
for pattern, bw in results.items():
    print(f"{pattern}: {bw:.2f} GB/s")
```

### Use Case 2: QoS Priority Testing

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel

# Submit requests with different priorities
controller.submit_request(addr=0x1000, is_read=True, qos_level=15)  # Critical
controller.submit_request(addr=0x2000, is_read=True, qos_level=8)   # Normal
controller.submit_request(addr=0x3000, is_read=True, qos_level=4)   # Low

# Critical requests should complete first
```

### Use Case 3: Refresh Impact Analysis

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

# Test with different refresh modes
for mode in [RefreshMode.ALL_BANK, RefreshMode.PER_BANK]:
    scheduler = HBM4RefreshScheduler(config=spec, mode=mode)
    # ... run simulation and measure impact
```

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Or for specific components
logger = logging.getLogger('hbm4.controller')
logger.setLevel(logging.DEBUG)
```

### Check Queue Status

```python
# Monitor queue depths
stats = controller.get_stats()
print(f"Read queue: {stats['queues']['read_queue_depth']}")
print(f"Write queue: {stats['queues']['write_queue_depth']}")
```

### Verify Address Decoding

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

decoder = HBM4AddressDecoder(spec=spec)
decoded = decoder.decode(0x1234_5678_9ABC_DEF0)

print(f"Stack: {decoded.stack_id}")
print(f"Channel: {decoded.channel_id}")
print(f"Bank: {decoded.bank_id}")
print(f"Row: {hex(decoded.row_id)}")
```

## Next Steps

- [Advanced Features](advanced_features.md) - Learn about multi-channel, QoS, and signal integrity
- [Performance Tuning](performance_tuning.md) - Optimize simulation performance
- [API Reference](../api/) - Detailed API documentation