# tests/compliance/test_integration.py
"""Integration tests for compliance modules"""

import pytest
from model.compliance.jedec_validator import (
    JEDECValidator,
    ComplianceLevel,
    ComplianceCheck,
)
from model.compliance.hbm3_compatibility import (
    HBM3CompatibilityChecker,
    CompatibilityResult,
)


class TestComplianceIntegration:
    """Integration tests for compliance checking pipeline"""

    def test_full_compliance_pipeline(self):
        """Test complete compliance validation pipeline"""
        validator = JEDECValidator()

        # Validate timing parameters
        timing_checks = validator.validate_timing(
            tRCD_ns=10.0,
            tRP_ns=10.0,
            tRAS_ns=25.0,
            tRC_ns=35.0
        )

        # Validate power parameters
        power_checks = validator.validate_power(
            active_power_w=15.0,
            idle_power_w=2.0
        )

        # Combine all checks
        all_checks = timing_checks + power_checks

        # Verify no failures
        failures = [c for c in all_checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 0

    def test_jedec_plus_hbm3_compatibility(self):
        """Test JEDEC validation combined with HBM3 compatibility"""
        validator = JEDECValidator()
        hbm3_checker = HBM3CompatibilityChecker()

        # JEDEC configuration
        jedec_config = {
            "tRCD_ns": 10.0,
            "tRP_ns": 10.0,
            "tRAS_ns": 25.0,
            "tRC_ns": 35.0,
            "active_power_w": 15.0,
            "idle_power_w": 2.0
        }

        # HBM3 compatibility configuration
        hbm3_config = {
            "mode": "HBM3_LEGACY",
            "tRCD_ns": 10.0
        }

        # Run both validations
        jedec_checks = validator.run_all_checks(jedec_config)
        hbm3_results = hbm3_checker.check_all(hbm3_config)

        # Verify JEDEC compliance
        jedec_failures = [c for c in jedec_checks if c.level == ComplianceLevel.FAIL]
        assert len(jedec_failures) == 0

        # Verify HBM3 compatibility
        incompatible = [r for r in hbm3_results if not r.compatible]
        assert len(incompatible) == 0

    def test_mode_support_validation(self):
        """Test HBM3 compatibility mode support checking"""
        checker = HBM3CompatibilityChecker()

        # Test HBM3 compatible modes
        for mode in ["HBM3_LEGACY", "HBM3_COMPAT"]:
            result = checker.check_mode_support(mode)
            assert result.compatible is True
            assert "compatible" in result.notes.lower()

        # Test HBM4 mode (not compatible with HBM3)
        result = checker.check_mode_support("HBM4")
        assert result.compatible is False

    def test_timing_compatibility_validation(self):
        """Test timing parameter compatibility checking"""
        checker = HBM3CompatibilityChecker()

        # Test compatible timing
        result = checker.check_timing_compatibility(hbm4_tRCD=10.0, hbm3_tRCD=10.0)
        assert result.compatible is True

        # Test marginal compatibility (within 2ns)
        result = checker.check_timing_compatibility(hbm4_tRCD=11.0, hbm3_tRCD=10.0)
        assert result.compatible is True

        # Test incompatible timing (difference > 2ns)
        result = checker.check_timing_compatibility(hbm4_tRCD=15.0, hbm3_tRCD=10.0)
        assert result.compatible is False

    def test_timing_validation_pass(self):
        """Test JEDEC timing validation with valid parameters"""
        validator = JEDECValidator()

        checks = validator.validate_timing(
            tRCD_ns=12.0,
            tRP_ns=10.0,
            tRAS_ns=30.0,
            tRC_ns=45.0
        )

        # tRC >= tRAS + tRP (45 >= 40) should pass
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 0

    def test_timing_validation_fail(self):
        """Test JEDEC timing validation catches violations"""
        validator = JEDECValidator()

        checks = validator.validate_timing(
            tRCD_ns=10.0,
            tRP_ns=10.0,
            tRAS_ns=30.0,
            tRC_ns=35.0  # tRC < tRAS + tRP (35 < 40)
        )

        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 1
        assert "tRC" in failures[0].message

    def test_power_validation_pass(self):
        """Test JEDEC power validation with valid parameters"""
        validator = JEDECValidator()

        checks = validator.validate_power(
            active_power_w=30.0,
            idle_power_w=5.0
        )

        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]

        assert len(failures) == 0
        # Idle power 5/30 = 16.7% < 20%, should not warn
        assert len(warnings) == 0

    def test_power_validation_exceed_max(self):
        """Test JEDEC power validation catches exceeding max power"""
        validator = JEDECValidator()

        checks = validator.validate_power(
            active_power_w=60.0,  # Exceeds default 50W max
            idle_power_w=5.0
        )

        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 1
        assert "active_power" in failures[0].check_name

    def test_power_validation_high_idle(self):
        """Test JEDEC power validation catches high idle power"""
        validator = JEDECValidator()

        checks = validator.validate_power(
            active_power_w=10.0,
            idle_power_w=3.0  # 30% > 20%, triggers warning
        )

        warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]
        assert len(warnings) == 1
        assert "idle_power" in warnings[0].check_name

    def test_timing_range_warnings(self):
        """Test timing parameter range warnings"""
        validator = JEDECValidator()

        # tRCD too low
        checks = validator.validate_timing(
            tRCD_ns=5.0,  # Below 8ns range
            tRP_ns=10.0,
            tRAS_ns=25.0,
            tRC_ns=35.0
        )

        warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]
        assert len(warnings) >= 1
        assert any("tRCD" in w.message for w in warnings)

    def test_timing_range_warnings_high(self):
        """Test timing parameter range warnings for high values"""
        validator = JEDECValidator()

        # tRP too high
        checks = validator.validate_timing(
            tRCD_ns=10.0,
            tRP_ns=25.0,  # Above 20ns range
            tRAS_ns=25.0,
            tRC_ns=50.0
        )

        warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]
        assert len(warnings) >= 1
        assert any("tRP" in w.message for w in warnings)

    def test_compliance_check_dataclass(self):
        """Test ComplianceCheck dataclass attributes"""
        check = ComplianceCheck(
            check_name="test_check",
            level=ComplianceLevel.WARNING,
            message="Test message",
            details={"key": "value", "count": 5}
        )

        assert check.check_name == "test_check"
        assert check.level == ComplianceLevel.WARNING
        assert check.message == "Test message"
        assert check.details["key"] == "value"
        assert check.details["count"] == 5

    def test_compatibility_result_dataclass(self):
        """Test CompatibilityResult dataclass attributes"""
        result = CompatibilityResult(
            feature="Timing Parameters",
            compatible=True,
            notes="All timing parameters compatible"
        )

        assert result.feature == "Timing Parameters"
        assert result.compatible is True
        assert "compatible" in result.notes.lower()

    def test_compliance_level_enum(self):
        """Test ComplianceLevel enum values"""
        assert ComplianceLevel.PASS.value == "pass"
        assert ComplianceLevel.WARNING.value == "warning"
        assert ComplianceLevel.FAIL.value == "fail"

    def test_run_all_checks_combined(self):
        """Test run_all_checks with combined validations"""
        validator = JEDECValidator()

        config = {
            "tRCD_ns": 10.0,
            "tRP_ns": 10.0,
            "tRAS_ns": 25.0,
            "tRC_ns": 35.0,
            "active_power_w": 15.0,
            "idle_power_w": 2.0
        }

        checks = validator.run_all_checks(config)

        # Valid config produces no FAILs (warnings optional)
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 0

        # With valid config, we may get empty checks list (no violations)
        # or checks for range warnings if any parameters are outside typical range
        assert isinstance(checks, list)

    def test_invalid_config_detection(self):
        """Test detection of invalid configuration"""
        validator = JEDECValidator()

        # Config with multiple violations
        config = {
            "tRCD_ns": 10.0,
            "tRP_ns": 10.0,
            "tRAS_ns": 25.0,
            "tRC_ns": 30.0,  # FAIL: tRC < tRAS + tRP
            "active_power_w": 60.0,  # FAIL: exceeds max
            "idle_power_w": 5.0
        }

        checks = validator.run_all_checks(config)
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]

        # Should detect at least 2 failures
        assert len(failures) >= 2

    def test_hbm3_check_all(self):
        """Test HBM3 compatibility check_all method"""
        checker = HBM3CompatibilityChecker()

        config = {
            "mode": "HBM3_LEGACY",
            "tRCD_ns": 10.0
        }

        results = checker.check_all(config)

        assert len(results) >= 2  # At least mode and timing checks
        # All should be compatible for this config
        incompatible = [r for r in results if not r.compatible]
        assert len(incompatible) == 0

    def test_incompatible_hbm3_mode(self):
        """Test HBM3 compatibility with incompatible mode"""
        checker = HBM3CompatibilityChecker()

        config = {
            "mode": "HBM4",  # Not compatible with HBM3
            "tRCD_ns": 10.0
        }

        results = checker.check_all(config)

        # Should have at least one incompatible result
        incompatible = [r for r in results if not r.compatible]
        assert len(incompatible) >= 1

    def test_validator_initialization(self):
        """Test validator initializes correctly"""
        validator = JEDECValidator()
        assert validator.checks == []

    def test_hbm3_checker_initialization(self):
        """Test HBM3 checker initializes correctly"""
        checker = HBM3CompatibilityChecker()
        assert checker.results == []