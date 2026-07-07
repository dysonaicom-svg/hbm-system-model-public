"""Tests for Phase 14 - HBM4 Optimized Controller Integration"""

import pytest
from model.controller.hbm4_optimized_controller import (
    HBM4OptimizedController,
    OptimizationReport,
    Phase14Stats,
    create_optimized_controller,
)


class TestHBM4OptimizedControllerCreation:
    """Test HBM4OptimizedController creation and initialization"""

    def test_basic_creation(self):
        """Test basic controller creation with defaults"""
        ctrl = HBM4OptimizedController()
        assert ctrl.channels == 32
        assert ctrl._enable_analysis is True
        assert ctrl._enable_compliance is True
        assert ctrl._enable_optimization is True

    def test_creation_with_flags(self):
        """Test creation with different feature flags"""
        ctrl = HBM4OptimizedController(
            enable_analysis=False,
            enable_compliance=True,
            enable_optimization=False,
        )
        assert ctrl._enable_analysis is False
        assert ctrl._enable_compliance is True
        assert ctrl._enable_optimization is False

    def test_factory_function(self):
        """Test factory function"""
        ctrl = create_optimized_controller(
            analysis=True,
            compliance=True,
            optimization=True
        )
        assert ctrl._enable_analysis is True
        assert ctrl._enable_compliance is True
        assert ctrl._enable_optimization is True


class TestHBM4OptimizedControllerModules:
    """Test Phase 10/11/13 module integration"""

    def test_analysis_modules_initialized(self):
        """Test that Phase 10 analysis modules are initialized"""
        ctrl = HBM4OptimizedController(enable_analysis=True)
        assert hasattr(ctrl, 'bottleneck_detector')
        assert hasattr(ctrl, 'hotspot_detector')
        assert hasattr(ctrl, 'dvfs_analyzer')
        assert hasattr(ctrl, 'optimizer')

    def test_compliance_modules_initialized(self):
        """Test that Phase 11 compliance modules are initialized"""
        ctrl = HBM4OptimizedController(enable_compliance=True)
        assert hasattr(ctrl, 'jedec_validator')
        assert hasattr(ctrl, 'hbm3_checker')

    def test_optimization_modules_initialized(self):
        """Test that Phase 13 optimization modules are initialized"""
        ctrl = HBM4OptimizedController(enable_optimization=True)
        assert hasattr(ctrl, 'parallel_scheduler')
        assert hasattr(ctrl, 'prefetch_engine')
        assert hasattr(ctrl, 'smart_queue')
        assert hasattr(ctrl, 'bank_predictor')

    def test_modules_disabled(self):
        """Test that modules are not created when disabled"""
        ctrl = HBM4OptimizedController(
            enable_analysis=False,
            enable_compliance=False,
            enable_optimization=False
        )
        assert not hasattr(ctrl, 'bottleneck_detector')
        assert not hasattr(ctrl, 'jedec_validator')
        assert not hasattr(ctrl, 'parallel_scheduler')


class TestHBM4OptimizedControllerRequestSubmission:
    """Test request submission with integrated analysis"""

    def test_submit_request(self):
        """Test basic request submission"""
        ctrl = HBM4OptimizedController()
        request_id = ctrl.submit_request(addr=0x1000, is_read=True)
        assert request_id is not None

    def test_submit_write_request(self):
        """Test write request submission"""
        ctrl = HBM4OptimizedController()
        request_id = ctrl.submit_request(addr=0x2000, is_read=False)
        assert request_id is not None

    def test_submit_multiple_requests(self):
        """Test multiple request submissions"""
        ctrl = HBM4OptimizedController()
        for i in range(10):
            request_id = ctrl.submit_request(
                addr=0x1000 + i * 64,
                is_read=(i % 2 == 0)
            )
            assert request_id is not None

    def test_access_history_tracking(self):
        """Test that access history is tracked"""
        ctrl = HBM4OptimizedController()
        ctrl.submit_request(addr=0x1000, is_read=True)
        ctrl.submit_request(addr=0x2000, is_read=False)
        assert len(ctrl._access_history) == 2
        assert ctrl._access_history[0] == (0x1000, True)
        assert ctrl._access_history[1] == (0x2000, False)


class TestHBM4OptimizedControllerTick:
    """Test tick operation with analysis integration"""

    def test_tick_basic(self):
        """Test basic tick operation"""
        ctrl = HBM4OptimizedController()
        ctrl.submit_request(addr=0x1000, is_read=True)
        responses = ctrl.tick()
        # Responses may be empty initially depending on timing

    def test_tick_with_multiple_requests(self):
        """Test tick with multiple requests"""
        ctrl = HBM4OptimizedController()
        for i in range(5):
            ctrl.submit_request(addr=0x1000 + i * 64, is_read=True)

        for _ in range(100):
            ctrl.tick()

        # Check that base controller processed requests
        assert ctrl.stats_base.total_requests >= 5


class TestHBM4OptimizedControllerAnalysis:
    """Test analysis functionality"""

    def test_analyze_performance(self):
        """Test performance analysis report generation"""
        ctrl = HBM4OptimizedController()

        # Generate some traffic
        for i in range(20):
            ctrl.submit_request(
                addr=0x1000 + i * 64,
                is_read=(i % 2 == 0)
            )

        # Run simulation
        for _ in range(200):
            ctrl.tick()

        # Analyze performance
        report = ctrl.analyze_performance()
        assert isinstance(report, OptimizationReport)
        assert hasattr(report, 'bottlenecks')
        assert hasattr(report, 'latency_stats')
        assert hasattr(report, 'suggestions')

    def test_optimization_score(self):
        """Test optimization score calculation"""
        ctrl = HBM4OptimizedController()
        report = ctrl.analyze_performance()
        assert 0.0 <= report.optimization_score <= 100.0


class TestHBM4OptimizedControllerDVFS:
    """Test DVFS control"""

    def test_set_frequency_valid(self):
        """Test setting valid frequencies"""
        ctrl = HBM4OptimizedController()

        assert ctrl.set_frequency(8.0) is True
        assert ctrl.get_current_frequency() == 8.0

        assert ctrl.set_frequency(12.0) is True
        assert ctrl.get_current_frequency() == 12.0

        assert ctrl.set_frequency(16.0) is True
        assert ctrl.get_current_frequency() == 16.0

    def test_set_frequency_invalid(self):
        """Test setting invalid frequency"""
        ctrl = HBM4OptimizedController()
        assert ctrl.set_frequency(10.0) is False  # Invalid
        assert ctrl.set_frequency(14.0) is False  # Invalid


class TestHBM4OptimizedControllerPrefetch:
    """Test prefetch prediction"""

    def test_get_prefetch_predictions(self):
        """Test prefetch prediction retrieval"""
        ctrl = HBM4OptimizedController(enable_optimization=True)

        # Generate some accesses
        for i in range(32):
            ctrl.submit_request(addr=0x1000 + i * 64, is_read=True)

        # Get predictions
        predictions = ctrl.get_prefetch_predictions(stream_id=0)
        assert isinstance(predictions, list)


class TestHBM4OptimizedControllerBankPredictor:
    """Test bank conflict prediction"""

    def test_get_bank_conflict_prediction(self):
        """Test bank conflict prediction"""
        ctrl = HBM4OptimizedController(enable_optimization=True)

        # Get prediction for a bank
        will_conflict, confidence = ctrl.get_bank_conflict_prediction(
            bank_id=5,
            target_row=0x300
        )

        assert isinstance(will_conflict, bool)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_get_optimal_bank_order(self):
        """Test optimal bank order calculation"""
        ctrl = HBM4OptimizedController(enable_optimization=True)

        # Get optimal order with valid bank IDs
        optimal = ctrl.get_optimal_bank_order([1, 2, 3])
        assert isinstance(optimal, list)


class TestHBM4OptimizedControllerQueue:
    """Test queue management"""

    def test_get_queue_stats(self):
        """Test queue statistics retrieval"""
        ctrl = HBM4OptimizedController(enable_optimization=True)

        stats = ctrl.get_queue_stats()
        assert 'smart_queue' in stats
        assert 'base_controller' in stats


class TestHBM4OptimizedControllerReset:
    """Test reset functionality"""

    def test_reset(self):
        """Test controller reset"""
        ctrl = HBM4OptimizedController()

        # Submit some requests
        for i in range(10):
            ctrl.submit_request(addr=0x1000 + i * 64, is_read=True)

        # Reset
        ctrl.reset()

        # Check state is reset
        assert len(ctrl._access_history) == 0
        assert ctrl.stats.accesses_analyzed == 0


class TestPhase14Stats:
    """Test Phase14Stats dataclass"""

    def test_stats_default_values(self):
        """Test default statistics values"""
        stats = Phase14Stats()
        assert stats.accesses_analyzed == 0
        assert stats.latency_samples_collected == 0
        assert stats.bottleneck_checks == 0
        assert stats.compliance_checks_passed == 0
        assert stats.optimizations_applied == 0


class TestHBM4OptimizedControllerProperties:
    """Test controller properties"""

    def test_channels_property(self):
        """Test channels property"""
        ctrl = HBM4OptimizedController()
        assert ctrl.channels == 32

    def test_pseudo_channels_property(self):
        """Test pseudo_channels property"""
        ctrl = HBM4OptimizedController()
        assert ctrl.pseudo_channels == 64

    def test_dfi_ready_property(self):
        """Test dfi_ready property"""
        ctrl = HBM4OptimizedController()
        assert isinstance(ctrl.dfi_ready, bool)

    def test_current_time_property(self):
        """Test current_time_ns property"""
        ctrl = HBM4OptimizedController()
        assert ctrl.current_time_ns >= 0.0

    def test_current_cycle_property(self):
        """Test current_cycle property"""
        ctrl = HBM4OptimizedController()
        assert ctrl.current_cycle >= 0
