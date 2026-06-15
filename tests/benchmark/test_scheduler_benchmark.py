"""
Tests for Scheduler Benchmark Module
"""

import pytest
from model.benchmark.scheduler_benchmark import (
    SchedulerBenchmark,
    SchedulerResult,
)
from model.benchmark.benchmark_config import SchedulerConfig, TestPattern


class TestSchedulerBenchmark:
    """Tests for SchedulerBenchmark"""
    
    def test_initialization(self):
        benchmark = SchedulerBenchmark()
        assert benchmark.speed_grade == "8Gbps"
        assert benchmark.config is not None
        assert benchmark.spec is not None
    
    def test_custom_config(self):
        config = SchedulerConfig(
            enable_qos=True,
            qos_levels=8,
            queue_depth=32
        )
        benchmark = SchedulerBenchmark(config=config)
        assert benchmark.config.enable_qos is True
        assert benchmark.config.qos_levels == 8
        assert benchmark.config.queue_depth == 32


class TestSchedulerResult:
    """Tests for SchedulerResult"""
    
    def test_default_result(self):
        result = SchedulerResult()
        assert result.qos_enabled is True
        assert result.row_hit_rate_percent == 0.0
        assert result.bank_conflict_rate_percent == 0.0
        assert result.total_requests == 0
    
    def test_result_to_dict(self):
        result = SchedulerResult()
        result.qos_enabled = True
        result.row_hit_rate_percent = 85.0
        result.bank_conflict_rate_percent = 10.0
        result.average_queue_depth = 25.5
        result.total_requests = 10000
        result.completed_requests = 9500
        
        d = result.to_dict()
        assert d['qos_enabled'] is True
        assert d['row_hit_rate_percent'] == 85.0
        assert d['bank_conflict_rate_percent'] == 10.0
        assert d['total_requests'] == 10000
    
    def test_result_str(self):
        result = SchedulerResult()
        result.qos_enabled = True
        result.priority_latency_ratio = 2.5
        result.row_hit_rate_percent = 85.0
        result.bank_conflict_rate_percent = 10.0
        result.average_queue_depth = 25.5
        result.max_queue_depth = 50
        result.requests_per_second = 1_000_000
        result.completed_requests = 10000
        result.total_requests = 10000
        
        s = str(result)
        assert "85" in s
        assert "2.5" in s
        assert "25" in s
        assert "50" in s


class TestQoSEffectiveness:
    """Tests for QoS effectiveness"""
    
    def test_priority_latency_ratio(self):
        """Test priority latency ratio calculation"""
        result = SchedulerResult()
        result.high_priority_avg_latency_ns = 40.0
        result.low_priority_avg_latency_ns = 100.0
        result.priority_latency_ratio = result.low_priority_avg_latency_ns / result.high_priority_avg_latency_ns
        
        assert result.priority_latency_ratio == 2.5
    
    def test_qos_distribution(self):
        """Test QoS distribution sum"""
        config = SchedulerConfig()
        total = sum(config.qos_distribution.values())
        assert total == pytest.approx(1.0, abs=0.01)


class TestRowHitRate:
    """Tests for row hit rate metrics"""
    
    def test_row_hit_rate_calculation(self):
        """Test row hit rate percentage calculation"""
        result = SchedulerResult()
        result.row_hit_count = 850
        result.row_miss_count = 150
        result.row_hit_rate_percent = (result.row_hit_count / 
                                       (result.row_hit_count + result.row_miss_count) * 100)
        
        assert result.row_hit_rate_percent == 85.0
    
    def test_optimal_row_hit_rate(self):
        """Test optimal row hit rate reference"""
        result = SchedulerResult()
        result.optimal_row_hit_rate_percent = 95.0  # Theoretical best
        
        assert result.optimal_row_hit_rate_percent == 95.0


class TestBankConflicts:
    """Tests for bank conflict metrics"""
    
    def test_bank_conflict_rate_calculation(self):
        """Test bank conflict rate calculation"""
        result = SchedulerResult()
        result.bank_conflict_count = 100
        result.bank_activation_count = 1000
        result.bank_conflict_rate_percent = (result.bank_conflict_count / 
                                             result.bank_activation_count * 100)
        
        assert result.bank_conflict_rate_percent == 10.0
    
    def test_average_bank_activations(self):
        """Test average bank activations per request"""
        result = SchedulerResult()
        result.bank_activation_count = 1000
        result.total_requests = 500
        result.average_bank_activations_per_request = (result.bank_activation_count / 
                                                        result.total_requests)
        
        assert result.average_bank_activations_per_request == 2.0


class TestQueueMetrics:
    """Tests for queue depth metrics"""
    
    def test_queue_depth_tracking(self):
        """Test queue depth tracking"""
        result = SchedulerResult()
        result.max_queue_depth = 64
        result.queue_full_count = 5
        result.rejected_requests = 10
        
        assert result.max_queue_depth == 64
        assert result.queue_full_count == 5
        assert result.rejected_requests == 10
    
    def test_queue_full_rate(self):
        """Test queue full rate calculation"""
        result = SchedulerResult()
        result.queue_full_count = 5
        result.total_requests = 1000
        queue_full_rate = result.queue_full_count / result.total_requests * 100
        
        assert queue_full_rate == 0.5


class TestThroughput:
    """Tests for throughput metrics"""
    
    def test_requests_per_second_calculation(self):
        """Test requests per second calculation"""
        result = SchedulerResult()
        result.completed_requests = 1_000_000
        result.test_duration_ns = 1_000_000_000  # 1 second
        
        result.requests_per_second = result.completed_requests / (result.test_duration_ns / 1e9)
        
        assert result.requests_per_second == 1_000_000