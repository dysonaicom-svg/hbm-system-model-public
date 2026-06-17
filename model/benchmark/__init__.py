"""
HBM Performance Benchmark Suite

This package provides comprehensive performance benchmarking for HBM memory controllers.

Modules:
- benchmark_config: Configuration and test parameters
- bandwidth_benchmark: Bandwidth tests (peak, sustained, refresh overhead)
- latency_benchmark: Latency tests (average, P99, distribution)
- scheduler_benchmark: Scheduler efficiency tests (QoS, row hit, bank conflicts)
- comparison_benchmark: HBM4 vs HBM3 comparison
- benchmark_runner: Main runner that orchestrates all tests
- enhanced_benchmark: Advanced tests (multi-channel, mixed traffic, BG conflicts, etc.)

Usage:
    from model.benchmark import BenchmarkRunner

    runner = BenchmarkRunner()
    report = runner.run_all_benchmarks()
    print(report)
"""

from .benchmark_runner import BenchmarkRunner, BenchmarkReport
from .benchmark_config import (
    BenchmarkConfig,
    BandwidthConfig,
    LatencyConfig,
    SchedulerConfig,
    ComparisonConfig,
)
from .bandwidth_benchmark import BandwidthBenchmark
from .latency_benchmark import LatencyBenchmark
from .scheduler_benchmark import SchedulerBenchmark
from .comparison_benchmark import ComparisonBenchmark
from .enhanced_benchmark import (
    EnhancedBenchmark,
    EnhancedBenchmarkReport,
    MultiChannelResult,
    MixedTrafficResult,
    BankGroupConflictResult,
    RefreshImpactResult,
    QoSImpactResult,
    run_enhanced_benchmark,
    run_multi_channel_benchmark,
    run_mixed_traffic_benchmark,
    run_bank_group_benchmark,
    run_refresh_benchmark,
    run_qos_benchmark,
)

__all__ = [
    # Original exports
    'BenchmarkRunner',
    'BenchmarkReport',
    'BenchmarkConfig',
    'BandwidthConfig',
    'LatencyConfig',
    'SchedulerConfig',
    'ComparisonConfig',
    'BandwidthBenchmark',
    'LatencyBenchmark',
    'SchedulerBenchmark',
    'ComparisonBenchmark',
    # Enhanced benchmark exports
    'EnhancedBenchmark',
    'EnhancedBenchmarkReport',
    'MultiChannelResult',
    'MixedTrafficResult',
    'BankGroupConflictResult',
    'RefreshImpactResult',
    'QoSImpactResult',
    'run_enhanced_benchmark',
    'run_multi_channel_benchmark',
    'run_mixed_traffic_benchmark',
    'run_bank_group_benchmark',
    'run_refresh_benchmark',
    'run_qos_benchmark',
]