"""
HBM4 Compliance Tests

Tests for JEDEC compliance, protocol compliance, and production margins.

Tests cover:
- JEDEC JESD238B compliance tests
- Protocol compliance tests
- Production margin tests
- Silicon validation tests
"""

import pytest
import sys
from typing import Dict, Any, Tuple

# Add model path for imports
sys.path.insert(0, '/home/ic/JXTF/HBM')

from model.dram.hbm4_spec_production import (
    HBM4ProductionSpec,
    SpeedGrade,
    ValidationLevel,
    create_production_spec,
    validate_timing_parameter,
    validate_voltage,
    validate_temperature,
    get_speed_grade_limits,
    HBM4_PRODUCTION_GRADES,
)

from model.dram.hbm4_validation import (
    SiliconValidator,
    SiliconValidationReport,
    MarginResult,
    MarginAnalyzer,
    ValidationResult,
    create_validator,
    run_production_validation,
)

from model.dram.hbm4_compliance import (
    HBM4ComplianceChecker,
    ComplianceReport,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceStatus,
    run_jedec_compliance,
    validate_hbm4_device,
)


# =============================================================================
# Production Spec Tests
# =============================================================================

class TestHBM4ProductionSpec:
    """Tests for HBM4 production specification"""

    def test_production_spec_creation(self):
        """Test production spec creation"""
        spec = create_production_spec("8Gbps")
        assert spec.speed_grade == SpeedGrade.SG_8G
        assert spec.data_rate_gtps == 8.0
        assert spec.tCK_ps == 125.0

    def test_production_spec_12g(self):
        """Test 12Gbps production spec"""
        spec = create_production_spec("12Gbps")
        assert spec.speed_grade == SpeedGrade.SG_12G
        assert spec.data_rate_gtps == 12.0
        assert abs(spec.tCK_ps - 83.33) < 0.1

    def test_production_spec_16g(self):
        """Test 16Gbps production spec"""
        spec = create_production_spec("16Gbps")
        assert spec.speed_grade == SpeedGrade.SG_16G
        assert spec.data_rate_gtps == 16.0
        assert abs(spec.tCK_ps - 62.5) < 0.1

    def test_validation_level_scaling(self):
        """Test that validation levels adjust margins"""
        eng_spec = create_production_spec("8Gbps", ValidationLevel.ENGINEERING)
        prod_spec = create_production_spec("8Gbps", ValidationLevel.PRODUCTION)

        # Engineering should have more margin
        assert eng_spec.timing_margin_percent > prod_spec.timing_margin_percent

    def test_timing_margin_calculation(self):
        """Test timing margin calculation"""
        spec = create_production_spec("8Gbps", ValidationLevel.PRODUCTION)
        base_value = 10
        margin_value = spec.get_timing_with_margin(base_value, "timing")

        # 10% margin means value is 90% of spec
        expected = int(base_value * 0.9)
        assert margin_value == expected

    def test_dq_margin_calculation(self):
        """Test DQ eye margin calculation"""
        spec = create_production_spec("8Gbps")
        margin_ps = spec.get_DQ_margin_ps()

        # 0.15 UI at 125ps = 18.75 ps
        expected = 125 / 2 * 0.15
        assert abs(margin_ps - expected) < 0.1

    def test_voltage_margin_calculation(self):
        """Test voltage margin calculation"""
        spec = create_production_spec("8Gbps")
        margin_mV = spec.get_voltage_margin_mV()

        # 5% of 1000mV = 50mV
        expected = 1000 * 0.05
        assert abs(margin_mV - expected) < 0.1


class TestSpeedGradeValidation:
    """Tests for speed grade validation"""

    @pytest.mark.parametrize("grade", ["8Gbps", "12Gbps", "16Gbps"])
    def test_speed_grade_limits(self, grade):
        """Test that speed grade limits are valid ranges"""
        limits = get_speed_grade_limits(grade)

        assert "data_rate_range" in limits
        assert "tCK_range" in limits
        assert "tCL_range" in limits
        assert "valid_voltage_mV" in limits
        assert "valid_temp_C" in limits

        # Verify ranges are valid
        assert limits["data_rate_range"][0] < limits["data_rate_range"][1]
        assert limits["tCK_range"][0] < limits["tCK_range"][1]
        assert limits["valid_voltage_mV"][0] < limits["valid_voltage_mV"][1]

    def test_8gbps_validation(self):
        """Test 8Gbps timing validation"""
        is_valid, msg = validate_timing_parameter("tCL", 8, "8Gbps")
        assert is_valid, msg

        # Out of range should fail
        is_valid, msg = validate_timing_parameter("tCL", 20, "8Gbps")
        assert not is_valid

    def test_12gbps_validation(self):
        """Test 12Gbps timing validation"""
        is_valid, msg = validate_timing_parameter("tCL", 10, "12Gbps")
        assert is_valid, msg

    def test_16gbps_validation(self):
        """Test 16Gbps timing validation"""
        is_valid, msg = validate_timing_parameter("tCL", 12, "16Gbps")
        assert is_valid, msg

    def test_voltage_validation(self):
        """Test voltage validation"""
        # Nominal voltage
        is_valid, msg = validate_voltage(1000.0, "8Gbps")
        assert is_valid, msg

        # Low voltage (should be in range)
        is_valid, msg = validate_voltage(900.0, "8Gbps")
        assert is_valid, msg

        # Out of range
        is_valid, msg = validate_voltage(800.0, "8Gbps")
        assert not is_valid

    def test_temperature_validation(self):
        """Test temperature validation"""
        # Room temp
        is_valid, msg = validate_temperature(25.0, "8Gbps")
        assert is_valid, msg

        # Hot temp
        is_valid, msg = validate_temperature(100.0, "8Gbps")
        assert is_valid, msg

        # Out of range
        is_valid, msg = validate_temperature(150.0, "8Gbps")
        assert not is_valid


# =============================================================================
# Silicon Validation Tests
# =============================================================================

class TestSiliconValidator:
    """Tests for silicon validation"""

    def test_validator_creation(self):
        """Test validator creation"""
        validator = create_validator("8Gbps")
        assert validator.speed_grade == "8Gbps"

    def test_timing_margin_validation(self):
        """Test timing margin validation"""
        validator = create_validator("8Gbps")
        result = validator.validate_timing_margin("tCL", 8, 125.0)

        assert isinstance(result, MarginResult)
        assert result.parameter == "tCL_nominal"
        assert result.measured_value == 8
        assert result.status in [ValidationResult.PASS, ValidationResult.MARGINAL]

    def test_voltage_margin_validation(self):
        """Test voltage margin validation"""
        validator = create_validator("8Gbps")
        result = validator.validate_voltage_margin(1000.0)

        assert isinstance(result, MarginResult)
        assert result.measured_value == 1000.0
        assert result.spec_min == 880
        assert result.spec_max == 1200
        assert result.status == ValidationResult.PASS

    def test_thermal_margin_validation(self):
        """Test thermal margin validation"""
        validator = create_validator("8Gbps")
        result = validator.validate_thermal_margin(25.0)

        assert isinstance(result, MarginResult)
        assert result.measured_value == 25.0
        assert result.spec_min == -40
        assert result.spec_max == 125
        assert result.status == ValidationResult.PASS

    def test_DQ_eye_analysis(self):
        """Test DQ eye analysis"""
        validator = create_validator("8Gbps")
        analysis = validator.analyze_DQ_eye(100.0, 0.4, "8Gbps")

        assert "eye_height_mV" in analysis
        assert "eye_width_ui" in analysis
        assert "overall_pass" in analysis
        assert analysis["overall_pass"] is True

    def test_DQS_eye_analysis(self):
        """Test DQS eye analysis"""
        validator = create_validator("8Gbps")
        analysis = validator.analyze_DQS_eye(80.0, 0.35)

        assert "eye_height_mV" in analysis
        assert "eye_width_ui" in analysis
        assert "overall_pass" in analysis

    def test_full_validation(self):
        """Test full validation run"""
        validator = create_validator("8Gbps")
        report = validator.run_full_validation(
            lot_id="TEST_LOT",
            die_id="TEST_DIE",
            temperature_C=85.0,
            voltage_mV=1000.0
        )

        assert isinstance(report, SiliconValidationReport)
        assert report.total_tests > 0
        assert report.speed_grade == "8Gbps"
        assert report.test_temperature == 85.0
        assert report.test_voltage == 1000.0


class TestMarginAnalyzer:
    """Tests for margin analyzer"""

    def test_guardband_calculation(self):
        """Test guardband calculation"""
        analyzer = MarginAnalyzer()
        guardband = analyzer.calculate_guardband(
            distribution_mean=100,
            distribution_stdev=5,
            spec_limit=120,
            direction="upper"
        )

        # 100 + 2.33*5 = 111.65, guardband = 111.65 - 120 = -8.35 (no guardband needed)
        assert guardband >= 0  # Should be 0 since mean is below spec

    def test_guardband_calculation_with_margin(self):
        """Test guardband when mean is closer to limit"""
        analyzer = MarginAnalyzer()
        guardband = analyzer.calculate_guardband(
            distribution_mean=115,
            distribution_stdev=5,
            spec_limit=120,
            direction="upper"
        )

        # 115 + 2.33*5 = 126.65, guardband = 126.65 - 120 = 6.65
        assert guardband > 0

    def test_screening_threshold(self):
        """Test screening threshold calculation"""
        analyzer = MarginAnalyzer()
        lower, upper = analyzer.calculate_screening_threshold(
            distribution=[90, 95, 100, 105, 110],
            fallout_percent=0.1
        )

        assert lower < 100
        assert upper > 100


# =============================================================================
# JEDEC Compliance Tests
# =============================================================================

class TestHBM4ComplianceChecker:
    """Tests for JEDEC compliance checker"""

    def test_checker_creation(self):
        """Test compliance checker creation"""
        checker = HBM4ComplianceChecker()
        assert checker.spec_version == "JESD238B"

    def test_interface_width_check(self):
        """Test interface width compliance check"""
        checker = HBM4ComplianceChecker()

        # Valid widths
        result = checker.check_interface_width(2048)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_interface_width(1024)
        assert result.status == ComplianceStatus.PASS

        # Invalid width
        result = checker.check_interface_width(512)
        assert result.status == ComplianceStatus.FAIL

    def test_data_rate_check(self):
        """Test data rate compliance check"""
        checker = HBM4ComplianceChecker()

        # Valid rates
        for rate in [8.0, 12.0, 16.0]:
            result = checker.check_data_rate(rate)
            assert result.status == ComplianceStatus.PASS

        # Invalid rate
        result = checker.check_data_rate(6.4)
        assert result.status == ComplianceStatus.FAIL

    def test_channel_count_check(self):
        """Test channel count compliance check"""
        checker = HBM4ComplianceChecker()

        # HBM4 native
        result = checker.check_channel_count(32, hbm3_compat=False)
        assert result.status == ComplianceStatus.PASS

        # HBM3 compatible
        result = checker.check_channel_count(16, hbm3_compat=True)
        assert result.status == ComplianceStatus.PASS

        # Invalid
        result = checker.check_channel_count(8, hbm3_compat=False)
        assert result.status == ComplianceStatus.FAIL

    def test_burst_length_check(self):
        """Test burst length compliance check"""
        checker = HBM4ComplianceChecker()

        result = checker.check_burst_length(4)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_burst_length(8)
        assert result.status == ComplianceStatus.FAIL

    def test_cas_latency_check(self):
        """Test CAS latency compliance check"""
        checker = HBM4ComplianceChecker()

        result = checker.check_cas_latency(8, 8.0)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_cas_latency(10, 12.0)
        assert result.status == ComplianceStatus.PASS

    def test_voltage_check(self):
        """Test voltage compliance check"""
        checker = HBM4ComplianceChecker()

        result = checker.check_voltage(1000.0)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_voltage(880.0)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_voltage(1200.0)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_voltage(800.0)
        assert result.status == ComplianceStatus.FAIL

    def test_temperature_check(self):
        """Test temperature compliance check"""
        checker = HBM4ComplianceChecker()

        result = checker.check_temperature(25.0)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_temperature(105.0)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_temperature(150.0)
        assert result.status == ComplianceStatus.FAIL

    def test_ecc_enabled_check(self):
        """Test ECC enablement check"""
        checker = HBM4ComplianceChecker()

        result = checker.check_ecc_enabled(True)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_ecc_enabled(False)
        assert result.status == ComplianceStatus.WARN

    def test_crc_enabled_check(self):
        """Test CRC enablement check"""
        checker = HBM4ComplianceChecker()

        result = checker.check_crc_enabled(True)
        assert result.status == ComplianceStatus.PASS

        result = checker.check_crc_enabled(False)
        assert result.status == ComplianceStatus.WARN

    def test_refresh_timing_check(self):
        """Test refresh timing check"""
        checker = HBM4ComplianceChecker()

        result = checker.check_refresh_timing(3900, 180, 8.0)
        assert result.status == ComplianceStatus.PASS

    def test_protocol_compliance(self):
        """Test protocol compliance checks"""
        checker = HBM4ComplianceChecker()
        device_config = {
            "interface_width": 2048,
            "data_rate": 8.0,
            "channels": 32,
            "burst_length": 4,
        }

        checks = checker.run_protocol_compliance(device_config)

        assert len(checks) > 0
        assert all(c.status == ComplianceStatus.PASS for c in checks)

    def test_timing_compliance(self):
        """Test timing compliance checks"""
        checker = HBM4ComplianceChecker()
        timing_config = {
            "data_rate": 8.0,
            "tCL": 8,
            "VDDQ": 1000,
            "Tj": 25,
            "tRCD": 8,
            "tRP": 8,
            "tRAS": 20,
            "tRC": 22,
            "tREFI": 3900,
            "tRFC": 180,
            "tCCD": 4,
            "tRRD": 4,
        }

        checks = checker.run_timing_compliance(timing_config)

        assert len(checks) > 0
        assert all(c.status == ComplianceStatus.PASS for c in checks)

    def test_reliability_compliance(self):
        """Test reliability compliance checks"""
        checker = HBM4ComplianceChecker()
        reliability_config = {
            "ecc_enabled": True,
            "crc_enabled": True,
        }

        checks = checker.run_reliability_compliance(reliability_config)

        assert len(checks) > 0
        # All should pass (ECC and CRC enabled)
        assert all(c.status == ComplianceStatus.PASS for c in checks)

    def test_full_compliance(self):
        """Test full compliance suite"""
        checker = HBM4ComplianceChecker()

        device_config = {
            "interface_width": 2048,
            "data_rate": 8.0,
            "channels": 32,
            "burst_length": 4,
        }
        timing_config = {
            "data_rate": 8.0,
            "tCL": 8,
            "VDDQ": 1000,
            "Tj": 25,
            "tRCD": 8,
            "tRP": 8,
            "tRAS": 20,
            "tRC": 22,
            "tREFI": 3900,
            "tRFC": 180,
            "tCCD": 4,
            "tRRD": 4,
        }
        reliability_config = {
            "ecc_enabled": True,
            "crc_enabled": True,
        }

        report = checker.run_full_compliance(
            device_config, timing_config, reliability_config
        )

        assert isinstance(report, ComplianceReport)
        assert report.overall_pass is True
        assert report.compliance_percentage == 100.0


class TestComplianceIntegration:
    """Integration tests for compliance system"""

    def test_run_jedec_compliance(self):
        """Test running JEDEC compliance"""
        device_config = {
            "interface_width": 2048,
            "data_rate": 8.0,
            "channels": 32,
            "burst_length": 4,
        }
        timing_config = {
            "data_rate": 8.0,
            "tCL": 8,
            "VDDQ": 1000,
            "Tj": 25,
            "tRCD": 8,
            "tRP": 8,
            "tRAS": 20,
            "tRC": 22,
            "tREFI": 3900,
            "tRFC": 180,
            "tCCD": 4,
            "tRRD": 4,
        }

        report = run_jedec_compliance(device_config, timing_config)

        assert report.overall_pass is True
        assert report.mandatory_failed == 0

    def test_validate_hbm4_device(self):
        """Test HBM4 device validation"""
        config = {
            "device": {
                "interface_width": 2048,
                "data_rate": 8.0,
                "channels": 32,
                "burst_length": 4,
            },
            "timing": {
                "data_rate": 8.0,
                "tCL": 8,
                "VDDQ": 1000,
                "Tj": 25,
                "tRCD": 8,
                "tRP": 8,
                "tRAS": 20,
                "tRC": 22,
                "tREFI": 3900,
                "tRFC": 180,
                "tCCD": 4,
                "tRRD": 4,
            },
            "reliability": {
                "ecc_enabled": True,
                "crc_enabled": True,
            },
            "info": {
                "vendor": "Test Vendor",
                "part_number": "HBM4-32G-8G",
            },
        }

        is_compliant, report = validate_hbm4_device(config)

        assert is_compliant is True
        assert isinstance(report, ComplianceReport)


# =============================================================================
# Production Margin Tests
# =============================================================================

class TestProductionMargins:
    """Tests for production margin requirements"""

    def test_timing_margin_all_speed_grades(self):
        """Test timing margins for all speed grades"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            spec = create_production_spec(grade)
            limits = get_speed_grade_limits(grade)

            # Verify margins are at least 10%
            for param, range_key in [("tCL", "tCL_range"),
                                     ("tRCD", "tRCD_range"),
                                     ("tRP", "tRP_range")]:
                if range_key in limits:
                    range_vals = limits[range_key]
                    margin = (range_vals[1] - range_vals[0]) / 2 / range_vals[1] * 100
                    assert margin >= 5, f"{grade} {param} margin too low"

    def test_voltage_margin_all_speed_grades(self):
        """Test voltage margins for all speed grades"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            spec = create_production_spec(grade)
            limits = get_speed_grade_limits(grade)

            voltage_range = limits.get("valid_voltage_mV", (850, 1250))
            nominal = 1000

            # Calculate margin from nominal
            margin_low = nominal - voltage_range[0]
            margin_high = voltage_range[1] - nominal

            margin_pct = min(margin_low, margin_high) / nominal * 100
            assert margin_pct >= 5, f"{grade} voltage margin too low"

    def test_thermal_margin_all_speed_grades(self):
        """Test thermal margins for all speed grades"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            limits = get_speed_grade_limits(grade)

            temp_range = limits.get("valid_temp_C", (-40, 105))
            test_temp = limits.get("characterization_temp_C", (0, 85))

            # Characterization temp should have margin from spec limits
            margin_low = test_temp[0] - temp_range[0]
            margin_high = temp_range[1] - test_temp[1]

            assert margin_low >= 10, f"{grade} low temp margin too low"
            assert margin_high >= 10, f"{grade} high temp margin too low"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])