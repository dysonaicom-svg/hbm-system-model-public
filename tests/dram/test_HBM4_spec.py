"""
Tests for HBM4 DRAM Specification Constants

Based on:
- JEDEC JESD270-4A HBM4 specification
- Ramulator 2.0 HBM3 timing reference
- Multi-agent research findings (2026-06-15)
"""

import pytest
from model.dram.HBM4_spec import (
    HBM4Spec, HBM4_CONFIG, HBM4_SPEED_GRADES,
    create_hbm4_spec_from_speed_grade, create_hbm4_spec_with_timing,
    calculate_tCK_from_rate
)
from model.dram.timing import HBM4Timing, get_timing_for_speed_grade, SPEED_GRADE_TIMING
from model.dram.HBM4_channel_model import HBM4Channel


class TestHBM4SpecChannels:
    """Test HBM4 channel configuration"""

    def test_hbm4_spec_channels(self):
        """HBM4 must have 32 channels, not 8 like HBM3"""
        spec = HBM4Spec()
        assert spec.channels == 32, "HBM4 must have 32 channels"

    def test_hbm4_spec_pseudo_channels(self):
        """32 channels × 2 pseudo-channels = 64 total"""
        spec = HBM4Spec()
        assert spec.pseudo_channels == 64, "64 pseudo-channels for HBM4"

    def test_hbm4_spec_total_banks(self):
        """Total banks = channels × pseudo-channels × banks_per_pseudo_channel"""
        spec = HBM4Spec()
        expected = 32 * 2 * 16  # 1024 banks
        assert spec.total_banks == expected, f"Expected {expected} total banks"


class TestHBM4SpecInterface:
    """Test HBM4 interface parameters"""

    def test_hbm4_spec_interface_width(self):
        """HBM4 interface width is 2048-bit (32 channels × 64-bit)"""
        spec = HBM4Spec()
        assert spec.io_width == 2048, "2048-bit interface for HBM4"

    def test_hbm4_spec_data_rate(self):
        """HBM4 base data rate is 8 GT/s"""
        spec = HBM4Spec()
        assert spec.data_rate_gtps == 8.0, "8 GT/s base rate"

    def test_hbm4_spec_bandwidth(self):
        """HBM4 @ 8 GT/s = 2.048 TB/s per stack"""
        spec = HBM4Spec()
        # 8 GT/s × 2048 bits / 8 / 1000 = 2.048 TB/s
        expected_bw = 2.048  # TB/s
        assert abs(spec.bandwidth - expected_bw) < 0.01

    def test_hbm4_spec_bandwidth_gbs(self):
        """HBM4 bandwidth in GB/s"""
        spec = HBM4Spec()
        expected_bw = 2048.0  # GB/s (8 GT/s × 2048 / 8)
        assert abs(spec.bandwidth_gbs - expected_bw) < 1.0


class TestHBM4SpecTiming:
    """Test HBM4 timing parameters"""

    def test_hbm4_tCK(self):
        """tCK should be 125ps for 8 GT/s DDR (1/8e9 = 125ps)"""
        spec = HBM4Spec()
        assert spec.tCK_ps == 125.0

    def test_hbm4_nCL(self):
        """CAS latency should be 8 cycles"""
        spec = HBM4Spec()
        assert spec.nCL == 8

    def test_hbm4_nRAS(self):
        """RAS delay should be 20 cycles"""
        spec = HBM4Spec()
        assert spec.nRAS == 20

    def test_hbm4_nRP(self):
        """Precharge delay should be 8 cycles"""
        spec = HBM4Spec()
        assert spec.nRP == 8

    def test_hbm4_nREFI(self):
        """Refresh interval should be 3900 cycles"""
        spec = HBM4Spec()
        assert spec.nREFI == 3900


class TestHBM4SpecAddressBits:
    """Test HBM4 address bit field configuration"""

    def test_channel_bits(self):
        """Channel field should be 5 bits (32 channels)"""
        spec = HBM4Spec()
        assert spec.ADDR_CHANNEL_BITS == 5

    def test_pseudo_channel_bits(self):
        """Pseudo-channel field should be 1 bit (2 per channel)"""
        spec = HBM4Spec()
        assert spec.ADDR_PCH_BITS == 1

    def test_bank_group_bits(self):
        """Bank group field should be 3 bits (8 groups)"""
        spec = HBM4Spec()
        assert spec.ADDR_BG_BITS == 3

    def test_bank_bits(self):
        """Bank field should be 4 bits (16 banks per group)"""
        spec = HBM4Spec()
        assert spec.ADDR_BANK_BITS == 4

    def test_row_bits(self):
        """Row field should be 19 bits (512K rows for 4TB capacity)"""
        spec = HBM4Spec()
        assert spec.ADDR_ROW_BITS == 19

    def test_col_bits(self):
        """Column field should be 6 bits (64 columns)"""
        spec = HBM4Spec()
        assert spec.ADDR_COL_BITS == 6


class TestHBM4SpecBitFieldExtraction:
    """Test address bit field extraction methods"""

    def test_get_channel_bits(self):
        """Channel bits should be (0, 5)"""
        spec = HBM4Spec()
        start, num = spec.get_channel_bits()
        assert start == 0
        assert num == 5

    def test_get_pseudo_channel_bits(self):
        """Pseudo-channel bits should start after channel"""
        spec = HBM4Spec()
        start, num = spec.get_pseudo_channel_bits()
        assert start == 5  # After channel bits
        assert num == 1

    def test_get_bank_group_bits(self):
        """Bank group bits should start after channel + pch"""
        spec = HBM4Spec()
        start, num = spec.get_bank_group_bits()
        assert start == 6  # After channel + pch
        assert num == 3

    def test_get_bank_bits(self):
        """Bank bits should start after channel + pch + bg"""
        spec = HBM4Spec()
        start, num = spec.get_bank_bits()
        assert start == 9  # After channel + pch + bg
        assert num == 4

    def test_get_row_bits(self):
        """Row bits should start after all other fields"""
        spec = HBM4Spec()
        start, num = spec.get_row_bits()
        assert start == 13  # After channel + pch + bg + bank
        assert num == 19  # 512K rows for 4TB capacity


class TestHBM4SpeedGrades:
    """Test HBM4 speed grade presets"""

    def test_speed_grades_available(self):
        """All speed grades should be available"""
        assert "8Gbps" in HBM4_SPEED_GRADES
        assert "12Gbps" in HBM4_SPEED_GRADES
        assert "16Gbps" in HBM4_SPEED_GRADES

    def test_speed_grade_8gbps(self):
        """8 Gbps grade should have correct parameters"""
        grade = HBM4_SPEED_GRADES["8Gbps"]
        assert grade["data_rate_gtps"] == 8.0
        assert grade["tCK_ps"] == 125.0  # 1000/8 = 125 ps for 8 GT/s DDR

    def test_speed_grade_12gbps(self):
        """12 Gbps grade should have correct parameters"""
        grade = HBM4_SPEED_GRADES["12Gbps"]
        assert grade["data_rate_gtps"] == 12.0
        assert abs(grade["tCK_ps"] - 83.33) < 0.1  # 1000/12 = 83.33 ps for 12 GT/s DDR

    def test_speed_grade_16gbps(self):
        """16 Gbps grade should have correct parameters"""
        grade = HBM4_SPEED_GRADES["16Gbps"]
        assert grade["data_rate_gtps"] == 16.0
        assert grade["tCK_ps"] == 62.5  # 1000/16 = 62.5 ps for 16 GT/s DDR


class TestHBM4Config:
    """Test default HBM4 configuration"""

    def test_default_config_exists(self):
        """Default configuration should exist"""
        assert HBM4_CONFIG is not None
        assert isinstance(HBM4_CONFIG, HBM4Spec)

    def test_default_config_values(self):
        """Default config should match HBM4 spec"""
        assert HBM4_CONFIG.channels == 32
        assert HBM4_CONFIG.io_width == 2048
        assert HBM4_CONFIG.data_rate_gtps == 8.0


class TestHBM4Comparison:
    """Test HBM4 vs HBM3 differences"""

    def test_hbm4_has_more_channels_than_hbm3(self):
        """HBM4 has 32 channels vs HBM3's 8 channels"""
        spec = HBM4Spec()
        hbm3_channels = 8  # Typical HBM3 configuration

        assert spec.channels > hbm3_channels
        assert spec.channels == 32

    def test_hbm4_has_wider_interface(self):
        """HBM4 has 2048-bit interface vs HBM3's 1024-bit"""
        spec = HBM4Spec()
        hbm3_width = 1024  # Typical HBM3 interface width

        assert spec.io_width > hbm3_width
        assert spec.io_width == 2048

    def test_hbm4_has_higher_bandwidth(self):
        """HBM4 has 2.048 TB/s vs HBM3's ~0.819 TB/s"""
        spec = HBM4Spec()
        hbm3_bandwidth = 0.8192  # TB/s at 6.4 GT/s with 1024-bit

        assert spec.bandwidth > hbm3_bandwidth
        assert spec.bandwidth == 2.048

    def test_hbm4_has_more_pseudo_channels(self):
        """HBM4 has 64 pseudo-channels vs HBM3's 16"""
        spec = HBM4Spec()
        hbm3_pseudo_channels = 16  # 8 channels × 2

        assert spec.pseudo_channels > hbm3_pseudo_channels
        assert spec.pseudo_channels == 64


class TestHBM4TCalculations:
    """Test tCK calculations"""

    def test_tCK_for_8gbps(self):
        """tCK for 8 GT/s should be 125 ps"""
        tCK = calculate_tCK_from_rate(8.0)
        assert abs(tCK - 125.0) < 0.01

    def test_tCK_for_12gbps(self):
        """tCK for 12 GT/s should be 83.33 ps"""
        tCK = calculate_tCK_from_rate(12.0)
        assert abs(tCK - 83.33) < 0.1

    def test_tCK_for_16gbps(self):
        """tCK for 16 GT/s should be 62.5 ps"""
        tCK = calculate_tCK_from_rate(16.0)
        assert abs(tCK - 62.5) < 0.01

    def test_speed_grade_tCK_matches_calculation(self):
        """Speed grade tCK values should match calculated values"""
        for grade_name, grade_params in HBM4_SPEED_GRADES.items():
            expected_tCK = calculate_tCK_from_rate(grade_params["data_rate_gtps"])
            actual_tCK = grade_params["tCK_ps"]
            assert abs(actual_tCK - expected_tCK) < 0.01, \
                f"{grade_name}: tCK mismatch ({actual_tCK} vs {expected_tCK})"


class TestHBM4SpeedGradeCreation:
    """Test speed grade spec creation"""

    def test_create_8gbps_spec(self):
        """Should create spec with 8 GT/s parameters"""
        spec = create_hbm4_spec_from_speed_grade("8Gbps")
        assert spec.data_rate_gtps == 8.0
        assert spec.tCK_ps == 125.0

    def test_create_12gbps_spec(self):
        """Should create spec with 12 GT/s parameters"""
        spec = create_hbm4_spec_from_speed_grade("12Gbps")
        assert spec.data_rate_gtps == 12.0
        assert abs(spec.tCK_ps - 83.33) < 0.1

    def test_create_16gbps_spec(self):
        """Should create spec with 16 GT/s parameters"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        assert spec.data_rate_gtps == 16.0
        assert spec.tCK_ps == 62.5

    def test_create_with_timing_multiplier(self):
        """Should support timing multiplier for tighter/looser timing"""
        spec = create_hbm4_spec_with_timing("16Gbps", timing_multiplier=1.5)
        assert spec.data_rate_gtps == 16.0
        # Timing parameters should be scaled

    def test_invalid_speed_grade_raises(self):
        """Invalid speed grade should raise ValueError"""
        with pytest.raises(ValueError):
            create_hbm4_spec_from_speed_grade("invalid")


class TestHBM4TimingSpeedGrades:
    """Test HBM4Timing with speed grades"""

    def test_for_8gbps(self):
        """HBM4Timing.for_8gbps() should return correct parameters"""
        timing = HBM4Timing.for_8gbps()
        assert timing.tCK_ps == 125.0

    def test_for_12gbps(self):
        """HBM4Timing.for_12gbps() should return correct parameters"""
        timing = HBM4Timing.for_12gbps()
        assert abs(timing.tCK_ps - 83.33) < 0.1

    def test_for_16gbps(self):
        """HBM4Timing.for_16gbps() should return correct parameters"""
        timing = HBM4Timing.for_16gbps()
        assert timing.tCK_ps == 62.5

    def test_for_speed_grade_8gbps(self):
        """HBM4Timing.for_speed_grade(8.0) should work"""
        timing = HBM4Timing.for_speed_grade(8.0)
        assert timing.tCK_ps == 125.0

    def test_for_speed_grade_16gbps(self):
        """HBM4Timing.for_speed_grade(16.0) should work"""
        timing = HBM4Timing.for_speed_grade(16.0)
        assert timing.tCK_ps == 62.5

    def test_clock_freq_for_16gbps(self):
        """Clock frequency for 16 GT/s should be 16 GHz DDR"""
        timing = HBM4Timing.for_16gbps()
        # tCK = 62.5 ps, so freq = 1/62.5e-12 = 16e9 Hz = 16 GHz
        assert abs(timing.clock_freq - 16e9) < 1e6

    def test_get_timing_for_speed_grade(self):
        """get_timing_for_speed_grade() should work for all grades"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            timing = get_timing_for_speed_grade(grade)
            assert isinstance(timing, HBM4Timing)


class TestHBM4ChannelSpeedGrades:
    """Test HBM4Channel with speed grades"""

    def test_create_with_8gbps(self):
        """HBM4Channel.create_with_speed_grade() for 8Gbps"""
        ch = HBM4Channel.create_with_speed_grade(0, "8Gbps")
        assert ch.spec.data_rate_gtps == 8.0
        assert ch.timing.tCK_ps == 125.0

    def test_create_with_16gbps(self):
        """HBM4Channel.create_with_speed_grade() for 16Gbps"""
        ch = HBM4Channel.create_with_speed_grade(0, "16Gbps")
        assert ch.spec.data_rate_gtps == 16.0
        assert ch.timing.tCK_ps == 62.5

    def test_16gbps_bandwidth(self):
        """16 GT/s should provide higher bandwidth"""
        ch = HBM4Channel.create_with_speed_grade(0, "16Gbps")
        # 16 GT/s x 2048 bits / 8 = 4096 GB/s = 4.096 TB/s
        expected_bw = 4.096  # TB/s
        assert abs(ch.spec.bandwidth - expected_bw) < 0.01

    def test_supported_speed_grades(self):
        """All speed grades should be listed"""
        assert "8Gbps" in HBM4Channel.SUPPORTED_SPEED_GRADES
        assert "12Gbps" in HBM4Channel.SUPPORTED_SPEED_GRADES
        assert "16Gbps" in HBM4Channel.SUPPORTED_SPEED_GRADES

    def test_invalid_speed_grade_raises(self):
        """Invalid speed grade should raise ValueError"""
        with pytest.raises(ValueError):
            HBM4Channel.create_with_speed_grade(0, "invalid")


class TestHBM4BandwidthScaling:
    """Test bandwidth scales correctly with data rate"""

    def test_8gbps_bandwidth(self):
        """8 GT/s should provide 2.048 TB/s"""
        spec = create_hbm4_spec_from_speed_grade("8Gbps")
        assert abs(spec.bandwidth - 2.048) < 0.01

    def test_12gbps_bandwidth(self):
        """12 GT/s should provide 3.072 TB/s"""
        spec = create_hbm4_spec_from_speed_grade("12Gbps")
        assert abs(spec.bandwidth - 3.072) < 0.01

    def test_16gbps_bandwidth(self):
        """16 GT/s should provide 4.096 TB/s"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        assert abs(spec.bandwidth - 4.096) < 0.01

    def test_bandwidth_scales_linearly(self):
        """Bandwidth should scale linearly with data rate"""
        spec_8 = create_hbm4_spec_from_speed_grade("8Gbps")
        spec_16 = create_hbm4_spec_from_speed_grade("16Gbps")
        # 16 GT/s is 2x of 8 GT/s, so bandwidth should be 2x
        assert abs(spec_16.bandwidth / spec_8.bandwidth - 2.0) < 0.01