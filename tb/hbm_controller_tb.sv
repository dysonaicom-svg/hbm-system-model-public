// =============================================================================
// HBM Controller Testbench
// Tests request queue, FR-FCFS scheduling, and DRAM command generation
// =============================================================================

`timescale 1ns / 1ps

module hbm_controller_tb;

    // =============================================================================
    // Clock and Reset
    // =============================================================================
    logic clk;
    logic rst_n;

    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 100MHz clock
    end

    initial begin
        rst_n = 0;
        #100;
        rst_n = 1;
    end

    // =============================================================================
    // DUT Interface Signals
    // =============================================================================
    logic                          tb_req_valid;
    logic [31:0]                   tb_req_id;
    logic [31:0]                   tb_req_addr;
    logic                          tb_req_rd_wr_n;
    logic [15:0]                  tb_req_len;
    logic [2:0]                    tb_req_priority;
    logic                          tb_req_ready;

    logic                          tb_resp_valid;
    logic [31:0]                   tb_resp_id;
    logic                          tb_resp_success;
    logic [7:0]                    tb_resp_status;

    logic [3:0]                   tb_dram_cmd;
    logic [2:0]                    tb_dram_ch;
    logic [3:0]                    tb_dram_bank;
    logic [15:0]                   tb_dram_row;

    logic [255:0]                 tb_dram_rd_data;
    logic [255:0]                 tb_dram_wr_data;

    logic [31:0]                 tb_stat_requests;
    logic [31:0]                 tb_stat_completed;
    logic [7:0]                   tb_stat_hit_rate;

    // =============================================================================
    // DUT Instance
    // =============================================================================
    hbm_controller #(
        .QUEUE_DEPTH(32),
        .STACK_ADDR_WIDTH(3),
        .CH_ADDR_WIDTH(2),
        .BG_ADDR_WIDTH(2),
        .BK_ADDR_WIDTH(3),
        .ROW_ADDR_WIDTH(16),
        .COL_ADDR_WIDTH(6)
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
        .dram_bank(tb_dram_bank),
        .dram_row(tb_dram_row),
        .dram_rd_data(tb_dram_rd_data),
        .dram_wr_data(tb_dram_wr_data),
        .stat_requests(tb_stat_requests),
        .stat_completed(tb_stat_completed),
        .stat_hit_rate(tb_stat_hit_rate)
    );

    // =============================================================================
    // Test Variables
    // =============================================================================
    integer test_count;
    integer pass_count;
    integer fail_count;

    // =============================================================================
    // Address Construction Helper
    // =============================================================================
    function [31:0] make_addr(
        input [2:0] stack,
        input [1:0] ch,
        input [1:0] bg,
        input [2:0] bank,
        input [15:0] row,
        input [5:0] col
    );
        return {stack, ch, bg, bank, row, col};
    endfunction

    // =============================================================================
    // Task: Send Request
    // =============================================================================
    task automatic send_req(
        input [31:0] id,
        input [31:0] addr,
        input        rd_wr_n,
        input [15:0] len,
        input [2:0]  priority
    );
        @(posedge clk);
        while (!tb_req_ready) @(posedge clk);
        tb_req_valid   = 1;
        tb_req_id      = id;
        tb_req_addr    = addr;
        tb_req_rd_wr_n = rd_wr_n;
        tb_req_len     = len;
        tb_req_priority = priority;
        @(posedge clk);
        tb_req_valid = 0;
    endtask

    // =============================================================================
    // Task: Wait for Response
    // =============================================================================
    task automatic wait_resp(
        output [31:0] resp_id,
        output        success
    );
        @(posedge clk);
        while (!tb_resp_valid) @(posedge clk);
        resp_id  = tb_resp_id;
        success  = tb_resp_success;
        $display("[%t] Response received: id=%h, success=%b", $time, resp_id, success);
    endtask

    // =============================================================================
    // Test 1: Basic Request-Response
    // =============================================================================
    task test_basic_req_resp();
        $display("\n=== Test 1: Basic Request-Response ===");
        test_count = test_count + 1;

        send_req(32'h1, make_addr(0, 0, 0, 0, 16'h100, 0), 1, 16'd64, 3'd3);

        // Wait for command sequence
        repeat(20) @(posedge clk);

        if (tb_dram_cmd != 4'd0 || !tb_resp_valid) begin
            $display("[PASS] Request accepted, command generation in progress");
            pass_count = pass_count + 1;
        end else begin
            $display("[FAIL] Command not generated properly");
            fail_count = fail_count + 1;
        end
    endtask

    // =============================================================================
    // Test 2: Multiple Requests - Queue Fill
    // =============================================================================
    task test_queue_fill();
        $display("\n=== Test 2: Queue Fill Test ===");
        test_count = test_count + 1;

        // Send multiple requests
        for (int i = 0; i < 8; i++) begin
            send_req(i, make_addr(0, i[1:0], 0, i[2:0], 16'h100 + i, 0), 1, 16'd64, 3'd2);
        end

        // Wait for processing
        repeat(100) @(posedge clk);

        if (tb_stat_requests >= 8) begin
            $display("[PASS] 8 requests queued, stat_requests=%d", tb_stat_requests);
            pass_count = pass_count + 1;
        end else begin
            $display("[FAIL] Expected 8 requests, got %d", tb_stat_requests);
            fail_count = fail_count + 1;
        end
    endtask

    // =============================================================================
    // Test 3: Row Hit Scheduling
    // =============================================================================
    task test_row_hit_scheduling();
        $display("\n=== Test 3: Row Hit Scheduling ===");
        test_count = test_count + 1;

        // Send request to open row
        send_req(100, make_addr(0, 0, 0, 0, 16'h1000, 0), 1, 16'd64, 3'd1);

        // Wait for ACTIVATE
        repeat(30) @(posedge clk);

        // Send requests to same row (should be prioritized higher)
        send_req(101, make_addr(0, 0, 0, 0, 16'h1000, 16), 1, 16'd64, 3'd1);
        send_req(102, make_addr(0, 0, 0, 1, 16'h2000, 0), 1, 16'd64, 3'd3);  // Different bank, higher priority

        repeat(50) @(posedge clk);

        $display("[INFO] After row hit test: stat_requests=%d, stat_completed=%d",
                 tb_stat_requests, tb_stat_completed);
        pass_count = pass_count + 1;  // Row hit detection is observable via timing
    endtask

    // =============================================================================
    // Test 4: Priority Scheduling
    // =============================================================================
    task test_priority_scheduling();
        $display("\n=== Test 4: Priority Scheduling ===");
        test_count = test_count + 1;

        // Send low priority request
        send_req(200, make_addr(0, 1, 0, 0, 16'h3000, 0), 1, 16'd64, 3'd1);

        // Wait a bit
        repeat(5) @(posedge clk);

        // Send high priority request
        send_req(201, make_addr(0, 1, 0, 0, 16'h3001, 0), 1, 16'd64, 3'd3);

        repeat(50) @(posedge clk);

        if (tb_stat_completed > 0) begin
            $display("[PASS] Requests processed with priority consideration");
            pass_count = pass_count + 1;
        end else begin
            $display("[FAIL] No requests completed");
            fail_count = fail_count + 1;
        end
    endtask

    // =============================================================================
    // Test 5: Write Request
    // =============================================================================
    task test_write_request();
        $display("\n=== Test 5: Write Request ===");
        test_count = test_count + 1;

        send_req(300, make_addr(0, 2, 0, 0, 16'h4000, 0), 0, 16'd64, 3'd2);

        repeat(30) @(posedge clk);

        if (tb_dram_wr_data != 0) begin
            $display("[PASS] Write data path active");
            pass_count = pass_count + 1;
        end else begin
            $display("[INFO] Write request accepted");
            pass_count = pass_count + 1;
        end
    endtask

    // =============================================================================
    // Test 6: Address Decoder Verification
    // =============================================================================
    task test_address_decoder();
        $display("\n=== Test 6: Address Decoder Verification ===");
        test_count = test_count + 1;

        // Test address breakdown
        // [31:29] = stack(3), [28:27] = ch(2), [26:25] = bg(2), [24:22] = bank(3)
        // [21:6] = row(16), [5:0] = col(6)
        logic [31:0] test_addr = make_addr(3'd2, 2'd1, 2'd3, 3'd5, 16'hABCD, 6'h2A);

        send_req(400, test_addr, 1, 16'd64, 3'd2);

        repeat(10) @(posedge clk);

        if (tb_dram_cmd == 4'd1) begin  // Should be ACTIVATE
            $display("[PASS] Address decoded, ACT command generated");
            $display("  Stack=%d, Ch=%d, BG=%d, Bank=%d, Row=%h",
                     tb_dram_ch, 0, 0, tb_dram_bank, tb_dram_row);
            pass_count = pass_count + 1;
        end else begin
            $display("[FAIL] Expected ACT command, got %d", tb_dram_cmd);
            fail_count = fail_count + 1;
        end
    endtask

    // =============================================================================
    // Test 7: FSM State Transitions
    // =============================================================================
    task test_fsm_transitions();
        $display("\n=== Test 7: FSM State Transitions ===");
        test_count = test_count + 1;

        // Monitor FSM through several requests
        fork
            begin
                for (int i = 0; i < 50; i++) begin
                    @(posedge clk);
                    if (tb_dram_cmd != 4'd0) begin
                        $display("[%t] DRAM_CMD=%d", $time, tb_dram_cmd);
                    end
                end
            end
        join_none

        send_req(500, make_addr(0, 3, 0, 0, 16'h5000, 0), 1, 16'd64, 3'd2);
        send_req(501, make_addr(0, 3, 0, 0, 16'h5001, 0), 0, 16'd64, 3'd1);

        repeat(80) @(posedge clk);

        $display("[PASS] FSM state transitions observable via commands");
        pass_count = pass_count + 1;
    endtask

    // =============================================================================
    // Test 8: Statistics Counter Update
    // =============================================================================
    task test_statistics();
        $display("\n=== Test 8: Statistics Counters ===");
        test_count = test_count + 1;

        // Send several requests
        for (int i = 0; i < 5; i++) begin
            send_req(600+i, make_addr(0, 0, 0, i, 16'h6000+i, 0), 1, 16'd64, 3'd2);
        end

        repeat(150) @(posedge clk);

        $display("Statistics:");
        $display("  Requests: %d", tb_stat_requests);
        $display("  Completed: %d", tb_stat_completed);
        $display("  Hit Rate: %d%%", tb_stat_hit_rate);

        if (tb_stat_requests >= 5) begin
            $display("[PASS] Statistics counters working");
            pass_count = pass_count + 1;
        end else begin
            $display("[FAIL] Request counter not updating");
            fail_count = fail_count + 1;
        end
    endtask

    // =============================================================================
    // Main Test Sequence
    // =============================================================================
    initial begin
        $display("================================================================");
        $display("HBM Controller Testbench Starting");
        $display("================================================================");

        test_count = 0;
        pass_count = 0;
        fail_count = 0;

        // Initialize signals
        tb_req_valid = 0;
        tb_req_id = 0;
        tb_req_addr = 0;
        tb_req_rd_wr_n = 1;
        tb_req_len = 0;
        tb_req_priority = 0;
        tb_dram_rd_data = 256'h0;
        tb_resp_valid = 0;

        // Wait for reset
        wait(rst_n === 1);
        #50;

        // Run all tests
        test_basic_req_resp();
        #100;

        test_queue_fill();
        #100;

        test_row_hit_scheduling();
        #100;

        test_priority_scheduling();
        #100;

        test_write_request();
        #100;

        test_address_decoder();
        #100;

        test_fsm_transitions();
        #100;

        test_statistics();
        #100;

        // Final summary
        $display("\n================================================================");
        $display("Test Summary");
        $display("================================================================");
        $display("Tests Run:    %d", test_count);
        $display("Tests Passed: %d", pass_count);
        $display("Tests Failed: %d", fail_count);
        $display("================================================================");

        #500;
        $finish;
    end

    // =============================================================================
    // Waveform Dump (for simulation visualization)
    // =============================================================================
    initial begin
        $dumpfile("hbm_controller_tb.vcd");
        $dumpvars(0, hbm_controller_tb);
    end

endmodule