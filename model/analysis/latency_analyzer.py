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
        self._cached_stats: Optional[LatencyStats] = None

    def add_sample(self, latency_ns: float):
        self.samples.append(latency_ns)
        self._cached_stats = None  # Invalidate cache

    def analyze(self) -> LatencyStats:
        if not self.samples:
            return LatencyStats()

        # Use cached result if available
        if self._cached_stats is not None:
            return self._cached_stats

        sorted_samples = sorted(self.samples)
        n = len(sorted_samples)

        # Compute all percentiles at once using statistics.quantiles
        qs = statistics.quantiles(sorted_samples, n=100) if n > 1 else []

        stats = LatencyStats(
            min_ns=min(sorted_samples),
            max_ns=max(sorted_samples),
            mean_ns=statistics.mean(sorted_samples),
            median_ns=qs[49] if len(qs) > 49 else sorted_samples[-1],  # p50
            p50_ns=qs[49] if len(qs) > 49 else sorted_samples[-1],
            p90_ns=qs[89] if len(qs) > 89 else sorted_samples[-1],
            p95_ns=qs[94] if len(qs) > 94 else sorted_samples[-1],
            p99_ns=qs[98] if len(qs) > 98 else sorted_samples[-1],
            std_dev_ns=statistics.stdev(sorted_samples) if n > 1 else 0.0,
            sample_count=n
        )

        self._cached_stats = stats
        return stats

    def get_histogram(self, bins: int = 20) -> Tuple[List[float], List[int]]:
        if not self.samples:
            return [], []

        min_val, max_val = min(self.samples), max(self.samples)
        # Use tolerance for float comparison
        if abs(max_val - min_val) < 1e-9:
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

        # Use statistics.quantiles for accurate percentile calculation
        if n >= 100:
            qs = statistics.quantiles(sorted_samples, n=100)
            result = {}
            for p in percentiles:
                idx = int(p) - 1
                if 0 <= idx < 99:
                    result[p] = qs[idx]
                else:
                    result[p] = sorted_samples[-1]
            return result
        else:
            # Fallback for small samples: use linear interpolation
            def percentile(p: float) -> float:
                idx = (n - 1) * p / 100
                lower = int(idx)
                upper = min(lower + 1, n - 1)
                weight = idx - lower
                return sorted_samples[lower] * (1 - weight) + sorted_samples[upper] * weight

            return {p: percentile(p) for p in percentiles}
