"""Benchmark Tests
性能基准测试
"""

import sys
sys.path.insert(0, '/home/ic/JXTF/HBM')

import pytest
from sim.benchmark import HBMBenchmark, BenchmarkResult, TrafficPattern


class TestHBMBenchmark:
    """测试 HBM 基准测试器"""

    def test_benchmark_creation(self):
        """测试基准测试器创建"""
        bench = HBMBenchmark()
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

    def test_benchmark_suite(self):
        """测试基准测试套件"""
        bench = HBMBenchmark()

        # 只测试少量配置快速验证
        patterns = [TrafficPattern.RANDOM, TrafficPattern.SEQUENTIAL]
        rates = [0.3, 0.5]

        for pattern in patterns:
            for rate in rates:
                result = bench.run_single(pattern, rate, time_us=10.0, seed=42)
                bench.results.append(result)

        assert len(bench.results) == 4

    def test_sequential_pattern(self):
        """测试顺序访问模式"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            time_us=10.0,
            seed=42
        )

        assert isinstance(result, BenchmarkResult)
        assert result.pattern == "sequential"
        assert result.request_rate == 0.8

    def test_stride_pattern(self):
        """测试步进访问模式"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.STRIDE,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        assert isinstance(result, BenchmarkResult)
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

        assert isinstance(result, BenchmarkResult)
        assert result.pattern == "hot_spot"

    def test_benchmark_result_fields(self):
        """测试 BenchmarkResult 所有字段"""
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        # 检查所有必需字段存在且有有效值
        assert hasattr(result, 'pattern')
        assert hasattr(result, 'request_rate')
        assert hasattr(result, 'total_requests')
        assert hasattr(result, 'completed')
        assert hasattr(result, 'row_hit_rate')
        assert hasattr(result, 'avg_latency')
        assert hasattr(result, 'throughput_gbps')
        assert hasattr(result, 'simulation_time_ms')

        # 检查数值范围
        assert 0 <= result.row_hit_rate <= 1.0
        assert result.avg_latency >= 0.0
        assert result.throughput_gbps >= 0.0
        assert result.simulation_time_ms > 0.0

    def test_multiple_runs(self):
        """测试多次运行累积结果"""
        bench = HBMBenchmark()

        # 运行多次测试并手动累积结果
        result1 = bench.run_single(TrafficPattern.RANDOM, 0.3, time_us=5.0, seed=42)
        bench.results.append(result1)
        result2 = bench.run_single(TrafficPattern.SEQUENTIAL, 0.5, time_us=5.0, seed=42)
        bench.results.append(result2)

        assert len(bench.results) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])