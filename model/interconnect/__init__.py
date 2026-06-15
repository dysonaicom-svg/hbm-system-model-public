"""
Interconnect Module for HBM4 System Modeling

This module provides interconnect models for HBM4 multi-stack systems,
supporting various topologies, routing mechanisms, and arbitration schemes.

Key Features:
- Multiple topology options (Crossbar, Mesh, Binary Tree)
- Flexible routing (Address-based, Load-based, Shortest Path)
- Configurable arbitration (Round-robin, Priority)
- Multi-stack support (1-8 HBM4 stacks)
- Load balancing across stacks

Based on:
- JEDEC JESD270-4A HBM4 specification
- Multi-agent research findings (2026-06-15)

Architecture Overview:
    Traffic Generator / Requesters
            |
    +-------+-------+
    |  Interconnect  |  <-- This module
    +-------+-------+
    |  HBM Controller |
    +-------+-------+
    |  HBM4 Stacks   |
    +---------------+

Topologies:
1. Crossbar: Full connectivity, O(1) routing, best for small scale
2. Mesh: Grid-based, good locality, scalable
3. Binary Tree: Hierarchical, efficient for broadcast, scalable

Usage Example:
    >>> from model.interconnect import CrossbarInterconnect, RoutingMode, ArbitrationMode
    >>> ic = CrossbarInterconnect(num_ports=32, stack_count=4)
    >>> ic.route_request(addr=0x123456, source_port=0)
    (dest_stack=0, dest_channel=9, latency=2)
"""

from .interconnect import (
    # Enums
    TopologyType,
    RoutingMode,
    ArbitrationMode,
    InterconnectPort,
    InterconnectRequest,
    InterconnectResponse,
    InterconnectStats,

    # Main Classes
    InterconnectBase,
    CrossbarInterconnect,
    MeshInterconnect,
    BinaryTreeInterconnect,
    InterconnectFactory,

    # Utility
    create_interconnect,
)

__all__ = [
    # Enums
    'TopologyType',
    'RoutingMode',
    'ArbitrationMode',
    'InterconnectPort',
    'InterconnectRequest',
    'InterconnectResponse',
    'InterconnectStats',

    # Main Classes
    'InterconnectBase',
    'CrossbarInterconnect',
    'MeshInterconnect',
    'BinaryTreeInterconnect',
    'InterconnectFactory',

    # Utility
    'create_interconnect',
]
