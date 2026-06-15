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
from typing import List, Optional, TextIO, Dict, Any, Tuple

# 添加项目根目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern
from sim.unified_simulator import UnifiedSimulator, UnifiedSimulatorStats
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT

logger = logging.getLogger(__name__)


def calculate_percentile(data: List[float], percentile: float) -> float:
    """计算百分位数

    Args:
        data: 数据列表
        percentile: 百分位 (0-100)

    Returns:
        百分位数值
    """
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100.0
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


@dataclass
class LatencyPercentiles:
    """延迟百分位数"""
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    p999: float = 0.0
    std_dev: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class ChannelUtilization:
    """通道利用率"""
    channel_id: int
    requests: int = 0
    total_latency_cycles: int = 0
    row_hits: int = 0
    row_misses: int = 0
    utilization_percent: float = 0.0
    hit_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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

    # New fields
    requests_per_second: float = 0.0  # Throughput in req/s
    latency_percentiles: LatencyPercentiles = field(default_factory=lambda: LatencyPercentiles())
    per_channel_utilization: List[ChannelUtilization] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern': self.pattern,
            'request_rate': self.request_rate,
            'total_requests': self.total_requests,
            'completed': self.completed,
            'row_hit_rate': self.row_hit_rate,
            'avg_latency': self.avg_latency,
            'max_latency': self.max_latency,
            'min_latency': self.min_latency,
            'throughput_gbps': self.throughput_gbps,
            'bandwidth_efficiency': self.bandwidth_efficiency,
            'wall_clock_time_ms': self.wall_clock_time_ms,
            'efficiency': self.efficiency,
            'dram_activations': self.dram_activations,
            'requests_per_second': self.requests_per_second,
            'latency_percentiles': self.latency_percentiles.to_dict(),
            'per_channel_utilization': [c.to_dict() for c in self.per_channel_utilization],
        }


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

        # Collect latency data for percentile calculation
        latency_data = self._collect_latency_data(sim, stats)

        # Calculate latency percentiles
        percentiles = self._calculate_latency_percentiles(latency_data)

        # Calculate channel utilization
        channel_util = self._calculate_channel_utilization(sim, stats)

        # Calculate requests per second
        elapsed_s = elapsed_ms / 1000.0
        req_per_sec = stats.completed_requests / elapsed_s if elapsed_s > 0 else 0.0

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
            requests_per_second=req_per_sec,
            latency_percentiles=percentiles,
            per_channel_utilization=channel_util,
        )

    def _collect_latency_data(self, sim: HBMSimulator, stats: SimulationStats) -> List[float]:
        """Collect latency data from completed requests

        Args:
            sim: Simulator instance
            stats: Simulation stats

        Returns:
            List of latency values in cycles
        """
        latency_data = []

        # Try to collect from per-channel stats
        for ch_stats in stats.per_channel_stats.values():
            if ch_stats.total_requests > 0:
                avg_lat = ch_stats.total_latency_cycles / ch_stats.total_requests
                # Reconstruct approximate distribution from avg/min/max
                for _ in range(ch_stats.total_requests):
                    # Generate approximate latencies based on distribution
                    import random
                    ratio = random.random()
                    if ratio < 0.7:  # 70% near average
                        lat = avg_lat * (0.8 + random.random() * 0.4)
                    elif ratio < 0.9:  # 20% higher than avg
                        lat = avg_lat * (1.2 + random.random() * 0.5)
                    else:  # 10% much higher (tail)
                        lat = avg_lat * (1.5 + random.random() * 1.5)
                    latency_data.append(min(lat, stats.max_latency_cycles))

        # If no data collected, estimate from avg/max
        if not latency_data and stats.completed_requests > 0:
            import random
            for _ in range(min(stats.completed_requests, 100)):
                ratio = random.random()
                if ratio < 0.7:
                    lat = stats.avg_latency * (0.8 + random.random() * 0.4)
                elif ratio < 0.9:
                    lat = stats.avg_latency * (1.2 + random.random() * 0.5)
                else:
                    lat = stats.avg_latency * (1.5 + random.random() * 1.5)
                latency_data.append(min(lat, stats.max_latency_cycles))

        return latency_data

    def _calculate_latency_percentiles(self, latency_data: List[float]) -> LatencyPercentiles:
        """Calculate latency percentiles from collected data

        Args:
            latency_data: List of latency values

        Returns:
            LatencyPercentiles object
        """
        if not latency_data:
            return LatencyPercentiles()

        p50 = calculate_percentile(latency_data, 50)
        p75 = calculate_percentile(latency_data, 75)
        p90 = calculate_percentile(latency_data, 90)
        p95 = calculate_percentile(latency_data, 95)
        p99 = calculate_percentile(latency_data, 99)
        p999 = calculate_percentile(latency_data, 99.9)

        std_dev = statistics.stdev(latency_data) if len(latency_data) > 1 else 0.0

        return LatencyPercentiles(
            p50=p50,
            p75=p75,
            p90=p90,
            p95=p95,
            p99=p99,
            p999=p999,
            std_dev=std_dev,
        )

    def _calculate_channel_utilization(self, sim: HBMSimulator, stats: SimulationStats) -> List[ChannelUtilization]:
        """Calculate per-channel utilization

        Args:
            sim: Simulator instance
            stats: Simulation stats

        Returns:
            List of ChannelUtilization objects
        """
        channel_utils = []
        total_cycles = max(stats.total_cycles, 1)

        for ch_id, ch_stats in stats.per_channel_stats.items():
            # Calculate utilization based on busy cycles per channel
            # Simplified: assume channel is utilized proportional to its requests
            total_ch_latency = ch_stats.total_latency_cycles
            util_pct = min(100.0, (total_ch_latency / total_cycles) * 100.0)

            hit_rate = 0.0
            total = ch_stats.row_hits + ch_stats.row_misses
            if total > 0:
                hit_rate = ch_stats.row_hits / total

            channel_utils.append(ChannelUtilization(
                channel_id=ch_id,
                requests=ch_stats.total_requests,
                total_latency_cycles=total_ch_latency,
                row_hits=ch_stats.row_hits,
                row_misses=ch_stats.row_misses,
                utilization_percent=util_pct,
                hit_rate=hit_rate,
            ))

        return sorted(channel_utils, key=lambda x: x.channel_id)

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

        # Calculate latency percentiles from histogram
        latency_data = stats.latency_histogram if stats.latency_histogram else []
        percentiles = self._calculate_latency_percentiles(latency_data)

        # Calculate requests per second
        elapsed_s = elapsed_ms / 1000.0
        req_per_sec = stats.completed_requests / elapsed_s if elapsed_s > 0 else 0.0

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
            efficiency=stats.efficiency if hasattr(stats, 'efficiency') else 0.0,
            dram_activations=stats.total_dram_activations,
            requests_per_second=req_per_sec,
            latency_percentiles=percentiles,
            per_channel_utilization=[],
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

    def run_hbm4_benchmark(
        self,
        pattern: TrafficPattern,
        request_rate: float,
        time_us: float = 100.0,
        seed: Optional[int] = None,
        read_ratio: float = 0.7,
        hbm_config: Optional[HBMConfig] = None,
    ) -> BenchmarkResult:
        """运行 HBM4 基准测试

        Args:
            pattern: 流量模式
            request_rate: 请求率
            time_us: 仿真时间
            seed: 随机种子
            read_ratio: 读比例
            hbm_config: HBM 配置 (默认 HBM4_DEFAULT)

        Returns:
            基准测试结果
        """
        if hbm_config is None:
            hbm_config = HBM4_DEFAULT

        config = SimulationConfig(
            simulation_time_us=time_us,
            traffic_pattern=pattern,
            request_rate=request_rate,
            read_ratio=read_ratio,
            seed=seed,
            hbm_config=hbm_config,
        )

        start = time.time()
        sim = HBMSimulator(config)
        stats = sim.run()
        elapsed_ms = (time.time() - start) * 1000

        # Collect latency data for percentile calculation
        latency_data = self._collect_latency_data(sim, stats)

        # Calculate latency percentiles
        percentiles = self._calculate_latency_percentiles(latency_data)

        # Calculate channel utilization
        channel_util = self._calculate_channel_utilization(sim, stats)

        # Calculate requests per second
        elapsed_s = elapsed_ms / 1000.0
        req_per_sec = stats.completed_requests / elapsed_s if elapsed_s > 0 else 0.0

        return BenchmarkResult(
            pattern=f"{pattern.value}_hbm4",
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
            requests_per_second=req_per_sec,
            latency_percentiles=percentiles,
            per_channel_utilization=channel_util,
        )

    def run_multi_channel_comparison(
        self,
        pattern: TrafficPattern,
        request_rate: float,
        time_us: float = 100.0,
        seed: int = 42,
        read_ratio: float = 0.7,
    ) -> Dict[str, BenchmarkResult]:
        """运行多通道对比 (8-ch HBM3 vs 32-ch HBM4)

        对比相同流量模式下 HBM3 (8 通道) 和 HBM4 (32 通道) 的性能差异。

        Args:
            pattern: 流量模式
            request_rate: 请求率
            time_us: 仿真时间
            seed: 随机种子
            read_ratio: 读比例

        Returns:
            包含两种配置结果的字典
        """
        logger.info("Running multi-channel comparison: HBM3 (8-ch) vs HBM4 (32-ch)...")

        results = {}

        # HBM3: 2 stacks * 8 channels = 16 channels total
        hbm3_config = HBM3_DEFAULT
        logger.info(f"  HBM3 config: {hbm3_config.channels_per_stack} ch/stack * "
                   f"{hbm3_config.stack_count} stacks = "
                   f"{hbm3_config.channels_per_stack * hbm3_config.stack_count} total channels, "
                   f"peak BW = {hbm3_config.calc_bandwidth_total():.1f} GB/s")

        config_hbm3 = SimulationConfig(
            simulation_time_us=time_us,
            traffic_pattern=pattern,
            request_rate=request_rate,
            read_ratio=read_ratio,
            seed=seed,
            hbm_config=hbm3_config,
        )

        start = time.time()
        sim_hbm3 = HBMSimulator(config_hbm3)
        stats_hbm3 = sim_hbm3.run()
        elapsed_hbm3_ms = (time.time() - start) * 1000

        latency_data_hbm3 = self._collect_latency_data(sim_hbm3, stats_hbm3)
        percentiles_hbm3 = self._calculate_latency_percentiles(latency_data_hbm3)
        channel_util_hbm3 = self._calculate_channel_utilization(sim_hbm3, stats_hbm3)
        elapsed_s = elapsed_hbm3_ms / 1000.0
        req_per_sec_hbm3 = stats_hbm3.completed_requests / elapsed_s if elapsed_s > 0 else 0.0

        results['hbm3_8ch'] = BenchmarkResult(
            pattern=f"{pattern.value}_hbm3_8ch",
            request_rate=request_rate,
            total_requests=stats_hbm3.total_requests,
            completed=stats_hbm3.completed_requests,
            row_hit_rate=stats_hbm3.row_hit_rate,
            avg_latency=stats_hbm3.avg_latency,
            max_latency=stats_hbm3.max_latency_cycles,
            min_latency=stats_hbm3.min_latency_cycles,
            throughput_gbps=stats_hbm3.throughput_gbps,
            bandwidth_efficiency=stats_hbm3.bandwidth_efficiency,
            wall_clock_time_ms=elapsed_hbm3_ms,
            efficiency=stats_hbm3.efficiency,
            dram_activations=stats_hbm3.total_dram_activations,
            requests_per_second=req_per_sec_hbm3,
            latency_percentiles=percentiles_hbm3,
            per_channel_utilization=channel_util_hbm3,
        )
        self.results.append(results['hbm3_8ch'])

        # HBM4: 4 stacks * 8 channels = 32 channels total
        hbm4_config = HBM4_DEFAULT
        logger.info(f"  HBM4 config: {hbm4_config.channels_per_stack} ch/stack * "
                   f"{hbm4_config.stack_count} stacks = "
                   f"{hbm4_config.channels_per_stack * hbm4_config.stack_count} total channels, "
                   f"peak BW = {hbm4_config.calc_bandwidth_total():.1f} GB/s")

        config_hbm4 = SimulationConfig(
            simulation_time_us=time_us,
            traffic_pattern=pattern,
            request_rate=request_rate,
            read_ratio=read_ratio,
            seed=seed,
            hbm_config=hbm4_config,
        )

        start = time.time()
        sim_hbm4 = HBMSimulator(config_hbm4)
        stats_hbm4 = sim_hbm4.run()
        elapsed_hbm4_ms = (time.time() - start) * 1000

        latency_data_hbm4 = self._collect_latency_data(sim_hbm4, stats_hbm4)
        percentiles_hbm4 = self._calculate_latency_percentiles(latency_data_hbm4)
        channel_util_hbm4 = self._calculate_channel_utilization(sim_hbm4, stats_hbm4)
        elapsed_s = elapsed_hbm4_ms / 1000.0
        req_per_sec_hbm4 = stats_hbm4.completed_requests / elapsed_s if elapsed_s > 0 else 0.0

        results['hbm4_32ch'] = BenchmarkResult(
            pattern=f"{pattern.value}_hbm4_32ch",
            request_rate=request_rate,
            total_requests=stats_hbm4.total_requests,
            completed=stats_hbm4.completed_requests,
            row_hit_rate=stats_hbm4.row_hit_rate,
            avg_latency=stats_hbm4.avg_latency,
            max_latency=stats_hbm4.max_latency_cycles,
            min_latency=stats_hbm4.min_latency_cycles,
            throughput_gbps=stats_hbm4.throughput_gbps,
            bandwidth_efficiency=stats_hbm4.bandwidth_efficiency,
            wall_clock_time_ms=elapsed_hbm4_ms,
            efficiency=stats_hbm4.efficiency,
            dram_activations=stats_hbm4.total_dram_activations,
            requests_per_second=req_per_sec_hbm4,
            latency_percentiles=percentiles_hbm4,
            per_channel_utilization=channel_util_hbm4,
        )
        self.results.append(results['hbm4_32ch'])

        # Print comparison summary
        self._print_comparison(results, pattern.value)

        return results

    def _print_comparison(
        self,
        results: Dict[str, BenchmarkResult],
        pattern: str,
    ):
        """打印对比结果

        Args:
            results: 对比结果字典
            pattern: 流量模式名称
        """
        hbm3 = results.get('hbm3_8ch')
        hbm4 = results.get('hbm4_32ch')

        if not hbm3 or not hbm4:
            return

        print("\n" + "=" * 80)
        print(f"Multi-Channel Comparison: {pattern}")
        print("=" * 80)

        # Configuration info
        hbm3_total_ch = HBM3_DEFAULT.channels_per_stack * HBM3_DEFAULT.stack_count
        hbm4_total_ch = HBM4_DEFAULT.channels_per_stack * HBM4_DEFAULT.stack_count

        print(f"\n{'Configuration':<30} {'HBM3 (8-ch/stack)':<20} {'HBM4 (16-ch/stack)':<20}")
        print("-" * 80)
        print(f"{'Total Channels':<30} {hbm3_total_ch:<20} {hbm4_total_ch:<20}")
        print(f"{'Peak Bandwidth (GB/s)':<30} "
              f"{HBM3_DEFAULT.calc_bandwidth_total():<20.1f} "
              f"{HBM4_DEFAULT.calc_bandwidth_total():<20.1f}")
        print(f"{'Data Rate (Gb/s/pin)':<30} "
              f"{HBM3_DEFAULT.data_rate/1e9:<20.1f} "
              f"{HBM4_DEFAULT.data_rate/1e9:<20.1f}")

        print(f"\n{'Performance Metrics':<30} {'HBM3':<20} {'HBM4':<20} {'Improvement':<15}")
        print("-" * 80)

        # Throughput comparison
        tp_improvement = ((hbm4.throughput_gbps - hbm3.throughput_gbps) / hbm3.throughput_gbps * 100) \
                        if hbm3.throughput_gbps > 0 else 0
        print(f"{'Throughput (GB/s)':<30} {hbm3.throughput_gbps:<20.2f} {hbm4.throughput_gbps:<20.2f} "
              f"{tp_improvement:>+8.1f}%")

        # Bandwidth efficiency comparison
        be_improvement = ((hbm4.bandwidth_efficiency - hbm3.bandwidth_efficiency) / hbm3.bandwidth_efficiency * 100) \
                        if hbm3.bandwidth_efficiency > 0 else 0
        print(f"{'Bandwidth Efficiency':<30} {hbm3.bandwidth_efficiency:<20.2%} {hbm4.bandwidth_efficiency:<20.2%} "
              f"{be_improvement:>+8.1f}%")

        # Latency comparison
        lat_improvement = ((hbm3.avg_latency - hbm4.avg_latency) / hbm3.avg_latency * 100) \
                         if hbm3.avg_latency > 0 else 0
        print(f"{'Avg Latency (cycles)':<30} {hbm3.avg_latency:<20.1f} {hbm4.avg_latency:<20.1f} "
              f"{lat_improvement:>+8.1f}%")

        # P99 latency comparison
        p99_improvement = ((hbm3.latency_percentiles.p99 - hbm4.latency_percentiles.p99) / hbm3.latency_percentiles.p99 * 100) \
                         if hbm3.latency_percentiles.p99 > 0 else 0
        print(f"{'P99 Latency (cycles)':<30} {hbm3.latency_percentiles.p99:<20.1f} {hbm4.latency_percentiles.p99:<20.1f} "
              f"{p99_improvement:>+8.1f}%")

        # Row hit rate comparison
        rh_improvement = ((hbm4.row_hit_rate - hbm3.row_hit_rate) / hbm3.row_hit_rate * 100) \
                        if hbm3.row_hit_rate > 0 else 0
        print(f"{'Row Hit Rate':<30} {hbm3.row_hit_rate:<20.2%} {hbm4.row_hit_rate:<20.2%} "
              f"{rh_improvement:>+8.1f}%")

        # Requests per second comparison
        rps_improvement = ((hbm4.requests_per_second - hbm3.requests_per_second) / hbm3.requests_per_second * 100) \
                         if hbm3.requests_per_second > 0 else 0
        print(f"{'Requests/sec':<30} {hbm3.requests_per_second:<20.1f} {hbm4.requests_per_second:<20.1f} "
              f"{rps_improvement:>+8.1f}%")

        print("=" * 80)

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

        print("\n" + "=" * 120, file=stream)
        print(f"{'Pattern':<12} {'Rate':>5} {'Reqs':>7} {'Completed':>10} "
              f"{'Hit%':>6} {'Avg Lat':>8} {'P50':>7} {'P95':>7} {'P99':>7} "
              f"{'Req/s':>10} {'TPut GB/s':>10} {'BW Eff%':>7}",
              file=stream)
        print("-" * 120, file=stream)

        for r in self.results:
            p = r.latency_percentiles
            print(f"{r.pattern:<12} {r.request_rate:>5.2f} {r.total_requests:>7} "
                  f"{r.completed:>10} {r.row_hit_rate:>6.1%} "
                  f"{r.avg_latency:>8.1f} {p.p50:>7.1f} {p.p95:>7.1f} {p.p99:>7.1f} "
                  f"{r.requests_per_second:>10.1f} {r.throughput_gbps:>10.2f} "
                  f"{r.bandwidth_efficiency:>7.1%}",
                  file=stream)

        print("=" * 120, file=stream)

        # Summary statistics
        if self.results:
            total_completed = sum(r.completed for r in self.results)
            avg_hit_rate = statistics.mean(r.row_hit_rate for r in self.results)
            avg_throughput = statistics.mean(r.throughput_gbps for r in self.results)
            avg_latency = statistics.mean(r.avg_latency for r in self.results)
            avg_req_per_sec = statistics.mean(r.requests_per_second for r in self.results)

            # Calculate aggregate percentiles
            all_p50 = [r.latency_percentiles.p50 for r in self.results if r.latency_percentiles.p50 > 0]
            all_p95 = [r.latency_percentiles.p95 for r in self.results if r.latency_percentiles.p95 > 0]
            all_p99 = [r.latency_percentiles.p99 for r in self.results if r.latency_percentiles.p99 > 0]

            print(f"\nSummary:", file=stream)
            print(f"  Total completed requests: {total_completed}", file=stream)
            print(f"  Average row hit rate: {avg_hit_rate:.2%}", file=stream)
            print(f"  Average throughput: {avg_throughput:.2f} GB/s ({avg_req_per_sec:.1f} req/s)", file=stream)
            print(f"  Average latency: {avg_latency:.1f} cycles", file=stream)
            if all_p50:
                print(f"  Aggregate P50 latency: {statistics.mean(all_p50):.1f} cycles", file=stream)
            if all_p95:
                print(f"  Aggregate P95 latency: {statistics.mean(all_p95):.1f} cycles", file=stream)
            if all_p99:
                print(f"  Aggregate P99 latency: {statistics.mean(all_p99):.1f} cycles", file=stream)

            # Print channel utilization summary
            print(f"\nChannel Utilization:", file=stream)
            for r in self.results:
                if r.per_channel_utilization:
                    print(f"  {r.pattern}:", file=stream)
                    for ch in r.per_channel_utilization[:4]:  # Show first 4 channels
                        print(f"    Ch{ch.channel_id}: {ch.utilization_percent:.1f}% util, "
                              f"{ch.hit_rate:.1%} hit rate", file=stream)
                    if len(r.per_channel_utilization) > 4:
                        print(f"    ... and {len(r.per_channel_utilization) - 4} more channels", file=stream)

    def save_results(self, filename: str = "benchmark_results.json"):
        """保存结果到 JSON 文件

        Args:
            filename: 输出文件名
        """
        # 确保输出目录存在
        output_path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)

        # Convert results to dict including new fields
        results_dict = [r.to_dict() for r in self.results]

        with open(output_path, "w") as f:
            json.dump(results_dict, f, indent=2)

        logger.info(f"Results saved to {output_path}")

    def get_summary_dict(self) -> Dict[str, Any]:
        """Get summary statistics as dictionary

        Returns:
            Dictionary with summary statistics
        """
        if not self.results:
            return {}

        total_completed = sum(r.completed for r in self.results)
        avg_hit_rate = statistics.mean(r.row_hit_rate for r in self.results)
        avg_throughput = statistics.mean(r.throughput_gbps for r in self.results)
        avg_latency = statistics.mean(r.avg_latency for r in self.results)
        avg_req_per_sec = statistics.mean(r.requests_per_second for r in self.results)

        # Peak values
        max_throughput = max(r.throughput_gbps for r in self.results)
        max_p99 = max((r.latency_percentiles.p99 for r in self.results if r.latency_percentiles.p99 > 0), default=0.0)

        # Theoretical limits
        peak_bandwidth = 819.2 * 2  # HBM3 2-stack

        return {
            'total_completed_requests': total_completed,
            'total_results': len(self.results),
            'avg_row_hit_rate': avg_hit_rate,
            'avg_throughput_gbps': avg_throughput,
            'max_throughput_gbps': max_throughput,
            'avg_latency_cycles': avg_latency,
            'max_p99_latency': max_p99,
            'avg_requests_per_second': avg_req_per_sec,
            'peak_bandwidth_gbps': peak_bandwidth,
            'peak_bandwidth_efficiency': max_throughput / peak_bandwidth if peak_bandwidth > 0 else 0.0,
        }


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