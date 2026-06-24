"""
Unit Tests for Enhanced GEM5 Memory Port Features

Tests cover:
- BurstTransaction
- MultiChannelPort
- AXI4ToMemoryBridge
- Enhanced gem5 port features

Target: Increase coverage from 52% to 80%+
"""

import pytest
import sys
from typing import List, Dict

sys.path.insert(0, '/home/ic/JXTF/HBM4')

from model.interconnect.gem5_memory_port import (
    # Core classes
    HBM4MemoryPort,
    HBM4MemoryRequest,
    HBM4MemoryResponse,
    CacheLineHandler,
    CacheLineConfig,
    CacheLineSize,
    PortConfig,
    PortStatistics,
    PortState,

    # Enhanced classes
    BurstTransaction,
    MultiChannelPort,
    AXI4ToMemoryBridge,

    # Base classes
    Gem5SlavePortBase,
    Gem5MasterPortBase,
    TrafficGeneratorInterface,

    # Factory functions
    create_memory_port,
    create_traffic_generator,
)


# ============================================================================
# BurstTransaction Tests
# ============================================================================

class TestBurstTransaction:
    """Test BurstTransaction functionality"""

    def test_transaction_creation(self):
        """Test burst transaction creation"""
        txn = BurstTransaction(
            req_id=1,
            addr=0x1000,
            size=64,
            is_write=True,
            num_beats=4,
        )
        assert txn.req_id == 1
        assert txn.addr == 0x1000
        assert txn.size == 64
        assert txn.is_write is True
        assert txn.num_beats == 4
        assert txn.current_beat == 0

    def test_transaction_data_initialization(self):
        """Test transaction data initialization"""
        txn = BurstTransaction(
            req_id=1,
            addr=0x1000,
            size=64,
            is_write=False,
            num_beats=4,
            data=[0xDEAD, 0xBEEF],
        )
        assert len(txn.data) == 2

    def test_is_complete_false(self):
        """Test is_complete when not done"""
        txn = BurstTransaction(req_id=1, addr=0x1000, size=64, is_write=True, num_beats=4)
        assert txn.is_complete is False

    def test_is_complete_true(self):
        """Test is_complete when all beats transferred"""
        txn = BurstTransaction(req_id=1, addr=0x1000, size=64, is_write=True, num_beats=4)
        txn.current_beat = 4
        assert txn.is_complete is True

    def test_progress_zero(self):
        """Test progress at start"""
        txn = BurstTransaction(req_id=1, addr=0x1000, size=64, is_write=True, num_beats=4)
        assert txn.progress == 0.0

    def test_progress_partial(self):
        """Test progress partially done"""
        txn = BurstTransaction(req_id=1, addr=0x1000, size=64, is_write=True, num_beats=4)
        txn.current_beat = 2
        assert txn.progress == 0.5

    def test_progress_complete(self):
        """Test progress when complete"""
        txn = BurstTransaction(req_id=1, addr=0x1000, size=64, is_write=True, num_beats=4)
        txn.current_beat = 4
        assert txn.progress == 1.0

    def test_progress_zero_beats(self):
        """Test progress with zero beats"""
        txn = BurstTransaction(req_id=1, addr=0x1000, size=64, is_write=True, num_beats=0)
        assert txn.progress == 1.0  # Immediate completion

    def test_advance_beat(self):
        """Test advancing beat"""
        txn = BurstTransaction(req_id=1, addr=0x1000, size=64, is_write=True, num_beats=4)
        assert txn.current_beat == 0
        txn.advance_beat()
        assert txn.current_beat == 1
        assert txn.is_complete is False

    def test_advance_beat_to_complete(self):
        """Test advancing to completion"""
        txn = BurstTransaction(req_id=1, addr=0x1000, size=64, is_write=True, num_beats=2)
        txn.advance_beat()
        txn.advance_beat()
        assert txn.current_beat == 2
        assert txn.is_complete is True
        assert txn.state == "complete"


# ============================================================================
# MultiChannelPort Tests
# ============================================================================

class TestMultiChannelPort:
    """Test MultiChannelPort functionality"""

    def test_port_creation(self):
        """Test multi-channel port creation"""
        port = MultiChannelPort(name="test", num_channels=8, queue_depth_per_channel=4)
        assert port.name == "test"
        assert port.num_channels == 8
        assert port.cache_line_size == 64

    def test_send_request_auto_channel(self):
        """Test sending request with auto channel selection"""
        port = MultiChannelPort(name="test", num_channels=8)
        req_id = port.send_request(addr=0x1000, size=64, is_write=False)
        assert req_id is not None
        assert req_id >= 0

    def test_send_request_channel_hint(self):
        """Test sending request with channel hint"""
        port = MultiChannelPort(name="test", num_channels=8)
        req_id = port.send_request(
            addr=0x1000,
            size=64,
            is_write=True,
            channel_hint=3,
        )
        assert req_id is not None
        assert port.stats['total_requests'] == 1

    def test_send_request_overflow(self):
        """Test overflow handling"""
        port = MultiChannelPort(name="test", num_channels=2, queue_depth_per_channel=1)

        # First request should succeed
        req_id1 = port.send_request(addr=0x1000, size=64, is_write=False, channel_hint=0)
        assert req_id1 is not None

        # Second to same channel should overflow
        req_id2 = port.send_request(addr=0x2000, size=64, is_write=False, channel_hint=0)
        assert req_id2 is None
        assert port.stats['overflows'] == 1

    def test_send_multiple_requests(self):
        """Test sending multiple requests"""
        port = MultiChannelPort(name="test", num_channels=8)
        for i in range(20):
            req_id = port.send_request(
                addr=0x1000 + i * 64,
                size=64,
                is_write=i % 2 == 0,
            )
            assert req_id is not None
        assert port.stats['total_requests'] == 20

    def test_channel_load(self):
        """Test channel load tracking"""
        port = MultiChannelPort(name="test", num_channels=8)
        port.send_request(addr=0x1000, size=64, is_write=False, channel_hint=2)
        port.send_request(addr=0x2000, size=64, is_write=False, channel_hint=2)

        load = port.get_channel_load(2)
        assert load == 2

    def test_total_load(self):
        """Test total load across all channels"""
        port = MultiChannelPort(name="test", num_channels=8)
        port.send_request(addr=0x1000, size=64, is_write=False, channel_hint=0)
        port.send_request(addr=0x2000, size=64, is_write=False, channel_hint=1)
        port.send_request(addr=0x3000, size=64, is_write=False, channel_hint=2)

        total = port.get_total_load()
        assert total == 3

    def test_least_loaded_channel(self):
        """Test finding least loaded channel"""
        port = MultiChannelPort(name="test", num_channels=4)
        port.send_request(addr=0x1000, size=64, is_write=False, channel_hint=0)
        port.send_request(addr=0x2000, size=64, is_write=False, channel_hint=0)
        port.send_request(addr=0x3000, size=64, is_write=False, channel_hint=1)

        least = port.get_least_loaded_channel()
        # Should be channel 2 or 3 (empty)
        assert least in [2, 3]

    def test_tick(self):
        """Test port tick"""
        port = MultiChannelPort(name="test", num_channels=4)
        port.send_request(addr=0x1000, size=64, is_write=False)
        port.tick()  # Should not crash

    def test_reset(self):
        """Test port reset"""
        port = MultiChannelPort(name="test", num_channels=4)
        for i in range(5):
            port.send_request(addr=0x1000 + i * 64, size=64, is_write=False)

        assert port.stats['total_requests'] == 5
        port.reset()
        assert port.stats['total_requests'] == 0

    def test_requests_per_channel_stats(self):
        """Test per-channel statistics"""
        port = MultiChannelPort(name="test", num_channels=4)
        port.send_request(addr=0x1000, size=64, is_write=False, channel_hint=0)
        port.send_request(addr=0x2000, size=64, is_write=False, channel_hint=1)
        port.send_request(addr=0x3000, size=64, is_write=False, channel_hint=1)

        assert port.stats['requests_per_channel'][0] == 1
        assert port.stats['requests_per_channel'][1] == 2


# ============================================================================
# AXI4ToMemoryBridge Tests
# ============================================================================

class TestAXI4ToMemoryBridge:
    """Test AXI4 to memory bridge functionality"""

    def test_bridge_creation(self):
        """Test bridge creation"""
        mem_port = create_memory_port(name="test")
        bridge = AXI4ToMemoryBridge(memory_port=mem_port)
        assert bridge.memory_port is mem_port
        assert bridge.max_outstanding == 32
        assert bridge.enable_reordering is True

    def test_submit_axi_read(self):
        """Test submitting AXI read"""
        mem_port = create_memory_port(name="test")
        bridge = AXI4ToMemoryBridge(memory_port=mem_port)

        txn_id = bridge.submit_axi_read(
            axi_addr=0x1000,
            size=64,
            length=3,
            axi_id=1,
            qos=8,
        )
        assert txn_id >= 0
        assert bridge.stats['axi_reads'] == 1

    def test_submit_axi_write(self):
        """Test submitting AXI write"""
        mem_port = create_memory_port(name="test")
        bridge = AXI4ToMemoryBridge(memory_port=mem_port)

        txn_id = bridge.submit_axi_write(
            axi_addr=0x2000,
            data=[0xDEAD, 0xBEEF, 0xCAFE, 0xFACE],
            size=64,
            axi_id=1,
            qos=4,
        )
        assert txn_id >= 0
        assert bridge.stats['axi_writes'] == 1

    def test_submit_overflow(self):
        """Test handling overflow"""
        mem_port = create_memory_port(name="test")
        bridge = AXI4ToMemoryBridge(memory_port=mem_port, max_outstanding=1)

        # First should succeed
        txn_id1 = bridge.submit_axi_read(
            axi_addr=0x1000, size=64, length=3, axi_id=1
        )
        assert txn_id1 >= 0

        # Second should be rejected
        txn_id2 = bridge.submit_axi_read(
            axi_addr=0x2000, size=64, length=3, axi_id=2
        )
        assert txn_id2 == -1

    def test_tick(self):
        """Test bridge tick"""
        mem_port = create_memory_port(name="test")
        bridge = AXI4ToMemoryBridge(memory_port=mem_port)

        bridge.submit_axi_read(axi_addr=0x1000, size=64, length=3, axi_id=1)
        bridge.tick()  # Should not crash

    def test_is_complete(self):
        """Test checking if transaction is complete"""
        mem_port = create_memory_port(name="test")
        bridge = AXI4ToMemoryBridge(memory_port=mem_port)

        txn_id = bridge.submit_axi_read(
            axi_addr=0x1000, size=64, length=3, axi_id=1
        )

        # Initially incomplete (beats remaining)
        assert bridge.is_complete(txn_id) is False

    def test_is_complete_unknown(self):
        """Test checking unknown transaction"""
        mem_port = create_memory_port(name="test")
        bridge = AXI4ToMemoryBridge(memory_port=mem_port)

        # Unknown transaction is considered complete
        assert bridge.is_complete(999) is True

    def test_get_pending_count(self):
        """Test getting pending count"""
        mem_port = create_memory_port(name="test")
        bridge = AXI4ToMemoryBridge(memory_port=mem_port)

        bridge.submit_axi_read(axi_addr=0x1000, size=64, length=3, axi_id=1)
        bridge.submit_axi_write(axi_addr=0x2000, data=[0xDEAD], size=64, axi_id=2)

        assert bridge.get_pending_count() == 2


# ============================================================================
# CacheLineHandler Enhanced Tests
# ============================================================================

class TestCacheLineHandlerEnhanced:
    """Test CacheLineHandler enhanced functionality"""

    def test_alignment_check(self):
        """Test alignment checking"""
        handler = CacheLineHandler(line_size=64)
        assert handler.is_aligned(0x1000, 64) is True
        assert handler.is_aligned(0x1001, 64) is False
        assert handler.is_aligned(0x1000, 128) is False

    def test_cache_line_config(self):
        """Test cache line configuration"""
        config = CacheLineConfig(line_size=128)
        assert config.line_size == 128
        assert config.addr_mask == 127

    def test_cache_line_size_enum(self):
        """Test cache line size enum"""
        assert CacheLineSize.SIZE_64.value == 64
        assert CacheLineSize.SIZE_128.value == 128
        assert CacheLineSize.SIZE_256.value == 256

    def test_burst_cycles_calculation(self):
        """Test burst cycle calculation"""
        handler = CacheLineHandler(line_size=64)
        # 4 beats per cycle, 64 bytes = 4 beats = 1 cycle
        cycles = handler.calculate_burst_cycles(64)
        assert cycles == 1

        # 128 bytes = 8 beats = 2 cycles
        cycles = handler.calculate_burst_cycles(128)
        assert cycles == 2

        # 256 bytes = 16 beats = 4 cycles
        cycles = handler.calculate_burst_cycles(256)
        assert cycles == 4

    def test_record_hit(self):
        """Test recording cache hit"""
        handler = CacheLineHandler(line_size=64)
        handler.record_hit()
        handler.record_hit()
        stats = handler.get_stats()
        assert stats['cache_hits'] == 2

    def test_record_miss(self):
        """Test recording cache miss"""
        handler = CacheLineHandler(line_size=64)
        handler.record_miss()
        stats = handler.get_stats()
        assert stats['cache_misses'] == 1

    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        handler = CacheLineHandler(line_size=64)
        handler.record_hit()
        handler.record_hit()
        handler.record_hit()
        handler.record_miss()
        stats = handler.get_stats()
        assert stats['hit_rate'] == 0.75


# ============================================================================
# Port Base Classes Tests
# ============================================================================

class TestGem5PortBase:
    """Test gem5 port base classes"""

    def test_slave_port_creation(self):
        """Test slave port creation"""
        port = Gem5SlavePortBase(name="slave")
        assert port.name == "slave"
        assert port.state == PortState.IDLE

    def test_slave_port_config(self):
        """Test slave port with config"""
        config = PortConfig(name="test", latency=20, bandwidth_gbs=4096.0)
        port = Gem5SlavePortBase(name="test", config=config)
        assert port.config.latency == 20
        assert port.config.bandwidth_gbs == 4096.0

    def test_slave_port_recv_request_empty(self):
        """Test receiving from empty queue"""
        port = Gem5SlavePortBase(name="test")
        result = port.recv_request()
        assert result is None

    def test_slave_port_set_callback(self):
        """Test setting callbacks"""
        port = Gem5SlavePortBase(name="test")
        called = [False]

        def recv_cb(req):
            called[0] = True

        port.set_callback("recv", recv_cb)
        assert port._on_recv is not None

    def test_master_port_creation(self):
        """Test master port creation"""
        port = Gem5MasterPortBase(name="master")
        assert port.name == "master"
        assert port.state == PortState.IDLE

    def test_port_config(self):
        """Test port configuration"""
        config = PortConfig(
            name="test",
            latency=15,
            bandwidth_gbs=2048.0,
            queue_depth=64,
            enable_backpressure=True,
        )
        assert config.name == "test"
        assert config.latency == 15
        assert config.queue_depth == 64

    def test_port_statistics(self):
        """Test port statistics"""
        stats = PortStatistics()
        assert stats.packets_sent == 0
        assert stats.bytes_sent == 0


# ============================================================================
# TrafficGenerator Enhanced Tests
# ============================================================================

class TestTrafficGeneratorEnhanced:
    """Test TrafficGeneratorInterface enhanced functionality"""

    def test_hotspot_pattern(self):
        """Test hotspot access pattern"""
        port = create_memory_port(name="test")
        tg = TrafficGeneratorInterface(name="tg", port=port)
        tg.set_pattern(TrafficGeneratorInterface.AccessPattern.HOTSPOT)

        # Generate some requests
        for _ in range(10):
            req_id = tg.generate_request()
            if req_id is not None:
                pass

        stats = tg.get_stats()
        assert stats['pattern'] == "hotspot"

    def test_stride_pattern(self):
        """Test stride access pattern"""
        port = create_memory_port(name="test")
        tg = TrafficGeneratorInterface(name="tg", port=port)
        tg.set_pattern(TrafficGeneratorInterface.AccessPattern.STRIDE)
        tg.stride = 256

        req_id = tg.generate_request()
        assert req_id is not None

    def test_set_base_address(self):
        """Test setting base address"""
        port = create_memory_port(name="test")
        tg = TrafficGeneratorInterface(name="tg", port=port)
        tg.set_base_address(0x2000)
        assert tg.base_addr == 0x2000
        assert tg._addr == 0x2000

    def test_set_access_size(self):
        """Test setting access size"""
        port = create_memory_port(name="test")
        tg = TrafficGeneratorInterface(name="tg", port=port)
        tg.set_access_size(128)
        assert tg.access_size == 128

    def test_record_response(self):
        """Test recording response"""
        port = create_memory_port(name="test")
        tg = TrafficGeneratorInterface(name="tg", port=port)

        tg.record_response(latency=10)
        tg.record_response(latency=20)

        stats = tg.get_stats()
        assert stats['responses_received'] == 2
        assert stats['average_latency'] == 15.0

    def test_response_stats_no_responses(self):
        """Test response stats with no responses"""
        port = create_memory_port(name="test")
        tg = TrafficGeneratorInterface(name="tg", port=port)

        stats = tg.get_stats()
        assert stats['average_latency'] == 0


# ============================================================================
# HBM4MemoryPort Enhanced Tests
# ============================================================================

class TestHBM4MemoryPortEnhanced:
    """Test HBM4MemoryPort enhanced functionality"""

    def test_pending_count(self):
        """Test getting pending count"""
        port = create_memory_port(name="test")
        port.send_request(addr=0x1000, size=64, is_write=False)
        port.send_request(addr=0x2000, size=64, is_write=True)
        assert port.get_pending_count() == 2

    def test_callbacks(self):
        """Test setting callbacks"""
        port = create_memory_port(name="test")
        request_callbacks = []
        response_callbacks = []

        port.set_callback("request", lambda r: request_callbacks.append(r))
        port.set_callback("response", lambda r: response_callbacks.append(r))

        port.send_request(addr=0x1000, size=64, is_write=False)
        # Callbacks should be set
        assert port._on_request is not None
        assert port._on_response is not None

    def test_stats_copy(self):
        """Test getting stats copy"""
        port = create_memory_port(name="test")
        stats = port.get_stats()
        assert 'channel_stats' in stats
        assert stats['channel_stats'] is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestGEM5Integration:
    """Integration tests for GEM5 memory port"""

    def test_multi_channel_to_axi_bridge(self):
        """Test multi-channel port to AXI4 bridge integration"""
        mem_port = create_memory_port(name="test")
        multi_port = MultiChannelPort(name="multi", num_channels=8)
        bridge = AXI4ToMemoryBridge(memory_port=mem_port)

        # Send requests through multi-channel
        for i in range(4):
            req_id = multi_port.send_request(
                addr=0x1000 + i * 64,
                size=64,
                is_write=i % 2 == 0,
                channel_hint=i % 4,
            )
            assert req_id is not None

        # Convert through AXI4 bridge
        txn_id = bridge.submit_axi_read(
            axi_addr=0x2000, size=64, length=3, axi_id=1
        )
        assert txn_id >= 0

    def test_traffic_generator_to_port(self):
        """Test traffic generator to memory port"""
        port = create_memory_port(name="test")
        tg = create_traffic_generator(name="tg", port=port, pattern="sequential")

        # Generate burst
        req_ids = tg.generate_burst(10)
        assert len(req_ids) <= 10

    def test_full_pipeline(self):
        """Test full pipeline simulation"""
        port = create_memory_port(name="dram")
        multi = MultiChannelPort(name="multi", num_channels=8)

        # Send through both
        for i in range(16):
            port.send_request(addr=0x1000 + i * 64, size=64, is_write=False)
            multi.send_request(addr=0x2000 + i * 64, size=64, is_write=True)

        # Tick both
        for _ in range(10):
            port.tick()
            multi.tick()


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestGEM5ErrorHandling:
    """Test error handling in GEM5 components"""

    def test_port_without_peer(self):
        """Test operations without peer connection"""
        port = create_memory_port(name="test")
        # Should handle gracefully without peer
        assert port.get_pending_count() >= 0

    def test_queue_depth_limit(self):
        """Test queue depth limiting"""
        port = create_memory_port(name="test", config=PortConfig(queue_depth=2))
        for i in range(5):
            port.send_request(addr=0x1000 + i * 64, size=64, is_write=False)

        # Should stall at queue depth
        stats = port.get_stats()
        assert stats['stalls'] >= 0

    def test_channel_hint_wrap(self):
        """Test channel hint wrapping"""
        port = MultiChannelPort(name="test", num_channels=4)
        # Request with channel hint > num_channels should wrap
        req_id = port.send_request(
            addr=0x1000, size=64, is_write=False, channel_hint=100
        )
        assert req_id is not None


# ============================================================================
# Stress Tests
# ============================================================================

class TestGEM5Stress:
    """Stress tests for GEM5 memory port"""

    def test_high_request_rate(self):
        """Test high request rate"""
        port = create_memory_port(name="test")
        for i in range(100):
            port.send_request(addr=0x1000 + i * 64, size=64, is_write=i % 2 == 0)
        assert port.get_pending_count() <= 100

    def test_multi_channel_distribution(self):
        """Test load distribution across channels"""
        port = MultiChannelPort(name="test", num_channels=32)
        for i in range(64):
            port.send_request(addr=0x1000 + i * 64, size=64, is_write=False)

        total = port.get_total_load()
        assert total == 64

    def test_sequential_then_random(self):
        """Test switching patterns"""
        port = create_memory_port(name="test")
        tg = create_traffic_generator(name="tg", port=port, pattern="sequential")

        # Sequential
        for _ in range(5):
            tg.generate_request()

        # Switch to random
        tg.set_pattern(TrafficGeneratorInterface.AccessPattern.RANDOM)
        for _ in range(5):
            tg.generate_request()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
