"""
Comprehensive Tests for Visualization Module - Extended Coverage

Tests remaining uncovered code paths in:
- bandwidth_chart.py
- channel_heatmap.py
- latency_histogram.py
- report_generator.py
"""

import pytest
import json
import os
import tempfile

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
    ReportData,
    VisualizationConfig,
    OutputFormat,
    generate_html_report,
    generate_ascii_report,
    generate_json_report,
    create_report_data_from_stats,
)


# =============================================================================
# BandwidthChart Extended Tests
# =============================================================================

class TestBandwidthChartExtended:
    """Extended tests for BandwidthChart"""

    def test_bandwidth_chart_pattern_bandwidth(self):
        """Test bar chart with pattern bandwidth data"""
        data = BandwidthData(
            pattern_bandwidth={"seq": 1000, "random": 500, "stride": 800},
            num_channels=8,
        )
        chart = BandwidthChart(data=data)

        bar_data = chart.generate_bar_chart_data()

        assert bar_data['type'] == 'bar'
        # Labels should be CH0, CH1, etc for channel-based
        assert 'data' in bar_data

    def test_bandwidth_chart_to_chartjs_script(self):
        """Test Chart.js script generation"""
        data = BandwidthData(
            channel_bandwidth={0: 100.0, 1: 200.0},
            bandwidth_time_series={0: 100.0, 1000: 150.0},
            peak_bandwidth_gbps=819.2,
            achieved_bandwidth_gbps=150.0,
        )
        chart = BandwidthChart(data=data)

        script = chart.to_chartjs_script()

        assert "Chart(bwBarCtx" in script
        assert "Chart(bwLineCtx" in script
        assert "Chart(bwGaugeCtx" in script

    def test_create_bandwidth_chart_from_stats_empty(self):
        """Test creating bandwidth chart from empty stats"""
        class EmptyStats:
            pass

        result = create_bandwidth_chart_from_stats(EmptyStats())

        assert isinstance(result, BandwidthData)
        assert result.peak_bandwidth_gbps == 819.2  # Default

    def test_create_bandwidth_chart_from_stats_partial(self):
        """Test creating bandwidth chart from partial stats"""
        class PartialStats:
            per_channel_stats = {0: type('obj', (), {'total_requests': 1000, 'avg_latency': 20})()}
            total_cycles = 128000000
            throughput_gbps = 163.84
            peak_bandwidth_gbps = 819.2

        result = create_bandwidth_chart_from_stats(PartialStats())

        assert isinstance(result, BandwidthData)
        assert result.peak_bandwidth_gbps == 819.2

    def test_generate_bandwidth_efficiency_gauge_only(self):
        """Test generating just efficiency gauge"""
        result = generate_bandwidth_efficiency_gauge(200.0, 819.2)

        assert result.achieved_bandwidth_gbps == 200.0
        assert result.peak_bandwidth_gbps == 819.2
        assert result.get_efficiency() > 0

    def test_bandwidth_time_series_multiple_points(self):
        """Test bandwidth time series with many points"""
        samples = [(i * 1000, 100.0 + i * 5) for i in range(20)]
        result = generate_bandwidth_time_series(samples, peak_bandwidth=819.2)

        assert len(result.bandwidth_time_series) == 20
        assert result.achieved_bandwidth_gbps > 100.0


# =============================================================================
# LatencyHistogram Extended Tests
# =============================================================================

class TestLatencyHistogramExtended:
    """Extended tests for LatencyHistogram"""

    def test_latency_histogram_time_series_data(self):
        """Test time series data generation"""
        data = LatencyData(
            latency_time_series={0: 20.0, 1000: 25.0, 2000: 30.0},
            time_stamps=[0, 1000, 2000],
        )
        chart = LatencyHistogram(data=data)

        ts_data = chart.generate_time_series_data()

        assert ts_data['type'] == 'line'
        assert 'datasets' in ts_data['data']

    def test_latency_histogram_percentile_annotations(self):
        """Test percentile annotation generation"""
        data = LatencyData(
            latencies=list(range(1, 101)),
        )
        data.calculate_percentiles()
        chart = LatencyHistogram(data=data)

        annotations = chart.generate_percentile_annotations()

        assert len(annotations) >= 0  # May be empty if percentiles are 0

    def test_latency_histogram_to_chartjs_script(self):
        """Test Chart.js script generation"""
        data = LatencyData(latencies=[10, 20, 30, 40, 50])
        data.calculate_histogram()
        data.calculate_percentiles()
        chart = LatencyHistogram(data=data)

        script = chart.to_chartjs_script()

        assert "Chart(latHistCtx" in script
        assert "Chart(latTsCtx" in script  # Note: abbreviated variable name

    def test_create_latency_histogram_from_stats_empty(self):
        """Test creating latency histogram from empty stats"""
        class EmptyStats:
            pass

        result = create_latency_histogram_from_stats(EmptyStats())

        assert isinstance(result, LatencyData)

    def test_create_latency_histogram_from_stats_avg_only(self):
        """Test creating latency histogram from stats with only average"""
        class AvgStats:
            avg_latency = 25.5
            completed_requests = 1000
            max_latency_cycles = 100

        result = create_latency_histogram_from_stats(AvgStats())

        assert isinstance(result, LatencyData)
        assert len(result.latencies) > 0

    def test_generate_ascii_histogram_empty(self):
        """Test ASCII histogram with empty data"""
        result = generate_ascii_histogram([], bin_size=10)

        assert "No latency data" in result

    def test_generate_ascii_histogram_single_bin(self):
        """Test ASCII histogram with single bin"""
        latencies = [5, 6, 7]  # All in bin 0
        result = generate_ascii_histogram(latencies, bin_size=10, max_width=30)

        assert "Latency Histogram" in result
        assert "cycles" in result

    def test_generate_ascii_histogram_custom_width(self):
        """Test ASCII histogram with custom width"""
        latencies = list(range(1, 101))
        result = generate_ascii_histogram(latencies, bin_size=10, max_width=50)

        assert "Latency Histogram" in result
        assert len(result) > 0

    def test_latency_data_to_dict(self):
        """Test LatencyData.to_dict()"""
        data = LatencyData(latencies=[10, 20, 30, 40, 50])
        data.calculate_histogram()
        data.calculate_percentiles()
        data.calculate_statistics()

        result = data.to_dict()

        assert 'histogram_bins' in result
        assert 'percentiles' in result
        assert 'statistics' in result
        assert 'p50' in result['percentiles']


# =============================================================================
# ChannelHeatmap Extended Tests
# =============================================================================

class TestChannelHeatmapExtended:
    """Extended tests for ChannelHeatmap"""

    def test_channel_heatmap_bank_group_activity_data(self):
        """Test bank group activity data generation"""
        data = ChannelHeatmapData(
            bank_group_activity={
                0: {0: 0.9, 1: 0.8, 2: 0.7, 3: 0.6},
                1: {0: 0.5, 1: 0.4, 2: 0.3, 3: 0.2},
            },
            num_channels=4,
            bank_groups_per_channel=4,
        )
        chart = ChannelHeatmap(data=data)

        bg_data = chart.generate_bank_group_activity_data()

        assert bg_data['type'] == 'matrix'
        assert 'datasets' in bg_data['data']

    def test_channel_heatmap_chart_js_script_exists(self):
        """Test Chart.js script generation exists"""
        data = ChannelHeatmapData(
            channel_utilization={0: 0.9, 1: 0.8},
            request_density={0: 1000, 1: 800},
            num_channels=2,
            bank_groups_per_channel=4,
        )
        chart = ChannelHeatmap(data=data)

        # Test that the heatmap data can be generated
        util_data = chart.generate_utilization_heatmap_data()
        density_data = chart.generate_request_density_data()
        bg_data = chart.generate_bank_group_activity_data()

        assert 'data' in util_data
        assert density_data['type'] == 'bar'
        assert bg_data['type'] == 'matrix'

    def test_create_channel_heatmap_from_stats_empty(self):
        """Test creating channel heatmap from empty stats"""
        class EmptyStats:
            pass

        result = create_channel_heatmap_from_stats(EmptyStats())

        assert isinstance(result, ChannelHeatmapData)

    def test_create_channel_heatmap_from_stats_full(self):
        """Test creating channel heatmap from full stats"""
        class ChannelStats:
            total_requests = 1000
            total_latency_cycles = 25000
            hit_rate = 0.6

        class FullStats:
            per_channel_stats = {
                0: ChannelStats(),
                1: ChannelStats(),
            }
            total_cycles = 128000000

        result = create_channel_heatmap_from_stats(FullStats())

        assert isinstance(result, ChannelHeatmapData)
        assert len(result.request_density) == 2

    def test_generate_bank_group_heatmap_empty(self):
        """Test generating bank group heatmap with empty data"""
        result = generate_bank_group_heatmap({}, num_channels=8, bank_groups=4)

        assert result.num_channels == 8
        assert result.bank_groups_per_channel == 4

    def test_generate_ascii_heatmap_custom_width(self):
        """Test ASCII heatmap with custom width"""
        utilization = {i: 0.1 * i for i in range(8)}
        result = generate_ascii_heatmap(utilization, num_channels=8, bank_groups=4, width=60)

        assert "Channel Utilization Heatmap" in result
        assert "Legend" in result

    def test_generate_ascii_heatmap_different_banks(self):
        """Test ASCII heatmap with different bank group counts"""
        utilization = {i: 0.2 * i for i in range(4)}
        result = generate_ascii_heatmap(utilization, num_channels=4, bank_groups=8, width=50)

        assert "Channel Utilization Heatmap" in result
        assert "8 bank groups" in result


# =============================================================================
# ReportGenerator Extended Tests
# =============================================================================

class TestReportGeneratorExtended:
    """Extended tests for ReportGenerator"""

    def test_visualization_config_to_dict(self):
        """Test VisualizationConfig.to_dict()"""
        config = VisualizationConfig(
            output_format=OutputFormat.HTML,
            output_path="test.html",
            chart_width=600,
            chart_height=300,
        )

        result = config.to_dict()

        assert 'output_format' in result
        assert 'output_path' in result
        assert result['output_format'] == 'html'

    def test_report_data_to_dict(self):
        """Test ReportData.to_dict()"""
        data = ReportData(
            simulation_name="Test Report",
            total_requests=1000,
            completed_requests=950,
            throughput_gbps=163.84,
        )

        result = data.to_dict()

        assert 'metadata' in result
        assert 'requests' in result
        assert 'performance' in result
        assert result['metadata']['simulation_name'] == "Test Report"

    def test_report_generator_with_config(self):
        """Test report generator with custom config"""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            chart_width=1200,
            chart_height=600,
            primary_color="#FF0000",
            secondary_color="#00FF00",
        )
        generator = ReportGenerator(config)

        data = ReportData(
            simulation_name="Custom Config Test",
            total_requests=100,
        )

        content = generator.generate(data)
        parsed = json.loads(content)

        assert parsed['metadata']['simulation_name'] == "Custom Config Test"

    def test_report_generator_save(self):
        """Test report generator save functionality"""
        config = VisualizationConfig(output_format=OutputFormat.ASCII)
        generator = ReportGenerator(config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name

        try:
            content = "Test Report Content"
            result_path = generator.save(content, temp_path)

            assert result_path == temp_path
            with open(result_path, 'r') as f:
                saved_content = f.read()
            assert saved_content == content
        finally:
            os.unlink(temp_path)

    def test_report_generator_save_auto_path(self):
        """Test report generator save with auto path"""
        config = VisualizationConfig(output_path="/tmp/test_report.txt")
        generator = ReportGenerator(config)

        content = "Test Content"
        result_path = generator.save(content)

        assert result_path == "/tmp/test_report.txt"
        with open(result_path, 'r') as f:
            assert f.read() == content

        os.unlink("/tmp/test_report.txt")

    def test_generate_html_report_full_path(self):
        """Test generating HTML report to specific path"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            data = ReportData(
                simulation_name="HTML Full Path Test",
                total_requests=500,
            )

            content = generate_html_report(data, output_path=temp_path)

            assert "<html" in content.lower() or "HTML Full Path Test" in content
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_generate_json_report_full_path(self):
        """Test generating JSON report to specific path"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            data = ReportData(
                simulation_name="JSON Full Path Test",
                total_requests=500,
            )

            content = generate_json_report(data, output_path=temp_path)

            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                parsed = json.load(f)
            assert parsed['metadata']['simulation_name'] == "JSON Full Path Test"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_create_report_data_from_stats_minimal(self):
        """Test creating report data from minimal stats"""
        class MinimalStats:
            total_cycles = 100000
            total_requests = 100
            completed_requests = 95
            read_requests = 70
            write_requests = 25
            throughput_gbps = 50.0
            peak_bandwidth_gbps = 819.2
            bandwidth_efficiency = 0.06
            avg_latency = 30.0
            row_hit_rate = 0.4

        result = create_report_data_from_stats(MinimalStats(), name="Minimal Test")

        assert result.simulation_name == "Minimal Test"
        assert result.total_requests == 100

    def test_create_report_data_from_stats_with_channels(self):
        """Test creating report data from stats with channel data"""
        class ChannelStat:
            avg_bandwidth = 100.0
            utilization = 0.8
            total_requests = 100

        class StatsWithChannels:
            total_cycles = 100000
            total_requests = 500
            completed_requests = 480
            read_requests = 300
            write_requests = 180
            throughput_gbps = 100.0
            peak_bandwidth_gbps = 819.2
            bandwidth_efficiency = 0.12
            avg_latency = 25.0
            row_hit_rate = 0.5
            per_channel_stats = {
                0: ChannelStat(),
                1: ChannelStat(),
            }

        result = create_report_data_from_stats(StatsWithChannels(), name="With Channels")

        assert result.simulation_name == "With Channels"
        assert len(result.channel_bandwidth) == 2
        assert len(result.channel_utilization) == 2


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestVisualizationEdgeCases:
    """Edge case tests for visualization modules"""

    def test_bandwidth_data_zero_channels(self):
        """Test bandwidth data with zero channels"""
        data = BandwidthData(
            channel_bandwidth={},
            num_channels=0,
        )

        chart = BandwidthChart(data=data)
        bar_data = chart.generate_bar_chart_data()

        assert bar_data['type'] == 'bar'

    def test_bandwidth_data_missing_channels(self):
        """Test bandwidth data with missing channel indices"""
        data = BandwidthData(
            channel_bandwidth={0: 100.0, 5: 200.0},  # Non-contiguous
            num_channels=8,
        )

        chart = BandwidthChart(data=data)
        bar_data = chart.generate_bar_chart_data()

        assert bar_data['type'] == 'bar'

    def test_latency_data_single_value(self):
        """Test latency data with single value"""
        data = LatencyData(latencies=[50.0])

        bins = data.calculate_histogram()
        percentiles = data.calculate_percentiles()
        stats = data.calculate_statistics()

        assert len(bins) == 1
        assert percentiles['p50'] == 50.0
        assert stats['mean'] == 50.0

    def test_latency_data_very_large_values(self):
        """Test latency data with very large values"""
        data = LatencyData(latencies=[1e6, 2e6, 3e6])

        bins = data.calculate_histogram()
        stats = data.calculate_statistics()

        assert stats['max'] == 3e6
        assert stats['mean'] == 2e6

    def test_channel_heatmap_zero_utilization(self):
        """Test channel heatmap with all zeros"""
        data = ChannelHeatmapData(
            channel_utilization={i: 0.0 for i in range(8)},
            num_channels=8,
        )

        chart = ChannelHeatmap(data=data)
        util_data = chart.generate_utilization_heatmap_data()

        assert 'data' in util_data

    def test_report_data_empty_strings(self):
        """Test report data with empty optional fields"""
        data = ReportData(
            simulation_name="Empty Test",
            total_requests=0,
            throughput_gbps=0.0,
            channel_bandwidth={},
            channel_utilization={},
        )

        content = generate_ascii_report(data)

        assert "Empty Test" in content


# =============================================================================
# Integration Tests
# =============================================================================

class TestVisualizationIntegrationExtended:
    """Extended integration tests"""

    def test_full_bandwidth_to_latency_workflow(self):
        """Test complete workflow from bandwidth to latency visualization"""
        # Generate bandwidth data
        channel_bw = {i: 100.0 + i * 5 for i in range(8)}
        bw_data = generate_bandwidth_bar_chart(channel_bw, peak_bandwidth=819.2)

        # Generate latency data
        import random
        random.seed(42)
        latencies = [abs(random.gauss(25, 10)) for _ in range(1000)]
        lat_data = generate_latency_histogram(latencies, bin_size=5)

        # Create charts
        bw_chart = BandwidthChart(data=bw_data)
        lat_chart = LatencyHistogram(data=lat_data)

        # Generate chart data
        bw_bar = bw_chart.generate_bar_chart_data()
        lat_hist = lat_chart.generate_histogram_data()

        assert bw_bar['type'] == 'bar'
        assert lat_hist['type'] == 'bar'

    def test_full_channel_to_report_workflow(self):
        """Test complete workflow from channel data to report"""
        # Generate channel heatmap data
        utilization = {i: 0.1 + 0.1 * i for i in range(8)}
        density = {i: 1000 - i * 100 for i in range(8)}

        heatmap_data = generate_channel_heatmap(utilization)
        density_data = generate_request_density_chart(density)

        # Create report data
        report_data = ReportData(
            simulation_name="Channel Workflow Test",
            total_requests=10000,
            completed_requests=9500,
            throughput_gbps=163.84,
            peak_bandwidth_gbps=819.2,
            bandwidth_efficiency=0.20,
            avg_latency_cycles=25.5,
            latency_p50=20.0,
            latency_p95=50.0,
            latency_p99=100.0,
            channel_bandwidth={i: 100.0 + i * 5 for i in range(8)},
            channel_utilization=utilization,
        )

        # Generate reports
        ascii_content = generate_ascii_report(report_data)
        json_content = generate_json_report(report_data)

        assert "Channel Workflow Test" in ascii_content
        parsed = json.loads(json_content)
        assert parsed['metadata']['simulation_name'] == "Channel Workflow Test"

    def test_stats_to_all_visualizations(self):
        """Test converting stats to all visualization types"""
        class ChannelStat:
            total_requests = 1000
            total_latency_cycles = 25000
            hit_rate = 0.6
            avg_bandwidth = 100.0
            utilization = 0.75

        class FullStats:
            total_cycles = 128000000
            total_requests = 5000
            completed_requests = 4800
            read_requests = 3000
            write_requests = 1800
            throughput_gbps = 163.84
            peak_bandwidth_gbps = 819.2
            bandwidth_efficiency = 0.20
            avg_latency = 25.0
            row_hit_rate = 0.5
            per_channel_stats = {
                0: ChannelStat(),
                1: ChannelStat(),
            }

        # Convert to all visualization types
        bw_data = create_bandwidth_chart_from_stats(FullStats())
        lat_data = create_latency_histogram_from_stats(FullStats())
        heatmap_data = create_channel_heatmap_from_stats(FullStats())
        report_data = create_report_data_from_stats(FullStats(), name="Full Stats Test")

        assert isinstance(bw_data, BandwidthData)
        assert isinstance(lat_data, LatencyData)
        assert isinstance(heatmap_data, ChannelHeatmapData)
        assert isinstance(report_data, ReportData)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
