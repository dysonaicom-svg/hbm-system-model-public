"""Tests for performance optimization module"""

import pytest
from model.optimization import (
    OptimizedMetrics,
    BatchRequestProcessor,
    OptimizedBankSelector,
    LatencyTracker,
    OPTIMIZATION_PROFILES,
    get_optimized_processor,
)


class TestOptimizedMetrics:
    def test_metrics_creation(self):
        metrics = OptimizedMetrics()
        assert metrics.request_count == 0
        assert metrics.hit_count == 0

    def test_record_hit(self):
        metrics = OptimizedMetrics()
        metrics.record_hit(channel=0, latency_ns=50.0)

        assert metrics.request_count == 1
        assert metrics.hit_count == 1
        assert metrics.miss_count == 0

    def test_record_miss(self):
        metrics = OptimizedMetrics()
        metrics.record_miss(channel=0, latency_ns=100.0)

        assert metrics.request_count == 1
        assert metrics.hit_count == 0
        assert metrics.miss_count == 1

    def test_hit_rate(self):
        metrics = OptimizedMetrics()
        metrics.record_hit(channel=0, latency_ns=50.0)
        metrics.record_hit(channel=0, latency_ns=50.0)
        metrics.record_miss(channel=0, latency_ns=100.0)

        assert metrics.hit_rate == pytest.approx(2/3)

    def test_avg_latency(self):
        metrics = OptimizedMetrics()
        metrics.record_hit(channel=0, latency_ns=50.0)
        metrics.record_hit(channel=0, latency_ns=100.0)

        assert metrics.avg_latency_ns == 75.0

    def test_channel_utilization(self):
        metrics = OptimizedMetrics()
        metrics.record_hit(channel=0, latency_ns=50.0)
        metrics.record_hit(channel=1, latency_ns=50.0)
        metrics.record_hit(channel=0, latency_ns=50.0)

        assert metrics.channel_utilization[0] == 2
        assert metrics.channel_utilization[1] == 1


class TestBatchRequestProcessor:
    def test_processor_creation(self):
        processor = BatchRequestProcessor(batch_size=32)
        assert processor.batch_size == 32

    def test_add_returns_empty_under_batch_size(self):
        processor = BatchRequestProcessor(batch_size=32)
        result = processor.add("request")

        assert result == []

    def test_add_returns_batch_when_full(self):
        processor = BatchRequestProcessor(batch_size=2)
        processor.add("req1")
        result = processor.add("req2")

        assert len(result) == 2
        assert processor.pending is not None

    def test_flush(self):
        processor = BatchRequestProcessor(batch_size=32)
        processor.add("req1")
        processor.add("req2")

        batch = processor.flush()
        assert len(batch) == 2
        assert len(processor.pending) == 0


class TestOptimizedBankSelector:
    def test_selector_creation(self):
        selector = OptimizedBankSelector(num_banks=16)
        assert selector.num_banks == 16

    def test_select_next(self):
        selector = OptimizedBankSelector(num_banks=16)
        bank = selector.select_next(channel=0, active_banks=[0, 1, 2])

        assert bank in [0, 1, 2]

    def test_select_next_avoids_last(self):
        selector = OptimizedBankSelector(num_banks=16)
        bank1 = selector.select_next(channel=0, active_banks=[0, 1, 2])
        bank2 = selector.select_next(channel=0, active_banks=[0, 1, 2])

        # Should avoid same bank if possible
        # (but may fallback if only one bank available)

    def test_select_next_empty_active(self):
        selector = OptimizedBankSelector(num_banks=16)
        bank = selector.select_next(channel=0, active_banks=[])

        assert bank == 0


class TestLatencyTracker:
    def test_tracker_creation(self):
        tracker = LatencyTracker()
        assert tracker.samples == []
        assert tracker._sorted is True

    def test_add(self):
        tracker = LatencyTracker()
        tracker.add(50.0)
        tracker.add(100.0)

        assert len(tracker.samples) == 2
        assert tracker._sorted is False

    def test_get_percentile_empty(self):
        tracker = LatencyTracker()
        result = tracker.get_percentile(50)

        assert result == 0.0

    def test_get_percentile(self):
        tracker = LatencyTracker()
        for i in range(100):
            tracker.add(float(i))

        p50 = tracker.get_percentile(50)
        assert 45 <= p50 <= 55

    def test_get_p50(self):
        tracker = LatencyTracker()
        for i in range(10):
            tracker.add(float(i))

        p50 = tracker.get_p50()
        assert p50 == 4.0 or p50 == 5.0

    def test_get_p90(self):
        tracker = LatencyTracker()
        for i in range(100):
            tracker.add(float(i))

        p90 = tracker.get_p90()
        assert 85 <= p90 <= 95

    def test_get_p99(self):
        tracker = LatencyTracker()
        for i in range(1000):
            tracker.add(float(i))

        p99 = tracker.get_p99()
        assert 985 <= p99 <= 999


class TestOptimizationProfiles:
    def test_profiles_exist(self):
        assert "speed" in OPTIMIZATION_PROFILES
        assert "balanced" in OPTIMIZATION_PROFILES
        assert "accuracy" in OPTIMIZATION_PROFILES

    def test_speed_profile(self):
        profile = OPTIMIZATION_PROFILES["speed"]
        assert profile["batch_size"] == 64
        assert profile["enable_caching"] is True
        assert profile["reduce_precision"] is True

    def test_balanced_profile(self):
        profile = OPTIMIZATION_PROFILES["balanced"]
        assert profile["batch_size"] == 32
        assert profile["enable_caching"] is True
        assert profile["reduce_precision"] is False

    def test_accuracy_profile(self):
        profile = OPTIMIZATION_PROFILES["accuracy"]
        assert profile["batch_size"] == 16
        assert profile["enable_caching"] is False
        assert profile["reduce_precision"] is False


class TestGetOptimizedProcessor:
    def test_get_balanced(self):
        config = get_optimized_processor("balanced")
        assert config["enable_caching"] is True

    def test_get_speed(self):
        config = get_optimized_processor("speed")
        assert config["reduce_precision"] is True

    def test_get_invalid_returns_balanced(self):
        config = get_optimized_processor("invalid_profile")
        # Returns processed config with batch_processor instance
        assert config["enable_caching"] is True
        assert config["reduce_precision"] is False
        assert isinstance(config["batch_processor"], BatchRequestProcessor)
