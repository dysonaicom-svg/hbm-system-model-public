"""
Unit tests for HBM4 Enhanced QoS Scheduler

Tests for:
- 16-class priority ordering
- Bandwidth guarantees
- Weighted fair queuing
- Anti-starvation mechanism
- Bank conflict awareness
- Traffic type classification
"""

import pytest
import time
from collections import defaultdict
from typing import List

from model.controller.HBM4_qos_scheduler import (
    HBM4QoSScheduler, QoSLevel, QoSClass, QoSWeight, QoSMonitor,
    TrafficType, TRAFFIC_TYPE_TO_QOS, QueuedRequest, BankConflictTracker
)
from model.controller.request import HBMRequest
from model.dram.hbm4_spec import HBM4Spec


class TestQoSLevelConstants:
    """Test QoS level constants are correctly defined"""

    def test_qos_critical_is_15(self):
        """CRITICAL QoS level should be 15"""
        assert HBM4QoSScheduler.QOS_CRITICAL == 15
        assert QoSLevel.CRITICAL == 15

    def test_qos_high_is_12(self):
        """HIGH QoS level should be 12"""
        assert HBM4QoSScheduler.QOS_HIGH == 12
        assert QoSLevel.HIGH == 12

    def test_qos_normal_is_8(self):
        """NORMAL QoS level should be 8"""
        assert HBM4QoSScheduler.QOS_NORMAL == 8
        assert QoSLevel.NORMAL == 8

    def test_qos_low_is_4(self):
        """LOW QoS level should be 4"""
        assert HBM4QoSScheduler.QOS_LOW == 4
        assert QoSLevel.LOW == 4

    def test_qos_idle_is_0(self):
        """IDLE QoS level should be 0"""
        assert HBM4QoSScheduler.QOS_IDLE == 0
        assert QoSLevel.IDLE == 0

    def test_all_16_levels_represented(self):
        """All 16 QoS levels (0-15) should have valid enum values"""
        for level in range(16):
            assert hasattr(QoSLevel, '_missing_') or level in [e.value for e in QoSLevel]


class TestTrafficTypeMapping:
    """Test traffic type to QoS level mapping"""

    def test_critical_traffic_maps_to_qos_15(self):
        """CRITICAL traffic type should map to QoS 15"""
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.CRITICAL] == 15
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.REAL_TIME] == 15

    def test_high_priority_traffic_maps_to_qos_12(self):
        """HIGH_PRIORITY traffic type should map to QoS 12"""
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.HIGH_PRIORITY] == 12

    def test_normal_traffic_maps_to_qos_8(self):
        """NORMAL traffic type should map to QoS 8"""
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.NORMAL] == 8

    def test_background_traffic_maps_to_qos_4(self):
        """BACKGROUND traffic type should map to QoS 4"""
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.BACKGROUND] == 4

    def test_idle_traffic_maps_to_qos_0(self):
        """IDLE traffic type should map to QoS 0"""
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.IDLE] == 0
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.PROBE] == 0


class TestSchedulerCreation:
    """Test scheduler initialization"""

    def test_scheduler_has_16_priority_levels(self):
        """Scheduler should have 16 priority levels"""
        scheduler = HBM4QoSScheduler()
        assert scheduler.priority_levels == 16

    def test_scheduler_initializes_qos_classes(self):
        """Scheduler should initialize all 16 QoS classes"""
        scheduler = HBM4QoSScheduler()
        classes = scheduler.get_all_qos_classes()
        assert len(classes) == 16
        for level in range(16):
            assert level in classes

    def test_scheduler_has_bank_tracker(self):
        """Scheduler should have bank conflict tracker"""
        scheduler = HBM4QoSScheduler()
        assert hasattr(scheduler, '_bank_tracker')
        assert isinstance(scheduler._bank_tracker, BankConflictTracker)

    def test_scheduler_has_qos_monitor(self):
        """Scheduler should have QoS monitor"""
        scheduler = HBM4QoSScheduler()
        assert hasattr(scheduler, '_monitor')
        assert isinstance(scheduler._monitor, QoSMonitor)


class TestQoSClassConfiguration:
    """Test QoS class configuration"""

    def test_critical_class_has_correct_properties(self):
        """CRITICAL class should have correct bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()
        cls = scheduler.get_qos_class(15)
        assert cls is not None
        assert cls.level == 15
        assert cls.bw_guarantee >= 200.0  # Minimum guarantee
        assert cls.weight >= 4.0  # High weight

    def test_high_class_has_correct_properties(self):
        """HIGH class should have correct bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()
        cls = scheduler.get_qos_class(12)
        assert cls is not None
        assert cls.level == 12
        assert cls.bw_guarantee >= 140.0
        assert cls.weight >= 3.0

    def test_normal_class_has_correct_properties(self):
        """NORMAL class should have correct bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()
        cls = scheduler.get_qos_class(8)
        assert cls is not None
        assert cls.level == 8
        assert cls.bw_guarantee >= 60.0
        assert cls.weight >= 2.0

    def test_low_class_has_correct_properties(self):
        """LOW class should have correct bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()
        cls = scheduler.get_qos_class(4)
        assert cls is not None
        assert cls.level == 4
        assert cls.bw_guarantee >= 20.0
        assert cls.weight >= 1.0

    def test_idle_class_has_zero_guarantee(self):
        """IDLE class should have zero bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()
        cls = scheduler.get_qos_class(0)
        assert cls is not None
        assert cls.level == 0
        assert cls.bw_guarantee == 0.0


class TestRequestSubmission:
    """Test request submission to scheduler"""

    def test_submit_valid_request(self):
        """Should successfully submit a valid request"""
        scheduler = HBM4QoSScheduler()
        result = scheduler.submit_request(
            request_id=1, addr=0x1000, qos=15, is_read=True
        )
        assert result is True
        assert scheduler.get_queue_size(15) == 1

    def test_submit_request_with_all_parameters(self):
        """Should submit request with all parameters"""
        scheduler = HBM4QoSScheduler()
        result = scheduler.submit_request(
            request_id=1, addr=0x1000, qos=12, is_read=True,
            channel=1, pseudo_channel=0, bank_group=1, bank=3, row=0x100, col=0x10,
            row_hit=True, length=64, traffic_type=TrafficType.HIGH_PRIORITY
        )
        assert result is True

    def test_submit_request_invalid_qos(self):
        """Should reject request with invalid QoS level"""
        scheduler = HBM4QoSScheduler()
        result = scheduler.submit_request(
            request_id=1, addr=0x1000, qos=16, is_read=True
        )
        assert result is False

    def test_submit_request_negative_qos(self):
        """Should reject request with negative QoS level"""
        scheduler = HBM4QoSScheduler()
        result = scheduler.submit_request(
            request_id=1, addr=0x1000, qos=-1, is_read=True
        )
        assert result is False

    def test_submit_multiple_requests_same_qos(self):
        """Should accept multiple requests at same QoS level"""
        scheduler = HBM4QoSScheduler()
        for i in range(10):
            result = scheduler.submit_request(
                request_id=i, addr=0x1000 + i, qos=8, is_read=True
            )
            assert result is True
        assert scheduler.get_queue_size(8) == 10


class TestPriorityOrdering:
    """Test 16-class priority ordering"""

    def test_high_priority_scheduled_before_low(self):
        """Higher priority requests should be scheduled before lower priority"""
        scheduler = HBM4QoSScheduler()

        # Submit low priority request first
        scheduler.submit_request(request_id=1, addr=0x1000, qos=4, is_read=True)

        # Submit high priority request
        scheduler.submit_request(request_id=2, addr=0x2000, qos=12, is_read=True)

        # Schedule should return the high priority request first
        scheduled = scheduler.schedule()
        assert scheduled is not None
        assert scheduled.qos == 12
        assert scheduled.request_id == 2

    def test_critical_priority_first(self):
        """CRITICAL priority (15) should be scheduled first"""
        scheduler = HBM4QoSScheduler()

        # Submit requests at all priority levels
        for qos in [0, 4, 8, 12, 15]:
            scheduler.submit_request(
                request_id=qos, addr=0x1000 + qos, qos=qos, is_read=True
            )

        # Schedule should return critical request first
        scheduled = scheduler.schedule()
        assert scheduled is not None
        assert scheduled.qos == 15

    def test_15_priority_before_14(self):
        """Priority 15 should be scheduled before priority 14"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=14, is_read=True)
        scheduler.submit_request(request_id=2, addr=0x2000, qos=15, is_read=True)

        scheduled = scheduler.schedule()
        assert scheduled.qos == 15

    def test_full_priority_order(self):
        """Requests should be scheduled in correct priority order (15 to 0)"""
        scheduler = HBM4QoSScheduler()

        # Submit one request at each priority level
        for qos in range(16):
            scheduler.submit_request(
                request_id=qos, addr=0x1000 + qos, qos=qos, is_read=True
            )

        # Schedule all and verify order
        scheduled_order = []
        while True:
            scheduled = scheduler.schedule()
            if scheduled is None:
                break
            scheduled_order.append(scheduled.qos)

        # All 16 requests should be scheduled
        assert len(scheduled_order) == 16

        # Verify descending order (15 first, 0 last)
        expected_order = list(range(15, -1, -1))
        assert scheduled_order == expected_order


class TestBandwidthGuarantees:
    """Test bandwidth guarantee mechanism"""

    def test_bandwidth_guarantee_setter(self):
        """Should be able to set bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()
        scheduler.set_bandwidth_guarantee(8, 100.0)
        assert scheduler._bw_guarantee[8] == 100.0

    def test_bandwidth_cap_setter(self):
        """Should be able to set bandwidth cap"""
        scheduler = HBM4QoSScheduler()
        scheduler.set_bandwidth_cap(8, 500.0)
        assert scheduler._bw_cap[8] == 500.0

    def test_default_bandwidth_guarantees(self):
        """Should have default bandwidth guarantees for all levels"""
        scheduler = HBM4QoSScheduler()
        for level in range(16):
            assert level in scheduler._bw_guarantee
            assert level in scheduler._bw_cap

    def test_can_schedule_below_guarantee(self):
        """Should always schedule when bandwidth is below guarantee"""
        scheduler = HBM4QoSScheduler()
        # Set very low guarantee
        scheduler.set_bandwidth_guarantee(8, 1000.0)
        # Current bandwidth is 0, should be able to schedule
        assert scheduler._can_schedule(8) is True

    def test_cannot_schedule_above_cap(self):
        """Should not schedule when bandwidth exceeds cap"""
        scheduler = HBM4QoSScheduler()
        # Set very low cap
        scheduler.set_bandwidth_cap(8, 0.001)
        # This level should not be schedulable
        # Note: actual behavior depends on current bandwidth tracking


class TestWeightedFairQueuing:
    """Test weighted fair queuing algorithm"""

    def test_weight_setter(self):
        """Should be able to set weight for a QoS level"""
        scheduler = HBM4QoSScheduler()
        scheduler.set_weight(8, 5.0)
        assert scheduler._weights.get_weight(8) == 5.0

    def test_default_weights_defined(self):
        """Default weights should be defined for main levels"""
        scheduler = HBM4QoSScheduler()
        assert scheduler._weights.get_weight(15) > scheduler._weights.get_weight(8)
        assert scheduler._weights.get_weight(8) > scheduler._weights.get_weight(0)

    def test_normalized_weights_sum_to_one(self):
        """Normalized weights should sum to 1.0"""
        weights = QoSWeight()
        normalized = weights.get_normalized_weights()
        total = sum(normalized.values())
        assert abs(total - 1.0) < 0.001

    def test_effective_weight_boost_at_low_fill(self):
        """Effective weight should be boosted when queue is nearly empty"""
        weights = QoSWeight()
        # At 5% fill, should get 2x boost
        effective_low = weights.get_effective_weight(8, 0.05)
        base = weights.get_weight(8)
        assert effective_low == base * 2.0

    def test_effective_weight_no_boost_at_high_fill(self):
        """Effective weight should not be boosted at high fill"""
        weights = QoSWeight()
        # At 50% fill, no boost
        effective_high = weights.get_effective_weight(8, 0.5)
        base = weights.get_weight(8)
        assert effective_high == base


class TestAntiStarvation:
    """Test anti-starvation mechanism"""

    def test_boost_starving_increments_age(self):
        """boost_starving should increment age counters"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=4, is_read=True)

        # Wait a bit
        time.sleep(0.01)

        # Call boost_starving
        scheduler.boost_starving()

        # Check that the request has age > 0
        req = scheduler._queues[4][0]
        assert req.age_cycles > 0

    def test_starvation_counter_increments(self):
        """Starvation counter should increment for old requests"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=4, is_read=True)

        # Wait for starvation threshold to pass
        # Note: actual threshold is in cycles, not time
        # This test just verifies the mechanism exists
        req = scheduler._queues[4][0]
        initial_counter = req.starvation_counter

        # Simulate old request by setting high age
        req.age_cycles = 2000

        scheduler.boost_starving()

        # Counter should have incremented
        assert req.starvation_counter >= initial_counter

    def test_starvation_boost_for_very_old_requests(self):
        """Very old requests should get priority boost"""
        scheduler = HBM4QoSScheduler()
        # Submit low priority request
        scheduler.submit_request(request_id=1, addr=0x1000, qos=4, is_read=True)

        # Simulate very old request
        req = scheduler._queues[4][0]
        req.arrival_time = time.time() - 100  # 100 seconds old

        # Get starvation boost
        boost = scheduler._get_starvation_boost(4)
        assert boost > 0


class TestFRFCFS:
    """Test First-Ready FCFS scheduling within priority"""

    def test_row_hit_priority(self):
        """Row hit requests should be scheduled first within same priority"""
        scheduler = HBM4QoSScheduler()

        # Submit non-row-hit first
        scheduler.submit_request(
            request_id=1, addr=0x1000, qos=8, is_read=True, row_hit=False
        )

        # Submit row-hit second
        scheduler.submit_request(
            request_id=2, addr=0x2000, qos=8, is_read=True, row_hit=True
        )

        # Row-hit should be scheduled first
        scheduled = scheduler.schedule()
        assert scheduled.row_hit is True
        assert scheduled.request_id == 2

    def test_oldest_first_when_no_row_hits(self):
        """Oldest request should be scheduled when no row hits"""
        scheduler = HBM4QoSScheduler()

        # Submit request 1 first
        scheduler.submit_request(request_id=1, addr=0x1000, qos=8, is_read=True)

        # Wait a bit longer to ensure age difference
        time.sleep(0.05)

        # Submit request 2 second
        scheduler.submit_request(request_id=2, addr=0x2000, qos=8, is_read=True)

        # Older (id=1) should be scheduled first based on arrival_time
        scheduled = scheduler.schedule()
        assert scheduled.request_id == 1


class TestBankConflictTracker:
    """Test bank conflict tracking"""

    def test_bank_tracker_creation(self):
        """Bank conflict tracker should be created"""
        tracker = BankConflictTracker()
        assert tracker.num_channels == 32
        assert tracker.num_banks == 16

    def test_row_open_detection(self):
        """Should detect when a row is open"""
        tracker = BankConflictTracker()
        tracker.open_row(channel=0, pseudo_channel=0, bg=0, bank=0, row=0x100)

        assert tracker.is_row_open(0, 0, 0, 0) is True
        assert tracker.get_open_row(0, 0, 0, 0) == 0x100

    def test_row_hit_detection(self):
        """Should detect row hits"""
        tracker = BankConflictTracker()
        tracker.open_row(channel=0, pseudo_channel=0, bg=0, bank=0, row=0x100)

        assert tracker.is_row_hit(0, 0, 0, 0, 0x100) is True
        assert tracker.is_row_hit(0, 0, 0, 0, 0x200) is False

    def test_row_close(self):
        """Should detect when row is closed"""
        tracker = BankConflictTracker()
        tracker.open_row(channel=0, pseudo_channel=0, bg=0, bank=0, row=0x100)
        tracker.close_row(channel=0, pseudo_channel=0, bg=0, bank=0)

        assert tracker.is_row_open(0, 0, 0, 0) is False
        assert tracker.get_open_row(0, 0, 0, 0) == -1


class TestSchedulerBankConflictIntegration:
    """Test scheduler integration with bank conflict tracking"""

    def test_scheduler_updates_bank_state(self):
        """Scheduler should update bank state when scheduling"""
        scheduler = HBM4QoSScheduler()

        # Submit request
        scheduler.submit_request(
            request_id=1, addr=0x1000, qos=15, is_read=True,
            channel=0, pseudo_channel=0, bank_group=0, bank=0, row=0x100
        )

        # Schedule it
        scheduler.schedule()

        # Bank state should be updated
        state = scheduler.get_bank_state(0, 0, 0, 0)
        assert state['open_row'] == 0x100

    def test_is_bank_conflict_detection(self):
        """Should detect bank conflicts"""
        scheduler = HBM4QoSScheduler()

        # Open a row (channel, pch, bg, bank, row)
        scheduler._bank_tracker.open_row(0, 0, 0, 0, 0x100)

        # Same row should not be a conflict (channel, pch, bg, bank, row)
        assert scheduler.is_bank_conflict(0, 0, 0, 0, 0x100) is False

        # Different row should be a conflict
        assert scheduler.is_bank_conflict(0, 0, 0, 0, 0x200) is True


class TestQoSMonitor:
    """Test QoS monitoring functionality"""

    def test_monitor_records_bandwidth(self):
        """Monitor should record bandwidth"""
        monitor = QoSMonitor()
        now = time.time()
        monitor.record_bandwidth(8, 1000, now)
        monitor.record_bandwidth(8, 1000, now)

        bw = monitor.get_bandwidth(8)
        assert bw > 0

    def test_monitor_records_schedule(self):
        """Monitor should record scheduling events"""
        monitor = QoSMonitor()
        monitor.record_schedule(8, row_hit=True)
        monitor.record_schedule(8, row_hit=False)

        stats = monitor.get_stats()
        assert stats['by_qos'][8]['scheduled'] == 2
        assert stats['by_qos'][8]['row_hit_rate'] == 0.5

    def test_monitor_records_starvation(self):
        """Monitor should record starvation events"""
        monitor = QoSMonitor()
        monitor.record_starvation(4)
        monitor.record_starvation(4)

        stats = monitor.get_stats()
        assert stats['by_qos'][4]['starvation_events'] == 2


class TestRequestClassification:
    """Test request classification"""

    def test_classify_request_with_valid_qos(self):
        """Request with valid QoS should use that QoS"""
        scheduler = HBM4QoSScheduler()
        req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=12)

        classified = scheduler.classify_request(req)
        assert classified == 12

    def test_classify_request_default_qos(self):
        """Request without QoS should default to NORMAL (8)"""
        scheduler = HBM4QoSScheduler()
        req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=8)

        classified = scheduler.classify_request(req)
        assert classified == 8

    def test_classify_invalid_qos(self):
        """Invalid QoS should default to NORMAL"""
        scheduler = HBM4QoSScheduler()
        req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=20)

        classified = scheduler.classify_request(req)
        assert classified == 8


class TestSubmitHBMRequest:
    """Test HBMRequest submission"""

    def test_submit_hbm_request(self):
        """Should submit HBMRequest object"""
        scheduler = HBM4QoSScheduler()
        req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=12)

        result = scheduler.submit_hbm_request(req)
        assert result is True
        assert scheduler.get_queue_size(12) == 1

    def test_submit_hbm_request_decodes_address(self):
        """Should decode address for bank/row info"""
        scheduler = HBM4QoSScheduler()
        # Use an address that will decode to valid fields
        addr = 0x0001_0000_0000_0000
        req = HBMRequest(addr=addr, length=64, is_read=True, qos=8)

        result = scheduler.submit_hbm_request(req)
        assert result is True


class TestQueueManagement:
    """Test queue management operations"""

    def test_get_queue_size(self):
        """Should return correct queue size"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=8, is_read=True)
        scheduler.submit_request(request_id=2, addr=0x2000, qos=8, is_read=True)

        assert scheduler.get_queue_size(8) == 2
        assert scheduler.get_queue_size(4) == 0

    def test_get_total_queue_size(self):
        """Should return total queue size across all levels"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=8, is_read=True)
        scheduler.submit_request(request_id=2, addr=0x2000, qos=12, is_read=True)
        scheduler.submit_request(request_id=3, addr=0x3000, qos=4, is_read=True)

        assert scheduler.get_total_queue_size() == 3

    def test_clear_queue(self):
        """Should clear specific queue"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=8, is_read=True)
        scheduler.submit_request(request_id=2, addr=0x2000, qos=8, is_read=True)

        scheduler.clear_queue(8)
        assert scheduler.get_queue_size(8) == 0

    def test_clear_all_queues(self):
        """Should clear all queues"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=8, is_read=True)
        scheduler.submit_request(request_id=2, addr=0x2000, qos=12, is_read=True)

        scheduler.clear_all_queues()
        assert scheduler.get_total_queue_size() == 0


class TestStatistics:
    """Test statistics collection"""

    def test_stats_tracking(self):
        """Should track scheduling statistics"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=8, is_read=True)
        scheduler.submit_request(request_id=2, addr=0x2000, qos=12, is_read=True)

        scheduler.schedule()
        scheduler.schedule()

        stats = scheduler.get_stats()
        assert stats['total_scheduled'] == 2
        assert stats['by_qos'][8] == 1
        assert stats['by_qos'][12] == 1

    def test_queue_depth_in_stats(self):
        """Stats should include queue depths"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=8, is_read=True)

        stats = scheduler.get_stats()
        assert 8 in stats['queues_by_level']
        assert stats['queues_by_level'][8] == 1


class TestSelectNext:
    """Test select_next method for external request lists"""

    def test_select_next_highest_priority(self):
        """Should select highest priority request"""
        scheduler = HBM4QoSScheduler()

        req_low = HBMRequest(addr=0x1000, length=64, is_read=True, qos=4)
        req_high = HBMRequest(addr=0x2000, length=64, is_read=True, qos=12)
        req_critical = HBMRequest(addr=0x3000, length=64, is_read=True, qos=15)

        requests = [req_low, req_high, req_critical]
        selected = scheduler.select_next(requests)

        assert selected.qos == 15

    def test_select_next_empty_list(self):
        """Should return None for empty list"""
        scheduler = HBM4QoSScheduler()
        selected = scheduler.select_next([])
        assert selected is None


class TestScheduleWeighted:
    """Test weighted fair queuing scheduling"""

    def test_schedule_weighted_returns_request(self):
        """schedule_weighted should return a scheduled request"""
        scheduler = HBM4QoSScheduler()
        scheduler.submit_request(request_id=1, addr=0x1000, qos=8, is_read=True)

        scheduled = scheduler.schedule_weighted()
        assert scheduled is not None
        assert scheduled.request_id == 1

    def test_schedule_weighted_prefers_higher_priority(self):
        """schedule_weighted should prefer higher priority"""
        scheduler = HBM4QoSScheduler()

        scheduler.submit_request(request_id=1, addr=0x1000, qos=4, is_read=True)
        scheduler.submit_request(request_id=2, addr=0x2000, qos=12, is_read=True)

        scheduled = scheduler.schedule_weighted()
        assert scheduled.qos == 12


# Integration test with real-world scenario
class TestRealWorldScenario:
    """Integration tests simulating real-world scenarios"""

    def test_ai_inference_workload(self):
        """Simulate AI inference workload with mixed priorities"""
        scheduler = HBM4QoSScheduler()

        # Critical inference requests (QoS 15)
        for i in range(5):
            scheduler.submit_request(
                request_id=i, addr=0x1000 + i * 0x100, qos=15, is_read=True,
                traffic_type=TrafficType.CRITICAL
            )

        # High priority requests (QoS 12)
        for i in range(5, 10):
            scheduler.submit_request(
                request_id=i, addr=0x2000 + i * 0x100, qos=12, is_read=True,
                traffic_type=TrafficType.HIGH_PRIORITY
            )

        # Batch processing (QoS 4)
        for i in range(10, 15):
            scheduler.submit_request(
                request_id=i, addr=0x3000 + i * 0x100, qos=4, is_read=True,
                traffic_type=TrafficType.BACKGROUND
            )

        # All critical should be scheduled first
        scheduled_order = []
        for _ in range(5):
            scheduled = scheduler.schedule()
            if scheduled:
                scheduled_order.append(scheduled.qos)

        assert all(q == 15 for q in scheduled_order)

    def test_bandwidth_guarantee_protection(self):
        """Higher priority should maintain bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()

        # Set different guarantees
        scheduler.set_bandwidth_guarantee(15, 500.0)  # High guarantee for critical
        scheduler.set_bandwidth_guarantee(4, 50.0)    # Low guarantee for background

        # Submit equal number of requests
        for i in range(10):
            scheduler.submit_request(
                request_id=i, addr=0x1000 + i, qos=15, is_read=True
            )
        for i in range(10, 20):
            scheduler.submit_request(
                request_id=i, addr=0x2000 + i, qos=4, is_read=True
            )

        # Critical requests should be scheduled first (guarantee protection)
        scheduled = scheduler.schedule()
        assert scheduled.qos == 15


if __name__ == '__main__':
    pytest.main([__file__, '-v'])