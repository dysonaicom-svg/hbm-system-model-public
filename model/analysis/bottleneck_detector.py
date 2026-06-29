"""Bottleneck Detection Module for HBM4 Performance Analysis"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional


class BottleneckType(Enum):
    """Types of performance bottlenecks"""
    BANK_CONFLICT = "bank_conflict"
    QUEUE_BLOCKING = "queue_blocking"
    CHANNEL_UTILIZATION = "channel_utilization"
    QUEUE_OVERFLOW = "queue_overflow"
    REFRESH_CONFLICT = "refresh_conflict"
    THERMAL_THROTTLE = "thermal_throttle"


@dataclass
class Bottleneck:
    """Represents a detected performance bottleneck"""
    bottleneck_type: BottleneckType
    severity: float  # 0.0 to 1.0
    location: str    # e.g., "channel_0.bank_3"
    description: str
    metrics: Optional[Dict] = None


class BottleneckReport:
    """Report of detected bottlenecks"""
    def __init__(self):
        self.bottlenecks: List[Bottleneck] = []

    def add(self, bottleneck: Bottleneck):
        self.bottlenecks.append(bottleneck)

    def get_summary(self) -> Dict:
        return {
            "total_bottlenecks": len(self.bottlenecks),
            "by_type": self._count_by_type(),
            "critical_count": len([b for b in self.bottlenecks if b.severity > 0.7])
        }

    def _count_by_type(self) -> Dict[str, int]:
        counts = {}
        for b in self.bottlenecks:
            key = b.bottleneck_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts


class BottleneckDetector:
    """Detects performance bottlenecks in HBM4 systems"""

    def __init__(self, conflict_threshold: float = 0.7, utilization_threshold: float = 0.9):
        self.conflict_threshold = conflict_threshold
        self.utilization_threshold = utilization_threshold

    def detect(self, metrics: Dict) -> BottleneckReport:
        """Detect bottlenecks from performance metrics"""
        report = BottleneckReport()

        for channel_name, channel_metrics in metrics.items():
            # Check bank conflicts
            conflict_rate = channel_metrics.get("bank_conflict_rate", 0)
            if conflict_rate > self.conflict_threshold:
                report.add(Bottleneck(
                    bottleneck_type=BottleneckType.BANK_CONFLICT,
                    severity=conflict_rate,
                    location=f"{channel_name}",
                    description=f"High bank conflict rate: {conflict_rate:.1%}"
                ))

            # Check channel utilization
            util = channel_metrics.get("utilization", 0)
            if util > self.utilization_threshold:
                report.add(Bottleneck(
                    bottleneck_type=BottleneckType.CHANNEL_UTILIZATION,
                    severity=util,
                    location=f"{channel_name}",
                    description=f"High channel utilization: {util:.1%}"
                ))

        return report
