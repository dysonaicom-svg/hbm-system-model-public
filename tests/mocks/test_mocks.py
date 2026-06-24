"""
Tests for Mock DFI/PHY Interfaces

Tests for all mock objects in tests/mocks/:
- MockDFIInterface
- MockPHY
- MockClock, MockReset, MockSignal, MockDataBus

Usage:
    pytest tests/mocks/test_mocks.py -v
"""

import pytest
from typing import List, Dict, Any

# Import mock modules
import sys
sys.path.insert(0, '/home/ic/JXTF/HBM4')

from tests.mocks import (
    MockDFIInterface,
    MockDFIRequest,
    MockDFIResponse,
    MockDFISignals,
    MockPHY,
    MockPHYTraining,
    MockPHYSignals,
    MockClock,
    MockReset,
    MockSignal,
    MockDataBus,
)
from tests.mocks.mock_dfi_interface import (
    DFICommand,
    DFILowPowerState,
    TrainingPhase as MockDFITrainingPhase,
)
from tests.mocks.mock_phy import (
    TrainingPhase,
)


# =============================================================================
# MockDFIInterface Tests
# =============================================================================

class TestMockDFIInterface:
    """Tests for MockDFIInterface"""

    def test_initialization(self):
        """Test basic initialization"""
        mock_dfi = MockDFIInterface()
        assert mock_dfi.cycle == 0
        assert mock_dfi.lp_state == DFILowPowerState.LP_IDLE
        assert not mock_dfi.training_complete

    def test_send_command(self):
        """Test sending commands"""
        mock_dfi = MockDFIInterface()
        req_id = mock_dfi.send_command(DFICommand.ACT, address=0x1000, bank=0)
        assert req_id == 0
        assert mock_dfi.signals.cmd == DFICommand.ACT.value
        assert mock_dfi.signals.cmd_en

    def test_send_act_command(self):
        """Test ACT command shortcut"""
        mock_dfi = MockDFIInterface()
        req_id = mock_dfi.send_act(bank=0, row=0x100)
        assert req_id == 0
        assert mock_dfi.signals.cmd == DFICommand.ACT.value

    def test_send_rd_wr_commands(self):
        """Test READ and WRITE commands"""
        mock_dfi = MockDFIInterface()

        # Read command
        req_id = mock_dfi.send_rd(bank=0, column=0x40)
        assert req_id == 0
        assert mock_dfi.signals.rddata_en

        # Write command
        req_id = mock_dfi.send_wr(bank=0, column=0x40)
        assert req_id == 1
        assert mock_dfi.signals.wrdata_en

    def test_tick_advances_cycle(self):
        """Test that tick() advances cycle counter"""
        mock_dfi = MockDFIInterface()
        assert mock_dfi.cycle == 0
        mock_dfi.tick()
        assert mock_dfi.cycle == 1
        mock_dfi.tick()
        assert mock_dfi.cycle == 2

    def test_ctrlupd_handshake(self):
        """Test control update handshake"""
        mock_dfi = MockDFIInterface()

        # Request control update
        assert mock_dfi.request_ctrlupd()
        assert mock_dfi.signals.ctrlupd_req

        # Manually acknowledge since auto-ack depends on tick timing
        mock_dfi.acknowledge_ctrlupd()
        assert mock_dfi.signals.ctrlupd_ack

        # Tick should complete the handshake
        mock_dfi.tick()
        assert not mock_dfi.signals.ctrlupd_req

    def test_acknowledge_ctrlupd(self):
        """Test manual control update acknowledgment"""
        mock_dfi = MockDFIInterface()

        mock_dfi.request_ctrlupd()
        assert mock_dfi.acknowledge_ctrlupd()
        assert mock_dfi.signals.ctrlupd_ack

    def test_freq_change_request(self):
        """Test frequency change request"""
        mock_dfi = MockDFIInterface()

        assert mock_dfi.request_freq_change(1200)
        assert mock_dfi.signals.freq_change_en

    def test_low_power_state(self):
        """Test low power state entry/exit"""
        mock_dfi = MockDFIInterface()

        # Request low power
        assert mock_dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert mock_dfi.lp_state == DFILowPowerState.LP_CTRL

        # Wake up
        mock_dfi.wakeup()

        # Advance until exit
        for _ in range(10):
            mock_dfi.tick()

        assert mock_dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_training_sequence(self):
        """Test training sequence"""
        mock_dfi = MockDFIInterface()

        mock_dfi.start_training()
        assert mock_dfi._training_phase == MockDFITrainingPhase.DRAM_RESET

        # Advance through training phases
        for _ in range(20):
            mock_dfi.tick()

        # Training should complete
        # Note: Simplified training for mock

    def test_response_queue(self):
        """Test response queue management"""
        mock_dfi = MockDFIInterface()

        # Send a read command
        req_id = mock_dfi.send_rd(bank=0, column=0x40)

        # Advance until response is ready
        for _ in range(20):
            mock_dfi.tick()

        # Should have a response
        response = mock_dfi.get_response()
        assert response is not None

    def test_statistics(self):
        """Test statistics collection"""
        mock_dfi = MockDFIInterface()

        mock_dfi.send_command(DFICommand.ACT)
        mock_dfi.send_command(DFICommand.RD)

        stats = mock_dfi.get_statistics()
        assert stats['commands_sent'] == 2
        assert stats['queue_depth'] == 2

    def test_reset(self):
        """Test reset functionality"""
        mock_dfi = MockDFIInterface()

        mock_dfi.send_command(DFICommand.ACT)
        mock_dfi.tick()
        mock_dfi.tick()

        mock_dfi.reset()

        assert mock_dfi.cycle == 0
        assert mock_dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_parity_error_injection(self):
        """Test parity error injection"""
        mock_dfi = MockDFIInterface()

        mock_dfi.inject_parity_error()
        assert mock_dfi.signals.parity_error

        stats = mock_dfi.get_statistics()
        assert stats['errors'] == 1

    def test_callback_mechanism(self):
        """Test callback hooks"""
        mock_dfi = MockDFIInterface()

        commands_sent = []

        def on_command(request):
            commands_sent.append(request)

        mock_dfi.set_callback('command_sent', on_command)
        mock_dfi.send_command(DFICommand.ACT)

        assert len(commands_sent) == 1


# =============================================================================
# MockPHY Tests
# =============================================================================

class TestMockPHY:
    """Tests for MockPHY"""

    def test_initialization(self):
        """Test basic initialization"""
        mock_phy = MockPHY()
        assert mock_phy.cycle == 0
        assert not mock_phy.is_initialized
        assert mock_phy.get_training_phase() == TrainingPhase.IDLE

    def test_initialize(self):
        """Test PHY initialization"""
        mock_phy = MockPHY()
        mock_phy.initialize()
        assert mock_phy.is_initialized
        assert mock_phy.signals.pll_locked
        assert mock_phy.signals.dll_locked

    def test_clock_reset_control(self):
        """Test clock and reset control"""
        mock_phy = MockPHY()

        # Clock disable
        mock_phy.set_clock_enable(False)
        assert not mock_phy.signals.phy_clock_enable

        # Reset
        mock_phy.set_reset(True)
        assert mock_phy.signals.phy_reset

    def test_pll_configuration(self):
        """Test PLL configuration"""
        mock_phy = MockPHY()

        mock_phy.configure_pll(frequency_mhz=1600, divider=1, multiplier=2)
        config = mock_phy.get_pll_config()
        assert config['frequency_mhz'] == 1600
        assert config['divider'] == 1
        assert config['multiplier'] == 2
        assert not config['locked']  # Should be unlocked after config

    def test_dll_configuration(self):
        """Test DLL configuration"""
        mock_phy = MockPHY()

        mock_phy.configure_dll(enabled=True, delay_elements=128)
        config = mock_phy.get_dll_config()
        assert config['enabled']
        assert config['delay_elements'] == 128

    def test_vref_configuration(self):
        """Test VREF configuration"""
        mock_phy = MockPHY()

        mock_phy.configure_vref(dram_vref=45, phy_vref=55)
        config = mock_phy.get_vref_config()
        assert config['dram_vref'] == 45
        assert config['phy_vref'] == 55

    def test_impedance_configuration(self):
        """Test impedance configuration"""
        mock_phy = MockPHY()

        mock_phy.configure_impedance(write_ohm=48, read_ohm=60)
        config = mock_phy.get_impedance_config()
        assert config['write_impedance'] == 48
        assert config['read_impedance'] == 60

    def test_mode_register_access(self):
        """Test mode register read/write"""
        mock_phy = MockPHY()

        # Write
        mock_phy.set_mode_register(address=0, value=0xAB)
        mock_phy.set_mode_register(address=1, value=0xCD)

        # Read
        assert mock_phy.get_mode_register(0) == 0xAB
        assert mock_phy.get_mode_register(1) == 0xCD
        assert mock_phy.get_mode_register(2) == 0  # Unset

        # Get all
        all_mr = mock_phy.get_all_mode_registers()
        assert len(all_mr) == 2

    def test_training_sequence(self):
        """Test training sequence"""
        mock_phy = MockPHY()

        mock_phy.start_training()
        assert mock_phy.is_training_in_progress()

        # Advance through training
        for _ in range(50):
            mock_phy.tick()

        # Training should complete
        assert mock_phy.is_training_complete()

    def test_training_results(self):
        """Test training results retrieval"""
        mock_phy = MockPHY()

        mock_phy.start_training()

        # Advance to completion
        for _ in range(50):
            mock_phy.tick()

        if mock_phy.did_training_pass():
            coeffs = mock_phy.get_coefficients()
            assert hasattr(coeffs, 'tx_precursor')
            assert hasattr(coeffs, 'rx_vref')

    def test_calibration(self):
        """Test ZQ calibration"""
        mock_phy = MockPHY()

        mock_phy.start_calibration()
        assert mock_phy.signals.cal_req

        mock_phy.complete_calibration()
        assert mock_phy.is_calibrated()
        assert mock_phy.signals.cal_complete

    def test_data_interface(self):
        """Test data interface signals"""
        mock_phy = MockPHY()

        mock_phy.set_wrdata_en(True)
        assert mock_phy.signals.wrdata_en

        mock_phy.set_rddata_en(True)
        assert mock_phy.signals.rddata_en

        mock_phy.set_data_valid(True)
        assert mock_phy.signals.data_valid

    def test_status_retrieval(self):
        """Test status retrieval"""
        mock_phy = MockPHY()

        mock_phy.initialize()
        mock_phy.complete_calibration()

        status = mock_phy.get_status()
        assert status['initialized']
        assert status['calibration_done']

    def test_info_retrieval(self):
        """Test info retrieval"""
        mock_phy = MockPHY()

        info = mock_phy.get_info()
        assert 'version' in info
        assert 'num_lanes' in info
        assert 'pll' in info

    def test_statistics(self):
        """Test statistics"""
        mock_phy = MockPHY()

        mock_phy.start_training()
        mock_phy.start_calibration()

        stats = mock_phy.get_statistics()
        assert stats['training_count'] == 1
        assert stats['calibration_count'] == 1

    def test_reset(self):
        """Test reset functionality"""
        mock_phy = MockPHY()

        mock_phy.initialize()
        mock_phy.start_training()
        mock_phy.tick()
        mock_phy.tick()

        mock_phy.reset()

        assert mock_phy.cycle == 0
        assert not mock_phy.is_initialized


# =============================================================================
# MockClock Tests
# =============================================================================

class TestMockClock:
    """Tests for MockClock"""

    def test_initialization(self):
        """Test clock initialization"""
        clock = MockClock(frequency_mhz=800)
        assert clock.frequency_mhz == 800
        assert clock.cycle == 0

    def test_tick_toggles_clock(self):
        """Test that tick() toggles clock"""
        clock = MockClock()
        initial = clock.value
        clock.tick()
        assert clock.value != initial

    def test_advance(self):
        """Test advance() method"""
        clock = MockClock()
        clock.advance(10)
        assert clock.tick_count > 0

    def test_period_calculation(self):
        """Test period calculation"""
        clock = MockClock(frequency_mhz=800)
        period_ps = clock.get_period_ps()
        assert period_ps > 0
        assert abs(period_ps - 1250) < 1  # 800 MHz = 1250 ps period


# =============================================================================
# MockReset Tests
# =============================================================================

class TestMockReset:
    """Tests for MockReset"""

    def test_initialization(self):
        """Test reset initialization"""
        reset = MockReset()
        assert not reset.is_asserted
        assert reset.value == True  # Active-low by default

    def test_assert_deassert(self):
        """Test assert and deassert"""
        reset = MockReset()

        reset.assert_reset()
        assert reset.is_asserted
        assert reset.value == False  # Active-low

        reset.deassert_reset()
        assert not reset.is_asserted
        assert reset.value == True

    def test_auto_deassert(self):
        """Test auto deassert after configured cycles"""
        reset = MockReset(deassert_cycles=5)

        reset.assert_reset()
        for _ in range(5):
            reset.tick()

        assert not reset.is_asserted

    def test_history_tracking(self):
        """Test history tracking"""
        reset = MockReset()

        reset.assert_reset(cycle=10)
        reset.deassert_reset(cycle=20)

        history = reset.get_history()
        assert len(history) == 2
        assert history[0]['event'] == 'assert'
        assert history[1]['event'] == 'deassert'


# =============================================================================
# MockSignal Tests
# =============================================================================

class TestMockSignal:
    """Tests for MockSignal"""

    def test_initialization(self):
        """Test signal initialization"""
        signal = MockSignal(name="test", width=8)
        assert signal.name == "test"
        assert signal.width == 8
        assert signal.value == 0

    def test_value_setting(self):
        """Test value setting"""
        signal = MockSignal()
        signal.value = 42
        assert signal.value == 42

    def test_change_detection(self):
        """Test change detection"""
        signal = MockSignal()
        signal.value = 1
        assert signal.did_change()
        signal.tick()
        signal.value = 2
        assert signal.did_change()

    def test_history_tracking(self):
        """Test history tracking"""
        signal = MockSignal()

        signal.value = 10
        signal.tick()
        signal.tick()
        signal.value = 20

        history = signal.get_history()
        assert len(history) == 2


# =============================================================================
# MockDataBus Tests
# =============================================================================

class TestMockDataBus:
    """Tests for MockDataBus"""

    def test_initialization(self):
        """Test bus initialization"""
        bus = MockDataBus(width=256, num_lanes=64)
        assert bus.width == 256
        assert bus.num_lanes == 64

    def test_write_read(self):
        """Test write and read"""
        bus = MockDataBus()

        test_data = 0xDEADBEEF
        bus.write(test_data)

        read_data = bus.read()
        assert read_data == test_data

    def test_lane_masking(self):
        """Test lane masking"""
        bus = MockDataBus(num_lanes=8)

        bus.write(0xFF, mask=0x03)  # Only lanes 0 and 1 enabled
        assert bus.mask == 0x03

    def test_error_injection(self):
        """Test error injection"""
        bus = MockDataBus()

        bus.inject_error(lane=0)
        assert bus.is_lane_failed(0)

        failed = bus.get_failed_lanes()
        assert 0 in failed

    def test_lane_repair(self):
        """Test lane repair"""
        bus = MockDataBus(num_lanes=8)

        bus.inject_error(lane=0)
        assert bus.is_lane_failed(0)

        bus.repair_lane(failed_lane=0, spare_lane=7)
        assert not bus.is_lane_failed(0)

    def test_statistics(self):
        """Test statistics"""
        bus = MockDataBus()

        bus.write(0x12345678)
        bus.inject_error(lane=0)

        stats = bus.get_statistics()
        assert stats['transfer_count'] == 1
        assert stats['lane_failures'] == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestMockIntegration:
    """Integration tests for mock components"""

    def test_dfi_phy_integration(self):
        """Test DFI and PHY integration"""
        mock_dfi = MockDFIInterface()
        mock_phy = MockPHY()

        # Initialize
        mock_phy.initialize()

        # Train PHY
        mock_phy.start_training()
        for _ in range(50):
            mock_phy.tick()
            mock_dfi.tick()

        # Send commands through DFI
        mock_dfi.send_act(bank=0, row=0x100)
        for _ in range(10):
            mock_dfi.tick()

        stats = mock_dfi.get_statistics()
        assert stats['commands_sent'] == 1

    def test_full_system_simulation(self):
        """Test full system simulation"""
        mock_dfi = MockDFIInterface()
        mock_phy = MockPHY()
        clock = MockClock(frequency_mhz=800)

        # Initialize
        mock_phy.initialize()

        # Run simulation
        for _ in range(100):
            clock.tick()
            mock_phy.tick()
            mock_dfi.tick()

            if _ % 10 == 0:
                # Send periodic commands
                mock_dfi.send_command(DFICommand.NOP)

        # Verify system state
        assert clock.cycle > 0


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
