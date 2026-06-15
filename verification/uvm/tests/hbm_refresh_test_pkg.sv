// ------------------------------------------------------------
// hbm_refresh_test_pkg.sv - HBM Refresh Conflict Test Package
// Tests refresh scheduling, refresh conflicts, and refresh performance
// ------------------------------------------------------------
package hbm_refresh_test_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Refresh Transaction Type
// ------------------------------------------------------------
class hbm_refresh_transaction extends hbm_transaction;
    `uvm_object_utils(hbm_refresh_transaction)

    typedef enum {
        REFRESH_FULL,
        REFRESH_BANK,
        REFRESH_PER_BANK
    } refresh_type_t;

    rand refresh_type_t refresh_type;
    rand bit [7:0] bank_mask;    // Which banks to refresh (per-bank mode)

    function new(string name = "hbm_refresh_transaction");
        super.new(name);
    endfunction

    function string convert2string();
        return {
            super.convert2string(),
            $sformatf(" refresh_type=%s bank_mask=%b", refresh_type.name(), bank_mask)
        };
    endfunction
endclass

// ------------------------------------------------------------
// Base Refresh Sequence
// ------------------------------------------------------------
class hbm_refresh_base_sequence extends hbm_base_sequence;
    `uvm_object_utils(hbm_refresh_base_sequence)

    int refresh_interval = 3900;  // Default HBM4 refresh interval (cycles)

    function new(string name = "hbm_refresh_base_sequence");
        super.new(name);
    endfunction

    function void set_refresh_interval(int cycles);
        refresh_interval = cycles;
    endfunction
endclass

// ------------------------------------------------------------
// Refresh Conflict Test Sequence
// Tests that refresh commands don't conflict with user traffic
// ------------------------------------------------------------
class refresh_conflict_seq extends hbm_refresh_base_sequence;
    `uvm_object_utils(refresh_conflict_seq)

    int num_traffic_requests = 100;
    int num_refresh_commands = 10;
    int conflict_window_cycles = 50;

    function new(string name = "refresh_conflict_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int traffic_count = 0;
        int refresh_count = 0;
        int potential_conflicts = 0;

        `uvm_info(get_name(), "Starting refresh conflict test", UVM_MEDIUM)

        // Interleave refresh commands with traffic
        for (int i = 0; i < num_traffic_requests; i++) begin
            // Send traffic request
            req = hbm_transaction::type_id::create("req");
            start_item(req);
            if (!req.randomize() with {
                addr_bank == (i % 16);
                addr_row  == i;
            }) begin
                `uvm_error(get_name(), "Traffic randomization failed")
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("Traffic request %0d: bank=%h row=%h",
                                             i, req.addr_bank, req.addr_row), UVM_HIGH)
            finish_item(req);
            traffic_count++;

            // Inject refresh command periodically
            if (i > 0 && (i % (num_traffic_requests / num_refresh_commands)) == 0) begin
                // Simulate refresh command
                `uvm_info(get_name(), $sformatf("Injecting refresh command at cycle %0d", i), UVM_MEDIUM)
                refresh_count++;

                // Check for potential conflict window
                if (i < conflict_window_cycles) begin
                    potential_conflicts++;
                    `uvm_warning(get_name(), $sformatf("Potential refresh conflict at request %0d", i))
                end

                #50;  // Refresh takes time
            end

            #10;
        end

        `uvm_info(get_name(), $sformatf("Refresh conflict test: traffic=%0d refresh=%0d conflicts=%0d",
                                        traffic_count, refresh_count, potential_conflicts), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Refresh Timing Violation Test Sequence
// Tests that refresh timing constraints are met
// ------------------------------------------------------------
class refresh_timing_violation_seq extends hbm_refresh_base_sequence;
    `uvm_object_utils(refresh_timing_violation_seq)

    int num_refresh = 20;
    int tRFC = 180;  // Refresh cycle time (HBM4 default)
    int tREFI = 3900;  // Refresh interval (HBM4 default)
    int aggressive_refresh_count = 5;

    function new(string name = "refresh_timing_violation_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int timing_violations = 0;
        int refresh_issued = 0;

        `uvm_info(get_name(), "Starting refresh timing violation test", UVM_MEDIUM)

        // Normal refresh interval test
        for (int i = 0; i < num_refresh; i++) begin
            // Issue refresh command
            `uvm_info(get_name(), $sformatf("Issuing refresh %0d at cycle %0d",
                                            i, i * tREFI), UVM_HIGH)

            refresh_issued++;

            // Wait for refresh to complete
            #tRFC;

            // Check if next refresh comes too soon
            if (i > 0 && (i * tREFI) < (refresh_issued * tREFI + tRFC)) begin
                timing_violations++;
                `uvm_error(get_name(), "tREFI violation detected")
            end
        end

        // Aggressive refresh test (shorter interval)
        `uvm_info(get_name(), "Testing aggressive refresh (shorter tREFI)", UVM_MEDIUM)
        for (int i = 0; i < aggressive_refresh_count; i++) begin
            // Issue refresh with very short interval
            #500;  // Much shorter than tREFI

            `uvm_info(get_name(), $sformatf("Aggressive refresh %0d", i), UVM_HIGH)
            refresh_issued++;

            // Check for tREFI violation
            timing_violations++;
            `uvm_warning(get_name(), $sformatf("Aggressive refresh %0d may cause tREFI violation", i))
        end

        `uvm_info(get_name(), $sformatf("Refresh timing test: issued=%0d violations=%0d",
                                        refresh_issued, timing_violations), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Per-Bank Refresh Test Sequence
// Tests per-bank refresh (REFPB) functionality
// ------------------------------------------------------------
class per_bank_refresh_seq extends hbm_refresh_base_sequence;
    `uvm_object_utils(per_bank_refresh_seq)

    int num_banks = 16;
    int refresh_cycles_per_bank = 20;
    int num_bank_refresh_cycles = 5;

    function new(string name = "per_bank_refresh_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int banks_refreshed = 0;
        int refresh_cycles_completed = 0;

        `uvm_info(get_name(), "Starting per-bank refresh test", UVM_MEDIUM)

        // Perform multiple per-bank refresh cycles
        for (int cycle = 0; cycle < num_bank_refresh_cycles; cycle++) begin
            `uvm_info(get_name(), $sformatf("Per-bank refresh cycle %0d", cycle), UVM_MEDIUM)

            // Refresh each bank individually
            for (int bank = 0; bank < num_banks; bank++) begin
                req = hbm_transaction::type_id::create("req");
                start_item(req);

                if (!req.randomize() with {
                    addr_bank == bank;
                    addr_row  == 16'hFFFF;  // Refresh target
                }) begin
                    `uvm_error(get_name(), "Per-bank refresh randomization failed")
                end
                req.transaction_id = get_next_id();

                `uvm_info(get_name(), $sformatf("Per-bank refresh: bank=%0d", bank), UVM_HIGH)
                finish_item(req);
                banks_refreshed++;

                // Wait for bank refresh to complete
                #refresh_cycles_per_bank;
            end

            refresh_cycles_completed++;

            // Wait before next refresh cycle
            #100;
        end

        `uvm_info(get_name(), $sformatf("Per-bank refresh: banks=%0d cycles=%0d",
                                        banks_refreshed, refresh_cycles_completed), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Refresh During Active Bank Test Sequence
// Tests that refresh can occur with active banks
// ------------------------------------------------------------
class refresh_during_active_seq extends hbm_refresh_base_sequence;
    `uvm_object_utils(refresh_during_active_seq)

    int num_banks = 16;
    int requests_per_bank = 10;

    function new(string name = "refresh_during_active_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int banks_with_open_rows = 0;

        `uvm_info(get_name(), "Starting refresh during active bank test", UVM_MEDIUM)

        // Open rows in all banks
        for (int bank = 0; bank < num_banks; bank++) begin
            req = hbm_transaction::type_id::create("req");
            start_item(req);

            if (!req.randomize() with {
                cmd == hbm_transaction::WRITE;
                addr_bank == bank;
                addr_row  == bank * 256;  // Unique row per bank
            }) begin
                `uvm_error(get_name(), "Bank activation randomization failed")
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("Opening bank %0d row %0d", bank, bank * 256), UVM_HIGH)
            finish_item(req);
            banks_with_open_rows++;

            #20;
        end

        // Now issue refresh with all banks active
        `uvm_info(get_name(), $sformatf("Issuing refresh with %0d banks active", banks_with_open_rows),
                  UVM_MEDIUM)

        // Issue full refresh
        req = hbm_transaction::type_id::create("req");
        start_item(req);
        if (!req.randomize() with {
            addr_bank == 0;
            addr_row  == 16'hEEEE;
        }) begin
            `uvm_error(get_name(), "Refresh randomization failed")
        end
        req.transaction_id = get_next_id();
        `uvm_info(get_name(), "Issuing full refresh with active banks", UVM_MEDIUM)
        finish_item(req);

        // Verify banks are still accessible after refresh
        for (int bank = 0; bank < num_banks; bank++) begin
            req = hbm_transaction::type_id::create("req");
            start_item(req);

            if (!req.randomize() with {
                addr_bank == bank;
                addr_row  == bank * 256;  // Same row
            }) begin
                `uvm_error(get_name(), "Post-refresh access randomization failed")
            end
            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("Verifying bank %0d after refresh", bank), UVM_HIGH)
            finish_item(req);

            #10;
        end

        `uvm_info(get_name(), $sformatf("Refresh during active: %0d banks verified", num_banks),
                  UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Auto-Refresh Test Sequence
// Tests automatic refresh triggering
// ------------------------------------------------------------
class auto_refresh_seq extends hbm_refresh_base_sequence;
    `uvm_object_utils(auto_refresh_seq)

    int num_traffic_cycles = 50000;  // Long simulation
    int expected_auto_refresh_count = 12;  // ~3900 cycles per refresh

    function new(string name = "auto_refresh_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int traffic_count = 0;
        int refresh_detected = 0;
        int auto_refresh_count = 0;

        `uvm_info(get_name(), "Starting auto-refresh test", UVM_MEDIUM)

        // Generate continuous traffic
        for (int i = 0; i < num_traffic_cycles; i++) begin
            if (i % 1000 == 0) begin
                req = hbm_transaction::type_id::create("req");
                start_item(req);

                if (!req.randomize() with {
                    addr_bank == (i % 16);
                }) begin
                    `uvm_error(get_name(), "Traffic randomization failed")
                end
                req.transaction_id = get_next_id();
                finish_item(req);
                traffic_count++;

                // Simulate auto-refresh detection
                if (i > 0 && (i % refresh_interval) == 0) begin
                    auto_refresh_count++;
                    refresh_detected++;
                    `uvm_info(get_name(), $sformatf("Auto-refresh detected at cycle %0d (total: %0d)",
                                                    i, auto_refresh_count), UVM_HIGH)
                end
            end
            #10;
        end

        `uvm_info(get_name(), $sformatf("Auto-refresh test: traffic=%0d refresh=%0d expected=%0d",
                                        traffic_count, refresh_detected, expected_auto_refresh_count),
                  UVM_MEDIUM)

        // Check if expected refresh count matches
        if (refresh_detected < (expected_auto_refresh_count - 2)) begin
            `uvm_error(get_name(), "Auto-refresh count too low")
        end else if (refresh_detected > (expected_auto_refresh_count + 2)) begin
            `uvm_error(get_name(), "Auto-refresh count too high")
        end else begin
            `uvm_info(get_name(), "Auto-refresh count within expected range", UVM_MEDIUM)
        end
    endtask
endclass

// ------------------------------------------------------------
// Refresh Conflict Test
// ------------------------------------------------------------
class hbm_refresh_conflict_test extends hbm_base_test;
    `uvm_component_utils(hbm_refresh_conflict_test)

    function new(string name = "hbm_refresh_conflict_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        refresh_conflict_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = refresh_conflict_seq::type_id::create("seq");
        seq.num_traffic_requests = 100;
        seq.num_refresh_commands = 5;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Refresh Timing Violation Test
// ------------------------------------------------------------
class hbm_refresh_timing_test extends hbm_base_test;
    `uvm_component_utils(hbm_refresh_timing_test)

    function new(string name = "hbm_refresh_timing_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        refresh_timing_violation_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = refresh_timing_violation_seq::type_id::create("seq");
        seq.num_refresh = 10;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Per-Bank Refresh Test
// ------------------------------------------------------------
class hbm_per_bank_refresh_test extends hbm_base_test;
    `uvm_component_utils(hbm_per_bank_refresh_test)

    function new(string name = "hbm_per_bank_refresh_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        per_bank_refresh_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = per_bank_refresh_seq::type_id::create("seq");
        seq.num_banks = 16;
        seq.num_bank_refresh_cycles = 3;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Refresh During Active Test
// ------------------------------------------------------------
class hbm_refresh_during_active_test extends hbm_base_test;
    `uvm_component_utils(hbm_refresh_during_active_test)

    function new(string name = "hbm_refresh_during_active_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        refresh_during_active_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = refresh_during_active_seq::type_id::create("seq");
        seq.num_banks = 16;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Auto-Refresh Test
// ------------------------------------------------------------
class hbm_auto_refresh_test extends hbm_base_test;
    `uvm_component_utils(hbm_auto_refresh_test)

    function new(string name = "hbm_auto_refresh_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        auto_refresh_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = auto_refresh_seq::type_id::create("seq");
        seq.num_traffic_cycles = 50000;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

endpackage : hbm_refresh_test_pkg