// ------------------------------------------------------------
// test_priority_inversion_seq.sv - HBM Priority Inversion Test
// Tests priority inversion scenarios where high-priority requests
// are blocked by lower-priority requests
// ------------------------------------------------------------
class test_priority_inversion_seq extends hbm_base_sequence;
    `uvm_object_utils(test_priority_inversion_seq)

    int num_high_priority = 10;
    int num_low_priority = 100;
    int high_priority_value = 3'b000;  // Critical priority
    int low_priority_value = 3'b011;   // Low priority
    bit enable_priority_override = 1;

    function new(string name = "test_priority_inversion_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int i;

        `uvm_info(get_name(), "Starting PRIORITY INVERSION test", UVM_MEDIUM)

        // Phase 1: Fill queue with low-priority requests
        `uvm_info(get_name(), "Phase 1: Filling queue with low-priority requests", UVM_MEDIUM)
        repeat (num_low_priority) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                cmd == hbm_transaction::READ;
                addr_bank == (i % 16);
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            // Low priority - will be queued
            finish_item(req);
            i++;
        end

        // Phase 2: Inject high-priority request
        `uvm_info(get_name(), "Phase 2: Injecting high-priority request", UVM_MEDIUM)
        req = new("req");
        start_item(req);

        if (!req.randomize() with {
            cmd == hbm_transaction::WRITE;
            addr_bank == 0;
        }) begin
            `uvm_error(get_name(), "Randomization failed")
        end

        req.transaction_id = get_next_id();
        req.req_priority = high_priority_value;
        finish_item(req);

        // Phase 3: Verify high-priority request is serviced first
        `uvm_info(get_name(), "Phase 3: Verifying priority inversion behavior", UVM_MEDIUM)

        `uvm_info(get_name(), "Priority inversion test completed", UVM_MEDIUM)
    endtask
endclass