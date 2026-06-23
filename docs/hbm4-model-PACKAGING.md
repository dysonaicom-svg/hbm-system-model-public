# HBM4 Model Package Specification

## Package Overview

| Field | Value |
|-------|-------|
| **Package Name** | `hbm4-model` |
| **Version** | `1.0.0` |
| **Description** | High Bandwidth Memory 4 system-level model with timing, power, and DRAM behavior |
| **Author** | HBM Development Team |
| **License** | Proprietary |

## Dependencies

| Dependency | Version | Type |
|------------|---------|------|
| `numpy` | `>=1.21.0` | Required |
| `scipy` | `>=1.7.0` | Required |

## Project Structure

```
hbm4-model/
├── pyproject.toml
├── setup.py
├── setup.cfg
├── README.md
├── LICENSE
├── hbm4/
│   ├── __init__.py
│   ├── controller/
│   │   ├── __init__.py
│   │   ├── controller.py
│   │   ├── command_sequencer.py
│   │   ├── address_decoder.py
│   │   ├── qos_scheduler.py
│   │   └── refresh_scheduler.py
│   ├── dram/
│   │   ├── __init__.py
│   │   ├── timing.py
│   │   ├── power_estimator.py
│   │   ├── bank_state_machine.py
│   │   └── channel_model.py
│   ├── phy/
│   │   ├── __init__.py
│   │   ├── phy_training.py
│   │   ├── lane_repair.py
│   │   └── ecc_crc.py
│   ├── dfi/
│   │   ├── __init__.py
│   │   └── dfi_interface.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── request.py
│   │   ├── queue.py
│   │   └── types.py
│   └── specs/
│       ├── __init__.py
│       └── hbm4_spec.py
└── tests/
    ├── __init__.py
    ├── controller/
    ├── dram/
    └── phy/
```

## setup.py

```python
#!/usr/bin/env python3
"""Setup script for hbm4-model package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("LICENSE", "r", encoding="utf-8") as fh:
    license_text = fh.read()

setup(
    name="hbm4-model",
    version="1.0.0",
    author="HBM Development Team",
    author_email="hbm-team@example.com",
    description="High Bandwidth Memory 4 system-level model",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/hbm4-model",
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
        "numpy>=1.21.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={},
)
```

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "hbm4-model"
version = "1.0.0"
description = "High Bandwidth Memory 4 system-level model"
readme = "README.md"
license = {text = "Proprietary"}
authors = [
    {name = "HBM Development Team", email = "hbm-team@example.com"}
]
keywords = ["hbm", "memory", "modeling", "simulation", "eda"]
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
    "numpy>=1.21.0",
    "scipy>=1.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=3.0.0",
    "black>=22.0.0",
    "flake8>=4.0.0",
    "mypy>=0.950",
]

[project.urls]
Homepage = "https://github.com/example/hbm4-model"
Documentation = "https://hbm4-model.readthedocs.io"
Repository = "https://github.com/example/hbm4-model"

[tool.setuptools]
packages = ["hbm4", "hbm4.controller", "hbm4.dram", "hbm4.phy", "hbm4.dfi", "hbm4.common", "hbm4.specs"]

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
name = hbm4-model
version = 1.0.0
description = High Bandwidth Memory 4 system-level model
long_description = file: README.md
long_description_content_type = text/markdown
url = https://github.com/example/hbm4-model
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
    numpy>=1.21.0
    scipy>=1.7.0

[options.packages.find]
exclude =
    tests
    tests.*

[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist

[tool:pytest]
testpaths = tests
```

## hbm4/__init__.py (Public API)

```python
"""
HBM4 Model Package

High Bandwidth Memory 4 system-level model with timing, power estimation,
and DRAM behavior simulation.

Usage:
    from hbm4 import HBM4Controller, HBM4Spec, DRAMTiming

    # Create HBM4 specification
    spec = HBM4Spec(speed_grade=16)  # 16 Gbps

    # Create controller model
    controller = HBM4Controller(spec)

    # Issue read request
    request = controller.read(address=0x1000, size=64)
    result = controller.wait(request)
"""

__version__ = "1.0.0"
__author__ = "HBM Development Team"

# Import public API
from hbm4.controller.controller import HBM4Controller
from hbm4.controller.command_sequencer import CommandSequencer
from hbm4.controller.address_decoder import AddressDecoder
from hbm4.controller.qos_scheduler import QoSScheduler
from hbm4.controller.refresh_scheduler import RefreshScheduler

from hbm4.dram.timing import DRAMTiming
from hbm4.dram.power_estimator import PowerEstimator
from hbm4.dram.bank_state_machine import BankStateMachine
from hbm4.dram.channel_model import ChannelModel

from hbm4.phy.phy_training import PHYTraining
from hbm4.phy.lane_repair import LaneRepair
from hbm4.phy.ecc_crc import ECCEngine, CRCEngine

from hbm4.dfi.dfi_interface import DFIInterface

from hbm4.specs.hbm4_spec import HBM4Spec, SpeedGrade, ChannelConfig

from hbm4.common.request import Request, RequestType, RequestStatus
from hbm4.common.queue import RequestQueue
from hbm4.common.types import Address, BurstLength, DataWidth

__all__ = [
    # Version
    "__version__",
    # Controller
    "HBM4Controller",
    "CommandSequencer",
    "AddressDecoder",
    "QoSScheduler",
    "RefreshScheduler",
    # DRAM
    "DRAMTiming",
    "PowerEstimator",
    "BankStateMachine",
    "ChannelModel",
    # PHY
    "PHYTraining",
    "LaneRepair",
    "ECCEngine",
    "CRCEngine",
    # DFI
    "DFIInterface",
    # Specs
    "HBM4Spec",
    "SpeedGrade",
    "ChannelConfig",
    # Common
    "Request",
    "RequestType",
    "RequestStatus",
    "RequestQueue",
    "Address",
    "BurstLength",
    "DataWidth",
]
```

## Installation

### From PyPI (when published)
```bash
pip install hbm4-model
```

### From source
```bash
git clone https://github.com/example/hbm4-model.git
cd hbm4-model
pip install -e .
```

### With dev dependencies
```bash
pip install -e ".[dev]"
```

## Usage Example

```python
"""Example usage of hbm4-model package."""

from hbm4 import HBM4Controller, HBM4Spec, SpeedGrade, RequestType

# Create HBM4 specification for 16 Gbps operation
spec = HBM4Spec(
    speed_grade=SpeedGrade.Gbps_16,
    num_channels=32,
    channels_per_package=8,
)

# Initialize controller
controller = HBM4Controller(spec)

# Configure address mapping
controller.set_address_map(
    channel_bits=5,    # 32 channels
    pseudo_channel_bits=1,
    bank_group_bits=2,
    bank_bits=2,
    row_bits=16,
    column_bits=10,
)

# Issue memory requests
read_req = controller.read(address=0x00010000, size=64, priority=RequestType.HIGH_PRIORITY)
write_req = controller.write(address=0x00020000, data=b'\xAA' * 64)

# Wait for completion
read_data = controller.wait(read_req)
controller.wait(write_req)

# Get power estimates
power = controller.estimate_power()
print(f"Current power: {power.total_power:.2f} mW")
```