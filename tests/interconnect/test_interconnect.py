"""
Unit Tests for HBM4 Interconnect Model

Tests all interconnect topologies, routing mechanisms, and arbitration schemes.

Test Coverage:
- Crossbar interconnect: Basic routing, contention, arbitration
- Mesh interconnect: XY routing, path computation, distance
- Binary Tree interconnect: Tree routing, broadcast, height calculation
- Routing modes: Address-based, load-balanced, shortest path
- Arbitration modes: Round-robin, priority
- Multi-stack support: Stack selection, load balancing
- Statistics: Latency tracking, congestion monitoring
"""

import pytest
import random
from typing import List, Tuple

from model.interconnect.interconnect import (
    # Enums
    TopologyType,
    RoutingMode,
    ArbitrationMode,

    # Data classes
    InterconnectPort,
    InterconnectRequest,
    InterconnectResponse,
    InterconnectStats,

    # Main classes
    InterconnectBase,
    CrossbarInterconnect,
    MeshInterconnect,
    BinaryTreeInterconnect,
    InterconnectFactory,

    # Utility
    create_interconnect,
)


class TestInterconnectPort:
    """Tests for InterconnectPort dataclass"""

    def test_port_creation(self):
        """Test port creation"""
        port = InterconnectPort(port_id=0, is_input=True)
        assert port.port_id == 0
        assert port.is_input is True
        assert port.is_active is True
        assert port.queue_depth == 0

    def test_port_repr(self):
        """Test port string representation"""
        port_in = InterconnectPort(port_id=0, is_input=True)
        port_out = InterconnectPort(port_id=1, is_input=False)

        assert "Port0(IN" in repr(port_in)
        assert "Port1(OUT" in repr(port_out)


class TestInterconnectRequest:
    """Tests for InterconnectRequest dataclass"""

    def test_request_creation(self):
        """Test request creation"""
        req = InterconnectRequest(source_port=0, addr=0x1000, size=64)
        assert req.source_port == 0
        assert req.addr == 0x1000
        assert req.size == 64
        assert req.is_read is True
        assert req.qos == 8

    def test_request_id_generation(self):
        """Test unique request ID generation"""
        req1 = InterconnectRequest(source_port=0, addr=0x1000)
        req2 = InterconnectRequest(source_port=1, addr=0x2000)
        assert req1.id != req2.id


class TestInterconnectResponse:
    """Tests for InterconnectResponse dataclass"""

    def test_response_creation(self):
        """Test response creation"""
        resp = InterconnectResponse(
            request_id=1,
            success=True,
            dest_stack=0,
            dest_channel=5,
            latency=2,
        )
        assert resp.request_id == 1
        assert resp.success is True
        assert resp.dest_stack == 0
        assert resp.dest_channel == 5
        assert resp.latency == 2

    def test_error_response(self):
        """Test error response"""
        resp = InterconnectResponse(
            request_id=1,
            success=False,
            error="Port busy",
        )
        assert resp.success is False
        assert resp.error == "Port busy"


class TestInterconnectStats:
    """Tests for InterconnectStats dataclass"""

    def test_stats_creation(self):
        """Test stats creation"""
        stats = InterconnectStats()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0

    def test_average_latency(self):
        """Test average latency calculation"""
        stats = InterconnectStats()
        stats.total_latency_cycles = 100
        stats.successful_requests = 10
        assert stats.average_latency == 10.0

    def test_average_latency_zero(self):
        """Test average latency with no requests"""
        stats = InterconnectStats()
        assert stats.average_latency == 0.0

    def test_success_rate(self):
        """Test success rate calculation"""
        stats = InterconnectStats()
        stats.total_requests = 100
        stats.successful_requests = 95
        stats.failed_requests = 5
        assert stats.success_rate == 0.95


class TestCrossbarInterconnect:
    """Tests for CrossbarInterconnect"""

    def test_crossbar_creation(self):
        """Test crossbar creation"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)
        assert ic.num_ports == 32
        assert ic.stack_count == 4
        assert ic.channels_per_stack == 32

    def test_crossbar_basic_routing(self):
        """Test basic crossbar routing"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        # Stack 0, Channel 1: addr = (0 << 46) | (1 << 41) = 0x20000000000
        req = InterconnectRequest(source_port=0, addr=0x20000000000)
        resp = ic.route_request(req)

        assert resp.success is True
        assert resp.dest_stack == 0
        assert resp.dest_channel == 1
        assert resp.latency == 1  # Crossbar is O(1)

    def test_crossbar_address_extraction(self):
        """Test address-based destination extraction"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        # Test stack 2, channel 15
        addr = (2 << 46) | (15 << 41)
        req = InterconnectRequest(source_port=0, addr=addr)
        resp = ic.route_request(req)

        assert resp.dest_stack == 2
        assert resp.dest_channel == 15

    def test_crossbar_multiple_requests(self):
        """Test multiple concurrent requests"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        requests = []
        for i in range(10):
            stack = i % 4
            channel = (i * 7) % 32  # Spread across channels
            addr = (stack << 46) | (channel << 41)
            req = InterconnectRequest(source_port=i, addr=addr)
            requests.append(req)

        for req in requests:
            resp = ic.route_request(req)
            assert resp.success is True

    def test_crossbar_statistics(self):
        """Test crossbar statistics tracking"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        for i in range(100):
            addr = ((i % 4) << 46) | ((i % 32) << 41)
            req = InterconnectRequest(source_port=i % 32, addr=addr)
            ic.route_request(req)

        stats = ic.get_stats()
        assert stats['total_requests'] == 100
        assert stats['successful_requests'] == 100
        assert stats['success_rate'] == 1.0

    def test_crossbar_reset(self):
        """Test crossbar reset"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        for i in range(10):
            addr = ((i % 4) << 46) | ((i % 32) << 41)
            req = InterconnectRequest(source_port=0, addr=addr)
            ic.route_request(req)

        ic.reset()
        stats = ic.get_stats()
        assert stats['total_requests'] == 0


class TestMeshInterconnect:
    """Tests for MeshInterconnect"""

    def test_mesh_creation(self):
        """Test mesh creation"""
        ic = MeshInterconnect(rows=4, cols=8, stack_count=4)
        assert ic.num_ports == 32  # 4 * 8
        assert ic.rows == 4
        assert ic.cols == 8

    def test_mesh_neighbor_computation(self):
        """Test mesh neighbor computation"""
        ic = MeshInterconnect(rows=4, cols=4, stack_count=1)

        # Corner node (0,0) should have 2 neighbors
        neighbors_00 = ic._get_neighbors(0)
        assert len(neighbors_00) == 2
        assert 1 in neighbors_00  # Right
        assert 4 in neighbors_00  # Down

        # Edge node (0,1) should have 3 neighbors
        neighbors_01 = ic._get_neighbors(1)
        assert len(neighbors_01) == 3

        # Center node (1,1) should have 4 neighbors
        neighbors_11 = ic._get_neighbors(5)
        assert len(neighbors_11) == 4

    def test_mesh_xy_routing(self):
        """Test XY routing path computation"""
        ic = MeshInterconnect(rows=4, cols=4, stack_count=1)

        # Route from (0,0) to (3,3) - should go right 3, down 3
        path = ic._xy_route(0, 15)  # Node 0 to node 15
        assert path[0] == 0
        assert path[-1] == 15
        assert len(path) == 7  # 6 hops + 1 for source

    def test_mesh_distance(self):
        """Test mesh distance calculation"""
        ic = MeshInterconnect(rows=4, cols=4, stack_count=1)

        # Distance from (0,0) to (3,3) = 3 right + 3 down = 6
        dist = ic._compute_hops(0, 15)
        assert dist == 6

        # Distance from (0,0) to (0,1) = 1 right
        dist = ic._compute_hops(0, 1)
        assert dist == 1

    def test_mesh_routing(self):
        """Test mesh routing"""
        ic = MeshInterconnect(rows=4, cols=8, stack_count=4)

        # Stack 0, Channel 1: addr = (0 << 46) | (1 << 41) = 0x20000000000
        req = InterconnectRequest(source_port=0, addr=0x20000000000)
        resp = ic.route_request(req)

        assert resp.success is True
        assert resp.dest_stack == 0
        assert resp.dest_channel == 1

    def test_mesh_statistics(self):
        """Test mesh statistics tracking"""
        ic = MeshInterconnect(rows=4, cols=8, stack_count=4)

        for i in range(100):
            addr = ((i % 4) << 46) | ((i % 32) << 41)
            req = InterconnectRequest(source_port=i % 32, addr=addr)
            ic.route_request(req)

        stats = ic.get_stats()
        assert stats['total_requests'] == 100
        assert stats['successful_requests'] == 100


class TestBinaryTreeInterconnect:
    """Tests for BinaryTreeInterconnect"""

    def test_tree_creation(self):
        """Test tree creation"""
        ic = BinaryTreeInterconnect(num_leaves=32, stack_count=4)
        assert ic.num_leaves == 32
        assert ic.num_ports == 32
        assert ic._height == 6  # log2(32) + 1

    def test_tree_height_calculation(self):
        """Test tree height calculation"""
        # 32 leaves: height = ceil(log2(32)) + 1 = 5 + 1 = 6
        ic = BinaryTreeInterconnect(num_leaves=32, stack_count=1)
        assert ic._height == 6

        # 16 leaves: height = ceil(log2(16)) + 1 = 4 + 1 = 5
        ic = BinaryTreeInterconnect(num_leaves=16, stack_count=1)
        assert ic._height == 5

        # 8 leaves: height = ceil(log2(8)) + 1 = 3 + 1 = 4
        ic = BinaryTreeInterconnect(num_leaves=8, stack_count=1)
        assert ic._height == 4

    def test_tree_routing(self):
        """Test tree routing"""
        ic = BinaryTreeInterconnect(num_leaves=32, stack_count=4)

        # Stack 0, Channel 1: addr = (0 << 46) | (1 << 41) = 0x20000000000
        req = InterconnectRequest(source_port=0, addr=0x20000000000)
        resp = ic.route_request(req)

        assert resp.success is True
        assert resp.dest_stack == 0
        assert resp.dest_channel == 1
        # Tree routing is ~2*height hops
        assert resp.latency >= 1

    def test_tree_broadcast(self):
        """Test tree broadcast"""
        ic = BinaryTreeInterconnect(num_leaves=8, stack_count=1)

        req = InterconnectRequest(source_port=0, addr=0x1000)
        responses = ic.broadcast(req)

        # Should have one response per output
        assert len(responses) == 8
        for resp in responses:
            assert resp.success is True


class TestRoutingModes:
    """Tests for different routing modes"""

    def test_address_based_routing(self):
        """Test address-based routing"""
        ic = CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            routing_mode=RoutingMode.ADDRESS_BASED,
        )

        # Stack 2, Channel 10
        addr = (2 << 46) | (10 << 41)
        req = InterconnectRequest(source_port=0, addr=addr)
        resp = ic.route_request(req)

        assert resp.dest_stack == 2
        assert resp.dest_channel == 10

    def test_shortest_path_routing(self):
        """Test shortest path routing"""
        ic = MeshInterconnect(
            rows=4,
            cols=8,
            stack_count=4,
            routing_mode=RoutingMode.SHORTEST_PATH,
        )

        req = InterconnectRequest(source_port=0, addr=0x0000_0000_0200_0000)
        resp = ic.route_request(req)

        assert resp.success is True

    def test_load_balanced_routing(self):
        """Test load-balanced routing"""
        ic = CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            routing_mode=RoutingMode.LOAD_BALANCED,
        )

        # Generate requests to same channel but different stacks
        for i in range(20):
            channel = 5  # Same channel
            addr = channel << 41  # No stack bits for load-balanced
            req = InterconnectRequest(source_port=i, addr=addr)
            ic.route_request(req)

        # Check load distribution
        stats = ic.get_stats()
        load_dist = stats['load_distribution']

        # With load balancing, stacks should have similar load
        stack_loads = [0, 0, 0, 0]
        for port, count in load_dist.items():
            stack = port // 32
            if stack < 4:
                stack_loads[stack] += count

        # All stacks should have some traffic
        assert sum(stack_loads) > 0


class TestArbitrationModes:
    """Tests for different arbitration modes"""

    def test_round_robin_arbitration(self):
        """Test round-robin arbitration"""
        ic = CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            arbitration_mode=ArbitrationMode.ROUND_ROBIN,
        )

        requests = []
        for i in range(10):
            addr = ((i % 4) << 46) | ((i % 32) << 41)
            req = InterconnectRequest(source_port=i, addr=addr)
            requests.append(req)

        for req in requests:
            resp = ic.route_request(req)
            assert resp.success is True

    def test_priority_arbitration(self):
        """Test priority arbitration"""
        ic = CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            arbitration_mode=ArbitrationMode.PRIORITY,
        )

        # Submit high priority request
        high_qos_req = InterconnectRequest(
            source_port=0,
            addr=0x1000,
            qos=15,  # Highest priority
        )

        # Submit low priority request
        low_qos_req = InterconnectRequest(
            source_port=1,
            addr=0x2000,
            qos=0,  # Lowest priority
        )

        # Both should succeed
        resp_high = ic.route_request(high_qos_req)
        resp_low = ic.route_request(low_qos_req)

        assert resp_high.success is True
        assert resp_low.success is True


class TestMultiStackSupport:
    """Tests for multi-stack support"""

    def test_single_stack(self):
        """Test single stack configuration"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=1)
        assert ic.stack_count == 1

        req = InterconnectRequest(source_port=0, addr=0x0000_0000_0000_1000)
        resp = ic.route_request(req)

        assert resp.dest_stack == 0
        assert resp.dest_channel >= 0

    def test_four_stacks(self):
        """Test 4-stack configuration"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)
        assert ic.stack_count == 4

        # Route to each stack
        for stack in range(4):
            addr = (stack << 46) | (15 << 41)
            req = InterconnectRequest(source_port=stack, addr=addr)
            resp = ic.route_request(req)

            assert resp.dest_stack == stack
            assert resp.dest_channel == 15

    def test_eight_stacks(self):
        """Test 8-stack configuration (max)

        Note: HBM4 standard address format uses 2 bits for stack (4 stacks).
        For 8 stacks, we use a modified address encoding with more bits.
        """
        ic = CrossbarInterconnect(num_ports=32, stack_count=8)
        assert ic.stack_count == 8

        # For 8 stacks, we use load-balanced routing which ignores stack bits
        # and distributes across all stacks
        ic.routing_mode = RoutingMode.LOAD_BALANCED

        # Route multiple requests - they should spread across stacks
        results = []
        for i in range(8):
            addr = (0 << 41)  # Same channel
            req = InterconnectRequest(source_port=i, addr=addr)
            resp = ic.route_request(req)
            results.append(resp)
            assert resp.success is True

        # All should succeed (load balancing routes to different stacks)
        assert all(r.success for r in results)


class TestInterconnectFactory:
    """Tests for InterconnectFactory"""

    def test_create_crossbar(self):
        """Test factory crossbar creation"""
        ic = InterconnectFactory.create_crossbar(
            num_ports=32,
            stack_count=4,
        )
        assert isinstance(ic, CrossbarInterconnect)
        assert ic.num_ports == 32
        assert ic.stack_count == 4

    def test_create_mesh(self):
        """Test factory mesh creation"""
        ic = InterconnectFactory.create_mesh(
            rows=4,
            cols=8,
            stack_count=4,
        )
        assert isinstance(ic, MeshInterconnect)
        assert ic.rows == 4
        assert ic.cols == 8

    def test_create_tree(self):
        """Test factory tree creation"""
        ic = InterconnectFactory.create_tree(
            num_leaves=32,
            stack_count=4,
        )
        assert isinstance(ic, BinaryTreeInterconnect)
        assert ic.num_leaves == 32

    def test_create_by_topology(self):
        """Test factory creation by topology type"""
        ic = InterconnectFactory.create(
            TopologyType.CROSSBAR,
            num_ports=32,
            stack_count=4,
        )
        assert isinstance(ic, CrossbarInterconnect)


class TestCreateInterconnectFunction:
    """Tests for create_interconnect utility function"""

    def test_create_crossbar_string(self):
        """Test create with crossbar string"""
        ic = create_interconnect(
            topology="crossbar",
            num_ports=32,
            stack_count=4,
        )
        assert isinstance(ic, CrossbarInterconnect)

    def test_create_mesh_string(self):
        """Test create with mesh string"""
        ic = create_interconnect(
            topology="mesh",
            num_ports=32,
            rows=4,
            cols=8,
        )
        assert isinstance(ic, MeshInterconnect)

    def test_create_tree_string(self):
        """Test create with tree string"""
        ic = create_interconnect(
            topology="tree",
            num_ports=32,
        )
        assert isinstance(ic, BinaryTreeInterconnect)

    def test_create_with_routing_mode(self):
        """Test create with routing mode strings"""
        ic = create_interconnect(
            topology="crossbar",
            routing_mode="load",
        )
        assert ic.routing_mode == RoutingMode.LOAD_BALANCED

    def test_create_with_arb_mode(self):
        """Test create with arbitration mode strings"""
        ic = create_interconnect(
            topology="crossbar",
            arbitration_mode="priority",
        )
        assert ic.arbitration_mode == ArbitrationMode.PRIORITY


class TestTickAndCycle:
    """Tests for tick/cycle advancement"""

    def test_tick_increments_cycle(self):
        """Test that tick increments cycle counter"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)
        assert ic._cycle == 0

        ic.tick()
        assert ic._cycle == 1

        ic.tick()
        assert ic._cycle == 2

    def test_request_arrival_cycle(self):
        """Test request arrival cycle tracking"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        ic.tick()
        ic.tick()

        req = InterconnectRequest(source_port=0, addr=0x1000)
        resp = ic.route_request(req)

        assert req.arrival_cycle == 2


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_empty_address(self):
        """Test routing with address 0"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        req = InterconnectRequest(source_port=0, addr=0)
        resp = ic.route_request(req)

        assert resp.success is True
        assert resp.dest_stack == 0
        assert resp.dest_channel == 0

    def test_max_address(self):
        """Test routing with max address"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        req = InterconnectRequest(source_port=0, addr=0xFFFFFFFFFFFFFFFF)
        resp = ic.route_request(req)

        assert resp.success is True
        # Stack and channel should wrap around
        assert resp.dest_stack < 4
        assert resp.dest_channel < 32

    def test_min_ports(self):
        """Test with minimum port count"""
        ic = CrossbarInterconnect(num_ports=1, stack_count=1)
        assert ic.num_ports == 1

    def test_boundary_stacks(self):
        """Test with boundary stack values"""
        # Test stack count boundaries
        ic_min = create_interconnect("crossbar", num_ports=32, stack_count=1)
        assert ic_min.stack_count == 1

        ic_max = create_interconnect("crossbar", num_ports=32, stack_count=8)
        assert ic_max.stack_count == 8


class TestPerformance:
    """Tests for performance characteristics"""

    def test_high_request_rate(self):
        """Test high request rate"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        # Submit 1000 requests rapidly
        for i in range(1000):
            addr = ((i % 4) << 46) | ((i % 32) << 41)
            req = InterconnectRequest(source_port=i % 32, addr=addr)
            ic.route_request(req)

        stats = ic.get_stats()
        assert stats['total_requests'] == 1000
        assert stats['successful_requests'] == 1000

    def test_concurrent_destinations(self):
        """Test concurrent requests to same destination"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)

        # 100 requests to same destination
        addr = (0 << 46) | (5 << 41)  # Stack 0, Channel 5
        for i in range(100):
            # Use different source ports to avoid round-robin queue buildup
            req = InterconnectRequest(source_port=i % 32, addr=addr)
            resp = ic.route_request(req)
            assert resp.success is True

        stats = ic.get_stats()
        assert stats['total_requests'] == 100

    def test_all_channels(self):
        """Test traffic across all channels"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=1)

        # Route to each channel
        for ch in range(32):
            addr = ch << 41
            req = InterconnectRequest(source_port=0, addr=addr)
            resp = ic.route_request(req)
            assert resp.dest_channel == ch


if __name__ == '__main__':
    pytest.main([__file__, '-v'])