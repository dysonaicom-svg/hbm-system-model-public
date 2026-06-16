# Performance Tuning Guide

This guide covers techniques to optimize HBM simulation performance.

## Understanding Performance Bottlenecks

### Key Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Requests/second | > 10K req/s | Throughput |
| Memory/stack | < 100MB | Memory usage |
| Simulation cycles | Minimal | Efficiency |
| Queue depth | Optimal | Latency |

### Bottleneck Categories

1. **Queue Management**: Excessive queue operations
2. **Bank Conflict**: Too many bank conflicts
3. **Refresh Overhead**: Refresh blocking command pipeline
4. **Channel Imbalance**: Uneven channel utilization

## Optimization Techniques

### 1. Batch Request Processing

```python
from model.controller.request import HBMRequestBatch

# Instead of processing one request at a time
for request in single_requests:
    controller.submit_request(request)

# Process in batches
batch = HBMRequestBatch(requests=single_requests, max_size=32)
controller.submit_batch(batch)
```

### 2. Object Pooling

```python
from model.controller.request import HBMRequestPool

# Create request pool to reduce allocation overhead
pool = HBMRequestPool(max_size=1000)

# Get request from pool (reuse instead of allocate)
request = pool.acquire()
request.addr = 0x1000
request.is_read = True

controller.submit_request(request)
pool.release(request)  # Return to pool
```

### 3. Queue Depth Tuning

```python
from model.controller.queue import QueueManager

# Balance queue depth vs memory usage
config = QueueManager.create(
    queue_depth=256,      # Default: 256
    # Too shallow: drops requests
    # Too deep: memory overhead
)

# For high throughput, increase depth
high_throughput_config = QueueManager.create(
    queue_depth=512,
)
```

### 4. Multi-Channel Optimization

```python
from model.multi_channel import AdaptiveLoadBalancer

# Use adaptive balancing for optimal channel utilization
balancer = AdaptiveLoadBalancer(
    num_channels=32,
    strategy="queue_aware",
    rebalance_interval=100,  # Rebalance every 100 cycles
)

# Monitor channel balance
stats = balancer.get_fairness_metrics()
if stats['jains_fairness_index'] < 0.8:
    print("Warning: Poor load balance detected")
```

### 5. Cache Frequently Accessed Data

```python
class OptimizedController:
    def __init__(self):
        self._spec = HBM4Spec()  # Cache spec
        self._timing_cache = {}  # Cache timing calculations
        self._addr_cache = {}    # Cache address decoding

    def decode_address(self, addr):
        if addr not in self._addr_cache:
            self._addr_cache[addr] = self._decoder.decode(addr)
        return self._addr_cache[addr]
```

### 6. Reduce Refresh Overhead

```python
from model.controller.hbm4_refresh_scheduler import RefreshMode

# Use per-bank refresh to reduce blocking
scheduler = HBM4RefreshScheduler(
    config=spec,
    mode=RefreshMode.PER_BANK,  # vs ALL_BANK
    stagger_refresh=True,
)

# Or use autonomous refresh
scheduler = HBM4RefreshScheduler(
    config=spec,
    mode=RefreshMode.AUTONOMOUS,
)
```

## Simulation Speed Optimization

### 1. Fast Forward Mode

```python
from sim.simulator import SimulationConfig, SimulationMode

config = SimulationConfig(
    mode=SimulationMode.FAST_FORWARD,  # Skip detailed timing
    fast_forward_cycles=10000,
)
```

### 2. Reduce Simulation Detail

```python
# Disable detailed state tracking for quick runs
config = SimulationConfig(
    track_bank_states=False,  # Skip bank state tracking
    track_power=False,        # Skip power calculation
    track_thermal=False,      # Skip thermal modeling
)
```

### 3. Parallel Simulation

```python
from concurrent.futures import ProcessPoolExecutor

def run_simulation(params):
    sim = HBMSimulator(params)
    return sim.run()

# Run multiple simulations in parallel
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(run_simulation, p) for p in param_sets]
    results = [f.result() for f in futures]
```

## Memory Optimization

### 1. Use __slots__

```python
# Instead of this
class Request:
    def __init__(self):
        self.addr = 0
        self.is_read = True

# Use this
class Request:
    __slots__ = ['addr', 'is_read', 'qos', 'state']

    def __init__(self):
        self.addr = 0
        self.is_read = True
```

### 2. Lazy Initialization

```python
class LazyController:
    def __init__(self):
        self._dram = None  # Deferred initialization
        self._spec = HBM4Spec()

    @property
    def dram(self):
        if self._dram is None:
            self._dram = DRAMModel(spec=self._spec)
        return self._dram
```

### 3. Memory-mapped Statistics

```python
import numpy as np

class EfficientStats:
    def __init__(self, num_channels=32):
        # Use numpy arrays instead of Python lists
        self.request_counts = np.zeros(num_channels, dtype=np.uint32)
        self.latencies = np.zeros(num_channels, dtype=np.float32)
```

## Benchmarking Performance

### Performance Benchmark Script

```python
from model.benchmark.benchmark_runner import BenchmarkRunner, BenchmarkConfig

config = BenchmarkConfig(
    warmup_cycles=1000,
    measure_cycles=10000,
    iterations=5,
)

runner = BenchmarkRunner(config)

# Run benchmarks
results = runner.run([
    ('controller', test_controller),
    ('multi_channel', test_multi_channel),
    ('dram', test_dram_model),
])

# Print results
for name, result in results.items():
    print(f"{name}: {result.throughput:.0f} req/s")
```

### Key Performance Indicators

```python
class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss

    def report(self, request_count):
        elapsed = time.time() - self.start_time
        memory_used = psutil.Process().memory_info().rss - self.start_memory

        throughput = request_count / elapsed
        memory_per_req = memory_used / request_count

        print(f"Throughput: {throughput:.0f} req/s")
        print(f"Memory/request: {memory_per_req:.0f} bytes")
```

## Configuration Recommendations

### High Performance Mode

```python
HIGH_PERF_CONFIG = {
    # Controller
    'queue_depth': 512,
    'batch_size': 32,
    'request_pool_size': 2000,

    # Multi-channel
    'num_channels': 32,
    'balance_strategy': 'adaptive',
    'rebalance_interval': 100,

    # DRAM
    'track_bank_states': True,
    'track_power': False,  # Disable for speed
    'track_thermal': False,

    # Simulation
    'mode': 'fast',
    'parallel_channels': 4,
}
```

### Balanced Mode

```python
BALANCED_CONFIG = {
    # Controller
    'queue_depth': 256,
    'batch_size': 16,
    'request_pool_size': 1000,

    # Multi-channel
    'num_channels': 32,
    'balance_strategy': 'adaptive',
    'rebalance_interval': 200,

    # DRAM
    'track_bank_states': True,
    'track_power': True,
    'track_thermal': False,

    # Simulation
    'mode': 'balanced',
    'parallel_channels': 2,
}
```

### Accurate Mode

```python
ACCURATE_CONFIG = {
    # Controller
    'queue_depth': 256,
    'batch_size': 8,
    'request_pool_size': 500,

    # Multi-channel
    'num_channels': 32,
    'balance_strategy': 'lru',
    'rebalance_interval': 50,

    # DRAM
    'track_bank_states': True,
    'track_power': True,
    'track_thermal': True,

    # Simulation
    'mode': 'accurate',
    'parallel_channels': 1,
}
```

## Profiling and Debugging

### Profile Memory Access

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run simulation
sim = HBMSimulator(config)
sim.run()

profiler.disable()

# Print top functions by cumulative time
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Memory Profiling

```python
import tracemalloc

tracemalloc.start()

# Run simulation
sim = HBMSimulator(config)
sim.run()

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1e6:.2f} MB")
print(f"Peak: {peak / 1e6:.2f} MB")

tracemalloc.stop()
```

## Summary Checklist

- [ ] Enable batch request processing
- [ ] Use object pooling for requests
- [ ] Tune queue depth for workload
- [ ] Enable adaptive load balancing
- [ ] Use per-bank refresh when possible
- [ ] Disable unnecessary tracking (power/thermal)
- [ ] Use fast-forward for warmup
- [ ] Profile and identify bottlenecks
- [ ] Iterate and validate improvements

## Next Steps

- [Advanced Features](advanced_features.md) - Learn about multi-channel, QoS, and signal integrity
- [Getting Started](getting_started.md) - Basic usage tutorial
- [API Reference](../api/) - Detailed API documentation