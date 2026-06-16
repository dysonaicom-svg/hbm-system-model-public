// =============================================================================
// HBM Controller Testbench - Single-process for --no-timing
// =============================================================================

`timescale 1ns/1ps
`include "hbm_types.svh"

module hbm_controller_tb_simple;

    // Clock - driven by main file in no-timing mode
    /* verilator lint_off STMTDLY */
    reg clk = 0;
    always #0.5 clk = ~clk;
    /* verilator lint_on STMTDLY */

    // Reset
    reg rst_n = 0;

    // Request/Response
    reg        tb_req_valid = 0;
    reg [31:0] tb_req_id = 0;
    reg [35:0] tb_req_addr = 0;
    reg        tb_req_rd_wr_n = 1;
    reg [15:0] tb_req_len = 64;
    reg [2:0]  tb_req_priority = 0;
    wire       tb_req_ready;

    wire       tb_resp_valid;
    wire [31:0] tb_resp_id;
    wire       tb_resp_success;
    wire [7:0] tb_resp_status;

    // DRAM interface
    wire [3:0]  tb_dram_cmd;
    wire [4:0]  tb_dram_ch;
    wire [2:0]  tb_dram_bg;
    wire [0:0]  tb_dram_pch;
    wire [3:0]  tb_dram_bank;
    wire [15:0] tb_dram_row;
    wire [255:0] tb_dram_rd_data;
    reg [255:0] tb_dram_wr_data = '0;

    // Statistics
    wire [31:0] tb_stat_requests;
    wire [31:0] tb_stat_completed;
    wire [7:0]  tb_stat_hit_rate;

    // DUT
    hbm_controller #(
        .QUEUE_DEPTH(32),
        .STACK_ADDR_WIDTH(2),
        .CH_ADDR_WIDTH(5)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .req_valid(tb_req_valid),
        .req_id(tb_req_id),
        .req_addr(tb_req_addr),
        .req_rd_wr_n(tb_req_rd_wr_n),
        .req_len(tb_req_len),
        .req_priority(tb_req_priority),
        .req_ready(tb_req_ready),
        .resp_valid(tb_resp_valid),
        .resp_id(tb_resp_id),
        .resp_success(tb_resp_success),
        .resp_status(tb_resp_status),
        .dram_cmd(tb_dram_cmd),
        .dram_ch(tb_dram_ch),
        .dram_bg(tb_dram_bg),
        .dram_pch(tb_dram_pch),
        .dram_bank(tb_dram_bank),
        .dram_row(tb_dram_row),
        .dram_rd_data(tb_dram_rd_data),
        .dram_wr_data(tb_dram_wr_data),
        .stat_requests(tb_stat_requests),
        .stat_completed(tb_stat_completed),
        .stat_hit_rate(tb_stat_hit_rate)
    );

    // Test variables
    integer cycle = 0;
    integer resp_count = 0;
    integer test_phase = 0;

    // Main test - single always block for --no-timing compatibility
    always @(posedge clk) begin
        if (!rst_n) begin
            // Reset phase
            cycle <= cycle + 1;
            if (cycle == 5) begin
                rst_n <= 1;
                cycle <= 0;
                $display("Reset released at cycle 0");
            end
        end else begin
            cycle <= cycle + 1;

            // Test 1: Send read request
            if (cycle == 1) begin
                test_phase <= 1;
                tb_req_valid <= 1;
                tb_req_id <= 32'h1;
                tb_req_addr <= 36'h0001_0000;
                tb_req_rd_wr_n <= 1;
                $display("Test 1: Read request at cycle %d", cycle);
            end

            if (cycle == 2 && tb_req_ready) begin
                tb_req_valid <= 0;
                $display("Request accepted at cycle %d", cycle);
            end

            // Collect response
            if (tb_resp_valid) begin
                resp_count <= resp_count + 1;
                $display("Response: id=%h success=%b status=%h at cycle %d", tb_resp_id, tb_resp_success, tb_resp_status, cycle);
            end

            // Test 2: Write request at cycle 20
            if (cycle == 20) begin
                test_phase <= 2;
                tb_req_valid <= 1;
                tb_req_id <= 32'h2;
                tb_req_addr <= 36'h0002_0000;
                tb_req_rd_wr_n <= 0;
                $display("Test 2: Write request at cycle %d", cycle);
            end

            if (cycle == 21 && tb_req_ready) begin
                tb_req_valid <= 0;
                $display("Write accepted at cycle %d", cycle);
            end

            // Summary at cycle 50
            if (cycle == 50) begin
                $display("========================================");
                $display("Test Complete at cycle %d", cycle);
                $display("Responses received: %d", resp_count);
                $display("Stats: req=%d completed=%d hit_rate=%d%%", tb_stat_requests, tb_stat_completed, tb_stat_hit_rate);
                $display("========================================");
                $finish;
            end
        end
    end

endmodule
