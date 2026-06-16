// ------------------------------------------------------------
// test_stress_seq.sv - HBM Stress Test Sequence
// Exercises all 16 banks simultaneously with mixed traffic
// and bank conflicts to maximize coverage
// ------------------------------------------------------------
// Copyright (c) 2026. All rights reserved.
class test_stress_seq extends hbm_base_sequence;
    `uvm_object_utils(test_stress_seq)

    // Configuration
    int num_iterations = 100;
    int requests_per_bank = 10;
    int num_banks = 16;
    bit [3:0] read_write_ratio = 4'b1010;  // 50/50 by default

    // Bank tracking for conflict detection
    bit [15:0] bank_active_rows [16];
    int conflict_count = 0;
    int row_hammer_count = 0;

    // Priority levels for QoS coverage
    bit [3:0] priority_levels [16];

    function new(string name = "test_stress_seq");
        super.new(name);
        // Initialize priority levels
        priority_levels[0] = 4'd15;  // Critical
        priority_levels[1] = 4'd14;  // High
        priority_levels[2] = 4'd13;  // High
        priority_levels[3] = 4'd12;  // High
        priority_levels[4] = 4'd11;  // Medium-high
        priority_levels[5] = 4'd10;  // Medium-high
        priority_levels[6] = 4'd9;   // Medium
        priority_levels[7] = 4'd8;   // Medium
        priority_levels[8] = 4'd7;   // Medium-low
        priority_levels[9] = 4'd6;   // Medium-low
        priority_levels[10] = 4'd5;  // Medium-low
        priority_levels[11] = 4'd4;  // Low
        priority_levels[12] = 4'd3;  // Low
        priority_levels[13] = 4'd2;  // Low
        priority_levels[14] = 4'd1;  // Background
        priority_levels[15] = 4'd0;  // Background
    endfunction

    function void set_iterations(int iter);
        num_iterations = iter;
    endfunction

    function void set_requests_per_bank(int req);
        requests_per_bank = req;
    endfunction

    function void set_read_write_ratio(bit [3:0] ratio);
        read_write_ratio = ratio;
    endfunction

    // ------------------------------------------------------------
    // Phase 1: All Banks Simultaneously
    // ------------------------------------------------------------
    task phase1_all_banks_simultaneous();
        hbm_transaction req;
        bit [7:0] bank_id;
        bit [15:0] row_id;
        int request_idx = 0;

        `uvm_info(get_name(), "PHASE 1: All banks simultaneous access", UVM_MEDIUM)

        // Create parallel streams for all 16 banks
        fork
            for (int bank = 0; bank < num_banks; bank++) begin : bank_streams
                automatic int b = bank;
                fork
                    for (int r = 0; r < requests_per_bank; r++) begin
                        req = new("req");
                        start_item(req);

                        row_id = r * 256 + b;  // Unique row per bank

                        if (!req.randomize() with {
                            addr_bank == b;
                            addr_row == row_id;
                            addr_col inside {[0:3]};
                            req_priority == priority_levels[b];
                        }) begin
                            `uvm_error(get_name(), "Phase 1 randomization failed")
                        end

                        req.transaction_id = get_next_id();
                        req.qos_priority = priority_levels[b];

                        `uvm_info(get_name(), $sformatf("P1: bank=%02d, row=0x%04x, col=%d, pri=%d, id=%d",
                            b, row_id, req.addr_col, priority_levels[b], req.transaction_id), UVM_FULL)
                        finish_item(req);

                        bank_active_rows[b] = row_id;
                        #(5ns);
                    end
                join_none
            end : bank_streams
        join

        #50ns;  // Allow transactions to complete
    endtask : phase1_all_banks_simultaneous

    // ------------------------------------------------------------
    // Phase 2: Mixed Read/Write Traffic
    // ------------------------------------------------------------
    task phase2_mixed_traffic();
        hbm_transaction req;
        int transaction_count = 0;

        `uvm_info(get_name(), "PHASE 2: Mixed read/write traffic", UVM_MEDIUM)

        for (int i = 0; i < num_iterations; i++) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                addr_bank inside {[0:15]};
                addr_row inside {[0:65535]};
                addr_col inside {[0:3]};
                req_priority inside {[0:15]};
            }) begin
                `uvm_error(get_name(), "Phase 2 randomization failed")
            end

            req.transaction_id = get_next_id();

            // Determine read/write based on ratio
            if ((i[3:0] & read_write_ratio) == 0) begin
                req.cmd = hbm_transaction::READ;
            end else begin
                req.cmd = hbm_transaction::WRITE;
                req.wdata = {64{32'($random)}};
                req.wdata_mask = '0;
            end

            `uvm_info(get_name(), $sformatf("P2: %s bank=%02d, row=0x%04x, col=%d, pri=%d, id=%d",
                (req.cmd == hbm_transaction::READ) ? "READ" : "WRITE",
                req.addr_bank, req.addr_row, req.addr_col, req.req_priority, req.transaction_id), UVM_FULL)
            finish_item(req);

            transaction_count++;
            #(10ns);
        end

        `uvm_info(get_name(), $sformatf("Phase 2 completed: %0d transactions", transaction_count), UVM_MEDIUM)
    endtask : phase2_mixed_traffic

    // ------------------------------------------------------------
    // Phase 3: Bank Conflicts (Same Bank, Different Row)
    // ------------------------------------------------------------
    task phase3_bank_conflicts();
        hbm_transaction req;
        bit [7:0] target_bank;
        bit [15:0] last_row;
        int conflict_iterations = 20;

        `uvm_info(get_name(), "PHASE 3: Bank conflicts (same bank, different rows)", UVM_MEDIUM)

        // Test conflicts on multiple banks
        for (int bank = 0; bank < 8; bank++) begin  // Test 8 banks for conflicts
            target_bank = bank;
            last_row = 16'hFFFF;  // Start with different row

            for (int i = 0; i < conflict_iterations; i++) begin
                req = new("req");
                start_item(req);

                // Alternate between rows to create conflicts
                if (i % 2 == 0) begin
                    req.addr_row = (bank * 256) + (i % 16);  // Row group A
                end else begin
                    req.addr_row = (bank * 256) + 256 + (i % 16);  // Row group B
                end

                if (!req.randomize() with {
                    addr_bank == target_bank;
                    addr_row == req.addr_row;
                    addr_col inside {[0:3]};
                    req_priority == priority_levels[bank];
                }) begin
                    `uvm_error(get_name(), "Phase 3 randomization failed")
                end

                req.transaction_id = get_next_id();

                // Detect conflict
                if (last_row != req.addr_row && last_row != 16'hFFFF) begin
                    conflict_count++;
                    `uvm_info(get_name(), $sformatf("P3 CONFLICT: bank=%02d, last_row=0x%04x, new_row=0x%04x, id=%d",
                        target_bank, last_row, req.addr_row, req.transaction_id), UVM_HIGH)
                end

                last_row = req.addr_row;

                `uvm_info(get_name(), $sformatf("P3: bank=%02d, row=0x%04x, col=%d, pri=%d, id=%d",
                    target_bank, req.addr_row, req.addr_col, req.req_priority, req.transaction_id), UVM_FULL)
                finish_item(req);

                bank_active_rows[target_bank] = req.addr_row;
                #(15ns);  // Shorter delay to increase conflicts
            end
        end

        `uvm_info(get_name(), $sformatf("Phase 3 completed: %0d bank conflicts detected", conflict_count), UVM_MEDIUM)
    endtask : phase3_bank_conflicts

    // ------------------------------------------------------------
    // Phase 4: Row Hammer Pattern Detection
    // ------------------------------------------------------------
    task phase4_row_hammer();
        hbm_transaction req;
        bit [7:0] hammer_bank = 8'h05;
        bit [15:0] hammer_row = 16'h1234;
        int hammer_threshold = 50;
        bit [15:0] activation_count = 0;

        `uvm_info(get_name(), "PHASE 4: Row hammer pattern exercise", UVM_MEDIUM)

        // Repeatedly activate same row to exercise row hammer detection
        for (int i = 0; i < hammer_threshold; i++) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                addr_bank == hammer_bank;
                addr_row == hammer_row;
                addr_col == 0;
                req_priority == 4'd15;  // Always critical for hammer
            }) begin
                `uvm_error(get_name(), "Phase 4 randomization failed")
            end

            req.transaction_id = get_next_id();
            activation_count++;

            `uvm_info(get_name(), $sformatf("P4 HAMMER: bank=%02d, row=0x%04x, count=%0d, id=%d",
                hammer_bank, hammer_row, activation_count, req.transaction_id), UVM_HIGH)
            finish_item(req);

            #(5ns);  // Rapid activation for hammer test
        end

        row_hammer_count = activation_count;

        // Now exercise adjacent rows
        hammer_row = 16'h1235;
        for (int i = 0; i < 10; i++) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                addr_bank == hammer_bank;
                addr_row == hammer_row;
                addr_col == 0;
                req_priority == 4'd15;
            }) begin
                `uvm_error(get_name(), "Phase 4 adjacent row randomization failed")
            end

            req.transaction_id = get_next_id();

            `uvm_info(get_name(), $sformatf("P4 ADJACENT: bank=%02d, row=0x%04x, id=%d",
                hammer_bank, hammer_row, req.transaction_id), UVM_HIGH)
            finish_item(req);

            #(10ns);
        end

        `uvm_info(get_name(), $sformatf("Phase 4 completed: %0d activations on row hammer target", row_hammer_count), UVM_MEDIUM)
    endtask : phase4_row_hammer

    // ------------------------------------------------------------
    // Phase 5: Refresh Command Exercise
    // ------------------------------------------------------------
    task phase5_refresh_commands();
        hbm_transaction req;
        int refresh_count = 10;

        `uvm_info(get_name(), "PHASE 5: Refresh command exercise", UVM_MEDIUM)

        for (int i = 0; i < refresh_count; i++) begin
            // Refresh each bank group
            for (int bank = 0; bank < 16; bank++) begin
                req = new("req");
                start_item(req);

                if (!req.randomize() with {
                    addr_bank == bank;
                    addr_row == 16'h0000;
                    addr_col == 0;
                }) begin
                    `uvm_error(get_name(), "Phase 5 randomization failed")
                end

                req.transaction_id = get_next_id();
                // Mark as refresh command (using special encoding)
                req.cmd = hbm_transaction::REFRESH;

                `uvm_info(get_name(), $sformatf("P5 REFRESH: bank=%02d, id=%d", bank, req.transaction_id), UVM_FULL)
                finish_item(req);

                #(5ns);
            end

            // tRFC delay (HBM3/4: ~230ns)
            #250ns;
        end

        `uvm_info(get_name(), $sformatf("Phase 5 completed: %0d refresh operations", refresh_count), UVM_MEDIUM)
    endtask : phase5_refresh_commands

    // ------------------------------------------------------------
    // Phase 6: Channel Interleaving
    // ------------------------------------------------------------
    task phase6_channel_interleaving();
        hbm_transaction req;
        int num_channels = 8;
        int requests_per_channel = 20;

        `uvm_info(get_name(), "PHASE 6: Channel interleaving", UVM_MEDIUM)

        // Round-robin across channels
        for (int i = 0; i < requests_per_channel; i++) begin
            fork
                for (int ch = 0; ch < num_channels; ch++) begin : ch_stream
                    automatic int c = ch;
                    req = new("req");
                    start_item(req);

                    if (!req.randomize() with {
                        addr_bank == (c % 16);
                        addr_row == (i * 256 + c);
                        addr_col inside {[0:3]};
                        req_priority == priority_levels[c];
                    }) begin
                        `uvm_error(get_name(), "Phase 6 randomization failed")
                    end

                    req.transaction_id = get_next_id();

                    `uvm_info(get_name(), $sformatf("P6 INTERLEAVE: channel=%d, bank=%02d, row=0x%04x, id=%d",
                        c, req.addr_bank, req.addr_row, req.transaction_id), UVM_FULL)
                    finish_item(req);

                    bank_active_rows[req.addr_bank] = req.addr_row;
                end : ch_stream
            join
            #20ns;
        end

        `uvm_info(get_name(), $sformatf("Phase 6 completed: %0d interleaved requests", requests_per_channel * num_channels), UVM_MEDIUM)
    endtask : phase6_channel_interleaving

    // ------------------------------------------------------------
    // Main Body
    // ------------------------------------------------------------
    task body();
        `uvm_info(get_name(), $sformatf("Starting STRESS test: iterations=%0d, banks=%0d, req/bank=%0d",
            num_iterations, num_banks, requests_per_bank), UVM_MEDIUM)

        // Initialize bank tracking
        for (int b = 0; b < 16; b++) begin
            bank_active_rows[b] = 16'hFFFF;
        end

        // Execute all phases
        fork
            phase1_all_banks_simultaneous();
            phase2_mixed_traffic();
            phase3_bank_conflicts();
            phase4_row_hammer();
            phase5_refresh_commands();
            phase6_channel_interleaving();
        join

        `uvm_info(get_name(), $sformatf("STRESS test completed: %0d conflicts, %0d hammer activations",
            conflict_count, row_hammer_count), UVM_MEDIUM)
    endtask : body

endclass : test_stress_seq
