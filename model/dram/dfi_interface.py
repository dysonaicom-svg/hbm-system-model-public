"""
DFI 5.1 Interface for HBM4 Controller-PHY Communication

Based on Synopsys HBM4 Controller findings:
- Extended DFI 5.1 for controller-PHY interface
- APB v2.0 register interface
- DFI PHY Independent Mode for initialization/training
- Low power state management
- Frequency change protocol

Reference:
- Synopsys DesignWare HBM4/4E Controller IP
- DFI 5.1 specification
- JEDEC JESD270-4A HBM4 specification
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


class DFICommand(Enum):
    """DFI command encoding for HBM4

    These are the standard DFI command codes used for
    communication between controller and PHY.
    """
    ACT = 0b0000     # Activate
    PRE = 0b0001     # Precharge
    PREA = 0b0010    # Precharge all
    RD = 0b0011      # Read
    WR = 0b0100      # Write
    RDA = 0b0101     # Read with auto-precharge
    WRA = 0b0110     # Write with auto-precharge
    REFab = 0b0111   # All-bank refresh
    REFsb = 0b1000   # Per-bank refresh
    RFMab = 0b1001   # All-bank row flash memory refresh
    RFMsb = 0b1010   # Per-bank row flash memory refresh


class DFILowPowerState(Enum):
    """DFI 5.1 low-power states

    Standard DFI low power state machine states.
    """
    LP_IDLE = 0          # Normal operation
    LP_CTRL = 1          # Controller in low-power (PHY still active)
    LP_DATA = 2          # Data path in low-power
    LP_FREQ_CHANGE = 3   # Frequency change in progress


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


class DFIPhyIF:
    """DFI PHY Interface

    Implements the DFI PHY Independent Mode features
    for initialization, training, and calibration.
    """

    def __init__(self):
        self.phy_clock_enable = True
        self.phy_reset = False
        self.phy_independent_mode = True
        self.calibration_data: Dict[str, Any] = {}

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

    def get_calibration_status(self) -> Dict[str, Any]:
        """Get calibration status

        Returns:
            Dictionary with calibration status for each lane
        """
        return self.calibration_data


class DFI5Interface:
    """DFI 5.1 interface implementation

    Implements the standard DFI 5.1 interface between HBM4 controller and PHY.

    Supports:
    - Command and address encoding
    - Data enable signals
    - Low-power state management
    - Frequency change protocol
    - PHY Independent Mode for initialization
    - Training and calibration

    Reference: DFI 5.1 Specification, Synopsys HBM4 Controller IP
    """

    VERSION = "5.1"

    def __init__(self, config=None):
        """Initialize DFI 5.1 interface

        Args:
            config: Optional configuration object
        """
        self.version = self.VERSION
        self.config = config
        self.supported_commands = list(DFICommand)

        # State tracking
        self.lp_state = DFILowPowerState.LP_IDLE
        self.frequency_mhz = 800  # 800 MT/s for 8 GT/s DDR
        self.training_complete = False
        self.training_in_progress = False

        # PHY interface
        self.phy = DFIPhyIF()

        # Request/response queues
        self.request_queue: List[DFIRequest] = []
        self.response_queue: List[DFIResponse] = []

    def encode_command(self, cmd: str, addr_vec: Dict[str, int]) -> DFIRequest:
        """Encode a command into DFI request format

        Args:
            cmd: Command name string ('ACT', 'PRE', 'RD', etc.)
            addr_vec: Dictionary with address components

        Returns:
            DFIRequest object
        """
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
        }

        dfi_cmd = cmd_map.get(cmd, DFICommand.ACT)

        return DFIRequest(
            command=dfi_cmd,
            address=addr_vec.get('row', addr_vec.get('address', 0)),
            bank=addr_vec.get('bank', 0),
            pseudo_channel=addr_vec.get('pseudo_channel', 0),
            channel=addr_vec.get('channel', 0),
            wrdata_en=(cmd in ['WR', 'WRA']),
            rddata_en=(cmd in ['RD', 'RDA']),
            chip=addr_vec.get('chip', 0)
        )

    def set_low_power_state(self, state: DFILowPowerState):
        """Set DFI low-power state

        Args:
            state: Target low-power state
        """
        self.lp_state = state

    def get_response(self) -> DFIResponse:
        """Get response from PHY

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
            phy_reset=self.phy.phy_reset
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

    def enter_freq_change(self):
        """Enter frequency change sequence

        Transitions to LP_FREQ_CHANGE state during
        frequency switching.
        """
        self.lp_state = DFILowPowerState.LP_FREQ_CHANGE

    def exit_freq_change(self):
        """Exit frequency change sequence

        Returns to normal operation after frequency change.
        """
        self.lp_state = DFILowPowerState.LP_IDLE

    def queue_request(self, request: DFIRequest):
        """Add request to queue

        Args:
            request: DFI request to queue
        """
        self.request_queue.append(request)

    def get_next_request(self) -> Optional[DFIRequest]:
        """Get next request from queue

        Returns:
            Next DFIRequest or None if queue empty
        """
        if self.request_queue:
            return self.request_queue.pop(0)
        return None

    def add_calibration_data(self, key: str, value: Any):
        """Add calibration data

        Args:
            key: Calibration data key (e.g., 'read_delay', 'write_leveling')
            value: Calibration value
        """
        self.phy.calibration_data[key] = value

    def get_bandwidth_gbs(self) -> float:
        """Get current bandwidth in GB/s

        Returns:
            Bandwidth based on current frequency
        """
        # DFI bandwidth = frequency × width / 8
        # Assuming 64-bit per channel
        return self.frequency_mhz * 64 / 8