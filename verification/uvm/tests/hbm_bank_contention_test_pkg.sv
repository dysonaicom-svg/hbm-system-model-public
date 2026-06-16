// ------------------------------------------------------------
// hbm_bank_contention_test_pkg.sv - HBM Bank Contention Test Package
// Tests bank arbitration, bank conflicts, and bank scheduling
// ------------------------------------------------------------
package hbm_bank_contention_test_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Bank Contention Transaction
// ------------------------------------------------------------
class hbm_bank_contention_transaction extends hbm_transaction;
    `uvm_object_utils(hbm_bank_contention_transaction)

    rand bit [3:0] target_bank_group;  // Bank group targeting
    rand bit [15:0] expected_latency;   // Expected access latency
    bit [15:0] actual_latency;          // Actual observed latency

    constraint bank_group_range {
        target_bank_group < 8;  // HBM4 has 8 bank groups
    }

    function new(string name = "hbm_bank_contention_transaction");
        super.new(name);
    endfunction

    function string convert2string();
        return {
            super.convert2string(),
            $sformatf(" bg=%h latency_exp=%0d latency_act=%0d",
                      target_bank_group, expected_latency, actual_latency)
        };
    endfunction
endclass

// ------------------------------------------------------------
// Base Bank Contention Sequence
// ------------------------------------------------------------
class hbm_bank_contention_base_sequence extends hbm_base_sequence;
    `uvm_object_utils(hbm_bank_contention_base_sequence)

    int num_banks = 16;
    int num_bank_groups = 8;

    function new(string name = "hbm_bank_contention_base_sequence");
        super.new(name);
    endfunction
endclass

// ------------------------------------------------------------
// Bank Group Conflict Test Sequence
// Tests access conflicts within the same bank group
// ------------------------------------------------------------
class bank_group_conflict_seq extends hbm_bank_contention_base_sequence;
    `uvm_object_utils(bank_group_conflict_seq)

    int requests_per_bank_group = 20;
    int num_bank_groups_tested = 8;

    function new(string name = "bank_group_conflict_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int conflicts_detected = 0;
        int total_requests = 0;

        `uvm_info(get_name(), "Starting bank group conflict test", UVM_MEDIUM)

        // Test each bank group
        for (int bg = 0; bg < num_bank_groups_tested; bg++) begin
            `uvm_info(get_name(), $sformatf("Testing bank group %0d", bg), UVM_MEDIUM)

            // Issue consecutive requests to banks in the same group
            for (int i = 0; i < requests_per_bank_group; i++) begin
                // Each group has 2 banks (16 banks / 8 groups)
                bit [3:0] bank_in_group = (bg * 2) + (i % 2);
                bit [15:0] row = i / 2;

                req = new("req");
                start_item(req);

                if (!req.randomize() with {
                    addr_bank == bank_in_group;
                    addr_row  == row;
                }) begin
                    `uvm_error(get_name(), "Randomization failed")
                end
                req.transaction_id = get_next_id();
                req.target_bank_group = bg;

                `uvm_info(get_name(), $sformatf("Bank group %0d: bank=%h row=%h",
                                                 bg, bank_in_group, row), UVM_DEBUG)
                finish_item(req);
                total_requests++;

                // Check for tRRD violation (same bank group activation delay)
                if (i > 0 && i % 2 == 0) begin
                    // Simulated conflict detection
                    if ($urandom() % 100 < 10) begin  // 10% simulated conflict rate
                        conflicts_detected++;
                        `uvm_warning(get_name(), $sformatf("Bank group %0d conflict at request %0d", bg, i))
                    end
                end

                #5;
            end

            // Small delay between bank groups
            #50;
        end

        `uvm_info(get_name(), $sformatf("Bank group test: total=%0d conflicts=%0d",
                                        total_requests, conflicts_detected), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Bank Activation Conflict Test Sequence
// Tests conflicts when activating already-active banks
// ------------------------------------------------------------
class bank_activation_conflict_seq extends hbm_bank_contention_base_sequence;
    `uvm_object_utils(bank_activation_conflict_seq)

    int banks_to_test = 16;
    int activations_per_bank = 5;

    function new(string name = "bank_activation_conflict_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int conflict_count = 0;
        int success_count = 0;

        `uvm_info(get_name(), "Starting bank activation conflict test", UVM_MEDIUM)

        for (int bank = 0; bank < banks_to_test; bank++) begin
            for (int act = 0; act < activations_per_bank; act++) begin
                req = new("req");
                start_item(req);

                if (!req.randomize() with {
                    cmd == hbm_transaction::WRITE;
                    addr_bank == bank;
                    addr_row  == act;  // Different row each activation
                }) begin
                    `uvm_error(get_name(), "Randomization failed")
                end
                req.transaction_id = get_next_id();

                `uvm_info(get_name(), $sformatf("Bank %0d activation %0d to row %0d",
                                                 bank, act, act), UVM_HIGH)
                finish_item(req);

                // Check for tRC violation (same bank activation delay)
                if (act > 0) begin
                    success_count++;
                    if ($urandom() % 100 < 5) begin  // 5% simulated conflict
                        conflict_count++;
                        `uvm_warning(get_name(), $sformatf("tRC conflict: bank %0d activation %0d", bank, act))
                    end
                end

                #20;  // Simulated tRC delay
            end

            // Precharge before next test
            #50;
        end

        `uvm_info(get_name(), $sformatf("Activation test: success=%0d conflicts=%0d",
                                        success_count, conflict_count), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Bank Round-Robin Test Sequence
// Tests fair bank arbitration with round-robin scheduling
// ------------------------------------------------------------
class bank_round_robin_seq extends hbm_bank_contention_base_sequence;
    `uvm_object_utils(bank_round_robin_seq)

    int num_requests_per_bank = 10;
    int banks_to_test = 16;

    function new(string name = "bank_round_robin_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int request_count_per_bank[16];
        int arbitration_count = 0;
        int last_served_bank = -1;
        int fairness_violations = 0;

        // Initialize counters
        for (int i = 0; i < 16; i++) begin
            request_count_per_bank[i] = 0;
        end

        `uvm_info(get_name(), "Starting round-robin bank test", UVM_MEDIUM)

        // Generate interleaved requests to all banks
        for (int round = 0; round < num_requests_per_bank; round++) begin
            for (int bank = 0; bank < banks_to_test; bank++) begin
                req = new("req");
                start_item(req);

                if (!req.randomize() with {
                    addr_bank == bank;
                    addr_row  == round;
                }) begin
                    `uvm_error(get_name(), "Randomization failed")
                end
                req.transaction_id = get_next_id();

                request_count_per_bank[bank]++;
                arbitration_count++;

                // Check for fair arbitration (no starvation)
                if (last_served_bank >= 0 && bank > last_served_bank + 8) begin
                    fairness_violations++;
                    `uvm_warning(get_name(), $sformatf("Fairness violation: bank %0d skipped", bank))
                end
                last_served_bank = bank;

                `uvm_info(get_name(), $sformatf("Round-robin: bank=%0d round=%0d", bank, round), UVM_DEBUG)
                finish_item(req);
                #10;
            end
        end

        `uvm_info(get_name(), $sformatf("Round-robin test: arbitration=%0d fairness_violations=%0d",
                                        arbitration_count, fairness_violations), UVM_MEDIUM)

        // Print per-bank statistics
        for (int i = 0; i < banks_to_test; i++) begin
            `uvm_info(get_name(), $sformatf("Bank %0d requests: %0d", i, request_count_per_bank[i]), UVM_HIGH)
        end
    endtask
endclass

// ------------------------------------------------------------
// Bank Open/Close Conflict Test Sequence
// Tests precharge conflicts and row close timing
// ------------------------------------------------------------
class bank_open_close_seq extends hbm_bank_contention_base_sequence;
    `uvm_object_utils(bank_open_close_seq)

    int num_banks = 16;
    int operations_per_bank = 10;

    function new(string name = "bank_open_close_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int open_count = 0;
        int close_count = 0;
        int conflict_count = 0;

        `uvm_info(get_name(), "Starting bank open/close conflict test", UVM_MEDIUM)

        for (int bank = 0; bank < num_banks; bank++) begin
            for (int op = 0; op < operations_per_bank; op++) begin
                req = new("req");
                start_item(req);

                if (!req.randomize() with {
                    addr_bank == bank;
                    addr_row  == op;
                }) begin
                    `uvm_error(get_name(), "Randomization failed")
                end
                req.transaction_id = get_next_id();

                `uvm_info(get_name(), $sformatf("Bank %0d operation %0d: row=%0d",
                                                 bank, op, op), UVM_HIGH)
                finish_item(req);

                open_count++;

                // Simulate precharge after each operation
                if (op % 3 == 0) begin
                    // Check for tRAS violation (precharge too soon)
                    if ($urandom() % 100 < 3) begin  // 3% simulated violation
                        conflict_count++;
                        `uvm_warning(get_name(), $sformatf("tRAS violation: bank %0d op %0d", bank, op))
                    end
                    close_count++;
                    #20;
                end

                #10;
            end
        end

        `uvm_info(get_name(), $sformatf("Open/close test: open=%0d close=%0d conflicts=%0d",
                                        open_count, close_count, conflict_count), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Cross-Bank Scheduling Test Sequence
// Tests scheduling across multiple banks with dependencies
// ------------------------------------------------------------
class cross_bank_scheduling_seq extends hbm_bank_contention_base_sequence;
    `uvm_object_utils(cross_bank_scheduling_seq)

    int num_requests = 100;
    int banks_to_use = 16;

    function new(string name = "cross_bank_scheduling_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int scheduled_count = 0;
        int delayed_count = 0;
        int queue_full_count = 0;

        `uvm_info(get_name(), "Starting cross-bank scheduling test", UVM_MEDIUM)

        for (int i = 0; i < num_requests; i++) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                addr_bank == (i % banks_to_use);
                addr_row  == i;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();

            `uvm_info(get_name(), $sformatf("Cross-bank schedule: req=%0d bank=%h row=%h",
                                             i, req.addr_bank, req.addr_row), UVM_DEBUG)
            finish_item(req);
            scheduled_count++;

            // Simulate scheduling delays
            if (i > 20 && i % 10 == 0) begin
                if ($urandom() % 100 < 15) begin  // 15% chance of delay
                    delayed_count++;
                end
                if ($urandom() % 100 < 5) begin  // 5% chance of queue full
                    queue_full_count++;
                    `uvm_warning(get_name(), $sformatf("Queue full at request %0d", i))
                end
            end

            #5;
        end

        `uvm_info(get_name(), $sformatf("Cross-bank scheduling: scheduled=%0d delayed=%0d queue_full=%0d",
                                        scheduled_count, delayed_count, queue_full_count), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Bank Contention Stress Test Sequence
// High-stress test with maximum bank utilization
// ------------------------------------------------------------
class bank_contention_stress_seq extends hbm_bank_contention_base_sequence;
    `uvm_object_utils(bank_contention_stress_seq)

    int total_requests = 500;
    int banks = 16;

    function new(string name = "bank_contention_stress_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int request_id = 0;
        int bank_busy_count = 0;
        int total_wait_cycles = 0;
        int max_wait_cycles = 0;
        int wait_cycles = 0;

        `uvm_info(get_name(), "Starting bank contention stress test", UVM_MEDIUM)

        // Generate high-stress traffic pattern
        for (int i = 0; i < total_requests; i++) begin
            req = new("req");
            start_item(req);

            // Random bank and row selection for maximum contention
            if (!req.randomize()) begin
                `uvm_error(get_name(), "Stress randomization failed")
            end
            req.transaction_id = get_next_id();
            request_id++;

            `uvm_info(get_name(), $sformatf("Stress request %0d: bank=%h", request_id, req.addr_bank),
                      UVM_DEBUG)
            finish_item(req);

            // Track simulated wait times
            wait_cycles = $urandom() % 100;
            total_wait_cycles += wait_cycles;
            if (wait_cycles > max_wait_cycles) begin
                max_wait_cycles = wait_cycles;
            end

            if (wait_cycles > 50) begin
                bank_busy_count++;
            end

            #($urandom() % 20 + 5);  // Random inter-request delay
        end

        `uvm_info(get_name(), $sformatf("Bank stress: requests=%0d busy=%0d avg_wait=%0d max_wait=%0d",
                                        total_requests, bank_busy_count,
                                        total_wait_cycles / total_requests, max_wait_cycles),
                  UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Bank Group Conflict Test
// ------------------------------------------------------------
class hbm_bank_group_conflict_test extends hbm_base_test;
    `uvm_component_utils(hbm_bank_group_conflict_test)

    function new(string name = "hbm_bank_group_conflict_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        bank_group_conflict_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = bank_group_conflictnew("seq");
        seq.requests_per_bank_group = 15;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Bank Activation Conflict Test
// ------------------------------------------------------------
class hbm_bank_activation_conflict_test extends hbm_base_test;
    `uvm_component_utils(hbm_bank_activation_conflict_test)

    function new(string name = "hbm_bank_activation_conflict_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        bank_activation_conflict_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = bank_activation_conflictnew("seq");
        seq.banks_to_test = 8;
        seq.activations_per_bank = 3;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Bank Round-Robin Test
// ------------------------------------------------------------
class hbm_bank_round_robin_test extends hbm_base_test;
    `uvm_component_utils(hbm_bank_round_robin_test)

    function new(string name = "hbm_bank_round_robin_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        bank_round_robin_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = bank_round_robinnew("seq");
        seq.num_requests_per_bank = 8;
        seq.banks_to_test = 16;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Bank Open/Close Conflict Test
// ------------------------------------------------------------
class hbm_bank_open_close_test extends hbm_base_test;
    `uvm_component_utils(hbm_bank_open_close_test)

    function new(string name = "hbm_bank_open_close_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        bank_open_close_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = bank_open_closenew("seq");
        seq.num_banks = 16;
        seq.operations_per_bank = 8;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Cross-Bank Scheduling Test
// ------------------------------------------------------------
class hbm_cross_bank_scheduling_test extends hbm_base_test;
    `uvm_component_utils(hbm_cross_bank_scheduling_test)

    function new(string name = "hbm_cross_bank_scheduling_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        cross_bank_scheduling_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = cross_bank_schedulingnew("seq");
        seq.num_requests = 100;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Bank Contention Stress Test
// ------------------------------------------------------------
class hbm_bank_contention_stress_test extends hbm_base_test;
    `uvm_component_utils(hbm_bank_contention_stress_test)

    function new(string name = "hbm_bank_contention_stress_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        bank_contention_stress_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = bank_contention_stressnew("seq");
        seq.total_requests = 200;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

endpackage : hbm_bank_contention_test_pkg