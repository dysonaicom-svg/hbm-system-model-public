import pytest
from model.analysis.dvfs_analyzer import (
    DVFSAnalyzer, DVFSResult, DVFSSpeedGrade, ParetoPoint
)


class TestDVFSResult:
    def test_from_speed_grade_s16(self):
        result = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        assert result.frequency_gtps == 16.0
        assert result.bandwidth_gbps > 0

    def test_from_speed_grade_s8(self):
        result = DVFSResult.from_speed_grade(DVFSSpeedGrade.S8)
        assert result.frequency_gtps == 8.0
        assert result.power_w < 20.0  # Should be lower than S16

    def test_voltage_scales_with_frequency(self):
        s8 = DVFSResult.from_speed_grade(DVFSSpeedGrade.S8)
        s16 = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        assert s16.voltage_v > s8.voltage_v

    def test_power_scales_with_frequency(self):
        s8 = DVFSResult.from_speed_grade(DVFSSpeedGrade.S8)
        s16 = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        assert s16.power_w > s8.power_w

    def test_bandwidth_scales_with_frequency(self):
        s8 = DVFSResult.from_speed_grade(DVFSSpeedGrade.S8)
        s16 = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        assert s16.bandwidth_gbps > s8.bandwidth_gbps

    def test_latency_inversely_scales(self):
        s8 = DVFSResult.from_speed_grade(DVFSSpeedGrade.S8)
        s16 = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        assert s8.latency_ns > s16.latency_ns

    def test_efficiency_calculation(self):
        result = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        expected_eff = result.bandwidth_gbps / result.power_w
        assert abs(result.efficiency - expected_eff) < 0.001

    def test_custom_base_values(self):
        result = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16, base_power_w=20.0, base_bw_gbps=128.0)
        assert result.power_w > 10.0
        assert result.bandwidth_gbps > 64.0


class TestDVFSAnalyzer:
    def test_frequency_sweep(self):
        analyzer = DVFSAnalyzer()
        results = analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        assert len(results) == 3  # 8, 12, 16 GT/s
        assert results[0].frequency_gtps == 8.0
        assert results[-1].frequency_gtps == 16.0

    def test_frequency_sweep_fine_grained(self):
        analyzer = DVFSAnalyzer()
        results = analyzer.analyze_frequency_sweep((8.0, 10.0, 1.0))
        assert len(results) == 3
        assert all(8.0 <= r.frequency_gtps <= 10.0 for r in results)

    def test_pareto_curve(self):
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        pareto = analyzer.generate_pareto_curve()
        knee_points = [p for p in pareto if p.is_knee_point]
        assert len(knee_points) >= 1

    def test_pareto_curve_has_optimal_points(self):
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        pareto = analyzer.generate_pareto_curve()
        power_opt = [p for p in pareto if p.is_optimal_power]
        perf_opt = [p for p in pareto if p.is_optimal_performance]
        assert len(power_opt) == 1
        assert len(perf_opt) == 1

    def test_pareto_curve_empty_when_no_results(self):
        analyzer = DVFSAnalyzer()
        pareto = analyzer.generate_pareto_curve()
        assert pareto == []

    def test_suggest_optimal_config(self):
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        config = analyzer.suggest_optimal_config(target_perf_percent=80.0)
        assert config.bandwidth_gbps > 0

    def test_suggest_optimal_config_prefer_power(self):
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        config = analyzer.suggest_optimal_config(prefer_power=True)
        assert config.power_w > 0

    def test_suggest_optimal_config_empty_results(self):
        analyzer = DVFSAnalyzer()
        config = analyzer.suggest_optimal_config()
        assert config.frequency_gtps == 0

    def test_suggest_optimal_config_target_percent(self):
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        max_bw = max(r.bandwidth_gbps for r in analyzer.results)
        config = analyzer.suggest_optimal_config(target_perf_percent=50.0)
        assert config.bandwidth_gbps >= max_bw * 0.5

    def test_results_stored_in_analyzer(self):
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        assert len(analyzer.results) == 3
        assert analyzer.results is analyzer.results  # Same reference


class TestDVFSSpeedGrade:
    def test_speed_grades_exist(self):
        assert DVFSSpeedGrade.S8.value == 8.0
        assert DVFSSpeedGrade.S12.value == 12.0
        assert DVFSSpeedGrade.S16.value == 16.0

    def test_speed_grades_iterable(self):
        grades = list(DVFSSpeedGrade)
        assert len(grades) == 3


class TestParetoPoint:
    def test_pareto_point_defaults(self):
        result = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        point = ParetoPoint(dvfs_result=result)
        assert point.is_knee_point is False
        assert point.is_optimal_power is False
        assert point.is_optimal_performance is False

    def test_pareto_point_can_be_modified(self):
        result = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        point = ParetoPoint(dvfs_result=result, is_knee_point=True)
        assert point.is_knee_point is True
