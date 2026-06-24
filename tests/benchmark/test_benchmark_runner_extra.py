"""
Additional Tests for Benchmark Runner Module

Covers edge cases and additional functionality.

Run with: pytest tests/benchmark/test_benchmark_runner_extra.py -v
"""

import pytest
from model.benchmark.benchmark_runner import (
    BenchmarkRunner,
    BenchmarkReport,
    run_quick_benchmark,
    run_comprehensive_benchmark,
)
from model.benchmark.benchmark_config import BenchmarkConfig


class TestBenchmarkRunnerMethods:
    """Tests for BenchmarkRunner methods"""

    def test_run_bandwidth_benchmarks(self):
        """Test running bandwidth benchmarks"""
        config = BenchmarkConfig(run_bandwidth=True)
        runner = BenchmarkRunner(config=config)

        result = runner.run_bandwidth_benchmarks()

        assert result is not None
        assert hasattr(result, 'peak_bandwidth_gbs')

    def test_run_latency_benchmarks(self):
        """Test running latency benchmarks"""
        config = BenchmarkConfig(run_latency=True)
        config.latency.num_requests = 100
        runner = BenchmarkRunner(config=config)

        result = runner.run_latency_benchmarks()

        assert result is not None
        assert hasattr(result, 'average_latency_ns')

    def test_run_scheduler_benchmarks(self):
        """Test running scheduler benchmarks"""
        config = BenchmarkConfig(run_scheduler=True)
        config.scheduler.test_duration_ns = 1_000_000
        runner = BenchmarkRunner(config=config)

        result = runner.run_scheduler_benchmarks()

        assert result is not None
        assert hasattr(result, 'row_hit_rate_percent')

    def test_run_comparison_benchmarks(self):
        """Test running comparison benchmarks"""
        config = BenchmarkConfig(run_comparison=True)
        config.comparison.configs_to_compare = [
            ("HBM4-8G", type('obj', (object,), {'version': 'hbm4', 'data_rate': 8.0, 'io_width': 2048})())
        ]
        runner = BenchmarkRunner(config=config)

        result = runner.run_comparison_benchmarks()

        assert result is not None


class TestBenchmarkReportMethods:
    """Tests for BenchmarkReport methods"""

    def test_to_dict_complete(self):
        """Test to_dict with all fields"""
        report = BenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"
        report.duration_seconds = 100.5
        report.config = "TestConfig"
        report.peak_bandwidth_gbs = 2048.0
        report.sustained_bandwidth_gbs = 1800.0
        report.average_latency_ns = 45.0
        report.p99_latency_ns = 75.0
        report.row_hit_rate_percent = 85.0
        report.bank_conflict_rate_percent = 10.0
        report.multi_channel_efficiency_percent = 80.0
        report.refresh_bandwidth_loss_percent = 2.0
        report.qos_effectiveness_percent = 90.0
        report.findings = ["Finding 1", "Finding 2"]
        report.warnings = ["Warning 1"]

        d = report.to_dict()

        assert d['timestamp'] == "2026-01-01T00:00:00"
        assert d['duration_seconds'] == 100.5
        assert d['peak_bandwidth_gbs'] == 2048.0
        assert d['average_latency_ns'] == 45.0
        assert d['row_hit_rate_percent'] == 85.0
        assert len(d['findings']) == 2
        assert len(d['warnings']) == 1

    def test_to_json_format(self):
        """Test JSON serialization"""
        report = BenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"

        json_str = report.to_json(indent=4)

        assert '"timestamp"' in json_str
        assert '"2026-01-01T00:00:00"' in json_str

    def test_to_markdown_complete(self):
        """Test markdown generation with all sections"""
        report = BenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"
        report.duration_seconds = 100.5
        report.config = "TestConfig"
        report.peak_bandwidth_gbs = 2048.0
        report.sustained_bandwidth_gbs = 1800.0
        report.average_latency_ns = 45.0
        report.p99_latency_ns = 75.0
        report.row_hit_rate_percent = 85.0
        report.bank_conflict_rate_percent = 10.0
        report.findings = ["Excellent bandwidth efficiency"]
        report.warnings = ["Queue overflow detected"]

        md = report.to_markdown()

        assert "# HBM Performance Benchmark Report" in md
        assert "2026-01-01" in md
        assert "2048" in md
        assert "45" in md
        assert "85" in md
        assert "Findings" in md


class TestBenchmarkRunnerFindings:
    """Tests for findings generation"""

    def test_findings_bandwidth_high_efficiency(self):
        """Test findings with high bandwidth efficiency"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = type('obj', (object,), {
            'peak_efficiency_percent': 92.0,
            'refresh_overhead_percent': 1.0
        })()

        findings = runner._generate_findings(report)

        assert any("Excellent" in f for f in findings)

    def test_findings_bandwidth_good_efficiency(self):
        """Test findings with good bandwidth efficiency"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = type('obj', (object,), {
            'peak_efficiency_percent': 75.0,
            'refresh_overhead_percent': 1.0
        })()

        findings = runner._generate_findings(report)

        assert any("Good bandwidth efficiency" in f for f in findings)

    def test_findings_refresh_overhead(self):
        """Test findings with refresh overhead"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = type('obj', (object,), {
            'peak_efficiency_percent': 90.0,
            'refresh_overhead_percent': 3.0
        })()

        findings = runner._generate_findings(report)

        assert any("Refresh overhead significant" in f for f in findings)

    def test_findings_low_latency_tail(self):
        """Test findings with low latency tail"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.latency = type('obj', (object,), {
            'average_latency_ns': 50.0,
            'p99_latency_ns': 120.0
        })()

        findings = runner._generate_findings(report)

        assert any("Consistent latency" in f for f in findings)

    def test_findings_scheduler_row_hit_high(self):
        """Test findings with high row hit rate"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.scheduler = type('obj', (object,), {
            'row_hit_rate_percent': 85.0,
            'bank_conflict_rate_percent': 10.0
        })()

        findings = runner._generate_findings(report)

        assert any("Excellent row locality" in f for f in findings)

    def test_findings_scheduler_row_hit_low(self):
        """Test findings with low row hit rate"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.scheduler = type('obj', (object,), {
            'row_hit_rate_percent': 40.0,
            'bank_conflict_rate_percent': 10.0
        })()

        findings = runner._generate_findings(report)

        assert any("needs improvement" in f.lower() for f in findings)

    def test_findings_scheduler_high_conflict(self):
        """Test findings with high bank conflict"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.scheduler = type('obj', (object,), {
            'row_hit_rate_percent': 80.0,
            'bank_conflict_rate_percent': 25.0
        })()

        findings = runner._generate_findings(report)

        assert any("High bank conflict" in f for f in findings)

    def test_findings_comparison(self):
        """Test findings from comparison"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()

        class MockComparison:
            hbm4_vs_hbm3_bandwidth_speedup = 2.5
            hbm4_vs_hbm3_latency_improvement = 0.2

        report.comparison = MockComparison()

        findings = runner._generate_findings(report)

        assert any("2.5x" in f for f in findings)
        assert any("improvement" in f.lower() or "20%" in f for f in findings)


class TestBenchmarkRunnerWarnings:
    """Tests for warnings generation"""

    def test_warnings_latency_high(self):
        """Test warnings with high latency"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.latency = type('obj', (object,), {
            'average_latency_ns': 150.0
        })()

        warnings = runner._generate_warnings(report)

        assert any("100ns" in w or "exceeds" in w.lower() for w in warnings)

    def test_warnings_queue_depth(self):
        """Test warnings with high queue depth"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.scheduler = type('obj', (object,), {
            'average_queue_depth': 55.0,
            'queue_full_count': 0
        })()

        warnings = runner._generate_warnings(report)

        assert any("queue" in w.lower() for w in warnings)

    def test_warnings_no_queue_overflow(self):
        """Test warnings without queue overflow"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.scheduler = type('obj', (object,), {
            'average_queue_depth': 30.0,
            'queue_full_count': 0
        })()

        warnings = runner._generate_warnings(report)

        # Should not have overflow warning
        assert not any("overflow" in w.lower() or "rejected" in w.lower() for w in warnings)


class TestBenchmarkRunnerAllBenchmarks:
    """Tests for run_all_benchmarks"""

    def test_run_all_benchmarks_bandwidth_only(self):
        """Test running bandwidth only"""
        config = BenchmarkConfig(
            run_bandwidth=True,
            run_latency=False,
            run_scheduler=False,
            run_comparison=False
        )
        config.bandwidth.test_duration_ns = 50_000
        runner = BenchmarkRunner(config=config)

        report = runner.run_all_benchmarks()

        assert report.bandwidth is not None
        assert report.latency is None
        assert report.scheduler is None

    def test_run_all_benchmarks_latency_only(self):
        """Test running latency only"""
        config = BenchmarkConfig(
            run_bandwidth=False,
            run_latency=True,
            run_scheduler=False,
            run_comparison=False
        )
        config.latency.num_requests = 100
        runner = BenchmarkRunner(config=config)

        report = runner.run_all_benchmarks()

        assert report.bandwidth is None
        assert report.latency is not None
        assert report.scheduler is None

    def test_run_all_benchmarks_none_enabled(self):
        """Test running with no benchmarks enabled"""
        config = BenchmarkConfig(
            run_bandwidth=False,
            run_latency=False,
            run_scheduler=False,
            run_comparison=False
        )
        runner = BenchmarkRunner(config=config)

        report = runner.run_all_benchmarks()

        assert report is not None


class TestBenchmarkRunnerSaveReport:
    """Tests for report saving"""

    def test_save_report_markdown(self, tmp_path):
        """Test saving report as markdown"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"
        runner.report = report

        filepath = tmp_path / "report.md"
        result = runner.save_report(str(filepath), format="markdown")

        assert filepath.exists()
        content = filepath.read_text()
        assert "HBM Performance Benchmark Report" in content

    def test_save_report_json(self, tmp_path):
        """Test saving report as JSON"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"
        runner.report = report

        filepath = tmp_path / "report.json"
        result = runner.save_report(str(filepath), format="json")

        assert filepath.exists()
        content = filepath.read_text()
        assert '"timestamp"' in content

    def test_save_report_no_report(self):
        """Test saving with no report"""
        runner = BenchmarkRunner()
        runner.report = None

        with pytest.raises(ValueError):
            runner.save_report("test.md")


class TestQuickComprehensiveBenchmark:
    """Tests for quick and comprehensive benchmarks"""

    def test_run_quick_benchmark_function(self):
        """Test run_quick_benchmark function"""
        report = run_quick_benchmark()

        assert isinstance(report, BenchmarkReport)
        assert report is not None

    def test_run_comprehensive_benchmark_function(self):
        """Test run_comprehensive_benchmark function"""
        report = run_comprehensive_benchmark()

        assert isinstance(report, BenchmarkReport)
        assert report is not None


class TestBenchmarkRunnerEdgeCases:
    """Tests for edge cases"""

    def test_runner_with_none_config(self):
        """Test runner with None config"""
        runner = BenchmarkRunner(config=None)

        assert runner.config is not None

    def test_report_with_no_results(self):
        """Test report with no results"""
        report = BenchmarkReport()

        # Should have default values
        assert report.peak_bandwidth_gbs == 0.0
        assert report.average_latency_ns == 0.0
        assert len(report.findings) == 0
        assert len(report.warnings) == 0

    def test_findings_with_none_results(self):
        """Test findings with None results"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = None
        report.latency = None
        report.scheduler = None
        report.comparison = None
        report.enhanced = None

        findings = runner._generate_findings(report)

        assert isinstance(findings, list)

    def test_warnings_with_none_results(self):
        """Test warnings with None results"""
        runner = BenchmarkRunner()
        report = BenchmarkReport()
        report.bandwidth = None
        report.latency = None
        report.scheduler = None
        report.enhanced = None

        warnings = runner._generate_warnings(report)

        assert isinstance(warnings, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
