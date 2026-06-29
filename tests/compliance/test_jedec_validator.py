import pytest
from model.compliance.jedec_validator import (
    JEDECValidator, ComplianceLevel, ComplianceCheck
)


class TestJEDECValidator:
    def test_timing_pass(self):
        validator = JEDECValidator()
        checks = validator.validate_timing(10.0, 10.0, 25.0, 35.0)
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 0

    def test_timing_fail(self):
        validator = JEDECValidator()
        checks = validator.validate_timing(10.0, 10.0, 25.0, 30.0)  # tRC < tRAS + tRP
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 1

    def test_power_fail(self):
        validator = JEDECValidator()
        checks = validator.validate_power(60.0, 2.0)  # Exceeds max
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 1

    def test_power_pass(self):
        validator = JEDECValidator()
        checks = validator.validate_power(10.0, 2.0)
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 0

    def test_timing_warning_range(self):
        validator = JEDECValidator()
        checks = validator.validate_timing(6.0, 10.0, 25.0, 35.0)  # tRCD too low
        warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]
        assert len(warnings) == 1
        assert "tRCD" in warnings[0].message

    def test_run_all_checks(self):
        validator = JEDECValidator()
        config = {
            "tRCD_ns": 10.0,
            "tRP_ns": 10.0,
            "tRAS_ns": 25.0,
            "tRC_ns": 35.0,
            "active_power_w": 10.0,
            "idle_power_w": 2.0
        }
        # Valid config produces no FAILs (warnings optional)
        checks = validator.run_all_checks(config)
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 0

    def test_run_all_checks_detects_violations(self):
        validator = JEDECValidator()
        config = {
            "tRCD_ns": 10.0,
            "tRP_ns": 10.0,
            "tRAS_ns": 25.0,
            "tRC_ns": 30.0,  # tRC < tRAS + tRP -> FAIL
            "active_power_w": 60.0,  # Exceeds max -> FAIL
            "idle_power_w": 2.0
        }
        checks = validator.run_all_checks(config)
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) >= 1

    def test_timing_tRCD_out_of_range(self):
        """tRCD outside typical range triggers warning"""
        validator = JEDECValidator()
        checks = validator.validate_timing(5.0, 10.0, 25.0, 35.0)  # tRCD=5ns too low
        warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]
        assert len(warnings) == 1
        assert warnings[0].check_name == "tRCD_timing"

    def test_timing_tRP_out_of_range(self):
        """tRP outside typical range triggers warning"""
        validator = JEDECValidator()
        checks = validator.validate_timing(10.0, 25.0, 25.0, 35.0)  # tRP=25ns too high
        warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]
        assert len(warnings) == 1
        assert warnings[0].check_name == "tRP_timing"

    def test_power_idle_high_warning(self):
        """Idle power > 20% of active triggers warning"""
        validator = JEDECValidator()
        checks = validator.validate_power(10.0, 3.0)  # 30% ratio
        warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]
        assert len(warnings) == 1
        assert warnings[0].check_name == "idle_power"

    def test_power_acceptable(self):
        """Valid power levels pass with no warnings/failures"""
        validator = JEDECValidator()
        checks = validator.validate_power(30.0, 5.0)  # Within limits
        issues = [c for c in checks if c.level in (ComplianceLevel.WARNING, ComplianceLevel.FAIL)]
        assert len(issues) == 0

    def test_compliance_check_dataclass(self):
        """ComplianceCheck stores all fields correctly"""
        check = ComplianceCheck(
            check_name="test_check",
            level=ComplianceLevel.WARNING,
            message="Test message",
            details={"key": "value"}
        )
        assert check.check_name == "test_check"
        assert check.level == ComplianceLevel.WARNING
        assert check.message == "Test message"
        assert check.details == {"key": "value"}

    def test_compliance_level_enum(self):
        """ComplianceLevel enum has correct values"""
        assert ComplianceLevel.PASS.value == "pass"
        assert ComplianceLevel.WARNING.value == "warning"
        assert ComplianceLevel.FAIL.value == "fail"

    def test_validator_initial_state(self):
        """JEDECValidator initializes with empty checks list"""
        validator = JEDECValidator()
        assert validator.checks == []

    def test_default_config_values(self):
        """run_all_checks uses correct defaults when config missing keys"""
        validator = JEDECValidator()
        checks = validator.run_all_checks({})  # Empty config
        # Should use defaults without crashing
        assert isinstance(checks, list)
