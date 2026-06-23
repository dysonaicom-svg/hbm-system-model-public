"""
Tests for HBM4 Power Estimator

Tests cover:
- Basic power calculation
- Per-command energy
- PHY power
- Power-down modes
- Per-channel tracking
"""

import pytest
from model.hbm4.power.power_estimator import (
    HBM4PowerEstimator,
    PowerDownMode,
    PowerBreakdown,
    ChannelPower,
    CommandEnergy,
    PHYPower,
    ControllerPower,
    ECCPower,
    ClockingPower,
    PowerDownPower,
    create_power_estimator,
)
from model.dram.hbm4_spec import HBM4Spec


class TestBasicPowerCalculation:
    """Test basic power calculation functionality"""

    def test_estimator_creation(self):
        """Test power estimator can be created"""
        estimator = HBM4PowerEstimator()
        assert estimator is not None
        assert estimator.spec is not None
        assert estimator.spec.channels == 32

    def test_static_power_calculation(self):
        """Test static power calculation"""
        estimator = HBM4PowerEstimator()
        static_power = estimator.calculate_static_power()
        assert static_power > 0
        assert isinstance(static_power, float)

    def test_dynamic_power_calculation(self):
        """Test dynamic power calculation with activity factor"""
        estimator = HBM4PowerEstimator()
        dynamic_power = estimator.calculate_dynamic_power(activity_factor=0.3)
        assert dynamic_power >= 0

    def test_total_power_calculation(self):
        """Test total power calculation"""
        estimator = HBM4PowerEstimator()
        total_power = estimator.calculate_total_power(activity_factor=0.3)
        assert total_power > 0
        # Total should equal static + dynamic
        static = estimator.calculate_static_power()
        dynamic = estimator.calculate_dynamic_power(activity_factor=0.3)
        assert abs(total_power - (static + dynamic)) < 0.001

    def test_power_breakdown(self):
        """Test power breakdown structure"""
        estimator = HBM4PowerEstimator()
        breakdown = estimator.get_power_breakdown()
        assert isinstance(breakdown, PowerBreakdown)
        assert breakdown.phy_power is not None
        assert breakdown.controller_power is not None
        assert breakdown.ecc_power is not None
        assert breakdown.clocking_power is not None

    def test_custom_spec(self):
        """Test power estimator with custom spec"""
        custom_spec = HBM4Spec(channels=16)
        estimator = HBM4PowerEstimator(spec=custom_spec)
        assert estimator.spec.channels == 16
        assert estimator.calculate_stack_power(num_channels=16) > 0


class TestPerCommandEnergy:
    """Test per-command energy calculations"""

    def test_act_energy(self):
        """Test ACT command energy"""
        estimator = HBM4PowerEstimator()
        act_energy = estimator.get_command_energy('ACT')
        assert act_energy > 0
        # ACT should be highest energy command
        pre_energy = estimator.get_command_energy('PRE')
        assert act_energy > pre_energy

    def test_pre_energy(self):
        """Test PRE command energy"""
        estimator = HBM4PowerEstimator()
        pre_energy = estimator.get_command_energy('PRE')
        assert pre_energy > 0

    def test_rd_wr_energy(self):
        """Test RD/WR command energy"""
        estimator = HBM4PowerEstimator()
        rd_energy = estimator.get_command_energy('RD')
        wr_energy = estimator.get_command_energy('WR')
        assert rd_energy > 0
        assert wr_energy > 0
        # Write typically uses more energy than read
        assert wr_energy >= rd_energy

    def test_refresh_energy(self):
        """Test refresh command energy"""
        estimator = HBM4PowerEstimator()
        refab_energy = estimator.get_command_energy('REFab')
        refsb_energy = estimator.get_command_energy('REFsb')
        assert refab_energy > 0
        assert refsb_energy > 0
        # All-bank refresh uses more energy
        assert refab_energy > refsb_energy

    def test_idle_energy(self):
        """Test idle power energy"""
        estimator = HBM4PowerEstimator()
        idle_energy = estimator.get_command_energy('idle')
        assert idle_energy > 0
        # Idle energy per cycle should be low
        assert idle_energy < estimator.get_command_energy('ACT')

    def test_energy_per_cycle_with_width(self):
        """Test energy calculation with data width scaling"""
        estimator = HBM4PowerEstimator()
        energy_64 = estimator.calculate_energy_per_cycle('RD', data_width=64)
        energy_128 = estimator.calculate_energy_per_cycle('RD', data_width=128)
        # 128-bit should use roughly double
        assert energy_128 > energy_64
        assert energy_128 < energy_64 * 3  # But not excessively more

    def test_command_pattern_power(self):
        """Test power estimation for command pattern"""
        estimator = HBM4PowerEstimator()
        pattern = [
            ('ACT', 10),
            ('RD', 100),
            ('WR', 50),
            ('PRE', 10),
        ]
        result = estimator.estimate_power_for_pattern(pattern)
        assert result['total_energy_pJ'] > 0
        assert result['total_cycles'] == 170
        assert result['average_power_mW'] >= 0


class TestPHYPower:
    """Test PHY power components"""

    def test_phy_power_total(self):
        """Test total PHY power"""
        estimator = HBM4PowerEstimator()
        phy_total = estimator.phy_power.total()
        assert phy_total > 0

    def test_tsv_phy_power(self):
        """Test TSV PHY power"""
        estimator = HBM4PowerEstimator()
        tsv_power = estimator.phy_power.tsv_phy
        assert tsv_power >= 0

    def test_d2d_phy_power(self):
        """Test D2D PHY power"""
        estimator = HBM4PowerEstimator()
        d2d_power = estimator.phy_power.d2d_phy
        assert d2d_power >= 0

    def test_dfi_interface_power(self):
        """Test DFI interface power"""
        estimator = HBM4PowerEstimator()
        dfi_power = estimator.phy_power.dfi_interface
        assert dfi_power > 0

    def test_phy_power_breakdown(self):
        """Test PHY power breakdown"""
        estimator = HBM4PowerEstimator()
        phy = estimator.phy_power
        total = phy.tsv_phy + phy.d2d_phy + phy.dfi_interface + phy.analog_front_end
        assert abs(phy.total() - total) < 0.001


class TestPowerDownModes:
    """Test power-down mode power consumption"""

    def test_pdn_power(self):
        """Test power-down mode power"""
        estimator = HBM4PowerEstimator()
        pdn_power = estimator.get_power_down_power(PowerDownMode.PDN)
        assert pdn_power > 0

    def test_sref_power(self):
        """Test self-refresh power"""
        estimator = HBM4PowerEstimator()
        sref_power = estimator.get_power_down_power(PowerDownMode.SREF)
        assert sref_power > 0

    def test_dpd_power(self):
        """Test deep power-down power"""
        estimator = HBM4PowerEstimator()
        dpd_power = estimator.get_power_down_power(PowerDownMode.DPD)
        assert dpd_power >= 0

    def test_power_down_comparison(self):
        """Test power savings in power-down modes"""
        estimator = HBM4PowerEstimator()
        active_power = estimator.calculate_total_power()
        pdn_power = estimator.get_power_down_power(PowerDownMode.PDN)
        sref_power = estimator.get_power_down_power(PowerDownMode.SREF)

        # Power-down modes should use less power
        assert pdn_power < active_power
        assert sref_power < active_power

    def test_set_power_down_mode(self):
        """Test setting power-down mode"""
        estimator = HBM4PowerEstimator()
        estimator.set_power_down_mode(PowerDownMode.SREF)
        # Mode should be set (no exception)

    def test_get_mode_power(self):
        """Test getting power for specific mode"""
        estimator = HBM4PowerEstimator()
        power_down = estimator.power_down
        pdn = power_down.get_mode_power(PowerDownMode.PDN)
        sref = power_down.get_mode_power(PowerDownMode.SREF)

        assert pdn == power_down.pdn_static + power_down.pdn_dynamic
        assert sref == power_down.sref_static + power_down.sref_dram


class TestPerChannelTracking:
    """Test per-channel power tracking"""

    def test_channel_count(self):
        """Test correct number of channel trackers"""
        estimator = HBM4PowerEstimator()
        assert len(estimator.channel_powers) == 32

    def test_get_channel_power(self):
        """Test getting channel power by ID"""
        estimator = HBM4PowerEstimator()
        channel_0 = estimator.get_channel_power(0)
        assert isinstance(channel_0, ChannelPower)
        assert channel_0.channel_id == 0

    def test_get_invalid_channel(self):
        """Test error on invalid channel ID"""
        estimator = HBM4PowerEstimator()
        with pytest.raises(ValueError):
            estimator.get_channel_power(100)

    def test_update_channel_power(self):
        """Test updating channel power"""
        estimator = HBM4PowerEstimator()
        initial_power = estimator.get_channel_power(5).dynamic_power

        estimator.update_channel_power(channel_id=5, cmd='ACT', cycles=10)

        new_power = estimator.get_channel_power(5).dynamic_power
        assert new_power >= initial_power

    def test_channel_stats_tracking(self):
        """Test command statistics tracking"""
        estimator = HBM4PowerEstimator()
        estimator.reset_stats()

        estimator.update_channel_power(channel_id=0, cmd='ACT', cycles=1)
        estimator.update_channel_power(channel_id=0, cmd='RD', cycles=1)
        estimator.update_channel_power(channel_id=0, cmd='WR', cycles=1)

        assert estimator.stats.act_count == 1
        assert estimator.stats.rd_count == 1
        assert estimator.stats.wr_count == 1
        assert estimator.stats.total_commands == 3

    def test_stack_power_calculation(self):
        """Test aggregate stack power calculation"""
        estimator = HBM4PowerEstimator()
        stack_power = estimator.calculate_stack_power(num_channels=32)
        assert stack_power > 0
        # Should be roughly 32x single channel
        single_power = estimator.calculate_total_power()
        assert abs(stack_power / 32 - single_power) < 10  # Within 10mW tolerance

    def test_partial_stack_power(self):
        """Test power calculation with partial channel usage"""
        estimator = HBM4PowerEstimator()
        full_power = estimator.calculate_stack_power(num_channels=32)
        half_power = estimator.calculate_stack_power(num_channels=16)
        assert half_power < full_power
        assert half_power > full_power / 4  # More than quarter


class TestFactoryFunction:
    """Test factory function"""

    def test_create_power_estimator_default(self):
        """Test create_power_estimator with defaults"""
        estimator = create_power_estimator()
        assert estimator is not None
        assert estimator.spec.data_rate_gtps == 8.0

    def test_create_power_estimator_12gbps(self):
        """Test create_power_estimator with 12Gbps"""
        estimator = create_power_estimator(speed_grade='12Gbps')
        assert estimator.spec.data_rate_gtps == 12.0
        assert estimator.freq_mhz == 1200

    def test_create_power_estimator_16gbps(self):
        """Test create_power_estimator with 16Gbps"""
        estimator = create_power_estimator(speed_grade='16Gbps')
        assert estimator.spec.data_rate_gtps == 16.0
        assert estimator.freq_mhz == 1600

    def test_create_power_estimator_custom_vdd(self):
        """Test create_power_estimator with custom VDD"""
        estimator = create_power_estimator(vdd_mv=1.0)
        assert estimator.vdd_mv == 1.0


class TestPowerSummary:
    """Test power summary generation"""

    def test_get_summary(self):
        """Test getting power summary"""
        estimator = HBM4PowerEstimator()
        summary = estimator.get_summary()

        assert 'spec' in summary
        assert 'parameters' in summary
        assert 'power_mW' in summary
        assert 'stats' in summary

        assert summary['spec']['channels'] == 32
        assert summary['parameters']['vdd_mv'] == 0.9
        assert summary['power_mW']['total'] > 0

    def test_reset_stats(self):
        """Test resetting statistics"""
        estimator = HBM4PowerEstimator()
        estimator.update_channel_power(channel_id=0, cmd='ACT', cycles=1)
        estimator.reset_stats()

        assert estimator.stats.total_commands == 0
        assert estimator.stats.energy_pJ == 0


class TestVoltageScaling:
    """Test power scaling with voltage"""

    def test_voltage_scaling(self):
        """Test that power scales with voltage"""
        est_0v9 = HBM4PowerEstimator(vdd_mv=900)
        est_1v0 = HBM4PowerEstimator(vdd_mv=1000)

        power_0v9 = est_0v9.calculate_total_power()
        power_1v0 = est_1v0.calculate_total_power()

        # Power should scale roughly with V^2
        # 1.0V / 0.9V = 1.111, squared = 1.23
        assert power_1v0 > power_0v9
        # But not 4x (which would be linear)
        assert power_1v0 < power_0v9 * 1.5


class TestFrequencyScaling:
    """Test power scaling with frequency"""

    def test_frequency_scaling(self):
        """Test that power scales with frequency"""
        est_800 = HBM4PowerEstimator(freq_mhz=800)
        est_1600 = HBM4PowerEstimator(freq_mhz=1600)

        power_800 = est_800.calculate_total_power()
        power_1600 = est_1600.calculate_total_power()

        # Higher frequency should mean higher power
        assert power_1600 > power_800
        # Dynamic power should scale roughly with frequency
        # Static power (clock tree, etc.) also scales


if __name__ == '__main__':
    pytest.main([__file__, '-v'])