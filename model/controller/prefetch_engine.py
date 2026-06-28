"""
Intelligent Prefetch Engine

Implements multiple prefetch policies to reduce memory latency:
- Sequential: Prefetch consecutive addresses
- Stride: Detect and follow stride patterns
- Correlation: Learn address correlations from history

Based on research findings for HBM4 optimization (2026-06-25).
"""

from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from collections import deque
import logging

_logger = logging.getLogger('hbm4.prefetch')


class PrefetchPolicy:
    """Prefetch policy types"""
    NONE = "none"
    SEQUENTIAL = "sequential"
    STRIDE = "stride"
    CORRELATION = "correlation"


@dataclass
class PrefetchRequest:
    """Prefetch request for memory controller"""
    address: int
    size: int
    priority: int  # 0-255, higher = more important
    confidence: float  # 0.0-1.0
    policy: str

    def __repr__(self):
        return (f"PrefetchRequest(addr=0x{self.address:x}, size={self.size}, "
                f"priority={self.priority}, confidence={self.confidence:.2f}, policy={self.policy})")


class PrefetchEngine:
    """Intelligent prefetch engine with multiple policies

    Features:
    - Sequential prefetch: Predict next consecutive addresses
    - Stride detection: Identify fixed stride patterns
    - Correlation learning: Learn frequently accessed address sequences

    The engine monitors access patterns and generates prefetch hints
    that the controller can use to pre-load data before it's needed.
    """

    def __init__(
        self,
        history_size: int = 1024,
        stride_confidence_threshold: float = 0.8,
        correlation_min_count: int = 3,
    ):
        """Initialize prefetch engine

        Args:
            history_size: Maximum number of accesses to track
            stride_confidence_threshold: Minimum confidence to use stride prediction
            correlation_min_count: Minimum occurrences to establish correlation
        """
        self.history: deque = deque(maxlen=history_size)
        self.stride_detector: Dict[int, Tuple[int, int, int]] = {}  # addr -> (prev_addr, stride, count)
        self.correlation_table: Dict[int, List[int]] = {}  # addr -> [next_addrs]
        self.correlation_counts: Dict[int, Dict[int, int]] = {}  # addr -> {next_addr: count}

        self.policy: str = PrefetchPolicy.SEQUENTIAL
        self.enabled: bool = True

        # Configuration
        self.stride_confidence_threshold = stride_confidence_threshold
        self.correlation_min_count = correlation_min_count

        # Statistics
        self.prefetch_requests_generated: int = 0
        self.prefetch_requests_issued: int = 0
        self.hits: int = 0
        self.misses: int = 0

    def record_access(self, address: int, size: int = 64):
        """Record an access for pattern analysis

        Args:
            address: Accessed memory address
            size: Size of access in bytes
        """
        if not self.enabled:
            return

        self.history.append((address, size))
        self._update_stride_detector(address)
        self._update_correlation(address)

    def _update_stride_detector(self, address: int):
        """Update stride detection based on new access

        Args:
            address: Current address
        """
        if len(self.history) < 2:
            return

        prev_addr, _ = self.history[-2]
        stride = address - prev_addr

        if stride == 0:
            return

        # Update stride table for previous address
        if prev_addr in self.stride_detector:
            prev_prev, prev_stride, count = self.stride_detector[prev_addr]
            if prev_stride == stride:
                # Consistent stride
                self.stride_detector[prev_addr] = (prev_addr, stride, count + 1)
            else:
                # Stride changed
                self.stride_detector[prev_addr] = (prev_addr, stride, 1)
        else:
            self.stride_detector[prev_addr] = (prev_addr, stride, 1)

        # Update current address entry for future lookups
        self.stride_detector[address] = (prev_addr, stride, 1)

    def _update_correlation(self, address: int):
        """Update correlation table based on new access

        Args:
            address: Current address
        """
        if len(self.history) < 2:
            return

        prev_addr, _ = self.history[-2]

        # Initialize correlation tracking for previous address
        if prev_addr not in self.correlation_counts:
            self.correlation_counts[prev_addr] = {}

        # Increment count for this correlation
        if address not in self.correlation_counts[prev_addr]:
            self.correlation_counts[prev_addr][address] = 0
        self.correlation_counts[prev_addr][address] += 1

        # Rebuild correlation table with frequent accesses
        if len(self.correlation_counts[prev_addr]) > 10:
            # Keep only top 5 most frequent
            sorted_addrs = sorted(
                self.correlation_counts[prev_addr].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            self.correlation_table[prev_addr] = [addr for addr, _ in sorted_addrs]
        else:
            self.correlation_table[prev_addr] = list(self.correlation_counts[prev_addr].keys())

    def get_prefetch_requests(
        self,
        current_addr: int,
        num_requests: int = 4,
    ) -> List[PrefetchRequest]:
        """Generate prefetch requests based on current policy

        Args:
            current_addr: Current memory address being accessed
            num_requests: Number of prefetch requests to generate

        Returns:
            List of prefetch requests
        """
        if not self.enabled:
            return []

        requests = []

        if self.policy == PrefetchPolicy.SEQUENTIAL:
            requests.extend(self._sequential_prefetch(current_addr, num_requests))
        elif self.policy == PrefetchPolicy.STRIDE:
            requests.extend(self._stride_prefetch(current_addr, num_requests))
        elif self.policy == PrefetchPolicy.CORRELATION:
            requests.extend(self._correlation_prefetch(current_addr, num_requests))

        self.prefetch_requests_generated += len(requests)
        return requests

    def _sequential_prefetch(
        self,
        addr: int,
        num: int,
    ) -> List[PrefetchRequest]:
        """Generate sequential prefetch requests

        Prefetches consecutive cache-line-sized blocks.

        Args:
            addr: Base address
            num: Number of prefetches

        Returns:
            List of prefetch requests
        """
        cache_line_size = 64
        base = addr & ~(cache_line_size - 1)

        requests = []
        for i in range(1, num + 1):
            prefetch_addr = base + i * cache_line_size
            requests.append(PrefetchRequest(
                address=prefetch_addr,
                size=cache_line_size,
                priority=128,
                confidence=0.9,
                policy=self.policy,
            ))

        return requests

    def _stride_prefetch(
        self,
        addr: int,
        num: int,
    ) -> List[PrefetchRequest]:
        """Generate stride-based prefetch requests

        Detects regular access patterns and follows them.

        Args:
            addr: Current address
            num: Number of prefetches

        Returns:
            List of prefetch requests
        """
        if addr in self.stride_detector:
            prev_addr, stride, count = self.stride_detector[addr]

            # Calculate confidence based on consistency
            confidence = min(1.0, count / 10.0)

            # Accept both positive and negative strides with sufficient confidence
            if stride != 0 and confidence >= self.stride_confidence_threshold:
                requests = []
                for i in range(1, num + 1):
                    prefetch_addr = addr + stride * i
                    requests.append(PrefetchRequest(
                        address=prefetch_addr,
                        size=64,
                        priority=192,  # Higher priority for stride
                        confidence=confidence,
                        policy=self.policy,
                    ))
                return requests

        # Fallback to sequential if no stride detected
        return self._sequential_prefetch(addr, num)

    def _correlation_prefetch(
        self,
        addr: int,
        num: int,
    ) -> List[PrefetchRequest]:
        """Generate correlation-based prefetch requests

        Uses learned address correlations to predict next accesses.

        Args:
            addr: Current address
            num: Number of prefetches

        Returns:
            List of prefetch requests
        """
        if addr in self.correlation_table:
            next_addrs = self.correlation_table[addr]

            requests = []
            for i, next_addr in enumerate(next_addrs[:num]):
                # Calculate confidence based on occurrence count
                if addr in self.correlation_counts:
                    count = self.correlation_counts[addr].get(next_addr, 0)
                    confidence = min(1.0, count / 10.0)
                else:
                    confidence = 0.7

                requests.append(PrefetchRequest(
                    address=next_addr,
                    size=64,
                    priority=160,
                    confidence=confidence,
                    policy=self.policy,
                ))

            return requests

        return []

    def mark_prefetch_hit(self, address: int):
        """Record that a prefetch was useful

        Args:
            address: Address that was prefetched and later accessed
        """
        self.hits += 1

    def mark_prefetch_miss(self, address: int):
        """Record that a prefetch was not useful

        Args:
            address: Address that was prefetched but not accessed
        """
        self.misses += 1

    def set_policy(self, policy: str):
        """Set the prefetch policy

        Args:
            policy: One of PrefetchPolicy constants
        """
        if policy in [PrefetchPolicy.NONE, PrefetchPolicy.SEQUENTIAL,
                      PrefetchPolicy.STRIDE, PrefetchPolicy.CORRELATION]:
            self.policy = policy
        else:
            _logger.warning(f"Unknown prefetch policy: {policy}")

    def enable(self):
        """Enable prefetching"""
        self.enabled = True

    def disable(self):
        """Disable prefetching"""
        self.enabled = False

    def reset(self):
        """Reset all state and statistics"""
        self.history.clear()
        self.stride_detector.clear()
        self.correlation_table.clear()
        self.correlation_counts.clear()
        self.prefetch_requests_generated = 0
        self.prefetch_requests_issued = 0
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict:
        """Get prefetch statistics

        Returns:
            Dictionary with statistics
        """
        total = self.hits + self.misses
        accuracy = self.hits / total if total > 0 else 0.0

        return {
            'policy': self.policy,
            'enabled': self.enabled,
            'history_size': len(self.history),
            'stride_patterns': len(self.stride_detector),
            'correlations': len(self.correlation_table),
            'requests_generated': self.prefetch_requests_generated,
            'requests_issued': self.prefetch_requests_issued,
            'hits': self.hits,
            'misses': self.misses,
            'accuracy': accuracy,
        }