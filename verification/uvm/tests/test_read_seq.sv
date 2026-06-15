// ------------------------------------------------------------
// test_read_seq.sv - HBM Read Test Sequence
// Generates 100 read transactions with random addresses
// ------------------------------------------------------------
// Copyright (c) 2026. All rights reserved.
class test_read_seq extends hbm_base_sequence;
    `uvm_object_utils(test_read_seq)

    int repeat_count = 100;
    bit [7:0] bank_base = 8'h00;

    function new(string name = "test_read_seq");
        super.new(name);
    endfunction

    function void set_repeat_count(int count);
        repeat_count = count;
    endfunction

    task body();
        hbm_transaction req;

        `uvm_info(get_name(), $sformatf("Starting READ sequence with %0d transactions", repeat_count), UVM_MEDIUM)

        repeat (repeat_count) begin
            req = hbm_transaction::type_id::create("req");
            start_item(req);

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank inside {['h00:'h0F]};  // Banks 0-15
                addr_row inside {['h0000:'hFFFF]};
                addr_col inside {[0:3]};
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            `uvm_info(get_name(), $sformatf("READ: bank=0x%02h, row=0x%04h, col=%0d, id=%0d",
                req.addr_bank, req.addr_row, req.addr_col, req.transaction_id), UVM_FULL)
            finish_item(req);

            // Small delay between transactions
            #(10ns);
        end

        `uvm_info(get_name(), "READ sequence completed", UVM_MEDIUM)
    endtask
endclass