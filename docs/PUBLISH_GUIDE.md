# HBM4 Publishing Guide

This guide covers the process for publishing HBM4 packages to PyPI.

## Overview

The HBM4 project publishes two packages to PyPI:

| Package | Description | Dependencies |
|---------|-------------|--------------|
| `hbm4-model` | Core HBM4 system model | numpy, scipy |
| `hbm4-sim` | Simulation framework | hbm4-model, numpy, matplotlib |

---

## Package Structure

```
HBM/
├── model/                    # → hbm4-model package
│   ├── controller/
│   ├── dram/
│   ├── hbm4/
│   ├── phy/
│   └── multi_channel.py
│
├── sim/                      # → hbm4-sim package
│   ├── simulator.py
│   ├── benchmark.py
│   ├── interconnect/
│   ├── trace/
│   └── visualization/
│
├── docs/                     # Documentation
│   ├── hbm4-model-PACKAGING.md
│   ├── hbm4-sim-PACKAGING.md
│   └── PUBLISH_GUIDE.md      # This file
│
├── rtl/                      # INTERNAL - Not published
├── verification/             # INTERNAL - Not published
├── tests/                    # INTERNAL - Not published
└── scripts/                  # INTERNAL - Not published
```

---

## Version Bump Process

### Semantic Versioning

HBM4 uses semantic versioning (SemVer):

```
MAJOR.MINOR.PATCH
  │     │     └── Bug fixes
  │     └───────── New features (backward compatible)
  └─────────────── Breaking changes
```

### Version Update Checklist

Before bumping version:

1. [ ] All tests passing
2. [ ] Changelog updated
3. [ ] Version number updated in:
   - `setup.py`
   - `pyproject.toml`
   - `model/__init__.py` (or relevant `__init__.py`)
   - `sim/__init__.py` (if applicable)

### Version Bump Commands

```bash
# Example: Bump patch version for hbm4-model
# 1. Edit setup.py
sed -i 's/version="1.0.0"/version="1.0.1"/' setup.py

# 2. Edit pyproject.toml
sed -i 's/version = "1.0.0"/version = "1.0.1"/' pyproject.toml

# 3. Edit package __init__.py
sed -i 's/__version__ = "1.0.0"/__version__ = "1.0.1"/' model/__init__.py

# 4. Create git tag
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

---

## Building Packages

### Prerequisites

```bash
# Install build tools
pip install build twine wheel setuptools

# Install additional tools for verification
pip install check-wheel-contents
```

### Build hbm4-model

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution
python -m build --sdist

# Build wheel
python -m build --wheel

# Verify the build
ls -la dist/
twine check dist/*
```

### Build hbm4-sim

```bash
cd /path/to/hbm4-sim

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build (hbm4-model must be installed or in path)
python -m build --sdist
python -m build --wheel

# Verify
twine check dist/*
```

---

## Publishing to PyPI

### PyPI Credentials

Configure PyPI credentials before publishing:

```bash
# Create ~/.pypirc
cat > ~/.pypirc << EOF
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
EOF

# Or use environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### TestPyPI First (Recommended)

Always test on TestPyPI first:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Install and verify from TestPyPI
pip install --index-url https://test.pypi.org/simple/ hbm4-model
```

### Publish to PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# Or upload specific files
twine upload dist/hbm4_model-1.0.0-py3-none-any.whl
twine upload dist/hbm4-model-1.0.0.tar.gz
```

---

## Release Checklist

### Pre-Release

- [ ] All 497 tests passing
- [ ] Version number updated in all files
- [ ] Changelog updated
- [ ] Documentation current
- [ ] No debug code or print statements
- [ ] License file present
- [ ] README.md complete

### Build Verification

- [ ] Source distribution builds without errors
- [ ] Wheel builds without errors
- [ ] Package size reasonable (< 100MB)
- [ ] Dependencies correctly declared
- [ ] Entry points work correctly

### PyPI Upload

- [ ] TestPyPI upload successful
- [ ] Test installation works
- [ ] Production PyPI upload successful
- [ ] Package page looks correct
- [ ] Version visible on PyPI

### Post-Release

- [ ] Git tag created
- [ ] GitHub release created (if applicable)
- [ ] Download tested
- [ ] Installation tested in fresh environment

---

## Release Scripts

### Complete Release Script

```bash
#!/bin/bash
# release.sh - Complete release process

set -e

PACKAGE=$1
VERSION=$2

if [ -z "$PACKAGE" ] || [ -z "$VERSION" ]; then
    echo "Usage: $0 <package> <version>"
    echo "Example: $0 hbm4-model 1.0.1"
    exit 1
fi

echo "=== Releasing $PACKAGE v$VERSION ==="

# 1. Update version
echo "Updating version to $VERSION..."
sed -i "s/version=\"[0-9.]*\"/version=\"$VERSION\"/" setup.py
sed -i "s/version = \"[0-9.]*\"/version = \"$VERSION\"/" pyproject.toml

# 2. Clean and build
echo "Building package..."
rm -rf dist/ build/ *.egg-info
python -m build

# 3. Verify
echo "Verifying package..."
twine check dist/*

# 4. Upload to TestPyPI
echo "Uploading to TestPyPI..."
twine upload --repository testpypi dist/*

# 5. Confirm production upload
echo "Ready to upload to PyPI? (Ctrl+C to abort)"
read -t 10 || true

# 6. Upload to PyPI
echo "Uploading to PyPI..."
twine upload dist/*

# 7. Create git tag
echo "Creating git tag..."
git tag -a v$VERSION -m "Release v$VERSION"
git push origin v$VERSION

echo "=== Release complete ==="
```

### Usage

```bash
# Make executable
chmod +x scripts/release.sh

# Run release
./scripts/release.sh hbm4-model 1.0.1
```

---

## Automated Release (GitHub Actions)

For automated releases, use GitHub Actions:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          pip install build twine
          
      - name: Build package
        run: |
          python -m build
          
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          twine upload dist/*
```

---

## Troubleshooting

### Common Issues

#### 1. Package not found on PyPI

```bash
# Check if package exists
pip search hbm4-model  # May require authentication
pip index versions hbm4-model
```

#### 2. Version conflict

```bash
# Uninstall old version
pip uninstall hbm4-model
pip install hbm4-model==1.0.1
```

#### 3. Dependency not found

```bash
# Check dependency is on PyPI
pip index versions numpy  # or relevant package
```

#### 4. Wheel build failed

```bash
# Ensure wheel is supported
python -c "import wheel; print(wheel.__version__)"
pip install --upgrade wheel setuptools
```

### Verification Commands

```bash
# Test package installation
pip install dist/*.whl --force-reinstall

# Verify imports
python -c "from model import HBM4Controller; print('OK')"

# Check entry points
python -c "from sim.simulator import run_simulation; print('OK')"
```

---

## Package Metadata Summary

### hbm4-model

| Field | Value |
|-------|-------|
| Name | hbm4-model |
| Version | 1.0.0 |
| Python | >=3.8 |
| License | Apache-2.0 |
| Dependencies | numpy>=1.21.0, scipy>=1.7.0 |
| Entry Points | None (library only) |

### hbm4-sim

| Field | Value |
|-------|-------|
| Name | hbm4-sim |
| Version | 1.0.0 |
| Python | >=3.8 |
| License | Apache-2.0 |
| Dependencies | hbm4-model>=1.0.0, numpy>=1.21.0, matplotlib>=3.5.0 |
| Entry Points | hbm4-sim, hbm4-benchmark, hbm4-report |

---

## Contact

For publishing issues or questions:
- Project Team: hbm-team@example.com
- Documentation: See `docs/` directory