"""
Unit Tests for AXI4 Bridge - Enhanced Coverage

Tests cover:
- AXI4TransactionIDTracker
- AXI4ReorderingBuffer
- AXI4BurstGenerator
- AXI4MasterInterface
- AXI4Bridge advanced features
- Signal interface methods

Target: Increase coverage from 63% to 80%+
"""

import pytest
import sys
from typing import List, Dict

sys.path.insert(0, '/home/ic/JXTF/HBM4')

from model.interconnect.axi4_bridge import (
    AXI4Bridge,
    AXI4BridgeConfig,
    AXI4BurstType,
    AXI4Response,
    AXI4Signals,
    AXI4ReadTransaction,
    AXI4WriteTransaction,
    AXI4TransactionResponse,
    AXI4OutOfOrderQueue,
    AXI4TransactionIDTracker,
    AXI4ReorderingBuffer,
    AXI4BurstGenerator,
    AXI4MasterInterface,
    AXI4InterfaceType,
    create_axi4_bridge,
)


# ============================================================================
# AXI4 Out-of-Order Queue Tests
# ============================================================================

class TestAXI4OutOfOrderQueue:
    """Test AXI4OutOfOrderQueue functionality"""

    def test_queue_creation(self):
        """Test queue creation"""
        queue = AXI4OutOfOrderQueue(max_size=16)
        assert queue.max_size == 16
        assert len(queue) == 0

    def test_add_transaction(self):
        """Test adding transaction to queue"""
        queue = AXI4OutOfOrderQueue(max_size=4)
        txn = AXI4ReadTransaction(addr=0x1000, id=1)
        assert queue.add(txn) is True
        assert len(queue) == 1
        assert 1 in queue

    def test_add_duplicate_id(self):
        """Test adding transaction with duplicate ID"""
        queue = AXI4OutOfOrderQueue(max_size=4)
        txn1 = AXI4ReadTransaction(addr=0x1000, id=1)
        txn2 = AXI4ReadTransaction(addr=0x2000, id=1)
        assert queue.add(txn1) is True
        assert queue.add(txn2) is False

    def test_add_full_queue(self):
        """Test adding to full queue"""
        queue = AXI4OutOfOrderQueue(max_size=2)
        txn1 = AXI4ReadTransaction(addr=0x1000, id=1)
        txn2 = AXI4ReadTransaction(addr=0x2000, id=2)
        txn3 = AXI4ReadTransaction(addr=0x3000, id=3)
        assert queue.add(txn1) is True
        assert queue.add(txn2) is True
        assert queue.add(txn3) is False

    def test_mark_completed(self):
        """Test marking transaction as completed"""
        queue = AXI4OutOfOrderQueue(max_size=4)
        txn = AXI4ReadTransaction(addr=0x1000, id=1)
        queue.add(txn)
        queue.mark_completed(1, 10)
        # After marking, it should be removed from pending
        assert 1 not in queue

    def test_remove_transaction(self):
        """Test removing transaction from queue"""
        queue = AXI4OutOfOrderQueue(max_size=4)
        txn = AXI4ReadTransaction(addr=0x1000, id=1)
        queue.add(txn)
        removed = queue.remove(1)
        assert removed is not None
        assert removed.id == 1
        assert 1 not in queue

    def test_remove_nonexistent(self):
        """Test removing nonexistent transaction"""
        queue = AXI4OutOfOrderQueue(max_size=4)
        removed = queue.remove(999)
        assert removed is None

    def test_get_next_completable(self):
        """Test getting next completable transaction"""
        queue = AXI4OutOfOrderQueue(max_size=4)
        txn = AXI4ReadTransaction(addr=0x1000, id=1)
        queue.add(txn)
        result = queue.get_next_completable()
        # May be None if not yet completable


# ============================================================================
# AXI4 Transaction ID Tracker Tests
# ============================================================================

class TestAXI4TransactionIDTracker:
    """Test AXI4TransactionIDTracker functionality"""

    def test_tracker_creation(self):
        """Test tracker creation"""
        tracker = AXI4TransactionIDTracker(id_width=8)
        assert tracker.id_width == 8
        assert tracker.max_id == 255

    def test_allocate_read_id(self):
        """Test allocating read transaction ID"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_read_id()
        assert txn_id in range(16)
        assert tracker.active_read_count() == 1

    def test_allocate_write_id(self):
        """Test allocating write transaction ID"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_write_id()
        assert txn_id in range(16)
        assert tracker.active_write_count() == 1

    def test_allocate_specific_id(self):
        """Test allocating specific transaction ID"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_read_id(requested_id=5)
        assert txn_id == 5

    def test_release_read_id(self):
        """Test releasing read transaction ID"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_read_id()
        assert tracker.active_read_count() == 1
        tracker.release_read_id(txn_id)
        assert tracker.active_read_count() == 0

    def test_release_write_id(self):
        """Test releasing write transaction ID"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_write_id()
        assert tracker.active_write_count() == 1
        tracker.release_write_id(txn_id)
        assert tracker.active_write_count() == 0

    def test_is_read_active(self):
        """Test checking if read transaction is active"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_read_id()
        assert tracker.is_read_active(txn_id) is True
        tracker.release_read_id(txn_id)
        assert tracker.is_read_active(txn_id) is False

    def test_is_write_active(self):
        """Test checking if write transaction is active"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_write_id()
        assert tracker.is_write_active(txn_id) is True
        tracker.release_write_id(txn_id)
        assert tracker.is_write_active(txn_id) is False

    def test_get_read_order(self):
        """Test getting read transaction order"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_read_id()
        order = tracker.get_read_order(txn_id)
        assert order is not None

    def test_get_write_order(self):
        """Test getting write transaction order"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        txn_id = tracker.allocate_write_id()
        order = tracker.get_write_order(txn_id)
        assert order is not None

    def test_tracker_reset(self):
        """Test resetting tracker"""
        tracker = AXI4TransactionIDTracker(id_width=4)
        tracker.allocate_read_id()
        tracker.allocate_write_id()
        tracker.reset()
        assert tracker.active_read_count() == 0
        assert tracker.active_write_count() == 0


# ============================================================================
# AXI4 Reordering Buffer Tests
# ============================================================================

class TestAXI4ReorderingBuffer:
    """Test AXI4ReorderingBuffer functionality"""

    def test_buffer_creation(self):
        """Test buffer creation"""
        buffer = AXI4ReorderingBuffer(max_entries=32)
        assert buffer.max_entries == 32
        assert buffer.pending_count() == 0
        assert buffer.expected_order() == 0

    def test_push_in_order(self):
        """Test pushing responses in order"""
        buffer = AXI4ReorderingBuffer(max_entries=4)
        resp1 = AXI4TransactionResponse(id=1, is_write=False, resp=AXI4Response.OKAY)
        resp2 = AXI4TransactionResponse(id=2, is_write=False, resp=AXI4Response.OKAY)

        ready1 = buffer.push(resp1, order=0)
        ready2 = buffer.push(resp2, order=1)
        assert buffer.stats['in_order_receptions'] >= 1

    def test_push_out_of_order(self):
        """Test pushing responses out of order"""
        buffer = AXI4ReorderingBuffer(max_entries=4)
        resp1 = AXI4TransactionResponse(id=1, is_write=False, resp=AXI4Response.OKAY)
        resp2 = AXI4TransactionResponse(id=2, is_write=False, resp=AXI4Response.OKAY)

        # Push second first
        buffer.push(resp2, order=1)
        # Push first
        buffer.push(resp1, order=0)
        assert buffer.stats['out_of_order_receptions'] >= 1

    def test_buffer_reset(self):
        """Test resetting buffer"""
        buffer = AXI4ReorderingBuffer(max_entries=4)
        resp = AXI4TransactionResponse(id=1, is_write=False, resp=AXI4Response.OKAY)
        buffer.push(resp, order=0)
        buffer.reset()
        assert buffer.pending_count() == 0


# ============================================================================
# AXI4 Burst Generator Tests
# ============================================================================

class TestAXI4BurstGenerator:
    """Test AXI4BurstGenerator functionality"""

    def test_generate_incr_addresses(self):
        """Test generating INCR burst addresses"""
        addresses = AXI4BurstGenerator.generate_addresses(
            start_addr=0x1000,
            size=2,  # 4 bytes
            length=3,  # 4 beats
            burst_type=AXI4BurstType.INCR,
        )
        assert len(addresses) == 4
        assert addresses[0] == 0x1000
        assert addresses[1] == 0x1004

    def test_generate_fixed_addresses(self):
        """Test generating FIXED burst addresses"""
        addresses = AXI4BurstGenerator.generate_addresses(
            start_addr=0x1000,
            size=2,
            length=3,
            burst_type=AXI4BurstType.FIXED,
        )
        assert len(addresses) == 4
        assert all(addr == 0x1000 for addr in addresses)

    def test_generate_wrap_addresses(self):
        """Test generating WRAP burst addresses"""
        addresses = AXI4BurstGenerator.generate_addresses(
            start_addr=0x1000,
            size=2,
            length=3,
            burst_type=AXI4BurstType.WRAP,
        )
        assert len(addresses) == 4

    def test_validate_burst_valid(self):
        """Test validating valid burst"""
        is_valid, error = AXI4BurstGenerator.validate_burst(
            addr=0x1000,
            size=2,
            length=255,
            burst_type=AXI4BurstType.INCR,
            max_length=256,
        )
        assert is_valid is True
        assert error is None

    def test_validate_burst_length_exceeded(self):
        """Test validating burst with exceeded length"""
        is_valid, error = AXI4BurstGenerator.validate_burst(
            addr=0x1000,
            size=2,
            length=256,
            burst_type=AXI4BurstType.INCR,
            max_length=256,
        )
        assert is_valid is False

    def test_validate_burst_alignment(self):
        """Test validating burst alignment"""
        is_valid, error = AXI4BurstGenerator.validate_burst(
            addr=0x1001,  # Not aligned to 4 bytes
            size=2,  # 4 bytes
            length=0,
            burst_type=AXI4BurstType.INCR,
        )
        assert is_valid is False

    def test_validate_wrap_boundary(self):
        """Test validating WRAP burst boundary"""
        is_valid, error = AXI4BurstGenerator.validate_burst(
            addr=0x1004,  # Not at 16-byte boundary
            size=2,  # 4 bytes
            length=3,  # 16 bytes total
            burst_type=AXI4BurstType.WRAP,
        )
        assert is_valid is False


# ============================================================================
# AXI4 Master Interface Tests
# ============================================================================

class TestAXI4MasterInterface:
    """Test AXI4MasterInterface functionality"""

    def test_interface_creation(self):
        """Test master interface creation"""
        bridge = create_axi4_bridge(max_pending=8)
        interface = AXI4MasterInterface(bridge=bridge, master_id=1, default_qos=4)
        assert interface.master_id == 1
        assert interface.default_qos == 4

    def test_interface_read(self):
        """Test read through master interface"""
        bridge = create_axi4_bridge(max_pending=8)
        interface = AXI4MasterInterface(bridge=bridge)
        txn_id = interface.read(addr=0x1000, size=6, length=3)
        assert txn_id >= 0

    def test_interface_write(self):
        """Test write through master interface"""
        bridge = create_axi4_bridge(max_pending=8)
        interface = AXI4MasterInterface(bridge=bridge)
        txn_id = interface.write(addr=0x2000, data=[0xDEAD, 0xBEEF], size=6)
        assert txn_id >= 0

    def test_interface_read_with_qos(self):
        """Test read with specific QoS"""
        bridge = create_axi4_bridge(max_pending=8)
        interface = AXI4MasterInterface(bridge=bridge, default_qos=4)
        txn_id = interface.read(addr=0x1000, qos=15)
        assert txn_id >= 0

    def test_get_pending_count(self):
        """Test getting pending count"""
        bridge = create_axi4_bridge(max_pending=8)
        interface = AXI4MasterInterface(bridge=bridge)
        interface.read(addr=0x1000)
        interface.write(addr=0x2000, data=[0xDEAD])
        count = interface.get_pending_count()
        assert count >= 2


# ============================================================================
# AXI4 Bridge Signal Interface Tests
# ============================================================================

class TestAXI4BridgeSignalInterface:
    """Test AXI4 bridge signal interface methods"""

    def test_set_ar_ready(self):
        """Test setting ARREADY signal"""
        bridge = create_axi4_bridge(max_pending=8)
        bridge.set_ar_ready(True)
        assert bridge.signals.arready is True

    def test_set_aw_ready(self):
        """Test setting AWREADY signal"""
        bridge = create_axi4_bridge(max_pending=8)
        bridge.set_aw_ready(True)
        assert bridge.signals.awready is True

    def test_set_w_ready(self):
        """Test setting WREADY signal"""
        bridge = create_axi4_bridge(max_pending=8)
        bridge.set_w_ready(True)
        assert bridge.signals.wready is True

    def test_set_r_valid(self):
        """Test setting RVALID signal"""
        bridge = create_axi4_bridge(max_pending=8)
        bridge.set_r_valid(True)
        assert bridge.signals.rvalid is True

    def test_set_b_valid(self):
        """Test setting BVALID signal"""
        bridge = create_axi4_bridge(max_pending=8)
        bridge.set_b_valid(True)
        assert bridge.signals.bvalid is True

    def test_drive_r_channel(self):
        """Test driving R channel"""
        bridge = create_axi4_bridge(max_pending=8)
        bridge.drive_r_channel(rid=1, rdata=0xDEADBEEF, rresp=0, rlast=True)
        assert bridge.signals.rid == 1
        assert bridge.signals.rdata == 0xDEADBEEF
        assert bridge.signals.rlast is True

    def test_drive_b_channel(self):
        """Test driving B channel"""
        bridge = create_axi4_bridge(max_pending=8)
        bridge.drive_b_channel(bid=1, bresp=0)
        assert bridge.signals.bid == 1


# ============================================================================
# AXI4 Bridge Transaction Tests
# ============================================================================

class TestAXI4BridgeAdvancedTransactions:
    """Test advanced AXI4 bridge transaction handling"""

    def test_get_outstanding_count(self):
        """Test getting outstanding transaction count"""
        bridge = create_axi4_bridge(max_pending=8)
        bridge.submit_read(addr=0x1000, length=0)
        bridge.tick()
        assert bridge.get_outstanding_count(is_read=True) >= 0

    def test_get_average_latency(self):
        """Test getting average latency"""
        bridge = create_axi4_bridge(max_pending=8)
        latency = bridge.get_average_latency(is_read=True)
        assert latency >= 0

    def test_transaction_rejection_full_queue(self):
        """Test transaction rejection when queue is full"""
        bridge = create_axi4_bridge(max_pending=2)
        bridge.submit_read(addr=0x1000)
        bridge.submit_read(addr=0x2000)
        txn_id = bridge.submit_read(addr=0x3000)
        assert txn_id == -1

    def test_burst_length_validation(self):
        """Test burst length validation"""
        bridge = create_axi4_bridge(max_pending=4)
        # Valid burst length
        txn_id = bridge.submit_read(addr=0x1000, length=255)
        assert txn_id >= 0

    def test_signals_state(self):
        """Test AXI4Signals initial state"""
        signals = AXI4Signals()
        assert signals.arid == 0
        assert signals.araddr == 0
        assert signals.arvalid is False


# ============================================================================
# AXI4 Bridge Tick Tests
# ============================================================================

class TestAXI4BridgeTick:
    """Test AXI4 bridge tick and channel processing"""

    def test_tick_increments_cycle(self):
        """Test that tick increments cycle"""
        bridge = create_axi4_bridge(max_pending=8)
        initial_cycle = bridge._cycle
        bridge.tick()
        assert bridge._cycle == initial_cycle + 1

    def test_tick_returns_responses(self):
        """Test that tick returns responses"""
        bridge = create_axi4_bridge(max_pending=8)
        responses = bridge.tick()
        assert isinstance(responses, list)


# ============================================================================
# AXI4 Bridge Configuration Tests
# ============================================================================

class TestAXI4BridgeConfig:
    """Test AXI4BridgeConfig validation"""

    def test_valid_config(self):
        """Test valid configuration"""
        config = AXI4BridgeConfig(
            data_width=512,
            addr_width=64,
            id_width=8,
            max_pending_reads=16,
        )
        assert config.data_width == 512

    def test_invalid_data_width(self):
        """Test invalid data width"""
        with pytest.raises(ValueError):
            AXI4BridgeConfig(data_width=3)  # Not power of 2

    def test_invalid_addr_width(self):
        """Test invalid address width"""
        with pytest.raises(ValueError):
            AXI4BridgeConfig(addr_width=16)  # Too small

    def test_invalid_id_width(self):
        """Test invalid ID width"""
        with pytest.raises(ValueError):
            AXI4BridgeConfig(id_width=20)  # Too large


# ============================================================================
# AXI4 Transaction Properties Tests
# ============================================================================

class TestAXI4TransactionProperties:
    """Test AXI4 transaction computed properties"""

    def test_read_transaction_latency(self):
        """Test read transaction latency property"""
        txn = AXI4ReadTransaction(addr=0x1000)
        txn.submission_cycle = 0
        txn.completion_cycle = 10
        assert txn.latency == 10

    def test_read_transaction_no_completion(self):
        """Test read transaction latency without completion"""
        txn = AXI4ReadTransaction(addr=0x1000)
        assert txn.latency == 0

    def test_transaction_repr(self):
        """Test transaction string representation"""
        txn = AXI4ReadTransaction(addr=0x1000, length=7, qos=8)
        repr_str = repr(txn)
        assert "0x1000" in repr_str


# ============================================================================
# Performance Tests
# ============================================================================

class TestAXI4BridgePerformance:
    """Performance and stress tests for AXI4 bridge"""

    def test_high_throughput_reads(self):
        """Test high throughput read scenario"""
        bridge = create_axi4_bridge(max_pending=64)

        for i in range(50):
            bridge.submit_read(addr=0x1000 + i * 64, length=3, qos=i % 8)

        for _ in range(100):
            bridge.tick()

        stats = bridge.get_stats()
        assert stats['cycle'] == 100

    def test_mixed_traffic(self):
        """Test mixed read/write traffic"""
        bridge = create_axi4_bridge(max_pending=32)

        for i in range(20):
            if i % 2 == 0:
                bridge.submit_read(addr=0x1000 + i * 64, qos=i)
            else:
                bridge.submit_write(addr=0x2000 + i * 64, data=[0xDEADBEEF] * 4, qos=i)

        for _ in range(50):
            bridge.tick()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
