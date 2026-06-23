"""
Tests for HBM4 Channel Model - Enhanced Version

Tests the enhanced HBM4 channel model with bank group organization,
bank group-aware timing, and system-level channel array functionality.

Reference: JEDEC JESD270-4A HBM4 specification
"""

import pytest
from model.dram.hbm4_channel_model import (
    HBM4Channel, PseudoChannel, HBM4ChannelState, PseudoChannelState,
    HBM4Command, BankGroup, BankGroupScheduler, HBM4ChannelArray
)
from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.timing import HBM4Timing, get_timing_for_speed_grade


# =============================================================================
# Test HBM4 Channel Creation
# =============================================================================
class TestHBM4ChannelCreation:
    """Test HBM4 channel creation"""

    def test_channel_creation_with_default_spec(self):
        """Channel must be created successfully with default spec"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert ch.channel_id == 0
        assert ch.spec.channels == 32
        assert len(ch.pseudo_channels) == 2

    def test_channel_creation_with_custom_spec(self):
        """Channel must work with custom spec"""
        spec = HBM4Spec(
            channels=32,
            pseudo_channels_per_channel=2,
            banks_per_pseudo_channel=16,
            bank_groups_per_channel=8
        )
        ch = HBM4Channel(5, spec)

        assert ch.channel_id == 5
        assert ch.spec.channels == 32

    def test_channel_has_two_pseudo_channels(self):
        """Each channel must have 2 pseudo-channels"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert len(ch.pseudo_channels) == 2
        assert ch.pseudo_channels[0].pseudo_channel_id == 0
        assert ch.pseudo_channels[1].pseudo_channel_id == 1

    def test_create_with_speed_grade_8gbps(self):
        """Must create channel with 8Gbps speed grade"""
        ch = HBM4Channel.create_with_speed_grade(0, "8Gbps")

        assert ch.spec.data_rate_gtps == 8.0
        assert ch.timing.tCK_ps == 125.0

    def test_create_with_speed_grade_12gbps(self):
        """Must create channel with 12Gbps speed grade"""
        ch = HBM4Channel.create_with_speed_grade(0, "12Gbps")

        assert ch.spec.data_rate_gtps == 12.0
        assert abs(ch.timing.tCK_ps - 83.33) < 0.1

    def test_create_with_speed_grade_16gbps(self):
        """Must create channel with 16Gbps speed grade"""
        ch = HBM4Channel.create_with_speed_grade(0, "16Gbps")

        assert ch.spec.data_rate_gtps == 16.0
        assert abs(ch.timing.tCK_ps - 62.5) < 0.1


# =============================================================================
# Test Bank Group Organization
# =============================================================================
class TestBankGroupOrganization:
    """Test bank group organization in pseudo-channels"""

    def test_pseudo_channel_has_8_bank_groups(self):
        """Each pseudo-channel must have 8 bank groups"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        assert len(pc0.bank_groups) == 8

    def test_bank_group_has_2_banks(self):
        """Each bank group must have 2 banks"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        for bg in pc0.bank_groups:
            assert bg.num_banks == 2
            assert len(bg.bank_indices) == 2

    def test_bank_group_indices_correct(self):
        """Bank group indices must be correctly mapped"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # BG0 should have banks 0, 1
        assert pc0.bank_groups[0].bank_indices == [0, 1]
        # BG1 should have banks 2, 3
        assert pc0.bank_groups[1].bank_indices == [2, 3]
        # BG7 should have banks 14, 15
        assert pc0.bank_groups[7].bank_indices == [14, 15]

    def test_get_bank_group_for_bank_id(self):
        """Must correctly identify bank group for a bank ID"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # Bank 0-1 should be in BG0
        assert pc0.get_bank_group(0).group_id == 0
        assert pc0.get_bank_group(1).group_id == 0
        # Bank 2-3 should be in BG1
        assert pc0.get_bank_group(2).group_id == 1
        # Bank 14-15 should be in BG7
        assert pc0.get_bank_group(14).group_id == 7
        assert pc0.get_bank_group(15).group_id == 7

    def test_get_bank_in_group(self):
        """Must retrieve correct bank within bank group"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # BG0, index 0 should be bank 0
        bank = pc0.get_bank_in_group(0, 0)
        assert bank.bank.bank_id == 0

        # BG3, index 1 should be bank 7
        bank = pc0.get_bank_in_group(3, 1)
        assert bank.bank.bank_id == 7

    def test_total_banks_in_pseudo_channel(self):
        """Total banks in pseudo-channel must be 16 (8 BG × 2 banks)"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        total_banks = sum(bg.num_banks for bg in pc0.bank_groups)
        assert total_banks == 16
        assert len(pc0.banks) == 16


# =============================================================================
# Test Bank Group Properties
# =============================================================================
class TestBankGroupProperties:
    """Test bank group properties and state tracking"""

    def test_bank_group_initial_state(self):
        """Bank group must start with no activations"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        bg0 = pc0.bank_groups[0]

        assert bg0.last_act_cycle < 0
        assert bg0.current_cycle == 0

    def test_bank_group_record_activation(self):
        """Bank group must record activation time"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        bg0 = pc0.bank_groups[0]

        # Set time on the bank group directly
        bg0.set_time(100)
        bg0.record_activation(100)

        assert bg0.last_act_cycle == 100

    def test_bank_group_can_activate_initially(self):
        """Bank group must be activatable initially"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        bg0 = pc0.bank_groups[0]

        assert bg0.can_activate_bank_group()

    def test_bank_group_timing_constraint_same_bg(self):
        """tRRDS must be enforced for same BG activation"""
        spec = HBM4Spec()
        timing = HBM4Timing()
        ch = HBM4Channel(0, spec, timing)

        pc0 = ch.pseudo_channels[0]
        bg0 = pc0.bank_groups[0]

        # First activation at cycle 0
        bg0.set_time(0)
        bg0.record_activation(0)

        # tRRDS = 3 cycles, so at cycle 2 should not be able to activate
        assert not bg0.can_activate_bank_group(2)

        # At 3 cycles, should be able to activate
        assert bg0.can_activate_bank_group(3)


# =============================================================================
# Test Bank Group-Aware Activation
# =============================================================================
class TestBankGroupAwareActivation:
    """Test activation with bank group awareness"""

    def test_activate_row_in_bank_group(self):
        """Must activate row in specific bank group"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # Activate row 100 in BG0, bank index 0
        result = pc0.activate_row_in_bank_group(0, 0, 100)

        assert result is True
        bank = pc0.get_bank_in_group(0, 0)
        # Bank should be in ACTIVATING state immediately after activation
        # (transitions to OPEN after tRCD=12 cycles)
        assert bank.bank.is_activating
        assert bank.bank.open_row == 100

    def test_activate_row_updates_bank_group_state(self):
        """Activation must update bank group state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # Activate in BG3
        pc0.activate_row_in_bank_group(3, 1, 200)

        bg3 = pc0.bank_groups[3]
        assert bg3.last_act_cycle >= 0

    def test_both_banks_in_group_can_be_active(self):
        """Both banks in a bank group can be active"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # Activate both banks in BG2
        pc0.activate_row_in_bank_group(2, 0, 100)
        pc0.activate_row_in_bank_group(2, 1, 200)

        bank0 = pc0.get_bank_in_group(2, 0)
        bank1 = pc0.get_bank_in_group(2, 1)

        # Both banks should be in ACTIVATING state immediately after activation
        # (transitions to OPEN after tRCD=12 cycles)
        assert bank0.bank.is_activating
        assert bank1.bank.is_activating

    def test_issue_command_with_bank_group(self):
        """Must issue command with bank group targeting"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        result = ch.issue_command_with_bank_group(
            'ACT', pseudo_channel=0,
            bank_group=3, bank_in_group=1,
            row=100
        )

        assert result is True
        # Bank should be in ACTIVATING state immediately after activation
        # (transitions to OPEN after tRCD=12 cycles)
        bank = ch.get_bank(0, 7)  # BG3, index 1 = bank 7
        assert bank.bank.is_activating


# =============================================================================
# Test Bank Group Scheduler
# =============================================================================
class TestBankGroupScheduler:
    """Test bank group-aware command scheduler"""

    def test_scheduler_creation(self):
        """Scheduler must be created successfully"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        assert scheduler.timing is timing

    def test_can_issue_act_initially(self):
        """Must be able to issue ACT initially"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=0)

    def test_faw_limits_activations(self):
        """FAW window must limit to 4 activations"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # FAW allows 4 activations within nFAW=16 cycles
        # Use different bank groups to avoid tRRDL constraint (4 cycles)
        # But within same BG we need tRRDS=3 cycles spacing
        # Issue 4 activations across cycles 0, 3, 6, 9 (3-cycle spacing for same BG)
        cycles = [0, 3, 6, 9]
        for i, cycle in enumerate(cycles):
            result = scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=cycle)
            assert result is True, f"Activation {i} at cycle {cycle} should succeed"
            scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=cycle)

        # 5th activation within FAW window should fail
        result = scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=10)
        assert result is False, "5th activation should fail due to FAW limit"

    def test_faw_window_expiration(self):
        """FAW window must expire after nFAW cycles"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # Issue 4 activations
        for i in range(4):
            scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=i)

        # 5th should fail
        assert not scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=4)

        # After FAW window expires (nFAW = 16), should succeed
        expired_cycle = 20
        result = scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=expired_cycle)
        assert result is True

    def test_rrd_same_bank_group(self):
        """tRRDS must be enforced for same BG"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # First activation at cycle 0
        scheduler.record_act(pseudo_channel=0, bank_group=2, current_cycle=0)

        # Same BG at 2 cycles - should fail (tRRDS = 3)
        assert not scheduler.can_issue_act(pseudo_channel=0, bank_group=2, current_cycle=2)

        # Same BG at 3 cycles - should succeed
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=2, current_cycle=3)

    def test_rrd_different_bank_group(self):
        """tRRDL must be enforced for different BG"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # First activation at cycle 0
        scheduler.record_act(pseudo_channel=0, bank_group=2, current_cycle=0)

        # Different BG at 3 cycles - should fail (tRRDL = 4)
        assert not scheduler.can_issue_act(pseudo_channel=0, bank_group=3, current_cycle=3)

        # Different BG at 4 cycles - should succeed
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=3, current_cycle=4)

    def test_column_command_tracking(self):
        """Column commands must be tracked for turnaround"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # Record a read in BG2 at cycle 0
        scheduler.record_col(pseudo_channel=0, bank_group=2, current_cycle=0, is_write=False)

        # Write in same BG before RTW should fail
        assert not scheduler.can_issue_col(pseudo_channel=0, bank_group=2, current_cycle=2, is_write=True)

        # Write after RTW should succeed
        assert scheduler.can_issue_col(pseudo_channel=0, bank_group=2, current_cycle=5, is_write=True)

    def test_ccds_same_bg(self):
        """nCCDS must be enforced for same BG same direction"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # Record a read in BG2 at cycle 0
        scheduler.record_col(pseudo_channel=0, bank_group=2, current_cycle=0, is_write=False)

        # Read in same BG at 1 cycle - should fail (nCCDS = 2)
        assert not scheduler.can_issue_col(pseudo_channel=0, bank_group=2, current_cycle=1, is_write=False)

        # Read in same BG at 2 cycles - should succeed
        assert scheduler.can_issue_col(pseudo_channel=0, bank_group=2, current_cycle=2, is_write=False)

    def test_ccdl_different_bg(self):
        """nCCDL must be enforced for different BG same direction"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # Record a read in BG2 at cycle 0
        scheduler.record_col(pseudo_channel=0, bank_group=2, current_cycle=0, is_write=False)

        # Read in different BG at 2 cycles - should fail (nCCDL = 3)
        assert not scheduler.can_issue_col(pseudo_channel=0, bank_group=3, current_cycle=2, is_write=False)

        # Read in different BG at 3 cycles - should succeed
        assert scheduler.can_issue_col(pseudo_channel=0, bank_group=3, current_cycle=3, is_write=False)

    def test_reset(self):
        """Reset must clear all state"""
        timing = HBM4Timing()
        scheduler = BankGroupScheduler(timing)

        # Record some commands
        scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=0)
        scheduler.record_col(pseudo_channel=0, bank_group=0, current_cycle=0, is_write=False)

        # Reset
        scheduler.reset()

        # Should be able to issue ACT again
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=100)


# =============================================================================
# Test Channel Command Handling
# =============================================================================
class TestChannelCommandHandling:
    """Test channel command issuance"""

    def test_issue_command_act(self):
        """ACT command must activate a row"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        assert result is True
        # Bank should be in ACTIVATING state immediately after activation
        # (transitions to OPEN after tRCD=12 cycles)
        pc0 = ch.pseudo_channels[0]
        active_banks = [b for b in pc0.banks if b.bank.is_activating]
        assert len(active_banks) > 0

    def test_issue_command_precharge(self):
        """PRE command must precharge banks"""
        from model.dram.hbm4_bank_state_machine import HBM4BankTiming
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Activate first
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Advance time using tick to meet tRAS timing requirement
        # tRAS = 28 cycles for bank timing, need 29 ticks minimum
        bank_timing = HBM4BankTiming()
        for _ in range(bank_timing.tRAS + 1):
            ch.tick()

        # Precharge - should now succeed after tRAS is satisfied
        result = ch.issue_command('PRE', pseudo_channel=0, bank=0, row=0)

        assert result is True

    def test_issue_command_read(self):
        """RD command must work"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        result = ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        assert result is True

    def test_issue_command_write(self):
        """WR command must work"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        result = ch.issue_command('WR', pseudo_channel=0, bank=0, row=100, col=0)

        assert result is True

    def test_issue_command_refresh(self):
        """REFab command must trigger refresh"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        result = ch.issue_command('REFab', pseudo_channel=0, bank=0, row=0)

        assert result is True

    def test_numeric_command_encoding(self):
        """Numeric command encoding must work"""
        from model.dram.hbm4_bank_state_machine import HBM4BankTiming
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # ACT = 1
        result = ch.issue_numeric_command(HBM4Command.ACT, pseudo_channel=0, bank=0, row=100)
        assert result is True

        # Advance time to meet tRAS timing requirement using tick
        # tRAS = 28 cycles for bank timing, need 29 ticks minimum
        bank_timing = HBM4BankTiming()
        for _ in range(bank_timing.tRAS + 1):
            ch.tick()

        # PRE = 4 - needs time after ACT to satisfy tRAS
        result = ch.issue_numeric_command(HBM4Command.PRE, pseudo_channel=0, bank=0, row=0)
        assert result is True


# =============================================================================
# Test Pseudo-Channel State Transitions
# =============================================================================
class TestPseudoChannelStateTransitions:
    """Test pseudo-channel state transitions"""

    def test_pseudo_channel_starts_idle(self):
        """Pseudo-channel must start in IDLE state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        assert pc0.state == PseudoChannelState.IDLE

    def test_pseudo_channel_transitions_to_active(self):
        """Pseudo-channel must transition to ACTIVE on activation"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        pc0.activate_row(100)

        assert pc0.state == PseudoChannelState.ACTIVE

    def test_pseudo_channel_transitions_to_reading(self):
        """Pseudo-channel must transition to READING state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        assert ch.pseudo_channels[0].state == PseudoChannelState.READING

    def test_pseudo_channel_transitions_to_writing(self):
        """Pseudo-channel must transition to WRITING state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('WR', pseudo_channel=0, bank=0, row=100, col=0)

        assert ch.pseudo_channels[0].state == PseudoChannelState.WRITING

    def test_pseudo_channel_transitions_to_refreshing(self):
        """Pseudo-channel must transition to REFRESHING state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('REFab', pseudo_channel=0, bank=0, row=0)

        assert ch.pseudo_channels[0].state == PseudoChannelState.REFRESHING


# =============================================================================
# Test Channel Timing
# =============================================================================
class TestChannelTiming:
    """Test channel timing advancement"""

    def test_tick_advances_time(self):
        """tick() must advance internal cycle counter"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        initial_cycle = ch.current_cycle
        ch.tick()

        assert ch.current_cycle == initial_cycle + 1

    def test_tick_advances_pseudo_channels(self):
        """tick() must advance all pseudo-channel times"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        initial_time = ch.pseudo_channels[0].current_time
        ch.tick()

        # After tick, pseudo-channel time should equal channel cycle
        assert ch.pseudo_channels[0].current_time == float(ch.current_cycle)
        assert ch.pseudo_channels[1].current_time == float(ch.current_cycle)

    def test_tick_advances_bank_groups(self):
        """tick() must advance all bank group times"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.tick()

        # Bank group times are tracked via the bank array
        for pc in ch.pseudo_channels:
            for bank in pc.banks:
                # Each bank's current_cycle should equal channel cycle
                assert bank.current_cycle == ch.current_cycle

    def test_refresh_completes_after_tick(self):
        """Refresh must complete after sufficient ticks"""
        spec = HBM4Spec()
        timing = HBM4Timing()
        ch = HBM4Channel(0, spec, timing)

        # Issue refresh
        ch.issue_command('REFab', pseudo_channel=0, bank=0, row=0)
        assert ch.pseudo_channels[0].state == PseudoChannelState.REFRESHING

        # Tick through refresh
        for _ in range(timing.nRFC + 1):
            ch.tick()

        assert ch.pseudo_channels[0].state == PseudoChannelState.IDLE


# =============================================================================
# Test HBM4 Channel Array
# =============================================================================
class TestHBM4ChannelArray:
    """Test HBM4 channel array (system-level)"""

    def test_channel_array_creation(self):
        """Channel array must be created successfully"""
        array = HBM4ChannelArray()

        assert len(array.channels) == 32

    def test_get_channel(self):
        """Must retrieve specific channel"""
        array = HBM4ChannelArray()

        ch = array.get_channel(15)
        assert ch is not None
        assert ch.channel_id == 15

    def test_get_invalid_channel(self):
        """Must return None for invalid channel ID"""
        array = HBM4ChannelArray()

        assert array.get_channel(32) is None
        assert array.get_channel(-1) is None

    def test_get_pseudo_channel(self):
        """Must retrieve specific pseudo-channel"""
        array = HBM4ChannelArray()

        pc = array.get_pseudo_channel(10, 1)
        assert pc is not None
        assert pc.pseudo_channel_id == 1

    def test_tick_advances_all_channels(self):
        """tick() must advance all channels"""
        array = HBM4ChannelArray()

        array.tick()

        for ch in array.channels:
            assert ch.current_cycle == 1

    def test_total_bandwidth_calculation(self):
        """Total bandwidth must be calculated correctly"""
        array = HBM4ChannelArray()

        total_gbs = array.total_bandwidth_gbs
        # 32 channels × 64 GB/s per channel = 2048 GB/s
        expected = 32 * 64.0
        assert abs(total_gbs - expected) < 1.0

        total_tbs = array.total_bandwidth_tbs
        assert abs(total_tbs - 2.048) < 0.001

    def test_system_state_summary(self):
        """System state summary must include all channels"""
        array = HBM4ChannelArray()

        summary = array.get_system_state_summary()

        assert summary['num_channels'] == 32
        assert summary['total_pseudo_channels'] == 64
        assert summary['total_bank_groups'] == 512  # 32 × 2 × 8
        assert summary['total_banks'] == 1024  # 32 × 2 × 16


# =============================================================================
# Test Bandwidth Calculations
# =============================================================================
class TestBandwidthCalculations:
    """Test bandwidth calculations"""

    def test_peak_bandwidth_per_channel(self):
        """Each channel provides 64 GB/s at 8 GT/s"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # Per channel: 8 GT/s × 64 bits / 8 = 64 GB/s
        assert abs(ch.peak_bandwidth_gbs - 64.0) < 0.1

    def test_peak_bandwidth_tbs(self):
        """Peak bandwidth in TB/s must be correct"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert abs(ch.peak_bandwidth_tbs - 0.064) < 0.001

    def test_aggregate_bandwidth_32_channels(self):
        """32 channels must provide 2 TB/s aggregate"""
        spec = HBM4Spec()

        total = sum(HBM4Channel(i, spec).peak_bandwidth_gbs for i in range(32))
        assert abs(total - 2048.0) < 1.0

    def test_bandwidth_with_12gbps(self):
        """12 GT/s must provide higher bandwidth"""
        ch_8 = HBM4Channel.create_with_speed_grade(0, "8Gbps")
        ch_12 = HBM4Channel.create_with_speed_grade(0, "12Gbps")

        assert ch_12.peak_bandwidth_gbs > ch_8.peak_bandwidth_gbs


# =============================================================================
# Test Channel Properties
# =============================================================================
class TestChannelProperties:
    """Test channel computed properties"""

    def test_total_pseudo_channels(self):
        """total_pseudo_channels must be 64"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert ch.total_pseudo_channels == 64

    def test_total_bank_groups(self):
        """total_bank_groups must be 8 per channel"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert ch.total_bank_groups == 8

    def test_banks_per_bank_group(self):
        """banks_per_bank_group must be 2"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert ch.banks_per_bank_group == 2


# =============================================================================
# Test State Summary
# =============================================================================
class TestStateSummary:
    """Test channel state summary generation"""

    def test_channel_state_summary(self):
        """State summary must include all state information"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        summary = ch.get_state_summary()

        assert 'channel_id' in summary
        assert 'state' in summary
        assert 'pseudo_channels' in summary
        assert 'current_cycle' in summary

        assert len(summary['pseudo_channels']) == 2

    def test_pseudo_channel_in_summary(self):
        """Pseudo-channel summary must include bank groups"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        summary = ch.get_state_summary()
        pc_summary = summary['pseudo_channels'][0]

        assert 'id' in pc_summary
        assert 'state' in pc_summary
        assert 'open_row' in pc_summary
        assert 'active_banks' in pc_summary
        assert 'bank_groups' in pc_summary

        assert len(pc_summary['bank_groups']) == 8

    def test_bank_group_in_summary(self):
        """Bank group summary must include active banks count"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        summary = ch.get_state_summary()
        pc_summary = summary['pseudo_channels'][0]
        bg_summary = pc_summary['bank_groups'][0]

        assert 'id' in bg_summary
        assert 'active_banks' in bg_summary


# =============================================================================
# Test Row Hit Detection
# =============================================================================
class TestRowHitDetection:
    """Test row hit/miss detection"""

    def test_row_open_after_activation(self):
        """Row must be open after activation"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        assert ch.is_row_hit(0, 100)

    def test_different_row_not_hit(self):
        """Different row must not be hit"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        assert not ch.is_row_hit(0, 200)

    def test_row_open_after_read(self):
        """Row must be open after read command"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        assert ch.is_row_hit(0, 100)

    def test_row_open_after_write(self):
        """Row must be open after write command"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('WR', pseudo_channel=0, bank=0, row=100, col=0)

        assert ch.is_row_hit(0, 100)


# =============================================================================
# Test Command Scheduling
# =============================================================================
class TestCommandScheduling:
    """Test bank group-aware command scheduling"""

    def test_can_schedule_act_initially(self):
        """Must be able to schedule ACT initially"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        assert ch.can_schedule_command('ACT', pseudo_channel=0, bank_group=0)

    def test_can_schedule_read(self):
        """Must be able to schedule read if row open"""
        from model.dram.hbm4_bank_state_machine import HBM4BankTiming
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Advance time past tRCD (12 cycles for bank timing, need 13 ticks)
        bank_timing = HBM4BankTiming()
        for _ in range(bank_timing.tRCD + 1):
            ch.tick()

        assert ch.can_schedule_command('RD', pseudo_channel=0, bank_group=0)

    def test_can_schedule_write(self):
        """Must be able to schedule write if row open"""
        from model.dram.hbm4_bank_state_machine import HBM4BankTiming
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Advance time past tRCD (12 cycles for bank timing, need 13 ticks)
        bank_timing = HBM4BankTiming()
        for _ in range(bank_timing.tRCD + 1):
            ch.tick()

        assert ch.can_schedule_command('WR', pseudo_channel=0, bank_group=0)


# =============================================================================
# Test HBM4Command Enum
# =============================================================================
class TestHBM4CommandEnum:
    """Test HBM4Command enum operations"""

    def test_command_from_string(self):
        """Must convert command string to enum"""
        assert HBM4Command.from_string('ACT') == HBM4Command.ACT
        assert HBM4Command.from_string('RD') == HBM4Command.READ
        assert HBM4Command.from_string('WR') == HBM4Command.WRITE
        assert HBM4Command.from_string('PRE') == HBM4Command.PRE
        assert HBM4Command.from_string('REFab') == HBM4Command.REF

    def test_command_to_string(self):
        """Must convert enum to command string"""
        assert HBM4Command.to_string(HBM4Command.ACT) == 'ACT'
        assert HBM4Command.to_string(HBM4Command.READ) == 'RD'
        assert HBM4Command.to_string(HBM4Command.WRITE) == 'WR'
        assert HBM4Command.to_string(HBM4Command.PRE) == 'PRE'
        assert HBM4Command.to_string(HBM4Command.REF) == 'REF'

    def test_command_numeric_values(self):
        """Command numeric values must match RTL encoding"""
        assert HBM4Command.NOP == 0
        assert HBM4Command.ACT == 1
        assert HBM4Command.READ == 2
        assert HBM4Command.WRITE == 3
        assert HBM4Command.PRE == 4
        assert HBM4Command.PREA == 5
        assert HBM4Command.REF == 6
        assert HBM4Command.RFM == 7


# =============================================================================
# Test Bank Group State Queries
# =============================================================================
class TestBankGroupStateQueries:
    """Test bank group state queries"""

    def test_get_bank_group_state(self):
        """Must return bank group state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        state = pc0.get_bank_group_state(0)

        assert 'group_id' in state
        assert 'last_act_cycle' in state
        assert 'active_banks' in state
        assert state['group_id'] == 0

    def test_bank_group_state_updates_on_activation(self):
        """Bank group state must update on activation"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        pc0.activate_row_in_bank_group(3, 1, 100)

        state = pc0.get_bank_group_state(3)
        assert state['active_banks'] == 1


# =============================================================================
# Test Pseudo-Channel Independence
# =============================================================================
class TestPseudoChannelIndependence:
    """Test pseudo-channel independence"""

    def test_pseudo_channels_do_not_interfere(self):
        """Activating in PC0 must not affect PC1"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        pc1 = ch.pseudo_channels[1]

        pc0.activate_row(100)

        assert pc0.is_row_open(100)
        assert not pc1.is_row_open(100)

    def test_both_pseudo_channels_can_be_active(self):
        """Both pseudo-channels can be active simultaneously"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        pc1 = ch.pseudo_channels[1]

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

        assert pc0_banks is not pc1_banks
        assert len(pc0_banks) == 16
        assert len(pc1_banks) == 16

    def test_pseudo_channels_have_independent_bank_groups(self):
        """Each pseudo-channel has independent bank groups"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0_bgs = ch.pseudo_channels[0].bank_groups
        pc1_bgs = ch.pseudo_channels[1].bank_groups

        assert pc0_bgs is not pc1_bgs
        assert len(pc0_bgs) == 8
        assert len(pc1_bgs) == 8


# =============================================================================
# Test Bank Group Read/Write Queries
# =============================================================================
class TestBankGroupReadWriteQueries:
    """Test read/write capability queries per bank group"""

    def test_can_read_in_bank_group(self):
        """Must query read capability per bank group"""
        from model.dram.hbm4_bank_state_machine import HBM4BankTiming
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # Activate in BG2
        pc0.activate_row_in_bank_group(2, 0, 100)

        # Advance time past tRCD (12 cycles for bank timing, need 13 ticks)
        bank_timing = HBM4BankTiming()
        for _ in range(bank_timing.tRCD + 1):
            ch.tick()

        assert pc0.can_read_in_bank_group(2)

    def test_can_write_in_bank_group(self):
        """Must query write capability per bank group"""
        from model.dram.hbm4_bank_state_machine import HBM4BankTiming
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # Activate in BG3
        pc0.activate_row_in_bank_group(3, 1, 100)

        # Advance time past tRCD (12 cycles for bank timing, need 13 ticks)
        bank_timing = HBM4BankTiming()
        for _ in range(bank_timing.tRCD + 1):
            ch.tick()

        assert pc0.can_write_in_bank_group(3)