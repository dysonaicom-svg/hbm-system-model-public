# HBM UVM Verification Environment

## Overview

This is a comprehensive UVM 1.2 compatible verification environment for HBM (High Bandwidth Memory) controllers. The environment supports multiple traffic patterns, functional coverage, code coverage, and integration with reference models.

## Architecture

```
+--------------------------------------------------------------------------+
|                        Testbench (hbm_tb)                                |
|  +--------------------------------------------------------------------+  |
|  |                    UVM Environment (hbm_env)                       |  |
|  |  +-------------+  +-------------+  +-------------+  +-----------+ |  |
|  |  | HBM Agent   |  | AXI4 Agent  |  | Scoreboard  |  | Coverage  | |  |
|  |  | - Driver    |  | - Driver    |  | - Compare   |  | - cmd     | |  |
|  |  | - Monitor   |  | - Monitor   |  | - Queue     |  | - bank    | |  |
|  |  | - Sequencer |  | - Sequencer |  | - Mismatch  |  | - row     | |  |
|  |  +-------------+  +-------------+  +-------------+  +-----------+ |  |
|  |                              |                                      |  |
|  |  +---------------------------+------------------------------+       |  |
|  |  |             Register Model (RAL)                        |       |  |
|  |  |  - control    - status    - timing0/1    - interrupt   |       |  |
|  |  +--------------------------------------------------------+       |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
|  +----------------------------------------------------------------------+ |
|  |                 Reference Models (Integrated in TB)                 | |
|  |  +---------------+  +------------------+  +---------------------+  | |
|  |  | DRAM Ref Model |  | Timing Checker   |  | Bandwidth Calculator|  | |
|  |  | - Bank states  |  | - tRCD/tRP/tRAS  |  | - Sliding window    |  | |
|  |  | - Row hits     |  | - tRC/tRRD       |  | - Efficiency calc   |  | |
|  |  +---------------+  +------------------+  +---------------------+  | |
|  +----------------------------------------------------------------------+ |
|                                                                          |
|  +----------------------------------------------------------------------+ |
|  |              DUT (HBM Controller RTL)                                | |
|  |  - Command queue        - Bank arbitration                           | |
|  |  - Address mapping      - DRAM interface                             | |
|  +----------------------------------------------------------------------+ |
+--------------------------------------------------------------------------+
```

## Test Categories

### 1. QoS Priority Tests (`hbm_qos_test_pkg.sv`)

Tests for QoS scheduling, priority handling, and fairness.

| Test Sequence | Description |
|--------------|-------------|
| `priority_inheritance_seq` | Tests high-priority request precedence |
| `starvation_prevention_seq` | Ensures low-priority requests don't starve |
| `deadline_miss_seq` | Tests deadline enforcement and miss detection |
| `mixed_traffic_qos_seq` | Tests scheduler under mixed traffic |

| Test Class | Description |
|-----------|-------------|
| `hbm_qos_priority_test` | Priority inheritance test |
| `hbm_qos_starvation_test` | Starvation prevention test |
| `hbm_qos_deadline_test` | Deadline miss test |
| `hbm_qos_mixed_traffic_test` | Mixed traffic test |

### 2. Refresh Conflict Tests (`hbm_refresh_test_pkg.sv`)

Tests for refresh scheduling and conflicts with user traffic.

| Test Sequence | Description |
|--------------|-------------|
| `refresh_conflict_seq` | Tests refresh commands vs user traffic |
| `refresh_timing_violation_seq` | Tests refresh timing constraints (tREFI, tRFC) |
| `per_bank_refresh_seq` | Tests per-bank refresh (REFPB) functionality |
| `refresh_during_active_seq` | Tests refresh with active banks |
| `auto_refresh_seq` | Tests automatic refresh triggering |

| Test Class | Description |
|-----------|-------------|
| `hbm_refresh_conflict_test` | Refresh conflict test |
| `hbm_refresh_timing_test` | Refresh timing test |
| `hbm_per_bank_refresh_test` | Per-bank refresh test |
| `hbm_refresh_during_active_test` | Refresh during active test |
| `hbm_auto_refresh_test` | Auto-refresh test |

### 3. Bank Contention Tests (`hbm_bank_contention_test_pkg.sv`)

Tests for bank arbitration, conflicts, and scheduling.

| Test Sequence | Description |
|--------------|-------------|
| `bank_group_conflict_seq` | Tests access conflicts within bank groups |
| `bank_activation_conflict_seq` | Tests conflicts with active banks |
| `bank_round_robin_seq` | Tests fair bank arbitration |
| `bank_open_close_seq` | Tests precharge conflicts and timing |
| `cross_bank_scheduling_seq` | Tests scheduling across multiple banks |
| `bank_contention_stress_seq` | High-stress test with maximum utilization |

| Test Class | Description |
|-----------|-------------|
| `hbm_bank_group_conflict_test` | Bank group conflict test |
| `hbm_bank_activation_conflict_test` | Bank activation conflict test |
| `hbm_bank_round_robin_test` | Round-robin test |
| `hbm_bank_open_close_test` | Open/close test |
| `hbm_cross_bank_scheduling_test` | Cross-bank scheduling test |
| `hbm_bank_contention_stress_test` | Stress test |

### 4. Multi-Channel Interleaving Tests (`test_multi_channel_seq.sv`)

Tests for HBM4 multi-channel operation with 32 channels.

| Test Sequence | Description |
|--------------|-------------|
| `multi_channel_interleave_seq` | Tests interleaved access across 32 channels |
| `channel_conflict_seq` | Tests conflicts when multiple channels access same bank |

| Test Class | Description |
|-----------|-------------|
| `hbm_multi_channel_interleave_test` | Multi-channel interleaving test |
| `hbm_channel_conflict_test` | Channel conflict test |

### 5. Boundary Condition Tests (`hbm_boundary_test_pkg.sv`)

Tests edge cases and boundary conditions.

| Test Sequence | Description |
|--------------|-------------|
| `max_address_seq` | Tests maximum valid addresses |
| `min_address_seq` | Tests minimum valid addresses |
| `address_overflow_seq` | Tests behavior with addresses beyond range |
| `queue_full_seq` | Tests behavior when queue is full |
| `queue_empty_seq` | Tests behavior when queue is empty |
| `burst_boundary_seq` | Tests burst access at boundaries |
| `timing_boundary_seq` | Tests timing parameters at extremes |
| `data_pattern_boundary_seq` | Tests various data patterns |

| Test Class | Description |
|-----------|-------------|
| `hbm_max_address_test` | Max address test |
| `hbm_min_address_test` | Min address test |
| `hbm_address_overflow_test` | Overflow test |
| `hbm_queue_full_test` | Queue full test |
| `hbm_queue_empty_test` | Queue empty test |
| `hbm_burst_boundary_test` | Burst boundary test |
| `hbm_timing_boundary_test` | Timing boundary test |
| `hbm_data_pattern_boundary_test` | Data pattern boundary test |

### 6. Coverage Collection (`hbm_coverage_pkg.sv`)

Comprehensive coverage models for verification completeness.

| Coverage Group | Description |
|---------------|-------------|
| `command_coverage` | Command type coverage (ACT, READ, WRITE, PRE, REF) |
| `bank_coverage` | Bank access patterns and bank groups |
| `row_coverage` | Row access patterns (hits, misses, regions) |
| `column_coverage` | Column and burst coverage |
| `qos_coverage` | QoS priority levels and deadlines |
| `refresh_coverage` | Refresh operation coverage |
| `timing_coverage` | Timing parameter coverage (tRCD, tRP, tRAS, tRC) |
| `transaction_coverage` | Complete transaction patterns |

## Quick Start

```bash
cd verification/uvm

# Compile
make compile

# Run single test
make run_qos_priority

# Run test suite
make test-qos

# Generate coverage
make coverage
```

## Test Selection

### Basic Tests
```bash
make run_single              # Single read test
make run_write               # Single write test
make run_write_read          # Write-read test
make run_hotspot             # Hotspot test
make run_random              # Random traffic test
make run_bank_stress         # Bank stress test
make run_comprehensive       # Comprehensive test
```

### QoS Priority Tests
```bash
make run_qos_priority        # Priority inheritance test
make run_qos_starvation      # Starvation prevention test
make run_qos_deadline        # Deadline test
make run_qos_mixed           # Mixed traffic test
make test-qos                # Run all QoS tests
```

### Refresh Tests
```bash
make run_refresh_conflict    # Refresh conflict test
make run_refresh_timing     # Refresh timing test
make run_per_bank_refresh    # Per-bank refresh test
make run_refresh_during_active  # Refresh during active test
make run_auto_refresh        # Auto-refresh test
make test-refresh            # Run all refresh tests
```

### Bank Contention Tests
```bash
make run_bank_group_conflict     # Bank group conflict test
make run_bank_activation_conflict # Bank activation conflict test
make run_bank_round_robin        # Round-robin test
make run_bank_open_close         # Open/close test
make run_cross_bank_scheduling    # Cross-bank scheduling test
make run_bank_contention_stress  # Stress test
make test-bank                   # Run all bank tests
```

### Multi-Channel Tests
```bash
make run_multi_channel_interleave # Multi-channel interleaving test
make run_channel_conflict         # Channel conflict test
make test-multi-channel           # Run all multi-channel tests
```

### Boundary Tests
```bash
make run_max_address            # Max address test
make run_min_address            # Min address test
make run_address_overflow       # Overflow test
make run_queue_full             # Queue full test
make run_queue_empty            # Queue empty test
make run_burst_boundary         # Burst boundary test
make run_timing_boundary        # Timing boundary test
make run_data_pattern_boundary  # Data pattern test
make test-boundary              # Run all boundary tests
```

### Test Suites
```bash
make test-new          # Run all new test categories
make test-all-full     # Run all tests (comprehensive)
```

## Coverage

### Functional Coverage
- Command coverage (ACT, READ, WRITE, PRE, REF)
- Bank coverage (all 16 banks + bank groups)
- Row coverage (low/mid/high regions, hits/misses)
- Column coverage (all 4 columns)
- Cross coverage (cmd x bank, cmd x row, bank x row)
- QoS coverage (priority levels, deadlines)
- Refresh coverage (full/per-bank refresh)
- Timing coverage (tRCD, tRP, tRAS, tRC)

### Code Coverage
- FSM state coverage
- Branch coverage
- Line coverage
- Toggle coverage

### Coverage Report
```bash
make coverage
```

## File Structure

```
verification/uvm/
├── hbm_env_pkg.sv              # Environment package (base)
├── hbm_test_pkg.sv            # Base test package
├── hbm_coverage.sv            # Functional coverage
├── hbm_tb.sv                  # Testbench top
├── Makefile                   # Build system
├── uvm.f                      # File list
├── uvm_stub/                  # UVM stub library
├── tests/
│   ├── test_read_seq.sv               # Single read sequence
│   ├── test_write_seq.sv              # Single write sequence
│   ├── test_bank_conflict_seq.sv      # Bank conflict sequence
│   ├── test_refresh_seq.sv           # Refresh sequence
│   ├── test_multi_channel_seq.sv      # Multi-channel interleaving tests
│   ├── hbm_qos_test_pkg.sv            # QoS priority tests
│   ├── hbm_refresh_test_pkg.sv        # Refresh conflict tests
│   ├── hbm_bank_contention_test_pkg.sv # Bank contention tests
│   ├── hbm_boundary_test_pkg.sv       # Boundary condition tests
│   ├── hbm_coverage_pkg.sv            # Coverage collection
│   └── hbm_test_pkg_list.sv           # Test package index
└── ../reference_model/
    ├── dram_ref_model.sv      # DRAM reference model
    ├── timing_checker.sv      # Timing validator
    ├── bandwidth_calc.sv      # Bandwidth calculator
    └── addr_decoder_ref.sv   # Address decoder
```

## Status

The UVM verification environment is complete with:

- UVM 1.2 compatible infrastructure
- AXI4 master agent for traffic generation
- Scoreboard for data checking
- Functional coverage collection
- Code coverage collection
- Register model for configuration
- Reference models integrated in testbench
- Multiple test scenarios
- Comprehensive Makefile with multiple targets
- **QoS priority test suite** (4 tests)
- **Refresh conflict test suite** (5 tests)
- **Bank contention test suite** (6 tests)
- **Multi-channel interleaving test suite** (2 tests)
- **Boundary condition test suite** (8 tests)
- **Coverage collection package** (8 coverage groups)

### Issues Found and Fixed

1. **Fixed** - `hbm_coverage.sv` line 100: Syntax error - `endcase` instead of `endgroup`
2. **Note** - Reference model directory is at `verification/reference_model/`, not `verification/uvm/reference_model/`
3. **Note** - Some Makefile targets reference test classes not included in the main test package (e.g., `hbm_row_hammer_test`, `hbm_axi4_test`). These are defined in separate test packages in `tests/` directory.

### Test Categories Summary

| Category | Sequences | Test Classes |
|----------|-----------|--------------|
| Base Tests | 6 (single_read, single_write, random_traffic, write_read, bank_stress, hotspot) | 6 |
| QoS Tests | 4 (priority_inheritance, starvation_prevention, deadline_miss, mixed_traffic) | 4 |
| Refresh Tests | 5 (refresh_conflict, refresh_timing_violation, per_bank_refresh, refresh_during_active, auto_refresh) | 5 |
| Bank Contention | 6 (bank_group_conflict, bank_activation_conflict, bank_round_robin, bank_open_close, cross_bank_scheduling, bank_contention_stress) | 6 |
| Multi-Channel | 2 (multi_channel_interleave, channel_conflict) | 2 |
| Boundary Tests | 8 (max_address, min_address, address_overflow, queue_full, queue_empty, burst_boundary, timing_boundary, data_pattern_boundary) | 8 |
| Register Tests | 1 (register_test) | 1 |
| **Total** | **33** | **33** |

## Next Steps

1. Run `make compile` to verify compilation
2. Run `make test-new` to execute new test suites
3. Run `make coverage` to generate coverage reports
4. Integrate with actual RTL controller when ready