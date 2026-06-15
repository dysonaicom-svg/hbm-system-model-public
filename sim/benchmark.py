"""HBM System Performance Benchmark
性能基准测试模块 - 分析不同流量模式下的吞吐量和延迟
"""

import os
import sys
import time
import logging
from dataclasses import dataclass
from typing import List, Optional, TextIO

# 添加项目根目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    pattern: str
    request_rate: float
    total_requests: int
    completed: int
    row_hit_rate: float
    avg_latency: float
    throughput_gbps: float
    wall_clock_time_ms: float  # 修复: 重命名以区分实际含义


class HBMBenchmark:
    """HBM 性能基准测试器"""

    def __init__(self, output_dir: str = "sim"):
        """初始化基准测试器

        Args:
            output_dir: 结果输出目录
        """
        self.results: List[BenchmarkResult] = []
        self.output_dir = output_dir

    def clear_results(self):
        """清空结果列表"""
        self.results = []

    def run_single(
        self,
        pattern: TrafficPattern,
        request_rate: float,
        time_us: float = 100.0,
        seed: Optional[int] = None,
        read_ratio: float = 0.7  # 修复: 暴露 read_ratio 参数
    ) -> BenchmarkResult:
        """运行单个基准测试

        Args:
            pattern: 流量模式
            request_rate: 请求率 (0.0-1.0)
            time_us: 仿真时间 (微秒)
            seed: 随机种子
            read_ratio: 读请求比例 (0.0-1.0)

        Returns:
            基准测试结果
        """
        config = SimulationConfig(
            simulation_time_us=time_us,
            traffic_pattern=pattern,
            request_rate=request_rate,
            read_ratio=read_ratio,  # 修复: 使用参数化值
            seed=seed
        )

        start = time.time()
        sim = HBMSimulator(config)
        stats = sim.run()
        elapsed_ms = (time.time() - start) * 1000

        return BenchmarkResult(
            pattern=pattern.value,
            request_rate=request_rate,
            total_requests=stats.total_requests,
            completed=stats.completed_requests,
            row_hit_rate=stats.row_hit_rate,
            avg_latency=stats.avg_latency,
            throughput_gbps=stats.throughput_gbps,
            wall_clock_time_ms=elapsed_ms  # 修复: 重命名字段
        )

    def run_suite(
        self,
        patterns: Optional[List[TrafficPattern]] = None,
        rates: Optional[List[float]] = None,
        time_us: float = 100.0,
        seed: int = 42,
        read_ratio: float = 0.7
    ) -> List[BenchmarkResult]:
        """运行基准测试套件

        Args:
            patterns: 要测试的流量模式列表
            rates: 要测试的请求率列表
            time_us: 仿真时间 (微秒)
            seed: 随机种子
            read_ratio: 读请求比例

        Returns:
            所有测试结果
        """
        if patterns is None:
            patterns = [
                TrafficPattern.RANDOM,
                TrafficPattern.SEQUENTIAL,
                TrafficPattern.STRIDE,
                TrafficPattern.HOT_SPOT,
            ]

        if rates is None:
            rates = [0.3, 0.5, 0.8, 1.0]

        for pattern in patterns:
            for rate in rates:
                logger.info(f"Running {pattern.value} @ rate={rate}...")
                result = self.run_single(
                    pattern, rate,
                    time_us=time_us,
                    seed=seed,
                    read_ratio=read_ratio
                )
                self.results.append(result)

        return self.results

    def print_results(self, stream: Optional[TextIO] = None):
        """打印结果表格

        Args:
            stream: 输出流 (默认 stdout)
        """
        if stream is None:
            stream = __import__('sys').stdout

        print("\n" + "=" * 90, file=stream)
        print(f"{'Pattern':<15} {'Rate':>6} {'Reqs':>8} {'Completed':>10} "
              f"{'Hit%':>8} {'Latency':>10} {'TPut':>10} {'Time':>8}", file=stream)
        print("-" * 90, file=stream)

        for r in self.results:
            print(f"{r.pattern:<15} {r.request_rate:>6.2f} {r.total_requests:>8} "
                  f"{r.completed:>10} {r.row_hit_rate:>8.1%} {r.avg_latency:>10.1f} "
                  f"{r.throughput_gbps:>10.2f} {r.wall_clock_time_ms:>8.1f}", file=stream)

        print("=" * 90, file=stream)

    def save_results(self, filename: str = "benchmark_results.json"):
        """保存结果到 JSON 文件

        Args:
            filename: 输出文件名
        """
        import json

        # 确保输出目录存在
        output_path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)

        results_dict = [
            {
                "pattern": r.pattern,
                "request_rate": r.request_rate,
                "total_requests": r.total_requests,
                "completed": r.completed,
                "row_hit_rate": r.row_hit_rate,
                "avg_latency": r.avg_latency,
                "throughput_gbps": r.throughput_gbps,
                "wall_clock_time_ms": r.wall_clock_time_ms
            }
            for r in self.results
        ]

        with open(output_path, "w") as f:
            json.dump(results_dict, f, indent=2)

        logger.info(f"Results saved to {output_path}")


def main():
    """运行基准测试"""
    print("=" * 60)
    print("HBM Performance Benchmark Suite")
    print("=" * 60)

    bench = HBMBenchmark(output_dir="sim")
    bench.run_suite(time_us=100.0, seed=42, read_ratio=0.7)
    bench.print_results()
    bench.save_results()

    # 生成 HTML 报告
    try:
        from sim.report_generator import generate_html_report, ReportData

        # 创建报告数据
        report = ReportData(
            simulation_name="HBM Performance Benchmark",
            simulation_time_us=100.0,
            total_requests=sum(r.total_requests for r in bench.results),
            completed_requests=sum(r.completed for r in bench.results),
            throughput_gbps=sum(r.throughput_gbps for r in bench.results) / len(bench.results),
            avg_latency_cycles=sum(r.avg_latency for r in bench.results) / len(bench.results),
        )

        # 添加各模式带宽数据
        for r in bench.results:
            report.bandwidth_by_pattern[r.pattern] = r.throughput_gbps

        # 生成报告
        generate_html_report(report, "sim/results/benchmark_report.html")
        print("\nHTML report generated: sim/results/benchmark_report.html")
    except Exception as e:
        print(f"\nReport generation skipped: {e}")

    print("\nBenchmark complete.")


if __name__ == "__main__":
    main()