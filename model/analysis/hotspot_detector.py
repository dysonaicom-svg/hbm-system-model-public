"""Hotspot Detection Module for HBM4 Performance Analysis"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Callable
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
    row_id: int = 0
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
        self._heatmaps: Dict[HotspotType, HeatmapData] = {}

    def add(self, hotspot: HotspotData):
        self.hotspots.append(hotspot)

    def get_top_n(self, n: int = 10) -> List[HotspotData]:
        return sorted(self.hotspots, key=lambda h: h.access_count, reverse=True)[:n]

    def get_heatmap(self) -> Dict[HotspotType, HeatmapData]:
        """Get heatmap data for all hotspot types"""
        return self._heatmaps

    def generate_heatmap(self) -> Dict[HotspotType, HeatmapData]:
        """Generate heatmap data for all hotspot types (alias for get_heatmap)"""
        for htype in HotspotType:
            type_hotspots = [h for h in self.hotspots if h.hotspot_type == htype]
            if not type_hotspots:
                continue
            max_count = max(h.access_count for h in type_hotspots)
            data = {}
            for h in type_hotspots:
                if htype == HotspotType.ADDRESS:
                    key = str(h.address)
                elif htype == HotspotType.BANK:
                    key = str(h.bank_id)
                elif htype == HotspotType.CHANNEL:
                    key = str(h.channel_id)
                else:  # ROW
                    key = str(h.row_id)
                data[key] = h.access_count / max_count if max_count > 0 else 0
            self._heatmaps[htype] = HeatmapData(type=htype, data=data, max_value=max_count)
        return self._heatmaps


class HotspotDetector:
    """Detects hotspots in HBM4 access patterns"""

    def __init__(self, threshold_percentile: float = 95.0):
        self.threshold_percentile = threshold_percentile

    def detect(self, trace: List[Tuple[int, bool]],
               decoder: Optional[Callable[[int], Dict[str, int]]] = None) -> HotspotReport:
        """Detect hotspots from request trace (address, is_read)

        Args:
            trace: List of (address, is_read) tuples
            decoder: Optional function to decode address into components
                    Returns dict with 'bank_id', 'channel_id', 'row_id' keys
        """
        report = HotspotReport()
        address_counts = defaultdict(int)
        bank_counts = defaultdict(int)
        channel_counts = defaultdict(int)
        row_counts = defaultdict(int)

        for addr, _ in trace:
            address_counts[addr] += 1

            if decoder:
                decoded = decoder(addr)
                bank_counts[decoded.get('bank_id', 0)] += 1
                channel_counts[decoded.get('channel_id', 0)] += 1
                row_counts[decoded.get('row_id', 0)] += 1

        if not address_counts:
            return report

        # Build all count dictionaries
        all_counts = {
            HotspotType.ADDRESS: address_counts,
            HotspotType.BANK: bank_counts,
            HotspotType.CHANNEL: channel_counts,
            HotspotType.ROW: row_counts,
        }

        # Calculate threshold from address counts
        counts = sorted(address_counts.values(), reverse=True)
        threshold_idx = int(len(counts) * self.threshold_percentile / 100)
        threshold = counts[min(threshold_idx, len(counts) - 1)] if counts else 0
        max_count = max(counts) if counts else 0

        # Add address hotspots
        for addr, count in address_counts.items():
            if count >= threshold:
                report.add(HotspotData(
                    hotspot_type=HotspotType.ADDRESS,
                    address=addr,
                    access_count=count,
                    heat_level=count / max_count if max_count > 0 else 0
                ))

        # Add bank/channel/row hotspots if decoder provided
        if decoder:
            for htype, counts_dict in [(HotspotType.BANK, bank_counts),
                                         (HotspotType.CHANNEL, channel_counts),
                                         (HotspotType.ROW, row_counts)]:
                if counts_dict:
                    max_c = max(counts_dict.values())
                    threshold_c = counts_dict[sorted(counts_dict.values(), reverse=True)[
                        min(threshold_idx, len(counts_dict) - 1)]] if counts_dict else 0
                    for loc_id, count in counts_dict.items():
                        if count >= threshold_c:
                            kwargs = {'hotspot_type': htype, 'access_count': count,
                                      'heat_level': count / max_c if max_c > 0 else 0}
                            if htype == HotspotType.BANK:
                                kwargs['bank_id'] = loc_id
                            elif htype == HotspotType.CHANNEL:
                                kwargs['channel_id'] = loc_id
                            else:
                                kwargs['row_id'] = loc_id
                            report.add(HotspotData(**kwargs))

        return report

    def detect_from_trace(self, trace: List[Tuple[int, bool]]) -> HotspotReport:
        """Detect hotspots from request trace (address, is_read) - legacy alias"""
        return self.detect(trace, decoder=None)