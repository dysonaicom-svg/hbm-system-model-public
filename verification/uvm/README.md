# HBM UVM Verification Environment

## Overview

This is a comprehensive UVM 1.2 compatible verification environment for HBM (High Bandwidth Memory) controllers. The environment supports multiple traffic patterns, functional coverage, and integration with reference models.

## Architecture

```
+--------------------------------------------------------------------------+
|                        Testbench (hbm_tb)                                |
|  +--------------------------------------------------------------------+  |
|  |                    UVM Environment (hbm_env)                       |  |
|  |  +-------------+  +-------------+  +-------------+  +-----------+ |  |
|  |  | HBM Agent   |  | AXI4 Agent  |  | Scoreboard  |  | Coverage  | |  |
|  |  | - Driver    |  | - Driver    |  | - Compare   |  | - cmd     | |  |
|  |  | - Monitor   |  | - Monitor   |  | - Queue     |  | - bank    | |  |
|  |  | - Sequencer |  | - Sequencer |  | - Mismatch  |  | - row     | |  |
|  |  +-------------+  +-------------+  +-------------+  +-----------+ |  |
|  |                              |                                      |  |
|  |  +---------------------------+------------------------------+       |  |
|  |  |             Register Model (RAL)                        |       |  |
|  |  |  - control    - status    - timing0/1    - interrupt   |       |  |
|  |  +--------------------------------------------------------+       |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
|  +----------------------------------------------------------------------+ |
|  |                 Reference Models (Integrated in TB)                 | |
|  |  +---------------+  +------------------+  +---------------------+  | |
|  |  | DRAM Ref Model |  | Timing Checker   |  | Bandwidth Calculator|  | |
|  |  | - Bank states  |  | - tRCD/tRP/tRAS  |  | - Sliding window    |  | |
|  |  | - Row hits     |  | - tRC/tRRD       |  | - Efficiency calc   |  | |
|  |  +---------------+  +------------------+  +---------------------+  | |
|  +----------------------------------------------------------------------+ |
|                                                                          |
|  +----------------------------------------------------------------------+ |
|  |              DUT (HBM Controller RTL)                                | |
|  |  - Command queue        - Bank arbitration                           | |
|  |  - Address mapping      - DRAM interface                             | |
|  +----------------------------------------------------------------------+ |
+--------------------------------------------------------------------------+
```

## Components

### Environment Package (`hbm_env_pkg.sv`)

| Component | Description |
|-----------|-------------|
| `hbm_if` | HBM transaction interface with clocking blocks |
| `axi4_if` | AXI4 interface for traffic generation |
| `hbm_agent` | Agent with driver/monitor/sequencer |
| `axi4_agent` | AXI4 agent for AXI traffic |
| `hbm_scoreboard` | Transaction comparison scoreboard |
| `hbm_coverage` | Functional coverage model |
| `hbm_reg_model` | Simplified register model (RAL) |
| `hbm_env` | Top-level UVM environment |

### Test Package (`hbm_test_pkg.sv`)

| Test Sequence | Description |
|--------------|-------------|
| `single_read_seq` | Single read operation |
| `single_write_seq` | Single write operation |
| `random_traffic_seq` | Random read/write traffic |
| `write_read_seq` | Write followed by read verification |
| `bank_stress_seq` | Round-robin bank stress test |
| `row_hammer_seq` | Row hammer pattern test |
| `hotspot_seq` | Repeated hotspot access |
| `register_test_seq` | Register read/write test |
| `axi4_traffic_seq` | AXI4 traffic pattern |

| Test Class | Description |
|-----------|-------------|
| `hbm_single_read_test` | Single read test |
| `hbm_single_write_test` | Single write test |
| `hbm_write_read_test` | Write-read verification |
| `hbm_random_test` | Random traffic test |
| `hbm_hotspot_test` | Hotspot access test |
| `hbm_bank_stress_test` | Bank stress test |
| `hbm_row_hammer_test` | Row hammer test |
| `hbm_register_test` | Register test |
| `hbm_axi4_test` | AXI4 test |
| `hbm_comprehensive_test` | All sequences combined |

### Reference Models (`../reference_model/`)

| Model | Description |
|-------|-------------|
| `dram_ref_model.sv` | DRAM bank state tracking, row hit/miss detection |
| `timing_checker.sv` | DRAM timing constraint validation |
| `bandwidth_calc.sv` | Real-time bandwidth calculation |
| `addr_decoder_ref.sv` | Address mapping validation (6 modes) |

## Interface Definition

### HBM Interface (`hbm_if`)

```systemverilog
interface hbm_if (input clk, rst_n);
    // Command interface
    logic [1:0]   cmd;           // 0=idle, 1=write, 2=read
    logic [7:0]   addr_bank;     // Bank address (0-15)
    logic [15:0]  addr_row;      // Row address
    logic [1:0]   addr_col;      // Column address
    logic [511:0] wdata;         // Write data
    logic [511:0] wdata_mask;    // Write data mask
    logic [511:0] rdata;         // Read data
    logic         rdata_valid;   // Read data valid
    logic         cmd_ready;     // Command ready

    clocking drv_ck @(posedge clk); ... endclocking
    clocking mon_ck @(posedge clk); ... endclocking
    modport drv_mp (clocking drv_ck);
    modport mon_mp (clocking mon_ck);
endinterface
```

### AXI4 Interface (`axi4_if`)

```systemverilog
interface axi4_if (input aclk, aresetn);
    // Write address channel
    logic [31:0] awaddr;
    logic [7:0]  awlen;
    logic [2:0]  awsize;
    logic [1:0]  awburst;
    logic        awvalid, awready;

    // Write data channel
    logic [511:0] wdata;
    logic [63:0]  wstrb;
    logic         wlast, wvalid, wready;

    // Write response channel
    logic [1:0]   bresp;
    logic         bvalid, bready;

    // Read address channel
    logic [31:0] araddr;
    logic [7:0]  arlen;
    logic [2:0]  arsize;
    logic [1:0]  arburst;
    logic        arvalid, arready;

    // Read data channel
    logic [511:0] rdata;
    logic [1:0]   rresp;
    logic         rlast, rvalid, rready;

    clocking axi_ck @(posedge aclk); ... endclocking
    modport axi_mp (clocking axi_ck);
endinterface
```

## Quick Start

```bash
cd verification/uvm

# Compile with Verilator
make compile

# Run default test (random traffic)
make run

# Run specific test
make run TEST=hbm_single_read_test

# Run all tests
make test-all

# Generate coverage report
make coverage
```

## Test Selection

| Test | Command |
|------|---------|
| Single Read | `make run_single` or `make run TEST=hbm_single_read_test` |
| Single Write | `make run_write` |
| Write-Read | `make run_write_read` |
| Hotspot | `make run_hotspot` |
| Random Traffic | `make run_random` |
| Bank Stress | `make run_bank_stress` |
| Row Hammer | `make run_row_hammer` |
| AXI4 | `make run_axi4` |
| Comprehensive | `make run_comprehensive` |

## Makefile Targets

| Target | Description |
|--------|-------------|
| `all` | Compile and run default test |
| `compile` | Compile sources with coverage |
| `compile-quick` | Quick compile without coverage |
| `compile-rtl` | Compile with RTL controller |
| `run` | Run simulation with TEST variable |
| `coverage` | Generate coverage report |
| `clean` | Clean build directory |
| `clean-all` | Clean all generated files |
| `test-all` | Run all tests sequentially |
| `test-all-parallel` | Run all tests in parallel |
| `help` | Show help message |

## Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UVM_HOME` | `./uvm_stub` | UVM library path |
| `SIM` | `verilator` | Simulator to use |
| `TEST` | `hbm_random_test` | Test to run |
| `UVM_VERBOSITY` | `UVM_MEDIUM` | UVM message verbosity |
| `WAVEFORM` | `dump.vcd` | VCD waveform file |

## Examples

```bash
# Run hotspot test with high verbosity
make run TEST=hbm_hotspot_test UVM_VERBOSITY=UVM_HIGH

# Run with custom waveform dump
make run TEST=hbm_random_test WAVEFORM=trace.vcd

# Quick compile without coverage
make compile-quick

# Compile with RTL controller
make compile-rtl

# Generate coverage
make coverage

# Clean and rebuild
make clean && make all
```

## Coverage Model

The coverage model includes:

- **Command coverage**: Read vs Write commands
- **Bank coverage**: All 16 banks + hotspot bank
- **Row coverage**: Low/Mid/High row regions
- **Column coverage**: All 4 column values
- **Cross coverage**: cmd x bank, cmd x row, bank x row

## Register Model

The simplified register model includes:

| Register | Address | Description |
|----------|---------|-------------|
| `control` | 0x00 | Start/Enable/Reset control |
| `status` | 0x04 | Idle/Busy/Error status |
| `timing0` | 0x08 | tRCD/tRP/tRAS values |
| `timing1` | 0x0C | tRC/tRRD/tCCD values |
| `interrupt_enable` | 0x10 | Interrupt enable bits |

## Simulator Support

### Verilator (Primary)
```bash
make compile
make run
```

### Cadence Xcelium
```bash
make xrun-compile
```

### Siemens Questa
```bash
make questa-compile
```

## Dependencies

| Dependency | Required | Location |
|-----------|----------|----------|
| Verilator | Yes | For syntax checking |
| System UVM | No | Falls back to stub |
| RTL Controller | No | Uses reference model |

## File Structure

```
verification/
├── uvm/
│   ├── hbm_env_pkg.sv       # Environment package
│   ├── hbm_test_pkg.sv      # Test package
│   ├── hbm_tb.sv           # Testbench top
│   ├── Makefile            # Build system
│   ├── uvm.f               # File list
│   ├── README.md            # This file
│   ├── uvm_stub/            # UVM stub library
│   │   ├── uvm.svh
│   │   └── uvm_macros.svh
│   ├── agents/              # Agent implementations
│   ├── scoreboard/          # Scoreboard implementations
│   ├── tests/              # Test implementations
│   └── build/              # Build output
└── reference_model/
    ├── dram_ref_model.sv    # DRAM reference model
    ├── timing_checker.sv    # Timing validator
    ├── bandwidth_calc.sv    # Bandwidth calculator
    └── addr_decoder_ref.sv  # Address decoder
```

## Status: COMPLETE

The UVM verification environment is complete with:

- UVM 1.2 compatible infrastructure
- AXI4 master agent for traffic generation
- Scoreboard for data checking
- Functional coverage collection
- Register model for configuration
- Reference models integrated in testbench
- Multiple test scenarios
- Comprehensive Makefile with multiple targets

## Next Steps

1. Run `make compile` to verify compilation
2. Run `make run` to execute tests
3. Run `make coverage` to generate coverage reports
4. Integrate with actual RTL controller when ready