# gem5 Integration for HBM System Modeling

This directory provides integration between the Python HBM model and gem5 simulator.

## Overview

The gem5 integration enables:
1. **gem5 as traffic generator**: Use gem5 workloads to drive the Python HBM model
2. **Python model as timing reference**: Accurate HBM timing for gem5 simulations
3. **Co-simulation**: Run both simulators in parallel with request/response exchange
4. **Validation**: Compare results between gem5 and Python model

## Directory Structure

```
integration/gem5/
├── hbm4_config.py              # HBM4 configuration for gem5
├── bridge.py                   # Python-gem5 bridge module
├── gem5_hbm4_example.py       # Example gem5 simulation script
├── python_model_integration.py # Python model with bridge interface
└── README.md                   # This file
```

## Prerequisites

### gem5 Installation

gem5 must be installed on your system. Install from source:

```bash
# Clone gem5 repository
git clone https://github.com/gem5/gem5.git
cd gem5

# Build with HBM support
scons build/GEM5_X86.opt -j$(nproc)
```

### Python Dependencies

```bash
pip install numpy scipy
```

## Usage

### 1. Standalone Python Model

Run the Python HBM model independently:

```bash
python integration/gem5/python_model_integration.py \
    --mode standalone \
    --pattern random \
    --duration 100 \
    --rate 0.5
```

### 2. gem5 Bridge Mode

Connect Python model to gem5 via bridge:

```bash
python integration/gem5/python_model_integration.py \
    --mode bridge \
    --sync-interval 100 \
    --num-requests 1000
```

### 3. Benchmark Mode

Run scaling benchmarks:

```bash
python integration/gem5/python_model_integration.py \
    --mode benchmark \
    --duration 50
```

### 4. gem5 Simulation

Run gem5 with HBM4 memory system:

```bash
# Example: 4-core system with HBM4 8-channel
python integration/gem5/gem5_hbm4_example.py \
    --cpu-type=TimingSimpleCPU \
    --num-cpus=4 \
    --hbm-config=hbm4_8ch \
    --binary=/path/to/test_binary
```

## Configuration Presets

| Preset | Channels | Data Rate | Peak BW | Description |
|--------|----------|-----------|---------|-------------|
| `hbm4_32ch` | 32 | 8.0 GT/s | ~3.2 TB/s | HBM4 full config |
| `hbm4_16ch` | 16 | 8.0 GT/s | ~1.6 TB/s | HBM4 half config |
| `hbm4_8ch` | 8 | 8.0 GT/s | ~819 GB/s | HBM4 half channels |
| `hbm3_8ch` | 8 | 6.4 GT/s | ~819 GB/s | HBM3 legacy |

## Bridge Interface

### MemoryRequest Structure

```python
@dataclass
class MemoryRequest:
    request_id: int           # Unique request ID
    request_type: RequestType # READ, WRITE, REFRESH
    addr: int                 # Memory address (64-bit)
    length: int               # Request length in bytes
    data: Optional[bytes]     # Write data
    qos: int                  # QoS priority (0-15)
    timestamp: float          # Request timestamp
```

### MemoryResponse Structure

```python
@dataclass
class MemoryResponse:
    request_id: int           # Matches request ID
    status: str              # "OK", "ERROR", "TIMEOUT"
    latency: float          # Latency in nanoseconds
    data: Optional[bytes]    # Read data
    timestamp: float         # Response timestamp
```

### Sync Interface

```python
# Create bridge
bridge = HBMBridge(config=BridgeConfig(sync_interval_cycles=100))

# Enable bridge
bridge.enable()

# In simulation loop:
for cycle in range(max_cycles):
    # Submit requests from gem5
    for req in gem5_requests:
        bridge.submit_request(req)

    # Sync at regular intervals
    if cycle % bridge.config.sync_interval_cycles == 0:
        bridge.sync(cycle)

    # Collect responses
    while not bridge._response_queue.empty():
        resp = bridge._response_queue.get_nowait()
        send_to_gem5(resp)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         gem5 Simulator                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐   │
│  │   CPU   │→ │  Cache  │→ │  MEM Ctrl│→ │  HBM Controller │   │
│  └─────────┘  └─────────┘  └─────────┘  └────────┬────────┘   │
└────────────────────────────────────────────────────┼────────────┘
                                                     │
                              ┌──────────────────────┴──────────────┐
                              │              Bridge                 │
                              │  ┌────────────┐  ┌────────────┐   │
                              │  │ gem5→Python│  │Python→gem5│   │
                              │  └────────────┘  └────────────┘   │
                              └──────────────────────┬────────────┘
                                                     │
┌────────────────────────────────────────────────────┼────────────────┐
│                     Python HBM Model                │                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  │                │
│  │ Controller │→ │   DRAM     │→ │  Stats     │  │                │
│  │   (FR-FCFS)│  │   Model    │  │  Collector │←┘                │
│  └────────────┘  └────────────┘  └────────────┘                   │
└───────────────────────────────────────────────────────────────────┘
```

## Timing Parameters

### HBM4 Timing (JEDEC Draft)

| Parameter | Value | Unit | Description |
|-----------|-------|------|-------------|
| tCK | 125 | ps | Clock period |
| tRCD | 16 | cycles | RAS to CAS delay |
| tRP | 16 | cycles | Precharge command period |
| tRAS | 40 | cycles | RAS active time |
| tRC | 56 | cycles | Row cycle time |
| tCCD | 4 | cycles | CAS to CAS delay |
| tRRD | 4 | cycles | Row to row delay |
| tFAW | 20 | cycles | Four-bank activation window |

## Limitations

1. **gem5 not installed**: If gem5 is not available, use standalone Python mode
2. **Bridge synchronization**: Requires careful timing alignment between simulators
3. **Memory coherence**: Only NUMA-style memory is modeled, no cache coherence

## Future Work

- [ ] gem5 DPRINTF integration for debug output
- [ ] Full HBM4 channel model in gem5
- [ ] Power/thermal modeling integration
- [ ] Multi-stack support with proper routing

## References

- [gem5 Memory System](https://www.gem5.org/documentation/general_docs/memory_system/)
- [JEDEC HBM4 Draft Specification](https://www.jedec.org/standards-documents)
- [gem5 HBM Controller](https://github.com/gem5/gem5/tree/master/src/mem/dram)