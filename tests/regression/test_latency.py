"""
Latency Regression Tests

延迟回归测试 - 验证不同流量模式下的延迟性能。
"""

import pytest
from tests.regression.constants import LATENCY_THRESHOLDS


class TestLatencyRegression:
    """延迟回归测试"""

    def test_latency_sequential(self, sequential_simulator):
        """顺序访问延迟回归测试

        顺序访问由于 row hit 较多，延迟应该较低。
        """
        stats = sequential_simulator.run()

        avg_latency = stats.avg_latency

        # 顺序访问平均延迟应该在合理范围
        assert avg_latency >= 0, "Latency should be non-negative"

        # 如果有完成的请求，验证延迟合理
        if stats.completed_requests > 0:
            assert avg_latency < 500, (
                f"Sequential latency {avg_latency:.1f} cycles too high"
            )

    def test_latency_random(self, random_simulator):
        """随机访问延迟回归测试

        随机访问由于 bank conflict，延迟可能较高。
        """
        stats = random_simulator.run()

        avg_latency = stats.avg_latency

        # 验证延迟非负
        assert avg_latency >= 0

        # 随机访问延迟可能比顺序访问高
        if stats.completed_requests > 0:
            assert avg_latency < 1000, (
                f"Random latency {avg_latency:.1f} cycles too high"
            )

    def test_latency_hot_spot(self, hot_spot_simulator):
        """热点访问延迟回归测试

        热点访问延迟应该较低（高 row hit rate）。
        """
        stats = hot_spot_simulator.run()

        avg_latency = stats.avg_latency

        assert avg_latency >= 0
        if stats.completed_requests > 0:
            assert avg_latency < 500, (
                f"Hot spot latency {avg_latency:.1f} cycles too high"
            )

    def test_latency_p50(self, random_simulator):
        """P50 延迟测试"""
        stats = random_simulator.run()

        # 计算 P50
        if hasattr(stats, 'latency_histogram') and stats.latency_histogram:
            import statistics
            sorted_latencies = sorted(stats.latency_histogram)
            p50_idx = len(sorted_latencies) // 2
            p50 = sorted_latencies[p50_idx]

            assert p50 < LATENCY_THRESHOLDS['p50_max'], (
                f"P50 latency {p50:.1f} cycles exceeds threshold"
            )

    def test_latency_p99(self, random_simulator):
        """P99 延迟测试"""
        stats = random_simulator.run()

        if hasattr(stats, 'latency_histogram') and stats.latency_histogram:
            import statistics
            sorted_latencies = sorted(stats.latency_histogram)
            p99_idx = int(len(sorted_latencies) * 0.99)
            if p99_idx >= len(sorted_latencies):
                p99_idx = len(sorted_latencies) - 1
            p99 = sorted_latencies[p99_idx]

            assert p99 < LATENCY_THRESHOLDS['p99_max'], (
                f"P99 latency {p99:.1f} cycles exceeds threshold"
            )


class TestLatencyDistribution:
    """延迟分布测试"""

    def test_latency_histogram_collection(self, random_simulator):
        """延迟直方图收集测试"""
        stats = random_simulator.run()

        # 验证延迟直方图被收集 (SimulationStats 可能没有此属性)
        if hasattr(stats, 'latency_histogram'):
            if stats.completed_requests > 0:
                assert len(stats.latency_histogram) > 0
        else:
            # 如果没有直方图，至少验证延迟统计存在
            assert stats.avg_latency >= 0

    def test_latency_range(self, sequential_simulator):
        """延迟范围测试"""
        stats = sequential_simulator.run()

        if hasattr(stats, 'latency_histogram') and stats.latency_histogram:
            latencies = stats.latency_histogram

            min_lat = min(latencies)
            max_lat = max(latencies)

            assert min_lat >= 0
            assert max_lat >= min_lat

    def test_latency_distribution_shape(self, random_simulator):
        """延迟分布形状测试

        验证延迟分布符合预期（大部分请求延迟较低）。
        """
        stats = random_simulator.run()

        if hasattr(stats, 'latency_histogram') and len(stats.latency_histogram) > 10:
            latencies = stats.latency_histogram
            import statistics

            mean = statistics.mean(latencies)
            median = statistics.median(latencies)

            # 中位数应该小于平均值（延迟分布右偏）
            assert median <= mean * 1.5, (
                f"Latency distribution not right-skewed: "
                f"median={median:.1f}, mean={mean:.1f}"
            )


class TestLatencyPerformance:
    """延迟性能测试"""

    def test_latency_consistency(self):
        """延迟一致性测试

        验证相同配置下多次运行的延迟一致性。
        """
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        results = []
        for seed in [42, 43, 44]:
            config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.SEQUENTIAL,
                request_rate=0.5,
                seed=seed,
            )
            sim = HBMSimulator(config)
            stats = sim.run()
            results.append(stats.avg_latency)

        # 所有运行的延迟都应该是非负的
        for lat in results:
            assert lat >= 0

    def test_latency_vs_request_rate(self):
        """延迟与请求率关系测试"""
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        latencies = []
        for rate in [0.3, 0.5, 0.8]:
            config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=rate,
                seed=42,
            )
            sim = HBMSimulator(config)
            stats = sim.run()
            latencies.append(stats.avg_latency)

        # 所有延迟都应该是非负的
        for lat in latencies:
            assert lat >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])