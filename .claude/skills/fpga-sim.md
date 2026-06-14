---
name: fpga-sim
description: Use when running Verilator simulations, building testbenches, or checking simulation results - automates make workflow and golden model comparison
---

# FPGA Simulation Skill

## Overview

Run Verilator simulations using the project's Makefile workflow, compare results with golden reference model, and analyze waveforms.

## When to Use

- "run simulation", "run sim", "simulate"
- "build the testbench", "make sim"
- "check the results", "compare with golden"
- After lint passes, before synthesis
- "run with ORDER=16", "test different sizes"

## Quick Reference

| Target | Command | Purpose |
|--------|---------|---------|
| Lint only | `make -C sim lint` | Syntax check, no build |
| Build | `make -C sim build` | Compile testbench |
| Simulate | `make -C sim sim` | Run and show output |
| With waves | `make -C sim waves` | Generate VCD file |
| Clean | `make -C sim clean` | Remove build artifacts |
| Demo | `make -C sim demo` | Run demo mode |

## Execution Flow

```
1. Check sim/Makefile exists
2. Determine target (lint/build/sim/waves)
3. Run make command
4. Capture output
5. If sim: compare with golden_reference.py
6. If waves: report VCD location
7. Report pass/fail with metrics
```

## Project Structure

```
FPGA-MixedSignal-Accelerator/
├── sim/
│   ├── Makefile              # Build/test workflow
│   ├── tb_top_fpga_mixed_signal.sv  # Main testbench
│   ├── tb_defs.svh          # Shared defines
│   ├── golden_reference.py   # Python golden model
│   └── golden_model_q16.py   # Q16.16 specific model
├── rtl/                      # RTL sources
├── obj_dir/                  # Verilator build output
└── sim_build/                # Final executables
```

## Golden Model Comparison

### Run with comparison
```bash
python sim/golden_reference.py --size 8 --verbose
```

### Output format for comparison
```
# Golden Reference Output
# Format: Q16.16 hex values
# Solution vector x:
# x[0] = 0x00010000 (1.000000)
```

### Pass criteria
- Max absolute error: < 1e-4
- Relative residual: < 1e-6
- No NaN/Inf values

## Simulation Modes

| Mode | Macro | Description |
|------|-------|-------------|
| Default | `SIM_MODE="TEST"` | Standard test with assertions |
| Demo | `SIM_MODE="DEMO"` | Visual output, reduced cycles |
| Debug | `+define+DEBUG` | Verbose internal signals |

### Run specific mode
```bash
cd sim_build && ./Vtb_top_fpga_mixed_signal +define+SIM_MODE=\"DEMO\"
```

## Output Format

```
## 🧪 Simulation Results

### Build Status
✅ Compilation successful (3.2s)

### Simulation Status
✅ PASS - All assertions passed

### Metrics
| Metric | Value |
|--------|-------|
| Cycles | 12,456 |
| Max error | 2.3e-5 |
| LU quality | PASS |

### Golden Comparison
| Test | Hardware | Golden | Diff |
|------|----------|--------|------|
| x[0] | 0x00010000 | 0x00010000 | 0 |

### Waveform
📁 VCD file: sim_build/tb_top_fpga_mixed_signal.vcd
   View with: gtkwave sim_build/tb_top_fpga_mixed_signal.vcd
```

## Multi-Size Testing

Run across ORDER=8, 16, 64:
```bash
for size in 8 16 64; do
    echo "=== Testing ORDER=$size ==="
    make -C sim clean
    make -C sim sim ORDER=$size
done
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "Vtb_top_fpga_mixed_signal not found" | Build failed | Run `make build` first |
| "WIDTHTRUNC warnings" | Index width mismatch | Add truncation or lint_off |
| "Assertion failed" | RTL bug or test error | Check assertion location |
| "Segmentation fault" | Memory access error | Check array bounds |

## Waveform Viewing

```bash
# With GTKWave
gtkwave sim_build/tb_top_fpga_mixed_signal.vcd

# Or use verilator_gui
verilator --gtkwave sim_build/tb_top_fpga_mixed_signal.vcd
```

## Environment Setup

Required tools:
```bash
# Verilator
verilator --version  # need 5.x+

# clang-18 (for C++20)
clang-18 --version

# GTKWave (optional, for waveforms)
gtkwave --version
```

Check with:
```bash
./install_env.sh
```