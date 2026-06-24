"""
Tests for HBM4 Production Specification

Covers model/dram/hbm4_spec_production.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from model.dram.hbm4_spec_production import (
    SpeedGrade, ValidationLevel, HBM4ProductionSpec,
    HBM4_PRODUCTION_GRADES, create_production_spec, get_speed_grade_limits,
    validate_timing_parameter, validate_voltage, validate_temperature,
    speed_grade_enum_name
)


class TestSpeedGrade:
    """Test SpeedGrade enum"""

    def test_speed_grade_values(self):
        assert SpeedGrade.SG_8G.value == "8Gbps"
        assert SpeedGrade.SG_12G.value == "12Gbps"
        assert SpeedGrade.SG_16G.value == "16Gbps"


class TestValidationLevel:
    """Test ValidationLevel enum"""

    def test_validation_level_values(self):
        assert ValidationLevel.ENGINEERING.value == "engineering"
        assert ValidationLevel.QUALIFICATION.value == "qualification"
        assert ValidationLevel.PRODUCTION.value == "production"
        assert ValidationLevel.AUTO_QUAL.value == "auto_qual"


class TestHBM4ProductionSpec:
    """Test HBM4ProductionSpec dataclass"""

    def test_default_spec(self):
        spec = HBM4ProductionSpec()
        assert spec.channels == 32
        assert spec.pseudo_channels_per_channel == 2
        assert spec.banks_per_pseudo_channel == 16
        assert spec.bank_groups_per_channel == 8
        assert spec.io_width == 2048
        assert spec.speed_grade == SpeedGrade.SG_8G
        assert spec.data_rate_gtps == 8.0
        assert spec.tCK_ps == 125.0

    def test_timing_margins(self):
        spec = HBM4ProductionSpec()
        assert spec.timing_margin_percent == 10.0
        assert spec.voltage_margin_percent == 5.0
        assert spec.temperature_margin_celsius == 15.0

    def test_read_write_margins(self):
        spec = HBM4ProductionSpec()
        assert spec.read_margin_ui == 0.15
        assert spec.write_margin_ui == 0.15
        assert spec.DQS_margin_ui == 0.20

    def test_validation_limits(self):
        spec = HBM4ProductionSpec()
        assert spec.max_read_latency_cycles == 20
        assert spec.max_write_latency_cycles == 12
        assert spec.min_tRP_cycles == 6
        assert spec.min_tRAS_cycles == 16
        assert spec.min_tRC_cycles == 18

    def test_speed_grade_validation_ranges(self):
        spec = HBM4ProductionSpec()

        sg_8g = spec.speed_grade_validation[SpeedGrade.SG_8G]
        assert sg_8g["data_rate_range"] == (7.6, 8.4)
        assert sg_8g["tCK_range"] == (119.0, 131.6)
        assert sg_8g["tCL_range"] == (6, 12)

        sg_12g = spec.speed_grade_validation[SpeedGrade.SG_12G]
        assert sg_12g["data_rate_range"] == (11.4, 12.6)

        sg_16g = spec.speed_grade_validation[SpeedGrade.SG_16G]
        assert sg_16g["data_rate_range"] == (15.2, 16.8)

    def test_reliability_limits(self):
        spec = HBM4ProductionSpec()
        assert spec.refresh_temp_threshold_C == 85.0
        assert spec.operating_voltage_max_mV == 1200
        assert spec.operating_voltage_nom_mV == 1000
        assert spec.operating_voltage_min_mV == 880
        assert spec.junction_temp_max_C == 105
        assert spec.junction_temp_hot_C == 115
        assert spec.thermal_resistance_C_per_W == 2.5

    def test_error_detection(self):
        spec = HBM4ProductionSpec()
        assert spec.ecc_enabled is True
        assert spec.crc_enabled is True
        assert spec.crc_polynomial == 0x1D
        assert spec.ecc_scrub_interval_cycles == 1000000

    def test_dram_array_margins(self):
        spec = HBM4ProductionSpec()
        assert spec.sense_amp_offset_mV == 30.0
        assert spec.wordline_margin_mV == 50.0
        assert spec.bitline_margin_mV == 40.0
        assert spec.ref_vref_tolerance_mV == 20.0

    def test_get_timing_with_margin_timing(self):
        spec = HBM4ProductionSpec()
        result = spec.get_timing_with_margin(100, "timing")
        # 10% margin: 100 * (1 - 0.10) = 90
        assert result == 90

    def test_get_timing_with_margin_voltage(self):
        spec = HBM4ProductionSpec()
        result = spec.get_timing_with_margin(100, "voltage")
        # 5% margin: 100 * (1 - 0.05) = 95
        assert result == 95

    def test_get_timing_with_margin_other(self):
        spec = HBM4ProductionSpec()
        result = spec.get_timing_with_margin(100, "other")
        assert result == 100

    def test_get_valid_timing_range(self):
        spec = HBM4ProductionSpec()
        min_val, max_val = spec.get_valid_timing_range("tCL", 8)
        # min = 8 * (1 - 0.10) = 7.2 -> 7
        # max = 8
        assert min_val == 7
        assert max_val == 8

    def test_get_DQ_margin_ps(self):
        spec = HBM4ProductionSpec(tCK_ps=125.0)
        margin = spec.get_DQ_margin_ps()
        # UI = 125 / 2 = 62.5 ps
        # margin = 62.5 * 0.15 = 9.375 ps
        assert margin == pytest.approx(9.375, rel=0.01)

    def test_get_DQS_margin_ps(self):
        spec = HBM4ProductionSpec(tCK_ps=125.0)
        margin = spec.get_DQS_margin_ps()
        # UI = 125 / 2 = 62.5 ps
        # margin = 62.5 * 0.20 = 12.5 ps
        assert margin == pytest.approx(12.5, rel=0.01)

    def test_get_voltage_margin_mV(self):
        spec = HBM4ProductionSpec()
        margin = spec.get_voltage_margin_mV()
        # 1000 * 0.05 = 50 mV
        assert margin == 50.0


class TestProductionGrades:
    """Test HBM4_PRODUCTION_GRADES"""

    def test_8gbps_grade(self):
        grade = HBM4_PRODUCTION_GRADES["8Gbps"]
        assert grade["speed_grade"] == SpeedGrade.SG_8G
        assert grade["data_rate_gtps"] == 8.0
        assert grade["tCK_ps"] == 125.0
        assert grade["tCL_cycles"] == 8
        assert grade["tRCD_cycles"] == 8
        assert grade["tRP_cycles"] == 8
        assert grade["tRAS_cycles"] == 20
        assert grade["tRC_cycles"] == 22
        assert grade["voltage_mV"] == 1000

    def test_12gbps_grade(self):
        grade = HBM4_PRODUCTION_GRADES["12Gbps"]
        assert grade["speed_grade"] == SpeedGrade.SG_12G
        assert grade["data_rate_gtps"] == 12.0
        assert grade["tCK_ps"] == pytest.approx(83.33, rel=0.01)
        assert grade["tCL_cycles"] == 10
        assert grade["tRCD_cycles"] == 10
        assert grade["tRP_cycles"] == 10
        assert grade["tRAS_cycles"] == 24
        assert grade["tRC_cycles"] == 26

    def test_16gbps_grade(self):
        grade = HBM4_PRODUCTION_GRADES["16Gbps"]
        assert grade["speed_grade"] == SpeedGrade.SG_16G
        assert grade["data_rate_gtps"] == 16.0
        assert grade["tCK_ps"] == 62.5
        assert grade["tCL_cycles"] == 12
        assert grade["tRCD_cycles"] == 12
        assert grade["tRP_cycles"] == 12
        assert grade["tRAS_cycles"] == 28
        assert grade["tRC_cycles"] == 30


class TestCreateProductionSpec:
    """Test create_production_spec function"""

    def test_create_8gbps_production(self):
        spec = create_production_spec("8Gbps")
        assert spec.speed_grade == SpeedGrade.SG_8G
        assert spec.data_rate_gtps == 8.0
        assert spec.tCK_ps == 125.0

    def test_create_12gbps_production(self):
        spec = create_production_spec("12Gbps")
        assert spec.speed_grade == SpeedGrade.SG_12G
        assert spec.data_rate_gtps == 12.0

    def test_create_16gbps_production(self):
        spec = create_production_spec("16Gbps")
        assert spec.speed_grade == SpeedGrade.SG_16G
        assert spec.data_rate_gtps == 16.0

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError):
            create_production_spec("invalid")

    def test_create_with_validation_level(self):
        spec = create_production_spec("8Gbps", ValidationLevel.ENGINEERING)
        # Engineering uses 1.5x margin
        assert spec.timing_margin_percent == pytest.approx(15.0, rel=0.01)

    def test_create_qualification_level(self):
        spec = create_production_spec("8Gbps", ValidationLevel.QUALIFICATION)
        # Qualification uses 1.2x margin
        assert spec.timing_margin_percent == pytest.approx(12.0, rel=0.01)

    def test_create_auto_qual_level(self):
        spec = create_production_spec("8Gbps", ValidationLevel.AUTO_QUAL)
        # Auto-Qual uses 0.9x margin
        assert spec.timing_margin_percent == pytest.approx(9.0, rel=0.01)


class TestGetSpeedGradeLimits:
    """Test get_speed_grade_limits function"""

    def test_8gbps_limits(self):
        limits = get_speed_grade_limits("8Gbps")
        assert "data_rate_range" in limits
        assert "tCK_range" in limits
        assert "tCL_range" in limits
        assert "tRCD_range" in limits
        assert "tRP_range" in limits
        assert "tRAS_range" in limits
        assert "tRC_range" in limits
        assert "valid_voltage_mV" in limits
        assert "valid_temp_C" in limits

    def test_12gbps_limits(self):
        limits = get_speed_grade_limits("12Gbps")
        assert limits["data_rate_range"] == (11.4, 12.6)

    def test_16gbps_limits(self):
        limits = get_speed_grade_limits("16Gbps")
        assert limits["data_rate_range"] == (15.2, 16.8)


class TestValidateTimingParameter:
    """Test validate_timing_parameter function"""

    def test_validate_tCL_valid(self):
        ok, msg = validate_timing_parameter("tCL", 8, "8Gbps")
        assert ok is True

    def test_validate_tCL_invalid(self):
        ok, msg = validate_timing_parameter("tCL", 2, "8Gbps")
        assert ok is False

    def test_validate_tRCD_valid(self):
        ok, msg = validate_timing_parameter("tRCD", 8, "8Gbps")
        assert ok is True

    def test_validate_tRCD_at_boundary(self):
        limits = get_speed_grade_limits("8Gbps")
        min_val = limits["tRCD_range"][0]
        ok, msg = validate_timing_parameter("tRCD", min_val, "8Gbps")
        assert ok is True

    def test_validate_unknown_param(self):
        ok, msg = validate_timing_parameter("unknown", 8, "8Gbps")
        assert ok is False

    def test_validate_tRAS_valid(self):
        ok, msg = validate_timing_parameter("tRAS", 20, "8Gbps")
        assert ok is True

    def test_validate_tRAS_invalid(self):
        ok, msg = validate_timing_parameter("tRAS", 10, "8Gbps")
        assert ok is False

    def test_validate_tRC_valid(self):
        ok, msg = validate_timing_parameter("tRC", 22, "8Gbps")
        assert ok is True

    def test_validate_16gbps_timing(self):
        # Higher speed grades have tighter ranges
        ok, msg = validate_timing_parameter("tCL", 12, "16Gbps")
        assert ok is True


class TestValidateVoltage:
    """Test validate_voltage function"""

    def test_validate_nominal_voltage(self):
        ok, msg = validate_voltage(1000, "8Gbps")
        assert ok is True

    def test_validate_min_voltage(self):
        ok, msg = validate_voltage(880, "8Gbps")
        assert ok is True

    def test_validate_max_voltage(self):
        ok, msg = validate_voltage(1200, "8Gbps")
        assert ok is True

    def test_validate_below_min_voltage(self):
        ok, msg = validate_voltage(850, "8Gbps")
        assert ok is False

    def test_validate_above_max_voltage(self):
        ok, msg = validate_voltage(1250, "8Gbps")
        assert ok is False

    def test_validate_voltage_16gbps(self):
        ok, msg = validate_voltage(1000, "16Gbps")
        assert ok is True


class TestValidateTemperature:
    """Test validate_temperature function"""

    def test_validate_room_temp(self):
        ok, msg = validate_temperature(25, "8Gbps")
        assert ok is True

    def test_validate_min_temp(self):
        ok, msg = validate_temperature(-40, "8Gbps")
        assert ok is True

    def test_validate_max_temp(self):
        ok, msg = validate_temperature(105, "8Gbps")
        assert ok is True

    def test_validate_below_min_temp(self):
        ok, msg = validate_temperature(-50, "8Gbps")
        assert ok is False

    def test_validate_above_max_temp(self):
        ok, msg = validate_temperature(130, "8Gbps")
        assert ok is False


class TestSpeedGradeEnumName:
    """Test speed_grade_enum_name function"""

    def test_8gbps(self):
        assert speed_grade_enum_name("8Gbps") == "SG_8G"

    def test_12gbps(self):
        assert speed_grade_enum_name("12Gbps") == "SG_12G"

    def test_16gbps(self):
        assert speed_grade_enum_name("16Gbps") == "SG_16G"

    def test_unknown(self):
        assert speed_grade_enum_name("unknown") == "unknown"


class TestIntegration:
    """Integration tests for production specs"""

    def test_full_production_validation_8gbps(self):
        """Test complete validation flow for 8Gbps"""
        spec = create_production_spec("8Gbps", ValidationLevel.PRODUCTION)

        # Validate timing parameters
        assert validate_timing_parameter("tCL", 8, "8Gbps")[0]
        assert validate_timing_parameter("tRCD", 8, "8Gbps")[0]
        assert validate_timing_parameter("tRP", 8, "8Gbps")[0]
        assert validate_timing_parameter("tRAS", 20, "8Gbps")[0]
        assert validate_timing_parameter("tRC", 22, "8Gbps")[0]

        # Validate voltage
        assert validate_voltage(1000, "8Gbps")[0]
        assert validate_voltage(880, "8Gbps")[0]
        assert validate_voltage(1200, "8Gbps")[0]

        # Validate temperature
        assert validate_temperature(25, "8Gbps")[0]
        assert validate_temperature(85, "8Gbps")[0]

    def test_full_production_validation_16gbps(self):
        """Test complete validation flow for 16Gbps"""
        spec = create_production_spec("16Gbps", ValidationLevel.PRODUCTION)

        # Validate timing parameters
        assert validate_timing_parameter("tCL", 12, "16Gbps")[0]
        assert validate_timing_parameter("tRCD", 12, "16Gbps")[0]
        assert validate_timing_parameter("tRP", 12, "16Gbps")[0]
        assert validate_timing_parameter("tRAS", 28, "16Gbps")[0]
        assert validate_timing_parameter("tRC", 30, "16Gbps")[0]

    def test_margin_calculations(self):
        """Test margin calculations across speed grades"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            spec = create_production_spec(grade)
            # DQ margin should scale with speed
            dq_margin = spec.get_DQ_margin_ps()
            dqs_margin = spec.get_DQS_margin_ps()
            voltage_margin = spec.get_voltage_margin_mV()

            assert dq_margin > 0
            assert dqs_margin > 0
            assert voltage_margin > 0

    def test_timing_margin_application(self):
        """Test timing margin application"""
        spec = create_production_spec("8Gbps", ValidationLevel.PRODUCTION)

        # With 10% margin
        base_value = 100
        result = spec.get_timing_with_margin(base_value, "timing")
        assert result == 90

    def test_auto_qual_tighter_margins(self):
        """Test Auto-Qual has tighter margins"""
        prod_spec = create_production_spec("8Gbps", ValidationLevel.PRODUCTION)
        auto_spec = create_production_spec("8Gbps", ValidationLevel.AUTO_QUAL)

        # Auto-Qual should have tighter margins (0.9x)
        assert auto_spec.timing_margin_percent < prod_spec.timing_margin_percent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
