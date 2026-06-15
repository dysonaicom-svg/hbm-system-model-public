// ------------------------------------------------------------
// hbm_coverage.sv - HBM Functional Coverage
// Tracks command, bank, row hit/miss coverage
// ------------------------------------------------------------
// Copyright (c) 2026. All rights reserved.

package hbm_coverage_pkg;

import uvm_pkg::*;
`include "uvm_macros.svh"

// ------------------------------------------------------------
// Coverage Monitor
// ------------------------------------------------------------
class hbm_coverage extends uvm_component;
    `uvm_component_utils(hbm_coverage)

    uvm_analysis_imp #(hbm_transaction, hbm_coverage) item_export;

    // Transaction tracking
    hbm_transaction trans_history[$];
    int max_history = 1000;

    // Previous transaction for comparison
    hbm_transaction prev_trans;

    // Covergroups
    covergroup cmd_cg;
        option.per_instance = 1;
        coverpoint cmd {
            bins read = {hbm_transaction::READ};
            bins write = {hbm_transaction::WRITE};
        }
    endgroup

    covergroup bank_cg;
        option.per_instance = 1;
        coverpoint bank {
            bins banks[] = {[0:15]};
            bins low = {[0:3]};
            bins med = {[4:11]};
            bins high = {[12:15]};
        }
    endgroup

    covergroup row_cg;
        option.per_instance = 1;
        coverpoint row_idx {
            bins low = {[0:255]};
            bins med = {[256:16383]};
            bins high = {[16384:65535]};
        }
    endgroup

    covergroup col_cg;
        option.per_instance = 1;
        coverpoint col {
            bins col0 = {[0:0]};
            bins col1 = {[1:1]};
            bins col2 = {[2:2]};
            bins col3 = {[3:3]};
        }
    endgroup

    // Row hit/miss tracking
    bit [15:0] last_row[16];  // Per bank
    bit [7:0] last_bank = 0;
    int row_hits = 0;
    int row_misses = 0;
    int row_conflicts = 0;

    covergroup row_hit_cg;
        option.per_instance = 1;
        coverpoint hit_type {
            bins hit = {1};
            bins miss = {0};
        }
    endgroup

    // Address patterns
    covergroup addr_pattern_cg;
        option.per_instance = 1;
        coverpoint pattern {
            bins sequential = {[0:15]};
            bins random = {[16:31]};
            bins hotspot = {[32:47]};
            bins stride = {[48:63]};
        }
    endgroup

    // Timing coverage
    covergroup timing_cg;
        option.per_instance = 1;
        coverpoint idle_cycles {
            bins idle0 = {0};
            bins idle1_5 = {[1:5]};
            bins idle6_10 = {[6:10]};
            bins idle_gte10 = {[10:]} with (this >= 10);
        }
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        item_export = new("item_export", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        `uvm_info(get_name(), "Coverage build complete", UVM_MEDIUM)
    endfunction

    virtual function void write(hbm_transaction t);
        // Store transaction
        trans_history.push_back(t);
        if (trans_history.size() > max_history) begin
            trans_history.pop_front();
        end

        // Analyze row hit/miss
        if (prev_trans != null) begin
            if (t.addr_bank == prev_trans.addr_bank) begin
                if (t.addr_row == prev_trans.addr_row) begin
                    row_hits++;
                    `uvm_info(get_name(), "ROW HIT", UVM_FULL)
                end else begin
                    row_conflicts++;
                    `uvm_info(get_name(), "ROW CONFLICT", UVM_FULL)
                end
            end else begin
                row_misses++;
            end
        end else begin
            row_misses++;  // First access is always a miss
        end

        // Update history
        prev_trans = t;
        last_bank = t.addr_bank;
        last_row[t.addr_bank] = t.addr_row;

        // Sample covergroups
        cmd_cg.sample();
        bank_cg.sample();
        row_cg.sample();
        col_cg.sample();
        row_hit_cg.sample();

        `uvm_info(get_name(), $sformatf(
            "Coverage: hits=%0d misses=%0d conflicts=%0d",
            row_hits, row_misses, row_conflicts), UVM_FULL)
    endfunction

    function void extract_phase(uvm_phase phase);
        super.extract_phase(phase);
        `uvm_info(get_name(), $sformatf(
            "=== Coverage Summary ===\n" //
            "Row Hits: %0d\n" //
            "Row Misses: %0d\n" //
            "Row Conflicts: %0d\n" //
            "Total Transactions: %0d\n" //
            "Hit Rate: %0.2f%%",
            row_hits, row_misses, row_conflicts,
            trans_history.size(),
            row_hits * 100.0 / (row_hits + row_misses + row_conflicts + 0.001)
        ), UVM_MEDIUM)
    endfunction

    function void report_phase(uvm_phase phase);
        real hit_rate;
        super.report_phase(phase);

        hit_rate = row_hits * 100.0 / (row_hits + row_misses + row_conflicts + 0.001);
        `uvm_info(get_name(), $sformatf(
            "=== Final Coverage Report ===\n" //
            "Total Transactions: %0d\n" //
            "Row Hits: %0d (%0.2f%%)\n" //
            "Row Misses: %0d\n" //
            "Row Conflicts: %0d",
            trans_history.size(),
            row_hits, hit_rate,
            row_misses, row_conflicts
        ), UVM_MEDIUM)
    endfunction
endclass

endpackage : hbm_coverage_pkg