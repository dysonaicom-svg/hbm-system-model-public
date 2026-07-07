"""Tests for performance_dashboard module"""

import pytest
from sim.visualization.performance_dashboard import (
    PerformanceDashboard, DashboardMetrics
)


class TestDashboardMetrics:
    def test_metrics_creation(self):
        metrics = DashboardMetrics(
            bandwidth_gbps=100.0,
            latency_ns=50.0,
            efficiency_percent=80.0
        )
        assert metrics.bandwidth_gbps == 100.0


class TestPerformanceDashboard:
    def test_dashboard_creation(self):
        dash = PerformanceDashboard(total_channels=32)
        assert dash.total_channels == 32

    def test_update_metrics(self):
        dash = PerformanceDashboard()
        metrics = DashboardMetrics(bandwidth_gbps=100.0)
        dash.update(metrics)
        assert len(dash.metrics_history) == 1

    def test_format_bar(self):
        dash = PerformanceDashboard()
        bar = dash._format_bar(50.0, 100.0)
        assert "50.0%" in bar
        assert len(bar) > 10

    def test_get_header(self):
        dash = PerformanceDashboard()
        header = dash.get_header()
        assert "HBM4" in header
        assert "Dashboard" in header

    def test_get_summary(self):
        dash = PerformanceDashboard()
        metrics = DashboardMetrics(bandwidth_gbps=100.0, latency_ns=50.0)
        summary = dash.get_summary(metrics)
        assert "100.00" in summary

    def test_get_channel_grid(self):
        dash = PerformanceDashboard(total_channels=8)
        utils = {0: 0.8, 1: 0.6, 2: 0.9, 3: 0.5}
        grid = dash.get_channel_grid(utils)
        assert "CH00" in grid

    def test_get_queue_status(self):
        dash = PerformanceDashboard()
        status = dash.get_queue_status(64, 128)
        assert "64" in status
        assert "128" in status

    def test_render(self):
        dash = PerformanceDashboard(total_channels=8)
        metrics = DashboardMetrics(bandwidth_gbps=100.0, latency_ns=50.0)
        output = dash.render(metrics, {0: 0.8}, 64, 128)
        assert "HBM4" in output
        assert "100.00" in output

    def test_render_trend_no_data(self):
        dash = PerformanceDashboard()
        trend = dash.render_trend("bandwidth")
        assert "No data" in trend

    def test_render_trend_with_data(self):
        dash = PerformanceDashboard()
        for i in range(10):
            dash.update(DashboardMetrics(bandwidth_gbps=50.0 + i * 5))
        trend = dash.render_trend("bandwidth")
        assert "BANDWIDTH" in trend
        assert "TREND" in trend
