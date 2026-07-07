"""Tests for report_generator module"""

import pytest
from sim.analysis.report_generator import (
    ReportGenerator, AnalysisReport, ReportMetadata,
    BandwidthMetrics, LatencyMetrics, BottleneckReport, HotspotReport
)


class TestReportMetadata:
    def test_metadata_creation(self):
        meta = ReportMetadata(title="Test Report", timestamp="2026-01-01", version="1.0")
        assert meta.title == "Test Report"
        assert meta.version == "1.0"


class TestBandwidthMetrics:
    def test_bandwidth_creation(self):
        bw = BandwidthMetrics(
            peak_gbps=100.0,
            achieved_gbps=80.0,
            efficiency_percent=80.0,
            channel_utilization={0: 0.8, 1: 0.9}
        )
        assert bw.peak_gbps == 100.0


class TestLatencyMetrics:
    def test_latency_creation(self):
        lat = LatencyMetrics(
            min_ns=10.0, max_ns=100.0, avg_ns=50.0,
            p50_ns=45.0, p90_ns=80.0, p99_ns=95.0, std_dev_ns=20.0
        )
        assert lat.avg_ns == 50.0


class TestAnalysisReport:
    def test_report_creation(self):
        report = AnalysisReport("Test Report")
        assert report.metadata.title == "Test Report"
        assert report.bandwidth is None

    def test_set_bandwidth(self):
        report = AnalysisReport()
        report.set_bandwidth(peak=100.0, achieved=80.0, efficiency=80.0,
                           channel_util={0: 0.8})
        assert report.bandwidth.peak_gbps == 100.0
        assert report.bandwidth.efficiency_percent == 80.0

    def test_set_latency(self):
        report = AnalysisReport()
        report.set_latency({"min_ns": 10, "max_ns": 100, "mean_ns": 50,
                           "p50_ns": 45, "p90_ns": 80, "p99_ns": 95, "std_dev_ns": 20})
        assert report.latency.avg_ns == 50.0

    def test_set_bottlenecks(self):
        report = AnalysisReport()
        bottlenecks = [{"type": "bank_conflict", "description": "Bank conflict detected"}]
        report.set_bottlenecks(bottlenecks, "warning", ["Suggestion 1"])
        assert report.bottlenecks.severity == "warning"
        assert len(report.bottlenecks.recommendations) == 1

    def test_set_hotspots(self):
        report = AnalysisReport()
        hotspots = [{"bank_id": 0, "heat_level": 0.8}]
        report.set_hotspots(hotspots, {"address": {}}, ["Suggestion 1"])
        assert len(report.hotspots.hotspots) == 1

    def test_to_dict(self):
        report = AnalysisReport()
        report.set_bandwidth(100.0, 80.0, 80.0, {})
        data = report.to_dict()
        assert "metadata" in data
        assert "bandwidth" in data

    def test_to_text(self):
        report = AnalysisReport("Test")
        report.set_bandwidth(100.0, 80.0, 80.0, {})
        text = report.to_text()
        assert "Test" in text
        assert "100.00" in text

    def test_export_json(self, tmp_path):
        report = AnalysisReport()
        report.set_bandwidth(100.0, 80.0, 80.0, {})
        filepath = tmp_path / "report.json"
        report.to_json(str(filepath))
        assert filepath.exists()


class TestReportGenerator:
    def test_generator_creation(self):
        gen = ReportGenerator()
        assert len(gen.reports) == 0

    def test_create_report(self):
        gen = ReportGenerator()
        report = gen.create_report("My Report")
        assert report.metadata.title == "My Report"
        assert len(gen.reports) == 1

    def test_generate_summary(self):
        gen = ReportGenerator()
        gen.create_report("Report 1")
        gen.create_report("Report 2")
        summary = gen.generate_summary()
        assert summary["reports"] == 2
