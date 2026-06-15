"""
Unit Tests for HBM4 Power Estimator

Tests power consumption estimation based on:
- Active/Idle states
- Read/Write operations
- Refresh operations
- Temperature and process corners

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

    def test_get_summary(self):
        """Test getting power summary"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=100)

        summary = estimator.get_summary()

        assert 'num_channels' in summary
        assert 'current_cycle' in summary
        assert 'total_power_mw' in summary
        assert 'average_power_mw' in summary
        assert 'peak_power_mw' in summary
        assert 'total_energy_pj' in summary
        assert 'energy_breakdown_pj' in summary
        assert 'efficiency' in summary
        assert 'thermal' in summary

    def test_reset(self):
        """Test resetting power counters"""
        estimator = HBM4PowerEstimator(num_channels=2)

        estimator.set_channel_state(0, PowerState.ACTIVE, cycles=100)
        estimator.set_channel_state(1, PowerState.IDLE, cycles=50)

        estimator.reset()

        assert estimator.current_cycle == 0
        assert estimator.peak_power_mw == 0.0
        assert estimator.channels[0].active_time_cycles == 0
        assert estimator.channels[1].idle_time_cycles == 0

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


class TestCreatePowerEstimator:
    """Tests for power estimator factory function"""

    def test_create_8gbps(self):
        """Test creating 8 Gbps estimator"""
        estimator = create_power_estimator(speed_grade='8Gbps', num_channels=16)

        assert estimator.num_channels == 16
        assert estimator.params.vddq_voltage == 1.1

    def test_create_12gbps(self):
        """Test creating 12 Gbps estimator"""
        estimator = create_power_estimator(speed_grade='12Gbps', num_channels=16)

        assert estimator.num_channels == 16
        assert estimator.params.vddq_voltage == 1.15

    def test_create_16gbps(self):
        """Test creating 16 Gbps estimator"""
        estimator = create_power_estimator(speed_grade='16Gbps', num_channels=16)

        assert estimator.num_channels == 16
        assert estimator.params.vddq_voltage == 1.2

    def test_create_unknown_preset(self):
        """Test creating with unknown preset falls back to 8Gbps"""
        estimator = create_power_estimator(speed_grade='unknown', num_channels=8)

        assert estimator.params.vddq_voltage == 1.1  # Fallback to 8Gbps


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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
