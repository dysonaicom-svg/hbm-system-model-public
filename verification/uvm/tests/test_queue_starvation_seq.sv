// ------------------------------------------------------------
// test_queue_starvation_seq.sv - HBM Queue Starvation Test
// Tests starvation scenarios where some requests never get serviced
// ------------------------------------------------------------
class test_queue_starvation_seq extends hbm_base_sequence;
    `uvm_object_utils(test_queue_starvation_seq)

    int num_low_priority = 100;
    int num_high_priority = 10;
    int max_queue_depth = 32;
    int check_starvation = 1;

    function new(string name = "test_queue_starvation_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int low_prio_queued = 0;
        int high_prio_queued = 0;
        int starvation_threshold = 50;

        `uvm_info(get_name(), "Starting QUEUE STARVATION test", UVM_MEDIUM)

        // Phase 1: Fill queue with low-priority requests
        `uvm_info(get_name(), "Phase 1: Filling queue with low-priority", UVM_MEDIUM)
        repeat (num_low_priority) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank inside {[0:15]};
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            req.req_priority = 3'b011;  // Low priority
            finish_item(req);
            low_prio_queued++;

            // Check for starvation after threshold
            if (check_starvation && low_prio_queued > starvation_threshold) begin
                `uvm_info(get_name(), $sformatf("STARVATION WARNING: %0d low-priority requests queued, may be starved",
                    low_prio_queued), UVM_MEDIUM)
            end
        end

        // Phase 2: Inject high-priority requests
        `uvm_info(get_name(), "Phase 2: Injecting high-priority requests", UVM_MEDIUM)
        repeat (num_high_priority) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                cmd == hbm_transaction::WRITE;
                addr_bank == 0;
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            req.req_priority = 3'b000;  // Critical priority
            finish_item(req);
            high_prio_queued++;
        end

        // Phase 3: Verify low-priority starvation
        `uvm_info(get_name(), $sformatf("STARVATION ANALYSIS: %0d low-prio queued, %0d high-prio queued",
            low_prio_queued, high_prio_queued), UVM_MEDIUM)

        `uvm_info(get_name(), "Queue starvation test completed", UVM_MEDIUM)
    endtask
endclass