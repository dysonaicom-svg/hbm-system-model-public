// =============================================================================
// HBM DRAM Model RTL
// Implements behavioral DRAM model with timing compliance
// =============================================================================

`timescale 1ns / 1ps

module dram_model #(
    // Timing parameters (in cycles @ 1GHz reference)
    parameter integer T_RCD    = 20,  // RAS to CAS delay
    parameter integer T_RP     = 20,  // Precharge period
    parameter integer T_RAS    = 320, // Active to precharge
    parameter integer T_RC     = 380, // Active to active
    parameter integer T_RFC    = 160, // Refresh cycle time
    parameter integer T_RTRS   = 4,   // Read-to-read/write-to-write switching
    parameter integer T_WTR    = 4,   // Write to read delay
    parameter integer T_RTW    = 4,   // Read to write delay
    parameter integer NUM_BANKS = 16,
    parameter integer NUM_BANKS_PER_ROW = 8,
    parameter integer NUM_ROWS = 65536,
    parameter integer BANK_ADDR_WIDTH = 4,
    parameter integer ROW_ADDR_WIDTH = 16,
    parameter integer DATA_WIDTH = 256,
    parameter integer BURST_LENGTH = 4  // BL4 or BL8
) (
    input  wire                           clk,
    input  wire                           rst_n,

    // Command interface
    input  wire [3:0]                    cmd,        // 4-bit command code
    input  wire [2:0]                    ch_id,      // Channel ID (0-7)
    input  wire [BANK_ADDR_WIDTH-1:0]    bank_id,    // Bank address (0-15)
    input  wire [ROW_ADDR_WIDTH-1:0]     row_id,     // Row address (0-65535)

    // Data interface
    input  wire [DATA_WIDTH-1:0]        wr_data,    // Write data
    output reg  [DATA_WIDTH-1:0]         rd_data,    // Read data

    // Bank state visibility
    output reg  [2:0]                    bank_state [0:NUM_BANKS-1],

    // Status outputs
    output wire                          cmd_ack,    // Command acknowledged
    output wire                          cmd_error,  // Command error flag
    output wire [3:0]                    error_code  // Specific error code
);

// =============================================================================
// Command Definitions
// =============================================================================
localparam CMD_NOP  = 4'b0000;
localparam CMD_ACT = 4'b0001;  // Activate
localparam CMD_READ= 4'b0010;  // Read
localparam CMD_WRITE=4'b0011;  // Write
localparam CMD_PRE = 4'b0100;  // Precharge
localparam CMD_REF = 4'b0101;  // Refresh (all banks)
localparam CMD_MRS = 4'b0110;  // Mode Register Set
localparam CMD_ZQ  = 4'b0111;  // ZQ calibration

// =============================================================================
// Bank State Definitions
// =============================================================================
localparam S_IDLE     = 3'b000;  // Bank is idle, row closed
localparam S_ACTIVE   = 3'b001;  // Bank is active, row open
localparam S_BUSY     = 3'b010;  // Bank is busy with operation
localparam S_REFRESH  = 3'b011;  // Bank in refresh mode
localparam S_POWERDN  = 3'b100;  // Bank in power down mode
localparam S_SELFREF  = 3'b101;  // Bank in self-refresh mode

// =============================================================================
// Internal State Variables
// =============================================================================

// Per-bank state registers
reg [2:0]                      bank_st_cur  [0:NUM_BANKS-1];
reg [2:0]                      bank_st_nxt  [0:NUM_BANKS-1];

// Per-bank open row tracking
reg [ROW_ADDR_WIDTH-1:0]       open_row     [0:NUM_BANKS-1];
reg [ROW_ADDR_WIDTH-1:0]       open_row_nxt [0:NUM_BANKS-1];

// Per-bank timer counters
reg [9:0]                      timer_cnt    [0:NUM_BANKS-1];
reg [9:0]                      timer_cnt_nxt[0:NUM_BANKS-1];
reg                            timer_run    [0:NUM_BANKS-1];
reg                            timer_run_nxt[0:NUM_BANKS-1];

// Timer type indicator
reg [2:0]                      timer_type   [0:NUM_BANKS-1];
localparam TIMER_NONE  = 3'b000;
localparam TIMER_ACT   = 3'b001;
localparam TIMER_RD    = 3'b010;
localparam TIMER_WR    = 3'b011;
localparam TIMER_PRE   = 3'b100;
localparam TIMER_REF   = 3'b101;

// Command queue for pipelining
reg  [3:0]                     cmd_q;
reg  [BANK_ADDR_WIDTH-1:0]      bank_id_q;
reg  [ROW_ADDR_WIDTH-1:0]       row_id_q;
reg                            cmd_valid_q;
reg                            cmd_accept;
reg                            cmd_accept_nxt;

// Status flags
reg                            cmd_ack_reg;
reg                            cmd_error_reg;
reg  [3:0]                     error_code_reg;

// Memory array (SRAM-style organized)
// [bank][row][column] - simplified as 2D array per bank
// Each row contains 256-bit data per column (8 columns for BL4 x 256-bit = 32 bytes per beat)
// For simulation efficiency, we model a subset of memory
localparam COLS_PER_ROW = 64;  // Number of column addresses per row
localparam COL_ADDR_WIDTH = 6;

// Memory array: [bank][row][col]
reg [DATA_WIDTH-1:0]           mem_array [0:NUM_BANKS-1][0:255][0:COLS_PER_ROW-1];

// Column counter for burst operations
reg [COL_ADDR_WIDTH-1:0]       col_addr [0:NUM_BANKS-1];
reg [COL_ADDR_WIDTH-1:0]       col_addr_nxt[0:NUM_BANKS-1];

// Write data buffer
reg [DATA_WIDTH-1:0]          wr_data_buf [0:NUM_BANKS-1];

// Read data valid pipeline
reg                            rd_data_valid;
reg                            rd_data_valid_nxt;

// Bank conflict detection
wire                           same_row_open;
wire                           bank_active;
wire                           bank_idle;

// =============================================================================
// Combinational Logic
// =============================================================================

// Check if bank has same row open
assign same_row_open = bank_st_cur[bank_id] == S_ACTIVE &&
                        open_row[bank_id] == row_id;

// Check if bank is active
assign bank_active = (bank_st_cur[bank_id] == S_ACTIVE) ||
                     (bank_st_cur[bank_id] == S_BUSY);

// Check if bank is idle
assign bank_idle = bank_st_cur[bank_id] == S_IDLE;

// Command acknowledgment
assign cmd_ack = cmd_accept & ~cmd_error_reg;

// Error code definitions:
// 4'b0001 - Bank conflict (trying to ACT active bank)
// 4'b0010 - Row mismatch (trying to READ/WRITE different row)
// 4'b0011 - Bank not active (READ/WRITE without ACT)
// 4'b0100 - Timing violation
// 4'b0101 - Invalid command
// 4'b0110 - Invalid bank address
// 4'b0111 - Invalid row address
assign cmd_error = cmd_error_reg;
assign error_code = error_code_reg;

// =============================================================================
// Command Decoder and Handler
// =============================================================================

always @(*) begin
    // Default values
    cmd_accept_nxt = 1'b0;
    cmd_error_reg = 1'b0;
    error_code_reg = 4'b0000;
    rd_data_valid_nxt = 1'b0;

    // Process command if valid
    if (cmd_valid_q) begin
        case (cmd_q)
            CMD_NOP: begin
                // No operation - always accepted
                cmd_accept_nxt = 1'b1;
            end

            CMD_ACT: begin
                // Activate command - open a row
                if (bank_id >= NUM_BANKS) begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0110;  // Invalid bank
                end else if (bank_st_cur[bank_id] == S_ACTIVE) begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0001;  // Bank conflict
                end else if (bank_st_cur[bank_id] == S_BUSY) begin
                    // Check if timing allows
                    if (timer_cnt[bank_id] == 10'd0 && timer_type[bank_id] == TIMER_RD) begin
                        cmd_accept_nxt = 1'b1;
                    end else begin
                        cmd_error_reg = 1'b1;
                        error_code_reg = 4'b0100;  // Timing violation
                    end
                end else if (bank_st_cur[bank_id] == S_REFRESH) begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0100;  // Timing violation
                end else begin
                    // Bank is idle - accept ACT
                    cmd_accept_nxt = 1'b1;
                end
            end

            CMD_READ: begin
                // Read command - requires bank active with matching row
                if (bank_id >= NUM_BANKS) begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0110;
                end else if (bank_st_cur[bank_id] == S_IDLE) begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0011;  // Bank not active
                end else if (bank_st_cur[bank_id] == S_ACTIVE) begin
                    if (!same_row_open) begin
                        cmd_error_reg = 1'b1;
                        error_code_reg = 4'b0010;  // Row mismatch
                    end else begin
                        cmd_accept_nxt = 1'b1;
                    end
                end else begin
                    // Bank busy - check timing
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0100;
                end
            end

            CMD_WRITE: begin
                // Write command - requires bank active with matching row
                if (bank_id >= NUM_BANKS) begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0110;
                end else if (bank_st_cur[bank_id] == S_IDLE) begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0011;
                end else if (bank_st_cur[bank_id] == S_ACTIVE) begin
                    if (!same_row_open) begin
                        cmd_error_reg = 1'b1;
                        error_code_reg = 4'b0010;
                    end else begin
                        cmd_accept_nxt = 1'b1;
                    end
                end else begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0100;
                end
            end

            CMD_PRE: begin
                // Precharge - close a row
                if (bank_id >= NUM_BANKS) begin
                    cmd_error_reg = 1'b1;
                    error_code_reg = 4'b0110;
                end else if (bank_st_cur[bank_id] == S_IDLE) begin
                    // Already idle - acceptable
                    cmd_accept_nxt = 1'b1;
                end else if (bank_st_cur[bank_id] == S_BUSY) begin
                    if (timer_cnt[bank_id] == 10'd0) begin
                        cmd_accept_nxt = 1'b1;
                    end else begin
                        cmd_error_reg = 1'b1;
                        error_code_reg = 4'b0100;
                    end
                end else begin
                    cmd_accept_nxt = 1'b1;
                end
            end

            CMD_REF: begin
                // Refresh all banks
                cmd_accept_nxt = 1'b1;
            end

            CMD_MRS: begin
                // Mode register set - for simulation, always accept
                cmd_accept_nxt = 1'b1;
            end

            CMD_ZQ: begin
                // ZQ calibration - always accept
                cmd_accept_nxt = 1'b1;
            end

            default: begin
                cmd_error_reg = 1'b1;
                error_code_reg = 4'b0101;  // Invalid command
            end
        endcase
    end
end

// =============================================================================
// Bank State Machine
// =============================================================================

genvar gen_b;
generate
    for (gen_b = 0; gen_b < NUM_BANKS; gen_b = gen_b + 1) begin : bank_fsm
        // Next state logic
        always @(*) begin
            bank_st_nxt[gen_b] = bank_st_cur[gen_b];
            timer_cnt_nxt[gen_b] = timer_cnt[gen_b];
            timer_run_nxt[gen_b] = timer_run[gen_b];
            open_row_nxt[gen_b] = open_row[gen_b];
            col_addr_nxt[gen_b] = col_addr[gen_b];

            // Only process command for target bank
            if (cmd_valid_q && cmd_accept_nxt && bank_id_q == gen_b) begin
                case (cmd_q)
                    CMD_ACT: begin
                        case (bank_st_cur[gen_b])
                            S_IDLE: begin
                                bank_st_nxt[gen_b] = S_BUSY;
                                timer_cnt_nxt[gen_b] = T_RCD[9:0];
                                timer_run_nxt[gen_b] = 1'b1;
                                open_row_nxt[gen_b] = row_id_q;
                            end
                            S_ACTIVE: begin
                                // Precharge first then activate
                                bank_st_nxt[gen_b] = S_BUSY;
                                timer_cnt_nxt[gen_b] = T_RP[9:0];
                                timer_run_nxt[gen_b] = 1'b1;
                            end
                            S_BUSY: begin
                                // Wait for current operation
                            end
                            default: begin
                                bank_st_nxt[gen_b] = bank_st_cur[gen_b];
                            end
                        endcase
                    end

                    CMD_READ: begin
                        if (bank_st_cur[gen_b] == S_ACTIVE && same_row_open) begin
                            bank_st_nxt[gen_b] = S_BUSY;
                            timer_cnt_nxt[gen_b] = T_RCD[9:0];  // CAS latency
                            timer_run_nxt[gen_b] = 1'b1;
                            col_addr_nxt[gen_b] = 0;
                        end
                    end

                    CMD_WRITE: begin
                        if (bank_st_cur[gen_b] == S_ACTIVE && same_row_open) begin
                            bank_st_nxt[gen_b] = S_BUSY;
                            timer_cnt_nxt[gen_b] = T_WTR[9:0];
                            timer_run_nxt[gen_b] = 1'b1;
                            col_addr_nxt[gen_b] = 0;
                            wr_data_buf[gen_b] = wr_data;
                        end
                    end

                    CMD_PRE: begin
                        case (bank_st_cur[gen_b])
                            S_ACTIVE: begin
                                bank_st_nxt[gen_b] = S_BUSY;
                                timer_cnt_nxt[gen_b] = T_RP[9:0];
                                timer_run_nxt[gen_b] = 1'b1;
                            end
                            S_IDLE: begin
                                // Already idle - no change
                            end
                            S_BUSY: begin
                                if (timer_cnt[gen_b] == 10'd0) begin
                                    bank_st_nxt[gen_b] = S_IDLE;
                                    timer_run_nxt[gen_b] = 1'b0;
                                end
                            end
                            default: begin
                                bank_st_nxt[gen_b] = S_IDLE;
                            end
                        endcase
                    end

                    CMD_REF: begin
                        bank_st_nxt[gen_b] = S_REFRESH;
                        timer_cnt_nxt[gen_b] = T_RFC[9:0];
                        timer_run_nxt[gen_b] = 1'b1;
                    end

                    default: begin
                        // No change
                    end
                endcase
            end

            // Timer countdown logic
            if (timer_run[gen_b] && timer_cnt[gen_b] > 0) begin
                timer_cnt_nxt[gen_b] = timer_cnt[gen_b] - 1;
            end

            // Timer expiration handling
            if (timer_run[gen_b] && timer_cnt[gen_b] == 0) begin
                timer_run_nxt[gen_b] = 1'b0;
                case (bank_st_cur[gen_b])
                    S_BUSY: begin
                        case (timer_type[gen_b])
                            TIMER_ACT: begin
                                bank_st_nxt[gen_b] = S_ACTIVE;
                            end
                            TIMER_RD: begin
                                bank_st_nxt[gen_b] = S_ACTIVE;
                                rd_data_valid_nxt = 1'b1;
                            end
                            TIMER_WR: begin
                                bank_st_nxt[gen_b] = S_ACTIVE;
                            end
                            TIMER_PRE: begin
                                bank_st_nxt[gen_b] = S_IDLE;
                            end
                            TIMER_REF: begin
                                bank_st_nxt[gen_b] = S_IDLE;
                            end
                            default: begin
                                bank_st_nxt[gen_b] = S_ACTIVE;
                            end
                        endcase
                    end
                    default: begin
                        // Keep current state
                    end
                endcase
            end
        end
    end
endgenerate

// =============================================================================
// Sequential Logic
// =============================================================================

// Command queue register
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        cmd_q       <= 4'b0;
        bank_id_q   <= 4'b0;
        row_id_q    <= 16'b0;
        cmd_valid_q <= 1'b0;
        cmd_accept <= 1'b0;
    end else begin
        // Only accept new command if queue is empty
        if (!cmd_valid_q) begin
            cmd_q       <= cmd;
            bank_id_q   <= bank_id;
            row_id_q    <= row_id;
            cmd_valid_q <= 1'b1;
        end else if (cmd_accept_nxt) begin
            // Command processed - clear queue
            cmd_valid_q <= 1'b0;
        end
        cmd_accept <= cmd_accept_nxt;
    end
end

// Bank state registers
always @(posedge clk or negedge rst_n) begin
    integer i;
    if (!rst_n) begin
        for (i = 0; i < NUM_BANKS; i = i + 1) begin
            bank_st_cur[i] <= S_IDLE;
            open_row[i]    <= 0;
            timer_cnt[i]   <= 0;
            timer_run[i]   <= 1'b0;
            timer_type[i]  <= TIMER_NONE;
            col_addr[i]    <= 0;
        end
        rd_data <= 0;
        rd_data_valid <= 1'b0;
    end else begin
        for (i = 0; i < NUM_BANKS; i = i + 1) begin
            bank_st_cur[i] <= bank_st_nxt[i];
            open_row[i]    <= open_row_nxt[i];
            timer_cnt[i]   <= timer_cnt_nxt[i];
            timer_run[i]   <= timer_run_nxt[i];
            col_addr[i]    <= col_addr_nxt[i];
        end

        // Read data output
        if (rd_data_valid) begin
            // Simple burst read - return data from first column
            rd_data <= mem_array[bank_id_q][open_row[bank_id_q]][0];
        end

        rd_data_valid <= rd_data_valid_nxt;
    end
end

// Bank state output (for visibility)
always @(posedge clk or negedge rst_n) begin
    integer i;
    if (!rst_n) begin
        for (i = 0; i < NUM_BANKS; i = i + 1) begin
            bank_state[i] <= S_IDLE;
        end
    end else begin
        for (i = 0; i < NUM_BANKS; i = i + 1) begin
            bank_state[i] <= bank_st_cur[i];
        end
    end
end

// =============================================================================
// Memory Write Operation
// =============================================================================

always @(posedge clk) begin
    if (cmd_valid_q && cmd_accept_nxt && cmd_q == CMD_WRITE) begin
        if (bank_st_cur[bank_id_q] == S_ACTIVE && same_row_open) begin
            // Write data to memory array
            mem_array[bank_id_q][open_row[bank_id_q]][col_addr[bank_id_q]] <= wr_data;
        end
    end
end

// =============================================================================
// Initialization
// =============================================================================

initial begin
    // Initialize memory to known state
    integer b, r, c;
    for (b = 0; b < NUM_BANKS; b = b + 1) begin
        for (r = 0; r < 256; r = r + 1) begin
            for (c = 0; c < COLS_PER_ROW; c = c + 1) begin
                mem_array[b][r][c] = 256'h0;
            end
        end
    end
end

// =============================================================================
// Assertions for Verification
// =============================================================================

// Assert that command is stable during processing
// synthesis translate_off
always @(posedge clk) begin
    if (cmd_valid_q && !cmd_accept_nxt && !cmd_error_reg) begin
        // Command pending - this is expected behavior
    end
end

// Assert bank state transitions are valid
always @(posedge clk) begin
    integer b;
    if (rst_n) begin
        for (b = 0; b < NUM_BANKS; b = b + 1) begin
            // Valid states are 0-5
            assert (bank_st_cur[b] inside {S_IDLE, S_ACTIVE, S_BUSY, S_REFRESH, S_POWERDN, S_SELFREF})
                else $error("Invalid bank state for bank %d: %b", b, bank_st_cur[b]);
        end
    end
end
// synthesis translate_on

endmodule