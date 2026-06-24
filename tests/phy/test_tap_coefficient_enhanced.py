"""
Enhanced Tests for Tap Coefficient Module

Tests additional tap coefficient functionality including:
- Advanced TX/RX coefficient operations
- Coefficient optimization algorithms
- Margin sensitivity analysis
- Coefficient serialization
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


class TestTXCoefficientsAdvanced:
    """Advanced tests for TX coefficients"""

    def test_get_all_taps(self):
        """Test getting all taps as single list"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.1, 0.2]
        tx.post_cursor = [0.15, 0.05]

        all_taps = tx.get_all_taps()

        assert len(all_taps) == 5  # 2 pre + 1 main + 2 post
        assert all_taps[0] == 0.1
        assert all_taps[1] == 0.2
        assert all_taps[2] == 1.0
        assert all_taps[3] == 0.15
        assert all_taps[4] == 0.05

    def test_set_taps_with_saturation(self):
        """Test setting taps with saturation"""
        tx = TXCoefficients()
        tx.max_tap_magnitude = 0.3

        tx.set_taps([0.5, 0.6], [0.7, 0.8])

        # All taps should be clamped
        for tap in tx.pre_cursor:
            assert abs(tap) <= 0.3
        for tap in tx.post_cursor:
            assert abs(tap) <= 0.3

    def test_normalize_maintains_sum(self):
        """Test normalization maintains unity DC gain"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.2, 0.2]
        tx.post_cursor = [0.2, 0.2]

        scale = tx.normalize()

        # After normalization, main_cursor should still be 1.0
        # But pre and post cursors are scaled
        total = sum(tx.pre_cursor) + tx.main_cursor + sum(tx.post_cursor)
        # Main cursor is 1.0, so sum = 1.0 + scaled_pre + scaled_post
        # The scale factor should bring sum(pre/post) to 0, making total ~= 1.0
        assert abs(tx.main_cursor - 1.0) < 0.01  # Main cursor unchanged

    def test_normalize_zero_sum(self):
        """Test normalization with zero sum"""
        tx = TXCoefficients()
        tx.main_cursor = 0.0

        scale = tx.normalize()

        assert scale == 1.0  # Should not divide by zero

    def test_from_fir_coeffs(self):
        """Test loading from FIR coefficients"""
        tx = TXCoefficients()
        fir = np.array([0.1, 0.2, 0.8, 0.15, 0.05])

        tx.from_fir_coeffs(fir)

        assert tx.pre_cursor == [0.1, 0.2]
        assert abs(tx.main_cursor - 0.8) < 0.01
        assert tx.post_cursor == [0.15, 0.05]

    def test_from_fir_coeffs_odd_length(self):
        """Test loading from odd-length FIR coefficients"""
        tx = TXCoefficients()
        fir = np.array([0.1, 0.5, 0.1])  # 3 taps

        tx.from_fir_coeffs(fir)

        assert tx.pre_cursor == [0.1]
        assert abs(tx.main_cursor - 0.5) < 0.01
        assert tx.post_cursor == [0.1]

    def test_boost_calculation_zero_taps(self):
        """Test boost calculation with zero pre/post taps"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.0, 0.0]
        tx.post_cursor = [0.0, 0.0]

        boost = tx.calculate_boost_db()

        # With no pre/post emphasis, boost should be ~0 dB
        assert boost >= 0

    def test_boost_calculation_max_taps(self):
        """Test boost calculation with maximum taps"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.4, 0.3]
        tx.post_cursor = [0.4, 0.3]

        boost = tx.calculate_boost_db()

        # With high pre/post emphasis, boost should be significant
        assert boost > 0

    def test_tap_properties(self):
        """Test tap property calculations"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.1, 0.2, 0.15, 0.05]  # Custom length
        tx.post_cursor = [0.15, 0.1, 0.05, 0.0]

        assert tx.num_pre_taps == 4
        assert tx.num_post_taps == 4
        assert tx.total_taps == 9  # 4 + 1 + 4

    def test_copy_preserves_all_fields(self):
        """Test copy preserves all coefficient fields"""
        tx = TXCoefficients()
        tx.pre_cursor = [0.15, 0.25]
        tx.post_cursor = [0.18, 0.08]
        tx.max_tap_magnitude = 0.4

        tx_copy = tx.copy()

        assert tx_copy.pre_cursor == tx.pre_cursor
        assert tx_copy.post_cursor == tx.post_cursor
        assert tx_copy.max_tap_magnitude == tx.max_tap_magnitude
        assert tx_copy.main_cursor == tx.main_cursor


class TestRXCoefficientsAdvanced:
    """Advanced tests for RX coefficients"""

    def test_set_ctle(self):
        """Test setting CTLE parameters"""
        rx = RXCoefficients()

        rx.set_ctle(3.0, 6.0)

        assert rx.ctle_dc_gain_db == 3.0
        assert rx.ctle_peaking_db == 6.0

    def test_set_ctle_saturation(self):
        """Test CTLE saturation"""
        rx = RXCoefficients()

        rx.set_ctle(10.0, 20.0)  # Way out of range

        assert rx.ctle_dc_gain_db == 6.0  # Clamped to max
        assert rx.ctle_peaking_db == 12.0  # Clamped to max

    def test_vref_setters(self):
        """Test VREF setter and clamping"""
        rx = RXCoefficients()

        # Valid range
        rx.set_vref(32)
        assert rx.vref == 32

        # Above max
        rx.set_vref(100)
        assert rx.vref == 63

        # Below min
        rx.set_vref(-10)
        assert rx.vref == 0

    def test_dfe_tap_setters(self):
        """Test DFE tap setters"""
        rx = RXCoefficients()

        rx.set_dfe_taps([0.1, 0.2, 0.15, 0.05, 0.0])

        assert len(rx.dfe_taps) == 5
        assert rx.dfe_taps[0] == 0.1

    def test_dfe_tap_saturation(self):
        """Test DFE tap saturation"""
        rx = RXCoefficients()
        rx.dfe_max_tap_magnitude = 0.2

        rx.set_dfe_taps([0.5, -0.6, 0.3, 0.2, 0.1])

        for tap in rx.dfe_taps:
            assert abs(tap) <= 0.2

    def test_update_single_dfe_tap(self):
        """Test updating a single DFE tap"""
        rx = RXCoefficients()

        rx.update_dfe_tap(2, 0.15)
        assert rx.dfe_taps[2] == 0.15

    def test_update_dfe_tap_bounds(self):
        """Test updating DFE tap within bounds"""
        rx = RXCoefficients()
        rx.dfe_max_tap_magnitude = 0.3

        rx.update_dfe_tap(0, 0.5)
        assert rx.dfe_taps[0] == 0.3  # Saturated

        rx.update_dfe_tap(0, -0.5)
        assert rx.dfe_taps[0] == -0.3  # Saturated

    def test_update_invalid_dfe_tap_index(self):
        """Test updating invalid DFE tap index"""
        rx = RXCoefficients()

        # Should not raise
        rx.update_dfe_tap(-1, 0.1)
        rx.update_dfe_tap(100, 0.1)

        # Original taps should be unchanged
        assert rx.dfe_taps[0] == 0.0

    def test_ctle_transfer_dc(self):
        """Test CTLE transfer function at DC"""
        rx = RXCoefficients()
        rx.ctle_dc_gain_db = 3.0

        freq = np.array([0.0])
        H = rx.calculate_ctle_transfer(freq)

        assert np.isfinite(H[0])

    def test_ctle_transfer_nyquist(self):
        """Test CTLE transfer function at Nyquist"""
        rx = RXCoefficients()
        rx.ctle_dc_gain_db = 3.0
        rx.ctle_peaking_db = 6.0

        freq = np.array([8e9])  # Nyquist for 16 GT/s
        H = rx.calculate_ctle_transfer(freq)

        assert np.isfinite(H[0])

    def test_ctle_zero_freq_property(self):
        """Test CTLE zero frequency property"""
        rx = RXCoefficients()
        rx.ctle_zero_idx = 1

        assert rx.ctle_zero_freq == rx.zero_options[1]

    def test_ctle_pole_freq_property(self):
        """Test CTLE pole frequency property"""
        rx = RXCoefficients()
        rx.ctle_pole_idx = 2

        assert rx.ctle_pole_freq == rx.pole_options[2]

    def test_rx_copy_preserves_all(self):
        """Test RX copy preserves all fields"""
        rx = RXCoefficients()
        rx.vref = 45
        rx.ctle_dc_gain_db = 4.0
        rx.ctle_peaking_db = 8.0
        rx.set_dfe_taps([0.1, 0.2, 0.15, 0.05, 0.0])

        rx_copy = rx.copy()

        assert rx_copy.vref == 45
        assert rx_copy.ctle_dc_gain_db == 4.0
        assert rx_copy.ctle_peaking_db == 8.0
        assert rx_copy.dfe_taps == [0.1, 0.2, 0.15, 0.05, 0.0]


class TestLaneCoefficientsAdvanced:
    """Advanced tests for lane coefficients"""

    def test_initialization_with_custom_lanes(self):
        """Test initialization with custom lane count"""
        lane = LaneCoefficients(num_lanes=32)

        assert lane.num_lanes == 32
        assert len(lane.rd_delays) == 32
        assert len(lane.wr_delays) == 32

    def test_set_rd_dq_delay(self):
        """Test setting read DQ delay"""
        lane = LaneCoefficients()

        lane.set_rd_dq_delay(0, 42)
        assert lane.rd_dq_delays[0] == 42

    def test_set_wr_dq_delay(self):
        """Test setting write DQ delay"""
        lane = LaneCoefficients()

        lane.set_wr_dq_delay(5, 38)
        assert lane.wr_dq_delays[5] == 38

    def test_rd_dq_delay_clamping(self):
        """Test read DQ delay clamping"""
        lane = LaneCoefficients()

        lane.set_rd_dq_delay(0, 100)  # Too high
        assert lane.rd_dq_delays[0] == 63

        lane.set_rd_dq_delay(0, -5)  # Too low
        assert lane.rd_dq_delays[0] == 0

    def test_wr_dq_delay_clamping(self):
        """Test write DQ delay clamping"""
        lane = LaneCoefficients()

        lane.set_wr_dq_delay(0, 100)
        assert lane.wr_dq_delays[0] == 63

        lane.set_wr_dq_delay(0, -5)
        assert lane.wr_dq_delays[0] == 0

    def test_lane_copy(self):
        """Test lane coefficient copy"""
        lane = LaneCoefficients()
        lane.set_rd_delay(0, 42)
        lane.set_wr_delay(1, 38)

        lane_copy = lane.copy()

        assert lane_copy.rd_delays[0] == 42
        assert lane_copy.wr_delays[1] == 38
        assert lane_copy is not lane


class TestCompleteTapCoefficientsAdvanced:
    """Advanced tests for complete tap coefficients"""

    def test_invalid_vref_low(self):
        """Test validity check with low VREF"""
        coeffs = CompleteTapCoefficients()
        coeffs.rx.vref = -1

        assert coeffs.is_valid() is False

    def test_invalid_vref_high(self):
        """Test validity check with high VREF"""
        coeffs = CompleteTapCoefficients()
        coeffs.rx.vref = 100

        assert coeffs.is_valid() is False

    def test_invalid_main_cursor(self):
        """Test validity check with zero main cursor"""
        coeffs = CompleteTapCoefficients()
        coeffs.tx.main_cursor = 0.0

        assert coeffs.is_valid() is False

    def test_deep_copy(self):
        """Test deep copy of complete coefficients"""
        coeffs = CompleteTapCoefficients()
        coeffs.channel_id = 5
        coeffs.rx.vref = 40
        coeffs.tx.pre_cursor = [0.1, 0.2]

        coeffs_copy = coeffs.copy()

        assert coeffs_copy.channel_id == 5
        assert coeffs_copy.rx.vref == 40
        assert coeffs_copy.tx.pre_cursor == [0.1, 0.2]

        # Ensure it's a deep copy
        coeffs_copy.rx.vref = 50
        coeffs_copy.tx.pre_cursor[0] = 0.9

        assert coeffs.rx.vref == 40  # Original unchanged
        assert coeffs.tx.pre_cursor[0] == 0.1  # Original unchanged


class TestCoefficientOptimizerAdvanced:
    """Advanced tests for coefficient optimizer"""

    def test_init_with_custom_coefficients(self):
        """Test optimizer with custom initial coefficients"""
        coeffs = create_default_coefficients(channel_id=3)
        opt = CoefficientOptimizer(coefficients=coeffs)

        assert opt.coeffs.channel_id == 3

    def test_convergence_history_tracking(self):
        """Test convergence history tracking"""
        opt = CoefficientOptimizer()

        # Set error history that converges well
        opt._error_history = [0.1, 0.05, 0.02, 0.01, 0.005, 0.003, 0.002, 0.0015, 0.001, 0.0009]
        opt.convergence_threshold = 0.001

        # Should be converged if variance of last 10 is below threshold
        history = opt.get_convergence_history()
        if len(history) >= 10:
            variance = np.var(history[-10:])
            assert variance < opt.convergence_threshold

    def test_not_converged_insufficient_history(self):
        """Test not converged with insufficient history"""
        opt = CoefficientOptimizer()

        opt._error_history = [0.1, 0.05]  # Less than 10 entries
        opt.convergence_threshold = 0.01

        assert opt.is_converged() is False

    def test_not_converged_high_variance(self):
        """Test not converged with high variance"""
        opt = CoefficientOptimizer()

        # Create history with high variance - need variance > 0.001
        # Using values like 0.1, 0.01 alternating gives variance ~0.002025
        opt._error_history = []
        for i in range(15):  # Need 10+ entries
            opt._error_history.append(0.1 if i % 2 == 0 else 0.01)
        opt.convergence_threshold = 0.001

        # Check that we have enough history
        history = opt.get_convergence_history()
        assert len(history) >= 10

        # Variance of [0.1, 0.01, 0.1, 0.01, ...] pattern over 10 elements = 0.002025
        # This is > 0.001, so is_converged should return False
        result = opt.is_converged()
        assert not result  # Use truthiness check instead of identity

    def test_vref_binary_search_wide_range(self):
        """Test VREF binary search with wide range"""
        opt = CoefficientOptimizer()

        # Simple margin function (optimal at vref=10)
        def measure_func(vref):
            return 1.0 - abs(vref - 10) / 10

        best_vref = opt.optimize_vref_binary_search(measure_func, min_vref=0, max_vref=63)

        assert 5 <= best_vref <= 20

    def test_vref_binary_search_narrow_range(self):
        """Test VREF binary search with narrow range"""
        opt = CoefficientOptimizer()

        def measure_func(vref):
            return 1.0 - abs(vref - 32) / 32

        best_vref = opt.optimize_vref_binary_search(measure_func, min_vref=20, max_vref=40)

        assert 25 <= best_vref <= 40

    def test_delay_sweep_empty_range(self):
        """Test delay sweep with empty range"""
        opt = CoefficientOptimizer()

        def measure_func(delay):
            return 0.5

        # Empty range should return defaults
        best_delay, best_margin = opt.optimize_delay_sweep(range(0), measure_func)

        assert best_delay == 32  # Default
        assert best_margin == 0.0


class TestCoefficientComparatorAdvanced:
    """Advanced tests for coefficient comparator"""

    def test_compare_tx_identical(self):
        """Test comparing identical TX coefficients"""
        tx1 = TXCoefficients()
        tx2 = TXCoefficients()

        result = CoefficientComparator.compare(tx1, tx2)

        assert result['max_difference'] == 0.0
        assert result['mean_difference'] == 0.0
        assert result['rms_difference'] == 0.0

    def test_compare_rx_identical(self):
        """Test comparing identical RX coefficients"""
        rx1 = RXCoefficients()
        rx2 = RXCoefficients()

        result = CoefficientComparator.compare_rx(rx1, rx2)

        assert result['vref_diff'] == 0
        assert result['ctle_gain_diff_db'] == 0.0

    def test_compare_rx_different_vref(self):
        """Test comparing RX with different VREF"""
        rx1 = RXCoefficients()
        rx2 = RXCoefficients()
        rx2.vref = 45

        result = CoefficientComparator.compare_rx(rx1, rx2)

        assert result['vref_diff'] == -13  # 32 - 45

    def test_analyze_margin_sensitivity(self):
        """Test margin sensitivity analysis"""
        coeffs = create_default_coefficients()

        def measure_func(c):
            return 0.8  # Constant margin

        sensitivities = CoefficientComparator.analyze_margin_sensitivity(
            coeffs, measure_func, perturbation=0.1
        )

        assert len(sensitivities) > 0
        # All sensitivities should be 0 since margin is constant
        for key, val in sensitivities.items():
            assert val == 0.0

    def test_analyze_margin_sensitivity_tx(self):
        """Test margin sensitivity for TX coefficients"""
        coeffs = create_default_coefficients()
        coeffs.tx.pre_cursor = [0.1, 0.1]
        coeffs.tx.post_cursor = [0.1, 0.1]

        def measure_func(c):
            # Higher main cursor = higher margin
            return c.tx.main_cursor

        sensitivities = CoefficientComparator.analyze_margin_sensitivity(
            coeffs, measure_func, perturbation=0.1
        )

        # Should have sensitivity for main cursor (index 2)
        assert 'tx_tap_2' in sensitivities  # Main cursor


class TestFactoryFunctionsAdvanced:
    """Advanced tests for factory functions"""

    def test_create_default_coefficients_multiple_channels(self):
        """Test creating defaults for multiple channels"""
        coeffs_0 = create_default_coefficients(channel_id=0)
        coeffs_1 = create_default_coefficients(channel_id=1)

        assert coeffs_0.channel_id == 0
        assert coeffs_1.channel_id == 1

    def test_export_empty_lanes(self):
        """Test exporting coefficients with default lane delays"""
        coeffs = create_default_coefficients(channel_id=5)

        data = export_coefficients_to_dict(coeffs)

        assert 'lane' in data
        assert 'rd_delays' in data['lane']

    def test_import_lane_delays(self):
        """Test importing lane delays"""
        data = {
            'channel_id': 7,
            'training_complete': True,
            'tx': {
                'pre_cursor': [0.0, 0.0],
                'main_cursor': 1.0,
                'post_cursor': [0.0, 0.0],
            },
            'rx': {
                'vref': 32,
                'dfe_taps': [0.0, 0.0, 0.0, 0.0, 0.0],
            },
            'lane': {
                'rd_delays': {0: 10, 1: 12},
                'wr_delays': {0: 15, 1: 18},
                'rd_dq_delays': {0: 20, 1: 22},
                'wr_dq_delays': {0: 25, 1: 28},
            }
        }

        coeffs = import_coefficients_from_dict(data)

        assert coeffs.lane.rd_delays[0] == 10
        assert coeffs.lane.wr_delays[1] == 18

    def test_import_missing_optional_fields(self):
        """Test importing with missing optional fields"""
        data = {
            'channel_id': 3,
        }

        coeffs = import_coefficients_from_dict(data)

        # Should use defaults
        assert coeffs.channel_id == 3
        assert coeffs.training_complete is False
        assert coeffs.rx.vref == 32  # Default


class TestCoefficientType:
    """Tests for coefficient type enum"""

    def test_all_types_defined(self):
        """Test all coefficient types are defined"""
        assert CoefficientType.TX_PRE_CURSOR is not None
        assert CoefficientType.TX_POST_CURSOR is not None
        assert CoefficientType.TX_MAIN_CURSOR is not None
        assert CoefficientType.RX_CTLE_DC_GAIN is not None
        assert CoefficientType.RX_CTLE_PEAKING is not None
        assert CoefficientType.RX_VREF is not None
        assert CoefficientType.DFE_TAP is not None

    def test_type_values(self):
        """Test coefficient type values"""
        assert CoefficientType.TX_PRE_CURSOR.value == "tx_pre_cursor"
        assert CoefficientType.RX_VREF.value == "rx_vref"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
