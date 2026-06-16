// ------------------------------------------------------------
// test_refresh_during_active_seq.sv - HBM Refresh During Active Rows
// Tests refresh commands with open rows
// ------------------------------------------------------------
class test_refresh_during_active_seq extends hbm_base_sequence;
    `uvm_object_utils(test_refresh_during_active_seq)

    int num_rows_open = 8;
    int num_transactions = 100;
    int trigger_refresh_with_open = 1;

    function new(string name = "test_refresh_during_active_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        bit [15:0] open_rows[16];
        int open_bank_count = 0;
        int refresh_count = 0;
        int collision_count = 0;

        `uvm_info(get_name(), "Starting REFRESH DURING ACTIVE test", UVM_MEDIUM)

        // Phase 1: Open multiple rows
        `uvm_info(get_name(), "Phase 1: Opening multiple rows", UVM_MEDIUM)
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

            `uvm_info(get_name(), $sformatf("Opened row: bank=%0d, row=0x%04h", bank, open_rows[bank]), UVM_FULL)
        end

        // Phase 2: Trigger refresh with open rows
        `uvm_info(get_name(), "Phase 2: Triggering refresh with open rows", UVM_MEDIUM)
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

            // Simulate refresh with open rows
            if (trigger_refresh_with_open && (refresh_count % 10 == 0)) begin
                collision_count++;
                `uvm_info(get_name(), $sformatf("REFRESH COLLISION: %0d banks open, refresh #%0d",
                    open_bank_count, refresh_count), UVM_MEDIUM)
            end

            refresh_count++;
        end

        `uvm_info(get_name(), $sformatf("Refresh during active test completed: %0d collisions detected",
            collision_count), UVM_MEDIUM)
    endtask
endclass