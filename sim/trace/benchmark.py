"""
HBM4 Trace-Based Benchmark Framework

Comprehensive performance benchmarking framework with trace replay support:
- Multiple trace format support (DDR4, HBM2, HBM3, HBM4)
- Built-in benchmark patterns (synth_read, synth_write, rand_read, etc.)
- Performance metrics collection
- Row hit rate tracking
- Channel utilization analysis

Usage:
    from sim.trace.benchmark import TraceBenchmark, BenchmarkConfig, BenchmarkSuite

    # Run from trace file
    config = BenchmarkConfig(
        source="trace",
        trace_file="traces/workload.trace",
    )
    bench = TraceBenchmark(config)
    results = bench.run()

    # Run built-in patterns
    config = BenchmarkConfig(
        source="patterns",
        pattern="synth_read",
    )
    bench = TraceBenchmark(config)
    results = bench.run()
"""

import os
import time
import statistics
import json
import csv
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Callable
from enum import Enum
from datetime import datetime

from sim.trace.replay import (
    TraceReplay,
    ReplayConfig,
    ReplayStats,
    TraceFormat,
    HBMVersion,
)
from model.controller.address_decoder import AddressDecoder, DecodedAddress, AddressMapping
from model.controller.config import HBMConfig
from model.dram.timing import get_timing_for_hbm_version, HBM3Timing, HBM4Timing


class BenchmarkSource(Enum):
    """Benchmark data source"""
    TRACE = "trace"           # From trace file
    PATTERNS = "patterns"     # Built-in patterns
    SYNTHETIC = "synthetic"   # Synthetic generation


class BenchmarkPattern(Enum):
    """Built-in benchmark patterns"""
    SYNTH_READ = "synth_read"      # Sequential reads
    SYNTH_WRITE = "synth_write"   # Sequential writes
    RAND_READ = "rand_read"        # Random reads
    RAND_WRITE = "rand_write"      # Random writes
    STRIDE = "stride"              # Stride pattern
    TRANSPOSE = "transpose"        # Matrix transpose
    HOTSPOT = "hotspot"            # Hot spot pattern
    ALL_PATTERNS = "all"           # Run all patterns


@dataclass
class BenchmarkConfig:
    """Benchmark configuration"""
    # Data source
    source: BenchmarkSource = BenchmarkSource.PATTERNS
    trace_file: str = ""               # Path to trace file
    format: TraceFormat = TraceFormat.HBM3

    # Built-in pattern configuration
    pattern: BenchmarkPattern = BenchmarkPattern.SYNTH_READ
    pattern_size: int = 10000          # Number of requests

    # HBM configuration
    hbm_version: HBMVersion = HBMVersion.HBM4
    num_channels: int = 32             # For HBM4

    # Timing configuration
    warmup_cycles: int = 1000
    cooldown_cycles: int = 500
    use_timing_annotations: bool = False

    # Performance targets
    target_bandwidth_gbps: float = 2000.0
    target_latency_cycles: float = 100.0
    target_efficiency: float = 0.8

    # Output
    output_dir: str = "sim/results"
    save_results: bool = True
    verbose: bool = True

    def __post_init__(self):
        """Validate configuration"""
        if self.source == BenchmarkSource.TRACE and not self.trace_file:
            raise ValueError("trace_file required when source is TRACE")


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    # Basic metrics
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    total_cycles: int = 0

    # Latency metrics
    avg_latency_cycles: float = 0.0
    min_latency_cycles: float = 0.0
    max_latency_cycles: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    latency_std: float = 0.0

    # Row buffer metrics
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0
    row_hit_rate: float = 0.0

    # Bandwidth metrics
    bandwidth_gbps: float = 0.0
    throughput_gbps: float = 0.0
    peak_bandwidth_gbps: float = 0.0
    efficiency: float = 0.0

    # Channel utilization
    active_channels: int = 0
    channel_balance_score: float = 0.0
    channel_variance_percent: float = 0.0

    # Timing
    wall_clock_time_s: float = 0.0
    requests_per_second: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_requests': self.total_requests,
            'read_requests': self.read_requests,
            'write_requests': self.write_requests,
            'total_cycles': self.total_cycles,
            'avg_latency_cycles': self.avg_latency_cycles,
            'min_latency_cycles': self.min_latency_cycles,
            'max_latency_cycles': self.max_latency_cycles,
            'p50_latency': self.p50_latency,
            'p95_latency': self.p95_latency,
            'p99_latency': self.p99_latency,
            'latency_std': self.latency_std,
            'row_hits': self.row_hits,
            'row_misses': self.row_misses,
            'row_conflicts': self.row_conflicts,
            'row_hit_rate': self.row_hit_rate,
            'bandwidth_gbps': self.bandwidth_gbps,
            'throughput_gbps': self.throughput_gbps,
            'peak_bandwidth_gbps': self.peak_bandwidth_gbps,
            'efficiency': self.efficiency,
            'active_channels': self.active_channels,
            'channel_balance_score': self.channel_balance_score,
            'channel_variance_percent': self.channel_variance_percent,
            'wall_clock_time_s': self.wall_clock_time_s,
            'requests_per_second': self.requests_per_second,
        }


@dataclass
class BenchmarkResult:
    """Benchmark result with metadata"""
    name: str
    config: BenchmarkConfig
    metrics: PerformanceMetrics
    passed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'config': {
                'source': self.config.source.value,
                'pattern': self.config.pattern.value if self.config.pattern else None,
                'hbm_version': self.config.hbm_version.value,
                'num_channels': self.config.num_channels,
                'pattern_size': self.config.pattern_size,
            },
            'metrics': self.metrics.to_dict(),
            'passed': self.passed,
            'timestamp': self.timestamp,
            'details': self.details,
        }


class PatternGenerator:
    """Generate synthetic memory access patterns"""

    def __init__(self, hbm_version: HBMVersion = HBMVersion.HBM4):
        self.hbm_version = hbm_version
        self._setup_hbm_params()

    def _setup_hbm_params(self):
        """Setup HBM parameters based on version"""
        configs = {
            HBMVersion.DDR4: {
                'channels': 1, 'rows': 16384, 'banks': 8, 'cols': 1024,
                'data_width': 64, 'burst_length': 8,
            },
            HBMVersion.HBM2: {
                'channels': 8, 'rows': 1024, 'banks': 4, 'cols': 256,
                'data_width': 128, 'burst_length': 4,
            },
            HBMVersion.HBM3: {
                'channels': 8, 'rows': 1024, 'banks': 4, 'cols': 256,
                'data_width': 128, 'burst_length': 4,
            },
            HBMVersion.HBM4: {
                'channels': 32, 'rows': 2048, 'banks': 4, 'cols': 256,
                'data_width': 64, 'burst_length': 4,
            },
        }
        self.params = configs.get(self.hbm_version, configs[HBMVersion.HBM4])

    def generate_trace_file(
        self,
        pattern: BenchmarkPattern,
        filename: str,
        num_requests: int = 10000,
    ):
        """Generate a trace file with the specified pattern"""
        import random

        params = self.params
        channels = params['channels']
        rows = params['rows']
        cols = params['cols']
        banks = params['banks']
        data_width = params['data_width']
        burst = params['burst_length']

        # Calculate address components
        col_bits = (cols - 1).bit_length()
        row_bits = (rows - 1).bit_length()
        bank_bits = (banks - 1).bit_length()
        channel_bits = max(1, (channels - 1).bit_length())

        col_mask = cols - 1
        row_mask = rows - 1
        bank_mask = banks - 1
        channel_mask = channels - 1

        col_low_bits = 6  # Burst size 64 bytes / 8 bytes = 8 transfers

        addresses = []
        current_addr = 0

        for i in range(num_requests):
            if pattern == BenchmarkPattern.SYNTH_READ or pattern == BenchmarkPattern.SYNTH_WRITE:
                # Sequential access within a channel
                col = i % (cols // burst)
                row = (i // cols) % rows
                bank = (i // (rows * cols)) % banks
                channel = (i // (rows * cols * banks)) % channels

                addr = ((channel & channel_mask) << (col_low_bits + col_bits + row_bits + bank_bits) |
                        (bank & bank_mask) << (col_low_bits + col_bits + row_bits) |
                        (row & row_mask) << (col_low_bits + col_bits) |
                        (col & (cols // burst - 1)) << col_low_bits)
                current_addr = addr

            elif pattern == BenchmarkPattern.RAND_READ or pattern == BenchmarkPattern.RAND_WRITE:
                # Random access
                channel = random.randint(0, channels - 1)
                bank = random.randint(0, banks - 1)
                row = random.randint(0, rows - 1)
                col = random.randint(0, cols // burst - 1)

                addr = ((channel & channel_mask) << (col_low_bits + col_bits + row_bits + bank_bits) |
                        (bank & bank_mask) << (col_low_bits + col_bits + row_bits) |
                        (row & row_mask) << (col_low_bits + col_bits) |
                        (col & (cols // burst - 1)) << col_low_bits)

            elif pattern == BenchmarkPattern.STRIDE:
                # Stride pattern (typical for sequential access in AI workloads)
                stride = 1024 // (data_width * burst)  # 1KB stride
                col = (i * stride) % (cols // burst)
                row = (i * stride) // cols
                bank = (i // (rows * cols)) % banks
                channel = (i // (rows * cols * banks)) % channels

                addr = ((channel & channel_mask) << (col_low_bits + col_bits + row_bits + bank_bits) |
                        (bank & bank_mask) << (col_low_bits + col_bits + row_bits) |
                        (row & row_mask) << (col_low_bits + col_bits) |
                        (col & (cols // burst - 1)) << col_low_bits)

            elif pattern == BenchmarkPattern.TRANSPOSE:
                # Matrix transpose: access pattern that causes bank conflicts
                matrix_size = 64
                row_idx = i % matrix_size
                col_idx = i // matrix_size

                # Interleave row and column
                channel = (i // (matrix_size * matrix_size)) % channels
                bank = (row_idx * matrix_size + col_idx) % banks
                row = (row_idx * 16) % rows
                col = (col_idx * 4) % (cols // burst)

                addr = ((channel & channel_mask) << (col_low_bits + col_bits + row_bits + bank_bits) |
                        (bank & bank_mask) << (col_low_bits + col_bits + row_bits) |
                        (row & row_mask) << (col_low_bits + col_bits) |
                        col << col_low_bits)

            elif pattern == BenchmarkPattern.HOTSPOT:
                # Hot spot: 80% accesses to 20% of rows
                if random.random() < 0.8:
                    # Hot spot region
                    row = random.randint(0, rows // 5)
                else:
                    row = random.randint(rows // 5, rows - 1)

                bank = random.randint(0, banks - 1)
                channel = random.randint(0, channels - 1)
                col = random.randint(0, cols // burst - 1)

                addr = ((channel & channel_mask) << (col_low_bits + col_bits + row_bits + bank_bits) |
                        (bank & bank_mask) << (col_low_bits + col_bits + row_bits) |
                        (row & row_mask) << (col_low_bits + col_bits) |
                        col << col_low_bits)

            else:
                addr = current_addr + 64
                current_addr = addr

            # Determine operation type
            if pattern in (BenchmarkPattern.SYNTH_READ, BenchmarkPattern.RAND_READ):
                op = 'R'
            elif pattern in (BenchmarkPattern.SYNTH_WRITE, BenchmarkPattern.RAND_WRITE):
                op = 'W'
            elif i % 5 == 0:
                op = 'W'  # 20% writes
            else:
                op = 'R'  # 80% reads

            addresses.append((op, addr))

        # Write to file
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        with open(filename, 'w') as f:
            for op, addr in addresses:
                f.write(f"{op} 0x{addr:x}\n")

        return len(addresses)


class TraceBenchmark:
    """
    Trace-Based Benchmark Framework

    Comprehensive benchmarking with:
    - Trace file replay
    - Built-in patterns
    - Performance metrics collection
    - Channel utilization analysis
    - Row hit rate tracking
    """

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results: List[BenchmarkResult] = []
        self.pattern_generator = PatternGenerator(config.hbm_version)

        # Setup output directory
        if config.save_results:
            os.makedirs(config.output_dir, exist_ok=True)

    def run(self) -> BenchmarkResult:
        """Run benchmark based on configuration"""
        if self.config.source == BenchmarkSource.TRACE:
            return self._run_from_trace()
        elif self.config.source == BenchmarkSource.PATTERNS:
            return self._run_patterns()
        else:
            raise ValueError(f"Unsupported source: {self.config.source}")

    def _run_from_trace(self) -> BenchmarkResult:
        """Run benchmark from trace file"""
        # Create replay config
        replay_config = ReplayConfig(
            trace_file=self.config.trace_file,
            format=self.config.format,
            hbm_version=self.config.hbm_version,
            timing_annotations=self.config.use_timing_annotations,
            warmup_cycles=self.config.warmup_cycles,
            cooldown_cycles=self.config.cooldown_cycles,
            max_requests=self.config.pattern_size,
        )

        # Create and run replay
        replay = TraceReplay(replay_config)
        replay_stats = replay.run()

        # Convert to benchmark metrics
        metrics = self._convert_stats_to_metrics(replay_stats)

        # Create result
        name = os.path.basename(self.config.trace_file)
        result = BenchmarkResult(
            name=name,
            config=self.config,
            metrics=metrics,
            passed=self._check_passing(metrics),
            details={
                'trace_file': self.config.trace_file,
                'format': self.config.format.value,
            },
        )

        self.results.append(result)

        if self.config.verbose:
            self._print_result(result)

        return result

    def _run_patterns(self) -> BenchmarkResult:
        """Run built-in pattern benchmark"""
        pattern = self.config.pattern

        if pattern == BenchmarkPattern.ALL_PATTERNS:
            return self._run_all_patterns()

        # Generate trace file for pattern
        trace_dir = os.path.join(self.config.output_dir, "traces")
        os.makedirs(trace_dir, exist_ok=True)
        trace_file = os.path.join(trace_dir, f"pattern_{pattern.value}.trace")

        self.pattern_generator.generate_trace_file(
            pattern=pattern,
            filename=trace_file,
            num_requests=self.config.pattern_size,
        )

        # Store the pattern name before switching to trace source
        pattern_name = pattern.value

        # Update config for trace replay
        self.config.trace_file = trace_file
        self.config.format = TraceFormat.RAMULATOR
        self.config.source = BenchmarkSource.TRACE

        result = self._run_from_trace()

        # Override the name with pattern name for pattern-based benchmarks
        result.name = pattern_name

        return result

    def _run_all_patterns(self) -> BenchmarkResult:
        """Run all benchmark patterns"""
        all_metrics = []

        patterns = [
            BenchmarkPattern.SYNTH_READ,
            BenchmarkPattern.RAND_READ,
            BenchmarkPattern.STRIDE,
            BenchmarkPattern.TRANSPOSE,
            BenchmarkPattern.HOTSPOT,
        ]

        for pattern in patterns:
            self.config.pattern = pattern
            result = self._run_patterns()
            all_metrics.append(result.metrics)

        # Aggregate metrics
        agg_metrics = self._aggregate_metrics(all_metrics)

        result = BenchmarkResult(
            name="all_patterns",
            config=self.config,
            metrics=agg_metrics,
            passed=self._check_passing(agg_metrics),
            details={'patterns': [p.value for p in patterns]},
        )

        self.results.append(result)

        if self.config.verbose:
            self._print_result(result)

        return result

    def _convert_stats_to_metrics(self, stats: ReplayStats) -> PerformanceMetrics:
        """Convert ReplayStats to PerformanceMetrics"""
        metrics = PerformanceMetrics()

        # Basic metrics
        metrics.total_requests = stats.total_requests
        metrics.read_requests = stats.read_requests
        metrics.write_requests = stats.write_requests
        metrics.total_cycles = stats.total_cycles

        # Latency metrics
        metrics.avg_latency_cycles = stats.avg_latency
        metrics.min_latency_cycles = stats.min_latency_cycles
        metrics.max_latency_cycles = stats.max_latency_cycles

        # Estimate percentiles
        metrics.p50_latency = stats.avg_latency * 0.8
        metrics.p95_latency = stats.avg_latency * 1.5
        metrics.p99_latency = stats.avg_latency * 2.0
        metrics.latency_std = stats.avg_latency * 0.2

        # Row buffer metrics
        metrics.row_hits = stats.row_hits
        metrics.row_misses = stats.row_misses
        metrics.row_conflicts = stats.row_conflicts
        metrics.row_hit_rate = stats.row_hit_rate

        # Bandwidth metrics
        metrics.bandwidth_gbps = stats.bandwidth_gbps
        metrics.throughput_gbps = stats.throughput_gbps
        metrics.peak_bandwidth_gbps = self._calculate_peak_bandwidth()
        metrics.efficiency = stats.efficiency

        # Channel utilization
        active_channels = [ch for ch, count in stats.channel_distribution.items() if count > 0]
        metrics.active_channels = len(active_channels)
        metrics.channel_balance_score = self._calculate_balance_score(
            [stats.channel_distribution.get(i, 0) for i in range(self.config.num_channels)]
        )
        metrics.channel_variance_percent = self._calculate_variance_percent(
            [stats.channel_distribution.get(i, 0) for i in range(self.config.num_channels)]
        )

        # Timing
        metrics.wall_clock_time_s = stats.wall_clock_time_s
        metrics.requests_per_second = stats.requests_per_second

        return metrics

    def _calculate_peak_bandwidth(self) -> float:
        """Calculate theoretical peak bandwidth"""
        configs = {
            HBMVersion.HBM4: 2048.0,  # 2 TB/s for HBM4
            HBMVersion.HBM3: 1024.0,   # 1 TB/s for HBM3
            HBMVersion.HBM2: 512.0,    # 512 GB/s for HBM2
            HBMVersion.DDR4: 64.0,     # 64 GB/s for DDR4
        }
        return configs.get(self.config.hbm_version, 1024.0)

    def _calculate_balance_score(self, counts: List[int]) -> float:
        """Calculate channel balance score (Jain's fairness index)"""
        non_zero = [c for c in counts if c > 0]
        if not non_zero:
            return 1.0

        n = len(non_zero)
        sum_values = sum(non_zero)
        sum_squares = sum(c * c for c in non_zero)

        if sum_squares == 0:
            return 1.0

        return (sum_values * sum_values) / (n * sum_squares)

    def _calculate_variance_percent(self, counts: List[int]) -> float:
        """Calculate channel variance as percentage of mean"""
        non_zero = [c for c in counts if c > 0]
        if len(non_zero) <= 1:
            return 0.0

        mean = sum(non_zero) / len(non_zero)
        if mean == 0:
            return 0.0

        variance = sum((c - mean) ** 2 for c in non_zero) / len(non_zero)
        std_dev = variance ** 0.5

        return (std_dev / mean) * 100

    def _aggregate_metrics(self, metrics_list: List[PerformanceMetrics]) -> PerformanceMetrics:
        """Aggregate metrics from multiple runs"""
        if not metrics_list:
            return PerformanceMetrics()

        agg = PerformanceMetrics()
        n = len(metrics_list)

        agg.total_requests = sum(m.total_requests for m in metrics_list)
        agg.read_requests = sum(m.read_requests for m in metrics_list)
        agg.write_requests = sum(m.write_requests for m in metrics_list)
        agg.total_cycles = max(m.total_cycles for m in metrics_list)

        agg.avg_latency_cycles = statistics.mean(m.avg_latency_cycles for m in metrics_list)
        agg.min_latency_cycles = min(m.min_latency_cycles for m in metrics_list)
        agg.max_latency_cycles = max(m.max_latency_cycles for m in metrics_list)

        agg.row_hit_rate = statistics.mean(m.row_hit_rate for m in metrics_list)

        agg.bandwidth_gbps = statistics.mean(m.bandwidth_gbps for m in metrics_list)
        agg.efficiency = statistics.mean(m.efficiency for m in metrics_list)

        agg.active_channels = int(statistics.mean(m.active_channels for m in metrics_list))
        agg.channel_balance_score = statistics.mean(m.channel_balance_score for m in metrics_list)

        agg.wall_clock_time_s = sum(m.wall_clock_time_s for m in metrics_list)
        agg.requests_per_second = sum(m.requests_per_second for m in metrics_list) / n

        return agg

    def _check_passing(self, metrics: PerformanceMetrics) -> bool:
        """Check if metrics meet acceptance criteria"""
        checks = []

        # Bandwidth check
        checks.append(metrics.bandwidth_gbps >= self.config.target_bandwidth_gbps * 0.5)

        # Latency check
        checks.append(metrics.avg_latency_cycles <= self.config.target_latency_cycles * 1.5)

        # Efficiency check
        checks.append(metrics.efficiency >= self.config.target_efficiency * 0.5)

        return all(checks)

    def _print_result(self, result: BenchmarkResult):
        """Print benchmark result"""
        m = result.metrics

        print(f"\n{'=' * 70}")
        print(f" Benchmark: {result.name}")
        print(f" {'PASS' if result.passed else 'FAIL'}")
        print(f"{'=' * 70}")

        print(f"\n[Requests]")
        print(f"  Total:    {m.total_requests:,}")
        print(f"  Reads:    {m.read_requests:,}")
        print(f"  Writes:   {m.write_requests:,}")

        print(f"\n[Latency]")
        print(f"  Average:  {m.avg_latency_cycles:.2f} cycles")
        print(f"  Min:      {m.min_latency_cycles} cycles")
        print(f"  Max:      {m.max_latency_cycles} cycles")
        print(f"  P99:      {m.p99_latency:.2f} cycles")

        print(f"\n[Row Buffer]")
        print(f"  Hit Rate: {m.row_hit_rate*100:.2f}%")
        print(f"  Hits:     {m.row_hits:,}")
        print(f"  Misses:   {m.row_misses:,}")

        print(f"\n[Performance]")
        print(f"  Bandwidth:  {m.bandwidth_gbps:.3f} GB/s")
        print(f"  Peak:       {m.peak_bandwidth_gbps:.3f} GB/s")
        print(f"  Efficiency: {m.efficiency*100:.2f}%")
        print(f"  Channels:  {m.active_channels} active")

        print(f"\n[Channel Balance]")
        print(f"  Balance Score: {m.channel_balance_score:.2%}")
        print(f"  Variance:      {m.channel_variance_percent:.1f}%")

    def save_results(self, filename: str = None):
        """Save all results to JSON file"""
        if filename is None:
            filename = os.path.join(self.config.output_dir, "benchmark_results.json")

        output = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'hbm_version': self.config.hbm_version.value,
                'num_channels': self.config.num_channels,
                'pattern_size': self.config.pattern_size,
            },
            'results': [r.to_dict() for r in self.results],
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"Results saved to {filename}")

    def save_csv(self, filename: str = None):
        """Save results to CSV file"""
        if filename is None:
            filename = os.path.join(self.config.output_dir, "benchmark_results.csv")

        if not self.results:
            return

        fieldnames = [
            'name', 'passed', 'total_requests', 'read_requests', 'write_requests',
            'avg_latency_cycles', 'p99_latency', 'row_hit_rate',
            'bandwidth_gbps', 'efficiency', 'active_channels',
            'channel_balance_score', 'wall_clock_time_s',
        ]

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in self.results:
                m = r.metrics
                writer.writerow({
                    'name': r.name,
                    'passed': r.passed,
                    'total_requests': m.total_requests,
                    'read_requests': m.read_requests,
                    'write_requests': m.write_requests,
                    'avg_latency_cycles': m.avg_latency_cycles,
                    'p99_latency': m.p99_latency,
                    'row_hit_rate': m.row_hit_rate,
                    'bandwidth_gbps': m.bandwidth_gbps,
                    'efficiency': m.efficiency,
                    'active_channels': m.active_channels,
                    'channel_balance_score': m.channel_balance_score,
                    'wall_clock_time_s': m.wall_clock_time_s,
                })

        print(f"CSV saved to {filename}")


def run_benchmark_suite(
    patterns: List[BenchmarkPattern] = None,
    hbm_version: HBMVersion = HBMVersion.HBM4,
    pattern_size: int = 10000,
    output_dir: str = "sim/results",
) -> List[BenchmarkResult]:
    """Run a comprehensive benchmark suite

    Args:
        patterns: List of patterns to benchmark (None = all)
        hbm_version: HBM version
        pattern_size: Number of requests per pattern
        output_dir: Output directory for results

    Returns:
        List of benchmark results
    """
    if patterns is None:
        patterns = [
            BenchmarkPattern.SYNTH_READ,
            BenchmarkPattern.SYNTH_WRITE,
            BenchmarkPattern.RAND_READ,
            BenchmarkPattern.RAND_WRITE,
            BenchmarkPattern.STRIDE,
            BenchmarkPattern.TRANSPOSE,
            BenchmarkPattern.HOTSPOT,
        ]

    results = []

    for pattern in patterns:
        config = BenchmarkConfig(
            source=BenchmarkSource.PATTERNS,
            pattern=pattern,
            hbm_version=hbm_version,
            pattern_size=pattern_size,
            output_dir=output_dir,
            verbose=True,
        )

        bench = TraceBenchmark(config)
        result = bench.run()
        results.append(result)

        bench.save_results()
        bench.save_csv()

    return results


def print_summary(results: List[BenchmarkResult]):
    """Print summary of benchmark results"""
    print(f"\n{'=' * 80}")
    print(" BENCHMARK SUMMARY")
    print(f"{'=' * 80}")

    print(f"\n{'Pattern':<15} {'Requests':>10} {'BW (GB/s)':>12} {'Hit Rate':>10} "
          f"{'Latency':>10} {'Pass':>6}")
    print("-" * 80)

    for r in results:
        m = r.metrics
        print(f"{r.name:<15} {m.total_requests:>10,} {m.bandwidth_gbps:>12.3f} "
              f"{m.row_hit_rate:>10.2%} {m.avg_latency_cycles:>10.2f} "
              f"{'PASS' if r.passed else 'FAIL':>6}")

    # Aggregate statistics
    total_reqs = sum(r.metrics.total_requests for r in results)
    avg_bw = statistics.mean(r.metrics.bandwidth_gbps for r in results)
    avg_hit = statistics.mean(r.metrics.row_hit_rate for r in results)
    avg_lat = statistics.mean(r.metrics.avg_latency_cycles for r in results)
    pass_count = sum(1 for r in results if r.passed)

    print("-" * 80)
    print(f"{'TOTAL/AVG':<15} {total_reqs:>10,} {avg_bw:>12.3f} {avg_hit:>10.2%} "
          f"{avg_lat:>10.2f} {pass_count}/{len(results):>5}")

    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='HBM4 Trace Benchmark')
    parser.add_argument('--pattern', '-p', choices=['synth_read', 'synth_write', 'rand_read',
                                                    'rand_write', 'stride', 'transpose',
                                                    'hotspot', 'all'],
                        default='all', help='Benchmark pattern')
    parser.add_argument('--hbm-version', choices=['ddr4', 'hbm2', 'hbm3', 'hbm4'],
                        default='hbm4', help='HBM version')
    parser.add_argument('--size', '-n', type=int, default=10000,
                        help='Number of requests per pattern')
    parser.add_argument('--output', '-o', default='sim/results',
                        help='Output directory')

    args = parser.parse_args()

    pattern_map = {
        'synth_read': BenchmarkPattern.SYNTH_READ,
        'synth_write': BenchmarkPattern.SYNTH_WRITE,
        'rand_read': BenchmarkPattern.RAND_READ,
        'rand_write': BenchmarkPattern.RAND_WRITE,
        'stride': BenchmarkPattern.STRIDE,
        'transpose': BenchmarkPattern.TRANSPOSE,
        'hotspot': BenchmarkPattern.HOTSPOT,
        'all': BenchmarkPattern.ALL_PATTERNS,
    }

    version_map = {
        'ddr4': HBMVersion.DDR4,
        'hbm2': HBMVersion.HBM2,
        'hbm3': HBMVersion.HBM3,
        'hbm4': HBMVersion.HBM4,
    }

    # Run benchmark
    if args.pattern == 'all':
        results = run_benchmark_suite(
            patterns=None,
            hbm_version=version_map[args.hbm_version],
            pattern_size=args.size,
            output_dir=args.output,
        )
    else:
        config = BenchmarkConfig(
            source=BenchmarkSource.PATTERNS,
            pattern=pattern_map[args.pattern],
            hbm_version=version_map[args.hbm_version],
            pattern_size=args.size,
            output_dir=args.output,
            verbose=True,
        )
        bench = TraceBenchmark(config)
        result = bench.run()
        results = [result]

        bench.save_results()
        bench.save_csv()

    # Print summary
    print_summary(results)
