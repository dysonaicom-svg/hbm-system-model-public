---
name: hdl-review
description: Use when reviewing RTL code, finding bugs, or checking for correctness issues in SystemVerilog - multi-angle parallel review with verification voting
---

# HDL Code Review Skill

## Overview

Comprehensive RTL code review using 9 parallel angles, with verification voting to confirm findings. Targets SystemVerilog pitfalls specific to FPGA development.

## When to Use

- "review the code", "find bugs"
- "check for issues", "code review"
- Before merging changes
- "is there a bug in matrix_solver"
- After bug reports to find root cause

## Quick Reference

| Mode | Command | Files |
|------|---------|-------|
| All RTL | `/hdl-review` | rtl/*.sv |
| Specific | `/hdl-review rtl/foo.sv` | specified files |
| Script | `./scripts/hdl-review.sh` | uses find |

## 9 Review Angles (Parallel)

### Correctness (5 angles)
1. **Line-by-line scan** - off-by-one, bounds, null, missing awaits
2. **Removed-behavior auditor** - removed guards, validations
3. **Cross-file tracer** - interface changes break callers
4. **Language-pitfall specialist** - SV-specific pitfalls
5. **Wrapper/proxy correctness** - protocol completeness

### Cleanup (3 angles)
6. **Reuse** - duplicated functionality
7. **Simplification** - unnecessary complexity
8. **Efficiency** - wasted resources/compute

### Architecture (1 angle)
9. **Altitude** - symptomatic fix vs root cause

## SystemVerilog Bug Patterns

### Critical
| Pattern | Example | Severity |
|---------|---------|----------|
| Off-by-one | `for (i=1; i<=N; i++)` when should be `i<N` | HIGH |
| Missing reset | `always_ff` without reset | HIGH |
| Incomplete case | `case (state)` without `default` | HIGH |
| Fake zero | `'0'` instead of `1'b0` | MEDIUM |
| X propagation | Uninitialized in `always_ff` | HIGH |
| Clock domain crossing | Missing `cdc_fifo` | CRITICAL |
| Uninitialized signal | `logic foo;` used before assigned | HIGH |
| Handshake violation | `valid` asserted without `ready` check | MEDIUM |
| Division by zero | `a / b` where `b` could be 0 | HIGH |
| Signed/unsigned mix | `$signed(a) + $unsigned(b)` | MEDIUM |

### Resource Issues
| Pattern | Example | Severity |
|---------|---------|----------|
| Large unpacked array | `[8192]` without BRAM inference | MEDIUM |
| Combinational loop | `assign a = b & a;` | CRITICAL |
| Parameter width mismatch | `param [3:0]` but used as `[7:0]` | MEDIUM |

### Cross-module Issues
| Pattern | Example | Severity |
|---------|---------|----------|
| Unconnected port | Module output not connected | LOW |
| Width mismatch | `.foo(8'b0)` when port expects 16-bit | MEDIUM |
| State machine deadlock | Unreachable state | HIGH |

## Known Pitfalls (from CLAUDE.md)

### 1. for loop in always_ff
```systemverilog
// ❌ BAD
logic [7:0] i;
always_ff @(posedge clk) begin
    for (i = 0; i < ORDER; i++) begin  // BLKANDNBLK error
```

```systemverilog
// ✅ GOOD
always_ff @(posedge clk) begin
    for (int i = 0; i < ORDER; i++) begin
```

### 2. Packed vs Unpacked
```systemverilog
// ❌ BAD - can't connect these directly
input  logic [NUM-1:0] signal_valid;           // packed
input  logic [31:0]     voltage_in [0:N-1];    // unpacked
```

### 3. Array index width
```systemverilog
// ❌ BAD - WIDTHTRUNC warning
logic [9:0] count;
queue_timestamp[count]  // 10-bit index into 256-deep array
```

## Verification Flow

```
1. Run 9 parallel agents (each finds ≤8 candidates)
2. Deduplicate and merge
3. Each candidate gets 1 verification vote:
   - CONFIRMED: real bug, high confidence
   - PLAUSIBLE: likely bug, needs manual check
   - REFUTED: not a bug, explain why
4. Keep only CONFIRMED or PLAUSIBLE
5. Gap sweep: 1 round to find missed issues
6. Return top 15 findings by severity
```

## Output Format

```json
[
  {
    "file": "rtl/matrix_solver.sv",
    "line": 142,
    "summary": "Division by zero when U[k,k] is singular",
    "severity": "CRITICAL",
    "failure_scenario": "matrix[i][i] ≈ 0 → division by zero → X output"
  },
  {
    "file": "rtl/event_scheduler.sv",
    "line": 89,
    "summary": "logic type for loop counter in always_ff",
    "severity": "ERROR",
    "failure_scenario": "Verilator BLKANDNBLK error, won't compile"
  }
]
```

## Limits
- Max 15 findings per review
- Empty array if no confirmed bugs
- Per-candidate: 1 vote (no retries)

## Red Flags - STOP and Report
- Code that compiles but produces wrong results
- Missing boundary checks
- Handshake protocols with race conditions
- Memory access without bounds checking