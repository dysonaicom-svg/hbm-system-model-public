"""
HBM Performance Monitoring Module

Provides real-time performance monitoring, latency analysis, and heatmap visualization
for HBM memory subsystem simulation.

Components:
- RealtimeMonitor: Real-time bandwidth and performance tracking
- LatencyAnalyzer: Comprehensive latency distribution analysis
- HeatmapGenerator: Channel/bank utilization heatmaps

Usage:
    from model.monitoring import RealtimeMonitor, LatencyAnalyzer, HeatmapGenerator

    # Real-time monitoring
    monitor = RealtimeMonitor(num_channels=32)
    monitor.start()
    # ... simulation ...
    stats = monitor.get_stats()

    # Latency analysis
    analyzer = LatencyAnalyzer(bin_size=5)
    analyzer.add_samples(latencies)
    report = analyzer.generate_report()

    # Heatmap visualization
    heatmap = HeatmapGenerator(num_channels=32)
    heatmap.record_request(channel=0, bank_group=2)
    print(heatmap.generate_ascii_heatmap())
"""

from model.monitoring.realtime_monitor import (
    RealtimeMonitor,
    ChannelMetrics,
    SystemMetrics,
    BandwidthTracker,
    create_monitor,
)
from model.monitoring.latency_analyzer import (
    LatencyAnalyzer,
    LatencyStats,
    LatencyHistogram,
    LatencyPattern,
    LatencyCategory,
    calculate_statistics,
    detect_outliers,
    categorize_latency,
    create_analyzer,
)
from model.monitoring.heatmap_generator import (
    HeatmapGenerator,
    ChannelActivity,
    BankGroupActivity,
    BankActivity,
    create_generator,
)

__all__ = [
    # Realtime monitoring
    'RealtimeMonitor',
    'ChannelMetrics',
    'SystemMetrics',
    'BandwidthTracker',
    'create_monitor',
    # Latency analysis
    'LatencyAnalyzer',
    'LatencyStats',
    'LatencyHistogram',
    'LatencyPattern',
    'LatencyCategory',
    'calculate_statistics',
    'detect_outliers',
    'categorize_latency',
    'create_analyzer',
    # Heatmap
    'HeatmapGenerator',
    'ChannelActivity',
    'BankGroupActivity',
    'BankActivity',
    'create_generator',
]

__version__ = '1.0.0'
