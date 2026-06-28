"""
HBM DRAM Bank State Machine - Optimized Version
Reference design document 2026-06-15-hbm-system-model-design.md Section 5.2.1 and 5.2.2

Optimizations:
- __slots__ for memory reduction
- Frozen dataclass for immutable types
- Batch state checks
- Pre-computed timing values
- Timing lookup table for O(1) access
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import sys


class BankStateEnum(IntEnum):
    """Bank state enum

    Supports both HBM3 and HBM4 state tracking:
    - HBM3 mode: 3-bit encoding (IDLE, ACTIVE, BUSY, REFRESHING, POWERDN, SELFREF)
    - HBM4 mode: Extended 4-bit with intermediate states (ACTIVATING, PRECHARGING)

    HBM4 State Encoding (from JEDEC JESD270-4A):
    - 000=CLOSED, 001=ACTIVATING, 010=OPEN, 011=PRECHARGING
    - 100=READ, 101=WRITE, 110=REFRESH, 111=POWER_DOWN/SELF_REFRESH
    """
    # HBM4 Primary States (JEDEC encoding)
    CLOSED = 0        # 000 - Bank precharged and idle
    ACTIVATING = 1    # 001 - Activation in progress (tRCD period)
    OPEN = 2          # 010 - Row is open and accessible
    PRECHARGING = 3   # 011 - Precharge in progress (tRP period)
    READ = 4          # 100 - Read operation in progress
    WRITE = 5         # 101 - Write operation in progress
    REFRESH = 6       # 110 - Refresh in progress
    POWER_DOWN = 7    # 111 - Power down mode

    # Extended states
    SELF_REFRESH = 8  # Self refresh mode

    # HBM3 compatibility aliases (using RTL 3-bit encoding)
    IDLE = 0          # Same as CLOSED
    ACTIVE = 2        # Same as OPEN
    BUSY = 4          # Same as READ (covers both read/write)
    REFRESHING = 6   # Same as REFRESH
    POWERDN = 7      # Same as POWER_DOWN
    SELFREF = 8      # Same as SELF_REFRESH

    # Legacy aliases
    READING = 4       # Same as READ
    WRITING = 5       # Same as WRITE


class OperationType(IntEnum):
    """Operation type enum"""
    NONE = 0
    READ = 1
    WRITE = 2
    REFRESH = 3


# Pre-computed state masks for fast checking
_STATE_IDLE = 1 << BankStateEnum.IDLE
_STATE_ACTIVE = 1 << BankStateEnum.ACTIVE
_STATE_BUSY = 1 << BankStateEnum.BUSY
_STATE_REFRESHING = 1 << BankStateEnum.REFRESHING
_STATE_ACTIVATING = 1 << BankStateEnum.ACTIVATING
_STATE_PRECHARGING = 1 << BankStateEnum.PRECHARGING


# HBM3 Timing lookup table (default values)
# HBM4 values: nRC=22, nRAS=20, nRCD=8, nRP=8, nRFC=180
_HBM3_TIMING = {
    'nRC': 340, 'nRAS': 320, 'nRCD': 20, 'nRP': 20, 'nRFC': 260,
    'nCL': 20, 'nCWL': 16, 'nCCD': 4, 'nWTRS': 4, 'nRTW': 4,
    # HBM3 aliases
    'tRC': 340, 'tRAS': 320, 'tRCD': 20, 'tRP': 20, 'tRFC': 260,
    'tCL': 20, 'tCWL': 16, 'tCCD': 4,
}

# HBM4 Timing lookup table (from JEDEC JESD270-4A)
# tCK = 125 ps @ 8 GT/s
_HBM4_TIMING = {
    'nRC': 22, 'nRAS': 20, 'nRCD': 8, 'nRP': 8, 'nRFC': 180,
    'nCL': 8, 'nCWL': 3, 'nCCD': 4, 'nWTRS': 4, 'nWTRL': 5, 'nRTW': 4,
    # HBM4 Bank Group timing
    'nCCDS': 2, 'nCCDL': 3, 'nRRDS': 3, 'nRRDL': 4, 'nFAW': 16,
    # HBM4 aliases
    'tRC': 22, 'tRAS': 20, 'tRCD': 8, 'tRP': 8, 'tRFC': 180,
    'tCL': 8, 'tCWL': 3, 'tCCD': 4,
}

# Default timing lookup uses HBM3 values for backward compatibility
_TIMING_LOOKUP = _HBM3_TIMING.copy()


class Bank:
    """DRAM Bank State

    Represents the state of a single DRAM bank.
    """
    __slots__ = ('bank_id', 'state', 'open_row', 'activate_time', 'precharge_time',
                 'last_operation_time', 'read_start_time', 'read_complete_time',
                 'write_start_time', 'write_complete_time', 'refresh_time',
                 'refresh_complete_time', '_cached_state')

    def __init__(self, bank_id: int):
        self.bank_id = bank_id
        self.state = BankStateEnum.IDLE
        self.open_row = -1
        self.activate_time = -1.0
        self.precharge_time = -1.0
        self.last_operation_time = 0.0
        self.read_start_time = -1.0
        self.read_complete_time = -1.0
        self.write_start_time = -1.0
        self.write_complete_time = -1.0
        self.refresh_time = -1.0
        self.refresh_complete_time = -1.0
        self._cached_state = 1 << BankStateEnum.IDLE

    @property
    def is_idle(self) -> bool:
        return self.state == BankStateEnum.IDLE

    @property
    def is_active(self) -> bool:
        return self.state == BankStateEnum.ACTIVE

    @property
    def is_busy(self) -> bool:
        return self.state == BankStateEnum.BUSY

    @property
    def is_refresh(self) -> bool:
        return self.state == BankStateEnum.REFRESHING

    @property
    def is_powered_down(self) -> bool:
        return self.state == BankStateEnum.POWERDN

    @property
    def is_self_refresh(self) -> bool:
        return self.state == BankStateEnum.SELFREF

    @property
    def row_open(self) -> bool:
        return self.is_active and self.open_row >= 0

    @property
    def has_been_activated(self) -> bool:
        """Check if bank has ever been activated"""
        return self.activate_time >= 0

    @property
    def has_been_precharged(self) -> bool:
        """Check if bank has ever been precharged"""
        return self.precharge_time >= 0

    # HBM4 extended state properties
    @property
    def is_closed(self) -> bool:
        """Check if bank is closed (HBM4 compatibility)"""
        return self.state == BankStateEnum.IDLE or self.state == BankStateEnum.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if bank is open (HBM4 compatibility)"""
        return self.state == BankStateEnum.ACTIVE or self.state == BankStateEnum.OPEN

    @property
    def is_activating(self) -> bool:
        """Check if bank is activating (HBM4 extended)"""
        return self.state == BankStateEnum.ACTIVATING

    @property
    def is_precharging(self) -> bool:
        """Check if bank is precharging (HBM4 extended)"""
        return self.state == BankStateEnum.PRECHARGING

    @property
    def is_reading(self) -> bool:
        """Check if bank is reading (HBM4 compatibility)"""
        return self.state == BankStateEnum.BUSY and self.read_start_time >= 0

    @property
    def is_writing(self) -> bool:
        """Check if bank is writing (HBM4 compatibility)"""
        return self.state == BankStateEnum.BUSY and self.write_start_time >= 0

    def update_state(self, new_state: BankStateEnum):
        """Update state with cached flag update"""
        self.state = new_state
        self._cached_state = 1 << new_state

    def __repr__(self) -> str:
        row_str = f"row=0x{self.open_row:x}" if self.open_row >= 0 else "row=closed"
        return f"Bank{self.bank_id}({self.state.name}, {row_str})"


class TimingViolation:
    """Timing violation record"""
    __slots__ = ('violation_type', 'required_time', 'actual_time', 'time_available', 'description')

    def __init__(self, violation_type: str, required_time: float, actual_time: float,
                 time_available: float, description: str):
        self.violation_type = violation_type
        self.required_time = required_time
        self.actual_time = actual_time
        self.time_available = time_available
        self.description = description


class TimingViolationList:
    """Efficient timing violation list"""
    __slots__ = ('_violations', '_capacity')

    def __init__(self, capacity: int = 16):
        self._violations = []
        self._capacity = capacity

    def append(self, violation: TimingViolation):
        self._violations.append(violation)

    def clear(self):
        self._violations.clear()

    def get_all(self) -> list:
        return self._violations.copy()

    def __len__(self) -> int:
        return len(self._violations)


class BankStateMachine:
    """Bank State Machine - Optimized Version

    Manages single bank state transitions and timing constraints.
    Supports HBM3/HBM4 timing parameters with unified state tracking.

    Optimizations:
    - Batch timing checks
    - Pre-computed timing conversions
    - Fast state comparisons using cached masks
    - Timing lookup table for O(1) access
    - No set_time() calls - time passed directly to check methods

    HBM4 Features:
    - Extended state tracking (ACTIVATING, PRECHARGING)
    - Bank group-aware scheduling
    - State transition history
    """

    __slots__ = ('bank_id', 'channel_id', 'pseudo_channel_id', 'bank_group_id',
                 'bank', 'timing', 'current_time', 'timing_violations',
                 '_clock_period_ns', '_clock_period_s', '_timing_cache',
                 '_cache_valid', '_cached_tRC', '_cached_tRAS', '_cached_tRCD',
                 '_cached_tRFC', '_cached_tCL', '_cached_tCWL', '_cached_tCCD',
                 '_is_hbm4', '_activation_complete_time', '_precharge_complete_time',
                 '_last_act_cycle', '_last_col_cmd_cycle', '_last_col_cmd_bg',
                 '_last_col_cmd_is_write')

    def __init__(self, bank_id: int, timing, channel_id: int = 0,
                 pseudo_channel_id: int = 0, bank_group_id: int = 0):
        """Initialize Bank State Machine

        Args:
            bank_id: Bank ID
            timing: Timing parameter object (HBM3Timing or HBM4Timing)
            channel_id: Channel index (0-31, for HBM4)
            pseudo_channel_id: Pseudo-channel index (0-1, for HBM4)
            bank_group_id: Bank group index (0-7, for HBM4)
        """
        # Store IDs as instance attributes for backward compatibility
        self.bank_id = bank_id
        self.channel_id = channel_id
        self.pseudo_channel_id = pseudo_channel_id
        self.bank_group_id = bank_group_id

        self.bank = Bank(bank_id=bank_id)
        self.timing = timing
        self.current_time = 0.0
        self.timing_violations: List[TimingViolation] = []

        # Detect HBM4 mode from timing object
        self._is_hbm4 = self._detect_hbm4_mode()

        # HBM4 extended context (private, for internal tracking)
        self._last_act_cycle = -1
        self._last_col_cmd_cycle = -1
        self._last_col_cmd_bg = -1
        self._last_col_cmd_is_write = False

        # Pre-compute clock period for fast cycles-to-seconds conversion
        # Use timing object's pre-computed value if available
        self._clock_period_s = getattr(timing, '_clock_period_s', None) or 0.78125e-9
        self._clock_period_ns = getattr(timing, '_clock_period_ns', None) or 0.78125

        # Pre-compute all timing values once at init time
        self._timing_cache = {}
        self._cache_valid = False
        self._init_timing_cache()

        # Cache commonly used timing values
        self._cached_tRC = 0
        self._cached_tRAS = 0
        self._cached_tRCD = 0
        self._cached_tRFC = 0
        self._cached_tCL = 0
        self._cached_tCWL = 0
        self._cached_tCCD = 0

    def _detect_hbm4_mode(self) -> bool:
        """Detect if timing object is HBM4

        Returns:
            True if HBM4 timing parameters detected
        """
        # HBM4 has nRCD = 8, HBM3 has nRCD = 17 (or 20 for older specs)
        nRCD = getattr(self.timing, 'nRCD', 0) or getattr(self.timing, 'tRCD', 0)
        if nRCD <= 10:  # HBM4: 8 cycles
            return True
        # Also check for HBM4 timing class
        if type(self.timing).__name__.startswith('HBM4'):
            return True
        return False

    def _init_timing_cache(self):
        """Initialize timing lookup cache at construction time"""
        # Pre-populate cache from timing object
        for name in _TIMING_LOOKUP:
            val = self.get_timing_value(name)
            if val > 0:
                self._timing_cache[name] = val

        # Also cache values from the timing object
        for name in dir(self.timing):
            if not name.startswith('_'):
                val = getattr(self.timing, name)
                if isinstance(val, (int, float)):
                    self._timing_cache[name] = int(val)

    def set_time(self, current_time: float):
        """Set current time (in cycles)

        OPTIMIZATION: This method is called frequently but most of its
        work is deferred. The actual time check is done in the operation
        methods directly.
        """
        self.current_time = current_time

    def _get_cached_timing(self, name: str) -> int:
        """Get timing value from cache (O(1) lookup)

        Args:
            name: Parameter name

        Returns:
            Timing value in cycles
        """
        # Fast path: check cache first
        if name in self._timing_cache:
            return self._timing_cache[name]

        # Fallback: compute and cache
        val = self.get_timing_value(name)
        self._timing_cache[name] = val
        return val

    def _record_violation(self, violation_type: str, required_time: float,
                         actual_time: float, description: str):
        """Record timing violation"""
        violation = TimingViolation(
            violation_type=violation_type,
            required_time=required_time,
            actual_time=actual_time,
            time_available=actual_time,
            description=description
        )
        self.timing_violations.append(violation)

    def get_timing_value(self, name: str) -> int:
        """Get timing parameter value (compatible with HBM3/HBM4 naming)

        Args:
            name: Parameter name (e.g., 'tRCD', 'nRCD', 'tRC', 'nRC', etc.)

        Returns:
            Timing parameter value (in cycles)
        """
        # Priority: timing object > mode-specific table > generic table
        # HBM4 n-prefix priority
        if hasattr(self.timing, name):
            return getattr(self.timing, name)
        # HBM3 t-prefix fallback
        hbm3_name = name.replace('n', 't', 1) if name.startswith('n') else name
        if hasattr(self.timing, hbm3_name):
            return getattr(self.timing, hbm3_name)
        # Check mode-specific table
        if self._is_hbm4 and name in _HBM4_TIMING:
            return _HBM4_TIMING[name]
        if name in _HBM3_TIMING:
            return _HBM3_TIMING[name]
        # Default to 0
        return 0

    # =========================================================================
    # Activation State Transitions
    # =========================================================================

    def can_activate(self) -> bool:
        """Check if activation can be initiated

        Timing constraints:
        - Bank must be IDLE
        - Must be >= tRC since last operation (ACT or PRE)
        """
        if self.bank.state != BankStateEnum.IDLE:
            return False

        # If never activated, can activate
        if self.bank.activate_time < 0:
            return True

        # tRC: Minimum interval between consecutive ACTs on same bank
        time_since_last = self.current_time - self.bank.last_operation_time
        # Use cached timing value directly
        tRC = self._get_cached_timing('nRC')
        tRC_seconds = self._cycles_to_seconds(tRC)
        return time_since_last >= tRC_seconds

    def activate(self, row: int) -> Tuple[bool, Optional[str]]:
        """Activate Bank

        Args:
            row: Row number to activate

        Returns:
            (success flag, error message)
        """
        # Use cached timing value directly (no refresh needed)
        tRC = self._get_cached_timing('nRC')
        tRC_seconds = self._cycles_to_seconds(tRC)

        if self.bank.state != BankStateEnum.IDLE:
            return False, f"Bank {self.bank.bank_id} not idle (state={self.bank.state.name})"

        # If ever activated, must satisfy tRC
        if self.bank.activate_time >= 0:
            time_since_last = self.current_time - self.bank.last_operation_time
            if time_since_last < tRC_seconds:
                msg = f"tRC violation: need {tRC_seconds}s, have {time_since_last}s"
                self._record_violation('tRC', tRC, time_since_last, msg)
                return False, msg

        # HBM4 mode: use intermediate ACTIVATING state
        if self._is_hbm4:
            self.bank.update_state(BankStateEnum.ACTIVATING)
            # Record activation complete time (after tRCD)
            tRCD = self._get_cached_timing('nRCD')
            self.bank.activate_time = self.current_time  # Start time
            self._activation_complete_time = self.current_time + tRCD
        else:
            self.bank.update_state(BankStateEnum.ACTIVE)

        self.bank.open_row = row
        self.bank.last_operation_time = self.current_time
        self._last_act_cycle = int(self.current_time)
        return True, None

    def complete_activation(self) -> bool:
        """Complete activation transition (HBM4)

        Call this after tRCD cycles have elapsed.

        Returns:
            True if activation was completed
        """
        if self.bank.state != BankStateEnum.ACTIVATING:
            return True  # Already completed or not in activating state

        if hasattr(self, '_activation_complete_time'):
            if self.current_time < self._activation_complete_time:
                return False

        self.bank.update_state(BankStateEnum.ACTIVE)
        return True

    # =========================================================================
    # Precharge State Transitions
    # =========================================================================

    def can_precharge(self) -> bool:
        """Check if precharge can be initiated

        Timing constraints:
        - Bank must be ACTIVE (or BUSY but READ/WRITE complete)
        - Must be >= tRAS since ACT
        """
        # Fast state check using cached mask
        state_mask = self.bank._cached_state
        if state_mask & (_STATE_ACTIVE | _STATE_BUSY) == 0:
            return False

        # If BUSY, check if operation complete
        if state_mask & _STATE_BUSY:
            if not self._is_operation_complete():
                return False

        time_since_act = self.current_time - self.bank.activate_time
        tRAS = self._get_cached_timing('nRAS')
        tRAS_seconds = self._cycles_to_seconds(tRAS)
        return time_since_act >= tRAS_seconds

    def precharge(self) -> Tuple[bool, Optional[str]]:
        """Close Bank

        Returns:
            (success flag, error message)
        """
        state_mask = self.bank._cached_state
        if state_mask & (_STATE_ACTIVE | _STATE_BUSY) == 0:
            return False, f"Bank {self.bank.bank_id} not active (state={self.bank.state.name})"

        # Check tRAS using cached value
        time_since_act = self.current_time - self.bank.activate_time
        tRAS = self._get_cached_timing('nRAS')
        tRAS_seconds = self._cycles_to_seconds(tRAS)
        if time_since_act < tRAS_seconds:
            msg = f"tRAS violation: need {tRAS} cycles ({tRAS_seconds}s), have {time_since_act}s"
            self._record_violation('tRAS', tRAS, time_since_act, msg)
            return False, msg

        # HBM4 mode: use intermediate PRECHARGING state
        if self._is_hbm4:
            self.bank.update_state(BankStateEnum.PRECHARGING)
            tRP = self._get_cached_timing('nRP')
            self._precharge_complete_time = self.current_time + tRP
        else:
            self.bank.update_state(BankStateEnum.IDLE)
            self.bank.open_row = -1
            self.bank.precharge_time = self.current_time
            self.bank.last_operation_time = self.current_time
        return True, None

    def complete_precharge(self) -> bool:
        """Complete precharge transition (HBM4)

        Call this after tRP cycles have elapsed.

        Returns:
            True if precharge was completed
        """
        if self.bank.state != BankStateEnum.PRECHARGING:
            return True  # Already completed or not in precharging state

        if hasattr(self, '_precharge_complete_time'):
            if self.current_time < self._precharge_complete_time:
                return False

        self.bank.update_state(BankStateEnum.IDLE)
        self.bank.open_row = -1
        self.bank.precharge_time = self.current_time
        self.bank.last_operation_time = self.current_time
        return True

    # =========================================================================
    # Read State Transitions
    # =========================================================================

    def _cycles_to_seconds(self, cycles: int) -> float:
        """Convert timing cycles to seconds

        OPTIMIZED: Uses pre-computed clock period for O(1) conversion.
        HBM3: tCK = 781.25 ps = 0.78125 ns = 0.78125e-9 s
        """
        return cycles * self._clock_period_s

    def can_read(self) -> bool:
        """Check if READ can be initiated

        Timing constraints:
        - Bank must be ACTIVE (or ACTIVATING in HBM4 mode with tRCD elapsed)
        - Must be >= tRCD since ACT
        """
        # HBM4: Also allow READ when in ACTIVATING state if tRCD elapsed
        if self._is_hbm4 and self.bank.state == BankStateEnum.ACTIVATING:
            if hasattr(self, '_activation_complete_time'):
                if self.current_time < self._activation_complete_time:
                    return False
            return True

        if self.bank.state != BankStateEnum.ACTIVE:
            return False

        time_since_act = self.current_time - self.bank.activate_time
        tRCD = self._get_cached_timing('nRCD')
        tRCD_seconds = self._cycles_to_seconds(tRCD)
        return time_since_act >= tRCD_seconds

    def read(self, burst_length: int = 4) -> Tuple[bool, Optional[str]]:
        """Initiate READ

        Args:
            burst_length: Burst length (default 4 for HBM)

        Returns:
            (success flag, error message)
        """
        if not self.can_read():
            return False, f"Cannot read: state={self.bank.state.name}, " \
                         f"time since act={self.current_time - self.bank.activate_time}"

        self.bank.update_state(BankStateEnum.BUSY)
        self.bank.read_start_time = self.current_time

        # Use cached timing values
        tRCD = self._get_cached_timing('nRCD')
        tCL = self._get_cached_timing('nCL')
        tCCD = self._get_cached_timing('nCCD')
        self.bank.read_complete_time = self.current_time + tRCD + tCL + (burst_length - 1) * tCCD

        # Track column command for bank group scheduling
        self._last_col_cmd_cycle = int(self.current_time)
        self._last_col_cmd_is_write = False

        return True, None

    def can_complete_read(self) -> bool:
        """Check if read can complete"""
        if self.bank.read_start_time < 0:
            return False
        return self.current_time >= self.bank.read_complete_time

    def complete_read(self) -> Tuple[bool, Optional[str]]:
        """READ complete, return to ACTIVE

        Returns:
            (success flag, error message)
        """
        if self.bank.state != BankStateEnum.BUSY:
            return False, "Not in BUSY state"

        if self.bank.read_start_time < 0:
            return False, "No read in progress"

        self.bank.update_state(BankStateEnum.ACTIVE)
        self.bank.last_operation_time = self.current_time
        self.bank.read_start_time = -1.0
        self.bank.read_complete_time = -1.0
        return True, None

    # =========================================================================
    # Write State Transitions
    # =========================================================================

    def can_write(self) -> bool:
        """Check if WRITE can be initiated

        Timing constraints:
        - Bank must be ACTIVE (or ACTIVATING in HBM4 mode with tRCD elapsed)
        - Must be >= tRCD since ACT
        """
        # HBM4: Also allow WRITE when in ACTIVATING state if tRCD elapsed
        if self._is_hbm4 and self.bank.state == BankStateEnum.ACTIVATING:
            if hasattr(self, '_activation_complete_time'):
                if self.current_time < self._activation_complete_time:
                    return False
            return True

        if self.bank.state != BankStateEnum.ACTIVE:
            return False

        time_since_act = self.current_time - self.bank.activate_time
        tRCD = self._get_cached_timing('nRCD')
        tRCD_seconds = self._cycles_to_seconds(tRCD)
        return time_since_act >= tRCD_seconds

    def write(self, burst_length: int = 4) -> Tuple[bool, Optional[str]]:
        """Initiate WRITE

        Args:
            burst_length: Burst length (default 4 for HBM)

        Returns:
            (success flag, error message)
        """
        if not self.can_write():
            return False, f"Cannot write: state={self.bank.state.name}, " \
                         f"time since act={self.current_time - self.bank.activate_time}"

        self.bank.update_state(BankStateEnum.BUSY)
        self.bank.write_start_time = self.current_time

        # Use cached timing values
        tRCD = self._get_cached_timing('nRCD')
        tCWL = self._get_cached_timing('nCWL')
        tCCD = self._get_cached_timing('nCCD')
        self.bank.write_complete_time = self.current_time + tRCD + tCWL + (burst_length - 1) * tCCD

        # Track column command for bank group scheduling
        self._last_col_cmd_cycle = int(self.current_time)
        self._last_col_cmd_is_write = True

        return True, None

    def can_complete_write(self) -> bool:
        """Check if write can complete"""
        if self.bank.write_start_time < 0:
            return False
        return self.current_time >= self.bank.write_complete_time

    def complete_write(self) -> Tuple[bool, Optional[str]]:
        """WRITE complete, return to ACTIVE

        Returns:
            (success flag, error message)
        """
        if self.bank.state != BankStateEnum.BUSY:
            return False, "Not in BUSY state"

        if self.bank.write_start_time < 0:
            return False, "No write in progress"

        self.bank.update_state(BankStateEnum.ACTIVE)
        self.bank.last_operation_time = self.current_time
        self.bank.write_start_time = -1.0
        self.bank.write_complete_time = -1.0
        return True, None

    # =========================================================================
    # Operation Completion Helpers
    # =========================================================================

    def _is_operation_complete(self) -> bool:
        """Check if current BUSY operation is complete"""
        if self.bank.read_start_time >= 0:
            return self.current_time >= self.bank.read_complete_time
        if self.bank.write_start_time >= 0:
            return self.current_time >= self.bank.write_complete_time
        return True  # No operation in progress

    def is_operation_in_progress(self) -> bool:
        """Check if operation is in progress (READ/WRITE/REFRESH)"""
        state_mask = self.bank._cached_state
        return (state_mask & (_STATE_BUSY | _STATE_REFRESHING)) != 0

    # =========================================================================
    # Turnaround Timing
    # =========================================================================

    def can_read_after_write(self) -> bool:
        """Check if READ can be initiated after WRITE (tWTRS/tWTRL)

        Returns:
            True if read can be initiated
        """
        if self.bank.write_start_time < 0:
            return True  # No write operation

        if not self.can_complete_write():
            return False

        # HBM4: Use bank group-aware timing
        if self._is_hbm4:
            tWTRS = self.get_timing_value('nWTRS')
            tWTRL = self.get_timing_value('nWTRL')
            # For simplicity, use tWTRS (same BG). In a full implementation,
            # this would check if the target is in the same bank group.
            tWTR = tWTRS
        else:
            tWTR = self.get_timing_value('nWTRS')

        time_since_write = self.current_time - self.bank.write_complete_time
        return time_since_write >= tWTR

    def can_write_after_read(self) -> bool:
        """Check if WRITE can be initiated after READ (tRTW)

        Returns:
            True if write can be initiated
        """
        if self.bank.read_start_time < 0:
            return True  # No read operation

        if not self.can_complete_read():
            return False

        # tRTW: Read to Write
        tRTW = self.get_timing_value('nRTW')
        time_since_read = self.current_time - self.bank.read_complete_time
        return time_since_read >= tRTW

    # =========================================================================
    # Bank Group-Aware Scheduling (HBM4)
    # =========================================================================

    def can_activate_after_bank_group(self, last_bg_id: int) -> bool:
        """Check if activation can proceed after another bank group (HBM4)

        Args:
            last_bg_id: Last activated bank group ID

        Returns:
            True if timing allows activation
        """
        if last_bg_id < 0:
            return True

        if self._last_act_cycle < 0:
            return True

        elapsed = self.current_time - self._last_act_cycle

        if self._bank_group_id == last_bg_id:
            # Same bank group: tRRDS
            tRRD = self.get_timing_value('nRRDS')
        else:
            # Different bank group: tRRDL
            tRRD = self.get_timing_value('nRRDL')

        return elapsed >= tRRD

    def get_info(self) -> dict:
        """Get bank state machine information

        Returns:
            Dictionary with state information
        """
        return {
            'bank_id': self.bank.bank_id,
            'channel_id': self._channel_id,
            'pseudo_channel_id': self._pseudo_channel_id,
            'bank_group_id': self._bank_group_id,
            'state': self.bank.state.name,
            'open_row': self.bank.open_row,
            'current_time': self.current_time,
            'is_hbm4': self._is_hbm4,
        }

    # =========================================================================
    # Refresh State Transitions
    # =========================================================================

    def can_refresh(self) -> bool:
        """Check if refresh can be initiated

        Timing constraints:
        - Bank must be IDLE
        - Must be >= tRFC since last refresh
        """
        if self.bank.state != BankStateEnum.IDLE:
            return False

        # If never refreshed, can refresh
        if self.bank.refresh_time < 0:
            return True

        time_since_refresh = self.current_time - self.bank.refresh_time
        tRFC = self._get_cached_timing('nRFC')
        tRFC_seconds = self._cycles_to_seconds(tRFC)
        return time_since_refresh >= tRFC_seconds

    def refresh(self) -> Tuple[bool, Optional[str]]:
        """Execute refresh

        Returns:
            (success flag, error message)
        """
        if self.bank.state != BankStateEnum.IDLE:
            return False, f"Bank not idle (state={self.bank.state.name})"

        self.bank.update_state(BankStateEnum.REFRESHING)
        self.bank.refresh_time = self.current_time

        # Use cached timing value
        tRFC = self._get_cached_timing('nRFC')
        self.bank.refresh_complete_time = self.current_time + tRFC

        return True, None

    def can_complete_refresh(self) -> bool:
        """Check if refresh can complete"""
        if self.bank.state != BankStateEnum.REFRESHING:
            return False
        if self.bank.refresh_complete_time < 0:
            return False
        return self.current_time >= self.bank.refresh_complete_time

    def complete_refresh(self) -> Tuple[bool, Optional[str]]:
        """Refresh complete

        Returns:
            (success flag, error message)
        """
        if self.bank.state != BankStateEnum.REFRESHING:
            return False, "Not refreshing"

        if self.bank.refresh_complete_time >= 0:
            if self.current_time < self.bank.refresh_complete_time:
                return False, f"Refresh not complete: need {self.bank.refresh_complete_time}, current {self.current_time}"

        self.bank.update_state(BankStateEnum.IDLE)
        self.bank.refresh_time = self.current_time
        self.bank.refresh_complete_time = -1.0
        self.bank.last_operation_time = self.current_time
        return True, None

    # =========================================================================
    # Power Management State Transitions
    # =========================================================================

    def can_enter_power_down(self) -> bool:
        """Check if power down mode can be entered

        Constraints:
        - Bank must be IDLE
        """
        return self.bank.state == BankStateEnum.IDLE

    def enter_power_down(self) -> Tuple[bool, Optional[str]]:
        """Enter power down mode

        Returns:
            (success flag, error message)
        """
        if not self.can_enter_power_down():
            return False, f"Cannot enter power down: state={self.bank.state.name}"

        self.bank.update_state(BankStateEnum.POWERDN)
        return True, None

    def exit_power_down(self) -> Tuple[bool, Optional[str]]:
        """Exit power down mode

        Returns:
            (success flag, error message)
        """
        if self.bank.state != BankStateEnum.POWERDN:
            return False, f"Not in power down: state={self.bank.state.name}"

        self.bank.update_state(BankStateEnum.IDLE)
        return True, None

    def can_enter_self_refresh(self) -> bool:
        """Check if self refresh mode can be entered

        Constraints:
        - Bank must be IDLE
        """
        return self.bank.state == BankStateEnum.IDLE

    def enter_self_refresh(self) -> Tuple[bool, Optional[str]]:
        """Enter self refresh mode

        Returns:
            (success flag, error message)
        """
        if not self.can_enter_self_refresh():
            return False, f"Cannot enter self refresh: state={self.bank.state.name}"

        self.bank.update_state(BankStateEnum.SELFREF)
        return True, None

    def exit_self_refresh(self) -> Tuple[bool, Optional[str]]:
        """Exit self refresh mode

        Returns:
            (success flag, error message)
        """
        if self.bank.state != BankStateEnum.SELFREF:
            return False, f"Not in self refresh: state={self.bank.state.name}"

        self.bank.update_state(BankStateEnum.IDLE)
        return True, None

    # =========================================================================
    # Row Access Helpers
    # =========================================================================

    def is_row_hit(self, row: int) -> bool:
        """Check if row hit"""
        return (self.bank.state == BankStateEnum.ACTIVE and
                self.bank.open_row == row)

    def is_row_open(self, row: int) -> bool:
        """Check if specified row is open"""
        return self.bank.open_row == row

    def close_row(self) -> Tuple[bool, Optional[str]]:
        """Close currently open row"""
        if self.bank.state != BankStateEnum.ACTIVE:
            return False, "Bank not active"
        return self.precharge()

    # =========================================================================
    # Timing Query
    # =========================================================================

    def time_to_ready(self) -> float:
        """Calculate time until next ACT can be initiated

        Returns:
            Required wait time (cycles), 0 if already ready
        """
        if self.bank.state != BankStateEnum.IDLE:
            return float('inf')  # Wrong state, need to precharge first

        if not self.bank.has_been_activated:
            return 0.0

        time_since_last = self.current_time - self.bank.last_operation_time
        tRC = self._get_cached_timing('nRC')
        if time_since_last >= tRC:
            return 0.0

        return tRC - time_since_last

    def time_to_read_ready(self) -> float:
        """Calculate time until READ can be initiated

        Returns:
            Required wait time (cycles)
        """
        if self.bank.state == BankStateEnum.ACTIVE:
            time_since_act = self.current_time - self.bank.activate_time
            tRCD = self._get_cached_timing('nRCD')
            if time_since_act >= tRCD:
                return 0.0
            return tRCD - time_since_act

        return float('inf')  # Need to activate first

    def time_to_precharge_ready(self) -> float:
        """Calculate time until PRE can be initiated

        Returns:
            Required wait time (cycles)
        """
        state_mask = self.bank._cached_state
        if state_mask & (_STATE_ACTIVE | _STATE_BUSY) == 0:
            return float('inf')

        time_since_act = self.current_time - self.bank.activate_time
        tRAS = self._get_cached_timing('nRAS')
        if time_since_act >= tRAS:
            return 0.0

        return tRAS - time_since_act

    def get_violations(self) -> List[TimingViolation]:
        """Get recorded timing violations"""
        return self.timing_violations.copy()

    def clear_violations(self):
        """Clear recorded timing violations"""
        self.timing_violations.clear()

    # =========================================================================
    # State Queries (for compatibility with existing code)
    # =========================================================================

    def complete_read_legacy(self):
        """READ complete, return ACTIVE (legacy)"""
        self.complete_read()

    def complete_write_legacy(self):
        """WRITE complete (legacy)"""
        self.complete_write()

    # =========================================================================
    # HBM4 Compatibility Methods
    # =========================================================================

    def get_state(self) -> BankStateEnum:
        """Get current bank state (HBM4 compatibility)"""
        return self.bank.state

    def get_open_row(self) -> int:
        """Get currently open row (HBM4 compatibility)"""
        return self.bank.open_row

    def is_row_hit(self, row: int) -> bool:
        """Check if the specified row is open (HBM4 compatibility)"""
        return self.bank.state == BankStateEnum.ACTIVE and self.bank.open_row == row

    def reset(self):
        """Reset bank state (HBM4 compatibility)"""
        self.bank.update_state(BankStateEnum.IDLE)
        self.bank.open_row = -1
        self.current_time = 0
        self.timing_violations.clear()
        self._last_act_cycle = -1
        self._last_col_cmd_cycle = -1

    def get_info(self) -> dict:
        """Get bank state information (HBM4 compatibility)"""
        return {
            'bank_id': self.bank_id,
            'channel_id': self.channel_id,
            'pseudo_channel_id': self.pseudo_channel_id,
            'bank_group_id': self.bank_group_id,
            'state': self.bank.state.name,
            'open_row': self.bank.open_row,
            'current_time': self.current_time,
            'is_hbm4': self._is_hbm4,
        }

    def __repr__(self) -> str:
        return (f"BankStateMachine(bank={self.bank_id}, ch={self.channel_id}, "
                f"pch={self.pseudo_channel_id}, bg={self.bank_group_id}, "
                f"state={self.bank.state.name}, row={self.bank.open_row})")


# Aliases for backward compatibility
def create_bank_state_machine(bank_id: int, timing, channel_id: int = 0,
                              pseudo_channel_id: int = 0, bank_group_id: int = 0) -> BankStateMachine:
    """Factory function to create BankStateMachine

    Args:
        bank_id: Bank ID
        timing: Timing parameter object (HBM3Timing or HBM4Timing)
        channel_id: Channel index (0-31, for HBM4)
        pseudo_channel_id: Pseudo-channel index (0-1, for HBM4)
        bank_group_id: Bank group index (0-7, for HBM4)

    Returns:
        BankStateMachine instance
    """
    return BankStateMachine(
        bank_id=bank_id,
        timing=timing,
        channel_id=channel_id,
        pseudo_channel_id=pseudo_channel_id,
        bank_group_id=bank_group_id
    )


class BankArray:
    """Array of banks for a single pseudo-channel

    Manages banks organized into bank groups.
    """

    def __init__(self, num_banks: int = 16, timing=None,
                 channel_id: int = 0, pseudo_channel_id: int = 0):
        """Initialize bank array

        Args:
            num_banks: Number of banks (default 16 for HBM4)
            timing: Timing parameter object
            channel_id: Channel index
            pseudo_channel_id: Pseudo-channel index
        """
        self.pseudo_channel_id = pseudo_channel_id
        self.channel_id = channel_id
        self.timing = timing
        self.num_banks = num_banks

        # Create banks with bank group assignment
        self.banks: List[BankStateMachine] = []
        for bank_id in range(num_banks):
            bg_id = bank_id // 2  # 2 banks per group
            bank = BankStateMachine(
                bank_id=bank_id,
                timing=timing,
                channel_id=channel_id,
                pseudo_channel_id=pseudo_channel_id,
                bank_group_id=bg_id
            )
            self.banks.append(bank)

    def set_time(self, cycle: float):
        """Set time for all banks"""
        for bank in self.banks:
            bank.set_time(cycle)

    def tick(self, advance_cycle: bool = True):
        """Advance time and process state completions

        Args:
            advance_cycle: If True, increment current_cycle for each bank.
        """
        for bank in self.banks:
            if advance_cycle:
                bank.current_time += 1

            # Auto-complete HBM4 state transitions
            if bank._is_hbm4:
                if bank.bank.state == BankStateEnum.ACTIVATING:
                    bank.complete_activation()
                elif bank.bank.state == BankStateEnum.PRECHARGING:
                    bank.complete_precharge()

    def get_bank(self, bank_id: int) -> Optional[BankStateMachine]:
        """Get bank by ID"""
        if 0 <= bank_id < len(self.banks):
            return self.banks[bank_id]
        return None

    def get_banks_in_group(self, bg_id: int) -> List[BankStateMachine]:
        """Get all banks in a bank group"""
        return [self.banks[bg_id * 2 + i] for i in range(2) if bg_id * 2 + i < len(self.banks)]

    def get_active_bank_count(self) -> int:
        """Get count of active (open) banks"""
        return sum(1 for b in self.banks if b.bank.is_active)

    def get_idle_bank_count(self) -> int:
        """Get count of idle (closed) banks"""
        return sum(1 for b in self.banks if b.bank.is_idle)

    def reset(self):
        """Reset all banks"""
        for bank in self.banks:
            bank.set_time(0)
            bank.bank.update_state(BankStateEnum.IDLE)
            bank.bank.open_row = -1


def create_bank_array(num_banks: int = 16, timing=None,
                      channel_id: int = 0, pseudo_channel_id: int = 0) -> BankArray:
    """Factory function to create BankArray

    Args:
        num_banks: Number of banks (default 16 for HBM4)
        timing: Timing parameter object
        channel_id: Channel index
        pseudo_channel_id: Pseudo-channel index

    Returns:
        BankArray with configured banks
    """
    return BankArray(
        num_banks=num_banks,
        timing=timing,
        channel_id=channel_id,
        pseudo_channel_id=pseudo_channel_id
    )


# Vectorized operations for batch processing (using lists, no numpy dependency)
def batch_check_can_activate(bank_machines: List[BankStateMachine]) -> List[bool]:
    """Batch check if banks can activate

    Args:
        bank_machines: List of BankStateMachine instances

    Returns:
        List of boolean results
    """
    return [bm.can_activate() for bm in bank_machines]


def batch_check_can_read(bank_machines: List[BankStateMachine]) -> List[bool]:
    """Batch check if banks can read

    Args:
        bank_machines: List of BankStateMachine instances

    Returns:
        List of boolean results
    """
    return [bm.can_read() for bm in bank_machines]


def batch_check_can_write(bank_machines: List[BankStateMachine]) -> List[bool]:
    """Batch check if banks can write

    Args:
        bank_machines: List of BankStateMachine instances

    Returns:
        List of boolean results
    """
    return [bm.can_write() for bm in bank_machines]