`timescale 1ps / 1fs

//------------------------------------------------------------------------------
// HBM4 VIP Package
//
// UVM Verification IP for HBM4 Logic Base Die validation
// Supports 32-channel independent operation, PAM3 signaling, DFI 5.0
//------------------------------------------------------------------------------

package hbm4_vip_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    //============================================================
    // Constants
    //============================================================
    localparam NUM_CHANNELS = 32;
    localparam CHANNEL_WIDTH = 64;
    localparam BURST_WIDTH = 256;
    localparam PAM3_ENABLED = 1;

    // Transaction types
    typedef enum {
        HBM4_ACT,
        HBM4_PRE,
        HBM4_RD,
        HBM4_WR,
        HBM4_REF,
        HBM4_MRS,
        HBM4_TRAIN
    } hbm4_cmd_e;

    // Channel states
    typedef enum {
        CH_IDLE,
        CH_ACTIVE,
        CH_TRAINING,
        CH_ERROR
    } channel_state_e;

    //============================================================
    // Configuration
    //============================================================
    class hbm4_vip_config extends uvm_object;
        `uvm_object_utils(hbm4_vip_config)

        int num_channels;
        int channel_width;
        int burst_width;
        bit pam3_enabled;
        bit ecc_enabled;
        bit crc_enabled;

        function new(string name = "hbm4_vip_config");
            super.new(name);
            num_channels = NUM_CHANNELS;
            channel_width = CHANNEL_WIDTH;
            burst_width = BURST_WIDTH;
            pam3_enabled = PAM3_ENABLED;
            ecc_enabled = 1;
            crc_enabled = 1;
        endfunction
    endclass

    //============================================================
    // Transaction
    //============================================================
    class hbm4_transaction extends uvm_sequence_item;
        `uvm_object_utils(hbm4_transaction)

        rand int channel_id;
        rand hbm4_cmd_e cmd;
        rand bit [47:0] address;
        rand bit [255:0] data;
        rand int data_width;

        bit [255:0] read_data;
        bit error;
        string error_msg;

        constraint valid_channel {
            channel_id >= 0;
            channel_id < NUM_CHANNELS;
        }

        constraint valid_cmd {
            cmd inside {HBM4_ACT, HBM4_PRE, HBM4_RD, HBM4_WR, HBM4_REF, HBM4_MRS};
        }

        function new(string name = "hbm4_transaction");
            super.new(name);
        endfunction

        function string convert2string();
            return $sformatf(
                "HBM4 Transaction: ch=%0d cmd=%s addr=0x%h",
                channel_id, cmd.name(), address
            );
        endfunction
    endclass

    //============================================================
    // PAM3 Signal Transaction
    //============================================================
    class pam3_symbol extends uvm_sequence_item;
        `uvm_object_utils(pam3_symbol)

        rand int level;  // -1, 0, +1
        rand bit [7:0] ui_position;
        rand bit [15:0] amplitude;  // Fixed point

        constraint valid_level {
            level >= -1;
            level <= 1;
        }

        function new(string name = "pam3_symbol");
            super.new(name);
        endfunction
    endclass

    //============================================================
    // Driver Interface
    //============================================================
    class hbm4_driver_if extends uvm_seq_item_pull_port #(hbm4_transaction);
        `uvm_component_utils(hbm4_driver_if)

        function new(string name, uvm_component parent);
            super.new(name, parent, UVM_PULL);
        endfunction
    endclass

    //============================================================
    // Monitor Interface
    //============================================================
    class hbm4_monitor_if extends uvm_analysis_port #(hbm4_transaction);
        `uvm_component_utils(hbm4_monitor_if)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass

    //============================================================
    // Sequence: Independent Channel Test
    //============================================================
    class hbm4_independent_channel_seq extends uvm_sequence #(hbm4_transaction);
        `uvm_object_utils(hbm4_independent_channel_seq)

        int num_transactions;

        function new(string name = "hbm4_independent_channel_seq");
            super.new(name);
            num_transactions = 1000;
        endfunction

        task body();
            for (int i = 0; i < num_transactions; i++) begin
                hbm4_transaction tx;
                `uvm_do_with(tx, {
                    channel_id == (i % 32);
                    cmd == HBM4_RD;
                })
            end
        endtask
    endclass

    //============================================================
    // Sequence: PAM3 Training Test
    //============================================================
    class hbm4_pam3_training_seq extends uvm_sequence #(hbm4_transaction);
        `uvm_object_utils(hbm4_pam3_training_seq)

        function new(string name = "hbm4_pam3_training_seq");
            super.new(name);
        endfunction

        task body();
            // Issue training commands to all channels
            for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                hbm4_transaction tx;
                `uvm_do_with(tx, {
                    channel_id == ch;
                    cmd == HBM4_TRAIN;
                })
                #100ns;
            end
        endtask
    endclass

    //============================================================
    // Driver
    //============================================================
    class hbm4_driver extends uvm_driver #(hbm4_transaction);
        `uvm_component_utils(hbm4_driver)

        hbm4_vip_config cfg;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db #(hbm4_vip_config)::get(this, "", "cfg", cfg))
                `uvm_fatal("NO_CFG", "hbm4_vip_config not set")
        endfunction

        task run_phase(uvm_phase phase);
            forever begin
                seq_item_port.get_next_item(req);
                drive_transaction(req);
                seq_item_port.item_done();
            end
        endtask

        virtual protected task drive_transaction(hbm4_transaction tx);
            // Simulate command drive
            case (tx.cmd)
                HBM4_ACT: drive_activate(tx);
                HBM4_PRE: drive_precharge(tx);
                HBM4_RD:  drive_read(tx);
                HBM4_WR:  drive_write(tx);
                HBM4_REF: drive_refresh(tx);
                HBM4_TRAIN: drive_training(tx);
            endcase
        endtask

        virtual protected task drive_activate(hbm4_transaction tx);
            `uvm_info("HBM4_DRV", $sformatf("ACT ch=%0d addr=0x%h", tx.channel_id, tx.address), UVM_HIGH)
        endtask

        virtual protected task drive_precharge(hbm4_transaction tx);
            `uvm_info("HBM4_DRV", $sformatf("PRE ch=%0d", tx.channel_id), UVM_HIGH)
        endtask

        virtual protected task drive_read(hbm4_transaction tx);
            `uvm_info("HBM4_DRV", $sformatf("RD ch=%0d addr=0x%h", tx.channel_id, tx.address), UVM_HIGH)
        endtask

        virtual protected task drive_write(hbm4_transaction tx);
            `uvm_info("HBM4_DRV", $sformatf("WR ch=%0d addr=0x%h data=0x%h", tx.channel_id, tx.address, tx.data), UVM_HIGH)
        endtask

        virtual protected task drive_refresh(hbm4_transaction tx);
            `uvm_info("HBM4_DRV", $sformatf("REF ch=%0d", tx.channel_id), UVM_HIGH)
        endtask

        virtual protected task drive_training(hbm4_transaction tx);
            `uvm_info("HBM4_DRV", $sformatf("TRAIN ch=%0d", tx.channel_id), UVM_HIGH)
            // Training takes time
            #500ns;
        endtask
    endclass

    //============================================================
    // Monitor
    //============================================================
    class hbm4_monitor extends uvm_monitor;
        `uvm_component_utils(hbm4_monitor)

        uvm_analysis_port #(hbm4_transaction) ap;
        hbm4_vip_config cfg;
        virtual interface hbm4_vip_if vif;

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db #(hbm4_vip_config)::get(this, "", "cfg", cfg))
                `uvm_fatal("NO_CFG", "hbm4_vip_config not set")
            if (!uvm_config_db #(virtual interface hbm4_vip_if)::get(this, "", "vif", vif))
                `uvm_fatal("NO_VIF", "hbm4_vip_if not set")
        endfunction

        task run_phase(uvm_phase phase);
            forever begin
                @(posedge vif.clk);
                // Monitor transactions on all channels
                for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                    if (vif.cmd_valid[ch]) begin
                        sample_transaction(ch);
                    end
                end
            end
        endtask

        virtual protected task sample_transaction(int ch);
            hbm4_transaction tx;
            tx = new("tx");
            tx.channel_id = ch;
            tx.address = vif.address[ch];
            case (vif.cmd_type[ch])
                3'd0: tx.cmd = HBM4_ACT;
                3'd1: tx.cmd = HBM4_PRE;
                3'd2: tx.cmd = HBM4_RD;
                3'd3: tx.cmd = HBM4_WR;
                3'd4: tx.cmd = HBM4_REF;
                default: tx.cmd = HBM4_MRS;
            endcase
            ap.write(tx);
        endtask
    endclass

    //============================================================
    // Agent
    //============================================================
    class hbm4_agent extends uvm_agent;
        `uvm_component_utils(hbm4_agent)

        hbm4_driver driver;
        hbm4_monitor monitor;
        uvm_sequencer #(hbm4_transaction) sequencer;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            monitor = hbm4_monitornew("monitor", this);
            driver = hbm4_drivernew("driver", this);
            sequencer = uvm_sequencer #(hbm4_transaction)new("sequencer", this);
        endfunction

        function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            driver.seq_item_port.connect(sequencer.seq_item_export);
        endfunction
    endclass

    //============================================================
    // Scoreboard
    //============================================================
    class hbm4_scoreboard extends uvm_scoreboard;
        `uvm_component_utils(hbm4_scoreboard)

        uvm_analysis_export #(hbm4_transaction) expected_export;
        uvm_analysis_export #(hbm4_transaction) actual_export;

        // Queues to store expected vs actual
        hbm4_transaction expected_q[$];
        hbm4_transaction actual_q[$];

        int mismatch_count;
        int total_transactions;

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expected_export = new("expected_export", this);
            actual_export = new("actual_export", this);
            mismatch_count = 0;
            total_transactions = 0;
        endfunction

        function void write_expected(hbm4_transaction tx);
            expected_q.push_back(tx);
            total_transactions++;
        endfunction

        function void write_actual(hbm4_transaction tx);
            actual_q.push_back(tx);
            check_transaction(tx);
        endfunction

        virtual function void check_transaction(hbm4_transaction tx);
            // Simplified check - real scoreboard would match expected/actual
            if (tx.error) begin
                mismatch_count++;
                `uvm_error("SBD", $sformatf("Transaction error: %s", tx.error_msg))
            end
        endfunction

        function void report_phase(uvm_phase phase);
            super.report_phase(phase);
            `uvm_info("SBD_REPORT",
                $sformatf("Total: %0d, Mismatches: %0d, Pass rate: %0d%%",
                    total_transactions, mismatch_count,
                    total_transactions > 0 ?
                    (100 * (total_transactions - mismatch_count) / total_transactions) : 100),
                UVM_MEDIUM)
        endfunction
    endclass

    //============================================================
    // Coverage Model
    //============================================================
    class hbm4_coverage extends uvm_subscriber #(hbm4_transaction);
        `uvm_component_utils(hbm4_coverage)

        covergroup channel_cg;
            option.per_instance = 1;
            channel: coverpoint tr.channel_id {
                bins ch[] = {[0:31]};
            }
            cmd: coverpoint tr.cmd {
                bins cmds[] = {HBM4_ACT, HBM4_PRE, HBM4_RD, HBM4_WR, HBM4_REF, HBM4_MRS};
            }
            cross_cmd_channel: cross channel, cmd;
        endgroup

        function new(string name, uvm_component parent);
            super.new(name, parent);
            channel_cg = new();
        endfunction

        function void write(hbm4_transaction t);
            tr = t;
            channel_cg.sample();
        endfunction

        hbm4_transaction tr;
    endclass

    //============================================================
    // Environment
    //============================================================
    class hbm4_env extends uvm_env;
        `uvm_component_utils(hbm4_env)

        hbm4_vip_config cfg;
        hbm4_agent agent;
        hbm4_scoreboard scoreboard;
        hbm4_coverage coverage;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function void build_phase(uvm_phase phase);
            super.build_phase(phase);

            cfg = hbm4_vip_confignew("cfg");
            uvm_config_db #(hbm4_vip_config)::set(this, "*", "cfg", cfg);

            agent = hbm4_agentnew("agent", this);
            scoreboard = hbm4_scoreboardnew("scoreboard", this);
            coverage = hbm4_coveragenew("coverage", this);
        endfunction

        function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.monitor.ap.connect(coverage.analysis_export);
        endfunction
    endclass

    //============================================================
    // Test: Independent Channel Test
    //============================================================
    class hbm4_independent_channel_test extends uvm_test;
        `uvm_component_utils(hbm4_independent_channel_test)

        hbm4_env env;

        function new(string name, uvm_test);
            super.new(name);
        endfunction

        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            env = hbm4_envnew("env", this);
        endfunction

        task run_phase(uvm_phase phase);
            hbm4_independent_channel_seq seq;
            phase.raise_objection(this);
            seq = hbm4_independent_channelnew("seq");
            fork
                seq.start(env.agent.sequencer);
            join_none
            #10us;
            phase.drop_objection(this);
        endtask
    endclass

    //============================================================
    // Test: PAM3 Training Test
    //============================================================
    class hbm4_pam3_training_test extends uvm_test;
        `uvm_component_utils(hbm4_pam3_training_test)

        hbm4_env env;

        function new(string name, uvm_test);
            super.new(name);
        endfunction

        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            env = hbm4_envnew("env", this);
        endfunction

        task run_phase(uvm_phase phase);
            hbm4_pam3_training_seq seq;
            phase.raise_objection(this);
            seq = hbm4_pam3_trainingnew("seq");
            seq.start(env.agent.sequencer);
            #50us;
            phase.drop_objection(this);
        endtask
    endclass

endpackage