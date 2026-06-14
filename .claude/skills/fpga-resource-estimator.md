---
name: fpga-resource-estimator
description: Use when estimating FPGA resource usage, checking if design fits, or planning implementation - estimates LUT/FF/BRAM/DSP from RTL code patterns
---

# FPGA Resource Estimator Skill

## Overview

Estimate FPGA resource utilization (LUT, FF, BRAM, DSP) from RTL code analysis. Use before synthesis to predict if design fits target device.

## When to Use

- "estimate resources", "will this fit"
- "check resource usage", "how many LUTs"
- "before synthesis", "planning implementation"
- "optimize design", "reduce resource"
- "target device fit", "XCVU37P"

## Target Devices

| Device | LUT | FF | BRAM36K | DSP |
|--------|-----|-----|--------|-----|
| XCVU37P (U280) | 1,254,000 | 2,508,000 | 1,368 | 9,504 |
| XCVU9P | 1,143,600 | 2,287,200 | 2,148 | 6,840 |
| XCAU25P | 93,920 | 187,840 | 96 | 192 |
| XQVU7P | 682,560 | 1,365,120 | 1,080 | 2,592 |

## Resource Estimation Formulas

### LUT Estimation

```javascript
// Basic LUT = combinational logic
luts += count_logic_gates() * 0.7;  // 70% utilization per gate

// Adders
luts += adders * 1.0;  // 1 LUT per bit for simple add
luts += multiplier_bits / 18;  // DSP slices used instead

// Muxes
luts += muxes * 1.5;  // 2:1 mux ≈ 1.5 LUTs

// Shift registers
luts += shift_regs * 1.0;
```

### FF Estimation

```javascript
// Registers (from always_ff)
ffs += register_count;

// Pipelines
ffs += pipeline_stages * data_width;

// State machines
ffs += state_count * state_encoding_bits;
```

### BRAM Estimation

```javascript
// BRAM36K = 36 Kbits per unit
// Total bits = depth * width

// Infer BRAM when:
// - Array size ≥ 512 words
// - Synchronous read/write
// - No complex address logic

if (array_depth >= 512 && access_pattern == "random") {
    bram_units = ceil(bits / 36_000);
}

// URAM = 288 Kbits per unit (UltraScale+)
if (device.includes("VU") && array_depth >= 4096) {
    uram_units = ceil(bits / 288_000);
}
```

### DSP Estimation

```javascript
// DSP48E2 (Ultrascale+)
// Capacity: 27×18 multiplier per DSP

// Multipliers
dsp += ceil(multiplier_width / 27) * ceil(multiplier_height / 18);

// Dividers (synthesized to multipliers)
dsp += ceil(divisor_width / 27) * ceil(divisor_height / 18);

// Accumulators
dsp += accumulators * 0.5;
```

## Common Patterns

### matrix_solver Resource Estimates

| Component | LUT | FF | BRAM | DSP |
|-----------|-----|-----|------|-----|
| BRAM Array (64×64×32) | 500 | 200 | 8 | 0 |
| PE Array (P=4) | 2,000 | 3,000 | 0 | 4 |
| Divider Unit (NR) | 800 | 600 | 0 | 1 |
| Control FSM | 300 | 400 | 0 | 0 |
| **Total ORDER=64** | **~3,600** | **~4,200** | **8** | **5** |

### BRAM Inference Rules

```systemverilog
// ✅ Inferred as BRAM
(* ram_style = "block" *)
logic [31:0] mem [0:1023];

// ⚠️ May NOT infer BRAM
logic [31:0] mem [0:63];  // Too small

// ⚠️ May NOT infer BRAM
always_comb begin
    mem[i] = ...;  // Async write
end
```

## Quick Estimation

### From RTL Files
```bash
# Count multipliers (DSP candidates)
grep -r "q16_mul\|q16_div\|multiplier" rtl/*.sv | wc -l

# Count BRAM declarations
grep -r "ram_style.*block" rtl/*.sv | wc -l

# Estimate state machine size
grep -r "typedef enum" rtl/*.sv
```

### From Architecture

```
LUT ≈ (Comb_LUT + FSM_LUT + Mux_LUT)
FF  ≈ (Registers + Pipeline_FF)
BRAM ≈ Σ(depth × width / 36Kb)
DSP  ≈ Σ(multipliers × 1)
```

## Output Format

```
## Resource Estimation

### Target Device: XCVU37P
| Resource | Estimated | Available | Usage | Status |
|----------|-----------|-----------|-------|--------|
| LUT | 3,600 | 1,254,000 | 0.3% | ✅ OK |
| FF | 4,200 | 2,508,000 | 0.2% | ✅ OK |
| BRAM | 8 | 1,368 | 0.6% | ✅ OK |
| DSP | 5 | 9,504 | 0.05% | ✅ OK |

### Critical Thresholds
- LUT > 70%: ⚠️ Warning - may have routing issues
- BRAM > 60%: ⚠️ Warning - check banking
- DSP > 70%: ⚠️ Warning - check utilization
```

## Optimization Tips

| Issue | Solution |
|-------|----------|
| High LUT% | Pipelining, retiming, reduce width |
| High BRAM% | Packed BRAM, URAM for large memories |
| High DSP% | Use DSP primitives, reduce precision |
| Timing fail | Add pipeline registers |

## Integration with fpga-synth

After estimation, use `fpga-synth` for actual synthesis:
- Estimation → Vivado synthesis → Report comparison
- Calibrate estimation accuracy over time