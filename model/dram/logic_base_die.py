"""
HBM4 Logic Base Die Model

Unified wrapper integrating all Logic Base Die components for HBM4 simulation.
The Logic Base Die is the control die in the HBM stack that manages:
- Address decoding and routing
- PHY interface and signal encoding
- Training and calibration
- Lane repair and redundancy
- ECC/CRC error handling

Key features:
- Per-channel independent operation (JEDEC requirement)
- Integration with existing modules (PHY, Lane Repair, ECC)
- Cycle-accurate timing model
- DFI 5.0 interface support

Based on:
- JEDEC JESD270-4A HBM4 specification
- Project's existing HBM4 modules
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import existing HBM4 modules
from model.dram.hbm4_spec import HBM4Spec
from model.dram.phy_signal import PAM3SignalModel, HBM4PAM3Encoder
from model.dram.phy_training import (
    HBM4PHYManager,
    PHYTrainingStateMachine,
    PHYInitializationStateMachine,
)
from model.dram.lane_repair import HBM4LaneRepairModel, RepairStatus
from model.dram.ecc_crc import HBM4DataIntegrity, HBM4ECC, HBM4CRC


class ChannelState(Enum):
    """Channel operational state"""
    IDLE = "idle"
    ACTIVE = "active"
    TRAINING = "training"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class ChannelContext:
    """Per-channel execution context

    Each channel maintains independent state including:
    - Local clock domain
    - Timing parameters
    - Bank state machine
    - Pending commands
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


@dataclass
class LogicBaseDieConfig:
    """Configuration for Logic Base Die model"""
    # Architecture
    num_channels: int = 32
    channel_width: int = 64           # JEDEC standard
    burst_width: int = 256           # Data width per channel (4 x 64)

    # Signal encoding
    pam3_enabled: bool = True
    symbol_rate_gbaud: float = 8.0   # 8 Gbaud for HBM4 base rate

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
    |  | PAM3 Encoder     |  | ECC/CRC Engine   |               |
    |  +------------------+  +------------------+               |
    |  +------------------+  +------------------+               |
    |  | PHY Manager      |  | Lane Repair      |               |
    |  +------------------+  +------------------+               |
    +----------------------------------------------------------+
    |              Per-Channel Contexts (x32)                  |
    |  [Ch0] [Ch1] [Ch2] ... [Ch31]                           |
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

        # Initialize PAM3 signal model (if enabled)
        if self.config.pam3_enabled:
            self.pam3_encoder = HBM4PAM3Encoder(config={
                'symbol_rate': self.config.symbol_rate_gbaud * 1e9,
                'voltage_swing': 0.8,
            })
        else:
            self.pam3_encoder = None

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

        # Per-channel contexts (independent operation)
        self._channels: List[ChannelContext] = []
        for ch in range(self.config.num_channels):
            self._channels.append(ChannelContext(channel_id=ch))

        # Global state
        self._global_cycle = 0
        self._initialized = False
        self._training_complete = False

        # Statistics
        self._total_commands = 0
        self._total_errors = 0

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

        Updates all channel contexts and component state machines.
        """
        self._global_cycle += 1

        # Update PHY state machines
        self.phy_manager.tick()

        # Update per-channel local cycles
        for ctx in self._channels:
            ctx.local_cycle += 1

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
            elif phy_status.get('state') != 'INIT_COMPLETE':
                all_ready = False

        if all_ready and self._initialized:
            self._training_complete = True

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
            return handler(ctx, address, data)

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

        return {
            'channel_id': channel_id,
            'state': ctx.state.value,
            'local_cycle': ctx.local_cycle,
            'open_row': ctx.open_row,
            'training_passed': ctx.training_passed,
            'repair_status': ctx.repair_status.value,
            'error_count': ctx.error_count,
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
            'ecc_enabled': self.config.ecc_enabled,
            'crc_enabled': self.config.crc_enabled,
            'channels_ready': sum(1 for ctx in self._channels if ctx.training_passed),
            'channels_total': self.config.num_channels,
        }

    def get_calibration_data(self, channel_id: Optional[int] = None) -> Dict:
        """Get calibration data for channel(s)

        Args:
            channel_id: Specific channel or None for all

        Returns:
            Calibration data dictionary
        """
        if channel_id is not None:
            return self._channels[channel_id].calibration_data

        return {
            f'ch{ch}': ctx.calibration_data
            for ch, ctx in enumerate(self._channels)
            if ctx.calibration_data
        }

    def get_lane_repair_stats(self) -> Dict:
        """Get lane repair statistics

        Returns:
            Lane repair statistics
        """
        return self.lane_repair.get_stats()