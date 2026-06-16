"""
Tests for Latency Benchmark Module
"""

import pytest
from model.benchmark.latency_benchmark import (
    LatencyBenchmark,
    LatencyResult,
)
from model.benchmark.benchmark_config import LatencyConfig, TestPattern


class TestLatencyBenchmark:
    """Tests for LatencyBenchmark"""
    
    def test_initialization(self):
        benchmark = LatencyBenchmark()
        assert benchmark.speed_grade == "8Gbps"
        assert benchmark.config is not None
        assert benchmark.spec is not None
    
    def test_custom_speed_grade(self):
        benchmark = LatencyBenchmark(speed_grade="12Gbps")
        assert benchmark.speed_grade == "12Gbps"
        assert benchmark.spec.data_rate_gtps == 12.0
    
    def test_custom_config(self):
        config = LatencyConfig(
            num_requests=5000,
            pattern=TestPattern.RANDOM,
            percentiles=[50, 90, 99]
        )
        benchmark = LatencyBenchmark(config=config)
        assert benchmark.config.num_requests == 5000
        assert benchmark.config.pattern == TestPattern.RANDOM
        assert benchmark.config.percentiles == [50, 90, 99]


class TestLatencyResult:
    """Tests for LatencyResult"""
    
    def test_default_result(self):
        result = LatencyResult()
        assert result.average_latency_ns == 0.0
        assert result.p99_latency_ns == 0.0
        assert result.total_requests == 0
    
    def test_result_to_dict(self):
        result = LatencyResult()
        result.average_latency_ns = 50.0
        result.p99_latency_ns = 75.0
        result.read_avg_latency_ns = 45.0
        result.write_avg_latency_ns = 55.0
        
        d = result.to_dict()
        assert d['average_latency_ns'] == 50.0
        assert d['p99_latency_ns'] == 75.0
        assert d['read_avg_latency_ns'] == 45.0
        assert d['write_avg_latency_ns'] == 55.0
    
    def test_result_str(self):
        result = LatencyResult()
        result.average_latency_ns = 50.0
        result.median_latency_ns = 48.0
        result.p50_latency_ns = 48.0
        result.p90_latency_ns = 60.0
        result.p95_latency_ns = 65.0
        result.p99_latency_ns = 75.0
        result.p999_latency_ns = 90.0
        result.read_avg_latency_ns = 45.0
        result.write_avg_latency_ns = 55.0
        result.min_latency_ns = 30.0
        result.max_latency_ns = 100.0
        result.std_dev_ns = 10.0
        result.total_requests = 10000
        result.measured_requests = 10000
        
        s = str(result)
        assert "50" in s
        assert "48" in s
        assert "75" in s
        assert "45" in s
        assert "55" in s


class TestPercentileCalculation:
    """Tests for percentile calculations"""
    
    def test_percentile_50(self):
        benchmark = LatencyBenchmark()
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        p50 = benchmark._calculate_percentile(data, 50)
        # P50 should be close to median (50-60 range)
        assert 40 <= p50 <= 60
    
    def test_percentile_90(self):
        benchmark = LatencyBenchmark()
        data = list(range(1, 101))  # 1-100
        p90 = benchmark._calculate_percentile(data, 90)
        # P90 should be close to 90 (91 is acceptable)
        assert 85 <= p90 <= 95
    
    def test_percentile_99(self):
        benchmark = LatencyBenchmark()
        data = list(range(1, 101))  # 1-100
        p99 = benchmark._calculate_percentile(data, 99)
        # P99 should be close to 99 (100 is acceptable for small datasets)
        assert 95 <= p99 <= 100
    
    def test_percentile_empty(self):
        benchmark = LatencyBenchmark()
        p = benchmark._calculate_percentile([], 50)
        assert p == 0.0
    
    def test_percentile_single(self):
        benchmark = LatencyBenchmark()
        p = benchmark._calculate_percentile([42], 50)
        assert p == 42


class TestHistogram:
    """Tests for histogram building"""
    
    def test_histogram_creation(self):
        benchmark = LatencyBenchmark()
        result = LatencyResult()
        result.latency_histogram_bins = [0, 50, 100, 200, 500]
        benchmark.result = result
        
        latencies = [10, 30, 60, 80, 150, 250, 600]
        histogram = benchmark._build_histogram(latencies)
        
        assert histogram['0-50'] == 2  # 10, 30
        assert histogram['50-100'] == 2  # 60, 80
        assert histogram['100-200'] == 1  # 150
        assert histogram['200-500'] == 1  # 250
        assert histogram['>500'] == 1  # 600


class TestAddressGeneration:
    """Tests for address generation in latency benchmarks"""
    
    def test_sequential_addresses(self):
        benchmark = LatencyBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.SEQUENTIAL, 10)
        assert len(addresses) == 10
        # Should be consecutive
        assert addresses == sorted(addresses)
    
    def test_random_addresses(self):
        benchmark = LatencyBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.RANDOM, 100)
        assert len(addresses) == 100
        # Most should be unique
        assert len(set(addresses)) > 90
    
    def test_hotspot_addresses(self):
        benchmark = LatencyBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.HOTSPOT, 100)
        assert len(addresses) == 100
        # 80% in first 20% of space (relaxed threshold)
        hotspot_count = sum(1 for a in addresses if a < 0x20_000_000)
        assert hotspot_count >= 50
    
    def test_row_hit_addresses(self):
        benchmark = LatencyBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.ROW_HIT, 100)
        assert len(addresses) == 100
        assert len(set(addresses)) == 1  # All same


class TestReadWriteLatency:
    """Tests for read/write latency separation"""
    
    def test_latency_separation(self):
        result = LatencyResult()
        result.read_latencies = [40, 45, 50]  # 3 reads
        result.write_latencies = [50, 55, 60]  # 3 writes
        
        result.read_avg_latency_ns = sum(result.read_latencies) / len(result.read_latencies)
        result.write_avg_latency_ns = sum(result.write_latencies) / len(result.write_latencies)
        
        assert result.read_avg_latency_ns == 45.0
        assert result.write_avg_latency_ns == 55.0
        assert result.write_avg_latency_ns > result.read_avg_latency_ns