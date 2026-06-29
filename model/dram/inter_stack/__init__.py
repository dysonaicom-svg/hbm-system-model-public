"""
Inter-Stack Interconnect Modeling
Multi-stack HBM interconnect network, routing, and scheduling

Reference: model/dram/stack_model.py
"""

from model.dram.inter_stack.inter_stack_network import (
    InterStackNetwork,
    InterconnectTopology,
    PacketType,
    InterStackLink,
    InterStackPacket,
    RouteMetrics,
    create_network,
)
from model.dram.inter_stack.stack_router import (
    StackRouter,
    RoutingAlgorithm,
    Route,
    QueueEntry,
)
from model.dram.inter_stack.topology_aware_scheduler import (
    TopologyAwareScheduler,
    SchedulingPolicy,
    Request,
    StackLoadInfo,
    ScheduledRequest,
)

__all__ = [
    # Network
    'InterStackNetwork',
    'InterconnectTopology',
    'PacketType',
    'InterStackLink',
    'InterStackPacket',
    'RouteMetrics',
    'create_network',
    # Router
    'StackRouter',
    'RoutingAlgorithm',
    'Route',
    'QueueEntry',
    # Scheduler
    'TopologyAwareScheduler',
    'SchedulingPolicy',
    'Request',
    'StackLoadInfo',
    'ScheduledRequest',
]