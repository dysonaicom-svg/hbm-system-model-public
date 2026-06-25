# HBM4UnifiedSimulator API

Integrated simulator combining all HBM4 components including Logic Base Die, PAM3, DFI 5.0, ECC, and RTL co-simulation.

## Class: HBM4UnifiedSimulator

```python
from sim.hbm4_unified_simulator import HBM4UnifiedSimulator, SimulationConfig, SimulationMode
```

### Constructor

```python
def __init__(self, config: SimulationConfig)
```

**Parameters:**
- `config`: Simulation configuration

### Configuration

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

**Simulation Modes:**
```python
class SimulationMode(Enum):
    QUICK = auto()       # Quick functional test
    FULL = auto()        # Full timing simulation
    STRESS = auto()      # Stress test all channels
    BENCHMARK = auto()   # Performance benchmark
```

---

## Core Methods

### initialize()

Initialize simulation (runs PHY training ~2000 cycles).

```python
def initialize(self)
```

### tick()

Advance one cycle.

```python
def tick(self)
```

### run()

Run simulation based on configured mode.

```python
def run(self) -> SimulationStats
```

**Returns:** Simulation statistics

### process_command()

Process a memory command.

```python
def process_command(
    self,
    channel: int,
    command: str,
    address: int,
    data: Optional[int] = None,
) -> Tuple[bool, str]
```

**Parameters:**
- `channel`: Channel ID (0-31)
- `command`: Command type (ACT, RD, WR, PRE, REF, etc.)
- `address`: Memory address
- `data`: Write data (for WR commands)

**Returns:** (success, message)

**Example:**
```python
simulator = HBM4UnifiedSimulator(config)

# Initialize
simulator.initialize()

# Process commands
simulator.process_command(channel=0, command='ACT', address=0x1000)
simulator.process_command(channel=0, command='RD', address=0x1000)
```

---

## PAM3 Methods

### process_pam3_sequence()

Process PAM3 encoding/decoding sequence.

```python
def process_pam3_sequence(
    self,
    data: int,
    dq_width: int = 128,
) -> List[PAM3Symbol]
```

**Parameters:**
- `data`: Data to encode
- `dq_width`: DQ bus width

**Returns:** PAM3 symbol list

---

## State and Statistics

### get_channel_state()

Get state of a specific channel.

```python
def get_channel_state(self, channel: int) -> Dict[str, Any]
```

### get_stats()

Get simulation statistics.

```python
def get_stats(self) -> Dict[str, Any]
```

**Returns:**
```python
{
    'total_cycles': int,
    'commands_processed': int,
    'pam3_symbols_encoded': int,
    'pam3_symbols_decoded': int,
    'errors_detected': int,
    'errors_corrected': int,
    'lanes_repaired': int,
    'power_mW': float,
    'duration_s': float,
    'throughput': float,
    'channel_stats': Dict[int, Dict],
    'rtl_cosim': {...},
    'gem5_cosim': {...},
}
```

---

## RTL Co-Simulation

### enable_rtl_cosimulation()

Enable RTL co-simulation with Verilator.

```python
def enable_rtl_cosimulation(
    self,
    enable_rtl: bool = True,
    compare_results: bool = True,
    trace_enabled: bool = False,
)
```

**Parameters:**
- `enable_rtl`: Enable RTL simulation
- `compare_results`: Compare Python vs RTL results
- `trace_enabled`: Enable transaction tracing

**Example:**
```python
simulator.enable_rtl_cosimulation(
    enable_rtl=True,
    compare_results=True,
    trace_enabled=True
)
```

### disable_rtl_cosimulation()

Disable RTL co-simulation.

```python
def disable_rtl_cosimulation(self)
```

---

## gem5 Co-Simulation

### enable_gem5_cosimulation()

Enable gem5 co-simulation.

```python
def enable_gem5_cosimulation(
    self,
    gem5_home: Optional[str] = None,
    cache_line_size: int = 64,
    default_latency: int = 10,
)
```

**Parameters:**
- `gem5_home`: gem5 installation path
- `cache_line_size`: Cache line size (64 or 128 bytes)
- `default_latency`: Default latency in cycles

**Example:**
```python
# Mock mode (no gem5 required)
simulator.enable_gem5_cosimulation()

# Full integration
simulator.enable_gem5_cosimulation(
    gem5_home="/path/to/gem5",
    cache_line_size=64,
)
```

### disable_gem5_cosimulation()

Disable gem5 co-simulation.

```python
def disable_gem5_cosimulation(self)
```

### send_gem5_request()

Send memory request through gem5 bridge.

```python
def send_gem5_request(
    self,
    addr: int,
    size: int = 64,
    is_write: bool = False,
    data: Optional[List[int]] = None,
    qos: int = 8,
) -> Optional[int]
```

**Returns:** Request ID

### recv_gem5_response()

Receive gem5 response.

```python
def recv_gem5_response(
    self,
    req_id: Optional[int] = None,
    timeout_cycles: int = 10000,
) -> Optional[Gem5Response]
```

### gem5_read()

Convenience method for reading memory.

```python
def gem5_read(
    self,
    addr: int,
    size: int = 64,
    qos: int = 8,
) -> Optional[List[int]]
```

### gem5_write()

Convenience method for writing memory.

```python
def gem5_write(
    self,
    addr: int,
    data: List[int],
    size: int = 64,
    qos: int = 8,
) -> bool
```

### get_gem5_stats()

Get gem5 co-simulation statistics.

```python
def get_gem5_stats(self) -> Dict[str, Any]
```

---

## Statistics Class

```python
@dataclass
class SimulationStats:
    total_cycles: int = 0
    commands_processed: int = 0
    pam3_symbols_encoded: int = 0
    pam3_symbols_decoded: int = 0
    errors_detected: int = 0
    errors_corrected: int = 0
    lanes_repaired: int = 0
    power_mW: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    channel_stats: Dict[int, Dict[str, int]] = {}
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `duration_s` | float | Simulation duration (seconds) |
| `throughput` | float | Commands per second |
| `rtl_match_rate` | float | RTL comparison match rate |

---

## Usage Examples

### Quick Start

```python
from sim.hbm4_unified_simulator import (
    HBM4UnifiedSimulator,
    SimulationConfig,
    SimulationMode,
)

# Create configuration
config = SimulationConfig(
    mode=SimulationMode.QUICK,
    num_channels=8,
    cycles=1000,
    speed_grade="16Gbps",
)

# Create simulator
simulator = HBM4UnifiedSimulator(config)

# Run
stats = simulator.run()

# Print results
print(f"Commands: {stats.commands_processed}")
print(f"Power: {stats.power_mW:.2f} mW")
```

### Full Simulation with RTL Co-Simulation

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
    speed_grade="16Gbps",
)

simulator = HBM4UnifiedSimulator(config)

# Enable RTL co-simulation
simulator.enable_rtl_cosimulation(
    enable_rtl=True,
    compare_results=True,
)

# Run simulation
stats = simulator.run()

# Check RTL match rate
print(f"RTL match rate: {stats.rtl_match_rate:.2%}")
```

### gem5 Integration

```python
simulator.enable_gem5_cosimulation(
    cache_line_size=64,
    default_latency=10,
)

# Send requests
req_id = simulator.send_gem5_request(
    addr=0x1000,
    size=64,
    is_write=False,
    qos=8,
)

# Receive response
response = simulator.recv_gem5_response(req_id=req_id)
if response:
    print(f"Latency: {response.latency} cycles")
```

### Stress Test

```python
config = SimulationConfig(
    mode=SimulationMode.STRESS,
    num_channels=32,
)

simulator = HBM4UnifiedSimulator(config)
stats = simulator.run()

# Check per-channel distribution
for ch, ch_stats in stats.channel_stats.items():
    print(f"Channel {ch}: {ch_stats}")
```

---

## Command Line Interface

```bash
# Quick test (8 channels)
python -m sim.hbm4_unified_simulator --mode quick --channels 8

# Full simulation (32 channels)
python -m sim.hbm4_unified_simulator --mode full --channels 32 --cycles 10000

# Stress test
python -m sim.hbm4_unified_simulator --mode stress --verbose

# Benchmark
python -m sim.hbm4_unified_simulator --mode benchmark

# With PAM3 disabled
python -m sim.hbm4_unified_simulator --mode full --no-pam3

# With gem5 integration
python -m sim.hbm4_unified_simulator --mode full --gem5

# High speed grade
python -m sim.hbm4_unified_simulator --mode full --speed-grade 16Gbps
```

**Arguments:**
| Argument | Default | Description |
|----------|---------|-------------|
| `--mode` | quick | Simulation mode |
| `--channels` | 32 | Number of channels |
| `--cycles` | 1000 | Cycle count |
| `--speed-grade` | 8Gbps | Speed grade (8/12/16 Gbps) |
| `--no-pam3` | - | Disable PAM3 encoding |
| `--no-ecc` | - | Disable ECC |
| `--no-lane-repair` | - | Disable lane repair |
| `--trace` | - | Enable command tracing |
| `--gem5` | - | Enable gem5 co-simulation |
| `--gem5-home` | - | gem5 installation path |
| `--gem5-cache-line` | 64 | Cache line size |
| `--gem5-latency` | 10 | Default latency |
| `--verbose` | - | Verbose output |
