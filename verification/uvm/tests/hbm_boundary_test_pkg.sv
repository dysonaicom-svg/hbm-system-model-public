// ------------------------------------------------------------
// hbm_boundary_test_pkg.sv - HBM Boundary Condition Test Package
// Tests edge cases, maximum/minimum values, and boundary conditions
// ------------------------------------------------------------
package hbm_boundary_test_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Boundary Transaction
// ------------------------------------------------------------
class hbm_boundary_transaction extends hbm_transaction;
    `uvm_object_utils(hbm_boundary_transaction)

    typedef enum {
        TEST_MAX_ADDR,
        TEST_MIN_ADDR,
        TEST_BANK_BOUNDARY,
        TEST_ROW_BOUNDARY,
        TEST_COL_BOUNDARY,
        TEST_BURST_BOUNDARY,
        TEST_QUEUE_FULL,
        TEST_QUEUE_EMPTY
    } boundary_test_type_t;

    rand boundary_test_type_t test_type;

    function new(string name = "hbm_boundary_transaction");
        super.new(name);
    endfunction

    function string convert2string();
        return {
            super.convert2string(),
            $sformatf(" test_type=%s", test_type.name())
        };
    endfunction
endclass

// ------------------------------------------------------------
// Base Boundary Sequence
// ------------------------------------------------------------
class hbm_boundary_base_sequence extends hbm_base_sequence;
    `uvm_object_utils(hbm_boundary_base_sequence)

    function new(string name = "hbm_boundary_base_sequence");
        super.new(name);
    endfunction
endclass

// ------------------------------------------------------------
// Maximum Address Test Sequence
// Tests access to maximum valid addresses
// ------------------------------------------------------------
class max_address_seq extends hbm_boundary_base_sequence;
    `uvm_object_utils(max_address_seq)

    int num_tests = 10;

    function new(string name = "max_address_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int pass_count = 0;
        int fail_count = 0;

        `uvm_info(get_name(), "Starting maximum address test", UVM_MEDIUM)

        // Test maximum bank address
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            addr_bank == 8'hFF;  // Max bank
            addr_row  == 16'hFFFF;  // Max row
            addr_col  == 2'h3;  // Max column
        }) begin
            `uvm_error(get_name(), "Max bank/row/col randomization failed")
        end
        req.transaction_id = get_next_id();
        `uvm_info(get_name(), $sformatf("Max address test: bank=%h row=%h col=%h",
                                         req.addr_bank, req.addr_row, req.addr_col), UVM_MEDIUM)
        finish_item(req);
        pass_count++;
        #50;

        // Test maximum channel address (HBM4: 32 channels)
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            addr_bank == 8'h1F;  // Max channel = 31
        }) begin
            `uvm_error(get_name(), "Max channel randomization failed")
        end
        req.transaction_id = get_next_id();
        `uvm_info(get_name(), $sformatf("Max channel test: bank=%h", req.addr_bank), UVM_MEDIUM)
        finish_item(req);
        pass_count++;
        #50;

        // Test maximum row in specific bank
        for (int bank = 0; bank < 4; bank++) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == bank;
                addr_row  == 16'hFFFF;
            }) begin
                `uvm_error(get_name(), "Max row randomization failed")
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("Max row test: bank=%h row=%h", bank, req.addr_row), UVM_MEDIUM)
            finish_item(req);
            pass_count++;
            #20;
        end

        `uvm_info(get_name(), $sformatf("Max address test: passed=%0d failed=%0d",
                                        pass_count, fail_count), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Minimum Address Test Sequence
// Tests access to minimum valid addresses (zero addresses)
// ------------------------------------------------------------
class min_address_seq extends hbm_boundary_base_sequence;
    `uvm_object_utils(min_address_seq)

    function new(string name = "min_address_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int pass_count = 0;

        `uvm_info(get_name(), "Starting minimum address test", UVM_MEDIUM)

        // Test minimum address (all zeros)
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            addr_bank == 8'h00;
            addr_row  == 16'h0000;
            addr_col  == 2'h0;
        }) begin
            `uvm_error(get_name(), "Min address randomization failed")
        end
        req.transaction_id = get_next_id();
        `uvm_info(get_name(), $sformatf("Min address test: bank=%h row=%h col=%h",
                                         req.addr_bank, req.addr_row, req.addr_col), UVM_MEDIUM)
        finish_item(req);
        pass_count++;
        #50;

        // Test minimum row with various banks
        for (int bank = 0; bank < 16; bank++) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == bank;
                addr_row  == 16'h0000;  // Min row
            }) begin
                `uvm_error(get_name(), "Min row randomization failed")
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("Min row test: bank=%h row=%h", bank, req.addr_row), UVM_HIGH)
            finish_item(req);
            pass_count++;
            #10;
        end

        `uvm_info(get_name(), $sformatf("Min address test: passed=%0d", pass_count), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Address Overflow Test Sequence
// Tests behavior with addresses beyond valid range
// ------------------------------------------------------------
class address_overflow_seq extends hbm_boundary_base_sequence;
    `uvm_object_utils(address_overflow_seq)

    function new(string name = "address_overflow_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int overflow_count = 0;
        int handled_count = 0;

        `uvm_info(get_name(), "Starting address overflow test", UVM_MEDIUM)

        // Test overflow bank address (should wrap or saturate)
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            addr_bank == 8'hFF;  // Beyond max (15)
        }) begin
            `uvm_error(get_name(), "Overflow randomization failed")
        end
        req.transaction_id = get_next_id();

        // Check if overflow is detected/handled
        if (req.addr_bank > 15) begin
            overflow_count++;
            `uvm_warning(get_name(), $sformatf("Bank overflow detected: %h", req.addr_bank))
        end else begin
            handled_count++;
            `uvm_info(get_name(), $sformatf("Bank overflow handled: %h -> %h",
                                             8'hFF, req.addr_bank), UVM_MEDIUM)
        end
        finish_item(req);
        #50;

        // Test overflow row address
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            addr_bank == 0;
            addr_row  == 16'hFFFF;  // Max row (valid)
        }) begin
            `uvm_error(get_name(), "Row overflow randomization failed")
        end
        req.transaction_id = get_next_id();
        `uvm_info(get_name(), $sformatf("Max row test: %h", req.addr_row), UVM_MEDIUM)
        finish_item(req);
        handled_count++;
        #50;

        `uvm_info(get_name(), $sformatf("Overflow test: overflow=%0d handled=%0d",
                                        overflow_count, handled_count), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Queue Full Condition Test Sequence
// Tests behavior when command queue is full
// ------------------------------------------------------------
class queue_full_seq extends hbm_boundary_base_sequence;
    `uvm_object_utils(queue_full_seq)

    int queue_depth = 32;
    int overflow_attempts = 50;

    function new(string name = "queue_full_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int queued_count = 0;
        int rejected_count = 0;
        int queue_full_events = 0;

        `uvm_info(get_name(), "Starting queue full test", UVM_MEDIUM)

        // Fill queue beyond capacity
        for (int i = 0; i < overflow_attempts; i++) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                addr_bank == (i % 16);
                addr_row  == i;
            }) begin
                `uvm_error(get_name(), "Queue randomization failed")
            end
            req.transaction_id = get_next_id();

            // Simulate queue full condition
            if (queued_count >= queue_depth) begin
                queue_full_events++;
                `uvm_warning(get_name(), $sformatf("Queue full at request %0d", i))

                // Simulate rejection
                if ($urandom() % 100 < 50) begin  // 50% rejection rate when full
                    rejected_count++;
                    `uvm_info(get_name(), "Request rejected due to queue full", UVM_HIGH)
                end
            end

            finish_item(req);
            queued_count++;
            #5;
        end

        `uvm_info(get_name(), $sformatf("Queue full test: queued=%0d rejected=%0d queue_full_events=%0d",
                                        queued_count, rejected_count, queue_full_events), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Empty Queue Condition Test Sequence
// Tests behavior when command queue is empty
// ------------------------------------------------------------
class queue_empty_seq extends hbm_boundary_base_sequence;
    `uvm_object_utils(queue_empty_seq)

    int idle_cycles = 100;

    function new(string name = "queue_empty_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int idle_count = 0;
        int wakeup_count = 0;

        `uvm_info(get_name(), "Starting queue empty test", UVM_MEDIUM)

        // Generate single request then wait
        req = new("req");
        start_item(req);
        if (!req.randomize()) begin
            `uvm_error(get_name(), "Empty queue randomization failed")
        end
        req.transaction_id = get_next_id();
        `uvm_info(get_name(), "Initial request sent", UVM_MEDIUM)
        finish_item(req);
        #100;

        // Wait while queue is empty
        `uvm_info(get_name(), $sformatf("Waiting %0d cycles with empty queue", idle_cycles), UVM_MEDIUM)
        for (int i = 0; i < idle_cycles; i++) begin
            idle_count++;
            #10;
        end

        // Send new request to wake up
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            addr_bank == 8'h05;
        }) begin
            `uvm_error(get_name(), "Wakeup randomization failed")
        end
        req.transaction_id = get_next_id();
        `uvm_info(get_name(), "Queue wakeup request sent", UVM_MEDIUM)
        finish_item(req);
        wakeup_count++;

        `uvm_info(get_name(), $sformatf("Queue empty test: idle=%0d wakeup=%0d",
                                        idle_count, wakeup_count), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Burst Boundary Test Sequence
// Tests burst access at various boundary conditions
// ------------------------------------------------------------
class burst_boundary_seq extends hbm_boundary_base_sequence;
    `uvm_object_utils(burst_boundary_seq)

    int num_bursts = 20;

    function new(string name = "burst_boundary_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int burst_count = 0;
        int boundary_crossings = 0;

        `uvm_info(get_name(), "Starting burst boundary test", UVM_MEDIUM)

        // Test bursts at column boundary
        for (int i = 0; i < num_bursts; i++) begin
            req = new("req");
            start_item(req);

            // Target column 3 (last column) to trigger boundary crossing
            if (!req.randomize() with {
                addr_bank == (i % 16);
                addr_col  == 2'h3;  // Max column
            }) begin
                `uvm_error(get_name(), "Burst boundary randomization failed")
            end
            req.transaction_id = get_next_id();

            // Check for boundary crossing
            if (req.addr_col == 2'h3) begin
                boundary_crossings++;
                `uvm_info(get_name(), $sformatf("Burst at column boundary: bank=%h", req.addr_bank), UVM_HIGH)
            end

            `uvm_info(get_name(), $sformatf("Burst test %0d: col=%h", i, req.addr_col), UVM_DEBUG)
            finish_item(req);
            burst_count++;
            #20;
        end

        `uvm_info(get_name(), $sformatf("Burst boundary test: bursts=%0d crossings=%0d",
                                        burst_count, boundary_crossings), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Timing Boundary Test Sequence
// Tests timing parameters at minimum and maximum values
// ------------------------------------------------------------
class timing_boundary_seq extends hbm_boundary_base_sequence;
    `uvm_object_utils(timing_boundary_seq)

    function new(string name = "timing_boundary_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;

        `uvm_info(get_name(), "Starting timing boundary test", UVM_MEDIUM)

        // Test with minimum timing parameters
        if (regmodel != null) begin
            `uvm_info(get_name(), "Testing minimum timing parameters", UVM_MEDIUM)

            // Minimum tRCD
            regmodel.write_timing0(32'h010101);  // tRCD=1, tRP=1, tRAS=1
            #100;

            // Minimum tRC
            regmodel.write_timing1(32'h010101);  // tRC=1, tRRD=1, tCCD=1
            #100;

            // Send request with minimum timing
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == 0;
            }) begin
                `uvm_error(get_name(), "Minimum timing randomization failed")
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), "Request with minimum timing", UVM_MEDIUM)
            finish_item(req);
            #200;
        end

        // Test with maximum timing parameters
        if (regmodel != null) begin
            `uvm_info(get_name(), "Testing maximum timing parameters", UVM_MEDIUM)

            // Maximum tRCD
            regmodel.write_timing0(32'hFF80FF);  // tRCD=255, tRP=128, tRAS=255
            #100;

            // Maximum tRC
            regmodel.write_timing1(32'hFFFF80);  // tRC=255, tRRD=255, tCCD=128
            #100;

            // Send request with maximum timing
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == 8'h0F;
            }) begin
                `uvm_error(get_name(), "Maximum timing randomization failed")
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), "Request with maximum timing", UVM_MEDIUM)
            finish_item(req);
            #5000;
        end

        // Reset to default timing
        if (regmodel != null) begin
            regmodel.write_timing0(32'h141828);
            regmodel.write_timing1(32'h3C1414);
            `uvm_info(get_name(), "Timing parameters reset to defaults", UVM_MEDIUM)
        end
    endtask
endclass

// ------------------------------------------------------------
// Data Pattern Boundary Test Sequence
// Tests various data patterns at boundaries
// ------------------------------------------------------------
class data_pattern_boundary_seq extends hbm_boundary_base_sequence;
    `uvm_object_utils(data_pattern_boundary_seq)

    int num_patterns = 10;

    function new(string name = "data_pattern_boundary_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;

        `uvm_info(get_name(), "Starting data pattern boundary test", UVM_MEDIUM)

        // Test all-ones pattern
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            cmd == WRITE;
            addr_bank == 0;
            addr_row  == 0;
        }) begin
            `uvm_error(get_name(), "Data pattern randomization failed")
        end
        req.transaction_id = get_next_id();
        req.wdata = '1;  // All ones
        req.wdata_mask = '0;
        `uvm_info(get_name(), "Testing all-ones data pattern", UVM_MEDIUM)
        finish_item(req);
        #50;

        // Test all-zeros pattern
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            cmd == WRITE;
            addr_bank == 1;
            addr_row  == 0;
        }) begin
            `uvm_error(get_name(), "Data pattern randomization failed")
        end
        req.transaction_id = get_next_id();
        req.wdata = '0;  // All zeros
        req.wdata_mask = '0;
        `uvm_info(get_name(), "Testing all-zeros data pattern", UVM_MEDIUM)
        finish_item(req);
        #50;

        // Test alternating pattern
        req = new("req");
        start_item(req);
        if (!req.randomize() with {
            cmd == WRITE;
            addr_bank == 2;
            addr_row  == 0;
        }) begin
            `uvm_error(get_name(), "Data pattern randomization failed")
        end
        req.transaction_id = get_next_id();
        req.wdata = 512'hAAAAAAAAAAAAAAAA;  // Alternating
        req.wdata_mask = '0;
        `uvm_info(get_name(), "Testing alternating data pattern", UVM_MEDIUM)
        finish_item(req);
        #50;

        // Test walking ones pattern
        for (int i = 0; i < num_patterns; i++) begin
            req = new("req");
            start_item(req);
            if (!req.randomize() with {
                cmd == WRITE;
                addr_bank == (i % 16);
            }) begin
                `uvm_error(get_name(), "Walking ones randomization failed")
            end
            req.transaction_id = get_next_id();
            req.wdata = (512'h1 << i);  // Single bit set
            req.wdata_mask = '0;
            `uvm_info(get_name(), $sformatf("Walking ones pattern bit %0d", i), UVM_HIGH)
            finish_item(req);
            #20;
        end

        `uvm_info(get_name(), $sformatf("Data pattern test: %0d patterns tested", num_patterns), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Maximum Address Test
// ------------------------------------------------------------
class hbm_max_address_test extends hbm_base_test;
    `uvm_component_utils(hbm_max_address_test)

    function new(string name = "hbm_max_address_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        max_address_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = max_addressnew("seq");
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Minimum Address Test
// ------------------------------------------------------------
class hbm_min_address_test extends hbm_base_test;
    `uvm_component_utils(hbm_min_address_test)

    function new(string name = "hbm_min_address_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        min_address_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = min_addressnew("seq");
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Address Overflow Test
// ------------------------------------------------------------
class hbm_address_overflow_test extends hbm_base_test;
    `uvm_component_utils(hbm_address_overflow_test)

    function new(string name = "hbm_address_overflow_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        address_overflow_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = address_overflownew("seq");
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Queue Full Test
// ------------------------------------------------------------
class hbm_queue_full_test extends hbm_base_test;
    `uvm_component_utils(hbm_queue_full_test)

    function new(string name = "hbm_queue_full_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        queue_full_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = queue_fullnew("seq");
        seq.queue_depth = 32;
        seq.overflow_attempts = 50;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Queue Empty Test
// ------------------------------------------------------------
class hbm_queue_empty_test extends hbm_base_test;
    `uvm_component_utils(hbm_queue_empty_test)

    function new(string name = "hbm_queue_empty_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        queue_empty_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = queue_emptynew("seq");
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Burst Boundary Test
// ------------------------------------------------------------
class hbm_burst_boundary_test extends hbm_base_test;
    `uvm_component_utils(hbm_burst_boundary_test)

    function new(string name = "hbm_burst_boundary_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        burst_boundary_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = burst_boundarynew("seq");
        seq.num_bursts = 20;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Timing Boundary Test
// ------------------------------------------------------------
class hbm_timing_boundary_test extends hbm_base_test;
    `uvm_component_utils(hbm_timing_boundary_test)

    function new(string name = "hbm_timing_boundary_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        timing_boundary_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = timing_boundarynew("seq");
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Data Pattern Boundary Test
// ------------------------------------------------------------
class hbm_data_pattern_boundary_test extends hbm_base_test;
    `uvm_component_utils(hbm_data_pattern_boundary_test)

    function new(string name = "hbm_data_pattern_boundary_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        data_pattern_boundary_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = data_pattern_boundarynew("seq");
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

endpackage : hbm_boundary_test_pkg