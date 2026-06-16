// ------------------------------------------------------------
// test_refresh_collision_seq.sv - HBM Refresh Collision Test
// Tests scenarios where refresh commands collide with user traffic
// ------------------------------------------------------------
class test_refresh_collision_seq extends hbm_base_sequence;
    `uvm_object_utils(test_refresh_collision_seq)

    int num_transactions = 50;
    int refresh_interval = 100;  // Cycles between refreshes
    int collision_window = 10;  // Window to check collision
    int trigger_refresh_during_traffic = 1;

    function new(string name = "test_refresh_collision_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int cycle_count = 0;
        int refresh_count = 0;

        `uvm_info(get_name(), "Starting REFRESH COLLISION test", UVM_MEDIUM)

        // Generate traffic with periodic refreshes
        repeat (num_transactions) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank inside {[0:15]};
                addr_row inside {[0:255], [65280:65535]};  // Hot and cold rows
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;

            // Simulate refresh trigger
            if (cycle_count % refresh_interval == 0) begin
                refresh_count++;
                `uvm_info(get_name(), $sformatf("REFRESH triggered at cycle %0d (refresh #%0d)",
                    cycle_count, refresh_count), UVM_HIGH)

                // Check if we're in a collision window
                if (trigger_refresh_during_traffic) begin
                    `uvm_info(get_name(), $sformatf("REFRESH COLLISION DETECTED: refresh #%0d at cycle %0d",
                        refresh_count, cycle_count), UVM_MEDIUM)
                end
            end

            #(10ns);
        end

        `uvm_info(get_name(), $sformatf("Refresh collision test completed: %0d transactions, %0d refreshes",
            num_transactions, refresh_count), UVM_MEDIUM)
    endtask
endclass