# Advanced Features Tutorial

This tutorial covers advanced features of the HBM System Modeling Platform.

## Multi-Channel Load Balancing

HBM4 features 32 independent channels. Load balancing distributes traffic efficiently across channels.

### Channel Selection Strategies

```python
from model.multi_channel import ChannelSelector, AdaptiveLoadBalancer

# Strategy 1: Round Robin (simple, fair distribution)
selector = ChannelSelector(
    num_channels=32,
    strategy=ChannelSelector.ROUND_ROBIN
)

# Strategy 2: Random (good for uniform traffic)
selector = ChannelSelector(
    num_channels=32,
    strategy=ChannelSelector.RANDOM
)

# Strategy 3: Least Recently Used (optimizes row hits)
selector = ChannelSelector(
    num_channels=32,
    strategy=ChannelSelector.LRU
)

# Strategy 4: Adaptive (queue-aware, best overall)
selector = ChannelSelector(
    num_channels=32,
    strategy=ChannelSelector.ADAPTIVE
)

# Select channel for address
channel_id = selector.select_channel(address=0x1234_5678_9ABC_DEF0)
```

### Adaptive Load Balancing

```python
from model.multi_channel import AdaptiveLoadBalancer, MultiChannelStats

balancer = AdaptiveLoadBalancer(
    num_channels=32,
    strategy="queue_aware",
    load_threshold=0.8,  # 80% threshold for rebalancing
)

# Add request to specific channel
balancer.add_request(channel_id=5, request=request)

# Check load balance
stats = balancer.get_statistics()
print(f"Jain's fairness index: {stats.jains_fairness_index:.3f}")
print(f"Channel variance: {stats.channel_variance:.3f}")

# Get fairness metrics
fairness = balancer.get_fairness_metrics()
print(f"Max channel load: {fairness['max_load']:.3f}")
print(f"Min channel load: {fairness['min_load']:.3f}")
```

### Per-Channel Statistics

```python
from model.multi_channel import MultiChannelStats, ChannelStats

stats = MultiChannelStats(num_channels=32)

# Record request per channel
stats.record_request(channel_id=0, is_read=True, latency_ns=45.0)
stats.record_request(channel_id=1, is_read=False, latency_ns=52.0)

# Get per-channel metrics
for ch in range(32):
    ch_stats = stats.get_channel_stats(ch)
    print(f"Channel {ch}:")
    print(f"  Requests: {ch_stats.request_count}")
    print(f"  Throughput: {ch_stats.throughput_gbps:.2f} GB/s")
    print(f"  Avg latency: {ch_stats.avg_latency_ns:.2f} ns")
```

## QoS Scheduling

16-level priority scheduling with bandwidth guarantees.

### QoS Configuration

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel

# Create scheduler with bandwidth guarantees
scheduler = HBM4QoSScheduler(
    config=spec,
    enable_bandwidth_guarantees=True,
    min_bandwidth_percent={15: 50, 12: 30, 8: 15, 4: 5, 0: 0},
)

# Submit requests with different QoS levels
requests = [
    HBMRequest(addr=0x1000, qos=15, is_read=True),   # Critical: 50% min
    HBMRequest(addr=0x2000, qos=12, is_read=True),   # High: 30% min
    HBMRequest(addr=0x3000, qos=8, is_read=True),    # Normal: 15% min
    HBMRequest(addr=0x4000, qos=4, is_read=True),    # Low: 5% min
]

# Select next request based on priority
selected = scheduler.select_next(requests)
```

### QoS Anti-Starvation

```python
from model.controller.hbm4_qos_scheduler import (
    HBM4QoSScheduler,
    QoSLevel,
    AntiStarvationConfig
)

config = AntiStarvationConfig(
    enabled=True,
    max_wait_cycles=1000,  # Max cycles a request can wait
    boost_threshold=0.5,   # Boost priority after 50% of max wait
)

scheduler = HBM4QoSScheduler(config=spec, anti_starvation=config)

# Requests that wait too long get boosted priority
```

## Signal Integrity Analysis

### TX Pre-emphasis Configuration

```python
from model.phy.signal_integrity import TXPreEmphasis, SignalIntegrityConfig

# Create TX with configurable taps
config = SignalIntegrityConfig(
    sample_rate=32e9,
    ui_ns=0.125,  # 8 Gbps
)

tx = TXPreEmphasis(config=config)

# Configure FIR taps (pre-cursor, main, post-cursor)
tx.set_taps(pre_cursor=-0.2, main_cursor=1.0, post_cursor=-0.1)

# Apply to signal
output_signal = tx.equalize(input_signal)

# Generate eye diagram
eye_data = tx.estimate_tx_eye(prbs_length=1024)
```

### RX CTLE Configuration

```python
from model.phy.signal_integrity import RXCTLE, CTLEConfig

# Create CTLE with peaking frequency control
ctle = RXCTLE(config=config)

# Configure CTLE parameters
ctle.set_peaking_freq(freq_ghz=4.0)  # Peaking frequency
ctle.set_gain(gain_db=6.0)            # DC gain
ctle.set_bandwidth(bw_ghz=8.0)       # Bandwidth limit

# Equalize received signal
equalized = ctle.equalize(rx_signal)
```

### DFE Configuration

```python
from model.phy.signal_integrity import DFE, DFEConfig

# Create DFE with tap count
dfe = DFE(config=config, num_taps=5)

# Configure DFE taps
for i in range(5):
    dfe.set_tap(index=i, value=0.1 / (i + 1))  # Decreasing taps

# Equalize with DFE feedback
equalized = dfe.equalize(rx_signal, decisions=previous_decisions)
```

### IBIS Model Simulation

```python
from model.phy.ibis_simulator import IBISSimulator, IBISModel

# Load IBIS model from file
ibis = IBISSimulator(ibis_file="path/to/model.ibis")

# Generate eye diagram at specific data rate
eye_data = ibis.generate_eye_diagram(
    data_rate=8e9,
    num_samples=10000,
    pattern="PRBS31",
)

# Get waveform for specific corner
waveform = ibis.get_waveform(
    corner="typical",
    temperature=25,
    voltage=1.1,
)
```

### Eye Diagram Analysis

```python
from model.phy.eye_analyzer import EyeAnalyzer, EyeMetrics

# Create analyzer
analyzer = EyeAnalyzer()

# Analyze eye diagram
metrics = analyzer.analyze_eye(eye_data)

print(f"Eye width: {metrics.eye_width_ns:.3f} ns")
print(f"Eye height: {metrics.eye_height_mv:.3f} mV")
print(f"SNR: {metrics.snr_db:.2f} dB")
print(f"Bert BER estimate: {metrics.ber_estimate:.2e}")

# Get bathtub curve
bathtub = analyzer.get_bathtub_curve(num_points=100)
```

## DFI Interface

### DFI Command Encoding

```python
from model.dram.dfi_interface import DFI5Interface, DFICommand, DFIRequest

# Create DFI interface
dfi = DFI5Interface()

# Encode DRAM command to DFI request
dfi_req = dfi.encode_command(
    command=DFICommand.ACT,
    params={
        'row': 0x100,
        'bank': 0,
        'pseudo_channel': 0,
    },
    priority=8,
)

# Queue request
dfi.queue_request(dfi_req)

# Process cycle
dfi.tick()

# Check if PHY is ready
ready = dfi.is_ready()
```

### DFI Low Power States

```python
from model.dram.dfi_interface import DFILowPowerState

# Enter low power mode
dfi.enter_low_power_state(DFILowPowerState.LP_DATA)

# Check state
state = dfi.get_current_state()
print(f"Current state: {state}")

# Exit low power mode
dfi.exit_low_power_state()
```

## Lane Repair

```python
from model.dram.lane_repair import LaneRepair, RepairMap

# Create lane repair manager
repair = LaneRepair(num_lanes=128)

# Mark failed lanes
repair.mark_failed_lane(lane_id=5)
repair.mark_failed_lane(lane_id=42)

# Get repair mapping
repair_map = repair.get_repair_map()

# Apply repair to address
repaired_addr = repair.apply_repair_mapping(address, repair_map)

# Check if repair available
has_repair = repair.has_repair_for(lane_id=5)
```

## ECC/CRC

```python
from model.dram.ecc_crc import ECCEngine, ECCConfig

# Create ECC engine
config = ECCConfig(
    ecc_enabled=True,
    crc_enabled=True,
    ecc_bits=8,  # 8-bit ECC for 256-bit data
)

engine = ECCEngine(config=config)

# Encode data with ECC
data = bytes([0xFF] * 32)
encoded = engine.encode(data)

# Decode and detect errors
decoded, errors = engine.decode(encoded)

if errors.corrected > 0:
    print(f"Corrected {errors.corrected} bit errors")
if errors.detected > 0:
    print(f"Detected {errors.detected} uncorrectable errors")
```

## Next Steps

- [Performance Tuning](performance_tuning.md) - Optimize simulation performance
- [Getting Started](getting_started.md) - Basic usage tutorial
- [API Reference](../api/) - Detailed API documentation