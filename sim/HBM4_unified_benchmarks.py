"""
HBM4 Unified Simulator Benchmark Scenarios

综合基准测试，涵盖 HBM4 所有新组件:
- PAM3 信号编码/解码
- Logic Base Die 操作
- 独立通道时序
- DFI 5.0 接口
- 功耗
"""

import time
import statistics
from typing import List, Dict, Callable, Any

from sim.HBM4_unified_simulator import (
    HBM4UnifiedSimulator,
    SimulationConfig,
    SimulationMode,
)


class BenchmarkSuite:
    """HBM4 统一仿真器基准测试套件"""

    def __init__(self):
        self.results: Dict[str, List[float]] = {}

    def run_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 100
    ) -> Dict[str, Any]:
        """运行基准测试并收集时间统计"""
        timings = []

        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            timings.append(end - start)

        self.results[name] = timings

        return {
            'name': name,
            'iterations': iterations,
            'mean_ms': statistics.mean(timings) * 1000,
            'std_ms': statistics.stdev(timings) * 1000 if len(timings) > 1 else 0,
            'min_ms': min(timings) * 1000,
            'max_ms': max(timings) * 1000,
            'ops_per_sec': iterations / sum(timings) if sum(timings) > 0 else 0,
        }

    def print_results(self):
        """打印基准测试结果"""
        print("\n" + "=" * 70)
        print("HBM4 UNIFIED SIMULATOR BENCHMARK RESULTS")
        print("=" * 70)

        for name, timings in self.results.items():
            mean = statistics.mean(timings) * 1000
            std = statistics.stdev(timings) * 1000 if len(timings) > 1 else 0
            ops = len(timings) / sum(timings) if sum(timings) > 0 else 0

            print(f"\n{name}:")
            print(f"  Mean:   {mean:.4f} ms")
            print(f"  Std:    {std:.4f} ms")
            print(f"  Min:    {min(timings)*1000:.4f} ms")
            print(f"  Max:    {max(timings)*1000:.4f} ms")
            print(f"  Ops/s:  {ops:.0f}")


# 基准测试函数

def benchmark_pam3_encoding():
    """基准测试 PAM3 编码性能"""
    config = SimulationConfig(
        mode=SimulationMode.BENCHMARK,
        num_channels=32,
        cycles=100
    )
    sim = HBM4UnifiedSimulator(config)
    sim.initialize()

    for _ in range(1000):
        sim.process_pam3_sequence(0xDEADBEEF)


def benchmark_channel_operations():
    """基准测试通道操作"""
    config = SimulationConfig(
        mode=SimulationMode.BENCHMARK,
        num_channels=32,
        cycles=100
    )
    sim = HBM4UnifiedSimulator(config)
    sim.initialize()

    for ch in range(32):
        sim.process_command(ch, 'ACT', address=0x1000 + ch)


def benchmark_full_simulation():
    """基准测试完整仿真"""
    config = SimulationConfig(
        mode=SimulationMode.FULL,
        num_channels=32,
        cycles=1000
    )
    sim = HBM4UnifiedSimulator(config)
    sim.run()


def benchmark_independent_timing():
    """基准测试独立通道时序"""
    config = SimulationConfig(
        mode=SimulationMode.BENCHMARK,
        num_channels=32,
        cycles=100
    )
    sim = HBM4UnifiedSimulator(config)
    sim.initialize()

    for _ in range(100):
        sim.timing_manager.tick()


def benchmark_dfi_interface():
    """基准测试 DFI 接口"""
    config = SimulationConfig(
        mode=SimulationMode.BENCHMARK,
        num_channels=32,
        cycles=100
    )
    sim = HBM4UnifiedSimulator(config)
    sim.initialize()

    # 测试 DFI 命令
    for _ in range(100):
        sim.dfi.send_command(channel=0, command=DFICommand.ACT, address=0x1000)


def benchmark_all() -> Dict[str, Any]:
    """运行所有基准测试"""
    suite = BenchmarkSuite()

    benchmarks = [
        ("PAM3 Encoding (1000 ops)", benchmark_pam3_encoding, 10),
        ("Channel Operations (32 channels)", benchmark_channel_operations, 10),
        ("Independent Timing (100 ticks)", benchmark_independent_timing, 10),
        ("DFI Interface (100 commands)", benchmark_dfi_interface, 10),
        ("Full Simulation (1000 cycles)", benchmark_full_simulation, 5),
    ]

    results = []
    for name, func, iterations in benchmarks:
        print(f"Running: {name}...")
        result = suite.run_benchmark(name, func, iterations)
        results.append(result)
        print(f"  Done: {result['ops_per_sec']:.0f} ops/s")

    suite.print_results()

    return {r['name']: r for r in results}


def benchmark_scaling() -> Dict[str, Any]:
    """测试不同通道数量的扩展性"""
    print("\n" + "=" * 70)
    print("CHANNEL SCALING BENCHMARK")
    print("=" * 70)

    channel_counts = [8, 16, 32]
    scaling_results = []

    for num_channels in channel_counts:
        config = SimulationConfig(
            mode=SimulationMode.BENCHMARK,
            num_channels=num_channels,
            cycles=100
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        start = time.perf_counter()
        for ch in range(num_channels):
            sim.process_command(ch, 'ACT', address=0x1000 + ch)
        for _ in range(100):
            sim.tick()
        elapsed = time.time() - start

        print(f"  {num_channels} channels: {elapsed*1000:.2f} ms")
        scaling_results.append({
            'channels': num_channels,
            'time_ms': elapsed * 1000,
        })

    return {'scaling': scaling_results}


def benchmark_speed_grades() -> Dict[str, Any]:
    """测试不同速度等级的性能"""
    print("\n" + "=" * 70)
    print("SPEED GRADE BENCHMARK")
    print("=" * 70)

    speed_grades = ['8Gbps', '12Gbps', '16Gbps']
    grade_results = []

    for grade in speed_grades:
        config = SimulationConfig(
            mode=SimulationMode.QUICK,
            num_channels=32,
            cycles=100,
            speed_grade=grade
        )
        sim = HBM4UnifiedSimulator(config)

        start = time.perf_counter()
        sim.run()
        elapsed = time.time() - start

        print(f"  {grade}: {elapsed*1000:.2f} ms")
        grade_results.append({
            'speed_grade': grade,
            'time_ms': elapsed * 1000,
            'stats': sim.get_stats(),
        })

    return {'speed_grades': grade_results}


if __name__ == '__main__':
    print("HBM4 Unified Simulator Benchmarks")
    print("=" * 70)

    # 运行所有基准测试
    results = benchmark_all()

    # 运行扩展性测试
    scaling = benchmark_scaling()

    # 运行速度等级测试
    grades = benchmark_speed_grades()

    print("\n" + "=" * 70)
    print("All benchmarks completed!")
    print("=" * 70)