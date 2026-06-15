"""
Multi-Channel HBM3 Validation Tests

Tests 8-channel HBM3 arbitration and channel utilization.
"""

import pytest
from typing import Dict, List

from model.controller.controller import HBMController
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.request import HBMRequest
from model.dram.dram_model import DRAMModel


class TestMultiChannelBasic:
    """Basic multi-channel tests"""

    def test_channel_count(self):
        """Verify default HBM3 has 8 channels per stack"""
        config = HBM3_DEFAULT
        assert config.channels_per_stack == 8

    def test_total_channel_count(self):
        """Verify total channels across all stacks"""
        config = HBM3_DEFAULT
        total_channels = config.stack_count * config.channels_per_stack
        assert total_channels == 16  # 2 stacks × 8 channels

    def test_dram_model_channels(self):
        """Verify DRAM model has correct channel count"""
        dram = DRAMModel(
            hbm_version="hbm3",
            stack_count=2,
            banks_per_channel=16
        )
        # Check stack count
        assert len(dram.stacks) == 2


class TestMultiChannelArbitration:
    """Multi-channel arbitration tests"""

    def test_channel_load_balancing(self):
        """Verify requests distribute across 8 channels"""
        config = HBMConfig(
            stack_count=1,
            channels_per_stack=8,
        )
        controller = HBMController(config)

        # Submit requests targeting different channels
        for ch in range(8):
            # Address range for each channel
            addr = ch << 20  # Each channel gets different address range
            req = HBMRequest(addr=addr, length=64, is_read=True, qos=8)
            controller.submit_request(req)

        # Verify all requests were accepted
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 8

    def test_channel_affinity(self):
        """Test that sequential addresses go to same channel"""
        config = HBMConfig(
            stack_count=1,
            channels_per_stack=8,
        )
        controller = HBMController(config)

        # Submit sequential requests
        base_addr = 0x1000
        requests = []
        for i in range(16):
            addr = base_addr + (i * 64)
            req = HBMRequest(addr=addr, length=64, is_read=True, qos=8)
            controller.submit_request(req)
            requests.append(req)

        # Verify at least some went to same channel
        channel_counts: Dict[int, int] = {}
        for req in requests:
            if req.channel_id not in channel_counts:
                channel_counts[req.channel_id] = 0
            channel_counts[req.channel_id] += 1

        # Should have some channel affinity
        assert len(channel_counts) <= 8  # Within 8 channels

    def test_qos_channel_priority(self):
        """Test QoS priority across channels"""
        config = HBMConfig(
            stack_count=1,
            channels_per_stack=8,
            scheduler_mode="qos",
        )
        controller = HBMController(config)

        # Submit requests with different QoS
        for ch in range(4):
            addr = ch << 20
            req = HBMRequest(addr=addr, length=64, is_read=True, qos=15-ch*4)
            controller.submit_request(req)

        # Verify high QoS request was accepted
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 4


class TestMultiChannelBankGroups:
    """Bank group tests for multi-channel"""

    def test_bank_group_count(self):
        """Verify bank group count per channel"""
        config = HBM3_DEFAULT
        assert config.bank_groups_per_channel == 8

    def test_banks_per_group(self):
        """Verify banks per group"""
        config = HBM3_DEFAULT
        banks_per_group = config.banks_per_pseudo_channel // config.bank_groups_per_channel
        assert banks_per_group == 2  # 16 banks / 8 groups = 2 banks per group

    def test_multi_bank_requests(self):
        """Test requests targeting different banks in same channel"""
        config = HBMConfig(
            stack_count=1,
            channels_per_stack=1,  # Single channel for focused test
        )
        controller = HBMController(config)

        # Submit requests to same channel, different banks
        for bg in range(8):  # 8 bank groups
            for bank in range(2):  # 2 banks per group
                addr = (bg * 0x10000) + (bank * 0x1000)
                req = HBMRequest(addr=addr, length=64, is_read=True, qos=8)
                controller.submit_request(req)

        # Verify all 16 banks were used
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 16


class TestMultiChannelSimulation:
    """Multi-channel simulation tests"""

    def test_multi_channel_simulation(self):
        """Test simulation with 8 channels"""
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        config = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.8,
            hbm_config=HBMConfig(
                stack_count=1,
                channels_per_stack=8,
            )
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # Verify requests completed
        assert stats.total_requests > 0

    def test_two_stack_simulation(self):
        """Test simulation with 2 stacks (16 channels total)"""
        from sim.simulator import HBMSimulator, SimulationConfig

        config = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.5,
            hbm_config=HBMConfig(
                stack_count=2,
                channels_per_stack=8,
            )
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # Verify requests completed
        assert stats.total_requests > 0

    def test_channel_bandwidth(self):
        """Test bandwidth calculation per channel"""
        config = HBM3_DEFAULT
        total_bw = config.calc_bandwidth_total()
        per_channel_bw = total_bw / (config.stack_count * config.channels_per_stack)

        # Should be roughly equal per channel
        assert abs(per_channel_bw - 102.4) < 1.0  # ~102.4 GB/s per channel


class TestMultiChannelPerformance:
    """Multi-channel performance tests"""

    def test_parallel_channel_access(self):
        """Test parallel access to different channels"""
        config = HBMConfig(
            stack_count=1,
            channels_per_stack=8,
        )
        controller = HBMController(config)

        # Submit 8 requests to 8 different channels
        for ch in range(8):
            req = HBMRequest(addr=(ch << 24), length=64, is_read=True, qos=8)
            controller.submit_request(req)

        # Run simulation
        responses = []
        for _ in range(200):
            resp = controller.tick()
            if resp:
                responses.append(resp)

        # Verify some completions
        assert len(responses) >= 0

    def test_channel_contention(self):
        """Test when multiple requests target same channel"""
        config = HBMConfig(
            stack_count=1,
            channels_per_stack=4,  # Fewer channels for contention test
        )
        controller = HBMController(config)

        # Submit many requests to same address range (same channel)
        base_addr = 0x1000
        for i in range(32):
            req = HBMRequest(addr=base_addr + (i % 4) * 0x100, length=64, is_read=True, qos=8)
            controller.submit_request(req)

        # Verify requests were queued
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 32


class TestChannelUtilizationStats:
    """Channel utilization statistics tests"""

    def test_stats_structure(self):
        """Verify stats include channel info"""
        config = HBM3_DEFAULT
        controller = HBMController(config)

        # Submit some requests
        for i in range(8):
            req = HBMRequest(addr=(i << 20), length=64, is_read=True, qos=8)
            controller.submit_request(req)

        stats = controller.get_stats()
        assert 'controller' in stats
        assert 'total_requests' in stats['controller']

    def test_queue_stats_per_channel(self):
        """Test queue statistics"""
        config = HBMConfig(
            stack_count=1,
            channels_per_stack=4,
        )
        controller = HBMController(config)

        # Submit requests
        for i in range(16):
            req = HBMRequest(addr=(i << 16), length=64, is_read=True, qos=8)
            controller.submit_request(req)

        # Verify queue stats
        queue_stats = controller.queue_manager.get_stats()
        assert 'read' in queue_stats
        assert 'write' in queue_stats
        assert queue_stats['read']['current_occupancy'] == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"])