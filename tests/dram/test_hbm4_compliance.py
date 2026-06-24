"""
Tests for HBM4 JEDEC Compliance Checker

Covers model/dram/hbm4_compliance.py
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from model.dram.hbm4_compliance import (
    ComplianceLevel, ComplianceStatus, ComplianceCheck, ComplianceReport,
    HBM4ComplianceChecker, run_jedec_compliance, validate_hbm4_device
)


class TestComplianceLevel:
    """Test ComplianceLevel enum"""

    def test_compliance_level_values(self):
        assert ComplianceLevel.MANDATORY.value == "mandatory"
        assert ComplianceLevel.RECOMMENDED.value == "recommended"
        assert ComplianceLevel.OPTIONAL.value == "optional"


class TestComplianceStatus:
    """Test ComplianceStatus enum"""

    def test_compliance_status_values(self):
        assert ComplianceStatus.PASS.value == "pass"
        assert ComplianceStatus.FAIL.value == "fail"
        assert ComplianceStatus.SKIP.value == "skip"
        assert ComplianceStatus.WARN.value == "warn"


class TestComplianceCheck:
    """Test ComplianceCheck dataclass"""

    def test_creation(self):
        check = ComplianceCheck(
            check_id="TEST_001",
            description="Test compliance check",
            level=ComplianceLevel.MANDATORY,
            status=ComplianceStatus.PASS,
            details="Test passed",
            spec_reference="JESD238B Section 1.0"
        )
        assert check.check_id == "TEST_001"
        assert check.level == ComplianceLevel.MANDATORY
        assert check.status == ComplianceStatus.PASS

    def test_to_dict(self):
        check = ComplianceCheck(
            check_id="TEST_001",
            description="Test compliance check",
            level=ComplianceLevel.MANDATORY,
            status=ComplianceStatus.PASS,
            details="Test passed",
            spec_reference="JESD238B Section 1.0",
            measured_value=100,
            expected_value=100
        )
        d = check.to_dict()
        assert d["check_id"] == "TEST_001"
        assert d["level"] == "mandatory"
        assert d["status"] == "pass"


class TestComplianceReport:
    """Test ComplianceReport dataclass"""

    def test_creation(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={"model": "HBM4-8G"}
        )
        assert report.spec_version == "JESD238B"
        assert len(report.checks) == 0
        assert report.mandatory_passed == 0
        assert report.mandatory_failed == 0

    def test_add_check_mandatory_pass(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        check = ComplianceCheck(
            check_id="TEST_001",
            description="Test",
            level=ComplianceLevel.MANDATORY,
            status=ComplianceStatus.PASS,
            details="Passed",
            spec_reference="Test"
        )
        report.add_check(check)
        assert report.mandatory_passed == 1
        assert report.mandatory_failed == 0

    def test_add_check_mandatory_fail(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        check = ComplianceCheck(
            check_id="TEST_001",
            description="Test",
            level=ComplianceLevel.MANDATORY,
            status=ComplianceStatus.FAIL,
            details="Failed",
            spec_reference="Test"
        )
        report.add_check(check)
        assert report.mandatory_passed == 0
        assert report.mandatory_failed == 1

    def test_add_check_recommended(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        check = ComplianceCheck(
            check_id="TEST_001",
            description="Test",
            level=ComplianceLevel.RECOMMENDED,
            status=ComplianceStatus.PASS,
            details="Passed",
            spec_reference="Test"
        )
        report.add_check(check)
        assert report.recommended_passed == 1
        assert report.recommended_failed == 0

    def test_add_check_optional(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        check = ComplianceCheck(
            check_id="TEST_001",
            description="Test",
            level=ComplianceLevel.OPTIONAL,
            status=ComplianceStatus.PASS,
            details="Passed",
            spec_reference="Test"
        )
        report.add_check(check)
        assert report.optional_passed == 1
        assert report.optional_failed == 0

    def test_overall_pass_all_mandatory_pass(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        assert report.overall_pass is True

        # Add failing mandatory
        check = ComplianceCheck(
            check_id="TEST_001",
            description="Test",
            level=ComplianceLevel.MANDATORY,
            status=ComplianceStatus.FAIL,
            details="Failed",
            spec_reference="Test"
        )
        report.add_check(check)
        assert report.overall_pass is False

    def test_compliance_percentage(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        assert report.compliance_percentage == 0.0

        # Add 3 passing and 1 failing
        for i in range(3):
            check = ComplianceCheck(
                check_id=f"TEST_{i}",
                description="Test",
                level=ComplianceLevel.MANDATORY,
                status=ComplianceStatus.PASS,
                details="Passed",
                spec_reference="Test"
            )
            report.add_check(check)

        check = ComplianceCheck(
            check_id="TEST_FAIL",
            description="Test",
            level=ComplianceLevel.MANDATORY,
            status=ComplianceStatus.FAIL,
            details="Failed",
            spec_reference="Test"
        )
        report.add_check(check)

        assert report.compliance_percentage == 75.0

    def test_to_dict(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={"model": "HBM4"}
        )
        check = ComplianceCheck(
            check_id="TEST_001",
            description="Test",
            level=ComplianceLevel.MANDATORY,
            status=ComplianceStatus.PASS,
            details="Passed",
            spec_reference="Test"
        )
        report.add_check(check)

        d = report.to_dict()
        assert d["spec_version"] == "JESD238B"
        assert d["summary"]["overall_pass"] is True
        assert len(d["checks"]) == 1


class TestHBM4ComplianceChecker:
    """Test HBM4ComplianceChecker class"""

    def test_creation(self):
        checker = HBM4ComplianceChecker()
        assert checker.spec_version == "JESD238B"
        assert checker.report is None

    def test_creation_with_config(self):
        checker = HBM4ComplianceChecker(config={"custom": "value"})
        assert checker.config["custom"] == "value"

    def test_constants(self):
        checker = HBM4ComplianceChecker()
        assert checker.INTERFACE_WIDTH_OPTIONS == [1024, 2048]
        assert checker.DATA_RATE_OPTIONS == [8.0, 12.0, 16.0]
        assert checker.BURST_LENGTH == 4
        assert checker.CHANNELS_HBM4 == 32
        assert checker.PSEUDO_CHANNELS_PER_CHANNEL == 2
        assert checker.BANKS_PER_PSEUDO_CHANNEL == 16
        assert checker.BANK_GROUPS == 8

    def test_check_interface_width_valid_1024(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_interface_width(1024)
        assert result.status == ComplianceStatus.PASS
        assert result.check_id == "IF_WIDTH_001"

    def test_check_interface_width_valid_2048(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_interface_width(2048)
        assert result.status == ComplianceStatus.PASS

    def test_check_interface_width_invalid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_interface_width(512)
        assert result.status == ComplianceStatus.FAIL
        assert result.remediation is not None

    def test_check_data_rate_valid_8gtps(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_data_rate(8.0)
        assert result.status == ComplianceStatus.PASS
        assert result.check_id == "DR_001"

    def test_check_data_rate_valid_12gtps(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_data_rate(12.0)
        assert result.status == ComplianceStatus.PASS

    def test_check_data_rate_valid_16gtps(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_data_rate(16.0)
        assert result.status == ComplianceStatus.PASS

    def test_check_data_rate_invalid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_data_rate(6.0)
        assert result.status == ComplianceStatus.FAIL

    def test_check_channel_count_hbm4_native(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_channel_count(32, hbm3_compat=False)
        assert result.status == ComplianceStatus.PASS

    def test_check_channel_count_hbm3_compat(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_channel_count(16, hbm3_compat=True)
        assert result.status == ComplianceStatus.PASS

    def test_check_channel_count_invalid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_channel_count(8, hbm3_compat=False)
        assert result.status == ComplianceStatus.FAIL

    def test_check_burst_length_valid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_burst_length(4)
        assert result.status == ComplianceStatus.PASS
        assert result.check_id == "BL_001"

    def test_check_burst_length_invalid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_burst_length(8)
        assert result.status == ComplianceStatus.FAIL

    def test_check_cas_latency_valid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_cas_latency(8, 8.0)
        assert result.status == ComplianceStatus.PASS

    def test_check_cas_latency_invalid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_cas_latency(2, 8.0)
        assert result.status == ComplianceStatus.FAIL

    def test_check_voltage_valid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_voltage(1000)
        assert result.status == ComplianceStatus.PASS

    def test_check_voltage_too_low(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_voltage(800)
        assert result.status == ComplianceStatus.FAIL

    def test_check_voltage_too_high(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_voltage(1300)
        assert result.status == ComplianceStatus.FAIL

    def test_check_temperature_valid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_temperature(25)
        assert result.status == ComplianceStatus.PASS

    def test_check_temperature_too_low(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_temperature(-50)
        assert result.status == ComplianceStatus.FAIL

    def test_check_temperature_too_high(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_temperature(130)
        assert result.status == ComplianceStatus.FAIL

    def test_check_timing_parameter_valid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_timing_parameter("tRCD", 8, 8)
        assert result.status == ComplianceStatus.PASS

    def test_check_timing_parameter_within_tolerance(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_timing_parameter("tRCD", 9, 8, tolerance_percent=20.0)
        assert result.status == ComplianceStatus.PASS

    def test_check_timing_parameter_outside_tolerance(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_timing_parameter("tRCD", 5, 8)
        assert result.status == ComplianceStatus.FAIL

    def test_check_ecc_enabled_true(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_ecc_enabled(True)
        assert result.status == ComplianceStatus.PASS
        assert result.level == ComplianceLevel.RECOMMENDED

    def test_check_ecc_enabled_false(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_ecc_enabled(False)
        assert result.status == ComplianceStatus.WARN

    def test_check_crc_enabled_true(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_crc_enabled(True)
        assert result.status == ComplianceStatus.PASS
        assert result.level == ComplianceLevel.RECOMMENDED

    def test_check_crc_enabled_false(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_crc_enabled(False)
        assert result.status == ComplianceStatus.WARN

    def test_check_refresh_timing_valid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_refresh_timing(3900, 180, 8.0)
        assert result.status == ComplianceStatus.PASS

    def test_check_refresh_timing_invalid(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_refresh_timing(1000, 100, 8.0)
        assert result.status == ComplianceStatus.FAIL

    def test_check_bank_group_timing_same_bg(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_bank_group_timing(4, 4, same_bank_group=True)
        assert result.status == ComplianceStatus.PASS

    def test_check_bank_group_timing_diff_bg(self):
        checker = HBM4ComplianceChecker()
        result = checker.check_bank_group_timing(6, 6, same_bank_group=False)
        assert result.status == ComplianceStatus.PASS

    def test_run_protocol_compliance(self):
        checker = HBM4ComplianceChecker()
        config = {
            "interface_width": 2048,
            "data_rate": 8.0,
            "channels": 32,
            "burst_length": 4
        }
        checks = checker.run_protocol_compliance(config)
        assert len(checks) == 4
        assert all(c.status == ComplianceStatus.PASS for c in checks)

    def test_run_timing_compliance(self):
        checker = HBM4ComplianceChecker()
        config = {
            "data_rate": 8.0,
            "tCL": 8,
            "VDDQ": 1000,
            "Tj": 25,
            "tRCD": 8,
            "tRP": 8,
            "tRAS": 20,
            "tRc": 22,
            "tREFI": 3900,
            "tRFC": 180,
            "tCCD": 4,
            "tRRD": 4
        }
        checks = checker.run_timing_compliance(config)
        assert len(checks) >= 3

    def test_run_reliability_compliance(self):
        checker = HBM4ComplianceChecker()
        config = {
            "ecc_enabled": True,
            "crc_enabled": True
        }
        checks = checker.run_reliability_compliance(config)
        assert len(checks) == 2

    def test_run_full_compliance(self):
        checker = HBM4ComplianceChecker()
        device_config = {
            "interface_width": 2048,
            "data_rate": 8.0,
            "channels": 32,
            "burst_length": 4
        }
        timing_config = {
            "data_rate": 8.0,
            "tCL": 8,
            "VDDQ": 1000,
            "Tj": 25,
            "tRCD": 8,
            "tRP": 8,
            "tRAS": 20,
            "tRc": 22,
            "tREFI": 3900,
            "tRFC": 180,
            "tCCD": 4,
            "tRRD": 4
        }
        reliability_config = {
            "ecc_enabled": True,
            "crc_enabled": True
        }
        report = checker.run_full_compliance(device_config, timing_config, reliability_config)
        assert report is not None
        assert report.spec_version == "JESD238B"
        assert report.overall_pass is True


class TestComplianceFunctions:
    """Test module-level compliance functions"""

    def test_run_jedec_compliance(self):
        device_config = {
            "interface_width": 2048,
            "data_rate": 8.0,
            "channels": 32,
            "burst_length": 4
        }
        timing_config = {
            "data_rate": 8.0,
            "tCL": 8,
            "VDDQ": 1000,
            "Tj": 25,
            "tRCD": 8,
            "tRP": 8,
            "tRAS": 20,
            "tRc": 22,
            "tREFI": 3900,
            "tRFC": 180,
            "tCCD": 4,
            "tRRD": 4
        }
        report = run_jedec_compliance(device_config, timing_config)
        assert report is not None
        assert report.overall_pass is True

    def test_run_jedec_compliance_with_reliability(self):
        device_config = {
            "interface_width": 2048,
            "data_rate": 16.0,
            "channels": 32,
            "burst_length": 4
        }
        timing_config = {
            "data_rate": 16.0,
            "tCL": 12,
            "VDDQ": 1000,
            "Tj": 25,
            "tRCD": 12,
            "tRP": 12,
            "tRAS": 28,
            "tRc": 30,
            "tREFI": 1950,
            "tRFC": 90,
            "tCCD": 4,
            "tRRD": 4
        }
        reliability_config = {
            "ecc_enabled": True,
            "crc_enabled": True
        }
        report = run_jedec_compliance(device_config, timing_config, reliability_config)
        assert report is not None

    def test_validate_hbm4_device(self):
        config = {
            "device": {
                "interface_width": 2048,
                "data_rate": 8.0,
                "channels": 32,
                "burst_length": 4
            },
            "timing": {
                "data_rate": 8.0,
                "tCL": 8,
                "VDDQ": 1000,
                "Tj": 25,
                "tRCD": 8,
                "tRP": 8,
                "tRAS": 20,
                "tRc": 22,
                "tREFI": 3900,
                "tRFC": 180,
                "tCCD": 4,
                "tRRD": 4
            },
            "reliability": {
                "ecc_enabled": True,
                "crc_enabled": True
            },
            "info": {
                "model": "HBM4-8G",
                "vendor": "Test"
            }
        }
        is_compliant, report = validate_hbm4_device(config)
        assert is_compliant is True
        assert report is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_compliance_report(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        assert report.compliance_percentage == 0.0
        assert report.overall_pass is True

    def test_all_checks_failing(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        for _ in range(3):
            check = ComplianceCheck(
                check_id="FAIL",
                description="Failing test",
                level=ComplianceLevel.MANDATORY,
                status=ComplianceStatus.FAIL,
                details="Failed",
                spec_reference="Test"
            )
            report.add_check(check)
        assert report.overall_pass is False
        assert report.compliance_percentage == 0.0

    def test_mixed_status_levels(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        # Add mandatory fail
        check1 = ComplianceCheck(
            check_id="M_FAIL",
            description="Mandatory fail",
            level=ComplianceLevel.MANDATORY,
            status=ComplianceStatus.FAIL,
            details="Failed",
            spec_reference="Test"
        )
        report.add_check(check1)
        assert report.overall_pass is False

    def test_warning_status(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        check = ComplianceCheck(
            check_id="WARN",
            description="Warning test",
            level=ComplianceLevel.RECOMMENDED,
            status=ComplianceStatus.WARN,
            details="Warning",
            spec_reference="Test"
        )
        report.add_check(check)
        assert report.recommended_failed == 1

    def test_skip_status(self):
        report = ComplianceReport(
            spec_version="JESD238B",
            test_date="2026-01-01",
            device_info={}
        )
        check = ComplianceCheck(
            check_id="SKIP",
            description="Skipped test",
            level=ComplianceLevel.OPTIONAL,
            status=ComplianceStatus.SKIP,
            details="Skipped",
            spec_reference="Test"
        )
        report.add_check(check)
        # SKIP should not affect pass/fail counts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
