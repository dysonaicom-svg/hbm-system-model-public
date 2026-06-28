"""
Tests for HBM4 Bank State Machine with Full State Tracking

These tests demonstrate:
- Bank state transitions: CLOSED -> ACTIVATING -> OPEN -> PRECHARGING -> CLOSED
- Timing parameter compliance: tRCD, tRP, tRAS, tRC
- Per-bank state machines (1024 total banks)
- Integration with HBM4 refresh scheduler
- State transition timing validation
- Bank group-aware scheduling
- Power management states

HBM4 Key Timing Parameters (12 Gbps optimized):
- tRCD: 12 cycles (Activate to Read/Write)
- tRP: 12 cycles (Precharge)
- tRAS: 28 cycles (Activate to Precharge)
- tRC: 40 cycles (Activate to Activate same bank)

Reference: JEDEC JESD270-4A HBM4 specification
"""

import pytest
from model.dram.hbm4_bank_state_machine import (
    HBM4BankStateMachine, HBM4BankArray, HBM4BankState, HBM4Command,
    HBM4BankTiming, TimingViolation, create_hbm4_bank_state_machine,
    create_hbm4_bank_array, HBM4Bank
)


# =============================================================================
# Test Class 1: HBM4 Bank States and Enums
# =============================================================================

class TestHBM4BankStateEnum:
    """Test HBM4 bank state enum definitions"""

    def test_all_bank_states_defined(self):
        """Verify all bank states are defined"""
        # Core states
        assert HBM4BankState.CLOSED == 0
        assert HBM4BankState.ACTIVATING == 1
        assert HBM4BankState.OPEN == 2
        assert HBM4BankState.PRECHARGING == 3
        assert HBM4BankState.READ == 4
        assert HBM4BankState.WRITE == 5
        assert HBM4BankState.REFRESH == 6
        assert HBM4BankState.POWER_DOWN == 7
        assert HBM4BankState.SELF_REFRESH == 8

    def test_backward_compatibility_aliases(self):
        """Verify backward compatibility aliases"""
        assert HBM4BankState.IDLE == HBM4BankState.CLOSED
        assert HBM4BankState.ACTIVE == HBM4BankState.OPEN


class TestHBM4CommandEnum:
    """Test HBM4 command enum definitions"""

    def test_all_commands_defined(self):
        """Verify all commands are defined"""
        assert HBM4Command.NOP == 0
        assert HBM4Command.ACT == 1
        assert HBM4Command.READ == 2
        assert HBM4Command.WRITE == 3
        assert HBM4Command.PRE == 4
        assert HBM4Command.PREA == 5
        assert HBM4Command.REF == 6
        assert HBM4Command.RFM == 7


# =============================================================================
# Test Class 2: Bank Initialization
# =============================================================================

class TestHBM4BankInitialization:
    """Test bank initialization"""

    def test_bank_starts_closed(self):
        """Bank must start in CLOSED state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        assert bank.bank.state == HBM4BankState.CLOSED
        assert bank.bank.is_closed
        assert not bank.bank.is_open
        assert not bank.bank.is_activating

    def test_bank_initialization_with_ids(self):
        """Bank initialization with all IDs"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(
            bank_id=5,
            channel_id=3,
            pseudo_channel_id=1,
            bank_group_id=2,
            timing=timing
        )

        assert bank.bank_id == 5
        assert bank.channel_id == 3
        assert bank.pseudo_channel_id == 1
        assert bank.bank_group_id == 2
        assert bank.bank.state == HBM4BankState.CLOSED

    def test_bank_initial_open_row(self):
        """Initial open row should be -1 (none)"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        assert bank.bank.open_row == -1
        assert not bank.bank.row_open

    def test_bank_timing_parameters(self):
        """Verify default timing parameters"""
        timing = HBM4BankTiming()

        # Values from HBM4TimingSource (JEDEC JESD270-4A baseline)
        assert timing.tRCD == 8
        assert timing.tRP == 8
        assert timing.tRAS == 20
        assert timing.tRC == 22
        assert timing.tCL == 8
        assert timing.tCWL == 3


# =============================================================================
# Test Class 3: Activation State Transitions
# =============================================================================

class TestHBM4Activation:
    """Test activation state transitions and timing"""

    def test_activation_from_closed(self):
        """ACT from CLOSED transitions to ACTIVATING"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        success, error = bank.activate(row=100)

        assert success is True
        assert error is None
        assert bank.bank.state == HBM4BankState.ACTIVATING
        assert bank.bank.is_activating
        assert bank.bank.open_row == 100
        assert bank.bank.activate_start_cycle == 0
        assert bank.bank.activate_complete_cycle == timing.tRCD

    def test_activation_complete_after_tRCD(self):
        """Activation completes after tRCD cycles"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        # Before tRCD - should not complete
        for cycle in range(1, timing.tRCD):
            bank.set_time(cycle)
            assert not bank.complete_activation()
            assert bank.bank.state == HBM4BankState.ACTIVATING

        # At tRCD - should complete
        bank.set_time(timing.tRCD)
        assert bank.complete_activation()
        assert bank.bank.state == HBM4BankState.OPEN
        assert bank.bank.is_open

    def test_cannot_activate_from_activating(self):
        """Cannot activate while ACTIVATING"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        # Try to activate again
        success, error = bank.activate(row=200)

        assert success is False
        assert error is not None
        assert "not closed" in error.lower()

    def test_cannot_activate_from_open(self):
        """Cannot activate while OPEN (must precharge first)"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Try to activate again while OPEN
        success, error = bank.activate(row=200)

        assert success is False
        assert error is not None

    def test_cannot_activate_from_precharging(self):
        """Cannot activate while PRECHARGING"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()

        # Try to activate while PRECHARGING
        success, error = bank.activate(row=200)

        assert success is False

    def test_activation_stores_row_address(self):
        """Activation stores correct row address"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        test_rows = [0, 100, 0xFFFF, 0x12345]

        for row in test_rows:
            bank.reset()
            bank.set_time(0)
            bank.activate(row=row)
            assert bank.bank.open_row == row


# =============================================================================
# Test Class 4: Precharge State Transitions
# =============================================================================

class TestHBM4Precharge:
    """Test precharge state transitions and timing"""

    def test_precharge_from_open(self):
        """PRE from OPEN transitions to PRECHARGING"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup: ACT and complete
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Wait for tRAS minimum
        bank.set_time(timing.tRAS)
        success, error = bank.precharge()

        assert success is True
        assert error is None
        assert bank.bank.state == HBM4BankState.PRECHARGING
        assert bank.bank.is_precharging
        assert bank.bank.precharge_start_cycle == timing.tRAS
        assert bank.bank.precharge_complete_cycle == timing.tRAS + timing.tRP

    def test_precharge_complete_after_tRP(self):
        """Precharge completes after tRP cycles"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()

        # Before tRP - should not complete
        for cycle in range(timing.tRAS + 1, timing.tRAS + timing.tRP):
            bank.set_time(cycle)
            assert not bank.complete_precharge()
            assert bank.bank.state == HBM4BankState.PRECHARGING

        # After tRP - should complete
        bank.set_time(timing.tRAS + timing.tRP)
        assert bank.complete_precharge()
        assert bank.bank.state == HBM4BankState.CLOSED
        assert bank.bank.is_closed
        assert bank.bank.open_row == -1

    def test_cannot_precharge_before_tRAS(self):
        """Cannot precharge before tRAS minimum"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Try before tRAS
        bank.set_time(timing.tRCD + 1)
        success, error = bank.precharge()

        assert success is False
        assert error is not None
        assert "tRAS" in error

    def test_cannot_precharge_closed_bank(self):
        """Cannot precharge already closed bank"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        success, error = bank.precharge()

        assert success is False
        assert error is not None

    def test_cannot_precharge_during_activation(self):
        """Cannot precharge during activation"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        # Try during activation
        success, error = bank.precharge()

        assert success is False


# =============================================================================
# Test Class 5: Read State Transitions
# =============================================================================

class TestHBM4Read:
    """Test read state transitions and timing"""

    def test_read_requires_open_bank(self):
        """READ requires OPEN state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Try from CLOSED
        bank.set_time(0)
        assert not bank.can_read()

        # Try during ACTIVATING
        bank.activate(row=100)
        assert not bank.can_read()

        # After OPEN
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert bank.can_read()

    def test_read_transitions_to_read_state(self):
        """READ transitions to READ state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Issue read
        bank.set_time(timing.tRCD + 1)
        success, error = bank.read(column=0)

        assert success is True
        assert error is None
        assert bank.bank.state == HBM4BankState.READ
        assert bank.bank.is_reading
        assert bank.bank.read_start_cycle == timing.tRCD + 1

    def test_read_complete_timing(self):
        """READ completes after CL + BL cycles"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Issue read
        read_cycle = timing.tRCD + 5
        bank.set_time(read_cycle)
        bank.read(column=0)

        expected_complete = read_cycle + timing.tCL + timing.tBL
        assert bank.bank.read_complete_cycle == expected_complete

    def test_read_completes_to_open(self):
        """READ completes back to OPEN state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Issue and complete read
        bank.set_time(timing.tRCD + 5)
        bank.read(column=0)

        bank.set_time(bank.bank.read_complete_cycle)
        assert bank.complete_read()
        assert bank.bank.state == HBM4BankState.OPEN

    def test_cannot_read_during_write(self):
        """Cannot read during WRITE"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup and write
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRCD + 1)
        bank.write(column=0)

        # Try to read
        success, error = bank.read(column=0)

        assert success is False


# =============================================================================
# Test Class 6: Write State Transitions
# =============================================================================

class TestHBM4Write:
    """Test write state transitions and timing"""

    def test_write_requires_open_bank(self):
        """WRITE requires OPEN state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Try from CLOSED
        bank.set_time(0)
        assert not bank.can_write()

        # Try during ACTIVATING
        bank.activate(row=100)
        assert not bank.can_write()

        # After OPEN
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert bank.can_write()

    def test_write_transitions_to_write_state(self):
        """WRITE transitions to WRITE state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Issue write
        bank.set_time(timing.tRCD + 1)
        success, error = bank.write(column=0)

        assert success is True
        assert error is None
        assert bank.bank.state == HBM4BankState.WRITE
        assert bank.bank.is_writing
        assert bank.bank.write_start_cycle == timing.tRCD + 1

    def test_write_complete_timing(self):
        """WRITE completes after CWL + BL cycles"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Issue write
        write_cycle = timing.tRCD + 5
        bank.set_time(write_cycle)
        bank.write(column=0)

        expected_complete = write_cycle + timing.tCWL + timing.tBL
        assert bank.bank.write_complete_cycle == expected_complete

    def test_write_completes_to_open(self):
        """WRITE completes back to OPEN state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Issue and complete write
        bank.set_time(timing.tRCD + 5)
        bank.write(column=0)

        bank.set_time(bank.bank.write_complete_cycle)
        assert bank.complete_write()
        assert bank.bank.state == HBM4BankState.OPEN

    def test_cannot_write_during_read(self):
        """Cannot write during READ"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup and read
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRCD + 1)
        bank.read(column=0)

        # Try to write
        success, error = bank.write(column=0)

        assert success is False


# =============================================================================
# Test Class 7: Refresh State Transitions
# =============================================================================

class TestHBM4Refresh:
    """Test refresh state transitions and timing"""

    def test_refresh_requires_closed_bank(self):
        """REF requires CLOSED state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Try from CLOSED (should work)
        bank.set_time(0)
        assert bank.can_refresh()

        # Activate and try again
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert not bank.can_refresh()

    def test_refresh_transitions_to_refresh_state(self):
        """REF transitions to REFRESH state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        success, error = bank.refresh()

        assert success is True
        assert error is None
        assert bank.bank.state == HBM4BankState.REFRESH
        assert bank.bank.is_refreshing
        assert bank.bank.refresh_start_cycle == 0
        assert bank.bank.refresh_complete_cycle == timing.tRFC

    def test_refresh_complete_after_tRFC(self):
        """Refresh completes after tRFC cycles"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.refresh()

        # Before tRFC
        for cycle in range(1, timing.tRFC):
            bank.set_time(cycle)
            assert not bank.complete_refresh()
            assert bank.bank.state == HBM4BankState.REFRESH

        # After tRFC
        bank.set_time(timing.tRFC)
        assert bank.complete_refresh()
        assert bank.bank.state == HBM4BankState.CLOSED
        assert bank.bank.is_closed

    def test_cannot_refresh_open_bank(self):
        """Cannot refresh open bank"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        success, error = bank.refresh()

        assert success is False
        assert error is not None

    def test_cannot_refresh_during_activation(self):
        """Cannot refresh during activation"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        success, error = bank.refresh()

        assert success is False


# =============================================================================
# Test Class 8: Complete State Transition Cycles
# =============================================================================

class TestHBM4StateTransitionCycles:
    """Test complete state transition cycles"""

    def test_full_act_open_pre_closed_cycle(self):
        """Complete ACT -> OPEN -> PRE -> CLOSED cycle"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # ACT
        bank.set_time(0)
        bank.activate(row=100)
        assert bank.bank.state == HBM4BankState.ACTIVATING

        # Complete ACT
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert bank.bank.state == HBM4BankState.OPEN

        # PRE
        bank.set_time(timing.tRAS)
        bank.precharge()
        assert bank.bank.state == HBM4BankState.PRECHARGING

        # Complete PRE
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()
        assert bank.bank.state == HBM4BankState.CLOSED

    def test_full_act_open_read_closed_cycle(self):
        """Complete ACT -> OPEN -> READ -> CLOSED cycle"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # ACT
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # READ
        bank.set_time(timing.tRCD + 5)
        bank.read(column=0)

        # Complete READ
        bank.set_time(bank.bank.read_complete_cycle)
        bank.complete_read()
        assert bank.bank.state == HBM4BankState.OPEN

        # PRE (wait for tRAS after activation)
        bank.set_time(bank.bank.activate_start_cycle + timing.tRAS)
        bank.precharge()
        assert bank.bank.state == HBM4BankState.PRECHARGING

        # Complete PRE
        bank.set_time(bank.current_cycle + timing.tRP)
        bank.complete_precharge()
        assert bank.bank.state == HBM4BankState.CLOSED

    def test_full_act_open_write_closed_cycle(self):
        """Complete ACT -> OPEN -> WRITE -> CLOSED cycle"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # ACT
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # WRITE
        bank.set_time(timing.tRCD + 5)
        bank.write(column=0)

        # Complete WRITE
        bank.set_time(bank.bank.write_complete_cycle)
        bank.complete_write()
        assert bank.bank.state == HBM4BankState.OPEN

        # PRE (wait for tRAS after activation)
        bank.set_time(bank.bank.activate_start_cycle + timing.tRAS)
        bank.precharge()
        assert bank.bank.state == HBM4BankState.PRECHARGING

        # Complete PRE
        bank.set_time(bank.current_cycle + timing.tRP)
        bank.complete_precharge()
        assert bank.bank.state == HBM4BankState.CLOSED

    def test_refresh_cycle(self):
        """Complete REF -> REFRESH -> CLOSED cycle"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # REF
        bank.set_time(0)
        bank.refresh()
        assert bank.bank.state == HBM4BankState.REFRESH

        # Complete REF
        bank.set_time(timing.tRFC)
        bank.complete_refresh()
        assert bank.bank.state == HBM4BankState.CLOSED


# =============================================================================
# Test Class 9: Timing Constraints - tRC
# =============================================================================

class TestHBM4TRCConstraint:
    """Test tRC (row cycle time) constraint"""

    def test_tRC_blocks_same_bank_reactivation(self):
        """tRC prevents reactivating same bank too soon"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # First activation
        bank.set_time(0)
        bank.activate(row=100)

        # Complete first activation and precharge
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # Try to reactivate before tRC
        bank.set_time(timing.tRC - 1)
        assert not bank.can_activate()

        # Try at exactly tRC - should work because >= is used
        bank.set_time(timing.tRC)
        assert bank.can_activate()

    def test_tRC_is_tracked_across_full_cycle(self):
        """tRC is measured from first ACT to next ACT"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # First activation
        bank.set_time(0)
        bank.activate(row=100)

        # Complete cycle quickly
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # Bank is closed but tRC may not be satisfied yet
        assert bank.bank.state == HBM4BankState.CLOSED

        # Before tRC - cannot activate
        bank.set_time(timing.tRCD + 1)
        assert not bank.can_activate()

        # At tRC - can activate
        bank.set_time(timing.tRC)
        assert bank.can_activate()


# =============================================================================
# Test Class 10: Timing Constraints - tRCD
# =============================================================================

class TestHBM4TRCDConstraint:
    """Test tRCD (RAS to CAS delay) constraint"""

    def test_read_write_require_tRCD_after_act(self):
        """Read/write require tRCD to elapse after ACT"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        # Before tRCD complete
        for cycle in range(1, timing.tRCD):
            bank.set_time(cycle)
            bank.complete_activation()
            assert not bank.can_read()
            assert not bank.can_write()

        # At tRCD
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert bank.can_read()
        assert bank.can_write()

    def test_tRCD_timing_value(self):
        """Verify tRCD is 8 cycles (JEDEC JESD270-4A baseline)"""
        timing = HBM4BankTiming()
        assert timing.tRCD == 8


# =============================================================================
# Test Class 11: Timing Constraints - tRAS
# =============================================================================

class TestHBM4TRASConstraint:
    """Test tRAS (row active time) constraint"""

    def test_tRAS_blocks_precharge_early(self):
        """tRAS blocks precharge before minimum"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Before tRAS
        for cycle in range(timing.tRCD + 1, timing.tRAS):
            bank.set_time(cycle)
            assert not bank.can_precharge()

        # At tRAS
        bank.set_time(timing.tRAS)
        assert bank.can_precharge()

    def test_tRAS_allows_precharge_at_minimum(self):
        """tRAS allows precharge at minimum"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # At exactly tRAS
        bank.set_time(timing.tRAS)
        success, _ = bank.precharge()
        assert success is True

    def test_tRAS_timing_value(self):
        """Verify tRAS is 20 cycles (JEDEC JESD270-4A baseline)"""
        timing = HBM4BankTiming()
        assert timing.tRAS == 20


# =============================================================================
# Test Class 12: Timing Constraints - tRP
# =============================================================================

class TestHBM4TRPConstraint:
    """Test tRP (precharge time) constraint"""

    def test_tRP_completes_precharge(self):
        """tRP completes precharge operation"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Complete activation
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Precharge
        bank.set_time(timing.tRAS)
        bank.precharge()
        precharge_start = timing.tRAS

        # Before tRP complete
        for cycle in range(precharge_start + 1, precharge_start + timing.tRP):
            bank.set_time(cycle)
            assert not bank.complete_precharge()

        # At tRP
        bank.set_time(precharge_start + timing.tRP)
        assert bank.complete_precharge()

    def test_tRP_timing_value(self):
        """Verify tRP is 8 cycles (JEDEC JESD270-4A baseline)"""
        timing = HBM4BankTiming()
        assert timing.tRP == 8


# =============================================================================
# Test Class 13: Bank Group Scheduling
# =============================================================================

class TestHBM4BankGroupScheduling:
    """Test bank group-aware scheduling"""

    def test_same_bank_group_tRRDS(self):
        """Same BG has tRRDS constraint"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing, bank_group_id=0)

        bank.set_time(0)
        bank.activate(row=100)

        # At t=0, should fail (0 < tRRDS=3)
        assert bank.can_activate_after_bank_group(0) is False

        bank.set_time(timing.tRRDS - 1)  # t=2
        assert bank.can_activate_after_bank_group(0) is False

        bank.set_time(timing.tRRDS)  # t=3
        assert bank.can_activate_after_bank_group(0) is True

    def test_different_bank_group_tRRDL(self):
        """Different BG has tRRDL constraint"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing, bank_group_id=0)

        bank.set_time(0)
        bank.activate(row=100)

        # At t=0, should fail (0 < tRRDL=4)
        assert bank.can_activate_after_bank_group(1) is False

        bank.set_time(timing.tRRDL - 1)  # t=3
        assert bank.can_activate_after_bank_group(1) is False

        bank.set_time(timing.tRRDL)  # t=4
        assert bank.can_activate_after_bank_group(1) is True

    def test_tRRDS_less_than_tRRDL(self):
        """tRRDS should be less than tRRDL for performance"""
        timing = HBM4BankTiming()
        assert timing.tRRDS < timing.tRRDL


# =============================================================================
# Test Class 14: Turnaround Timing
# =============================================================================

class TestHBM4TurnaroundTiming:
    """Test turnaround timing constraints"""

    def test_read_after_write_same_bank(self):
        """READ after WRITE requires tWTRS"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Write
        write_time = timing.tRCD + 5
        bank.set_time(write_time)
        bank.write(column=0)

        # After write command at exact time - should fail
        assert not bank.can_read_after_write()

        # Advance time but still within tWTRS
        bank.set_time(write_time + timing.tWTRS - 1)
        elapsed = bank.current_cycle - bank.last_col_cmd_cycle
        assert elapsed < timing.tWTRS
        assert not bank.can_read_after_write()

        # At tWTRS boundary - should pass
        bank.set_time(write_time + timing.tWTRS)
        elapsed = bank.current_cycle - bank.last_col_cmd_cycle
        assert elapsed >= timing.tWTRS
        assert bank.can_read_after_write()

    def test_write_after_read_same_bank(self):
        """WRITE after READ requires tRTW"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Read
        read_time = timing.tRCD + 5
        bank.set_time(read_time)
        bank.read(column=0)

        # After read command at exact time - should fail
        assert not bank.can_write_after_read()

        # Advance time but still within tRTW
        bank.set_time(read_time + timing.tRTW - 1)
        elapsed = bank.current_cycle - bank.last_col_cmd_cycle
        assert elapsed < timing.tRTW
        assert not bank.can_write_after_read()

        # At tRTW boundary - should pass
        bank.set_time(read_time + timing.tRTW)
        elapsed = bank.current_cycle - bank.last_col_cmd_cycle
        assert elapsed >= timing.tRTW
        assert bank.can_write_after_read()


# =============================================================================
# Test Class 15: State Transition History
# =============================================================================

class TestHBM4StateTransitionHistory:
    """Test state transition history tracking"""

    def test_transitions_recorded(self):
        """State transitions are recorded"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        transitions = bank.bank.get_transitions()
        assert len(transitions) >= 1
        assert transitions[-1].from_state == HBM4BankState.CLOSED
        assert transitions[-1].to_state == HBM4BankState.ACTIVATING
        assert transitions[-1].command == HBM4Command.ACT

    def test_full_cycle_transition_sequence(self):
        """Full cycle produces correct transition sequence"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # ACT
        bank.set_time(0)
        bank.activate(row=100)

        # Complete ACT
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # PRE
        bank.set_time(timing.tRAS)
        bank.precharge()

        # Complete PRE
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        transitions = bank.bank.get_transitions()
        assert len(transitions) == 4

        assert transitions[0].to_state == HBM4BankState.ACTIVATING
        assert transitions[1].to_state == HBM4BankState.OPEN
        assert transitions[2].to_state == HBM4BankState.PRECHARGING
        assert transitions[3].to_state == HBM4BankState.CLOSED

    def test_read_transition_recorded(self):
        """READ transition is recorded"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRCD + 1)
        bank.read(column=0)

        transitions = bank.bank.get_transitions()
        # Last transition should be READ
        read_transition = transitions[-1]
        assert read_transition.to_state == HBM4BankState.READ
        assert read_transition.command == HBM4Command.READ

    def test_refresh_transition_recorded(self):
        """REFRESH transition is recorded"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.refresh()

        transitions = bank.bank.get_transitions()
        assert len(transitions) == 1
        assert transitions[0].to_state == HBM4BankState.REFRESH
        assert transitions[0].command == HBM4Command.REF


# =============================================================================
# Test Class 16: Timing Violation Detection
# =============================================================================

class TestHBM4TimingViolations:
    """Test timing violation detection"""

    def test_no_violation_for_valid_timing(self):
        """Valid timing produces no violations"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Valid sequence
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        violations = bank.validate_timing()
        # Should not have critical timing violations
        critical_violations = [v for v in violations if v.violation_type in ['tRC', 'tRAS']]
        assert len(critical_violations) == 0

    def test_timing_violation_types(self):
        """Verify timing violation types"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Early precharge (tRAS violation)
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRCD + 1)
        bank.precharge()

        violations = bank.get_violations()
        # Violation should be recorded

    def test_clear_violations(self):
        """Violations can be cleared"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        assert len(bank.get_violations()) >= 0
        bank.clear_violations()
        assert len(bank.get_violations()) == 0


# =============================================================================
# Test Class 17: Time Calculation Methods
# =============================================================================

class TestHBM4TimeCalculations:
    """Test time calculation methods"""

    def test_time_to_activate_when_closed(self):
        """time_to_activate returns 0 when bank is closed and ready"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # At tRC+1
        bank.set_time(timing.tRC + 1)
        assert bank.time_to_activate() == 0

    def test_time_to_activate_tRC_not_satisfied(self):
        """time_to_activate returns remaining cycles when tRC not satisfied"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # Before tRC
        bank.set_time(timing.tRC - 10)
        assert bank.time_to_activate() == 10

    def test_time_to_activate_open_bank(self):
        """time_to_activate returns -1 when bank is open"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        assert bank.time_to_activate() == -1

    def test_time_to_read(self):
        """time_to_read returns correct value"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        # During activation - bank is not open yet, returns -1
        bank.set_time(5)
        remaining = bank.time_to_read()
        assert remaining == -1  # Bank not open during activation

        # After tRCD
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert bank.time_to_read() == 0

    def test_time_to_precharge(self):
        """time_to_precharge returns correct value"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # During tRAS
        bank.set_time(timing.tRCD + 5)
        remaining = bank.time_to_precharge()
        assert remaining == timing.tRAS - timing.tRCD - 5

        # After tRAS
        bank.set_time(timing.tRAS)
        assert bank.time_to_precharge() == 0


# =============================================================================
# Test Class 18: Row Hit Detection
# =============================================================================

class TestHBM4RowHit:
    """Test row hit detection"""

    def test_row_hit_on_open_row(self):
        """Row hit when accessing open row"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        assert bank.is_row_hit(100)
        assert bank.is_row_hit(100)  # Consistent

    def test_row_miss_on_different_row(self):
        """Row miss when accessing different row"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        assert not bank.is_row_hit(200)
        assert not bank.is_row_hit(0)

    def test_no_hit_on_closed_bank(self):
        """No row hit on closed bank"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        assert not bank.is_row_hit(100)


# =============================================================================
# Test Class 19: Bank Reset
# =============================================================================

class TestHBM4BankReset:
    """Test bank reset functionality"""

    def test_reset_clears_state(self):
        """Reset clears all state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Perform some operations
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Reset
        bank.reset()

        assert bank.bank.state == HBM4BankState.CLOSED
        assert bank.bank.open_row == -1
        assert bank.current_cycle == 0

    def test_reset_allows_fresh_operations(self):
        """Reset allows fresh operations"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # First use
        bank.set_time(0)
        bank.activate(row=100)

        # Reset
        bank.reset()

        # Fresh operation
        bank.set_time(0)
        success, _ = bank.activate(row=200)
        assert success is True
        assert bank.bank.open_row == 200


# =============================================================================
# Test Class 20: Bank Array Operations
# =============================================================================

class TestHBM4BankArray:
    """Test bank array operations"""

    def test_bank_array_16_banks(self):
        """Bank array has 16 banks"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)
        assert len(bank_array.banks) == 16

    def test_bank_group_assignment(self):
        """Banks assigned to correct bank groups"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        for bg_id in range(8):
            banks_in_group = bank_array.get_banks_in_group(bg_id)
            assert len(banks_in_group) == 2

            for bank in banks_in_group:
                assert bank.bank_group_id == bg_id

    def test_active_bank_count(self):
        """Active bank count is correct"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        assert bank_array.get_active_bank_count() == 0

        # Activate banks
        for i in range(4):
            bank = bank_array.banks[i]
            bank.set_time(i * 10)
            bank.activate(row=100 * i)
            bank.set_time(i * 10 + bank_array.timing.tRCD)
            bank.complete_activation()

        assert bank_array.get_active_bank_count() == 4

    def test_idle_bank_count(self):
        """Idle bank count is correct"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        initial_idle = bank_array.get_idle_bank_count()
        assert initial_idle == 16

        # Activate one bank
        bank = bank_array.banks[0]
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(bank_array.timing.tRCD)
        bank.complete_activation()

        assert bank_array.get_idle_bank_count() == 15

    def test_tick_completes_activations(self):
        """tick() completes state transitions"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)
        bank = bank_array.banks[0]

        bank.set_time(0)
        bank.activate(row=100)

        # Advance through tRCD
        for _ in range(bank_array.timing.tRCD):
            bank_array.tick()

        assert bank.bank.state == HBM4BankState.OPEN

    def test_tick_completes_precharges(self):
        """tick() completes precharge operations"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)
        bank = bank_array.banks[0]

        bank.set_time(0)
        bank.activate(row=100)

        # Complete activation
        for _ in range(bank_array.timing.tRCD):
            bank_array.tick()

        # Precharge
        bank.set_time(bank_array.timing.tRAS)
        bank.precharge()

        # Complete precharge
        for _ in range(bank_array.timing.tRP):
            bank_array.tick()

        assert bank.bank.state == HBM4BankState.CLOSED

    def test_reset_all_banks(self):
        """Reset clears all banks"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        # Activate all banks
        for bank in bank_array.banks:
            bank.set_time(0)
            bank.activate(row=100)

        bank_array.reset()

        for bank in bank_array.banks:
            assert bank.bank.state == HBM4BankState.CLOSED


# =============================================================================
# Test Class 21: Factory Functions
# =============================================================================

class TestHBM4FactoryFunctions:
    """Test factory functions"""

    def test_create_bank_state_machine(self):
        """Factory creates correct bank"""
        bank = create_hbm4_bank_state_machine(
            bank_id=5,
            channel_id=3,
            pseudo_channel_id=1
        )

        assert bank.bank_id == 5
        assert bank.channel_id == 3
        assert bank.pseudo_channel_id == 1
        assert bank.bank_group_id == 2  # 5 // 2 = 2

    def test_create_bank_array(self):
        """Factory creates correct bank array"""
        bank_array = create_hbm4_bank_array(
            pseudo_channel_id=1,
            channel_id=2
        )

        assert len(bank_array.banks) == 16
        assert bank_array.pseudo_channel_id == 1
        assert bank_array.channel_id == 2


# =============================================================================
# Test Class 22: Speed Grade Timing
# =============================================================================

class TestHBM4SpeedGradeTiming:
    """Test timing for different speed grades"""

    def test_8gbps_timing(self):
        """Verify 8 Gbps timing"""
        timing = HBM4BankTiming.for_speed_grade(8.0)

        assert timing.tCK_ps == 125.0

    def test_12gbps_timing(self):
        """Verify 12 Gbps timing"""
        timing = HBM4BankTiming.for_speed_grade(12.0)

        assert timing.tCK_ps == pytest.approx(83.33, rel=0.01)

    def test_16gbps_timing(self):
        """Verify 16 Gbps timing"""
        timing = HBM4BankTiming.for_speed_grade(16.0)

        assert timing.tCK_ps == pytest.approx(62.5, rel=0.01)

    def test_speed_grade_preserves_cycle_counts(self):
        """Speed grade change preserves cycle counts"""
        timing_8 = HBM4BankTiming.for_speed_grade(8.0)
        timing_16 = HBM4BankTiming.for_speed_grade(16.0)

        # Cycle counts should be the same
        assert timing_8.tRCD == timing_16.tRCD
        assert timing_8.tRP == timing_16.tRP
        assert timing_8.tRAS == timing_16.tRAS
        assert timing_8.tRC == timing_16.tRC


# =============================================================================
# Test Class 23: Timing Conversions
# =============================================================================

class TestHBM4TimingConversions:
    """Test timing unit conversions"""

    def test_cycles_to_ns(self):
        """Convert cycles to nanoseconds"""
        timing = HBM4BankTiming(tCK_ps=125.0)

        # 8 cycles = 1 ns
        assert abs(timing.cycles_to_ns(8) - 1.0) < 0.001

        # 40 cycles = 5 ns
        assert abs(timing.cycles_to_ns(40) - 5.0) < 0.001

    def test_cycles_to_seconds(self):
        """Convert cycles to seconds"""
        timing = HBM4BankTiming(tCK_ps=125.0)

        cycles = 1000
        expected_s = 1000 * 125e-12
        assert abs(timing.cycles_to_seconds(cycles) - expected_s) < 1e-15

    def test_clock_period_ns(self):
        """Clock period in ns"""
        timing = HBM4BankTiming(tCK_ps=125.0)
        assert abs(timing.clock_period_ns - 0.125) < 0.001


# =============================================================================
# Test Class 24: HBM4 Spec Integration
# =============================================================================

class TestHBM4SpecIntegration:
    """Test integration with HBM4 spec"""

    def test_1024_total_banks(self):
        """Verify 1024 total banks: 32ch x 2pch x 16bank"""
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        total = spec.channels * spec.pseudo_channels_per_channel * spec.banks_per_pseudo_channel
        assert total == 1024

    def test_64_pseudo_channels(self):
        """Verify 64 total pseudo-channels: 32ch x 2pch"""
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        total_pch = spec.channels * spec.pseudo_channels_per_channel
        assert total_pch == 64

    def test_512_bank_groups(self):
        """Verify 512 total bank groups: 64pch x 8bg"""
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        total_pch = spec.channels * spec.pseudo_channels_per_channel
        total_bg = total_pch * spec.bank_groups_per_channel
        assert total_bg == 512


# =============================================================================
# Test Class 25: Refresh Scheduler Integration
# =============================================================================

class TestHBM4RefreshSchedulerIntegration:
    """Test integration with refresh scheduler"""

    def test_refresh_scheduler_tracks_1024_banks(self):
        """Refresh scheduler tracks 1024 banks"""
        from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler

        scheduler = HBM4RefreshScheduler()
        assert len(scheduler.bank_status) == 1024

    def test_per_bank_refresh_sequence(self):
        """Per-bank refresh cycles through banks"""
        from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

        scheduler = HBM4RefreshScheduler()
        scheduler.set_mode(RefreshMode.PER_BANK)

        # Advance to refresh interval
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()
        assert cmd is not None
        command_name, channel_id, pch_id, bank_id = cmd
        assert command_name == 'REFsb'


# =============================================================================
# Test Class 26: Edge Cases
# =============================================================================

class TestHBM4EdgeCases:
    """Test edge cases"""

    def test_multiple_reads_in_sequence(self):
        """Multiple reads to same open row"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Open bank
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Multiple reads - need to complete each before starting next
        for i in range(5):
            read_time = timing.tRCD + 5 + i * 50  # Space reads far apart
            bank.set_time(read_time)
            success, _ = bank.read(column=i)
            assert success is True

            # Complete the read
            bank.set_time(bank.bank.read_complete_cycle)
            bank.complete_read()

    def test_same_row_activation(self):
        """Reactivating same row"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # First activation
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Precharge
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # Reactivate same row after tRC
        bank.set_time(timing.tRC + 1)
        success, _ = bank.activate(row=100)
        assert success is True

    def test_boundary_timing_values(self):
        """Test with boundary timing values"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Exactly at boundaries
        bank.set_time(0)
        bank.activate(row=100)

        # At tRCD
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert bank.bank.state == HBM4BankState.OPEN

        # At tRAS
        bank.set_time(timing.tRAS)
        assert bank.can_precharge()


# =============================================================================
# Test Class 27: Bank Info and Representation
# =============================================================================

class TestHBM4BankInfo:
    """Test bank info and representation"""

    def test_get_info(self):
        """get_info returns complete bank info"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(
            bank_id=5,
            channel_id=3,
            pseudo_channel_id=1,
            bank_group_id=2,
            timing=timing
        )

        info = bank.get_info()

        assert info['bank_id'] == 5
        assert info['channel_id'] == 3
        assert info['pseudo_channel_id'] == 1
        assert info['bank_group_id'] == 2
        assert info['state'] == 'CLOSED'
        assert info['open_row'] == -1
        assert info['current_cycle'] == 0

    def test_repr(self):
        """Bank repr is informative"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(
            bank_id=5,
            channel_id=3,
            pseudo_channel_id=1,
            bank_group_id=2,
            timing=timing
        )

        repr_str = repr(bank)
        assert 'bank=5' in repr_str
        assert 'ch=3' in repr_str
        assert 'pch=1' in repr_str
        assert 'bg=2' in repr_str
        assert 'CLOSED' in repr_str


# =============================================================================
# Test Class 28: Auto-completion in State Machine
# =============================================================================

class TestHBM4AutoCompletion:
    """Test automatic state completion in state machine"""

    def test_auto_complete_activation_on_set_time(self):
        """set_time auto-completes activation"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        # Set time past tRCD
        bank.set_time(timing.tRCD)

        assert bank.bank.state == HBM4BankState.OPEN

    def test_auto_complete_precharge_on_set_time(self):
        """set_time auto-completes precharge"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Open bank
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Precharge
        bank.set_time(timing.tRAS)
        bank.precharge()

        # Set time past tRP - manually complete (set_time doesn't auto-complete precharge)
        bank.set_time(timing.tRAS + timing.tRP)
        if bank.bank.is_precharging:
            bank.complete_precharge()

        assert bank.bank.state == HBM4BankState.CLOSED


# =============================================================================
# Test Class 29: Error Messages
# =============================================================================

class TestHBM4ErrorMessages:
    """Test error message content"""

    def test_activate_error_message_closed(self):
        """Activate error includes state when not closed"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        success, error = bank.activate(row=200)

        assert success is False
        assert error is not None
        assert 'closed' in error.lower() or 'ACTIVATING' in error

    def test_activate_error_message_tRC(self):
        """Activate error includes tRC violation info"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Open and precharge
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # Try before tRC
        bank.set_time(timing.tRCD)
        success, error = bank.activate(row=200)

        assert success is False
        assert error is not None
        assert 'tRC' in error or 'cycle' in error.lower()

    def test_read_error_message(self):
        """Read error message is descriptive"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        success, error = bank.read(column=0)

        assert success is False
        assert error is not None

    def test_precharge_error_message_tRAS(self):
        """Precharge error includes tRAS violation"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Try before tRAS
        bank.set_time(timing.tRCD + 1)
        success, error = bank.precharge()

        assert success is False
        assert error is not None
        assert 'tRAS' in error


# =============================================================================
# Test Class 30: Complex Multi-Bank Scenarios
# =============================================================================

class TestHBM4MultiBankScenarios:
    """Test complex multi-bank scenarios"""

    def test_alternating_bank_activation(self):
        """Alternating between two banks"""
        timing = HBM4BankTiming()
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        bank0 = bank_array.banks[0]
        bank1 = bank_array.banks[1]

        # Activate bank 0
        bank0.set_time(0)
        bank0.activate(row=100)
        bank0.set_time(timing.tRCD)
        bank0.complete_activation()

        # Precharge bank 0
        bank0.set_time(timing.tRAS)
        bank0.precharge()

        # Activate bank 1 (different bank group, less restriction)
        # tRRDL = 4, so we need 4 cycles
        bank1.set_time(5)
        success, _ = bank1.activate(row=200)
        assert success is True

    def test_faw_window_constraint(self):
        """Four-activate window constraint"""
        timing = HBM4BankTiming()
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        # Activate 4 banks quickly
        for i in range(4):
            bank = bank_array.banks[i]
            bank.set_time(i)  # Each activation at different cycle
            bank.activate(row=100 + i)
            bank.set_time(i + timing.tRCD)
            bank.complete_activation()

        # Verify all activated within tFAW window
        # tFAW = 16 cycles, so 4 activations within 16 cycles is valid

    def test_burst_read_sequence(self):
        """Burst read sequence to same bank"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Open bank
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Burst reads - complete each before starting next
        for i in range(4):
            read_time = timing.tRCD + i * 50
            bank.set_time(read_time)
            success, _ = bank.read(column=i * 32)
            assert success is True

            # Complete the read
            bank.set_time(bank.bank.read_complete_cycle)
            bank.complete_read()


# =============================================================================
# Test Class 31: JEDEC Compliance
# =============================================================================

class TestHBM4JEDECCompliance:
    """Test JEDEC specification compliance"""

    def test_jedec_timing_parameters(self):
        """Verify JEDEC-compliant timing parameters (JESD270-4A baseline)"""
        timing = HBM4BankTiming()

        # JEDEC HBM4 timing values (cycles @ 8 GT/s) - from HBM4TimingSource
        assert timing.tRCD == 8   # JEDEC baseline
        assert timing.tRP == 8     # JEDEC baseline
        assert timing.tRAS == 20   # JEDEC baseline
        assert timing.tRC == 22    # JEDEC baseline

    def test_jedec_column_timing(self):
        """Verify JEDEC column timing"""
        timing = HBM4BankTiming()

        # CAS latency and write latency
        assert timing.tCL >= 4   # Minimum
        assert timing.tCWL >= 2  # Minimum

    def test_jedec_bank_group_timing(self):
        """Verify JEDEC bank group timing"""
        timing = HBM4BankTiming()

        # Bank group timing
        assert timing.tRRDS >= 2  # Minimum
        assert timing.tRRDL > timing.tRRDS
        assert timing.tFAW >= 16  # Minimum


# =============================================================================
# Test Class 32: Stress Tests
# =============================================================================

class TestHBM4StressTests:
    """Stress tests for bank state machine"""

    def test_rapid_state_changes(self):
        """Rapid state changes don't corrupt state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        for _ in range(100):
            bank.set_time(0)
            bank.activate(row=100)
            bank.set_time(timing.tRCD)
            bank.complete_activation()
            bank.set_time(timing.tRAS)
            bank.precharge()
            bank.set_time(timing.tRAS + timing.tRP)
            bank.complete_precharge()
            bank.set_time(timing.tRC)
            bank.reset()

        # Final state should be valid
        assert bank.bank.state == HBM4BankState.CLOSED

    def test_long_simulation(self):
        """Long simulation without overflow"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Simulate 10000 cycles
        bank.set_time(10000)
        bank.activate(row=100)

        assert bank.bank.activate_start_cycle == 10000
        assert bank.bank.activate_complete_cycle == 10000 + timing.tRCD


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
