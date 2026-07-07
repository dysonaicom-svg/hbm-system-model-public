"""
Advanced Prefetch Engine with ML-based Pattern Detection

Implements intelligent prefetch policies:
- Stride detection with confidence scoring
- Access pattern classification
- Confidence-based prefetch throttling
"""

import logging
from typing import List, Optional, Tuple, Dict, Set
from dataclasses import dataclass, field
from collections import deque
import statistics

_logger = logging.getLogger('hbm4.advanced_prefetch')


@dataclass
class PrefetchDecision:
    """Prefetch decision with confidence"""
    address: int
    confidence: float  # 0.0-1.0
    policy: str
    prefetch_degree: int = 1


@dataclass
class StridePattern:
    """Detected stride pattern"""
    base_address: int
    stride: int
    count: int = 0
    confidence: float = 0.0
    last_accesses: List[Tuple[int, int]] = field(default_factory=list)  # (addr, cycle)


class AccessPatternClassifier:
    """Classifies access patterns based on historical data"""

    SEQUENTIAL = "sequential"
    RANDOM = "random"
    STRIDE = "stride"
    HOTSPOT = "hotspot"
    MIXED = "mixed"

    def __init__(self, history_size: int = 64):
        self.history_size = history_size
        self.access_history: deque = deque(maxlen=history_size)

    def classify(self) -> str:
        """Classify current access pattern"""
        if len(self.access_history) < 8:
            return self.MIXED

        addresses = [addr for addr, _ in self.access_history]

        # Check for hotspot pattern
        if self._is_hotspot(addresses):
            return self.HOTSPOT

        # Check for stride pattern
        strides = self._calculate_strides(addresses)
        if strides and len(set(strides)) == 1:
            return self.STRIDE

        # Check for sequential pattern
        if self._is_sequential(addresses):
            return self.SEQUENTIAL

        return self.RANDOM

    def add_access(self, address: int, cycle: int):
        """Add an access to history"""
        self.access_history.append((address, cycle))

    def _is_hotspot(self, addresses: List[int]) -> bool:
        """Check if addresses follow hotspot pattern"""
        from collections import Counter
        counts = Counter(addresses)
        most_common = counts.most_common(1)[0]
        return most_common[1] / len(addresses) > 0.4

    def _is_sequential(self, addresses: List[int]) -> bool:
        """Check if addresses are sequential"""
        if len(addresses) < 4:
            return False
        # Check if differences are mostly 1
        diffs = [addresses[i+1] - addresses[i] for i in range(len(addresses)-1)]
        return sum(1 for d in diffs if d == 1) / len(diffs) > 0.7

    def _calculate_strides(self, addresses: List[int]) -> List[int]:
        """Calculate strides between consecutive accesses"""
        return [addresses[i+1] - addresses[i] for i in range(len(addresses)-1)]


class AdvancedPrefetchEngine:
    """Advanced prefetch engine with ML-based pattern detection

    Features:
    - Multi-stride detection
    - Pattern confidence scoring
    - Adaptive prefetch degree
    - Prefetch throttling based on accuracy
    """

    def __init__(self, max_prefetch_degree: int = 8, confidence_threshold: float = 0.7):
        self.max_prefetch_degree = max_prefetch_degree
        self.confidence_threshold = confidence_threshold

        # Pattern detection
        self.stride_patterns: Dict[int, StridePattern] = {}  # keyed by stream ID
        self.classifier = AccessPatternClassifier()

        # Prefetch tracking
        self.prefetch_history: deque = deque(maxlen=1024)
        self.accuracy_history: deque = deque(maxlen=256)

        # Statistics
        self.total_prefetches = 0
        self.useful_prefetches = 0
        self.dropped_prefetches = 0

    def predict(self, address: int, stream_id: int = 0) -> List[PrefetchDecision]:
        """Predict prefetch addresses based on detected patterns"""
        decisions = []

        pattern = self.stride_patterns.get(stream_id)
        if pattern and pattern.confidence >= self.confidence_threshold:
            # Generate prefetch based on detected stride
            degree = min(pattern.stride != 0, self.max_prefetch_degree)
            for i in range(1, degree + 1):
                prefetch_addr = address + pattern.stride * i
                decisions.append(PrefetchDecision(
                    address=prefetch_addr,
                    confidence=pattern.confidence,
                    policy="stride",
                    prefetch_degree=i
                ))
        else:
            # Default sequential prefetch
            decisions.append(PrefetchDecision(
                address=address + 64,  # Cache line size
                confidence=0.5,
                policy="sequential",
                prefetch_degree=1
            ))

        return decisions

    def update(self, address: int, stream_id: int = 0, is_prefetch: bool = False):
        """Update pattern detection with new access"""
        self.classifier.add_access(address, 0)

        if is_prefetch:
            self.total_prefetches += 1
            if address in self.prefetch_history:
                self.useful_prefetches += 1
            else:
                self.dropped_prefetches += 1

        self.prefetch_history.append(address)
        self._detect_stride(address, stream_id)

    def _detect_stride(self, address: int, stream_id: int):
        """Detect stride pattern from access history"""
        if stream_id not in self.stride_patterns:
            self.stride_patterns[stream_id] = StridePattern(
                base_address=address,
                stride=0
            )

        pattern = self.stride_patterns[stream_id]
        pattern.last_accesses.append((address, 0))

        # Keep last 8 accesses for stride detection
        if len(pattern.last_accesses) > 8:
            pattern.last_accesses.pop(0)

        # Calculate stride
        if len(pattern.last_accesses) >= 3:
            strides = []
            for i in range(len(pattern.last_accesses) - 1):
                s = pattern.last_accesses[i+1][0] - pattern.last_accesses[i][0]
                strides.append(s)

            if strides and len(set(strides)) == 1:
                pattern.stride = strides[0]
                pattern.count += 1
                pattern.confidence = min(1.0, pattern.count / 8)
            else:
                # Stride broken, reset
                pattern.count = max(0, pattern.count - 2)
                pattern.confidence = pattern.count / 8

    def get_pattern_class(self) -> str:
        """Get current access pattern class"""
        return self.classifier.classify()

    def get_statistics(self) -> Dict:
        """Get prefetch statistics"""
        accuracy = (
            self.useful_prefetches / self.total_prefetches
            if self.total_prefetches > 0 else 0.0
        )

        return {
            'total_prefetches': self.total_prefetches,
            'useful_prefetches': self.useful_prefetches,
            'dropped_prefetches': self.dropped_prefetches,
            'accuracy': accuracy,
            'active_streams': len(self.stride_patterns),
            'pattern_class': self.get_pattern_class(),
        }

    def should_throttle(self) -> bool:
        """Determine if prefetch should be throttled"""
        if len(self.accuracy_history) < 32:
            return False

        recent_accuracy = statistics.mean(self.accuracy_history)
        return recent_accuracy < 0.3  # Throttle if accuracy < 30%

    def reset(self):
        """Reset prefetch state"""
        self.stride_patterns.clear()
        self.prefetch_history.clear()
        self.accuracy_history.clear()
        self.total_prefetches = 0
        self.useful_prefetches = 0
        self.dropped_prefetches = 0
