// ------------------------------------------------------------
// test_bank_group_conflict_seq.sv - HBM Bank Group Conflict Test
// Tests bank group conflicts where 4 banks share timing constraints
// ------------------------------------------------------------
class test_bank_group_conflict_seq extends hbm_base_sequence;
    `uvm_object_utils(test_bank_group_conflict_seq)

    int num_transactions = 100;
    int bank_group = 0;  // 0-3 for HBM4
    int banks_per_group = 4;
    int max_group_transactions = 10;

    function new(string name = "test_bank_group_conflict_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int bank_idx;
        int cycle_count = 0;

        `uvm_info(get_name(), $sformatf("Starting BANK GROUP CONFLICT test: group=%0d", bank_group), UVM_MEDIUM)

        // Generate rapid transactions within same bank group
        repeat (num_transactions) begin
            req = new("req");
            start_item(req);

            // Calculate bank within group
            bank_idx = bank_group * banks_per_group + (cycle_count % banks_per_group);

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == bank_idx;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            finish_item(req);

            cycle_count++;

            // Very short delay to trigger group conflict
            #(5ns);

            // Check for tRRD violation (minimum row activation interval)
            if (cycle_count > 1 && (cycle_count % banks_per_group) == 0) begin
                `uvm_info(get_name(), $sformatf("BANK GROUP CONFLICT: group=%0d, cycle=%0d, tRRD may be violated",
                    bank_group, cycle_count), UVM_MEDIUM)
            end
        end

        `uvm_info(get_name(), $sformatf("Bank group conflict test completed: %0d transactions in group %0d",
            num_transactions, bank_group), UVM_MEDIUM)
    endtask
endclass