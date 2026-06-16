"""
gem5 Bridge Integration Tests
测试 HBM 仿真平台与 gem5 桥接功能

Tests:
1. Gem5Bridge instantiation and configuration
2. Mock gem5 integration
3. Request round-trip latency
4. Request/response handling
5. QoS handling
6. Error handling
"""

import pytest
import sys
import os
from typing import List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sim.interconnect.gem5_bridge import (
    Gem5Bridge,
    BridgeConfig,
    Gem5APIState,
    Gem5MockPort,
    Gem5MockSystem,
    create_bridge,
)
from sim.interconnect.gem5_types import (
    Gem5Request,
    Gem5Response,
    Gem5Transaction,
    Gem5CommandType,
    Gem5ResponseStatus,
    Gem5Address,
    create_read_request,
    create_write_request,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def default_bridge():
    """Create a bridge with default configuration"""
    bridge = Gem5Bridge()
    bridge.connect_to_gem5()
    yield bridge
    bridge.disconnect()


@pytest.fixture
def configured_bridge():
    """Create a bridge with custom configuration"""
    config = BridgeConfig(
        default_latency=20,
        max_pending_requests=128,
        enable_qos=True,
    )
    bridge = Gem5Bridge(config=config)
    bridge.connect_to_gem5()
    yield bridge
    bridge.disconnect()


@pytest.fixture
def mock_system():
    """Create a mock gem5 system"""
    return Gem5MockSystem()


# ============================================================================
# Test: Bridge Instantiation
# ============================================================================

class TestBridgeInstantiation:
    """Test bridge creation and configuration"""

    def test_create_bridge_default(self):
        """Test creating bridge with default config"""
        bridge = Gem5Bridge()
        assert bridge is not None
        assert bridge.state == Gem5APIState.DISCONNECTED

    def test_create_bridge_with_config(self):
        """Test creating bridge with custom config"""
        config = BridgeConfig(
            gem5_home="/path/to/gem5",
            default_latency=15,
            max_pending_requests=64,
        )
        bridge = Gem5Bridge(config=config)
        assert bridge.config.default_latency == 15
        assert bridge.config.max_pending_requests == 64

    def test_create_bridge_with_gem5_home(self):
        """Test creating bridge with gem5_home parameter"""
        bridge = Gem5Bridge(gem5_home="/path/to/gem5")
        assert bridge.config.gem5_home == "/path/to/gem5"

    def test_factory_function(self):
        """Test create_bridge factory function"""
        bridge = create_bridge(use_mock=True)
        assert bridge is not None
        assert bridge.state == Gem5APIState.CONNECTED
        bridge.disconnect()

    def test_context_manager(self):
        """Test bridge as context manager"""
        with Gem5Bridge() as bridge:
            assert bridge.state == Gem5APIState.CONNECTED
        assert bridge.state == Gem5APIState.DISCONNECTED


# ============================================================================
# Test: Connection Management
# ============================================================================

class TestConnectionManagement:
    """Test connection to gem5"""

    def test_connect_disconnect(self, default_bridge):
        """Test basic connect/disconnect cycle"""
        assert default_bridge.state == Gem5APIState.CONNECTED
        default_bridge.disconnect()
        assert default_bridge.state == Gem5APIState.DISCONNECTED

    def test_double_connect(self, default_bridge):
        """Test connecting when already connected"""
        result = default_bridge.connect_to_gem5()
        assert result is True
        assert default_bridge.state == Gem5APIState.CONNECTED

    def test_mock_system_setup(self, default_bridge):
        """Test mock system is properly set up"""
        assert default_bridge._mock_system is not None
        assert default_bridge._mock_port is not None
        assert default_bridge.master_port is not None


# ============================================================================
# Test: Request/Response Handling
# ============================================================================

class TestRequestResponse:
    """Test request and response handling"""

    def test_send_read_request(self, default_bridge):
        """Test sending a read request"""
        req_id = default_bridge.send_request(
            addr=0x1000,
            size=64,
            is_write=False,
        )
        assert req_id is not None
        assert req_id >= 0
        assert default_bridge.get_pending_count() == 1

    def test_send_write_request(self, default_bridge):
        """Test sending a write request"""
        data = [0xDEADBEEF, 0xCAFEBABE]
        req_id = default_bridge.send_request(
            addr=0x2000,
            size=16,
            is_write=True,
            data=data,
        )
        assert req_id is not None
        assert default_bridge.get_pending_count() == 1

    def test_send_multiple_requests(self, default_bridge):
        """Test sending multiple requests"""
        req_ids = []
        for i in range(5):
            req_id = default_bridge.send_request(
                addr=0x1000 + i * 0x100,
                size=64,
                is_write=False,
            )
            req_ids.append(req_id)

        assert len(req_ids) == 5
        assert all(rid is not None for rid in req_ids)
        assert default_bridge.get_pending_count() == 5

    def test_receive_response(self, default_bridge):
        """Test receiving a response"""
        req_id = default_bridge.send_request(
            addr=0x1000,
            size=64,
            is_write=False,
        )
        assert req_id is not None

        # Sync to allow response
        default_bridge.sync(cycle=100)

        resp = default_bridge.recv_response(req_id=req_id, timeout_cycles=100)
        assert resp is not None
        assert resp.req_id == req_id
        assert resp.status == Gem5ResponseStatus.OK

    def test_read_write_roundtrip(self, default_bridge):
        """Test complete read/write roundtrip"""
        # Write data
        write_data = [0x12345678, 0xABCDEF00]
        write_id = default_bridge.send_request(
            addr=0x3000,
            size=16,
            is_write=True,
            data=write_data,
        )
        default_bridge.sync(cycle=50)
        write_resp = default_bridge.recv_response(req_id=write_id, timeout_cycles=100)
        assert write_resp is not None

        # Read back
        read_id = default_bridge.send_request(
            addr=0x3000,
            size=16,
            is_write=False,
        )
        default_bridge.sync(cycle=100)
        read_resp = default_bridge.recv_response(req_id=read_id, timeout_cycles=100)
        assert read_resp is not None


# ============================================================================
# Test: Round-Trip Latency
# ============================================================================

class TestRoundTripLatency:
    """Test request round-trip latency"""

    def test_expected_latency(self, default_bridge):
        """Test that round-trip latency matches expected cycles"""
        # Send request
        req_id = default_bridge.send_request(
            addr=0x1000,
            size=64,
            is_write=False,
        )
        issue_cycle = default_bridge._current_cycle

        # Sync through expected latency + buffer
        expected_latency = default_bridge.config.default_latency
        default_bridge.sync(cycle=issue_cycle + expected_latency + 10)

        # Should receive response
        resp = default_bridge.recv_response(req_id=req_id, timeout_cycles=10)
        assert resp is not None
        assert resp.latency >= expected_latency

    def test_custom_latency(self, mock_system):
        """Test with custom latency configuration"""
        config = BridgeConfig(default_latency=25)
        bridge = Gem5Bridge(config=config)
        bridge.connect_to_gem5()

        # Set custom latency in mock system
        bridge._mock_system.set_latency(bridge.master_port.name, 25)

        req_id = bridge.send_request(addr=0x1000, size=64)
        bridge.sync(cycle=50)

        resp = bridge.recv_response(req_id=req_id, timeout_cycles=50)
        assert resp is not None
        # Response should arrive after 25 cycles minimum
        assert resp.latency >= 25

        bridge.disconnect()

    def test_burst_latency(self, default_bridge):
        """Test latency for burst transactions"""
        num_beats = 4
        beat_size = 64
        expected_latency = default_bridge.config.default_latency * num_beats

        req_id = default_bridge.send_request(
            addr=0x1000,
            size=beat_size * num_beats,
            is_write=False,
        )

        default_bridge.sync(cycle=expected_latency + 20)
        resp = default_bridge.recv_response(req_id=req_id, timeout_cycles=100)

        assert resp is not None
        assert resp.latency >= expected_latency

    def test_latency_statistics(self, default_bridge):
        """Test latency statistics tracking"""
        # Send multiple requests
        req_ids = []
        for i in range(5):
            req_id = default_bridge.send_request(
                addr=0x1000 + i * 0x100,
                size=64,
            )
            req_ids.append(req_id)

        # Process responses
        for req_id in req_ids:
            default_bridge.sync(cycle=1000)
            resp = default_bridge.recv_response(req_id=req_id, timeout_cycles=100)
            assert resp is not None

        stats = default_bridge.get_stats()
        assert stats["total_requests"] == 5
        assert stats["total_responses"] == 5
        assert stats["avg_latency"] > 0


# ============================================================================
# Test: QoS Handling
# ============================================================================

class TestQoSHandling:
    """Test QoS priority handling"""

    def test_qos_parameter(self, default_bridge):
        """Test QoS parameter is accepted"""
        req_id = default_bridge.send_request(
            addr=0x1000,
            size=64,
            qos=15,  # Highest priority
        )
        assert req_id is not None

        pending = default_bridge._pending_requests.get(req_id)
        assert pending is not None
        assert pending.request.qos == 15

    def test_multiple_qos_levels(self, default_bridge):
        """Test requests with different QoS levels"""
        qos_levels = [0, 4, 8, 15]
        req_ids = []

        for qos in qos_levels:
            req_id = default_bridge.send_request(
                addr=0x1000 + qos * 0x100,
                size=64,
                qos=qos,
            )
            req_ids.append((req_id, qos))

        for req_id, qos in req_ids:
            pending = default_bridge._pending_requests.get(req_id)
            assert pending is not None
            assert pending.request.qos == qos


# ============================================================================
# Test: High-Level Operations
# ============================================================================

class TestHighLevelOperations:
    """Test high-level read/write operations"""

    def test_read_method(self, default_bridge):
        """Test read() convenience method"""
        data = default_bridge.read(addr=0x1000, size=64)
        assert data is not None
        assert isinstance(data, list)

    def test_write_method(self, default_bridge):
        """Test write() convenience method"""
        data = [0xDEADBEEF, 0xCAFEBABE]
        result = default_bridge.write(addr=0x2000, data=data, size=16)
        assert result is True

    def test_burst_read(self, default_bridge):
        """Test burst_read() method"""
        responses = default_bridge.burst_read(
            addr=0x1000,
            num_beats=4,
            beat_size=64,
        )
        assert len(responses) == 4
        for resp in responses:
            assert resp.status == Gem5ResponseStatus.OK


# ============================================================================
# Test: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling"""

    def test_timeout_handling(self, configured_bridge):
        """Test request timeout handling"""
        # Send request
        req_id = configured_bridge.send_request(addr=0x1000, size=64)

        # Don't sync - request should timeout
        configured_bridge.sync(cycle=configured_bridge.config.request_timeout + 100)

        resp = configured_bridge.recv_response(req_id=req_id, timeout_cycles=10)
        assert resp is not None
        assert resp.status == Gem5ResponseStatus.TIMEOUT

    def test_disconnect_drains_requests(self, default_bridge):
        """Test disconnect drains pending requests"""
        # Send some requests
        for i in range(3):
            default_bridge.send_request(addr=0x1000 + i * 0x100, size=64)

        assert default_bridge.get_pending_count() == 3

        # Disconnect should drain
        default_bridge.disconnect()
        assert default_bridge.get_pending_count() == 0

    def test_max_pending_limit(self, default_bridge):
        """Test max pending requests limit"""
        max_requests = default_bridge.config.max_pending_requests

        # Send max requests
        for i in range(max_requests):
            req_id = default_bridge.send_request(addr=0x1000 + i * 0x100, size=64)
            assert req_id is not None

        # Try to exceed limit
        extra_id = default_bridge.send_request(addr=0xFFFF0000, size=64)
        assert extra_id is None


# ============================================================================
# Test: Statistics
# ============================================================================

class TestStatistics:
    """Test statistics tracking"""

    def test_stats_initialization(self, default_bridge):
        """Test stats are properly initialized"""
        stats = default_bridge.get_stats()
        assert stats["total_requests"] == 0
        assert stats["total_responses"] == 0
        assert stats["pending_requests"] == 0

    def test_stats_update(self, default_bridge):
        """Test stats update correctly"""
        # Send requests
        for i in range(3):
            default_bridge.send_request(addr=0x1000 + i * 0x100, size=64)

        stats = default_bridge.get_stats()
        assert stats["total_requests"] == 3

    def test_stats_reset(self, default_bridge):
        """Test reset_stats()"""
        # Generate some stats
        for i in range(5):
            default_bridge.send_request(addr=0x1000 + i * 0x100, size=64)
            default_bridge.sync(cycle=1000)
            default_bridge.recv_response(timeout_cycles=10)

        default_bridge.reset_stats()
        stats = default_bridge.get_stats()
        assert stats["total_requests"] == 0
        assert stats["total_responses"] == 0


# ============================================================================
# Test: Transaction Tracking
# ============================================================================

class TestTransactionTracking:
    """Test transaction state tracking"""

    def test_transaction_creation(self, default_bridge):
        """Test transaction is created for each request"""
        req_id = default_bridge.send_request(addr=0x1000, size=64)
        txn = default_bridge.get_transaction(req_id)

        assert txn is not None
        assert txn.state == "issued"
        assert txn.request.req_id == req_id

    def test_transaction_completion(self, default_bridge):
        """Test transaction state updates on completion"""
        req_id = default_bridge.send_request(addr=0x1000, size=64)
        default_bridge.sync(cycle=100)

        resp = default_bridge.recv_response(req_id=req_id)
        txn = default_bridge.get_transaction(req_id)

        # Transaction should be completed or in response map
        if txn:
            assert txn.state in ["completed", "failed"]


# ============================================================================
# Test: Mock gem5 System
# ============================================================================

class TestMockSystem:
    """Test mock gem5 system"""

    def test_mock_system_creation(self, mock_system):
        """Test mock system creation"""
        assert mock_system is not None
        assert mock_system.clock == 0

    def test_mock_system_tick(self, mock_system):
        """Test mock system tick"""
        mock_system.tick(cycles=100)
        assert mock_system.clock == 100

    def test_mock_port_connection(self, mock_system):
        """Test mock port connection"""
        port = Gem5MockPort("test_port", "master")
        mock_system.register_master_port("test_port", port)
        assert port.connected is True

    def test_mock_latency(self, mock_system):
        """Test mock latency configuration"""
        mock_system.set_latency("test_port", 20)
        assert mock_system.get_latency("test_port") == 20


# ============================================================================
# Test: Integration with AXI
# ============================================================================

class TestIntegrationWithAXI:
    """Test integration with AXI interconnect"""

    def test_bridge_with_axi_interconnect(self):
        """Test that gem5 bridge can work with AXI interconnect"""
        from sim.interconnect.axi import create_hbm_interconnect

        # Create AXI interconnect
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=1)

        # Create gem5 bridge
        bridge = Gem5Bridge()
        bridge.connect_to_gem5()

        # Both should coexist
        assert bridge.state == Gem5APIState.CONNECTED
        assert len(interconnect.masters) == 1

        bridge.disconnect()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])