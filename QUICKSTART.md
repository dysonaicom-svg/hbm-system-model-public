# HBM System Modeling Platform - Quick Start Guide

**Estimated Time**: 5 minutes
**Level**: Beginner to Intermediate

---

## Prerequisites

```bash
# Check Python version (3.8+ required)
python3 --version

# Install dependencies
pip install -r requirements.txt
```

---

## 1. Run a Basic Simulation (30 seconds)

```bash
# Functional simulation with built-in traffic generator
python -m sim.simulator --mode functional
```

**Expected Output**:
- Simulation progress bar
- Bandwidth and latency metrics
- Final statistics summary

---

## 2. Run Tests (1 minute)

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/controller/ -v      # Controller tests (98 tests)
pytest tests/dram/ -v            # DRAM tests (22 tests)
pytest tests/hbm4/ -v            # HBM4 tests (225+ tests)
pytest tests/integration/ -v     # Integration tests (46 tests)
```

---

## 3. Run Benchmark (2 minutes)

```bash
# Run performance benchmark
python -m sim.benchmark

# View results
cat sim/benchmark_results.json
```

---

## 4. Run Unified Simulation (1 minute)

```bash
# Python + RTL co-simulation
python -m sim.unified_simulator
```

---

## Common Commands Reference

### Simulation Modes

| Command | Description |
|---------|-------------|
| `python -m sim.simulator --mode functional` | Functional simulation |
| `python -m sim.simulator --mode transaction` | Transaction-level |
| `python -m sim.simulator --mode timing` | Timing-accurate |
| `python -m sim.unified_simulator` | Python + RTL unified |

### Test Commands

| Command | Description |
|---------|-------------|
| `pytest tests/ -v` | Run all tests |
| `pytest tests/controller/ -v` | Controller tests |
| `pytest tests/dram/ -v` | DRAM tests |
| `pytest tests/hbm4/ -v` | HBM4 specific tests |
| `pytest tests/integration/ -v` | Integration tests |
| `pytest tests/ -k "qos"` | Run tests matching "qos" |

### Traffic Patterns

| Pattern | Command |
|---------|---------|
| Sequential | `--pattern sequential` |
| Random | `--pattern random` |
| Stride | `--pattern stride` |
| Hotspot | `--pattern hot_spot` |

### Configuration Options

| Option | Example |
|--------|---------|
| Stack count | `--stacks 2` |
| Channels per stack | `--channels 8` |
| Data rate | `--data-rate 6.4` |
| Request rate | `--rate 0.5` |

---

## Quick Examples

### Example 1: Sequential Read Benchmark

```bash
python -m sim.simulator \
  --mode functional \
  --pattern sequential \
  --stacks 2 \
  --channels 8 \
  --duration 10
```

### Example 2: Random Access with QoS

```bash
python -m sim.simulator \
  --mode functional \
  --pattern random \
  --scheduler qos \
  --qos-high 12 \
  --qos-low 4
```

### Example 3: Custom Configuration

```bash
python -m sim.simulator \
  --mode functional \
  --config configs/custom.yaml
```

---

## Troubleshooting

### Import Errors

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
```

### Test Failures

```bash
# Run with verbose output
pytest tests/ -v --tb=short

# Run single test
pytest tests/controller/test_hbm4_address_decoder.py::test_basic_decode -v
```

### Simulation Hangs

```bash
# Add timeout
timeout 60 python -m sim.simulator --mode functional
```

---

## Next Steps

1. **Read the Design Document**: `docs/design/2026-06-15-hbm-system-model-design.md`
2. **Explore HBM4 Features**: `model/controller/hbm4_controller.py`
3. **Review Test Coverage**: `tests/` directory
4. **Check Release Notes**: `RELEASE.md`

---

## File Locations

| Purpose | Path |
|---------|------|
| Main entry point | `sim/simulator.py` |
| Controller model | `model/controller/` |
| DRAM model | `model/dram/` |
| RTL code | `rtl/` |
| Tests | `tests/` |
| Documentation | `docs/` |
| Release notes | `RELEASE.md` |

---

**Need Help?** Check `docs/design/2026-06-15-hbm-system-model-design.md` or `RELEASE.md`