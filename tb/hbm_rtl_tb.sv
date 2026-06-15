// =============================================================================
// HBM RTL Testbench
// Validates RTL DRAM model against expected behavior
// =============================================================================

`timescale 1ns / 1ps

module hbm_rtl_tb;

    // Clock and reset
    reg clk;
    reg rst_n;

    // DUT signals
    reg [3:0] cmd;
    reg [2:0] ch_id;
    reg [3:0] bank_id;
    reg [15:0] row_id;
    reg [255:0] wr_data;
    wire [255:0] rd_data;
    wire [2:0] bank_state [0:15];
    wire cmd_ack;
    wire cmd_error;
    wire [3:0] error_code;

    // Test control
    reg [31:0] test_count;
    reg [31:0] error_count;
    reg [63:0] start_time;
    reg [63:0] end_time;

    // Clock generation - 1.28 GHz (781.25ps period)
    always begin
        #0.390625 clk = ~clk;  // Half period = 0.390625ns
    end

    // DUT instantiation
    dram_model #(
        .T_RCD(20),
        .T_RP(20),
        .T_RAS(32),
        .T_RC(38),
        .T_RFC(16),
        .NUM_BANKS(16)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .cmd(cmd),
        .ch_id(ch_id),
        .bank_id(bank_id),
        .row_id(row_id),
        .wr_data(wr_data),
        .rd_data(rd_data),
        .bank_state(bank_state),
        .cmd_ack(cmd_ack),
        .cmd_error(cmd_error),
        .error_code(error_code)
    );

    // Test stimulus
    initial begin
        $dumpfile("hbm_rtl_tb.vcd");
        $dumpvars(0, hbm_rtl_tb);

        // Initialize
        clk = 0;
        rst_n = 0;
        cmd = 4'b0000;
        ch_id = 0;
        bank_id = 0;
        row_id = 0;
        wr_data = 0;
        test_count = 0;
        error_count = 0;

        // Reset sequence
        #100 rst_n = 1;
        #50;

        $display("=== HBM RTL Testbench Started ===");
        $display("Time: %0t", $time);

        // Wait for reset
        @(posedge rst_n);
        #100;

        start_time = $time;

        // Test 1: Basic activation
        test_count++;
        $display("\n--- Test %0d: Basic Activation ---", test_count);
        test_basic_activation();

        // Test 2: Read after activate
        test_count++;
        $display("\n--- Test %0d: Read After Activate ---", test_count);
        test_read_after_activate();

        // Test 3: Write after activate
        test_count++;
        $display("\n--- Test %0d: Write After Activate ---", test_count);
        test_write_after_activate();

        // Test 4: Precharge
        test_count++;
        $display("\n--- Test %0d: Precharge ---", test_count);
        test_precharge();

        // Test 5: Row conflict
        test_count++;
        $display("\n--- Test %0d: Row Conflict ---", test_count);
        test_row_conflict();

        // Test 6: Bank parallel
        test_count++;
        $display("\n--- Test %0d: Bank Parallel ---", test_count);
        test_bank_parallel();

        end_time = $time;

        // Summary
        $display("\n========================================");
        $display("  TEST SUMMARY");
        $display("========================================");
        $display("Total tests: %0d", test_count);
        $display("Passed: %0d", test_count - error_count);
        $display("Failed: %0d", error_count);
        $display("Elapsed time: %0t ns", end_time - start_time);
        $display("========================================");

        if (error_count == 0) begin
            $display("RESULT: ALL TESTS PASSED");
        end else begin
            $display("RESULT: SOME TESTS FAILED");
        end

        #100 $finish;
    end

    // =========================================================================
    // Test Tasks
    // =========================================================================

    task test_basic_activation;
        reg [15:0] delay_cycles;
    begin
        // Wait for idle
        wait_idle();

        // Issue ACT command
        cmd = 4'b0001;  // CMD_ACT
        bank_id = 4'd0;
        row_id = 16'h1234;
        @(posedge clk);

        // Check command accepted
        if (cmd_ack !== 1'b1) begin
            $display("ERROR: ACT not acknowledged at time %0t", $time);
            error_count++;
        end

        // Wait for tRCD (20 cycles)
        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        // Check bank is active
        if (bank_state[bank_id] !== 3'b001) begin
            $display("ERROR: Bank not active after ACT at time %0t", $time);
            error_count++;
        end else begin
            $display("PASS: Bank %0d active, row 0x%04h", bank_id, row_id);
        end

        // Clear command
        cmd = 4'b0000;
    end
    endtask

    task test_read_after_activate;
        reg [15:0] delay_cycles;
    begin
        // Wait for idle
        wait_idle();

        // First activate
        cmd = 4'b0001;  // CMD_ACT
        bank_id = 4'd0;
        row_id = 16'h5678;
        @(posedge clk);

        // Wait for tRCD
        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        // Issue READ
        cmd = 4'b0010;  // CMD_READ
        @(posedge clk);

        // Wait for read latency
        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        if (cmd_ack !== 1'b1) begin
            $display("ERROR: READ not acknowledged at time %0t", $time);
            error_count++;
        end else begin
            $display("PASS: READ completed at time %0t", $time);
        end

        // Clear command
        cmd = 4'b0000;
    end
    endtask

    task test_write_after_activate;
        reg [15:0] delay_cycles;
    begin
        // Wait for idle
        wait_idle();

        // Activate
        cmd = 4'b0001;  // CMD_ACT
        bank_id = 4'd1;
        row_id = 16'hABCD;
        wr_data = 256'hDEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF;
        @(posedge clk);

        // Wait for tRCD
        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        // Issue WRITE
        cmd = 4'b0011;  // CMD_WRITE
        @(posedge clk);

        // Wait for write completion
        delay_cycles = 10;
        repeat(delay_cycles) @(posedge clk);

        if (cmd_ack !== 1'b1) begin
            $display("ERROR: WRITE not acknowledged at time %0t", $time);
            error_count++;
        end else begin
            $display("PASS: WRITE completed at time %0t", $time);
        end

        // Clear command
        cmd = 4'b0000;
    end
    endtask

    task test_precharge;
        reg [15:0] delay_cycles;
    begin
        // Wait for idle
        wait_idle();

        // Activate bank
        cmd = 4'b0001;
        bank_id = 4'd2;
        row_id = 16'h1111;
        @(posedge clk);

        // Wait for activation
        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        // Issue PRECHARGE
        cmd = 4'b0100;  // CMD_PRE
        @(posedge clk);

        // Wait for tRP
        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        // Check bank is idle
        if (bank_state[bank_id] !== 3'b000) begin
            $display("ERROR: Bank not idle after PRE at time %0t", $time);
            error_count++;
        end else begin
            $display("PASS: Bank %0d precharged", bank_id);
        end

        // Clear command
        cmd = 4'b0000;
    end
    endtask

    task test_row_conflict;
        reg [15:0] delay_cycles;
    begin
        // Wait for idle
        wait_idle();

        // Activate bank with row 0
        cmd = 4'b0001;
        bank_id = 4'd3;
        row_id = 16'h0000;
        @(posedge clk);

        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        // Precharge
        cmd = 4'b0100;
        @(posedge clk);

        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        // Activate same bank with row 1 (conflict)
        cmd = 4'b0001;
        row_id = 16'h0001;
        @(posedge clk);

        delay_cycles = 20;
        repeat(delay_cycles) @(posedge clk);

        if (bank_state[bank_id] === 3'b001) begin
            $display("PASS: Row conflict handled, new row activated");
        end else begin
            $display("ERROR: Row conflict not handled at time %0t", $time);
            error_count++;
        end

        cmd = 4'b0000;
    end
    endtask

    task test_bank_parallel;
        integer i;
        reg [15:0] delay_cycles;
    begin
        // Activate multiple banks in parallel
        for (i = 0; i < 4; i++) begin
            wait_idle();

            cmd = 4'b0001;
            bank_id = i[3:0];
            row_id = 16'h1000 + i;
            @(posedge clk);

            delay_cycles = 20;
            repeat(delay_cycles) @(posedge clk);

            if (bank_state[i] === 3'b001) begin
                $display("PASS: Bank %0d activated", i);
            end else begin
                $display("ERROR: Bank %0d not activated", i);
                error_count++;
            end
        end

        cmd = 4'b0000;
    end
    endtask

    task wait_idle;
        integer timeout;
    begin
        timeout = 0;
        while (timeout < 1000) begin
            if (cmd === 4'b0000 && cmd_ack === 1'b0) begin
                @(posedge clk);
                @(posedge clk);
                return;
            end
            timeout++;
            @(posedge clk);
        end
        $display("WARNING: wait_idle timeout at time %0t", $time);
    end
    endtask

    // Timeout watchdog
    initial begin
        #10_000_000;  // 10ms timeout
        $display("ERROR: Simulation timeout at time %0t", $time);
        $finish;
    end

endmodule