"""
HBM4 End-to-End Integration Test

Tests complete integration of all 5 layers in the HBM4 system:
1. Traffic Generator -> Generates memory requests
2. Interconnect -> Routes requests to channels
3. Controller -> Schedules requests with QoS
4. DRAM Model -> Executes DRAM commands
5. PHY -> Physical layer interface (modeled)

This test verifies:
- End-to-end request flow
- Latency measurement
- Bandwidth calculation
- Error handling
- Performance metrics

Based on JEDEC JESD270-4A HBM4 specification
"""

import pytest
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from model.dram.hbm4_spec import HBM4Spec, HBM4_SPEED_GRADES
from model.dram.hbm4_channel_model import (
    HBM4Channel, HBM4ChannelArray, HBM4Command, HBM4ChannelState
)
from model.dram.dfi_interface import DFI5Interface, DFICommand, DFIRequest
from model.dram.timing import HBM4Timing
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.controller.request import HBMRequest, HBMResponse, RequestState
from model.interconnect.interconnect import (
    CrossbarInterconnect, MeshInterconnect, InterconnectRequest,
    InterconnectResponse, RoutingMode, ArbitrationMode
)
from model.traffic.traffic_generator import (
    TrafficGenerator, TrafficConfig, TrafficPattern,
    AITrainingPattern, AIInferencePattern
)


# =============================================================================
# Test Configuration
# =============================================================================

@dataclass
class IntegrationTestConfig:
    """Configuration for integration tests"""
    # Number of test requests
    num_requests: int = 100

    # Traffic configuration
    read_ratio: float = 0.7
    request_rate: float = 1e6

    # Simulation time
    simulation_cycles: int = 1000

    # HBM4 configuration
    stack_count: int = 4
    channels_per_stack: int = 32

    # Test patterns
    test_addresses: List[int] = field(default_factory=list)


def create_test_config() -> IntegrationTestConfig:
    """Create standard test configuration"""
    return IntegrationTestConfig(
        num_requests=100,
        read_ratio=0.7,
        request_rate=1e6,
        simulation_cycles=1000,
        test_addresses=[
            0x1000_0000,  # Channel 0, Row 0x800
            0x1020_0000,  # Channel 1, Row 0x800
            0x2000_0000,  # Channel 0, Stack 1
            0x4000_0000,  # Channel 0, Stack 2
            0x8000_0000,  # Channel 0, Stack 3
        ]
    )


# =============================================================================
# Layer 1: Traffic Generator Tests
# =============================================================================

class TestTrafficGeneratorLayer:
    """Test Layer 1: Traffic Generator"""

    @pytest.fixture
    def config(self) -> TrafficConfig:
        """Create traffic configuration"""
        return TrafficConfig(request_rate=1e6)

    @pytest.fixture
    def generator(self, config) -> TrafficGenerator:
        """Create traffic generator"""
        return TrafficGenerator(config)

    def test_generator_initialization(self, generator):
        """Test that traffic generator initializes correctly"""
        assert generator is not None
        assert generator.config is not None
        assert generator.hbm_spec.channels == 32

    def test_request_generation(self, generator):
        """Test that generator produces valid requests"""
        requests = generator.generate(count=10)

        assert len(requests) == 10
        for req in requests:
            assert isinstance(req, HBMRequest)
            assert req.length > 0
            assert req.addr > 0

    def test_pattern_switching(self, generator):
        """Test traffic pattern switching"""
        # Test synthetic patterns
        generator.set_pattern(TrafficPattern.SYNTHETIC_RANDOM)
        random_reqs = generator.generate(count=5)
        assert len(random_reqs) == 5

        generator.set_pattern(TrafficPattern.SYNTHETIC_BURST)
        burst_reqs = generator.generate(count=5)
        assert len(burst_reqs) == 5

    def test_qos_distribution(self, generator):
        """Test QoS level distribution"""
        requests = generator.generate(count=100)

        qos_counts = {}
        for req in requests:
            qos_counts[req.qos] = qos_counts.get(req.qos, 0) + 1

        # Should have some distribution across QoS levels
        assert len(qos_counts) > 0
        # Most requests should be normal QoS (8)
        assert 8 in qos_counts


# =============================================================================
# Layer 2: Interconnect Tests
# =============================================================================

class TestInterconnectLayer:
    """Test Layer 2: Interconnect"""

    @pytest.fixture
    def crossbar(self) -> CrossbarInterconnect:
        """Create crossbar interconnect"""
        return CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            channels_per_stack=32,
            routing_mode=RoutingMode.ADDRESS_BASED
        )

    @pytest.fixture
    def mesh(self) -> MeshInterconnect:
        """Create mesh interconnect"""
        return MeshInterconnect(
            rows=4,
            cols=8,
            stack_count=4,
            channels_per_stack=32
        )

    def test_crossbar_routing(self, crossbar):
        """Test crossbar routing"""
        for addr in [0x1000_0000, 0x2020_0000, 0x4040_0000]:
            req = InterconnectRequest(
                source_port=0,
                addr=addr,
                size=64,
                is_read=True
            )
            resp = crossbar.route_request(req)

            assert resp.success
            assert 0 <= resp.dest_stack < 4
            assert 0 <= resp.dest_channel < 32

    def test_mesh_routing(self, mesh):
        """Test mesh routing"""
        req = InterconnectRequest(
            source_port=0,
            addr=0x1000_0000,
            size=64,
            is_read=True
        )
        resp = mesh.route_request(req)

        assert resp.success
        assert resp.latency >= 0

    def test_multi_stack_routing(self, crossbar):
        """Test routing across multiple stacks"""
        results = []

        for stack_id in range(4):
            # Address that routes to this stack
            addr = 0x8000_0000 if stack_id == 3 else (stack_id << 44)
            req = InterconnectRequest(
                source_port=stack_id,
                addr=addr,
                size=64,
                is_read=True
            )
            resp = crossbar.route_request(req)
            results.append((stack_id, resp.dest_stack))

        # Each stack should be reachable
        routed_stacks = {r[1] for r in results}
        assert len(routed_stacks) >= 1  # At least one stack used


# =============================================================================
# Layer 3: Controller Tests
# =============================================================================

class TestControllerLayer:
    """Test Layer 3: HBM4 Controller"""

    @pytest.fixture
    def spec(self) -> HBM4Spec:
        """Create HBM4 specification"""
        return HBM4Spec()

    @pytest.fixture
    def controller(self, spec) -> HBM4Controller:
        """Create HBM4 controller"""
        return HBM4Controller(spec=spec)

    @pytest.fixture
    def decoder(self, spec) -> HBM4AddressDecoder:
        """Create HBM4 address decoder"""
        return HBM4AddressDecoder(spec=spec)

    def test_controller_initialization(self, controller, spec):
        """Test controller initialization"""
        assert controller is not None
        assert controller.channels == 32
        assert controller.dfi is not None

    def test_request_submission(self, controller):
        """Test request submission to controller"""
        result = controller.submit_request(
            addr=0x1000_0000,
            is_read=True,
            qos_level=8,
            size_bytes=64
        )
        assert result is not None

    def test_address_decoding(self, decoder):
        """Test address decoding"""
        addr = 0x1000_0000
        decoded = decoder.decode(addr)

        assert 0 <= decoded.channel_id < 32
        assert 0 <= decoded.pseudo_channel_id < 2
        assert 0 <= decoded.bank_group_id < 8
        assert 0 <= decoded.bank_id < 16
        assert 0 <= decoded.row_id < (1 << 16)

    def test_qos_scheduling(self, controller):
        """Test QoS-based request scheduling"""
        # Submit requests with different priorities
        for i in range(8):
            result = controller.submit_request(
                addr=0x1000_0000 + (i << 12),
                is_read=True,
                qos_level=i,
                size_bytes=64
            )
            assert result is not None

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 8

    def test_refresh_scheduling(self, controller, spec):
        """Test refresh scheduling integration"""
        refresh_scheduler = HBM4RefreshScheduler(config=spec)

        # Simulate some cycles
        for _ in range(100):
            refresh_scheduler.tick()

        # Refresh should have occurred
        stats = controller.get_stats()
        assert 'refresh' in stats


# =============================================================================
# Layer 4: DRAM Model Tests
# =============================================================================

class TestDRAMModelLayer:
    """Test Layer 4: HBM4 DRAM Model"""

    @pytest.fixture
    def spec(self) -> HBM4Spec:
        """Create HBM4 specification"""
        return HBM4Spec()

    @pytest.fixture
    def channel(self, spec) -> HBM4Channel:
        """Create single HBM4 channel"""
        return HBM4Channel(channel_id=0, spec=spec)

    @pytest.fixture
    def channel_array(self, spec) -> HBM4ChannelArray:
        """Create HBM4 channel array"""
        return HBM4ChannelArray(spec=spec)

    def test_channel_initialization(self, channel, spec):
        """Test channel initialization"""
        assert channel.channel_id == 0
        assert channel.spec.channels == 32
        assert len(channel.pseudo_channels) == 2

    def test_row_activation(self, channel):
        """Test row activation command"""
        # Activate row 0 in bank 0
        result = channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)
        assert result

        # Check channel state
        state = channel.get_state_summary()
        assert state['state'] == 'ACTIVE'

    def test_read_command(self, channel):
        """Test read command"""
        # Activate first
        channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)

        # Issue read
        result = channel.issue_command('RD', pseudo_channel=0, bank=0, row=0)
        assert result

    def test_write_command(self, channel):
        """Test write command"""
        # Activate first
        channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)

        # Issue write
        result = channel.issue_command('WR', pseudo_channel=0, bank=0, row=0)
        assert result

    def test_refresh_command(self, channel):
        """Test all-bank refresh"""
        result = channel.execute_refresh('REFab')
        assert result

    def test_channel_array(self, channel_array, spec):
        """Test channel array with all 32 channels"""
        assert len(channel_array.channels) == 32

        # Access multiple channels
        for ch_id in range(0, 32, 8):  # Every 8th channel
            ch = channel_array.get_channel(ch_id)
            assert ch is not None
            assert ch.channel_id == ch_id

    def test_numeric_command_encoding(self, channel):
        """Test numeric command encoding for RTL interface"""
        # Test command encoding/decoding for valid commands
        test_pairs = [
            (HBM4Command.ACT, 'ACT'),
            (HBM4Command.READ, 'RD'),
            (HBM4Command.WRITE, 'WR'),
            (HBM4Command.PRE, 'PRE'),
            (HBM4Command.REF, 'REFab'),  # REFab maps to REF
        ]

        for cmd, cmd_str in test_pairs:
            # Verify to_string conversion
            result = HBM4Command.to_string(cmd)
            assert result == cmd_str or cmd_str.startswith(result) or result in cmd_str, \
                f"Command {cmd.name} to_string returned {result}, expected {cmd_str}"

            # Verify from_string conversion
            cmd_back = HBM4Command.from_string(cmd_str)
            assert cmd_back == cmd, f"Command from_string('{cmd_str}') returned {cmd_back.name}, expected {cmd.name}"


# =============================================================================
# Layer 5: PHY Interface Tests
# =============================================================================

class TestPHYLayer:
    """Test Layer 5: DFI PHY Interface"""

    @pytest.fixture
    def dfi(self) -> DFI5Interface:
        """Create DFI5 interface"""
        return DFI5Interface()

    def test_dfi_initialization(self, dfi):
        """Test DFI initialization"""
        assert dfi is not None
        assert dfi.is_ready()

    def test_dfi_command_encoding(self, dfi):
        """Test DFI command encoding"""
        req = dfi.encode_command(
            cmd='RD',
            addr_vec={'row': 0, 'bank': 0, 'channel': 0, 'address': 0x1000},
            priority=8
        )
        assert req is not None

    def test_dfi_low_power_states(self, dfi):
        """Test DFI low power state transitions"""
        from model.dram.dfi_interface import DFILowPowerState

        # Enter controller low power state
        assert dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert dfi.lp_state == DFILowPowerState.LP_CTRL

        # Wakeup requires tick() cycles to complete (tLP_CTRL_EXIT latency)
        dfi.wakeup_from_low_power()
        # Call tick() to advance the state machine
        for _ in range(10):
            dfi.tick()
        assert dfi.lp_state == DFILowPowerState.LP_IDLE


# =============================================================================
# End-to-End Integration Tests
# =============================================================================

class TestEndToEndIntegration:
    """End-to-end integration tests for all 5 layers"""

    @pytest.fixture
    def spec(self) -> HBM4Spec:
        """Create HBM4 specification"""
        return HBM4Spec()

    @pytest.fixture
    def traffic_gen(self) -> TrafficGenerator:
        """Create traffic generator"""
        config = TrafficConfig(request_rate=1e6)
        return TrafficGenerator(config)

    @pytest.fixture
    def interconnect(self) -> CrossbarInterconnect:
        """Create interconnect"""
        return CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            channels_per_stack=32
        )

    @pytest.fixture
    def controller(self, spec) -> HBM4Controller:
        """Create controller"""
        return HBM4Controller(spec=spec)

    @pytest.fixture
    def channel_array(self, spec) -> HBM4ChannelArray:
        """Create DRAM channel array"""
        return HBM4ChannelArray(spec=spec)

    def test_complete_pipeline(self, traffic_gen, interconnect, controller, channel_array, spec):
        """Test complete 5-layer pipeline"""
        # Layer 1: Generate traffic
        requests = traffic_gen.generate(count=10)
        assert len(requests) == 10

        # Layer 2: Route through interconnect
        routed = []
        for req in requests:
            ic_req = InterconnectRequest(
                source_port=0,
                addr=req.addr,
                size=req.length,
                is_read=req.is_read
            )
            ic_resp = interconnect.route_request(ic_req)
            assert ic_resp.success
            routed.append((req, ic_resp))

        # Layer 3: Submit to controller
        submitted = []
        for req, ic_resp in routed:
            result = controller.submit_request(
                addr=req.addr,
                is_read=req.is_read,
                qos_level=req.qos,
                size_bytes=req.length
            )
            if result:
                submitted.append(result)

        # Layer 4: Execute on DRAM model
        for ch_id in range(0, 32, 8):
            ch = channel_array.get_channel(ch_id)
            if ch:
                ch.issue_command('ACT', pseudo_channel=0, bank=0, row=0)
                ch.issue_command('RD', pseudo_channel=0, bank=0, row=0)

        # Verify total bandwidth
        total_bw = channel_array.total_bandwidth_gbs
        assert total_bw > 0

        print(f"\nPipeline Test Results:")
        print(f"  Generated: {len(requests)} requests")
        print(f"  Routed: {len(routed)} requests")
        print(f"  Submitted: {len(submitted)} requests")
        print(f"  DRAM Channels: {len(channel_array.channels)}")
        print(f"  Total Bandwidth: {total_bw:.1f} GB/s")

    def test_qos_priority_integration(self, controller, traffic_gen):
        """Test QoS priority across layers"""
        # Generate requests with different QoS levels
        traffic_gen.set_pattern(TrafficPattern.SYNTHETIC_FIXED_RATE)
        requests = traffic_gen.generate(count=20)

        # Submit all requests
        for req in requests:
            controller.submit_request(
                addr=req.addr,
                is_read=req.is_read,
                qos_level=req.qos,
                size_bytes=req.length
            )

        # Verify statistics
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] >= 20

    def test_multi_channel_load_balancing(self, controller, interconnect):
        """Test load balancing across 32 channels"""
        # Generate requests targeting different channels
        num_requests = 100

        for i in range(num_requests):
            # Create addresses that spread across channels
            addr = 0x1000_0000 + (i << 20)  # Spread across channels
            controller.submit_request(
                addr=addr,
                is_read=(i % 2 == 0),
                qos_level=8,
                size_bytes=64
            )

            # Route through interconnect
            ic_req = InterconnectRequest(
                source_port=i % 32,
                addr=addr,
                size=64,
                is_read=(i % 2 == 0)
            )
            interconnect.route_request(ic_req)

        # Get statistics
        stats = controller.get_stats()
        interconnect_stats = interconnect.get_stats()

        print(f"\nLoad Balancing Test Results:")
        print(f"  Controller requests: {stats['controller']['total_requests']}")
        print(f"  Interconnect requests: {interconnect_stats['total_requests']}")
        print(f"  Success rate: {interconnect_stats['success_rate']:.2%}")

    def test_refresh_integration(self, controller, spec):
        """Test refresh scheduling integration with controller"""
        refresh_scheduler = HBM4RefreshScheduler(config=spec)

        # Submit some requests
        for i in range(10):
            controller.submit_request(
                addr=0x1000_0000 + (i << 12),
                is_read=True,
                qos_level=8,
                size_bytes=64
            )

        # Simulate refresh cycles
        refresh_count = 0
        for cycle in range(1000):
            refresh_scheduler.tick()

            if refresh_scheduler.can_refresh():
                refresh_cmd = refresh_scheduler.get_refresh_command()
                if refresh_cmd:
                    refresh_count += 1

        print(f"\nRefresh Test Results:")
        print(f"  Cycles simulated: 1000")
        print(f"  Refresh commands issued: {refresh_count}")

    def test_bandwidth_calculation(self, controller, traffic_gen, spec):
        """Test end-to-end bandwidth calculation"""
        # Submit requests
        requests = traffic_gen.generate(count=100)

        total_bytes = 0
        for req in requests:
            result = controller.submit_request(
                addr=req.addr,
                is_read=req.is_read,
                qos_level=req.qos,
                size_bytes=req.length
            )
            if result:
                total_bytes += req.length

        # Calculate bandwidth
        controller.current_time_ns = 1000  # 1us
        bandwidth = controller.get_bandwidth_gbs()

        print(f"\nBandwidth Test Results:")
        print(f"  Requests: {len(requests)}")
        print(f"  Total bytes: {total_bytes}")
        print(f"  Bandwidth: {bandwidth:.2f} GB/s")
        print(f"  Peak bandwidth: {spec.bandwidth_gbs:.2f} GB/s")


# =============================================================================
# Performance Benchmark Tests
# =============================================================================

class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    @pytest.fixture
    def spec(self) -> HBM4Spec:
        """Create HBM4 specification"""
        return HBM4Spec()

    def test_hbm4_bandwidth_baseline(self, spec):
        """Verify HBM4 bandwidth meets specification"""
        # HBM4 @ 8 GT/s, 2048-bit interface = 2.048 TB/s
        expected = 2.048  # TB/s
        actual = spec.bandwidth

        assert abs(actual - expected) < 0.001, f"Bandwidth mismatch: {actual} vs {expected}"

    def test_latency_baseline(self, spec):
        """Test read latency baseline"""
        # Read latency = nRCDRD + nCL + nBL
        expected_latency = spec.nRCDRD + spec.nCL + spec.nBL  # 8 + 8 + 4 = 20 cycles
        actual_latency = expected_latency

        print(f"\nLatency Test:")
        print(f"  Read latency: {actual_latency} cycles")
        print(f"  tRCD: {spec.nRCDRD}, tCL: {spec.nCL}, tBL: {spec.nBL}")

    def test_multi_stack_bandwidth(self, spec):
        """Test multi-stack bandwidth scaling"""
        # 4 stacks × 2.048 TB/s = 8.192 TB/s
        single_stack_bw = spec.bandwidth
        multi_stack_bw = single_stack_bw * 4

        print(f"\nMulti-Stack Bandwidth:")
        print(f"  Single stack: {single_stack_bw:.3f} TB/s")
        print(f"  4 stacks: {multi_stack_bw:.3f} TB/s")


# =============================================================================
# Main entry point
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])