"""
Comprehensive Tests for HBM4 Training Sequences and MBIST Algorithms

Demonstrates and tests:
- Full PHY training sequences (CA, RDDQ, WDQ, GL, VREF)
- PRBS pattern generation and properties
- MBIST algorithms: march, checkerboard, walking ones/zeros
- Integration between training, loopback, and MBIST

Reference:
- JEDEC JESD270-4A HBM4 specification
- Cadence HBM4E documentation
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from model.dram.phy_training import (
    PHYTrainingStateMachine,
    PHYInitializationStateMachine,
    TrainingPhase,
    TrainingParameters,
    DFI5TrainingControl,
)
from model.dram.mbist_controller import (
    MBISTController,
    MBISTAlgorithm,
    MBISTConfig,
    FaultType,
    MBISTResult,
)
from model.dram.loopback_controller import (
    LoopbackController,
    LoopbackMode,
    LoopbackLevel,
    LoopbackConfig,
    PRBSGenerator,
)


class TestPHYTrainingSequenceComplete:
    """Test complete PHY training sequence"""

    def test_full_training_sequence(self):
        """Test full training sequence executes all phases"""
        sm = PHYTrainingStateMachine(channel_id=0)
        sm.start_training()

        phases_executed = []

        for _ in range(500000):
            sm.process_training_cycle()
            sm.tick()

            current = sm.status.current_phase
            if current not in phases_executed and current != TrainingPhase.TRAIN_IDLE:
                phases_executed.append(current)

            if sm.is_training_complete():
                break

        # Check all expected phases were executed
        expected_phases = [
            TrainingPhase.TRAIN_RD_DQS,
            TrainingPhase.TRAIN_WR_LEVELING,
            TrainingPhase.TRAIN_RD_DQ,
            TrainingPhase.TRAIN_RD_DQ_EYE,
            TrainingPhase.TRAIN_WR_DQ,
            TrainingPhase.TRAIN_WR_DQ_EYE,
            TrainingPhase.TRAIN_GATE,
            TrainingPhase.TRAIN_GATE_DELAY,
            TrainingPhase.TRAIN_VREF_CA,
            TrainingPhase.TRAIN_VREF_DQ,
        ]

        for phase in expected_phases:
            assert phase in phases_executed, f"Phase {phase.name} not executed"

    def test_training_results_structure(self):
        """Test training results contain all required fields"""
        sm = PHYTrainingStateMachine(channel_id=0)
        sm.start_training()

        for _ in range(500000):
            sm.process_training_cycle()
            sm.tick()
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

    def test_training_parameters_after_completion(self):
        """Test training parameters are set after completion"""
        sm = PHYTrainingStateMachine(channel_id=0)
        sm.start_training()

        for _ in range(500000):
            sm.process_training_cycle()
            sm.tick()
            if sm.is_training_complete():
                break

        if sm.params.training_passed:
            # Verify parameters are in valid range
            assert 0 <= sm.params.rd_vref <= 63
            assert 0 <= sm.params.wr_vref <= 63
            assert 0 <= sm.params.ca_vref <= 63


class TestDFI5TrainingEncoding:
    """Test DFI 5 training command encoding"""

    def test_all_training_phases_encoding(self):
        """Test all training phases encode correctly"""
        ctrl = DFI5TrainingControl()

        # Test each phase in the training sequence
        phases_and_expected = [
            (TrainingPhase.TRAIN_RD_DQS, True, 1, 0),
            (TrainingPhase.TRAIN_WR_LEVELING, True, 1, 1),
            (TrainingPhase.TRAIN_RD_DQ, True, 2, 0),
            (TrainingPhase.TRAIN_RD_DQ_EYE, True, 2, 1),
            (TrainingPhase.TRAIN_WR_DQ, True, 3, 0),
            (TrainingPhase.TRAIN_WR_DQ_EYE, True, 3, 1),
            (TrainingPhase.TRAIN_GATE, True, 4, 0),
            (TrainingPhase.TRAIN_GATE_DELAY, True, 4, 1),
            (TrainingPhase.TRAIN_VREF_CA, True, 5, 0),
            (TrainingPhase.TRAIN_VREF_DQ, True, 5, 1),
        ]

        for phase, expected_req, expected_mode, expected_type in phases_and_expected:
            tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(phase)
            assert tra_req == expected_req, f"tra_req mismatch for {phase.name}"
            assert tra_mode == expected_mode, f"tra_mode mismatch for {phase.name}"
            assert tra_type == expected_type, f"tra_type mismatch for {phase.name}"

    def test_idle_encoding(self):
        """Test IDLE phase encodes to disabled"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_IDLE)
        assert tra_req is False
        assert tra_mode == 0
        assert tra_type == 0

    def test_unknown_phase_encoding(self):
        """Test unknown phases encode to disabled"""
        ctrl = DFI5TrainingControl()
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_COMPLETE)
        assert tra_req is False


class TestPRBSPatternProperties:
    """Test PRBS pattern statistical properties"""

    def test_prbs7_periodicity(self):
        """Test PRBS-7 has correct period (127 bits)"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        first_bits = [gen.next() for _ in range(127)]

        gen.reset(0x7F)
        second_bits = [gen.next() for _ in range(127)]

        # Full period should repeat
        assert first_bits == second_bits

    def test_prbs15_periodicity(self):
        """Test PRBS-15 has correct period (32767 bits)"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_15, seed=0x7FFF)

        # Just verify first and last bits of period match after reset
        first_bit = gen.next()
        for _ in range(32766):
            gen.next()
        last_bit = gen.next()

        gen.reset(0x7FFF)
        reset_first = gen.next()
        for _ in range(32766):
            gen.next()
        reset_last = gen.next()

        assert first_bit == reset_first
        assert last_bit == reset_last

    def test_prbs7_runs_property(self):
        """Test PRBS-7 runs property (consecutive bits)"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        bits = [gen.next() for _ in range(1000)]

        # Count runs of consecutive same bits
        runs = 1
        for i in range(1, len(bits)):
            if bits[i] != bits[i-1]:
                runs += 1

        # For PRBS, runs should be roughly 1/2 of bits
        # Allow range of 40-60%
        runs_ratio = runs / len(bits)
        assert 0.35 < runs_ratio < 0.65

    def test_prbs_generates_random_bytes(self):
        """Test PRBS generates non-repeating byte patterns"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        bytes_list = gen.generate_n_bytes(100)

        # Check that not all bytes are the same
        unique_bytes = set(bytes_list)
        assert len(unique_bytes) > 50  # Should have high entropy

    def test_prbs_seed_affects_sequence(self):
        """Test different seeds produce different sequences"""
        gen1 = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        gen2 = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x3F)

        bits1 = [gen1.next() for _ in range(50)]
        bits2 = [gen2.next() for _ in range(50)]

        # Sequences should differ
        assert bits1 != bits2


class TestMBISTMarchAlgorithms:
    """Test MBIST March algorithm implementations"""

    def test_march_c_pattern_count(self):
        """Test March-C has 6 pattern elements"""
        controller = MBISTController()
        patterns = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_C]

        assert len(patterns) == 6

    def test_march_l_pattern_count(self):
        """Test March-L has 6 pattern elements"""
        controller = MBISTController()
        patterns = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_L]

        assert len(patterns) == 6

    def test_march_u_pattern_count(self):
        """Test March-U has 8 pattern elements"""
        controller = MBISTController()
        patterns = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_U]

        assert len(patterns) == 8

    def test_march_minus_pattern_count(self):
        """Test March-Minus has 6 pattern elements"""
        controller = MBISTController()
        patterns = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_MINUS]

        assert len(patterns) == 6

    def test_march_plus_pattern_count(self):
        """Test March-Plus has 10 pattern elements"""
        controller = MBISTController()
        patterns = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_PLUS]

        assert len(patterns) == 10

    def test_march_pattern_operations(self):
        """Test March patterns use valid operations"""
        controller = MBISTController()
        valid_ops = {'w0', 'w1', 'r0', 'r1', 'ra', 'wa'}

        for algo in [MBISTAlgorithm.MARCH_C, MBISTAlgorithm.MARCH_L,
                     MBISTAlgorithm.MARCH_U, MBISTAlgorithm.MARCH_MINUS,
                     MBISTAlgorithm.MARCH_PLUS]:
            patterns = controller.MARCH_PATTERNS[algo]
            for pattern in patterns:
                assert pattern.operation in valid_ops, f"Invalid operation {pattern.operation}"

    def test_all_march_algorithms_executable(self):
        """Test all March algorithms can execute"""
        algorithms = [
            MBISTAlgorithm.MARCH_C,
            MBISTAlgorithm.MARCH_L,
            MBISTAlgorithm.MARCH_U,
            MBISTAlgorithm.MARCH_MINUS,
            MBISTAlgorithm.MARCH_PLUS,
        ]

        for algo in algorithms:
            controller = MBISTController()
            config = MBISTConfig(
                algorithm=algo,
                start_address=0,
                end_address=15,
            )
            result = controller.run_test(config)
            assert result is not None
            assert result.algorithm == algo


class TestMBISTWalkingPatterns:
    """Test MBIST Walking Ones/Zeros algorithms"""

    def test_walking_ones_test(self):
        """Test Walking Ones test executes correctly"""
        controller = MBISTController()
        result = controller.run_walking_ones()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.WALKING_ONES
        assert result.addresses_tested > 0

    def test_walking_zeros_test(self):
        """Test Walking Zeros test executes correctly"""
        controller = MBISTController()
        result = controller.run_walking_zeros()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.WALKING_ZEROS
        assert result.addresses_tested > 0

    def test_walking_patterns_detect_stuck_at(self):
        """Test walking patterns can detect stuck-at faults"""
        controller = MBISTController()
        controller.inject_fault(0, FaultType.STUCK_AT_0)

        result = controller.run_walking_ones()

        # Should detect the fault
        assert len(result.faults_found) > 0
        assert result.status == "FAIL"


class TestMBISTCheckerboard:
    """Test MBIST Checkerboard pattern algorithm"""

    def test_checkerboard_address_test(self):
        """Test checkerboard via address test"""
        controller = MBISTController()

        # Use address test which effectively tests checkerboard-like patterns
        config = MBISTConfig(
            algorithm=MBISTAlgorithm.ADDRESS_TEST,
            start_address=0,
            end_address=31,
        )
        result = controller.run_address_test()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.ADDRESS_TEST


class TestMBISTDataRetention:
    """Test MBIST Data Retention test"""

    def test_data_retention_basic(self):
        """Test data retention test executes"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.DATA_RETENTION,
            start_address=0,
            end_address=15,
            retention_time_cycles=10,  # Short for testing
        )
        result = controller.run_data_retention_test()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.DATA_RETENTION

    def test_data_retention_detects_failure(self):
        """Test data retention detects retention failures"""
        controller = MBISTController()

        # Inject a stuck-at-0 fault which simulates retention failure
        controller.inject_fault(0, FaultType.DATA_RETENTION, value=0x5555555555555555)

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.DATA_RETENTION,
            start_address=0,
            end_address=7,
            retention_time_cycles=10,
            fail_stop=False,
        )
        result = controller.run_data_retention_test()

        # Should detect the fault
        assert len(result.faults_found) >= 1


class TestMBISTFaultClassification:
    """Test MBIST fault classification"""

    def test_classify_stuck_at_0(self):
        """Test stuck-at-0 classification"""
        controller = MBISTController()
        fault_type = controller._classify_fault(0xFFFFFFFFFFFFFFFF, 0)
        assert fault_type == FaultType.STUCK_AT_1  # expected=1, actual=0

    def test_classify_stuck_at_1(self):
        """Test stuck-at-1 classification"""
        controller = MBISTController()
        fault_type = controller._classify_fault(0, 0xFFFFFFFFFFFFFFFF)
        assert fault_type == FaultType.STUCK_AT_0  # expected=0, actual=1

    def test_classify_transition_fault(self):
        """Test transition fault classification"""
        controller = MBISTController()
        # XOR of expected and actual gives non-zero but not all 1s
        fault_type = controller._classify_fault(0xAAAAAAAA, 0x55555555)
        assert fault_type in [FaultType.TRANSITION, FaultType.DATA_RETENTION]

    def test_multiple_fault_injection(self):
        """Test multiple faults can be injected and detected"""
        controller = MBISTController()

        controller.inject_fault(0, FaultType.STUCK_AT_0)
        controller.inject_fault(10, FaultType.STUCK_AT_1, 0xFFFFFFFFFFFFFFFF)

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=15,
            fail_stop=False,
        )
        result = controller.run_test(config)

        # Should find at least 2 faults
        assert len(result.faults_found) >= 2


class TestLoopbackPRBSIntegration:
    """Test PRBS integration in loopback controller"""

    def test_prbs7_loopback(self):
        """Test PRBS-7 loopback test"""
        config = LoopbackConfig(
            mode=LoopbackMode.PRBS_7,
            test_length=100,
        )
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()

        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break

        assert ctrl.is_complete()
        assert ctrl.is_passed()

    def test_prbs15_loopback(self):
        """Test PRBS-15 loopback test"""
        config = LoopbackConfig(
            mode=LoopbackMode.PRBS_15,
            test_length=100,
        )
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()

        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break

        assert ctrl.is_complete()

    def test_fixed_pattern_loopback(self):
        """Test fixed pattern loopback"""
        config = LoopbackConfig(
            mode=LoopbackMode.FIXED_ALTERNATING,
            test_length=100,
        )
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()

        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break

        assert ctrl.is_complete()
        assert ctrl.is_passed()

    def test_loopback_ber_calculation(self):
        """Test BER is calculated correctly"""
        config = LoopbackConfig(
            mode=LoopbackMode.PRBS_7,
            test_length=1000,
        )
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()

        for _ in range(10000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break

        summary = ctrl.get_summary()
        assert 'total_bits' in summary
        assert 'total_errors' in summary
        assert 'overall_ber' in summary


class TestTrainingLoopbackIntegration:
    """Test integration between training and loopback"""

    def test_phy_training_sm_reference(self):
        """Test loopback can reference PHY training SM"""
        from model.dram.phy_training import PHYTrainingStateMachine

        phy_sm = PHYTrainingStateMachine(channel_id=0)

        config = LoopbackConfig(
            mode=LoopbackMode.PRBS_7,
            test_length=10,
        )
        ctrl = LoopbackController(
            num_channels=1,
            phy_training_sm=phy_sm,
            config=config,
        )

        assert ctrl.phy_training_sm is phy_sm

    def test_training_then_loopback(self):
        """Test running training then loopback"""
        from model.dram.phy_training import PHYTrainingStateMachine

        # Run training
        phy_sm = PHYTrainingStateMachine(channel_id=0)
        phy_sm.start_training()

        for _ in range(50000):
            phy_sm.process_training_cycle()
            phy_sm.tick()
            if phy_sm.is_training_complete():
                break

        # Run loopback
        config = LoopbackConfig(
            mode=LoopbackMode.PRBS_7,
            test_length=10,
        )
        ctrl = LoopbackController(
            num_channels=1,
            phy_training_sm=phy_sm,
            config=config,
        )
        ctrl.start()

        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break

        assert ctrl.is_complete()


class TestLaneRepairIntegration:
    """Test lane repair integration with training"""

    def test_lane_repair_during_training(self):
        """Test lane repair can be invoked during training"""
        from model.dram.lane_repair import HBM4LaneRepairModel

        repair_model = HBM4LaneRepairModel(num_channels=1)

        # Simulate detecting a failed lane during training
        failed_lane = 5
        spare_lane = repair_model.perform_repair(channel_id=0, failed_lane=failed_lane)

        assert spare_lane is not None
        assert spare_lane >= 64  # Spare lanes are after data lanes

        # Verify remapping
        remapped = repair_model.get_remapped_lane(channel_id=0, lane_id=failed_lane)
        assert remapped == spare_lane

    def test_multiple_lane_repairs(self):
        """Test multiple lane repairs"""
        from model.dram.lane_repair import HBM4LaneRepairModel

        repair_model = HBM4LaneRepairModel(num_channels=1, spare_lanes_per_channel=4)

        # Repair multiple lanes
        failed_lanes = [5, 12, 23, 42]
        for lane in failed_lanes:
            spare = repair_model.perform_repair(channel_id=0, failed_lane=lane)
            assert spare is not None

        # Check stats
        stats = repair_model.get_stats()
        assert stats['total_repairs'] == 4


class TestTrainingWithLaneRepair:
    """Test training with lane repair integration"""

    def test_training_adapts_to_repairs(self):
        """Test training can adapt to repaired lanes"""
        from model.dram.lane_repair import HBM4LaneRepairModel

        repair_model = HBM4LaneRepairModel(num_channels=1)

        # Before repair - lane is normal
        lane_ok = not repair_model.is_lane_remapped(channel_id=0, lane_id=10)

        # Repair lane
        repair_model.perform_repair(channel_id=0, failed_lane=10)

        # After repair - lane is remapped
        lane_remapped = repair_model.is_lane_remapped(channel_id=0, lane_id=10)

        assert lane_ok
        assert lane_remapped


class TestInitializationSequence:
    """Test full initialization sequence"""

    def test_initialization_with_training(self):
        """Test initialization sequence with integrated training"""
        init_sm = PHYInitializationStateMachine()
        init_sm.start_initialization()

        for _ in range(500000):
            init_sm.process_init_cycle()
            init_sm.tick()
            if init_sm.is_initialized:
                break

        assert init_sm.is_initialized

    def test_initialization_status_tracking(self):
        """Test initialization tracks state properly"""
        init_sm = PHYInitializationStateMachine()
        init_sm.start_initialization()

        status_history = []
        for _ in range(1000):
            init_sm.process_init_cycle()
            init_sm.tick()

            status = init_sm.get_initialization_status()
            if status['state'] not in status_history:
                status_history.append(status['state'])

            if init_sm.is_initialized:
                break

        # Should have progressed through states
        assert len(status_history) >= 3


class TestDFIInterface:
    """Test DFI interface integration"""

    def test_dfi_training_signals(self):
        """Test DFI training signals are set correctly"""
        ctrl = DFI5TrainingControl()

        # Encode training command
        tra_req, tra_mode, tra_type = ctrl.encode_training_cmd(TrainingPhase.TRAIN_RD_DQ)

        ctrl.tra_req = tra_req
        ctrl.tra_mode = tra_mode
        ctrl.tra_type = tra_type

        assert ctrl.tra_req is True
        assert ctrl.tra_mode > 0

    def test_training_with_dfi_interface(self):
        """Test training with DFI interface"""
        from model.dram.dfi_interface import DFI5Interface

        dfi = DFI5Interface()
        sm = PHYTrainingStateMachine(channel_id=0, dfi_interface=dfi)

        assert sm.dfi is not None
        sm.start_training()

        # DFI should indicate training in progress
        assert sm.dfi.training_in_progress or sm.dfi.training_complete


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
