---
name: fpga-vivado-runner
description: Use when running Vivado synthesis, implementation, generating bitstream, or checking project status - wraps Vivado MCP tools into workflow commands
---

# FPGA Vivado Runner Skill

## Overview

Wrap Vivado MCP tools into high-level workflow commands. Simplify synthesis, implementation, and bitstream generation for the project.

## When to Use

- "run synthesis", "synthesize the design"
- "implement", "run implementation"
- "generate bitstream", "build FPGA"
- "check project status", "Vivado status"
- "resource report", "timing report"

## Prerequisites

1. Vivado 2023.1 installed at `/opt/Xilinx/Vivado/2023.1/bin/vivado`
2. MCP server configured in `.mcp.json`
3. Hardware target board (or simulation mode)

## Quick Reference

| Task | MCP Command | Alternative |
|------|------------|--------------|
| List sessions | `mcp__vivado__list_sessions` | - |
| Start GUI | `mcp__vivado__start_session` | `vivado &` |
| Project info | `mcp__vivado__get_project_info` | - |
| Run synthesis | `mcp__vivado__run_synthesis` | Tcl script |
| Run impl | `mcp__vivado__run_implementation` | Tcl script |
| Generate bitstream | `mcp__vivado__generate_bitstream` | Tcl script |
| Resource report | `mcp__vivado__get_utilization_report` | - |
| Timing report | `mcp__vivado__get_timing_report` | - |
| CW check | `mcp__vivado__get_critical_warnings` | - |

## Workflows

### Workflow 1: Full Build (synth → impl → bitstream)

```
1. mcp__vivado__get_project_info      → Check project exists
2. mcp__vivado__run_synthesis        → Run synthesis
3. mcp__vivado__get_utilization_report → Check resource
4. mcp__vivado__run_implementation    → Run implementation
5. mcp__vivado__get_timing_report     → Check timing
6. mcp__vivado__check_bitstream_readiness → Pre-flight check
7. mcp__vivado__generate_bitstream    → Generate bitstream
```

### Workflow 2: Quick Synthesis Check

```
1. mcp__vivado__run_synthesis        → Run synthesis
2. mcp__vivado__get_utilization_report → Get resource usage
3. mcp__vivado__get_next_suggestion  → What to do next
```

### Workflow 3: Debug Implementation

```
1. mcp__vivado__get_run_progress     → Check status
2. mcp__vivado__get_critical_warnings → Get warnings
3. mcp__vivado__get_timing_report    → Check timing
4. mcp__vivado__get_utilization_report → Check resource
```

## MCP Tool Reference

### Session Management

```javascript
// Start new session (GUI mode)
{
  tool: "mcp__vivado__start_session",
  args: {
    session_id: "fpga_accel",
    mode: "gui",
    timeout: 120
  }
}

// List active sessions
{
  tool: "mcp__vivado__list_sessions"
}

// Stop session
{
  tool: "mcp__vivado__stop_session",
  args: { session_id: "fpga_accel" }
}
```

### Build Commands

```javascript
// Run synthesis
{
  tool: "mcp__vivado__run_synthesis",
  args: {
    session_id: "fpga_accel",
    run_name: "synth_1",
    jobs: 4,
    timeout_minutes: 30
  }
}

// Run implementation
{
  tool: "mcp__vivado__run_implementation",
  args: {
    session_id: "fpga_accel",
    run_name: "impl_1",
    jobs: 4,
    timeout_minutes: 60
  }
}

// Generate bitstream
{
  tool: "mcp__vivado__generate_bitstream",
  args: {
    session_id: "fpga_accel",
    impl_run: "impl_1",
    force: false,
    timeout_minutes: 30
  }
}
```

### Report Commands

```javascript
// Get project info
{
  tool: "mcp__vivado__get_project_info",
  args: { session_id: "fpga_accel" }
}

// Get utilization report
{
  tool: "mcp__vivado__get_utilization_report",
  args: { session_id: "fpga_accel" }
}

// Get timing report
{
  tool: "mcp__vivado__get_timing_report",
  args: { session_id: "fpga_accel" }
}

// Get critical warnings
{
  tool: "mcp__vivado__get_critical_warnings",
  args: {
    run_name: "impl_1",
    compare_with_last: true,
    session_id: "fpga_accel"
  }
}

// Check bitstream readiness
{
  tool: "mcp__vivado__check_bitstream_readiness",
  args: {
    impl_run: "impl_1",
    session_id: "fpga_accel"
  }
}
```

### Tcl Commands

```javascript
// Run custom Tcl
{
  tool: "mcp__vivado__run_tcl",
  args: {
    session_id: "fpga_accel",
    command: "report_utilization -return_string",
    timeout: 120
  }
}

// Safe Tcl with parameters
{
  tool: "mcp__vivado__safe_tcl",
  args: {
    session_id: "fpga_accel",
    template: "create_project {0} {1} -part {2}",
    args: ["my_proj", "C:/design", "xcvu37p-fsvh2892-2L-e"]
  }
}
```

## Output Format

```
## Vivado Runner Results

### Session: fpga_accel
Status: Active (GUI)

### Synthesis
| Run | Status | WNS | LUT | FF | BRAM | DSP |
|-----|--------|-----|-----|-----|------|-----|
| synth_1 | Complete | N/A | 3,234 | 4,521 | 8 | 4 |

### Implementation
| Run | Status | WNS | WHS | Status |
|-----|--------|-----|-----|--------|
| impl_1 | Complete | 0.123ns | 0.456ns | ✅ MET |

### Bitstream
| Check | Result | Notes |
|-------|--------|-------|
| Route Complete | ✅ | Done |
| CRITICAL WARNING | 0 | Clean |
| Timing | ✅ MET | WNS=0.123ns |

### Next Steps
1. Program device with bitstream
2. Or run timing simulation
```

## Project-Specific Configuration

For this project (`FPGA-MixedSignal-Accelerator`):

```javascript
// Project settings
const PROJECT = {
  name: "fpga_mixed_signal",
  part: "xcvu37p-fsvh2892-2L-e",  // UltraScale+ VU37P
  top: "top_fpga_mixed_signal",
  rtl_dir: "/home/ic/FPGA-MixedSignal-Accelerator/rtl",
  xdc_dir: "/home/ic/FPGA-MixedSignal-Accelerator/xdc"
};

// Target resources (ORDER=64)
const TARGET = {
  LUT: 10000,
  FF: 15000,
  BRAM: 16,
  DSP: 10,
  Fmax: "250MHz"  // Target
};
```

## Pre-flight Checklist

Before generating bitstream:

- [ ] `mcp__vivado__run_synthesis` completed
- [ ] `mcp__vivado__get_utilization_report` shows < 90% on all resources
- [ ] `mcp__vivado__run_implementation` completed
- [ ] `mcp__vivado__get_timing_report` shows WNS > 0
- [ ] `mcp__vivado__get_critical_warnings` count = 0

## Common Issues

| Issue | Check | Fix |
|-------|-------|-----|
| No project | `get_project_info` | `open_project` or `create_project` |
| Synthesis error | `get_critical_warnings` | Fix RTL |
| Timing fail | `get_timing_report` | Pipelining |
| CW > 0 | `get_critical_warnings` | Review warnings |
| Resource > 90% | `get_utilization_report` | Optimize RTL |

## Integration with Other Skills

- `fpga-synth`: Full synthesis workflow
- `fpga-resource-estimator`: Pre-synthesis estimate
- `fpga-verification-runner`: Post-build verification