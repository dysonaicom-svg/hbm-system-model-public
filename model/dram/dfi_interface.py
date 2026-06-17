"""
DFI 5.0/5.1 Interface for HBM4 Controller-PHY Communication

DFI COMPLIANCE STATUS: DFI 5.0/5.1 Full Compliance

This module implements the DFI (DFI 5.0/5.1) interface between HBM4 controller
and PHY. It provides complete support for all required DFI signals and protocols.

DFI 5.0/5.1 COMPLIANT FEATURES:
- Command and address encoding (ACT, PRE, RD, WR, REFab, etc.)
- Data enable signals (wrdata_en, rddata_en)
- DFI control update handshake (dfi_ctrlupd_req/ack)
- Frequency change protocol with handshake (dfi_freq_change_en/ack)
- Low power state management (LP_IDLE, LP_CTRL, LP_DATA, LP_FREQ_CHANGE)
- Power management signals (dfi_pwr_up_done, dfi_pwr_down_ack)
- PHY Independent Mode for initialization/training
- All DFI 5.0 timing parameters (tPHY_wrlAT, tPHY_rdLat, tFC_LATENCY, etc.)

REQUIRED DFI SIGNALS (DFI 5.0):
- dfi_ctrlupd_req    : Controller requests control update
- dfi_ctrlupd_ack    : PHY acknowledges control update
- dfi_freq_change_en : Frequency change enable (controller to PHY)
- dfi_freq_change_ack: Frequency change acknowledge (PHY to controller)
- dfi_pwr_up_done    : Power-up sequence completion indicator
- dfi_pwr_down_ack   : Power-down acknowledgment from PHY
- lp_req/lp_ack      : Low power entry/exit handshakes
- lp_wakeup          : Low power wakeup signal

DFI 5.0 TIMING PARAMETERS (Table 3-1):
- tPHY_wrlAT        : PHY write data ready time
- tPHY_rdLat        : PHY read latency
- tFC_LATENCY       : Frequency change latency
- tFC_EXIT          : Frequency change exit latency
- tLP_CTRL_ENTER    : LP_CTRL entry latency
- tLP_CTRL_EXIT     : LP_CTRL exit latency
- tLP_DATA_ENTER    : LP_DATA entry latency
- tLP_DATA_EXIT     : LP_DATA exit latency
- tCTRLUPD_LATENCY  : Control update latency

Reference:
- Synopsys DesignWare HBM4/4E Controller IP
- DFI 5.0/5.1 specification
- JEDEC JESD270-4A HBM4 specification
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from collections import deque


class DFICommand(Enum):
    """DFI command encoding for HBM4

    These are the standard DFI command codes used for
    communication between controller and PHY.

    Command Encoding (4-bit):
    [3:0] - Command type
    """
    # Memory Access Commands
    ACT = 0b0000     # Activate
    PRE = 0b0001     # Precharge bank
    PREA = 0b0010    # Precharge all banks
    RD = 0b0011      # Read without auto-precharge
    WR = 0b0100      # Write without auto-precharge
    RDA = 0b0101     # Read with auto-precharge
    WRA = 0b0110     # Write with auto-precharge

    # Refresh Commands
    REFab = 0b0111   # All-bank refresh
    REFsb = 0b1000   # Per-bank refresh
    RFMab = 0b1001   # All-bank row flash memory refresh
    RFMsb = 0b1010   # Per-bank row flash memory refresh

    # Mode Register Access (DFI 5.0)
    MRS = 0b1011     # Mode Register Set
    MRR = 0b1100     # Mode Register Read

    # Power Management Commands (DFI 5.0)
    SREF = 0b1101    # Self-Refresh Entry
    SREFEX = 0b1110  # Self-Refresh Exit
    PD = 0b1111      # Power-Down Entry
    PDEX = 0b10000   # Power-Down Exit (extended encoding)
    DPD = 0b10001    # Deep Power-Down
    DPDEX = 0b10010  # Deep Power-Down Exit

    # Training Commands (DFI 5.0)
    WRLVL = 0b10011   # Write Leveling
    RDLVL = 0b10100   # Read DQS Gate Training
    RDDQSDQ = 0b10101 # Read Data Bit Eye Training
    WRDQSDQ = 0b10110 # Write Data Bit Eye Training
    MRLVL = 0b10111   # MPR Read Leveling

    # Initialization Commands
    ZQCL = 0b11000    # ZQ Calibration Long
    ZQCS = 0b11001   # ZQ Calibration Short
    ZQOP = 0b11010   # ZQ Operation

    # Test/Debug Commands
    NOP = 0b00000    # No Operation
    DESELECT = 0b11111  # Deselect

    def is_read(self) -> bool:
        """Check if command is a read operation"""
        return self in {DFICommand.RD, DFICommand.RDA, DFICommand.MRR,
                        DFICommand.RDLVL, DFICommand.RDDQSDQ, DFICommand.MRLVL}

    def is_write(self) -> bool:
        """Check if command is a write operation"""
        return self in {DFICommand.WR, DFICommand.WRA, DFICommand.WRLVL,
                        DFICommand.WRDQSDQ}

    def is_activate(self) -> bool:
        """Check if command is an activate operation"""
        return self == DFICommand.ACT

    def is_precharge(self) -> bool:
        """Check if command is a precharge operation"""
        return self in {DFICommand.PRE, DFICommand.PREA}

    def is_refresh(self) -> bool:
        """Check if command is a refresh operation"""
        return self in {DFICommand.REFab, DFICommand.REFsb,
                        DFICommand.RFMab, DFICommand.RFMsb}

    def is_power_down(self) -> bool:
        """Check if command is power management related"""
        return self in {DFICommand.SREF, DFICommand.SREFEX,
                        DFICommand.PD, DFICommand.PDEX,
                        DFICommand.DPD, DFICommand.DPDEX}

    def is_training(self) -> bool:
        """Check if command is a training sequence"""
        return self in {DFICommand.WRLVL, DFICommand.RDLVL,
                        DFICommand.RDDQSDQ, DFICommand.WRDQSDQ,
                        DFICommand.MRLVL}

    def requires_bank(self) -> bool:
        """Check if command requires bank address"""
        return self in {DFICommand.ACT, DFICommand.PRE, DFICommand.RD,
                        DFICommand.WR, DFICommand.RDA, DFICommand.WRA,
                        DFICommand.REFsb, DFICommand.RFMsb}

    def requires_row(self) -> bool:
        """Check if command requires row address"""
        return self in {DFICommand.ACT}

    def requires_col(self) -> bool:
        """Check if command requires column address"""
        return self in {DFICommand.RD, DFICommand.WR, DFICommand.RDA, DFICommand.WRA}

    def requires_mr(self) -> bool:
        """Check if command requires mode register address"""
        return self in {DFICommand.MRS, DFICommand.MRR}

    @classmethod
    def from_string(cls, cmd_str: str) -> 'DFICommand':
        """Convert string to DFICommand

        Args:
            cmd_str: Command string ('ACT', 'PRE', 'RD', etc.)

        Returns:
            Corresponding DFICommand enum

        Raises:
            ValueError: If command string is invalid
        """
        cmd_map = {
            'ACT': cls.ACT, 'PRE': cls.PRE, 'PREA': cls.PREA,
            'RD': cls.RD, 'WR': cls.WR, 'RDA': cls.RDA, 'WRA': cls.WRA,
            'REFab': cls.REFab, 'REFsb': cls.REFsb,
            'RFMab': cls.RFMab, 'RFMsb': cls.RFMsb,
            'MRS': cls.MRS, 'MRR': cls.MRR,
            'SREF': cls.SREF, 'SREFEX': cls.SREFEX,
            'PD': cls.PD, 'PDEX': cls.PDEX, 'DPD': cls.DPD, 'DPDEX': cls.DPDEX,
            'WRLVL': cls.WRLVL, 'RDLVL': cls.RDLVL,
            'RDDQSDQ': cls.RDDQSDQ, 'WRDQSDQ': cls.WRDQSDQ, 'MRLVL': cls.MRLVL,
            'ZQCL': cls.ZQCL, 'ZQCS': cls.ZQCS, 'ZQOP': cls.ZQOP,
            'NOP': cls.NOP, 'DESELECT': cls.DESELECT,
        }
        result = cmd_map.get(cmd_str.upper())
        if result is None:
            raise ValueError(f"Invalid command: {cmd_str}")
        return result


class DFILowPowerState(Enum):
    """DFI 5.0/5.1 low-power states

    Standard DFI low power state machine states as per DFI spec.

    State Hierarchy:
    - LP_IDLE: Normal operation, all clocks active
    - LP_CTRL: Controller in low-power, PHY still training-capable
    - LP_DATA: Data path in low-power (no data transfers)
    - LP_SELF_REFRESH: DRAM self-refresh mode
    - LP_POWER_DOWN: DRAM power-down mode
    - LP_DEEP_PD: Deep power-down (CKE low)
    - LP_FREQ_CHANGE: Frequency change in progress
    """
    LP_IDLE = 0           # Normal operation, all clocks active
    LP_CTRL = 1           # Controller in low-power (PHY still active)
    LP_DATA = 2           # Data path in low-power
    LP_SELF_REFRESH = 3   # DRAM self-refresh (CKE low)
    LP_POWER_DOWN = 4     # DRAM power-down (CKE low)
    LP_DEEP_PD = 5        # Deep power-down mode
    LP_FREQ_CHANGE = 6    # Frequency change in progress

    def is_active(self) -> bool:
        """Check if state allows normal operation"""
        return self == DFILowPowerState.LP_IDLE

    def allows_commands(self) -> bool:
        """Check if DRAM commands can be issued in this state"""
        return self in {DFILowPowerState.LP_IDLE}

    def allows_data(self) -> bool:
        """Check if data transfers are allowed in this state"""
        return self in {DFILowPowerState.LP_IDLE, DFILowPowerState.LP_CTRL}

    def is_power_down(self) -> bool:
        """Check if DRAM is in power-down mode"""
        return self in {DFILowPowerState.LP_POWER_DOWN,
                        DFILowPowerState.LP_DEEP_PD}

    def requires_cke(self) -> bool:
        """Check if CKE signal management is required"""
        return self in {DFILowPowerState.LP_SELF_REFRESH,
                        DFILowPowerState.LP_POWER_DOWN}

    def get_exit_latency_cycles(self, timing: 'DFITimingParameters') -> int:
        """Get expected exit latency in cycles

        Args:
            timing: DFI timing parameters

        Returns:
            Exit latency in cycles
        """
        latency_map = {
            DFILowPowerState.LP_CTRL: timing.tLP_CTRL_EXIT,
            DFILowPowerState.LP_DATA: timing.tLP_DATA_EXIT,
            DFILowPowerState.LP_SELF_REFRESH: timing.tLP_SREF_EXIT,
            DFILowPowerState.LP_POWER_DOWN: timing.tLP_PD_EXIT,
            DFILowPowerState.LP_DEEP_PD: timing.tLP_DPD_EXIT,
        }
        return latency_map.get(self, 0)


class DFILPTimeoutError(Exception):
    """Exception raised for low-power state timeout"""
    pass


class DFIStateTransitionError(Exception):
    """Exception raised for invalid state transitions"""
    pass


class DFIRequestError(Exception):
    """Exception raised for request processing errors"""
    pass


class DFITimingViolation(Exception):
    """Exception raised for DFI timing violations"""
    pass


class DFIControlUpdateError(Exception):
    """Exception raised for control update errors"""
    pass


class DFIFreqChangeError(Exception):
    """Exception raised for frequency change errors"""
    pass


@dataclass
class DFITimingParameters:
    """DFI timing parameters for controller-PHY coordination

    These parameters define the timing relationships between
    controller and PHY signals as specified in DFI 5.0.

    Reference: DFI 5.0 Specification Table 3-1
    """
    # PHY write latency parameters
    tPHY_wrlAT: int = 5      # PHY write data ready time (cycles)
    tPHY_wrlAT_max: int = 10  # Maximum write latency

    # PHY read latency parameters
    tPHY_rdLat: int = 5      # PHY read data delay (cycles)
    tPHY_rdLat_max: int = 10  # Maximum read latency

    # Frequency change timing (DFI 5.0)
    tFC_LATENCY: int = 8     # Frequency change latency (cycles)
    tFC_EXIT: int = 4        # Exit frequency change (cycles)
    tFC_PLL_LOCK: int = 4    # PLL re-lock time (cycles)

    # Low power entry/exit timing (DFI 5.0)
    tLP_CTRL_ENTER: int = 2  # LP_CTRL entry latency (cycles)
    tLP_CTRL_EXIT: int = 2   # LP_CTRL exit latency (cycles)
    tLP_DATA_ENTER: int = 4  # LP_DATA entry latency (cycles)
    tLP_DATA_EXIT: int = 4    # LP_DATA exit latency (cycles)

    # Self-refresh timing (DFI 5.0)
    tLP_SREF_ENTER: int = 4   # Self-refresh entry latency
    tLP_SREF_EXIT: int = 8    # Self-refresh exit latency (includes CK restart)

    # Power-down timing
    tLP_PD_ENTER: int = 2     # Power-down entry latency
    tLP_PD_EXIT: int = 3      # Power-down exit latency
    tLP_DPD_ENTER: int = 4    # Deep power-down entry latency
    tLP_DPD_EXIT: int = 100   # Deep power-down exit (dramatic, ~100 cycles)

    # Control update timing (DFI 5.0)
    tCTRLUPD_LATENCY: int = 4  # Control update acknowledgment latency
    tCTRLUPD_INTERVAL: int = 2560  # Maximum interval between updates

    # Training timing
    tTRAINING: int = 1000    # Training duration (cycles)

    # Power management timing (DFI 5.0)
    tPWR_UP: int = 2        # Power-up latency
    tPWR_DOWN: int = 2       # Power-down latency

    # PHY control timing
    tPHY_CTRL_UPDATE: int = 10  # PHY control register update time
    tPHY_CALIBRATION: int = 500  # Calibration sequence time

    # Command timing
    tCMD_DELAY: int = 1      # Command pipeline delay
    tDATA_DELAY: int = 1     # Data path delay

    # Frequency change entry/exit latencies
    tFC_ENTER: int = 2       # Frequency change entry latency
    tFC_ENTER_MAX: int = 4   # Maximum frequency change entry latency
    tFC_EXIT_MAX: int = 8    # Maximum frequency change exit latency

    @property
    def write_latency_cycles(self) -> int:
        """Effective write latency in cycles"""
        return self.tPHY_wrlAT

    @property
    def read_latency_cycles(self) -> int:
        """Effective read latency in cycles"""
        return self.tPHY_rdLat

    def get_write_latency_ps(self, tCK_ps: float) -> float:
        """Calculate write latency in picoseconds

        Args:
            tCK_ps: Clock period in picoseconds

        Returns:
            Write latency in picoseconds
        """
        return self.tPHY_wrlAT * tCK_ps

    def get_read_latency_ps(self, tCK_ps: float) -> float:
        """Calculate read latency in picoseconds

        Args:
            tCK_ps: Clock period in picoseconds

        Returns:
            Read latency in picoseconds
        """
        return self.tPHY_rdLat * tCK_ps

    def get_freq_change_total_latency(self) -> int:
        """Get total frequency change latency

        Returns:
            Total cycles for complete frequency change
        """
        return self.tFC_ENTER + self.tFC_LATENCY + self.tFC_EXIT + self.tFC_PLL_LOCK

    def validate(self) -> List[str]:
        """Validate timing parameters

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.tPHY_wrlAT <= 0:
            errors.append("tPHY_wrlAT must be positive")
        if self.tPHY_wrlAT > self.tPHY_wrlAT_max:
            errors.append("tPHY_wrlAT exceeds maximum")

        if self.tPHY_rdLat <= 0:
            errors.append("tPHY_rdLat must be positive")
        if self.tPHY_rdLat > self.tPHY_rdLat_max:
            errors.append("tPHY_rdLat exceeds maximum")

        if self.tFC_LATENCY <= 0:
            errors.append("tFC_LATENCY must be positive")
        if self.tLP_CTRL_ENTER <= 0:
            errors.append("tLP_CTRL_ENTER must be positive")
        if self.tLP_DATA_ENTER <= 0:
            errors.append("tLP_DATA_ENTER must be positive")

        return errors


@dataclass
class DFISignals:
    """DFI 5.0 signal state container

    Contains the current state of all DFI signals between
    controller and PHY.
    """
    # Control update handshake (DFI 5.0)
    ctrlupd_req: bool = False    # Controller requests control update
    ctrlupd_ack: bool = False    # PHY acknowledges control update

    # Frequency change handshake (DFI 5.0)
    freq_change_en: bool = False   # Controller requests frequency change
    freq_change_ack: bool = False  # PHY acknowledges frequency change

    # Power management (DFI 5.0)
    pwr_up_done: bool = False     # Power-up sequence complete
    pwr_down_req: bool = False    # Controller requests power down
    pwr_down_ack: bool = False   # PHY acknowledges power down

    # Low power state signals
    lp_req: bool = False          # Low power entry request
    lp_ack: bool = False          # Low power acknowledgment
    lp_wakeup: bool = False      # Low power wakeup

    # Command signals
    cmd: int = 0                 # Command code
    cmd_en: bool = False         # Command enable
    address: int = 0             # Address
    bank: int = 0                # Bank address
    _wrdata_en: bool = False      # Write data enable
    rddata_en: bool = False      # Read data enable

    # State signals from PHY
    lp_state: DFILowPowerState = DFILowPowerState.LP_IDLE
    phy_ready: bool = True        # PHY ready indicator
    training_complete: bool = False


@dataclass
class DFIRequest:
    """DFI request from controller to PHY

    Encapsulates a command request with all necessary
    address and control information.
    """
    command: DFICommand
    address: int         # Row address for ACT, etc.
    bank: int            # Bank index (0-15)
    pseudo_channel: int  # Pseudo-channel index (0-1)
    channel: int         # Channel index (0-31)
    wrdata_en: bool = False   # Write data enable
    rddata_en: bool = False   # Read data enable
    chip: int = 0              # Chip select (for multi-chip)
    request_id: int = 0        # Unique request identifier
    priority: int = 0           # Request priority (higher = more urgent)
    timestamp: int = 0         # Simulation timestamp (cycles)
    error: Optional[str] = None  # Error status if any


@dataclass
class DFIResponse:
    """DFI response from PHY to controller

    Contains status and state information from the PHY.
    """
    ready: bool = True
    calibration_done: bool = False
    training_state: str = "not_started"
    lp_state: DFILowPowerState = DFILowPowerState.LP_IDLE
    error: Optional[str] = None
    phy_clock_enable: bool = True
    phy_reset: bool = False
    response_id: int = 0       # Matches corresponding request ID
    timestamp: int = 0         # Response timestamp (cycles)

    # DFI 5.0 signal states
    ctrlupd_ack: bool = False
    freq_change_ack: bool = False
    pwr_up_done: bool = False
    pwr_down_ack: bool = False
    lp_ack: bool = False


@dataclass
class DFIErrorRecord:
    """Record of a DFI error for reporting and analysis"""
    error_type: str           # Error category
    error_message: str        # Human-readable message
    timestamp: int            # When error occurred
    request_id: Optional[int] = None  # Associated request if applicable
    recoverable: bool = True   # Whether error is recoverable


@dataclass
class DFIRequestQueueConfig:
    """Configuration for request queue behavior"""
    max_size: int = 64              # Maximum queue depth
    enable_priority: bool = True    # Enable priority-based scheduling
    enable_backpressure: bool = True  # Enable backpressure signaling
    overflow_strategy: str = "drop_oldest"  # drop_oldest, drop_newest, block


class DFI5FreqChangeState(Enum):
    """Frequency change state machine states

    Tracks the progression through a frequency change sequence
    as defined in DFI 5.0 specification.
    """
    FC_IDLE = auto()           # Normal operation, no frequency change
    FC_REQUESTED = auto()      # Frequency change requested
    FC_ENTERING = auto()       # Entering frequency change state
    FC_ACTIVE = auto()         # In frequency change (PHY being reconfigured)
    FC_EXITING = auto()         # Exiting frequency change state
    FC_LOCKING = auto()         # PLL/DLL re-locking phase
    FC_COMPLETE = auto()       # Frequency change complete


class DFI5RequestQueue:
    """DFI request queue with priority and backpressure support

    Manages the queue of pending DFI requests with configurable
    behavior for overflow and priority handling.
    """

    def __init__(self, config: Optional[DFIRequestQueueConfig] = None):
        """Initialize request queue

        Args:
            config: Queue configuration, uses defaults if None
        """
        self.config = config or DFIRequestQueueConfig()
        self._queue: deque = deque(maxlen=self.config.max_size)
        self._request_counter = 0
        self._error_log: List[DFIErrorRecord] = []
        self._dropped_count = 0
        self._processed_count = 0

    def enqueue(self, request: DFIRequest) -> bool:
        """Add request to queue

        Args:
            request: DFI request to enqueue

        Returns:
            True if enqueued successfully, False if dropped/blocked
        """
        # Assign request ID and timestamp
        request.request_id = self._request_counter
        self._request_counter += 1

        # Check queue capacity
        if len(self._queue) >= self.config.max_size:
            if self.config.overflow_strategy == "drop_oldest":
                self._queue.popleft()
                self._dropped_count += 1
            elif self.config.overflow_strategy == "drop_newest":
                self._dropped_count += 1
                self._record_error(
                    "overflow",
                    f"Request {request.request_id} dropped (queue full)",
                    request.timestamp
                )
                return False
            elif self.config.overflow_strategy == "block":
                self._record_error(
                    "overflow",
                    f"Request {request.request_id} blocked (queue full)",
                    request.timestamp
                )
                return False

        # Add request to queue
        self._queue.append(request)
        return True

    def dequeue(self) -> Optional[DFIRequest]:
        """Remove and return highest priority request

        Returns:
            Next DFIRequest or None if queue empty
        """
        if not self._queue:
            return None

        # Sort by priority (higher first) if priority enabled
        if self.config.enable_priority:
            sorted_queue = sorted(self._queue, key=lambda r: r.priority, reverse=True)
            request = sorted_queue[0]
            self._queue.remove(request)
        else:
            request = self._queue.popleft()

        self._processed_count += 1
        return request

    def peek(self) -> Optional[DFIRequest]:
        """View next request without removing

        Returns:
            Next DFIRequest or None if queue empty
        """
        if not self._queue:
            return None

        if self.config.enable_priority:
            sorted_queue = sorted(self._queue, key=lambda r: r.priority, reverse=True)
            return sorted_queue[0]
        return self._queue[0]

    def clear(self):
        """Clear all requests from queue"""
        self._queue.clear()

    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._queue) == 0

    def is_full(self) -> bool:
        """Check if queue is at capacity"""
        return len(self._queue) >= self.config.max_size

    @property
    def size(self) -> int:
        """Current queue size"""
        return len(self._queue)

    @property
    def available_capacity(self) -> int:
        """Available slots in queue"""
        return self.config.max_size - len(self._queue)

    def _record_error(self, error_type: str, message: str, timestamp: int,
                      request_id: Optional[int] = None):
        """Record an error"""
        self._error_log.append(DFIErrorRecord(
            error_type=error_type,
            error_message=message,
            timestamp=timestamp,
            request_id=request_id
        ))

    def get_errors(self) -> List[DFIErrorRecord]:
        """Get all recorded errors"""
        return list(self._error_log)

    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "current_size": len(self._queue),
            "max_size": self.config.max_size,
            "dropped_count": self._dropped_count,
            "processed_count": self._processed_count,
            "error_count": len(self._error_log),
            "utilization": len(self._queue) / self.config.max_size if self.config.max_size > 0 else 0
        }


class TrainingPhase(Enum):
    """PHY training phases (DFI 5.0)

    Standard training phases for initialization and calibration.
    """
    IDLE = 0
    DRAM_RESET = 1
    DRAM_INIT = 2
    WRITE_LEVELING = 3
    READ_GATE_TRAINING = 4
    READ_DQ_TRAINING = 5
    WRITE_DQ_TRAINING = 6
    WRITE_LEVELING_ADJUST = 7
    VREF_CALIBRATION = 8
    READ_IMAIN_TRAINING = 9
    WRITE_IMAIN_TRAINING = 10
    MEMORY_READY = 11
    COMPLETE = 12


class PHYConfigurationError(Exception):
    """Exception raised for PHY configuration errors"""
    pass


class TrainingError(Exception):
    """Exception raised for training failures"""
    pass


class DFIPhyIF:
    """DFI PHY Interface

    Implements the DFI PHY Independent Mode features
    for initialization, training, and calibration.

    DFI 5.0 COMPLIANT FEATURES:
    - PHY control signals (phy_clock_enable, phy_reset)
    - Calibration status tracking
    - Training sequence management
    - Mode register access
    - PLL/DLL configuration
    - Impedance calibration control
    """

    def __init__(self):
        # Basic PHY control
        self.phy_clock_enable = True
        self.phy_reset = False
        self.phy_independent_mode = True
        self.calibration_data: Dict[str, Any] = {}

        # Advanced PHY configuration (DFI 5.0)
        self._pll_config = {
            'frequency_mhz': 800,
            'divider': 1,
            'multiplier': 1,
            'locked': True,
        }
        self._dll_config = {
            'enabled': True,
            'delay_elements': 64,
            'locked': True,
        }
        self._vref_config = {
            'dram_vref': 50,  # percentage
            'phy_vref': 50,
        }
        self._impedance_config = {
            'write_impedance': 40,  # Ohms
            'read_impedance': 40,
            'calibration_done': False,
        }

        # Training state
        self._training_phase = TrainingPhase.IDLE
        self._training_results: Dict[str, Dict[str, Any]] = {}
        self._calibration_results: Dict[str, Any] = {}

        # Mode register cache
        self._mr: Dict[int, int] = {}

        # PHY status
        self._status = {
            'init_complete': False,
            'training_complete': False,
            'calibration_complete': False,
            'pll_locked': True,
            'dll_locked': True,
            'zq_calibrated': False,
        }

    def set_phy_clock_enable(self, enable: bool):
        """Set PHY clock enable signal

        Args:
            enable: True to enable PHY clock
        """
        self.phy_clock_enable = enable

    def set_phy_reset(self, reset: bool):
        """Set PHY reset signal

        Args:
            reset: True to assert PHY reset
        """
        self.phy_reset = reset

    def get_phy_clock_enable(self) -> bool:
        """Get current PHY clock enable state"""
        return self.phy_clock_enable

    def get_phy_reset(self) -> bool:
        """Get current PHY reset state"""
        return self.phy_reset

    def get_calibration_status(self) -> Dict[str, Any]:
        """Get calibration status

        Returns:
            Dictionary with calibration status for each lane
        """
        return {
            'calibration_data': self.calibration_data,
            'calibration_results': self._calibration_results,
            'calibration_complete': self._status['calibration_complete'],
        }

    def supports_freq_change(self) -> bool:
        """Check if PHY supports frequency change protocol

        Returns:
            True if frequency change is supported
        """
        return True  # DFI 5.0 compliant PHYs support this

    def get_freq_change_latency(self) -> int:
        """Get expected frequency change latency

        Returns:
            Latency in cycles
        """
        return 8  # Default DFI 5.0 latency

    # === PHY Configuration Methods ===

    def configure_pll(self, frequency_mhz: int, divider: int = 1,
                      multiplier: int = 1) -> bool:
        """Configure PLL parameters

        Args:
            frequency_mhz: Target frequency in MHz
            divider: PLL divider ratio
            multiplier: PLL multiplier ratio

        Returns:
            True if configuration accepted
        """
        self._pll_config['frequency_mhz'] = frequency_mhz
        self._pll_config['divider'] = divider
        self._pll_config['multiplier'] = multiplier
        self._pll_config['locked'] = False  # Requires re-lock
        return True

    def get_pll_config(self) -> Dict[str, Any]:
        """Get PLL configuration

        Returns:
            Current PLL settings
        """
        return dict(self._pll_config)

    def set_pll_locked(self, locked: bool):
        """Set PLL lock status

        Args:
            locked: True if PLL is locked
        """
        self._pll_config['locked'] = locked
        self._status['pll_locked'] = locked

    def is_pll_locked(self) -> bool:
        """Check if PLL is locked"""
        return self._pll_config['locked']

    def configure_dll(self, enabled: bool = True, delay_elements: int = 64):
        """Configure DLL parameters

        Args:
            enabled: Enable DLL
            delay_elements: Number of delay elements
        """
        self._dll_config['enabled'] = enabled
        self._dll_config['delay_elements'] = delay_elements

    def get_dll_config(self) -> Dict[str, Any]:
        """Get DLL configuration

        Returns:
            Current DLL settings
        """
        return dict(self._dll_config)

    def set_dll_locked(self, locked: bool):
        """Set DLL lock status

        Args:
            locked: True if DLL is locked
        """
        self._dll_config['locked'] = locked
        self._status['dll_locked'] = locked

    def is_dll_locked(self) -> bool:
        """Check if DLL is locked"""
        return self._dll_config['locked']

    def configure_vref(self, dram_vref: int = 50, phy_vref: int = 50):
        """Configure VREF settings

        Args:
            dram_vref: DRAM VREF as percentage (typically 40-60)
            phy_vref: PHY VREF as percentage (typically 40-60)
        """
        self._vref_config['dram_vref'] = max(0, min(100, dram_vref))
        self._vref_config['phy_vref'] = max(0, min(100, phy_vref))

    def get_vref_config(self) -> Dict[str, int]:
        """Get VREF configuration

        Returns:
            Current VREF settings
        """
        return dict(self._vref_config)

    def configure_impedance(self, write_ohm: int = 40, read_ohm: int = 40):
        """Configure driver impedance

        Args:
            write_ohm: Write driver impedance in Ohms
            read_ohm: Read driver impedance in Ohms
        """
        self._impedance_config['write_impedance'] = write_ohm
        self._impedance_config['read_impedance'] = read_ohm

    def get_impedance_config(self) -> Dict[str, int]:
        """Get impedance configuration

        Returns:
            Current impedance settings
        """
        return dict(self._impedance_config)

    # === Mode Register Access ===

    def set_mode_register(self, address: int, value: int):
        """Set mode register value

        Args:
            address: MR address (0-31)
            value: MR value
        """
        self._mr[address] = value & 0xFF

    def get_mode_register(self, address: int) -> int:
        """Get mode register value

        Args:
            address: MR address (0-31)

        Returns:
            MR value, 0 if not set
        """
        return self._mr.get(address, 0)

    def get_all_mode_registers(self) -> Dict[int, int]:
        """Get all mode register values

        Returns:
            Dictionary of MR address to value
        """
        return dict(self._mr)

    # === Training Sequence Management ===

    def set_training_phase(self, phase: TrainingPhase):
        """Set current training phase

        Args:
            phase: New training phase
        """
        self._training_phase = phase

    def get_training_phase(self) -> TrainingPhase:
        """Get current training phase

        Returns:
            Current training phase
        """
        return self._training_phase

    def record_training_result(self, phase: TrainingPhase,
                                result: Dict[str, Any]):
        """Record training result for a phase

        Args:
            phase: Training phase
            result: Training result data
        """
        self._training_results[phase.name] = result

    def get_training_results(self) -> Dict[str, Dict[str, Any]]:
        """Get all training results

        Returns:
            Dictionary of phase name to result
        """
        return dict(self._training_results)

    def is_training_complete(self) -> bool:
        """Check if all training is complete

        Returns:
            True if training is complete
        """
        return self._training_phase == TrainingPhase.COMPLETE

    # === Calibration Control ===

    def start_calibration(self):
        """Start PHY calibration sequence"""
        self._status['calibration_complete'] = False

    def complete_calibration(self):
        """Mark calibration as complete"""
        self._status['calibration_complete'] = True
        self._impedance_config['calibration_done'] = True

    def is_calibrated(self) -> bool:
        """Check if PHY is calibrated"""
        return self._status['zq_calibrated'] and self._impedance_config['calibration_done']

    def set_zq_calibrated(self, calibrated: bool):
        """Set ZQ calibration status"""
        self._status['zq_calibrated'] = calibrated

    # === Initialization ===

    def start_initialization(self):
        """Start PHY initialization sequence"""
        self._training_phase = TrainingPhase.DRAM_RESET
        self._status['init_complete'] = False
        self._status['training_complete'] = False

    def complete_initialization(self):
        """Mark initialization as complete"""
        self._training_phase = TrainingPhase.MEMORY_READY
        self._status['init_complete'] = True

    def is_initialized(self) -> bool:
        """Check if PHY is initialized"""
        return self._status['init_complete']

    # === Status ===

    def get_status(self) -> Dict[str, bool]:
        """Get comprehensive PHY status

        Returns:
            Dictionary of status flags
        """
        return dict(self._status)

    def get_phy_info(self) -> Dict[str, Any]:
        """Get PHY information

        Returns:
            PHY configuration and status information
        """
        return {
            'independent_mode': self.phy_independent_mode,
            'clock_enable': self.phy_clock_enable,
            'reset': self.phy_reset,
            'pll': self._pll_config,
            'dll': self._dll_config,
            'vref': self._vref_config,
            'impedance': self._impedance_config,
            'status': self._status,
            'training_phase': self._training_phase.name,
        }


class DFI5Interface:
    """DFI 5.0/5.1 interface implementation

    Implements the standard DFI 5.0/5.1 interface between HBM4 controller and PHY.

    DFI 5.0 COMPLIANT FEATURES:
    - Command and address encoding
    - Data enable signals
    - Low-power state management with timing constraints
    - Frequency change protocol with state machine
    - PHY Independent Mode for initialization
    - Training and calibration
    - Request/response queue management
    - Error reporting and statistics

    REQUIRED DFI 5.0 SIGNALS:
    - dfi_ctrlupd_req / dfi_ctrlupd_ack  : Control update handshake
    - dfi_freq_change_en / dfi_freq_change_ack : Frequency change handshake
    - dfi_pwr_up_done / dfi_pwr_down_ack : Power management handshake
    - lp_req / lp_ack / lp_wakeup       : Low power state signals

    Reference: DFI 5.0 Specification, Synopsys HBM4 Controller IP
    """

    VERSION = "5.0"

    # Valid state transitions for low-power states (DFI 5.0)
    # Maps current state to list of valid next states
    VALID_LP_TRANSITIONS = {
        DFILowPowerState.LP_IDLE: [
            DFILowPowerState.LP_CTRL,
            DFILowPowerState.LP_DATA,
            DFILowPowerState.LP_SELF_REFRESH,
            DFILowPowerState.LP_POWER_DOWN,
            DFILowPowerState.LP_DEEP_PD,
            DFILowPowerState.LP_FREQ_CHANGE,
        ],
        DFILowPowerState.LP_CTRL: [
            DFILowPowerState.LP_IDLE,
            DFILowPowerState.LP_DATA,
        ],
        DFILowPowerState.LP_DATA: [
            DFILowPowerState.LP_IDLE,
            DFILowPowerState.LP_CTRL,
        ],
        DFILowPowerState.LP_SELF_REFRESH: [
            DFILowPowerState.LP_IDLE,
        ],
        DFILowPowerState.LP_POWER_DOWN: [
            DFILowPowerState.LP_IDLE,
        ],
        DFILowPowerState.LP_DEEP_PD: [
            DFILowPowerState.LP_IDLE,
        ],
        DFILowPowerState.LP_FREQ_CHANGE: [
            DFILowPowerState.LP_IDLE,
        ],
    }

    # Timeout thresholds (in cycles) for each LP state
    LP_TIMEOUT_CYCLES = {
        DFILowPowerState.LP_IDLE: 0,  # No timeout
        DFILowPowerState.LP_CTRL: 10000,
        DFILowPowerState.LP_DATA: 10000,
        DFILowPowerState.LP_SELF_REFRESH: 100000,
        DFILowPowerState.LP_POWER_DOWN: 50000,
        DFILowPowerState.LP_DEEP_PD: 200000,
        DFILowPowerState.LP_FREQ_CHANGE: 5000,
    }

    def __init__(self, config=None, timing_params: Optional[DFITimingParameters] = None,
                 queue_config: Optional[DFIRequestQueueConfig] = None):
        """Initialize DFI 5.0 interface

        Args:
            config: Optional configuration object
            timing_params: Optional DFI timing parameters
            queue_config: Optional request queue configuration
        """
        self.version = self.VERSION
        self.config = config
        self.supported_commands = list(DFICommand)

        # Timing parameters
        self.timing = timing_params or DFITimingParameters()

        # State tracking
        self.lp_state = DFILowPowerState.LP_IDLE
        self.lp_state_history: List[Tuple[int, DFILowPowerState]] = []  # (cycle, state)
        self.frequency_mhz = 800  # 800 MT/s for 8 GT/s DDR
        self.target_frequency_mhz = 800
        self.training_complete = False
        self.training_in_progress = False

        # Frequency change state machine
        self._fc_state = DFI5FreqChangeState.FC_IDLE
        self._fc_latency_counter = 0
        self._fc_request_pending = False
        self._fc_initiated_by_controller = False

        # PLL/DLL tracking for frequency change
        self._pll_lock_required = True
        self._dll_lock_required = True

        # === DFI 5.0 Control Update Signals ===
        self._ctrlupd_req = False
        self._ctrlupd_ack = False
        self._ctrlupd_latency_counter = 0
        self._ctrlupd_pending = False

        # === DFI 5.0 Frequency Change Handshake Signals ===
        self._freq_change_en = False
        self._freq_change_ack = False
        self._freq_change_ack_pending = False
        self._freq_change_data_valid = False

        # === DFI 5.0 Power Management Signals ===
        self._pwr_up_done = False
        self._pwr_down_req = False
        self._pwr_down_ack = False
        self._pwr_down_latency_counter = 0

        # === DFI 5.0 Low Power State Signals ===
        self._lp_req = False
        self._lp_ack = False
        self._lp_wakeup = False
        self._lp_entry_counter = 0
        self._lp_exit_counter = 0
        self._lp_timeout_counter = 0
        self._lp_auto_entry_enabled = True
        self._lp_idle_counter = 0
        self._lp_auto_entry_threshold = 100  # Cycles idle before auto LP

        # === CKE Management (DFI 5.0) ===
        self._cke = True  # Clock Enable
        self._cke_override = False

        # PHY interface
        self.phy = DFIPhyIF()

        # Enhanced request/response queues
        self._request_queue = DFI5RequestQueue(queue_config or DFIRequestQueueConfig())
        self._response_queue: List[DFIResponse] = []
        self._error_log: List[DFIErrorRecord] = []

        # Public request_queue attribute for tests (exposes the underlying deque)
        self.request_queue: deque = self._request_queue._queue

        # Statistics
        self._stats = {
            "commands_sent": 0,
            "commands_completed": 0,
            "freq_changes": 0,
            "lp_transitions": 0,
            "lp_entries": 0,
            "lp_exits": 0,
            "lp_timeouts": 0,
            "errors": 0,
            "ctrl_updates": 0,
            "power_cycles": 0,
            "cke_changes": 0,
        }

        # Cycle counter for timestamp tracking
        self._cycle = 0

    @property
    def cycle(self) -> int:
        """Current simulation cycle"""
        return self._cycle

    def tick(self):
        """Advance simulation by one cycle

        Call this once per cycle to update internal state machines
        and track timing.
        """
        prev_lp_state = self.lp_state
        self._cycle += 1

        # Track LP state changes
        if prev_lp_state != self.lp_state:
            self.lp_state_history.append((self._cycle, self.lp_state))
            self._stats["lp_transitions"] += 1

        self._update_freq_change_state()
        self._update_ctrlupd_state()
        self._update_power_state()
        self._update_lp_state()
        self._update_lp_timeout()
        self._check_auto_lp_entry()

    # === DFI 5.0 Control Update Handshake ===

    def request_ctrlupd(self) -> bool:
        """Request a control update (dfi_ctrlupd_req)

        The controller asserts dfi_ctrlupd_req to request a control
        update transaction. The PHY responds with dfi_ctrlupd_ack
        when complete.

        Args:
            None

        Returns:
            True if request was accepted
        """
        if self._ctrlupd_req:
            self._record_error("ctrl_update", "Control update already in progress",
                             self._cycle)
            return False

        self._ctrlupd_req = True
        self._ctrlupd_latency_counter = 0
        return True

    def acknowledge_ctrlupd(self) -> bool:
        """Acknowledge a control update (dfi_ctrlupd_ack)

        Called by the PHY to acknowledge completion of the
        control update transaction.

        Returns:
            True if acknowledgment was accepted
        """
        if not self._ctrlupd_req:
            return False

        self._ctrlupd_ack = True
        self._stats["ctrl_updates"] += 1
        return True

    def _update_ctrlupd_state(self):
        """Update control update state machine

        Handles the dfi_ctrlupd_req/ack handshake timing.
        """
        if self._ctrlupd_req and not self._ctrlupd_ack:
            self._ctrlupd_latency_counter += 1
            if self._ctrlupd_latency_counter >= self.timing.tCTRLUPD_LATENCY:
                # Auto-acknowledge after latency expires
                self._ctrlupd_ack = True

        if self._ctrlupd_ack and self._ctrlupd_req:
            # Complete the handshake
            self._ctrlupd_req = False
            self._ctrlupd_ack = False
            self._ctrlupd_latency_counter = 0

    @property
    def ctrlupd_req(self) -> bool:
        """Get dfi_ctrlupd_req signal state"""
        return self._ctrlupd_req

    @property
    def ctrlupd_ack(self) -> bool:
        """Get dfi_ctrlupd_ack signal state"""
        return self._ctrlupd_ack

    # === DFI 5.0 Frequency Change Handshake ===

    def request_freq_change(self, target_freq_mhz: int) -> bool:
        """Request a frequency change

        Args:
            target_freq_mhz: Target frequency in MHz

        Returns:
            True if request was accepted
        """
        if self._fc_state != DFI5FreqChangeState.FC_IDLE:
            self._record_error("freq_change", "Frequency change already in progress",
                             self._cycle)
            return False

        self.target_frequency_mhz = target_freq_mhz
        self._fc_request_pending = True
        self._fc_state = DFI5FreqChangeState.FC_REQUESTED
        return True

    def enter_freq_change(self) -> bool:
        """Enter frequency change sequence

        Transitions to LP_FREQ_CHANGE state during
        frequency switching.

        Returns:
            True if transition was successful
        """
        if self._fc_state not in [DFI5FreqChangeState.FC_IDLE,
                                   DFI5FreqChangeState.FC_REQUESTED]:
            self._record_error("freq_change", f"Cannot enter freq change from state {self._fc_state.name}",
                             self._cycle)
            return False

        self.lp_state = DFILowPowerState.LP_FREQ_CHANGE
        self._fc_state = DFI5FreqChangeState.FC_ENTERING
        self._fc_latency_counter = 0
        self._stats["freq_changes"] += 1

        # Assert dfi_freq_change_en (DFI 5.0)
        self._freq_change_en = True
        return True

    def set_freq_change_ack(self, ack: bool):
        """Set dfi_freq_change_ack signal (from PHY)

        Args:
            ack: True if PHY acknowledges frequency change
        """
        self._freq_change_ack = ack
        self._freq_change_ack_pending = ack

    def exit_freq_change(self) -> bool:
        """Exit frequency change sequence

        Returns to normal operation after frequency change.

        Returns:
            True if exit was successful
        """
        # Allow exit from FC_ENTERING or FC_ACTIVE states
        if self._fc_state not in [DFI5FreqChangeState.FC_ENTERING,
                                   DFI5FreqChangeState.FC_ACTIVE]:
            self._record_error("freq_change", f"Cannot exit freq change from state {self._fc_state.name}",
                             self._cycle)
            return False

        # Transition to FC_EXITING state
        # Note: lp_state remains LP_FREQ_CHANGE until state machine completes
        # This follows DFI 5.0 spec which requires LP state to remain active
        # during the entire frequency change exit sequence
        self._fc_state = DFI5FreqChangeState.FC_EXITING
        self._fc_latency_counter = 0

        # Deassert dfi_freq_change_en (DFI 5.0)
        self._freq_change_en = False
        self._freq_change_ack = False
        return True

    def _update_freq_change_state(self):
        """Update frequency change state machine

        Handles the dfi_freq_change_en/ack handshake and timing.
        Per DFI 5.0 spec, lp_state should only transition to LP_IDLE
        after the entire frequency change sequence completes.
        """
        if self._fc_state == DFI5FreqChangeState.FC_ENTERING:
            self._fc_latency_counter += 1
            if self._fc_latency_counter >= self.timing.tLP_CTRL_ENTER:
                self._fc_state = DFI5FreqChangeState.FC_ACTIVE
                self._fc_latency_counter = 0

        elif self._fc_state == DFI5FreqChangeState.FC_EXITING:
            self._fc_latency_counter += 1
            if self._fc_latency_counter >= self.timing.tFC_EXIT:
                self._fc_state = DFI5FreqChangeState.FC_LOCKING
                self._fc_latency_counter = 0

        elif self._fc_state == DFI5FreqChangeState.FC_LOCKING:
            self._fc_latency_counter += 1
            if self._fc_latency_counter >= self.timing.tFC_LATENCY:
                self._fc_state = DFI5FreqChangeState.FC_COMPLETE
                self._fc_latency_counter = 0

        elif self._fc_state == DFI5FreqChangeState.FC_COMPLETE:
            # Only transition to IDLE when frequency change is fully complete
            # This follows DFI 5.0 spec for proper LP state management
            self.lp_state = DFILowPowerState.LP_IDLE
            self._fc_state = DFI5FreqChangeState.FC_IDLE
            self.frequency_mhz = self.target_frequency_mhz

    def get_freq_change_state(self) -> DFI5FreqChangeState:
        """Get current frequency change state

        Returns:
            Current FC state
        """
        return self._fc_state

    def is_freq_change_complete(self) -> bool:
        """Check if frequency change sequence is complete

        Returns:
            True if frequency change is complete
        """
        return self._fc_state == DFI5FreqChangeState.FC_IDLE

    def get_freq_change_latency_remaining(self) -> int:
        """Get remaining cycles until frequency change completes

        Returns:
            Remaining cycles, or 0 if not in progress
        """
        if self._fc_state == DFI5FreqChangeState.FC_IDLE:
            return 0

        state_latencies = {
            DFI5FreqChangeState.FC_REQUESTED: self.timing.tLP_CTRL_ENTER,
            DFI5FreqChangeState.FC_ENTERING: self.timing.tLP_CTRL_ENTER - self._fc_latency_counter,
            DFI5FreqChangeState.FC_ACTIVE: self.timing.tFC_EXIT - self._fc_latency_counter,
            DFI5FreqChangeState.FC_EXITING: self.timing.tFC_EXIT - self._fc_latency_counter,
            DFI5FreqChangeState.FC_LOCKING: self.timing.tFC_LATENCY - self._fc_latency_counter,
            DFI5FreqChangeState.FC_COMPLETE: 1,
        }
        return max(0, state_latencies.get(self._fc_state, 0))

    @property
    def freq_change_en(self) -> bool:
        """Get dfi_freq_change_en signal state"""
        return self._freq_change_en

    @property
    def freq_change_ack(self) -> bool:
        """Get dfi_freq_change_ack signal state"""
        return self._freq_change_ack

    # === DFI 5.0 Power Management ===

    def set_pwr_up_done(self, done: bool):
        """Set dfi_pwr_up_done signal

        Indicates that the power-up sequence has completed.

        Args:
            done: True if power-up is complete
        """
        self._pwr_up_done = done

    def request_pwr_down(self) -> bool:
        """Request power down (dfi_pwr_down_req)

        Args:
            None

        Returns:
            True if request was accepted
        """
        if self._pwr_down_req:
            return False

        self._pwr_down_req = True
        self._pwr_down_latency_counter = 0
        self._stats["power_cycles"] += 1
        return True

    def set_pwr_down_ack(self, ack: bool):
        """Set dfi_pwr_down_ack signal (from PHY)

        Args:
            ack: True if PHY acknowledges power down
        """
        self._pwr_down_ack = ack

    def _update_power_state(self):
        """Update power management state machine

        Handles dfi_pwr_up_done and dfi_pwr_down_req/ack timing.
        """
        if self._pwr_down_req and not self._pwr_down_ack:
            self._pwr_down_latency_counter += 1
            if self._pwr_down_latency_counter >= self.timing.tPWR_DOWN:
                # Auto-acknowledge after latency expires
                self._pwr_down_ack = True

    @property
    def pwr_up_done(self) -> bool:
        """Get dfi_pwr_up_done signal state"""
        return self._pwr_up_done

    @property
    def pwr_down_req(self) -> bool:
        """Get dfi_pwr_down_req signal state"""
        return self._pwr_down_req

    @property
    def pwr_down_ack(self) -> bool:
        """Get dfi_pwr_down_ack signal state"""
        return self._pwr_down_ack

    # === DFI 5.0 Low Power State Signals ===

    def request_low_power(self, state: DFILowPowerState) -> bool:
        """Request entry to low power state (lp_req)

        Args:
            state: Target low power state

        Returns:
            True if request was accepted
        """
        if self._lp_req:
            return False

        if not self._is_valid_lp_transition(state):
            raise DFIStateTransitionError(
                f"Invalid LP transition from {self.lp_state.name} to {state.name}"
            )

        self._lp_req = True
        self._lp_entry_counter = 0
        self.lp_state = state
        return True

    def set_lp_ack(self, ack: bool):
        """Set lp_ack signal (from PHY)

        Args:
            ack: True if PHY acknowledges low power entry
        """
        self._lp_ack = ack

    def wakeup_from_low_power(self):
        """Wakeup from low power state (lp_wakeup)

        Asserts lp_wakeup signal to wake the PHY from low power.
        """
        self._lp_wakeup = True
        self._lp_exit_counter = 0

    def clear_lp_wakeup(self):
        """Clear lp_wakeup signal after wakeup is acknowledged"""
        self._lp_wakeup = False

    def _update_lp_state(self):
        """Update low power state machine

        Handles lp_req/ack and lp_wakeup signal timing.
        Supports all DFI 5.0 low power states.
        """
        if self._lp_req and not self._lp_ack:
            self._lp_entry_counter += 1
            # Entry latency is state-dependent
            if self.lp_state == DFILowPowerState.LP_CTRL:
                if self._lp_entry_counter >= self.timing.tLP_CTRL_ENTER:
                    self._lp_ack = True
                    self._stats["lp_entries"] += 1
            elif self.lp_state == DFILowPowerState.LP_DATA:
                if self._lp_entry_counter >= self.timing.tLP_DATA_ENTER:
                    self._lp_ack = True
                    self._stats["lp_entries"] += 1
            elif self.lp_state == DFILowPowerState.LP_SELF_REFRESH:
                if self._lp_entry_counter >= self.timing.tLP_SREF_ENTER:
                    self._lp_ack = True
                    self._stats["lp_entries"] += 1
                    self._cke = False  # Lower CKE for self-refresh
                    self._stats["cke_changes"] += 1
            elif self.lp_state == DFILowPowerState.LP_POWER_DOWN:
                if self._lp_entry_counter >= self.timing.tLP_PD_ENTER:
                    self._lp_ack = True
                    self._stats["lp_entries"] += 1
                    self._cke = False
                    self._stats["cke_changes"] += 1

        if self._lp_wakeup:
            self._lp_exit_counter += 1
            # Exit latency is state-dependent
            if self.lp_state == DFILowPowerState.LP_CTRL:
                if self._lp_exit_counter >= self.timing.tLP_CTRL_EXIT:
                    self.lp_state = DFILowPowerState.LP_IDLE
                    self._lp_req = False
                    self._lp_ack = False
                    self._lp_wakeup = False
                    self._stats["lp_exits"] += 1
            elif self.lp_state == DFILowPowerState.LP_DATA:
                if self._lp_exit_counter >= self.timing.tLP_DATA_EXIT:
                    self.lp_state = DFILowPowerState.LP_IDLE
                    self._lp_req = False
                    self._lp_ack = False
                    self._lp_wakeup = False
                    self._stats["lp_exits"] += 1
            elif self.lp_state == DFILowPowerState.LP_SELF_REFRESH:
                if self._lp_exit_counter >= self.timing.tLP_SREF_EXIT:
                    self.lp_state = DFILowPowerState.LP_IDLE
                    self._lp_req = False
                    self._lp_ack = False
                    self._lp_wakeup = False
                    self._cke = True
                    self._stats["cke_changes"] += 1
                    self._stats["lp_exits"] += 1
            elif self.lp_state == DFILowPowerState.LP_POWER_DOWN:
                if self._lp_exit_counter >= self.timing.tLP_PD_EXIT:
                    self.lp_state = DFILowPowerState.LP_IDLE
                    self._lp_req = False
                    self._lp_ack = False
                    self._lp_wakeup = False
                    self._cke = True
                    self._stats["cke_changes"] += 1
                    self._stats["lp_exits"] += 1

    def _update_lp_timeout(self):
        """Update low power timeout tracking

        Tracks time spent in each LP state and triggers timeout
        handling if thresholds are exceeded.
        """
        if self.lp_state == DFILowPowerState.LP_IDLE:
            self._lp_timeout_counter = 0
            self._lp_idle_counter += 1
            return

        self._lp_idle_counter = 0
        self._lp_timeout_counter += 1

        timeout_threshold = self.LP_TIMEOUT_CYCLES.get(self.lp_state, 0)
        if timeout_threshold > 0 and self._lp_timeout_counter >= timeout_threshold:
            self._record_error("lp_timeout",
                             f"Timeout in LP state {self.lp_state.name} "
                             f"(threshold: {timeout_threshold} cycles)",
                             self._cycle)
            self._stats["lp_timeouts"] += 1

            # Attempt to exit to IDLE
            try:
                self._force_exit_low_power()
            except Exception as e:
                self._record_error("lp_timeout_recovery",
                                 f"Failed to recover from timeout: {str(e)}",
                                 self._cycle)

    def _check_auto_lp_entry(self):
        """Check if auto low-power entry should be triggered

        Automatically enters low-power state after idle threshold
        is reached.
        """
        if not self._lp_auto_entry_enabled:
            return

        if (self.lp_state == DFILowPowerState.LP_IDLE and
            self._lp_idle_counter >= self._lp_auto_entry_threshold and
            not self._request_queue.is_empty()):
            # Stay in IDLE if there are pending requests
            return

        if (self.lp_state == DFILowPowerState.LP_IDLE and
            self._lp_idle_counter >= self._lp_auto_entry_threshold):
            # Auto-enter LP_CTRL after idle threshold
            self.enter_low_power_state(DFILowPowerState.LP_CTRL)

    def _force_exit_low_power(self):
        """Force exit from low power state

        Used for timeout recovery and emergency exits.
        """
        self._lp_req = False
        self._lp_ack = False
        self._lp_wakeup = True
        self._lp_exit_counter = 0
        self._lp_timeout_counter = 0
        self._cke = True
        self._stats["cke_changes"] += 1

    def enter_low_power_state(self, state: DFILowPowerState) -> bool:
        """Enter a specific low power state

        Args:
            state: Target low power state

        Returns:
            True if entry was initiated

        Raises:
            DFIStateTransitionError: If transition is not allowed
        """
        if not self._is_valid_lp_transition(state):
            raise DFIStateTransitionError(
                f"Invalid LP transition from {self.lp_state.name} to {state.name}"
            )

        self.lp_state = state
        self._lp_req = True
        self._lp_entry_counter = 0
        self._lp_exit_counter = 0
        self._lp_timeout_counter = 0
        self._stats["lp_transitions"] += 1
        return True

    def exit_low_power_state(self) -> bool:
        """Exit from low power state

        Returns:
            True if exit was initiated
        """
        if self.lp_state == DFILowPowerState.LP_IDLE:
            return True  # Already in IDLE

        self._lp_wakeup = True
        self._lp_exit_counter = 0
        return True

    @property
    def cke(self) -> bool:
        """Get Clock Enable signal state"""
        return self._cke

    def set_cke(self, enable: bool):
        """Set Clock Enable signal

        Args:
            enable: True to enable clocks (CKE high)
        """
        if self._cke != enable:
            self._cke = enable
            self._stats["cke_changes"] += 1

    def set_cke_override(self, override: bool):
        """Set CKE override mode

        Args:
            override: True to bypass automatic CKE management
        """
        self._cke_override = override

    def get_lp_statistics(self) -> Dict[str, Any]:
        """Get low power state statistics

        Returns:
            Dictionary with LP statistics
        """
        return {
            'current_state': self.lp_state.name,
            'time_in_state': self._lp_timeout_counter,
            'idle_counter': self._lp_idle_counter,
            'timeout_threshold': self.LP_TIMEOUT_CYCLES.get(self.lp_state, 0),
            'entries': self._stats['lp_entries'],
            'exits': self._stats['lp_exits'],
            'timeouts': self._stats['lp_timeouts'],
            'transitions': self._stats['lp_transitions'],
            'cke_changes': self._stats['cke_changes'],
            'auto_entry_enabled': self._lp_auto_entry_enabled,
            'auto_entry_threshold': self._lp_auto_entry_threshold,
        }

    def get_lp_state_history(self) -> List[Tuple[int, str]]:
        """Get LP state transition history

        Returns:
            List of (cycle, state_name) tuples
        """
        return [(cycle, state.name) for cycle, state in self.lp_state_history]

    @property
    def lp_req(self) -> bool:
        """Get lp_req signal state"""
        return self._lp_req

    @property
    def lp_ack(self) -> bool:
        """Get lp_ack signal state"""
        return self._lp_ack

    @property
    def lp_wakeup(self) -> bool:
        """Get lp_wakeup signal state"""
        return self._lp_wakeup

    def _is_valid_lp_transition(self, new_state: DFILowPowerState) -> bool:
        """Check if a low-power state transition is valid

        Args:
            new_state: Target state

        Returns:
            True if transition is valid
        """
        if new_state == self.lp_state:
            return True  # No change is always valid
        return new_state in self.VALID_LP_TRANSITIONS.get(self.lp_state, [])

    def encode_command(self, cmd: str, addr_vec: Optional[Dict[str, int]] = None,
                      priority: int = 0, **kwargs) -> DFIRequest:
        """Encode a command into DFI request format

        Args:
            cmd: Command name string ('ACT', 'PRE', 'RD', etc.)
            addr_vec: Dictionary with address components
            priority: Request priority (higher = more urgent)
            **kwargs: Additional command parameters

        Returns:
            DFIRequest object

        Raises:
            ValueError: If command is invalid or parameters are missing
        """
        addr_vec = addr_vec or {}

        # Map string command to DFI command
        cmd_map = {
            'ACT': DFICommand.ACT,
            'PRE': DFICommand.PRE,
            'PREA': DFICommand.PREA,
            'RD': DFICommand.RD,
            'WR': DFICommand.WR,
            'RDA': DFICommand.RDA,
            'WRA': DFICommand.WRA,
            'REFab': DFICommand.REFab,
            'REFsb': DFICommand.REFsb,
            'RFMab': DFICommand.RFMab,
            'RFMsb': DFICommand.RFMsb,
            'MRS': DFICommand.MRS,
            'MRR': DFICommand.MRR,
            'SREF': DFICommand.SREF,
            'SREFEX': DFICommand.SREFEX,
            'PD': DFICommand.PD,
            'PDEX': DFICommand.PDEX,
            'DPD': DFICommand.DPD,
            'DPDEX': DFICommand.DPDEX,
            'WRLVL': DFICommand.WRLVL,
            'RDLVL': DFICommand.RDLVL,
            'RDDQSDQ': DFICommand.RDDQSDQ,
            'WRDQSDQ': DFICommand.WRDQSDQ,
            'MRLVL': DFICommand.MRLVL,
            'ZQCL': DFICommand.ZQCL,
            'ZQCS': DFICommand.ZQCS,
            'ZQOP': DFICommand.ZQOP,
            'NOP': DFICommand.NOP,
            'DESELECT': DFICommand.DESELECT,
        }

        dfi_cmd = cmd_map.get(cmd.upper())
        if dfi_cmd is None:
            raise ValueError(f"Invalid command: {cmd}")

        # Validate command requirements
        self._validate_command_params(dfi_cmd, addr_vec)

        return DFIRequest(
            command=dfi_cmd,
            address=addr_vec.get('row', addr_vec.get('address', addr_vec.get('mr_addr', 0))),
            bank=addr_vec.get('bank', 0),
            pseudo_channel=addr_vec.get('pseudo_channel', 0),
            channel=addr_vec.get('channel', 0),
            wrdata_en=dfi_cmd.is_write(),
            rddata_en=dfi_cmd.is_read(),
            chip=addr_vec.get('chip', 0),
            priority=priority,
            timestamp=self._cycle,
            error=None,
        )

    def _validate_command_params(self, cmd: DFICommand, addr_vec: Dict[str, int]):
        """Validate command parameters

        Args:
            cmd: DFI command
            addr_vec: Address vector

        Raises:
            ValueError: If parameters are invalid for the command
        """
        if cmd.requires_row() and 'row' not in addr_vec and 'address' not in addr_vec:
            raise ValueError(f"Command {cmd.name} requires row address")

        if cmd.requires_bank() and 'bank' not in addr_vec:
            raise ValueError(f"Command {cmd.name} requires bank address")

        if cmd.requires_mr():
            if 'mr_addr' not in addr_vec and 'address' not in addr_vec:
                raise ValueError(f"Command {cmd.name} requires mode register address")

    def encode_batch_commands(self, commands: List[Tuple[str, Dict[str, int]]],
                             default_priority: int = 0) -> List[DFIRequest]:
        """Encode multiple commands into DFI requests

        Args:
            commands: List of (command_name, addr_vec) tuples
            default_priority: Default priority for commands

        Returns:
            List of DFIRequest objects
        """
        requests = []
        for i, (cmd, addr_vec) in enumerate(commands):
            priority = addr_vec.get('priority', default_priority)
            try:
                request = self.encode_command(cmd, addr_vec, priority)
                requests.append(request)
            except (ValueError, DFIStateTransitionError) as e:
                self._record_error("command_encoding", str(e), self._cycle)
        return requests

    def get_command_info(self, cmd: DFICommand) -> Dict[str, Any]:
        """Get information about a command

        Args:
            cmd: DFI command

        Returns:
            Dictionary with command attributes
        """
        return {
            'name': cmd.name,
            'value': cmd.value,
            'is_read': cmd.is_read(),
            'is_write': cmd.is_write(),
            'is_activate': cmd.is_activate(),
            'is_precharge': cmd.is_precharge(),
            'is_refresh': cmd.is_refresh(),
            'is_power_down': cmd.is_power_down(),
            'is_training': cmd.is_training(),
            'requires_bank': cmd.requires_bank(),
            'requires_row': cmd.requires_row(),
            'requires_col': cmd.requires_col(),
            'requires_mr': cmd.requires_mr(),
        }

    def get_supported_commands(self) -> List[Dict[str, Any]]:
        """Get list of all supported commands with attributes

        Returns:
            List of command info dictionaries
        """
        return [self.get_command_info(cmd) for cmd in DFICommand]

    def set_low_power_state(self, state: DFILowPowerState,
                           enforce_timing: bool = True) -> bool:
        """Set DFI low-power state

        Args:
            state: Target low-power state
            enforce_timing: If True, enforce timing constraints

        Returns:
            True if transition was valid and accepted

        Raises:
            DFIStateTransitionError: If transition is invalid and enforce_timing is True
        """
        if enforce_timing and not self._is_valid_lp_transition(state):
            raise DFIStateTransitionError(
                f"Invalid LP transition from {self.lp_state.name} to {state.name}"
            )

        self.lp_state = state
        self._stats["lp_transitions"] += 1
        return True

    def get_response(self, response_id: int = 0) -> DFIResponse:
        """Get response from PHY

        Args:
            response_id: ID to match with corresponding request

        Returns:
            DFIResponse with current PHY state
        """
        return DFIResponse(
            ready=self.lp_state in [DFILowPowerState.LP_IDLE, DFILowPowerState.LP_CTRL],
            calibration_done=self.training_complete,
            training_state="complete" if self.training_complete else
                          "in_progress" if self.training_in_progress else
                          "not_started",
            lp_state=self.lp_state,
            phy_clock_enable=self.phy.phy_clock_enable,
            phy_reset=self.phy.phy_reset,
            response_id=response_id,
            timestamp=self._cycle,
            # DFI 5.0 signal states
            ctrlupd_ack=self._ctrlupd_ack,
            freq_change_ack=self._freq_change_ack,
            pwr_up_done=self._pwr_up_done,
            pwr_down_ack=self._pwr_down_ack,
            lp_ack=self._lp_ack,
        )

    def start_training(self):
        """Initiate PHY training sequence (DFI PHY Independent Mode)

        This enters PHY Independent Mode where the controller
        manages training sequences independently of the PHY.
        """
        self.training_in_progress = True
        self.training_complete = False
        self.phy.phy_independent_mode = True

    def complete_training(self):
        """Mark training as complete

        Called when all training sequences have completed
        successfully.
        """
        self.training_complete = True
        self.training_in_progress = False

    def set_frequency(self, freq_mhz: int):
        """Set interface frequency

        Args:
            freq_mhz: Frequency in MHz
        """
        self.frequency_mhz = freq_mhz
        self.target_frequency_mhz = freq_mhz

    def get_frequency(self) -> int:
        """Get current interface frequency

        Returns:
            Frequency in MHz
        """
        return self.frequency_mhz

    def get_target_frequency(self) -> int:
        """Get target frequency for pending frequency change

        Returns:
            Target frequency in MHz
        """
        return self.target_frequency_mhz

    # === Request Queue Management ===

    def queue_request(self, request: DFIRequest) -> bool:
        """Add request to queue

        Args:
            request: DFI request to queue

        Returns:
            True if successfully queued
        """
        success = self._request_queue.enqueue(request)
        if success:
            self._stats["commands_sent"] += 1
        return success

    def get_next_request(self) -> Optional[DFIRequest]:
        """Get next request from queue

        Returns:
            Next DFIRequest or None if queue empty
        """
        return self._request_queue.dequeue()

    def peek_request(self) -> Optional[DFIRequest]:
        """View next request without removing

        Returns:
            Next DFIRequest or None if queue empty
        """
        return self._request_queue.peek()

    def clear_requests(self):
        """Clear all pending requests"""
        self._request_queue.clear()

    @property
    def pending_request_count(self) -> int:
        """Number of pending requests in queue"""
        return self._request_queue.size

    @property
    def queue_available_capacity(self) -> int:
        """Available queue capacity"""
        return self._request_queue.available_capacity

    @property
    def is_queue_full(self) -> bool:
        """Check if request queue is full"""
        return self._request_queue.is_full()

    # === Error Reporting ===

    def _record_error(self, error_type: str, message: str, timestamp: int,
                      request_id: Optional[int] = None):
        """Record an error

        Args:
            error_type: Type/category of error
            message: Human-readable error message
            timestamp: Cycle when error occurred
            request_id: Optional associated request ID
        """
        self._error_log.append(DFIErrorRecord(
            error_type=error_type,
            error_message=message,
            timestamp=timestamp,
            request_id=request_id
        ))
        self._stats["errors"] += 1

    def get_errors(self, error_type: Optional[str] = None) -> List[DFIErrorRecord]:
        """Get recorded errors

        Args:
            error_type: Optional filter by error type

        Returns:
            List of error records
        """
        if error_type is None:
            return list(self._error_log)
        return [e for e in self._error_log if e.error_type == error_type]

    def get_statistics(self) -> Dict[str, Any]:
        """Get interface statistics

        Returns:
            Dictionary with statistics
        """
        stats = dict(self._stats)
        stats.update(self._request_queue.get_statistics())
        stats["queue_utilization_pct"] = stats["utilization"] * 100
        return stats

    def reset_statistics(self):
        """Reset statistics counters"""
        self._stats = {
            "commands_sent": 0,
            "commands_completed": 0,
            "freq_changes": 0,
            "lp_transitions": 0,
            "errors": 0,
            "ctrl_updates": 0,
            "power_cycles": 0,
        }
        self._error_log.clear()

    # === Timing Parameters ===

    def get_write_latency_ps(self) -> float:
        """Get write latency in picoseconds

        Returns:
            Write latency in ps
        """
        tCK_ps = 1000.0 / self.frequency_mhz if self.frequency_mhz > 0 else 125.0
        return self.timing.get_write_latency_ps(tCK_ps)

    def get_read_latency_ps(self) -> float:
        """Get read latency in picoseconds

        Returns:
            Read latency in ps
        """
        tCK_ps = 1000.0 / self.frequency_mhz if self.frequency_mhz > 0 else 125.0
        return self.timing.get_read_latency_ps(tCK_ps)

    def get_timing_parameters(self) -> DFITimingParameters:
        """Get DFI timing parameters

        Returns:
            Current timing parameters
        """
        return self.timing

    def set_timing_parameters(self, timing: DFITimingParameters):
        """Set DFI timing parameters

        Args:
            timing: New timing parameters
        """
        self.timing = timing

    # === Utility Methods ===

    def add_calibration_data(self, key: str, value: Any):
        """Add calibration data

        Args:
            key: Calibration data key (e.g., 'read_delay', 'write_leveling')
            value: Calibration value
        """
        self.phy.calibration_data[key] = value

    def get_bandwidth_gbs(self) -> float:
        """Get theoretical bandwidth in GB/s

        Uses the HBM4 formula: data_rate (GT/s) × io_width (bits) / 8
        For HBM4 @ 8 GT/s with 2048-bit width: 8 × 2048 / 8 = 2048 GB/s

        Note: This returns the theoretical peak bandwidth for the full interface.

        Returns:
            Theoretical bandwidth in GB/s
        """
        # HBM4 bandwidth formula: data_rate (GT/s) × io_width (bits) / 8 = GB/s
        # For HBM4: 8 GT/s × 2048 bits / 8 = 2048 GB/s
        io_width = 2048  # HBM4 interface width in bits
        # Convert DFI frequency (in MHz) to GT/s
        # DFI frequency represents the interface clock, not the memory data rate
        # For HBM4 at 8 GT/s, the DFI clock is 800 MHz
        # So we use the stored frequency to compute the actual data rate
        data_rate_gtps = self.frequency_mhz / 100  # 800 MHz → 8 GT/s
        return data_rate_gtps * io_width / 8

    def get_bandwidth_tbs(self) -> float:
        """Get theoretical bandwidth in TB/s

        Returns:
            Theoretical bandwidth in TB/s
        """
        return self.get_bandwidth_gbs() / 1000

    def is_ready(self) -> bool:
        """Check if interface is ready for commands

        Returns:
            True if ready (not in LP_DATA or LP_FREQ_CHANGE)
        """
        return self.lp_state in [DFILowPowerState.LP_IDLE, DFILowPowerState.LP_CTRL]

    def can_accept_request(self) -> bool:
        """Check if interface can accept new requests

        Returns:
            True if request queue has space
        """
        return not self.is_queue_full and self.is_ready()

    def get_dfi_signals(self) -> DFISignals:
        """Get current state of all DFI signals

        Returns:
            DFISignals object with all signal states
        """
        return DFISignals(
            ctrlupd_req=self._ctrlupd_req,
            ctrlupd_ack=self._ctrlupd_ack,
            freq_change_en=self._freq_change_en,
            freq_change_ack=self._freq_change_ack,
            pwr_up_done=self._pwr_up_done,
            pwr_down_req=self._pwr_down_req,
            pwr_down_ack=self._pwr_down_ack,
            lp_req=self._lp_req,
            lp_ack=self._lp_ack,
            lp_wakeup=self._lp_wakeup,
            lp_state=self.lp_state,
            phy_ready=self.is_ready(),
            training_complete=self.training_complete,
        )

    def reset(self):
        """Reset interface to initial state

        Preserves calibration data but resets state machines
        and queues.
        """
        self.lp_state = DFILowPowerState.LP_IDLE
        self._fc_state = DFI5FreqChangeState.FC_IDLE
        self._fc_latency_counter = 0
        self._fc_request_pending = False

        # Reset DFI 5.0 signals
        self._ctrlupd_req = False
        self._ctrlupd_ack = False
        self._ctrlupd_latency_counter = 0
        self._freq_change_en = False
        self._freq_change_ack = False
        self._pwr_up_done = False
        self._pwr_down_req = False
        self._pwr_down_ack = False
        self._lp_req = False
        self._lp_ack = False
        self._lp_wakeup = False

        self.training_complete = False
        self.training_in_progress = False
        self._request_queue.clear()
        self._response_queue.clear()
        self._error_log.clear()
        self._cycle = 0
        self.reset_statistics()