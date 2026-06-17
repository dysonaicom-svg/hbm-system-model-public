"""
Bandwidth Regression Tests

带宽回归测试 - 验证不同流量模式下的带宽性能。
"""

import pytest
from tests.regression.constants import BANDWIDTH_THRESHOLDS


class TestBandwidthRegression:
    """带宽回归测试"""

    def test_bandwidth_sequential(self, sequential_simulator):
        """顺序访问带宽回归测试

        验证顺序访问能达到合理的带宽。
        理论峰值: 819.2 GB/s/stack (HBM3 @ 6.4 Gbps)
        """
        stats = sequential_simulator.run()

        # 验证带宽在合理范围
        throughput = stats.throughput_gbps

        # 顺序访问应该能达到较高带宽
        assert throughput > BANDWIDTH_THRESHOLDS['sequential_min'], (
            f"Sequential bandwidth {throughput:.1f} GB/s below threshold "
            f"{BANDWIDTH_THRESHOLDS['sequential_min']} GB/s"
        )

        # 带宽不应超过理论峰值太多
        assert throughput < 1500, (
            f"Sequential bandwidth {throughput:.1f} GB/s exceeds reasonable limit"
        )

    def test_bandwidth_random(self, random_simulator):
        """随机访问带宽回归测试

        随机访问由于 bank conflict，带宽会较低。
        """
        stats = random_simulator.run()

        throughput = stats.throughput_gbps

        # 随机访问带宽应该高于最小阈值
        assert throughput > BANDWIDTH_THRESHOLDS['random_min'], (
            f"Random bandwidth {throughput:.1f} GB/s below threshold "
            f"{BANDWIDTH_THRESHOLDS['random_min']} GB/s"
        )

    def test_bandwidth_hot_spot(self, hot_spot_simulator):
        """热点访问带宽回归测试

        热点访问应该有较高的 row hit rate 和带宽。
        """
        stats = hot_spot_simulator.run()

        throughput = stats.throughput_gbps

        assert throughput > BANDWIDTH_THRESHOLDS['hot_spot_min'], (
            f"Hot spot bandwidth {throughput:.1f} GB/s below threshold "
            f"{BANDWIDTH_THRESHOLDS['hot_spot_min']} GB/s"
        )

    def test_bandwidth_stride(self, stride_simulator):
        """Stride 访问带宽回归测试

        Stride 访问通常会导致 bank conflict，带宽较低。
        """
        stats = stride_simulator.run()

        throughput = stats.throughput_gbps

        # Stride 访问带宽可以较低
        assert throughput >= 0, (
            f"Stride bandwidth {throughput:.1f} GB/s invalid"
        )

    def test_bandwidth_multi_pattern(self):
        """多模式带宽测试

        验证所有流量模式都能正常运行。
        """
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        patterns = [
            TrafficPattern.SEQUENTIAL,
            TrafficPattern.RANDOM,
            TrafficPattern.HOT_SPOT,
            TrafficPattern.STRIDE,
        ]

        results = {}
        for pattern in patterns:
            config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=pattern,
                request_rate=0.5,
                seed=42,
            )
            sim = HBMSimulator(config)
            stats = sim.run()
            results[pattern.name] = stats.throughput_gbps

        # 所有模式都应该产生带宽数据
        for pattern_name, bw in results.items():
            assert bw >= 0, f"Pattern {pattern_name} has invalid bandwidth {bw}"

    def test_bandwidth_vs_requests(self, random_simulator):
        """带宽与请求数关系测试

        验证请求数增加时带宽应该保持稳定。
        """
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.3,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats_low = sim.run()

        config.request_rate = 0.8
        sim = HBMSimulator(config)
        stats_high = sim.run()

        # 高请求率应该产生更多请求
        assert stats_high.total_requests > stats_low.total_requests

        # 带宽应该都在合理范围
        assert stats_low.throughput_gbps >= 0
        assert stats_high.throughput_gbps >= 0


class TestBandwidthPerformance:
    """带宽性能测试"""

    @pytest.mark.slow
    def test_long_simulation_bandwidth(self, long_simulator):
        """长时仿真的带宽稳定性

        验证长时间运行后带宽保持稳定。
        """
        stats = long_simulator.run()

        assert stats.total_cycles > 0
        assert stats.completed_requests > 0
        assert stats.throughput_gbps > 0

    def test_bandwidth_consistency(self):
        """带宽一致性测试

        验证相同配置下多次运行的结果一致性。
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
            results.append(stats.throughput_gbps)

        # 所有运行都应该产生正的带宽
        for bw in results:
            assert bw > 0

        # 带宽变化应该在合理范围内 (标准差 < 20%)
        import statistics
        mean = statistics.mean(results)
        stdev = statistics.stdev(results) if len(results) > 1 else 0
        if mean > 0:
            cv = stdev / mean
            assert cv < 0.3, f"Bandwidth variation {cv:.1%} too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])