# HBM4 Simulation Package Specification

## Package Overview

| Field | Value |
|-------|-------|
| **Package Name** | `hbm4-sim` |
| **Version** | `1.0.0` |
| **Description** | High Bandwidth Memory 4 simulation framework with traffic generation and visualization |
| **Author** | HBM Development Team |
| **License** | Proprietary |

## Dependencies

### Direct Dependencies

| Dependency | Version | Type |
|------------|---------|------|
| `hbm4-model` | `>=1.0.0` | Required |
| `numpy` | `>=1.21.0` | Required |
| `matplotlib` | `>=3.5.0` | Required |

### Dependency Graph

```
hbm4-sim (v1.0.0)
    │
    ├── hbm4-model (v1.0.0)  ← PRIMARY DEPENDENCY
    │       ├── numpy (>=1.21.0)
    │       └── scipy (>=1.7.0)
    │
    ├── numpy (>=1.21.0)
    │
    └── matplotlib (>=3.5.0)
```

## Project Structure

```
hbm4-sim/
├── pyproject.toml
├── setup.py
├── setup.cfg
├── README.md
├── LICENSE
├── hbm4_sim/
│   ├── __init__.py
│   ├── simulator.py
│   ├── traffic/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── trace_reader.py
│   │   └── patterns.py
│   ├── interconnect/
│   │   ├── __init__.py
│   │   ├── axi_interconnect.py
│   │   └── noc.py
│   ├── trace/
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   └── recorder.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── bandwidth.py
│   │   ├── latency.py
│   │   └── power.py
│   ├── benchmarks/
│   │   ├── __init__.py
│   │   ├── benchmark.py
│   │   └── patterns.py
│   └── unified/
│       ├── __init__.py
│       └── unified_simulator.py
└── tests/
    ├── __init__.py
    ├── traffic/
    ├── interconnect/
    └── visualization/
```

## setup.py

```python
#!/usr/bin/env python3
"""Setup script for hbm4-sim package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hbm4-sim",
    version="1.0.0",
    author="HBM Development Team",
    author_email="hbm-team@example.com",
    description="High Bandwidth Memory 4 simulation framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/hbm4-sim",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: Proprietary",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "hbm4-model>=1.0.0",
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "notebook": [
            "jupyter>=1.0.0",
            "ipykernel>=6.0.0",
            "pandas>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hbm4-sim=hbm4_sim.cli:main",
        ],
    },
)
```

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "hbm4-sim"
version = "1.0.0"
description = "High Bandwidth Memory 4 simulation framework"
readme = "README.md"
license = {text = "Proprietary"}
authors = [
    {name = "HBM Development Team", email = "hbm-team@example.com"}
]
keywords = ["hbm", "memory", "simulation", "traffic-generator", "visualization"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    "License :: OSI Approved :: Proprietary",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
requires-python = ">=3.8"
dependencies = [
    "hbm4-model>=1.0.0",
    "numpy>=1.21.0",
    "matplotlib>=3.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=3.0.0",
    "black>=22.0.0",
    "flake8>=4.0.0",
    "mypy>=0.950",
]
notebook = [
    "jupyter>=1.0.0",
    "ipykernel>=6.0.0",
    "pandas>=1.3.0",
]

[project.urls]
Homepage = "https://github.com/example/hbm4-sim"
Documentation = "https://hbm4-sim.readthedocs.io"
Repository = "https://github.com/example/hbm4-sim"

[project.scripts]
hbm4-sim = "hbm4_sim.cli:main"

[tool.setuptools]
packages = [
    "hbm4_sim",
    "hbm4_sim.traffic",
    "hbm4_sim.interconnect",
    "hbm4_sim.trace",
    "hbm4_sim.visualization",
    "hbm4_sim.benchmarks",
    "hbm4_sim.unified",
]

[tool.black]
line-length = 100
target-version = ["py38", "py39", "py310", "py311"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
```

## setup.cfg

```ini
[metadata]
name = hbm4-sim
version = 1.0.0
description = High Bandwidth Memory 4 simulation framework
long_description = file: README.md
long_description_content_type = text/markdown
url = https://github.com/example/hbm4-sim
author = HBM Development Team
author_email = hbm-team@example.com
license = Proprietary
classifiers =
    Development Status :: 4 - Beta
    Intended Audience :: Science/Research
    Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)
    Programming Language :: Python :: 3
    Programming Language :: Python :: 3.8
    Programming Language :: Python :: 3.9
    Programming Language :: Python :: 3.10
    Programming Language :: Python :: 3.11

[options]
packages = find:
python_requires = >=3.8
install_requires =
    hbm4-model>=1.0.0
    numpy>=1.21.0
    matplotlib>=3.5.0

[options.packages.find]
exclude =
    tests
    tests.*

[options.entry_points]
console_scripts =
    hbm4-sim = hbm4_sim.cli:main

[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist

[tool:pytest]
testpaths = tests
```

## hbm4_sim/__init__.py (Public API)

```python
"""
HBM4 Simulation Package

High Bandwidth Memory 4 simulation framework with traffic generation,
interconnect modeling, and visualization capabilities.

Usage:
    from hbm4_sim import Simulator, TrafficGenerator, Benchmark

    # Create simulator
    sim = Simulator()

    # Generate traffic
    traffic = TrafficGenerator.sequential(num_requests=10000)
    results = sim.run(traffic)

    # Visualize results
    results.plot_bandwidth()
"""

__version__ = "1.0.0"
__author__ = "HBM Development Team"

# Core simulation
from hbm4_sim.simulator import Simulator, SimulationConfig, SimulationResult

# Traffic generation
from hbm4_sim.traffic.generator import TrafficGenerator, TrafficPattern
from hbm4_sim.traffic.trace_reader import TraceReader, TraceFormat
from hbm4_sim.traffic.patterns import (
    SequentialPattern,
    RandomPattern,
    StridePattern,
    HotspotPattern,
    GaussianPattern,
)

# Interconnect
from hbm4_sim.interconnect.axi_interconnect import AXIInterconnect
from hbm4_sim.interconnect.noc import NoC, NoCConfig

# Trace and recording
from hbm4_sim.trace.parser import TraceParser
from hbm4_sim.trace.recorder import TraceRecorder, RecordFormat

# Visualization
from hbm4_sim.visualization.bandwidth import BandwidthPlotter
from hbm4_sim.visualization.latency import LatencyPlotter
from hbm4_sim.visualization.power import PowerPlotter

# Benchmarks
from hbm4_sim.benchmarks.benchmark import Benchmark, BenchmarkResult
from hbm4_sim.benchmarks.patterns import (
    BenchmarkSequential,
    BenchmarkRandom,
    BenchmarkStride,
    BenchmarkHotspot,
)

# Unified simulation (combines Python model with RTL)
from hbm4_sim.unified.unified_simulator import UnifiedSimulator, RTLConfig

__all__ = [
    # Version
    "__version__",
    # Core simulation
    "Simulator",
    "SimulationConfig",
    "SimulationResult",
    # Traffic generation
    "TrafficGenerator",
    "TrafficPattern",
    "TraceReader",
    "TraceFormat",
    "SequentialPattern",
    "RandomPattern",
    "StridePattern",
    "HotspotPattern",
    "GaussianPattern",
    # Interconnect
    "AXIInterconnect",
    "NoC",
    "NoCConfig",
    # Trace
    "TraceParser",
    "TraceRecorder",
    "RecordFormat",
    # Visualization
    "BandwidthPlotter",
    "LatencyPlotter",
    "PowerPlotter",
    # Benchmarks
    "Benchmark",
    "BenchmarkResult",
    "BenchmarkSequential",
    "BenchmarkRandom",
    "BenchmarkStride",
    "BenchmarkHotspot",
    # Unified
    "UnifiedSimulator",
    "RTLConfig",
]
```

## Dependency Declaration

The `hbm4-sim` package explicitly declares its dependency on `hbm4-model`:

### In setup.py:
```python
install_requires=[
    "hbm4-model>=1.0.0",  # <-- Primary dependency
    "numpy>=1.21.0",
    "matplotlib>=3.5.0",
],
```

### In pyproject.toml:
```toml
dependencies = [
    "hbm4-model>=1.0.0",  # <-- Primary dependency
    "numpy>=1.21.0",
    "matplotlib>=3.5.0",
],
```

### Runtime Verification:
```python
# hbm4_sim/__init__.py
try:
    import hbm4_model
except ImportError:
    raise ImportError(
        "hbm4-sim requires hbm4-model. "
        "Install it with: pip install hbm4-model"
    )
```

## Installation

### Standard installation
```bash
pip install hbm4-sim
```
Note: This automatically installs `hbm4-model` as a dependency.

### From source
```bash
git clone https://github.com/example/hbm4-sim.git
cd hbm4-sim
pip install -e .
```

### With dev dependencies
```bash
pip install -e ".[dev]"
```

### With notebook support
```bash
pip install -e ".[notebook]"
```

## Usage Example

```python
"""Example usage of hbm4-sim package."""

from hbm4_sim import (
    Simulator,
    TrafficGenerator,
    Benchmark,
    SimulationConfig,
)
from hbm4_model import HBM4Spec, SpeedGrade

# Create HBM4 specification
spec = HBM4Spec(speed_grade=SpeedGrade.Gbps_16)

# Configure simulation
config = SimulationConfig(
    num_cycles=100000,
    verbose=True,
    record_traces=True,
)

# Create simulator
sim = Simulator(spec=spec, config=config)

# Generate traffic patterns
traffic = TrafficGenerator.random(
    num_requests=10000,
    address_range=(0x0, 0x100000),
    read_ratio=0.7,
)

# Run simulation
results = sim.run(traffic)

# Print summary
print(f"Total requests: {results.num_requests}")
print(f"Average latency: {results.avg_latency:.2f} cycles")
print(f"Bandwidth: {results.bandwidth:.2f} GB/s")

# Run built-in benchmarks
benchmark = Benchmark(spec)
benchmark_results = benchmark.run_all()

# Visualize results
results.plot_bandwidth()
results.plot_latency_histogram()
```

## Installation Order

When installing both packages from source:

```bash
# 1. Install hbm4-model first (hbm4-sim depends on it)
pip install /path/to/hbm4-model

# 2. Then install hbm4-sim
pip install /path/to/hbm4-sim
```

Or install in editable mode for development:

```bash
# 1. Install hbm4-model in editable mode
pip install -e /path/to/hbm4-model

# 2. Install hbm4-sim in editable mode
pip install -e /path/to/hbm4-sim
```