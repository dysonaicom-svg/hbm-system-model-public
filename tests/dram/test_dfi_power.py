"""
Tests for DFI Power State Transitions and Low Power Modes

Tests the DFI 5.0/5.1 power state management including:
- Power state transitions (ACT, LP, PD, SR)
- Low power entry/exit sequences
- Power management timing
- Address/command mapping for power states

Reference: DFI 5.0 Specification Section 3
"""

import pytest
from model.dram.dfi_interface import (
    DFI5Interface,
    DFICommand,
    DFILowPowerState,
    DFIRequest,
    DFIRequestQueueConfig,
    DFITimingParameters,
    DFIStateTransitionError,
    DFI5FreqChangeState,
)


class TestDFIPowerStateTransitions:
    """Test DFI power state transitions"""

    def test_power_state_from_active_to_lp_ctrl(self):
        """Test transition from active (LP_IDLE) to LP_CTRL"""
        dfi = DFI5Interface()

        # Initially in LP_IDLE (active)
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

        # Transition to LP_CTRL
        result = dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        assert result is True
        assert dfi.lp_state == DFILowPowerState.LP_CTRL

    def test_power_state_from_active_to_lp_data(self):
        """Test transition from active to LP_DATA"""
        dfi = DFI5Interface()

        result = dfi.set_low_power_state(DFILowPowerState.LP_DATA)
        assert result is True
        assert dfi.lp_state == DFILowPowerState.LP_DATA

    def test_power_state_from_lp_ctrl_to_idle(self):
        """Test transition from LP_CTRL back to IDLE"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        result = dfi.set_low_power_state(DFILowPowerState.LP_IDLE)
        assert result is True
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_power_state_from_lp_data_to_idle(self):
        """Test transition from LP_DATA back to IDLE"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)

        result = dfi.set_low_power_state(DFILowPowerState.LP_IDLE)
        assert result is True
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_power_state_all_valid_transitions(self):
        """Test all valid power state transitions"""
        dfi = DFI5Interface()

        # LP_IDLE -> LP_CTRL (valid)
        assert dfi.set_low_power_state(DFILowPowerState.LP_CTRL, enforce_timing=False)

        # LP_CTRL -> LP_DATA (valid)
        assert dfi.set_low_power_state(DFILowPowerState.LP_DATA, enforce_timing=False)

        # LP_DATA -> LP_IDLE (valid)
        assert dfi.set_low_power_state(DFILowPowerState.LP_IDLE, enforce_timing=False)

    def test_power_state_invalid_transition(self):
        """Test invalid transition raises error"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_FREQ_CHANGE)

        # LP_FREQ_CHANGE -> LP_CTRL is invalid
        with pytest.raises(DFIStateTransitionError):
            dfi.request_low_power(DFILowPowerState.LP_CTRL)

    def test_power_state_request_vs_set(self):
        """Test difference between set_low_power_state and request_low_power"""
        dfi = DFI5Interface()

        # set_low_power_state bypasses handshake
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        assert dfi.lp_state == DFILowPowerState.LP_CTRL

        # request_low_power uses handshake
        dfi.reset()
        result = dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert result is True
        assert dfi.lp_req is True


class TestDFIActPowerState:
    """Test ACT power state (Active/IDLE state)"""

    def test_act_state_is_idle(self):
        """LP_IDLE is the ACTIVE (normal operation) state"""
        dfi = DFI5Interface()
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_commands_accepted_in_act_state(self):
        """Commands should be accepted in ACT state"""
        dfi = DFI5Interface()

        request = DFIRequest(
            command=DFICommand.ACT,
            address=0x100,
            bank=0,
            pseudo_channel=0,
            channel=0
        )

        result = dfi.queue_request(request)
        assert result is True

    def test_is_ready_in_act_state(self):
        """Interface should be ready in ACT state"""
        dfi = DFI5Interface()
        assert dfi.is_ready() is True

    def test_can_accept_request_in_act_state(self):
        """Interface can accept requests in ACT state"""
        dfi = DFI5Interface()
        assert dfi.can_accept_request() is True


class TestDFILowPowerStates:
    """Test LP power states"""

    def test_lp_ctrl_state_entry(self):
        """Test entering LP_CTRL state"""
        dfi = DFI5Interface()

        result = dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert result is True
        assert dfi.lp_req is True
        assert dfi.lp_state == DFILowPowerState.LP_CTRL

    def test_lp_ctrl_state_entry_with_latency(self):
        """LP_CTRL entry should observe entry latency"""
        dfi = DFI5Interface()
        entry_latency = dfi.timing.tLP_CTRL_ENTER

        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        # Before latency expires
        for _ in range(entry_latency - 1):
            dfi.tick()
        assert dfi.lp_ack is False

        # After latency
        dfi.tick()
        assert dfi.lp_ack is True

    def test_lp_data_state_entry(self):
        """Test entering LP_DATA state"""
        dfi = DFI5Interface()

        result = dfi.request_low_power(DFILowPowerState.LP_DATA)
        assert result is True
        assert dfi.lp_state == DFILowPowerState.LP_DATA

    def test_lp_data_state_entry_with_latency(self):
        """LP_DATA entry should observe entry latency"""
        dfi = DFI5Interface()
        entry_latency = dfi.timing.tLP_DATA_ENTER

        dfi.request_low_power(DFILowPowerState.LP_DATA)

        for _ in range(entry_latency):
            dfi.tick()

        assert dfi.lp_ack is True

    def test_lp_freq_change_state(self):
        """Test LP_FREQ_CHANGE state"""
        dfi = DFI5Interface()

        dfi.enter_freq_change()
        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE

    def test_lp_state_is_not_ready(self):
        """LP_DATA should not be ready for commands"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)

        assert dfi.is_ready() is False

    def test_lp_ctrl_is_ready(self):
        """LP_CTRL should still be ready for some commands"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        assert dfi.is_ready() is True


class TestDFIPowerDownState:
    """Test PD (Power Down) state"""

    def test_pwr_down_request(self):
        """Test requesting power down"""
        dfi = DFI5Interface()

        result = dfi.request_pwr_down()
        assert result is True
        assert dfi.pwr_down_req is True

    def test_pwr_down_ack(self):
        """Test power down acknowledgment"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()

        dfi.set_pwr_down_ack(True)
        assert dfi.pwr_down_ack is True

    def test_pwr_down_auto_ack(self):
        """Power down should auto-acknowledge after latency"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()

        for _ in range(dfi.timing.tPWR_DOWN):
            dfi.tick()

        assert dfi.pwr_down_ack is True

    def test_pwr_down_rejected_when_active(self):
        """Cannot request power down when already in progress"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()

        result = dfi.request_pwr_down()
        assert result is False


class TestDFISelfRefreshState:
    """Test SR (Self Refresh) state - simulated via LP states"""

    def test_self_refresh_enter_via_lp_ctrl(self):
        """Self-refresh can be entered via LP_CTRL"""
        dfi = DFI5Interface()

        dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert dfi.lp_state == DFILowPowerState.LP_CTRL

    def test_self_refresh_enter_via_lp_data(self):
        """Self-refresh can be entered via LP_DATA"""
        dfi = DFI5Interface()

        dfi.request_low_power(DFILowPowerState.LP_DATA)
        assert dfi.lp_state == DFILowPowerState.LP_DATA

    def test_self_refresh_wakeup(self):
        """Self-refresh wakeup should clear wakeup signal"""
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

        assert dfi.lp_wakeup is False
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_self_refresh_clear_wakeup(self):
        """Wakeup signal can be cleared"""
        dfi = DFI5Interface()

        dfi.wakeup_from_low_power()
        assert dfi.lp_wakeup is True

        dfi.clear_lp_wakeup()
        assert dfi.lp_wakeup is False


class TestDFILowPowerEntryExit:
    """Test low power entry/exit sequences"""

    def test_lp_entry_sets_request_signal(self):
        """LP entry should set lp_req signal"""
        dfi = DFI5Interface()

        dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert dfi.lp_req is True

    def test_lp_entry_sets_ack_after_latency(self):
        """LP entry should set lp_ack after entry latency"""
        dfi = DFI5Interface()

        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        assert dfi.lp_ack is True

    def test_lp_exit_clears_request(self):
        """LP exit should clear lp_req"""
        dfi = DFI5Interface()

        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        # Wait for entry
        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        dfi.wakeup_from_low_power()

        # Wait for exit
        for _ in range(dfi.timing.tLP_CTRL_EXIT + 1):
            dfi.tick()

        assert dfi.lp_req is False

    def test_lp_exit_clears_ack(self):
        """LP exit should clear lp_ack"""
        dfi = DFI5Interface()

        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        # Wait for entry
        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        dfi.wakeup_from_low_power()

        # Wait for exit
        for _ in range(dfi.timing.tLP_CTRL_EXIT + 1):
            dfi.tick()

        assert dfi.lp_ack is False

    def test_lp_exit_returns_to_idle(self):
        """LP exit should return to LP_IDLE"""
        dfi = DFI5Interface()

        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        # Wait for entry
        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        dfi.wakeup_from_low_power()

        # Wait for exit
        for _ in range(dfi.timing.tLP_CTRL_EXIT + 1):
            dfi.tick()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_lp_entry_exit_timing(self):
        """Entry and exit timing should be independent"""
        dfi = DFI5Interface()
        entry_latency = dfi.timing.tLP_CTRL_ENTER
        exit_latency = dfi.timing.tLP_CTRL_EXIT

        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        # Verify entry timing
        for i in range(entry_latency):
            dfi.tick()
        # After entry latency, ack should be set
        assert dfi.lp_ack is True

        dfi.wakeup_from_low_power()

        # Verify exit timing
        for i in range(exit_latency):
            dfi.tick()
        # After exit latency, should be back to IDLE
        assert dfi.lp_state == DFILowPowerState.LP_IDLE


class TestDFIPowerStateCommands:
    """Test commands that interact with power states"""

    def test_refresh_in_power_state(self):
        """Refresh command should work in LP_CTRL"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        request = DFIRequest(
            command=DFICommand.REFab,
            address=0,
            bank=0,
            pseudo_channel=0,
            channel=0
        )

        result = dfi.queue_request(request)
        assert result is True

    def test_activate_in_power_state(self):
        """ACT command should work in LP_IDLE"""
        dfi = DFI5Interface()

        request = DFIRequest(
            command=DFICommand.ACT,
            address=0x100,
            bank=0,
            pseudo_channel=0,
            channel=0
        )

        result = dfi.queue_request(request)
        assert result is True

    def test_read_blocked_in_lp_data(self):
        """Read command should be blocked in LP_DATA"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)

        # Interface should not be ready
        assert dfi.is_ready() is False


class TestDFIPowerManagementSignals:
    """Test DFI power management signals"""

    def test_pwr_up_done_signal(self):
        """pwr_up_done signal should be settable"""
        dfi = DFI5Interface()

        dfi.set_pwr_up_done(True)
        assert dfi.pwr_up_done is True

        dfi.set_pwr_up_done(False)
        assert dfi.pwr_up_done is False

    def test_pwr_down_req_signal(self):
        """pwr_down_req signal should be set on request"""
        dfi = DFI5Interface()

        dfi.request_pwr_down()
        assert dfi.pwr_down_req is True

    def test_pwr_down_ack_signal(self):
        """pwr_down_ack signal should be set by PHY"""
        dfi = DFI5Interface()

        dfi.set_pwr_down_ack(True)
        assert dfi.pwr_down_ack is True

    def test_power_signals_response_integration(self):
        """Power signals should be in response"""
        dfi = DFI5Interface()
        dfi.set_pwr_up_done(True)
        dfi.request_pwr_down()

        response = dfi.get_response()
        assert hasattr(response, 'pwr_up_done')
        assert hasattr(response, 'pwr_down_ack')


class TestDFIPowerStateStatistics:
    """Test statistics tracking for power states"""

    def test_lp_transitions_count(self):
        """LP transitions should be counted"""
        dfi = DFI5Interface()

        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        stats = dfi.get_statistics()
        assert stats['lp_transitions'] >= 1

    def test_power_cycles_count(self):
        """Power cycles should be counted"""
        dfi = DFI5Interface()

        dfi.request_pwr_down()
        stats = dfi.get_statistics()
        assert stats['power_cycles'] == 1

    def test_power_state_reset(self):
        """Power state should be reset"""
        dfi = DFI5Interface()

        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        dfi.reset()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE


class TestDFIPowerStateAddressMapping:
    """Test address/command mapping for power states"""

    def test_address_encoding_in_power_state(self):
        """Address encoding should work in any power state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        request = dfi.encode_command('ACT', {
            'row': 0x1000,
            'bank': 5,
            'pseudo_channel': 1,
            'channel': 15
        })

        assert request.address == 0x1000
        assert request.bank == 5
        assert request.pseudo_channel == 1
        assert request.channel == 15

    def test_command_priority_in_power_state(self):
        """Command priority should work in any power state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        request = dfi.encode_command('ACT', {
            'row': 0x100,
            'bank': 0
        }, priority=10)

        assert request.priority == 10

    def test_timestamp_in_power_state(self):
        """Timestamp should advance in power state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        request1 = dfi.encode_command('ACT', {'row': 0, 'bank': 0})
        assert request1.timestamp >= 0

        dfi.tick()
        request2 = dfi.encode_command('ACT', {'row': 0, 'bank': 0})
        assert request2.timestamp > request1.timestamp


class TestDFIPowerStateResponse:
    """Test response handling in power states"""

    def test_response_lp_state_reflects_current(self):
        """Response should reflect current LP state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        response = dfi.get_response()
        assert response.lp_state == DFILowPowerState.LP_CTRL

    def test_response_ready_in_lp_ctrl(self):
        """Response ready should be True in LP_CTRL"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        response = dfi.get_response()
        assert response.ready is True

    def test_response_ready_in_lp_data(self):
        """Response ready should be False in LP_DATA"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)

        response = dfi.get_response()
        assert response.ready is False

    def test_response_lp_ack_reflects_state(self):
        """Response lp_ack should reflect state"""
        dfi = DFI5Interface()

        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        # Before entry latency
        response = dfi.get_response()
        assert response.lp_ack is False

        # After entry latency
        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        response = dfi.get_response()
        assert response.lp_ack is True


class TestDFIPowerStateQueueInteraction:
    """Test request queue interaction with power states"""

    def test_queue_accepts_in_lp_ctrl(self):
        """Queue should accept requests in LP_CTRL"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        request = DFIRequest(DFICommand.ACT, 0, 0, 0, 0)
        result = dfi.queue_request(request)
        assert result is True

    def test_queue_blocked_in_lp_data(self):
        """Queue should handle backpressure in LP_DATA"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)

        # Even though queue might accept, is_ready is False
        assert dfi.is_ready() is False

    def test_queue_full_in_power_state(self):
        """Queue full condition should work in any state"""
        dfi = DFI5Interface(
            queue_config=DFIRequestQueueConfig(max_size=2)
        )

        dfi.queue_request(DFIRequest(DFICommand.ACT, 0, 0, 0, 0))
        dfi.queue_request(DFIRequest(DFICommand.ACT, 0, 0, 0, 0))

        assert dfi.is_queue_full is True

    def test_can_accept_request_checks_both(self):
        """can_accept_request should check queue and LP state"""
        dfi = DFI5Interface(
            queue_config=DFIRequestQueueConfig(max_size=2)
        )

        # Fill queue
        dfi.queue_request(DFIRequest(DFICommand.ACT, 0, 0, 0, 0))
        dfi.queue_request(DFIRequest(DFICommand.ACT, 0, 0, 0, 0))

        assert dfi.can_accept_request() is False


class TestDFIPowerStateTraining:
    """Test training interaction with power states"""

    def test_training_in_lp_idle(self):
        """Training should be possible in LP_IDLE"""
        dfi = DFI5Interface()
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

        dfi.start_training()
        assert dfi.training_in_progress is True

    def test_training_in_lp_ctrl(self):
        """Training should be possible in LP_CTRL"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        dfi.start_training()
        assert dfi.training_in_progress is True

    def test_training_complete(self):
        """Training completion should update response"""
        dfi = DFI5Interface()

        dfi.start_training()
        dfi.complete_training()

        response = dfi.get_response()
        assert response.calibration_done is True
        assert response.training_state == "complete"


class TestDFIPowerStateFreqChange:
    """Test frequency change interaction with power states"""

    def test_freq_change_in_lp_idle(self):
        """Frequency change should be possible in LP_IDLE"""
        dfi = DFI5Interface()
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

        result = dfi.request_freq_change(1600)
        assert result is True

    def test_freq_change_in_lp_ctrl(self):
        """Frequency change can be requested in LP_CTRL (checks FC state, not LP state)"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        # request_freq_change checks FC state, not LP state
        result = dfi.request_freq_change(1600)
        assert result is True
        assert dfi.get_target_frequency() == 1600

    def test_freq_change_sets_lp_state(self):
        """Frequency change should set LP_FREQ_CHANGE state"""
        dfi = DFI5Interface()

        dfi.enter_freq_change()
        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE

    def test_freq_change_complete_resets_state(self):
        """Frequency change completion should reset LP state"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        dfi.exit_freq_change()

        # Advance through state machine
        for _ in range(50):
            dfi.tick()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])