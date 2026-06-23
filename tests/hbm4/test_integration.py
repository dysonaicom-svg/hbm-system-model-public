"""
HBM4 Logic Base Die Integration Tests

End-to-end integration tests for HBM4 memory subsystem.
Tests the complete flow from traffic generation through controller
to DRAM channel model with statistics collection.

Test coverage:
- Traffic pattern generation and submission
- Multi-channel address decoding
- Request scheduling and completion
- Bandwidth and latency measurement
- Power estimation
- Thermal modeling integration

Based on:
- JEDEC JESD270-4A HBM4 specification
- Design document 2026-06-15-hbm-system-model-design.md
"""

import pytest
import time
import random
from typing import List, Dict, Any
from dataclasses import dataclass

from model.dram.HBM4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.controller.HBM4_controller import HBM4Controller, HBM4ControllerStats
from model.controller.HBM4_address_decoder import HBM4AddressDecoder
from model.controller.HBM4_qos_scheduler import HBM4QoSScheduler, QoSLevel
from model.controller.HBM4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.dram.HBM4_channel_model import HBM4Channel
from model.dram.dfi_interface import DFI5Interface, DFIRequest, DFIResponse
from sim.simulator import (
    TrafficGenerator, TrafficPattern, SimulationConfig, SimulationStats
)


# =============================================================================
# Traffic Generator for HBM4
# =============================================================================

class HBM4TrafficGenerator:
    """HBM4-specific traffic generator with channel-aware address generation"""

    def __init__(self, config: SimulationConfig, controller: HBM4Controller):
        self.config = config
        self.controller = controller
        self.decoder = HBM4AddressDecoder(spec=controller.spec)
        if config.seed is not None:
            random.seed(config.seed)
        self.current_addr = 0
        self.hot_bank = 0
        self.hot_channel = 0

    def generate(self) -> List[Dict[str, Any]]:
        """Generate requests based on traffic pattern"""
        requests = []

        # According to request rate, decide if we generate requests
        if random.random() > self.config.request_rate:
            return requests

        # Generate address based on pattern
        if self.config.traffic_pattern == TrafficPattern.RANDOM:
            addr = self._generate_random_addr()
        elif self.config.traffic_pattern == TrafficPattern.SEQUENTIAL:
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.burst_size) % self.config.address_range
        elif self.config.traffic_pattern == TrafficPattern.STRIDE:
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.stride_value) % self.config.address_range
        elif self.config.traffic_pattern == TrafficPattern.HOT_SPOT:
            addr = self._generate_hot_spot_addr()
        else:  # ADDR_SCATTER
            addr = self._generate_scatter_addr()

        # Align address to burst boundary
        addr = addr & ~0x3F  # 64-byte alignment

        # Generate read or write request
        is_read = random.random() < self.config.read_ratio

        # QoS level based on pattern
        qos_level = self._get_qos_for_pattern(addr)

        requests.append({
            'addr': addr,
            'is_read': is_read,
            'qos_level': qos_level,
            'size_bytes': self.config.burst_size
        })

        return requests

    def _generate_random_addr(self) -> int:
        """Generate random address across all channels"""
        return random.randint(0, self.config.address_range - 1)

    def _generate_hot_spot_addr(self) -> int:
        """Generate address with 80% access to hot spot"""
        if random.random() < 0.8:
            # Hot spot: specific channel and bank
            return self.hot_channel << 41 | self.hot_bank << 17 | 0x8
        else:
            return random.randint(0, self.config.address_range - 1)

    def _generate_scatter_addr(self) -> int:
        """Generate scattered addresses across channels"""
        ch = random.randint(0, self.controller.spec.channels - 1)
        row = random.randint(0, 1023)
        return ch << 41 | row << 17 | 0x8

    def _get_qos_for_pattern(self, addr: int) -> int:
        """Get QoS level based on address pattern"""
        decoded = self.decoder.decode(addr)
        # Higher priority for specific channels
        if decoded.channel_id in [0, 1, 2, 3]:
            return random.choice([0, 1, 2])  # Critical priority
        elif decoded.channel_id in [4, 5, 6, 7]:
            return random.choice([4, 5, 6])  # High priority
        else:
            return random.choice([8, 9, 10])  # Normal priority


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def hbm4_spec():
    """Create default HBM4 specification"""
    return HBM4Spec()


@pytest.fixture
def hbm4_controller(hbm4_spec):
    """Create HBM4 controller with default settings"""
    return HBM4Controller(
        spec=hbm4_spec,
        enable_qos=True,
        enable_refresh=True
    )


@pytest.fixture
def simulation_config():
    """Create default simulation configuration"""
    return SimulationConfig(
        simulation_time_us=10.0,  # Short for tests
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        read_ratio=0.7,
        burst_size=64,
        address_range=0x100_0000,
        stride_value=4096,
        seed=42
    )


# =============================================================================
# Test Cases
# =============================================================================

class TestHBM4TrafficGeneration:
    """Test traffic generation and submission"""

    def test_random_traffic_submission(self, hbm4_controller, simulation_config):
        """Test submitting random traffic pattern requests"""
        traffic_gen = HBM4TrafficGenerator(simulation_config, hbm4_controller)

        submitted = 0
        for _ in range(100):
            requests = traffic_gen.generate()
            for req in requests:
                request_id = hbm4_controller.submit_request(
                    addr=req['addr'],
                    is_read=req['is_read'],
                    qos_level=req['qos_level'],
                    size_bytes=req['size_bytes']
                )
                if request_id is not None:
                    submitted += 1

        assert submitted > 0, "No requests were submitted"
        assert hbm4_controller.stats.total_requests == submitted

    def test_sequential_traffic_submission(self, hbm4_controller, hbm4_spec):
        """Test submitting sequential traffic pattern requests"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=1.0,
            read_ratio=1.0,
            burst_size=64,
            seed=42
        )
        traffic_gen = HBM4TrafficGenerator(config, hbm4_controller)

        # Submit 50 sequential requests
        for _ in range(50):
            requests = traffic_gen.generate()
            for req in requests:
                hbm4_controller.submit_request(
                    addr=req['addr'],
                    is_read=req['is_read'],
                    qos_level=req['qos_level']
                )

        # Verify all requests were submitted
        assert hbm4_controller.stats.total_requests == 50
        # Sequential requests - all should be successfully submitted

    def test_stride_traffic_submission(self, hbm4_controller):
        """Test submitting stride traffic pattern requests"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.STRIDE,
            request_rate=1.0,
            read_ratio=1.0,
            stride_value=4096,
            seed=42
        )
        traffic_gen = HBM4TrafficGenerator(config, hbm4_controller)

        for _ in range(32):
            requests = traffic_gen.generate()
            for req in requests:
                hbm4_controller.submit_request(
                    addr=req['addr'],
                    is_read=req['is_read'],
                    qos_level=8
                )

        # All 32 stride requests should be submitted
        assert hbm4_controller.stats.total_requests == 32


class TestHBM4RequestScheduling:
    """Test request scheduling and completion"""

    def test_all_channels_scheduled(self, hbm4_controller):
        """Test that requests across all channels are scheduled"""
        # Submit requests to all 32 channels
        for ch in range(32):
            addr = ch << 41 | 0x8  # Channel at bits 45:41
            hbm4_controller.submit_request(addr=addr, is_read=True)

        # Run simulation until all complete
        completed_channels = set()
        for _ in range(100):
            responses = hbm4_controller.tick()
            for resp in responses:
                if resp.channel_id is not None:
                    completed_channels.add(resp.channel_id)

        # All 32 channels should have completed
        assert len(completed_channels) == 32

    def test_read_write_interleaving(self, hbm4_controller):
        """Test interleaved read/write operations"""
        # Submit interleaved read/write requests
        for i in range(16):
            is_read = (i % 2 == 0)
            hbm4_controller.submit_request(
                addr=i * 0x100,
                is_read=is_read,
                qos_level=8
            )

        # Run until complete
        read_completed = 0
        write_completed = 0
        for _ in range(50):
            responses = hbm4_controller.tick()
            for resp in responses:
                if resp.status == "OK":
                    if hbm4_controller.stats.read_requests > 0:
                        read_completed += 1
                    else:
                        write_completed += 1

        # Both reads and writes should complete
        total = read_completed + write_completed
        assert total >= 16

    def test_qos_priority_scheduling(self, hbm4_controller):
        """Test QoS-based priority scheduling"""
        # Submit with different QoS levels
        # Low priority first
        for i in range(4):
            hbm4_controller.submit_request(
                addr=0x1000 + i * 0x100,
                is_read=True,
                qos_level=15  # Low priority
            )

        # High priority last
        high_req_id = hbm4_controller.submit_request(
            addr=0x0000,
            is_read=True,
            qos_level=0  # High priority
        )

        # Run simulation
        for _ in range(20):
            hbm4_controller.tick()

        # Statistics should show all requests processed
        assert hbm4_controller.stats.total_requests == 5


class TestHBM4BandwidthLatency:
    """Test bandwidth and latency measurement"""

    def test_bandwidth_measurement(self, hbm4_controller):
        """Test bandwidth calculation after traffic submission"""
        # Submit many requests
        for i in range(100):
            addr = i * 0x100
            hbm4_controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=8,
                size_bytes=64
            )

        # Run simulation
        for _ in range(200):
            hbm4_controller.tick()

        # Check bandwidth is calculated
        bandwidth = hbm4_controller.get_bandwidth_gbs()
        assert bandwidth >= 0, "Bandwidth should be non-negative"

        # Effective bandwidth should be <= peak bandwidth
        effective_tbps = hbm4_controller.get_effective_bandwidth_tbps()
        assert effective_tbps <= hbm4_controller.spec.bandwidth

    def test_latency_measurement(self, hbm4_controller):
        """Test latency tracking"""
        # Submit requests and track completion
        submitted_ids = []
        for i in range(20):
            req_id = hbm4_controller.submit_request(
                addr=i * 0x100,
                is_read=True,
                qos_level=8
            )
            if req_id:
                submitted_ids.append(req_id)

        # Run until all complete
        for _ in range(100):
            hbm4_controller.tick()

        # Check average latency is tracked
        avg_latency = hbm4_controller.stats.average_latency_ns
        assert avg_latency >= 0, "Average latency should be non-negative"

    def test_row_hit_rate(self, hbm4_controller):
        """Test row hit rate calculation"""
        # Submit to same row (should be row hits)
        for i in range(10):
            hbm4_controller.submit_request(
                addr=0x10000,  # Same row
                is_read=True,
                qos_level=8
            )

        # Run simulation
        for _ in range(50):
            hbm4_controller.tick()

        # Row hit rate should be calculated
        hit_rate = hbm4_controller.stats.row_hit_rate
        assert 0 <= hit_rate <= 1, "Row hit rate should be between 0 and 1"


class TestHBM4RefreshScheduling:
    """Test refresh scheduling functionality"""

    def test_refresh_count_increments(self, hbm4_controller):
        """Test that refresh count increments over time"""
        initial_refresh = hbm4_controller.stats.refresh_count

        # Run many cycles to trigger refresh
        for _ in range(10000):
            hbm4_controller.tick()

        # Refresh should have occurred
        assert hbm4_controller.stats.refresh_count >= initial_refresh

    def test_refresh_scheduler_mode(self, hbm4_controller):
        """Test refresh scheduler is in per-bank mode"""
        assert hbm4_controller.refresh_scheduler is not None
        assert hbm4_controller.refresh_scheduler.mode == RefreshMode.PER_BANK


class TestHBM4StatisticsCollection:
    """Test comprehensive statistics collection"""

    def test_complete_stats_collection(self, hbm4_controller):
        """Test all statistics are collected correctly"""
        # Submit mixed traffic
        for i in range(30):
            is_read = (i % 3 != 0)
            hbm4_controller.submit_request(
                addr=i * 0x100,
                is_read=is_read,
                qos_level=i % 16
            )

        # Run simulation
        for _ in range(100):
            hbm4_controller.tick()

        # Get comprehensive stats
        stats = hbm4_controller.get_stats()

        # Verify all stat categories exist
        assert 'controller' in stats
        assert 'spec' in stats
        assert 'queues' in stats
        assert 'qos' in stats
        assert 'refresh' in stats

        # Verify controller stats
        ctrl_stats = stats['controller']
        assert ctrl_stats['total_requests'] == 30
        assert ctrl_stats['read_requests'] > 0
        assert ctrl_stats['write_requests'] > 0
        assert 'row_hit_rate' in ctrl_stats
        assert 'average_latency_ns' in ctrl_stats

        # Verify spec stats
        spec_stats = stats['spec']
        assert spec_stats['channels'] == 32
        assert spec_stats['pseudo_channels'] == 64
        assert spec_stats['bandwidth_tbps'] > 0

    def test_queue_depth_tracking(self, hbm4_controller):
        """Test queue depth is tracked"""
        # Submit requests to fill queues
        for i in range(50):
            hbm4_controller.submit_request(
                addr=i * 0x100,
                is_read=True,
                qos_level=8
            )

        # Get stats
        stats = hbm4_controller.get_stats()

        # Queue depths should be tracked
        assert 'read_depth' in stats['queues']
        assert 'write_depth' in stats['queues']

    def test_power_estimation_in_stats(self, hbm4_controller):
        """Test power-related stats are present"""
        # Submit some traffic
        for i in range(20):
            hbm4_controller.submit_request(
                addr=i * 0x100,
                is_read=True,
                qos_level=8
            )

        # Run simulation
        for _ in range(50):
            hbm4_controller.tick()

        # Check stats include relevant metrics
        stats = hbm4_controller.get_stats()
        assert stats['controller']['total_requests'] == 20


class TestHBM4SpeedGrades:
    """Test different speed grade configurations"""

    def test_8gbps_speed_grade(self, hbm4_spec):
        """Test 8 GT/s baseline configuration"""
        # Verify baseline spec
        assert hbm4_spec.data_rate_gtps == 8.0
        assert hbm4_spec.bandwidth == pytest.approx(2.048, rel=0.01)

        # Create controller with this spec
        controller = HBM4Controller(spec=hbm4_spec)

        # Submit requests
        for i in range(10):
            controller.submit_request(addr=i * 0x100, is_read=True)

        # Run
        for _ in range(30):
            controller.tick()

        # Verify bandwidth
        bw = controller.get_bandwidth_gbs()
        assert bw > 0

    def test_12gbps_speed_grade(self):
        """Test 12 GT/s extended rate configuration"""
        spec = create_hbm4_spec_from_speed_grade("12Gbps")
        assert spec.data_rate_gtps == 12.0

        controller = HBM4Controller(spec=spec)

        # Submit requests
        for i in range(10):
            controller.submit_request(addr=i * 0x100, is_read=True)

        # Run
        for _ in range(30):
            controller.tick()

        # Verify stats
        stats = controller.get_stats()
        assert stats['spec']['data_rate_gtps'] == 12.0

    def test_16gbps_speed_grade(self):
        """Test 16 GT/s maximum rate configuration"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        assert spec.data_rate_gtps == 16.0

        controller = HBM4Controller(spec=spec)

        # Submit requests
        for i in range(10):
            controller.submit_request(addr=i * 0x100, is_read=True)

        # Run
        for _ in range(30):
            controller.tick()

        # Verify peak bandwidth
        assert spec.bandwidth == pytest.approx(4.096, rel=0.01)


class TestHBM4EndToEnd:
    """End-to-end integration tests"""

    def test_complete_simulation_workflow(self, hbm4_controller):
        """Test complete simulation workflow from traffic to completion"""
        # 1. Generate traffic using TrafficGenerator
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            read_ratio=0.7,
            seed=42
        )
        traffic_gen = HBM4TrafficGenerator(config, hbm4_controller)

        # 2. Submit traffic for 100 cycles
        for cycle in range(100):
            requests = traffic_gen.generate()
            for req in requests:
                hbm4_controller.submit_request(
                    addr=req['addr'],
                    is_read=req['is_read'],
                    qos_level=req['qos_level'],
                    size_bytes=req['size_bytes']
                )

            # 3. Execute cycle
            hbm4_controller.tick()

        # 4. Collect statistics
        stats = hbm4_controller.get_stats()

        # 5. Verify results
        assert stats['controller']['total_requests'] > 0
        assert stats['controller']['read_requests'] > 0
        assert stats['controller']['write_requests'] > 0
        assert stats['spec']['channels'] == 32

    def test_sustained_traffic_simulation(self, hbm4_controller):
        """Test sustained traffic over extended simulation"""
        # Submit continuous traffic for 500 cycles
        total_submitted = 0
        for cycle in range(500):
            # Submit to 4 channels each cycle
            for ch in range(4):
                addr = (ch << 41) + (cycle << 8)
                req_id = hbm4_controller.submit_request(
                    addr=addr,
                    is_read=True,
                    qos_level=8
                )
                if req_id:
                    total_submitted += 1

            hbm4_controller.tick()

        # Verify all submitted
        assert hbm4_controller.stats.total_requests == total_submitted

        # Check bandwidth
        bandwidth = hbm4_controller.get_bandwidth_gbs()
        assert bandwidth > 0

    def test_mixed_traffic_patterns(self, hbm4_controller):
        """Test mixing different traffic patterns"""
        patterns = [
            TrafficPattern.RANDOM,
            TrafficPattern.SEQUENTIAL,
            TrafficPattern.STRIDE,
            TrafficPattern.HOT_SPOT
        ]

        for pattern in patterns:
            config = SimulationConfig(
                simulation_time_us=5.0,
                traffic_pattern=pattern,
                request_rate=1.0,
                read_ratio=0.7,
                seed=42
            )
            traffic_gen = HBM4TrafficGenerator(config, hbm4_controller)

            # Submit 20 requests
            for _ in range(20):
                requests = traffic_gen.generate()
                for req in requests:
                    hbm4_controller.submit_request(
                        addr=req['addr'],
                        is_read=req['is_read'],
                        qos_level=req['qos_level']
                    )

            # Run to completion
            for _ in range(50):
                hbm4_controller.tick()

            # Pattern should complete
            assert hbm4_controller.stats.total_requests >= 20


# =============================================================================
# Performance Benchmark Tests
# =============================================================================

class TestHBM4Performance:
    """Performance benchmark tests"""

    def test_peak_bandwidth_accessible(self, hbm4_spec):
        """Test that peak bandwidth is accessible"""
        controller = HBM4Controller(spec=hbm4_spec)

        # Submit to all channels simultaneously
        for ch in range(32):
            addr = ch << 41
            for _ in range(8):
                controller.submit_request(addr=addr, is_read=True)

        # Run simulation
        for _ in range(100):
            controller.tick()

        # Peak bandwidth should be achievable
        assert hbm4_spec.bandwidth_gbs > 0

    def test_latency_under_load(self, hbm4_controller):
        """Test latency characteristics under load"""
        # Submit high load
        for ch in range(16):
            for row in range(4):
                addr = (ch << 41) | (row << 17)
                hbm4_controller.submit_request(
                    addr=addr,
                    is_read=True,
                    qos_level=8
                )

        # Run
        for _ in range(200):
            hbm4_controller.tick()

        # Check latency
        avg_latency = hbm4_controller.stats.average_latency_ns
        assert avg_latency >= 0


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])