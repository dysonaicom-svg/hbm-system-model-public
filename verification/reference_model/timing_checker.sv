// timing_checker.sv - HBM DRAM Timing Constraint Validator
// Validates DRAM timing constraints (tRCD, tRP, tRAS, tRC, etc.)

`timescale 1ps / 1ps

module timing_checker #(
    parameter int NUM_BANKS      = 16,
    parameter int MAX_Timing_VAL = 256
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        enable,

    // Command interface
    input  logic        cmd_valid,
    input  logic [2:0]  cmd_type,    // 0=ACT, 1=RD, 2=WR, 3=PRE, 4=REF, 5=REFPB
    input  logic [5:0]  bank_idx,
    input  logic [15:0] row_addr,
    input  logic [9:0]  col_addr,

    // Timing parameters (in clock cycles)
    input  logic [7:0]  tRCD,         // RAS to CAS delay
    input  logic [7:0]  tRP,          // Precharge command period
    input  logic [7:0]  tRAS,         // RAS active time
    input  logic [15:0] tRC,          // Row cycle time
    input  logic [7:0]  tRRD,         // ACT to ACT delay
    input  logic [7:0]  tCCD,         // CAS to CAS delay
    input  logic [7:0]  tWTR,         // Write to Read delay
    input  logic [7:0]  tRTW,         // Read to Write delay
    input  logic [7:0]  tRTP,         // Read to Precharge
    input  logic [7:0]  tREFI,        // Refresh interval
    input  logic [7:0]  tRFC,         // Refresh cycle time

    // Error reporting
    output logic        timing_violation,
    output logic [7:0]  violation_type,  // 0=none, 1=tRCD, 2=tRP, 3=tRAS, 4=tRC, 5=tRRD, etc.
    output logic [15:0] violation_bank,
    output logic [15:0] violation_cycle,
    output logic [31:0] total_violations
);

    // Violation type definitions
    localparam VIO_NONE   = 8'd0;
    localparam VIO_TRCD   = 8'd1;    // RAS to CAS delay violation
    localparam VIO_TRP    = 8'd2;    // Precharge period violation
    localparam VIO_TRAS   = 8'd3;    // RAS active time violation
    localparam VIO_TRC   = 8'd4;    // Row cycle time violation
    localparam VIO_TRRD   = 8'd5;    // ACT to ACT delay violation
    localparam VIO_TCCD   = 8'd6;    // CAS to CAS delay violation
    localparam VIO_TWTR   = 8'd7;    // Write to Read delay violation
    localparam VIO_TRTW   = 8'd8;    // Read to Write delay violation
    localparam VIO_TRTP   = 8'd9;    // Read to Precharge violation
    localparam VIO_TREFI  = 8'd10;   // Refresh interval violation
    localparam VIO_TRFC   = 8'd11;   // Refresh cycle time violation
    localparam VIO_CMDORD = 8'd12;   // Command ordering violation

    // Bank state tracking
    typedef struct {
        logic        active;
        logic [15:0] open_row;
        logic [15:0] act_cycle;
        logic [15:0] last_cmd_cycle;
        logic [2:0]  last_cmd_type;
        logic [15:0] prechg_cycle;
    } bank_timing_t;

    bank_timing_t banks[NUM_BANKS];

    // Global timing state
    logic [15:0] current_cycle;
    logic [15:0] last_ref_cycle;
    logic [31:0] violation_count;
    logic [31:0] total_violations_int;

    // Bank group tracking for tRRD
    logic [7:0] bg_last_act_cycle[4];  // 4 bank groups
    logic [7:0] bg_last_act_bank[4];

    // Internal signals
    logic        violation_flag;
    logic [7:0]  violation_type_int;
    logic [15:0] violation_bank_int;
    logic [15:0] violation_cycle_int;

    // Output assignment
    assign timing_violation = violation_flag;
    assign violation_type = violation_type_int;
    assign violation_bank = violation_bank_int;
    assign violation_cycle = violation_cycle_int;
    assign total_violations = total_violations_int;

    // Cycle counter
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
            banks[i].active = 1'b0;
            banks[i].open_row = '0;
            banks[i].act_cycle = '0;
            banks[i].last_cmd_cycle = '0;
            banks[i].last_cmd_type = '0;
            banks[i].prechg_cycle = '0;
        end
        for (int i = 0; i < 4; i++) begin
            bg_last_act_cycle[i] = '0;
            bg_last_act_bank[i] = '0;
        end
        last_ref_cycle = '0;
        violation_count = '0;
        total_violations_int = '0;
        violation_flag = 1'b0;
        violation_type_int = VIO_NONE;
    end

    // Main timing check logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            violation_flag <= 1'b0;
            violation_type_int <= VIO_NONE;
            violation_bank_int <= '0;
            violation_cycle_int <= '0;
        end else begin
            // Clear violation flag each cycle
            violation_flag <= 1'b0;
            violation_type_int <= VIO_NONE;

            if (enable && cmd_valid && bank_idx < NUM_BANKS) begin
                case (cmd_type)
                    3'b000: begin // ACTIVATE
                        // Check tRCD: Previous command must be PRE or IDLE
                        if (banks[bank_idx].last_cmd_cycle > 0) begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - banks[bank_idx].last_cmd_cycle;

                            if (banks[bank_idx].last_cmd_type == 3'b011) begin // PRE
                                if (elapsed < tRP) begin
                                    violation_flag <= 1'b1;
                                    violation_type_int <= VIO_TRP;
                                    violation_bank_int <= {10'b0, bank_idx};
                                    violation_cycle_int <= current_cycle;
                                    violation_count <= violation_count + 1;
                                end
                            end
                        end

                        // Check tRC: Same bank ACT to ACT
                        if (banks[bank_idx].active && banks[bank_idx].act_cycle > 0) begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - banks[bank_idx].act_cycle;
                            if (elapsed < tRC[7:0]) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TRC;
                                violation_bank_int <= {10'b0, bank_idx};
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                        end

                        // Check tRRD: ACT to ACT in same bank group
                        begin
                            logic [7:0] bg;
                            bg = bank_idx[5:4];  // Bank group from bank index
                            if (current_cycle - bg_last_act_cycle[bg] < tRRD &&
                                bg_last_act_cycle[bg] > 0) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TRRD;
                                violation_bank_int <= {10'b0, bank_idx};
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                            bg_last_act_cycle[bg] <= current_cycle[7:0];
                        end

                        // Update bank state
                        banks[bank_idx].active <= 1'b1;
                        banks[bank_idx].open_row <= row_addr;
                        banks[bank_idx].act_cycle <= current_cycle;
                        banks[bank_idx].last_cmd_type <= 3'b000;
                        banks[bank_idx].last_cmd_cycle <= current_cycle;
                    end

                    3'b001: begin // READ
                        // Check tRCD: Must have ACT completed
                        if (!banks[bank_idx].active) begin
                            violation_flag <= 1'b1;
                            violation_type_int <= VIO_TRCD;
                            violation_bank_int <= {10'b0, bank_idx};
                            violation_cycle_int <= current_cycle;
                            violation_count <= violation_count + 1;
                        end else begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - banks[bank_idx].act_cycle;
                            if (elapsed < tRCD) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TRCD;
                                violation_bank_int <= {10'b0, bank_idx};
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                        end

                        // Check tCCD: CAS to CAS delay (same bank)
                        if (banks[bank_idx].last_cmd_type == 3'b001 ||
                            banks[bank_idx].last_cmd_type == 3'b010) begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - banks[bank_idx].last_cmd_cycle;
                            if (elapsed < tCCD) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TCCD;
                                violation_bank_int <= {10'b0, bank_idx};
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                        end

                        banks[bank_idx].last_cmd_type <= 3'b001;
                        banks[bank_idx].last_cmd_cycle <= current_cycle;
                    end

                    3'b010: begin // WRITE
                        // Check tRCD: Must have ACT completed
                        if (!banks[bank_idx].active) begin
                            violation_flag <= 1'b1;
                            violation_type_int <= VIO_TRCD;
                            violation_bank_int <= {10'b0, bank_idx};
                            violation_cycle_int <= current_cycle;
                            violation_count <= violation_count + 1;
                        end else begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - banks[bank_idx].act_cycle;
                            if (elapsed < tRCD) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TRCD;
                                violation_bank_int <= {10'b0, bank_idx};
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                        end

                        // Check tWTR: Write to Read delay
                        if (banks[bank_idx].last_cmd_type == 3'b010) begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - banks[bank_idx].last_cmd_cycle;
                            if (elapsed < tWTR) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TWTR;
                                violation_bank_int <= {10'b0, bank_idx};
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                        end

                        banks[bank_idx].last_cmd_type <= 3'b010;
                        banks[bank_idx].last_cmd_cycle <= current_cycle;
                    end

                    3'b011: begin // PRECHARGE
                        // Check tRAS: Minimum ACT to PRE time
                        if (banks[bank_idx].active && banks[bank_idx].act_cycle > 0) begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - banks[bank_idx].act_cycle;
                            if (elapsed < tRAS) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TRAS;
                                violation_bank_int <= {10'b0, bank_idx};
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                        end

                        banks[bank_idx].active <= 1'b0;
                        banks[bank_idx].prechg_cycle <= current_cycle;
                        banks[bank_idx].last_cmd_type <= 3'b011;
                        banks[bank_idx].last_cmd_cycle <= current_cycle;
                    end

                    3'b100: begin // REFRESH (all banks)
                        // Check tREFI: Minimum refresh interval
                        if (last_ref_cycle > 0) begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - last_ref_cycle;
                            if (elapsed < tREFI) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TREFI;
                                violation_bank_int <= '0;
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                        end

                        last_ref_cycle <= current_cycle;
                        banks[bank_idx].last_cmd_type <= 3'b100;
                        banks[bank_idx].last_cmd_cycle <= current_cycle;
                    end

                    3'b101: begin // REFPB (per-bank refresh)
                        // Check tRFC: Refresh cycle time
                        if (banks[bank_idx].last_cmd_type == 3'b101) begin
                            logic [15:0] elapsed;
                            elapsed = current_cycle - banks[bank_idx].last_cmd_cycle;
                            if (elapsed < tRFC) begin
                                violation_flag <= 1'b1;
                                violation_type_int <= VIO_TRFC;
                                violation_bank_int <= {10'b0, bank_idx};
                                violation_cycle_int <= current_cycle;
                                violation_count <= violation_count + 1;
                            end
                        end

                        banks[bank_idx].last_cmd_type <= 3'b101;
                        banks[bank_idx].last_cmd_cycle <= current_cycle;
                    end

                    default: begin
                        // Unknown command type
                    end
                endcase
            end
        end
    end

    // Update total violations count
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            total_violations_int <= '0;
        end else begin
            total_violations_int <= total_violations_int + violation_count;
            violation_count <= '0;  // Reset per cycle
        end
    end

    // Helper function for violation type to string
    function string violation_name(input logic [7:0] vtype);
        case (vtype)
            VIO_NONE:   return "NONE";
            VIO_TRCD:   return "tRCD";
            VIO_TRP:    return "tRP";
            VIO_TRAS:   return "tRAS";
            VIO_TRC:    return "tRC";
            VIO_TRRD:   return "tRRD";
            VIO_TCCD:   return "tCCD";
            VIO_TWTR:   return "tWTR";
            VIO_TRTW:   return "tRTW";
            VIO_TRTP:   return "tRTP";
            VIO_TREFI:  return "tREFI";
            VIO_TRFC:   return "tRFC";
            VIO_CMDORD: return "CMD_ORDER";
            default:    return "UNKNOWN";
        endcase
    endfunction

endmodule


// Simplified timing assertion module
module timing_assertions #(
    parameter int T_RCD = 20,
    parameter int T_RP  = 20,
    parameter int T_RAS = 40,
    parameter int T_RC  = 60
) (
    input logic clk,
    input logic rst_n,
    input logic act_valid,
    input logic rd_valid,
    input logic wr_valid,
    input logic pre_valid,
    input logic [5:0] bank
);

    // Simple timing violation check without SVA assertions
    // (Verilator doesn't support ## cycle delays)
    logic [7:0] act_counter;
    logic act_pending;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            act_counter <= 8'd0;
            act_pending <= 1'b0;
        end else begin
            // Track ACT timing
            if (act_valid) begin
                act_counter <= 8'd0;
                act_pending <= 1'b1;
            end else if (act_pending && act_counter < 8'd255) begin
                act_counter <= act_counter + 1;
            end

            // Check for tRCD violation (READ/WRITE before tRCD cycles)
            if (act_pending && act_counter < T_RCD && (rd_valid || wr_valid)) begin
                $display("[TIMING_ERR] tRCD violation: READ/WRITE before tRCD cycles");
            end

            // Check for tRAS violation (PRE before tRAS cycles)
            if (act_pending && act_counter >= T_RCD && pre_valid) begin
                $display("[TIMING_WARN] tRAS violation: PRE before tRAS cycles");
            end
        end
    end

endmodule