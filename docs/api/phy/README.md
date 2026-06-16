# PHY Model API Reference

This directory contains API documentation for the HBM PHY and signal integrity module.

## Overview

The PHY module provides:
- Signal integrity analysis (TX pre-emphasis, RX CTLE, DFE)
- IBIS model parsing and simulation
- Eye diagram analysis
- Channel modeling

## Key Classes

### SignalIntegrityConfig

Configuration for signal integrity analysis.

```python
from model.phy.signal_integrity import SignalIntegrityConfig, TXPreEmphasis, CTLE, DFE

config = SignalIntegrityConfig(
    sample_rate=32e9,
    ui_ns=0.125,
    signal_amplitude=1.0,
)
```

### IBISSimulator

IBIS model-based signal integrity simulation.

```python
from model.phy.ibis_simulator import IBISSimulator

sim = IBISSimulator(ibis_file="path/to/model.ibis")
```

### EyeAnalyzer

Eye diagram analysis and metrics.

```python
from model.phy.eye_analyzer import EyeAnalyzer, EyeMetrics

analyzer = EyeAnalyzer()
metrics = analyzer.analyze_eye(eye_data)
```

---

## File Structure

```
docs/api/phy/
├── README.md              # This file
├── signal_integrity.md   # Signal integrity API
├── ibis_model.md         # IBIS model API
└── eye_analysis.md       # Eye diagram analysis API
```