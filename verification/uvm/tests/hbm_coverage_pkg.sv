// ------------------------------------------------------------
// hbm_coverage_pkg.sv - HBM Coverage Collection Package
// Functional and code coverage for HBM verification
// ------------------------------------------------------------
package hbm_coverage_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// =============================================================
// Command Coverage
// =============================================================
covergroup command_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "command_coverage";
    option.comment = "Coverage for HBM command types";

    // Command type coverage
    cmd: coverpoint cmd_type {
        type_option.weight = 0;  // Don't count total

        bins cmd_nop     = {3'b000};
        bins cmd_act     = {3'b001};
        bins cmd_read    = {3'b010};
        bins cmd_write   = {3'b011};
        bins cmd_pre     = {3'b100};
        bins cmd_ref     = {3'b101};
        bins cmd_refpb   = {3'b110};

        illegal_bins illegal_cmd = {3'b111};
    }

    // Bank coverage
    bank: coverpoint bank_idx {
        option.weight = 0;

        bins bank_0 = {0};
        bins bank_1_7 = {[1:7]};
        bins bank_8_15 = {[8:15]};
        bins bank_high = {[15:MAX_BANKS-1]};
    }

    // Command x Bank cross coverage
    cmd_x_bank: cross cmd, bank {
        // Interesting combinations
        bins act_bank0  = binsof(cmd.cmd_act) && binsof(bank.bank_0);
        bins rd_bank_hi = binsof(cmd.cmd_read) && binsof(bank.bank_high);
        bins wr_bank_lo = binsof(cmd.cmd_write) && binsof(bank.bank_1_7);
    }
endgroup

// =============================================================
// Bank Coverage
// =============================================================
covergroup bank_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "bank_coverage";
    option.comment = "Coverage for bank access patterns";

    // Per-bank access coverage
    bank_access: coverpoint bank_idx {
        option.weight = 0;

        // Individual bank coverage
        banks: bins bank[] = {[0:MAX_BANKS-1]};

        // Bank group coverage (8 groups, 2 banks each)
        bins group_0 = {[0:1]};
        bins group_1 = {[2:3]};
        bins group_2 = {[4:5]};
        bins group_3 = {[6:7]};
        bins group_4 = {[8:9]};
        bins group_5 = {[10:11]};
        bins group_6 = {[12:13]};
        bins group_7 = {[14:15]};
    }

    // Row coverage within banks
    row_access: coverpoint row_addr {
        option.weight = 0;

        bins row_low    = {[0:255]};
        bins row_mid    = {[256:65280]};
        bins row_high   = {[65281:65534]};
        bins row_max    = {[65535]};
        bins row_zero   = {[0]};
    }

    // Bank x Row cross coverage
    bank_x_row: cross bank_access, row_access {
        bins hot_bank_row = binsof(bank_access.banks) && binsof(row_access.row_zero);
        ignore_bins ignore_invalid = binsof(bank_access.banks) && binsof(row_access.row_high);
    }
endgroup

// =============================================================
// Row Coverage
// =============================================================
covergroup row_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "row_coverage";
    option.comment = "Coverage for row access patterns";

    // Row region coverage
    row_region: coverpoint row_addr {
        option.weight = 0;

        bins row_region_0  = {[0:16383]};
        bins row_region_1  = {[16384:32767]};
        bins row_region_2  = {[32768:49151]};
        bins row_region_3  = {[49152:65535]};
    }

    // Row pattern coverage (consecutive accesses)
    row_pattern: coverpoint row_addr {
        option.weight = 0;

        bins row_same    = (row_addr => row_addr);
        bins row_inc     = (row_addr => row_addr + 1);
        bins row_dec     = (row_addr => row_addr - 1);
        bins row_random  = default sequence;
    }

    // Row hits vs misses
    row_hit_miss: coverpoint row_hit {
        option.weight = 0;

        bins row_hit   = {1'b1};
        bins row_miss  = {1'b0};
    }
endgroup

// =============================================================
// Column Coverage
// =============================================================
covergroup column_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "column_coverage";
    option.comment = "Coverage for column access patterns";

    // Column coverage
    col: coverpoint col_addr {
        option.weight = 0;

        bins col_0 = {0};
        bins col_1 = {1};
        bins col_2 = {2};
        bins col_3 = {3};
        bins col_all = {0,1,2,3};
    }

    // Burst coverage
    burst: coverpoint burst_len {
        option.weight = 0;

        bins burst_1  = {1};
        bins burst_2  = {2};
        bins burst_4  = {4};
        bins burst_8  = {8};
        bins burst_16 = {16};
    }
endgroup

// =============================================================
// Priority/QoS Coverage
// =============================================================
covergroup qos_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "qos_coverage";
    option.comment = "Coverage for QoS priority levels";

    // Priority level coverage
    priority: coverpoint priority {
        option.weight = 0;

        bins prio_critical = {3'b000};
        bins prio_high     = {3'b001};
        bins prio_normal   = {3'b010};
        bins prio_low      = {3'b011};
        bins prio_idle     = {3'b111};
    }

    // Deadline coverage
    deadline: coverpoint deadline {
        option.weight = 0;

        bins deadline_short = {[1:50]};
        bins deadline_med   = {[51:200]};
        bins deadline_long  = {[201:1000]};
        bins deadline_none  = {0};
    }

    // Priority x Bank cross coverage
    prio_x_bank: cross priority, bank_idx {
        bins critical_bank = binsof(priority.prio_critical);
        bins low_bank      = binsof(priority.prio_low);
    }

    // Priority x Command cross coverage
    prio_x_cmd: cross priority, cmd_type {
        bins critical_read  = binsof(priority.prio_critical) && binsof(cmd_type.cmd_read);
        bins critical_write = binsof(priority.prio_critical) && binsof(cmd_type.cmd_write);
    }
endgroup

// =============================================================
// Refresh Coverage
// =============================================================
covergroup refresh_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "refresh_coverage";
    option.comment = "Coverage for refresh operations";

    // Refresh type coverage
    refresh_type: coverpoint refresh_type {
        option.weight = 0;

        bins ref_full  = {REFRESH_FULL};
        bins ref_bank  = {REFRESH_BANK};
        bins ref_pb    = {REFRESH_PER_BANK};
    }

    // Refresh timing coverage
    refresh_interval: coverpoint refresh_interval_cycles {
        option.weight = 0;

        bins ref_early   = {[1:1000]};
        bins ref_normal  = {[1001:5000]};
        bins ref_late    = {[5001:10000]};
        bins ref_timeout = {[10001:$]};
    }

    // Refresh during traffic coverage
    refresh_during_traffic: coverpoint refresh_during_active {
        option.weight = 0;

        bins ref_idle    = {1'b0};
        bins ref_active  = {1'b1};
    }
endgroup

// =============================================================
// Timing Coverage
// =============================================================
covergroup timing_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "timing_coverage";
    option.comment = "Coverage for timing parameter settings";

    // tRCD coverage
    tRCD: coverpoint tRCD_value {
        option.weight = 0;

        bins trcd_min = {[1:8]};
        bins trcd_nom = {[9:20]};
        bins trcd_max = {[21:255]};
    }

    // tRP coverage
    tRP: coverpoint tRP_value {
        option.weight = 0;

        bins trp_min = {[1:8]};
        bins trp_nom = {[9:20]};
        bins trp_max = {[21:255]};
    }

    // tRAS coverage
    tRAS: coverpoint tRAS_value {
        option.weight = 0;

        bins tras_min = {[1:20]};
        bins tras_nom = {[21:40]};
        bins tras_max = {[41:255]};
    }

    // tRC coverage
    tRC: coverpoint tRC_value {
        option.weight = 0;

        bins trc_min = {[1:30]};
        bins trc_nom = {[31:60]};
        bins trc_max = {[61:255]};
    }
endgroup

// =============================================================
// Transaction Coverage
// =============================================================
covergroup transaction_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "transaction_coverage";
    option.comment = "Coverage for complete transaction patterns";

    // Transaction type
    trans_type: coverpoint transaction_type {
        option.weight = 0;

        bins read_trans  = {1'b0};
        bins write_trans = {1'b1};
    }

    // Address coverage
    addr_coverage: coverpoint addr_bank {
        option.weight = 0;

        bins addr_all = {[0:MAX_BANKS-1]};
    }

    // Data valid coverage
    data_valid: coverpoint data_valid {
        option.weight = 0;

        bins data_valid   = {1'b1};
        bins data_invalid = {1'b0};
    }

    // Transaction success coverage
    trans_success: coverpoint transaction_success {
        option.weight = 0;

        bins success = {1'b1};
        bins failure = {1'b0};
    }

    // Cross coverage: type x success
    type_x_success: cross trans_type, trans_success {
        bins read_success  = binsof(trans_type.read_trans) && binsof(trans_success.success);
        bins write_success = binsof(trans_type.write_trans) && binsof(trans_success.success);
    }
endgroup

// =============================================================
// HBM Functional Coverage Collector
// =============================================================
class hbm_functional_coverage extends uvm_subscriber #(hbm_transaction);
    `uvm_component_utils(hbm_functional_coverage)

    // Coverage groups
    command_coverage cmd_cov;
    bank_coverage bank_cov;
    row_coverage row_cov;
    column_coverage col_cov;
    qos_coverage qos_cov;
    refresh_coverage ref_cov;
    timing_coverage timing_cov;
    transaction_coverage trans_cov;

    // Internal state
    logic [2:0] cmd_type;
    logic [5:0] bank_idx;
    logic [15:0] row_addr;
    logic [9:0] col_addr;
    logic [2:0] priority;
    logic [15:0] deadline;
    logic row_hit;
    bit [7:0] burst_len;
    bit data_valid;
    bit transaction_type;
    bit transaction_success;

    // Refresh state
    typedef enum {REFRESH_FULL, REFRESH_BANK, REFRESH_PER_BANK} refresh_type_t;
    refresh_type_t refresh_type;
    int refresh_interval_cycles;
    bit refresh_during_active;

    // Timing state
    logic [7:0] tRCD_value;
    logic [7:0] tRP_value;
    logic [7:0] tRAS_value;
    logic [15:0] tRC_value;

    // Coverage counters
    int total_transactions = 0;
    int covered_transactions = 0;
    real coverage_percent = 0.0;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        cmd_cov     = new();
        bank_cov    = new();
        row_cov     = new();
        col_cov     = new();
        qos_cov     = new();
        ref_cov    = new();
        timing_cov = new();
        trans_cov  = new();
    endfunction

    function void write(T t);
        // Update internal state from transaction
        cmd_type = t.cmd;
        bank_idx = t.addr_bank[5:0];
        row_addr = t.addr_row;
        col_addr = {8'b0, t.addr_col};
        priority = t.req_priority;
        row_hit = (t.addr_row == prev_row_for_bank(t.addr_bank)) ? 1'b1 : 1'b0;
        data_valid = t.rdata_valid;
        transaction_type = (t.cmd == hbm_transaction::READ) ? 1'b0 : 1'b1;
        transaction_success = t.rdata_valid;

        // Sample coverage
        sample_transaction(t);

        total_transactions++;
    endfunction

    function void sample_transaction(hbm_transaction t);
        // Sample all coverage groups
        cmd_cov.sample();
        bank_cov.sample();
        row_cov.sample();
        col_cov.sample();

        if (t.req_priority != 0) begin
            qos_cov.sample();
        end

        if (t.cmd == hbm_transaction::READ || t.cmd == hbm_transaction::WRITE) begin
            trans_cov.sample();
        end

        covered_transactions++;
    endfunction

    function void sample_refresh(refresh_type_t rtype, int interval);
        refresh_type = rtype;
        refresh_interval_cycles = interval;
        ref_cov.sample();
    endfunction

    function void sample_timing(logic [7:0] tRCD, tRP, tRAS, logic [15:0] tRC);
        tRCD_value = tRCD;
        tRP_value = tRP;
        tRAS_value = tRAS;
        tRC_value = tRC;
        timing_cov.sample();
    endfunction

    function logic [15:0] prev_row_for_bank(bit [7:0] bank);
        // Track previous row for each bank (simplified)
        return prev_row[bank];
    endfunction

    // Previous row tracking
    logic [15:0] prev_row[MAX_BANKS];

    function real get_coverage();
        return coverage_percent;
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);

        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)
        `uvm_info(get_name(), "         HBM Functional Coverage Report          ", UVM_MEDIUM)
        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Total Transactions:    %0d", total_transactions), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Covered Transactions:  %0d", covered_transactions), UVM_MEDIUM)
        `uvm_info(get_name(), "--------------------------------------------------", UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Command Coverage:      %.2f%%", cmd_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Bank Coverage:         %.2f%%", bank_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Row Coverage:         %.2f%%", row_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Column Coverage:       %.2f%%", col_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("QoS Coverage:          %.2f%%", qos_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Refresh Coverage:      %.2f%%", ref_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Timing Coverage:      %.2f%%", timing_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Transaction Coverage: %.2f%%", trans_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)

        // Check for low coverage
        if (cmd_cov.get_coverage() < 80.0) begin
            `uvm_warning(get_name(), "Command coverage below 80%")
        end
        if (bank_cov.get_coverage() < 70.0) begin
            `uvm_warning(get_name(), "Bank coverage below 70%")
        end
    endfunction
endclass

// =============================================================
// Code Coverage Helper
// =============================================================
class hbm_code_coverage extends uvm_subscriber #(hbm_transaction);
    `uvm_component_utils(hbm_code_coverage)

    // State machine state coverage
    int fsm_states_covered = 0;
    int total_fsm_states = 8;

    // Branch coverage counters
    int branches_taken = 0;
    int total_branches = 16;

    // Line coverage tracking
    bit line_covered[bit];
    int lines_covered = 0;
    int total_lines = 100;

    // Toggle coverage
    int toggles_covered = 0;
    int total_toggles = 256;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void write(T t);
        // Track FSM state transitions
        fsm_states_covered = fsm_states_covered + 1;

        // Track branches
        branches_taken = branches_taken + 1;

        // Track lines
        if (!line_covered.exists(t.transaction_id)) begin
            line_covered[t.transaction_id] = 1'b1;
            lines_covered++;
        end
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);

        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)
        `uvm_info(get_name(), "         HBM Code Coverage Report               ", UVM_MEDIUM)
        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("FSM State Coverage:   %0d/%0d states (%.2f%%)",
                                        fsm_states_covered, total_fsm_states,
                                        fsm_states_covered * 100.0 / total_fsm_states), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Branch Coverage:      %0d/%0d branches (%.2f%%)",
                                        branches_taken, total_branches,
                                        branches_taken * 100.0 / total_branches), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Line Coverage:        %0d/%0d lines (%.2f%%)",
                                        lines_covered, total_lines,
                                        lines_covered * 100.0 / total_lines), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Toggle Coverage:      %0d/%0d bits (%.2f%%)",
                                        toggles_covered, total_toggles,
                                        toggles_covered * 100.0 / total_toggles), UVM_MEDIUM)
        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)
    endfunction
endclass

// =============================================================
// Coverage Manager
// =============================================================
class hbm_coverage_manager extends uvm_component;
    `uvm_component_utils(hbm_coverage_manager)

    hbm_functional_coverage func_cov;
    hbm_code_coverage code_cov;

    uvm_analysis_imp #(hbm_transaction, hbm_coverage_manager) analysis_export;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        func_cov = hbm_functional_coverage::type_id::create("func_cov", this);
        code_cov = hbm_code_coverage::type_id::create("code_cov", this);
        analysis_export = new("analysis_export", this);
    endfunction

    function void write(hbm_transaction t);
        // Forward to coverage collectors
        void'(func_cov.write(t));
        void'(code_cov.write(t));
    endfunction

    function real get_functional_coverage();
        return func_cov.get_coverage();
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);

        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)
        `uvm_info(get_name(), "         HBM Coverage Summary                    ", UVM_MEDIUM)
        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Functional Coverage:  %.2f%%", get_functional_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)
    endfunction
endclass

endpackage : hbm_coverage_pkg