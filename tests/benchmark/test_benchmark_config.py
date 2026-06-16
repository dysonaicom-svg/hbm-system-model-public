"""
Tests for Benchmark Configuration Module
"""

import pytest
from model.benchmark.benchmark_config import (
    BenchmarkConfig,
    BandwidthConfig,
    LatencyConfig,
    SchedulerConfig,
    ComparisonConfig,
    TestPattern,
    SpeedGrade,
)


class TestBandwidthConfig:
    """Tests for BandwidthConfig"""
    
    def test_default_config(self):
        config = BandwidthConfig()
        assert config.test_duration_ns == 100_000_000
        assert config.request_batch_size == 1000
        assert config.num_batches == 100
        assert config.pattern == TestPattern.SEQUENTIAL
    
    def test_custom_config(self):
        config = BandwidthConfig(
            test_duration_ns=50_000_000,
            pattern=TestPattern.RANDOM,
            read_write_ratio=0.5
        )
        assert config.test_duration_ns == 50_000_000
        assert config.pattern == TestPattern.RANDOM
        assert config.read_write_ratio == 0.5
    
    def test_repr(self):
        config = BandwidthConfig()
        repr_str = repr(config)
        assert "BandwidthConfig" in repr_str
        assert "duration" in repr_str


class TestLatencyConfig:
    """Tests for LatencyConfig"""
    
    def test_default_config(self):
        config = LatencyConfig()
        assert config.num_requests == 10_000
        assert config.warmup_requests == 1000
        assert 50 in config.percentiles
        assert 99 in config.percentiles
    
    def test_percentiles(self):
        config = LatencyConfig(percentiles=[50, 90, 99])
        assert config.percentiles == [50, 90, 99]
    
    def test_repr(self):
        config = LatencyConfig()
        repr_str = repr(config)
        assert "LatencyConfig" in repr_str


class TestSchedulerConfig:
    """Tests for SchedulerConfig"""
    
    def test_default_config(self):
        config = SchedulerConfig()
        assert config.enable_qos is True
        assert config.qos_levels == 16
        assert config.queue_depth == 64
    
    def test_qos_distribution(self):
        config = SchedulerConfig()
        assert 0 in config.qos_distribution
        assert 15 in config.qos_distribution
        assert sum(config.qos_distribution.values()) == pytest.approx(1.0)
    
    def test_repr(self):
        config = SchedulerConfig()
        repr_str = repr(config)
        assert "SchedulerConfig" in repr_str


class TestComparisonConfig:
    """Tests for ComparisonConfig"""
    
    def test_default_config(self):
        config = ComparisonConfig()
        assert len(config.configs_to_compare) >= 2
        assert config.compare_bandwidth is True
        assert config.compare_latency is True
    
    def test_speed_grades(self):
        assert SpeedGrade.HBM3_6_4.version == "hbm3"
        assert SpeedGrade.HBM4_8.version == "hbm4"
        assert SpeedGrade.HBM4_8.data_rate == 8.0
        assert SpeedGrade.HBM4_12.data_rate == 12.0


class TestBenchmarkConfig:
    """Tests for BenchmarkConfig"""
    
    def test_default_config(self):
        config = BenchmarkConfig()
        assert config.run_bandwidth is True
        assert config.run_latency is True
        assert config.run_scheduler is True
        assert config.run_comparison is True
    
    def test_quick_config(self):
        config = BenchmarkConfig.quick()
        assert config.bandwidth.test_duration_ns == 1_000_000
        assert config.latency.num_requests == 1000
    
    def test_comprehensive_config(self):
        config = BenchmarkConfig.comprehensive()
        assert config.bandwidth.test_duration_ns == 100_000_000
        assert config.latency.num_requests == 100_000
        assert len(config.comparison.configs_to_compare) == 4


class TestTestPattern:
    """Tests for TestPattern enum"""
    
    def test_all_patterns(self):
        patterns = list(TestPattern)
        assert TestPattern.SEQUENTIAL in patterns
        assert TestPattern.RANDOM in patterns
        assert TestPattern.STRIDED in patterns
        assert TestPattern.HOTSPOT in patterns
        assert TestPattern.BANK_CONFLICT in patterns
        assert TestPattern.ROW_HIT in patterns
    
    def test_pattern_values(self):
        assert TestPattern.SEQUENTIAL.value == "sequential"
        assert TestPattern.RANDOM.value == "random"