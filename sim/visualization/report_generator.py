"""
Report Generator Module

Provides comprehensive report generation capabilities:
- HTML report generation
- ASCII terminal visualization
- JSON structured output
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum


class OutputFormat(Enum):
    """Output format enumeration"""
    HTML = "html"
    ASCII = "ascii"
    JSON = "json"


@dataclass
class VisualizationConfig:
    """Configuration for visualization output"""
    # Output settings
    output_format: OutputFormat = OutputFormat.HTML
    output_path: str = "sim/results/report.html"
    
    # Chart settings
    chart_width: int = 800
    chart_height: int = 400
    include_bandwidth: bool = True
    include_latency: bool = True
    include_heatmap: bool = True
    
    # Theme settings
    theme: str = "default"  # default, dark, minimal
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    
    # Performance thresholds
    bandwidth_threshold: float = 0.5  # 50% of peak = good
    latency_p99_threshold: float = 100.0  # cycles
    utilization_threshold: float = 0.7  # 70% = good
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            'output_format': self.output_format.value,
            'output_path': self.output_path,
            'chart_width': self.chart_width,
            'chart_height': self.chart_height,
            'include_bandwidth': self.include_bandwidth,
            'include_latency': self.include_latency,
            'include_heatmap': self.include_heatmap,
            'theme': self.theme,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
        }


@dataclass
class ReportData:
    """Complete report data container"""
    # Metadata
    simulation_name: str = "HBM Simulation"
    timestamp: str = ""
    simulation_time_us: float = 0.0
    total_cycles: int = 0
    
    # Request statistics
    total_requests: int = 0
    completed_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    
    # Performance metrics
    throughput_gbps: float = 0.0
    peak_bandwidth_gbps: float = 819.2
    bandwidth_efficiency: float = 0.0
    avg_latency_cycles: float = 0.0
    row_hit_rate: float = 0.0
    
    # Latency percentiles
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    
    # Per-channel data
    channel_bandwidth: Dict[int, float] = field(default_factory=dict)
    channel_utilization: Dict[int, float] = field(default_factory=dict)
    request_density: Dict[int, int] = field(default_factory=dict)
    
    # Bank group activity
    bank_group_activity: Dict[int, Dict[int, float]] = field(default_factory=dict)
    
    # Bandwidth time series
    bandwidth_time_series: Dict[int, float] = field(default_factory=dict)
    
    # Latency histogram
    latency_histogram: Dict[int, int] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            'metadata': {
                'simulation_name': self.simulation_name,
                'timestamp': self.timestamp,
                'simulation_time_us': self.simulation_time_us,
                'total_cycles': self.total_cycles,
            },
            'requests': {
                'total': self.total_requests,
                'completed': self.completed_requests,
                'read': self.read_requests,
                'write': self.write_requests,
            },
            'performance': {
                'throughput_gbps': self.throughput_gbps,
                'peak_bandwidth_gbps': self.peak_bandwidth_gbps,
                'bandwidth_efficiency': self.bandwidth_efficiency,
                'avg_latency_cycles': self.avg_latency_cycles,
                'row_hit_rate': self.row_hit_rate,
            },
            'latency_percentiles': {
                'p50': self.latency_p50,
                'p95': self.latency_p95,
                'p99': self.latency_p99,
            },
            'channel_data': {
                'bandwidth': self.channel_bandwidth,
                'utilization': self.channel_utilization,
                'request_density': self.request_density,
            },
            'bank_group_activity': self.bank_group_activity,
            'bandwidth_time_series': self.bandwidth_time_series,
            'latency_histogram': self.latency_histogram,
        }


class ReportGenerator:
    """Comprehensive report generator"""
    
    def __init__(self, config: VisualizationConfig = None):
        self.config = config or VisualizationConfig()
    
    def generate(self, data: ReportData) -> str:
        """Generate report based on configuration
        
        Args:
            data: Report data
            
        Returns:
            Generated report string
        """
        if self.config.output_format == OutputFormat.HTML:
            return self._generate_html(data)
        elif self.config.output_format == OutputFormat.ASCII:
            return self._generate_ascii(data)
        elif self.config.output_format == OutputFormat.JSON:
            return self._generate_json(data)
        else:
            raise ValueError(f"Unknown output format: {self.config.output_format}")
    
    def _generate_html(self, data: ReportData) -> str:
        """Generate HTML report"""
        chartjs_script = self._generate_chartjs_script(data)
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.simulation_name} - Performance Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{
            background: linear-gradient(135deg, {self.config.primary_color} 0%, {self.config.secondary_color} 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        header h1 {{ font-size: 2rem; margin-bottom: 10px; }}
        header .meta {{ opacity: 0.9; font-size: 0.9rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            color: {self.config.primary_color};
            margin-bottom: 15px;
            font-size: 1rem;
            border-bottom: 2px solid {self.config.primary_color};
            padding-bottom: 10px;
        }}
        .stat {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .stat:last-child {{ border-bottom: none; }}
        .stat-value {{ font-weight: 600; }}
        .stat-value.highlight {{ color: {self.config.primary_color}; font-size: 1.2rem; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .chart-wrapper {{ position: relative; height: {self.config.chart_height}px; }}
        .chart-title {{ color: {self.config.primary_color}; margin-bottom: 20px; font-size: 1.2rem; }}
        footer {{ text-align: center; padding: 20px; color: #666; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{data.simulation_name}</h1>
            <div class="meta">
                Generated: {data.timestamp} | 
                Simulation Time: {data.simulation_time_us:.1f} us | 
                Cycles: {data.total_cycles:,}
            </div>
        </header>

        <div class="grid">
            <div class="card">
                <h3>Request Statistics</h3>
                <div class="stat">
                    <span>Total Requests</span>
                    <span class="stat-value highlight">{data.total_requests:,}</span>
                </div>
                <div class="stat">
                    <span>Completed</span>
                    <span class="stat-value">{data.completed_requests:,}</span>
                </div>
                <div class="stat">
                    <span>Read / Write</span>
                    <span class="stat-value">{data.read_requests:,} / {data.write_requests:,}</span>
                </div>
                <div class="stat">
                    <span>Row Hit Rate</span>
                    <span class="stat-value badge badge-success">{data.row_hit_rate * 100:.1f}%</span>
                </div>
            </div>

            <div class="card">
                <h3>Performance Metrics</h3>
                <div class="stat">
                    <span>Throughput</span>
                    <span class="stat-value highlight">{data.throughput_gbps:.2f} GB/s</span>
                </div>
                <div class="stat">
                    <span>Peak Bandwidth</span>
                    <span class="stat-value">{data.peak_bandwidth_gbps:.2f} GB/s</span>
                </div>
                <div class="stat">
                    <span>Efficiency</span>
                    <span class="stat-value badge badge-{self._get_efficiency_badge(data.bandwidth_efficiency)}">{data.bandwidth_efficiency * 100:.1f}%</span>
                </div>
                <div class="stat">
                    <span>Avg Latency</span>
                    <span class="stat-value">{data.avg_latency_cycles:.1f} cycles</span>
                </div>
            </div>

            <div class="card">
                <h3>Latency Percentiles</h3>
                <div class="stat">
                    <span>P50</span>
                    <span class="stat-value">{data.latency_p50:.1f} cycles</span>
                </div>
                <div class="stat">
                    <span>P95</span>
                    <span class="stat-value">{data.latency_p95:.1f} cycles</span>
                </div>
                <div class="stat">
                    <span>P99</span>
                    <span class="stat-value badge badge-{self._get_latency_badge(data.latency_p99)}">{data.latency_p99:.1f} cycles</span>
                </div>
            </div>
        </div>
"""

    def _generate_chartjs_script(self, data: ReportData) -> str:
        """Generate Chart.js scripts for visualizations"""
        # Bandwidth bar chart data
        channel_labels = [f"CH{i}" for i in range(data.channel_bandwidth.get('num_channels', 8))]
        channel_values = [data.channel_bandwidth.get(i, 0.0) for i in range(len(channel_labels))]
        
        bandwidth_bar = {
            'type': 'bar',
            'data': {
                'labels': channel_labels,
                'datasets': [{
                    'label': 'Bandwidth (GB/s)',
                    'data': channel_values,
                    'backgroundColor': 'rgba(102, 126, 234, 0.8)',
                    'borderColor': 'rgba(102, 126, 234, 1)',
                    'borderWidth': 1,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}},
                'scales': {
                    'y': {'beginAtZero': True, 'title': {'display': True, 'text': 'Bandwidth (GB/s)'}},
                    'x': {'title': {'display': True, 'text': 'Channel'}}
                }
            }
        }
        
        # Latency histogram data
        sorted_bins = sorted(data.latency_histogram.items())
        latency_labels = [str(b[0]) for b in sorted_bins]
        latency_values = [b[1] for b in sorted_bins]
        
        latency_hist = {
            'type': 'bar',
            'data': {
                'labels': latency_labels,
                'datasets': [{
                    'label': 'Count',
                    'data': latency_values,
                    'backgroundColor': 'rgba(118, 75, 162, 0.8)',
                    'borderColor': 'rgba(118, 75, 162, 1)',
                    'borderWidth': 1,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}},
                'scales': {
                    'y': {'beginAtZero': True, 'title': {'display': True, 'text': 'Count'}},
                    'x': {'title': {'display': True, 'text': 'Latency (cycles)'}}
                }
            }
        }
        
        return f"""
    <script>
        const bwBarData = {json.dumps(bandwidth_bar)};
        const latHistData = {json.dumps(latency_hist)};
        
        // Bandwidth bar chart
        const bwBarCtx = document.getElementById('bwBarChart');
        if (bwBarCtx) {{ new Chart(bwBarCtx, bwBarData); }}
        
        // Latency histogram
        const latCtx = document.getElementById('latHistogram');
        if (latCtx) {{ new Chart(latCtx, latHistData); }}
    </script>
</body>
</html>
"""
    
    def _get_efficiency_badge(self, efficiency: float) -> str:
        """Get badge class for efficiency"""
        if efficiency >= 0.5:
            return "success"
        elif efficiency >= 0.3:
            return "warning"
        else:
            return "danger"
    
    def _get_latency_badge(self, latency: float) -> str:
        """Get badge class for latency"""
        if latency < 50:
            return "success"
        elif latency < 100:
            return "warning"
        else:
            return "danger"
    
    def _generate_ascii(self, data: ReportData) -> str:
        """Generate ASCII report for terminal"""
        lines = []
        width = 80
        
        # Header
        lines.append("=" * width)
        lines.append(f"HBM SIMULATION PERFORMANCE REPORT".center(width))
        lines.append(f"Generated: {data.timestamp}".center(width))
        lines.append("=" * width)
        
        # Summary section
        lines.append("\n" + "-" * width)
        lines.append("SIMULATION SUMMARY".center(width))
        lines.append("-" * width)
        lines.append(f"  Simulation Name: {data.simulation_name}")
        lines.append(f"  Simulation Time: {data.simulation_time_us:.1f} us ({data.total_cycles:,} cycles)")
        lines.append(f"  Total Requests: {data.total_requests:,} | Completed: {data.completed_requests:,}")
        lines.append(f"  Read/Write Ratio: {data.read_requests:,} / {data.write_requests:,}")
        
        # Performance section
        lines.append("\n" + "-" * width)
        lines.append("PERFORMANCE METRICS".center(width))
        lines.append("-" * width)
        lines.append(f"  Throughput: {data.throughput_gbps:.2f} GB/s")
        lines.append(f"  Peak Bandwidth: {data.peak_bandwidth_gbps:.2f} GB/s")
        lines.append(f"  Bandwidth Efficiency: {data.bandwidth_efficiency * 100:.1f}%")
        lines.append(f"  Average Latency: {data.avg_latency_cycles:.1f} cycles")
        lines.append(f"  Row Hit Rate: {data.row_hit_rate * 100:.1f}%")
        
        # Latency percentiles
        lines.append("\n" + "-" * width)
        lines.append("LATENCY PERCENTILES".center(width))
        lines.append("-" * width)
        lines.append(f"  P50: {data.latency_p50:.1f} cycles")
        lines.append(f"  P95: {data.latency_p95:.1f} cycles")
        lines.append(f"  P99: {data.latency_p99:.1f} cycles")
        
        # Channel utilization
        lines.append("\n" + "-" * width)
        lines.append("CHANNEL UTILIZATION".center(width))
        lines.append("-" * width)
        for ch in range(len(data.channel_utilization)):
            util = data.channel_utilization.get(ch, 0.0)
            bar_len = int(util * 40)
            bar = "█" * bar_len + "░" * (40 - bar_len)
            bw = data.channel_bandwidth.get(ch, 0.0)
            lines.append(f"  CH{ch}: {bar} {util*100:5.1f}% ({bw:.2f} GB/s)")
        
        # ASCII histogram
        lines.append("\n" + "-" * width)
        lines.append("LATENCY HISTOGRAM".center(width))
        lines.append("-" * width)
        if data.latency_histogram:
            sorted_bins = sorted(data.latency_histogram.items())
            max_count = max(c for _, c in sorted_bins) if sorted_bins else 1
            for bin_start, count in sorted_bins[:20]:  # Limit to first 20 bins
                bar_len = int((count / max_count) * 40) if max_count > 0 else 0
                bar = "#" * bar_len
                lines.append(f"  {bin_start:5d} | {bar} {count}")
        
        lines.append("\n" + "=" * width)
        lines.append("END OF REPORT".center(width))
        lines.append("=" * width)
        
        return "\n".join(lines)
    
    def _generate_json(self, data: ReportData) -> str:
        """Generate JSON report"""
        return json.dumps(data.to_dict(), indent=2)
    
    def save(self, content: str, path: str = None) -> str:
        """Save report to file
        
        Args:
            content: Report content
            path: Output path (uses config if not provided)
            
        Returns:
            Path where report was saved
        """
        output_path = path or self.config.output_path
        
        # Ensure directory exists
        import os
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        return output_path


def generate_html_report(
    data: ReportData,
    output_path: str = "sim/results/report.html",
    config: VisualizationConfig = None
) -> str:
    """Generate HTML report shortcut
    
    Args:
        data: Report data
        output_path: Output file path
        config: Visualization config
        
    Returns:
        HTML report string
    """
    cfg = config or VisualizationConfig()
    cfg.output_format = OutputFormat.HTML
    cfg.output_path = output_path
    
    generator = ReportGenerator(cfg)
    content = generator.generate(data)
    generator.save(content)
    
    return content


def generate_ascii_report(
    data: ReportData
) -> str:
    """Generate ASCII report for terminal
    
    Args:
        data: Report data
        
    Returns:
        ASCII report string
    """
    cfg = VisualizationConfig()
    cfg.output_format = OutputFormat.ASCII
    
    generator = ReportGenerator(cfg)
    return generator.generate(data)


def generate_json_report(
    data: ReportData,
    output_path: str = "sim/results/report.json"
) -> str:
    """Generate JSON report
    
    Args:
        data: Report data
        output_path: Output file path
        
    Returns:
        JSON report string
    """
    cfg = VisualizationConfig()
    cfg.output_format = OutputFormat.JSON
    cfg.output_path = output_path
    
    generator = ReportGenerator(cfg)
    content = generator.generate(data)
    generator.save(content)
    
    return content


def create_report_data_from_stats(stats: Any, name: str = "HBM Simulation") -> ReportData:
    """Create ReportData from SimulationStats
    
    Args:
        stats: SimulationStats object
        name: Report name
        
    Returns:
        ReportData for report generation
    """
    data = ReportData(
        simulation_name=name,
        timestamp=datetime.now().isoformat(),
        simulation_time_us=stats.total_cycles * 0.78125 / 1e6,
        total_cycles=stats.total_cycles,
        total_requests=stats.total_requests,
        completed_requests=stats.completed_requests,
        read_requests=stats.read_requests,
        write_requests=stats.write_requests,
        throughput_gbps=stats.throughput_gbps,
        peak_bandwidth_gbps=stats.peak_bandwidth_gbps,
        bandwidth_efficiency=stats.bandwidth_efficiency,
        avg_latency_cycles=stats.avg_latency,
        row_hit_rate=stats.row_hit_rate,
    )
    
    # Extract per-channel data
    if hasattr(stats, 'per_channel_stats') and stats.per_channel_stats:
        for ch_id, ch_stats in stats.per_channel_stats.items():
            data.channel_bandwidth[ch_id] = getattr(ch_stats, 'avg_bandwidth', 0.0)
            data.channel_utilization[ch_id] = getattr(ch_stats, 'utilization', 0.0)
            data.request_density[ch_id] = getattr(ch_stats, 'total_requests', 0)
    
    return data


if __name__ == "__main__":
    # Demo: Generate sample reports
    print("Report Generation Demo")
    print("=" * 50)
    
    # Create sample report data
    data = ReportData(
        simulation_name="HBM3 Random Traffic Test",
        simulation_time_us=100.0,
        total_cycles=128000000,
        total_requests=19256,
        completed_requests=19256,
        read_requests=13479,
        write_requests=5777,
        throughput_gbps=163.8,
        peak_bandwidth_gbps=819.2,
        bandwidth_efficiency=0.20,
        avg_latency_cycles=2.43,
        row_hit_rate=0.0,
        latency_p50=2.0,
        latency_p95=3.5,
        latency_p99=4.5,
    )
    
    # Add channel data
    data.channel_bandwidth = {
        0: 102.4, 1: 98.7, 2: 105.2, 3: 95.8,
        4: 110.3, 5: 88.9, 6: 99.1, 7: 103.5,
    }
    data.channel_utilization = {
        0: 0.95, 1: 0.82, 2: 0.78, 3: 0.65,
        4: 0.55, 5: 0.42, 6: 0.28, 7: 0.15,
    }
    data.request_density = {
        0: 15000, 1: 12500, 2: 11200, 3: 8500,
        4: 6200, 5: 4200, 6: 2800, 7: 1200,
    }
    
    # Add latency histogram
    data.latency_histogram = {
        0: 50, 10: 200, 20: 500, 30: 300, 40: 150,
        50: 80, 60: 40, 70: 20, 80: 10, 90: 5,
    }
    
    # Generate ASCII report
    print("\nASCII Report:")
    print("-" * 50)
    ascii_report = generate_ascii_report(data)
    print(ascii_report)
    
    # Generate HTML report
    html_path = "sim/results/report.html"
    html_content = generate_html_report(data, html_path)
    print(f"\nHTML report generated: {html_path}")
    
    # Generate JSON report
    json_path = "sim/results/report.json"
    json_content = generate_json_report(data, json_path)
    print(f"JSON report generated: {json_path}")
    
    print("\nDemo complete!")