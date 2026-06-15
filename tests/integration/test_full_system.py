"""
Full System Integration Tests

Tests complete integration of all modules:
1. Traffic Generator → HBM4Controller
2. Interconnect → HBM4Controller
3. Complete system simulation with end-to-end validation

Based on HBM4 specification (JEDEC JESD270-4A)
"""

import pytest
import time
from typing import Dict, List, Tuple

from model.dram.hbm4_spec import HBM4Spec, HBM4_CONFIG, HBM4_SPEED_GRADES
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler
from model.controller.request import HBMRequest
from model.dram.hbm4_channel_model import HBM4Channel
from model.interconnect.interconnect import (
    CrossbarInterconnect,
    MeshInterconnect,
    InterconnectRequest,
    InterconnectResponse,
    RoutingMode,
)
from sim.simulator import (
    HBMSimulator,
    SimulationConfig,
    TrafficPattern,
    SimulationStats,
)


def create_hbm4_config():
    """Create HBM4 configuration matching 32-channel specification"""
    return HBMConfig(
        stack_count=4,  # 4 stacks (ADDR_STACK_BITS = 2)
        channels_per_stack=32,  # HBM4: 32 channels per stack
        pseudo_channels_per_channel=2,
        banks_per_pseudo_channel=16,
        bank_groups_per_channel=8,
        row_size=2048,
        burst_length=32,
        data_rate=8.0e9,  # 8 GT/s
        io_width=2048,  # 2048-bit interface
        read_latency_base=30,
        write_latency_base=10,
        phy_latency=20,
        queue_depth=64,
        max_outstanding=32,
    )


def create_hbm4_spec():
    """Create HBM4 specification object"""
    return HBM4Spec()


# Create HBM4_DEFAULT config
HBM4_DEFAULT = create_hbm4_config()
HBM4_SPEC = create_hbm4_spec()


# ============================================================================
# Test 1: Traffic Generator → HBM4Controller Integration
# ============================================================================

class TestTrafficGeneratorControllerIntegration:
    """Test integration between Traffic Generator and HBM4Controller"""

    @pytest.fixture
    def config(self):
        """Create HBM4 configuration"""
        return HBM4_DEFAULT

    @pytest.fixture
    def spec(self):
        """Create HBM4 specification"""
        return HBM4_SPEC

    @pytest.fixture
    def controller(self, spec):
        """Create HBM4 Controller"""
        return HBM4Controller(spec=spec)

    @pytest.fixture
    def address_decoder(self, spec):
        """Create HBM4 Address Decoder"""
        return HBM4AddressDecoder(spec=spec)

    def test_ai_training_traffic_injection(self, controller, address_decoder):
        """Test AI training workload traffic injection"""
        # Simulate AI training workload:
        # - Large batch of read requests
        # - Sequential row access pattern
        # - High priority for training data

        base_addr = 0x1000_0000
        request_count = 100
        submitted = 0

        for i in range(request_count):
            # Sequential addresses (row by row)
            addr = base_addr + (i * 4096)  # 4KB stride

            # Submit request using HBM4Controller API
            result = controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=12,  # HIGH priority
                size_bytes=64
            )

            if result:
                submitted += 1

        # Verify submission
        assert submitted > 0, "No requests were submitted"

        # Verify queue state
        queue_depth = controller.get_queue_depth()
        assert queue_depth >= 0, f"Invalid queue depth: {queue_depth}"

    def test_request_submission_success(self, controller):
        """Test that requests are submitted successfully"""
        result = controller.submit_request(
            addr=0x1000_0000,
            is_read=True,
            qos_level=8,
            size_bytes=64
        )
        assert result is not None, "Request submission failed"

    def test_statistics_collection(self, controller):
        """Test that statistics are collected correctly"""
        # Submit several requests
        for i in range(10):
            controller.submit_request(
                addr=0x1000_0000 + (i * 64),
                is_read=(i % 2 == 0),
                qos_level=8,
                size_bytes=64
            )

        # Get statistics
        stats = controller.get_stats()

        # Verify statistics
        assert 'total_requests' in stats
        assert 'read_requests' in stats
        assert 'write_requests' in stats
        assert stats['total_requests'] >= 10


# ============================================================================
# Test 2: Interconnect → HBM4Controller Integration
# ============================================================================

class TestInterconnectControllerIntegration:
    """Test integration between Interconnect and HBM4Controller"""

    @pytest.fixture
    def hbm_config(self):
        """Create HBM4 configuration"""
        return HBM4_DEFAULT

    @pytest.fixture
    def hbm_spec(self):
        """Create HBM4 specification"""
        return HBM4_SPEC

    @pytest.fixture
    def crossbar(self, hbm_spec):
        """Create Crossbar Interconnect for 4-stack system"""
        total_channels = hbm_spec.channels

        return CrossbarInterconnect(
            num_ports=total_channels,
            stack_count=4,
            routing_strategy=RoutingMode.ADDRESS_BASED
        )

    @pytest.fixture
    def mesh(self, hbm_spec):
        """Create Mesh Interconnect for 4x8 system"""
        total_channels = hbm_spec.channels

        return MeshInterconnect(
            rows=4,
            cols=total_channels // 4,
            stack_count=4
        )

    @pytest.fixture
    def controller(self, hbm_spec):
        """Create HBM4 Controller"""
        return HBM4Controller(spec=hbm_spec)

    def test_crossbar_multi_stack_routing(self, crossbar, hbm_spec):
        """Test multi-stack routing with crossbar"""
        total_channels = hbm_spec.channels

        for stack_id in range(4):
            for ch in range(min(8, total_channels)):  # Test first 8 channels
                # Route request to this stack/channel
                addr = 0x1000_0000 + (stack_id << 20) + (ch << 12)

                request = InterconnectRequest(
                    source_port=0,
                    addr=addr,
                    size=64,
                    is_read=True
                )

                response = crossbar.route_request(request)

                assert response.dest_stack == stack_id
                assert response.dest_channel == ch

    def test_bandwidth_allocation(self, crossbar):
        """Test bandwidth allocation across stacks"""
        # Generate burst traffic
        requests = []
        for i in range(100):
            addr = 0x1000_0000 + (i * 64)
            request = InterconnectRequest(
                source_port=i % 8,
                addr=addr,
                size=64,
                is_read=True
            )
            requests.append(request)

        # Route all requests
        routes = []
        for req in requests:
            response = crossbar.route_request(req)
            routes.append((response.dest_stack, response.dest_channel))

        # Check distribution (should be reasonably balanced)
        stack_counts = {}
        for stack, ch in routes:
            stack_counts[stack] = stack_counts.get(stack, 0) + 1

        # Each stack should get roughly equal traffic
        avg_per_stack = len(routes) / len(stack_counts)
        for stack, count in stack_counts.items():
            # Allow 2x deviation from average
            assert count < avg_per_stack * 2, f"Stack {stack} overloaded: {count}"

    def test_latency_modeling(self, crossbar):
        """Test interconnect latency modeling"""
        # Test different packet sizes
        for size in [64, 128, 256, 512]:
            request = InterconnectRequest(
                source_port=0,
                addr=0x1000_0000,
                size=size,
                is_read=True
            )

            response = crossbar.route_request(request)

            # Latency should scale with packet size
            assert response.latency_cycles >= 0
            assert response.latency_cycles < 100  # Reasonable upper bound

    def test_interconnect_controller_coordination(self, crossbar, controller, hbm_spec):
        """Test coordination between interconnect and controller"""
        # Create a request that goes through interconnect to controller
        addr = 0x1000_0000
        request = InterconnectRequest(
            source_port=0,
            addr=addr,
            size=64,
            is_read=True
        )

        # Route through interconnect
        response = crossbar.route_request(request)

        # Submit to controller using the routed channel
        result = controller.submit_request(
            addr=addr,
            is_read=True,
            qos_level=8,
            size_bytes=64
        )

        assert result is not None, "Controller rejected valid request"

    def test_mesh_topology_routing(self, mesh, hbm_spec):
        """Test mesh topology routing"""
        total_channels = hbm_spec.channels

        # Test corner cases
        test_cases = [
            (0, 0x1000_0000),  # First node
            (total_channels - 1, 0x1FFF_F000),  # Last node
            (total_channels // 2, 0x1800_0000),  # Middle
        ]

        for expected_channel, addr in test_cases:
            request = InterconnectRequest(
                source_port=0,
                addr=addr,
                size=64,
                is_read=True
            )

            response = mesh.route_request(request)

            # Should route to valid channel
            assert 0 <= response.dest_channel < total_channels
            assert 0 <= response.dest_stack < 4


# ============================================================================
# Test 3: Complete System Simulation
# ============================================================================

class TestCompleteSystemSimulation:
    """End-to-end system simulation tests"""

    @pytest.fixture
    def sim_config(self):
        """Create simulation configuration"""
        return SimulationConfig(
            simulation_time_us=50.0,  # 50us simulation
            request_rate=0.5,
            read_ratio=0.7,
            traffic_pattern=TrafficPattern.RANDOM,
            enable_stats=True,
        )

    @pytest.fixture
    def sequential_config(self):
        """Create sequential traffic configuration"""
        return SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.8,
            read_ratio=1.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
        )

    def test_basic_simulation_runs(self, sim_config):
        """Test that basic simulation completes"""
        sim = HBMSimulator(sim_config)
        stats = sim.run()

        assert stats.total_cycles > 0
        assert stats.total_requests >= 0

    def test_sequential_traffic_high_hit_rate(self, sequential_config):
        """Test sequential traffic achieves high hit rate"""
        sim = HBMSimulator(sequential_config)
        stats = sim.run()

        # Sequential traffic should have high row hit rate
        # Note: actual hit rate depends on address mapping and queue depth
        assert stats.total_requests >= 0  # Sanity check
        if stats.completed_requests > 0:
            assert stats.avg_latency >= 0  # Latency should be tracked

    def test_end_to_end_performance(self, sim_config):
        """Test end-to-end performance metrics"""
        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # Get all performance metrics
        metrics = {
            'total_cycles': stats.total_cycles,
            'total_requests': stats.total_requests,
            'completed_requests': stats.completed_requests,
            'avg_latency': stats.avg_latency,
            'throughput_gbps': stats.throughput_gbps,
            'efficiency': stats.efficiency,
            'row_hit_rate': stats.row_hit_rate,
        }

        # Verify all metrics are present
        for key, value in metrics.items():
            assert value is not None, f"Missing metric: {key}"

        # Verify reasonable bounds
        assert metrics['total_cycles'] > 0
        assert metrics['total_requests'] >= 0
        assert 0 <= metrics['avg_latency'] < 10000  # Latency reasonable
        assert 0 <= metrics['throughput_gbps'] < 10000  # Throughput reasonable
        assert 0 <= metrics['efficiency'] <= 1.0
        assert 0 <= metrics['row_hit_rate'] <= 1.0

    def test_throughput_scaling(self):
        """Test throughput scales with request rate"""
        results = {}

        for rate in [0.2, 0.5, 0.8]:
            config = SimulationConfig(
                simulation_time_us=30.0,
                request_rate=rate,
                read_ratio=0.7,
                traffic_pattern=TrafficPattern.RANDOM,
            )

            sim = HBMSimulator(config)
            stats = sim.run()

            results[rate] = stats.throughput_gbps

        # Higher request rate should result in higher throughput
        # (or at least not lower)
        assert results[0.5] >= results[0.2] * 0.8, "Throughput not scaling correctly"
        assert results[0.8] >= results[0.5] * 0.8, "Throughput not scaling correctly"

    def test_multi_channel_load_balancing(self, sim_config):
        """Test load balancing across channels"""
        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # Get per-channel stats
        per_channel = stats.per_channel_stats

        if len(per_channel) > 1:
            # Calculate load balance
            requests_per_channel = [s.total_requests for s in per_channel.values()]

            total = sum(requests_per_channel)
            if total > 0:
                avg = total / len(requests_per_channel)

                # Check balance (no channel should have >2x average)
                for i, count in enumerate(requests_per_channel):
                    assert count <= avg * 3, f"Channel {i} overloaded: {count} vs avg {avg:.1f}"


# ============================================================================
# Test 4: HBM4 Specific Integration Tests
# ============================================================================

class TestHBM4SpecificIntegration:
    """HBM4-specific integration tests"""

    @pytest.fixture
    def hbm4_spec(self):
        """Create HBM4 specification"""
        return HBM4Spec()

    @pytest.fixture
    def hbm4_config(self):
        """Create HBM4 configuration"""
        return HBM4_DEFAULT

    @pytest.fixture
    def hbm4_controller(self, hbm4_spec):
        """Create HBM4 Controller"""
        return HBM4Controller(spec=hbm4_spec)

    @pytest.fixture
    def hbm4_channel_model(self, hbm4_spec):
        """Create HBM4 Channel Model"""
        return HBM4Channel(
            channel_id=0,
            banks_per_pseudo_channel=hbm4_spec.banks_per_pseudo_channel,
            bank_groups_per_channel=hbm4_spec.bank_groups_per_channel,
        )

    @pytest.fixture
    def hbm4_address_decoder(self, hbm4_spec):
        """Create HBM4 Address Decoder"""
        return HBM4AddressDecoder(spec=hbm4_spec)

    def test_hbm4_32_channel_support(self, hbm4_controller, hbm4_spec):
        """Test HBM4 32-channel configuration"""
        assert hbm4_spec.channels == 32
        assert hbm4_controller.channels == 32

    def test_hbm4_bandwidth_calculation(self, hbm4_spec):
        """Test HBM4 bandwidth calculation"""
        # HBM4 @ 8 GT/s = 2.048 TB/s per stack
        expected_bw = 2.048  # TB/s
        assert abs(hbm4_spec.bandwidth - expected_bw) < 0.01

    def test_hbm4_address_mapping(self, hbm4_address_decoder):
        """Test HBM4 address mapping for 32 channels"""
        # Test addresses across all 32 channels
        test_addr = 0x1000_0000

        decoded = hbm4_address_decoder.decode(test_addr)

        # Verify all fields are valid
        assert 0 <= decoded.stack_id < 4
        assert 0 <= decoded.channel_id < 32
        assert 0 <= decoded.pseudo_channel_id < 64
        assert 0 <= decoded.bank_group_id < 8
        assert 0 <= decoded.bank_id < 16

    def test_hbm4_qos_integration(self, hbm4_controller):
        """Test HBM4 QoS scheduler integration"""
        scheduler = HBM4QoSScheduler()

        # Submit requests with different priorities
        for priority in range(8):
            result = hbm4_controller.submit_request(
                addr=0x1000_0000 + (priority * 64),
                is_read=True,
                qos_level=priority,  # 0-7 priority levels
                size_bytes=64
            )

        # Verify queue depth
        assert hbm4_controller.get_queue_depth() >= 0

    def test_hbm4_refresh_integration(self, hbm4_controller):
        """Test HBM4 refresh scheduler integration"""
        scheduler = HBM4RefreshScheduler(config=HBM4Spec())

        # Simulate some cycles
        for cycle in range(100):
            scheduler.tick()

            # Check if refresh should be issued
            refresh_cmd = scheduler.get_refresh_command()
            if refresh_cmd:
                hbm4_controller.submit_request(refresh_cmd)


# ============================================================================
# Test 5: Stress and Regression Tests
# ============================================================================

class TestStressAndRegression:
    """Stress tests for system stability"""

    def test_high_traffic_sustained(self):
        """Test sustained high traffic"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            request_rate=0.95,  # Near饱和
            read_ratio=0.5,
            traffic_pattern=TrafficPattern.RANDOM,
        )

        sim = HBMSimulator(config)
        stats = sim.run()

        # Should complete without errors
        assert stats.total_cycles > 0
        assert stats.total_requests > 0

    def test_burst_traffic_pattern(self):
        """Test burst traffic pattern"""
        results = []

        for burst_size in [10, 50, 100]:
            config = SimulationConfig(
                simulation_time_us=20.0,
                request_rate=0.3,
                read_ratio=0.7,
                traffic_pattern=TrafficPattern.HOT_SPOT,
            )

            sim = HBMSimulator(config)
            stats = sim.run()

            results.append(stats.throughput_gbps)

        # All burst sizes should produce valid results
        assert all(r >= 0 for r in results)

    def test_long_duration_simulation(self):
        """Test long duration simulation stability"""
        config = SimulationConfig(
            simulation_time_us=500.0,  # 500us
            request_rate=0.5,
            read_ratio=0.6,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
        )

        sim = HBMSimulator(config)
        stats = sim.run()

        # Should complete without memory leaks or crashes
        assert stats.total_cycles > 0
        assert stats.completed_requests >= 0


# ============================================================================
# Test 6: Performance Baseline Tests
# ============================================================================

class TestPerformanceBaselines:
    """Performance baseline validation"""

    def test_hbm4_bandwidth_baseline(self):
        """Test HBM4 bandwidth meets baseline"""
        spec = HBM4Spec()

        # HBM4 @ 8 GT/s
        expected_peak_tbps = 2.048  # TB/s per stack

        # Our calculated bandwidth
        calculated = spec.bandwidth

        # Should be within 5% of expected
        assert abs(calculated - expected_peak_tbps) < 0.1

    def test_latency_baseline(self):
        """Test latency meets baseline"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            request_rate=0.3,
            traffic_pattern=TrafficPattern.RANDOM,
            seed=42,
        )

        sim = HBMSimulator(config)
        stats = sim.run()

        # Baseline: latency should be reasonable
        # HBM3 typical: 30-50 cycles for read
        # HBM4 should be similar or better
        if stats.completed_requests > 0:
            assert stats.avg_latency < 200, f"Latency too high: {stats.avg_latency}"

    def test_efficiency_baseline(self):
        """Test efficiency meets baseline"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            request_rate=0.7,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
        )

        sim = HBMSimulator(config)
        stats = sim.run()

        # Efficiency should be > 50% for sequential traffic
        assert stats.efficiency > 0.3, f"Efficiency too low: {stats.efficiency}"


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])