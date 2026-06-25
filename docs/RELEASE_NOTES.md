# HBM4 System Modeling Platform - Release Notes

## Version 2.2.0 (Current)

**Release Date:** 2026-06-25

### What's New

#### Phase G-J Complete

This release marks the completion of Phase G-J development:

| Phase | Feature | Status |
|-------|---------|--------|
| G | Logic Base Die Core | Complete |
| H | Unified Simulator | Complete |
| I | Performance Optimization | Complete |
| J | Controller Integration | Complete |

#### Key Features

1. **Logic Base Die (LBD)**
   - Unified controller model
   - Per-channel independent timing
   - PAM3 encoder/decoder
   - Lane repair support
   - ECC/CRC handling

2. **Unified Simulator**
   - Combined HBM4 + RTL simulation
   - gem5 integration support
   - RTL co-simulation
   - Comprehensive statistics

3. **Performance**
   - Optimized throughput > 300 GB/s
   - Efficiency > 20%
   - Queue overflow prevention

#### API Changes

- `HBM4UnifiedSimulator` - New unified simulator class
- `HBM4LogicBaseDie` - Logic Base Die controller
- `HBM4PAM3Encoder` - PAM3 encoding support
- `RTLInterface` - RTL co-simulation interface

### Bug Fixes

- Fixed Random pattern efficiency > 100% bug
- Fixed benchmark test segmentation faults
- Fixed conftest.py duplicate fixture issues
- Fixed filename case sensitivity conflicts
- Fixed DFI interface request queue overflow

### Test Suite

| Category | Tests | Status |
|----------|-------|--------|
| Controller Tests | 411+ | Passing |
| DRAM Tests | 1000+ | Passing |
| HBM4 Tests | 700+ | Passing |
| Integration Tests | 100+ | Passing |
| Simulation Tests | 64+ | Passing |
| **Total** | **4,409+** | **100%** |

---

## Version 2.1.0

**Release Date:** 2026-06-20

### What's New

#### DFI 5.0 Interface

- Complete DFI 5.0/5.1 implementation
- Low power state management
- Frequency change protocol
- PHY training interface
- Command encoding

#### Channel Model Enhancements

- Independent channel timing
- Enhanced bank state machine
- FAW tracking
- Per-channel statistics

### Breaking Changes

- `DFIInterface` renamed to `DFI5Interface`
- Command encoding changed to 5-bit format

---

## Version 2.0.0

**Release Date:** 2026-06-15

### What's New

#### HBM4 Support

- 32-channel architecture
- 8-16 GT/s data rates
- Pseudo-channel support
- Bank group organization
- PAM3 encoding

#### Phase A-F Complete

| Phase | Feature | Status |
|-------|---------|--------|
| A | HBM Controller Model | Complete |
| B | DRAM Timing Model | Complete |
| C | PHY Integration | Complete |
| D | RTL-Python Integration | Complete |
| E | Documentation | Complete |
| F | Verification | Complete |

---

## Upgrade Guide

### Upgrading from v2.1.x to v2.2.0

1. **No API changes** required for existing code
2. New optional features available:
   - `HBM4UnifiedSimulator` for combined simulations
   - `RTLInterface` for RTL co-simulation
   - `gem5_bridge` for system simulation

### Upgrading from v2.0.x to v2.1.0

1. Update import:
   ```python
   # Old
   from model.dram.dfi_interface import DFIInterface

   # New
   from model.dram.dfi_interface import DFI5Interface
   ```

2. Update command encoding if using raw commands:
   ```python
   # Old: 4-bit encoding
   cmd = 0b0001  # ACT

   # New: 5-bit encoding
   cmd = 0b00001  # ACT
   ```

---

## Known Issues

| Issue | Severity | Workaround |
|-------|----------|------------|
| gem5 bridge requires mock mode | Low | Use `--gem5` flag for mock |
| RTL simulation slow | Low | Use QUICK mode for testing |
| Lane repair limited to simulation | Low | Full support in RTL only |

---

## Deprecation Notes

The following will be removed in v3.0.0:

- `model.dram.channel_model` - Use `model.dram.hbm4_channel_model`
- `model.dram.timing` - Use `model.dram.hbm4_timing`

---

## Contact & Support

- **GitHub Issues:** https://github.com/dysonaicom-svg/hbm-system-model-public/issues
- **Documentation:** docs/README.md
- **Quick Reference:** docs/QUICKREF.md
