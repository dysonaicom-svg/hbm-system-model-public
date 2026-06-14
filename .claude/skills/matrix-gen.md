---
name: matrix-gen
description: Use when generating test matrices, creating golden reference data, or comparing hardware outputs against expected results for the matrix solver
---

# Matrix Generator Skill

## Overview

Generate test matrices and golden reference data for the FPGA matrix solver. Includes Q16.16 fixed-point conversion and LU decomposition verification.

## When to Use

- "generate matrix", "create test matrix"
- "golden reference", "expected output"
- "compare results", "verify accuracy"
- "test ORDER=16", "different matrix sizes"
- "generate random matrix", "sparse matrix"
- After simulation to verify results

## Quick Reference

| Task | Command |
|------|---------|
| Golden reference | `python sim/golden_reference.py --size 8` |
| Verbose output | `python sim/golden_reference.py --size 8 -v` |
| Random matrix | `python sim/golden_reference.py --size 16 --test random` |
| Hilbert matrix | `python sim/golden_reference.py --size 8 --test hilbert` |
| Q16.16 format | `python sim/golden_model_q16.py --size 8` |

## Test Matrix Types

| Type | Command | Use Case |
|------|---------|----------|
| Default (G-matrix) | `--test default` | Standard verification |
| Identity | `--test identity` | Sanity check |
| Random | `--test random` | Stress test |
| Hilbert | `--test hilbert` | Ill-conditioned |

### G-Matrix Pattern
```
2 -1  0  0 ...
-1  2 -1  0 ...
 0 -1  2 -1 ...
 0  0 -1  2 ...
```

Used for: Standard tests, matches common academic examples.

### Random Matrix
```python
A = random.randn(n, n)
A = A @ A.T + 2 * I  # Symmetric positive definite
```

Used for: Random verification, non-trivial solutions.

### Hilbert Matrix
```
H[i,j] = 1 / (i + j + 1)
```

Used for: Ill-conditioned matrices, numerical stability tests.

## Q16.16 Fixed-Point Format

### Conversion
```python
Q16_SCALE = 65536.0  # 2^16

def float_to_q16(f):
    return int(round(f * Q16_SCALE)) & 0xFFFFFFFF

def q16_to_float(q):
    if q >= 0x80000000:
        return (q - 0x100000000) / Q16_SCALE
    return q / Q16_SCALE
```

### Range
- Integer bits: 15 (signed)
- Fractional bits: 16
- Range: [-32768, 32767.999984]

## Output Format

```
## Matrix Generation Results

### Configuration
- Size: 8x8
- Type: default (G-matrix)
- Precision: Q16.16

### Matrix A (top-left 4x4)
  2.0000  -1.0000   0.0000   0.0000 ...
 -1.0000   2.0000  -1.0000   0.0000 ...

### Solution Vector x
[1.000000, 2.000000, 1.000000, 0.000000 ...]

### Q16.16 Output (hex)
# x[0] = 0x00010000 (1.000000)
# x[1] = 0x00020000 (2.000000)

### Verification
- ||L*U - A|| max error: 1.23e-14
- ||Ax - b|| residual: 2.45e-15
- Status: ✅ PASS
```

## Golden Reference Model

Located at: `sim/golden_reference.py`

### Features
- Pure Python (numpy)
- Floating-point LU decomposition
- Q16.16 input/output conversion
- Solution verification metrics

### Usage
```bash
# Basic
python sim/golden_reference.py --size 8

# Verbose (show L, U matrices)
python sim/golden_reference.py --size 16 --verbose

# Random matrix
python sim/golden_reference.py --size 64 --test random

# Compare with hardware output
python sim/golden_reference.py --size 8 --compare hw_output.txt
```

## Performance Estimation

```python
def estimate_cycles(n):
    """Estimate FPGA cycles for sequential LU"""
    lu_cycles = n * n * n         # O(n³) for LU
    solve_cycles = n * n * 2       # Forward/backward sub
    return lu_cycles + solve_cycles
```

| ORDER | LU Cycles | Solve Cycles | Total |
|-------|-----------|--------------|-------|
| 8 | 512 | 128 | 640 |
| 16 | 4,096 | 512 | 4,608 |
| 64 | 262,144 | 8,192 | 270,336 |

## Test Sizes for Phase 1.2

| Size | Use Case |
|------|----------|
| 8x8 | Quick verification |
| 16x16 | Main target |
| 64x64 | Stress test |

## File Formats

### Hex (for RTL simulation)
```
0x00010000  # x[0] = 1.0 in Q16.16
0x00020000  # x[1] = 2.0 in Q16.16
```

### CSV (for analysis)
```csv
index,float,q16_hex,q16_dec
0,1.0,0x00010000,65536
1,2.0,0x00020000,131072
```

### Binary (for memory initialization)
```python
import struct
struct.pack('>I', q16_value)  # Big-endian 32-bit
```