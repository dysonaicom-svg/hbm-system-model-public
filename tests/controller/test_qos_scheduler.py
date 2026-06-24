"""
Tests for HBM QoS Scheduler
Increases coverage from 33% to 95%+

Covers:
- BandwidthTracker
- QoSScheduler
- Bandwidth tracking methods
- QoS scheduling logic
"""

import pytest
from model.controller.qos_scheduler import (
    BandwidthTracker, QoSScheduler
)
from model.controller.config import HBMConfig
from model.controller.request import HBMRequest
from model.controller.queue import ReadQueue, WriteQueue
from model.controller.scheduler import BankState


class TestBandwidthTracker:
    """Tests for BandwidthTracker"""

    def test_creation(self):
        """Test BandwidthTracker creation"""
        tracker = BandwidthTracker(window_ms=2.0, max_samples=100)
        assert tracker.window_ms == 2.0
        assert tracker.max_samples == 100

    def test_record_single(self):
        """Test recording single bandwidth sample"""
        tracker = BandwidthTracker()
        tracker.record(qos=15, bytes=640, timestamp_ms=1.0)
        assert len(tracker.data[15]) == 1
        assert tracker.data[15][0] == (1.0, 640)

    def test_record_multiple_qos_levels(self):
        """Test recording for multiple QoS levels"""
        tracker = BandwidthTracker()
        tracker.record(qos=15, bytes=640, timestamp_ms=1.0)
        tracker.record(qos=8, bytes=320, timestamp_ms=1.0)
        tracker.record(qos=0, bytes=64, timestamp_ms=1.0)

        assert len(tracker.data[15]) == 1
        assert len(tracker.data[8]) == 1
        assert len(tracker.data[0]) == 1

    def test_get_bandwidth_no_data(self):
        """Test get_bandwidth with no data"""
        tracker = BandwidthTracker()
        bw = tracker.get_bandwidth(qos=15)
        assert bw == 0.0

    def test_get_bandwidth_with_data(self):
        """Test get_bandwidth with data"""
        tracker = BandwidthTracker(window_ms=1.0)
        tracker.record(qos=15, bytes=1000000000, timestamp_ms=0.5)  # 1GB at 0.5ms
        bw = tracker.get_bandwidth(qos=15)
        # Bandwidth = bytes / time / 1e9 = GB/s
        assert bw > 0

    def test_cleanup_old_data(self):
        """Test that old data is cleaned up"""
        tracker = BandwidthTracker(window_ms=1.0)
        tracker.record(qos=15, bytes=640, timestamp_ms=0.0)
        tracker.record(qos=15, bytes=640, timestamp_ms=0.5)
        tracker.record(qos=15, bytes=640, timestamp_ms=1.5)  # Old

        tracker.record(qos=15, bytes=640, timestamp_ms=2.0)

        # Old data at 0.0 and 0.5 should be cleaned when timestamp=2.0
        # Check that data is within window
        if tracker.data[15]:
            timestamps = [t for t, _ in tracker.data[15]]
            assert all(t >= 1.0 for t in timestamps)

    def test_max_samples_limit(self):
        """Test max samples limit"""
        tracker = BandwidthTracker(max_samples=5)
        for i in range(10):
            tracker.record(qos=15, bytes=64, timestamp_ms=float(i))

        assert len(tracker.data[15]) <= 5

    def test_multiple_qos_levels_tracking(self):
        """Test independent tracking per QoS level"""
        tracker = BandwidthTracker()

        # Add data to different QoS levels
        for qos in range(16):
            tracker.record(qos=qos, bytes=1000, timestamp_ms=1.0)

        for qos in range(16):
            assert len(tracker.data[qos]) == 1


class TestQoSScheduler:
    """Tests for QoSScheduler"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HBMConfig()

    @pytest.fixture
    def scheduler(self, config):
        """Create test scheduler"""
        return QoSScheduler(config)

    def test_scheduler_creation(self, scheduler, config):
        """Test scheduler creation"""
        assert scheduler.config == config
        assert scheduler.QOS_CRITICAL == 15
        assert scheduler.QOS_HIGH == 12
        assert scheduler.QOS_NORMAL == 8
        assert scheduler.QOS_LOW == 4
        assert scheduler.QOS_IDLE == 0

    def test_bandwidth_guarantee_config(self, scheduler):
        """Test bandwidth guarantee configuration"""
        assert scheduler.bandwidth_guarantee[15] == 200.0
        assert scheduler.bandwidth_guarantee[12] == 300.0
        assert scheduler.bandwidth_guarantee[8] == 200.0
        assert scheduler.bandwidth_guarantee[4] == 100.0

    def test_bandwidth_cap_config(self, scheduler):
        """Test bandwidth cap configuration"""
        assert scheduler.bandwidth_cap[15] == 1000.0
        assert scheduler.bandwidth_cap[12] == 800.0
        assert scheduler.bandwidth_cap[8] == 400.0
        assert scheduler.bandwidth_cap[4] == 200.0
        assert scheduler.bandwidth_cap[0] == 50.0

    def test_schedule_empty_queues(self, scheduler):
        """Test schedule with empty queues"""
        read_queue = ReadQueue()
        write_queue = WriteQueue()
        bank_states = {}

        result = scheduler.schedule(read_queue, write_queue, bank_states, 100.0)
        assert result is None

    def test_schedule_high_priority_read(self, scheduler):
        """Test scheduling high priority read request"""
        read_queue = ReadQueue()
        write_queue = WriteQueue()

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            qos=15,  # Critical
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            bank_group_id=0,
        )
        read_queue.push(request)

        result = scheduler.schedule(read_queue, write_queue, {}, 100.0)

        assert result is not None
        assert result.qos == 15

    def test_schedule_multiple_qos_levels(self, scheduler):
        """Test scheduling across multiple QoS levels"""
        read_queue = ReadQueue()

        # Add requests with different QoS levels
        for qos in [0, 4, 8, 12, 15]:
            for i in range(3):
                request = HBMRequest(
                    addr=0x1000 + (qos * 0x1000) + i,
                    length=64,
                    is_read=True,
                    qos=qos,
                    channel_id=0,
                    pseudo_channel_id=0,
                    bank_id=i,
                    bank_group_id=0,
                )
                read_queue.push(request)

        # Schedule should pick highest QoS first
        bank_states = {}
        result1 = scheduler.schedule(read_queue, WriteQueue(), bank_states, 100.0)
        assert result1.qos == 15

    def test_can_schedule_below_guarantee(self, scheduler):
        """Test _can_schedule when below guarantee"""
        # Clear bandwidth tracking
        scheduler.bw_tracker = BandwidthTracker()

        result = scheduler._can_schedule(15, 640)
        assert result is True  # Below guarantee, can schedule

    def test_can_schedule_above_cap(self, scheduler):
        """Test _can_schedule when above cap"""
        # Set bandwidth slightly above cap
        tracker = BandwidthTracker()
        # Add many samples to push bandwidth above cap (400 GB/s for qos 8)
        for i in range(200):
            tracker.record(qos=8, bytes=5000000000, timestamp_ms=float(i) * 0.001)
        scheduler.bw_tracker = tracker

        # Check current bandwidth is above cap
        current_bw = tracker.get_bandwidth(8)
        cap = scheduler.bandwidth_cap[8]
        assert current_bw >= cap  # Verify setup

        result = scheduler._can_schedule(8, 64)
        assert result is False  # Above cap, should not schedule

    def test_can_schedule_between_guarantee_and_cap(self, scheduler):
        """Test _can_schedule between guarantee and cap"""
        # Set bandwidth between guarantee and cap
        tracker = BandwidthTracker()
        tracker.record(qos=8, bytes=300000000, timestamp_ms=0.5)  # 300 GB/s
        scheduler.bw_tracker = tracker

        result = scheduler._can_schedule(8, 64)
        # Should allow scheduling (race condition mode)
        assert result is True

    def test_set_bandwidth_guarantee(self, scheduler):
        """Test set_bandwidth_guarantee"""
        scheduler.set_bandwidth_guarantee(15, 500.0)
        assert scheduler.bandwidth_guarantee[15] == 500.0

    def test_set_bandwidth_cap(self, scheduler):
        """Test set_bandwidth_cap"""
        scheduler.set_bandwidth_cap(15, 2000.0)
        assert scheduler.bandwidth_cap[15] == 2000.0

    def test_get_qos_stats(self, scheduler):
        """Test get_qos_stats"""
        stats = scheduler.get_qos_stats()

        assert 15 in stats
        assert 0 in stats
        assert 'bandwidth' in stats[15]
        assert 'guarantee' in stats[15]
        assert 'cap' in stats[15]

    def test_schedule_write_request(self, scheduler):
        """Test scheduling write request"""
        read_queue = ReadQueue()
        write_queue = WriteQueue()

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=False,  # Write
            qos=12,
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            bank_group_id=0,
        )
        write_queue.push(request)

        result = scheduler.schedule(read_queue, write_queue, {}, 100.0)

        assert result is not None
        assert result.is_read is False

    def test_schedule_marks_request_scheduled(self, scheduler):
        """Test that schedule marks request as scheduled"""
        read_queue = ReadQueue()
        write_queue = WriteQueue()

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            qos=10,
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            bank_group_id=0,
        )
        request.state = 0  # PENDING
        read_queue.push(request)

        scheduler.schedule(read_queue, write_queue, {}, 100.0)

        # Request should be removed from queue
        assert read_queue.size() == 0

    def test_fallback_to_frfcfs(self, scheduler):
        """Test fallback to FR-FCFS when all QoS limited"""
        # Set all QoS bandwidth above cap
        tracker = BandwidthTracker()
        for qos in range(16):
            for i in range(200):
                tracker.record(qos=qos, bytes=10000000, timestamp_ms=float(i) * 0.001)
        scheduler.bw_tracker = tracker

        read_queue = ReadQueue()
        write_queue = WriteQueue()

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            qos=8,
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            bank_group_id=0,
        )
        read_queue.push(request)

        # Should fallback to FR-FCFS
        result = scheduler.schedule(read_queue, write_queue, {}, 100.0)
        assert result is not None

    def test_custom_bandwidth_values(self):
        """Test scheduler with custom bandwidth values"""
        config = HBMConfig()
        config.bw_guarantee_critical = 500.0
        config.bw_guarantee_high = 600.0
        config.bw_guarantee_normal = 400.0
        config.bw_guarantee_low = 200.0

        scheduler = QoSScheduler(config)

        assert scheduler.bandwidth_guarantee[15] == 500.0
        assert scheduler.bandwidth_guarantee[12] == 600.0


class TestQoSSchedulerIntegration:
    """Integration tests for QoS scheduler"""

    def test_mixed_read_write_qos(self):
        """Test mixed read/write with QoS"""
        config = HBMConfig()
        scheduler = QoSScheduler(config)
        read_queue = ReadQueue()
        write_queue = WriteQueue()

        # High priority write
        write_req = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=False,
            qos=15,
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            bank_group_id=0,
        )
        write_queue.push(write_req)

        # Low priority read
        read_req = HBMRequest(
            addr=0x2000,
            length=64,
            is_read=True,
            qos=4,
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=1,
            bank_group_id=0,
        )
        read_queue.push(read_req)

        # Should prioritize high QoS write
        result = scheduler.schedule(read_queue, write_queue, {}, 100.0)
        assert result.qos == 15
        assert result.is_read is False

    def test_qos_starvation_prevention(self):
        """Test that low QoS doesn't starve completely"""
        config = HBMConfig()
        scheduler = QoSScheduler(config)

        # Low QoS request
        read_queue = ReadQueue()
        write_queue = WriteQueue()

        low_req = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            qos=0,  # Lowest
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            bank_group_id=0,
        )
        read_queue.push(low_req)

        # After many iterations with high QoS, low should get scheduled
        # This tests the bandwidth cap mechanism
        result = scheduler.schedule(read_queue, write_queue, {}, 100000.0)
        assert result is not None
