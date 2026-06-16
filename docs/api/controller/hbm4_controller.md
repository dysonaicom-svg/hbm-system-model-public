# HBM4Controller API

Main controller integration for HBM4 memory systems.

## Class: HBM4Controller

```python
from model.controller.hbm4_controller import HBM4Controller
```

### Constructor

```python
def __init__(
    self,
    spec: Optional[HBM4Spec] = None,
    config: Optional[HBMConfig] = None,
    enable_qos: bool = True,
    enable_refresh: bool = True,
    enable_dfi: bool = True,
)
```

**Parameters:**
- `spec`: HBM4 specification (uses default if None)
- `config`: Optional HBMConfig for base class compatibility
- `enable_qos`: Enable QoS scheduling (default: True)
- `enable_refresh`: Enable refresh scheduling (default: True)
- `enable_dfi`: Enable DFI 5.0 interface (default: True)

### Methods

#### submit_request()

Submit a memory request to the controller.

```python
def submit_request(
    self,
    addr: int,
    is_read: bool,
    qos_level: int = 8,
    size_bytes: int = 64,
) -> Optional[str]
```

**Parameters:**
- `addr`: 64-bit physical address
- `is_read`: True for read, False for write
- `qos_level`: QoS priority level (0-15, higher = higher priority)
- `size_bytes`: Request size in bytes (default: 64)

**Returns:** Request ID if successful, None if queue full

**Example:**
```python
request_id = controller.submit_request(
    addr=0x0001_0000_0000_0000,
    is_read=True,
    qos_level=8,
    size_bytes=64,
)
```

#### tick()

Execute one clock cycle.

```python
def tick(self) -> List[HBMResponse]
```

**Returns:** List of completed responses this cycle

**Example:**
```python
for _ in range(1000):
    responses = controller.tick()
    for resp in responses:
        print(f"Completed: {resp.request_id}, latency={resp.latency}ns")
```

#### get_stats()

Get comprehensive statistics.

```python
def get_stats(self) -> Dict
```

**Returns:** Dictionary containing:
- `controller`: Request counts, row hit rate, average latency
- `spec`: HBM4 specification parameters
- `queues`: Queue depth information
- `qos`: QoS configuration
- `refresh`: Refresh mode and status
- `dfi`: DFI interface status

**Example:**
```python
stats = controller.get_stats()
print(f"Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
print(f"Total requests: {stats['controller']['total_requests']}")
```

#### get_bandwidth_gbs()

Calculate current effective bandwidth.

```python
def get_bandwidth_gbs(self) -> float
```

**Returns:** Effective bandwidth in GB/s (capped at peak)

#### get_effective_bandwidth_tbps()

Calculate effective bandwidth in TB/s.

```python
def get_effective_bandwidth_tbps(self) -> float
```

**Returns:** Effective bandwidth in TB/s

#### trigger_training()

Trigger PHY training for a channel.

```python
def trigger_training(self, channel_id: Optional[int] = None) -> str
```

**Parameters:**
- `channel_id`: Specific channel to train, or None for all

**Returns:** Training command ID

---

## DFI Interface Methods

#### dfi_request_ctrlupd()

Request a DFI control update.

```python
def dfi_request_ctrlupd(self) -> bool
```

#### dfi_set_frequency()

Set DFI interface frequency.

```python
def dfi_set_frequency(self, freq_mhz: int) -> bool
```

#### dfi_set_low_power()

Set DFI low power state.

```python
def dfi_set_low_power(self, state: DFILowPowerState) -> bool
```

#### dfi_get_signals()

Get current DFI signal states.

```python
def dfi_get_signals(self) -> DFISignals
```

---

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `channels` | int | Number of HBM4 channels |
| `pseudo_channels` | int | Total pseudo-channels |
| `dfi_ready` | bool | Check if DFI interface is ready |

---

## Statistics Class: HBM4ControllerStats

```python
@dataclass
class HBM4ControllerStats:
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    row_hit_count: int = 0
    refresh_count: int = 0
    training_count: int = 0
    repair_count: int = 0
    total_latency_ns: float = 0.0
    total_bandwidth_bytes: float = 0.0
```

**Computed Properties:**
- `average_latency_ns`: Average request latency
- `row_hit_rate`: Row buffer hit rate

---

## Usage Example

```python
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import HBM4Spec

# Create controller with HBM4 spec
spec = HBM4Spec()
controller = HBM4Controller(spec=spec, enable_qos=True)

# Submit multiple requests
for i in range(100):
    addr = i * 0x1000
    controller.submit_request(
        addr=addr,
        is_read=(i % 2 == 0),
        qos_level=8 if i % 2 == 0 else 4,
    )

# Run simulation
completed = 0
for cycle in range(10000):
    responses = controller.tick()
    completed += len(responses)
    if completed >= 100:
        break

# Get final statistics
stats = controller.get_stats()
print(f"Completed: {completed} requests")
print(f"Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
print(f"Bandwidth: {controller.get_bandwidth_gbs():.2f} GB/s")
```