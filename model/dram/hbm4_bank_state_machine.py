"""
HBM4 DRAM Bank State Machine - Enhanced Version with Full State Tracking

This module implements comprehensive bank state machine for HBM4 memory systems,
supporting all JEDEC HBM4 timing requirements and state transitions.

Key features:
- Bank state tracking: CLOSED, OPEN, ACTIVATING, PRECHARGING, READ, WRITE
- Full timing parameter compliance: tRCD, tRP, tRAS, tRC
- Per-bank state machines (1024 total banks for HBM4: 32ch × 2pch × 16bank)
- Integration with HBM4 refresh scheduler
- State transition timing validation
- Bank group-aware scheduling

HBM4 Key Timing Parameters (from HBM4TimingSource):
- tRCD: 8 cycles (Activate to Read/Write)
- tRP: 8 cycles (Precharge)
- tRAS: 20 cycles (Activate to Precharge)
- tRC: 22 cycles (Activate to Activate same bank)

Reference:
- JEDEC JESD270-4A HBM4 specification
- Ramulator 2.0 HBM3 implementation
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Set
import logging

# Import unified timing source
from model.dram.timing import HBM4TimingSource, HBM4_TIMING as UNIFIED_TIMING

# Configure logging
logger = logging.getLogger(__name__)


class HBM4BankState(IntEnum):
    """HBM4 Bank State with CLOSED/OPEN/ACTIVATING/PRECHARGING tracking

    This state machine follows JEDEC HBM4 specification with explicit
    tracking of intermediate states for accurate timing validation.

    State transitions:
    - CLOSED -> ACTIVATING (on ACT command)
    - ACTIVATING -> OPEN (after tRCD cycles)
    - OPEN -> PRECHARGING (on PRE command, after tRAS minimum)
    - PRECHARGING -> CLOSED (after tRP cycles)
    - OPEN -> READ (on RD command, after tRCD)
    - OPEN -> WRITE (on WR command, after tRCD)
    - READ/WRITE -> OPEN (after data transfer completes)
    """
    CLOSED = 0        # Bank is precharged and idle
    ACTIVATING = 1   # Activation in progress (tRCD period)
    OPEN = 2         # Row is open and accessible
    PRECHARGING = 3  # Precharge in progress (tRP period)
    READ = 4         # Read operation in progress
    WRITE = 5        # Write operation in progress
    REFRESH = 6      # Refresh in progress
    POWER_DOWN = 7   # Power down mode
    SELF_REFRESH = 8 # Self refresh mode

    # Backward compatibility aliases
    IDLE = 0
    ACTIVE = 2


class HBM4Command(IntEnum):
    """HBM4 Command encoding"""
    NOP = 0
    ACT = 1      # Activate
    READ = 2     # Read
    WRITE = 3    # Write
    PRE = 4      # Precharge single bank
    PREA = 5     # Precharge all
    REF = 6      # Refresh
    RFM = 7      # Row flash memory


# Use unified timing source - single source of truth
# Reference: JEDEC JESD270-4A HBM4 specification with JEDEC baseline timing
BANK_TIMING = {
    # Row command timing (cycles @ 8 GT/s, tCK = 125 ps)
    # Values from HBM4TimingSource (HBM4 spec baseline)
    'tRCD': UNIFIED_TIMING.nRCD,    # RAS to CAS delay (8 cycles = 1 ns)
    'tRP': UNIFIED_TIMING.nRP,     # Precharge time (8 cycles = 1 ns)
    'tRAS': UNIFIED_TIMING.nRAS,    # Row active time minimum (20 cycles = 2.5 ns)
    'tRC': UNIFIED_TIMING.nRC,      # Row cycle time (same bank) (22 cycles = 2.75 ns)

    # Column command timing
    'tCL': UNIFIED_TIMING.nCL,      # CAS latency (8 cycles = 1 ns)
    'tCWL': UNIFIED_TIMING.nCWL,    # CAS write latency (3 cycles = 375 ps)

    # Bank group timing
    'tCCD': UNIFIED_TIMING.nCCD,    # CAS-to-CAS delay (4 cycles = 500 ps)
    'tCCDS': UNIFIED_TIMING.nCCDS,  # CAS-to-CAS delay (same BG) (2 cycles = 250 ps)
    'tCCDL': UNIFIED_TIMING.nCCDL,  # CAS-to-CAS delay (different BG) (3 cycles = 375 ps)

    # Row timing
    'tRRD': UNIFIED_TIMING.nRRD,    # Row-to-row delay (4 cycles = 500 ps)
    'tRRDS': UNIFIED_TIMING.nRRDS,  # Row-to-row delay (same BG) (3 cycles = 375 ps)
    'tRRDL': UNIFIED_TIMING.nRRDL,  # Row-to-row delay (different BG) (4 cycles = 500 ps)
    'tFAW': UNIFIED_TIMING.nFAW,    # Four-activate window (16 cycles = 2 ns)

    # Turnaround timing
    'tWTRS': UNIFIED_TIMING.nWTRS,  # Write to read (same BG) (4 cycles = 500 ps)
    'tWTRL': UNIFIED_TIMING.nWTRL,  # Write to read (different BG) (5 cycles = 625 ps)
    'tRTW': UNIFIED_TIMING.nRTW,    # Read to write (4 cycles = 500 ps)

    # Refresh timing
    'tRFC': UNIFIED_TIMING.nRFC,    # Refresh cycle time (180 cycles = 22.5 ns)
    'tREFI': UNIFIED_TIMING.nREFI,  # Refresh interval (3900 cycles = 487.5 us)
}


@dataclass
class HBM4BankTiming:
    """HBM4 timing parameters for a single bank - uses unified timing source

    All timing values are in clock cycles @ 8 GT/s (tCK = 125 ps)
    Values are sourced from HBM4TimingSource for consistency.
    """
    # Clock period - from unified source
    tCK_ps: float = 125.0  # Default 125 ps

    # Row command timing - from unified source
    tRCD: int = UNIFIED_TIMING.nRCD   # RAS to CAS delay
    tRP: int = UNIFIED_TIMING.nRP     # Precharge time
    tRAS: int = UNIFIED_TIMING.nRAS   # Row active time minimum
    tRC: int = UNIFIED_TIMING.nRC     # Row cycle time (same bank)

    # Column command timing - from unified source
    tCL: int = UNIFIED_TIMING.nCL     # CAS latency
    tCWL: int = UNIFIED_TIMING.nCWL   # CAS write latency

    # Bank group timing - from unified source
    tRRDS: int = UNIFIED_TIMING.nRRDS # RAS to RAS delay (same BG)
    tRRDL: int = UNIFIED_TIMING.nRRDL # RAS to RAS delay (different BG)
    tFAW: int = UNIFIED_TIMING.nFAW   # Four-activate window

    # Turnaround timing - from unified source
    tWTRS: int = UNIFIED_TIMING.nWTRS # Write to read (same BG)
    tWTRL: int = UNIFIED_TIMING.nWTRL # Write to read (different BG)
    tRTW: int = UNIFIED_TIMING.nRTW   # Read to write

    # CAS-to-CAS delay - from unified source
    tCCD: int = UNIFIED_TIMING.nCCD   # CAS-to-CAS delay (column command spacing)

    # Refresh timing - from unified source
    tRFC: int = UNIFIED_TIMING.nRFC   # Refresh cycle time

    # Burst length
    tBL: int = UNIFIED_TIMING.nBL     # Burst length (FLINE = 4 beats)

    @property
    def clock_period_ns(self) -> float:
        """Clock period in nanoseconds"""
        return self.tCK_ps / 1000.0

    def cycles_to_ns(self, cycles: int) -> float:
        """Convert cycles to nanoseconds"""
        return cycles * self.clock_period_ns

    def cycles_to_seconds(self, cycles: int) -> float:
        """Convert cycles to seconds"""
        return cycles * self.tCK_ps * 1e-12

    @classmethod
    def for_speed_grade(cls, speed_gbps: float) -> 'HBM4BankTiming':
        """Create timing for specific speed grade

        Args:
            speed_gbps: Data rate in GT/s

        Returns:
            HBM4BankTiming configured for the speed grade
        """
        tCK_ps = 1000.0 / speed_gbps
        return cls(tCK_ps=tCK_ps)


@dataclass
class BankStateTransition:
    """Record of a state transition for validation"""
    from_state: HBM4BankState
    to_state: HBM4BankState
    cycle: int
    command: Optional[HBM4Command] = None
    row: int = -1


@dataclass
class HBM4Bank:
    """HBM4 Bank state with full state tracking

    Tracks all bank state and timing information.
    """
    bank_id: int
    channel_id: int = 0
    pseudo_channel_id: int = 0

    # State tracking
    state: HBM4BankState = HBM4BankState.CLOSED
    open_row: int = -1

    # Timing tracking (in cycles)
    activate_start_cycle: int = -1
    activate_complete_cycle: int = -1
    precharge_start_cycle: int = -1
    precharge_complete_cycle: int = -1
    read_start_cycle: int = -1
    read_complete_cycle: int = -1
    write_start_cycle: int = -1
    write_complete_cycle: int = -1
    refresh_start_cycle: int = -1
    refresh_complete_cycle: int = -1

    # Last operation tracking
    last_operation_cycle: int = -1

    # State history for validation
    transition_history: List[BankStateTransition] = field(default_factory=list)

    # Bank group info
    bank_group_id: int = 0

    @property
    def is_closed(self) -> bool:
        """Check if bank is in CLOSED state"""
        return self.state == HBM4BankState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if bank is in OPEN state"""
        return self.state == HBM4BankState.OPEN

    @property
    def is_activating(self) -> bool:
        """Check if bank is in ACTIVATING state"""
        return self.state == HBM4BankState.ACTIVATING

    @property
    def is_precharging(self) -> bool:
        """Check if bank is in PRECHARGING state"""
        return self.state == HBM4BankState.PRECHARGING

    @property
    def is_reading(self) -> bool:
        """Check if bank is in READ state"""
        return self.state == HBM4BankState.READ

    @property
    def is_writing(self) -> bool:
        """Check if bank is in WRITE state"""
        return self.state == HBM4BankState.WRITE

    @property
    def is_refreshing(self) -> bool:
        """Check if bank is in REFRESH state"""
        return self.state == HBM4BankState.REFRESH

    @property
    def row_open(self) -> bool:
        """Check if a row is open"""
        return self.is_open and self.open_row >= 0

    def record_transition(self, to_state: HBM4BankState,
                         cycle: int, command: Optional[HBM4Command] = None):
        """Record a state transition"""
        transition = BankStateTransition(
            from_state=self.state,
            to_state=to_state,
            cycle=cycle,
            command=command,
            row=self.open_row
        )
        self.transition_history.append(transition)
        self.state = to_state

    def get_transitions(self) -> List[BankStateTransition]:
        """Get state transition history"""
        return self.transition_history.copy()


class TimingViolationError(Exception):
    """Exception raised when timing constraints are violated"""
    def __init__(self, violation_type: str, required_cycles: int,
                 actual_cycles: int, description: str):
        self.violation_type = violation_type
        self.required_cycles = required_cycles
        self.actual_cycles = actual_cycles
        self.description = description
        super().__init__(description)


@dataclass
class TimingViolation:
    """Record of a timing violation"""
    violation_type: str
    required_cycles: int
    actual_cycles: int
    bank_id: int
    cycle: int
    description: str


class HBM4BankStateMachine:
    """HBM4 Bank State Machine with full state tracking

    Implements the complete HBM4 bank state machine with:
    - CLOSED/OPEN/ACTIVATING/PRECHARGING state tracking
    - Timing parameter compliance (tRCD, tRP, tRAS, tRC)
    - Bank group-aware scheduling
    - Integration with refresh scheduler
    - Timing violation detection and reporting

    Architecture:
    - 32 channels × 2 pseudo-channels × 16 banks = 1024 total banks
    - 8 bank groups per pseudo-channel (2 banks per group)

    Reference: JEDEC JESD270-4A HBM4 specification
    """

    def __init__(self, bank_id: int, timing: Optional[HBM4BankTiming] = None,
                 channel_id: int = 0, pseudo_channel_id: int = 0,
                 bank_group_id: int = 0):
        """Initialize HBM4 Bank State Machine

        Args:
            bank_id: Bank index within pseudo-channel (0-15)
            timing: Timing parameters (uses HBM4 defaults if None)
            channel_id: Channel index (0-31)
            pseudo_channel_id: Pseudo-channel index (0-1)
            bank_group_id: Bank group index (0-7)
        """
        self.bank_id = bank_id
        self.channel_id = channel_id
        self.pseudo_channel_id = pseudo_channel_id
        self.bank_group_id = bank_group_id

        # Use provided timing or HBM4 defaults
        self.timing = timing if timing is not None else HBM4BankTiming()

        # Bank state
        self.bank = HBM4Bank(
            bank_id=bank_id,
            channel_id=channel_id,
            pseudo_channel_id=pseudo_channel_id,
            bank_group_id=bank_group_id
        )

        # Current simulation time
        self.current_cycle = 0

        # Violation tracking
        self.violations: List[TimingViolation] = []

        # Command tracking for bank group scheduling
        self.last_act_cycle: int = -1
        self.last_col_cmd_cycle: int = -1
        self.last_col_cmd_bg: int = -1
        self.last_col_cmd_is_write: bool = False

    def set_time(self, cycle: int):
        """Set current simulation cycle

        Args:
            cycle: Current simulation cycle
        """
        self.current_cycle = cycle
        # Auto-complete activation when tRCD has elapsed
        if self.bank.state == HBM4BankState.ACTIVATING:
            self.complete_activation()

    def _record_violation(self, violation_type: str, required_cycles: int,
                          actual_cycles: int, description: str):
        """Record a timing violation"""
        violation = TimingViolation(
            violation_type=violation_type,
            required_cycles=required_cycles,
            actual_cycles=actual_cycles,
            bank_id=self.bank_id,
            cycle=self.current_cycle,
            description=description
        )
        self.violations.append(violation)
        logger.warning(f"Timing violation at bank {self.bank_id}, cycle {self.current_cycle}: "
                       f"{description}")

    def _cycles_since(self, start_cycle: int) -> int:
        """Calculate cycles elapsed since start_cycle"""
        if start_cycle < 0:
            return -1
        return self.current_cycle - start_cycle

    # =========================================================================
    # State Query Methods
    # =========================================================================

    def can_activate(self) -> bool:
        """Check if ACT command can be issued

        Timing constraints:
        - Bank must be CLOSED
        - Must be >= tRC since last operation (for same bank)
        """
        if self.bank.state != HBM4BankState.CLOSED:
            return False

        # Check tRC for same bank
        if self.last_act_cycle >= 0:
            elapsed = self._cycles_since(self.last_act_cycle)
            if elapsed < self.timing.tRC:
                return False

        return True

    def can_read(self) -> bool:
        """Check if READ command can be issued

        Timing constraints:
        - Bank must be OPEN
        - Must be >= tRCD since activation started
        """
        if not self.bank.is_open:
            return False

        # tRCD must have elapsed since activation started
        if self.bank.activate_start_cycle >= 0:
            elapsed = self._cycles_since(self.bank.activate_start_cycle)
            if elapsed < self.timing.tRCD:
                return False

        return True

    def can_write(self) -> bool:
        """Check if WRITE command can be issued

        Timing constraints:
        - Bank must be OPEN
        - Must be >= tRCD since activation started
        """
        if not self.bank.is_open:
            return False

        if self.bank.activate_start_cycle >= 0:
            elapsed = self._cycles_since(self.bank.activate_start_cycle)
            if elapsed < self.timing.tRCD:
                return False

        return True

    def can_precharge(self) -> bool:
        """Check if PRE command can be issued

        Timing constraints:
        - Bank must be OPEN or READ or WRITE
        - Must be >= tRAS since activation started
        """
        if self.bank.state not in (HBM4BankState.OPEN,
                                   HBM4BankState.READ,
                                   HBM4BankState.WRITE):
            return False

        # tRAS minimum must have elapsed
        if self.bank.activate_start_cycle >= 0:
            elapsed = self._cycles_since(self.bank.activate_start_cycle)
            if elapsed < self.timing.tRAS:
                return False

        return True

    def can_refresh(self) -> bool:
        """Check if REF command can be issued

        Constraints:
        - Bank must be CLOSED
        """
        return self.bank.is_closed

    # =========================================================================
    # State Transition Methods
    # =========================================================================

    def activate(self, row: int) -> Tuple[bool, Optional[str]]:
        """Issue ACTIVATE command

        Transitions: CLOSED -> ACTIVATING

        Args:
            row: Row to activate

        Returns:
            (success, error_message)
        """
        if not self.can_activate():
            if self.bank.state != HBM4BankState.CLOSED:
                return False, f"Bank {self.bank_id} not closed (state={self.bank.state.name})"
            if self.last_act_cycle >= 0:
                elapsed = self._cycles_since(self.last_act_cycle)
                return False, f"tRC violation: need {self.timing.tRC} cycles, have {elapsed}"
            return False, f"Cannot activate bank {self.bank_id}"

        # Record transition
        self.bank.record_transition(HBM4BankState.ACTIVATING, self.current_cycle,
                                   HBM4Command.ACT)
        self.bank.activate_start_cycle = self.current_cycle
        self.bank.activate_complete_cycle = self.current_cycle + self.timing.tRCD
        self.bank.open_row = row
        self.last_act_cycle = self.current_cycle

        logger.debug(f"Bank {self.bank_id}: ACT row={row} at cycle {self.current_cycle}")
        return True, None

    def complete_activation(self) -> bool:
        """Complete activation (called after tRCD cycles)

        Transitions: ACTIVATING -> OPEN

        Returns:
            True if activation was completed (or already completed)
        """
        # Already open means activation completed
        if self.bank.state == HBM4BankState.OPEN:
            return True

        if self.bank.state != HBM4BankState.ACTIVATING:
            return False

        if self.bank.activate_complete_cycle >= 0:
            if self.current_cycle < self.bank.activate_complete_cycle:
                return False

        self.bank.record_transition(HBM4BankState.OPEN, self.current_cycle)
        logger.debug(f"Bank {self.bank_id}: Activation complete at cycle {self.current_cycle}")
        return True

    def read(self, column: int = 0) -> Tuple[bool, Optional[str]]:
        """Issue READ command

        Transitions: OPEN -> READ -> OPEN

        Args:
            column: Column address

        Returns:
            (success, error_message)
        """
        if not self.can_read():
            return False, f"Cannot read bank {self.bank_id}: not ready (state={self.bank.state.name})"

        self.bank.record_transition(HBM4BankState.READ, self.current_cycle,
                                   HBM4Command.READ)
        self.bank.read_start_cycle = self.current_cycle
        # Read completes after CAS latency + burst
        self.bank.read_complete_cycle = self.current_cycle + self.timing.tCL + self.timing.tBL

        self.last_col_cmd_cycle = self.current_cycle
        self.last_col_cmd_is_write = False

        logger.debug(f"Bank {self.bank_id}: READ at cycle {self.current_cycle}")
        return True, None

    def complete_read(self) -> bool:
        """Complete READ operation

        Returns:
            True if read was completed
        """
        if self.bank.state != HBM4BankState.READ:
            return False

        if self.bank.read_complete_cycle >= 0:
            if self.current_cycle < self.bank.read_complete_cycle:
                return False

        self.bank.record_transition(HBM4BankState.OPEN, self.current_cycle)
        self.bank.read_start_cycle = -1
        self.bank.read_complete_cycle = -1
        return True

    def write(self, column: int = 0) -> Tuple[bool, Optional[str]]:
        """Issue WRITE command

        Transitions: OPEN -> WRITE -> OPEN

        Args:
            column: Column address

        Returns:
            (success, error_message)
        """
        if not self.can_write():
            return False, f"Cannot write bank {self.bank_id}: not ready (state={self.bank.state.name})"

        self.bank.record_transition(HBM4BankState.WRITE, self.current_cycle,
                                   HBM4Command.WRITE)
        self.bank.write_start_cycle = self.current_cycle
        # Write completes after CWL + burst
        self.bank.write_complete_cycle = self.current_cycle + self.timing.tCWL + self.timing.tBL

        self.last_col_cmd_cycle = self.current_cycle
        self.last_col_cmd_is_write = True

        logger.debug(f"Bank {self.bank_id}: WRITE at cycle {self.current_cycle}")
        return True, None

    def complete_write(self) -> bool:
        """Complete WRITE operation

        Returns:
            True if write was completed
        """
        if self.bank.state != HBM4BankState.WRITE:
            return False

        if self.bank.write_complete_cycle >= 0:
            if self.current_cycle < self.bank.write_complete_cycle:
                return False

        self.bank.record_transition(HBM4BankState.OPEN, self.current_cycle)
        self.bank.write_start_cycle = -1
        self.bank.write_complete_cycle = -1
        return True

    def precharge(self) -> Tuple[bool, Optional[str]]:
        """Issue PRECHARGE command

        Transitions: OPEN/READ/WRITE -> PRECHARGING

        Args:
            None

        Returns:
            (success, error_message)
        """
        if not self.can_precharge():
            if self.bank.activate_start_cycle >= 0:
                elapsed = self._cycles_since(self.bank.activate_start_cycle)
                return False, f"tRAS violation: need {self.timing.tRAS}, have {elapsed}"
            return False, f"Cannot precharge bank {self.bank_id} (state={self.bank.state.name})"

        # Complete any pending read/write first
        if self.bank.is_reading:
            self.complete_read()
        elif self.bank.is_writing:
            self.complete_write()

        self.bank.record_transition(HBM4BankState.PRECHARGING, self.current_cycle,
                                   HBM4Command.PRE)
        self.bank.precharge_start_cycle = self.current_cycle
        self.bank.precharge_complete_cycle = self.current_cycle + self.timing.tRP

        logger.debug(f"Bank {self.bank_id}: PRE at cycle {self.current_cycle}")
        return True, None

    def complete_precharge(self) -> bool:
        """Complete precharge operation

        Transitions: PRECHARGING -> CLOSED

        Returns:
            True if precharge was completed
        """
        if self.bank.state != HBM4BankState.PRECHARGING:
            return False

        if self.bank.precharge_complete_cycle >= 0:
            if self.current_cycle < self.bank.precharge_complete_cycle:
                return False

        self.bank.record_transition(HBM4BankState.CLOSED, self.current_cycle)
        self.bank.open_row = -1
        self.bank.precharge_start_cycle = -1
        self.bank.precharge_complete_cycle = -1
        self.bank.last_operation_cycle = self.current_cycle

        logger.debug(f"Bank {self.bank_id}: Precharge complete at cycle {self.current_cycle}")
        return True

    def refresh(self) -> Tuple[bool, Optional[str]]:
        """Issue REFRESH command

        Transitions: CLOSED -> REFRESH -> CLOSED

        Returns:
            (success, error_message)
        """
        if not self.can_refresh():
            return False, f"Cannot refresh bank {self.bank_id}: not closed"

        self.bank.record_transition(HBM4BankState.REFRESH, self.current_cycle,
                                   HBM4Command.REF)
        self.bank.refresh_start_cycle = self.current_cycle
        self.bank.refresh_complete_cycle = self.current_cycle + self.timing.tRFC

        logger.debug(f"Bank {self.bank_id}: REF at cycle {self.current_cycle}")
        return True, None

    def complete_refresh(self) -> bool:
        """Complete refresh operation

        Returns:
            True if refresh was completed
        """
        if self.bank.state != HBM4BankState.REFRESH:
            return False

        if self.bank.refresh_complete_cycle >= 0:
            if self.current_cycle < self.bank.refresh_complete_cycle:
                return False

        self.bank.record_transition(HBM4BankState.CLOSED, self.current_cycle)
        self.bank.refresh_start_cycle = -1
        self.bank.refresh_complete_cycle = -1
        self.bank.last_operation_cycle = self.current_cycle

        logger.debug(f"Bank {self.bank_id}: Refresh complete at cycle {self.current_cycle}")
        return True

    # =========================================================================
    # Bank Group Scheduling
    # =========================================================================

    def can_activate_after_bank_group(self, last_bg_id: int) -> bool:
        """Check if activation can proceed after another bank group

        Args:
            last_bg_id: Last activated bank group ID

        Returns:
            True if timing allows activation
        """
        if last_bg_id < 0:
            return True

        if self.last_act_cycle < 0:
            return True

        elapsed = self._cycles_since(self.last_act_cycle)

        if self.bank_group_id == last_bg_id:
            # Same bank group: tRRDS
            return elapsed >= self.timing.tRRDS
        else:
            # Different bank group: tRRDL
            return elapsed >= self.timing.tRRDL

    def can_read_after_write(self) -> bool:
        """Check if READ can follow WRITE (turnaround)

        Returns:
            True if timing allows READ after WRITE
        """
        if self.last_col_cmd_cycle < 0:
            return True

        if self.last_col_cmd_is_write:
            elapsed = self._cycles_since(self.last_col_cmd_cycle)
            return elapsed >= self.timing.tWTRS

        return True

    def can_write_after_read(self) -> bool:
        """Check if WRITE can follow READ (turnaround)

        Returns:
            True if timing allows WRITE after READ
        """
        if self.last_col_cmd_cycle < 0:
            return True

        if not self.last_col_cmd_is_write:
            elapsed = self._cycles_since(self.last_col_cmd_cycle)
            return elapsed >= self.timing.tRTW

        return True

    # =========================================================================
    # Timing Queries
    # =========================================================================

    def time_to_activate(self) -> int:
        """Calculate cycles until activation is possible

        Returns:
            Cycles until bank can be activated (0 if ready now)
        """
        if self.bank.state != HBM4BankState.CLOSED:
            return -1  # Not closable

        if self.last_act_cycle < 0:
            return 0  # Never activated

        elapsed = self._cycles_since(self.last_act_cycle)
        if elapsed >= self.timing.tRC:
            return 0

        return self.timing.tRC - elapsed

    def time_to_read(self) -> int:
        """Calculate cycles until READ is possible

        Returns:
            Cycles until READ can be issued
        """
        if not self.bank.is_open:
            return -1

        if self.bank.activate_start_cycle >= 0:
            elapsed = self._cycles_since(self.bank.activate_start_cycle)
            if elapsed >= self.timing.tRCD:
                return 0
            return self.timing.tRCD - elapsed

        return -1

    def time_to_precharge(self) -> int:
        """Calculate cycles until precharge is possible

        Returns:
            Cycles until PRE can be issued
        """
        if self.bank.state not in (HBM4BankState.OPEN, HBM4BankState.READ, HBM4BankState.WRITE):
            return -1

        if self.bank.activate_start_cycle >= 0:
            elapsed = self._cycles_since(self.bank.activate_start_cycle)
            if elapsed >= self.timing.tRAS:
                return 0
            return self.timing.tRAS - elapsed

        return -1

    def validate_timing(self) -> List[TimingViolation]:
        """Validate timing constraints and return any violations

        Returns:
            List of timing violations
        """
        violations = []

        # Check tRC
        if self.last_act_cycle >= 0 and self.bank.state == HBM4BankState.CLOSED:
            elapsed = self._cycles_since(self.last_act_cycle)
            if elapsed < self.timing.tRC:
                violations.append(TimingViolation(
                    violation_type='tRC',
                    required_cycles=self.timing.tRC,
                    actual_cycles=elapsed,
                    bank_id=self.bank_id,
                    cycle=self.current_cycle,
                    description=f"tRC: need {self.timing.tRC} cycles, have {elapsed}"
                ))

        # Check tRAS
        if self.bank.activate_start_cycle >= 0:
            elapsed = self._cycles_since(self.bank.activate_start_cycle)
            if self.bank.state == HBM4BankState.OPEN and elapsed < self.timing.tRAS:
                # Precharge should not have happened
                pass
            elif elapsed < self.timing.tRAS and self.bank.state == HBM4BankState.CLOSED:
                # Early precharge
                violations.append(TimingViolation(
                    violation_type='tRAS',
                    required_cycles=self.timing.tRAS,
                    actual_cycles=elapsed,
                    bank_id=self.bank_id,
                    cycle=self.current_cycle,
                    description=f"tRAS: need {self.timing.tRAS} cycles, have {elapsed}"
                ))

        return violations

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_state(self) -> HBM4BankState:
        """Get current bank state"""
        return self.bank.state

    def get_open_row(self) -> int:
        """Get currently open row"""
        return self.bank.open_row

    def is_row_hit(self, row: int) -> bool:
        """Check if the specified row is open"""
        return self.bank.is_open and self.bank.open_row == row

    def get_violations(self) -> List[TimingViolation]:
        """Get recorded timing violations"""
        return self.violations.copy()

    def clear_violations(self):
        """Clear recorded violations"""
        self.violations.clear()

    def reset(self):
        """Reset bank state"""
        self.bank = HBM4Bank(
            bank_id=self.bank_id,
            channel_id=self.channel_id,
            pseudo_channel_id=self.pseudo_channel_id,
            bank_group_id=self.bank_group_id
        )
        self.current_cycle = 0
        self.violations.clear()
        self.last_act_cycle = -1
        self.last_col_cmd_cycle = -1

    def get_info(self) -> Dict:
        """Get bank state information"""
        return {
            'bank_id': self.bank_id,
            'channel_id': self.channel_id,
            'pseudo_channel_id': self.pseudo_channel_id,
            'bank_group_id': self.bank_group_id,
            'state': self.bank.state.name,
            'open_row': self.bank.open_row,
            'current_cycle': self.current_cycle,
            'last_act_cycle': self.last_act_cycle,
            'violations': len(self.violations)
        }

    def __repr__(self) -> str:
        return (f"HBM4BankSM(bank={self.bank_id}, ch={self.channel_id}, "
                f"pch={self.pseudo_channel_id}, bg={self.bank_group_id}, "
                f"state={self.bank.state.name}, row={self.bank.open_row})")


class HBM4BankArray:
    """Array of HBM4 banks for a single pseudo-channel

    Manages 16 banks organized into 8 bank groups (2 banks per group).
    """

    def __init__(self, pseudo_channel_id: int = 0, channel_id: int = 0,
                 timing: Optional[HBM4BankTiming] = None):
        """Initialize bank array

        Args:
            pseudo_channel_id: Pseudo-channel index (0-1)
            channel_id: Channel index (0-31)
            timing: Timing parameters
        """
        self.pseudo_channel_id = pseudo_channel_id
        self.channel_id = channel_id
        self.timing = timing if timing is not None else HBM4BankTiming()

        # Create 16 banks (8 bank groups × 2 banks)
        self.banks: List[HBM4BankStateMachine] = []
        for bank_id in range(16):
            bg_id = bank_id // 2  # Bank group: 0-7
            bank = HBM4BankStateMachine(
                bank_id=bank_id,
                timing=self.timing,
                channel_id=channel_id,
                pseudo_channel_id=pseudo_channel_id,
                bank_group_id=bg_id
            )
            self.banks.append(bank)

    def set_time(self, cycle: int):
        """Set time for all banks"""
        for bank in self.banks:
            bank.set_time(cycle)

    def tick(self, advance_cycle: bool = True):
        """Advance time and process state completions

        Args:
            advance_cycle: If True, increment current_cycle for each bank.
                          Set to False when called from HBM4Channel.tick() which
                          already sets current_time via set_time().
        """
        for bank in self.banks:
            # Only increment if explicitly requested
            if advance_cycle:
                bank.current_cycle += 1

            # Auto-complete state transitions
            if bank.bank.state == HBM4BankState.ACTIVATING:
                bank.complete_activation()
            elif bank.bank.state == HBM4BankState.PRECHARGING:
                bank.complete_precharge()
            elif bank.bank.state == HBM4BankState.READ:
                bank.complete_read()
            elif bank.bank.state == HBM4BankState.WRITE:
                bank.complete_write()
            elif bank.bank.state == HBM4BankState.REFRESH:
                bank.complete_refresh()

    def get_bank(self, bank_id: int) -> Optional[HBM4BankStateMachine]:
        """Get bank by ID"""
        if 0 <= bank_id < len(self.banks):
            return self.banks[bank_id]
        return None

    def get_banks_in_group(self, bg_id: int) -> List[HBM4BankStateMachine]:
        """Get all banks in a bank group"""
        return [self.banks[bg_id * 2 + i] for i in range(2)]

    def get_active_bank_count(self) -> int:
        """Get count of active (open) banks"""
        return sum(1 for b in self.banks if b.bank.is_open)

    def get_idle_bank_count(self) -> int:
        """Get count of idle (closed) banks"""
        return sum(1 for b in self.banks if b.bank.is_closed)

    def reset(self):
        """Reset all banks"""
        for bank in self.banks:
            bank.reset()


# Factory functions
def create_hbm4_bank_state_machine(bank_id: int, timing: Optional[HBM4BankTiming] = None,
                                    channel_id: int = 0, pseudo_channel_id: int = 0) -> HBM4BankStateMachine:
    """Factory function to create HBM4 bank state machine

    Args:
        bank_id: Bank index within pseudo-channel (0-15)
        timing: Timing parameters
        channel_id: Channel index (0-31)
        pseudo_channel_id: Pseudo-channel index (0-1)

    Returns:
        HBM4BankStateMachine instance
    """
    bg_id = bank_id // 2
    return HBM4BankStateMachine(
        bank_id=bank_id,
        timing=timing,
        channel_id=channel_id,
        pseudo_channel_id=pseudo_channel_id,
        bank_group_id=bg_id
    )


def create_hbm4_bank_array(pseudo_channel_id: int = 0, channel_id: int = 0,
                           timing: Optional[HBM4BankTiming] = None) -> HBM4BankArray:
    """Factory function to create HBM4 bank array for a pseudo-channel

    Args:
        pseudo_channel_id: Pseudo-channel index (0-1)
        channel_id: Channel index (0-31)
        timing: Timing parameters

    Returns:
        HBM4BankArray with 16 banks
    """
    return HBM4BankArray(
        pseudo_channel_id=pseudo_channel_id,
        channel_id=channel_id,
        timing=timing
    )
