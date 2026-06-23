"""
HBM4 Logic Base Die Model

Unified wrapper integrating all Logic Base Die components for HBM4 simulation.
The Logic Base Die is the control die in the HBM stack that manages:
- Address decoding and routing
- PHY interface and signal encoding
- Training and calibration
- Lane repair and redundancy
- ECC/CRC error handling
- Per-channel independent timing management

Key features:
- Per-channel independent operation (JEDEC requirement)
- Integration with existing modules (PHY, Lane Repair, ECC)
- Cycle-accurate timing model
- DFI 5.0 interface support
- Enhanced PAM3 encoding/decoding
- Advanced command buffering and scheduling
- Comprehensive calibration data management

Based on:
- JEDEC JESD270-4A HBM4 specification
- Project's existing HBM4 modules
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import math

# Import existing HBM4 modules
from model.dram.hbm4_spec import HBM4Spec
from model.dram.phy_signal import (
    PAM3SignalModel,
    HBM4PAM3Encoder,
    PAM3Symbol,
    PAM3Level,
    PAM3EyeDiagram,
)
from model.dram.phy_training import (
    HBM4PHYManager,
    PHYTrainingStateMachine,
    PHYInitializationStateMachine,
)
from model.dram.lane_repair import HBM4LaneRepairModel, RepairStatus
from model.dram.ecc_crc import HBM4DataIntegrity, HBM4ECC, HBM4CRC
from model.dram.dfi_interface import (
    DFI5Interface,
    DFICommand,
    DFIRequest,
    DFIResponse,
    DFILowPowerState,
)
from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
from model.dram.timing import HBM3Timing


class ChannelState(Enum):
    """Channel operational state"""
    IDLE = "idle"
    ACTIVE = "active"
    TRAINING = "training"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    LOW_POWER = "low_power"


# ============================================================================
# Calibration Data Management
# ============================================================================

class CalibrationType(Enum):
    """Types of calibration procedures"""
    WRITE_LEVELING = "write_leveling"
    READ_GATE_TRAINING = "read_gate_training"
    READ_DQ_TRAINING = "read_dq_training"
    WRITE_DQ_TRAINING = "write_dq_training"
    VREF_CALIBRATION = "vref_calibration"
    IMPEDANCE_CALIBRATION = "impedance_calibration"
    READ_IMAIN = "read_imain"
    WRITE_IMAIN = "write_imain"
    MARGIN_CHECK = "margin_check"


@dataclass
class CalibrationData:
    """Calibration data for a single calibration procedure"""
    calibration_type: CalibrationType
    channel_id: int
    passed: bool = False
    timestamp: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)
    margins: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    iterations: int = 0
    quality_score: float = 0.0  # 0.0 to 1.0


@dataclass
class CalibrationResult:
    """Complete calibration result for a channel"""
    channel_id: int
    timestamp: int
    overall_passed: bool = False
    calibrations: Dict[CalibrationType, CalibrationData] = field(default_factory=dict)
    firmware_version: str = "1.0.0"
    build_date: str = ""
    notes: str = ""

    def get_calibration(self, cal_type: CalibrationType) -> Optional[CalibrationData]:
        """Get calibration data for a specific type"""
        return self.calibrations.get(cal_type)

    def is_calibration_done(self, cal_type: CalibrationType) -> bool:
        """Check if a specific calibration is complete and passed"""
        cal = self.calibrations.get(cal_type)
        return cal is not None and cal.passed

    def get_overall_quality(self) -> float:
        """Calculate overall calibration quality score"""
        if not self.calibrations:
            return 0.0
        total = sum(c.quality_score for c in self.calibrations.values())
        return total / len(self.calibrations)


class CalibrationManager:
    """Manages calibration data for all channels

    Provides centralized storage and retrieval of calibration data
    with support for persistence and comparison.
    """

    def __init__(self, num_channels: int = 32):
        """Initialize calibration manager

        Args:
            num_channels: Number of channels to support
        """
        self.num_channels = num_channels
        self._calibration_results: Dict[int, CalibrationResult] = {}
        self._calibration_history: Dict[int, List[CalibrationResult]] = {}
        self._pending_calibrations: Dict[int, List[CalibrationType]] = {}
        self._calibration_callbacks: Dict[CalibrationType, List[Callable]] = {}

        # Initialize empty results for all channels
        for ch in range(num_channels):
            self._calibration_results[ch] = CalibrationResult(
                channel_id=ch,
                timestamp=0,
            )
            self._calibration_history[ch] = []
            self._pending_calibrations[ch] = []

    def start_calibration(
        self,
        channel_id: int,
        cal_type: CalibrationType,
        timestamp: int = 0,
    ) -> CalibrationData:
        """Start a new calibration procedure

        Args:
            channel_id: Target channel
            cal_type: Type of calibration
            timestamp: Current simulation cycle

        Returns:
            CalibrationData object for tracking progress
        """
        cal_data = CalibrationData(
            calibration_type=cal_type,
            channel_id=channel_id,
            timestamp=timestamp,
        )

        # Store in results
        if channel_id not in self._calibration_results:
            self._calibration_results[channel_id] = CalibrationResult(
                channel_id=channel_id,
                timestamp=timestamp,
            )
        self._calibration_results[channel_id].calibrations[cal_type] = cal_data

        # Add to pending list
        if cal_type not in self._pending_calibrations[channel_id]:
            self._pending_calibrations[channel_id].append(cal_type)

        return cal_data

    def update_calibration(
        self,
        channel_id: int,
        cal_type: CalibrationType,
        settings: Optional[Dict[str, Any]] = None,
        margins: Optional[Dict[str, float]] = None,
    ):
        """Update calibration data during procedure

        Args:
            channel_id: Target channel
            cal_type: Type of calibration
            settings: Updated settings
            margins: Updated margins
        """
        if channel_id not in self._calibration_results:
            return

        cal_data = self._calibration_results[channel_id].calibrations.get(cal_type)
        if cal_data is None:
            return

        if settings:
            cal_data.settings.update(settings)
        if margins:
            cal_data.margins.update(margins)
        cal_data.iterations += 1

    def complete_calibration(
        self,
        channel_id: int,
        cal_type: CalibrationType,
        passed: bool,
        final_settings: Optional[Dict[str, Any]] = None,
        quality_score: float = 1.0,
    ):
        """Complete a calibration procedure

        Args:
            channel_id: Target channel
            cal_type: Type of calibration
            passed: Whether calibration passed
            final_settings: Final calibrated settings
            quality_score: Quality score (0.0 to 1.0)
        """
        if channel_id not in self._calibration_results:
            return

        cal_data = self._calibration_results[channel_id].calibrations.get(cal_type)
        if cal_data is None:
            return

        cal_data.passed = passed
        if final_settings:
            cal_data.settings = final_settings
        cal_data.quality_score = quality_score

        # Remove from pending
        if cal_type in self._pending_calibrations[channel_id]:
            self._pending_calibrations[channel_id].remove(cal_type)

        # Trigger callbacks
        for callback in self._calibration_callbacks.get(cal_type, []):
            callback(channel_id, cal_data)

        # Check overall status
        self._update_overall_passed(channel_id)

    def fail_calibration(
        self,
        channel_id: int,
        cal_type: CalibrationType,
        error: str,
    ):
        """Record a calibration failure

        Args:
            channel_id: Target channel
            cal_type: Type of calibration
            error: Error message
        """
        if channel_id not in self._calibration_results:
            return

        cal_data = self._calibration_results[channel_id].calibrations.get(cal_type)
        if cal_data:
            cal_data.errors.append(error)
            cal_data.passed = False

    def _update_overall_passed(self, channel_id: int):
        """Update overall pass status for channel"""
        result = self._calibration_results.get(channel_id)
        if result is None:
            return

        # All required calibrations must pass
        required = [
            CalibrationType.WRITE_LEVELING,
            CalibrationType.READ_GATE_TRAINING,
            CalibrationType.VREF_CALIBRATION,
        ]
        result.overall_passed = all(
            result.is_calibration_done(cal_type) for cal_type in required
        )

    def get_channel_calibration(self, channel_id: int) -> CalibrationResult:
        """Get complete calibration result for a channel

        Args:
            channel_id: Channel to query

        Returns:
            CalibrationResult for the channel
        """
        return self._calibration_results.get(
            channel_id,
            CalibrationResult(channel_id=channel_id, timestamp=0)
        )

    def get_calibration_status(self, channel_id: int) -> Dict[str, Any]:
        """Get calibration status summary for a channel

        Args:
            channel_id: Channel to query

        Returns:
            Dictionary with calibration status
        """
        result = self._calibration_results.get(channel_id)
        if result is None:
            return {'calibrated': False, 'pending': []}

        return {
            'calibrated': result.overall_passed,
            'pending': [c.value for c in self._pending_calibrations[channel_id]],
            'completed': [
                (c.value, data.passed, data.quality_score)
                for c, data in result.calibrations.items()
            ],
            'quality_score': result.get_overall_quality(),
        }

    def is_channel_calibrated(self, channel_id: int) -> bool:
        """Check if a channel is fully calibrated

        Args:
            channel_id: Channel to check

        Returns:
            True if all required calibrations passed
        """
        result = self._calibration_results.get(channel_id)
        return result is not None and result.overall_passed

    def register_callback(
        self,
        cal_type: CalibrationType,
        callback: Callable[[int, CalibrationData], None],
    ):
        """Register a callback for calibration completion

        Args:
            cal_type: Calibration type to watch
            callback: Function to call on completion
        """
        if cal_type not in self._calibration_callbacks:
            self._calibration_callbacks[cal_type] = []
        self._calibration_callbacks[cal_type].append(callback)

    def export_calibration(self, channel_id: int) -> Dict[str, Any]:
        """Export calibration data for persistence

        Args:
            channel_id: Channel to export

        Returns:
            Dictionary suitable for JSON serialization
        """
        result = self._calibration_results.get(channel_id)
        if result is None:
            return {}

        return {
            'channel_id': result.channel_id,
            'timestamp': result.timestamp,
            'overall_passed': result.overall_passed,
            'calibrations': {
                c.value: {
                    'passed': d.passed,
                    'settings': d.settings,
                    'margins': d.margins,
                    'quality_score': d.quality_score,
                    'iterations': d.iterations,
                }
                for c, d in result.calibrations.items()
            },
        }

    def import_calibration(self, data: Dict[str, Any]):
        """Import calibration data from persistence

        Args:
            data: Dictionary from export_calibration
        """
        if not data or 'channel_id' not in data:
            return

        channel_id = data['channel_id']
        result = CalibrationResult(
            channel_id=channel_id,
            timestamp=data.get('timestamp', 0),
            overall_passed=data.get('overall_passed', False),
        )

        for cal_str, cal_data in data.get('calibrations', {}).items():
            try:
                cal_type = CalibrationType(cal_str)
                result.calibrations[cal_type] = CalibrationData(
                    calibration_type=cal_type,
                    channel_id=channel_id,
                    passed=cal_data.get('passed', False),
                    settings=cal_data.get('settings', {}),
                    margins=cal_data.get('margins', {}),
                    quality_score=cal_data.get('quality_score', 0.0),
                    iterations=cal_data.get('iterations', 0),
                )
            except ValueError:
                pass

        self._calibration_results[channel_id] = result

    def compare_calibrations(
        self,
        channel_a: int,
        channel_b: int,
    ) -> Dict[str, Tuple[float, float]]:
        """Compare calibrations between two channels

        Args:
            channel_a: First channel
            channel_b: Second channel

        Returns:
            Dictionary mapping calibration type to (channel_a_score, channel_b_score)
        """
        result_a = self._calibration_results.get(channel_a)
        result_b = self._calibration_results.get(channel_b)

        if result_a is None or result_b is None:
            return {}

        comparison = {}
        all_types = set(result_a.calibrations.keys()) | set(result_b.calibrations.keys())

        for cal_type in all_types:
            cal_a = result_a.calibrations.get(cal_type)
            cal_b = result_b.calibrations.get(cal_type)
            score_a = cal_a.quality_score if cal_a else 0.0
            score_b = cal_b.quality_score if cal_b else 0.0
            comparison[cal_type.value] = (score_a, score_b)

        return comparison


# ============================================================================
# Per-Channel Independent Timing Management
# ============================================================================

@dataclass
class ChannelTimingContext:
    """Independent timing state for each channel

    Each channel maintains its own timing counters and constraints
    independent of other channels, as required by JEDEC specification.
    """
    channel_id: int

    # Timing counters (cycles)
    cycle_counter: int = 0
    last_act_cycle: int = -1
    last_pre_cycle: int = -1
    last_rd_cycle: int = -1
    last_wr_cycle: int = -1
    last_ref_cycle: int = -1
    last_mrs_cycle: int = -1

    # State tracking
    open_row: Optional[int] = None
    open_bank: Optional[int] = None

    # Timing constraints from spec
    tRC_cycles: int = 0      # Row cycle time
    tRCD_cycles: int = 0     # RAS to CAS delay
    tRP_cycles: int = 0      # Precharge time
    tRAS_cycles: int = 0     # Active to precharge
    tRRD_cycles: int = 0     # Active to active
    tFAW_cycles: int = 0     # Four activate window
    tCCD_cycles: int = 0     # CAS to CAS
    tWTR_cycles: int = 0     # Write to read
    tRTW_cycles: int = 0     # Read to write
    tWR_cycles: int = 0      # Write recovery
    tRFC_cycles: int = 0     # Refresh cycle time

    # Command rate limiting
    act_count_4cycle_window: int = 0
    last_4act_window_start: int = 0

    # Channel-specific frequency (supports mixed speed grades)
    frequency_mhz: int = 800

    # PLL/DLL state
    pll_locked: bool = False
    dll_locked: bool = False

    # Calibration state
    calibrated: bool = False
    training_passed: bool = False

    def can_issue_act(self) -> bool:
        """Check if ACT command can be issued based on timing"""
        if self.last_act_cycle < 0:
            return True

        # tRC constraint
        cycles_since_act = self.cycle_counter - self.last_act_cycle
        if cycles_since_act < self.tRC_cycles:
            return False

        # tRRD constraint
        cycles_since_rrd = self.cycle_counter - self.last_act_cycle
        if cycles_since_rrd < self.tRRD_cycles:
            return False

        # tFAW constraint (4 activations in 4*tFAW window)
        window_start = self.cycle_counter - self.tFAW_cycles * 4
        if window_start > self.last_4act_window_start:
            self.act_count_4cycle_window = 0
            self.last_4act_window_start = self.cycle_counter

        if self.act_count_4cycle_window >= 4:
            return False

        return True

    def can_issue_pre(self) -> bool:
        """Check if PRE command can be issued based on timing"""
        if self.last_act_cycle < 0:
            return False

        # tRAS constraint
        cycles_since_act = self.cycle_counter - self.last_act_cycle
        if cycles_since_act < self.tRAS_cycles:
            return False

        return True

    def can_issue_rd(self) -> bool:
        """Check if READ command can be issued based on timing"""
        if self.last_act_cycle < 0:
            return False

        # tRCD constraint
        cycles_since_act = self.cycle_counter - self.last_act_cycle
        if cycles_since_act < self.tRCD_cycles:
            return False

        # tCCD constraint
        if self.last_rd_cycle >= 0:
            cycles_since_rd = self.cycle_counter - self.last_rd_cycle
            if cycles_since_rd < self.tCCD_cycles:
                return False

        # tRTW constraint
        if self.last_wr_cycle >= 0:
            cycles_since_wr = self.cycle_counter - self.last_wr_cycle
            if cycles_since_wr < self.tRTW_cycles:
                return False

        return True

    def can_issue_wr(self) -> bool:
        """Check if WRITE command can be issued based on timing"""
        if self.last_act_cycle < 0:
            return False

        # tRCD constraint
        cycles_since_act = self.cycle_counter - self.last_act_cycle
        if cycles_since_act < self.tRCD_cycles:
            return False

        # tCCD constraint
        if self.last_wr_cycle >= 0:
            cycles_since_wr = self.cycle_counter - self.last_wr_cycle
            if cycles_since_wr < self.tCCD_cycles:
                return False

        # tWTR constraint
        if self.last_rd_cycle >= 0:
            cycles_since_rd = self.cycle_counter - self.last_rd_cycle
            if cycles_since_rd < self.tWTR_cycles:
                return False

        return True

    def can_issue_ref(self) -> bool:
        """Check if REFRESH command can be issued based on timing"""
        if self.last_ref_cycle < 0:
            return True

        cycles_since_ref = self.cycle_counter - self.last_ref_cycle
        if cycles_since_ref < self.tRFC_cycles:
            return False

        return True

    def issue_act(self, row: int, bank: Optional[int] = None):
        """Record an ACT command was issued"""
        self.last_act_cycle = self.cycle_counter
        self.open_row = row
        self.open_bank = bank

        # Update tFAW counter
        window_start = self.cycle_counter - self.tFAW_cycles * 4
        if window_start > self.last_4act_window_start:
            self.act_count_4cycle_window = 0
            self.last_4act_window_start = self.cycle_counter
        self.act_count_4cycle_window += 1

    def issue_pre(self):
        """Record a PRE command was issued"""
        self.last_pre_cycle = self.cycle_counter
        self.open_row = None
        self.open_bank = None

    def issue_rd(self):
        """Record a READ command was issued"""
        self.last_rd_cycle = self.cycle_counter

    def issue_wr(self):
        """Record a WRITE command was issued"""
        self.last_wr_cycle = self.cycle_counter

    def issue_ref(self):
        """Record a REFRESH command was issued"""
        self.last_ref_cycle = self.cycle_counter

    def is_row_hit(self, row: int) -> bool:
        """Check if row is currently open"""
        return self.open_row == row

    def get_timing_violation_info(self) -> Dict[str, int]:
        """Get information about timing violations if any"""
        violations = {}

        if self.last_act_cycle >= 0:
            cycles_since_act = self.cycle_counter - self.last_act_cycle
            if cycles_since_act < self.tRC_cycles:
                violations['tRC'] = self.tRC_cycles - cycles_since_act
            if cycles_since_act < self.tRCD_cycles:
                violations['tRCD'] = self.tRCD_cycles - cycles_since_act
            if cycles_since_act < self.tRAS_cycles:
                violations['tRAS'] = self.tRAS_cycles - cycles_since_act

        return violations


# ============================================================================
# Enhanced Channel Context
# ============================================================================

@dataclass
class ChannelContext:
    """Per-channel execution context

    Each channel maintains independent state including:
    - Local clock domain
    - Timing parameters
    - Bank state machine
    - Pending commands
    - Calibration data
    - PAM3 state
    """
    channel_id: int
    state: ChannelState = ChannelState.IDLE
    local_cycle: int = 0

    # Timing state
    last_act_cycle: int = -1
    last_pre_cycle: int = -1
    last_rd_cycle: int = -1
    last_wr_cycle: int = -1
    open_row: Optional[int] = None

    # Training state
    training_passed: bool = False
    calibration_data: Dict[str, Any] = field(default_factory=dict)

    # Lane repair state
    repair_status: RepairStatus = RepairStatus.NO_REPAIR
    repaired_lanes: List[int] = field(default_factory=list)

    # Error state
    error_count: int = 0
    last_error: Optional[str] = None

    # Bank state tracking per pseudo-channel and bank
    bank_states: Dict[int, BankStateEnum] = field(default_factory=dict)

    # Enhanced timing context
    timing_ctx: Optional[ChannelTimingContext] = None

    # PAM3 encoding state
    pam3_symbol_buffer: List[PAM3Symbol] = field(default_factory=list)
    pam3_decode_errors: int = 0

    # Command scheduling
    pending_commands: deque = field(default_factory=lambda: deque(maxlen=32))
    command_aging_cycles: int = 0

    # Low power state
    in_low_power: bool = False
    lp_entry_cycle: int = -1

    def get_idle_time(self, current_cycle: int) -> int:
        """Get time since last command"""
        last_cycle = max(
            self.last_act_cycle,
            self.last_pre_cycle,
            self.last_rd_cycle,
            self.last_wr_cycle,
        )
        if last_cycle < 0:
            return current_cycle
        return current_cycle - last_cycle


# ============================================================================
# Enhanced Command Buffer with Priority Scheduling
# ============================================================================

class SchedulingPolicy(Enum):
    """Command scheduling policies"""
    FIFO = "fifo"                    # Strict FIFO ordering
    PRIORITY = "priority"            # Priority-based scheduling
    AGING = "aging"                  # Aging-based scheduling (fairness)
    CHANNEL_AWARE = "channel_aware"  # Per-channel fairness
    MIXED = "mixed"                  # Combination of policies


@dataclass
class ScheduledCommand:
    """Enhanced command entry with scheduling metadata"""
    # Basic command info
    id: int
    command: str
    channel: int
    address: int
    priority: int = 0
    data: Optional[int] = None

    # Scheduling metadata
    enqueued_cycle: int = 0
    issued_cycle: Optional[int] = None
    completed_cycle: Optional[int] = None
    age: int = 0                     # Time in buffer (cycles)
    wait_time: int = 0               # Accumulated wait time
    starvation_counter: int = 0      # Commands bypassed by higher priority

    # State
    completed: bool = False
    deferred: bool = False
    deferred_reason: Optional[str] = None

    # Resource tracking
    bank: Optional[int] = None
    pseudo_channel: Optional[int] = None
    row: Optional[int] = None
    column: Optional[int] = None

    # Command-specific metadata
    is_read: bool = False
    is_write: bool = False
    is_refresh: bool = False


class CommandBuffer:
    """Enhanced command buffer with advanced scheduling

    Implements a multi-policy command buffer with:
    - Priority-based scheduling
    - Aging for fairness (prevent starvation)
    - Per-channel isolation
    - Command deferral for timing constraints
    - Bandwidth allocation per channel
    """

    def __init__(
        self,
        depth: int = 64,
        scheduling_policy: SchedulingPolicy = SchedulingPolicy.PRIORITY,
        enable_aging: bool = True,
        max_command_age: int = 1000,
    ):
        """Initialize enhanced command buffer

        Args:
            depth: Maximum number of commands in buffer
            scheduling_policy: Default scheduling policy
            enable_aging: Enable aging-based fairness
            max_command_age: Maximum age before forced scheduling
        """
        self.depth = depth
        self.scheduling_policy = scheduling_policy
        self.enable_aging = enable_aging
        self.max_command_age = max_command_age

        self._buffer: deque = deque(maxlen=depth)
        self._command_counter = 0
        self._total_commands_issued = 0
        self._total_commands_completed = 0
        self._total_commands_deferred = 0
        self._total_commands_dropped = 0

        # Per-channel statistics
        self._channel_stats: Dict[int, Dict[str, int]] = {}
        for ch in range(32):
            self._channel_stats[ch] = {
                'commands_issued': 0,
                'commands_completed': 0,
                'commands_deferred': 0,
                'total_wait_cycles': 0,
            }

        # Bandwidth allocation per channel
        self._channel_bandwidth_share: Dict[int, float] = {
            ch: 1.0 / 32 for ch in range(32)
        }
        self._channel_command_count: Dict[int, int] = {ch: 0 for ch in range(32)}

        # Command history for analysis
        self._command_history: deque = deque(maxlen=1000)

    def enqueue(
        self,
        command: str,
        channel: int,
        address: int,
        priority: int = 0,
        data: Optional[int] = None,
        enqueued_cycle: int = 0,
        **kwargs,
    ) -> int:
        """Add command to buffer with enhanced metadata

        Args:
            command: Command name (ACT, PRE, RD, WR, REF, MRS)
            channel: Target channel (0-31)
            address: Memory address
            priority: Command priority (higher = more urgent)
            data: Optional data payload for write commands
            enqueued_cycle: Current simulation cycle
            **kwargs: Additional metadata (bank, row, column, etc.)

        Returns:
            Command ID if successful, -1 if buffer full
        """
        if len(self._buffer) >= self.depth:
            self._total_commands_dropped += 1
            return -1

        cmd_id = self._command_counter
        self._command_counter += 1

        # Parse command type
        is_read = command in {'RD', 'RDA'}
        is_write = command in {'WR', 'WRA'}
        is_refresh = command in {'REF', 'REFab', 'REFsb'}

        cmd_entry = ScheduledCommand(
            id=cmd_id,
            command=command,
            channel=channel,
            address=address,
            priority=priority,
            data=data,
            enqueued_cycle=enqueued_cycle,
            bank=kwargs.get('bank'),
            pseudo_channel=kwargs.get('pseudo_channel'),
            row=kwargs.get('row'),
            column=kwargs.get('column'),
            is_read=is_read,
            is_write=is_write,
            is_refresh=is_refresh,
        )

        self._buffer.append(cmd_entry)
        self._channel_command_count[channel] = self._channel_command_count.get(channel, 0) + 1
        self._total_commands_issued += 1
        return cmd_id

    def dequeue(self) -> Optional[ScheduledCommand]:
        """Remove and return next command based on scheduling policy

        Returns:
            Next ScheduledCommand or None if empty
        """
        if not self._buffer:
            return None

        # Select command based on policy
        cmd = self._select_next_command()
        if cmd is None:
            return None

        cmd.completed = True
        self._buffer.remove(cmd)
        self._total_commands_completed += 1
        self._channel_stats[cmd.channel]['commands_completed'] += 1
        self._channel_stats[cmd.channel]['total_wait_cycles'] += cmd.wait_time
        self._channel_command_count[cmd.channel] -= 1

        # Record to history
        self._command_history.append({
            'id': cmd.id,
            'command': cmd.command,
            'channel': cmd.channel,
            'enqueued_cycle': cmd.enqueued_cycle,
            'completed_cycle': cmd.enqueued_cycle + cmd.age,
        })

        return cmd

    def _select_next_command(self) -> Optional[ScheduledCommand]:
        """Select next command based on scheduling policy

        Returns:
            Selected ScheduledCommand or None
        """
        if not self._buffer:
            return None

        # Update ages and check for starvation
        current_age = 0
        max_age = 0
        for cmd in self._buffer:
            if cmd.completed or cmd.deferred:
                continue
            cmd.age += 1
            cmd.wait_time += 1

            # Starvation detection
            if cmd.age > self.max_command_age:
                cmd.starvation_counter += 100  # Boost priority significantly

            if cmd.age > max_age:
                max_age = cmd.age
            current_age = max(current_age, cmd.age)

        # Filter out completed/deferred commands
        candidates = [cmd for cmd in self._buffer if not cmd.completed and not cmd.deferred]
        if not candidates:
            return None

        if self.scheduling_policy == SchedulingPolicy.FIFO:
            return candidates[0]  # Strict order

        elif self.scheduling_policy == SchedulingPolicy.PRIORITY:
            # Priority with aging boost
            for cmd in candidates:
                effective_priority = cmd.priority + (cmd.age // 10)
                cmd.effective_priority = effective_priority
            candidates.sort(key=lambda c: c.effective_priority, reverse=True)
            return candidates[0]

        elif self.scheduling_policy == SchedulingPolicy.AGING:
            # Age-based with priority tiebreaker
            candidates.sort(key=lambda c: (c.age, c.priority), reverse=True)
            return candidates[0]

        elif self.scheduling_policy == SchedulingPolicy.CHANNEL_AWARE:
            # Fair per-channel scheduling
            channel_counts = {}
            for cmd in candidates:
                ch = cmd.channel
                if ch not in channel_counts:
                    channel_counts[ch] = 0
                channel_counts[ch] += 1

            # Select from least-served channel
            min_count = min(channel_counts.values())
            least_served = [ch for ch, cnt in channel_counts.items() if cnt == min_count]

            # Among least-served, pick highest priority
            from_least_served = [c for c in candidates if c.channel in least_served]
            from_least_served.sort(key=lambda c: c.priority, reverse=True)
            return from_least_served[0] if from_least_served else candidates[0]

        else:  # MIXED or default
            # Combination: age boost + priority + channel fairness
            for cmd in candidates:
                age_boost = min(cmd.age // 20, 5)  # Max 5 age boost
                starvation_boost = min(cmd.starvation_counter // 10, 10)
                cmd.effective_priority = (
                    cmd.priority * 10 + age_boost + starvation_boost
                )

            candidates.sort(key=lambda c: c.effective_priority, reverse=True)
            return candidates[0]

    def defer_command(
        self,
        cmd_id: int,
        reason: str,
    ) -> bool:
        """Defer a command (keep in buffer but skip scheduling)

        Args:
            cmd_id: Command ID to defer
            reason: Reason for deferral

        Returns:
            True if command was found and deferred
        """
        for cmd in self._buffer:
            if cmd.id == cmd_id and not cmd.completed:
                cmd.deferred = True
                cmd.deferred_reason = reason
                self._total_commands_deferred += 1
                return True
        return False

    def can_issue_command(self, cmd: ScheduledCommand) -> Tuple[bool, Optional[str]]:
        """Check if a command can be issued (timing, resources)

        Args:
            cmd: Command to check

        Returns:
            Tuple of (can_issue, reason_if_not)
        """
        if cmd.deferred:
            return False, cmd.deferred_reason

        # Check channel state
        if cmd.channel not in range(32):
            return False, "Invalid channel"

        # Check buffer capacity
        if self.is_full:
            return False, "Buffer full"

        return True, None

    def peek(self) -> Optional[ScheduledCommand]:
        """View next command without removing

        Returns:
            Next ScheduledCommand or None if empty
        """
        if not self._buffer:
            return None

        candidates = [cmd for cmd in self._buffer if not cmd.completed and not cmd.deferred]
        if not candidates:
            return None

        # Return highest priority
        candidates.sort(key=lambda c: (c.priority, -c.age), reverse=True)
        return candidates[0]

    def peek_channel(self, channel: int) -> List[ScheduledCommand]:
        """Get all commands for a specific channel

        Args:
            channel: Channel to query

        Returns:
            List of commands for the channel
        """
        return [
            cmd for cmd in self._buffer
            if cmd.channel == channel and not cmd.completed
        ]

    def tick(self, current_cycle: int = 0):
        """Advance buffer state (called each cycle)

        Updates internal timestamps and aging for queued commands.
        """
        # Reset starvation counters for commands that were bypassed
        for cmd in self._buffer:
            if not cmd.completed and not cmd.deferred:
                if cmd.age > 0:
                    cmd.starvation_counter = 0

    def clear(self):
        """Clear all commands from buffer"""
        self._buffer.clear()
        self._channel_command_count = {ch: 0 for ch in range(32)}

    def get_channel_queue_depth(self, channel: int) -> int:
        """Get number of pending commands for a channel

        Args:
            channel: Channel to query

        Returns:
            Number of pending commands
        """
        return self._channel_command_count.get(channel, 0)

    @property
    def size(self) -> int:
        """Current buffer size"""
        return len(self._buffer)

    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return len(self._buffer) == 0

    @property
    def is_full(self) -> bool:
        """Check if buffer is at capacity"""
        return len(self._buffer) >= self.depth

    @property
    def available_capacity(self) -> int:
        """Available slots in buffer"""
        return self.depth - len(self._buffer)

    def get_stats(self) -> Dict:
        """Get comprehensive buffer statistics"""
        return {
            'current_size': len(self._buffer),
            'max_depth': self.depth,
            'total_commands_issued': self._total_commands_issued,
            'total_commands_completed': self._total_commands_completed,
            'total_commands_deferred': self._total_commands_deferred,
            'total_commands_dropped': self._total_commands_dropped,
            'utilization': len(self._buffer) / self.depth if self.depth > 0 else 0,
            'scheduling_policy': self.scheduling_policy.value,
            'channel_stats': self._channel_stats,
        }


# ============================================================================
# Enhanced PAM3 Encoder/Decoder
# ============================================================================

class EnhancedPAM3Codec:
    """Enhanced PAM3 encoder/decoder with protocol-specific features

    Extends the basic PAM3 signal model with:
    - Command encoding with redundancy
    - Error detection and correction
    - Training pattern generation
    - Eye diagram analysis
    - SNR estimation
    - Multi-lane synchronization
    """

    def __init__(
        self,
        symbol_rate_gbaud: float = 8.0,
        voltage_swing: float = 0.8,
        enable_ecc: bool = True,
        enable_scrambling: bool = True,
    ):
        """Initialize enhanced PAM3 codec

        Args:
            symbol_rate_gbaud: Symbol rate in GBaud
            voltage_swing: Signal voltage swing (Vdiff)
            enable_ecc: Enable error correction coding
            enable_scrambling: Enable data scrambling
        """
        self.symbol_rate_gbaud = symbol_rate_gbaud
        self.voltage_swing = voltage_swing
        self.enable_ecc = enable_ecc
        self.enable_scrambling = enable_scrambling

        # Initialize base signal model
        self.signal_model = PAM3SignalModel(
            symbol_rate=symbol_rate_gbaud * 1e9,
            voltage_swing=voltage_swing,
        )

        # Scrambling polynomial (IEEE 802.3 compliant)
        self._scrambler_lfsr = 0x7FFF
        self._scrambler_polynomial = 0x4000  # x^15 + x + 1

        # Statistics
        self.symbols_encoded = 0
        self.symbols_decoded = 0
        self.encode_errors = 0
        self.decode_errors = 0
        self.corrected_errors = 0

        # Lane synchronization state
        self._lane_sync_state: Dict[int, Dict] = {}

        # Initialize training patterns
        self._training_patterns = self._init_training_patterns()

    def _init_training_patterns(self) -> Dict[str, List[int]]:
        """Initialize training patterns

        Returns:
            Dictionary of training patterns
        """
        patterns = {}

        # Balanced pattern: equal distribution of levels
        balanced = []
        for i in range(32):
            level = self.signal_model.LEVELS[i % 3]
            balanced.append(level)
        patterns['balanced'] = balanced

        # All positive level
        patterns['all_positive'] = [1] * 32

        # All negative level
        patterns['all_negative'] = [-1] * 32

        # PRBS9 pattern
        import random
        random.seed(0xABCD)
        lfsr = 0x1FF
        prbs9 = []
        for _ in range(32):
            bit = (lfsr >> 8) & 1
            prbs9.append(self.signal_model.LEVELS[bit] if bit else 0)
            new_bit = ((lfsr >> 4) ^ (lfsr >> 3) ^ (lfsr >> 1)) & 1
            lfsr = ((lfsr << 1) | new_bit) & 0x1FF
        patterns['prbs9'] = prbs9

        # PRBS15 pattern
        lfsr = 0x7FFF
        prbs15 = []
        for _ in range(32):
            bit = (lfsr >> 14) & 1
            prbs15.append(self.signal_model.LEVELS[bit] if bit else 0)
            new_bit = ((lfsr >> 13) ^ (lfsr >> 12) ^ (lfsr >> 10) ^ (lfsr >> 9)) & 1
            lfsr = ((lfsr << 1) | new_bit) & 0x7FFF
        patterns['prbs15'] = prbs15

        # DQ-DQS training pattern (alternating)
        dq_dqs = []
        for i in range(32):
            if i % 4 < 2:
                dq_dqs.append(1)   # DQS rising
            else:
                dq_dqs.append(-1)  # DQS falling
        patterns['dq_dqs'] = dq_dqs

        # Read DQ eye training pattern
        eye_pattern = []
        for i in range(32):
            level_idx = (i // 4) % 3
            eye_pattern.append(self.signal_model.LEVELS[level_idx])
        patterns['eye_train'] = eye_pattern

        return patterns

    def scramble(self, data: int, num_bits: int) -> int:
        """Scramble data using LFSR

        Args:
            data: Input data
            num_bits: Number of bits to scramble

        Returns:
            Scrambled data
        """
        scrambled = 0
        for i in range(num_bits):
            # Get LFSR output bit
            lfsr_bit = self._scrambler_lfsr & 1

            # Get data bit
            data_bit = (data >> i) & 1

            # XOR
            out_bit = data_bit ^ lfsr_bit
            scrambled |= (out_bit << i)

            # Advance LFSR
            new_bit = (
                (self._scrambler_lfsr >> 14) ^
                (self._scrambler_lfsr >> 0)
            ) & 1
            self._scrambler_lfsr = ((self._scrambler_lfsr >> 1) | (new_bit << 14)) & 0x7FFF

        return scrambled

    def descramble(self, data: int, num_bits: int) -> int:
        """Descramble data using LFSR

        Args:
            data: Scrambled data
            num_bits: Number of bits to descramble

        Returns:
            Original data
        """
        # Note: Descrambling uses same LFSR state
        return self.scramble(data, num_bits)

    def encode_command(
        self,
        command: int,
        address: int,
        cmd_bits: int = 16,
        addr_bits: int = 20,
    ) -> List[PAM3Symbol]:
        """Encode command and address as PAM3 symbols

        Args:
            command: Command bits
            address: Address bits
            cmd_bits: Number of command bits
            addr_bits: Number of address bits

        Returns:
            List of PAM3Symbol
        """
        # Combine command and address
        combined = (command << addr_bits) | (address & ((1 << addr_bits) - 1))
        total_bits = cmd_bits + addr_bits

        # Apply scrambling if enabled
        if self.enable_scrambling:
            combined = self.scramble(combined, total_bits)

        # Add ECC if enabled
        if self.enable_ecc:
            # Simple parity for demonstration
            parity = bin(combined).count('1') % 2
            combined = (combined << 1) | parity
            total_bits += 1

        try:
            symbols = self.signal_model.encode(combined, total_bits)
            self.symbols_encoded += len(symbols)
            return symbols
        except Exception as e:
            self.encode_errors += 1
            return []

    def decode_command(
        self,
        symbols: List[PAM3Symbol],
        cmd_bits: int = 16,
        addr_bits: int = 20,
    ) -> Tuple[Optional[int], Optional[int], bool]:
        """Decode PAM3 symbols to command and address

        Args:
            symbols: Received PAM3 symbols
            cmd_bits: Expected command bits
            addr_bits: Expected address bits

        Returns:
            Tuple of (command, address, error_detected)
        """
        if not symbols:
            self.decode_errors += 1
            return None, None, True

        try:
            # Decode symbols to bits
            expected_bits = cmd_bits + addr_bits
            if self.enable_ecc:
                expected_bits += 1

            data, num_bits = self.signal_model.decode(symbols)

            if num_bits < expected_bits:
                # Pad with zeros
                data <<= (expected_bits - num_bits)

            # Check ECC/parity if enabled
            error_detected = False
            if self.enable_ecc and num_bits >= expected_bits:
                received_parity = data & 1
                data >>= 1
                computed_parity = bin(data).count('1') % 2
                if received_parity != computed_parity:
                    error_detected = True
                    self.decode_errors += 1
                    # For single-bit errors, we could correct here
                    # For now, just report the error

            # Remove scrambling if enabled
            if self.enable_scrambling:
                data = self.descramble(data, expected_bits - (1 if self.enable_ecc else 0))

            # Extract command and address
            addr_bits_actual = addr_bits if not self.enable_ecc else addr_bits
            cmd_bits_actual = cmd_bits if not self.enable_ecc else cmd_bits

            address = data & ((1 << addr_bits_actual) - 1)
            command = (data >> addr_bits_actual) & ((1 << cmd_bits_actual) - 1)

            self.symbols_decoded += len(symbols)
            return command, address, error_detected

        except Exception as e:
            self.decode_errors += 1
            return None, None, True

    def encode_data_burst(
        self,
        data: int,
        dq_width: int = 128,
    ) -> List[PAM3Symbol]:
        """Encode data burst for transmission

        Args:
            data: Data to encode
            dq_width: DQ width per channel

        Returns:
            List of PAM3Symbol
        """
        # Apply scrambling
        if self.enable_scrambling:
            data = self.scramble(data, dq_width)

        try:
            symbols = self.signal_model.encode(data, dq_width)
            self.symbols_encoded += len(symbols)
            return symbols
        except Exception as e:
            self.encode_errors += 1
            return []

    def decode_data_burst(
        self,
        symbols: List[PAM3Symbol],
        dq_width: int = 128,
    ) -> Tuple[Optional[int], bool]:
        """Decode received data burst

        Args:
            symbols: Received PAM3 symbols
            dq_width: DQ width per channel

        Returns:
            Tuple of (data, error_detected)
        """
        if not symbols:
            self.decode_errors += 1
            return None, True

        try:
            data, num_bits = self.signal_model.decode(symbols)

            if num_bits < dq_width:
                data <<= (dq_width - num_bits)

            # Remove scrambling
            if self.enable_scrambling:
                data = self.descramble(data, dq_width)

            self.symbols_decoded += len(symbols)
            return data, False

        except Exception as e:
            self.decode_errors += 1
            return None, True

    def insert_training_sequence(
        self,
        pattern_name: str,
        length: int = 32,
    ) -> List[PAM3Symbol]:
        """Generate training sequence

        Args:
            pattern_name: Name of pattern to generate
            length: Sequence length

        Returns:
            List of PAM3Symbol for training
        """
        base_pattern = self._training_patterns.get(pattern_name, [0] * 32)
        symbols = []

        for i in range(length):
            level = base_pattern[i % len(base_pattern)]
            symbols.append(PAM3Symbol(
                level=level,
                ui_position=float(i),
                amplitude=self.signal_model.level_voltage[level],
            ))

        return symbols

    def verify_training_sequence(
        self,
        received: List[PAM3Symbol],
        pattern_name: str,
        tolerance: float = 0.05,
    ) -> Tuple[bool, float, Dict[str, int]]:
        """Verify received training sequence

        Args:
            received: Received symbols
            pattern_name: Expected pattern name
            tolerance: Error tolerance ratio

        Returns:
            Tuple of (passed, error_rate, error_positions)
        """
        expected = self._training_patterns.get(pattern_name, [])
        if not expected or not received:
            return False, 1.0, {}

        errors = 0
        error_positions = {}

        for i, sym in enumerate(received):
            expected_level = expected[i % len(expected)]

            # Check level match
            if sym.level != expected_level:
                errors += 1
                error_positions[i] = {
                    'expected': expected_level,
                    'received': sym.level,
                    'amplitude_error': abs(sym.amplitude - self.signal_model.level_voltage[expected_level]),
                }

        error_rate = errors / len(received)
        passed = error_rate <= tolerance

        return passed, error_rate, error_positions

    def analyze_eye_diagram(
        self,
        num_symbols: int = 1000,
    ) -> PAM3EyeDiagram:
        """Analyze eye diagram metrics

        Args:
            num_symbols: Number of symbols to simulate

        Returns:
            PAM3EyeDiagram with computed metrics
        """
        return self.signal_model.compute_eye_diagram(num_symbols=num_symbols)

    def get_snr_estimate(self) -> float:
        """Get current SNR estimate

        Returns:
            SNR in dB
        """
        return self.signal_model.get_snr_estimate()

    def get_bandwidth_efficiency(self) -> float:
        """Get bandwidth efficiency

        Returns:
            Bits per symbol
        """
        return self.signal_model.get_bandwidth_efficiency()

    def sync_lane(
        self,
        lane_id: int,
        training_sequence: List[PAM3Symbol],
    ) -> Tuple[bool, Dict]:
        """Synchronize a lane using training sequence

        Args:
            lane_id: Lane to synchronize
            training_sequence: Training sequence received

        Returns:
            Tuple of (sync_success, sync_info)
        """
        # Verify training sequence
        passed, error_rate, errors = self.verify_training_sequence(
            training_sequence,
            'prbs9',
            tolerance=0.01,
        )

        # Calculate offset
        offset = 0
        if errors:
            # Estimate timing offset from error positions
            error_positions = sorted(errors.keys())
            if len(error_positions) >= 2:
                offset = sum(errors[p].get('amplitude_error', 0) for p in error_positions) / len(error_positions)

        sync_info = {
            'lane_id': lane_id,
            'passed': passed,
            'error_rate': error_rate,
            'timing_offset': offset,
            'estimated_skew': len(errors) * 0.1,  # Simplified estimation
        }

        self._lane_sync_state[lane_id] = sync_info
        return passed, sync_info

    def get_lane_sync_status(self) -> Dict[int, Dict]:
        """Get synchronization status of all lanes

        Returns:
            Dictionary mapping lane_id to sync status
        """
        return dict(self._lane_sync_state)

    def reset_lfsr(self):
        """Reset scrambler LFSR state"""
        self._scrambler_lfsr = 0x7FFF

    def get_stats(self) -> Dict:
        """Get codec statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'symbols_encoded': self.symbols_encoded,
            'symbols_decoded': self.symbols_decoded,
            'encode_errors': self.encode_errors,
            'decode_errors': self.decode_errors,
            'corrected_errors': self.corrected_errors,
            'symbol_rate_gbaud': self.symbol_rate_gbaud,
            'snr_estimate_db': self.get_snr_estimate(),
            'bandwidth_efficiency': self.get_bandwidth_efficiency(),
            'lanes_synchronized': len(self._lane_sync_state),
        }


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class LogicBaseDieConfig:
    """Configuration for Logic Base Die model"""
    # Architecture
    num_channels: int = 32
    channel_width: int = 64           # JEDEC standard
    burst_width: int = 256            # Data width per channel (4 x 64)

    # Signal encoding
    pam3_enabled: bool = True
    symbol_rate_gbaud: float = 8.0    # 8 Gbaud for HBM4 base rate
    enable_pam3_ecc: bool = True
    enable_pam3_scrambling: bool = True

    # ECC/CRC
    ecc_enabled: bool = True
    crc_enabled: bool = True
    data_width: int = 64

    # Lane repair
    lanes_per_channel: int = 64
    spare_lanes_per_channel: int = 4

    # Training
    training_timeout_cycles: int = 50000
    auto_training: bool = True

    # Timing (cycles @ 8 GT/s)
    tCK_ps: float = 125.0            # 125ps = 8 GHz

    # Command buffer
    command_buffer_depth: int = 64
    scheduling_policy: SchedulingPolicy = SchedulingPolicy.PRIORITY
    enable_command_aging: bool = True
    max_command_age: int = 1000

    # Bank state tracking
    banks_per_channel: int = 16       # 16 banks per pseudo-channel
    pseudo_channels_per_channel: int = 2

    # Per-channel independent timing
    enable_independent_timing: bool = True


# ============================================================================
# Main Logic Base Die Class
# ============================================================================

class HBM4LogicBaseDie:
    """HBM4 Logic Base Die Model

    Unified model integrating all Logic Base Die functionality.
    Provides cycle-accurate simulation of the control die in HBM4 stack.

    Architecture:
    ```
    +----------------------------------------------------------+
    |                    Logic Base Die                          |
    |  +------------------+  +------------------+               |
    |  | Address Decoder   |  | Command Queue    |               |
    |  +------------------+  +------------------+               |
    |  +------------------+  +------------------+               |
    |  | Enhanced PAM3    |  | ECC/CRC Engine   |               |
    |  +------------------+  +------------------+               |
    |  +------------------+  +------------------+               |
    |  | PHY Manager      |  | Lane Repair      |               |
    |  +------------------+  +------------------+               |
    |  +------------------+  +------------------+               |
    |  | DFI 5.0 Interface|  | Calib. Manager  |               |
    |  +------------------+  +------------------+               |
    +----------------------------------------------------------+
    |         Per-Channel Contexts (x32) + Timing               |
    |  [Ch0] [Ch1] [Ch2] ... [Ch31]                            |
    |  [Timing0] [Timing1] ... [Timing31]                       |
    +----------------------------------------------------------+
    ```

    Usage:
        >>> lbd = HBM4LogicBaseDie()
        >>> lbd.initialize()
        >>> for _ in range(1000):
        ...     lbd.tick()
        >>> status = lbd.get_status()
    """

    def __init__(self, config: Optional[LogicBaseDieConfig] = None):
        """Initialize Logic Base Die model

        Args:
            config: Optional configuration
        """
        self.config = config or LogicBaseDieConfig()

        # Initialize specification
        self.spec = HBM4Spec()

        # Initialize Enhanced PAM3 codec (if enabled)
        if self.config.pam3_enabled:
            self.pam3_codec = EnhancedPAM3Codec(
                symbol_rate_gbaud=self.config.symbol_rate_gbaud,
                voltage_swing=0.8,
                enable_ecc=self.config.enable_pam3_ecc,
                enable_scrambling=self.config.enable_pam3_scrambling,
            )
            self.pam3_encoder = HBM4PAM3Encoder(config={
                'symbol_rate': self.config.symbol_rate_gbaud * 1e9,
                'voltage_swing': 0.8,
            })
        else:
            self.pam3_codec = None
            self.pam3_encoder = None

        # Initialize DFI 5.0 Interface
        self.dfi = DFI5Interface()

        # Initialize PHY Manager (per-channel training)
        self.phy_manager = HBM4PHYManager(
            num_channels=self.config.num_channels,
            config={
                'timeout_cycles': self.config.training_timeout_cycles,
            }
        )

        # Initialize Lane Repair (per-channel redundancy)
        self.lane_repair = HBM4LaneRepairModel(
            num_channels=self.config.num_channels,
            lanes_per_channel=self.config.lanes_per_channel,
            spare_lanes_per_channel=self.config.spare_lanes_per_channel,
        )

        # Initialize ECC/CRC (per-channel error handling)
        self.data_integrity = HBM4DataIntegrity(
            data_width=self.config.data_width,
            enable_ecc=self.config.ecc_enabled,
            enable_crc=self.config.crc_enabled,
        )

        # Initialize Calibration Manager
        self.calibration_manager = CalibrationManager(
            num_channels=self.config.num_channels
        )

        # Initialize Enhanced Command Buffer
        self.command_buffer = CommandBuffer(
            depth=self.config.command_buffer_depth,
            scheduling_policy=self.config.scheduling_policy,
            enable_aging=self.config.enable_command_aging,
            max_command_age=self.config.max_command_age,
        )

        # Initialize Bank State Tracking
        # Each channel has pseudo_channels * banks structure
        self._bank_state_machines: Dict[int, Dict[int, BankStateMachine]] = {}
        self._initialize_bank_state_machines()

        # Per-channel contexts (independent operation)
        self._channels: List[ChannelContext] = []
        self._timing_contexts: List[ChannelTimingContext] = []
        for ch in range(self.config.num_channels):
            self._channels.append(ChannelContext(channel_id=ch))
            self._timing_contexts.append(
                ChannelTimingContext(
                    channel_id=ch,
                    tRC_cycles=self.spec.nRC,
                    tRCD_cycles=self.spec.nRCDRD,  # Use nRCDRD for read timing
                    tRP_cycles=self.spec.nRP,
                    tRAS_cycles=self.spec.nRAS,
                    tRRD_cycles=self.spec.nRRDS,
                    tFAW_cycles=self.spec.nFAW,
                    tCCD_cycles=self.spec.nCCDS,
                    tWTR_cycles=self.spec.nWTRS,
                    tRTW_cycles=self.spec.nRTW,
                    tWR_cycles=self.spec.nWR,
                    tRFC_cycles=self.spec.nRFC,
                )
            )

        # Global state
        self._global_cycle = 0
        self._initialized = False
        self._training_complete = False

        # Statistics
        self._total_commands = 0
        self._total_errors = 0
        self._dfi_commands_sent = 0
        self._dfi_commands_completed = 0
        self._pam3_encode_count = 0
        self._pam3_decode_count = 0

    def _initialize_bank_state_machines(self):
        """Initialize bank state machines for all channels"""
        timing = HBM3Timing()
        total_banks = self.config.banks_per_channel * self.config.pseudo_channels_per_channel

        for ch in range(self.config.num_channels):
            self._bank_state_machines[ch] = {}
            for bank_id in range(total_banks):
                self._bank_state_machines[ch][bank_id] = BankStateMachine(
                    bank_id=bank_id,
                    timing=timing
                )

    @property
    def cycle(self) -> int:
        """Current global cycle"""
        return self._global_cycle

    @property
    def is_initialized(self) -> bool:
        """Check if Logic Base Die is initialized"""
        return self._initialized

    @property
    def is_ready(self) -> bool:
        """Check if all channels are ready"""
        return self._initialized and self._training_complete and self._phy_ready()

    def _phy_ready(self) -> bool:
        """Check if PHY training is complete on all channels"""
        return all(
            ctx.training_passed for ctx in self._channels
        )

    # ==================== Initialization ====================

    def initialize(self):
        """Initialize Logic Base Die

        Starts initialization sequence on all channels.
        """
        if self._initialized:
            return

        # Start PHY initialization on all channels
        self.phy_manager.start_initialization()
        self._initialized = True

    def tick(self):
        """Advance simulation by one cycle

        Updates all channel contexts, DFI interface, command buffer,
        and component state machines.
        """
        self._global_cycle += 1

        # Update DFI interface
        self.dfi.tick()

        # Update command buffer
        self.command_buffer.tick(self._global_cycle)

        # Update PHY state machines
        self.phy_manager.tick()

        # Update per-channel local cycles and timing contexts
        for ctx, timing in zip(self._channels, self._timing_contexts):
            ctx.local_cycle += 1
            timing.cycle_counter += 1

        # Check training completion
        if not self._training_complete:
            self._check_training_complete()

    def _check_training_complete(self):
        """Check if training is complete on all channels"""
        all_ready = True

        for ch, ctx in enumerate(self._channels):
            phy_status = self.phy_manager.get_channel_status(ch)

            if phy_status.get('training', {}).get('passed'):
                if not ctx.training_passed:
                    ctx.training_passed = True
                    # Collect calibration data
                    ctx.calibration_data = self.phy_manager.get_channel_status(ch)
                    timing = self._timing_contexts[ch]
                    timing.training_passed = True
                    timing.calibrated = True
                    timing.pll_locked = True  # PLL locks after training completes
                    timing.dll_locked = True  # DLL locks after training completes
            elif phy_status.get('state') != 'INIT_COMPLETE':
                all_ready = False

        if all_ready and self._initialized:
            self._training_complete = True

    # ==================== Enhanced Timing Management ====================

    def get_timing_context(self, channel_id: int) -> Optional[ChannelTimingContext]:
        """Get timing context for a channel

        Args:
            channel_id: Channel to query

        Returns:
            ChannelTimingContext or None
        """
        if 0 <= channel_id < self.config.num_channels:
            return self._timing_contexts[channel_id]
        return None

    def can_issue_timed_command(
        self,
        channel_id: int,
        command: str,
    ) -> Tuple[bool, Optional[str]]:
        """Check if a command can be issued based on channel timing

        Args:
            channel_id: Target channel
            command: Command to check

        Returns:
            Tuple of (can_issue, reason_if_not)
        """
        timing = self.get_timing_context(channel_id)
        if timing is None:
            return False, "Invalid channel"

        # Check PLL/DLL lock
        if not timing.pll_locked:
            return False, "PLL not locked"

        # Check training status
        if not timing.training_passed:
            return False, "Training not complete"

        # Check command-specific timing
        if command == 'ACT':
            if not timing.can_issue_act():
                return False, "tRC/tRRD/tFAW violation"
        elif command == 'PRE':
            if not timing.can_issue_pre():
                return False, "tRAS violation"
        elif command == 'RD' or command == 'RDA':
            if not timing.can_issue_rd():
                return False, "tRCD/tCCD/tRTW violation"
        elif command == 'WR' or command == 'WRA':
            if not timing.can_issue_wr():
                return False, "tRCD/tCCD/tWTR violation"
        elif command == 'REF' or command.startswith('REF'):
            if not timing.can_issue_ref():
                return False, "tRFC violation"

        return True, None

    def issue_timed_command(
        self,
        channel_id: int,
        command: str,
        address: int = 0,
    ) -> bool:
        """Issue a command and update channel timing

        Args:
            channel_id: Target channel
            command: Command to issue
            address: Address (row for ACT)

        Returns:
            True if command was issued
        """
        timing = self.get_timing_context(channel_id)
        if timing is None:
            return False

        row = address & 0xFFFF  # Extract row from address

        if command == 'ACT':
            timing.issue_act(row=row)
        elif command == 'PRE':
            timing.issue_pre()
        elif command in {'RD', 'RDA'}:
            timing.issue_rd()
        elif command in {'WR', 'WRA'}:
            timing.issue_wr()
        elif command.startswith('REF'):
            timing.issue_ref()

        return True

    def get_timing_violations(self, channel_id: int) -> Dict[str, int]:
        """Get pending timing violations for a channel

        Args:
            channel_id: Channel to check

        Returns:
            Dictionary of violation type to cycles remaining
        """
        timing = self.get_timing_context(channel_id)
        if timing is None:
            return {}
        return timing.get_timing_violation_info()

    # ==================== Calibration Management ====================

    def start_calibration(
        self,
        channel_id: int,
        cal_type: CalibrationType,
    ) -> bool:
        """Start calibration for a channel

        Args:
            channel_id: Target channel
            cal_type: Type of calibration

        Returns:
            True if started successfully
        """
        if not 0 <= channel_id < self.config.num_channels:
            return False

        self.calibration_manager.start_calibration(
            channel_id=channel_id,
            cal_type=cal_type,
            timestamp=self._global_cycle,
        )

        # Update channel state
        ctx = self._channels[channel_id]
        ctx.state = ChannelState.TRAINING

        return True

    def complete_calibration(
        self,
        channel_id: int,
        cal_type: CalibrationType,
        passed: bool,
        settings: Optional[Dict[str, Any]] = None,
        quality_score: float = 1.0,
    ):
        """Complete calibration for a channel

        Args:
            channel_id: Target channel
            cal_type: Type of calibration
            passed: Whether calibration passed
            settings: Final calibrated settings
            quality_score: Quality score (0.0 to 1.0)
        """
        self.calibration_manager.complete_calibration(
            channel_id=channel_id,
            cal_type=cal_type,
            passed=passed,
            final_settings=settings,
            quality_score=quality_score,
        )

        # Update channel state if all calibrations complete
        if self.calibration_manager.is_channel_calibrated(channel_id):
            ctx = self._channels[channel_id]
            if ctx.state == ChannelState.TRAINING:
                ctx.state = ChannelState.IDLE

    def get_calibration_status(
        self,
        channel_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get calibration status

        Args:
            channel_id: Specific channel or None for all

        Returns:
            Calibration status dictionary
        """
        if channel_id is not None:
            return self.calibration_manager.get_calibration_status(channel_id)

        return {
            f'ch{ch}': self.calibration_manager.get_calibration_status(ch)
            for ch in range(self.config.num_channels)
        }

    def is_calibrated(self, channel_id: int) -> bool:
        """Check if a channel is fully calibrated

        Args:
            channel_id: Channel to check

        Returns:
            True if calibrated
        """
        return self.calibration_manager.is_channel_calibrated(channel_id)

    # ==================== PAM3 Encoding/Decoding ====================

    def encode_pam3_command(
        self,
        command: int,
        address: int,
        channel: int,
    ) -> List[PAM3Symbol]:
        """Encode command as PAM3 symbols

        Args:
            command: Command bits
            address: Address bits
            channel: Target channel

        Returns:
            List of PAM3Symbol
        """
        if self.pam3_codec is None:
            return []

        symbols = self.pam3_codec.encode_command(command, address)
        self._pam3_encode_count += len(symbols)

        # Track in channel context
        if 0 <= channel < len(self._channels):
            self._channels[channel].pam3_symbol_buffer.extend(symbols)

        return symbols

    def decode_pam3_command(
        self,
        symbols: List[PAM3Symbol],
        channel: int,
    ) -> Tuple[Optional[int], Optional[int], bool]:
        """Decode PAM3 symbols to command

        Args:
            symbols: Received symbols
            channel: Source channel

        Returns:
            Tuple of (command, address, error_detected)
        """
        if self.pam3_codec is None:
            return None, None, True

        command, address, error = self.pam3_codec.decode_command(symbols)
        self._pam3_decode_count += 1

        # Track errors in channel context
        if 0 <= channel < len(self._channels) and error:
            self._channels[channel].pam3_decode_errors += 1

        return command, address, error

    def encode_pam3_data(
        self,
        data: int,
        channel: int,
    ) -> List[PAM3Symbol]:
        """Encode data as PAM3 symbols

        Args:
            data: Data to encode
            channel: Target channel

        Returns:
            List of PAM3Symbol
        """
        if self.pam3_codec is None:
            return []

        symbols = self.pam3_codec.encode_data_burst(data, dq_width=128)
        self._pam3_encode_count += len(symbols)

        if 0 <= channel < len(self._channels):
            self._channels[channel].pam3_symbol_buffer.extend(symbols)

        return symbols

    def decode_pam3_data(
        self,
        symbols: List[PAM3Symbol],
        channel: int,
    ) -> Tuple[Optional[int], bool]:
        """Decode PAM3 symbols to data

        Args:
            symbols: Received symbols
            channel: Source channel

        Returns:
            Tuple of (data, error_detected)
        """
        if self.pam3_codec is None:
            return None, True

        data, error = self.pam3_codec.decode_data_burst(symbols, dq_width=128)
        self._pam3_decode_count += 1

        if 0 <= channel < len(self._channels) and error:
            self._channels[channel].pam3_decode_errors += 1

        return data, error

    def get_pam3_stats(self) -> Dict:
        """Get PAM3 codec statistics

        Returns:
            Dictionary with statistics
        """
        if self.pam3_codec is None:
            return {'enabled': False}

        stats = self.pam3_codec.get_stats()
        stats.update({
            'encode_count': self._pam3_encode_count,
            'decode_count': self._pam3_decode_count,
            'channel_stats': {
                ch: {
                    'symbol_buffer_size': len(ctx.pam3_symbol_buffer),
                    'decode_errors': ctx.pam3_decode_errors,
                }
                for ch, ctx in enumerate(self._channels)
            },
        })
        return stats

    def analyze_pam3_eye(self) -> Optional[PAM3EyeDiagram]:
        """Analyze PAM3 eye diagram

        Returns:
            Eye diagram metrics or None if PAM3 disabled
        """
        if self.pam3_codec is None:
            return None
        return self.pam3_codec.analyze_eye_diagram()

    # ==================== Bank State Tracking ====================

    def get_bank_state(self, channel_id: int, bank_id: int) -> Optional[BankStateEnum]:
        """Get state of a specific bank

        Args:
            channel_id: Channel index (0-31)
            bank_id: Bank index within channel

        Returns:
            BankStateEnum or None if invalid channel/bank
        """
        if not 0 <= channel_id < self.config.num_channels:
            return None

        if channel_id not in self._bank_state_machines:
            return None

        if bank_id not in self._bank_state_machines[channel_id]:
            return None

        bsm = self._bank_state_machines[channel_id][bank_id]
        return bsm.bank.state

    def get_all_bank_states(self, channel_id: int) -> Dict[int, BankStateEnum]:
        """Get states of all banks in a channel

        Args:
            channel_id: Channel index (0-31)

        Returns:
            Dictionary mapping bank_id to BankStateEnum
        """
        if not 0 <= channel_id < self.config.num_channels:
            return {}

        states = {}
        if channel_id in self._bank_state_machines:
            for bank_id, bsm in self._bank_state_machines[channel_id].items():
                states[bank_id] = bsm.bank.state

        return states

    def can_activate_bank(self, channel_id: int, bank_id: int) -> bool:
        """Check if a bank can be activated

        Args:
            channel_id: Channel index
            bank_id: Bank index

        Returns:
            True if bank can be activated
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)
        return bsm.can_activate()

    def activate_bank(self, channel_id: int, bank_id: int, row: int) -> bool:
        """Activate a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index
            row: Row address to activate

        Returns:
            True if activation successful
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)
        success = bsm.activate(row)

        if success:
            # Update channel context
            ctx = self._channels[channel_id]
            ctx.last_act_cycle = ctx.local_cycle
            ctx.state = ChannelState.ACTIVE
            ctx.open_row = row
            ctx.bank_states[bank_id] = BankStateEnum.ACTIVE

            # Update timing context
            self.issue_timed_command(channel_id, 'ACT', address=row)

        return success

    def can_precharge_bank(self, channel_id: int, bank_id: int) -> bool:
        """Check if a bank can be precharged

        Args:
            channel_id: Channel index
            bank_id: Bank index

        Returns:
            True if bank can be precharged
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)

        # Check tRAS timing from timing context
        timing = self._timing_contexts[channel_id]
        if timing.last_act_cycle >= 0:
            cycles_since_act = timing.cycle_counter - timing.last_act_cycle
            if cycles_since_act < timing.tRAS_cycles:
                return False

        return bsm.can_precharge()

    def precharge_bank(self, channel_id: int, bank_id: int) -> bool:
        """Precharge a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index

        Returns:
            True if precharge successful
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)
        success = bsm.precharge()

        if success:
            # Update channel context
            ctx = self._channels[channel_id]
            ctx.last_pre_cycle = ctx.local_cycle
            ctx.open_row = None
            ctx.bank_states[bank_id] = BankStateEnum.IDLE

            # Update timing context
            self.issue_timed_command(channel_id, 'PRE')

        return success

    def can_read_bank(self, channel_id: int, bank_id: int) -> bool:
        """Check if a read can be issued to a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index

        Returns:
            True if read can be issued
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)
        return bsm.can_read()

    def read_bank(self, channel_id: int, bank_id: int) -> bool:
        """Issue a read to a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index

        Returns:
            True if read started successfully
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)
        success = bsm.read()

        if success:
            ctx = self._channels[channel_id]
            ctx.last_rd_cycle = ctx.local_cycle

            # Update timing context
            self.issue_timed_command(channel_id, 'RD')

        return success

    def can_write_bank(self, channel_id: int, bank_id: int) -> bool:
        """Check if a write can be issued to a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index

        Returns:
            True if write can be issued
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)
        return bsm.can_write()

    def write_bank(self, channel_id: int, bank_id: int) -> bool:
        """Issue a write to a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index

        Returns:
            True if write started successfully
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)
        success = bsm.write()

        if success:
            ctx = self._channels[channel_id]
            ctx.last_wr_cycle = ctx.local_cycle

            # Update timing context
            self.issue_timed_command(channel_id, 'WR')

        return success

    def complete_bank_read(self, channel_id: int, bank_id: int):
        """Complete a read operation on a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index
        """
        if channel_id in self._bank_state_machines and \
           bank_id in self._bank_state_machines[channel_id]:
            self._bank_state_machines[channel_id][bank_id].complete_read()

    def complete_bank_write(self, channel_id: int, bank_id: int):
        """Complete a write operation on a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index
        """
        if channel_id in self._bank_state_machines and \
           bank_id in self._bank_state_machines[channel_id]:
            self._bank_state_machines[channel_id][bank_id].complete_write()

    def refresh_bank(self, channel_id: int, bank_id: int) -> bool:
        """Refresh a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index

        Returns:
            True if refresh successful
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        bsm = self._bank_state_machines[channel_id][bank_id]
        bsm.set_time(self._global_cycle)
        success = bsm.refresh()

        if success:
            ctx = self._channels[channel_id]
            ctx.state = ChannelState.MAINTENANCE

            # Update timing context
            self.issue_timed_command(channel_id, 'REF')

        return success

    def complete_bank_refresh(self, channel_id: int, bank_id: int):
        """Complete a refresh operation on a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index
        """
        if channel_id in self._bank_state_machines and \
           bank_id in self._bank_state_machines[channel_id]:
            self._bank_state_machines[channel_id][bank_id].complete_refresh()
            ctx = self._channels[channel_id]
            if ctx.state == ChannelState.MAINTENANCE:
                ctx.state = ChannelState.IDLE

    def is_row_hit(self, channel_id: int, bank_id: int, row: int) -> bool:
        """Check if a row is currently open in a bank

        Args:
            channel_id: Channel index
            bank_id: Bank index
            row: Row address to check

        Returns:
            True if row is open (row hit)
        """
        if channel_id not in self._bank_state_machines:
            return False
        if bank_id not in self._bank_state_machines[channel_id]:
            return False

        return self._bank_state_machines[channel_id][bank_id].is_row_hit(row)

    # ==================== DFI Interface ====================

    def submit_dfi_command(self, command: DFICommand, address: int, bank: int,
                          channel: int, pseudo_channel: int = 0,
                          wrdata_en: bool = False, rddata_en: bool = False,
                          priority: int = 0) -> bool:
        """Submit a command through the DFI interface

        Args:
            command: DFI command type
            address: Memory address
            bank: Bank index
            channel: Channel index (0-31)
            pseudo_channel: Pseudo-channel index (0-1)
            wrdata_en: Write data enable
            rddata_en: Read data enable
            priority: Command priority

        Returns:
            True if command submitted successfully
        """
        request = DFIRequest(
            command=command,
            address=address,
            bank=bank,
            pseudo_channel=pseudo_channel,
            channel=channel,
            wrdata_en=wrdata_en,
            rddata_en=rddata_en,
            priority=priority,
            timestamp=self._global_cycle
        )

        success = self.dfi.queue_request(request)
        if success:
            self._dfi_commands_sent += 1
        return success

    def submit_dfi_act(self, channel: int, bank: int, row: int,
                       priority: int = 0) -> bool:
        """Submit ACTIVATE command through DFI

        Args:
            channel: Channel index
            bank: Bank index
            row: Row address
            priority: Command priority

        Returns:
            True if command submitted
        """
        return self.submit_dfi_command(
            command=DFICommand.ACT,
            address=row,
            bank=bank,
            channel=channel,
            priority=priority
        )

    def submit_dfi_pre(self, channel: int, bank: int,
                        priority: int = 0) -> bool:
        """Submit PRECHARGE command through DFI

        Args:
            channel: Channel index
            bank: Bank index
            priority: Command priority

        Returns:
            True if command submitted
        """
        return self.submit_dfi_command(
            command=DFICommand.PRE,
            address=0,
            bank=bank,
            channel=channel,
            priority=priority
        )

    def submit_dfi_read(self, channel: int, bank: int, column: int,
                        pseudo_channel: int = 0, priority: int = 0) -> bool:
        """Submit READ command through DFI

        Args:
            channel: Channel index
            bank: Bank index
            column: Column address
            pseudo_channel: Pseudo-channel index
            priority: Command priority

        Returns:
            True if command submitted
        """
        return self.submit_dfi_command(
            command=DFICommand.RD,
            address=column,
            bank=bank,
            channel=channel,
            pseudo_channel=pseudo_channel,
            rddata_en=True,
            priority=priority
        )

    def submit_dfi_write(self, channel: int, bank: int, column: int,
                         pseudo_channel: int = 0, priority: int = 0) -> bool:
        """Submit WRITE command through DFI

        Args:
            channel: Channel index
            bank: Bank index
            column: Column address
            pseudo_channel: Pseudo-channel index
            priority: Command priority

        Returns:
            True if command submitted
        """
        return self.submit_dfi_command(
            command=DFICommand.WR,
            address=column,
            bank=bank,
            channel=channel,
            pseudo_channel=pseudo_channel,
            wrdata_en=True,
            priority=priority
        )

    def submit_dfi_refresh(self, channel: int, priority: int = 0) -> bool:
        """Submit REFRESH command through DFI

        Args:
            channel: Channel index
            priority: Command priority

        Returns:
            True if command submitted
        """
        return self.submit_dfi_command(
            command=DFICommand.REFab,
            address=0,
            bank=0,
            channel=channel,
            priority=priority
        )

    def get_next_dfi_request(self) -> Optional[DFIRequest]:
        """Get next request from DFI queue

        Returns:
            Next DFIRequest or None
        """
        return self.dfi.get_next_request()

    def peek_dfi_request(self) -> Optional[DFIRequest]:
        """Peek at next request without removing

        Returns:
            Next DFIRequest or None
        """
        return self.dfi.peek_request()

    @property
    def dfi_pending_count(self) -> int:
        """Number of pending DFI requests"""
        return self.dfi.pending_request_count

    @property
    def dfi_is_ready(self) -> bool:
        """Check if DFI interface is ready"""
        return self.dfi.is_ready()

    def get_dfi_signals(self) -> Dict:
        """Get current DFI signal states

        Returns:
            Dictionary with DFI signal states
        """
        return self.dfi.get_dfi_signals()

    # ==================== Command Buffer ====================

    def enqueue_command(
        self,
        command: str,
        channel: int,
        address: int,
        priority: int = 0,
        data: Optional[int] = None,
        **kwargs,
    ) -> int:
        """Add a command to the internal command buffer

        Args:
            command: Command name (ACT, PRE, RD, WR, REF, MRS)
            channel: Target channel
            address: Memory address
            priority: Command priority
            data: Optional data payload
            **kwargs: Additional metadata (bank, row, column, etc.)

        Returns:
            Command ID if successful, -1 if buffer full
        """
        return self.command_buffer.enqueue(
            command=command,
            channel=channel,
            address=address,
            priority=priority,
            data=data,
            enqueued_cycle=self._global_cycle,
            **kwargs,
        )

    def dequeue_command(self) -> Optional[ScheduledCommand]:
        """Remove and return next command from buffer

        Returns:
            Next ScheduledCommand or None
        """
        return self.command_buffer.dequeue()

    def peek_command(self) -> Optional[ScheduledCommand]:
        """View next command without removing

        Returns:
            Next ScheduledCommand or None
        """
        return self.command_buffer.peek()

    def peek_channel_commands(self, channel: int) -> List[ScheduledCommand]:
        """Get all commands for a specific channel

        Args:
            channel: Channel to query

        Returns:
            List of ScheduledCommand
        """
        return self.command_buffer.peek_channel(channel)

    def get_channel_queue_depth(self, channel: int) -> int:
        """Get number of pending commands for a channel

        Args:
            channel: Channel to query

        Returns:
            Number of pending commands
        """
        return self.command_buffer.get_channel_queue_depth(channel)

    @property
    def command_buffer_size(self) -> int:
        """Current command buffer size"""
        return self.command_buffer.size

    @property
    def command_buffer_full(self) -> bool:
        """Check if command buffer is full"""
        return self.command_buffer.is_full

    def get_command_buffer_stats(self) -> Dict:
        """Get command buffer statistics

        Returns:
            Dictionary with buffer stats
        """
        return self.command_buffer.get_stats()

    # ==================== Command Processing ====================

    def process_command(
        self,
        channel_id: int,
        command: str,
        address: int,
        data: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Process command on a channel

        Args:
            channel_id: Target channel (0-31)
            command: Command type ('ACT', 'PRE', 'RD', 'WR', 'REF', etc.)
            address: Address for command
            data: Optional data for write commands

        Returns:
            Tuple of (success, error_message)
        """
        if not 0 <= channel_id < self.config.num_channels:
            return False, f"Invalid channel {channel_id}"

        ctx = self._channels[channel_id]
        self._total_commands += 1

        # Check channel state
        if ctx.state == ChannelState.ERROR:
            return False, f"Channel {channel_id} in error state"

        # Check timing constraints
        can_issue, reason = self.can_issue_timed_command(channel_id, command)
        if not can_issue:
            return False, reason or "Timing violation"

        # Route to command handler
        handlers = {
            'ACT': self._handle_activate,
            'PRE': self._handle_precharge,
            'RD': self._handle_read,
            'WR': self._handle_write,
            'REF': self._handle_refresh,
            'MRS': self._handle_mrs,
        }

        handler = handlers.get(command)
        if handler:
            result = handler(ctx, address, data)
            if result[0]:
                # Update timing
                self.issue_timed_command(channel_id, command, address)
            return result

        return False, f"Unknown command: {command}"

    def _handle_activate(
        self,
        ctx: ChannelContext,
        address: int,
        data: Optional[int],
    ) -> Tuple[bool, str]:
        """Handle ACTIVATE command"""
        # Check timing (tRC from spec)
        if ctx.last_act_cycle >= 0:
            cycles_since_act = ctx.local_cycle - ctx.last_act_cycle
            if cycles_since_act < self.spec.nRC:
                return False, f"tRC violation: {cycles_since_act} < {self.spec.nRC}"

        ctx.last_act_cycle = ctx.local_cycle
        ctx.state = ChannelState.ACTIVE
        ctx.open_row = address & 0xFFFF  # Extract row from address

        return True, ""

    def _handle_precharge(
        self,
        ctx: ChannelContext,
        address: int,
        data: Optional[int],
    ) -> Tuple[bool, str]:
        """Handle PRECHARGE command"""
        if ctx.last_rd_cycle >= 0:
            cycles_since_rd = ctx.local_cycle - ctx.last_rd_cycle
            if cycles_since_rd < self.spec.nRTPS:
                return False, f"tRTPS violation"

        ctx.state = ChannelState.IDLE
        ctx.open_row = None

        return True, ""

    def _handle_read(
        self,
        ctx: ChannelContext,
        address: int,
        data: Optional[int],
    ) -> Tuple[bool, str]:
        """Handle READ command"""
        if ctx.state != ChannelState.ACTIVE:
            return False, "Bank not active"

        # Check timing from activation
        if ctx.last_act_cycle >= 0:
            cycles_since_act = ctx.local_cycle - ctx.last_act_cycle
            if cycles_since_act < self.spec.nRCDRD:
                return False, f"tRCD_RD violation"

        # Check previous command
        if ctx.last_rd_cycle >= 0 or ctx.last_wr_cycle >= 0:
            last_cmd_cycle = max(ctx.last_rd_cycle, ctx.last_wr_cycle)
            cycles_since_last = ctx.local_cycle - last_cmd_cycle
            if cycles_since_last < self.spec.nCCDS:
                return False, f"tCCD violation"

        ctx.last_rd_cycle = ctx.local_cycle

        # Apply lane repair mapping if needed
        # (lane_repair handles this transparently)

        return True, ""

    def _handle_write(
        self,
        ctx: ChannelContext,
        address: int,
        data: Optional[int],
    ) -> Tuple[bool, str]:
        """Handle WRITE command"""
        if ctx.state != ChannelState.ACTIVE:
            return False, "Bank not active"

        if data is None:
            return False, "Write data required"

        # Check timing
        if ctx.last_act_cycle >= 0:
            cycles_since_act = ctx.local_cycle - ctx.last_act_cycle
            if cycles_since_act < self.spec.nRCDWR:
                return False, f"tRCD_WR violation"

        # Apply ECC encoding
        if self.config.ecc_enabled:
            encoded = self.data_integrity.encode_data(data)
            data = encoded['data']

        # Apply lane repair mapping
        if self.lane_repair.is_lane_remapped(ctx.channel_id, 0):
            # Data will be transparently routed through spare lanes
            pass

        ctx.last_wr_cycle = ctx.local_cycle

        return True, ""

    def _handle_refresh(
        self,
        ctx: ChannelContext,
        address: int,
        data: Optional[int],
    ) -> Tuple[bool, str]:
        """Handle REFRESH command"""
        ctx.state = ChannelState.MAINTENANCE

        # Refresh timing handled by spec
        return True, ""

    def _handle_mrs(
        self,
        ctx: ChannelContext,
        address: int,
        data: Optional[int],
    ) -> Tuple[bool, str]:
        """Handle MODE REGISTER SET command"""
        # MRS timing
        return True, ""

    # ==================== Channel State ====================

    def get_channel_state(self, channel_id: int) -> Optional[Dict]:
        """Get state for a specific channel

        Args:
            channel_id: Channel to query

        Returns:
            Dictionary with channel state or None
        """
        if not 0 <= channel_id < self.config.num_channels:
            return None

        ctx = self._channels[channel_id]
        timing = self._timing_contexts[channel_id]

        return {
            'channel_id': channel_id,
            'state': ctx.state.value,
            'local_cycle': ctx.local_cycle,
            'open_row': ctx.open_row,
            'training_passed': ctx.training_passed,
            'repair_status': ctx.repair_status.value,
            'error_count': ctx.error_count,
            'calibrated': self.calibration_manager.is_channel_calibrated(channel_id),
            'timing': {
                'last_act': ctx.last_act_cycle,
                'last_rd': ctx.last_rd_cycle,
                'last_wr': ctx.last_wr_cycle,
                'pll_locked': timing.pll_locked,
                'dll_locked': timing.dll_locked,
            },
        }

    def get_all_channel_states(self) -> List[Dict]:
        """Get state for all channels

        Returns:
            List of channel state dictionaries
        """
        return [self.get_channel_state(ch) for ch in range(self.config.num_channels)]

    # ==================== Statistics ====================

    def get_stats(self) -> Dict:
        """Get Logic Base Die statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'global_cycle': self._global_cycle,
            'initialized': self._initialized,
            'training_complete': self._training_complete,
            'ready': self.is_ready,
            'total_commands': self._total_commands,
            'total_errors': self._total_errors,
            'pam3_enabled': self.config.pam3_enabled,
            'pam3_stats': self.get_pam3_stats(),
            'ecc_enabled': self.config.ecc_enabled,
            'crc_enabled': self.config.crc_enabled,
            'channels_ready': sum(1 for ctx in self._channels if ctx.training_passed),
            'channels_total': self.config.num_channels,
            'channels_calibrated': sum(
                1 for ch in range(self.config.num_channels)
                if self.calibration_manager.is_channel_calibrated(ch)
            ),
            'command_buffer': self.command_buffer.get_stats(),
        }

    def get_calibration_data(self, channel_id: Optional[int] = None) -> Dict:
        """Get calibration data for channel(s)

        Args:
            channel_id: Specific channel or None for all

        Returns:
            Calibration data dictionary
        """
        if channel_id is not None:
            return self.calibration_manager.export_calibration(channel_id)

        return {
            f'ch{ch}': self.calibration_manager.export_calibration(ch)
            for ch in range(self.config.num_channels)
        }

    def get_lane_repair_stats(self) -> Dict:
        """Get lane repair statistics

        Returns:
            Lane repair statistics
        """
        return self.lane_repair.get_stats()

    # ==================== Utility Methods ====================

    def wait_for_ready(self, max_cycles: int = 100000) -> bool:
        """Wait for Logic Base Die to be ready

        Args:
            max_cycles: Maximum cycles to wait

        Returns:
            True if ready, False if timeout
        """
        for _ in range(max_cycles):
            if self.is_ready:
                return True
            self.tick()
        return False

    def reset(self):
        """Reset Logic Base Die to initial state

        Resets all state machines, queues, and statistics.
        Preserves configuration.
        """
        # Reset global state
        self._global_cycle = 0
        self._initialized = False
        self._training_complete = False

        # Reset DFI interface
        self.dfi.reset()

        # Reset command buffer
        self.command_buffer.clear()

        # Reset PAM3 codec LFSR
        if self.pam3_codec:
            self.pam3_codec.reset_lfsr()

        # Reset bank state machines
        timing = HBM3Timing()
        total_banks = self.config.banks_per_channel * self.config.pseudo_channels_per_channel
        for ch in range(self.config.num_channels):
            for bank_id in range(total_banks):
                self._bank_state_machines[ch][bank_id] = BankStateMachine(
                    bank_id=bank_id,
                    timing=timing
                )

        # Reset channel contexts
        for ctx, timing in zip(self._channels, self._timing_contexts):
            ctx.state = ChannelState.IDLE
            ctx.local_cycle = 0
            ctx.last_act_cycle = -1
            ctx.last_pre_cycle = -1
            ctx.last_rd_cycle = -1
            ctx.last_wr_cycle = -1
            ctx.open_row = None
            ctx.training_passed = False
            ctx.calibration_data = {}
            ctx.error_count = 0
            ctx.last_error = None
            ctx.bank_states = {}
            ctx.pam3_symbol_buffer.clear()
            ctx.pam3_decode_errors = 0

            # Reset timing context
            timing.cycle_counter = 0
            timing.last_act_cycle = -1
            timing.last_pre_cycle = -1
            timing.last_rd_cycle = -1
            timing.last_wr_cycle = -1
            timing.last_ref_cycle = -1
            timing.open_row = None
            timing.open_bank = None
            timing.act_count_4cycle_window = 0
            timing.last_4act_window_start = 0
            timing.pll_locked = False
            timing.dll_locked = False
            timing.calibrated = False
            timing.training_passed = False

        # Reset statistics
        self._total_commands = 0
        self._total_errors = 0
        self._dfi_commands_sent = 0
        self._dfi_commands_completed = 0
        self._pam3_encode_count = 0
        self._pam3_decode_count = 0

    def get_status(self) -> Dict:
        """Get comprehensive status of Logic Base Die

        Returns:
            Dictionary with complete status information
        """
        return {
            'cycle': self._global_cycle,
            'initialized': self._initialized,
            'training_complete': self._training_complete,
            'ready': self.is_ready,
            'dfi': {
                'lp_state': self.dfi.lp_state.value,
                'frequency_mhz': self.dfi.frequency_mhz,
                'pending_requests': self.dfi_pending_count,
                'ready': self.dfi_is_ready,
            },
            'command_buffer': {
                'size': self.command_buffer_size,
                'full': self.command_buffer_full,
                'stats': self.command_buffer.get_stats(),
            },
            'channels': {
                'total': self.config.num_channels,
                'ready': sum(1 for ctx in self._channels if ctx.training_passed),
                'calibrated': sum(
                    1 for ch in range(self.config.num_channels)
                    if self.calibration_manager.is_channel_calibrated(ch)
                ),
            },
            'calibration': self.get_calibration_status(),
            'pam3': self.get_pam3_stats(),
            'statistics': self.get_stats(),
        }
