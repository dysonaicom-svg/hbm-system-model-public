"""
PHY Training State Machine for HBM4

Implements PHY initialization and training sequences according to
JEDEC JESD270-4A HBM4 specification.

Key features:
- PHY initialization state machine (PH-003)
- Training sequence state machine (PH-004)
- Read/Write DQS training
- Read DQ (RDDQ) training - data eye training
- Write DQ (WDQ) training - write data eye training
- Gate Training (GL) for read gate alignment
- VREF CA/DQ training
- DFI 5.0/5.1 interface integration
- Per-lane and per-group calibration support
- HBM4 PAM3 (3-level) signaling training
- PAM3 eye diagram and DFE training
- PHY Independent Mode (PIM) for DFI 5.0

Training Sequence (JEDEC JESD270-4A):
1. Initialize training
2. Read DQS training (T_RDDQS)
3. Write leveling (T_WRLVL)
4. Read DQ training / Read Data Eye (T_RDDQ / RDDQ)
5. Write DQ training / Write Data Eye (T_WRDQ / WDQ)
6. Gate Training (T_GL)
7. VREF CA training (T_VREF_CA)
8. VREF DQ training (T_VREF_DQ)
9. PAM3-specific training (HBM4E)
10. Verify and complete

HBM4 PAM3 Signaling:
- Uses 3-level signaling: -1, 0, +1 (vs NRZ's 0, 1)
- Requires 3-level VREF calibration
- Requires PAM3-specific eye training
- DFE tap coefficients for 3-level decision boundaries
- PAM3-specific margin measurement

Reference:
- JEDEC JESD270-4A HBM4 specification
- Cadence HBM4E documentation
- DFI 5.0/5.1 specification
- Synopsys DesignWare HBM4/4E Controller IP
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import deque


# HBM4 VREF range constants (JEDEC JESD270-4A)
# VREF DAC is typically 6-bit (0-63)
VREF_DAC_BITS = 6
VREF_DAC_RANGE = (0, 63)  # 6-bit DAC range
VREF_CA_MIN = VREF_DAC_RANGE[0]  # 0
VREF_CA_MAX = VREF_DAC_RANGE[1]  # 63
VREF_DQ_MIN = VREF_DAC_RANGE[0]  # 0
VREF_DQ_MAX = VREF_DAC_RANGE[1]  # 63
# VREF as percentage of VDDQ (typical range)
VREF_CA_RANGE_PERCENT = (15.0, 45.0)  # 15-45% VDDQ
VREF_DQ_RANGE_PERCENT = (15.0, 45.0)   # 15-45% VDDQ


# =============================================================================
# HBM4 PAM3 Signaling Constants (JEDEC JESD270-4A)
# =============================================================================
# HBM4 introduces PAM3 (3-level Pulse Amplitude Modulation) at higher speeds
# PAM3 uses three signal levels: -1, 0, +1 (vs NRZ's binary 0, 1)

class PAM3Level(Enum):
    """PAM3 signal levels for HBM4"""
    LOW = -1    # -1 level (negative)
    ZERO = 0    # 0 level (baseline)
    HIGH = 1   # +1 level (positive)


class PAM3TrainingState(Enum):
    """PAM3-specific training phases for HBM4E"""
    PAM3_INIT = auto()                    # Initialize PAM3 training
    PAM3_VREF_CAL = auto()               # PAM3 VREF calibration (3-level)
    PAM3_EYE_TRAINING = auto()            # PAM3 eye diagram training
    PAM3_DFE_TAPS = auto()                # DFE tap coefficient training
    PAM3_MARGIN_VERIFY = auto()           # Verify PAM3 margins
    PAM3_COMPLETE = auto()                # PAM3 training complete


# PAM3 VREF DAC settings (HBM4 uses finer granularity for 3-level)
PAM3_VREF_DAC_BITS = 7        # 7-bit DAC for PAM3 (vs 6-bit for NRZ)
PAM3_VREF_DAC_RANGE = (0, 127)  # 7-bit range
PAM3_VREF_HIGH_MIN = 40        # Upper VREF threshold for +1 level
PAM3_VREF_HIGH_MAX = 90        # Max upper threshold
PAM3_VREF_LOW_MIN = 10         # Min lower threshold
PAM3_VREF_LOW_MAX = 60         # Max lower threshold
PAM3_VREF_MID = 63             # Middle point (same as NRZ center)

# PAM3 eye center margins (typical values)
PAM3_UPPER_EYE_MARGIN = 0.2   # Upper eye opening (UI fraction)
PAM3_LOWER_EYE_MARGIN = 0.2   # Lower eye opening (UI fraction)
PAM3_VERTICAL_EYE_MARGIN = 0.15  # Vertical margin between eyes

# PAM3 DFE configuration
PAM3_DFE_NUM_TAPS = 5          # Number of DFE taps for PAM3
PAM3_DFE_MAX_TAP_WEIGHT = 0.25  # Maximum DFE tap weight
PAM3_DFE_CONVERGENCE_RATE = 0.01  # DFE LMS convergence rate


class PAM3SignalConfig:
    """PAM3 signal configuration for HBM4"""

    def __init__(self):
        # PAM3 level thresholds (VREF settings)
        self.vref_high: int = PAM3_VREF_MID        # Threshold between ZERO and HIGH
        self.vref_low: int = PAM3_VREF_MID         # Threshold between LOW and ZERO

        # PAM3 margins
        self.upper_eye_margin: float = PAM3_UPPER_EYE_MARGIN
        self.lower_eye_margin: float = PAM3_LOWER_EYE_MARGIN
        self.vertical_margin: float = PAM3_VERTICAL_EYE_MARGIN

        # DFE taps for PAM3
        self.dfe_taps: List[float] = [0.0] * PAM3_DFE_NUM_TAPS

        # Training status
        self.training_complete: bool = False
        self.training_passed: bool = False
        self.errors: List[str] = []

    def validate_vref_settings(self) -> bool:
        """Validate PAM3 VREF settings are within valid range"""
        if not (PAM3_VREF_DAC_RANGE[0] <= self.vref_high <= PAM3_VREF_DAC_RANGE[1]):
            self.errors.append(f"vref_high {self.vref_high} out of range")
            return False
        if not (PAM3_VREF_DAC_RANGE[0] <= self.vref_low <= PAM3_VREF_DAC_RANGE[1]):
            self.errors.append(f"vref_low {self.vref_low} out of range")
            return False
        if self.vref_low >= self.vref_high:
            self.errors.append(f"vref_low ({self.vref_low}) >= vref_high ({self.vref_high})")
            return False
        return True

    def get_pam3_level(self, sample: float) -> PAM3Level:
        """Determine PAM3 level from analog sample

        Args:
            sample: Analog sample value (normalized -1 to +1)

        Returns:
            PAM3Level corresponding to sample
        """
        if sample >= self.vref_high / PAM3_VREF_DAC_RANGE[1]:
            return PAM3Level.HIGH
        elif sample <= self.vref_low / PAM3_VREF_DAC_RANGE[1]:
            return PAM3Level.LOW
        else:
            return PAM3Level.ZERO

    def calculate_eye_center(self) -> Tuple[float, float]:
        """Calculate PAM3 eye center positions

        Returns:
            Tuple of (upper_eye_center, lower_eye_center) normalized positions
        """
        upper_center = (self.vref_high + PAM3_VREF_DAC_RANGE[1]) / 2 / PAM3_VREF_DAC_RANGE[1]
        lower_center = self.vref_low / 2 / PAM3_VREF_DAC_RANGE[1]
        return (upper_center, lower_center)


# =============================================================================
# DFI 5.0 Interface Constants
# =============================================================================

# DFI 5.0 Frequency Change Protocol
DFI5_FREQ_CHANGE_TIMEOUT = 10000      # Cycles for freq change timeout
DFI5_FREQ_LATENCY = 5                 # Frequency change latency cycles

# DFI 5.0 Low Power States
class DFI5LowPowerState(Enum):
    """DFI 5.0 Low Power State Machine"""
    LP_IDLE = auto()          # Normal operation
    LP_CTRL = auto()         # Controller-initiated low power
    LP_DATA = auto()         # Data transfer low power
    LP_FREQ_CHANGE = auto()  # Frequency change in progress
    LP_SELF_REFRESH = auto() # Self-refresh state


# DFI 5.0 PHY Independent Mode (PIM) signals
class DFIPIMSignals:
    """DFI 5.0 PHY Independent Mode signals

    PIM allows the PHY to operate autonomously during initialization
    and training without controller intervention.
    """

    def __init__(self):
        # PIM control
        self.pim_enable: bool = False           # Enable PHY Independent Mode
        self.pim_mode: int = 0                   # PIM operating mode (0-3)

        # Training control
        self.pim_training_req: bool = False     # Training request from PHY
        self.pim_training_ack: bool = False      # Controller acknowledgment
        self.pim_training_done: bool = False     # Training completion

        # Frequency change
        self.pim_freq_req: bool = False         # Frequency change request
        self.pim_freq_ack: bool = False          # Frequency change acknowledgment

        # Status
        self.pim_status: int = 0                # PHY status code
        self.pim_error: bool = False             # Error flag
        self.pim_error_code: int = 0             # Error code


class PHYInitState(Enum):
    """PHY Initialization State Machine (PH-003)

    Tracks the initialization sequence from power-on to ready state.
    """
    INIT_IDLE = auto()           # Initial idle state
    INIT_START = auto()          # Start initialization sequence
    INIT_POWER_UP = auto()      # Power-up sequence
    INIT_RESET = auto()          # Reset phase
    INIT_CONFIG = auto()         # Configuration loading
    INIT_CALIBRATE = auto()      # Calibration phase
    INIT_TRAINING = auto()       # Training phase
    INIT_COMPLETE = auto()       # Initialization complete


class TrainingPhase(Enum):
    """Training Sequence State Machine (PH-004)

    Defines the stages of memory training for link optimization.
    Includes HBM4 PAM3-specific training phases for HBM4E support.
    """
    # Initial states
    TRAIN_IDLE = auto()                    # Not training
    TRAIN_START = auto()                   # Start training sequence
    TRAIN_INIT = auto()                    # Training initialization

    # DQS training phases
    TRAIN_RD_DQS = auto()                  # Read DQS training
    TRAIN_WR_LEVELING = auto()             # Write leveling

    # DQ training phases - Read DQ / RDDQ (data eye training)
    TRAIN_RD_DQ = auto()                  # Read DQ training (RDDQ)
    TRAIN_RD_DQ_EYE = auto()               # Read DQ eye center training

    # DQ training phases - Write DQ / WDQ (data eye training)
    TRAIN_WR_DQ = auto()                   # Write DQ training (WDQ)
    TRAIN_WR_DQ_EYE = auto()               # Write DQ eye center training

    # Gate training
    TRAIN_GATE = auto()                    # Gate training (read gate alignment)
    TRAIN_GATE_DELAY = auto()              # Gate delay optimization

    # VREF training
    TRAIN_VREF_CA = auto()                 # VREF CA training
    TRAIN_VREF_DQ = auto()                 # VREF DQ training

    # HBM4E PAM3 Training phases
    TRAIN_PAM3_INIT = auto()               # PAM3 training initialization
    TRAIN_PAM3_VREF = auto()               # PAM3 VREF calibration (3-level)
    TRAIN_PAM3_EYE = auto()                # PAM3 eye diagram training
    TRAIN_PAM3_DFE = auto()               # PAM3 DFE tap training
    TRAIN_PAM3_VERIFY = auto()             # PAM3 margin verification

    # Completion states
    TRAIN_VERIFY = auto()                  # Verify training results
    TRAIN_COMPLETE = auto()                # Training complete
    TRAIN_FAIL = auto()                     # Training failed


class TrainingResult(Enum):
    """Training result codes"""
    SUCCESS = auto()                       # Training passed
    FAIL_TIMEOUT = auto()                  # Timeout during training
    FAIL_MARGIN = auto()                   # Margin too small
    FAIL_VERIFY = auto()                   # Verification failed
    FAIL_PARAM = auto()                    # Invalid parameters


@dataclass
class TrainingParameters:
    """Training parameters for each training phase

    Stores delay values, margins, and configuration for each
    training stage. Includes HBM4 PAM3-specific parameters.
    """
    # Read DQS training
    rd_dqs_delay: int = 0                  # Read DQS delay (taps)
    rd_dqs_gate_delay: int = 0             # Read DQS gate delay (taps)

    # Write leveling
    wr_level_delay: int = 0               # Write leveling delay (taps)
    wr_dq_delay: int = 0                   # Write DQ delay (taps)

    # Margin training
    rd_margin: float = 0.0                 # Read margin (UI)
    wr_margin: float = 0.0                 # Write margin (UI)
    rd_vref: int = 0                       # Read VREF setting
    wr_vref: int = 0                       # Write VREF setting

    # CA training
    ca_vref: int = 0                       # CA VREF setting
    ca_delay: int = 0                      # CA delay (taps)

    # Per-lane calibration data
    lane_delays: Dict[int, int] = field(default_factory=dict)  # Lane-specific delays

    # PAM3 training parameters (HBM4E)
    pam3_enabled: bool = False             # PAM3 mode enabled
    pam3_upper_vref: int = PAM3_VREF_MID   # Upper VREF threshold
    pam3_lower_vref: int = PAM3_VREF_MID   # Lower VREF threshold
    pam3_upper_margin: float = 0.0        # Upper eye margin (UI)
    pam3_lower_margin: float = 0.0        # Lower eye margin (UI)
    pam3_dfe_taps: List[float] = field(default_factory=lambda: [0.0] * PAM3_DFE_NUM_TAPS)
    pam3_training_complete: bool = False   # PAM3 training completed

    # Training status
    training_passed: bool = False
    training_errors: List[str] = field(default_factory=list)


@dataclass
class DFI5TrainingControl:
    """DFI 5.0/5.1 Training Control Signals

    According to DFI 5.0/5.1 specification for PHY Independent Mode
    training control. Includes PAM3-specific training commands for HBM4E.
    """
    # Training request signals
    tra_req: bool = False                  # Training request
    tra_mode: int = 0                       # Training mode (0-7)
    tra_type: int = 0                       # Training type selector

    # Training acknowledge
    tra_ack: bool = False                  # Training acknowledge from PHY
    tra_complete: bool = False              # Training complete

    # Training status
    tra_error: bool = False                 # Training error
    tra_fail_code: int = 0                  # Failure code

    # DFI 5.0 Frequency change signals
    freq_change_req: bool = False           # Frequency change request
    freq_change_ack: bool = False           # Frequency change acknowledge
    freq_change_en: bool = False            # Frequency change enable
    freq_ratio: int = 1                     # Frequency ratio (PHY/CTRL)

    # DFI 5.0 Low power signals
    lp_req: bool = False                    # Low power entry request
    lp_ack: bool = False                    # Low power acknowledge
    lp_wakeup: bool = False                 # Low power wakeup
    lp_state: DFI5LowPowerState = DFI5LowPowerState.LP_IDLE

    # DFI 5.0 PHY Independent Mode (PIM) signals
    pim_enable: bool = False                # Enable PHY Independent Mode
    pim_training_req: bool = False         # PIM training request
    pim_training_done: bool = False        # PIM training done
    pim_status: int = 0                    # PHY status during PIM

    # DFI 5.0 Control update
    ctrlupd_req: bool = False              # Controller update request
    ctrlupd_ack: bool = False               # Controller update acknowledge

    # PAM3 training commands (DFI 5.0 for HBM4E)
    pam3_training_req: bool = False         # PAM3 training request
    pam3_vref_req: bool = False             # PAM3 VREF calibration request
    pam3_dfe_req: bool = False              # PAM3 DFE tap training request

    def encode_training_cmd(self, cmd: TrainingPhase) -> Tuple[bool, int, int]:
        """Encode training command for DFI interface

        Args:
            cmd: Training phase command

        Returns:
            Tuple of (tra_req, tra_mode, tra_type)
        """
        cmd_map = {
            TrainingPhase.TRAIN_RD_DQS: (True, 1, 0),
            TrainingPhase.TRAIN_WR_LEVELING: (True, 1, 1),
            TrainingPhase.TRAIN_RD_DQ: (True, 2, 0),       # RDDQ
            TrainingPhase.TRAIN_RD_DQ_EYE: (True, 2, 1),   # Read eye center
            TrainingPhase.TRAIN_WR_DQ: (True, 3, 0),       # WDQ
            TrainingPhase.TRAIN_WR_DQ_EYE: (True, 3, 1),   # Write eye center
            TrainingPhase.TRAIN_GATE: (True, 4, 0),       # Gate training
            TrainingPhase.TRAIN_GATE_DELAY: (True, 4, 1),  # Gate delay
            TrainingPhase.TRAIN_VREF_CA: (True, 5, 0),
            TrainingPhase.TRAIN_VREF_DQ: (True, 5, 1),
        }
        return cmd_map.get(cmd, (False, 0, 0))

    def encode_pam3_training_cmd(self, pam3_state: PAM3TrainingState) -> Tuple[bool, int]:
        """Encode PAM3 training command for DFI interface

        Args:
            pam3_state: PAM3 training state

        Returns:
            Tuple of (pam3_req, pam3_subtype)
        """
        pam3_cmd_map = {
            PAM3TrainingState.PAM3_INIT: (True, 0),
            PAM3TrainingState.PAM3_VREF_CAL: (True, 1),       # VREF calibration
            PAM3TrainingState.PAM3_EYE_TRAINING: (True, 2),  # Eye training
            PAM3TrainingState.PAM3_DFE_TAPS: (True, 3),       # DFE training
            PAM3TrainingState.PAM3_MARGIN_VERIFY: (True, 4),  # Margin verification
            PAM3TrainingState.PAM3_COMPLETE: (False, 0),
        }
        return pam3_cmd_map.get(pam3_state, (False, 0))

    def start_freq_change(self, target_ratio: int = 2):
        """Initiate DFI 5.0 frequency change sequence

        Args:
            target_ratio: Target frequency ratio (PHY/CTRL)
        """
        self.freq_change_req = True
        self.freq_ratio = target_ratio
        self.lp_state = DFI5LowPowerState.LP_FREQ_CHANGE

    def complete_freq_change(self):
        """Complete frequency change sequence"""
        self.freq_change_req = False
        self.freq_change_ack = False
        self.freq_change_en = False
        self.lp_state = DFI5LowPowerState.LP_IDLE

    def enter_low_power(self, lp_type: DFI5LowPowerState = DFI5LowPowerState.LP_CTRL):
        """Enter low power state

        Args:
            lp_type: Type of low power state to enter
        """
        self.lp_req = True
        self.lp_state = lp_type

    def exit_low_power(self):
        """Exit low power state"""
        self.lp_wakeup = True
        self.lp_req = False
        self.lp_ack = False
        self.lp_state = DFI5LowPowerState.LP_IDLE

    def enable_pim_mode(self, pim_mode: int = 1):
        """Enable PHY Independent Mode (PIM)

        Args:
            pim_mode: PIM operating mode (1=training, 2=calibration, 3=both)
        """
        self.pim_enable = True
        self.pim_mode = pim_mode
        self.pim_training_req = True


@dataclass
class TrainingStatus:
    """Current training status and statistics"""
    current_phase: TrainingPhase = TrainingPhase.TRAIN_IDLE
    phase_start_cycle: int = 0
    phase_timeout_cycles: int = 0
    total_training_cycles: int = 0
    retry_count: int = 0
    max_retries: int = 3
    results: Dict[TrainingPhase, TrainingResult] = field(default_factory=dict)
    params: TrainingParameters = field(default_factory=TrainingParameters)


@dataclass
class PHYInitStatus:
    """PHY Initialization Status"""
    state: PHYInitState = PHYInitState.INIT_IDLE
    state_enter_cycle: int = 0
    calibration_count: int = 0
    error_count: int = 0
    warnings: List[str] = field(default_factory=list)


class PHYTrainingError(Exception):
    """Exception raised for PHY training errors"""
    pass


class PHYInitError(Exception):
    """Exception raised for PHY initialization errors"""
    pass


class PHYTrainingStateMachine:
    """PHY Training State Machine

    Implements the training sequence state machine (PH-004)
    for HBM4 PHY calibration.

    Training sequence follows JEDEC HBM4 specification:
    1. Initialize training
    2. Read DQS training
    3. Write leveling
    4. Read margin training
    5. Write margin training
    6. Read DQ training
    7. Write DQ training
    8. VREF CA training
    9. VREF DQ training
    10. Verify and complete
    """

    # Training phase sequence order (JEDEC JESD270-4A)
    # Includes PAM3 training for HBM4E @ 16 GT/s
    TRAINING_SEQUENCE = [
        TrainingPhase.TRAIN_RD_DQS,
        TrainingPhase.TRAIN_WR_LEVELING,
        TrainingPhase.TRAIN_RD_DQ,
        TrainingPhase.TRAIN_RD_DQ_EYE,
        TrainingPhase.TRAIN_WR_DQ,
        TrainingPhase.TRAIN_WR_DQ_EYE,
        TrainingPhase.TRAIN_GATE,
        TrainingPhase.TRAIN_GATE_DELAY,
        TrainingPhase.TRAIN_VREF_CA,
        TrainingPhase.TRAIN_VREF_DQ,
        # PAM3 training phases (HBM4E)
        TrainingPhase.TRAIN_PAM3_INIT,
        TrainingPhase.TRAIN_PAM3_VREF,
        TrainingPhase.TRAIN_PAM3_EYE,
        TrainingPhase.TRAIN_PAM3_DFE,
        TrainingPhase.TRAIN_PAM3_VERIFY,
    ]

    # PAM3 training phase sequence (separate sequence for clarity)
    PAM3_TRAINING_SEQUENCE = [
        PAM3TrainingState.PAM3_INIT,
        PAM3TrainingState.PAM3_VREF_CAL,
        PAM3TrainingState.PAM3_EYE_TRAINING,
        PAM3TrainingState.PAM3_DFE_TAPS,
        PAM3TrainingState.PAM3_MARGIN_VERIFY,
    ]

    # Default timeout per training phase (cycles @ 8 GT/s)
    # Based on JEDEC HBM4 training time budget
    DEFAULT_TIMEOUT_CYCLES = 50000  # ~5ms @ 10ns cycle

    def __init__(self, channel_id: int = 0,
                 dfi_interface=None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize PHY training state machine

        Args:
            channel_id: Channel index for this training instance
            dfi_interface: Optional DFI 5.0 interface for integration
            config: Optional configuration dictionary
        """
        self.channel_id = channel_id
        self.dfi = dfi_interface

        # Configuration
        self.config = config or {}
        self.timeout_cycles = self.config.get('timeout_cycles',
                                              self.DEFAULT_TIMEOUT_CYCLES)
        self.enable_retry = self.config.get('enable_retry', True)
        self.verify_results = self.config.get('verify_results', True)

        # HBM4 PAM3 configuration
        self.pam3_enabled = self.config.get('pam3_enabled', False)
        self.pam3_config = PAM3SignalConfig() if self.pam3_enabled else None
        self._pam3_state = PAM3TrainingState.PAM3_INIT

        # State tracking
        self.status = TrainingStatus()
        self.params = TrainingParameters()
        self.dfi_control = DFI5TrainingControl()

        # Set PAM3 parameters if enabled
        if self.pam3_enabled:
            self.params.pam3_enabled = True

        # Cycle counter
        self._cycle = 0

        # Training patterns (PRBS, walking 1/0, PAM3 patterns, etc.)
        self._training_patterns = self._init_training_patterns()

        # Lane data for per-lane calibration
        self._lane_count = 64  # HBM4: 64 lanes per channel

    def _init_training_patterns(self) -> Dict[str, List[int]]:
        """Initialize training test patterns

        Returns:
            Dictionary of training patterns including PAM3 patterns for HBM4
        """
        # PRBS-7 pattern
        prbs7 = []
        lfsr = 0x7F
        for _ in range(128):
            prbs7.append((lfsr >> 6) & 1)
            new_bit = ((lfsr >> 6) ^ (lfsr >> 5)) & 1
            lfsr = ((lfsr << 1) | new_bit) & 0x7F

        # PRBS-9 pattern (for longer patterns)
        prbs9 = []
        lfsr9 = 0x1FF
        for _ in range(256):
            prbs9.append((lfsr9 >> 8) & 1)
            new_bit = ((lfsr9 >> 8) ^ (lfsr9 >> 4)) & 1
            lfsr9 = ((lfsr9 << 1) | new_bit) & 0x1FF

        # Walking 1 pattern
        walking_1 = [1 << i for i in range(64)]

        # Walking 0 pattern
        walking_0 = [~(1 << i) & 0xFFFF for i in range(64)]

        # All ones / zeros
        all_ones = [0xFFFF] * 64
        all_zeros = [0x0000] * 64

        # PAM3 training patterns (3-level patterns)
        # PAM3 uses ternary values: -1, 0, +1 encoded as 0, 1, 2
        pam3_all_high = [2] * 64      # All +1 levels
        pam3_all_mid = [1] * 64       # All 0 levels
        pam3_all_low = [0] * 64       # All -1 levels

        # PAM3 alternating pattern (for eye training)
        pam3_alternate = [2 if i % 2 == 0 else 0 for i in range(64)]

        # PAM3 walking 1 in ternary (walks +1 level through lanes)
        pam3_walking_high = []
        for i in range(64):
            pattern = [1] * 64  # Start with all 0
            pattern[i] = 2      # Set +1 level
            pam3_walking_high.append(sum(pattern[j] << (j * 2) for j in range(min(32, len(pattern)))))

        # PAM3 mixed pattern for DFE training
        pam3_mixed = []
        for i in range(128):
            # Mix of levels for DFE convergence
            pam3_mixed.append(i % 3)

        return {
            'prbs7': prbs7,
            'prbs9': prbs9,
            'walking_1': walking_1,
            'walking_0': walking_0,
            'all_ones': all_ones,
            'all_zeros': all_zeros,
            # PAM3 patterns
            'pam3_all_high': pam3_all_high,
            'pam3_all_mid': pam3_all_mid,
            'pam3_all_low': pam3_all_low,
            'pam3_alternate': pam3_alternate,
            'pam3_walking_high': pam3_walking_high,
            'pam3_mixed': pam3_mixed,
        }

    @property
    def cycle(self) -> int:
        """Current simulation cycle"""
        return self._cycle

    def tick(self):
        """Advance training state machine by one cycle

        Call this once per cycle to update state machine.
        """
        self._cycle += 1

        # Update phase timer
        if self.status.current_phase != TrainingPhase.TRAIN_IDLE:
            elapsed = self._cycle - self.status.phase_start_cycle
            if elapsed > self.timeout_cycles:
                self._handle_phase_timeout()

    def start_training(self) -> bool:
        """Start training sequence

        Returns:
            True if training started successfully
        """
        if self.status.current_phase not in [TrainingPhase.TRAIN_IDLE,
                                              TrainingPhase.TRAIN_COMPLETE,
                                              TrainingPhase.TRAIN_FAIL]:
            return False

        # Reset training state
        self.status.current_phase = TrainingPhase.TRAIN_START
        self.status.phase_start_cycle = self._cycle
        self.status.total_training_cycles = 0
        self.status.retry_count = 0
        self.status.results.clear()
        self.params = TrainingParameters()

        # Signal DFI interface
        if self.dfi:
            self.dfi.start_training()

        return True

    def _execute_phase(self, phase: TrainingPhase) -> bool:
        """Execute a training phase

        Args:
            phase: Training phase to execute

        Returns:
            True if phase completed successfully
        """
        phase_handlers = {
            TrainingPhase.TRAIN_RD_DQS: self._train_rd_dqs,
            TrainingPhase.TRAIN_WR_LEVELING: self._train_wr_leveling,
            TrainingPhase.TRAIN_RD_DQ: self._train_rd_dq,
            TrainingPhase.TRAIN_RD_DQ_EYE: self._train_rd_dq_eye,
            TrainingPhase.TRAIN_WR_DQ: self._train_wr_dq,
            TrainingPhase.TRAIN_WR_DQ_EYE: self._train_wr_dq_eye,
            TrainingPhase.TRAIN_GATE: self._train_gate,
            TrainingPhase.TRAIN_GATE_DELAY: self._train_gate_delay,
            TrainingPhase.TRAIN_VREF_CA: self._train_vref_ca,
            TrainingPhase.TRAIN_VREF_DQ: self._train_vref_dq,
            # PAM3 training phases
            TrainingPhase.TRAIN_PAM3_INIT: self._train_pam3_init,
            TrainingPhase.TRAIN_PAM3_VREF: self._train_pam3_vref,
            TrainingPhase.TRAIN_PAM3_EYE: self._train_pam3_eye,
            TrainingPhase.TRAIN_PAM3_DFE: self._train_pam3_dfe,
            TrainingPhase.TRAIN_PAM3_VERIFY: self._train_pam3_verify,
        }

        handler = phase_handlers.get(phase)
        if handler:
            return handler()

        return False

    def _train_rd_dqs(self) -> bool:
        """Execute Read DQS training

        Finds optimal DQS sampling position for reads.

        Returns:
            True if training passed
        """
        # Send training request via DFI
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_RD_DQS)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        # Simulate DQS delay sweep
        best_delay = 0
        best_margin = 0.0

        for delay in range(64):  # 64 tap sweep
            margin = self._measure_rd_dqs_margin(delay)
            if margin > best_margin:
                best_margin = margin
                best_delay = delay

        self.params.rd_dqs_delay = best_delay

        # Verify result
        if best_margin < 0.1:  # Minimum margin threshold
            self.params.training_errors.append("RD DQS margin too small")
            return False

        return True

    def _train_wr_leveling(self) -> bool:
        """Execute Write Leveling training

        Aligns write DQS with data.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_WR_LEVELING)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        # Find optimal write leveling delay
        best_delay = 0
        best_margin = 0.0

        for delay in range(64):
            margin = self._measure_wr_level_margin(delay)
            if margin > best_margin:
                best_margin = margin
                best_delay = delay

        self.params.wr_level_delay = best_delay

        if best_margin < 0.1:
            self.params.training_errors.append("WR leveling margin too small")
            return False

        return True

    def _train_rd_dq(self) -> bool:
        """Execute Read DQ Training (RDDQ)

        Per-lane DQ delay calibration for read data capture.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_RD_DQ)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        # Per-lane calibration
        for lane in range(self._lane_count):
            best_delay = self._calibrate_lane_rd(lane)
            self.params.lane_delays[lane] = best_delay

        return True

    def _train_rd_dq_eye(self) -> bool:
        """Execute Read DQ Eye Center Training

        Fine-tunes read DQ delay for optimal data eye center.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_RD_DQ_EYE)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        # Fine-tune around best delay found in RD_DQ
        best_margin = 0.0
        for lane in range(self._lane_count):
            base_delay = self.params.lane_delays.get(lane, 32)

            # Sweep around base delay
            for offset in range(-8, 9):
                delay = base_delay + offset
                if 0 <= delay <= 63:
                    margin = self._measure_rd_dq_margin(delay)
                    if margin > best_margin:
                        best_margin = margin
                        self.params.lane_delays[lane] = delay

        self.params.rd_margin = best_margin

        if best_margin < 0.15:
            self.params.training_errors.append("RD DQ eye center training failed")
            return False

        return True

    def _train_wr_dq(self) -> bool:
        """Execute Write DQ Training (WDQ)

        Per-lane write DQ delay calibration.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_WR_DQ)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        for lane in range(self._lane_count):
            best_delay = self._calibrate_lane_wr(lane)
            self.params.lane_delays[lane + self._lane_count] = best_delay

        return True

    def _train_wr_dq_eye(self) -> bool:
        """Execute Write DQ Eye Center Training

        Fine-tunes write DQ delay for optimal data eye center.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_WR_DQ_EYE)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        # Fine-tune around best delay found in WR_DQ
        best_margin = 0.0
        for lane in range(self._lane_count):
            base_delay = self.params.lane_delays.get(lane + self._lane_count, 32)

            # Sweep around base delay
            for offset in range(-8, 9):
                delay = base_delay + offset
                if 0 <= delay <= 63:
                    margin = self._measure_wr_dq_margin(delay)
                    if margin > best_margin:
                        best_margin = margin
                        self.params.lane_delays[lane + self._lane_count] = delay

        self.params.wr_margin = best_margin

        if best_margin < 0.15:
            self.params.training_errors.append("WR DQ eye center training failed")
            return False

        return True

    def _train_gate(self) -> bool:
        """Execute Gate Training

        Trains read gate timing to properly capture data.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_GATE)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        best_delay = 0
        best_margin = 0.0

        for delay in range(64):
            margin = self._measure_gate_margin(delay)
            if margin > best_margin:
                best_margin = margin
                best_delay = delay

        self.params.rd_dqs_gate_delay = best_delay

        if best_margin < 0.1:
            self.params.training_errors.append("Gate training margin too small")
            return False

        return True

    def _train_gate_delay(self) -> bool:
        """Execute Gate Delay Optimization

        Fine-tunes gate delay for optimal timing.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_GATE_DELAY)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        base_delay = self.params.rd_dqs_gate_delay
        best_delay = base_delay
        best_margin = 0.0

        # Fine sweep around base delay
        for offset in range(-4, 5):
            delay = base_delay + offset
            if 0 <= delay <= 63:
                margin = self._measure_gate_margin(delay)
                if margin > best_margin:
                    best_margin = margin
                    best_delay = delay

        self.params.rd_dqs_gate_delay = best_delay

        if best_margin < 0.12:
            self.params.training_errors.append("Gate delay optimization failed")
            return False

        return True

    def _train_vref_ca(self) -> bool:
        """Execute VREF CA Training

        Trains CA interface VREF.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_VREF_CA)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        best_vref = 32
        best_margin = 0.0

        # Sweep VREF DAC range (0-63 for 6-bit DAC)
        for vref in range(VREF_CA_MIN, VREF_CA_MAX + 1):
            margin = self._measure_ca_vref_margin(vref)
            if margin > best_margin:
                best_margin = margin
                best_vref = vref

        # Validate VREF result
        self.params.ca_vref = best_vref
        if not self._validate_vref_result(best_vref, "CA"):
            return False

        if best_margin < 0.1:
            self.params.training_errors.append("VREF CA training failed")
            return False

        return True

    def _train_vref_dq(self) -> bool:
        """Execute VREF DQ Training

        Trains DQ interface VREF.

        Returns:
            True if training passed
        """
        tra_req, tra_mode, tra_type = self.dfi_control.encode_training_cmd(
            TrainingPhase.TRAIN_VREF_DQ)
        self.dfi_control.tra_req = tra_req
        self.dfi_control.tra_mode = tra_mode
        self.dfi_control.tra_type = tra_type

        # DQ VREF calibrated in margin training - validate stored results
        if hasattr(self.params, 'rd_vref') and not self._validate_vref_result(self.params.rd_vref, "DQ"):
            return False
        if hasattr(self.params, 'wr_vref') and not self._validate_vref_result(self.params.wr_vref, "DQ"):
            return False

        return True

    # =========================================================================
    # PAM3 Training Methods (HBM4E Support)
    # =========================================================================

    def _train_pam3_init(self) -> bool:
        """Execute PAM3 Training Initialization

        Initializes PAM3 training mode and configures the PHY for
        3-level signaling training.

        Returns:
            True if initialization passed
        """
        if not self.pam3_enabled:
            # PAM3 not enabled, skip
            self._pam3_state = PAM3TrainingState.PAM3_COMPLETE
            return True

        # Set PAM3 training mode via DFI
        self.dfi_control.pam3_training_req = True

        # Initialize PAM3 state
        self._pam3_state = PAM3TrainingState.PAM3_INIT
        self.pam3_config = PAM3SignalConfig()

        # Configure DFI for PAM3 mode
        if hasattr(self.dfi, 'set_pam3_mode'):
            self.dfi.set_pam3_mode(True)

        # Initialize VREF to mid-range
        self.params.pam3_upper_vref = PAM3_VREF_MID
        self.params.pam3_lower_vref = PAM3_VREF_MID

        return True

    def _train_pam3_vref(self) -> bool:
        """Execute PAM3 VREF Calibration

        Calibrates the upper and lower VREF thresholds for 3-level signaling.
        This is critical for proper PAM3 eye opening.

        Returns:
            True if VREF calibration passed
        """
        if not self.pam3_enabled:
            return True

        self._pam3_state = PAM3TrainingState.PAM3_VREF_CAL
        self.dfi_control.pam3_vref_req = True

        # Encode PAM3 training command
        req, subtype = self.dfi_control.encode_pam3_training_cmd(
            PAM3TrainingState.PAM3_VREF_CAL)
        self.dfi_control.pam3_training_req = req

        # Sweep upper VREF threshold
        best_upper_vref = PAM3_VREF_MID
        best_upper_margin = 0.0

        for vref in range(PAM3_VREF_HIGH_MIN, PAM3_VREF_HIGH_MAX):
            margin = self._measure_pam3_upper_margin(vref)
            if margin > best_upper_margin:
                best_upper_margin = margin
                best_upper_vref = vref

        self.params.pam3_upper_vref = best_upper_vref
        self.pam3_config.vref_high = best_upper_vref

        # Sweep lower VREF threshold
        best_lower_vref = PAM3_VREF_MID
        best_lower_margin = 0.0

        for vref in range(PAM3_VREF_LOW_MIN, PAM3_VREF_LOW_MAX):
            margin = self._measure_pam3_lower_margin(vref)
            if margin > best_lower_margin:
                best_lower_margin = margin
                best_lower_vref = vref

        self.params.pam3_lower_vref = best_lower_vref
        self.pam3_config.vref_low = best_lower_vref

        # Validate PAM3 VREF settings
        if not self.pam3_config.validate_vref_settings():
            self.params.training_errors.extend(self.pam3_config.errors)
            return False

        # Check margins
        if best_upper_margin < PAM3_VERTICAL_EYE_MARGIN:
            self.params.training_errors.append(
                f"PAM3 upper eye margin ({best_upper_margin:.2f}) too small")
            return False

        if best_lower_margin < PAM3_VERTICAL_EYE_MARGIN:
            self.params.training_errors.append(
                f"PAM3 lower eye margin ({best_lower_margin:.2f}) too small")
            return False

        return True

    def _train_pam3_eye(self) -> bool:
        """Execute PAM3 Eye Diagram Training

        Optimizes timing delays for maximum PAM3 eye opening.
        Trains per-lane to maximize eye margins.

        Returns:
            True if eye training passed
        """
        if not self.pam3_enabled:
            return True

        self._pam3_state = PAM3TrainingState.PAM3_EYE_TRAINING

        # Encode PAM3 training command
        req, subtype = self.dfi_control.encode_pam3_training_cmd(
            PAM3TrainingState.PAM3_EYE_TRAINING)
        self.dfi_control.pam3_training_req = req

        # Per-lane PAM3 eye training
        best_upper_margin = 0.0
        best_lower_margin = 0.0

        for lane in range(self._lane_count):
            # Sweep delay for this lane
            best_delay = 32
            best_lane_margin = 0.0

            for delay in range(64):
                margin = self._measure_pam3_eye_margin(delay)
                if margin > best_lane_margin:
                    best_lane_margin = margin
                    best_delay = delay

            self.params.lane_delays[f'pam3_{lane}'] = best_delay

            # Track best margins
            upper_margin = self._measure_pam3_upper_margin(
                self.params.pam3_upper_vref)
            lower_margin = self._measure_pam3_lower_margin(
                self.params.pam3_lower_vref)
            best_upper_margin = max(best_upper_margin, upper_margin)
            best_lower_margin = max(best_lower_margin, lower_margin)

        self.params.pam3_upper_margin = best_upper_margin
        self.params.pam3_lower_margin = best_lower_margin

        # Check minimum PAM3 eye margins
        if best_upper_margin < PAM3_UPPER_EYE_MARGIN:
            self.params.training_errors.append(
                f"PAM3 upper eye margin ({best_upper_margin:.2f}) below threshold")
            return False

        if best_lower_margin < PAM3_LOWER_EYE_MARGIN:
            self.params.training_errors.append(
                f"PAM3 lower eye margin ({best_lower_margin:.2f}) below threshold")
            return False

        return True

    def _train_pam3_dfe(self) -> bool:
        """Execute PAM3 DFE Tap Training

        Trains DFE (Decision Feedback Equalizer) tap coefficients
        for improved PAM3 signal recovery.

        Returns:
            True if DFE training passed
        """
        if not self.pam3_enabled:
            return True

        self._pam3_state = PAM3TrainingState.PAM3_DFE_TAPS
        self.dfi_control.pam3_dfe_req = True

        # Encode PAM3 training command
        req, subtype = self.dfi_control.encode_pam3_training_cmd(
            PAM3TrainingState.PAM3_DFE_TAPS)
        self.dfi_control.pam3_training_req = req

        # Initialize DFE taps
        dfe_taps = [0.0] * PAM3_DFE_NUM_TAPS

        # LMS-based DFE tap training
        for iteration in range(100):  # Max iterations
            tap_updates = [0.0] * PAM3_DFE_NUM_TAPS

            # Measure error and update taps
            for tap_idx in range(PAM3_DFE_NUM_TAPS):
                # Test tap adjustment
                tap_test = dfe_taps.copy()
                tap_test[tap_idx] += PAM3_DFE_CONVERGENCE_RATE

                # Clamp to max tap weight
                tap_test[tap_idx] = min(
                    tap_test[tap_idx], PAM3_DFE_MAX_TAP_WEIGHT)

                # Measure BER with adjusted tap
                ber = self._measure_pam3_ber(tap_test)

                # Update tap based on error
                tap_delta = self._calculate_dfe_tap_delta(
                    tap_idx, dfe_taps[tap_idx], ber)
                tap_updates[tap_idx] = tap_delta

            # Apply tap updates
            for tap_idx in range(PAM3_DFE_NUM_TAPS):
                new_tap = dfe_taps[tap_idx] + tap_updates[tap_idx]
                # Clamp
                new_tap = max(-PAM3_DFE_MAX_TAP_WEIGHT,
                             min(PAM3_DFE_MAX_TAP_WEIGHT, new_tap))
                dfe_taps[tap_idx] = new_tap

            # Check convergence
            if all(abs(u) < 0.001 for u in tap_updates):
                break

        self.params.pam3_dfe_taps = dfe_taps
        self.pam3_config.dfe_taps = dfe_taps

        return True

    def _train_pam3_verify(self) -> bool:
        """Execute PAM3 Margin Verification

        Verifies that all PAM3 margins meet minimum requirements.

        Returns:
            True if verification passed
        """
        if not self.pam3_enabled:
            return True

        self._pam3_state = PAM3TrainingState.PAM3_MARGIN_VERIFY

        # Final PAM3 margin measurement
        upper_margin = self._measure_pam3_upper_margin(
            self.params.pam3_upper_vref)
        lower_margin = self._measure_pam3_lower_margin(
            self.params.pam3_lower_vref)

        self.params.pam3_upper_margin = upper_margin
        self.params.pam3_lower_margin = lower_margin

        # Verify margins
        if upper_margin < PAM3_UPPER_EYE_MARGIN:
            self.params.training_errors.append(
                f"PAM3 upper margin verification failed: {upper_margin:.2f}")
            return False

        if lower_margin < PAM3_LOWER_EYE_MARGIN:
            self.params.training_errors.append(
                f"PAM3 lower margin verification failed: {lower_margin:.2f}")
            return False

        # Verify PAM3 VREF settings
        if not self.pam3_config.validate_vref_settings():
            self.params.training_errors.extend(self.pam3_config.errors)
            return False

        # Mark PAM3 training complete
        self._pam3_state = PAM3TrainingState.PAM3_COMPLETE
        self.params.pam3_training_complete = True
        self.pam3_config.training_complete = True
        self.pam3_config.training_passed = True

        return True

    # =========================================================================
    # PAM3 Measurement Helpers
    # =========================================================================

    def _measure_pam3_upper_margin(self, vref: int) -> float:
        """Measure PAM3 upper eye margin at given VREF

        Args:
            vref: Upper VREF threshold setting

        Returns:
            Margin as fraction of UI (0.0 to 1.0)
        """
        import random
        # PAM3 upper eye is between ZERO and HIGH levels
        # Centered around the upper VREF
        noise = random.uniform(-0.03, 0.03)
        margin = PAM3_UPPER_EYE_MARGIN - abs(vref - PAM3_VREF_MID) / 128 + noise
        return max(0.0, min(1.0, margin))

    def _measure_pam3_lower_margin(self, vref: int) -> float:
        """Measure PAM3 lower eye margin at given VREF

        Args:
            vref: Lower VREF threshold setting

        Returns:
            Margin as fraction of UI (0.0 to 1.0)
        """
        import random
        # PAM3 lower eye is between LOW and ZERO levels
        noise = random.uniform(-0.03, 0.03)
        margin = PAM3_LOWER_EYE_MARGIN - abs(vref - PAM3_VREF_MID) / 128 + noise
        return max(0.0, min(1.0, margin))

    def _measure_pam3_eye_margin(self, delay: int) -> float:
        """Measure PAM3 eye margin at given delay tap

        Args:
            delay: Delay tap value

        Returns:
            Combined eye margin (UI fraction)
        """
        import random
        noise = random.uniform(-0.04, 0.04)
        # PAM3 eye training considers both upper and lower eyes
        upper = 0.3 - abs(delay - 32) / 96 + noise
        lower = 0.25 - abs(delay - 32) / 96 + noise
        return max(0.0, min(1.0, (upper + lower) / 2))

    def _measure_pam3_ber(self, dfe_taps: List[float]) -> float:
        """Measure PAM3 bit error rate with given DFE taps

        Args:
            dfe_taps: List of DFE tap coefficients

        Returns:
            Estimated BER
        """
        import random
        # Simulate BER with DFE tap adjustment
        # Better taps = lower BER
        tap_quality = sum(abs(t) for t in dfe_taps) / len(dfe_taps)
        noise = random.uniform(-0.0001, 0.0001)
        ber = 1e-6 * (1 + tap_quality * 10) + noise
        return max(1e-10, min(1.0, ber))

    def _calculate_dfe_tap_delta(self, tap_idx: int, current_tap: float,
                                  ber: float) -> float:
        """Calculate DFE tap update delta

        Args:
            tap_idx: DFE tap index
            current_tap: Current tap value
            ber: Measured BER

        Returns:
            Tap delta for update
        """
        import random
        # LMS-based tap update
        sign = 1 if random.random() > 0.5 else -1
        delta = sign * PAM3_DFE_CONVERGENCE_RATE * (1 - ber)
        return delta

    # === Measurement helpers ===

    def _validate_vref(self, vref: int, vref_type: str = "DQ") -> bool:
        """Validate VREF setting is within valid range

        Args:
            vref: VREF DAC setting to validate
            vref_type: Type of VREF ("CA" or "DQ")

        Returns:
            True if VREF is valid

        Raises:
            ValueError: If VREF is out of range
        """
        if vref_type == "CA":
            vref_min = VREF_CA_MIN
            vref_max = VREF_CA_MAX
        else:
            vref_min = VREF_DQ_MIN
            vref_max = VREF_DQ_MAX

        if not (vref_min <= vref <= vref_max):
            raise ValueError(
                f"Invalid {vref_type} VREF value {vref}: "
                f"must be in range [{vref_min}, {vref_max}]"
            )
        return True

    def _validate_vref_result(self, vref: int, vref_type: str = "DQ") -> bool:
        """Validate VREF training result

        Args:
            vref: VREF DAC setting from training
            vref_type: Type of VREF ("CA" or "DQ")

        Returns:
            True if VREF is within valid range
        """
        try:
            self._validate_vref(vref, vref_type)
        except ValueError:
            self.params.training_errors.append(
                f"{vref_type} VREF training resulted in invalid value: {vref}"
            )
            return False
        return True

    def _measure_rd_dqs_margin(self, delay: int) -> float:
        """Measure read DQS margin for given delay

        Args:
            delay: DQS delay tap value

        Returns:
            Margin as fraction of UI (0.0 to 1.0)
        """
        # Simulate margin measurement
        # Real implementation would send patterns and measure errors
        import random
        noise = random.uniform(-0.05, 0.05)
        margin = 0.5 - abs(delay - 32) / 64 + noise
        return max(0.0, min(1.0, margin))

    def _measure_wr_level_margin(self, delay: int) -> float:
        """Measure write leveling margin

        Args:
            delay: Write leveling delay tap

        Returns:
            Margin as fraction of UI
        """
        import random
        noise = random.uniform(-0.05, 0.05)
        margin = 0.5 - abs(delay - 32) / 64 + noise
        return max(0.0, min(1.0, margin))

    def _measure_rd_dq_margin(self, delay: int) -> float:
        """Measure read DQ margin for given delay

        Args:
            delay: DQ delay tap value

        Returns:
            Margin as fraction of UI (0.0 to 1.0)
        """
        import random
        noise = random.uniform(-0.04, 0.04)
        margin = 0.5 - abs(delay - 32) / 64 + noise
        return max(0.0, min(1.0, margin))

    def _measure_wr_dq_margin(self, delay: int) -> float:
        """Measure write DQ margin for given delay

        Args:
            delay: Write DQ delay tap value

        Returns:
            Margin as fraction of UI
        """
        import random
        noise = random.uniform(-0.04, 0.04)
        margin = 0.5 - abs(delay - 32) / 64 + noise
        return max(0.0, min(1.0, margin))

    def _measure_gate_margin(self, delay: int) -> float:
        """Measure gate training margin

        Args:
            delay: Gate delay tap value

        Returns:
            Margin as fraction of UI
        """
        import random
        noise = random.uniform(-0.05, 0.05)
        margin = 0.5 - abs(delay - 32) / 64 + noise
        return max(0.0, min(1.0, margin))

    def _measure_rd_margin(self, vref: int) -> float:
        """Measure read margin at given VREF

        Args:
            vref: VREF setting

        Returns:
            Margin as fraction of UI
        """
        import random
        # VREF centered around 32
        noise = random.uniform(-0.03, 0.03)
        margin = 0.5 - abs(vref - 32) / 128 + noise
        return max(0.0, min(1.0, margin))

    def _measure_wr_margin(self, vref: int) -> float:
        """Measure write margin at given VREF

        Args:
            vref: VREF setting

        Returns:
            Margin as fraction of UI
        """
        import random
        noise = random.uniform(-0.03, 0.03)
        margin = 0.5 - abs(vref - 32) / 128 + noise
        return max(0.0, min(1.0, margin))

    def _measure_ca_vref_margin(self, vref: int) -> float:
        """Measure CA VREF margin

        Args:
            vref: CA VREF setting

        Returns:
            Margin as fraction of UI
        """
        import random
        noise = random.uniform(-0.04, 0.04)
        margin = 0.5 - abs(vref - 32) / 128 + noise
        return max(0.0, min(1.0, margin))

    def _calibrate_lane_rd(self, lane: int) -> int:
        """Calibrate read delay for a single lane

        Args:
            lane: Lane index

        Returns:
            Optimal delay tap value
        """
        import random
        # Find best delay for this lane
        best_delay = random.randint(28, 36)  # Simulated optimal
        return best_delay

    def _calibrate_lane_wr(self, lane: int) -> int:
        """Calibrate write delay for a single lane

        Args:
            lane: Lane index

        Returns:
            Optimal delay tap value
        """
        import random
        best_delay = random.randint(28, 36)
        return best_delay

    def _handle_phase_timeout(self):
        """Handle training phase timeout"""
        self.status.results[self.status.current_phase] = TrainingResult.FAIL_TIMEOUT
        self.params.training_errors.append(
            f"Timeout in phase {self.status.current_phase.name}"
        )

        if self.enable_retry and self.status.retry_count < self.status.max_retries:
            self.status.retry_count += 1
            self.status.current_phase = TrainingPhase.TRAIN_INIT
        else:
            self.status.current_phase = TrainingPhase.TRAIN_FAIL

    def _advance_to_next_phase(self):
        """Advance to next training phase in sequence"""
        try:
            current_idx = self.TRAINING_SEQUENCE.index(self.status.current_phase)
            if current_idx < len(self.TRAINING_SEQUENCE) - 1:
                next_phase = self.TRAINING_SEQUENCE[current_idx + 1]
                self.status.current_phase = next_phase
                self.status.phase_start_cycle = self._cycle
            else:
                # Training sequence complete
                self.status.current_phase = TrainingPhase.TRAIN_VERIFY
        except ValueError:
            # Not in sequence, move to first phase
            if self.TRAINING_SEQUENCE:
                self.status.current_phase = self.TRAINING_SEQUENCE[0]
                self.status.phase_start_cycle = self._cycle

    def process_training_cycle(self) -> bool:
        """Process one training cycle

        Main state machine advancement logic.

        Returns:
            True if training completed successfully
        """
        current = self.status.current_phase

        if current == TrainingPhase.TRAIN_IDLE:
            # Waiting for training start
            pass

        elif current == TrainingPhase.TRAIN_START:
            # Initialize training
            self.status.current_phase = TrainingPhase.TRAIN_INIT
            self.status.phase_start_cycle = self._cycle

        elif current == TrainingPhase.TRAIN_INIT:
            # Move to first training phase
            if self.TRAINING_SEQUENCE:
                self.status.current_phase = self.TRAINING_SEQUENCE[0]
                self.status.phase_start_cycle = self._cycle

        elif current in self.TRAINING_SEQUENCE:
            # Execute current phase
            success = self._execute_phase(current)
            if success:
                self.status.results[current] = TrainingResult.SUCCESS
                self._advance_to_next_phase()
            else:
                self.status.results[current] = TrainingResult.FAIL_MARGIN
                if self.enable_retry and self.status.retry_count < self.status.max_retries:
                    self.status.retry_count += 1
                    # Retry current phase
                    self.status.phase_start_cycle = self._cycle
                else:
                    self.status.current_phase = TrainingPhase.TRAIN_FAIL

        elif current == TrainingPhase.TRAIN_VERIFY:
            # Verify training results
            if self.verify_results:
                verified = self._verify_training_results()
                if verified:
                    self.status.current_phase = TrainingPhase.TRAIN_COMPLETE
                    self.params.training_passed = True
                else:
                    self.status.results[current] = TrainingResult.FAIL_VERIFY
                    self.status.current_phase = TrainingPhase.TRAIN_FAIL
            else:
                self.status.current_phase = TrainingPhase.TRAIN_COMPLETE
                self.params.training_passed = True

        elif current == TrainingPhase.TRAIN_COMPLETE:
            # Training complete
            if self.dfi:
                self.dfi.complete_training()
            return True

        elif current == TrainingPhase.TRAIN_FAIL:
            # Training failed
            return False

        return False

    def _verify_training_results(self) -> bool:
        """Verify all training results

        Returns:
            True if all results meet requirements
        """
        # Check that all phases passed
        for phase in self.TRAINING_SEQUENCE:
            result = self.status.results.get(phase)
            if result != TrainingResult.SUCCESS:
                return False

        # Check parameter validity
        if self.params.rd_vref < 0 or self.params.rd_vref > 63:
            return False
        if self.params.wr_vref < 0 or self.params.wr_vref > 63:
            return False

        # Check margins
        if self.params.rd_margin < 0.1 or self.params.wr_margin < 0.1:
            return False

        # Verify PAM3 training results if enabled
        if self.pam3_enabled:
            # Check PAM3 VREF settings
            if not (PAM3_VREF_DAC_RANGE[0] <= self.params.pam3_upper_vref <= PAM3_VREF_DAC_RANGE[1]):
                return False
            if not (PAM3_VREF_DAC_RANGE[0] <= self.params.pam3_lower_vref <= PAM3_VREF_DAC_RANGE[1]):
                return False

            # Check PAM3 margins
            if self.params.pam3_upper_margin < PAM3_UPPER_EYE_MARGIN:
                return False
            if self.params.pam3_lower_margin < PAM3_LOWER_EYE_MARGIN:
                return False

            # Verify PAM3 training complete
            if not self.params.pam3_training_complete:
                return False

        return True

    def get_training_results(self) -> Dict[str, Any]:
        """Get training results summary

        Returns:
            Dictionary with training results
        """
        result = {
            'channel_id': self.channel_id,
            'passed': self.params.training_passed,
            'current_phase': self.status.current_phase.name,
            'total_cycles': self._cycle,
            'retry_count': self.status.retry_count,
            'results': {p.name: r.name for p, r in self.status.results.items()},
            'parameters': {
                'rd_dqs_delay': self.params.rd_dqs_delay,
                'wr_level_delay': self.params.wr_level_delay,
                'rd_vref': self.params.rd_vref,
                'wr_vref': self.params.wr_vref,
                'ca_vref': self.params.ca_vref,
                'rd_margin': self.params.rd_margin,
                'wr_margin': self.params.wr_margin,
            },
            'errors': self.params.training_errors,
        }

        # Include PAM3 results if enabled
        if self.pam3_enabled:
            result['pam3'] = {
                'enabled': self.pam3_enabled,
                'training_complete': self.params.pam3_training_complete,
                'upper_vref': self.params.pam3_upper_vref,
                'lower_vref': self.params.pam3_lower_vref,
                'upper_margin': self.params.pam3_upper_margin,
                'lower_margin': self.params.pam3_lower_margin,
                'dfe_taps': self.params.pam3_dfe_taps,
                'pam3_state': self._pam3_state.name,
            }

        return result

    def is_training_complete(self) -> bool:
        """Check if training is complete

        Returns:
            True if training reached terminal state
        """
        return self.status.current_phase in [TrainingPhase.TRAIN_COMPLETE,
                                              TrainingPhase.TRAIN_FAIL]

    def is_training_passed(self) -> bool:
        """Check if training passed

        Returns:
            True if training completed successfully
        """
        return self.status.current_phase == TrainingPhase.TRAIN_COMPLETE

    def start_loopback_test(self) -> bool:
        """Signal start of loopback test from loopback controller

        This is called by the loopback controller when starting
        a loopback test sequence.

        Returns:
            True if loopback test can proceed
        """
        # If training is complete, allow loopback test
        if self.is_training_passed():
            return True
        # If training is in progress, don't allow loopback
        return False

    def get_loopback_ready_status(self) -> Dict[str, Any]:
        """Get status for loopback test readiness

        Returns:
            Dictionary with loopback readiness information
        """
        status = {
            'training_complete': self.is_training_passed(),
            'training_failed': self.status.current_phase == TrainingPhase.TRAIN_FAIL,
            'current_phase': self.status.current_phase.name,
            'coefficients': {
                'rd_dqs_delay': self.params.rd_dqs_delay,
                'wr_level_delay': self.params.wr_level_delay,
                'rd_vref': self.params.rd_vref,
                'wr_vref': self.params.wr_vref,
                'ca_vref': self.params.ca_vref,
                'rd_margin': self.params.rd_margin,
                'wr_margin': self.params.wr_margin,
            },
            'lane_count': self._lane_count,
        }

        # Include PAM3 coefficients if enabled
        if self.pam3_enabled:
            status['pam3_coefficients'] = {
                'upper_vref': self.params.pam3_upper_vref,
                'lower_vref': self.params.pam3_lower_vref,
                'upper_margin': self.params.pam3_upper_margin,
                'lower_margin': self.params.pam3_lower_margin,
                'dfe_taps': self.params.pam3_dfe_taps,
                'pam3_training_complete': self.params.pam3_training_complete,
            }

        return status

    def get_pam3_status(self) -> Dict[str, Any]:
        """Get PAM3 training status

        Returns:
            Dictionary with PAM3 status information
        """
        if not self.pam3_enabled:
            return {
                'enabled': False,
                'message': 'PAM3 mode not enabled',
            }

        return {
            'enabled': True,
            'pam3_state': self._pam3_state.name,
            'training_complete': self.params.pam3_training_complete,
            'vref_settings': {
                'upper': self.params.pam3_upper_vref,
                'lower': self.params.pam3_lower_vref,
            },
            'margins': {
                'upper': self.params.pam3_upper_margin,
                'lower': self.params.pam3_lower_margin,
            },
            'dfe_taps': self.params.pam3_dfe_taps,
            'eye_center': self.pam3_config.calculate_eye_center() if self.pam3_config else None,
        }

    def set_pam3_mode(self, enabled: bool):
        """Enable or disable PAM3 mode

        Args:
            enabled: True to enable PAM3, False to disable
        """
        self.pam3_enabled = enabled
        if enabled and self.pam3_config is None:
            self.pam3_config = PAM3SignalConfig()
        self.params.pam3_enabled = enabled


class PHYInitializationStateMachine:
    """PHY Initialization State Machine (PH-003)

    Implements the initialization sequence from power-on
    to ready state for HBM4 PHY.

    Sequence:
    1. Power-up
    2. Reset
    3. Configuration
    4. Calibration
    5. Training
    6. Complete
    """

    # State transition timeout (cycles)
    STATE_TIMEOUT = 100000  # 100ms @ 1ns cycle

    def __init__(self, training_sm: Optional[PHYTrainingStateMachine] = None,
                 dfi_interface=None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize PHY initialization state machine

        Args:
            training_sm: Training state machine instance
            dfi_interface: Optional DFI 5.1 interface
            config: Optional configuration dictionary
        """
        self.training_sm = training_sm
        self.dfi = dfi_interface
        self.config = config or {}

        # Status tracking
        self.status = PHYInitStatus()
        self.training_sm_ref = training_sm

        # Configuration loaded from config
        self._config_loaded = False
        self._calibration_data: Dict[str, Any] = {}

        # Cycle counter
        self._cycle = 0

    @property
    def cycle(self) -> int:
        """Current simulation cycle"""
        return self._cycle

    @property
    def is_initialized(self) -> bool:
        """Check if initialization is complete"""
        return self.status.state == PHYInitState.INIT_COMPLETE

    @property
    def is_ready(self) -> bool:
        """Check if PHY is ready for operation"""
        return (self.is_initialized and
                (self.training_sm is None or self.training_sm.is_training_passed()))

    def tick(self):
        """Advance initialization state machine by one cycle"""
        self._cycle += 1

        # Update training state machine if exists
        if self.training_sm:
            self.training_sm.tick()

        # Check for state timeout
        elapsed = self._cycle - self.status.state_enter_cycle
        if elapsed > self.STATE_TIMEOUT:
            self._handle_state_timeout()

    def _handle_state_timeout(self):
        """Handle state timeout"""
        self.status.error_count += 1
        self.status.warnings.append(
            f"Timeout in state {self.status.state.name} at cycle {self._cycle}"
        )

    def start_initialization(self):
        """Start PHY initialization sequence"""
        if self.status.state != PHYInitState.INIT_IDLE:
            return

        self.status.state = PHYInitState.INIT_START
        self.status.state_enter_cycle = self._cycle
        self.status.error_count = 0
        self.status.warnings.clear()

    def process_init_cycle(self):
        """Process one initialization cycle

        Main state machine advancement logic.
        """
        current = self.status.state

        if current == PHYInitState.INIT_IDLE:
            # Waiting for initialization start
            pass

        elif current == PHYInitState.INIT_START:
            # Move to power-up
            self.status.state = PHYInitState.INIT_POWER_UP
            self.status.state_enter_cycle = self._cycle

        elif current == PHYInitState.INIT_POWER_UP:
            # Simulate power-up sequence
            # In real hardware, this involves voltage ramps, etc.
            if self._cycle - self.status.state_enter_cycle > 100:
                self.status.state = PHYInitState.INIT_RESET
                self.status.state_enter_cycle = self._cycle

        elif current == PHYInitState.INIT_RESET:
            # Simulate reset sequence
            if self._cycle - self.status.state_enter_cycle > 50:
                self.status.state = PHYInitState.INIT_CONFIG
                self.status.state_enter_cycle = self._cycle

        elif current == PHYInitState.INIT_CONFIG:
            # Load configuration
            if not self._config_loaded:
                self._load_configuration()
            if self._cycle - self.status.state_enter_cycle > 20:
                self.status.state = PHYInitState.INIT_CALIBRATE
                self.status.state_enter_cycle = self._cycle

        elif current == PHYInitState.INIT_CALIBRATE:
            # Run calibration
            if self._cycle - self.status.state_enter_cycle > 1000:
                self.status.calibration_count += 1
                self.status.state = PHYInitState.INIT_TRAINING
                self.status.state_enter_cycle = self._cycle

                # Start training if state machine exists
                if self.training_sm:
                    self.training_sm.start_training()

        elif current == PHYInitState.INIT_TRAINING:
            # Run training sequence
            if self.training_sm:
                complete = self.training_sm.process_training_cycle()
                if complete:
                    self.status.state = PHYInitState.INIT_COMPLETE
                    self.status.state_enter_cycle = self._cycle
            else:
                # No training, skip to complete
                self.status.state = PHYInitState.INIT_COMPLETE
                self.status.state_enter_cycle = self._cycle

        elif current == PHYInitState.INIT_COMPLETE:
            # Initialization complete
            pass

    def _load_configuration(self):
        """Load PHY configuration"""
        # Load default calibration data
        self._calibration_data = {
            'rd_vref': 32,
            'wr_vref': 32,
            'ca_vref': 32,
            'dqs_delay': 0,
            'dq_delays': {},
        }

        # Apply any config overrides
        if 'default_rd_vref' in self.config:
            self._calibration_data['rd_vref'] = self.config['default_rd_vref']
        if 'default_wr_vref' in self.config:
            self._calibration_data['wr_vref'] = self.config['default_wr_vref']

        self._config_loaded = True

    def get_initialization_status(self) -> Dict[str, Any]:
        """Get initialization status

        Returns:
            Dictionary with status information
        """
        status = {
            'state': self.status.state.name,
            'cycle': self._cycle,
            'calibration_count': self.status.calibration_count,
            'error_count': self.status.error_count,
            'warnings': list(self.status.warnings),
            'initialized': self.is_initialized,
            'ready': self.is_ready,
        }

        if self.training_sm:
            status['training'] = self.training_sm.get_training_results()

        return status

    def get_calibration_data(self) -> Dict[str, Any]:
        """Get calibration data

        Returns:
            Dictionary with calibration values
        """
        data = dict(self._calibration_data)

        # Always include default calibration data if config was loaded
        if not data and self._config_loaded:
            data = {
                'rd_vref': 32,
                'wr_vref': 32,
                'ca_vref': 32,
                'dqs_delay': 0,
                'dq_delays': {},
            }
            if 'default_rd_vref' in self.config:
                data['rd_vref'] = self.config['default_rd_vref']
            if 'default_wr_vref' in self.config:
                data['wr_vref'] = self.config['default_wr_vref']

        # Merge with training results if training has completed
        if self.training_sm and self.training_sm.params.training_passed:
            params = self.training_sm.params
            data.update({
                'rd_vref': params.rd_vref,
                'wr_vref': params.wr_vref,
                'ca_vref': params.ca_vref,
                'rd_dqs_delay': params.rd_dqs_delay,
                'wr_level_delay': params.wr_level_delay,
                'rd_margin': params.rd_margin,
                'wr_margin': params.wr_margin,
            })

        return data


class HBM4PHYManager:
    """HBM4 PHY Manager

    Top-level manager that coordinates PHY initialization
    and training across all channels.

    This class provides the unified interface for PHY control
    and integrates with the DFI 5.1 interface.
    """

    def __init__(self, num_channels: int = 32,
                 dfi_interface=None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize HBM4 PHY Manager

        Args:
            num_channels: Number of HBM4 channels
            dfi_interface: Optional DFI 5.1 interface
            config: Optional configuration dictionary
        """
        self.num_channels = num_channels
        self.dfi = dfi_interface
        self.config = config or {}

        # Create initialization state machines per channel
        self._init_machines: List[PHYInitializationStateMachine] = []
        self._training_machines: List[PHYTrainingStateMachine] = []

        for ch in range(num_channels):
            # Create training state machine
            training_sm = PHYTrainingStateMachine(
                channel_id=ch,
                dfi_interface=dfi_interface,
                config=self.config.get('training', {})
            )
            self._training_machines.append(training_sm)

            # Create initialization state machine
            init_sm = PHYInitializationStateMachine(
                training_sm=training_sm,
                dfi_interface=dfi_interface,
                config=self.config
            )
            self._init_machines.append(init_sm)

        # Global state
        self._global_cycle = 0
        self._all_initialized = False

    @property
    def cycle(self) -> int:
        """Current global cycle"""
        return self._global_cycle

    def tick(self):
        """Advance all PHY state machines by one cycle"""
        self._global_cycle += 1

        for init_sm in self._init_machines:
            init_sm.tick()
            init_sm.process_init_cycle()

        # Check if all initialized
        self._all_initialized = all(sm.is_initialized for sm in self._init_machines)

    def start_initialization(self):
        """Start initialization on all channels"""
        for init_sm in self._init_machines:
            init_sm.start_initialization()

    def process_cycles(self, num_cycles: int):
        """Process multiple initialization cycles

        Args:
            num_cycles: Number of cycles to process
        """
        for _ in range(num_cycles):
            # Process each channel
            for init_sm in self._init_machines:
                init_sm.process_init_cycle()

            self.tick()

    def wait_for_initialization(self, max_cycles: int = 100000) -> bool:
        """Wait for initialization to complete

        Args:
            max_cycles: Maximum cycles to wait

        Returns:
            True if initialization completed successfully
        """
        for _ in range(max_cycles):
            if self._all_initialized:
                return True
            self.process_cycles(1)
        return False

    def get_channel_status(self, channel: int) -> Dict[str, Any]:
        """Get status for a specific channel

        Args:
            channel: Channel index

        Returns:
            Channel status dictionary
        """
        if channel < 0 or channel >= self.num_channels:
            return {'error': 'Invalid channel index'}

        return self._init_machines[channel].get_initialization_status()

    def get_all_channel_status(self) -> List[Dict[str, Any]]:
        """Get status for all channels

        Returns:
            List of channel status dictionaries
        """
        return [sm.get_initialization_status() for sm in self._init_machines]

    def is_ready(self) -> bool:
        """Check if all PHYs are ready

        Returns:
            True if all channels are ready
        """
        return self._all_initialized and all(sm.is_ready for sm in self._init_machines)

    def get_aggregate_calibration_data(self) -> Dict[str, Any]:
        """Get calibration data aggregated across all channels

        Returns:
            Dictionary with calibration data
        """
        all_data = [sm.get_calibration_data() for sm in self._init_machines]

        # Aggregate statistics
        return {
            'num_channels': self.num_channels,
            'num_initialized': sum(1 for sm in self._init_machines if sm.is_initialized),
            'num_ready': sum(1 for sm in self._init_machines if sm.is_ready),
            'channel_data': all_data,
        }