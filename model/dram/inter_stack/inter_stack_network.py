"""
Inter-Stack Interconnect Network Model
Multi-stack HBM interconnect with configurable topologies

Supports:
- Mesh topology (nearest-neighbor)
- Full crossbar (any-to-any with low latency)
- Butterfly network (scalable, logarithmic diameter)

Reference: model/dram/stack_model.py
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math


class InterconnectTopology(Enum):
    """Inter-stack interconnect topologies"""
    MESH = "mesh"              # 2D mesh, nearest neighbor
    TORUS = "torus"            # 2D torus with wrap-around
    FULL_CROSSBAR = "full_crossbar"  # Any stack to any stack
    BUTTERFLY = "butterfly"    # Logarithmic diameter network


class PacketType(Enum):
    """Inter-stack packet types"""
    DATA = "data"
    REQUEST = "request"
    RESPONSE = "response"
    COHERENCE = "coherence"
    BROADCAST = "broadcast"


@dataclass
class InterStackLink:
    """Physical link between two stacks"""
    src_stack: int
    dst_stack: int
    bandwidth_gbps: float = 256.0      # Link bandwidth
    latency_ns: float = 1.0            # Link traversal latency
    congested: bool = False
    utilization: float = 0.0           # 0.0 to 1.0

    def __hash__(self):
        return hash((self.src_stack, self.dst_stack))


@dataclass
class InterStackPacket:
    """Packet traversing the interconnect"""
    packet_id: int
    src_stack: int
    dst_stack: int
    packet_type: PacketType
    size_bytes: int = 64
    data_rate: float = 16.0            # GT/s
    created_at: float = 0.0
    hops: List[int] = field(default_factory=list)

    @property
    def transmission_time_ns(self) -> float:
        """Time to transmit packet over one link"""
        return (self.size_bytes * 8) / (self.data_rate * 1e9) * 1e9


@dataclass
class RouteMetrics:
    """Routing decision metrics"""
    path_hops: int
    total_latency_ns: float
    link_congestion: List[float]  # Utilization per link
    estimated_queue_time_ns: float = 0.0


class InterStackNetwork:
    """Inter-stack interconnect network model

    Models the physical interconnect between HBM stacks.
    Supports multiple topologies and routing algorithms.
    """

    def __init__(
        self,
        num_stacks: int,
        topology: InterconnectTopology = InterconnectTopology.MESH,
        link_bandwidth_gbps: float = 256.0,
        link_latency_ns: float = 1.0,
        mesh_rows: int = 2,
        mesh_cols: Optional[int] = None,
    ):
        self.num_stacks = num_stacks
        self.topology = topology
        self.link_bandwidth_gbps = link_bandwidth_gbps
        self.link_latency_ns = link_latency_ns

        # Mesh dimensions (for MESH/TORUS topologies)
        self.mesh_rows = mesh_rows
        self.mesh_cols = mesh_cols or math.ceil(num_stacks / mesh_rows)

        # Link state
        self.links: Dict[Tuple[int, int], InterStackLink] = {}
        self._init_topology()

        # Statistics
        self.total_packets: int = 0
        self.total_hops: int = 0
        self.packet_id_counter: int = 0

    def _init_topology(self):
        """Initialize link topology based on selected architecture"""
        if self.topology == InterconnectTopology.FULL_CROSSBAR:
            # Every stack connected to every other stack
            for src in range(self.num_stacks):
                for dst in range(self.num_stacks):
                    if src != dst:
                        self.links[(src, dst)] = InterStackLink(
                            src_stack=src,
                            dst_stack=dst,
                            bandwidth_gbps=self.link_bandwidth_gbps,
                            latency_ns=self.link_latency_ns,
                        )

        elif self.topology in (InterconnectTopology.MESH, InterconnectTopology.TORUS):
            # Nearest neighbor connections
            self._init_mesh_topology()

        elif self.topology == InterconnectTopology.BUTTERFLY:
            # Butterfly network: log2(n) stages
            self._init_butterfly_topology()

    def _init_mesh_topology(self):
        """Initialize 2D mesh/torus topology"""
        def stack_coord(stack_id: int) -> Tuple[int, int]:
            return (stack_id // self.mesh_cols, stack_id % self.mesh_cols)

        def coord_to_stack(row: int, col: int) -> Optional[int]:
            if 0 <= row < self.mesh_rows and 0 <= col < self.mesh_cols:
                idx = row * self.mesh_cols + col
                if idx < self.num_stacks:
                    return idx
            return None

        for stack in range(self.num_stacks):
            row, col = stack_coord(stack)

            # Cardinal directions
            neighbors = [
                (row - 1, col),  # North
                (row + 1, col),  # South
                (row, col - 1),  # West
                (row, col + 1),  # East
            ]

            # Torus wrap-around
            if self.topology == InterconnectTopology.TORUS:
                neighbors = [
                    ((row - 1) % self.mesh_rows, col),
                    ((row + 1) % self.mesh_rows, col),
                    (row, (col - 1) % self.mesh_cols),
                    (row, (col + 1) % self.mesh_cols),
                ]

            for n_row, n_col in neighbors:
                neighbor = coord_to_stack(n_row, n_col)
                if neighbor is not None and neighbor != stack:
                    # Avoid duplicate links
                    if (stack, neighbor) not in self.links:
                        self.links[(stack, neighbor)] = InterStackLink(
                            src_stack=stack,
                            dst_stack=neighbor,
                            bandwidth_gbps=self.link_bandwidth_gbps,
                            latency_ns=self.link_latency_ns,
                        )

    def _init_butterfly_topology(self):
        """Initialize butterfly network topology"""
        stages = math.ceil(math.log2(self.num_stacks))
        for stage in range(stages):
            for node in range(self.num_stacks):
                # Butterfly connects to node with one bit flipped at this stage
                bit_pos = stage % stages
                neighbor = node ^ (1 << bit_pos)
                if neighbor < self.num_stacks and neighbor != node:
                    if (node, neighbor) not in self.links:
                        self.links[(node, neighbor)] = InterStackLink(
                            src_stack=node,
                            dst_stack=neighbor,
                            bandwidth_gbps=self.link_bandwidth_gbps,
                            latency_ns=self.link_latency_ns,
                        )

    def get_hops(self, src: int, dst: int) -> List[int]:
        """Compute minimum hop path from src to dst"""
        if src == dst:
            return [src]

        if self.topology == InterconnectTopology.FULL_CROSSBAR:
            return [src, dst]

        if self.topology == InterconnectTopology.MESH:
            return self._mesh_routing(src, dst)

        if self.topology == InterconnectTopology.TORUS:
            return self._torus_routing(src, dst)

        if self.topology == InterconnectTopology.BUTTERFLY:
            return self._butterfly_routing(src, dst)

        return [src, dst]  # Fallback

    def _mesh_routing(self, src: int, dst: int) -> List[int]:
        """Dimensional routing for mesh"""
        src_row, src_col = src // self.mesh_cols, src % self.mesh_cols
        dst_row, dst_col = dst // self.mesh_cols, dst % self.mesh_cols

        path = [src]
        curr = src

        while curr != dst:
            row, col = curr // self.mesh_cols, curr % self.mesh_cols

            # Move toward destination
            if row < dst_row:
                next_stack = (row + 1) * self.mesh_cols + col
            elif row > dst_row:
                next_stack = (row - 1) * self.mesh_cols + col
            elif col < dst_col:
                next_stack = row * self.mesh_cols + (col + 1)
            elif col > dst_col:
                next_stack = row * self.mesh_cols + (col - 1)
            else:
                break

            if next_stack < self.num_stacks and (curr, next_stack) in self.links:
                path.append(next_stack)
                curr = next_stack
            else:
                # Dead end, try alternate route
                break

        if path[-1] != dst:
            path.append(dst)
        return path

    def _torus_routing(self, src: int, dst: int) -> List[int]:
        """Dimensional routing for torus with wrap-around"""
        src_row, src_col = src // self.mesh_cols, src % self.mesh_cols
        dst_row, dst_col = dst // self.mesh_cols, dst % self.mesh_cols

        path = [src]
        curr = src

        while curr != dst:
            row, col = curr // self.mesh_cols, curr % self.mesh_cols

            # Wrap-aware distance
            d_row = (dst_row - row) % self.mesh_rows
            d_col = (dst_col - col) % self.mesh_cols

            # Pick dimension with larger distance (or row on tie)
            if d_row >= d_col:
                next_row = (row + 1) % self.mesh_rows
                next_stack = next_row * self.mesh_cols + col
            else:
                next_col = (col + 1) % self.mesh_cols
                next_stack = row * self.mesh_cols + next_col

            if (curr, next_stack) in self.links:
                path.append(next_stack)
                curr = next_stack
            else:
                break

        if path[-1] != dst:
            path.append(dst)
        return path

    def _butterfly_routing(self, src: int, dst: int) -> List[int]:
        """Bitwise butterfly routing"""
        path = [src]
        curr = src
        stages = math.ceil(math.log2(self.num_stacks))

        for stage in range(stages):
            bit_pos = stage % stages
            # Check if destination bit differs at this position
            if ((dst >> bit_pos) & 1) != ((curr >> bit_pos) & 1):
                neighbor = curr ^ (1 << bit_pos)
                if neighbor < self.num_stacks and (curr, neighbor) in self.links:
                    path.append(neighbor)
                    curr = neighbor

        if path[-1] != dst:
            path.append(dst)
        return path

    def calculate_route_metrics(self, src: int, dst: int) -> RouteMetrics:
        """Calculate metrics for a route"""
        path = self.get_hops(src, dst)
        hops = len(path) - 1

        total_latency = 0.0
        congestion = []

        for i in range(len(path) - 1):
            link = self.links.get((path[i], path[i + 1]))
            if link:
                total_latency += link.latency_ns
                congestion.append(link.utilization)

        return RouteMetrics(
            path_hops=hops,
            total_latency_ns=total_latency,
            link_congestion=congestion,
        )

    def send_packet(
        self,
        src_stack: int,
        dst_stack: int,
        packet_type: PacketType,
        size_bytes: int = 64,
        current_time: float = 0.0,
    ) -> Tuple[InterStackPacket, RouteMetrics]:
        """Send a packet from src to dst"""
        path = self.get_hops(src_stack, dst_stack)
        metrics = self.calculate_route_metrics(src_stack, dst_stack)

        packet = InterStackPacket(
            packet_id=self.packet_id_counter,
            src_stack=src_stack,
            dst_stack=dst_stack,
            packet_type=packet_type,
            size_bytes=size_bytes,
            created_at=current_time,
            hops=path,
        )
        self.packet_id_counter += 1

        # Update link utilization
        for i in range(len(path) - 1):
            link = self.links.get((path[i], path[i + 1]))
            if link:
                link.utilization = min(1.0, link.utilization + 0.1)

        self.total_packets += 1
        self.total_hops += len(path) - 1

        return packet, metrics

    def get_topology_info(self) -> Dict:
        """Get topology information"""
        return {
            'num_stacks': self.num_stacks,
            'topology': self.topology.value,
            'mesh_rows': self.mesh_rows,
            'mesh_cols': self.mesh_cols,
            'num_links': len(self.links),
            'link_bandwidth_gbps': self.link_bandwidth_gbps,
            'link_latency_ns': self.link_latency_ns,
        }

    def get_stats(self) -> Dict:
        """Get network statistics"""
        avg_hops = self.total_hops / max(1, self.total_packets)
        avg_congestion = sum(l.utilization for l in self.links.values()) / max(1, len(self.links))

        return {
            'total_packets': self.total_packets,
            'total_hops': self.total_hops,
            'avg_hops': avg_hops,
            'avg_link_utilization': avg_congestion,
            'topology': self.topology.value,
        }


def create_network(
    num_stacks: int,
    topology: str = "mesh",
    **kwargs,
) -> InterStackNetwork:
    """Factory function to create an inter-stack network"""
    topo_map = {
        'mesh': InterconnectTopology.MESH,
        'torus': InterconnectTopology.TORUS,
        'crossbar': InterconnectTopology.FULL_CROSSBAR,
        'butterfly': InterconnectTopology.BUTTERFLY,
    }

    topo = topo_map.get(topology.lower(), InterconnectTopology.MESH)
    return InterStackNetwork(num_stacks=num_stacks, topology=topo, **kwargs)