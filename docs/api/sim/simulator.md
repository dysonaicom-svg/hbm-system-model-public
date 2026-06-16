# HBMSimulator API

End-to-end HBM system simulation framework with cycle-accurate modeling.

## Class: HBMSimulator

```python
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
```

### Constructor

```python
def __init__(self, sim_config: SimulationConfig)
```

**Parameters:**
- `sim_config`: Simulation configuration

### Simulation Configuration

```python
@dataclass
class SimulationConfig:
    # Clock configuration
    clock_freq_hz: float = 1.28e9      # 1.28 GHz
    simulation_time_us: float = 100.0  # Simulation time (us)

    # Traffic configuration
    traffic_pattern: TrafficPattern = TrafficPattern.RANDOM
    request_rate: float = 0.5           # 0-1
    read_ratio: float = 0.7             # Read ratio
    burst_size: int = 64               # Burst size

    # Multi-request configuration
    max_requests_per_cycle: int = 4     # Max requests per cycle

    # Address configuration
    address_range: int = 0x400000000000  # 64TB address space
    stride_value: int = 4096              # Stride for stride pattern

    # Queue configuration
    queue_depth: int = 512
    max_outstanding: int = 256

    # Simulation options
    enable_logging: bool = False
    enable_stats: bool = True
    seed: Optional[int] = None
```

### Traffic Patterns

```python
class TrafficPattern(Enum):
    RANDOM = "random"       # Random address access
    SEQUENTIAL = "sequential"  # Sequential access
    STRIDE = "stride"       # Strided access
    HOT_SPOT = "hot_spot"   # Hot spot access (80% to hot spot)
    ADDR_SCATTER = "scatter"  # Scattered access
```

---

## Methods

### run()

Run simulation to completion.

```python
def run(self) -> SimulationStats
```

**Returns:** Simulation statistics

**Example:**
```python
config = SimulationConfig(
    simulation_time_us=100.0,
    traffic_pattern=TrafficPattern.RANDOM,
    request_rate=0.5,
)
sim = HBMSimulator(config)
stats = sim.run()

print(f"Completed: {stats.completed_requests}")
print(f"Throughput: {stats.throughput_gbps:.2f} GB/s")
```

### run_verbose()

Run simulation with detailed output.

```python
def run_verbose(self) -> SimulationStats
```

**Returns:** Simulation statistics

**Example:**
```python
stats = sim.run_verbose()
# Prints detailed statistics to console
```

### step()

Execute one simulation cycle.

```python
def step(self) -> Optional[HBMResponse]
```

**Returns:** HBMResponse if a request completed this cycle

### get_stats()

Get current statistics.

```python
def get_stats(self) -> SimulationStats
```

---

## Load Balancing Methods

### get_jains_fairness_index()

Calculate Jain's fairness index for channel distribution.

```python
def get_jains_fairness_index(self) -> float
```

**Returns:** Fairness index between 0 and 1 (1 = perfect fairness)

### get_load_balance_score()

Calculate load balance score (0-1, 1=perfect balance).

```python
def get_load_balance_score(self) -> float
```

### get_load_balance_metrics()

Get comprehensive load balance metrics.

```python
def get_load_balance_metrics(self) -> Dict[str, float]
```

**Returns:**
```python
{
    'jains_fairness_index': float,
    'load_balance_score': float,
    'load_std_dev': float,
    'load_variance': float,
    'load_spread': int,
    'min_load': int,
    'max_load': int,
    'active_channels': int,
    'completed_fairness': float,
    'channel_variance_percent': float,
    'per_channel_distribution': Dict[int, int],
}
```

### get_channel_stats()

Get per-channel statistics.

```python
def get_channel_stats(self) -> Dict[int, ChannelStats]
```

---

## Statistics

### SimulationStats Properties

| Property | Type | Description |
|----------|------|-------------|
| `total_cycles` | int | Total simulation cycles |
| `total_requests` | int | Total requests submitted |
| `completed_requests` | int | Requests completed |
| `read_requests` | int | Read requests |
| `write_requests` | int | Write requests |
| `row_hit_rate` | float | Row buffer hit rate |
| `avg_latency` | float | Average latency (cycles) |
| `throughput_gbps` | float | Throughput (GB/s) |
| `efficiency` | float | System efficiency |
| `bandwidth_efficiency` | float | Bandwidth efficiency |
| `per_channel_stats` | Dict | Per-channel statistics |

### Throughput Metrics

```python
@property
def throughput_gbps(self) -> float:
    """Aggregate throughput considering pipelined operations"""

@property
def effective_bandwidth_gbps(self) -> float:
    """Effective bandwidth from actual DRAM operations"""

@property
def peak_bandwidth_gbps(self) -> float:
    """Theoretical peak bandwidth"""

@property
def pipelined_throughput_gbps(self) -> float:
    """Pipelined throughput accounting for multi-channel parallelism"""
```

---

## Usage Example

```python
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

# Create configuration
config = SimulationConfig(
    simulation_time_us=100.0,
    traffic_pattern=TrafficPattern.RANDOM,
    request_rate=0.5,
    read_ratio=0.7,
    max_requests_per_cycle=4,
)

# Create simulator
sim = HBMSimulator(config)

# Run simulation
stats = sim.run_verbose()

# Get load balance metrics
metrics = sim.get_load_balance_metrics()
print(f"Jain's fairness index: {metrics['jains_fairness_index']:.3f}")
print(f"Channel variance: {metrics['channel_variance_percent']:.1f}%")

# Check per-channel distribution
for ch, count in metrics['per_channel_distribution'].items():
    print(f"Channel {ch}: {count} requests")
```

---

## Performance Benchmarks

| Metric | Target | Description |
|--------|--------|-------------|
| `sim_speed_L0` | > 10M req/s | Functional mode |
| `sim_speed_L1` | > 1M req/s | Transaction mode |
| `sim_speed_L2` | > 100K req/s | Timing-approx mode |
| `sim_speed_L3` | > 10K req/s | Timing-accurate mode |
| `memory_per_stack` | < 100MB | Memory footprint |