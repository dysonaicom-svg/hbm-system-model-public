// ------------------------------------------------------------
// test_bank_activation_conflict_seq.sv - HBM Bank Activation Conflict
// Tests rapid activation of the same bank (row hammer like)
// ------------------------------------------------------------
class test_bank_activation_conflict_seq extends hbm_base_sequence;
    `uvm_object_utils(test_bank_activation_conflict_seq)

    int num_activations = 200;
    bit [7:0] target_bank = 8'h05;
    int num_rows = 8;
    int activation_spacing = 4;  // Cycles between activations
    bit enable_row_hammer = 1;    // Enable row hammer pattern

    function new(string name = "test_bank_activation_conflict_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int row_idx;
        int cycle_count = 0;
        int conflict_count = 0;

        `uvm_info(get_name(), $sformatf("Starting BANK ACTIVATION CONFLICT test: bank=0x%02h, rows=%0d",
            target_bank, num_rows), UVM_MEDIUM)

        repeat (num_activations) begin
            req = new("req");
            start_item(req);

            // Row hammer pattern: alternating rows
            if (enable_row_hammer) begin
                row_idx = (cycle_count / 2) % num_rows;
            end else begin
                row_idx = cycle_count % num_rows;
            end

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == target_bank;
                addr_row == (row_idx * 256);  // Row spacing
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;

            // Track activation conflicts
            if (cycle_count > 1) begin
                conflict_count++;
                `uvm_info(get_name(), $sformatf("ACTIVATION CONFLICT: bank=0x%02h, row=0x%04h, conflict #%0d",
                    target_bank, row_idx * 256, conflict_count), UVM_HIGH)
            end

            // Short delay between activations
            #(5ns);
        end

        `uvm_info(get_name(), $sformatf("Bank activation conflict test completed: %0d activations, %0d conflicts",
            num_activations, conflict_count), UVM_MEDIUM)
    endtask
endclass