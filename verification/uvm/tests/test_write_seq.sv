// ------------------------------------------------------------
// test_write_seq.sv - HBM Write Test Sequence
// Generates 100 write transactions with random addresses and data
// ------------------------------------------------------------
// Copyright (c) 2026. All rights reserved.
class test_write_seq extends hbm_base_sequence;
    `uvm_object_utils(test_write_seq)

    int repeat_count = 100;
    bit [511:0] data_pattern = 'hDEADBEEF;

    function new(string name = "test_write_seq");
        super.new(name);
    endfunction

    function void set_repeat_count(int count);
        repeat_count = count;
    endfunction

    task body();
        hbm_transaction req;

        `uvm_info(get_name(), $sformatf("Starting WRITE sequence with %0d transactions", repeat_count), UVM_MEDIUM)

        repeat (repeat_count) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                cmd == hbm_transaction::WRITE;
                addr_bank inside {['h00:'h0F]};
                addr_row inside {['h0000:'hFFFF]};
                addr_col inside {[0:3]};
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            req.wdata = data_pattern;
            req.wdata_mask = '0;  // All bytes valid

            `uvm_info(get_name(), $sformatf("WRITE: bank=0x%02h, row=0x%04h, col=%0d, id=%0d",
                req.addr_bank, req.addr_row, req.addr_col, req.transaction_id), UVM_FULL)
            finish_item(req);

            #(10ns);
        end

        `uvm_info(get_name(), "WRITE sequence completed", UVM_MEDIUM)
    endtask
endclass