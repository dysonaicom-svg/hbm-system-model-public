# HBM4 System Quick Start Guide

A practical guide to get started with the HBM4 System Modeling Platform.

**Estimated Time:** 5 minutes to first simulation  
**Prerequisites:** Python 3.8+

---

## Quick Start (5 Minutes)

### Step 1: Install (30 seconds)

```bash
pip install -r requirements.txt
pip install -e .
```

### Step 2: Verify (10 seconds)

```bash
python -c "from model.dram.hbm4_spec import HBM4Spec; print('OK')"
# Output: OK
```

### Step 3: First Simulation (5 lines)

Create `quick_sim.py`:

```python
#!/usr/bin/env python3
"""Minimal HBM4 simulation - 5 lines to first results"""
from sim.simulator import HBMSimulator

sim = HBMSimulator(channels=32, data_rate_gbps=16)  # 1. Create
sim.submit_request(addr=0x1000, size=64, is_write=False)  # 2. Submit
sim.run(cycles=100)  # 3. Run
stats = sim.get_stats()  # 4. Get results
print(f"Bandwidth: {stats['bandwidth_gbps']:.2f} GB/s, Latency: {stats['avg_latency_cycles']:.1f} cycles")
```

Run it:

```bash
python quick_sim.py
```

Expected output:
```
Bandwidth: 164.32 GB/s, Latency: 12.93 cycles
```

### Step 4: Run Tests (Optional)

```bash
pytest tests/controller/test_hbm4_address_decoder.py -v
```

---

## Table of Contents

1. [Installation](#1-installation)
2. [Basic Usage](#2-basic-usage)
3. [HBM3 Controller Example](#3-hbm3-controller-example)
4. [HBM4 Controller Example](#4-hbm4-controller-example)
5. [Traffic Generation](#5-traffic-generation)
6. [Address Decoding](#6-address-decoding)
7. [QoS Scheduling](#7-qos-scheduling)
8. [Refresh Management](#8-refresh-management)
9. [DRAM Model](#9-dram-model)
10. [Interconnect](#10-interconnect)
11. [Running Tests](#11-running-tests)
12. [Performance Measurement](#12-performance-measurement)
13. [Common Patterns](#13-common-patterns)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Installation

### Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Install in editable mode
```

### Verify Installation

```python
python -c "from model.controller.config import HBM3_DEFAULT, HBM4_DEFAULT; print('HBM3:', HBM3_DEFAULT); print('HBM4:', HBM4_DEFAULT)"
```

---

## 2. Basic Usage

### Minimal Example

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

# Create controller
controller = HBMController(HBM3_DEFAULT)

# Submit request
request = HBMRequest(addr=0x1000, length=64, is_read=True)
controller.submit_request(request)

# Run one cycle
for _ in range(100):
    scheduled, response = controller.tick()
    if response:
        print(f"Completed request {response.request_id}")
        break
```

### Run Complete Simulation

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

controller = HBMController(HBM3_DEFAULT)

# Submit 100 sequential requests
for i in range(100):
    request = HBMRequest(
        addr=0x1000 + i * 64,
        length=64,
        is_read=(i % 2 == 0)  # Alternate read/write
    )
    controller.submit_request(request)

# Run simulation
completed = 0
for cycle in range(10000):
    scheduled, response = controller.tick()
    if response:
        completed += 1
        if completed % 10 == 0:
            print(f"Cycle {cycle}: {completed} completed")

    if completed >= 100:
        break

# Get statistics
stats = controller.get_stats()
print(f"\nStatistics:")
print(f"  Total requests: {stats['controller']['total_requests']}")
print(f"  Read requests: {stats['controller']['read_requests']}")
print(f"  Write requests: {stats['controller']['write_requests']}")
print(f"  Row hit rate: {stats['scheduler']['row_hit_rate']:.1%}")
```

---

## 3. HBM3 Controller Example

### Create Custom HBM3 Configuration

```python
from model.controller.config import HBMConfig
from model.dram.timing import HBM3Timing

# Custom HBM3 config
config = HBMConfig(
    stack_count=2,
    channels_per_stack=8,
    pseudo_channels_per_channel=2,
    banks_per_pseudo_channel=16,
    bank_groups_per_channel=8,
    data_rate=6.4e9,
    io_width=1024,
    queue_depth=32,
    scheduler_mode="fr-fcfs",
    timing=HBM3Timing(),
)

# Calculate bandwidth
print(f"Peak bandwidth: {config.calc_bandwidth():.1f} GB/s")
print(f"Total bandwidth: {config.calc_bandwidth_total():.1f} GB/s")
```

### Sequential Access Pattern

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

controller = HBMController(HBM3_DEFAULT)

# Sequential addresses (good row hit rate)
for i in range(1000):
    request = HBMRequest(
        addr=0x1000 + i * 64,  # 64-byte stride
        length=64,
        is_read=True
    )
    controller.submit_request(request)

# Run with row hit tracking
row_hits = 0
for _ in range(10000):
    scheduled, response = controller.tick()
    if scheduled and scheduled.row_hit:
        row_hits += 1

print(f"Row hit rate: {row_hits / 1000:.1%}")
```

---

## 4. HBM4 Controller Example

### HBM4 Configuration

```python
from model.controller.config import HBMConfig
from model.dram.timing import HBM4Timing

# HBM4 configuration
config = HBMConfig(
    stack_count=4,
    channels_per_stack=16,  # 16 channels per stack for HBM4
    pseudo_channels_per_channel=2,
    banks_per_pseudo_channel=16,
    bank_groups_per_channel=8,
    data_rate=12.8e9,  # HBM4 speed
    io_width=2048,    # Double HBM3 width
    queue_depth=64,
    max_outstanding=32,
    scheduler_mode="qos",
    timing=HBM4Timing.for_12gbps(),
)

print(f"HBM4 peak bandwidth: {config.calc_bandwidth():.1f} GB/s")
```

### HBM4 32-Channel Address Decoding

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

decoder = HBM4AddressDecoder(mapping_scheme="rbc")

# Decode addresses across all 32 channels
for channel in range(32):
    addr = channel * 0x10000000000  # Space addresses across channels
    decoded = decoder.decode(addr)
    print(f"Channel {channel}: bank={decoded.bank_id}, row=0x{decoded.row_id:x}")

# Quick field extraction
addr = 0x123456789ABC
channel = decoder.get_channel_id(addr)
bank = decoder.get_bank_id(addr)
row = decoder.get_row_id(addr)
print(f"Address 0x{addr:016x}: ch={channel}, bank={bank}, row=0x{row:x}")
```

---

## 5. Traffic Generation

### Basic Traffic Generation

```python
from model.traffic.traffic_generator import (
    TrafficGenerator,
    TrafficConfig,
    TrafficPattern
)

# Create traffic generator
config = TrafficConfig(
    request_rate=1e6,  # 1M requests/second
    read_write_ratio=0.7,  # 70% reads
    burst_size=32,
)
tg = TrafficGenerator(config)

# Generate random traffic
requests = tg.generate(count=100, pattern=TrafficPattern.SYNTHETIC_RANDOM)
print(f"Generated {len(requests)} random requests")

# Generate sequential traffic
tg.set_pattern(TrafficPattern.SYNTHETIC_FIXED_RATE)
requests = tg.generate(count=100)
print(f"Generated {len(requests)} sequential requests")
```

### AI Training Traffic

```python
from model.traffic.traffic_generator import TrafficGenerator, TrafficConfig, TrafficPattern

config = TrafficConfig(
    request_rate=10e6,  # High rate for training
    read_write_ratio=0.5,  # Balanced read/write
    batch_size=32,
)
tg = TrafficGenerator(config)

# Weight update phase
tg.set_pattern(TrafficPattern.TRAINING_WEIGHT_UPDATE)
weight_requests = tg.generate(count=1000)

# Gradient computation phase
tg.set_pattern(TrafficPattern.TRAINING_GRADIENT)
gradient_requests = tg.generate(count=1000)

# Feature map transfer
tg.set_pattern(TrafficPattern.TRAINING_FEATURE_MAP)
feature_requests = tg.generate(count=2000)

print(f"Weight updates: {len(weight_requests)}")
print(f"Gradients: {len(gradient_requests)}")
print(f"Feature maps: {len(feature_requests)}")
```

### AI Inference Traffic

```python
from model.traffic.traffic_generator import TrafficGenerator, TrafficConfig, TrafficPattern

config = TrafficConfig(
    request_rate=5e6,
    read_write_ratio=0.9,  # Mostly reads
    precision=DataPrecision.FP16,
)
tg = TrafficGenerator(config)

# Burst reads for inference
tg.set_pattern(TrafficPattern.INFERENCE_BURST_READ)
requests = tg.generate(count=100)

# Weight reuse pattern
tg.set_pattern(TrafficPattern.INFERENCE_WEIGHT_REUSE)
requests = tg.generate(count=100)

# Get statistics
stats = tg.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Read ratio: {stats['read_ratio']:.1%}")
```

---

## 6. Address Decoding

### HBM4 Address Decoder

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.hbm4_spec import HBM4Spec

# Create decoder with default spec
decoder = HBM4AddressDecoder()

# Decode various addresses
test_addresses = [
    0x0000_0000_0000_1000,  # Stack 0, Channel 0
    0x4000_0000_0000_0000,  # Stack 2
    0x0001_2345_6789_ABCD,  # Random address
]

for addr in test_addresses:
    decoded = decoder.decode(addr)
    print(f"0x{addr:016x}")
    print(f"  Stack: {decoded.stack_id}")
    print(f"  Channel: {decoded.channel_id}")
    print(f"  Pseudo-channel: {decoded.pseudo_channel_id}")
    print(f"  Bank group: {decoded.bank_group_id}")
    print(f"  Bank: {decoded.bank_id}")
    print(f"  Row: 0x{decoded.row_id:04x}")
    print(f"  Column: {decoded.col_id}")
    print()
```

### Different Mapping Schemes

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

# Test different schemes
for scheme in ["rbc", "bcr", "crb", "hbm4"]:
    decoder = HBM4AddressDecoder(mapping_scheme=scheme)
    addr = 0x123456789ABC

    decoded = decoder.decode(addr)
    print(f"Scheme: {scheme}")
    print(f"  Channel: {decoded.channel_id}")
    print(f"  Bank: {decoded.bank_id}")
    print(f"  Row: 0x{decoded.row_id:x}")
    print()
```

---

## 7. QoS Scheduling

### Basic QoS Scheduling

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler

scheduler = HBM4QoSScheduler()

# Submit requests with different priorities
scheduler.submit_request(
    request_id=1, addr=0x1000, qos=15, is_read=True, row_hit=True
)
scheduler.submit_request(
    request_id=2, addr=0x2000, qos=8, is_read=True, row_hit=True
)
scheduler.submit_request(
    request_id=3, addr=0x3000, qos=4, is_read=False, row_hit=False
)
scheduler.submit_request(
    request_id=4, addr=0x4000, qos=15, is_read=True, row_hit=False
)

# Schedule - should pick QoS 15 with row hit first
for _ in range(4):
    req = scheduler.schedule()
    if req:
        print(f"Scheduled: id={req.request_id}, qos={req.qos}, row_hit={req.row_hit}")

# Get statistics
stats = scheduler.get_stats()
print(f"Total scheduled: {stats['total_scheduled']}")
print(f"By QoS: {stats['by_qos']}")
```

### QoS with Bandwidth Guarantees

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler

scheduler = HBM4QoSScheduler()

# Customize bandwidth guarantees
scheduler.set_bandwidth_guarantee(15, 500.0)  # Critical gets 500 GB/s
scheduler.set_bandwidth_guarantee(12, 400.0)  # High gets 400 GB/s
scheduler.set_bandwidth_cap(15, 1000.0)  # Cap at 1 TB/s

# Submit high-priority traffic
for i in range(100):
    scheduler.submit_request(
        request_id=i, addr=0x1000 + i * 64,
        qos=15, is_read=True, row_hit=(i % 2 == 0)
    )

# Schedule and monitor
for _ in range(100):
    req = scheduler.schedule()
    if req is None:
        break

stats = scheduler.get_stats()
print(f"High priority scheduled: {stats['by_qos'].get(15, 0)}")
```

---

## 8. Refresh Management

### Per-Bank Refresh

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

scheduler = HBM4RefreshScheduler()

# Use per-bank refresh (default for HBM4)
scheduler.set_mode(RefreshMode.PER_BANK)

# Simulate refresh
refresh_count = 0
for cycle in range(100000):
    scheduler.tick()

    cmd = scheduler.get_refresh_command()
    if cmd:
        refresh_count += 1
        cmd_name, channel, bank = cmd
        print(f"Cycle {cycle}: {cmd_name} ch={channel}, bank={bank}")

print(f"Total refreshes in 100K cycles: {refresh_count}")
```

### Enable DRFM (Row-Hammer Mitigation)

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler

scheduler = HBM4RefreshScheduler()

# Enable DRFM for row-hammer mitigation
scheduler.enable_drfm(enabled=True, threshold=1000)

# Simulate and check for banks needing refresh
for cycle in range(50000):
    scheduler.tick()

    # Check if any banks need targeted refresh
    banks_needing = scheduler.get_banks_needing_refresh()
    if banks_needing:
        print(f"Cycle {cycle}: Banks {banks_needing} need refresh")
```

### Get Refresh Statistics

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler

scheduler = HBM4RefreshScheduler()

# Run refresh simulation
for _ in range(100000):
    scheduler.tick()
    scheduler.get_refresh_command()

# Get statistics
stats = scheduler.get_stats()
print(f"Total refreshes: {stats['total_refreshes']}")
print(f"All-bank refreshes: {stats['all_bank_refreshes']}")
print(f"Per-bank refreshes: {stats['per_bank_refreshes']}")
print(f"Current mode: {stats['mode']}")
print(f"DRFM enabled: {stats['drfm_enabled']}")
```

---

## 9. DRAM Model

### HBM4 Channel Model

```python
from model.dram.hbm4_channel_model import HBM4Channel, HBM4Command

# Create channel with 8Gbps speed grade
channel = HBM4Channel.create_with_speed_grade(0, "8Gbps")

# Issue activate command
result = channel.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
print(f"ACT result: {result}")

# Issue read command
result = channel.issue_command('RD', pseudo_channel=0, bank=0, row=100)
print(f"RD result: {result}")

# Advance time
for _ in range(10):
    channel.tick()

# Check state
state = channel.get_state_summary()
print(f"Channel state: {state['state']}")
print(f"Active banks: {state['pseudo_channels'][0]['active_banks']}")
```

### Numeric Command Encoding (RTL Interface)

```python
from model.dram.hbm4_channel_model import HBM4Channel, HBM4Command

channel = HBM4Channel.create_with_speed_grade(0, "8Gbps")

# Issue commands using numeric encoding (matches RTL)
channel.issue_numeric_command(HBM4Command.ACT, pseudo_channel=0, bank=0, row=100)
channel.issue_numeric_command(HBM4Command.READ, pseudo_channel=0, bank=0, row=100)
channel.issue_numeric_command(HBM4Command.PRE, pseudo_channel=0, bank=0, row=0)

# Advance time
for _ in range(20):
    channel.tick()
```

### Bank State Machine

```python
from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
from model.dram.hbm4_spec import get_timing_for_speed_grade

timing = get_timing_for_speed_grade("8Gbps")
bank = BankStateMachine(bank_id=0, timing=timing)

print(f"Initial state: {bank.bank.state.name}")

# Activate row
result = bank.activate(row=100)
print(f"Activate result: {result}, state: {bank.bank.state.name}")

# Check if row is open
is_hit = bank.is_row_hit(100)
print(f"Row 100 hit: {is_hit}")

# Read (should succeed with open row)
result = bank.read()
print(f"Read result: {result}")

# Advance time
for _ in range(10):
    bank.set_time(bank.current_time + 1)

# Precharge
result = bank.precharge()
print(f"Precharge result: {result}, state: {bank.bank.state.name}")
```

---

## 10. Interconnect

### Crossbar Interconnect

```python
from model.interconnect.interconnect import CrossbarInterconnect, InterconnectRequest

# Create crossbar
ic = CrossbarInterconnect(
    num_ports=32,
    stack_count=4,
    channels_per_stack=32,
)

# Route requests
for i in range(10):
    req = InterconnectRequest(
        source_port=i % 32,
        addr=0x1000 + i * 0x1000000000,
        size=64,
        qos=8,
    )
    resp = ic.route_request(req)
    print(f"Request {i}: stack={resp.dest_stack}, ch={resp.dest_channel}")

# Get statistics
stats = ic.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average latency: {stats['average_latency']:.1f} cycles")
```

### Mesh Interconnect

```python
from model.interconnect.interconnect import MeshInterconnect, InterconnectRequest, RoutingMode

# Create 4x8 mesh
ic = MeshInterconnect(
    rows=4,
    cols=8,
    stack_count=4,
    routing_mode=RoutingMode.SHORTEST_PATH,
)

# Route requests
for i in range(10):
    req = InterconnectRequest(
        source_port=i,
        addr=0x1000 + i * 64,
        size=64,
    )
    resp = ic.route_request(req)
    print(f"Request {i}: latency={resp.latency} cycles")

ic.tick()  # Advance simulation
```

### Binary Tree Interconnect

```python
from model.interconnect.interconnect import BinaryTreeInterconnect, InterconnectRequest

# Create binary tree
ic = BinaryTreeInterconnect(
    num_leaves=32,
    stack_count=4,
)

# Broadcast capability
req = InterconnectRequest(source_port=0, addr=0x1000)
responses = ic.broadcast(req)
print(f"Broadcast to {len(responses)} destinations")
```

---

## 11. Running Tests

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test directory
pytest tests/controller/ -v
pytest tests/dram/ -v

# Run with coverage
pytest tests/ --cov=model --cov-report=html
```

### Run Specific Tests

```bash
# Address decoder tests
pytest tests/controller/test_hbm4_address_decoder.py -v

# Controller integration tests
pytest tests/controller/test_integration.py -v

# QoS scheduler tests
pytest tests/controller/test_hbm4_qos_scheduler.py -v

# DRAM model tests
pytest tests/dram/test_hbm4_channel_model.py -v
```

### Run Benchmarks

```bash
# Bandwidth benchmark
python -m model.benchmark.bandwidth_benchmark

# Latency benchmark
python -m model.benchmark.latency_benchmark

# Scheduler benchmark
python -m model.benchmark.scheduler_benchmark
```

---

## 12. Performance Measurement

### Built-in Performance Metrics

The simulator automatically collects these metrics:

```python
sim = HBMSimulator()
sim.run(cycles=10000)
stats = sim.get_stats()

# Available metrics
print("=== Performance Summary ===")
print(f"Total Cycles:        {stats['cycles']}")
print(f"Total Requests:      {stats['total_requests']}")
print(f"Read Requests:       {stats['read_requests']}")
print(f"Write Requests:      {stats['write_requests']}")
print(f"Bandwidth (GB/s):    {stats['bandwidth_gbps']:.2f}")
print(f"Avg Latency (cyc):   {stats['avg_latency_cycles']:.2f}")
print(f"Max Latency (cyc):   {stats['max_latency_cycles']}")
print(f"Row Hit Rate:        {stats['row_hit_rate']*100:.1f}%")
print(f"Queue Utilization:   {stats['queue_utilization']*100:.1f}%")
```

### Bandwidth Efficiency Calculation

```python
def calculate_efficiency(stats, channels, data_rate_gbps):
    """Calculate bandwidth efficiency vs theoretical peak"""
    peak_bw = channels * data_rate_gbps * 256 / 8  # GB/s for 2048-bit interface
    achieved_bw = stats['bandwidth_gbps']
    efficiency = (achieved_bw / peak_bw) * 100
    return efficiency

stats = sim.get_stats()
efficiency = calculate_efficiency(stats, channels=32, data_rate_gbps=16)
print(f"Bandwidth Efficiency: {efficiency:.1f}%")
```

### Latency Distribution

```python
def analyze_latency(sim):
    """Analyze latency distribution"""
    latencies = sim.get_latency_samples()

    import statistics
    p50 = statistics.median(latencies)
    latencies_sorted = sorted(latencies)
    p95_idx = int(len(latencies_sorted) * 0.95)
    p99_idx = int(len(latencies_sorted) * 0.99)

    print(f"Latency P50: {p50:.1f} cycles")
    print(f"Latency P95: {latencies_sorted[p95_idx]:.1f} cycles")
    print(f"Latency P99: {latencies_sorted[p99_idx]:.1f} cycles")

analyze_latency(sim)
```

### Performance Benchmarks

```python
#!/usr/bin/env python3
"""Complete traffic benchmark example"""

from sim.simulator import HBMSimulator

def benchmark_pattern(name, pattern, **kwargs):
    """Run a benchmark with specified traffic pattern"""
    print(f"\n=== {name} Benchmark ===")

    sim = HBMSimulator(channels=32, data_rate_gbps=16)

    # Generate traffic based on pattern
    from model.traffic.traffic_generator import TrafficGenerator
    gen = TrafficGenerator(pattern=pattern)
    requests = gen.generate(**kwargs)

    for req in requests:
        sim.submit_request(**req)

    sim.run(cycles=10000)
    stats = sim.get_stats()

    print(f"  Requests:     {stats['total_requests']}")
    print(f"  Bandwidth:   {stats['bandwidth_gbps']:.2f} GB/s")
    print(f"  Avg Latency: {stats['avg_latency_cycles']:.2f} cycles")
    print(f"  Row Hits:    {stats['row_hit_rate']*100:.1f}%")

# Run benchmarks
benchmark_pattern("Sequential Read", "sequential",
    start_addr=0x0, size_bytes=64, num_requests=1000, is_write=False)
benchmark_pattern("Random Access", "random",
    start_addr=0x0, size_bytes=4096, num_requests=1000, is_write=False)
benchmark_pattern("Stride Access", "stride",
    start_addr=0x0, stride_bytes=256, num_requests=1000, is_write=False)
```

---

## 13. Common Patterns

### Pattern 1: Sequential Access with High Row Hit Rate

```python
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

controller = HBMController(HBM3_DEFAULT)

# Sequential addresses with small stride (maximizes row hits)
base_addr = 0x1000
for i in range(1000):
    request = HBMRequest(
        addr=base_addr + (i // 16) * 2048 + (i % 16) * 64,
        length=64,
        is_read=True
    )
    controller.submit_request(request)

# Run and measure
row_hits = 0
for _ in range(2000):
    scheduled, response = controller.tick()
    if scheduled and scheduled.row_hit:
        row_hits += 1

print(f"Row hit rate: {row_hits / 1000:.1%}")
```

### Pattern 2: Random Access with Load Balancing

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.controller import HBMController
from model.controller.request import HBMRequest
import random

decoder = HBM4AddressDecoder()
controller = HBMController()

# Random addresses across all channels
for i in range(1000):
    # Generate random address
    addr = random.randint(0, 0xFFFFFFFFF)
    # Align to 8-byte boundary
    addr = addr & ~0x7

    request = HBMRequest(
        addr=addr,
        length=64,
        is_read=random.random() < 0.7
    )
    controller.submit_request(request)

# Run simulation
for _ in range(10000):
    controller.tick()
```

### Pattern 3: QoS-Aware Priority Scheduling

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler

scheduler = HBM4QoSScheduler()

# Submit requests with different QoS levels
critical_requests = [
    HBMRequest(addr=0x1000 + i * 64, length=64, is_read=True, qos=15)
    for i in range(10)
]
normal_requests = [
    HBMRequest(addr=0x2000 + i * 64, length=64, is_read=True, qos=8)
    for i in range(10)
]

for req in critical_requests:
    scheduler.submit_request(req.request_id, req.addr, req.qos, req.is_read)
for req in normal_requests:
    scheduler.submit_request(req.request_id, req.addr, req.qos, req.is_read)

# Schedule - critical requests should be prioritized
scheduled = []
for _ in range(20):
    req = scheduler.schedule()
    if req:
        scheduled.append(req)

print(f"Scheduled {len(scheduled)} requests")
print(f"High priority (15): {sum(1 for r in scheduled if r.qos == 15)}")
print(f"Normal priority (8): {sum(1 for r in scheduled if r.qos == 8)}")
```

### Pattern 4: Multi-Stack Configuration

```python
from model.controller.config import HBMConfig
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.controller import HBMController
from model.controller.request import HBMRequest

# Configure for 4 stacks
config = HBMConfig(
    stack_count=4,
    channels_per_stack=16,
    data_rate=12.8e9,
)

controller = HBMController(config)

# Generate addresses for all 4 stacks
for stack in range(4):
    for channel in range(16):
        addr = (stack << 46) | (channel << 41)
        request = HBMRequest(
            addr=addr,
            length=64,
            is_read=True
        )
        controller.submit_request(request)

# Run and verify stack distribution
stats = controller.get_stats()
print(f"Total requests across {config.stack_count} stacks")
```

### Pattern 5: Integration with Traffic Generator

```python
from model.traffic.traffic_generator import TrafficGenerator, TrafficConfig, TrafficPattern
from model.controller.config import HBM3_DEFAULT
from model.controller.controller import HBMController

# Create components
traffic_config = TrafficConfig(request_rate=1e6, read_write_ratio=0.7)
traffic_gen = TrafficGenerator(traffic_config)
controller = HBMController(HBM3_DEFAULT)

# Set AI training pattern
traffic_gen.set_pattern(TrafficPattern.TRAINING_WEIGHT_UPDATE)

# Generate and submit requests
requests = traffic_gen.generate(count=100)
for req in requests:
    controller.submit_request(req)

# Run simulation
completed = 0
for cycle in range(10000):
    scheduled, response = controller.tick()
    if response:
        completed += 1
        if completed % 10 == 0:
            print(f"Completed: {completed}")

# Final statistics
controller_stats = controller.get_stats()
traffic_stats = traffic_gen.get_stats()

print(f"\nController stats: {controller_stats['controller']}")
print(f"Traffic stats: {traffic_stats}")
```

---

## 14. Troubleshooting

### Common Issues and Solutions

#### Issue 1: Queue Overflow Warnings

```
WARNING: Request queue full, submission delayed
```

**Solution:** Increase queue depth or reduce request rate:

```python
# Increase queue depth
from model.controller.config import HBMConfig
config = HBMConfig(
    queue_depth=512,  # Increase from default 32
)
controller = HBMController(config)

# Or reduce request rate with backpressure
sim = HBMSimulator()
sim.set_throttle(requests_per_cycle=0.8)
```

#### Issue 2: Address Alignment Errors

```
ValueError: Address not aligned to burst size
```

**Solution:** Align addresses to 8-byte boundaries:

```python
# Correct: 8-byte aligned
addr = 0x1000 & ~0x7  # addr = 0x1000

# For 64-byte cache lines
addr = original_addr & ~0x3F
```

#### Issue 3: Import Errors

```
ModuleNotFoundError: No module named 'model.dram'
```

**Solution:** Reinstall the package:

```bash
pip uninstall hbm4-platform
pip install -e .
```

#### Issue 4: Timing Parameter Mismatch

```
ValueError: Timing parameters do not match data rate
```

**Solution:** Use matching timing for data rate:

```python
from model.dram.timing import HBM4Timing
from model.controller.config import HBMConfig

config = HBMConfig(
    data_rate=12.8e9,
    timing=HBM4Timing.for_12gbps()  # Match data rate
)
```

### Debug Mode

Enable verbose logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

sim = HBMSimulator(debug=True)
sim.run(cycles=100)
```

### Request Tracing

Track individual request completion:

```python
# Enable request tracking
sim = HBMSimulator(track_requests=True)

# Submit requests with tags
for i in range(10):
    sim.submit_request(
        addr=i * 64,
        size=64,
        is_write=False,
        tag=f"req_{i}"
    )

sim.run(cycles=1000)

# Get individual request status
for i in range(10):
    status = sim.get_request_status(f"req_{i}")
    print(f"req_{i}: {status}")
```

### Performance Profiling

Identify bottlenecks in your simulation:

```python
# Enable profiling
sim = HBMSimulator(profile=True)
sim.run(cycles=10000)

# Get profile report
profile = sim.get_profile()
for component, cycles in sorted(profile.items(), key=lambda x: -x[1]):
    print(f"{component}: {cycles} cycles")
```

### Debug Quick Reference

| Issue | Command/Check | Solution |
|-------|---------------|----------|
| Queue full | `controller.queue_manager.can_push()` | Increase queue depth |
| Address error | `addr & ~0x7` | Align to 8 bytes |
| Import error | `pip install -e .` | Reinstall package |
| Timing mismatch | `HBM4Timing.for_XXgbps()` | Match timing to data rate |
| Slow simulation | `sim.set_throttle()` | Reduce request rate |
| No results | `sim.get_stats()` | Check simulation ran |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    HBM4 QUICK START                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INSTALL                                                        │
│  pip install -r requirements.txt                               │
│  pip install -e .                                               │
│                                                                 │
│  BASIC SIMULATION                                               │
│  from sim.simulator import HBMSimulator                         │
│  sim = HBMSimulator(channels=32, data_rate_gbps=16)             │
│  sim.submit_request(addr, size, is_write)                       │
│  sim.run(cycles=10000)                                          │
│  stats = sim.get_stats()                                        │
│                                                                 │
│  HBM3 CONTROLLER                                                │
│  from model.controller.controller import HBMController          │
│  from model.controller.request import HBMRequest                │
│  controller = HBMController(HBM3_DEFAULT)                       │
│  controller.submit_request(HBMRequest(...))                      │
│                                                                 │
│  ADDRESS DECODING                                               │
│  from model.controller.hbm4_address_decoder import HBM4AddressDecoder
│  decoder = HBM4AddressDecoder()                                 │
│  decoded = decoder.decode(addr)                                  │
│                                                                 │
│  QOS SCHEDULING                                                 │
│  from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler
│  scheduler = HBM4QoSScheduler()                                │
│  scheduler.submit_request(req_id, addr, qos, is_read)           │
│  scheduled = scheduler.schedule()                               │
│                                                                 │
│  PERFORMANCE                                                    │
│  stats['bandwidth_gbps']    # GB/s achieved                     │
│  stats['avg_latency_cycles'] # Average cycles                   │
│  stats['row_hit_rate']      # Hit rate (0-1)                    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  TESTS              pytest tests/ -v                           │
│  BENCHMARK          python -m sim.benchmark                    │
│  RTL SIMULATION     cd rtl && verilator --cc --trace ...        │
└─────────────────────────────────────────────────────────────────┘
```

---

## See Also

- [API Documentation](API.md) - Complete API reference
- [Architecture Documentation](ARCHITECTURE.md) - System architecture details
- [Design Document](design/2026-06-15-hbm-system-model-design.md) - Design specification
- [User Guide](USER_GUIDE.md) - Detailed user documentation
- [Benchmark Results](BENCHMARK_RESULTS.md) - Performance benchmarks