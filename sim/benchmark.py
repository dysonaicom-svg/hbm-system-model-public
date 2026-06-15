"""HBM System Performance Benchmark
性能基准测试模块 - 分析不同流量模式下的吞吐量和延迟
"""

import os
import sys
import time
import json
import statistics
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, TextIO, Dict, Any

# 添加项目根目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern
from sim.unified_simulator import UnifiedSimulator, UnifiedSimulatorStats

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
    max_latency: float
    min_latency: float
    throughput_gbps: float
    bandwidth_efficiency: float
    wall_clock_time_ms: float
    efficiency: float = 0.0
    dram_activations: int = 0


@dataclass
class PerformanceMetrics:
    """详细性能指标"""
    cycles_per_request: float
    requests_per_cycle: float
    row_open_ratio: float
    read_write_ratio: float
    theoretical_bandwidth_gbps: float
    actual_bandwidth_gbps: float
    latency_percentiles: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
        read_ratio: float = 0.7
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
            read_ratio=read_ratio,
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
            max_latency=stats.max_latency_cycles,
            min_latency=stats.min_latency_cycles,
            throughput_gbps=stats.throughput_gbps,
            bandwidth_efficiency=stats.bandwidth_efficiency,
            wall_clock_time_ms=elapsed_ms,
            efficiency=stats.efficiency,
            dram_activations=stats.total_dram_activations,
        )

    def run_unified_single(
        self,
        pattern: TrafficPattern,
        request_rate: float,
        time_us: float = 100.0,
        seed: Optional[int] = None,
        read_ratio: float = 0.7,
        num_masters: int = 4,
    ) -> BenchmarkResult:
        """运行统一仿真器基准测试

        Args:
            pattern: 流量模式
            request_rate: 请求率
            time_us: 仿真时间
            seed: 随机种子
            read_ratio: 读比例
            num_masters: AXI master 数量

        Returns:
            基准测试结果
        """
        config = SimulationConfig(
            simulation_time_us=time_us,
            traffic_pattern=pattern,
            request_rate=request_rate,
            read_ratio=read_ratio,
            seed=seed
        )

        start = time.time()
        sim = UnifiedSimulator(
            sim_config=config,
            num_masters=num_masters,
            enable_axi=True,
        )
        stats = sim.run()
        elapsed_ms = (time.time() - start) * 1000

        return BenchmarkResult(
            pattern=f"{pattern.value}_multi",
            request_rate=request_rate,
            total_requests=stats.total_requests,
            completed=stats.completed_requests,
            row_hit_rate=stats.row_hit_rate,
            avg_latency=stats.avg_latency,
            max_latency=stats.max_latency_cycles,
            min_latency=stats.min_latency_cycles,
            throughput_gbps=stats.throughput_gbps,
            bandwidth_efficiency=stats.bandwidth_efficiency,
            wall_clock_time_ms=elapsed_ms,
            dram_activations=stats.total_dram_activations,
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

    def run_unified_suite(
        self,
        patterns: Optional[List[TrafficPattern]] = None,
        rates: Optional[List[float]] = None,
        time_us: float = 100.0,
        seed: int = 42,
        num_masters: int = 4,
    ) -> List[BenchmarkResult]:
        """运行统一仿真器基准测试套件

        Args:
            patterns: 要测试的流量模式
            rates: 请求率列表
            time_us: 仿真时间
            seed: 随机种子
            num_masters: AXI master 数量

        Returns:
            所有测试结果
        """
        if patterns is None:
            patterns = [TrafficPattern.RANDOM, TrafficPattern.SEQUENTIAL]

        if rates is None:
            rates = [0.3, 0.5, 0.8]

        for pattern in patterns:
            for rate in rates:
                logger.info(f"Running unified {pattern.value} @ rate={rate}...")
                result = self.run_unified_single(
                    pattern, rate,
                    time_us=time_us,
                    seed=seed,
                    num_masters=num_masters,
                )
                self.results.append(result)

        return self.results

    def run_stress_test(
        self,
        duration_us: float = 500.0,
        seed: int = 42,
    ) -> BenchmarkResult:
        """运行压力测试 (最大请求率)

        Args:
            duration_us: 仿真时间
            seed: 随机种子

        Returns:
            压力测试结果
        """
        logger.info("Running stress test (max request rate)...")
        return self.run_single(
            TrafficPattern.RANDOM,
            request_rate=1.0,
            time_us=duration_us,
            seed=seed,
            read_ratio=0.7,
        )

    def calculate_metrics(self, result: BenchmarkResult) -> PerformanceMetrics:
        """计算详细性能指标

        Args:
            result: 基准测试结果

        Returns:
            性能指标
        """
        cycles_per_req = (
            result.completed / result.total_requests
            if result.total_requests > 0 and result.completed > 0
            else 0.0
        )

        return PerformanceMetrics(
            cycles_per_request=cycles_per_req,
            requests_per_cycle=result.completed / (result.total_requests + 1e-9),
            row_open_ratio=result.row_hit_rate,
            read_write_ratio=result.read_ratio if hasattr(result, 'read_ratio') else 0.7,
            theoretical_bandwidth_gbps=819.2 * 2,  # HBM3 2-stack peak
            actual_bandwidth_gbps=result.throughput_gbps,
        )

    def print_results(self, stream: Optional[TextIO] = None):
        """打印结果表格

        Args:
            stream: 输出流 (默认 stdout)
        """
        if stream is None:
            stream = __import__('sys').stdout

        print("\n" + "=" * 100, file=stream)
        print(f"{'Pattern':<12} {'Rate':>5} {'Reqs':>7} {'Completed':>10} "
              f"{'Hit%':>7} {'Avg Lat':>8} {'Max Lat':>8} "
              f"{'TPut GB/s':>10} {'Eff%':>6} {'BW Eff%':>8} {'Time(ms)':>9}",
              file=stream)
        print("-" * 100, file=stream)

        for r in self.results:
            print(f"{r.pattern:<12} {r.request_rate:>5.2f} {r.total_requests:>7} "
                  f"{r.completed:>10} {r.row_hit_rate:>7.1%} "
                  f"{r.avg_latency:>8.1f} {r.max_latency:>8.1f} "
                  f"{r.throughput_gbps:>10.2f} {r.efficiency:>6.1%} "
                  f"{r.bandwidth_efficiency:>8.2%} {r.wall_clock_time_ms:>9.1f}",
                  file=stream)

        print("=" * 100, file=stream)

        # Summary statistics
        if self.results:
            total_completed = sum(r.completed for r in self.results)
            avg_hit_rate = statistics.mean(r.row_hit_rate for r in self.results)
            avg_throughput = statistics.mean(r.throughput_gbps for r in self.results)
            avg_latency = statistics.mean(r.avg_latency for r in self.results)

            print(f"\nSummary:", file=stream)
            print(f"  Total completed requests: {total_completed}", file=stream)
            print(f"  Average row hit rate: {avg_hit_rate:.2%}", file=stream)
            print(f"  Average throughput: {avg_throughput:.2f} GB/s", file=stream)
            print(f"  Average latency: {avg_latency:.1f} cycles", file=stream)

    def save_results(self, filename: str = "benchmark_results.json"):
        """保存结果到 JSON 文件

        Args:
            filename: 输出文件名
        """
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
                "max_latency": r.max_latency,
                "min_latency": r.min_latency,
                "throughput_gbps": r.throughput_gbps,
                "bandwidth_efficiency": r.bandwidth_efficiency,
                "wall_clock_time_ms": r.wall_clock_time_ms,
                "efficiency": r.efficiency,
                "dram_activations": r.dram_activations,
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

    # 基础测试套件
    print("\n--- Basic Benchmark Suite ---")
    bench.run_suite(time_us=100.0, seed=42, read_ratio=0.7)
    bench.print_results()
    bench.save_results()

    # 压力测试
    print("\n--- Stress Test (Max Rate) ---")
    stress_result = bench.run_stress_test(duration_us=200.0, seed=42)
    print(f"  Completed: {stress_result.completed}")
    print(f"  Throughput: {stress_result.throughput_gbps:.2f} GB/s")
    print(f"  Bandwidth efficiency: {stress_result.bandwidth_efficiency:.2%}")
    print(f"  Efficiency: {stress_result.efficiency:.2%}")

    # 统一仿真器测试 (可选)
    print("\n--- Unified Simulator Suite (AXI Interconnect) ---")
    bench.run_unified_suite(
        patterns=[TrafficPattern.RANDOM, TrafficPattern.SEQUENTIAL],
        rates=[0.3, 0.5],
        time_us=50.0,
        seed=42,
        num_masters=4,
    )
    bench.print_results()

    # 生成报告
    try:
        from sim.report_generator import generate_html_report, ReportData

        # 创建报告数据
        report = ReportData(
            simulation_name="HBM Performance Benchmark",
            simulation_time_us=100.0,
            total_requests=sum(r.total_requests for r in bench.results),
            completed_requests=sum(r.completed for r in bench.results),
            throughput_gbps=sum(r.throughput_gbps for r in bench.results) / max(len(bench.results), 1),
            avg_latency_cycles=sum(r.avg_latency for r in bench.results) / max(len(bench.results), 1),
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