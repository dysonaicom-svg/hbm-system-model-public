"""Tests for Export Module"""

import pytest
import json
import os
import tempfile
from pathlib import Path

from model.export.report_exporter import (
    AnalysisReportExporter,
    ExporterConfig,
)
from model.export.visualization_export import (
    VisualizationExporter,
    ChartData,
    quick_chart,
)


class TestAnalysisReportExporter:
    """Test AnalysisReportExporter"""

    def setup_method(self):
        self.exporter = AnalysisReportExporter()
        self.temp_dir = tempfile.mkdtemp()

    def test_export_json(self):
        """Test JSON export"""
        data = {"key": "value", "number": 42}
        output_path = os.path.join(self.temp_dir, "test.json")

        result = self.exporter.export_json(data, output_path)

        assert result == output_path
        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded["data"]["key"] == "value"

    def test_export_csv(self):
        """Test CSV export"""
        data = [
            {"name": "test1", "value": 10},
            {"name": "test2", "value": 20},
        ]
        output_path = os.path.join(self.temp_dir, "test.csv")

        result = self.exporter.export_csv(data, output_path)

        assert result == output_path
        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            content = f.read()
        assert "name,value" in content
        assert "test1,10" in content

    def test_export_csv_empty(self):
        """Test CSV export with empty data"""
        output_path = os.path.join(self.temp_dir, "empty.csv")
        result = self.exporter.export_csv([], output_path)
        assert result == output_path

    def test_export_html(self):
        """Test HTML export"""
        data = {"title": "Test", "value": 42}
        output_path = os.path.join(self.temp_dir, "test.html")

        result = self.exporter.export_html(data, "Test Report", output_path)

        assert result == output_path
        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            content = f.read()
        assert "<html>" in content
        assert "Test Report" in content
        assert "Test" in content

    def test_export_html_with_nested_dict(self):
        """Test HTML export with nested dictionary"""
        data = {
            "section1": {"key1": "value1"},
            "section2": {"key2": "value2"},
        }
        output_path = os.path.join(self.temp_dir, "nested.html")

        self.exporter.export_html(data, output_path=output_path)

        with open(output_path, 'r') as f:
            content = f.read()
        assert "section1" in content
        assert "section2" in content

    def test_export_html_with_list(self):
        """Test HTML export with list data"""
        data = {
            "items": [
                {"name": "item1", "value": 1},
                {"name": "item2", "value": 2},
            ]
        }
        output_path = os.path.join(self.temp_dir, "list.html")

        self.exporter.export_html(data, output_path=output_path)

        with open(output_path, 'r') as f:
            content = f.read()
        assert "<table>" in content
        assert "item1" in content

    def test_export_bottleneck_report(self):
        """Test bottleneck report export"""
        data = {
            "bottlenecks": [
                {"type": "bank", "count": 10},
                {"type": "channel", "count": 5},
            ]
        }

        results = self.exporter.export_bottleneck_report(data)

        assert "json" in results
        assert "csv" in results
        assert "html" in results

        for path in results.values():
            assert os.path.exists(path)

    def test_export_performance_summary(self):
        """Test performance summary export"""
        data = {"throughput": 100.0, "latency": 10.5}
        output_path = self.exporter.export_performance_summary(data)

        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert "exported_at" in loaded or "timestamp" in loaded

    def test_config_no_timestamp(self):
        """Test config without timestamp"""
        config = ExporterConfig(timestamp=False)
        exporter = AnalysisReportExporter(config)

        data = {"test": "value"}
        output_path = os.path.join(self.temp_dir, "no_ts.json")

        exporter.export_json(data, output_path)

        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded.get("exported_at") is None


class TestVisualizationExporter:
    """Test VisualizationExporter"""

    def setup_method(self):
        self.exporter = VisualizationExporter()

    def test_create_bar_chart(self):
        """Test bar chart creation"""
        chart = self.exporter.create_bar_chart(
            "Test Chart",
            ["A", "B", "C"],
            [10, 20, 30]
        )
        assert chart.title == "Test Chart"
        assert chart.chart_type == "bar"
        assert len(chart.data) == 3

    def test_create_line_chart(self):
        """Test line chart creation"""
        chart = self.exporter.create_line_chart(
            "Line Test",
            ["1", "2", "3"],
            [5, 15, 10]
        )
        assert chart.chart_type == "line"
        assert len(chart.data) == 3

    def test_export_ascii_bar_chart(self):
        """Test ASCII bar chart export"""
        chart = self.exporter.create_bar_chart("Test", ["A", "B"], [10, 20])
        result = self.exporter.export_ascii_chart(chart)

        assert "Test" in result
        assert "A" in result
        assert "B" in result

    def test_export_ascii_empty(self):
        """Test ASCII export with no data"""
        chart = ChartData(title="Empty", data=[])
        result = self.exporter.export_ascii_chart(chart)
        assert "No data" in result

    def test_export_heatmap_ascii(self):
        """Test heatmap ASCII export"""
        heatmap = self.exporter.create_heatmap_data(
            "Test Heatmap",
            ["Row1", "Row2"],
            ["Col1", "Col2"],
            [[0.1, 0.5], [0.8, 0.2]]
        )
        result = self.exporter.export_heatmap_ascii(heatmap)

        assert "Test Heatmap" in result
        assert "Row1" in result
        assert "Col1" in result

    def test_export_timing_diagram(self):
        """Test timing diagram export"""
        signals = [
            ("CLK", [1, 0, 1, 0, 1, 0, 1, 0]),
            ("DATA", [0, 0, 1, 1, 0, 0, 1, 1]),
        ]
        result = self.exporter.export_timing_diagram(signals, "Test Timing")

        assert "Test Timing" in result
        assert "CLK" in result
        assert "DATA" in result

    def test_export_svg(self):
        """Test SVG export"""
        chart = self.exporter.create_bar_chart("SVG Test", ["A", "B"], [10, 20])
        svg = self.exporter.export_to_svg(chart, width=200, height=150)

        assert "<svg" in svg
        assert "SVG Test" in svg
        assert "</svg>" in svg

    def test_add_chart(self):
        """Test adding charts"""
        chart1 = ChartData(title="Chart1", data=[("A", 10)])
        chart2 = ChartData(title="Chart2", data=[("B", 20)])

        self.exporter.add_chart(chart1)
        self.exporter.add_chart(chart2)

        assert len(self.exporter.charts) == 2

    def test_generate_full_report(self):
        """Test full report generation"""
        chart = self.exporter.create_bar_chart("Test", ["A", "B"], [10, 20])
        self.exporter.add_chart(chart)

        report = self.exporter.generate_full_report()

        assert "HBM4 ANALYSIS VISUALIZATION REPORT" in report
        assert "Test" in report


class TestQuickChart:
    """Test quick_chart helper function"""

    def test_quick_chart(self):
        """Test quick chart generation"""
        data = [("Item1", 10), ("Item2", 20), ("Item3", 15)]
        result = quick_chart(data, "Quick Test")

        assert "Quick Test" in result
        assert "Item1" in result
        assert "Item2" in result
