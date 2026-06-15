"""Benchmark Tests with Enhanced Metrics
性能基准测试 - 包含吞吐量和延迟百分位数指标
"""

import sys
import os
sys.path.insert(0, '/home/ic/JXTF/HBM')

import pytest
from sim.benchmark import (
    HBMComprehensiveBenchmark as HBMBenchmark,
    BenchmarkResult,
    LatencyPercentiles,
    ChannelMetrics,
    calculate_percentile,
)
from sim.simulator import TrafficPattern


class TestLatencyPercentiles:
    """测试延迟百分位数计算"""

    def test_calculate_percentile_median(self):
        """测试中位数计算"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert calculate_percentile(data, 50) == 5.5

    def test_calculate_percentile_empty(self):
        """测试空数据"""
        assert calculate_percentile([], 50) == 0.0

    def test_calculate_percentile_single(self):
        """测试单元素"""
        assert calculate_percentile([42], 50) == 42.0

    def test_calculate_percentile_p95(self):
        """测试P95"""
        data = list(range(1, 101))  # 1-100
        p95 = calculate_percentile(data, 95)
        assert 94 <= p95 <= 96

    def test_calculate_percentile_p99(self):
        """测试P99"""
        data = list(range(1, 1001))  # 1-1000
        p99 = calculate_percentile(data, 99)
        assert 990 <= p99 <= 1000

    def test_latency_percentiles_to_dict(self):
        """测试百分位数对象转字典"""
        p = LatencyPercentiles(p50=10.0, p95=50.0, p99=100.0)
        d = p.to_dict()
        assert d['p50'] == 10.0
        assert d['p95'] == 50.0
        assert d['p99'] == 100.0


class TestChannelUtilization:
    """测试通道利用率"""

    def test_channel_utilization_creation(self):
        """测试通道利用率创建"""
        ch = ChannelMetrics(
            channel_id=0,
            requests=100,
            total_latency_cycles=5000,
            row_hits=70,
            row_misses=30,
            utilization_percent=50.0,
            hit_rate=0.7,
        )
        assert ch.channel_id == 0
        assert ch.requests == 100
        assert ch.hit_rate == 0.7

    def test_channel_utilization_to_dict(self):
        """测试通道利用率转字典"""
        ch = ChannelMetrics(channel_id=0)
        d = ch.to_dict()
        assert 'channel_id' in d
        assert 'utilization_percent' in d
        assert 'hit_rate' in d


class TestBenchmarkResult:
    """测试基准测试结果"""

    def test_result_with_new_fields(self):
        """测试包含新字段的结果"""
        result = BenchmarkResult(
            pattern="random",
            request_rate=0.5,
            total_requests=1000,
            completed=900,
            row_hit_rate=0.75,
            avg_latency=50.0,
            max_latency=100,
            min_latency=20,
            throughput_gbps=100.0,
            bandwidth_efficiency=0.12,
            wall_clock_time_ms=500.0,
            efficiency=0.8,
            dram_activations=500,
            requests_per_second=1800.0,
            latency_percentiles=LatencyPercentiles(p50=48.0, p95=80.0, p99=95.0),
            per_channel_utilization=[],
        )

        assert result.requests_per_second == 1800.0
        assert result.latency_percentiles.p50 == 48.0
        assert result.latency_percentiles.p95 == 80.0
        assert result.latency_percentiles.p99 == 95.0

    def test_result_to_dict(self):
        """测试结果转字典"""
        result = BenchmarkResult(
            pattern="random",
            request_rate=0.5,
            total_requests=1000,
            completed=900,
            row_hit_rate=0.75,
            avg_latency=50.0,
            max_latency=100,
            min_latency=20,
            throughput_gbps=100.0,
            bandwidth_efficiency=0.12,
            wall_clock_time_ms=500.0,
            efficiency=0.8,
            dram_activations=500,
        )

        d = result.to_dict()
        assert 'pattern' in d
        assert 'requests_per_second' in d
        assert 'latency_percentiles' in d
        assert 'per_channel_utilization' in d


class TestHBMBenchmark:
    """测试 HBM 基准测试器"""

    def test_benchmark_creation(self):
        """测试基准测试器创建"""
        bench = HBMBenchmark()
        assert len(bench.results) == 0
        assert bench.output_dir == "sim"

    def test_clear_results(self):
        """测试清空结果"""
        bench = HBMBenchmark()
        result = bench.run_single(TrafficPattern.RANDOM, 0.5, time_us=10.0, seed=42)
        bench.results.append(result)
        assert len(bench.results) == 1
        bench.clear_results()
        assert len(bench.results) == 0

    def test_single_benchmark(self):
        """测试单个基准测试"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        assert isinstance(result, BenchmarkResult)
        assert result.pattern == "random"
        assert result.request_rate == 0.5
        assert result.total_requests >= 0
        assert result.row_hit_rate >= 0.0
        assert result.throughput_gbps >= 0.0
        assert result.wall_clock_time_ms >= 0.0

    def test_throughput_measurement(self):
        """测试吞吐量测量 (req/s)"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        # 吞吐量应该大于0
        assert result.requests_per_second >= 0.0
        # 如果有完成的请求，应该有吞吐量
        if result.completed > 0:
            assert result.requests_per_second > 0

    def test_latency_percentiles(self):
        """测试延迟百分位数"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        p = result.latency_percentiles
        assert isinstance(p, LatencyPercentiles)
        # P95应该 >= P50
        if p.p50 > 0 and p.p95 > 0:
            assert p.p95 >= p.p50
        # P99应该 >= P95
        if p.p95 > 0 and p.p99 > 0:
            assert p.p99 >= p.p95

    def test_channel_utilization_metrics(self):
        """测试通道利用率指标"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        # 检查通道利用率列表
        assert isinstance(result.per_channel_utilization, list)
        # 如果有请求，通道利用率应该不为空
        if result.completed > 0:
            assert len(result.per_channel_utilization) > 0
            # 每个通道应该有利用率和命中率
            for ch in result.per_channel_utilization:
                assert isinstance(ch, ChannelUtilization)
                assert 0 <= ch.hit_rate <= 1.0

    def test_read_ratio_parameter(self):
        """测试 read_ratio 参数化"""
        bench = HBMBenchmark()

        # 测试纯读
        result_read = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42,
            read_ratio=1.0
        )
        assert result_read.total_requests >= 0

        # 测试纯写
        bench.clear_results()
        result_write = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42,
            read_ratio=0.0
        )
        assert result_write.total_requests >= 0

    def test_benchmark_suite(self):
        """测试基准测试套件"""
        bench = HBMBenchmark()

        patterns = [TrafficPattern.RANDOM, TrafficPattern.SEQUENTIAL]
        rates = [0.3, 0.5]

        bench.run_suite(patterns=patterns, rates=rates, time_us=10.0, seed=42)
        assert len(bench.results) == 4

    def test_sequential_pattern(self):
        """测试顺序访问模式"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )
        assert result.pattern == "sequential"
        assert result.throughput_gbps >= 0.0

    def test_stride_pattern(self):
        """测试跨步访问模式"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.STRIDE,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )
        assert result.pattern == "stride"

    def test_hotspot_pattern(self):
        """测试热点访问模式"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.HOT_SPOT,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )
        assert result.pattern == "hot_spot"

    def test_reproducibility(self):
        """测试可重现性 - 相同种子应产生相同结果"""
        bench1 = HBMBenchmark()
        result1 = bench1.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=12345
        )

        bench2 = HBMBenchmark()
        result2 = bench2.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=12345
        )

        # 相同种子应该产生相同数量的请求
        assert result1.total_requests == result2.total_requests

    def test_edge_case_zero_rate(self):
        """测试零请求率边界情况"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.0,
            time_us=10.0,
            seed=42
        )
        assert result.total_requests == 0

    def test_edge_case_max_rate(self):
        """测试最大请求率边界情况"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=1.0,
            time_us=10.0,
            seed=42
        )
        assert result.total_requests >= 0
        assert result.completed >= 0

    def test_result_fields(self):
        """测试结果字段完整性"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        # 验证所有字段都存在且类型正确
        assert isinstance(result.pattern, str)
        assert isinstance(result.request_rate, float)
        assert isinstance(result.total_requests, int)
        assert isinstance(result.completed, int)
        assert isinstance(result.row_hit_rate, float)
        assert isinstance(result.avg_latency, float)
        assert isinstance(result.max_latency, int)  # Latency in cycles
        assert isinstance(result.min_latency, int)
        assert isinstance(result.throughput_gbps, float)
        assert isinstance(result.bandwidth_efficiency, float)
        assert isinstance(result.wall_clock_time_ms, float)
        assert isinstance(result.efficiency, float)

        # 新字段验证
        assert isinstance(result.requests_per_second, float)
        assert isinstance(result.latency_percentiles, LatencyPercentiles)
        assert isinstance(result.per_channel_utilization, list)

        # 检查数值范围
        assert 0 <= result.row_hit_rate <= 1.0
        assert result.avg_latency >= 0.0
        assert result.throughput_gbps >= 0.0
        assert result.wall_clock_time_ms >= 0.0
        assert 0.0 <= result.bandwidth_efficiency <= 1.0
        assert result.requests_per_second >= 0.0

    def test_stress_test(self):
        """测试压力测试"""
        bench = HBMBenchmark()
        result = bench.run_stress_test(duration_us=50.0, seed=42)

        assert result.pattern == "random"
        assert result.request_rate == 1.0
        assert result.efficiency >= 0.0

    def test_calculate_metrics(self):
        """测试性能指标计算"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        metrics = bench.calculate_metrics(result)
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.theoretical_bandwidth_gbps == 819.2 * 2
        assert metrics.actual_bandwidth_gbps == result.throughput_gbps

    def test_save_results(self, tmp_path):
        """测试保存结果到文件"""
        bench = HBMBenchmark(output_dir=str(tmp_path))
        result = bench.run_single(TrafficPattern.RANDOM, 0.5, time_us=10.0, seed=42)
        bench.results.append(result)  # Manually add result (run_single doesn't auto-add)

        bench.save_results("test_results.json")

        output_file = tmp_path / "test_results.json"
        assert output_file.exists()

        # 验证保存的内容包含新字段
        import json
        with open(output_file) as f:
            data = json.load(f)
        assert len(data) > 0
        assert 'requests_per_second' in data[0]
        assert 'latency_percentiles' in data[0]

    def test_print_results_output(self, capsys):
        """测试打印结果输出"""
        bench = HBMBenchmark()
        result = bench.run_single(TrafficPattern.RANDOM, 0.5, time_us=10.0, seed=42)
        bench.results.append(result)

        bench.print_results()

        captured = capsys.readouterr()
        assert "random" in captured.out
        # 验证新的列标题存在
        assert "P50" in captured.out or "Req/s" in captured.out

    def test_unified_simulator_benchmark(self):
        """测试统一仿真器基准测试"""
        bench = HBMBenchmark()
        result = bench.run_unified_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.3,
            time_us=10.0,
            seed=42,
            num_masters=2,
        )

        assert "multi" in result.pattern
        assert result.bandwidth_efficiency >= 0.0
        assert result.requests_per_second >= 0.0

    def test_get_summary_dict(self):
        """测试获取摘要字典"""
        bench = HBMBenchmark()
        result = bench.run_single(TrafficPattern.RANDOM, 0.5, time_us=10.0, seed=42)
        bench.results.append(result)  # Manually add result

        summary = bench.get_summary_dict()
        assert isinstance(summary, dict)
        assert 'total_completed_requests' in summary
        assert 'avg_throughput_gbps' in summary
        assert 'peak_bandwidth_gbps' in summary
        assert 'peak_bandwidth_efficiency' in summary


class TestLatencyPercentileCalculation:
    """测试延迟百分位数计算的正确性"""

    def test_percentile_ordering(self):
        """验证百分位数单调递增"""
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        p50 = calculate_percentile(data, 50)
        p95 = calculate_percentile(data, 95)
        p99 = calculate_percentile(data, 99)

        assert p50 <= p95 <= p99

    def test_percentile_with_realistic_data(self):
        """使用真实模拟的延迟数据测试"""
        import random
        random.seed(42)

        # 模拟一个行命中率70%的请求延迟分布
        data = []
        for _ in range(1000):
            if random.random() < 0.7:
                # Row hit: 30-50 cycles
                data.append(random.uniform(30, 50))
            else:
                # Row miss: 80-150 cycles
                data.append(random.uniform(80, 150))

        p50 = calculate_percentile(data, 50)
        p95 = calculate_percentile(data, 95)
        p99 = calculate_percentile(data, 99)

        # P50 应该接近行命中的范围
        assert 30 <= p50 <= 60
        # P95 应该包含一些行缺失
        assert p95 >= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])