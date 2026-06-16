# HBM4 Controller Verification Plan

## Document Information
- **Version**: 1.0
- **Date**: 2026-06-15
- **Author**: HBM Verification Team
- **Status**: Draft

## Overview

This document defines the verification strategy, test plan, and coverage goals for the HBM4 Controller RTL implementation.

## Target Design

### HBM4 Controller Specification
- **Channels**: 32 independent channels
- **Banks per Channel**: 16 banks (4 bank groups x 4 banks)
- **Rows per Bank**: 65536 (16-bit row address)
- **Columns**: 256 (8-bit column address)
- **Data Width**: 256 bits per channel
- **Protocol**: PAM3 signaling (HBM4)
- **Interface**: DFI 5.0 compatible

### Key Parameters
| Parameter | Value |
|-----------|-------|
| tCK | 0.781 ns (1.28 GHz) |
| tRCD | 20 cycles |
| tRP | 20 cycles |
| tRAS | 40 cycles |
| tRC | 60 cycles |
| tRRD | 8 cycles |
| tCCD | 4 cycles |
| tREFI | 3.9 us |
| tRFC | 180 ns |

## Verification Goals

### Primary Goals
1. **Functional Coverage**: Verify all command types (ACT, PRE, RD, WR, REF)
2. **Bank Arbitration**: Verify fair bank scheduling and conflict resolution
3. **Queue Management**: Verify request queuing, prioritization, and overflow handling
4. **QoS Scheduling**: Verify priority-based scheduling and starvation prevention
5. **Refresh Handling**: Verify refresh commands don't corrupt user traffic
6. **Timing Compliance**: Verify all DRAM timing constraints are met

### Secondary Goals
1. **Performance Metrics**: Measure bandwidth utilization and latency
2. **Error Handling**: Verify error detection and reporting
3. **Power Management**: Verify low-power state transitions

## Verification Architecture

### Verification Components

```
+------------------+     +------------------+     +------------------+
| Traffic Gen/     | --> | HBM Controller   | --> | DRAM Reference   |
| Trace Reader     |     | (RTL)            |     | Model            |
+------------------+     +------------------+     +------------------+
                               |                         |
                               v                         v
                        +------------------+     +------------------+
                        | Scoreboard       | <-- | Timing Checker   |
                        +------------------+     +------------------+
                               |
                               v
                        +------------------+
                        | Coverage Collector|
                        +------------------+
```

### UVM Environment Components
1. **Agent**: HBM transaction driver/monitor
2. **Sequencer**: Transaction generation and scheduling
3. **Scoreboard**: Expected vs actual transaction comparison
4. **Coverage**: Functional and code coverage collection

## Test Plan

### Test Categories

#### 1. Basic Functionality Tests
| Test Name | Description | Priority |
|-----------|-------------|----------|
| `single_read_test` | Single read transaction | P0 |
| `single_write_test` | Single write transaction | P0 |
| `write_read_seq_test` | Write followed by read to same address | P0 |
| `random_traffic_test` | Random read/write transactions | P1 |

#### 2. Bank Contention Tests
| Test Name | Description | Priority |
|-----------|-------------|----------|
| `bank_conflict_seq_test` | Same bank, different rows | P0 |
| `bank_group_conflict_test` | Same bank group activation | P1 |
| `bank_activation_conflict_test` | Rapid same-bank activations | P1 |
| `bank_round_robin_test` | Fair round-robin scheduling | P1 |
| `bank_open_close_test` | Row open/close timing | P1 |
| `bank_contention_stress_test` | Maximum bank utilization | P2 |

#### 3. QoS Priority Tests
| Test Name | Description | Priority |
|-----------|-------------|----------|
| `qos_priority_test` | High-priority requests served first | P1 |
| `qos_starvation_test` | Low-priority not starved | P1 |
| `qos_deadline_test` | Deadline miss detection | P2 |
| `qos_mixed_traffic_test` | Mixed priority traffic | P1 |

#### 4. Refresh Tests
| Test Name | Description | Priority |
|-----------|-------------|----------|
| `refresh_conflict_test` | Refresh with user traffic | P1 |
| `refresh_timing_test` | Refresh timing constraints | P1 |
| `per_bank_refresh_test` | Per-bank refresh (REFPB) | P2 |
| `refresh_during_active_test` | Refresh with open rows | P2 |
| `auto_refresh_test` | Automatic refresh triggering | P2 |

#### 5. Multi-Channel Tests
| Test Name | Description | Priority |
|-----------|-------------|----------|
| `multi_channel_interleave_test` | 32-channel interleaving | P1 |
| `channel_conflict_test` | Channel-to-bank conflicts | P2 |

#### 6. Boundary Tests
| Test Name | Description | Priority |
|-----------|-------------|----------|
| `max_address_test` | Maximum valid addresses | P1 |
| `min_address_test` | Minimum addresses (zero) | P1 |
| `queue_full_test` | Queue overflow handling | P1 |
| `queue_empty_test` | Idle queue behavior | P2 |
| `timing_boundary_test` | Min/max timing parameters | P2 |

#### 7. Stress Tests
| Test Name | Description | Priority |
|-----------|-------------|----------|
| `hotspot_test` | Repeated same location access | P1 |
| `bank_stress_test` | All banks stressed | P1 |
| `cross_bank_scheduling_test` | Complex bank dependencies | P2 |
| `comprehensive_test` | All scenarios combined | P2 |

## Coverage Model

### Functional Coverage Points

#### Command Coverage
- ACT, PRE, RD, WR, REF commands
- Command sequences (ACT-RD, ACT-WR, PRE-ACT, etc.)

#### Address Coverage
- Bank: 0-15 (all banks)
- Row: Low, middle, high addresses
- Column: All 4 column values

#### Channel Coverage
- All 32 channels accessed
- Channel interleaving patterns

#### Transaction Coverage
- Read vs Write ratio
- Burst length variations
- Address patterns (sequential, random, stride)

### Timing Coverage
- Row hit rate
- Row conflict rate
- Bank group conflicts
- Queue fullness over time

### Coverage Goals
| Metric | Goal |
|--------|------|
| Command coverage | 100% |
| Bank coverage | 100% |
| Row address coverage | >90% |
| Channel coverage | >95% |
| Row hit rate | Track actual |

## Scoreboard Strategy

### Expected Transaction Storage
- Queue of expected transactions
- Key: transaction_id
- Data: cmd, addr_bank, addr_row, addr_col, wdata

### Comparison Logic
1. On driver: Store expected transaction
2. On monitor: Compare with expected
3. Report mismatches with details

### Data Verification
- Write data: Compare with expected
- Read data: Check valid flag and data pattern

## Regression Strategy

### Smoke Tests (Quick)
- `single_read_test`
- `single_write_test`
- `write_read_seq_test`

### Feature Tests (Medium)
- All bank contention tests
- All QoS tests
- All refresh tests

### Full Regression (Long)
- All tests
- Random seed variations

### CI Integration
```bash
# Quick smoke test
make test-smoke

# Feature tests
make test-features

# Full regression
make test-full
```

## Known Issues and Limitations

1. **Verilator UVM Stub**: Limited UVM functionality for simulation
2. **Coverage**: Covergroups not fully implemented in stub
3. **Parameterized Classes**: Limited support in Verilator

## Appendix: Test Execution

### Running Individual Tests
```bash
cd verification/uvm
make compile
make run TEST=hbm_single_read_test
make run TEST=hbm_random_test
```

### Running Test Suites
```bash
make test-smoke    # Quick tests
make test-features # All feature tests
make test-all      # Full regression
```

### Viewing Results
- VCD waveform: `hbm_tb.vcd`
- Coverage report: `coverage/` directory

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-15 | Verification Team | Initial version |