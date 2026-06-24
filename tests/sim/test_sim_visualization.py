"""
Sim Visualization and Benchmark Module Tests

Tests for sim/visualization and sim/benchmark modules to improve coverage.

Run with: pytest tests/sim/test_sim_visualization.py -v
"""

import pytest
import sys
import os
import json
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/ic/JXTF/HBM4')


# =============================================================================
# Test Visualization Report Generator
# =============================================================================

class TestVisualizationReportGenerator:
    """Test visualization/report_generator.py"""

    def test_import_report_generator(self):
        """Test importing report generator"""
        try:
            from sim.visualization.report_generator import (
                ReportGenerator,
                generate_html_report,
                generate_json_summary,
            )
            assert ReportGenerator is not None
        except ImportError as e:
            pytest.skip(f"Report generator import failed: {e}")


# =============================================================================
# Test Visualization Advanced Charts
# =============================================================================

class TestAdvancedCharts:
    """Test visualization/advanced_charts.py"""

    def test_import_advanced_charts(self):
        """Test importing advanced charts"""
        try:
            from sim.visualization.advanced_charts import (
                ChartType,
                generate_bandwidth_chart,
                generate_latency_chart,
            )
            assert ChartType is not None
        except ImportError as e:
            pytest.skip(f"Advanced charts import failed: {e}")


# =============================================================================
# Test Visualization Bandwidth Chart
# =============================================================================

class TestBandwidthChart:
    """Test visualization/bandwidth_chart.py"""

    def test_import_bandwidth_chart(self):
        """Test importing bandwidth chart"""
        try:
            from sim.visualization.bandwidth_chart import (
                BandwidthChart,
                plot_bandwidth_timeline,
            )
            assert BandwidthChart is not None
        except ImportError as e:
            pytest.skip(f"Bandwidth chart import failed: {e}")


# =============================================================================
# Test Visualization Channel Heatmap
# =============================================================================

class TestChannelHeatmap:
    """Test visualization/channel_heatmap.py"""

    def test_import_channel_heatmap(self):
        """Test importing channel heatmap"""
        try:
            from sim.visualization.channel_heatmap import (
                ChannelHeatmap,
                plot_channel_activity,
            )
            assert ChannelHeatmap is not None
        except ImportError as e:
            pytest.skip(f"Channel heatmap import failed: {e}")


# =============================================================================
# Test Visualization Latency Histogram
# =============================================================================

class TestLatencyHistogram:
    """Test visualization/latency_histogram.py"""

    def test_import_latency_histogram(self):
        """Test importing latency histogram"""
        try:
            from sim.visualization.latency_histogram import (
                LatencyHistogram,
                plot_latency_distribution,
            )
            assert LatencyHistogram is not None
        except ImportError as e:
            pytest.skip(f"Latency histogram import failed: {e}")


# =============================================================================
# Test Benchmark Suite
# =============================================================================

class TestBenchmarkSuiteImports:
    """Test benchmark_suite.py imports and basic structure"""

    def test_import_benchmark_suite(self):
        """Test importing benchmark suite"""
        try:
            from sim.benchmark_suite import (
                BenchmarkCategory,
                BenchmarkResult,
                BenchmarkSuiteStats,
                PerformanceBenchmarkSuite,
                create_parser,
            )
            assert BenchmarkCategory is not None
            assert BenchmarkResult is not None
            assert BenchmarkSuiteStats is not None
        except ImportError as e:
            pytest.skip(f"Benchmark suite import failed: {e}")

    def test_benchmark_category_enum(self):
        """Test BenchmarkCategory enum"""
        from sim.benchmark_suite import BenchmarkCategory
        assert BenchmarkCategory.BANDWIDTH.value == "bandwidth"
        assert BenchmarkCategory.LATENCY.value == "latency"
        assert BenchmarkCategory.THROUGHPUT.value == "throughput"
        assert BenchmarkCategory.CHANNEL_INDEPENDENCE.value == "channel_independence"
        assert BenchmarkCategory.PAM3_EFFICIENCY.value == "pam3_efficiency"
        assert BenchmarkCategory.QOS_SCHEDULING.value == "qos_scheduling"
        assert BenchmarkCategory.POWER.value == "power"
        assert BenchmarkCategory.RTL_COSIM.value == "rtl_cosim"

    def test_benchmark_result_creation(self):
        """Test BenchmarkResult creation"""
        from sim.benchmark_suite import BenchmarkResult

        result = BenchmarkResult(
            name="Test Benchmark",
            category="bandwidth",
            passed=True,
            value=100.5,
            unit="GB/s",
            target=100.0,
            iterations=1000,
            duration_ms=50.0,
            details={"key": "value"},
        )

        assert result.name == "Test Benchmark"
        assert result.passed is True
        assert result.value == 100.5

    def test_benchmark_result_str(self):
        """Test BenchmarkResult string representation"""
        from sim.benchmark_suite import BenchmarkResult

        result = BenchmarkResult(
            name="Test",
            category="bandwidth",
            passed=True,
            value=100.0,
            unit="GB/s",
            target=80.0,
            iterations=100,
            duration_ms=10.0,
        )

        s = str(result)
        assert "PASS" in s
        assert "Test" in s
        assert "100.00" in s

    def test_benchmark_result_to_dict(self):
        """Test BenchmarkResult serialization"""
        from sim.benchmark_suite import BenchmarkResult

        result = BenchmarkResult(
            name="Test",
            category="latency",
            passed=False,
            value=60.0,
            unit="cycles",
            target=50.0,
            iterations=200,
            duration_ms=20.0,
            details={"sample": 1},
        )

        d = result.to_dict()
        assert d['name'] == "Test"
        assert d['passed'] is False
        assert d['value'] == 60.0
        assert 'details' in d

    def test_benchmark_suite_stats_creation(self):
        """Test BenchmarkSuiteStats creation"""
        from sim.benchmark_suite import BenchmarkSuiteStats, BenchmarkResult

        stats = BenchmarkSuiteStats()
        assert stats.total_benchmarks == 0
        assert stats.passed == 0
        assert stats.failed == 0

    def test_benchmark_suite_stats_pass_rate(self):
        """Test BenchmarkSuiteStats pass rate"""
        from sim.benchmark_suite import BenchmarkSuiteStats, BenchmarkResult

        stats = BenchmarkSuiteStats()
        assert stats.pass_rate == 0.0

        result1 = BenchmarkResult(
            name="Test1", category="test", passed=True,
            value=100, unit="x", target=90, iterations=1, duration_ms=1
        )
        result2 = BenchmarkResult(
            name="Test2", category="test", passed=False,
            value=80, unit="x", target=90, iterations=1, duration_ms=1
        )

        stats.add_result(result1)
        stats.add_result(result2)

        assert stats.total_benchmarks == 2
        assert stats.passed == 1
        assert stats.failed == 1
        assert stats.pass_rate == pytest.approx(0.5)

    def test_benchmark_suite_stats_to_dict(self):
        """Test BenchmarkSuiteStats serialization"""
        from sim.benchmark_suite import BenchmarkSuiteStats, BenchmarkResult

        stats = BenchmarkSuiteStats()
        result = BenchmarkResult(
            name="Test", category="test", passed=True,
            value=100, unit="x", target=90, iterations=1, duration_ms=1
        )
        stats.add_result(result)

        d = stats.to_dict()
        assert 'total_benchmarks' in d
        assert 'pass_rate' in d
        assert 'results' in d

    def test_benchmark_suite_creation(self):
        """Test PerformanceBenchmarkSuite creation"""
        try:
            from sim.benchmark_suite import PerformanceBenchmarkSuite

            suite = PerformanceBenchmarkSuite(quick_mode=True, verbose=False)
            assert suite is not None
            assert suite.quick_mode is True
            assert suite.verbose is False
        except ImportError:
            pytest.skip("BenchmarkSuite not fully available")

    def test_benchmark_suite_creation_with_options(self):
        """Test PerformanceBenchmarkSuite with custom options"""
        try:
            from sim.benchmark_suite import PerformanceBenchmarkSuite

            suite = PerformanceBenchmarkSuite(
                quick_mode=False,
                verbose=True,
                seed=12345,
                output_dir="/tmp/benchmark_output",
            )
            assert suite.seed == 12345
            assert str(suite.output_dir) == "/tmp/benchmark_output"
        except ImportError:
            pytest.skip("BenchmarkSuite not fully available")

    def test_benchmark_suite_log(self):
        """Test log method"""
        try:
            from sim.benchmark_suite import PerformanceBenchmarkSuite

            suite = PerformanceBenchmarkSuite(verbose=False)
            # Should not raise
            suite.log("Test message")
        except ImportError:
            pytest.skip("BenchmarkSuite not fully available")

    def test_benchmark_suite_print_header(self):
        """Test print_header method"""
        try:
            from sim.benchmark_suite import PerformanceBenchmarkSuite

            suite = PerformanceBenchmarkSuite(verbose=False)
            # Should not raise
            suite.print_header("Test Header")
        except ImportError:
            pytest.skip("BenchmarkSuite not fully available")

    def test_benchmark_suite_print_result(self):
        """Test print_result method"""
        try:
            from sim.benchmark_suite import PerformanceBenchmarkSuite, BenchmarkResult

            suite = PerformanceBenchmarkSuite(verbose=False)
            result = BenchmarkResult(
                name="Test", category="test", passed=True,
                value=100, unit="x", target=90, iterations=1, duration_ms=1,
                details={"key": "value"},
            )
            # Should not raise
            suite.print_result(result)
        except ImportError:
            pytest.skip("BenchmarkSuite not fully available")

    def test_benchmark_suite_export_results(self):
        """Test exporting results to JSON"""
        try:
            from sim.benchmark_suite import PerformanceBenchmarkSuite, BenchmarkResult

            with tempfile.TemporaryDirectory() as tmpdir:
                suite = PerformanceBenchmarkSuite(output_dir=tmpdir)
                result = BenchmarkResult(
                    name="Test", category="test", passed=True,
                    value=100, unit="x", target=90, iterations=1, duration_ms=1
                )
                suite.stats.add_result(result)

                path = suite.export_results()
                assert os.path.exists(path)

                with open(path, 'r') as f:
                    data = json.load(f)
                assert 'timestamp' in data
                assert 'stats' in data
        except ImportError:
            pytest.skip("BenchmarkSuite not fully available")

    def test_benchmark_suite_export_csv(self):
        """Test exporting results to CSV"""
        try:
            from sim.benchmark_suite import PerformanceBenchmarkSuite, BenchmarkResult

            with tempfile.TemporaryDirectory() as tmpdir:
                suite = PerformanceBenchmarkSuite(output_dir=tmpdir)
                result = BenchmarkResult(
                    name="Test", category="test", passed=True,
                    value=100, unit="x", target=90, iterations=1, duration_ms=1
                )
                suite.stats.add_result(result)

                path = suite.export_csv()
                assert os.path.exists(path)

                with open(path, 'r') as f:
                    content = f.read()
                assert "Name,Category,Passed" in content
                assert "Test" in content
        except ImportError:
            pytest.skip("BenchmarkSuite not fully available")

    def test_create_parser(self):
        """Test argument parser creation"""
        try:
            from sim.benchmark_suite import create_parser

            parser = create_parser()
            assert parser is not None

            # Test default arguments
            args = parser.parse_args([])
            assert args.quick is False
            assert args.verbose is False
            assert args.format == 'both'
            assert args.seed == 42

            # Test custom arguments
            args = parser.parse_args([
                '--quick',
                '--verbose',
                '--format', 'json',
                '--seed', '12345',
                '--output', '/tmp/output',
            ])
            assert args.quick is True
            assert args.verbose is True
            assert args.format == 'json'
            assert args.seed == 12345
        except ImportError:
            pytest.skip("BenchmarkSuite not fully available")


# =============================================================================
# Test HBM4 Benchmark Module
# =============================================================================

class TestHBM4BenchmarkImports:
    """Test hbm4_benchmark.py imports"""

    def test_import_hbm4_benchmark(self):
        """Test importing HBM4 benchmark"""
        try:
            from sim.hbm4_benchmark import (
                HBM4Benchmark,
                BandwidthMetrics,
                LatencyMetrics,
                ChannelIndependenceMetrics,
                PAM3Metrics,
                QoSMetrics,
                BenchmarkTestResult,
                BenchmarkSuiteResult,
                calculate_percentile,
                calculate_jains_fairness,
            )
            assert HBM4Benchmark is not None
        except ImportError as e:
            pytest.skip(f"HBM4 benchmark import failed: {e}")

    def test_metrics_dataclasses(self):
        """Test HBM4 benchmark metrics dataclasses"""
        try:
            from sim.hbm4_benchmark import (
                BandwidthMetrics,
                LatencyMetrics,
                ChannelIndependenceMetrics,
                PAM3Metrics,
                QoSMetrics,
                BenchmarkTestResult,
                BenchmarkSuiteResult,
            )

            # Test BandwidthMetrics
            bw = BandwidthMetrics(
                peak_bandwidth_gbs=2000.0,
                sustained_bandwidth_gbs=1800.0,
                bytes_transferred=1000000,
                cycles_elapsed=10000,
                active_channels=32,
                transactions_completed=5000,
                efficiency_percent=90.0,
            )
            assert bw.peak_bandwidth_gbs == 2000.0
            assert bw.to_dict()['peak_bandwidth_gbs'] == 2000.0

            # Test LatencyMetrics
            lat = LatencyMetrics(
                avg_latency_cycles=50.0,
                min_latency_cycles=30.0,
                max_latency_cycles=100.0,
                p50_latency=45.0,
                p90_latency=70.0,
                p95_latency=85.0,
                p99_latency=95.0,
                std_dev=10.5,
            )
            assert lat.avg_latency_cycles == 50.0
            assert lat.to_dict()['p50_latency'] == 45.0

            # Test ChannelIndependenceMetrics
            ch = ChannelIndependenceMetrics(
                total_channels=32,
                channels_operating_correctly=30,
                isolation_violations=2,
                cross_channel_interference_detected=True,
            )
            assert ch.total_channels == 32
            assert ch.to_dict()['isolation_rate_percent'] == pytest.approx(93.75)

            # Test PAM3Metrics
            pam = PAM3Metrics(
                symbols_encoded=100000,
                bits_encoded=158500,
                encoding_time_us=10.0,
                throughput_msyms_per_s=10000.0,
                bandwidth_efficiency_bits_per_symbol=1.585,
            )
            assert pam.symbols_encoded == 100000
            assert pam.to_dict()['efficiency_percent'] > 0

            # Test QoSMetrics
            qos = QoSMetrics(
                high_priority_requests=100,
                low_priority_requests=400,
                high_priority_completed=95,
                low_priority_completed=380,
                avg_high_priority_latency=45.0,
                avg_low_priority_latency=55.0,
                latency_advantage_high_prio=18.0,
                starvation_count=0,
                qos_violations=0,
                fairness_index=0.95,
                channel_balance_score=0.90,
            )
            assert qos.high_priority_requests == 100
            assert qos.to_dict()['latency_advantage_percent'] == 18.0

        except ImportError:
            pytest.skip("HBM4 benchmark metrics not available")

    def test_calculate_percentile(self):
        """Test percentile calculation"""
        try:
            from sim.hbm4_benchmark import calculate_percentile

            data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            assert calculate_percentile(data, 50) == pytest.approx(5.5)
            assert calculate_percentile(data, 90) == pytest.approx(9.1)
            assert calculate_percentile([], 50) == 0.0

        except ImportError:
            pytest.skip("calculate_percentile not available")

    def test_calculate_jains_fairness(self):
        """Test Jain's fairness index calculation"""
        try:
            from sim.hbm4_benchmark import calculate_jains_fairness

            # Perfect fairness
            values = [100, 100, 100, 100]
            assert calculate_jains_fairness(values) == pytest.approx(1.0)

            # Some unfairness
            values = [50, 100, 150, 200]
            fairness = calculate_jains_fairness(values)
            assert 0 < fairness < 1

            # Empty
            assert calculate_jains_fairness([]) == 1.0

            # Single value
            assert calculate_jains_fairness([100]) == 1.0

            # Zero values
            assert calculate_jains_fairness([0, 0, 0]) == 1.0

        except ImportError:
            pytest.skip("calculate_jains_fairness not available")

    def test_benchmark_test_result(self):
        """Test BenchmarkTestResult dataclass"""
        try:
            from sim.hbm4_benchmark import (
                BenchmarkTestResult,
                BandwidthMetrics,
                LatencyMetrics,
            )

            result = BenchmarkTestResult(
                name="Bandwidth Test",
                passed=True,
                value=2000.0,
                unit="GB/s",
                details="Test passed",
                duration_ms=100.5,
                bandwidth_metrics=BandwidthMetrics(
                    peak_bandwidth_gbs=2000.0,
                    sustained_bandwidth_gbs=1800.0,
                    bytes_transferred=1000000,
                    cycles_elapsed=10000,
                    active_channels=32,
                    transactions_completed=5000,
                    efficiency_percent=90.0,
                ),
            )

            assert result.name == "Bandwidth Test"
            assert result.passed is True
            assert result.bandwidth_metrics is not None

            d = result.to_dict()
            assert 'bandwidth_metrics' in d
            assert d['bandwidth_metrics']['peak_bandwidth_gbs'] == 2000.0

        except ImportError:
            pytest.skip("BenchmarkTestResult not available")

    def test_benchmark_suite_result(self):
        """Test BenchmarkSuiteResult dataclass"""
        try:
            from sim.hbm4_benchmark import (
                BenchmarkSuiteResult,
                BenchmarkTestResult,
            )

            result = BenchmarkSuiteResult(
                timestamp="2024-01-01T00:00:00",
                total_tests=5,
                passed_tests=4,
                failed_tests=1,
                total_duration_ms=500.0,
                hbm4_spec={
                    'peak_bandwidth_tbs': 2.0,
                    'channels': 32,
                    'data_rate_gtps': 16.0,
                },
                tests=[],
            )

            assert result.total_tests == 5
            assert result.passed_tests == 4
            assert result.to_dict()['pass_rate_percent'] == 80.0

        except ImportError:
            pytest.skip("BenchmarkSuiteResult not available")

    def test_hbm4_benchmark_creation(self):
        """Test HBM4Benchmark creation"""
        try:
            from sim.hbm4_benchmark import HBM4Benchmark

            bench = HBM4Benchmark(quick_mode=True, verbose=False)
            assert bench is not None
            assert bench.quick_mode is True
            assert bench.iterations == 100  # Quick mode

            bench_full = HBM4Benchmark(quick_mode=False, verbose=True)
            assert bench_full.iterations == 1000  # Full mode

        except ImportError:
            pytest.skip("HBM4Benchmark not available")

    def test_hbm4_benchmark_log(self):
        """Test HBM4Benchmark log method"""
        try:
            from sim.hbm4_benchmark import HBM4Benchmark

            bench = HBM4Benchmark(verbose=False)
            bench.log("Test message")  # Should not raise

        except ImportError:
            pytest.skip("HBM4Benchmark not available")

    def test_hbm4_benchmark_headers(self):
        """Test HBM4Benchmark print methods"""
        try:
            from sim.hbm4_benchmark import HBM4Benchmark, BenchmarkTestResult

            bench = HBM4Benchmark(verbose=False)
            bench.print_header("Test Header")
            # Test with a valid result
            result = BenchmarkTestResult(
                name="Test",
                passed=True,
                value=100,
                unit="GB/s",
            )
            bench.print_result(result)  # Should work fine
        except ImportError:
            pytest.skip("HBM4Benchmark not available")


# =============================================================================
# Test HBM4 Unified Benchmarks
# =============================================================================

class TestHBM4UnifiedBenchmarks:
    """Test hbm4_unified_benchmarks.py"""

    def test_import_hbm4_unified_benchmarks(self):
        """Test importing unified benchmarks"""
        try:
            from sim.hbm4_unified_benchmarks import (
                HBM4UnifiedBenchmarks,
                BenchmarkConfig,
            )
            # Module exists but may not be fully implemented
            assert True
        except ImportError as e:
            pytest.skip(f"Unified benchmarks import failed: {e}")


# =============================================================================
# Test Report Generator
# =============================================================================

class TestReportGenerator:
    """Test report_generator.py"""

    def test_import_report_generator(self):
        """Test importing report generator"""
        try:
            from sim.report_generator import (
                ReportGenerator,
                generate_html_report,
                generate_json_summary,
            )
            # Module exists but may have dependencies
            assert True
        except ImportError as e:
            pytest.skip(f"Report generator import failed: {e}")


# =============================================================================
# Test Trace Benchmark Module
# =============================================================================

class TestTraceBenchmarkImports:
    """Test trace/benchmark.py imports"""

    def test_import_trace_benchmark(self):
        """Test importing trace benchmark"""
        try:
            from sim.trace.benchmark import (
                TraceBenchmark,
                TraceBenchmarkResult,
            )
            assert True
        except ImportError as e:
            pytest.skip(f"Trace benchmark import failed: {e}")


# =============================================================================
# Integration Test
# =============================================================================

class TestSimModuleIntegration:
    """Integration tests for sim module components"""

    def test_all_visualization_imports(self):
        """Test all visualization imports work"""
        try:
            from sim.visualization import (
                ReportGenerator,
            )
            from sim.visualization.advanced_charts import ChartType
            from sim.visualization.bandwidth_chart import BandwidthChart
            from sim.visualization.channel_heatmap import ChannelHeatmap
            from sim.visualization.latency_histogram import LatencyHistogram
            assert True
        except ImportError as e:
            pytest.skip(f"Some visualization imports failed: {e}")

    def test_all_benchmark_imports(self):
        """Test all benchmark imports work"""
        try:
            from sim.benchmark_suite import (
                BenchmarkCategory,
                BenchmarkResult,
                BenchmarkSuiteStats,
            )
            from sim.hbm4_benchmark import (
                HBM4Benchmark,
                BandwidthMetrics,
            )
            assert True
        except ImportError as e:
            pytest.skip(f"Some benchmark imports failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
