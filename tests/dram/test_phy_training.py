"""
Comprehensive Unit Tests for PHY Training State Machine

Tests all PHY initialization and training sequences for HBM4 including:
- Write Leveling (WRLVL)
- Read DQS Training
- Read DQ Training (RDDQ)
- Write DQ Training (WDQ)
- Gate Training
- VREF CA/DQ Training
- PAM3 Training (HBM4E)
- DFI 5.0/5.1 Interface Integration
- Training Sequence Executor
- Training Completion Detector

Reference:
- JEDEC JESD270-4A HBM4 specification
- Cadence HBM4E documentation
- DFI 5.1 specification
"""

import pytest
import sys
import os
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock, patch
from collections import deque

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from model.dram.phy_training import (
    # Enums
    PHYInitState,
    TrainingPhase,
    TrainingResult,
    PAM3Level,
    PAM3TrainingState,
    DFI5LowPowerState,
    # Config classes
    TrainingParameters,
    # Control classes
    DFI5TrainingControl,
    TrainingStatus,
    PHYInitStatus,
    # Signal config
    PAM3SignalConfig,
    PAM3_VREF_DAC_RANGE,
    PAM3_VREF_HIGH_MIN,
    PAM3_VREF_HIGH_MAX,
    PAM3_VREF_LOW_MIN,
    PAM3_VREF_LOW_MAX,
    PAM3_VREF_MID,
    PAM3_UPPER_EYE_MARGIN,
    PAM3_LOWER_EYE_MARGIN,
    PAM3_VERTICAL_EYE_MARGIN,
    PAM3_DFE_NUM_TAPS,
    PAM3_DFE_MAX_TAP_WEIGHT,
    PAM3_DFE_CONVERGENCE_RATE,
    # VREF constants
    VREF_DAC_RANGE,
    VREF_CA_MIN,
    VREF_CA_MAX,
    VREF_DQ_MIN,
    VREF_DQ_MAX,
    # Exceptions
    PHYTrainingError,
    PHYInitError,
    # State machines
    PHYTrainingStateMachine,
    PHYInitializationStateMachine,
    HBM4PHYManager,
)

from model.phy.training_sequences import (
    TrainingSequenceType,
    DFITrainingCommand,
    TrainingSequenceStep,
    TrainingSequenceDefinition,
    DFITrainingControl,
    TrainingCompletionStatus,
    TrainingSequenceExecutor,
    TrainingCompletionDetector,
    QUICK_BOOT_SEQUENCE,
    NORMAL_TRAINING_SEQUENCE,
    EXTENDED_TRAINING_SEQUENCE,
    MARGIN_SCAN_SEQUENCE,
    create_training_sequence,
    get_dfi_training_command,
)


# =============================================================================
# Test Write Leveling (WRLVL)
# =============================================================================

class TestWriteLeveling:
    """Tests for Write Leveling training sequence"""

    def test_write_leveling_initialization(self):
        """Test Write Leveling initialization"""
        sm = PHYTrainingStateMachine(channel_id=0)
        sm.start_training()

        # Check that training has started
        assert sm.status.current_phase == TrainingPhase.TRAIN_START

        # Move through init phases
        for _ in range(10):
            sm.tick()
            sm.process_training_cycle()

        # Should have progressed past IDLE
        assert sm.status.current_phase != TrainingPhase.TRAIN_IDLE

    def test_write_leveling_phase_exists(self):
        """Test TRAIN_WR_LEVELING phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_WR_LEVELING')
        assert TrainingPhase.TRAIN_WR_LEVELING is not None

    def test_write_leveling_encoding(self):
        """Test DFI encoding for Write Leveling"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_WR_LEVELING)

        assert tra_req is True
        assert tra_mode == 1
        assert tra_type == 1

    def test_write_leveling_delay_sweep(self):
        """Test Write Leveling delay sweep"""
        sm = PHYTrainingStateMachine(channel_id=0)

        # Simulate delay sweep
        delays = []
        for delay in range(64):
            margin = sm._measure_wr_level_margin(delay)
            delays.append((delay, margin))

        # Check that we have measurements
        assert len(delays) == 64
        # At least some margins should be reasonable
        valid_margins = [m for d, m in delays if 0 <= m <= 1]
        assert len(valid_margins) == 64

    def test_write_leveling_margin_threshold(self):
        """Test Write Leveling margin threshold"""
        sm = PHYTrainingStateMachine(channel_id=0)

        # Measure margin
        margin = sm._measure_wr_level_margin(32)
        assert 0 <= margin <= 1

    def test_write_leveling_best_delay_selection(self):
        """Test best delay selection for Write Leveling"""
        sm = PHYTrainingStateMachine(channel_id=0)

        best_delay = 0
        best_margin = 0.0

        for delay in range(64):
            margin = sm._measure_wr_level_margin(delay)
            if margin > best_margin:
                best_margin = margin
                best_delay = delay

        assert 0 <= best_delay < 64
        assert 0 <= best_margin <= 1

    def test_write_leveling_in_training_sequence(self):
        """Test Write Leveling is in training sequence"""
        assert TrainingPhase.TRAIN_WR_LEVELING in PHYTrainingStateMachine.TRAINING_SEQUENCE

    def test_write_leveling_dfi_signals(self):
        """Test DFI signals for Write Leveling"""
        ctrl = DFI5TrainingControl()

        # Start Write Leveling
        ctrl.tra_req = True
        ctrl.tra_mode = 1
        ctrl.tra_type = 1

        assert ctrl.tra_req is True
        assert ctrl.tra_mode == 1
        assert ctrl.tra_type == 1


# =============================================================================
# Test Read DQS Training
# =============================================================================

class TestReadDQSTraining:
    """Tests for Read DQS training sequence"""

    def test_read_dqs_phase_exists(self):
        """Test TRAIN_RD_DQS phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_RD_DQS')
        assert TrainingPhase.TRAIN_RD_DQS is not None

    def test_read_dqs_encoding(self):
        """Test DFI encoding for Read DQS"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_RD_DQS)

        assert tra_req is True
        assert tra_mode == 1
        assert tra_type == 0

    def test_read_dqs_delay_sweep(self):
        """Test Read DQS delay sweep"""
        sm = PHYTrainingStateMachine(channel_id=0)

        delays = []
        for delay in range(64):
            margin = sm._measure_rd_dqs_margin(delay)
            delays.append((delay, margin))

        assert len(delays) == 64

    def test_read_dqs_margin_measurement(self):
        """Test Read DQS margin measurement"""
        sm = PHYTrainingStateMachine(channel_id=0)

        margin_32 = sm._measure_rd_dqs_margin(32)
        margin_0 = sm._measure_rd_dqs_margin(0)
        margin_63 = sm._measure_rd_dqs_margin(63)

        assert 0 <= margin_32 <= 1
        assert 0 <= margin_0 <= 1
        assert 0 <= margin_63 <= 1

    def test_read_dqs_in_training_sequence(self):
        """Test Read DQS is in training sequence"""
        assert TrainingPhase.TRAIN_RD_DQS in PHYTrainingStateMachine.TRAINING_SEQUENCE


# =============================================================================
# Test Read DQ Training (RDDQ / Read Data Eye)
# =============================================================================

class TestReadDQTraining:
    """Tests for Read DQ training sequence"""

    def test_read_dq_phase_exists(self):
        """Test TRAIN_RD_DQ phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_RD_DQ')
        assert TrainingPhase.TRAIN_RD_DQ is not None

    def test_read_dq_eye_phase_exists(self):
        """Test TRAIN_RD_DQ_EYE phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_RD_DQ_EYE')
        assert TrainingPhase.TRAIN_RD_DQ_EYE is not None

    def test_read_dq_encoding(self):
        """Test DFI encoding for Read DQ"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_RD_DQ)

        assert tra_req is True
        assert tra_mode == 2
        assert tra_type == 0

    def test_read_dq_eye_encoding(self):
        """Test DFI encoding for Read DQ Eye"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_RD_DQ_EYE)

        assert tra_req is True
        assert tra_mode == 2
        assert tra_type == 1

    def test_read_dq_margin_measurement(self):
        """Test Read DQ margin measurement"""
        sm = PHYTrainingStateMachine(channel_id=0)

        for delay in range(64):
            margin = sm._measure_rd_dq_margin(delay)
            assert 0 <= margin <= 1

    def test_read_dq_per_lane_calibration(self):
        """Test per-lane Read DQ calibration"""
        sm = PHYTrainingStateMachine(channel_id=0)

        for lane in range(64):
            delay = sm._calibrate_lane_rd(lane)
            assert 0 <= delay <= 63

    def test_read_dq_in_training_sequence(self):
        """Test Read DQ is in training sequence"""
        assert TrainingPhase.TRAIN_RD_DQ in PHYTrainingStateMachine.TRAINING_SEQUENCE
        assert TrainingPhase.TRAIN_RD_DQ_EYE in PHYTrainingStateMachine.TRAINING_SEQUENCE


# =============================================================================
# Test Write DQ Training (WDQ / Write Data Eye)
# =============================================================================

class TestWriteDQTraining:
    """Tests for Write DQ training sequence"""

    def test_write_dq_phase_exists(self):
        """Test TRAIN_WR_DQ phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_WR_DQ')
        assert TrainingPhase.TRAIN_WR_DQ is not None

    def test_write_dq_eye_phase_exists(self):
        """Test TRAIN_WR_DQ_EYE phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_WR_DQ_EYE')
        assert TrainingPhase.TRAIN_WR_DQ_EYE is not None

    def test_write_dq_encoding(self):
        """Test DFI encoding for Write DQ"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_WR_DQ)

        assert tra_req is True
        assert tra_mode == 3
        assert tra_type == 0

    def test_write_dq_eye_encoding(self):
        """Test DFI encoding for Write DQ Eye"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_WR_DQ_EYE)

        assert tra_req is True
        assert tra_mode == 3
        assert tra_type == 1

    def test_write_dq_margin_measurement(self):
        """Test Write DQ margin measurement"""
        sm = PHYTrainingStateMachine(channel_id=0)

        for delay in range(64):
            margin = sm._measure_wr_dq_margin(delay)
            assert 0 <= margin <= 1

    def test_write_dq_per_lane_calibration(self):
        """Test per-lane Write DQ calibration"""
        sm = PHYTrainingStateMachine(channel_id=0)

        for lane in range(64):
            delay = sm._calibrate_lane_wr(lane)
            assert 0 <= delay <= 63

    def test_write_dq_in_training_sequence(self):
        """Test Write DQ is in training sequence"""
        assert TrainingPhase.TRAIN_WR_DQ in PHYTrainingStateMachine.TRAINING_SEQUENCE
        assert TrainingPhase.TRAIN_WR_DQ_EYE in PHYTrainingStateMachine.TRAINING_SEQUENCE


# =============================================================================
# Test Gate Training
# =============================================================================

class TestGateTraining:
    """Tests for Gate Training sequence"""

    def test_gate_phase_exists(self):
        """Test TRAIN_GATE phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_GATE')
        assert TrainingPhase.TRAIN_GATE is not None

    def test_gate_delay_phase_exists(self):
        """Test TRAIN_GATE_DELAY phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_GATE_DELAY')
        assert TrainingPhase.TRAIN_GATE_DELAY is not None

    def test_gate_encoding(self):
        """Test DFI encoding for Gate Training"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_GATE)

        assert tra_req is True
        assert tra_mode == 4
        assert tra_type == 0

    def test_gate_delay_encoding(self):
        """Test DFI encoding for Gate Delay"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_GATE_DELAY)

        assert tra_req is True
        assert tra_mode == 4
        assert tra_type == 1

    def test_gate_margin_measurement(self):
        """Test Gate margin measurement"""
        sm = PHYTrainingStateMachine(channel_id=0)

        for delay in range(64):
            margin = sm._measure_gate_margin(delay)
            assert 0 <= margin <= 1

    def test_gate_in_training_sequence(self):
        """Test Gate Training is in training sequence"""
        assert TrainingPhase.TRAIN_GATE in PHYTrainingStateMachine.TRAINING_SEQUENCE
        assert TrainingPhase.TRAIN_GATE_DELAY in PHYTrainingStateMachine.TRAINING_SEQUENCE


# =============================================================================
# Test VREF Training
# =============================================================================

class TestVREFTraining:
    """Tests for VREF Training sequence"""

    def test_vref_ca_phase_exists(self):
        """Test TRAIN_VREF_CA phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_VREF_CA')
        assert TrainingPhase.TRAIN_VREF_CA is not None

    def test_vref_dq_phase_exists(self):
        """Test TRAIN_VREF_DQ phase exists"""
        assert hasattr(TrainingPhase, 'TRAIN_VREF_DQ')
        assert TrainingPhase.TRAIN_VREF_DQ is not None

    def test_vref_ca_encoding(self):
        """Test DFI encoding for VREF CA"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_VREF_CA)

        assert tra_req is True
        assert tra_mode == 5
        assert tra_type == 0

    def test_vref_dq_encoding(self):
        """Test DFI encoding for VREF DQ"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_VREF_DQ)

        assert tra_req is True
        assert tra_mode == 5
        assert tra_type == 1

    def test_vref_dac_range(self):
        """Test VREF DAC range constants"""
        assert VREF_CA_MIN == 0
        assert VREF_CA_MAX == 63
        assert VREF_DQ_MIN == 0
        assert VREF_DQ_MAX == 63

    def test_vref_margin_measurement(self):
        """Test VREF margin measurement"""
        sm = PHYTrainingStateMachine(channel_id=0)

        for vref in range(VREF_CA_MIN, VREF_CA_MAX + 1):
            margin = sm._measure_ca_vref_margin(vref)
            assert 0 <= margin <= 1

    def test_vref_validation(self):
        """Test VREF validation"""
        sm = PHYTrainingStateMachine(channel_id=0)

        # Valid VREF
        assert sm._validate_vref(32, "CA") is True
        assert sm._validate_vref(32, "DQ") is True

        # Invalid VREF
        with pytest.raises(ValueError):
            sm._validate_vref(100, "CA")

        with pytest.raises(ValueError):
            sm._validate_vref(-1, "DQ")

    def test_vref_in_training_sequence(self):
        """Test VREF Training is in training sequence"""
        assert TrainingPhase.TRAIN_VREF_CA in PHYTrainingStateMachine.TRAINING_SEQUENCE
        assert TrainingPhase.TRAIN_VREF_DQ in PHYTrainingStateMachine.TRAINING_SEQUENCE


# =============================================================================
# Test PAM3 Training (HBM4E)
# =============================================================================

class TestPAM3Training:
    """Tests for PAM3 (3-level signaling) training sequence for HBM4E"""

    def test_pam3_enabled_by_config(self):
        """Test PAM3 mode can be enabled via config"""
        config = {'pam3_enabled': True}
        sm = PHYTrainingStateMachine(channel_id=0, config=config)

        assert sm.pam3_enabled is True
        assert sm.pam3_config is not None

    def test_pam3_disabled_by_default(self):
        """Test PAM3 mode is disabled by default"""
        sm = PHYTrainingStateMachine(channel_id=0)

        assert sm.pam3_enabled is False
        assert sm.pam3_config is None

    def test_pam3_levels(self):
        """Test PAM3 level enum"""
        assert PAM3Level.LOW.value == -1
        assert PAM3Level.ZERO.value == 0
        assert PAM3Level.HIGH.value == 1

    def test_pam3_level_detection(self):
        """Test PAM3 level detection from sample"""
        config = PAM3SignalConfig()
        # Default vref_high = vref_low = 63, range is 127
        # So vref_high / 127 = 63/127 ≈ 0.496
        # Sample 0.9 >= 0.496 -> HIGH
        # Sample 0.1 <= 0.496 -> LOW
        # Sample 0.4 < 0.496 and 0.4 > 0.496 -> ZERO (not reachable with default)
        assert config.get_pam3_level(0.9) == PAM3Level.HIGH
        assert config.get_pam3_level(0.1) == PAM3Level.LOW

        # Test mid-range value: 0.4 is <= 0.496 so it's LOW
        assert config.get_pam3_level(0.4) == PAM3Level.LOW

        # Test with custom vref settings
        config.vref_high = 80
        config.vref_low = 40
        # vref_high / 127 = 80/127 ≈ 0.630
        # vref_low / 127 = 40/127 ≈ 0.315
        assert config.get_pam3_level(0.9) == PAM3Level.HIGH
        assert config.get_pam3_level(0.1) == PAM3Level.LOW
        assert config.get_pam3_level(0.5) == PAM3Level.ZERO

    def test_pam3_vref_validation(self):
        """Test PAM3 VREF validation"""
        config = PAM3SignalConfig()

        # Valid settings
        config.vref_high = 80
        config.vref_low = 20
        assert config.validate_vref_settings() is True

        # Invalid: out of range
        config.vref_high = 200
        assert config.validate_vref_settings() is False

    def test_pam3_vref_range(self):
        """Test PAM3 VREF range constants"""
        assert PAM3_VREF_DAC_RANGE == (0, 127)
        assert PAM3_VREF_HIGH_MIN == 40
        assert PAM3_VREF_HIGH_MAX == 90
        assert PAM3_VREF_LOW_MIN == 10
        assert PAM3_VREF_LOW_MAX == 60
        assert PAM3_VREF_MID == 63

    def test_pam3_eye_margins(self):
        """Test PAM3 eye margin constants"""
        assert PAM3_UPPER_EYE_MARGIN == 0.2
        assert PAM3_LOWER_EYE_MARGIN == 0.2
        assert PAM3_VERTICAL_EYE_MARGIN == 0.15

    def test_pam3_dfe_config(self):
        """Test PAM3 DFE configuration constants"""
        assert PAM3_DFE_NUM_TAPS == 5
        assert PAM3_DFE_MAX_TAP_WEIGHT == 0.25
        assert PAM3_DFE_CONVERGENCE_RATE == 0.01

    def test_pam3_signal_config_init(self):
        """Test PAM3SignalConfig initialization"""
        config = PAM3SignalConfig()

        assert config.vref_high == PAM3_VREF_MID
        assert config.vref_low == PAM3_VREF_MID
        assert len(config.dfe_taps) == PAM3_DFE_NUM_TAPS
        assert all(t == 0.0 for t in config.dfe_taps)
        assert config.training_complete is False
        assert config.training_passed is False

    def test_pam3_eye_center_calculation(self):
        """Test PAM3 eye center calculation"""
        config = PAM3SignalConfig()
        config.vref_high = 80
        config.vref_low = 20

        upper_center, lower_center = config.calculate_eye_center()

        assert upper_center > 0.5
        assert lower_center < 0.5
        assert upper_center > lower_center

    def test_pam3_training_states(self):
        """Test PAM3 training state enum"""
        expected_states = [
            PAM3TrainingState.PAM3_INIT,
            PAM3TrainingState.PAM3_VREF_CAL,
            PAM3TrainingState.PAM3_EYE_TRAINING,
            PAM3TrainingState.PAM3_DFE_TAPS,
            PAM3TrainingState.PAM3_MARGIN_VERIFY,
            PAM3TrainingState.PAM3_COMPLETE,
        ]

        for state in expected_states:
            assert state is not None

    def test_pam3_upper_margin_measurement(self):
        """Test PAM3 upper margin measurement"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'pam3_enabled': True})

        for vref in range(PAM3_VREF_HIGH_MIN, PAM3_VREF_HIGH_MAX):
            margin = sm._measure_pam3_upper_margin(vref)
            assert 0 <= margin <= 1

    def test_pam3_lower_margin_measurement(self):
        """Test PAM3 lower margin measurement"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'pam3_enabled': True})

        for vref in range(PAM3_VREF_LOW_MIN, PAM3_VREF_LOW_MAX):
            margin = sm._measure_pam3_lower_margin(vref)
            assert 0 <= margin <= 1

    def test_pam3_eye_margin_measurement(self):
        """Test PAM3 eye margin measurement"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'pam3_enabled': True})

        for delay in range(64):
            margin = sm._measure_pam3_eye_margin(delay)
            assert 0 <= margin <= 1

    def test_pam3_ber_measurement(self):
        """Test PAM3 BER measurement"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'pam3_enabled': True})

        taps = [0.0] * PAM3_DFE_NUM_TAPS
        ber = sm._measure_pam3_ber(taps)

        assert 0 < ber <= 1

    def test_pam3_dfe_tap_delta(self):
        """Test PAM3 DFE tap delta calculation"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'pam3_enabled': True})

        for tap_idx in range(PAM3_DFE_NUM_TAPS):
            delta = sm._calculate_dfe_tap_delta(tap_idx, 0.1, 1e-6)
            # Delta should be small value
            assert isinstance(delta, float)

    def test_pam3_pam3_training_sequence(self):
        """Test PAM3 training sequence is defined"""
        assert len(PHYTrainingStateMachine.PAM3_TRAINING_SEQUENCE) > 0
        assert PHYTrainingStateMachine.PAM3_TRAINING_SEQUENCE[0] == PAM3TrainingState.PAM3_INIT

    def test_pam3_pam3_in_main_sequence(self):
        """Test PAM3 phases are in main training sequence"""
        assert TrainingPhase.TRAIN_PAM3_INIT in PHYTrainingStateMachine.TRAINING_SEQUENCE
        assert TrainingPhase.TRAIN_PAM3_VREF in PHYTrainingStateMachine.TRAINING_SEQUENCE
        assert TrainingPhase.TRAIN_PAM3_EYE in PHYTrainingStateMachine.TRAINING_SEQUENCE
        assert TrainingPhase.TRAIN_PAM3_DFE in PHYTrainingStateMachine.TRAINING_SEQUENCE
        assert TrainingPhase.TRAIN_PAM3_VERIFY in PHYTrainingStateMachine.TRAINING_SEQUENCE

    def test_pam3_dfi_encoding(self):
        """Test PAM3 DFI encoding"""
        ctrl = DFI5TrainingControl()

        for state in PAM3TrainingState:
            req, subtype = ctrl.encode_pam3_training_cmd(state)
            assert isinstance(req, bool)
            assert isinstance(subtype, int)

    def test_pam3_set_mode(self):
        """Test setting PAM3 mode"""
        sm = PHYTrainingStateMachine(channel_id=0)

        sm.set_pam3_mode(True)
        assert sm.pam3_enabled is True
        assert sm.pam3_config is not None

        sm.set_pam3_mode(False)
        assert sm.pam3_enabled is False

    def test_pam3_status(self):
        """Test PAM3 status reporting"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'pam3_enabled': True})

        status = sm.get_pam3_status()

        assert status['enabled'] is True
        assert 'pam3_state' in status
        assert 'vref_settings' in status
        assert 'margins' in status

    def test_pam3_loopback_ready(self):
        """Test PAM3 loopback ready status"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'pam3_enabled': True})

        status = sm.get_loopback_ready_status()

        assert 'pam3_coefficients' in status
        assert 'upper_vref' in status['pam3_coefficients']
        assert 'lower_vref' in status['pam3_coefficients']


# =============================================================================
# Test DFI 5.0 Interface
# =============================================================================

class TestDFI5Interface:
    """Tests for DFI 5.0 interface integration"""

    def test_dfi_training_control_init(self):
        """Test DFI5TrainingControl initialization"""
        ctrl = DFI5TrainingControl()

        assert ctrl.tra_req is False
        assert ctrl.tra_mode == 0
        assert ctrl.tra_type == 0
        assert ctrl.tra_ack is False
        assert ctrl.tra_complete is False
        assert ctrl.tra_error is False

    def test_dfi_freq_change_protocol(self):
        """Test DFI 5.0 frequency change protocol"""
        ctrl = DFI5TrainingControl()

        ctrl.start_freq_change(target_ratio=2)

        assert ctrl.freq_change_req is True
        assert ctrl.freq_ratio == 2
        assert ctrl.lp_state == DFI5LowPowerState.LP_FREQ_CHANGE

    def test_dfi_freq_change_complete(self):
        """Test DFI 5.0 frequency change completion"""
        ctrl = DFI5TrainingControl()
        ctrl.start_freq_change(target_ratio=2)

        ctrl.complete_freq_change()

        assert ctrl.freq_change_req is False
        assert ctrl.lp_state == DFI5LowPowerState.LP_IDLE

    def test_dfi_low_power_entry(self):
        """Test DFI 5.0 low power entry"""
        ctrl = DFI5TrainingControl()

        ctrl.enter_low_power(DFI5LowPowerState.LP_CTRL)

        assert ctrl.lp_req is True
        assert ctrl.lp_state == DFI5LowPowerState.LP_CTRL

    def test_dfi_low_power_exit(self):
        """Test DFI 5.0 low power exit"""
        ctrl = DFI5TrainingControl()
        ctrl.enter_low_power(DFI5LowPowerState.LP_CTRL)

        ctrl.exit_low_power()

        assert ctrl.lp_state == DFI5LowPowerState.LP_IDLE

    def test_dfi_pim_mode(self):
        """Test DFI 5.0 PHY Independent Mode"""
        ctrl = DFI5TrainingControl()

        ctrl.enable_pim_mode(pim_mode=1)

        assert ctrl.pim_enable is True
        assert ctrl.pim_mode == 1
        assert ctrl.pim_training_req is True

    def test_dfi_ctrl_update(self):
        """Test DFI 5.0 control update"""
        ctrl = DFI5TrainingControl()

        ctrl.ctrlupd_req = True
        assert ctrl.ctrlupd_req is True

        ctrl.ctrlupd_ack = True
        assert ctrl.ctrlupd_ack is True

    def test_dfi_all_training_phases_encoded(self):
        """Test all training phases can be encoded"""
        ctrl = DFI5TrainingControl()

        for phase in TrainingPhase:
            tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(phase)
            assert isinstance(tra_req, bool)
            assert isinstance(tra_mode, int)
            assert isinstance(tra_type, int)


# =============================================================================
# Test Training Sequence Executor
# =============================================================================

class TestTrainingSequenceExecutor:
    """Tests for TrainingSequenceExecutor"""

    def test_executor_init(self):
        """Test executor initialization"""
        executor = TrainingSequenceExecutor()

        assert executor.sequence is None
        assert executor.current_step is None
        assert executor.is_complete is False

    def test_executor_with_sequence(self):
        """Test executor with sequence"""
        executor = TrainingSequenceExecutor(sequence=QUICK_BOOT_SEQUENCE)

        assert executor.sequence == QUICK_BOOT_SEQUENCE

    def test_executor_start_quick_boot(self):
        """Test starting quick boot sequence"""
        executor = TrainingSequenceExecutor()

        executor.start_sequence(TrainingSequenceType.QUICK_BOOT)

        assert executor.sequence is not None
        assert executor.current_step is not None
        assert executor.current_step.name == "Write Leveling"

    def test_executor_start_normal(self):
        """Test starting normal sequence"""
        executor = TrainingSequenceExecutor()

        executor.start_sequence(TrainingSequenceType.NORMAL)

        assert executor.sequence.sequence_type == TrainingSequenceType.NORMAL
        assert len(executor.sequence.steps) > 0

    def test_executor_start_extended(self):
        """Test starting extended sequence"""
        executor = TrainingSequenceExecutor()

        executor.start_sequence(TrainingSequenceType.EXTENDED)

        assert executor.sequence.sequence_type == TrainingSequenceType.EXTENDED

    def test_executor_start_margin_scan(self):
        """Test starting margin scan sequence"""
        executor = TrainingSequenceExecutor()

        executor.start_sequence(TrainingSequenceType.MARGIN_SCAN)

        assert executor.sequence.sequence_type == TrainingSequenceType.MARGIN_SCAN

    def test_executor_tick(self):
        """Test executor tick"""
        executor = TrainingSequenceExecutor()
        executor.start_sequence(TrainingSequenceType.QUICK_BOOT)

        # Process some cycles
        for _ in range(100):
            executor.tick()

        # Should have made progress
        assert executor.completion_status.total_cycles > 0

    def test_executor_results(self):
        """Test executor results"""
        executor = TrainingSequenceExecutor()
        executor.start_sequence(TrainingSequenceType.QUICK_BOOT)

        # Run to completion
        for _ in range(100000):
            if executor.is_complete:
                break
            executor.tick()

        results = executor.get_results()

        assert 'sequence_name' in results
        assert 'is_complete' in results
        assert 'step_results' in results


# =============================================================================
# Test Training Completion Detector
# =============================================================================

class TestTrainingCompletionDetector:
    """Tests for TrainingCompletionDetector"""

    def test_detector_init(self):
        """Test detector initialization"""
        detector = TrainingCompletionDetector()

        assert detector.min_pass_count == 2
        assert detector.margin_stable_threshold == 0.02
        assert detector.consecutive_pass_required == 3

    def test_detector_custom_config(self):
        """Test detector with custom config"""
        config = {
            'min_pass_count': 3,
            'margin_stable_threshold': 0.05,
            'consecutive_pass_required': 5,
        }
        detector = TrainingCompletionDetector(config=config)

        assert detector.min_pass_count == 3
        assert detector.margin_stable_threshold == 0.05
        assert detector.consecutive_pass_required == 5

    def test_detector_consecutive_pass(self):
        """Test detector with consecutive passes"""
        detector = TrainingCompletionDetector(
            config={'consecutive_pass_required': 3}
        )

        # Not enough consecutive passes yet
        for i in range(2):
            result = detector.update(True, 0.5, f'phase_{i}')
            # Result may be True if other conditions are met
            assert isinstance(result, bool)

        # Third consecutive pass should trigger completion
        result = detector.update(True, 0.5, 'phase_3')
        # Result should be True after 3 consecutive passes
        assert result is True

    def test_detector_margin_stability(self):
        """Test detector margin stability"""
        detector = TrainingCompletionDetector(
            config={'margin_stable_threshold': 0.01}
        )

        # Stable margins
        for i in range(5):
            result = detector.update(True, 0.5, f'phase_{i}')
            # Eventually should complete due to stability
            if result:
                break

    def test_detector_reset(self):
        """Test detector reset"""
        detector = TrainingCompletionDetector()

        # Add some data
        detector.update(True, 0.5, 'phase_0')
        detector.update(True, 0.6, 'phase_1')

        # Reset
        detector.reset()

        # Should be cleared
        assert len(detector._pass_history) == 0
        assert len(detector._margin_history) == 0


# =============================================================================
# Test Training Sequence Definitions
# =============================================================================

class TestTrainingSequenceDefinitions:
    """Tests for pre-defined training sequences"""

    def test_quick_boot_sequence(self):
        """Test Quick Boot sequence definition"""
        assert QUICK_BOOT_SEQUENCE.name == "Quick Boot Training"
        assert QUICK_BOOT_SEQUENCE.sequence_type == TrainingSequenceType.QUICK_BOOT
        assert len(QUICK_BOOT_SEQUENCE.steps) == 3

    def test_normal_sequence(self):
        """Test Normal sequence definition"""
        assert NORMAL_TRAINING_SEQUENCE.name == "Normal Training"
        assert NORMAL_TRAINING_SEQUENCE.sequence_type == TrainingSequenceType.NORMAL
        assert len(NORMAL_TRAINING_SEQUENCE.steps) > 3

    def test_extended_sequence(self):
        """Test Extended sequence definition"""
        assert EXTENDED_TRAINING_SEQUENCE.name == "Extended Training"
        assert EXTENDED_TRAINING_SEQUENCE.sequence_type == TrainingSequenceType.EXTENDED
        assert len(EXTENDED_TRAINING_SEQUENCE.steps) > len(NORMAL_TRAINING_SEQUENCE.steps)

    def test_margin_scan_sequence(self):
        """Test Margin Scan sequence definition"""
        assert MARGIN_SCAN_SEQUENCE.name == "Margin Scan"
        assert MARGIN_SCAN_SEQUENCE.sequence_type == TrainingSequenceType.MARGIN_SCAN

    def test_create_training_sequence_quick(self):
        """Test factory function for quick boot"""
        seq = create_training_sequence(TrainingSequenceType.QUICK_BOOT)
        assert seq == QUICK_BOOT_SEQUENCE

    def test_create_training_sequence_normal(self):
        """Test factory function for normal"""
        seq = create_training_sequence(TrainingSequenceType.NORMAL)
        assert seq == NORMAL_TRAINING_SEQUENCE

    def test_get_dfi_training_command(self):
        """Test DFI training command mapping"""
        assert get_dfi_training_command('WRLVL') == DFITrainingCommand.WRLVL_REQ
        assert get_dfi_training_command('RDGD') == DFITrainingCommand.RDGD_REQ
        # Use exact phase names from mapping
        assert get_dfi_training_command('MGCAL_VREF') == DFITrainingCommand.VREF_REQ
        assert get_dfi_training_command('DFE_TRAIN') == DFITrainingCommand.DFE_REQ
        # Test unknown returns NOP
        assert get_dfi_training_command('UNKNOWN') == DFITrainingCommand.NOP


# =============================================================================
# Test DFI Training Control (from training_sequences)
# =============================================================================

class TestDFITrainingControlSignals:
    """Tests for DFITrainingControl from training_sequences"""

    def test_dfi_training_control_init(self):
        """Test DFITrainingControl initialization"""
        ctrl = DFITrainingControl()

        assert ctrl.training_req is False
        assert ctrl.training_cmd == DFITrainingCommand.NOP
        assert ctrl.training_mode == 0
        assert ctrl.training_ack is False
        assert ctrl.training_error is False
        assert ctrl.training_complete is False
        assert ctrl.training_passed is False

    def test_dfi_training_control_lane_enable(self):
        """Test lane enable bits"""
        ctrl = DFITrainingControl()

        assert ctrl.lane_enable == 0xFFFFFFFFFFFFFFFF
        assert ctrl.lane_select == 0


# =============================================================================
# Test Training Completion Status
# =============================================================================

class TestTrainingCompletionStatus:
    """Tests for TrainingCompletionStatus"""

    def test_completion_status_init(self):
        """Test completion status initialization"""
        status = TrainingCompletionStatus()

        assert status.sequence_complete is False
        assert status.all_phases_passed is False
        assert status.total_cycles == 0
        assert len(status.failed_phases) == 0
        assert status.warning_count == 0
        assert status.min_read_margin == 0.0
        assert status.min_write_margin == 0.0
        assert status.min_vref_margin == 0.0


# =============================================================================
# Integration Tests
# =============================================================================

class TestPHYTrainingIntegration:
    """Integration tests for complete PHY training flow"""

    def test_full_training_sequence(self):
        """Test complete training sequence execution"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'timeout_cycles': 100000})
        sm.start_training()

        phases_executed = []
        for _ in range(500000):
            sm.tick()
            current_phase = sm.status.current_phase

            if current_phase not in phases_executed and current_phase != TrainingPhase.TRAIN_IDLE:
                phases_executed.append(current_phase)

            if sm.is_training_complete():
                break

            sm.process_training_cycle()

        # Should have executed multiple phases
        assert len(phases_executed) > 0

    def test_training_with_mock_dfi(self):
        """Test training with mock DFI interface"""
        mock_dfi = Mock()
        sm = PHYTrainingStateMachine(channel_id=0, dfi_interface=mock_dfi)

        sm.start_training()

        # Verify DFI start was called
        mock_dfi.start_training.assert_called_once()

    def test_training_results_structure(self):
        """Test training results structure"""
        sm = PHYTrainingStateMachine(channel_id=0)
        sm.start_training()

        # Process some cycles
        for _ in range(1000):
            sm.tick()
            sm.process_training_cycle()
            if sm.is_training_complete():
                break

        results = sm.get_training_results()

        assert 'channel_id' in results
        assert 'passed' in results
        assert 'current_phase' in results
        assert 'total_cycles' in results
        assert 'retry_count' in results
        assert 'results' in results
        assert 'parameters' in results
        assert 'errors' in results

    def test_initialization_with_training(self):
        """Test initialization with integrated training"""
        training_sm = PHYTrainingStateMachine(channel_id=0)
        init_sm = PHYInitializationStateMachine(training_sm=training_sm)

        init_sm.start_initialization()

        # Process through states
        for _ in range(500000):
            init_sm.tick()
            init_sm.process_init_cycle()

            if init_sm.is_initialized:
                break

        assert init_sm.is_initialized

    def test_multi_channel_initialization(self):
        """Test multi-channel initialization"""
        manager = HBM4PHYManager(num_channels=4)

        manager.start_initialization()

        # Process cycles
        for _ in range(500000):
            if manager.is_ready():
                break
            manager.tick()

        # All channels should be initialized
        assert all(sm.is_initialized for sm in manager._init_machines)


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestPHYTrainingErrors:
    """Tests for PHY training error handling"""

    def test_training_phase_timeout(self):
        """Test training phase timeout handling"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'timeout_cycles': 10})
        sm.start_training()

        # Process many cycles to trigger timeout
        for _ in range(100):
            sm.tick()
            sm.process_training_cycle()

        # Should have recorded errors
        assert len(sm.params.training_errors) > 0 or \
               sm.status.current_phase in [TrainingPhase.TRAIN_COMPLETE,
                                           TrainingPhase.TRAIN_FAIL]

    def test_invalid_channel_status(self):
        """Test invalid channel status access"""
        manager = HBM4PHYManager(num_channels=4)

        status = manager.get_channel_status(10)

        assert 'error' in status

    def test_vref_result_validation(self):
        """Test VREF result validation"""
        sm = PHYTrainingStateMachine(channel_id=0)

        # Valid result
        assert sm._validate_vref_result(32, "CA") is True
        assert sm._validate_vref_result(32, "DQ") is True


# =============================================================================
# Performance Tests
# =============================================================================

class TestPHYTrainingPerformance:
    """Performance tests for PHY training"""

    def test_training_cycles_efficiency(self):
        """Test training completes in reasonable cycles"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'timeout_cycles': 100000})
        sm.start_training()

        initial_cycle = sm.cycle

        # Run training
        for _ in range(100000):
            sm.tick()
            sm.process_training_cycle()
            if sm.is_training_complete():
                break

        final_cycle = sm.cycle
        total_cycles = final_cycle - initial_cycle

        # Training should complete (or fail) within timeout
        assert total_cycles <= 100000

    def test_executor_cycles_efficiency(self):
        """Test executor completes in reasonable cycles"""
        executor = TrainingSequenceExecutor()
        executor.start_sequence(TrainingSequenceType.QUICK_BOOT)

        initial_cycles = executor.completion_status.total_cycles

        # Run executor
        for _ in range(100000):
            executor.tick()
            if executor.is_complete:
                break

        final_cycles = executor.completion_status.total_cycles
        total_cycles = final_cycles - initial_cycles

        # Quick boot should complete in reasonable time
        assert total_cycles <= 100000


# =============================================================================
# State Machine Transition Tests
# =============================================================================

class TestPHYTrainingStateTransitions:
    """Tests for training state machine transitions"""

    def test_idle_to_start_transition(self):
        """Test IDLE to START transition"""
        sm = PHYTrainingStateMachine(channel_id=0)

        assert sm.status.current_phase == TrainingPhase.TRAIN_IDLE

        sm.start_training()

        assert sm.status.current_phase == TrainingPhase.TRAIN_START

    def test_training_states_sequence(self):
        """Test training states follow correct sequence"""
        expected_sequence = [
            TrainingPhase.TRAIN_START,
            TrainingPhase.TRAIN_INIT,
        ]

        sm = PHYTrainingStateMachine(channel_id=0)
        sm.start_training()

        # Initial transition
        sm.tick()
        sm.process_training_cycle()

        assert sm.status.current_phase in expected_sequence

    def test_training_retry_count(self):
        """Test training retry count tracking"""
        sm = PHYTrainingStateMachine(channel_id=0)

        assert sm.status.retry_count == 0

        sm.start_training()

        assert sm.status.retry_count == 0

    def test_initialization_states_sequence(self):
        """Test initialization states follow correct sequence"""
        expected_states = [
            PHYInitState.INIT_IDLE,
            PHYInitState.INIT_START,
            PHYInitState.INIT_POWER_UP,
            PHYInitState.INIT_RESET,
            PHYInitState.INIT_CONFIG,
            PHYInitState.INIT_CALIBRATE,
            PHYInitState.INIT_TRAINING,
            PHYInitState.INIT_COMPLETE,
        ]

        init_sm = PHYInitializationStateMachine()

        assert init_sm.status.state == PHYInitState.INIT_IDLE

        init_sm.start_initialization()

        assert init_sm.status.state == PHYInitState.INIT_START


# =============================================================================
# Parameter and Status Tests
# =============================================================================

class TestPHYTrainingParameters:
    """Tests for training parameters"""

    def test_training_parameters_defaults(self):
        """Test default training parameters"""
        params = TrainingParameters()

        assert params.rd_dqs_delay == 0
        assert params.wr_level_delay == 0
        assert params.rd_margin == 0.0
        assert params.wr_margin == 0.0
        assert params.rd_vref == 0
        assert params.wr_vref == 0
        assert params.ca_vref == 0
        assert params.training_passed is False
        assert len(params.training_errors) == 0

    def test_training_parameters_pam3(self):
        """Test PAM3 training parameters"""
        params = TrainingParameters()

        assert params.pam3_enabled is False
        assert params.pam3_upper_vref == PAM3_VREF_MID
        assert params.pam3_lower_vref == PAM3_VREF_MID
        assert params.pam3_training_complete is False

    def test_training_status_defaults(self):
        """Test default training status"""
        status = TrainingStatus()

        assert status.current_phase == TrainingPhase.TRAIN_IDLE
        assert status.phase_start_cycle == 0
        assert status.total_training_cycles == 0
        assert status.retry_count == 0
        assert status.max_retries == 3

    def test_phy_init_status_defaults(self):
        """Test default PHY init status"""
        status = PHYInitStatus()

        assert status.state == PHYInitState.INIT_IDLE
        assert status.state_enter_cycle == 0
        assert status.calibration_count == 0
        assert status.error_count == 0
        assert len(status.warnings) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
