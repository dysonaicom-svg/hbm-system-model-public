"""
Tests for Comparison Benchmark Module
"""

import pytest
from model.benchmark.comparison_benchmark import (
    ComparisonBenchmark,
    ComparisonResult,
    ComparisonReport,
)
from model.benchmark.benchmark_config import ComparisonConfig, SpeedGrade


class TestComparisonBenchmark:
    """Tests for ComparisonBenchmark"""
    
    def test_initialization(self):
        benchmark = ComparisonBenchmark()
        assert benchmark.config is not None
        assert len(benchmark.config.configs_to_compare) >= 2
    
    def test_custom_config(self):
        config = ComparisonConfig(
            configs_to_compare=[
                ("HBM4-8G", SpeedGrade.HBM4_8),
                ("HBM4-16G", SpeedGrade.HBM4_16),
            ]
        )
        benchmark = ComparisonBenchmark(config=config)
        assert len(benchmark.config.configs_to_compare) == 2
    
    def test_bandwidth_comparison(self):
        """Test bandwidth comparison calculation"""
        benchmark = ComparisonBenchmark()
        results = benchmark.run_bandwidth_comparison()
        
        assert "HBM3" in results or "HBM4" in str(results)
        assert all(v > 0 for v in results.values())


class TestComparisonResult:
    """Tests for ComparisonResult"""
    
    def test_default_result(self):
        result = ComparisonResult()
        assert result.config_name == ""
        assert result.peak_bandwidth_gbs == 0.0
        assert result.bandwidth_vs_baseline == 0.0
    
    def test_result_to_dict(self):
        result = ComparisonResult()
        result.config_name = "HBM4-8G"
        result.data_rate_gtps = 8.0
        result.io_width = 2048
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1800.0
        result.bandwidth_efficiency_percent = 87.8
        result.average_latency_ns = 40.0
        result.bandwidth_vs_baseline = 2.0
        
        d = result.to_dict()
        assert d['config_name'] == "HBM4-8G"
        assert d['peak_bandwidth_gbs'] == 2048.0
        assert d['bandwidth_vs_baseline'] == 2.0
    
    def test_result_str(self):
        result = ComparisonResult()
        result.config_name = "HBM4-8G"
        result.data_rate_gtps = 8.0
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1800.0
        result.bandwidth_efficiency_percent = 87.8
        result.average_latency_ns = 40.0
        result.p99_latency_ns = 60.0
        result.bandwidth_vs_baseline = 2.0
        result.latency_vs_baseline = 1.2
        
        s = str(result)
        assert "HBM4-8G" in s
        assert "2048" in s
        assert "40" in s


class TestComparisonReport:
    """Tests for ComparisonReport"""
    
    def test_default_report(self):
        report = ComparisonReport()
        assert report.baseline is None
        assert len(report.configs) == 0
        assert report.best_bandwidth_config == ""
    
    def test_report_to_dict(self):
        report = ComparisonReport()
        report.baseline = ComparisonResult()
        report.baseline.config_name = "HBM3"
        report.baseline.peak_bandwidth_gbs = 819.2
        
        hbm4_result = ComparisonResult()
        hbm4_result.config_name = "HBM4-8G"
        hbm4_result.peak_bandwidth_gbs = 2048.0
        hbm4_result.bandwidth_vs_baseline = 2.5
        report.configs.append(hbm4_result)
        
        report.best_bandwidth_gbs = 2048.0
        report.best_bandwidth_config = "HBM4-8G"
        report.hbm4_vs_hbm3_bandwidth_speedup = 2.5
        
        d = report.to_dict()
        assert d['baseline'] is not None
        assert len(d['configs']) == 1
        assert d['best_bandwidth_config'] == "HBM4-8G"
        assert d['hbm4_vs_hbm3_bandwidth_speedup'] == 2.5


class TestSpeedGradeComparison:
    """Tests for speed grade comparisons"""
    
    def test_hbm3_speed_grade(self):
        """Test HBM3 speed grade parameters"""
        grade = SpeedGrade.HBM3_6_4
        assert grade.version == "hbm3"
        assert grade.data_rate == 6.4
        assert grade.io_width == 1024
    
    def test_hbm4_speed_grades(self):
        """Test HBM4 speed grade parameters"""
        for grade in [SpeedGrade.HBM4_8, SpeedGrade.HBM4_12, SpeedGrade.HBM4_16]:
            assert grade.version == "hbm4"
            assert grade.io_width == 2048
    
    def test_hbm4_bandwidth_calculation(self):
        """Test HBM4 bandwidth calculation"""
        grade = SpeedGrade.HBM4_8
        # 8 GT/s * 2048 bits / 8 = 2048 GB/s
        expected_bw = grade.data_rate * grade.io_width / 8
        assert expected_bw == pytest.approx(2048.0, rel=0.01)
    
    def test_hbm4_12gbps_bandwidth(self):
        """Test HBM4 12Gbps bandwidth"""
        grade = SpeedGrade.HBM4_12
        expected_bw = grade.data_rate * grade.io_width / 8
        assert expected_bw == pytest.approx(3072.0, rel=0.01)
    
    def test_hbm4_16gbps_bandwidth(self):
        """Test HBM4 16Gbps bandwidth"""
        grade = SpeedGrade.HBM4_16
        expected_bw = grade.data_rate * grade.io_width / 8
        assert expected_bw == pytest.approx(4096.0, rel=0.01)


class TestBaselineComparison:
    """Tests for baseline comparison calculations"""
    
    def test_bandwidth_speedup(self):
        """Test bandwidth speedup calculation"""
        hbm3 = ComparisonResult()
        hbm3.peak_bandwidth_gbs = 819.2
        
        hbm4 = ComparisonResult()
        hbm4.peak_bandwidth_gbs = 2048.0
        
        speedup = hbm4.peak_bandwidth_gbs / hbm3.peak_bandwidth_gbs
        assert speedup == pytest.approx(2.5, rel=0.01)
    
    def test_latency_improvement(self):
        """Test latency improvement calculation"""
        hbm3 = ComparisonResult()
        hbm3.average_latency_ns = 50.0
        
        hbm4 = ComparisonResult()
        hbm4.average_latency_ns = 40.0
        
        improvement = (hbm3.average_latency_ns - hbm4.average_latency_ns) / hbm3.average_latency_ns
        assert improvement == pytest.approx(0.2, rel=0.01)  # 20% improvement