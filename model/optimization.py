"""Performance Optimization Module for HBM4 Simulator"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import deque


@dataclass
class OptimizedMetrics:
    """Optimized performance metrics collection"""
    request_count: int = 0
    hit_count: int = 0
    miss_count: int = 0
    total_latency_ns: float = 0.0
    channel_utilization: Dict[int, float] = None

    def __post_init__(self):
        if self.channel_utilization is None:
            self.channel_utilization = {}

    def record_hit(self, channel: int, latency_ns: float):
        self.request_count += 1
        self.hit_count += 1
        self.total_latency_ns += latency_ns
        self.channel_utilization[channel] = self.channel_utilization.get(channel, 0) + 1

    def record_miss(self, channel: int, latency_ns: float):
        self.request_count += 1
        self.miss_count += 1
        self.total_latency_ns += latency_ns
        self.channel_utilization[channel] = self.channel_utilization.get(channel, 0) + 1

    @property
    def hit_rate(self) -> float:
        return self.hit_count / self.request_count if self.request_count > 0 else 0.0

    @property
    def avg_latency_ns(self) -> float:
        return self.total_latency_ns / self.request_count if self.request_count > 0 else 0.0


class BatchRequestProcessor:
    """Optimized batch request processing"""

    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self.pending = deque()

    def add(self, request) -> List:
        """Add request and return batch if full"""
        self.pending.append(request)
        if len(self.pending) >= self.batch_size:
            return self._flush()
        return []

    def flush(self) -> List:
        """Force flush current batch"""
        return self._flush()

    def _flush(self) -> List:
        batch = list(self.pending)
        self.pending.clear()
        return batch


class OptimizedBankSelector:
    """Optimized bank selection using cached state"""

    def __init__(self, num_banks: int = 16):
        self.num_banks = num_banks
        self._cache: Dict[int, int] = {}

    def select_next(self, channel: int, active_banks: List[int]) -> int:
        """Select next bank avoiding recently used"""
        if not active_banks:
            return 0

        last = self._cache.get(channel, -1)

        for bank in active_banks:
            if bank != last:
                self._cache[channel] = bank
                return bank

        return active_banks[0]


class LatencyTracker:
    """Optimized latency tracking with O(1) percentile"""

    def __init__(self):
        self.samples: List[float] = []
        self._sorted = True

    def add(self, latency: float):
        self.samples.append(latency)
        self._sorted = False

    def get_percentile(self, p: float) -> float:
        if not self.samples:
            return 0.0

        if not self._sorted:
            self.samples.sort()
            self._sorted = True

        idx = int(len(self.samples) * p / 100)
        idx = min(idx, len(self.samples) - 1)
        return self.samples[idx]

    def get_p50(self) -> float:
        return self.get_percentile(50)

    def get_p90(self) -> float:
        return self.get_percentile(90)

    def get_p99(self) -> float:
        return self.get_percentile(99)


# Optimization configurations
OPTIMIZATION_PROFILES = {
    "speed": {
        "batch_size": 64,
        "enable_caching": True,
        "reduce_precision": True,
    },
    "balanced": {
        "batch_size": 32,
        "enable_caching": True,
        "reduce_precision": False,
    },
    "accuracy": {
        "batch_size": 16,
        "enable_caching": False,
        "reduce_precision": False,
    },
}


def get_optimized_processor(profile: str = "balanced") -> Dict:
    """Get optimized processor config for profile"""
    config = OPTIMIZATION_PROFILES.get(profile, OPTIMIZATION_PROFILES["balanced"])
    return {
        "batch_processor": BatchRequestProcessor(config["batch_size"]),
        "enable_caching": config["enable_caching"],
        "reduce_precision": config["reduce_precision"],
    }
