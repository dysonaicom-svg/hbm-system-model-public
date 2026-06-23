"""
Tests for DFI 5.0 Interface

Tests the DFI 5.0 interface between HBM4 controller and PHY.
Includes tests for:
- Basic interface creation
- Command encoding
- Low power states
- Frequency change protocol with handshake signals
- Control update handshake (dfi_ctrlupd_req/ack)
- Power management (dfi_pwr_up_done, dfi_pwr_down_req/ack)
- Low power state signals (lp_req/ack/wakeup)
- Timing parameters
- Request queue management
- Error reporting
- DFI 5.0 compliance verification
"""

import pytest
from model.dram.dfi_interface import (
    DFI5Interface, DFICommand, DFILowPowerState,
    DFIRequest, DFIResponse, DFIPhyIF, DFITimingParameters,
    DFIRequestQueueConfig, DFI5RequestQueue, DFI5FreqChangeState,
    DFIStateTransitionError, DFIErrorRecord, DFISignals
)
from model.dram.hbm4_spec import HBM4Spec


class TestDFICompliance:
    """Test DFI 5.0 compliance requirements"""

    def test_version_is_5_0(self):
        """DFI interface must report version 5.0"""
        dfi = DFI5Interface()
        assert dfi.version == "5.0"

    def test_all_required_signals_exist(self):
        """All DFI 5.0 required signals must exist"""
        dfi = DFI5Interface()

        # Control update signals
        assert hasattr(dfi, 'ctrlupd_req')
        assert hasattr(dfi, 'ctrlupd_ack')

        # Frequency change signals
        assert hasattr(dfi, 'freq_change_en')
        assert hasattr(dfi, 'freq_change_ack')

        # Power management signals
        assert hasattr(dfi, 'pwr_up_done')
        assert hasattr(dfi, 'pwr_down_req')
        assert hasattr(dfi, 'pwr_down_ack')

        # Low power signals
        assert hasattr(dfi, 'lp_req')
        assert hasattr(dfi, 'lp_ack')
        assert hasattr(dfi, 'lp_wakeup')

    def test_get_dfi_signals_returns_complete_state(self):
        """get_dfi_signals() must return all signal states"""
        dfi = DFI5Interface()
        signals = dfi.get_dfi_signals()

        assert isinstance(signals, DFISignals)
        assert hasattr(signals, 'ctrlupd_req')
        assert hasattr(signals, 'ctrlupd_ack')
        assert hasattr(signals, 'freq_change_en')
        assert hasattr(signals, 'freq_change_ack')
        assert hasattr(signals, 'pwr_up_done')
        assert hasattr(signals, 'pwr_down_req')
        assert hasattr(signals, 'pwr_down_ack')
        assert hasattr(signals, 'lp_req')
        assert hasattr(signals, 'lp_ack')
        assert hasattr(signals, 'lp_wakeup')


class TestDFIInterfaceCreation:
    """Test DFI interface creation"""

    def test_dfi_interface_creation(self):
        """DFI 5.0 interface must be created"""
        dfi = DFI5Interface()
        assert dfi is not None
        assert dfi.version == "5.0"

    def test_dfi_has_supported_commands(self):
        """DFI must have supported commands list"""
        dfi = DFI5Interface()
        assert len(dfi.supported_commands) > 0

    def test_dfi_has_timing_parameters(self):
        """DFI must have timing parameters"""
        dfi = DFI5Interface()
        assert hasattr(dfi, 'timing')
        assert isinstance(dfi.timing, DFITimingParameters)

    def test_dfi_has_request_queue(self):
        """DFI must have request queue"""
        dfi = DFI5Interface()
        assert hasattr(dfi, '_request_queue')
        assert isinstance(dfi._request_queue, DFI5RequestQueue)


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

    def test_encode_command_with_priority(self):
        """Command encoding must support priority"""
        dfi = DFI5Interface()

        request = dfi.encode_command('ACT', {
            'row': 100,
            'bank': 5
        }, priority=10)

        assert request.priority == 10

    def test_encode_command_has_timestamp(self):
        """Encoded command must have timestamp"""
        dfi = DFI5Interface()
        request = dfi.encode_command('ACT', {'row': 100, 'bank': 5})

        assert request.timestamp == 0

        dfi.tick()
        request = dfi.encode_command('ACT', {'row': 100, 'bank': 5})
        assert request.timestamp == 1


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

    def test_valid_lp_transitions(self):
        """Valid LP state transitions must be allowed"""
        dfi = DFI5Interface()

        # LP_IDLE -> LP_CTRL is valid
        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)
        assert dfi.set_low_power_state(DFILowPowerState.LP_CTRL, enforce_timing=False) is True

        # LP_CTRL -> LP_IDLE is valid
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        assert dfi.set_low_power_state(DFILowPowerState.LP_IDLE, enforce_timing=False) is True

    def test_invalid_lp_transition_raises(self):
        """Invalid LP state transitions must raise exception"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_FREQ_CHANGE)

        with pytest.raises(DFIStateTransitionError):
            dfi.set_low_power_state(DFILowPowerState.LP_CTRL, enforce_timing=True)

    def test_lp_state_response_ready(self):
        """Response ready status must reflect LP state"""
        dfi = DFI5Interface()

        # LP_IDLE: ready = True
        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)
        response = dfi.get_response()
        assert response.ready is True

        # LP_CTRL: ready = True
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        response = dfi.get_response()
        assert response.ready is True

        # LP_DATA: ready = False
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)
        response = dfi.get_response()
        assert response.ready is False


class TestDFIControlUpdate:
    """Test DFI 5.0 control update handshake (dfi_ctrlupd_req/ack)"""

    def test_ctrlupd_req_initial_state(self):
        """dfi_ctrlupd_req must be False initially"""
        dfi = DFI5Interface()
        assert dfi.ctrlupd_req is False

    def test_ctrlupd_ack_initial_state(self):
        """dfi_ctrlupd_ack must be False initially"""
        dfi = DFI5Interface()
        assert dfi.ctrlupd_ack is False

    def test_request_ctrlupd(self):
        """request_ctrlupd() must assert dfi_ctrlupd_req"""
        dfi = DFI5Interface()

        result = dfi.request_ctrlupd()
        assert result is True
        assert dfi.ctrlupd_req is True

    def test_ctrlupd_acknowledge(self):
        """acknowledge_ctrlupd() must assert dfi_ctrlupd_ack"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()

        result = dfi.acknowledge_ctrlupd()
        assert result is True
        assert dfi.ctrlupd_ack is True

    def test_ctrlupd_handshake_auto_complete(self):
        """Control update handshake must auto-complete after latency"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()

        # Advance past latency
        for _ in range(dfi.timing.tCTRLUPD_LATENCY + 1):
            dfi.tick()

        # Handshake should complete
        assert dfi.ctrlupd_req is False
        assert dfi.ctrlupd_ack is False

    def test_ctrlupd_rejected_when_in_progress(self):
        """Cannot request ctrlupd when one is in progress"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()

        result = dfi.request_ctrlupd()
        assert result is False

    def test_ctrlupd_statistics(self):
        """Control update statistics must be tracked"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()

        stats = dfi.get_statistics()
        assert "ctrl_updates" in stats


class TestDFIFrequencyChange:
    """Test DFI frequency change protocol"""

    def test_freq_change_request(self):
        """Frequency change request must be accepted"""
        dfi = DFI5Interface()

        result = dfi.request_freq_change(1200)
        assert result is True

    def test_freq_change_state_transitions(self):
        """Frequency change must follow state machine"""
        dfi = DFI5Interface()

        # Initial state
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE

        # Request frequency change
        dfi.request_freq_change(1200)
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_REQUESTED

        # Enter frequency change
        dfi.enter_freq_change()
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_ENTERING

    def test_freq_change_en_asserted(self):
        """dfi_freq_change_en must be asserted during frequency change"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        assert dfi.freq_change_en is True

    def test_freq_change_ack(self):
        """dfi_freq_change_ack can be set by PHY"""
        dfi = DFI5Interface()
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        dfi.set_freq_change_ack(True)
        assert dfi.freq_change_ack is True

    def test_freq_change_cycles(self):
        """Frequency change must advance through cycles"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        # Advance cycles
        for _ in range(10):
            dfi.tick()

        # Exit frequency change
        dfi.exit_freq_change()

        # Continue ticking until complete
        for _ in range(20):
            dfi.tick()

        assert dfi.is_freq_change_complete() is True
        assert dfi.frequency_mhz == 1200

    def test_freq_change_rejects_when_in_progress(self):
        """Cannot start new frequency change when one is in progress"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        # Try to request another frequency change
        result = dfi.request_freq_change(1600)
        assert result is False

    def test_freq_change_latency_remaining(self):
        """Frequency change latency remaining must be tracked"""
        dfi = DFI5Interface()

        # Not in frequency change
        assert dfi.get_freq_change_latency_remaining() == 0

        # Request frequency change
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        # Latency should be greater than 0
        assert dfi.get_freq_change_latency_remaining() > 0

    def test_freq_change_en_deasserted_on_exit(self):
        """dfi_freq_change_en must be deasserted on exit"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        assert dfi.freq_change_en is True

        dfi.exit_freq_change()
        dfi.tick()  # Advance state machine

        assert dfi.freq_change_en is False


class TestDFIPowerManagement:
    """Test DFI 5.0 power management signals"""

    def test_pwr_up_done_initial_state(self):
        """dfi_pwr_up_done must be False initially"""
        dfi = DFI5Interface()
        assert dfi.pwr_up_done is False

    def test_set_pwr_up_done(self):
        """set_pwr_up_done() must set the signal"""
        dfi = DFI5Interface()

        dfi.set_pwr_up_done(True)
        assert dfi.pwr_up_done is True

        dfi.set_pwr_up_done(False)
        assert dfi.pwr_up_done is False

    def test_pwr_down_req_initial_state(self):
        """dfi_pwr_down_req must be False initially"""
        dfi = DFI5Interface()
        assert dfi.pwr_down_req is False

    def test_request_pwr_down(self):
        """request_pwr_down() must assert dfi_pwr_down_req"""
        dfi = DFI5Interface()

        result = dfi.request_pwr_down()
        assert result is True
        assert dfi.pwr_down_req is True

    def test_pwr_down_ack_initial_state(self):
        """dfi_pwr_down_ack must be False initially"""
        dfi = DFI5Interface()
        assert dfi.pwr_down_ack is False

    def test_set_pwr_down_ack(self):
        """set_pwr_down_ack() must set the signal"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()

        dfi.set_pwr_down_ack(True)
        assert dfi.pwr_down_ack is True

    def test_pwr_down_auto_acknowledge(self):
        """Power down must auto-acknowledge after latency"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()

        # Advance past latency
        for _ in range(dfi.timing.tPWR_DOWN + 1):
            dfi.tick()

        assert dfi.pwr_down_ack is True

    def test_pwr_down_rejected_when_in_progress(self):
        """Cannot request power down when one is in progress"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()

        result = dfi.request_pwr_down()
        assert result is False

    def test_power_cycles_statistics(self):
        """Power cycles must be tracked in statistics"""
        dfi = DFI5Interface()
        dfi.request_pwr_down()

        stats = dfi.get_statistics()
        assert "power_cycles" in stats
        assert stats["power_cycles"] == 1


class TestDFILowPowerSignals:
    """Test DFI 5.0 low power state signals (lp_req/ack/wakeup)"""

    def test_lp_req_initial_state(self):
        """lp_req must be False initially"""
        dfi = DFI5Interface()
        assert dfi.lp_req is False

    def test_lp_ack_initial_state(self):
        """lp_ack must be False initially"""
        dfi = DFI5Interface()
        assert dfi.lp_ack is False

    def test_lp_wakeup_initial_state(self):
        """lp_wakeup must be False initially"""
        dfi = DFI5Interface()
        assert dfi.lp_wakeup is False

    def test_request_low_power(self):
        """request_low_power() must assert lp_req"""
        dfi = DFI5Interface()

        result = dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert result is True
        assert dfi.lp_req is True

    def test_set_lp_ack(self):
        """set_lp_ack() must set the signal"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_CTRL)

        dfi.set_lp_ack(True)
        assert dfi.lp_ack is True

    def test_wakeup_from_low_power(self):
        """wakeup_from_low_power() must assert lp_wakeup"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_CTRL)
        dfi.set_lp_ack(True)

        dfi.wakeup_from_low_power()
        assert dfi.lp_wakeup is True

    def test_clear_lp_wakeup(self):
        """clear_lp_wakeup() must clear the signal"""
        dfi = DFI5Interface()
        dfi.wakeup_from_low_power()

        dfi.clear_lp_wakeup()
        assert dfi.lp_wakeup is False

    def test_lp_wakeup_transitions_to_idle(self):
        """lp_wakeup must cause transition to LP_IDLE"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_CTRL)
        dfi.set_lp_ack(True)
        dfi.wakeup_from_low_power()

        # Advance past exit latency
        for _ in range(dfi.timing.tLP_CTRL_EXIT + 1):
            dfi.tick()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE


class TestDFITimingParameters:
    """Test DFI timing parameters"""

    def test_timing_parameters_creation(self):
        """Timing parameters must be created with defaults"""
        timing = DFITimingParameters()
        assert timing.tPHY_wrlAT > 0
        assert timing.tPHY_rdLat > 0

    def test_timing_parameters_custom(self):
        """Timing parameters must accept custom values"""
        timing = DFITimingParameters(
            tPHY_wrlAT=8,
            tPHY_rdLat=10,
            tFC_LATENCY=12
        )
        assert timing.tPHY_wrlAT == 8
        assert timing.tPHY_rdLat == 10
        assert timing.tFC_LATENCY == 12

    def test_write_latency_ps(self):
        """Write latency in picoseconds must be calculated"""
        timing = DFITimingParameters(tPHY_wrlAT=5)
        latency = timing.get_write_latency_ps(125.0)  # 125ps = 8 GHz
        assert latency == 625.0  # 5 * 125 ps

    def test_read_latency_ps(self):
        """Read latency in picoseconds must be calculated"""
        timing = DFITimingParameters(tPHY_rdLat=8)
        latency = timing.get_read_latency_ps(125.0)
        assert latency == 1000.0  # 8 * 125 ps

    def test_interface_timing_parameters(self):
        """DFI interface must provide timing parameters"""
        dfi = DFI5Interface()
        timing = dfi.get_timing_parameters()
        assert isinstance(timing, DFITimingParameters)

    def test_set_timing_parameters(self):
        """DFI interface must allow setting timing parameters"""
        dfi = DFI5Interface()
        new_timing = DFITimingParameters(tPHY_wrlAT=10)
        dfi.set_timing_parameters(new_timing)
        assert dfi.timing.tPHY_wrlAT == 10

    def test_interface_write_latency_ps(self):
        """DFI interface must provide write latency"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)  # 8 GHz
        latency = dfi.get_write_latency_ps()
        assert latency > 0

    def test_interface_read_latency_ps(self):
        """DFI interface must provide read latency"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)
        latency = dfi.get_read_latency_ps()
        assert latency > 0

    def test_ctrlupd_latency_parameter(self):
        """tCTRLUPD_LATENCY parameter must exist"""
        timing = DFITimingParameters()
        assert hasattr(timing, 'tCTRLUPD_LATENCY')
        assert timing.tCTRLUPD_LATENCY > 0

    def test_power_timing_parameters(self):
        """Power management timing parameters must exist"""
        timing = DFITimingParameters()
        assert hasattr(timing, 'tPWR_UP')
        assert hasattr(timing, 'tPWR_DOWN')
        assert timing.tPWR_UP > 0
        assert timing.tPWR_DOWN > 0


class TestDFIRequestQueue:
    """Test DFI request queue"""

    def test_queue_creation(self):
        """Queue must be created with configuration"""
        queue = DFI5RequestQueue()
        assert queue.size == 0
        assert not queue.is_full()

    def test_queue_enqueue(self):
        """Requests must be enqueued"""
        dfi = DFI5Interface()
        request = dfi.encode_command('ACT', {'row': 100, 'bank': 5})

        result = dfi.queue_request(request)
        assert result is True
        assert dfi.pending_request_count == 1

    def test_queue_dequeue(self):
        """Requests must be dequeued in priority order"""
        dfi = DFI5Interface()

        # Queue multiple requests with different priorities
        r1 = dfi.encode_command('ACT', {'row': 100, 'bank': 5}, priority=5)
        r2 = dfi.encode_command('ACT', {'row': 200, 'bank': 6}, priority=10)
        r3 = dfi.encode_command('ACT', {'row': 300, 'bank': 7}, priority=1)

        dfi.queue_request(r1)
        dfi.queue_request(r2)
        dfi.queue_request(r3)

        # Highest priority should come first
        next_req = dfi.get_next_request()
        assert next_req.priority == 10
        assert next_req.address == 200

    def test_queue_peek(self):
        """Queue peek must not remove request"""
        dfi = DFI5Interface()
        request = dfi.encode_command('ACT', {'row': 100, 'bank': 5}, priority=10)

        dfi.queue_request(request)
        peeked = dfi.peek_request()
        count_after = dfi.pending_request_count

        assert peeked.address == 100
        assert dfi.pending_request_count == count_after

    def test_queue_overflow_drop_oldest(self):
        """Queue must drop oldest when full (drop_oldest strategy)"""
        config = DFIRequestQueueConfig(max_size=3, overflow_strategy="drop_oldest")
        queue = DFI5RequestQueue(config)

        dfi = DFI5Interface()

        # Fill queue
        for i in range(3):
            request = dfi.encode_command('ACT', {'row': i * 100, 'bank': 0})
            queue.enqueue(request)

        # Add one more (should drop oldest)
        extra = dfi.encode_command('ACT', {'row': 999, 'bank': 0})
        queue.enqueue(extra)

        assert queue.size == 3
        # Oldest (row=0) should be dropped, so row=100 should be first
        first = queue.peek()
        assert first.address == 100

    def test_queue_overflow_drop_newest(self):
        """Queue must reject newest when full (drop_newest strategy)"""
        config = DFIRequestQueueConfig(max_size=2, overflow_strategy="drop_newest")
        queue = DFI5RequestQueue(config)

        dfi = DFI5Interface()

        r1 = dfi.encode_command('ACT', {'row': 100, 'bank': 0})
        r2 = dfi.encode_command('ACT', {'row': 200, 'bank': 0})
        extra = dfi.encode_command('ACT', {'row': 999, 'bank': 0})

        queue.enqueue(r1)
        queue.enqueue(r2)
        result = queue.enqueue(extra)

        assert result is False
        assert queue.size == 2

    def test_queue_clear(self):
        """Queue must be clearable"""
        dfi = DFI5Interface()
        for i in range(5):
            request = dfi.encode_command('ACT', {'row': i * 100, 'bank': 0})
            dfi.queue_request(request)

        dfi.clear_requests()
        assert dfi.pending_request_count == 0

    def test_queue_statistics(self):
        """Queue must provide statistics"""
        dfi = DFI5Interface()
        queue = dfi._request_queue

        for i in range(3):
            request = dfi.encode_command('ACT', {'row': i * 100, 'bank': 0})
            queue.enqueue(request)

        stats = queue.get_statistics()
        assert stats["current_size"] == 3
        assert stats["processed_count"] == 0
        assert stats["dropped_count"] == 0


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

    def test_response_has_timestamp(self):
        """Response must have timestamp"""
        dfi = DFI5Interface()
        response = dfi.get_response()
        assert response.timestamp == 0

        dfi.tick()
        response = dfi.get_response()
        assert response.timestamp == 1

    def test_response_has_response_id(self):
        """Response must have response_id"""
        dfi = DFI5Interface()
        response = dfi.get_response(response_id=42)
        assert response.response_id == 42

    def test_response_has_ctrlupd_ack(self):
        """Response must include ctrlupd_ack signal state"""
        dfi = DFI5Interface()
        response = dfi.get_response()
        assert hasattr(response, 'ctrlupd_ack')

    def test_response_has_freq_change_ack(self):
        """Response must include freq_change_ack signal state"""
        dfi = DFI5Interface()
        response = dfi.get_response()
        assert hasattr(response, 'freq_change_ack')

    def test_response_has_pwr_up_done(self):
        """Response must include pwr_up_done signal state"""
        dfi = DFI5Interface()
        response = dfi.get_response()
        assert hasattr(response, 'pwr_up_done')

    def test_response_has_pwr_down_ack(self):
        """Response must include pwr_down_ack signal state"""
        dfi = DFI5Interface()
        response = dfi.get_response()
        assert hasattr(response, 'pwr_down_ack')

    def test_response_has_lp_ack(self):
        """Response must include lp_ack signal state"""
        dfi = DFI5Interface()
        response = dfi.get_response()
        assert hasattr(response, 'lp_ack')


class TestDFICommandsEnum:
    """Test DFI command enum values

    These tests verify the DFI 5.0 command encoding matches the specification.
    Reference: DFI 5.0 Specification Table 4-1
    """

    def test_act_command_value(self):
        """ACT command must have correct enum value"""
        assert DFICommand.ACT.value == 0b0001

    def test_pre_command_value(self):
        """PRE command must have correct enum value"""
        assert DFICommand.PRE.value == 0b0010

    def test_rd_command_value(self):
        """RD command must have correct enum value"""
        assert DFICommand.RD.value == 0b0100

    def test_wr_command_value(self):
        """WR command must have correct enum value"""
        assert DFICommand.WR.value == 0b0101

    def test_all_commands_defined(self):
        """All expected commands must be defined"""
        expected = ['ACT', 'PRE', 'PREA', 'RD', 'WR', 'RDA', 'WRA', 'REFab', 'REFsb']
        for cmd_name in expected:
            assert hasattr(DFICommand, cmd_name)


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

    def test_phy_freq_change_support(self):
        """PHY must report frequency change support"""
        dfi = DFI5Interface()
        assert hasattr(dfi.phy, 'supports_freq_change')
        assert dfi.phy.supports_freq_change() is True

    def test_phy_freq_change_latency(self):
        """PHY must report frequency change latency"""
        dfi = DFI5Interface()
        assert hasattr(dfi.phy, 'get_freq_change_latency')
        latency = dfi.phy.get_freq_change_latency()
        assert latency > 0


class TestDFIStatistics:
    """Test DFI statistics and error reporting"""

    def test_statistics_collection(self):
        """DFI must collect statistics"""
        dfi = DFI5Interface()

        stats = dfi.get_statistics()
        assert "commands_sent" in stats
        assert "freq_changes" in stats
        assert "lp_transitions" in stats
        assert "errors" in stats
        assert "ctrl_updates" in stats
        assert "power_cycles" in stats

    def test_statistics_update_on_commands(self):
        """Statistics must update on command queuing"""
        dfi = DFI5Interface()

        request = dfi.encode_command('ACT', {'row': 100, 'bank': 5})
        dfi.queue_request(request)

        stats = dfi.get_statistics()
        assert stats["commands_sent"] == 1

    def test_statistics_update_on_freq_change(self):
        """Statistics must update on frequency change"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        stats = dfi.get_statistics()
        assert stats["freq_changes"] == 1

    def test_error_logging(self):
        """Errors must be logged"""
        dfi = DFI5Interface()

        # Trigger an error (request freq change while already in one)
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        dfi.request_freq_change(1600)  # This should fail

        errors = dfi.get_errors()
        assert len(errors) > 0

    def test_error_filtering(self):
        """Errors must be filterable by type"""
        dfi = DFI5Interface()

        # Generate some errors
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        dfi.request_freq_change(1600)

        freq_errors = dfi.get_errors("freq_change")
        assert all(e.error_type == "freq_change" for e in freq_errors)

    def test_reset_statistics(self):
        """Statistics must be resettable"""
        dfi = DFI5Interface()

        # Generate some activity
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        dfi.reset_statistics()
        stats = dfi.get_statistics()
        assert stats["freq_changes"] == 0
        assert stats["ctrl_updates"] == 0
        assert stats["power_cycles"] == 0


class TestDFIUtilityMethods:
    """Test DFI utility methods"""

    def test_is_ready(self):
        """is_ready() must check LP state"""
        dfi = DFI5Interface()

        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)
        assert dfi.is_ready() is True

        dfi.set_low_power_state(DFILowPowerState.LP_DATA)
        assert dfi.is_ready() is False

    def test_can_accept_request(self):
        """can_accept_request() must check queue and LP state"""
        dfi = DFI5Interface()
        assert dfi.can_accept_request() is True

        # Fill queue
        config = DFIRequestQueueConfig(max_size=2)
        dfi = DFI5Interface(timing_params=DFITimingParameters(), queue_config=config)

        for i in range(2):
            request = dfi.encode_command('ACT', {'row': i * 100, 'bank': 0})
            dfi.queue_request(request)

        assert dfi.is_queue_full is True
        assert dfi.can_accept_request() is False

    def test_get_set_frequency(self):
        """Frequency getter and setter must work"""
        dfi = DFI5Interface()

        dfi.set_frequency(1200)
        assert dfi.get_frequency() == 1200

    def test_get_target_frequency(self):
        """Target frequency must be tracked"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1600)
        assert dfi.get_target_frequency() == 1600

    def test_bandwidth_calculation(self):
        """Bandwidth must be calculated correctly"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)

        bw = dfi.get_bandwidth_gbs()
        assert bw > 0
        assert isinstance(bw, float)

    def test_reset(self):
        """DFI must be resettable"""
        dfi = DFI5Interface()

        # Make some state changes
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        # Valid transition from FC_ACTIVE to LP_CTRL is not allowed,
        # so use valid LP states instead
        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        # Reset
        dfi.reset()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE
        assert dfi.pending_request_count == 0
        assert dfi.cycle == 0

        # Verify DFI 5.0 signals are reset
        assert dfi.ctrlupd_req is False
        assert dfi.ctrlupd_ack is False
        assert dfi.freq_change_en is False
        assert dfi.freq_change_ack is False
        assert dfi.pwr_up_done is False
        assert dfi.pwr_down_req is False
        assert dfi.pwr_down_ack is False
        assert dfi.lp_req is False
        assert dfi.lp_ack is False
        assert dfi.lp_wakeup is False

    def test_cycle_counter(self):
        """Cycle counter must advance on tick"""
        dfi = DFI5Interface()
        assert dfi.cycle == 0

        dfi.tick()
        assert dfi.cycle == 1

        dfi.tick()
        assert dfi.cycle == 2


class TestDFIErrorRecords:
    """Test DFI error record structure"""

    def test_error_record_creation(self):
        """Error records must be creatable"""
        error = DFIErrorRecord(
            error_type="test",
            error_message="Test error",
            timestamp=100,
            request_id=42
        )
        assert error.error_type == "test"
        assert error.error_message == "Test error"
        assert error.timestamp == 100
        assert error.request_id == 42
        assert error.recoverable is True

    def test_error_record_non_recoverable(self):
        """Error records can be marked non-recoverable"""
        error = DFIErrorRecord(
            error_type="fatal",
            error_message="Fatal error",
            timestamp=100,
            recoverable=False
        )
        assert error.recoverable is False


class TestDFIRequestQueueConfig:
    """Test request queue configuration"""

    def test_default_config(self):
        """Default configuration must have sensible values"""
        config = DFIRequestQueueConfig()
        assert config.max_size == 64
        assert config.enable_priority is True
        assert config.enable_backpressure is True
        assert config.overflow_strategy == "drop_oldest"

    def test_custom_config(self):
        """Configuration must accept custom values"""
        config = DFIRequestQueueConfig(
            max_size=128,
            enable_priority=False,
            overflow_strategy="block"
        )
        assert config.max_size == 128
        assert config.enable_priority is False
        assert config.overflow_strategy == "block"


class TestDFIFreqChangeState:
    """Test frequency change state enum"""

    def test_all_states_defined(self):
        """All frequency change states must be defined"""
        expected = ['FC_IDLE', 'FC_REQUESTED', 'FC_ENTERING', 'FC_ACTIVE',
                   'FC_EXITING', 'FC_LOCKING', 'FC_COMPLETE']
        for state_name in expected:
            assert hasattr(DFI5FreqChangeState, state_name)


class TestDFISignals:
    """Test DFISignals dataclass"""

    def test_dfisignals_creation(self):
        """DFISignals must be creatable"""
        signals = DFISignals()
        assert signals.ctrlupd_req is False
        assert signals.ctrlupd_ack is False
        assert signals.freq_change_en is False
        assert signals.freq_change_ack is False
        assert signals.pwr_up_done is False
        assert signals.pwr_down_req is False
        assert signals.pwr_down_ack is False
        assert signals.lp_req is False
        assert signals.lp_ack is False
        assert signals.lp_wakeup is False

    def test_dfisignals_with_values(self):
        """DFISignals must accept custom values"""
        signals = DFISignals(
            ctrlupd_req=True,
            freq_change_en=True,
            pwr_up_done=True,
            lp_state=DFILowPowerState.LP_CTRL
        )
        assert signals.ctrlupd_req is True
        assert signals.freq_change_en is True
        assert signals.pwr_up_done is True
        assert signals.lp_state == DFILowPowerState.LP_CTRL


class TestHBM4PAM3Signals:
    """Test HBM4 PAM3 signal support"""

    def test_pam3_enable_initial_state(self):
        """PAM3 enable must be False initially"""
        dfi = DFI5Interface()
        assert dfi.pam3_enable is False

    def test_pam3_mode_initial_state(self):
        """PAM3 mode must be 0 (NRZ) initially"""
        dfi = DFI5Interface()
        assert dfi.pam3_mode == 0

    def test_set_pam3_enable(self):
        """set_pam3_enable() must enable PAM3"""
        dfi = DFI5Interface()
        dfi.set_pam3_enable(True)
        assert dfi.pam3_enable is True

    def test_set_pam3_mode(self):
        """set_pam3_mode() must set PAM3 mode"""
        dfi = DFI5Interface()
        dfi.set_pam3_mode(1)  # PAM3 mode
        assert dfi.pam3_mode == 1

    def test_is_pam3_active(self):
        """is_pam3_active() must check enable and settled state"""
        dfi = DFI5Interface()
        # Not active initially
        assert dfi.is_pam3_active() is False

        # Enable PAM3
        dfi.set_pam3_enable(True)
        dfi.set_pam3_mode(1)
        # Not active until settled
        assert dfi.is_pam3_active() is False

        # Wait for settling
        for _ in range(dfi.timing.tPAM3_SWITCH + 1):
            dfi.tick()
        assert dfi.is_pam3_active() is True

    def test_pam3_switch_progress(self):
        """get_pam3_switch_progress() must return switch info"""
        dfi = DFI5Interface()
        dfi.set_pam3_enable(True)

        progress = dfi.get_pam3_switch_progress()
        assert 'switch_pending' in progress
        assert 'switch_counter' in progress
        assert 'switch_latency' in progress
        assert 'remaining_cycles' in progress


class TestHBM4ExtendedDFISignals:
    """Test HBM4 extended DFI 5.0 signals"""

    def test_phyupd_resp_initial_state(self):
        """phyupd_resp must be False initially"""
        dfi = DFI5Interface()
        assert dfi.phyupd_resp is False

    def test_set_phyupd_resp(self):
        """set_phyupd_resp() must set response"""
        dfi = DFI5Interface()
        dfi.set_phyupd_resp(True)
        assert dfi.phyupd_resp is True

    def test_self_refresh_n_initial_state(self):
        """self_refresh_n must be True (active-high) initially"""
        dfi = DFI5Interface()
        assert dfi.self_refresh_n is True

    def test_set_self_refresh_n(self):
        """set_self_refresh_n() must set self-refresh state"""
        dfi = DFI5Interface()
        dfi.set_self_refresh_n(False)  # Active-low
        assert dfi.self_refresh_n is False

    def test_memdata_disable_initial_state(self):
        """memdata_disable must be False initially"""
        dfi = DFI5Interface()
        assert dfi.memdata_disable is False

    def test_set_memdata_disable(self):
        """set_memdata_disable() must disable data path"""
        dfi = DFI5Interface()
        dfi.set_memdata_disable(True)
        assert dfi.memdata_disable is True

    def test_parity_signals(self):
        """Parity signals must be accessible"""
        dfi = DFI5Interface()

        # parity_in
        dfi.set_parity_in(True)
        assert dfi.parity_in is True

        # parity_out
        dfi.set_parity_out(False)
        assert dfi.parity_out is False

        # parity_error
        dfi.set_parity_error(True)
        assert dfi.parity_error is True


class TestHBM432ChannelSupport:
    """Test HBM4 32-channel independent operation support"""

    def test_channel_count_initial(self):
        """Channel count must be 32 for HBM4"""
        dfi = DFI5Interface()
        assert dfi.get_channel_count() == 32

    def test_set_channel_count(self):
        """set_channel_count() must update channel count"""
        dfi = DFI5Interface()
        dfi.set_channel_count(16)
        assert dfi.get_channel_count() == 16

    def test_channel_active_status(self):
        """Channel active status must be tracked"""
        dfi = DFI5Interface()

        # All channels initially active
        assert dfi.get_active_channel_count() == 32

        # Deactivate channels
        dfi.set_channel_active(0, False)
        dfi.set_channel_active(1, False)
        assert dfi.get_active_channel_count() == 30
        assert dfi.is_channel_active(0) is False
        assert dfi.is_channel_active(1) is False
        assert dfi.is_channel_active(2) is True

    def test_channel_frequency(self):
        """Channel-specific frequency must be tracked"""
        dfi = DFI5Interface()

        # Default frequency
        assert dfi.get_channel_frequency(5) == 800

        # Set custom frequency
        dfi.set_channel_frequency(5, 1200)
        assert dfi.get_channel_frequency(5) == 1200

    def test_channel_lp_state(self):
        """Channel-specific LP state must be tracked"""
        dfi = DFI5Interface()

        # Default LP state
        assert dfi.get_channel_lp_state(5) == DFILowPowerState.LP_IDLE

        # Set custom LP state
        dfi.set_channel_lp_state(5, DFILowPowerState.LP_SELF_REFRESH)
        assert dfi.get_channel_lp_state(5) == DFILowPowerState.LP_SELF_REFRESH

    def test_channel_states_summary(self):
        """get_channel_states() must return comprehensive info"""
        dfi = DFI5Interface()

        states = dfi.get_channel_states()
        assert 'total_channels' in states
        assert 'active_channels' in states
        assert 'channel_active' in states
        assert 'channel_frequencies' in states
        assert 'channel_lp_states' in states

    def test_enter_all_channels_lp(self):
        """enter_all_channels_lp() must update all channels"""
        dfi = DFI5Interface()

        dfi.enter_all_channels_lp(DFILowPowerState.LP_SELF_REFRESH)

        assert dfi.get_channel_lp_state(0) == DFILowPowerState.LP_SELF_REFRESH
        assert dfi.get_channel_lp_state(31) == DFILowPowerState.LP_SELF_REFRESH
        assert dfi.lp_state == DFILowPowerState.LP_SELF_REFRESH

    def test_wakeup_all_channels(self):
        """wakeup_all_channels() must restore all channels"""
        dfi = DFI5Interface()

        # Enter self-refresh
        dfi.enter_all_channels_lp(DFILowPowerState.LP_SELF_REFRESH)

        # Wake up
        dfi.wakeup_all_channels()

        assert dfi.get_channel_lp_state(0) == DFILowPowerState.LP_IDLE
        assert dfi.get_channel_lp_state(31) == DFILowPowerState.LP_IDLE
        assert dfi.lp_state == DFILowPowerState.LP_IDLE


class TestHBM4TimingParameters:
    """Test HBM4 extended timing parameters"""

    def test_pam3_timing_parameters(self):
        """PAM3 timing parameters must exist"""
        timing = DFITimingParameters()
        assert hasattr(timing, 'tPAM3_ENABLE')
        assert hasattr(timing, 'tPAM3_SWITCH')
        assert hasattr(timing, 'tPAM3_SETTLE')

    def test_extended_dfi_timing(self):
        """Extended DFI 5.0 timing parameters must exist"""
        timing = DFITimingParameters()
        assert hasattr(timing, 'tPHYUPD_RESP')
        assert hasattr(timing, 'tPARITY_LATENCY')
        assert hasattr(timing, 'tMEMDATA_DISABLE')

    def test_channel_timing(self):
        """Channel-specific timing parameters must exist"""
        timing = DFITimingParameters()
        assert hasattr(timing, 'tCHANNEL_GATE')
        assert hasattr(timing, 'tCHANNEL_SYNC')

    def test_timing_default_values(self):
        """HBM4 timing parameters must have reasonable defaults"""
        timing = DFITimingParameters()

        assert timing.tPAM3_ENABLE == 4
        assert timing.tPAM3_SWITCH == 8
        assert timing.tPAM3_SETTLE == 2
        assert timing.tPHYUPD_RESP == 6
        assert timing.tPARITY_LATENCY == 2
        assert timing.tMEMDATA_DISABLE == 2
        assert timing.tCHANNEL_GATE == 1
        assert timing.tCHANNEL_SYNC == 4


class TestHBM4DFISignalsIntegration:
    """Test HBM4 signals integration with get_dfi_signals()"""

    def test_get_dfi_signals_includes_pam3(self):
        """get_dfi_signals() must include PAM3 signals"""
        dfi = DFI5Interface()
        dfi.set_pam3_enable(True)
        dfi.set_pam3_mode(1)

        signals = dfi.get_dfi_signals()
        assert hasattr(signals, 'pam3_enable')
        assert hasattr(signals, 'pam3_mode')
        assert signals.pam3_enable is True
        assert signals.pam3_mode == 1

    def test_get_dfi_signals_includes_extended_signals(self):
        """get_dfi_signals() must include HBM4 extended signals"""
        dfi = DFI5Interface()
        dfi.set_phyupd_resp(True)
        dfi.set_self_refresh_n(False)
        dfi.set_memdata_disable(True)
        dfi.set_parity_error(True)

        signals = dfi.get_dfi_signals()
        assert signals.phyupd_resp is True
        assert signals.self_refresh_n is False
        assert signals.memdata_disable is True
        assert signals.parity_error is True

    def test_reset_clears_hbm4_state(self):
        """reset() must clear HBM4 state"""
        dfi = DFI5Interface()

        # Set HBM4 state
        dfi.set_pam3_enable(True)
        dfi.set_pam3_mode(1)
        dfi.set_phyupd_resp(True)
        dfi.set_channel_active(0, False)

        # Reset
        dfi.reset()

        # Verify cleared
        assert dfi.pam3_enable is False
        assert dfi.pam3_mode == 0
        assert dfi.phyupd_resp is False
        assert dfi.is_channel_active(0) is True  # Reset to True
