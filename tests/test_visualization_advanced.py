"""
Comprehensive Tests for Advanced Visualization Module

Tests advanced_charts.py components:
- ASCIIRenderer
- ChartConfig
- VisualizationData
- AdvancedVisualizer
- PerformanceAnalyzer
"""

import pytest
import json
import math
import os
import tempfile

from sim.visualization.advanced_charts import (
    ASCIIRenderer,
    ChartConfig,
    ChartType,
    VisualizationData,
    AdvancedVisualizer,
    PerformanceAnalyzer,
    create_visualizer,
    analyze_and_visualize,
)


# =============================================================================
# ChartConfig Tests
# =============================================================================

class TestChartConfig:
    """Tests for ChartConfig dataclass"""

    def test_default_config(self):
        """Test default chart configuration"""
        config = ChartConfig()

        assert config.title == ""
        assert config.width == 80
        assert config.height == 20
        assert config.bar_char == '#'
        assert config.empty_char == ' '
        assert config.show_labels is True
        assert config.show_values is True
        assert config.decimal_places == 2
        assert config.colors_enabled is False

    def test_custom_config(self):
        """Test custom chart configuration"""
        config = ChartConfig(
            title="Test Chart",
            width=100,
            height=30,
            bar_char='*',
            empty_char='.',
            show_labels=False,
            show_values=False,
            decimal_places=3,
            colors_enabled=True,
        )

        assert config.title == "Test Chart"
        assert config.width == 100
        assert config.height == 30
        assert config.bar_char == '*'
        assert config.empty_char == '.'
        assert config.show_labels is False
        assert config.show_values is False
        assert config.decimal_places == 3
        assert config.colors_enabled is True


# =============================================================================
# ChartType Tests
# =============================================================================

class TestChartType:
    """Tests for ChartType enum"""

    def test_chart_types_exist(self):
        """Test all chart types are defined"""
        assert ChartType.BAR.value == "bar"
        assert ChartType.LINE.value == "line"
        assert ChartType.HISTOGRAM.value == "histogram"
        assert ChartType.HEATMAP.value == "heatmap"
        assert ChartType.GAUGE.value == "gauge"
        assert ChartType.ASCII_BAR.value == "ascii_bar"
        assert ChartType.ASCII_HISTOGRAM.value == "ascii_histogram"


# =============================================================================
# ASCIIRenderer Tests
# =============================================================================

class TestASCIIRenderer:
    """Tests for ASCIIRenderer class"""

    def test_colorize_disabled(self):
        """Test colorize with colors disabled"""
        result = ASCIIRenderer.colorize("test", "red", enabled=False)
        assert result == "test"

    def test_colorize_enabled(self):
        """Test colorize with colors enabled"""
        result = ASCIIRenderer.colorize("test", "red", enabled=True)
        assert '\033[91m' in result
        assert '\033[0m' in result
        assert "test" in result

    def test_colorize_unknown_color(self):
        """Test colorize with unknown color"""
        result = ASCIIRenderer.colorize("test", "unknown_color", enabled=True)
        assert "test" in result
        assert '\033[0m' in result  # Should still have reset

    def test_render_bar_chart_empty(self):
        """Test bar chart with empty data"""
        config = ChartConfig(title="Empty Chart")
        result = ASCIIRenderer.render_bar_chart({}, config)
        assert "No data to display" in result

    def test_render_bar_chart_basic(self):
        """Test basic bar chart rendering"""
        config = ChartConfig(title="Test Bar", height=15, width=50)
        data = {"A": 100, "B": 200, "C": 150}
        result = ASCIIRenderer.render_bar_chart(data, config)

        assert "Test Bar" in result
        assert "═" in result or "100" in result

    def test_render_bar_chart_uniform_values(self):
        """Test bar chart with uniform values"""
        config = ChartConfig(title="Uniform")
        data = {"A": 100, "B": 100, "C": 100}
        result = ASCIIRenderer.render_bar_chart(data, config)

        assert "No data" not in result

    def test_render_bar_chart_many_items(self):
        """Test bar chart with many items (truncation)"""
        config = ChartConfig(title="Many Items", width=30)
        data = {f"Item{i}": i * 10 for i in range(50)}
        result = ASCIIRenderer.render_bar_chart(data, config)

        assert "50 items" in result

    def test_render_histogram_empty(self):
        """Test histogram with empty data"""
        config = ChartConfig(title="Empty Hist")
        result = ASCIIRenderer.render_histogram([], config)
        assert "No data to display" in result

    def test_render_histogram_basic(self):
        """Test basic histogram rendering"""
        config = ChartConfig(title="Test Histogram", height=15)
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        result = ASCIIRenderer.render_histogram(values, config)

        assert "Test Histogram" in result
        assert "═" in result or "─" in result

    def test_render_histogram_single_value(self):
        """Test histogram with single value"""
        config = ChartConfig(title="Single")
        values = [42.0]
        result = ASCIIRenderer.render_histogram(values, config)

        assert "No data" not in result

    def test_render_heatmap_empty(self):
        """Test heatmap with empty data"""
        config = ChartConfig(title="Empty Heatmap")
        result = ASCIIRenderer.render_heatmap({}, config)
        assert "No data to display" in result

    def test_render_heatmap_single_row(self):
        """Test heatmap with single row"""
        config = ChartConfig(title="Single Row")
        data = {"CH0": {"BG0": 0.5, "BG1": 0.8}}
        result = ASCIIRenderer.render_heatmap(data, config)

        assert "Single Row" in result

    def test_render_heatmap_multiple_rows(self):
        """Test heatmap with multiple rows"""
        config = ChartConfig(title="Multi Row", height=20)
        data = {
            "CH0": {"BG0": 0.9, "BG1": 0.7, "BG2": 0.5},
            "CH1": {"BG0": 0.3, "BG1": 0.6, "BG2": 0.8},
        }
        result = ASCIIRenderer.render_heatmap(data, config)

        assert "Multi Row" in result
        assert "CH0" in result
        assert "CH1" in result

    def test_render_gauge_basic(self):
        """Test gauge rendering"""
        config = ChartConfig(title="Test Gauge")
        result = ASCIIRenderer.render_gauge(75.0, 100.0, config)

        assert "Test Gauge" in result
        assert "75.00" in result or "100.00" in result

    def test_render_gauge_zero_max(self):
        """Test gauge with zero max value"""
        config = ChartConfig(title="Zero Max")
        result = ASCIIRenderer.render_gauge(50.0, 0.0, config)

        assert "Test" not in result  # Title check
        assert "0.0" in result

    def test_render_gauge_low_status(self):
        """Test gauge low status (< 50%)"""
        config = ChartConfig(title="Low Status", colors_enabled=True)
        result = ASCIIRenderer.render_gauge(30.0, 100.0, config)

        assert "LOW" in result

    def test_render_gauge_medium_status(self):
        """Test gauge medium status (50-80%)"""
        config = ChartConfig(title="Medium Status", colors_enabled=True)
        result = ASCIIRenderer.render_gauge(65.0, 100.0, config)

        assert "MEDIUM" in result

    def test_render_gauge_high_status(self):
        """Test gauge high status (>= 80%)"""
        config = ChartConfig(title="High Status", colors_enabled=True)
        result = ASCIIRenderer.render_gauge(90.0, 100.0, config)

        assert "HIGH" in result


# =============================================================================
# VisualizationData Tests
# =============================================================================

class TestVisualizationData:
    """Tests for VisualizationData dataclass"""

    def test_default_data(self):
        """Test default visualization data"""
        data = VisualizationData()

        assert data.bandwidth_per_channel == {}
        assert data.bandwidth_over_time == []
        assert data.latency_samples == []
        assert data.latency_by_pattern == {}
        assert data.channel_activity == {}
        assert data.power_samples == []
        assert data.power_per_channel == {}
        assert data.rtl_comparison == []
        assert data.timestamp != ""
        assert data.simulation_cycles == 0
        assert data.peak_bandwidth_gbps == 0.0
        assert data.avg_latency_cycles == 0.0

    def test_custom_data(self):
        """Test custom visualization data"""
        data = VisualizationData(
            bandwidth_per_channel={0: 100.0, 1: 200.0},
            bandwidth_over_time=[(0, 0.0), (1000, 150.0)],
            latency_samples=[10, 20, 30],
            latency_by_pattern={"random": [15, 25], "seq": [5, 8]},
            channel_activity={0: {"reads": 100, "writes": 50}},
            power_samples=[1.5, 2.0, 1.8],
            power_per_channel={0: 1.5, 1: 1.8},
            rtl_comparison=[{"match": True, "python_latency": 10, "rtl_latency": 10}],
            simulation_cycles=128000000,
            peak_bandwidth_gbps=819.2,
            avg_latency_cycles=25.0,
        )

        assert len(data.bandwidth_per_channel) == 2
        assert len(data.bandwidth_over_time) == 2
        assert len(data.latency_samples) == 3
        assert "random" in data.latency_by_pattern
        assert 0 in data.channel_activity
        assert len(data.power_samples) == 3
        assert len(data.power_per_channel) == 2
        assert len(data.rtl_comparison) == 1
        assert data.simulation_cycles == 128000000
        assert data.peak_bandwidth_gbps == 819.2


# =============================================================================
# AdvancedVisualizer Tests
# =============================================================================

class TestAdvancedVisualizer:
    """Tests for AdvancedVisualizer class"""

    def test_init_default(self):
        """Test default initialization"""
        viz = AdvancedVisualizer()

        assert viz.colors_enabled is False
        assert viz.renderer == ASCIIRenderer
        assert isinstance(viz.data, VisualizationData)

    def test_init_with_colors(self):
        """Test initialization with colors enabled"""
        viz = AdvancedVisualizer(colors_enabled=True)

        assert viz.colors_enabled is True

    def test_set_data(self):
        """Test setting visualization data"""
        viz = AdvancedVisualizer()
        new_data = VisualizationData(simulation_cycles=100000)

        viz.set_data(new_data)

        assert viz.data.simulation_cycles == 100000

    def test_plot_bandwidth(self):
        """Test bandwidth plotting"""
        viz = AdvancedVisualizer()
        data = {"CH0": 100, "CH1": 200, "CH2": 150}

        result = viz.plot_bandwidth(data, title="Test Bandwidth")

        assert "Test Bandwidth" in result
        assert "CH0" in result or "100" in result

    def test_plot_bandwidth_empty(self):
        """Test bandwidth plotting with empty data"""
        viz = AdvancedVisualizer()

        result = viz.plot_bandwidth({}, title="Empty")

        assert "No data" in result

    def test_plot_latency_histogram(self):
        """Test latency histogram plotting"""
        viz = AdvancedVisualizer()
        latencies = [10, 20, 30, 40, 50]

        result = viz.plot_latency_histogram(latencies, title="Latency", bins=10)

        assert "Latency" in result

    def test_plot_latency_histogram_empty(self):
        """Test latency histogram with empty data"""
        viz = AdvancedVisualizer()

        result = viz.plot_latency_histogram([], title="Empty")

        assert "No data" in result

    def test_plot_channel_activity(self):
        """Test channel activity heatmap plotting"""
        viz = AdvancedVisualizer()
        activity = {
            0: {"commands": 100, "reads": 60, "writes": 40},
            1: {"commands": 150, "reads": 90, "writes": 60},
        }

        result = viz.plot_channel_activity(activity, title="Channel Activity")

        assert "Channel Activity" in result
        assert "CH00" in result or "CH01" in result

    def test_plot_bandwidth_efficiency(self):
        """Test bandwidth efficiency gauge plotting"""
        viz = AdvancedVisualizer()

        result = viz.plot_bandwidth_efficiency(150.0, 200.0, title="Efficiency")

        assert "Efficiency" in result

    def test_generate_bandwidth_report_empty(self):
        """Test bandwidth report with no data"""
        viz = AdvancedVisualizer()

        result = viz.generate_bandwidth_report()

        assert "BANDWIDTH ANALYSIS REPORT" in result

    def test_generate_bandwidth_report_with_data(self):
        """Test bandwidth report with data"""
        viz = AdvancedVisualizer()
        viz.data.bandwidth_per_channel = {0: 100.0, 1: 200.0}
        viz.data.peak_bandwidth_gbps = 819.2
        viz.data.bandwidth_over_time = [(0, 0.0), (1000, 150.0)]

        result = viz.generate_bandwidth_report()

        assert "BANDWIDTH ANALYSIS REPORT" in result
        assert "CH00" in result or "100.00" in result

    def test_generate_latency_report_empty(self):
        """Test latency report with no data"""
        viz = AdvancedVisualizer()

        result = viz.generate_latency_report()

        assert "LATENCY ANALYSIS REPORT" in result

    def test_generate_latency_report_with_data(self):
        """Test latency report with data"""
        viz = AdvancedVisualizer()
        viz.data.latency_samples = [10, 20, 30, 40, 50]
        viz.data.latency_by_pattern = {"random": [15, 25], "seq": [5, 8]}

        result = viz.generate_latency_report()

        assert "LATENCY ANALYSIS REPORT" in result
        assert "random" in result

    def test_generate_channel_report_empty(self):
        """Test channel report with no data"""
        viz = AdvancedVisualizer()

        result = viz.generate_channel_report()

        assert "CHANNEL ANALYSIS REPORT" in result

    def test_generate_channel_report_with_data(self):
        """Test channel report with data"""
        viz = AdvancedVisualizer()
        viz.data.channel_activity = {
            0: {"commands": 100, "reads": 60, "writes": 40},
        }

        result = viz.generate_channel_report()

        assert "CHANNEL ANALYSIS REPORT" in result
        assert "Total Commands" in result

    def test_generate_rtl_comparison_report_empty(self):
        """Test RTL comparison report with no data"""
        viz = AdvancedVisualizer()

        result = viz.generate_rtl_comparison_report()

        assert "RTL CO-SIMULATION COMPARISON REPORT" in result

    def test_generate_rtl_comparison_report_with_matches(self):
        """Test RTL comparison report with matching data"""
        viz = AdvancedVisualizer()
        viz.data.rtl_comparison = [
            {"match": True, "python_latency": 10, "rtl_latency": 10},
            {"match": True, "python_latency": 15, "rtl_latency": 15},
            {"match": False, "python_latency": 20, "rtl_latency": 22},
        ]

        result = viz.generate_rtl_comparison_report()

        assert "RTL CO-SIMULATION COMPARISON REPORT" in result
        assert "Matches:" in result
        assert "Mismatches:" in result
        assert "66.67%" in result  # 2/3 = 66.67%

    def test_generate_rtl_comparison_report_all_match(self):
        """Test RTL comparison report with all matches"""
        viz = AdvancedVisualizer()
        viz.data.rtl_comparison = [
            {"match": True, "python_latency": 10, "rtl_latency": 10},
            {"match": True, "python_latency": 15, "rtl_latency": 15},
        ]

        result = viz.generate_rtl_comparison_report()

        assert "100.00%" in result

    def test_generate_full_report(self):
        """Test full report generation"""
        viz = AdvancedVisualizer()
        viz.data.timestamp = "2026-06-24T00:00:00"
        viz.data.simulation_cycles = 128000000
        viz.data.bandwidth_per_channel = {0: 100.0}
        viz.data.latency_samples = [10, 20, 30]
        viz.data.channel_activity = {0: {"commands": 100}}

        result = viz.generate_full_report()

        assert "HBM UNIFIED SIMULATOR" in result
        assert "BANDWIDTH ANALYSIS REPORT" in result
        assert "LATENCY ANALYSIS REPORT" in result
        assert "CHANNEL ANALYSIS REPORT" in result
        assert "128,000,000" in result

    def test_export_json(self):
        """Test JSON export"""
        viz = AdvancedVisualizer()
        viz.data.bandwidth_per_channel = {0: 100.0}
        viz.data.bandwidth_over_time = [(0, 0.0), (1000, 100.0)]
        viz.data.latency_samples = [10, 20, 30]
        viz.data.peak_bandwidth_gbps = 819.2

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            viz.export_json(temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)

            assert 'bandwidth_per_channel' in data
            assert 'bandwidth_over_time' in data
            assert 'latency_samples' in data
            assert data['bandwidth_per_channel']['0'] == 100.0
        finally:
            os.unlink(temp_path)

    def test_export_html_report(self):
        """Test HTML report export"""
        viz = AdvancedVisualizer()
        viz.data.timestamp = "2026-06-24T00:00:00"
        viz.data.simulation_cycles = 128000000
        viz.data.bandwidth_per_channel = {0: 100.0, 1: 200.0}
        viz.data.avg_latency_cycles = 25.0
        viz.data.peak_bandwidth_gbps = 819.2
        viz.data.latency_samples = [10, 20, 30, 40, 50]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            viz.export_html_report(temp_path)

            with open(temp_path, 'r') as f:
                content = f.read()

            assert "<html>" in content.lower()
            assert "HBM" in content
            assert "128,000,000" in content
        finally:
            os.unlink(temp_path)


# =============================================================================
# PerformanceAnalyzer Tests
# =============================================================================

class TestPerformanceAnalyzer:
    """Tests for PerformanceAnalyzer class"""

    def test_compute_statistics_empty(self):
        """Test statistics with empty list"""
        result = PerformanceAnalyzer.compute_statistics([])

        assert result == {}

    def test_compute_statistics_single_value(self):
        """Test statistics with single value"""
        result = PerformanceAnalyzer.compute_statistics([42.0])

        assert result['count'] == 1
        assert result['mean'] == 42.0
        assert result['median'] == 42.0
        assert result['std_dev'] == 0.0
        assert result['min'] == 42.0
        assert result['max'] == 42.0

    def test_compute_statistics_multiple_values(self):
        """Test statistics with multiple values"""
        values = [1, 2, 3, 4, 5]
        result = PerformanceAnalyzer.compute_statistics(values)

        assert result['count'] == 5
        assert result['mean'] == 3.0
        assert result['median'] == 3.0
        assert result['std_dev'] > 0
        assert result['min'] == 1
        assert result['max'] == 5

    def test_compute_statistics_even_count(self):
        """Test median with even count"""
        values = [1, 2, 3, 4]
        result = PerformanceAnalyzer.compute_statistics(values)

        # Median of [1,2,3,4] is (2+3)/2 = 2.5
        assert result['median'] == 2.5

    def test_detect_outliers_empty(self):
        """Test outlier detection with empty list"""
        result = PerformanceAnalyzer.detect_outliers([])

        assert result == []

    def test_detect_outliers_single_value(self):
        """Test outlier detection with single value"""
        result = PerformanceAnalyzer.detect_outliers([42.0])

        assert result == []

    def test_detect_outliers_two_values(self):
        """Test outlier detection with two values"""
        result = PerformanceAnalyzer.detect_outliers([1.0, 2.0])

        assert result == []

    def test_detect_outliers_normal_distribution(self):
        """Test outlier detection with normal distribution"""
        import random
        random.seed(42)
        values = [50.0]  # Center value
        values.extend([random.gauss(50, 5) for _ in range(20)])

        # Add clear outliers
        outliers = [100.0, 150.0, 200.0, 250.0]
        values.extend(outliers)

        result = PerformanceAnalyzer.detect_outliers(values, threshold=2.0)

        # Should detect at least some outliers
        assert len(result) >= 1

    def test_compute_percentiles_empty(self):
        """Test percentiles with empty list"""
        result = PerformanceAnalyzer.compute_percentiles([])

        assert result == {}

    def test_compute_percentiles_default(self):
        """Test percentiles with default percentiles"""
        values = list(range(1, 101))  # 1 to 100
        result = PerformanceAnalyzer.compute_percentiles(values)

        assert 50 in result
        assert 75 in result
        assert 90 in result
        assert 95 in result
        assert 99 in result

        # Check approximate values (boundaries may vary slightly)
        assert 49 <= result[50] <= 51
        assert 74 <= result[75] <= 76

    def test_compute_percentiles_custom(self):
        """Test percentiles with custom percentiles"""
        values = list(range(1, 101))
        result = PerformanceAnalyzer.compute_percentiles(values, [25, 50, 75])

        assert 25 in result
        assert 50 in result
        assert 75 in result
        assert 90 not in result

    def test_compare_results_empty(self):
        """Test comparing with empty baseline"""
        result = PerformanceAnalyzer.compare_results({}, {})

        assert result['metrics'] == []
        assert result['regressions'] == []
        assert result['improvements'] == []

    def test_compare_results_no_change(self):
        """Test comparing results with no change"""
        baseline = {"throughput": 100.0}
        current = {"throughput": 100.0}

        result = PerformanceAnalyzer.compare_results(baseline, current)

        assert len(result['metrics']) == 1
        assert result['metrics'][0]['diff'] == 0.0
        assert result['metrics'][0]['pct_change'] == 0.0
        assert result['regressions'] == []
        assert result['improvements'] == []

    def test_compare_results_improvement(self):
        """Test comparing results with improvement (>5%)"""
        baseline = {"throughput": 100.0}
        current = {"throughput": 120.0}  # 20% improvement

        result = PerformanceAnalyzer.compare_results(baseline, current)

        assert result['improvements'] == ["throughput"]
        assert result['metrics'][0]['pct_change'] == 20.0

    def test_compare_results_regression(self):
        """Test comparing results with regression (<-5%)"""
        baseline = {"throughput": 100.0}
        current = {"throughput": 90.0}  # 10% regression

        result = PerformanceAnalyzer.compare_results(baseline, current)

        assert result['regressions'] == ["throughput"]
        assert result['metrics'][0]['pct_change'] == -10.0

    def test_compare_results_zero_baseline(self):
        """Test comparing with zero baseline value"""
        baseline = {"throughput": 0.0}
        current = {"throughput": 100.0}

        result = PerformanceAnalyzer.compare_results(baseline, current)

        assert result['metrics'][0]['pct_change'] == 0.0  # Should handle div by zero


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_create_visualizer_default(self):
        """Test create_visualizer with defaults"""
        viz = create_visualizer()

        assert isinstance(viz, AdvancedVisualizer)
        assert viz.colors_enabled is False

    def test_create_visualizer_with_colors(self):
        """Test create_visualizer with colors"""
        viz = create_visualizer(colors=True)

        assert isinstance(viz, AdvancedVisualizer)
        assert viz.colors_enabled is True

    def test_analyze_and_visualize_empty(self):
        """Test analyze_and_visualize with empty stats"""
        stats = {}

        result = analyze_and_visualize(stats)

        assert "HBM UNIFIED SIMULATOR" in result
        assert "BANDWIDTH ANALYSIS REPORT" in result

    def test_analyze_and_visualize_full(self):
        """Test analyze_and_visualize with complete stats"""
        stats = {
            'total_cycles': 128000000,
            'throughput_gbps': 163.84,
            'latency_histogram': [10, 20, 30, 40, 50],
            'channel_stats': {
                0: {"commands": 100, "reads": 60, "writes": 40},
                1: {"commands": 150, "reads": 90, "writes": 60},
            },
        }

        result = analyze_and_visualize(stats)

        assert "HBM UNIFIED SIMULATOR" in result
        assert "128,000,000" in result


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_bar_chart_with_negative_values(self):
        """Test bar chart with negative values"""
        config = ChartConfig(title="Negative")
        data = {"A": -50, "B": 100, "C": -25}

        result = ASCIIRenderer.render_bar_chart(data, config)

        assert "No data" not in result

    def test_bar_chart_zero_range(self):
        """Test bar chart with zero range (all same values)"""
        config = ChartConfig(title="Zero Range")
        data = {"A": 100, "B": 100, "C": 100}

        result = ASCIIRenderer.render_bar_chart(data, config)

        assert "No data" not in result

    def test_histogram_with_identical_values(self):
        """Test histogram with identical values"""
        config = ChartConfig(title="Identical")
        values = [50, 50, 50, 50, 50]

        result = ASCIIRenderer.render_histogram(values, config)

        assert "No data" not in result

    def test_heatmap_with_zero_activity(self):
        """Test heatmap with all zero values"""
        config = ChartConfig(title="Zero Activity")
        data = {"CH0": {"BG0": 0, "BG1": 0}}

        result = ASCIIRenderer.render_heatmap(data, config)

        assert "CH0" in result

    def test_statistics_with_constant_values(self):
        """Test statistics with constant values"""
        values = [10.0] * 100

        result = PerformanceAnalyzer.compute_statistics(values)

        assert result['mean'] == 10.0
        assert result['std_dev'] == 0.0
        assert result['min'] == 10.0
        assert result['max'] == 10.0

    def test_statistics_with_large_numbers(self):
        """Test statistics with large numbers"""
        values = [1e10 + i for i in range(100)]

        result = PerformanceAnalyzer.compute_statistics(values)

        assert result['count'] == 100
        assert result['mean'] > 1e10

    def test_percentiles_with_identical_values(self):
        """Test percentiles with identical values"""
        values = [50.0] * 100

        result = PerformanceAnalyzer.compute_percentiles(values)

        assert all(v == 50.0 for v in result.values())


# =============================================================================
# Integration Tests
# =============================================================================

class TestAdvancedVisualizationIntegration:
    """Integration tests for complete visualization workflows"""

    def test_full_workflow_bandwidth_to_report(self):
        """Test complete workflow from bandwidth data to report"""
        # Create visualizer
        viz = create_visualizer(colors=False)

        # Set bandwidth data
        viz.data.bandwidth_per_channel = {
            0: 100.0, 1: 120.0, 2: 90.0, 3: 110.0,
            4: 80.0, 5: 130.0, 6: 95.0, 7: 115.0,
        }
        viz.data.bandwidth_over_time = [(0, 0), (1000, 105), (2000, 110)]
        viz.data.peak_bandwidth_gbps = 819.2

        # Generate report
        report = viz.generate_bandwidth_report()

        assert "BANDWIDTH ANALYSIS REPORT" in report
        assert "Per-Channel Bandwidth" in report

    def test_full_workflow_latency_to_report(self):
        """Test complete workflow from latency data to report"""
        import random
        random.seed(42)

        viz = create_visualizer()

        # Generate realistic latency data
        viz.data.latency_samples = [abs(random.gauss(25, 10)) for _ in range(1000)]
        viz.data.latency_by_pattern = {
            "sequential": [abs(random.gauss(15, 5)) for _ in range(500)],
            "random": [abs(random.gauss(35, 15)) for _ in range(500)],
        }

        # Generate report
        report = viz.generate_latency_report()

        assert "LATENCY ANALYSIS REPORT" in report
        assert "Sample Count" in report
        assert "sequential" in report
        assert "random" in report

    def test_full_workflow_rtl_comparison(self):
        """Test complete RTL comparison workflow"""
        import random
        random.seed(42)

        viz = create_visualizer()

        # Generate comparison data
        viz.data.rtl_comparison = []
        for i in range(100):
            python_lat = abs(random.gauss(25, 10))
            rtl_lat = python_lat + random.gauss(0, 1)  # Small difference
            viz.data.rtl_comparison.append({
                "match": abs(python_lat - rtl_lat) < 2,
                "python_latency": python_lat,
                "rtl_latency": rtl_lat,
            })

        # Generate report
        report = viz.generate_rtl_comparison_report()

        assert "RTL CO-SIMULATION COMPARISON REPORT" in report
        assert "Match Rate" in report

    def test_export_and_reimport_json(self):
        """Test JSON export and reimport workflow"""
        viz1 = create_visualizer()
        viz1.data.bandwidth_per_channel = {0: 100.0, 1: 200.0}
        viz1.data.latency_samples = [10, 20, 30]
        viz1.data.peak_bandwidth_gbps = 819.2

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            # Export
            viz1.export_json(temp_path)

            # Reimport
            with open(temp_path, 'r') as f:
                data = json.load(f)

            assert data['bandwidth_per_channel']['0'] == 100.0
            assert data['bandwidth_per_channel']['1'] == 200.0
            assert data['latency_samples'] == [10, 20, 30]
        finally:
            os.unlink(temp_path)


# =============================================================================
# Performance Tests
# =============================================================================

class TestAdvancedVisualizationPerformance:
    """Performance tests for advanced visualization"""

    def test_large_bandwidth_data(self):
        """Test with large number of channels (HBM4 with 32 channels)"""
        viz = create_visualizer()
        viz.data.bandwidth_per_channel = {i: 50.0 + (i % 8) * 5 for i in range(32)}

        result = viz.generate_bandwidth_report()

        assert "BANDWIDTH ANALYSIS REPORT" in result

    def test_large_latency_data(self):
        """Test with large number of latency samples"""
        import random
        random.seed(42)

        viz = create_visualizer()
        viz.data.latency_samples = [abs(random.gauss(25, 10)) for _ in range(100000)]

        result = viz.generate_latency_report()

        assert "LATENCY ANALYSIS REPORT" in result
        assert "100000" in result  # Number without comma

    def test_many_outliers_detection(self):
        """Test outlier detection with many values"""
        import random
        random.seed(42)

        values = [random.gauss(50, 5) for _ in range(1000)]
        values.extend([150 + i for i in range(50)])  # Many outliers

        outliers = PerformanceAnalyzer.detect_outliers(values, threshold=2.0)

        # Should detect many outliers
        assert len(outliers) > 40

    def test_compare_many_metrics(self):
        """Test comparing many performance metrics"""
        baseline = {f"metric_{i}": 100.0 + i for i in range(100)}
        # Current has > 5% improvement on even indices, < -5% on odd indices
        current = {f"metric_{i}": 100.0 + i + (10 if i % 2 == 0 else -15) for i in range(100)}

        result = PerformanceAnalyzer.compare_results(baseline, current)

        assert len(result['metrics']) == 100
        # With 10% change on even indices: improvements
        assert len(result['improvements']) > 0
        # With -15% change on odd indices: regressions
        assert len(result['regressions']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
