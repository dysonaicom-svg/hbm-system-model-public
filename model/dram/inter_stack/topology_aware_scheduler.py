"""
Topology-Aware Request Scheduler
Schedules requests across multiple HBM stacks with topology awareness

Features:
- Workload-aware stack selection
- Congestion-aware routing
- Load balancing across stacks
- Priority-based scheduling

Reference: model/dram/stack_model.py
"""

from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import heapq
import random

from model.dram.inter_stack.inter_stack_network import (
    InterStackNetwork,
    InterconnectTopology,
    PacketType,
)
from model.dram.inter_stack.stack_router import (
    StackRouter,
    RoutingAlgorithm,
    Route,
)


class SchedulingPolicy(Enum):
    """Request scheduling policies"""
    ROUND_ROBIN = "round_robin"
    SHORTEST_QUEUE = "shortest_queue"
    TOPOLOGY_AWARE = "topology_aware"
    CONGESTION_AWARE = "congestion_aware"
    PRIORITY = "priority"
    WEIGHTED = "weighted"


@dataclass
class Request:
    """Memory request that may span multiple stacks"""
    request_id: int
    src_stack: int
    dst_stack: int
    address: int
    size_bytes: int = 64
    is_write: bool = False
    priority: int = 0          # Higher = more urgent
    weight: float = 1.0        # For weighted scheduling
    created_at: float = 0.0
    deadline_ns: Optional[float] = None
    traffic_class: str = "best_effort"  # best_effort, high_priority, realtime

    @property
    def latency_sensitive(self) -> bool:
        return self.traffic_class in ("high_priority", "realtime")

    def __lt__(self, other):
        # Priority queue ordering: higher priority first, then earlier deadline
        if self.priority != other.priority:
            return self.priority > other.priority
        if self.deadline_ns is not None and other.deadline_ns is not None:
            return self.deadline_ns < other.deadline_ns
        return self.request_id < other.request_id


@dataclass
class StackLoadInfo:
    """Per-stack load information"""
    stack_id: int
    pending_requests: int = 0
    queue_depth: int = 0
    avg_latency_ns: float = 0.0
    throughput_gbps: float = 0.0
    congestion_score: float = 0.0

    @property
    def load_factor(self) -> float:
        """Normalized load metric (0.0 = idle, 1.0 = saturated)"""
        return min(1.0, (self.queue_depth + self.pending_requests) / 32.0)


@dataclass
class ScheduledRequest:
    """Request with scheduling decision"""
    request: Request
    route: Route
    scheduled_at: float
    estimated_latency_ns: float


class TopologyAwareScheduler:
    """Topology-aware request scheduler for multi-stack HBM

    Schedules requests across multiple stacks considering:
    - Network topology and distance
    - Link congestion
    - Stack load balancing
    - Request priority and deadlines
    """

    def __init__(
        self,
        network: InterStackNetwork,
        router: Optional[StackRouter] = None,
        scheduling_policy: SchedulingPolicy = SchedulingPolicy.TOPOLOGY_AWARE,
        max_queue_depth: int = 32,
    ):
        self.network = network
        self.router = router or StackRouter(network, RoutingAlgorithm.MINIMAL)
        self.policy = scheduling_policy
        self.max_queue_depth = max_queue_depth

        # Stack load tracking
        self.stack_load: Dict[int, StackLoadInfo] = {
            i: StackLoadInfo(stack_id=i)
            for i in range(network.num_stacks)
        }

        # Request queues per stack
        self.request_queues: Dict[int, List[Request]] = {
            i: [] for i in range(network.num_stacks)
        }

        # Global scheduling queue
        self.scheduling_queue: List[Request] = []

        # Statistics
        self.total_scheduled: int = 0
        self.total_rejected: int = 0
        self.request_id_counter: int = 0
        self.scheduling_decisions: Dict[str, int] = {}

    def submit_request(
        self,
        dst_stack: int,
        address: int,
        size_bytes: int = 64,
        is_write: bool = False,
        src_stack: Optional[int] = None,
        priority: int = 0,
        weight: float = 1.0,
        traffic_class: str = "best_effort",
        current_time: float = 0.0,
    ) -> Optional[Request]:
        """Submit a new request for scheduling"""
        # Assign source stack if not specified
        if src_stack is None:
            src_stack = self._select_source_stack(dst_stack, current_time)

        request = Request(
            request_id=self.request_id_counter,
            src_stack=src_stack,
            dst_stack=dst_stack,
            address=address,
            size_bytes=size_bytes,
            is_write=is_write,
            priority=priority,
            weight=weight,
            created_at=current_time,
            traffic_class=traffic_class,
        )
        self.request_id_counter += 1

        # Check queue capacity
        if len(self.request_queues[dst_stack]) >= self.max_queue_depth:
            self.total_rejected += 1
            return None

        # Add to scheduling queue
        heapq.heappush(self.scheduling_queue, request)
        self.stack_load[dst_stack].pending_requests += 1

        return request

    def _select_source_stack(self, dst: int, current_time: float) -> int:
        """Select best source stack based on policy"""
        if self.policy == SchedulingPolicy.ROUND_ROBIN:
            # Simple round-robin from stack 0
            return self.total_scheduled % self.network.num_stacks

        elif self.policy == SchedulingPolicy.SHORTEST_QUEUE:
            # Select stack with lowest load
            return min(
                range(self.network.num_stacks),
                key=lambda s: self.stack_load[s].queue_depth
            )

        elif self.policy == SchedulingPolicy.WEIGHTED:
            # Weighted random selection
            weights = [1.0 / (self.stack_load[i].load_factor + 0.1)
                      for i in range(self.network.num_stacks)]
            total = sum(weights)
            weights = [w / total for w in weights]
            return random.choices(range(self.network.num_stacks), weights=weights)[0]

        else:
            # Default: local stack (same as destination for local access)
            return dst

    def schedule_next(self, current_time: float = 0.0) -> Optional[ScheduledRequest]:
        """Schedule the next request from the queue"""
        if not self.scheduling_queue:
            return None

        # Get highest priority request
        request = heapq.heappop(self.scheduling_queue)
        self.stack_load[request.dst_stack].pending_requests -= 1

        # Compute route
        route = self.router.route(request.src_stack, request.dst_stack, PacketType.REQUEST)

        if route is None:
            return None

        # Calculate estimated latency
        link_latency = route.latency_ns
        queue_delay = self.stack_load[request.dst_stack].load_factor * 10.0  # Simple model
        est_latency = link_latency + queue_delay

        # Create scheduled request
        scheduled = ScheduledRequest(
            request=request,
            route=route,
            scheduled_at=current_time,
            estimated_latency_ns=est_latency,
        )

        # Update statistics
        self.total_scheduled += 1
        self.request_queues[request.dst_stack].append(request)

        decision_key = f"{request.src_stack}->{request.dst_stack}"
        self.scheduling_decisions[decision_key] = self.scheduling_decisions.get(decision_key, 0) + 1

        # Update stack load
        self.stack_load[request.dst_stack].queue_depth = len(self.request_queues[request.dst_stack])

        return scheduled

    def complete_request(self, request: Request, actual_latency_ns: float, current_time: float):
        """Mark a request as completed"""
        if request in self.request_queues[request.dst_stack]:
            self.request_queues[request.dst_stack].remove(request)
            self.stack_load[request.dst_stack].queue_depth = len(self.request_queues[request.dst_stack])

            # Update latency statistics
            load = self.stack_load[request.dst_stack]
            load.avg_latency_ns = (load.avg_latency_ns * 0.9 + actual_latency_ns * 0.1)

            # Update congestion
            load.congestion_score = min(1.0, actual_latency_ns / 100.0)

    def select_best_stack(
        self,
        address: int,
        access_type: str = "read",
        current_time: float = 0.0,
    ) -> int:
        """Select the best stack for a given address

        This is a simplified address-to-stack mapping.
        In real systems, this would use complex address decoding.
        """
        # Simple hash-based distribution
        stack_id = address % self.network.num_stacks

        if self.policy == SchedulingPolicy.CONGESTION_AWARE:
            # Find least congested stack
            best_stack = min(
                range(self.network.num_stacks),
                key=lambda s: self.stack_load[s].congestion_score
            )
            stack_id = best_stack

        elif self.policy == SchedulingPolicy.TOPOLOGY_AWARE:
            # Consider topology distance from requestor
            min_load = float('inf')
            best_stack = stack_id
            for s in range(self.network.num_stacks):
                route = self.router.route(s, stack_id)
                if route:
                    cost = route.num_hops * 10 + self.stack_load[s].load_factor * 5
                    if cost < min_load:
                        min_load = cost
                        best_stack = s
            stack_id = best_stack

        return stack_id

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        total_queue_depth = sum(len(q) for q in self.request_queues.values())
        avg_congestion = sum(s.congestion_score for s in self.stack_load.values()) / max(1, self.network.num_stacks)

        return {
            'total_scheduled': self.total_scheduled,
            'total_rejected': self.total_rejected,
            'rejection_rate': self.total_rejected / max(1, self.total_scheduled + self.total_rejected),
            'pending_requests': sum(s.pending_requests for s in self.stack_load.values()),
            'total_queue_depth': total_queue_depth,
            'avg_congestion': avg_congestion,
            'scheduling_policy': self.policy.value,
            'scheduling_decisions': dict(self.scheduling_decisions),
            'stack_load': {
                s: {
                    'queue_depth': self.stack_load[s].queue_depth,
                    'congestion_score': self.stack_load[s].congestion_score,
                    'avg_latency_ns': self.stack_load[s].avg_latency_ns,
                }
                for s in range(self.network.num_stacks)
            },
        }

    def reset_stats(self):
        """Reset statistics counters"""
        self.total_scheduled = 0
        self.total_rejected = 0
        self.scheduling_decisions.clear()