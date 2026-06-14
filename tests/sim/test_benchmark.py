"""Benchmark Tests
性能基准测试
"""

import sys
import os
sys.path.insert(0, '/home/ic/JXTF/HBM')

import pytest
from sim.benchmark import HBMBenchmark, BenchmarkResult, TrafficPattern


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
        assert isinstance(result.throughput_gbps, float)
        assert isinstance(result.wall_clock_time_ms, float)

        # 检查数值范围
        assert 0 <= result.row_hit_rate <= 1.0
        assert result.avg_latency >= 0.0
        assert result.throughput_gbps >= 0.0
        assert result.wall_clock_time_ms >= 0.0

    def test_save_results(self, tmp_path):
        """测试保存结果到文件"""
        bench = HBMBenchmark(output_dir=str(tmp_path))
        bench.run_single(TrafficPattern.RANDOM, 0.5, time_us=10.0, seed=42)

        bench.save_results("test_results.json")

        output_file = tmp_path / "test_results.json"
        assert output_file.exists()

    def test_print_results_output(self, capsys):
        """测试打印结果输出"""
        bench = HBMBenchmark()
        result = bench.run_single(TrafficPattern.RANDOM, 0.5, time_us=10.0, seed=42)
        bench.results.append(result)

        bench.print_results()

        captured = capsys.readouterr()
        assert "random" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])