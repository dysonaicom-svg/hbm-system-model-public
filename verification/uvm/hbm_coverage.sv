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
  // Bank Conflict Coverage (Enhanced)
  // ============================================================================
  covergroup bank_conflict_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 100;

    bank_id: coverpoint bank_id {
      bins banks[] = {[0:15]};
      bins bank_groups_0_3 = {[0:3]};
      bins bank_groups_4_7 = {[4:7]};
      bins bank_groups_8_11 = {[8:11]};
      bins bank_groups_12_15 = {[12:15]};
    }

    conflict_type: coverpoint conflict_type {
      bins same_bank_different_row = {1};
      bins same_row = {2};
      bins different_bank = {0};
      bins same_bank_same_row = {3};
    }

    cross bank_id, conflict_type;

    bank_group_conflict: coverpoint (bank_id / 4) {
      bins group0 = {0};
      bins group1 = {1};
      bins group2 = {2};
      bins group3 = {3};
    }
  endgroup : bank_conflict_cg

  // ============================================================================
  // Row Hammer Pattern Coverage
  // ============================================================================
  covergroup row_hammer_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 90;

    hammer_bank: coverpoint hammer_bank_id {
      bins banks[] = {[0:15]};
      bins all_banks = {[0:15]};
    }

    hammer_count: coverpoint hammer_count {
      bins low = {[1:10]};
      bins medium = {[11:50]};
      bins high = {[51:100]};
      bins very_high = {[101:500]};
      bins extreme = {[501:$]};
    }

    hammer_intensity: coverpoint hammer_intensity {
      bins single_row = {1};        // Same row activated repeatedly
      bins adjacent_row = {2};       // Adjacent rows activated
      bins both_adjacent = {3};      // Both sides activated
    }

    cross hammer_bank, hammer_intensity;
  endgroup : row_hammer_cg

  // ============================================================================
  // Refresh Command Coverage
  // ============================================================================
  covergroup refresh_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 100;

    refresh_type: coverpoint refresh_type {
      bins refresh_all = {0};       // All bank refresh
      bins refresh_group = {1};     // Bank group refresh
      bins self_refresh = {2};      // Self-refresh entry
      bins partial_refresh = {3};   // Partial array refresh
    }

    refresh_bank: coverpoint refresh_bank_id {
      bins banks[] = {[0:15]};
      bins all_banks = {[0:15]};
      bins bank_group_0 = {[0:3]};
      bins bank_group_1 = {[4:7]};
      bins bank_group_2 = {[8:11]};
      bins bank_group_3 = {[12:15]};
    }

    refresh_interval: coverpoint refresh_interval_cycles {
      bins very_short = {[1:10]};    // < 10 cycles
      bins short = {[11:50]};        // 11-50 cycles
      bins normal = {[51:200]};      // 51-200 cycles
      bins long = {[201:1000]};      // 201-1000 cycles
      bins very_long = {[1001:$]};  // > 1000 cycles
    }

    cross refresh_type, refresh_bank;
  endgroup : refresh_cg

  // ============================================================================
  // Channel Interleaving Coverage
  // ============================================================================
  covergroup channel_interleave_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 95;

    channel_id_cov: coverpoint channel_id {
      bins channels[] = {[0:31]};    // HBM4 supports 32 channels
      bins pseudo_channel_0 = {[0:15]};
      bins pseudo_channel_1 = {[16:31]};
    }

    interleave_depth: coverpoint interleave_depth {
      bins single = {1};
      bins two_way = {2};
      bins four_way = {4};
      bins eight_way = {8};
      bins sixteen_way = {16};
    }

    interleave_pattern: coverpoint interleave_pattern {
      bins sequential = {0};        // Consecutive addresses
      bins round_robin = {1};       // Round-robin across channels
      bins hash_based = {2};        // Hash-based distribution
      bins priority_based = {3};     // Priority-weighted
    }

    channel_switch_count: coverpoint channel_switches {
      bins low = {[1:5]};
      bins medium = {[6:20]};
      bins high = {[21:50]};
      bins very_high = {[51:$]};
    }

    cross channel_id_cov, interleave_pattern;
  endgroup : channel_interleave_cg

  // ============================================================================
  // Row Hit/Miss Coverage (Enhanced)
  // ============================================================================
  covergroup row_hit_miss_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 100;

    access_type: coverpoint access_type {
      bins row_hit = {2};           // Same row already open
      bins row_miss = {0};          // Bank idle, need ACT
      bins row_conflict = {1};      // Different row, need PRE + ACT
      bins row_close = {3};         // Bank closed, explicit PRE
    }

    channel: coverpoint channel_id {
      bins channels[] = {[0:31]};
      bins pc0 = {[0:15]};
      bins pc1 = {[16:31]};
    }

    row_address: coverpoint row_addr {
      bins low_rows = {[0:255]};
      bins mid_rows = {[256:16383]};
      bins high_rows = {[16384:65535]};
    }

    cross access_type, channel;
    cross access_type, row_address;
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
      bins channels[] = {[0:31]};
      bins pc0 = {[0:15]};
      bins pc1 = {[16:31]};
    }

    cross cmd_type, channel;
  endgroup : command_type_cg

  // ============================================================================
  // Latency Coverage (Enhanced)
  // ============================================================================
  covergroup latency_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 95;

    read_latency: coverpoint read_latency {
      bins very_fast = {[0:20]};     // < 20 cycles
      bins fast = {[21:40]};         // 21-40 cycles
      bins normal = {[41:60]};       // 41-60 cycles
      bins slow = {[61:100]};        // 61-100 cycles
      bins very_slow = {[101:$]};    // > 100 cycles
    }

    write_latency: coverpoint write_latency {
      bins very_fast = {[0:10]};    // < 10 cycles
      bins fast = {[11:20]};         // 11-20 cycles
      bins normal = {[21:40]};       // 21-40 cycles
      bins slow = {[41:60]};         // 41-60 cycles
      bins very_slow = {[61:$]};     // > 60 cycles
    }

    cmd_mix_latency: coverpoint cmd_type {
      bins activate_latency = {3'b011};   // ACT command timing
      bins read_latency_bin = {3'b010};  // READ timing
      bins write_latency_bin = {3'b001}; // WRITE timing
    }

    cross cmd_mix_latency, read_latency;
    cross cmd_mix_latency, write_latency;
  endgroup : latency_cg

  // ============================================================================
  // Bandwidth Coverage (Enhanced)
  // ============================================================================
  covergroup bandwidth_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 90;

    bandwidth_util: coverpoint bandwidth_util {
      bins idle = {0};              // No traffic
      bins low = {[1:25]};          // 1-25%
      bins medium = {[26:50]};      // 26-50%
      bins high = {[51:75]};        // 51-75%
      bins very_high = {[76:100]};  // 76-100%
    }

    read_write_ratio: coverpoint read_write_ratio {
      bins read_heavy = {[0:30]};      // > 70% reads
      bins balanced = {[31:69]};       // 31-69% reads
      bins write_heavy = {[70:100]};  // > 70% writes
    }

    data_width_util: coverpoint data_width_util {
      bins quarter = {[0:25]};
      bins half = {[26:50]};
      bins three_quarter = {[51:75]};
      bins full = {[76:100]};
    }

    cross bandwidth_util, read_write_ratio;
  endgroup : bandwidth_cg

  // ============================================================================
  // QoS Priority Coverage (Enhanced)
  // ============================================================================
  covergroup qos_priority_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 100;

    priority: coverpoint priority {
      bins critical = {4'd15};       // Highest priority
      bins high = {[4'd12:4'd14]};   // High priority
      bins medium_high = {[4'd10:4'd11]};  // Medium-high
      bins medium = {[4'd8:4'd9]};    // Medium priority
      bins medium_low = {[4'd5:4'd7]};     // Medium-low
      bins low = {[4'd1:4'd4]};       // Low priority
      bins background = {4'd0};      // Background/idle
    }

    channel: coverpoint channel_id {
      bins channels[] = {[0:31]};
      bins pc0 = {[0:15]};
      bins pc1 = {[16:31]};
    }

    priority_transition: coverpoint priority_transition {
      bins same_priority = {0};           // No change
      bins up_one = {[1:4]};              // Increase by 1-4 levels
      bins up_many = {[5:15]};             // Increase by 5+ levels
      bins down_one = {16};                // Decrease by 1
      bins down_few = {[17:20]};          // Decrease by 2-5
      bins down_many = {[21:31]};         // Decrease by 6+
    }

    qos_starvation: coverpoint starvation_cycles {
      bins none = {0};                   // No starvation
      bins short = {[1:50]};             // 1-50 cycles
      bins medium = {[51:200]};           // 51-200 cycles
      bins long = {[201:1000]};          // 201-1000 cycles
      bins severe = {[1001:$]};          // > 1000 cycles
    }

    cross priority, channel;
    cross priority, qos_starvation;
  endgroup : qos_priority_cg

  // ============================================================================
  // Combined Transaction Coverage
  // ============================================================================
  covergroup transaction_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 85;

    transaction_type: coverpoint transaction_type {
      bins single_read = {0};
      bins single_write = {1};
      bins burst_read = {2};
      bins burst_write = {3};
      bins read_modify_write = {4};
      bins activate = {5};
      bins precharge = {6};
      bins refresh = {7};
    }

    address_pattern: coverpoint address_pattern {
      bins sequential = {0};
      bins random = {1};
      bins stride = {2};
      bins bank_interleaved = {3};
      bins row_interleaved = {4};
    }

    data_pattern: coverpoint data_pattern {
      bins all_zeros = {0};
      bins all_ones = {1};
      bins walking_one = {2};
      bins walking_zero = {3};
      bins checkerboard = {4};
      bins random_data = {5};
    }

    cross transaction_type, address_pattern;
  endgroup : transaction_cg

endpackage : hbm_coverage_pkg

`endif // HBM_COVERAGE_SV