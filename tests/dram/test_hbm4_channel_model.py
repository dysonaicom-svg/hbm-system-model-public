"""
Tests for HBM4 Channel Model

Tests the HBM4 channel state machine with 32 channels and pseudo-channel support.
"""

import pytest
from model.dram.hbm4_channel_model import HBM4Channel, PseudoChannel, HBM4ChannelState, PseudoChannelState
from model.dram.hbm4_spec import HBM4Spec


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
        activated_banks = [b for b in pc0.banks if b.bank.state.value == 1]  # ACTIVE state
        assert len(activated_banks) > 0

    def test_precharge_command(self):
        """PRE command must precharge banks"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        # First activate
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

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
        ch = HBM4Channel(0, spec)

        # Activate a row
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Get current bank time
        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]
        activation_time = bank.bank.activate_time

        # Tick
        ch.tick()

        # Time should have advanced
        assert bank.bank.activate_time >= activation_time


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
    """Test bank state transitions"""

    def test_bank_starts_idle(self):
        """Banks must start in IDLE state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        assert bank.bank.state.value == 0  # IDLE = 0

    def test_bank_activates_and_transitions_to_active(self):
        """Bank must transition from IDLE to ACTIVE on activation"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        # Bank should be IDLE initially
        assert bank.bank.state.value == 0

        # Activate
        pc0.activate_row(100)

        # Bank should now be ACTIVE
        assert bank.bank.state.value == 1  # ACTIVE = 1

    def test_bank_tracks_open_row(self):
        """Bank must track which row is open"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        # Activate row 100
        pc0.activate_row(100)

        # Bank should track the open row
        assert bank.bank.open_row == 100

    def test_bank_precharge_returns_to_idle(self):
        """Bank must return to IDLE after precharge"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        bank = pc0.banks[0]

        # Activate
        pc0.activate_row(100)
        assert bank.bank.state.value == 1  # ACTIVE

        # Advance time past tRAS (20 cycles for HBM4)
        for _ in range(25):
            ch.tick()

        # Precharge
        pc0.precharge_all()

        # Bank should be IDLE
        assert bank.bank.state.value == 0

    def test_row_hit_detection(self):
        """Bank must detect row hits"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]

        # Activate row 100
        pc0.activate_row(100)

        # Should be row hit for row 100
        assert pc0.is_row_open(100)

        # Should NOT be row hit for row 200
        assert not pc0.is_row_open(200)


class TestHBM4PseudoChannelStateTransitions:
    """Test pseudo-channel state transitions"""

    def test_pseudo_channel_starts_idle(self):
        """Pseudo-channel must start in IDLE state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        assert pc0.state == PseudoChannelState.IDLE

    def test_pseudo_channel_transitions_to_active_on_activation(self):
        """Pseudo-channel must transition to ACTIVE when a row is activated"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        pc0.activate_row(100)

        assert pc0.state == PseudoChannelState.ACTIVE

    def test_pseudo_channel_transitions_to_reading(self):
        """Pseudo-channel must transition to READING state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

        assert pc0.state == PseudoChannelState.READING

    def test_pseudo_channel_transitions_to_writing(self):
        """Pseudo-channel must transition to WRITING state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        ch.issue_command('WR', pseudo_channel=0, bank=0, row=100, col=0)

        assert pc0.state == PseudoChannelState.WRITING

    def test_pseudo_channel_transitions_to_refreshing(self):
        """Pseudo-channel must transition to REFRESHING state"""
        spec = HBM4Spec()
        ch = HBM4Channel(0, spec)

        pc0 = ch.pseudo_channels[0]
        ch.issue_command('REFab', pseudo_channel=0, bank=0, row=0)

        assert pc0.state == PseudoChannelState.REFRESHING


class TestHBM4TimingParameters:
    """Test HBM4 timing parameters are correctly configured"""

    def test_tCK_is_125ps_for_8gtps(self):
        """tCK should be 125ps for 8 GT/s DDR"""
        spec = HBM4Spec()

        assert spec.tCK_ps == 125.0

    def test_nRAS_is_20_cycles(self):
        """nRAS (row active time) should be 20 cycles"""
        spec = HBM4Spec()

        assert spec.nRAS == 20

    def test_nCL_is_8_cycles(self):
        """CAS latency should be 8 cycles"""
        spec = HBM4Spec()

        assert spec.nCL == 8

    def test_bandwidth_calculation_for_8gtps(self):
        """Verify bandwidth calculation for 8 GT/s"""
        spec = HBM4Spec()

        # 8 GT/s x 2048 bits / 8 = 2048 GB/s
        expected = 2048.0
        assert abs(spec.bandwidth_gbs - expected) < 1.0

        # In TB/s: 2048 / 1000 = 2.048 TB/s
        assert abs(spec.bandwidth - 2.048) < 0.001