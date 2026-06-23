"""
Common Mock Utilities

Provides common mock components used across all mock implementations:
- MockClock: Clock signal generator
- MockReset: Reset signal generator
- MockSignal: Generic signal wrapper with history tracking
- MockDataBus: Data bus with lane modeling

Usage:
    from tests.mocks import MockClock, MockSignal, MockDataBus

    clock = MockClock(frequency_mhz=800)
    signal = MockSignal(name="test_signal")
    bus = MockDataBus(width=256)

Reference:
- DFI 5.0/5.1 specification
- JEDEC JESD270-4A HBM4 specification
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Union
from collections import deque
import random


# =============================================================================
# MockClock
# =============================================================================

@dataclass
class MockClock:
    """Mock clock generator

    Generates clock signals with configurable frequency and phase.
    Supports both half-frequency (DDR) and full-frequency (SDR) modes.
    """

    def __init__(self, frequency_mhz: float = 800.0, phase_deg: float = 0.0,
                 duty_cycle: float = 0.5, start_value: bool = False):
        """Initialize mock clock

        Args:
            frequency_mhz: Clock frequency in MHz
            phase_deg: Initial phase offset in degrees (0-360)
            duty_cycle: Clock duty cycle (0.0-1.0)
            start_value: Initial clock value
        """
        self.frequency_mhz = frequency_mhz
        self.phase_deg = phase_deg
        self.duty_cycle = duty_cycle
        self._value = start_value
        self._cycle = 0
        self._tick_count = 0

        # Calculate phase offset in ticks (assuming 1 tick = 1/2*fclk for DDR)
        self._phase_offset = int(phase_deg / 360.0 * 2)  # 2 ticks per cycle for DDR

        # Statistics
        self._toggle_count = 0
        self._period_count = 0

    @property
    def value(self) -> bool:
        """Current clock value"""
        return self._value

    @property
    def cycle(self) -> int:
        """Current clock cycle (rising edge count)"""
        return self._cycle

    @property
    def tick_count(self) -> int:
        """Current tick count (including both edges)"""
        return self._tick_count

    def tick(self) -> bool:
        """Advance clock by one tick and return new value

        For DDR clocks, one cycle = 2 ticks (rising + falling edge).
        """
        self._tick_count += 1

        # Determine if we should toggle
        # DDR: toggle every tick
        # SDR: toggle every 2 ticks
        self._value = not self._value
        self._toggle_count += 1

        # Count complete periods
        if self._toggle_count % 2 == 0:
            self._cycle += 1

        return self._value

    def advance(self, num_ticks: int = 1) -> bool:
        """Advance clock by multiple ticks

        Args:
            num_ticks: Number of ticks to advance

        Returns:
            Final clock value after advancement
        """
        for _ in range(num_ticks):
            self.tick()
        return self._value

    def is_rising_edge(self) -> bool:
        """Check if current tick is a rising edge"""
        return self._value  # Value is True after rising edge

    def is_falling_edge(self) -> bool:
        """Check if current tick is a falling edge"""
        return not self._value  # Value is False after falling edge

    def reset(self):
        """Reset clock to initial state"""
        self._value = False
        self._cycle = 0
        self._tick_count = 0
        self._toggle_count = 0

    def get_period_ps(self) -> float:
        """Get clock period in picoseconds"""
        return 1.0 / (self.frequency_mhz * 1e6) * 1e12

    def get_statistics(self) -> Dict[str, Any]:
        """Get clock statistics"""
        return {
            'frequency_mhz': self.frequency_mhz,
            'phase_deg': self.phase_deg,
            'duty_cycle': self.duty_cycle,
            'cycle': self._cycle,
            'tick': self._tick_count,
            'toggle_count': self._toggle_count,
            'current_value': self._value,
        }


# =============================================================================
# MockReset
# =============================================================================

@dataclass
class MockReset:
    """Mock reset signal generator

    Generates reset signals with configurable timing and duration.
    Supports synchronous and asynchronous reset patterns.
    """

    def __init__(self, active_low: bool = True, reset_cycles: int = 10,
                 deassert_cycles: int = 5):
        """Initialize mock reset

        Args:
            active_low: True for active-low reset (RESET_N)
            reset_cycles: Number of cycles to hold reset
            deassert_cycles: Number of cycles before deassert after start
        """
        self.active_low = active_low
        self.reset_cycles = reset_cycles
        self.deassert_cycles = deassert_cycles

        self._asserted = False
        self._cycle = 0
        self._assert_start = 0
        self._in_reset = False
        self._deassert_timer = 0

        # Reset history
        self._history: List[Dict[str, Any]] = []

    @property
    def value(self) -> bool:
        """Current reset signal value"""
        if self.active_low:
            return not self._asserted
        return self._asserted

    @property
    def is_asserted(self) -> bool:
        """Check if reset is currently asserted"""
        return self._asserted

    @property
    def is_active(self) -> bool:
        """Check if reset is active (legacy)"""
        return self.is_asserted

    def assert_reset(self, cycle: Optional[int] = None):
        """Assert reset signal

        Args:
            cycle: Optional cycle to record (defaults to current)
        """
        if not self._asserted:
            self._asserted = True
            self._assert_start = cycle if cycle is not None else self._cycle
            self._in_reset = True
            self._deassert_timer = 0
            self._history.append({
                'event': 'assert',
                'cycle': self._assert_start,
            })

    def deassert_reset(self, cycle: Optional[int] = None):
        """Deassert reset signal

        Args:
            cycle: Optional cycle to record (defaults to current)
        """
        if self._asserted:
            self._asserted = False
            duration = (cycle if cycle is not None else self._cycle) - self._assert_start
            self._in_reset = False
            self._history.append({
                'event': 'deassert',
                'cycle': cycle if cycle is not None else self._cycle,
                'duration': duration,
            })

    def tick(self):
        """Advance simulation by one cycle"""
        self._cycle += 1

        # Auto-deassert after configured duration
        if self._in_reset and self._deassert_timer < self.deassert_cycles:
            self._deassert_timer += 1
            if self._deassert_timer >= self.deassert_cycles:
                self.deassert_reset()

    def pulse(self, duration: Optional[int] = None):
        """Generate a reset pulse

        Args:
            duration: Pulse duration in cycles (defaults to reset_cycles)
        """
        self.assert_reset()
        self._reset_duration = duration if duration is not None else self.reset_cycles
        self._pulse_timer = 0

    def advance(self, num_cycles: int = 1):
        """Advance simulation by multiple cycles

        Args:
            num_cycles: Number of cycles to advance
        """
        for _ in range(num_cycles):
            self.tick()

    def get_history(self) -> List[Dict[str, Any]]:
        """Get reset signal history"""
        return list(self._history)

    def reset(self):
        """Reset the mock reset generator"""
        self._asserted = False
        self._cycle = 0
        self._assert_start = 0
        self._in_reset = False
        self._deassert_timer = 0
        self._history.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get reset statistics"""
        return {
            'active_low': self.active_low,
            'is_asserted': self._asserted,
            'cycle': self._cycle,
            'in_reset': self._in_reset,
            'history_length': len(self._history),
        }


# =============================================================================
# MockSignal
# =============================================================================

@dataclass
class MockSignal:
    """Mock signal with history tracking

    Generic signal wrapper that tracks value changes and history.
    Useful for monitoring signals during test execution.
    """

    def __init__(self, name: str = "signal", width: int = 1,
                 initial_value: Union[int, bool] = 0):
        """Initialize mock signal

        Args:
            name: Signal name for debugging
            width: Signal width in bits
            initial_value: Initial signal value
        """
        self.name = name
        self.width = width
        self._value = initial_value
        self._prev_value = initial_value
        self._cycle = 0

        # History tracking
        self._history: deque = deque(maxlen=1000)
        self._change_count = 0

        # Callbacks
        self._on_change: Optional[Callable] = None

    @property
    def value(self) -> Union[int, bool]:
        """Current signal value"""
        return self._value

    @value.setter
    def value(self, new_value: Union[int, bool]):
        """Set signal value

        Args:
            new_value: New signal value
        """
        if new_value != self._value:
            self._prev_value = self._value
            self._value = new_value
            self._change_count += 1

            # Record in history
            self._history.append({
                'cycle': self._cycle,
                'old_value': self._prev_value,
                'new_value': self._value,
            })

            # Trigger callback
            if self._on_change:
                self._on_change(self._prev_value, self._value, self._cycle)

    @property
    def prev_value(self) -> Union[int, bool]:
        """Previous signal value"""
        return self._prev_value

    def set(self, value: Union[int, bool], cycle: Optional[int] = None):
        """Set signal value

        Args:
            value: New value
            cycle: Optional cycle (uses current if None)
        """
        self._cycle = cycle if cycle is not None else self._cycle
        self.value = value

    def get(self, cycle: Optional[int] = None) -> Union[int, bool]:
        """Get signal value at specific cycle

        Args:
            cycle: Target cycle (returns current if None)

        Returns:
            Signal value at cycle
        """
        if cycle is None:
            return self._value

        # Search history for value at cycle
        for entry in reversed(self._history):
            if entry['cycle'] <= cycle:
                return entry['new_value']
        return self._history[0]['new_value'] if self._history else self._value

    def tick(self):
        """Advance simulation cycle"""
        self._cycle += 1

    def advance(self, num_cycles: int = 1):
        """Advance simulation by multiple cycles

        Args:
            num_cycles: Number of cycles to advance
        """
        self._cycle += num_cycles

    def did_change(self) -> bool:
        """Check if signal changed on last tick"""
        return self._value != self._prev_value

    def set_change_callback(self, callback: Callable):
        """Set callback for signal changes

        Args:
            callback: Function(old_value, new_value, cycle)
        """
        self._on_change = callback

    def get_history(self, max_entries: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get signal change history

        Args:
            max_entries: Maximum entries to return (None for all)

        Returns:
            List of history entries
        """
        if max_entries is None:
            return list(self._history)
        return list(self._history)[-max_entries:]

    def reset(self):
        """Reset signal to initial state"""
        self._value = 0
        self._prev_value = 0
        self._cycle = 0
        self._change_count = 0
        self._history.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get signal statistics"""
        return {
            'name': self.name,
            'width': self.width,
            'current_value': self._value,
            'change_count': self._change_count,
            'history_length': len(self._history),
            'cycle': self._cycle,
        }


# =============================================================================
# MockDataBus
# =============================================================================

@dataclass
class MockDataBus:
    """Mock data bus with lane modeling

    Simulates a parallel data bus with per-lane control and error injection.
    Useful for testing data path operations and lane-level failures.
    """

    def __init__(self, width: int = 256, num_lanes: int = 64,
                 lane_width: int = 4):
        """Initialize mock data bus

        Args:
            width: Total bus width in bits
            num_lanes: Number of data lanes
            lane_width: Width of each lane in bits
        """
        self.width = width
        self.num_lanes = num_lanes
        self.lane_width = lane_width

        # Data storage
        self._data: int = 0
        self._mask: int = 0  # Lane enable mask

        # Lane status
        self._lane_failed: List[bool] = [False] * num_lanes
        self._lane_repaired: List[int] = [0] * num_lanes  # Repair mapping

        # Valid/error signals
        self._valid = False
        self._error = False
        self._error_lanes: List[int] = []

        # Statistics
        self._transfer_count = 0
        self._error_count = 0
        self._lane_failures = 0

        # Callback
        self._on_error: Optional[Callable] = None

    @property
    def data(self) -> int:
        """Current bus data"""
        return self._data

    @data.setter
    def data(self, value: int):
        """Set bus data"""
        self._data = value & ((1 << self.width) - 1)

    @property
    def mask(self) -> int:
        """Current lane mask"""
        return self._mask

    @mask.setter
    def mask(self, value: int):
        """Set lane mask"""
        self._mask = value & ((1 << self.num_lanes) - 1)

    @property
    def valid(self) -> bool:
        """Bus valid signal"""
        return self._valid

    @valid.setter
    def valid(self, value: bool):
        """Set valid signal"""
        self._valid = value

    def write(self, data: int, mask: int = None, lane_indices: List[int] = None):
        """Write data to bus

        Args:
            data: Data to write
            mask: Lane mask (all lanes if None)
            lane_indices: Specific lanes to write (overrides mask)
        """
        self._transfer_count += 1
        self._valid = True

        # Set data
        self._data = data & ((1 << self.width) - 1)

        # Set mask
        if lane_indices is not None:
            self._mask = 0
            for lane in lane_indices:
                if 0 <= lane < self.num_lanes:
                    self._mask |= (1 << lane)
        elif mask is not None:
            self._mask = mask & ((1 << self.num_lanes) - 1)
        else:
            self._mask = (1 << self.num_lanes) - 1  # All lanes

        # Check for lane failures
        self._error = False
        self._error_lanes = []
        for lane in range(self.num_lanes):
            if self._mask & (1 << lane):
                if self._lane_failed[lane]:
                    self._error = True
                    self._error_lanes.append(lane)
                    self._error_count += 1

    def read(self) -> int:
        """Read data from bus

        Returns:
            Bus data with failed lanes masked
        """
        self._valid = False
        data = self._data

        # Mask out failed lanes
        for lane in range(self.num_lanes):
            if self._lane_failed[lane]:
                lane_mask = ((1 << self.lane_width) - 1) << (lane * self.lane_width)
                data &= ~lane_mask

        return data

    def inject_error(self, lane: int = None):
        """Inject error on lane(s)

        Args:
            lane: Specific lane (random if None)
        """
        if lane is not None and 0 <= lane < self.num_lanes:
            self._lane_failed[lane] = True
            self._lane_failures += 1
        else:
            # Random lane
            import random
            random_lane = random.randint(0, self.num_lanes - 1)
            self._lane_failed[random_lane] = True
            self._lane_failures += 1

        self._error = True
        self._error_count += 1

        if self._on_error:
            self._on_error(lane if lane is not None else random_lane)

    def repair_lane(self, failed_lane: int, spare_lane: int):
        """Repair failed lane using spare

        Args:
            failed_lane: Index of failed lane
            spare_lane: Index of spare lane to use
        """
        if 0 <= failed_lane < self.num_lanes and 0 <= spare_lane < self.num_lanes:
            self._lane_repaired[failed_lane] = spare_lane
            self._lane_failed[failed_lane] = False
            self._lane_failed[spare_lane] = True

    def is_lane_failed(self, lane: int) -> bool:
        """Check if lane has failed"""
        return self._lane_failed[lane] if 0 <= lane < self.num_lanes else True

    def get_failed_lanes(self) -> List[int]:
        """Get list of failed lanes"""
        return [i for i, failed in enumerate(self._lane_failed) if failed]

    def set_error_callback(self, callback: Callable):
        """Set callback for lane errors

        Args:
            callback: Function(lane_index)
        """
        self._on_error = callback

    def reset(self):
        """Reset bus state"""
        self._data = 0
        self._mask = 0
        self._valid = False
        self._error = False
        self._error_lanes = []
        self._lane_failed = [False] * self.num_lanes
        self._lane_repaired = [0] * self.num_lanes

    def get_statistics(self) -> Dict[str, Any]:
        """Get bus statistics"""
        return {
            'width': self.width,
            'num_lanes': self.num_lanes,
            'lane_width': self.lane_width,
            'transfer_count': self._transfer_count,
            'error_count': self._error_count,
            'lane_failures': self._lane_failures,
            'failed_lanes': self.get_failed_lanes(),
            'current_data': self._data,
            'current_mask': self._mask,
            'valid': self._valid,
            'has_error': self._error,
        }


# =============================================================================
# MockBitErrorInjector
# =============================================================================

class MockBitErrorInjector:
    """Bit error injector for testing error detection/correction

    Injects random bit errors, stuck-at faults, and pattern errors
    for testing ECC/CRC and error handling logic.
    """

    def __init__(self, error_rate: float = 0.0, seed: int = None):
        """Initialize error injector

        Args:
            error_rate: Probability of error injection (0.0-1.0)
            seed: Random seed for reproducibility
        """
        self.error_rate = error_rate
        self._rng = random.Random(seed)

        # Error counters
        self._total_injections = 0
        self._bit_flip_count = 0
        self._stuck_at_0_count = 0
        self._stuck_at_1_count = 0

        # Stuck-at fault model
        self._stuck_at_faults: Dict[int, int] = {}

    def inject_bit_flip(self, data: int, width: int = 32) -> int:
        """Inject random single-bit flip

        Args:
            data: Input data
            width: Data width in bits

        Returns:
            Data with potentially flipped bit
        """
        self._total_injections += 1

        if self._rng.random() < self.error_rate:
            bit_pos = self._rng.randint(0, width - 1)
            data ^= (1 << bit_pos)
            self._bit_flip_count += 1

        return data

    def inject_double_bit_error(self, data: int, width: int = 32) -> int:
        """Inject double-bit error

        Args:
            data: Input data
            width: Data width in bits

        Returns:
            Data with potentially flipped two bits
        """
        self._total_injections += 1

        if self._rng.random() < self.error_rate:
            bit1 = self._rng.randint(0, width - 1)
            bit2 = self._rng.randint(0, width - 1)
            while bit2 == bit1:
                bit2 = self._rng.randint(0, width - 1)
            data ^= (1 << bit1)
            data ^= (1 << bit2)
            self._bit_flip_count += 2

        return data

    def set_stuck_at_fault(self, bit_pos: int, value: int):
        """Set stuck-at fault on bit

        Args:
            bit_pos: Bit position
            value: Stuck value (0 or 1)
        """
        self._stuck_at_faults[bit_pos] = value

    def apply_stuck_at_faults(self, data: int) -> int:
        """Apply stuck-at faults to data

        Args:
            data: Input data

        Returns:
            Data with stuck-at faults applied
        """
        for bit_pos, value in self._stuck_at_faults.items():
            if value == 0:
                data &= ~(1 << bit_pos)
            else:
                data |= (1 << bit_pos)

        self._total_injections += len(self._stuck_at_faults)
        return data

    def clear_stuck_at_faults(self):
        """Clear all stuck-at faults"""
        self._stuck_at_faults.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get error injector statistics"""
        return {
            'error_rate': self.error_rate,
            'total_injections': self._total_injections,
            'bit_flips': self._bit_flip_count,
            'stuck_at_0': self._stuck_at_0_count,
            'stuck_at_1': self._stuck_at_1_count,
            'active_stuck_at_faults': len(self._stuck_at_faults),
        }

    def reset(self):
        """Reset error injector"""
        self._total_injections = 0
        self._bit_flip_count = 0
        self._stuck_at_0_count = 0
        self._stuck_at_1_count = 0
        self._stuck_at_faults.clear()
