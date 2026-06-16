"""
Latency Histogram Visualization Module

Provides latency distribution visualization including:
- Latency distribution histogram
- Percentile markers (P50, P95, P99)
- Latency over time
"""

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


@dataclass
class LatencyData:
    """Data container for latency visualization"""
    # Raw latency values (in cycles)
    latencies: List[float] = field(default_factory=list)
    
    # Latency histogram bins
    histogram_bins: Dict[int, int] = field(default_factory=dict)
    
    # Percentiles
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    p999: float = 0.0
    
    # Statistics
    mean: float = 0.0
    std_dev: float = 0.0
    min_latency: float = 0.0
    max_latency: float = 0.0
    
    # Latency over time (cycle -> avg_latency)
    latency_time_series: Dict[int, float] = field(default_factory=dict)
    
    # Timestamps for time series
    time_stamps: List[int] = field(default_factory=list)
    
    def calculate_histogram(self, bin_size: int = 10) -> Dict[int, int]:
        """Calculate histogram bins from latencies
        
        Args:
            bin_size: Size of each histogram bin
            
        Returns:
            Dict mapping bin start value to count
        """
        if not self.latencies:
            return {}
        
        bins = {}
        for lat in self.latencies:
            bin_start = int(lat // bin_size) * bin_size
            bins[bin_start] = bins.get(bin_start, 0) + 1
        
        self.histogram_bins = bins
        return bins
    
    def calculate_percentiles(self) -> Dict[str, float]:
        """Calculate percentiles from latencies
        
        Returns:
            Dict mapping percentile name to value
        """
        if not self.latencies:
            return {'p50': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 0.0, 'p99': 0.0, 'p999': 0.0}
        
        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)
        
        def percentile(p: float) -> float:
            idx = (p / 100.0) * (n - 1)
            lower = int(idx)
            upper = min(lower + 1, n - 1)
            weight = idx - lower
            return sorted_latencies[lower] * (1 - weight) + sorted_latencies[upper] * weight
        
        self.p50 = percentile(50)
        self.p75 = percentile(75)
        self.p90 = percentile(90)
        self.p95 = percentile(95)
        self.p99 = percentile(99)
        self.p999 = percentile(99.9)
        
        return {
            'p50': self.p50,
            'p75': self.p75,
            'p90': self.p90,
            'p95': self.p95,
            'p99': self.p99,
            'p999': self.p999,
        }
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate mean, std dev, min, max from latencies
        
        Returns:
            Dict with statistics
        """
        if not self.latencies:
            return {'mean': 0.0, 'std_dev': 0.0, 'min': 0.0, 'max': 0.0}
        
        n = len(self.latencies)
        self.mean = sum(self.latencies) / n
        variance = sum((x - self.mean) ** 2 for x in self.latencies) / n
        self.std_dev = math.sqrt(variance)
        self.min_latency = min(self.latencies)
        self.max_latency = max(self.latencies)
        
        return {
            'mean': self.mean,
            'std_dev': self.std_dev,
            'min': self.min_latency,
            'max': self.max_latency,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            'histogram_bins': self.histogram_bins,
            'percentiles': {
                'p50': self.p50,
                'p75': self.p75,
                'p90': self.p90,
                'p95': self.p95,
                'p99': self.p99,
                'p999': self.p999,
            },
            'statistics': {
                'mean': self.mean,
                'std_dev': self.std_dev,
                'min': self.min_latency,
                'max': self.max_latency,
            },
            'latency_time_series': self.latency_time_series,
            'time_stamps': self.time_stamps,
        }


@dataclass
class LatencyHistogram:
    """Latency histogram chart generator"""
    data: LatencyData
    
    # Chart configuration
    title: str = "Latency Distribution"
    width: int = 800
    height: int = 400
    
    # Histogram bin size
    bin_size: int = 10
    
    # Color scheme
    bar_color: str = "rgba(118, 75, 162, 0.8)"
    bar_border_color: str = "rgba(118, 75, 162, 1)"
    line_color: str = "rgba(102, 126, 234, 1)"
    percentile_colors: Dict[str, str] = field(default_factory=lambda: {
        'p50': '#4CAF50',  # Green
        'p95': '#FF9800',  # Orange
        'p99': '#F44336',  # Red
    })
    
    def generate_histogram_data(self) -> Dict[str, Any]:
        """Generate data for Chart.js histogram"""
        # Ensure histogram is calculated
        if not self.data.histogram_bins:
            self.data.calculate_histogram(self.bin_size)
        
        # Sort bins by key
        sorted_bins = sorted(self.data.histogram_bins.keys())
        labels = [f"{b}" for b in sorted_bins]
        values = [self.data.histogram_bins[b] for b in sorted_bins]
        
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Request Count',
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
                            'text': 'Count'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': f'Latency (cycles, bin={self.bin_size})'
                        },
                        'type': 'linear',
                        'position': 'bottom'
                    }
                }
            }
        }
    
    def generate_percentile_annotations(self) -> List[Dict[str, Any]]:
        """Generate annotation data for percentiles
        
        Returns:
            List of annotation configs for Chart.js
        """
        # Ensure percentiles are calculated
        if self.data.p50 == 0.0 and not self.data.latencies:
            self.data.calculate_percentiles()
        
        annotations = []
        for p_name, p_value in [
            ('p50', self.data.p50),
            ('p95', self.data.p95),
            ('p99', self.data.p99),
        ]:
            if p_value > 0:
                color = self.percentile_colors.get(p_name, '#000000')
                annotations.append({
                    'type': 'line',
                    'mode': 'vertical',
                    'scaleID': 'x',
                    'value': p_value,
                    'borderColor': color,
                    'borderWidth': 2,
                    'borderDash': [5, 5] if p_name == 'p50' else [10, 5],
                    'label': {
                        'display': True,
                        'content': f'{p_name.upper()}={p_value:.1f}',
                        'position': 'start',
                        'backgroundColor': color,
                        'color': '#fff',
                        'font': {'size': 10}
                    }
                })
        
        return annotations
    
    def generate_time_series_data(self) -> Dict[str, Any]:
        """Generate data for latency over time chart"""
        if not self.data.latency_time_series:
            return {'type': 'line', 'data': {'labels': [], 'datasets': []}}
        
        sorted_times = sorted(self.data.latency_time_series.keys())
        labels = [str(t) for t in sorted_times]
        values = [self.data.latency_time_series[t] for t in sorted_times]
        
        return {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Average Latency (cycles)',
                    'data': values,
                    'borderColor': self.line_color,
                    'backgroundColor': 'rgba(102, 126, 234, 0.1)',
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
                        'text': 'Latency Over Time',
                        'font': {'size': 16}
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Latency (cycles)'
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
    
    def to_chartjs_script(self) -> str:
        """Generate JavaScript for Chart.js integration"""
        hist_data = self.generate_histogram_data()
        ts_data = self.generate_time_series_data()
        annotations = self.generate_percentile_annotations()
        
        return f"""
// Histogram: Latency distribution
const latHistCtx = document.getElementById('latHistogram');
if (latHistCtx) {{
    new Chart(latHistCtx, {json.dumps(hist_data)});
}}

// Line chart: Latency over time
const latTsCtx = document.getElementById('latTimeSeries');
if (latTsCtx) {{
    new Chart(latTsCtx, {json.dumps(ts_data)});
}}

// Percentile annotations (use chartjs-plugin-annotation)
// Add annotations for p50, p95, p99 markers
"""


def generate_latency_histogram(
    latencies: List[float],
    bin_size: int = 10
) -> LatencyData:
    """Generate latency histogram data
    
    Args:
        latencies: List of latency values in cycles
        bin_size: Size of histogram bins
        
    Returns:
        LatencyData for visualization
    """
    data = LatencyData(latencies=latencies)
    data.calculate_histogram(bin_size)
    data.calculate_percentiles()
    data.calculate_statistics()
    
    return data


def generate_percentile_markers(
    latencies: List[float]
) -> Dict[str, float]:
    """Generate percentile markers from latency data
    
    Args:
        latencies: List of latency values
        
    Returns:
        Dict mapping percentile name to value
    """
    data = LatencyData(latencies=latencies)
    return data.calculate_percentiles()


def generate_latency_time_series(
    latency_samples: List[Tuple[int, float]]
) -> LatencyData:
    """Generate latency time series from samples
    
    Args:
        latency_samples: List of (cycle, avg_latency) tuples
        
    Returns:
        LatencyData for visualization
    """
    data = LatencyData(
        latency_time_series=dict(latency_samples),
        time_stamps=[s[0] for s in latency_samples],
    )
    
    # Calculate statistics from time series
    if latency_samples:
        latencies = [s[1] for s in latency_samples]
        data.latencies = latencies
        data.calculate_statistics()
    
    return data


def create_latency_histogram_from_stats(stats: Any) -> LatencyData:
    """Create latency histogram data from SimulationStats
    
    Args:
        stats: SimulationStats object from simulator
        
    Returns:
        LatencyData for visualization
    """
    # Extract latencies from per-channel stats if available
    latencies = []
    
    if hasattr(stats, 'per_channel_stats') and stats.per_channel_stats:
        for ch_stats in stats.per_channel_stats.values():
            if hasattr(ch_stats, 'total_latency_cycles') and hasattr(ch_stats, 'total_requests'):
                if ch_stats.total_requests > 0:
                    # Use average latency for this channel
                    avg_lat = ch_stats.total_latency_cycles / ch_stats.total_requests
                    latencies.extend([avg_lat] * ch_stats.total_requests)
    
    # If no per-channel data, use aggregate statistics
    if not latencies:
        if hasattr(stats, 'avg_latency') and stats.avg_latency > 0:
            # Estimate from average
            avg = stats.avg_latency
            if hasattr(stats, 'completed_requests') and stats.completed_requests > 0:
                latencies = [avg] * stats.completed_requests
            else:
                latencies = [avg]
        
        if hasattr(stats, 'max_latency_cycles') and stats.max_latency_cycles > 0:
            max_lat = stats.max_latency_cycles
            min_lat = getattr(stats, 'min_latency_cycles', 1)
            
            # Generate sample distribution for visualization
            if not latencies:
                import random
                random.seed(42)
                for _ in range(min(1000, max(10, stats.completed_requests))):
                    # Simple normal-ish distribution
                    lat = min_lat + (max_lat - min_lat) * random.random() ** 2
                    latencies.append(lat)
    
    data = LatencyData(latencies=latencies)
    data.calculate_histogram()
    data.calculate_percentiles()
    data.calculate_statistics()
    
    return data


def generate_ascii_histogram(
    latencies: List[float],
    bin_size: int = 10,
    max_width: int = 60
) -> str:
    """Generate ASCII histogram for terminal output
    
    Args:
        latencies: List of latency values
        bin_size: Size of histogram bins
        max_width: Maximum width of bars in characters
        
    Returns:
        ASCII histogram string
    """
    if not latencies:
        return "No latency data available"
    
    # Calculate histogram
    bins = {}
    for lat in latencies:
        bin_start = int(lat // bin_size) * bin_size
        bins[bin_start] = bins.get(bin_start, 0) + 1
    
    if not bins:
        return "No latency data available"
    
    # Sort and prepare
    sorted_bins = sorted(bins.items())
    max_count = max(c for _, c in sorted_bins)
    
    # Find latency range
    min_lat = min(latencies)
    max_lat = max(latencies)
    
    lines = []
    lines.append(f"Latency Histogram (bin={bin_size} cycles)")
    lines.append(f"Range: {min_lat:.1f} - {max_lat:.1f} cycles")
    lines.append("-" * (max_width + 20))
    
    for bin_start, count in sorted_bins:
        bar_len = int((count / max_count) * max_width) if max_count > 0 else 0
        bar = "#" * bar_len
        lines.append(f"{bin_start:5d} | {bar} {count}")
    
    lines.append("-" * (max_width + 20))
    
    # Add statistics
    mean = sum(latencies) / len(latencies)
    lines.append(f"Mean: {mean:.1f} cycles")
    
    # Add percentiles
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    
    def get_p(p):
        idx = int((p / 100.0) * (n - 1))
        return sorted_lat[idx]
    
    lines.append(f"P50: {get_p(50):.1f}, P95: {get_p(95):.1f}, P99: {get_p(99):.1f}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo: Generate sample latency data
    print("Latency Histogram Visualization Demo")
    print("=" * 50)
    
    # Sample latency data (in cycles)
    import random
    random.seed(42)
    
    # Generate sample latencies with realistic distribution
    sample_latencies = []
    for _ in range(1000):
        # Most requests ~10-30 cycles, some outliers up to 100
        lat = random.gauss(20, 10)
        lat = max(1, min(150, lat))
        sample_latencies.append(lat)
    
    # Generate histogram data
    hist_data = generate_latency_histogram(sample_latencies, bin_size=10)
    print(f"\nHistogram Data:")
    print(f"  Bins: {len(hist_data.histogram_bins)}")
    print(f"  Min/Max: {hist_data.min_latency:.1f}/{hist_data.max_latency:.1f} cycles")
    print(f"  Mean: {hist_data.mean:.1f} cycles")
    print(f"  Std Dev: {hist_data.std_dev:.1f} cycles")
    
    # Show percentiles
    percentiles = hist_data.calculate_percentiles()
    print(f"\nPercentiles:")
    for p_name, p_value in percentiles.items():
        print(f"  {p_name.upper()}: {p_value:.1f} cycles")
    
    # Generate ASCII histogram
    print(f"\nASCII Histogram:")
    print(generate_ascii_histogram(sample_latencies, bin_size=10))
    
    print("\nDemo complete!")