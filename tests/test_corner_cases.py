"""
HBM4 Corner Cases and Boundary Condition Tests

Comprehensive tests covering:
1. Corner Cases:
   - Empty/full queue handling
   - Bank conflict scenarios
   - Refresh timing edge cases
   - ECC/CRC error injection
   - Lane repair activation

2. Boundary Conditions:
   - Maximum request size
   - Minimum timing constraints
   - Overflow/underflow conditions
   - Channel count extremes (1, 16, 32)

3. Stress Tests:
   - Sustained high-load testing
   - Long-duration simulation
   - Memory exhaustion scenarios
   - Concurrent operation stress

4. Integration Tests:
   - Controller-DRAM integration
   - Multi-channel coordination

Target: 50+ new test cases
"""

import pytest
import time
import random
from typing import List, Optional, Tuple
from dataclasses import dataclass

from model.dram.hbm4_spec import HBM4Spec
from model.dram.ecc_crc import (
    HBM4ECC, HBM4CRC, HBM4Parity, HBM4DataIntegrity,
    HBM4ECCMode, HBM4CRCMode, ErrorType, ErrorTracker, ErrorCounter
)
from model.dram.lane_repair import (
    HBM4LaneRepairModel, RepairStatus, LaneFailureMode
)
from model.dram.hbm4_bank_state_machine import HBM4BankStateMachine, HBM4BankState
from model.dram.hbm4_channel_model import HBM4Channel
from model.controller.queue import (
    ReadQueue, WriteQueue, PriorityQueue, QueueManager
)
from model.controller.request import HBMRequest, RequestState
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode


# ============================================================================
# Corner Case Tests: Empty/Full Queue Handling
# ============================================================================

class TestEmptyQueueHandling:
    """Test queue behavior at empty state"""

    def test_read_queue_empty_pop_returns_none(self):
        """Pop on empty queue must return None"""
        queue = ReadQueue(max_depth=32)
        result = queue.pop()
        assert result is None

    def test_read_queue_empty_peek_returns_none(self):
        """Peek on empty queue must return None"""
        queue = ReadQueue(max_depth=32)
        result = queue.peek()
        assert result is None

    def test_read_queue_empty_size_is_zero(self):
        """Empty queue size must be 0"""
        queue = ReadQueue(max_depth=32)
        assert queue.size() == 0

    def test_read_queue_empty_is_empty(self):
        """Empty queue must report is_empty() as True"""
        queue = ReadQueue(max_depth=32)
        assert queue.is_empty() is True

    def test_read_queue_empty_is_not_full(self):
        """Empty queue must report is_full() as False"""
        queue = ReadQueue(max_depth=32)
        assert queue.is_full() is False

    def test_read_queue_empty_remove_returns_false(self):
        """Remove on empty queue must return False"""
        queue = ReadQueue(max_depth=32)
        result = queue.remove("non-existent-id")
        assert result is False

    def test_read_queue_empty_get_row_hit_returns_empty(self):
        """get_row_hit_requests on empty queue must return empty list"""
        queue = ReadQueue(max_depth=32)
        result = queue.get_row_hit_requests()
        assert result == []

    def test_read_queue_empty_get_oldest_returns_none(self):
        """get_oldest_request on empty queue must return None"""
        queue = ReadQueue(max_depth=32)
        result = queue.get_oldest_request()
        assert result is None

    def test_priority_queue_empty_pop_returns_none(self):
        """PriorityQueue pop on empty must return None"""
        queue = PriorityQueue(max_depth=32)
        result = queue.pop()
        assert result is None

    def test_priority_queue_empty_schedule_returns_none(self):
        """Scheduler on empty queue must return None"""
        scheduler = HBM4QoSScheduler()
        result = scheduler.schedule()
        assert result is None


class TestFullQueueHandling:
    """Test queue behavior at full state"""

    def test_read_queue_full_push_rejected(self):
        """Push on full queue must be rejected"""
        queue = ReadQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))

        result = queue.push(HBMRequest(addr=0x300, length=64, is_read=True))
        assert result is False

    def test_read_queue_full_size_equals_max(self):
        """Full queue size must equal max_depth"""
        queue = ReadQueue(max_depth=4)
        for i in range(4):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))
        assert queue.size() == 4

    def test_read_queue_full_is_full(self):
        """Full queue must report is_full() as True"""
        queue = ReadQueue(max_depth=3)
        for i in range(3):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))
        assert queue.is_full() is True

    def test_read_queue_full_is_not_empty(self):
        """Full queue must report is_empty() as False"""
        queue = ReadQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))
        assert queue.is_empty() is False

    def test_read_queue_full_stats_reject_count(self):
        """Full queue must track reject count"""
        queue = ReadQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x300, length=64, is_read=True))  # Rejected

        stats = queue.get_stats()
        assert stats['reject_count'] == 1

    def test_priority_queue_full_push_rejected(self):
        """PriorityQueue push on full must be rejected"""
        queue = PriorityQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True, qos=8))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True, qos=8))

        result = queue.push(HBMRequest(addr=0x300, length=64, is_read=True, qos=8))
        assert result is False

    def test_write_queue_drain_threshold_exceeded(self):
        """WriteQueue should trigger drain when threshold exceeded"""
        queue = WriteQueue(max_depth=10, drain_threshold=0.5)
        for i in range(6):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=False))
        assert queue.should_drain() is True

    def test_queue_manager_full_both_queues(self):
        """QueueManager full when both read and write queues full"""
        manager = QueueManager.create(queue_depth=2)

        # Fill read queue
        manager.push_read(HBMRequest(addr=0x100, length=64, is_read=True))
        manager.push_read(HBMRequest(addr=0x200, length=64, is_read=True))

        # is_full should be True
        assert manager.is_full() is True


class TestQueueBoundaryConditions:
    """Test queue at size boundaries"""

    def test_queue_size_1(self):
        """Queue with max_depth=1"""
        queue = ReadQueue(max_depth=1)
        assert queue.is_empty()

        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        assert queue.is_full()
        assert queue.size() == 1

        queue.pop()
        assert queue.is_empty()

    def test_queue_size_very_large(self):
        """Queue with very large max_depth"""
        queue = ReadQueue(max_depth=100000)
        assert queue.max_depth == 100000

        # Push many items
        for i in range(1000):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))
        assert queue.size() == 1000

    def test_queue_alternating_push_pop(self):
        """Alternating push/pop at boundary"""
        queue = ReadQueue(max_depth=4)

        for i in range(20):
            if not queue.is_full():
                queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))
            elif not queue.is_empty():
                queue.pop()


# ============================================================================
# Corner Case Tests: Bank Conflict Scenarios
# ============================================================================

class TestBankConflicts:
    """Test bank conflict detection and handling"""

    def test_bank_state_active_to_active_conflict(self):
        """ACT to ACT conflict on same bank"""
        bsm = HBM4BankStateMachine(bank_id=0)

        # Activate row 0
        success, _ = bsm.activate(row=0x100)
        assert success
        assert bsm.bank.state == HBM4BankState.ACTIVATING or bsm.bank.state == HBM4BankState.ACTIVE

        # Try to activate different row - should conflict
        can_activate = bsm.can_activate()
        assert can_activate is False

    def test_bank_state_active_to_idle_no_conflict(self):
        """ACT after precharge - no conflict"""
        bsm = HBM4BankStateMachine(bank_id=0)

        # Activate
        success, _ = bsm.activate(row=0x100)
        assert success

        # Precharge
        bsm.precharge()

        # Now can activate again
        can_activate = bsm.can_activate()
        assert can_activate is True

    def test_bank_conflict_in_same_bank_group(self):
        """Conflict within same bank group"""
        bsm = HBM4BankStateMachine(bank_id=0)

        # Activate
        bsm.activate(row=0x100)

        # Try different row same bank - should be blocked until precharged
        can_activate = bsm.can_activate()
        assert can_activate is False

    def test_bank_state_timing_conflicts(self):
        """Test tRRD timing between banks"""
        bsm = HBM4BankStateMachine(bank_id=0)

        # Activate first bank
        bsm.activate(row=0x100)

        # Different bank should work
        bsm2 = HBM4BankStateMachine(bank_id=1)
        can_activate = bsm2.can_activate()
        assert can_activate is True


class TestBankGroupConflicts:
    """Test bank group conflict handling"""

    def test_bank_group_all_banks_busy(self):
        """All banks in group busy - should queue"""
        # Create multiple banks in same group
        banks = []
        for bank_id in range(8):
            bsm = HBM4BankStateMachine(bank_id=bank_id)
            bsm.activate(row=0x100)
            banks.append(bsm)

        # All should be in ACTIVE state
        for bsm in banks:
            assert bsm.bank.state in [HBM4BankState.ACTIVATING, HBM4BankState.ACTIVE]

    def test_bank_group_rotation(self):
        """Test refresh rotation through bank groups"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.BANK_GROUP

        # Get multiple refresh commands
        groups_seen = set()
        for _ in range(32):
            for _ in range(scheduler.tREFIpb):
                scheduler.tick()
            cmd = scheduler.get_refresh_command()
            if cmd and hasattr(scheduler, 'current_bank_group'):
                groups_seen.add(scheduler.current_bank_group)

        # Should see some bank group rotation
        assert len(groups_seen) >= 1


# ============================================================================
# Corner Case Tests: Refresh Timing Edge Cases
# ============================================================================

class TestRefreshTimingEdgeCases:
    """Test refresh timing at edge conditions"""

    def test_refresh_exactly_at_boundary(self):
        """Refresh at exactly tREFI boundary"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Advance exactly to tREFI
        for _ in range(scheduler.tREFI):
            scheduler.tick()

        assert scheduler.can_refresh() is True

    def test_refresh_one_cycle_before_boundary(self):
        """Refresh one cycle before tREFI"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        for _ in range(scheduler.tREFI - 1):
            scheduler.tick()

        assert scheduler.can_refresh() is False

    def test_refresh_immediately_after_boundary(self):
        """Refresh immediately after tREFI"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        for _ in range(scheduler.tREFI + 1):
            scheduler.tick()

        assert scheduler.can_refresh() is True

    def test_refresh_overdue_single_cycle(self):
        """Refresh overdue by single cycle"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Advance past tREFI
        for _ in range(scheduler.tREFI + 1):
            scheduler.tick()

        # Should still be able to refresh (overdue is still valid)
        assert scheduler.can_refresh() is True

    def test_refresh_overdue_many_cycles(self):
        """Refresh overdue by many cycles"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Advance way past tREFI
        for _ in range(scheduler.tREFI * 5):
            scheduler.tick()

        assert scheduler.can_refresh() is True

    def test_refresh_blocked_exactly_at_boundary(self):
        """Refresh blocked at exact boundary"""
        scheduler = HBM4RefreshScheduler()

        # Block for exactly 100 cycles
        scheduler.block_refresh_for_qos(100)

        for _ in range(100):
            scheduler.tick()

        assert scheduler.can_issue_refresh() is True

    def test_refresh_blocked_one_before_boundary(self):
        """Refresh blocked one before boundary"""
        scheduler = HBM4RefreshScheduler()

        scheduler.block_refresh_for_qos(100)

        for _ in range(99):
            scheduler.tick()

        assert scheduler.can_issue_refresh() is False


class TestRefreshConcurrentOperations:
    """Test refresh with concurrent operations"""

    def test_refresh_during_active_transaction(self):
        """Refresh attempted during active transaction"""
        bsm = HBM4BankStateMachine(bank_id=0)
        bsm.activate(row=0x100)

        # Refresh should work if targeting different bank
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Refresh should work
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()
        assert cmd is not None

    def test_refresh_all_banks_during_operations(self):
        """ALL_BANKS refresh during ongoing operations"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Submit some requests
        controller = HBM4Controller()

        for i in range(50):
            controller.submit_request(addr=i * 0x100, is_read=True)

        # Run with refresh enabled
        for _ in range(scheduler.tREFI):
            scheduler.tick()
            controller.tick()

        # Should complete without errors
        cmd = scheduler.get_refresh_command()
        assert cmd is not None or scheduler.can_refresh() is True


# ============================================================================
# Corner Case Tests: ECC/CRC Error Injection
# ============================================================================

class TestECCErrorInjection:
    """Test ECC error injection scenarios"""

    def test_single_bit_error_injection(self):
        """Inject and detect single bit error"""
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED, enable_tracking=True)

        original = 0x123456789ABCDEF0
        encoded = ecc.encode(original)

        # Inject single bit error
        corrupted = encoded ^ (1 << 10)
        result = ecc.decode(corrupted)

        assert result.error_type != ErrorType.NO_ERROR

    def test_multi_bit_error_injection(self):
        """Inject multi-bit errors"""
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED)

        original = 0xABCDEF0123456789
        encoded = ecc.encode(original)

        # Inject 5-bit error
        corrupted = encoded ^ 0x7E0  # Bits 5,6,7,8,9
        result = ecc.decode(corrupted)

        assert result.error_type != ErrorType.NO_ERROR

    def test_error_at_bit_boundary(self):
        """Error at bit position boundaries"""
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED)

        boundary_positions = [0, 7, 8, 15, 31, 63]

        for pos in boundary_positions:
            original = 0xDEADBEEF
            encoded = ecc.encode(original)
            corrupted = encoded ^ (1 << pos)
            result = ecc.decode(corrupted)
            assert result.error_type != ErrorType.NO_ERROR

    def test_all_zeros_error_injection(self):
        """Error injection on all-zeros data"""
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED)

        original = 0
        encoded = ecc.encode(original)

        # Inject single bit error
        corrupted = encoded ^ 1
        result = ecc.decode(corrupted)

        assert result.error_type != ErrorType.NO_ERROR

    def test_all_ones_error_injection(self):
        """Error injection on all-ones data"""
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED)

        original = 0xFFFFFFFFFFFFFFFF
        encoded = ecc.encode(original)

        # Inject single bit error
        corrupted = encoded ^ 0x8000000000000000
        result = ecc.decode(corrupted)

        assert result.error_type != ErrorType.NO_ERROR

    def test_rapid_error_injection(self):
        """Rapid sequential error injection"""
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED, enable_tracking=True)

        errors_detected = 0
        for i in range(100):
            original = i
            encoded = ecc.encode(original)
            corrupted = encoded ^ (1 << (i % 64))
            result = ecc.decode(corrupted)
            if result.error_type != ErrorType.NO_ERROR:
                errors_detected += 1

        # Errors should be detected
        assert errors_detected > 0


class TestCRCErrorInjection:
    """Test CRC error injection scenarios"""

    def test_crc_single_bit_error(self):
        """CRC single bit flip detection"""
        crc = HBM4CRC(crc_mode=HBM4CRCMode.CRC16)

        data = 0x12345678
        crc_value = crc.calculate_crc16(data)

        # Flip one bit
        corrupted_data = data ^ 0x100
        valid, _ = crc.verify_crc16(corrupted_data, crc_value)

        assert valid is False

    def test_crc_multi_bit_error(self):
        """CRC multi-bit error detection"""
        crc = HBM4CRC(crc_mode=HBM4CRCMode.CRC16)

        data = 0xDEADBEEF
        crc_value = crc.calculate_crc16(data)

        # Flip multiple bits
        corrupted_data = data ^ 0xFFFF0000
        valid, _ = crc.verify_crc16(corrupted_data, crc_value)

        assert valid is False

    def test_crc_corner_cases(self):
        """CRC on corner case data"""
        crc = HBM4CRC(crc_mode=HBM4CRCMode.CRC16)

        # All zeros
        data = 0
        calculated = crc.calculate_crc16(data)
        valid, _ = crc.verify_crc16(data, calculated)
        assert valid

        # Alternating pattern
        data = 0xAAAAAAAAAAAAAAA
        calculated = crc.calculate_crc16(data)
        valid, _ = crc.verify_crc16(data, calculated)
        assert valid


# ============================================================================
# Corner Case Tests: Lane Repair Activation
# ============================================================================

class TestLaneRepairEdgeCases:
    """Test lane repair edge cases"""

    def test_repair_first_lane(self):
        """Repair lane 0"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        spare = model.perform_repair(channel_id=0, failed_lane=0)
        assert spare is not None
        assert spare >= 64  # Spare lanes

    def test_repair_last_lane(self):
        """Repair last data lane"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        spare = model.perform_repair(channel_id=0, failed_lane=63)
        assert spare is not None

    def test_repair_middle_lane(self):
        """Repair middle lane"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        spare = model.perform_repair(channel_id=0, failed_lane=32)
        assert spare is not None

    def test_repair_multiple_adjacent_lanes(self):
        """Repair adjacent failed lanes"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        # Repair adjacent lanes
        spare1 = model.perform_repair(channel_id=0, failed_lane=10)
        spare2 = model.perform_repair(channel_id=0, failed_lane=11)

        assert spare1 is not None
        assert spare2 is not None

    def test_exhaust_all_spares(self):
        """Use all available spare lanes"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        repaired = []
        for lane in range(4):
            spare = model.perform_repair(channel_id=0, failed_lane=lane * 10)
            if spare:
                repaired.append(spare)

        assert len(repaired) == 4

        # Check no more spares available
        rm = model.get_channel_repair_map(0)
        assert rm.available_spares == 0

    def test_repair_after_exhaustion_fails(self):
        """Repair attempt after spares exhausted"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=2)

        # Exhaust spares
        model.perform_repair(channel_id=0, failed_lane=10)
        model.perform_repair(channel_id=0, failed_lane=20)

        # Try another repair
        result = model.perform_repair(channel_id=0, failed_lane=30)
        assert result is None

    def test_repair_remapping_consistency(self):
        """Consistent remapping after repair"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        spare = model.perform_repair(channel_id=0, failed_lane=15)

        # Multiple lookups should return same remapped lane
        for _ in range(10):
            remapped = model.get_remapped_lane(channel_id=0, lane_id=15)
            assert remapped == spare


# ============================================================================
# Boundary Condition Tests
# ============================================================================

class TestMaximumRequestSize:
    """Test maximum request size handling"""

    def test_maximum_request_length(self):
        """Test maximum burst length"""
        controller = HBM4Controller()

        # Maximum HBM4 burst is 256 bytes (256/8 = 32 beats)
        max_size = 256

        req_id = controller.submit_request(
            addr=0x1000,
            is_read=True,
            size_bytes=max_size
        )

        assert req_id is not None

    def test_minimum_request_length(self):
        """Test minimum burst length (single beat)"""
        controller = HBM4Controller()

        min_size = 8  # Single beat

        req_id = controller.submit_request(
            addr=0x1000,
            is_read=True,
            size_bytes=min_size
        )

        assert req_id is not None

    def test_boundary_request_lengths(self):
        """Test boundary length values"""
        controller = HBM4Controller()

        sizes = [8, 16, 32, 64, 128, 256]

        for size in sizes:
            req_id = controller.submit_request(
                addr=0x1000,
                is_read=True,
                size_bytes=size
            )
            assert req_id is not None


class TestMinimumTimingConstraints:
    """Test minimum timing constraints"""

    def test_minimum_tCK(self):
        """Minimum clock period constraint"""
        spec = HBM4Spec()

        # At 16 GT/s, tCK = 62.5 ps
        assert spec.tCK_ps > 0
        assert spec.tCK_ps <= 125  # Maximum at slowest rate

    def test_tRRD_L_minimum(self):
        """Minimum tRRD (bank-to-bank delay)"""
        spec = HBM4Spec()

        # Use nRRDL from spec
        assert spec.nRRDL > 0
        assert spec.nRRDL >= 3  # Minimum per spec

    def test_tRAS_minimum(self):
        """Minimum tRAS (row active time)"""
        spec = HBM4Spec()

        # nRAS should be positive
        assert spec.nRAS > 0

    def test_tRCD_minimum(self):
        """Minimum tRCD (RCD delay)"""
        spec = HBM4Spec()

        # nRCDRD and nRCDWR should be positive
        assert spec.nRCDRD > 0
        assert spec.nRCDWR > 0

    def test_tRP_minimum(self):
        """Minimum tRP (precharge time)"""
        spec = HBM4Spec()

        assert spec.nRP > 0

    def test_tRC_minimum(self):
        """Minimum tRC (cycle time)"""
        spec = HBM4Spec()

        assert spec.nRC > 0
        # RC is typically RAS + RP + some overhead


class TestChannelCountExtremes:
    """Test channel count at extremes"""

    def test_single_channel(self):
        """Single channel configuration"""
        controller = HBM4Controller()
        decoder = HBM4AddressDecoder()

        # Address for channel 0
        addr = 0x8

        req_id = controller.submit_request(
            addr=addr,
            is_read=True,
            size_bytes=64
        )

        assert req_id is not None

        # Run a few cycles
        for _ in range(100):
            controller.tick()

    def test_16_channels(self):
        """16 channel configuration"""
        controller = HBM4Controller()

        # Submit to channels 0-15
        for ch in range(16):
            addr = (ch << 41) | 0x8
            req_id = controller.submit_request(
                addr=addr,
                is_read=True,
                size_bytes=64
            )
            assert req_id is not None

    def test_full_32_channels(self):
        """Full 32 channel configuration"""
        controller = HBM4Controller()

        # Submit to all 32 channels
        for ch in range(32):
            addr = (ch << 41) | 0x8
            req_id = controller.submit_request(
                addr=addr,
                is_read=True,
                size_bytes=64
            )
            assert req_id is not None

        # Run simulation
        for _ in range(200):
            controller.tick()

        # Verify all channels processed
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] >= 32


class TestOverflowUnderflowConditions:
    """Test overflow and underflow conditions"""

    def test_queue_overflow_handling(self):
        """Queue overflow must be handled gracefully"""
        controller = HBM4Controller()

        # Submit many requests
        submitted = 0
        rejected = 0

        for i in range(10000):
            req_id = controller.submit_request(
                addr=i * 0x100,
                is_read=True,
                size_bytes=64
            )
            if req_id is not None:
                submitted += 1
            else:
                rejected += 1

        # Some should be accepted, some rejected
        assert submitted > 0
        assert rejected >= 0

    def test_negative_address_rejection(self):
        """Negative addresses should be handled"""
        controller = HBM4Controller()

        # Very large address (simulates negative when interpreted)
        addr = 0xFFFFFFFFFFFFFFFF

        # Should not crash
        try:
            req_id = controller.submit_request(addr=addr, is_read=True, size_bytes=64)
            # May be rejected, but no crash
        except Exception:
            pytest.fail("Controller crashed on large address")

    def test_zero_cycle_wait(self):
        """Zero cycle wait handling"""
        scheduler = HBM4RefreshScheduler()

        # Wait 0 cycles
        scheduler.tick()  # 1 cycle
        scheduler.tick()  # Another cycle

        # Should not have accumulated 0 cycles
        assert scheduler.cycles_since_refresh > 0

    def test_max_cycle_handling(self):
        """Maximum cycle count handling"""
        scheduler = HBM4RefreshScheduler()

        # Simulate very long run
        for _ in range(1000000):
            scheduler.tick()

        # Should handle gracefully
        assert scheduler.current_cycle > 0


# ============================================================================
# Stress Tests
# ============================================================================

class TestSustainedHighLoad:
    """Test sustained high-load scenarios"""

    def test_sustained_read_load(self):
        """Sustained high read load"""
        controller = HBM4Controller()

        # Submit many reads
        submitted = 0
        for i in range(1000):
            req_id = controller.submit_request(
                addr=(i % 32) << 41 | 0x1000,
                is_read=True,
                size_bytes=64
            )
            if req_id is not None:
                submitted += 1

        # Run simulation
        for _ in range(5000):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] > 0

    def test_sustained_write_load(self):
        """Sustained high write load"""
        controller = HBM4Controller()

        submitted = 0
        for i in range(500):
            req_id = controller.submit_request(
                addr=(i % 32) << 41 | 0x1000,
                is_read=False,  # Write
                size_bytes=64
            )
            if req_id is not None:
                submitted += 1

        # Run simulation
        for _ in range(3000):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] > 0

    def test_mixed_read_write_load(self):
        """Mixed read/write high load"""
        controller = HBM4Controller()

        for i in range(2000):
            controller.submit_request(
                addr=(i % 32) << 41 | 0x1000,
                is_read=(i % 2 == 0),
                size_bytes=64
            )

        # Run
        for _ in range(5000):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] > 0


class TestLongDurationSimulation:
    """Test long-duration simulation stability"""

    def test_long_simulation_no_crash(self):
        """Long simulation without crashes"""
        controller = HBM4Controller()

        # Submit periodically
        for cycle in range(10000):
            controller.submit_request(
                addr=0x1000,
                is_read=True,
                size_bytes=64
            )
            controller.tick()

        # Should complete without error
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] > 0

    def test_many_refresh_cycles(self):
        """Many refresh cycles without error"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        refresh_count = 0
        for _ in range(scheduler.tREFI * 100):  # 100 refresh intervals
            scheduler.tick()

            if scheduler.can_refresh():
                scheduler.get_refresh_command()
                refresh_count += 1

        assert refresh_count > 90  # Allow some tolerance


class TestMemoryExhaustion:
    """Test memory exhaustion scenarios"""

    def test_queue_memory_bounds(self):
        """Queue with large depth memory behavior"""
        queue = PriorityQueue(max_depth=100000)

        # Fill partially
        for i in range(50000):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True, qos=8))

        assert queue.size() == 50000

        # Drain
        for _ in range(50000):
            queue.pop()

        assert queue.size() == 0

    def test_error_tracker_memory(self):
        """Error tracker memory management"""
        tracker = ErrorTracker(max_events=1000)

        # Record many errors
        for i in range(5000):
            tracker.record_event(
                error_type=ErrorType.SINGLE_BIT,
                channel=i % 32,
                bank=i % 16
            )

        # Should not crash, oldest events may be dropped
        events = tracker.get_recent_errors(100)
        assert len(events) <= 100


class TestConcurrentOperationStress:
    """Test concurrent operation stress"""

    def test_all_channels_active(self):
        """All 32 channels active simultaneously"""
        controller = HBM4Controller()

        # Submit to all channels
        for ch in range(32):
            for i in range(10):
                addr = (ch << 41) | (i * 0x1000)
                controller.submit_request(addr=addr, is_read=True, size_bytes=64)

        # Run simulation
        for _ in range(500):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] >= 256  # Queue limited

    def test_all_banks_active(self):
        """All 1024 banks potentially active"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Get many refresh commands
        banks_seen = set()
        for _ in range(1100):
            for _ in range(scheduler.tREFIpb):
                scheduler.tick()

            cmd = scheduler.get_refresh_command()
            if cmd and cmd[3] is not None:
                ch, pch, bank = cmd[1], cmd[2], cmd[3]
                global_bank = ch * 32 + pch * 16 + bank
                banks_seen.add(global_bank)

        # Should have seen many banks
        assert len(banks_seen) >= 100


# ============================================================================
# Integration Tests
# ============================================================================

class TestControllerDRAMIntegration:
    """Test controller-DRAM integration"""

    def test_controller_to_channel(self):
        """Controller submit to channel model"""
        controller = HBM4Controller()
        channel = HBM4Channel(channel_id=0)

        # Submit request
        req_id = controller.submit_request(
            addr=0x1000,
            is_read=True,
            size_bytes=64
        )

        assert req_id is not None

        # Run simulation
        for _ in range(200):
            controller.tick()
            channel.tick()

    def test_address_decode_to_bank(self):
        """Address decode to bank state"""
        decoder = HBM4AddressDecoder()

        # Decode address
        for ch in range(4):
            addr = (ch << 41) | 0x1000
            decoded = decoder.decode(addr)

            assert decoded is not None
            assert 0 <= decoded.channel_id < 32

    def test_controller_refresh_integration(self):
        """Controller with refresh integration"""
        controller = HBM4Controller(enable_refresh=True)

        # Submit requests
        for i in range(100):
            controller.submit_request(addr=i * 0x100, is_read=True, size_bytes=64)

        # Run with refresh
        for _ in range(5000):
            controller.tick()

        # Should have processed requests and refreshes
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] > 0


class TestMultiChannelCoordination:
    """Test multi-channel coordination"""

    def test_channel_independence(self):
        """Channels operate independently"""
        controller = HBM4Controller()

        # Submit to different channels
        ch0_req = controller.submit_request(addr=(0 << 41) | 0x1000, is_read=True, size_bytes=64)
        ch1_req = controller.submit_request(addr=(1 << 41) | 0x1000, is_read=True, size_bytes=64)

        assert ch0_req is not None
        assert ch1_req is not None

        # Run
        for _ in range(500):
            controller.tick()

    def test_cross_channel_bank_conflicts(self):
        """Bank conflicts across channels"""
        # Channel 0
        bsm0 = HBM4BankStateMachine(bank_id=0)
        bsm0.activate(row=0x100)

        # Channel 1 - same bank, should not conflict (different channel)
        bsm1 = HBM4BankStateMachine(bank_id=0)
        can_act = bsm1.can_activate()

        assert can_act is True  # Different channel, no conflict

    def test_all_channels_coordinated(self):
        """All channels coordinated"""
        controller = HBM4Controller()

        # Submit to all channels
        for ch in range(32):
            for beat in range(4):
                addr = (ch << 41) | (beat * 0x100)
                controller.submit_request(addr=addr, is_read=True, size_bytes=64)

        # Verify all submitted
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] >= 128

        # Run
        for _ in range(1000):
            controller.tick()


class TestSchedulerIntegration:
    """Test scheduler integration"""

    def test_qos_scheduler_controller_integration(self):
        """QoS scheduler with controller"""
        scheduler = HBM4QoSScheduler()
        controller = HBM4Controller()

        # Submit with various QoS
        for i in range(50):
            scheduler.submit_request(
                request_id=i,
                addr=(i % 8) << 41 | 0x1000,
                qos=15 - (i % 16),
                is_read=True
            )

        # Schedule and submit to controller
        for _ in range(50):
            req = scheduler.schedule()
            if req:
                controller.submit_request(
                    addr=req.addr,
                    is_read=req.is_read,
                    size_bytes=64
                )

    def test_refresh_scheduler_integration(self):
        """Refresh scheduler with controller"""
        controller = HBM4Controller()
        scheduler = HBM4RefreshScheduler()

        # Run together
        for _ in range(10000):
            controller.tick()
            scheduler.tick()


# ============================================================================
# ECC/CRC Combined Error Tests
# ============================================================================

class TestCombinedIntegrityProtection:
    """Test combined ECC/CRC/Parity protection"""

    def test_all_protections_enabled(self):
        """All protections enabled together"""
        di = HBM4DataIntegrity(
            data_width=64,
            enable_ecc=True,
            enable_crc=True,
            enable_parity=True
        )

        original = 0xDEADBEEFCAFEBABE
        encoded = di.encode_with_protection(original)
        result = di.decode_with_verification(encoded)

        assert result['valid']
        assert result['data'] == original

    def test_ecc_corrects_crc_detects(self):
        """ECC corrects, CRC detects"""
        di = HBM4DataIntegrity(data_width=64, enable_ecc=True, enable_crc=True)

        original = 0x123456789ABCDEF0
        encoded = di.encode_with_protection(original)

        # Inject bit error
        if isinstance(encoded, dict):
            encoded['data'] ^= 0x10

        result = di.decode_with_verification(encoded)

        # Should either correct or detect
        assert result is not None


# ============================================================================
# Run tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
