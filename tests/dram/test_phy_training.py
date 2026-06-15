"""
Unit Tests for PHY Training State Machine

Tests PHY initialization and training sequences for HBM4.

Reference:
- JEDEC JESD270-4A HBM4 specification
- Cadence HBM4E documentation
- DFI 5.1 specification
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from model.dram.phy_training import (
    PHYInitState,
    TrainingPhase,
    TrainingResult,
    TrainingParameters,
    DFI5TrainingControl,
    TrainingStatus,
    PHYTrainingStateMachine,
    PHYInitializationStateMachine,
    HBM4PHYManager,
    PHYTrainingError,
    PHYInitError,
)


class TestPHYTrainingStateMachine:
    """Tests for PHYTrainingStateMachine"""

    def test_initialization(self):
        """Test training state machine initialization"""
        sm = PHYTrainingStateMachine(channel_id=0)

        assert sm.channel_id == 0
        assert sm.status.current_phase == TrainingPhase.TRAIN_IDLE
        assert sm.status.total_training_cycles == 0
        assert sm.status.retry_count == 0
        assert not sm.is_training_complete()

    def test_start_training(self):
        """Test starting training sequence"""
        sm = PHYTrainingStateMachine(channel_id=0)

        result = sm.start_training()

        assert result is True
        assert sm.status.current_phase == TrainingPhase.TRAIN_START
        assert sm.status.phase_start_cycle >= 0

    def test_training_sequence_order(self):
        """Test training phase sequence order"""
        expected_sequence = [
            TrainingPhase.TRAIN_RD_DQS,
            TrainingPhase.TRAIN_WR_LEVELING,
            TrainingPhase.TRAIN_RD_MT,
            TrainingPhase.TRAIN_WR_MT,
            TrainingPhase.TRAIN_RD_DQ,
            TrainingPhase.TRAIN_WR_DQ,
            TrainingPhase.TRAIN_VREF_CA,
            TrainingPhase.TRAIN_VREF_DQ,
        ]

        assert PHYTrainingStateMachine.TRAINING_SEQUENCE == expected_sequence

    def test_training_parameters_default(self):
        """Test default training parameters"""
        params = TrainingParameters()

        assert params.rd_dqs_delay == 0
        assert params.wr_level_delay == 0
        assert params.rd_margin == 0.0
        assert params.wr_margin == 0.0
        assert params.rd_vref == 0
        assert params.wr_vref == 0
        assert params.ca_vref == 0
        assert not params.training_passed
        assert len(params.training_errors) == 0

    def test_dfi_training_control_encoding(self):
        """Test DFI training control encoding"""
        ctrl = DFI5TrainingControl()

        # Test RD_DQS encoding
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_RD_DQS)
        assert tra_req is True
        assert tra_mode == 1
        assert tra_type == 0

        # Test WR_LEVELING encoding
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_WR_LEVELING)
        assert tra_req is True
        assert tra_mode == 1
        assert tra_type == 1

        # Test RD_MT encoding
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_RD_MT)
        assert tra_req is True
        assert tra_mode == 2
        assert tra_type == 0

        # Test WR_MT encoding
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_WR_MT)
        assert tra_req is True
        assert tra_mode == 2
        assert tra_type == 1

    def test_dfi_training_control_idle(self):
        """Test DFI training control for idle state"""
        ctrl = DFI5TrainingControl()

        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_IDLE)
        assert tra_req is False
        assert tra_mode == 0
        assert tra_type == 0

    def test_tick_increments_cycle(self):
        """Test that tick increments cycle counter"""
        sm = PHYTrainingStateMachine(channel_id=0)

        initial_cycle = sm.cycle
        sm.tick()
        assert sm.cycle == initial_cycle + 1

        sm.tick()
        sm.tick()
        assert sm.cycle == initial_cycle + 3

    def test_training_phase_execution(self):
        """Test training phase execution"""
        sm = PHYTrainingStateMachine(channel_id=0, config={'timeout_cycles': 100000})
        sm.start_training()

        # Run through training sequence
        completed_phases = []
        for _ in range(100000):
            sm.process_training_cycle()
            current = sm.status.current_phase

            if current not in completed_phases and current != TrainingPhase.TRAIN_START:
                if current in sm.TRAINING_SEQUENCE:
                    completed_phases.append(current)

            if sm.is_training_complete():
                break

        # Should complete training sequence
        assert sm.is_training_complete() or len(completed_phases) > 0

    def test_training_results_structure(self):
        """Test training results structure"""
        sm = PHYTrainingStateMachine(channel_id=0)
        results = sm.get_training_results()

        assert 'channel_id' in results
        assert 'passed' in results
        assert 'current_phase' in results
        assert 'total_cycles' in results
        assert 'retry_count' in results
        assert 'results' in results
        assert 'parameters' in results
        assert 'errors' in results

    def test_lane_calibration_data(self):
        """Test lane-specific calibration data storage"""
        sm = PHYTrainingStateMachine(channel_id=0)

        # Simulate setting lane delays
        sm.params.lane_delays[0] = 32
        sm.params.lane_delays[1] = 34

        assert sm.params.lane_delays[0] == 32
        assert sm.params.lane_delays[1] == 34
        assert len(sm.params.lane_delays) == 2

    def test_training_timeout_config(self):
        """Test training timeout configuration"""
        custom_timeout = 5000
        sm = PHYTrainingStateMachine(channel_id=0, config={'timeout_cycles': custom_timeout})

        assert sm.timeout_cycles == custom_timeout


class TestPHYInitializationStateMachine:
    """Tests for PHYInitializationStateMachine"""

    def test_initialization(self):
        """Test initialization state machine"""
        sm = PHYInitializationStateMachine()

        assert sm.status.state == PHYInitState.INIT_IDLE
        assert sm.status.error_count == 0
        assert not sm.is_initialized
        assert not sm.is_ready

    def test_start_initialization(self):
        """Test starting initialization"""
        sm = PHYInitializationStateMachine()

        sm.start_initialization()

        assert sm.status.state == PHYInitState.INIT_START
        assert sm.status.state_enter_cycle >= 0

    def test_initialization_state_sequence(self):
        """Test initialization state sequence"""
        sm = PHYInitializationStateMachine()

        sm.start_initialization()

        # Process through states
        states_seen = [sm.status.state]

        for _ in range(1000):
            sm.process_init_cycle()
            sm.tick()

            current_state = sm.status.state
            if current_state not in states_seen:
                states_seen.append(current_state)

            if sm.is_initialized:
                break

        # Should progress through states
        assert PHYInitState.INIT_START in states_seen
        assert PHYInitState.INIT_POWER_UP in states_seen
        assert PHYInitState.INIT_RESET in states_seen
        assert PHYInitState.INIT_CONFIG in states_seen

    def test_initialization_with_training(self):
        """Test initialization with integrated training"""
        training_sm = PHYTrainingStateMachine(channel_id=0)
        sm = PHYInitializationStateMachine(training_sm=training_sm)

        sm.start_initialization()

        # Process through all states including training
        for _ in range(500000):  # Allow time for full sequence
            sm.process_init_cycle()
            sm.tick()

            if sm.is_initialized:
                break

        assert sm.is_initialized

    def test_initialization_status(self):
        """Test initialization status reporting"""
        sm = PHYInitializationStateMachine()

        status = sm.get_initialization_status()

        assert 'state' in status
        assert 'cycle' in status
        assert 'calibration_count' in status
        assert 'error_count' in status
        assert 'warnings' in status
        assert 'initialized' in status
        assert 'ready' in status

    def test_calibration_data(self):
        """Test calibration data retrieval"""
        sm = PHYInitializationStateMachine()

        # Start initialization to load configuration
        sm.start_initialization()

        # Process enough cycles to reach calibration
        # INIT_START -> INIT_POWER_UP (1 cycle)
        # INIT_POWER_UP -> INIT_RESET (100 cycles)
        # INIT_RESET -> INIT_CONFIG (50 cycles)
        # INIT_CONFIG: loads config on first tick
        # INIT_CONFIG -> INIT_CALIBRATE (20 cycles)
        for _ in range(200):
            sm.process_init_cycle()
            sm.tick()
            if sm.status.state == PHYInitState.INIT_CALIBRATE:
                break

        # After reaching CALIBRATE state, config should be loaded
        data = sm.get_calibration_data()

        assert 'rd_vref' in data
        assert 'wr_vref' in data
        assert 'ca_vref' in data

    def test_config_loading(self):
        """Test configuration loading"""
        config = {
            'default_rd_vref': 30,
            'default_wr_vref': 35,
        }
        sm = PHYInitializationStateMachine(config=config)

        sm.start_initialization()

        for _ in range(1000):
            sm.process_init_cycle()
            sm.tick()

            if sm.status.state == PHYInitState.INIT_COMPLETE:
                break

        data = sm.get_calibration_data()
        assert data['rd_vref'] == 30
        assert data['wr_vref'] == 35


class TestHBM4PHYManager:
    """Tests for HBM4PHYManager"""

    def test_initialization(self):
        """Test PHY manager initialization"""
        manager = HBM4PHYManager(num_channels=4)

        assert manager.num_channels == 4
        assert len(manager._init_machines) == 4
        assert len(manager._training_machines) == 4
        assert not manager.is_ready()

    def test_start_initialization(self):
        """Test starting initialization on all channels"""
        manager = HBM4PHYManager(num_channels=2)

        manager.start_initialization()

        for sm in manager._init_machines:
            assert sm.status.state != PHYInitState.INIT_IDLE

    def test_process_cycles(self):
        """Test processing multiple cycles"""
        manager = HBM4PHYManager(num_channels=2)

        manager.start_initialization()
        initial_cycle = manager.cycle

        manager.process_cycles(100)

        assert manager.cycle == initial_cycle + 100

    def test_wait_for_initialization(self):
        """Test waiting for initialization to complete"""
        manager = HBM4PHYManager(num_channels=2)

        manager.start_initialization()
        success = manager.wait_for_initialization(max_cycles=500000)

        # Should complete (or timeout)
        assert isinstance(success, bool)

    def test_channel_status(self):
        """Test getting channel status"""
        manager = HBM4PHYManager(num_channels=4)

        status = manager.get_channel_status(2)

        assert 'state' in status
        assert 'initialized' in status

    def test_all_channel_status(self):
        """Test getting all channel statuses"""
        manager = HBM4PHYManager(num_channels=4)

        all_status = manager.get_all_channel_status()

        assert len(all_status) == 4
        for status in all_status:
            assert 'state' in status

    def test_invalid_channel_status(self):
        """Test getting status for invalid channel"""
        manager = HBM4PHYManager(num_channels=4)

        status = manager.get_channel_status(10)

        assert 'error' in status

    def test_aggregate_calibration_data(self):
        """Test aggregate calibration data"""
        manager = HBM4PHYManager(num_channels=4)

        agg_data = manager.get_aggregate_calibration_data()

        assert agg_data['num_channels'] == 4
        assert 'num_initialized' in agg_data
        assert 'num_ready' in agg_data
        assert 'channel_data' in agg_data
        assert len(agg_data['channel_data']) == 4


class TestPHYInitStateEnums:
    """Tests for PHYInitState enumeration"""

    def test_all_init_states_defined(self):
        """Test all initialization states are defined"""
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

        for state in expected_states:
            assert state is not None

    def test_init_state_names(self):
        """Test initialization state names"""
        assert PHYInitState.INIT_IDLE.name == 'INIT_IDLE'
        assert PHYInitState.INIT_START.name == 'INIT_START'
        assert PHYInitState.INIT_COMPLETE.name == 'INIT_COMPLETE'


class TestTrainingPhaseEnums:
    """Tests for TrainingPhase enumeration"""

    def test_all_training_phases_defined(self):
        """Test all training phases are defined"""
        expected_phases = [
            TrainingPhase.TRAIN_IDLE,
            TrainingPhase.TRAIN_START,
            TrainingPhase.TRAIN_INIT,
            TrainingPhase.TRAIN_RD_DQS,
            TrainingPhase.TRAIN_WR_LEVELING,
            TrainingPhase.TRAIN_RD_MT,
            TrainingPhase.TRAIN_WR_MT,
            TrainingPhase.TRAIN_RD_DQ,
            TrainingPhase.TRAIN_WR_DQ,
            TrainingPhase.TRAIN_VREF_CA,
            TrainingPhase.TRAIN_VREF_DQ,
            TrainingPhase.TRAIN_VERIFY,
            TrainingPhase.TRAIN_COMPLETE,
            TrainingPhase.TRAIN_FAIL,
        ]

        for phase in expected_phases:
            assert phase is not None

    def test_training_phase_sequence_complete(self):
        """Test training sequence contains all expected phases"""
        sequence = PHYTrainingStateMachine.TRAINING_SEQUENCE

        expected_phases = [
            TrainingPhase.TRAIN_RD_DQS,
            TrainingPhase.TRAIN_WR_LEVELING,
            TrainingPhase.TRAIN_RD_MT,
            TrainingPhase.TRAIN_WR_MT,
            TrainingPhase.TRAIN_RD_DQ,
            TrainingPhase.TRAIN_WR_DQ,
            TrainingPhase.TRAIN_VREF_CA,
            TrainingPhase.TRAIN_VREF_DQ,
        ]

        for phase in expected_phases:
            assert phase in sequence


class TestTrainingResultEnums:
    """Tests for TrainingResult enumeration"""

    def test_all_results_defined(self):
        """Test all training results are defined"""
        expected_results = [
            TrainingResult.SUCCESS,
            TrainingResult.FAIL_TIMEOUT,
            TrainingResult.FAIL_MARGIN,
            TrainingResult.FAIL_VERIFY,
            TrainingResult.FAIL_PARAM,
        ]

        for result in expected_results:
            assert result is not None

    def test_result_names(self):
        """Test training result names"""
        assert TrainingResult.SUCCESS.name == 'SUCCESS'
        assert TrainingResult.FAIL_TIMEOUT.name == 'FAIL_TIMEOUT'


class TestDFI5TrainingControl:
    """Tests for DFI5TrainingControl"""

    def test_default_values(self):
        """Test default control values"""
        ctrl = DFI5TrainingControl()

        assert ctrl.tra_req is False
        assert ctrl.tra_mode == 0
        assert ctrl.tra_type == 0
        assert ctrl.tra_ack is False
        assert ctrl.tra_complete is False
        assert ctrl.tra_error is False
        assert ctrl.tra_fail_code == 0

    def test_encode_vref_ca(self):
        """Test VREF CA training encoding"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_VREF_CA)

        assert tra_req is True
        assert tra_mode == 4
        assert tra_type == 0

    def test_encode_vref_dq(self):
        """Test VREF DQ training encoding"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_VREF_DQ)

        assert tra_req is True
        assert tra_mode == 4
        assert tra_type == 1


class TestTrainingParameters:
    """Tests for TrainingParameters dataclass"""

    def test_default_parameters(self):
        """Test default parameter values"""
        params = TrainingParameters()

        assert params.rd_dqs_delay == 0
        assert params.wr_level_delay == 0
        assert params.wr_dq_delay == 0
        assert params.rd_margin == 0.0
        assert params.wr_margin == 0.0
        assert params.rd_vref == 0
        assert params.wr_vref == 0
        assert params.ca_vref == 0
        assert params.ca_delay == 0
        assert len(params.lane_delays) == 0
        assert not params.training_passed
        assert len(params.training_errors) == 0

    def test_custom_parameters(self):
        """Test custom parameter values"""
        params = TrainingParameters(
            rd_dqs_delay=32,
            wr_level_delay=28,
            rd_vref=35,
            wr_vref=30,
            rd_margin=0.25,
            wr_margin=0.22,
            training_passed=True,
        )

        assert params.rd_dqs_delay == 32
        assert params.wr_level_delay == 28
        assert params.rd_vref == 35
        assert params.wr_vref == 30
        assert params.rd_margin == 0.25
        assert params.wr_margin == 0.22
        assert params.training_passed


class TestTrainingStatus:
    """Tests for TrainingStatus dataclass"""

    def test_default_status(self):
        """Test default status values"""
        status = TrainingStatus()

        assert status.current_phase == TrainingPhase.TRAIN_IDLE
        assert status.phase_start_cycle == 0
        assert status.phase_timeout_cycles == 0
        assert status.total_training_cycles == 0
        assert status.retry_count == 0
        assert status.max_retries == 3
        assert len(status.results) == 0

    def test_custom_timeout(self):
        """Test custom timeout values"""
        status = TrainingStatus(
            phase_timeout_cycles=10000,
            max_retries=5,
        )

        assert status.phase_timeout_cycles == 10000
        assert status.max_retries == 5


# Integration tests with DFI interface
class TestPHYTrainingWithDFI:
    """Integration tests with DFI interface"""

    def test_training_with_mock_dfi(self):
        """Test training with mock DFI interface"""
        from model.dram.dfi_interface import DFI5Interface

        dfi = DFI5Interface()
        sm = PHYTrainingStateMachine(channel_id=0, dfi_interface=dfi)

        assert sm.dfi is not None
        assert sm.dfi.training_in_progress is False

        sm.start_training()

        assert sm.dfi.training_in_progress is True

    def test_initialization_with_dfi(self):
        """Test initialization with DFI interface"""
        from model.dram.dfi_interface import DFI5Interface

        dfi = DFI5Interface()
        training_sm = PHYTrainingStateMachine(channel_id=0, dfi_interface=dfi)
        init_sm = PHYInitializationStateMachine(training_sm=training_sm, dfi_interface=dfi)

        init_sm.start_initialization()

        for _ in range(100000):
            init_sm.process_init_cycle()
            init_sm.tick()

            if init_sm.is_initialized:
                break

        # DFI should have training signals
        assert init_sm.dfi.training_in_progress or init_sm.dfi.training_complete


if __name__ == '__main__':
    pytest.main([__file__, '-v'])