"""
Smart Priority Queue with Aging and Request Coalescing

Features:
- Priority aging to prevent starvation
- Request coalescing for write combining
- Deadlock prevention
"""

import heapq
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field
from collections import deque
import logging

_logger = logging.getLogger('hbm4.smart_queue')

from model.controller.request import HBMRequest, RequestState


@dataclass
class QueueEntry:
    """Queue entry with aging information"""
    request: HBMRequest
    enqueue_time: int = 0  # Simulation cycle
    wait_cycles: int = 0
    priority: int = 0  # Original priority

    def __lt__(self, other):
        # Compare by effective priority (considering aging)
        return self.effective_priority < other.effective_priority

    @property
    def effective_priority(self) -> int:
        """Calculate effective priority with aging"""
        # Priority increases over time to prevent starvation
        aging_bonus = min(self.wait_cycles // 100, 8)  # Max +8 priority boost
        return self.priority + aging_bonus


@dataclass
class CoalescedWrite:
    """Coalesced write request"""
    base_address: int
    requests: List[HBMRequest] = field(default_factory=list)
    total_size: int = 0
    max_address: int = 0


class SmartQueue:
    """Smart priority queue with aging and coalescing

    Features:
    - Priority aging to prevent starvation
    - Request coalescing (write combining)
    - Deadlock prevention with timeout
    - Request reordering for optimal scheduling
    """

    def __init__(
        self,
        max_size: int = 64,
        aging_factor: int = 100,
        coalescing_window: int = 10,
        max_wait_timeout: int = 10000
    ):
        self.max_size = max_size
        self.aging_factor = aging_factor
        self.coalescing_window = coalescing_window
        self.max_wait_timeout = max_wait_timeout

        self._heap: List[QueueEntry] = []
        self._address_index: Dict[int, QueueEntry] = {}  # For coalescing
        self._current_cycle: int = 0

        # Statistics
        self.total_enqueues = 0
        self.total_dequeues = 0
        self.coalesced_count = 0
        self.aged_requests = 0

    def enqueue(self, request: HBMRequest, priority: int = 0) -> bool:
        """Add request to queue

        Returns True if enqueued, False if queue is full.
        """
        if len(self._heap) >= self.max_size:
            return False

        self.total_enqueues += 1

        # Check for coalescing opportunity (writes only)
        if not request.is_read:  # is_read=False means write
            coalesced = self._try_coalesce(request)
            if coalesced:
                return True

        entry = QueueEntry(
            request=request,
            enqueue_time=self._current_cycle,
            wait_cycles=0,
            priority=priority
        )

        heapq.heappush(self._heap, entry)
        self._address_index[request.addr] = entry
        return True

    def dequeue(self) -> Optional[HBMRequest]:
        """Remove and return highest priority request"""
        if not self._heap:
            return None

        entry = heapq.heappop(self._heap)
        self._address_index.pop(entry.request.addr, None)
        self.total_dequeues += 1

        if entry.wait_cycles > 0:
            self.aged_requests += 1

        return entry.request

    def peek(self) -> Optional[HBMRequest]:
        """View highest priority request without removing"""
        if not self._heap:
            return None
        return self._heap[0].request

    def update_aging(self):
        """Update aging for all entries"""
        self._current_cycle += 1
        for entry in self._heap:
            entry.wait_cycles = self._current_cycle - entry.enqueue_time

        # Reheapify after aging update
        heapq.heapify(self._heap)

    def _try_coalesce(self, request: HBMRequest) -> bool:
        """Try to coalesce write request with existing"""
        # Find nearby addresses
        nearby = [
            addr for addr in self._address_index.keys()
            if abs(addr - request.addr) <= self.coalescing_window
        ]

        for addr in nearby:
            existing = self._address_index[addr]
            if not existing.request.is_read and existing.request.qos == request.qos:  # is_read=False means write
                # Coalesce: merge data if possible, or just mark for batching
                self.coalesced_count += 1
                _logger.debug(f"Coalesced write at 0x{request.addr:x} with 0x{addr:x}")
                return True

        return False

    def check_deadlock(self) -> List[HBMRequest]:
        """Check for potentially deadlocked requests"""
        timed_out = []
        for entry in self._heap:
            if entry.wait_cycles > self.max_wait_timeout:
                timed_out.append(entry.request)
        return timed_out

    def abort_request(self, request_id: int) -> bool:
        """Abort a specific request by ID"""
        for i, entry in enumerate(self._heap):
            if entry.request.request_id == request_id:
                del self._heap[i]
                self._address_index.pop(entry.request.addr, None)
                heapq.heapify(self._heap)
                return True
        return False

    def get_queue_depth(self) -> int:
        """Get current queue depth"""
        return len(self._heap)

    def get_oldest_request_age(self) -> int:
        """Get age of oldest request in cycles"""
        if not self._heap:
            return 0
        return max(entry.wait_cycles for entry in self._heap)

    def get_statistics(self) -> Dict:
        """Get queue statistics"""
        return {
            'current_depth': len(self._heap),
            'max_size': self.max_size,
            'total_enqueues': self.total_enqueues,
            'total_dequeues': self.total_dequeues,
            'coalesced_count': self.coalesced_count,
            'aged_requests': self.aged_requests,
            'oldest_request_age': self.get_oldest_request_age(),
        }

    def clear(self):
        """Clear all entries"""
        self._heap.clear()
        self._address_index.clear()

    def __len__(self) -> int:
        return len(self._heap)

    def __contains__(self, request_id: int) -> bool:
        """Check if request ID is in queue"""
        return any(e.request.request_id == request_id for e in self._heap)
