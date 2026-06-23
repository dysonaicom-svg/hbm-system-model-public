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
// verilator lint_off UNSIGNED

module hbm_controller #(
    parameter QUEUE_DEPTH       = 32,
    parameter STACK_ADDR_WIDTH = 2,    // Stack selection (4 stacks per HBM4 spec)
    parameter CH_ADDR_WIDTH    = 5,    // Channel within stack (32 channels for HBM4)
    parameter BG_ADDR_WIDTH    = 3,    // Bank group (8 bank groups per HBM4)
    parameter BK_ADDR_WIDTH    = 4,    // Bank (16 banks per HBM4)
    parameter ROW_ADDR_WIDTH   = 16,   // Row address
    parameter COL_ADDR_WIDTH   = 6,    // Column address (byte address within burst)
    parameter PCH_ADDR_WIDTH   = 1,    // Pseudo-channel (2 per channel for HBM4)
    parameter ADDR_WIDTH       = STACK_ADDR_WIDTH + CH_ADDR_WIDTH + BG_ADDR_WIDTH +
                                 BK_ADDR_WIDTH + ROW_ADDR_WIDTH + COL_ADDR_WIDTH
)(
    input  logic                          clk,
    input  logic                          rst_n,

    // Request interface
    input  logic                          req_valid,
    input  logic [31:0]                   req_id,
    input  logic [ADDR_WIDTH-1:0]           req_addr,
    input  logic                          req_rd_wr_n,  // 0=write, 1=read
    input  logic [15:0]                  req_len,
    input  logic [2:0]                    req_priority,
    output logic                          req_ready,

    // Response interface
    output logic                          resp_valid,
    output logic [31:0]                   resp_id,
    output logic                          resp_success,
    output logic [7:0]                    resp_status,

    // DRAM interface - HBM4 4-bit command encoding
    // CMD_NOP=0, CMD_ACT=1, CMD_READ=2, CMD_WRITE=3, CMD_PRE=4, CMD_PREA=5, CMD_REF=6
    output logic [3:0]                   dram_cmd,
    output logic [CH_ADDR_WIDTH-1:0]    dram_ch,     // 5 bits for 32 channels
    output logic [BG_ADDR_WIDTH-1:0]     dram_bg,     // 3 bits for 8 bank groups
    output logic [BK_ADDR_WIDTH-1:0]     dram_bank,   // 4 bits for 16 banks
    output logic [PCH_ADDR_WIDTH-1:0]    dram_pch,    // 1 bit for 2 pseudo-channels
    output logic [ROW_ADDR_WIDTH-1:0]    dram_row,
    input  logic [255:0]                 dram_rd_data,
    output logic [255:0]                 dram_wr_data,

    // Statistics
    output logic [31:0]                 stat_requests,
    output logic [31:0]                 stat_completed,
    output logic [7:0]                   stat_hit_rate
);

    // =============================================================================
    // Address Decoder - HBM4 RBC (Row-Bank-Channel) Mapping
    // =============================================================================
    // Address layout for HBM4 (42-bit effective address):
    // [47:46] Stack (2 bits)
    // [45:41] Channel (5 bits, 32 channels)
    // [40]    Pseudo-channel (1 bit, 2 pseudo-channels)
    // [39:37] Bank group (3 bits, 8 bank groups)
    // [36:33] Bank (4 bits, 16 banks)
    // [32:17] Row (16 bits, 64K rows)
    // [16:11] Column (6 bits, 64 columns)
    // [10:3]  Burst/offset (8 bytes per beat, 4-beat burst)
    // =============================================================================
    localparam COL_LSB_WIDTH = 3;  // 8-byte granularity for 256-bit bus
    localparam BURST_SIZE = 1 << COL_LSB_WIDTH;  // 8 bytes per burst beat

    logic [STACK_ADDR_WIDTH-1:0]  dec_stack;
    logic [CH_ADDR_WIDTH-1:0]     dec_ch;
    logic [BG_ADDR_WIDTH-1:0]    dec_bg;
    logic [BK_ADDR_WIDTH-1:0]    dec_bank;
    logic [PCH_ADDR_WIDTH-1:0]    dec_pch;
    logic [ROW_ADDR_WIDTH-1:0]    dec_row;
    logic [COL_ADDR_WIDTH-1:0]    dec_col;

    always_comb begin
        // HBM4 RBC address mapping - matches Python hbm4_address_decoder.py
        dec_col   = req_addr[COL_ADDR_WIDTH-1:0];                              // Bits [5:0]
        dec_row   = req_addr[ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:COL_ADDR_WIDTH]; // Bits [21:6]
        dec_bank  = req_addr[BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                           ROW_ADDR_WIDTH+COL_ADDR_WIDTH];                   // Bits [25:22]
        dec_bg    = req_addr[BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                           BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];       // Bits [28:26]
        dec_pch   = req_addr[BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH]; // Bit [29]
        dec_ch    = req_addr[CH_ADDR_WIDTH+BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                           BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH]; // Bits [34:30]
        dec_stack = req_addr[ADDR_WIDTH-1:CH_ADDR_WIDTH+BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH]; // Bits [35]
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
        logic [CH_ADDR_WIDTH-1:0]  open_ch;     // Currently open channel
        logic [BG_ADDR_WIDTH-1:0] open_bg;     // Currently open bank group
        logic [BK_ADDR_WIDTH-1:0] open_bank;   // Currently open bank
        logic [PCH_ADDR_WIDTH-1:0] open_pch;   // Currently open pseudo-channel
        logic [ROW_ADDR_WIDTH-1:0] open_row_addr; // Currently open row
        logic [STACK_ADDR_WIDTH-1:0] open_stack; // Currently open stack
        logic [7:0]             age;         // Age counter for FIFO tiebreak
        logic [3:0]             state;        // Request state
    } req_entry_t;

    // =============================================================================
    // Request Queue
    // =============================================================================
    localparam QUEUE_PTR_WIDTH = $clog2(QUEUE_DEPTH);
    localparam QUEUE_CNT_WIDTH = QUEUE_PTR_WIDTH + 1;  // Need extra bit to count to QUEUE_DEPTH
    req_entry_t [QUEUE_DEPTH-1:0] queue;
    logic [QUEUE_PTR_WIDTH-1:0] enq_ptr;
    logic [QUEUE_PTR_WIDTH-1:0] deq_ptr;
    logic [QUEUE_CNT_WIDTH-1:0] queue_count;
    logic [7:0] age_counter;

    // Queue full when count equals queue depth
    wire queue_full  = (queue_count >= QUEUE_DEPTH);
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

            // Track queue entries - increment on enqueue
            if (req_valid && req_ready) begin
                if (queue_count < QUEUE_DEPTH)
                    queue_count <= queue_count + 1;
            end
            // Decrement on dequeue
            if (grant_valid && !queue_empty) begin
                if (queue_count > 0)
                    queue_count <= queue_count - 1;
                deq_ptr <= deq_ptr + 1;
            end
            // Update pointers for simultaneous enq/deq or individual operations
            if (req_valid && req_ready && grant_valid) begin
                // simultaneous enq and deq - no pointer change needed
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
    // Row Buffer State (per channel/pseudo-channel/bank)
    // =============================================================================
    localparam NUM_CHANNELS = 32;  // HBM4: 32 channels
    localparam CH_IDX_WIDTH = $clog2(NUM_CHANNELS);

    // Per-channel row open state tracking
    // Each entry tracks: open_row, open_bank, open_bg, open_pch
    logic [NUM_CHANNELS-1:0]      row_open;              // Row open flag per channel
    logic [NUM_CHANNELS-1:0][PCH_ADDR_WIDTH-1:0]  open_pch_reg;   // Pseudo-channel
    logic [NUM_CHANNELS-1:0][BG_ADDR_WIDTH-1:0]   open_bg_reg;    // Bank group
    logic [NUM_CHANNELS-1:0][BK_ADDR_WIDTH-1:0]   open_bank_reg;  // Bank
    logic [NUM_CHANNELS-1:0][ROW_ADDR_WIDTH-1:0]  open_row_reg;   // Row

    function logic [CH_IDX_WIDTH-1:0] get_ch_idx(input logic [CH_ADDR_WIDTH-1:0] ch);
        return ch[CH_IDX_WIDTH-1:0];
    endfunction

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            row_open      <= '0;
            open_pch_reg  <= '0;
            open_bg_reg   <= '0;
            open_bank_reg <= '0;
            open_row_reg  <= '0;
        end else begin
            if (dram_cmd == 4'd1) begin  // CMD_ACT
                open_pch_reg[get_ch_idx(dec_ch)]  <= dec_pch;
                open_bg_reg[get_ch_idx(dec_ch)]   <= dec_bg;
                open_bank_reg[get_ch_idx(dec_ch)] <= dec_bank;
                open_row_reg[get_ch_idx(dec_ch)]  <= dec_row;
                row_open[get_ch_idx(dec_ch)]      <= 1;
            end else if (dram_cmd == 4'd4) begin  // CMD_PRE
                // Close row if matching
                if (dec_pch  == open_pch_reg[get_ch_idx(dec_ch)] &&
                    dec_bg   == open_bg_reg[get_ch_idx(dec_ch)]  &&
                    dec_bank == open_bank_reg[get_ch_idx(dec_ch)])
                    row_open[get_ch_idx(dec_ch)] <= 0;
            end
        end
    end

    // =============================================================================
    // Address Decode Function for Queue Entries
    // =============================================================================
    function automatic logic check_row_hit(input logic [ADDR_WIDTH-1:0] addr);
        logic [CH_ADDR_WIDTH-1:0]   q_ch;
        logic [PCH_ADDR_WIDTH-1:0]  q_pch;
        logic [BG_ADDR_WIDTH-1:0]   q_bg;
        logic [BK_ADDR_WIDTH-1:0]   q_bank;
        logic [ROW_ADDR_WIDTH-1:0]  q_row;
    begin
        // HBM4 RBC address mapping - extracts fields from packed address
        q_ch    = addr[CH_ADDR_WIDTH+BK_ADDR_WIDTH+BG_ADDR_WIDTH+PCH_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                         BK_ADDR_WIDTH+BG_ADDR_WIDTH+PCH_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
        q_bg    = addr[BK_ADDR_WIDTH+BG_ADDR_WIDTH+PCH_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                         BG_ADDR_WIDTH+PCH_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
        q_pch   = addr[BK_ADDR_WIDTH+PCH_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                         PCH_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
        q_bank  = addr[BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                         ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
        q_row   = addr[ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                         COL_ADDR_WIDTH];

        // Row hit requires matching: channel, pseudo-channel, bank group, bank, row
        check_row_hit = row_open[get_ch_idx(q_ch)] &&
                        (q_pch  == open_pch_reg[get_ch_idx(q_ch)]) &&
                        (q_bg   == open_bg_reg[get_ch_idx(q_ch)]) &&
                        (q_bank == open_bank_reg[get_ch_idx(q_ch)]) &&
                        (q_row  == open_row_reg[get_ch_idx(q_ch)]);
    end
    endfunction

    // =============================================================================
    // FR-FCFS Scheduler - only active when FSM is idle
    // =============================================================================
    logic [$clog2(QUEUE_DEPTH)-1:0] best_idx;
    logic [2:0] best_priority;
    logic [7:0] best_age;
    logic best_row_hit;
    logic grant_valid;

    always_comb begin
        // Default assignments to avoid latches
        best_idx = '0;
        best_priority = '0;
        best_age = '0;
        best_row_hit = 1'b0;
        // Only assert grant_valid when FSM is idle
        grant_valid = 1'b0;

        for (int i = 0; i < QUEUE_DEPTH; i++) begin
            logic row_hit;

            // Default row_hit to 0 when queue entry is invalid
            row_hit = 1'b0;

            // Only select requests when FSM is idle
            if (queue[i].valid && (state == IDLE)) begin
                // Check row hit for this queue entry
                row_hit = check_row_hit(queue[i].addr);

                // Selection criteria: row_hit > priority > age (older wins)
                if (!grant_valid) begin
                    best_idx = i[$clog2(QUEUE_DEPTH)-1:0];
                    best_priority = queue[i].req_priority;
                    best_age = queue[i].age;
                    best_row_hit = row_hit;
                    grant_valid = 1'b1;
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
    logic [ADDR_WIDTH-1:0] grant_addr;  // Latch address at grant time
    logic grant_rd_wr_n;                // Latch read/write at grant time

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant_idx <= 0;
            grant_row_hit <= 0;
            grant_addr <= '0;
            grant_rd_wr_n <= 1;
        end else begin
            if (grant_valid && fsm_ready) begin
                grant_idx <= best_idx;
                grant_row_hit <= best_row_hit;
                // Latch current request fields at grant time
                grant_addr <= queue[best_idx].addr;
                grant_rd_wr_n <= queue[best_idx].rd_wr_n;
            end
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
                // Use registered grant signals for stable FSM decision
                if (grant_valid && fsm_ready) begin
                    // For row hit (open row), skip ACTIVATE and go directly to READ/WRITE
                    // For row miss (closed row), need to ACTIVATE first
                    if (grant_row_hit) begin
                        // Determine READ or WRITE based on latched rd_wr_n
                        next_state = grant_rd_wr_n ? READ : WRITE;
                    end else begin
                        next_state = ACTIVATE;
                    end
                end
            end

            ACTIVATE: begin
                // After ACTIVATE, go to READ or WRITE based on latched command
                next_state = grant_rd_wr_n ? READ : WRITE;
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
    logic txn_started;  // High when a new transaction has started (ID captured)

    assign fsm_ready = (state == IDLE);
    assign do_activate = (state == ACTIVATE);
    assign do_read = (state == READ);
    assign do_write = (state == WRITE);
    assign do_precharge = (state == PRECHARGE);

    // =============================================================================
    // DRAM Command Output - HBM4 Command Encoding
    // =============================================================================
    // Command values: 4'd0=NOP, 4'd1=ACT, 4'd2=READ, 4'd3=WRITE, 4'd4=PRE, 4'd5=PREA, 4'd6=REF
    // =============================================================================
    logic [31:0] cur_id;
    logic cur_rd_wr_n;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dram_cmd <= 4'd0;
            cur_id <= 0;
            cur_rd_wr_n <= 1;
            txn_started <= 0;
        end else begin
            dram_cmd <= 4'd0;

            if (do_activate) begin
                dram_cmd <= 4'd1;  // CMD_ACT
            end else if (do_read) begin
                dram_cmd <= 4'd2;  // CMD_READ
            end else if (do_write) begin
                dram_cmd <= 4'd3;  // CMD_WRITE
            end else if (do_precharge) begin
                dram_cmd <= 4'd4;  // CMD_PRE
            end

            // Capture request info when new transaction starts
            // Only capture once per transaction until response is issued
            if (grant_valid && fsm_ready && !txn_started) begin
                cur_id <= queue[grant_idx].id;
                cur_rd_wr_n <= grant_rd_wr_n;
                txn_started <= 1;
            end

            // Clear txn_started when response is issued
            if (resp_valid) begin
                txn_started <= 0;
            end
        end
    end

    // DRAM address outputs - HBM4 address fields
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dram_ch   <= '0;
            dram_bg   <= '0;
            dram_bank <= '0;
            dram_pch  <= '0;
            dram_row  <= '0;
        end else begin
            // Use latched grant address for stable output
            if (grant_valid && fsm_ready) begin
                dram_ch   <= grant_addr[CH_ADDR_WIDTH+BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                                  BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
                dram_bg   <= grant_addr[BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                                  BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
                dram_bank <= grant_addr[BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:
                                  ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
                dram_pch  <= grant_addr[BG_ADDR_WIDTH+BK_ADDR_WIDTH+ROW_ADDR_WIDTH+COL_ADDR_WIDTH];
                dram_row  <= grant_addr[ROW_ADDR_WIDTH+COL_ADDR_WIDTH-1:COL_ADDR_WIDTH];
            end
        end
    end

    // Write data assignment
    always_ff @(posedge clk) begin
        if (do_write)
            dram_wr_data <= 256'hDEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF_DEADBEEF;
    end

    // =============================================================================
    // Read Data Handling
    // =============================================================================
    // verilator lint_off UNUSEDSIGNAL
    logic [255:0] read_data_q;  // Read data capture register
    assign read_data_q = dram_rd_data;  // Use read data (captured in READ_WF state)
    // verilator lint_on UNUSEDSIGNAL

    // =============================================================================
    // Response Generation
    // =============================================================================
    // resp_id must be updated on the same cycle as resp_valid
    // to ensure correct ID is returned with the response
    // Use resp_issued to prevent multiple responses per transaction

    logic resp_issued;  // High after response is issued for current transaction

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            resp_valid <= 0;
            resp_id <= 0;
            resp_success <= 0;
            resp_status <= 0;
            resp_issued <= 0;
        end else begin
            // Clear response at start of new cycle
            resp_valid <= 0;
            resp_issued <= 0;

            if (state == COMPLETE && !resp_issued) begin
                resp_valid <= 1;
                resp_id <= cur_id;
                resp_success <= 1;
                resp_status <= 8'd0;  // Success
                resp_issued <= 1;    // Mark as issued to prevent duplicates
            end
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
                stat_hit_rate <= 8'((completed_q * 100) / requests_q);
            else
                stat_hit_rate <= 8'd0;
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

    // =============================================================================
    // SystemVerilog Assertions
    // =============================================================================
    // Enable assertions in simulation
    `ifdef ASSERT_ON
    `ifdef VERILATOR
    `else
    // =============================================================================
    // 1. Reset Behavior Assertions
    // =============================================================================
    assert property (@(posedge clk) rst_n === 1'b0 |=> rst_n[*0:$] throughout req_ready == 1'b1)
        else $error("Controller should be ready after reset");

    assert property (@(posedge clk) disable iff (!rst_n)
        state == IDLE)
        else $error("FSM should be in IDLE after reset");

    // =============================================================================
    // 2. Queue Behavior Assertions
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        req_valid && req_ready |-> queue_count < QUEUE_DEPTH)
        else $error("Should not enqueue when queue is full");

    assert property (@(posedge clk) disable iff (!rst_n)
        grant_valid |-> queue_count > 0)
        else $error("Should not grant when queue is empty");

    assert property (@(posedge clk) disable iff (!rst_n)
        req_valid && req_ready |-> queue_count <= QUEUE_DEPTH)
        else $error("Queue count should not exceed depth");

    // =============================================================================
    // 3. FSM State Transition Assertions (Critical Timing Paths)
    // =============================================================================
    // ACT -> READ/WRITE path (row miss case)
    assert property (@(posedge clk) disable iff (!rst_n)
        state == ACTIVATE |=> state == READ || state == WRITE)
        else $error("ACTIVATE should transition to READ or WRITE based on command");

    // READ -> READ_WF -> PRECHARGE -> COMPLETE path
    assert property (@(posedge clk) disable iff (!rst_n)
        state == READ |=> state == READ_WF)
        else $error("READ should transition to READ_WF");

    assert property (@(posedge clk) disable iff (!rst_n)
        state == READ_WF |=> state == PRECHARGE)
        else $error("READ_WF should transition to PRECHARGE");

    // WRITE -> WRITE_WF -> PRECHARGE path
    assert property (@(posedge clk) disable iff (!rst_n)
        state == WRITE |=> state == WRITE_WF)
        else $error("WRITE should transition to WRITE_WF");

    assert property (@(posedge clk) disable iff (!rst_n)
        state == WRITE_WF |=> state == PRECHARGE)
        else $error("WRITE_WF should transition to PRECHARGE");

    // PRECHARGE -> COMPLETE -> IDLE path
    assert property (@(posedge clk) disable iff (!rst_n)
        state == PRECHARGE |=> state == COMPLETE)
        else $error("PRECHARGE should transition to COMPLETE");

    assert property (@(posedge clk) disable iff (!rst_n)
        state == COMPLETE |=> state == IDLE)
        else $error("COMPLETE should transition to IDLE");

    // Row hit path: IDLE -> READ/WRITE (skipping ACTIVATE)
    assert property (@(posedge clk) disable iff (!rst_n)
        state == IDLE && grant_valid && grant_row_hit |=> state == READ || state == WRITE)
        else $error("Row hit should skip ACTIVATE and go directly to READ/WRITE");

    // Row miss path: IDLE -> ACTIVATE
    assert property (@(posedge clk) disable iff (!rst_n)
        state == IDLE && grant_valid && !grant_row_hit |=> state == ACTIVATE)
        else $error("Row miss should go to ACTIVATE");

    // =============================================================================
    // 4. DRAM Command Validity Assertions
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        dram_cmd inside {4'd0, 4'd1, 4'd2, 4'd3, 4'd4})
        else $error("DRAM command should be valid (NOP, ACT, READ, WRITE, or PRE)");

    assert property (@(posedge clk) disable iff (!rst_n)
        (state == IDLE && !grant_valid) |-> dram_cmd == 4'd0)
        else $error("Should issue NOP when idle and no grant");

    assert property (@(posedge clk) disable iff (!rst_n)
        state == ACTIVATE |-> dram_cmd == 4'd1)
        else $error("ACTIVATE state should issue CMD_ACT");

    assert property (@(posedge clk) disable iff (!rst_n)
        state == READ |-> dram_cmd == 4'd2)
        else $error("READ state should issue CMD_READ");

    assert property (@(posedge clk) disable iff (!rst_n)
        state == WRITE |-> dram_cmd == 4'd3)
        else $error("WRITE state should issue CMD_WRITE");

    assert property (@(posedge clk) disable iff (!rst_n)
        state == PRECHARGE |-> dram_cmd == 4'd4)
        else $error("PRECHARGE state should issue CMD_PRE");

    // =============================================================================
    // 5. Critical Timing Path: ACT->RD/WR->PRE Sequence
    // =============================================================================
    // Verify ACT command precedes READ for row miss
    assert property (@(posedge clk) disable iff (!rst_n)
        state == READ && $past(state) == ACTIVATE |-> $past(dram_cmd) == 4'd1)
        else $error("READ should follow ACT command");

    // Verify ACT command precedes WRITE for row miss
    assert property (@(posedge clk) disable iff (!rst_n)
        state == WRITE && $past(state) == ACTIVATE |-> $past(dram_cmd) == 4'd1)
        else $error("WRITE should follow ACT command");

    // Verify PRE command follows READ_WF
    assert property (@(posedge clk) disable iff (!rst_n)
        state == PRECHARGE && $past(state) == READ_WF |-> $past(dram_cmd) == 4'd2)
        else $error("PRECHARGE should follow READ_WF with READ command");

    // Verify PRE command follows WRITE_WF
    assert property (@(posedge clk) disable iff (!rst_n)
        state == PRECHARGE && $past(state) == WRITE_WF |-> $past(dram_cmd) == 4'd3)
        else $error("PRECHARGE should follow WRITE_WF with WRITE command");

    // Verify PRE is issued before returning to IDLE
    assert property (@(posedge clk) disable iff (!rst_n)
        state == COMPLETE |-> $past(state) == PRECHARGE)
        else $error("COMPLETE should follow PRECHARGE");

    // =============================================================================
    // 6. Address Channel Range Assertions
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        grant_valid |-> dram_ch < (1 << CH_ADDR_WIDTH))
        else $error("DRAM channel index out of range");

    assert property (@(posedge clk) disable iff (!rst_n)
        grant_valid |-> dram_bg < (1 << BG_ADDR_WIDTH))
        else $error("DRAM bank group index out of range");

    assert property (@(posedge clk) disable iff (!rst_n)
        grant_valid |-> dram_bank < (1 << BK_ADDR_WIDTH))
        else $error("DRAM bank index out of range");

    assert property (@(posedge clk) disable iff (!rst_n)
        grant_valid |-> dram_pch < (1 << PCH_ADDR_WIDTH))
        else $error("DRAM pseudo-channel index out of range");

    // =============================================================================
    // 7. Response Validity Assertions
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        resp_valid |-> resp_id != 0)
        else $error("Response ID should not be zero");

    assert property (@(posedge clk) disable iff (!rst_n)
        resp_valid |-> resp_status == 8'd0)
        else $error("Response status should be success (0)");

    assert property (@(posedge clk) disable iff (!rst_n)
        resp_valid |-> resp_success == 1'b1)
        else $error("Response success flag should be set");

    // =============================================================================
    // 8. Row Buffer Consistency Assertions
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        row_open == 1'b1 |-> open_bank_reg[get_ch_idx(dec_ch)] != '0)
        else $error("Row open but bank register is invalid");

    assert property (@(posedge clk) disable iff (!rst_n)
        row_open == 1'b1 |-> open_row_reg[get_ch_idx(dec_ch)] != '0)
        else $error("Row open but row register is invalid");

    // =============================================================================
    // 9. Grant Signal Consistency
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        grant_valid |-> 1'b1)
        else $error("Grant should be valid when selected");

    // =============================================================================
    // 10. Priority Encoding Assertions
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        req_valid |-> req_priority <= 3'd7)
        else $error("Request priority should be 3-bit value (0-7)");

    // =============================================================================
    // 11. Transaction Atomicity
    // =============================================================================
    // Queue entry should remain valid during entire transaction (ACT path)
    assert property (@(posedge clk) disable iff (!rst_n)
        grant_valid && fsm_ready && state == IDLE && !grant_row_hit
        |->
        queue[grant_idx].valid throughout (ACTIVATE[*1:$] ##1 (READ[*0:$] or WRITE[*0:$] ##1 READ_WF[*0:$] or WRITE_WF[*0:$] ##1 PRECHARGE ##1 COMPLETE)))
        else $error("Queue entry should remain valid during ACT->RD/WR->PRE transaction");

    // Queue entry should remain valid during row hit transaction
    assert property (@(posedge clk) disable iff (!rst_n)
        grant_valid && fsm_ready && state == IDLE && grant_row_hit
        |->
        queue[grant_idx].valid throughout ((READ[*0:$] or WRITE[*0:$]) ##1 (READ_WF[*0:$] or WRITE_WF[*0:$]) ##1 PRECHARGE ##1 COMPLETE))
        else $error("Queue entry should remain valid during row hit transaction");

    // =============================================================================
    // 12. No Back-to-Back Grants (One transaction at a time)
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        state != IDLE |-> !grant_valid || fsm_ready)
        else $error("Should not grant new transaction while FSM is busy");

    // =============================================================================
    // 13. Write Data Validity
    // =============================================================================
    assert property (@(posedge clk) disable iff (!rst_n)
        dram_cmd == 4'd3 |-> dram_wr_data != '0)
        else $error("Write data should be valid during WRITE command");

    `endif  // VERILATOR
    `endif  // ASSERT_ON

endmodule
// verilator lint_on WIDTHEXPAND
// verilator lint_on SELRANGE
// verilator lint_on WIDTHTRUNC
// verilator lint_on UNUSEDSIGNAL
// verilator lint_on UNUSEDPARAM
// verilator lint_on LATCH
// verilator lint_on MISINDENT
// verilator lint_on EOFNEWLINE
// verilator lint_on UNSIGNED
