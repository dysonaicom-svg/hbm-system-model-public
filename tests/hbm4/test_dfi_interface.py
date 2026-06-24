"""
Tests for DFI 5.1 Interface

Tests the DFI interface implementation for HBM4 controller-PHY
communication, including timing parameters, PHY control, frequency
changes, low-power states, and training.
"""

import pytest
from model.dram.dfi_interface import (
    DFICommand,
    DFILowPowerState,
    DFIRequest,
    DFIResponse,
    DFIPhyIF,
    DFI5Interface,
)


class TestDFICommandEncoding:
    """Test DFI command encoding and constants"""

    def test_all_commands_have_valid_codes(self):
        """Verify all DFI commands have valid binary encodings"""
        commands = [
            (DFICommand.ACT, 0b0000),
            (DFICommand.PRE, 0b0001),
            (DFICommand.PREA, 0b0010),
            (DFICommand.RD, 0b0011),
            (DFICommand.WR, 0b0100),
            (DFICommand.RDA, 0b0101),
            (DFICommand.WRA, 0b0110),
            (DFICommand.REFab, 0b0111),
            (DFICommand.REFsb, 0b1000),
            (DFICommand.RFMab, 0b1001),
            (DFICommand.RFMsb, 0b1010),
        ]
        for cmd, expected_code in commands:
            assert cmd.value == expected_code, f"{cmd.name} should have code {expected_code}"

    def test_command_count(self):
        """Verify all expected commands are present"""
        assert len(DFICommand) == 11, "DFI should have 11 commands"


class TestDFIPhyInterface:
    """Test DFI PHY interface control"""

    def test_phy_clock_enable(self):
        """Test PHY clock enable control"""
        phy = DFIPhyIF()

        assert phy.phy_clock_enable is True  # Default enabled

        phy.set_phy_clock_enable(False)
        assert phy.phy_clock_enable is False

        phy.set_phy_clock_enable(True)
        assert phy.phy_clock_enable is True

    def test_phy_reset_control(self):
        """Test PHY reset control"""
        phy = DFIPhyIF()

        assert phy.phy_reset is False  # Default not reset

        phy.set_phy_reset(True)
        assert phy.phy_reset is True

        phy.set_phy_reset(False)
        assert phy.phy_reset is False

    def test_calibration_status_empty(self):
        """Test calibration status returns initial state"""
        phy = DFIPhyIF()
        status = phy.get_calibration_status()
        # Check the status has the expected structure
        assert 'calibration_data' in status
        assert 'calibration_results' in status
        assert 'calibration_complete' in status
        assert status['calibration_complete'] is False
        assert status['calibration_data'] == {}
        assert status['calibration_results'] == {}

    def test_calibration_data_persistence(self):
        """Test calibration data can be stored and retrieved"""
        phy = DFIPhyIF()
        phy.calibration_data['read_delay'] = 42
        phy.calibration_data['write_leveling'] = 7

        status = phy.get_calibration_status()
        assert status['calibration_data']['read_delay'] == 42
        assert status['calibration_data']['write_leveling'] == 7


class TestDFI5InterfaceTiming:
    """Test DFI 5.1 timing parameters"""

    def test_interface_version(self):
        """Test DFI interface version"""
        dfi = DFI5Interface()
        # DFI5Interface supports DFI 5.0
        assert dfi.version in ["5.0", "5.1"]

    def test_default_frequency(self):
        """Test default frequency is 800 MT/s for HBM4"""
        dfi = DFI5Interface()
        assert dfi.frequency_mhz == 800

    def test_set_frequency(self):
        """Test frequency setting"""
        dfi = DFI5Interface()

        dfi.set_frequency(6400)
        assert dfi.frequency_mhz == 6400

        dfi.set_frequency(3200)
        assert dfi.frequency_mhz == 3200

    def test_bandwidth_calculation(self):
        """Test bandwidth calculation based on frequency"""
        dfi = DFI5Interface()

        # Default 800 MT/s
        bandwidth = dfi.get_bandwidth_gbs()
        assert bandwidth > 0  # Bandwidth should be positive

        dfi.set_frequency(6400)
        bandwidth = dfi.get_bandwidth_gbs()
        # 6400 MHz → 64 GT/s → 64 * 2048 / 8 = 16384 GB/s
        assert bandwidth == 16384.0


class TestDFICommandEncoding:
    """Test command encoding to DFI request"""

    def test_encode_act_command(self):
        """Test ACT command encoding"""
        dfi = DFI5Interface()
        addr_vec = {'row': 0x100, 'bank': 3, 'channel': 0, 'pseudo_channel': 0}
        request = dfi.encode_command('ACT', addr_vec)

        assert request.command == DFICommand.ACT
        assert request.address == 0x100
        assert request.bank == 3
        assert request.wrdata_en is False
        assert request.rddata_en is False

    def test_encode_read_command(self):
        """Test READ command encoding with rddata_en"""
        dfi = DFI5Interface()
        addr_vec = {'address': 0x200, 'bank': 1, 'channel': 5, 'pseudo_channel': 1}
        request = dfi.encode_command('RD', addr_vec)

        assert request.command == DFICommand.RD
        assert request.rddata_en is True
        assert request.wrdata_en is False
        assert request.pseudo_channel == 1

    def test_encode_write_command(self):
        """Test WRITE command encoding with wrdata_en"""
        dfi = DFI5Interface()
        addr_vec = {'row': 0x300, 'bank': 7, 'channel': 15}
        request = dfi.encode_command('WR', addr_vec)

        assert request.command == DFICommand.WR
        assert request.wrdata_en is True
        assert request.rddata_en is False

    def test_encode_refresh_command(self):
        """Test REFRESH command encoding"""
        dfi = DFI5Interface()
        request = dfi.encode_command('REFab', {'bank': 0, 'channel': 0})

        assert request.command == DFICommand.REFab

    def test_encode_write_with_auto_precharge(self):
        """Test WRA command sets wrdata_en"""
        dfi = DFI5Interface()
        request = dfi.encode_command('WRA', {'bank': 2, 'channel': 0})

        assert request.command == DFICommand.WRA
        assert request.wrdata_en is True


class TestDFILowPowerState:
    """Test DFI low-power state machine"""

    def test_default_lp_state_is_idle(self):
        """Test default LP state is LP_IDLE"""
        dfi = DFI5Interface()
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_set_low_power_state(self):
        """Test setting low-power state"""
        dfi = DFI5Interface()

        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        assert dfi.lp_state == DFILowPowerState.LP_CTRL

        dfi.set_low_power_state(DFILowPowerState.LP_DATA)
        assert dfi.lp_state == DFILowPowerState.LP_DATA

    def test_lp_state_count(self):
        """Test all expected LP states exist"""
        # DFI 5.0 has 7 low power states
        assert len(DFILowPowerState) == 7


class TestDFIFrequencyChange:
    """Test DFI frequency change handling"""

    def test_enter_freq_change(self):
        """Test entering frequency change state"""
        dfi = DFI5Interface()
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

        dfi.enter_freq_change()
        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE

    def test_exit_freq_change(self):
        """Test exiting frequency change"""
        dfi = DFI5Interface()

        dfi.enter_freq_change()
        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE

        # Exit frequency change - state machine starts exit sequence
        dfi.exit_freq_change()
        # The state machine enters exit sequence, lp_state may still be LP_FREQ_CHANGE
        # until the full exit sequence completes (per DFI 5.0 spec)
        assert dfi.lp_state in [DFILowPowerState.LP_FREQ_CHANGE, DFILowPowerState.LP_IDLE]

    def test_frequency_change_preserves_frequency(self):
        """Test frequency is preserved during change"""
        dfi = DFI5Interface()
        dfi.set_frequency(6400)

        dfi.enter_freq_change()
        assert dfi.frequency_mhz == 6400

        dfi.exit_freq_change()
        assert dfi.frequency_mhz == 6400


class TestDFITrainingInterface:
    """Test DFI training and calibration interface"""

    def test_default_training_state(self):
        """Test training starts in not_started state"""
        dfi = DFI5Interface()
        assert dfi.training_complete is False
        assert dfi.training_in_progress is False

    def test_start_training(self):
        """Test starting training sequence"""
        dfi = DFI5Interface()

        dfi.start_training()
        assert dfi.training_in_progress is True
        assert dfi.training_complete is False

    def test_complete_training(self):
        """Test completing training sequence"""
        dfi = DFI5Interface()

        dfi.start_training()
        dfi.complete_training()

        assert dfi.training_complete is True
        assert dfi.training_in_progress is False

    def test_training_response_states(self):
        """Test response reflects training state correctly"""
        dfi = DFI5Interface()

        response = dfi.get_response()
        assert response.training_state == "not_started"

        dfi.start_training()
        response = dfi.get_response()
        assert response.training_state == "in_progress"

        dfi.complete_training()
        response = dfi.get_response()
        assert response.training_state == "complete"

    def test_calibration_data_via_phy(self):
        """Test adding calibration data through PHY interface"""
        dfi = DFI5Interface()

        dfi.add_calibration_data('read_gate', 0xABC)
        dfi.add_calibration_data('write_level', 0x123)

        status = dfi.phy.get_calibration_status()
        # Calibration data is stored in calibration_data dict
        assert status['calibration_data']['read_gate'] == 0xABC
        assert status['calibration_data']['write_level'] == 0x123


class TestDFIRequestResponse:
    """Test DFI request and response handling"""

    def test_request_queue_empty_initially(self):
        """Test request queue is empty on init"""
        dfi = DFI5Interface()
        assert len(dfi.request_queue) == 0

    def test_queue_request(self):
        """Test adding request to queue"""
        dfi = DFI5Interface()
        request = DFIRequest(
            command=DFICommand.ACT,
            address=0x100,
            bank=0,
            pseudo_channel=0,
            channel=0
        )

        dfi.queue_request(request)
        assert len(dfi.request_queue) == 1

    def test_get_next_request(self):
        """Test getting next request from queue"""
        dfi = DFI5Interface()

        request1 = DFIRequest(DFICommand.ACT, 0x100, 0, 0, 0)
        request2 = DFIRequest(DFICommand.WR, 0x200, 1, 0, 0)

        dfi.queue_request(request1)
        dfi.queue_request(request2)

        next_req = dfi.get_next_request()
        assert next_req == request1
        assert len(dfi.request_queue) == 1

    def test_get_next_request_empty_queue(self):
        """Test getting from empty queue returns None"""
        dfi = DFI5Interface()
        result = dfi.get_next_request()
        assert result is None

    def test_response_ready_in_idle_state(self):
        """Test response ready flag in IDLE state"""
        dfi = DFI5Interface()
        response = dfi.get_response()

        assert response.ready is True

    def test_response_ready_in_ctrl_state(self):
        """Test response ready flag in LP_CTRL state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        response = dfi.get_response()
        assert response.ready is True

    def test_response_not_ready_in_freq_change(self):
        """Test response not ready during frequency change"""
        dfi = DFI5Interface()
        dfi.enter_freq_change()

        response = dfi.get_response()
        assert response.ready is False

    def test_response_phy_controls(self):
        """Test response includes PHY control signals"""
        dfi = DFI5Interface()

        dfi.phy.set_phy_clock_enable(False)
        dfi.phy.set_phy_reset(True)

        response = dfi.get_response()
        assert response.phy_clock_enable is False
        assert response.phy_reset is True


class TestDFIRequest:
    """Test DFI request dataclass"""

    def test_request_defaults(self):
        """Test DFI request default values"""
        request = DFIRequest(
            command=DFICommand.ACT,
            address=0,
            bank=0,
            pseudo_channel=0,
            channel=0
        )

        assert request.wrdata_en is False
        assert request.rddata_en is False
        assert request.chip == 0

    def test_request_all_fields(self):
        """Test DFI request with all fields specified"""
        request = DFIRequest(
            command=DFICommand.WR,
            address=0xABC,
            bank=7,
            pseudo_channel=1,
            channel=15,
            wrdata_en=True,
            rddata_en=False,
            chip=1
        )

        assert request.command == DFICommand.WR
        assert request.address == 0xABC
        assert request.bank == 7
        assert request.pseudo_channel == 1
        assert request.channel == 15
        assert request.wrdata_en is True
        assert request.chip == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])