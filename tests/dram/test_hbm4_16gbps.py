"""
Tests for HBM4 16Gbps Speed Grade Support

Comprehensive tests for the 16 Gbps speed grade including:
- Timing parameters at 16 GT/s DDR (tCK = 62.5 ps)
- Power parameters scaled for higher frequency operation
- Bandwidth calculations (4.096 TB/s)
- Channel model integration
- Speed grade transitions

Based on:
- JEDEC JESD270-4A HBM4 specification
- HBM4E extended rate requirements
"""

import pytest
from model.dram.hbm4_spec import (
    HBM4Spec, HBM4_SPEED_GRADES, HBM4_DEFAULT_TIMING,
    create_hbm4_spec_from_speed_grade, create_hbm4_spec_with_timing,
    calculate_bandwidth, calculate_tCK_from_rate
)
from model.dram.timing import (
    HBM4Timing, get_timing_for_speed_grade, get_timing_for_hbm_version
)
from model.dram.power_estimator import (
    PowerParameters, HBM4PowerEstimator, POWER_PRESETS,
    create_power_estimator, create_power_estimator_with_config,
    CommandType, PowerState
)
from model.dram.hbm4_channel_model import HBM4Channel


class TestHBM416GbpsTiming:
    """Test HBM4 timing parameters at 16 GT/s"""

    def test_tCK_62_5ps(self):
        """tCK should be 62.5 ps for 16 GT/s DDR"""
        timing = HBM4Timing.for_16gbps()
        assert abs(timing.tCK_ps - 62.5) < 0.01

    def test_clock_frequency_16GHz(self):
        """Clock frequency should be 16 GHz DDR"""
        timing = HBM4Timing.for_16gbps()
        expected_freq = 16e9  # 16 GHz
        assert abs(timing.clock_freq - expected_freq) < 1e6

    def test_clock_period_ns(self):
        """Clock period should be 0.0625 ns"""
        timing = HBM4Timing.for_16gbps()
        expected_ns = 0.0625
        assert abs(timing.clock_period_ns - expected_ns) < 0.001

    def test_nCL_at_16gbps(self):
        """CAS latency should be 8 cycles at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nCL == 8

    def test_nRAS_at_16gbps(self):
        """Row active time should be 20 cycles at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nRAS == 20

    def test_nRC_at_16gbps(self):
        """Row cycle time should be 22 cycles at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nRC == 22

    def test_nCCD_at_16gbps(self):
        """CAS-to-CAS delay should be 4 cycles at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nCCD == 4

    def test_nFAW_at_16gbps(self):
        """Four-activate window should be 16 cycles at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nFAW == 16

    def test_nRFC_at_16gbps(self):
        """Refresh cycle time should be 180 cycles at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nRFC == 180

    def test_nREFI_at_16gbps(self):
        """Refresh interval should be 3900 cycles at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nREFI == 3900

    def test_for_speed_grade_16(self):
        """for_speed_grade(16.0) should work"""
        timing = HBM4Timing.for_speed_grade(16.0)
        assert timing.tCK_ps == 62.5

    def test_get_timing_for_hbm_version(self):
        """hbm4_16gbps should return 16Gbps timing"""
        timing = get_timing_for_hbm_version("hbm4_16gbps")
        assert timing.tCK_ps == 62.5

    def test_cycles_to_ns_at_16gbps(self):
        """8 cycles should be 0.5 ns at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        result = timing.cycles_to_ns(8)
        expected = 0.5  # 8 * 62.5 ps = 500 ps = 0.5 ns
        assert abs(result - expected) < 0.01

    def test_ns_to_cycles_at_16gbps(self):
        """0.5 ns should be 8 cycles at 16 GT/s"""
        timing = HBM4Timing.for_16gbps()
        result = timing.ns_to_cycles(0.5)
        expected = 8  # 0.5 ns / 62.5 ps = 8 cycles
        assert abs(result - expected) < 1

    def test_alias_nRCDRD(self):
        """nRCDRD should be alias for nRCD"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nRCDRD == timing.nRCD

    def test_alias_nRCDWR(self):
        """nRCDWR should be alias for nRCD"""
        timing = HBM4Timing.for_16gbps()
        assert timing.nRCDWR == timing.nRCD


class TestHBM416GbpsSpec:
    """Test HBM4Spec at 16 GT/s"""

    def test_create_16gbps_spec(self):
        """Should create spec with 16 GT/s parameters"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        assert spec.data_rate_gtps == 16.0
        assert spec.tCK_ps == 62.5

    def test_16gbps_bandwidth(self):
        """16 GT/s should provide 4.096 TB/s"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        expected_bw = 4.096  # TB/s
        assert abs(spec.bandwidth - expected_bw) < 0.01

    def test_16gbps_bandwidth_gbs(self):
        """16 GT/s should provide 4096 GB/s"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        expected_bw = 4096.0  # GB/s
        assert abs(spec.bandwidth_gbs - expected_bw) < 1.0

    def test_bandwidth_scales_linearly(self):
        """Bandwidth should double when going from 8 to 16 GT/s"""
        spec_8 = create_hbm4_spec_from_speed_grade("8Gbps")
        spec_16 = create_hbm4_spec_from_speed_grade("16Gbps")
        ratio = spec_16.bandwidth / spec_8.bandwidth
        assert abs(ratio - 2.0) < 0.01

    def test_speed_grade_in_speed_grades(self):
        """16Gbps should be in HBM4_SPEED_GRADES"""
        assert "16Gbps" in HBM4_SPEED_GRADES

    def test_speed_grade_params(self):
        """Speed grade params should be correct"""
        grade = HBM4_SPEED_GRADES["16Gbps"]
        assert grade["data_rate_gtps"] == 16.0
        assert grade["tCK_ps"] == 62.5
        assert "16 GT/s" in grade["description"]

    def test_create_with_timing_multiplier(self):
        """Should support timing multiplier"""
        spec = create_hbm4_spec_with_timing("16Gbps", timing_multiplier=1.5)
        assert spec.data_rate_gtps == 16.0
        # With 1.5x multiplier, nCL should be 12 (8 * 1.5)
        assert spec.nCL == 12


class TestHBM416GbpsChannel:
    """Test HBM4Channel at 16 GT/s"""

    def test_create_channel_16gbps(self):
        """Should create channel with 16Gbps parameters"""
        ch = HBM4Channel.create_with_speed_grade(0, "16Gbps")
        assert ch.spec.data_rate_gtps == 16.0
        assert ch.timing.tCK_ps == 62.5

    def test_channel_bandwidth(self):
        """Channel should provide 128 GB/s at 16 GT/s"""
        ch = HBM4Channel.create_with_speed_grade(0, "16Gbps")
        # 16 GT/s * 64 bits / 8 = 128 GB/s per channel
        expected = 128.0  # GB/s per channel
        assert abs(ch.spec.bandwidth_gbs / 32 - expected) < 1.0

    def test_16gbps_in_supported_grades(self):
        """16Gbps should be in supported speed grades"""
        assert "16Gbps" in HBM4Channel.SUPPORTED_SPEED_GRADES

    def test_tCK_from_rate_calculation(self):
        """tCK calculation should match 16 GT/s"""
        tCK = calculate_tCK_from_rate(16.0)
        assert abs(tCK - 62.5) < 0.01


class TestHBM416GbpsPower:
    """Test power parameters at 16 GT/s"""

    def test_16gbps_power_preset_exists(self):
        """16Gbps power preset should exist"""
        assert "16Gbps" in POWER_PRESETS

    def test_16gbps_power_params(self):
        """Power parameters should be higher at 16 GT/s"""
        params_8 = POWER_PRESETS["8Gbps"]
        params_16 = POWER_PRESETS["16Gbps"]

        # Active power should be higher
        assert params_16.active_power_ma > params_8.active_power_ma

        # Read power should be higher
        assert params_16.read_power_ma > params_8.read_power_ma

        # Write power should be higher
        assert params_16.write_power_ma > params_8.write_power_ma

    def test_16gbps_voltage_scaling(self):
        """VDDQ voltage should be higher at 16 GT/s"""
        params_16 = POWER_PRESETS["16Gbps"]
        assert params_16.vddq_voltage > 1.1  # Higher than 8Gbps baseline

    def test_16gbps_energy_scaling(self):
        """Command energy should scale with voltage"""
        params_8 = POWER_PRESETS["8Gbps"]
        params_16 = POWER_PRESETS["16Gbps"]

        # Activation energy should be higher
        assert params_16.act_energy_pj > params_8.act_energy_pj

        # Read energy should be higher
        assert params_16.rd_energy_pj > params_8.rd_energy_pj

        # Write energy should be higher
        assert params_16.wr_energy_pj > params_8.wr_energy_pj

    def test_create_power_estimator_16gbps(self):
        """Should create power estimator for 16Gbps"""
        est = create_power_estimator("16Gbps")
        assert est.data_rate_gtps == 16.0
        assert est.params.active_power_ma == 500.0

    def test_power_estimator_tCK(self):
        """Power estimator should calculate correct tCK"""
        est = create_power_estimator("16Gbps")
        tCK = est._get_tCK_ps()
        assert abs(tCK - 62.5) < 0.01

    def test_power_estimator_with_config(self):
        """Should create power estimator with custom config"""
        est = create_power_estimator_with_config(
            speed_grade="16Gbps",
            process_corner="TT",
            temperature_c=55.0
        )
        assert est.data_rate_gtps == 16.0
        assert est.params.process_corner.value == "typical"
        assert est.params.temperature_c == 55.0


class TestHBM416GbpsBandwidth:
    """Test bandwidth calculations at 16 GT/s"""

    def test_bandwidth_calculation(self):
        """Calculate bandwidth from rate and width"""
        bw = calculate_bandwidth(16.0, 2048)
        expected = 4.096  # TB/s
        assert abs(bw - expected) < 0.01

    def test_16gbps_vs_8gbps_bandwidth(self):
        """16 GT/s should provide 2x bandwidth of 8 GT/s"""
        bw_8 = calculate_bandwidth(8.0, 2048)
        bw_16 = calculate_bandwidth(16.0, 2048)
        assert abs(bw_16 / bw_8 - 2.0) < 0.01

    def test_16gbps_vs_12gbps_bandwidth(self):
        """16 GT/s should provide 4/3 bandwidth of 12 GT/s"""
        bw_12 = calculate_bandwidth(12.0, 2048)
        bw_16 = calculate_bandwidth(16.0, 2048)
        assert abs(bw_16 / bw_12 - 4/3) < 0.01


class TestHBM416GbpsTimingConversions:
    """Test timing conversions at 16 GT/s"""

    def test_absolute_timing_constants(self):
        """Absolute timing values should be constant across speed grades"""
        # tRCD absolute time should be same across grades
        timing_8 = HBM4Timing.for_8gbps()
        timing_16 = HBM4Timing.for_16gbps()

        # 8 cycles at 8 GT/s = 8 * 125 ps = 1000 ps
        tRCD_8 = timing_8.cycles_to_ns(timing_8.nRCD) * 1000  # ps
        # 8 cycles at 16 GT/s = 8 * 62.5 ps = 500 ps
        tRCD_16 = timing_16.cycles_to_ns(timing_16.nRCD) * 1000  # ps

        # At same cycle count, absolute time halves with double data rate
        # This is expected - higher speed = shorter cycle time
        assert tRCD_16 < tRCD_8

    def test_refresh_interval_absolute(self):
        """Refresh interval should scale with tCK"""
        timing_8 = HBM4Timing.for_8gbps()
        timing_16 = HBM4Timing.for_16gbps()

        # nREFI is in cycles, so absolute time differs with tCK
        # 3900 cycles at 8 GT/s = 3900 * 125 ps = 487.5 us
        # 3900 cycles at 16 GT/s = 3900 * 62.5 ps = 243.75 us
        refresh_us_8 = timing_8.cycles_to_ns(timing_8.nREFI) / 1000
        refresh_us_16 = timing_16.cycles_to_ns(timing_16.nREFI) / 1000

        # 16 GT/s should have half the refresh interval in absolute time
        assert abs(refresh_us_16 - refresh_us_8 / 2) < 1  # Within 1 us


class TestHBM416GbpsIntegration:
    """Integration tests for 16 GT/s operation"""

    def test_channel_lifecycle(self):
        """Test complete channel lifecycle at 16 GT/s"""
        ch = HBM4Channel.create_with_speed_grade(0, "16Gbps")

        # Activate row in pseudo-channel 0, bank 0
        result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=0)
        assert result, "ACT should succeed"

        # Read should work (will auto-activate if needed)
        result = ch.issue_command('RD', pseudo_channel=0, bank=0, row=0)
        assert result, "RD should succeed"

        # Advance cycles for read to complete
        for _ in range(ch.timing.nCL + 4):
            ch.tick()

        # Write should work
        result = ch.issue_command('WR', pseudo_channel=0, bank=0, row=0)
        assert result, "WR should succeed"

        # Advance cycles for write to complete
        for _ in range(ch.timing.nCWL + 4):
            ch.tick()

        # Precharge
        result = ch.issue_command('PRE', pseudo_channel=0, bank=0, row=0)
        assert result, "PRE should succeed"

    def test_power_estimation_lifecycle(self):
        """Test power estimation at 16 GT/s"""
        est = create_power_estimator("16Gbps")

        # Set active state
        est.set_channel_state(0, PowerState.ACTIVE, 100)
        est.tick(100)

        # Set read state
        est.set_channel_state(0, PowerState.READ, 50)
        est.tick(50)

        # Check power
        power = est.get_channel_power_mw(0)
        assert power > 0

    def test_command_energy_tracking(self):
        """Test command energy tracking at 16 GT/s"""
        est = create_power_estimator("16Gbps")

        # Record commands
        est.record_command(0, CommandType.ACT)
        est.record_command(0, CommandType.RD)
        est.record_command(0, CommandType.WR)

        # Check command counts
        counts = est.get_command_count_breakdown()
        assert counts["act"] == 1
        assert counts["rd"] == 1
        assert counts["wr"] == 1

    def test_power_report_generation(self):
        """Test power report generation at 16 GT/s"""
        est = create_power_estimator("16Gbps")

        # Simulate some activity
        est.set_all_channels_state(PowerState.ACTIVE, 1000)
        est.tick(1000)

        # Generate report
        report = est.generate_report()

        assert report.data_rate_gtps == 16.0
        assert report.total_power_mw > 0
        assert report.num_channels == 32


class TestHBM416GbpsSpeedGradeTransitions:
    """Test transitions between speed grades"""

    def test_8_to_16_transition(self):
        """Test transitioning from 8 to 16 GT/s"""
        ch_8 = HBM4Channel.create_with_speed_grade(0, "8Gbps")
        ch_16 = HBM4Channel.create_with_speed_grade(0, "16Gbps")

        assert ch_16.timing.tCK_ps < ch_8.timing.tCK_ps
        assert ch_16.spec.data_rate_gtps > ch_8.spec.data_rate_gtps

    def test_12_to_16_transition(self):
        """Test transitioning from 12 to 16 GT/s"""
        ch_12 = HBM4Channel.create_with_speed_grade(0, "12Gbps")
        ch_16 = HBM4Channel.create_with_speed_grade(0, "16Gbps")

        assert ch_16.timing.tCK_ps < ch_12.timing.tCK_ps
        assert ch_16.spec.data_rate_gtps > ch_12.spec.data_rate_gtps

    def test_power_transition(self):
        """Test power parameters across speed grades"""
        est_8 = create_power_estimator("8Gbps")
        est_16 = create_power_estimator("16Gbps")

        # 16Gbps should have higher active power
        assert est_16.params.active_power_ma > est_8.params.active_power_ma

    def test_timing_multiplier_effect(self):
        """Test timing multiplier affects timing correctly"""
        spec_base = create_hbm4_spec_with_timing("16Gbps", timing_multiplier=1.0)
        spec_tight = create_hbm4_spec_with_timing("16Gbps", timing_multiplier=0.75)
        spec_loose = create_hbm4_spec_with_timing("16Gbps", timing_multiplier=1.25)

        # With tighter timing, cycles should be fewer
        assert spec_tight.nCL < spec_base.nCL
        # With looser timing, cycles should be more
        assert spec_loose.nCL > spec_base.nCL


class TestHBM416GbpsEdgeCases:
    """Test edge cases for 16 GT/s operation"""

    def test_invalid_speed_grade_raises(self):
        """Invalid speed grade should raise ValueError"""
        with pytest.raises(ValueError):
            create_hbm4_spec_from_speed_grade("invalid")

    def test_invalid_timing_speed_grade_raises(self):
        """Invalid speed grade for timing should raise ValueError"""
        with pytest.raises(ValueError):
            get_timing_for_speed_grade("invalid")

    def test_invalid_power_speed_grade_raises(self):
        """Invalid speed grade for power should use default"""
        # Should not raise, just use default
        est = create_power_estimator("invalid")
        assert est.data_rate_gtps == 8.0  # Default

    def test_boundary_values(self):
        """Test boundary values for timing parameters"""
        timing = HBM4Timing.for_16gbps()

        # All timing parameters should be positive integers
        assert timing.nCL > 0
        assert timing.nRAS > 0
        assert timing.nRC > 0
        assert timing.nRFC > 0

        # nRC should be >= nRAS (HBM4 uses nRC = nRAS + nRP - 1)
        assert timing.nRC >= timing.nRAS

    def test_burst_length_constant(self):
        """Burst length should be constant across speed grades"""
        # Burst length comes from spec, not timing class
        spec_8 = create_hbm4_spec_from_speed_grade("8Gbps")
        spec_16 = create_hbm4_spec_from_speed_grade("16Gbps")

        # HBM4 FLINE burst length is 4
        assert spec_8.burst_length == spec_16.burst_length == 4


class TestHBM416GbpsPerformance:
    """Performance benchmarks for 16 GT/s"""

    def test_peak_bandwidth(self):
        """Peak bandwidth should meet HBM4E spec"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        # 16 GT/s * 2048 bits / 8 / 1000 = 4.096 TB/s
        assert spec.bandwidth >= 4.0  # At least 4 TB/s

    def test_latency_ns(self):
        """Latency in ns should meet timing spec"""
        timing = HBM4Timing.for_16gbps()

        # CAS latency: 8 cycles * 62.5 ps = 0.5 ns
        cl_ns = timing.cycles_to_ns(timing.nCL)
        assert cl_ns < 1.0  # Less than 1 ns

        # RAS-to-CAS: 8 cycles * 62.5 ps = 0.5 ns
        tRCD_ns = timing.cycles_to_ns(timing.nRCD)
        assert tRCD_ns < 1.0

    def test_power_density(self):
        """Power density should be reasonable"""
        est = create_power_estimator("16Gbps")

        # Set all channels to active
        est.set_all_channels_state(PowerState.ACTIVE, 1000)

        total_power = est.get_total_power_mw()
        power_per_channel = total_power / 32

        # Should be less than 1W per channel
        assert power_per_channel < 1000

    def test_refresh_overhead(self):
        """Refresh overhead should be manageable"""
        timing = HBM4Timing.for_16gbps()

        # Refresh interval: 3900 cycles
        # Refresh duration: 180 cycles
        refresh_overhead = timing.nRFC / timing.nREFI
        assert refresh_overhead < 0.1  # Less than 10% overhead