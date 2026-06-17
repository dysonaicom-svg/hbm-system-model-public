"""
HBM Trace Package

Provides trace parsing, replay, and benchmarking functionality:
- TraceParser: Parse and analyze trace files
- TraceReplay: Replay traces with cycle-accurate timing
- TraceBenchmark: Comprehensive performance benchmarking

Supported formats:
- DDR4, HBM2, HBM3, HBM4
- CSV, binary, memory dump
"""

from sim.trace.parser import (
    TraceParser,
    TraceConfig,
    TraceRequest,
    TraceStats,
    TraceFormat,
    HBMVersion as TraceHBMVersion,
    parse_trace_file,
    parse_directory,
    generate_summary_table,
)

from sim.trace.replay import (
    TraceReplay,
    ReplayConfig,
    ReplayStats,
    ReplayRequest,
    ChannelUtilization,
    TraceFormat as ReplayTraceFormat,
    HBMVersion as ReplayHBMVersion,
    replay_trace,
    create_sample_trace,
)

from sim.trace.benchmark import (
    TraceBenchmark,
    BenchmarkConfig,
    BenchmarkResult,
    PerformanceMetrics,
    BenchmarkSource,
    BenchmarkPattern,
    PatternGenerator,
    run_benchmark_suite,
    print_summary,
)

__all__ = [
    # Parser module
    "TraceParser",
    "TraceConfig",
    "TraceRequest",
    "TraceStats",
    "TraceFormat",
    "TraceHBMVersion",
    "parse_trace_file",
    "parse_directory",
    "generate_summary_table",

    # Replay module
    "TraceReplay",
    "ReplayConfig",
    "ReplayStats",
    "ReplayRequest",
    "ChannelUtilization",
    "ReplayTraceFormat",
    "ReplayHBMVersion",
    "replay_trace",
    "create_sample_trace",

    # Benchmark module
    "TraceBenchmark",
    "BenchmarkConfig",
    "BenchmarkResult",
    "PerformanceMetrics",
    "BenchmarkSource",
    "BenchmarkPattern",
    "PatternGenerator",
    "run_benchmark_suite",
    "print_summary",
]
