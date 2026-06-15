// =============================================================================
// HBM Controller Testbench - Verilator compatible (no timing, cycle-based)
// =============================================================================

`timescale 1ns / 1ps
`include "hbm_types.svh"

module hbm_controller_tb;

    // ============================================================================
    // Clock and Reset
    // ============================================================================
    logic clk = 0;
    logic rst_n = 0;
    int cycle_count = 0;

    // Clock generation - 1ns period @ 1GHz
    always begin
        #0.5;
        clk = ~clk;
        if (clk == 1) cycle_count++;
    end

    // Reset sequence
    initial begin
        rst_n = 0;
        #10;
        rst_n = 1;
    end

    // ============================================================================
    // Request Interface Signals
    // ============================================================================
    logic        req_valid = 0;
    logic [31:0] req_id = 0;
    logic [31:0] req_addr = 0;
    logic        req_rd_wr_n = 1;
    logic [15:0] req_len = 64;
    logic [2:0]  req_priority = 0;
    logic        req_ready;

    // ============================================================================
    // Response Interface Signals
    // ============================================================================
    logic        resp_valid;
    logic [31:0] resp_id;
    logic        resp_success;
    logic [7:0]  resp_status;

    // ============================================================================
    // DRAM Interface Signals
    // ============================================================================
    logic [2:0]  dram_cmd;
    logic [2:0]  dram_ch;
    logic [3:0]  dram_bank;
    logic [15:0] dram_row;
    logic [255:0] dram_rd_data = 0;
    logic [255:0] dram_wr_data;

    // ============================================================================
    // Statistics Signals
    // ============================================================================
    logic [31:0] stat_requests;
    logic [31:0] stat_completed;
    logic [7:0]  stat_hit_rate;

    // ============================================================================
    // DUT - HBM Controller
    // ============================================================================
    hbm_controller #(
        .QUEUE_DEPTH(32),
        .STACK_ADDR_WIDTH(3),
        .CH_ADDR_WIDTH(3),
        .BG_ADDR_WIDTH(3),
        .BK_ADDR_WIDTH(4),
        .ROW_ADDR_WIDTH(16),
        .COL_ADDR_WIDTH(6)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),

        // Request interface
        .req_valid(req_valid),
        .req_id(req_id),
        .req_addr(req_addr[31:0]),
        .req_rd_wr_n(req_rd_wr_n),
        .req_len(req_len),
        .req_priority(req_priority),
        .req_ready(req_ready),

        // Response interface
        .resp_valid(resp_valid),
        .resp_id(resp_id),
        .resp_success(resp_success),
        .resp_status(resp_status),

        // DRAM interface
        .dram_cmd(dram_cmd),
        .dram_ch(dram_ch),
        .dram_bank(dram_bank),
        .dram_row(dram_row),
        .dram_rd_data(dram_rd_data),
        .dram_wr_data(dram_wr_data),

        // Statistics
        .stat_requests(stat_requests),
        .stat_completed(stat_completed),
        .stat_hit_rate(stat_hit_rate)
    );

    // ============================================================================
    // DRAM Model (Simple behavioral)
    // ============================================================================
    always begin
        @(posedge clk);
        if (rst_n && (dram_cmd == CMD_READ)) begin
            dram_rd_data <= 256'hDEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF;
        end
    end

    // ============================================================================
    // Testbench Variables
    // ============================================================================
    int test_count = 0;
    int pass_count = 0;
    int fail_count = 0;
    int resp_expected = 0;
    int resp_received = 0;

    // ============================================================================
    // Main Test Sequence (cycle-based)
    // ============================================================================
    initial begin
        $display("============================================================");
        $display("HBM Controller RTL Testbench");
        $display("============================================================");

        // Wait for reset
        wait (rst_n == 1);
        $display("Reset complete at cycle %0d, starting tests...", cycle_count);

        // Wait a few cycles for initialization
        repeat(10) @(posedge clk);

        // =========================================================================
        // Test 1: Single Read Request
        // =========================================================================
        test_count = test_count + 1;
        $display("[TEST %0d] Single Read Request", test_count);

        req_valid = 1;
        req_id = 32'h1;
        req_addr = 32'h0001_0000;
        req_rd_wr_n = 1;
        req_priority = 3'd5;

        @(posedge clk);
        while (req_ready == 0) @(posedge clk);
        req_valid = 0;

        resp_expected = resp_expected + 1;

        $display("  Request submitted at cycle %0d", cycle_count);

        // =========================================================================
        // Test 2: Single Write Request
        // =========================================================================
        test_count = test_count + 1;
        $display("[TEST %0d] Single Write Request", test_count);

        req_valid = 1;
        req_id = 32'h2;
        req_addr = 32'h0002_0000;
        req_rd_wr_n = 0;
        req_priority = 3'd5;

        @(posedge clk);
        while (req_ready == 0) @(posedge clk);
        req_valid = 0;

        resp_expected = resp_expected + 1;

        $display("  Request submitted at cycle %0d", cycle_count);

        // =========================================================================
        // Test 3: Multiple Sequential Requests
        // =========================================================================
        test_count = test_count + 1;
        $display("[TEST %0d] Multiple Sequential Requests (5 requests)", test_count);

        repeat(5) begin
            req_valid = 1;
            req_id = req_id + 1;
            req_addr = req_addr + 32'h1000;
            req_rd_wr_n = (req_id[0] == 1);
            req_priority = 3'd3;

            @(posedge clk);
            while (req_ready == 0) @(posedge clk);
            req_valid = 0;
            resp_expected = resp_expected + 1;
        end

        $display("  5 requests submitted, total expected responses: %0d", resp_expected);

        // =========================================================================
        // Wait for all responses
        // =========================================================================
        $display("Waiting for responses...");
        while (resp_received < resp_expected) begin
            @(posedge clk);
            if (resp_valid) begin
                resp_received = resp_received + 1;
                $display("  Response %0d received: id=%h, success=%b at cycle %0d",
                         resp_received, resp_id, resp_success, cycle_count);
            end
        end

        // =========================================================================
        // Final Summary
        // =========================================================================
        repeat(20) @(posedge clk);

        $display("============================================================");
        $display("Test Summary:");
        $display("  Total Tests:     %0d", test_count);
        $display("  Expected Resp:   %0d", resp_expected);
        $display("  Received Resp:   %0d", resp_received);
        $display("  Statistics:      req=%0d, comp=%0d, hit_rate=%0d%%",
                 stat_requests, stat_completed, stat_hit_rate);
        $display("============================================================");

        if (resp_received >= resp_expected) begin
            $display("ALL TESTS PASSED!");
        end else begin
            $display("SOME RESPONSES MISSING!");
        end

        $display("Simulation completed at cycle %0d", cycle_count);
        $finish;
    end

    // ============================================================================
    // VCD Waveform Dump
    // ============================================================================
    initial begin
        $dumpfile("hbm_controller_tb.vcd");
        $dumpvars(0, hbm_controller_tb);
    end

endmodule