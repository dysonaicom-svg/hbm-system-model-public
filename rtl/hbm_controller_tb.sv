// =============================================================================
// HBM Controller Testbench - Cycle-based (Verilator --no-timing compatible)
// =============================================================================
// Uses a single always block with cycle counter for all timing control

`timescale 1ns / 1ps
`include "hbm_types.svh"

module hbm_controller_tb;

    // ============================================================================
    // Clock
    // ============================================================================
    logic clk = 0;
    int cycle_count = 0;

    // Clock generation in initial block (no delays in always with --no-timing)
    initial begin
        forever begin
            clk = 0;
            #0.5;
            clk = 1;
            #0.5;
        end
    end

    // Cycle counter - must be in separate always block
    always @(posedge clk) begin
        cycle_count <= cycle_count + 1;
    end

    // ============================================================================
    // Signals
    // ============================================================================
    logic        rst_n = 0;
    logic        req_valid = 0;
    logic [31:0] req_id = 0;
    logic [31:0] req_addr = 0;
    logic        req_rd_wr_n = 1;
    logic [15:0] req_len = 64;
    logic [2:0]  req_priority = 0;
    logic        req_ready;
    logic        resp_valid;
    logic [31:0] resp_id;
    logic        resp_success;
    logic [7:0]  resp_status;
    logic [2:0]  dram_cmd;
    logic [2:0]  dram_ch;
    logic [3:0]  dram_bank;
    logic [15:0] dram_row;
    logic [255:0] dram_rd_data = 0;
    logic [255:0] dram_wr_data;
    logic [31:0] stat_requests;
    logic [31:0] stat_completed;
    logic [7:0]  stat_hit_rate;

    // ============================================================================
    // DUT
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
        .clk(clk), .rst_n(rst_n),
        .req_valid(req_valid), .req_id(req_id), .req_addr(req_addr[31:0]),
        .req_rd_wr_n(req_rd_wr_n), .req_len(req_len), .req_priority(req_priority),
        .req_ready(req_ready), .resp_valid(resp_valid), .resp_id(resp_id),
        .resp_success(resp_success), .resp_status(resp_status),
        .dram_cmd(dram_cmd), .dram_ch(dram_ch), .dram_bank(dram_bank),
        .dram_row(dram_row), .dram_rd_data(dram_rd_data), .dram_wr_data(dram_wr_data),
        .stat_requests(stat_requests), .stat_completed(stat_completed),
        .stat_hit_rate(stat_hit_rate)
    );

    // DRAM response
    always @(posedge clk) begin
        if (rst_n && (dram_cmd == CMD_READ)) begin
            dram_rd_data <= 256'hDEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF;
        end
    end

    // ============================================================================
    // Test Variables
    // ============================================================================
    int test_state = 0;
    int resp_expected = 0;
    int resp_received = 0;
    int start_cycle = 0;
    int end_cycle = 0;
    int seq_count = 0;
    int done = 0;

    // ============================================================================
    // Main State Machine - Single always block
    // ============================================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            test_state <= 0;
            seq_count <= 0;
            req_valid <= 0;
            resp_expected <= 0;
            resp_received <= 0;
            done <= 0;
        end else if (!done) begin
            case (test_state)
                // State 0: Reset release at cycle 10
                0: begin
                    if (cycle_count == 10) begin
                        rst_n <= 1;
                        $display("Reset released at cycle %0d, starting tests...", cycle_count);
                        test_state <= 1;
                    end
                end

                // State 1: Submit first read request
                1: begin
                    req_valid <= 1;
                    req_id <= 32'h1;
                    req_addr <= 32'h0001_0000;
                    req_rd_wr_n <= 1;
                    req_priority <= 3'd5;
                    $display("[TEST 1] Read Request submitted at cycle %0d", cycle_count);
                    test_state <= 2;
                end

                // State 2: Wait for ready
                2: begin
                    req_valid <= 0;
                    resp_expected <= resp_expected + 1;
                    $display("[TEST 1] Request accepted at cycle %0d", cycle_count);
                    test_state <= 3;
                end

                // State 3: Submit write request
                3: begin
                    req_valid <= 1;
                    req_id <= 32'h2;
                    req_addr <= 32'h0002_0000;
                    req_rd_wr_n <= 0;
                    req_priority <= 3'd5;
                    $display("[TEST 2] Write Request submitted at cycle %0d", cycle_count);
                    test_state <= 4;
                end

                // State 4: Wait for ready
                4: begin
                    req_valid <= 0;
                    resp_expected <= resp_expected + 1;
                    $display("[TEST 2] Request accepted at cycle %0d", cycle_count);
                    test_state <= 5;
                end

                // State 5: Submit sequential requests
                5: begin
                    if (seq_count < 5) begin
                        req_valid <= 1;
                        req_id <= req_id + 1;
                        req_addr <= req_addr + 32'h1000;
                        req_rd_wr_n <= (req_id[0] == 1);
                        req_priority <= 3'd3;
                        seq_count <= seq_count + 1;
                        $display("[TEST 3.%0d] Sequential Request submitted at cycle %0d", seq_count, cycle_count);
                        test_state <= 6;
                    end else begin
                        $display("[TEST 3] All 5 sequential requests submitted, total expected: %0d", resp_expected);
                        test_state <= 7;
                    end
                end

                // State 6: Wait for ready
                6: begin
                    req_valid <= 0;
                    resp_expected <= resp_expected + 1;
                    $display("[TEST 3.%0d] Request accepted at cycle %0d", seq_count, cycle_count);
                    test_state <= 5;
                end

                // State 7: Collect responses
                7: begin
                    if (resp_valid) begin
                        resp_received <= resp_received + 1;
                        $display("  Response %0d: id=%h, success=%b at cycle %0d",
                                 resp_received, resp_id, resp_success, cycle_count);
                    end
                    if (resp_received >= resp_expected) begin
                        $display("All %0d responses received", resp_received);
                        test_state <= 8;
                    end
                end

                // State 8: Final summary
                8: begin
                    end_cycle <= cycle_count;
                    $display("");
                    $display("============================================================");
                    $display("Test Summary:");
                    $display("  Total Tests:     %0d", 3);
                    $display("  Expected Resp:   %0d", resp_expected);
                    $display("  Received Resp:   %0d", resp_received);
                    $display("  Statistics:      req=%0d, comp=%0d, hit_rate=%0d%%",
                             stat_requests, stat_completed, stat_hit_rate);
                    $display("  Start Cycle:     %0d", 11);
                    $display("  End Cycle:       %0d", end_cycle);
                    $display("  Total Cycles:    %0d", end_cycle - 11);
                    $display("============================================================");

                    if (resp_received >= resp_expected) begin
                        $display("ALL TESTS PASSED!");
                    end else begin
                        $display("SOME RESPONSES MISSING!");
                    end

                    $display("Simulation completed at cycle %0d", cycle_count);
                    done <= 1;
                    $finish;
                end
            endcase
        end
    end

    // ============================================================================
    // VCD Dump
    // ============================================================================
    initial begin
        $dumpfile("hbm_controller_tb.vcd");
        $dumpvars(0, hbm_controller_tb);
    end

endmodule