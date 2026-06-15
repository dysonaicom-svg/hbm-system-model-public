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

parameter time CLK_PERIOD = 2ns;

initial begin
    clk = 0;
    forever begin
        #1 clk = ~clk;
    end
end

initial begin
    rst_n = 0;
    #11 rst_n = 1;
    $display("[TB] Reset released at time %0t", $time);
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
logic [33:0]  req_addr;
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
// RTL Controller Instantiation
// =============================================================
hbm_controller #(
    .QUEUE_DEPTH      (32),
    .STACK_ADDR_WIDTH (8),
    .CH_ADDR_WIDTH    (2),
    .BG_ADDR_WIDTH    (2),
    .BK_ADDR_WIDTH    (3),
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
// Testbench Stimulus (combinational FSM)
// =============================================================
int test_count = 0;
int cycle_count = 0;
logic [1:0] state;

// State machine states
localparam IDLE = 2'd0;
localparam SEND_READ = 2'd1;
localparam SEND_WRITE = 2'd2;
localparam DONE = 2'd3;

// FSM
always @(posedge clk) begin
    if (!rst_n) begin
        req_valid <= 0;
        req_id <= 0;
        req_addr <= 0;
        req_rd_wr_n <= 0;
        req_len <= 0;
        req_priority <= 0;
        cycle_count <= 0;
        state <= IDLE;
    end else begin
        cycle_count <= cycle_count + 1;

        case (state)
            IDLE: begin
                req_valid <= 0;
                if (cycle_count >= 10) begin
                    $display("[TB] === Test 1: Single Read ===");
                    req_valid <= 1;
                    req_id <= 32'd1;
                    req_addr <= 34'h00000000;
                    req_rd_wr_n <= 1;
                    test_count <= test_count + 1;
                    state <= SEND_READ;
                end
            end

            SEND_READ: begin
                req_valid <= 0;
                if (cycle_count >= 60) begin
                    $display("[TB] === Test 2: Single Write ===");
                    req_valid <= 1;
                    req_id <= 32'd2;
                    req_addr <= 34'h00000010;
                    req_rd_wr_n <= 0;
                    test_count <= test_count + 1;
                    state <= SEND_WRITE;
                end
            end

            SEND_WRITE: begin
                req_valid <= 0;
                if (cycle_count >= 200) begin
                    state <= DONE;
                end
            end

            DONE: begin
                req_valid <= 0;
                $display("");
                $display("========================================");
                $display("HBM Controller Test Results");
                $display("========================================");
                $display("Total requests sent: %0d", test_count);
                $display("DRAM Reference Model:");
                $display("  ACT count:     %0d", ref_act_count);
                $display("  Read count:    %0d", ref_read_count);
                $display("  Write count:   %0d", ref_write_count);
                $display("  Row hits:      %0d", ref_row_hits);
                $display("  Row misses:   %0d", ref_row_misses);
                $display("");
                $display("Controller Statistics:");
                $display("  Requests:      %0d", wrapper_stat_requests);
                $display("  Completed:    %0d", wrapper_stat_completed);
                $display("  Hit rate:      %0d%%", wrapper_stat_hit_rate);
                $display("========================================");
                $display("[TB] Simulation completed");
                $finish;
            end
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