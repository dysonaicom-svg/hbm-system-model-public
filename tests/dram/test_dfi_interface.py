"""
Tests for DFI 5.1 Interface

Tests the DFI 5.1 interface between HBM4 controller and PHY.
"""

import pytest
from model.dram.dfi_interface import (
    DFI5Interface, DFICommand, DFILowPowerState,
    DFIRequest, DFIResponse, DFIPhyIF
)
from model.dram.hbm4_spec import HBM4Spec


class TestDFIInterfaceCreation:
    """Test DFI interface creation"""

    def test_dfi_interface_creation(self):
        """DFI 5.1 interface must be created"""
        dfi = DFI5Interface()
        assert dfi is not None
        assert dfi.version == "5.1"

    def test_dfi_has_supported_commands(self):
        """DFI must have supported commands list"""
        dfi = DFI5Interface()
        assert len(dfi.supported_commands) > 0


class TestDFICommands:
    """Test DFI command encoding"""

    def test_encode_act_command(self):
        """ACT command must be encoded correctly"""
        dfi = DFI5Interface()

        request = dfi.encode_command('ACT', {
            'row': 100,
            'bank': 5,
            'pseudo_channel': 0,
            'channel': 15
        })

        assert request.command == DFICommand.ACT
        assert request.address == 100
        assert request.bank == 5

    def test_encode_pre_command(self):
        """PRE command must be encoded correctly"""
        dfi = DFI5Interface()

        request = dfi.encode_command('PRE', {
            'bank': 3,
            'pseudo_channel': 1
        })

        assert request.command == DFICommand.PRE

    def test_encode_rd_command(self):
        """RD command must set rddata_en"""
        dfi = DFI5Interface()

        request = dfi.encode_command('RD', {
            'col': 10,
            'bank': 0,
            'pseudo_channel': 0
        })

        assert request.command == DFICommand.RD
        assert request.rddata_en is True
        assert request.wrdata_en is False

    def test_encode_wr_command(self):
        """WR command must set wrdata_en"""
        dfi = DFI5Interface()

        request = dfi.encode_command('WR', {
            'col': 10,
            'bank': 0,
            'pseudo_channel': 0
        })

        assert request.command == DFICommand.WR
        assert request.wrdata_en is True
        assert request.rddata_en is False

    def test_encode_refresh_command(self):
        """REFab command must be encoded correctly"""
        dfi = DFI5Interface()

        request = dfi.encode_command('REFab', {})

        assert request.command == DFICommand.REFab


class TestDFILowPowerStates:
    """Test DFI low power states"""

    def test_lp_idle_state(self):
        """LP_IDLE state must be available"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)

        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_lp_ctrl_state(self):
        """LP_CTRL state must be available"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        assert dfi.lp_state == DFILowPowerState.LP_CTRL

    def test_lp_data_state(self):
        """LP_DATA state must be available"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)

        assert dfi.lp_state == DFILowPowerState.LP_DATA

    def test_lp_freq_change_state(self):
        """LP_FREQ_CHANGE state must be available"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_FREQ_CHANGE)

        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE


class TestDFITraining:
    """Test DFI training interface"""

    def test_training_not_started_initially(self):
        """Training should not be started initially"""
        dfi = DFI5Interface()

        response = dfi.get_response()
        assert response.training_state == "not_started"
        assert response.calibration_done is False

    def test_start_training(self):
        """start_training() must initiate training"""
        dfi = DFI5Interface()

        dfi.start_training()

        response = dfi.get_response()
        assert response.training_state == "in_progress"
        assert response.calibration_done is False

    def test_complete_training(self):
        """complete_training() must mark training done"""
        dfi = DFI5Interface()

        dfi.start_training()
        dfi.complete_training()

        response = dfi.get_response()
        assert response.training_state == "complete"
        assert response.calibration_done is True


class TestDFIPhyIF:
    """Test DFI PHY Independent Mode"""

    def test_phy_independent_mode_support(self):
        """DFI must support PHY Independent Mode"""
        dfi = DFI5Interface()

        assert hasattr(dfi.phy, 'phy_independent_mode')
        assert dfi.phy.phy_independent_mode is True

    def test_phy_clock_enable(self):
        """PHY clock enable must be supported"""
        dfi = DFI5Interface()

        dfi.phy.set_phy_clock_enable(True)
        assert dfi.phy.phy_clock_enable is True

        dfi.phy.set_phy_clock_enable(False)
        assert dfi.phy.phy_clock_enable is False

    def test_phy_reset(self):
        """PHY reset control must be supported"""
        dfi = DFI5Interface()

        dfi.phy.set_phy_reset(True)
        assert dfi.phy.phy_reset is True

        dfi.phy.set_phy_reset(False)
        assert dfi.phy.phy_reset is False


class TestDFIResponse:
    """Test DFI response handling"""

    def test_get_response_with_lp_state(self):
        """Response must reflect current LP state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        response = dfi.get_response()
        assert response.lp_state == DFILowPowerState.LP_CTRL

    def test_response_ready_when_idle(self):
        """Response ready should be True when idle"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)

        response = dfi.get_response()
        assert response.ready is True

    def test_response_ready_when_ctrl(self):
        """Response ready should be True when in LP_CTRL"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        response = dfi.get_response()
        assert response.ready is True


class TestDFICommandsEnum:
    """Test DFI command enum values"""

    def test_act_command_value(self):
        """ACT command must have correct enum value"""
        assert DFICommand.ACT.value == 0b0000

    def test_pre_command_value(self):
        """PRE command must have correct enum value"""
        assert DFICommand.PRE.value == 0b0001

    def test_rd_command_value(self):
        """RD command must have correct enum value"""
        assert DFICommand.RD.value == 0b0011

    def test_wr_command_value(self):
        """WR command must have correct enum value"""
        assert DFICommand.WR.value == 0b0100

    def test_all_commands_defined(self):
        """All expected commands must be defined"""
        expected = ['ACT', 'PRE', 'PREA', 'RD', 'WR', 'RDA', 'WRA', 'REFab', 'REFsb']
        for cmd_name in expected:
            assert hasattr(DFICommand, cmd_name)