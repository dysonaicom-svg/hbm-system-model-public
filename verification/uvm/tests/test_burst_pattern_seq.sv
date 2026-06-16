// ------------------------------------------------------------
// test_burst_pattern_seq.sv - HBM Burst Pattern Test
// Tests various burst patterns and boundaries
// ------------------------------------------------------------
class test_burst_pattern_seq extends hbm_base_sequence;
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
        int pattern_type = 0;

        `uvm_info(get_name(), "Starting BURST PATTERN test", UVM_MEDIUM)

        // Test sequential bursts
        `uvm_info(get_name(), "Testing sequential burst patterns", UVM_MEDIUM)
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

            `uvm_info(get_name(), $sformatf("BURST: pattern=%0d, bank=%0d, col=%0d, len=%0d",
                pattern_type, req.addr_bank, req.addr_col, req.burst_length), UVM_FULL)

            // Sequential address pattern
            pattern_type = (pattern_type + 1) % 4;
        end

        // Test column boundary crossing
        `uvm_info(get_name(), "Testing column boundary crossing", UVM_MEDIUM)
        for (int bank = 0; bank < 16; bank++) begin
            repeat (4) begin
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
            end
        end

        `uvm_info(get_name(), $sformatf("Burst pattern test completed: %0d bursts tested", num_bursts), UVM_MEDIUM)
    endtask
endclass