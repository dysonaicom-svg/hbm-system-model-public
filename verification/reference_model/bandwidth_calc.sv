// bandwidth_calc.sv - HBM Real-time Bandwidth Calculator
// Simplified version using integer arithmetic for Verilator compatibility

`timescale 1ps / 1ps
// verilator lint_off WIDTHEXPAND
// verilator lint_off BLKANDNBLK

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

    // Constants (scaled for integer arithmetic)
    // MAX_BW in Gbps * 1000 for mGbps precision
    localparam int MAX_BW_MGPS = int'(REAL_CLK_FREQ * real'(BUS_WIDTH) / 1.0e6);  // Theoretical max in Mbps

    // Internal counters
    logic [COUNTER_WIDTH-1:0] total_bytes_window;
    logic [31:0]             total_bytes_accum;
    logic [31:0]             transaction_count;
    logic [31:0]             window_index;
    logic [31:0]             cycles_in_window;

    // Peak tracking
    logic [COUNTER_WIDTH-1:0] peak_bytes_window;
    logic [31:0]             peak_bandwidth_calc;

    // Bandwidth calculation (integer, mbps units)
    logic [31:0] current_bw_mbps;
    logic [31:0] current_efficiency;

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
            peak_bandwidth_calc <= '0;
            current_bw_mbps <= '0;
            current_efficiency <= '0;
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
                end

                // Calculate bandwidth every cycle
                if (cycles_in_window > 0) begin
                    // Bandwidth = (bytes * 8 * freq) / (cycles * 1e9) in Gbps
                    // Using fixed point: (bytes * 8 * freq) / cycles / 1e9
                    // In mbps: (bytes * 8 * freq) / cycles / 1e6
                    int tmp_bw;
                    tmp_bw = int'(total_bytes_window) * 8 * int'(REAL_CLK_FREQ / 1.0e6) / int'(cycles_in_window);

                    current_bw_mbps <= tmp_bw;
                    current_efficiency <= (MAX_BW_MGPS > 0) ? (tmp_bw * 100) / MAX_BW_MGPS : 0;

                    // Track peak
                    if (tmp_bw > peak_bandwidth_calc) begin
                        peak_bandwidth_calc <= tmp_bw;
                    end
                end
            end
        end
    end

    // Output assignment
    assign bandwidth_gbps = current_bw_mbps / 1000;  // Convert mbps to gbps
    assign efficiency_pct = current_efficiency;
    assign peak_bandwidth_gbps = peak_bandwidth_calc / 1000;
    assign avg_bandwidth_gbps = (transaction_count > 0) ? (int'(total_bytes_accum) * 8 * int'(REAL_CLK_FREQ / 1.0e6) / (transaction_count * 1000)) : 0;
    assign window_count = window_index;
    assign total_transactions = transaction_count;

endmodule