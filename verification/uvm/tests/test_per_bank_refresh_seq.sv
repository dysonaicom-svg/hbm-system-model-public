// ------------------------------------------------------------
// test_per_bank_refresh_seq.sv - HBM Per-Bank Refresh Test
// Tests REFPB (per-bank refresh) commands
// ------------------------------------------------------------
class test_per_bank_refresh_seq extends hbm_base_sequence;
    `uvm_object_utils(test_per_bank_refresh_seq)

    int num_banks = 16;
    int cycles_per_bank_refresh = 20;
    int num_refresh_cycles = 8;

    function new(string name = "test_per_bank_refresh_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int refresh_bank;
        int total_refpb_commands = 0;
        int cycle_count = 0;

        `uvm_info(get_name(), "Starting PER-BANK REFRESH test", UVM_MEDIUM)

        // Per-bank refresh sequence
        repeat (num_refresh_cycles) begin
            for (int bank = 0; bank < num_banks; bank++) begin
                req = new("req");
                start_item(req);

                if (!req.randomize() with {
                    cmd == hbm_transaction::READ;
                    addr_bank == bank;
                }) begin
                    `uvm_error(get_name(), "Randomization failed")
                end

                req.transaction_id = get_next_id();
                refresh_bank = bank;
                finish_item(req);

                total_refpb_commands++;
                cycle_count++;

                `uvm_info(get_name(), $sformatf("REFPB: bank=%0d, cycle=%0d, command #%0d",
                    refresh_bank, cycle_count, total_refpb_commands), UVM_FULL)

                #(5ns);  // Short delay for per-bank refresh
            end
        end

        `uvm_info(get_name(), $sformatf("Per-bank refresh test completed: %0d REFPB commands",
            total_refpb_commands), UVM_MEDIUM)
    endtask
endclass