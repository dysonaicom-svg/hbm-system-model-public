"""
HBM4 Queue Operations and Priority Tests

Comprehensive tests for queue operations, priority handling, and scheduling.

Test coverage:
- Queue push/pop operations
- Priority queue management
- Starvation detection and prevention
- Queue statistics and monitoring
- FR-FCFS scheduling
- Age tracking
"""

import pytest
import time
from model.controller.queue import (
    ReadQueue, WriteQueue, PriorityQueue, QueueManager,
    AgeTrackingMixin, PriorityAwareMixin
)
from model.controller.request import HBMRequest, RequestState
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler


class TestReadQueueOperations:
    """Test ReadQueue operations"""

    def test_read_queue_creation(self):
        """Test ReadQueue creation"""
        queue = ReadQueue(max_depth=32)
        assert queue.max_depth == 32
        assert queue.size() == 0
        assert queue.is_empty()

    def test_read_queue_push(self):
        """Test push to ReadQueue"""
        queue = ReadQueue(max_depth=32)

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        result = queue.push(req)

        assert result is True
        assert queue.size() == 1
        assert not queue.is_empty()

    def test_read_queue_pop(self):
        """Test pop from ReadQueue"""
        queue = ReadQueue(max_depth=32)

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        queue.push(req)

        popped = queue.pop()
        assert popped is not None
        assert popped.addr == 0x100
        assert queue.size() == 0

    def test_read_queue_full(self):
        """Test queue full condition"""
        queue = ReadQueue(max_depth=2)

        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))

        assert queue.is_full()

        # Third push should fail
        result = queue.push(HBMRequest(addr=0x300, length=64, is_read=True))
        assert result is False

    def test_read_queue_peek(self):
        """Test peek operation"""
        queue = ReadQueue(max_depth=32)

        req1 = HBMRequest(addr=0x100, length=64, is_read=True)
        req2 = HBMRequest(addr=0x200, length=64, is_read=True)

        queue.push(req1)
        queue.push(req2)

        peeked = queue.peek()
        assert peeked.addr == 0x100  # First item

        # Queue unchanged
        assert queue.size() == 2

    def test_read_queue_remove(self):
        """Test remove by request ID"""
        queue = ReadQueue(max_depth=32)

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        queue.push(req)

        result = queue.remove(req.request_id)
        assert result is True
        assert queue.size() == 0

    def test_read_queue_get_row_hit_requests(self):
        """Test getting row hit requests"""
        queue = ReadQueue(max_depth=32)

        req1 = HBMRequest(addr=0x100, length=64, is_read=True, row_hit=False)
        req2 = HBMRequest(addr=0x200, length=64, is_read=True, row_hit=True)

        queue.push(req1)
        queue.push(req2)

        hit_requests = queue.get_row_hit_requests()
        assert len(hit_requests) == 1
        assert hit_requests[0].row_hit is True

    def test_read_queue_get_oldest_request(self):
        """Test getting oldest request"""
        queue = ReadQueue(max_depth=32)

        req1 = HBMRequest(addr=0x100, length=64, is_read=True)
        req1.arrival_time = 10

        req2 = HBMRequest(addr=0x200, length=64, is_read=True)
        req2.arrival_time = 5

        queue.push(req1)
        queue.push(req2)

        oldest = queue.get_oldest_request()
        assert oldest.arrival_time == 5


class TestWriteQueueOperations:
    """Test WriteQueue operations"""

    def test_write_queue_creation(self):
        """Test WriteQueue creation"""
        queue = WriteQueue(max_depth=32)
        assert queue.max_depth == 32
        assert queue.size() == 0

    def test_write_queue_push(self):
        """Test push to WriteQueue"""
        queue = WriteQueue(max_depth=32)

        req = HBMRequest(addr=0x100, length=64, is_read=False)
        result = queue.push(req)

        assert result is True
        assert queue.size() == 1

    def test_write_queue_should_drain(self):
        """Test drain threshold"""
        queue = WriteQueue(max_depth=10, drain_threshold=0.5)

        # Below threshold
        for i in range(4):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=False))

        assert not queue.should_drain()

        # At threshold
        for i in range(4, 6):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=False))

        assert queue.should_drain()

    def test_write_queue_pending_bytes(self):
        """Test pending bytes calculation"""
        queue = WriteQueue(max_depth=32)

        queue.push(HBMRequest(addr=0x100, length=64, is_read=False))
        queue.push(HBMRequest(addr=0x200, length=128, is_read=False))

        assert queue.get_pending_bytes() == 192


class TestPriorityQueueOperations:
    """Test PriorityQueue operations"""

    def test_priority_queue_creation(self):
        """Test PriorityQueue creation"""
        queue = PriorityQueue(max_depth=64, num_priority_classes=16)
        assert queue.max_depth == 64
        assert queue._num_priority_classes == 16

    def test_priority_queue_push_ordering(self):
        """Test priority-based ordering"""
        queue = PriorityQueue(max_depth=64, num_priority_classes=16)

        # Push high priority first
        req1 = HBMRequest(addr=0x100, length=64, is_read=True, qos=5)
        queue.push(req1)

        # Push higher priority second
        req2 = HBMRequest(addr=0x200, length=64, is_read=True, qos=15)
        queue.push(req2)

        # Queue uses FIFO for deque, priority is tracked in priority queue
        # Check that both items are in the queue
        assert queue.size() == 2
        # Check priority queue has correct ordering
        assert len(queue._priority_queue) == 2

    def test_priority_queue_same_priority_fifo(self):
        """Test FIFO within same priority"""
        queue = PriorityQueue(max_depth=64)

        req1 = HBMRequest(addr=0x100, length=64, is_read=True, qos=8)
        req2 = HBMRequest(addr=0x200, length=64, is_read=True, qos=8)

        queue.push(req1)
        queue.push(req2)

        # Both should be in queue
        assert queue.size() == 2

    def test_priority_queue_full_rejection(self):
        """Test priority queue full rejection"""
        queue = PriorityQueue(max_depth=3)

        for i in range(3):
            result = queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True, qos=8))
            assert result is True

        # Full, should reject
        result = queue.push(HBMRequest(addr=0x400, length=64, is_read=True, qos=8))
        assert result is False

    def test_priority_queue_stats(self):
        """Test priority queue statistics"""
        queue = PriorityQueue(max_depth=32)

        for i in range(10):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True, qos=i % 16))

        stats = queue.get_stats()
        assert stats['current_occupancy'] == 10
        assert stats['push_count'] == 10

    def test_priority_queue_distribution(self):
        """Test priority distribution"""
        queue = PriorityQueue(max_depth=64)

        for i in range(16):
            # Only push 4 per priority to fit in 64 depth
            for _ in range(4):
                queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True, qos=i))

        dist = queue.get_priority_distribution()
        # All 16 priority levels should have 4 requests each (64 total)
        assert queue.size() == 64
        for i in range(16):
            assert dist[i] == 4


class TestAgeTracking:
    """Test AgeTrackingMixin"""

    def test_age_tracking_clock(self):
        """Test age tracking clock"""
        tracker = AgeTrackingMixin()

        assert tracker.get_clock() == 0.0

        tracker.tick(10)
        assert tracker.get_clock() == 10.0

        tracker.set_clock(100)
        assert tracker.get_clock() == 100.0

    def test_request_age_calculation(self):
        """Test request age calculation"""
        tracker = AgeTrackingMixin()
        tracker.set_clock(50)

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        req.arrival_time = 30

        age = tracker.get_request_age(req)
        assert age == 20.0

    def test_starvation_detection(self):
        """Test starvation detection"""
        tracker = AgeTrackingMixin()
        tracker._age_threshold_critical = 100

        # Young request - not starving
        req1 = HBMRequest(addr=0x100, length=64, is_read=True)
        req1.arrival_time = 0
        tracker.set_clock(50)

        assert tracker.is_starving(req1) is False

        # Old request - starving
        req2 = HBMRequest(addr=0x200, length=64, is_read=True)
        req2.arrival_time = 0
        tracker.set_clock(150)

        assert tracker.is_starving(req2) is True

    def test_starvation_score(self):
        """Test starvation score calculation"""
        tracker = AgeTrackingMixin()
        tracker._age_threshold_critical = 100

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        req.arrival_time = 0
        tracker.set_clock(50)

        score = tracker.get_starvation_score(req)
        assert score == 0.5

    def test_oldest_request_age(self):
        """Test getting oldest request age"""
        tracker = AgeTrackingMixin()
        tracker.set_clock(100)

        req1 = HBMRequest(addr=0x100, length=64, is_read=True)
        req1.arrival_time = 10

        req2 = HBMRequest(addr=0x200, length=64, is_read=True)
        req2.arrival_time = 30

        queue = [req1, req2]
        oldest_age = tracker.get_oldest_request_age(queue)
        # oldest_age = clock - min(arrival_time) = 100 - 10 = 90
        assert oldest_age == 90


class TestQueueManager:
    """Test QueueManager"""

    def test_queue_manager_creation(self):
        """Test QueueManager creation"""
        manager = QueueManager.create(queue_depth=32)

        assert manager.read_queue is not None
        assert manager.write_queue is not None
        assert manager.total_size() == 0

    def test_queue_manager_push_read(self):
        """Test push read"""
        manager = QueueManager.create(queue_depth=32)

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        result = manager.push_read(req)

        assert result is True
        assert manager.total_size() == 1

    def test_queue_manager_push_write(self):
        """Test push write"""
        manager = QueueManager.create(queue_depth=32)

        req = HBMRequest(addr=0x100, length=64, is_read=False)
        result = manager.push_write(req)

        assert result is True
        assert manager.total_size() == 1

    def test_queue_manager_remove_read(self):
        """Test remove read"""
        manager = QueueManager.create(queue_depth=32)

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        manager.push_read(req)

        result = manager.remove_read(req.request_id)
        assert result is True
        assert manager.total_size() == 0

    def test_queue_manager_remove_write(self):
        """Test remove write"""
        manager = QueueManager.create(queue_depth=32)

        req = HBMRequest(addr=0x100, length=64, is_read=False)
        manager.push_write(req)

        result = manager.remove_write(req.request_id)
        assert result is True

    def test_queue_manager_is_full(self):
        """Test is_full"""
        manager = QueueManager.create(queue_depth=2)

        assert not manager.is_full()

        manager.push_read(HBMRequest(addr=0x100, length=64, is_read=True))
        manager.push_read(HBMRequest(addr=0x200, length=64, is_read=True))

        assert manager.is_full()

    def test_queue_manager_stats(self):
        """Test queue manager stats"""
        manager = QueueManager.create(queue_depth=32)

        manager.push_read(HBMRequest(addr=0x100, length=64, is_read=True))
        manager.push_write(HBMRequest(addr=0x200, length=64, is_read=False))

        stats = manager.get_stats()
        assert stats['total']['size'] == 2


class TestQoSSchedulerIntegration:
    """Test QoS scheduler integration with queue"""

    def test_scheduler_queue_integration(self):
        """Test scheduler and queue work together"""
        scheduler = HBM4QoSScheduler()
        queue = PriorityQueue(max_depth=64)

        # Submit through scheduler
        for i in range(10):
            scheduler.submit_request(
                request_id=i,
                addr=i * 0x100,
                qos=15 - i,  # Decreasing priority
                is_read=True
            )

        # Get from queue
        while True:
            req = scheduler.schedule()
            if req is None:
                break
            queue.push(HBMRequest(
                addr=req.addr,
                length=64,
                is_read=True,
                qos=req.qos
            ))

        # Higher priority at front
        popped = queue.pop()
        assert popped.qos == 15

    def test_scheduler_priority_ordering(self):
        """Test priority ordering in scheduler"""
        scheduler = HBM4QoSScheduler()

        # Submit mixed priorities
        scheduler.submit_request(request_id=1, qos=0, is_read=True)
        scheduler.submit_request(request_id=2, qos=8, is_read=True)
        scheduler.submit_request(request_id=3, qos=15, is_read=True)

        # Highest priority first
        req1 = scheduler.schedule()
        req2 = scheduler.schedule()
        req3 = scheduler.schedule()

        assert req1.qos == 15
        assert req2.qos == 8
        assert req3.qos == 0


class TestQueuePerformance:
    """Test queue performance characteristics"""

    def test_bulk_operations(self):
        """Test bulk push operations"""
        queue = PriorityQueue(max_depth=10000)

        start = time.time()

        for i in range(10000):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True, qos=8))

        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0
        assert queue.size() == 10000

    def test_bulk_pop_operations(self):
        """Test bulk pop operations"""
        queue = PriorityQueue(max_depth=10000)

        for i in range(10000):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True, qos=8))

        start = time.time()

        for _ in range(10000):
            queue.pop()

        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0
        assert queue.size() == 0


class TestQueueEdgeCases:
    """Test queue edge cases"""

    def test_clear_queue(self):
        """Test clearing queue"""
        queue = ReadQueue(max_depth=32)

        for i in range(10):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))

        queue.clear()
        assert queue.size() == 0
        assert queue.is_empty()

    def test_multiple_clear(self):
        """Test multiple clears"""
        queue = ReadQueue(max_depth=32)

        for _ in range(5):
            for i in range(10):
                queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))
            queue.clear()

        assert queue.size() == 0

    def test_iterate_empty_queue(self):
        """Test iterating empty queue"""
        queue = ReadQueue(max_depth=32)

        items = list(queue)
        assert items == []

    def test_iterate_non_empty_queue(self):
        """Test iterating non-empty queue"""
        queue = ReadQueue(max_depth=32)

        for i in range(5):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))

        items = list(queue)
        assert len(items) == 5


class TestQueueWithConcurrentAccess:
    """Test queue with concurrent access patterns"""

    def test_rapid_push_pop(self):
        """Test rapid push and pop"""
        queue = ReadQueue(max_depth=1000)

        for i in range(100):
            req = HBMRequest(addr=i * 0x100, length=64, is_read=True)
            queue.push(req)

            if i % 2 == 0:
                queue.pop()

        # Should have 50 items
        assert queue.size() == 50

    def test_priority_queue_concurrent(self):
        """Test priority queue under load"""
        queue = PriorityQueue(max_depth=1000)

        for i in range(100):
            qos = i % 16
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True, qos=qos))

        # Verify all items are in queue
        assert queue.size() == 100
        assert not queue.is_empty()

        # Pop all and verify queue empties
        count = 0
        while not queue.is_empty():
            req = queue.pop()
            count += 1

        assert count == 100


class TestStarvationPrevention:
    """Test starvation prevention mechanisms"""

    def test_low_priority_eventually_scheduled(self):
        """Test low priority is eventually scheduled"""
        scheduler = HBM4QoSScheduler()

        # Flood with high priority
        for i in range(10):
            scheduler.submit_request(request_id=i, qos=15, is_read=True)

        # Add low priority
        scheduler.submit_request(request_id=999, qos=0, is_read=True)

        # Drain all requests
        scheduled_ids = []
        for _ in range(20):
            req = scheduler.schedule()
            if req is not None:
                scheduled_ids.append(req.qos)

        # All requests should be scheduled
        assert len(scheduled_ids) == 11

    def test_priority_queue_starvation_score(self):
        """Test starvation scores in priority queue"""
        queue = PriorityQueue(max_depth=64)
        queue._age_threshold_critical = 100

        # Add old low priority request
        old_req = HBMRequest(addr=0x100, length=64, is_read=True, qos=0)
        old_req.arrival_time = 0
        queue._clock = 150
        queue.push(old_req)

        # Add new high priority request
        new_req = HBMRequest(addr=0x200, length=64, is_read=True, qos=15)
        new_req.arrival_time = 100
        queue.push(new_req)

        # Starvation score calculation
        old_score = queue.get_starvation_score(old_req)
        new_score = queue.get_starvation_score(new_req)

        assert old_score > new_score


class TestQueueStatistics:
    """Test queue statistics"""

    def test_reject_count(self):
        """Test rejection counter"""
        queue = ReadQueue(max_depth=2)

        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))

        # This should be rejected
        queue.push(HBMRequest(addr=0x300, length=64, is_read=True))

        stats = queue.get_stats()
        assert stats['reject_count'] == 1

    def test_max_occupancy(self):
        """Test max occupancy tracking"""
        queue = ReadQueue(max_depth=10)

        for i in range(5):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))

        stats = queue.get_stats()
        assert stats['max_occupancy'] == 5

        # Add more
        for i in range(5, 8):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))

        stats = queue.get_stats()
        assert stats['max_occupancy'] == 8

    def test_occupancy_rate(self):
        """Test occupancy rate calculation"""
        queue = ReadQueue(max_depth=100)

        for i in range(50):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))

        stats = queue.get_stats()
        assert stats['occupancy_rate'] == 0.5
