"""
HBM4 Independent Channel Timing Tests

Tests for per-channel independent timing model.
"""

import pytest
from model.dram.channel_timing import (
    IndependentChannelTiming,
    HBM4TimingManager,
    TimingParameters,
    ChannelClockDomain,
    BankState,
    TimingConstraint,
)


class TestIndependentChannelTiming:
    """Test Independent Channel Timing Model"""

    def test_initialization(self):
        """Test channel timing initialization"""
        timing = IndependentChannelTiming(channel_id=0)

        assert timing.channel_id == 0
        assert timing.local_cycle == 0
        assert len(timing.bank_states) == 16

    def test_tick_advancement(self):
        """Test local cycle advancement"""
        timing = IndependentChannelTiming(channel_id=0)

        timing.tick()
        assert timing.local_cycle == 1

        timing.tick()
        timing.tick()
        assert timing.local_cycle == 3

    def test_activate_timing(self):
        """Test ACTIVATE command timing"""
        timing = IndependentChannelTiming(channel_id=0)

        # First ACT should succeed
        success, msg, data = timing.execute_with_independent_timing('ACT', bank=0, row=0x1000)
        assert success
        assert timing.bank_states[0].state == "ACTIVE"
        assert timing.bank_states[0].row_id == 0x1000

    def test_tRC_violation(self):
        """Test tRC timing constraint"""
        timing = IndependentChannelTiming(channel_id=0)

        # First ACT
        timing.execute_with_independent_timing('ACT', bank=0, row=0x1000)
        timing.tick()

        # Immediate second ACT on same bank should fail (tRC not met)
        ok, msg = timing.check_timing_constraints('ACT', bank=0, row=0x2000)
        assert not ok
        assert "tRC" in msg

    def test_tRCD_constraint(self):
        """Test tRCD timing constraint"""
        timing = IndependentChannelTiming(channel_id=0)

        # ACT
        timing.execute_with_independent_timing('ACT', bank=0, row=0x1000)

        # Immediate READ should fail (tRCD not met)
        ok, msg = timing.check_timing_constraints('RD', bank=0)
        assert not ok
        assert "tRCD" in msg

    def test_tCCD_constraint(self):
        """Test tCCD (column to column) constraint"""
        timing = IndependentChannelTiming(channel_id=0)

        # Setup: open bank and first read
        success, msg, data = timing.execute_with_independent_timing('ACT', bank=0, row=0x1000)
        assert success

        for _ in range(10):  # Wait for tRCD
            timing.tick()

        success, msg, data = timing.execute_with_independent_timing('RD', bank=0)
        assert success

        # Wait at least tCCD cycles
        for _ in range(5):  # tCCD = 2, wait 5
            timing.tick()

        # Second READ should succeed (tCCD=2, waited 5 cycles)
        ok, msg = timing.check_timing_constraints('RD', bank=0)
        assert ok

    def test_tRAS_constraint(self):
        """Test tRAS timing constraint"""
        timing = IndependentChannelTiming(channel_id=0)

        # ACT
        timing.execute_with_independent_timing('ACT', bank=0, row=0x1000)

        # Immediate PRE should fail (tRAS not met)
        ok, msg = timing.check_timing_constraints('PRE', bank=0)
        assert not ok
        assert "tRAS" in msg

    def test_bank_state_tracking(self):
        """Test per-bank state tracking"""
        timing = IndependentChannelTiming(channel_id=0)

        # ACT bank 0
        timing.execute_with_independent_timing('ACT', bank=0, row=0x1000)
        assert timing.bank_states[0].is_open

        # PRE bank 0
        for _ in range(25):  # Wait for tRAS
            timing.tick()
        timing.execute_with_independent_timing('PRE', bank=0)
        assert not timing.bank_states[0].is_open

        # Bank 1 should still be closed
        assert not timing.bank_states[1].is_open

    def test_timing_parameters_update(self):
        """Test timing parameter updates"""
        timing = IndependentChannelTiming(channel_id=0)

        # Update timing parameters
        params = TimingParameters(nCL=10, nCWL=5)
        timing.set_timing_params(params)

        assert timing.params.nCL == 10
        assert timing.params.nCWL == 5

    def test_clock_domain_frequency(self):
        """Test clock domain frequency"""
        timing = IndependentChannelTiming(channel_id=0)

        # Default timing params: tCK_ps = 125.0
        # frequency_mhz = 1000/125 = 8.0 MHz (at 8 GT/s data rate)
        # Note: This is MHz, so 8 GT/s = 8.0 MHz
        assert abs(timing.clock_domain.base_frequency_mhz - 8.0) < 0.1
        # tCK = 1000/frequency = 1000/8 = 125ps
        assert abs(timing.clock_domain.tCK_ps - 125.0) < 0.1

    def test_timing_status(self):
        """Test timing status reporting"""
        timing = IndependentChannelTiming(channel_id=0)

        # Execute some commands
        timing.execute_with_independent_timing('ACT', bank=0, row=0x1000)
        for _ in range(10):
            timing.tick()

        status = timing.get_timing_status()

        assert status['channel_id'] == 0
        assert status['open_banks'] == 1
        assert status['commands_executed'] == 1


class TestHBM4TimingManager:
    """Test HBM4 Timing Manager for all channels"""

    def test_initialization(self):
        """Test manager initialization"""
        manager = HBM4TimingManager(num_channels=32)

        assert manager.num_channels == 32
        assert len(manager.channels) == 32

    def test_tick_all_channels(self):
        """Test advancing all channel cycles"""
        manager = HBM4TimingManager(num_channels=32)

        manager.tick()

        for ch in manager.channels:
            assert ch.local_cycle == 1

    def test_get_channel_timing(self):
        """Test getting specific channel timing"""
        manager = HBM4TimingManager(num_channels=32)

        timing = manager.get_channel_timing(15)
        assert timing is not None
        assert timing.channel_id == 15

    def test_set_channel_timing_params(self):
        """Test setting per-channel timing parameters"""
        manager = HBM4TimingManager(num_channels=32)

        params = TimingParameters(nCL=12)
        manager.set_channel_timing_params(15, params)

        assert manager.channels[15].params.nCL == 12

    def test_independent_channel_operation(self):
        """Test that channels operate independently"""
        manager = HBM4TimingManager(num_channels=32)

        # Execute ACT on channel 0
        manager.channels[0].execute_with_independent_timing('ACT', bank=0, row=0x1000)

        # Channel 0 has open bank
        assert manager.channels[0].bank_states[0].is_open

        # Channel 1 should not be affected
        assert not manager.channels[1].bank_states[0].is_open

    def test_all_timing_status(self):
        """Test getting all channel timing status"""
        manager = HBM4TimingManager(num_channels=32)

        status_list = manager.get_all_timing_status()

        assert len(status_list) == 32
        assert all(s['channel_id'] in range(32) for s in status_list)


class TestBankState:
    """Test Bank State tracking"""

    def test_bank_state_creation(self):
        """Test bank state creation"""
        bank = BankState(bank_id=5)

        assert bank.bank_id == 5
        assert bank.state == "IDLE"
        assert bank.row_id is None
        assert not bank.is_open

    def test_bank_open_state(self):
        """Test bank open state"""
        bank = BankState(bank_id=0)
        bank.state = "ACTIVE"
        bank.row_id = 0x1234

        assert bank.is_open


class TestTimingParameters:
    """Test Timing Parameters"""

    def test_default_parameters(self):
        """Test default timing parameters"""
        params = TimingParameters()

        # HBM4 defaults @ 8 GT/s
        assert params.tCK_ps == 125.0
        assert params.nCL == 8
        assert params.nCWL == 3
        assert params.nRCDRD == 8
        assert params.nRAS == 20

    def test_frequency_calculation(self):
        """Test frequency calculation from period"""
        params = TimingParameters(tCK_ps=125.0)

        # 1000/125 = 8.0 MHz (at 8 GT/s data rate)
        assert abs(params.frequency_mhz - 8.0) < 0.1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])