---
name: fpga-test-generator
description: Use when generating test cases, creating testbenches, or adding new test scenarios - automates test vector generation for matrix solver and other modules
---

# FPGA Test Generator Skill

## Overview

Automatically generate test vectors and testbenches for RTL modules. Focus on matrix solver tests but extensible to other modules.

## When to Use

- "generate test", "add new test case"
- "create testbench", "test matrix solver"
- "coverage test", "edge case test"
- "random test", "stress test"
- When adding new features or fixing bugs

## Quick Reference

| Test Type | Command | Purpose |
|---------|---------|---------|
| Unit test | `matrix-gen` | Single operation test |
| Integration | `tb_e2e_verification` | Full pipeline test |
| Stress | `python -m pytest` | Multiple random tests |
| Golden | `golden_reference.py` | Reference comparison |

## Test Categories

### 1. Unit Tests

Test individual operations (q16_mul, q16_div, etc.):

```python
# Test q16_mul accuracy
test_cases = [
    (1.0, 1.0),      # Identity
    (2.0, 3.0),      # Normal
    (-1.0, 2.0),     # Negative
    (0.5, 0.5),      # Fractional
    (1e-6, 1e6),     # Edge case
]
```

### 2. Matrix Tests

Test LU decomposition with various matrices:

```python
# Generate test matrices
matrices = [
    ("identity", identity_matrix(8)),
    ("diagonal", diagonal_matrix(8, 2.0)),
    ("random", random_matrix(8, seed=42)),
    ("singular", singular_matrix(8)),  # Should fail
    ("ill-conditioned", hilbert_matrix(8)),
]
```

### 3. Integration Tests

Test full solver pipeline:

```bash
# Test with different ORDER sizes
for size in 8 16 64; do
    make sim ORDER=$size
done

# Test with different number formats
for fmt in Q16.16 Q8.24 Q4.28; do
    make sim FORMAT=$fmt
done
```

## Test Matrix Templates

### Identity Matrix
```python
def identity_matrix(n):
    """Create n×n identity matrix"""
    A = [[0.0] * n for _ in range(n)]
    for i in range(n):
        A[i][i] = 1.0
    return A
```

### Diagonal Matrix
```python
def diagonal_matrix(n, value):
    """Create n×n diagonal matrix"""
    A = [[0.0] * n for _ in range(n)]
    for i in range(n):
        A[i][i] = value
    return A
```

### Random Matrix
```python
import random

def random_matrix(n, seed=None, min_val=-10.0, max_val=10.0):
    """Create n×n random matrix"""
    if seed:
        random.seed(seed)
    A = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            A[i][j] = random.uniform(min_val, max_val)
    return A
```

### Hilbert Matrix (ill-conditioned)
```python
def hilbert_matrix(n):
    """Create n×n Hilbert matrix (ill-conditioned)"""
    A = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            A[i][j] = 1.0 / (i + j + 1)
    return A
```

### Singular Matrix (for error detection)
```python
def singular_matrix(n):
    """Create n×n singular matrix"""
    A = [[1.0] * n for _ in range(n)]  # All rows identical
    return A
```

## Test Vector Generation

### Generate random test vectors
```bash
# Generate 100 random test cases
python sim/golden_reference.py --size 8 --random --count 100 --output tests/

# Generate edge cases
python sim/golden_reference.py --size 8 --edge-cases --output tests/
```

### Generate corner cases
```python
def generate_corner_cases():
    """Generate corner case test vectors"""
    cases = []
    
    # Near-zero pivot
    cases.append(([[1e-10, 1], [1, 1]], "near_zero_pivot"))
    
    # Large values
    cases.append(([[1e6, 1], [1, 1e6]], "large_values"))
    
    # Small values
    cases.append(([[1e-6, 1], [1, 1e-6]], "small_values"))
    
    # Mixed precision
    cases.append(([[1e15, 1e-15], [1e-15, 1e15]], "mixed_precision"))
    
    return cases
```

## Testbench Template

```systemverilog
`timescale 1ns / 1ps

module tb_matrix_solver_test;
    // Clock and reset
    logic clk = 0;
    logic rst_n = 0;
    
    // DUT signals
    logic [31:0] matrix_data [0:ORDER*ORDER-1];
    logic [$clog2(ORDER)-1:0] matrix_order;
    logic start, data_valid;
    logic [31:0] result_data [0:ORDER-1];
    logic result_valid, busy, ready;
    
    // Test control
    int test_count = 0;
    int pass_count = 0;
    
    // DUT instantiation
    matrix_solver #(
        .ORDER(ORDER)
    ) dut (.*);
    
    // Clock generation
    initial forever #5 clk = ~clk;
    
    // Test stimulus
    initial begin
        $display("=== Starting Tests ===");
        
        // Test 1: Identity matrix
        test_identity();
        
        // Test 2: Diagonal matrix
        test_diagonal();
        
        // Test 3: Random matrix
        test_random();
        
        $display("=== Tests Complete ===");
        $display("Passed: %d/%d", pass_count, test_count);
        $finish;
    end
    
    task test_identity;
        // Generate identity matrix
        for (int i = 0; i < ORDER; i++) begin
            for (int j = 0; j < ORDER; j++) begin
                matrix_data[i*ORDER + j] = (i == j) ? 32'h00010000 : 32'h0;
            end
        end
        matrix_order = ORDER;
        start <= 1; data_valid <= 1;
        @(posedge clk);
        start <= 0; data_valid <= 0;
        
        wait(result_valid);
        // Verify result (should be identity for identity input)
        check_result("identity", result_data);
    endtask
endmodule
```

## Test Coverage Goals

| Module | Coverage Target | Test Count |
|--------|----------------|------------|
| matrix_solver | 90% functional | 50 |
| q16_mul | 95% | 20 |
| q16_div | 95% | 20 |
| divider_unit | 90% | 30 |
| PE array | 85% | 40 |

## Edge Case Tests

### Numerical Edge Cases
```python
edge_cases = [
    # Zero
    {"name": "zero_matrix", "data": [[0]*8 for _ in range(8)]},
    
    # Near-zero
    {"name": "near_zero_pivot", "data": [[1e-10 if i==j else 1 for j in range(8)] for i in range(8)]},
    
    # Overflow
    {"name": "large_values", "data": [[1e6 if i==j else 0 for j in range(8)] for i in range(8)]},
    
    # Underflow
    {"name": "small_values", "data": [[1e-6 if i==j else 0 for j in range(8)] for i in range(8)]},
    
    # Negative
    {"name": "negative_diagonal", "data": [[-1 if i==j else 0 for j in range(8)] for i in range(8)]},
    
    # Singular
    {"name": "singular", "data": [[1]*8 for _ in range(8)]},
]
```

### Structural Edge Cases
```python
structural_cases = [
    {"name": "order_1", "order": 1, "data": [[1]]},
    {"name": "order_2", "order": 2, "data": [[2, 1], [1, 2]]},
    {"name": "order_min", "order": 1, "data": [[1]]},
    {"name": "order_max", "order": ORDER_MAX, "data": random_matrix(ORDER_MAX)},
]
```

## Output Format

```
## Test Generation Results

### Generated Test Vectors
| Test | Type | ORDER | Status |
|------|------|-------|--------|
| identity_8 | unit | 8 | ✅ |
| diagonal_16 | unit | 16 | ✅ |
| random_64 | stress | 64 | ✅ |
| hilbert_8 | numerical | 8 | ✅ |
| singular_8 | error | 8 | ⚠️ EXPECTED FAIL |

### Coverage Report
| Module | Statement | Branch | FSM |
|--------|-----------|--------|-----|
| matrix_solver | 92% | 88% | 95% |
| divider_unit | 96% | 90% | N/A |

### Summary
- Total tests: 100
- Passed: 95
- Failed: 5 (4 expected, 1 bug)
```

## Integration with Other Skills

- `fpga-sim`: Run generated tests
- `fpga-verification-runner`: Full test suite
- `matrix-gen`: Golden reference for comparison
- `fpga-numeric-verification`: Accuracy verification

## Auto-Generate Script

```bash
#!/bin/bash
# Generate test suite

PROJECT="/home/ic/FPGA-MixedSignal-Accelerator"
OUT_DIR="$PROJECT/sim/test_vectors"

mkdir -p "$OUT_DIR"

# Generate standard tests
python3 << EOF
import sys
sys.path.insert(0, "$PROJECT/sim")

from golden_reference import generate_matrix, TestMatrix

# Generate tests for ORDER=8
for name, generator in [
    ("identity", lambda n: TestMatrix.identity(n)),
    ("diagonal", lambda n: TestMatrix.diagonal(n, 2.0)),
    ("random", lambda n: TestMatrix.random(n, seed=42)),
    ("hilbert", lambda n: TestMatrix.hilbert(n)),
    ("singular", lambda n: TestMatrix.singular(n)),
]:
    mat = generator(8)
    mat.save(f"$OUT_DIR/{name}_8.mat")
    print(f"Generated: {name}_8.mat")

EOF

echo "Test generation complete: $OUT_DIR"
```