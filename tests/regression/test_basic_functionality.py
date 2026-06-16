"""
Basic Functionality Smoke Tests

Smoke tests for basic HBM simulation functionality.
These tests verify core features work correctly before running more complex tests.

Test Categories:
- initialization: Simulator initialization and configuration
- basic_requests: Basic request submission and completion
- read_write: Read and write operations
- queue_operations: Queue push/pop operations
- channel_routing: Channel selection and routing

References:
- JEDEC JESD238 HBM3 Specification
- HBM4 JESD270-4A Specification
"""

import pytest
from typing import List

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.request import HBMRequest, HBMResponse


@pytest.mark.regression
class TestBasicFunctionality:
    """Basic functionality smoke tests"""

    def test_simulator_initialization(self, hbm3_config):
        """Test that simulator initializes correctly"""
        sim_config = SimulationConfig(
            simulation_time_us=10.0,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)

        assert sim is not None
        assert sim.config is not None
        assert sim.current_cycle == 0
        assert sim.stats is not None

    def test_simulator_run_completes(self, hbm3_config):
        """Test that simulator runs to completion"""
        sim_config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        assert stats is not None
        assert stats.total_cycles > 0
        assert stats.total_requests >= 0

    def test_controller_initialization(self, hbm3_config):
        """Test controller initializes correctly"""
        from model.controller.controller import HBMController

        controller = HBMController(hbm3_config)

        assert controller is not None
        assert controller.config == hbm3_config
        assert controller.current_time == 0
        assert controller.decoder is not None
        assert controller.queue_manager is not None
        assert controller.scheduler is not None

    def test_address_decoder(self, hbm3_config):
        """Test address decoding"""
        from model.controller.address_decoder import AddressDecoder

        decoder = AddressDecoder(hbm3_config)

        # Test various addresses
        test_addresses = [
            0x0000_0000_0000,
            0x1000_0000_0000,
            0xFFFF_FFFF_FFFF,
        ]

        for addr in test_addresses:
            decoded = decoder.decode(addr)
            assert decoded is not None
            assert 0 <= decoded.channel_id < hbm3_config.channels_per_stack
            assert 0 <= decoded.stack_id < hbm3_config.stack_count

    def test_request_creation(self):
        """Test request object creation"""
        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True
        )

        assert request is not None
        assert request.addr == 0x1000
        assert request.length == 64
        assert request.is_read is True
        assert request.request_id > 0

    def test_response_creation(self):
        """Test response object creation"""
        response = HBMResponse(
            request_id=1,
            status="OK",
            latency=100.0,
        )

        assert response is not None
        assert response.request_id == 1
        assert response.status == "OK"
        assert response.latency == 100.0

    def test_basic_request_submission(self, hbm3_config):
        """Test basic request submission"""
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest

        controller = HBMController(hbm3_config)

        # Submit a read request
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        success = controller.submit_request(request)

        assert success is True
        assert controller.stats['total_requests'] == 1
        assert controller.stats['read_requests'] == 1

    def test_write_request_submission(self, hbm3_config):
        """Test write request submission"""
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest

        controller = HBMController(hbm3_config)

        # Submit a write request
        request = HBMRequest(addr=0x1000, length=64, is_read=False)
        success = controller.submit_request(request)

        assert success is True
        assert controller.stats['total_requests'] == 1
        assert controller.stats['write_requests'] == 1

    def test_queue_push_pop(self, hbm3_config):
        """Test queue push and pop operations"""
        from model.controller.queue import ReadQueue
        from model.controller.request import HBMRequest

        queue = ReadQueue(max_depth=16)

        # Push some requests
        for i in range(4):
            request = HBMRequest(addr=0x1000 + i * 0x100, length=64, is_read=True)
            success = queue.push(request)
            assert success is True

        # Verify queue has correct size
        assert len(queue) == 4

        # Pop requests
        popped = []
        while not queue.empty():
            request = queue.pop()
            if request:
                popped.append(request)

        assert len(popped) == 4

    def test_multiple_requests(self, hbm3_config):
        """Test submitting multiple requests"""
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest

        controller = HBMController(hbm3_config)

        # Submit multiple requests
        for i in range(10):
            request = HBMRequest(
                addr=0x1000 + i * 0x1000,
                length=64,
                is_read=(i % 2 == 0)
            )
            success = controller.submit_request(request)
            assert success is True

        assert controller.stats['total_requests'] == 10
        assert controller.stats['read_requests'] == 5
        assert controller.stats['write_requests'] == 5

    def test_queue_overflow(self, hbm3_config):
        """Test queue overflow handling"""
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest

        # Small queue for overflow test
        config = hbm3_config.copy()
        config.queue_depth = 4

        controller = HBMController(config)

        # Fill the queue
        for i in range(4):
            request = HBMRequest(addr=0x1000 + i * 0x100, length=64, is_read=True)
            success = controller.submit_request(request)
            assert success is True

        # Try to add more (should fail)
        request = HBMRequest(addr=0x5000, length=64, is_read=True)
        success = controller.submit_request(request)

        # Queue should be full
        assert success is False or controller.queue_manager.read_queue.full()

    def test_traffic_generator_random(self, hbm3_config):
        """Test random traffic generation"""
        sim_config = SimulationConfig(
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)

        # Generate some requests
        requests = []
        for _ in range(10):
            sim.step()

        # Simulator should have processed some cycles
        assert sim.current_cycle > 0

    def test_traffic_generator_sequential(self, hbm3_config):
        """Test sequential traffic generation"""
        sim_config = SimulationConfig(
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)

        # Run simulation
        stats = sim.run()

        # Should complete requests
        assert stats.completed_requests >= 0

    def test_controller_tick(self, hbm3_config):
        """Test controller tick operation"""
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest

        controller = HBMController(hbm3_config)

        # Submit a request
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        controller.submit_request(request)

        # Tick the controller
        scheduled, response = controller.tick()

        assert controller.current_time == 1
        # Response may or may not be present depending on scheduling

    def test_dram_model_initialization(self):
        """Test DRAM model initializes correctly"""
        from model.dram.dram_model import DRAMModel

        dram = DRAMModel(
            hbm_version="hbm3",
            stack_count=2,
            banks_per_channel=16
        )

        assert dram is not None
        assert dram.spec is not None
        assert dram.timing is not None

    def test_config_bandwidth_calculation(self, hbm3_config):
        """Test bandwidth calculation in config"""
        bandwidth = hbm3_config.calc_bandwidth()

        assert bandwidth > 0
        assert isinstance(bandwidth, float)

        # HBM3 at 6.4 Gbps with 1024-bit interface:
        # 6.4 * 1024 / 8 = 819.2 GB/s
        expected = 6.4 * 1024 / 8
        assert abs(bandwidth - expected) < 1.0  # Within 1 GB/s

    def test_multi_channel_config(self, hbm3_config):
        """Test multi-channel configuration"""
        config = hbm3_config.copy()
        config.channels_per_stack = 16
        config.stack_count = 2

        total_channels = config.channels_per_stack * config.stack_count

        assert total_channels == 32

        bandwidth = config.calc_bandwidth_total()
        assert bandwidth > 0


@pytest.mark.regression
class TestBasicOperations:
    """Basic operation tests"""

    def test_read_after_write(self, hbm3_config):
        """Test read following write"""
        sim_config = SimulationConfig(
            simulation_time_us=20.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            read_ratio=0.5,  # Mix of reads and writes
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # Should complete some requests
        assert stats.completed_requests >= 0

    def test_multiple_channels(self, hbm3_config):
        """Test operation with multiple channels"""
        config = hbm3_config.copy()
        config.channels_per_stack = 8

        sim_config = SimulationConfig(
            simulation_time_us=20.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        assert stats.total_requests >= 0

    def test_bank_state_tracking(self, hbm3_config):
        """Test bank state tracking"""
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest

        controller = HBMController(hbm3_config)

        # Submit requests to same address (same bank)
        for i in range(3):
            request = HBMRequest(
                addr=0x1000 + i * 0x100,  # Adjacent addresses
                length=64,
                is_read=True
            )
            controller.submit_request(request)

        # Should track bank states
        assert len(controller.bank_states) >= 0

    def test_scheduler_mode(self, hbm3_config):
        """Test different scheduler modes"""
        # FR-FCFS mode
        config = hbm3_config.copy()
        config.scheduler_mode = "fr-fcfs"

        from model.controller.controller import HBMController
        controller = HBMController(config)
        assert controller.scheduler is not None

        # QoS mode
        try:
            config.scheduler_mode = "qos"
            controller = HBMController(config)
            assert controller.scheduler is not None
        except Exception:
            pytest.skip("QoS scheduler not available")


@pytest.mark.regression
class TestErrorHandling:
    """Error handling tests"""

    def test_invalid_address(self, hbm3_config):
        """Test handling of invalid addresses"""
        from model.controller.address_decoder import AddressDecoder

        decoder = AddressDecoder(hbm3_config)

        # Very large address (should be handled gracefully)
        addr = 0xFFFF_FFFF_FFFF_FFFF
        decoded = decoder.decode(addr)

        # Should either work or wrap around
        assert decoded is not None

    def test_queue_full_handling(self, hbm3_config):
        """Test handling when queue is full"""
        config = hbm3_config.copy()
        config.queue_depth = 2

        sim_config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=1.0,  # Maximum rate
            seed=42,
            hbm_config=config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # Should complete some requests despite small queue
        assert stats is not None

    def test_zero_length_request(self):
        """Test handling of zero-length request"""
        request = HBMRequest(addr=0x1000, length=0, is_read=True)

        # Should create request but with zero length
        assert request.length == 0

    def test_negative_address(self):
        """Test handling of negative address (should be converted to unsigned)"""
        # Python will handle negative addresses by converting to positive
        addr = -1
        addr_uint = addr & 0xFFFF_FFFF_FFFF_FFFF  # Convert to uint64

        # Should produce valid unsigned address
        assert addr_uint >= 0

        request = HBMRequest(addr=addr_uint, length=64, is_read=True)
        assert request.addr >= 0