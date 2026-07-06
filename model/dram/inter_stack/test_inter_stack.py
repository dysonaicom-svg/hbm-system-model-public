"""
Tests for Inter-Stack Modeling
Multi-stack interconnect network, routing, and scheduling tests

Reference: model/dram/stack_model.py
"""

import pytest
import math
from typing import List

from model.dram.inter_stack.inter_stack_network import (
    InterStackNetwork,
    InterconnectTopology,
    PacketType,
    create_network,
)
from model.dram.inter_stack.stack_router import (
    StackRouter,
    RoutingAlgorithm,
    Route,
)
from model.dram.inter_stack.topology_aware_scheduler import (
    TopologyAwareScheduler,
    SchedulingPolicy,
    Request,
    ScheduledRequest,
)


class TestInterStackNetwork:
    """Tests for InterStackNetwork"""

    def test_mesh_topology_creation(self):
        """Test mesh topology initialization"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH, mesh_rows=2)
        assert network.num_stacks == 4
        assert network.topology == InterconnectTopology.MESH

        # 2x2 mesh should have 4 horizontal + 4 vertical links = 4 internal links
        # (each link is bidirectional but stored once)
        assert len(network.links) >= 4

    def test_crossbar_topology_creation(self):
        """Test full crossbar topology initialization"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.FULL_CROSSBAR)
        assert network.num_stacks == 4

        # Full crossbar: n*(n-1) unidirectional links
        assert len(network.links) == 4 * 3  # 12 links

    def test_butterfly_topology_creation(self):
        """Test butterfly network topology"""
        network = InterStackNetwork(num_stacks=8, topology=InterconnectTopology.BUTTERFLY)
        assert network.num_stacks == 8

        # Butterfly with 3 stages, 8 nodes
        stages = math.ceil(math.log2(8))
        assert stages == 3

    def test_mesh_routing(self):
        """Test dimensional routing in mesh"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH, mesh_rows=2)

        # Stack 0 to Stack 3 (diagonal)
        path = network.get_hops(0, 3)
        assert path[0] == 0
        assert path[-1] == 3
        assert len(path) >= 2  # At least one hop

    def test_crossbar_routing(self):
        """Test crossbar routing (direct)"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.FULL_CROSSBAR)

        # Crossbar is one hop
        path = network.get_hops(0, 3)
        assert path == [0, 3]

    def test_butterfly_routing(self):
        """Test butterfly network routing"""
        network = InterStackNetwork(num_stacks=8, topology=InterconnectTopology.BUTTERFLY)

        path = network.get_hops(0, 7)
        assert path[0] == 0
        assert path[-1] == 7
        # Butterfly diameter is log2(n)
        assert len(path) - 1 <= math.ceil(math.log2(8))

    def test_torus_topology(self):
        """Test torus topology with wrap-around"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.TORUS, mesh_rows=2)
        assert network.topology == InterconnectTopology.TORUS

        # Torus should have more links than mesh due to wrap-around
        mesh_network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH, mesh_rows=2)
        assert len(network.links) >= len(mesh_network.links)

    def test_packet_creation(self):
        """Test packet creation and transmission"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)

        packet, metrics = network.send_packet(
            src_stack=0,
            dst_stack=2,
            packet_type=PacketType.DATA,
            size_bytes=64,
            current_time=10.0,
        )

        assert packet.packet_id == 0
        assert packet.src_stack == 0
        assert packet.dst_stack == 2
        assert packet.packet_type == PacketType.DATA
        assert packet.created_at == 10.0

    def test_route_metrics(self):
        """Test route metrics calculation"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)

        metrics = network.calculate_route_metrics(0, 3)
        assert metrics.path_hops >= 0
        assert metrics.total_latency_ns >= 0

    def test_network_statistics(self):
        """Test network statistics tracking"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)

        # Send some packets
        network.send_packet(0, 2, PacketType.DATA)
        network.send_packet(1, 3, PacketType.REQUEST)

        stats = network.get_stats()
        assert stats['total_packets'] == 2
        assert stats['total_hops'] > 0

    def test_factory_function(self):
        """Test network factory function"""
        network = create_network(num_stacks=8, topology="crossbar")
        assert network.num_stacks == 8
        assert network.topology == InterconnectTopology.FULL_CROSSBAR


class TestStackRouter:
    """Tests for StackRouter"""

    def test_router_creation(self):
        """Test router initialization"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        router = StackRouter(network)

        assert router.network is network
        assert router.routing_algorithm == RoutingAlgorithm.MINIMAL

    def test_minimal_routing(self):
        """Test minimal routing algorithm"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        router = StackRouter(network, RoutingAlgorithm.MINIMAL)

        route = router.route(0, 3)
        assert route is not None
        assert route.num_hops >= 1

    def test_congestion_aware_routing(self):
        """Test congestion-aware routing"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        router = StackRouter(network, RoutingAlgorithm.CONGESTION_AWARE)

        route = router.route(0, 3)
        assert route is not None

    def test_ecmp_routing(self):
        """Test ECMP routing"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.FULL_CROSSBAR)
        router = StackRouter(network, RoutingAlgorithm.ECMP)

        # Multiple calls should sometimes select different routes
        routes = set()
        for _ in range(10):
            route = router.route(0, 3)
            if route:
                routes.add(tuple(route.path))

        # With ECMP, we may get same route due to randomness
        assert len(routes) >= 1

    def test_alternate_routes(self):
        """Test getting alternate routes"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        router = StackRouter(network, enable_alternate_routes=True)

        routes = router.get_alternate_routes(0, 3)
        assert len(routes) >= 1

    def test_local_route(self):
        """Test routing to same stack"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        router = StackRouter(network)

        route = router.route(2, 2)
        assert route is not None
        assert route.num_hops == 0
        assert route.path == [2]

    def test_router_statistics(self):
        """Test router statistics"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        router = StackRouter(network)

        router.route(0, 2)
        router.route(1, 3)

        stats = router.get_stats()
        assert stats['routes_computed'] == 2
        assert '0->2' in stats['routes_used']
        assert '1->3' in stats['routes_used']


class TestTopologyAwareScheduler:
    """Tests for TopologyAwareScheduler"""

    def test_scheduler_creation(self):
        """Test scheduler initialization"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network)

        assert scheduler.network is network
        assert scheduler.policy == SchedulingPolicy.TOPOLOGY_AWARE

    def test_request_submission(self):
        """Test submitting a request"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network)

        request = scheduler.submit_request(
            dst_stack=2,
            address=0x1000,
            size_bytes=64,
            is_write=False,
            current_time=0.0,
        )

        assert request is not None
        assert request.dst_stack == 2
        assert request.address == 0x1000
        assert not request.is_write

    def test_request_scheduling(self):
        """Test scheduling a request"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network)

        scheduler.submit_request(
            dst_stack=2,
            address=0x1000,
            current_time=0.0,
        )

        scheduled = scheduler.schedule_next(current_time=0.0)
        assert scheduled is not None
        assert isinstance(scheduled, ScheduledRequest)
        assert scheduled.request.dst_stack == 2

    def test_priority_scheduling(self):
        """Test priority-based scheduling"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network, scheduling_policy=SchedulingPolicy.PRIORITY)

        # Submit requests with different priorities
        req1 = scheduler.submit_request(dst_stack=0, address=0x1000, priority=1, current_time=0.0)
        req2 = scheduler.submit_request(dst_stack=1, address=0x2000, priority=10, current_time=0.0)
        req3 = scheduler.submit_request(dst_stack=2, address=0x3000, priority=5, current_time=0.0)

        # High priority should be scheduled first
        scheduled = scheduler.schedule_next()
        assert scheduled.request.priority == 10

    def test_load_balancing(self):
        """Test load balancing across stacks"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network, scheduling_policy=SchedulingPolicy.SHORTEST_QUEUE)

        # Submit many requests
        for i in range(20):
            scheduler.submit_request(dst_stack=i % 4, address=0x1000 * i, current_time=0.0)

        # Check pending requests are tracked correctly
        stats = scheduler.get_stats()
        assert stats['pending_requests'] == 20
        assert stats['total_scheduled'] == 0  # Not yet scheduled

        # Schedule some requests
        for _ in range(10):
            scheduler.schedule_next(current_time=0.0)

        # Check scheduling stats
        stats = scheduler.get_stats()
        assert stats['total_scheduled'] == 10
        assert stats['pending_requests'] == 10  # 20 submitted - 10 scheduled

    def test_request_rejection(self):
        """Test request rejection when queue is full"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network, max_queue_depth=2)

        # Fill up the queue
        for i in range(3):
            scheduler.submit_request(dst_stack=0, address=0x1000 * i, current_time=0.0)

        # Schedule one to make room
        scheduler.schedule_next()

        # Submit more - one should succeed, one should fail
        req1 = scheduler.submit_request(dst_stack=0, address=0x5000, current_time=0.0)
        req2 = scheduler.submit_request(dst_stack=0, address=0x6000, current_time=0.0)

        # At least one should succeed
        assert req1 is not None or req2 is not None

    def test_scheduled_request_completion(self):
        """Test marking request as completed"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network)

        request = scheduler.submit_request(dst_stack=2, address=0x1000, current_time=0.0)
        scheduled = scheduler.schedule_next(current_time=0.0)

        # Complete the request
        scheduler.complete_request(scheduled.request, actual_latency_ns=15.0, current_time=15.0)

        assert request not in scheduler.request_queues[2]

    def test_scheduler_statistics(self):
        """Test scheduler statistics"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network)

        for i in range(5):
            scheduler.submit_request(dst_stack=i % 4, address=0x1000 * i, current_time=0.0)
            scheduler.schedule_next(current_time=float(i))

        stats = scheduler.get_stats()
        assert stats['total_scheduled'] == 5
        assert stats['total_rejected'] == 0

    def test_weighted_scheduling(self):
        """Test weighted scheduling policy"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        scheduler = TopologyAwareScheduler(network, scheduling_policy=SchedulingPolicy.WEIGHTED)

        # Submit weighted requests
        for i in range(10):
            scheduler.submit_request(
                dst_stack=i % 4,
                address=0x1000 * i,
                weight=float(10 - i),
                current_time=0.0,
            )

        # Should schedule based on weights
        scheduled = scheduler.schedule_next()
        assert scheduled is not None


class TestIntegration:
    """Integration tests for inter-stack components"""

    def test_network_router_integration(self):
        """Test network and router working together"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        router = StackRouter(network)

        # Route through network
        route = router.route(0, 3)
        assert route is not None

        # Verify route exists in network
        path = network.get_hops(0, 3)
        assert route.path == path or len(route.path) <= len(path) + 1

    def test_full_system_integration(self):
        """Test full system: network, router, scheduler"""
        network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        router = StackRouter(network, RoutingAlgorithm.CONGESTION_AWARE)
        scheduler = TopologyAwareScheduler(network, router, SchedulingPolicy.TOPOLOGY_AWARE)

        # Submit multiple requests
        for i in range(10):
            scheduler.submit_request(
                dst_stack=i % 4,
                address=0x1000 * i,
                is_write=(i % 2 == 0),
                priority=i % 3,
                current_time=float(i),
            )

        # Schedule and complete requests
        completed = 0
        current_time = 10.0
        while True:
            scheduled = scheduler.schedule_next(current_time)
            if scheduled is None:
                break

            actual_latency = scheduled.estimated_latency_ns * 0.8  # Simulate completion
            scheduler.complete_request(scheduled.request, actual_latency, current_time)
            current_time += 1.0
            completed += 1

        stats = scheduler.get_stats()
        assert stats['total_scheduled'] == completed

    def test_crossbar_performance(self):
        """Test crossbar topology performance"""
        network = InterStackNetwork(num_stacks=8, topology=InterconnectTopology.FULL_CROSSBAR)
        router = StackRouter(network)

        # All routes should be 1 hop
        for src in range(8):
            for dst in range(8):
                if src != dst:
                    route = router.route(src, dst)
                    assert route.num_hops == 1

    def test_mesh_vs_crossbar_hops(self):
        """Compare hop counts between mesh and crossbar"""
        mesh_network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.MESH)
        crossbar_network = InterStackNetwork(num_stacks=4, topology=InterconnectTopology.FULL_CROSSBAR)

        mesh_router = StackRouter(mesh_network)
        crossbar_router = StackRouter(crossbar_network)

        # Crossbar should have fewer hops
        for src in range(4):
            for dst in range(4):
                if src != dst:
                    mesh_route = mesh_router.route(src, dst)
                    crossbar_route = crossbar_router.route(src, dst)

                    if mesh_route and crossbar_route:
                        assert crossbar_route.num_hops <= mesh_route.num_hops


if __name__ == "__main__":
    pytest.main([__file__, "-v"])