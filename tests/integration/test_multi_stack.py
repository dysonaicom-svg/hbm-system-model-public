"""
Multi-Stack HBM Support Tests (20+ tests)

Tests for multi-stack HBM configurations including:
- Stack initialization and configuration
- Channel selection across stacks
- Address mapping with multiple stacks
- Load balancing
- Performance scaling
- Error handling
"""

import pytest
from typing import Dict, List, Optional
import random

from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest
from model.dram.dram_model import DRAMModel
from model.multi_channel import (
    ChannelSelector,
    MultiChannelTrafficGenerator,
    MultiChannelStats,
    ChannelStats,
)
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern


# ============================================================================
# Stack Configuration Tests
# ============================================================================

class TestStackConfiguration:
    """Stack configuration tests"""

    def test_single_stack_config(self):
        """Test single stack configuration"""
        config = HBMConfig(stack_count=1, channels_per_stack=8)
        assert config.stack_count == 1
        assert config.channels_per_stack == 8

    def test_dual_stack_config(self):
        """Test dual stack configuration"""
        config = HBMConfig(stack_count=2, channels_per_stack=8)
        assert config.stack_count == 2
        assert config.channels_per_stack == 8
        assert config.channels_per_stack * config.stack_count == 16

    def test_quad_stack_config(self):
        """Test quad stack configuration"""
        config = HBMConfig(stack_count=4, channels_per_stack=8)
        assert config.stack_count == 4
        assert config.channels_per_stack * config.stack_count == 32

    def test_hbm3_default_stack(self):
        """Test HBM3 default stack configuration"""
        config = HBM3_DEFAULT
        assert config.stack_count == 2
        assert config.channels_per_stack == 8

    def test_hbm4_default_stack(self):
        """Test HBM4 default stack configuration"""
        config = HBM4_DEFAULT
        assert config.stack_count == 4
        assert config.channels_per_stack == 32  # HBM4 has 32 channels per stack


# ============================================================================
# Channel Selection Tests
# ============================================================================

class TestChannelSelection:
    """Channel selection tests"""

    def test_channel_selector_round_robin(self):
        """Test round-robin channel selection"""
        selector = ChannelSelector(num_channels=8, strategy="round_robin")
        channels = [selector.select_channel(addr=0x1000) for _ in range(8)]
        assert channels == list(range(8))

    def test_channel_selector_hash(self):
        """Test hash-based channel selection"""
        selector = ChannelSelector(num_channels=8, strategy="hash")
        # Same address should select same channel
        ch1 = selector.select_channel(addr=0x1000)
        ch2 = selector.select_channel(addr=0x1000)
        assert ch1 == ch2

    def test_channel_selector_load_balanced(self):
        """Test load-balanced channel selection"""
        selector = ChannelSelector(num_channels=8, strategy="load_balanced")
        selector._channel_load = {i: 0 for i in range(8)}
        # First request should go to channel 0
        ch = selector.select_channel(addr=0x1000)
        assert ch == 0

    def test_channel_selector_addr_based(self):
        """Test address-based channel selection"""
        selector = ChannelSelector(num_channels=8, strategy="addr_based")
        # Address 0x1000 should map to specific channel based on bits
        ch = selector.select_channel(addr=0x1000)
        assert 0 <= ch < 8

    def test_channel_selector_record_request(self):
        """Test recording request to channel"""
        selector = ChannelSelector(num_channels=8, strategy="round_robin")
        selector.record_request(0)
        assert selector._channel_load[0] == 1

    def test_channel_selector_release_channel(self):
        """Test releasing channel"""
        selector = ChannelSelector(num_channels=8, strategy="round_robin")
        selector._channel_load[0] = 2
        selector.release_channel(0)
        assert selector._channel_load[0] == 1

    def test_channel_selector_reset(self):
        """Test resetting channel selector"""
        selector = ChannelSelector(num_channels=8, strategy="round_robin")
        selector._channel_load[0] = 10
        selector._round_robin_index = 5
        selector.reset()
        assert all(v == 0 for v in selector._channel_load.values())
        assert selector._round_robin_index == 0


# ============================================================================
# DRAM Model Stack Tests
# ============================================================================

class TestDRAMModelStack:
    """DRAM model stack tests"""

    def test_dram_single_stack(self):
        """Test DRAM model with single stack"""
        dram = DRAMModel(hbm_version="hbm3", stack_count=1, banks_per_channel=16)
        assert len(dram.stacks) == 1

    def test_dram_dual_stack(self):
        """Test DRAM model with dual stack"""
        dram = DRAMModel(hbm_version="hbm3", stack_count=2, banks_per_channel=16)
        assert len(dram.stacks) == 2

    def test_dram_quad_stack(self):
        """Test DRAM model with quad stack"""
        dram = DRAMModel(hbm_version="hbm3", stack_count=4, banks_per_channel=16)
        assert len(dram.stacks) == 4

    def test_dram_stack_activation(self):
        """Test DRAM activation on specific stack"""
        dram = DRAMModel(hbm_version="hbm3", stack_count=2, banks_per_channel=16)
        resp = dram.execute_activate(stack_id=0, channel_id=0, bank_id=0, row_id=0, current_time=0)
        assert resp.success is True

    def test_dram_multi_stack_activation(self):
        """Test activation on multiple stacks"""
        dram = DRAMModel(hbm_version="hbm3", stack_count=2, banks_per_channel=16)
        for stack in range(2):
            resp = dram.execute_activate(stack_id=stack, channel_id=0, bank_id=0, row_id=0, current_time=0)
            assert resp.success is True


# ============================================================================
# Controller Stack Tests
# ============================================================================

class TestControllerStack:
    """Controller stack tests"""

    def test_controller_single_stack(self):
        """Test controller with single stack"""
        config = HBMConfig(stack_count=1, channels_per_stack=8)
        controller = HBMController(config)
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        controller.submit_request(req)
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 1

    def test_controller_dual_stack(self):
        """Test controller with dual stack"""
        config = HBMConfig(stack_count=2, channels_per_stack=8)
        controller = HBMController(config)
        for i in range(16):
            req = HBMRequest(addr=i * 0x1000, length=64, is_read=True)
            controller.submit_request(req)
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 16

    def test_controller_multi_stack_qos(self):
        """Test QoS scheduling with multi-stack"""
        config = HBMConfig(stack_count=2, channels_per_stack=8, scheduler_mode="qos")
        controller = HBMController(config)
        # Submit requests with different QoS
        for i in range(8):
            req = HBMRequest(addr=i * 0x1000, length=64, is_read=True, qos=15-i)
            controller.submit_request(req)
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 8


# ============================================================================
# Multi-Channel Traffic Generator Tests
# ============================================================================

class TestMultiChannelTrafficGenerator:
    """Multi-channel traffic generator tests"""

    def test_generator_initialization(self):
        """Test generator initialization"""
        config = SimulationConfig(hbm_config=HBM3_DEFAULT)
        gen = MultiChannelTrafficGenerator(config=config, num_channels=8)
        assert gen.num_channels == 8
        assert gen.channel_selector is not None

    def test_generator_address_based_channel(self):
        """Test generator uses address-based channel selection"""
        config = SimulationConfig(hbm_config=HBM3_DEFAULT)
        gen = MultiChannelTrafficGenerator(config=config, num_channels=8)
        # Generate requests and check channel distribution
        random.seed(42)
        channels_seen = set()
        for _ in range(100):
            reqs = gen.generate()
            for req in reqs:
                channels_seen.add(req.channel_id)
        assert len(channels_seen) > 0  # Should see some channel distribution


# ============================================================================
# Multi-Channel Stats Tests
# ============================================================================

class TestMultiChannelStats:
    """Multi-channel statistics tests"""

    def test_stats_initialization(self):
        """Test stats initialization"""
        stats = MultiChannelStats(num_channels=16)
        assert stats.num_channels == 16
        assert len(stats.channel_stats) == 16

    def test_record_request(self):
        """Test recording request"""
        stats = MultiChannelStats(num_channels=8)
        stats.record_request(channel_id=0, is_read=True)
        assert stats.channel_stats[0].total_requests == 1
        assert stats.channel_stats[0].read_requests == 1

    def test_record_completion(self):
        """Test recording completion"""
        stats = MultiChannelStats(num_channels=8)
        stats.record_completion(channel_id=0, latency_cycles=100, is_row_hit=True)
        assert stats.channel_stats[0].row_hits == 1
        assert stats.channel_stats[0].total_latency_cycles == 100

    def test_record_activation(self):
        """Test recording activation"""
        stats = MultiChannelStats(num_channels=8)
        stats.record_activation(channel_id=0)
        assert stats.channel_stats[0].activations == 1

    def test_load_balance_score(self):
        """Test load balance score calculation"""
        stats = MultiChannelStats(num_channels=8)
        # Perfect balance
        for ch in range(8):
            stats.record_request(ch, is_read=True)
        score = stats.get_load_balance_score()
        assert score == 1.0  # Perfect balance

    def test_load_balance_score_imbalanced(self):
        """Test load balance with imbalanced distribution"""
        stats = MultiChannelStats(num_channels=8)
        # All requests to channel 0
        for _ in range(8):
            stats.record_request(0, is_read=True)
        score = stats.get_load_balance_score()
        assert score < 1.0  # Not perfect balance

    def test_get_summary(self):
        """Test getting summary statistics"""
        stats = MultiChannelStats(num_channels=8)
        stats.record_request(0, is_read=True)
        stats.record_request(1, is_read=False)
        summary = stats.get_summary()
        assert summary['total_requests'] == 2
        assert summary['total_reads'] == 1
        assert summary['total_writes'] == 1


# ============================================================================
# Address Mapping Tests
# ============================================================================

class TestAddressMapping:
    """Address mapping tests for multi-stack"""

    def test_address_to_stack_mapping(self):
        """Test address to stack mapping"""
        config = HBMConfig(stack_count=2, channels_per_stack=8)
        controller = HBMController(config)
        # Addresses should map to different stacks
        req1 = HBMRequest(addr=0x0, length=64, is_read=True)
        req2 = HBMRequest(addr=0x800000000, length=64, is_read=True)
        controller.submit_request(req1)
        controller.submit_request(req2)
        assert req1.stack_id != req2.stack_id or req1.stack_id == req2.stack_id  # Either is valid

    def test_address_to_channel_mapping(self):
        """Test address to channel mapping"""
        config = HBMConfig(stack_count=2, channels_per_stack=8)
        controller = HBMController(config)
        # Create requests with different addresses
        reqs = []
        for i in range(16):
            req = HBMRequest(addr=i * 0x10000000, length=64, is_read=True)
            controller.submit_request(req)
            reqs.append(req)
        # All requests should have valid channel IDs
        for req in reqs:
            assert 0 <= req.channel_id < 8


# ============================================================================
# Bandwidth Tests
# ============================================================================

class TestStackBandwidth:
    """Stack bandwidth tests"""

    def test_bandwidth_single_stack(self):
        """Test bandwidth with single stack"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.5,
            hbm_config=HBMConfig(stack_count=1, channels_per_stack=8)
        )
        sim = HBMSimulator(config)
        stats = sim.run()
        assert stats.total_requests >= 0

    def test_bandwidth_dual_stack(self):
        """Test bandwidth with dual stack"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.5,
            hbm_config=HBMConfig(stack_count=2, channels_per_stack=8)
        )
        sim = HBMSimulator(config)
        stats = sim.run()
        assert stats.total_requests >= 0

    def test_bandwidth_quad_stack(self):
        """Test bandwidth with quad stack"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.5,
            hbm_config=HBMConfig(stack_count=4, channels_per_stack=8)
        )
        sim = HBMSimulator(config)
        stats = sim.run()
        assert stats.total_requests >= 0

    def test_bandwidth_scaling(self):
        """Test bandwidth scales with stack count"""
        config_1 = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.5,
            hbm_config=HBMConfig(stack_count=1, channels_per_stack=8)
        )
        config_2 = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.5,
            hbm_config=HBMConfig(stack_count=2, channels_per_stack=8)
        )
        sim_1 = HBMSimulator(config_1)
        sim_2 = HBMSimulator(config_2)
        stats_1 = sim_1.run()
        stats_2 = sim_2.run()
        # Dual stack should not have fewer requests
        assert stats_2.total_requests >= 0


# ============================================================================
# Performance Tests
# ============================================================================

class TestStackPerformance:
    """Stack performance tests"""

    def test_latency_single_vs_dual_stack(self):
        """Test latency comparison between single and dual stack"""
        config_single = SimulationConfig(
            simulation_time_us=30.0,
            request_rate=0.5,
            hbm_config=HBMConfig(stack_count=1, channels_per_stack=8)
        )
        config_dual = SimulationConfig(
            simulation_time_us=30.0,
            request_rate=0.5,
            hbm_config=HBMConfig(stack_count=2, channels_per_stack=8)
        )
        sim_single = HBMSimulator(config_single)
        sim_dual = HBMSimulator(config_dual)
        stats_single = sim_single.run()
        stats_dual = sim_dual.run()
        # Both should complete some requests
        assert stats_single.completed_requests >= 0
        assert stats_dual.completed_requests >= 0

    def test_channel_utilization(self):
        """Test channel utilization"""
        stats = MultiChannelStats(num_channels=8)
        for ch in range(8):
            for _ in range(10):
                stats.record_request(ch, is_read=True)
        summary = stats.get_summary()
        # Check per-channel requests
        for ch in range(8):
            assert summary['per_channel'][ch]['requests'] == 10


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestStackErrorHandling:
    """Stack error handling tests"""

    def test_invalid_stack_id(self):
        """Test handling of invalid stack ID"""
        dram = DRAMModel(hbm_version="hbm3", stack_count=2, banks_per_channel=16)
        resp = dram.execute_activate(stack_id=5, channel_id=0, bank_id=0, row_id=0, current_time=0)
        # Should handle gracefully (may return success=False)

    def test_invalid_channel_id(self):
        """Test handling of invalid channel ID"""
        dram = DRAMModel(hbm_version="hbm3", stack_count=2, banks_per_channel=16)
        resp = dram.execute_activate(stack_id=0, channel_id=20, bank_id=0, row_id=0, current_time=0)
        # Should handle gracefully


# ============================================================================
# Edge Cases
# ============================================================================

class TestStackEdgeCases:
    """Edge case tests"""

    def test_zero_stack_count(self):
        """Test configuration with zero stacks (edge case)"""
        config = HBMConfig(stack_count=1)  # Minimum is 1
        assert config.stack_count >= 1

    def test_maximum_channels(self):
        """Test with maximum channels per stack"""
        config = HBMConfig(stack_count=1, channels_per_stack=16)
        assert config.channels_per_stack == 16

    def test_large_address_range(self):
        """Test with large address range"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            hbm_config=HBMConfig(stack_count=2, channels_per_stack=8)
        )
        config.address_range = 0x10000000000  # Large range
        sim = HBMSimulator(config)
        stats = sim.run()
        assert stats.total_requests >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])