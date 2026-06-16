# HBM4 Controller Verification Plan

## Document Information
- **Version**: 1.1
- **Date**: 2026-06-16
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
| Test Name | Description | Priority | Status |
|-----------|-------------|----------|--------|
| `single_read_test` | Single read transaction | P0 | Existing |
| `single_write_test` | Single write transaction | P0 | Existing |
| `write_read_seq_test` | Write followed by read to same address | P0 | Existing |
| `random_traffic_test` | Random read/write transactions | P1 | Existing |
| `burst_pattern_test` | Various burst patterns and boundaries | P1 | **NEW** |

#### 2. Bank Contention Tests
| Test Name | Description | Priority | Status |
|-----------|-------------|----------|--------|
| `bank_conflict_seq_test` | Same bank, different rows | P0 | Existing |
| `bank_group_conflict_test` | Same bank group activation | P1 | **NEW** |
| `bank_activation_conflict_test` | Rapid same-bank activations | P1 | **NEW** |
| `bank_round_robin_test` | Fair round-robin scheduling | P1 | **NEW** |
| `bank_open_close_test` | Row open/close timing | P1 | Existing |
| `bank_contention_stress_test` | Maximum bank utilization | P2 | Existing |
| `multi_bank_round_robin_test` | Fair scheduling across all banks | P1 | **NEW** |
| `timing_violation_test` | DRAM timing constraint violations | P1 | **NEW** |

#### 3. QoS Priority Tests
| Test Name | Description | Priority | Status |
|-----------|-------------|----------|--------|
| `qos_priority_test` | High-priority requests served first | P1 | Existing |
| `qos_starvation_test` | Low-priority not starved | P1 | Existing |
| `qos_deadline_test` | Deadline miss detection | P2 | Existing |
| `qos_mixed_traffic_test` | Mixed priority traffic | P1 | Existing |
| `priority_inversion_test` | High-priority blocked by low | P1 | **NEW** |
| `qos_deadline_violation_test` | Deadline exceeded scenarios | P2 | **NEW** |
| `queue_starvation_test` | Requests never serviced | P1 | **NEW** |

#### 4. Refresh Tests
| Test Name | Description | Priority | Status |
|-----------|-------------|----------|--------|
| `refresh_conflict_test` | Refresh with user traffic | P1 | Existing |
| `refresh_timing_test` | Refresh timing constraints | P1 | Existing |
| `per_bank_refresh_test` | Per-bank refresh (REFPB) | P2 | **NEW** |
| `refresh_during_active_test` | Refresh with open rows | P2 | **NEW** |
| `auto_refresh_test` | Automatic refresh triggering | P2 | Existing |
| `refresh_collision_test` | Refresh colliding with traffic | P1 | **NEW** |

#### 5. Multi-Channel Tests
| Test Name | Description | Priority | Status |
|-----------|-------------|----------|--------|
| `multi_channel_interleave_test` | 32-channel interleaving | P1 | Existing |
| `channel_conflict_test` | Channel-to-bank conflicts | P2 | Existing |

#### 6. Boundary Tests
| Test Name | Description | Priority | Status |
|-----------|-------------|----------|--------|
| `max_address_test` | Maximum valid addresses | P1 | Existing |
| `min_address_test` | Minimum addresses (zero) | P1 | Existing |
| `queue_full_test` | Queue overflow handling | P1 | Existing |
| `queue_empty_test` | Idle queue behavior | P2 | Existing |
| `timing_boundary_test` | Min/max timing parameters | P2 | Existing |

#### 7. Stress Tests
| Test Name | Description | Priority | Status |
|-----------|-------------|----------|--------|
| `hotspot_test` | Repeated same location access | P1 | Existing |
| `bank_stress_test` | All banks stressed | P1 | Existing |
| `cross_bank_scheduling_test` | Complex bank dependencies | P2 | Existing |
| `comprehensive_test` | All scenarios combined | P2 | Existing |

## Coverage Model

### Coverage Groups (Enhanced)

#### 1. Command Coverage
- ACT, PRE, RD, WR, REF commands
- Command sequences (ACT-RD, ACT-WR, PRE-ACT, etc.)
- **NEW**: REFPB (per-bank refresh) command coverage

#### 2. Bank Coverage
- All 16 banks covered individually
- Bank groups (4 groups of 4 banks)
- Bank x Row cross coverage
- **NEW**: Bank group conflict detection

#### 3. Row Coverage
- Row regions (low, mid, high, max)
- Row patterns (same, increment, decrement, random)
- Row hit/miss tracking
- **NEW**: Row activation conflict (row hammer detection)

#### 4. Column Coverage
- Column values (0-3)
- Burst lengths (1, 2, 4, 8, 16)
- Column x Burst cross coverage
- **NEW**: Burst pattern coverage

#### 5. QoS Priority Coverage (Enhanced)
- Priority levels (critical, high, normal, low, idle)
- Deadline values (short, medium, long, none)
- **NEW**: Deadline violation tracking
- Priority x Bank, Priority x Command cross coverage
- Priority x Deadline cross coverage

#### 6. Priority Inversion Coverage (NEW)
- High-priority blocked detection
- Blocking priority level tracking
- Queue fill level during inversion
- High-priority x Queue fill cross coverage

#### 7. Starvation Coverage (NEW)
- Low-priority queue depth tracking
- Starvation detection flag
- Starvation duration tracking
- Low-priority x Starvation cross coverage

#### 8. Refresh Coverage (Enhanced)
- Refresh types (full, bank, per-bank)
- Refresh intervals (early, normal, late, timeout)
- **NEW**: Refresh collision detection
- **NEW**: Banks open during refresh tracking
- Refresh x Collision cross coverage

#### 9. Timing Coverage (Enhanced)
- tRCD, tRP, tRAS, tRC values
- **NEW**: tRRD, tCCD coverage
- **NEW**: Timing violation tracking
- **NEW**: Violation type categorization (tRRD, tRC, tRCD, tRP, tRAS)

#### 10. Transaction Coverage (Enhanced)
- Transaction type (read/write)
- Address coverage
- Data valid coverage
- Transaction success tracking
- **NEW**: Latency coverage buckets

#### 11. Queue Coverage (NEW)
- Queue fill level tracking
- Queue turnover rate
- Overflow detection

#### 12. Bank Group Conflict Coverage (NEW)
- Bank group identification
- Conflict detection flag
- tRRD violation tracking
- Bank group x Conflict cross coverage

### Coverage Goals
| Metric | Goal | Current |
|--------|------|---------|
| Command coverage | 100% | 87% |
| Bank coverage | 100% | 75% |
| Bank group coverage | 100% | 50% |
| Row address coverage | >90% | 65% |
| Column coverage | >95% | 60% |
| Channel coverage | >95% | 80% |
| QoS coverage | >80% | 45% |
| Priority inversion coverage | >70% | 0% |
| Starvation coverage | >70% | 0% |
| Refresh coverage | >85% | 60% |
| Timing coverage | >75% | 50% |
| Queue coverage | >80% | 0% |

### Coverage Improvement Plan
1. **Phase 1**: Add new test sequences targeting low-coverage areas
2. **Phase 2**: Run directed tests for missing coverage bins
3. **Phase 3**: Randomization improvements for better coverage
4. **Phase 4**: Coverage closure and sign-off

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

### Smoke Tests (Quick) - ~5 min
- `single_read_test`
- `single_write_test`
- `write_read_seq_test`
- `burst_pattern_test`

### Feature Tests (Medium) - ~30 min
- All bank contention tests
- All QoS tests
- All refresh tests

### Full Regression (Long) - ~60 min
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

## New Test Descriptions

### Priority Inversion Test
Tests scenarios where high-priority requests are blocked by lower-priority requests already queued. Verifies:
- High-priority request detection
- Queue blocking behavior
- Priority override mechanisms

### Refresh Collision Test
Tests refresh commands colliding with active user traffic. Verifies:
- Refresh timing during active operations
- Data integrity during refresh
- Collision detection and handling

### Bank Group Conflict Test
Tests bank group conflicts where 4 banks share timing constraints. Verifies:
- tRRD constraint between banks in same group
- Bank group arbitration
- Group-level scheduling fairness

### Bank Activation Conflict Test
Tests rapid activation of the same bank (row hammer patterns). Verifies:
- Row activation sequencing
- tRC constraint compliance
- Row hammer protection

### QoS Deadline Violation Test
Tests scenarios where transaction deadlines are exceeded. Verifies:
- Deadline tracking mechanism
- Deadline miss detection
- Priority escalation

### Queue Starvation Test
Tests starvation scenarios where some requests never get serviced. Verifies:
- Starvation detection
- Fair scheduling under load
- Low-priority request progress

### Multi-Bank Round-Robin Test
Tests fair round-robin scheduling across all banks. Verifies:
- Fairness across 16 banks
- Round-robin implementation
- Service count distribution

### Refresh During Active Test
Tests refresh commands with open rows. Verifies:
- Row preservation during refresh
- PRECHARGE before refresh
- Post-refresh row restoration

### Per-Bank Refresh Test
Tests REFPB (per-bank refresh) commands. Verifies:
- Per-bank refresh sequencing
- Bank-specific refresh timing
- Partial array refresh

### Timing Violation Test
Tests various DRAM timing constraint violations. Verifies:
- tRRD violation detection
- tRC violation detection
- Timing error reporting

### Burst Pattern Test
Tests various burst patterns and boundaries. Verifies:
- All burst lengths (1, 2, 4, 8, 16)
- Column boundary handling
- Burst scheduling

## Known Issues and Limitations

1. **Verilator UVM Stub**: Limited UVM functionality for simulation
2. **Coverage**: Covergroups not fully implemented in stub
3. **Parameterized Classes**: Limited support in Verilator
4. **RTL Integration**: Full RTL simulation pending

## Appendix: Test Execution

### Running Individual Tests
```bash
cd verification/uvm
make compile
make run TEST=hbm_single_read_test
make run TEST=hbm_hotspot_test
make run TEST=hbm_priority_inversion_test
make run TEST=hbm_refresh_collision_test
```

### Running Test Suites
```bash
make test-smoke    # Quick tests
make test-features # All feature tests
make test-new      # All new tests
make test-all      # Full regression
```

### Running New Tests
```bash
# Priority inversion
make run TEST=hbm_priority_inversion_test

# Refresh collision
make run TEST=hbm_refresh_collision_test

# Bank group conflict
make run TEST=hbm_bank_group_conflict_test

# All new tests
make test-new
```

### Viewing Results
- VCD waveform: `hbm_tb.vcd`
- Coverage report: `coverage/` directory

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-15 | Verification Team | Initial version |
| 1.1 | 2026-06-16 | Verification Team | Added 11 new test scenarios, enhanced coverage model |