"""
Latency Distribution Analysis Module

Provides comprehensive latency analysis capabilities for HBM systems.
Features:
- Latency distribution analysis (histograms, percentiles)
- Pattern-based latency categorization
- Outlier detection
- Statistical analysis (mean, std dev, variance)
- Time-series latency tracking
- ASCII visualization for terminal output

Usage:
    from model.monitoring.latency_analyzer import LatencyAnalyzer

    analyzer = LatencyAnalyzer(bin_size=5)
    analyzer.add_samples(latencies)
    report = analyzer.generate_report()
"""

import math
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum


class LatencyCategory(Enum):
    """Latency categorization based on request type"""
    ROW_HIT = "row_hit"
    ROW_MISS = "row_miss"
    PAGE_OPEN = "page_open"
    PAGE_CLOSE = "page_close"
    PRECHARGE = "precharge"
    REFRESH = "refresh"
    ACTIVATE = "activate"


@dataclass
class LatencyStats:
    """Statistical summary of latency data"""
    count: int = 0
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    variance: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    p999: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            'count': self.count,
            'mean': self.mean,
            'median': self.median,
            'std_dev': self.std_dev,
            'variance': self.variance,
            'min': self.min_val,
            'max': self.max_val,
            'p50': self.p50,
            'p75': self.p75,
            'p90': self.p90,
            'p95': self.p95,
            'p99': self.p99,
            'p999': self.p999,
        }


@dataclass
class LatencyHistogram:
    """Histogram representation of latency distribution"""
    bins: Dict[int, int] = field(default_factory=dict)  # bin_start -> count
    bin_size: int = 10
    total_samples: int = 0
    overflow_count: int = 0  # samples exceeding max bin

    def add_value(self, value: float):
        """Add a value to the histogram"""
        bin_start = int(value // self.bin_size) * self.bin_size
        self.bins[bin_start] = self.bins.get(bin_start, 0) + 1
        self.total_samples += 1

    def get_distribution(self) -> List[Tuple[int, int, float]]:
        """Get distribution as (bin_start, count, percentage) tuples"""
        result = []
        for bin_start in sorted(self.bins.keys()):
            count = self.bins[bin_start]
            pct = (count / self.total_samples * 100) if self.total_samples > 0 else 0
            result.append((bin_start, count, pct))
        return result

    def get_cumulative(self) -> List[Tuple[int, int, float]]:
        """Get cumulative distribution"""
        result = []
        cum_count = 0
        for bin_start, count in sorted(self.bins.items()):
            cum_count += count
            pct = (cum_count / self.total_samples * 100) if self.total_samples > 0 else 0
            result.append((bin_start, cum_count, pct))
        return result


@dataclass
class LatencyPattern:
    """Latency pattern analysis for specific traffic pattern"""
    pattern_name: str
    samples: List[float] = field(default_factory=list)
    histogram: Optional[LatencyHistogram] = None
    stats: Optional[LatencyStats] = None

    def analyze(self, bin_size: int = 10) -> LatencyStats:
        """Perform full analysis on collected samples"""
        if not self.samples:
            return LatencyStats()

        # Calculate histogram
        self.histogram = LatencyHistogram(bin_size=bin_size)
        for s in self.samples:
            self.histogram.add_value(s)

        # Calculate statistics
        self.stats = calculate_statistics(self.samples)
        return self.stats


def calculate_statistics(values: List[float]) -> LatencyStats:
    """Calculate comprehensive statistics from latency values"""
    if not values:
        return LatencyStats()

    n = len(values)
    sorted_vals = sorted(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n

    stats = LatencyStats()
    stats.count = n
    stats.mean = mean
    stats.median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    stats.std_dev = math.sqrt(variance)
    stats.variance = variance
    stats.min_val = min(values)
    stats.max_val = max(values)

    # Calculate percentiles
    def pct(p: float) -> float:
        idx = (p / 100.0) * (n - 1)
        lower = int(idx)
        upper = min(lower + 1, n - 1)
        weight = idx - lower
        return sorted_vals[lower] * (1 - weight) + sorted_vals[upper] * weight

    stats.p50 = pct(50)
    stats.p75 = pct(75)
    stats.p90 = pct(90)
    stats.p95 = pct(95)
    stats.p99 = pct(99)
    stats.p999 = pct(99.9)

    return stats


def detect_outliers(values: List[float], threshold: float = 2.5) -> Tuple[List[int], List[float]]:
    """Detect outliers using z-score method

    Returns:
        Tuple of (indices, outlier_values)
    """
    if len(values) < 3:
        return [], []

    stats = calculate_statistics(values)
    if stats.std_dev == 0:
        return [], []

    outliers = []
    outlier_indices = []
    for i, v in enumerate(values):
        z_score = abs((v - stats.mean) / stats.std_dev)
        if z_score > threshold:
            outlier_indices.append(i)
            outliers.append(v)

    return outlier_indices, outliers


def categorize_latency(latency: float, base_timing: int = 10) -> LatencyCategory:
    """Categorize latency based on expected timing"""
    if latency <= base_timing:
        return LatencyCategory.ROW_HIT
    elif latency <= base_timing * 2:
        return LatencyCategory.ROW_MISS
    elif latency <= base_timing * 3:
        return LatencyCategory.PAGE_OPEN
    elif latency <= base_timing * 5:
        return LatencyCategory.PAGE_CLOSE
    elif latency <= base_timing * 10:
        return LatencyCategory.PRECHARGE
    elif latency <= base_timing * 50:
        return LatencyCategory.REFRESH
    else:
        return LatencyCategory.ACTIVATE


class LatencyAnalyzer:
    """
    Comprehensive latency analysis for HBM simulation results.

    Features:
    - Multi-pattern latency tracking
    - Statistical analysis
    - Outlier detection
    - Time-series analysis
    - ASCII visualization
    """

    def __init__(
        self,
        bin_size: int = 10,
        max_samples: int = 100000,
        history_windows: int = 100
    ):
        self.bin_size = bin_size
        self.max_samples = max_samples
        self.history_windows = history_windows

        # All samples
        self.all_samples: deque = deque(maxlen=max_samples)

        # Per-pattern samples
        self.patterns: Dict[str, List[float]] = defaultdict(list)

        # Per-channel samples
        self.channel_samples: Dict[int, List[float]] = defaultdict(list)

        # Category distribution
        self.category_counts: Dict[LatencyCategory, int] = defaultdict(int)

        # Time series (cycle -> avg latency)
        self.time_series: deque = deque(maxlen=history_windows)

        # Overall histogram
        self.histogram = LatencyHistogram(bin_size=bin_size)

        # Computed statistics
        self.stats: Optional[LatencyStats] = None

    def add_sample(self, latency: float, cycle: int = 0):
        """Add a single latency sample"""
        self.all_samples.append(latency)
        self.histogram.add_value(latency)

        # Categorize
        category = categorize_latency(latency)
        self.category_counts[category] += 1

    def add_samples(self, latencies: List[float], cycle: Optional[int] = None):
        """Add multiple latency samples"""
        for lat in latencies:
            self.add_sample(lat, cycle)

    def add_pattern_sample(self, pattern_name: str, latency: float):
        """Add a latency sample for a specific pattern"""
        self.add_sample(latency)
        self.patterns[pattern_name].append(latency)

    def add_channel_sample(self, channel_id: int, latency: float):
        """Add a latency sample for a specific channel"""
        self.add_sample(latency)
        self.channel_samples[channel_id].append(latency)

    def add_time_point(self, cycle: int, avg_latency: float):
        """Add a time series data point"""
        self.time_series.append((cycle, avg_latency))

    def analyze(self) -> LatencyStats:
        """Perform full analysis on collected samples"""
        if not self.all_samples:
            return LatencyStats()

        self.stats = calculate_statistics(list(self.all_samples))
        return self.stats

    def get_histogram_data(self) -> List[Tuple[int, int, float]]:
        """Get histogram distribution data"""
        return self.histogram.get_distribution()

    def get_cumulative_distribution(self) -> List[Tuple[int, int, float]]:
        """Get cumulative distribution data"""
        return self.histogram.get_cumulative()

    def get_pattern_report(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """Get analysis report for a specific pattern"""
        if pattern_name not in self.patterns or not self.patterns[pattern_name]:
            return None

        samples = self.patterns[pattern_name]
        stats = calculate_statistics(samples)

        histogram = LatencyHistogram(bin_size=self.bin_size)
        for s in samples:
            histogram.add_value(s)

        return {
            'pattern': pattern_name,
            'count': stats.count,
            'statistics': stats.to_dict(),
            'distribution': histogram.get_distribution(),
        }

    def get_category_distribution(self) -> Dict[str, int]:
        """Get latency category distribution"""
        return {cat.value: count for cat, count in self.category_counts.items()}

    def get_outliers(self, threshold: float = 2.5) -> Tuple[List[int], List[float]]:
        """Get outlier samples"""
        return detect_outliers(list(self.all_samples), threshold)

    def generate_ascii_histogram(
        self,
        max_width: int = 60,
        show_percentiles: bool = True
    ) -> str:
        """Generate ASCII histogram for terminal output"""
        if not self.all_samples:
            return "No latency data available"

        self.analyze()
        dist = self.get_histogram_data()

        max_count = max(c for _, c, _ in dist) if dist else 1
        max_val = self.stats.max_val if self.stats else 0
        min_val = self.stats.min_val if self.stats else 0

        lines = []
        lines.append("Latency Distribution Histogram")
        lines.append(f"Range: {min_val:.1f} - {max_val:.1f} cycles (bin={self.bin_size})")
        lines.append("-" * (max_width + 25))

        for bin_start, count, pct in dist:
            bar_len = int((count / max_count) * max_width) if max_count > 0 else 0
            bar = "#" * bar_len
            lines.append(f"{bin_start:5d} |{bar:<{max_width}}| {count:5d} ({pct:4.1f}%)")

        lines.append("-" * (max_width + 25))

        if show_percentiles and self.stats:
            lines.append(f"Statistics:")
            lines.append(f"  Mean:   {self.stats.mean:>8.1f} cycles")
            lines.append(f"  Median: {self.stats.median:>8.1f} cycles")
            lines.append(f"  StdDev: {self.stats.std_dev:>8.1f} cycles")
            lines.append(f"  Min:    {self.stats.min_val:>8.1f} cycles")
            lines.append(f"  Max:    {self.stats.max_val:>8.1f} cycles")
            lines.append("")
            lines.append(f"Percentiles:")
            lines.append(f"  P50: {self.stats.p50:>6.1f}  P75: {self.stats.p75:>6.1f}  P90: {self.stats.p90:>6.1f}")
            lines.append(f"  P95: {self.stats.p95:>6.1f}  P99: {self.stats.p99:>6.1f}  P99.9: {self.stats.p999:>6.1f}")

        return "\n".join(lines)

    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        lines = []
        lines.append("=" * 70)
        lines.append(" LATENCY ANALYSIS REPORT")
        lines.append("=" * 70)

        # Overall statistics
        self.analyze()
        if self.stats:
            lines.append(f"\nSample Count: {self.stats.count:,}")
            lines.append(f"Mean Latency: {self.stats.mean:.2f} cycles")
            lines.append(f"Median: {self.stats.median:.2f} cycles")
            lines.append(f"Std Dev: {self.stats.std_dev:.2f} cycles")
            lines.append(f"Range: {self.stats.min_val:.1f} - {self.stats.max_val:.1f} cycles")

            lines.append("\nPercentiles:")
            lines.append(f"  P50:  {self.stats.p50:>8.2f} cycles")
            lines.append(f"  P75:  {self.stats.p75:>8.2f} cycles")
            lines.append(f"  P90:  {self.stats.p90:>8.2f} cycles")
            lines.append(f"  P95:  {self.stats.p95:>8.2f} cycles")
            lines.append(f"  P99:  {self.stats.p99:>8.2f} cycles")
            lines.append(f"  P99.9:{self.stats.p999:>8.2f} cycles")

        # Category distribution
        cat_dist = self.get_category_distribution()
        if cat_dist:
            lines.append("\nLatency Categories:")
            for cat, count in sorted(cat_dist.items(), key=lambda x: -x[1]):
                pct = (count / self.stats.count * 100) if self.stats and self.stats.count > 0 else 0
                lines.append(f"  {cat:15s}: {count:>8,} ({pct:>5.1f}%)")

        # Pattern analysis
        if self.patterns:
            lines.append("\nPer-Pattern Latency:")
            for pattern, samples in self.patterns.items():
                if samples:
                    p_stats = calculate_statistics(samples)
                    lines.append(f"  {pattern:15s}: mean={p_stats.mean:>6.1f}, p99={p_stats.p99:>6.1f} (n={len(samples)})")

        # Channel analysis
        if self.channel_samples:
            lines.append("\nPer-Channel Latency:")
            for ch, samples in sorted(self.channel_samples.items()):
                if samples:
                    ch_stats = calculate_statistics(samples)
                    lines.append(f"  CH{ch:02d}: mean={ch_stats.mean:>6.1f}, p99={ch_stats.p99:>6.1f} (n={len(samples)})")

        # Outliers
        outlier_idx, outliers = self.get_outliers()
        if outliers:
            lines.append(f"\nOutliers Detected: {len(outliers)} (threshold: 2.5 sigma)")
            lines.append(f"  Max outlier: {max(outliers):.1f} cycles")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def export_data(self) -> Dict[str, Any]:
        """Export all analysis data"""
        self.analyze()
        return {
            'sample_count': len(self.all_samples),
            'statistics': self.stats.to_dict() if self.stats else {},
            'histogram': {
                'bin_size': self.histogram.bin_size,
                'distribution': self.get_histogram_data(),
                'cumulative': self.get_cumulative_distribution(),
            },
            'categories': self.get_category_distribution(),
            'patterns': {
                name: calculate_statistics(samples).to_dict()
                for name, samples in self.patterns.items()
                if samples
            },
            'channels': {
                ch: calculate_statistics(samples).to_dict()
                for ch, samples in self.channel_samples.items()
                if samples
            },
            'time_series': list(self.time_series),
            'outliers': {
                'count': len(self.get_outliers()[1]),
                'max_value': max(self.get_outliers()[1]) if self.get_outliers()[1] else None,
            },
        }


def create_analyzer(bin_size: int = 10) -> LatencyAnalyzer:
    """Create a configured LatencyAnalyzer"""
    return LatencyAnalyzer(bin_size=bin_size)


if __name__ == "__main__":
    # Demo: Test latency analysis
    print("Latency Analyzer Demo")
    print("=" * 70)

    # Create analyzer
    analyzer = LatencyAnalyzer(bin_size=5)

    # Generate sample data with realistic distribution
    import random
    random.seed(42)

    # Simulate different traffic patterns
    patterns = {
        'sequential': [],
        'random': [],
        'hotspot': [],
    }

    for _ in range(5000):
        # Sequential: mostly row hits, low latency
        lat = abs(random.gauss(12, 3))
        patterns['sequential'].append(lat)
        analyzer.add_pattern_sample('sequential', lat)

    for _ in range(3000):
        # Random: mix of hits and misses
        lat = abs(random.gauss(25, 15))
        patterns['random'].append(lat)
        analyzer.add_pattern_sample('random', lat)

    for _ in range(2000):
        # Hotspot: mostly hits with some misses
        lat = abs(random.gauss(15, 8))
        patterns['hotspot'].append(lat)
        analyzer.add_pattern_sample('hotspot', lat)

    # Add some outliers
    for _ in range(50):
        lat = random.uniform(100, 200)
        analyzer.add_sample(lat)

    # Generate report
    print(analyzer.generate_report())

    # ASCII histogram
    print("\n" + analyzer.generate_ascii_histogram())

    # Export data
    data = analyzer.export_data()
    print(f"\nExported data includes {data['sample_count']} samples")

    print("\nDemo complete!")