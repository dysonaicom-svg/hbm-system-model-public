// ------------------------------------------------------------
// hbm_tb.sv - HBM Testbench Top Module
// Minimal RTL testbench for Verilator without timing constructs
// ------------------------------------------------------------
`timescale 1ns / 1ps

module hbm_tb;

// =============================================================
// Clock and Reset Generation
// =============================================================
logic clk;
logic rst_n;

// Clock driven externally via eval()
// Reset pulse on start
initial begin
    rst_n = 0;
end

// Reset released after initial evaluation
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        rst_n <= 1;  // Release reset after first clock edge
    end
end

// =============================================================
// RTL Controller Signals
// =============================================================
logic [3:0]   wrapper_dram_cmd;
logic [7:0]   wrapper_dram_ch;
logic [2:0]   wrapper_dram_bank;
logic [15:0]  wrapper_dram_row;
logic [255:0] wrapper_dram_rd_data;
logic [255:0] wrapper_dram_wr_data;

logic [31:0]  wrapper_stat_requests;
logic [31:0]  wrapper_stat_completed;
logic [7:0]   wrapper_stat_hit_rate;

logic         wrapper_dram_rd_data_valid;
logic [255:0] wrapper_dram_rd_data_q;

logic         req_valid;
logic [31:0]  req_id;
logic [41:0] req_addr;  // STACK(8) + CH(5) + BG(3) + BK(4) + ROW(16) + COL(6) = 42 bits
logic         req_rd_wr_n;
logic [15:0]  req_len;
logic [2:0]   req_priority;
logic         req_ready;

logic         resp_valid;
logic [31:0]  resp_id;
logic         resp_success;
logic [7:0]   resp_status;

// =============================================================
// Reference Model Command Mapping
// =============================================================
logic [2:0]  ref_cmd_type;
logic [5:0]  ref_bank_idx;
logic [15:0] ref_row_addr;
logic [9:0]  ref_col_addr;

logic [7:0]  ref_tRCD = 20;
logic [7:0]  ref_tRP = 20;
logic [7:0]  ref_tRAS = 40;
logic [15:0] ref_tRC = 60;

logic [31:0] ref_act_count;
logic [31:0] ref_read_count;
logic [31:0] ref_write_count;
logic [31:0] ref_row_hits;
logic [31:0] ref_row_misses;
logic [31:0] ref_avg_latency;

// =============================================================
// Timing Checker Signals
// =============================================================
logic        timing_violation;
logic [7:0]  timing_violation_type;
logic [15:0] timing_violation_bank;
logic [15:0] timing_violation_cycle;
logic [31:0] timing_total_violations;

// =============================================================
// Bandwidth Calculator Signals
// =============================================================
logic [31:0] bw_bandwidth_gbps;
logic [31:0] bw_efficiency_pct;
logic [31:0] bw_peak_bw;
logic [31:0] bw_avg_bw;

// =============================================================
// DRAM Reference Model Instance
// =============================================================
dram_ref_model #(
    .NUM_BANKS(16),
    .NUM_BANK_GROUPS(4)
) u_dram_ref (
    .clk          (clk),
    .rst_n        (rst_n),
    .cmd_valid    (wrapper_dram_cmd != 0),
    .cmd_type     (ref_cmd_type),
    .bank_idx     (ref_bank_idx),
    .row_addr     (ref_row_addr),
    .col_addr     (ref_col_addr),
    .tRCD         (ref_tRCD),
    .tRP          (ref_tRP),
    .tRAS         (ref_tRAS),
    .tRC          (ref_tRC),
    .act_count    (ref_act_count),
    .read_count   (ref_read_count),
    .write_count  (ref_write_count),
    .row_hits     (ref_row_hits),
    .row_misses   (ref_row_misses),
    .avg_latency  (ref_avg_latency)
);

// =============================================================
// Timing Checker Instance
// =============================================================
timing_checker #(
    .NUM_BANKS(16)
) u_timing_checker (
    .clk              (clk),
    .rst_n            (rst_n),
    .enable           (1'b1),
    .cmd_valid        (wrapper_dram_cmd != 0),
    .cmd_type         (ref_cmd_type),
    .bank_idx         (ref_bank_idx),
    .row_addr         (ref_row_addr),
    .col_addr         (ref_col_addr),
    .tRCD             (ref_tRCD),
    .tRP              (ref_tRP),
    .tRAS             (ref_tRAS),
    .tRC              ({{8{1'b0}}, ref_tRC}),
    .tRRD             (8'd8),
    .tCCD             (8'd4),
    .tWTR             (8'd8),
    .tRTW             (8'd8),
    .tRTP             (8'd8),
    .tREFI            (8'd156),
    .tRFC             (8'd64),
    .timing_violation  (timing_violation),
    .violation_type   (timing_violation_type),
    .violation_bank   (timing_violation_bank),
    .violation_cycle  (timing_violation_cycle),
    .total_violations (timing_total_violations)
);

// =============================================================
// Bandwidth Calculator Instance
// =============================================================
bandwidth_calc #(
    .WINDOW_SIZE(1000),
    .REAL_CLK_FREQ(1.28e9),
    .BUS_WIDTH(1024)
) u_bandwidth_calc (
    .clk              (clk),
    .rst_n            (rst_n),
    .enable           (1'b1),
    .trans_valid      (wrapper_dram_cmd != 0),
    .trans_type       ({1'b0, wrapper_dram_cmd}),
    .trans_bytes      (64),
    .bandwidth_gbps   (bw_bandwidth_gbps),
    .efficiency_pct   (bw_efficiency_pct),
    .peak_bandwidth_gbps (bw_peak_bw),
    .avg_bandwidth_gbps  (bw_avg_bw),
    .window_count     (),
    .total_transactions ()
);

// =============================================================
// Simple DRAM Response Model
// =============================================================
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        wrapper_dram_rd_data_valid <= 1'b0;
        wrapper_dram_rd_data_q <= '0;
    end else begin
        if (wrapper_dram_cmd == 4'd2) begin
            wrapper_dram_rd_data_q <= {256{$random}};
            wrapper_dram_rd_data_valid <= 1'b1;
        end else if (wrapper_dram_cmd == 4'd3) begin
            wrapper_dram_rd_data_valid <= 1'b0;
        end else begin
            wrapper_dram_rd_data_valid <= 1'b0;
        end
    end
end

assign wrapper_dram_rd_data = wrapper_dram_rd_data_q;

// =============================================================
// Controller Instantiation (Reference Model Stub)
// =============================================================
hbm_controller #(
    .QUEUE_DEPTH       (32),
    .STACK_ADDR_WIDTH (8),
    .CH_ADDR_WIDTH    (5),
    .BG_ADDR_WIDTH    (3),
    .BK_ADDR_WIDTH    (4),
    .ROW_ADDR_WIDTH   (16),
    .COL_ADDR_WIDTH   (6)
) u_hbm_controller (
    .clk            (clk),
    .rst_n          (rst_n),

    .req_valid      (req_valid),
    .req_id         (req_id),
    .req_addr       (req_addr),
    .req_rd_wr_n    (req_rd_wr_n),
    .req_len        (req_len),
    .req_priority   (req_priority),
    .req_ready      (req_ready),

    .resp_valid     (resp_valid),
    .resp_id        (resp_id),
    .resp_success   (resp_success),
    .resp_status    (resp_status),

    .dram_cmd       (wrapper_dram_cmd),
    .dram_ch        (wrapper_dram_ch),
    .dram_bank      (wrapper_dram_bank),
    .dram_row       (wrapper_dram_row),
    .dram_rd_data   (wrapper_dram_rd_data),
    .dram_wr_data   (wrapper_dram_wr_data),

    .stat_requests  (wrapper_stat_requests),
    .stat_completed (wrapper_stat_completed),
    .stat_hit_rate  (wrapper_stat_hit_rate)
);

// =============================================================
// Reference Model Command Mapping
// =============================================================
always_comb begin
    ref_cmd_type = 3'b000;
    ref_bank_idx = '0;
    ref_row_addr = '0;
    ref_col_addr = '0;

    case (wrapper_dram_cmd)
        4'd1: begin
            ref_cmd_type = 3'b000;
            ref_bank_idx = wrapper_dram_bank[2:0];
            ref_row_addr = wrapper_dram_row;
        end
        4'd2: begin
            ref_cmd_type = 3'b001;
            ref_bank_idx = wrapper_dram_bank[2:0];
            ref_row_addr = wrapper_dram_row;
        end
        4'd3: begin
            ref_cmd_type = 3'b010;
            ref_bank_idx = wrapper_dram_bank[2:0];
            ref_row_addr = wrapper_dram_row;
        end
        4'd4: begin
            ref_cmd_type = 3'b011;
            ref_bank_idx = wrapper_dram_bank[2:0];
        end
    endcase
end

// =============================================================
// Testbench Stimulus (combinational FSM) - Enhanced
// =============================================================
logic [31:0] test_count = 0;
logic [31:0] cycle_count = 0;
logic [3:0] state;
logic [31:0] test_num = 0;
logic [31:0] req_delay = 0;

// Bank/row counters for test scenarios
logic [7:0] bank_counter = 0;
logic [15:0] row_counter = 0;
logic [4:0] ch_counter = 0;

// State machine states
localparam IDLE = 4'd0;
localparam TEST_SINGLE_READ = 4'd1;
localparam TEST_SINGLE_WRITE = 4'd2;
localparam TEST_BANK_CONFLICT = 4'd3;
localparam TEST_MULTI_CHANNEL = 4'd4;
localparam TEST_REFRESH = 4'd5;
localparam TEST_QOS = 4'd6;
localparam TEST_RANDOM = 4'd7;
localparam TEST_BANK_STRESS = 4'd8;
localparam DONE = 4'd15;

// Test configuration
localparam [31:0] TEST_BANK_CONFLICT_CYCLES = 500;
localparam [31:0] TEST_MULTI_CHANNEL_CYCLES = 1000;
localparam [31:0] TEST_REFRESH_CYCLES = 1500;
localparam [31:0] TEST_QOS_CYCLES = 2000;
localparam [31:0] TEST_RANDOM_CYCLES = 2500;
localparam [31:0] TEST_BANK_STRESS_CYCLES = 3000;

// Statistics
logic [31:0] total_reads = 0;
logic [31:0] total_writes = 0;
logic [31:0] bank_conflicts = 0;
logic [31:0] row_hits = 0;
logic [31:0] row_misses = 0;

// FSM
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        req_valid <= 0;
        req_id <= 0;
        req_addr <= 0;
        req_rd_wr_n <= 0;
        req_len <= 0;
        req_priority <= 0;
        cycle_count <= 0;
        state <= IDLE;
        test_num <= 0;
        bank_counter <= 0;
        row_counter <= 0;
        ch_counter <= 0;
        total_reads <= 0;
        total_writes <= 0;
        bank_conflicts <= 0;
    end else begin
        cycle_count <= cycle_count + 1;
        req_valid <= 0;
        req_delay <= req_delay + 1;

        case (state)
            IDLE: begin
                req_valid <= 0;
                if (cycle_count >= 10) begin
                    test_num <= test_num + 1;
                    if (test_num == 1) state <= TEST_SINGLE_READ;
                    else if (test_num == 2) state <= TEST_SINGLE_WRITE;
                    else if (test_num == 3) state <= TEST_BANK_CONFLICT;
                    else if (test_num == 4) state <= TEST_MULTI_CHANNEL;
                    else if (test_num == 5) state <= TEST_REFRESH;
                    else if (test_num == 6) state <= TEST_QOS;
                    else if (test_num == 7) state <= TEST_RANDOM;
                    else if (test_num == 8) state <= TEST_BANK_STRESS;
                    else state <= DONE;
                    $display("");
                    $display("========================================");
                    $display("Starting Test %0d", test_num);
                    if (test_num == 1) $display("Test 1: Single Read");
                    else if (test_num == 2) $display("Test 2: Single Write");
                    else if (test_num == 3) $display("Test 3: Bank Conflict");
                    else if (test_num == 4) $display("Test 4: Multi-Channel");
                    else if (test_num == 5) $display("Test 5: Refresh");
                    else if (test_num == 6) $display("Test 6: QoS Priority");
                    else if (test_num == 7) $display("Test 7: Random Traffic");
                    else if (test_num == 8) $display("Test 8: Bank Stress");
                    $display("========================================");
                end
            end

            TEST_SINGLE_READ: begin
                if (cycle_count >= 20) begin
                    $display("[TB] Test 1: Single Read");
                    req_valid <= 1;
                    req_id <= test_count + 1;
                    req_addr <= 42'h000000000;  // STACK=0, CH=0, BG=0, BK=0, ROW=0, COL=0
                    req_rd_wr_n <= 1;  // Read
                    req_priority <= 3'd4;
                    test_count <= test_count + 1;
                    total_reads <= total_reads + 1;
                    state <= TEST_SINGLE_WRITE;
                end
            end

            TEST_SINGLE_WRITE: begin
                if (cycle_count >= 80) begin
                    $display("[TB] Test 2: Single Write");
                    req_valid <= 1;
                    req_id <= test_count + 1;
                    req_addr <= 42'h000000010;  // COL=0x10
                    req_rd_wr_n <= 0;  // Write
                    req_priority <= 3'd4;
                    test_count <= test_count + 1;
                    total_writes <= total_writes + 1;
                    state <= TEST_BANK_CONFLICT;
                    bank_counter <= 0;
                    row_counter <= 0;
                end
            end

            TEST_BANK_CONFLICT: begin
                if (cycle_count >= 150) begin
                    // Test bank conflicts: same bank, different rows
                    if (bank_counter < 16) begin
                        $display("[TB] Test 3: Bank=%0d Row=%0d", bank_counter, row_counter);
                        req_valid <= 1;
                        req_id <= test_count + 1;
                        req_addr <= {8'h00, 5'd0, 3'd0, bank_counter[3:0], row_counter, 6'd0};
                        req_rd_wr_n <= 1;  // Read
                        req_priority <= 3'd3;
                        test_count <= test_count + 1;
                        total_reads <= total_reads + 1;
                        row_counter <= row_counter + 1;
                        if (row_counter >= 15) begin
                            row_counter <= 0;
                            bank_counter <= bank_counter + 1;
                            bank_conflicts <= bank_conflicts + 1;
                        end
                    end else if (cycle_count >= TEST_BANK_CONFLICT_CYCLES) begin
                        bank_counter <= 0;
                        row_counter <= 0;
                        state <= TEST_MULTI_CHANNEL;
                        test_num <= 3;
                    end
                end
            end

            TEST_MULTI_CHANNEL: begin
                if (cycle_count >= 600) begin
                    // Test 32-channel interleaving
                    $display("[TB] Test 4: Channel=%0d", ch_counter);
                    req_valid <= 1;
                    req_id <= test_count + 1;
                    req_addr <= {8'h00, ch_counter[4:0], 3'd0, 4'd0, row_counter, 6'd0};
                    req_rd_wr_n <= cycle_count[0];  // Alternate read/write
                    req_priority <= {1'b0, ch_counter[2:1]};
                    test_count <= test_count + 1;
                    if (cycle_count[0]) total_reads <= total_reads + 1;
                    else total_writes <= total_writes + 1;
                    row_counter <= row_counter + 1;
                    ch_counter <= ch_counter + 1;
                    if (cycle_count >= TEST_MULTI_CHANNEL_CYCLES) begin
                        row_counter <= 0;
                        ch_counter <= 0;
                        state <= TEST_REFRESH;
                        test_num <= 4;
                    end
                end
            end

            TEST_REFRESH: begin
                if (cycle_count >= 1200) begin
                    // Traffic during refresh periods
                    if ((cycle_count % 50) == 0) begin
                        $display("[TB] Test 5: Refresh - traffic bank=%0d", bank_counter);
                        req_valid <= 1;
                        req_id <= test_count + 1;
                        req_addr <= {8'h00, 5'd0, 3'd0, bank_counter[3:0], row_counter, 6'd0};
                        req_rd_wr_n <= 1;
                        req_priority <= 3'd5;
                        test_count <= test_count + 1;
                        total_reads <= total_reads + 1;
                        bank_counter <= bank_counter + 1;
                        row_counter <= row_counter + 1;
                    end
                    if (cycle_count >= TEST_REFRESH_CYCLES) begin
                        state <= TEST_QOS;
                        test_num <= 5;
                        bank_counter <= 0;
                        row_counter <= 0;
                    end
                end
            end

            TEST_QOS: begin
                if (cycle_count >= 1700) begin
                    // Test QoS priority levels
                    logic [2:0] prio = cycle_count[9:7];
                    $display("[TB] Test 6: Priority=%0d", prio);
                    req_valid <= 1;
                    req_id <= test_count + 1;
                    req_addr <= {8'h00, 5'd0, 3'd0, prio[3:0], row_counter, 6'd0};
                    req_rd_wr_n <= 1;
                    req_priority <= prio;
                    test_count <= test_count + 1;
                    total_reads <= total_reads + 1;
                    row_counter <= row_counter + 1;
                    if (cycle_count >= TEST_QOS_CYCLES) begin
                        row_counter <= 0;
                        state <= TEST_RANDOM;
                        test_num <= 6;
                    end
                end
            end

            TEST_RANDOM: begin
                if (cycle_count >= 2200) begin
                    // Random traffic pattern using LFSR
                    logic [31:0] lfsr = cycle_count ^ (cycle_count << 13);
                    logic [3:0] rnd_bank = lfsr[3:0];
                    logic [15:0] rnd_row = lfsr[31:16];
                    $display("[TB] Test 7: Random bank=%0d row=%0d", rnd_bank, rnd_row);
                    req_valid <= 1;
                    req_id <= test_count + 1;
                    req_addr <= {8'h00, 5'd0, 3'd0, rnd_bank, rnd_row, 6'd0};
                    req_rd_wr_n <= lfsr[0];
                    req_priority <= lfsr[2:0];
                    test_count <= test_count + 1;
                    if (lfsr[0]) total_reads <= total_reads + 1;
                    else total_writes <= total_writes + 1;
                    if (cycle_count >= TEST_RANDOM_CYCLES) begin
                        state <= TEST_BANK_STRESS;
                        test_num <= 7;
                    end
                end
            end

            TEST_BANK_STRESS: begin
                if (cycle_count >= 2700) begin
                    // Stress all 16 banks with high activity
                    logic [3:0] stress_bank = cycle_count[7:4];
                    logic [15:0] stress_row = cycle_count[15:0];
                    $display("[TB] Test 8: Stress bank=%0d row=%0d", stress_bank, stress_row);
                    req_valid <= 1;
                    req_id <= test_count + 1;
                    req_addr <= {8'h00, 5'd0, 3'd0, stress_bank, stress_row, 6'd0};
                    req_rd_wr_n <= cycle_count[0];
                    req_priority <= 3'd7;  // Lowest priority
                    test_count <= test_count + 1;
                    if (cycle_count[0]) total_reads <= total_reads + 1;
                    else total_writes <= total_writes + 1;
                    if (cycle_count >= TEST_BANK_STRESS_CYCLES) begin
                        state <= DONE;
                        test_num <= 8;
                    end
                end
            end

            DONE: begin
                req_valid <= 0;
                $display("");
                $display("========================================");
                $display("HBM Controller Comprehensive Test Results");
                $display("========================================");
                $display("Total tests completed: %0d", test_num);
                $display("Total requests sent: %0d", test_count);
                $display("");
                $display("Transaction Statistics:");
                $display("  Reads:         %0d", total_reads);
                $display("  Writes:        %0d", total_writes);
                if (test_count > 0) begin
                    $display("  Read ratio:    %0d%%", (total_reads * 100) / test_count);
                    $display("  Write ratio:   %0d%%", (total_writes * 100) / test_count);
                end
                $display("");
                $display("DRAM Reference Model:");
                $display("  ACT count:     %0d", ref_act_count);
                $display("  Read count:    %0d", ref_read_count);
                $display("  Write count:   %0d", ref_write_count);
                $display("  Row hits:      %0d", ref_row_hits);
                $display("  Row misses:    %0d", ref_row_misses);
                if ((ref_row_hits + ref_row_misses) > 0)
                    $display("  Hit rate:      %0d%%", (ref_row_hits * 100) / (ref_row_hits + ref_row_misses));
                $display("");
                $display("Controller Statistics:");
                $display("  Requests:      %0d", wrapper_stat_requests);
                $display("  Completed:    %0d", wrapper_stat_completed);
                $display("  Hit rate:      %0d%%", wrapper_stat_hit_rate);
                $display("");
                $display("Bandwidth Metrics:");
                $display("  Current:       %0d Gbps", bw_bandwidth_gbps);
                $display("  Efficiency:    %0d%%", bw_efficiency_pct);
                $display("  Peak:          %0d Gbps", bw_peak_bw);
                $display("");
                if (timing_total_violations > 0)
                    $display("WARNING: Timing violations detected: %0d", timing_total_violations);
                else
                    $display("No timing violations detected");
                $display("========================================");
                $display("[TB] Simulation completed successfully");
                $finish;
            end

            default: state <= IDLE;
        endcase
    end
end

// =============================================================
// VCD Waveform Dump
// =============================================================
initial begin
    $dumpfile("hbm_tb.vcd");
    $dumpvars(0, hbm_tb);
end

endmodule : hbm_tb