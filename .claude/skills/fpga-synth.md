---
name: fpga-synth
description: Use when running Vivado synthesis, checking resource utilization, or estimating FPGA resource usage - automates synthesis workflow and interprets utilization reports
---

# FPGA Synthesis Skill

## Overview

Run Vivado synthesis, analyze resource utilization reports, and provide actionable feedback on design resource usage.

## When to Use

- "run synthesis", "synthesize", "synth"
- "check resource usage", "how many LUTs"
- "estimate resources", "will this fit"
- Before generating bitstream
- After RTL changes to check impact

## Quick Reference

| Action | Command | Tool |
|--------|---------|------|
| Synthesis | `make -C vivado synth` | Vivado |
| Implementation | `make -C vivado impl` | Vivado |
| Utilization | `mcp__vivado__get_utilization_report` | MCP |
| Timing | `mcp__vivado__get_timing_report` | MCP |
| Bitstream | `mcp__vivado__generate_bitstream` | MCP |

## Resource Types

### For XCVU37P (U280 HBM)

| Resource | Total | Critical Threshold |
|----------|-------|-------------------|
| LUT | 1,254,000 | > 70% (880,000) |
| FF | 2,508,000 | > 80% (2,000,000) |
| BRAM | 1,368 (36Kb) | > 60% (820) |
| DSP | 9,504 | > 70% (6,650) |
| URAM | 960 (288Kb) | > 60% (576) |

### Resource Estimation Formulas

```
LUTs ≈ (combinational_logic + shift_regs + muxes) / 0.6
FFs ≈ (registers + pipelines * stages)
BRAM ≈ (memories * depth) / 36Kb_per_BRAM
DSP ≈ (multipliers + dividers) * 1
```

## Execution Flow

```
1. Source Vivado environment: /opt/Xilinx/Vivado/2023.1/settings64.sh
2. Check/create Vivado project
3. Run synthesis (or use existing results)
4. Fetch utilization report via MCP
5. Analyze and report
6. Check timing if requested
```

## Vivado MCP Tools

### Get Utilization Report
```bash
mcp__vivado__get_utilization_report()
```
Returns: LUT/FF/BRAM/DSP/IOB percentages

### Get Timing Report
```bash
mcp__vivado__get_timing_report()
```
Returns: WNS/WHS, critical paths

### Run Synthesis
```bash
mcp__vivado__run_synthesis(jobs=4, timeout=30)
```

## Output Format

```
## 🔧 Synthesis Results

### Project
- Name: fpga_mixed_signal_accelerator
- Part: xcvu37p-fsvh2892-2L-e
- Top: top_fpga_mixed_signal

### Resource Utilization
| Resource | Used | Available | % | Status |
|----------|------|-----------|---|--------|
| LUT | 45,230 | 1,254,000 | 3.6% | ✅ OK |
| FF | 62,480 | 2,508,000 | 2.5% | ✅ OK |
| BRAM | 24 | 1,368 | 1.8% | ✅ OK |
| DSP | 8 | 9,504 | 0.1% | ✅ OK |

### Timing Summary
| Path | Slack | Status |
|------|-------|--------|
| WNS | 2.45ns | ✅ MET |
| WHS | 0.12ns | ✅ MET |

### Recommendations
- Resources well within limits
- No congestion concerns
- Ready for implementation
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| High LUT% (>80%) | Too much combinational logic | Pipelining, retiming |
| High BRAM% (>70%) | Memory config inefficient | Packed BRAM, URAM |
| Timing failing | Long combinational paths | Pipeline registers |
| High FF% | Large state machines | State encoding |
| DSP overflow | Unoptimized multipliers | Use DSP48 primitives |

## Vivado Project Structure

```
vivado/
├── fpga_mixed_signal_accelerator.xpr  # Project file
├── fpga_mixed_signal_accelerator.runs/
│   ├── synth_1/                       # Synthesis run
│   │   ├── top_utilization_synth.rpt
│   │   └── runme.log
│   └── impl_1/                       # Implementation run
│       ├── top_utilization_placed.rpt
│       └── runme.log
└── fpga_mixed_signal_accelerator.cache/
```

## Phase 1.2 Resource Targets

For matrix_solver with P=4 PE array:

| Module | LUT | FF | BRAM | DSP |
|--------|-----|-----|------|-----|
| PE Array (4x) | ~8,000 | ~12,000 | 4 | 4 |
| Divider Unit | ~2,000 | ~3,000 | 0 | 0 |
| BRAM Controller | ~1,500 | ~2,000 | 0 | 0 |
| Control FSM | ~500 | ~800 | 0 | 0 |
| **Total** | **~12,000** | **~18,000** | **4** | **4** |

## Checking Synthesis Status

```bash
# Via MCP
mcp__vivado__get_run_progress(run_name="synth_1")

# Via log
tail -50 vivado/vivado.log | grep -E "Phase|Progress|ERROR"
```

## Pre-synthesis Checklist

- [ ] All lint errors fixed
- [ ] All simulations passing
- [ ] Target part correct (xcvu37p-...)
- [ ] Timing constraints defined
- [ ] Clock period set (typically 10ns for 100MHz)