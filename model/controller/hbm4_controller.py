"""
HBM4 Controller Integration

Integrates all HBM4-specific modules into a complete controller model.

Key modules:
- HBM4AddressDecoder: 32-channel address decoding
- HBM4QoSScheduler: 16-level QoS scheduling
- HBM4RefreshScheduler: Per-bank and autonomous refresh
- HBM4ChannelModel: DRAM channel timing
- DFI5Interface: Controller-PHY interface

Based on:
- JEDEC JESD270-4A HBM4 specification
- Multi-agent research findings (2026-06-15)
"""

from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
import time
import uuid

from model.dram.hbm4_spec import HBM4Spec
from model.controller.config import HBMConfig
from model.controller.request import HBMRequest, HBMResponse, RequestState
from model.controller.queue import ReadQueue, WriteQueue, QueueManager
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.controller.exceptions import QueueOverflowError


@dataclass
class HBM4ControllerStats:
    """Statistics for HBM4 Controller"""
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    row_hit_count: int = 0
    refresh_count: int = 0
    training_count: int = 0
    repair_count: int = 0
    total_latency_ns: float = 0.0
    total_bandwidth_bytes: float = 0.0

    @property
    def average_latency_ns(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ns / self.total_requests

    @property
    def row_hit_rate(self) -> float:
        if self.read_requests + self.write_requests == 0:
            return 0.0
        return self.row_hit_count / (self.read_requests + self.write_requests)


class HBM4Controller:
    """HBM4 Memory Controller Integration

    This controller integrates all HBM4-specific modules:
    - 32 independent channels
    - Per-channel and pseudo-channel scheduling
    - QoS-based request prioritization
    - Per-bank and autonomous refresh
    - DFI-like PHY interface abstraction
    - Lane repair and training support
    """

    def __init__(
        self,
        spec: Optional[HBM4Spec] = None,
        config: Optional[HBMConfig] = None,
        enable_qos: bool = True,
        enable_refresh: bool = True,
    ):
        """Initialize HBM4 Controller

        Args:
            spec: HBM4 specification (uses default if None)
            config: Optional HBMConfig for base class compatibility
            enable_qos: Enable QoS scheduling
            enable_refresh: Enable refresh scheduling
        """
        self.spec = spec or HBM4Spec()
        self.current_time_ns = 0
        self._cycle_count = 0

        # Configuration
        self._enable_qos = enable_qos
        self._enable_refresh = enable_refresh

        # Initialize HBM4-specific address decoder
        self.decoder = HBM4AddressDecoder(spec=self.spec)

        # Initialize queue manager with HBM4 channel count
        # Each channel gets a portion of the total queue depth
        # Allow 8 requests per channel to ensure all channels can submit simultaneously
        per_channel_queue = 8  # Fixed capacity per channel
        self.queue_manager = QueueManager.create(queue_depth=per_channel_queue * self.spec.channels)

        # Initialize QoS scheduler
        if self._enable_qos:
            self.qos_scheduler = HBM4QoSScheduler(config=self.spec)
        else:
            self.qos_scheduler = None

        # Initialize refresh scheduler
        if self._enable_refresh:
            self.refresh_scheduler = HBM4RefreshScheduler(config=self.spec)
        else:
            self.refresh_scheduler = None

        # Per-channel state tracking
        self._channel_states: Dict[int, 'ChannelState'] = {}
        for ch in range(self.spec.channels):
            self._channel_states[ch] = ChannelState(channel_id=ch)

        # Statistics
        self.stats = HBM4ControllerStats()

        # Request tracking
        self._pending_requests: Dict[str, HBMRequest] = {}
        self._completed_requests: List[HBMResponse] = []

    @property
    def channels(self) -> int:
        """Number of HBM4 channels"""
        return self.spec.channels

    @property
    def pseudo_channels(self) -> int:
        """Total pseudo-channels"""
        return self.spec.pseudo_channels

    def submit_request(
        self,
        addr: int,
        is_read: bool,
        qos_level: int = 8,
        size_bytes: int = 64,
    ) -> Optional[str]:
        """Submit a request to the controller

        Args:
            addr: 64-bit physical address
            is_read: True for read, False for write
            qos_level: QoS priority level (0-15, lower = higher priority)
            size_bytes: Request size in bytes

        Returns:
            Request ID if successful, None if queue full
        """
        # Decode address
        decoded = self.decoder.decode(addr)

        # Create request
        request = HBMRequest(
            addr=addr,
            length=size_bytes,
            is_read=is_read,
            qos=qos_level,
            channel_id=decoded.channel_id,
            pseudo_channel_id=decoded.pseudo_channel_id,
            bank_id=decoded.bank_id,
            row_id=decoded.row_id,
            col_id=decoded.col_id,
        )
        request.arrival_time = self.current_time_ns

        # Enqueue request - queue push returns success/failure
        if is_read:
            success = self.queue_manager.push_read(request)
        else:
            success = self.queue_manager.push_write(request)

        if not success:
            return None

        # Track request
        self._pending_requests[request.request_id] = request

        # Update statistics
        self.stats.total_requests += 1
        if is_read:
            self.stats.read_requests += 1
        else:
            self.stats.write_requests += 1

        return request.request_id

    def tick(self) -> List[HBMResponse]:
        """Execute one clock cycle

        Returns:
            List of completed responses this cycle
        """
        self._cycle_count += 1
        self.current_time_ns += 1  # 1ns per cycle at 1 GHz

        responses = []

        # Handle refresh if enabled
        if self.refresh_scheduler:
            self.refresh_scheduler.tick()
            refresh_response = self._handle_refresh()
            if refresh_response:
                responses.append(refresh_response)

        # Handle per-channel scheduling
        for ch_id in range(self.spec.channels):
            response = self._schedule_channel(ch_id)
            if response:
                responses.append(response)

        # Handle training/repair if needed
        self._handle_background_tasks()

        return responses

    def _handle_refresh(self) -> Optional[HBMResponse]:
        """Handle refresh scheduling

        Returns:
            Refresh response if refresh completed
        """
        if not self.refresh_scheduler:
            return None

        # Check if refresh is needed
        if self.refresh_scheduler.can_refresh():
            # Get next bank to refresh
            bank_info = self.refresh_scheduler.get_next_refresh_bank()
            if bank_info:
                channel_id, bank_id = bank_info

                # Execute refresh
                self.refresh_scheduler.mark_bank_refreshed(
                    channel_id, bank_id, self._cycle_count
                )
                self.stats.refresh_count += 1

                return HBMResponse(
                    request_id=f"refresh_ch{channel_id}_bank{bank_id}",
                    status="REFRESH_COMPLETE",
                    latency=self.spec.nRFC,
                    channel_id=channel_id,
                    bank_id=bank_id,
                )

        return None

    def _schedule_channel(self, channel_id: int) -> Optional[HBMResponse]:
        """Schedule requests for a specific channel

        Args:
            channel_id: Channel to schedule

        Returns:
            Response if request completed
        """
        channel_state = self._channel_states[channel_id]

        # Get requests for this channel
        read_queue = self.queue_manager.read_queue
        write_queue = self.queue_manager.write_queue

        # Filter requests for this channel
        ch_reads = [r for r in read_queue if r.channel_id == channel_id]
        ch_writes = [r for r in write_queue if r.channel_id == channel_id]

        if not ch_reads and not ch_writes:
            return None

        # Select request based on QoS if enabled
        if self.qos_scheduler and self._enable_qos:
            # Use QoS scheduler to select highest priority request
            all_requests = ch_reads + ch_writes
            selected = self.qos_scheduler.select_next(all_requests)
        else:
            # Simple FCFS
            all_requests = ch_reads + ch_writes
            if all_requests:
                selected = min(all_requests, key=lambda r: r.arrival_time)
            else:
                selected = None

        if not selected:
            return None

        # Calculate latency based on row hit/miss
        if selected.row_hit:
            latency = self.spec.nCL + self.spec.nBL
            self.stats.row_hit_count += 1
        else:
            latency = self.spec.nCL + self.spec.nBL + self.spec.nRCDRD

        # Mark request completed
        selected.mark_completed(self.current_time_ns)

        # Update statistics
        self.stats.total_latency_ns += latency
        self.stats.total_bandwidth_bytes += selected.length

        # Remove from queue
        if selected.is_read:
            read_queue.remove(selected.request_id)
        else:
            write_queue.remove(selected.request_id)

        # Update channel state
        channel_state.queue_depth = max(0, channel_state.queue_depth - 1)

        # Remove from pending
        if selected.request_id in self._pending_requests:
            del self._pending_requests[selected.request_id]

        return HBMResponse(
            request_id=selected.request_id,
            status="OK",
            latency=latency,
            channel_id=channel_id,
            bank_id=selected.bank_id,
        )

    def _handle_background_tasks(self) -> None:
        """Handle background tasks like training and repair"""
        # Training is typically triggered externally
        # This is a placeholder for the model
        pass

    def _get_queue_capacity(self) -> int:
        """Get per-channel queue capacity"""
        return 8  # 8 requests per channel

    def trigger_training(self, channel_id: Optional[int] = None) -> str:
        """Trigger training for a channel or all channels

        Args:
            channel_id: Specific channel to train, or None for all

        Returns:
            Training command ID
        """
        training_id = f"train_{uuid.uuid4().hex[:8]}"
        self.stats.training_count += 1

        # Training is modeled as a blocking operation
        # In real hardware, this would take many cycles
        return training_id

    def trigger_repair(self, channel_id: int, lane_mask: int) -> bool:
        """Trigger lane repair for a channel

        Args:
            channel_id: Channel to repair
            lane_mask: Bit mask of lanes to remap

        Returns:
            True if repair successful
        """
        if channel_id not in self._channel_states:
            return False

        channel_state = self._channel_states[channel_id]
        channel_state.repair_state = lane_mask
        self.stats.repair_count += 1

        return True

    def get_stats(self) -> Dict:
        """Get comprehensive statistics

        Returns:
            Dictionary of all statistics
        """
        return {
            'controller': {
                'total_requests': self.stats.total_requests,
                'read_requests': self.stats.read_requests,
                'write_requests': self.stats.write_requests,
                'row_hit_rate': self.stats.row_hit_rate,
                'average_latency_ns': self.stats.average_latency_ns,
                'refresh_count': self.stats.refresh_count,
                'training_count': self.stats.training_count,
                'repair_count': self.stats.repair_count,
            },
            'spec': {
                'channels': self.spec.channels,
                'pseudo_channels': self.spec.pseudo_channels,
                'total_banks': self.spec.total_banks,
                'bandwidth_tbps': self.spec.bandwidth,
                'io_width': self.spec.io_width,
                'data_rate_gtps': self.spec.data_rate_gtps,
            },
            'queues': {
                'read_depth': len(self.queue_manager.read_queue),
                'write_depth': len(self.queue_manager.write_queue),
            },
            'qos': {
                'enabled': self._enable_qos,
                'priority_levels': 16,
            } if self.qos_scheduler else None,
            'refresh': {
                'enabled': self._enable_refresh,
                'mode': str(self.refresh_scheduler.mode) if self.refresh_scheduler else None,
            } if self.refresh_scheduler else None,
        }

    def get_bandwidth_gbs(self) -> float:
        """Calculate current effective bandwidth in GB/s

        Returns:
            Effective bandwidth in GB/s (capped at peak bandwidth)
        """
        if self.current_time_ns == 0:
            return 0.0

        # Bandwidth = bytes / time
        bytes_per_ns = self.stats.total_bandwidth_bytes / self.current_time_ns
        gbs = bytes_per_ns * 1000  # Convert to GB/s

        # Cap at peak bandwidth
        return min(gbs, self.spec.bandwidth_gbs)

    def get_effective_bandwidth_tbps(self) -> float:
        """Calculate effective bandwidth after overhead

        Returns:
            Effective bandwidth in TB/s
        """
        gbs = self.get_bandwidth_gbs()
        return gbs / 1000  # Convert to TB/s


@dataclass
class ChannelState:
    """State tracking for a single HBM4 channel"""
    channel_id: int
    queue_depth: int = 0
    repair_state: int = 0  # 0 = no repair needed
    last_refresh_cycle: int = 0
    training_state: str = "COMPLETE"  # IDLE, TRAINING, COMPLETE
    power_state: str = "ACTIVE"  # ACTIVE, SELF_REFRESH, POWER_DOWN

    def is_available(self) -> bool:
        """Check if channel is available for requests"""
        return (
            self.training_state == "COMPLETE" and
            self.power_state == "ACTIVE"
        )