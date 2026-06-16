# Signal Integrity API

Signal integrity models for HBM PHY simulation including TX pre-emphasis, RX CTLE, and DFE.

## Classes

### SignalIntegrityConfig

Complete signal integrity configuration.

```python
from model.phy.signal_integrity import SignalIntegrityConfig

config = SignalIntegrityConfig(
    sample_rate=32e9,
    ui_ns=0.125,           # Unit interval for 8 Gbps
    signal_amplitude=1.0,
    noise_rms=0.05,
    jitter_rms_ps=2.0,
)
```

### PreEmphasisConfig

Configuration for TX pre-emphasis.

```python
from model.phy.signal_integrity import PreEmphasisConfig

config = PreEmphasisConfig(
    n_pre_taps=2,          # Number of pre-tap positions
    n_post_taps=2,         # Number of post-tap positions
    max_tap_weight=0.4,    # Maximum tap weight
    tap_resolution=5,      # Tap resolution (bits)
    main_cursor=1.0,       # Main cursor weight
)
```

### CTLEConfig

Configuration for RX CTLE.

```python
from model.phy.signal_integrity import CTLEConfig

config = CTLEConfig(
    n_dc_gain_stages=4,
    dc_gain_range=(-6.0, 6.0),
    zero_options=[4e9, 8e9, 12e9],
    pole_options=[8e9, 16e9, 24e9],
    peaking_range=(0.0, 12.0),
    stage_resolution=1.0,
)
```

### DFEConfig

Configuration for DFE.

```python
from model.phy.signal_integrity import DFEConfig

config = DFEConfig(
    n_taps=5,
    max_tap_magnitude=0.3,
    mu=0.01,
    decision_threshold=0.0,
)
```

---

## Equalizer Classes

### TXPreEmphasis

TX Pre-emphasis equalizer using FIR-based pre-emphasis.

```python
from model.phy.signal_integrity import TXPreEmphasis, PreEmphasisConfig

tx = TXPreEmphasis(config=PreEmphasisConfig())

# Set tap weights
tx.set_taps([0.2, 0.5, 0.2, 0.1])  # [pre1, main, post1, post2]

# Equalize signal
equalized = tx.equalize(signal_samples)
```

**Methods:**
- `set_taps(tap_values)`: Set FIR tap weights
- `equalize(signal)`: Apply pre-emphasis to signal
- `get_transfer_function()`: Get frequency response

### RXCTLE

RX Continuous Time Linear Equalizer.

```python
from model.phy.signal_integrity import RXCTLE, CTLEConfig

ctle = RXCTLE(config=CTLEConfig())

# Set DC gain and peaking
ctle.set_dc_gain(-3.0)  # dB
ctle.set_peaking(6.0)   # dB

# Equalize signal
equalized = ctle.equalize(signal_samples)
```

### DFE

Decision Feedback Equalizer.

```python
from model.phy.signal_integrity import DFE, DFEConfig

dfe = DFE(config=DFEConfig())

# Process samples
for bit in decision_samples:
    decision = dfe.equalize(bit)
    dfe.update_taps(error)
```

---

## Signal Integrity Analysis

### ChannelResponse

Channel frequency response.

```python
from model.phy.signal_integrity import ChannelResponse

response = ChannelResponse(
    frequency=[...],
    impedance=[...],
    transfer_function=[...],
)

# Get metrics
il_db = response.get_insertion_loss(4e9)  # dB
phase_delay = response.get_phase_delay(4e9)  # ns
```

### WaveformMetrics

Computed waveform quality metrics.

```python
from model.phy.signal_integrity import WaveformMetrics

metrics = WaveformMetrics(
    rise_time=0.5,      # 20%-80% rise time (ns)
    fall_time=0.5,       # 20%-80% fall time (ns)
    overshoot=0.1,       # Maximum overshoot (V)
    undershoot=0.05,     # Maximum undershoot (V)
    settling_time=2.0,   # Settling time (ns)
    max_slew_rate=2.0,   # Maximum slew rate (V/ns)
)
```

---

## Usage Example

```python
import numpy as np
from model.phy.signal_integrity import (
    SignalIntegrityConfig,
    TXPreEmphasis,
    RXCTLE,
    DFE,
)

# Create configuration
config = SignalIntegrityConfig(sample_rate=32e9, ui_ns=0.125)

# Create equalizers
tx = TXPreEmphasis()
rx_ctle = RXCTLE()
dfe = DFE()

# Generate test signal
t = np.linspace(0, 1e-6, 1000)
signal = np.sin(2 * np.pi * 8e9 * t)  # 8 Gbps pattern

# Apply equalization
tx_output = tx.equalize(signal)
rx_output = rx_ctle.equalize(tx_output)

# Process with DFE
decisions = []
for sample in rx_output:
    decision = dfe.equalize(sample)
    decisions.append(decision)
```

---

## Signal Integrity Metrics

### SignalIntegrityMetric Enum

| Metric | Description |
|--------|-------------|
| `OVERSHOOT` | Maximum overshoot voltage |
| `UNDERSHOOT` | Maximum undershoot voltage |
| `SETTLING_TIME` | Time to settle within tolerance |
| `RINGING_FREQUENCY` | Ringing frequency |
| `CROSSTALK_PEAK` | Peak crosstalk |
| `EYE_WIDTH` | Eye diagram width |
| `EYE_HEIGHT` | Eye diagram height |