// bandwidth_calc.sv - HBM Real-time Bandwidth Calculator
// Calculates bandwidth and efficiency using sliding window method

`timescale 1ps / 1ps

module bandwidth_calc #(
    parameter int   WINDOW_SIZE   = 1000,      // Sliding window size in cycles
    parameter real  REAL_CLK_FREQ = 1.28e9,    // 1.28 GHz real clock frequency
    parameter int   BUS_WIDTH     = 1024,      // 1024-bit data bus
    parameter int   COUNTER_WIDTH = 64        // Counter width for large values
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        enable,

    // Transaction input
    input  logic        trans_valid,
    input  logic [3:0]  trans_type,   // 0=idle, 1=read, 2=write, 3=ACT, 4=PRE, etc.
    input  logic [31:0] trans_bytes,

    // Bandwidth outputs
    output logic [31:0] bandwidth_gbps,
    output logic [31:0] efficiency_pct,

    // Detailed statistics
    output logic [31:0] peak_bandwidth_gbps,
    output logic [31:0] avg_bandwidth_gbps,
    output logic [31:0] window_count,
    output logic [31:0] total_transactions
);

    // Constants
    localparam real MAX_BANDWIDTH = REAL_CLK_FREQ * BUS_WIDTH / 1e9;  // Theoretical max GB/s

    // Internal counters
    logic [COUNTER_WIDTH-1:0] total_bytes_window;
    logic [31:0]             total_bytes_accum;
    logic [31:0]             transaction_count;
    logic [31:0]             window_index;
    logic [31:0]             cycles_in_window;

    // Sliding window ring buffer
    logic [COUNTER_WIDTH-1:0] window_buffer[WINDOW_SIZE];
    logic [31:0]             window_head;
    logic [31:0]             window_tail;

    // Peak tracking
    logic [COUNTER_WIDTH-1:0] peak_bytes_window;
    logic [31:0]             peak_bandwidth_calc;

    // Intermediate calculations
    real                      bandwidth_calc;
    real                      efficiency_calc;

    // Initialize
    initial begin
        for (int i = 0; i < WINDOW_SIZE; i++) begin
            window_buffer[i] = '0;
        end
        window_head = '0;
        window_tail = '0;
        total_bytes_window = '0;
        total_bytes_accum = '0;
        transaction_count = '0;
        window_index = '0;
        cycles_in_window = '0;
        peak_bytes_window = '0;
    end

    // Main bandwidth calculation logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all counters
            total_bytes_window <= '0;
            total_bytes_accum <= '0;
            transaction_count <= '0;
            window_index <= '0;
            cycles_in_window <= '0;
            peak_bytes_window <= '0;
            window_head <= '0;
            window_tail <= '0;

            for (int i = 0; i < WINDOW_SIZE; i++) begin
                window_buffer[i] <= '0;
            end

            bandwidth_calc <= 0.0;
            efficiency_calc <= 0.0;
        end else begin
            if (enable) begin
                // Increment cycle counter
                cycles_in_window <= cycles_in_window + 1;

                // Process transaction if valid
                if (trans_valid) begin
                    transaction_count <= transaction_count + 1;
                    total_bytes_accum <= total_bytes_accum + trans_bytes;

                    // Add to sliding window
                    total_bytes_window <= total_bytes_window + trans_bytes;
                    window_buffer[window_head[WINDOW_SIZE-1:0]] <= trans_bytes;
                    window_head <= window_head + 1;

                    // Check if window is full
                    if (cycles_in_window >= WINDOW_SIZE) begin
                        // Remove oldest entry from window
                        total_bytes_window <= total_bytes_window - window_buffer[window_tail[WINDOW_SIZE-1:0]];
                        window_tail <= window_tail + 1;
                        window_index <= window_index + 1;
                    end
                end

                // Calculate bandwidth every cycle
                if (cycles_in_window > 0) begin
                    // Bandwidth = (bytes * 8 * clock_freq) / (window_cycles * 1e9)
                    bandwidth_calc = real'(total_bytes_window) * 8.0 * REAL_CLK_FREQ /
                                    (real'(cycles_in_window) * 1.0e9);

                    // Efficiency = actual_bandwidth / theoretical_max * 100
                    efficiency_calc = (bandwidth_calc / MAX_BANDWIDTH) * 100.0;

                    // Track peak
                    if (total_bytes_window > peak_bytes_window) begin
                        peak_bytes_window <= total_bytes_window;
                        peak_bandwidth_calc <= real'(bandwidth_calc);
                    end
                end else begin
                    bandwidth_calc = 0.0;
                    efficiency_calc = 0.0;
                end
            end else begin
                bandwidth_calc = 0.0;
                efficiency_calc = 0.0;
            end
        end
    end

    // Output assignment with rounding
    always_comb begin
        bandwidth_gbps = logic [31:0](bandwidth_calc * 1000.0 + 0.5) / 1000;  // Convert to Gbps with scaling
        efficiency_pct = logic [31:0](efficiency_calc * 100.0 + 0.5) / 100;
        peak_bandwidth_gbps = logic [31:0](peak_bandwidth_calc * 1000.0 + 0.5) / 1000;

        // Average bandwidth calculation
        if (transaction_count > 0) begin
            avg_bandwidth_gbps = logic [31:0](real'(total_bytes_accum) * 8.0 * REAL_CLK_FREQ /
                                              (real'(window_index + WINDOW_SIZE) * 1.0e9) * 1000.0 + 0.5) / 1000;
        end else begin
            avg_bandwidth_gbps = 0;
        end

        window_count = window_index;
        total_transactions = transaction_count;
    end

    // Utility function for immediate bandwidth query
    function real get_instantaneous_bw(input logic [COUNTER_WIDTH-1:0] bytes, input int cycles);
        if (cycles == 0) return 0.0;
        return real'(bytes) * 8.0 * REAL_CLK_FREQ / (real'(cycles) * 1.0e9);
    endfunction

endmodule


// Simplified bandwidth monitor with ready/valid handshake
module bandwidth_monitor #(
    parameter real REAL_CLK_FREQ = 1.28e9,
    parameter int BUS_WIDTH = 1024
) (
    input  logic        clk,
    input  logic        rst_n,

    // Streaming interface
    input  logic        s_valid,
    input  logic [127:0] s_data,
    output logic        s_ready,

    // Statistics interface
    output logic [31:0] current_bw_gbps,
    output logic [31:0] efficiency_pct,
    output logic [63:0] total_bytes_transferred
);

    localparam real MAX_BW = REAL_CLK_FREQ * BUS_WIDTH / 1e9;

    logic [63:0] byte_counter;
    logic [31:0] cycle_counter;
    logic [31:0] bw_calc;
    logic [31:0] eff_calc;

    assign s_ready = 1'b1;
    assign total_bytes_transferred = byte_counter;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            byte_counter <= '0;
            cycle_counter <= '0;
        end else begin
            cycle_counter <= cycle_counter + 1;

            if (s_valid) begin
                byte_counter <= byte_counter + (s_data[7:0] != 0 ? 128/8 : 0);
            end

            // Calculate bandwidth
            if (cycle_counter > 0) begin
                bw_calc <= real'(byte_counter) * 8.0 * REAL_CLK_FREQ / (real'(cycle_counter) * 1.0e12);
                eff_calc <= real'(byte_counter) * 800.0 / (real'(cycle_counter) * MAX_BW);
            end
        end
    end

    assign current_bw_gbps = bw_calc;
    assign efficiency_pct = eff_calc;

endmodule