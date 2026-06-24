"""
Additional Tests for Comparison Benchmark Module

Covers edge cases and additional functionality.

Run with: pytest tests/benchmark/test_comparison_benchmark_extra.py -v
"""

import pytest
from model.benchmark.comparison_benchmark import (
    ComparisonBenchmark,
    ComparisonResult,
    ComparisonReport,
)
from model.benchmark.benchmark_config import ComparisonConfig, SpeedGrade


class TestComparisonBenchmarkMethods:
    """Tests for comparison benchmark methods"""

    def test_run_single_config_hbm3(self):
        """Test running single HBM3 config"""
        result = ComparisonBenchmark._run_single_config_test(
            ComparisonBenchmark(),
            "HBM3",
            SpeedGrade.HBM3_6_4
        )

        assert isinstance(result, ComparisonResult)
        assert result.config_name == "HBM3"
        assert result.data_rate_gtps == 6.4

    def test_run_single_config_hbm4(self):
        """Test running single HBM4 config"""
        result = ComparisonBenchmark._run_single_config_test(
            ComparisonBenchmark(),
            "HBM4-8G",
            SpeedGrade.HBM4_8
        )

        assert isinstance(result, ComparisonResult)
        assert result.config_name == "HBM4-8G"
        assert result.data_rate_gtps == 8.0

    def test_run_single_config_hbm4_12g(self):
        """Test running HBM4 12Gbps config"""
        result = ComparisonBenchmark._run_single_config_test(
            ComparisonBenchmark(),
            "HBM4-12G",
            SpeedGrade.HBM4_12
        )

        assert isinstance(result, ComparisonResult)
        assert result.data_rate_gtps == 12.0

    def test_run_single_config_hbm4_16g(self):
        """Test running HBM4 16Gbps config"""
        result = ComparisonBenchmark._run_single_config_test(
            ComparisonBenchmark(),
            "HBM4-16G",
            SpeedGrade.HBM4_16
        )

        assert isinstance(result, ComparisonResult)
        assert result.data_rate_gtps == 16.0


class TestComparisonResult:
    """Tests for ComparisonResult"""

    def test_result_complete(self):
        """Test result with all fields"""
        result = ComparisonResult()
        result.config_name = "HBM4-8G"
        result.data_rate_gtps = 8.0
        result.io_width = 2048
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1800.0
        result.bandwidth_efficiency_percent = 87.8
        result.average_latency_ns = 40.0
        result.p99_latency_ns = 65.0
        result.requests_per_ns = 1e-6
        result.energy_per_bit = 1.0
        result.bandwidth_vs_baseline = 2.0
        result.latency_vs_baseline = 1.2

        assert result.config_name == "HBM4-8G"
        assert result.data_rate_gtps == 8.0
        assert result.bandwidth_vs_baseline == 2.0

    def test_to_dict_complete(self):
        """Test to_dict with all fields"""
        result = ComparisonResult()
        result.config_name = "HBM4-16G"
        result.data_rate_gtps = 16.0
        result.io_width = 2048
        result.peak_bandwidth_gbs = 4096.0
        result.measured_bandwidth_gbs = 3500.0
        result.bandwidth_efficiency_percent = 85.4
        result.average_latency_ns = 35.0
        result.p99_latency_ns = 55.0
        result.bandwidth_vs_baseline = 4.0
        result.latency_vs_baseline = 1.5

        d = result.to_dict()

        assert d['config_name'] == "HBM4-16G"
        assert d['peak_bandwidth_gbs'] == 4096.0
        assert d['bandwidth_vs_baseline'] == 4.0

    def test_to_str_complete(self):
        """Test __str__ with all fields"""
        result = ComparisonResult()
        result.config_name = "HBM4-8G"
        result.data_rate_gtps = 8.0
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1800.0
        result.bandwidth_efficiency_percent = 87.8
        result.average_latency_ns = 40.0
        result.p99_latency_ns = 65.0
        result.bandwidth_vs_baseline = 2.0
        result.latency_vs_baseline = 1.2

        s = str(result)

        assert "HBM4-8G" in s
        assert "8.0" in s
        assert "2048" in s
        assert "40" in s


class TestComparisonReport:
    """Tests for ComparisonReport"""

    def test_report_complete(self):
        """Test report with all fields"""
        report = ComparisonReport()

        # Add baseline
        baseline = ComparisonResult()
        baseline.config_name = "HBM3"
        baseline.peak_bandwidth_gbs = 819.2
        baseline.average_latency_ns = 50.0
        report.baseline = baseline

        # Add HBM4 result
        hbm4 = ComparisonResult()
        hbm4.config_name = "HBM4-8G"
        hbm4.peak_bandwidth_gbs = 2048.0
        hbm4.measured_bandwidth_gbs = 1800.0
        hbm4.average_latency_ns = 40.0
        hbm4.bandwidth_vs_baseline = 2.5
        hbm4.latency_vs_baseline = 1.25
        report.configs.append(hbm4)

        report.best_bandwidth_config = "HBM4-8G"
        report.best_bandwidth_gbs = 2048.0
        report.best_latency_config = "HBM4-8G"
        report.best_latency_ns = 40.0
        report.hbm4_vs_hbm3_bandwidth_speedup = 2.5
        report.hbm4_vs_hbm3_latency_improvement = 0.2

        assert report.baseline is not None
        assert len(report.configs) == 1
        assert report.best_bandwidth_config == "HBM4-8G"
        assert report.hbm4_vs_hbm3_bandwidth_speedup == 2.5

    def test_to_dict_complete(self):
        """Test to_dict with all fields"""
        report = ComparisonReport()

        baseline = ComparisonResult()
        baseline.config_name = "HBM3"
        baseline.peak_bandwidth_gbs = 819.2
        report.baseline = baseline

        hbm4 = ComparisonResult()
        hbm4.config_name = "HBM4-8G"
        hbm4.peak_bandwidth_gbs = 2048.0
        hbm4.bandwidth_vs_baseline = 2.5
        report.configs.append(hbm4)

        report.best_bandwidth_gbs = 2048.0
        report.best_latency_ns = 40.0
        report.hbm4_vs_hbm3_bandwidth_speedup = 2.5

        d = report.to_dict()

        assert d['baseline'] is not None
        assert len(d['configs']) == 1
        assert d['best_bandwidth_gbs'] == 2048.0
        assert d['hbm4_vs_hbm3_bandwidth_speedup'] == 2.5

    def test_to_str_complete(self):
        """Test __str__ with all fields"""
        report = ComparisonReport()

        hbm3 = ComparisonResult()
        hbm3.config_name = "HBM3"
        hbm3.peak_bandwidth_gbs = 819.2
        hbm3.average_latency_ns = 50.0
        report.configs.append(hbm3)

        hbm4 = ComparisonResult()
        hbm4.config_name = "HBM4-8G"
        hbm4.peak_bandwidth_gbs = 2048.0
        hbm4.average_latency_ns = 40.0
        hbm4.bandwidth_vs_baseline = 2.5
        hbm4.latency_vs_baseline = 1.25
        report.configs.append(hbm4)

        report.best_bandwidth_config = "HBM4-8G"
        report.best_bandwidth_gbs = 2048.0
        report.best_latency_config = "HBM4-8G"
        report.best_latency_ns = 40.0
        report.hbm4_vs_hbm3_bandwidth_speedup = 2.5
        report.hbm4_vs_hbm3_latency_improvement = 0.2

        s = str(report)

        assert "Comparison Report" in s
        assert "HBM3" in s
        assert "HBM4-8G" in s
        assert "2048" in s
        assert "2.5" in s


class TestComparisonBenchmarkExecution:
    """Tests for benchmark execution"""

    def test_run_comparison(self):
        """Test running full comparison"""
        config = ComparisonConfig(
            configs_to_compare=[
                ("HBM4-8G", SpeedGrade.HBM4_8),
                ("HBM4-12G", SpeedGrade.HBM4_12),
            ]
        )
        benchmark = ComparisonBenchmark(config=config)

        report = benchmark.run_comparison()

        assert isinstance(report, ComparisonReport)
        assert len(report.configs) >= 2

    def test_run_comparison_with_baseline(self):
        """Test comparison with HBM3 baseline"""
        config = ComparisonConfig(
            configs_to_compare=[
                ("HBM3", SpeedGrade.HBM3_6_4),
                ("HBM4-8G", SpeedGrade.HBM4_8),
            ]
        )
        benchmark = ComparisonBenchmark(config=config)

        report = benchmark.run_comparison()

        assert report.baseline is not None
        assert "HBM3" in [c.config_name for c in report.configs]

    def test_run_bandwidth_comparison(self):
        """Test bandwidth comparison"""
        config = ComparisonConfig(
            configs_to_compare=[
                ("HBM4-8G", SpeedGrade.HBM4_8),
                ("HBM4-16G", SpeedGrade.HBM4_16),
            ]
        )
        benchmark = ComparisonBenchmark(config=config)

        results = benchmark.run_bandwidth_comparison()

        assert isinstance(results, dict)
        assert len(results) >= 2
        # 16Gbps should have higher bandwidth than 8Gbps
        assert results.get("HBM4-16G", 0) > results.get("HBM4-8G", 0)

    def test_run_latency_comparison(self):
        """Test latency comparison"""
        config = ComparisonConfig(
            configs_to_compare=[
                ("HBM4-8G", SpeedGrade.HBM4_8),
                ("HBM4-12G", SpeedGrade.HBM4_12),
            ]
        )
        benchmark = ComparisonBenchmark(config=config)

        results = benchmark.run_latency_comparison()

        assert isinstance(results, dict)
        assert len(results) >= 2

    def test_get_summary(self):
        """Test get_summary method"""
        config = ComparisonConfig(
            configs_to_compare=[
                ("HBM4-8G", SpeedGrade.HBM4_8),
            ]
        )
        benchmark = ComparisonBenchmark(config=config)

        summary = benchmark.get_summary()

        assert isinstance(summary, str)
        assert "Comparison Report" in summary


class TestComparisonEdgeCases:
    """Tests for edge cases"""

    def test_empty_config(self):
        """Test with empty configs"""
        config = ComparisonConfig(configs_to_compare=[])
        benchmark = ComparisonBenchmark(config=config)

        report = benchmark.run_comparison()

        assert isinstance(report, ComparisonReport)
        assert len(report.configs) == 0

    def test_single_config(self):
        """Test with single config"""
        config = ComparisonConfig(
            configs_to_compare=[
                ("HBM4-8G", SpeedGrade.HBM4_8),
            ]
        )
        benchmark = ComparisonBenchmark(config=config)

        report = benchmark.run_comparison()

        assert isinstance(report, ComparisonReport)
        assert len(report.configs) == 1

    def test_bandwidth_comparison_empty(self):
        """Test bandwidth comparison with empty config"""
        config = ComparisonConfig(configs_to_compare=[])
        benchmark = ComparisonBenchmark(config=config)

        results = benchmark.run_bandwidth_comparison()

        assert isinstance(results, dict)
        assert len(results) == 0

    def test_latency_comparison_empty(self):
        """Test latency comparison with empty config"""
        config = ComparisonConfig(configs_to_compare=[])
        benchmark = ComparisonBenchmark(config=config)

        results = benchmark.run_latency_comparison()

        assert isinstance(results, dict)
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
