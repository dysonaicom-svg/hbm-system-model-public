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

## 2. Run the Smoke Test (30 seconds)

```bash
# This is the recommended first test to verify installation
python3 examples/basic_read_write.py
```

**Expected Output**:
- Example 1: Basic HBM4 Controller
- Example 2: Custom Speed Grades
- Example 3: Row Hit Optimization
- Example 4: Different Request Sizes
- Example 5: QoS Priority Levels

---

## 3. Run Tests (1 minute)

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/controller/ -v      # Controller tests (98 tests)
pytest tests/dram/ -v            # DRAM tests (22 tests)
pytest tests/hbm4/ -v            # HBM4 tests (225+ tests)
pytest tests/integration/ -v      # Integration tests (46 tests)
```

---

## 4. Run Benchmark (2 minutes)

```bash
# Run performance benchmark
python -m sim.benchmark

# View results
cat sim/benchmark_results.json
```

---

## 5. Run Unified Simulation (1 minute)

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

1. **Read the README**: `README.md` for complete project documentation
2. **Explore Examples**: Run through `examples/` directory
3. **Review Test Coverage**: `tests/` directory for 497 test cases
4. **Check API Reference**: `docs/API_REFERENCE.md`
5. **Read Design Document**: `docs/ARCHITECTURE.md`

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
| Examples | `examples/` |
| Release notes | `RELEASE.md` |

---

## Available Examples

| File | Description |
|------|-------------|
| `basic_read_write.py` | First example to run - basic operations |
| `basic_controller.py` | Controller creation and operations |
| `address_decoding.py` | Address mapping schemes |
| `qos_scheduling.py` | Priority-based scheduling |
| `refresh_scheduling.py` | Refresh management |
| `dfi_interface.py` | DFI protocol usage |
| `bandwidth_benchmark.py` | Performance measurement |
| `multi_channel.py` | Multi-channel parallelism |
| `dram_features.py` | ECC, lane repair, PHY training |
| `logic_base_die_example.py` | Logic base die model |

---

**Need Help?** Check `docs/USER_GUIDE.md` or `RELEASE.md`