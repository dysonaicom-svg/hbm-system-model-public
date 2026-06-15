// =============================================================================
// HBM Controller RTL - JXTF Project
// Implements FR-FCFS scheduling with address decoding for HBM memory
// =============================================================================

`timescale 1ns / 1ps

// verilator lint_off WIDTHEXPAND
// verilator lint_off SELRANGE
// verilator lint_off WIDTHTRUNC
// verilator lint_off UNUSEDSIGNAL
// verilator lint_off UNUSEDPARAM
// verilator lint_off LATCH
// verilator lint_off MISINDENT
// verilator lint_off EOFNEWLINE

module hbm_controller #(
    parameter QUEUE_DEPTH       = 32,
    parameter STACK_ADDR_WIDTH = 8,   // Stack selection (1-8 stacks)
    parameter CH_ADDR_WIDTH    = 2,   // Channel within stack (1-4 channels)
    parameter BG_ADDR_WIDTH    = 2,   // Bank group
    parameter BK_ADDR_WIDTH    = 3,   // Bank
    parameter ROW_ADDR_WIDTH   = 16,  // Row address
    parameter COL_ADDR_WIDTH   = 6,   // Column address (byte address within burst)
    parameter ADDR_WIDTH       = STACK_ADDR_WIDTH + CH_ADDR_WIDTH + BG_ADDR_WIDTH +
                                 BK_ADDR_WIDTH + ROW_ADDR_WIDTH + COL_ADDR_WIDTH
)(
    input  logic                          clk,
    input  logic                          rst_n,

    // Request interface
    input  logic                          req_valid,
    input  logic [31:0]                   req_id,
    input  logic [ADDR_WIDTH-1:0]         req_addr,
    input  logic                          req_rd_wr_n,  // 0=write, 1=read
    input  logic [15:0]                  req_len,
    input  logic [2:0]                    req_priority,
    output logic                          req_ready,

    // Response interface
    output logic                          resp_valid,
    output logic [31:0]                   resp_id,
    output logic                          resp_success,
    output logic [7:0]                    resp_status,

    // DRAM interface
    output logic [3:0]                   dram_cmd,
    output logic [STACK_ADDR_WIDTH-1:0]  dram_ch,
    output logic [BK_ADDR_WIDTH-1:0]      dram_bank,
    output logic [ROW_ADDR_WIDTH-1:0]     dram_row,
    input  logic [255:0]                 dram_rd_data,
    output logic [255:0]                 dram_wr_data,

    // Statistics
    output logic [31:0]                 stat_requests,
    output logic [31:0]                 stat_completed,
    output logic [7:0]                   stat_hit_rate
);

    // =============================================================================
    // Address Decoder
    // =============================================================================
    localparam COL_LSB_WIDTH = 3;  // 8-byte granularity for 256-bit bus

    logic [STACK_ADDR_WIDTH-1:0]  dec_stack;
    logic [CH_ADDR_WIDTH-1:0]     dec_ch;
    logic [BG_ADDR_WIDTH-1:0]     dec_bg;
    logic [BK_ADDR_WIDTH-1:0]     dec_bank;
    logic [ROW_ADDR_WIDTH-1:0]    dec_row;
    logic [COL_ADDR_WIDTH-1:0]    dec_col;

    always_comb begin
        dec_col   = req_addr[COL_ADDR_WIDTH-1:0];
        dec_row   = req_addr[ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:COL_ADDR_WIDTH];
        dec_bank  = req_addr[BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                           ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
        dec_bg    = req_addr[BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                           BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
        dec_ch    = req_addr[CH_ADDR_WIDTH+BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                           BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
        dec_stack = req_addr[ADDR_WIDTH-1:CH_ADDR_WIDTH+BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
    end

    // =============================================================================
    // Request Queue Entry
    // =============================================================================
    typedef struct packed {
        logic                   valid;
        logic [31:0]            id;
        logic [ADDR_WIDTH-1:0]  addr;
        logic                   rd_wr_n;
        logic [15:0]            len;
        logic [2:0]             req_priority;
        logic                   open_row;     // Row buffer open flag
        logic [BK_ADDR_WIDTH-1:0]  open_bank; // Currently open bank
        logic [ROW_ADDR_WIDTH-1:0] open_row_addr; // Currently open row
        logic [CH_ADDR_WIDTH-1:0]  open_ch;   // Currently open channel
        logic [STACK_ADDR_WIDTH-1:0] open_stack; // Currently open stack
        logic [7:0]             age;         // Age counter for FIFO tiebreak
        logic [3:0]             state;        // Request state
    } req_entry_t;

    // =============================================================================
    // Request Queue
    // =============================================================================
    req_entry_t [QUEUE_DEPTH-1:0] queue;
    logic [$clog2(QUEUE_DEPTH)-1:0] enq_ptr;
    logic [$clog2(QUEUE_DEPTH)-1:0] deq_ptr;
    logic [$clog2(QUEUE_DEPTH)-1:0] queue_count;
    logic [7:0] age_counter;

    wire queue_full  = (queue_count == QUEUE_DEPTH);
    wire queue_empty = (queue_count == 0);

    // Queue count tracking
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            queue_count <= 0;
            enq_ptr <= 0;
            deq_ptr <= 0;
            age_counter <= 0;
        end else begin
            // Increment age counter periodically
            if (age_counter == 8'hFF)
                age_counter <= 0;
            else
                age_counter <= age_counter + 1;

            // Track queue entries
            if (req_valid && req_ready && !queue_empty) begin
                if (queue_count < QUEUE_DEPTH)
                    queue_count <= queue_count + 1;
            end
            if (grant_valid && !queue_empty) begin
                if (queue_count > 0)
                    queue_count <= queue_count - 1;
                deq_ptr <= deq_ptr + 1;
            end
            if (req_valid && req_ready && grant_valid) begin
                // simultaneous enq and deq
            end else if (req_valid && req_ready) begin
                enq_ptr <= enq_ptr + 1;
            end else if (grant_valid && !queue_empty) begin
                deq_ptr <= deq_ptr + 1;
            end
        end
    end

    assign req_ready = !queue_full;

    // Enqueue new request
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < QUEUE_DEPTH; i++) begin
                queue[i].valid <= 0;
            end
        end else begin
            if (req_valid && req_ready) begin
                queue[enq_ptr].valid         <= 1;
                queue[enq_ptr].id            <= req_id;
                queue[enq_ptr].addr          <= req_addr;
                queue[enq_ptr].rd_wr_n       <= req_rd_wr_n;
                queue[enq_ptr].len           <= req_len;
                queue[enq_ptr].req_priority      <= req_priority;
                queue[enq_ptr].age           <= age_counter;
                queue[enq_ptr].state         <= 4'd0;  // Queued
                // Check if same channel/bank/row is already open
                queue[enq_ptr].open_ch     <= dec_ch;
                queue[enq_ptr].open_bank   <= dec_bank;
                queue[enq_ptr].open_row_addr <= dec_row;
                queue[enq_ptr].open_stack   <= dec_stack;
                queue[enq_ptr].open_row      <=
                    (dec_bank == open_bank_reg[get_ch_idx(dec_ch)]) &&
                    (dec_row == open_row_reg[get_ch_idx(dec_ch)]) &&
                    row_open[get_ch_idx(dec_ch)];
            end
        end
    end

    // =============================================================================
    // Row Buffer State (per channel/bank)
    // =============================================================================
    localparam NUM_CHANNELS = 8;  // Maximum channels
    localparam CH_IDX_WIDTH = $clog2(NUM_CHANNELS);

    logic [NUM_CHANNELS-1:0][3:0] row_open;           // Per channel row open
    logic [NUM_CHANNELS-1:0][BK_ADDR_WIDTH-1:0] open_bank_reg;
    logic [NUM_CHANNELS-1:0][ROW_ADDR_WIDTH-1:0] open_row_reg;  // Fixed: ROW not BANK

    function logic [CH_IDX_WIDTH-1:0] get_ch_idx(input logic [CH_ADDR_WIDTH-1:0] ch);
        return ch[CH_IDX_WIDTH-1:0];
    endfunction

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            row_open      <= '0;
            open_bank_reg <= '0;
            open_row_reg  <= '0;
        end else begin
            if (dram_cmd == 4'd1) begin  // ACTIVATE
                open_bank_reg[get_ch_idx(dec_ch)] <= dec_bank;
                open_row_reg[get_ch_idx(dec_ch)]  <= dec_row;
                row_open[get_ch_idx(dec_ch)]      <= 1;
            end else if (dram_cmd == 4'd4) begin  // PRECHARGE
                if (dec_bank == open_bank_reg[get_ch_idx(dec_ch)])
                    row_open[get_ch_idx(dec_ch)] <= 0;
            end
        end
    end

    // =============================================================================
    // FR-FCFS Scheduler
    // =============================================================================
    logic [$clog2(QUEUE_DEPTH)-1:0] best_idx;
    logic [2:0] best_priority;
    logic [7:0] best_age;
    logic best_row_hit;
    logic grant_valid;

    always_comb begin
        // Default assignments to avoid latches
        best_idx = 0;
        best_priority = 0;
        best_age = 0;
        best_row_hit = 0;
        grant_valid = 0;

        for (int i = 0; i < QUEUE_DEPTH; i++) begin
            if (queue[i].valid) begin
                logic row_hit;
                logic [CH_ADDR_WIDTH-1:0]  q_ch;
                logic [BK_ADDR_WIDTH-1:0]  q_bank;
                logic [ROW_ADDR_WIDTH-1:0] q_row;
                logic [STACK_ADDR_WIDTH-1:0] q_stack;

                q_ch    = queue[i].addr[CH_ADDR_WIDTH+BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                                BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
                q_bank  = queue[i].addr[BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                                ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
                q_row   = queue[i].addr[ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                                COL_ADDR_WIDTH];
                q_stack = queue[i].addr[ADDR_WIDTH-1:CH_ADDR_WIDTH+BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];

                row_hit = row_open[get_ch_idx(q_ch)] &&
                          (q_bank == open_bank_reg[get_ch_idx(q_ch)]) &&
                          (q_row  == open_row_reg[get_ch_idx(q_ch)]) &&
                          (q_stack == dec_stack);  // Simplified - should track per stack

                // Selection criteria: row_hit > priority > age (older wins)
                if (!grant_valid) begin
                    best_idx = i[$clog2(QUEUE_DEPTH)-1:0];
                    best_priority = queue[i].req_priority;
                    best_age = queue[i].age;
                    best_row_hit = row_hit;
                    grant_valid = 1;
                end else if (row_hit && !best_row_hit) begin
                    best_idx = i[$clog2(QUEUE_DEPTH)-1:0];
                    best_priority = queue[i].req_priority;
                    best_age = queue[i].age;
                    best_row_hit = row_hit;
                end else if (row_hit && best_row_hit) begin
                    if (queue[i].req_priority > best_priority) begin
                        best_idx = i[$clog2(QUEUE_DEPTH)-1:0];
                        best_priority = queue[i].req_priority;
                        best_age = queue[i].age;
                    end else if (queue[i].req_priority == best_priority) begin
                        if (queue[i].age < best_age) begin
                            best_idx = i[$clog2(QUEUE_DEPTH)-1:0];
                            best_age = queue[i].age;
                        end
                    end
                end else if (!row_hit && !best_row_hit) begin
                    if (queue[i].req_priority > best_priority) begin
                        best_idx = i[$clog2(QUEUE_DEPTH)-1:0];
                        best_priority = queue[i].req_priority;
                        best_age = queue[i].age;
                    end else if (queue[i].req_priority == best_priority) begin
                        if (queue[i].age < best_age) begin
                            best_idx = i[$clog2(QUEUE_DEPTH)-1:0];
                            best_age = queue[i].age;
                        end
                    end
                end
            end
        end
    end

    // Registered grant for timing
    logic [$clog2(QUEUE_DEPTH)-1:0] grant_idx;
    logic grant_row_hit;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant_idx <= 0;
            grant_row_hit <= 0;
        end else begin
            if (grant_valid)
                grant_idx <= best_idx;
                grant_row_hit <= best_row_hit;
        end
    end

    // =============================================================================
    // DRAM Command Generator FSM
    // =============================================================================
    typedef enum logic [3:0] {
        IDLE       = 4'd0,
        ACTIVATE   = 4'd1,
        READ       = 4'd2,
        WRITE      = 4'd3,
        PRECHARGE  = 4'd4,
        COMPLETE   = 4'd5,
        READ_WF    = 4'd6,
        WRITE_WF   = 4'd7
    } dram_state_t;

    dram_state_t state, next_state;

    // FSM state register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    // FSM next state logic
    always_comb begin
        next_state = state;

        case (state)
            IDLE: begin
                if (grant_valid && fsm_ready)
                    next_state = grant_row_hit ? READ : ACTIVATE;
            end

            ACTIVATE: begin
                next_state = READ;
            end

            READ: begin
                next_state = READ_WF;
            end

            READ_WF: begin
                next_state = PRECHARGE;
            end

            WRITE: begin
                next_state = WRITE_WF;
            end

            WRITE_WF: begin
                next_state = PRECHARGE;
            end

            PRECHARGE: begin
                next_state = COMPLETE;
            end

            COMPLETE: begin
                next_state = IDLE;
            end

            default: next_state = IDLE;
        endcase
    end

    // FSM control signals
    logic fsm_ready;
    logic do_activate;
    logic do_read;
    logic do_write;
    logic do_precharge;

    assign fsm_ready = (state == IDLE);
    assign do_activate = (state == ACTIVATE);
    assign do_read = (state == READ);
    assign do_write = (state == WRITE);
    assign do_precharge = (state == PRECHARGE);

    // =============================================================================
    // DRAM Command Output
    // =============================================================================
    logic [31:0] cur_id;
    logic cur_rd_wr_n;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dram_cmd <= 4'd0;
            cur_id <= 0;
            cur_rd_wr_n <= 1;
        end else begin
            dram_cmd <= 4'd0;

            if (do_activate) begin
                dram_cmd <= 4'd1;  // ACT
                cur_id <= queue[grant_idx].id;
                cur_rd_wr_n <= queue[grant_idx].rd_wr_n;
            end else if (do_read) begin
                dram_cmd <= 4'd2;  // RD
            end else if (do_write) begin
                dram_cmd <= 4'd3;  // WR
            end else if (do_precharge) begin
                dram_cmd <= 4'd4;  // PRE
            end
        end
    end

    // DRAM address outputs
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dram_ch   <= '0;
            dram_bank <= '0;
            dram_row  <= '0;
        end else begin
            if (grant_valid && fsm_ready) begin
                dram_ch   <= dec_ch;
                dram_bank <= dec_bank;
                dram_row  <= dec_row;
            end
        end
    end

    // Write data assignment
    always_ff @(posedge clk) begin
        if (do_write)
            dram_wr_data <= 256'hDEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF;
    end

    // =============================================================================
    // Response Generation
    // =============================================================================
    logic [31:0] resp_id_q;
    logic resp_success_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            resp_valid <= 0;
            resp_id_q <= 0;
            resp_success_q <= 0;
            resp_status <= 0;
        end else begin
            resp_valid <= 0;
            if (state == COMPLETE) begin
                resp_valid <= 1;
                resp_id_q <= cur_id;
                resp_success_q <= 1;
                resp_status <= 8'd0;  // Success
            end
            resp_id <= resp_id_q;
            resp_success <= resp_success_q;
        end
    end

    // =============================================================================
    // Statistics Counters
    // =============================================================================
    logic [31:0] requests_q;
    logic [31:0] completed_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            requests_q <= 0;
            completed_q <= 0;
        end else begin
            if (req_valid && req_ready)
                requests_q <= requests_q + 1;
            if (resp_valid)
                completed_q <= completed_q + 1;

            stat_requests <= requests_q;
            stat_completed <= completed_q;

            // Calculate hit rate (percentage)
            if (requests_q > 0)
                stat_hit_rate <= (completed_q * 100) / requests_q;
            else
                stat_hit_rate <= 0;
        end
    end

    // =============================================================================
    // Queue Entry Cleanup on Grant
    // =============================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < QUEUE_DEPTH; i++) begin
                queue[i].valid <= 0;
            end
        end else begin
            if (grant_valid && fsm_ready && state == IDLE)
                queue[grant_idx].valid <= 0;
        end
    end

endmodule
// verilator lint_on WIDTHEXPAND
// verilator lint_on SELRANGE
// verilator lint_on WIDTHTRUNC
// verilator lint_on UNUSEDSIGNAL
// verilator lint_on UNUSEDPARAM
// verilator lint_on LATCH
// verilator lint_on MISINDENT
// verilator lint_on EOFNEWLINE
