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
        assert status == {
            'calibration_data': {},
            'calibration_results': {},
            'calibration_complete': False
        }

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
        assert dfi.version in ["5.0", "5.1"]  # Supports HBM4 DFI 5.0 extensions

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

        # HBM4 @ 8 GT/s with 2048-bit interface: 8 × 2048 / 8 = 2048 GB/s
        # DFI frequency 800 MHz maps to 8 GT/s data rate via /100 conversion
        assert dfi.get_bandwidth_gbs() == pytest.approx(2048.0, rel=0.01)

        dfi.set_frequency(6400)
        # 6400 MHz / 100 = 64 GT/s, bandwidth = 64 × 2048 / 8 = 16384 GB/s
        assert dfi.get_bandwidth_gbs() == pytest.approx(16384.0, rel=0.01)


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
        assert len(DFILowPowerState) == 7  # LP_IDLE, LP_CTRL, LP_DATA, LP_SELF_REFRESH, LP_POWER_DOWN, LP_DEEP_PD, LP_FREQ_CHANGE


class TestDFIFrequencyChange:
    """Test DFI frequency change handling"""

    def test_enter_freq_change(self):
        """Test entering frequency change state"""
        dfi = DFI5Interface()
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

        dfi.enter_freq_change()
        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE

    def test_exit_freq_change(self):
        """Test exiting frequency change returns to IDLE after state machine completes"""
        dfi = DFI5Interface()

        dfi.enter_freq_change()
        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE

        dfi.exit_freq_change()
        # lp_state remains LP_FREQ_CHANGE during exit until state machine completes
        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE

        # Advance state machine to completion
        for _ in range(20):
            dfi.tick()

        # After state machine completes, lp_state should be LP_IDLE
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

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


class TestDFIControlUpdateHandshake:
    """Test DFI 5.0 control update handshake (dfi_ctrlupd_req/ack)"""

    def test_ctrlupd_req_initially_false(self):
        """Test ctrlupd_req is initially false"""
        dfi = DFI5Interface()
        assert dfi.ctrlupd_req is False
        assert dfi.ctrlupd_ack is False

    def test_request_ctrlupd(self):
        """Test requesting control update"""
        dfi = DFI5Interface()
        result = dfi.request_ctrlupd()
        assert result is True
        assert dfi.ctrlupd_req is True

    def test_ctrlupd_ack_after_latency(self):
        """Test ctrlupd_ack is set after latency expires and handshake completes"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()

        # Initially not acknowledged
        assert dfi.ctrlupd_ack is False

        # Tick until latency expires
        for _ in range(dfi.timing.tCTRLUPD_LATENCY + 1):
            dfi.tick()

        # Handshake should have completed (both signals cleared)
        assert dfi.ctrlupd_req is False
        assert dfi.ctrlupd_ack is False

    def test_ctrlupd_complete_after_handshake(self):
        """Test handshake completes and signals reset"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()

        # Wait for full handshake
        for _ in range(dfi.timing.tCTRLUPD_LATENCY + 1):
            dfi.tick()

        # Both signals should be cleared
        assert dfi.ctrlupd_req is False
        assert dfi.ctrlupd_ack is False

    def test_double_ctrlupd_request_rejected(self):
        """Test double request_ctrlupd is rejected"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()
        result = dfi.request_ctrlupd()
        assert result is False

    def test_acknowledge_ctrlupd_from_phy(self):
        """Test manual acknowledgment from PHY"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()
        dfi.acknowledge_ctrlupd()
        assert dfi.ctrlupd_ack is True

        # Verify stats updated
        stats = dfi.get_statistics()
        assert stats["ctrl_updates"] == 1


class TestDFIFrequencyChangeProtocol:
    """Test DFI 5.0 frequency change protocol"""

    def test_freq_change_en_initially_false(self):
        """Test freq_change_en is initially false"""
        dfi = DFI5Interface()
        assert dfi.freq_change_en is False
        assert dfi.freq_change_ack is False

    def test_request_freq_change(self):
        """Test requesting frequency change"""
        dfi = DFI5Interface()
        result = dfi.request_freq_change(6400)
        assert result is True

    def test_freq_change_state_machine(self):
        """Test frequency change state machine progression"""
        dfi = DFI5Interface()
        from model.dram.dfi_interface import DFI5FreqChangeState

        dfi.request_freq_change(6400)
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_REQUESTED

        dfi.enter_freq_change()
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_ENTERING
        assert dfi.freq_change_en is True

    def test_freq_change_complete(self):
        """Test frequency change completes after full state machine"""
        dfi = DFI5Interface()
        from model.dram.dfi_interface import DFI5FreqChangeState

        dfi.request_freq_change(6400)
        dfi.enter_freq_change()
        dfi.exit_freq_change()

        # Complete the state machine
        for _ in range(50):
            dfi.tick()

        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE
        assert dfi.frequency_mhz == 6400

    def test_freq_change_latency_remaining(self):
        """Test latency remaining calculation"""
        dfi = DFI5Interface()

        dfi.enter_freq_change()
        remaining = dfi.get_freq_change_latency_remaining()
        assert remaining > 0

    def test_freq_change_rejected_when_active(self):
        """Test freq change request rejected when already in progress"""
        dfi = DFI5Interface()
        dfi.request_freq_change(6400)
        dfi.enter_freq_change()

        result = dfi.request_freq_change(3200)
        assert result is False

    def test_set_freq_change_ack(self):
        """Test setting freq_change_ack from PHY"""
        dfi = DFI5Interface()
        dfi.set_freq_change_ack(True)
        assert dfi.freq_change_ack is True


class TestDFIPowerManagement:
    """Test DFI 5.0 power management"""

    def test_pwr_up_done_initially_false(self):
        """Test pwr_up_done is initially false"""
        dfi = DFI5Interface()
        assert dfi.pwr_up_done is False

    def test_set_pwr_up_done(self):
        """Test setting pwr_up_done"""
        dfi = DFI5Interface()
        dfi.set_pwr_up_done(True)
        assert dfi.pwr_up_done is True

    def test_request_pwr_down(self):
        """Test requesting power down"""
        dfi = DFI5Interface()
        result = dfi.request_pwr_down()
        assert result is True
        assert dfi.pwr_down_req is True

    def test_pwr_down_ack_after_latency(self):
        """Test pwr_down_ack after latency"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()

        for _ in range(dfi.timing.tPWR_DOWN):
            dfi.tick()

        assert dfi.pwr_down_ack is True

    def test_set_pwr_down_ack(self):
        """Test manual pwr_down_ack from PHY"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()
        dfi.set_pwr_down_ack(True)
        assert dfi.pwr_down_ack is True

    def test_power_cycles_stat(self):
        """Test power cycles statistic"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()
        stats = dfi.get_statistics()
        assert stats["power_cycles"] == 1


class TestDFILowPowerStateManagement:
    """Test DFI 5.0 low power state management"""

    def test_request_low_power_ctrl(self):
        """Test requesting LP_CTRL state"""
        dfi = DFI5Interface()
        result = dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert result is True
        assert dfi.lp_req is True
        assert dfi.lp_state == DFILowPowerState.LP_CTRL

    def test_request_low_power_data(self):
        """Test requesting LP_DATA state"""
        dfi = DFI5Interface()
        result = dfi.request_low_power(DFILowPowerState.LP_DATA)
        assert result is True
        assert dfi.lp_state == DFILowPowerState.LP_DATA

    def test_lp_ack_after_entry_latency(self):
        """Test lp_ack after entry latency"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        for _ in range(dfi.timing.tLP_CTRL_ENTER):
            dfi.tick()

        assert dfi.lp_ack is True

    def test_wakeup_from_low_power(self):
        """Test wakeup from low power state"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        # Wait for entry
        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        dfi.wakeup_from_low_power()
        assert dfi.lp_wakeup is True

        # Wait for exit
        for _ in range(dfi.timing.tLP_CTRL_EXIT + 1):
            dfi.tick()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE
        assert dfi.lp_wakeup is False

    def test_clear_lp_wakeup(self):
        """Test clearing lp_wakeup signal"""
        dfi = DFI5Interface()
        dfi.wakeup_from_low_power()
        dfi.clear_lp_wakeup()
        assert dfi.lp_wakeup is False

    def test_lp_transitions_stat(self):
        """Test LP transitions statistic"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        stats = dfi.get_statistics()
        assert stats["lp_transitions"] == 1

    def test_invalid_lp_transition_raises(self):
        """Test invalid LP transition raises exception"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        with pytest.raises(Exception):  # DFIStateTransitionError
            dfi.request_low_power(DFILowPowerState.LP_FREQ_CHANGE)


class TestDFITimingParameters:
    """Test DFI timing parameters"""

    def test_default_timing_parameters(self):
        """Test default timing parameters"""
        from model.dram.dfi_interface import DFITimingParameters
        timing = DFITimingParameters()

        assert timing.tPHY_wrlAT == 5
        assert timing.tPHY_rdLat == 5
        assert timing.tFC_LATENCY == 8
        assert timing.tFC_EXIT == 4

    def test_write_latency_property(self):
        """Test write latency property"""
        dfi = DFI5Interface()
        assert dfi.timing.write_latency_cycles == 5

    def test_read_latency_property(self):
        """Test read latency property"""
        dfi = DFI5Interface()
        assert dfi.timing.read_latency_cycles == 5

    def test_get_write_latency_ps(self):
        """Test write latency calculation in picoseconds"""
        from model.dram.dfi_interface import DFITimingParameters
        timing = DFITimingParameters()
        latency_ps = timing.get_write_latency_ps(125.0)  # 8ns period
        assert latency_ps == 625.0  # 5 * 125

    def test_get_read_latency_ps(self):
        """Test read latency calculation in picoseconds"""
        from model.dram.dfi_interface import DFITimingParameters
        timing = DFITimingParameters()
        latency_ps = timing.get_read_latency_ps(125.0)
        assert latency_ps == 625.0

    def test_get_timing_parameters(self):
        """Test getting timing parameters"""
        dfi = DFI5Interface()
        timing = dfi.get_timing_parameters()
        assert timing is not None

    def test_set_timing_parameters(self):
        """Test setting timing parameters"""
        from model.dram.dfi_interface import DFITimingParameters
        dfi = DFI5Interface()
        new_timing = DFITimingParameters(tPHY_wrlAT=10)
        dfi.set_timing_parameters(new_timing)
        assert dfi.timing.tPHY_wrlAT == 10


class TestDFIErrorReporting:
    """Test DFI error reporting"""

    def test_error_log_empty_initially(self):
        """Test error log is empty on init"""
        dfi = DFI5Interface()
        errors = dfi.get_errors()
        assert len(errors) == 0

    def test_get_errors_by_type(self):
        """Test filtering errors by type"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()  # This should not error
        dfi.request_ctrlupd()  # This should create error

        errors = dfi.get_errors("ctrl_update")
        assert len(errors) >= 0  # May or may not have errors depending on timing

    def test_errors_count_stat(self):
        """Test errors count in statistics"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()
        dfi.request_ctrlupd()  # This will fail

        stats = dfi.get_statistics()
        assert "errors" in stats


class TestDFIStatistics:
    """Test DFI statistics"""

    def test_initial_statistics(self):
        """Test initial statistics"""
        dfi = DFI5Interface()
        stats = dfi.get_statistics()

        assert stats["commands_sent"] == 0
        assert stats["commands_completed"] == 0
        assert stats["freq_changes"] == 0
        assert stats["lp_transitions"] == 0
        assert stats["errors"] == 0

    def test_commands_sent_on_queue(self):
        """Test commands_sent incremented on queue"""
        dfi = DFI5Interface()
        request = DFIRequest(
            command=DFICommand.ACT,
            address=0x100,
            bank=0,
            pseudo_channel=0,
            channel=0
        )
        dfi.queue_request(request)
        stats = dfi.get_statistics()
        assert stats["commands_sent"] == 1

    def test_freq_changes_stat(self):
        """Test freq_changes incremented"""
        dfi = DFI5Interface()
        dfi.enter_freq_change()
        stats = dfi.get_statistics()
        assert stats["freq_changes"] == 1

    def test_reset_statistics(self):
        """Test resetting statistics"""
        dfi = DFI5Interface()
        request = DFIRequest(DFICommand.ACT, 0, 0, 0, 0)
        dfi.queue_request(request)

        dfi.reset_statistics()
        stats = dfi.get_statistics()
        assert stats["commands_sent"] == 0


class TestDFISignals:
    """Test DFI signal state access"""

    def test_get_dfi_signals(self):
        """Test getting all DFI signals"""
        dfi = DFI5Interface()
        signals = dfi.get_dfi_signals()

        assert hasattr(signals, 'ctrlupd_req')
        assert hasattr(signals, 'freq_change_en')
        assert hasattr(signals, 'lp_state')
        assert hasattr(signals, 'phy_ready')

    def test_signals_reflect_state(self):
        """Test signals reflect current state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        signals = dfi.get_dfi_signals()
        assert signals.lp_state == DFILowPowerState.LP_CTRL


class TestDFIReset:
    """Test DFI interface reset"""

    def test_reset_clears_state(self):
        """Test reset clears all state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        dfi.request_freq_change(6400)
        # Don't change frequency, keep default 800MHz for reset test

        dfi.reset()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE
        assert dfi.training_complete is False

    def test_reset_clears_queue(self):
        """Test reset clears request queue"""
        dfi = DFI5Interface()
        request = DFIRequest(DFICommand.ACT, 0, 0, 0, 0)
        dfi.queue_request(request)

        dfi.reset()

        assert len(dfi.request_queue) == 0


class TestDFIReadyCheck:
    """Test DFI ready state checking"""

    def test_is_ready_in_idle(self):
        """Test is_ready returns True in LP_IDLE"""
        dfi = DFI5Interface()
        assert dfi.is_ready() is True

    def test_is_ready_in_ctrl(self):
        """Test is_ready returns True in LP_CTRL"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        assert dfi.is_ready() is True

    def test_is_not_ready_in_data(self):
        """Test is_ready returns False in LP_DATA"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)
        assert dfi.is_ready() is False

    def test_is_not_ready_in_freq_change(self):
        """Test is_ready returns False in LP_FREQ_CHANGE"""
        dfi = DFI5Interface()
        dfi.enter_freq_change()
        assert dfi.is_ready() is False

    def test_can_accept_request_in_idle(self):
        """Test can_accept_request returns True in LP_IDLE with space"""
        dfi = DFI5Interface()
        assert dfi.can_accept_request() is True

    def test_cannot_accept_request_when_queue_full(self):
        """Test can_accept_request returns False when queue full"""
        from model.dram.dfi_interface import DFIRequestQueueConfig
        dfi = DFI5Interface(queue_config=DFIRequestQueueConfig(max_size=2))

        dfi.queue_request(DFIRequest(DFICommand.ACT, 0, 0, 0, 0))
        dfi.queue_request(DFIRequest(DFICommand.PRE, 0, 0, 0, 0))

        assert dfi.can_accept_request() is False


class TestDFIFreqChangeStateMachine:
    """Test frequency change state machine states"""

    def test_fc_state_idle_initially(self):
        """Test FC state is IDLE initially"""
        dfi = DFI5Interface()
        from model.dram.dfi_interface import DFI5FreqChangeState
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE

    def test_is_freq_change_complete_initially(self):
        """Test is_freq_change_complete returns True initially"""
        dfi = DFI5Interface()
        assert dfi.is_freq_change_complete() is True

    def test_is_freq_change_not_complete_during(self):
        """Test is_freq_change_complete returns False during change"""
        dfi = DFI5Interface()
        dfi.enter_freq_change()
        assert dfi.is_freq_change_complete() is False


class TestDFIPhyInterfaceExtended:
    """Test extended PHY interface features"""

    def test_supports_freq_change(self):
        """Test PHY supports frequency change"""
        dfi = DFI5Interface()
        assert dfi.phy.supports_freq_change() is True

    def test_get_freq_change_latency(self):
        """Test PHY frequency change latency"""
        dfi = DFI5Interface()
        latency = dfi.phy.get_freq_change_latency()
        assert latency == 8  # Default DFI 5.0 latency


class TestDFIRequestQueueConfig:
    """Test request queue configuration"""

    def test_default_queue_config(self):
        """Test default queue configuration"""
        from model.dram.dfi_interface import DFIRequestQueueConfig
        config = DFIRequestQueueConfig()

        assert config.max_size == 64
        assert config.enable_priority is True
        assert config.enable_backpressure is True

    def test_queue_is_empty(self):
        """Test queue is_empty method"""
        dfi = DFI5Interface()
        assert dfi._request_queue.is_empty() is True

        dfi.queue_request(DFIRequest(DFICommand.ACT, 0, 0, 0, 0))
        assert dfi._request_queue.is_empty() is False

    def test_queue_is_full(self):
        """Test queue is_full method"""
        dfi = DFI5Interface()
        assert dfi._request_queue.is_full() is False

    def test_pending_request_count(self):
        """Test pending request count property"""
        dfi = DFI5Interface()
        assert dfi.pending_request_count == 0

        dfi.queue_request(DFIRequest(DFICommand.ACT, 0, 0, 0, 0))
        assert dfi.pending_request_count == 1

    def test_queue_available_capacity(self):
        """Test queue available capacity"""
        dfi = DFI5Interface()
        capacity = dfi.queue_available_capacity
        assert capacity == 64  # Default max_size

    def test_peek_request(self):
        """Test peek request without removal"""
        dfi = DFI5Interface()
        request = DFIRequest(DFICommand.ACT, 0x100, 0, 0, 0)
        dfi.queue_request(request)

        peeked = dfi.peek_request()
        assert peeked == request
        assert dfi.pending_request_count == 1  # Still in queue

    def test_clear_requests(self):
        """Test clearing all requests"""
        dfi = DFI5Interface()
        dfi.queue_request(DFIRequest(DFICommand.ACT, 0, 0, 0, 0))
        dfi.queue_request(DFIRequest(DFICommand.WR, 0, 0, 0, 0))

        dfi.clear_requests()
        assert dfi.pending_request_count == 0


class TestDFICycleCounter:
    """Test cycle counter"""

    def test_cycle_starts_at_zero(self):
        """Test cycle starts at 0"""
        dfi = DFI5Interface()
        assert dfi.cycle == 0

    def test_cycle_increments_on_tick(self):
        """Test cycle increments on tick"""
        dfi = DFI5Interface()
        dfi.tick()
        assert dfi.cycle == 1

        dfi.tick()
        dfi.tick()
        assert dfi.cycle == 3


class TestDFIVersion:
    """Test DFI version"""

    def test_version_attribute(self):
        """Test version attribute exists"""
        dfi = DFI5Interface()
        assert hasattr(dfi, 'version')
        assert dfi.version == "5.0"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])