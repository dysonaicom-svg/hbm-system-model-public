"""
Unit Tests for HBM4 Power Estimator

Tests power consumption estimation based on:
- Active/Idle states
- Read/Write operations
- Refresh operations
- Temperature and process corners
- Per-command energy tracking
- Dynamic power calculation
- Power report generation

Reference:
- JEDEC JESD270-4A HBM4 specification
- Synopsys DesignWare HBM4 Power Analysis
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
    create_power_estimator,
    create_power_estimator_with_config,
    CommandType,
    CommandEnergy,
    ProcessCorner,
    PowerReport,
)


class TestPowerState:
    """Tests for PowerState enumeration"""

    def test_all_power_states_defined(self):
        """Test all power states are defined"""
        expected_states = [
            'ACTIVE', 'READ', 'WRITE', 'REFRESH',
            'IDLE', 'SELF_REFRESH', 'POWER_DOWN'
        ]
        actual_states = [s.name for s in PowerState]
        for state in expected_states:
            assert state in actual_states

    def test_power_state_values(self):
        """Test power state string values"""
        assert PowerState.ACTIVE.value == 'active'
        assert PowerState.IDLE.value == 'idle'
        assert PowerState.SELF_REFRESH.value == 'self_refresh'


class TestProcessCorner:
    """Tests for ProcessCorner enumeration"""

    def test_all_corners_defined(self):
        """Test all process corners are defined"""
        expected = ['SS', 'TT', 'FF']
        actual = [c.name for c in ProcessCorner]
        for corner in expected:
            assert corner in actual


class TestCommandType:
    """Tests for CommandType enumeration"""

    def test_all_commands_defined(self):
        """Test all command types are defined"""
        expected = [
            'ACT', 'PRE', 'PREA', 'RD', 'WR', 'RDA', 'WRA',
            'REFAB', 'REFSB', 'RFMAB', 'RFMSB', 'MRW', 'MRR',
            'PDN_ENTER', 'PDN_EXIT', 'SREF_ENTER', 'SREF_EXIT'
        ]
        actual = [c.name for c in CommandType]
        for cmd in expected:
            assert cmd in actual


class TestPowerParameters:
    """Tests for PowerParameters dataclass"""

    def test_default_parameters(self):
        """Test default power parameters"""
        params = PowerParameters()

        assert params.active_power_ma == 350.0
        assert params.read_power_ma == 450.0
        assert params.write_power_ma == 420.0
        assert params.idle_power_ma == 50.0
        assert params.self_refresh_power_ma == 8.0
        assert params.power_down_power_ma == 5.0
        assert params.vddq_voltage == 1.1
        assert params.vddq2_voltage == 0.95
        assert params.vpp_voltage == 2.5

    def test_power_conversion_properties(self):
        """Test power conversion to mW"""
        params = PowerParameters()

        assert params.active_power_mw == pytest.approx(385.0, rel=0.01)  # 350 * 1.1
        assert params.read_power_mw == pytest.approx(495.0, rel=0.01)   # 450 * 1.1
        assert params.write_power_mw == pytest.approx(462.0, rel=0.01)   # 420 * 1.1
        assert params.idle_power_mw == pytest.approx(55.0, rel=0.01)    # 50 * 1.1

    def test_custom_parameters(self):
        """Test custom power parameters"""
        params = PowerParameters(
            active_power_ma=400.0,
            read_power_ma=500.0,
            vddq_voltage=1.2,
        )

        assert params.active_power_ma == 400.0
        assert params.read_power_ma == 500.0
        assert params.vddq_voltage == 1.2

    def test_process_scaling_factor(self):
        """Test process corner scaling factors"""
        params = PowerParameters()

        # TT should be 1.0
        params.process_corner = ProcessCorner.TT
        assert params.get_process_scaling_factor() == pytest.approx(1.0, rel=0.01)

        # FF should be > 1.0
        params.process_corner = ProcessCorner.FF
        assert params.get_process_scaling_factor() > 1.0

        # SS should be < 1.0
        params.process_corner = ProcessCorner.SS
        assert params.get_process_scaling_factor() < 1.0

    def test_temperature_scaling_factor(self):
        """Test temperature scaling factors"""
        params = PowerParameters()

        # At reference temperature, should be 1.0
        params.temperature_c = 45.0
        assert params.get_temperature_scaling_factor() == pytest.approx(1.0, rel=0.01)

        # Above reference, should increase
        params.temperature_c = 85.0
        assert params.get_temperature_scaling_factor() > 1.0

    def test_effective_power_scale(self):
        """Test combined power scaling"""
        params = PowerParameters()
        params.process_corner = ProcessCorner.TT
        params.temperature_c = 45.0

        scale = params.get_effective_power_scale()
        assert scale == pytest.approx(1.0, rel=0.01)

    def test_command_energy_pj(self):
        """Test command energy retrieval"""
        params = PowerParameters()

        # Test various command energies
        assert params.get_command_energy_pj(CommandType.ACT) == params.act_energy_pj
        assert params.get_command_energy_pj(CommandType.RD) == params.rd_energy_pj
        assert params.get_command_energy_pj(CommandType.WR) == params.wr_energy_pj
        assert params.get_command_energy_pj(CommandType.REFAB) == params.refab_energy_pj


class TestCommandEnergy:
    """Tests for CommandEnergy dataclass"""

    def test_command_energy_creation(self):
        """Test command energy tracker creation"""
        ce = CommandEnergy()

        assert ce.act_count == 0
        assert ce.rd_count == 0
        assert ce.total_commands == 0
        assert ce.total_energy_pj == 0.0

    def test_total_commands(self):
        """Test total command counting"""
        ce = CommandEnergy()
        ce.act_count = 10
        ce.rd_count = 20
        ce.wr_count = 5

        assert ce.total_commands == 35

    def test_energy_breakdown(self):
        """Test energy breakdown generation"""
        ce = CommandEnergy()
        ce.act_count = 10
        ce.total_act_energy_pj = 3200.0  # 10 * 320 pJ

        breakdown = ce.get_energy_breakdown()
        assert 'act' in breakdown
        assert breakdown['act'] == 3200.0

    def test_count_breakdown(self):
        """Test count breakdown generation"""
        ce = CommandEnergy()
        ce.rd_count = 100
        ce.wr_count = 50

        breakdown = ce.get_count_breakdown()
        assert breakdown['rd'] == 100
        assert breakdown['wr'] == 50


class TestChannelPower:
    """Tests for ChannelPower dataclass"""

    def test_channel_power_creation(self):
        """Test channel power tracker creation"""
        channel = ChannelPower(channel_id=0)

        assert channel.channel_id == 0
        assert channel.state == PowerState.IDLE
        assert channel.total_energy_pj == 0.0

    def test_channel_power_update_idle(self):
        """Test updating energy for idle state"""
        channel = ChannelPower(channel_id=0)

        channel.update_energy(cycles=100, state=PowerState.IDLE)

        assert channel.idle_time_cycles == 100
        assert channel.total_energy_pj > 0.0

    def test_channel_power_update_active(self):
        """Test updating energy for active state"""
        channel = ChannelPower(channel_id=0)

        channel.update_energy(cycles=50, state=PowerState.ACTIVE)

        assert channel.active_time_cycles == 50

    def test_channel_power_update_read(self):
        """Test updating energy for read state"""
        channel = ChannelPower(channel_id=0)

        channel.update_energy(cycles=30, state=PowerState.READ)

        assert channel.read_time_cycles == 30

    def test_channel_power_update_write(self):
        """Test updating energy for write state"""
        channel = ChannelPower(channel_id=0)

        channel.update_energy(cycles=30, state=PowerState.WRITE)

        assert channel.write_time_cycles == 30

    def test_channel_power_update_refresh(self):
        """Test updating energy for refresh state"""
        channel = ChannelPower(channel_id=0)

        channel.update_energy(cycles=5, state=PowerState.REFRESH)

        assert channel.refresh_time_cycles == 5

    def test_channel_power_update_self_refresh(self):
        """Test updating energy for self-refresh state"""
        channel = ChannelPower(channel_id=0)

        channel.update_energy(cycles=1000, state=PowerState.SELF_REFRESH)

        assert channel.self_refresh_cycles == 1000

    def test_get_average_power(self):
        """Test average power calculation"""
        channel = ChannelPower(channel_id=0)

        channel.update_energy(cycles=100, state=PowerState.ACTIVE)
        channel.update_energy(cycles=100, state=PowerState.IDLE)

        avg_power = channel.get_average_power_mw(total_cycles=200)
        assert avg_power > 0.0

    def test_get_average_power_zero_cycles(self):
        """Test average power with zero cycles returns zero"""
        channel = ChannelPower(channel_id=0)

        avg_power = channel.get_average_power_mw(total_cycles=0)
        assert avg_power == 0.0

    def test_record_command(self):
        """Test command recording"""
        channel = ChannelPower(channel_id=0)
        params = PowerParameters()

        channel.record_command(CommandType.ACT, params)
        channel.record_command(CommandType.RD, params)

        assert channel.command_energy.act_count == 1
        assert channel.command_energy.rd_count == 1
        assert channel.command_energy.total_act_energy_pj > 0
        assert channel.command_energy.total_rd_energy_pj > 0

    def test_get_peak_power(self):
        """Test peak power from history"""
        channel = ChannelPower(channel_id=0)

        # Update with different states
        channel.update_energy(10, PowerState.IDLE)
        channel.update_energy(10, PowerState.ACTIVE)
        channel.update_energy(10, PowerState.READ)

        peak = channel.get_peak_power_mw()
        assert peak > 0.0

    def test_get_power_stats(self):
        """Test power statistics"""
        channel = ChannelPower(channel_id=0)

        channel.update_energy(100, PowerState.ACTIVE)

        stats = channel.get_power_stats()
        assert 'average_mw' in stats
        assert 'peak_mw' in stats
        assert 'min_mw' in stats
        assert 'rms_mw' in stats


class TestHBM4PowerEstimator:
    """Tests for HBM4PowerEstimator"""

    def test_estimator_creation(self):
        """Test power estimator creation"""
        estimator = HBM4PowerEstimator(num_channels=8)

        assert estimator.num_channels == 8
        assert len(estimator.channels) == 8
        assert estimator.current_cycle == 0
        assert estimator.peak_power_mw == 0.0

    def test_estimator_default_channels(self):
        """Test default channel count"""
        estimator = HBM4PowerEstimator()
        assert estimator.num_channels == 32

    def test_tick(self):
        """Test tick increments cycle counter"""
        estimator = HBM4PowerEstimator(num_channels=2)

        initial_cycle = estimator.current_cycle
        estimator.tick()
        assert estimator.current_cycle == initial_cycle + 1

        estimator.tick(cycles=10)
        assert estimator.current_cycle == initial_cycle + 11

    def test_set_channel_state(self):
        """Test setting channel state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(channel_id=2, state=PowerState.ACTIVE, cycles=100)

        assert estimator.channels[2].state == PowerState.ACTIVE
        assert estimator.channels[2].active_time_cycles == 100

    def test_set_channel_state_invalid_id(self):
        """Test setting state for invalid channel ID"""
        estimator = HBM4PowerEstimator(num_channels=4)

        # Should not raise, just ignore
        estimator.set_channel_state(channel_id=10, state=PowerState.ACTIVE)
        estimator.set_channel_state(channel_id=-1, state=PowerState.ACTIVE)

    def test_set_all_channels_state(self):
        """Test setting all channels to same state"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_all_channels_state(state=PowerState.IDLE, cycles=50)

        for ch in estimator.channels:
            assert ch.state == PowerState.IDLE
            assert ch.idle_time_cycles == 50

    def test_get_total_power(self):
        """Test getting total power across all channels"""
        estimator = HBM4PowerEstimator(num_channels=4)

        # Set all to active
        estimator.set_all_channels_state(state=PowerState.ACTIVE, cycles=1)

        total = estimator.get_total_power_mw()
        # 4 channels * 350mA * 1.1V = 1540 mW
        assert total == pytest.approx(1540.0, rel=0.01)

    def test_get_average_power(self):
        """Test getting average power"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=100)
        estimator.tick(cycles=200)  # Advance cycle counter for average calculation

        avg = estimator.get_average_power_mw()
        assert avg > 0.0

    def test_get_channel_power(self):
        """Test getting specific channel power"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(2, PowerState.ACTIVE, cycles=1)

        power = estimator.get_channel_power_mw(2)
        assert power == pytest.approx(385.0, rel=0.01)  # 350 * 1.1

    def test_get_channel_power_invalid(self):
        """Test getting power for invalid channel"""
        estimator = HBM4PowerEstimator(num_channels=4)

        power = estimator.get_channel_power_mw(10)
        assert power == 0.0

        power = estimator.get_channel_power_mw(-1)
        assert power == 0.0

    def test_energy_breakdown(self):
        """Test energy breakdown by state"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(0, PowerState.READ, cycles=50)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=150)

        breakdown = estimator.get_energy_breakdown_pj()

        assert 'active' in breakdown
        assert 'read' in breakdown
        assert 'write' in breakdown
        assert 'idle' in breakdown
        assert breakdown['active'] > 0.0
        assert breakdown['read'] > 0.0
        assert breakdown['idle'] > 0.0

    def test_command_energy_breakdown(self):
        """Test command energy breakdown"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)
        estimator.record_command(1, CommandType.WR)

        breakdown = estimator.get_command_energy_breakdown()
        assert 'act' in breakdown
        assert 'rd' in breakdown
        assert 'wr' in breakdown
        assert breakdown['act'] > 0
        assert breakdown['rd'] > 0
        assert breakdown['wr'] > 0

    def test_command_count_breakdown(self):
        """Test command count breakdown"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(1, CommandType.RD)

        counts = estimator.get_command_count_breakdown()
        assert counts['act'] == 2
        assert counts['rd'] == 1

    def test_bandwidth_efficiency(self):
        """Test bandwidth efficiency calculation"""
        estimator = HBM4PowerEstimator(num_channels=1)

        efficiency = estimator.get_bandwidth_efficiency(active_cycles=100, total_cycles=200)
        assert efficiency == 0.5

    def test_bandwidth_efficiency_zero_total(self):
        """Test efficiency with zero total returns zero"""
        estimator = HBM4PowerEstimator(num_channels=1)

        efficiency = estimator.get_bandwidth_efficiency(active_cycles=100, total_cycles=0)
        assert efficiency == 0.0

    def test_thermal_estimation(self):
        """Test thermal estimation"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_all_channels_state(PowerState.IDLE, cycles=1000)

        thermal = estimator.estimate_thermal(ambient_temp_c=45.0)

        assert 'ambient_temp_c' in thermal
        assert 'junction_temp_c' in thermal
        assert 'average_power_w' in thermal
        assert 'theta_ja' in thermal
        assert 'peak_power_w' in thermal
        assert thermal['ambient_temp_c'] == 45.0

    def test_calculate_dynamic_power(self):
        """Test dynamic power calculation"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_all_channels_state(PowerState.ACTIVE, cycles=1)

        dynamic = estimator.calculate_dynamic_power(activity_factor=0.3)
        assert dynamic > 0.0
        assert dynamic < estimator.get_total_power_mw()

    def test_calculate_power_efficiency(self):
        """Test power efficiency calculation"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=100)
        estimator.tick(cycles=200)  # Advance cycle counter for average calculation

        # GB/s per Watt
        eff = estimator.calculate_power_efficiency(
            achieved_bandwidth_gbs=500.0,
            peak_bandwidth_gbs=1000.0,
        )
        assert eff > 0.0

    def test_generate_report(self):
        """Test power report generation"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=100)
        estimator.tick(cycles=200)  # Advance cycle counter for average calculation
        estimator.record_command(0, CommandType.ACT)
        estimator.record_command(0, CommandType.RD)

        report = estimator.generate_report()

        assert isinstance(report, PowerReport)
        assert report.total_power_mw > 0.0
        assert report.average_power_mw > 0.0  # Now > 0 since we ticked
        assert report.num_channels == 2
        assert report.command_counts['act'] == 1
        assert report.command_counts['rd'] == 1

    def test_report_to_text(self):
        """Test text report generation"""
        estimator = HBM4PowerEstimator(num_channels=1)
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=10)

        report = estimator.generate_report()
        text = report.to_text()

        assert 'HBM4 POWER CONSUMPTION REPORT' in text
        assert 'POWER SUMMARY' in text
        assert 'ENERGY SUMMARY' in text
        assert 'COMMAND STATISTICS' in text

    def test_report_to_dict(self):
        """Test dictionary conversion"""
        estimator = HBM4PowerEstimator(num_channels=1)
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=10)

        report = estimator.generate_report()
        d = report.to_dict()

        assert 'power' in d
        assert 'energy' in d
        assert 'commands' in d
        assert 'thermal' in d

    def test_get_summary(self):
        """Test getting power summary"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=100)
        estimator.record_command(0, CommandType.ACT)

        summary = estimator.get_summary()

        assert 'num_channels' in summary
        assert 'current_cycle' in summary
        assert 'total_power_mw' in summary
        assert 'average_power_mw' in summary
        assert 'peak_power_mw' in summary
        assert 'total_energy_pj' in summary
        assert 'energy_breakdown_pj' in summary
        assert 'command_energy_pj' in summary
        assert 'command_counts' in summary
        assert 'efficiency' in summary
        assert 'thermal' in summary
        assert 'process_scaling' in summary
        assert 'temperature_scaling' in summary

    def test_reset(self):
        """Test resetting power counters"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=50)
        estimator.record_command(0, CommandType.ACT)

        estimator.reset()

        assert estimator.current_cycle == 0
        assert estimator.peak_power_mw == 0.0
        assert estimator.channels[0].active_time_cycles == 0
        assert estimator.channels[1].idle_time_cycles == 0
        assert estimator.total_command_energy.act_count == 0

    def test_refresh_interval(self):
        """Test refresh interval tracking"""
        estimator = HBM4PowerEstimator(num_channels=2)

        # Default refresh interval is 62400 cycles
        assert estimator.refresh_interval_cycles == 62400

        # Tick through refresh interval
        for _ in range(62400):
            estimator.tick()

        # After refresh, cycles_since_refresh should be reset
        assert estimator.cycles_since_refresh == 0

    def test_peak_power_tracking(self):
        """Test peak power tracking"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.IDLE, cycles=1)
        initial_peak = estimator.peak_power_mw

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1)
        assert estimator.peak_power_mw > initial_peak

    def test_activity_tracking(self):
        """Test activity cycle tracking"""
        estimator = HBM4PowerEstimator(num_channels=1)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(0, PowerState.READ, cycles=50)
        estimator.set_channel_state(0, PowerState.WRITE, cycles=25)

        assert estimator.active_cycles == 100
        assert estimator.read_cycles == 50
        assert estimator.write_cycles == 25

    def test_data_rate_tck(self):
        """Test tCK calculation from data rate"""
        estimator = HBM4PowerEstimator(data_rate_gtps=8.0)
        assert estimator._get_tCK_ps() == pytest.approx(125.0, rel=0.01)

        estimator = HBM4PowerEstimator(data_rate_gtps=16.0)
        assert estimator._get_tCK_ps() == pytest.approx(62.5, rel=0.01)

    def test_repr(self):
        """Test string representation"""
        estimator = HBM4PowerEstimator(num_channels=8)

        repr_str = repr(estimator)
        assert 'HBM4PowerEstimator' in repr_str
        assert '8' in repr_str


class TestPowerPresets:
    """Tests for power presets"""

    def test_all_presets_defined(self):
        """Test all speed grade presets are defined"""
        assert '8Gbps' in POWER_PRESETS
        assert '12Gbps' in POWER_PRESETS
        assert '16Gbps' in POWER_PRESETS

    def test_8gbps_preset(self):
        """Test 8 Gbps preset"""
        params = POWER_PRESETS['8Gbps']

        assert params.vddq_voltage == 1.1
        assert params.active_power_ma == 350.0

    def test_12gbps_preset(self):
        """Test 12 Gbps preset"""
        params = POWER_PRESETS['12Gbps']

        assert params.vddq_voltage == 1.15
        assert params.active_power_ma == 420.0

    def test_16gbps_preset(self):
        """Test 16 Gbps preset"""
        params = POWER_PRESETS['16Gbps']

        assert params.vddq_voltage == 1.2
        assert params.active_power_ma == 500.0

    def test_energy_scaling_with_voltage(self):
        """Test energy scales with voltage"""
        params_8 = POWER_PRESETS['8Gbps']
        params_16 = POWER_PRESETS['16Gbps']

        # Higher voltage should have higher energy
        assert params_16.act_energy_pj > params_8.act_energy_pj
        assert params_16.rd_energy_pj > params_8.rd_energy_pj


class TestCreatePowerEstimator:
    """Tests for power estimator factory function"""

    def test_create_8gbps(self):
        """Test creating 8 Gbps estimator"""
        estimator = create_power_estimator(speed_grade='8Gbps', num_channels=16)

        assert estimator.num_channels == 16
        assert estimator.params.vddq_voltage == 1.1
        assert estimator.data_rate_gtps == 8.0

    def test_create_12gbps(self):
        """Test creating 12 Gbps estimator"""
        estimator = create_power_estimator(speed_grade='12Gbps', num_channels=16)

        assert estimator.num_channels == 16
        assert estimator.params.vddq_voltage == 1.15
        assert estimator.data_rate_gtps == 12.0

    def test_create_16gbps(self):
        """Test creating 16 Gbps estimator"""
        estimator = create_power_estimator(speed_grade='16Gbps', num_channels=16)

        assert estimator.num_channels == 16
        assert estimator.params.vddq_voltage == 1.2
        assert estimator.data_rate_gtps == 16.0

    def test_create_unknown_preset(self):
        """Test creating with unknown preset falls back to 8Gbps"""
        estimator = create_power_estimator(speed_grade='unknown', num_channels=8)

        assert estimator.params.vddq_voltage == 1.1  # Fallback to 8Gbps


class TestCreatePowerEstimatorWithConfig:
    """Tests for power estimator with custom config"""

    def test_create_with_ss_corner(self):
        """Test creating with slow-slow corner"""
        estimator = create_power_estimator_with_config(
            speed_grade='8Gbps',
            process_corner='SS',
            temperature_c=45.0,
        )

        assert estimator.params.process_corner == ProcessCorner.SS

    def test_create_with_ff_corner(self):
        """Test creating with fast-fast corner"""
        estimator = create_power_estimator_with_config(
            speed_grade='16Gbps',
            process_corner='FF',
            temperature_c=85.0,
        )

        assert estimator.params.process_corner == ProcessCorner.FF

    def test_create_with_temperature(self):
        """Test creating with custom temperature"""
        estimator = create_power_estimator_with_config(
            speed_grade='12Gbps',
            temperature_c=75.0,
        )

        assert estimator.params.temperature_c == 75.0


class TestDefaultEstimator:
    """Tests for default power estimator singleton"""

    def test_default_estimator_exists(self):
        """Test default estimator is created"""
        assert DEFAULT_POWER_ESTIMATOR is not None
        assert isinstance(DEFAULT_POWER_ESTIMATOR, HBM4PowerEstimator)

    def test_default_estimator_channels(self):
        """Test default estimator has 32 channels"""
        assert DEFAULT_POWER_ESTIMATOR.num_channels == 32


class TestPowerEstimatorEdgeCases:
    """Edge case tests for power estimator"""

    def test_multiple_state_changes(self):
        """Test multiple state changes on same channel"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=10)
        estimator.set_channel_state(0, PowerState.READ, cycles=20)
        estimator.set_channel_state(0, PowerState.IDLE, cycles=30)

        ch = estimator.channels[0]
        assert ch.active_time_cycles == 10
        assert ch.read_time_cycles == 20
        assert ch.idle_time_cycles == 30

    def test_parallel_channels(self):
        """Test parallel channel operation"""
        estimator = HBM4PowerEstimator(num_channels=4)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.READ, cycles=100)
        estimator.set_channel_state(2, PowerState.WRITE, cycles=100)
        estimator.set_channel_state(3, PowerState.IDLE, cycles=100)

        # All channels should have independent state
        assert estimator.channels[0].state == PowerState.ACTIVE
        assert estimator.channels[1].state == PowerState.READ
        assert estimator.channels[2].state == PowerState.WRITE
        assert estimator.channels[3].state == PowerState.IDLE

    def test_power_calculation_consistency(self):
        """Test power calculation is consistent"""
        estimator = HBM4PowerEstimator(num_channels=1)

        # Set active
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1)
        power1 = estimator.get_total_power_mw()

        # Reset and set again
        estimator.reset()
        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=1)
        power2 = estimator.get_total_power_mw()

        assert power1 == power2

    def test_all_command_types_recorded(self):
        """Test all command types can be recorded"""
        estimator = HBM4PowerEstimator(num_channels=1)

        commands = [
            CommandType.ACT, CommandType.PRE, CommandType.RD, CommandType.WR,
            CommandType.REFAB, CommandType.REFSB, CommandType.MRW,
        ]

        for cmd in commands:
            estimator.record_command(0, cmd)

        counts = estimator.get_command_count_breakdown()
        for cmd in commands:
            assert counts[cmd.value] == 1


class TestPowerReport:
    """Tests for PowerReport"""

    def test_report_creation(self):
        """Test report creation"""
        report = PowerReport()
        assert report.num_channels == 32

    def test_report_text_format(self):
        """Test report text formatting"""
        report = PowerReport()
        report.timestamp = "2024-01-01 12:00:00"
        report.total_power_mw = 1000.0
        report.average_power_mw = 800.0
        report.peak_power_mw = 1200.0
        report.command_counts = {"act": 100, "rd": 50}

        text = report.to_text()
        assert "HBM4 POWER CONSUMPTION REPORT" in text
        assert "1000.00" in text

    def test_report_dict_format(self):
        """Test report dict conversion"""
        report = PowerReport()
        report.num_channels = 16

        d = report.to_dict()
        assert d['configuration']['num_channels'] == 16


if __name__ == '__main__':
    pytest.main([__file__, '-v'])