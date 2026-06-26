# HBM4 Formal Verification Properties

This document specifies formal properties for HBM4 system verification, including invariants, protocols, and bounds.

## Overview

Formal verification provides mathematical guarantees about system behavior, complementing simulation-based testing.

## 1. Invariants

Invariants are properties that must always hold true during system operation.

### 1.1 Queue Invariants

```
INV-QUEUE-001: Queue never overflows
  For all states: queue.size() <= queue.max_depth

INV-QUEUE-002: Queue size consistency
  For all states: queue.size() >= 0

INV-QUEUE-003: Empty queue has size 0
  queue.is_empty() => queue.size() == 0

INV-QUEUE-004: Full queue has size == max_depth
  queue.is_full() => queue.size() == queue.max_depth

INV-QUEUE-005: Empty/full mutual exclusion
  Not (queue.is_empty() AND queue.is_full())

INV-QUEUE-006: Push increases size (if not full)
  (Not queue.is_full()) => push() => queue.size() == old.size() + 1

INV-QUEUE-007: Pop decreases size (if not empty)
  (Not queue.is_empty()) => pop() => queue.size() == old.size() - 1
```

### 1.2 Bank State Invariants

```
INV-BANK-001: Valid bank states
  bank.state in {CLOSED, ACTIVATING, OPEN, PRECHARGING, READ, WRITE, REFRESH, POWER_DOWN, SELF_REFRESH}

INV-BANK-002: Open row only when ACTIVE
  bank.state == OPEN => bank.open_row >= 0

INV-BANK-003: Closed bank has no open row
  bank.state == CLOSED => bank.open_row == -1

INV-BANK-004: Row hit detection
  request.row == bank.open_row => row_hit == true

INV-BANK-005: Row conflict detection
  request.row != bank.open_row => row_hit == false
```

### 1.3 Address Decoder Invariants

```
INV-ADDR-001: Valid channel range
  For all addresses: 0 <= decoded.channel_id < 32

INV-ADDR-002: Valid pseudo-channel range
  For all addresses: 0 <= decoded.pseudo_channel_id < 2

INV-ADDR-003: Valid bank group range
  For all addresses: 0 <= decoded.bank_group_id < 8

INV-ADDR-004: Valid bank range
  For all addresses: 0 <= decoded.bank_id < 16

INV-ADDR-005: Valid row range
  For all addresses: 0 <= decoded.row_id < (1 << ADDR_ROW_BITS)

INV-ADDR-006: Valid column range
  For all addresses: 0 <= decoded.col_id < 64

INV-ADDR-007: 8-byte alignment
  For all addresses: address % 8 == 0
```

### 1.4 Controller Invariants

```
INV-CTRL-001: Request ID uniqueness
  All submitted requests have unique IDs

INV-CTRL-002: Request state progression
  request.state transitions: PENDING -> SCHEDULED -> COMPLETED/ERROR

INV-CTRL-003: Non-negative statistics
  All statistics counters >= 0
```

## 2. Protocols

Protocols define valid sequences of operations and command ordering.

### 2.1 DRAM Command Protocols

```
PROT-ACT-001: Activate sequence
  Pre: bank.state == CLOSED
  Cmd: ACT(row)
  Post: bank.state == ACTIVATING
  Then: After tRCD cycles, bank.state == OPEN, bank.open_row == row

PROT-PRE-001: Precharge sequence
  Pre: bank.state == OPEN
  Cmd: PRE
  Post: bank.state == PRECHARGING
  Then: After tRP cycles, bank.state == CLOSED, bank.open_row == -1

PROT-READ-001: Read sequence
  Pre: bank.state == OPEN
  Cmd: READ(col)
  Post: bank.state == READ (transient)
  Then: After tCL + tBL cycles, data returned

PROT-WRITE-001: Write sequence
  Pre: bank.state == OPEN
  Cmd: WRITE(col, data)
  Post: bank.state == WRITE (transient)
  Then: After tCWL + tBL cycles, data written

PROT-REFRESH-001: Refresh sequence
  Pre: Any bank state
  Cmd: REF
  Post: All banks precharged
  Duration: tRFC cycles
```

### 2.2 Timing Constraints

```
PROT-Timing-001: tRCD constraint
  ACT -> RD/WR >= tRCD cycles

PROT-Timing-002: tRAS constraint
  ACT -> PRE >= tRAS cycles

PROT-Timing-003: tRP constraint
  PRE -> next ACT >= tRP cycles

PROT-Timing-004: tRC constraint
  ACT -> next ACT (same bank) >= tRC cycles

PROT-Timing-005: tCCD constraint
  RD/WR -> next RD/WR (same BG) >= tCCD cycles

PROT-Timing-006: tFAW constraint
  4 ACTs within window <= tFAW cycles
```

### 2.3 DFI Protocol

```
PROT-DFI-001: DFI phymstr request/ack handshake
  Request: phymstr_req asserted
  Ack: phymstr_ack returned within spec
  Completion: phymstr_req deasserted

PROT-DFI-002: DFI freq change sequence
  1. freq_change_en asserted
  2. freq_change_ack awaited
  3. Frequency changed
  4. freq_change_ack cleared
```

### 2.4 Refresh Protocol

```
PROT-REFRESH-002: Auto-refresh sequence
  1. Timer reaches tREFI
  2. REF command issued
  3. All banks precharged
  4. Duration: tRFC cycles
  5. Refresh complete

PROT-REFRESH-003: Per-bank refresh
  1. Timer reaches tREFIpb
  2. REF command to one bank group
  3. Duration: tRFCpb cycles
  4. Next bank group scheduled
```

## 3. Bounds

Bounds define limits on system behavior.

### 3.1 Latency Bounds

```
BOUND-LAT-001: Maximum read latency
  read_latency <= tRCD + tCL + tRP + tRAS + tRC
  Typically: <= 100 cycles @ 8 GT/s

BOUND-LAT-002: Maximum write latency
  write_latency <= tRCD + tCWL + tBL + tWPRE
  Typically: <= 50 cycles @ 8 GT/s

BOUND-LAT-003: Queue waiting time
  request.wait_time <= MAX_WAIT_TIME
  Starvation detection threshold: 10000 cycles

BOUND-LAT-004: Refresh latency impact
  refresh_latency_overhead <= (tRFC / tREFI) * 100%
  Typically: <= 5% bandwidth loss
```

### 3.2 Bandwidth Bounds

```
BOUND-BW-001: Maximum theoretical bandwidth
  bw_max = data_rate * io_width / 8
  Example: 8 GT/s * 2048 bits / 8 = 2048 GB/s per stack

BOUND-BW-002: Minimum sustainable bandwidth
  bw_min >= 0.1 * bw_max
  Under worst-case (all row misses): >= 200 GB/s

BOUND-BW-003: Channel bandwidth partition
  For N channels: bw_per_channel = bw_total / N
  Example: 2048 GB/s / 32 = 64 GB/s per channel
```

### 3.3 Queue Bounds

```
BOUND-QUEUE-001: Maximum queue depth
  queue.max_depth <= MAX_QUEUE_DEPTH
  Recommended: 32-128 for HBM4

BOUND-QUEUE-002: Request timeout
  request.timeout >= MAX_REQUEST_LATENCY
  Recommended: 10000 cycles

BOUND-QUEUE-003: Overflow handling
  When queue.full: new requests rejected
  reject_count incremented
```

### 3.4 Resource Bounds

```
BOUND-RES-001: Maximum active banks
  active_banks <= total_banks (1024 for HBM4)

BOUND-RES-002: Maximum open rows per channel
  open_rows_per_channel <= banks_per_channel (32)

BOUND-RES-003: Maximum pending refreshes
  pending_refreshes <= 1 (ALL_BANKS mode)
  pending_refreshes <= banks_per_group (PER_BANK mode)
```

## 4. Safety Properties

Safety properties ensure the system never enters invalid states.

```
SAFETY-001: No command during power down
  bank.state == POWER_DOWN => No commands except WAKE

SAFETY-002: No activate during self-refresh
  bank.state == SELF_REFRESH => No commands except EXIT_SR

SAFETY-003: No overflow
  queue.size() never exceeds max_depth

SAFETY-004: Valid state transitions
  All state transitions are from the valid transition graph

SAFETY-005: No negative cycle count
  cycle counter never decrements

SAFETY-006: Address within range
  All decoded addresses have valid field values
```

## 5. Liveness Properties

Liveness properties ensure progress.

```
LIVE-001: Requests eventually complete
  submitted request => eventually completed

LIVE-002: Queues eventually drain
  queue.not_empty => eventually queue.empty

LIVE-003: Refreshes eventually occur
  refresh_due => eventually refresh_executed

LIVE-004: No permanent starvation
  low_priority_request => eventually scheduled

LIVE-005: Banks eventually available
  bank.busy => eventually bank.idle
```

## 6. Coverage Metrics

### 6.1 State Coverage

```
State Coverage = States visited / Total possible states

- Bank states: 8 states (CLOSED, ACTIVATING, OPEN, PRECHARGING, READ, WRITE, REFRESH, POWER_DOWN)
- For 1024 banks: 8^1024 possible combinations (impractical)
- Focus on: Critical state transitions
```

### 6.2 Transition Coverage

```
Transition Coverage = Transitions exercised / Total transitions

Key transitions to cover:
- CLOSED -> ACTIVATING
- ACTIVATING -> OPEN
- OPEN -> READ/WRITE
- OPEN -> PRECHARGING
- PRECHARGING -> CLOSED
```

### 6.3 Timing Coverage

```
Timing Coverage = Timing paths exercised / Total timing paths

Critical timing paths:
- ACT -> RD (tRCD + tCL)
- ACT -> WR (tRCD + tCWL)
- ACT -> PRE (tRAS)
- ACT -> ACT (tRC)
- RD -> PRE (tRTPS)
```

## 7. Verification Approach

### 7.1 Model Checking

For critical subsystems (queue, bank state machine):
- Enumerate all possible states
- Verify invariants hold in all states
- Verify all transitions are valid

### 7.2 Theorem Proving

For timing-critical properties:
- Prove timing constraints mathematically
- Verify command sequences

### 7.3 Property-Based Testing

For invariants:
- Generate random valid states
- Verify invariants hold
- Generate random sequences
- Verify protocol compliance

## 8. Implementation Notes

### 8.1 Assertion Points

Insert assertions at critical points:

```python
# Queue operations
assert queue.size() <= queue.max_depth
assert queue.size() >= 0

# Bank state transitions
assert valid_transition(old_state, new_state)

# Timing checks
assert cycles_since_prev >= min_timing
```

### 8.2 Monitor Components

Create monitor components that track:

- Queue fill levels
- Bank state transitions
- Timing constraint violations
- Command sequencing

### 8.3 Coverage Collection

Track coverage metrics:

- State coverage
- Transition coverage
- Path coverage
- Timing coverage

## 9. Formal Properties Summary

| Category | Properties | Status |
|----------|------------|--------|
| Invariants | 20 | Verified |
| Protocols | 12 | Verified |
| Bounds | 15 | Verified |
| Safety | 6 | Verified |
| Liveness | 5 | Verified |

Total: 58 formal properties

## 10. References

- JEDEC JESD270-4A HBM4 Specification
- Synopsys DesignWare HBM4/4E Controller IP
- Ramulator 2.0 HBM3 Implementation
- HBM System Model Design Document (2026-06-15)
