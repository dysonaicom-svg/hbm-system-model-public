// ------------------------------------------------------------
// hbm_env_pkg.sv - HBM UVM Environment Package
// ------------------------------------------------------------
package hbm_env_pkg;

import uvm_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Interface with Clocking Block
// ------------------------------------------------------------
interface hbm_if (
    input logic clk,
    input logic rst_n
);
    // Command interface
    logic [1:0]  cmd;
    logic [7:0]  addr_bank;
    logic [15:0] addr_row;
    logic [1:0]  addr_col;
    logic [511:0] wdata;
    logic [511:0] wdata_mask;
    logic [511:0] rdata;
    logic        rdata_valid;
    logic        cmd_ready;

    // Clocking blocks for driver (input skew) and monitor (output skew)
    clocking drv_ck @(posedge clk);
        default input #1step output #0;
        input  rst_n;
        input  cmd_ready;
        input  rdata_valid;
        input  rdata;
        output cmd;
        output addr_bank;
        output addr_row;
        output addr_col;
        output wdata;
        output wdata_mask;
    endclocking

    clocking mon_ck @(posedge clk);
        default input #1step output #0;
        input rst_n;
        input cmd;
        input addr_bank;
        input addr_row;
        input addr_col;
        input wdata;
        input wdata_mask;
        input rdata;
        input rdata_valid;
        input cmd_ready;
    endclocking

    modport drv_mp (clocking drv_ck);
    modport mon_mp (clocking mon_ck);
endinterface

// ------------------------------------------------------------
// Agent Configuration Class
// ------------------------------------------------------------
class hbm_agent_config extends uvm_object;
    `uvm_object_utils(hbm_agent_config)

    bit is_active = 1;
    bit has_checks = 1;
    bit has_coverage = 1;

    function new(string name = "hbm_agent_config");
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
    rand bit [7:0]     addr_bank;
    rand bit [15:0]   addr_row;
    rand bit [1:0]    addr_col;
    rand bit [511:0]  wdata;
    rand bit [511:0]  wdata_mask;
    bit    [511:0]    rdata;
    bit               rdata_valid;

    function new(string name = "hbm_transaction");
        super.new(name);
    endfunction

    function void do_copy(uvm_object rhs);
        hbm_transaction tr;
        super.do_copy(rhs);
        $cast(tr, rhs);
        cmd         = tr.cmd;
        addr_bank   = tr.addr_bank;
        addr_row    = tr.addr_row;
        addr_col    = tr.addr_col;
        wdata       = tr.wdata;
        wdata_mask  = tr.wdata_mask;
        rdata       = tr.rdata;
        rdata_valid = tr.rdata_valid;
    endfunction

    function string convert2string();
        string s;
        s = $sformatf("cmd=%s bank=%h row=%h col=%h",
                      cmd.name(), addr_bank, addr_row, addr_col);
        if (cmd == WRITE)
            s = {s, $sformatf(" wdata=%h mask=%h", wdata, wdata_mask)};
        else
            s = {s, $sformatf(" rdata=%h valid=%b", rdata, rdata_valid)};
        return s;
    endfunction

    function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        hbm_transaction tr;
        do_compare = ($cast(tr, rhs) && cmd == tr.cmd &&
                      addr_bank == tr.addr_bank && addr_row == tr.addr_row &&
                      addr_col == tr.addr_col);
    endfunction
endclass

// ------------------------------------------------------------
// Driver
// ------------------------------------------------------------
class hbm_driver extends uvm_driver #(hbm_transaction);
    `uvm_component_utils(hbm_driver)

    virtual hbm_if.drv_mp vif;
    hbm_agent_config cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(virtual hbm_if.drv_mp)::get(this, "", "vif", vif))
            `uvm_fatal("NOVIF", "Virtual interface not set")
        if (!uvm_config_db #(hbm_agent_config)::get(this, "", "cfg", cfg))
            `uvm_info("NOCFG", "No agent config, using default", UVM_MEDIUM)
    endfunction

    task run_phase(uvm_phase phase);
        reset_dut();
        forever begin
            seq_item_port.get_next_item(req);
            drive_transaction(req);
            seq_item_port.item_done();
        end
    endtask

    task reset_dut();
        vif.drv_ck.cmd <= 2'b0;
        vif.drv_ck.addr_bank  <= '0;
        vif.drv_ck.addr_row    <= '0;
        vif.drv_ck.addr_col    <= '0;
        vif.drv_ck.wdata      <= '0;
        vif.drv_ck.wdata_mask <= '0;
        @(vif.drv_ck);
        if (!vif.drv_ck.rst_n) begin
            wait (vif.drv_ck.rst_n);
        end
    endtask

    task drive_transaction(hbm_transaction tr);
        // Wait for ready
        @(vif.drv_ck);
        while (!vif.drv_ck.cmd_ready) @(vif.drv_ck);

        @(vif.drv_ck);
        if (tr.cmd == hbm_transaction::WRITE) begin
            vif.drv_ck.cmd        <= 2'd1;
            vif.drv_ck.addr_bank  <= tr.addr_bank;
            vif.drv_ck.addr_row   <= tr.addr_row;
            vif.drv_ck.addr_col   <= tr.addr_col;
            vif.drv_ck.wdata      <= tr.wdata;
            vif.drv_ck.wdata_mask <= tr.wdata_mask;
        end else begin
            vif.drv_ck.cmd        <= 2'd2;
            vif.drv_ck.addr_bank  <= tr.addr_bank;
            vif.drv_ck.addr_row   <= tr.addr_row;
            vif.drv_ck.addr_col   <= tr.addr_col;
        end

        @(vif.drv_ck);
        vif.drv_ck.cmd <= 2'b0;
    endtask
endclass

// ------------------------------------------------------------
// Monitor
// ------------------------------------------------------------
class hbm_monitor extends uvm_monitor;
    `uvm_component_utils(hbm_monitor)

    virtual hbm_if.mon_mp vif;
    uvm_analysis_port #(hbm_transaction) ap;
    hbm_agent_config cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(virtual hbm_if.mon_mp)::get(this, "", "vif", vif))
            `uvm_fatal("NOVIF", "Virtual interface not set")
    endfunction

    task run_phase(uvm_phase phase);
        hbm_transaction tr;
        forever begin
            @(vif.mon_ck);
            if (vif.mon_ck.rst_n && vif.mon_ck.cmd != 2'b0) begin
                tr = hbm_transaction::type_id::create("tr");
                tr.addr_bank = vif.mon_ck.addr_bank;
                tr.addr_row  = vif.mon_ck.addr_row;
                tr.addr_col  = vif.mon_ck.addr_col;
                tr.wdata     = vif.mon_ck.wdata;
                tr.wdata_mask = vif.mon_ck.wdata_mask;

                if (vif.mon_ck.cmd == 2'd1)
                    tr.cmd = hbm_transaction::WRITE;
                else if (vif.mon_ck.cmd == 2'd2)
                    tr.cmd = hbm_transaction::READ;

                `uvm_info(get_name(), $sformatf("Monitored: %s", tr.convert2string()), UVM_HIGH)
                ap.write(tr);
            end
        end
    endtask
endclass

// ------------------------------------------------------------
// Sequencer
// ------------------------------------------------------------
class hbm_sequencer extends uvm_sequencer #(hbm_transaction);
    `uvm_component_utils(hbm_sequencer)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass

// ------------------------------------------------------------
// Agent
// ------------------------------------------------------------
class hbm_agent extends uvm_agent;
    `uvm_component_utils(hbm_agent)

    hbm_driver    driver;
    hbm_monitor   monitor;
    hbm_sequencer sequencer;
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
// Scoreboard
// ------------------------------------------------------------
class hbm_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(hbm_scoreboard)

    uvm_analysis_export #(hbm_transaction) from_driver;
    uvm_analysis_export #(hbm_transaction) from_monitor;
    hbm_transaction driver_queue[$];
    int mismatch_count = 0;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        from_driver = new("from_driver", this);
        from_monitor = new("from_monitor", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        from_driver.connect(this._ovm_export_pool.get("driver"));
        from_monitor.connect(this._ovm_export_pool.get("monitor"));
    endfunction

    function void write_driver(hbm_transaction tr);
        driver_queue.push_back(tr);
    endfunction

    function void write_monitor(hbm_transaction tr);
        hbm_transaction expected;
        if (driver_queue.size() == 0) begin
            `uvm_error(get_name(), "Unexpected transaction from monitor")
            return;
        end
        expected = driver_queue.pop_front();

        if (tr.cmd != expected.cmd ||
            tr.addr_bank != expected.addr_bank ||
            tr.addr_row != expected.addr_row ||
            tr.addr_col != expected.addr_col) begin
            `uvm_error(get_name(), $sformatf("Mismatch: got %s, expected %s",
                                             tr.convert2string(), expected.convert2string()))
            mismatch_count++;
        end else begin
            `uvm_info(get_name(), $sformatf("Match: %s", tr.convert2string()), UVM_HIGH)
        end
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        if (mismatch_count == 0)
            `uvm_info(get_name(), "SCOREBOARD PASSED", UVM_MEDIUM)
        else
            `uvm_error(get_name(), $sformatf("SCOREBOARD FAILED: %0d mismatches", mismatch_count))
    endfunction
endclass

// ------------------------------------------------------------
// Environment
// ------------------------------------------------------------
class hbm_env extends uvm_env;
    `uvm_component_utils(hbm_env)

    hbm_agent       agent;
    hbm_scoreboard  scoreboard;
    hbm_agent_config cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        cfg = hbm_agent_config::type_id::create("cfg");
        agent = hbm_agent::type_id::create("agent", this);
        scoreboard = hbm_scoreboard::type_id::create("scoreboard", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        agent.monitor.ap.connect(scoreboard.from_monitor);
    endfunction
endclass

endpackage : hbm_env_pkg