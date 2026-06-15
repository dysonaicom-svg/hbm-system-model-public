// ------------------------------------------------------------
// hbm_test_pkg.sv - HBM UVM Test Package
// Simplified for Verilator compatibility
// ------------------------------------------------------------
package hbm_test_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Base Sequence with Register Access
// ------------------------------------------------------------
class hbm_base_sequence extends uvm_sequence #(hbm_transaction);
    `uvm_object_utils(hbm_base_sequence)

    hbm_reg_model regmodel;
    int transaction_id = 0;

    function new(string name = "hbm_base_sequence");
        super.new(name);
    endfunction

    function void set_regmodel(hbm_reg_model rm);
        regmodel = rm;
    endfunction

    function int get_next_id();
        transaction_id++;
        return transaction_id;
    endfunction

    task wait_for_idle();
        // Wait for DUT to be idle
        repeat(10) @(posedge clk);
    endtask
endclass

// ------------------------------------------------------------
// Single Read Sequence
// ------------------------------------------------------------
class single_read_seq extends hbm_base_sequence;
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
        req.transaction_id = get_next_id();
        `uvm_info(get_name(), $sformatf("Sending: %s", req.convert2string()), UVM_MEDIUM)
        finish_item(req);
    endtask
endclass

// ------------------------------------------------------------
// Single Write Sequence
// ------------------------------------------------------------
class single_write_seq extends hbm_base_sequence;
    `uvm_object_utils(single_write_seq)

    bit [7:0]   write_bank = 8'h00;
    bit [15:0]  write_row = 16'h0000;
    bit [1:0]   write_col = 2'h0;
    bit [511:0] write_data = 'hDEADBEEF;

    function new(string name = "single_write_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        req = hbm_transaction::type_id::create("req");
        start_item(req);
        if (!req.randomize() with {
            cmd == hbm_transaction::WRITE;
            addr_bank == write_bank;
            addr_row  == write_row;
            addr_col  == write_col;
        }) begin
            `uvm_error(get_name(), "Randomization failed")
        end
        req.transaction_id = get_next_id();
        req.wdata = write_data;
        req.wdata_mask = '0;  // All bytes valid
        `uvm_info(get_name(), $sformatf("Sending: %s", req.convert2string()), UVM_MEDIUM)
        finish_item(req);
    endtask
endclass

// ------------------------------------------------------------
// Random Traffic Sequence
// ------------------------------------------------------------
class random_traffic_seq extends hbm_base_sequence;
    `uvm_object_utils(random_traffic_seq)

    int num_requests = 100;
    bit [1:0] read_write_ratio = 2'b11;  // 50% read, 50% write

    function new(string name = "random_traffic_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        req = hbm_transaction::type_id::create("req");

        for (int i = 0; i < num_requests; i++) begin
            start_item(req);
            if (!req.randomize()) begin
                `uvm_error(get_name(), $sformatf("Randomization failed at request %0d", i))
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("Request %0d: %s", i, req.convert2string()), UVM_MEDIUM)
            finish_item(req);

            // Small delay between requests
            #10;
        end
    endtask
endclass

// ------------------------------------------------------------
// Write-Read Sequence (same address verification)
// ------------------------------------------------------------
class write_read_seq extends hbm_base_sequence;
    `uvm_object_utils(write_read_seq)

    int num_iterations = 10;
    bit [7:0]  test_bank = 8'h03;
    bit [15:0] test_row = 16'h1234;
    bit [1:0]  test_col = 2'h0;

    function new(string name = "write_read_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;

        for (int i = 0; i < num_iterations; i++) begin
            // Write pattern
            req = hbm_transaction::type_id::create("req");
            start_item(req);
            if (!req.randomize() with {
                cmd == hbm_transaction::WRITE;
                addr_bank == test_bank;
                addr_row  == test_row;
                addr_col  == test_col;
            }) begin
                `uvm_error(get_name(), "Write randomization failed")
            end
            req.transaction_id = get_next_id();
            req.wdata = {64{32'(i)}};  // Unique pattern per iteration
            req.wdata_mask = '0;
            `uvm_info(get_name(), $sformatf("Write iteration %0d: %s", i, req.convert2string()), UVM_MEDIUM)
            finish_item(req);

            // Read back for verification
            req = hbm_transaction::type_id::create("req");
            start_item(req);
            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == test_bank;
                addr_row  == test_row;
                addr_col  == test_col;
            }) begin
                `uvm_error(get_name(), "Read randomization failed")
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("Read iteration %0d: %s", i, req.convert2string()), UVM_MEDIUM)
            finish_item(req);

            // Delay between iterations
            #50;
        end
    endtask
endclass

// ------------------------------------------------------------
// Bank Stress Sequence
// ------------------------------------------------------------
class bank_stress_seq extends hbm_base_sequence;
    `uvm_object_utils(bank_stress_seq)

    int num_banks = 16;
    int requests_per_bank = 20;

    function new(string name = "bank_stress_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;

        // Round-robin through all banks
        for (int bank = 0; bank < num_banks; bank++) begin
            for (int i = 0; i < requests_per_bank; i++) begin
                req = hbm_transaction::type_id::create("req");
                start_item(req);
                if (!req.randomize() with {
                    addr_bank == bank;
                    addr_row  == i;
                    addr_col  == 0;
                }) begin
                    `uvm_error(get_name(), "Randomization failed")
                end
                req.transaction_id = get_next_id();
                `uvm_info(get_name(), $sformatf("Bank %0d Request %0d: %s", bank, i, req.convert2string()), UVM_HIGH)
                finish_item(req);
            end
        end
    endtask
endclass

// ------------------------------------------------------------
// Hotspot Sequence
// ------------------------------------------------------------
class hotspot_seq extends hbm_base_sequence;
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
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("Hotspot %0d: %s", i, req.convert2string()), UVM_MEDIUM)
            finish_item(req);

            // Small delay at hotspot
            #20;
        end
    endtask
endclass

// ------------------------------------------------------------
// Register Test Sequence
// ------------------------------------------------------------
class register_test_seq extends hbm_base_sequence;
    `uvm_object_utils(register_test_seq)

    function new(string name = "register_test_seq");
        super.new(name);
    endfunction

    task body();
        if (regmodel == null) begin
            `uvm_warning(get_name(), "No register model available")
            return;
        end

        // Test control register
        `uvm_info(get_name(), "Testing control register", UVM_MEDIUM)
        regmodel.write_control(32'h0001);  // Start
        #100;
        regmodel.write_control(32'h0003);  // Enable + Start
        #100;
        regmodel.write_control(32'h0000);  // Stop
        #100;

        // Test timing registers
        `uvm_info(get_name(), "Testing timing registers", UVM_MEDIUM)
        regmodel.write_timing0(32'h141828);  // tRCD=20, tRP=20, tRAS=40
        #100;
        regmodel.write_timing1(32'h3C1414);  // tRC=60, tRRD=20, tCCD=20
        #100;

        `uvm_info(get_name(), "Register test complete", UVM_MEDIUM)
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
        // Print register model
        if (env.regmodel != null) begin
            env.regmodel.print();
        end
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
            seq.set_regmodel(env.regmodel);
            seq.start(env.hbm_agent_inst.sequencer);
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
            seq.set_regmodel(env.regmodel);
            seq.start(env.hbm_agent_inst.sequencer);
        end
        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Single Write Test
// ------------------------------------------------------------
class hbm_single_write_test extends hbm_base_test;
    `uvm_component_utils(hbm_single_write_test)

    function new(string name = "hbm_single_write_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        single_write_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);
        begin
            seq = single_write_seq::type_id::create("seq");
            seq.set_regmodel(env.regmodel);
            seq.start(env.hbm_agent_inst.sequencer);
        end
        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Write-Read Test
// ------------------------------------------------------------
class hbm_write_read_test extends hbm_base_test;
    `uvm_component_utils(hbm_write_read_test)

    function new(string name = "hbm_write_read_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        write_read_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);
        begin
            seq = write_read_seq::type_id::create("seq");
            seq.num_iterations = 20;
            seq.set_regmodel(env.regmodel);
            seq.start(env.hbm_agent_inst.sequencer);
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
            seq.num_requests = 100;
            seq.set_regmodel(env.regmodel);
            seq.start(env.hbm_agent_inst.sequencer);
        end
        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Bank Stress Test
// ------------------------------------------------------------
class hbm_bank_stress_test extends hbm_base_test;
    `uvm_component_utils(hbm_bank_stress_test)

    function new(string name = "hbm_bank_stress_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        bank_stress_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);
        begin
            seq = bank_stress_seq::type_id::create("seq");
            seq.num_banks = 16;
            seq.requests_per_bank = 10;
            seq.set_regmodel(env.regmodel);
            seq.start(env.hbm_agent_inst.sequencer);
        end
        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Register Test
// ------------------------------------------------------------
class hbm_register_test extends hbm_base_test;
    `uvm_component_utils(hbm_register_test)

    function new(string name = "hbm_register_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        register_test_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);
        begin
            seq = register_test_seq::type_id::create("seq");
            seq.set_regmodel(env.regmodel);
            fork
                seq.start(null);  // Standalone register sequence
            join_none
        end
        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Comprehensive Test (all sequences)
// ------------------------------------------------------------
class hbm_comprehensive_test extends hbm_base_test;
    `uvm_component_utils(hbm_comprehensive_test)

    function new(string name = "hbm_comprehensive_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        super.run_phase(phase);
        phase.raise_objection(this);

        fork
        begin
            // Register configuration
            register_test_seq reg_seq;
            reg_seq = register_test_seq::type_id::create("reg_seq");
            reg_seq.set_regmodel(env.regmodel);
            reg_seq.start(null);
        end

        begin
            // Random traffic
            random_traffic_seq rand_seq;
            rand_seq = random_traffic_seq::type_id::create("rand_seq");
            rand_seq.num_requests = 50;
            rand_seq.set_regmodel(env.regmodel);
            rand_seq.start(env.hbm_agent_inst.sequencer);
        end

        begin
            // Hotspot traffic
            hotspot_seq hot_seq;
            hot_seq = hotspot_seq::type_id::create("hot_seq");
            hot_seq.num_requests = 30;
            hot_seq.set_regmodel(env.regmodel);
            hot_seq.start(env.hbm_agent_inst.sequencer);
        end
        join

        phase.drop_objection(this);
    endtask
endclass

endpackage : hbm_test_pkg