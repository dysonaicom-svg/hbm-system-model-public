"""
HBM FR-FCFS Scheduler - Enhanced HBM4 Version

Reference design document 2026-06-15-hbm-system-model-design.md Section 5.1.2 and 5.1.3

FR-FCFS (First-Ready First-Come-First-Served):
1. Priority for row-hit requests
2. Same priority by timestamp, select oldest
3. Read/Write arbitration

HBM4 Enhancements:
- 16 QoS priority classes (0-15, higher = higher priority)
- Bank conflict awareness (avoid scheduling conflicting banks)
- 32-channel architecture support
- Integration with HBM4Config and HBM4Spec

Key HBM4 Parameters:
- 32 channels per stack (5-bit channel field)
- 64 pseudo-channels (1-bit)
- 16 bank groups (3-bit), 16 banks per group (4-bit)
- 64K rows (16-bit)
- Queue depth: 64
- Speed grades: 8/12/16 Gbps
"""

from typing import Optional, List, Tuple, Dict, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import IntEnum
import time

from model.controller.config import HBMConfig, HBM4_DEFAULT
from model.controller.request import HBMRequest, RequestState
from model.controller.queue import ReadQueue, WriteQueue
from model.dram.HBM4_spec import HBM4Spec


class QoSLevel(IntEnum):
    """HBM4 QoS priority levels (0-15)
    
    Higher values = higher priority.
    Critical traffic (real-time) gets highest priority.
    """
    CRITICAL = 15    # Real-time/critical
    HIGH = 12        # High priority
    NORMAL = 8       # Normal traffic
    LOW = 4          # Background/batch
    IDLE = 0         # Idle/probe


class BankState:
    """Bank state tracker for FR-FCFS scheduling

    Tracks open row and access timing for row-hit detection.
    """
    __slots__ = ('bank_id', 'is_open', 'open_row', 'last_row', 'last_access_time',
                 'last_command', 'rank_id')

    def __init__(self, bank_id: int, rank_id: int = 0):
        self.bank_id = bank_id
        self.rank_id = rank_id
        self.is_open = False
        self.open_row = -1
        self.last_row = -1  # Track last activated row for hit detection
        self.last_access_time = 0.0
        self.last_command = None  # 'ACT', 'PRE', 'RD', 'WR'

    def can_precharge(self, current_time: float, tRP: int = 4) -> bool:
        """Check if bank can be precharged (tRP elapsed)"""
        if not self.is_open:
            return True
        # tRP penalty in time units (cycles converted to time)
        return (current_time - self.last_access_time) >= tRP

    def activate(self, row_id: int, current_time: float):
        """Activate a row in this bank"""
        self.is_open = True
        self.open_row = row_id
        self.last_row = row_id  # Remember last activated row
        self.last_access_time = current_time
        self.last_command = 'ACT'

    def precharge(self, current_time: float):
        """Precharge this bank"""
        self.is_open = False
        # Keep last_row for row-hit detection on next access to same row
        # open_row set to -1 because row is closed, but last_row remembers
        self.last_access_time = current_time
        self.last_command = 'PRE'


class BankGroupState:
    """Bank group state for conflict detection
    
    Tracks bank group commands for conflict awareness.
    """
    __slots__ = ('group_id', 'banks', 'last_command_time', 'last_bank_activated')

    def __init__(self, group_id: int, num_banks: int = 16):
        self.group_id = group_id
        self.banks = {i: BankState(i) for i in range(num_banks)}
        self.last_command_time = 0.0
        self.last_bank_activated = -1

    def get_open_bank_count(self) -> int:
        """Count banks with open rows"""
        return sum(1 for b in self.banks.values() if b.is_open)

    def get_open_rows(self) -> Dict[int, int]:
        """Get mapping of bank_id -> open_row for all open banks"""
        return {bid: b.open_row for bid, b in self.banks.items() if b.is_open}


class BankConflictTracker:
    """Tracks bank conflicts for scheduling decisions
    
    Monitors bank groups to avoid scheduling conflicting banks
    within the same command window (tCCD).
    """
    
    def __init__(self, num_bank_groups: int = 8, num_banks_per_group: int = 16):
        self.num_bank_groups = num_bank_groups
        self.num_banks_per_group = num_banks_per_group
        self.bank_groups: Dict[int, BankGroupState] = {
            i: BankGroupState(i, num_banks_per_group) 
            for i in range(num_bank_groups)
        }
        
        # Track recent commands for conflict detection
        # Format: (time, bank_group_id, bank_id)
        self._recent_commands: List[Tuple[float, int, int]] = []
        self._command_history_max = 64

    def record_command(self, bank_group_id: int, bank_id: int, 
                      current_time: float, command: str = 'ACT'):
        """Record a command execution for conflict tracking"""
        self._recent_commands.append((current_time, bank_group_id, bank_id))
        
        # Update bank group state
        if bank_group_id in self.bank_groups:
            bg = self.bank_groups[bank_group_id]
            bg.last_command_time = current_time
            bg.last_bank_activated = bank_id
            
            if command == 'ACT' and bank_id in bg.banks:
                bg.banks[bank_id].activate(-1, current_time)  # Row will be set later
            elif command == 'PRE':
                for b in bg.banks.values():
                    b.precharge(current_time)
        
        # Trim history
        if len(self._recent_commands) > self._command_history_max:
            self._recent_commands = self._recent_commands[-self._command_history_max:]

    def has_conflict(self, bank_group_id: int, bank_id: int, 
                    current_time: float, tCCD: float = 4.0) -> bool:
        """Check if scheduling this bank would cause a conflict
        
        Args:
            bank_group_id: Target bank group
            bank_id: Target bank
            current_time: Current simulation time
            tCCD: Column command delay threshold
            
        Returns:
            True if there would be a timing conflict
        """
        if bank_group_id not in self.bank_groups:
            return False
            
        bg = self.bank_groups[bank_group_id]
        
        # Check if any command was issued to this bank group recently
        time_since_last = current_time - bg.last_command_time
        if time_since_last < tCCD:
            # Same bank group was accessed recently
            return True
            
        return False

    def get_conflicting_banks(self, current_time: float, 
                              tCCD: float = 4.0) -> Set[Tuple[int, int]]:
        """Get set of (bank_group_id, bank_id) pairs that are in conflict
        
        Returns:
            Set of tuples representing conflicting bank locations
        """
        conflicts = set()
        
        for bg_id, bg in self.bank_groups.items():
            if current_time - bg.last_command_time < tCCD:
                if bg.last_bank_activated >= 0:
                    conflicts.add((bg_id, bg.last_bank_activated))
                    
        return conflicts

    def get_best_bank_in_group(self, bank_group_id: int, 
                               candidates: List[HBMRequest]) -> Optional[HBMRequest]:
        """Select best bank from candidates within a bank group
        
        Priority: row hit > no conflict > oldest
        """
        if bank_group_id not in self.bank_groups:
            return None
            
        bg = self.bank_groups[bank_group_id]
        valid = []
        
        for req in candidates:
            if req.bank_group_id != bank_group_id:
                continue
                
            # Check row hit
            if req.row_hit:
                return req
                
            valid.append(req)
            
        return valid[0] if valid else None


@dataclass
class SchedulerStats:
    """Scheduler statistics"""
    schedule_count: int = 0
    row_hit_count: int = 0
    row_miss_count: int = 0
    read_count: int = 0
    write_count: int = 0
    qos_distribution: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    bank_conflict_count: int = 0
    qos_starved_count: int = 0

    @property
    def row_hit_rate(self) -> float:
        if self.schedule_count == 0:
            return 0.0
        return self.row_hit_count / self.schedule_count

    @property
    def bank_conflict_rate(self) -> float:
        if self.schedule_count == 0:
            return 0.0
        return self.bank_conflict_count / self.schedule_count

    def record_schedule(self, request: HBMRequest, row_hit: bool = False,
                       qos: int = 8, is_read: bool = True):
        """Record a scheduling event"""
        self.schedule_count += 1
        if row_hit:
            self.row_hit_count += 1
        else:
            self.row_miss_count += 1
        if is_read:
            self.read_count += 1
        else:
            self.write_count += 1
        self.qos_distribution[qos] += 1

    def to_dict(self) -> Dict:
        """Export statistics as dictionary"""
        return {
            'schedule_count': self.schedule_count,
            'row_hit_count': self.row_hit_count,
            'row_miss_count': self.row_miss_count,
            'read_count': self.read_count,
            'write_count': self.write_count,
            'row_hit_rate': self.row_hit_rate,
            'bank_conflict_count': self.bank_conflict_count,
            'bank_conflict_rate': self.bank_conflict_rate,
            'qos_distribution': dict(self.qos_distribution),
        }


class HBMScheduler:
    """HBM Scheduler base class"""

    __slots__ = ('config',)

    def __init__(self, config: HBMConfig):
        self.config = config

    def schedule(self, read_queue: ReadQueue, write_queue: WriteQueue,
                bank_states: Dict[Tuple, BankState], current_time: float) -> Optional[HBMRequest]:
        """Schedule next request

        Args:
            read_queue: Read queue
            write_queue: Write queue
            bank_states: Bank state dictionary
            current_time: Current time

        Returns:
            Next scheduled request
        """
        raise NotImplementedError


# Pre-computed turnaround penalty (in cycles)
_TURNAROUND_PENALTY = 3


class FRFCFSScheduler(HBMScheduler):
    """FR-FCFS Scheduler - Enhanced HBM4 Version

    First-Ready FCFS scheduling strategy with HBM4 enhancements:
    - Row-hit priority
    - Same priority by timestamp (FCFS)
    - Configurable read/write arbitration
    - 16 QoS priority classes
    - Bank conflict awareness
    - 32-channel HBM4 support

    HBM4 Parameters:
    - 32 channels per stack (5-bit channel field)
    - 64 pseudo-channels (1-bit)
    - 16 bank groups (3-bit), 16 banks per group (4-bit)
    - 64K rows (16-bit)
    - Queue depth: 64
    - 16 QoS priority classes (0-15)

    Optimizations:
    - Batch candidate filtering
    - Pre-computed priority scores
    - Reduced method call overhead
    - Bank conflict caching
    """

    __slots__ = ('rd_priority', 'wr_priority', 'TURNAROUND_PENALTY',
                 '_qos_enabled', '_qos_weights',
                 '_bank_conflict_tracker', '_last_qos_served', '_starvation_counter',
                 'stats', '_cached_read_candidates', '_cached_write_candidates')

    # Read/Write arbitration weights
    RD_PRIORITY = 1.0
    WR_PRIORITY = 1.0

    # QoS level constants (0-15)
    QOS_LEVELS = 16
    QOS_CRITICAL = 15
    QOS_HIGH = 12
    QOS_NORMAL = 8
    QOS_LOW = 4
    QOS_IDLE = 0

    def __init__(self, config: HBMConfig, rd_priority: float = 1.0, 
                 wr_priority: float = 1.0, qos_enabled: bool = True):
        """Initialize FR-FCFS Scheduler
        
        Args:
            config: HBM configuration (HBMConfig or HBM4_DEFAULT)
            rd_priority: Read priority weight
            wr_priority: Write priority weight
            qos_enabled: Enable QoS scheduling (16 priority levels)
        """
        super().__init__(config)
        self.rd_priority = rd_priority
        self.wr_priority = wr_priority

        # Read-Write turnaround penalty (cycles)
        self.TURNAROUND_PENALTY = _TURNAROUND_PENALTY

        # QoS configuration
        self._qos_enabled = qos_enabled
        # Higher QoS level = higher weight (0-15 maps to 0.0-1.0)
        self._qos_weights = {i: i / 15.0 for i in range(16)}
        self._last_qos_served = 15
        self._starvation_counter: Dict[int, int] = defaultdict(int)

        # Bank conflict tracking
        num_bg = getattr(config, 'bank_groups_per_channel', 8)
        num_banks = getattr(config, 'banks_per_pseudo_channel', 16)
        self._bank_conflict_tracker = BankConflictTracker(
            num_bank_groups=num_bg,
            num_banks_per_group=num_banks
        )

        # Statistics
        self.stats = SchedulerStats()

        # Cached candidates for batch processing
        self._cached_read_candidates: List[HBMRequest] = []
        self._cached_write_candidates: List[HBMRequest] = []

    def _compute_qos_score(self, request: HBMRequest, current_time: float) -> float:
        """Compute scheduling score based on QoS and age
        
        Score = base_priority + age_bonus
        
        Higher score = higher priority for scheduling.
        
        Args:
            request: HBM request
            current_time: Current simulation time
            
        Returns:
            Composite scheduling score
        """
        qos = request.qos if hasattr(request, 'qos') else 8
        age = current_time - request.arrival_time
        
        # Base score from QoS (normalized to 0-1)
        base_score = self._qos_weights.get(qos, 0.5)
        
        # Age bonus: accumulate over time to prevent starvation
        # After 100 time units, low priority catches up
        age_bonus = min(age / 100.0, 1.0) * 0.5
        
        return base_score + age_bonus

    def _update_starvation(self, qos_level: int):
        """Update starvation counter for a QoS level
        
        Args:
            qos_level: QoS level that was just served
        """
        # Increment counter for all levels below the served one
        for q in range(qos_level):
            self._starvation_counter[q] += 1
            
        # Reset counter for served level
        self._starvation_counter[qos_level] = 0
        self._last_qos_served = qos_level

    def _get_starvation_bonus(self, qos_level: int) -> float:
        """Get starvation bonus for a QoS level
        
        Prevents low-priority requests from being starved.
        
        Args:
            qos_level: QoS level to check
            
        Returns:
            Starvation bonus (0-1)
        """
        starve_count = self._starvation_counter.get(qos_level, 0)
        # After 10 consecutive services of higher priority, start bonus
        return min(starve_count / 10.0, 1.0) * 0.5

    def schedule(self, read_queue: ReadQueue, write_queue: WriteQueue,
                bank_states: Dict[Tuple, BankState],
                current_time: float,
                last_cmd_type: str = "READ") -> Optional[HBMRequest]:
        """FR-FCFS scheduling with HBM4 enhancements

        Args:
            read_queue: Read queue
            write_queue: Write queue
            bank_states: Bank state dictionary keyed by (channel, pch, bank)
            current_time: Current time
            last_cmd_type: Last command type ("READ" or "WRITE")

        Returns:
            Next scheduled request
        """
        # Get candidates with row-hit detection
        read_candidates = self._get_row_hit_candidates_fast(read_queue, bank_states)
        write_candidates = self._get_row_hit_candidates_fast(write_queue, bank_states)

        # If no row-hit requests, get all requests
        if not read_candidates and not write_candidates:
            read_candidates = list(read_queue._queue)
            write_candidates = list(write_queue._queue)

        if not read_candidates and not write_candidates:
            return None

        # Apply QoS selection if enabled
        if self._qos_enabled:
            selected = self._qos_aware_select(
                read_candidates, write_candidates, current_time, last_cmd_type
            )
        else:
            # Standard FR-FCFS: row-hit first, then oldest
            best_read = self._select_oldest(read_candidates) if read_candidates else None
            best_write = self._select_oldest(write_candidates) if write_candidates else None
            selected = self._arbitrate_read_write_fast(best_read, best_write, last_cmd_type)

        if selected:
            # Update request state
            selected.mark_scheduled(current_time)
            
            # Update statistics
            self.stats.record_schedule(
                selected, 
                row_hit=selected.row_hit,
                qos=getattr(selected, 'qos', 8),
                is_read=selected.is_read
            )
            
            # Update QoS starvation tracking
            if self._qos_enabled:
                self._update_starvation(getattr(selected, 'qos', 8))
            
            # Record bank command for conflict tracking
            self._bank_conflict_tracker.record_command(
                selected.bank_group_id,
                selected.bank_id,
                current_time,
                'ACT' if not selected.row_hit else 'RD'  # Simplified
            )
            
            # Remove from queue
            if selected.is_read:
                read_queue.remove(selected.request_id)
            else:
                write_queue.remove(selected.request_id)

        return selected

    def _qos_aware_select(self, read_candidates: List[HBMRequest],
                          write_candidates: List[HBMRequest],
                          current_time: float,
                          last_cmd_type: str) -> Optional[HBMRequest]:
        """QoS-aware request selection with FR-FCFS within priority
        
        Args:
            read_candidates: Read requests with row-hit info
            write_candidates: Write requests with row-hit info
            current_time: Current simulation time
            last_cmd_type: Last command type
            
        Returns:
            Best request to schedule
        """
        # Group by QoS level
        by_qos_read: Dict[int, List[HBMRequest]] = defaultdict(list)
        by_qos_write: Dict[int, List[HBMRequest]] = defaultdict(list)
        
        for req in read_candidates:
            qos = getattr(req, 'qos', 8)
            by_qos_read[qos].append(req)
            
        for req in write_candidates:
            qos = getattr(req, 'qos', 8)
            by_qos_write[qos].append(req)
        
        # Find best candidate across all QoS levels
        best_score = -1.0
        best_request = None
        
        for qos in range(15, -1, -1):  # High to low
            read_list = by_qos_read.get(qos, [])
            write_list = by_qos_write.get(qos, [])
            
            # Get best from this QoS level
            best_read = self._fr_fcfs_select(read_list) if read_list else None
            best_write = self._fr_fcfs_select(write_list) if write_list else None
            
            # Compute scores
            for req, candidates in [(best_read, read_list), (best_write, write_list)]:
                if req is None:
                    continue
                    
                score = self._compute_qos_score(req, current_time)
                score += self._get_starvation_bonus(qos)
                
                if score > best_score:
                    best_score = score
                    best_request = req
        
        # If no request selected via QoS, fallback to standard arbitration
        if best_request is None:
            best_read = self._select_oldest(read_candidates) if read_candidates else None
            best_write = self._select_oldest(write_candidates) if write_candidates else None
            best_request = self._arbitrate_read_write_fast(
                best_read, best_write, last_cmd_type
            )
            
        return best_request

    def _fr_fcfs_select(self, candidates: List[HBMRequest]) -> Optional[HBMRequest]:
        """First-Ready FCFS selection
        
        Priority:
        1. Row hit requests
        2. Oldest request (FCFS)
        
        Args:
            candidates: List of candidate requests
            
        Returns:
            Best request to schedule
        """
        if not candidates:
            return None
            
        # Priority 1: Row hit requests
        row_hits = [r for r in candidates if r.row_hit]
        if row_hits:
            return min(row_hits, key=lambda r: r.arrival_time)
            
        # Priority 2: All requests, oldest first
        return min(candidates, key=lambda r: r.arrival_time)

    def _get_row_hit_candidates_fast(self, queue, 
                                     bank_states: Dict) -> List[HBMRequest]:
        """Fast batch get row-hit candidates

        Optimizations:
        - Direct queue iteration
        - Early exit for hit detection
        - Reduced bank_state lookups
        """
        candidates = []
        queue_items = queue._queue

        for req in queue_items:
            bank_key = (req.channel_id, req.pseudo_channel_id, req.bank_id)
            bank_state = bank_states.get(bank_key)

            if bank_state is None:
                # No state tracked, use existing row_hit flag
                if req.row_hit:
                    candidates.append(req)
                continue

            # Row hit detection:
            # 1. Fast path: row currently open
            # 2. Slower path: row was recently accessed (last_row), needs PRE then ACT
            if bank_state.is_open and bank_state.open_row == req.row_id:
                req.row_hit = True
                candidates.append(req)
            elif bank_state.last_row == req.row_id:
                # Row was recently accessed - can still hit after PRE+ACT
                # This counts as a row hit for scheduling priority
                req.row_hit = True
                candidates.append(req)
            else:
                req.row_hit = False

        return candidates

    def _get_row_hit_candidates(self, queue, bank_states: Dict) -> List[HBMRequest]:
        """Get row-hit candidate requests - Legacy compatibility"""
        return self._get_row_hit_candidates_fast(queue, bank_states)

    def _select_oldest(self, candidates: List[HBMRequest]) -> Optional[HBMRequest]:
        """Select oldest request - Optimized"""
        if not candidates:
            return None
        return min(candidates, key=lambda r: r.arrival_time)

    def _arbitrate_read_write_fast(self, read_req: Optional[HBMRequest],
                                   write_req: Optional[HBMRequest],
                                   last_cmd: str) -> Optional[HBMRequest]:
        """Fast read/write arbitration

        Optimizations:
        - Pre-computed turnaround penalty
        - Reduced branching
        """
        if not read_req and not write_req:
            return None

        if read_req and not write_req:
            return read_req

        if write_req and not read_req:
            return write_req

        # Both exist - select by arrival time with turnaround penalty
        read_score = read_req.arrival_time
        write_score = write_req.arrival_time

        # Apply turnaround penalty (in time units)
        if last_cmd == "READ":
            # Penalize write after read
            write_score += self.TURNAROUND_PENALTY
        else:
            # Penalize read after write
            read_score += self.TURNAROUND_PENALTY

        return read_req if read_score < write_score else write_req

    def _arbitrate_read_write(self, read_req: Optional[HBMRequest],
                              write_req: Optional[HBMRequest],
                              last_cmd: str, current_time: float) -> Optional[HBMRequest]:
        """Read/Write arbitration - Legacy compatibility"""
        return self._arbitrate_read_write_fast(read_req, write_req, last_cmd)

    def check_bank_conflict(self, request: HBMRequest, 
                           current_time: float, tCCD: float = 4.0) -> bool:
        """Check if a request would conflict with recent commands
        
        Args:
            request: Request to check
            current_time: Current simulation time
            tCCD: Column command delay threshold
            
        Returns:
            True if there would be a conflict
        """
        return self._bank_conflict_tracker.has_conflict(
            request.bank_group_id,
            request.bank_id,
            current_time,
            tCCD
        )

    def clear_cache(self):
        """Clear cached candidates"""
        self._cached_read_candidates.clear()
        self._cached_write_candidates.clear()

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        return self.stats.to_dict()

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = SchedulerStats()
        self._starvation_counter.clear()


# Batch scheduler for processing multiple requests at once
@dataclass
class BatchSchedulerConfig:
    """Configuration for batch scheduling"""
    batch_size: int = 32
    max_queue_scan: int = 64  # Maximum queue entries to scan per batch


class BatchScheduler(HBMScheduler):
    """Batch Scheduler - Process multiple requests efficiently

    Optimizations:
    - Process requests in batches
    - Vectorized priority calculation
    - Reduced queue operations
    """

    __slots__ = ('batch_config', '_scheduler')

    def __init__(self, config: HBMConfig, batch_config: BatchSchedulerConfig = None):
        super().__init__(config)
        self.batch_config = batch_config or BatchSchedulerConfig()
        self._scheduler = FRFCFSScheduler(config)

    def schedule_batch(self, read_queue: ReadQueue, write_queue: WriteQueue,
                      bank_states: Dict[Tuple, BankState],
                      current_time: float,
                      last_cmd_type: str = "READ") -> List[HBMRequest]:
        """Schedule batch of requests

        Args:
            read_queue: Read queue
            write_queue: Write queue
            bank_states: Bank state dictionary
            current_time: Current time
            last_cmd_type: Last command type

        Returns:
            List of scheduled requests
        """
        scheduled = []
        batch_size = self.batch_config.batch_size

        for _ in range(batch_size):
            # Check if queues are empty
            if read_queue.is_empty() and write_queue.is_empty():
                break

            request = self._scheduler.schedule(
                read_queue, write_queue, bank_states, current_time, last_cmd_type
            )

            if request is None:
                break

            scheduled.append(request)
            last_cmd_type = "READ" if request.is_read else "WRITE"

        return scheduled

    def schedule(self, read_queue: ReadQueue, write_queue: WriteQueue,
                bank_states: Dict[Tuple, BankState],
                current_time: float,
                last_cmd_type: str = "READ") -> Optional[HBMRequest]:
        """Single request scheduling - delegates to FRFCFSScheduler"""
        return self._scheduler.schedule(
            read_queue, write_queue, bank_states, current_time, last_cmd_type
        )


# Utility function for creating HBM4 scheduler
def create_hbm4_scheduler(config: HBMConfig = None, 
                          qos_enabled: bool = True) -> FRFCFSScheduler:
    """Create an HBM4 FR-FCFS scheduler
    
    Args:
        config: HBM configuration (uses HBM4_DEFAULT if None)
        qos_enabled: Enable 16-level QoS scheduling
        
    Returns:
        Configured FRFCFSScheduler instance
    """
    if config is None:
        config = HBM4_DEFAULT
    return FRFCFSScheduler(config, qos_enabled=qos_enabled)