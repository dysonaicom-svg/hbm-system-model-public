"""Latency Analysis Module for HBM4 Performance Analysis"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import statistics


@dataclass
class LatencyStats:
    """Statistical summary of latency data"""
    min_ns: float = 0.0
    max_ns: float = 0.0
    mean_ns: float = 0.0
    median_ns: float = 0.0
    p50_ns: float = 0.0
    p90_ns: float = 0.0
    p95_ns: float = 0.0
    p99_ns: float = 0.0
    std_dev_ns: float = 0.0
    sample_count: int = 0


class LatencyDistribution:
    """Analyzes latency distribution"""

    def __init__(self):
        self.samples: List[float] = []

    def add_sample(self, latency_ns: float):
        self.samples.append(latency_ns)

    def analyze(self) -> LatencyStats:
        if not self.samples:
            return LatencyStats()

        sorted_samples = sorted(self.samples)
        n = len(sorted_samples)

        def percentile(p: float) -> float:
            idx = int(n * p / 100)
            idx = min(idx, n - 1)
            return sorted_samples[idx]

        return LatencyStats(
            min_ns=min(sorted_samples),
            max_ns=max(sorted_samples),
            mean_ns=statistics.mean(sorted_samples),
            median_ns=percentile(50),
            p50_ns=percentile(50),
            p90_ns=percentile(90),
            p95_ns=percentile(95),
            p99_ns=percentile(99),
            std_dev_ns=statistics.stdev(sorted_samples) if n > 1 else 0.0,
            sample_count=n
        )

    def get_histogram(self, bins: int = 20) -> Tuple[List[float], List[int]]:
        if not self.samples:
            return [], []

        min_val, max_val = min(self.samples), max(self.samples)
        if min_val == max_val:
            return [min_val], [len(self.samples)]

        bin_width = (max_val - min_val) / bins
        edges = [min_val + i * bin_width for i in range(bins + 1)]
        counts = [0] * bins

        for s in self.samples:
            bin_idx = min(int((s - min_val) / bin_width), bins - 1)
            counts[bin_idx] += 1

        centers = [(edges[i] + edges[i + 1]) / 2 for i in range(bins)]
        return centers, counts

    def get_percentiles(self, percentiles: List[float]) -> Dict[float, float]:
        """Get custom percentiles from the distribution"""
        if not self.samples:
            return {p: 0.0 for p in percentiles}

        sorted_samples = sorted(self.samples)
        n = len(sorted_samples)

        def percentile(p: float) -> float:
            idx = int(n * p / 100)
            idx = min(idx, n - 1)
            return sorted_samples[idx]

        return {p: percentile(p) for p in percentiles}
