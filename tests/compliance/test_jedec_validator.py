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
