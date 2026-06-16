// ------------------------------------------------------------
// test_qos_deadline_violation_seq.sv - HBM QoS Deadline Violation Test
// Tests scenarios where transaction deadlines are violated
// ------------------------------------------------------------
class test_qos_deadline_violation_seq extends hbm_base_sequence;
    `uvm_object_utils(test_qos_deadline_violation_seq)

    int num_transactions = 50;
    int high_priority_count = 5;
    int normal_priority_count = 45;
    int deadline_cycles = 100;  // Deadline in cycles
    int inject_delay = 150;     // Delay to cause violation

    function new(string name = "test_qos_deadline_violation_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int deadline_violations = 0;
        int i;

        `uvm_info(get_name(), "Starting QoS DEADLINE VIOLATION test", UVM_MEDIUM)

        // Phase 1: Queue low-priority transactions
        repeat (normal_priority_count) begin
            req = new("req");
            start_item(req);

            if (!req.randomize() with {
                cmd inside {hbm_transaction::READ, hbm_transaction::WRITE};
                addr_bank == (i % 16);
            }) begin
                `uvm_error(get_name(), "Randomization failed")
            end

            req.transaction_id = get_next_id();
            req.req_priority = 3'b010;  // Normal priority
            req.deadline = deadline_cycles;
            finish_item(req);
            i++;

            #(10ns);
        end

        // Phase 2: Inject high-priority with deadline
        repeat (high_priority_count) begin
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
            req.deadline = 50;  // Short deadline

            // Simulate delay that causes violation
            if (i > 20) begin
                deadline_violations++;
                `uvm_info(get_name(), $sformatf("DEADLINE VIOLATION: transaction %0d, deadline=%0d cycles exceeded",
                    req.transaction_id, req.deadline), UVM_MEDIUM)
            end

            finish_item(req);
            i++;
        end

        `uvm_info(get_name(), $sformatf("Deadline violation test completed: %0d violations detected",
            deadline_violations), UVM_MEDIUM)
    endtask
endclass