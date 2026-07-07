"""
Parallel Multi-Channel Scheduler for HBM4

Optimizes 32-channel parallel access with load balancing and conflict avoidance.
"""

from typing import List, Optional, Tuple, Dict, Set
from dataclasses import dataclass, field
from collections import defaultdict
import logging

_logger = logging.getLogger('hbm4.parallel_scheduler')

from model.controller.request import HBMRequest


@dataclass
class ChannelLoad:
    """Per-channel load information"""
    channel_id: int
    pending_requests: int = 0
    active_banks: Set[int] = field(default_factory=set)
    last_service_cycle: int = 0
    load_score: float = 0.0

    def update_score(self, current_cycle: int):
        """Calculate channel load score"""
        # Factor in pending requests and time since last service
        time_factor = min(1.0, (current_cycle - self.last_service_cycle) / 1000.0)
        self.load_score = self.pending_requests * 0.7 + time_factor * 0.3


class ParallelChannelScheduler:
    """Multi-channel parallel scheduler with load balancing

    Features:
    - 32-channel parallel scheduling
    - Load balancing across channels
    - Bank conflict avoidance across channels
    - Priority-based arbitration
    """

    def __init__(self, num_channels: int = 32):
        self.num_channels = num_channels
        self.channel_loads: Dict[int, ChannelLoad] = {
            i: ChannelLoad(channel_id=i) for i in range(num_channels)
        }
        self._pending_by_channel: Dict[int, List[HBMRequest]] = defaultdict(list)
        self._request_channel: Dict[int, int] = {}  # request_id -> channel

    def submit_request(self, request: HBMRequest, channel_id: int):
        """Submit a request to a specific channel"""
        self._pending_by_channel[channel_id].append(request)
        self._request_channel[request.request_id] = channel_id
        self.channel_loads[channel_id].pending_requests += 1

    def schedule_next(self, current_cycle: int) -> List[HBMRequest]:
        """Schedule next batch of requests across all channels

        Returns list of requests to execute, one per available bank group.
        """
        scheduled = []

        # Update load scores
        for ch_id, load in self.channel_loads.items():
            load.update_score(current_cycle)

        # Get channels sorted by load (least loaded first)
        sorted_channels = sorted(
            self.channel_loads.items(),
            key=lambda x: x[1].load_score
        )

        # Schedule one request per channel
        for ch_id, load in sorted_channels[:8]:  # Max 8 parallel
            if self._pending_by_channel[ch_id]:
                # Find best request (row-hit first)
                best_req = self._select_best_request(ch_id)
                if best_req:
                    scheduled.append(best_req)
                    load.last_service_cycle = current_cycle

        return scheduled

    def _select_best_request(self, channel_id: int) -> Optional[HBMRequest]:
        """Select best request from channel queue"""
        queue = self._pending_by_channel[channel_id]
        if not queue:
            return None

        # FR-FCFS: prioritize row-hit, then by timestamp
        row_hits = [r for r in queue if r.row_hit]
        if row_hits:
            return min(row_hits, key=lambda r: r.arrival_time)

        return min(queue, key=lambda r: r.arrival_time)

    def get_channel_load_stats(self) -> Dict[int, float]:
        """Get load statistics for all channels"""
        return {ch_id: load.load_score for ch_id, load in self.channel_loads.items()}

    def get_least_loaded_channel(self) -> int:
        """Get the least loaded channel ID"""
        return min(
            self.channel_loads.items(),
            key=lambda x: x[1].load_score
        )[0]

    def get_most_loaded_channel(self) -> int:
        """Get the most loaded channel ID"""
        return max(
            self.channel_loads.items(),
            key=lambda x: x[1].load_score
        )[0]

    def balance_load(self, threshold: float = 0.3) -> List[Tuple[int, int]]:
        """Balance load between channels

        Returns list of (src_channel, dst_channel) for migration.
        """
        migrations = []

        most_loaded = self.get_most_loaded_channel()
        least_loaded = self.get_least_loaded_channel()

        load_diff = (
            self.channel_loads[most_loaded].load_score -
            self.channel_loads[least_loaded].load_score
        )

        if load_diff > threshold:
            # Migrate one request
            queue = self._pending_by_channel[most_loaded]
            if len(queue) > 2:  # Keep at least 2 requests
                req = queue.pop(0)
                self._request_channel[req.request_id] = least_loaded
                self._pending_by_channel[least_loaded].append(req)

                self.channel_loads[most_loaded].pending_requests -= 1
                self.channel_loads[least_loaded].pending_requests += 1

                migrations.append((most_loaded, least_loaded))

        return migrations

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        total_pending = sum(l.pending_requests for l in self.channel_loads.values())
        return {
            'total_pending': total_pending,
            'channels_active': sum(1 for l in self.channel_loads.values() if l.pending_requests > 0),
            'avg_load': sum(l.load_score for l in self.channel_loads.values()) / self.num_channels,
            'load_variance': self._calculate_load_variance(),
        }

    def _calculate_load_variance(self) -> float:
        """Calculate load variance across channels"""
        loads = [l.load_score for l in self.channel_loads.values()]
        mean = sum(loads) / len(loads)
        return sum((x - mean) ** 2 for x in loads) / len(loads)
