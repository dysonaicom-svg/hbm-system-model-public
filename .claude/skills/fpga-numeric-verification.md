---
name: fpga-numeric-verification
description: Use when verifying numerical accuracy, checking Q16.16 fixed-point precision, or comparing fixed-point vs floating-point results - validates numerical correctness
---

# FPGA Numeric Verification Skill

## Overview

Verify numerical accuracy of fixed-point implementations (Q16.16). Compare fixed-point results with golden floating-point reference to ensure precision requirements are met.

## When to Use

- "check precision", "verify accuracy"
- "compare Q16.16", "numerical error"
- "check overflow", "rounding error"
- "golden comparison", "bit-accurate"
- After any arithmetic change

## Q16.16 Format

```
┌─────────────────────────────────────────────┐
│  31  ...  16  │  15  ...   0              │
│  Integer Part │  Fractional Part            │
│   (16 bits)   │   (16 bits)                 │
└─────────────────────────────────────────────┘

Range: -32768.0 to +32767.999984
Precision: 1/65536 ≈ 1.5259e-5
```

## Conversion Functions

### Python (for golden reference)
```python
def q16_from_float(f: float) -> int:
    """Convert float to Q16.16"""
    result = int(f * 65536)
    return result & 0xFFFFFFFF

def q16_to_float(q: int) -> float:
    """Convert Q16.16 to float"""
    # Handle negative numbers
    if q & 0x80000000:
        q = q - 0x100000000
    return q / 65536.0

def q16_mul(a: int, b: int) -> int:
    """Q16.16 multiplication: result[47:16]"""
    result = (a * b) >> 16
    return result & 0xFFFFFFFF
```

### SystemVerilog
```systemverilog
function automatic logic signed [31:0] q16_mul(
    input logic signed [31:0] a,
    input logic signed [31:0] b
);
    logic signed [63:0] temp;
    temp = $signed(a) * $signed(b);
    q16_mul = temp[47:16];  // Q32.32 → Q16.16
endfunction

function automatic logic signed [31:0] q16_div(
    input logic signed [31:0] dividend,
    input logic signed [31:0] divisor
);
    logic signed [63:0] temp;
    temp = $signed(dividend) << 16;
    q16_div = temp / divisor;
endfunction
```

## Accuracy Metrics

| Metric | Formula | Pass Criteria |
|--------|----------|---------------|
| Absolute Error | \|FPGA - Float\| | < 1e-4 |
| Relative Error | \|FPGA - Float\| / \|Float\| | < 1e-3 |
| Max ULP | max(\|diff\| / precision) | < 1.0 |
| Bit Error Rate | wrong_bits / total_bits | < 0.1% |

## Common Operations

### Addition
```
FPGA:  a + b (with saturation)
Golden: float(a) + float(b)
Check:  |a_q16 + b_q16 - (a_float + b_float)| < 1.0
```

### Multiplication
```
FPGA:  q16_mul(a, b)
Golden: float(a) * float(b)
Check:  |q16_mul - golden| < 1e-4
```

### Division (Reciprocal)
```
FPGA:  q16_div(1, d)  or  Newton-Raphson
Golden: 1.0 / float(d)
Check:  |result - golden| < 1e-3
```

## Verification Script Template

```python
#!/usr/bin/env python3
"""Q16.16 Numeric Verification"""

import sys
import os

def q16_from_float(f):
    return int(f * 65536)

def q16_to_float(q):
    if q & 0x80000000:
        q = q - 0x100000000
    return q / 65536.0

def q16_mul(a, b):
    return ((a * b) >> 16) & 0xFFFFFFFF

def verify_multiplication(a_float, b_float, tolerance=1e-4):
    """Verify Q16.16 multiplication"""
    a_q = q16_from_float(a_float)
    b_q = q16_from_float(b_float)
    
    result_q = q16_mul(a_q, b_q)
    result_float = q16_to_float(result_q)
    golden = a_float * b_float
    
    abs_error = abs(result_float - golden)
    rel_error = abs_error / abs(golden) if golden != 0 else 0
    
    passed = abs_error < tolerance
    return {
        'passed': passed,
        'abs_error': abs_error,
        'rel_error': rel_error,
        'result': result_float,
        'golden': golden
    }

def main():
    # Test cases
    tests = [
        (1.0, 1.0, 1e-4),    # 1 × 1
        (2.0, 3.0, 1e-4),    # 2 × 3
        (0.5, 0.5, 1e-4),    # 0.5 × 0.5
        (-1.0, 2.0, 1e-4),   # -1 × 2
        (1e-6, 1e6, 1e-3),   # Edge case
    ]
    
    print("## Q16.16 Numeric Verification")
    print("| a | b | Result | Golden | Abs Err | Rel Err | Pass |")
    print("|---|-----|--------|--------|---------|--------|------|")
    
    all_passed = True
    for a, b, tol in tests:
        r = verify_multiplication(a, b, tol)
        status = "✅" if r['passed'] else "❌"
        print(f"| {a} | {b} | {r['result']:.6f} | {r['golden']:.6f} | {r['abs_error']:.2e} | {r['rel_error']:.2e} | {status} |")
        all_passed = all_passed and r['passed']
    
    if all_passed:
        print("\n✅ All tests passed")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Integration with sim/golden_reference.py

The project's golden reference uses Q16.16:

```bash
# Run golden reference
python sim/golden_reference.py --size 8 --verbose

# Expected output format
# A matrix (Q16.16):
#   A[0][0] = 0x00010000 (1.000000)
#   A[0][1] = 0x00020000 (2.000000)
# Solution:
#   x[0] = 0x00010000 (1.000000)
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Accumulator overflow | ORDER×Q16 > 32bit | Use 48-bit accumulator |
| Rounding bias | Truncation vs rounding | Add +0.5 before truncate |
| Saturation | Overflow | Saturate to MAX/MIN |
| Division by zero | Singular matrix | Check with EPSILON |

## Output Format

```
## Numeric Verification Results

### Q16.16 Multiplication
| Test | a | b | FPGA | Golden | Abs Error | Rel Error | Status |
|------|---|---|------|--------|-----------|-----------|--------|
| T1   | 1.0 | 1.0 | 1.000000 | 1.000000 | 0.00e+00 | 0.00e+00 | ✅ |
| T2   | 2.0 | 3.0 | 5.999985 | 6.000000 | 1.53e-05 | 2.55e-06 | ✅ |
| T3   | -1.0| 2.0 | -2.000000| -2.000000| 0.00e+00 | 0.00e+00 | ✅ |

### LU Decomposition Accuracy
| ORDER | Max Rel Error | Status |
|-------|---------------|--------|
| 8     | 2.3e-05       | ✅ PASS |
| 16    | 4.1e-05       | ✅ PASS |
| 64    | 8.7e-05       | ✅ PASS |

### Summary
- ✅ All operations verified
- ✅ Max relative error < 1e-3
- ✅ No overflow detected
```

## Pass Criteria for Matrix Solver

| Criterion | Value | Notes |
|-----------|-------|-------|
| Relative error (ORDER=8) | < 0.01% | Very strict |
| Relative error (ORDER=64) | < 0.1% | Relaxed |
| Singular detection | 100% | No false positives |
| No NaN/Inf | Required | Must be clean |