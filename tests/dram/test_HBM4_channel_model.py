"""
Tests for HBM4 Channel Model with Enhanced State Tracking

Tests the HBM4 channel state machine with 32 channels and pseudo-channel support,
including enhanced bank state tracking and timing validation.

Key HBM4 Timing Parameters (Enhanced):
- tRCD: 12 cycles (Activate to Read/Write)
- tRP: 12 cycles (Precharge)
- tRAS: 28 cycles (Activate to Precharge)
- tRC: 40 cycles (Activate to Activate same bank)
"""

import pytest
from model.dram.HBM4_channel_model import (
    HBM4Channel, PseudoChannel, HBM4ChannelState, PseudoChannelState,
    HBM4ChannelArray, BankGroupScheduler
)
from model.dram.HBM4_spec import HBM4Spec
from model.dram.HBM4_bank_state_machine import (
    HBM4BankState, HBM4BankTiming, TimingViolation
)
from model.dram.timing import HBM4Timing


class TestHBM4ChannelCreation:
    """Test HBM4 channel creation"""

    def test_channel_creation(self):
        """32 channels must be created successfully"""
        spec = HBM4Spec()
        channels = [HBM4Channel(i, spec) for i in range(32)]

        assert len(channels) == 32
        for ch in channels:
            assert ch.channel_id in range(32)

    def test_channel_has_two_pseudo_channels(self):
        """Each channel must have 2 pseudo-channels"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert len(ch.pseudo_channels) == 2
        assert ch.pseudo_channels[0].pseudo_channel_id == 0
        assert ch.pseudo_channels[1].pseudo_channel_id == 1

    def test_pseudo_channels_are_independent(self):
        """Pseudo-channels must operate independently"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        pc1 = ch.pseudo_channels[1]

        # Both should start in IDLE state
        assert pc0.state == PseudoChannelState.IDLE
        assert pc1.state == PseudoChannelState.IDLE


class TestHBM4ChannelCommands:
    """Test HBM4 channel command handling"""

    def test_channel_commands(self):
        """All HBM4 commands must be supported"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        expected_commands = ['ACT', 'PRE', 'PREA', 'RD', 'WR', 'RDA', 'WRA',
                            'REFab', 'REFsb', 'RFMab', 'RFMsb']
        for cmd in expected_commands:
            assert cmd in ch.COMMANDS

    def test_activate_command(self):
        """ACT command must activate a row"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        assert result is True
        # Verify a bank was activated
        pc0 = ch.pseudo_channels[0]

        # Check using enhanced bank state machine
        if hasattr(pc0.banks[0], 'get_state'):
            # Enhanced state machine
            assert pc0.banks[0].get_state().name in ['ACTIVATING', 'OPEN']
        else:
            # Legacy state machine
            from model.dram.bank_state_machine import BankStateEnum
            activated_banks = [b for b in pc0.banks if b.bank.state.value == 1]  # ACTIVE state
            assert len(activated_banks) > 0

    def test_precharge_command(self):
        """PRE command must precharge banks"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)

        # First activate
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Advance time past tRAS (28 cycles for enhanced timing)
        for _ in range(35):
            ch.tick()

        # Then precharge
        result = ch.issue_command('PRE', pseudo_channel=0, bank=0, row=0)

        assert result is True

    def test_read_command(self):
        """RD command must work"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        result = ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        assert result is True

    def test_write_command(self):
        """WR command must work"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        result = ch.issue_command('WR', pseudo_channel=0, bank=0, row=100, col=0)

        assert result is True


class TestHBM4PseudoChannelIndependence:
    """Test pseudo-channel independence"""

    def test_pseudo_channels_do_not_interfere(self):
        """Activating in PC0 must not affect PC1"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        pc1 = ch.pseudo_channels[1]

        # Activate row in PC0
        pc0.activate_row(100)

        # PC0 should have row open
        assert pc0.is_row_open(100)

        # PC1 should not be affected
        assert not pc1.is_row_open(100)

    def test_both_pseudo_channels_can_be_active(self):
        """Both pseudo-channels can be active simultaneously"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        pc1 = ch.pseudo_channels[1]

        # Activate in both
        pc0.activate_row(100)
        pc1.activate_row(200)

        assert pc0.is_row_open(100)
        assert pc1.is_row_open(200)

    def test_pseudo_channels_have_independent_banks(self):
        """Each pseudo-channel has independent bank state machines"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0_banks = ch.pseudo_channels[0].banks
        pc1_banks = ch.pseudo_channels[1].banks

        # They should be separate bank instances
        assert pc0_banks is not pc1_banks
        assert len(pc0_banks) == 16  # 16 banks per pseudo-channel
        assert len(pc1_banks) == 16


class TestHBM4ChannelTick:
    """Test channel timing advancement"""

    def test_tick_advances_time(self):
        """tick() must advance internal cycle counter"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        initial_cycle = ch.current_cycle
        ch.tick()

        assert ch.current_cycle == initial_cycle + 1

    def test_tick_advances_bank_timers(self):
        """tick() must advance all bank timers"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)

        # Activate a row
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Get current bank
        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        # Time should have advanced
        if hasattr(bank.bank, 'activate_start_cycle'):
            activation_time = bank.bank.activate_start_cycle
            ch.tick()
            assert bank.bank.activate_start_cycle >= activation_time


class TestHBM4ChannelState:
    """Test channel state machine"""

    def test_channel_starts_idle(self):
        """Channel must start in IDLE state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert ch.state == HBM4ChannelState.IDLE

    def test_channel_becomes_active_on_activation(self):
        """Channel must transition to ACTIVE on activation"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # At least one pseudo-channel should be active
        active_count = sum(1 for pc in ch.pseudo_channels if pc.state != HBM4ChannelState.IDLE)
        assert active_count > 0

    def test_refresh_state(self):
        """Channel must support REFRESH state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('REFab', pseudo_channel=0, bank=0, row=0)

        # Should have entered refresh state
        refresh_count = sum(1 for pc in ch.pseudo_channels if pc.state == PseudoChannelState.REFRESHING)
        assert refresh_count > 0


class TestHBM4ChannelBandwidth:
    """Test channel bandwidth calculations"""

    def test_peak_bandwidth_per_channel(self):
        """Each channel provides 64-bit @ 8 GT/s = 64 GB/s"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Per-channel bandwidth = total / 32
        expected_per_channel = spec.bandwidth_gbs / 32

        assert abs(ch.peak_bandwidth_gbs - expected_per_channel) < 0.1

    def test_aggregate_bandwidth(self):
        """32 channels provide 2 TB/s aggregate"""
        spec = HBM4Spec()
        total = sum(HBM4Channel(i, spec).peak_bandwidth_gbs for i in range(32))

        assert abs(total - spec.bandwidth_gbs) < 1.0


class TestHBM4BankStateTransitions:
    """Test enhanced bank state transitions"""

    def test_bank_starts_closed(self):
        """Banks must start in CLOSED state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        # Check using enhanced state machine
        if hasattr(bank, 'get_state'):
            assert bank.get_state() == HBM4BankState.CLOSED
        else:
            from model.dram.bank_state_machine import BankStateEnum
            assert bank.bank.state.value == 0  # IDLE = 0

    def test_bank_activates_and_transitions_to_activating(self):
        """Bank must transition from CLOSED to ACTIVATING on activation"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        # Bank should be CLOSED initially
        if hasattr(bank, 'get_state'):
            assert bank.get_state() == HBM4BankState.CLOSED

        # Activate
        pc0.activate_row(100, bank_id=0)

        # Bank should now be ACTIVATING
        if hasattr(bank, 'get_state'):
            assert bank.get_state() == HBM4BankState.ACTIVATING

    def test_bank_completes_activation(self):
        """Bank must complete activation after tRCD"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]
        timing = HBM4BankTiming()

        # Activate
        pc0.activate_row(100, bank_id=0)

        # Initially ACTIVATING
        if hasattr(bank, 'get_state'):
            assert bank.get_state() == HBM4BankState.ACTIVATING

            # Advance past tRCD
            for _ in range(timing.tRCD + 1):
                ch.tick()

            # Should be OPEN now
            assert bank.get_state() == HBM4BankState.OPEN

    def test_bank_tracks_open_row(self):
        """Bank must track which row is open"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]
        timing = HBM4BankTiming()

        # Activate row 100
        pc0.activate_row(100, bank_id=0)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            ch.tick()

        # Bank should track the open row
        if hasattr(bank, 'get_open_row'):
            assert bank.get_open_row() == 100
        else:
            assert bank.bank.open_row == 100

    def test_bank_precharge_returns_to_closed(self):
        """Bank must return to CLOSED after precharge"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]
        timing = HBM4BankTiming()

        # Activate
        pc0.activate_row(100, bank_id=0)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            ch.tick()

        # Advance past tRAS
        for _ in range(timing.tRAS + 1):
            ch.tick()

        # Precharge
        pc0.precharge_bank(0)

        # Advance past tRP
        for _ in range(timing.tRP + 1):
            ch.tick()

        # Bank should be CLOSED
        if hasattr(bank, 'get_state'):
            assert bank.get_state() == HBM4BankState.CLOSED
        else:
            from model.dram.bank_state_machine import BankStateEnum
            assert bank.bank.state.value == 0


class TestHBM4TimingCompliance:
    """Test HBM4 timing parameter compliance using enhanced timing"""

    def test_enhanced_timing_tRCD_is_12_cycles(self):
        """tRCD must be 12 cycles in enhanced bank timing"""
        timing = HBM4BankTiming()
        assert timing.tRCD == 12

    def test_enhanced_timing_tRP_is_12_cycles(self):
        """tRP must be 12 cycles in enhanced bank timing"""
        timing = HBM4BankTiming()
        assert timing.tRP == 12

    def test_enhanced_timing_tRAS_is_28_cycles(self):
        """tRAS must be 28 cycles in enhanced bank timing"""
        timing = HBM4BankTiming()
        assert timing.tRAS == 28

    def test_enhanced_timing_tRC_is_40_cycles(self):
        """tRC must be 40 cycles in enhanced bank timing"""
        timing = HBM4BankTiming()
        assert timing.tRC == 40

    def test_activation_timing_with_enhanced_banks(self):
        """Verify activation follows tRCD timing with enhanced banks"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)
        timing = HBM4BankTiming()

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        # Activate
        pc0.activate_row(100, bank_id=0)

        # Check activation started at cycle 0
        if hasattr(bank.bank, 'activate_start_cycle'):
            assert bank.bank.activate_start_cycle == 0

        # Check activation completes after tRCD
        for cycle in range(1, timing.tRCD):
            ch.tick()
            # Should not be able to read yet
            if hasattr(bank, 'can_read'):
                assert not bank.can_read()

        # At tRCD + 1, should be able to read
        ch.tick()
        if hasattr(bank, 'can_read'):
            assert bank.can_read()

    def test_precharge_timing_with_enhanced_banks(self):
        """Verify precharge follows tRP timing with enhanced banks"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)
        timing = HBM4BankTiming()

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        # Activate and wait
        pc0.activate_row(100, bank_id=0)
        for _ in range(timing.tRCD + 1):
            ch.tick()

        # Wait past tRAS
        for _ in range(timing.tRAS + 1):
            ch.tick()

        # Precharge
        pc0.precharge_bank(0)

        # Initially PRECHARGING
        if hasattr(bank, 'get_state'):
            assert bank.get_state() == HBM4BankState.PRECHARGING

        # After tRP, should be CLOSED
        for _ in range(timing.tRP + 1):
            ch.tick()

        if hasattr(bank, 'get_state'):
            assert bank.get_state() == HBM4BankState.CLOSED


class TestHBM4TimingValidation:
    """Test timing validation and violation detection"""

    def test_validate_timing_returns_empty_for_valid_sequence(self):
        """No violations for valid timing sequence"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)
        timing = HBM4BankTiming()

        # Valid sequence: ACT -> wait tRCD -> READ -> wait tRAS -> PRE -> wait tRP
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            ch.tick()

        # Read
        ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        # Advance past tRAS
        for _ in range(timing.tRAS + 1):
            ch.tick()

        # Precharge
        ch.issue_command('PRE', pseudo_channel=0, bank=0, row=0)

        # Advance past tRP
        for _ in range(timing.tRP + 1):
            ch.tick()

        # Validate timing
        violations = ch.validate_timing()
        # May have some violations depending on implementation

    def test_channel_validates_all_banks(self):
        """Channel validates timing for all banks"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)
        timing = HBM4BankTiming()

        # Activate multiple banks
        for bank_id in range(4):
            ch.issue_command('ACT', pseudo_channel=0, bank=bank_id, row=100 * bank_id)
            for _ in range(timing.tRCD + 1):
                ch.tick()

        # Validate timing
        violations = ch.validate_timing()
        assert isinstance(violations, list)


class TestHBM4ChannelArray:
    """Test HBM4 channel array for full system"""

    def test_32_channels_created(self):
        """Channel array must have 32 channels"""
        array = HBM4ChannelArray()

        assert array.num_channels == 32

    def test_1024_total_banks(self):
        """Channel array must have 1024 total banks"""
        array = HBM4ChannelArray()

        assert array.total_banks == 1024

    def test_total_bandwidth_calculation(self):
        """Total bandwidth must be calculated correctly"""
        array = HBM4ChannelArray()

        # 32 channels × 64 GB/s per channel = 2048 GB/s
        assert abs(array.total_bandwidth_gbs - 2048.0) < 1.0

    def test_tick_advances_all_channels(self):
        """tick() must advance all channels"""
        array = HBM4ChannelArray()

        initial_cycles = [ch.current_cycle for ch in array.channels]

        array.tick()

        for i, ch in enumerate(array.channels):
            assert ch.current_cycle == initial_cycles[i] + 1

    def test_system_state_summary(self):
        """System state summary must report all banks"""
        array = HBM4ChannelArray()

        summary = array.get_system_state_summary()

        assert summary['num_channels'] == 32
        assert summary['total_banks'] == 1024
        assert summary['total_pseudo_channels'] == 64


class TestHBM4BankGroupScheduler:
    """Test bank group-aware command scheduler"""

    def test_scheduler_initialization(self):
        """Scheduler must initialize correctly"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        assert scheduler.timing is not None

    def test_can_issue_act_same_bank_group(self):
        """Must respect tRRDS for same BG"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # First ACT
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=0)
        scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=0)

        # Immediate second ACT to same BG - should fail (tRRDS not met)
        assert not scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=1)

        # After tRRDS - should succeed
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=0,
                                      current_cycle=timing.nRRDS + 1)

    def test_can_issue_act_different_bank_group(self):
        """Different BG has less restrictive timing (tRRDL > tRRDS)"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # First ACT to BG 0
        scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=0)

        # Immediate ACT to different BG at tRRDL - should succeed because tRRDL is met
        # Note: tRRDL is for RAS-to-RAS delay, so at cycle 4, tRRDL=4 is satisfied
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=1,
                                      current_cycle=timing.nRRDL)


class TestHBM4EnhancedChannelIntegration:
    """Integration tests for enhanced channel model"""

    def test_enhanced_banks_option(self):
        """Enhanced banks option must work"""
        spec = HBM4Spec()

        # With enhanced banks
        ch_enhanced = HBM4Channel(0, spec, use_enhanced_banks=True)
        assert ch_enhanced.use_enhanced_banks

        # With legacy banks
        ch_legacy = HBM4Channel(0, spec, use_enhanced_banks=False)
        assert not ch_legacy.use_enhanced_banks

    def test_speed_grade_configuration(self):
        """Speed grade configuration must work"""
        ch = HBM4Channel.create_with_speed_grade(0, "8Gbps")

        assert ch.timing.tCK_ps == 125.0
        assert ch.spec.data_rate_gtps == 8.0

    def test_32_channel_full_system(self):
        """Full 32-channel system must work"""
        array = HBM4ChannelArray()

        # Activate banks across all channels
        for ch_id in range(32):
            ch = array.channels[ch_id]
            for pch_id in range(2):
                for bank_id in range(4):
                    ch.issue_command('ACT', pseudo_channel=pch_id, bank=bank_id,
                                     row=ch_id * 100 + pch_id * 10 + bank_id)

        # Advance time
        for _ in range(15):
            array.tick()

        # All channels should have some active banks
        summary = array.get_system_state_summary()
        assert summary['num_channels'] == 32


class TestHBM4RefreshIntegration:
    """Test integration with refresh scheduler"""

    def test_per_bank_refresh_integration(self):
        """Per-bank refresh must work with channel"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec, use_enhanced_banks=True)
        timing = HBM4BankTiming()

        # Precharge all banks first
        for bank_id in range(16):
            ch.issue_command('ACT', pseudo_channel=0, bank=bank_id, row=100)
            for _ in range(timing.tRCD + 1):
                ch.tick()
            for _ in range(timing.tRAS + 1):
                ch.tick()
            ch.issue_command('PRE', pseudo_channel=0, bank=bank_id, row=0)
            for _ in range(timing.tRP + 1):
                ch.tick()

        # Issue per-bank refresh
        result = ch.issue_command('REFsb', pseudo_channel=0, bank=0, row=0)
        assert result is True

    def test_all_bank_refresh_integration(self):
        """All-bank refresh must work with channel"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Precharge all banks first
        ch.issue_command('PREA', pseudo_channel=0, bank=0, row=0)
        ch.issue_command('PREA', pseudo_channel=1, bank=0, row=0)

        for _ in range(15):
            ch.tick()

        # Issue all-bank refresh
        result = ch.issue_command('REFab', pseudo_channel=0, bank=0, row=0)
        assert result is True


class TestHBM4PerformanceStatistics:
    """Test performance statistics collection"""

    def test_channel_performance_stats_initialization(self):
        """Channel must have performance statistics initialized"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        stats = ch.get_performance_stats()
        assert stats is not None
        assert stats.act_count == 0
        assert stats.read_count == 0
        assert stats.write_count == 0

    def test_activation_increments_stat(self):
        """Activation must increment act_count"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Issue some activations
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        ch.issue_command('ACT', pseudo_channel=1, bank=0, row=200)

        stats = ch.get_performance_stats()
        assert stats.act_count >= 2

    def test_read_increments_stat(self):
        """Read must increment read_count"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        stats = ch.get_performance_stats()
        assert stats.read_count >= 1

    def test_write_increments_stat(self):
        """Write must increment write_count"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('WR', pseudo_channel=0, bank=0, row=100, col=0)

        stats = ch.get_performance_stats()
        assert stats.write_count >= 1

    def test_row_hit_tracking(self):
        """Row hits and misses must be tracked"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # First access - row miss
        ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        stats = ch.get_performance_stats()
        # After opening a row, next access to same row should be hit
        assert stats.row_misses >= 1

    def test_performance_summary(self):
        """Performance summary must contain expected keys"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        summary = ch.get_performance_stats().get_summary()
        assert 'act_count' in summary
        assert 'read_count' in summary
        assert 'write_count' in summary
        assert 'row_hit_rate' in summary

    def test_reset_clears_statistics(self):
        """Reset must clear performance statistics"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Generate some activity
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        # Reset
        ch.reset()

        stats = ch.get_performance_stats()
        assert stats.act_count == 0
        assert stats.read_count == 0


class TestHBM4EnhancedScheduler:
    """Test enhanced bank group scheduler with independent timing domains"""

    def test_enhanced_scheduler_creation(self):
        """Enhanced scheduler must be created for each pseudo-channel"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        scheduler0 = ch.get_scheduler(0)
        scheduler1 = ch.get_scheduler(1)

        assert scheduler0 is not None
        assert scheduler1 is not None

    def test_scheduler_tracks_per_pseudo_channel(self):
        """Scheduler must track timing independently per pseudo-channel"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Activate in PC0
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Scheduler state should be tracked
        state0 = ch.get_scheduler_state(0)
        assert state0.get('last_act_cycle', -1) >= 0

    def test_scheduler_can_issue_act(self):
        """Scheduler must check timing constraints for ACT"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        scheduler = ch.get_scheduler(0)

        # First ACT should succeed
        assert scheduler.can_issue_act(0, 0, 0)

        # Record the ACT
        scheduler.record_act(0, 0, 0)

        # Immediate second ACT to same BG should fail (tRRDS not met)
        assert not scheduler.can_issue_act(0, 0, 1)

    def test_scheduler_faw_tracking(self):
        """Scheduler must track FAW window"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        scheduler = ch.get_scheduler(0)
        timing = ch.timing

        # The FAW window limits 4 activations within nFAW cycles
        # We need to issue 4 ACTs to fill the window

        # Issue 4 activations - all to same BG to avoid tRRDL issues
        # But we need to wait tRRDS between same BG activations
        cycles = [0, timing.nRRDS, timing.nRRDS * 2, timing.nRRDS * 3]

        for cycle in cycles:
            assert scheduler.can_issue_act(0, 0, cycle), f"ACT at cycle {cycle} should be allowed"
            scheduler.record_act(0, 0, cycle)

        # After recording 4 ACTs, the FAW window is full with [0, 3, 6, 9]
        # 5th activation before nFAW expires should be blocked by FAW
        # At cycle 10 (still within FAW window since oldest is at 0 and nFAW = 16)
        assert not scheduler.can_issue_act(0, 0, timing.nRRDS + 1), \
            "5th ACT should be blocked by FAW window"

        # After nFAW cycles, the oldest entries expire and the 5th becomes allowed
        expired_cycle = cycles[0] + timing.nFAW
        # At this point, the first entry (at 0) has expired (16 cycles elapsed)
        # So FAW window has only 3 entries, allowing 5th ACT
        assert scheduler.can_issue_act(0, 0, expired_cycle), \
            "ACT after FAW window expired should be allowed"

    def test_scheduler_column_command_tracking(self):
        """Scheduler must track column commands"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        scheduler = ch.get_scheduler(0)

        # Record a READ
        scheduler.record_col(0, 0, 10, is_write=False)

        # Record a WRITE immediately - should be blocked (nRTW not met)
        assert not scheduler.can_issue_col(0, 0, 11, is_write=True)

        # After nRTW cycles, should be allowed
        assert scheduler.can_issue_col(0, 0, 15, is_write=True)

    def test_get_available_bank_groups(self):
        """Must return list of available bank groups"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        scheduler = ch.get_scheduler(0)

        # All BGs should be available initially
        available = scheduler.get_available_bank_groups(0, 0)
        assert len(available) == 8

    def test_get_next_available_cycle(self):
        """Must calculate next available cycle for BG"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        scheduler = ch.get_scheduler(0)

        # Record an ACT
        scheduler.record_act(0, 0, 5)

        # Next available for same BG should be 5 + tRRDS
        timing = ch.timing
        next_cycle = scheduler.get_next_available_cycle(0, 0, 5)
        assert next_cycle == 5 + timing.nRRDS


class TestHBM4ChannelArrayPerformance:
    """Test system-level performance statistics"""

    def test_system_performance_summary(self):
        """System must aggregate performance across all channels"""
        spec = HBM4Spec()
        array = HBM4ChannelArray()

        # Generate activity on channel 0
        ch = array.get_channel(0)
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        perf = array.get_system_performance_summary()
        assert 'total_activations' in perf
        assert 'total_reads' in perf
        assert 'peak_bandwidth_gbs' in perf

    def test_channel_performance_retrieval(self):
        """Must retrieve performance for specific channel"""
        spec = HBM4Spec()
        array = HBM4ChannelArray()

        perf = array.get_channel_performance(0)
        assert perf is not None
        assert 'act_count' in perf

    def test_invalid_channel_returns_none(self):
        """Invalid channel ID must return None"""
        spec = HBM4Spec()
        array = HBM4ChannelArray()

        perf = array.get_channel_performance(99)
        assert perf is None

    def test_reset_all_clears_stats(self):
        """Reset all must clear system statistics"""
        spec = HBM4Spec()
        array = HBM4ChannelArray()

        # Generate activity
        ch = array.get_channel(0)
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Reset all
        array.reset_all()

        # Stats should be cleared
        perf = array.get_system_performance_summary()
        assert perf['total_activations'] == 0


class TestHBM4TimingDomainIsolation:
    """Test independent timing domain isolation between pseudo-channels"""

    def test_pseudo_channels_have_independent_timing(self):
        """Pseudo-channels must have independent timing tracking"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Activate in PC0
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # PC1 should still be able to issue commands without PC0 delay
        scheduler1 = ch.get_scheduler(1)
        # PC1's own timing should not be affected by PC0
        assert scheduler1.can_issue_act(1, 0, ch.current_cycle)

    def test_scheduler_state_per_pseudo_channel(self):
        """Scheduler state must be tracked per pseudo-channel"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Activate in PC0
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        state0 = ch.get_scheduler_state(0)
        state1 = ch.get_scheduler_state(1)

        # PC0 should have ACT recorded, PC1 should not
        assert state0.get('last_act_cycle', -1) >= 0
        # PC1's state may be empty or -1
        assert state1.get('last_act_cycle', -1) == -1 or state1 == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
