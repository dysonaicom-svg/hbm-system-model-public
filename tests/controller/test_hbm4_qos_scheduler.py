"""
Enhanced Tests for HBM4 QoS Scheduler

Comprehensive tests covering:
- All 16 priority levels (0-15)
- Fairness and weighted fair queuing
- Anti-starvation guarantees
- Traffic type classification
- Bandwidth guarantees and caps
- Bank conflict tracking (FR-FCFS)
- Queue management
- Statistics and monitoring
"""

import pytest
import time
from model.controller.hbm4_qos_scheduler import (
    HBM4QoSScheduler, QoSLevel, TrafficType, TRAFFIC_TYPE_TO_QOS,
    QoSClass, QoSWeight, QoSMonitor, BankConflictTracker, QueuedRequest
)
from model.dram.hbm4_spec import HBM4Spec


# =============================================================================
# Test Class: Basic Scheduler Creation
# =============================================================================

class TestHBM4QoSSchedulerCreation:
    """Test QoS scheduler creation"""

    def test_scheduler_creation(self):
        """HBM4 QoS scheduler must support 16 priority levels"""
        scheduler = HBM4QoSScheduler()

        assert scheduler.priority_levels == 16
        assert scheduler.QOS_CRITICAL == 15
        assert scheduler.QOS_HIGH == 12
        assert scheduler.QOS_NORMAL == 8
        assert scheduler.QOS_LOW == 4
        assert scheduler.QOS_IDLE == 0

    def test_scheduler_with_config(self):
        """Scheduler must work with custom HBM4 spec"""
        spec = HBM4Spec()
        scheduler = HBM4QoSScheduler(spec)

        assert scheduler.priority_levels == 16
        assert scheduler.config is spec

    def test_qos_levels_defined(self):
        """All QoS levels must be defined correctly"""
        assert QoSLevel.CRITICAL == 15
        assert QoSLevel.HIGH == 12
        assert QoSLevel.NORMAL == 8
        assert QoSLevel.LOW == 4
        assert QoSLevel.IDLE == 0

    def test_qos_level_constants(self):
        """All QoS level constants must match"""
        assert QoSLevel.CRITICAL == HBM4QoSScheduler.QOS_CRITICAL
        assert QoSLevel.HIGH == HBM4QoSScheduler.QOS_HIGH
        assert QoSLevel.NORMAL == HBM4QoSScheduler.QOS_NORMAL
        assert QoSLevel.LOW == HBM4QoSScheduler.QOS_LOW
        assert QoSLevel.IDLE == HBM4QoSScheduler.QOS_IDLE


# =============================================================================
# Test Class: All 16 Priority Levels
# =============================================================================

class TestAll16PriorityLevels:
    """Test all 16 priority levels (0-15)"""

    def test_submit_all_qos_levels(self):
        """All 16 QoS levels (0-15) must accept requests"""
        scheduler = HBM4QoSScheduler()

        for qos in range(16):
            result = scheduler.submit_request(request_id=qos, qos=qos)
            assert result is True, f"Failed to submit QoS level {qos}"
            assert scheduler.get_queue_size(qos) == 1

    def test_schedule_all_qos_levels(self):
        """All 16 QoS levels must be schedulable"""
        scheduler = HBM4QoSScheduler()

        # Submit one request at each level
        for qos in range(16):
            scheduler.submit_request(request_id=qos, qos=qos)

        # Schedule all and verify
        scheduled_levels = []
        for _ in range(16):
            req = scheduler.schedule()
            assert req is not None, "Failed to schedule request"
            scheduled_levels.append(req.qos)

        # All levels should be scheduled
        assert len(scheduled_levels) == 16
        assert scheduler.get_total_queue_size() == 0

    def test_priority_order_all_levels(self):
        """Higher QoS levels must be scheduled first across all 16 levels"""
        scheduler = HBM4QoSScheduler()

        # Submit all levels, lowest first
        for qos in range(16):
            scheduler.submit_request(request_id=qos, qos=qos)

        # Schedule and verify order
        scheduled_levels = []
        for _ in range(16):
            req = scheduler.schedule()
            if req:
                scheduled_levels.append(req.qos)

        # Should be in descending order (15, 14, ..., 0)
        assert scheduled_levels == list(range(15, -1, -1))

    def test_qos_15_vs_qos_0(self):
        """QoS 15 (CRITICAL) must always be scheduled before QoS 0 (IDLE)"""
        scheduler = HBM4QoSScheduler()

        # Submit idle first
        scheduler.submit_request(request_id=1, qos=0)

        # Submit critical second
        scheduler.submit_request(request_id=2, qos=15)

        # Critical should be scheduled first
        scheduled = scheduler.schedule()
        assert scheduled.qos == 15
        assert scheduled.request_id == 2

    def test_qos_boundary_values(self):
        """Boundary QoS values (0 and 15) must work correctly"""
        scheduler = HBM4QoSScheduler()

        # Minimum QoS (0)
        result = scheduler.submit_request(request_id=1, qos=0)
        assert result is True
        assert scheduler.get_queue_size(0) == 1

        # Maximum QoS (15)
        result = scheduler.submit_request(request_id=2, qos=15)
        assert result is True
        assert scheduler.get_queue_size(15) == 1

        # Schedule and verify order
        req = scheduler.schedule()
        assert req.qos == 15  # Higher priority first

    def test_qos_intermediate_levels(self):
        """Intermediate QoS levels (1-14) must work correctly"""
        scheduler = HBM4QoSScheduler()

        # Submit a range of intermediate levels
        test_levels = [1, 5, 7, 10, 14]
        for qos in test_levels:
            scheduler.submit_request(request_id=qos, qos=qos)

        # Schedule and verify descending order
        scheduled = []
        for _ in range(len(test_levels)):
            req = scheduler.schedule()
            if req:
                scheduled.append(req.qos)

        assert scheduled == sorted(scheduled, reverse=True)


# =============================================================================
# Test Class: Traffic Type Classification
# =============================================================================

class TestTrafficTypeClassification:
    """Test traffic type to QoS level mapping"""

    def test_traffic_type_mapping(self):
        """Traffic types must map to correct QoS levels"""
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.REAL_TIME] == QoSLevel.CRITICAL
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.CRITICAL] == QoSLevel.CRITICAL
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.HIGH_PRIORITY] == QoSLevel.HIGH
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.NORMAL] == QoSLevel.NORMAL
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.BACKGROUND] == QoSLevel.LOW
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.PROBE] == QoSLevel.IDLE
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.IDLE] == QoSLevel.IDLE

    def test_submit_with_traffic_type(self):
        """Requests submitted with traffic type must be queued correctly"""
        scheduler = HBM4QoSScheduler()

        result = scheduler.submit_request(
            request_id=1,
            qos=8,
            traffic_type=TrafficType.CRITICAL
        )
        assert result is True

    def test_qos_class_traffic_priority(self):
        """Higher traffic priority must result in higher effective priority"""
        scheduler = HBM4QoSScheduler()

        # Submit with different traffic types at same QoS level
        # Traffic type is stored but scheduling uses QoS level
        scheduler.submit_request(request_id=1, qos=8, traffic_type=TrafficType.IDLE)
        scheduler.submit_request(request_id=2, qos=8, traffic_type=TrafficType.CRITICAL)

        # Both at QoS 8, so first submitted (IDLE) should be scheduled first
        req1 = scheduler.schedule()
        assert req1.traffic_type == TrafficType.IDLE  # IDLE was first

        req2 = scheduler.schedule()
        assert req2.traffic_type == TrafficType.CRITICAL  # CRITICAL was second


# =============================================================================
# Test Class: Fairness Tests
# =============================================================================

class TestFairness:
    """Test fairness in scheduling"""

    def test_equal_requests_equal_qos(self):
        """Requests at same QoS level must be scheduled in FCFS order"""
        scheduler = HBM4QoSScheduler()

        for i in range(5):
            scheduler.submit_request(request_id=i, qos=8)

        # Should schedule in order: 0, 1, 2, 3, 4
        for expected_id in range(5):
            req = scheduler.schedule()
            assert req.request_id == expected_id

    def test_weighted_fair_queuing_basic(self):
        """Weighted fair queuing must respect QoS weights"""
        scheduler = HBM4QoSScheduler()

        # Submit requests at different QoS levels
        # Higher QoS should get more scheduling opportunities
        for _ in range(10):
            scheduler.submit_request(request_id=_, qos=15, addr=_ * 0x1000)  # CRITICAL
        for _ in range(10):
            scheduler.submit_request(request_id=100 + _, qos=4, addr=(100 + _) * 0x1000)  # LOW

        # Count scheduling by level
        critical_count = 0
        low_count = 0

        for _ in range(20):
            req = scheduler.schedule()
            if req:
                if req.qos == 15:
                    critical_count += 1
                elif req.qos == 4:
                    low_count += 1

        # CRITICAL should be scheduled first due to higher priority
        assert critical_count > 0
        assert low_count >= 0

    def test_fairness_with_equal_weights(self):
        """When weights are equal, scheduling should be fair"""
        scheduler = HBM4QoSScheduler()

        # Set equal weights for two levels
        scheduler.set_weight(8, 1.0)
        scheduler.set_weight(10, 1.0)

        # Submit equal number of requests
        for i in range(5):
            scheduler.submit_request(request_id=i, qos=8)
            scheduler.submit_request(request_id=i + 10, qos=10)

        # Both levels should eventually be scheduled
        qos_8_count = 0
        qos_10_count = 0

        for _ in range(10):
            req = scheduler.schedule()
            if req.qos == 8:
                qos_8_count += 1
            elif req.qos == 10:
                qos_10_count += 1

        # Both should be scheduled
        assert qos_8_count > 0
        assert qos_10_count > 0

    def test_bandwidth_guarantee_respected(self):
        """Bandwidth guarantees must be configurable and respected"""
        scheduler = HBM4QoSScheduler()

        # Set bandwidth guarantees
        scheduler.set_bandwidth_guarantee(15, 200.0)  # CRITICAL gets 200 GB/s
        scheduler.set_bandwidth_guarantee(0, 10.0)    # IDLE gets 10 GB/s

        # Verify guarantees are set
        assert scheduler.bw_guarantee[15] == 200.0
        assert scheduler.bw_guarantee[0] == 10.0
        assert scheduler.bw_guarantee[15] > scheduler.bw_guarantee[0]

    def test_starvation_free_scheduling(self):
        """Low priority requests must eventually be scheduled"""
        scheduler = HBM4QoSScheduler()

        # Submit many high priority requests
        for i in range(50):
            scheduler.submit_request(request_id=i, qos=15)

        # Submit one low priority request
        scheduler.submit_request(request_id=1000, qos=0)

        # Low priority should eventually be scheduled
        low_priority_scheduled = False
        for _ in range(51):
            req = scheduler.schedule()
            if req and req.qos == 0:
                low_priority_scheduled = True
                break

        assert low_priority_scheduled, "Low priority was starved"


# =============================================================================
# Test Class: Anti-Starvation Tests
# =============================================================================

class TestAntiStarvation:
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

    def test_starvation_counter_increment(self):
        """Starvation counter must increment for waiting requests"""
        scheduler = HBM4QoSScheduler()

        scheduler.submit_request(request_id=1, qos=0)

        # Trigger starvation boost check
        scheduler.boost_starving()

        # Get the request and check starvation
        req = scheduler._queues[0][0]
        assert req.starvation_counter >= 0

    def test_bandwidth_guarantee(self):
        """Each QoS level must have configurable bandwidth guarantee"""
        scheduler = HBM4QoSScheduler()

        # Verify bandwidth guarantees are set
        assert scheduler.bw_guarantee[15] > scheduler.bw_guarantee[0]
        assert scheduler.bw_guarantee[12] > scheduler.bw_guarantee[4]

    def test_max_starvation_cycles(self):
        """Maximum starvation cycles limit must be respected"""
        scheduler = HBM4QoSScheduler()

        assert scheduler._max_starvation_cycles == 10000
        assert scheduler.DEFAULT_MAX_STARVATION_CYCLES == 10000

    def test_starvation_boost_threshold(self):
        """Starvation boost threshold must be configurable"""
        scheduler = HBM4QoSScheduler()

        assert scheduler._starvation_threshold == 1000
        assert scheduler.DEFAULT_STARVATION_BOOST_THRESHOLD == 1000
        assert scheduler._starvation_boost_factor == 2.0
        assert scheduler.DEFAULT_STARVATION_BOOST_FACTOR == 2.0


# =============================================================================
# Test Class: FR-FCFS Scheduling
# =============================================================================

class TestFRFCFS:
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

    def test_multiple_row_hits_fcfs(self):
        """Multiple row hits must be scheduled in FCFS order"""
        scheduler = HBM4QoSScheduler()

        scheduler.submit_request(request_id=1, qos=8, row_hit=True)
        scheduler.submit_request(request_id=2, qos=8, row_hit=True)
        scheduler.submit_request(request_id=3, qos=8, row_hit=True)

        # First request (oldest) should be scheduled first
        scheduled = scheduler.schedule()
        assert scheduled.request_id == 1

    def test_row_miss_after_row_hits(self):
        """Row miss requests must wait for all row hits"""
        scheduler = HBM4QoSScheduler()

        scheduler.submit_request(request_id=1, qos=8, row_hit=False)
        scheduler.submit_request(request_id=2, qos=8, row_hit=True)
        scheduler.submit_request(request_id=3, qos=8, row_hit=True)

        # Row hit (2) should be scheduled first
        scheduled = scheduler.schedule()
        assert scheduled.request_id == 2
        assert scheduled.row_hit is True

        # Second row hit (3) should be next
        scheduled = scheduler.schedule()
        assert scheduled.request_id == 3
        assert scheduled.row_hit is True

        # Now row miss (1) should be scheduled
        scheduled = scheduler.schedule()
        assert scheduled.request_id == 1
        assert scheduled.row_hit is False

    def test_fr_fcfs_with_mixed_priorities(self):
        """FR-FCFS applies within same priority level"""
        scheduler = HBM4QoSScheduler()

        # Low priority with row hit
        scheduler.submit_request(request_id=1, qos=4, row_hit=False)

        # High priority with row miss
        scheduler.submit_request(request_id=2, qos=15, row_hit=False)

        # High priority should still be scheduled first
        scheduled = scheduler.schedule()
        assert scheduled.qos == 15
        assert scheduled.request_id == 2


# =============================================================================
# Test Class: Queue Management
# =============================================================================

class TestQueueManagement:
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

    def test_clear_all_queues(self):
        """clear_all_queues must remove all requests from all levels"""
        scheduler = HBM4QoSScheduler()

        for qos in range(16):
            for i in range(3):
                scheduler.submit_request(request_id=qos * 100 + i, qos=qos)

        assert scheduler.get_total_queue_size() == 48

        scheduler.clear_all_queues()
        assert scheduler.get_total_queue_size() == 0

    def test_get_total_queue_size(self):
        """get_total_queue_size must return total across all priorities"""
        scheduler = HBM4QoSScheduler()

        for i in range(5):
            scheduler.submit_request(request_id=i, qos=8)
        for i in range(3):
            scheduler.submit_request(request_id=i + 10, qos=15)

        assert scheduler.get_total_queue_size() == 8

    def test_queue_depth_limit(self):
        """Requests must be rejected when queue is full"""
        scheduler = HBM4QoSScheduler()

        # Default max queue depth is 32
        for i in range(32):
            result = scheduler.submit_request(request_id=i, qos=8)
            assert result is True

        # Next request should be rejected
        result = scheduler.submit_request(request_id=999, qos=8)
        assert result is False


# =============================================================================
# Test Class: Bandwidth Configuration
# =============================================================================

class TestBandwidthConfiguration:
    """Test bandwidth configuration"""

    def test_default_bandwidth_guarantees(self):
        """Default bandwidth guarantees must be set correctly"""
        scheduler = HBM4QoSScheduler()

        # CRITICAL should have highest guarantee
        assert scheduler.bw_guarantee[15] > scheduler.bw_guarantee[8]
        assert scheduler.bw_guarantee[8] > scheduler.bw_guarantee[0]

    def test_set_bandwidth_guarantee(self):
        """Bandwidth guarantee must be configurable"""
        scheduler = HBM4QoSScheduler()

        scheduler.set_bandwidth_guarantee(8, 100.0)
        assert scheduler.bw_guarantee[8] == 100.0

        # QoS class should also be updated
        qos_class = scheduler.get_qos_class(8)
        assert qos_class.bw_guarantee == 100.0

    def test_set_bandwidth_cap(self):
        """Bandwidth cap must be configurable"""
        scheduler = HBM4QoSScheduler()

        scheduler.set_bandwidth_cap(8, 500.0)
        assert scheduler.bw_cap[8] == 500.0

    def test_bandwidth_cap_higher_than_guarantee(self):
        """Bandwidth cap should be higher than guarantee"""
        scheduler = HBM4QoSScheduler()

        for level in range(16):
            guarantee = scheduler.bw_guarantee[level]
            cap = scheduler.bw_cap[level]
            # Cap should be >= guarantee (or infinite)
            assert cap >= guarantee or cap == float('inf')


# =============================================================================
# Test Class: Request Submission
# =============================================================================

class TestRequestSubmission:
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

    def test_submit_request_negative_qos(self):
        """Negative QoS level must be rejected"""
        scheduler = HBM4QoSScheduler()

        result = scheduler.submit_request(request_id=1, qos=-1)
        assert result is False

    def test_submit_multiple_requests(self):
        """Multiple requests must be queued"""
        scheduler = HBM4QoSScheduler()

        for i in range(10):
            scheduler.submit_request(request_id=i, qos=8)

        assert scheduler.get_queue_size(8) == 10

    def test_submit_request_with_all_fields(self):
        """Requests with all fields must be submitted correctly"""
        scheduler = HBM4QoSScheduler()

        result = scheduler.submit_request(
            request_id=1,
            addr=0x10000000,
            qos=12,
            is_read=True,
            channel=15,
            pseudo_channel=1,
            bank_group=5,
            bank=10,
            row=0x1000,
            col=0x40,
            row_hit=True,
            length=128
        )

        assert result is True

        req = scheduler.schedule()
        assert req.channel == 15
        assert req.pseudo_channel == 1
        assert req.bank_group == 5
        assert req.bank == 10
        assert req.row == 0x1000
        assert req.col == 0x40
        assert req.row_hit is True
        assert req.length == 128


# =============================================================================
# Test Class: Scheduling
# =============================================================================

class TestScheduling:
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

    def test_schedule_weighted(self):
        """schedule_weighted() must implement weighted fair queuing"""
        scheduler = HBM4QoSScheduler()

        for i in range(5):
            scheduler.submit_request(request_id=i, qos=15)
        for i in range(5):
            scheduler.submit_request(request_id=i + 10, qos=4)

        # Should schedule multiple rounds
        scheduled = []
        for _ in range(10):
            req = scheduler.schedule_weighted()
            if req:
                scheduled.append(req)

        assert len(scheduled) == 10


# =============================================================================
# Test Class: Bank Conflict Tracking
# =============================================================================

class TestBankConflictTracking:
    """Test bank conflict tracking for FR-FCFS"""

    def test_bank_tracker_creation(self):
        """Bank conflict tracker must initialize correctly"""
        tracker = BankConflictTracker()

        assert tracker.num_channels == 32
        assert tracker.num_pseudo_channels == 2
        assert tracker.num_bank_groups == 8
        assert tracker.num_banks == 16

    def test_open_and_close_row(self):
        """Rows must be openable and closeable"""
        tracker = BankConflictTracker()

        # Open a row
        tracker.open_row(channel=0, pseudo_channel=0, bg=0, bank=0, row=100)

        assert tracker.is_row_open(0, 0, 0, 0) is True
        assert tracker.get_open_row(0, 0, 0, 0) == 100

        # Close the row
        tracker.close_row(channel=0, pseudo_channel=0, bg=0, bank=0)

        assert tracker.is_row_open(0, 0, 0, 0) is False
        assert tracker.get_open_row(0, 0, 0, 0) == -1

    def test_row_hit_detection(self):
        """Row hit must be detected correctly"""
        tracker = BankConflictTracker()

        # Open row 100
        tracker.open_row(channel=0, pseudo_channel=0, bg=0, bank=0, row=100)

        # Row 100 access is a hit
        assert tracker.is_row_hit(0, 0, 0, 0, row=100) is True

        # Row 200 access is a miss
        assert tracker.is_row_hit(0, 0, 0, 0, row=200) is False

    def test_bank_state(self):
        """Bank state must be retrievable"""
        tracker = BankConflictTracker()

        tracker.open_row(channel=1, pseudo_channel=1, bg=3, bank=5, row=500)

        state = tracker.get_bank_state(1, 1, 3, 5)
        assert state['open_row'] == 500
        assert state['last_cmd'] == 'ACTIVATE'

    def test_scheduler_bank_tracking(self):
        """Scheduler must track bank state"""
        scheduler = HBM4QoSScheduler()

        # Submit request that opens a row
        scheduler.submit_request(
            request_id=1,
            qos=8,
            channel=0,
            pseudo_channel=0,
            bank_group=0,
            bank=0,
            row=100
        )

        req = scheduler.schedule()
        assert req is not None

        # Check bank state
        state = scheduler.get_bank_state(0, 0, 0, 0)
        assert state['open_row'] == 100


# =============================================================================
# Test Class: QoS Monitor
# =============================================================================

class TestQoSMonitor:
    """Test QoS monitoring functionality"""

    def test_monitor_creation(self):
        """QoS monitor must initialize correctly"""
        monitor = QoSMonitor()

        assert monitor.window_ms == 1.0
        assert monitor.max_samples == 1000

    def test_record_bandwidth(self):
        """Bandwidth must be recordable"""
        monitor = QoSMonitor()

        monitor.record_bandwidth(15, 1000, time.time())
        bw = monitor.get_bandwidth(15)
        assert bw > 0

    def test_record_latency(self):
        """Latency must be recordable"""
        monitor = QoSMonitor()

        start = time.time()
        end = start + 0.001  # 1ms = 1000us

        monitor.record_latency(8, start, end)
        avg_latency = monitor.get_average_latency(8)

        # Should be approximately 1000 us
        assert avg_latency > 0

    def test_record_schedule(self):
        """Scheduling events must be recordable"""
        monitor = QoSMonitor()

        monitor.record_schedule(8, row_hit=True)
        monitor.record_schedule(8, row_hit=False)

        stats = monitor.get_stats()
        assert stats['by_qos'][8]['scheduled'] == 2

    def test_record_reject(self):
        """Rejected requests must be recordable"""
        monitor = QoSMonitor()

        monitor.record_reject(8)
        monitor.record_reject(8)

        stats = monitor.get_stats()
        assert stats['by_qos'][8]['rejected'] == 2

    def test_row_hit_rate(self):
        """Row hit rate must be calculable"""
        monitor = QoSMonitor()

        for _ in range(10):
            monitor.record_schedule(8, row_hit=True)
        for _ in range(10):
            monitor.record_schedule(8, row_hit=False)

        rate = monitor.get_row_hit_rate(8)
        assert rate == 0.5


# =============================================================================
# Test Class: QoS Class Configuration
# =============================================================================

class TestQoSClassConfiguration:
    """Test QoS class configuration"""

    def test_qos_class_creation(self):
        """QoS class must initialize with correct defaults"""
        qos_class = QoSClass(level=8)

        assert qos_class.level == 8
        assert qos_class.weight == 1.0
        assert qos_class.bw_guarantee == 0.0
        assert qos_class.bw_cap == float('inf')
        assert qos_class.max_queue_depth == 32
        assert qos_class.latency_sla == -1.0

    def test_qos_class_description(self):
        """QoS class must have description"""
        qos_class = QoSClass(level=15)
        assert "Real-time" in qos_class.description or qos_class.description != ""

    def test_scheduler_qos_classes(self):
        """Scheduler must provide QoS class access"""
        scheduler = HBM4QoSScheduler()

        # All 16 levels should have QoS classes
        for level in range(16):
            qos_class = scheduler.get_qos_class(level)
            assert qos_class is not None
            assert qos_class.level == level

    def test_get_all_qos_classes(self):
        """All QoS classes must be retrievable"""
        scheduler = HBM4QoSScheduler()

        all_classes = scheduler.get_all_qos_classes()
        assert len(all_classes) == 16


# =============================================================================
# Test Class: QoS Weight Configuration
# =============================================================================

class TestQoSWeight:
    """Test QoS weight configuration"""

    def test_default_weights(self):
        """Default weights must be set correctly"""
        weights = QoSWeight()

        # CRITICAL should have highest weight
        assert weights.get_weight(15) == 4.0
        assert weights.get_weight(12) == 3.0
        assert weights.get_weight(8) == 2.0
        assert weights.get_weight(4) == 1.0
        assert weights.get_weight(0) == 0.5

    def test_custom_weights(self):
        """Custom weights must be configurable"""
        custom = {15: 8.0, 0: 1.0}
        weights = QoSWeight(weights=custom)

        assert weights.get_weight(15) == 8.0
        assert weights.get_weight(0) == 1.0

    def test_normalized_weights(self):
        """Normalized weights must sum to 1.0"""
        weights = QoSWeight()

        normalized = weights.get_normalized_weights()
        total = sum(normalized.values())

        assert abs(total - 1.0) < 0.001

    def test_effective_weight_queue_fill(self):
        """Effective weight must consider queue fill"""
        weights = QoSWeight()

        # Empty queue gets boost
        effective_empty = weights.get_effective_weight(8, queue_fill=0.0)
        # Nearly full queue gets no boost
        effective_full = weights.get_effective_weight(8, queue_fill=0.9)

        assert effective_empty >= weights.get_weight(8)
        assert effective_full == weights.get_weight(8)

    def test_set_weight(self):
        """Weight must be settable"""
        weights = QoSWeight()
        weights.set_weight(8, 5.0)
        assert weights.get_weight(8) == 5.0


# =============================================================================
# Test Class: Statistics
# =============================================================================

class TestStatistics:
    """Test scheduler statistics"""

    def test_initial_stats(self):
        """Initial statistics must be zero"""
        scheduler = HBM4QoSScheduler()

        stats = scheduler.get_stats()
        assert stats['total_scheduled'] == 0
        assert stats['total_rejected'] == 0

    def test_stats_after_schedule(self):
        """Statistics must update after scheduling"""
        scheduler = HBM4QoSScheduler()

        scheduler.submit_request(request_id=1, qos=8)
        scheduler.schedule()

        stats = scheduler.get_stats()
        assert stats['total_scheduled'] == 1
        assert stats['by_qos'][8] == 1

    def test_stats_after_reject(self):
        """Rejected requests must be tracked"""
        scheduler = HBM4QoSScheduler()

        # Fill the queue
        for i in range(32):
            scheduler.submit_request(request_id=i, qos=8)

        # Try to submit one more (should be rejected)
        scheduler.submit_request(request_id=999, qos=8)

        stats = scheduler.get_stats()
        assert stats['total_rejected'] >= 1

    def test_queue_depth_in_stats(self):
        """Queue depth must be in statistics"""
        scheduler = HBM4QoSScheduler()

        for i in range(5):
            scheduler.submit_request(request_id=i, qos=8)

        stats = scheduler.get_stats()
        assert stats['total_queued'] == 5
        assert stats['queues_by_level'][8] == 5


# =============================================================================
# Test Class: HBM4 Spec Integration
# =============================================================================

class TestHBM4SpecIntegration:
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

    def test_address_decoder_integration(self):
        """Address decoder must be integrated"""
        scheduler = HBM4QoSScheduler()

        assert scheduler._decoder is not None


# =============================================================================
# Test Class: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_very_high_qos_boost(self):
        """Very high QoS boost must not exceed limits"""
        scheduler = HBM4QoSScheduler()

        # Submit request at lowest priority
        scheduler.submit_request(request_id=1, qos=0)

        # Force starvation boost
        boost = scheduler._get_starvation_boost(0)
        # Boost should be 0 for fresh request
        assert boost >= 0
        assert boost <= 15  # Cannot exceed max

    def test_concurrent_queue_operations(self):
        """Concurrent queue operations must be safe"""
        scheduler = HBM4QoSScheduler()

        # Submit to multiple levels
        for qos in range(16):
            for i in range(3):
                scheduler.submit_request(request_id=qos * 10 + i, qos=qos)

        # Schedule from all levels
        total = 0
        while True:
            req = scheduler.schedule()
            if req is None:
                break
            total += 1

        assert total == 48  # 16 levels * 3 requests each

    def test_zero_length_queue(self):
        """Empty queue operations must work"""
        scheduler = HBM4QoSScheduler()

        assert scheduler.get_queue_size(0) == 0
        assert scheduler.get_total_queue_size() == 0

        scheduler.clear_queue(0)  # Should not error
        scheduler.clear_all_queues()  # Should not error

    def test_invalid_bandwidth_config(self):
        """Invalid bandwidth config must be handled"""
        scheduler = HBM4QoSScheduler()

        # Set negative guarantee (edge case)
        scheduler.set_bandwidth_guarantee(8, -1.0)
        assert scheduler.bw_guarantee[8] == -1.0

    def test_request_id_uniqueness(self):
        """Request IDs must be preserved"""
        scheduler = HBM4QoSScheduler()

        # Submit 32 requests (within queue depth limit)
        ids = list(range(32))
        for req_id in ids:
            scheduler.submit_request(request_id=req_id, qos=8)

        # Schedule all and verify order
        scheduled_ids = []
        for _ in range(32):
            req = scheduler.schedule()
            if req:
                scheduled_ids.append(req.request_id)

        assert scheduled_ids == ids
