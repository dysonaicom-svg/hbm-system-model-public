// ------------------------------------------------------------
// test_bank_conflict_seq.sv - HBM Bank Conflict Test Sequence
// Generates transactions to same bank with different rows
// to trigger row conflicts
// ------------------------------------------------------------
// Copyright (c) 2026. All rights reserved.
class test_bank_conflict_seq extends hbm_base_sequence;
    `uvm_object_utils(test_bank_conflict_seq)

    int repeat_count = 50;
    bit [7:0] target_bank = 8'h00;
    int num_rows = 16;  // Cycle through 16 different rows

    function new(string name = "test_bank_conflict_seq");
        super.new(name);
    endfunction

    function void set_target_bank(bit [7:0] bank);
        target_bank = bank;
    endfunction

    function void set_num_rows(int rows);
        num_rows = rows;
    endfunction

    task body();
        hbm_transaction req;
        int row_idx;
        bit [15:0] row_addr;

        `uvm_info(get_name(), $sformatf("Starting BANK CONFLICT sequence: bank=0x%02h, %0d rows",
            target_bank, num_rows), UVM_MEDIUM)

        repeat (repeat_count) begin
            req = new("req");
            start_item(req);

            // Rotate through different rows to trigger conflicts
            row_idx = (req.transaction_id - 1) % num_rows;
            row_addr = row_idx * 256;  // Each row is 256 apart

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == target_bank;
                addr_row == row_addr;
                addr_col inside {[0:3]};
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("CONFLICT: bank=0x%02h, row=0x%04h, col=%0d, id=%0d (row_idx=%0d)",
                req.addr_bank, req.addr_row, req.addr_col, req.transaction_id, row_idx), UVM_FULL)
            finish_item(req);

            // Small delay between conflicts
            #(20ns);
        end

        `uvm_info(get_name(), "BANK CONFLICT sequence completed", UVM_MEDIUM)
    endtask
endclass