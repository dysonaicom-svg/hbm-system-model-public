"""
Tests for HBM4 FR-FCFS Scheduler

Tests the enhanced FR-FCFS scheduler with:
- 16 QoS priority classes
- Row hit detection
- Bank conflict awareness
- 32-channel HBM4 support
"""

import pytest
from typing import Dict, Tuple

from model.controller.scheduler import (
    FRFCFSScheduler,
    BatchScheduler,
    BankState,
    BankConflictTracker,
    SchedulerStats,
    QoSLevel,
    create_hbm4_scheduler,
    HBMRequest,
    RequestState,
)
from model.controller.config import HBM4_DEFAULT, HBMConfig
from model.controller.queue import ReadQueue, WriteQueue


class TestBankState:
    """Tests for BankState"""
    
    def test_bank_state_init(self):
        """Bank state initializes correctly"""
        bank = BankState(bank_id=5, rank_id=0)
        
        assert bank.bank_id == 5
        assert bank.rank_id == 0
        assert not bank.is_open
        assert bank.open_row == -1
    
    def test_bank_activate(self):
        """Bank activation opens row"""
        bank = BankState(bank_id=0)
        bank.activate(row_id=100, current_time=10.0)
        
        assert bank.is_open
        assert bank.open_row == 100
        assert bank.last_access_time == 10.0
        assert bank.last_command == 'ACT'
    
    def test_bank_precharge(self):
        """Bank precharge closes row"""
        bank = BankState(bank_id=0)
        bank.activate(row_id=100, current_time=10.0)
        bank.precharge(current_time=20.0)

        assert not bank.is_open
        assert bank.last_row == 100  # last_row preserved for row-hit detection
        assert bank.last_command == 'PRE'


class TestBankConflictTracker:
    """Tests for BankConflictTracker"""
    
    def test_conflict_tracker_init(self):
        """Conflict tracker initializes with correct bank groups"""
        tracker = BankConflictTracker(num_bank_groups=8, num_banks_per_group=16)
        
        assert len(tracker.bank_groups) == 8
        for bg_id, bg in tracker.bank_groups.items():
            assert len(bg.banks) == 16
    
    def test_record_command(self):
        """Commands are recorded correctly"""
        tracker = BankConflictTracker()
        tracker.record_command(
            bank_group_id=3, bank_id=7,
            current_time=100.0, command='ACT'
        )
        
        bg = tracker.bank_groups[3]
        assert bg.last_command_time == 100.0
        assert bg.last_bank_activated == 7
    
    def test_conflict_detection(self):
        """Conflicts are detected correctly"""
        tracker = BankConflictTracker()
        
        # Record a command
        tracker.record_command(
            bank_group_id=3, bank_id=7,
            current_time=100.0, command='ACT'
        )
        
        # Same bank group, different bank - should conflict
        assert tracker.has_conflict(3, 5, current_time=101.0, tCCD=4.0)
        
        # Different bank group - no conflict
        assert not tracker.has_conflict(1, 5, current_time=101.0, tCCD=4.0)
        
        # Same bank group but after tCCD elapsed - no conflict
        assert not tracker.has_conflict(3, 5, current_time=110.0, tCCD=4.0)


class TestSchedulerStats:
    """Tests for SchedulerStats"""
    
    def test_stats_init(self):
        """Statistics initialize to zero"""
        stats = SchedulerStats()
        
        assert stats.schedule_count == 0
        assert stats.row_hit_count == 0
        assert stats.row_hit_rate == 0.0
    
    def test_record_schedule(self):
        """Scheduling events are recorded correctly"""
        stats = SchedulerStats()
        
        # Create a mock request
        req = HBMRequest(
            addr=0x1000, length=64, is_read=True, qos=8,
            row_hit=True, request_id=1
        )
        
        stats.record_schedule(req, row_hit=True, qos=8, is_read=True)
        
        assert stats.schedule_count == 1
        assert stats.row_hit_count == 1
        assert stats.row_hit_rate == 1.0
        assert stats.read_count == 1
    
    def test_qos_distribution(self):
        """QoS distribution is tracked"""
        stats = SchedulerStats()
        
        # Record requests at different QoS levels
        for qos in [15, 12, 8, 8, 4]:
            req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=qos)
            stats.record_schedule(req, qos=qos, is_read=True)
        
        assert stats.qos_distribution[15] == 1
        assert stats.qos_distribution[8] == 2


class TestFRFCFSSchedulerInit:
    """Tests for FR-FCFS scheduler initialization"""
    
    def test_scheduler_init_default(self):
        """Scheduler initializes with default config"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT)
        
        assert scheduler.config is not None
        assert scheduler.QOS_LEVELS == 16
        assert scheduler._qos_enabled
        assert scheduler.stats.schedule_count == 0
    
    def test_scheduler_init_hbm4(self):
        """Scheduler initializes correctly with HBM4 config"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT, qos_enabled=True)
        
        assert scheduler._qos_enabled
        assert scheduler.QOS_CRITICAL == 15
        assert scheduler.QOS_IDLE == 0
    
    def test_create_hbm4_scheduler(self):
        """Utility function creates HBM4 scheduler"""
        scheduler = create_hbm4_scheduler()
        
        assert isinstance(scheduler, FRFCFSScheduler)
        assert scheduler.config.channels_per_stack == 32


class TestFRFCFSSchedulerRowHit:
    """Tests for row hit detection"""
    
    def test_row_hit_detection(self):
        """Row hits are detected correctly"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT)
        
        # Create bank state with open row
        bank_states: Dict[Tuple, BankState] = {}
        bank_states[(0, 0, 5)] = BankState(bank_id=5)
        bank_states[(0, 0, 5)].activate(row_id=100, current_time=0.0)
        
        # Create request targeting same row
        req1 = HBMRequest(
            addr=0x1000, length=64, is_read=True, 
            channel_id=0, pseudo_channel_id=0, bank_id=5, row_id=100
        )
        
        # Create request targeting different row
        req2 = HBMRequest(
            addr=0x2000, length=64, is_read=True,
            channel_id=0, pseudo_channel_id=0, bank_id=5, row_id=200
        )
        
        # Get candidates
        queue = ReadQueue(max_depth=32)
        queue.push(req1)
        queue.push(req2)
        
        candidates = scheduler._get_row_hit_candidates_fast(queue, bank_states)
        
        # Only req1 should be in candidates (row hit)
        assert len(candidates) == 1
        assert candidates[0].request_id == req1.request_id
    
    def test_row_hit_prioritized(self):
        """Row hit requests are prioritized"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT)
        
        bank_states: Dict[Tuple, BankState] = {}
        bank_states[(0, 0, 5)] = BankState(bank_id=5)
        bank_states[(0, 0, 5)].activate(row_id=100, current_time=0.0)
        
        # Create requests
        req1 = HBMRequest(  # Row miss, arrives first
            addr=0x1000, length=64, is_read=True,
            channel_id=0, pseudo_channel_id=0, bank_id=5, row_id=200,
            arrival_time=0.0, request_id=1
        )
        req2 = HBMRequest(  # Row hit, arrives second
            addr=0x2000, length=64, is_read=True,
            channel_id=0, pseudo_channel_id=0, bank_id=5, row_id=100,
            arrival_time=1.0, request_id=2
        )
        
        read_queue = ReadQueue(max_depth=32)
        read_queue.push(req1)
        read_queue.push(req2)
        
        scheduled = scheduler.schedule(
            read_queue, WriteQueue(32),
            bank_states, current_time=2.0
        )
        
        # Row hit should be scheduled first
        assert scheduled is not None
        assert scheduled.request_id == req2.request_id


class TestFRFCFSSchedulerQoS:
    """Tests for 16-level QoS scheduling"""
    
    def test_qos_levels_defined(self):
        """All QoS levels are properly defined"""
        assert QoSLevel.CRITICAL == 15
        assert QoSLevel.HIGH == 12
        assert QoSLevel.NORMAL == 8
        assert QoSLevel.LOW == 4
        assert QoSLevel.IDLE == 0
    
    def test_qos_priority_order(self):
        """Higher QoS requests are scheduled first"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT, qos_enabled=True)
        
        bank_states: Dict[Tuple, BankState] = {}
        
        # Create requests at different QoS levels
        req_low = HBMRequest(
            addr=0x1000, length=64, is_read=True, qos=4,
            channel_id=0, pseudo_channel_id=0, bank_id=0, row_id=100,
            arrival_time=0.0, request_id=1
        )
        req_high = HBMRequest(
            addr=0x2000, length=64, is_read=True, qos=15,
            channel_id=0, pseudo_channel_id=0, bank_id=1, row_id=100,
            arrival_time=0.5, request_id=2
        )
        req_critical = HBMRequest(
            addr=0x3000, length=64, is_read=True, qos=15,
            channel_id=0, pseudo_channel_id=0, bank_id=2, row_id=100,
            arrival_time=0.3, request_id=3
        )
        
        read_queue = ReadQueue(max_depth=32)
        read_queue.push(req_low)   # Earliest arrival
        read_queue.push(req_high) # Later arrival, high priority
        read_queue.push(req_critical)  # Middle arrival, critical priority
        
        scheduled = scheduler.schedule(
            read_queue, WriteQueue(32),
            bank_states, current_time=1.0
        )
        
        # Critical (15) should be first despite middle arrival time
        assert scheduled.request_id == req_critical.request_id
        
        # Schedule next
        scheduled2 = scheduler.schedule(
            read_queue, WriteQueue(32),
            bank_states, current_time=2.0
        )
        
        # High (15) should be second
        assert scheduled2.request_id == req_high.request_id
    
    def test_qos_within_same_priority_fcfs(self):
        """Within same QoS level, FCFS ordering applies"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT, qos_enabled=True)
        
        bank_states: Dict[Tuple, BankState] = {}
        
        # All same QoS level
        req1 = HBMRequest(
            addr=0x1000, length=64, is_read=True, qos=8,
            arrival_time=0.0, request_id=1
        )
        req2 = HBMRequest(
            addr=0x2000, length=64, is_read=True, qos=8,
            arrival_time=1.0, request_id=2
        )
        req3 = HBMRequest(
            addr=0x3000, length=64, is_read=True, qos=8,
            arrival_time=2.0, request_id=3
        )
        
        read_queue = ReadQueue(max_depth=32)
        read_queue.push(req1)
        read_queue.push(req2)
        read_queue.push(req3)
        
        # Schedule 3 requests
        for expected_id in [1, 2, 3]:
            scheduled = scheduler.schedule(
                read_queue, WriteQueue(32),
                bank_states, current_time=float(expected_id + 1)
            )
            assert scheduled.request_id == expected_id


class TestFRFCFSSchedulerBankConflict:
    """Tests for bank conflict awareness"""
    
    def test_bank_conflict_tracking(self):
        """Bank conflicts are tracked and avoided"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT)
        
        # Check no initial conflicts
        assert not scheduler.check_bank_conflict(
            HBMRequest(addr=0x1000, length=64, is_read=True,
                      bank_group_id=3, bank_id=5),
            current_time=100.0
        )
        
        # Schedule a request to create conflict
        bank_states: Dict[Tuple, BankState] = {}
        req = HBMRequest(
            addr=0x1000, length=64, is_read=True,
            channel_id=0, pseudo_channel_id=0, bank_id=5,
            bank_group_id=3, row_id=100,
            arrival_time=0.0, request_id=1
        )
        
        read_queue = ReadQueue(max_depth=32)
        read_queue.push(req)
        
        scheduler.schedule(
            read_queue, WriteQueue(32),
            bank_states, current_time=100.0
        )
        
        # Now there should be a conflict
        assert scheduler.check_bank_conflict(
            HBMRequest(addr=0x2000, length=64, is_read=True,
                      bank_group_id=3, bank_id=5),
            current_time=101.0, tCCD=4.0
        )


class TestFRFCFSSchedulerArbitration:
    """Tests for read/write arbitration"""
    
    def test_read_write_turnaround(self):
        """Read/write turnaround penalty is applied"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT)
        
        bank_states: Dict[Tuple, BankState] = {}
        
        read_queue = ReadQueue(max_depth=32)
        write_queue = WriteQueue(max_depth=32)
        
        read_req = HBMRequest(
            addr=0x1000, length=64, is_read=True,
            arrival_time=0.0, request_id=1
        )
        write_req = HBMRequest(
            addr=0x2000, length=64, is_read=False,
            arrival_time=0.1, request_id=2
        )
        
        read_queue.push(read_req)
        write_queue.push(write_req)
        
        # After read, write should be penalized
        scheduled = scheduler.schedule(
            read_queue, write_queue,
            bank_states, current_time=1.0, last_cmd_type="READ"
        )
        
        # Read arrives first, should be scheduled
        assert scheduled.is_read


class TestFRFCFSSchedulerStatistics:
    """Tests for scheduler statistics"""
    
    def test_statistics_tracked(self):
        """Scheduling statistics are tracked"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT)
        
        bank_states: Dict[Tuple, BankState] = {}
        
        read_queue = ReadQueue(max_depth=32)
        
        for i in range(5):
            req = HBMRequest(
                addr=0x1000 + i * 0x100, length=64, is_read=True,
                arrival_time=float(i), request_id=i
            )
            read_queue.push(req)
        
        for _ in range(5):
            scheduler.schedule(
                read_queue, WriteQueue(32),
                bank_states, current_time=float(_ + 10)
            )
        
        stats = scheduler.get_stats()
        assert stats['schedule_count'] == 5
        assert stats['read_count'] == 5


class TestBatchScheduler:
    """Tests for BatchScheduler"""
    
    def test_batch_scheduler_init(self):
        """Batch scheduler initializes correctly"""
        batch_scheduler = BatchScheduler(HBM4_DEFAULT)
        
        assert batch_scheduler._scheduler is not None
        assert batch_scheduler.batch_config.batch_size == 32
    
    def test_schedule_batch(self):
        """Batch scheduling works"""
        batch_scheduler = BatchScheduler(HBM4_DEFAULT)
        
        bank_states: Dict[Tuple, BankState] = {}
        read_queue = ReadQueue(max_depth=64)
        write_queue = WriteQueue(max_depth=64)
        
        for i in range(10):
            req = HBMRequest(
                addr=0x1000 + i * 0x100, length=64, is_read=True,
                arrival_time=float(i), request_id=i
            )
            read_queue.push(req)
        
        scheduled = batch_scheduler.schedule_batch(
            read_queue, write_queue,
            bank_states, current_time=10.0
        )
        
        assert len(scheduled) == 10


# Test fixtures
@pytest.fixture
def hbm4_scheduler():
    """Create HBM4 scheduler for tests"""
    return FRFCFSScheduler(HBM4_DEFAULT, qos_enabled=True)


@pytest.fixture
def bank_states():
    """Create bank states for tests"""
    states: Dict[Tuple, BankState] = {}
    for ch in range(2):
        for pch in range(2):
            for bank in range(4):
                key = (ch, pch, bank)
                states[key] = BankState(bank_id=bank)
                # Open some rows
                if bank % 2 == 0:
                    states[key].activate(row_id=bank * 100, current_time=0.0)
    return states


@pytest.fixture
def queues_with_requests():
    """Create queues with test requests"""
    read_queue = ReadQueue(max_depth=32)
    write_queue = WriteQueue(max_depth=32)
    
    # Add read requests
    for i in range(5):
        req = HBMRequest(
            addr=0x1000 + i * 0x100, length=64, is_read=True,
            qos=8, arrival_time=float(i), request_id=i,
            channel_id=0, pseudo_channel_id=0, bank_id=i % 4, row_id=i * 100
        )
        read_queue.push(req)
    
    # Add write requests
    for i in range(3):
        req = HBMRequest(
            addr=0x2000 + i * 0x100, length=64, is_read=False,
            qos=8, arrival_time=float(i + 10), request_id=i + 10,
            channel_id=0, pseudo_channel_id=0, bank_id=(i + 2) % 4, row_id=i * 100
        )
        write_queue.push(req)
    
    return read_queue, write_queue


class TestIntegration:
    """Integration tests for full scheduler workflow"""
    
    def test_full_scheduling_workflow(self, hbm4_scheduler, bank_states, queues_with_requests):
        """Test complete scheduling workflow"""
        read_queue, write_queue = queues_with_requests
        
        scheduled_requests = []
        
        # Schedule up to 8 requests
        for t in range(8):
            req = hbm4_scheduler.schedule(
                read_queue, write_queue,
                bank_states, current_time=float(t + 100)
            )
            if req:
                scheduled_requests.append(req)
        
        assert len(scheduled_requests) > 0
        
        # Verify stats are tracked
        stats = hbm4_scheduler.get_stats()
        assert stats['schedule_count'] == len(scheduled_requests)
    
    def test_qos_starvation_prevention(self):
        """Low priority requests not starved"""
        scheduler = FRFCFSScheduler(HBM4_DEFAULT, qos_enabled=True)
        bank_states: Dict[Tuple, BankState] = {}
        
        # Submit many high priority requests
        read_queue = ReadQueue(max_depth=64)
        for i in range(20):
            req = HBMRequest(
                addr=0x1000 + i * 0x100, length=64, is_read=True,
                qos=15, arrival_time=float(i), request_id=i
            )
            read_queue.push(req)
        
        # Submit one low priority request
        low_req = HBMRequest(
            addr=0x8000, length=64, is_read=True,
            qos=0, arrival_time=0.0, request_id=100
        )
        read_queue.push(low_req)
        
        # Schedule all requests
        scheduled_ids = []
        current_time = 100.0
        while not read_queue.is_empty():
            req = scheduler.schedule(
                read_queue, WriteQueue(64),
                bank_states, current_time=current_time
            )
            if req:
                scheduled_ids.append(req.request_id)
                current_time += 1.0
            else:
                break
        
        # Low priority should eventually be scheduled
        assert 100 in scheduled_ids


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
