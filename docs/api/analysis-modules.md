# Analysis Modules

Performance analysis and compliance validation modules for HBM4 system simulation.

## Quick Start

```python
# Analysis Integration
from sim.analysis_integration import SimulatorAnalyzer

analyzer = SimulatorAnalyzer(enabled=True)
analyzer.record_request(address=0x1000, is_read=True, latency_ns=50.0)
report = analyzer.analyze(metrics={"channel_0": {"bank_conflict_rate": 0.3}})
print(report.to_dict())

# Compliance Validation
from sim.compliance_integration import ComplianceValidator, run_compliance_check

report = run_compliance_check()
print(f"Compliant: {report.is_compliant}")
```

## Analysis Modules

### BottleneckDetector

Detects performance bottlenecks in HBM4 systems.

```python
from model.analysis.bottleneck_detector import BottleneckDetector, BottleneckReport

detector = BottleneckDetector(conflict_threshold=0.7, utilization_threshold=0.9)
report = detector.detect(metrics={
    "channel_0": {"bank_conflict_rate": 0.8, "utilization": 0.95}
})

print(f"Total bottlenecks: {report.get_summary()['total_bottlenecks']}")
for bottleneck in report.bottlenecks:
    print(f"  {bottleneck.bottleneck_type.value}: {bottleneck.description}")
```

**Bottleneck Types:**
- `BANK_CONFLICT` - High bank conflict rate
- `QUEUE_BLOCKING` - Queue blocking issues
- `CHANNEL_UTILIZATION` - High channel utilization
- `QUEUE_OVERFLOW` - Queue overflow detected
- `REFRESH_CONFLICT` - Refresh timing conflicts
- `THERMAL_THROTTLE` - Thermal throttling active

### HotspotDetector

Identifies memory access hotspots with heatmap generation.

```python
from model.analysis.hotspot_detector import HotspotDetector, HotspotType

detector = HotspotDetector(threshold_percentile=95.0)
trace = [(0x1000, True), (0x1000, True), (0x2000, True)] * 10
report = detector.detect_from_trace(trace)

# Get top hotspots
top = report.get_top_n(5)
for hotspot in top:
    print(f"  Address 0x{hotspot.address:x}: {hotspot.access_count} accesses")

# Generate heatmaps
heatmaps = report.generate_heatmap()
for htype, hdata in heatmaps.items():
    print(f"{htype.value}: max={hdata.max_value}")
```

### LatencyAnalyzer

Statistical latency analysis with percentiles.

```python
from model.analysis.latency_analyzer import LatencyDistribution

dist = LatencyDistribution()
for latency in [50.0, 60.0, 70.0, 80.0, 90.0, 100.0]:
    dist.add_sample(latency)

stats = dist.analyze()
print(f"Mean: {stats.mean_ns:.2f} ns")
print(f"P50: {stats.p50_ns:.2f} ns")
print(f"P90: {stats.p90_ns:.2f} ns")
print(f"P99: {stats.p99_ns:.2f} ns")

# Get histogram
centers, counts = dist.get_histogram(bins=10)
```

### DVFSAnalyzer

Power-performance tradeoff analysis for different speed grades.

```python
from model.analysis.dvfs_analyzer import DVFSAnalyzer, DVFSSpeedGrade

analyzer = DVFSAnalyzer()

# Analyze across frequency range
results = analyzer.analyze_frequency_sweep((8.0, 16.0, 2.0), base_power_w=10.0)

for r in results:
    print(f"{r.frequency_gtps} GT/s: {r.power_w:.2f}W, {r.bandwidth_gbps:.1f} GB/s, {r.efficiency:.2f} GB/s/W")

# Generate Pareto curve
pareto = analyzer.generate_pareto_curve()
for p in pareto:
    if p.is_knee_point:
        print(f"Best efficiency: {p.dvfs_result.frequency_gtps} GT/s")

# Suggest optimal config
optimal = analyzer.suggest_optimal_config(target_perf_percent=80.0, prefer_power=False)
print(f"Optimal: {optimal.frequency_gtps} GT/s")
```

### PowerPerformanceCurve

Generates and analyzes power-performance curves.

```python
from model.analysis.power_performance_curve import PowerPerformanceCurve
from model.analysis.dvfs_analyzer import DVFSAnalyzer

dvfs = DVFSAnalyzer()
dvfs.analyze_frequency_sweep((8.0, 16.0, 2.0))

curve = PowerPerformanceCurve()
curve.generate_from_dvfs(dvfs)

# Find operating point
point = curve.find_operating_point(target_performance=50.0, tolerance=0.1)
if point:
    print(f"Operating point: {point.label} - {point.x:.2f}W, {point.y:.1f} GB/s")
```

### Optimizer

Generates optimization suggestions based on analysis results.

```python
from model.analysis.optimizer import Optimizer

optimizer = Optimizer()
suggestions = optimizer.generate_suggestions(bottleneck_report, dvfs_results)

print("Top suggestions:")
for s in optimizer.get_top_suggestions(3):
    print(f"  [{s.category}] P{s.priority}: {s.description}")
    print(f"    Expected: {s.expected_improvement}")
```

## Compliance Modules

### JEDECValidator

Validates HBM4 implementation against JEDEC JESD270-4A standards.

```python
from model.compliance.jedec_validator import JEDECValidator, ComplianceLevel

validator = JEDECValidator()

# Run all checks
checks = validator.run_all_checks({
    "tRCD_ns": 10.0,
    "tRP_ns": 10.0,
    "tRAS_ns": 25.0,
    "tRC_ns": 35.0,
    "active_power_w": 15.0,
    "idle_power_w": 2.0,
})

# Check results
failures = [c for c in checks if c.level == ComplianceLevel.FAIL]
warnings = [c for c in checks if c.level == ComplianceLevel.WARNING]
print(f"Failures: {len(failures)}, Warnings: {len(warnings)}")
```

**Validation Checks:**
- Timing parameters (tRCD, tRP, tRAS, tRC)
- Power consumption limits
- tRC consistency (tRC >= tRAS + tRP)

### HBM3CompatibilityChecker

Checks HBM4/HBM3 backward compatibility.

```python
from model.compliance.hbm3_compatibility import HBM3CompatibilityChecker

checker = HBM3CompatibilityChecker()

# Check compatibility
results = checker.check_all({
    "mode": "HBM4",
    "tRCD_ns": 10.0,
})

for result in results:
    status = "PASS" if result.compatible else "FAIL"
    print(f"[{status}] {result.feature}: {result.notes}")
```

## Performance Optimization

```python
from model.optimization import (
    OptimizedMetrics,
    BatchRequestProcessor,
    OptimizedBankSelector,
    LatencyTracker,
    get_optimized_processor,
)

# Get optimization profile
config = get_optimized_processor("balanced")

# Track metrics
metrics = OptimizedMetrics()
metrics.record_hit(channel=0, latency_ns=50.0)
print(f"Hit rate: {metrics.hit_rate:.2%}")

# Batch processing
processor = BatchRequestProcessor(batch_size=32)
batch = processor.add(request)
if batch:
    process_batch(batch)

# Latency tracking
tracker = LatencyTracker()
tracker.add(50.0)
print(f"P99: {tracker.get_p99():.2f} ns")
```

## CLI Usage

```bash
# Run with analysis enabled
python -m sim.simulator --mode functional --analyze

# Run compliance check
python -c "from sim.compliance_integration import run_compliance_check; print(run_compliance_check().is_compliant)"
```
