// ------------------------------------------------------------
// hbm_tb.sv - HBM Testbench Top Module
// ------------------------------------------------------------
module hbm_tb;

import uvm_pkg::*;
import hbm_env_pkg::*;
import hbm_test_pkg::*;
`include "uvm_macros.svh"

// Clock and reset
logic clk;
logic rst_n;

// Interface instance
hbm_if dut_if (clk, rst_n);

// DUT instantiation (placeholder - connect to actual HBM model)
hbm_dut dut (
    .clk         (clk),
    .rst_n       (rst_n),
    .cmd         (dut_if.cmd),
    .addr_bank   (dut_if.addr_bank),
    .addr_row    (dut_if.addr_row),
    .addr_col    (dut_if.addr_col),
    .wdata       (dut_if.wdata),
    .wdata_mask  (dut_if.wdata_mask),
    .rdata       (dut_if.rdata),
    .rdata_valid (dut_if.rdata_valid),
    .cmd_ready   (dut_if.cmd_ready)
);

// Clock generation (500MHz HBM clock)
initial begin
    clk = 0;
    forever #1ns clk = ~clk;  // 2ns period = 500MHz
end

// Reset generation
initial begin
    rst_n = 0;
    #100ns rst_n = 1;
end

// Initial block to run UVM test
initial begin
    // Set interface into config DB
    uvm_config_db #(virtual hbm_if.drv_mp)::set(null, "uvm_test_top.env.agent", "vif", dut_if.drv_mp);
    uvm_config_db #(virtual hbm_if.mon_mp)::set(null, "uvm_test_top.env.agent", "vif", dut_if.mon_mp);

    // Run test
    run_test();
end

// Timeout watchdog (10ms)
initial begin
    #10ms;
    `uvm_error("TIMEOUT", "Simulation timeout - test did not complete")
    $finish;
end

endmodule : hbm_tb

// ------------------------------------------------------------
// Placeholder DUT Module
// ------------------------------------------------------------
module hbm_dut (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [1:0] cmd,
    input  logic [7:0] addr_bank,
    input  logic [15:0] addr_row,
    input  logic [1:0] addr_col,
    input  logic [511:0] wdata,
    input  logic [511:0] wdata_mask,
    output logic [511:0] rdata,
    output logic        rdata_valid,
    output logic        cmd_ready
);
    // Simple model: always ready, no-op
    assign cmd_ready   = rst_n;
    assign rdata      = 512'h0;
    assign rdata_valid = 1'b0;
endmodule : hbm_dut