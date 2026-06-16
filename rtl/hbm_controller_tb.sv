// =============================================================================
// HBM Controller Testbench - SystemVerilog wrapper
// Clock is driven externally by C++ testbench main
// =============================================================================

`timescale 1ns / 1ps
`include "hbm_types.svh"

module hbm_controller_tb;

    // ============================================================================
    // Clock - driven externally by C++ main
    // ============================================================================
    logic clk = 0;
    int cycle_count = 0;

    always @(posedge clk) begin
        cycle_count <= cycle_count + 1;
    end

    // ============================================================================
    // Signals - matching controller interface widths
    // ============================================================================
    logic        rst_n = 0;
    logic        req_valid = 0;
    logic [31:0] req_id = 0;
    // Calculate address width: STACK(2) + CH(5) + BG(3) + BK(4) + ROW(16) + COL(6) = 36 bits
    localparam ADDR_WIDTH = 2 + 5 + 3 + 4 + 16 + 6;
    logic [ADDR_WIDTH-1:0] req_addr = 0;
    logic        req_rd_wr_n = 1;
    logic [15:0] req_len = 64;
    logic [2:0]  req_priority = 0;
    logic        req_ready;
    logic        resp_valid;
    logic [31:0] resp_id;
    logic        resp_success;
    logic [7:0]  resp_status;

    // DRAM interface - 4-bit command encoding per hbm_types.svh
    logic [3:0]  dram_cmd;
    logic [4:0]  dram_ch;      // 5 bits for HBM4 32 channels
    logic [2:0]  dram_bg;      // 3 bits for bank group
    logic [3:0]  dram_bank;
    logic [0:0]  dram_pch;     // 1 bit for pseudo-channel
    logic [15:0] dram_row;
    logic [255:0] dram_rd_data = 0;
    logic [255:0] dram_wr_data = 0;

    // Statistics
    logic [31:0] stat_requests;
    logic [31:0] stat_completed;
    logic [7:0]  stat_hit_rate;

    // ============================================================================
    // DUT - HBM4 Controller
    // ============================================================================
    hbm_controller #(
        .QUEUE_DEPTH(32),
        .STACK_ADDR_WIDTH(2),
        .CH_ADDR_WIDTH(5),     // HBM4: 32 channels
        .BG_ADDR_WIDTH(3),
        .BK_ADDR_WIDTH(4),
        .ROW_ADDR_WIDTH(16),
        .COL_ADDR_WIDTH(6),
        .PCH_ADDR_WIDTH(1)
    ) dut (
        .clk(clk), .rst_n(rst_n),
        .req_valid(req_valid), .req_id(req_id), .req_addr(req_addr),
        .req_rd_wr_n(req_rd_wr_n), .req_len(req_len), .req_priority(req_priority),
        .req_ready(req_ready), .resp_valid(resp_valid), .resp_id(resp_id),
        .resp_success(resp_success), .resp_status(resp_status),
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

    // ============================================================================
    // DRAM Response Model
    // ============================================================================
    // Return data on READ command
    always @(posedge clk) begin
        if (rst_n && (dram_cmd == 4'd2)) begin  // CMD_READ
            dram_rd_data <= 256'hDEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF
                           + {{8{resp_id[7:0]}}, 32'd0};
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