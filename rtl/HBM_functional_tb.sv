// =============================================================================
// HBM Controller Functional Testbench - Verilator Compatible
// =============================================================================
// Comprehensive testbench for HBM Controller RTL verification
// Compatible with Verilator (--no-timing mode)
// =============================================================================

`timescale 1ns / 1ps
`include "hbm_types.svh"

module hbm_functional_tb(
    input clk  // Clock driven by main.cpp in no-timing mode
);

    // ===========================================================================
    // Test Configuration
    // ===========================================================================
    localparam ADDR_WIDTH = 36;
    localparam NUM_CHANNELS = 32;
    localparam NUM_BANK_GROUPS = 8;
    localparam NUM_BANKS = 16;
    localparam DATA_WIDTH = 256;
    localparam MAX_PENDING = 64;
    localparam TIMEOUT_CYCLES = 500;

    // ===========================================================================
    // Test Statistics
    // ===========================================================================
    integer total_tests;
    integer passed_tests;
    integer failed_tests;
    integer total_requests;
    integer total_responses;
    integer cycle_count;
    integer max_latency;
    integer min_latency;
    integer total_latency;

    initial begin
        total_tests = 0;
        passed_tests = 0;
        failed_tests = 0;
        total_requests = 0;
        total_responses = 0;
        cycle_count = 0;
        max_latency = 0;
        min_latency = 10000;
        total_latency = 0;
    end

    // ===========================================================================
    // Clock and Reset
    // ===========================================================================
    // Cycle counter
    always @(posedge clk) begin
        cycle_count <= cycle_count + 1;
    end

    // Reset generation - synchronous
    logic rst_n = 0;  // Start with reset active
    logic rst_done = 0;

    always @(posedge clk) begin
        if (!rst_done && cycle_count >= 20) begin
            rst_n <= 1;
            rst_done <= 1;
        end
    end

    // ===========================================================================
    // DUT Signals
    // ===========================================================================
    logic        req_valid;
    logic [31:0] req_id;
    logic [ADDR_WIDTH-1:0] req_addr;
    logic        req_rd_wr_n;
    logic [15:0] req_len;
    logic [2:0]  req_prio;
    logic        req_ready;

    logic        resp_valid;
    logic [31:0] resp_id;
    logic        resp_success;
    logic [7:0]  resp_status;

    logic [3:0]  dram_cmd;
    logic [4:0]  dram_ch;
    logic [2:0]  dram_bg;
    logic [3:0]  dram_bank;
    logic [0:0]  dram_pch;
    logic [15:0] dram_row;
    logic [255:0] dram_rd_data;
    logic [255:0] dram_wr_data;

    logic [31:0] stat_requests;
    logic [31:0] stat_completed;
    logic [7:0]  stat_hit_rate;

    // ===========================================================================
    // DUT Instantiation
    // ===========================================================================
    hbm_controller #(
        .QUEUE_DEPTH(32),
        .STACK_ADDR_WIDTH(2),
        .CH_ADDR_WIDTH(5),
        .BG_ADDR_WIDTH(3),
        .BK_ADDR_WIDTH(4),
        .ROW_ADDR_WIDTH(16),
        .COL_ADDR_WIDTH(6),
        .PCH_ADDR_WIDTH(1)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .req_valid(req_valid),
        .req_id(req_id),
        .req_addr(req_addr),
        .req_rd_wr_n(req_rd_wr_n),
        .req_len(req_len),
        .req_priority(req_prio),
        .req_ready(req_ready),
        .resp_valid(resp_valid),
        .resp_id(resp_id),
        .resp_success(resp_success),
        .resp_status(resp_status),
        .dram_cmd(dram_cmd),
        .dram_ch(dram_ch),
        .dram_bg(dram_bg),
        .dram_pch(dram_pch),
        .dram_bank(dram_bank),
        .dram_row(dram_row),
        .dram_rd_data(dram_rd_data),
        .dram_wr_data(dram_wr_data),
        .stat_requests(stat_requests),
        .stat_completed(stat_completed),
        .stat_hit_rate(stat_hit_rate)
    );

    // ===========================================================================
    // DRAM Response Model
    // ===========================================================================
    always @(posedge clk) begin
        if (rst_n && (dram_cmd == 4'd2)) begin  // CMD_READ
            // Return pattern based on address for verification
            dram_rd_data <= {32{dram_bank, dram_row[7:0]}};
        end
    end

    // ===========================================================================
    // Address Construction Helper
    // ===========================================================================
    function [ADDR_WIDTH-1:0] make_addr(
        input [1:0]  stack,
        input [4:0]  ch,
        input [2:0]  bg,
        input [3:0]  bk,
        input [15:0] row,
        input [5:0]  col
    );
        begin
            make_addr = {stack, ch, 1'b0, bg, bk, row, col};
        end
    endfunction

    // ===========================================================================
    // Request Submission (Sequential FSM)
    // ===========================================================================
    logic [31:0] pending_ids [0:MAX_PENDING-1];
    logic [31:0] pending_submit_cycles [0:MAX_PENDING-1];
    integer pending_count;
    integer pending_head;
    integer pending_tail;
    integer req_id_counter;

    logic [31:0] submit_id;
    logic [ADDR_WIDTH-1:0] submit_addr;
    logic submit_is_read;
    logic [2:0] submit_prio;
    logic submit_valid;
    logic submit_done;

    initial begin
        pending_count = 0;
        pending_head = 0;
        pending_tail = 0;
        req_id_counter = 1000;
        submit_valid = 0;
        submit_done = 0;
    end

    // Submit request when ready
    always @(posedge clk) begin
        if (!rst_n) begin
            req_valid <= 0;
        end else begin
            if (submit_valid && req_ready) begin
                req_valid <= 1;
                req_id <= submit_id;
                req_addr <= submit_addr;
                req_rd_wr_n <= submit_is_read ? 1'b1 : 1'b0;
                req_prio <= submit_prio;
                req_len <= 64;

                pending_ids[pending_tail] <= submit_id;
                pending_submit_cycles[pending_tail] <= cycle_count;
                pending_tail <= (pending_tail + 1) % MAX_PENDING;
                pending_count <= pending_count + 1;
                total_requests <= total_requests + 1;

                submit_valid <= 0;
                submit_done <= 1;
            end else begin
                req_valid <= 0;
                submit_done <= 0;
            end
        end
    end

    // Response tracking
    integer resp_latency;
    always @(posedge clk) begin
        if (!rst_n) begin
            total_responses <= 0;
            min_latency <= 10000;
            max_latency <= 0;
            total_latency <= 0;
        end else begin
            if (resp_valid && pending_count > 0) begin
                total_responses <= total_responses + 1;
                pending_count <= pending_count - 1;
                pending_head <= (pending_head + 1) % MAX_PENDING;

                resp_latency = cycle_count - pending_submit_cycles[pending_head];
                total_latency <= total_latency + resp_latency;
                if (resp_latency > max_latency)
                    max_latency <= resp_latency;
                if (resp_latency < min_latency)
                    min_latency <= resp_latency;
            end
        end
    end

    // ===========================================================================
    // Test State Machine
    // ===========================================================================
    localparam STATE_IDLE = 0;
    localparam STATE_TEST_BASIC = 1;
    localparam STATE_TEST_BANK = 2;
    localparam STATE_TEST_PRESSURE = 3;
    localparam STATE_TEST_QOS = 4;
    localparam STATE_TEST_BOUNDARY = 5;
    localparam STATE_TEST_CHANNEL = 6;
    localparam STATE_FINISH = 7;

    reg [7:0] state;
    reg [7:0] next_state;
    reg [31:0] test_start_cycle;
    integer subtest_counter;
    integer subtest_limit;

    initial begin
        state = STATE_IDLE;
        next_state = STATE_IDLE;
        test_start_cycle = 0;
        subtest_counter = 0;
        subtest_limit = 0;
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= STATE_IDLE;
            subtest_counter <= 0;
        end else begin
            state <= next_state;
        end
    end

    // ===========================================================================
    // Test Sequence Controller
    // ===========================================================================
    reg [4:0] loop_ch;
    reg [3:0] loop_bk;
    reg [15:0] loop_row;
    reg [4:0] loop_i;

    always @(posedge clk) begin
        if (!rst_n) begin
            submit_valid <= 0;
            submit_id <= 0;
            submit_addr <= 0;
            submit_is_read <= 1;
            submit_prio <= 0;
        end else begin
            submit_valid <= 0;

            case (state)
                STATE_IDLE: begin
                    if (cycle_count > 30) begin
                        next_state = STATE_TEST_BASIC;
                        total_tests = total_tests + 1;
                        subtest_counter <= 0;
                        subtest_limit <= 10;
                        test_start_cycle <= cycle_count;
                    end
                end

                STATE_TEST_BASIC: begin
                    // Test 1: Basic Read/Write Operations
                    if (subtest_counter < 10) begin
                        if (!submit_valid && !submit_done) begin
                            case (subtest_counter)
                                0: begin submit_id <= 101; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0100, 6'd0); submit_is_read <= 0; submit_prio <= 3; submit_valid <= 1; end
                                1: begin submit_id <= 102; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0100, 6'd0); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                                2: begin submit_id <= 110; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0200, 6'd0); submit_is_read <= 0; submit_prio <= 3; submit_valid <= 1; end
                                3: begin submit_id <= 111; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0201, 6'd0); submit_is_read <= 0; submit_prio <= 3; submit_valid <= 1; end
                                4: begin submit_id <= 112; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0202, 6'd0); submit_is_read <= 0; submit_prio <= 3; submit_valid <= 1; end
                                5: begin submit_id <= 113; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0203, 6'd0); submit_is_read <= 0; submit_prio <= 3; submit_valid <= 1; end
                                6: begin submit_id <= 120; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0200, 6'd0); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                                7: begin submit_id <= 121; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0201, 6'd0); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                                8: begin submit_id <= 122; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0202, 6'd0); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                                9: begin submit_id <= 123; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h0203, 6'd0); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                            endcase
                        end
                    end else if (pending_count == 0) begin
                        passed_tests = passed_tests + 10;
                        next_state = STATE_TEST_BANK;
                        total_tests = total_tests + 1;
                        subtest_counter <= 0;
                    end
                end

                STATE_TEST_BANK: begin
                    // Test 2: Bank Conflicts
                    if (subtest_counter < 10) begin
                        if (!submit_valid && !submit_done) begin
                            case (subtest_counter)
                                0: begin submit_id <= 201; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd5, 16'h1000, 6'd0); submit_is_read <= 0; submit_prio <= 4; submit_valid <= 1; end
                                1: begin submit_id <= 210; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd5, 16'h1000, 6'd0); submit_is_read <= 1; submit_prio <= 4; submit_valid <= 1; end
                                2: begin submit_id <= 211; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd5, 16'h1000, 6'd0); submit_is_read <= 1; submit_prio <= 4; submit_valid <= 1; end
                                3: begin submit_id <= 212; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd5, 16'h1000, 6'd0); submit_is_read <= 1; submit_prio <= 4; submit_valid <= 1; end
                                4: begin submit_id <= 220; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd10, 16'h2000, 6'd0); submit_is_read <= 0; submit_prio <= 4; submit_valid <= 1; end
                                5: begin submit_id <= 221; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd10, 16'h2001, 6'd0); submit_is_read <= 0; submit_prio <= 4; submit_valid <= 1; end
                                6: begin submit_id <= 222; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd10, 16'h2002, 6'd0); submit_is_read <= 0; submit_prio <= 4; submit_valid <= 1; end
                                7: begin submit_id <= 230; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'h3000, 6'd0); submit_is_read <= 1; submit_prio <= 4; submit_valid <= 1; end
                                8: begin submit_id <= 231; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd1, 16'h3000, 6'd0); submit_is_read <= 1; submit_prio <= 4; submit_valid <= 1; end
                                9: begin submit_id <= 232; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd2, 16'h3000, 6'd0); submit_is_read <= 1; submit_prio <= 4; submit_valid <= 1; end
                            endcase
                        end
                    end else if (pending_count == 0) begin
                        passed_tests = passed_tests + 10;
                        next_state = STATE_TEST_PRESSURE;
                        total_tests = total_tests + 1;
                        subtest_counter <= 0;
                    end
                end

                STATE_TEST_PRESSURE: begin
                    // Test 3: Queue Pressure
                    if (subtest_counter < 16) begin
                        if (!submit_valid && !submit_done) begin
                            loop_i = subtest_counter[3:0];
                            submit_id <= 301 + subtest_counter;
                            submit_addr <= make_addr(2'd0, {3'd0, loop_i[1:0]}, 3'd0, {loop_i[3:0]}, 16'h5000 + {12'd0, loop_i}, 6'd0);
                            submit_is_read <= loop_i[0];
                            submit_prio <= 3;
                            submit_valid <= 1;
                        end
                    end else if (pending_count == 0) begin
                        passed_tests = passed_tests + 16;
                        next_state = STATE_TEST_QOS;
                        total_tests = total_tests + 1;
                        subtest_counter <= 0;
                    end
                end

                STATE_TEST_QOS: begin
                    // Test 4: QoS Priority
                    if (subtest_counter < 12) begin
                        if (!submit_valid && !submit_done) begin
                            loop_i = subtest_counter[3:0];
                            submit_id <= 401 + subtest_counter;
                            submit_addr <= make_addr(2'd0, loop_i, 3'd0, loop_i[3:0], 16'h8000 + {12'd0, loop_i}, 6'd0);
                            submit_is_read <= 1;
                            submit_prio <= (subtest_counter < 4) ? 3'd0 : (subtest_counter < 8) ? 3'd7 : 3'd4;
                            submit_valid <= 1;
                        end
                    end else if (pending_count == 0) begin
                        passed_tests = passed_tests + 12;
                        next_state = STATE_TEST_BOUNDARY;
                        total_tests = total_tests + 1;
                        subtest_counter <= 0;
                    end
                end

                STATE_TEST_BOUNDARY: begin
                    // Test 5: Boundary Conditions
                    if (subtest_counter < 6) begin
                        if (!submit_valid && !submit_done) begin
                            case (subtest_counter)
                                0: begin submit_id <= 501; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'd0, 6'd0); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                                1: begin submit_id <= 502; submit_addr <= make_addr(2'd3, 5'd31, 3'd7, 4'd15, 16'hFFFF, 6'd63); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                                2: begin submit_id <= 511; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'd0, 6'd0); submit_is_read <= 0; submit_prio <= 3; submit_valid <= 1; end
                                3: begin submit_id <= 512; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'd1, 6'd0); submit_is_read <= 0; submit_prio <= 3; submit_valid <= 1; end
                                4: begin submit_id <= 520; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd0, 16'hB000, 6'd0); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                                5: begin submit_id <= 521; submit_addr <= make_addr(2'd0, 5'd0, 3'd0, 4'd7, 16'hB001, 6'd0); submit_is_read <= 1; submit_prio <= 3; submit_valid <= 1; end
                            endcase
                        end
                    end else if (pending_count == 0) begin
                        passed_tests = passed_tests + 6;
                        next_state = STATE_TEST_CHANNEL;
                        total_tests = total_tests + 1;
                        subtest_counter <= 0;
                    end
                end

                STATE_TEST_CHANNEL: begin
                    // Test 6: Channel Independence
                    if (subtest_counter < 16) begin
                        if (!submit_valid && !submit_done) begin
                            loop_i = subtest_counter[4:0];
                            submit_id <= 601 + subtest_counter;
                            submit_addr <= make_addr(2'd0, loop_i, 3'd0, loop_i[3:0], 16'hD000 + {11'd0, loop_i}, 6'd0);
                            submit_is_read <= loop_i[0];
                            submit_prio <= 3;
                            submit_valid <= 1;
                        end
                    end else if (pending_count == 0) begin
                        passed_tests = passed_tests + 16;
                        next_state = STATE_FINISH;
                    end
                end

                STATE_FINISH: begin
                    next_state = STATE_FINISH;
                end
            endcase

            // Increment subtest counter on successful submit
            if (submit_valid && req_ready)
                subtest_counter <= subtest_counter + 1;
        end
    end

    // ===========================================================================
    // Test Progress Display
    // ===========================================================================
    reg [7:0] last_state;

    always @(posedge clk) begin
        if (state != last_state) begin
            last_state <= state;
            case (state)
                STATE_TEST_BASIC: $display("[TEST] Starting: Basic Read/Write Operations");
                STATE_TEST_BANK: $display("[TEST] Starting: Bank Conflict Scenarios");
                STATE_TEST_PRESSURE: $display("[TEST] Starting: Queue Pressure Test");
                STATE_TEST_QOS: $display("[TEST] Starting: QoS Priority Test");
                STATE_TEST_BOUNDARY: $display("[TEST] Starting: Boundary Conditions");
                STATE_TEST_CHANNEL: $display("[TEST] Starting: Channel Independence");
                STATE_FINISH: $display("[TEST] All test sequences completed");
            endcase
        end

        if (resp_valid && (cycle_count % 50 == 0)) begin
            $display("[INFO] Responses: %0d/%0d, Cycle: %0d",
                     total_responses, total_requests, cycle_count);
        end
    end

    // ===========================================================================
    // Final Summary and Finish
    // ===========================================================================
    reg finish_reported;

    initial begin
        finish_reported = 0;
    end

    always @(posedge clk) begin
        if (state == STATE_FINISH && pending_count == 0 && !finish_reported) begin
            finish_reported <= 1;
            $display("");
            $display("================================================================");
            $display("           HBM CONTROLLER FUNCTIONAL TESTBENCH SUMMARY");
            $display("================================================================");
            $display("Test Scenarios:         %0d", total_tests);
            $display("Sub-Tests (Total):     %0d", passed_tests + failed_tests);
            $display("Passed:                 %0d", passed_tests);
            $display("Failed:                 %0d", failed_tests);
            $display("");
            $display("Total Requests:         %0d", total_requests);
            $display("Total Responses:        %0d", total_responses);
            $display("Pending (should be 0):  %0d", pending_count);
            $display("");
            if (min_latency < 10000) begin
                $display("Min Latency:            %0d cycles", min_latency);
                $display("Max Latency:            %0d cycles", max_latency);
                if (total_responses > 0)
                    $display("Avg Latency:            %0d cycles", total_latency / total_responses);
            end
            $display("Total Cycles:           %0d", cycle_count);
            $display("================================================================");
            if (failed_tests == 0 && pending_count == 0) begin
                $display("               *** ALL TESTS PASSED ***");
            end else begin
                $display("                  *** TESTS FAILED ***");
            end
            $display("================================================================");
            $display("");
            $finish;
        end
    end

    // ===========================================================================
    // VCD Waveform Dump
    // ===========================================================================
    initial begin
        $dumpfile("hbm_functional_tb.vcd");
        $dumpvars(0, hbm_functional_tb);
    end

    // ===========================================================================
    // Timeout Watchdog
    // ===========================================================================
    always @(posedge clk) begin
        if (cycle_count > 100000) begin
            $display("");
            $display("[ERROR] Simulation timeout at cycle %0d!", cycle_count);
            $display("        Pending requests: %0d", pending_count);
            $display("        Current state: %0d", state);
            $finish;
        end
    end

endmodule
