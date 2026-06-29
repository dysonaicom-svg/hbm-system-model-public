"""Performance Analysis Module for HBM4"""

from model.analysis.bottleneck_detector import (
    Bottleneck,
    BottleneckType,
    BottleneckReport,
    BottleneckDetector,
)
from model.analysis.hotspot_detector import (
    HotspotData,
    HotspotType,
    HeatmapData,
    HotspotReport,
    HotspotDetector,
)
from model.analysis.latency_analyzer import (
    LatencyStats,
    LatencyDistribution,
)
from model.analysis.dvfs_analyzer import (
    DVFSAnalyzer,
    DVFSResult,
    DVFSSpeedGrade,
    ParetoPoint,
)

__all__ = [
    # Bottleneck
    "Bottleneck",
    "BottleneckType",
    "BottleneckReport",
    "BottleneckDetector",
    # Hotspot
    "HotspotData",
    "HotspotType",
    "HeatmapData",
    "HotspotReport",
    "HotspotDetector",
    # Latency
    "LatencyStats",
    "LatencyDistribution",
    # DVFS
    "DVFSAnalyzer",
    "DVFSResult",
    "DVFSSpeedGrade",
    "ParetoPoint",
]