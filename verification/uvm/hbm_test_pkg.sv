// ------------------------------------------------------------
// hbm_test_pkg.sv - HBM UVM Test Package
// ------------------------------------------------------------
package hbm_test_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Single Read Sequence
// ------------------------------------------------------------
class single_read_seq extends uvm_sequence #(hbm_transaction);
    `uvm_object_utils(single_read_seq)

    function new(string name = "single_read_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        req = hbm_transaction::type_id::create("req");
        start_item(req);
        if (!req.randomize() with {
            cmd == hbm_transaction::READ;
            addr_bank == 8'h00;
            addr_row  == 16'h0000;
            addr_col  == 2'h0;
        }) begin
            `uvm_error(get_name(), "Randomization failed")
        end
        `uvm_info(get_name(), $sformatf("Sending: %s", req.convert2string()), UVM_MEDIUM)
        finish_item(req);
    endtask
endclass

// ------------------------------------------------------------
// Random Traffic Sequence (100 requests)
// ------------------------------------------------------------
class random_traffic_seq extends uvm_sequence #(hbm_transaction);
    `uvm_object_utils(random_traffic_seq)

    int num_requests = 100;

    function new(string name = "random_traffic_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        req = hbm_transaction::type_id::create("req");

        for (int i = 0; i < num_requests; i++) begin
            start_item(req);
            if (!req.randomize()) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            `uvm_info(get_name(), $sformatf("Request %0d: %s", i, req.convert2string()), UVM_MEDIUM)
            finish_item(req);
        end
    endtask
endclass

// ------------------------------------------------------------
// Hotspot Sequence (repeated access to specific addresses)
// ------------------------------------------------------------
class hotspot_seq extends uvm_sequence #(hbm_transaction);
    `uvm_object_utils(hotspot_seq)

    int num_requests = 50;
    int hotspot_bank;
    int hotspot_row;
    int hotspot_col;

    function new(string name = "hotspot_seq");
        super.new(name);
        hotspot_bank = 8'h05;
        hotspot_row  = 16'h1234;
        hotspot_col  = 2'h2;
    endfunction

    task body();
        hbm_transaction req;
        req = hbm_transaction::type_id::create("req");

        for (int i = 0; i < num_requests; i++) begin
            start_item(req);
            if (!req.randomize() with {
                addr_bank == hotspot_bank;
                addr_row  == hotspot_row;
                addr_col  == hotspot_col;
            }) begin
                `uvm_error(get_name(), "Hotspot randomization failed")
            end
            `uvm_info(get_name(), $sformatf("Hotspot %0d: %s", i, req.convert2string()), UVM_MEDIUM)
            finish_item(req);
        end
    endtask
endclass

// ------------------------------------------------------------
// Base Test
// ------------------------------------------------------------
class hbm_base_test extends uvm_test;
    `uvm_component_utils(hbm_base_test)

    hbm_env env;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        env = hbm_env::type_id::create("env", this);
        `uvm_info(get_name(), "Build phase complete", UVM_MEDIUM)
    endfunction

    function void end_of_elaboration_phase(uvm_phase phase);
        super.end_of_elaboration_phase(phase);
        `uvm_info(get_name(), "End of elaboration", UVM_MEDIUM)
        print();
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
    endtask

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        `uvm_info(get_name(), "Test completed", UVM_MEDIUM)
    endfunction
endclass

// ------------------------------------------------------------
// Random Traffic Test
// ------------------------------------------------------------
class hbm_random_test extends hbm_base_test;
    `uvm_component_utils(hbm_random_test)

    function new(string name = "hbm_random_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        random_traffic_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);
        begin
            seq = random_traffic_seq::type_id::create("seq");
            seq.num_requests = 100;
            seq.start(env.agent.sequencer);
        end
        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Single Read Test
// ------------------------------------------------------------
class hbm_single_read_test extends hbm_base_test;
    `uvm_component_utils(hbm_single_read_test)

    function new(string name = "hbm_single_read_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        single_read_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);
        begin
            seq = single_read_seq::type_id::create("seq");
            seq.start(env.agent.sequencer);
        end
        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Hotspot Test
// ------------------------------------------------------------
class hbm_hotspot_test extends hbm_base_test;
    `uvm_component_utils(hbm_hotspot_test)

    function new(string name = "hbm_hotspot_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        hotspot_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);
        begin
            seq = hotspot_seq::type_id::create("seq");
            seq.num_requests = 50;
            seq.start(env.agent.sequencer);
        end
        phase.drop_objection(this);
    endtask
endclass

endpackage : hbm_test_pkg