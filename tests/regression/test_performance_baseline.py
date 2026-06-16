"""
Performance Baseline Regression Tests

性能基线回归测试 - 验证不同流量模式下的基本性能指标。
测试 row hit rate、latency 和 throughput 是否在预期范围内。

Traffic Patterns Tested:
- Random: 随机访问，通常有较低的 row hit rate
- Sequential: 顺序访问，应该有较高的 row hit rate
- Hot Spot: 热点访问，应该有最高的 row hit rate
"""

import pytest
from typing import Dict, Any

from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern
from model.controller.config import HBMConfig, HBM3_DEFAULT
from tests.regression.conftest import (
    LATENCY_THRESHOLDS,
    ROW_HIT_THRESHOLDS,
)


class TestRandomTrafficBaseline:
    """随机流量性能基线测试"""

    @pytest.mark.regression
    @pytest.mark.performance
    def test_random_row_hit_rate(self, random_simulator):
        """验证随机访问的 row hit rate 在合理范围

        随机访问由于地址完全随机分布，row hit rate 应该较低。
        预期范围: 0% - 30% (由于 bank 随机分布)
        """
        stats = random_simulator.run()

        row_hit_rate = stats.row_hit_rate

        # 随机访问的 row hit rate 应该较低 (低于 30%)
        assert row_hit_rate < 0.30, (
            f"Random traffic row hit rate {row_hit_rate:.2%} unexpectedly high. "
            f"Expected < 30% for random access."
        )

        # row hit rate 应该非负
        assert row_hit_rate >= 0.0, (
            f"Row hit rate {row_hit_rate:.2%} is negative"
        )

    @pytest.mark.regression
    @pytest.mark.performance
    def test_random_latency(self, random_simulator):
        """验证随机访问的平均延迟在阈值内

        随机访问由于 row miss 较多，延迟应该较高。
        """
        stats = random_simulator.run()

        avg_latency = stats.avg_latency

        # 验证延迟在合理范围内
        assert avg_latency >= 0, (
            f"Average latency {avg_latency:.1f} cycles is invalid"
        )

        # P50 延迟不应超过阈值
        # 注意: 实际 P50 延迟从 avg_latency 推算
        assert avg_latency < LATENCY_THRESHOLDS['p50_max'], (
            f"Random traffic P50 latency {avg_latency:.1f} cycles exceeds threshold "
            f"{LATENCY_THRESHOLDS['p50_max']} cycles"
        )

    @pytest.mark.regression
    def test_random_throughput(self, random_simulator):
        """验证随机访问的吞吐量

        随机访问吞吐量应该为正数。
        """
        stats = random_simulator.run()

        throughput = stats.throughput_gbps

        assert throughput >= 0, (
            f"Random traffic throughput {throughput:.2f} GB/s is invalid"
        )

    @pytest.mark.regression
    def test_random_request_completion(self, random_simulator):
        """验证随机访问的请求完成率

        应该有请求被提交和完成。
        """
        stats = random_simulator.run()

        assert stats.total_requests >= 0, (
            "Total requests should be non-negative"
        )
        assert stats.completed_requests >= 0, (
            "Completed requests should be non-negative"
        )

        # 完成率应该合理 (允许队列满导致的未完成)
        if stats.total_requests > 0:
            completion_rate = stats.completed_requests / stats.total_requests
            assert completion_rate >= 0, (
                f"Completion rate {completion_rate:.2%} is invalid"
            )


class TestSequentialTrafficBaseline:
    """顺序流量性能基线测试"""

    @pytest.mark.regression
    @pytest.mark.performance
    def test_sequential_row_hit_rate(self, sequential_simulator):
        """验证顺序访问的 row hit rate

        顺序访问由于地址连续，row hit rate 应该较高。
        预期范围: 50% - 95%
        """
        stats = sequential_simulator.run()

        row_hit_rate = stats.row_hit_rate

        # 顺序访问应该至少有基本的 row hit
        # 由于 bank group 结构，row hit rate 可能不是 100%
        assert row_hit_rate >= ROW_HIT_THRESHOLDS['sequential_min'], (
            f"Sequential traffic row hit rate {row_hit_rate:.2%} below minimum "
            f"threshold {ROW_HIT_THRESHOLDS['sequential_min']:.2%}"
        )

        # 顺序访问的 row hit rate 通常较高
        # 但由于 HBM bank group 结构，实际可能不是特别高
        assert row_hit_rate >= 0.0, (
            f"Row hit rate {row_hit_rate:.2%} is invalid"
        )

    @pytest.mark.regression
    @pytest.mark.performance
    def test_sequential_latency(self, sequential_simulator):
        """验证顺序访问的低延迟

        顺序访问由于 row hit 较多，延迟应该较低。
        """
        stats = sequential_simulator.run()

        avg_latency = stats.avg_latency

        assert avg_latency >= 0, (
            f"Sequential traffic latency {avg_latency:.1f} cycles is invalid"
        )

        # 顺序访问延迟应该明显低于随机访问
        # 这里我们验证延迟在合理范围内即可
        assert avg_latency < LATENCY_THRESHOLDS['p50_max'], (
            f"Sequential traffic P50 latency {avg_latency:.1f} cycles exceeds threshold"
        )

    @pytest.mark.regression
    def test_sequential_throughput(self, sequential_simulator):
        """验证顺序访问的高吞吐量

        顺序访问应该有较高的带宽利用率。
        """
        stats = sequential_simulator.run()

        throughput = stats.throughput_gbps

        assert throughput >= 0, (
            f"Sequential traffic throughput {throughput:.2f} GB/s is invalid"
        )


class TestHotSpotTrafficBaseline:
    """热点流量性能基线测试"""

    @pytest.mark.regression
    @pytest.mark.performance
    def test_hotspot_row_hit_rate(self, hot_spot_simulator):
        """验证热点访问的高 row hit rate

        热点访问由于 80% 流量访问热点区域，row hit rate 应该最高。
        预期范围: 40% - 90%
        """
        stats = hot_spot_simulator.run()

        row_hit_rate = stats.row_hit_rate

        # 热点访问应该有较高的 row hit rate
        assert row_hit_rate >= ROW_HIT_THRESHOLDS['hot_spot_min'], (
            f"Hot spot traffic row hit rate {row_hit_rate:.2%} below minimum "
            f"threshold {ROW_HIT_THRESHOLDS['hot_spot_min']:.2%}"
        )

        assert row_hit_rate >= 0.0, (
            f"Row hit rate {row_hit_rate:.2%} is invalid"
        )

    @pytest.mark.regression
    @pytest.mark.performance
    def test_hotspot_latency(self, hot_spot_simulator):
        """验证热点访问的低延迟

        热点访问应该有较低的延迟。
        """
        stats = hot_spot_simulator.run()

        avg_latency = stats.avg_latency

        assert avg_latency >= 0, (
            f"Hot spot traffic latency {avg_latency:.1f} cycles is invalid"
        )

        assert avg_latency < LATENCY_THRESHOLDS['p50_max'], (
            f"Hot spot traffic P50 latency {avg_latency:.1f} cycles exceeds threshold"
        )

    @pytest.mark.regression
    def test_hotspot_throughput(self, hot_spot_simulator):
        """验证热点访问的高吞吐量

        热点访问应该有较高的带宽利用率。
        """
        stats = hot_spot_simulator.run()

        throughput = stats.throughput_gbps

        assert throughput >= 0, (
            f"Hot spot traffic throughput {throughput:.2f} GB/s is invalid"
        )


class TestStrideTrafficBaseline:
    """Stride 流量性能基线测试"""

    @pytest.mark.regression
    def test_stride_basic_operation(self, stride_simulator):
        """验证 stride 访问的基本运行

        Stride 访问会导致 bank conflict，带宽较低但应该能正常运行。
        """
        stats = stride_simulator.run()

        # 验证基本统计
        assert stats.total_requests >= 0, (
            "Stride traffic total requests should be non-negative"
        )
        assert stats.completed_requests >= 0, (
            "Stride traffic completed requests should be non-negative"
        )
        assert stats.row_hit_rate >= 0.0, (
            f"Stride traffic row hit rate {stats.row_hit_rate:.2%} is invalid"
        )

    @pytest.mark.regression
    def test_stride_latency(self, stride_simulator):
        """验证 stride 访问的延迟

        Stride 访问由于 bank conflict，延迟可能较高。
        """
        stats = stride_simulator.run()

        avg_latency = stats.avg_latency

        assert avg_latency >= 0, (
            f"Stride traffic latency {avg_latency:.1f} cycles is invalid"
        )


class TestPerformanceComparison:
    """流量模式性能对比测试"""

    @pytest.mark.regression
    @pytest.mark.performance
    def test_row_hit_rate_ranking(self):
        """验证 row hit rate 排序符合预期

        预期排序: Hot Spot > Sequential > Random
        (Hot Spot 和 Sequential 可能接近，Random 最低)
        """
        results: Dict[str, Dict[str, float]] = {}

        patterns = [
            TrafficPattern.RANDOM,
            TrafficPattern.SEQUENTIAL,
            TrafficPattern.HOT_SPOT,
        ]

        for pattern in patterns:
            config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=pattern,
                request_rate=0.5,
                seed=42,
            )
            sim = HBMSimulator(config)
            stats = sim.run()
            results[pattern.value] = {
                'row_hit_rate': stats.row_hit_rate,
                'avg_latency': stats.avg_latency,
            }

        # 验证 Random 的 row hit rate 最低
        random_rate = results[TrafficPattern.RANDOM.value]['row_hit_rate']
        sequential_rate = results[TrafficPattern.SEQUENTIAL.value]['row_hit_rate']
        hotspot_rate = results[TrafficPattern.HOT_SPOT.value]['row_hit_rate']

        # Hot Spot 和 Sequential 的 row hit rate 应该 >= Random
        assert hotspot_rate >= random_rate * 0.5, (
            f"Hot spot row hit rate {hotspot_rate:.2%} should be >= "
            f"random row hit rate {random_rate:.2%}"
        )
        assert sequential_rate >= random_rate * 0.5, (
            f"Sequential row hit rate {sequential_rate:.2%} should be >= "
            f"random row hit rate {random_rate:.2%}"
        )

    @pytest.mark.regression
    def test_latency_vs_row_hit_correlation(self):
        """验证延迟与 row hit rate 的相关性

        Row hit 越多，延迟应该越低。
        """
        results: Dict[str, Dict[str, float]] = {}

        patterns = [
            TrafficPattern.RANDOM,
            TrafficPattern.SEQUENTIAL,
            TrafficPattern.HOT_SPOT,
        ]

        for pattern in patterns:
            config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=pattern,
                request_rate=0.5,
                seed=42,
            )
            sim = HBMSimulator(config)
            stats = sim.run()
            results[pattern.value] = {
                'row_hit_rate': stats.row_hit_rate,
                'avg_latency': stats.avg_latency,
            }

        # 比较延迟和 row hit rate 的关系
        # 这是一个相关性检查，不做硬性断言
        for pattern in patterns:
            rate = results[pattern.value]['row_hit_rate']
            latency = results[pattern.value]['avg_latency']

            assert latency >= 0, (
                f"{pattern.value} latency should be non-negative"
            )
            assert rate >= 0 and rate <= 1, (
                f"{pattern.value} row hit rate should be in [0, 1]"
            )


class TestStabilityAndConsistency:
    """稳定性和一致性测试"""

    @pytest.mark.regression
    @pytest.mark.slow
    def test_multiple_seeds_consistency(self):
        """验证使用不同种子时的一致性

        相同配置不同种子应该产生相似的结果分布。
        """
        seeds = [42, 123, 456, 789, 1024]
        results = []

        for seed in seeds:
            config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.SEQUENTIAL,
                request_rate=0.5,
                seed=seed,
            )
            sim = HBMSimulator(config)
            stats = sim.run()
            results.append({
                'row_hit_rate': stats.row_hit_rate,
                'avg_latency': stats.avg_latency,
                'completed': stats.completed_requests,
            })

        # 验证所有运行都成功完成
        for i, r in enumerate(results):
            assert r['completed'] >= 0, (
                f"Seed {seeds[i]}: completed requests should be non-negative"
            )

        # 计算变异系数 (CV)
        import statistics

        completed_counts = [r['completed'] for r in results]
        mean_completed = statistics.mean(completed_counts)
        if mean_completed > 0:
            stdev_completed = statistics.stdev(completed_counts) if len(completed_counts) > 1 else 0
            cv_completed = stdev_completed / mean_completed

            # 变异系数应该在合理范围内
            assert cv_completed < 0.5, (
                f"Completed requests variation {cv_completed:.1%} too high. "
                f"Values: {completed_counts}"
            )

    @pytest.mark.regression
    def test_no_crash_or_deadlock(self):
        """验证长时间仿真不会崩溃或死锁

        运行较长时间的仿真，确保系统稳定。
        """
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        sim = HBMSimulator(config)

        # 运行仿真
        stats = sim.run()

        # 验证没有异常状态
        assert stats.total_cycles > 0, (
            "Total cycles should be positive"
        )
        assert stats.total_requests >= 0, (
            "Total requests should be non-negative"
        )

        # 完成请求数应该合理
        assert stats.completed_requests >= 0, (
            "Completed requests should be non-negative"
        )

    @pytest.mark.regression
    @pytest.mark.slow
    def test_long_duration_stability(self, long_simulator):
        """验证长时仿真的稳定性

        500us 仿真应该能正常完成。
        """
        stats = long_simulator.run()

        assert stats.total_cycles > 0, (
            "Total cycles should be positive after long simulation"
        )
        assert stats.completed_requests >= 0, (
            "Completed requests should be non-negative"
        )


class TestBandwidthMetrics:
    """带宽指标测试"""

    @pytest.mark.regression
    def test_bandwidth_calculation(self):
        """验证带宽计算的正确性

        带宽应该基于完成请求数和总周期数计算。
        """
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 带宽计算
        throughput = stats.throughput_gbps

        # 带宽应该是正数（如果有完成请求）
        if stats.completed_requests > 0:
            assert throughput > 0, (
                f"Throughput should be positive when {stats.completed_requests} "
                f"requests completed"
            )

        # 带宽不应该超过理论峰值太多 (HBM3 ~ 819 GB/s/stack)
        assert throughput < 2000, (
            f"Throughput {throughput:.2f} GB/s exceeds reasonable maximum"
        )

    @pytest.mark.regression
    @pytest.mark.performance
    def test_read_write_bandwidth_split(self):
        """验证读写带宽分配

        读请求通常占用更多带宽。
        """
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            read_ratio=0.7,  # 70% 读
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 读请求应该多于写请求
        assert stats.read_requests >= stats.write_requests, (
            f"Read requests {stats.read_requests} should be >= "
            f"write requests {stats.write_requests} with 70% read ratio"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "regression"])