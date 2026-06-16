// ============================================================================
// Extended Coverage Test Package
// Additional covergroups for comprehensive HBM verification
// ============================================================================

package test_coverage_extended_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // -------------------------------------------------------------------------
  // Row Buffer Coverage - hit/miss/conflict patterns
  // -------------------------------------------------------------------------
  covergroup row_buffer_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 95;

    // Row buffer hit/miss patterns
    row_buffer_state: coverpoint row_buffer_state_t'({
      bins hit = {ROW_HIT};
      bins miss = {ROW_MISS};
      bins conflict = {ROW_CONFLICT};
      bins closed = {ROW_CLOSED};
    });

    // Bank group vs row buffer interaction
    bg_interaction: coverpoint (bank_group_id * 4 + row_buffer_state_t'(row_buffer_state)) {
      bins bg0_hit = {[0:3]};
      bins bg1_hit = {[4:7]};
      bins bg2_hit = {[8:11]};
      bins bg3_hit = {[12:15]};
    }
  endgroup

  // -------------------------------------------------------------------------
  // Command Timing Coverage - critical timing paths
  // -------------------------------------------------------------------------
  covergroup cmd_timing_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 90;

    // Command-to-command timing
    tCCD_L: coverpoint tCCD_value {
      bins min = {4};      // Minimum CCD
      bins mid = {[5:7]};
      bins max = {[8:$]};  // Extended
    }

    tRCD_L: coverpoint tRCD_value {
      bins min = {17};     // HBM3 tRCD
      bins extended = {[18:20]};
    }

    // Cross coverage
    tCCD_vs_RCD: cross tCCD_L, tRCD_L;
  endgroup

  // -------------------------------------------------------------------------
  // Power Coverage - power states and transitions
  // -------------------------------------------------------------------------
  covergroup power_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 85;

    power_state: coverpoint power_state_t'({
      bins active = {PWR_ACTIVE};
      bins standby = {PWR_STANDBY};
      bins self_refresh = {PWR_SELF_REFRESH};
      bins power_down = {PWR_POWER_DOWN};
    });

    power_transition: coverpoint (prev_power_state * 4 + power_state_t'(power_state)) {
      bins active_to_standby = {[PWR_ACTIVE*4+PWR_STANDBY]};
      bins standby_to_active = {[PWR_STANDBY*4+PWR_ACTIVE]};
      bins any_to_self_refresh = {[0:$]};
    }
  endgroup

  // -------------------------------------------------------------------------
  // Error Coverage - ECC/CRC error injection and detection
  // -------------------------------------------------------------------------
  covergroup error_cg @(posedge clk);
    option.per_instance = 1;
    option.goal = 80;

    error_type: coverpoint error_type_t {
      bins no_error = {ERR_NONE};
      bins single_bit = {ERR_SINGLE_BIT};
      bins multi_bit = {ERR_MULTI_BIT};
      bins uncorrectable = {ERR_UNCORRECTABLE};
    }

    error_detection: coverpoint error_detected {
      bins detected = {1};
      bins not_detected = {0};
    }

    cross error_type, error_detection;
  endgroup

endpackage
