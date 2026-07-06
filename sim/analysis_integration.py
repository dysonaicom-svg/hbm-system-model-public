"""Analysis Integration Module for HBMSimulator"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from model.analysis.bottleneck_detector import (
    BottleneckDetector,
    BottleneckReport,
)
from model.analysis.hotspot_detector import (
    HotspotDetector,
    HotspotReport,
)
from model.analysis.latency_analyzer import (
    LatencyDistribution,
    LatencyStats,
)
from model.analysis.dvfs_analyzer import (
    DVFSAnalyzer,
    DVFSResult,
)
from model.analysis.power_performance_curve import (
    PowerPerformanceCurve,
)
from model.analysis.optimizer import (
    Optimizer,
    OptimizationSuggestion,
)


@dataclass
class AnalysisReport:
    """Complete analysis report combining all analysis results"""
    bottleneck_report: BottleneckReport
    hotspot_report: HotspotReport
    latency_stats: LatencyStats
    dvfs_results: List[DVFSResult]
    power_performance_curve: PowerPerformanceCurve
    suggestions: List[OptimizationSuggestion]
    analysis_time_cycles: int = 0

    def to_dict(self) -> Dict:
        """Convert report to dictionary for JSON export"""
        return {
            "bottlenecks": {
                "total": self.bottleneck_report.get_summary()["total_bottlenecks"],
                "by_type": self.bottleneck_report.get_summary()["by_type"],
                "critical": self.bottleneck_report.get_summary()["critical_count"],
            },
            "latency": {
                "min_ns": self.latency_stats.min_ns,
                "max_ns": self.latency_stats.max_ns,
                "mean_ns": self.latency_stats.mean_ns,
                "p50_ns": self.latency_stats.p50_ns,
                "p90_ns": self.latency_stats.p90_ns,
                "p99_ns": self.latency_stats.p99_ns,
                "sample_count": self.latency_stats.sample_count,
            },
            "dvfs": [
                {
                    "frequency_gtps": r.frequency_gtps,
                    "voltage_v": r.voltage_v,
                    "power_w": r.power_w,
                    "bandwidth_gbps": r.bandwidth_gbps,
                    "efficiency": r.efficiency,
                }
                for r in self.dvfs_results
            ],
            "suggestions": [
                {
                    "category": s.category,
                    "priority": s.priority,
                    "description": s.description,
                    "expected_improvement": s.expected_improvement,
                }
                for s in self.suggestions
            ],
            "analysis_time_cycles": self.analysis_time_cycles,
        }


class SimulatorAnalyzer:
    """Integrated analyzer for HBMSimulator"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.bottleneck_detector = BottleneckDetector()
        self.hotspot_detector = HotspotDetector()
        self.latency_distribution = LatencyDistribution()
        self.dvfs_analyzer = DVFSAnalyzer()
        self.power_curve = PowerPerformanceCurve()
        self.optimizer = Optimizer()
        self.request_trace: List[tuple] = []

    def record_request(self, address: int, is_read: bool, latency_ns: float):
        """Record a request for analysis"""
        if not self.enabled:
            return
        self.request_trace.append((address, is_read))
        self.latency_distribution.add_sample(latency_ns)

    def analyze(self, metrics: Dict, analysis_cycles: int = 0) -> AnalysisReport:
        """Run full analysis and generate report"""
        if not self.enabled:
            return None

        bottleneck_report = self.bottleneck_detector.detect(metrics)
        hotspot_report = self.hotspot_detector.detect(self.request_trace)
        latency_stats = self.latency_distribution.analyze()

        self.dvfs_analyzer.analyze_frequency_sweep((8.0, 16.0, 2.0))
        dvfs_results = self.dvfs_analyzer.results
        self.power_curve.generate_from_dvfs(self.dvfs_analyzer)

        suggestions = self.optimizer.generate_suggestions(bottleneck_report, dvfs_results)

        return AnalysisReport(
            bottleneck_report=bottleneck_report,
            hotspot_report=hotspot_report,
            latency_stats=latency_stats,
            dvfs_results=dvfs_results,
            power_performance_curve=self.power_curve,
            suggestions=suggestions,
            analysis_time_cycles=analysis_cycles,
        )

    def reset(self):
        """Reset all analysis state"""
        self.request_trace.clear()
        self.latency_distribution = LatencyDistribution()
