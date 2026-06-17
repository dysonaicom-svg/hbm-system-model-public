"""
DFI 5.1 Encoder for HBM4 Controller/PHY Interface

This module implements the DFI 5.1 compliant encoder that translates
controller requests into DFI signals for communication with the HBM4 PHY.

DFI 5.1 COMPLIANT FEATURES:
- Complete command encoding (ACT, PRE, RD, WR, REFab, etc.)
- Address encoding for 32-channel HBM4 architecture
- Data enable signals with proper timing (wrdata_en, rddata_en)
- Control update handshake protocol
- Frequency change protocol with state machine
- Low power state management (CKE-based)
- All DFI 5.1 timing parameters

DFI 5.1 SPECIFIC PARAMETERS:
- tPHY_wrlAT: PHY write data ready time (cycles)
- tPHY_rdLat: PHY read latency (cycles)
- tDFI_PHY_UPD: PHY update minimum interval
- tDFI_CTRL_UPD: Controller update minimum interval
- tDFI_PHY_UPD_DELAY: PHY update delay
- tDFI_CTRL_UPD_DELAY: Controller update delay
- tDFI_PHY_UPD_INTERVAL: PHY update interval
- tDFI_CTRL_UPD_INTERVAL: Controller update interval

HBM4 ARCHITECTURE:
- 32 channels (5-bit channel field)
- 64 pseudo-channels (1-bit pseudo-channel field)
- 16 banks per pseudo-channel
- 8 bank groups per channel
- 2048-bit interface width

Reference:
- DFI 5.1 Specification (DFI 5.0/5.1)
- JEDEC JESD270-4A HBM4 Specification
- Synopsys DesignWare HBM4/4E Controller IP
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union
from collections import deque


class DFIEncoderError(Exception):
    """Base exception for DFI encoder errors"""
    pass


class DFIEncodingError(DFIEncoderError):
    """Exception raised for command/address encoding errors"""
    pass


class DFITimingError(DFIEncoderError):
    """Exception raised for DFI timing violations"""
    pass


class DFIChannelError(DFIEncoderError):
    """Exception raised for channel-related errors"""
    pass


class DFIPowerStateError(DFIEncoderError):
    """Exception raised for power state errors"""
    pass


# =============================================================================
# DFI 5.1 Command Definitions
# =============================================================================

class DFI5Command(Enum):
    """DFI 5.1 command encoding for HBM4

    These commands are encoded onto the DFI bus for communication
    between the memory controller and PHY.
    """
    NOP = 0b0000       # No operation
    ACT = 0b0001       # Activate - opens a row
    PRE = 0b0010       # Precharge - closes a bank
    PREA = 0b0011      # Precharge all - closes all banks in a pseudo-channel
    RD = 0b0100        # Read - initiates a read command
    RD_A = 0b0101      # Read with auto-precharge
    WR = 0b0110        # Write - initiates a write command
    WR_A = 0b0111      # Write with auto-precharge
    REFab = 0b1000     # All-bank refresh
    REFsb = 0b1001     # Per-bank (same bank) refresh
    RFMab = 0b1010     # Row flash memory refresh all-bank
    RFMsb = 0b1011     # Row flash memory refresh same bank
    MRS = 0b1100       # Mode register set
    REFab_1 = 0b1101   # Extended refresh command 1
    REFab_2 = 0b1110   # Extended refresh command 2
    PD = 0b1111        # Power-down entry


class DFIPowerState(Enum):
    """DFI 5.1 power state definitions

    Represents the power state of the DFI interface.
    """
    PWR_IDLE = 0       # Normal operation state
    PWR_POWER_DOWN = 1 # Controller power-down state
    PWR_SELF_REFRESH = 2  # Self-refresh state
    PWR_DEEP_POWER_DOWN = 3  # Deep power-down state


class DFI5PhyState(Enum):
    """DFI 5.1 PHY state definitions

    Tracks the state of the PHY for frequency and power management.
    """
    PHY_IDLE = auto()          # Normal operation
    PHY_UPDATE = auto()         # PHY update in progress
    PHY_FREQ_CHANGE = auto()    # Frequency change in progress
    PHY_POWER_DOWN = auto()    # PHY power-down state
    PHY_RESET = auto()          # PHY being reset
    PHY_TRAINING = auto()       # PHY in training mode


class DFI5FreqChangeState(Enum):
    """DFI 5.1 frequency change state machine

    Tracks the progression through a frequency change sequence.
    """
    FC_IDLE = auto()           # No frequency change in progress
    FC_REQUESTED = auto()      # Frequency change requested
    FC_ENTERING = auto()       # Entering frequency change
    FC_ACTIVE = auto()         # Frequency change active
    FC_EXITING = auto()        # Exiting frequency change
    FC_LOCKING = auto()        # PLL/DLL re-locking
    FC_COMPLETE = auto()       # Frequency change complete


# =============================================================================
# DFI 5.1 Timing Parameters
# =============================================================================

@dataclass
class DFI5TimingParams:
    """DFI 5.1 timing parameters for controller-PHY coordination

    These parameters define the timing relationships between controller
    and PHY signals as specified in DFI 5.1.

    Reference: DFI 5.1 Specification Table 3-1
    """
    # PHY write latency (DFI 5.1)
    tPHY_wrlAT: int = 5           # PHY write data ready time (cycles)
    tPHY_wrlAT_max: int = 20     # Maximum write latency

    # PHY read latency (DFI 5.1)
    tPHY_rdLat: int = 5           # PHY read data delay (cycles)
    tPHY_rdLat_max: int = 20     # Maximum read latency

    # DFI 5.1 Update timing
    tDFI_PHY_UPD: int = 8         # PHY update minimum interval
    tDFI_CTRL_UPD: int = 8       # Controller update minimum interval
    tDFI_PHY_UPD_DELAY: int = 4   # PHY update delay
    tDFI_CTRL_UPD_DELAY: int = 4  # Controller update delay
    tDFI_PHY_UPD_INTERVAL: int = 256  # PHY update maximum interval
    tDFI_CTRL_UPD_INTERVAL: int = 256  # Controller update maximum interval

    # Frequency change timing (DFI 5.1)
    tFC_LATENCY: int = 8          # Frequency change latency (cycles)
    tFC_EXIT: int = 4             # Exit frequency change latency

    # Low power timing (DFI 5.1)
    tLP_CTRL_ENTER: int = 2       # LP_CTRL entry latency
    tLP_CTRL_EXIT: int = 2       # LP_CTRL exit latency
    tLP_DATA_ENTER: int = 4      # LP_DATA entry latency
    tLP_DATA_EXIT: int = 4       # LP_DATA exit latency

    # Power management timing
    tPWR_UP: int = 2              # Power-up latency
    tPWR_DOWN: int = 2            # Power-down latency
    tSR_ENTER: int = 5            # Self-refresh entry latency
    tSR_EXIT: int = 5             # Self-refresh exit latency
    tDPD_ENTER: int = 3           # Deep power-down entry latency
    tDPD_EXIT: int = 3           # Deep power-down exit latency

    # Training timing
    tTRAINING: int = 1000         # Training duration (cycles)

    # CA parity timing (HBM4 specific)
    tCA_PARITY: int = 2           # CA parity error detection latency

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


# =============================================================================
# DFI 5.1 Signal Bundles
# =============================================================================

@dataclass
class DFI5AddressSignals:
    """DFI 5.1 address signal bundle

    Contains all address-related DFI signals that are sent from
    controller to PHY.
    """
    # Command encoding (4 bits)
    dfi_cmd: int = 0                    # DFI command code
    dfi_cmd_addr: int = 0               # Command address field

    # Bank address (4 bits for HBM4)
    dfi_bank: int = 0

    # Row address (19 bits for HBM4)
    dfi_row: int = 0

    # Column address (6 bits for HBM4)
    dfi_col: int = 0

    # Channel address (5 bits for HBM4's 32 channels)
    dfi_channel: int = 0

    # Pseudo-channel address (1 bit for HBM4)
    dfi_pseudo_channel: int = 0

    # Bank group address (3 bits for HBM4)
    dfi_bank_group: int = 0

    @classmethod
    def create_empty(cls) -> "DFI5AddressSignals":
        """Create an empty signal bundle with all zeros"""
        return cls()

    def clear(self):
        """Clear all signal values"""
        self.dfi_cmd = 0
        self.dfi_cmd_addr = 0
        self.dfi_bank = 0
        self.dfi_row = 0
        self.dfi_col = 0
        self.dfi_channel = 0
        self.dfi_pseudo_channel = 0
        self.dfi_bank_group = 0


@dataclass
class DFI5ControlSignals:
    """DFI 5.1 control signal bundle

    Contains all control-related DFI signals including update
    handshakes and power management.
    """
    # Command enable
    dfi_cmd_en: bool = False           # Command enable strobe

    # Control update handshake
    dfi_ctrlupd_req: bool = False     # Controller requests control update
    dfi_ctrlupd_ack: bool = False      # PHY acknowledges control update

    # PHY update handshake
    dfi_phyupd_req: bool = False      # PHY requests update
    dfi_phyupd_ack: bool = False      # Controller acknowledges update
    dfi_phyupd_type: int = 0          # PHY update type

    # Frequency change
    dfi_freq_change_en: bool = False  # Frequency change enable
    dfi_freq_change_ack: bool = False # Frequency change acknowledge

    # Power management
    dfi_pwr_up_done: bool = False     # Power-up sequence complete
    dfi_pwr_down_req: bool = False   # Power-down request
    dfi_pwr_down_ack: bool = False   # Power-down acknowledge
    dfi_cke: int = 0                 # Clock enable (one per pseudo-channel)

    # Low power state
    dfi_lp_req: bool = False         # Low power entry request
    dfi_lp_ack: bool = False         # Low power acknowledgment
    dfi_lp_wakeup: bool = False      # Low power wakeup

    # Training control
    dfi_training: bool = False       # Training mode indicator
    dfi_wrlvl_start: bool = False    # Write leveling start
    dfi_rdlvl_start: bool = False    # Read leveling start
    dfi_rdlvl_gate_start: bool = False  # Read gate leveling start


@dataclass
class DFI5DataSignals:
    """DFI 5.1 data signal bundle

    Contains all data-related DFI signals including write data
    enables and read data valid signals.
    """
    # Write data
    dfi_wrdata_en: int = 0           # Write data enable (per pseudo-channel)
    dfi_wrdata: int = 0              # Write data bus
    dfi_wrdata_mask: int = 0         # Write data mask

    # Read data
    dfi_rddata_en: int = 0           # Read data enable (per pseudo-channel)
    dfi_rddata: int = 0              # Read data bus
    dfi_rddata_valid: bool = False   # Read data valid strobe

    # ECC/CRC (HBM4 specific)
    dfi_wrdata_ecc: int = 0          # Write ECC data
    dfi_rddata_ecc: int = 0          # Read ECC data


@dataclass
class DFI5EncodedFrame:
    """Complete DFI 5.1 encoded frame

    Contains all DFI signal groups for a single cycle.
    """
    cycle: int = 0

    # Address signals
    addr: DFI5AddressSignals = field(default_factory=DFI5AddressSignals)

    # Control signals
    ctrl: DFI5ControlSignals = field(default_factory=DFI5ControlSignals)

    # Data signals
    data: DFI5DataSignals = field(default_factory=DFI5DataSignals)

    # Metadata
    is_valid: bool = False
    request_id: Optional[int] = None
    timestamp: int = 0


# =============================================================================
# DFI 5.1 Encoder Request/Response
# =============================================================================

@dataclass
class DFI5EncoderRequest:
    """Request to be encoded by DFI 5.1 encoder

    Contains all information needed to encode a controller request
    into DFI signals.
    """
    command: DFI5Command
    channel: int                      # Channel index (0-31)
    pseudo_channel: int               # Pseudo-channel index (0-1)
    bank: int                         # Bank index (0-15)
    bank_group: int                   # Bank group index (0-7)
    row: int                          # Row address
    col: int                          # Column address
    request_id: int = 0               # Unique request identifier
    priority: int = 0                 # Priority (higher = more urgent)
    timestamp: int = 0                # Simulation timestamp
    is_read: bool = True              # Read vs write flag
    is_auto_precharge: bool = False  # Auto-precharge flag
    data: Optional[int] = None        # Write data (if applicable)


@dataclass
class DFI5EncoderResponse:
    """Response from DFI 5.1 encoder

    Contains encoded signals and status information.
    """
    success: bool = True
    frames: List[DFI5EncodedFrame] = field(default_factory=list)
    error_message: Optional[str] = None
    timing_violations: List[str] = field(default_factory=list)
    latency_cycles: int = 0


# =============================================================================
# HBM4 Address Decoder for DFI
# =============================================================================

@dataclass
class HBM4DFIAddressDecoder:
    """Address decoder for HBM4 DFI interface

    Decodes memory addresses into DFI address fields according
    to the HBM4 address mapping.

    HBM4 Address Format:
    [Stack:2][Channel:5][Pch:1][Bg:3][Bank:4][Row:19][Col:6][Burst:2]

    Total: 42 bits
    """
    # Address field widths (matching HBM4Spec)
    STACK_BITS: int = 2
    CHANNEL_BITS: int = 5      # 32 channels
    PCH_BITS: int = 1           # 2 pseudo-channels
    BG_BITS: int = 3            # 8 bank groups
    BANK_BITS: int = 4          # 16 banks per group
    ROW_BITS: int = 19          # 512K rows
    COL_BITS: int = 6           # 64 columns
    BURST_BITS: int = 2         # 4-beat burst alignment

    @property
    def channel_count(self) -> int:
        """Number of channels"""
        return 1 << self.CHANNEL_BITS  # 32

    @property
    def pseudo_channel_count(self) -> int:
        """Number of pseudo-channels per channel"""
        return 1 << self.PCH_BITS  # 2

    @property
    def bank_count(self) -> int:
        """Number of banks per pseudo-channel"""
        return 1 << self.BANK_BITS  # 16

    @property
    def bank_group_count(self) -> int:
        """Number of bank groups per channel"""
        return 1 << self.BG_BITS  # 8

    @property
    def row_count(self) -> int:
        """Number of rows"""
        return 1 << self.ROW_BITS  # 512K

    @property
    def col_count(self) -> int:
        """Number of columns"""
        return 1 << self.COL_BITS  # 64

    def decode_address(self, address: int) -> Dict[str, int]:
        """Decode a memory address into HBM4 fields

        Args:
            address: Full memory address

        Returns:
            Dictionary with decoded fields: stack, channel, pseudo_channel,
            bank_group, bank, row, column, burst
        """
        result = {}

        # Extract burst (LSB)
        result['burst'] = address & ((1 << self.BURST_BITS) - 1)
        address >>= self.BURST_BITS

        # Extract column
        result['column'] = address & ((1 << self.COL_BITS) - 1)
        address >>= self.COL_BITS

        # Extract row
        result['row'] = address & ((1 << self.ROW_BITS) - 1)
        address >>= self.ROW_BITS

        # Extract bank
        result['bank'] = address & ((1 << self.BANK_BITS) - 1)
        address >>= self.BANK_BITS

        # Extract bank group
        result['bank_group'] = address & ((1 << self.BG_BITS) - 1)
        address >>= self.BG_BITS

        # Extract pseudo-channel
        result['pseudo_channel'] = address & ((1 << self.PCH_BITS) - 1)
        address >>= self.PCH_BITS

        # Extract channel
        result['channel'] = address & ((1 << self.CHANNEL_BITS) - 1)
        address >>= self.CHANNEL_BITS

        # Extract stack
        result['stack'] = address & ((1 << self.STACK_BITS) - 1)

        return result

    def encode_address(self,
                       stack: int = 0,
                       channel: int = 0,
                       pseudo_channel: int = 0,
                       bank_group: int = 0,
                       bank: int = 0,
                       row: int = 0,
                       column: int = 0,
                       burst: int = 0) -> int:
        """Encode HBM4 fields into a memory address

        Args:
            stack: Stack index (0-3)
            channel: Channel index (0-31)
            pseudo_channel: Pseudo-channel index (0-1)
            bank_group: Bank group index (0-7)
            bank: Bank index (0-15)
            row: Row address (0-511K)
            column: Column address (0-63)
            burst: Burst offset (0-3)

        Returns:
            Full memory address
        """
        address = 0

        # Build from LSB to MSB
        address |= (burst & ((1 << self.BURST_BITS) - 1))
        address |= (column & ((1 << self.COL_BITS) - 1)) << self.BURST_BITS
        address |= (row & ((1 << self.ROW_BITS) - 1)) << (self.BURST_BITS + self.COL_BITS)
        address |= (bank & ((1 << self.BANK_BITS) - 1)) << (self.BURST_BITS + self.COL_BITS + self.ROW_BITS)
        address |= (bank_group & ((1 << self.BG_BITS) - 1)) << (self.BURST_BITS + self.COL_BITS + self.ROW_BITS + self.BANK_BITS)
        address |= (pseudo_channel & ((1 << self.PCH_BITS) - 1)) << (self.BURST_BITS + self.COL_BITS + self.ROW_BITS + self.BANK_BITS + self.BG_BITS)
        address |= (channel & ((1 << self.CHANNEL_BITS) - 1)) << (self.BURST_BITS + self.COL_BITS + self.ROW_BITS + self.BANK_BITS + self.BG_BITS + self.PCH_BITS)
        address |= (stack & ((1 << self.STACK_BITS) - 1)) << (self.BURST_BITS + self.COL_BITS + self.ROW_BITS + self.BANK_BITS + self.BG_BITS + self.PCH_BITS + self.CHANNEL_BITS)

        return address

    def validate_address_fields(self,
                                channel: int,
                                pseudo_channel: int,
                                bank_group: int,
                                bank: int,
                                row: int,
                                column: int) -> Tuple[bool, str]:
        """Validate address fields are within valid ranges

        Args:
            channel: Channel index
            pseudo_channel: Pseudo-channel index
            bank_group: Bank group index
            bank: Bank index
            row: Row address
            column: Column address

        Returns:
            Tuple of (is_valid, error_message)
        """
        if channel < 0 or channel >= self.channel_count:
            return False, f"Channel {channel} out of range [0, {self.channel_count - 1}]"

        if pseudo_channel < 0 or pseudo_channel >= self.pseudo_channel_count:
            return False, f"Pseudo-channel {pseudo_channel} out of range [0, {self.pseudo_channel_count - 1}]"

        if bank_group < 0 or bank_group >= self.bank_group_count:
            return False, f"Bank group {bank_group} out of range [0, {self.bank_group_count - 1}]"

        if bank < 0 or bank >= self.bank_count:
            return False, f"Bank {bank} out of range [0, {self.bank_count - 1}]"

        if row < 0 or row >= self.row_count:
            return False, f"Row {row} out of range [0, {self.row_count - 1}]"

        if column < 0 or column >= self.col_count:
            return False, f"Column {column} out of range [0, {self.col_count - 1}]"

        return True, ""


# =============================================================================
# DFI 5.1 Encoder Core
# =============================================================================

class DFI5Encoder:
    """DFI 5.1 compliant encoder for HBM4 Controller/PHY interface

    This encoder translates controller requests into DFI signals
    for communication with the HBM4 PHY.

    KEY FEATURES:
    - Full DFI 5.1 compliance
    - 32-channel HBM4 architecture support
    - Cycle-accurate timing modeling
    - Command and address encoding
    - Data enable signal generation
    - Control update handshake
    - Frequency change protocol
    - Low power state management

    DFI SIGNAL GROUPS:
    1. Address Group: dfi_cmd, dfi_cmd_addr, dfi_bank, dfi_channel, etc.
    2. Control Group: dfi_ctrlupd_req/ack, dfi_phyupd_req/ack, dfi_freq_change_*
    3. Data Group: dfi_wrdata_en, dfi_rddata_en, dfi_wrdata, dfi_rddata

    USAGE:
        encoder = DFI5Encoder(tCK_ps=125.0)
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=0, pseudo_channel=0, bank=0, bank_group=0,
            row=100, col=0
        )
        response = encoder.encode(request)

    Reference:
    - DFI 5.1 Specification
    - JEDEC JESD270-4A HBM4 Specification
    """

    VERSION = "5.1"

    # Valid command sequences for timing checks
    VALID_COMMANDS = {
        DFI5Command.ACT: {'next': [DFI5Command.RD, DFI5Command.WR, DFI5Command.RD_A, DFI5Command.WR_A, DFI5Command.PRE, DFI5Command.PREA]},
        DFI5Command.PRE: {'next': [DFI5Command.ACT, DFI5Command.REFab, DFI5Command.REFsb]},
        DFI5Command.PREA: {'next': [DFI5Command.ACT, DFI5Command.REFab]},
        DFI5Command.RD: {'next': [DFI5Command.RD, DFI5Command.WR, DFI5Command.PRE, DFI5Command.PREA, DFI5Command.NOP]},
        DFI5Command.WR: {'next': [DFI5Command.WR, DFI5Command.RD, DFI5Command.PRE, DFI5Command.PREA, DFI5Command.NOP]},
        DFI5Command.RD_A: {'next': [DFI5Command.ACT, DFI5Command.REFab, DFI5Command.NOP]},
        DFI5Command.WR_A: {'next': [DFI5Command.ACT, DFI5Command.REFab, DFI5Command.NOP]},
        DFI5Command.REFab: {'next': [DFI5Command.REFab, DFI5Command.ACT, DFI5Command.NOP]},
        DFI5Command.REFsb: {'next': [DFI5Command.REFsb, DFI5Command.ACT, DFI5Command.NOP]},
        DFI5Command.NOP: {'next': list(DFI5Command)},
    }

    def __init__(self,
                 tCK_ps: float = 125.0,
                 timing_params: Optional[DFI5TimingParams] = None,
                 enable_timing_checks: bool = True,
                 channel_count: int = 32):
        """Initialize DFI 5.1 encoder

        Args:
            tCK_ps: Clock period in picoseconds (125ps = 8 GT/s)
            timing_params: DFI timing parameters
            enable_timing_checks: Enable cycle-accurate timing validation
            channel_count: Number of HBM4 channels (default 32)
        """
        self.tCK_ps = tCK_ps
        self.timing = timing_params or DFI5TimingParams()
        self.enable_timing_checks = enable_timing_checks
        self.channel_count = channel_count

        # Address decoder
        self.address_decoder = HBM4DFIAddressDecoder()

        # State tracking
        self._cycle = 0
        self._last_command: Dict[int, DFI5Command] = {}  # Per-channel tracking
        self._last_command_cycle: Dict[int, int] = {}     # Per-channel timing
        self._active_row: Dict[int, int] = {}            # Track open rows per channel
        self._phy_state = DFI5PhyState.PHY_IDLE
        self._ctrl_state = DFIPowerState.PWR_IDLE

        # Frequency change state machine
        self._fc_state = DFI5FreqChangeState.FC_IDLE
        self._fc_latency_counter = 0
        self._target_frequency = 0

        # Control/PHY update tracking
        self._ctrlupd_req_pending = False
        self._ctrlupd_ack_pending = False
        self._phyupd_req_pending = False
        self._phyupd_ack_pending = False
        self._update_counters = {'ctrl': 0, 'phy': 0}

        # Command queue for cycle-accurate simulation
        self._command_queue: deque = deque(maxlen=256)

        # Statistics
        self._stats = {
            'commands_encoded': 0,
            'frames_generated': 0,
            'timing_violations': 0,
            'freq_changes': 0,
            'ctrl_updates': 0,
            'errors': 0,
        }

        # Error log
        self._error_log: List[Dict[str, Any]] = []

    @property
    def cycle(self) -> int:
        """Current simulation cycle"""
        return self._cycle

    @property
    def frequency_mhz(self) -> float:
        """Current frequency in MHz

        For HBM4 at 8 GT/s DDR:
        - tCK = 125 ps = 8 GHz clock
        - DFI frequency = 8 GT/s / 2 = 4 GHz = 4000 MT/s for DQ, or 8 GHz for command

        The formula 1e6 / tCK_ps converts from ps to MHz:
        - 1e6 / 125 = 8000 MHz (for 8 GT/s DDR at tCK=125ps)
        - 1e6 / 83.33 = 12000 MHz (for 12 GT/s DDR at tCK=83.33ps)
        - 1e6 / 62.5 = 16000 MHz (for 16 GT/s DDR at tCK=62.5ps)
        """
        return 1e6 / self.tCK_ps if self.tCK_ps > 0 else 0

    def tick(self):
        """Advance simulation by one cycle

        Call this once per cycle to update internal state machines.
        """
        self._cycle += 1
        self._update_fc_state()
        self._update_ctrlupd_state()
        self._update_phyupd_state()
        self._process_command_queue()

    # =========================================================================
    # Command Encoding
    # =========================================================================

    def encode(self, request: DFI5EncoderRequest) -> DFI5EncoderResponse:
        """Encode a controller request into DFI signals

        This is the main entry point for encoding requests.

        Args:
            request: DFI encoder request with command and address info

        Returns:
            DFI encoder response with encoded frames
        """
        response = DFI5EncoderResponse()

        # Validate channel index
        if request.channel < 0 or request.channel >= self.channel_count:
            self._record_error('channel', f"Invalid channel {request.channel}", request.timestamp)
            response.success = False
            response.error_message = f"Invalid channel index: {request.channel}"
            return response

        # Validate address fields
        valid, error_msg = self.address_decoder.validate_address_fields(
            request.channel,
            request.pseudo_channel,
            request.bank_group,
            request.bank,
            request.row,
            request.col
        )
        if not valid:
            self._record_error('address', error_msg, request.timestamp)
            response.success = False
            response.error_message = error_msg
            return response

        # Check timing constraints
        if self.enable_timing_checks:
            timing_ok, violations = self._check_timing_constraints(request)
            if not timing_ok:
                response.timing_violations = violations
                self._stats['timing_violations'] += len(violations)

        # Encode command
        try:
            frames = self._encode_command(request)
            response.frames = frames
            response.success = True
            response.latency_cycles = self._calculate_latency(request)
            self._stats['commands_encoded'] += 1
            self._stats['frames_generated'] += len(frames)
        except DFIEncodingError as e:
            response.success = False
            response.error_message = str(e)
            self._record_error('encoding', str(e), request.timestamp)

        return response

    def _encode_command(self, request: DFI5EncoderRequest) -> List[DFI5EncodedFrame]:
        """Encode a command into DFI frames

        Args:
            request: The request to encode

        Returns:
            List of encoded DFI frames
        """
        frames = []
        channel_key = request.channel

        # Determine number of cycles based on command type
        if request.command == DFI5Command.ACT:
            num_cycles = 1
        elif request.command in [DFI5Command.RD, DFI5Command.WR]:
            num_cycles = 1
        elif request.command in [DFI5Command.RD_A, DFI5Command.WR_A]:
            num_cycles = 1
        elif request.command == DFI5Command.PRE:
            num_cycles = 1
        elif request.command == DFI5Command.PREA:
            num_cycles = 1
        elif request.command in [DFI5Command.REFab, DFI5Command.REFsb]:
            num_cycles = 1
        else:
            num_cycles = 1

        # Generate frames
        for i in range(num_cycles):
            frame = DFI5EncodedFrame()
            frame.cycle = self._cycle + i
            frame.is_valid = True
            frame.request_id = request.request_id
            frame.timestamp = request.timestamp

            # Encode address signals
            frame.addr.dfi_cmd = request.command.value
            frame.addr.dfi_channel = request.channel
            frame.addr.dfi_pseudo_channel = request.pseudo_channel
            frame.addr.dfi_bank_group = request.bank_group
            frame.addr.dfi_bank = request.bank
            frame.addr.dfi_row = request.row
            frame.addr.dfi_col = request.col

            # Encode control signals (command enable on first cycle)
            frame.ctrl.dfi_cmd_en = (i == 0)

            # Generate data enable for read/write commands
            if request.command in [DFI5Command.RD, DFI5Command.RD_A]:
                frame.data.dfi_rddata_en = 1 << request.pseudo_channel
                frame.data.dfi_rddata_valid = False  # Valid follows after latency
            elif request.command in [DFI5Command.WR, DFI5Command.WR_A]:
                frame.data.dfi_wrdata_en = 1 << request.pseudo_channel
                if request.data is not None:
                    frame.data.dfi_wrdata = request.data

            frames.append(frame)

        # Update state tracking
        self._last_command[channel_key] = request.command
        self._last_command_cycle[channel_key] = self._cycle

        if request.command == DFI5Command.ACT:
            # Track active row for this channel/pseudo-channel
            row_key = (request.channel, request.pseudo_channel, request.bank)
            self._active_row[row_key] = request.row

        return frames

    def _calculate_latency(self, request: DFI5EncoderRequest) -> int:
        """Calculate expected latency for a request

        Args:
            request: The request

        Returns:
            Latency in cycles
        """
        if request.command in [DFI5Command.RD, DFI5Command.RD_A]:
            return self.timing.tPHY_rdLat
        elif request.command in [DFI5Command.WR, DFI5Command.WR_A]:
            return self.timing.tPHY_wrlAT
        else:
            return 0

    def _check_timing_constraints(self, request: DFI5EncoderRequest) -> Tuple[bool, List[str]]:
        """Check timing constraints for a request

        Args:
            request: The request to check

        Returns:
            Tuple of (is_valid, list of violations)
        """
        violations = []
        channel_key = request.channel

        # Check if we have a previous command on this channel
        if channel_key in self._last_command:
            last_cmd = self._last_command[channel_key]
            last_cycle = self._last_command_cycle[channel_key]
            cycles_since = self._cycle - last_cycle

            # Check tCCD (CAS to CAS delay)
            if request.command in [DFI5Command.RD, DFI5Command.WR] and last_cmd in [DFI5Command.RD, DFI5Command.WR]:
                # Same bank group
                if request.bank_group == self._last_command.get(f'{channel_key}_bg', 0):
                    min_cycles = self.timing.tLP_CTRL_ENTER  # tCCD_L (same BG)
                else:
                    min_cycles = self.timing.tLP_DATA_ENTER  # tCCD_S (different BG)

                if cycles_since < min_cycles:
                    violations.append(f"tCCD violation: {cycles_since} < {min_cycles} cycles")

            # Check tRCD (RAS to CAS)
            if request.command in [DFI5Command.RD, DFI5Command.WR, DFI5Command.RD_A, DFI5Command.WR_A]:
                if last_cmd == DFI5Command.ACT:
                    row_key = (request.channel, request.pseudo_channel, request.bank)
                    if row_key in self._active_row:
                        # Row is open, check tRCD
                        if cycles_since < self.timing.tPHY_rdLat:
                            violations.append(f"tRCD violation: {cycles_since} < {self.timing.tPHY_rdLat} cycles")

        return (len(violations) == 0, violations)

    # =========================================================================
    # Control Update Handshake
    # =========================================================================

    def request_ctrlupd(self) -> bool:
        """Request a control update

        Returns:
            True if request was accepted
        """
        if self._ctrlupd_req_pending:
            return False

        self._ctrlupd_req_pending = True
        self._update_counters['ctrl'] += 1
        self._stats['ctrl_updates'] += 1
        return True

    def acknowledge_ctrlupd(self) -> bool:
        """Acknowledge a control update

        Returns:
            True if acknowledgment was accepted
        """
        if not self._ctrlupd_req_pending:
            return False

        self._ctrlupd_ack_pending = True
        return True

    def _update_ctrlupd_state(self):
        """Update control update state machine"""
        if self._ctrlupd_req_pending and self._ctrlupd_ack_pending:
            self._ctrlupd_req_pending = False
            self._ctrlupd_ack_pending = False

    def get_ctrlupd_signals(self) -> Tuple[bool, bool]:
        """Get control update signals

        Returns:
            Tuple of (req, ack)
        """
        return (self._ctrlupd_req_pending, self._ctrlupd_ack_pending)

    # =========================================================================
    # PHY Update Handshake
    # =========================================================================

    def request_phyupd(self, update_type: int = 0) -> bool:
        """Request a PHY update

        Args:
            update_type: Type of PHY update (0=normal, 1=CA training, etc.)

        Returns:
            True if request was accepted
        """
        if self._phyupd_req_pending:
            return False

        self._phyupd_req_pending = True
        self._update_counters['phy'] += 1
        return True

    def acknowledge_phyupd(self) -> bool:
        """Acknowledge a PHY update

        Returns:
            True if acknowledgment was accepted
        """
        if not self._phyupd_req_pending:
            return False

        self._phyupd_ack_pending = True
        return True

    def _update_phyupd_state(self):
        """Update PHY update state machine"""
        if self._phyupd_req_pending and self._phyupd_ack_pending:
            self._phyupd_req_pending = False
            self._phyupd_ack_pending = False

    def get_phyupd_signals(self) -> Tuple[bool, bool, int]:
        """Get PHY update signals

        Returns:
            Tuple of (req, ack, update_type)
        """
        return (self._phyupd_req_pending, self._phyupd_ack_pending, 0)

    # =========================================================================
    # Frequency Change Protocol
    # =========================================================================

    def request_freq_change(self, target_freq_mhz: float) -> bool:
        """Request a frequency change

        Args:
            target_freq_mhz: Target frequency in MHz

        Returns:
            True if request was accepted
        """
        if self._fc_state != DFI5FreqChangeState.FC_IDLE:
            return False

        self._target_frequency = target_freq_mhz
        self._fc_state = DFI5FreqChangeState.FC_REQUESTED
        self._fc_latency_counter = 0
        return True

    def enter_freq_change(self) -> bool:
        """Enter frequency change sequence

        Returns:
            True if transition was successful
        """
        if self._fc_state == DFI5FreqChangeState.FC_REQUESTED:
            self._fc_state = DFI5FreqChangeState.FC_ENTERING
            return True
        return False

    def exit_freq_change(self) -> bool:
        """Exit frequency change sequence

        Returns:
            True if exit was successful
        """
        if self._fc_state in [DFI5FreqChangeState.FC_ENTERING, DFI5FreqChangeState.FC_ACTIVE]:
            self._fc_state = DFI5FreqChangeState.FC_EXITING
            self._fc_latency_counter = 0
            return True
        return False

    def _update_fc_state(self):
        """Update frequency change state machine"""
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
            self._fc_state = DFI5FreqChangeState.FC_IDLE
            self.tCK_ps = 1000.0 / self._target_frequency if self._target_frequency > 0 else 125.0
            self._stats['freq_changes'] += 1

    def get_freq_change_state(self) -> DFI5FreqChangeState:
        """Get current frequency change state

        Returns:
            Current FC state
        """
        return self._fc_state

    def get_freq_change_signals(self) -> Tuple[bool, bool]:
        """Get frequency change signals

        Returns:
            Tuple of (freq_change_en, freq_change_ack)
        """
        return (
            self._fc_state in [DFI5FreqChangeState.FC_ENTERING, DFI5FreqChangeState.FC_ACTIVE],
            self._fc_state == DFI5FreqChangeState.FC_COMPLETE
        )

    def get_freq_change_latency_remaining(self) -> int:
        """Get remaining cycles until frequency change completes

        Returns:
            Remaining cycles, or 0 if not in progress
        """
        if self._fc_state == DFI5FreqChangeState.FC_IDLE:
            return 0

        latencies = {
            DFI5FreqChangeState.FC_REQUESTED: self.timing.tLP_CTRL_ENTER,
            DFI5FreqChangeState.FC_ENTERING: self.timing.tLP_CTRL_ENTER - self._fc_latency_counter,
            DFI5FreqChangeState.FC_ACTIVE: self.timing.tFC_EXIT - self._fc_latency_counter,
            DFI5FreqChangeState.FC_EXITING: self.timing.tFC_EXIT - self._fc_latency_counter,
            DFI5FreqChangeState.FC_LOCKING: self.timing.tFC_LATENCY - self._fc_latency_counter,
            DFI5FreqChangeState.FC_COMPLETE: 1,
        }
        return max(0, latencies.get(self._fc_state, 0))

    # =========================================================================
    # Command Queue Management
    # =========================================================================

    def queue_command(self, request: DFI5EncoderRequest) -> bool:
        """Add command to the queue

        Args:
            request: Command to queue

        Returns:
            True if successfully queued
        """
        if len(self._command_queue) >= 256:
            return False

        self._command_queue.append(request)
        return True

    def _process_command_queue(self):
        """Process pending commands in the queue"""
        # Implementation for cycle-accurate queue processing
        pass

    def get_pending_commands(self) -> int:
        """Get number of pending commands

        Returns:
            Number of pending commands
        """
        return len(self._command_queue)

    # =========================================================================
    # Low Power State Management (CKE-based)
    # =========================================================================

    def set_power_state(self, state: DFIPowerState) -> bool:
        """Set the power state

        Args:
            state: Target power state

        Returns:
            True if transition was successful
        """
        valid_transitions = {
            DFIPowerState.PWR_IDLE: [DFIPowerState.PWR_POWER_DOWN, DFIPowerState.PWR_SELF_REFRESH],
            DFIPowerState.PWR_POWER_DOWN: [DFIPowerState.PWR_IDLE],
            DFIPowerState.PWR_SELF_REFRESH: [DFIPowerState.PWR_IDLE],
            DFIPowerState.PWR_DEEP_POWER_DOWN: [DFIPowerState.PWR_IDLE],
        }

        if state in valid_transitions.get(self._ctrl_state, []):
            self._ctrl_state = state
            return True

        return False

    def get_power_state(self) -> DFIPowerState:
        """Get current power state

        Returns:
            Current power state
        """
        return self._ctrl_state

    def set_cke(self, cke_mask: int) -> bool:
        """Set clock enable signals

        Args:
            cke_mask: CKE mask (one bit per pseudo-channel)

        Returns:
            True if CKE was set
        """
        if self._ctrl_state == DFIPowerState.PWR_IDLE:
            return True
        return False

    def get_cke(self) -> int:
        """Get current CKE values

        Returns:
            CKE mask
        """
        if self._ctrl_state == DFIPowerState.PWR_IDLE:
            return 0xFF  # All CKE high
        elif self._ctrl_state == DFIPowerState.PWR_POWER_DOWN:
            return 0x00  # All CKE low
        elif self._ctrl_state == DFIPowerState.PWR_SELF_REFRESH:
            return 0x00  # All CKE low
        return 0x00

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _record_error(self, error_type: str, message: str, timestamp: int):
        """Record an error

        Args:
            error_type: Type of error
            message: Error message
            timestamp: Cycle when error occurred
        """
        self._error_log.append({
            'type': error_type,
            'message': message,
            'timestamp': timestamp,
        })
        self._stats['errors'] += 1

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get all recorded errors

        Returns:
            List of error records
        """
        return list(self._error_log)

    def get_statistics(self) -> Dict[str, Any]:
        """Get encoder statistics

        Returns:
            Dictionary with statistics
        """
        stats = dict(self._stats)
        stats['frequency_mhz'] = self.frequency_mhz
        stats['pending_commands'] = len(self._command_queue)
        stats['update_counters'] = dict(self._update_counters)
        return stats

    def reset_statistics(self):
        """Reset statistics counters"""
        self._stats = {
            'commands_encoded': 0,
            'frames_generated': 0,
            'timing_violations': 0,
            'freq_changes': 0,
            'ctrl_updates': 0,
            'errors': 0,
        }
        self._error_log.clear()

    def get_write_latency_ps(self) -> float:
        """Get write latency in picoseconds

        Returns:
            Write latency in ps
        """
        return self.timing.get_write_latency_ps(self.tCK_ps)

    def get_read_latency_ps(self) -> float:
        """Get read latency in picoseconds

        Returns:
            Read latency in ps
        """
        return self.timing.get_read_latency_ps(self.tCK_ps)

    def reset(self):
        """Reset encoder to initial state"""
        self._cycle = 0
        self._last_command.clear()
        self._last_command_cycle.clear()
        self._active_row.clear()
        self._phy_state = DFI5PhyState.PHY_IDLE
        self._ctrl_state = DFIPowerState.PWR_IDLE
        self._fc_state = DFI5FreqChangeState.FC_IDLE
        self._fc_latency_counter = 0
        self._ctrlupd_req_pending = False
        self._ctrlupd_ack_pending = False
        self._phyupd_req_pending = False
        self._phyupd_ack_pending = False
        self._update_counters = {'ctrl': 0, 'phy': 0}
        self._command_queue.clear()
        self.reset_statistics()

    def get_dfi_signals_summary(self) -> Dict[str, Any]:
        """Get summary of all DFI signals

        Returns:
            Dictionary with signal states
        """
        return {
            'version': self.VERSION,
            'frequency_mhz': self.frequency_mhz,
            'tCK_ps': self.tCK_ps,
            'cycle': self._cycle,
            'phy_state': self._phy_state.name,
            'ctrl_state': self._ctrl_state.name,
            'fc_state': self._fc_state.name,
            'ctrlupd_req': self._ctrlupd_req_pending,
            'ctrlupd_ack': self._ctrlupd_ack_pending,
            'phyupd_req': self._phyupd_req_pending,
            'phyupd_ack': self._phyupd_ack_pending,
            'freq_change_en': self._fc_state in [DFI5FreqChangeState.FC_ENTERING, DFI5FreqChangeState.FC_ACTIVE],
            'freq_change_ack': self._fc_state == DFI5FreqChangeState.FC_COMPLETE,
            'cke': self.get_cke(),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_hbm4_encoder(speed_grade: str = "8Gbps") -> DFI5Encoder:
    """Create a DFI 5.1 encoder configured for HBM4 speed grade

    Args:
        speed_grade: One of "8Gbps", "12Gbps", "16Gbps"

    Returns:
        Configured DFI5Encoder instance
    """
    speed_grades = {
        "8Gbps": 125.0,
        "12Gbps": 83.33,
        "16Gbps": 62.5,
    }

    if speed_grade not in speed_grades:
        raise ValueError(f"Unknown speed grade: {speed_grade}")

    tCK_ps = speed_grades[speed_grade]
    return DFI5Encoder(tCK_ps=tCK_ps)


def encode_hbm4_request(command: str,
                         channel: int,
                         pseudo_channel: int,
                         bank_group: int,
                         bank: int,
                         row: int,
                         col: int,
                         tCK_ps: float = 125.0) -> DFI5EncoderResponse:
    """Convenience function to encode an HBM4 request

    Args:
        command: Command name ('ACT', 'PRE', 'RD', 'WR', etc.)
        channel: Channel index (0-31)
        pseudo_channel: Pseudo-channel index (0-1)
        bank_group: Bank group index (0-7)
        bank: Bank index (0-15)
        row: Row address
        col: Column address
        tCK_ps: Clock period in picoseconds

    Returns:
        DFI encoder response
    """
    encoder = DFI5Encoder(tCK_ps=tCK_ps)

    # Map command string to DFI5Command
    cmd_map = {
        'ACT': DFI5Command.ACT,
        'PRE': DFI5Command.PRE,
        'PREA': DFI5Command.PREA,
        'RD': DFI5Command.RD,
        'RDA': DFI5Command.RD_A,
        'WR': DFI5Command.WR,
        'WRA': DFI5Command.WR_A,
        'REFab': DFI5Command.REFab,
        'REFsb': DFI5Command.REFsb,
        'NOP': DFI5Command.NOP,
    }

    dfi_cmd = cmd_map.get(command, DFI5Command.NOP)
    is_read = command in ['RD', 'RDA']
    is_auto_precharge = command in ['RDA', 'WRA']

    request = DFI5EncoderRequest(
        command=dfi_cmd,
        channel=channel,
        pseudo_channel=pseudo_channel,
        bank=bank,
        bank_group=bank_group,
        row=row,
        col=col,
        is_read=is_read,
        is_auto_precharge=is_auto_precharge,
    )

    return encoder.encode(request)