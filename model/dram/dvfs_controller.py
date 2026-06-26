"""
HBM4 DVFS (Dynamic Voltage/Frequency Scaling) Controller

Implements voltage and frequency scaling for HBM4 power management:
- Voltage/frequency state machine with multiple power states
- DVS (Dynamic Voltage Scaling) support
- DFS (Dynamic Frequency Scaling) support
- Transition latency modeling
- Power impact calculation
- Thermal impact tracking
- JEDEC JESD270-4A compliance

DVFS STATES:
============
HBM4 supports multiple performance states (P-states) that trade off
bandwidth for power consumption:

  P0: Maximum performance (16 GT/s, nominal voltage)
  P1: High performance (12 GT/s, reduced voltage)
  P2: Balanced (8 GT/s, minimum voltage)
  P3: Low power (idle/retention)

Based on:
- JEDEC JESD270-4A HBM4 specification
- JEDEC JESD78C DDR DRAM肖特基二极管闭锁测试
- Intel Speed Shift technology
- AMD Infinity Fabric power management
"""

from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import math


class DVFSState(Enum):
    """DVFS power states"""
    P0 = "P0"       # Maximum performance
    P1 = "P1"       # High performance
    P2 = "P2"       # Balanced
    P3 = "P3"       # Low power
    TRANSITIONING = "transitioning"
    ERROR = "error"


class DVFSTransitionType(Enum):
    """Type of DVFS transition"""
    UP = "up"           # Increase frequency/voltage
    DOWN = "down"       # Decrease frequency/voltage
    SAME = "same"       # Same state (no change)


@dataclass
class PowerState:
    """Power state configuration"""
    state: DVFSState
    frequency_gtps: float       # Data rate in GT/s
    voltage_mv: float           # Core voltage in mV
    vdd_voltage_mv: float       # VDD voltage in mV
    vddq_voltage_mv: float      # VDDQ voltage in mV
    power_ma: float             # Typical current in mA
    power_static_ma: float      # Static/leakage current in mA
    power_dynamic_ma: float     # Dynamic current in mA
    thermal_theta: float        # Thermal resistance (C/W)
    latency_cycles: int         # Transition latency in cycles
    latency_ns: int             # Transition latency in ns


@dataclass
class TransitionRecord:
    """Record of a DVFS transition"""
    timestamp_ns: int
    from_state: DVFSState
    to_state: DVFSState
    transition_type: DVFSTransitionType
    latency_cycles: int
    latency_ns: int
    power_impact_ma: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class DVFSThresholds:
    """DVFS trigger thresholds"""
    thermal_warning_c: float = 85.0
    thermal_throttle_c: float = 95.0
    thermal_critical_c: float = 105.0
    utilization_high: float = 0.90     # 90% triggers throttle
    utilization_low: float = 0.30     # 30% allows power down
    traffic_threshold_bw: float = 0.5  # 50% bandwidth threshold


class DVFSController:
    """HBM4 DVFS Controller

    Manages dynamic voltage and frequency scaling for HBM4 power efficiency.
    Implements a state machine that transitions between performance states
    based on thermal conditions, utilization, and traffic patterns.

    USAGE:
    ======
    ```python
    dvfs = DVFSController(num_channels=32)

    # Check current state
    state = dvfs.get_current_state()

    # Request state change (if allowed)
    if dvfs.can_transition_to(DVFSState.P1):
        dvfs.transition_to(DVFSState.P1)

    # Advance simulation
    dvfs.advance_cycle(1000)

    # Query power impact
    power = dvfs.calculate_power_impact(DVFSState.P1)
    ```

    INTEGRATION:
    ===========
    - Thermal Model: Read temperatures to trigger throttling
    - Traffic Monitor: Read utilization to optimize power states
    - Controller: Apply frequency changes to timing
    - Power Estimator: Read power state for accurate estimation
    """

    # Default HBM4 power states (based on JESD270-4A)
    DEFAULT_STATES: Dict[DVFSState, PowerState] = {
        DVFSState.P0: PowerState(
            state=DVFSState.P0,
            frequency_gtps=16.0,
            voltage_mv=1000,      # Nominal core voltage
            vdd_voltage_mv=1000,
            vddq_voltage_mv=675,
            power_ma=2500,        # Full power at 16 GT/s
            power_static_ma=100,   # ~100mA leakage
            power_dynamic_ma=2400,
            thermal_theta=0.5,    # C/W
            latency_cycles=0,     # No transition
            latency_ns=0,
        ),
        DVFSState.P1: PowerState(
            state=DVFSState.P1,
            frequency_gtps=12.0,
            voltage_mv=950,       # Reduced voltage
            vdd_voltage_mv=950,
            vddq_voltage_mv=650,
            power_ma=1800,        # Reduced power at 12 GT/s
            power_static_ma=95,
            power_dynamic_ma=1705,
            thermal_theta=0.5,
            latency_cycles=0,
            latency_ns=0,
        ),
        DVFSState.P2: PowerState(
            state=DVFSState.P2,
            frequency_gtps=8.0,
            voltage_mv=850,       # Minimum operational voltage
            vdd_voltage_mv=850,
            vddq_voltage_mv=625,
            power_ma=1200,        # Low power at 8 GT/s
            power_static_ma=90,
            power_dynamic_ma=1110,
            thermal_theta=0.5,
            latency_cycles=0,
            latency_ns=0,
        ),
        DVFSState.P3: PowerState(
            state=DVFSState.P3,
            frequency_gtps=0.0,   # Retention/self-refresh
            voltage_mv=600,       # Retention voltage
            vdd_voltage_mv=600,
            vddq_voltage_mv=600,
            power_ma=50,          # Minimal power
            power_static_ma=40,
            power_dynamic_ma=10,
            thermal_theta=0.5,
            latency_cycles=256,    # Long wake-up latency
            latency_ns=16000,      # 16 us self-refresh exit
        ),
    }

    def __init__(
        self,
        num_channels: int = 32,
        initial_state: DVFSState = DVFSState.P0,
        enable_auto_transition: bool = True,
        enable_dvs: bool = True,
        enable_dfs: bool = True,
    ):
        """Initialize DVFS Controller

        Args:
            num_channels: Number of HBM channels
            initial_state: Starting power state
            enable_auto_transition: Enable automatic state transitions
            enable_dvs: Enable dynamic voltage scaling
            enable_dfs: Enable dynamic frequency scaling
        """
        self.num_channels = num_channels
        self.enable_auto_transition = enable_auto_transition
        self.enable_dvs = enable_dvs
        self.enable_dfs = enable_dfs

        # State machine
        self._current_state = initial_state
        self._target_state: Optional[DVFSState] = None
        self._transition_start_ns: Optional[int] = None
        self._transition_latency_cycles: int = 0

        # Power states configuration - copy to avoid sharing
        self._states: Dict[DVFSState, PowerState] = {}
        for state, ps in self.DEFAULT_STATES.items():
            self._states[state] = PowerState(
                state=ps.state,
                frequency_gtps=ps.frequency_gtps,
                voltage_mv=ps.voltage_mv,
                vdd_voltage_mv=ps.vdd_voltage_mv,
                vddq_voltage_mv=ps.vddq_voltage_mv,
                power_ma=ps.power_ma,
                power_static_ma=ps.power_static_ma,
                power_dynamic_ma=ps.power_dynamic_ma,
                thermal_theta=ps.thermal_theta,
                latency_cycles=ps.latency_cycles,
                latency_ns=ps.latency_ns,
            )

        # Simulation state
        self._current_cycle: int = 0
        self._current_time_ns: int = 0

        # Transition history
        self._transition_history: List[TransitionRecord] = []
        self._max_history: int = 1000

        # Thresholds
        self._thresholds = DVFSThresholds()

        # Statistics
        self._total_transitions: int = 0
        self._transition_count_by_state: Dict[DVFSState, int] = {
            state: 0 for state in DVFSState
        }
        self._time_in_state: Dict[DVFSState, int] = {
            state: 0 for state in DVFSState
        }
        self._last_state_change_ns: int = 0

        # External inputs for auto-transition decisions
        self._thermal_readings: Dict[str, float] = {}
        self._utilization: float = 0.0
        self._traffic_bandwidth: float = 0.0

        # Callbacks
        self._on_transition_start: Optional[Callable] = None
        self._on_transition_complete: Optional[Callable] = None
        self._on_throttle_start: Optional[Callable] = None

        # Transition constraints (which transitions are allowed)
        self._allowed_transitions: Dict[DVFSState, List[DVFSState]] = {
            DVFSState.P0: [DVFSState.P1, DVFSState.P2],
            DVFSState.P1: [DVFSState.P0, DVFSState.P2, DVFSState.P3],
            DVFSState.P2: [DVFSState.P0, DVFSState.P1, DVFSState.P3],
            DVFSState.P3: [DVFSState.P1, DVFSState.P2],
        }

    # ==================== State Machine ====================

    def get_current_state(self) -> DVFSState:
        """Get current DVFS state"""
        return self._current_state

    def get_current_power_state(self) -> PowerState:
        """Get current power state configuration"""
        return self._states[self._current_state]

    def is_transitioning(self) -> bool:
        """Check if currently in transition"""
        return self._current_state == DVFSState.TRANSITIONING

    def can_transition_to(self, target_state: DVFSState) -> bool:
        """Check if transition to target state is allowed

        Args:
            target_state: Desired state

        Returns:
            True if transition is allowed
        """
        if self._current_state == DVFSState.TRANSITIONING:
            return False
        if self._current_state == DVFSState.ERROR:
            return False
        if target_state == DVFSState.TRANSITIONING:
            return False
        if target_state == DVFSState.ERROR:
            return False

        # Check allowed transitions
        allowed = self._allowed_transitions.get(self._current_state, [])
        return target_state in allowed

    def transition_to(
        self,
        target_state: DVFSState,
        force: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Request transition to a new power state

        Args:
            target_state: Desired power state
            force: Force transition even if not normally allowed

        Returns:
            Tuple of (success, error_message)
        """
        # Check if already in transition
        if self._current_state == DVFSState.TRANSITIONING:
            return False, "Already in transition"

        # Check transition validity
        if not force and not self.can_transition_to(target_state):
            return False, f"Transition from {self._current_state.value} to {target_state.value} not allowed"

        # Record transition
        from_state = self._current_state
        self._target_state = target_state
        self._current_state = DVFSState.TRANSITIONING
        self._transition_start_ns = self._current_time_ns
        self._transition_latency_cycles = self._calculate_transition_cycles(
            from_state, target_state
        )

        # Create transition record
        record = TransitionRecord(
            timestamp_ns=self._current_time_ns,
            from_state=from_state,
            to_state=target_state,
            transition_type=self._classify_transition(from_state, target_state),
            latency_cycles=self._transition_latency_cycles,
            latency_ns=self._transition_latency_cycles * self._get_cycle_time_ns(from_state),
            power_impact_ma=0.0,  # Will be calculated
            success=True,
        )
        self._transition_history.append(record)
        if len(self._transition_history) > self._max_history:
            self._transition_history.pop(0)

        self._total_transitions += 1
        self._transition_count_by_state[target_state] += 1

        # Invoke callback
        if self._on_transition_start:
            self._on_transition_start(from_state, target_state)

        return True, None

    def complete_transition(self) -> bool:
        """Complete the current transition and enter target state

        Returns:
            True if transition was completed
        """
        if self._current_state != DVFSState.TRANSITIONING:
            return False

        if self._target_state is None:
            self._current_state = DVFSState.ERROR
            return False

        # Update time tracking
        if self._last_state_change_ns > 0:
            duration = self._current_time_ns - self._last_state_change_ns
            self._time_in_state[self._current_state] += duration

        self._current_state = self._target_state
        self._last_state_change_ns = self._current_time_ns
        self._target_state = None
        self._transition_start_ns = None

        # Invoke callback
        if self._on_transition_complete:
            self._on_transition_complete(self._current_state)

        return True

    def _calculate_transition_cycles(self, from_state: DVFSState, to_state: DVFSState) -> int:
        """Calculate transition latency in cycles"""
        # Voltage transitions take longer than frequency-only
        from_ps = self._states[from_state]
        to_ps = self._states[to_state]

        voltage_diff = abs(from_ps.voltage_mv - to_ps.voltage_mv)

        # Base latency from target state
        base_latency = to_ps.latency_cycles

        # Add voltage transition overhead (roughly 1 cycle per 10mV change)
        voltage_overhead = int(voltage_diff / 10)

        # Frequency change overhead
        freq_diff = abs(from_ps.frequency_gtps - to_ps.frequency_gtps)
        freq_overhead = int(freq_diff * 2)  # 2 cycles per GT/s change

        return base_latency + voltage_overhead + freq_overhead

    def _classify_transition(
        self,
        from_state: DVFSState,
        to_state: DVFSState,
    ) -> DVFSTransitionType:
        """Classify transition direction"""
        from_ps = self._states[from_state]
        to_ps = self._states[to_state]

        if to_ps.frequency_gtps > from_ps.frequency_gtps:
            return DVFSTransitionType.UP
        elif to_ps.frequency_gtps < from_ps.frequency_gtps:
            return DVFSTransitionType.DOWN
        return DVFSTransitionType.SAME

    def _get_cycle_time_ns(self, state: DVFSState) -> int:
        """Get cycle time in ns for a state"""
        if state == DVFSState.TRANSITIONING:
            # Use target state for cycle time during transition
            if self._target_state and self._target_state in self._states:
                return int(1000 / self._states[self._target_state].frequency_gtps)
            return 1000  # Default
        if state not in self._states:
            return 1000  # Default
        ps = self._states[state]
        if ps.frequency_gtps <= 0:
            return 1000  # Default for retention
        return int(1000 / ps.frequency_gtps)  # 1/frequency in ns

    # ==================== Simulation ====================

    def advance_cycle(self, cycles: int = 1) -> None:
        """Advance simulation by cycles

        Args:
            cycles: Number of cycles to advance
        """
        self._current_cycle += cycles
        cycle_time_ns = self._get_cycle_time_ns(self._current_state)
        self._current_time_ns += cycles * cycle_time_ns

        # Check if transition should complete
        if self._current_state == DVFSState.TRANSITIONING:
            self._transition_latency_cycles -= cycles
            if self._transition_latency_cycles <= 0:
                self.complete_transition()

        # Update time in state
        self._time_in_state[self._current_state] += cycles * cycle_time_ns

        # Auto-transition logic
        if self.enable_auto_transition:
            self._evaluate_auto_transition()

    def _evaluate_auto_transition(self) -> None:
        """Evaluate and perform automatic state transitions"""
        if self._current_state == DVFSState.TRANSITIONING:
            return

        # Thermal throttling
        max_temp = self._thermal_readings.get('max', 45.0)
        if max_temp >= self._thresholds.thermal_critical_c:
            if self.can_transition_to(DVFSState.P2):
                self.transition_to(DVFSState.P2)
                if self._on_throttle_start:
                    self._on_throttle_start("thermal_critical")
                return
        elif max_temp >= self._thresholds.thermal_throttle_c:
            if self.can_transition_to(DVFSState.P1):
                self.transition_to(DVFSState.P1)
                if self._on_throttle_start:
                    self._on_throttle_start("thermal_throttle")
                return

        # Utilization-based transitions
        if self._utilization > self._thresholds.utilization_high:
            # High utilization - try to go faster
            if self._current_state == DVFSState.P1 and self.can_transition_to(DVFSState.P0):
                self.transition_to(DVFSState.P0)
            elif self._current_state == DVFSState.P2:
                if self.can_transition_to(DVFSState.P1):
                    self.transition_to(DVFSState.P1)
                elif self.can_transition_to(DVFSState.P0):
                    self.transition_to(DVFSState.P0)
        elif self._utilization < self._thresholds.utilization_low:
            # Low utilization - try to save power
            if self._current_state == DVFSState.P0 and self.can_transition_to(DVFSState.P1):
                self.transition_to(DVFSState.P1)
            elif self._current_state == DVFSState.P1:
                if self.can_transition_to(DVFSState.P2):
                    self.transition_to(DVFSState.P2)
                elif self.can_transition_to(DVFSState.P3):
                    self.transition_to(DVFSState.P3)

    def set_thermal_reading(self, location: str, temperature_c: float) -> None:
        """Set thermal reading for auto-transition decisions

        Args:
            location: Location name (e.g., 'max', 'lbd_center')
            temperature_c: Temperature in Celsius
        """
        self._thermal_readings[location] = temperature_c

    def set_utilization(self, utilization: float) -> None:
        """Set current utilization (0-1)

        Args:
            utilization: Channel utilization (0.0 to 1.0)
        """
        self._utilization = max(0.0, min(1.0, utilization))

    def set_traffic_bandwidth(self, bandwidth: float) -> None:
        """Set current traffic bandwidth (0-1)

        Args:
            bandwidth: Relative bandwidth (0.0 to 1.0)
        """
        self._traffic_bandwidth = max(0.0, min(1.0, bandwidth))

    # ==================== Power Calculations ====================

    def calculate_power_impact(self, target_state: DVFSState) -> Dict[str, float]:
        """Calculate power impact of transitioning to a state

        Args:
            target_state: Target power state

        Returns:
            Dictionary with power metrics
        """
        current_ps = self._states[self._current_state]
        target_ps = self._states[target_state]

        current_power = self._calculate_power(current_ps)
        target_power = self._calculate_power(target_ps)

        return {
            'current_power_ma': current_power,
            'target_power_ma': target_power,
            'delta_power_ma': target_power - current_power,
            'power_savings_percent': (
                (current_power - target_power) / current_power * 100
                if current_power > 0 else 0
            ),
            'current_frequency_gtps': current_ps.frequency_gtps,
            'target_frequency_gtps': target_ps.frequency_gtps,
            'current_voltage_mv': current_ps.voltage_mv,
            'target_voltage_mv': target_ps.voltage_mv,
        }

    def _calculate_power(self, ps: PowerState) -> float:
        """Calculate total power for a power state"""
        return ps.power_ma * self.num_channels / 32  # Scale by active channels

    def calculate_dynamic_power_ratio(self, utilization: float) -> float:
        """Calculate dynamic power scaling factor based on utilization

        Args:
            utilization: Channel utilization (0-1)

        Returns:
            Power ratio relative to peak
        """
        # Power scales roughly with frequency * voltage^2 * activity
        ps = self._states[self._current_state]
        v_ratio = ps.voltage_mv / 1000.0  # Normalized to Vdd
        return (utilization ** 1.5) * (v_ratio ** 2)

    def estimate_efficiency(self) -> float:
        """Estimate power efficiency (bandwidth per watt)

        Returns:
            Efficiency in GB/s/mA
        """
        ps = self._states[self._current_state]
        if ps.power_ma <= 0:
            return 0.0

        # Bandwidth in GB/s (per channel)
        bandwidth = ps.frequency_gtps * 1024 / 8  # 1024-bit interface
        power = ps.power_ma * self.num_channels / 32

        return bandwidth / power if power > 0 else 0.0

    # ==================== Configuration ====================

    def configure_state(
        self,
        state: DVFSState,
        frequency_gtps: Optional[float] = None,
        voltage_mv: Optional[float] = None,
        latency_cycles: Optional[int] = None,
    ) -> None:
        """Configure a power state

        Args:
            state: State to configure
            frequency_gtps: Data rate in GT/s
            voltage_mv: Core voltage in mV
            latency_cycles: Transition latency in cycles
        """
        if state not in self._states:
            return

        ps = self._states[state]
        if frequency_gtps is not None:
            ps.frequency_gtps = frequency_gtps
        if voltage_mv is not None:
            ps.voltage_mv = voltage_mv
            ps.vdd_voltage_mv = voltage_mv
        if latency_cycles is not None:
            ps.latency_cycles = latency_cycles
            ps.latency_ns = latency_cycles * self._get_cycle_time_ns(state)

    def set_thresholds(self, thresholds: DVFSThresholds) -> None:
        """Set DVFS trigger thresholds

        Args:
            thresholds: New threshold configuration
        """
        self._thresholds = thresholds

    # ==================== Statistics ====================

    def get_transition_history(
        self,
        count: int = 100,
    ) -> List[TransitionRecord]:
        """Get recent transition history

        Args:
            count: Number of records to return

        Returns:
            List of TransitionRecord
        """
        return self._transition_history[-count:]

    def get_stats(self) -> Dict[str, Any]:
        """Get DVFS statistics

        Returns:
            Dictionary with statistics
        """
        current_ps = self._states[self._current_state]
        return {
            'current_state': self._current_state.value,
            'current_frequency_gtps': current_ps.frequency_gtps,
            'current_voltage_mv': current_ps.voltage_mv,
            'total_transitions': self._total_transitions,
            'transitions_by_state': {
                k.value: v for k, v in self._transition_count_by_state.items()
            },
            'time_in_state_ns': {
                k.value: v for k, v in self._time_in_state.items()
            },
            'current_cycle': self._current_cycle,
            'current_time_ns': self._current_time_ns,
            'is_transitioning': self.is_transitioning(),
        }

    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of all power states

        Returns:
            Dictionary with state information
        """
        return {
            'states': {
                state.value: {
                    'frequency_gtps': ps.frequency_gtps,
                    'voltage_mv': ps.voltage_mv,
                    'power_ma': ps.power_ma,
                    'latency_cycles': ps.latency_cycles,
                }
                for state, ps in self._states.items()
            },
            'current_state': self._current_state.value,
            'allowed_transitions': {
                state.value: [s.value for s in targets]
                for state, targets in self._allowed_transitions.items()
            },
        }

    def reset(self) -> None:
        """Reset DVFS controller state"""
        self._current_state = DVFSState.P0
        self._target_state = None
        self._transition_start_ns = None
        self._transition_latency_cycles = 0
        self._current_cycle = 0
        self._current_time_ns = 0
        self._transition_history.clear()
        self._total_transitions = 0
        self._transition_count_by_state = {state: 0 for state in DVFSState}
        self._time_in_state = {state: 0 for state in DVFSState}
        self._last_state_change_ns = 0
        self._thermal_readings.clear()
        self._utilization = 0.0
        self._traffic_bandwidth = 0.0

    # ==================== Callbacks ====================

    def register_transition_start_callback(
        self,
        callback: Callable[[DVFSState, DVFSState], None],
    ) -> None:
        """Register callback for transition start events"""
        self._on_transition_start = callback

    def register_transition_complete_callback(
        self,
        callback: Callable[[DVFSState], None],
    ) -> None:
        """Register callback for transition complete events"""
        self._on_transition_complete = callback

    def register_throttle_callback(
        self,
        callback: Callable[[str], None],
    ) -> None:
        """Register callback for throttle events"""
        self._on_throttle_start = callback


class DVFSManager:
    """DVFS Manager for multi-channel HBM4

    Manages DVFS across multiple channels with per-channel or
    global state coordination.
    """

    def __init__(
        self,
        num_channels: int = 32,
        coordinated_mode: bool = True,
    ):
        """Initialize DVFS Manager

        Args:
            num_channels: Number of HBM channels
            coordinated_mode: If True, all channels share same state
        """
        self.num_channels = num_channels
        self.coordinated_mode = coordinated_mode

        if coordinated_mode:
            # Single controller for all channels
            self._global_controller = DVFSController(
                num_channels=num_channels,
            )
            self._channel_controllers = None
        else:
            # Per-channel controllers
            self._global_controller = None
            self._channel_controllers = [
                DVFSController(num_channels=1)
                for _ in range(num_channels)
            ]

    def get_controller(self, channel: Optional[int] = None) -> DVFSController:
        """Get DVFS controller for a channel or global

        Args:
            channel: Channel number (None for global in coordinated mode)

        Returns:
            DVFSController instance
        """
        if self.coordinated_mode:
            return self._global_controller

        if channel is not None and channel < len(self._channel_controllers):
            return self._channel_controllers[channel]

        return self._channel_controllers[0]

    def get_current_frequency(self, channel: Optional[int] = None) -> float:
        """Get current frequency for a channel or global

        Args:
            channel: Channel number (None for global in coordinated mode)

        Returns:
            Frequency in GT/s
        """
        ctrl = self.get_controller(channel)
        return ctrl.get_current_power_state().frequency_gtps

    def advance_cycle(self, cycles: int = 1) -> None:
        """Advance simulation for all controllers

        Args:
            cycles: Number of cycles to advance
        """
        if self.coordinated_mode:
            self._global_controller.advance_cycle(cycles)
        else:
            for ctrl in self._channel_controllers:
                ctrl.advance_cycle(cycles)
