"""
Tests for HBM4 Silicon Validation

Covers model/dram/hbm4_validation.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from model.dram.hbm4_validation import (
    ValidationResult, TemperatureCorner, VoltageCorner, MarginResult,
    SiliconValidationReport, SiliconValidator, MarginAnalyzer,
    create_validator, run_production_validation
)


class TestValidationResult:
    """Test ValidationResult enum"""

    def test_validation_result_values(self):
        assert ValidationResult.PASS.value == "pass"
        assert ValidationResult.FAIL.value == "fail"
        assert ValidationResult.MARGINAL.value == "marginal"
        assert ValidationResult.NOT_TESTED.value == "not_tested"


class TestTemperatureCorner:
    """Test TemperatureCorner enum"""

    def test_temperature_corner_values(self):
        assert TemperatureCorner.COLD.value == "cold"
        assert TemperatureCorner.ROOM.value == "room"
        assert TemperatureCorner.HOT.value == "hot"
        assert TemperatureCorner.HOT_EXTREME.value == "hot_extreme"


class TestVoltageCorner:
    """Test VoltageCorner enum"""

    def test_voltage_corner_values(self):
        assert VoltageCorner.NOMINAL.value == "nominal"
        assert VoltageCorner.MIN.value == "min"
        assert VoltageCorner.MAX.value == "max"
        assert VoltageCorner.MARGIN_LOW.value == "margin_low"
        assert VoltageCorner.MARGIN_HIGH.value == "margin_high"


class TestMarginResult:
    """Test MarginResult dataclass"""

    def test_creation(self):
        result = MarginResult(
            parameter="tCL",
            measured_value=8,
            spec_min=6,
            spec_max=12,
            margin_low=2,
            margin_high=4,
            status=ValidationResult.PASS
        )
        assert result.parameter == "tCL"
        assert result.measured_value == 8
        assert result.status == ValidationResult.PASS

    def test_margin_percent_calculation(self):
        result = MarginResult(
            parameter="tCL",
            measured_value=8,
            spec_min=6,
            spec_max=12,
            margin_low=2,
            margin_high=4,
            status=ValidationResult.PASS
        )
        # spec_window = 12 - 6 = 6
        # min_margin_percent = 2/6 * 100 = 33.3%
        # max_margin_percent = 4/6 * 100 = 66.7%
        # margin_percent = min(33.3, 66.7) = 33.3%
        assert result.margin_percent == pytest.approx(33.33, rel=0.1)

    def test_margin_percent_zero_window(self):
        result = MarginResult(
            parameter="exact",
            measured_value=10,
            spec_min=10,
            spec_max=10,
            margin_low=0,
            margin_high=0,
            status=ValidationResult.PASS
        )
        assert result.margin_percent == 0.0

    def test_to_dict(self):
        result = MarginResult(
            parameter="tCL",
            measured_value=8,
            spec_min=6,
            spec_max=12,
            margin_low=2,
            margin_high=4,
            status=ValidationResult.PASS
        )
        d = result.to_dict()
        assert d["parameter"] == "tCL"
        assert d["measured_value"] == 8
        assert d["status"] == "pass"


class TestSiliconValidationReport:
    """Test SiliconValidationReport dataclass"""

    def test_creation(self):
        report = SiliconValidationReport(
            speed_grade="8Gbps",
            lot_id="LOT001",
            die_id="DIE001",
            test_temperature=25.0,
            test_voltage=1000.0,
            timestamp="2026-01-01T00:00:00"
        )
        assert report.speed_grade == "8Gbps"
        assert report.total_tests == 0
        assert report.overall_status == ValidationResult.NOT_TESTED

    def test_add_result_pass(self):
        report = SiliconValidationReport(
            speed_grade="8Gbps",
            lot_id="LOT001",
            die_id="DIE001",
            test_temperature=25.0,
            test_voltage=1000.0,
            timestamp="2026-01-01T00:00:00"
        )
        result = MarginResult(
            parameter="tCL",
            measured_value=8,
            spec_min=6,
            spec_max=12,
            margin_low=2,
            margin_high=4,
            status=ValidationResult.PASS
        )
        report.add_result(result)
        assert report.total_tests == 1
        assert report.passed_tests == 1
        assert report.failed_tests == 0
        assert report.overall_status == ValidationResult.PASS

    def test_add_result_fail(self):
        report = SiliconValidationReport(
            speed_grade="8Gbps",
            lot_id="LOT001",
            die_id="DIE001",
            test_temperature=25.0,
            test_voltage=1000.0,
            timestamp="2026-01-01T00:00:00"
        )
        result = MarginResult(
            parameter="tCL",
            measured_value=2,
            spec_min=6,
            spec_max=12,
            margin_low=-4,
            margin_high=10,
            status=ValidationResult.FAIL
        )
        report.add_result(result)
        assert report.total_tests == 1
        assert report.failed_tests == 1
        assert report.overall_status == ValidationResult.FAIL

    def test_add_result_marginal(self):
        report = SiliconValidationReport(
            speed_grade="8Gbps",
            lot_id="LOT001",
            die_id="DIE001",
            test_temperature=25.0,
            test_voltage=1000.0,
            timestamp="2026-01-01T00:00:00"
        )
        result = MarginResult(
            parameter="tCL",
            measured_value=6,
            spec_min=6,
            spec_max=12,
            margin_low=0,
            margin_high=6,
            status=ValidationResult.MARGINAL
        )
        report.add_result(result)
        assert report.marginal_tests == 1
        assert report.overall_status == ValidationResult.MARGINAL

    def test_pass_rate(self):
        report = SiliconValidationReport(
            speed_grade="8Gbps",
            lot_id="LOT001",
            die_id="DIE001",
            test_temperature=25.0,
            test_voltage=1000.0,
            timestamp="2026-01-01T00:00:00"
        )
        for _ in range(3):
            report.add_result(MarginResult(
                parameter="tCL",
                measured_value=8,
                spec_min=6,
                spec_max=12,
                margin_low=2,
                margin_high=4,
                status=ValidationResult.PASS
            ))
        for _ in range(1):
            report.add_result(MarginResult(
                parameter="tRCD",
                measured_value=4,
                spec_min=6,
                spec_max=12,
                margin_low=-2,
                margin_high=8,
                status=ValidationResult.FAIL
            ))
        assert report.pass_rate == 75.0

    def test_to_dict(self):
        report = SiliconValidationReport(
            speed_grade="8Gbps",
            lot_id="LOT001",
            die_id="DIE001",
            test_temperature=25.0,
            test_voltage=1000.0,
            timestamp="2026-01-01T00:00:00"
        )
        report.add_result(MarginResult(
            parameter="VDDQ_voltage",
            measured_value=1000,
            spec_min=880,
            spec_max=1200,
            margin_low=120,
            margin_high=200,
            status=ValidationResult.PASS
        ))
        d = report.to_dict()
        assert d["device_info"]["speed_grade"] == "8Gbps"
        assert d["summary"]["total_tests"] == 1


class TestSiliconValidator:
    """Test SiliconValidator class"""

    def test_creation_default(self):
        validator = SiliconValidator()
        assert validator.speed_grade == "8Gbps"
        assert validator.results == []

    def test_creation_custom_speed_grade(self):
        validator = SiliconValidator(speed_grade="16Gbps")
        assert validator.speed_grade == "16Gbps"

    def test_timing_specs(self):
        validator = SiliconValidator()
        assert "tCK" in validator.TIMING_SPECS
        assert "tCL" in validator.TIMING_SPECS
        assert "tRCD" in validator.TIMING_SPECS
        assert validator.TIMING_SPECS["tCL"] == (6, 12)

    def test_voltage_specs(self):
        validator = SiliconValidator()
        assert "VDDQ" in validator.VOLTAGE_SPECS
        assert validator.VOLTAGE_SPECS["VDDQ"] == (880, 1200)

    def test_thermal_specs(self):
        validator = SiliconValidator()
        assert "Tj" in validator.THERMAL_SPECS
        assert validator.THERMAL_SPECS["Tj"] == (-40, 125)

    def test_required_margins(self):
        validator = SiliconValidator()
        assert validator.REQUIRED_MARGINS["timing"] == 10.0
        assert validator.REQUIRED_MARGINS["voltage"] == 5.0
        assert validator.REQUIRED_MARGINS["thermal"] == 15.0

    def test_validate_timing_margin_pass(self):
        validator = SiliconValidator()
        # Measured value in center of spec
        result = validator.validate_timing_margin("tCL", 9, 125.0)
        assert result.status == ValidationResult.PASS

    def test_validate_voltage_margin_pass(self):
        validator = SiliconValidator()
        result = validator.validate_voltage_margin(1000)
        assert result.status == ValidationResult.PASS
        assert result.parameter == "VDDQ_voltage"

    def test_validate_voltage_margin_fail(self):
        validator = SiliconValidator()
        result = validator.validate_voltage_margin(800)
        assert result.status == ValidationResult.FAIL

    def test_validate_thermal_margin_pass(self):
        validator = SiliconValidator()
        result = validator.validate_thermal_margin(50)
        assert result.status == ValidationResult.PASS

    def test_validate_thermal_margin_fail(self):
        validator = SiliconValidator()
        result = validator.validate_thermal_margin(-50)
        assert result.status == ValidationResult.FAIL

    def test_analyze_DQ_eye_pass(self):
        validator = SiliconValidator()
        result = validator.analyze_DQ_eye(60.0, 0.4, "8Gbps")
        assert result["overall_pass"] is True
        assert result["height_pass"] is True
        assert result["width_pass"] is True

    def test_analyze_DQ_eye_fail_height(self):
        validator = SiliconValidator()
        result = validator.analyze_DQ_eye(30.0, 0.4, "8Gbps")
        assert result["overall_pass"] is False
        assert result["height_pass"] is False
        assert result["width_pass"] is True

    def test_analyze_DQ_eye_fail_width(self):
        validator = SiliconValidator()
        result = validator.analyze_DQ_eye(60.0, 0.2, "8Gbps")
        assert result["overall_pass"] is False
        assert result["height_pass"] is True
        assert result["width_pass"] is False

    def test_analyze_DQS_eye_pass(self):
        validator = SiliconValidator()
        result = validator.analyze_DQS_eye(50.0, 0.3)
        assert result["overall_pass"] is True

    def test_analyze_DQS_eye_fail(self):
        validator = SiliconValidator()
        result = validator.analyze_DQS_eye(30.0, 0.2)
        assert result["overall_pass"] is False

    def test_run_full_validation(self):
        validator = SiliconValidator(speed_grade="8Gbps")
        report = validator.run_full_validation(
            lot_id="LOT001",
            die_id="DIE001",
            temperature_C=25.0,
            voltage_mV=1000.0
        )
        assert report is not None
        assert report.speed_grade == "8Gbps"
        assert report.lot_id == "LOT001"
        assert report.total_tests >= 2  # At least thermal and voltage

    def test_batch_analyze(self):
        validator = SiliconValidator()
        measurements = [
            {"param": "tCL", "value": 8, "unit": "cycles"},
            {"param": "tCL", "value": 9, "unit": "cycles"},
            {"param": "tCL", "value": 7, "unit": "cycles"},
            {"param": "tRCD", "value": 8, "unit": "cycles"},
            {"param": "tRCD", "value": 9, "unit": "cycles"},
        ]
        results = validator.batch_analyze(measurements)
        assert len(results) == 2  # tCL and tRCD groups

    def test_batch_analyze_insufficient_data(self):
        validator = SiliconValidator()
        measurements = [
            {"param": "tCL", "value": 8, "unit": "cycles"},
        ]
        results = validator.batch_analyze(measurements)
        # Single data point should be skipped
        assert len(results) == 0


class TestMarginAnalyzer:
    """Test MarginAnalyzer class"""

    def test_creation(self):
        analyzer = MarginAnalyzer()
        assert analyzer.target_yield == 0.99

    def test_creation_custom_yield(self):
        analyzer = MarginAnalyzer(target_yield_percent=99.9)
        assert analyzer.target_yield == pytest.approx(0.999, rel=0.001)

    def test_calculate_guardband_upper(self):
        analyzer = MarginAnalyzer()
        # mean=100, stdev=5, spec_limit=90
        # guardband = 100 + 2.33*5 - 90 = 21.65
        gb = analyzer.calculate_guardband(100, 5, 90, "upper")
        assert gb == pytest.approx(21.65, rel=0.1)

    def test_calculate_guardband_lower(self):
        analyzer = MarginAnalyzer()
        # mean=100, stdev=5, spec_limit=110
        # guardband = 110 - (100 - 2.33*5) = 21.65
        gb = analyzer.calculate_guardband(100, 5, 110, "lower")
        assert gb == pytest.approx(21.65, rel=0.1)

    def test_analyze_margin_trend_stable(self):
        analyzer = MarginAnalyzer()
        data = [
            {"timestamp": 0, "margin": 10.0},
            {"timestamp": 1, "margin": 10.2},
            {"timestamp": 2, "margin": 9.8},
            {"timestamp": 3, "margin": 10.1},
        ]
        result = analyzer.analyze_margin_trend(data)
        assert "trend" in result
        assert result["current_margin"] == 10.1
        assert result["initial_margin"] == 10.0

    def test_analyze_margin_trend_improving(self):
        analyzer = MarginAnalyzer()
        data = [
            {"timestamp": 0, "margin": 8.0},
            {"timestamp": 1, "margin": 9.0},
            {"timestamp": 2, "margin": 10.0},
            {"timestamp": 3, "margin": 11.0},
        ]
        result = analyzer.analyze_margin_trend(data)
        assert result["trend"] == "improving"
        assert result["margin_change"] > 0

    def test_analyze_margin_trend_degrading(self):
        analyzer = MarginAnalyzer()
        data = [
            {"timestamp": 0, "margin": 12.0},
            {"timestamp": 1, "margin": 11.0},
            {"timestamp": 2, "margin": 10.0},
            {"timestamp": 3, "margin": 9.0},
        ]
        result = analyzer.analyze_margin_trend(data)
        assert result["trend"] == "degrading"
        assert result["margin_change"] < 0

    def test_analyze_margin_trend_insufficient_data(self):
        analyzer = MarginAnalyzer()
        data = [{"timestamp": 0, "margin": 10.0}]
        result = analyzer.analyze_margin_trend(data)
        assert result["status"] == "insufficient_data"

    def test_calculate_screening_threshold(self):
        analyzer = MarginAnalyzer()
        distribution = [95, 100, 105, 98, 102, 97, 103, 99, 101, 100]
        lower, upper = analyzer.calculate_screening_threshold(distribution)
        assert lower < upper
        assert lower < 100
        assert upper > 100


class TestValidationFunctions:
    """Test module-level validation functions"""

    def test_create_validator(self):
        validator = create_validator("8Gbps")
        assert validator.speed_grade == "8Gbps"

    def test_create_validator_16gbps(self):
        validator = create_validator("16Gbps")
        assert validator.speed_grade == "16Gbps"

    def test_run_production_validation(self):
        report = run_production_validation(
            speed_grade="8Gbps",
            lot_id="LOT001",
            temperature_C=85.0,
            voltage_mV=1000.0
        )
        assert report is not None
        assert report.speed_grade == "8Gbps"
        assert report.lot_id == "LOT001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
