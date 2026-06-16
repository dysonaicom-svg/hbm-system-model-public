# HBM RTL Integration Plan
**Date**: 2026-06-15
**Version**: 1.0
**Status**: Phase D - Planning

---

## 1. Overview

This document defines the integration plan for connecting the HBM SystemC/Python model with RTL (Verilog/SystemVerilog) through DPI-C co-simulation. This is **Phase D** of the HBM modeling platform development.

### 1.1 Goals
- Enable cycle-accurate comparison between Python model and RTL
- Provide reference model for RTL verification
- Enable early performance validation before silicon

### 1.2 Current Status
| Component | Status |
|-----------|--------|
| Python Reference Model | Complete |
| RTL HBM Controller | Complete |
| UVM Testbench | Complete |
| DPI-C Binding | Not Started |

---

## 2. Integration Phases

### Phase D: RTL Co-simulation (4-6 weeks)

```
Week 1-2          Week 3-4          Week 5-6
+----------------+----------------+----------------+
| DPI-C Binding  | UVM Integration| End-to-End     |
| Python-RTL     | Testbench      | Verification   |
+----------------+----------------+----------------+
```

| Phase | Duration | Description |
|-------|----------|-------------|
| **D.1** | Week 1-2 | DPI-C binding setup, basic function calls |
| **D.2** | Week 3-4 | UVM testbench integration with RTL |
| **D.3** | Week 5-6 | End-to-end verification and regression |

---

## 3. Detailed Milestones

### 3.1 Week 1-2: DPI-C Binding

**Objective**: Enable Python to call RTL functions and vice versa

| Task | Description | Deliverable |
|------|-------------|-------------|
| D.1.1 | Setup DPI-C infrastructure | DPI-C header files, Makefile |
| D.1.2 | Implement basic read/write APIs | `dpi_read()`, `dpi_write()` functions |
| D.1.3 | Create Python wrapper layer | `pyhbm/rtl_interface.py` |
| D.1.4 | Basic connectivity test | Verified read/write round-trip |

**Key Files**:
```
sim/
├── dpi/                        # DPI-C implementation
│   ├── dpi_functions.c         # C wrapper for RTL
│   ├── dpi_functions.h
│   └── dpi_bindings.i          # SWIG interface
├── pyhbm/                      # Python DPI bindings
│   ├── rtl_interface.py        # Python wrapper
│   └── dpi_types.py            # Data type definitions
└── cosim/
    └── test_basic_dpi.py       # Connectivity test
```

### 3.2 Week 3-4: UVM Testbench Integration

**Objective**: Connect UVM environment with RTL and Python model

| Task | Description | Deliverable |
|------|-------------|-------------|
| D.2.1 | Integrate RTL with UVM | HDL integration in testbench |
| D.2.2 | Create DPI-C scoreboard | Compare RTL vs Model outputs |
| D.2.3 | Implement error injection | Test corner cases |
| D.2.4 | Add waveform debug support | VCD generation |

**Key Files**:
```
verification/
├── uvm/
│   └── hbm_env/
│       ├── hbm_scoreboard.sv   # Scoreboard with DPI
│       ├── hbm_predictor.sv    # Reference model predictor
│       └── hbm_env.sv          # Environment integration
└── dpi/
    └── uvm_dpi_adapter.sv      # DPI adapter for UVM
```

### 3.3 Week 5-6: End-to-End Verification

**Objective**: Complete verification coverage and regression

| Task | Description | Deliverable |
|------|-------------|-------------|
| D.3.1 | Full regression suite | 100+ test cases passing |
| D.3.2 | Performance comparison | Bandwidth/latency matching |
| D.3.3 | Corner case coverage | Refresh, bank conflicts |
| D.3.4 | Documentation | Integration guide |

---

## 4. Dependencies

### 4.1 External Dependencies
| Dependency | Source | Status |
|------------|--------|--------|
| SystemVerilog DPI-C support | Vivado Simulator | Available |
| Python CFFI or ctypes | Python | Available |
| UVM library | Verification IP | Available |

### 4.2 Internal Dependencies
| Dependency | Required By | Status |
|------------|------------|--------|
| RTL HBM Controller | Phase D.1 | Complete |
| Python Reference Model | Phase D.2 | Complete |
| UVM Environment | Phase D.2 | Complete |

---

## 5. Risks and Mitigations

### 5.1 Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| DPI-C performance overhead | High | Medium | Batch transactions, async processing |
| Timing synchronization mismatch | High | Medium | Cycle-accurate handshake protocol |
| Language boundary bugs | Medium | High | Comprehensive boundary testing |
| RTL/Model semantic differences | High | Medium | Detailed protocol documentation |

### 5.2 Schedule Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| DPI-C integration complexity | High | High | Spike early, buffer time for debugging |
| UVM/DPI interoperability issues | Medium | Medium | Pre-integration dry run |
| RTL changes requiring model updates | Low | Medium | Version control, regression tests |

### 5.3 Risk Response Strategies

1. **DPI-C Performance**: Start with small transaction batches, profile early
2. **Timing Sync**: Use cycle-accurate handshake with explicit ready/valid
3. **Boundary Testing**: Automated tests at each language boundary
4. **Documentation**: Maintain protocol spec with examples

---

## 6. Verification Plan

### 6.1 Test Categories

| Category | Test Count | Description |
|----------|------------|-------------|
| Basic Function | 20 | Read/write, address decode |
| Timing Accuracy | 30 | tRCD, tRP, tRAS verification |
| Bank Conflicts | 25 | Various conflict patterns |
| Refresh | 15 | Refresh during traffic |
| QoS | 10 | Priority handling |

### 6.2 Pass Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Bandwidth match | Within 5% | Compare peak BW |
| Latency match | Within 10% | Compare P50/P99 |
| Error rate | 0% | No protocol violations |

---

## 7. Timeline Summary

```
Week 1     Week 2     Week 3     Week 4     Week 5     Week 6
   |         |         |         |         |         |
   v         v         v         v         v         v
+---------+---------+---------+---------+---------+---------+
| DPI-C   |         | UVM     |         | E2E     |         |
| Binding |         | Integ   |         | Verify  |         |
+---------+---------+---------+---------+---------+---------+
   |         |         |         |         |         |
   M1 -------+         |         |         |         |
                     M2 -------+         |         |
                                   M3 -------+         |
                                             M4 -------+
```

| Milestone | Week | Description |
|-----------|------|-------------|
| M1 | Week 2 | DPI-C binding functional |
| M2 | Week 4 | UVM integration complete |
| M3 | Week 5 | Performance matching verified |
| M4 | Week 6 | All regression tests passing |

---

## 8. Documentation Requirements

| Document | Owner | Due |
|----------|-------|-----|
| DPI-C API Specification | AI | Week 1 |
| UVM Integration Guide | AI | Week 3 |
| Verification Plan | AI | Week 4 |
| Release Notes | AI | Week 6 |

---

## 9. Contact & Escalation

- **RTL Team**: Contact for RTL questions and changes
- **Model Team**: Contact for model questions and updates
- **Escalation**: Design decisions go through User (Designer/Reviewer)

---

**Document Status**: Phase D Planning
**Last Updated**: 2026-06-15