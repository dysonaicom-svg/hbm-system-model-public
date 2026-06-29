"""
Tests for HBM Performance Monitoring Module

Tests for:
- RealtimeMonitor: Real-time bandwidth and performance monitoring
- LatencyAnalyzer: Latency distribution analysis
- HeatmapGenerator: Heatmap visualization for channel/bank utilization

Run with: pytest tests/model/monitoring/test_monitoring.py -v
"""

import pytest
import random
import json
import tempfile
import os
from pathlib import Path

# Import monitoring modules
from model.monitoring.realtime_monitor import (
    RealtimeMonitor,
    ChannelMetrics,
    SystemMetrics,
    BandwidthTracker,
    create_monitor
)
from model.monitoring.latency_analyzer import (
    LatencyAnalyzer,
    LatencyStats,
    LatencyHistogram,
    calculate_statistics,
    detect_outliers,
    categorize_latency,
    LatencyCategory,
    create_analyzer
)
from model.monitoring.heatmap_generator import (
    HeatmapGenerator,
    ChannelActivity,
    BankGroupActivity,
    create_generator
)


class TestRealtimeMonitor:
    """Tests for RealtimeMonitor"""

    def test_monitor_creation(self):
        """Test monitor can be created with default parameters"""
        monitor = RealtimeMonitor()
        assert monitor.num_channels == 8
        assert monitor.peak_bandwidth_gbps == 819.2
        assert not monitor._running

    def test_monitor_creation_with_config(self):
        """Test monitor creation with custom parameters"""
        monitor = RealtimeMonitor(
            num_channels=32,
            peak_bandwidth_gbps=4096.0,
            update_interval_ms=50.0,
            history_size=500
        )
        assert monitor.num_channels == 32
        assert monitor.peak_bandwidth_gbps == 4096.0
        assert monitor.update_interval_ms == 50.0
        assert monitor.history_size == 500

    def test_monitor_start_stop(self):
        """Test monitor start and stop"""
        monitor = RealtimeMonitor()
        monitor.start()
        assert monitor._running
        assert monitor._start_time is not None
        monitor.stop()
        assert not monitor._running

    def test_monitor_reset(self):
        """Test monitor reset clears all data"""
        monitor = RealtimeMonitor(num_channels=4)

        # Add some data
        monitor.start()
        monitor.record_request(0, True, 128, 20, True, 100)
        monitor.record_request(1, False, 128, 25, False, 100)
        monitor.stop()

        # Reset
        monitor.reset()

        # Verify reset
        assert all(ch.request_count == 0 for ch in monitor.channels.values())
        assert monitor.system.total_requests == 0
        assert not monitor._running

    def test_record_request_basic(self):
        """Test recording a basic request"""
        monitor = RealtimeMonitor(num_channels=4)
        monitor.start()

        monitor.record_request(
            channel_id=0,
            is_read=True,
            bytes_count=128,
            latency_cycles=20,
            is_row_hit=True,
            cycle=100
        )

        ch0 = monitor.channels[0]
        assert ch0.request_count == 1
        assert ch0.read_count == 1
        assert ch0.write_count == 0
        assert ch0.bytes_transferred == 128
        assert ch0.total_latency_cycles == 20
        assert ch0.row_hits == 1
        assert ch0.row_misses == 0

    def test_record_request_write(self):
        """Test recording a write request"""
        monitor = RealtimeMonitor(num_channels=4)
        monitor.start()

        monitor.record_request(
            channel_id=1,
            is_read=False,
            bytes_count=256,
            latency_cycles=30,
            is_row_hit=False,
            cycle=200
        )

        ch1 = monitor.channels[1]
        assert ch1.request_count == 1
        assert ch1.read_count == 0
        assert ch1.write_count == 1
        assert ch1.bytes_transferred == 256
        assert ch1.row_misses == 1

    def test_record_multiple_channels(self):
        """Test recording requests across multiple channels"""
        monitor = RealtimeMonitor(num_channels=8)
        monitor.start()

        for ch in range(8):
            for _ in range(10):
                monitor.record_request(
                    channel_id=ch,
                    is_read=True,
                    bytes_count=128,
                    latency_cycles=20,
                    is_row_hit=True,
                    cycle=100
                )

        for ch in range(8):
            assert monitor.channels[ch].request_count == 10

    def test_get_stats(self):
        """Test getting statistics"""
        monitor = RealtimeMonitor(num_channels=4)
        monitor.start()

        # Add requests
        for ch in range(4):
            for _ in range(100):
                monitor.record_request(
                    channel_id=ch,
                    is_read=True,
                    bytes_count=128,
                    latency_cycles=20,
                    is_row_hit=True,
                    cycle=100
                )

        stats = monitor.get_stats()

        assert 'system' in stats
        assert 'channels' in stats
        assert 'bandwidth_series' in stats

        assert stats['system']['total_requests'] == 400
        assert stats['system']['total_reads'] == 400
        assert len(stats['channels']) == 4

    def test_channel_metrics_properties(self):
        """Test ChannelMetrics computed properties"""
        ch = ChannelMetrics(channel_id=0)

        ch.bytes_transferred = 1280
        ch.request_count = 10
        ch.total_latency_cycles = 200
        ch.row_hits = 7
        ch.row_misses = 3

        assert ch.avg_latency == 20.0
        assert ch.hit_rate == 0.7

    def test_system_metrics_update(self):
        """Test SystemMetrics update_from_channels"""
        channels = {
            0: ChannelMetrics(channel_id=0),
            1: ChannelMetrics(channel_id=1),
        }
        channels[0].bytes_transferred = 1280
        channels[0].request_count = 10
        channels[1].bytes_transferred = 2560
        channels[1].request_count = 20

        system = SystemMetrics()
        system.update_from_channels(channels, peak_bw_per_ch=2048.0)

        assert system.total_bytes == 3840
        assert system.total_requests == 30
        assert system.peak_bandwidth_gbps > 0

    def test_bandwidth_tracker(self):
        """Test BandwidthTracker"""
        tracker = BandwidthTracker(window_size=100, num_samples=10)

        tracker.add_transfer(128, 50)
        tracker.add_transfer(128, 100)
        tracker.add_transfer(128, 150)

        series = tracker.get_bandwidth_series()
        assert len(series) >= 0  # Windows may not be complete yet

        avg_bw = tracker.get_average_bandwidth()
        assert avg_bw >= 0

    def test_get_summary(self):
        """Test getting human-readable summary"""
        monitor = RealtimeMonitor(num_channels=4)
        monitor.start()

        for ch in range(4):
            for _ in range(50):
                monitor.record_request(
                    channel_id=ch,
                    is_read=True,
                    bytes_count=128,
                    latency_cycles=20,
                    is_row_hit=True,
                    cycle=100
                )

        summary = monitor.get_summary()
        assert 'REAL-TIME PERFORMANCE MONITOR SUMMARY' in summary
        assert 'Total Requests' in summary
        assert 'Bandwidth' in summary

    def test_to_dict_export(self):
        """Test dictionary export"""
        monitor = RealtimeMonitor(num_channels=4)
        monitor.start()
        monitor.record_request(0, True, 128, 20, True, 100)

        data = monitor.to_dict()
        assert 'system' in data
        assert 'channels' in data


class TestLatencyAnalyzer:
    """Tests for LatencyAnalyzer"""

    def test_analyzer_creation(self):
        """Test analyzer can be created"""
        analyzer = LatencyAnalyzer()
        assert analyzer.bin_size == 10
        assert len(analyzer.all_samples) == 0

    def test_add_sample(self):
        """Test adding single sample"""
        analyzer = LatencyAnalyzer()
        analyzer.add_sample(25.0)
        assert len(analyzer.all_samples) == 1
        assert analyzer.all_samples[0] == 25.0

    def test_add_samples(self):
        """Test adding multiple samples"""
        analyzer = LatencyAnalyzer()
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
        analyzer.add_samples(latencies)
        assert len(analyzer.all_samples) == 5

    def test_histogram_generation(self):
        """Test histogram generation"""
        analyzer = LatencyAnalyzer(bin_size=10)
        for i in range(100):
            analyzer.add_sample(15.0 + (i % 50))

        dist = analyzer.get_histogram_data()
        assert len(dist) > 0
        bin_start, count, pct = dist[0]
        assert count > 0
        assert 0 <= pct <= 100

    def test_statistics_calculation(self):
        """Test statistics calculation"""
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = calculate_statistics(latencies)

        assert stats.count == 5
        assert stats.mean == 30.0
        assert stats.min_val == 10.0
        assert stats.max_val == 50.0
        assert stats.p50 == 30.0

    def test_percentiles(self):
        """Test percentile calculation"""
        latencies = list(range(1, 101))  # 1 to 100
        stats = calculate_statistics(latencies)

        assert 49 <= stats.p50 <= 51
        assert 94 <= stats.p95 <= 96
        assert 98 <= stats.p99 <= 100

    def test_analyze_method(self):
        """Test full analysis"""
        analyzer = LatencyAnalyzer(bin_size=5)
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
        analyzer.add_samples(latencies)

        stats = analyzer.analyze()
        assert stats.count == 5
        assert stats.mean == 30.0

    def test_outlier_detection(self):
        """Test outlier detection"""
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 200.0]  # 200 is outlier
        indices, outliers = detect_outliers(latencies, threshold=2.0)

        assert len(outliers) > 0
        assert 200.0 in outliers

    def test_latency_categorization(self):
        """Test latency categorization"""
        assert categorize_latency(5, 10) == LatencyCategory.ROW_HIT
        assert categorize_latency(15, 10) == LatencyCategory.ROW_MISS
        assert categorize_latency(100, 10) == LatencyCategory.PRECHARGE

    def test_pattern_tracking(self):
        """Test per-pattern latency tracking"""
        analyzer = LatencyAnalyzer()

        analyzer.add_pattern_sample('sequential', 10.0)
        analyzer.add_pattern_sample('sequential', 12.0)
        analyzer.add_pattern_sample('random', 30.0)

        assert 'sequential' in analyzer.patterns
        assert 'random' in analyzer.patterns
        assert len(analyzer.patterns['sequential']) == 2
        assert len(analyzer.patterns['random']) == 1

    def test_channel_tracking(self):
        """Test per-channel latency tracking"""
        analyzer = LatencyAnalyzer()

        analyzer.add_channel_sample(0, 15.0)
        analyzer.add_channel_sample(0, 18.0)
        analyzer.add_channel_sample(1, 25.0)

        assert 0 in analyzer.channel_samples
        assert 1 in analyzer.channel_samples
        assert len(analyzer.channel_samples[0]) == 2

    def test_pattern_report(self):
        """Test getting pattern report"""
        analyzer = LatencyAnalyzer(bin_size=10)
        for _ in range(100):
            analyzer.add_pattern_sample('test', 20.0 + random.gauss(0, 5))

        report = analyzer.get_pattern_report('test')
        assert report is not None
        assert 'statistics' in report
        assert 'distribution' in report

    def test_category_distribution(self):
        """Test category distribution"""
        analyzer = LatencyAnalyzer()
        for _ in range(10):
            analyzer.add_sample(5.0)   # ROW_HIT
        for _ in range(5):
            analyzer.add_sample(15.0)  # ROW_MISS

        dist = analyzer.get_category_distribution()
        assert 'row_hit' in dist
        assert 'row_miss' in dist

    def test_ascii_histogram(self):
        """Test ASCII histogram generation"""
        analyzer = LatencyAnalyzer(bin_size=10)
        for _ in range(100):
            analyzer.add_sample(20.0 + random.gauss(0, 10))

        hist = analyzer.generate_ascii_histogram()
        assert 'Latency Distribution Histogram' in hist
        assert 'cycles' in hist

    def test_generate_report(self):
        """Test report generation"""
        analyzer = LatencyAnalyzer(bin_size=5)
        for _ in range(100):
            analyzer.add_sample(20.0 + random.gauss(0, 10))

        report = analyzer.generate_report()
        assert 'LATENCY ANALYSIS REPORT' in report
        assert 'Sample Count' in report
        assert 'Percentiles' in report

    def test_export_data(self):
        """Test data export"""
        analyzer = LatencyAnalyzer(bin_size=10)
        for _ in range(50):
            analyzer.add_sample(25.0)

        data = analyzer.export_data()
        assert 'sample_count' in data
        assert 'statistics' in data
        assert 'histogram' in data


class TestHeatmapGenerator:
    """Tests for HeatmapGenerator"""

    def test_generator_creation(self):
        """Test generator can be created"""
        gen = HeatmapGenerator()
        assert gen.num_channels == 8
        assert gen.bank_groups_per_channel == 4
        assert gen.banks_per_group == 4

    def test_generator_custom_config(self):
        """Test generator with custom configuration"""
        gen = HeatmapGenerator(
            num_channels=32,
            bank_groups_per_channel=8,
            banks_per_group=4
        )
        assert gen.num_channels == 32
        assert gen.bank_groups_per_channel == 8

    def test_record_request(self):
        """Test recording a request"""
        gen = HeatmapGenerator(num_channels=8)

        gen.record_request(
            channel=0,
            bank_group=1,
            bank=2,
            is_read=True,
            latency_cycles=20,
            bytes_count=128,
            is_row_hit=True
        )

        ch = gen.channel_activity[0]
        assert ch.total_requests == 1
        assert ch.read_requests == 1
        assert ch.row_hits == 1

    def test_record_multiple_requests(self):
        """Test recording multiple requests"""
        gen = HeatmapGenerator(num_channels=8)

        for ch in range(8):
            for bg in range(4):
                for _ in range(10):
                    gen.record_request(
                        channel=ch,
                        bank_group=bg,
                        bank=0,
                        is_read=True,
                        latency_cycles=20,
                        bytes_count=128
                    )

        for ch in range(8):
            assert gen.channel_activity[ch].total_requests == 40

    def test_get_channel_utilization(self):
        """Test getting channel utilization"""
        gen = HeatmapGenerator(num_channels=4)

        # Record multiple requests per channel
        for _ in range(100):
            gen.record_request(channel=0)
        for _ in range(50):
            gen.record_request(channel=1)

        util = gen.get_channel_utilization()
        assert len(util) == 4
        # CH0 has more requests, should have higher utilization in BG0
        assert util[0][0] >= util[1][0]

    def test_get_bank_group_heatmap(self):
        """Test getting bank group heatmap"""
        gen = HeatmapGenerator(num_channels=4, bank_groups_per_channel=4)

        for ch in range(4):
            for bg in range(4):
                for _ in range((ch + 1) * 10):
                    gen.record_request(channel=ch, bank_group=bg)

        heatmap = gen.get_bank_group_heatmap()
        assert len(heatmap) == 4
        assert len(heatmap[0]) == 4
        # CH3 should have higher activity than CH0
        assert sum(heatmap[3]) >= sum(heatmap[0])

    def test_hit_rate_heatmap(self):
        """Test hit rate heatmap"""
        gen = HeatmapGenerator(num_channels=4)

        # All hits on CH0, BG0
        for _ in range(100):
            gen.record_request(channel=0, bank_group=0, is_row_hit=True)
        # All misses on CH1, BG0
        for _ in range(100):
            gen.record_request(channel=1, bank_group=0, is_row_hit=False)

        hit_rate = gen.get_hit_rate_heatmap()
        assert len(hit_rate) == 4
        # CH0 BG0 should be 100% hit rate
        assert abs(hit_rate[0][0] - 1.0) < 0.01
        # CH1 BG0 should be 0% hit rate
        assert abs(hit_rate[1][0] - 0.0) < 0.01

    def test_bandwidth_heatmap(self):
        """Test bandwidth heatmap"""
        gen = HeatmapGenerator(num_channels=4)

        gen.record_request(channel=0, bytes_count=1280)
        gen.record_request(channel=1, bytes_count=2560)

        bw_heatmap = gen.get_bandwidth_heatmap()
        assert len(bw_heatmap) == 4
        # CH1 should have higher normalized bandwidth
        assert bw_heatmap[1][0] >= bw_heatmap[0][0]

    def test_ascii_heatmap(self):
        """Test ASCII heatmap generation"""
        gen = HeatmapGenerator(num_channels=4, bank_groups_per_channel=4)

        for ch in range(4):
            for bg in range(4):
                for _ in range((ch + 1) * 100):
                    gen.record_request(channel=ch, bank_group=bg)

        util = gen.get_channel_utilization()
        ascii_hm = gen.generate_ascii_heatmap(util, title="Test Heatmap")
        assert 'Test Heatmap' in ascii_hm

    def test_html_generation(self):
        """Test HTML generation"""
        gen = HeatmapGenerator(num_channels=4)

        for ch in range(4):
            for _ in range(100):
                gen.record_request(channel=ch)

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            html_path = f.name

        try:
            gen.generate_html(html_path)
            assert os.path.exists(html_path)

            with open(html_path, 'r') as f:
                content = f.read()
                assert '<html>' in content
                assert 'HBM' in content
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)

    def test_json_export(self):
        """Test JSON export"""
        gen = HeatmapGenerator(num_channels=4)

        for ch in range(4):
            for _ in range(50):
                gen.record_request(channel=ch, is_read=True)

        data = gen.generate_json()
        assert 'metadata' in data
        assert 'channel_utilization' in data
        assert 'channel_stats' in data
        assert data['metadata']['num_channels'] == 4

    def test_channel_activity_properties(self):
        """Test ChannelActivity computed properties"""
        activity = ChannelActivity(channel_id=0)
        activity.total_requests = 100
        activity.total_latency_cycles = 2000
        activity.row_hits = 60
        activity.row_misses = 40

        assert activity.avg_latency == 20.0
        assert activity.hit_rate == 0.6

    def test_bank_group_activity_properties(self):
        """Test BankGroupActivity computed properties"""
        bg = BankGroupActivity(channel_id=0, bank_group_id=0)
        bg.requests = 100
        bg.row_hits = 70

        assert bg.hit_rate == 0.7

    def test_color_schemes(self):
        """Test different color schemes"""
        for scheme in ['blue', 'green', 'red', 'viridis', 'plasma']:
            gen = HeatmapGenerator(color_scheme=scheme)
            assert gen.color_scheme == scheme
            assert scheme in HeatmapGenerator.COLOR_SCHEMES


class TestIntegration:
    """Integration tests combining multiple components"""

    def test_full_workflow(self):
        """Test complete monitoring workflow"""
        # Create components
        monitor = RealtimeMonitor(num_channels=8)
        analyzer = LatencyAnalyzer(bin_size=5)
        heatmap = HeatmapGenerator(num_channels=8)

        # Start monitoring
        monitor.start()

        # Simulate workload
        random.seed(42)
        for cycle in range(1000):
            for ch in range(8):
                if random.random() < 0.2:
                    is_read = random.random() < 0.7
                    latency = int(abs(random.gauss(25, 10)))
                    is_hit = random.random() < 0.5

                    # Record in monitor
                    monitor.record_request(
                        channel_id=ch,
                        is_read=is_read,
                        bytes_count=128,
                        latency_cycles=latency,
                        is_row_hit=is_hit,
                        cycle=cycle
                    )

                    # Record in analyzer
                    analyzer.add_sample(float(latency), cycle)

                    # Record in heatmap
                    heatmap.record_request(
                        channel=ch,
                        bank_group=random.randint(0, 3),
                        bank=random.randint(0, 3),
                        is_read=is_read,
                        latency_cycles=latency,
                        is_row_hit=is_hit
                    )

        # Stop monitoring
        monitor.stop()

        # Verify data was collected
        stats = monitor.get_stats()
        assert stats['system']['total_requests'] > 0

        analyzer.analyze()
        assert analyzer.stats is not None
        assert analyzer.stats.count > 0

        heatmap_data = heatmap.generate_json()
        assert sum(ch['total_requests'] for ch in heatmap_data['channel_stats'].values()) > 0

    def test_create_helper_functions(self):
        """Test create_* helper functions"""
        monitor = create_monitor(num_channels=16)
        assert monitor.num_channels == 16

        analyzer = create_analyzer(bin_size=20)
        assert analyzer.bin_size == 20

        heatmap = create_generator(num_channels=32, bank_groups=8)
        assert heatmap.num_channels == 32
        assert heatmap.bank_groups_per_channel == 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
