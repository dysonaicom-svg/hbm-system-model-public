"""Analysis Report Generator

Generates comprehensive analysis reports from all analysis modules.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class ReportMetadata:
    """Report metadata"""
    title: str
    timestamp: str
    version: str = "1.0.0"


@dataclass
class BandwidthMetrics:
    """Bandwidth performance metrics"""
    peak_gbps: float
    achieved_gbps: float
    efficiency_percent: float
    channel_utilization: Dict[int, float]


@dataclass
class LatencyMetrics:
    """Latency performance metrics"""
    min_ns: float
    max_ns: float
    avg_ns: float
    p50_ns: float
    p90_ns: float
    p99_ns: float
    std_dev_ns: float


@dataclass
class BottleneckReport:
    """Bottleneck analysis report"""
    bottlenecks: List[Dict[str, Any]]
    severity: str  # critical, warning, info
    recommendations: List[str]


@dataclass
class HotspotReport:
    """Hotspot analysis report"""
    hotspots: List[Dict[str, Any]]
    heatmap_data: Dict[str, Dict[str, float]]
    mitigation_suggestions: List[str]


class AnalysisReport:
    """Comprehensive analysis report"""

    def __init__(self, title: str = "HBM4 Analysis Report"):
        self.metadata = ReportMetadata(
            title=title,
            timestamp=datetime.now().isoformat()
        )
        self.bandwidth: Optional[BandwidthMetrics] = None
        self.latency: Optional[LatencyMetrics] = None
        self.bottlenecks: Optional[BottleneckReport] = None
        self.hotspots: Optional[HotspotReport] = None
        self.dvfs_state: Dict[str, Any] = {}
        self.compliance_status: Dict[str, Any] = {}
        self.raw_data: Dict[str, Any] = {}

    def set_bandwidth(self, peak: float, achieved: float, efficiency: float,
                     channel_util: Dict[int, float]) -> None:
        self.bandwidth = BandwidthMetrics(
            peak_gbps=peak,
            achieved_gbps=achieved,
            efficiency_percent=efficiency,
            channel_utilization=channel_util
        )

    def set_latency(self, stats: Dict[str, float]) -> None:
        self.latency = LatencyMetrics(
            min_ns=stats.get("min_ns", 0),
            max_ns=stats.get("max_ns", 0),
            avg_ns=stats.get("mean_ns", 0),
            p50_ns=stats.get("p50_ns", 0),
            p90_ns=stats.get("p90_ns", 0),
            p99_ns=stats.get("p99_ns", 0),
            std_dev_ns=stats.get("std_dev_ns", 0)
        )

    def set_bottlenecks(self, bottlenecks: List[Dict], severity: str,
                       recommendations: List[str]) -> None:
        self.bottlenecks = BottleneckReport(
            bottlenecks=[asdict(b) if hasattr(b, '__dict__') else b for b in bottlenecks],
            severity=severity,
            recommendations=recommendations
        )

    def set_hotspots(self, hotspots: List[Dict], heatmap: Dict,
                    suggestions: List[str]) -> None:
        self.hotspots = HotspotReport(
            hotspots=hotspots,
            heatmap_data=heatmap,
            mitigation_suggestions=suggestions
        )

    def set_dvfs_state(self, state: Dict[str, Any]) -> None:
        self.dvfs_state = state

    def set_compliance(self, status: Dict[str, Any]) -> None:
        self.compliance_status = status

    def add_custom_data(self, key: str, data: Any) -> None:
        self.raw_data[key] = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": asdict(self.metadata),
            "bandwidth": asdict(self.bandwidth) if self.bandwidth else None,
            "latency": asdict(self.latency) if self.latency else None,
            "bottlenecks": asdict(self.bottlenecks) if self.bottlenecks else None,
            "hotspots": asdict(self.hotspots) if self.hotspots else None,
            "dvfs": self.dvfs_state,
            "compliance": self.compliance_status,
            "custom": self.raw_data
        }

    def to_json(self, filepath: str, indent: int = 2) -> None:
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent)

    def to_text(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"  {self.metadata.title}")
        lines.append("=" * 60)
        lines.append(f"Generated: {self.metadata.timestamp}")
        lines.append("")

        if self.bandwidth:
            lines.append("BANDWIDTH METRICS")
            lines.append("-" * 40)
            lines.append(f"  Peak:     {self.bandwidth.peak_gbps:.2f} GB/s")
            lines.append(f"  Achieved: {self.bandwidth.achieved_gbps:.2f} GB/s")
            lines.append(f"  Efficiency: {self.bandwidth.efficiency_percent:.1f}%")
            lines.append("")

        if self.latency:
            lines.append("LATENCY METRICS")
            lines.append("-" * 40)
            lines.append(f"  Min:   {self.latency.min_ns:.2f} ns")
            lines.append(f"  Avg:   {self.latency.avg_ns:.2f} ns")
            lines.append(f"  Max:   {self.latency.max_ns:.2f} ns")
            lines.append(f"  P99:   {self.latency.p99_ns:.2f} ns")
            lines.append(f"  StdDev: {self.latency.std_dev_ns:.2f} ns")
            lines.append("")

        if self.bottlenecks:
            lines.append("BOTTLENECKS")
            lines.append("-" * 40)
            lines.append(f"  Severity: {self.bottlenecks.severity}")
            for b in self.bottlenecks.bottlenecks[:5]:
                lines.append(f"  - {b.get('type', 'unknown')}: {b.get('description', '')}")
            lines.append("")

        if self.hotspots:
            lines.append("HOTSPOTS")
            lines.append("-" * 40)
            for h in self.hotspots.hotspots[:5]:
                lines.append(f"  - Bank {h.get('bank_id', '?')}: {h.get('heat_level', 0):.2%}")
            lines.append("")

        return "\n".join(lines)


class ReportGenerator:
    """Factory for creating analysis reports"""

    def __init__(self):
        self.reports: List[AnalysisReport] = []

    def create_report(self, title: str = "HBM4 Analysis Report") -> AnalysisReport:
        report = AnalysisReport(title)
        self.reports.append(report)
        return report

    def generate_summary(self) -> Dict[str, Any]:
        if not self.reports:
            return {"reports": 0}

        return {
            "reports": len(self.reports),
            "latest": self.reports[-1].metadata.title if self.reports else None
        }
