// ------------------------------------------------------------
// hbm_env_pkg.sv - HBM UVM Environment Package
// Simplified for Verilator compatibility
// ------------------------------------------------------------
package hbm_env_pkg;

import uvm_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Constants and Types
// ------------------------------------------------------------
`define HBM_MAX_BANKS 16
`define HBM_MAX_CHANNELS 8

typedef enum logic [2:0] {
    HBM_CMD_IDLE   = 3'b000,
    HBM_CMD_WRITE  = 3'b001,
    HBM_CMD_READ   = 3'b010,
    HBM_CMD_ACT    = 3'b011,
    HBM_CMD_PRE    = 3'b100,
    HBM_CMD_REF    = 3'b101
} hbm_cmd_t;

// ------------------------------------------------------------
// Agent Configuration Class
// ------------------------------------------------------------
class hbm_agent_config extends uvm_object;
    `uvm_object_utils(hbm_agent_config)

    bit is_active = 1;
    bit has_checks = 1;
    bit has_coverage = 1;
    string name_tag = "hbm_agent";

    `uvm_field_utils(hbm_agent_config)

    function new(string name = "hbm_agent_config");
        super.new(name);
    endfunction

    function void set_name_tag(string tag);
        name_tag = tag;
    endfunction
endclass

// ------------------------------------------------------------
// AXI4 Agent Configuration
// ------------------------------------------------------------
class axi4_agent_config extends uvm_object;
    `uvm_object_utils(axi4_agent_config)

    bit is_active = 1;
    bit has_checks = 1;
    bit has_coverage = 1;
    string name_tag = "axi4_agent";

    `uvm_field_utils(axi4_agent_config)

    function new(string name = "axi4_agent_config");
        super.new(name);
    endfunction
endclass

// ------------------------------------------------------------
// Transaction Item
// ------------------------------------------------------------
class hbm_transaction extends uvm_sequence_item;
    `uvm_object_utils(hbm_transaction)

    typedef enum {READ, WRITE} cmd_t;
    rand cmd_t        cmd;
    rand bit [7:0]    addr_bank;
    rand bit [15:0]   addr_row;
    rand bit [1:0]    addr_col;
    rand bit [511:0]  wdata;
    rand bit [511:0]  wdata_mask;
    bit    [511:0]    rdata;
    bit               rdata_valid;
    bit   [31:0]      transaction_id;
    bit   [63:0]      timestamp;

    // Constraints for valid ranges
    constraint valid_bank { addr_bank < `HBM_MAX_BANKS; }
    constraint valid_col { addr_col < 4; }

    function new(string name = "hbm_transaction");
        super.new(name);
    endfunction

    function void do_copy(uvm_object rhs);
        hbm_transaction tr;
        super.do_copy(rhs);
        if ($cast(tr, rhs)) begin
            cmd         = tr.cmd;
            addr_bank   = tr.addr_bank;
            addr_row    = tr.addr_row;
            addr_col    = tr.addr_col;
            wdata       = tr.wdata;
            wdata_mask  = tr.wdata_mask;
            rdata       = tr.rdata;
            rdata_valid = tr.rdata_valid;
            transaction_id = tr.transaction_id;
            timestamp    = tr.timestamp;
        end
    endfunction

    function string convert2string();
        string s;
        s = $sformatf("id=%0d cmd=%s bank=%h row=%h col=%h",
                      transaction_id, cmd.name(), addr_bank, addr_row, addr_col);
        if (cmd == WRITE)
            s = {s, $sformatf(" wdata=%h mask=%h", wdata, wdata_mask)};
        else
            s = {s, $sformatf(" rdata=%h valid=%b", rdata, rdata_valid)};
        return s;
    endfunction

    function bit do_compare(uvm_object rhs);
        hbm_transaction tr;
        do_compare = ($cast(tr, rhs) && cmd == tr.cmd &&
                      addr_bank == tr.addr_bank && addr_row == tr.addr_row &&
                      addr_col == tr.addr_col);
    endfunction

    function void post_randomize();
        timestamp = $time;
    endfunction
endclass

// ------------------------------------------------------------
// AXI4 Transaction
// ------------------------------------------------------------
class axi4_transaction extends uvm_sequence_item;
    `uvm_object_utils(axi4_transaction)

    typedef enum {AXI_READ, AXI_WRITE} axi_cmd_t;
    rand axi_cmd_t cmd;
    rand bit [31:0] addr;
    rand bit [511:0] wdata;
    bit    [511:0] rdata;
    rand bit [7:0] len;
    rand bit [2:0] size;
    rand bit [1:0] burst;
    rand bit [63:0] wstrb;
    bit [1:0] resp;
    bit [31:0] transaction_id;

    constraint valid_addr { addr[26:0] == 0; }  // 128MB boundary
    constraint valid_size { size inside {0, 2, 4, 6}; }  // 1, 4, 16, 64 bytes

    function new(string name = "axi4_transaction");
        super.new(name);
        size = 6;  // 64 bytes default (HBM burst size)
        burst = 1;  // INCR burst
        len = 0;   // Single beat
    endfunction

    function string convert2string();
        string s;
        s = $sformatf("id=%0d cmd=%s addr=%h", transaction_id, cmd.name(), addr);
        if (cmd == AXI_WRITE)
            s = {s, $sformatf(" wdata=%h strb=%h", wdata, wstrb)};
        else
            s = {s, $sformatf(" rdata=%h resp=%b", rdata, resp)};
        return s;
    endfunction
endclass

// ------------------------------------------------------------
// HBM Driver (Simplified)
// ------------------------------------------------------------
class hbm_driver extends uvm_driver #(hbm_transaction);
    `uvm_component_utils(hbm_driver)

    int drive_count = 0;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        hbm_transaction req;
        forever begin
            seq_item_port.get_next_item(req);
            drive_transaction(req);
            seq_item_port.item_done();
            drive_count++;
        end
    endtask

    task drive_transaction(hbm_transaction tr);
        `uvm_info(get_name(), $sformatf("Driving: %s", tr.convert2string()), UVM_HIGH)
        #10;
    endtask
endclass

// ------------------------------------------------------------
// AXI4 Driver (Simplified)
// ------------------------------------------------------------
class axi4_driver extends uvm_driver #(axi4_transaction);
    `uvm_component_utils(axi4_driver)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        axi4_transaction req;
        forever begin
            seq_item_port.get_next_item(req);
            `uvm_info(get_name(), $sformatf("Driving AXI: %s", req.convert2string()), UVM_HIGH)
            seq_item_port.item_done();
        end
    endtask
endclass

// ------------------------------------------------------------
// HBM Monitor (Simplified)
// ------------------------------------------------------------
class hbm_monitor extends uvm_monitor;
    `uvm_component_utils(hbm_monitor)

    uvm_analysis_port #(hbm_transaction) ap;
    int monitor_count = 0;

    // Pending read transactions waiting for data return
    hbm_transaction pending_reads[$];
    bit [511:0] captured_rdata;
    bit captured_rdata_valid;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    task run_phase(uvm_phase phase);
        hbm_transaction tr;
        forever begin
            #5;
            // Simulated monitoring
            monitor_count++;
        end
    endtask

    // Function to receive data from testbench
    function void receive_read_data(bit [511:0] rdata);
        captured_rdata = rdata;
        captured_rdata_valid = 1'b1;

        if (pending_reads.size() > 0) begin
            hbm_transaction pending_tr = pending_reads.pop_front();
            pending_tr.rdata = captured_rdata[255:0];
            pending_tr.rdata_valid = 1'b1;
            `uvm_info(get_name(), $sformatf("Read data captured: %h", captured_rdata[255:0]), UVM_HIGH)
            ap.write(pending_tr);
        end
    endfunction
endclass

// ------------------------------------------------------------
// AXI4 Monitor (Simplified)
// ------------------------------------------------------------
class axi4_monitor extends uvm_monitor;
    `uvm_component_utils(axi4_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        forever begin
            #5;
        end
    endtask
endclass

// ------------------------------------------------------------
// HBM Sequencer
// ------------------------------------------------------------
class hbm_sequencer extends uvm_sequencer #(hbm_transaction);
    `uvm_component_utils(hbm_sequencer)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass

// ------------------------------------------------------------
// AXI4 Sequencer
// ------------------------------------------------------------
class axi4_sequencer extends uvm_sequencer #(axi4_transaction);
    `uvm_component_utils(axi4_sequencer)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass

// ------------------------------------------------------------
// HBM Agent
// ------------------------------------------------------------
class hbm_agent extends uvm_agent;
    `uvm_component_utils(hbm_agent)

    hbm_driver     driver;
    hbm_monitor    monitor;
    hbm_sequencer  sequencer;
    hbm_agent_config cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(hbm_agent_config)::get(this, "", "cfg", cfg))
            cfg = hbm_agent_config::type_id::create("cfg");
        if (is_active) begin
            sequencer = hbm_sequencer::type_id::create("sequencer", this);
            driver    = hbm_driver::type_id::create("driver", this);
        end
        monitor = hbm_monitor::type_id::create("monitor", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if (is_active && driver != null && sequencer != null)
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction
endclass

// ------------------------------------------------------------
// AXI4 Agent
// ------------------------------------------------------------
class axi4_agent extends uvm_agent;
    `uvm_component_utils(axi4_agent)

    axi4_driver    driver;
    axi4_monitor  monitor;
    axi4_sequencer sequencer;
    axi4_agent_config cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi4_agent_config)::get(this, "", "cfg", cfg))
            cfg = axi4_agent_config::type_id::create("cfg");
        if (is_active) begin
            sequencer = axi4_sequencer::type_id::create("sequencer", this);
            driver    = axi4_driver::type_id::create("driver", this);
        end
        monitor = axi4_monitor::type_id::create("monitor", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if (is_active && driver != null && sequencer != null)
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction
endclass

// ------------------------------------------------------------
// Scoreboard
// ------------------------------------------------------------
class hbm_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(hbm_scoreboard)

    // Internal queues for comparison
    hbm_transaction driver_queue[$];
    int mismatch_count = 0;
    int match_count = 0;

    // Expected data storage using transaction_id as key
    bit [511:0] expected_data[bit [31:0]];
    bit [511:0] expected_mask[bit [31:0]];

    // Track transaction counts for debugging
    int driver_tx_count = 0;
    int monitor_tx_count = 0;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // write_driver: called when a transaction arrives from the driver
    function void write_driver(hbm_transaction tr);
        `uvm_info("SB_DRIVER", $sformatf("Received from driver: %s", tr.convert2string()), UVM_HIGH)
        driver_queue.push_back(tr);
        driver_tx_count++;

        // Store expected write data using transaction_id as key
        if (tr.cmd == hbm_transaction::WRITE) begin
            expected_data[tr.transaction_id] = tr.wdata;
            expected_mask[tr.transaction_id] = tr.wdata_mask;
        end
    endfunction

    // write_monitor: called when a transaction is observed on the interface
    function void write_monitor(hbm_transaction tr);
        hbm_transaction expected;
        `uvm_info("SB_MONITOR", $sformatf("Received from monitor: %s", tr.convert2string()), UVM_HIGH)
        monitor_tx_count++;

        if (driver_queue.size() == 0) begin
            `uvm_error(get_name(), "Unexpected transaction from monitor")
            mismatch_count++;
            return;
        end
        expected = driver_queue.pop_front();

        // Check command and address match
        if (tr.cmd != expected.cmd ||
            tr.addr_bank != expected.addr_bank ||
            tr.addr_row != expected.addr_row ||
            tr.addr_col != expected.addr_col) begin
            `uvm_error(get_name(), $sformatf("Mismatch: got %s, expected %s",
                                             tr.convert2string(), expected.convert2string()))
            mismatch_count++;
        end else begin
            // Check data for read operations
            if (tr.cmd == hbm_transaction::READ && tr.rdata_valid) begin
                `uvm_info(get_name(), $sformatf("Read data valid: %h", tr.rdata), UVM_HIGH)
            end
            // Verify write data was captured correctly
            if (tr.cmd == hbm_transaction::WRITE && expected_data.exists(expected.transaction_id)) begin
                `uvm_info(get_name(), $sformatf("Write completed: id=%0d, expected_data=%h",
                                                expected.transaction_id, expected_data[expected.transaction_id]), UVM_HIGH)
            end
            `uvm_info(get_name(), $sformatf("Match: %s", tr.convert2string()), UVM_HIGH)
            match_count++;
        end

        // Remove from expected data using transaction_id
        if (expected_data.exists(expected.transaction_id))
            expected_data.delete(expected.transaction_id);
        if (expected_mask.exists(expected.transaction_id))
            expected_mask.delete(expected.transaction_id);
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        `uvm_info(get_name(), $sformatf("Scoreboard Results: %0d matches, %0d mismatches",
                                        match_count, mismatch_count), UVM_MEDIUM)
        if (mismatch_count == 0)
            `uvm_info(get_name(), "SCOREBOARD PASSED", UVM_MEDIUM)
        else
            `uvm_error(get_name(), $sformatf("SCOREBOARD FAILED: %0d mismatches", mismatch_count))
    endfunction
endclass

// ------------------------------------------------------------
// HBM Register Model (RAL) - Simplified
// ------------------------------------------------------------
class hbm_reg_model extends uvm_object;
    `uvm_object_utils(hbm_reg_model)

    // Control register fields
    bit [31:0] control;
    bit [31:0] status;
    bit [31:0] timing0;
    bit [31:0] timing1;
    bit [31:0] interrupt_enable;

    function new(string name = "hbm_reg_model");
        super.new(name);
    endfunction

    // Write to control register
    function void write_control(bit [31:0] value);
        control = value;
        `uvm_info(get_name(), $sformatf("Control write: 0x%08x", value), UVM_HIGH)
    endfunction

    function bit [31:0] read_control();
        return control;
    endfunction

    // Write to timing0 register (tRCD, tRP, tRAS)
    function void write_timing0(bit [31:0] value);
        timing0 = value;
        `uvm_info(get_name(), $sformatf("Timing0 write: 0x%08x (tRCD=%d, tRP=%d, tRAS=%d)",
                                        value, value[7:0], value[15:8], value[23:16]), UVM_HIGH)
    endfunction

    function bit [31:0] read_timing0();
        return timing0;
    endfunction

    // Write to timing1 register (tRC, tRRD, tCCD)
    function void write_timing1(bit [31:0] value);
        timing1 = value;
        `uvm_info(get_name(), $sformatf("Timing1 write: 0x%08x (tRC=%d, tRRD=%d, tCCD=%d)",
                                        value, value[7:0], value[15:8], value[23:16]), UVM_HIGH)
    endfunction

    function bit [31:0] read_timing1();
        return timing1;
    endfunction

    function void print();
        `uvm_info(get_name(), "Register Model Contents:", UVM_MEDIUM)
        $display("  control:          0x%08x", control);
        $display("  status:           0x%08x", status);
        $display("  timing0:          0x%08x", timing0);
        $display("  timing1:          0x%08x", timing1);
        $display("  interrupt_enable: 0x%08x", interrupt_enable);
    endfunction
endclass

// ------------------------------------------------------------
// Environment
// ------------------------------------------------------------
class hbm_env extends uvm_env;
    `uvm_component_utils(hbm_env)

    hbm_agent       hbm_agent_inst;
    axi4_agent      axi4_agent_inst;
    hbm_scoreboard  scoreboard;
    hbm_agent_config hbm_cfg;
    axi4_agent_config axi4_cfg;

    // Register model
    hbm_reg_model regmodel;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Create configurations
        hbm_cfg = hbm_agent_config::type_id::create("hbm_cfg");
        axi4_cfg = axi4_agent_config::type_id::create("axi4_cfg");

        // Set config DB
        uvm_config_db #(hbm_agent_config)::set(this, "hbm_agent_inst", "cfg", hbm_cfg);
        uvm_config_db #(axi4_agent_config)::set(this, "axi4_agent_inst", "cfg", axi4_cfg);

        // Create components
        hbm_agent_inst = hbm_agent::type_id::create("hbm_agent_inst", this);
        axi4_agent_inst = axi4_agent::type_id::create("axi4_agent_inst", this);
        scoreboard = hbm_scoreboard::type_id::create("scoreboard", this);

        // Create register model
        regmodel = hbm_reg_model::type_id::create("regmodel");
        regmodel.control = 32'h0007;  // reset, enable, start
        regmodel.timing0 = 32'h141828;  // tRCD=20, tRP=20, tRAS=40
        regmodel.timing1 = 32'h3C1414;  // tRC=60, tRRD=20, tCCD=20

        // Set register model in config DB
        uvm_config_db #(hbm_reg_model)::set(this, "*", "regmodel", regmodel);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // Connect monitor transactions to scoreboard
        hbm_agent_inst.monitor.ap.connect(scoreboard);
    endfunction

    function void end_of_elaboration_phase(uvm_phase phase);
        super.end_of_elaboration_phase(phase);
        `uvm_info(get_name(), "End of elaboration", UVM_MEDIUM)
        if (regmodel != null) begin
            regmodel.print();
        end
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        `uvm_info(get_name(), "Environment report phase", UVM_MEDIUM)
    endfunction
endclass

endpackage : hbm_env_pkg
