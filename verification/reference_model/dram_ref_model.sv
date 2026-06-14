// dram_ref_model.sv - DRAM Performance Reference Model
// Tracks bank states, command statistics, and calculates average latency

`timescale 1ps / 1ps

module dram_ref_model #(
    parameter int NUM_BANKS = 16,
    parameter int NUM_BANK_GROUPS = 4
) (
    input  logic        clk,
    input  logic        rst_n,

    // Command interface
    input  logic        cmd_valid,
    input  logic [2:0]  cmd_type,     // 0=ACT, 1=RD, 2=WR, 3=PRE, 4=REF, 5=REFPB
    input  logic [5:0]  bank_idx,
    input  logic [15:0] row_addr,
    input  logic [9:0]  col_addr,

    // Timing parameters (in cycles)
    input  logic [7:0]  tRCD,
    input  logic [7:0]  tRP,
    input  logic [7:0]  tRAS,
    input  logic [15:0] tRC,

    // Statistics output
    output logic [31:0] act_count,
    output logic [31:0] read_count,
    output logic [31:0] write_count,
    output logic [31:0] row_hits,
    output logic [31:0] row_misses,
    output logic [31:0] avg_latency
);

    // Bank state enumeration
    typedef enum logic [2:0] {
        BANK_IDLE    = 3'b000,
        BANK_ACTIVE  = 3'b001,
        BANK_BUSY_RD = 3'b010,
        BANK_BUSY_WR = 3'b011,
        BANK_BUSY    = 3'b100,
        BANK_REFRESH = 3'b101,
        BANK_PRECHRG = 3'b110
    } bank_state_t;

    // Bank state tracking
    typedef struct {
        bank_state_t state;
        logic [15:0] open_row;
        logic [15:0] act_cycle;
        logic        valid;
    } bank_info_t;

    bank_info_t banks[NUM_BANKS];

    // Statistics counters
    logic [31:0] act_count_int;
    logic [31:0] read_count_int;
    logic [31:0] write_count_int;
    logic [31:0] row_hits_int;
    logic [31:0] row_misses_int;

    // Latency tracking
    logic [31:0] latency_sum;
    logic [31:0] latency_count;
    logic [31:0] avg_latency_int;

    // Internal tracking
    logic [15:0] current_cycle;
    logic        cmd_accept;
    logic [2:0]  prev_cmd_type;
    logic [5:0]  prev_bank_idx;
    logic [15:0] prev_row_addr;

    // Timing counters per bank
    logic [7:0] bank_timer[NUM_BANKS];

    // Initialize statistics outputs
    assign act_count    = act_count_int;
    assign read_count    = read_count_int;
    assign write_count   = write_count_int;
    assign row_hits      = row_hits_int;
    assign row_misses    = row_misses_int;
    assign avg_latency   = avg_latency_int;

    // Reset and clock
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_cycle <= '0;
        end else begin
            current_cycle <= current_cycle + 1;
        end
    end

    // Initialize bank states
    initial begin
        for (int i = 0; i < NUM_BANKS; i++) begin
            banks[i].state = BANK_IDLE;
            banks[i].open_row = '0;
            banks[i].act_cycle = '0;
            banks[i].valid = 1'b1;
            bank_timer[i] = '0;
        end
        act_count_int = '0;
        read_count_int = '0;
        write_count_int = '0;
        row_hits_int = '0;
        row_misses_int = '0;
        latency_sum = '0;
        latency_count = '0;
        avg_latency_int = '0;
        cmd_accept = 1'b0;
        prev_cmd_type = '0;
        prev_bank_idx = '0;
        prev_row_addr = '0;
    end

    // Main bank state machine and statistics
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < NUM_BANKS; i++) begin
                banks[i].state = BANK_IDLE;
                banks[i].open_row = '0;
                bank_timer[i] = '0;
            end
        end else begin
            // Update timers for all banks
            for (int i = 0; i < NUM_BANKS; i++) begin
                if (bank_timer[i] > 0) begin
                    bank_timer[i] = bank_timer[i] - 1;
                    // Check if timer expired and transition state
                    if (bank_timer[i] == 0) begin
                        case (banks[i].state)
                            BANK_ACTIVE: banks[i].state = BANK_IDLE;
                            BANK_BUSY_RD: banks[i].state = BANK_ACTIVE;
                            BANK_BUSY_WR: banks[i].state = BANK_ACTIVE;
                            BANK_BUSY: banks[i].state = BANK_IDLE;
                            BANK_REFRESH: banks[i].state = BANK_IDLE;
                            BANK_PRECHRG: banks[i].state = BANK_IDLE;
                            default: banks[i].state = BANK_IDLE;
                        endcase
                    end
                end
            end

            // Process command
            if (cmd_valid && !cmd_accept) begin
                cmd_accept = 1'b1;
                prev_cmd_type = cmd_type;
                prev_bank_idx = bank_idx;
                prev_row_addr = row_addr;

                case (cmd_type)
                    3'b000: begin // ACT
                        if (bank_idx < NUM_BANKS) begin
                            act_count_int = act_count_int + 1;
                            banks[bank_idx].state = BANK_ACTIVE;
                            banks[bank_idx].open_row = row_addr;
                            banks[bank_idx].act_cycle = current_cycle;
                            bank_timer[bank_idx] = tRCD;
                        end
                    end

                    3'b001: begin // READ
                        if (bank_idx < NUM_BANKS) begin
                            read_count_int = read_count_int + 1;
                            // Check for row hit/miss
                            if (banks[bank_idx].state == BANK_ACTIVE &&
                                banks[bank_idx].open_row == row_addr) begin
                                row_hits_int = row_hits_int + 1;
                            end else begin
                                row_misses_int = row_misses_int + 1;
                            end
                            banks[bank_idx].state = BANK_BUSY_RD;
                            bank_timer[bank_idx] = tRCD;
                        end
                    end

                    3'b010: begin // WRITE
                        if (bank_idx < NUM_BANKS) begin
                            write_count_int = write_count_int + 1;
                            // Check for row hit/miss
                            if (banks[bank_idx].state == BANK_ACTIVE &&
                                banks[bank_idx].open_row == row_addr) begin
                                row_hits_int = row_hits_int + 1;
                            end else begin
                                row_misses_int = row_misses_int + 1;
                            end
                            banks[bank_idx].state = BANK_BUSY_WR;
                            bank_timer[bank_idx] = tRCD;
                        end
                    end

                    3'b011: begin // PRECHARGE
                        if (bank_idx < NUM_BANKS) begin
                            banks[bank_idx].state = BANK_PRECHRG;
                            bank_timer[bank_idx] = tRP;
                        end
                    end

                    3'b100: begin // REFRESH (all banks)
                        for (int i = 0; i < NUM_BANKS; i++) begin
                            banks[i].state = BANK_REFRESH;
                            bank_timer[i] = tRC[7:0];
                        end
                    end

                    3'b101: begin // REFPB (per-bank refresh)
                        if (bank_idx < NUM_BANKS) begin
                            banks[bank_idx].state = BANK_REFRESH;
                            bank_timer[bank_idx] = tRC[7:0];
                        end
                    end

                    default: begin
                        cmd_accept = 1'b0;
                    end
                endcase
            end else begin
                cmd_accept = 1'b0;
            end
        end
    end

    // Calculate average latency
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            latency_sum = '0;
            latency_count = '0;
            avg_latency_int = '0;
        end else begin
            // Calculate latency when operation completes
            if (cmd_valid && (cmd_type == 3'b001 || cmd_type == 3'b010)) begin
                if (latency_count < 32'hFFFFFFFF) begin
                    latency_count = latency_count + 1;
                    // Simplified latency calculation based on row hit/miss
                    if (row_hits_int > 0 || row_misses_int > 0) begin
                        // Average latency: hits are faster
                        latency_sum = latency_sum + (prev_row_addr == banks[prev_bank_idx].open_row ?
                                                      16'd100 : 16'd200);
                    end
                end
            end

            // Update average
            if (latency_count > 0) begin
                avg_latency_int = latency_sum / latency_count;
            end
        end
    end

    // Utility functions
    function logic is_bank_idle(input logic [5:0] bank);
        return (bank < NUM_BANKS) && (banks[bank].state == BANK_IDLE);
    endfunction

    function logic is_bank_active(input logic [5:0] bank);
        return (bank < NUM_BANKS) && (banks[bank].state == BANK_ACTIVE);
    endfunction

    function logic is_row_open(input logic [5:0] bank, input logic [15:0] row);
        return is_bank_active(bank) && (banks[bank].open_row == row);
    endfunction

endmodule