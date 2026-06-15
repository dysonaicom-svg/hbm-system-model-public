// ============================================================================
// HBM Functional Coverage
// ============================================================================
// Covergroups for:
// - Bank conflicts
// - Row hit/miss rates
// - Queue fullness
// - Command types (ACT/PRE/RD/WR)
// ============================================================================

`ifndef HBM_COVERAGE_SV
`define HBM_COVERAGE_SV

// ============================================================================
// Coverage Package
// ============================================================================
package hbm_coverage_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // ============================================================================
  // Bank Conflict Coverage
  // ============================================================================
  covergroup bank_conflict_cg @(posedge clk);
    option.per_instance = 1;

    bank_id: coverpoint bank_id {
      bins banks[] = {[0:15]};
    }

    conflict_type: coverpoint conflict_type {
      bins same_bank_different_row = {1};
      bins same_row = {2};
      bins different_bank = {0};
    }

    cross bank_id, conflict_type;
  endgroup : bank_conflict_cg

  // ============================================================================
  // Row Hit/Miss Coverage
  // ============================================================================
  covergroup row_hit_miss_cg @(posedge clk);
    option.per_instance = 1;

    access_type: coverpoint access_type {
      bins row_hit = {2};    // Same row already open
      bins row_miss = {0};   // Bank idle, need ACT
      bins row_conflict = {1}; // Different row, need PRE + ACT
    }

    channel: coverpoint channel_id {
      bins channels[] = {[0:7]};
    }

    cross access_type, channel;
  endgroup : row_hit_miss_cg

  // ============================================================================
  // Queue Fullness Coverage
  // ============================================================================
  covergroup queue_fullness_cg @(posedge clk);
    option.per_instance = 1;

    read_queue_depth: coverpoint read_queue_depth {
      bins empty = {[0:4]};
      bins low = {[5:10]};
      bins medium = {[11:20]};
      bins high = {[21:30]};
      bins full = {[31:32]};
    }

    write_queue_depth: coverpoint write_queue_depth {
      bins empty = {[0:4]};
      bins low = {[5:10]};
      bins medium = {[11:20]};
      bins high = {[21:30]};
      bins full = {[31:32]};
    }

    cross read_queue_depth, write_queue_depth;
  endgroup : queue_fullness_cg

  // ============================================================================
  // Command Type Coverage
  // ============================================================================
  covergroup command_type_cg @(posedge clk);
    option.per_instance = 1;

    cmd_type: coverpoint cmd_type {
      bins activate = {3'b011};  // ACT
      bins precharge = {3'b100}; // PRE
      bins read = {3'b010};      // READ
      bins write = {3'b001};     // WRITE
      bins refresh = {3'b101};   // REFRESH
      bins idle = {3'b000};      // IDLE
    }

    channel: coverpoint channel_id {
      bins channels[] = {[0:7]};
    }

    cross cmd_type, channel;
  endgroup : command_type_cg

  // ============================================================================
  // Latency Coverage
  // ============================================================================
  covergroup latency_cg @(posedge clk);
    option.per_instance = 1;

    read_latency: coverpoint read_latency {
      bins very_fast = {[0:20]};
      bins fast = {[21:40]};
      bins normal = {[41:60]};
      bins slow = {[61:100]};
      bins very_slow = {[101:$]};
    }

    write_latency: coverpoint write_latency {
      bins very_fast = {[0:10]};
      bins fast = {[11:20]};
      bins normal = {[21:40]};
      bins slow = {[41:60]};
      bins very_slow = {[61:$]};
    }
  endgroup : latency_cg

  // ============================================================================
  // Bandwidth Coverage
  // ============================================================================
  covergroup bandwidth_cg @(posedge clk);
    option.per_instance = 1;

    bandwidth_util: coverpoint bandwidth_util {
      bins low = {[0:25]};       // 0-25%
      bins medium = {[26:50]};    // 26-50%
      bins high = {[51:75]};      // 51-75%
      bins very_high = {[76:100]}; // 76-100%
    }
  endgroup : bandwidth_cg

  // ============================================================================
  // QoS Priority Coverage
  // ============================================================================
  covergroup qos_priority_cg @(posedge clk);
    option.per_instance = 1;

    priority: coverpoint priority {
      bins critical = {4'd15};  // Highest priority
      bins high = {[4'd12:4'd14]};
      bins medium = {[4'd8:4'd11]};
      bins low = {[4'd1:4'd7]};
      bins background = {4'd0};
    }

    channel: coverpoint channel_id {
      bins channels[] = {[0:7]};
    }

    cross priority, channel;
  endgroup : qos_priority_cg

endpackage : hbm_coverage_pkg

`endif // HBM_COVERAGE_SV