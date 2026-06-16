// ------------------------------------------------------------
// hbm_qos_test_pkg.sv - HBM QoS Priority Test Package
// Tests QoS scheduling, priority inversion, and fairness
// ------------------------------------------------------------
package hbm_qos_test_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// QoS Priority Level Definitions
// ------------------------------------------------------------
typedef enum logic [2:0] {
    PRIO_CRITICAL = 3'b000,  // Highest priority - critical data
    PRIO_HIGH     = 3'b001,  // High priority
    PRIO_NORMAL   = 3'b010,  // Normal priority
    PRIO_LOW      = 3'b011,  // Low priority
    PRIO_IDLE     = 3'b111   // Idle/best-effort
} qos_priority_t;

// ------------------------------------------------------------
// QoS Transaction with Priority
// ------------------------------------------------------------
class hbm_qos_transaction extends hbm_transaction;
    `uvm_object_utils(hbm_qos_transaction)

    rand qos_priority_t qos_prio;
    rand bit [7:0] deadline;      // Relative deadline in cycles
    rand bit [15:0] flow_id;     // Flow identifier

    constraint deadline_range {
        deadline inside {[1:1000]};
    }

    function new(string name = "hbm_qos_transaction");
        super.new(name);
    endfunction

    function string convert2string();
        return {
            super.convert2string(),
            $sformatf(" qos_prio=%s deadline=%0d flow_id=%h",
                      qos_prio.name(), deadline, flow_id)
        };
    endfunction

    function void do_copy(uvm_object rhs);
        hbm_qos_transaction tr;
        super.do_copy(rhs);
        if ($cast(tr, rhs)) begin
            qos_prio = tr.qos_prio;
            deadline = tr.deadline;
            flow_id = tr.flow_id;
        end
    endfunction
endclass

// ------------------------------------------------------------
// Base QoS Sequence
// ------------------------------------------------------------
class hbm_qos_base_sequence extends hbm_base_sequence;
    `uvm_object_utils(hbm_qos_base_sequence)

    int high_prio_requests = 0;
    int low_prio_requests = 0;

    function new(string name = "hbm_qos_base_sequence");
        super.new(name);
    endfunction

    function void set_priorities(int high, int low);
        high_prio_requests = high;
        low_prio_requests = low;
    endfunction
endclass

// ------------------------------------------------------------
// Priority Inheritance Test Sequence
// Tests that high-priority requests are served first
// ------------------------------------------------------------
class qos_inheritance_seq extends hbm_qos_base_sequence;
    `uvm_object_utils(qos_inheritance_seq)

    int num_low_prio = 50;
    int num_high_prio = 10;
    int interleave_count = 10;

    function new(string name = "qos_inheritance_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;

        `uvm_info(get_name(), "Starting priority inheritance test", UVM_MEDIUM)

        // Send multiple low-priority requests first
        for (int i = 0; i < num_low_prio; i++) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == (i % 16);
                addr_row  == i;
                addr_col  == 0;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_qos_prio = 1'b0;  // Low priority
            `uvm_info(get_name(), $sformatf("Low priority request %0d", i), UVM_HIGH)
            finish_item(req);
            #5;
        end

        // Send high-priority requests interspersed with low-priority
        for (int i = 0; i < interleave_count; i++) begin
            // Low priority request
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == (i + 100);
            }) begin
                `uvm_error(get_name(), "Low priority randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_qos_prio = 1'b0;
            finish_item(req);
            #5;

            // High priority request (should be served first)
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == (i + 200);
            }) begin
                `uvm_error(get_name(), "High priority randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_qos_prio = 1'b1;  // High priority
            `uvm_info(get_name(), $sformatf("High priority request %0d", i), UVM_MEDIUM)
            finish_item(req);
            #5;
        end

        // Send remaining low-priority requests
        for (int i = 0; i < (num_low_prio - interleave_count); i++) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == (i + 300);
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_qos_prio = 1'b0;
            finish_item(req);
            #5;
        end

        `uvm_info(get_name(), "Priority inheritance test complete", UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Starvation Prevention Test Sequence
// Ensures low-priority requests don't starve
// ------------------------------------------------------------
class starvation_prevention_seq extends hbm_qos_base_sequence;
    `uvm_object_utils(starvation_prevention_seq)

    int num_high_prio = 100;
    int num_low_prio = 10;
    int max_wait_cycles = 500;

    function new(string name = "starvation_prevention_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int low_prio_started;
        int low_prio_completed;
        int high_prio_started;
        int high_prio_completed;

        `uvm_info(get_name(), "Starting starvation prevention test", UVM_MEDIUM)

        // Phase 1: Start low-priority requests
        for (int i = 0; i < num_low_prio; i++) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == i;
                addr_row  == 16'hAAAA;
            }) begin
                `uvm_error(get_name(), "Low priority randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_qos_prio = 1'b0;
            `uvm_info(get_name(), $sformatf("Started low-priority request %0d", i), UVM_HIGH)
            finish_item(req);
            low_prio_started++;
            #10;
        end

        // Phase 2: Continuous high-priority traffic
        fork
        begin
            for (int i = 0; i < num_high_prio; i++) begin
                req = new("req");
                start_item(req);
                if (!req.randomize() with {
                    addr_bank == (i % 16);
                }) begin
                    `uvm_error(get_name(), "High priority randomization failed")
                end
                req.transaction_id = get_next_id();
                req.req_qos_prio = 1'b1;
                finish_item(req);
                high_prio_started++;
                #5;
            end
        end
        join

        `uvm_info(get_name(), $sformatf("Starvation test: started=%0d high=%0d low=%0d",
                                         high_prio_started, low_prio_started,
                                         low_prio_completed), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Deadline Miss Test Sequence
// Tests deadline enforcement and miss detection
// ------------------------------------------------------------
class deadline_miss_seq extends hbm_qos_base_sequence;
    `uvm_object_utils(deadline_miss_seq)

    int num_requests = 50;
    int short_deadline = 20;   // Cycles
    int long_deadline = 200;   // Cycles

    function new(string name = "deadline_miss_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int deadline_misses = 0;
        int deadline_hits = 0;
        int is_short_deadline = 0;

        `uvm_info(get_name(), "Starting deadline miss test", UVM_MEDIUM)

        for (int i = 0; i < num_requests; i++) begin
            req = new("req");
            start_item(req);

            // Alternate between short and long deadlines
            is_short_deadline = (i % 2 == 0);

            if (!req.randomize() with {
                addr_bank == i;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();

            // Set priority based on deadline
            req.req_qos_prio = is_short_deadline ? 1'b1 : 1'b0;

            `uvm_info(get_name(), $sformatf("Request %0d: deadline=%0d cycles",
                                             i, is_short_deadline ? short_deadline : long_deadline),
                      UVM_HIGH)

            finish_item(req);
            #100;  // Delay to simulate deadline miss for short deadline

            if (is_short_deadline) begin
                deadline_misses++;
                `uvm_warning(get_name(), $sformatf("Request %0d likely missed deadline", i))
            end else begin
                deadline_hits++;
            end
        end

        `uvm_info(get_name(), $sformatf("Deadline test results: hits=%0d misses=%0d",
                                        deadline_hits, deadline_misses), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Mixed Traffic QoS Test Sequence
// Tests scheduler under mixed traffic conditions
// ------------------------------------------------------------
class mixed_traffic_qos_seq extends hbm_qos_base_sequence;
    `uvm_object_utils(mixed_traffic_qos_seq)

    int total_requests = 200;
    int traffic_mix_ratio = 70;  // Percentage of high-priority traffic

    function new(string name = "mixed_traffic_qos_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int high_prio_count = 0;
        int normal_prio_count = 0;
        int low_prio_count = 0;
        int flow_id;
        int is_high_prio;

        `uvm_info(get_name(), "Starting mixed traffic QoS test", UVM_MEDIUM)

        for (int i = 0; i < total_requests; i++) begin
            req = new("req");
            start_item(req);

            // Determine priority based on address pattern (simulated flow)
            flow_id = i[7:0];
            is_high_prio = (flow_id < (traffic_mix_ratio * 255 / 100));

            if (!req.randomize() with {
                addr_bank == (i % 16);
                addr_row  == flow_id;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            req.transaction_id = get_next_id();
            req.req_qos_prio = is_high_prio;

            if (is_high_prio) begin
                high_prio_count++;
            end else begin
                normal_prio_count++;
            end

            `uvm_info(get_name(), $sformatf("Request %0d: flow=%h prio=%b",
                                             i, flow_id, req.req_qos_prio), UVM_DEBUG)
            finish_item(req);
            #5;
        end

        `uvm_info(get_name(), $sformatf("Mixed traffic: high=%0d normal=%0d total=%0d",
                                        high_prio_count, normal_prio_count, total_requests),
                  UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// QoS Priority Test
// ------------------------------------------------------------
class hbm_qos_priority_test extends hbm_base_test;
    `uvm_component_utils(hbm_qos_priority_test)

    function new(string name = "hbm_qos_priority_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        qos_inheritance_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = qos_inheritancenew("seq");
        seq.num_low_prio = 30;
        seq.num_high_prio = 10;
        seq.interleave_count = 5;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// QoS Starvation Prevention Test
// ------------------------------------------------------------
class hbm_qos_starvation_test extends hbm_base_test;
    `uvm_component_utils(hbm_qos_starvation_test)

    function new(string name = "hbm_qos_starvation_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        starvation_prevention_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = starvation_preventionnew("seq");
        seq.num_high_prio = 50;
        seq.num_low_prio = 5;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// QoS Deadline Test
// ------------------------------------------------------------
class hbm_qos_deadline_test extends hbm_base_test;
    `uvm_component_utils(hbm_qos_deadline_test)

    function new(string name = "hbm_qos_deadline_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        deadline_miss_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = deadline_missnew("seq");
        seq.num_requests = 30;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Mixed Traffic QoS Test
// ------------------------------------------------------------
class hbm_qos_mixed_traffic_test extends hbm_base_test;
    `uvm_component_utils(hbm_qos_mixed_traffic_test)

    function new(string name = "hbm_qos_mixed_traffic_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        mixed_traffic_qos_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = mixed_traffic_qosnew("seq");
        seq.total_requests = 100;
        seq.traffic_mix_ratio = 30;  // 30% high-priority
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

endpackage : hbm_qos_test_pkg
