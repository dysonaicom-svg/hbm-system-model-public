"""HBM System Performance Benchmark
性能基准测试模块 - 分析不同流量模式下的吞吐量和延迟
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Optional
from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern


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
    simulation_time_ms: float


class HBMBenchmark:
    """HBM 性能基准测试器"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def run_single(
        self,
        pattern: TrafficPattern,
        request_rate: float,
        time_us: float = 100.0,
        seed: Optional[int] = None
    ) -> BenchmarkResult:
        """运行单个基准测试"""
        config = SimulationConfig(
            simulation_time_us=time_us,
            traffic_pattern=pattern,
            request_rate=request_rate,
            read_ratio=0.7,
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
            simulation_time_ms=elapsed_ms
        )

    def run_suite(self) -> List[BenchmarkResult]:
        """运行完整基准测试套件"""
        patterns = [
            TrafficPattern.RANDOM,
            TrafficPattern.SEQUENTIAL,
            TrafficPattern.STRIDE,
            TrafficPattern.HOT_SPOT,
        ]

        rates = [0.3, 0.5, 0.8, 1.0]

        for pattern in patterns:
            for rate in rates:
                print(f"Running {pattern.value} @ rate={rate}...")
                result = self.run_single(pattern, rate, time_us=100.0, seed=42)
                self.results.append(result)

        return self.results

    def print_results(self):
        """打印结果表格"""
        print("\n" + "=" * 90)
        print(f"{'Pattern':<15} {'Rate':>6} {'Reqs':>8} {'Completed':>10} "
              f"{'Hit%':>8} {'Latency':>10} {'TPut':>10} {'Time':>8}")
        print("-" * 90)

        for r in self.results:
            print(f"{r.pattern:<15} {r.request_rate:>6.2f} {r.total_requests:>8} "
                  f"{r.completed:>10} {r.row_hit_rate:>8.1%} {r.avg_latency:>10.1f} "
                  f"{r.throughput_gbps:>10.2f} {r.simulation_time_ms:>8.1f}")

        print("=" * 90)


def main():
    """运行基准测试"""
    print("=" * 60)
    print("HBM Performance Benchmark Suite")
    print("=" * 60)

    bench = HBMBenchmark()
    bench.run_suite()
    bench.print_results()

    # 保存结果
    import json
    results_dict = [
        {
            "pattern": r.pattern,
            "request_rate": r.request_rate,
            "total_requests": r.total_requests,
            "completed": r.completed,
            "row_hit_rate": r.row_hit_rate,
            "avg_latency": r.avg_latency,
            "throughput_gbps": r.throughput_gbps,
            "simulation_time_ms": r.simulation_time_ms
        }
        for r in bench.results
    ]

    with open("sim/benchmark_results.json", "w") as f:
        json.dump(results_dict, f, indent=2)

    print("\nResults saved to sim/benchmark_results.json")


if __name__ == "__main__":
    main()