"""
HBM4 Lane Repair Model

Implements lane repair functionality for HBM4 channels.

Key features:
- Lane failure tracking and remapping
- Spare lane allocation
- Repair state management
- Integration with PHY training

Based on:
- JEDEC JESD270-4A HBM4 specification
- Cadence HBM4E documentation
- Synopsys HBM4 Controller IP
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random


class RepairStatus(Enum):
    """Lane repair status"""
    NO_REPAIR = "no_repair"
    PARTIAL_REPAIR = "partial_repair"
    FULL_REPAIR = "full_repair"
    UNREPAIRABLE = "unrepairable"


@dataclass
class LaneRepairEntry:
    """Single lane repair entry"""
    failed_lane: int
    spare_lane: int
    repair_type: str  # "bit", "byte", "channel"
    channel_id: int


@dataclass
class LaneRepairMap:
    """Lane repair map for one channel"""
    channel_id: int
    total_lanes: int
    total_spares: int
    failed_lanes: List[int] = field(default_factory=list)
    spare_lanes: List[int] = field(default_factory=list)
    repair_entries: List[LaneRepairEntry] = field(default_factory=list)

    # Repair state
    repair_count: int = 0
    max_repair_count: int = 0  # Set during initialization

    def __post_init__(self):
        if self.max_repair_count == 0:
            self.max_repair_count = self.total_spares

    @property
    def available_spares(self) -> int:
        """Number of spare lanes available"""
        return self.total_spares - len(self.repair_entries)

    @property
    def is_repairable(self) -> bool:
        """Check if more repairs are possible"""
        return len(self.failed_lanes) <= self.total_spares and self.repair_count < self.max_repair_count

    @property
    def status(self) -> RepairStatus:
        """Get current repair status"""
        if len(self.failed_lanes) == 0:
            return RepairStatus.NO_REPAIR
        if len(self.failed_lanes) < self.total_spares:
            return RepairStatus.PARTIAL_REPAIR
        if len(self.failed_lanes) == self.total_spares:
            return RepairStatus.FULL_REPAIR
        return RepairStatus.UNREPAIRABLE


class HBM4LaneRepairModel:
    """HBM4 Lane Repair Model

    Manages lane repair for all channels in the HBM4 stack.

    Key capabilities:
    - Per-channel repair maps
    - Lane failure detection simulation
    - Spare lane allocation
    - Repair state tracking
    - Integration with training state machine
    """

    def __init__(
        self,
        num_channels: int = 32,
        lanes_per_channel: int = 64,
        spare_lanes_per_channel: int = 4,
    ):
        """Initialize Lane Repair Model

        Args:
            num_channels: Number of HBM4 channels (default 32)
            lanes_per_channel: Data lanes per channel (default 64 for x64 DQ)
            spare_lanes_per_channel: Number of spare lanes (typical: 2-4)
        """
        self.num_channels = num_channels
        self.lanes_per_channel = lanes_per_channel
        self.spare_lanes_per_channel = spare_lanes_per_channel

        # Initialize per-channel repair maps
        self._repair_maps: Dict[int, LaneRepairMap] = {}
        for ch in range(num_channels):
            self._repair_maps[ch] = LaneRepairMap(
                channel_id=ch,
                total_lanes=lanes_per_channel,
                total_spares=spare_lanes_per_channel,
            )

        # Global statistics
        self._total_repairs: int = 0
        self._total_failed_lanes: int = 0
        self._unrepairable_channels: List[int] = []

    # ==================== Configuration ====================

    def configure_channel(
        self,
        channel_id: int,
        lanes: int,
        spares: int,
    ) -> None:
        """Configure lane/spare counts for a channel

        Args:
            channel_id: Channel to configure
            lanes: Number of data lanes
            spares: Number of spare lanes
        """
        if channel_id not in self._repair_maps:
            self._repair_maps[channel_id] = LaneRepairMap(
                channel_id=channel_id,
                total_lanes=lanes,
                total_spares=spares,
            )
        else:
            rm = self._repair_maps[channel_id]
            rm.total_lanes = lanes
            rm.total_spares = spares
            rm.max_repair_count = spares

    # ==================== Repair Operations ====================

    def add_failed_lane(self, channel_id: int, lane_id: int) -> bool:
        """Add a failed lane to repair map

        Args:
            channel_id: Channel with failed lane
            lane_id: Failed lane index

        Returns:
            True if lane added successfully
        """
        if channel_id not in self._repair_maps:
            return False

        rm = self._repair_maps[channel_id]

        # Check if lane already tracked
        if lane_id in rm.failed_lanes:
            return True  # Already tracked

        # Check if repair possible
        if not rm.is_repairable:
            if channel_id not in self._unrepairable_channels:
                self._unrepairable_channels.append(channel_id)
            return False

        rm.failed_lanes.append(lane_id)
        self._total_failed_lanes += 1

        return True

    def allocate_spare(
        self,
        channel_id: int,
        failed_lane: int,
        spare_lane: int,
        repair_type: str = "bit",
    ) -> bool:
        """Allocate a spare lane for a failed lane

        Args:
            channel_id: Channel to repair
            failed_lane: Failed lane index
            spare_lane: Spare lane to use
            repair_type: Type of repair ("bit", "byte", "channel")

        Returns:
            True if spare allocated successfully
        """
        if channel_id not in self._repair_maps:
            return False

        rm = self._repair_maps[channel_id]

        # Validate spare lane
        if spare_lane in rm.spare_lanes:
            return False  # Spare already used

        # Check repair capacity
        if rm.available_spares <= 0:
            return False

        # Add repair entry
        entry = LaneRepairEntry(
            failed_lane=failed_lane,
            spare_lane=spare_lane,
            repair_type=repair_type,
            channel_id=channel_id,
        )
        rm.repair_entries.append(entry)
        rm.spare_lanes.append(spare_lane)
        rm.repair_count += 1
        self._total_repairs += 1

        return True

    def perform_repair(
        self,
        channel_id: int,
        failed_lane: int,
        repair_type: str = "bit",
    ) -> Optional[int]:
        """Perform repair by allocating first available spare

        Args:
            channel_id: Channel to repair
            failed_lane: Failed lane index
            repair_type: Type of repair

        Returns:
            Spare lane allocated, or None if repair failed
        """
        if channel_id not in self._repair_maps:
            return None

        rm = self._repair_maps[channel_id]

        # Add failed lane if not already tracked
        if failed_lane not in rm.failed_lanes:
            if not self.add_failed_lane(channel_id, failed_lane):
                return None

        # Find first available spare
        spare_base = rm.total_lanes  # Spares are after data lanes
        for i in range(rm.total_spares):
            spare_lane = spare_base + i
            if spare_lane not in rm.spare_lanes:
                if self.allocate_spare(channel_id, failed_lane, spare_lane, repair_type):
                    return spare_lane

        return None

    def is_lane_remapped(self, channel_id: int, lane_id: int) -> bool:
        """Check if a lane has been remapped to a spare

        Args:
            channel_id: Channel to check
            lane_id: Lane index

        Returns:
            True if lane has been remapped
        """
        if channel_id not in self._repair_maps:
            return False
        rm = self._repair_maps[channel_id]
        return any(e.failed_lane == lane_id for e in rm.repair_entries)

    def get_remapped_lane(self, channel_id: int, lane_id: int) -> int:
        """Get the spare lane that replaces a failed lane

        Args:
            channel_id: Channel to check
            lane_id: Original lane index

        Returns:
            Remapped spare lane index, or original lane if not remapped
        """
        if channel_id not in self._repair_maps:
            return lane_id
        rm = self._repair_maps[channel_id]
        for entry in rm.repair_entries:
            if entry.failed_lane == lane_id:
                return entry.spare_lane
        return lane_id

    # ==================== Query Operations ====================

    def get_channel_repair_map(self, channel_id: int) -> Optional[LaneRepairMap]:
        """Get repair map for a channel

        Args:
            channel_id: Channel to query

        Returns:
            LaneRepairMap or None if channel doesn't exist
        """
        return self._repair_maps.get(channel_id)

    def get_repair_status(self, channel_id: int) -> RepairStatus:
        """Get repair status for a channel

        Args:
            channel_id: Channel to query

        Returns:
            RepairStatus enum value
        """
        if channel_id not in self._repair_maps:
            return RepairStatus.NO_REPAIR
        return self._repair_maps[channel_id].status

    def get_all_failed_lanes(self, channel_id: int) -> List[int]:
        """Get all failed lanes for a channel

        Args:
            channel_id: Channel to query

        Returns:
            List of failed lane indices
        """
        if channel_id not in self._repair_maps:
            return []
        return list(self._repair_maps[channel_id].failed_lanes)

    # ==================== Statistics ====================

    def get_stats(self) -> Dict:
        """Get lane repair statistics

        Returns:
            Dictionary with repair statistics
        """
        total_repairs = sum(rm.repair_count for rm in self._repair_maps.values())
        total_failed = sum(len(rm.failed_lanes) for rm in self._repair_maps.values())

        return {
            'total_channels': self.num_channels,
            'lanes_per_channel': self.lanes_per_channel,
            'spares_per_channel': self.spare_lanes_per_channel,
            'total_repairs': total_repairs,
            'total_failed_lanes': total_failed,
            'unrepairable_channels': len(self._unrepairable_channels),
            'channels_with_repairs': sum(1 for rm in self._repair_maps.values() if rm.repair_count > 0),
        }

    def get_channel_stats(self, channel_id: int) -> Optional[Dict]:
        """Get statistics for a specific channel

        Args:
            channel_id: Channel to query

        Returns:
            Dictionary with channel statistics
        """
        rm = self._repair_maps.get(channel_id)
        if rm is None:
            return None

        return {
            'channel_id': channel_id,
            'failed_lanes': len(rm.failed_lanes),
            'repair_count': rm.repair_count,
            'available_spares': rm.available_spares,
            'status': rm.status.value,
            'is_repairable': rm.is_repairable,
        }

    # ==================== Simulation Support ====================

    def simulate_yield_loss(
        self,
        channel_id: int,
        failure_rate: float = 0.01,
    ) -> int:
        """Simulate random lane failures for yield analysis

        Args:
            channel_id: Channel to simulate
            failure_rate: Probability of each lane failing (0.0-1.0)

        Returns:
            Number of lanes that failed
        """
        if channel_id not in self._repair_maps:
            return 0

        rm = self._repair_maps[channel_id]
        failed_count = 0

        for lane in range(rm.total_lanes):
            if random.random() < failure_rate:
                if lane not in rm.failed_lanes:
                    rm.failed_lanes.append(lane)
                    self._total_failed_lanes += 1
                    failed_count += 1

        return failed_count

    def reset_channel(self, channel_id: int) -> None:
        """Reset repair state for a channel

        Args:
            channel_id: Channel to reset
        """
        if channel_id in self._repair_maps:
            rm = self._repair_maps[channel_id]
            rm.failed_lanes.clear()
            rm.spare_lanes.clear()
            rm.repair_entries.clear()
            rm.repair_count = 0

            if channel_id in self._unrepairable_channels:
                self._unrepairable_channels.remove(channel_id)

    def reset_all(self) -> None:
        """Reset all repair state"""
        for ch in self._repair_maps:
            self.reset_channel(ch)
        self._total_repairs = 0
        self._total_failed_lanes = 0
        self._unrepairable_channels.clear()