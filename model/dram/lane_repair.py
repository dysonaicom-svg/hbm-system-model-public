"""
HBM4 Lane Repair (Redundancy) Model

Implements lane repair functionality for HBM4 channels, providing redundancy
to mitigate DRAM manufacturing defects and improve overall system yield.

LANE ARCHITECTURE:
================
Each HBM4 channel contains N data lanes plus S spare lanes:
  - Data lanes: indices 0 to (lanes_per_channel - 1)
  - Spare lanes: indices lanes_per_channel to (lanes_per_channel + total_spares - 1)

For example, with 64 data lanes and 4 spares:
  - Data lane indices: 0-63
  - Spare lane indices: 64-67

REPAIR TYPES:
============
  - "bit": Single bit repair within a lane (granularity: individual bit)
  - "byte": Byte-level repair (8 bits repaired as a unit)
  - "channel": Full lane/channel repair (entire lane replaced)

REPAIR WORKFLOW:
===============
1. During manufacturing test or PHY training, failed lanes are detected
2. add_failed_lane() or perform_repair() registers the failure
3. Spare lanes are allocated from the available pool
4. Traffic is transparently remapped via get_remapped_lane()

REPAIR LIMITS:
=============
Each channel has a fixed number of spare lanes (typical: 2-4 for HBM4).
When all spares are exhausted, the channel is marked UNREPAIRABLE.
The system tracks repair status per-channel and globally.

Based on:
  - JEDEC JESD270-4A HBM4 specification
  - Cadence HBM4E documentation
  - Synopsys HBM4 Controller IP
"""

from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random
import struct
import time


class RepairStatus(Enum):
    """Lane repair status indicating repair coverage level.

    NO_REPAIR:      No failures detected in this channel
    PARTIAL_REPAIR: Some failures repaired, spares remain available
    FULL_REPAIR:    All spares used, channel fully repaired
    UNREPAIRABLE:  Failures exceed spare capacity
    """
    NO_REPAIR = "no_repair"
    PARTIAL_REPAIR = "partial_repair"
    FULL_REPAIR = "full_repair"
    UNREPAIRABLE = "unrepairable"


class ServiceEventType(Enum):
    """Types of lane repair service events for RAS tracking."""
    REPAIR_COMPLETED = "repair_completed"
    REPAIR_FAILED = "repair_failed"
    SPARE_EXHAUSTED = "spare_exhausted"
    CHANNEL_UNREPAIRABLE = "channel_unrepairable"
    REPAIR_VERIFICATION = "repair_verification"
    REPAIR_UNDO = "repair_undo"
    BULK_REPAIR_LOADED = "bulk_repair_loaded"


class LaneFailureMode(Enum):
    """Classification of lane failure modes for diagnostics."""
    STUCK_AT_0 = "stuck_at_0"
    STUCK_AT_1 = "stuck_at_1"
    FLICKERING = "flickering"
    MARGINAL = "marginal"
    COMPLETE = "complete"


@dataclass
class LaneFailureInfo:
    """Detailed information about a lane failure for diagnostics."""
    lane_id: int
    channel_id: int
    failure_mode: LaneFailureMode
    first_detected_cycle: int
    bit_error_mask: int = 0  # For partial lane failures
    confidence: float = 1.0  # 0.0-1.0 confidence level
    repair_type: str = "bit"


@dataclass
class ServiceEvent:
    """Lane repair service event for RAS tracking."""
    event_type: ServiceEventType
    timestamp: float
    cycle: int
    channel_id: int
    lane_id: Optional[int] = None
    spare_lane: Optional[int] = None
    repair_type: Optional[str] = None
    details: str = ""


@dataclass
class LaneRepairErrorStats:
    """Extended error statistics for lane repair RAS features."""
    total_error_injections: int = 0
    successful_corrections: int = 0
    failed_corrections: int = 0
    remap_transactions: int = 0
    spare_allocation_count: int = 0
    repair_verification_count: int = 0
    repair_undo_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting."""
        return {
            'total_error_injections': self.total_error_injections,
            'successful_corrections': self.successful_corrections,
            'failed_corrections': self.failed_corrections,
            'remap_transactions': self.remap_transactions,
            'spare_allocation_count': self.spare_allocation_count,
            'repair_verification_count': self.repair_verification_count,
            'repair_undo_count': self.repair_undo_count,
        }


@dataclass
class LaneRepairEntry:
    """Single lane repair mapping entry.

    Attributes:
        failed_lane: Index of the defective data lane (0 to lanes-1)
        spare_lane: Index of the replacement spare lane (lanes to lanes+spares-1)
        repair_type: Granularity of repair ("bit", "byte", "channel")
        channel_id: HBM4 channel this repair applies to
    """
    failed_lane: int
    spare_lane: int
    repair_type: str  # "bit", "byte", "channel"
    channel_id: int


@dataclass
class LaneRepairMap:
    """Lane repair map for one HBM4 channel.

    Maintains the complete repair state for a single channel including:
      - List of failed lanes (detected defects)
      - List of allocated spare lanes (in use)
      - Repair entries (failed -> spare mappings)
      - Repair capacity tracking
      - Failure info for diagnostics
      - Service events for RAS tracking

    Lane Indexing Convention:
      - Data lanes: indices 0 to (total_lanes - 1)
      - Spare lanes: indices total_lanes to (total_lanes + total_spares - 1)
    """
    channel_id: int
    total_lanes: int
    total_spares: int
    failed_lanes: List[int] = field(default_factory=list)
    spare_lanes: List[int] = field(default_factory=list)
    repair_entries: List[LaneRepairEntry] = field(default_factory=list)

    # Repair state
    repair_count: int = 0
    max_repair_count: int = 0  # Set during initialization

    # Extended RAS tracking
    failure_info: Dict[int, LaneFailureInfo] = field(default_factory=dict)
    service_events: deque = field(default_factory=lambda: deque(maxlen=100))
    current_cycle: int = 0

    def __post_init__(self):
        if self.max_repair_count == 0:
            self.max_repair_count = self.total_spares

    @property
    def available_spares(self) -> int:
        """Number of spare lanes still available for repair."""
        return self.total_spares - len(self.repair_entries)

    @property
    def is_repairable(self) -> bool:
        """Check if channel can accept more repairs.

        A channel is repairable if:
          - Failed lane count does not exceed total spares
          - Repair count is below maximum (spares available)
        """
        return len(self.failed_lanes) <= self.total_spares and self.repair_count < self.max_repair_count

    @property
    def status(self) -> RepairStatus:
        """Get current repair status based on failed lane count vs spares."""
        if len(self.failed_lanes) == 0:
            return RepairStatus.NO_REPAIR
        if len(self.failed_lanes) < self.total_spares:
            return RepairStatus.PARTIAL_REPAIR
        if len(self.failed_lanes) == self.total_spares:
            return RepairStatus.FULL_REPAIR
        return RepairStatus.UNREPAIRABLE

    def get_failure_info(self, lane_id: int) -> Optional[LaneFailureInfo]:
        """Get failure information for a specific lane."""
        return self.failure_info.get(lane_id)

    def get_all_failure_info(self) -> List[LaneFailureInfo]:
        """Get all failure information."""
        return list(self.failure_info.values())

    def get_recent_service_events(self, count: int = 10) -> List[ServiceEvent]:
        """Get recent service events."""
        return list(self.service_events)[-count:]

    def record_service_event(
        self,
        event_type: ServiceEventType,
        lane_id: Optional[int] = None,
        spare_lane: Optional[int] = None,
        repair_type: Optional[str] = None,
        details: str = "",
    ):
        """Record a service event."""
        event = ServiceEvent(
            event_type=event_type,
            timestamp=time.time(),
            cycle=self.current_cycle,
            channel_id=self.channel_id,
            lane_id=lane_id,
            spare_lane=spare_lane,
            repair_type=repair_type,
            details=details,
        )
        self.service_events.append(event)


class HBM4LaneRepairModel:
    """HBM4 Lane Repair (Redundancy) Model

    Manages lane repair for all channels in the HBM4 stack. This model
    implements the redundancy mechanism used in HBM devices to improve
    manufacturing yield by providing spare lanes to replace defective ones.

    KEY CAPABILITIES:
    =================
    - Per-channel repair maps: Each of N channels has independent repair tracking
    - Spare lane allocation: Automatic selection from available spare pool
    - Lane remapping: Transparent traffic redirection via get_remapped_lane()
    - Repair status tracking: NO_REPAIR -> PARTIAL_REPAIR -> FULL_REPAIR -> UNREPAIRABLE
    - Yield simulation: Simulate random failures to analyze system-level impact
    - Error injection: Test error detection and correction paths
    - Service events: Track repair operations for RAS compliance
    - Failure diagnostics: Record failure modes and confidence levels

    USAGE EXAMPLE:
    ==============
    ```python
    # Create model for 32-channel HBM4 (64 DQ lanes + 4 spare per channel)
    model = HBM4LaneRepairModel(num_channels=32, lanes_per_channel=64, spare_lanes_per_channel=4)

    # Detect and repair a failed lane
    spare = model.perform_repair(channel_id=0, failed_lane=42)
    if spare is not None:
        print(f"Remapped lane 42 -> spare {spare}")

    # Check remapping for data traffic
    actual_lane = model.get_remapped_lane(channel_id=0, lane_id=42)  # Returns spare index
    actual_lane = model.get_remapped_lane(channel_id=0, lane_id=10)  # Returns 10 (no remap)

    # Query system health
    stats = model.get_stats()
    print(f"Total repairs: {stats['total_repairs']}, Unrepairable channels: {stats['unrepairable_channels']}")

    # Error injection for testing
    model.inject_lane_error(channel_id=0, lane_id=10, error_mask=0xFF)
    ```

    INTEGRATION POINTS:
    ===================
    - PHY Training: Report failed lanes detected during margin testing
    - Memory BIST: Register defects found during manufacturing test
    - Traffic Monitor: Use get_remapped_lane() to redirect traffic through spares
    - System Simulation: simulate_yield_loss() for statistical analysis
    - ECC/CRC: Integrate with error tracking for RAS compliance
    """

    def __init__(
        self,
        num_channels: int = 32,
        lanes_per_channel: int = 64,
        spare_lanes_per_channel: int = 4,
        enable_service_events: bool = True,
        enable_error_injection: bool = True,
    ):
        """Initialize Lane Repair Model

        Args:
            num_channels: Number of HBM4 channels (default 32 for full HBM4 stack)
            lanes_per_channel: Data lanes per channel (default 64 for x64 DQ interface)
            spare_lanes_per_channel: Number of spare lanes (typical: 2-4 per JEDEC)
            enable_service_events: Enable service event tracking for RAS
            enable_error_injection: Enable error injection for testing
        """
        self.num_channels = num_channels
        self.lanes_per_channel = lanes_per_channel
        self.spare_lanes_per_channel = spare_lanes_per_channel
        self.enable_service_events = enable_service_events
        self.enable_error_injection = enable_error_injection

        # Simulation cycle counter
        self._current_cycle: int = 0
        self._start_time: float = time.time()

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

        # Extended RAS statistics
        self._error_stats = LaneRepairErrorStats()
        self._global_service_events: deque = deque(maxlen=1000)

        # Error injection state (for testing)
        self._injected_errors: Dict[int, Dict[int, int]] = {}  # channel -> lane -> error_mask

        # Callback hooks for integration
        self._on_repair_complete: Optional[Callable] = None
        self._on_channel_unrepairable: Optional[Callable] = None

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

    def add_failed_lane(
        self,
        channel_id: int,
        lane_id: int,
        failure_mode: LaneFailureMode = LaneFailureMode.COMPLETE,
        bit_error_mask: int = 0,
        confidence: float = 1.0,
    ) -> bool:
        """Add a failed lane to repair map

        Args:
            channel_id: Channel with failed lane
            lane_id: Failed lane index
            failure_mode: Classification of failure type
            bit_error_mask: Bit mask for partial failures (8 bits for byte-level)
            confidence: Confidence level 0.0-1.0 for failure detection

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
                self._record_service_event(
                    rm, ServiceEventType.CHANNEL_UNREPAIRABLE,
                    details=f"Channel {channel_id} has {len(rm.failed_lanes)} failed lanes, exceeds {rm.total_spares} spares"
                )
            return False

        rm.failed_lanes.append(lane_id)
        self._total_failed_lanes += 1

        # Record failure info for diagnostics
        rm.failure_info[lane_id] = LaneFailureInfo(
            lane_id=lane_id,
            channel_id=channel_id,
            failure_mode=failure_mode,
            first_detected_cycle=rm.current_cycle,
            bit_error_mask=bit_error_mask,
            confidence=confidence,
        )

        return True

    def perform_repair(
        self,
        channel_id: int,
        failed_lane: int,
        repair_type: str = "bit",
        failure_mode: LaneFailureMode = LaneFailureMode.COMPLETE,
    ) -> Optional[int]:
        """Perform repair by allocating first available spare lane.

        This is the main repair operation - it:
          1. Checks if lane is already remapped (return existing spare)
          2. Adds the failed lane to the track list (if not already tracked)
          3. Finds the first available spare lane
          4. Creates the repair mapping entry

        Args:
            channel_id: Channel to repair
            failed_lane: Failed lane index (0 to lanes_per_channel-1)
            repair_type: Granularity of repair ("bit", "byte", "channel")
            failure_mode: Classification of the failure for diagnostics

        Returns:
            Spare lane index allocated, or None if repair failed (no spares available)
        """
        if channel_id not in self._repair_maps:
            return None

        rm = self._repair_maps[channel_id]

        # Check if lane is already remapped - return existing spare
        for entry in rm.repair_entries:
            if entry.failed_lane == failed_lane:
                return entry.spare_lane

        # Add failed lane if not already tracked
        if failed_lane not in rm.failed_lanes:
            if not self.add_failed_lane(channel_id, failed_lane, failure_mode):
                self._record_service_event(
                    rm, ServiceEventType.REPAIR_FAILED,
                    lane_id=failed_lane,
                    details=f"Failed to add lane {failed_lane} - unrepairable"
                )
                self._error_stats.failed_corrections += 1
                return None

        # Find first available spare
        spare_base = rm.total_lanes  # Spares are after data lanes
        for i in range(rm.total_spares):
            spare_lane = spare_base + i
            if spare_lane not in rm.spare_lanes:
                if self.allocate_spare(channel_id, failed_lane, spare_lane, repair_type):
                    # Record service event
                    self._record_service_event(
                        rm, ServiceEventType.REPAIR_COMPLETED,
                        lane_id=failed_lane,
                        spare_lane=spare_lane,
                        repair_type=repair_type,
                        details=f"Repaired lane {failed_lane} using spare {spare_lane}"
                    )
                    self._error_stats.successful_corrections += 1

                    # Update failure info with repair type
                    if failed_lane in rm.failure_info:
                        rm.failure_info[failed_lane].repair_type = repair_type

                    # Check if spares exhausted
                    if rm.available_spares == 0:
                        self._record_service_event(
                            rm, ServiceEventType.SPARE_EXHAUSTED,
                            details=f"All {rm.total_spares} spares exhausted on channel {channel_id}"
                        )

                    # Invoke callback if registered
                    if self._on_repair_complete:
                        self._on_repair_complete(channel_id, failed_lane, spare_lane)

                    return spare_lane

        # No spare available
        self._record_service_event(
            rm, ServiceEventType.REPAIR_FAILED,
            lane_id=failed_lane,
            details=f"No spare lanes available for lane {failed_lane}"
        )
        self._error_stats.failed_corrections += 1
        return None

    def _record_service_event(
        self,
        rm: LaneRepairMap,
        event_type: ServiceEventType,
        lane_id: Optional[int] = None,
        spare_lane: Optional[int] = None,
        repair_type: Optional[str] = None,
        details: str = "",
    ):
        """Record a service event both locally and globally."""
        if not self.enable_service_events:
            return

        event = ServiceEvent(
            event_type=event_type,
            timestamp=time.time(),
            cycle=rm.current_cycle,
            channel_id=rm.channel_id,
            lane_id=lane_id,
            spare_lane=spare_lane,
            repair_type=repair_type,
            details=details,
        )

        rm.service_events.append(event)
        self._global_service_events.append(event)

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
        self._error_stats.spare_allocation_count += 1

        return True

    def is_lane_remapped(self, channel_id: int, lane_id: int) -> bool:
        """Check if a lane has been remapped to a spare.

        Use this to determine if traffic for a given lane should be redirected.

        Args:
            channel_id: Channel to check
            lane_id: Lane index to query

        Returns:
            True if lane has been remapped to a spare lane
        """
        if channel_id not in self._repair_maps:
            return False
        rm = self._repair_maps[channel_id]
        return any(e.failed_lane == lane_id for e in rm.repair_entries)

    def get_remapped_lane(self, channel_id: int, lane_id: int) -> int:
        """Get the spare lane that replaces a failed lane.

        This is the primary interface for traffic redirection - use in the data path
        to transparently route traffic through spare lanes.

        Args:
            channel_id: Channel to check
            lane_id: Original (failed) lane index

        Returns:
            Spare lane index if remapped, otherwise returns original lane_id
        """
        if channel_id not in self._repair_maps:
            return lane_id
        rm = self._repair_maps[channel_id]
        for entry in rm.repair_entries:
            if entry.failed_lane == lane_id:
                self._error_stats.remap_transactions += 1
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
        """Simulate random lane failures for yield analysis.

        Used for statistical analysis of system yield. Each lane has an independent
        probability of failure based on failure_rate.

        Args:
            channel_id: Channel to simulate failures on
            failure_rate: Probability of each lane failing (0.0 to 1.0).
                          Default 0.01 (1% per lane).

        Returns:
            Number of lanes that failed in this simulation run
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
        """Reset repair state for a channel (e.g., for new test scenario).

        Clears all repair entries, failed lanes, and statistics for the channel.
        Does not affect other channels.

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
        """Reset all repair state across all channels.

        Clears all repair maps, failed lanes, and global statistics.
        Useful for running multiple independent test scenarios.
        """
        for ch in self._repair_maps:
            self.reset_channel(ch)
        self._total_repairs = 0
        self._total_failed_lanes = 0
        self._unrepairable_channels.clear()

    # ==================== Repair Sequence Generation ====================

    def generate_repair_sequence(self, channel_id: int) -> Optional[List[Dict[str, Any]]]:
        """Generate repair programming sequence for eFuse/fuse box.

        Creates a sequence of repair entries that can be programmed into
        non-volatile storage (eFuses) for permanent lane remapping.

        Args:
            channel_id: Channel to generate sequence for

        Returns:
            List of repair entries, each containing:
              - failed_lane: Original lane index
              - spare_lane: Replacement spare lane index
              - repair_type: Type of repair ("bit", "byte", "channel")
              - encoding: Encoded value for fuse programming
            Returns None if channel doesn't exist or has no repairs
        """
        if channel_id not in self._repair_maps:
            return None

        rm = self._repair_maps[channel_id]
        if not rm.repair_entries:
            return None

        sequence = []
        for entry in rm.repair_entries:
            sequence.append({
                'failed_lane': entry.failed_lane,
                'spare_lane': entry.spare_lane,
                'repair_type': entry.repair_type,
                'encoding': self._encode_repair_entry(entry),
            })

        return sequence

    def _encode_repair_entry(self, entry: LaneRepairEntry) -> int:
        """Encode repair entry into a single integer for fuse programming.


        Encoding format (32 bits):
          [31:24] - Repair type (0=bit, 1=byte, 2=channel)
          [23:16] - Channel ID (0-255)
          [15:8]  - Failed lane (0-255)
          [7:0]   - Spare lane (0-255)

        Args:
            entry: Repair entry to encode

        Returns:
            32-bit encoded value
        """
        type_map = {'bit': 0, 'byte': 1, 'channel': 2}
        type_val = type_map.get(entry.repair_type, 0)

        encoding = (type_val << 24) | (entry.channel_id << 16) | \
                   (entry.failed_lane << 8) | entry.spare_lane
        return encoding

    def decode_repair_entry(self, encoding: int) -> Dict[str, Any]:
        """Decode a fused repair entry back to components.

        Args:
            encoding: 32-bit encoded value

        Returns:
            Dictionary with decoded fields:
              - repair_type: String ("bit", "byte", "channel")
              - channel_id: Channel number
              - failed_lane: Original lane index
              - spare_lane: Replacement spare index
        """
        type_map = {0: 'bit', 1: 'byte', 2: 'channel'}
        type_val = (encoding >> 24) & 0xFF
        channel_id = (encoding >> 16) & 0xFF
        failed_lane = (encoding >> 8) & 0xFF
        spare_lane = encoding & 0xFF

        return {
            'repair_type': type_map.get(type_val, 'bit'),
            'channel_id': channel_id,
            'failed_lane': failed_lane,
            'spare_lane': spare_lane,
        }

    def generate_bulk_repair_sequence(self) -> Dict[int, List[Dict[str, Any]]]:
        """Generate repair sequences for all channels.

        Creates a complete programming sequence for all channels with repairs.
        Useful for mass programming of eFuses during manufacturing.

        Returns:
            Dictionary mapping channel_id -> list of repair entries
        """
        bulk_sequence = {}
        for ch_id in self._repair_maps:
            seq = self.generate_repair_sequence(ch_id)
            if seq:
                bulk_sequence[ch_id] = seq
        return bulk_sequence

    def export_repair_map(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Export complete repair map for a channel.

        Creates a serializable dictionary representation of the repair state
        for persistence or transmission to other systems.

        Args:
            channel_id: Channel to export

        Returns:
            Dictionary containing:
              - channel_id: Channel number
              - total_lanes: Number of data lanes
              - total_spares: Number of spare lanes
              - repair_entries: List of repair mappings
              - status: Repair status string
              - encoding: Encoded fuse values for each repair
        """
        if channel_id not in self._repair_maps:
            return None

        rm = self._repair_maps[channel_id]
        entries = []
        for entry in rm.repair_entries:
            entries.append({
                'failed_lane': entry.failed_lane,
                'spare_lane': entry.spare_lane,
                'repair_type': entry.repair_type,
                'encoding': self._encode_repair_entry(entry),
            })

        return {
            'channel_id': channel_id,
            'total_lanes': rm.total_lanes,
            'total_spares': rm.total_spares,
            'repair_entries': entries,
            'status': rm.status.value,
            'failed_lanes': list(rm.failed_lanes),
        }

    def import_repair_map(self, data: Dict[str, Any]) -> bool:
        """Import repair map from serialized data.

        Restores repair state from a previously exported repair map.
        Useful for loading manufacturing test results.

        Args:
            data: Dictionary from export_repair_map()

        Returns:
            True if import succeeded
        """
        try:
            channel_id = data['channel_id']
            total_lanes = data['total_lanes']
            total_spares = data['total_spares']

            # Configure channel
            self.configure_channel(channel_id, total_lanes, total_spares)

            # Reset existing state
            self.reset_channel(channel_id)

            # Restore repairs
            for entry_data in data['repair_entries']:
                failed_lane = entry_data['failed_lane']
                spare_lane = entry_data['spare_lane']
                repair_type = entry_data['repair_type']

                self.add_failed_lane(channel_id, failed_lane)
                self.allocate_spare(channel_id, failed_lane, spare_lane, repair_type)

            return True
        except (KeyError, TypeError):
            return False

    def verify_repair_integrity(self, channel_id: int) -> Dict[str, Any]:
        """Verify repair state integrity for a channel.

        Checks that repair mappings are internally consistent:
          - No duplicate failed lanes
          - No duplicate spare lanes
          - All spare lanes are valid (in spare range)
          - Repair count matches entry count

        Args:
            channel_id: Channel to verify

        Returns:
            Dictionary with:
              - valid: Boolean indicating if state is valid
              - errors: List of error strings (empty if valid)
              - warnings: List of warning strings
        """
        if channel_id not in self._repair_maps:
            return {'valid': False, 'errors': ['Channel not found'], 'warnings': []}

        rm = self._repair_maps[channel_id]
        errors = []
        warnings = []

        # Check for duplicate failed lanes
        if len(rm.failed_lanes) != len(set(rm.failed_lanes)):
            errors.append('Duplicate failed lanes detected')

        # Check for duplicate spare lanes
        if len(rm.spare_lanes) != len(set(rm.spare_lanes)):
            errors.append('Duplicate spare lanes detected')

        # Check spare lane range
        spare_base = rm.total_lanes
        spare_top = rm.total_lanes + rm.total_spares
        for spare in rm.spare_lanes:
            if spare < spare_base or spare >= spare_top:
                errors.append(f'Invalid spare lane {spare} (valid range: {spare_base}-{spare_top-1})')

        # Check failed lane range
        for failed in rm.failed_lanes:
            if failed < 0 or failed >= rm.total_lanes:
                errors.append(f'Invalid failed lane {failed} (valid range: 0-{rm.total_lanes-1})')

        # Check repair count matches
        if rm.repair_count != len(rm.repair_entries):
            errors.append(f'Repair count mismatch: {rm.repair_count} != {len(rm.repair_entries)}')

        # Check entry consistency
        for entry in rm.repair_entries:
            if entry.channel_id != channel_id:
                errors.append(f'Entry channel mismatch: {entry.channel_id} != {channel_id}')

        # Warnings
        if rm.available_spares == 0 and rm.status != RepairStatus.UNREPAIRABLE:
            warnings.append('All spares used')

        if rm.status == RepairStatus.UNREPAIRABLE:
            warnings.append('Channel marked unrepairable')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
        }

    # ==================== Error Injection for Testing ====================

    def inject_lane_error(
        self,
        channel_id: int,
        lane_id: int,
        error_mask: int = 0xFF,
        failure_mode: LaneFailureMode = LaneFailureMode.COMPLETE,
    ) -> bool:
        """Inject an error into a lane for testing error detection paths.

        This is used to test that the error detection and correction
        mechanisms work properly.

        Args:
            channel_id: Channel with the lane to inject error into
            lane_id: Lane index to inject error into (0 to lanes-1)
            error_mask: 8-bit mask for partial lane errors (which bits to corrupt)
            failure_mode: Classification of the failure for diagnostics

        Returns:
            True if error injection succeeded
        """
        if not self.enable_error_injection:
            return False

        if channel_id not in self._repair_maps:
            return False

        rm = self._repair_maps[channel_id]
        if lane_id < 0 or lane_id >= rm.total_lanes:
            return False

        # Record injected error
        if channel_id not in self._injected_errors:
            self._injected_errors[channel_id] = {}
        self._injected_errors[channel_id][lane_id] = error_mask
        self._error_stats.total_error_injections += 1

        # Record failure info if not already tracked
        if lane_id not in rm.failed_lanes:
            rm.failed_lanes.append(lane_id)
            rm.failure_info[lane_id] = LaneFailureInfo(
                lane_id=lane_id,
                channel_id=channel_id,
                failure_mode=failure_mode,
                first_detected_cycle=rm.current_cycle,
                bit_error_mask=error_mask,
                confidence=1.0,
            )

        return True

    def clear_injected_error(self, channel_id: int, lane_id: int) -> bool:
        """Clear an injected error (for recovery testing).

        Args:
            channel_id: Channel with the injected error
            lane_id: Lane index to clear

        Returns:
            True if error was cleared
        """
        if channel_id in self._injected_errors:
            if lane_id in self._injected_errors[channel_id]:
                del self._injected_errors[channel_id][lane_id]
                return True
        return False

    def get_injected_errors(self, channel_id: int) -> Dict[int, int]:
        """Get all injected errors for a channel.

        Args:
            channel_id: Channel to query

        Returns:
            Dictionary mapping lane_id to error_mask
        """
        return self._injected_errors.get(channel_id, {}).copy()

    def clear_all_injected_errors(self) -> None:
        """Clear all injected errors."""
        self._injected_errors.clear()

    def apply_error_to_data(self, data: int, lane_id: int, error_mask: int) -> int:
        """Apply an injected error to data.

        This simulates the effect of a lane failure on actual data.

        Args:
            data: Original data (64-bit for a lane)
            lane_id: Lane index
            error_mask: 8-bit mask for which bits to corrupt

        Returns:
            Corrupted data
        """
        # XOR with error mask (corrupt bits where mask has 1s)
        return data ^ error_mask

    # ==================== Service Events ====================

    def get_service_events(
        self,
        channel_id: Optional[int] = None,
        event_type: Optional[ServiceEventType] = None,
        count: int = 100,
    ) -> List[ServiceEvent]:
        """Get service events, optionally filtered.

        Args:
            channel_id: Filter by channel (None for all channels)
            event_type: Filter by event type (None for all types)
            count: Maximum number of events to return

        Returns:
            List of service events
        """
        events = list(self._global_service_events)

        if channel_id is not None:
            events = [e for e in events if e.channel_id == channel_id]

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        return events[-count:]

    def get_channel_service_events(
        self,
        channel_id: int,
        count: int = 100,
    ) -> List[ServiceEvent]:
        """Get service events for a specific channel.

        Args:
            channel_id: Channel to query
            count: Maximum number of events to return

        Returns:
            List of service events for the channel
        """
        rm = self._repair_maps.get(channel_id)
        if rm is None:
            return []
        return list(rm.service_events)[-count:]

    # ==================== Cycle Tracking ====================

    def advance_cycle(self, cycles: int = 1) -> None:
        """Advance the simulation cycle counter.

        This is used for timing-related diagnostics.

        Args:
            cycles: Number of cycles to advance
        """
        self._current_cycle += cycles
        for rm in self._repair_maps.values():
            rm.current_cycle += cycles

    def set_cycle(self, cycle: int) -> None:
        """Set the simulation cycle counter.

        Args:
            cycle: Cycle number to set
        """
        self._current_cycle = cycle
        for rm in self._repair_maps.values():
            rm.current_cycle = cycle

    def get_cycle(self) -> int:
        """Get the current simulation cycle.

        Returns:
            Current cycle number
        """
        return self._current_cycle

    def get_uptime(self) -> float:
        """Get elapsed time since model creation.

        Returns:
            Elapsed time in seconds
        """
        return time.time() - self._start_time

    # ==================== Callbacks ====================

    def register_repair_complete_callback(
        self,
        callback: Callable[[int, int, int], None],
    ) -> None:
        """Register a callback for repair completion events.

        The callback will be invoked with (channel_id, failed_lane, spare_lane)
        when a repair is completed.

        Args:
            callback: Function to call on repair completion
        """
        self._on_repair_complete = callback

    def register_unrepairable_callback(
        self,
        callback: Callable[[int], None],
    ) -> None:
        """Register a callback for unrepairable channel events.

        The callback will be invoked with (channel_id,) when a channel
        becomes unrepairable.

        Args:
            callback: Function to call when channel becomes unrepairable
        """
        self._on_channel_unrepairable = callback

    # ==================== Enhanced Statistics ====================

    def get_error_stats(self) -> Dict:
        """Get extended error statistics for RAS reporting.

        Returns:
            Dictionary with detailed error statistics
        """
        return self._error_stats.to_dict()

    def get_full_stats(self) -> Dict:
        """Get complete statistics including all RAS metrics.

        Returns:
            Dictionary with comprehensive statistics
        """
        basic_stats = self.get_stats()
        error_stats = self.get_error_stats()

        return {
            **basic_stats,
            **error_stats,
            'current_cycle': self._current_cycle,
            'uptime_seconds': self.get_uptime(),
            'total_service_events': len(self._global_service_events),
        }

    def get_repair_efficiency(self) -> float:
        """Calculate repair efficiency (repairs attempted vs successful).

        Returns:
            Efficiency as a percentage (0-100)
        """
        total_attempted = (
            self._error_stats.successful_corrections +
            self._error_stats.failed_corrections
        )
        if total_attempted == 0:
            return 100.0
        return (self._error_stats.successful_corrections / total_attempted) * 100.0

    # ==================== Integration Helpers ====================

    def get_lane_bit_error_rate(
        self,
        channel_id: int,
        lane_id: int,
    ) -> Optional[float]:
        """Calculate bit error rate for a specific lane.

        Based on failure info and repair attempts.

        Args:
            channel_id: Channel to query
            lane_id: Lane to query

        Returns:
            Estimated bit error rate, or None if no data
        """
        rm = self._repair_maps.get(channel_id)
        if rm is None or lane_id not in rm.failure_info:
            return None

        info = rm.failure_info[lane_id]
        if info.bit_error_mask == 0:
            return 0.0

        # Calculate as bits in error / total bits
        bits_in_error = bin(info.bit_error_mask).count('1')
        return bits_in_error / 8.0  # 8 bits per lane

    def get_failure_analysis(self, channel_id: int) -> Dict:
        """Get comprehensive failure analysis for a channel.

        Args:
            channel_id: Channel to analyze

        Returns:
            Dictionary with failure statistics and patterns
        """
        rm = self._repair_maps.get(channel_id)
        if rm is None:
            return {}

        failure_modes = {}
        for info in rm.failure_info.values():
            mode = info.failure_mode.value
            failure_modes[mode] = failure_modes.get(mode, 0) + 1

        return {
            'channel_id': channel_id,
            'total_failures': len(rm.failure_info),
            'failure_modes': failure_modes,
            'repairs_completed': rm.repair_count,
            'spares_remaining': rm.available_spares,
            'status': rm.status.value,
        }
