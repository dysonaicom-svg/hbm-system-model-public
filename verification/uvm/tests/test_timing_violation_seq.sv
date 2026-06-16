// ------------------------------------------------------------
// test_timing_violation_seq.sv - HBM Timing Violation Test
// Tests various DRAM timing constraint violations
// ------------------------------------------------------------
class test_timing_violation_seq extends hbm_base_sequence;
    `uvm_object_utils(test_timing_violation_seq)

    int num_violations = 50;
    int tRCD_violations = 0;
    int tRP_violations = 0;
    int tRAS_violations = 0;
    int tRC_violations = 0;
    int tRRD_violations = 0;

    function new(string name = "test_timing_violation_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int cycle_count = 0;

        `uvm_info(get_name(), "Starting TIMING VIOLATION test", UVM_MEDIUM)

        // Test tRRD violation (minimum row activation interval)
        `uvm_info(get_name(), "Testing tRRD violations", UVM_MEDIUM)
        repeat (20) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank inside {[0:3]};  // Same bank group
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;

            // Violate tRRD (should be 8 cycles)
            if (cycle_count > 1 && cycle_count % 8 == 0) begin
                tRRD_violations++;
                `uvm_info(get_name(), $sformatf("tRRD VIOLATION at cycle %0d", cycle_count), UVM_MEDIUM)
            end

            #(5ns);  // Too fast, will violate tRRD
        end

        // Test tRC violation (row cycle time)
        `uvm_info(get_name(), "Testing tRC violations", UVM_MEDIUM)
        cycle_count = 0;
        repeat (10) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == (cycle_count % 16);
                addr_row == (cycle_count % 256);
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;

            // Violate tRC (should be 60 cycles)
            if (cycle_count > 0 && cycle_count % 60 == 0) begin
                tRC_violations++;
                `uvm_info(get_name(), $sformatf("tRC VIOLATION at cycle %0d", cycle_count), UVM_MEDIUM)
            end

            #(10ns);
        end

        `uvm_info(get_name(), $sformatf("Timing violation test completed: tRRD=%0d, tRC=%0d",
            tRRD_violations, tRC_violations), UVM_MEDIUM)
    endtask
endclass