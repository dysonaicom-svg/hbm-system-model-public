---
name: fpga-protocol-checker
description: Use when checking handshake protocols, verifying ready/valid interfaces, or debugging pipeline stalls - validates AXI/ready-valid protocol correctness
---

# FPGA Protocol Checker Skill

## Overview

Check and verify ready/valid handshake protocols in RTL code. Detect common protocol violations like combinational loops, missing backpressure, and timing issues.

## When to Use

- "check protocol", "verify handshake"
- "debug ready/valid", "pipeline stall"
- "check backpressure", "AXI verification"
- "protocol violation", "handshake error"
- When simulation hangs or produces incorrect results

## Supported Protocols

| Protocol | Description | Common Use |
|----------|------------|------------|
| Ready/Valid | `ready` ← `valid` | Internal pipelines |
| AXI-Stream | `tready` ← `tvalid` | Data streams |
| AXI4 | Full address/data handshake | Memory interfaces |
| FIFO | `full`/`empty` flags | Buffer status |

## Ready/Valid Protocol Rules

### Correct Pattern
```systemverilog
// Producer
always_ff @(posedge clk) begin
    if (valid && ready) begin
        data <= '0;
        valid <= 1'b0;
    end
    if (new_data) begin
        data <= new_data;
        valid <= 1'b1;
    end
end

// Consumer
assign ready = !fifo_full;
```

### Common Violations

| Violation | Code | Issue | Fix |
|----------|------|-------|-----|
| Combinational ready | `assign ready = !stall_comb;` | Can glitch | Register ready signal |
| Valid without ready check | `valid <= 1;` | Data loss | Check `ready` before setting `valid` |
| Ready depends on valid | `assign ready = valid;` | Deadlock | `ready` must be independent |
| Unregistered signals | `ready_comb` | Timing issues | Register outputs |

## Protocol Checker Commands

### Find all handshake interfaces
```bash
# Find ready/valid pairs
grep -rn "ready\|valid" rtl/*.sv | grep -E "(input|output).*logic"

# Find AXI signals
grep -rn "tready\|tvalid\|tlast\|tkeep" rtl/*.sv
```

### Check protocol pattern
```bash
# Verify ready is registered
grep -A10 "always_ff" rtl/*.sv | grep -E "ready.*<="

# Check for combinational ready loops
grep -rn "assign.*ready" rtl/*.sv
```

## Protocol Violation Patterns

### 1. Combinational Ready Loop (DEADLOCK)
```systemverilog
// ❌ BAD: ready depends on internal state combinatorially
assign ready = (state == S_IDLE) && !stall;

// ✅ GOOD: ready is registered
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) ready <= 1'b0;
    else ready <= (state == S_IDLE) && !stall;
end
```

### 2. Valid Set Without Ready Check (DATA LOSS)
```systemverilog
// ❌ BAD: can set valid when not ready
always_ff @(posedge clk) begin
    if (new_data) valid <= 1'b1;  // May clobber pending data
end

// ✅ GOOD: only set valid when ready
always_ff @(posedge clk) begin
    if (ready && done) valid <= 1'b0;
    else if (new_data && !valid) valid <= 1'b1;  // Check not already valid
end
```

### 3. Backpressure Without Register (GLITCH)
```systemverilog
// ❌ BAD: combinational backpressure
assign ready = !almost_full;  // Can cause glitches

// ✅ GOOD: registered backpressure
always_ff @(posedge clk) begin
    ready <= !almost_full;
end
```

### 4. Handshake Without Reset (INIT STATE)
```systemverilog
// ❌ BAD: no reset for handshake signals
always_ff @(posedge clk) begin
    ready <= ...;  // Unknown initial state
end

// ✅ GOOD: reset valid/ready
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        valid <= 1'b0;
        ready <= 1'b1;
    end else begin
        ...
    end
end
```

## Protocol State Machine

```
┌─────────────────────────────────────────────────────────┐
│                    Handshake State                       │
│                                                           │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐            │
│   │ IDLE    │───▶│ WAIT_    │───▶│ ACTIVE  │            │
│   │         │    │ READY    │    │         │            │
│   └─────────┘    └─────────┘    └─────────┘            │
│        ▲              │               │                  │
│        │              ▼               ▼                  │
│        │         ┌─────────┐    ┌─────────┐            │
│        └─────────│ DEFER   │◀───│ ACCEPT  │            │
│                  │         │    │         │            │
│                  └─────────┘    └─────────┘            │
└─────────────────────────────────────────────────────────┘

IDLE:     No transaction pending
WAIT_READY: Valid asserted, waiting for ready
ACTIVE:   Handshake in progress
ACCEPT:   Handshake complete, data transferred
DEFER:    Ready deasserted, wait
```

## Verification Checklist

- [ ] `ready` is registered (not combinational)
- [ ] `valid` is only set when ready or before ready goes high
- [ ] `ready` is independent of `valid` (no combinational dependency)
- [ ] Handshake signals have reset initialization
- [ ] No combinational loops in ready/valid logic
- [ ] FIFO/threshold has hysteresis to avoid oscillation
- [ ] Backpressure propagates correctly through pipeline

## Output Format

```
## Protocol Check Results

### Handshake Interfaces Found
| Module | Signal | Direction | Registered | Protocol |
|--------|--------|----------|------------|----------|
| divider_unit | valid_in | input | ✅ | R/V |
| divider_unit | ready_out | output | ✅ | R/V |
| pe_array | start | input | ✅ | R/V |

### Violations Detected
| File | Line | Violation | Severity | Fix |
|------|------|-----------|----------|-----|
| rtl/foo.sv | 42 | Combinational ready | ERROR | Register ready |
| rtl/bar.sv | 55 | Valid set without ready check | WARN | Check ready first |

### Summary
- Interfaces: N
- Valid: M
- Violations: K (0 critical = PASS)
```

## Integration with fpga-lint

This skill complements `fpga-lint`:
- `fpga-lint`: Syntax and known pitfalls
- `fpga-protocol-checker`: Protocol correctness

## Common Debug Scenarios

| Symptom | Likely Cause | Check |
|---------|--------------|-------|
| Simulation hangs | Ready stuck low | Check ready logic |
| Data appears twice | Valid not cleared on handshake | Check valid <= 0 |
| Missing data | Ready depends on valid | Check ready independence |
| Glitchy output | Combinational ready | Register ready |

## Auto-Check Script

```bash
#!/bin/bash
# Protocol checker script
FILES="rtl/*.sv"

echo "## Checking ready/valid protocols..."

# Check for combinational ready
echo "### Combinational ready signals:"
grep -rn "assign.*ready" $FILES || echo "None found"

# Check for unregistered ready
echo "### Unregistered ready:"
grep -rn "output.*ready" $FILES | while read line; do
    file=$(echo $line | cut -d: -f1)
    line_num=$(echo $line | cut -d: -f2)
    if ! grep -B5 "output.*ready" $file | grep -q "always_ff.*ready"; then
        echo "WARN: $file:$line_num - ready may not be registered"
    fi
done

# Check for valid without ready check
echo "### Valid without ready check:"
grep -rn "valid.*<=" $FILES | grep -v "if.*ready" || echo "None found"
```