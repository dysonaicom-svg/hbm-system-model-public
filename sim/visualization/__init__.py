"""
HBM Performance Visualization Module

Provides visualization and reporting capabilities for HBM simulation data.
Supports multiple output formats: HTML reports, ASCII terminal output, and JSON.
"""

from sim.visualization.bandwidth_chart import (
    BandwidthChart,
    BandwidthData,
    generate_bandwidth_bar_chart,
    generate_bandwidth_time_series,
    generate_bandwidth_efficiency_gauge,
)
from sim.visualization.latency_histogram import (
    LatencyHistogram,
    LatencyData,
    generate_latency_histogram,
    generate_percentile_markers,
    generate_latency_time_series,
)
from sim.visualization.channel_heatmap import (
    ChannelHeatmap,
    ChannelHeatmapData,
    generate_channel_heatmap,
    generate_bank_group_heatmap,
    generate_request_density_chart,
)
from sim.visualization.report_generator import (
    ReportGenerator,
    ReportData,
    VisualizationConfig,
    OutputFormat,
    generate_html_report,
    generate_ascii_report,
    generate_json_report,
)
from sim.visualization.advanced_charts import (
    AdvancedVisualizer,
    PerformanceAnalyzer,
    VisualizationData,
    ASCIIRenderer,
    ChartConfig,
    ChartType,
    create_visualizer,
    analyze_and_visualize,
)
from sim.visualization.performance_dashboard import (
    PerformanceDashboard,
    DashboardMetrics,
)
from sim.visualization.thermal_heatmap import ThermalHeatmap

__all__ = [
    # Bandwidth charts
    'BandwidthChart',
    'BandwidthData',
    'generate_bandwidth_bar_chart',
    'generate_bandwidth_time_series',
    'generate_bandwidth_efficiency_gauge',
    # Latency histogram
    'LatencyHistogram',
    'LatencyData',
    'generate_latency_histogram',
    'generate_percentile_markers',
    'generate_latency_time_series',
    # Channel heatmap
    'ChannelHeatmap',
    'ChannelHeatmapData',
    'generate_channel_heatmap',
    'generate_bank_group_heatmap',
    'generate_request_density_chart',
    # Report generator
    'ReportGenerator',
    'ReportData',
    'VisualizationConfig',
    'OutputFormat',
    'generate_html_report',
    'generate_ascii_report',
    'generate_json_report',
    # Advanced visualization
    'AdvancedVisualizer',
    'PerformanceAnalyzer',
    'VisualizationData',
    'ASCIIRenderer',
    'ChartConfig',
    'ChartType',
    'create_visualizer',
    'analyze_and_visualize',
    # Phase 16: Performance Dashboard
    'PerformanceDashboard',
    'DashboardMetrics',
    # Phase 16: Thermal Heatmap
    'ThermalHeatmap',
]