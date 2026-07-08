# Export Guide

## HBM4 Export & CLI Enhancement

Phase 18 adds comprehensive export capabilities and CLI interface for HBM4 analysis.

---

## Report Exporter

### Basic Usage

```python
from model.export import AnalysisReportExporter, ExporterConfig

# Create exporter
exporter = AnalysisReportExporter()

# Export JSON
data = {"throughput": 100.0, "latency": 10.5}
exporter.export_json(data, "report.json")

# Export HTML
exporter.export_html(data, "Report Title", "report.html")

# Export CSV
data_list = [{"name": "test", "value": 10}]
exporter.export_csv(data_list, "data.csv")
```

### Bottleneck Report Export

```python
from model.export import AnalysisReportExporter

exporter = AnalysisReportExporter()
bottleneck_data = {
    "bottlenecks": [
        {"type": "bank", "count": 10},
        {"type": "channel", "count": 5},
    ]
}

# Export all formats at once
results = exporter.export_bottleneck_report(bottleneck_data)
# Returns: {"json": "bottleneck_report.json", "csv": "...", "html": "..."}
```

---

## CLI Interface

### Installation

Add to your `pyproject.toml`:

```toml
[project.scripts]
hbm4 = "model.export.cli:main"
```

### Commands

#### Analyze

```bash
# Bottleneck analysis
hbm4 analyze --type bottleneck --output report.json

# Hotspot analysis
hbm4 analyze --type hotspot --output hotspots.json

# Latency analysis
hbm4 analyze --type latency --output latency.json

# DVFS analysis
hbm4 analyze --type dvfs --output dvfs.json
```

#### Validate

```bash
# Run compliance validation
hbm4 validate --level normal --output validation.json

# Strict validation
hbm4 validate --level strict
```

#### Export

```bash
# Convert between formats
hbm4 export --input data.json --output data.html --format html
hbm4 export --input data.json --output data.csv --format csv
```

#### Benchmark

```bash
# Quick benchmark
hbm4 benchmark --mode quick --channels 32

# Full benchmark
hbm4 benchmark --mode full

# Stress test
hbm4 benchmark --mode stress
```

---

## Visualization Export

### ASCII Charts

```python
from model.export import VisualizationExporter, ChartData

exporter = VisualizationExporter()

# Create bar chart
chart = exporter.create_bar_chart(
    "Bandwidth",
    ["Sequential", "Random", "Hotspot"],
    [164, 82, 75]
)

# Export as ASCII
print(exporter.export_ascii_chart(chart))
```

### Heatmap

```python
# Create heatmap data
heatmap = exporter.create_heatmap_data(
    "Channel Utilization",
    ["Ch0", "Ch1", "Ch2"],
    ["Bank0", "Bank1", "Bank2"],
    [[0.9, 0.3, 0.1], [0.2, 0.8, 0.4], [0.5, 0.6, 0.7]]
)

print(exporter.export_heatmap_ascii(heatmap))
```

### Timing Diagram

```python
signals = [
    ("CLK", [1, 0, 1, 0, 1, 0, 1, 0]),
    ("DATA", [0, 0, 1, 1, 0, 0, 1, 1]),
]
print(exporter.export_timing_diagram(signals, "Read Timing"))
```

### Quick Chart Helper

```python
from model.export import quick_chart

data = [("Sequential", 164), ("Random", 82), ("Hotspot", 75)]
print(quick_chart(data, "Bandwidth GB/s"))
```

---

## HTML Report Template

Exported HTML reports include:
- Timestamp
- Styled tables for tabular data
- Hierarchical sections for nested data
- Responsive design

---

## Files

| File | Description |
|------|-------------|
| `model/export/__init__.py` | Module exports |
| `model/export/report_exporter.py` | Report export (JSON/HTML/CSV) |
| `model/export/cli.py` | CLI interface |
| `model/export/visualization_export.py` | ASCII/SVG visualization |
| `tests/export/test_export.py` | Tests |
