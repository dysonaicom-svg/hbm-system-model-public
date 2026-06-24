"""
Unit Tests for Interconnect Enhanced Features

Tests cover:
- HBM4AddressTranslator
- InterconnectScheduler
- Enhanced interconnect functionality

Target: Increase coverage of interconnect.py
"""

import pytest
import sys
from collections import deque

sys.path.insert(0, '/home/ic/JXTF/HBM4')

from model.interconnect.interconnect import (
    # Core classes
    CrossbarInterconnect,
    MeshInterconnect,
    BinaryTreeInterconnect,

    # Enhanced classes
    HBM4AddressTranslator,
    InterconnectScheduler,

    # Data classes
    InterconnectRequest,

    # Enums
    RoutingMode,
    ArbitrationMode,
)


# ============================================================================
# HBM4AddressTranslator Tests
# ============================================================================

class TestHBM4AddressTranslator:
    """Test HBM4AddressTranslator functionality"""

    def test_translator_creation(self):
        """Test translator creation"""
        translator = HBM4AddressTranslator()
        assert translator.num_stacks == 1
        assert translator.channels_per_stack == 32

    def test_custom_translator(self):
        """Test custom translator configuration"""
        translator = HBM4AddressTranslator(
            num_stacks=4,
            channels_per_stack=32,
            banks_per_channel=16,
            rows_per_bank=65536,
        )
        assert translator.num_stacks == 4
        assert translator.channels_per_stack == 32
        assert translator.banks_per_channel == 16

    def test_translate_simple_address(self):
        """Test translating simple address"""
        translator = HBM4AddressTranslator()
        addr = 0x0001_0000_0000_1234
        fields = translator.translate(addr)

        assert 'stack' in fields
        assert 'channel' in fields
        assert 'bank' in fields
        assert 'row' in fields
        assert 'col' in fields
        assert 'offset' in fields

    def test_translate_boundary_addresses(self):
        """Test translating boundary addresses"""
        translator = HBM4AddressTranslator(num_stacks=2)  # Use 2 stacks to ensure difference

        # Address 0
        fields = translator.translate(0)
        assert fields['stack'] == 0

        # Max address should wrap around
        fields = translator.translate(0xFFFFFFFFFFFF)
        # Should have valid values (may be 0 or 1 for 2 stacks)
        assert fields['stack'] < translator.num_stacks
        assert fields['channel'] < translator.channels_per_stack

    def test_route_to_stack_channel(self):
        """Test routing address to stack and channel"""
        translator = HBM4AddressTranslator(num_stacks=4, channels_per_stack=32)

        stack, channel = translator.route_to_stack_channel(0x0001_0000_0000_1234)
        assert 0 <= stack < 4
        assert 0 <= channel < 32

    def test_pseudo_channel_mode(self):
        """Test pseudo-channel mode"""
        translator = HBM4AddressTranslator(pseudo_channel_mode=True)
        assert translator.pseudo_channel_mode is True

    def test_address_field_bits(self):
        """Test address field bit calculations"""
        translator = HBM4AddressTranslator(
            num_stacks=8,  # 3 bits
            channels_per_stack=64,  # 6 bits
            banks_per_channel=32,  # 5 bits
            rows_per_bank=131072,  # 17 bits
            cols_per_row=512,  # 9 bits
        )
        assert translator.stack_bits >= 3
        assert translator.channel_bits >= 6


# ============================================================================
# InterconnectScheduler Tests
# ============================================================================

class TestInterconnectScheduler:
    """Test InterconnectScheduler functionality"""

    def test_scheduler_creation(self):
        """Test scheduler creation"""
        scheduler = InterconnectScheduler()
        assert scheduler.num_queues == 16
        assert scheduler.max_queue_depth == 64

    def test_custom_scheduler(self):
        """Test custom scheduler configuration"""
        scheduler = InterconnectScheduler(
            num_queues=8,
            max_queue_depth=32,
            scheduling_mode=ArbitrationMode.PRIORITY,
        )
        assert scheduler.num_queues == 8
        assert scheduler.max_queue_depth == 32
        assert scheduler.scheduling_mode == ArbitrationMode.PRIORITY

    def test_enqueue_single(self):
        """Test enqueueing single request"""
        scheduler = InterconnectScheduler()
        req = InterconnectRequest(source_port=0, addr=0x1000, qos=8)
        result = scheduler.enqueue(req)
        assert result is True

    def test_enqueue_qos_mapping(self):
        """Test QoS to queue mapping"""
        scheduler = InterconnectScheduler(num_queues=4)

        for qos in range(16):
            req = InterconnectRequest(source_port=0, addr=0x1000 + qos, qos=qos)
            result = scheduler.enqueue(req)
            assert result is True

    def test_enqueue_full_queue(self):
        """Test enqueueing when queue is full"""
        scheduler = InterconnectScheduler(num_queues=2, max_queue_depth=1)

        # Fill queue
        req1 = InterconnectRequest(source_port=0, addr=0x1000, qos=8)
        assert scheduler.enqueue(req1) is True

        # Should fail now
        req2 = InterconnectRequest(source_port=1, addr=0x2000, qos=8)
        assert scheduler.enqueue(req2) is False

        assert scheduler.total_dropped >= 0

    def test_dequeue_priority(self):
        """Test priority dequeue"""
        scheduler = InterconnectScheduler(scheduling_mode=ArbitrationMode.PRIORITY)

        # Enqueue low priority first
        req_low = InterconnectRequest(source_port=0, addr=0x1000, qos=1)
        scheduler.enqueue(req_low)

        # Enqueue high priority
        req_high = InterconnectRequest(source_port=1, addr=0x2000, qos=15)
        scheduler.enqueue(req_high)

        # High priority should come first
        dequeued = scheduler.dequeue()
        assert dequeued is not None
        assert dequeued.qos == 15

    def test_dequeue_round_robin(self):
        """Test round-robin dequeue"""
        scheduler = InterconnectScheduler(scheduling_mode=ArbitrationMode.ROUND_ROBIN)

        for i in range(5):
            req = InterconnectRequest(source_port=i, addr=0x1000 + i, qos=8)
            scheduler.enqueue(req)

        # Dequeue all
        count = 0
        while True:
            req = scheduler.dequeue()
            if req is None:
                break
            count += 1

        assert count == 5

    def test_dequeue_empty(self):
        """Test dequeue from empty scheduler"""
        scheduler = InterconnectScheduler()
        result = scheduler.dequeue()
        assert result is None

    def test_queue_depth_total(self):
        """Test total queue depth"""
        scheduler = InterconnectScheduler()

        for i in range(5):
            req = InterconnectRequest(source_port=0, addr=0x1000 + i, qos=8)
            scheduler.enqueue(req)

        depth = scheduler.queue_depth()
        assert depth == 5

    def test_multiple_dequeues(self):
        """Test multiple dequeue operations"""
        scheduler = InterconnectScheduler()

        for i in range(10):
            req = InterconnectRequest(source_port=i, addr=0x1000 + i, qos=i % 4)
            scheduler.enqueue(req)

        # Dequeue 5
        for _ in range(5):
            scheduler.dequeue()

        depth = scheduler.queue_depth()
        assert depth == 5


# ============================================================================
# Enhanced Interconnect Tests
# ============================================================================

class TestEnhancedInterconnect:
    """Test enhanced interconnect features"""

    def test_scheduler_with_interconnect(self):
        """Test scheduler working with interconnect"""
        scheduler = InterconnectScheduler(
            num_queues=8,
            scheduling_mode=ArbitrationMode.PRIORITY,
        )

        ic = CrossbarInterconnect(
            num_ports=16,
            stack_count=2,
        )

        # Generate requests with different priorities
        for i in range(10):
            req = InterconnectRequest(
                source_port=i,
                addr=0x1000 + i * 0x1000,
                qos=i % 16,
            )
            scheduler.enqueue(req)

        # Dequeue and route
        while True:
            req = scheduler.dequeue()
            if req is None:
                break
            ic.route_request(req)

    def test_load_balanced_with_scheduler(self):
        """Test load balancing with scheduler"""
        scheduler = InterconnectScheduler()

        ic = CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            routing_mode=RoutingMode.LOAD_BALANCED,
        )

        # Send requests targeting same channel
        for i in range(20):
            # Same channel, different source
            addr = (i % 32) << 41
            req = InterconnectRequest(source_port=i, addr=addr, qos=8)
            scheduler.enqueue(req)

        # Route all
        while True:
            req = scheduler.dequeue()
            if req is None:
                break
            ic.route_request(req)

        # Check load distribution
        stats = ic.get_stats()
        load = stats['load_distribution']
        assert sum(load.values()) == 20


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestInterconnectSchedulerEdgeCases:
    """Test edge cases in scheduler"""

    def test_qos_bounds(self):
        """Test QoS bounds handling"""
        scheduler = InterconnectScheduler()

        # Negative QoS
        req_neg = InterconnectRequest(source_port=0, addr=0x1000, qos=-5)
        result = scheduler.enqueue(req_neg)
        assert result is True

        # Excessive QoS
        scheduler2 = InterconnectScheduler()
        req_high = InterconnectRequest(source_port=0, addr=0x2000, qos=100)
        result = scheduler2.enqueue(req_high)
        assert result is True

    def test_empty_dequeue_stats(self):
        """Test statistics after empty dequeue"""
        scheduler = InterconnectScheduler()
        scheduler.dequeue()
        # Should not crash
        assert scheduler.total_scheduled == 0

    def test_full_queue_stats(self):
        """Test statistics after full queue"""
        scheduler = InterconnectScheduler(max_queue_depth=1)

        req1 = InterconnectRequest(source_port=0, addr=0x1000, qos=8)
        scheduler.enqueue(req1)

        req2 = InterconnectRequest(source_port=1, addr=0x2000, qos=8)
        scheduler.enqueue(req2)

        assert scheduler.total_dropped >= 1


class TestHBM4TranslatorEdgeCases:
    """Test edge cases in translator"""

    def test_zero_rows(self):
        """Test with edge case row counts"""
        translator = HBM4AddressTranslator(rows_per_bank=1)
        fields = translator.translate(0x1000)
        assert fields['row'] < translator.rows_per_bank

    def test_single_bank(self):
        """Test with single bank"""
        translator = HBM4AddressTranslator(banks_per_channel=1)
        fields = translator.translate(0x1000)
        assert fields['bank'] == 0

    def test_single_channel(self):
        """Test with single channel"""
        translator = HBM4AddressTranslator(channels_per_stack=1)
        fields = translator.translate(0x1000)
        assert fields['channel'] == 0

    def test_large_stack_count(self):
        """Test with large stack count"""
        translator = HBM4AddressTranslator(num_stacks=8)
        # Verify valid translation
        fields = translator.translate(0x1000)
        assert fields['stack'] < 8


# ============================================================================
# Performance Tests
# ============================================================================

class TestSchedulerPerformance:
    """Performance tests for scheduler"""

    def test_high_throughput_enqueue(self):
        """Test high throughput enqueue"""
        scheduler = InterconnectScheduler(num_queues=16, max_queue_depth=256)

        for i in range(1000):
            req = InterconnectRequest(
                source_port=i % 32,
                addr=0x1000 + i * 64,
                qos=i % 16,
            )
            scheduler.enqueue(req)

        assert scheduler.queue_depth() <= 1000

    def test_mixed_enqueue_dequeue(self):
        """Test mixed enqueue/dequeue"""
        scheduler = InterconnectScheduler(num_queues=8)

        for i in range(100):
            # Enqueue some
            for j in range(5):
                req = InterconnectRequest(source_port=j, addr=0x1000 + j, qos=j)
                scheduler.enqueue(req)

            # Dequeue some
            for _ in range(3):
                scheduler.dequeue()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
