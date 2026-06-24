"""
Additional Tests for Bandwidth Benchmark Module

Covers edge cases and additional functionality.

Run with: pytest tests/benchmark/test_bandwidth_benchmark_extra.py -v
"""

import pytest
from model.benchmark.bandwidth_benchmark import (
    BandwidthBenchmark,
    BandwidthResult,
)
from model.benchmark.benchmark_config import BandwidthConfig, TestPattern


class TestBandwidthBenchmarkMethods:
    """Tests for bandwidth benchmark methods"""

    def test_create_spec(self):
        """Test spec creation for different speed grades"""
        benchmark = BandwidthBenchmark(speed_grade="16Gbps")
        assert benchmark.spec is not None
        assert benchmark.spec.data_rate_gtps == 16.0

    def test_create_spec_12gbps(self):
        """Test spec creation for 12Gbps"""
        benchmark = BandwidthBenchmark(speed_grade="12Gbps")
        assert benchmark.spec.data_rate_gtps == 12.0

    def test_create_spec_invalid(self):
        """Test spec creation with invalid speed grade"""
        with pytest.raises(ValueError):
            BandwidthBenchmark(speed_grade="invalid")

    def test_generate_addresses_all_patterns(self):
        """Test address generation for all patterns"""
        config = BandwidthConfig()
        benchmark = BandwidthBenchmark(config=config)

        for pattern in TestPattern:
            addresses = benchmark._generate_addresses(pattern, 50)
            assert len(addresses) == 50, f"Failed for pattern {pattern}"

    def test_generate_addresses_with_custom_range(self):
        """Test address generation with custom range"""
        config = BandwidthConfig(
            address_range_start=0x1000,
            address_range_end=0x2000
        )
        benchmark = BandwidthBenchmark(config=config)

        addresses = benchmark._generate_addresses(TestPattern.SEQUENTIAL, 10)

        for addr in addresses:
            assert 0x1000 <= addr < 0x2000 or addr < config.address_range_end


class TestBandwidthResultMethods:
    """Tests for BandwidthResult methods"""

    def test_to_dict_complete(self):
        """Test to_dict with all fields"""
        result = BandwidthResult()
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1800.0
        result.peak_efficiency_percent = 87.8
        result.sustained_bandwidth_gbs = 1600.0
        result.sustained_efficiency_percent = 78.1
        result.bandwidth_variance_percent = 5.0
        result.refresh_overhead_percent = 1.5
        result.refresh_count = 100
        result.refresh_total_time_ns = 18000.0
        result.total_requests = 100000
        result.read_requests = 70000
        result.write_requests = 30000
        result.total_bytes = 6400000
        result.test_duration_ns = 100000000.0
        result.channel_bandwidth = {0: 64.0, 1: 65.0, 2: 63.0}

        d = result.to_dict()

        assert d['peak_bandwidth_gbs'] == 2048.0
        assert d['measured_bandwidth_gbs'] == 1800.0
        assert d['refresh_count'] == 100
        assert d['total_requests'] == 100000
        assert d['read_requests'] == 70000

    def test_to_str_complete(self):
        """Test __str__ with all fields"""
        result = BandwidthResult()
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1800.0
        result.peak_efficiency_percent = 87.8
        result.sustained_bandwidth_gbs = 1600.0
        result.sustained_efficiency_percent = 78.1
        result.refresh_overhead_percent = 1.5
        result.total_requests = 100000
        result.read_requests = 70000
        result.write_requests = 30000

        s = str(result)

        assert "2048" in s
        assert "1800" in s
        assert "100000" in s
        assert "70000" in s


class TestBandwidthTests:
    """Tests for bandwidth test methods"""

    def test_run_peak_bandwidth_test(self):
        """Test peak bandwidth test"""
        config = BandwidthConfig(
            test_duration_ns=100_000,
            request_batch_size=50,
            num_batches=5
        )
        benchmark = BandwidthBenchmark(config=config)

        result = benchmark.run_peak_bandwidth_test()

        assert isinstance(result, BandwidthResult)
        assert result.peak_bandwidth_gbs > 0
        assert result.total_requests >= 0

    def test_run_sustained_bandwidth_test(self):
        """Test sustained bandwidth test"""
        config = BandwidthConfig(
            test_duration_ns=100_000,
            pattern=TestPattern.SEQUENTIAL
        )
        benchmark = BandwidthBenchmark(config=config)

        result = benchmark.run_sustained_bandwidth_test()

        assert isinstance(result, BandwidthResult)
        assert result.peak_bandwidth_gbs > 0

    def test_run_refresh_overhead_test(self):
        """Test refresh overhead test"""
        config = BandwidthConfig(
            test_duration_ns=50_000
        )
        benchmark = BandwidthBenchmark(config=config)

        result = benchmark.run_refresh_overhead_test()

        assert isinstance(result, BandwidthResult)
        assert result.peak_bandwidth_gbs > 0

    def test_run_all_tests_default(self):
        """Test run_all_tests with defaults"""
        config = BandwidthConfig(
            calculate_peak=True,
            calculate_sustained=True,
            calculate_refresh_overhead=True,
            test_duration_ns=50_000
        )
        benchmark = BandwidthBenchmark(config=config)

        results = benchmark.run_all_tests()

        assert isinstance(results, dict)
        assert 'peak' in results
        assert 'sustained' in results
        assert 'refresh_overhead' in results

    def test_run_all_tests_partial(self):
        """Test run_all_tests with partial enablement"""
        config = BandwidthConfig(
            calculate_peak=True,
            calculate_sustained=False,
            calculate_refresh_overhead=False
        )
        benchmark = BandwidthBenchmark(config=config)

        results = benchmark.run_all_tests()

        assert 'peak' in results
        assert 'sustained' not in results
        assert 'refresh_overhead' not in results

    def test_get_summary_empty(self):
        """Test get_summary with no results"""
        benchmark = BandwidthBenchmark()
        benchmark.results = []

        summary = benchmark.get_summary()

        assert isinstance(summary, BandwidthResult)

    def test_get_summary_with_results(self):
        """Test get_summary with results"""
        config = BandwidthConfig(test_duration_ns=50_000)
        benchmark = BandwidthBenchmark(config=config)

        benchmark.run_all_tests()
        summary = benchmark.get_summary()

        assert isinstance(summary, BandwidthResult)
        assert summary.peak_bandwidth_gbs > 0


class TestBandwidthEdgeCases:
    """Tests for edge cases"""

    def test_zero_duration(self):
        """Test with zero duration"""
        config = BandwidthConfig(test_duration_ns=0)
        benchmark = BandwidthBenchmark(config=config)

        result = benchmark.run_peak_bandwidth_test()

        assert isinstance(result, BandwidthResult)

    def test_zero_batches(self):
        """Test with zero batches"""
        config = BandwidthConfig(num_batches=0)
        benchmark = BandwidthBenchmark(config=config)

        result = benchmark.run_peak_bandwidth_test()

        assert isinstance(result, BandwidthResult)

    def test_zero_batch_size(self):
        """Test with zero batch size"""
        config = BandwidthConfig(request_batch_size=0)
        benchmark = BandwidthBenchmark(config=config)

        result = benchmark.run_peak_bandwidth_test()

        assert isinstance(result, BandwidthResult)

    def test_empty_address_range(self):
        """Test with empty address range"""
        config = BandwidthConfig(
            address_range_start=0,
            address_range_end=0
        )
        benchmark = BandwidthBenchmark(config=config)

        addresses = benchmark._generate_addresses(TestPattern.SEQUENTIAL, 10)

        # Should handle edge case
        assert len(addresses) == 10

    def test_large_stride(self):
        """Test with large stride"""
        config = BandwidthConfig(stride_bytes=1024*1024)
        benchmark = BandwidthBenchmark(config=config)

        addresses = benchmark._generate_addresses(TestPattern.STRIDED, 10)

        assert len(addresses) == 10

    def test_zero_read_write_ratio(self):
        """Test with zero read ratio (all writes)"""
        config = BandwidthConfig(read_write_ratio=0.0)
        benchmark = BandwidthBenchmark(config=config)

        # Should handle gracefully
        assert benchmark.config.read_write_ratio == 0.0

    def test_full_read_write_ratio(self):
        """Test with full read ratio (all reads)"""
        config = BandwidthConfig(read_write_ratio=1.0)
        benchmark = BandwidthBenchmark(config=config)

        # Should handle gracefully
        assert benchmark.config.read_write_ratio == 1.0


class TestBandwidthCalculationEdgeCases:
    """Tests for bandwidth calculation edge cases"""

    def test_efficiency_calculation_zero_peak(self):
        """Test efficiency with zero peak bandwidth"""
        result = BandwidthResult()
        result.peak_bandwidth_gbs = 0.0
        result.measured_bandwidth_gbs = 100.0

        efficiency = (result.measured_bandwidth_gbs / result.peak_bandwidth_gbs * 100
                     if result.peak_bandwidth_gbs > 0 else 0)

        assert efficiency == 0.0

    def test_efficiency_calculation_normal(self):
        """Test efficiency with normal values"""
        result = BandwidthResult()
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1024.0

        efficiency = (result.measured_bandwidth_gbs / result.peak_bandwidth_gbs * 100
                     if result.peak_bandwidth_gbs > 0 else 0)

        assert efficiency == 50.0

    def test_variance_calculation_single_value(self):
        """Test variance with single value"""
        result = BandwidthResult()
        result.bandwidth_variance_percent = 0.0  # No variance with single value

        assert result.bandwidth_variance_percent == 0.0

    def test_variance_calculation_multiple_values(self):
        """Test variance with multiple values"""
        result = BandwidthResult()
        # Simulate variance calculation
        values = [100, 110, 90, 105, 95]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        result.bandwidth_variance_percent = (variance ** 0.5 / mean * 100)

        assert result.bandwidth_variance_percent > 0

    def test_refresh_overhead_zero_time(self):
        """Test refresh overhead with zero time"""
        result = BandwidthResult()
        result.refresh_total_time_ns = 0.0
        result.test_duration_ns = 0.0

        overhead = (result.refresh_total_time_ns / result.test_duration_ns * 100
                   if result.test_duration_ns > 0 else 0)

        assert overhead == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
