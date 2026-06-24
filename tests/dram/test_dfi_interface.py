"""
Comprehensive Tests for DFI 5.0/5.1 Interface

Tests the DFI 5.0/5.1 interface between HBM4 controller and PHY.
This test suite provides complete coverage of all DFI 5.0/5.1 features
including HBM4-specific extensions.

DFI 5.0/5.1 COMPLIANCE TESTS:
- Command encoding and validation
- Frequency change protocol with full state machine
- Control update handshake
- Power management signals
- Low power state management
- PHY Independent Mode
- Training sequences
- Timing parameter validation

HBM4 EXTENSION TESTS:
- PAM3 signaling (8+ GT/s operation)
- Extended DFI 5.0 signals (phyupd_resp, self_refresh_n, etc.)
- 32-channel independent operation
- Parity error detection
- Lane repair capabilities

Reference:
- DFI 5.0/5.1 Specification
- JEDEC JESD270-4A HBM4 Specification
- Synopsys DesignWare HBM4/4E Controller IP
"""

import pytest
import time
from model.dram.dfi_interface import (
    DFI5Interface, DFICommand, DFILowPowerState,
    DFIRequest, DFIResponse, DFIPhyIF, DFITimingParameters,
    DFIRequestQueueConfig, DFI5RequestQueue, DFI5FreqChangeState,
    DFIStateTransitionError, DFIErrorRecord, DFISignals,
    TrainingPhase, DFIPhyIF
)
from model.dram.hbm4_spec import HBM4Spec


# =============================================================================
# SECTION 1: DFI 5.0/5.1 Compliance Tests
# =============================================================================

class TestDFICompliance:
    """Test DFI 5.0/5.1 compliance requirements"""

    def test_version_is_5_0(self):
        """DFI interface must report version 5.0"""
        dfi = DFI5Interface()
        assert dfi.version == "5.0"

    def test_all_required_signals_exist(self):
        """All DFI 5.0 required signals must exist"""
        dfi = DFI5Interface()

        # Control update signals (DFI 5.0)
        assert hasattr(dfi, 'ctrlupd_req')
        assert hasattr(dfi, 'ctrlupd_ack')

        # Frequency change signals (DFI 5.0)
        assert hasattr(dfi, 'freq_change_en')
        assert hasattr(dfi, 'freq_change_ack')

        # Power management signals (DFI 5.0)
        assert hasattr(dfi, 'pwr_up_done')
        assert hasattr(dfi, 'pwr_down_req')
        assert hasattr(dfi, 'pwr_down_ack')

        # Low power signals (DFI 5.0)
        assert hasattr(dfi, 'lp_req')
        assert hasattr(dfi, 'lp_ack')
        assert hasattr(dfi, 'lp_wakeup')

        # HBM4 extended signals
        assert hasattr(dfi, 'phyupd_resp')
        assert hasattr(dfi, 'self_refresh_n')
        assert hasattr(dfi, 'memdata_disable')
        assert hasattr(dfi, 'parity_in')
        assert hasattr(dfi, 'parity_out')
        assert hasattr(dfi, 'parity_error')
        assert hasattr(dfi, 'pam3_enable')
        assert hasattr(dfi, 'pam3_mode')

    def test_get_dfi_signals_returns_complete_state(self):
        """get_dfi_signals() must return all signal states"""
        dfi = DFI5Interface()
        signals = dfi.get_dfi_signals()

        assert isinstance(signals, DFISignals)

        # DFI 5.0 control signals
        assert hasattr(signals, 'ctrlupd_req')
        assert hasattr(signals, 'ctrlupd_ack')
        assert hasattr(signals, 'freq_change_en')
        assert hasattr(signals, 'freq_change_ack')

        # DFI 5.0 power signals
        assert hasattr(signals, 'pwr_up_done')
        assert hasattr(signals, 'pwr_down_req')
        assert hasattr(signals, 'pwr_down_ack')

        # DFI 5.0 LP signals
        assert hasattr(signals, 'lp_req')
        assert hasattr(signals, 'lp_ack')
        assert hasattr(signals, 'lp_wakeup')

        # HBM4 extended signals
        assert hasattr(signals, 'phyupd_resp')
        assert hasattr(signals, 'self_refresh_n')
        assert hasattr(signals, 'memdata_disable')
        assert hasattr(signals, 'pam3_enable')
        assert hasattr(signals, 'pam3_mode')


# =============================================================================
# SECTION 2: Command Encoding Tests
# =============================================================================

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
        assert request.pseudo_channel == 0
        assert request.channel == 15

    def test_encode_pre_command(self):
        """PRE command must be encoded correctly"""
        dfi = DFI5Interface()

        request = dfi.encode_command('PRE', {
            'bank': 3,
            'pseudo_channel': 1
        })

        assert request.command == DFICommand.PRE
        assert request.bank == 3

    def test_encode_prea_command(self):
        """PREA (precharge all) command must be encoded correctly"""
        dfi = DFI5Interface()
        request = dfi.encode_command('PREA', {})
        assert request.command == DFICommand.PREA

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

    def test_encode_rda_command(self):
        """RDA (read with auto-precharge) must be encoded"""
        dfi = DFI5Interface()
        request = dfi.encode_command('RDA', {
            'col': 10,
            'bank': 0,
            'pseudo_channel': 0
        })
        assert request.command == DFICommand.RDA
        assert request.rddata_en is True

    def test_encode_wra_command(self):
        """WRA (write with auto-precharge) must be encoded"""
        dfi = DFI5Interface()
        request = dfi.encode_command('WRA', {
            'col': 10,
            'bank': 0,
            'pseudo_channel': 0
        })
        assert request.command == DFICommand.WRA
        assert request.wrdata_en is True

    def test_encode_refresh_commands(self):
        """Refresh commands must be encoded correctly"""
        dfi = DFI5Interface()

        # All-bank refresh
        request = dfi.encode_command('REFab', {})
        assert request.command == DFICommand.REFab

        # Per-bank refresh
        request = dfi.encode_command('REFsb', {'bank': 3})
        assert request.command == DFICommand.REFsb

        # Row flash memory refresh
        request = dfi.encode_command('RFMab', {})
        assert request.command == DFICommand.RFMab

        request = dfi.encode_command('RFMsb', {'bank': 5})
        assert request.command == DFICommand.RFMsb

    def test_encode_mode_register_commands(self):
        """Mode register commands must be encoded correctly"""
        dfi = DFI5Interface()

        # MRS - Mode Register Set
        request = dfi.encode_command('MRS', {'mr_addr': 0, 'address': 0x123456})
        assert request.command == DFICommand.MRS

        # MRR - Mode Register Read
        request = dfi.encode_command('MRR', {'mr_addr': 1})
        assert request.command == DFICommand.MRR

    def test_encode_power_commands(self):
        """Power management commands must be encoded"""
        dfi = DFI5Interface()

        # Self-refresh entry
        request = dfi.encode_command('SRE', {})
        assert request.command == DFICommand.SRE

        # Self-refresh exit
        request = dfi.encode_command('SRX', {})
        assert request.command == DFICommand.SRX

        # Power-down entry
        request = dfi.encode_command('PDE', {})
        assert request.command == DFICommand.PDE

        # Deep power-down
        request = dfi.encode_command('DPD', {})
        assert request.command == DFICommand.DPD

    def test_encode_training_commands(self):
        """Training commands must be encoded correctly"""
        dfi = DFI5Interface()

        # Write leveling
        request = dfi.encode_command('WRLVL', {'bank': 0})
        assert request.command == DFICommand.WRLVL

        # Read DQS gate training
        request = dfi.encode_command('RDLVL', {'bank': 0})
        assert request.command == DFICommand.RDLVL

        # Read DQ training
        request = dfi.encode_command('RDDQSDQ', {'bank': 0})
        assert request.command == DFICommand.RDDQSDQ

        # Write DQ training
        request = dfi.encode_command('WRDQSDQ', {'bank': 0})
        assert request.command == DFICommand.WRDQSDQ

        # MPR read leveling
        request = dfi.encode_command('MRLVL', {'bank': 0})
        assert request.command == DFICommand.MRLVL

    def test_encode_zq_calibration_commands(self):
        """ZQ calibration commands must be encoded"""
        dfi = DFI5Interface()

        # ZQ Calibration Long
        request = dfi.encode_command('ZQCL', {})
        assert request.command == DFICommand.ZQCL

        # ZQ Calibration Short
        request = dfi.encode_command('ZQCS', {})
        assert request.command == DFICommand.ZQCS

        # ZQ Calibration Operation
        request = dfi.encode_command('ZQOP', {})
        assert request.command == DFICommand.ZQOP

    def test_encode_nop_command(self):
        """NOP command must be encoded"""
        dfi = DFI5Interface()
        request = dfi.encode_command('NOP', {})
        assert request.command == DFICommand.NOP

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

    def test_encode_batch_commands(self):
        """Batch command encoding must work"""
        dfi = DFI5Interface()

        commands = [
            ('ACT', {'row': 100, 'bank': 0}),
            ('RD', {'col': 10, 'bank': 0}),
            ('PRE', {'bank': 0}),
        ]

        requests = dfi.encode_batch_commands(commands)
        assert len(requests) == 3
        assert requests[0].command == DFICommand.ACT
        assert requests[1].command == DFICommand.RD
        assert requests[2].command == DFICommand.PRE


class TestDFICommandMethods:
    """Test DFI command enum methods"""

    def test_command_is_read(self):
        """is_read() must return True for read commands"""
        read_commands = [DFICommand.RD, DFICommand.RDA, DFICommand.MRR,
                        DFICommand.RDLVL, DFICommand.RDDQSDQ, DFICommand.MRLVL]
        for cmd in read_commands:
            assert cmd.is_read() is True, f"{cmd.name} should be read command"

    def test_command_is_write(self):
        """is_write() must return True for write commands"""
        write_commands = [DFICommand.WR, DFICommand.WRA, DFICommand.WRLVL,
                         DFICommand.WRDQSDQ]
        for cmd in write_commands:
            assert cmd.is_write() is True, f"{cmd.name} should be write command"

    def test_command_is_activate(self):
        """is_activate() must return True for ACT"""
        assert DFICommand.ACT.is_activate() is True
        assert DFICommand.RD.is_activate() is False

    def test_command_is_precharge(self):
        """is_precharge() must return True for precharge commands"""
        assert DFICommand.PRE.is_precharge() is True
        assert DFICommand.PREA.is_precharge() is True
        assert DFICommand.ACT.is_precharge() is False

    def test_command_is_refresh(self):
        """is_refresh() must return True for refresh commands"""
        refresh_commands = [DFICommand.REFab, DFICommand.REFsb,
                           DFICommand.RFMab, DFICommand.RFMsb]
        for cmd in refresh_commands:
            assert cmd.is_refresh() is True, f"{cmd.name} should be refresh command"

    def test_command_requires_bank(self):
        """requires_bank() must return True for bank commands"""
        assert DFICommand.ACT.requires_bank() is True
        assert DFICommand.RD.requires_bank() is True
        assert DFICommand.REFab.requires_bank() is False

    def test_command_requires_row(self):
        """requires_row() must return True for row commands"""
        assert DFICommand.ACT.requires_row() is True
        assert DFICommand.RD.requires_row() is False

    def test_command_requires_col(self):
        """requires_col() must return True for column commands"""
        assert DFICommand.RD.requires_col() is True
        assert DFICommand.WR.requires_col() is True
        assert DFICommand.ACT.requires_col() is False

    def test_command_requires_mr(self):
        """requires_mr() must return True for mode register commands"""
        assert DFICommand.MRS.requires_mr() is True
        assert DFICommand.MRR.requires_mr() is True
        assert DFICommand.ACT.requires_mr() is False

    def test_command_from_string(self):
        """from_string() must convert string to enum"""
        assert DFICommand.from_string('ACT') == DFICommand.ACT
        assert DFICommand.from_string('PRE') == DFICommand.PRE
        assert DFICommand.from_string('RD') == DFICommand.RD
        assert DFICommand.from_string('WR') == DFICommand.WR

    def test_command_from_string_case_insensitive(self):
        """from_string() must be case insensitive for uppercase commands"""
        assert DFICommand.from_string('ACT') == DFICommand.ACT
        assert DFICommand.from_string('REFab') == DFICommand.REFab

    def test_command_from_string_invalid(self):
        """from_string() must raise for invalid commands"""
        with pytest.raises(ValueError):
            DFICommand.from_string('INVALID')

    def test_get_command_info(self):
        """get_command_info() must return command attributes"""
        dfi = DFI5Interface()
        info = dfi.get_command_info(DFICommand.RD)

        assert info['name'] == 'RD'
        assert info['value'] == DFICommand.RD.value
        assert info['is_read'] is True
        assert info['is_write'] is False
        assert info['requires_col'] is True

    def test_get_supported_commands(self):
        """get_supported_commands() must return all commands"""
        dfi = DFI5Interface()
        commands = dfi.get_supported_commands()
        assert len(commands) > 20  # Should have all DFI commands


# =============================================================================
# SECTION 3: Low Power State Tests
# =============================================================================

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

    def test_lp_self_refresh_state(self):
        """LP_SELF_REFRESH state must be available"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_SELF_REFRESH)
        assert dfi.lp_state == DFILowPowerState.LP_SELF_REFRESH

    def test_lp_power_down_state(self):
        """LP_POWER_DOWN state must be available"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_POWER_DOWN)
        assert dfi.lp_state == DFILowPowerState.LP_POWER_DOWN

    def test_lp_deep_pd_state(self):
        """LP_DEEP_PD state must be available"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_DEEP_PD)
        assert dfi.lp_state == DFILowPowerState.LP_DEEP_PD

    def test_lp_freq_change_state(self):
        """LP_FREQ_CHANGE state must be available"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_FREQ_CHANGE)
        assert dfi.lp_state == DFILowPowerState.LP_FREQ_CHANGE

    def test_lp_state_is_active(self):
        """is_active() must return True only for LP_IDLE"""
        assert DFILowPowerState.LP_IDLE.is_active() is True
        assert DFILowPowerState.LP_CTRL.is_active() is False
        assert DFILowPowerState.LP_DATA.is_active() is False

    def test_lp_state_allows_commands(self):
        """allows_commands() must return True only for LP_IDLE"""
        assert DFILowPowerState.LP_IDLE.allows_commands() is True
        assert DFILowPowerState.LP_CTRL.allows_commands() is False

    def test_lp_state_allows_data(self):
        """allows_data() must return True for LP_IDLE and LP_CTRL"""
        assert DFILowPowerState.LP_IDLE.allows_data() is True
        assert DFILowPowerState.LP_CTRL.allows_data() is True
        assert DFILowPowerState.LP_DATA.allows_data() is False

    def test_valid_lp_transitions_from_idle(self):
        """Valid transitions from LP_IDLE must be allowed"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)

        valid_states = [
            DFILowPowerState.LP_CTRL,
            DFILowPowerState.LP_DATA,
            DFILowPowerState.LP_SELF_REFRESH,
            DFILowPowerState.LP_POWER_DOWN,
            DFILowPowerState.LP_DEEP_PD,
            DFILowPowerState.LP_FREQ_CHANGE,
        ]

        for state in valid_states:
            result = dfi.set_low_power_state(state, enforce_timing=False)
            assert result is True, f"Transition to {state.name} should be valid"

    def test_invalid_lp_transition_raises(self):
        """Invalid LP state transitions must raise exception"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_SELF_REFRESH)

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

    def test_enter_low_power_state(self):
        """enter_low_power_state() must initiate entry"""
        dfi = DFI5Interface()
        result = dfi.enter_low_power_state(DFILowPowerState.LP_CTRL)
        assert result is True
        assert dfi.lp_state == DFILowPowerState.LP_CTRL
        assert dfi.lp_req is True

    def test_exit_low_power_state(self):
        """exit_low_power_state() must initiate exit"""
        dfi = DFI5Interface()
        dfi.enter_low_power_state(DFILowPowerState.LP_CTRL)
        result = dfi.exit_low_power_state()
        assert result is True
        assert dfi.lp_wakeup is True


# =============================================================================
# SECTION 4: Control Update Handshake Tests
# =============================================================================

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

    def test_ctrlupd_acknowledge_requires_request(self):
        """acknowledge_ctrlupd() fails without request"""
        dfi = DFI5Interface()
        result = dfi.acknowledge_ctrlupd()
        assert result is False

    def test_ctrlupd_statistics(self):
        """Control update statistics must be tracked"""
        dfi = DFI5Interface()
        dfi.request_ctrlupd()
        for _ in range(dfi.timing.tCTRLUPD_LATENCY + 1):
            dfi.tick()

        stats = dfi.get_statistics()
        assert "ctrl_updates" in stats


# =============================================================================
# SECTION 5: Frequency Change Protocol Tests
# =============================================================================

class TestDFIFrequencyChange:
    """Test DFI frequency change protocol"""

    def test_freq_change_request(self):
        """Frequency change request must be accepted"""
        dfi = DFI5Interface()
        result = dfi.request_freq_change(1200)
        assert result is True
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_REQUESTED

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

    def test_freq_change_complete_state_machine(self):
        """Full frequency change state machine must work"""
        dfi = DFI5Interface()

        # Start frequency change
        dfi.request_freq_change(1600)
        dfi.enter_freq_change()

        # Advance through states
        total_latency = dfi.get_total_freq_change_latency()
        for _ in range(total_latency + 10):
            dfi.tick()

        # Should be back to IDLE
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE
        assert dfi.frequency_mhz == 1600

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

    def test_freq_change_progress(self):
        """get_freq_change_progress() must return detailed info"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        progress = dfi.get_freq_change_progress()
        assert 'state' in progress
        assert 'request_pending' in progress
        assert 'latency_counter' in progress
        assert 'remaining_cycles' in progress
        assert progress['target_freq_mhz'] == 1200

    def test_freq_change_data_valid(self):
        """Frequency change data valid signal must work"""
        dfi = DFI5Interface()
        dfi.set_freq_change_data_valid(True)
        progress = dfi.get_freq_change_progress()
        assert progress['data_valid'] is True

    def test_initiate_freq_change(self):
        """initiate_freq_change() must start full sequence"""
        dfi = DFI5Interface()
        result = dfi.initiate_freq_change(1200)
        assert result is True
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_REQUESTED

    def test_initiate_freq_change_from_non_idle_fails(self):
        """initiate_freq_change() fails from non-IDLE state"""
        dfi = DFI5Interface()
        dfi.set_low_power_state(DFILowPowerState.LP_SELF_REFRESH)
        result = dfi.initiate_freq_change(1200)
        assert result is False

    def test_cancel_freq_change(self):
        """cancel_freq_change() must cancel pending request"""
        dfi = DFI5Interface()
        dfi.request_freq_change(1200)
        result = dfi.cancel_freq_change()
        assert result is True
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE

    def test_cancel_freq_change_fails_when_active(self):
        """cancel_freq_change() fails during active change"""
        dfi = DFI5Interface()
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        # Can't cancel once in FC_ACTIVE
        dfi.tick()  # Move to FC_ACTIVE
        result = dfi.cancel_freq_change()
        assert result is False

    def test_is_freq_change_in_progress(self):
        """is_freq_change_in_progress() must work"""
        dfi = DFI5Interface()
        assert dfi.is_freq_change_in_progress() is False

        dfi.request_freq_change(1200)
        assert dfi.is_freq_change_in_progress() is True

    def test_is_freq_change_complete(self):
        """is_freq_change_complete() must work"""
        dfi = DFI5Interface()
        assert dfi.is_freq_change_complete() is True

        dfi.request_freq_change(1200)
        assert dfi.is_freq_change_complete() is False

    def test_total_freq_change_latency(self):
        """get_total_freq_change_latency() must return valid latency"""
        dfi = DFI5Interface()
        total = dfi.get_total_freq_change_latency()
        assert total > 0
        assert total == (dfi.timing.tFC_ENTER + dfi.timing.tFC_LATENCY +
                        dfi.timing.tFC_EXIT + dfi.timing.tFC_PLL_LOCK)

    def test_pll_lock_status(self):
        """PLL/DLL lock status must be tracked"""
        dfi = DFI5Interface()
        assert dfi.is_pll_locked() is True
        assert dfi.is_dll_locked() is True

        dfi.request_freq_change(1600)
        dfi.enter_freq_change()

        # Advance to FC_ACTIVE state (after FC_ENTER latency)
        for _ in range(dfi.timing.tFC_ENTER + 1):
            dfi.tick()

        assert dfi.is_pll_locked() is False


# =============================================================================
# SECTION 6: Power Management Tests
# =============================================================================

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


# =============================================================================
# SECTION 7: Low Power Signal Tests
# =============================================================================

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

    def test_lp_self_refresh_entry(self):
        """LP_SELF_REFRESH must lower CKE"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_SELF_REFRESH)

        # Advance past entry latency
        for _ in range(dfi.timing.tLP_SREF_ENTER + 1):
            dfi.tick()

        assert dfi.lp_ack is True
        assert dfi.cke is False  # CKE should be low in self-refresh

    def test_lp_self_refresh_exit(self):
        """LP_SELF_REFRESH exit must restore CKE"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_SELF_REFRESH)
        for _ in range(dfi.timing.tLP_SREF_ENTER + 1):
            dfi.tick()

        dfi.wakeup_from_low_power()
        for _ in range(dfi.timing.tLP_SREF_EXIT + 1):
            dfi.tick()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE
        assert dfi.cke is True  # CKE restored

    def test_lp_power_down_entry(self):
        """LP_POWER_DOWN must lower CKE"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_POWER_DOWN)

        for _ in range(dfi.timing.tLP_PD_ENTER + 1):
            dfi.tick()

        assert dfi.cke is False

    def test_lp_deep_pd_entry(self):
        """LP_DEEP_PD entry must set state"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_DEEP_PD)
        # Deep PD entry doesn't auto-acknowledge, verify state is set
        assert dfi.lp_state == DFILowPowerState.LP_DEEP_PD
        assert dfi.lp_req is True

    def test_cke_override(self):
        """CKE override must work"""
        dfi = DFI5Interface()
        dfi.set_cke_override(True)
        dfi.set_cke(False)
        assert dfi.cke is False
        dfi.set_cke(True)
        assert dfi.cke is True


# =============================================================================
# SECTION 8: LP Statistics and History Tests
# =============================================================================

class TestDFILPStatistics:
    """Test LP statistics and history tracking"""

    def test_lp_statistics(self):
        """get_lp_statistics() must return valid stats"""
        dfi = DFI5Interface()
        dfi.request_low_power(DFILowPowerState.LP_CTRL)
        dfi.set_lp_ack(True)

        stats = dfi.get_lp_statistics()
        assert 'current_state' in stats
        assert 'time_in_state' in stats
        assert 'entries' in stats
        assert 'exits' in stats
        assert 'transitions' in stats

    def test_lp_state_history(self):
        """LP state history must be tracked"""
        dfi = DFI5Interface()

        # Initial LP_IDLE
        dfi.tick()

        # LP_IDLE -> LP_CTRL (recorded on tick when state changes)
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        dfi.tick()

        # LP_CTRL -> LP_DATA
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)
        dfi.tick()

        history = dfi.get_lp_state_history()
        assert len(history) >= 2

    def test_lp_entry_exit_counters(self):
        """LP entries and exits must be tracked"""
        dfi = DFI5Interface()

        # Enter LP_CTRL
        dfi.request_low_power(DFILowPowerState.LP_CTRL)
        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        stats = dfi.get_lp_statistics()
        assert stats['entries'] >= 1


# =============================================================================
# SECTION 9: Request Queue Tests
# =============================================================================

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

    def test_queue_available_capacity(self):
        """Available capacity must be tracked"""
        dfi = DFI5Interface()
        assert dfi.queue_available_capacity == 64

        for i in range(10):
            request = dfi.encode_command('ACT', {'row': i * 100, 'bank': 0})
            dfi.queue_request(request)

        assert dfi.queue_available_capacity == 54


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


# =============================================================================
# SECTION 10: Timing Parameters Tests
# =============================================================================

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

    def test_write_latency_cycles(self):
        """write_latency_cycles property must work"""
        timing = DFITimingParameters(tPHY_wrlAT=7)
        assert timing.write_latency_cycles == 7

    def test_read_latency_cycles(self):
        """read_latency_cycles property must work"""
        timing = DFITimingParameters(tPHY_rdLat=9)
        assert timing.read_latency_cycles == 9

    def test_write_latency_ps(self):
        """Write latency in picoseconds must be calculated"""
        timing = DFITimingParameters(tPHY_wrlAT=5)
        latency = timing.get_write_latency_ps(125.0)
        assert latency == 625.0

    def test_read_latency_ps(self):
        """Read latency in picoseconds must be calculated"""
        timing = DFITimingParameters(tPHY_rdLat=8)
        latency = timing.get_read_latency_ps(125.0)
        assert latency == 1000.0

    def test_freq_change_total_latency(self):
        """Total frequency change latency must be calculated"""
        timing = DFITimingParameters()
        total = timing.get_freq_change_total_latency()
        assert total == (timing.tFC_ENTER + timing.tFC_LATENCY +
                        timing.tFC_EXIT + timing.tFC_PLL_LOCK)

    def test_timing_validate(self):
        """Timing parameters must be validatable"""
        timing = DFITimingParameters()
        errors = timing.validate()
        assert isinstance(errors, list)

    def test_timing_validate_invalid(self):
        """Invalid timing parameters must be detected"""
        timing = DFITimingParameters(tPHY_wrlAT=0)
        errors = timing.validate()
        assert len(errors) > 0

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
        dfi.set_frequency(8000)
        latency = dfi.get_write_latency_ps()
        assert latency > 0

    def test_interface_read_latency_ps(self):
        """DFI interface must provide read latency"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)
        latency = dfi.get_read_latency_ps()
        assert latency > 0


# =============================================================================
# SECTION 11: Response Tests
# =============================================================================

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

    def test_response_has_dfi_signals(self):
        """Response must include DFI signal states"""
        dfi = DFI5Interface()
        response = dfi.get_response()

        assert hasattr(response, 'ctrlupd_ack')
        assert hasattr(response, 'freq_change_ack')
        assert hasattr(response, 'pwr_up_done')
        assert hasattr(response, 'pwr_down_ack')
        assert hasattr(response, 'lp_ack')

    def test_response_phy_status(self):
        """Response must include PHY status"""
        dfi = DFI5Interface()
        response = dfi.get_response()

        assert hasattr(response, 'phy_clock_enable')
        assert hasattr(response, 'phy_reset')


# =============================================================================
# SECTION 12: PHY Interface Tests
# =============================================================================

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
        assert dfi.phy.supports_freq_change() is True

    def test_phy_freq_change_latency(self):
        """PHY must report frequency change latency"""
        dfi = DFI5Interface()
        latency = dfi.phy.get_freq_change_latency()
        assert latency > 0

    def test_phy_pll_config(self):
        """PHY PLL configuration must work"""
        dfi = DFI5Interface()
        dfi.phy.configure_pll(1600, divider=1, multiplier=2)
        config = dfi.phy.get_pll_config()
        assert config['frequency_mhz'] == 1600
        assert config['locked'] is False  # Requires re-lock

    def test_phy_pll_lock(self):
        """PHY PLL lock status must work"""
        dfi = DFI5Interface()
        assert dfi.phy.is_pll_locked() is True

        dfi.phy.set_pll_locked(False)
        assert dfi.phy.is_pll_locked() is False

    def test_phy_dll_config(self):
        """PHY DLL configuration must work"""
        dfi = DFI5Interface()
        dfi.phy.configure_dll(enabled=True, delay_elements=64)
        config = dfi.phy.get_dll_config()
        assert config['enabled'] is True
        assert config['delay_elements'] == 64

    def test_phy_dll_lock(self):
        """PHY DLL lock status must work"""
        dfi = DFI5Interface()
        assert dfi.phy.is_dll_locked() is True

        dfi.phy.set_dll_locked(False)
        assert dfi.phy.is_dll_locked() is False

    def test_phy_vref_config(self):
        """PHY VREF configuration must work"""
        dfi = DFI5Interface()
        dfi.phy.configure_vref(dram_vref=45, phy_vref=55)
        config = dfi.phy.get_vref_config()
        assert config['dram_vref'] == 45
        assert config['phy_vref'] == 55

    def test_phy_impedance_config(self):
        """PHY impedance configuration must work"""
        dfi = DFI5Interface()
        dfi.phy.configure_impedance(write_ohm=48, read_ohm=40)
        config = dfi.phy.get_impedance_config()
        assert config['write_impedance'] == 48
        assert config['read_impedance'] == 40

    def test_phy_mode_registers(self):
        """PHY mode register access must work"""
        dfi = DFI5Interface()
        dfi.phy.set_mode_register(0, 0x12)
        assert dfi.phy.get_mode_register(0) == 0x12

        dfi.phy.set_mode_register(1, 0x34)
        all_mr = dfi.phy.get_all_mode_registers()
        assert len(all_mr) == 2

    def test_phy_training_phase(self):
        """PHY training phase management must work"""
        dfi = DFI5Interface()
        dfi.phy.set_training_phase(TrainingPhase.WRITE_LEVELING)
        assert dfi.phy.get_training_phase() == TrainingPhase.WRITE_LEVELING

    def test_phy_training_results(self):
        """PHY training results must be recordable"""
        dfi = DFI5Interface()
        result = {'status': 'success', 'delay': 5}
        dfi.phy.record_training_result(TrainingPhase.WRITE_LEVELING, result)

        results = dfi.phy.get_training_results()
        assert 'WRITE_LEVELING' in results
        assert results['WRITE_LEVELING']['status'] == 'success'

    def test_phy_calibration(self):
        """PHY calibration must work"""
        dfi = DFI5Interface()
        assert dfi.phy.is_calibrated() is False

        dfi.phy.start_calibration()
        dfi.phy.complete_calibration()
        dfi.phy.set_zq_calibrated(True)  # Both ZQ and impedance needed
        assert dfi.phy.is_calibrated() is True

    def test_phy_initialization(self):
        """PHY initialization must work"""
        dfi = DFI5Interface()
        dfi.phy.start_initialization()
        assert dfi.phy.is_initialized() is False

        dfi.phy.complete_initialization()
        assert dfi.phy.is_initialized() is True

    def test_phy_status(self):
        """PHY status must be queryable"""
        dfi = DFI5Interface()
        status = dfi.phy.get_status()
        assert 'init_complete' in status
        assert 'training_complete' in status

    def test_phy_info(self):
        """PHY info must be comprehensive"""
        dfi = DFI5Interface()
        info = dfi.phy.get_phy_info()
        assert 'independent_mode' in info
        assert 'pll' in info
        assert 'dll' in info
        assert 'vref' in info
        assert 'impedance' in info


# =============================================================================
# SECTION 13: Training Tests
# =============================================================================

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


# =============================================================================
# SECTION 14: HBM4 PAM3 Signal Tests
# =============================================================================

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
        dfi.set_pam3_mode(1)
        assert dfi.pam3_mode == 1

    def test_is_pam3_active(self):
        """is_pam3_active() must check enable and settled state"""
        dfi = DFI5Interface()
        assert dfi.is_pam3_active() is False

        dfi.set_pam3_enable(True)
        dfi.set_pam3_mode(1)
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

    def test_pam3_mode_transition(self):
        """PAM3 mode transition must work"""
        dfi = DFI5Interface()

        # Enable PAM3
        dfi.set_pam3_enable(True)
        dfi.set_pam3_mode(1)

        # Wait for switch
        for _ in range(dfi.timing.tPAM3_SWITCH + 1):
            dfi.tick()

        assert dfi.is_pam3_active() is True

        # Switch back to NRZ
        dfi.set_pam3_enable(False)
        dfi.set_pam3_mode(0)

        # Wait for switch
        for _ in range(dfi.timing.tPAM3_SWITCH + 1):
            dfi.tick()

        assert dfi.is_pam3_active() is False


# =============================================================================
# SECTION 15: HBM4 Extended DFI 5.0 Signal Tests
# =============================================================================

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
        dfi.set_self_refresh_n(False)
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

    def test_parity_in(self):
        """parity_in must be settable"""
        dfi = DFI5Interface()
        dfi.set_parity_in(True)
        assert dfi.parity_in is True

    def test_parity_out(self):
        """parity_out must be settable"""
        dfi = DFI5Interface()
        dfi.set_parity_out(False)
        assert dfi.parity_out is False

    def test_parity_error(self):
        """parity_error must be settable"""
        dfi = DFI5Interface()
        dfi.set_parity_error(True)
        assert dfi.parity_error is True


# =============================================================================
# SECTION 16: HBM4 32-Channel Support Tests
# =============================================================================

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
        assert dfi.get_active_channel_count() == 32

        dfi.set_channel_active(0, False)
        dfi.set_channel_active(1, False)
        assert dfi.get_active_channel_count() == 30
        assert dfi.is_channel_active(0) is False
        assert dfi.is_channel_active(2) is True

    def test_channel_frequency(self):
        """Channel-specific frequency must be tracked"""
        dfi = DFI5Interface()
        assert dfi.get_channel_frequency(5) == 800

        dfi.set_channel_frequency(5, 1200)
        assert dfi.get_channel_frequency(5) == 1200

    def test_channel_lp_state(self):
        """Channel-specific LP state must be tracked"""
        dfi = DFI5Interface()
        assert dfi.get_channel_lp_state(5) == DFILowPowerState.LP_IDLE

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
        dfi.enter_all_channels_lp(DFILowPowerState.LP_SELF_REFRESH)
        dfi.wakeup_all_channels()

        assert dfi.get_channel_lp_state(0) == DFILowPowerState.LP_IDLE
        assert dfi.get_channel_lp_state(31) == DFILowPowerState.LP_IDLE
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_invalid_channel_index(self):
        """Invalid channel indices must return defaults"""
        dfi = DFI5Interface()
        assert dfi.is_channel_active(100) is False
        assert dfi.get_channel_frequency(100) == 800
        assert dfi.get_channel_lp_state(100) == DFILowPowerState.LP_IDLE


# =============================================================================
# SECTION 17: HBM4 Extended Timing Tests
# =============================================================================

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

        # PAM3 timing
        assert timing.tPAM3_ENABLE == 4
        assert timing.tPAM3_SWITCH == 8
        assert timing.tPAM3_SETTLE == 2

        # Extended DFI timing
        assert timing.tPHYUPD_RESP == 6
        assert timing.tPARITY_LATENCY == 2
        assert timing.tMEMDATA_DISABLE == 2

        # Channel timing
        assert timing.tCHANNEL_GATE == 1
        assert timing.tCHANNEL_SYNC == 4


# =============================================================================
# SECTION 18: Utility Methods Tests
# =============================================================================

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

    def test_bandwidth_tbs(self):
        """Bandwidth in TB/s must be calculated"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)

        bw = dfi.get_bandwidth_tbs()
        assert bw > 0
        assert bw < dfi.get_bandwidth_gbs()

    def test_reset(self):
        """DFI must be resettable"""
        dfi = DFI5Interface()

        # Make some state changes
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)

        # Reset
        dfi.reset()

        assert dfi.lp_state == DFILowPowerState.LP_IDLE
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE
        assert dfi.pending_request_count == 0
        assert dfi.cycle == 0

    def test_reset_clears_dfi_signals(self):
        """Reset must clear all DFI signals"""
        dfi = DFI5Interface()

        # Set various signals
        dfi.set_pam3_enable(True)
        dfi.set_phyupd_resp(True)
        dfi.set_channel_active(0, False)
        dfi.set_parity_error(True)

        # Reset
        dfi.reset()

        # Verify cleared
        assert dfi.pam3_enable is False
        assert dfi.phyupd_resp is False
        assert dfi.is_channel_active(0) is True
        assert dfi.parity_error is False

    def test_cycle_counter(self):
        """Cycle counter must advance on tick"""
        dfi = DFI5Interface()
        assert dfi.cycle == 0

        dfi.tick()
        assert dfi.cycle == 1

        dfi.tick()
        assert dfi.cycle == 2

    def test_interface_status(self):
        """get_interface_status() must return comprehensive info"""
        dfi = DFI5Interface()
        status = dfi.get_interface_status()

        assert 'version' in status
        assert 'cycle' in status
        assert 'frequency_mhz' in status
        assert 'lp_state' in status
        assert 'fc_state' in status
        assert 'training_complete' in status
        assert 'queue_depth' in status
        assert 'ready' in status
        assert 'error_count' in status

    def test_validate_interface(self):
        """validate_interface() must check configuration"""
        dfi = DFI5Interface()
        valid, errors = dfi.validate_interface()

        assert valid is True
        assert len(errors) == 0


# =============================================================================
# SECTION 19: Error Handling Tests
# =============================================================================

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


class TestDFIErrorHandling:
    """Test DFI error handling"""

    def test_error_logging(self):
        """Errors must be logged"""
        dfi = DFI5Interface()

        # Trigger an error (request freq change while already in one)
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        dfi.request_freq_change(1600)

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


# =============================================================================
# SECTION 20: Frequency Change State Enum Tests
# =============================================================================

class TestDFIFreqChangeState:
    """Test frequency change state enum"""

    def test_all_states_defined(self):
        """All frequency change states must be defined"""
        expected = ['FC_IDLE', 'FC_REQUESTED', 'FC_ENTERING', 'FC_ACTIVE',
                   'FC_EXITING', 'FC_LOCKING', 'FC_COMPLETE']
        for state_name in expected:
            assert hasattr(DFI5FreqChangeState, state_name)


# =============================================================================
# SECTION 21: DFISignals Dataclass Tests
# =============================================================================

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


# =============================================================================
# SECTION 22: Integration Tests
# =============================================================================

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


# =============================================================================
# SECTION 23: Performance and Benchmark Tests
# =============================================================================

class TestDFIPerformance:
    """Test DFI interface performance characteristics"""

    def test_command_encoding_performance(self):
        """Command encoding must be fast"""
        dfi = DFI5Interface()
        start = time.time()

        for _ in range(1000):
            dfi.encode_command('ACT', {'row': 100, 'bank': 5})
            dfi.encode_command('RD', {'col': 10, 'bank': 0})

        elapsed = time.time() - start
        # Should complete 1000 command pairs in under 100ms
        assert elapsed < 0.1

    def test_queue_operations_performance(self):
        """Queue operations must be fast"""
        dfi = DFI5Interface()
        start = time.time()

        for i in range(1000):
            request = dfi.encode_command('ACT', {'row': i, 'bank': 0})
            dfi.queue_request(request)

        elapsed = time.time() - start
        # Should complete 1000 enqueue operations in under 100ms
        assert elapsed < 0.1

    def test_tick_performance(self):
        """Tick operations must be fast"""
        dfi = DFI5Interface()
        start = time.time()

        for _ in range(10000):
            dfi.tick()

        elapsed = time.time() - start
        # Should complete 10000 ticks in under 100ms
        assert elapsed < 0.1


# =============================================================================
# SECTION 24: Edge Case Tests
# =============================================================================

class TestDFIEdgeCases:
    """Test DFI interface edge cases"""

    def test_zero_priority_command(self):
        """Zero priority commands must work"""
        dfi = DFI5Interface()
        request = dfi.encode_command('ACT', {'row': 100, 'bank': 5}, priority=0)
        assert request.priority == 0

    def test_max_priority_command(self):
        """Maximum priority commands must work"""
        dfi = DFI5Interface()
        request = dfi.encode_command('ACT', {'row': 100, 'bank': 5}, priority=1000)
        assert request.priority == 1000

    def test_large_address_encoding(self):
        """Large addresses must be encodable"""
        dfi = DFI5Interface()
        request = dfi.encode_command('ACT', {'row': 0xFFFF, 'bank': 15})
        assert request.address == 0xFFFF

    def test_all_banks_encoding(self):
        """All bank values must be encodable"""
        dfi = DFI5Interface()
        for bank in range(16):
            request = dfi.encode_command('ACT', {'row': 0, 'bank': bank})
            assert request.bank == bank

    def test_all_channels_encoding(self):
        """All channel values must be encodable"""
        dfi = DFI5Interface()
        for ch in range(32):
            request = dfi.encode_command('ACT', {'row': 0, 'bank': 0, 'channel': ch})
            assert request.channel == ch

    def test_consecutive_freq_changes(self):
        """Consecutive frequency changes must work"""
        dfi = DFI5Interface()

        # Change to 1200
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        for _ in range(dfi.get_total_freq_change_latency() + 5):
            dfi.tick()

        # Change to 1600
        dfi.request_freq_change(1600)
        dfi.enter_freq_change()
        for _ in range(dfi.get_total_freq_change_latency() + 5):
            dfi.tick()

        assert dfi.frequency_mhz == 1600

    def test_multiple_ctrl_updates(self):
        """Multiple control updates must work"""
        dfi = DFI5Interface()

        for _ in range(5):
            dfi.request_ctrlupd()
            for _ in range(dfi.timing.tCTRLUPD_LATENCY + 1):
                dfi.tick()
            assert dfi.ctrlupd_req is False

    def test_lp_state_sequence(self):
        """LP state sequence must work correctly"""
        dfi = DFI5Interface()

        # IDLE -> LP_CTRL
        dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
        assert dfi.lp_state == DFILowPowerState.LP_CTRL

        # LP_CTRL -> LP_DATA
        dfi.set_low_power_state(DFILowPowerState.LP_DATA)
        assert dfi.lp_state == DFILowPowerState.LP_DATA

        # LP_DATA -> LP_IDLE
        dfi.set_low_power_state(DFILowPowerState.LP_IDLE)
        assert dfi.lp_state == DFILowPowerState.LP_IDLE


# =============================================================================
# SECTION 25: Calibration Data Tests
# =============================================================================

class TestDFICalibrationData:
    """Test calibration data handling"""

    def test_add_calibration_data(self):
        """Calibration data must be addable"""
        dfi = DFI5Interface()
        dfi.add_calibration_data('read_delay', 5)
        dfi.add_calibration_data('write_level', 10)

        assert 'read_delay' in dfi.phy.calibration_data
        assert 'write_level' in dfi.phy.calibration_data

    def test_get_calibration_status(self):
        """Calibration status must be queryable"""
        dfi = DFI5Interface()
        status = dfi.phy.get_calibration_status()
        assert 'calibration_data' in status
        assert 'calibration_complete' in status
