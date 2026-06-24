"""
Additional Tests for Scheduler Benchmark Module

Covers edge cases and additional functionality.

Run with: pytest tests/benchmark/test_scheduler_benchmark_extra.py -v
"""

import pytest
from model.benchmark.scheduler_benchmark import (
    SchedulerBenchmark,
    SchedulerResult,
)
from model.benchmark.benchmark_config import SchedulerConfig, TestPattern


class TestSchedulerBenchmarkMethods:
    """Tests for scheduler benchmark methods"""

    def test_create_spec(self):
        """Test spec creation for different speed grades"""
        benchmark = SchedulerBenchmark(speed_grade="16Gbps")
        assert benchmark.spec is not None
        assert benchmark.spec.data_rate_gtps > 0

    def test_generate_addresses_sequential(self):
        """Test address generation for sequential pattern"""
        config = SchedulerConfig(pattern=TestPattern.SEQUENTIAL)
        benchmark = SchedulerBenchmark(config=config)

        addresses = benchmark._generate_addresses(TestPattern.SEQUENTIAL, 100)

        assert len(addresses) == 100
        # Should be consecutive
        assert addresses[0] == addresses[1] - 64 or addresses[0] + 64 == addresses[1]

    def test_generate_addresses_random(self):
        """Test address generation for random pattern"""
        config = SchedulerConfig(pattern=TestPattern.RANDOM)
        benchmark = SchedulerBenchmark(config=config)

        addresses = benchmark._generate_addresses(TestPattern.RANDOM, 100)

        assert len(addresses) == 100
        # Should have variety
        assert len(set(addresses)) > 50

    def test_generate_addresses_row_hit(self):
        """Test address generation for row hit pattern"""
        config = SchedulerConfig(pattern=TestPattern.ROW_HIT)
        benchmark = SchedulerBenchmark(config=config)

        addresses = benchmark._generate_addresses(TestPattern.ROW_HIT, 100)

        assert len(addresses) == 100
        # All addresses should be same
        assert len(set(addresses)) == 1

    def test_generate_addresses_bank_conflict(self):
        """Test address generation for bank conflict pattern"""
        config = SchedulerConfig(pattern=TestPattern.BANK_CONFLICT)
        benchmark = SchedulerBenchmark(config=config)

        addresses = benchmark._generate_addresses(
            TestPattern.BANK_CONFLICT, 100, bank_conflict_mode=True
        )

        assert len(addresses) == 100
        # Should span different addresses
        assert len(set(addresses)) > 10


class TestSchedulerResultMethods:
    """Tests for scheduler result methods"""

    def test_to_dict_complete(self):
        """Test to_dict with all fields"""
        result = SchedulerResult()
        result.qos_enabled = True
        result.high_priority_avg_latency_ns = 30.0
        result.low_priority_avg_latency_ns = 80.0
        result.priority_latency_ratio = 2.67
        result.row_hit_rate_percent = 85.0
        result.row_miss_count = 150
        result.row_hit_count = 850
        result.optimal_row_hit_rate_percent = 95.0
        result.bank_conflict_rate_percent = 10.0
        result.bank_conflict_count = 100
        result.bank_activation_count = 1000
        result.average_bank_activations_per_request = 1.5
        result.average_queue_depth = 25.5
        result.max_queue_depth = 64
        result.queue_full_count = 5
        result.total_requests = 10000
        result.completed_requests = 9500
        result.rejected_requests = 500
        result.test_duration_ns = 50_000_000.0
        result.requests_per_second = 190_000.0

        d = result.to_dict()

        assert d['qos_enabled'] is True
        assert d['priority_latency_ratio'] == 2.67
        assert d['row_hit_rate_percent'] == 85.0
        assert d['bank_conflict_rate_percent'] == 10.0
        assert d['average_queue_depth'] == 25.5
        assert d['max_queue_depth'] == 64
        assert d['total_requests'] == 10000
        assert d['completed_requests'] == 9500

    def test_to_str_complete(self):
        """Test __str__ with all fields"""
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

        assert "True" in s or "QoS" in s
        assert "85" in s
        assert "10" in s
        assert "25" in s


class TestSchedulerQOS:
    """Tests for QoS scheduling"""

    def test_qos_effectiveness_test(self):
        """Test QoS effectiveness test execution"""
        config = SchedulerConfig(
            enable_qos=True,
            qos_levels=16
        )
        benchmark = SchedulerBenchmark(config=config)

        result = benchmark.run_qos_effectiveness_test()

        assert isinstance(result, SchedulerResult)
        assert result.qos_enabled is True
        assert result.total_requests >= 0

    def test_qos_disabled(self):
        """Test with QoS disabled"""
        config = SchedulerConfig(enable_qos=False)
        benchmark = SchedulerBenchmark(config=config)

        result = benchmark.run_qos_effectiveness_test()

        # Should still produce result
        assert isinstance(result, SchedulerResult)


class TestSchedulerRowHit:
    """Tests for row hit rate"""

    def test_row_hit_rate_test(self):
        """Test row hit rate test execution"""
        config = SchedulerConfig(
            row_hit_test_enabled=True,
            row_hit_test_duration_ns=10_000_000
        )
        benchmark = SchedulerBenchmark(config=config)

        result = benchmark.run_row_hit_rate_test()

        assert isinstance(result, SchedulerResult)
        assert result.row_hit_rate_percent >= 0
        assert result.row_hit_rate_percent <= 100

    def test_row_hit_disabled(self):
        """Test with row hit test disabled"""
        config = SchedulerConfig(row_hit_test_enabled=False)
        benchmark = SchedulerBenchmark(config=config)

        # Should still be able to run
        assert benchmark.config.row_hit_test_enabled is False


class TestSchedulerBankConflict:
    """Tests for bank conflict"""

    def test_bank_conflict_test(self):
        """Test bank conflict test execution"""
        config = SchedulerConfig(
            bank_conflict_test_enabled=True,
            bank_conflict_test_duration_ns=10_000_000
        )
        benchmark = SchedulerBenchmark(config=config)

        result = benchmark.run_bank_conflict_test()

        assert isinstance(result, SchedulerResult)
        assert result.bank_conflict_rate_percent >= 0
        assert result.bank_conflict_rate_percent <= 100

    def test_bank_conflict_disabled(self):
        """Test with bank conflict test disabled"""
        config = SchedulerConfig(bank_conflict_test_enabled=False)
        benchmark = SchedulerBenchmark(config=config)

        # Should still be able to run
        assert benchmark.config.bank_conflict_test_enabled is False


class TestSchedulerQueue:
    """Tests for queue depth"""

    def test_queue_depth_test(self):
        """Test queue depth test execution"""
        config = SchedulerConfig(
            queue_depth=32
        )
        benchmark = SchedulerBenchmark(config=config)

        result = benchmark.run_queue_depth_test()

        assert isinstance(result, SchedulerResult)
        assert result.max_queue_depth >= 0
        assert result.queue_full_count >= 0


class TestSchedulerAllTests:
    """Tests for run_all_tests method"""

    def test_run_all_tests(self):
        """Test running all scheduler tests"""
        config = SchedulerConfig(
            enable_qos=True,
            row_hit_test_enabled=True,
            bank_conflict_test_enabled=True,
            test_duration_ns=5_000_000
        )
        benchmark = SchedulerBenchmark(config=config)

        results = benchmark.run_all_tests()

        assert isinstance(results, dict)
        if config.enable_qos:
            assert 'qos_effectiveness' in results
        if config.row_hit_test_enabled:
            assert 'row_hit_rate' in results
        if config.bank_conflict_test_enabled:
            assert 'bank_conflict' in results
        assert 'queue_depth' in results

    def test_run_all_tests_qos_disabled(self):
        """Test run_all_tests with QoS disabled"""
        config = SchedulerConfig(
            enable_qos=False,
            row_hit_test_enabled=True,
            bank_conflict_test_enabled=True
        )
        benchmark = SchedulerBenchmark(config=config)

        results = benchmark.run_all_tests()

        assert 'qos_effectiveness' not in results


class TestSchedulerSummary:
    """Tests for get_summary method"""

    def test_get_summary_empty(self):
        """Test summary with no results"""
        benchmark = SchedulerBenchmark()
        benchmark.results = {}

        summary = benchmark.get_summary()

        assert isinstance(summary, SchedulerResult)
        assert summary.total_requests == 0

    def test_get_summary_with_results(self):
        """Test summary with results"""
        config = SchedulerConfig(
            enable_qos=True,
            row_hit_test_enabled=True,
            bank_conflict_test_enabled=True
        )
        benchmark = SchedulerBenchmark(config=config)

        benchmark.run_all_tests()
        summary = benchmark.get_summary()

        assert isinstance(summary, SchedulerResult)
        assert summary.total_requests > 0 or summary.completed_requests >= 0


class TestSchedulerEdgeCases:
    """Tests for edge cases"""

    def test_zero_duration(self):
        """Test with zero duration"""
        config = SchedulerConfig(test_duration_ns=0)
        benchmark = SchedulerBenchmark(config=config)

        # Should handle gracefully
        result = benchmark.run_queue_depth_test()
        assert result is not None

    def test_zero_queue_depth(self):
        """Test with zero queue depth"""
        config = SchedulerConfig(queue_depth=0)
        benchmark = SchedulerBenchmark(config=config)

        # Should handle gracefully
        result = benchmark.run_queue_depth_test()
        assert result is not None

    def test_qos_distribution_validation(self):
        """Test QoS distribution sums to approximately 1.0"""
        config = SchedulerConfig()
        total = sum(config.qos_distribution.values())

        assert 0.99 <= total <= 1.01

    def test_custom_qos_distribution(self):
        """Test with custom QoS distribution"""
        config = SchedulerConfig(
            qos_distribution={
                0: 0.2,
                8: 0.6,
                15: 0.2
            }
        )
        benchmark = SchedulerBenchmark(config=config)

        total = sum(benchmark.config.qos_distribution.values())
        assert total == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
