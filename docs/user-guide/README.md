# User Guide

This directory contains user guide documentation for the HBM4 System Modeling Platform.

## Files

- [USER_GUIDE.md](USER_GUIDE.md) - Complete user guide

## Contents

1. Quick Start - 5-minute setup guide
2. Installation - Prerequisites and setup
3. Basic Usage - Running simulations
4. Configuration - Configuration options
5. Simulation Modes - Available modes
6. Examples - Code examples
7. Troubleshooting - Common issues

## Quick Start

```bash
# Run a quick simulation
python -m sim.hbm4_unified_simulator --mode quick --channels 8

# Run tests
pytest tests/ -v

# Run benchmark
python -m sim.benchmark
```

## Related Documentation

- [API Documentation](../api/) - Complete API reference
- [Quick Reference](../QUICKREF.md) - Command reference
- [Release Notes](../RELEASE_NOTES.md) - Version history
