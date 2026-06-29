"""Power-Performance Curve Generation Module"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from model.analysis.dvfs_analyzer import DVFSAnalyzer, DVFSResult, ParetoPoint

@dataclass
class CurvePoint:
    """A point on the power-performance curve"""
    x: float  # Power (W)
    y: float  # Performance (GB/s)
    label: str = ""

class PowerPerformanceCurve:
    """Generates and analyzes power-performance curves"""

    def __init__(self):
        self.points: List[CurvePoint] = []
        self.pareto_points: List[ParetoPoint] = []

    def generate_from_dvfs(self, dvfs_analyzer: DVFSAnalyzer) -> List[CurvePoint]:
        """Generate curve from DVFS analysis results"""
        self.points = []
        for r in dvfs_analyzer.results:
            self.points.append(CurvePoint(
                x=r.power_w,
                y=r.bandwidth_gbps,
                label=f"{r.frequency_gtps} GT/s"
            ))
        self.pareto_points = dvfs_analyzer.generate_pareto_curve()
        return self.points

    def find_operating_point(
        self,
        target_performance: float,
        tolerance: float = 0.05
    ) -> Optional[CurvePoint]:
        """Find operating point closest to target performance"""
        if not self.points:
            return None

        best = None
        best_diff = float('inf')

        for p in self.points:
            diff = abs(p.y - target_performance) / target_performance
            if diff < best_diff:
                best_diff = diff
                best = p

        return best if best_diff <= tolerance else None
