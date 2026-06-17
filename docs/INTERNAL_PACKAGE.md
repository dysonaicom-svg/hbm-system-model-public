# Internal Package Documentation

This document describes the internal packages that are **NOT published to PyPI** but are essential for internal development and verification.

## Internal Package Overview

| Package | Path | Purpose | Published |
|---------|------|---------|-----------|
| RTL Code | `rtl/` | Verilog/SystemVerilog RTL implementation | No |
| UVM Verification | `verification/` | UVM-based verification environment | No |
| Test Suite | `tests/` | Comprehensive test suite | No |
| Integration | `integration/` | gem5 integration code | No |
| Configuration | `config/` | Project configuration files | No |
| Internal Scripts | `scripts/` | Build and verification scripts | No |
| Research | `research/` | Reference implementations (Ramulator2) | No |

---

## 1. RTL Code (`rtl/`)

**Purpose:** Verilog/SystemVerilog RTL implementation of HBM Controller

**Contents:**
```
rtl/
├── hbm_controller.sv          # Main controller RTL
├── hbm_types.svh             # Type definitions
├── hbm_pkg.sv                # Package definitions
├── dram_model.sv             # DRAM behavioral model
├── hbm_controller_tb.sv     # SystemVerilog testbench
├── hbm_controller_tb.cpp     # C++ testbench main
├── hbm_controller_tb_main.cpp
├── Makefile                  # Build instructions
├── filelist.f                # Verilog file list
├── build_rtl.sh              # Build script
└── README.md
```

**Key Components:**
- `hbm_controller.sv` - HBM Controller RTL with DFI interface
- `dram_model.sv` - Behavioral DRAM model
- `hbm_types.svh` - SystemVerilog type definitions

**License:** Proprietary (not for external distribution)

---

## 2. UVM Verification (`verification/`)

**Purpose:** UVM-based verification environment for HBM Controller

**Contents:**
```
verification/
├── uvm/
│   ├── hbm4_vip_pkg.sv       # VIP package
│   ├── hbm_env_pkg.sv        # Environment package
│   ├── hbm_test_pkg.sv       # Test package
│   ├── hbm_coverage.sv       # Coverage model
│   ├── hbm_tb.sv             # Top-level testbench
│   ├── uvm.f                 # UVM file list
│   ├── uvm_stub/             # UVM stub files
│   │   ├── src/uvm.svh
│   │   └── src/uvm_macros.svh
│   ├── tests/
│   │   ├── test_read_seq.sv
│   │   ├── test_write_seq.sv
│   │   ├── test_refresh_seq.sv
│   │   ├── test_multi_channel_seq.sv
│   │   ├── test_bank_conflict_seq.sv
│   │   ├── hbm_bank_contention_test_pkg.sv
│   │   ├── hbm_boundary_test_pkg.sv
│   │   ├── hbm_coverage_pkg.sv
│   │   ├── hbm_qos_test_pkg.sv
│   │   └── hbm_refresh_test_pkg.sv
│   ├── scripts/
│   │   └── gen_coverage_report.py
│   └── docs/
└── reference_model/
    └── (internal reference models)
```

**Key Components:**
- VIP package for HBM protocol verification
- Environment with monitors, scoreboards, and coverage
- Comprehensive test sequences for all HBM operations

**License:** Proprietary

---

## 3. Test Suite (`tests/`)

**Purpose:** Comprehensive Python test suite for model verification

**Contents:**
```
tests/
├── __init__.py
├── conftest.py               # Pytest configuration
├── controller/               # Controller tests (98 tests)
├── dram/                     # DRAM tests (22 tests)
├── hbm4/                     # HBM4 specific tests (225+ tests)
├── simulation/               # Simulation tests (72 tests)
├── integration/              # Integration tests (46 tests)
├── interconnect/
├── traffic/
├── coverage/
├── performance/
├── regression/
├── rtl_verification/
└── verification/
```

**Test Coverage:**
| Category | Tests | Status |
|----------|-------|--------|
| Controller Tests | 98 | Passing |
| DRAM Tests | 22 | Passing |
| HBM4 DFI Tests | 34 | Passing |
| HBM4 PHY/TSV/Lane | 225+ | Passing |
| Simulation Tests | 72 | Passing |
| Integration Tests | 46 | Passing |
| **Total** | **497** | **All Passing** |

**Running Tests:**
```bash
# Run all tests
pytest tests/ -v

# Run by category
pytest tests/controller/ -v
pytest tests/dram/ -v
pytest tests/hbm4/ -v

# Run with coverage
pytest tests/ --cov=model --cov-report=html
```

---

## 4. Integration (`integration/`)

**Purpose:** gem5 integration for system-level simulation

**Contents:**
```
integration/
└── gem5/
    ├── hbm4_config.py        # gem5 configuration
    └── python_model_integration.py  # Python model wrapper
```

**Usage:** gem5 full-system simulation with HBM4 model

---

## 5. Configuration (`config/`)

**Purpose:** Project configuration files

**Contents:**
```
config/
├── default.yaml              # Default configuration
├── hbm4_16gbps.yaml          # 16 Gbps speed grade config
└── simulation.yaml           # Simulation parameters
```

**Configuration Format:** YAML

---

## 6. Internal Scripts (`scripts/`)

**Purpose:** Build, verification, and analysis scripts

**Contents:**
```
scripts/
├── auto_compare.py           # RTL vs Model comparison
├── ci_check.sh              # CI pre-check
├── ci_test.sh               # CI test runner
├── compare_rtl_model.py     # RTL-Python comparison
├── coverage_collector.py    # Coverage collection
├── create_public_release.sh # Release creation script
├── hbm4_integration_demo.py # Integration demo
├── quickstart_verify.py     # Quick verification
├── rtl_verification_runner.py # RTL verification runner
├── run_comprehensive_benchmark.sh
├── run_rtl_benchmark.sh
└── comparison/
    ├── comparison_report.json
    └── comparison_report.md
```

---

## 7. Research (`research/`)

**Purpose:** Reference implementations for validation

**Contents:**
```
research/
└── ramulator2/              # Ramulator2 reference simulator
```

**Note:** Used for cross-validation against industry-standard simulator

---

## Version Management Strategy

### Internal Versioning

Internal packages use date-based versioning for tracking:

```
Internal Version: YYYY.MM.DD.build
Example: 2026.06.16.001
```

### Git Tagging

Internal releases are tagged with prefix:

```bash
# Tag format for internal releases
git tag -a internal/v1.0.0 -m "Internal release v1.0.0"
git push origin internal/v1.0.0
```

### Public Package Versioning

PyPI packages use semantic versioning:

```
Public Version: X.Y.Z
Example: 1.0.0
```

Sync internal commits with public releases:
```bash
# When publishing to PyPI
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## Build Instructions

### RTL Build

```bash
cd rtl

# Build with Verilator
verilator --cc --trace \
    -f filelist.f \
    --top-module hbm_controller \
    -o obj_dir/hbm_controller

# Build testbench
make -f Makefile
```

### Python Test Suite

```bash
# Install dependencies
pip install -r requirements.txt

# Run full test suite
pytest tests/ -v --tb=short

# Run with coverage report
pytest tests/ --cov=model --cov-report=html --cov-report=term
```

### UVM Verification

```bash
cd verification/uvm

# Compile with Questa/ModelSim
vlog -f uvm.f
vsim -c -do "run -all; quit"
```

---

## Release Checklist

Before creating a public release:

- [ ] All internal tests passing (497 tests)
- [ ] RTL verification complete
- [ ] Documentation updated
- [ ] Version numbers synchronized
- [ ] Internal packages excluded from build
- [ ] Public API documented
- [ ] PyPI credentials configured
- [ ] Git tags created for release

---

## Directory Exclusion from PyPI

The following directories are excluded from PyPI packages in `setup.py` and `pyproject.toml`:

```python
exclude=[
    "tests",
    "tests.*",
    "docs",
    "docs.*",
    "verification",
    "verification.*",
    "verification.uvm",
    "verification.uvm.*",
    "verification.reference_model",
    "verification.reference_model.*",
    "rtl",
    "rtl.*",
    "research",
    "research.*",
    "model.controller.tests",
    "model.dram.tests",
    "model.benchmark",
    "model.benchmark.*",
    "model.interconnect",
    "model.interconnect.*",
    "model.traffic",
    "model.traffic.*",
    "sim.interconnect",
    "sim.interconnect.*",
    "sim.trace",
    "sim.trace.*",
]
```