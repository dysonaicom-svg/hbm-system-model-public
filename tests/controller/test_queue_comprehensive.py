"""
Comprehensive tests for HBM Queue Operations
Increases coverage from 55% to 95%+

Covers:
- AgeTrackingMixin
- PriorityAwareMixin
- ReadQueue
- WriteQueue
- PriorityQueue (all methods)
- HBM4QueueManager (all methods)
- QueueManager
"""

import pytest
import threading
import time
from model.controller.queue import (
    AgeTrackingMixin, PriorityAwareMixin,
    RequestQueue, ReadQueue, WriteQueue,
    PriorityQueue, HBM4QueueManager, QueueManager
)
from model.controller.request import HBMRequest


class TestAgeTrackingMixin:
    """Tests for AgeTrackingMixin"""

    def test_creation(self):
        """Test mixin creation"""
        mixin = AgeTrackingMixin()
        assert mixin._clock == 0.0
        assert mixin._age_threshold_high == 1000.0
        assert mixin._age_threshold_critical == 5000.0

    def test_tick(self):
        """Test tick advances clock"""
        mixin = AgeTrackingMixin()
        mixin.tick(100)
        assert mixin._clock == 100.0
        mixin.tick(50)
        assert mixin._clock == 150.0

    def test_set_clock(self):
        """Test set_clock"""
        mixin = AgeTrackingMixin()
        mixin.set_clock(500.0)
        assert mixin.get_clock() == 500.0

    def test_get_request_age(self):
        """Test get_request_age"""
        mixin = AgeTrackingMixin()
        mixin.set_clock(1000.0)

        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=800.0)
        age = mixin.get_request_age(request)
        assert age == 200.0

    def test_get_request_age_not_arrived(self):
        """Test age for request that hasn't arrived"""
        mixin = AgeTrackingMixin()
        mixin.set_clock(100.0)

        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=200.0)
        age = mixin.get_request_age(request)
        assert age == 0.0  # Not yet arrived

    def test_is_starving_false(self):
        """Test is_starving returns False"""
        mixin = AgeTrackingMixin()
        mixin.set_clock(1000.0)

        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=800.0)
        assert mixin.is_starving(request) is False

    def test_is_starving_true(self):
        """Test is_starving returns True"""
        mixin = AgeTrackingMixin()
        mixin.set_clock(6000.0)

        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=0.0)
        assert mixin.is_starving(request) is True

    def test_get_starvation_score(self):
        """Test starvation score calculation"""
        mixin = AgeTrackingMixin()
        mixin.set_clock(2500.0)

        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=0.0)
        score = mixin.get_starvation_score(request)
        assert 0.0 <= score <= 1.0
        assert score == 0.5  # 2500 / 5000

    def test_get_oldest_request_age(self):
        """Test get_oldest_request_age"""
        mixin = AgeTrackingMixin()
        mixin.set_clock(1000.0)

        requests = [
            HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=500.0),
            HBMRequest(addr=0x2000, length=64, is_read=True, arrival_time=700.0),
            HBMRequest(addr=0x3000, length=64, is_read=True, arrival_time=900.0),
        ]

        oldest = mixin.get_oldest_request_age(requests)
        # Oldest is the one with smallest arrival_time (500.0)
        # age = clock - arrival_time = 1000 - 500 = 500
        assert oldest == 500.0

    def test_get_oldest_request_age_empty(self):
        """Test get_oldest_request_age with empty list"""
        mixin = AgeTrackingMixin()
        oldest = mixin.get_oldest_request_age([])
        assert oldest == 0.0

    def test_set_age_thresholds(self):
        """Test set_age_thresholds"""
        mixin = AgeTrackingMixin()
        mixin.set_age_thresholds(high=2000.0, critical=10000.0)
        assert mixin._age_threshold_high == 2000.0
        assert mixin._age_threshold_critical == 10000.0


class TestPriorityAwareMixin:
    """Tests for PriorityAwareMixin"""

    def test_creation(self):
        """Test mixin creation"""
        mixin = PriorityAwareMixin(num_priority_classes=16)
        assert mixin._num_priority_classes == 16
        assert len(mixin._priority_buckets) == 16

    def test_get_priority(self):
        """Test get_priority"""
        mixin = PriorityAwareMixin()
        request = HBMRequest(addr=0x1000, length=64, is_read=True, qos=10)
        assert mixin.get_priority(request) == 10

    def test_get_priority_clamping(self):
        """Test priority clamping"""
        mixin = PriorityAwareMixin()
        request_high = HBMRequest(addr=0x1000, length=64, is_read=True, qos=100)
        request_low = HBMRequest(addr=0x1000, length=64, is_read=True, qos=-10)

        assert mixin.get_priority(request_high) == 15  # Clamped to max
        assert mixin.get_priority(request_low) == 0    # Clamped to min

    def test_get_priority_bucket(self):
        """Test get_priority_bucket"""
        mixin = PriorityAwareMixin()
        bucket = mixin.get_priority_bucket(10)
        assert bucket == []
        assert bucket is mixin._priority_buckets[10]

    def test_get_priority_bucket_clamping(self):
        """Test bucket clamping"""
        mixin = PriorityAwareMixin()
        bucket_high = mixin.get_priority_bucket(100)
        bucket_low = mixin.get_priority_bucket(-10)
        assert bucket_high is mixin._priority_buckets[15]
        assert bucket_low is mixin._priority_buckets[0]

    def test_enqueue_by_priority(self):
        """Test enqueue_by_priority"""
        mixin = PriorityAwareMixin()
        request = HBMRequest(addr=0x1000, length=64, is_read=True, qos=10)
        bucket = mixin._priority_buckets[10]
        mixin.enqueue_by_priority(request, bucket)
        # Request is added to the priority bucket
        assert request in mixin._priority_buckets[10]

    def test_find_best_by_priority_age(self):
        """Test find_best_by_priority_age"""
        mixin = PriorityAwareMixin()
        tracker = AgeTrackingMixin()
        tracker.set_clock(1000.0)

        requests = [
            HBMRequest(addr=0x1000, length=64, is_read=True, qos=10, arrival_time=800.0),
            HBMRequest(addr=0x2000, length=64, is_read=True, qos=15, arrival_time=850.0),
            HBMRequest(addr=0x3000, length=64, is_read=True, qos=5, arrival_time=900.0),
        ]

        best = mixin.find_best_by_priority_age(requests, tracker)
        assert best is not None
        assert best.qos == 15  # Highest priority

    def test_find_best_by_priority_age_empty(self):
        """Test with empty list"""
        mixin = PriorityAwareMixin()
        tracker = AgeTrackingMixin()
        best = mixin.find_best_by_priority_age([], tracker)
        assert best is None

    def test_get_queue_depth_by_priority(self):
        """Test get_queue_depth_by_priority"""
        mixin = PriorityAwareMixin()
        mixin._priority_buckets[10].append(HBMRequest(addr=0x1000, length=64, is_read=True, qos=10))
        mixin._priority_buckets[10].append(HBMRequest(addr=0x2000, length=64, is_read=True, qos=10))
        mixin._priority_buckets[5].append(HBMRequest(addr=0x3000, length=64, is_read=True, qos=5))

        depth = mixin.get_queue_depth_by_priority()
        assert depth[10] == 2
        assert depth[5] == 1
        assert depth[0] == 0

    def test_set_num_priority_classes_increase(self):
        """Test increasing priority classes"""
        mixin = PriorityAwareMixin(num_priority_classes=8)
        mixin._priority_buckets[5].append(HBMRequest(addr=0x1000, length=64, is_read=True, qos=5))

        mixin.set_num_priority_classes(16)
        assert mixin._num_priority_classes == 16
        assert len(mixin._priority_buckets) == 16

    def test_set_num_priority_classes_decrease(self):
        """Test decreasing priority classes"""
        mixin = PriorityAwareMixin(num_priority_classes=16)
        # Add requests at high priority
        mixin._priority_buckets[5].append(HBMRequest(addr=0x1000, length=64, is_read=True, qos=5))
        mixin._priority_buckets[7].append(HBMRequest(addr=0x2000, length=64, is_read=True, qos=7))

        mixin.set_num_priority_classes(8)
        assert mixin._num_priority_classes == 8
        # Requests at priority 5 and 7 should stay (since 5, 7 < 8)
        assert len(mixin._priority_buckets[5]) == 1
        assert len(mixin._priority_buckets[7]) == 1


class TestReadQueue:
    """Tests for ReadQueue"""

    def test_creation(self):
        """Test ReadQueue creation"""
        queue = ReadQueue(max_depth=64)
        assert queue.max_depth == 64
        assert queue.name == "ReadQueue"
        assert queue.is_empty()

    def test_get_row_hit_requests(self):
        """Test get_row_hit_requests"""
        queue = ReadQueue()

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True, row_hit=True))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True, row_hit=False))
        queue.push(HBMRequest(addr=0x3000, length=64, is_read=True, row_hit=True))

        hits = queue.get_row_hit_requests()
        assert len(hits) == 2

    def test_get_oldest_request(self):
        """Test get_oldest_request"""
        queue = ReadQueue()

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        req1.arrival_time = 100.0

        req2 = HBMRequest(addr=0x2000, length=64, is_read=True)
        req2.arrival_time = 50.0

        queue.push(req1)
        queue.push(req2)

        oldest = queue.get_oldest_request()
        assert oldest.arrival_time == 50.0

    def test_get_oldest_request_empty(self):
        """Test get_oldest_request with empty queue"""
        queue = ReadQueue()
        oldest = queue.get_oldest_request()
        assert oldest is None

    def test_get_best_request_row_hit(self):
        """Test get_best_request prefers row hit"""
        queue = ReadQueue()

        req_old = HBMRequest(addr=0x1000, length=64, is_read=True, row_hit=False)
        req_old.arrival_time = 0.0

        req_new = HBMRequest(addr=0x2000, length=64, is_read=True, row_hit=True)
        req_new.arrival_time = 100.0

        queue.push(req_old)
        queue.push(req_new)

        best = queue.get_best_request()
        assert best.row_hit is True

    def test_get_best_request_fallback_to_oldest(self):
        """Test get_best_request falls back to oldest"""
        queue = ReadQueue()

        req_old = HBMRequest(addr=0x1000, length=64, is_read=True, row_hit=False)
        req_old.arrival_time = 0.0

        req_new = HBMRequest(addr=0x2000, length=64, is_read=True, row_hit=False)
        req_new.arrival_time = 100.0

        queue.push(req_new)
        queue.push(req_old)

        best = queue.get_best_request()
        assert best.arrival_time == 0.0


class TestWriteQueue:
    """Tests for WriteQueue"""

    def test_creation(self):
        """Test WriteQueue creation"""
        queue = WriteQueue(max_depth=64, drain_threshold=0.8)
        assert queue.max_depth == 64
        assert queue.drain_threshold == 0.8
        assert queue.name == "WriteQueue"

    def test_should_drain_below_threshold(self):
        """Test should_drain below threshold"""
        queue = WriteQueue(max_depth=64, drain_threshold=0.8)
        assert queue.should_drain() is False

    def test_should_drain_above_threshold(self):
        """Test should_drain above threshold"""
        queue = WriteQueue(max_depth=10, drain_threshold=0.8)

        for i in range(9):
            queue.push(HBMRequest(addr=0x1000 + i, length=64, is_read=False))

        assert queue.should_drain() is True

    def test_get_oldest_request(self):
        """Test get_oldest_request"""
        queue = WriteQueue()

        req1 = HBMRequest(addr=0x1000, length=64, is_read=False)
        req1.arrival_time = 100.0

        req2 = HBMRequest(addr=0x2000, length=64, is_read=False)
        req2.arrival_time = 50.0

        queue.push(req1)
        queue.push(req2)

        oldest = queue.get_oldest_request()
        assert oldest.arrival_time == 50.0

    def test_get_pending_bytes(self):
        """Test get_pending_bytes"""
        queue = WriteQueue()

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=False))
        queue.push(HBMRequest(addr=0x2000, length=128, is_read=False))
        queue.push(HBMRequest(addr=0x3000, length=32, is_read=False))

        total = queue.get_pending_bytes()
        assert total == 224  # 64 + 128 + 32


class TestPriorityQueue:
    """Comprehensive tests for PriorityQueue"""

    def test_creation(self):
        """Test PriorityQueue creation"""
        queue = PriorityQueue(max_depth=64, num_priority_classes=16)
        assert queue.max_depth == 64
        assert queue._num_priority_classes == 16
        assert queue._priority_boost_enabled is True
        assert queue._priority_boost_factor == 2.0

    def test_push_sets_arrival_time(self):
        """Test that push sets arrival_time if not set"""
        queue = PriorityQueue()
        queue.set_clock(100.0)

        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        request.arrival_time = -1  # Invalid

        queue.push(request)
        assert request.arrival_time == 100.0

    def test_push_preserves_arrival_time(self):
        """Test that push preserves existing arrival_time"""
        queue = PriorityQueue()
        queue.set_clock(100.0)

        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=50.0)

        queue.push(request)
        assert request.arrival_time == 50.0

    def test_get_best_request(self):
        """Test get_best_request"""
        queue = PriorityQueue()
        queue.set_clock(1000.0)

        # Add starving high priority request
        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, qos=15, arrival_time=0.0)
        # Add non-starving lower priority
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, qos=8, arrival_time=900.0)

        queue.push(req1)
        queue.push(req2)

        best = queue.get_best_request()
        assert best.qos == 15

    def test_get_best_request_all_starving(self):
        """Test when all requests are starving"""
        queue = PriorityQueue()
        queue.set_clock(10000.0)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, qos=15, arrival_time=0.0)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, qos=8, arrival_time=100.0)

        queue.push(req1)
        queue.push(req2)

        best = queue.get_best_request()
        # Should pick oldest
        assert best.arrival_time == 0.0

    def test_get_best_request_empty(self):
        """Test get_best_request with empty queue"""
        queue = PriorityQueue()
        best = queue.get_best_request()
        assert best is None

    def test_get_requests_by_priority(self):
        """Test get_requests_by_priority"""
        queue = PriorityQueue()

        for qos in [5, 10, 10, 15]:
            queue.push(HBMRequest(addr=0x1000 + qos, length=64, is_read=True, qos=qos))

        reqs_10 = queue.get_requests_by_priority(10)
        assert len(reqs_10) == 2

    def test_get_priority_distribution(self):
        """Test get_priority_distribution"""
        queue = PriorityQueue()

        for qos in [5, 10, 10, 15, 15, 15]:
            queue.push(HBMRequest(addr=0x1000 + qos, length=64, is_read=True, qos=qos))

        dist = queue.get_priority_distribution()
        assert dist[5] == 1
        assert dist[10] == 2
        assert dist[15] == 3

    def test_get_avg_wait_time(self):
        """Test get_avg_wait_time"""
        queue = PriorityQueue()
        queue.set_clock(1000.0)

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=800.0))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True, arrival_time=900.0))

        avg = queue.get_avg_wait_time()
        assert avg == 150.0  # (200 + 100) / 2

    def test_get_avg_wait_time_empty(self):
        """Test avg wait time with empty queue"""
        queue = PriorityQueue()
        avg = queue.get_avg_wait_time()
        assert avg == 0.0

    def test_get_max_wait_time(self):
        """Test get_max_wait_time"""
        queue = PriorityQueue()
        queue.set_clock(1000.0)

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=800.0))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True, arrival_time=950.0))

        max_wait = queue.get_max_wait_time()
        # Oldest request is at 800.0, clock is 1000.0
        # max_wait = 1000 - 800 = 200
        assert max_wait == 200.0

    def test_get_max_wait_time_empty(self):
        """Test max wait time with empty queue"""
        queue = PriorityQueue()
        max_wait = queue.get_max_wait_time()
        assert max_wait == 0.0

    def test_get_starving_requests(self):
        """Test get_starving_requests"""
        queue = PriorityQueue()
        queue.set_clock(10000.0)

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=0.0))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True, arrival_time=9000.0))

        starving = queue.get_starving_requests()
        assert len(starving) == 1
        assert starving[0].arrival_time == 0.0

    def test_enable_priority_boost(self):
        """Test enable_priority_boost"""
        queue = PriorityQueue()
        assert queue._priority_boost_enabled is True

        queue.enable_priority_boost(False)
        assert queue._priority_boost_enabled is False

        queue.enable_priority_boost(True)
        assert queue._priority_boost_enabled is True

    def test_set_priority_boost_factor(self):
        """Test set_priority_boost_factor"""
        queue = PriorityQueue()
        queue.set_priority_boost_factor(3.0)
        assert queue._priority_boost_factor == 3.0

        # Test clamping to minimum 1.0
        queue.set_priority_boost_factor(0.5)
        assert queue._priority_boost_factor == 1.0

    def test_get_detailed_stats(self):
        """Test get_detailed_stats"""
        queue = PriorityQueue()
        queue.set_clock(1000.0)

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True, qos=10, arrival_time=800.0))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True, qos=5, arrival_time=900.0))

        stats = queue.get_detailed_stats()

        assert 'current_occupancy' in stats
        assert 'occupancy_rate' in stats
        assert 'avg_wait_time' in stats
        assert 'max_wait_time' in stats
        assert 'priority_distribution' in stats
        assert stats['current_occupancy'] == 2


class TestHBM4QueueManager:
    """Tests for HBM4QueueManager"""

    def test_creation(self):
        """Test HBM4QueueManager creation"""
        manager = HBM4QueueManager(
            queue_depth=64,
            num_priority_classes=16,
            per_channel_queues=False,
            num_channels=32
        )

        assert manager.read_queue is not None
        assert manager.write_queue is not None
        assert manager.num_channels == 32
        assert manager.per_channel_queues is False

    def test_creation_with_per_channel_queues(self):
        """Test creation with per-channel queues"""
        manager = HBM4QueueManager(
            queue_depth=64,
            per_channel_queues=True,
            num_channels=32
        )

        assert manager.channel_queues is not None
        assert len(manager.channel_queues) == 32
        assert 0 in manager.channel_queues

    def test_tick(self):
        """Test tick"""
        manager = HBM4QueueManager()
        manager._global_clock = 0.0

        manager.tick(100)
        assert manager._global_clock == 100.0

    def test_push_read(self):
        """Test push_read"""
        manager = HBM4QueueManager()
        manager._global_clock = 100.0

        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        result = manager.push_read(request)

        assert result is True
        assert manager.read_queue.size() == 1

    def test_push_read_per_channel(self):
        """Test push_read to specific channel"""
        manager = HBM4QueueManager(per_channel_queues=True, num_channels=32)
        manager._global_clock = 100.0

        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        result = manager.push_read(request, channel_id=5)

        assert result is True
        # Check per-channel queue
        rq, _ = manager.channel_queues[5]
        assert rq.size() == 1

    def test_push_write(self):
        """Test push_write"""
        manager = HBM4QueueManager()
        manager._global_clock = 100.0

        request = HBMRequest(addr=0x1000, length=64, is_read=False)
        result = manager.push_write(request)

        assert result is True
        assert manager.write_queue.size() == 1

    def test_pop_read(self):
        """Test pop_read"""
        manager = HBM4QueueManager()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        manager.push_read(request)

        popped = manager.pop_read()
        assert popped is not None
        assert popped.addr == 0x1000

    def test_pop_write(self):
        """Test pop_write"""
        manager = HBM4QueueManager()
        request = HBMRequest(addr=0x1000, length=64, is_read=False)
        manager.push_write(request)

        popped = manager.pop_write()
        assert popped is not None
        assert popped.addr == 0x1000

    def test_get_best_read(self):
        """Test get_best_read"""
        manager = HBM4QueueManager()

        # Need to set clock through tick mechanism
        manager._global_clock = 1000.0

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, qos=5)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, qos=15)
        manager.push_read(req1)
        manager.push_read(req2)

        best = manager.get_best_read()
        assert best.qos == 15

    def test_get_best_write(self):
        """Test get_best_write"""
        manager = HBM4QueueManager()

        # Need to set clock through tick mechanism
        manager._global_clock = 1000.0

        req1 = HBMRequest(addr=0x1000, length=64, is_read=False, qos=5)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=False, qos=15)
        manager.push_write(req1)
        manager.push_write(req2)

        best = manager.get_best_write()
        assert best.qos == 15

    def test_total_size(self):
        """Test total_size"""
        manager = HBM4QueueManager()

        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_read(HBMRequest(addr=0x2000, length=64, is_read=True))
        manager.push_write(HBMRequest(addr=0x3000, length=64, is_read=False))

        assert manager.total_size() == 3

    def test_total_size_with_per_channel(self):
        """Test total_size with per-channel queues"""
        manager = HBM4QueueManager(per_channel_queues=True, num_channels=2)

        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_read(HBMRequest(addr=0x2000, length=64, is_read=True), channel_id=0)
        manager.push_read(HBMRequest(addr=0x3000, length=64, is_read=True), channel_id=1)

        # Should count main queue + per-channel queues
        total = manager.total_size()
        assert total >= 3

    def test_is_full(self):
        """Test is_full"""
        manager = HBM4QueueManager(queue_depth=2)

        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_read(HBMRequest(addr=0x2000, length=64, is_read=True))

        assert manager.is_full() is True

    def test_is_full_with_space(self):
        """Test is_full with available space"""
        manager = HBM4QueueManager(queue_depth=64)
        assert manager.is_full() is False

    def test_get_stats(self):
        """Test get_stats"""
        manager = HBM4QueueManager()

        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_write(HBMRequest(addr=0x2000, length=64, is_read=False))

        stats = manager.get_stats()

        assert 'read' in stats
        assert 'write' in stats
        assert 'total' in stats
        assert stats['total']['size'] == 2


class TestQueueManager:
    """Tests for QueueManager"""

    def test_creation(self):
        """Test QueueManager creation"""
        manager = QueueManager.create(queue_depth=32)
        assert manager.read_queue is not None
        assert manager.write_queue is not None

    def test_push_read(self):
        """Test push_read"""
        manager = QueueManager.create()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        result = manager.push_read(request)
        assert result is True

    def test_push_write(self):
        """Test push_write"""
        manager = QueueManager.create()
        request = HBMRequest(addr=0x1000, length=64, is_read=False)
        result = manager.push_write(request)
        assert result is True

    def test_remove_read(self):
        """Test remove_read"""
        manager = QueueManager.create()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        manager.push_read(request)

        result = manager.remove_read(request.request_id)
        assert result is True

    def test_remove_write(self):
        """Test remove_write"""
        manager = QueueManager.create()
        request = HBMRequest(addr=0x1000, length=64, is_read=False)
        manager.push_write(request)

        result = manager.remove_write(request.request_id)
        assert result is True

    def test_total_size(self):
        """Test total_size"""
        manager = QueueManager.create()
        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_write(HBMRequest(addr=0x2000, length=64, is_read=False))

        assert manager.total_size() == 2

    def test_is_full(self):
        """Test is_full"""
        manager = QueueManager.create(queue_depth=2)
        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_read(HBMRequest(addr=0x2000, length=64, is_read=True))

        assert manager.is_full() is True

    def test_get_stats(self):
        """Test get_stats"""
        manager = QueueManager.create()
        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_write(HBMRequest(addr=0x2000, length=64, is_read=False))

        stats = manager.get_stats()
        assert 'read' in stats
        assert 'write' in stats
        assert stats['total']['size'] == 2


class TestPriorityQueueIntegration:
    """Integration tests for PriorityQueue"""

    def test_priority_ordering(self):
        """Test that priority ordering is maintained"""
        queue = PriorityQueue()
        queue.set_clock(1000.0)

        # Push in random order
        for qos in [5, 15, 8, 12, 0]:
            queue.push(HBMRequest(addr=0x1000 + qos, length=64, is_read=True, qos=qos))

        # Pop should return highest priority first
        best = queue.get_best_request()
        assert best.qos == 15

    def test_same_priority_fifo(self):
        """Test FIFO within same priority"""
        queue = PriorityQueue()
        queue.set_clock(1000.0)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, qos=10, arrival_time=100.0)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, qos=10, arrival_time=200.0)

        queue.push(req2)
        queue.push(req1)

        # Both have same priority, should pick oldest
        best = queue.get_best_request()
        assert best.arrival_time == 100.0

    def test_full_queue_rejection(self):
        """Test queue rejection when full"""
        queue = PriorityQueue(max_depth=2)

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True))

        # Queue is full, should reject
        result = queue.push(HBMRequest(addr=0x3000, length=64, is_read=True))
        assert result is False

    def test_priority_bucket_maintenance(self):
        """Test that priority buckets are maintained correctly"""
        queue = PriorityQueue(num_priority_classes=8)

        for qos in range(8):
            for _ in range(2):
                queue.push(HBMRequest(addr=0x1000 + qos, length=64, is_read=True, qos=qos))

        # Check that all queues have correct count
        for qos in range(8):
            requests = queue.get_requests_by_priority(qos)
            assert len(requests) == 2
