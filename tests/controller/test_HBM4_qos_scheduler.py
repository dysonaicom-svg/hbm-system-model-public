"""
Tests for HBM4 QoS Scheduler

Tests the QoS scheduler with 16 priority levels and anti-starvation.
"""

import pytest
from model.controller.HBM4_qos_scheduler import HBM4QoSScheduler, QoSLevel, QueuedRequest
from model.dram.HBM4_spec import HBM4Spec


class TestHBM4QoSSchedulerCreation:
    """Test QoS scheduler creation"""

    def test_scheduler_creation(self):
        """HBM4 QoS scheduler must support 16 priority levels"""
        scheduler = HBM4QoSScheduler()

        assert scheduler.priority_levels == 16
        assert scheduler.QOS_CRITICAL == 15
        assert scheduler.QOS_IDLE == 0

    def test_qos_levels_defined(self):
        """All QoS levels must be defined"""
        assert QoSLevel.CRITICAL == 15
        assert QoSLevel.HIGH == 12
        assert QoSLevel.NORMAL == 8
        assert QoSLevel.LOW == 4
        assert QoSLevel.IDLE == 0


class TestHBM4QoSSchedulerSubmit:
    """Test request submission"""

    def test_submit_request(self):
        """Requests must be submitted successfully"""
        scheduler = HBM4QoSScheduler()

        result = scheduler.submit_request(
            request_id=1,
            addr=0x10000000,
            qos=8,
            is_read=True
        )

        assert result is True
        assert scheduler.get_queue_size(8) == 1

    def test_submit_request_invalid_qos(self):
        """Invalid QoS level must be rejected"""
        scheduler = HBM4QoSScheduler()

        # QoS 16 is out of range (0-15)
        result = scheduler.submit_request(
            request_id=1,
            qos=16
        )

        assert result is False

    def test_submit_multiple_requests(self):
        """Multiple requests must be queued"""
        scheduler = HBM4QoSScheduler()

        for i in range(10):
            scheduler.submit_request(request_id=i, qos=8)

        assert scheduler.get_queue_size(8) == 10


class TestHBM4QoSSchedulerSchedule:
    """Test request scheduling"""

    def test_schedule_returns_request(self):
        """schedule() must return a queued request"""
        scheduler = HBM4QoSScheduler()

        scheduler.submit_request(request_id=1, qos=8)
        scheduled = scheduler.schedule()

        assert scheduled is not None
        assert scheduled.request_id == 1

    def test_schedule_respects_priority(self):
        """High priority must be scheduled before low priority"""
        scheduler = HBM4QoSScheduler()

        # Submit low priority first
        scheduler.submit_request(request_id=1, qos=0)

        # Submit high priority second
        scheduler.submit_request(request_id=2, qos=15)

        # High priority (15) should be scheduled first
        scheduled = scheduler.schedule()
        assert scheduled.qos == 15
        assert scheduled.request_id == 2

    def test_schedule_empty_queue(self):
        """schedule() must return None when queue empty"""
        scheduler = HBM4QoSScheduler()

        scheduled = scheduler.schedule()
        assert scheduled is None

    def test_schedule_fifo_within_priority(self):
        """Within same priority, FCFS ordering must apply"""
        scheduler = HBM4QoSScheduler()

        scheduler.submit_request(request_id=1, qos=8)
        scheduler.submit_request(request_id=2, qos=8)
        scheduler.submit_request(request_id=3, qos=8)

        scheduled = scheduler.schedule()
        assert scheduled.request_id == 1  # Oldest first


class TestHBM4QoSAntiStarvation:
    """Test anti-starvation guarantees"""

    def test_low_priority_not_starved(self):
        """Low priority requests must eventually be schedulable"""
        scheduler = HBM4QoSScheduler()

        # Submit high priority requests (simulating high bandwidth usage)
        for i in range(10):
            scheduler.submit_request(request_id=i, qos=15)

        # Submit low priority request
        scheduler.submit_request(request_id=100, qos=0)

        # Low priority should still be schedulable
        # (it will be after high priority is drained)
        while True:
            req = scheduler.schedule()
            if req is None:
                break
            if req.qos == 0:
                assert req.request_id == 100
                return

        # If we get here without finding low priority, test fails
        assert False, "Low priority was starved"

    def test_bandwidth_guarantee(self):
        """Each QoS level must have configurable bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()

        # Verify bandwidth guarantees are set
        assert scheduler.bw_guarantee[15] > scheduler.bw_guarantee[0]
        assert scheduler.bw_guarantee[12] > scheduler.bw_guarantee[4]


class TestHBM4QoSFRFCFS:
    """Test FR-FCFS scheduling within priority"""

    def test_row_hit_preferred(self):
        """Row hit requests must be preferred"""
        scheduler = HBM4QoSScheduler()

        # Submit row miss request first
        scheduler.submit_request(request_id=1, qos=8, row_hit=False)

        # Submit row hit request second
        scheduler.submit_request(request_id=2, qos=8, row_hit=True)

        # Row hit should be scheduled first despite arriving later
        scheduled = scheduler.schedule()
        assert scheduled.row_hit is True
        assert scheduled.request_id == 2


class TestHBM4QoSQueueManagement:
    """Test queue management"""

    def test_get_queue_size(self):
        """get_queue_size must return correct count"""
        scheduler = HBM4QoSScheduler()

        for i in range(5):
            scheduler.submit_request(request_id=i, qos=8)

        assert scheduler.get_queue_size(8) == 5
        assert scheduler.get_queue_size(15) == 0

    def test_clear_queue(self):
        """clear_queue must remove all requests"""
        scheduler = HBM4QoSScheduler()

        for i in range(10):
            scheduler.submit_request(request_id=i, qos=8)

        scheduler.clear_queue(8)
        assert scheduler.get_queue_size(8) == 0

    def test_get_total_queue_size(self):
        """get_total_queue_size must return total across all priorities"""
        scheduler = HBM4QoSScheduler()

        for i in range(5):
            scheduler.submit_request(request_id=i, qos=8)
        for i in range(3):
            scheduler.submit_request(request_id=i + 10, qos=15)

        assert scheduler.get_total_queue_size() == 8


class TestHBM4QoSWithSpec:
    """Test scheduler with HBM4 spec"""

    def test_scheduler_with_hbm4_spec(self):
        """Scheduler must work with HBM4 specification"""
        spec = HBM4Spec()
        scheduler = HBM4QoSScheduler(spec)

        assert scheduler.priority_levels == 16

        # Submit request
        scheduler.submit_request(
            request_id=1,
            addr=0x10000000,
            qos=8,
            is_read=True,
            channel=15,
            pseudo_channel=1,
            bank=5
        )

        scheduled = scheduler.schedule()
        assert scheduled.channel == 15
        assert scheduled.pseudo_channel == 1
        assert scheduled.bank == 5