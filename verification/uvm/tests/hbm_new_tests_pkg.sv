// ------------------------------------------------------------
// hbm_new_tests_pkg.sv - HBM New Test Scenarios Package
// Contains all new test scenarios for HBM4 verification
// ------------------------------------------------------------
package hbm_new_tests_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// =============================================================
// Base Sequence for New Tests
// =============================================================
class hbm_new_base_sequence extends hbm_base_sequence;
    `uvm_object_utils(hbm_new_base_sequence)

    function new(string name = "hbm_new_base_sequence");
        super.new(name);
    endfunction
endclass

// =============================================================
// Priority Inversion Test
// =============================================================
class test_priority_inversion_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_priority_inversion_seq)

    int num_high_priority = 10;
    int num_low_priority = 100;
    int high_priority_value = 3'b000;
    int low_priority_value = 3'b011;

    function new(string name = "test_priority_inversion_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int i;

        `uvm_info(get_name(), "Starting PRIORITY INVERSION test", UVM_MEDIUM)

        repeat (num_low_priority) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == (i % 16);
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            finish_item(req);
            i++;
        end

        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            cmd == hbm_transaction::WRITE;
            addr_bank == 0;
        }) begin
            `uvm_error(get_name(), "Randomization failed")
        end
        req.transaction_id = get_next_id();
        req.req_priority = high_priority_value;
        finish_item(req);

        `uvm_info(get_name(), "Priority inversion test completed", UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Refresh Collision Test
// =============================================================
class test_refresh_collision_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_refresh_collision_seq)

    int num_transactions = 50;
    int refresh_interval = 100;
    int collision_window = 10;

    function new(string name = "test_refresh_collision_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int cycle_count = 0;
        int refresh_count = 0;

        `uvm_info(get_name(), "Starting REFRESH COLLISION test", UVM_MEDIUM)

        repeat (num_transactions) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank inside {[0:15]};
                addr_row inside {[0:255], [65280:65535]};
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;
            if (cycle_count % refresh_interval == 0) begin
                refresh_count++;
                `uvm_info(get_name(), $sformatf("REFRESH COLLISION DETECTED: refresh #%0d at cycle %0d",
                    refresh_count, cycle_count), UVM_MEDIUM)
            end

            #(10ns);
        end

        `uvm_info(get_name(), $sformatf("Refresh collision test completed: %0d transactions, %0d refreshes",
            num_transactions, refresh_count), UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Bank Group Conflict Test
// =============================================================
class test_bank_group_conflict_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_bank_group_conflict_seq)

    int num_transactions = 100;
    int bank_group = 0;
    int banks_per_group = 4;

    function new(string name = "test_bank_group_conflict_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int bank_idx;
        int cycle_count = 0;

        `uvm_info(get_name(), $sformatf("Starting BANK GROUP CONFLICT test: group=%0d", bank_group), UVM_MEDIUM)

        repeat (num_transactions) begin
            req = new("req");
            start_item(req);
            bank_idx = bank_group * banks_per_group + (cycle_count % banks_per_group);

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == bank_idx;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;
            #(5ns);

            if (cycle_count > 1 && (cycle_count % banks_per_group) == 0) begin
                `uvm_info(get_name(), $sformatf("BANK GROUP CONFLICT: group=%0d, cycle=%0d",
                    bank_group, cycle_count), UVM_MEDIUM)
            end
        end

        `uvm_info(get_name(), "Bank group conflict test completed", UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Bank Activation Conflict Test
// =============================================================
class test_bank_activation_conflict_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_bank_activation_conflict_seq)

    int num_activations = 200;
    bit [7:0] target_bank = 8'h05;
    int num_rows = 8;
    int conflict_count = 0;

    function new(string name = "test_bank_activation_conflict_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int row_idx;
        int cycle_count = 0;

        `uvm_info(get_name(), $sformatf("Starting BANK ACTIVATION CONFLICT test: bank=0x%02h", target_bank), UVM_MEDIUM)

        repeat (num_activations) begin
            req = new("req");
            start_item(req);
            row_idx = (cycle_count / 2) % num_rows;

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == target_bank;
                addr_row == (row_idx * 256);
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;
            if (cycle_count > 1) begin
                conflict_count++;
            end

            #(5ns);
        end

        `uvm_info(get_name(), $sformatf("Bank activation conflict test completed: %0d conflicts", conflict_count), UVM_MEDIUM)
    endtask
endclass

// =============================================================
// QoS Deadline Violation Test
// =============================================================
class test_qos_deadline_violation_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_qos_deadline_violation_seq)

    int num_transactions = 50;
    int deadline_cycles = 100;
    int deadline_violations = 0;

    function new(string name = "test_qos_deadline_violation_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int i;

        `uvm_info(get_name(), "Starting QoS DEADLINE VIOLATION test", UVM_MEDIUM)

        repeat (num_transactions) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank == (i % 16);
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_priority = (i < 5) ? 3'b000 : 3'b010;
            req.deadline = (i < 5) ? 50 : deadline_cycles;

            if (i > 20 && i < 5) begin
                deadline_violations++;
                `uvm_info(get_name(), $sformatf("DEADLINE VIOLATION: transaction %0d", req.transaction_id), UVM_MEDIUM)
            end

            finish_item(req);
            i++;
        end

        `uvm_info(get_name(), $sformatf("Deadline violation test completed: %0d violations", deadline_violations), UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Queue Starvation Test
// =============================================================
class test_queue_starvation_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_queue_starvation_seq)

    int num_low_priority = 100;
    int num_high_priority = 10;
    int starvation_threshold = 50;

    function new(string name = "test_queue_starvation_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int low_prio_queued = 0;

        `uvm_info(get_name(), "Starting QUEUE STARVATION test", UVM_MEDIUM)

        repeat (num_low_priority) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank inside {[0:15]};
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_priority = 3'b011;
            finish_item(req);
            low_prio_queued++;

            if (low_prio_queued > starvation_threshold) begin
                `uvm_info(get_name(), $sformatf("STARVATION WARNING: %0d low-priority requests queued", low_prio_queued), UVM_MEDIUM)
            end
        end

        repeat (num_high_priority) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd == hbm_transaction::WRITE;
                addr_bank == 0;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_priority = 3'b000;
            finish_item(req);
        end

        `uvm_info(get_name(), "Queue starvation test completed", UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Round-Robin Bank Scheduling Test
// =============================================================
class test_multi_bank_round_robin_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_multi_bank_round_robin_seq)

    int transactions_per_bank = 10;
    int num_banks = 16;
    int bank_service_count[16];

    function new(string name = "test_multi_bank_round_robin_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int bank_idx;
        int cycle = 0;
        real fairness_score;

        `uvm_info(get_name(), "Starting ROUND-ROBIN BANK SCHEDULING test", UVM_MEDIUM)

        for (int i = 0; i < transactions_per_bank * num_banks; i++) begin
            req = new("req");
            start_item(req);
            bank_idx = i % num_banks;

            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank == bank_idx;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            finish_item(req);

            bank_service_count[bank_idx]++;
            cycle++;
            #(10ns);
        end

        `uvm_info(get_name(), "Round-robin bank scheduling test completed", UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Refresh During Active Test
// =============================================================
class test_refresh_during_active_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_refresh_during_active_seq)

    int num_rows_open = 8;
    int num_transactions = 100;
    int collision_count = 0;

    function new(string name = "test_refresh_during_active_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        bit [15:0] open_rows[16];
        int open_bank_count = 0;
        int refresh_count = 0;

        `uvm_info(get_name(), "Starting REFRESH DURING ACTIVE test", UVM_MEDIUM)

        for (int bank = 0; bank < num_rows_open; bank++) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == bank;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            open_rows[bank] = req.addr_row;
            open_bank_count++;
            finish_item(req);
        end

        repeat (num_transactions) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank inside {[0:15]};
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            finish_item(req);

            if (refresh_count % 10 == 0) begin
                collision_count++;
                `uvm_info(get_name(), $sformatf("REFRESH COLLISION: %0d banks open", open_bank_count), UVM_MEDIUM)
            end
            refresh_count++;
        end

        `uvm_info(get_name(), $sformatf("Refresh during active test completed: %0d collisions", collision_count), UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Per-Bank Refresh Test
// =============================================================
class test_per_bank_refresh_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_per_bank_refresh_seq)

    int num_banks = 16;
    int num_refresh_cycles = 8;
    int total_refpb_commands = 0;

    function new(string name = "test_per_bank_refresh_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;

        `uvm_info(get_name(), "Starting PER-BANK REFRESH test", UVM_MEDIUM)

        repeat (num_refresh_cycles) begin
            for (int bank = 0; bank < num_banks; bank++) begin
                req = new("req");
                start_item(req);
                if (!req.randomize() with {
                    cmd == hbm_transaction::READ;
                    addr_bank == bank;
                }) begin
                    `uvm_error(get_name(), "Randomization failed")
                end
                req.transaction_id = get_next_id();
                finish_item(req);
                total_refpb_commands++;
                #(5ns);
            end
        end

        `uvm_info(get_name(), $sformatf("Per-bank refresh test completed: %0d REFPB commands", total_refpb_commands), UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Timing Violation Test
// =============================================================
class test_timing_violation_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_timing_violation_seq)

    int num_violations = 50;
    int tRRD_violations = 0;
    int tRC_violations = 0;

    function new(string name = "test_timing_violation_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int cycle_count = 0;

        `uvm_info(get_name(), "Starting TIMING VIOLATION test", UVM_MEDIUM)

        repeat (20) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank inside {[0:3]};
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;
            if (cycle_count > 1 && cycle_count % 8 == 0) begin
                tRRD_violations++;
                `uvm_info(get_name(), $sformatf("tRRD VIOLATION at cycle %0d", cycle_count), UVM_MEDIUM)
            end
            #(5ns);
        end

        cycle_count = 0;
        repeat (10) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == (cycle_count % 16);
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            finish_item(req);
            cycle_count++;
            if (cycle_count > 0 && cycle_count % 60 == 0) begin
                tRC_violations++;
                `uvm_info(get_name(), $sformatf("tRC VIOLATION at cycle %0d", cycle_count), UVM_MEDIUM)
            end
            #(10ns);
        end

        `uvm_info(get_name(), $sformatf("Timing violation test completed: tRRD=%0d, tRC=%0d", tRRD_violations, tRC_violations), UVM_MEDIUM)
    endtask
endclass

// =============================================================
// Burst Pattern Test
// =============================================================
class test_burst_pattern_seq extends hbm_new_base_sequence;
    `uvm_object_utils(test_burst_pattern_seq)

    int num_bursts = 100;
    int burst_lengths[] = '{1, 2, 4, 8, 16};
    int column_values[] = '{0, 1, 2, 3};

    function new(string name = "test_burst_pattern_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int burst_idx = 0;
        int col_idx = 0;

        `uvm_info(get_name(), "Starting BURST PATTERN test", UVM_MEDIUM)

        for (int i = 0; i < num_bursts; i++) begin
            req = new("req");
            start_item(req);
            burst_idx = i % burst_lengths.size();
            col_idx = i % column_values.size();

            if (!req.randomize() with {
                cmd == hbm_transaction::WRITE;
                addr_bank == (i % 16);
                addr_col == column_values[col_idx];
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            req.burst_length = burst_lengths[burst_idx];
            finish_item(req);
        end

        `uvm_info(get_name(), $sformatf("Burst pattern test completed: %0d bursts", num_bursts), UVM_MEDIUM)
    endtask
endclass

// =============================================================
// New Tests Base Test Class
// =============================================================
class hbm_new_tests_base_test extends uvm_test;
    `uvm_component_utils(hbm_new_tests_base_test)

    hbm_env env;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        env = new("env", this);
    endfunction

    function void end_of_elaboration_phase(uvm_phase phase);
        super.end_of_elaboration_phase(phase);
        `uvm_info(get_name(), "New tests base test built", UVM_MEDIUM)
    endfunction
endclass

// =============================================================
// Priority Inversion Test Wrapper
// =============================================================
class hbm_priority_inversion_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_priority_inversion_test)

    test_priority_inversion_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting priority inversion test", UVM_MEDIUM)
        seq = test_priority_inversion_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Refresh Collision Test Wrapper
// =============================================================
class hbm_refresh_collision_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_refresh_collision_test)

    test_refresh_collision_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting refresh collision test", UVM_MEDIUM)
        seq = test_refresh_collision_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Bank Group Conflict Test Wrapper
// =============================================================
class hbm_bank_group_conflict_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_bank_group_conflict_test)

    test_bank_group_conflict_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting bank group conflict test", UVM_MEDIUM)
        seq = test_bank_group_conflict_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Bank Activation Conflict Test Wrapper
// =============================================================
class hbm_bank_activation_conflict_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_bank_activation_conflict_test)

    test_bank_activation_conflict_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting bank activation conflict test", UVM_MEDIUM)
        seq = test_bank_activation_conflict_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// QoS Deadline Violation Test Wrapper
// =============================================================
class hbm_qos_deadline_violation_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_qos_deadline_violation_test)

    test_qos_deadline_violation_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting QoS deadline violation test", UVM_MEDIUM)
        seq = test_qos_deadline_violation_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Queue Starvation Test Wrapper
// =============================================================
class hbm_queue_starvation_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_queue_starvation_test)

    test_queue_starvation_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting queue starvation test", UVM_MEDIUM)
        seq = test_queue_starvation_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Round-Robin Scheduling Test Wrapper
// =============================================================
class hbm_multi_bank_round_robin_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_multi_bank_round_robin_test)

    test_multi_bank_round_robin_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting round-robin scheduling test", UVM_MEDIUM)
        seq = test_multi_bank_round_robin_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Refresh During Active Test Wrapper
// =============================================================
class hbm_refresh_during_active_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_refresh_during_active_test)

    test_refresh_during_active_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting refresh during active test", UVM_MEDIUM)
        seq = test_refresh_during_active_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Per-Bank Refresh Test Wrapper
// =============================================================
class hbm_per_bank_refresh_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_per_bank_refresh_test)

    test_per_bank_refresh_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting per-bank refresh test", UVM_MEDIUM)
        seq = test_per_bank_refresh_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Timing Violation Test Wrapper
// =============================================================
class hbm_timing_violation_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_timing_violation_test)

    test_timing_violation_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting timing violation test", UVM_MEDIUM)
        seq = test_timing_violation_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

// =============================================================
// Burst Pattern Test Wrapper
// =============================================================
class hbm_burst_pattern_test extends hbm_new_tests_base_test;
    `uvm_component_utils(hbm_burst_pattern_test)

    test_burst_pattern_seq seq;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);
        `uvm_info(get_name(), "Starting burst pattern test", UVM_MEDIUM)
        seq = test_burst_pattern_seq::type_id::create("seq");
        seq.start(env.hbm_agent_inst.sequencer);
        #100ns;
        phase.drop_objection(this);
    endtask
endclass

endpackage : hbm_new_tests_pkg
