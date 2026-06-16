// ------------------------------------------------------------
// test_refresh_seq.sv - HBM Refresh Test Sequence
// Generates refresh commands for all banks
// ------------------------------------------------------------
// Copyright (c) 2026. All rights reserved.
class test_refresh_seq extends hbm_base_sequence;
    `uvm_object_utils(test_refresh_seq)

    int repeat_count = 10;
    int banks_per_refresh = 16;

    function new(string name = "test_refresh_seq");
        super.new(name);
    endfunction

    function void set_repeat_count(int count);
        repeat_count = count;
    endfunction

    task body();
        hbm_transaction req;
        int bank_idx;

        `uvm_info(get_name(), $sformatf("Starting REFRESH sequence: %0d refreshes", repeat_count), UVM_MEDIUM)

        repeat (repeat_count) begin
            // Refresh all banks
            for (bank_idx = 0; bank_idx < banks_per_refresh; bank_idx++) begin
                req = new("req");
                start_item(req);

                if (!req.randomize() with {
                    // Use bank field to indicate refresh
                    addr_bank == bank_idx;
                    addr_row == 16'h0000;
                    addr_col == 2'h0;
                }) begin
                    `uvm_error(get_name(), "Randomization failed")
                end

                req.transaction_id = get_next_id();
                `uvm_info(get_name(), $sformatf("REFRESH bank %0d/%0d, id=%0d",
                    bank_idx + 1, banks_per_refresh, req.transaction_id), UVM_FULL)
                finish_item(req);

                // Inter-bank delay
                #(5ns);
            end

            // tRFC delay (HBM3: ~230ns for full refresh)
            #(250ns);
        end

        `uvm_info(get_name(), "REFRESH sequence completed", UVM_MEDIUM)
    endtask
endclass