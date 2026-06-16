"""
Comprehensive Tests for HBM3/4 Power Estimator

Tests power consumption estimation based on:
- JEDEC JESD238 HBM3 specifications
- JEDEC JESD270-4A HBM4 specifications
- Per-channel power tracking
- Command-based power calculation (ACT, RD, WR, REF, PRE)
- Temperature-dependent power scaling
- Process corner modeling (SS, TT, FF)
- Voltage scaling support
- Power state machine (active, idle, refresh, self-refresh, power-down)

Reference:
- JEDEC JESD238 HBM3 specification
- JEDEC JESD270-4A HBM4 specification
- Synopsys DesignWare HBM3/HBM4 Power Analysis
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from model.dram.power_estimator import (
    PowerState,
    PowerParameters,
    ChannelPower,
    HBM4PowerEstimator,
    DEFAULT_POWER_ESTIMATOR,
    POWER_PRESETS,
    HBM3_POWER_PRESETS,
    ALL_POWER_PRESETS,
    create_power_estimator,
    create_power_estimator_with_config,
    create_hbm3_power_estimator,
    create_power_estimator_for_version,
    CommandType,
    CommandEnergy,
    ProcessCorner,
    PowerReport,
)


# =============================================================================
# Test HBM3 Power Specifications (JEDEC JESD238)
# =============================================================================

class TestHBM3Specifications:
    """Tests for HBM3 power specifications per JEDEC JESD238"""

    def test_hbm3_64_active_power(self):
        """Test HBM3 6.4 Gbps active power (~120mW/channel)"""
        params = HBM3_POWER_PRESETS["hbm3_64"]

        # Active power: ~120mW/channel at 1.1V
        active_power_mw = params.active_power_mw
        assert active_power_mw == pytest.approx(120.0, rel=0.1), \
            f"Expected ~120mW, got {active_power_mw}mW"

    def test_hbm3_64_read_power(self):
        """Test HBM3 6.4 Gbps read power (~80mW/channel)"""
        params = HBM3_POWER_PRESETS["hbm3_64"]

        # Read power: ~80mW/channel at 1.1V
        read_power_mw = params.read_power_mw
        assert read_power_mw == pytest.approx(80.0, rel=0.1), \
            f"Expected ~80mW, got {read_power_mw}mW"

    def test_hbm3_64_write_power(self):
        """Test HBM3 6.4 Gbps write power (~95mW/channel)"""
        params = HBM3_POWER_PRESETS["hbm3_64"]

        # Write power: ~95mW/channel at 1.1V
        write_power_mw = params.write_power_mw
        assert write_power_mw == pytest.approx(95.0, rel=0.1), \
            f"Expected ~95mW, got {write_power_mw}mW"

    def test_hbm3_64_refresh_power(self):
        """Test HBM3 6.4 Gbps refresh power (~150mW/channel)"""
        params = HBM3_POWER_PRESETS["hbm3_64"]

        # Refresh power: ~150mW/channel at 1.1V
        refresh_power_mw = params.refresh_power_mw
        assert refresh_power_mw == pytest.approx(150.0, rel=0.1), \
            f"Expected ~150mW, got {refresh_power_mw}mW"

    def test_hbm3_64_idle_power(self):
        """Test HBM3 6.4 Gbps idle power (~25mW/channel)"""
        params = HBM3_POWER_PRESETS["hbm3_64"]

        # Idle power: ~25mW/channel at 1.1V
        idle_power_mw = params.idle_power_mw
        assert idle_power_mw == pytest.approx(25.0, rel=0.1), \
            f"Expected ~25mW, got {idle_power_mw}mW"

    def test_hbm3_8g_power_scaling(self):
        """Test HBM3 8 Gbps power scales with frequency"""
        params_64 = HBM3_POWER_PRESETS["hbm3_64"]
        params_8g = HBM3_POWER_PRESETS["hbm3_8g"]

        # Higher frequency should have higher power
        assert params_8g.active_power_mw > params_64.active_power_mw
        assert params_8g.read_power_mw > params_64.read_power_mw

    def test_hbm3_96_power_scaling(self):
        """Test HBM3 9.6 Gbps power scales with frequency"""
        params_64 = HBM3_POWER_PRESETS["hbm3_64"]
        params_96 = HBM3_POWER_PRESETS["hbm3_96"]

        # Higher frequency should have higher power
        assert params_96.active_power_mw > params_64.active_power_mw
        assert params_96.read_power_mw > params_64.read_power_mw

    def test_hbm3_voltage_levels(self):
        """Test HBM3 voltage levels"""
        params = HBM3_POWER_PRESETS["hbm3_64"]

        # HBM3 VDDQ voltage
        assert params.vddq_voltage == pytest.approx(1.1, rel=0.01)
        assert params.vddq2_voltage == pytest.approx(1.1, rel=0.01)
        assert params.vpp_voltage == pytest.approx(2.5, rel=0.01)

    def test_hbm3_command_energies(self):
        """Test HBM3 command energies are defined"""
        params = HBM3_POWER_PRESETS["hbm3_64"]

        # ACT energy should be reasonable
        assert params.act_energy_pj > 0
        assert params.act_energy_pj < 300  # pJ

        # RD/WR energies should be reasonable
        assert params.rd_energy_pj > 0
        assert params.rd_energy_pj < 200
        assert params.wr_energy_pj > 0
        assert params.wr_energy_pj < 200

        # REF energy should be higher
        assert params.refab_energy_pj > params.act_energy_pj


# =============================================================================
# Test HBM4 Power Specifications
# =============================================================================

class TestHBM4Specifications:
    """Tests for HBM4 power specifications per JEDEC JESD270-4A"""

    def test_hbm4_8gbps_power(self):
        """Test HBM4 8 Gbps power values"""
        params = POWER_PRESETS["8Gbps"]

        # Active power at 1.1V
        assert params.active_power_mw == pytest.approx(385.0, rel=0.01)

        # Read power at 1.1V
        assert params.read_power_mw == pytest.approx(495.0, rel=0.01)

    def test_hbm4_12gbps_power_scaling(self):
        """Test HBM4 12 Gbps power scales with voltage"""
        params_8 = POWER_PRESETS["8Gbps"]
        params_12 = POWER_PRESETS["12Gbps"]

        # Higher voltage should have higher power
        assert params_12.vddq_voltage > params_8.vddq_voltage
        assert params_12.active_power_mw > params_8.active_power_mw

    def test_hbm4_16gbps_power_scaling(self):
        """Test HBM4 16 Gbps power scales with voltage"""
        params_8 = POWER_PRESETS["8Gbps"]
        params_16 = POWER_PRESETS["16Gbps"]

        # Higher voltage should have higher power
        assert params_16.vddq_voltage > params_8.vddq_voltage
        assert params_16.active_power_mw > params_8.active_power_mw


# =============================================================================
# Test Process Corner Modeling
# =============================================================================

class TestProcessCornerModeling:
    """Tests for process corner (SS, TT, FF) power scaling"""

    def test_ss_corner_slower_power(self):
        """Test SS corner has lower power due to higher Vt"""
        params = PowerParameters()
        params.process_corner = ProcessCorner.SS

        scale = params.get_process_scaling_factor()
        assert scale < 1.0, "SS corner should scale down power"
        assert scale == pytest.approx(0.75, rel=0.01)

    def test_tt_corner_baseline(self):
        """Test TT corner is baseline"""
        params = PowerParameters()
        params.process_corner = ProcessCorner.TT

        scale = params.get_process_scaling_factor()
        assert scale == pytest.approx(1.0, rel=0.01)

    def test_ff_corner_faster_power(self):
        """Test FF corner has higher power due to lower Vt"""
        params = PowerParameters()
        params.process_corner = ProcessCorner.FF

        scale = params.get_process_scaling_factor()
        assert scale > 1.0, "FF corner should scale up power"
        assert scale == pytest.approx(1.25, rel=0.01)

    def test_process_scaling_applied_to_power(self):
        """Test process scaling is applied to power calculation"""
        params = PowerParameters()
        params.process_corner = ProcessCorner.FF
        params.temperature_c = 45.0

        # Get effective scale
        scale = params.get_effective_power_scale()
        assert scale > 1.0

    def test_ss_vs_ff_power_difference(self):
        """Test SS and FF corners have significant power difference"""
        params_ss = PowerParameters(process_corner=ProcessCorner.SS)
        params_ff = PowerParameters(process_corner=ProcessCorner.FF)

        scale_ss = params_ss.get_process_scaling_factor()
        scale_ff = params_ff.get_process_scaling_factor()

        # FF should be significantly higher than SS
        assert scale_ff / scale_ss > 1.5


# =============================================================================
# Test Temperature-Dependent Power Scaling
# =============================================================================

class TestTemperatureScaling:
    """Tests for temperature-dependent power scaling"""

    def test_reference_temperature_no_scaling(self):
        """Test at reference temperature (45C) no scaling"""
        params = PowerParameters()
        params.temperature_c = 45.0

        scale = params.get_temperature_scaling_factor()
        assert scale == pytest.approx(1.0, rel=0.01)

    def test_high_temperature_increases_power(self):
        """Test higher temperature increases power due to leakage"""
        params = PowerParameters()
        params.temperature_c = 85.0

        scale = params.get_temperature_scaling_factor()
        assert scale > 1.0, "High temperature should increase power"

    def test_low_temperature_no_scaling(self):
        """Test low temperature doesn't add scaling"""
        params = PowerParameters()
        params.temperature_c = 25.0

        scale = params.get_temperature_scaling_factor()
        assert scale <= 1.0, "Low temperature should not increase power"

    def test_exponential_leakage_model(self):
        """Test leakage follows exponential model with temperature"""
        params = PowerParameters()

        # At 45C (reference): scale = 1.0
        params.temperature_c = 45.0
        scale_45 = params.get_temperature_scaling_factor()

        # At 55C (+10C): scale should increase ~10%
        params.temperature_c = 55.0
        scale_55 = params.get_temperature_scaling_factor()

        assert scale_55 > scale_45

    def test_combined_temperature_and_process_scaling(self):
        """Test combined temperature and process scaling"""
        params = PowerParameters()
        params.process_corner = ProcessCorner.FF
        params.temperature_c = 85.0

        combined = params.get_effective_power_scale()
        assert combined > 1.0

        # Combined should be product of individual factors
        temp_scale = params.get_temperature_scaling_factor()
        proc_scale = params.get_process_scaling_factor()
        assert combined == pytest.approx(temp_scale * proc_scale, rel=0.01)


# =============================================================================
# Test Voltage Scaling Support
# =============================================================================

class TestVoltageScaling:
    """Tests for voltage scaling support"""

    def test_power_proportional_to_voltage(self):
        """Test power scales with voltage (P = V * I)"""
        params = PowerParameters()
        params.vddq_voltage = 1.1
        params.active_power_ma = 100.0

        power_1v1 = params.active_power_mw

        # Double voltage
        params.vddq_voltage = 2.2
        power_2v2 = params.active_power_mw

        assert power_2v2 == pytest.approx(power_1v1 * 2, rel=0.01)

    def test_hbm3_voltage_vs_hbm4(self):
        """Test HBM3 and HBM4 have different voltage levels"""
        hbm3 = HBM3_POWER_PRESETS["hbm3_64"]
        hbm4 = POWER_PRESETS["8Gbps"]

        # HBM4 typically operates at higher voltage
        assert hbm4.vddq_voltage >= hbm3.vddq_voltage

    def test_voltage_dependent_power(self):
        """Test power scales with voltage (P = V * I)"""
        params_1v1 = PowerParameters(vddq_voltage=1.1)
        params_1v2 = PowerParameters(vddq_voltage=1.2)

        # Power (mW) = voltage * current, so higher voltage = higher power
        power_1v1 = params_1v1.active_power_mw
        power_1v2 = params_1v2.active_power_mw

        # At same current, power should scale with voltage
        assert power_1v2 > power_1v1


# =============================================================================
# Test Power State Machine
# =============================================================================

class TestPowerStateMachine:
    """Tests for power state machine transitions"""

    def test_initial_state_is_idle(self):
        """Test power estimator starts in idle state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        for ch in estimator.channels:
            assert ch.state == PowerState.IDLE

    def test_active_state_transition(self):
        """Test transition to active state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)

        assert estimator.channels[0].state == PowerState.ACTIVE
        assert estimator.channels[0].active_time_cycles == 100

    def test_read_state_transition(self):
        """Test transition to read state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(0, PowerState.READ, cycles=50)

        assert estimator.channels[0].state == PowerState.READ
        assert estimator.channels[0].read_time_cycles == 50

    def test_write_state_transition(self):
        """Test transition to write state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(0, PowerState.WRITE, cycles=50)

        assert estimator.channels[0].state == PowerState.WRITE
        assert estimator.channels[0].write_time_cycles == 50

    def test_refresh_state_transition(self):
        """Test transition to refresh state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(0, PowerState.REFRESH, cycles=10)

        assert estimator.channels[0].state == PowerState.REFRESH
        assert estimator.channels[0].refresh_time_cycles == 10

    def test_self_refresh_state(self):
        """Test self-refresh state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(0, PowerState.SELF_REFRESH, cycles=1000)

        assert estimator.channels[0].state == PowerState.SELF_REFRESH
        assert estimator.channels[0].self_refresh_cycles == 1000

    def test_power_down_state(self):
        """Test power-down state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(0, PowerState.POWER_DOWN, cycles=500)

        assert estimator.channels[0].state == PowerState.POWER_DOWN

    def test_state_cycle_accumulation(self):
        """Test cycle counts accumulate correctly"""
        estimator = HBM4PowerEstimator(num_channels=1)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(0, PowerState.READ, cycles=50)
        estimator.set_channel_state(0, PowerState.IDLE, cycles=200)

        ch = estimator.channels[0]
        assert ch.active_time_cycles == 100
        assert ch.read_time_cycles == 50
        assert ch.idle_time_cycles == 200


# =============================================================================
# Test Command-Based Power Calculation
# =============================================================================

class TestCommandBasedPower:
    """Tests for command-based power calculation"""

    def test_activate_command_energy(self):
        """Test ACT command energy is recorded"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.ACT)

        counts = estimator.get_command_count_breakdown()
        assert counts['act'] == 2

    def test_read_command_energy(self):
        """Test READ command energy is recorded"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.record_command(0, CommandType.RD)
        estimator.record_command(0, CommandType.RD)
        estimator.record_command(0, CommandType.RD)

        counts = estimator.get_command_count_breakdown()
        assert counts['rd'] == 3

    def test_write_command_energy(self):
        """Test WRITE command energy is recorded"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.record_command(0, CommandType.WR)

        counts = estimator.get_command_count_breakdown()
        assert counts['wr'] == 1

    def test_refresh_command_energy(self):
        """Test REF command energy is recorded"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.record_command(0, CommandType.REFAB)

        counts = estimator.get_command_count_breakdown()
        assert counts['refab'] == 1

    def test_precharge_command_energy(self):
        """Test PRE command energy is recorded"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.record_command(0, CommandType.PRE)
        estimator.record_command(0, CommandType.PREA)

        counts = estimator.get_command_count_breakdown()
        assert counts['pre'] == 1
        assert counts['prea'] == 1

    def test_all_command_types_recordable(self):
        """Test all command types can be recorded"""
        estimator = HBM4PowerEstimator(num_channels=1)

        commands = [
            CommandType.ACT, CommandType.PRE, CommandType.PREA,
            CommandType.RD, CommandType.WR, CommandType.RDA, CommandType.WRA,
            CommandType.REFAB, CommandType.REFSB, CommandType.MRW, CommandType.MRR,
        ]

        for cmd in commands:
            estimator.record_command(0, cmd)

        counts = estimator.get_command_count_breakdown()
        for cmd in commands:
            assert counts[cmd.value] == 1

    def test_command_energy_breakdown(self):
        """Test command energy breakdown"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)
        estimator.record_command(1, CommandType.WR)

        breakdown = estimator.get_command_energy_breakdown()
        assert breakdown['act'] > 0
        assert breakdown['rd'] > 0
        assert breakdown['wr'] > 0


# =============================================================================
# Test Per-Channel Power Tracking
# =============================================================================

class TestPerChannelPower:
    """Tests for per-channel power tracking"""

    def test_channel_power_tracking(self):
        """Test individual channels track power"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=100)
        estimator.set_channel_state(2, PowerState.READ, cycles=100)
        estimator.set_channel_state(3, PowerState.WRITE, cycles=100)

        # Each channel should have independent state
        assert estimator.channels[0].state == PowerState.ACTIVE
        assert estimator.channels[1].state == PowerState.IDLE
        assert estimator.channels[2].state == PowerState.READ
        assert estimator.channels[3].state == PowerState.WRITE

    def test_get_channel_power(self):
        """Test getting specific channel power"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(2, PowerState.ACTIVE, cycles=1)

        power = estimator.get_channel_power_mw(2)
        assert power > 0

    def test_get_invalid_channel_power(self):
        """Test getting power for invalid channel returns 0"""
        estimator = HBM4PowerEstimator(num_channels=4)

        power = estimator.get_channel_power_mw(-1)
        assert power == 0.0

        power = estimator.get_channel_power_mw(100)
        assert power == 0.0

    def test_set_all_channels_state(self):
        """Test setting all channels to same state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_all_channels_state(PowerState.IDLE, cycles=100)

        for ch in estimator.channels:
            assert ch.state == PowerState.IDLE
            assert ch.idle_time_cycles == 100

    def test_total_power_across_channels(self):
        """Test total power calculation across all channels"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1)

        total = estimator.get_total_power_mw()
        # 4 channels * active power (350mA * 1.1V)
        assert total == pytest.approx(1540.0, rel=0.01)


# =============================================================================
# Test Factory Functions
# =============================================================================

class TestFactoryFunctions:
    """Tests for power estimator factory functions"""

    def test_create_hbm3_power_estimator(self):
        """Test creating HBM3 power estimator"""
        estimator = create_hbm3_power_estimator(
            speed_grade="hbm3_64",
            num_channels=16,
            process_corner="TT",
            temperature_c=45.0,
        )

        assert estimator.num_channels == 16
        assert estimator.data_rate_gtps == pytest.approx(6.4, rel=0.01)
        assert estimator.params.process_corner == ProcessCorner.TT
        assert estimator.params.temperature_c == 45.0

    def test_create_power_estimator_for_hbm2(self):
        """Test creating HBM2 power estimator"""
        estimator = create_power_estimator_for_version(
            hbm_version="hbm2",
            process_corner="TT",
            temperature_c=45.0,
        )

        assert estimator.num_channels == 8
        assert estimator.data_rate_gtps == pytest.approx(1.2, rel=0.01)

    def test_create_power_estimator_for_hbm3(self):
        """Test creating HBM3 power estimator"""
        estimator = create_power_estimator_for_version(
            hbm_version="hbm3",
            speed_grade="hbm3_8g",
            process_corner="TT",
            temperature_c=45.0,
        )

        assert estimator.num_channels == 16
        assert estimator.data_rate_gtps == pytest.approx(8.0, rel=0.01)

    def test_create_power_estimator_for_hbm4(self):
        """Test creating HBM4 power estimator"""
        estimator = create_power_estimator_for_version(
            hbm_version="hbm4",
            speed_grade="16Gbps",
            process_corner="FF",
            temperature_c=85.0,
        )

        assert estimator.num_channels == 32
        assert estimator.data_rate_gtps == pytest.approx(16.0, rel=0.01)
        assert estimator.params.process_corner == ProcessCorner.FF
        assert estimator.params.temperature_c == 85.0

    def test_create_power_estimator_unknown_version(self):
        """Test creating with unknown version raises error"""
        with pytest.raises(ValueError):
            create_power_estimator_for_version(hbm_version="hbm5")

    def test_create_hbm3_power_estimator_default(self):
        """Test HBM3 defaults to 6.4 Gbps"""
        estimator = create_hbm3_power_estimator()

        assert estimator.data_rate_gtps == pytest.approx(6.4, rel=0.01)

    def test_all_presets_available(self):
        """Test all presets are available in combined presets"""
        expected = [
            "8Gbps", "12Gbps", "16Gbps",
            "hbm3_64", "hbm3_8g", "hbm3_96",
        ]
        for preset in expected:
            assert preset in ALL_POWER_PRESETS


# =============================================================================
# Test Power Report Generation
# =============================================================================

class TestPowerReport:
    """Tests for power report generation"""

    def test_report_with_hbm3_estimator(self):
        """Test report generation for HBM3 estimator"""
        estimator = create_hbm3_power_estimator()

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=100)
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)

        report = estimator.generate_report()

        assert report.num_channels == 16
        assert report.total_power_mw > 0
        assert report.command_counts['act'] == 1
        assert report.command_counts['rd'] == 1

    def test_report_text_format_hbm3(self):
        """Test text report format for HBM3"""
        estimator = create_hbm3_power_estimator()
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)

        report = estimator.generate_report()
        text = report.to_text()

        assert "HBM4 POWER CONSUMPTION REPORT" in text  # Uses same report class
        assert "POWER SUMMARY" in text
        assert "COMMAND STATISTICS" in text

    def test_report_dict_format(self):
        """Test dict report format"""
        estimator = create_hbm3_power_estimator()
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)

        report = estimator.generate_report()
        d = report.to_dict()

        assert 'power' in d
        assert 'energy' in d
        assert 'commands' in d
        assert 'thermal' in d
        assert 'configuration' in d

    def test_power_efficiency_calculation(self):
        """Test power efficiency calculation"""
        estimator = create_hbm3_power_estimator()

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=100)
        estimator.tick(cycles=200)

        eff = estimator.calculate_power_efficiency(
            achieved_bandwidth_gbs=500.0,
            peak_bandwidth_gbs=1000.0,
        )

        assert eff > 0


# =============================================================================
# Test Integration with Thermal Model
# =============================================================================

class TestThermalIntegration:
    """Tests for power-thermal integration"""

    def test_power_estimator_thermal_estimation(self):
        """Test power estimator provides thermal estimation"""
        estimator = create_hbm3_power_estimator()

        estimator.set_all_channels_state(PowerState.IDLE, cycles=1000)

        thermal = estimator.estimate_thermal(ambient_temp_c=45.0)

        assert 'ambient_temp_c' in thermal
        assert 'junction_temp_c' in thermal
        assert 'average_power_w' in thermal
        assert 'theta_ja' in thermal

    def test_power_efficiency_metric(self):
        """Test power efficiency metric calculation"""
        estimator = create_hbm3_power_estimator()

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.tick(cycles=100)

        # Calculate bandwidth efficiency
        active_total = estimator.active_cycles + estimator.read_cycles + estimator.write_cycles
        eff = estimator.get_bandwidth_efficiency(active_total, estimator.current_cycle)

        assert 0 <= eff <= 1.0


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge case tests for power estimator"""

    def test_zero_cycles_power(self):
        """Test power with zero cycles"""
        estimator = HBM4PowerEstimator(num_channels=1)

        avg = estimator.get_average_power_mw()
        assert avg == 0.0

    def test_multiple_state_changes(self):
        """Test multiple rapid state changes"""
        estimator = HBM4PowerEstimator(num_channels=1)

        states = [
            (PowerState.ACTIVE, 10),
            (PowerState.READ, 20),
            (PowerState.WRITE, 30),
            (PowerState.IDLE, 40),
            (PowerState.ACTIVE, 50),
        ]

        for state, cycles in states:
            estimator.set_channel_state(0, state, cycles=cycles)

        ch = estimator.channels[0]
        assert ch.active_time_cycles == 60  # 10 + 50
        assert ch.read_time_cycles == 20
        assert ch.write_time_cycles == 30
        assert ch.idle_time_cycles == 40

    def test_power_calculation_consistency(self):
        """Test power calculation is consistent"""
        estimator = HBM4PowerEstimator(num_channels=1)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1)
        power1 = estimator.get_total_power_mw()

        estimator.reset()
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1)
        power2 = estimator.get_total_power_mw()

        assert power1 == power2

    def test_command_count_consistency(self):
        """Test command counts are consistent"""
        estimator = HBM4PowerEstimator(num_channels=1)

        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)

        counts = estimator.get_command_count_breakdown()
        energy = estimator.get_command_energy_breakdown()

        # Count * energy per command should equal total energy
        act_energy_per_cmd = estimator.params.get_command_energy_pj(CommandType.ACT)
        assert counts['act'] * act_energy_per_cmd == energy['act']

    def test_reset_clears_all_state(self):
        """Test reset clears all state"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=50)
        estimator.record_command(0, CommandType.ACT)

        estimator.reset()

        assert estimator.current_cycle == 0
        assert estimator.channels[0].active_time_cycles == 0
        assert estimator.channels[1].idle_time_cycles == 0
        assert estimator.total_command_energy.act_count == 0


# =============================================================================
# Test Performance Characteristics
# =============================================================================

class TestPerformance:
    """Tests for power estimator performance"""

    def test_large_channel_count(self):
        """Test with maximum channel count"""
        estimator = HBM4PowerEstimator(num_channels=32)

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=100)

        total = estimator.get_total_power_mw()
        assert total > 0

        report = estimator.generate_report()
        assert len(report.channel_powers) == 32

    def test_high_cycle_count(self):
        """Test with large number of cycles"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=100000)

        avg = estimator.get_average_power_mw()
        assert avg > 0

    def test_many_commands(self):
        """Test with many commands"""
        estimator = HBM4PowerEstimator(num_channels=1)

        for _ in range(10000):
            estimator.record_command(0, CommandType.ACT)
            estimator.record_command(0, CommandType.RD)

        counts = estimator.get_command_count_breakdown()
        assert counts['act'] == 10000
        assert counts['rd'] == 10000


# =============================================================================
# Test Default Power Estimator
# =============================================================================

class TestDefaultEstimator:
    """Tests for default power estimator singleton"""

    def test_default_estimator_exists(self):
        """Test default estimator is created"""
        assert DEFAULT_POWER_ESTIMATOR is not None
        assert isinstance(DEFAULT_POWER_ESTIMATOR, HBM4PowerEstimator)

    def test_default_estimator_channels(self):
        """Test default estimator has 32 channels (HBM4)"""
        assert DEFAULT_POWER_ESTIMATOR.num_channels == 32


if __name__ == '__main__':
    pytest.main([__file__, '-v'])