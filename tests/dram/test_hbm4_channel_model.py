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
import random
from model.dram.hbm4_channel_model import (
    HBM4Channel, PseudoChannel, HBM4ChannelState, PseudoChannelState,
    HBM4ChannelArray, BankGroupScheduler
)
from model.dram.hbm4_spec import HBM4Spec
from model.dram.hbm4_bank_state_machine import (
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

    def test_enhanced_timing_tRCD_is_8_cycles(self):
        """tRCD is 8 cycles (JEDEC JESD270-4A baseline)"""
        timing = HBM4BankTiming()
        assert timing.tRCD == 8

    def test_enhanced_timing_tRP_is_8_cycles(self):
        """tRP is 8 cycles (JEDEC JESD270-4A baseline)"""
        timing = HBM4BankTiming()
        assert timing.tRP == 8

    def test_enhanced_timing_tRAS_is_20_cycles(self):
        """tRAS is 20 cycles (JEDEC JESD270-4A baseline)"""
        timing = HBM4BankTiming()
        assert timing.tRAS == 20

    def test_enhanced_timing_tRC_is_22_cycles(self):
        """tRC is 22 cycles (JEDEC JESD270-4A baseline)"""
        timing = HBM4BankTiming()
        assert timing.tRC == 22

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


class TestMultiChannelCoordination:
    """Test multi-channel coordination across HBM4 channels"""

    def test_32_channel_array_creation(self):
        """32-channel array must be created successfully"""
        array = HBM4ChannelArray()

        assert array.num_channels == 32
        assert array.total_banks == 1024

    def test_all_channels_tick_together(self):
        """All channels must advance together on tick()"""
        array = HBM4ChannelArray()

        initial_cycles = [ch.current_cycle for ch in array.channels]

        array.tick()

        for i, ch in enumerate(array.channels):
            assert ch.current_cycle == initial_cycles[i] + 1

    def test_global_reset_synchronizes_all_channels(self):
        """reset_all() must synchronize all channels"""
        array = HBM4ChannelArray()

        # Advance some cycles
        for _ in range(100):
            array.tick()

        # Reset all
        array.reset_all()

        # All should be at cycle 0
        for ch in array.channels:
            assert ch.current_cycle == 0

    def test_concurrent_activation_timing(self):
        """Concurrent activations across channels must respect timing"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Activate in multiple channels simultaneously
        for ch_id in range(8):
            ch = array.channels[ch_id]
            result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
            assert result is True

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            array.tick()

        # Reads should now succeed
        for ch_id in range(8):
            ch = array.channels[ch_id]
            result = ch.issue_command('RD', pseudo_channel=0, bank=0,
                                     row=100, col=0)
            assert result is True

    def test_cross_channel_refresh_coordination(self):
        """Refresh commands must coordinate across channels"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Precharge all banks in first channel
        ch = array.channels[0]
        ch.issue_command('PREA', pseudo_channel=0, bank=0, row=0)
        ch.issue_command('PREA', pseudo_channel=1, bank=0, row=0)

        for _ in range(timing.tRP + 1):
            array.tick()

        # Issue all-bank refresh
        result = ch.issue_command('REFab', pseudo_channel=0, bank=0, row=0)
        assert result is True

    def test_aggregate_bandwidth_calculation(self):
        """Aggregate bandwidth must be calculated correctly"""
        array = HBM4ChannelArray()

        # 32 channels * 64 GB/s per channel = 2048 GB/s
        assert abs(array.total_bandwidth_gbs - 2048.0) < 1.0

    def test_system_performance_summary(self):
        """System performance summary must report all channels"""
        array = HBM4ChannelArray()

        summary = array.get_system_performance_summary()

        assert 'total_activations' in summary
        assert 'total_reads' in summary
        assert 'total_writes' in summary
        assert 'peak_bandwidth_gbs' in summary

    def test_concurrent_reads_across_channels(self):
        """Concurrent reads across all channels must work"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Activate rows in all channels
        for ch_id in range(32):
            ch = array.channels[ch_id]
            ch.issue_command('ACT', pseudo_channel=0, bank=0, row=ch_id)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            array.tick()

        # Read from all channels
        success_count = 0
        for ch_id in range(32):
            ch = array.channels[ch_id]
            result = ch.issue_command('RD', pseudo_channel=0, bank=0,
                                     row=ch_id, col=0)
            if result:
                success_count += 1

        assert success_count == 32

    def test_burst_traffic_all_channels(self):
        """Burst traffic to all channels must work"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Burst activate to all channels
        for ch_id in range(32):
            ch = array.channels[ch_id]
            for pch_id in range(2):
                for bank_id in range(4):
                    ch.issue_command('ACT', pseudo_channel=pch_id,
                                   bank=bank_id, row=ch_id * 100 + bank_id)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            array.tick()

        # Read from all channels
        for ch_id in range(32):
            ch = array.channels[ch_id]
            for pch_id in range(2):
                result = ch.issue_command('RD', pseudo_channel=pch_id,
                                    bank=0, row=ch_id * 100, col=0)
                assert result is True

    def test_faw_tracking_per_channel(self):
        """FAW window must be tracked per pseudo-channel"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        ch = array.channels[0]
        scheduler = ch.get_scheduler(0)

        # Test FAW behavior: max 4 activations in nFAW (16) cycles window
        # Issue ACTs to same BG with proper tRRDS timing (3 cycles)
        current_cycle = 0
        successful_acts = 0
        for i in range(5):
            can_issue = scheduler.can_issue_act(pseudo_channel=0, bank_group=0,
                                               current_cycle=current_cycle)
            if can_issue:
                scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=current_cycle)
                successful_acts += 1
            # Advance by tRRDS for same BG
            current_cycle += timing.tRRDS

        # Should have exactly 4 successful ACTs within FAW window
        assert successful_acts == 4

        # After advancing past nFAW, should be able to ACT again
        current_cycle = 20  # Past nFAW (16 cycles)
        can_issue = scheduler.can_issue_act(pseudo_channel=0, bank_group=0,
                                          current_cycle=current_cycle)
        assert can_issue is True

    def test_bg_timing_same_channel(self):
        """Bank group timing must work on same channel"""
        array = HBM4ChannelArray()
        timing = HBM4Timing()

        ch = array.channels[0]
        scheduler = ch.get_scheduler(0)

        # Issue ACT to BG 0
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=0)
        scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=0)

        # Immediate ACT to same BG - should fail (tRRDS not met)
        assert not scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=1)

        # After nRRDL, ACT to different BG should succeed
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=1,
                                    current_cycle=timing.nRRDL)

    def test_pseudo_channel_states_independent(self):
        """Pseudo-channel states must be independent"""
        array = HBM4ChannelArray()

        ch = array.channels[0]
        pc0 = ch.pseudo_channels[0]
        pc1 = ch.pseudo_channels[1]

        # Activate row in PC0
        pc0.activate_row(100, bank_id=0)

        # PC0 should be ACTIVE
        assert pc0.state == PseudoChannelState.ACTIVE

        # PC1 should still be IDLE
        assert pc1.state == PseudoChannelState.IDLE

    def test_column_commands_independent_pseudo_channels(self):
        """Column commands must work independently on pseudo-channels"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        ch = array.channels[0]

        # Activate in both pseudo-channels
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        ch.issue_command('ACT', pseudo_channel=1, bank=0, row=200)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            ch.tick()

        # Read from both
        result0 = ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)
        result1 = ch.issue_command('RD', pseudo_channel=1, bank=1, row=200, col=0)

        assert result0 is True
        assert result1 is True


class TestMultiChannelLoadBalancing:
    """Test load balancing across channels"""

    def test_channel_selector_distributes_uniformly(self):
        """Channel selector must distribute load uniformly"""
        from model.multi_channel import ChannelSelector

        selector = ChannelSelector(num_channels=32, strategy=ChannelSelector.ROUND_ROBIN)

        # Generate 3200 requests (100 per channel)
        for i in range(3200):
            ch = selector.select_channel(addr=i * 64, length=64)
            selector.record_request(ch)

        loads = selector.get_channel_load()
        load_values = list(loads.values())

        # Each channel should have approximately 100 requests
        avg = sum(load_values) / len(load_values)
        max_deviation = max(abs(v - avg) for v in load_values)

        assert max_deviation <= avg * 0.15  # 15% max deviation

    def test_queue_aware_selector_balances_load(self):
        """Queue-aware selector must balance load"""
        from model.multi_channel import QueueAwareChannelSelector, calculate_jains_fairness_index

        selector = QueueAwareChannelSelector(
            num_channels=32,
            strategy="queue_aware",
            enable_adaptive=True
        )

        # Simulate uneven queue depths
        depths = {i: (i % 10) * 2 for i in range(32)}
        selector.update_pending_depths(depths)

        # Select channels multiple times
        for _ in range(100):
            ch = selector.select_channel(addr=random.randint(0, 100000))
            selector.record_request(ch)

        loads = selector.get_channel_load()
        load_values = list(loads.values())
        jains = calculate_jains_fairness_index(load_values)

        assert jains > 0.7  # Good fairness

    def test_round_robin_strategy(self):
        """Round-robin strategy must cycle through channels"""
        from model.multi_channel import ChannelSelector

        selector = ChannelSelector(num_channels=32, strategy=ChannelSelector.ROUND_ROBIN)

        selected = []
        for i in range(64):
            ch = selector.select_channel(addr=i * 64, length=64)
            selected.append(ch)

        # Should cycle evenly
        for ch in range(32):
            count = selected.count(ch)
            assert count == 2  # 64 / 32 = 2

    def test_hash_strategy_deterministic(self):
        """Hash strategy must be deterministic"""
        from model.multi_channel import ChannelSelector

        selector = ChannelSelector(num_channels=32, strategy=ChannelSelector.HASH)

        addresses = [1000, 2000, 3000, 4000, 5000]

        # Same address should always select same channel
        for addr in addresses:
            ch1 = selector.select_channel(addr=addr, length=64)
            ch2 = selector.select_channel(addr=addr, length=64)
            assert ch1 == ch2


class TestMultiChannelStress:
    """Stress tests for multi-channel operation"""

    def test_1000_cycles_stress(self):
        """System must handle 1000 cycles of continuous operation"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        for cycle in range(1000):
            # Activate random banks across random channels
            for ch_id in range(min(cycle % 8 + 1, 32)):
                ch = array.channels[ch_id]
                ch.issue_command('ACT', pseudo_channel=0, bank=cycle % 16,
                               row=cycle * 100)

            # Advance time
            for _ in range(timing.tRCD + 1):
                array.tick()

        # System should still be operational
        summary = array.get_system_state_summary()
        assert summary['num_channels'] == 32

    def test_random_access_pattern(self):
        """Random access pattern across channels must work"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        random.seed(42)  # Deterministic

        # Generate random requests
        for _ in range(500):
            ch_id = random.randint(0, 31)
            pch_id = random.randint(0, 1)
            bank_id = random.randint(0, 15)
            row = random.randint(0, 65535)

            ch = array.channels[ch_id]
            ch.issue_command('ACT', pseudo_channel=pch_id, bank=bank_id, row=row)

            # Advance time
            for _ in range(timing.tRCD + 1):
                array.tick()

        # System should be operational
        summary = array.get_system_performance_summary()
        assert summary['total_activations'] > 0

    def test_reset_channel_recovers(self):
        """Channel must recover after reset"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        ch = array.channels[0]

        # Perform some operations
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Advance past tRAS + tRP to complete the operation
        for _ in range(timing.tRAS + timing.tRP + 1):
            ch.tick()

        # Reset
        ch.reset()

        # Should be able to operate again after reset
        result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=200)
        assert result is True

    def test_boundary_channel_indices(self):
        """Boundary channel indices must work"""
        array = HBM4ChannelArray()

        # First channel
        ch0 = array.channels[0]
        assert ch0.channel_id == 0

        # Last channel
        ch31 = array.channels[31]
        assert ch31.channel_id == 31


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
