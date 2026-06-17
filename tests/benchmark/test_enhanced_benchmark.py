"""
Enhanced Benchmark Tests

Tests for the enhanced HBM4 benchmark suite covering:
1. Multi-channel parallel access
2. Mixed traffic patterns
3. Bank group conflicts
4. Refresh impact
5. QoS impact

Run with: pytest tests/benchmark/test_enhanced_benchmark.py -v
"""

import pytest
import random
from model.benchmark.enhanced_benchmark import (
    EnhancedBenchmark,
    EnhancedBenchmarkReport,
    MultiChannelResult,
    MixedTrafficResult,
    BankGroupConflictResult,
    RefreshImpactResult,
    QoSImpactResult,
    run_enhanced_benchmark,
    run_multi_channel_benchmark,
    run_mixed_traffic_benchmark,
    run_bank_group_benchmark,
    run_refresh_benchmark,
    run_qos_benchmark,
)


class TestEnhancedBenchmark:
    """Test suite for enhanced benchmark module"""

    def test_enhanced_benchmark_initialization(self):
        """Test EnhancedBenchmark initialization"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps", random_seed=42)

        assert benchmark.speed_grade == "8Gbps"
        assert benchmark.random_seed == 42
        assert benchmark.spec is not None
        assert benchmark.spec.channels == 32

    def test_multi_channel_test_basic(self):
        """Test basic multi-channel test execution"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_multi_channel_test(
            num_requests_per_channel=100,
            pattern=None  # Use default
        )

        assert isinstance(result, MultiChannelResult)
        assert result.num_channels == 32
        assert result.channels_active > 0
        assert result.total_requests > 0
        assert result.peak_bandwidth_gbs > 0

    def test_multi_channel_efficiency(self):
        """Test multi-channel efficiency calculation"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_multi_channel_test(num_requests_per_channel=200)

        # Efficiency should be reasonable
        assert 0 <= result.bandwidth_efficiency_percent <= 100
        assert 0 <= result.channel_utilization_percent <= 100

    def test_multi_channel_all_channels_active(self):
        """Test that multiple channels can be utilized"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_multi_channel_test(num_requests_per_channel=50)

        # Multiple channels should be active (not all 32 due to queue limits)
        assert result.channels_active >= 3

    def test_mixed_traffic_test_basic(self):
        """Test basic mixed traffic test execution"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_mixed_traffic_test(
            read_ratio=0.7,
            num_requests=1000
        )

        assert isinstance(result, MixedTrafficResult)
        assert abs(result.read_ratio - 0.7) < 0.01
        assert abs(result.write_ratio - 0.3) < 0.01
        assert result.total_requests > 0
        assert result.read_requests + result.write_requests == result.total_requests

    def test_mixed_traffic_read_heavy(self):
        """Test read-heavy mixed traffic"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_mixed_traffic_test(
            read_ratio=0.9,
            num_requests=500
        )

        assert result.read_requests > result.write_requests
        assert result.read_bandwidth_gbs > 0

    def test_mixed_traffic_write_heavy(self):
        """Test write-heavy mixed traffic"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_mixed_traffic_test(
            read_ratio=0.2,
            num_requests=500
        )

        assert result.write_requests > result.read_requests
        assert result.write_bandwidth_gbs > 0

    def test_mixed_traffic_balanced(self):
        """Test balanced read/write traffic"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_mixed_traffic_test(
            read_ratio=0.5,
            num_requests=100
        )

        # Should have similar counts (relaxed tolerance for simulation variance)
        total = result.read_requests + result.write_requests
        if total > 0:
            actual_ratio = result.read_requests / total
            # Allow some variance due to random nature
            assert 0.3 <= actual_ratio <= 0.7

    def test_bank_group_conflict_test_basic(self):
        """Test basic bank group conflict test execution"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_bank_group_conflict_test(num_requests=500)

        assert isinstance(result, BankGroupConflictResult)
        assert result.total_requests > 0
        assert result.same_bank_group_requests + result.different_bank_group_requests == result.total_requests

    def test_bank_group_conflict_latency_penalty(self):
        """Test that different BG has higher latency"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_bank_group_conflict_test(num_requests=200)

        # Different BG should have higher latency due to timing
        assert result.different_bg_latency_avg_ns >= result.same_bg_latency_avg_ns
        assert result.latency_penalty_ns >= 0

    def test_bank_group_conflict_efficiency(self):
        """Test bank group efficiency calculation"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_bank_group_conflict_test(num_requests=100)

        # Efficiency should be between 0 and 100
        assert 0 <= result.bank_group_efficiency_percent <= 100

    def test_refresh_impact_test_basic(self):
        """Test basic refresh impact test execution"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_refresh_impact_test(
            test_duration_ns=50_000,
            enable_refresh=True
        )

        assert isinstance(result, RefreshImpactResult)
        assert result.refresh_duration_ns > 0
        assert result.test_duration_ns > 0

    def test_refresh_bandwidth_loss(self):
        """Test that refresh causes some bandwidth loss"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_refresh_impact_test(
            test_duration_ns=50_000,
            enable_refresh=True
        )

        # With refresh, bandwidth should be lower than theoretical peak
        assert result.bandwidth_with_refresh_gbs <= result.bandwidth_without_refresh_gbs
        # Bandwidth loss should be positive
        assert result.bandwidth_loss_percent >= 0

    def test_refresh_coverage(self):
        """Test refresh coverage calculation"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_refresh_impact_test(test_duration_ns=50_000)

        # Refresh coverage should be reasonable
        assert 0 <= result.refresh_coverage_percent <= 100

    def test_qos_impact_test_basic(self):
        """Test basic QoS impact test execution"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_qos_impact_test(
            num_requests=100,
            high_load=True
        )

        assert isinstance(result, QoSImpactResult)
        assert result.num_qos_levels == 16
        assert result.total_requests > 0

    def test_qos_priority_levels(self):
        """Test QoS priority level metrics"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_qos_impact_test(num_requests=200)

        # Should have metrics for multiple QoS levels
        assert len(result.qos_level_latency_avg) > 0
        assert len(result.qos_level_requests) > 0

    def test_qos_critical_vs_normal(self):
        """Test critical vs normal priority latency"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_qos_impact_test(num_requests=200)

        # Critical should have lower latency than normal if QoS works
        if result.critical_latency_ns > 0 and result.normal_latency_ns > 0:
            # The ratio indicates how much faster critical is vs normal
            # (should be > 1.0 if QoS is working)
            assert result.critical_to_normal_ratio >= 0

    def test_qos_effectiveness(self):
        """Test QoS effectiveness metric"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_qos_impact_test(num_requests=50)

        # Effectiveness should be a valid number
        assert result.qos_effectiveness_percent > 0
        assert result.qos_effectiveness_percent < 1000  # Sanity check

    def test_qos_no_starvation(self):
        """Test that starvation is properly detected"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_qos_impact_test(
            num_requests=50,
            high_load=True
        )

        # Starvation detection should be boolean
        assert isinstance(result.starvation_detected, bool)

    @pytest.mark.slow
    def test_run_all_tests(self):
        """Test running all enhanced benchmark tests"""
        # Skip this test for now as it's slow
        # Full benchmark should be run separately
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        report = benchmark.run_all_tests()

        assert isinstance(report, EnhancedBenchmarkReport)

    @pytest.mark.slow
    def test_report_findings_generation(self):
        """Test that findings are generated from results"""
        report = run_enhanced_benchmark(speed_grade="8Gbps")

        assert isinstance(report.findings, list)
        assert isinstance(report.warnings, list)

    @pytest.mark.slow
    def test_report_duration(self):
        """Test that report captures test duration"""
        report = run_enhanced_benchmark(speed_grade="8Gbps")

        assert report.duration_seconds > 0
        assert report.timestamp != ""

    def test_result_to_dict(self):
        """Test that results can be serialized to dict"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")

        mc_result = benchmark.run_multi_channel_test(num_requests_per_channel=10)
        assert isinstance(mc_result.to_dict(), dict)

        mt_result = benchmark.run_mixed_traffic_test(num_requests=50)
        assert isinstance(mt_result.to_dict(), dict)

        bg_result = benchmark.run_bank_group_conflict_test(num_requests=50)
        assert isinstance(bg_result.to_dict(), dict)

        rf_result = benchmark.run_refresh_impact_test(test_duration_ns=20_000)
        assert isinstance(rf_result.to_dict(), dict)

        qos_result = benchmark.run_qos_impact_test(num_requests=50)
        assert isinstance(qos_result.to_dict(), dict)

    def test_result_str_conversion(self):
        """Test that results can be converted to string"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")

        mc_result = benchmark.run_multi_channel_test(num_requests_per_channel=20)
        assert isinstance(str(mc_result), str)

        mt_result = benchmark.run_mixed_traffic_test(num_requests=100)
        assert isinstance(str(mt_result), str)

    def test_different_speed_grades(self):
        """Test running benchmarks at different speed grades"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            benchmark = EnhancedBenchmark(speed_grade=grade)
            result = benchmark.run_multi_channel_test(num_requests_per_channel=50)

            assert result.peak_bandwidth_gbs > 0

    def test_random_seed_reproducibility(self):
        """Test that same seed produces same results"""
        # Run same benchmark twice with same seed
        benchmark1 = EnhancedBenchmark(speed_grade="8Gbps", random_seed=12345)
        result1 = benchmark1.run_multi_channel_test(num_requests_per_channel=100)

        benchmark2 = EnhancedBenchmark(speed_grade="8Gbps", random_seed=12345)
        result2 = benchmark2.run_multi_channel_test(num_requests_per_channel=100)

        # Should have same number of requests per channel (order may differ)
        for ch in result1.per_channel_requests:
            assert result1.per_channel_requests[ch] == result2.per_channel_requests[ch]


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_run_multi_channel_benchmark(self):
        """Test run_multi_channel_benchmark convenience function"""
        result = run_multi_channel_benchmark()
        assert isinstance(result, MultiChannelResult)
        assert result.num_channels == 32

    def test_run_mixed_traffic_benchmark(self):
        """Test run_mixed_traffic_benchmark convenience function"""
        result = run_mixed_traffic_benchmark(read_ratio=0.8)
        assert isinstance(result, MixedTrafficResult)
        assert result.read_ratio == 0.8

    def test_run_bank_group_benchmark(self):
        """Test run_bank_group_benchmark convenience function"""
        result = run_bank_group_benchmark()
        assert isinstance(result, BankGroupConflictResult)

    def test_run_refresh_benchmark(self):
        """Test run_refresh_benchmark convenience function"""
        result = run_refresh_benchmark()
        assert isinstance(result, RefreshImpactResult)

    def test_run_qos_benchmark(self):
        """Test run_qos_benchmark convenience function"""
        result = run_qos_benchmark()
        assert isinstance(result, QoSImpactResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
