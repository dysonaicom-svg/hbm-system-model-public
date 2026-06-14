---
name: fpga-lint
description: Use when checking Verilog/SystemVerilog syntax, running lint, or fixing HDL code issues - automates Verilator/Verible checks and detects known SystemVerilog pitfalls
---

# FPGA Lint Skill

## Overview

Run static lint checks on RTL files and detect known SystemVerilog pitfalls from CLAUDE.md. Combines Verilator, Verible, and pattern-based checks.

## When to Use

- "check the code", "run lint", "syntax check"
- "lint the file", "find errors in RTL"
- After editing any `.sv` or `.v` file
- Before committing RTL changes

## Quick Reference

| Tool | Command | Purpose |
|------|---------|---------|
| Verilator | `verilator --lint-only -sv <files>` | Syntax/semantic check |
| Verible | `verible-verilog-lint <file>` | Style/best practice |
| Pattern | See Known Pitfalls below | Project-specific issues |

## Execution Flow

```
1. Identify target files (git diff or user-specified)
2. Run Verilator lint (always)
3. Run Verible lint (if installed)
4. Check known pitfalls from CLAUDE.md
5. Report findings with severity
```

## Known Pitfalls (from CLAUDE.md)

### 1. BLKANDNBLK - for loop in always_ff
```systemverilog
// ❌ BAD: logic type in for loop inside always_ff
logic [7:0] i;
always_ff @(posedge clk) begin
    for (i = 0; i < ORDER; i++) begin  // ERROR
```

```systemverilog
// ✅ GOOD: use int type (block-local)
always_ff @(posedge clk) begin
    for (int i = 0; i < ORDER; i++) begin  // OK
```

### 2. Packed vs Unpacked Array Mismatch
```systemverilog
// ❌ BAD: connecting packed to unpacked
input  logic [NUM-1:0] signal_valid;      // packed
input  logic [31:0]     voltage_in [0:N-1]; // unpacked - can't connect directly
```

```systemverilog
// ✅ GOOD: use intermediate signal or concatenation
.voltage_in({NUM_CHANNELS{1'b0}})  // for zero init
```

### 3. Array Index Width Warning
```systemverilog
// ❌ BAD: width mismatch causes WIDTHTRUNC
logic [9:0] count;  // 10 bits
queue_timestamp[count]  // only need 8 bits for 256 depth
```

```systemverilog
// ✅ GOOD: explicit truncation
queue_timestamp[count[7:0]]
// or add lint_off comment
/* verilator lint_off WIDTHTRUNC */
```

## Lint Commands

### Verilator (always available)
```bash
verilator --lint-only -Wno-fatal -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND \
    --no-timing --top-module <TOP> -sv <RTL_FILES>
```

### Verible (if installed)
```bash
verible-verilog-lint --lint_fatal=false <file>
```

### Project-specific lint script
```bash
./scripts/run_lint.sh
```

## Output Format

```
## 🔍 Lint Results

### Files Checked
- rtl/matrix_solver.sv
- rtl/event_scheduler.sv

### Verilator Output
[errors/warnings from Verilator]

### Verible Output
[errors/warnings from Verible]

### Known Pitfalls Detected
| File | Line | Issue | Severity |
|------|------|-------|----------|
| rtl/foo.sv | 42 | logic type in always_ff for loop | ERROR |

### Summary
- Errors: N
- Warnings: N
- Pitfalls: N
```

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `Unsupported: for/while inside always_ff with blocking` | loop in wrong always block | Move to always_comb or use int |
| `Signal is not declared` | typo or missing import | Check module name |
| `Port connection mismatch` | packed/unpacked type mismatch | Use intermediate signal |
| `WIDTHTRUNC` | index width exceeds array depth | Explicit truncation |

## Auto-detection Patterns

Run these grep patterns to find issues:
```bash
# Find logic/for in always_ff
grep -n "logic.*\].*;" rtl/*.sv | grep -A5 "always_ff"

# Find packed/unpacked issues
grep -n "input.*\[.*:.*\].*\[.*:.*\]" rtl/*.sv

# Find array index width issues
grep -n "\[.*\[.*:.*\]\]" rtl/*.sv
```