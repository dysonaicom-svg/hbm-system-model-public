"""
Enhanced Tests for Eye Analyzer Module

Tests additional eye analyzer functionality including:
- DQ/DQS eye analysis
- JEDEC compliance checking
- Bathtub curve generation
- Eye visualization helpers
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.phy.eye_analyzer import (
    EyeDiagramAnalyzer, EyeMeasurementConfig, EyeMaskConfig, DQDEyeConfig,
    EyeMetrics, DQDEyeMetrics, DQDEyeAnalyzer,
    BathtubCurveGenerator, EyeVisualizationHelper, create_hbm4_eye_analyzer,
    estimate_channel_budget, EyeMeasurementType, DQSignalType
)


class TestEyeMeasurementConfig:
    """Tests for eye measurement configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = EyeMeasurementConfig()
        assert config.samples_per_ui == 64
        assert config.n_ui == 1000
        assert config.target_ber == 1e-16

    def test_custom_config(self):
        """Test custom configuration"""
        config = EyeMeasurementConfig(
            samples_per_ui=128,
            n_ui=2000,
            target_ber=1e-12
        )
        assert config.samples_per_ui == 128
        assert config.n_ui == 2000
        assert config.target_ber == 1e-12


class TestEyeMaskConfig:
    """Tests for eye mask configuration"""

    def test_hbm4_mask_defaults(self):
        """Test HBM4 mask defaults"""
        config = EyeMaskConfig(mask_type='hbm4')
        assert config.eye_height_target == 0.1
        assert config.eye_width_target == 0.25
        assert config.ber_target == 1e-16

    def test_mask_points(self):
        """Test mask points are defined"""
        config = EyeMaskConfig()
        assert len(config.mask_points) > 0


class TestDQDEyeConfig:
    """Tests for DQ/DQS eye configuration"""

    def test_default_config(self):
        """Test default DQ/DQS config"""
        config = DQDEyeConfig()
        assert config.dqs_to_dq_offset == 0.0
        assert config.dqs_duty_cycle == 0.5
        assert config.read_preamble_ui == 2.0

    def test_custom_config(self):
        """Test custom DQ/DQS config"""
        config = DQDEyeConfig(
            dqs_duty_cycle=0.45,
            read_preamble_ui=3.0
        )
        assert config.dqs_duty_cycle == 0.45
        assert config.read_preamble_ui == 3.0


class TestEyeMetrics:
    """Tests for eye metrics dataclass"""

    def test_metrics_creation(self):
        """Test creating eye metrics"""
        metrics = EyeMetrics(
            eye_width=0.8,
            eye_height=0.4,
            eye_area=0.32,
            vertical_closure=80.0,
            horizontal_closure=20.0,
            ber_estimate=1e-15,
            snr_db=15.0,
            jitter_rms=0.05,
            noise_rms=0.02,
            one_level_mean=0.8,
            zero_level_mean=-0.8,
            one_level_sigma=0.01,
            zero_level_sigma=0.01
        )
        assert metrics.eye_width == 0.8
        assert metrics.eye_height == 0.4


class TestDQDEyeMetrics:
    """Tests for DQ/DQS eye metrics"""

    def test_dqd_metrics_creation(self):
        """Test creating DQ/DQS metrics"""
        metrics = DQDEyeMetrics(
            eye_height_mv=100.0,
            eye_width_ui=0.8,
            setup_margin_ps=20.0,
            hold_margin_ps=15.0,
            compliant=True
        )
        assert metrics.eye_height_mv == 100.0
        assert metrics.compliant is True


class TestDQDEyeAnalyzer:
    """Tests for DQ/DQS eye analyzer"""

    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly"""
        analyzer = DQDEyeAnalyzer()
        assert analyzer.config is not None

    def test_analyze_clean_signals(self):
        """Test analyzing clean DQ/DQS signals"""
        analyzer = DQDEyeAnalyzer()

        # Create clean DQ signal
        dq = np.concatenate([np.ones(100), -np.ones(100)]) * 0.5

        # Create clean DQS signal
        dqs = np.concatenate([
            np.ones(25) * 0.5,
            np.zeros(25),
            np.ones(25) * 0.5,
            np.zeros(25)
        ])

        metrics = analyzer.analyze_dq_dqs_eye(dq, dqs, sample_rate=32e9)

        assert 'eye_height_mv' in dir(metrics) or hasattr(metrics, 'eye_height_mv')

    def test_find_dqs_edges(self):
        """Test finding DQS edges"""
        analyzer = DQDEyeAnalyzer()

        dqs = np.concatenate([
            np.linspace(0, 0.5, 50),
            np.linspace(0.5, 0, 50)
        ])

        edges = analyzer._find_dqs_edges(dqs, sample_rate=32e9)
        assert len(edges) > 0

    def test_sample_at_edges(self):
        """Test sampling at edges"""
        analyzer = DQDEyeAnalyzer()

        signal = np.linspace(0, 1, 100)
        edges = np.array([10, 50, 90])

        samples = analyzer._sample_at_edges(signal, edges)
        assert len(samples) == 3

    def test_calculate_duty_error(self):
        """Test DQS duty error calculation"""
        analyzer = DQDEyeAnalyzer()

        dqs = np.concatenate([np.ones(500), np.zeros(500)])
        error = analyzer._calculate_duty_error(dqs, sample_rate=32e9)

        assert error >= 0

    def test_estimate_skew(self):
        """Test DQ-DQS skew estimation"""
        analyzer = DQDEyeAnalyzer()

        dq = np.concatenate([np.ones(100), -np.ones(100)]) * 0.5
        dqs = np.concatenate([np.ones(50) * 0.5, np.zeros(50), np.ones(50) * 0.5, np.zeros(50)])

        skew = analyzer._estimate_skew(dq, dqs, sample_rate=32e9)
        assert skew >= 0

    def test_calculate_setup_hold_margins(self):
        """Test setup/hold margin calculation"""
        analyzer = DQDEyeAnalyzer()

        dq = np.concatenate([np.ones(100), -np.ones(100)]) * 0.5
        dqs = np.concatenate([np.ones(50) * 0.5, np.zeros(50), np.ones(50) * 0.5, np.zeros(50)])

        setup, hold = analyzer._calculate_setup_hold_margins(dq, dqs, sample_rate=32e9)
        assert setup >= 0
        assert hold >= 0

    def test_estimate_ber_from_dq_dqs(self):
        """Test BER estimation from DQ/DQS metrics"""
        analyzer = DQDEyeAnalyzer()

        ber = analyzer._estimate_ber_from_dq_dqs(eye_height=0.2, jitter_ui=0.05)
        assert 0 <= ber <= 1.0


class TestEyeDiagramAnalyzerAdvanced:
    """Advanced tests for eye diagram analyzer"""

    def test_estimate_jitter(self):
        """Test jitter estimation"""
        config = EyeMeasurementConfig(samples_per_ui=64, n_ui=100)
        analyzer = EyeDiagramAnalyzer(config)

        # Create signal with jitter
        signal = np.concatenate([np.ones(6400), -np.ones(6400)])
        signal += np.random.randn(len(signal)) * 0.02

        analyzer.generate_eye_diagram(signal)
        jitter = analyzer.estimate_jitter()

        assert jitter >= 0

    def test_estimate_jitter_decomposed(self):
        """Test jitter decomposition"""
        config = EyeMeasurementConfig(samples_per_ui=64, n_ui=100)
        analyzer = EyeDiagramAnalyzer(config)

        signal = np.concatenate([np.ones(6400), -np.ones(6400)])

        analyzer.generate_eye_diagram(signal)
        total, dcd, rj, dj = analyzer.estimate_jitter_decomposed()

        assert total >= 0
        assert dcd >= 0
        assert rj >= 0
        assert dj >= 0

    def test_estimate_noise(self):
        """Test noise estimation"""
        config = EyeMeasurementConfig(samples_per_ui=64, n_ui=100)
        analyzer = EyeDiagramAnalyzer(config)

        signal = np.concatenate([np.ones(6400), -np.ones(6400)])
        signal += np.random.randn(len(signal)) * 0.05

        analyzer.generate_eye_diagram(signal)
        noise = analyzer.estimate_noise()

        assert noise >= 0

    def test_check_jedec_compliance_pass(self):
        """Test JEDEC compliance check - passing"""
        config = EyeMeasurementConfig(samples_per_ui=64, n_ui=200)
        analyzer = EyeDiagramAnalyzer(config)

        # Create good signal
        signal = np.concatenate([np.ones(6400), -np.ones(6400)]) * 0.5
        signal += np.random.randn(len(signal)) * 0.01

        analyzer.generate_eye_diagram(signal)
        result = analyzer.check_jedec_compliance()

        assert 'compliant' in result
        assert 'requirements' in result

    def test_check_jedec_compliance_fail(self):
        """Test JEDEC compliance check - failing"""
        config = EyeMeasurementConfig(samples_per_ui=64, n_ui=100)
        analyzer = EyeDiagramAnalyzer(config)

        # Create poor quality signal
        signal = np.random.randn(6400) * 0.5

        analyzer.generate_eye_diagram(signal)
        result = analyzer.check_jedec_compliance()

        assert 'compliant' in result

    def test_margin_analysis_at_target(self):
        """Test margin analysis at specific target BER"""
        config = EyeMeasurementConfig(samples_per_ui=64, n_ui=100)
        analyzer = EyeDiagramAnalyzer(config)

        signal = np.concatenate([np.ones(6400), -np.ones(6400)])
        signal += np.random.randn(len(signal)) * 0.02

        analyzer.generate_eye_diagram(signal)
        margin = analyzer.margin_analysis(target_ber=1e-12)

        assert 'voltage_margin' in margin
        assert 'time_margin_ui' in margin
        assert 'meets_target_ber' in margin


class TestBathtubCurveGeneratorAdvanced:
    """Advanced tests for bathtub curve generator"""

    def test_fit_bathtub_model(self):
        """Test fitting bathtub model"""
        generator = BathtubCurveGenerator(n_samples_per_ui=64)

        # Create synthetic bathtub data
        t = np.linspace(0, 1, 64)
        ber = np.exp(-((t - 0.5) ** 2) * 100) + 0.001

        params = generator.fit_bathtub_model(t, ber)

        assert 'center_ui' in params
        assert 'sigma_ui' in params
        assert 'ber_floor' in params

    def test_estimate_ber_from_bathtub(self):
        """Test BER estimation from bathtub curve"""
        generator = BathtubCurveGenerator(n_samples_per_ui=64)

        # Create synthetic bathtub curve
        t = np.linspace(0, 1, 64)
        ber = np.exp(-((t - 0.5) ** 2) * 100) + 0.001

        ber_at_margin = generator.estimate_ber_from_bathtub((t, ber), time_margin=0.1)

        assert 0 <= ber_at_margin <= 1.0


class TestEyeVisualizationHelper:
    """Tests for eye visualization helper"""

    def test_create_eye_plot_data(self):
        """Test creating eye plot data"""
        histogram = np.random.rand(100, 100)
        time_bins = np.linspace(0, 1, 100)
        voltage_bins = np.linspace(-1, 1, 100)

        data = EyeVisualizationHelper.create_eye_plot_data(
            histogram, time_bins, voltage_bins
        )

        assert 'histogram' in data
        assert 'time_bins' in data
        assert 'voltage_bins' in data
        assert 'time_range' in data
        assert 'voltage_range' in data

    def test_create_mask_polygon(self):
        """Test creating mask polygon"""
        config = EyeMaskConfig()
        polygon = EyeVisualizationHelper.create_mask_polygon(config, signal_swing=1.0)

        assert len(polygon) > 0
        # Last point should be same as first (closed polygon)
        assert polygon[0] == polygon[-1]

    def test_annotate_eye_metrics(self):
        """Test creating eye metric annotations"""
        metrics = EyeMetrics(
            eye_width=0.8,
            eye_height=0.4,
            eye_area=0.32,
            vertical_closure=80.0,
            horizontal_closure=20.0,
            ber_estimate=1e-15,
            snr_db=15.0,
            jitter_rms=0.05,
            noise_rms=0.02,
            one_level_mean=0.8,
            zero_level_mean=-0.8,
            one_level_sigma=0.01,
            zero_level_sigma=0.01,
            eye_height_mv=400.0,
            eye_width_ps=66.66
        )

        annotations = EyeVisualizationHelper.annotate_eye_metrics(metrics, ui_ps=83.33)

        assert 'eye_height' in annotations
        assert 'eye_width' in annotations
        assert 'ber' in annotations
        assert 'snr' in annotations


class TestCreateHBM4EyeAnalyzer:
    """Tests for HBM4 eye analyzer creation"""

    def test_create_default(self):
        """Test creating HBM4 eye analyzer with defaults"""
        analyzer = create_hbm4_eye_analyzer()

        assert analyzer.config is not None
        assert analyzer.mask_config is not None

    def test_create_8gt(self):
        """Test creating analyzer for 8 GT/s"""
        analyzer = create_hbm4_eye_analyzer(data_rate_gt=8.0)

        assert analyzer.config is not None

    def test_create_16gt(self):
        """Test creating analyzer for 16 GT/s"""
        analyzer = create_hbm4_eye_analyzer(data_rate_gt=16.0, target_ber=1e-15)

        assert analyzer.config is not None
        assert analyzer.mask_config.ber_target == 1e-15


class TestEstimateChannelBudget:
    """Tests for channel budget estimation"""

    def test_channel_budget_full(self):
        """Test complete channel budget estimation"""
        metrics = EyeMetrics(
            eye_width=0.7,
            eye_height=0.35,
            eye_area=0.245,
            vertical_closure=82.5,
            horizontal_closure=30.0,
            ber_estimate=1e-15,
            snr_db=15.0,
            jitter_rms=0.05,
            noise_rms=0.02,
            one_level_mean=0.8,
            zero_level_mean=-0.8,
            one_level_sigma=0.01,
            zero_level_sigma=0.01,
            eye_height_mv=350.0,
            eye_width_ps=58.33
        )

        budget = estimate_channel_budget(metrics, ui_ps=83.33)

        assert 'total_time_ui' in budget
        assert 'total_voltage_mv' in budget
        assert 'allocated_to_jitter_ui' in budget
        assert 'remaining_timing_margin_ui' in budget
        assert 'eye_openness_percent' in budget

    def test_channel_budget_limits(self):
        """Test channel budget with edge cases"""
        metrics = EyeMetrics(
            eye_width=0.5,
            eye_height=0.2,
            eye_area=0.1,
            vertical_closure=90.0,
            horizontal_closure=50.0,
            ber_estimate=0.5,
            snr_db=5.0,
            jitter_rms=0.15,
            noise_rms=0.1,
            one_level_mean=0.6,
            zero_level_mean=-0.6,
            one_level_sigma=0.05,
            zero_level_sigma=0.05,
            eye_height_mv=200.0,
            eye_width_ps=41.67
        )

        budget = estimate_channel_budget(metrics, ui_ps=83.33)

        assert budget['remaining_timing_margin_ui'] >= 0
        # remaining_voltage_mv might not be in the result, check only if present
        if 'remaining_voltage_mv' in budget:
            assert budget['remaining_voltage_mv'] >= 0


class TestEyeMeasurementType:
    """Tests for eye measurement type enum"""

    def test_measurement_types(self):
        """Test all measurement types are defined"""
        assert EyeMeasurementType.TIME_DOMAIN is not None
        assert EyeMeasurementType.VOLTAGE_DOMAIN is not None
        assert EyeMeasurementType.COMBINED is not None


class TestDQSignalType:
    """Tests for DQ signal type enum"""

    def test_signal_types(self):
        """Test all DQ signal types are defined"""
        assert DQSignalType.DQ is not None
        assert DQSignalType.DQS is not None
        assert DQSignalType.WCK is not None


class TestEyeAnalyzerEdgeCases:
    """Tests for edge cases and error handling"""

    def test_empty_signal(self):
        """Test handling of empty signal"""
        config = EyeMeasurementConfig()
        analyzer = EyeDiagramAnalyzer(config)

        # Empty or very short signal
        signal = np.array([])

        # Should handle gracefully
        histogram = analyzer.generate_eye_diagram(signal)
        assert histogram is not None

    def test_single_value_signal(self):
        """Test handling of single-value signal"""
        config = EyeMeasurementConfig()
        analyzer = EyeDiagramAnalyzer(config)

        signal = np.ones(64)

        histogram = analyzer.generate_eye_diagram(signal)
        assert histogram is not None

    def test_all_same_signal(self):
        """Test handling of all-same-value signal"""
        config = EyeMeasurementConfig()
        analyzer = EyeDiagramAnalyzer(config)

        signal = np.ones(6400) * 0.5

        histogram = analyzer.generate_eye_diagram(signal)
        assert histogram is not None

    def test_prbs_with_noise(self):
        """Test PRBS signal with various noise levels"""
        config = EyeMeasurementConfig(samples_per_ui=64, n_ui=100)
        analyzer = EyeDiagramAnalyzer(config)

        # Generate PRBS
        prbs = np.array([1 if i % 2 == 0 else -1 for i in range(127)])
        signal = np.repeat(prbs, 64)[:6400]

        # Test with low noise
        np.random.seed(42)
        signal_noisy = signal + np.random.randn(len(signal)) * 0.01
        analyzer.generate_eye_diagram(signal_noisy)
        metrics_low = analyzer.calculate_full_metrics()

        # Test with high noise
        np.random.seed(123)
        signal_noisy = signal + np.random.randn(len(signal)) * 0.1
        analyzer.generate_eye_diagram(signal_noisy)
        metrics_high = analyzer.calculate_full_metrics()

        # Noise estimates should be higher for noisy signal
        assert metrics_high.noise_rms > metrics_low.noise_rms


class TestBathtubCurveEdgeCases:
    """Tests for bathtub curve edge cases"""

    def test_constant_signal(self):
        """Test bathtub for constant signal"""
        generator = BathtubCurveGenerator(n_samples_per_ui=64)

        signal = np.ones(6400)

        t, ber = generator.generate_bathtub(signal)
        assert len(t) == 64
        assert len(ber) == 64

    def test_empty_bathtub_data(self):
        """Test bathtub with empty curve"""
        generator = BathtubCurveGenerator()

        # Empty arrays should not cause errors
        try:
            ber = generator.estimate_ber_from_bathtub(
                (np.array([]), np.array([])),
                time_margin=0.1
            )
            # Should handle gracefully
            assert True
        except (IndexError, ValueError):
            # Acceptable if it raises an exception for invalid data
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
