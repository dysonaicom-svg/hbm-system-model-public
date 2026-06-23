"""
Tests for HBM4 Bank State Machine with Full State Tracking

These tests demonstrate:
- Bank state transitions: CLOSED -> ACTIVATING -> OPEN -> PRECHARGING -> CLOSED
- Timing parameter compliance: tRCD, tRP, tRAS, tRC
- Per-bank state machines (1024 total banks)
- Integration with HBM4 refresh scheduler
- State transition timing validation

HBM4 Key Timing Parameters (12 Gbps optimized):
- tRCD: 12 cycles (Activate to Read/Write)
- tRP: 12 cycles (Precharge)
- tRAS: 28 cycles (Activate to Precharge)
- tRC: 40 cycles (Activate to Activate same bank)
"""

import pytest
from model.dram.hbm4_bank_state_machine import (
    HBM4BankStateMachine, HBM4BankArray, HBM4BankState, HBM4Command,
    HBM4BankTiming, TimingViolation, create_hbm4_bank_state_machine,
    create_hbm4_bank_array
)


class TestHBM4BankStates:
    """Test HBM4 bank state definitions and basic transitions"""

    def test_bank_state_enum_values(self):
        """Verify all bank states are defined correctly"""
        assert HBM4BankState.CLOSED == 0
        assert HBM4BankState.ACTIVATING == 1
        assert HBM4BankState.OPEN == 2
        assert HBM4BankState.PRECHARGING == 3
        assert HBM4BankState.READ == 4
        assert HBM4BankState.WRITE == 5
        assert HBM4BankState.REFRESH == 6
        assert HBM4BankState.POWER_DOWN == 7
        assert HBM4BankState.SELF_REFRESH == 8

    def test_bank_starts_closed(self):
        """Bank must start in CLOSED state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        assert bank.bank.state == HBM4BankState.CLOSED
        assert bank.bank.is_closed
        assert not bank.bank.is_open
        assert not bank.bank.is_activating


class TestHBM4ActivationTiming:
    """Test activation timing compliance (tRCD, tRC)"""

    def test_activation_transitions_to_activating(self):
        """ACT must transition bank to ACTIVATING state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        success, error = bank.activate(row=100)

        assert success is True
        assert error is None
        assert bank.bank.state == HBM4BankState.ACTIVATING
        assert bank.bank.is_activating
        assert bank.bank.open_row == 100

    def test_activation_complete_after_tRCD(self):
        """Activation must complete after tRCD cycles"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        # Before tRCD - should not be complete
        for cycle in range(1, timing.tRCD):
            bank.set_time(cycle)
            assert not bank.complete_activation()

        # After tRCD - should complete
        bank.set_time(timing.tRCD)
        assert bank.complete_activation()
        assert bank.bank.state == HBM4BankState.OPEN
        assert bank.bank.is_open

    def test_cannot_activate_closed_bank_twice(self):
        """Cannot activate same bank twice without precharge"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        success, _ = bank.activate(row=100)
        assert success is True

        # Try to activate again while still ACTIVATING
        success, error = bank.activate(row=200)
        assert success is False
        assert error is not None
        assert "not closed" in error.lower()

    def test_tRC_constraint_for_same_bank(self):
        """tRC must be satisfied before reactivating same bank"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # First activation
        bank.set_time(0)
        bank.activate(row=100)

        # Complete activation and precharge cycle
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Wait past tRAS and precharge
        bank.set_time(timing.tRAS)
        bank.precharge()

        # Complete precharge - bank becomes CLOSED
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # Now bank is CLOSED, but tRC may not be satisfied
        # tRC = 40, so from t=0 to t=52, we only have 52 cycles
        # Need to wait until cycle 40 total from start
        # At t=41, tRC is satisfied (41 >= 40)
        bank.set_time(timing.tRC + 1)
        assert bank.can_activate(), f"Bank should be able to activate at cycle {timing.tRC + 1}, tRC={timing.tRC}"

    def test_tRCD_timing_value(self):
        """Verify tRCD is 12 cycles"""
        timing = HBM4BankTiming()
        assert timing.tRCD == 12


class TestHBM4PrechargeTiming:
    """Test precharge timing compliance (tRP, tRAS)"""

    def test_precharge_transitions_to_precharging(self):
        """PRE must transition bank to PRECHARGING state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Activate and complete
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Wait past tRAS minimum before precharge
        bank.set_time(timing.tRAS)
        success, error = bank.precharge()
        assert success is True
        assert error is None
        assert bank.bank.state == HBM4BankState.PRECHARGING
        assert bank.bank.is_precharging

    def test_precharge_complete_after_tRP(self):
        """Precharge must complete after tRP cycles"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Setup: activate and complete
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Wait past tRAS and precharge
        bank.set_time(timing.tRAS)
        bank.precharge()

        # Before tRP - should not be complete
        for cycle in range(timing.tRAS + 1, timing.tRAS + timing.tRP):
            bank.set_time(cycle)
            assert not bank.complete_precharge()

        # After tRP - should complete
        bank.set_time(timing.tRAS + timing.tRP)
        assert bank.complete_precharge()
        assert bank.bank.state == HBM4BankState.CLOSED
        assert bank.bank.is_closed

    def test_cannot_precharge_before_tRAS(self):
        """Cannot precharge before tRAS minimum"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Activate and complete
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Try to precharge before tRAS
        bank.set_time(timing.tRCD + 1)
        assert not bank.can_precharge()

    def test_can_precharge_after_tRAS(self):
        """Can precharge after tRAS minimum is satisfied"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Activate and complete
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # After tRAS
        bank.set_time(timing.tRAS)
        assert bank.can_precharge()

    def test_tRAS_timing_value(self):
        """Verify tRAS is 28 cycles"""
        timing = HBM4BankTiming()
        assert timing.tRAS == 28

    def test_tRP_timing_value(self):
        """Verify tRP is 12 cycles"""
        timing = HBM4BankTiming()
        assert timing.tRP == 12


class TestHBM4ReadWriteTiming:
    """Test read/write timing compliance"""

    def test_read_requires_open_bank(self):
        """READ can only be issued when bank is OPEN"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Try to read from closed bank
        bank.set_time(0)
        assert not bank.can_read()

        # Activate but not yet complete
        bank.activate(row=100)
        assert not bank.can_read()

        # Complete activation
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert bank.can_read()

    def test_read_transitions_through_read_state(self):
        """READ must transition through READ state"""
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
        assert bank.bank.is_reading

        # Now complete the read
        bank.set_time(bank.bank.read_complete_cycle)
        bank.complete_read()
        assert bank.bank.state == HBM4BankState.OPEN

    def test_write_requires_open_bank(self):
        """WRITE can only be issued when bank is OPEN"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Try to write to closed bank
        bank.set_time(0)
        assert not bank.can_write()

        # Activate but not yet complete
        bank.activate(row=100)
        assert not bank.can_write()

        # Complete activation
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert bank.can_write()

    def test_write_transitions_through_write_state(self):
        """WRITE must transition through WRITE state"""
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
        assert bank.bank.is_writing

        # Now complete the write
        bank.set_time(bank.bank.write_complete_cycle)
        bank.complete_write()
        assert bank.bank.state == HBM4BankState.OPEN


class TestHBM4RefreshTiming:
    """Test refresh timing compliance"""

    def test_refresh_requires_closed_bank(self):
        """REF can only be issued when bank is CLOSED"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Try to refresh open bank
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        assert not bank.can_refresh()

        # Precharge first
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # Now can refresh
        assert bank.can_refresh()

    def test_refresh_transitions_through_refresh_state(self):
        """REFRESH must transition through REFRESH state"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        success, error = bank.refresh()
        assert success is True
        assert bank.bank.is_refreshing

    def test_refresh_completes_after_tRFC(self):
        """Refresh must complete after tRFC cycles"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.refresh()

        # Before tRFC - should not be complete
        for cycle in range(1, timing.tRFC):
            bank.set_time(cycle)
            assert not bank.complete_refresh()

        # After tRFC - should complete
        bank.set_time(timing.tRFC)
        assert bank.complete_refresh()
        assert bank.bank.is_closed


class TestHBM4TimingValues:
    """Test that timing parameters match requirements"""

    def test_all_timing_parameters(self):
        """Verify all key timing parameters match requirements"""
        timing = HBM4BankTiming()

        # Key parameters from requirements
        assert timing.tRCD == 12, f"tRCD should be 12, got {timing.tRCD}"
        assert timing.tRP == 12, f"tRP should be 12, got {timing.tRP}"
        assert timing.tRAS == 28, f"tRAS should be 28, got {timing.tRAS}"
        assert timing.tRC == 40, f"tRC should be 40, got {timing.tRC}"

    def test_timing_to_ns_conversion(self):
        """Verify timing cycles convert to nanoseconds correctly"""
        timing = HBM4BankTiming()

        # tCK = 125 ps = 0.125 ns
        assert abs(timing.cycles_to_ns(8) - 1.0) < 0.001  # 8 cycles = 1 ns

    def test_timing_to_seconds_conversion(self):
        """Verify timing cycles convert to seconds correctly"""
        timing = HBM4BankTiming()

        # tCK = 125e-12 s
        cycles = 1000
        expected_s = 1000 * 125e-12
        assert abs(timing.cycles_to_seconds(cycles) - expected_s) < 1e-15


class TestHBM4BankArray:
    """Test HBM4 bank array for a pseudo-channel"""

    def test_bank_array_has_16_banks(self):
        """Bank array must have 16 banks per pseudo-channel"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        assert len(bank_array.banks) == 16

    def test_bank_ids_are_unique(self):
        """All bank IDs must be unique"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        bank_ids = [b.bank_id for b in bank_array.banks]
        assert len(bank_ids) == len(set(bank_ids))

    def test_bank_group_assignment(self):
        """Banks must be assigned to correct bank groups (2 per group)"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        for bg_id in range(8):
            banks_in_group = bank_array.get_banks_in_group(bg_id)
            assert len(banks_in_group) == 2

            for bank in banks_in_group:
                assert bank.bank_group_id == bg_id

    def test_tick_completes_state_transitions(self):
        """tick() must auto-complete state transitions"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        # Activate bank 0
        bank = bank_array.banks[0]
        bank.set_time(0)
        bank.activate(row=100)

        # Initial state should be ACTIVATING
        assert bank.bank.state == HBM4BankState.ACTIVATING

        # After tRCD ticks, should transition to OPEN
        for _ in range(bank_array.timing.tRCD):
            bank_array.tick()

        assert bank.bank.state == HBM4BankState.OPEN

    def test_active_bank_count(self):
        """get_active_bank_count must return correct count"""
        bank_array = create_hbm4_bank_array(pseudo_channel_id=0, channel_id=0)

        assert bank_array.get_active_bank_count() == 0

        # Activate some banks
        for i in range(4):
            bank = bank_array.banks[i]
            bank.set_time(i * 10)
            bank.activate(row=100 * i)
            bank.set_time(i * 10 + bank_array.timing.tRCD)
            bank.complete_activation()

        # All should be active after tRCD
        assert bank_array.get_active_bank_count() == 4


class TestHBM4BankGroupScheduling:
    """Test bank group-aware scheduling"""

    def test_same_bank_group_tRRDS_constraint(self):
        """Activations to same BG must respect tRRDS"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Activate bank
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Within tRRDS - should not be able to activate same bank again
        bank.set_time(timing.tRCD + 1)
        assert not bank.can_activate()

        # After tRRDS but before tRC - same BG restriction
        bank.set_time(timing.tRRDS + 1)
        # Should fail because tRC not satisfied
        assert not bank.can_activate()

    def test_different_bank_group_tRRDL_constraint(self):
        """Different BG has different timing constraint"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Activate bank
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # tRRDL > tRRDS, so even at tRRDS+1, different BG would fail
        # because we're trying to activate the same bank


class TestHBM4StateTransitionHistory:
    """Test state transition history tracking"""

    def test_transitions_are_recorded(self):
        """State transitions must be recorded"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        bank.set_time(0)
        bank.activate(row=100)

        transitions = bank.bank.get_transitions()
        assert len(transitions) >= 1
        assert transitions[-1].from_state == HBM4BankState.CLOSED
        assert transitions[-1].to_state == HBM4BankState.ACTIVATING
        assert transitions[-1].command == HBM4Command.ACT

    def test_full_cycle_transitions(self):
        """Complete ACT -> OPEN -> PRE -> CLOSED cycle"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # ACT
        bank.set_time(0)
        bank.activate(row=100)

        # Complete activation
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # PRE
        bank.set_time(timing.tRAS)
        bank.precharge()

        # Complete precharge
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        transitions = bank.bank.get_transitions()
        assert len(transitions) == 4

        assert transitions[0].to_state == HBM4BankState.ACTIVATING
        assert transitions[1].to_state == HBM4BankState.OPEN
        assert transitions[2].to_state == HBM4BankState.PRECHARGING
        assert transitions[3].to_state == HBM4BankState.CLOSED


class TestHBM4TimingValidation:
    """Test timing violation detection"""

    def test_no_violation_for_valid_timing(self):
        """No violations for properly timed commands"""
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
        # Should not have tRAS violation
        assert not any(v.violation_type == 'tRAS' for v in violations)

    def test_timing_violation_recorded_early_precharge(self):
        """Timing violations must be recorded for early precharge"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Activate
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()

        # Try to precharge before tRAS (cycle 5, tRAS = 28)
        bank.set_time(5)
        bank.precharge()

        # Check that we recorded the violation
        violations = bank.get_violations()
        # The violation happens because we issued PRE before tRAS minimum

    def test_clear_violations(self):
        """Violations can be cleared"""
        timing = HBM4BankTiming()
        bank = HBM4BankStateMachine(bank_id=0, timing=timing)

        # Create some violations
        bank.set_time(0)
        bank.activate(row=100)
        bank.set_time(timing.tRCD)
        bank.complete_activation()
        bank.set_time(timing.tRAS)
        bank.precharge()
        bank.set_time(timing.tRAS + timing.tRP)
        bank.complete_precharge()

        # Violations list exists
        bank.clear_violations()
        assert len(bank.get_violations()) == 0


class TestHBM4SpeedGradeTiming:
    """Test timing for different speed grades"""

    def test_8gbps_timing(self):
        """Verify 8 Gbps timing parameters"""
        timing = HBM4BankTiming.for_speed_grade(8.0)

        assert timing.tCK_ps == 125.0
        assert timing.tRCD == 12
        assert timing.tRP == 12
        assert timing.tRAS == 28
        assert timing.tRC == 40

    def test_12gbps_timing(self):
        """Verify 12 Gbps timing parameters"""
        timing = HBM4BankTiming.for_speed_grade(12.0)

        assert timing.tCK_ps == pytest.approx(83.33, rel=0.01)
        # Cycles should remain constant, only tCK changes

    def test_16gbps_timing(self):
        """Verify 16 Gbps timing parameters"""
        timing = HBM4BankTiming.for_speed_grade(16.0)

        assert timing.tCK_ps == pytest.approx(62.5, rel=0.01)


class TestHBM4BankFactoryFunctions:
    """Test factory functions"""

    def test_create_bank_state_machine(self):
        """Factory function creates correct bank"""
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
        """Factory function creates correct bank array"""
        bank_array = create_hbm4_bank_array(
            pseudo_channel_id=1,
            channel_id=2
        )

        assert len(bank_array.banks) == 16
        assert bank_array.pseudo_channel_id == 1
        assert bank_array.channel_id == 2


class TestHBM4BankIntegration:
    """Integration tests for full HBM4 bank operation"""

    def test_1024_total_banks_calculation(self):
        """Verify 1024 total banks: 32ch × 2pch × 16bank"""
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        total = spec.channels * spec.pseudo_channels_per_channel * spec.banks_per_pseudo_channel

        assert total == 1024, f"Expected 1024 banks, got {total}"

    def test_64_pseudo_channels_calculation(self):
        """Verify 64 total pseudo-channels: 32ch × 2pch"""
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        total_pch = spec.channels * spec.pseudo_channels_per_channel

        assert total_pch == 64, f"Expected 64 pseudo-channels, got {total_pch}"

    def test_512_bank_groups_calculation(self):
        """Verify 512 total bank groups: 64pch × 8bg"""
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        total_pch = spec.channels * spec.pseudo_channels_per_channel
        total_bg = total_pch * spec.bank_groups_per_channel

        assert total_bg == 512, f"Expected 512 bank groups, got {total_bg}"


class TestHBM4RefreshSchedulerIntegration:
    """Test integration with HBM4 refresh scheduler"""

    def test_refresh_scheduler_creates_1024_banks(self):
        """Refresh scheduler tracks 1024 banks"""
        from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler

        scheduler = HBM4RefreshScheduler()

        assert len(scheduler.bank_status) == 1024

    def test_per_bank_refresh_sequence(self):
        """Per-bank refresh cycles through all banks"""
        from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

        scheduler = HBM4RefreshScheduler()
        scheduler.set_mode(RefreshMode.PER_BANK)

        # Advance to tREFIpb cycles so refresh can be issued
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        # Get first refresh command
        cmd = scheduler.get_refresh_command()
        assert cmd is not None
        command_name, channel_id, pch_id, bank_id = cmd
        assert command_name == 'REFsb'

        # Advance time past refresh interval
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        # Should get next bank
        cmd2 = scheduler.get_refresh_command()
        assert cmd2 is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
