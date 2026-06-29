"""DVFS Power-Performance Analysis Module for HBM4"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum


class DVFSSpeedGrade(Enum):
    """HBM4 speed grades"""
    S8 = 8.0    # 8 GT/s
    S12 = 12.0  # 12 GT/s
    S16 = 16.0  # 16 GT/s (max)


@dataclass
class DVFSResult:
    """Result of DVFS analysis at a specific frequency"""
    frequency_gtps: float
    voltage_v: float
    power_w: float
    bandwidth_gbps: float
    latency_ns: float
    efficiency: float  # GB/s per Watt

    @classmethod
    def from_speed_grade(cls, grade: DVFSSpeedGrade, base_power_w: float = 10.0,
                         base_bw_gbps: float = 64.0) -> "DVFSResult":
        """Create DVFS result from speed grade (simplified model)"""
        freq = grade.value
        # Voltage scales roughly with frequency (JEDEC compliance)
        voltage = 0.8 + (freq - 8.0) * 0.03  # 0.8V @ 8GT/s to ~1.04V @ 16GT/s
        # Power scales with V^2 * f
        power_ratio = (voltage ** 2 * freq) / (0.8 ** 2 * 8.0)
        power = base_power_w * power_ratio
        # Bandwidth scales linearly with frequency
        bw_ratio = freq / 16.0
        bandwidth = base_bw_gbps * bw_ratio
        # Latency inversely scales with frequency
        latency = 100.0 * 16.0 / freq  # Base latency ~100ns @ 16GT/s
        # Efficiency = bandwidth / power
        efficiency = bandwidth / power if power > 0 else 0.0

        return cls(
            frequency_gtps=freq,
            voltage_v=voltage,
            power_w=power,
            bandwidth_gbps=bandwidth,
            latency_ns=latency,
            efficiency=efficiency
        )


@dataclass
class ParetoPoint:
    """A point on the Pareto optimal curve"""
    dvfs_result: DVFSResult
    is_knee_point: bool = False
    is_optimal_power: bool = False
    is_optimal_performance: bool = False


class DVFSAnalyzer:
    """Analyzes DVFS power-performance tradeoffs"""

    def __init__(self):
        self.results: List[DVFSResult] = []

    def analyze_frequency_sweep(
        self,
        freq_range: Tuple[float, float, float],  # min, max, step (GT/s)
        base_power_w: float = 10.0
    ) -> List[DVFSResult]:
        """Analyze across frequency range"""
        min_f, max_f, step = freq_range
        self.results = []

        freq = min_f
        while freq <= max_f + 0.001:  # Small epsilon for float comparison
            grade = DVFSSpeedGrade.S8
            if freq >= 15.0:
                grade = DVFSSpeedGrade.S16
            elif freq >= 10.0:
                grade = DVFSSpeedGrade.S12

            result = DVFSResult.from_speed_grade(grade, base_power_w)
            result.frequency_gtps = round(freq, 1)
            self.results.append(result)
            freq += step

        return self.results

    def generate_pareto_curve(self) -> List[ParetoPoint]:
        """Generate Pareto optimal curve"""
        if not self.results:
            return []

        pareto_points = []
        for r in self.results:
            point = ParetoPoint(dvfs_result=r)

            # Identify knee point (maximum efficiency)
            max_eff = max(p.efficiency for p in self.results)
            if r.efficiency == max_eff:
                point.is_knee_point = True

            # Identify optimal power point (lowest power)
            min_power = min(r.power_w for r in self.results)
            if r.power_w == min_power:
                point.is_optimal_power = True

            # Identify optimal performance point (highest bandwidth)
            max_bw = max(r.bandwidth_gbps for r in self.results)
            if r.bandwidth_gbps == max_bw:
                point.is_optimal_performance = True

            pareto_points.append(point)

        return pareto_points

    def suggest_optimal_config(
        self,
        target_perf_percent: float = 80.0,
        prefer_power: bool = False
    ) -> DVFSResult:
        """Suggest optimal configuration based on target performance"""
        if not self.results:
            return DVFSResult(0, 0, 0, 0, 0, 0)

        max_bw = max(r.bandwidth_gbps for r in self.results)
        target_bw = max_bw * (target_perf_percent / 100.0)

        if prefer_power:
            # Find lowest power that meets target
            candidates = [r for r in self.results if r.bandwidth_gbps >= target_bw]
            if candidates:
                return min(candidates, key=lambda r: r.power_w)
            return min(self.results, key=lambda r: r.power_w)

        # Default: find best efficiency
        candidates = [r for r in self.results if r.bandwidth_gbps >= target_bw]
        if candidates:
            return max(candidates, key=lambda r: r.efficiency)
        return max(self.results, key=lambda r: r.efficiency)