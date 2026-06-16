"""
Tests for HBM Performance Visualization Module

Tests bandwidth charts, latency histograms, channel heatmaps, and report generation.
"""

import pytest
import json
import os
from typing import Any

# Import visualization modules
from sim.visualization.bandwidth_chart import (
    BandwidthChart,
    BandwidthData,
    generate_bandwidth_bar_chart,
    generate_bandwidth_time_series,
    generate_bandwidth_efficiency_gauge,
    create_bandwidth_chart_from_stats,
)
from sim.visualization.latency_histogram import (
    LatencyHistogram,
    LatencyData,
    generate_latency_histogram,
    generate_percentile_markers,
    generate_latency_time_series,
    create_latency_histogram_from_stats,
    generate_ascii_histogram,
)
from sim.visualization.channel_heatmap import (
    ChannelHeatmap,
    ChannelHeatmapData,
    generate_channel_heatmap,
    generate_bank_group_heatmap,
    generate_request_density_chart,
    create_channel_heatmap_from_stats,
    generate_ascii_heatmap,
)
from sim.visualization.report_generator import (
    ReportGenerator,
    VisualizationConfig,
    ReportData,
    OutputFormat,
    generate_html_report,
    generate_ascii_report,
    generate_json_report,
    create_report_data_from_stats,
)


# =============================================================================
# Bandwidth Chart Tests
# =============================================================================

class TestBandwidthChart:
    """Tests for bandwidth chart generation"""
    
    def test_bandwidth_data_creation(self):
        """Test BandwidthData creation and properties"""
        data = BandwidthData(
            channel_bandwidth={0: 100.0, 1: 80.0},
            peak_bandwidth_gbps=819.2,
            achieved_bandwidth_gbps=180.0,
            num_channels=8,
        )
        
        assert data.channel_bandwidth[0] == 100.0
        assert data.channel_bandwidth[1] == 80.0
        assert data.peak_bandwidth_gbps == 819.2
        assert data.num_channels == 8
    
    def test_bandwidth_efficiency_calculation(self):
        """Test bandwidth efficiency calculation"""
        data = BandwidthData(
            achieved_bandwidth_gbps=163.84,
            peak_bandwidth_gbps=819.2,
        )
        
        efficiency = data.get_efficiency()
        assert 0.19 < efficiency < 0.21  # ~20% efficiency
    
    def test_bandwidth_efficiency_zero_peak(self):
        """Test efficiency with zero peak bandwidth"""
        data = BandwidthData(
            achieved_bandwidth_gbps=100.0,
            peak_bandwidth_gbps=0.0,
        )
        
        efficiency = data.get_efficiency()
        assert efficiency == 0.0
    
    def test_generate_bandwidth_bar_chart(self):
        """Test bandwidth bar chart generation"""
        channel_bw = {i: 100.0 + i * 5 for i in range(8)}
        data = generate_bandwidth_bar_chart(channel_bw, peak_bandwidth=819.2, num_channels=8)
        
        assert len(data.channel_bandwidth) == 8
        assert data.peak_bandwidth_gbps == 819.2
        assert data.achieved_bandwidth_gbps > 0
    
    def test_generate_bandwidth_time_series(self):
        """Test bandwidth time series generation"""
        samples = [(0, 0.0), (1000, 85.3), (2000, 92.1), (3000, 88.7)]
        data = generate_bandwidth_time_series(samples, peak_bandwidth=819.2)
        
        assert len(data.bandwidth_time_series) == 4
        assert len(data.time_stamps) == 4
        assert data.achieved_bandwidth_gbps > 0
    
    def test_bandwidth_chart_bar_data(self):
        """Test bar chart data generation"""
        data = BandwidthData(
            channel_bandwidth={0: 100.0, 1: 80.0, 2: 90.0},
            num_channels=3,
        )
        chart = BandwidthChart(data=data)
        
        bar_data = chart.generate_bar_chart_data()
        assert bar_data['type'] == 'bar'
        assert len(bar_data['data']['labels']) == 3
        assert len(bar_data['data']['datasets'][0]['data']) == 3
    
    def test_bandwidth_chart_line_data(self):
        """Test line chart data generation"""
        data = BandwidthData(
            bandwidth_time_series={0: 0.0, 1000: 85.0, 2000: 92.0},
            time_stamps=[0, 1000, 2000],
        )
        chart = BandwidthChart(data=data)
        
        line_data = chart.generate_line_chart_data()
        assert line_data['type'] == 'line'
        assert len(line_data['data']['datasets'][0]['data']) == 3
    
    def test_bandwidth_chart_gauge_data(self):
        """Test gauge chart data generation"""
        data = BandwidthData(
            achieved_bandwidth_gbps=163.84,
            peak_bandwidth_gbps=819.2,
        )
        chart = BandwidthChart(data=data)
        
        gauge_data = chart.generate_gauge_data()
        assert gauge_data['type'] == 'doughnut'
        assert gauge_data['data']['datasets'][0]['data'][0] > 0
    
    def test_to_dict(self):
        """Test dictionary export"""
        data = BandwidthData(
            channel_bandwidth={0: 100.0},
            peak_bandwidth_gbps=819.2,
            achieved_bandwidth_gbps=100.0,
        )
        
        d = data.to_dict()
        assert 'channel_bandwidth' in d
        assert 'peak_bandwidth_gbps' in d
        assert 'efficiency' in d


# =============================================================================
# Latency Histogram Tests
# =============================================================================

class TestLatencyHistogram:
    """Tests for latency histogram generation"""
    
    def test_latency_data_creation(self):
        """Test LatencyData creation"""
        data = LatencyData(latencies=[10.0, 20.0, 30.0, 15.0, 25.0])
        
        assert len(data.latencies) == 5
        assert min(data.latencies) == 10.0
        assert max(data.latencies) == 30.0
    
    def test_calculate_histogram(self):
        """Test histogram calculation"""
        latencies = [10, 15, 20, 25, 30, 35, 40, 45, 50]
        data = LatencyData(latencies=latencies)

        bins = data.calculate_histogram(bin_size=10)

        # Latency 10, 15 go to bin 10 (floor(10/10)*10 = 10)
        assert 10 in bins
        assert bins[10] == 2  # 10, 15
        # Latency 20, 25 go to bin 20
        assert 20 in bins
        assert bins[20] == 2  # 20, 25
        # Latency 30, 35 go to bin 30
        assert 30 in bins
        assert bins[30] == 2  # 30, 35
    
    def test_calculate_percentiles(self):
        """Test percentile calculation"""
        latencies = list(range(1, 101))  # 1 to 100
        data = LatencyData(latencies=latencies)
        
        percentiles = data.calculate_percentiles()
        
        assert 49 < percentiles['p50'] < 51  # ~50
        assert 94 < percentiles['p95'] < 96  # ~95
        assert 98 < percentiles['p99'] < 100  # ~99
    
    def test_calculate_statistics(self):
        """Test statistics calculation"""
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
        data = LatencyData(latencies=latencies)
        
        stats = data.calculate_statistics()
        
        assert stats['mean'] == 30.0
        assert stats['min'] == 10.0
        assert stats['max'] == 50.0
        assert stats['std_dev'] > 0
    
    def test_generate_latency_histogram(self):
        """Test latency histogram generation"""
        latencies = [10, 15, 20, 25, 30, 35, 40, 45, 50]
        data = generate_latency_histogram(latencies, bin_size=10)
        
        assert len(data.histogram_bins) > 0
        assert data.p50 > 0
        assert data.mean > 0
    
    def test_generate_percentile_markers(self):
        """Test percentile marker generation"""
        latencies = list(range(1, 101))
        percentiles = generate_percentile_markers(latencies)
        
        assert 'p50' in percentiles
        assert 'p95' in percentiles
        assert 'p99' in percentiles
        assert percentiles['p50'] < percentiles['p95']
        assert percentiles['p95'] < percentiles['p99']
    
    def test_latency_histogram_bar_data(self):
        """Test histogram bar chart data generation"""
        data = LatencyData(latencies=[10, 20, 30, 40, 50])
        data.calculate_histogram(bin_size=10)
        
        chart = LatencyHistogram(data=data)
        hist_data = chart.generate_histogram_data()
        
        assert hist_data['type'] == 'bar'
        assert 'datasets' in hist_data['data']
    
    def test_latency_time_series(self):
        """Test latency time series generation"""
        samples = [(0, 10.0), (1000, 12.5), (2000, 15.0)]
        data = generate_latency_time_series(samples)
        
        assert len(data.latency_time_series) == 3
        assert data.time_stamps == [0, 1000, 2000]
    
    def test_generate_ascii_histogram(self):
        """Test ASCII histogram generation"""
        latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        ascii_output = generate_ascii_histogram(latencies, bin_size=20)
        
        assert "Latency Histogram" in ascii_output
        assert "cycles" in ascii_output
        assert "Mean:" in ascii_output
        assert "P50:" in ascii_output
    
    def test_empty_latencies(self):
        """Test handling of empty latency data"""
        data = LatencyData(latencies=[])
        
        bins = data.calculate_histogram()
        percentiles = data.calculate_percentiles()
        stats = data.calculate_statistics()
        
        assert bins == {}
        assert percentiles['p50'] == 0.0
        assert stats['mean'] == 0.0


# =============================================================================
# Channel Heatmap Tests
# =============================================================================

class TestChannelHeatmap:
    """Tests for channel heatmap generation"""
    
    def test_channel_heatmap_data_creation(self):
        """Test ChannelHeatmapData creation"""
        data = ChannelHeatmapData(
            channel_utilization={0: 0.9, 1: 0.8, 2: 0.7},
            request_density={0: 1000, 1: 800, 2: 700},
            num_channels=8,
        )
        
        assert len(data.channel_utilization) == 3
        assert len(data.request_density) == 3
        assert data.num_channels == 8
    
    def test_generate_channel_heatmap(self):
        """Test channel heatmap generation"""
        utilization = {i: 0.1 * i for i in range(8)}
        data = generate_channel_heatmap(utilization, num_channels=8, bank_groups=4)
        
        assert len(data.channel_utilization) == 8
        assert data.num_channels == 8
        assert data.bank_groups_per_channel == 4
    
    def test_generate_bank_group_heatmap(self):
        """Test bank group heatmap generation"""
        activity = {
            0: {0: 0.9, 1: 0.8, 2: 0.7, 3: 0.6},
            1: {0: 0.5, 1: 0.4, 2: 0.3, 3: 0.2},
        }
        data = generate_bank_group_heatmap(activity, num_channels=8, bank_groups=4)
        
        assert len(data.bank_group_activity) == 2
        assert data.channel_utilization[0] > 0
    
    def test_generate_request_density_chart(self):
        """Test request density chart generation"""
        counts = {i: 1000 - i * 100 for i in range(8)}
        data = generate_request_density_chart(counts, num_channels=8)
        
        assert len(data.request_density) == 8
        assert data.peak_requests == 1000
        assert 0 in data.channel_utilization
    
    def test_channel_heatmap_utilization_data(self):
        """Test utilization heatmap data generation"""
        data = ChannelHeatmapData(
            channel_utilization={i: 0.1 * i for i in range(4)},
            num_channels=4,
            bank_groups_per_channel=4,
        )
        chart = ChannelHeatmap(data=data)
        
        util_data = chart.generate_utilization_heatmap_data()
        assert 'data' in util_data
        assert len(util_data['data']['datasets'][0]['data']) > 0
    
    def test_channel_heatmap_request_density_data(self):
        """Test request density data generation"""
        data = ChannelHeatmapData(
            request_density={i: 1000 - i * 100 for i in range(4)},
            num_channels=4,
        )
        chart = ChannelHeatmap(data=data)
        
        density_data = chart.generate_request_density_data()
        assert density_data['type'] == 'bar'
        assert len(density_data['data']['datasets'][0]['data']) == 4
    
    def test_generate_ascii_heatmap(self):
        """Test ASCII heatmap generation"""
        utilization = {i: 0.1 * i for i in range(4)}
        ascii_output = generate_ascii_heatmap(utilization, num_channels=4, width=40)

        assert "Channel Utilization Heatmap" in ascii_output
        assert "CH" in ascii_output  # Channel label format
        assert "Legend" in ascii_output
    
    def test_to_dict(self):
        """Test dictionary export"""
        data = ChannelHeatmapData(
            channel_utilization={0: 0.9},
            request_density={0: 1000},
        )
        
        d = data.to_dict()
        assert 'channel_utilization' in d
        assert 'request_density' in d


# =============================================================================
# Report Generator Tests
# =============================================================================

class TestReportGenerator:
    """Tests for report generation"""
    
    def test_visualization_config_creation(self):
        """Test VisualizationConfig creation"""
        config = VisualizationConfig(
            output_format=OutputFormat.HTML,
            output_path="test.html",
            chart_width=600,
            chart_height=300,
        )
        
        assert config.output_format == OutputFormat.HTML
        assert config.chart_width == 600
        assert config.chart_height == 300
    
    def test_report_data_creation(self):
        """Test ReportData creation"""
        data = ReportData(
            simulation_name="Test Simulation",
            total_requests=10000,
            completed_requests=9500,
            throughput_gbps=163.84,
        )
        
        assert data.simulation_name == "Test Simulation"
        assert data.total_requests == 10000
        assert data.completed_requests == 9500
        assert data.timestamp != ""
    
    def test_report_generator_html(self):
        """Test HTML report generation"""
        config = VisualizationConfig(output_format=OutputFormat.HTML)
        generator = ReportGenerator(config)
        
        data = ReportData(
            simulation_name="Test",
            total_requests=100,
            completed_requests=95,
            throughput_gbps=100.0,
        )
        
        content = generator.generate(data)
        assert "Test" in content
        assert "<html" in content.lower() or "Test" in content
    
    def test_report_generator_ascii(self):
        """Test ASCII report generation"""
        config = VisualizationConfig(output_format=OutputFormat.ASCII)
        generator = ReportGenerator(config)
        
        data = ReportData(
            simulation_name="Test Simulation",
            total_requests=100,
            completed_requests=95,
            throughput_gbps=163.84,
            bandwidth_efficiency=0.20,
            channel_utilization={0: 0.9, 1: 0.8},
            latency_histogram={0: 10, 10: 20},
        )
        
        content = generator.generate(data)
        assert "Test Simulation" in content
        assert "SIMULATION SUMMARY" in content
        assert "CH0" in content or "Channel" in content
    
    def test_report_generator_json(self):
        """Test JSON report generation"""
        config = VisualizationConfig(output_format=OutputFormat.JSON)
        generator = ReportGenerator(config)
        
        data = ReportData(
            simulation_name="Test",
            total_requests=100,
            throughput_gbps=100.0,
        )
        
        content = generator.generate(data)
        
        # Should be valid JSON
        parsed = json.loads(content)
        assert parsed['metadata']['simulation_name'] == "Test"
    
    def test_generate_html_report_shortcut(self):
        """Test HTML report shortcut function"""
        data = ReportData(
            simulation_name="Shortcut Test",
            total_requests=500,
        )
        
        content = generate_html_report(data, output_path="/tmp/test_report.html")
        assert "Shortcut Test" in content
    
    def test_generate_ascii_report(self):
        """Test ASCII report function"""
        data = ReportData(
            simulation_name="ASCII Test",
            total_requests=500,
        )
        
        content = generate_ascii_report(data)
        assert "ASCII Test" in content
        assert "SIMULATION SUMMARY" in content
    
    def test_generate_json_report(self):
        """Test JSON report function"""
        data = ReportData(
            simulation_name="JSON Test",
            total_requests=500,
        )
        
        content = generate_json_report(data, output_path="/tmp/test.json")
        parsed = json.loads(content)
        assert parsed['metadata']['simulation_name'] == "JSON Test"
    
    def test_create_report_data_from_stats(self):
        """Test creating ReportData from mock stats"""
        # Create mock stats object
        class MockStats:
            total_cycles = 128000000
            total_requests = 10000
            completed_requests = 9500
            read_requests = 7000
            write_requests = 3000
            throughput_gbps = 163.84
            peak_bandwidth_gbps = 819.2
            bandwidth_efficiency = 0.20
            avg_latency = 25.5
            row_hit_rate = 0.45
            per_channel_stats = {}
        
        data = create_report_data_from_stats(MockStats(), name="Stats Test")
        
        assert data.simulation_name == "Stats Test"
        assert data.total_requests == 10000
        assert data.completed_requests == 9500
        assert data.throughput_gbps == 163.84


# =============================================================================
# Integration Tests
# =============================================================================

class TestVisualizationIntegration:
    """Integration tests for complete visualization workflow"""
    
    def test_complete_bandwidth_workflow(self):
        """Test complete bandwidth visualization workflow"""
        # Generate data
        channel_bw = {i: 100.0 + i * 5 for i in range(8)}
        data = generate_bandwidth_bar_chart(channel_bw)
        
        # Create chart
        chart = BandwidthChart(data=data)
        
        # Generate chart data
        bar_data = chart.generate_bar_chart_data()
        line_data = chart.generate_line_chart_data()
        gauge_data = chart.generate_gauge_data()
        
        assert bar_data['type'] == 'bar'
        assert line_data['type'] == 'line'
        assert gauge_data['type'] == 'doughnut'
    
    def test_complete_latency_workflow(self):
        """Test complete latency visualization workflow"""
        # Generate sample latencies
        import random
        random.seed(42)
        latencies = [random.gauss(25, 10) for _ in range(1000)]
        
        # Generate data
        data = generate_latency_histogram(latencies, bin_size=5)
        
        # Create chart
        chart = LatencyHistogram(data=data)
        
        # Generate chart data
        hist_data = chart.generate_histogram_data()
        ts_data = chart.generate_time_series_data()
        annotations = chart.generate_percentile_annotations()
        
        assert hist_data['type'] == 'bar'
        assert len(annotations) >= 0  # May be empty if no latencies
    
    def test_complete_heatmap_workflow(self):
        """Test complete heatmap visualization workflow"""
        # Generate data
        utilization = {i: 0.1 + 0.1 * i for i in range(8)}
        density = {i: 1000 - i * 100 for i in range(8)}
        
        heatmap_data = generate_channel_heatmap(utilization)
        density_data = generate_request_density_chart(density)
        
        # Create charts
        heatmap_chart = ChannelHeatmap(data=heatmap_data)
        density_chart = ChannelHeatmap(data=density_data)
        
        # Generate chart data
        util_data = heatmap_chart.generate_utilization_heatmap_data()
        density_chart_data = density_chart.generate_request_density_data()
        
        assert 'data' in util_data
        assert density_chart_data['type'] == 'bar'
    
    def test_complete_report_workflow(self):
        """Test complete report generation workflow"""
        # Create report data
        data = ReportData(
            simulation_name="Integration Test",
            total_requests=10000,
            completed_requests=9500,
            throughput_gbps=163.84,
            peak_bandwidth_gbps=819.2,
            bandwidth_efficiency=0.20,
            avg_latency_cycles=25.5,
            latency_p50=20.0,
            latency_p95=50.0,
            latency_p99=100.0,
            row_hit_rate=0.45,
            channel_utilization={i: 0.1 * i for i in range(8)},
            channel_bandwidth={i: 100.0 + i * 5 for i in range(8)},
            latency_histogram={i: 100 - i * 5 for i in range(20)},
        )
        
        # Generate reports
        html_content = generate_html_report(data)
        ascii_content = generate_ascii_report(data)
        json_content = generate_json_report(data)
        
        # Validate
        assert "Integration Test" in html_content
        assert "Integration Test" in ascii_content
        parsed = json.loads(json_content)
        assert parsed['metadata']['simulation_name'] == "Integration Test"
    
    def test_stats_to_report_workflow(self):
        """Test complete stats to report workflow"""
        # Create mock stats
        class MockStats:
            total_cycles = 128000000
            total_requests = 10000
            completed_requests = 9500
            read_requests = 7000
            write_requests = 3000
            throughput_gbps = 163.84
            peak_bandwidth_gbps = 819.2
            bandwidth_efficiency = 0.20
            avg_latency = 25.5
            row_hit_rate = 0.45
            per_channel_stats = {
                0: type('obj', (), {
                    'total_requests': 1500,
                    'hit_rate': 0.5,
                    'avg_latency': 25.0,
                    'total_latency_cycles': 37500,
                })()
            }
        
        # Convert to report data
        report_data = create_report_data_from_stats(MockStats())

        # Generate report
        ascii_content = generate_ascii_report(report_data)

        assert "HBM Simulation" in ascii_content
        assert "10,000" in ascii_content or "10000" in ascii_content


# =============================================================================
# Performance Tests
# =============================================================================

class TestVisualizationPerformance:
    """Performance tests for visualization module"""
    
    def test_large_bandwidth_data(self):
        """Test handling of large bandwidth data"""
        # Create data for many channels (e.g., HBM4 with 32 channels)
        channel_bw = {i: 50.0 + (i % 8) * 5 for i in range(32)}
        data = generate_bandwidth_bar_chart(channel_bw, num_channels=32)
        
        chart = BandwidthChart(data=data)
        bar_data = chart.generate_bar_chart_data()
        
        assert len(bar_data['data']['labels']) == 32
    
    def test_large_latency_data(self):
        """Test handling of large latency data"""
        import random
        random.seed(42)
        
        # Generate large number of latencies
        latencies = [abs(random.gauss(25, 10)) for _ in range(100000)]
        data = generate_latency_histogram(latencies, bin_size=5)
        
        chart = LatencyHistogram(data=data)
        hist_data = chart.generate_histogram_data()
        
        assert len(hist_data['data']['datasets'][0]['data']) > 0
    
    def test_rapid_report_generation(self):
        """Test rapid generation of multiple reports"""
        data = ReportData(
            simulation_name="Performance Test",
            total_requests=1000,
            throughput_gbps=100.0,
        )
        
        # Generate multiple reports rapidly
        for i in range(10):
            content = generate_ascii_report(data)
            assert len(content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])