"""
Tests for HBM3 Ramulator2 vs Python model comparison framework
"""
import pytest
from sim.comparison_framework import (
    ComparisonFramework,
    ComparisonMetrics,
    ComparisonReport,
    RamulatorResult,
    parse_ramulator_log
)


class TestComparisonMetrics:
    """Test comparison metrics"""

    def test_row_hit_rate_calculation(self):
        """Test row hit rate calculation"""
        metrics = ComparisonMetrics(
            row_hits=625,
            row_misses=250,
            row_conflicts=125,
            avg_latency=12.0
        )
        # 625 / (625 + 250 + 125) = 625 / 1000 = 0.625
        assert abs(metrics.row_hit_rate - 0.625) < 0.001

    def test_zero_total_returns_zero_hit_rate(self):
        """Test zero total returns 0"""
        metrics = ComparisonMetrics()
        assert metrics.row_hit_rate == 0.0

    def test_hit_rate_with_only_hits(self):
        """Test hit rate when only hits exist"""
        metrics = ComparisonMetrics(row_hits=1000, row_misses=0, row_conflicts=0)
        assert metrics.row_hit_rate == 1.0

    def test_hit_rate_with_no_hits(self):
        """Test hit rate when no hits exist"""
        metrics = ComparisonMetrics(row_hits=0, row_misses=500, row_conflicts=500)
        assert metrics.row_hit_rate == 0.0

    def test_to_dict_includes_row_hit_rate(self):
        """Test to_dict includes row_hit_rate property"""
        metrics = ComparisonMetrics(
            row_hits=625,
            row_misses=250,
            row_conflicts=125,
            avg_latency=12.0
        )
        d = metrics.to_dict()
        assert 'row_hit_rate' in d
        assert abs(d['row_hit_rate'] - 0.625) < 0.001


class TestComparisonReport:
    """Test comparison report"""

    def test_compute_errors(self):
        """Test error computation"""
        ramulator = ComparisonMetrics(
            row_hits=62481,
            row_misses=24992,
            row_conflicts=12495,
            avg_latency=12.93
        )
        python = ComparisonMetrics(
            row_hits=50000,  # Different value
            row_misses=30000,
            row_conflicts=20000,
            avg_latency=15.0
        )

        report = ComparisonReport(
            trace_name='test',
            ramulator_metrics=ramulator,
            python_metrics=python
        )
        report.compute_errors()

        assert 'hit_rate_error_pp' in report.errors
        assert 'latency_error_pct' in report.errors
        assert report.errors['hit_rate_error_pp'] > 0

    def test_compute_errors_perfect_match(self):
        """Test error computation with perfect match"""
        metrics = ComparisonMetrics(
            row_hits=62481,
            row_misses=24992,
            row_conflicts=12495,
            avg_latency=12.93
        )

        report = ComparisonReport(
            trace_name='test',
            ramulator_metrics=metrics,
            python_metrics=metrics
        )
        report.compute_errors()

        assert report.errors['hit_rate_error_pp'] == 0.0
        assert report.errors['latency_error_pct'] == 0.0

    def test_to_dict_format(self):
        """Test to_dict output format"""
        ramulator = ComparisonMetrics(
            row_hits=62481,
            row_misses=24992,
            row_conflicts=12495,
            avg_latency=12.93
        )
        python = ComparisonMetrics(
            row_hits=50000,
            row_misses=30000,
            row_conflicts=20000,
            avg_latency=15.0
        )

        report = ComparisonReport(
            trace_name='seq_rd',
            ramulator_metrics=ramulator,
            python_metrics=python
        )

        d = report.to_dict()
        assert d['trace_name'] == 'seq_rd'
        assert 'ramulator' in d
        assert 'python' in d
        assert 'errors' in d
        assert 'timestamp' in d


class TestParseRamulatorLog:
    """Test Ramulator log parsing"""

    def test_parse_sample_log(self, tmp_path):
        """Test parsing sample log"""
        log_content = """
=== HBM3 Simulation ===
Average latency: 12.93 cycles
Total requests: 100000
Row hits: 62481
Row misses: 24992
Row conflicts: 12495
"""
        log_file = tmp_path / "test.log"
        log_file.write_text(log_content)

        result = parse_ramulator_log(str(log_file), 'test')
        assert result.trace_name == 'test'
        assert result.avg_latency == 12.93

    def test_parse_log_with_average_latency(self, tmp_path):
        """Test parsing log with average latency format"""
        log_content = """
Simulation complete.
Average latency: 15.5
Total Cycles: 1000000
"""
        log_file = tmp_path / "test2.log"
        log_file.write_text(log_content)

        result = parse_ramulator_log(str(log_file), 'test2')
        assert result.avg_latency == 15.5

    def test_parse_empty_log(self, tmp_path):
        """Test parsing empty log uses defaults for unknown trace"""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")

        result = parse_ramulator_log(str(log_file), 'empty')
        # Should return defaults for unknown trace (empty string doesn't match known traces)
        assert result.trace_name == 'empty'
        # Unknown trace returns zero values
        assert result.total_requests == 0
        assert result.row_hits == 0


class TestRamulatorResult:
    """Test RamulatorResult dataclass"""

    def test_ramulator_result_creation(self):
        """Test creating RamulatorResult"""
        result = RamulatorResult(
            trace_name='seq_rd',
            total_requests=100000,
            row_hits=62481,
            row_misses=24992,
            row_conflicts=12495,
            avg_latency=12.93,
            total_cycles=924397
        )

        assert result.trace_name == 'seq_rd'
        assert result.total_requests == 100000
        assert result.row_hits == 62481
        assert result.avg_latency == 12.93


class TestComparisonFrameworkKnownResults:
    """Test known Ramulator results from summary.md"""

    def test_get_known_ramulator_result_seq_rd(self):
        """Test known seq_rd results from summary.md"""
        framework = ComparisonFramework()
        result = framework._get_known_ramulator_result('seq_rd')

        assert result.trace_name == 'seq_rd'
        assert result.total_requests == 100000
        assert result.row_hits == 62481
        assert result.row_misses == 24992
        assert result.row_conflicts == 12495
        assert abs(result.avg_latency - 12.93) < 0.01

    def test_get_known_ramulator_result_stride_rd(self):
        """Test known stride_rd results from summary.md"""
        framework = ComparisonFramework()
        result = framework._get_known_ramulator_result('stride_rd')

        assert result.trace_name == 'stride_rd'
        assert result.total_requests == 100000
        assert result.row_hits == 0  # 0% hit rate for stride
        assert result.row_conflicts == 99935
        assert abs(result.avg_latency - 12.66) < 0.01

    def test_get_known_ramulator_result_random_rdwr(self):
        """Test known random_rdwr results from summary.md"""
        framework = ComparisonFramework()
        result = framework._get_known_ramulator_result('random_rdwr')

        assert result.trace_name == 'random_rdwr'
        assert result.total_requests == 100000
        assert result.row_hits == 17
        assert result.row_misses == 3550
        assert result.row_conflicts == 96383
        assert abs(result.avg_latency - 14.14) < 0.01

    def test_get_known_ramulator_result_unknown(self):
        """Test unknown trace returns zero values"""
        framework = ComparisonFramework()
        result = framework._get_known_ramulator_result('unknown_trace')

        assert result.trace_name == 'unknown_trace'
        assert result.total_requests == 0
        assert result.row_hits == 0
        assert result.avg_latency == 0.0
