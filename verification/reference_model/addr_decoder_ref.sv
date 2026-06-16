// addr_decoder_ref.sv - HBM Address Decoder Reference Model
// Supports multiple address mapping modes: RBC, BCR, CRB, etc.

`timescale 1ps / 1ps

module addr_decoder_ref #(
    parameter int ADDR_BITS    = 32,
    parameter int STACK_BITS  = 3,    // Number of stacks (8 max)
    parameter int CHAN_BITS   = 3,    // Channels per stack (8 max)
    parameter int BG_BITS     = 2,    // Bank group bits (4 groups)
    parameter int BA_BITS     = 2,    // Bank bits (4 banks)
    parameter int ROW_BITS   = 16,   // Row address bits
    parameter int COL_BITS   = 10    // Column address bits
) (
    input  logic [ADDR_BITS-1:0] addr,
    input  logic [2:0]          mapping_mode,  // Address mapping mode selector

    // Decoded outputs
    output logic [STACK_BITS-1:0] stack,
    output logic [CHAN_BITS-1:0]  channel,
    output logic [BG_BITS-1:0]   bank_group,
    output logic [BA_BITS-1:0]   bank,
    output logic [ROW_BITS-1:0]  row,
    output logic [COL_BITS-1:0]  col,
    output logic                 valid
);

    // Address mapping mode definitions
    localparam MODE_RBC = 3'd0;  // Row-Bank-Column (standard)
    localparam MODE_BCR = 3'd1;  // Bank-Column-Row
    localparam MODE_CRB = 3'd2;  // Column-Row-Bank
    localparam MODE_BRC = 3'd3;  // Bank-Row-Column
    localparam MODE_RCB = 3'd4;  // Row-Column-Bank
    localparam MODE_CBR = 3'd5;  // Column-Bank-Row

    // Calculate total bits needed
    localparam TOTAL_DECODE_BITS = STACK_BITS + CHAN_BITS + BG_BITS + BA_BITS + ROW_BITS + COL_BITS;
    localparam STACK_CHAN_BITS   = STACK_BITS + CHAN_BITS;

    // Intermediate decoded values
    logic [STACK_BITS-1:0]  stack_int;
    logic [CHAN_BITS-1:0]   channel_int;
    logic [BG_BITS-1:0]    bg_int;
    logic [BA_BITS-1:0]    ba_int;
    logic [ROW_BITS-1:0]   row_int;
    logic [COL_BITS-1:0]   col_int;

    // Temporary storage for swapping
    logic [ADDR_BITS-1:0]  temp_addr;
    logic [STACK_BITS-1:0] temp_field1;
    logic [STACK_BITS-1:0] temp_field2;

    assign valid = 1'b1;  // Always valid for reference model

    // Stage 1: Initial extraction (RBC format)
    // Format: [stack:chan:bg:ba:row:col]
    always_comb begin
        // Default values
        stack_int    = '0;
        channel_int  = '0;
        bg_int       = '0;
        ba_int       = '0;
        row_int      = '0;
        col_int      = '0;

        // Extract fields in RBC order (bit allocation)
        // RBC: MSB->LSB = [stack:chan:bg:ba:row:col]
        if (ADDR_BITS >= TOTAL_DECODE_BITS) begin
            // Stack bits (MSB portion)
            if (STACK_BITS > 0)
                stack_int   = addr[ADDR_BITS-1 -: STACK_BITS];

            // Channel bits
            if (CHAN_BITS > 0)
                channel_int = addr[ADDR_BITS-1-STACK_BITS -: CHAN_BITS];

            // Bank group bits
            if (BG_BITS > 0)
                bg_int      = addr[ADDR_BITS-1-STACK_BITS-CHAN_BITS -: BG_BITS];

            // Bank bits
            if (BA_BITS > 0)
                ba_int      = addr[ADDR_BITS-1-STACK_BITS-CHAN_BITS-BG_BITS -: BA_BITS];

            // Row bits
            if (ROW_BITS > 0)
                row_int     = addr[TOTAL_DECODE_BITS-1-STACK_BITS-CHAN_BITS-BG_BITS-BA_BITS -: ROW_BITS];

            // Column bits (LSB portion)
            if (COL_BITS > 0)
                col_int     = addr[COL_BITS-1:0];
        end
    end

    // Stage 2: Apply mapping mode transformation
    // This implements the address permutation based on mapping_mode
    always_comb begin
        // Default passthrough
        stack   = stack_int;
        channel = channel_int;
        bank_group = bg_int;
        bank   = ba_int;
        row    = row_int;
        col    = col_int;

        case (mapping_mode)
            MODE_RBC: begin
                // Row-Bank-Column: Default passthrough
                stack   = stack_int;
                channel = channel_int;
                bank_group = bg_int;
                bank   = ba_int;
                row    = row_int;
                col    = col_int;
            end

            MODE_BCR: begin
                // Bank-Column-Row: Swap row and bank fields
                // Row becomes bank, bank becomes row
                stack   = stack_int;
                channel = channel_int;
                bank_group = bg_int;
                bank   = row_int[BA_BITS-1:0];    // Lower bits of row -> bank
                row    = {{(ROW_BITS-BA_BITS){1'b0}}, ba_int};  // bank -> row
                col    = col_int;
            end

            MODE_CRB: begin
                // Column-Row-Bank: Major permutation
                // [stack:chan:bg:ba:row:col] -> [stack:chan:bg:col:row:ba]
                stack        = stack_int;
                channel      = channel_int;
                bank_group   = bg_int;
                bank         = col_int[BA_BITS-1:0];  // Lower col bits -> bank
                row          = row_int;
                col          = {{(COL_BITS-BA_BITS){1'b0}}, ba_int};  // bank -> col
            end

            MODE_BRC: begin
                // Bank-Row-Column: Swap col and bank
                stack   = stack_int;
                channel = channel_int;
                bank_group = bg_int;
                bank   = col_int[BA_BITS-1:0];  // Lower col bits -> bank
                row    = row_int;
                col    = {{(COL_BITS-BA_BITS){1'b0}}, ba_int};  // bank -> col
            end

            MODE_RCB: begin
                // Row-Column-Bank: Major permutation
                // [stack:chan:bg:ba:row:col] -> [stack:chan:bg:col:ba:row]
                stack        = stack_int;
                channel      = channel_int;
                bank_group   = bg_int;
                bank         = col_int[BA_BITS-1:0];
                row          = row_int;
                col          = {{(COL_BITS-BA_BITS){1'b0}}, ba_int};
            end

            MODE_CBR: begin
                // Column-Bank-Row: Swap bank and col
                stack   = stack_int;
                channel = channel_int;
                bank_group = bg_int;
                bank   = row_int[BA_BITS-1:0];
                row    = {{(ROW_BITS-BA_BITS){1'b0}}, ba_int};
                col    = col_int;
            end

            default: begin
                // Default to RBC mapping
                stack   = stack_int;
                channel = channel_int;
                bank_group = bg_int;
                bank   = ba_int;
                row    = row_int;
                col    = col_int;
            end
        endcase
    end

    // Validation checks
    always_comb begin
        // Check for address overflow
        if (ADDR_BITS < TOTAL_DECODE_BITS) begin
            // Warning: address bits may not cover all fields
        end
    end

endmodule


// Testbench wrapper for address decoder verification
module addr_decoder_ref_tb;

    logic [31:0] addr;
    logic [2:0]  mapping_mode;
    logic [2:0]  stack;
    logic [2:0]  channel;
    logic [1:0]  bank_group;
    logic [1:0]  bank;
    logic [15:0] row;
    logic [9:0]  col;
    logic        valid;

    addr_decoder_ref #(
        .ADDR_BITS(32),
        .STACK_BITS(3),
        .CHAN_BITS(3),
        .BG_BITS(2),
        .BA_BITS(2),
        .ROW_BITS(16),
        .COL_BITS(10)
    ) dut (.*);

    initial begin
        $display("Address Decoder Reference Model Test");
        $display("=====================================");

        // Test all mapping modes
        for (int mode = 0; mode < 6; mode++) begin
            mapping_mode = mode[2:0];
            $display("\nMapping Mode: %0d", mode);

            addr = 32'h12345678;
            #10;
            $display("Input: 0x%08x", addr);
            $display("Output: stack=%b, chan=%b, bg=%b, ba=%b, row=0x%04x, col=%b",
                     stack, channel, bank_group, bank, row, col);
        end

        $display("\nTest complete");
        $finish;
    end

endmodule