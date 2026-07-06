"""Optimization Suggestions Module for HBM4 Performance Analysis"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from model.analysis.bottleneck_detector import BottleneckReport, BottleneckType
from model.analysis.dvfs_analyzer import DVFSAnalyzer, DVFSResult, DVFSSpeedGrade


@dataclass
class OptimizationSuggestion:
    """A suggested optimization"""
    category: str  # "frequency", "addressing", "scheduling"
    priority: int  # 1 = highest
    description: str
    expected_improvement: str
    config_change: Optional[Dict] = None


class Optimizer:
    """Generates optimization suggestions based on analysis results"""

    def __init__(self):
        self.suggestions: List[OptimizationSuggestion] = []

    def generate_suggestions(
        self,
        bottleneck_report: BottleneckReport,
        dvfs_results: List[DVFSResult]
    ) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions based on bottleneck and DVFS analysis"""
        suggestions = []

        # Analyze bottlenecks and generate suggestions
        suggestions.extend(self._analyze_bottlenecks(bottleneck_report))

        # Generate DVFS-based suggestions
        suggestions.extend(self._analyze_dvfs(dvfs_results))

        # Sort by priority (lower number = higher priority)
        suggestions.sort(key=lambda s: s.priority)

        self.suggestions = suggestions
        return suggestions

    def _analyze_bottlenecks(self, report: BottleneckReport) -> List[OptimizationSuggestion]:
        """Analyze bottlenecks and generate scheduling/addressing suggestions"""
        suggestions = []

        if not report.bottlenecks:
            return suggestions

        # Check for high-severity bank conflicts
        bank_conflicts = [
            b for b in report.bottlenecks
            if b.bottleneck_type == BottleneckType.BANK_CONFLICT and b.severity > 0.7
        ]
        if bank_conflicts:
            suggestions.append(OptimizationSuggestion(
                category="scheduling",
                priority=1,
                description="High bank conflict detected - consider optimizing address mapping",
                expected_improvement="15-25% latency reduction"
            ))

        # Check for queue blocking issues
        queue_blocking = [
            b for b in report.bottlenecks
            if b.bottleneck_type == BottleneckType.QUEUE_BLOCKING
        ]
        if queue_blocking:
            suggestions.append(OptimizationSuggestion(
                category="scheduling",
                priority=2,
                description="Queue blocking detected - consider increasing queue depth",
                expected_improvement="10-15% throughput improvement"
            ))

        # Check for channel utilization issues
        channel_util = [
            b for b in report.bottlenecks
            if b.bottleneck_type == BottleneckType.CHANNEL_UTILIZATION
        ]
        if channel_util:
            suggestions.append(OptimizationSuggestion(
                category="addressing",
                priority=2,
                description="High channel utilization - consider redistributing load across channels",
                expected_improvement="20-30% bandwidth improvement"
            ))

        # Check for queue overflow
        queue_overflow = [
            b for b in report.bottlenecks
            if b.bottleneck_type == BottleneckType.QUEUE_OVERFLOW
        ]
        if queue_overflow:
            suggestions.append(OptimizationSuggestion(
                category="scheduling",
                priority=2,
                description="Queue overflow detected - consider increasing buffer size",
                expected_improvement="5-10% request completion rate"
            ))

        # Check for refresh conflicts
        refresh_conflicts = [
            b for b in report.bottlenecks
            if b.bottleneck_type == BottleneckType.REFRESH_CONFLICT
        ]
        if refresh_conflicts:
            suggestions.append(OptimizationSuggestion(
                category="scheduling",
                priority=3,
                description="Refresh conflicts detected - consider adjusting refresh timing",
                expected_improvement="10-20% latency reduction during refresh"
            ))

        # Check for thermal throttling
        thermal_throttle = [
            b for b in report.bottlenecks
            if b.bottleneck_type == BottleneckType.THERMAL_THROTTLE
        ]
        if thermal_throttle:
            suggestions.append(OptimizationSuggestion(
                category="frequency",
                priority=3,
                description="Thermal throttling active - consider reducing frequency or improving cooling",
                expected_improvement="Sustained performance by avoiding throttle cycles"
            ))

        return suggestions

    def _analyze_dvfs(self, dvfs_results: List[DVFSResult]) -> List[OptimizationSuggestion]:
        """Generate DVFS-based frequency optimization suggestions"""
        suggestions = []

        if not dvfs_results:
            return suggestions

        # Find best efficiency configuration
        best_eff = max(dvfs_results, key=lambda r: r.efficiency)
        suggestions.append(OptimizationSuggestion(
            category="frequency",
            priority=2,
            description=f"Consider using {best_eff.frequency_gtps} GT/s for best efficiency",
            expected_improvement=f"{best_eff.efficiency:.1f} GB/s per Watt",
            config_change={"frequency": best_eff.frequency_gtps}
        ))

        # Find best performance configuration
        best_perf = max(dvfs_results, key=lambda r: r.bandwidth_gbps)
        if best_perf != best_eff:
            suggestions.append(OptimizationSuggestion(
                category="frequency",
                priority=3,
                description=f"For maximum bandwidth, use {best_perf.frequency_gtps} GT/s",
                expected_improvement=f"{best_perf.bandwidth_gbps:.1f} GB/s peak bandwidth",
                config_change={"frequency": best_perf.frequency_gtps}
            ))

        # Find lowest power configuration
        lowest_power = min(dvfs_results, key=lambda r: r.power_w)
        suggestions.append(OptimizationSuggestion(
            category="frequency",
            priority=3,
            description=f"For minimum power, use {lowest_power.frequency_gtps} GT/s",
            expected_improvement=f"{lowest_power.power_w:.2f} W power consumption",
            config_change={"frequency": lowest_power.frequency_gtps}
        ))

        return suggestions

    def get_top_suggestions(self, n: int = 3) -> List[OptimizationSuggestion]:
        """Get top N highest priority suggestions"""
        return self.suggestions[:n]

    def get_by_category(self, category: str) -> List[OptimizationSuggestion]:
        """Get all suggestions for a specific category"""
        return [s for s in self.suggestions if s.category == category]
