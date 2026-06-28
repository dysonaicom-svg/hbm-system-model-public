"""
HBM4 Enhanced QoS Scheduler with 16 Priority Classes

Implements a comprehensive QoS scheduling system for HBM4 with:
- 16 QoS priority classes (0-15, higher = higher priority)
- Priority mapping for traffic types: CRITICAL(15), HIGH(12), NORMAL(8), LOW(4), IDLE(0)
- Weighted fair queuing with configurable bandwidth guarantees
- Anti-starvation mechanism (age-based priority boost)
- Bank conflict awareness for scheduling decisions
- Integration with HBM4AddressDecoder and PriorityQueue

Based on JEDEC JESD270-4A HBM4 specification and Synopsys DesignWare findings.
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, TYPE_CHECKING, Tuple
from collections import defaultdict, deque
import time
import math

from model.dram.hbm4_spec import HBM4Spec
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.bank_state_cache import BankStateCache

if TYPE_CHECKING:
    from model.controller.request import HBMRequest


class QoSLevel(IntEnum):
    """HBM4 QoS priority levels (0-15)

    Higher values = higher priority.
    Critical traffic (real-time AI inference) gets highest priority.
    """
    CRITICAL = 15    # Real-time/critical - latency-sensitive AI inference
    HIGH = 12        # High priority - time-sensitive workloads
    NORMAL = 8       # Normal traffic - general compute
    LOW = 4          # Background/batch - batch processing
    IDLE = 0         # Idle/probe - diagnostic traffic


class TrafficType(IntEnum):
    """HBM4 traffic classification types

    Maps application-level traffic types to QoS priorities.
    """
    REAL_TIME = 15      # AI inference, latency-critical
    CRITICAL = 15       # Critical data transfers
    HIGH_PRIORITY = 12  # Time-sensitive workloads
    NORMAL = 8          # General compute
    BACKGROUND = 4      # Batch processing
    PROBE = 0           # Diagnostic traffic
    IDLE = 0            # Idle/idle probing


# Traffic type to QoS level mapping
TRAFFIC_TYPE_TO_QOS = {
    TrafficType.REAL_TIME: QoSLevel.CRITICAL,
    TrafficType.CRITICAL: QoSLevel.CRITICAL,
    TrafficType.HIGH_PRIORITY: QoSLevel.HIGH,
    TrafficType.NORMAL: QoSLevel.NORMAL,
    TrafficType.BACKGROUND: QoSLevel.LOW,
    TrafficType.PROBE: QoSLevel.IDLE,
    TrafficType.IDLE: QoSLevel.IDLE,
}


@dataclass
class QoSClass:
    """Represents a QoS class with scheduling parameters

    Attributes:
        level: QoS level (0-15)
        weight: Relative weight for fair queuing (higher = more frequent scheduling)
        bw_guarantee: Minimum bandwidth guarantee (GB/s)
        bw_cap: Maximum bandwidth cap (GB/s)
        max_queue_depth: Maximum queue depth for this class
        latency_sla: Latency SLA in microseconds (-1 = no SLA)
        description: Human-readable description
    """
    level: int
    weight: float = 1.0
    bw_guarantee: float = 0.0
    bw_cap: float = float('inf')
    max_queue_depth: int = 32
    latency_sla: float = -1.0  # microseconds, -1 = no SLA
    description: str = ""

    def __post_init__(self):
        if not self.description:
            self.description = self._get_default_description()

    def _get_default_description(self) -> str:
        """Get default description based on level"""
        descriptions = {
            15: "Real-time/Critical - AI inference, latency-sensitive",
            12: "High priority - Time-sensitive workloads",
            8: "Normal - General compute",
            4: "Low/Background - Batch processing",
            0: "Idle/Probe - Diagnostic traffic",
        }
        return descriptions.get(self.level, f"Level {self.level}")

    @property
    def priority(self) -> int:
        """Alias for level to match HBMRequest interface"""
        return self.level


@dataclass
class QoSWeight:
    """Bandwidth weights configuration for QoS classes

    Manages the relative weights used in weighted fair queuing.
    """
    # Default weights matching Synopsys HBM4 Controller recommendations
    DEFAULT_WEIGHTS = {
        15: 4.0,   # CRITICAL: 4x weight
        12: 3.0,   # HIGH: 3x weight
        8: 2.0,    # NORMAL: 2x weight
        4: 1.0,    # LOW: 1x weight
        0: 0.5,    # IDLE: 0.5x weight
    }

    def __init__(self, weights: Optional[Dict[int, float]] = None):
        """Initialize with optional custom weights

        Args:
            weights: Optional dict mapping QoS level to weight
        """
        self._weights = weights.copy() if weights else self.DEFAULT_WEIGHTS.copy()
        # Ensure all 16 levels have weights
        for i in range(16):
            if i not in self._weights:
                self._weights[i] = 1.0

    def get_weight(self, qos_level: int) -> float:
        """Get weight for a QoS level

        Args:
            qos_level: QoS level (0-15)

        Returns:
            Weight value
        """
        return self._weights.get(qos_level, 1.0)

    def set_weight(self, qos_level: int, weight: float):
        """Set weight for a QoS level

        Args:
            qos_level: QoS level (0-15)
            weight: Weight value (higher = more scheduling opportunities)
        """
        self._weights[qos_level] = weight

    def get_normalized_weights(self) -> Dict[int, float]:
        """Get normalized weights that sum to 1.0

        Returns:
            Dict mapping QoS level to normalized weight
        """
        total = sum(self._weights.values())
        if total == 0:
            return {i: 1.0/16 for i in range(16)}
        return {k: v/total for k, v in self._weights.items()}

    def get_effective_weight(self, qos_level: int, queue_fill: float) -> float:
        """Calculate effective weight considering queue fill

        Args:
            qos_level: QoS level (0-15)
            queue_fill: Queue fill ratio (0.0-1.0)

        Returns:
            Effective weight (boosted when queue is nearly empty)
        """
        base_weight = self.get_weight(qos_level)
        # Boost weight when queue is nearly empty (anti-starvation)
        # Fill factor < 0.1 gets 2x boost, < 0.3 gets 1.5x boost
        if queue_fill < 0.1:
            return base_weight * 2.0
        elif queue_fill < 0.3:
            return base_weight * 1.5
        return base_weight


@dataclass
class QueuedRequest:
    """Request in QoS queue with tracking information

    Attributes:
        request_id: Unique request identifier
        addr: Memory address
        qos: QoS level (0-15)
        is_read: True for read, False for write
        arrival_time: Wall-clock arrival time
        row_hit: Whether this is a row hit request
        channel: Target channel (0-31)
        pseudo_channel: Target pseudo-channel (0-1)
        bank_group: Target bank group (0-7)
        bank: Target bank (0-15)
        row: Target row
        col: Target column
        length: Transaction length in bytes
        traffic_type: Traffic type for classification
        starvation_counter: Number of scheduling rounds skipped
        age_cycles: Age in scheduling cycles
    """
    request_id: int
    addr: int
    qos: int
    is_read: bool
    arrival_time: float
    row_hit: bool = False
    channel: int = 0
    pseudo_channel: int = 0
    bank_group: int = 0
    bank: int = 0
    row: int = 0
    col: int = 0
    length: int = 64
    traffic_type: TrafficType = TrafficType.NORMAL
    starvation_counter: int = 0
    age_cycles: int = 0

    def increment_age(self):
        """Increment age counter"""
        self.age_cycles += 1

    def reset_starvation(self):
        """Reset starvation counter after being scheduled"""
        self.starvation_counter = 0


class QoSMonitor:
    """Monitor for QoS scheduling metrics

    Tracks bandwidth usage, latency, and queue statistics per QoS level.
    """
    def __init__(self, window_ms: float = 1.0, max_samples: int = 1000):
        """Initialize QoS monitor

        Args:
            window_ms: Bandwidth measurement window in milliseconds
            max_samples: Maximum samples to retain per level
        """
        self.window_ms = window_ms
        self.max_samples = max_samples

        # Bandwidth tracking: {qos_level: deque of (timestamp, bytes)}
        self._bandwidth_data: Dict[int, deque] = defaultdict(lambda: deque(maxlen=max_samples))

        # Latency tracking: {qos_level: list of (submit_time, complete_time)}
        self._latency_data: Dict[int, List[Tuple[float, float]]] = defaultdict(list)

        # Queue depth history: {qos_level: deque of (timestamp, depth)}
        self._queue_depth_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=max_samples))

        # Scheduling counters
        self._scheduled_count: Dict[int, int] = defaultdict(int)
        self._rejected_count: Dict[int, int] = defaultdict(int)
        self._row_hit_count: Dict[int, int] = defaultdict(int)

        # Starvation tracking
        self._starvation_events: Dict[int, int] = defaultdict(int)

    def record_bandwidth(self, qos_level: int, bytes: int, timestamp: float):
        """Record bandwidth usage for a QoS level

        Args:
            qos_level: QoS level
            bytes: Number of bytes transferred
            timestamp: Current timestamp
        """
        self._bandwidth_data[qos_level].append((timestamp, bytes))
        self._cleanup_old_samples(qos_level, timestamp)

    def record_latency(self, qos_level: int, submit_time: float, complete_time: float):
        """Record request latency

        Args:
            qos_level: QoS level
            submit_time: When request was submitted
            complete_time: When request completed
        """
        self._latency_data[qos_level].append((submit_time, complete_time))
        # Keep only recent samples
        if len(self._latency_data[qos_level]) > self.max_samples:
            self._latency_data[qos_level] = self._latency_data[qos_level][-self.max_samples:]

    def record_queue_depth(self, qos_level: int, depth: int, timestamp: float):
        """Record queue depth snapshot

        Args:
            qos_level: QoS level
            depth: Current queue depth
            timestamp: Current timestamp
        """
        self._queue_depth_history[qos_level].append((timestamp, depth))

    def record_schedule(self, qos_level: int, row_hit: bool):
        """Record a scheduling event

        Args:
            qos_level: QoS level
            row_hit: Whether this was a row hit
        """
        self._scheduled_count[qos_level] += 1
        if row_hit:
            self._row_hit_count[qos_level] += 1

    def record_reject(self, qos_level: int):
        """Record a rejected request

        Args:
            qos_level: QoS level
        """
        self._rejected_count[qos_level] += 1

    def record_starvation(self, qos_level: int):
        """Record a starvation event

        Args:
            qos_level: QoS level
        """
        self._starvation_events[qos_level] += 1

    def _cleanup_old_samples(self, qos_level: int, timestamp: float):
        """Remove samples outside the window

        Args:
            qos_level: QoS level
            timestamp: Current timestamp
        """
        cutoff = timestamp - self.window_ms / 1000.0
        data = self._bandwidth_data[qos_level]
        while data and data[0][0] < cutoff:
            data.popleft()

    def get_bandwidth(self, qos_level: int) -> float:
        """Get current bandwidth for a QoS level

        Args:
            qos_level: QoS level

        Returns:
            Bandwidth in GB/s
        """
        data = self._bandwidth_data.get(qos_level, deque())
        if not data:
            return 0.0

        total_bytes = sum(b for _, b in data)
        total_time = self.window_ms / 1000.0
        return total_bytes / total_time / 1e9 if total_time > 0 else 0.0

    def get_average_latency(self, qos_level: int) -> float:
        """Get average latency for a QoS level

        Args:
            qos_level: QoS level

        Returns:
            Average latency in microseconds
        """
        data = self._latency_data.get(qos_level, [])
        if not data:
            return 0.0

        total_latency = sum(complete - submit for submit, complete in data)
        return total_latency / len(data) * 1e6  # Convert to microseconds

    def get_queue_depth_avg(self, qos_level: int) -> float:
        """Get average queue depth

        Args:
            qos_level: QoS level

        Returns:
            Average queue depth
        """
        data = self._queue_depth_history.get(qos_level, deque())
        if not data:
            return 0.0
        return sum(d for _, d in data) / len(data)

    def get_row_hit_rate(self, qos_level: int) -> float:
        """Get row hit rate for a QoS level

        Args:
            qos_level: QoS level

        Returns:
            Row hit rate (0.0-1.0)
        """
        total = self._scheduled_count.get(qos_level, 0)
        if total == 0:
            return 0.0
        return self._row_hit_count.get(qos_level, 0) / total

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics

        Returns:
            Dictionary with all metrics
        """
        stats = {
            'scheduled_total': sum(self._scheduled_count.values()),
            'rejected_total': sum(self._rejected_count.values()),
            'by_qos': {}
        }

        for level in range(16):
            stats['by_qos'][level] = {
                'scheduled': self._scheduled_count.get(level, 0),
                'rejected': self._rejected_count.get(level, 0),
                'bandwidth_gbs': self.get_bandwidth(level),
                'avg_latency_us': self.get_average_latency(level),
                'queue_depth_avg': self.get_queue_depth_avg(level),
                'row_hit_rate': self.get_row_hit_rate(level),
                'starvation_events': self._starvation_events.get(level, 0),
            }

        return stats


class BankConflictTracker:
    """Tracks bank state for conflict-aware scheduling

    Maintains per-bank state to enable FR-FCFS scheduling decisions.
    """
    def __init__(self, num_channels: int = 32, num_pseudo_channels: int = 2,
                 num_bank_groups: int = 8, num_banks: int = 16):
        """Initialize bank conflict tracker

        Args:
            num_channels: Number of channels (32 for HBM4)
            num_pseudo_channels: Pseudo-channels per channel (2)
            num_bank_groups: Bank groups per pseudo-channel (8)
            num_banks: Banks per bank group (16)
        """
        self.num_channels = num_channels
        self.num_pseudo_channels = num_pseudo_channels
        self.num_bank_groups = num_bank_groups
        self.num_banks = num_banks

        # Bank state: (channel, pch, bg, bank) -> {'open_row': int, 'last_cmd': str}
        self._bank_states: Dict[Tuple[int, int, int, int], Dict] = defaultdict(
            lambda: {'open_row': -1, 'last_cmd': None}
        )

        # Recent commands for timing
        self._recent_cmds: Dict[Tuple[int, int, int, int], float] = {}

    def get_bank_key(self, channel: int, pseudo_channel: int, bg: int, bank: int) -> Tuple:
        """Get bank key tuple"""
        return (channel, pseudo_channel, bg, bank)

    def is_row_open(self, channel: int, pseudo_channel: int, bg: int, bank: int) -> bool:
        """Check if a row is open in a bank

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bg: Bank group ID
            bank: Bank ID

        Returns:
            True if a row is open
        """
        key = self.get_bank_key(channel, pseudo_channel, bg, bank)
        return self._bank_states[key]['open_row'] >= 0

    def get_open_row(self, channel: int, pseudo_channel: int, bg: int, bank: int) -> int:
        """Get the currently open row

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bg: Bank group ID
            bank: Bank ID

        Returns:
            Open row ID, or -1 if none open
        """
        key = self.get_bank_key(channel, pseudo_channel, bg, bank)
        return self._bank_states[key]['open_row']

    def is_row_hit(self, channel: int, pseudo_channel: int, bg: int, bank: int, row: int) -> bool:
        """Check if access is a row hit

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bg: Bank group ID
            bank: Bank ID
            row: Row to access

        Returns:
            True if row is currently open
        """
        return self.is_row_open(channel, pseudo_channel, bg, bank) and \
               self.get_open_row(channel, pseudo_channel, bg, bank) == row

    def open_row(self, channel: int, pseudo_channel: int, bg: int, bank: int, row: int):
        """Open a row

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bg: Bank group ID
            bank: Bank ID
            row: Row to open
        """
        key = self.get_bank_key(channel, pseudo_channel, bg, bank)
        self._bank_states[key]['open_row'] = row
        self._bank_states[key]['last_cmd'] = 'ACTIVATE'

    def close_row(self, channel: int, pseudo_channel: int, bg: int, bank: int):
        """Close the open row

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bg: Bank group ID
            bank: Bank ID
        """
        key = self.get_bank_key(channel, pseudo_channel, bg, bank)
        self._bank_states[key]['open_row'] = -1
        self._bank_states[key]['last_cmd'] = 'PRECHARGE'

    def get_bank_state(self, channel: int, pseudo_channel: int, bg: int, bank: int) -> Dict:
        """Get full bank state

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bg: Bank group ID
            bank: Bank ID

        Returns:
            Dict with bank state info
        """
        key = self.get_bank_key(channel, pseudo_channel, bg, bank)
        return dict(self._bank_states[key])


class HBM4QoSScheduler:
    """Enhanced HBM4 QoS Scheduler with 16 Priority Classes

    Key features:
    - 16 priority levels (0-15, higher = higher priority)
    - Weighted fair queuing with configurable weights
    - Anti-starvation via age-based priority boost
    - Bank conflict awareness (FR-FCFS)
    - Per-QoS bandwidth guarantees and caps
    - Integration with HBM4AddressDecoder

    Reference: Synopsys DesignWare HBM4/4E Controller IP, JEDEC JESD270-4A

    Attributes:
        QOS_CRITICAL: Priority level for critical traffic (15)
        QOS_HIGH: Priority level for high priority traffic (12)
        QOS_NORMAL: Priority level for normal traffic (8)
        QOS_LOW: Priority level for low priority traffic (4)
        QOS_IDLE: Priority level for idle/probe traffic (0)
    """

    # Priority level constants
    QOS_CRITICAL = 15
    QOS_HIGH = 12
    QOS_NORMAL = 8
    QOS_LOW = 4
    QOS_IDLE = 0

    # Anti-starvation configuration
    DEFAULT_STARVATION_BOOST_THRESHOLD = 1000  # Cycles before boost kicks in
    DEFAULT_STARVATION_BOOST_FACTOR = 2.0  # Priority boost factor
    DEFAULT_MAX_STARVATION_CYCLES = 10000  # Maximum cycles before forced scheduling

    def __init__(self, config: Optional[HBM4Spec] = None):
        """Initialize HBM4 QoS scheduler

        Args:
            config: HBM4 specification (uses default if None)
        """
        self.config = config if config else HBM4Spec()
        self.priority_levels = 16

        # Address decoder for bank conflict tracking
        self._decoder = HBM4AddressDecoder(spec=self.config)

        # Bank conflict tracker
        self._bank_tracker = BankConflictTracker(
            num_channels=self.config.channels,
            num_pseudo_channels=self.config.pseudo_channels_per_channel,
            num_bank_groups=self.config.bank_groups_per_channel,
            num_banks=self.config.banks_per_pseudo_channel
        )

        # Bank state cache for efficient lookups
        self._bank_state_cache = BankStateCache(max_size=2048)

        # QoS class configuration
        self._qos_classes: Dict[int, QoSClass] = {}
        self._initialize_qos_classes()

        # Bandwidth weights
        self._weights = QoSWeight()

        # Bandwidth guarantees and caps per level
        self._bw_guarantee: Dict[int, float] = {}
        self._bw_cap: Dict[int, float] = {}
        self._initialize_bandwidth_config()

        # Request queues per priority level
        self._queues: Dict[int, List[QueuedRequest]] = defaultdict(list)

        # QoS monitor
        self._monitor = QoSMonitor()

        # Scheduling state
        self._current_time = 0.0
        self._scheduled_this_round: Dict[int, int] = defaultdict(int)
        self._total_scheduled = 0
        self._scheduling_round = 0

        # Anti-starvation state
        self._starvation_threshold = self.DEFAULT_STARVATION_BOOST_THRESHOLD
        self._starvation_boost_factor = self.DEFAULT_STARVATION_BOOST_FACTOR
        self._max_starvation_cycles = self.DEFAULT_MAX_STARVATION_CYCLES
        self._last_scheduled: Dict[int, float] = defaultdict(float)

        # Statistics
        self._stats = {
            'total_scheduled': 0,
            'total_rejected': 0,
            'by_qos': defaultdict(int),
            'starvation_boosts': defaultdict(int),
            'bank_conflict_skips': 0,
        }

        # Legacy compatibility - maintain old interface
        self.bw_guarantee = self._bw_guarantee
        self.bw_cap = self._bw_cap
        self.bw_window_ms = 1.0
        self.bandwidth_tracked: Dict[int, List[tuple]] = defaultdict(list)
        self.queues = self._queues
        self.stats = {
            'total_scheduled': 0,
            'by_qos': defaultdict(int)
        }

    def _initialize_qos_classes(self):
        """Initialize default QoS classes for all 16 levels"""
        # Default class configs based on Synopsys recommendations
        class_configs = [
            # level, weight, bw_guarantee, bw_cap, latency_sla
            (15, 4.0, 200.0, 1000.0, 10.0),    # CRITICAL: 10us SLA
            (14, 4.0, 180.0, 950.0, 15.0),
            (13, 3.5, 160.0, 900.0, 20.0),
            (12, 3.0, 140.0, 850.0, 25.0),     # HIGH
            (11, 3.0, 120.0, 800.0, 30.0),
            (10, 2.5, 100.0, 700.0, 40.0),
            (9, 2.5, 80.0, 600.0, 50.0),
            (8, 2.0, 60.0, 500.0, 100.0),      # NORMAL
            (7, 2.0, 50.0, 400.0, 150.0),
            (6, 1.5, 40.0, 300.0, 200.0),
            (5, 1.5, 30.0, 250.0, 300.0),
            (4, 1.0, 20.0, 200.0, 500.0),      # LOW
            (3, 1.0, 15.0, 150.0, 750.0),
            (2, 0.75, 10.0, 100.0, 1000.0),
            (1, 0.5, 5.0, 50.0, 2000.0),
            (0, 0.5, 0.0, 25.0, -1.0),         # IDLE: no SLA
        ]

        for level, weight, bw_g, bw_c, sla in class_configs:
            self._qos_classes[level] = QoSClass(
                level=level,
                weight=weight,
                bw_guarantee=bw_g,
                bw_cap=bw_c,
                latency_sla=sla,
                description=self._get_level_description(level)
            )

    def _get_level_description(self, level: int) -> str:
        """Get description for a QoS level"""
        descriptions = {
            15: "Real-time/Critical",
            12: "High Priority",
            8: "Normal",
            4: "Low/Background",
            0: "Idle/Probe",
        }
        if level in descriptions:
            return descriptions[level]
        if level >= 12:
            return f"High Priority ({level})"
        if level >= 8:
            return f"Normal ({level})"
        if level >= 4:
            return f"Low Priority ({level})"
        return f"Idle ({level})"

    def _initialize_bandwidth_config(self):
        """Initialize default bandwidth configuration"""
        for level in range(16):
            cls = self._qos_classes.get(level)
            if cls:
                self._bw_guarantee[level] = cls.bw_guarantee
                self._bw_cap[level] = cls.bw_cap
            else:
                self._bw_guarantee[level] = 0.0
                self._bw_cap[level] = 100.0

    def classify_request(self, request: 'HBMRequest') -> int:
        """Classify a request into a QoS level

        Uses the request's QoS field if valid, otherwise infers from traffic type.

        Args:
            request: HBM request to classify

        Returns:
            QoS level (0-15)
        """
        # If request already has valid QoS, use it
        if 0 <= request.qos < 16:
            return request.qos

        # Infer from traffic type if available
        traffic_type = getattr(request, 'traffic_type', None)
        if traffic_type is not None:
            return TRAFFIC_TYPE_TO_QOS.get(traffic_type, self.QOS_NORMAL)

        # Default to NORMAL
        return self.QOS_NORMAL

    def submit_request(self, request_id: int, addr: int = 0,
                      qos: int = 8, is_read: bool = True,
                      channel: int = 0, pseudo_channel: int = 0,
                      bank_group: int = 0, bank: int = 0, row: int = 0, col: int = 0,
                      row_hit: bool = False, length: int = 64,
                      traffic_type: TrafficType = TrafficType.NORMAL) -> bool:
        """Submit a request to the QoS scheduler

        Args:
            request_id: Unique request identifier
            addr: Address
            qos: QoS level (0-15)
            is_read: True for read, False for write
            channel: Target channel (0-31)
            pseudo_channel: Target pseudo-channel (0-1)
            bank_group: Target bank group (0-7)
            bank: Target bank (0-15)
            row: Target row
            col: Target column
            row_hit: Whether this is a row hit
            length: Transaction length in bytes
            traffic_type: Traffic type for classification

        Returns:
            True if request was queued
        """
        if qos < 0 or qos >= self.priority_levels:
            return False

        # Check queue depth limit
        if len(self._queues[qos]) >= self._get_max_queue_depth(qos):
            self._monitor.record_reject(qos)
            self._stats['total_rejected'] += 1
            return False

        req = QueuedRequest(
            request_id=request_id,
            addr=addr,
            qos=qos,
            is_read=is_read,
            arrival_time=time.time(),
            row_hit=row_hit,
            channel=channel,
            pseudo_channel=pseudo_channel,
            bank_group=bank_group,
            bank=bank,
            row=row,
            col=col,
            length=length,
            traffic_type=traffic_type
        )

        self._queues[qos].append(req)
        return True

    def submit_hbm_request(self, request: 'HBMRequest') -> bool:
        """Submit an HBMRequest object to the scheduler

        Args:
            request: HBMRequest to submit

        Returns:
            True if request was queued
        """
        # Decode address for bank/row info if not already set
        if request.row_id == 0 and request.addr > 0:
            decoded = self._decoder.decode(request.addr)
            request.row_id = decoded.row_id
            request.bank_id = decoded.bank_id
            request.bank_group_id = decoded.bank_group_id
            request.channel_id = decoded.channel_id
            request.pseudo_channel_id = decoded.pseudo_channel_id

        qos = self.classify_request(request)
        row_hit = getattr(request, 'row_hit', False)

        return self.submit_request(
            request_id=request.request_id,
            addr=request.addr,
            qos=qos,
            is_read=request.is_read,
            channel=request.channel_id,
            pseudo_channel=request.pseudo_channel_id,
            bank_group=request.bank_group_id,
            bank=request.bank_id,
            row=request.row_id,
            col=request.col_id,
            row_hit=row_hit,
            length=request.length,
            traffic_type=getattr(request, 'traffic_type', TrafficType.NORMAL)
        )

    def _get_max_queue_depth(self, qos_level: int) -> int:
        """Get maximum queue depth for a QoS level

        Args:
            qos_level: QoS level

        Returns:
            Maximum queue depth
        """
        cls = self._qos_classes.get(qos_level)
        if cls:
            return cls.max_queue_depth
        return 32

    def _get_current_bandwidth(self, qos_level: int) -> float:
        """Calculate current bandwidth for a QoS level

        Args:
            qos_level: QoS level to check

        Returns:
            Current bandwidth in GB/s
        """
        return self._monitor.get_bandwidth(qos_level)

    def _can_schedule(self, qos_level: int) -> bool:
        """Check if a QoS level can be scheduled (bandwidth check)

        Args:
            qos_level: QoS level to check

        Returns:
            True if this level can be scheduled
        """
        current_bw = self._get_current_bandwidth(qos_level)

        # Below guarantee: can always schedule
        if current_bw < self._bw_guarantee.get(qos_level, 0):
            return True

        # Above cap: cannot schedule
        if current_bw >= self._bw_cap.get(qos_level, float('inf')):
            return False

        return True

    def _get_starvation_boost(self, qos_level: int) -> int:
        """Calculate priority boost due to starvation

        Args:
            qos_level: QoS level to check

        Returns:
            Priority boost (0 if not starving)
        """
        candidates = self._queues.get(qos_level, [])
        if not candidates:
            return 0

        # Check if any request in this level is starving
        now = time.time()
        for req in candidates:
            age = now - req.arrival_time
            age_cycles = int(age * 1000)  # Rough conversion to cycles

            if age_cycles > self._max_starvation_cycles:
                # Force schedule
                self._stats['starvation_boosts'][qos_level] += 1
                self._monitor.record_starvation(qos_level)
                return 15  # Maximum boost

            if age_cycles > self._starvation_threshold:
                # Progressive boost
                boost = int((age_cycles - self._starvation_threshold) /
                           (self._starvation_threshold * self._starvation_boost_factor))
                if boost > 0:
                    self._stats['starvation_boosts'][qos_level] += 1
                    return min(boost, 14)

        return 0

    def boost_starving(self) -> None:
        """Boost priority of starving requests

        This method implements the anti-starvation mechanism by:
        1. Finding requests that haven't been scheduled for too long
        2. Temporarily boosting their effective priority
        3. Recording starvation events for monitoring
        """
        now = time.time()

        for qos_level in range(16):
            candidates = self._queues.get(qos_level, [])
            for req in candidates:
                age = now - req.arrival_time
                req.age_cycles = int(age * 1000)

                # Track starvation
                if req.age_cycles > self._starvation_threshold:
                    req.starvation_counter += 1
                    if req.starvation_counter > 10:  # Significant starvation
                        self._monitor.record_starvation(qos_level)

    def schedule(self) -> Optional[QueuedRequest]:
        """Schedule the next request using QoS + Weighted Fair Queuing

        Priority order:
        1. Check bandwidth guarantees (below guarantee = immediate scheduling)
        2. Check starvation (old requests get boosted priority)
        3. Highest effective priority (base + boost) that can be scheduled
        4. FR-FCFS within same priority (row hits first, then oldest)

        Returns:
            Next request to schedule, or None if queue empty
        """
        self._scheduling_round += 1
        self._scheduled_this_round.clear()

        # Update ages and check starvation
        self.boost_starving()

        # Check QoS levels from high to low
        for effective_level in range(15, -1, -1):
            # Get base QoS level for this effective level
            base_level = effective_level % 16

            # Skip if queue empty
            if not self._queues[base_level]:
                continue

            # Apply starvation boost
            starvation_boost = self._get_starvation_boost(base_level)
            actual_level = base_level + starvation_boost

            # Check if this effective level matches
            if actual_level != effective_level:
                continue

            # Check bandwidth constraints
            if not self._can_schedule(base_level):
                continue

            # FR-FCFS selection within same priority
            best = self._fr_fcfs_select(self._queues[base_level])
            if best:
                self._queues[base_level].remove(best)
                self._stats['total_scheduled'] += 1
                self._stats['by_qos'][base_level] += 1
                self._total_scheduled += 1
                self._last_scheduled[base_level] = time.time()

                # Track bandwidth
                now = time.time()
                self._monitor.record_bandwidth(base_level, best.length, now)
                self._monitor.record_schedule(base_level, best.row_hit)

                # Update bank state
                self._bank_tracker.open_row(
                    best.channel, best.pseudo_channel,
                    best.bank_group, best.bank, best.row
                )

                return best

        return None

    def schedule_weighted(self) -> Optional[QueuedRequest]:
        """Schedule using weighted fair queuing algorithm

        This method implements strict weighted fair queuing where:
        1. Requests are selected based on their weight relative to others
        2. Higher weight QoS levels get proportionally more scheduling opportunities
        3. FR-FCFS still applies within the same weight class

        Returns:
            Next request to schedule, or None if queue empty
        """
        self._scheduling_round += 1

        # Collect all non-empty queues with their weights
        active_levels = []
        for qos_level in range(16):
            if self._queues[qos_level]:
                queue_fill = len(self._queues[qos_level]) / self._get_max_queue_depth(qos_level)
                weight = self._weights.get_effective_weight(qos_level, queue_fill)
                active_levels.append((qos_level, weight, len(self._queues[qos_level])))

        if not active_levels:
            return None

        # Sort by effective priority (weight * queue_depth factor)
        # This ensures fair distribution while respecting weights
        def effective_priority(item):
            qos, weight, depth = item
            # starvation boost
            starvation = self._get_starvation_boost(qos)
            # Queue depth factor (prefer non-empty, but not overwhelming)
            depth_factor = min(depth / self._get_max_queue_depth(qos), 1.0)
            return (qos + starvation) * weight * (1.0 + depth_factor)

        active_levels.sort(key=effective_priority, reverse=True)

        # Try to schedule from highest effective priority level
        for qos_level, weight, depth in active_levels:
            if not self._can_schedule(qos_level):
                continue

            # FR-FCFS selection
            candidates = self._queues[qos_level]
            best = self._fr_fcfs_select(candidates)
            if best:
                self._queues[qos_level].remove(best)
                self._stats['total_scheduled'] += 1
                self._stats['by_qos'][qos_level] += 1
                self._total_scheduled += 1
                self._last_scheduled[qos_level] = time.time()

                # Track metrics
                now = time.time()
                self._monitor.record_bandwidth(qos_level, best.length, now)
                self._monitor.record_schedule(qos_level, best.row_hit)

                # Update bank state
                self._bank_tracker.open_row(
                    best.channel, best.pseudo_channel,
                    best.bank_group, best.bank, best.row
                )

                return best

        return None

    def _fr_fcfs_select(self, candidates: List[QueuedRequest]) -> Optional[QueuedRequest]:
        """First-Ready FCFS selection

        Priority:
        1. Row hit requests (first)
        2. Oldest request (FCFS)

        Args:
            candidates: List of candidate requests

        Returns:
            Best request to schedule, or None
        """
        if not candidates:
            return None

        # Priority 1: Row hit requests
        row_hits = [r for r in candidates if r.row_hit]
        if row_hits:
            return min(row_hits, key=lambda r: r.arrival_time)

        # Priority 2: All requests, oldest first
        return min(candidates, key=lambda r: r.arrival_time)

    def select_next(self, requests: List['HBMRequest']) -> Optional['HBMRequest']:
        """Select next request from a list using QoS priority + FR-FCFS

        This method accepts a list of HBMRequest objects and selects
        the highest priority one based on QoS level and row hit status.

        Args:
            requests: List of HBMRequest objects to select from

        Returns:
            Selected request or None if list is empty
        """
        if not requests:
            return None

        # Group requests by QoS level
        by_qos: Dict[int, List] = defaultdict(list)
        for req in requests:
            qos = self.classify_request(req)
            by_qos[qos].append(req)

        # Select from highest QoS level that has requests
        for qos_level in range(self.priority_levels - 1, -1, -1):
            if qos_level not in by_qos or not by_qos[qos_level]:
                continue

            candidates = by_qos[qos_level]

            # FR-FCFS: row hits first, then oldest
            row_hits = [r for r in candidates if getattr(r, 'row_hit', False)]
            if row_hits:
                return min(row_hits, key=lambda r: getattr(r, 'arrival_time', 0))

            # No row hits, select oldest
            return min(candidates, key=lambda r: getattr(r, 'arrival_time', 0))

        return None

    def get_queue_size(self, qos_level: int) -> int:
        """Get number of requests in a specific queue

        Args:
            qos_level: QoS level to query

        Returns:
            Number of queued requests
        """
        return len(self._queues[qos_level])

    def get_total_queue_size(self) -> int:
        """Get total number of queued requests across all priorities

        Returns:
            Total queued requests
        """
        return sum(len(q) for q in self._queues.values())

    def clear_queue(self, qos_level: int):
        """Clear all requests in a specific queue

        Args:
            qos_level: QoS level to clear
        """
        self._queues[qos_level].clear()

    def clear_all_queues(self):
        """Clear all queues"""
        self._queues.clear()

    def set_bandwidth_guarantee(self, qos_level: int, guarantee_gbs: float):
        """Set bandwidth guarantee for a QoS level

        Args:
            qos_level: QoS level
            guarantee_gbs: Bandwidth guarantee in GB/s
        """
        self._bw_guarantee[qos_level] = guarantee_gbs
        if qos_level in self._qos_classes:
            self._qos_classes[qos_level].bw_guarantee = guarantee_gbs

    def set_bandwidth_cap(self, qos_level: int, cap_gbs: float):
        """Set bandwidth cap for a QoS level

        Args:
            qos_level: QoS level
            cap_gbs: Bandwidth cap in GB/s
        """
        self._bw_cap[qos_level] = cap_gbs
        if qos_level in self._qos_classes:
            self._qos_classes[qos_level].bw_cap = cap_gbs

    def set_weight(self, qos_level: int, weight: float):
        """Set scheduling weight for a QoS level

        Args:
            qos_level: QoS level
            weight: Weight value (higher = more scheduling opportunities)
        """
        self._weights.set_weight(qos_level, weight)
        if qos_level in self._qos_classes:
            self._qos_classes[qos_level].weight = weight

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'total_scheduled': self._stats['total_scheduled'],
            'total_rejected': self._stats['total_rejected'],
            'by_qos': dict(self._stats['by_qos']),
            'starvation_boosts': dict(self._stats['starvation_boosts']),
            'bank_conflict_skips': self._stats['bank_conflict_skips'],
            'total_queued': self.get_total_queue_size(),
            'queues_by_level': {
                qos: len(reqs) for qos, reqs in self._queues.items()
            },
            'monitor': self._monitor.get_stats(),
        }

    def get_qos_class(self, qos_level: int) -> Optional[QoSClass]:
        """Get QoS class configuration

        Args:
            qos_level: QoS level (0-15)

        Returns:
            QoSClass or None
        """
        return self._qos_classes.get(qos_level)

    def get_all_qos_classes(self) -> Dict[int, QoSClass]:
        """Get all QoS class configurations

        Returns:
            Dict mapping level to QoSClass
        """
        return dict(self._qos_classes)

    def get_bank_state(self, channel: int, pseudo_channel: int,
                     bg: int, bank: int) -> Dict:
        """Get bank state for conflict-aware scheduling

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bg: Bank group ID
            bank: Bank ID

        Returns:
            Dict with bank state info
        """
        return self._bank_tracker.get_bank_state(channel, pseudo_channel, bg, bank)

    def is_bank_conflict(self, channel: int, pseudo_channel: int,
                        bg: int, bank: int, row: int) -> bool:
        """Check if access would cause a bank conflict

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bg: Bank group ID
            bank: Bank ID
            row: Target row

        Returns:
            True if bank is open but to a different row
        """
        if self._bank_tracker.is_row_open(channel, pseudo_channel, bg, bank):
            open_row = self._bank_tracker.get_open_row(channel, pseudo_channel, bg, bank)
            return open_row != row
        return False

    def check_bank_available(self, channel: int, bank: int, cycle: int) -> bool:
        """Check if bank is available using cache.

        Uses BankStateCache for faster lookups when same bank is queried repeatedly.

        Args:
            channel: Channel ID
            bank: Bank ID
            cycle: Current simulation cycle

        Returns:
            True if bank is available (IDLE)
        """
        # Pseudo-channel defaults to 0 for simple lookups
        cached = self._bank_state_cache.get(channel, 0, bank)
        if cached:
            return cached[0] == "IDLE"

        # Cache miss - query tracker and update cache
        state_dict = self._bank_tracker.get_bank_state(channel, 0, 0, bank)
        is_idle = state_dict.get('open_row', -1) < 0  # IDLE if no row open
        state = "IDLE" if is_idle else "ACTIVE"
        self._bank_state_cache.set(channel, 0, bank, state, cycle)
        return is_idle

    def invalidate_bank_cache(self, channel: int, bank: int):
        """Invalidate cache entry for a bank after state change.

        Args:
            channel: Channel ID
            bank: Bank ID
        """
        self._bank_state_cache.invalidate(channel, 0, bank)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get bank state cache statistics.

        Returns:
            Dict with cache hits, misses, hit_rate, size
        """
        return self._bank_state_cache.get_stats()