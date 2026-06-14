---
name: fpga-verification-runner
description: Use when running verification pipeline, testing multiple ORDER sizes, or comparing simulation results with golden reference - automates lint/build/sim/golden workflow
---

# FPGA Verification Runner Skill

## Overview

Run complete verification pipeline: lint → build → simulate → golden compare. Test across ORDER=8/16/64 and generate unified report.

## When to Use

- "run verification", "verify all tests"
- "test ORDER=16", "multi-size test"
- "compare with golden", "check accuracy"
- "full test suite", "regression test"
- After any RTL change before committing

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./verify_and_report.sh` | Full pipeline (lint→build→sim) |
| `./scripts/verify_all.sh` | Extended with golden compare |
| `make -C sim lint` | Lint only |
| `make -C sim build` | Build only |
| `make -C sim sim` | Simulate only |

## Execution Flow

```
1. Clean build artifacts
2. Run lint check (Verilator)
3. Build simulation
4. Run simulation for each ORDER size
5. Generate golden reference
6. Compare results
7. Report summary
```

## Multi-Size Testing

### Run across ORDER=8/16/64
```bash
for size in 8 16 64; do
    echo "=== Testing ORDER=$size ==="
    make -C sim clean
    make -C sim build ORDER=$size
    make -C sim sim ORDER=$size
done
```

### Quick size sweep
```bash
# Single command with size parameter
cd sim && for s in 8 16; do make clean && make sim ORDER=$s; done
```

## Verification Metrics

| Metric | Pass Criteria |
|--------|---------------|
| Lint | No errors |
| Build | Exit code 0 |
| Simulation | "Result: PASS" in output |
| Relative Error | < 1% (configurable) |
| Golden Match | Max diff < 1e-4 |

## Output Format

```
## Verification Results

### Step 1: Lint
✅ PASS - No errors

### Step 2: Build
✅ PASS - Build successful

### Step 3: Simulation
| ORDER | Status | Max Rel Error | Cycles |
|-------|--------|---------------|--------|
| 8     | PASS   | 2.3e-5       | 640    |
| 16    | PASS   | 4.1e-5       | 4608   |
| 64    | PASS   | 8.7e-5       | 270336 |

### Step 4: Golden Compare
| ORDER | HW Solution | Golden | Diff |
|-------|-------------|--------|------|
| 8     | 0x00010000  | 0x00010000 | 0    |

### Summary
- Overall: ✅ ALL CHECKS PASSED
- Log files: /tmp/fpga_verification_*/
```

## Golden Reference

### Run with comparison
```bash
python sim/golden_reference.py --size 8 --verbose
```

### Output format
```
# Golden Reference Output
# Format: Q16.16 hex values
# x[0] = 0x00010000 (1.000000)
# x[1] = 0x00020000 (2.000000)
```

### Pass criteria
- Max absolute error: < 1e-4
- Relative residual: < 1e-6
- No NaN/Inf values

## Integration with fpga-sim

This skill uses `fpga-sim` for individual steps:

| Step | Calls |
|------|--------|
| Lint | `fpga-sim` lint target |
| Build | `fpga-sim` build target |
| Sim | `fpga-sim` sim target |
| Golden | `matrix-gen` golden_reference.py |

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Lint errors | Syntax issues | Fix RTL, re-run |
| Build fails | Missing sources | Check Makefile |
| Sim timeout | Infinite loop | Check FSM |
| Golden mismatch | Precision loss | Check Q16.16 arithmetic |

## Automated Script

Use `scripts/verify_all.sh` for full pipeline:
```bash
cd /home/ic/FPGA-MixedSignal-Accelerator
./scripts/verify_all.sh
```

Output saved to `/tmp/fpga_verification_YYYYMMDD_HHMMSS/`