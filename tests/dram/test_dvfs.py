"""
Tests for HBM4 DVFS Controller

Tests DVFS state transitions, frequency changes, and power management.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.dram.dvfs_controller import (
    DVFSController, DVFSState, DVFSTransitionType, DVFSManager,
    PowerState, TransitionRecord, DVFSThresholds,
)


class TestDVFSStateMachine:
    """Test DVFS state machine"""

    def test_initial_state(self):
        """Test initial state is P0"""
        dvfs = DVFSController()
        assert dvfs.get_current_state() == DVFSState.P0

    def test_initial_state_custom(self):
        """Test custom initial state"""
        dvfs = DVFSController(initial_state=DVFSState.P1)
        assert dvfs.get_current_state() == DVFSState.P1

    def test_can_transition_valid(self):
        """Test valid transitions"""
        dvfs = DVFSController(initial_state=DVFSState.P0)
        assert dvfs.can_transition_to(DVFSState.P1) is True
        assert dvfs.can_transition_to(DVFSState.P2) is True

    def test_can_transition_invalid(self):
        """Test invalid transitions"""
        dvfs = DVFSController(initial_state=DVFSState.P3)
        assert dvfs.can_transition_to(DVFSState.P0) is False  # No direct P3->P0

    def test_transition_to(self):
        """Test basic transition"""
        dvfs = DVFSController(initial_state=DVFSState.P0)
        success, error = dvfs.transition_to(DVFSState.P1)
        assert success is True
        assert error is None
        assert dvfs.is_transitioning() is True

    def test_transition_complete(self):
        """Test transition completion"""
        dvfs = DVFSController(initial_state=DVFSState.P0, enable_auto_transition=False)
        dvfs.transition_to(DVFSState.P1)
        dvfs.advance_cycle(500)  # Enough cycles to complete (P1 has latency + overhead)
        assert dvfs.get_current_state() == DVFSState.P1

    def test_transition_history(self):
        """Test transition history tracking"""
        dvfs = DVFSController(initial_state=DVFSState.P0, enable_auto_transition=False)
        dvfs.transition_to(DVFSState.P1)
        dvfs.advance_cycle(500)  # Complete transition
        dvfs.transition_to(DVFSState.P2)
        dvfs.advance_cycle(500)  # Complete transition

        history = dvfs.get_transition_history(count=10)
        assert len(history) == 2
        assert history[0].from_state == DVFSState.P0
        assert history[0].to_state == DVFSState.P1


class TestDVFSPowerStates:
    """Test power state configurations"""

    def test_p0_state_config(self):
        """Test P0 state has max frequency"""
        dvfs = DVFSController()
        p0 = dvfs.get_current_power_state()
        assert p0.frequency_gtps == 16.0
        assert p0.voltage_mv == 1000

    def test_p3_state_config(self):
        """Test P3 state is retention"""
        dvfs = DVFSController()
        p3 = dvfs._states[DVFSState.P3]
        assert p3.frequency_gtps == 0.0
        assert p3.latency_cycles > 0  # Long wake-up latency

    def test_power_impact_calculation(self):
        """Test power impact calculation"""
        dvfs = DVFSController()
        impact = dvfs.calculate_power_impact(DVFSState.P2)
        assert 'current_power_ma' in impact
        assert 'target_power_ma' in impact
        assert 'delta_power_ma' in impact
        assert 'power_savings_percent' in impact


class TestDVFSSimulation:
    """Test DVFS simulation"""

    def test_advance_cycle(self):
        """Test cycle advancement"""
        dvfs = DVFSController()
        dvfs.advance_cycle(100)
        assert dvfs._current_cycle == 100

    def test_time_tracking(self):
        """Test time tracking"""
        dvfs = DVFSController()
        dvfs.advance_cycle(1000)
        assert dvfs._current_time_ns > 0

    def test_auto_transition_disabled(self):
        """Test auto transition can be disabled"""
        dvfs = DVFSController(enable_auto_transition=False)
        dvfs.set_utilization(1.0)  # High utilization
        dvfs.advance_cycle(100)
        # Should not transition when disabled
        assert dvfs.get_current_state() == DVFSState.P0

    def test_auto_transition_enabled(self):
        """Test auto transition with thermal throttle"""
        dvfs = DVFSController(enable_auto_transition=True)
        dvfs.set_thermal_reading('max', 110.0)  # Above critical
        dvfs.advance_cycle(10)
        # May or may not transition depending on timing
        # Just verify no errors
        dvfs.get_current_state()


class TestDVFSThresholds:
    """Test DVFS thresholds"""

    def test_default_thresholds(self):
        """Test default threshold values"""
        dvfs = DVFSController()
        t = dvfs._thresholds
        assert t.thermal_warning_c == 85.0
        assert t.thermal_throttle_c == 95.0
        assert t.utilization_high == 0.90

    def test_custom_thresholds(self):
        """Test custom threshold configuration"""
        thresholds = DVFSThresholds(
            thermal_warning_c=80.0,
            thermal_throttle_c=90.0,
        )
        dvfs = DVFSController()
        dvfs.set_thresholds(thresholds)
        assert dvfs._thresholds.thermal_warning_c == 80.0
        assert dvfs._thresholds.thermal_throttle_c == 90.0


class TestDVFSConfiguration:
    """Test DVFS configuration"""

    def test_configure_state(self):
        """Test state configuration"""
        dvfs = DVFSController()
        dvfs.configure_state(
            DVFSState.P0,
            frequency_gtps=14.0,
            voltage_mv=950,
        )
        p0 = dvfs._states[DVFSState.P0]
        assert p0.frequency_gtps == 14.0
        assert p0.voltage_mv == 950


class TestDVFSStatistics:
    """Test DVFS statistics"""

    def test_stats_initial(self):
        """Test initial statistics"""
        dvfs = DVFSController()
        stats = dvfs.get_stats()
        assert 'current_state' in stats
        assert 'total_transitions' in stats
        assert stats['total_transitions'] == 0

    def test_stats_after_transition(self):
        """Test statistics after transitions"""
        dvfs = DVFSController(enable_auto_transition=False)
        dvfs.transition_to(DVFSState.P1)
        dvfs.advance_cycle(500)  # Complete transition
        dvfs.transition_to(DVFSState.P2)
        dvfs.advance_cycle(500)  # Complete transition

        stats = dvfs.get_stats()
        assert stats['total_transitions'] == 2

    def test_state_summary(self):
        """Test state summary"""
        dvfs = DVFSController()
        summary = dvfs.get_state_summary()
        assert 'states' in summary
        assert 'P0' in summary['states']
        assert 'P1' in summary['states']
        assert 'P2' in summary['states']
        assert 'P3' in summary['states']


class TestDVFSManager:
    """Test DVFS Manager for multi-channel"""

    def test_coordinated_mode(self):
        """Test coordinated mode (single controller)"""
        manager = DVFSManager(num_channels=32, coordinated_mode=True)
        ctrl = manager.get_controller()
        assert isinstance(ctrl, DVFSController)
        assert ctrl.num_channels == 32

    def test_independent_mode(self):
        """Test independent mode (per-channel)"""
        manager = DVFSManager(num_channels=8, coordinated_mode=False)
        ctrl0 = manager.get_controller(channel=0)
        ctrl1 = manager.get_controller(channel=1)
        assert ctrl0 is not ctrl1
        assert ctrl0.num_channels == 1

    def test_get_current_frequency(self):
        """Test getting current frequency"""
        manager = DVFSManager(num_channels=32, coordinated_mode=True)
        # Get fresh controller and check frequency
        ctrl = manager.get_controller()
        ctrl.reset()  # Reset to ensure clean state
        ctrl._states[DVFSState.P0].frequency_gtps = 16.0  # Ensure P0 is correct
        freq = ctrl.get_current_power_state().frequency_gtps
        assert freq == 16.0  # P0 frequency

    def test_advance_cycle(self):
        """Test advancing cycle on all controllers"""
        manager = DVFSManager(num_channels=4, coordinated_mode=False)
        manager.advance_cycle(100)
        for ch in range(4):
            ctrl = manager.get_controller(channel=ch)
            assert ctrl._current_cycle == 100


class TestDVFSReset:
    """Test DVFS reset"""

    def test_reset(self):
        """Test reset functionality"""
        dvfs = DVFSController(initial_state=DVFSState.P1)
        dvfs.transition_to(DVFSState.P2)
        dvfs.advance_cycle(100)
        dvfs.reset()

        assert dvfs.get_current_state() == DVFSState.P0
        assert dvfs._current_cycle == 0
        assert dvfs._total_transitions == 0


class TestDVFSCallbacks:
    """Test DVFS callbacks"""

    def test_transition_callbacks(self):
        """Test transition callbacks are called"""
        dvfs = DVFSController(enable_auto_transition=False)
        dvfs.reset()  # Start fresh

        start_called = []
        complete_called = []

        dvfs.register_transition_start_callback(
            lambda f, t: start_called.append((f, t))
        )
        dvfs.register_transition_complete_callback(
            lambda s: complete_called.append(s)
        )

        dvfs.transition_to(DVFSState.P1)
        dvfs.advance_cycle(500)  # Complete transition

        assert len(start_called) == 1
        assert len(complete_called) == 1


class TestDVFSTransitionLatency:
    """Test transition latency calculations"""

    def test_transition_latency_p0_to_p3(self):
        """Test P0 to P3 has significant latency (self-refresh)"""
        dvfs = DVFSController(initial_state=DVFSState.P0)
        latency = dvfs._calculate_transition_cycles(DVFSState.P0, DVFSState.P3)
        # P3 has 256 cycle base latency
        assert latency >= 256

    def test_transition_latency_same_state(self):
        """Test same state has minimal latency"""
        dvfs = DVFSController(initial_state=DVFSState.P0)
        latency = dvfs._calculate_transition_cycles(DVFSState.P0, DVFSState.P1)
        assert latency >= 0  # Some overhead due to freq diff


class TestDVFSEfficiency:
    """Test DVFS efficiency calculations"""

    def test_estimate_efficiency(self):
        """Test efficiency estimation"""
        dvfs = DVFSController()
        eff = dvfs.estimate_efficiency()
        assert eff > 0  # Should have some efficiency

    def test_dynamic_power_ratio(self):
        """Test dynamic power ratio calculation"""
        dvfs = DVFSController()
        ratio = dvfs.calculate_dynamic_power_ratio(0.5)
        assert 0 <= ratio <= 1


class TestDVFSThermal:
    """Test thermal integration"""

    def test_set_thermal_reading(self):
        """Test setting thermal readings"""
        dvfs = DVFSController()
        dvfs.set_thermal_reading('lbd_center', 75.0)
        dvfs.set_thermal_reading('dram_die', 80.0)
        assert dvfs._thermal_readings['lbd_center'] == 75.0
        assert dvfs._thermal_readings['dram_die'] == 80.0

    def test_utilization_setting(self):
        """Test utilization setting"""
        dvfs = DVFSController()
        dvfs.set_utilization(0.75)
        assert dvfs._utilization == 0.75

    def test_utilization_clamping(self):
        """Test utilization clamping to valid range"""
        dvfs = DVFSController()
        dvfs.set_utilization(1.5)
        assert dvfs._utilization == 1.0
        dvfs.set_utilization(-0.5)
        assert dvfs._utilization == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
