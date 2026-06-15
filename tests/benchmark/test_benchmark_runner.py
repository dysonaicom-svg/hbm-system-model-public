"""
Tests for Benchmark Runner Module
"""

import pytest
from model.benchmark.benchmark_runner import (
    BenchmarkRunner,
    BenchmarkReport,
)
from model.benchmark.benchmark_config import BenchmarkConfig


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner"""
    
    def test_initialization(self):
        runner = BenchmarkRunner()
        assert runner.config is not None
        assert runner.report is None
    
    def test_custom_config(self):
        config = BenchmarkConfig.quick()
        runner = BenchmarkRunner(config=config)
        assert runner.config.bandwidth.test_duration_ns == 1_000_000
    
    def test_initialization_with_comprehensive(self):
        config = BenchmarkConfig.comprehensive()
        runner = BenchmarkRunner(config=config)
        assert runner.config.comparison.configs_to_compare is not None


class TestBenchmarkReport:
    """Tests for BenchmarkReport"""
    
    def test_default_report(self):
        report = BenchmarkReport()
        assert report.timestamp == ""
        assert report.duration_seconds == 0.0
        assert report.peak_bandwidth_gbs == 0.0
        assert report.average_latency_ns == 0.0
    
    def test_report_to_dict(self):
        report = BenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"
        report.duration_seconds = 10.5
        report.peak_bandwidth_gbs = 2048.0
        report.average_latency_ns = 45.0
        report.p99_latency_ns = 75.0
        report.row_hit_rate_percent = 85.0
        report.bank_conflict_rate_percent = 10.0
        report.findings = ["Good bandwidth efficiency"]
        report.warnings = []
        
        d = report.to_dict()
        assert d['timestamp'] == "2026-01-01T00:00:00"
        assert d['duration_seconds'] == 10.5
        assert d['peak_bandwidth_gbs'] == 2048.0
        assert len(d['findings']) == 1
    
    def test_report_to_json(self):
        report = BenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"
        
        json_str = report.to_json()
        assert '"timestamp"' in json_str
        assert "2026-01-01" in json_str
    
    def test_report_to_markdown(self):
        report = BenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"
        report.duration_seconds = 10.5
        report.config = "Quick"
        report.peak_bandwidth_gbs = 2048.0
        report.sustained_bandwidth_gbs = 1800.0
        report.average_latency_ns = 45.0
        report.p99_latency_ns = 75.0
        report.row_hit_rate_percent = 85.0
        report.bank_conflict_rate_percent = 10.0
        
        md = report.to_markdown()
        assert "# HBM Performance Benchmark Report" in md
        assert "2048" in md
        assert "45" in md
        assert "85" in md


class TestFindingsGeneration:
    """Tests for findings generation"""
    
    def test_high_efficiency_finding(self):
        """Test high efficiency finding generation"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = type('obj', (object,), {
            'peak_efficiency_percent': 95.0,
            'refresh_overhead_percent': 1.0
        })()
        
        findings = runner._generate_findings(report)
        assert any("Excellent bandwidth efficiency" in f for f in findings)
    
    def test_low_efficiency_finding(self):
        """Test low efficiency finding generation"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = type('obj', (object,), {
            'peak_efficiency_percent': 60.0,
            'refresh_overhead_percent': 1.0
        })()
        
        findings = runner._generate_findings(report)
        assert any("Bandwidth efficiency below target" in f for f in findings)
    
    def test_high_latency_tail_finding(self):
        """Test high latency tail finding"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.latency = type('obj', (object,), {
            'average_latency_ns': 50.0,
            'p99_latency_ns': 200.0
        })()
        
        findings = runner._generate_findings(report)
        assert any("High latency tail" in f for f in findings)


class TestWarningsGeneration:
    """Tests for warnings generation"""
    
    def test_low_efficiency_warning(self):
        """Test low efficiency warning"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = type('obj', (object,), {
            'peak_efficiency_percent': 40.0,
            'refresh_overhead_percent': 6.0
        })()
        
        warnings = runner._generate_warnings(report)
        assert any("critically low" in w for w in warnings)
    
    def test_high_refresh_overhead_warning(self):
        """Test high refresh overhead warning"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = type('obj', (object,), {
            'peak_efficiency_percent': 85.0,
            'refresh_overhead_percent': 6.0
        })()
        
        warnings = runner._generate_warnings(report)
        assert any("Refresh overhead exceeds 5%" in w for w in warnings)
    
    def test_queue_overflow_warning(self):
        """Test queue overflow warning"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.scheduler = type('obj', (object,), {
            'average_queue_depth': 60.0,
            'queue_full_count': 5
        })()
        
        warnings = runner._generate_warnings(report)
        assert any("overflow" in w or "rejected" in w for w in warnings)


class TestQuickBenchmark:
    """Tests for quick benchmark"""
    
    def test_quick_benchmark_config(self):
        """Test quick benchmark configuration"""
        runner = BenchmarkRunner(BenchmarkConfig.quick())
        assert runner.config.bandwidth.test_duration_ns == 1_000_000
        assert runner.config.latency.num_requests == 1000
    
    def test_run_quick_benchmark_function(self):
        """Test run_quick_benchmark convenience function"""
        from model.benchmark.benchmark_runner import run_quick_benchmark
        # This will run actual benchmarks, just test the function exists
        assert callable(run_quick_benchmark)


class TestComprehensiveBenchmark:
    """Tests for comprehensive benchmark"""
    
    def test_comprehensive_config(self):
        """Test comprehensive benchmark configuration"""
        runner = BenchmarkRunner(BenchmarkConfig.comprehensive())
        assert runner.config.bandwidth.test_duration_ns == 100_000_000
        assert runner.config.latency.num_requests == 100_000
        assert len(runner.config.comparison.configs_to_compare) == 4