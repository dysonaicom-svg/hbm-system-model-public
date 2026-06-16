// ------------------------------------------------------------
// test_multi_channel_seq.sv - Multi-Channel Interleaving Test
// Tests HBM4 controller with 32-channel interleaving
// ------------------------------------------------------------
package hbm_multi_channel_pkg;

import uvm_pkg::*;
import hbm_env_pkg::*;
import hbm_test_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Multi-Channel Transaction
// ------------------------------------------------------------
class hbm_multi_channel_transaction extends hbm_transaction;
    `uvm_object_utils(hbm_multi_channel_transaction)

    rand bit [4:0] channel;  // HBM4 supports 32 channels
    bit [2:0]     channel_priority;

    constraint valid_channel {
        channel < 32;  // HBM4: 32 channels
    }

    function new(string name = "hbm_multi_channel_transaction");
        super.new(name);
    endfunction

    function string convert2string();
        return {
            super.convert2string(),
            $sformatf(" channel=%0d priority=%b", channel, channel_priority)
        };
    endfunction
endclass

// ------------------------------------------------------------
// Base Multi-Channel Sequence
// ------------------------------------------------------------
class hbm_multi_channel_base_sequence extends hbm_base_sequence;
    `uvm_object_utils(hbm_multi_channel_base_sequence)

    int num_channels = 32;  // HBM4 default
    int requests_per_channel = 10;

    function new(string name = "hbm_multi_channel_base_sequence");
        super.new(name);
    endfunction

    function void set_num_channels(int num);
        num_channels = num;
    endfunction
endclass

// ------------------------------------------------------------
// Multi-Channel Interleaving Sequence
// Tests interleaved access across multiple channels
// ------------------------------------------------------------
class multi_channel_interleave_seq extends hbm_multi_channel_base_sequence;
    `uvm_object_utils(multi_channel_interleave_seq)

    int interleave_mode = 0;  // 0=round-robin, 1=priority, 2=random

    function new(string name = "multi_channel_interleave_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int request_id = 0;
        int channel_requests[32];
        int channel_conflicts[32];

        // Initialize counters
        for (int i = 0; i < 32; i++) begin
            channel_requests[i] = 0;
            channel_conflicts[i] = 0;
        end

        `uvm_info(get_name(), "Starting multi-channel interleaving test", UVM_MEDIUM)

        case (interleave_mode)
            0: begin // Round-robin interleaving
                `uvm_info(get_name(), "Mode: Round-robin interleaving", UVM_MEDIUM)

                for (int round = 0; round < requests_per_channel; round++) begin
                    for (int ch = 0; ch < num_channels; ch++) begin
                        req = new("req");
                        start_item(req);

                        if (!req.randomize() with {
                            addr_bank == ch;
                            addr_row  == round;
                        }) begin
                            `uvm_error(get_name(), "Round-robin randomization failed")
                        end
                        req.transaction_id = get_next_id();
                        req.channel = ch;
                        req.channel_priority = 0;

                        channel_requests[ch]++;
                        request_id++;

                        `uvm_info(get_name(), $sformatf(
                            "Round-robin: ch=%0d req=%0d bank=%h row=%h",
                            ch, request_id, req.addr_bank, req.addr_row), UVM_DEBUG)
                        finish_item(req);
                        #5;
                    end
                end
            end

            1: begin // Priority-based interleaving
                `uvm_info(get_name(), "Mode: Priority-based interleaving", UVM_MEDIUM)

                // High priority channels first
                for (int ch = 0; ch < 8; ch++) begin  // Top 8 channels get high priority
                    for (int i = 0; i < 5; i++) begin
                        req = new("req");
                        start_item(req);

                        if (!req.randomize() with {
                            addr_bank == ch;
                        }) begin
                            `uvm_error(get_name(), "Priority randomization failed")
                        end
                        req.transaction_id = get_next_id();
                        req.channel = ch;
                        req.channel_priority = 3'b000;  // High priority

                        channel_requests[ch]++;
                        request_id++;

                        `uvm_info(get_name(), $sformatf(
                            "Priority: ch=%0d req=%0d prio=high", ch, request_id), UVM_DEBUG)
                        finish_item(req);
                        #5;
                    end
                end

                // Low priority channels
                for (int ch = 8; ch < num_channels; ch++) begin
                    for (int i = 0; i < 5; i++) begin
                        req = new("req");
                        start_item(req);

                        if (!req.randomize() with {
                            addr_bank == ch;
                        }) begin
                            `uvm_error(get_name(), "Low priority randomization failed")
                        end
                        req.transaction_id = get_next_id();
                        req.channel = ch;
                        req.channel_priority = 3'b111;  // Low priority

                        channel_requests[ch]++;
                        request_id++;

                        finish_item(req);
                        #5;
                    end
                end
            end

            2: begin // Random channel interleaving
                `uvm_info(get_name(), "Mode: Random channel interleaving", UVM_MEDIUM)

                for (int i = 0; i < (num_channels * requests_per_channel); i++) begin
                    req = new("req");
                    start_item(req);

                    if (!req.randomize()) begin
                        `uvm_error(get_name(), "Random channel randomization failed")
                    end
                    req.transaction_id = get_next_id();
                    req.channel = i % num_channels;
                    req.channel_priority = $urandom() % 8;

                    channel_requests[req.channel % 32]++;
                    request_id++;

                    `uvm_info(get_name(), $sformatf(
                        "Random: req=%0d ch=%0d", request_id, req.channel), UVM_DEBUG)
                    finish_item(req);
                    #5;
                end
            end
        endcase

        // Print statistics
        `uvm_info(get_name(), "=== Multi-Channel Statistics ===", UVM_MEDIUM)
        for (int ch = 0; ch < num_channels; ch++) begin
            if (channel_requests[ch] > 0) begin
                `uvm_info(get_name(), $sformatf(
                    "Channel %0d: %0d requests", ch, channel_requests[ch]), UVM_HIGH)
            end
        end
        `uvm_info(get_name(), $sformatf(
            "Total requests: %0d", request_id), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Channel Conflict Sequence
// Tests for conflicts when multiple channels access same bank
// ------------------------------------------------------------
class channel_conflict_seq extends hbm_multi_channel_base_sequence;
    `uvm_object_utils(channel_conflict_seq)

    int target_bank = 0;
    int channels_per_bank = 4;

    function new(string name = "channel_conflict_seq");
        super.new(name);
    endfunction

    task body();
        hbm_transaction req;
        int conflict_count = 0;
        int total_requests = 0;

        `uvm_info(get_name(), "Starting channel conflict test", UVM_MEDIUM)

        // Each channel targets the same bank (worst case)
        for (int ch = 0; ch < num_channels; ch++) begin
            for (int i = 0; i < 10; i++) begin
                req = new("req");
                start_item(req);

                if (!req.randomize() with {
                    addr_bank == target_bank;
                    addr_row  == i;
                }) begin
                    `uvm_error(get_name(), "Conflict randomization failed")
                end
                req.transaction_id = get_next_id();
                req.channel = ch;

                total_requests++;

                // Check for simulated conflicts
                if (i > 0 && ($urandom() % 100 < 20)) begin  // 20% conflict rate
                    conflict_count++;
                    `uvm_warning(get_name(), $sformatf(
                        "Channel %0d conflict at request %0d", ch, i))
                end

                `uvm_info(get_name(), $sformatf(
                    "Conflict: ch=%0d req=%0d bank=%h row=%h",
                    ch, total_requests, req.addr_bank, req.addr_row), UVM_DEBUG)
                finish_item(req);
                #5;
            end
        end

        `uvm_info(get_name(), $sformatf(
            "Channel conflict test: total=%0d conflicts=%0d",
            total_requests, conflict_count), UVM_MEDIUM)
    endtask
endclass

// ------------------------------------------------------------
// Multi-Channel Interleaving Test
// ------------------------------------------------------------
class hbm_multi_channel_interleave_test extends hbm_base_test;
    `uvm_component_utils(hbm_multi_channel_interleave_test)

    function new(string name = "hbm_multi_channel_interleave_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        multi_channel_interleave_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = new();
        seq.num_channels = 32;
        seq.requests_per_channel = 5;
        seq.interleave_mode = 0;  // Round-robin
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

// ------------------------------------------------------------
// Channel Conflict Test
// ------------------------------------------------------------
class hbm_channel_conflict_test extends hbm_base_test;
    `uvm_component_utils(hbm_channel_conflict_test)

    function new(string name = "hbm_channel_conflict_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        channel_conflict_seq seq;
        super.run_phase(phase);
        phase.raise_objection(this);

        seq = new();
        seq.num_channels = 32;
        seq.target_bank = 0;
        seq.set_regmodel(env.regmodel);
        seq.start(env.hbm_agent_inst.sequencer);

        phase.drop_objection(this);
    endtask
endclass

endpackage : hbm_multi_channel_pkg