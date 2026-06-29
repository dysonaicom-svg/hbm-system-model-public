import pytest
from model.compliance.hbm3_compatibility import (
    HBM3CompatibilityChecker, CompatibilityResult
)


class TestHBM3CompatibilityChecker:
    def test_mode_hbm3_legacy_compatible(self):
        checker = HBM3CompatibilityChecker()
        result = checker.check_mode_support("HBM3_LEGACY")
        assert result.compatible is True
        assert result.feature == "HBM3 Mode"

    def test_mode_hbm3_compat_compatible(self):
        checker = HBM3CompatibilityChecker()
        result = checker.check_mode_support("HBM3_COMPAT")
        assert result.compatible is True

    def test_mode_hbm4_not_compatible(self):
        checker = HBM3CompatibilityChecker()
        result = checker.check_mode_support("HBM4")
        assert result.compatible is False

    def test_mode_hbm4_native_not_compatible(self):
        checker = HBM3CompatibilityChecker()
        result = checker.check_mode_support("HBM4_NATIVE")
        assert result.compatible is False

    def test_timing_compatible(self):
        checker = HBM3CompatibilityChecker()
        result = checker.check_timing_compatibility(10.0, 10.0)
        assert result.compatible is True
        assert result.feature == "Timing Parameters"

    def test_timing_slightly_different(self):
        checker = HBM3CompatibilityChecker()
        result = checker.check_timing_compatibility(11.0, 10.0)
        assert result.compatible is True

    def test_timing_incompatible(self):
        checker = HBM3CompatibilityChecker()
        result = checker.check_timing_compatibility(15.0, 10.0)
        assert result.compatible is False

    def test_check_all(self):
        checker = HBM3CompatibilityChecker()
        config = {"mode": "HBM3_LEGACY", "tRCD_ns": 10.0}
        results = checker.check_all(config)
        assert len(results) == 2
        assert all(isinstance(r, CompatibilityResult) for r in results)

    def test_check_all_hbm4_mode(self):
        checker = HBM3CompatibilityChecker()
        config = {"mode": "HBM4", "tRCD_ns": 10.0}
        results = checker.check_all(config)
        mode_result = next(r for r in results if r.feature == "HBM3 Mode")
        assert mode_result.compatible is False

    def test_results_initialized_empty(self):
        checker = HBM3CompatibilityChecker()
        assert checker.results == []
