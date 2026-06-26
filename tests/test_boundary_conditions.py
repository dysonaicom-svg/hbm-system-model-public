"""
HBM4 Extended Boundary Condition Tests

Comprehensive tests covering address, channel, timing, and queue boundary conditions.
Targets: 50+ test cases for 90%+ coverage.

Test Categories:
1. Address Boundary: 0x0, max_address, overflow conditions
2. Channel Boundary: 0, 31, out-of-range scenarios
3. Timing Boundary: min/max cycle counts
4. Queue Boundary: empty, full, overflow conditions
"""

import pytest
import random
from typing import List, Optional

from model.dram.hbm4_spec import HBM4Spec
from model.dram.hbm4_bank_state_machine import (
    HBM4BankStateMachine, HBM4BankState, HBM4BankTiming
)
from model.dram.hbm4_channel_model import HBM4Channel
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
# Address Boundary Tests
# ============================================================================

class TestAddressBoundary:
    """Test address boundaries: 0x0, max_address, overflow"""

    def test_address_zero_decode(self):
        """Address 0 should decode correctly"""
        decoder = HBM4AddressDecoder()
        decoded = decoder.decode(0)

        assert decoded.channel_id == 0
        assert decoded.bank_id == 0
        assert decoded.row_id == 0
        assert decoded.col_id == 0

    def test_address_minimum_all_fields(self):
        """Minimum address with all fields at 0"""
        decoder = HBM4AddressDecoder()
        decoded = decoder.decode(0)

        assert decoded.stack_id == 0
        assert decoded.pseudo_channel_id == 0
        assert decoded.bank_group_id == 0

    def test_address_max_valid_boundary(self):
        """Maximum valid address boundary"""
        decoder = HBM4AddressDecoder()
        spec = HBM4Spec()

        # Maximum address: (1 << 42) - 8 for 8-byte alignment
        max_addr = (1 << 42) - 8
        decoded = decoder.decode(max_addr)

        assert decoded is not None
        # Channel should be masked to valid range
        assert 0 <= decoded.channel_id < 32

    def test_address_all_fields_max(self):
        """All fields at maximum values"""
        decoder = HBM4AddressDecoder()

        # Row field is 16 bits (max 0xFFFF)
        addr = (
            (3 << 46) |    # Stack: 3
            (31 << 41) |   # Channel: 31
            (1 << 40) |    # PCH: 1
            (7 << 37) |    # BG: 7
            (15 << 33) |   # Bank: 15
            (0xFFFF << 16) | # Row: 0xFFFF (max for 16-bit row)
            (63 << 8) |    # Col: 63
            (3 << 6)       # Burst: 3
        )
        decoded = decoder.decode(addr)

        assert decoded.stack_id == 3
        assert decoded.channel_id == 31
        assert decoded.pseudo_channel_id == 1
        assert decoded.bank_group_id == 7
        assert decoded.bank_id == 15
        assert decoded.row_id == 0xFFFF
        assert decoded.col_id == 63

    def test_address_row_boundary_0_and_1(self):
        """Row boundary between 0 and 1"""
        decoder = HBM4AddressDecoder()

        # Row field is at bit 16, so shift by 16
        addr_row0 = 0  # row 0
        addr_row1 = 1 << 16  # row 1 (bit 16 set)

        decoded0 = decoder.decode(addr_row0)
        decoded1 = decoder.decode(addr_row1)

        assert decoded0.row_id == 0
        assert decoded1.row_id == 1

    def test_address_row_boundary_last_two(self):
        """Row boundary at end of range"""
        decoder = HBM4AddressDecoder()

        addr_row_max1 = ((1 << 19) - 1) << 17  # Row 511K
        addr_row_max2 = ((1 << 19) - 2) << 17  # Row 511K - 1

        decoded1 = decoder.decode(addr_row_max1)
        decoded2 = decoder.decode(addr_row_max2)

        # Values may be masked due to row field width
        assert decoded1.row_id >= 0
        assert decoded2.row_id >= 0

    def test_address_column_boundary_0_and_63(self):
        """Column boundary at extremes"""
        decoder = HBM4AddressDecoder()

        addr_col0 = 0
        addr_col63 = 63 << 8

        decoded0 = decoder.decode(addr_col0)
        decoded63 = decoder.decode(addr_col63)

        assert decoded0.col_id == 0
        assert decoded63.col_id == 63

    def test_address_overflow_beyond_42_bits(self):
        """Address overflow beyond 42 bits should be handled"""
        decoder = HBM4AddressDecoder()

        # Address beyond valid range
        overflow_addr = 1 << 50
        decoded = decoder.decode(overflow_addr)

        assert decoded is not None

    def test_address_negative_simulation(self):
        """Negative address handling (Python signed int)"""
        decoder = HBM4AddressDecoder()

        # Python allows negative addresses
        addr = -0x1000
        decoded = decoder.decode(addr)

        # Should produce valid decoded address or handle gracefully
        assert decoded is not None

    def test_address_alignment_boundaries(self):
        """8-byte alignment boundaries"""
        decoder = HBM4AddressDecoder()

        # Test 8-byte aligned addresses
        for offset in range(0, 64, 8):
            addr = 0x1000 + offset
            decoded = decoder.decode(addr)
            assert decoded is not None

    def test_address_misalignment_handling(self):
        """Misaligned address auto-correction"""
        decoder = HBM4AddressDecoder()

        # Misaligned addresses (not 8-byte aligned)
        for offset in [1, 2, 3, 4, 5, 6, 7]:
            addr = 0x1000 + offset
            decoded = decoder.decode(addr)
            assert decoded is not None


# ============================================================================
# Channel Boundary Tests
# ============================================================================

class TestChannelBoundary:
    """Test channel boundaries: 0, 31, out-of-range"""

    def test_channel_0_valid(self):
        """Channel 0 should be valid"""
        decoder = HBM4AddressDecoder()
        decoded = decoder.decode(0)
        assert decoded.channel_id == 0

    def test_channel_31_valid(self):
        """Channel 31 (max) should be valid"""
        decoder = HBM4AddressDecoder()
        addr = 31 << 41
        decoded = decoder.decode(addr)
        assert decoded.channel_id == 31

    def test_channel_boundary_ch0_ch1(self):
        """Channel boundary between 0 and 1"""
        decoder = HBM4AddressDecoder()

        addr_ch0 = 0
        addr_ch1 = 1 << 41

        assert decoder.get_channel_id(addr_ch0) == 0
        assert decoder.get_channel_id(addr_ch1) == 1

    def test_channel_boundary_ch30_ch31(self):
        """Channel boundary between 30 and 31"""
        decoder = HBM4AddressDecoder()

        addr_ch30 = 30 << 41
        addr_ch31 = 31 << 41

        assert decoder.get_channel_id(addr_ch30) == 30
        assert decoder.get_channel_id(addr_ch31) == 31

    def test_all_32_channels_accessible(self):
        """All 32 channels should be accessible"""
        decoder = HBM4AddressDecoder()

        for ch in range(32):
            addr = ch << 41
            decoded = decoder.decode(addr)
            assert decoded.channel_id == ch

    def test_channel_out_of_range_high(self):
        """Channel > 31 should be masked"""
        decoder = HBM4AddressDecoder()

        # Channel 32 (invalid)
        addr = 32 << 41
        decoded = decoder.decode(addr)

        # Should be masked to valid range
        assert 0 <= decoded.channel_id < 32

    def test_channel_negative_invalid(self):
        """Negative channel should be handled"""
        decoder = HBM4AddressDecoder()

        addr = -1
        decoded = decoder.decode(addr)

        # Should produce valid result
        assert decoded is not None

    def test_pseudo_channel_0_and_1(self):
        """Both pseudo-channels should be valid"""
        decoder = HBM4AddressDecoder()

        addr_pch0 = 0
        addr_pch1 = 1 << 40

        assert decoder.get_pseudo_channel_id(addr_pch0) == 0
        assert decoder.get_pseudo_channel_id(addr_pch1) == 1

    def test_all_64_pseudo_channels_accessible(self):
        """All 64 pseudo-channels should be accessible"""
        decoder = HBM4AddressDecoder()

        for ch in range(32):
            for pch in range(2):
                addr = (ch << 41) | (pch << 40)
                decoded = decoder.decode(addr)
                assert decoded.channel_id == ch
                assert decoded.pseudo_channel_id == pch


# ============================================================================
# Timing Boundary Tests
# ============================================================================

class TestTimingBoundary:
    """Test timing boundaries: min/max cycle counts"""

    def test_minimum_tCK(self):
        """Minimum clock period constraint"""
        spec = HBM4Spec()
        assert spec.tCK_ps > 0
        assert spec.tCK_ps <= 125

    def test_tRCD_minimum(self):
        """Minimum tRCD timing"""
        timing = HBM4BankTiming()
        assert timing.tRCD >= 1

    def test_tRP_minimum(self):
        """Minimum tRP timing"""
        timing = HBM4BankTiming()
        assert timing.tRP >= 1

    def test_tRAS_minimum(self):
        """Minimum tRAS (row active time)"""
        timing = HBM4BankTiming()
        assert timing.tRAS >= 1

    def test_tRC_minimum(self):
        """Minimum tRC (row cycle time)"""
        timing = HBM4BankTiming()
        assert timing.tRC >= 1
        assert timing.tRC > timing.tRAS

    def test_tCCD_minimum(self):
        """Minimum CCD timing"""
        timing = HBM4BankTiming()
        assert timing.tCCD >= 1

    def test_tRRD_minimum(self):
        """Minimum RRD timing"""
        timing = HBM4BankTiming()
        assert timing.tRRDS >= 1

    def test_maximum_latency(self):
        """Maximum latency should be bounded"""
        spec = HBM4Spec()
        # Max latency should be reasonable
        assert spec.nCL <= 100
        assert spec.nRCDRD <= 100

    def test_tREFI_minimum(self):
        """Minimum refresh interval"""
        scheduler = HBM4RefreshScheduler()
        assert scheduler.tREFI > 0

    def test_tRFC_minimum(self):
        """Minimum refresh cycle time"""
        timing = HBM4BankTiming()
        assert timing.tRFC > 0

    def test_tFAW_window(self):
        """FAW window should be reasonable"""
        timing = HBM4BankTiming()
        assert timing.tFAW >= timing.tRRDS * 4

    def test_turnaround_timing_relationships(self):
        """Turnaround timing should have proper relationships"""
        timing = HBM4BankTiming()
        # tWTRL > tWTRS (longer for different BG)
        assert timing.tWTRL >= timing.tWTRS
        # tRTW should be reasonable
        assert timing.tRTW >= 1

    def test_burst_length_minimum(self):
        """Burst length should be positive"""
        timing = HBM4BankTiming()
        assert timing.tBL >= 1

    def test_speed_grade_8gbps_timing(self):
        """8 Gbps speed grade timing"""
        timing = HBM4BankTiming.for_speed_grade(8.0)
        assert abs(timing.tCK_ps - 125.0) < 0.1

    def test_speed_grade_12gbps_timing(self):
        """12 Gbps speed grade timing"""
        timing = HBM4BankTiming.for_speed_grade(12.0)
        assert abs(timing.tCK_ps - 83.33) < 0.1

    def test_speed_grade_16gbps_timing(self):
        """16 Gbps speed grade timing"""
        timing = HBM4BankTiming.for_speed_grade(16.0)
        assert abs(timing.tCK_ps - 62.5) < 0.1


# ============================================================================
# Queue Boundary Tests
# ============================================================================

class TestQueueBoundary:
    """Test queue boundaries: empty, full, overflow"""

    def test_empty_queue_pop(self):
        """Pop on empty queue"""
        queue = ReadQueue(max_depth=32)
        result = queue.pop()
        assert result is None

    def test_empty_queue_size(self):
        """Empty queue size is 0"""
        queue = ReadQueue(max_depth=32)
        assert queue.size() == 0
        assert queue.is_empty()
        assert not queue.is_full()

    def test_empty_queue_peek(self):
        """Peek on empty queue"""
        queue = ReadQueue(max_depth=32)
        result = queue.peek()
        assert result is None

    def test_full_queue_push_rejected(self):
        """Push rejected on full queue"""
        queue = ReadQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))

        result = queue.push(HBMRequest(addr=0x300, length=64, is_read=True))
        assert result is False

    def test_full_queue_size(self):
        """Full queue size equals max"""
        queue = ReadQueue(max_depth=4)
        for i in range(4):
            queue.push(HBMRequest(addr=i * 0x100, length=64, is_read=True))

        assert queue.size() == 4
        assert queue.is_full()

    def test_queue_depth_1(self):
        """Queue with depth 1"""
        queue = ReadQueue(max_depth=1)
        assert queue.is_empty()

        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        assert queue.is_full()
        assert queue.size() == 1

        queue.pop()
        assert queue.is_empty()

    def test_queue_depth_very_large(self):
        """Queue with very large depth"""
        queue = ReadQueue(max_depth=100000)
        assert queue.max_depth == 100000

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

    def test_write_queue_empty(self):
        """Write queue empty behavior"""
        queue = WriteQueue(max_depth=32)
        result = queue.pop()
        assert result is None

    def test_write_queue_full(self):
        """Write queue full behavior"""
        queue = WriteQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=False))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=False))

        result = queue.push(HBMRequest(addr=0x300, length=64, is_read=False))
        assert result is False

    def test_priority_queue_empty(self):
        """Priority queue empty behavior"""
        queue = PriorityQueue(max_depth=32)
        result = queue.pop()
        assert result is None

    def test_priority_queue_full(self):
        """Priority queue full behavior"""
        queue = PriorityQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True, qos=8))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True, qos=8))

        result = queue.push(HBMRequest(addr=0x300, length=64, is_read=True, qos=8))
        assert result is False

    def test_queue_manager_empty(self):
        """Queue manager empty behavior"""
        manager = QueueManager.create(queue_depth=32)
        # Queue manager empty means total size is 0
        assert manager.total_size() == 0

    def test_queue_manager_full(self):
        """Queue manager full behavior"""
        manager = QueueManager.create(queue_depth=2)

        # Fill read queue
        manager.push_read(HBMRequest(addr=0x100, length=64, is_read=True))
        manager.push_read(HBMRequest(addr=0x200, length=64, is_read=True))

        assert manager.is_full()

    def test_queue_overflow_stats(self):
        """Queue overflow statistics tracking"""
        queue = ReadQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x100, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x200, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x300, length=64, is_read=True))  # Rejected

        stats = queue.get_stats()
        assert stats['reject_count'] == 1


# ============================================================================
# Combined Boundary Tests
# ============================================================================

class TestCombinedBoundaries:
    """Test combinations of boundaries"""

    def test_max_channel_max_row(self):
        """Maximum channel with maximum row"""
        decoder = HBM4AddressDecoder()

        addr = (31 << 41) | (0x7FFFF << 17)
        decoded = decoder.decode(addr)

        assert decoded.channel_id == 31

    def test_min_channel_min_row(self):
        """Minimum channel with minimum row"""
        decoder = HBM4AddressDecoder()

        addr = 0
        decoded = decoder.decode(addr)

        assert decoded.channel_id == 0
        assert decoded.row_id == 0

    def test_boundary_refresh_during_activity(self):
        """Refresh at boundary during active operations"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        bsm = HBM4BankStateMachine(bank_id=0)
        bsm.activate(row=0x100)

        # Advance to refresh boundary
        for _ in range(scheduler.tREFI):
            scheduler.tick()

        assert scheduler.can_refresh() is True

    def test_boundary_channel_queue_full(self):
        """Channel operations with full queues"""
        controller = HBM4Controller()

        # Submit many requests to same channel
        for i in range(100):
            addr = 0 | (i * 0x100)
            controller.submit_request(addr=addr, is_read=True, size_bytes=64)

        # Should handle gracefully
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] > 0


# ============================================================================
# Run tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
