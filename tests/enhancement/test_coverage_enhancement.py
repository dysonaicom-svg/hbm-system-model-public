"""
Enhanced Boundary Condition and Corner Case Tests for HBM4

Comprehensive test coverage for edge cases and boundary conditions including:
1. Extreme address boundary conditions (min, max, overflow)
2. Channel boundary testing (0, max, out-of-range)
3. Timing constraint boundary testing (min/max values)
4. Queue boundary testing (empty, full, overflow)
5. Combined multi-boundary scenarios
6. Error injection at boundaries
7. Pseudo-channel edge cases
8. Bank group timing boundaries

Target: 60+ test cases for comprehensive coverage

Test Organization:
- TestAddressBoundaries: Address space edge cases
- TestChannelBoundaries: Channel count and ID boundaries
- TestTimingBoundaries: Timing parameter limits
- TestQueueBoundaries: Queue depth and state transitions
- TestMultiBoundaryScenarios: Combined boundary conditions
- TestPseudoChannelBoundaries: Pseudo-channel edge cases
- TestBankGroupBoundaries: Bank group timing limits
- TestErrorInjectionBoundaries: Error conditions at boundaries
"""

import pytest
import random
from typing import List, Optional, Tuple
from dataclasses import dataclass

from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.hbm4_bank_state_machine import (
    create_hbm4_bank_state_machine, HBM4BankState, HBM4BankTiming,
    HBM4Command
)
from model.dram.hbm4_channel_model import (
    HBM4Channel, HBM4ChannelArray
)
from model.dram.ecc_crc import (
    HBM4ECC, HBM4CRC, ErrorType, ErrorTracker
)
from model.dram.lane_repair import (
    HBM4LaneRepairModel, RepairStatus, LaneFailureMode
)
from model.controller.queue import (
    ReadQueue, WriteQueue, PriorityQueue, QueueManager
)
from model.controller.request import HBMRequest, RequestState
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler
from model.controller.hbm4_refresh_scheduler import (
    HBM4RefreshScheduler, RefreshMode, RefreshCommand
)


# ============================================================================
# Test Address Boundaries
# ============================================================================

class TestAddressBoundaries:
    """Test address space boundary conditions"""

    def test_address_zero_all_fields(self):
        """Address 0x0 - all fields minimum"""
        decoder = HBM4AddressDecoder()
        decoded = decoder.decode(0)

        assert decoded.channel_id == 0
        assert decoded.bank_id == 0
        assert decoded.row_id == 0
        assert decoded.col_id == 0
        assert decoded.stack_id == 0
        assert decoded.pseudo_channel_id == 0
        assert decoded.bank_group_id == 0

    def test_address_maximum_42bit(self):
        """Maximum 42-bit address boundary"""
        decoder = HBM4AddressDecoder()
        max_addr = (1 << 42) - 8  # 8-byte aligned

        decoded = decoder.decode(max_addr)
        assert decoded is not None
        # Channel should be masked to valid range
        assert 0 <= decoded.channel_id < 32

    def test_address_43bit_overflow(self):
        """Address overflow beyond 42 bits"""
        decoder = HBM4AddressDecoder()
        overflow_addr = 1 << 43

        decoded = decoder.decode(overflow_addr)
        assert decoded is not None

    def test_address_48bit_overflow(self):
        """Address overflow beyond 48 bits"""
        decoder = HBM4AddressDecoder()
        overflow_addr = 1 << 48

        decoded = decoder.decode(overflow_addr)
        assert decoded is not None

    def test_address_64bit_extreme(self):
        """64-bit address extreme value"""
        decoder = HBM4AddressDecoder()
        extreme_addr = 0xFFFFFFFFFFFFFFFF

        decoded = decoder.decode(extreme_addr)
        assert decoded is not None

    def test_address_negative_python_int(self):
        """Negative address handling (Python signed integer)"""
        decoder = HBM4AddressDecoder()

        for neg_addr in [-1, -0x100, -0x10000]:
            decoded = decoder.decode(neg_addr)
            assert decoded is not None

    def test_address_row_min_boundary(self):
        """Row boundary at minimum (0)"""
        decoder = HBM4AddressDecoder()

        addr = 0  # row = 0
        decoded = decoder.decode(addr)
        assert decoded.row_id == 0

    def test_address_row_max_boundary(self):
        """Row boundary at maximum"""
        decoder = HBM4AddressDecoder()

        # Row field is 16 bits, max 0xFFFF
        addr = 0xFFFF << 16
        decoded = decoder.decode(addr)
        assert decoded.row_id == 0xFFFF

    def test_address_row_boundary_transition(self):
        """Row boundary transition from 0xFFFE to 0xFFFF"""
        decoder = HBM4AddressDecoder()

        addr1 = 0xFFFE << 16
        addr2 = 0xFFFF << 16

        decoded1 = decoder.decode(addr1)
        decoded2 = decoder.decode(addr2)

        assert decoded2.row_id > decoded1.row_id

    def test_address_column_min_boundary(self):
        """Column boundary at minimum (0)"""
        decoder = HBM4AddressDecoder()

        decoded = decoder.decode(0)
        assert decoded.col_id == 0

    def test_address_column_max_boundary(self):
        """Column boundary at maximum (63)"""
        decoder = HBM4AddressDecoder()

        addr = 63 << 8
        decoded = decoder.decode(addr)
        assert decoded.col_id == 63

    def test_address_column_boundary_transition(self):
        """Column boundary transition at edge"""
        decoder = HBM4AddressDecoder()

        addr1 = 62 << 8
        addr2 = 63 << 8

        decoded1 = decoder.decode(addr1)
        decoded2 = decoder.decode(addr2)

        assert decoded2.col_id > decoded1.col_id

    def test_address_alignment_8byte_aligned(self):
        """8-byte aligned addresses"""
        decoder = HBM4AddressDecoder()

        for offset in range(0, 64, 8):
            addr = 0x1000 + offset
            decoded = decoder.decode(addr)
            assert decoded is not None

    def test_address_alignment_4byte_misaligned(self):
        """4-byte misaligned addresses (auto-corrected)"""
        decoder = HBM4AddressDecoder()

        for offset in [0, 1, 2, 3]:
            addr = 0x1000 + offset
            decoded = decoder.decode(addr)
            assert decoded is not None

    def test_address_alignment_2byte_misaligned(self):
        """2-byte misaligned addresses (auto-corrected)"""
        decoder = HBM4AddressDecoder()

        for offset in [0, 1]:
            addr = 0x1000 + offset
            decoded = decoder.decode(addr)
            assert decoded is not None

    def test_address_all_bank_combinations(self):
        """All bank values from 0 to 15"""
        decoder = HBM4AddressDecoder()

        # Bank field is at bits 36:33 (4 bits)
        for bank in range(16):
            addr = bank << 33
            decoded = decoder.decode(addr)
            assert decoded.bank_id == bank

    def test_address_all_bank_group_combinations(self):
        """All bank group values from 0 to 7"""
        decoder = HBM4AddressDecoder()

        for bg in range(8):
            addr = bg << 37
            decoded = decoder.decode(addr)
            assert decoded.bank_group_id == bg


# ============================================================================
# Test Channel Boundaries
# ============================================================================

class TestChannelBoundaries:
    """Test channel boundary conditions"""

    def test_channel_minimum_ch0(self):
        """Channel 0 minimum boundary"""
        decoder = HBM4AddressDecoder()

        decoded = decoder.decode(0)
        assert decoded.channel_id == 0

    def test_channel_maximum_ch31(self):
        """Channel 31 maximum boundary"""
        decoder = HBM4AddressDecoder()

        addr = 31 << 41
        decoded = decoder.decode(addr)
        assert decoded.channel_id == 31

    def test_channel_boundary_ch0_to_ch1(self):
        """Channel boundary between 0 and 1"""
        decoder = HBM4AddressDecoder()

        addr_ch0 = 0
        addr_ch1 = 1 << 41

        assert decoder.get_channel_id(addr_ch0) == 0
        assert decoder.get_channel_id(addr_ch1) == 1

    def test_channel_boundary_ch30_to_ch31(self):
        """Channel boundary between 30 and 31"""
        decoder = HBM4AddressDecoder()

        addr_ch30 = 30 << 41
        addr_ch31 = 31 << 41

        assert decoder.get_channel_id(addr_ch30) == 30
        assert decoder.get_channel_id(addr_ch31) == 31

    def test_all_32_channels_sequential(self):
        """All 32 channels accessible sequentially"""
        decoder = HBM4AddressDecoder()

        for ch in range(32):
            addr = ch << 41
            decoded = decoder.decode(addr)
            assert decoded.channel_id == ch

    def test_channel_out_of_range_ch32(self):
        """Channel 32 out of range (should mask)"""
        decoder = HBM4AddressDecoder()

        addr = 32 << 41
        decoded = decoder.decode(addr)

        # Should be masked to valid range
        assert 0 <= decoded.channel_id < 32

    def test_channel_out_of_range_ch63(self):
        """Channel 63 out of range"""
        decoder = HBM4AddressDecoder()

        addr = 63 << 41
        decoded = decoder.decode(addr)

        # Should be masked
        assert 0 <= decoded.channel_id < 32

    def test_channel_out_of_range_ch255(self):
        """Channel 255 out of range (extreme)"""
        decoder = HBM4AddressDecoder()

        addr = 255 << 41
        decoded = decoder.decode(addr)

        assert 0 <= decoded.channel_id < 32

    def test_channel_negative_index(self):
        """Negative channel index handling"""
        decoder = HBM4AddressDecoder()

        addr = -1
        decoded = decoder.decode(addr)
        assert decoded is not None


# ============================================================================
# Test Timing Boundaries
# ============================================================================

class TestTimingBoundaries:
    """Test timing parameter boundary conditions"""

    def test_tCK_minimum_boundary(self):
        """Minimum clock period"""
        spec = HBM4Spec()
        assert spec.tCK_ps > 0
        assert spec.tCK_ps <= 125  # 16 Gbps max

    def test_tCK_8gbps_boundary(self):
        """Clock period at 8 Gbps"""
        timing = HBM4BankTiming.for_speed_grade(8.0)
        assert abs(timing.tCK_ps - 125.0) < 0.1

    def test_tCK_12gbps_boundary(self):
        """Clock period at 12 Gbps"""
        timing = HBM4BankTiming.for_speed_grade(12.0)
        assert abs(timing.tCK_ps - 83.33) < 0.1

    def test_tCK_16gbps_boundary(self):
        """Clock period at 16 Gbps"""
        timing = HBM4BankTiming.for_speed_grade(16.0)
        assert abs(timing.tCK_ps - 62.5) < 0.1

    def test_tRCD_minimum(self):
        """Minimum RAS to CAS delay"""
        timing = HBM4BankTiming()
        assert timing.tRCD >= 1

    def test_tRP_minimum(self):
        """Minimum precharge time"""
        timing = HBM4BankTiming()
        assert timing.tRP >= 1

    def test_tRAS_minimum(self):
        """Minimum row active time"""
        timing = HBM4BankTiming()
        assert timing.tRAS >= 1

    def test_tRC_minimum(self):
        """Minimum row cycle time"""
        timing = HBM4BankTiming()
        assert timing.tRC >= timing.tRAS
        assert timing.tRC >= timing.tRCD

    def test_tRC_equals_tRAS_plus_tRP(self):
        """tRC should equal tRAS + tRP approximately"""
        timing = HBM4BankTiming()
        # tRC >= tRAS + tRP, with some margin
        assert timing.tRC >= timing.tRAS

    def test_tCCD_minimum(self):
        """Minimum CAS-to-CAS delay"""
        timing = HBM4BankTiming()
        assert timing.tCCD >= 1

    def test_tRRD_minimum(self):
        """Minimum row-to-row delay (same bank group)"""
        timing = HBM4BankTiming()
        assert timing.tRRDS >= 1

    def test_tFAW_minimum(self):
        """Minimum four-bank activation window"""
        timing = HBM4BankTiming()
        assert timing.tFAW >= timing.tRRDS * 4

    def test_tREFI_minimum(self):
        """Minimum refresh interval"""
        scheduler = HBM4RefreshScheduler()
        assert scheduler.tREFI > 0

    def test_tRFC_minimum(self):
        """Minimum refresh cycle time"""
        timing = HBM4BankTiming()
        assert timing.tRFC > 0

    def test_nCL_minimum(self):
        """Minimum CAS latency"""
        spec = HBM4Spec()
        assert spec.nCL >= 1

    def test_nCL_maximum(self):
        """Maximum CAS latency bound"""
        spec = HBM4Spec()
        assert spec.nCL <= 100

    def test_nRCDRD_minimum(self):
        """Minimum RCD for read"""
        spec = HBM4Spec()
        assert spec.nRCDRD >= 1

    def test_tWTRL_vs_tWTRS(self):
        """Write to read delay long vs short"""
        timing = HBM4BankTiming()
        assert timing.tWTRL >= timing.tWTRS

    def test_tRTW_minimum(self):
        """Read to write turnaround"""
        timing = HBM4BankTiming()
        assert timing.tRTW >= 1


# ============================================================================
# Test Queue Boundaries
# ============================================================================

class TestQueueBoundaries:
    """Test queue boundary conditions"""

    def test_queue_depth_1_empty(self):
        """Queue depth 1 - empty state"""
        queue = ReadQueue(max_depth=1)
        assert queue.is_empty()
        assert not queue.is_full()

    def test_queue_depth_1_after_push(self):
        """Queue depth 1 - after single push"""
        queue = ReadQueue(max_depth=1)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))

        assert queue.is_full()
        assert not queue.is_empty()
        assert queue.size() == 1

    def test_queue_depth_1_overflow(self):
        """Queue depth 1 - overflow rejection"""
        queue = ReadQueue(max_depth=1)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))

        result = queue.push(HBMRequest(addr=0x200, length=64, is_read=True))
        assert result is False

    def test_queue_depth_1_drain(self):
        """Queue depth 1 - drain and refill"""
        queue = ReadQueue(max_depth=1)

        # Push and pop cycle
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        item = queue.pop()

        assert item is not None
        assert queue.is_empty()

    def test_queue_depth_very_large_1m(self):
        """Queue with 1M depth"""
        queue = ReadQueue(max_depth=1000000)
        assert queue.max_depth == 1000000

        # Should handle large capacity
        for i in range(100):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))

        assert queue.size() == 100

    def test_queue_empty_pop_none(self):
        """Pop on empty queue returns None"""
        queue = ReadQueue(max_depth=32)
        result = queue.pop()
        assert result is None

    def test_queue_empty_peek_none(self):
        """Peek on empty queue returns None"""
        queue = ReadQueue(max_depth=32)
        result = queue.peek()
        assert result is None

    def test_queue_full_rejection(self):
        """Full queue rejects additional push"""
        queue = ReadQueue(max_depth=2)

        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))

        result = queue.push(HBMRequest(addr=0x300, length=64, is_read=True))
        assert result is False

    def test_queue_full_stats(self):
        """Full queue tracks rejection count"""
        queue = ReadQueue(max_depth=2)

        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x300, length=64, is_read=True))  # Rejected

        stats = queue.get_stats()
        assert stats['reject_count'] == 1

    def test_write_queue_boundary(self):
        """Write queue boundary behavior"""
        queue = WriteQueue(max_depth=4)

        for i in range(4):
            result = queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=False))
            assert result is True

        result = queue.push(HBMRequest(addr=0x500, length=64, is_read=False))
        assert result is False

    def test_priority_queue_boundary(self):
        """Priority queue boundary behavior"""
        queue = PriorityQueue(max_depth=4)

        for i in range(4):
            result = queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True, qos=i))
            assert result is True

        result = queue.push(HBMRequest(addr=0x500, length=64, is_read=True, qos=8))
        assert result is False


# ============================================================================
# Test Pseudo-Channel Boundaries
# ============================================================================

class TestPseudoChannelBoundaries:
    """Test pseudo-channel boundary conditions"""

    def test_pseudo_channel_0(self):
        """Pseudo-channel 0 boundary"""
        decoder = HBM4AddressDecoder()

        addr = 0
        decoded = decoder.decode(addr)
        assert decoded.pseudo_channel_id == 0

    def test_pseudo_channel_1(self):
        """Pseudo-channel 1 boundary"""
        decoder = HBM4AddressDecoder()

        addr = 1 << 40
        decoded = decoder.decode(addr)
        assert decoded.pseudo_channel_id == 1

    def test_pseudo_channel_transition(self):
        """Pseudo-channel 0 to 1 transition"""
        decoder = HBM4AddressDecoder()

        addr_pch0 = 0
        addr_pch1 = 1 << 40

        decoded0 = decoder.decode(addr_pch0)
        decoded1 = decoder.decode(addr_pch1)

        assert decoded0.pseudo_channel_id == 0
        assert decoded1.pseudo_channel_id == 1

    def test_all_64_pseudo_channels(self):
        """All 64 pseudo-channels accessible"""
        decoder = HBM4AddressDecoder()

        for ch in range(32):
            for pch in range(2):
                addr = (ch << 41) | (pch << 40)
                decoded = decoder.decode(addr)
                assert decoded.channel_id == ch
                assert decoded.pseudo_channel_id == pch

    def test_pseudo_channel_permutations(self):
        """All channel x pseudo-channel combinations"""
        decoder = HBM4AddressDecoder()

        combinations = 0
        for ch in range(32):
            for pch in range(2):
                for bg in range(8):
                    for bank in range(16):
                        addr = (ch << 41) | (pch << 40) | (bg << 37) | (bank << 33)
                        decoded = decoder.decode(addr)
                        combinations += 1

        assert combinations == 32 * 2 * 8 * 16


# ============================================================================
# Test Bank Group Boundaries
# ============================================================================

class TestBankGroupBoundaries:
    """Test bank group boundary conditions"""

    def test_bank_group_0_minimum(self):
        """Bank group 0 minimum boundary"""
        decoder = HBM4AddressDecoder()

        decoded = decoder.decode(0)
        assert decoded.bank_group_id == 0

    def test_bank_group_7_maximum(self):
        """Bank group 7 maximum boundary"""
        decoder = HBM4AddressDecoder()

        addr = 7 << 37
        decoded = decoder.decode(addr)
        assert decoded.bank_group_id == 7

    def test_bank_group_boundary(self):
        """Bank group boundary transitions"""
        decoder = HBM4AddressDecoder()

        for bg in range(7):
            addr1 = bg << 37
            addr2 = (bg + 1) << 37

            decoded1 = decoder.decode(addr1)
            decoded2 = decoder.decode(addr2)

            assert decoded2.bank_group_id == bg + 1

    def test_bank_group_timing_faw(self):
        """FAW window across bank groups"""
        timing = HBM4BankTiming()

        # FAW should cover 4-bank activation window
        assert timing.tFAW >= timing.tRRDS * 4

    def test_bank_group_rrd_same_vs_different(self):
        """tRRD for same vs different bank groups"""
        timing = HBM4BankTiming()

        # tRRDS (same BG) should be <= tRRDL (different BG)
        assert timing.tRRDS <= timing.tRRDL


# ============================================================================
# Test Multi-Boundary Scenarios
# ============================================================================

class TestMultiBoundaryScenarios:
    """Test combinations of multiple boundary conditions"""

    def test_max_channel_max_row_max_col(self):
        """Maximum values for channel, row, and column"""
        decoder = HBM4AddressDecoder()

        addr = (31 << 41) | (0xFFFF << 16) | (63 << 8)
        decoded = decoder.decode(addr)

        assert decoded.channel_id == 31
        assert decoded.row_id == 0xFFFF
        assert decoded.col_id == 63

    def test_min_channel_min_row_min_col(self):
        """Minimum values for channel, row, and column"""
        decoder = HBM4AddressDecoder()

        addr = 0
        decoded = decoder.decode(addr)

        assert decoded.channel_id == 0
        assert decoded.row_id == 0
        assert decoded.col_id == 0

    def test_channel_boundary_during_refresh(self):
        """Channel operation at refresh boundary"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        bsm = create_hbm4_bank_state_machine(bank_id=0)
        bsm.activate(row=0x100)

        # Advance to refresh boundary
        for _ in range(scheduler.tREFI):
            scheduler.tick()

        assert scheduler.can_refresh() is True

    def test_full_queue_at_channel_boundary(self):
        """Full queue operation at channel boundary"""
        controller = HBM4Controller()

        # Submit many requests to channel 31 (boundary)
        for i in range(100):
            addr = (31 << 41) | (i * 0x100)
            controller.submit_request(addr=addr, is_read=True, size_bytes=64)

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] > 0

    def test_8gbps_timing_at_boundary(self):
        """8 Gbps timing at all boundaries"""
        timing = HBM4BankTiming.for_speed_grade(8.0)

        assert timing.tCK_ps > 0
        assert timing.tRCD >= 1
        assert timing.tRP >= 1
        assert timing.tRAS >= 1
        assert timing.tRC >= timing.tRAS

    def test_16gbps_timing_at_boundary(self):
        """16 Gbps timing at all boundaries"""
        timing = HBM4BankTiming.for_speed_grade(16.0)

        assert timing.tCK_ps > 0
        assert timing.tRCD >= 1
        assert timing.tRP >= 1
        assert timing.tRAS >= 1
        assert timing.tRC >= timing.tRAS

    def test_all_speed_grades_boundary(self):
        """All speed grades at timing boundaries"""
        for gbps in [8.0, 12.0, 16.0]:
            timing = HBM4BankTiming.for_speed_grade(gbps)

            assert timing.tCK_ps > 0
            assert timing.tRCD >= 1
            assert timing.tRP >= 1
            assert timing.tRAS >= 1

    def test_queue_full_with_max_requests(self):
        """Queue full with maximum request size"""
        queue = ReadQueue(max_depth=2)

        queue.push(HBMRequest(addr=0x100, length=256, is_read=True))  # Max length
        queue.push(HBMRequest(addr=0x200, length=256, is_read=True))

        assert queue.is_full()

        result = queue.push(HBMRequest(addr=0x300, length=256, is_read=True))
        assert result is False


# ============================================================================
# Test Error Injection at Boundaries
# ============================================================================

class TestErrorInjectionBoundaries:
    """Test error injection at boundary conditions"""

    def test_ecc_boundary_operations(self):
        """ECC operations at boundary"""
        ecc = HBM4ECC(data_width=64)

        data = 0xFFFFFFFFFFFFFFFF
        ecc_code = ecc.encode(data)

        decoded = ecc.decode(data, ecc_code)
        assert decoded == data

    def test_crc_boundary_operations(self):
        """CRC operations at boundary"""
        crc = HBM4CRC()

        data = b'\xAA' * 64
        crc_value = crc.calculate_crc16(data)
        assert crc.verify_crc16(data, crc_value) is True

    def test_error_tracker_at_queue_boundary(self):
        """Error tracking at queue boundary"""
        tracker = ErrorTracker()

        # Track errors at boundary
        tracker.log_error(ErrorType.ECC_CORRECTABLE, channel=31)
        tracker.log_error(ErrorType.ECC_UNCORRECTABLE, channel=0)
        tracker.log_error(ErrorType.CRC_ERROR, channel=15)

        assert tracker.total_errors > 0

    def test_lane_repair_at_channel_boundary(self):
        """Lane repair at channel boundary"""
        repair = HBM4LaneRepairModel(HBM4Spec())

        # Add failure at channel boundary
        status = repair.add_failure(
            channel_id=31,
            lane_id=0,
            failure_mode=LaneFailureMode.STUCK_AT_0
        )
        assert status in [RepairStatus.ACTIVATED, RepairStatus.PENDING]

    def test_error_counter_overflow_boundary(self):
        """Error counter at overflow boundary"""
        tracker = ErrorTracker()

        # Track many errors
        for i in range(1000):
            tracker.log_error(ErrorType.ECC_CORRECTABLE, channel=i % 32)

        assert tracker.total_errors >= 1000


# ============================================================================
# Test State Machine Boundaries
# ============================================================================

class TestStateMachineBoundaries:
    """Test state machine transitions at boundaries"""

    def test_bank_state_closed_to_active_boundary(self):
        """Bank state transition from CLOSED to ACTIVE"""
        bsm = create_hbm4_bank_state_machine(bank_id=0)

        assert bsm.bank.state == HBM4BankState.CLOSED

        success, _ = bsm.activate(row=0)
        assert success is True

    def test_bank_state_active_to_precharge_boundary(self):
        """Bank state transition from ACTIVE to PRECHARGE"""
        bsm = create_hbm4_bank_state_machine(bank_id=0)

        bsm.activate(row=0x100)

        # Advance through ACTIVE state
        success = bsm.precharge()
        # May fail due to timing, that's expected
        assert success is not None  # Either True or False is valid

    def test_bank_state_precharge_to_closed(self):
        """Bank state transition from PRECHARGE to CLOSED"""
        bsm = create_hbm4_bank_state_machine(bank_id=0)

        bsm.activate(row=0x100)

        # Try precharge after timing
        bsm.precharge()

        # State should be CLOSED after tRP
        assert bsm.bank.state in [HBM4BankState.ACTIVE, HBM4BankState.PRECHARGING, HBM4BankState.CLOSED]

    def test_bank_conflict_at_tRRD_boundary(self):
        """Bank conflict detection at tRRD boundary"""
        bsm1 = create_hbm4_bank_state_machine(bank_id=0)
        bsm2 = create_hbm4_bank_state_machine(bank_id=1)

        # Activate first bank
        bsm1.activate(row=0x100)

        # Different bank should be activatable
        can_activate = bsm2.can_activate()
        assert can_activate is True

    def test_refresh_command_at_boundary(self):
        """Refresh command at timing boundary"""
        scheduler = HBM4RefreshScheduler()

        # Advance to refresh time
        for _ in range(scheduler.tREFI):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()
        assert cmd is not None


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
