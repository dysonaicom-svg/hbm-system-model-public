// ------------------------------------------------------------
// test_multi_bank_round_robin_seq.sv - HBM Round-Robin Bank Scheduling
// Tests fair round-robin scheduling across all banks
// ------------------------------------------------------------
class test_multi_bank_round_robin_seq extends hbm_base_sequence;
    `uvm_object_utils(test_multi_bank_round_robin_seq)

    int transactions_per_bank = 10;
    int num_banks = 16;
    int total_transactions;
    int bank_service_count[16];

    function new(string name = "test_multi_bank_round_robin_seq");
        super.new(name);
    endfunction

    function void build();
        super.build();
        for (int i = 0; i < 16; i++) begin
            bank_service_count[i] = 0;
        end
    endfunction

    task body();
        hbm_transaction req;
        int bank_idx;
        int cycle = 0;
        real fairness_score;

        `uvm_info(get_name(), "Starting ROUND-ROBIN BANK SCHEDULING test", UVM_MEDIUM)

        total_transactions = transactions_per_bank * num_banks;

        // Round-robin through all banks
        for (int i = 0; i < total_transactions; i++) begin
            req = new("req");
            start_item(req);

            // Round-robin bank selection
            bank_idx = i % num_banks;

            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank == bank_idx;
                addr_row == (i / num_banks) * 256;  // Different row per pass
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            req.req_priority = 3'b010;  // Normal priority
            finish_item(req);

            bank_service_count[bank_idx]++;
            cycle++;

            #(10ns);
        end

        // Calculate fairness
        fairness_score = calculate_fairness();

        `uvm_info(get_name(), "Round-robin bank scheduling test completed", UVM_MEDIUM)
        `uvm_info(get_name(), $sformatf("Fairness score: %.2f%%", fairness_score), UVM_MEDIUM)

        // Report per-bank service counts
        for (int i = 0; i < num_banks; i++) begin
            `uvm_info(get_name(), $sformatf("Bank %0d serviced: %0d times", i, bank_service_count[i]), UVM_FULL)
        end
    endtask

    function real calculate_fairness();
        real avg;
        real variance;
        real sum;
        int min_count;
        int max_count;

        avg = real'(total_transactions) / real'(num_banks);
        min_count = bank_service_count[0];
        max_count = bank_service_count[0];

        for (int i = 0; i < num_banks; i++) begin
            sum += real'(bank_service_count[i]);
            if (bank_service_count[i] < min_count) min_count = bank_service_count[i];
            if (bank_service_count[i] > max_count) max_count = bank_service_count[i];
        end

        variance = (real'(max_count - min_count)) / avg * 100.0;
        return 100.0 - variance;
    endfunction
endclass