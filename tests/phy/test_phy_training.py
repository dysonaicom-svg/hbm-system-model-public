"""
Tests for PHY Training Model

Tests the PHY training implementation including:
- Training state machine transitions
- Sequence execution
- Coefficient convergence
- DFI integration

Reference:
- JEDEC JESD270-4A HBM4 specification
- DFI 5.0/5.1 specification
"""

import pytest
import numpy as np
from model.phy.phy_training import (
    PHYTrainingState,
    PHYTrainingType,
    TrainingPattern,
    PHYTrainingConfig,
    TrainingPhaseResult,
    PHYTapCoefficients,
    PHYTrainingStatus,
    PHYTrainingModel,
    create_phy_training_model,
)


class TestPHYTrainingStateMachine:
    """Test PHY training state machine"""
    
    def test_initial_state_is_idle(self):
        """Test initial state is IDLE"""
        model = PHYTrainingModel(channel_id=0)
        assert model.status.state == PHYTrainingState.IDLE
        assert not model.is_training
        assert not model.is_complete
    
    def test_start_training_transitions_to_init(self):
        """Test starting training transitions to INIT"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training()
        
        assert model.is_training
        assert model.status.state == PHYTrainingState.INIT
    
    def test_training_sequence_order(self):
        """Test training follows correct sequence"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training()
        
        expected_sequence = [
            PHYTrainingState.WRLVL,
            PHYTrainingState.WRLVL_DQS,
            PHYTrainingState.RDGD,
            PHYTrainingState.RDGD_DQS,
            PHYTrainingState.RDDLY,
            PHYTrainingState.WR_DQ,
            PHYTrainingState.RD_DQ,
            PHYTrainingState.MGCAL_VREF,
            PHYTrainingState.MGCAL_DQ,
            PHYTrainingState.DFE_TRAIN,
        ]
        
        assert model.TRAINING_SEQUENCE == expected_sequence
    
    def test_process_cycle_advances_state(self):
        """Test process_cycle advances through states"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training()
        
        # Process INIT state
        model.process_cycle()
        assert model.status.state == PHYTrainingState.WRLVL
    
    def test_training_completes(self):
        """Test training completes after all phases"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training()
        
        # Run until complete
        for _ in range(10000):
            done = model.process_cycle()
            model.tick()
            if model.is_complete:
                break
        
        assert model.is_complete
        # Training may pass or fail depending on simulation
        results = model.get_training_results()
        assert 'state' in results
        assert 'total_cycles' in results


class TestPHYTrainingTypes:
    """Test different training types"""
    
    def test_normal_training_type(self):
        """Test normal training type"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training(PHYTrainingType.NORMAL)
        assert model.status.training_type == PHYTrainingType.NORMAL
    
    def test_quick_training_type(self):
        """Test quick training type"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training(PHYTrainingType.QUICK)
        assert model.status.training_type == PHYTrainingType.QUICK
    
    def test_verify_only_type(self):
        """Test verify-only training type"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training(PHYTrainingType.VERIFY_ONLY)
        assert model.status.training_type == PHYTrainingType.VERIFY_ONLY


class TestTrainingPatterns:
    """Test training pattern generation"""
    
    def test_prbs7_generation(self):
        """Test PRBS7 pattern generation"""
        model = PHYTrainingModel(channel_id=0)
        pattern = model._generate_training_pattern(TrainingPattern.PRBS7)
        
        assert isinstance(pattern, np.ndarray)
        assert len(pattern) > 0
        # PRBS7 values should be +/- 1
        assert all(v in [-1, 1] for v in pattern)
    
    def test_prbs15_generation(self):
        """Test PRBS15 pattern generation"""
        model = PHYTrainingModel(channel_id=0)
        pattern = model._generate_training_pattern(TrainingPattern.PRBS15)
        
        assert isinstance(pattern, np.ndarray)
        assert len(pattern) > 0
    
    def test_walking_1_generation(self):
        """Test walking 1 pattern"""
        model = PHYTrainingModel(channel_id=0)
        pattern = model._generate_training_pattern(TrainingPattern.WALKING_1)
        
        assert isinstance(pattern, np.ndarray)
        assert len(pattern) > 0
    
    def test_all_ones_pattern(self):
        """Test all ones pattern"""
        model = PHYTrainingModel(channel_id=0)
        pattern = model._generate_training_pattern(TrainingPattern.ALL_ONES)
        
        assert isinstance(pattern, np.ndarray)
        assert all(v == 1 for v in pattern)
    
    def test_all_zeros_pattern(self):
        """Test all zeros pattern"""
        model = PHYTrainingModel(channel_id=0)
        pattern = model._generate_training_pattern(TrainingPattern.ALL_ZEROS)
        
        assert isinstance(pattern, np.ndarray)
        assert all(v == -1 for v in pattern)
    
    def test_alternating_pattern(self):
        """Test alternating pattern"""
        model = PHYTrainingModel(channel_id=0)
        pattern = model._generate_training_pattern(TrainingPattern.ALTERNATING)
        
        assert isinstance(pattern, np.ndarray)
        # Should alternate between 1 and -1
        for i in range(len(pattern) - 1):
            assert pattern[i] != pattern[i + 1]


class TestTapCoefficients:
    """Test tap coefficient management"""
    
    def test_initial_coefficients(self):
        """Test initial coefficient values"""
        model = PHYTrainingModel(channel_id=0)
        coeffs = model.coefficients
        
        # TX should have default values
        assert len(coeffs.tx_precursor) >= 0
        assert coeffs.tx_main_cursor == 1.0
        
        # RX VREF should be mid-range
        assert 0 <= coeffs.rx_vref <= 63
    
    def test_tx_taps_getter(self):
        """Test getting TX taps"""
        model = PHYTrainingModel(channel_id=0)
        taps = model.coefficients.get_tx_taps()
        
        assert isinstance(taps, list)
        assert len(taps) > 0
    
    def test_coefficients_validity(self):
        """Test coefficient validity check"""
        model = PHYTrainingModel(channel_id=0)
        
        # Valid coefficients
        assert model.coefficients.is_valid() is True
        
        # Invalid VREF
        model.coefficients.rx_vref = 100
        assert model.coefficients.is_valid() is False


class TestPerLaneCalibration:
    """Test per-lane calibration"""
    
    def test_lane_count(self):
        """Test lane count configuration"""
        config = PHYTrainingConfig(num_lanes=64, enable_per_lane=True)
        model = PHYTrainingModel(channel_id=0, config=config)
        
        assert model._lane_count == 64
    
    def test_lane_delays_initialized(self):
        """Test lane delays are initialized"""
        model = PHYTrainingModel(channel_id=0)
        
        for lane in range(model._lane_count):
            assert lane in model.coefficients.lane_delays
    
    def test_per_lane_training(self):
        """Test per-lane training flag"""
        config = PHYTrainingConfig(enable_per_lane=True)
        model = PHYTrainingModel(channel_id=0, config=config)
        
        assert model.config.enable_per_lane is True


class TestTrainingConfiguration:
    """Test training configuration"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = PHYTrainingConfig()
        
        assert config.enable_write_leveling is True
        assert config.enable_read_gate is True
        assert config.enable_margin_cal is True
        assert config.enable_dfe is True
        assert config.num_lanes == 64
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = PHYTrainingConfig(
            num_lanes=32,
            enable_per_lane=False,
            wrlvl_iterations=128
        )
        
        assert config.num_lanes == 32
        assert config.enable_per_lane is False
        assert config.wrlvl_iterations == 128


class TestTrainingResults:
    """Test training results reporting"""
    
    def test_get_training_results_structure(self):
        """Test results structure"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training()
        
        # Run some cycles
        for _ in range(100):
            model.process_cycle()
            model.tick()
        
        results = model.get_training_results()
        
        assert 'channel_id' in results
        assert 'passed' in results
        assert 'state' in results
        assert 'total_cycles' in results
        assert 'coefficients' in results
    
    def test_results_include_coefficients(self):
        """Test results include trained coefficients"""
        model = PHYTrainingModel(channel_id=0)
        results = model.get_training_results()
        
        coeffs = results['coefficients']
        assert 'tx_precursor' in coeffs
        assert 'tx_postcursor' in coeffs
        assert 'rx_vref' in coeffs
        assert 'dfe_taps' in coeffs


class TestTrainingCycle:
    """Test training cycle counting"""
    
    def test_cycle_starts_at_zero(self):
        """Test cycle starts at 0"""
        model = PHYTrainingModel(channel_id=0)
        assert model.cycle == 0
    
    def test_cycle_increments_on_tick(self):
        """Test cycle increments on tick"""
        model = PHYTrainingModel(channel_id=0)
        model.tick()
        assert model.cycle == 1
        
        model.tick()
        model.tick()
        assert model.cycle == 3
    
    def test_total_cycles_tracked(self):
        """Test total cycles are tracked"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training()
        
        for _ in range(10):
            model.process_cycle()
            model.tick()
        
        assert model.status.total_cycles > 0


class TestTrainingTimeout:
    """Test training timeout handling"""
    
    def test_timeout_config(self):
        """Test timeout configuration"""
        config = PHYTrainingConfig(timeout_cycles=1000)
        model = PHYTrainingModel(channel_id=0, config=config)
        
        assert model.config.timeout_cycles == 1000
    
    def test_timeout_handling(self):
        """Test timeout is detected"""
        config = PHYTrainingConfig(timeout_cycles=10)
        model = PHYTrainingModel(channel_id=0, config=config)
        model.start_training()
        
        # Simulate timeout
        for _ in range(100):
            model.tick()
            if model.is_complete:
                break
        
        # Should eventually fail or complete
        assert model.is_complete


class TestRetryMechanism:
    """Test training retry mechanism"""
    
    def test_retry_count_config(self):
        """Test retry count configuration"""
        config = PHYTrainingConfig(retry_count=5)
        model = PHYTrainingModel(channel_id=0, config=config)
        
        assert model.config.retry_count == 5
    
    def test_retry_tracking(self):
        """Test retry count is tracked"""
        model = PHYTrainingModel(channel_id=0)
        model.start_training()
        
        assert model.status.retry_count == 0


class TestChannelId:
    """Test channel ID handling"""
    
    def test_channel_id_assignment(self):
        """Test channel ID is assigned correctly"""
        model = PHYTrainingModel(channel_id=5)
        assert model.channel_id == 5
    
    def test_channel_id_in_results(self):
        """Test channel ID appears in results"""
        model = PHYTrainingModel(channel_id=15)
        results = model.get_training_results()
        
        assert results['channel_id'] == 15


class TestFactoryFunction:
    """Test factory function"""
    
    def test_create_phy_training_model(self):
        """Test factory function creates model"""
        model = create_phy_training_model(channel_id=3)
        
        assert model is not None
        assert model.channel_id == 3
        assert model.status.state == PHYTrainingState.IDLE


# === Training Sequences Tests ===

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
    create_training_sequence,
    get_dfi_training_command,
)


class TestDFITrainingCommands:
    """Test DFI training commands"""
    
    def test_command_count(self):
        """Test all expected commands exist"""
        assert len(DFITrainingCommand) > 0
    
    def test_command_values(self):
        """Test command values are correct"""
        assert DFITrainingCommand.WRLVL_REQ.value == 0x01
        assert DFITrainingCommand.RDGD_REQ.value == 0x02
        assert DFITrainingCommand.VREF_REQ.value == 0x06
        assert DFITrainingCommand.DFE_REQ.value == 0x08


class TestTrainingSequenceDefinitions:
    """Test training sequence definitions"""
    
    def test_quick_boot_sequence(self):
        """Test quick boot sequence exists"""
        assert QUICK_BOOT_SEQUENCE is not None
        assert QUICK_BOOT_SEQUENCE.name == "Quick Boot Training"
        assert len(QUICK_BOOT_SEQUENCE.steps) > 0
    
    def test_normal_sequence(self):
        """Test normal sequence exists"""
        assert NORMAL_TRAINING_SEQUENCE is not None
        assert NORMAL_TRAINING_SEQUENCE.name == "Normal Training"
        assert len(NORMAL_TRAINING_SEQUENCE.steps) >= 10
    
    def test_sequence_steps_have_commands(self):
        """Test sequence steps have commands"""
        for step in NORMAL_TRAINING_SEQUENCE.steps:
            assert step.command is not None
            assert isinstance(step.command, DFITrainingCommand)


class TestTrainingSequenceExecutor:
    """Test training sequence executor"""
    
    def test_executor_initialization(self):
        """Test executor initializes correctly"""
        executor = TrainingSequenceExecutor()
        assert executor is not None
        assert not executor.is_complete
    
    def test_start_sequence(self):
        """Test starting a sequence"""
        executor = TrainingSequenceExecutor()
        executor.start_sequence(TrainingSequenceType.NORMAL)
        
        assert executor.sequence is not None
        assert executor.current_step is not None
    
    def test_executor_tick(self):
        """Test executor tick advances sequence"""
        executor = TrainingSequenceExecutor()
        executor.start_sequence(TrainingSequenceType.QUICK_BOOT)
        
        # Process some ticks
        for _ in range(100):
            executor.tick()
            if executor.is_complete:
                break
        
        # Check results exist
        results = executor.get_results()
        assert 'sequence_name' in results
    
    def test_sequence_type_selection(self):
        """Test sequence type selects correct sequence"""
        executor = TrainingSequenceExecutor()
        
        executor.start_sequence(TrainingSequenceType.QUICK_BOOT)
        assert executor.sequence.sequence_type == TrainingSequenceType.QUICK_BOOT
        
        executor.start_sequence(TrainingSequenceType.NORMAL)
        assert executor.sequence.sequence_type == TrainingSequenceType.NORMAL


class TestTrainingCompletionDetector:
    """Test training completion detector"""
    
    def test_detector_initialization(self):
        """Test detector initializes correctly"""
        detector = TrainingCompletionDetector()
        assert detector is not None
    
    def test_consecutive_pass_detection(self):
        """Test consecutive pass detection"""
        detector = TrainingCompletionDetector(
            config={'consecutive_pass_required': 3}
        )
        
        # Not enough consecutive passes
        result = detector.update(True, 0.5, "test")
        assert result is False
        
        # More passes needed
        detector.update(True, 0.5, "test")
        result = detector.update(True, 0.5, "test")
        assert result is True
    
    def test_reset(self):
        """Test detector reset"""
        detector = TrainingCompletionDetector()
        detector.update(True, 0.5, "test")
        detector.reset()
        
        # Should be ready for new measurements
        assert len(detector._pass_history) == 0


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_create_training_sequence(self):
        """Test create_training_sequence factory"""
        seq = create_training_sequence(TrainingSequenceType.NORMAL)
        assert seq is not None
        assert seq.sequence_type == TrainingSequenceType.NORMAL
    
    def test_get_dfi_training_command(self):
        """Test get_dfi_training_command mapping"""
        cmd = get_dfi_training_command('WRLVL')
        assert cmd == DFITrainingCommand.WRLVL_REQ

        cmd = get_dfi_training_command('RDGD')
        assert cmd == DFITrainingCommand.RDGD_REQ

        cmd = get_dfi_training_command('MGCAL_VREF')
        assert cmd == DFITrainingCommand.VREF_REQ

        cmd = get_dfi_training_command('UNKNOWN')
        assert cmd == DFITrainingCommand.NOP


# === Tap Coefficient Tests ===

from model.phy.tap_coefficient import (
    CoefficientType,
    TXCoefficients,
    RXCoefficients,
    LaneCoefficients,
    CompleteTapCoefficients,
    CoefficientOptimizer,
    CoefficientComparator,
    create_default_coefficients,
    export_coefficients_to_dict,
    import_coefficients_from_dict,
)


class TestTXCoefficients:
    """Test TX coefficients"""
    
    def test_initial_taps(self):
        """Test initial TX tap values"""
        tx = TXCoefficients()
        
        assert tx.main_cursor == 1.0
        assert len(tx.pre_cursor) == 2
        assert len(tx.post_cursor) == 2
    
    def test_set_taps(self):
        """Test setting TX taps"""
        tx = TXCoefficients()
        tx.set_taps([0.1, 0.2], [0.15, 0.05])
        
        assert len(tx.pre_cursor) == 2
        assert len(tx.post_cursor) == 2
    
    def test_normalize(self):
        """Test TX tap normalization"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.1, 0.1]
        tx.post_cursor = [0.1, 0.1]
        
        scale = tx.normalize()
        
        assert abs(tx.main_cursor) > 0
    
    def test_boost_calculation(self):
        """Test high-frequency boost calculation"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.2, 0.1]
        tx.post_cursor = [0.15, 0.05]
        
        boost = tx.calculate_boost_db()
        assert boost >= 0
    
    def test_to_fir_coeffs(self):
        """Test converting to FIR coefficients"""
        tx = TXCoefficients()
        fir = tx.to_fir_coeffs()
        
        assert isinstance(fir, np.ndarray)
        assert len(fir) == tx.total_taps
    
    def test_copy(self):
        """Test TX coefficient copy"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.1, 0.2]
        
        tx_copy = tx.copy()
        assert tx_copy.pre_cursor == [0.1, 0.2]


class TestRXCoefficients:
    """Test RX coefficients"""
    
    def test_initial_vref(self):
        """Test initial VREF value"""
        rx = RXCoefficients()
        assert rx.vref == 32
    
    def test_set_vref(self):
        """Test setting VREF"""
        rx = RXCoefficients()
        rx.set_vref(45)
        assert rx.vref == 45
    
    def test_vref_clamping(self):
        """Test VREF value clamping"""
        rx = RXCoefficients()
        rx.set_vref(100)  # Too high
        assert rx.vref == 63
        
        rx.set_vref(-10)  # Too low
        assert rx.vref == 0
    
    def test_ctle_transfer(self):
        """Test CTLE transfer function calculation"""
        rx = RXCoefficients()
        freq = np.linspace(1e9, 20e9, 100)
        
        H = rx.calculate_ctle_transfer(freq)
        
        assert isinstance(H, np.ndarray)
        assert len(H) == len(freq)
    
    def test_set_dfe_taps(self):
        """Test setting DFE taps"""
        rx = RXCoefficients()
        rx.set_dfe_taps([0.1, 0.2, 0.05, 0.0, -0.05])
        
        assert len(rx.dfe_taps) == 5
        assert all(abs(t) <= rx.dfe_max_tap_magnitude for t in rx.dfe_taps)
    
    def test_copy(self):
        """Test RX coefficient copy"""
        rx = RXCoefficients()
        rx.vref = 40
        rx.ctle_dc_gain_db = 3.0
        
        rx_copy = rx.copy()
        assert rx_copy.vref == 40
        assert rx_copy.ctle_dc_gain_db == 3.0


class TestLaneCoefficients:
    """Test lane coefficients"""
    
    def test_initial_lane_count(self):
        """Test initial lane count"""
        lane = LaneCoefficients()
        assert lane.num_lanes == 64
    
    def test_custom_lane_count(self):
        """Test custom lane count"""
        lane = LaneCoefficients(num_lanes=32)
        assert lane.num_lanes == 32
    
    def test_set_rd_delay(self):
        """Test setting read delay"""
        lane = LaneCoefficients()
        lane.set_rd_delay(0, 42)
        
        assert lane.rd_delays[0] == 42
    
    def test_rd_delay_clamping(self):
        """Test read delay clamping"""
        lane = LaneCoefficients()
        lane.set_rd_delay(0, 100)  # Too high
        assert lane.rd_delays[0] == 63
        
        lane.set_rd_delay(0, -5)  # Too low
        assert lane.rd_delays[0] == 0


class TestCompleteTapCoefficients:
    """Test complete tap coefficients"""
    
    def test_initial_coefficients(self):
        """Test initial complete coefficients"""
        coeffs = CompleteTapCoefficients()
        
        assert coeffs.tx is not None
        assert coeffs.rx is not None
        assert coeffs.lane is not None
    
    def test_validity_check(self):
        """Test validity check"""
        coeffs = CompleteTapCoefficients()
        
        # Valid
        assert coeffs.is_valid() is True
        
        # Invalid VREF
        coeffs.rx.vref = 100
        assert coeffs.is_valid() is False
    
    def test_copy(self):
        """Test complete coefficient copy"""
        coeffs = CompleteTapCoefficients()
        coeffs.channel_id = 5
        
        coeffs_copy = coeffs.copy()
        assert coeffs_copy.channel_id == 5


class TestCoefficientOptimizer:
    """Test coefficient optimizer"""
    
    def test_initialization(self):
        """Test optimizer initialization"""
        opt = CoefficientOptimizer()
        assert opt is not None
        assert opt.lms_mu == 0.01
    
    def test_vref_binary_search(self):
        """Test VREF binary search optimization"""
        opt = CoefficientOptimizer()
        
        # Simple margin function (optimal at vref=40)
        def measure_func(vref):
            return 1.0 - abs(vref - 40) / 40
        
        best_vref = opt.optimize_vref_binary_search(measure_func)
        
        assert 35 <= best_vref <= 45  # Should be close to 40
    
    def test_delay_sweep(self):
        """Test delay sweep optimization"""
        opt = CoefficientOptimizer()
        
        # Simple margin function
        def measure_func(delay):
            return 1.0 - abs(delay - 30) / 30
        
        best_delay, best_margin = opt.optimize_delay_sweep(
            range(64), measure_func
        )
        
        assert 25 <= best_delay <= 35
        assert best_margin > 0
    
    def test_convergence_history(self):
        """Test convergence history tracking"""
        opt = CoefficientOptimizer()
        opt._error_history = [0.1, 0.05, 0.02, 0.01]
        
        history = opt.get_convergence_history()
        assert len(history) == 4


class TestCoefficientSerialization:
    """Test coefficient serialization"""
    
    def test_export_to_dict(self):
        """Test exporting to dictionary"""
        coeffs = create_default_coefficients(channel_id=3)
        data = export_coefficients_to_dict(coeffs)
        
        assert 'channel_id' in data
        assert 'tx' in data
        assert 'rx' in data
        assert data['channel_id'] == 3
    
    def test_import_from_dict(self):
        """Test importing from dictionary"""
        data = {
            'channel_id': 7,
            'training_complete': True,
            'tx': {
                'pre_cursor': [0.1, 0.2],
                'main_cursor': 1.0,
                'post_cursor': [0.15, 0.05],
            },
            'rx': {
                'vref': 40,
                'dfe_taps': [0.1, 0.2, 0.05, 0.0, -0.05],
            },
        }
        
        coeffs = import_coefficients_from_dict(data)
        
        assert coeffs.channel_id == 7
        assert coeffs.rx.vref == 40
        assert coeffs.training_complete is True
    
    def test_roundtrip(self):
        """Test export and import roundtrip"""
        original = create_default_coefficients(channel_id=10)
        original.rx.vref = 45
        original.tx.pre_cursor = [0.1, 0.2]
        
        data = export_coefficients_to_dict(original)
        restored = import_coefficients_from_dict(data)
        
        assert restored.channel_id == original.channel_id
        assert restored.rx.vref == original.rx.vref
        assert restored.tx.pre_cursor == original.tx.pre_cursor


class TestCoefficientComparator:
    """Test coefficient comparison"""
    
    def test_compare_tx(self):
        """Test TX coefficient comparison"""
        tx1 = TXCoefficients()
        tx2 = TXCoefficients()
        tx2.pre_cursor = [0.1, 0.2]
        
        result = CoefficientComparator.compare(tx1, tx2)
        
        assert 'max_difference' in result
        assert 'mean_difference' in result
    
    def test_compare_rx(self):
        """Test RX coefficient comparison"""
        rx1 = RXCoefficients()
        rx2 = RXCoefficients()
        rx2.vref = 40

        result = CoefficientComparator.compare_rx(rx1, rx2)

        assert 'vref_diff' in result
        assert result['vref_diff'] == -8  # rx1.vref - rx2.vref = 32 - 40 = -8


class TestFactoryFunctions:
    """Test factory functions"""
    
    def test_create_default_coefficients(self):
        """Test create_default_coefficients"""
        coeffs = create_default_coefficients(channel_id=5)
        
        assert coeffs.channel_id == 5
        assert coeffs.tx.main_cursor == 1.0
        assert coeffs.rx.vref == 32


if __name__ == '__main__':
    pytest.main([__file__, '-v'])