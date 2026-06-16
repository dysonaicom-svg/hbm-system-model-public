# gem5 Integration Tutorial

This tutorial covers the integration of HBM4 simulation platform with gem5 memory system simulator.

## Overview

The gem5 integration provides:
- **Gem5Bridge**: Core bridge between HBM simulation and gem5
- **Memory Port**: TimingSimpleMemory-compatible port interface
- **Traffic Generator**: CPU/NPU/GPU traffic generation interface
- **Cache Line Handler**: 64/128 byte cache line support
- **Burst Transaction Support**: Multi-beat burst transactions

## Quick Start

### Basic Usage

```python
from sim.interconnect.gem5_bridge import Gem5Bridge

# Create bridge
bridge = Gem5Bridge()

# Connect to gem5 (uses mock mode if gem5 not available)
bridge.connect_to_gem5()

# Send request
req_id = bridge.send_request(
    addr=0x1000,
    size=64,
    is_write=False,
)

# Receive response
response = bridge.recv_response(req_id=req_id, timeout_cycles=1000)

# Sync simulation
bridge.sync(cycle=100)

# Disconnect
bridge.disconnect()
```

### Context Manager Usage

```python
from sim.interconnect.gem5_bridge import Gem5Bridge

with Gem5Bridge() as bridge:
    # Send request
    req_id = bridge.send_request(addr=0x1000, size=64)
    
    # Process response
    response = bridge.recv_response(req_id=req_id)
    print(f"Latency: {response.latency} cycles")
```

## Gem5Bridge API

### Connection Management

```python
from sim.interconnect.gem5_bridge import Gem5Bridge, BridgeConfig

# Default configuration
bridge = Gem5Bridge()

# Custom configuration
config = BridgeConfig(
    gem5_home="/path/to/gem5",       # gem5 installation path
    default_latency=10,              # Default latency in cycles
    max_pending_requests=256,        # Maximum pending requests
    request_timeout=10000,          # Request timeout in cycles
    cache_line_size=64,              # Cache line size (64 or 128)
    enable_qos=True,                 # Enable QoS prioritization
)

bridge = Gem5Bridge(config=config)
bridge.connect_to_gem5(system=gem5_system)  # Connect to real or mock gem5
```

### Request/Response Handling

```python
# Send read request
req_id = bridge.send_request(
    addr=0x1000,           # Target address
    size=64,               # Request size in bytes
    is_write=False,        # Read or write
    qos=8,                 # QoS priority (0-15)
    master_id=0,           # Master ID
)

# Send write request
req_id = bridge.send_request(
    addr=0x2000,
    size=64,
    is_write=True,
    data=[0xDEADBEEF, 0xCAFEBABE],  # Write data
    qos=8,
)

# Receive response
response = bridge.recv_response(req_id=req_id)
print(f"Status: {response.status}")
print(f"Latency: {response.latency} cycles")
if response.data:
    print(f"Data: {response.data}")
```

### High-Level Operations

```python
# Simple read
data = bridge.read(addr=0x1000, size=64)
print(f"Read data: {data}")

# Simple write
result = bridge.write(addr=0x2000, data=[0x12345678], size=8)
print(f"Write successful: {result}")

# Burst read
responses = bridge.burst_read(
    addr=0x1000,
    num_beats=4,
    beat_size=64,
)
print(f"Received {len(responses)} beats")

# Burst write
responses = bridge.burst_write(
    addr=0x2000,
    data=[i for i in range(32)],
    num_beats=4,
    beat_size=64,
)
```

## Traffic Generator Interface

The traffic generator interface provides standardized traffic patterns for CPU/NPU/GPU simulation.

### Available Patterns

```python
# Create traffic generator
tg = bridge.create_traffic_generator("tg1", pattern="sequential")

# Supported patterns:
# - "sequential": Sequential address access
# - "random": Random address access
# - "hotspot": Hotspot-based access (80% to hot region)
# - "stride": Strided address access
```

### Pattern Configuration

```python
# Configure sequential pattern
tg.set_base_address(0x1000_0000)
tg.set_access_size(64)

# Configure stride pattern
tg.set_base_address(0x1000_0000)
tg.stride = 256  # 256-byte stride

# Configure hotspot pattern
tg.hotspot_base = 0x1000_0000
tg.hotspot_size = 0x1000_0000  # 256 MB hotspot
tg.hotspot_ratio = 0.8  # 80% access hotspot
```

### Traffic Generation

```python
# Generate single request
req_id = tg.generate_request()
print(f"Generated request: {req_id}")

# Generate burst
req_ids = tg.generate_burst(num_requests=10)
print(f"Generated {len(req_ids)} requests")

# Get statistics
stats = tg.get_stats()
print(f"Pattern: {stats['pattern']}")
print(f"Requests sent: {stats['requests_sent']}")
print(f"Responses received: {stats['responses_received']}")
print(f"Average latency: {stats['average_latency']}")
```

## Cache Line Handling

The bridge handles cache line alignment automatically for 64-byte and 128-byte cache lines.

### Manual Cache Line Handler

```python
from sim.interconnect.gem5_bridge import CacheLineHandler

handler = CacheLineHandler(line_size=64)

# Align address to cache line boundary
aligned = handler.align_address(0x1001)  # Returns 0x1000

# Check alignment
is_aligned = handler.is_aligned(0x1000, 64)  # Returns True

# Split unaligned request
chunks = handler.split_request(0x1001, 192)
# Returns [(0x1000, 63), (0x1040, 64), (0x1080, 64)]

# Calculate beats
beats = handler.calculate_beats(128)  # Returns 8

# Calculate burst cycles
cycles = handler.calculate_burst_cycles(128)  # Returns 2
```

### Statistics

```python
stats = handler.get_stats()
print(f"Cache hits: {stats['cache_hits']}")
print(f"Cache misses: {stats['cache_misses']}")
print(f"Split requests: {stats['split_requests']}")
print(f"Hit rate: {stats['hit_rate']}")
```

## HBM4-Specific Features

### Channel Load Tracking

```python
# Get load for specific channel
load = bridge.get_channel_load(channel_id=5)
print(f"Channel 5 load: {load}")

# Get statistics for all channels
channel_stats = bridge.get_channel_stats()
for ch_id, stats in channel_stats.items():
    print(f"Channel {ch_id}: {stats['requests']} requests")
```

### Integration with HBM4 Controller

```python
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import HBM4Spec

# Create HBM4 spec and controller
spec = HBM4Spec()
controller = HBM4Controller(spec=spec)

# Submit request through controller
req_id = controller.submit_request(
    addr=0x1000,
    is_read=True,
    qos_level=8,
    size_bytes=64,
)

# Also use bridge for gem5 integration
bridge_req_id = bridge.send_request(
    addr=0x2000,
    size=64,
    is_write=False,
)
```

## Memory Port Implementation

### Creating Memory Port

```python
from model.interconnect.gem5_memory_port import (
    HBM4MemoryPort,
    CacheLineHandler,
    TrafficGeneratorInterface,
    create_memory_port,
    create_traffic_generator,
)

# Create memory port
port = HBM4MemoryPort(
    name="dram.port",
    cache_line_size=64,
)

# Or use factory function
port = create_memory_port(
    name="dram.port",
    cache_line_size=64,
)
```

### Memory Port Operations

```python
# Connect to master port
port.connect(master_port)

# Send request
req_id = port.send_request(
    addr=0x1000,
    size=64,
    is_write=False,
    qos=8,
)

# Receive response
response = port.recv_response(req_id=req_id, timeout_cycles=1000)

# Get channel load
load = port.get_channel_load(channel_id=5)

# Get statistics
stats = port.get_stats()
print(f"Packets sent: {stats['packets_sent']}")
print(f"Current cycle: {stats['current_cycle']}")
```

### Traffic Generator with Port

```python
# Create traffic generator
tg = create_traffic_generator(
    name="cpu_tg",
    port=port,
    pattern="sequential",
)

# Generate traffic
tg.generate_burst(num_requests=100)

# Get traffic stats
tg_stats = tg.get_stats()
```

## Error Handling

### Timeout Handling

```python
# Set timeout in config
config = BridgeConfig(request_timeout=10000)

# Check for timeout
response = bridge.recv_response(req_id=req_id, timeout_cycles=1000)
if response and response.status == Gem5ResponseStatus.TIMEOUT:
    print("Request timed out!")
```

### Queue Overflow Handling

```python
# Check queue status
pending = bridge.get_pending_count()
max_pending = bridge.config.max_pending_requests

if pending >= max_pending:
    print("Queue full, wait before sending more requests")
```

### Disconnect Handling

```python
# Disconnect drains all pending requests
bridge.disconnect()
assert bridge.get_pending_count() == 0
```

## Statistics and Monitoring

### Bridge Statistics

```python
stats = bridge.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Total responses: {stats['total_responses']}")
print(f"Average latency: {stats['avg_latency']}")
print(f"Read ratio: {stats['read_ratio']}")
print(f"Pending requests: {stats['pending_requests']}")
print(f"Current cycle: {stats['current_cycle']}")

# Cache line stats
if 'cache_line' in stats:
    print(f"Cache hits: {stats['cache_line']['cache_hits']}")
    print(f"Cache misses: {stats['cache_line']['cache_misses']}")
```

### Reset Statistics

```python
bridge.reset_stats()
print(bridge.get_stats()["total_requests"])  # 0
```

## Advanced Usage

### Callback Functions

```python
def on_request_sent(request):
    print(f"Request sent: {request.req_id}")

def on_response_received(response):
    print(f"Response received: {response.req_id}, latency={response.latency}")

bridge.set_callback("request_sent", on_request_sent)
bridge.set_callback("response_received", on_response_received)
```

### Transaction Tracking

```python
# Get transaction for request
txn = bridge.get_transaction(req_id)
print(f"Transaction state: {txn.state}")
print(f"Created cycle: {txn.created_cycle}")
print(f"Issued cycle: {txn.issued_cycle}")
print(f"Latency: {txn.latency}")
```

### Multiple Traffic Generators

```python
# Create multiple traffic generators
cpu_tg = bridge.create_traffic_generator("cpu", "sequential")
npu_tg = bridge.create_traffic_generator("npu", "hotspot")
gpu_tg = bridge.create_traffic_generator("gpu", "random")

# Generate traffic from all sources
cpu_tg.generate_burst(100)
npu_tg.generate_burst(50)
gpu_tg.generate_burst(200)

# Get all generators
all_tg = bridge.get_all_traffic_generators()
for name, tg in all_tg.items():
    print(f"{name}: {tg.get_stats()}")
```

## Mock Mode

The bridge automatically falls back to mock mode if gem5 is not available:

```python
bridge = Gem5Bridge()

# Check if using mock mode
if bridge._use_mock:
    print("Running in mock mode")
    
    # Mock system is available
    mock_system = bridge._mock_system
    mock_system.set_latency("cpu.inst", 20)
```

## Complete Example

```python
#!/usr/bin/env python3
"""Complete gem5 integration example"""

from sim.interconnect.gem5_bridge import Gem5Bridge, BridgeConfig
from model.dram.hbm4_spec import HBM4Spec

def main():
    # Create bridge with HBM4 spec
    spec = HBM4Spec()
    config = BridgeConfig(
        default_latency=10,
        max_pending_requests=256,
        cache_line_size=64,
    )
    
    with Gem5Bridge(config=config, spec=spec) as bridge:
        print(f"Connected to gem5 (mock_mode={bridge._use_mock})")
        
        # Create traffic generator
        tg = bridge.create_traffic_generator("workload", "sequential")
        tg.set_base_address(0x1000_0000)
        tg.set_access_size(64)
        
        # Generate workload
        req_ids = tg.generate_burst(100)
        print(f"Generated {len(req_ids)} requests")
        
        # Process responses
        responses = 0
        for req_id in req_ids:
            resp = bridge.recv_response(req_id=req_id, timeout_cycles=1000)
            if resp:
                responses += 1
                tg.record_response(resp.latency)
        
        print(f"Received {responses} responses")
        
        # Print statistics
        bridge_stats = bridge.get_stats()
        tg_stats = tg.get_stats()
        
        print("\n=== Bridge Statistics ===")
        print(f"Total requests: {bridge_stats['total_requests']}")
        print(f"Average latency: {bridge_stats['avg_latency']:.2f} cycles")
        
        print("\n=== Traffic Generator Statistics ===")
        print(f"Pattern: {tg_stats['pattern']}")
        print(f"Requests sent: {tg_stats['requests_sent']}")
        print(f"Average latency: {tg_stats['average_latency']:.2f} cycles")

if __name__ == "__main__":
    main()
```

## See Also

- [Getting Started Guide](getting_started.md) - Basic HBM4 simulation setup
- [Performance Tuning](performance_tuning.md) - Optimizing simulation performance
- [Advanced Features](advanced_features.md) - Advanced simulation features