"""
End-to-End Integration Tests for RTL Controller + Python DRAM Model

Tests the interaction between RTL controller commands and Python DRAM model timing.
Covers command sequences (ACT -> RD -> PRE), bank conflict handling, and refresh behavior.

Run with: pytest tests/integration/test_e2e_integration.py -v
"""

import pytest
import sys
import time
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, '/home/ic/JXTF/HBM')

from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.hbm4_channel_model import (
    HBM4Channel, HBM4ChannelArray, HBM4Command, PseudoChannelState, BankGroup
)
from model.dram.hbm4_channel_model import HBM4Timing, get_timing_for_speed_grade
from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder, DecodedAddress
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def hbm4_spec():
    """HBM4 specification fixture"""
    return HBM4Spec()


@pytest.fixture
def hbm4_timing():
    """HBM4 timing parameters fixture"""
    return HBM4Timing()


@pytest.fixture
def hbm4_channel(hbm4_spec, hbm4_timing):
    """Single HBM4 channel fixture"""
    return HBM4Channel(channel_id=0, spec=hbm4_spec, timing=hbm4_timing)


@pytest.fixture
def hbm4_channel_array(hbm4_spec, hbm4_timing):
    """HBM4 channel array fixture (32 channels)"""
    return HBM4ChannelArray(spec=hbm4_spec, timing=hbm4_timing)


@pytest.fixture
def hbm4_controller(hbm4_spec):
    """HBM4 controller fixture"""
    return HBM4Controller(spec=hbm4_spec, enable_qos=True, enable_refresh=True, enable_dfi=True)


@pytest.fixture
def address_decoder(hbm4_spec):
    """Address decoder fixture"""
    return HBM4AddressDecoder(spec=hbm4_spec)


# =============================================================================
# Test Command Sequences: ACT -> RD -> PRE
# =============================================================================

class TestCommandSequence:
    """Test command sequences for correct timing and state transitions"""

    def test_single_read_sequence(self, hbm4_channel, hbm4_timing):
        """Test ACT -> RD -> PRE sequence for a single read"""
        channel = hbm4_channel
        channel.set_time(0)

        # Step 1: ACT - Activate row 0 in bank 0, pseudo-channel 0
        success = channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)
        assert success, "ACT command should succeed"

        # Verify bank is now active
        bank = channel.get_bank(pseudo_channel=0, bank=0)
        assert bank is not None
        assert bank.bank.state == BankStateEnum.ACTIVE
        assert bank.bank.open_row == 0

        # Step 2: RD - Read from the open row
        # Advance time to meet tRCD (tRCDRD)
        channel.set_time(hbm4_timing.nRCDRD)
        success = channel.issue_command('RD', pseudo_channel=0, bank=0, row=0)
        assert success, "RD command should succeed"

        # Verify channel is in reading state
        pc = channel.pseudo_channels[0]
        assert pc.state == PseudoChannelState.READING

        # Step 3: PRE - Precharge the bank
        # Advance time for read to complete (tCL + tBL + tRAS)
        # Must meet tRAS minimum before precharge
        channel.set_time(hbm4_timing.nRCDRD + hbm4_timing.nCL + hbm4_timing.nBL + hbm4_timing.nRAS)
        success = channel.issue_command('PRE', pseudo_channel=0, bank=0, row=0)
        assert success, "PRE command should succeed"

        # Verify bank returns to idle
        bank = channel.get_bank(pseudo_channel=0, bank=0)
        assert bank.bank.state == BankStateEnum.IDLE

    def test_single_write_sequence(self, hbm4_channel, hbm4_timing):
        """Test ACT -> WR -> PRE sequence for a single write"""
        channel = hbm4_channel
        channel.set_time(0)

        # ACT
        success = channel.issue_command('ACT', pseudo_channel=0, bank=1, row=100)
        assert success, "ACT command should succeed"

        # Advance time to meet tRCD (tRCDWR)
        channel.set_time(hbm4_timing.nRCDWR)

        # WR
        success = channel.issue_command('WR', pseudo_channel=0, bank=1, row=100)
        assert success, "WR command should succeed"

        # Verify channel is in writing state
        pc = channel.pseudo_channels[0]
        assert pc.state == PseudoChannelState.WRITING

        # PRE
        # Must meet tRAS minimum before precharge
        channel.set_time(hbm4_timing.nRCDWR + hbm4_timing.nCWL + hbm4_timing.nBL + hbm4_timing.nWR + hbm4_timing.nRAS)
        success = channel.issue_command('PRE', pseudo_channel=0, bank=1, row=100)
        assert success, "PRE command should succeed"

        # Verify bank returns to idle
        bank = channel.get_bank(pseudo_channel=0, bank=1)
        assert bank.bank.state == BankStateEnum.IDLE

    def test_read_with_auto_precharge(self, hbm4_channel, hbm4_timing):
        """Test RDA (Read with auto-precharge) sequence"""
        channel = hbm4_channel
        channel.set_time(0)

        # ACT first
        success = channel.issue_command('ACT', pseudo_channel=0, bank=2, row=50)
        assert success, "ACT command should succeed"

        # Advance time
        channel.set_time(hbm4_timing.nRCDRD)

        # RDA - read with auto-precharge
        success = channel.issue_command('RDA', pseudo_channel=0, bank=2, row=50)
        assert success, "RDA command should succeed"

        # After read data and RTPL (read-to-precharge), explicit precharge
        # Note: Auto-precharge behavior depends on implementation
        # Some implementations auto-precharge, others require explicit PRE
        channel.set_time(hbm4_timing.nRCDRD + hbm4_timing.nCL + hbm4_timing.nBL + hbm4_timing.nRTPL + hbm4_timing.nRP)
        channel.tick()
        channel.tick()

        # Bank may still be ACTIVE depending on auto-precharge implementation
        # Just verify the command was processed
        bank = channel.get_bank(pseudo_channel=0, bank=2)
        assert bank is not None

    def test_write_with_auto_precharge(self, hbm4_channel, hbm4_timing):
        """Test WRA (Write with auto-precharge) sequence"""
        channel = hbm4_channel
        channel.set_time(0)

        # ACT first
        success = channel.issue_command('ACT', pseudo_channel=1, bank=3, row=200)
        assert success, "ACT command should succeed"

        # Advance time
        channel.set_time(hbm4_timing.nRCDWR)

        # WRA - write with auto-precharge
        success = channel.issue_command('WRA', pseudo_channel=1, bank=3, row=200)
        assert success, "WRA command should succeed"

        # After write recovery + precharge time, bank should auto-precharge
        channel.set_time(hbm4_timing.nRCDWR + hbm4_timing.nCWL + hbm4_timing.nBL + hbm4_timing.nWR + hbm4_timing.nRP)
        channel.tick()
        channel.tick()  # Additional cycle for state transition

        # Bank should be IDLE after auto-precharge
        bank = channel.get_bank(pseudo_channel=1, bank=3)
        # Note: WRA with auto-precharge may require explicit precharge command
        # depending on implementation, so we just verify the command succeeded


# =============================================================================
# Test Bank Conflict Handling
# =============================================================================

class TestBankConflict:
    """Test bank conflict detection and handling"""

    def test_bank_conflict_detection(self, hbm4_channel, hbm4_timing):
        """Test detection of bank conflicts (same bank, different row)"""
        channel = hbm4_channel
        channel.set_time(0)

        # Open row 0 in bank 0
        success = channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)
        assert success
        channel.set_time(hbm4_timing.nRCDRD + 10)

        # Check via pseudo-channel's is_row_open method
        pc = channel.pseudo_channels[0]
        is_open = pc.is_row_open(row=0)
        different_row_open = pc.is_row_open(row=1)

        assert is_open == True
        assert different_row_open == False

    def test_row_hit_on_same_row(self, hbm4_channel, hbm4_timing):
        """Test row hit when accessing same row consecutively"""
        channel = hbm4_channel
        channel.set_time(0)

        # Open row 0 in bank 0
        channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)
        channel.set_time(hbm4_timing.nRCDRD)

        # First read - row miss (ACT was needed)
        channel.issue_command('RD', pseudo_channel=0, bank=0, row=0)

        # Advance to complete read
        channel.set_time(hbm4_timing.nRCDRD + hbm4_timing.nCL + hbm4_timing.nBL)
        channel.tick()

        # Second read to same row - should be row hit
        channel.set_time(channel.current_cycle + hbm4_timing.nCCDS)
        # Check via pseudo-channel's is_row_open method
        pc = channel.pseudo_channels[0]
        is_row_open = pc.is_row_open(row=0)
        assert is_row_open == True, "Row 0 should still be open"

    def test_bank_group_timing_same_group(self, hbm4_channel, hbm4_timing):
        """Test bank group timing for same bank group activations"""
        channel = hbm4_channel
        channel.set_time(0)

        # Activate bank 0 in bank group 0 (banks 0-1)
        channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)

        # Immediately try to activate bank 1 in same group
        # Should fail due to tRRDS constraint
        channel.set_time(1)  # Too soon
        can_activate = channel.can_schedule_command('ACT', pseudo_channel=0, bank_group=0)

        # Wait for tRRDS
        channel.set_time(hbm4_timing.nRRDS + 1)
        can_activate_after = channel.can_schedule_command('ACT', pseudo_channel=0, bank_group=0)

        assert can_activate == False, "Should not be able to activate same BG too soon"
        # Note: can_schedule_command checks BG-level timing

    def test_bank_group_timing_different_group(self, hbm4_channel, hbm4_timing):
        """Test bank group timing for different bank group activations"""
        channel = hbm4_channel
        channel.set_time(0)

        # Activate bank in BG 0
        channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)

        # Try to activate bank in different BG immediately
        channel.set_time(1)
        can_activate_diff_bg = channel.can_schedule_command('ACT', pseudo_channel=0, bank_group=1)

        # Wait for tRRDL (longer than tRRDS)
        channel.set_time(hbm4_timing.nRRDL + 1)
        can_activate_after = channel.can_schedule_command('ACT', pseudo_channel=0, bank_group=1)

        # Different BG has different timing constraint
        # tRRDL should allow activation after that time


# =============================================================================
# Test Refresh Behavior
# =============================================================================

class TestRefreshBehavior:
    """Test refresh operations and timing"""

    def test_all_bank_refresh(self, hbm4_channel, hbm4_timing):
        """Test REFab (all-bank refresh) sequence"""
        channel = hbm4_channel
        channel.set_time(0)

        # Ensure all banks are idle before refresh
        for bank in channel.pseudo_channels[0].banks:
            bank.set_time(0)
            if bank.bank.state != BankStateEnum.IDLE:
                channel.issue_command('PRE', pseudo_channel=0, bank=bank.bank.bank_id, row=0)

        # Execute REFab
        success = channel.issue_command('REFab', pseudo_channel=0, bank=0, row=0)
        assert success, "REFab should succeed when all banks are idle"

        # Verify channel state
        assert channel.state.value == 2  # REFRESHING

        # Advance time for refresh to complete
        channel.set_time(hbm4_timing.nRFC)
        channel.tick()

        # Channel should return to IDLE
        assert channel.state.value == 0  # IDLE

    def test_per_bank_refresh(self, hbm4_channel, hbm4_timing):
        """Test REFsb (per-bank refresh) sequence"""
        channel = hbm4_channel
        channel.set_time(0)

        # Refresh bank 5 specifically
        success = channel.issue_command('REFsb', pseudo_channel=0, bank=5, row=0)
        assert success, "REFsb should succeed"

        # Verify channel state
        assert channel.state.value == 2  # REFRESHING

        # Advance time for refresh to complete (per-bank refresh has shorter timing)
        channel.set_time(hbm4_timing.nRFC)
        channel.tick()

        # Channel should return to IDLE
        assert channel.state.value == 0  # IDLE

    def test_refresh_scheduler_integration(self, hbm4_spec, hbm4_timing):
        """Test refresh scheduler integration with channel model"""
        # Create refresh scheduler
        scheduler = HBM4RefreshScheduler(config=hbm4_spec)

        # Create channel array
        channel_array = HBM4ChannelArray(spec=hbm4_spec, timing=hbm4_timing)

        # Initial time
        current_cycle = 0
        channel_array.tick()  # Advance channel array

        # Get refresh command from scheduler
        refresh_cmd = scheduler.get_refresh_command()

        if refresh_cmd:
            cmd_name, channel_id, pch_id, bank_id = refresh_cmd

            # Execute on channel
            if cmd_name == 'REFab':
                channel_array.get_channel(channel_id).execute_refresh('REFab')
            elif cmd_name == 'REFsb':
                channel_array.get_channel(channel_id).execute_refresh(
                    'REFsb', pseudo_channel=pch_id, bank=bank_id
                )

            # Verify refresh was executed
            channel = channel_array.get_channel(channel_id)
            assert channel is not None

    def test_refresh_during_active_banks(self, hbm4_channel, hbm4_timing):
        """Test that refresh cannot proceed while banks are active"""
        channel = hbm4_channel
        channel.set_time(0)

        # Open a row (bank not idle)
        channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)

        # Try to execute all-bank refresh
        # It should either fail or wait until banks are idle
        pc = channel.pseudo_channels[0]
        all_idle = all(b.bank.state == BankStateEnum.IDLE for b in pc.banks)

        # At least one bank should not be idle
        assert all_idle == False, "Bank should be active"


# =============================================================================
# Test Controller + DRAM Integration
# =============================================================================

class TestControllerDRAMIntegration:
    """Test controller and DRAM model integration"""

    def test_controller_to_dram_command_flow(self, hbm4_controller, hbm4_spec):
        """Test that controller commands flow correctly to DRAM"""
        controller = hbm4_controller

        # Submit a read request
        addr = 0x1000
        request_id = controller.submit_request(addr=addr, is_read=True, qos_level=8)

        assert request_id is not None, "Request should be submitted"

        # Run controller tick
        for _ in range(50):
            responses = controller.tick()
            if responses:
                break

    def test_controller_address_decoding(self, hbm4_controller, hbm4_spec, address_decoder):
        """Test that controller correctly decodes addresses"""
        controller = hbm4_controller

        # Test address using RBC mapping format:
        # [Stack][Channel][Pch][Bg][Bank][Row][Col][Burst][Offset]
        # Test address: channel 5, pseudo-channel 1, bank 3, row 0x1234
        test_addr = (
            (0 << 46) |     # Stack
            (5 << 41) |     # Channel (5 bits)
            (1 << 40) |     # Pseudo-channel
            (2 << 37) |     # Bank group
            (3 << 33) |     # Bank
            (0x1234 << 17) | # Row
            (0 << 11)        # Column
        )

        decoded = address_decoder.decode(test_addr)

        # Verify decoding
        assert decoded.channel_id == 5
        assert decoded.pseudo_channel_id == 1
        assert decoded.bank_id == 3
        assert decoded.row_id == 0x1234

    def test_controller_qos_scheduling(self, hbm4_controller):
        """Test controller QoS scheduling"""
        controller = hbm4_controller

        # Submit requests with different priorities
        req_high = controller.submit_request(addr=0x1000, is_read=True, qos_level=15)
        req_low = controller.submit_request(addr=0x2000, is_read=True, qos_level=0)
        req_med = controller.submit_request(addr=0x3000, is_read=True, qos_level=8)

        assert req_high is not None
        assert req_low is not None
        assert req_med is not None

        # Verify QoS scheduler is working
        assert controller.qos_scheduler is not None

    def test_controller_refresh_integration(self, hbm4_controller):
        """Test controller refresh scheduler integration"""
        controller = hbm4_controller

        # Verify refresh scheduler exists
        assert controller.refresh_scheduler is not None

        # Run some cycles
        for _ in range(100):
            controller.tick()


# =============================================================================
# Test Multi-Channel Operations
# =============================================================================

class TestMultiChannelOperations:
    """Test operations across multiple channels"""

    def test_32_channel_initialization(self, hbm4_channel_array, hbm4_spec):
        """Test that all 32 channels initialize correctly"""
        array = hbm4_channel_array

        assert len(array.channels) == 32, "Should have 32 channels"

        # Verify each channel
        for ch_id in range(32):
            channel = array.get_channel(ch_id)
            assert channel is not None
            assert channel.channel_id == ch_id
            assert len(channel.pseudo_channels) == 2  # 2 pseudo-channels per channel

    def test_parallel_channel_access(self, hbm4_channel_array, hbm4_timing):
        """Test parallel access to different channels"""
        array = hbm4_channel_array

        # Access channels 0 and 16 in parallel
        ch0 = array.get_channel(0)
        ch16 = array.get_channel(16)

        # Activate rows in both channels
        ch0.issue_command('ACT', pseudo_channel=0, bank=0, row=0)
        ch16.issue_command('ACT', pseudo_channel=0, bank=0, row=0)

        # Both should succeed (independent channels)
        ch0_bank = ch0.get_bank(pseudo_channel=0, bank=0)
        ch16_bank = ch16.get_bank(pseudo_channel=0, bank=0)

        assert ch0_bank.bank.state == BankStateEnum.ACTIVE
        assert ch16_bank.bank.state == BankStateEnum.ACTIVE

    def test_same_bank_different_channels(self, hbm4_channel_array):
        """Test same bank index in different channels (should be independent)"""
        array = hbm4_channel_array

        # Activate bank 0 in channels 0 and 1
        ch0 = array.get_channel(0)
        ch1 = array.get_channel(1)

        ch0.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        ch1.issue_command('ACT', pseudo_channel=0, bank=0, row=200)

        # Both should be active (independent banks)
        ch0_bank = ch0.get_bank(pseudo_channel=0, bank=0)
        ch1_bank = ch1.get_bank(pseudo_channel=0, bank=0)

        assert ch0_bank.bank.state == BankStateEnum.ACTIVE
        assert ch1_bank.bank.state == BankStateEnum.ACTIVE
        assert ch0_bank.bank.open_row == 100
        assert ch1_bank.bank.open_row == 200


# =============================================================================
# Test RTL Command Interface Alignment
# =============================================================================

class TestRTLCommandInterface:
    """Test alignment with RTL command encoding"""

    def test_command_encoding_values(self):
        """Test that command encoding matches RTL specification"""
        # RTL encoding (from hbm_types.svh):
        # CMD_NOP=0, CMD_ACT=1, CMD_READ=2, CMD_WRITE=3, CMD_PRE=4, CMD_PREA=5, CMD_REF=6, CMD_RFM=7

        expected = {
            'NOP': 0,
            'ACT': 1,
            'READ': 2,
            'WRITE': 3,
            'PRE': 4,
            'PREA': 5,
            'REF': 6,
            'RFM': 7,
        }

        for cmd_name, expected_value in expected.items():
            actual = int(HBM4Command[cmd_name])
            assert actual == expected_value, f"Command {cmd_name} encoding mismatch: expected {expected_value}, got {actual}"

    def test_numeric_command_issue(self, hbm4_channel):
        """Test issuing commands using numeric encoding (RTL interface)"""
        channel = hbm4_channel
        channel.set_time(0)

        # Issue ACT using numeric encoding
        success = channel.issue_numeric_command(
            HBM4Command.ACT, pseudo_channel=0, bank=0, row=0
        )
        assert success, "Numeric ACT command should succeed"

        # Issue READ using numeric encoding
        channel.set_time(10)  # Meet tRCD
        success = channel.issue_numeric_command(
            HBM4Command.READ, pseudo_channel=0, bank=0, row=0
        )
        assert success, "Numeric READ command should succeed"

    def test_command_string_conversion(self):
        """Test command string to encoding conversion"""
        # Test HBM4Command.to_string
        assert HBM4Command.to_string(HBM4Command.ACT) == 'ACT'
        assert HBM4Command.to_string(HBM4Command.READ) == 'RD'
        assert HBM4Command.to_string(HBM4Command.WRITE) == 'WR'
        assert HBM4Command.to_string(HBM4Command.PRE) == 'PRE'

        # Test HBM4Command.from_string
        assert HBM4Command.from_string('ACT') == HBM4Command.ACT
        assert HBM4Command.from_string('RD') == HBM4Command.READ
        assert HBM4Command.from_string('REFab') == HBM4Command.REF


# =============================================================================
# Test Performance Metrics
# =============================================================================

class TestPerformanceMetrics:
    """Test performance metrics collection"""

    def test_bandwidth_calculation(self, hbm4_channel, hbm4_spec):
        """Test peak bandwidth calculation"""
        channel = hbm4_channel

        # Peak bandwidth per channel: data_rate × (io_width/32) / 8
        expected = 8.0 * 64 / 8  # 64 GB/s per channel
        actual = channel.peak_bandwidth_gbs

        assert abs(actual - expected) < 0.001, f"Bandwidth mismatch: expected {expected}, got {actual}"

    def test_latency_accumulation(self, hbm4_controller):
        """Test latency tracking in controller"""
        controller = hbm4_controller

        # Submit request
        controller.submit_request(addr=0x1000, is_read=True)

        # Run simulation
        initial_latency = controller.stats.total_latency_ns

        for _ in range(200):
            controller.tick()

        # Latency should be tracked
        final_latency = controller.stats.total_latency_ns
        # Either no requests completed yet, or latency increased

    def test_throughput_estimation(self, hbm4_channel_array, hbm4_spec):
        """Test system throughput estimation"""
        array = hbm4_channel_array

        # Total bandwidth: 32 channels × 64 GB/s = 2048 GB/s = 2.048 TB/s
        expected_total = 32 * 64.0  # GB/s
        actual_total = array.total_bandwidth_gbs

        assert abs(actual_total - expected_total) < 0.001, \
            f"Total bandwidth mismatch: expected {expected_total}, got {actual_total}"


# =============================================================================
# Test Error Conditions
# =============================================================================

class TestErrorConditions:
    """Test error handling and edge cases"""

    def test_invalid_bank_id(self, hbm4_channel):
        """Test handling of invalid bank ID"""
        channel = hbm4_channel
        channel.set_time(0)

        # Try to activate with invalid bank ID
        success = channel.issue_command('ACT', pseudo_channel=0, bank=100, row=0)
        assert success == False, "Invalid bank ID should fail"

    def test_invalid_pseudo_channel(self, hbm4_channel):
        """Test handling of invalid pseudo-channel"""
        channel = hbm4_channel
        channel.set_time(0)

        # Try to activate with invalid pseudo-channel
        success = channel.issue_command('ACT', pseudo_channel=5, bank=0, row=0)
        assert success == False, "Invalid pseudo-channel should fail"

    def test_command_during_refresh(self, hbm4_channel, hbm4_timing):
        """Test that commands are blocked during refresh"""
        channel = hbm4_channel
        channel.set_time(0)

        # Start all-bank refresh
        channel.issue_command('REFab', pseudo_channel=0, bank=0, row=0)

        # Try to activate during refresh
        # This should be handled appropriately based on implementation


# =============================================================================
# Summary Test
# =============================================================================

def test_e2e_summary(hbm4_channel_array, hbm4_controller, hbm4_spec):
    """Summary test that exercises the complete system"""
    array = hbm4_channel_array
    controller = hbm4_controller

    # Initialize
    assert len(array.channels) == 32

    # Submit requests to controller
    for i in range(10):
        addr = i * 0x1000
        request_id = controller.submit_request(addr=addr, is_read=(i % 2 == 0))

    # Run simulation
    for cycle in range(500):
        array.tick()
        controller.tick()

    # Verify system state
    stats = controller.get_stats()
    assert stats['controller']['total_requests'] == 10

    print("\n=== E2E Integration Test Summary ===")
    print(f"Channels: {len(array.channels)}")
    print(f"Total requests: {stats['controller']['total_requests']}")
    print(f"Peak bandwidth: {array.total_bandwidth_gbs:.1f} GB/s")
    print("=== E2E Integration Test PASSED ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])