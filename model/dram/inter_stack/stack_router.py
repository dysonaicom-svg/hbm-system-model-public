"""
Stack Router - Routing Logic Between HBM Stacks
Multi-path routing with congestion awareness

Reference: model/dram/stack_model.py
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import heapq

from model.dram.inter_stack.inter_stack_network import (
    InterStackNetwork,
    InterStackPacket,
    PacketType,
    RouteMetrics,
)


class RoutingAlgorithm(Enum):
    """Routing algorithm selection"""
    MINIMAL = "minimal"                    # Shortest path only
    CONGESTION_AWARE = "congestion_aware"  # Avoid congested links
    ADAPTIVE = "adaptive"                  # Runtime adaptation
    ECMP = "ecmp"                          # Equal-cost multipath


@dataclass
class Route:
    """Computed route from source to destination"""
    path: List[int]
    cost: float
    metrics: RouteMetrics
    algorithm: RoutingAlgorithm

    @property
    def num_hops(self) -> int:
        return len(self.path) - 1

    @property
    def latency_ns(self) -> float:
        return self.metrics.total_latency_ns


@dataclass
class QueueEntry:
    """Priority queue entry for routing search"""
    cost: float
    node: int
    path: Tuple[int, ...]
    priority: int = 0  # Tie-breaker


class StackRouter:
    """Router for inter-stack traffic

    Supports multiple routing algorithms:
    - Minimal: Always shortest path
    - Congestion-aware: Avoid congested links
    - Adaptive: Switch based on runtime conditions
    - ECMP: Random among equal-cost paths
    """

    def __init__(
        self,
        network: InterStackNetwork,
        routing_algorithm: RoutingAlgorithm = RoutingAlgorithm.MINIMAL,
        enable_alternate_routes: bool = True,
    ):
        self.network = network
        self.routing_algorithm = routing_algorithm
        self.enable_alternate_routes = enable_alternate_routes

        # Routing tables (precomputed)
        self.routing_tables: Dict[int, Dict[int, List[Route]]] = {}
        self._build_routing_tables()

        # Statistics
        self.routes_computed: int = 0
        self.routes_used: Dict[str, int] = {}

    def _build_routing_tables(self):
        """Precompute routing tables for all source-destination pairs"""
        for src in range(self.network.num_stacks):
            self.routing_tables[src] = {}
            for dst in range(self.network.num_stacks):
                if src != dst:
                    routes = self._find_all_routes(src, dst)
                    self.routing_tables[src][dst] = routes
                else:
                    self.routing_tables[src][dst] = []

    def _find_all_routes(self, src: int, dst: int) -> List[Route]:
        """Find all routes from src to dst using BFS"""
        if src == dst:
            return [Route(
                path=[src],
                cost=0.0,
                metrics=RouteMetrics(
                    path_hops=0,
                    total_latency_ns=0.0,
                    link_congestion=[],
                ),
                algorithm=self.routing_algorithm,
            )]

        routes: List[Route] = []
        visited: Dict[int, List[Tuple[float, Tuple[int, ...]]]] = {}

        # Priority queue: (cost, counter, node, path)
        counter = 0
        pq: List[Tuple[float, int, int, Tuple[int, ...]]] = [(0.0, counter, src, (src,))]
        counter += 1

        while pq and len(routes) < 4:  # Cap at 4 alternate routes
            cost, _, curr, path = heapq.heappop(pq)

            if curr == dst:
                path_list = list(path)
                metrics = self.network.calculate_route_metrics(src, dst)
                routes.append(Route(
                    path=path_list,
                    cost=cost,
                    metrics=metrics,
                    algorithm=self.routing_algorithm,
                ))
                continue

            # Explore neighbors
            for (u, v), link in self.network.links.items():
                if u == curr:
                    next_node = v
                    if next_node not in path:
                        new_path = path + (next_node,)
                        link_cost = self._link_cost(link, cost)
                        heapq.heappush(pq, (link_cost, counter, next_node, new_path))
                        counter += 1

        # Sort by cost
        routes.sort(key=lambda r: r.cost)
        return routes

    def _link_cost(self, link, base_cost: float) -> float:
        """Calculate link cost with congestion awareness"""
        if self.routing_algorithm == RoutingAlgorithm.CONGESTION_AWARE:
            # Higher utilization = higher cost
            utilization_factor = 1.0 + link.utilization * 10.0
            return base_cost + link.latency_ns * utilization_factor
        elif self.routing_algorithm == RoutingAlgorithm.ADAPTIVE:
            # Dynamic cost based on congestion
            congestion_penalty = link.utilization * 5.0
            return base_cost + link.latency_ns + congestion_penalty
        else:
            return base_cost + link.latency_ns

    def route(self, src: int, dst: int, packet_type: PacketType = PacketType.DATA) -> Route:
        """Route a packet from src to dst

        Returns the selected route based on the routing algorithm.
        """
        self.routes_computed += 1

        if src == dst:
            return Route(
                path=[src],
                cost=0.0,
                metrics=RouteMetrics(path_hops=0, total_latency_ns=0.0, link_congestion=[]),
                algorithm=self.routing_algorithm,
            )

        routes = self.routing_tables.get(src, {}).get(dst, [])
        if not routes:
            # Fallback: compute single path
            path = self.network.get_hops(src, dst)
            metrics = self.network.calculate_route_metrics(src, dst)
            route = Route(
                path=path,
                cost=sum(self.network.links.get((path[i], path[i+1]), link or type('', (), {'latency_ns': 1.0})()).latency_ns
                        for i in range(len(path)-1) for link in [self.network.links.get((path[i], path[i+1]))]),
                metrics=metrics,
                algorithm=self.routing_algorithm,
            )
            routes = [route]

        # Select route based on algorithm
        if self.routing_algorithm == RoutingAlgorithm.MINIMAL:
            selected = routes[0] if routes else None
        elif self.routing_algorithm == RoutingAlgorithm.CONGESTION_AWARE:
            selected = self._select_congestion_aware(routes)
        elif self.routing_algorithm == RoutingAlgorithm.ECMP:
            selected = self._select_ecmp(routes)
        else:
            selected = routes[0] if routes else None

        if selected:
            route_key = f"{src}->{dst}"
            self.routes_used[route_key] = self.routes_used.get(route_key, 0) + 1

        return selected

    def _select_congestion_aware(self, routes: List[Route]) -> Optional[Route]:
        """Select route with lowest congestion"""
        if not routes:
            return None
        return min(routes, key=lambda r: max(r.metrics.link_congestion) if r.metrics.link_congestion else 0)

    def _select_ecmp(self, routes: List[Route]) -> Optional[Route]:
        """Equal-cost multipath: randomly select among routes with similar cost"""
        if not routes:
            return None

        if len(routes) == 1:
            return routes[0]

        min_cost = routes[0].cost
        equal_cost = [r for r in routes if abs(r.cost - min_cost) < 0.01]

        import random
        return random.choice(equal_cost)

    def get_alternate_routes(self, src: int, dst: int) -> List[Route]:
        """Get all alternate routes for a source-destination pair"""
        if not self.enable_alternate_routes:
            route = self.route(src, dst)
            return [route] if route else []

        return self.routing_tables.get(src, {}).get(dst, [])

    def update_link_congestion(self, src: int, dst: int, delta: float):
        """Update link congestion (call after packet transmission)"""
        link = self.network.links.get((src, dst))
        if link:
            link.utilization = max(0.0, min(1.0, link.utilization + delta))

    def get_stats(self) -> Dict:
        """Get router statistics"""
        return {
            'routes_computed': self.routes_computed,
            'routes_used': dict(self.routes_used),
            'routing_algorithm': self.routing_algorithm.value,
            'alternate_routes_enabled': self.enable_alternate_routes,
            'network_stats': self.network.get_stats(),
        }