"""Hotspot Detection Module for HBM4 Performance Analysis"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class HotspotType(Enum):
    """Types of hotspots"""
    ADDRESS = "address"
    BANK = "bank"
    CHANNEL = "channel"
    ROW = "row"


@dataclass
class HotspotData:
    """Represents a detected hotspot"""
    hotspot_type: HotspotType
    address: int = 0
    bank_id: int = 0
    channel_id: int = 0
    access_count: int = 0
    heat_level: float = 0.0  # 0.0 to 1.0


@dataclass
class HeatmapData:
    """Heatmap representation of hotspots"""
    type: HotspotType
    data: Dict[str, float]  # location -> heat level
    max_value: float = 0.0


class HotspotReport:
    """Report of detected hotspots"""
    def __init__(self):
        self.hotspots: List[HotspotData] = []
        self.heatmaps: Dict[HotspotType, HeatmapData] = {}

    def add(self, hotspot: HotspotData):
        self.hotspots.append(hotspot)

    def get_top_n(self, n: int = 10) -> List[HotspotData]:
        return sorted(self.hotspots, key=lambda h: h.access_count, reverse=True)[:n]

    def generate_heatmap(self) -> Dict[HotspotType, HeatmapData]:
        for htype in HotspotType:
            type_hotspots = [h for h in self.hotspots if h.hotspot_type == htype]
            if not type_hotspots:
                continue
            max_count = max(h.access_count for h in type_hotspots)
            data = {}
            for h in type_hotspots:
                key = str(h.address if htype == HotspotType.ADDRESS else
                         h.bank_id if htype == HotspotType.BANK else h.channel_id)
                data[key] = h.access_count / max_count if max_count > 0 else 0
            self.heatmaps[htype] = HeatmapData(type=htype, data=data, max_value=max_count)
        return self.heatmaps


class HotspotDetector:
    """Detects hotspots in HBM4 access patterns"""

    def __init__(self, threshold_percentile: float = 95.0):
        self.threshold_percentile = threshold_percentile

    def detect_from_trace(self, trace: List[Tuple[int, bool]]) -> HotspotReport:
        """Detect hotspots from request trace (address, is_read)"""
        report = HotspotReport()
        address_counts = defaultdict(int)

        for addr, _ in trace:
            address_counts[addr] += 1

        if not address_counts:
            return report

        # Calculate threshold
        counts = sorted(address_counts.values(), reverse=True)
        threshold_idx = int(len(counts) * self.threshold_percentile / 100)
        threshold = counts[min(threshold_idx, len(counts) - 1)]
        max_count = max(counts)

        for addr, count in address_counts.items():
            if count >= threshold:
                report.add(HotspotData(
                    hotspot_type=HotspotType.ADDRESS,
                    address=addr,
                    access_count=count,
                    heat_level=count / max_count if max_count > 0 else 0
                ))

        return report