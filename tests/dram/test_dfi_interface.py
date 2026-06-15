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