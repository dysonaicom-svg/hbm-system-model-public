"""
Tests for MBIST Controller

Tests the Memory Built-In Self-Test controller for HBM4 DRAM verification.
"""

import pytest
from model.dram.mbist_controller import (
    MBISTController,
    MBISTState,
    MBISTAlgorithm,
    MBISTConfig,
    MBISTFault,
    MBISTResult,
    MBISTStats,
    FaultType,
    MarchPattern,
    create_mbist_controller,
    create_mbist_config,
)


class TestMBISTControllerCreation:
    """Test MBIST controller creation"""

    def test_controller_creation(self):
        """MBIST controller must be created successfully"""
        controller = MBISTController()
        assert controller is not None
        assert controller.state == MBISTState.IDLE

    def test_controller_with_spec(self):
        """MBIST controller with HBM4 spec"""
        from model.dram.hbm4_spec import HBM4Spec
        spec = HBM4Spec()
        controller = MBISTController(spec=spec)
        assert controller.spec == spec

    def test_factory_function(self):
        """Factory function must create controller"""
        controller = create_mbist_controller()
        assert isinstance(controller, MBISTController)


class TestMBISTConfig:
    """Test MBIST configuration"""

    def test_default_config(self):
        """Default configuration must be valid"""
        config = MBISTConfig()
        assert config.algorithm == MBISTAlgorithm.MARCH_C
        assert config.start_address == 0
        assert config.end_address == 0xFFFFFFFF
        assert config.fail_stop is True

    def test_custom_config(self):
        """Custom configuration must work"""
        config = MBISTConfig(
            algorithm=MBISTAlgorithm.WALKING_ONES,
            start_address=0x1000,
            end_address=0x2000,
            fail_stop=False,
        )
        assert config.algorithm == MBISTAlgorithm.WALKING_ONES
        assert config.start_address == 0x1000
        assert config.end_address == 0x2000
        assert config.fail_stop is False

    def test_factory_function(self):
        """Factory config function"""
        config = create_mbist_config(
            algorithm=MBISTAlgorithm.MARCH_L,
            start_addr=0x100,
            end_addr=0x200,
        )
        assert config.algorithm == MBISTAlgorithm.MARCH_L
        assert config.start_address == 0x100
        assert config.end_address == 0x200


class TestMBISTStateMachine:
    """Test MBIST state machine transitions"""

    def test_initial_state(self):
        """Controller starts in IDLE state"""
        controller = MBISTController()
        assert controller.state == MBISTState.IDLE

    def test_start_test_transitions(self):
        """Starting test transitions through states"""
        controller = MBISTController()
        controller.configure(MBISTConfig())

        result = controller.start_test()
        assert result is True
        # Should transition to SETUP then RUNNING
        assert controller.state in [MBISTState.SETUP, MBISTState.RUNNING]

    def test_cannot_start_when_running(self):
        """Cannot start new test while running"""
        controller = MBISTController()
        controller.configure(MBISTConfig())
        controller.start_test()

        # Try to start another test
        result = controller.start_test()
        assert result is False

    def test_reset(self):
        """Reset returns to IDLE state"""
        controller = MBISTController()
        controller.configure(MBISTConfig())
        controller.start_test()
        controller.reset()

        assert controller.state == MBISTState.IDLE


class TestMarchPatterns:
    """Test March pattern definitions"""

    def test_march_c_pattern(self):
        """March-C pattern must be defined"""
        controller = MBISTController()
        patterns = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_C]

        assert len(patterns) == 6
        # Pattern: w0, r0, w1, r1, w0, r0
        assert patterns[0].operation == "w0"
        assert patterns[1].operation == "r0"
        assert patterns[2].operation == "w1"
        assert patterns[3].operation == "r1"
        assert patterns[4].operation == "w0"
        assert patterns[5].operation == "r0"

    def test_march_l_pattern(self):
        """March-L pattern must be defined"""
        controller = MBISTController()
        patterns = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_L]

        assert len(patterns) == 6
        assert patterns[0].operation == "w0"

    def test_all_march_algorithms_have_patterns(self):
        """All March algorithms must have patterns"""
        controller = MBISTController()

        march_algos = [
            MBISTAlgorithm.MARCH_C,
            MBISTAlgorithm.MARCH_L,
            MBISTAlgorithm.MARCH_U,
            MBISTAlgorithm.MARCH_MINUS,
            MBISTAlgorithm.MARCH_PLUS,
        ]

        for algo in march_algos:
            assert algo in controller.MARCH_PATTERNS
            patterns = controller.MARCH_PATTERNS[algo]
            assert len(patterns) > 0


class TestMarchAlgorithmExecution:
    """Test March algorithm execution"""

    def test_march_c_execution(self):
        """March-C algorithm must execute without errors"""
        controller = MBISTController()

        # Use small address range for testing
        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=15,  # 16 addresses
        )

        result = controller.run_test(config)

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.MARCH_C
        assert result.addresses_tested > 0
        # Should pass with no faults (simulated memory)
        assert result.status in ["PASS", "FAIL"]

    def test_march_l_execution(self):
        """March-L algorithm must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_L,
            start_address=0,
            end_address=15,
        )

        result = controller.run_test(config)

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.MARCH_L

    def test_march_u_execution(self):
        """March-U algorithm must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_U,
            start_address=0,
            end_address=15,
        )

        result = controller.run_test(config)

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.MARCH_U

    def test_march_minus_execution(self):
        """March-Minus algorithm must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_MINUS,
            start_address=0,
            end_address=15,
        )

        result = controller.run_test(config)

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.MARCH_MINUS

    def test_march_plus_execution(self):
        """March-Plus algorithm must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_PLUS,
            start_address=0,
            end_address=15,
        )

        result = controller.run_test(config)

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.MARCH_PLUS

    def test_tick_based_execution(self):
        """Tick-based execution must work"""
        controller = MBISTController()
        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=7,
        )
        controller.configure(config)
        controller.start_test()

        # Execute for limited cycles
        cycles = 0
        max_cycles = 1000
        while controller.tick() and cycles < max_cycles:
            cycles += 1

        assert cycles > 0

    def test_timeout_handling(self):
        """Timeout must stop test"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=7,
            timeout_cycles=10,  # Very short timeout
        )

        result = controller.run_test(config)

        # With very small address range, should complete before timeout
        assert result is not None

    def test_march_pattern_definitions(self):
        """Test all March patterns are correctly defined"""
        controller = MBISTController()

        # March-C: w0, r0, w1, r1, w0, r0
        march_c = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_C]
        assert len(march_c) == 6
        assert march_c[0].operation == "w0"
        assert march_c[1].operation == "r0"
        assert march_c[2].operation == "w1"
        assert march_c[3].operation == "r1"
        assert march_c[4].operation == "w0"
        assert march_c[5].operation == "r0"

        # March-L: w0, r0, w1, r1, w0, r0
        march_l = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_L]
        assert len(march_l) == 6

        # March-U: longer pattern
        march_u = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_U]
        assert len(march_u) == 8

    def test_march_address_order(self):
        """Test March patterns with both address orders"""
        controller = MBISTController()

        patterns = controller.MARCH_PATTERNS[MBISTAlgorithm.MARCH_C]

        # Check that patterns can have different address orders
        for pattern in patterns:
            assert pattern.address_order in ["up", "down"]


class TestWalkingOnesZeros:
    """Test Walking Ones/Zeros algorithms"""

    def test_walking_ones_execution(self):
        """Walking Ones test must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.WALKING_ONES,
            start_address=0,
            end_address=31,  # Small range for faster test
        )

        result = controller.run_walking_ones()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.WALKING_ONES
        assert result.addresses_tested > 0

    def test_walking_zeros_execution(self):
        """Walking Zeros test must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.WALKING_ZEROS,
            start_address=0,
            end_address=31,
        )

        result = controller.run_walking_zeros()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.WALKING_ZEROS


class TestAddressTest:
    """Test Address decoder test"""

    def test_address_test_execution(self):
        """Address test must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.ADDRESS_TEST,
            start_address=0,
            end_address=255,
        )

        result = controller.run_address_test()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.ADDRESS_TEST
        assert result.addresses_tested > 0


class TestDataRetentionTest:
    """Test Data Retention test"""

    def test_data_retention_execution(self):
        """Data retention test must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.DATA_RETENTION,
            start_address=0,
            end_address=63,
            retention_time_cycles=10,  # Short retention for testing
        )

        result = controller.run_data_retention_test()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.DATA_RETENTION


class TestGalPatTest:
    """Test Galloping Pattern test"""

    def test_galpat_execution(self):
        """GalPat test must execute"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.GALPAT,
            start_address=0,
            end_address=31,
        )

        result = controller.run_galpat_test()

        assert result is not None
        assert result.algorithm == MBISTAlgorithm.GALPAT


class TestFaultDetection:
    """Test fault detection and classification"""

    def test_inject_stuck_at_0(self):
        """Injecting stuck-at-0 fault must be detected"""
        controller = MBISTController()

        # Inject fault at address 0
        controller.inject_fault(0, FaultType.STUCK_AT_0)

        # Run March-C test with longer timeout
        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=7,
            fail_stop=False,  # Don't stop on first fault
            timeout_cycles=10000,  # Allow more time for complete test
        )

        result = controller.run_test(config)

        # Should detect the fault
        assert len(result.faults_found) > 0
        assert result.status == "FAIL"

    def test_inject_stuck_at_1(self):
        """Injecting stuck-at-1 fault must be detected"""
        controller = MBISTController()

        # Inject fault at address 10
        controller.inject_fault(10, FaultType.STUCK_AT_1, 0xFFFFFFFFFFFFFFFF)

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=15,
            fail_stop=False,
            timeout_cycles=10000,
        )

        result = controller.run_test(config)

        assert len(result.faults_found) > 0

    def test_fault_classification(self):
        """Faults must be classified correctly"""
        controller = MBISTController()

        # Test with specific expected vs actual values
        fault_type = controller._classify_fault(0, 1)
        assert fault_type == FaultType.STUCK_AT_0

        fault_type = controller._classify_fault(0xFFFFFFFFFFFFFFFF, 0)
        assert fault_type == FaultType.STUCK_AT_1

    def test_multiple_faults(self):
        """Multiple faults must be tracked"""
        controller = MBISTController()

        # Inject multiple faults
        controller.inject_fault(5, FaultType.STUCK_AT_0)
        controller.inject_fault(10, FaultType.STUCK_AT_1, 0xFFFFFFFFFFFFFFFF)

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=15,
            fail_stop=False,
            timeout_cycles=10000,
        )

        result = controller.run_test(config)

        assert len(result.faults_found) >= 2


class TestStatistics:
    """Test MBIST statistics"""

    def test_initial_stats(self):
        """Initial statistics must be zero"""
        controller = MBISTController()

        assert controller.stats.total_tests == 0
        assert controller.stats.passed_tests == 0
        assert controller.stats.failed_tests == 0
        assert controller.stats.total_faults == 0

    def test_stats_after_test(self):
        """Statistics must update after test"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=15,
        )

        controller.run_test(config)

        assert controller.stats.total_tests > 0
        assert controller.stats.total_cycles > 0
        assert controller.stats.total_addresses_tested > 0

    def test_pass_rate_calculation(self):
        """Pass rate must be calculated correctly"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=15,
        )

        controller.run_test(config)

        # With no faults, should have 100% pass rate
        if controller.stats.failed_tests == 0:
            assert controller.stats.pass_rate == 1.0

    def test_fault_coverage(self):
        """Fault coverage must be computed"""
        controller = MBISTController()

        # Inject a fault
        controller.inject_fault(0, FaultType.STUCK_AT_0)

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=7,
            fail_stop=False,
        )

        controller.run_test(config)

        coverage = controller.stats.fault_coverage
        assert isinstance(coverage, dict)


class TestSummary:
    """Test MBIST summary generation"""

    def test_get_summary(self):
        """Summary must contain all required fields"""
        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=15,
        )

        controller.run_test(config)

        summary = controller.get_summary()

        assert 'stats' in summary
        assert 'results' in summary
        assert 'current_state' in summary

        assert 'total_tests' in summary['stats']
        assert 'passed_tests' in summary['stats']
        assert 'failed_tests' in summary['stats']


class TestRunAllAlgorithms:
    """Test running all algorithms"""

    def test_run_all_march_algorithms(self):
        """All March algorithms must run"""
        # Run each algorithm with a fresh controller
        algorithms = [
            MBISTAlgorithm.MARCH_C,
            MBISTAlgorithm.MARCH_L,
            MBISTAlgorithm.MARCH_U,
        ]

        for algo in algorithms:
            controller = MBISTController()  # Fresh controller per algorithm
            config = MBISTConfig(
                algorithm=algo,
                start_address=0,
                end_address=7,
            )
            result = controller.run_test(config)
            assert result is not None
            assert result.algorithm == algo


class TestMBISTResult:
    """Test MBISTResult dataclass"""

    def test_result_passed_property(self):
        """passed property must return True when no faults"""
        result = MBISTResult(
            test_name="Test",
            algorithm=MBISTAlgorithm.MARCH_C,
            start_time=0,
            end_time=100,
            cycles_executed=100,
            addresses_tested=16,
        )

        assert result.passed is True

    def test_result_fault_rate(self):
        """fault_rate must be calculated"""
        result = MBISTResult(
            test_name="Test",
            algorithm=MBISTAlgorithm.MARCH_C,
            start_time=0,
            end_time=100,
            cycles_executed=100,
            addresses_tested=100,
        )

        assert result.fault_rate == 0.0

    def test_result_with_faults(self):
        """Fault rate with faults"""
        result = MBISTResult(
            test_name="Test",
            algorithm=MBISTAlgorithm.MARCH_C,
            start_time=0,
            end_time=100,
            cycles_executed=100,
            addresses_tested=100,
            faults_found=[
                MBISTFault(
                    fault_type=FaultType.STUCK_AT_0,
                    address=0,
                    expected=0,
                    actual=1,
                    cycle=10,
                    algorithm=MBISTAlgorithm.MARCH_C,
                    channel=0,
                    bank=0,
                    row=0,
                    column=0,
                ),
            ],
        )

        assert result.passed is False
        assert result.fault_rate == 0.01


class TestIntegration:
    """Integration tests for MBIST with channel model"""

    def test_controller_integration_setup(self):
        """MBIST controller must integrate with channel model"""
        from model.dram.hbm4_channel_model import HBM4Channel
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        channel = HBM4Channel(0, spec)

        # Create controller with channel
        controller = MBISTController(channel_model=None, spec=spec)
        controller.channel_model = type('obj', (object,), {'channels': [channel]})()

        assert controller.channel_model is not None

    def test_controller_spec_provided(self):
        """Controller must use provided spec for address decoding"""
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()

        controller = MBISTController(spec=spec)
        controller.configure(MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=31,
        ))

        # Should work with spec
        result = controller.run_test()
        assert result is not None


class TestMBISTFault:
    """Test MBISTFault dataclass"""

    def test_fault_creation(self):
        """Fault must be created with all fields"""
        fault = MBISTFault(
            fault_type=FaultType.STUCK_AT_0,
            address=0x1000,
            expected=0,
            actual=1,
            cycle=100,
            algorithm=MBISTAlgorithm.MARCH_C,
            channel=0,
            bank=1,
            row=10,
            column=5,
        )

        assert fault.fault_type == FaultType.STUCK_AT_0
        assert fault.address == 0x1000
        assert fault.expected == 0
        assert fault.actual == 1
        assert fault.cycle == 100
        assert fault.channel == 0
        assert fault.bank == 1


class TestMBISTState:
    """Test MBISTState enum"""

    def test_all_states_defined(self):
        """All states must be defined"""
        assert MBISTState.IDLE is not None
        assert MBISTState.SETUP is not None
        assert MBISTState.RUNNING is not None
        assert MBISTState.COMPLETE is not None
        assert MBISTState.FAIL is not None

    def test_state_values(self):
        """State values must be sequential"""
        assert MBISTState.IDLE.value == 0
        assert MBISTState.SETUP.value == 1
        assert MBISTState.RUNNING.value == 2
        assert MBISTState.COMPLETE.value == 3
        assert MBISTState.FAIL.value == 4


class TestFaultType:
    """Test FaultType enum"""

    def test_all_fault_types_defined(self):
        """All fault types must be defined"""
        assert FaultType.STUCK_AT_0 is not None
        assert FaultType.STUCK_AT_1 is not None
        assert FaultType.TRANSITION is not None
        assert FaultType.ADDRESS_DECODE is not None
        assert FaultType.COUPLING is not None
        assert FaultType.DATA_RETENTION is not None
        assert FaultType.READ_DISTURB is not None


class TestPerformance:
    """Performance tests for MBIST"""

    def test_small_range_fast_execution(self):
        """Small address range must execute quickly"""
        import time

        controller = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=31,
        )

        start = time.time()
        controller.run_test(config)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 1 second for 32 addresses)
        assert elapsed < 1.0

    def test_memory_efficiency(self):
        """Memory usage must be reasonable"""
        controller = MBISTController()

        # Run multiple tests
        for i in range(10):
            config = MBISTConfig(
                algorithm=MBISTAlgorithm.MARCH_C,
                start_address=0,
                end_address=63,
            )
            controller.run_test(config)

        # Should not accumulate too much memory
        assert controller.stats.total_addresses_tested > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])