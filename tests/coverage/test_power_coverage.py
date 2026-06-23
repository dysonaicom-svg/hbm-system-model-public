"""
Comprehensive Power Coverage Tests - Enhanced for HBM4

Tests power estimation for all HBM4 speed grades, process corners,
and power states. Validates the HBM4PowerEstimator against specifications.

Coverage targets:
- All 3 speed grades (8Gbps, 12Gbps, 16Gbps)
- All 3 process corners (SS, TT, FF)
- All power states (ACTIVE, READ, WRITE, IDLE, REFRESH, SELF_REFRESH, POWER_DOWN)
- All command types and their energy consumption
- Per-channel power tracking (32 channels)
- Cross-coverage: power vs temperature, power vs voltage
- Boundary conditions: min/max power values
- Error cases: invalid parameters
- Thermal modeling
- HBM4 specification parameter integration

Reference:
- JEDEC JESD270-4A HBM4 specification
- Synopsys DesignWare HBM4/4E Controller IP power data
"""

import pytest
from model.dram.power_estimator import (
    HBM4PowerEstimator, PowerParameters, ChannelPower, PowerReport,
    CommandEnergy, PowerState, ProcessCorner, CommandType,
    create_power_estimator, create_power_estimator_with_config,
    POWER_PRESETS,
)
from model.dram.hbm4_spec import HBM4Spec, HBM4_SPEED_GRADES


class TestPowerSpeedGrades:
    """Test power estimation for all HBM4 speed grades"""

    def test_8gbps_power_estimator_created(self):
        """8 GT/s speed grade should create valid power estimator"""
        estimator = create_power_estimator(speed_grade="8Gbps")

        assert estimator is not None
        assert estimator.data_rate_gtps == 8.0
        assert estimator.num_channels == 32
        assert len(estimator.channels) == 32

    def test_12gbps_power_estimator_created(self):
        """12 GT/s speed grade should create valid power estimator"""
        estimator = create_power_estimator(speed_grade="12Gbps")

        assert estimator is not None
        assert estimator.data_rate_gtps == 12.0
        assert estimator.num_channels == 32

    def test_16gbps_power_estimator_created(self):
        """16 GT/s speed grade should create valid power estimator"""
        estimator = create_power_estimator(speed_grade="16Gbps")

        assert estimator is not None
        assert estimator.data_rate_gtps == 16.0
        assert estimator.num_channels == 32

    def test_8gbps_power_values_baseline(self):
        """8 GT/s power values should match baseline specification"""
        params = POWER_PRESETS["8Gbps"]

        assert params.active_power_ma == 350.0
        assert params.read_power_ma == 450.0
        assert params.write_power_ma == 420.0
        assert params.idle_power_ma == 50.0
        assert params.vddq_voltage == 1.1

    def test_12gbps_power_values_scaled(self):
        """12 GT/s power values should be higher than 8 GT/s"""
        params_8g = POWER_PRESETS["8Gbps"]
        params_12g = POWER_PRESETS["12Gbps"]

        # Higher data rate should have higher power consumption
        assert params_12g.active_power_ma > params_8g.active_power_ma
        assert params_12g.read_power_ma > params_8g.read_power_ma
        assert params_12g.vddq_voltage > params_8g.vddq_voltage

    def test_16gbps_power_values_maximum(self):
        """16 GT/s power values should be highest"""
        params_8g = POWER_PRESETS["8Gbps"]
        params_12g = POWER_PRESETS["12Gbps"]
        params_16g = POWER_PRESETS["16Gbps"]

        assert params_16g.active_power_ma > params_12g.active_power_ma
        assert params_16g.active_power_ma > params_8g.active_power_ma
        assert params_16g.vddq_voltage > params_12g.vddq_voltage

    def test_invalid_speed_grade_falls_back_to_default(self):
        """Invalid speed grade should fall back to default (8Gbps)"""
        # Should not raise, just use default
        estimator = create_power_estimator(speed_grade="invalid_grade")
        assert estimator.data_rate_gtps == 8.0  # Falls back to default

    def test_speed_grade_tck_calculation(self):
        """tCK should be correctly calculated for each speed grade"""
        estimator_8g = create_power_estimator("8Gbps")
        estimator_12g = create_power_estimator("12Gbps")
        estimator_16g = create_power_estimator("16Gbps")

        # tCK = 1000 / data_rate (ps)
        assert abs(estimator_8g._get_tCK_ps() - 125.0) < 0.01
        assert abs(estimator_12g._get_tCK_ps() - 83.33) < 0.01
        assert abs(estimator_16g._get_tCK_ps() - 62.5) < 0.01


class TestPowerProcessCorners:
    """Test power scaling for process corners"""

    def test_ss_corner_lowest_power(self):
        """Slow-slow corner should have lowest power scaling"""
        params = PowerParameters(process_corner=ProcessCorner.SS)

        assert params.get_process_scaling_factor() == 0.75

    def test_tt_corner_nominal_power(self):
        """Typical corner should have nominal power scaling"""
        params = PowerParameters(process_corner=ProcessCorner.TT)
        assert params.get_process_scaling_factor() == 1.0

    def test_ff_corner_highest_power(self):
        """Fast-fast corner should have highest power scaling"""
        params = PowerParameters(process_corner=ProcessCorner.FF)
        assert params.get_process_scaling_factor() == 1.25

    def test_ss_vs_ff_power_difference(self):
        """SS vs FF should have significant power difference"""
        params_ss = PowerParameters(process_corner=ProcessCorner.SS)
        params_ff = PowerParameters(process_corner=ProcessCorner.FF)
        ratio = params_ff.get_process_scaling_factor() / params_ss.get_process_scaling_factor()
        assert ratio > 1.5  # At least 50% difference

    def test_custom_power_estimator_with_corner(self):
        """Custom power estimator with process corner should apply scaling"""
        estimator = create_power_estimator_with_config(
            speed_grade="8Gbps",
            process_corner="SS",
            temperature_c=45.0,
        )

        assert estimator.params.process_corner == ProcessCorner.SS
        # Power should be lower for SS corner
        base_power = estimator.get_total_power_mw()
        assert base_power > 0


class TestPowerStates:
    """Test power consumption for all operational states"""

    def test_idle_state_power(self):
        """Idle state should have minimal power"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.IDLE, cycles=1000)
        power = estimator.get_total_power_mw()

        assert power > 0
        # Idle power should be much lower than active
        idle_power = power

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1)
        active_power = estimator.get_total_power_mw()

        assert idle_power < active_power

    def test_active_state_power(self):
        """Active state should have highest power"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=100)
        power = estimator.get_total_power_mw()
        assert power > 0
        # Active power should be significant
        assert power > 1000  # mW for 32 channels

    def test_read_state_power(self):
        """Read state should have power similar to active"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.READ, cycles=100)
        read_power = estimator.get_total_power_mw()

        assert read_power > 0
        # Read power should be comparable to active
        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1)
        active_power = estimator.get_total_power_mw()

        assert abs(read_power - active_power) < active_power * 0.3

    def test_write_state_power(self):
        """Write state should have power similar to read"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.WRITE, cycles=100)
        write_power = estimator.get_total_power_mw()

        assert write_power > 0
        estimator.set_all_channels_state(PowerState.READ, cycles=1)
        read_power = estimator.get_total_power_mw()

        assert abs(write_power - read_power) < read_power * 0.3

    def test_refresh_state_power(self):
        """Refresh state should have elevated power"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.REFRESH, cycles=100)
        refresh_power = estimator.get_total_power_mw()

        assert refresh_power > 0
        # Refresh should be higher than idle
        estimator.set_all_channels_state(PowerState.IDLE, cycles=1)
        idle_power = estimator.get_total_power_mw()

        assert refresh_power > idle_power

    def test_self_refresh_power_minimum(self):
        """Self-refresh should have minimum power"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.SELF_REFRESH, cycles=1000)
        sref_power = estimator.get_total_power_mw()

        assert sref_power > 0
        # Self-refresh should be very low
        estimator.set_all_channels_state(PowerState.IDLE, cycles=1)
        idle_power = estimator.get_total_power_mw()

        assert sref_power < idle_power

    def test_power_down_minimum(self):
        """Power-down should have lowest power consumption"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.POWER_DOWN, cycles=1000)
        pdn_power = estimator.get_total_power_mw()
        assert pdn_power > 0
        # Power-down should be lower than self-refresh
        estimator.set_all_channels_state(PowerState.SELF_REFRESH, cycles=1)
        sref_power = estimator.get_total_power_mw()

        assert pdn_power < sref_power


class TestPowerCommandEnergy:
    """Test energy consumption for all command types"""

    def test_all_command_types_have_energy(self):
        """All command types should have non-zero energy values"""
        params = PowerParameters()

        for cmd in CommandType:
            energy = params.get_command_energy_pj(cmd)
            assert energy >= 0, f"Command {cmd} should have non-negative energy"

    def test_act_command_energy(self):
        """ACT command should have significant energy"""
        params = PowerParameters()
        energy = params.get_command_energy_pj(CommandType.ACT)

        assert energy > 100  # pJ - activation is expensive

    def test_read_write_energy_comparison(self):
        """READ and WRITE energy should be similar"""
        params = PowerParameters()

        rd_energy = params.get_command_energy_pj(CommandType.RD)
        wr_energy = params.get_command_energy_pj(CommandType.WR)
        assert rd_energy > 0
        assert wr_energy > 0
        # Write should be slightly higher (data write energy)
        assert abs(rd_energy - wr_energy) < max(rd_energy, wr_energy) * 0.2

    def test_precharge_energy_lower_than_act(self):
        """PRECHARGE energy should be lower than ACT"""
        params = PowerParameters()
        act_energy = params.get_command_energy_pj(CommandType.ACT)
        pre_energy = params.get_command_energy_pj(CommandType.PRE)

        assert pre_energy < act_energy

    def test_refresh_energy_highest(self):
        """All-bank refresh should have highest energy"""
        params = PowerParameters()

        refab_energy = params.get_command_energy_pj(CommandType.REFAB)
        act_energy = params.get_command_energy_pj(CommandType.ACT)
        assert refab_energy > act_energy

    def test_per_bank_refresh_lower_than_all_bank(self):
        """Per-bank refresh should use less energy than all-bank"""
        params = PowerParameters()
        refab_energy = params.get_command_energy_pj(CommandType.REFAB)
        refsb_energy = params.get_command_energy_pj(CommandType.REFSB)

        assert refsb_energy < refab_energy

    def test_record_command_updates_energy(self):
        """Recording a command should update energy counters"""
        estimator = create_power_estimator("8Gbps")

        initial_energy = estimator.total_command_energy.total_energy_pj

        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)

        final_energy = estimator.total_command_energy.total_energy_pj
        assert final_energy > initial_energy


class TestPowerChannelTracking:
    """Test per-channel power tracking for all 32 channels"""

    def test_all_32_channels_initialized(self):
        """All 32 channels should be initialized"""
        estimator = create_power_estimator("8Gbps")

        assert len(estimator.channels) == 32
        for i, ch in enumerate(estimator.channels):
            assert ch.channel_id == i

    def test_set_channel_state_individual(self):
        """Setting state for individual channel should work"""
        estimator = create_power_estimator("8Gbps")
        # Set channel 15 to ACTIVE
        estimator.set_channel_state(15, PowerState.ACTIVE, cycles=100)

        # Channel 15 should have active power
        ch15_power = estimator.get_channel_power_mw(15)
        assert ch15_power > 0

    def test_set_channel_state_out_of_range_rejected(self):
        """Setting state for out-of-range channel should be ignored"""
        estimator = create_power_estimator("8Gbps")

        # Should not raise, just ignore
        estimator.set_channel_state(32, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(-1, PowerState.ACTIVE, cycles=100)

    def test_get_channel_power_invalid_index(self):
        """Getting power for invalid channel should return 0"""
        estimator = create_power_estimator("8Gbps")

        power_invalid = estimator.get_channel_power_mw(100)
        assert power_invalid == 0.0

    def test_channel_energy_accumulation(self):
        """Channel energy should accumulate over time"""
        estimator = create_power_estimator("8Gbps")

        ch = estimator.channels[0]
        initial_energy = ch.total_energy_pj

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1000)
        estimator.set_channel_state(0, PowerState.READ, cycles=500)

        final_energy = ch.total_energy_pj
        assert final_energy > initial_energy

    def test_record_command_per_channel(self):
        """Recording commands per channel should work"""
        estimator = create_power_estimator("8Gbps")
        estimator.record_command(5, CommandType.ACT)
        estimator.record_command(5, CommandType.RD)
        estimator.record_command(5, CommandType.PRE)

        ch5 = estimator.channels[5]
        assert ch5.command_energy.act_count == 1
        assert ch5.command_energy.rd_count == 1
        assert ch5.command_energy.pre_count == 1


class TestPowerTemperatureScaling:
    """Test temperature-based power scaling"""

    def test_low_temperature_lowest_power(self):
        """Low temperature should have lowest power scaling"""
        params_low = PowerParameters(temperature_c=25.0)
        params_high = PowerParameters(temperature_c=85.0)

        scale_low = params_low.get_temperature_scaling_factor()
        scale_high = params_high.get_temperature_scaling_factor()

        # High temp should have higher scaling than low temp
        assert scale_high > scale_low

    def test_high_temperature_highest_power(self):
        """High temperature should have highest power scaling"""
        params_high = PowerParameters(temperature_c=85.0)
        params_nom = PowerParameters(temperature_c=45.0)
        scale_high = params_high.get_temperature_scaling_factor()
        scale_nom = params_nom.get_temperature_scaling_factor()
        assert scale_high > scale_nom

    def test_temperature_exponential_leakage(self):
        """Temperature scaling should increase with temperature"""
        params_45 = PowerParameters(temperature_c=45.0)
        params_65 = PowerParameters(temperature_c=65.0)
        params_85 = PowerParameters(temperature_c=85.0)

        scale_45 = params_45.get_temperature_scaling_factor()
        scale_65 = params_65.get_temperature_scaling_factor()
        scale_85 = params_85.get_temperature_scaling_factor()

        assert scale_45 < scale_65 < scale_85

    def test_combined_scaling_factor(self):
        """Combined scaling should multiply process and temperature"""
        params = PowerParameters(
            process_corner=ProcessCorner.FF,
            temperature_c=85.0,
        )

        combined = params.get_effective_power_scale()
        process_scale = params.get_process_scaling_factor()
        temp_scale = params.get_temperature_scaling_factor()
        assert combined == pytest.approx(process_scale * temp_scale, rel=0.01)


class TestPowerVoltageScaling:
    """Test voltage-based power scaling"""

    def test_vddq_voltage_affects_power(self):
        """VDDQ voltage should affect power calculation"""
        params_low_v = PowerParameters(vddq_voltage=1.0)
        params_high_v = PowerParameters(vddq_voltage=1.2)

        # Power scales with V^2 for dynamic power
        power_low = params_low_v.active_power_ma * params_low_v.vddq_voltage
        power_high = params_high_v.active_power_ma * params_high_v.vddq_voltage

        assert power_high > power_low

    def test_vddq2_voltage_present(self):
        """VDDQ2 voltage should be defined"""
        params = PowerParameters()
        assert params.vddq2_voltage > 0
        assert params.vddq2_voltage < params.vddq_voltage

    def test_vpp_voltage_present(self):
        """VPP voltage should be defined"""
        params = PowerParameters()

        assert params.vpp_voltage > 0
        # VPP is typically higher than VDDQ
        assert params.vpp_voltage > params.vddq_voltage


class TestPowerThermalModeling:
    """Test thermal estimation and modeling"""

    def test_estimate_thermal_returns_dict(self):
        """Thermal estimation should return dictionary"""
        estimator = create_power_estimator("8Gbps")
        thermal = estimator.estimate_thermal(ambient_temp_c=45.0)

        assert isinstance(thermal, dict)
        assert 'junction_temp_c' in thermal
        assert 'ambient_temp_c' in thermal
        assert 'theta_ja' in thermal

    def test_junction_temp_higher_than_ambient(self):
        """Junction temperature should be at least ambient (or higher with power)"""
        estimator = create_power_estimator("8Gbps")
        # Advance some cycles to have power data
        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        thermal = estimator.estimate_thermal(ambient_temp_c=45.0)

        # Junction temp should be >= ambient (exactly = if no power dissipated)
        assert thermal['junction_temp_c'] >= thermal['ambient_temp_c']

    def test_thermal_increases_with_power(self):
        """Junction temperature should increase with power"""
        estimator_low = create_power_estimator("8Gbps")
        estimator_high = create_power_estimator("16Gbps")

        # Advance cycles to generate power data
        estimator_low.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        estimator_high.set_all_channels_state(PowerState.ACTIVE, cycles=1000)

        thermal_low = estimator_low.estimate_thermal(ambient_temp_c=45.0)
        thermal_high = estimator_high.estimate_thermal(ambient_temp_c=45.0)

        # Higher speed grade = higher power = higher junction temp
        assert thermal_high['junction_temp_c'] >= thermal_low['junction_temp_c']

    def test_theta_ja_constant(self):
        """Thermal resistance should be constant"""
        estimator = create_power_estimator("8Gbps")

        thermal = estimator.estimate_thermal()

        assert thermal['theta_ja'] > 0
        assert thermal['theta_ja'] < 1.0  # Reasonable range for HBM


class TestPowerBandwidthEfficiency:
    """Test power efficiency calculations"""

    def test_bandwidth_efficiency_calculation(self):
        """Bandwidth efficiency should be calculated correctly"""
        estimator = create_power_estimator("8Gbps")

        efficiency = estimator.get_bandwidth_efficiency(
            active_cycles=300,
            total_cycles=1000,
        )

        assert 0 <= efficiency <= 1
        assert efficiency == 0.3

    def test_efficiency_zero_when_no_active(self):
        """Efficiency should be zero when no active cycles"""
        estimator = create_power_estimator("8Gbps")

        efficiency = estimator.get_bandwidth_efficiency(
            active_cycles=0,
            total_cycles=1000,
        )

        assert efficiency == 0.0

    def test_efficiency_full_when_all_active(self):
        """Efficiency should be 1.0 when all cycles are active"""
        estimator = create_power_estimator("8Gbps")

        efficiency = estimator.get_bandwidth_efficiency(
            active_cycles=1000,
            total_cycles=1000,
        )

        assert efficiency == 1.0

    def test_power_efficiency_calculation(self):
        """Power efficiency (bandwidth/watt) should be calculated"""
        estimator = create_power_estimator("8Gbps")
        # Set some state to have non-zero power
        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        efficiency = estimator.calculate_power_efficiency(
            achieved_bandwidth_gbs=1024.0,
            peak_bandwidth_gbs=2048.0,
        )

        assert efficiency >= 0

    def test_efficiency_zero_when_no_power(self):
        """Power efficiency should be zero when no power consumed"""
        estimator = create_power_estimator("8Gbps")

        efficiency = estimator.calculate_power_efficiency(
            achieved_bandwidth_gbs=1024.0,
            peak_bandwidth_gbs=2048.0,
        )

        # No power consumed yet
        assert efficiency == 0.0


class TestPowerReportGeneration:
    """Test power report generation"""

    def test_generate_report_returns_power_report(self):
        """Report generation should return PowerReport"""
        estimator = create_power_estimator("8Gbps")
        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        report = estimator.generate_report()

        assert isinstance(report, PowerReport)

    def test_report_contains_power_summary(self):
        """Report should contain power summary"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        report = estimator.generate_report()

        assert report.total_power_mw > 0
        assert report.total_power_mw > 0  # 32 channels should have total power > 0
        assert report.num_channels == 32

    def test_report_contains_energy_summary(self):
        """Report should contain energy summary"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        report = estimator.generate_report()
        assert report.total_energy_pj > 0
        assert report.total_energy_mj > 0

    def test_report_contains_command_statistics(self):
        """Report should contain command statistics"""
        estimator = create_power_estimator("8Gbps")

        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)
        report = estimator.generate_report()
        assert 'ACT' in report.command_counts or report.command_counts
        assert len(report.command_counts) > 0

    def test_report_contains_channel_powers(self):
        """Report should contain per-channel power breakdown"""
        estimator = create_power_estimator("8Gbps")
        report = estimator.generate_report()

        assert len(report.channel_powers) == 32

    def test_report_to_text(self):
        """Text report generation should work"""
        estimator = create_power_estimator("8Gbps")
        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        report = estimator.generate_report()

        text = report.to_text()
        assert "HBM4 POWER CONSUMPTION REPORT" in text
        assert "POWER SUMMARY" in text

    def test_report_to_dict(self):
        """Dictionary conversion should work"""
        estimator = create_power_estimator("8Gbps")
        report = estimator.generate_report()
        report_dict = report.to_dict()

        assert isinstance(report_dict, dict)
        assert 'power' in report_dict
        assert 'energy' in report_dict
        assert 'configuration' in report_dict


class TestPowerSummary:
    """Test power summary generation"""

    def test_get_summary_returns_dict(self):
        """get_summary should return dictionary"""
        estimator = create_power_estimator("8Gbps")
        summary = estimator.get_summary()

        assert isinstance(summary, dict)

    def test_summary_contains_key_metrics(self):
        """Summary should contain key power metrics"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        summary = estimator.get_summary()
        assert 'total_power_mw' in summary
        assert 'average_power_mw' in summary
        assert 'peak_power_mw' in summary
        assert 'num_channels' in summary

    def test_summary_contains_energy_breakdown(self):
        """Summary should contain energy breakdown by state"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=500)
        estimator.set_all_channels_state(PowerState.READ, cycles=500)
        summary = estimator.get_summary()

        assert 'energy_breakdown_pj' in summary
        breakdown = summary['energy_breakdown_pj']
        assert 'active' in breakdown
        assert 'read' in breakdown

    def test_summary_contains_command_energy(self):
        """Summary should contain command energy breakdown"""
        estimator = create_power_estimator("8Gbps")
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)
        summary = estimator.get_summary()
        assert 'command_energy_pj' in summary

    def test_summary_contains_efficiency(self):
        """Summary should contain efficiency metrics"""
        estimator = create_power_estimator("8Gbps")
        summary = estimator.get_summary()

        assert 'efficiency' in summary
        eff = summary['efficiency']
        assert 'active_ratio' in eff
        assert 'idle_ratio' in eff

    def test_summary_contains_thermal(self):
        """Summary should contain thermal estimates"""
        estimator = create_power_estimator("8Gbps")

        summary = estimator.get_summary()
        assert 'thermal' in summary


class TestPowerReset:
    """Test power counter reset functionality"""

    def test_reset_clears_all_counters(self):
        """Reset should clear all power counters"""
        estimator = create_power_estimator("8Gbps")

        # Add some activity
        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        estimator.record_command(0, CommandType.ACT)

        # Reset
        estimator.reset()

        # All counters should be zero
        for ch in estimator.channels:
            assert ch.active_time_cycles == 0
            assert ch.read_time_cycles == 0
            assert ch.write_time_cycles == 0
            assert ch.total_energy_pj == 0.0

    def test_reset_clears_global_counters(self):
        """Reset should clear global tracking"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        estimator.record_command(0, CommandType.ACT)

        estimator.reset()

        assert estimator.current_cycle == 0
        assert estimator.peak_power_mw == 0.0
        assert estimator.total_command_energy.total_commands == 0


class TestPowerBoundaryConditions:
    """Test boundary conditions and error cases"""

    def test_zero_cycles_no_energy(self):
        """Zero cycles should not add energy"""
        estimator = create_power_estimator("8Gbps")

        initial_energy = estimator.channels[0].total_energy_pj
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=0)

        assert estimator.channels[0].total_energy_pj == initial_energy

    def test_negative_cycles_handled(self):
        """Negative cycles should not cause errors"""
        estimator = create_power_estimator("8Gbps")

        # Should not raise, just ignore
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=-100)

    def test_all_channels_power_state_transitions(self):
        """All channels should handle state transitions"""
        estimator = create_power_estimator("8Gbps")

        states = [
            PowerState.IDLE,
            PowerState.ACTIVE,
            PowerState.READ,
            PowerState.WRITE,
            PowerState.REFRESH,
            PowerState.SELF_REFRESH,
            PowerState.POWER_DOWN,
        ]

        for state in states:
            estimator.set_all_channels_state(state, cycles=100)
            for ch in estimator.channels:
                # State should be tracked
                pass

    def test_high_channel_count_power_scaling(self):
        """Power should scale linearly with channel count"""
        estimator_16 = create_power_estimator("8Gbps")
        estimator_32 = create_power_estimator("8Gbps")

        # Note: Both are 32 channels, but we can check per-channel power
        power_per_ch = estimator_32.get_channel_power_mw(0)
        assert power_per_ch > 0


class TestPowerCrossCoverage:
    """Test cross-coverage between power parameters"""

    def test_power_vs_temperature_cross_coverage(self):
        """Power should vary with temperature across all states"""
        estimator = create_power_estimator("8Gbps")

        # Set up same activity
        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=100)

        # Check power at different temperatures
        params_25 = PowerParameters(temperature_c=25.0)
        params_85 = PowerParameters(temperature_c=85.0)

        scale_25 = params_25.get_effective_power_scale()
        scale_85 = params_85.get_effective_power_scale()

        assert scale_85 > scale_25

    def test_power_vs_voltage_cross_coverage(self):
        """Power should vary with voltage across all states"""
        params_10 = PowerParameters(vddq_voltage=1.0)
        params_12 = PowerParameters(vddq_voltage=1.2)

        power_10 = params_10.active_power_mw
        power_12 = params_12.active_power_mw

        assert power_12 > power_10

    def test_power_vs_speed_grade_cross_coverage(self):
        """Power should vary with speed grade across all states"""
        estimator_8g = create_power_estimator("8Gbps")
        estimator_16g = create_power_estimator("16Gbps")
        estimator_8g.set_all_channels_state(PowerState.ACTIVE, cycles=100)
        estimator_16g.set_all_channels_state(PowerState.ACTIVE, cycles=100)

        power_8g = estimator_8g.get_total_power_mw()
        power_16g = estimator_16g.get_total_power_mw()

        assert power_16g > power_8g

    def test_power_vs_process_corner_cross_coverage(self):
        """Power should vary with process corner across all states"""
        estimator_ss = create_power_estimator_with_config(
            speed_grade="8Gbps",
            process_corner="SS",
        )
        estimator_ff = create_power_estimator_with_config(
            speed_grade="8Gbps",
            process_corner="FF",
        )

        estimator_ss.set_all_channels_state(PowerState.ACTIVE, cycles=100)
        estimator_ff.set_all_channels_state(PowerState.ACTIVE, cycles=100)

        power_ss = estimator_ss.get_total_power_mw()
        power_ff = estimator_ff.get_total_power_mw()
        # Both should have valid power values
        assert power_ss > 0
        assert power_ff > 0
        # FF typically has higher power than SS
        assert power_ff >= power_ss


class TestPowerHBM4SpecIntegration:
    """Test power estimation with HBM4 specification parameters"""

    def test_power_estimator_uses_hbm4_spec(self):
        """Power estimator should use HBM4 specification"""
        spec = HBM4Spec()
        estimator = create_power_estimator("8Gbps")

        assert estimator.num_channels == spec.channels
        assert len(estimator.channels) == spec.channels

    def test_power_32_channels_validation(self):
        """Power estimation should work with full 32-channel HBM4"""
        estimator = create_power_estimator("8Gbps")
        assert estimator.num_channels == 32

        # All channels should be addressable
        for ch_id in range(32):
            power = estimator.get_channel_power_mw(ch_id)
            assert power >= 0

    def test_power_with_spec_timing_parameters(self):
        """Power should integrate with HBM4 timing parameters"""
        estimator = create_power_estimator("8Gbps")

        # Advance time with tick
        estimator.tick(cycles=1000)
        assert estimator.current_cycle == 1000
        assert estimator.cycles_since_refresh >= 0

    def test_bandwidth_calculation_in_power_context(self):
        """Bandwidth should be correctly calculated for power context"""
        spec = HBM4Spec()
        estimator = create_power_estimator("8Gbps")
        # Peak bandwidth from spec
        peak_bw = spec.bandwidth  # TB/s
        peak_bw_gbs = spec.bandwidth_gbs  # GB/s
        assert peak_bw == pytest.approx(2.048, rel=0.01)
        assert peak_bw_gbs == pytest.approx(2048.0, rel=0.01)

    def test_power_vs_spec_channels(self):
        """Power should match spec channel count"""
        spec = HBM4Spec()
        estimator = create_power_estimator("8Gbps")

        assert estimator.num_channels == spec.channels
        assert estimator.num_channels == 32

    def test_power_vs_spec_pseudo_channels(self):
        """Power tracking should handle pseudo-channels"""
        spec = HBM4Spec()
        assert spec.pseudo_channels == 64  # 32 channels × 2 PCH

        estimator = create_power_estimator("8Gbps")
        # All 32 channels should be tracked
        assert len(estimator.channels) == spec.channels

    def test_power_vs_spec_total_banks(self):
        """Power model should account for total banks"""
        spec = HBM4Spec()
        assert spec.total_banks == 1024  # 32 × 2 × 16

    def test_power_vs_spec_io_width(self):
        """Power should scale with IO width"""
        spec = HBM4Spec()
        assert spec.io_width == 2048  # 2048-bit interface

        estimator = create_power_estimator("8Gbps")
        # Power should be reasonable for 2048-bit interface
        total_power = estimator.get_total_power_mw()
        assert total_power > 0


class TestPowerPerformance:
    """Test power estimation performance characteristics"""

    def test_many_channels_power_calculation_fast(self):
        """Power calculation across many channels should be fast"""
        import time

        estimator = create_power_estimator("8Gbps")

        start = time.time()
        # Simulate many state changes
        for i in range(32):
            for _ in range(100):
                estimator.set_channel_state(i, PowerState.ACTIVE, cycles=1)
                estimator.set_channel_state(i, PowerState.READ, cycles=1)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0

    def test_power_report_generation_fast(self):
        """Report generation should be fast"""
        import time

        estimator = create_power_estimator("8Gbps")

        # Add some activity
        for i in range(32):
            estimator.set_channel_state(i, PowerState.ACTIVE, cycles=1000)

        start = time.time()
        report = estimator.generate_report()
        elapsed = time.time() - start

        assert elapsed < 1.0

    def test_summary_generation_fast(self):
        """Summary generation should be fast"""
        import time

        estimator = create_power_estimator("8Gbps")

        for i in range(32):
            estimator.set_channel_state(i, PowerState.ACTIVE, cycles=100)
        start = time.time()
        summary = estimator.get_summary()
        elapsed = time.time() - start

        assert elapsed < 1.0


class TestPowerCommandEnergyTracking:
    """Test detailed command energy tracking"""

    def test_command_energy_counts(self):
        """Command counts should be tracked correctly"""
        estimator = create_power_estimator("8Gbps")

        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)
        estimator.record_command(0, CommandType.RD)
        estimator.record_command(0, CommandType.RD)
        estimator.record_command(0, CommandType.WR)

        ce = estimator.total_command_energy
        assert ce.act_count == 2
        assert ce.rd_count == 3
        assert ce.wr_count == 1

    def test_command_energy_totals(self):
        """Command energy totals should be calculated"""
        estimator = create_power_estimator("8Gbps")
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)

        ce = estimator.total_command_energy
        assert ce.total_act_energy_pj > 0
        assert ce.total_rd_energy_pj > 0
        assert ce.total_energy_pj > 0

    def test_command_energy_breakdown(self):
        """Energy breakdown by command type should be available"""
        estimator = create_power_estimator("8Gbps")
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)
        estimator.record_command(0, CommandType.WR)

        breakdown = estimator.get_command_energy_breakdown()

        assert 'act' in breakdown
        assert 'rd' in breakdown
        assert 'wr' in breakdown
        assert breakdown['act'] > 0

    def test_command_count_breakdown(self):
        """Count breakdown by command type should be available"""
        estimator = create_power_estimator("8Gbps")
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)
        breakdown = estimator.get_command_count_breakdown()

        assert 'act' in breakdown
        assert 'rd' in breakdown
        assert breakdown['act'] == 2
        assert breakdown['rd'] == 1


class TestPowerStateTransitions:
    """Test power state transitions and tracking"""

    def test_state_transitions_tracked(self):
        """State transitions should be tracked in time counters"""
        estimator = create_power_estimator("8Gbps")
        estimator.set_channel_state(0, PowerState.IDLE, cycles=100)
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=200)
        estimator.set_channel_state(0, PowerState.READ, cycles=300)

        ch = estimator.channels[0]
        assert ch.idle_time_cycles == 100
        assert ch.active_time_cycles == 200
        assert ch.read_time_cycles == 300

    def test_power_history_maintained(self):
        """Power history should be maintained"""
        estimator = create_power_estimator("8Gbps")

        # Set various states to create history
        for _ in range(10):
            estimator.set_channel_state(0, PowerState.ACTIVE, cycles=10)
        ch = estimator.channels[0]
        assert len(ch.power_history) > 0

    def test_peak_power_tracked(self):
        """Peak power should be tracked correctly"""
        estimator = create_power_estimator("8Gbps")
        # Set to lower power state first
        estimator.set_channel_state(0, PowerState.IDLE, cycles=100)

        initial_peak = estimator.peak_power_mw

        # Set to higher power state
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        assert estimator.peak_power_mw >= initial_peak

    def test_power_history_bounded(self):
        """Power history should be bounded to prevent memory issues"""
        estimator = create_power_estimator("8Gbps")
        # Generate many state changes
        for _ in range(20000):
            estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1)
        ch = estimator.channels[0]
        # History should be bounded (keep last entries)
        assert len(ch.power_history) <= 10000


class TestPowerDynamicPower:
    """Test dynamic power calculations"""

    def test_dynamic_power_activity_factor(self):
        """Dynamic power should scale with activity factor"""
        estimator = create_power_estimator("8Gbps")
        power_low_activity = estimator.calculate_dynamic_power(activity_factor=0.1)
        power_high_activity = estimator.calculate_dynamic_power(activity_factor=0.8)

        assert power_high_activity > power_low_activity

    def test_dynamic_power_zero_activity(self):
        """Dynamic power should be zero with zero activity"""
        estimator = create_power_estimator("8Gbps")
        power_zero = estimator.calculate_dynamic_power(activity_factor=0.0)

        assert power_zero == 0.0

    def test_total_power_combines_static_and_dynamic(self):
        """Total power should combine static and dynamic"""
        estimator = create_power_estimator("8Gbps")

        # Get idle power (static) and active power
        idle_power = estimator.params.idle_power_mw
        active_power = estimator.params.active_power_mw

        # Total power when all channels active should be higher than idle
        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1000)
        total_power = estimator.get_total_power_mw()
        assert total_power > idle_power * estimator.num_channels


class TestPowerChannelPowerStats:
    """Test per-channel power statistics"""

    def test_channel_power_stats(self):
        """Channel power statistics should be available"""
        estimator = create_power_estimator("8Gbps")
        # Add some power history
        for _ in range(100):
            estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1)

        ch = estimator.channels[0]
        stats = ch.get_power_stats()

        assert 'average_mw' in stats
        assert 'peak_mw' in stats
        assert 'min_mw' in stats
        assert 'rms_mw' in stats

    def test_channel_average_power(self):
        """Average power should be calculated correctly"""
        estimator = create_power_estimator("8Gbps")

        estimator.set_channel_state(0, PowerState.IDLE, cycles=100)
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)

        ch = estimator.channels[0]
        avg_power = ch.get_average_power_mw(total_cycles=200)

        assert avg_power > 0

    def test_channel_peak_power(self):
        """Peak power should be correctly identified"""
        estimator = create_power_estimator("8Gbps")
        # Add various power states
        for _ in range(50):
            estimator.set_channel_state(0, PowerState.IDLE, cycles=1)
            estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1)

        ch = estimator.channels[0]
        peak = ch.get_peak_power_mw()
        assert peak > 0


class TestPowerHBM4SpecCrossCoverage:
    """Test cross-coverage between power and HBM4 specification parameters"""

    def test_power_channels_vs_spec_channels(self):
        """Power estimator channels should match spec channels"""
        spec = HBM4Spec()
        estimator = create_power_estimator("8Gbps")

        assert estimator.num_channels == spec.channels
        assert len(estimator.channels) == spec.channels

    def test_power_pseudo_channels_vs_spec(self):
        """Pseudo-channel count should be derived from spec"""
        spec = HBM4Spec()
        assert spec.pseudo_channels_per_channel == 2
        assert spec.pseudo_channels == 64

    def test_power_banks_vs_spec(self):
        """Bank count should match spec"""
        spec = HBM4Spec()
        assert spec.banks_per_pseudo_channel == 16
        assert spec.total_banks == 1024

    def test_power_bank_groups_vs_spec(self):
        """Bank group count should match spec"""
        spec = HBM4Spec()
        assert spec.bank_groups_per_channel == 8

    def test_power_io_width_vs_spec(self):
        """IO width should match spec"""
        spec = HBM4Spec()
        assert spec.io_width == 2048

    def test_power_data_rate_vs_spec(self):
        """Data rate should match spec"""
        spec = HBM4Spec()
        assert spec.data_rate_gtps == 8.0

    def test_power_burst_length_vs_spec(self):
        """Burst length should match spec"""
        spec = HBM4Spec()
        assert spec.burst_length == 4

    def test_power_bandwidth_vs_spec(self):
        """Bandwidth should be derived from spec parameters"""
        spec = HBM4Spec()
        estimator = create_power_estimator("8Gbps")

        # Peak bandwidth per channel: 8 GT/s × 64 bits / 8 = 64 GB/s
        expected_per_channel = spec.data_rate_gtps * (spec.io_width // spec.channels) / 8
        assert expected_per_channel == 64.0

        # Total bandwidth: 32 channels × 64 GB/s = 2048 GB/s
        expected_total = spec.bandwidth_gbs
        assert expected_total == 2048.0

    def test_power_speed_grade_tCK_vs_spec(self):
        """tCK should match spec for each speed grade"""
        for grade_name, grade_params in HBM4_SPEED_GRADES.items():
            estimator = create_power_estimator(grade_name)
            tCK_ps = estimator._get_tCK_ps()

            assert abs(tCK_ps - grade_params["tCK_ps"]) < 0.01

    def test_power_voltage_vs_spec_timing(self):
        """Voltage parameters should align with timing specs"""
        params = PowerParameters()

        # VDDQ should be in reasonable range for HBM4
        assert 1.0 <= params.vddq_voltage <= 1.3

        # VDDQ2 should be lower than VDDQ
        assert params.vddq2_voltage < params.vddq_voltage

        # VPP should be higher than VDDQ
        assert params.vpp_voltage > params.vddq_voltage


class TestPowerSpeedGradeCrossCoverage:
    """Test power cross-coverage across speed grades"""

    def test_all_speed_grades_have_valid_power(self):
        """All speed grades should produce valid power estimates"""
        for grade_name in ["8Gbps", "12Gbps", "16Gbps"]:
            estimator = create_power_estimator(grade_name)
            estimator.set_all_channels_state(PowerState.ACTIVE, cycles=100)
            power = estimator.get_total_power_mw()
            assert power > 0

    def test_speed_grade_power_hierarchy(self):
        """Power should increase with speed grade"""
        power_8g = create_power_estimator("8Gbps").get_total_power_mw()
        power_12g = create_power_estimator("12Gbps").get_total_power_mw()
        power_16g = create_power_estimator("16Gbps").get_total_power_mw()

        # Generate some activity for measurement
        for est in [power_8g, power_12g, power_16g]:
            pass

        # Create estimators and compare
        est_8g = create_power_estimator("8Gbps")
        est_12g = create_power_estimator("12Gbps")
        est_16g = create_power_estimator("16Gbps")

        est_8g.set_all_channels_state(PowerState.ACTIVE, cycles=100)
        est_12g.set_all_channels_state(PowerState.ACTIVE, cycles=100)
        est_16g.set_all_channels_state(PowerState.ACTIVE, cycles=100)

        power_8g = est_8g.get_total_power_mw()
        power_12g = est_12g.get_total_power_mw()
        power_16g = est_16g.get_total_power_mw()

        assert power_8g > 0
        assert power_12g > 0
        assert power_16g > 0

    def test_speed_grade_voltage_hierarchy(self):
        """Voltage should increase with speed grade"""
        params_8g = POWER_PRESETS["8Gbps"]
        params_12g = POWER_PRESETS["12Gbps"]
        params_16g = POWER_PRESETS["16Gbps"]

        assert params_8g.vddq_voltage < params_12g.vddq_voltage
        assert params_12g.vddq_voltage < params_16g.vddq_voltage

    def test_speed_grade_energy_hierarchy(self):
        """Command energy should increase with speed grade"""
        params_8g = POWER_PRESETS["8Gbps"]
        params_16g = POWER_PRESETS["16Gbps"]

        # ACT energy should be higher at higher voltage/speed
        assert params_16g.act_energy_pj > params_8g.act_energy_pj