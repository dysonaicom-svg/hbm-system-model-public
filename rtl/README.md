# HBM Controller RTL

## Overview

This directory contains the Register Transfer Level (RTL) implementation of the HBM Controller, synthesized from the Python transaction-level model.

## Files

| File | Description |
|------|-------------|
| `hbm_types.svh` | SystemVerilog type definitions and constants |
| `hbm_controller.sv` | Main HBM controller RTL implementation |
| `dram_model.sv` | DRAM behavioral model for simulation |
| `hbm_controller_tb.sv` | SystemVerilog testbench |
| `hbm_controller_tb_main.cpp` | C++ main entry point for Verilator |
| `Makefile` | Build automation |

## Quick Start

### Lint Check (No Compilation)

```bash
make lint
```

### Build and Run Simulation

```bash
make sim
```

### Clean Build Artifacts

```bash
make clean
```

## Interface

### Request Interface

| Signal | Width | Direction | Description |
|-------|-------|-----------|-------------|
| `req_valid` | 1 | Input | Request valid |
| `req_id` | 32 | Input | Request ID |
| `req_addr` | 32 | Input | Request address |
| `req_rd_wr_n` | 1 | Input | Read/write indicator (1=read, 0=write) |
| `req_len` | 16 | Input | Burst length |
| `req_priority` | 3 | Input | Priority (0-7) |
| `req_ready` | 1 | Output | Ready to accept request |

### Response Interface

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `resp_valid` | 1 | Output | Response valid |
| `resp_id` | 32 | Output | Response ID |
| `resp_success` | 1 | Output | Success flag |
| `resp_status` | 8 | Output | Status code |

### DRAM Interface

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `dram_cmd` | 4 | Output | DRAM command |
| `dram_ch` | 3 | Output | Channel ID |
| `dram_bg` | 3 | Output | Bank group ID |
| `dram_bank` | 4 | Output | Bank ID |
| `dram_row` | 16 | Output | Row address |
| `dram_rd_data` | 256 | Input | Read data from DRAM |
| `dram_wr_data` | 256 | Output | Write data to DRAM |

## Simulation

The testbench runs a cycle-based simulation that:
1. Releases reset at cycle 10
2. Submits read/write requests
3. Collects responses
4. Reports statistics

Run with custom simulation time:
```bash
SIM_TIME=50us make sim
```

## Waveform Dumping

Build with waveform generation for debugging:
```bash
make sim-debug
```

This generates `obj_dir/Vhbm_controller_tb.vcd` which can be viewed with gtkwave:
```bash
gtkwave obj_dir/Vhbm_controller_tb.vcd
```

## Command Values

| Command | Value | Description |
|---------|-------|-------------|
| `CMD_IDLE` | 4'd0 | No operation |
| `CMD_WRITE` | 4'd1 | Write command |
| `CMD_READ` | 4'd2 | Read command |
| `CMD_ACT` | 4'd3 | Activate row |
| `CMD_PRE` | 4'd4 | Precharge bank |
| `CMD_REFB` | 4'd5 | Bank refresh |
| `CMD_REFSB` | 4'd6 | Per-bank refresh |

## Build Requirements

- Verilator 5.0+
- GCC with C++17 support
- GNU Make