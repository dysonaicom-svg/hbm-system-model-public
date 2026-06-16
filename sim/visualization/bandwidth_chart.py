"""
Bandwidth Visualization Module

Provides bandwidth visualization capabilities including:
- Per-channel bandwidth bar charts
- Bandwidth over time line charts
- Bandwidth efficiency gauge
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


@dataclass
class BandwidthData:
    """Data container for bandwidth visualization"""
    # Per-channel bandwidth data (in GB/s)
    channel_bandwidth: Dict[int, float] = field(default_factory=dict)
    
    # Bandwidth over time (cycle -> bandwidth)
    bandwidth_time_series: Dict[int, float] = field(default_factory=dict)
    
    # Per-pattern bandwidth
    pattern_bandwidth: Dict[str, float] = field(default_factory=dict)
    
    # Theoretical peak bandwidth
    peak_bandwidth_gbps: float = 819.2
    
    # Current achieved bandwidth
    achieved_bandwidth_gbps: float = 0.0
    
    # Number of channels
    num_channels: int = 8
    
    # Timestamps for time series (in simulation cycles)
    time_stamps: List[int] = field(default_factory=list)
    
    def get_efficiency(self) -> float:
        """Calculate bandwidth efficiency"""
        if self.peak_bandwidth_gbps <= 0:
            return 0.0
        return self.achieved_bandwidth_gbps / self.peak_bandwidth_gbps
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            'channel_bandwidth': self.channel_bandwidth,
            'bandwidth_time_series': self.bandwidth_time_series,
            'pattern_bandwidth': self.pattern_bandwidth,
            'peak_bandwidth_gbps': self.peak_bandwidth_gbps,
            'achieved_bandwidth_gbps': self.achieved_bandwidth_gbps,
            'efficiency': self.get_efficiency(),
            'num_channels': self.num_channels,
            'time_stamps': self.time_stamps,
        }


@dataclass
class BandwidthChart:
    """Bandwidth chart generator"""
    data: BandwidthData
    
    # Chart configuration
    title: str = "HBM Bandwidth Analysis"
    width: int = 800
    height: int = 400
    
    # Color scheme
    bar_color: str = "rgba(102, 126, 234, 0.8)"
    bar_border_color: str = "rgba(102, 126, 234, 1)"
    line_color: str = "rgba(118, 75, 162, 1)"
    gauge_color: str = "#667eea"
    
    def generate_bar_chart_data(self) -> Dict[str, Any]:
        """Generate data for Chart.js bar chart (per-channel bandwidth)"""
        labels = [f"CH{i}" for i in range(self.data.num_channels)]
        values = [
            self.data.channel_bandwidth.get(i, 0.0)
            for i in range(self.data.num_channels)
        ]
        
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Bandwidth (GB/s)',
                    'data': values,
                    'backgroundColor': self.bar_color,
                    'borderColor': self.bar_border_color,
                    'borderWidth': 1,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {
                        'display': True,
                        'text': self.title,
                        'font': {'size': 16}
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Bandwidth (GB/s)'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Channel'
                        }
                    }
                }
            }
        }
    
    def generate_line_chart_data(self) -> Dict[str, Any]:
        """Generate data for Chart.js line chart (bandwidth over time)"""
        sorted_times = sorted(self.data.bandwidth_time_series.keys())
        labels = [str(t) for t in sorted_times]
        values = [self.data.bandwidth_time_series[t] for t in sorted_times]
        
        return {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Bandwidth (GB/s)',
                    'data': values,
                    'borderColor': self.line_color,
                    'backgroundColor': 'rgba(118, 75, 162, 0.1)',
                    'fill': True,
                    'tension': 0.3,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': True},
                    'title': {
                        'display': True,
                        'text': 'Bandwidth Over Time',
                        'font': {'size': 16}
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Bandwidth (GB/s)'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Simulation Cycle'
                        }
                    }
                }
            }
        }
    
    def generate_gauge_data(self) -> Dict[str, Any]:
        """Generate data for Chart.js doughnut gauge (bandwidth efficiency)"""
        efficiency = self.get_efficiency_display()
        remaining = 1.0 - efficiency
        
        return {
            'type': 'doughnut',
            'data': {
                'labels': ['Used', 'Available'],
                'datasets': [{
                    'data': [efficiency * 100, remaining * 100],
                    'backgroundColor': [
                        self.gauge_color,
                        'rgba(200, 200, 200, 0.3)'
                    ],
                    'borderWidth': 0,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'circumference': 180,
                'rotation': 270,
                'cutout': '70%',
                'plugins': {
                    'legend': {'display': False},
                    'title': {
                        'display': True,
                        'text': f'Efficiency: {efficiency * 100:.1f}%',
                        'font': {'size': 14}
                    },
                    'tooltip': {
                        'enabled': False
                    }
                }
            }
        }
    
    def get_efficiency_display(self) -> float:
        """Get efficiency for display (0-1 scale)"""
        return min(1.0, max(0.0, self.data.get_efficiency()))
    
    def to_chartjs_script(self) -> str:
        """Generate JavaScript for Chart.js integration"""
        bar_data = self.generate_bar_chart_data()
        line_data = self.generate_line_chart_data()
        gauge_data = self.generate_gauge_data()
        
        return f"""
// Bar chart: Per-channel bandwidth
const bwBarCtx = document.getElementById('bwBarChart');
if (bwBarCtx) {{
    new Chart(bwBarCtx, {json.dumps(bar_data)});
}}

// Line chart: Bandwidth over time
const bwLineCtx = document.getElementById('bwLineChart');
if (bwLineCtx) {{
    new Chart(bwLineCtx, {json.dumps(line_data)});
}}

// Gauge: Bandwidth efficiency
const bwGaugeCtx = document.getElementById('bwGaugeChart');
if (bwGaugeCtx) {{
    new Chart(bwGaugeCtx, {json.dumps(gauge_data)});
}}
"""


def generate_bandwidth_bar_chart(
    channel_bandwidth: Dict[int, float],
    peak_bandwidth: float = 819.2,
    num_channels: int = 8
) -> BandwidthData:
    """Generate bandwidth bar chart data from channel statistics
    
    Args:
        channel_bandwidth: Dict mapping channel_id to bandwidth in GB/s
        peak_bandwidth: Theoretical peak bandwidth
        num_channels: Total number of channels
        
    Returns:
        BandwidthData for visualization
    """
    data = BandwidthData(
        channel_bandwidth=channel_bandwidth,
        peak_bandwidth_gbps=peak_bandwidth,
        num_channels=num_channels,
    )
    
    # Calculate total achieved bandwidth
    data.achieved_bandwidth_gbps = sum(channel_bandwidth.values())
    
    return data


def generate_bandwidth_time_series(
    bandwidth_samples: List[Tuple[int, float]],
    peak_bandwidth: float = 819.2
) -> BandwidthData:
    """Generate bandwidth time series from samples
    
    Args:
        bandwidth_samples: List of (cycle, bandwidth) tuples
        peak_bandwidth: Theoretical peak bandwidth
        
    Returns:
        BandwidthData for visualization
    """
    data = BandwidthData(
        bandwidth_time_series=dict(bandwidth_samples),
        time_stamps=[s[0] for s in bandwidth_samples],
        peak_bandwidth_gbps=peak_bandwidth,
    )
    
    # Calculate average achieved bandwidth
    if bandwidth_samples:
        data.achieved_bandwidth_gbps = sum(s[1] for s in bandwidth_samples) / len(bandwidth_samples)
    
    return data


def generate_bandwidth_efficiency_gauge(
    achieved_bandwidth: float,
    peak_bandwidth: float = 819.2
) -> BandwidthData:
    """Generate bandwidth efficiency gauge data
    
    Args:
        achieved_bandwidth: Actual achieved bandwidth in GB/s
        peak_bandwidth: Theoretical peak bandwidth
        
    Returns:
        BandwidthData for visualization
    """
    return BandwidthData(
        achieved_bandwidth_gbps=achieved_bandwidth,
        peak_bandwidth_gbps=peak_bandwidth,
    )


def create_bandwidth_chart_from_stats(stats: Any) -> BandwidthData:
    """Create bandwidth chart data from SimulationStats
    
    Args:
        stats: SimulationStats object from simulator
        
    Returns:
        BandwidthData for visualization
    """
    # Extract per-channel bandwidth from stats
    channel_bw = {}
    if hasattr(stats, 'per_channel_stats') and stats.per_channel_stats:
        for ch_id, ch_stats in stats.per_channel_stats.items():
            # Calculate bandwidth per channel
            if hasattr(ch_stats, 'total_requests') and ch_stats.total_requests > 0:
                # Each request transfers 128 bytes
                bytes_per_request = 128
                # tCK = 781.25 ps = 0.78125 ns per cycle
                tCK_ns = 0.78125
                # Calculate from stats if available
                if hasattr(ch_stats, 'avg_latency') and hasattr(stats, 'total_cycles'):
                    # Use throughput metric
                    if stats.total_cycles > 0:
                        channel_bw[ch_id] = ch_stats.total_requests * bytes_per_request / (stats.total_cycles * tCK_ns)
                    else:
                        channel_bw[ch_id] = 0.0
                else:
                    channel_bw[ch_id] = 0.0
            else:
                channel_bw[ch_id] = 0.0
    
    # Get peak bandwidth
    peak_bw = getattr(stats, 'peak_bandwidth_gbps', 819.2)
    
    # Create bandwidth data
    data = BandwidthData(
        channel_bandwidth=channel_bw,
        peak_bandwidth_gbps=peak_bw,
        achieved_bandwidth_gbps=getattr(stats, 'throughput_gbps', 0.0),
        num_channels=len(channel_bw) if channel_bw else 8,
    )
    
    return data


if __name__ == "__main__":
    # Demo: Generate sample bandwidth data
    print("Bandwidth Visualization Demo")
    print("=" * 50)
    
    # Sample channel bandwidth data
    sample_channel_bw = {
        0: 102.4,
        1: 98.7,
        2: 105.2,
        3: 95.8,
        4: 110.3,
        5: 88.9,
        6: 99.1,
        7: 103.5,
    }
    
    # Sample time series data
    sample_time_series = [
        (0, 0.0),
        (1000, 85.3),
        (2000, 92.1),
        (3000, 88.7),
        (4000, 95.2),
        (5000, 98.5),
        (6000, 102.1),
        (7000, 99.8),
        (8000, 101.3),
        (9000, 100.2),
        (10000, 98.9),
    ]
    
    # Generate bar chart data
    bar_data = generate_bandwidth_bar_chart(sample_channel_bw)
    print(f"\nBar Chart Data:")
    print(f"  Total bandwidth: {bar_data.achieved_bandwidth_gbps:.2f} GB/s")
    print(f"  Efficiency: {bar_data.get_efficiency() * 100:.1f}%")
    
    # Generate time series data
    ts_data = generate_bandwidth_time_series(sample_time_series)
    print(f"\nTime Series Data:")
    print(f"  Samples: {len(ts_data.bandwidth_time_series)}")
    print(f"  Average bandwidth: {ts_data.achieved_bandwidth_gbps:.2f} GB/s")
    
    # Generate gauge data
    gauge_data = generate_bandwidth_efficiency_gauge(100.0, 819.2)
    print(f"\nGauge Data:")
    print(f"  Achieved: {gauge_data.achieved_bandwidth_gbps:.2f} GB/s")
    print(f"  Efficiency: {gauge_data.get_efficiency() * 100:.1f}%")
    
    # Create chart objects
    bar_chart = BandwidthChart(data=bar_data)
    line_chart = BandwidthChart(data=ts_data)
    gauge_chart = BandwidthChart(data=gauge_data)
    
    print(f"\nChart configurations:")
    print(f"  Bar chart: {bar_chart.width}x{bar_chart.height}")
    print(f"  Line chart: {line_chart.width}x{line_chart.height}")
    print(f"  Gauge: {gauge_chart.width}x{gauge_chart.height}")
    
    print("\nDemo complete!")