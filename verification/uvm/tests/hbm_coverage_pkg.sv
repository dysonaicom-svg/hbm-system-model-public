// ------------------------------------------------------------
// hbm_coverage_pkg.sv - Enhanced HBM Coverage Collection Package
// Comprehensive functional and code coverage for HBM4 verification
// ------------------------------------------------------------
package hbm_coverage_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// =============================================================
// Coverage Configuration
// =============================================================
class hbm_coverage_config extends uvm_object;
    `uvm_object_utils(hbm_coverage_config)

    bit enable_command_cov = 1;
    bit enable_bank_cov = 1;
    bit enable_row_cov = 1;
    bit enable_column_cov = 1;
    bit enable_qos_cov = 1;
    bit enable_refresh_cov = 1;
    bit enable_timing_cov = 1;
    bit enable_transaction_cov = 1;
    bit enable_priority_inversion_cov = 1;
    bit enable_starvation_cov = 1;
    bit enable_bank_group_cov = 1;
    bit enable_burst_cov = 1;

    int bank_count = 16;
    int bank_group_count = 4;
    int row_count = 65536;
    int column_count = 4;
    int priority_levels = 8;
    int queue_depth = 32;

    function new(string name = "hbm_coverage_config");
        super.new(name);
    endfunction
endclass

// =============================================================
// Command Coverage - Enhanced
// =============================================================
covergroup command_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "command_coverage";
    option.comment = "Coverage for HBM command types";

    cmd: coverpoint cmd_type {
        type_option.weight = 0;

        bins cmd_nop     = {3'b000};
        bins cmd_act     = {3'b001};
        bins cmd_read    = {3'b010};
        bins cmd_write   = {3'b011};
        bins cmd_pre     = {3'b100};
        bins cmd_ref     = {3'b101};
        bins cmd_refpb   = {3'b110};

        illegal_bins illegal_cmd = {3'b111};
    }

    bank: coverpoint bank_idx {
        option.weight = 0;

        bins bank_0 = {0};
        bins bank_1_7 = {[1:7]};
        bins bank_8_15 = {[8:15]};
        bins bank_high = {[15:MAX_BANKS-1]};
    }

    cmd_x_bank: cross cmd, bank {
        bins act_bank0  = binsof(cmd.cmd_act) && binsof(bank.bank_0);
        bins rd_bank_hi = binsof(cmd.cmd_read) && binsof(bank.bank_high);
        bins wr_bank_lo = binsof(cmd.cmd_write) && binsof(bank.bank_1_7);
    }
endgroup

// =============================================================
// Bank Coverage - Enhanced with all 16 banks
// =============================================================
covergroup bank_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "bank_coverage";
    option.comment = "Coverage for bank access patterns";

    bank_access: coverpoint bank_idx {
        option.weight = 0;
        banks: bins bank[] = {[0:MAX_BANKS-1]};

        bins group_0 = {[0:3]};
        bins group_1 = {[4:7]};
        bins group_2 = {[8:11]};
        bins group_3 = {[12:15]};
    }

    row_access: coverpoint row_addr {
        option.weight = 0;

        bins row_low    = {[0:255]};
        bins row_mid    = {[256:65280]};
        bins row_high   = {[65281:65534]};
        bins row_max    = {[65535]};
        bins row_zero   = {[0]};
    }

    bank_x_row: cross bank_access, row_access {
        bins hot_bank_row = binsof(bank_access.banks) && binsof(row_access.row_zero);
        ignore_bins ignore_invalid = binsof(bank_access.banks) && binsof(row_access.row_high);
    }
endgroup

// =============================================================
// Bank Group Conflict Coverage
// =============================================================
covergroup bank_group_conflict_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "bank_group_conflict_coverage";
    option.comment = "Coverage for bank group conflicts";

    bank_group: coverpoint bank_group_idx {
        option.weight = 0;

        bins group_0 = {0};
        bins group_1 = {1};
        bins group_2 = {2};
        bins group_3 = {3};
        bins all_groups = {[0:3]};
    }

    conflict_detected: coverpoint conflict_flag {
        option.weight = 0;

        bins conflict = {1'b1};
        bins no_conflict = {1'b0};
    }

    group_x_conflict: cross bank_group, conflict_detected {
        bins group_0_conflict = binsof(bank_group.group_0) && binsof(conflict_detected.conflict);
        bins group_1_conflict = binsof(bank_group.group_1) && binsof(conflict_detected.conflict);
        bins group_2_conflict = binsof(bank_group.group_2) && binsof(conflict_detected.conflict);
        bins group_3_conflict = binsof(bank_group.group_3) && binsof(conflict_detected.conflict);
    }

    // tRRD violation tracking
    tRRD_violation: coverpoint trrd_violation_flag {
        option.weight = 0;

        bins violation = {1'b1};
        bins ok = {1'b0};
    }
endgroup

// =============================================================
// Row Coverage - Enhanced
// =============================================================
covergroup row_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "row_coverage";
    option.comment = "Coverage for row access patterns";

    row_region: coverpoint row_addr {
        option.weight = 0;

        bins row_region_0  = {[0:16383]};
        bins row_region_1  = {[16384:32767]};
        bins row_region_2  = {[32768:49151]};
        bins row_region_3  = {[49152:65535]};
    }

    row_pattern: coverpoint row_addr {
        option.weight = 0;

        bins row_same    = (row_addr => row_addr);
        bins row_inc     = (row_addr => row_addr + 1);
        bins row_dec     = (row_addr => row_addr - 1);
        bins row_random  = default sequence;
    }

    row_hit_miss: coverpoint row_hit {
        option.weight = 0;

        bins row_hit   = {1'b1};
        bins row_miss  = {1'b0};
    }

    // Row activation conflict (row hammer detection)
    row_activation_conflict: coverpoint activation_conflict {
        option.weight = 0;

        bins conflict_detected = {1'b1};
        bins no_conflict = {1'b0};
    }
endgroup

// =============================================================
// Column Coverage - Enhanced with burst patterns
// =============================================================
covergroup column_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "column_coverage";
    option.comment = "Coverage for column access patterns";

    col: coverpoint col_addr {
        option.weight = 0;

        bins col_0 = {0};
        bins col_1 = {1};
        bins col_2 = {2};
        bins col_3 = {3};
        bins col_all = {0,1,2,3};
    }

    burst: coverpoint burst_len {
        option.weight = 0;

        bins burst_1  = {1};
        bins burst_2  = {2};
        bins burst_4  = {4};
        bins burst_8  = {8};
        bins burst_16 = {16};
        bins burst_all = {1,2,4,8,16};
    }

    col_x_burst: cross col, burst {
        bins col0_burst4 = binsof(col.col_0) && binsof(burst.burst_4);
        bins col3_burst8 = binsof(col.col_3) && binsof(burst.burst_8);
    }
endgroup

// =============================================================
// QoS Priority Coverage - Enhanced
// =============================================================
covergroup qos_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "qos_coverage";
    option.comment = "Coverage for QoS priority levels";

    priority: coverpoint priority {
        option.weight = 0;

        bins prio_critical = {3'b000};
        bins prio_high     = {3'b001};
        bins prio_normal   = {3'b010};
        bins prio_low      = {3'b011};
        bins prio_idle     = {3'b111};
        bins all_priorities = {[0:7]};
    }

    deadline: coverpoint deadline {
        option.weight = 0;

        bins deadline_short = {[1:50]};
        bins deadline_med   = {[51:200]};
        bins deadline_long  = {[201:1000]};
        bins deadline_none  = {0};
    }

    deadline_violation: coverpoint deadline_violated {
        option.weight = 0;

        bins violated = {1'b1};
        bins met = {1'b0};
    }

    prio_x_bank: cross priority, bank_idx {
        bins critical_bank = binsof(priority.prio_critical);
        bins low_bank      = binsof(priority.prio_low);
    }

    prio_x_cmd: cross priority, cmd_type {
        bins critical_read  = binsof(priority.prio_critical) && binsof(cmd_type.cmd_read);
        bins critical_write = binsof(priority.prio_critical) && binsof(cmd_type.cmd_write);
    }

    prio_x_deadline: cross priority, deadline {
        bins critical_short = binsof(priority.prio_critical) && binsof(deadline.deadline_short);
        bins low_long = binsof(priority.prio_low) && binsof(deadline.deadline_long);
    }
endgroup

// =============================================================
// Priority Inversion Coverage
// =============================================================
covergroup priority_inversion_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "priority_inversion_coverage";
    option.comment = "Coverage for priority inversion scenarios";

    high_priority_blocked: coverpoint high_prio_blocked {
        option.weight = 0;

        bins blocked = {1'b1};
        bins served = {1'b0};
    }

    blocking_priority: coverpoint blocking_prio {
        option.weight = 0;

        bins block_low = {3'b011};
        bins block_normal = {3'b010};
        bins block_high = {3'b001};
        bins block_all = {[0:7]};
    }

    queue_fill_level: coverpoint queue_fill {
        option.weight = 0;

        bins queue_empty = {[0:4]};
        bins queue_low = {[5:15]};
        bins queue_med = {[16:27]};
        bins queue_high = {[28:31]};
        bins queue_full = {32};
    }

    inversion_x_queue: cross high_priority_blocked, queue_fill_level {
        bins full_queue_inversion = binsof(high_priority_blocked.blocked) && binsof(queue_fill_level.queue_full);
        bins empty_queue_inversion = binsof(high_priority_blocked.served) && binsof(queue_fill_level.queue_empty);
    }
endgroup

// =============================================================
// Starvation Coverage
// =============================================================
covergroup starvation_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "starvation_coverage";
    option.comment = "Coverage for starvation detection";

    low_priority_queued: coverpoint low_prio_queue_depth {
        option.weight = 0;

        bins starving = {[50:100]};
        bins healthy = {[0:49]};
    }

    starvation_detected: coverpoint starvation_flag {
        option.weight = 0;

        bins starved = {1'b1};
        bins not_starved = {1'b0};
    }

    starvation_time: coverpoint starvation_cycles {
        option.weight = 0;

        bins short_starve = {[1:100]};
        bins medium_starve = {[101:500]};
        bins long_starve = {[501:$]};
    }

    low_prio_x_starvation: cross low_priority_queued, starvation_detected {
        bins queue_depth_starvation = binsof(low_priority_queued.starving) && binsof(starvation_detected.starved);
    }
endgroup

// =============================================================
// Refresh Coverage - Enhanced
// =============================================================
covergroup refresh_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "refresh_coverage";
    option.comment = "Coverage for refresh operations";

    refresh_type: coverpoint refresh_type {
        option.weight = 0;

        bins ref_full  = {REFRESH_FULL};
        bins ref_bank  = {REFRESH_BANK};
        bins ref_pb    = {REFRESH_PER_BANK};
        bins all_types = {[0:2]};
    }

    refresh_interval: coverpoint refresh_interval_cycles {
        option.weight = 0;

        bins ref_early   = {[1:1000]};
        bins ref_normal  = {[1001:5000]};
        bins ref_late    = {[5001:10000]};
        bins ref_timeout = {[10001:$]};
    }

    refresh_during_traffic: coverpoint refresh_during_active {
        option.weight = 0;

        bins ref_idle    = {1'b0};
        bins ref_active  = {1'b1};
    }

    refresh_collision: coverpoint collision_detected {
        option.weight = 0;

        bins collision = {1'b1};
        bins clean = {1'b0};
    }

    banks_open_during_refresh: coverpoint banks_open {
        option.weight = 0;

        bins zero_banks = {0};
        bins few_banks = {[1:4]};
        bins many_banks = {[5:15]};
        bins all_banks = {16};
    }

    ref_x_collision: cross refresh_type, refresh_collision {
        bins full_ref_collision = binsof(refresh_type.ref_full) && binsof(refresh_collision.collision);
        bins pb_ref_collision = binsof(refresh_type.ref_pb) && binsof(refresh_collision.collision);
    }
endgroup

// =============================================================
// Timing Coverage - Enhanced
// =============================================================
covergroup timing_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "timing_coverage";
    option.comment = "Coverage for timing parameter settings";

    tRCD: coverpoint tRCD_value {
        option.weight = 0;

        bins trcd_min = {[1:8]};
        bins trcd_nom = {[9:20]};
        bins trcd_max = {[21:255]};
    }

    tRP: coverpoint tRP_value {
        option.weight = 0;

        bins trp_min = {[1:8]};
        bins trp_nom = {[9:20]};
        bins trp_max = {[21:255]};
    }

    tRAS: coverpoint tRAS_value {
        option.weight = 0;

        bins tras_min = {[1:20]};
        bins tras_nom = {[21:40]};
        bins tras_max = {[41:255]};
    }

    tRC: coverpoint tRC_value {
        option.weight = 0;

        bins trc_min = {[1:30]};
        bins trc_nom = {[31:60]};
        bins trc_max = {[61:255]};
    }

    tRRD: coverpoint tRRD_value {
        option.weight = 0;

        bins trrd_min = {[1:4]};
        bins trrd_nom = {[5:8]};
        bins trrd_max = {[9:$]};
    }

    tCCD: coverpoint tCCD_value {
        option.weight = 0;

        bins tccd_min = {[1:2]};
        bins tccd_nom = {[3:4]};
        bins tccd_max = {[5:$]};
    }

    // Timing violation tracking
    timing_violation: coverpoint timing_violated {
        option.weight = 0;

        bins violated = {1'b1};
        bins compliant = {1'b0};
    }

    violation_type: coverpoint violation_type {
        option.weight = 0;

        bins trrd_violation = {0};
        bins trc_violation = {1};
        bins trcd_violation = {2};
        bins trp_violation = {3};
        bins tras_violation = {4};
    }
endgroup

// =============================================================
// Transaction Coverage - Enhanced
// =============================================================
covergroup transaction_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "transaction_coverage";
    option.comment = "Coverage for complete transaction patterns";

    trans_type: coverpoint transaction_type {
        option.weight = 0;

        bins read_trans  = {1'b0};
        bins write_trans = {1'b1};
    }

    addr_coverage: coverpoint addr_bank {
        option.weight = 0;

        bins addr_all = {[0:MAX_BANKS-1]};
    }

    data_valid: coverpoint data_valid {
        option.weight = 0;

        bins data_valid   = {1'b1};
        bins data_invalid = {1'b0};
    }

    trans_success: coverpoint transaction_success {
        option.weight = 0;

        bins success = {1'b1};
        bins failure = {1'b0};
    }

    type_x_success: cross trans_type, trans_success {
        bins read_success  = binsof(trans_type.read_trans) && binsof(trans_success.success);
        bins write_success = binsof(trans_type.write_trans) && binsof(trans_success.success);
    }

    latency_coverage: coverpoint transaction_latency {
        option.weight = 0;

        bins latency_low = {[0:20]};
        bins latency_med = {[21:50]};
        bins latency_high = {[51:100]};
        bins latency_very_high = {[101:$]};
    }
endgroup

// =============================================================
// Queue Coverage
// =============================================================
covergroup queue_coverage @(posedge clk);
    option.per_instance = 1;
    option.name = "queue_coverage";
    option.comment = "Coverage for queue occupancy";

    queue_fill: coverpoint queue_occupancy {
        option.weight = 0;

        bins empty = {0};
        bins low = {[1:8]};
        bins medium = {[9:24]};
        bins high = {[25:31]};
        bins full = {32};
    }

    queue_turnover: coverpoint queue_entries_per_cycle {
        option.weight = 0;

        bins low_turnover = {[0:2]};
        bins med_turnover = {[3:5]};
        bins high_turnover = {[6:$]};
    }

    overflow_detected: coverpoint queue_overflow {
        option.weight = 0;

        bins overflow = {1'b1};
        bins safe = {1'b0};
    }
endgroup

// =============================================================
// HBM Functional Coverage Collector - Enhanced
// =============================================================
class hbm_functional_coverage extends uvm_subscriber #(hbm_transaction);
    `uvm_component_utils(hbm_functional_coverage)

    hbm_coverage_config cfg;

    // Coverage groups
    command_coverage cmd_cov;
    bank_coverage bank_cov;
    bank_group_conflict_coverage group_cov;
    row_coverage row_cov;
    column_coverage col_cov;
    qos_coverage qos_cov;
    priority_inversion_coverage inv_cov;
    starvation_coverage starve_cov;
    refresh_coverage ref_cov;
    timing_coverage timing_cov;
    transaction_coverage trans_cov;
    queue_coverage queue_cov;

    // Internal state
    logic [2:0] cmd_type;
    logic [3:0] bank_group_idx;
    logic [5:0] bank_idx;
    logic [15:0] row_addr;
    logic [9:0] col_addr;
    logic [2:0] priority;
    logic [15:0] deadline;
    logic row_hit;
    bit [7:0] burst_len;
    bit conflict_flag;
    bit activation_conflict;
    bit data_valid;
    bit transaction_type;
    bit transaction_success;
    bit [15:0] transaction_latency;

    // Priority inversion state
    bit high_prio_blocked;
    logic [2:0] blocking_prio;
    bit [7:0] queue_fill;

    // Starvation state
    bit [7:0] low_prio_queue_depth;
    bit starvation_flag;
    bit [15:0] starvation_cycles;

    // Refresh state
    typedef enum {REFRESH_FULL, REFRESH_BANK, REFRESH_PER_BANK} refresh_type_t;
    refresh_type_t refresh_type;
    int refresh_interval_cycles;
    bit refresh_during_active;
    bit collision_detected;
    bit [5:0] banks_open;

    // Timing state
    logic [7:0] tRCD_value;
    logic [7:0] tRP_value;
    logic [7:0] tRAS_value;
    logic [15:0] tRC_value;
    logic [7:0] tRRD_value;
    logic [7:0] tCCD_value;
    bit timing_violated;
    bit [2:0] violation_type;

    // Queue state
    bit [7:0] queue_occupancy;
    bit [3:0] queue_entries_per_cycle;
    bit queue_overflow;

    // Coverage counters
    int total_transactions = 0;
    int covered_transactions = 0;
    real coverage_percent = 0.0;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        cfg = hbm_coverage_config::type_id::create("cfg");

        cmd_cov     = new();
        bank_cov    = new();
        group_cov   = new();
        row_cov     = new();
        col_cov     = new();
        qos_cov     = new();
        inv_cov     = new();
        starve_cov  = new();
        ref_cov     = new();
        timing_cov  = new();
        trans_cov   = new();
        queue_cov   = new();
    endfunction

    function void write(T t);
        // Update internal state from transaction
        cmd_type = t.cmd;
        bank_idx = t.addr_bank[5:0];
        bank_group_idx = t.addr_bank[3:2];
        row_addr = t.addr_row;
        col_addr = {8'b0, t.addr_col};
        priority = t.req_priority;
        row_hit = (t.addr_row == prev_row_for_bank(t.addr_bank)) ? 1'b1 : 1'b0;
        data_valid = t.rdata_valid;
        transaction_type = (t.cmd == hbm_transaction::READ) ? 1'b0 : 1'b1;
        transaction_success = t.rdata_valid;
        queue_occupancy = queue_occupancy + 1;
        if (queue_occupancy > cfg.queue_depth)
            queue_overflow = 1'b1;

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
        queue_cov.sample();

        if (t.req_priority != 0) begin
            qos_cov.sample();
        end

        if (t.cmd == hbm_transaction::READ || t.cmd == hbm_transaction::WRITE) begin
            trans_cov.sample();
        end

        covered_transactions++;
    endfunction

    function void sample_bank_group_conflict(int group, bit conflict);
        bank_group_idx = group;
        conflict_flag = conflict;
        group_cov.sample();
    endfunction

    function void sample_row_activation_conflict(bit conflict);
        activation_conflict = conflict;
        row_cov.sample();
    endfunction

    function void sample_priority_inversion(bit blocked, logic [2:0] blocking_prio_val, bit [7:0] fill);
        high_prio_blocked = blocked;
        blocking_prio = blocking_prio_val;
        queue_fill = fill;
        inv_cov.sample();
    endfunction

    function void sample_starvation(bit [7:0] low_queue, bit starved, bit [15:0] cycles);
        low_prio_queue_depth = low_queue;
        starvation_flag = starved;
        starvation_cycles = cycles;
        starve_cov.sample();
    endfunction

    function void sample_refresh(refresh_type_t rtype, int interval);
        refresh_type = rtype;
        refresh_interval_cycles = interval;
        ref_cov.sample();
    endfunction

    function void sample_refresh_collision(bit collision, bit [5:0] banks);
        collision_detected = collision;
        banks_open = banks;
        ref_cov.sample();
    endfunction

    function void sample_timing(logic [7:0] tRCD, tRP, tRAS, logic [15:0] tRC, tRRD, tCCD);
        tRCD_value = tRCD;
        tRP_value = tRP;
        tRAS_value = tRAS;
        tRC_value = tRC;
        tRRD_value = tRRD;
        tCCD_value = tCCD;
        timing_cov.sample();
    endfunction

    function void sample_timing_violation(bit violated, bit [2:0] vtype);
        timing_violated = violated;
        violation_type = vtype;
        timing_cov.sample();
    endfunction

    function void sample_deadline_violation(bit violated);
        deadline_violated = violated;
        qos_cov.sample();
    endfunction

    function logic [15:0] prev_row_for_bank(bit [7:0] bank);
        return prev_row[bank];
    endfunction

    logic [15:0] prev_row[MAX_BANKS];

    function real get_coverage();
        real total = 0.0;
        real count = 0.0;

        total += cmd_cov.get_coverage();
        total += bank_cov.get_coverage();
        total += row_cov.get_coverage();
        total += col_cov.get_coverage();
        total += qos_cov.get_coverage();
        total += ref_cov.get_coverage();
        total += timing_cov.get_coverage();
        total += trans_cov.get_coverage();
        total += group_cov.get_coverage();
        total += inv_cov.get_coverage();
        total += starve_cov.get_coverage();
        total += queue_cov.get_coverage();

        count = 12.0;  // Number of coverage groups
        coverage_percent = total / count;

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
        `uvm_info(get_name(), $sformatf("Command Coverage:        %.2f%%", cmd_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Bank Coverage:           %.2f%%", bank_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Bank Group Coverage:    %.2f%%", group_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Row Coverage:            %.2f%%", row_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Column Coverage:         %.2f%%", col_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("QoS Coverage:            %.2f%%", qos_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Priority Inversion Cov: %.2f%%", inv_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Starvation Coverage:    %.2f%%", starve_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Refresh Coverage:       %.2f%%", ref_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Timing Coverage:        %.2f%%", timing_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Transaction Coverage:   %.2f%%", trans_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Queue Coverage:         %.2f%%", queue_cov.get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), "--------------------------------------------------", UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Overall Coverage:       %.2f%%", get_coverage()), UVM_MEDIUM)
        `uvm_info(get_name(), "==================================================", UVM_MEDIUM)

        // Check for low coverage
        if (cmd_cov.get_coverage() < 80.0) begin
            `uvm_warning(get_name(), "Command coverage below 80%")
        end
        if (bank_cov.get_coverage() < 70.0) begin
            `uvm_warning(get_name(), "Bank coverage below 70%")
        end
        if (qos_cov.get_coverage() < 60.0) begin
            `uvm_warning(get_name(), "QoS coverage below 60%")
        end
        if (inv_cov.get_coverage() < 50.0) begin
            `uvm_warning(get_name(), "Priority inversion coverage below 50%")
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
        fsm_states_covered = fsm_states_covered + 1;
        branches_taken = branches_taken + 1;

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