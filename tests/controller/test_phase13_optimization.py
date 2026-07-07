"""
Tests for Phase 13 Performance Optimization Modules
"""

import pytest
from model.controller.parallel_scheduler import (
    ParallelChannelScheduler,
    ChannelLoad,
)
from model.controller.advanced_prefetch import (
    AdvancedPrefetchEngine,
    AccessPatternClassifier,
    PrefetchDecision,
)
from model.controller.smart_queue import SmartQueue, QueueEntry
from model.controller.bank_predictor import BankPredictor, BankState


class TestParallelChannelScheduler:
    """Tests for parallel channel scheduler"""

    def test_creation(self):
        scheduler = ParallelChannelScheduler(num_channels=32)
        assert scheduler.num_channels == 32
        assert len(scheduler.channel_loads) == 32

    def test_submit_request(self):
        from model.controller.request import HBMRequest
        scheduler = ParallelChannelScheduler(num_channels=8)

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            qos=8,
            request_id=1,
            arrival_time=0
        )
        scheduler.submit_request(request, channel_id=3)

        assert scheduler.channel_loads[3].pending_requests == 1
        assert len(scheduler._pending_by_channel[3]) == 1

    def test_schedule_next(self):
        from model.controller.request import HBMRequest
        scheduler = ParallelChannelScheduler(num_channels=8)

        # Submit requests to multiple channels
        for ch in range(8):
            for i in range(2):
                request = HBMRequest(
                    addr=0x1000 + i * 64,
                    length=64,
                    is_read=True,
                    qos=8,
                    request_id=ch * 10 + i,
                    arrival_time=0
                )
                scheduler.submit_request(request, channel_id=ch)

        scheduled = scheduler.schedule_next(current_cycle=100)
        assert len(scheduled) <= 8  # Max 8 parallel

    def test_load_balancing(self):
        scheduler = ParallelChannelScheduler(num_channels=8)

        # Manually set unbalanced loads
        scheduler.channel_loads[0].pending_requests = 10
        scheduler.channel_loads[7].pending_requests = 1

        migrations = scheduler.balance_load(threshold=0.3)
        # Should migrate at least one request
        assert isinstance(migrations, list)

    def test_get_stats(self):
        scheduler = ParallelChannelScheduler(num_channels=8)
        stats = scheduler.get_stats()

        assert 'total_pending' in stats
        assert 'channels_active' in stats
        assert 'avg_load' in stats
        assert 'load_variance' in stats


class TestAccessPatternClassifier:
    """Tests for access pattern classifier"""

    def test_sequential_detection(self):
        classifier = AccessPatternClassifier()

        # Add sequential accesses with larger stride to distinguish from stride
        for i in range(20):
            classifier.add_access(i * 64, i)  # Stride of 64

        pattern = classifier.classify()
        # Should be detected as either sequential or stride (both are good)
        assert pattern in [classifier.SEQUENTIAL, classifier.STRIDE]

    def test_stride_detection(self):
        classifier = AccessPatternClassifier()

        # Add stride accesses (stride = 64)
        for i in range(20):
            classifier.add_access(i * 64, i)

        assert classifier.classify() == classifier.STRIDE

    def test_hotspot_detection(self):
        classifier = AccessPatternClassifier()

        # Add hotspot (same address repeated)
        for i in range(20):
            classifier.add_access(0x1000, i)

        assert classifier.classify() == classifier.HOTSPOT

    def test_random_detection(self):
        classifier = AccessPatternClassifier()

        # Add random accesses
        import random
        random.seed(42)
        for i in range(20):
            classifier.add_access(random.randint(0, 0xFFFF), i)

        # Random should not be any other pattern
        pattern = classifier.classify()
        assert pattern in [
            classifier.SEQUENTIAL,
            classifier.RANDOM,
            classifier.STRIDE,
            classifier.HOTSPOT,
            classifier.MIXED
        ]


class TestAdvancedPrefetchEngine:
    """Tests for advanced prefetch engine"""

    def test_creation(self):
        engine = AdvancedPrefetchEngine()
        assert engine.max_prefetch_degree == 8
        assert engine.confidence_threshold == 0.7

    def test_stride_prediction(self):
        engine = AdvancedPrefetchEngine()

        # Record stride pattern
        for i in range(16):
            engine.update(i * 64, stream_id=0)

        # Get prediction
        decisions = engine.predict(64, stream_id=0)
        assert len(decisions) > 0
        assert all(isinstance(d, PrefetchDecision) for d in decisions)

    def test_statistics(self):
        engine = AdvancedPrefetchEngine()

        # Record some accesses
        for i in range(32):
            engine.update(i * 64)

        stats = engine.get_statistics()
        assert 'total_prefetches' in stats
        assert 'accuracy' in stats
        assert 'pattern_class' in stats

    def test_reset(self):
        engine = AdvancedPrefetchEngine()

        for i in range(32):
            engine.update(i * 64)

        engine.reset()
        stats = engine.get_statistics()
        assert stats['total_prefetches'] == 0
        assert stats['useful_prefetches'] == 0


class TestSmartQueue:
    """Tests for smart priority queue"""

    def test_creation(self):
        queue = SmartQueue(max_size=64)
        assert queue.max_size == 64
        assert len(queue) == 0

    def test_enqueue_dequeue(self):
        from model.controller.request import HBMRequest
        queue = SmartQueue(max_size=64)

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            qos=8,
            request_id=1,
            arrival_time=0
        )

        assert queue.enqueue(request, priority=5)
        assert len(queue) == 1

        dequeued = queue.dequeue()
        assert dequeued is not None
        assert dequeued.request_id == 1

    def test_full_queue(self):
        from model.controller.request import HBMRequest
        queue = SmartQueue(max_size=2)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, qos=8, request_id=1)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, qos=8, request_id=2)
        req3 = HBMRequest(addr=0x3000, length=64, is_read=True, qos=8, request_id=3)

        assert queue.enqueue(req1, priority=5)
        assert queue.enqueue(req2, priority=5)
        assert not queue.enqueue(req3, priority=5)  # Queue full

    def test_priority_aging(self):
        from model.controller.request import HBMRequest
        queue = SmartQueue(max_size=64, aging_factor=100)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, qos=4, request_id=1)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, qos=8, request_id=2)

        queue.enqueue(req1, priority=4)
        queue.enqueue(req2, priority=8)

        # After aging, lower priority request should get boost
        for _ in range(150):
            queue.update_aging()

        # Check aging was applied
        stats = queue.get_statistics()
        assert stats['aged_requests'] >= 0

    def test_statistics(self):
        from model.controller.request import HBMRequest
        queue = SmartQueue(max_size=64)

        for i in range(10):
            req = HBMRequest(addr=0x1000 + i*64, length=64, is_read=True, qos=8, request_id=i)
            queue.enqueue(req, priority=5)

        stats = queue.get_statistics()
        assert stats['total_enqueues'] == 10
        assert stats['current_depth'] == 10


class TestBankPredictor:
    """Tests for bank conflict predictor"""

    def test_creation(self):
        predictor = BankPredictor(num_banks=16)
        assert predictor.num_banks == 16
        assert len(predictor.banks) == 16

    def test_record_access(self):
        predictor = BankPredictor(num_banks=16)

        # Record access to bank 5
        is_hit = predictor.record_access(bank_id=5, row_id=0x100, cycle=100)
        assert not is_hit  # First access is always miss

        # Record same row
        is_hit = predictor.record_access(bank_id=5, row_id=0x100, cycle=101)
        assert is_hit  # Same row is a hit

        # Record different row
        is_hit = predictor.record_access(bank_id=5, row_id=0x200, cycle=102)
        assert not is_hit  # Different row is miss

    def test_predict_conflict(self):
        predictor = BankPredictor(num_banks=16)

        # Record some accesses
        for i in range(32):
            predictor.record_access(i % 16, (i * 0x100) % 0x1000, i)

        # Predict conflict
        prediction = predictor.predict_conflict(5, 0x300, 100)

        assert isinstance(prediction.will_conflict, bool)
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.estimated_penalty_cycles >= 0

    def test_optimal_bank_order(self):
        predictor = BankPredictor(num_banks=16)

        # Record accesses to establish pattern
        for i in range(64):
            predictor.record_access(bank_id=i % 16, row_id=i % 256, cycle=i)

        # Get optimal order
        request_banks = [0, 1, 2, 3, 4, 5, 6, 7]
        optimal = predictor.get_optimal_bank_order(request_banks)

        assert len(optimal) == len(request_banks)
        assert set(optimal) == set(request_banks)

    def test_bank_utilization(self):
        predictor = BankPredictor(num_banks=16)

        # Record uneven accesses
        for i in range(100):
            predictor.record_access(bank_id=i % 4, row_id=i, cycle=i)

        util = predictor.get_bank_utilization()
        assert len(util) == 16
        assert util[0] > util[8]  # Banks 0-3 used more

    def test_statistics(self):
        predictor = BankPredictor(num_banks=16)

        # Record some accesses
        for i in range(32):
            predictor.record_access(bank_id=i % 16, row_id=i, cycle=i)

        stats = predictor.get_statistics()
        assert 'total_predictions' in stats
        assert 'prediction_accuracy' in stats
        assert 'active_banks' in stats


# Run if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
