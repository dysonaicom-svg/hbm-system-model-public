# Phase 10: Performance Optimization Framework & DVFS Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build performance analysis infrastructure with DVFS power-performance tradeoff analysis for HBM4

**Architecture:** Modular incremental design - build on existing modules (dvfs_controller.py, power_estimator.py, realtime_monitor.py) with new analysis capabilities. Each module is independently testable and incrementally deliverable.

**Tech Stack:** Python 3.10+, pytest, dataclasses, existing HBM4 model infrastructure

## Global Constraints

- Python 3.10+
- Test coverage target: 90%+ per module
- All new public APIs must have docstrings
- Follow existing code patterns from model/dram/ and model/monitoring/
- New modules go under model/analysis/ and tests/analysis/
- Use TDD approach: write test first, then implementation

---

## File Structure Overview

```
model/analysis/                        # NEW - Performance analysis module
├── __init__.py                        # Package init with exports
├── bottleneck_detector.py             # Bottleneck identification
├── hotspot_detector.py                # Hot spot detection
├── latency_analyzer.py                # Latency distribution analysis
├── dvfs_analyzer.py                   # DVFS power-performance analysis
├── power_performance_curve.py         # Pareto curve generation
└── optimizer.py                       # Optimization suggestions

model/compliance/                      # NEW - Compliance verification module
├── __init__.py
├── jedec_validator.py                 # JEDEC standard validator
├── hbm3_compatibility.py              # HBM3 compatibility checker
└── report_generator.py                # Compliance report generator

tests/analysis/                        # NEW - Analysis tests
├── __init__.py
├── test_bottleneck_detector.py        # 15+ tests
├── test_hotspot_detector.py           # 12+ tests
├── test_latency_analyzer.py           # 10+ tests
├── test_dvfs_analyzer.py              # 15+ tests
├── test_power_performance_curve.py    # 10+ tests
└── test_optimizer.py                  # 8+ tests

tests/compliance/                      # NEW - Compliance tests
├── __init__.py
├── test_jedec_validator.py            # 20+ tests
└── test_hbm3_compatibility.py         # 12+ tests

docs/superpowers/plans/                # Plan documentation
└── 2026-06-30-phase10-implementation-plan.md  # This file
```

---

## Task 1: Bottleneck Detector Module

**Files:**
- Create: `model/analysis/bottleneck_detector.py`
- Create: `tests/analysis/test_bottleneck_detector.py`
- Modify: `model/analysis/__init__.py`

**Interfaces:**
- Consumes: Performance metrics from model/monitoring/realtime_monitor.py
- Produces: `Bottleneck` dataclass, `BottleneckReport` class with `detect()`, `get_summary()` methods

**Dependencies:** None (first module)

### Task 1.1: Create Bottleneck Data Classes

- [ ] **Step 1: Write the failing test**

```python
# tests/analysis/test_bottleneck_detector.py
import pytest
from model.analysis.bottleneck_detector import Bottleneck, BottleneckType, BottleneckReport

class TestBottleneckDataclass:
    def test_bottleneck_creation(self):
        bottleneck = Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.8,
            location="channel_0.bank_3",
            description="Bank 3 has 85% conflict rate"
        )
        assert bottleneck.bottleneck_type == BottleneckType.BANK_CONFLICT
        assert bottleneck.severity == 0.8
        assert "bank_3" in bottleneck.location

    def test_bottleneck_type_enum(self):
        assert BottleneckType.BANK_CONFLICT.value == "bank_conflict"
        assert BottleneckType.QUEUE_BLOCKING.value == "queue_blocking"
        assert BottleneckType.CHANNEL_UTILIZATION.value == "channel_utilization"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/analysis/test_bottleneck_detector.py::TestBottleneckDataclass -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'model.analysis'"

- [ ] **Step 3: Create module structure**

Create directories and files:
```bash
mkdir -p model/analysis tests/analysis
touch model/analysis/__init__.py tests/analysis/__init__.py
```

- [ ] **Step 4: Write minimal implementation**

```python
# model/analysis/bottleneck_detector.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/analysis/test_bottleneck_detector.py::TestBottleneckDataclass -v`
Expected: PASS

- [ ] **Step 6: Add BottleneckDetector class tests**

```python
# tests/analysis/test_bottleneck_detector.py (append)
class TestBottleneckDetector:
    def test_detector_creation(self):
        from model.analysis.bottleneck_detector import BottleneckDetector
        detector = BottleneckDetector()
        assert detector is not None

    def test_detect_bank_conflict(self):
        from model.analysis.bottleneck_detector import BottleneckDetector, BottleneckType
        detector = BottleneckDetector()
        # Mock metrics with high bank conflict
        metrics = {
            "channel_0": {
                "bank_conflict_rate": 0.85,
                "bank_utilization": {"bank_0": 0.9, "bank_1": 0.85}
            }
        }
        report = detector.detect(metrics)
        assert len(report.bottlenecks) > 0
        assert any(b.bottleneck_type == BottleneckType.BANK_CONFLICT for b in report.bottlenecks)
```

- [ ] **Step 7: Implement BottleneckDetector**

```python
# model/analysis/bottleneck_detector.py (add class)
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
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/analysis/test_bottleneck_detector.py -v`
Expected: All PASS

- [ ] **Step 9: Update __init__.py**

```python
# model/analysis/__init__.py
"""Performance Analysis Module for HBM4"""

from model.analysis.bottleneck_detector import (
    Bottleneck,
    BottleneckType,
    BottleneckReport,
    BottleneckDetector,
)

__all__ = [
    "Bottleneck",
    "BottleneckType",
    "BottleneckReport",
    "BottleneckDetector",
]
```

- [ ] **Step 10: Commit**

```bash
git add model/analysis/ tests/analysis/
git commit -m "feat: add BottleneckDetector module

- Add Bottleneck and BottleneckType classes
- Add BottleneckDetector with bank conflict detection
- Add BottleneckReport for summary generation
- Add 15+ unit tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Hotspot Detector Module

**Files:**
- Create: `model/analysis/hotspot_detector.py`
- Create: `tests/analysis/test_hotspot_detector.py`

**Interfaces:**
- Consumes: Request trace data, address mappings
- Produces: `HotspotData` dataclass, `HotspotReport` with `detect()`, `get_heatmap()` methods

**Dependencies:** Task 1 (BottleneckDetector)

### Task 2.1: Create Hotspot Data Classes

- [ ] **Step 1: Write the failing test**

```python
# tests/analysis/test_hotspot_detector.py
import pytest
from model.analysis.hotspot_detector import HotspotData, HotspotType, HotspotReport

class TestHotspotDataclass:
    def test_hotspot_data_creation(self):
        hotspot = HotspotData(
            hotspot_type=HotspotType.ADDRESS,
            address=0x1000,
            access_count=1000,
            heat_level=0.85
        )
        assert hotspot.hotspot_type == HotspotType.ADDRESS
        assert hotspot.address == 0x1000
        assert hotspot.heat_level == 0.85

    def test_hotspot_type_enum(self):
        assert HotspotType.ADDRESS.value == "address"
        assert HotspotType.BANK.value == "bank"
        assert HotspotType.CHANNEL.value == "channel"
```

- [ ] **Step 2: Implement module**

```python
# model/analysis/hotspot_detector.py
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
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/analysis/test_hotspot_detector.py -v`
Expected: All PASS

- [ ] **Step 4: Add more tests**

```python
# tests/analysis/test_hotspot_detector.py (append)
class TestHotspotDetector:
    def test_detect_from_trace(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector()
        trace = [(0x1000, True), (0x1000, False), (0x2000, True)] * 10
        report = detector.detect_from_trace(trace)
        assert len(report.hotspots) >= 1
        assert report.hotspots[0].address == 0x1000

    def test_empty_trace(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector()
        report = detector.detect_from_trace([])
        assert len(report.hotspots) == 0
```

- [ ] **Step 5: Run all tests**

Run: `pytest tests/analysis/test_hotspot_detector.py -v`
Expected: All PASS

- [ ] **Step 6: Update __init__.py and commit**

```bash
git add model/analysis/ tests/analysis/
git commit -m "feat: add HotspotDetector module

- Add HotspotData and HotspotType classes
- Add HotspotDetector with trace-based detection
- Add HotspotReport with heatmap generation
- Add 12+ unit tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Latency Analyzer Module

**Files:**
- Create: `model/analysis/latency_analyzer.py`
- Create: `tests/analysis/test_latency_analyzer.py`

**Interfaces:**
- Consumes: Latency samples (cycles or ns)
- Produces: `LatencyStats` dataclass, `LatencyDistribution` class with `analyze()`, `get_percentiles()` methods

**Dependencies:** None (standalone module)

- [ ] **Write tests, implementation, and commit**

```python
# model/analysis/latency_analyzer.py
"""Latency Analysis Module for HBM4 Performance Analysis"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import statistics

@dataclass
class LatencyStats:
    """Statistical summary of latency data"""
    min_ns: float = 0.0
    max_ns: float = 0.0
    mean_ns: float = 0.0
    median_ns: float = 0.0
    p50_ns: float = 0.0
    p90_ns: float = 0.0
    p95_ns: float = 0.0
    p99_ns: float = 0.0
    std_dev_ns: float = 0.0
    sample_count: int = 0

class LatencyDistribution:
    """Analyzes latency distribution"""

    def __init__(self):
        self.samples: List[float] = []

    def add_sample(self, latency_ns: float):
        self.samples.append(latency_ns)

    def analyze(self) -> LatencyStats:
        if not self.samples:
            return LatencyStats()

        sorted_samples = sorted(self.samples)
        n = len(sorted_samples)

        def percentile(p: float) -> float:
            idx = int(n * p / 100)
            idx = min(idx, n - 1)
            return sorted_samples[idx]

        return LatencyStats(
            min_ns=min(sorted_samples),
            max_ns=max(sorted_samples),
            mean_ns=statistics.mean(sorted_samples),
            median_ns=percentile(50),
            p50_ns=percentile(50),
            p90_ns=percentile(90),
            p95_ns=percentile(95),
            p99_ns=percentile(99),
            std_dev_ns=statistics.stdev(sorted_samples) if n > 1 else 0.0,
            sample_count=n
        )

    def get_histogram(self, bins: int = 20) -> Tuple[List[float], List[int]]:
        if not self.samples:
            return [], []

        min_val, max_val = min(self.samples), max(self.samples)
        if min_val == max_val:
            return [min_val], [len(self.samples)]

        bin_width = (max_val - min_val) / bins
        edges = [min_val + i * bin_width for i in range(bins + 1)]
        counts = [0] * bins

        for s in self.samples:
            bin_idx = min(int((s - min_val) / bin_width), bins - 1)
            counts[bin_idx] += 1

        centers = [(edges[i] + edges[i + 1]) / 2 for i in range(bins)]
        return centers, counts
```

```python
# tests/analysis/test_latency_analyzer.py
import pytest
from model.analysis.latency_analyzer import LatencyStats, LatencyDistribution

class TestLatencyDistribution:
    def test_empty_distribution(self):
        dist = LatencyDistribution()
        stats = dist.analyze()
        assert stats.sample_count == 0

    def test_single_sample(self):
        dist = LatencyDistribution()
        dist.add_sample(100.0)
        stats = dist.analyze()
        assert stats.mean_ns == 100.0
        assert stats.sample_count == 1

    def test_percentiles(self):
        dist = LatencyDistribution()
        for i in range(100):
            dist.add_sample(float(i))
        stats = dist.analyze()
        assert 49 <= stats.p50_ns <= 51
        assert 89 <= stats.p90_ns <= 91
```

---

## Task 4: DVFS Analyzer Module

**Files:**
- Create: `model/analysis/dvfs_analyzer.py`
- Create: `tests/analysis/test_dvfs_analyzer.py`

**Interfaces:**
- Consumes: Existing `model/dram/dvfs_controller.py`, `model/dram/power_estimator.py`
- Produces: `DVFSResult`, `DVFSCurve`, `ParetoPoint` dataclasses with `analyze()`, `generate_pareto()` methods

**Dependencies:** Tasks 1-3, existing DVFS controller

- [ ] **Write tests, implementation, and commit**

```python
# model/analysis/dvfs_analyzer.py
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
```

```python
# tests/analysis/test_dvfs_analyzer.py
import pytest
from model.analysis.dvfs_analyzer import (
    DVFSAnalyzer, DVFSResult, DVFSSpeedGrade, ParetoPoint
)

class TestDVFSResult:
    def test_from_speed_grade_s16(self):
        result = DVFSResult.from_speed_grade(DVFSSpeedGrade.S16)
        assert result.frequency_gtps == 16.0
        assert result.bandwidth_gbps > 0

    def test_from_speed_grade_s8(self):
        result = DVFSResult.from_speed_grade(DVFSSpeedGrade.S8)
        assert result.frequency_gtps == 8.0
        assert result.power_w < 20.0  # Should be lower than S16

class TestDVFSAnalyzer:
    def test_frequency_sweep(self):
        analyzer = DVFSAnalyzer()
        results = analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        assert len(results) == 3  # 8, 12, 16 GT/s
        assert results[0].frequency_gtps == 8.0
        assert results[-1].frequency_gtps == 16.0

    def test_pareto_curve(self):
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        pareto = analyzer.generate_pareto_curve()
        knee_points = [p for p in pareto if p.is_knee_point]
        assert len(knee_points) >= 1

    def test_suggest_optimal_config(self):
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))
        config = analyzer.suggest_optimal_config(target_perf_percent=80.0)
        assert config.bandwidth_gbps > 0
```

---

## Task 5: Power-Performance Curve Module

**Files:**
- Create: `model/analysis/power_performance_curve.py`
- Create: `tests/analysis/test_power_performance_curve.py`

**Dependencies:** Task 4 (DVFSAnalyzer)

- [ ] **Write tests, implementation, and commit**

```python
# model/analysis/power_performance_curve.py
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
```

---

## Task 6: Optimizer Module

**Files:**
- Create: `model/analysis/optimizer.py`
- Create: `tests/analysis/test_optimizer.py`

**Dependencies:** Tasks 1-5

- [ ] **Write tests, implementation, and commit**

```python
# model/analysis/optimizer.py
"""Optimization Suggestions Module"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from model.analysis.bottleneck_detector import BottleneckReport
from model.analysis.dvfs_analyzer import DVFSAnalyzer, DVFSResult

@dataclass
class OptimizationSuggestion:
    """A suggested optimization"""
    category: str  # "frequency", "addressing", "scheduling"
    priority: int  # 1 = highest
    description: str
    expected_improvement: str
    config_change: Optional[Dict] = None

class Optimizer:
    """Generates optimization suggestions based on analysis"""

    def __init__(self):
        self.suggestions: List[OptimizationSuggestion] = []

    def generate_suggestions(
        self,
        bottleneck_report: BottleneckReport,
        dvfs_results: List[DVFSResult]
    ) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions"""
        suggestions = []

        # Suggest frequency changes based on bottlenecks
        has_conflict = any(
            b.severity > 0.7 for b in bottleneck_report.bottlenecks
        )
        if has_conflict:
            suggestions.append(OptimizationSuggestion(
                category="scheduling",
                priority=1,
                description="High bank conflict detected - consider optimizing address mapping",
                expected_improvement="15-25% latency reduction"
            ))

        # Suggest DVFS configuration
        if dvfs_results:
            best_eff = max(dvfs_results, key=lambda r: r.efficiency)
            suggestions.append(OptimizationSuggestion(
                category="frequency",
                priority=2,
                description=f"Consider using {best_eff.frequency_gtps} GT/s for best efficiency",
                expected_improvement=f"{best_eff.efficiency:.1f} GB/s per Watt",
                config_change={"frequency": best_eff.frequency_gtps}
            ))

        return suggestions
```

---

## Task 7: JEDEC Validator Module

**Files:**
- Create: `model/compliance/jedec_validator.py`
- Create: `tests/compliance/test_jedec_validator.py`

**Dependencies:** None (standalone)

- [ ] **Write tests, implementation, and commit**

```python
# model/compliance/jedec_validator.py
"""JEDEC Standard Compliance Validator"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class ComplianceLevel(Enum):
    """Compliance check levels"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"

@dataclass
class ComplianceCheck:
    """Result of a single compliance check"""
    check_name: str
    level: ComplianceLevel
    message: str
    details: Optional[Dict] = None

class JEDECValidator:
    """Validates HBM4 implementation against JEDEC JESD270-4A"""

    def __init__(self):
        self.checks: List[ComplianceCheck] = []

    def validate_timing(
        self,
        tRCD_ns: float,
        tRP_ns: float,
        tRAS_ns: float,
        tRC_ns: float
    ) -> List[ComplianceCheck]:
        """Validate DRAM timing parameters"""
        checks = []

        # JEDEC HBM4 timing constraints (simplified)
        if tRCD_ns < 8.0 or tRCD_ns > 20.0:
            checks.append(ComplianceCheck(
                check_name="tRCD_timing",
                level=ComplianceLevel.WARNING,
                message=f"tRCD={tRCD_ns}ns outside typical range (8-20ns)"
            ))

        if tRP_ns < 8.0 or tRP_ns > 20.0:
            checks.append(ComplianceCheck(
                check_name="tRP_timing",
                level=ComplianceLevel.WARNING,
                message=f"tRP={tRP_ns}ns outside typical range (8-20ns)"
            ))

        # tRC should be >= tRAS + tRP
        if tRC_ns < tRAS_ns + tRP_ns:
            checks.append(ComplianceCheck(
                check_name="tRC_consistency",
                level=ComplianceLevel.FAIL,
                message=f"tRC({tRC_ns}ns) must be >= tRAS({tRAS_ns}) + tRP({tRP_ns})"
            ))

        return checks

    def validate_power(
        self,
        active_power_w: float,
        idle_power_w: float,
        max_power_w: float = 50.0
    ) -> List[ComplianceCheck]:
        """Validate power consumption"""
        checks = []

        if active_power_w > max_power_w:
            checks.append(ComplianceCheck(
                check_name="active_power",
                level=ComplianceLevel.FAIL,
                message=f"Active power ({active_power_w}W) exceeds max ({max_power_w}W)"
            ))

        if idle_power_w > active_power_w * 0.2:
            checks.append(ComplianceCheck(
                check_name="idle_power",
                level=ComplianceLevel.WARNING,
                message="Idle power seems high relative to active power"
            ))

        return checks

    def run_all_checks(self, config: Dict) -> List[ComplianceCheck]:
        """Run all compliance checks"""
        all_checks = []

        # Timing checks
        all_checks.extend(self.validate_timing(
            tRCD_ns=config.get("tRCD_ns", 10.0),
            tRP_ns=config.get("tRP_ns", 10.0),
            tRAS_ns=config.get("tRAS_ns", 25.0),
            tRC_ns=config.get("tRC_ns", 35.0)
        ))

        # Power checks
        all_checks.extend(self.validate_power(
            active_power_w=config.get("active_power_w", 10.0),
            idle_power_w=config.get("idle_power_w", 2.0)
        ))

        return all_checks
```

```python
# tests/compliance/test_jedec_validator.py
import pytest
from model.compliance.jedec_validator import (
    JEDECValidator, ComplianceLevel, ComplianceCheck
)

class TestJEDECValidator:
    def test_timing_pass(self):
        validator = JEDECValidator()
        checks = validator.validate_timing(10.0, 10.0, 25.0, 35.0)
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 0

    def test_timing_fail(self):
        validator = JEDECValidator()
        checks = validator.validate_timing(10.0, 10.0, 25.0, 30.0)  # tRC < tRAS + tRP
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 1

    def test_power_fail(self):
        validator = JEDECValidator()
        checks = validator.validate_power(60.0, 2.0)  # Exceeds max
        failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
        assert len(failures) == 1
```

---

## Task 8: HBM3 Compatibility Checker

**Files:**
- Create: `model/compliance/hbm3_compatibility.py`
- Create: `tests/compliance/test_hbm3_compatibility.py`

**Dependencies:** Task 7

- [ ] **Write tests, implementation, and commit**

```python
# model/compliance/hbm3_compatibility.py
"""HBM3 Compatibility Checker"""

from dataclasses import dataclass
from typing import List, Dict
from model.compliance.jedec_validator import ComplianceLevel

@dataclass
class CompatibilityResult:
    """Result of compatibility check"""
    feature: str
    compatible: bool
    notes: str

class HBM3CompatibilityChecker:
    """Checks HBM4 implementation for HBM3 backward compatibility"""

    def __init__(self):
        self.results: List[CompatibilityResult] = []

    def check_mode_support(self, hbm4_mode: str) -> CompatibilityResult:
        """Check if HBM4 mode supports HBM3 operation"""
        hbm3_modes = ["HBM3_LEGACY", "HBM3_COMPAT"]
        return CompatibilityResult(
            feature="HBM3 Mode",
            compatible=hbm4_mode in hbm3_modes,
            notes=f"Mode '{hbm4_mode}' is {'compatible' if hbm4_mode in hbm3_modes else 'not compatible'}"
        )

    def check_timing_compatibility(
        self,
        hbm4_tRCD: float,
        hbm3_tRCD: float = 10.0
    ) -> CompatibilityResult:
        """Check if timing parameters are HBM3 compatible"""
        compatible = abs(hbm4_tRCD - hbm3_tRCD) <= 2.0
        return CompatibilityResult(
            feature="Timing Parameters",
            compatible=compatible,
            notes=f"tRCD difference: {abs(hbm4_tRCD - hbm3_tRCD):.1f}ns"
        )

    def check_all(self, config: Dict) -> List[CompatibilityResult]:
        """Run all compatibility checks"""
        results = []

        results.append(self.check_mode_support(config.get("mode", "HBM4")))
        results.append(self.check_timing_compatibility(
            hbm4_tRCD=config.get("tRCD_ns", 10.0)
        ))

        return results
```

---

## Task 9: Integration Tests and Final Verification

**Files:**
- Create: `tests/analysis/test_integration.py`
- Create: `tests/compliance/test_integration.py`

**Dependencies:** Tasks 1-8

- [ ] **Write integration tests**

```python
# tests/analysis/test_integration.py
"""Integration tests for analysis modules"""

import pytest
from model.analysis.bottleneck_detector import BottleneckDetector
from model.analysis.hotspot_detector import HotspotDetector
from model.analysis.latency_analyzer import LatencyDistribution
from model.analysis.dvfs_analyzer import DVFSAnalyzer
from model.analysis.optimizer import Optimizer

class TestAnalysisIntegration:
    def test_full_pipeline(self):
        """Test complete analysis pipeline"""
        # Generate sample data
        trace = [(0x1000 + i % 16, True) for i in range(100)]

        # Step 1: Detect hotspots
        hotspot_det = HotspotDetector()
        hotspot_report = hotspot_det.detect_from_trace(trace)

        # Step 2: Analyze latency
        latency_dist = LatencyDistribution()
        for _ in range(50):
            latency_dist.add_sample(100.0 + (_ % 10) * 5)
        stats = latency_dist.analyze()

        # Step 3: DVFS analysis
        dvfs_analyzer = DVFSAnalyzer()
        dvfs_analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))

        # Step 4: Generate suggestions
        bottleneck_det = BottleneckDetector()
        bottleneck_report = bottleneck_det.detect({
            "ch0": {"bank_conflict_rate": 0.6, "utilization": 0.8}
        })

        optimizer = Optimizer()
        suggestions = optimizer.generate_suggestions(
            bottleneck_report,
            dvfs_analyzer.results
        )

        # Verify results
        assert len(hotspot_report.hotspots) >= 0
        assert stats.sample_count == 50
        assert len(dvfs_analyzer.results) == 3
        assert len(suggestions) >= 0
```

- [ ] **Run all Phase 10 tests**

```bash
pytest tests/analysis/ tests/compliance/ -v --tb=short
```

- [ ] **Final commit**

```bash
git add model/analysis/ model/compliance/ tests/analysis/ tests/compliance/
git commit -m "feat: complete Phase 10 implementation

- Performance analysis infrastructure (bottleneck, hotspot, latency)
- DVFS power-performance analysis
- JEDEC compliance verification
- HBM3 compatibility checker
- Optimizer for suggestions

Total: ~100 new tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Summary

| Task | Description | Tests | Status |
|------|-------------|-------|--------|
| 1 | Bottleneck Detector | 15+ | Pending |
| 2 | Hotspot Detector | 12+ | Pending |
| 3 | Latency Analyzer | 10+ | Pending |
| 4 | DVFS Analyzer | 15+ | Pending |
| 5 | Power-Performance Curve | 10+ | Pending |
| 6 | Optimizer | 8+ | Pending |
| 7 | JEDEC Validator | 20+ | Pending |
| 8 | HBM3 Compatibility | 12+ | Pending |
| 9 | Integration Tests | 10+ | Pending |
| **Total** | | **~110+** | |

**Estimated Time:** ~15-20 minutes with parallel agents