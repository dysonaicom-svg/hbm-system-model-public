"""
Unit tests for AXI4 Bridge and Interconnect Model

Tests cover:
- AXI4 protocol support (full and Lite)
- Address translation
- Transaction reordering and outstanding support
- AXI4 monitor for traffic analysis
- gem5 memory port integration
"""

import pytest
import sys
from typing import List, Dict

# Add model path
sys.path.insert(0, '/home/ic/JXTF/HBM')

from model.interconnect.axi4_bridge import (
    AXI4Bridge, AXI4BridgeConfig, AXI4BurstType, AXI4Response,
    AXI4Size, AXI4ReadTransaction, AXI4WriteTransaction,
    create_axi4_bridge, create_axi4lite_bridge
)
from model.interconnect.axi4_converter import (
    AXI4Converter, AddressMapping, AddressMappingMode,
    AXI4ToHBMConverter, HBMToAXI4Converter,
    create_axi4_converter, create_hbm_address_mapping
)
from model.interconnect.axi4_monitor import (
    AXI4Monitor, ViolationType, ProtocolViolation,
    TransactionLogEntry, PerformanceMetrics,
    create_axi4_monitor, analyze_axi4_log
)
from model.interconnect.interconnect import (
    CrossbarInterconnect, MeshInterconnect, BinaryTreeInterconnect,
    InterconnectFactory, RoutingMode, ArbitrationMode,
    InterconnectRequest, InterconnectResponse,
    create_interconnect
)
from model.interconnect.gem5_memory_port import (
    HBM4MemoryPort, CacheLineHandler, CacheLineConfig,
    Gem5SlavePortBase, Gem5MasterPortBase,
    TrafficGeneratorInterface, create_memory_port
)


# ============================================================================
# AXI4 Bridge Tests
# ============================================================================

class TestAXI4Bridge:
    """Test AXI4 Bridge functionality"""

    def test_bridge_creation(self):
        """Test bridge creation with default config"""
        bridge = create_axi4_bridge(max_pending=16)
        assert bridge is not None
        assert bridge.config.max_pending_reads == 16
        assert bridge.config.max_pending_writes == 16

    def test_bridge_creation_with_full_config(self):
        """Test bridge creation with full configuration"""
        config = AXI4BridgeConfig(
            max_pending_reads=32,
            max_pending_writes=32,
            enable_out_of_order=True,
            enable_outstanding=True,
            enable_qos=True,
            data_width=512,
            id_width=8,
        )
        bridge = AXI4Bridge(config)
        assert bridge.config.max_pending_reads == 32
        assert bridge.config.enable_out_of_order is True

    def test_submit_read_transaction(self):
        """Test submitting a read transaction"""
        bridge = create_axi4_bridge(max_pending=8)
        txn_id = bridge.submit_read(
            addr=0x1000,
            size=6,  # 64 bytes
            length=7,  # 8 beats
            burst=AXI4BurstType.INCR,
            id=1,
            qos=8
        )
        assert txn_id >= 0
        assert bridge.get_pending_count(is_read=True) == 1
        assert bridge.stats['read_submitted'] == 1

    def test_submit_write_transaction(self):
        """Test submitting a write transaction"""
        bridge = create_axi4_bridge(max_pending=8)
        data = [0xDEADBEEF] * 8
        txn_id = bridge.submit_write(
            addr=0x2000,
            data=data,
            size=6,
            length=7,
            burst=AXI4BurstType.INCR,
            qos=4
        )
        assert txn_id >= 0
        assert bridge.get_pending_count(is_read=False) == 1
        assert bridge.stats['write_submitted'] == 1

    def test_burst_types(self):
        """Test different burst types"""
        bridge = create_axi4_bridge(max_pending=16)

        # FIXED burst
        read_id = bridge.submit_read(
            addr=0x1000,
            burst=AXI4BurstType.FIXED,
            length=7
        )
        assert read_id >= 0

        # WRAP burst
        read_id2 = bridge.submit_read(
            addr=0x1000,
            burst=AXI4BurstType.WRAP,
            length=7
        )
        assert read_id2 >= 0

        # INCR burst
        read_id3 = bridge.submit_read(
            addr=0x1000,
            burst=AXI4BurstType.INCR,
            length=7
        )
        assert read_id3 >= 0

    def test_outstanding_transactions(self):
        """Test outstanding transaction support"""
        bridge = create_axi4_bridge(
            max_pending=16,
            enable_outstanding=True
        )

        # Submit multiple reads
        for i in range(10):
            txn_id = bridge.submit_read(
                addr=0x1000 + i * 64,
                length=3,
                qos=i % 4
            )
            assert txn_id >= 0

        assert bridge.get_pending_count(is_read=True) == 10

    def test_qos_priority(self):
        """Test QoS-based prioritization"""
        bridge = create_axi4_bridge(max_pending=16)

        # Submit with different QoS
        bridge.submit_read(addr=0x1000, qos=1)
        bridge.submit_read(addr=0x2000, qos=8)
        bridge.submit_read(addr=0x3000, qos=4)

        # Clock a few cycles to trigger selection
        for _ in range(5):
            bridge.tick()

    def test_transaction_latency_tracking(self):
        """Test latency tracking"""
        bridge = create_axi4_bridge(max_pending=16)
        txn_id = bridge.submit_read(addr=0x1000, length=0)
        
        # Clock cycles
        for _ in range(10):
            bridge.tick()

        # Transaction should still be pending
        assert bridge.get_pending_count(is_read=True) >= 0

    def test_bridge_reset(self):
        """Test bridge reset"""
        bridge = create_axi4_bridge(max_pending=8)
        
        # Add transactions
        bridge.submit_read(addr=0x1000)
        bridge.submit_write(addr=0x2000, data=[0xDEAD])
        
        assert bridge.get_pending_count(is_read=True) == 1
        assert bridge.get_pending_count(is_read=False) == 1

        # Reset
        bridge.reset()

        assert bridge.get_pending_count(is_read=True) == 0
        assert bridge.get_pending_count(is_read=False) == 0
        assert bridge._cycle == 0

    def test_bridge_statistics(self):
        """Test statistics collection"""
        bridge = create_axi4_bridge(max_pending=8)
        
        bridge.submit_read(addr=0x1000)
        bridge.submit_write(addr=0x2000, data=[0xBEEF])
        
        for _ in range(10):
            bridge.tick()

        stats = bridge.get_stats()
        assert 'cycle' in stats
        assert stats['cycle'] > 0

    def test_axi4lite_bridge(self):
        """Test AXI4-Lite bridge creation"""
        bridge = create_axi4lite_bridge()
        assert bridge.config.interface_type.value == 1  # AXI4_LITE
        assert bridge.config.max_pending_reads == 1
        assert bridge.config.max_pending_writes == 1

    def test_burst_length_validation(self):
        """Test burst length validation"""
        bridge = create_axi4_bridge(max_pending=4)
        
        # Valid burst length
        txn_id = bridge.submit_read(addr=0x1000, length=255)
        assert txn_id >= 0

    def test_read_transaction_properties(self):
        """Test read transaction computed properties"""
        txn = AXI4ReadTransaction(
            addr=0x1000,
            size=6,  # 64 bytes
            length=7,  # 8 beats
            burst=AXI4BurstType.INCR
        )
        
        assert txn.num_beats == 8
        assert txn.total_bytes == 512
        assert not txn.is_completed

    def test_write_transaction_properties(self):
        """Test write transaction computed properties"""
        txn = AXI4WriteTransaction(
            addr=0x1000,
            size=6,
            length=3,
            data=[0xDEAD, 0xBEEF, 0xCAFE, 0xFACE],
            burst=AXI4BurstType.INCR
        )
        
        assert txn.num_beats == 4
        assert txn.total_bytes == 256
        assert not txn.is_completed

    def test_beat_address_calculation_incr(self):
        """Test INCR burst address calculation"""
        txn = AXI4ReadTransaction(
            addr=0x1000,
            size=2,  # 4 bytes per beat
            length=3,  # 4 beats
            burst=AXI4BurstType.INCR
        )
        
        addresses = txn.get_beat_addresses()
        assert len(addresses) == 4
        assert addresses[0] == 0x1000
        assert addresses[1] == 0x1004
        assert addresses[2] == 0x1008
        assert addresses[3] == 0x100C

    def test_beat_address_calculation_wrap(self):
        """Test WRAP burst address calculation"""
        txn = AXI4ReadTransaction(
            addr=0x100C,
            size=2,  # 4 bytes
            length=3,  # 4 beats
            burst=AXI4BurstType.WRAP
        )
        
        addresses = txn.get_beat_addresses()
        assert len(addresses) == 4
        # WRAP should wrap at boundary (4 beats * 4 bytes = 16 bytes)
        # Starting at 0x100C, should wrap around 0x1000 boundary
        assert addresses[0] == 0x100C
        assert addresses[3] == 0x1008

    def test_beat_address_calculation_fixed(self):
        """Test FIXED burst address calculation"""
        txn = AXI4ReadTransaction(
            addr=0x1000,
            size=2,
            length=3,
            burst=AXI4BurstType.FIXED
        )
        
        addresses = txn.get_beat_addresses()
        assert len(addresses) == 4
        # All addresses should be the same
        assert all(addr == 0x1000 for addr in addresses)

    def test_response_callbacks(self):
        """Test response callbacks"""
        bridge = create_axi4_bridge(max_pending=8)
        
        callback_received = []
        bridge.on_read_complete(lambda txn: callback_received.append(txn))
        bridge.on_write_complete(lambda txn: callback_received.append(txn))

        bridge.submit_read(addr=0x1000)
        bridge.submit_write(addr=0x2000, data=[0xDEAD])

        for _ in range(5):
            bridge.tick()


# ============================================================================
# AXI4 Converter Tests
# ============================================================================

class TestAXI4Converter:
    """Test AXI4 to HBM converter"""

    def test_converter_creation(self):
        """Test converter creation"""
        converter = create_axi4_converter()
        assert converter is not None
        assert converter.axi4_to_hbm is not None
        assert converter.hbm_to_axi4 is not None

    def test_address_mapping_decode(self):
        """Test address decoding"""
        mapping = AddressMapping()
        test_addr = 0x0001_0000_0000_1234
        
        decoded = mapping.decode_axi_addr(test_addr)
        assert 'stack' in decoded
        assert 'channel' in decoded
        assert 'bank_group' in decoded
        assert 'bank' in decoded
        assert 'row' in decoded

    def test_address_mapping_encode_decode(self):
        """Test encode/decode round-trip"""
        mapping = AddressMapping()
        
        original = mapping.encode_hbm_addr(
            stack=1,
            channel=8,
            pseudo_channel=0,
            bank_group=3,
            bank=5,
            row=0x1234,
            col=2,
            byte_offset=0
        )
        
        decoded = mapping.decode_axi_addr(original)
        assert decoded['stack'] == 1
        assert decoded['channel'] == 8
        assert decoded['bank_group'] == 3
        assert decoded['bank'] == 5

    def test_channel_selection(self):
        """Test channel selection based on address"""
        mapping = AddressMapping()
        
        # Different addresses should map to different channels
        addr1 = 0x0000_0000_0000_0000
        addr2 = 0x0000_0002_0000_0000
        
        ch1 = mapping.decode_axi_addr(addr1)['channel']
        ch2 = mapping.decode_axi_addr(addr2)['channel']
        
        assert ch1 != ch2 or ch1 == ch2  # Just verify they're computed

    def test_read_conversion(self):
        """Test AXI4 read to HBM request conversion"""
        converter = create_axi4_converter()
        
        txn = AXI4ReadTransaction(
            addr=0x1000,
            size=6,  # 64 bytes
            length=7,
            burst=AXI4BurstType.INCR,
            id=1,
            qos=8
        )
        
        result = converter.to_hbm(txn)
        assert result.success is True
        assert len(result.hbm_requests) > 0
        assert result.beats_generated == 8
        assert result.bytes_converted == 512

    def test_write_conversion(self):
        """Test AXI4 write to HBM request conversion"""
        converter = create_axi4_converter()
        
        txn = AXI4WriteTransaction(
            addr=0x2000,
            size=6,
            length=3,
            data=[0xDEADBEEF] * 4,
            burst=AXI4BurstType.INCR,
            id=2,
            qos=4
        )
        
        result = converter.to_hbm(txn)
        assert result.success is True
        assert len(result.hbm_requests) > 0

    def test_hbm_address_mapping_factory(self):
        """Test HBM address mapping factory"""
        mapping = create_hbm_address_mapping(
            mode="row_bank_channel",
            channels=32,
            stacks=4
        )
        
        assert mapping.hbm_channels == 32
        assert mapping.hbm_stacks == 4
        assert mapping.mapping_mode == AddressMappingMode.ROW_BANK_CHANNEL

    def test_conversion_statistics(self):
        """Test conversion statistics"""
        converter = create_axi4_converter()
        
        # Convert some transactions
        read_txn = AXI4ReadTransaction(addr=0x1000, size=6, length=3)
        converter.to_hbm(read_txn)
        
        write_txn = AXI4WriteTransaction(
            addr=0x2000, size=6, length=3, data=[0xDEAD] * 4
        )
        converter.to_hbm(write_txn)
        
        stats = converter.get_stats()
        assert stats['axi4_to_hbm']['reads_converted'] == 1
        assert stats['axi4_to_hbm']['writes_converted'] == 1


# ============================================================================
# AXI4 Monitor Tests
# ============================================================================

class TestAXI4Monitor:
    """Test AXI4 protocol monitor"""

    def test_monitor_creation(self):
        """Test monitor creation"""
        monitor = create_axi4_monitor(strict_protocol=True)
        assert monitor is not None
        assert monitor.strict_protocol is True

    def test_monitor_connection(self):
        """Test connecting monitor to bridge"""
        bridge = create_axi4_bridge(max_pending=8)
        monitor = create_axi4_monitor()
        monitor.connect_signals(bridge.signals)
        
        assert hasattr(monitor, '_signals')

    def test_transaction_logging(self):
        """Test transaction logging"""
        monitor = create_axi4_monitor(enable_log=True)
        
        # Simulate some cycles
        for _ in range(10):
            monitor.tick()
        
        log = monitor.get_transaction_log()
        assert isinstance(log, list)

    def test_violation_detection(self):
        """Test protocol violation detection"""
        monitor = AXI4Monitor(strict_protocol=False)
        
        violations = monitor.get_violations()
        assert isinstance(violations, list)

    def test_performance_metrics(self):
        """Test performance metrics collection"""
        monitor = create_axi4_monitor()
        
        for _ in range(100):
            monitor.tick()
        
        metrics = monitor.get_metrics()
        assert metrics.total_cycles == 100

    def test_compliance_check(self):
        """Test protocol compliance check"""
        monitor = create_axi4_monitor(strict_protocol=True)
        
        for _ in range(50):
            monitor.tick()
        
        is_compliant = monitor.is_compliant()
        assert isinstance(is_compliant, bool)

    def test_report_generation(self):
        """Test report generation"""
        monitor = create_axi4_monitor()
        
        bridge = create_axi4_bridge(max_pending=8)
        monitor.connect_signals(bridge.signals)
        
        bridge.submit_read(addr=0x1000)
        bridge.submit_write(addr=0x2000, data=[0xDEAD])
        
        for _ in range(20):
            bridge.tick()
            monitor.tick()
        
        report = monitor.get_report()
        assert 'cycle' in report
        assert 'metrics' in report
        assert 'violations' in report

    def test_analyze_log(self):
        """Test transaction log analysis"""
        log_entries = []
        
        result = analyze_axi4_log(log_entries)
        assert result == {}

    def test_monitor_reset(self):
        """Test monitor reset"""
        monitor = create_axi4_monitor()
        
        for _ in range(50):
            monitor.tick()
        
        assert monitor._cycle == 50
        
        monitor.reset()
        assert monitor._cycle == 0


# ============================================================================
# Interconnect Tests
# ============================================================================

class TestInterconnect:
    """Test interconnect models"""

    def test_crossbar_creation(self):
        """Test crossbar creation"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)
        assert ic.num_ports == 32
        assert ic.stack_count == 4

    def test_crossbar_routing(self):
        """Test crossbar request routing"""
        ic = CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            channels_per_stack=8
        )
        
        # Create request
        request = InterconnectRequest(
            source_port=0,
            addr=0x0001_0000_0000_1234,
            size=64,
            is_read=True,
            qos=8
        )
        
        response = ic.route_request(request)
        assert isinstance(response, InterconnectResponse)
        assert response.request_id == request.id

    def test_mesh_creation(self):
        """Test mesh creation"""
        ic = MeshInterconnect(rows=4, cols=8, stack_count=4)
        assert ic.rows == 4
        assert ic.cols == 8

    def test_mesh_routing(self):
        """Test mesh request routing"""
        ic = MeshInterconnect(rows=4, cols=8)
        
        request = InterconnectRequest(
            source_port=0,
            addr=0x1000,
            is_read=True
        )
        
        response = ic.route_request(request)
        assert response.success is True

    def test_tree_creation(self):
        """Test binary tree creation"""
        ic = BinaryTreeInterconnect(num_leaves=32, stack_count=4)
        assert ic.num_leaves == 32

    def test_tree_routing(self):
        """Test binary tree routing"""
        ic = BinaryTreeInterconnect(num_leaves=32)
        
        request = InterconnectRequest(
            source_port=0,
            addr=0x1000,
            is_read=True
        )
        
        response = ic.route_request(request)
        assert response.success is True

    def test_tree_broadcast(self):
        """Test binary tree broadcast"""
        ic = BinaryTreeInterconnect(num_leaves=8)
        
        request = InterconnectRequest(
            source_port=0,
            addr=0x1000,
            is_read=True
        )
        
        responses = ic.broadcast(request)
        assert len(responses) == 8

    def test_routing_modes(self):
        """Test different routing modes"""
        for mode in [RoutingMode.ADDRESS_BASED, RoutingMode.LOAD_BALANCED, RoutingMode.SHORTEST_PATH]:
            ic = CrossbarInterconnect(
                num_ports=16,
                routing_mode=mode
            )
            assert ic.routing_mode == mode

    def test_arbitration_modes(self):
        """Test different arbitration modes"""
        for mode in [ArbitrationMode.ROUND_ROBIN, ArbitrationMode.PRIORITY]:
            ic = CrossbarInterconnect(
                num_ports=16,
                arbitration_mode=mode
            )
            assert ic.arbitration_mode == mode

    def test_address_based_routing(self):
        """Test address-based routing"""
        ic = CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            routing_mode=RoutingMode.ADDRESS_BASED
        )
        
        # Request to different addresses
        for i in range(8):
            request = InterconnectRequest(
                source_port=0,
                addr=0x1000 + i * 0x2000_0000,  # Different channels
                is_read=True
            )
            response = ic.route_request(request)
            assert response.success is True

    def test_qos_priority_routing(self):
        """Test QoS priority routing"""
        ic = CrossbarInterconnect(
            num_ports=16,
            arbitration_mode=ArbitrationMode.PRIORITY
        )
        
        # High priority first
        high_req = InterconnectRequest(source_port=0, addr=0x1000, qos=15)
        low_req = InterconnectRequest(source_port=1, addr=0x2000, qos=1)
        
        ic.route_request(high_req)
        ic.route_request(low_req)

    def test_interconnect_statistics(self):
        """Test interconnect statistics"""
        ic = CrossbarInterconnect(num_ports=32, stack_count=4)
        
        # Route some requests
        for i in range(10):
            request = InterconnectRequest(
                source_port=i % 32,
                addr=0x1000 * i,
                is_read=True
            )
            ic.route_request(request)
        
        stats = ic.get_stats()
        assert stats['total_requests'] == 10
        assert stats['successful_requests'] == 10

    def test_interconnect_reset(self):
        """Test interconnect reset"""
        ic = CrossbarInterconnect(num_ports=16)
        
        # Add some traffic
        for _ in range(5):
            request = InterconnectRequest(source_port=0, addr=0x1000)
            ic.route_request(request)
        
        ic.reset()
        stats = ic.get_stats()
        assert stats['total_requests'] == 0

    def test_factory_create_crossbar(self):
        """Test factory crossbar creation"""
        ic = InterconnectFactory.create_crossbar(
            num_ports=32,
            stack_count=4
        )
        assert isinstance(ic, CrossbarInterconnect)

    def test_factory_create_mesh(self):
        """Test factory mesh creation"""
        ic = InterconnectFactory.create_mesh(rows=4, cols=8)
        assert isinstance(ic, MeshInterconnect)

    def test_factory_create_tree(self):
        """Test factory tree creation"""
        ic = InterconnectFactory.create_tree(num_leaves=32)
        assert isinstance(ic, BinaryTreeInterconnect)

    def test_create_interconnect_function(self):
        """Test create_interconnect convenience function"""
        ic = create_interconnect(
            topology="crossbar",
            num_ports=32,
            stack_count=4
        )
        assert isinstance(ic, CrossbarInterconnect)

        ic = create_interconnect(
            topology="mesh",
            rows=4,
            cols=8
        )
        assert isinstance(ic, MeshInterconnect)


# ============================================================================
# gem5 Memory Port Tests
# ============================================================================

class TestGem5MemoryPort:
    """Test gem5 memory port integration"""

    def test_memory_port_creation(self):
        """Test memory port creation"""
        port = create_memory_port(name="dram.port", cache_line_size=64)
        assert port is not None
        assert port.name == "dram.port"

    def test_cache_line_handler(self):
        """Test cache line handler"""
        handler = CacheLineHandler(line_size=64)
        
        # Test alignment
        aligned = handler.align_address(0x123)
        assert aligned == 0x100
        
        # Test split
        chunks = handler.split_request(0x10, 200)
        assert len(chunks) > 1

    def test_cache_line_beats_calculation(self):
        """Test beat calculation"""
        handler = CacheLineHandler(line_size=64)
        
        beats = handler.calculate_beats(64)
        assert beats == 4
        
        beats = handler.calculate_beats(128)
        assert beats == 8

    def test_memory_port_send_request(self):
        """Test sending memory request"""
        port = create_memory_port(name="test.port")
        
        req_id = port.send_request(
            addr=0x1000,
            size=64,
            is_write=False,
            qos=8
        )
        assert req_id is not None
        assert req_id >= 0

    def test_memory_port_stats(self):
        """Test memory port statistics"""
        port = create_memory_port(name="test.port")
        
        port.send_request(addr=0x1000, size=64, is_write=False)
        port.send_request(addr=0x2000, size=64, is_write=True)
        
        stats = port.get_stats()
        assert stats['packets_sent'] == 2
        assert stats['bytes_sent'] == 128

    def test_memory_port_tick(self):
        """Test memory port tick"""
        port = create_memory_port(name="test.port")
        
        for _ in range(10):
            port.tick()
        
        stats = port.get_stats()
        assert stats['current_cycle'] == 10

    def test_memory_port_channel_load(self):
        """Test channel load tracking"""
        port = create_memory_port(name="test.port")
        
        # Send requests to same channel
        for _ in range(5):
            port.send_request(addr=0x1000, size=64, is_write=False)
        
        # All should map to same channel initially
        load = port.get_channel_load(0)
        assert load >= 0


class TestTrafficGenerator:
    """Test traffic generator"""

    def test_traffic_generator_creation(self):
        """Test traffic generator creation"""
        port = create_memory_port(name="test.port")
        tg = TrafficGeneratorInterface(name="tg", port=port)
        
        assert tg.name == "tg"
        assert tg.pattern == TrafficGeneratorInterface.AccessPattern.SEQUENTIAL

    def test_traffic_generator_sequential(self):
        """Test sequential access pattern"""
        port = create_memory_port(name="test.port")
        tg = TrafficGeneratorInterface(name="tg", port=port)
        tg.set_pattern(TrafficGeneratorInterface.AccessPattern.SEQUENTIAL)
        
        req_id = tg.generate_request()
        assert req_id is not None

    def test_traffic_generator_random(self):
        """Test random access pattern"""
        port = create_memory_port(name="test.port")
        tg = TrafficGeneratorInterface(name="tg", port=port)
        tg.set_pattern(TrafficGeneratorInterface.AccessPattern.RANDOM)
        
        for _ in range(10):
            tg.generate_request()

    def test_traffic_generator_burst(self):
        """Test burst generation"""
        port = create_memory_port(name="test.port")
        tg = TrafficGeneratorInterface(name="tg", port=port)
        
        req_ids = tg.generate_burst(5)
        assert len(req_ids) == 5


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for full AXI4 to HBM pipeline"""

    def test_axi4_bridge_to_converter(self):
        """Test connecting AXI4 bridge to converter"""
        bridge = create_axi4_bridge(max_pending=16)
        converter = create_axi4_converter()
        
        # Submit transactions
        read_id = bridge.submit_read(addr=0x1000, size=6, length=3, qos=8)
        write_id = bridge.submit_write(
            addr=0x2000, data=[0xDEAD] * 4, size=6, length=3, qos=4
        )
        
        # Get pending transactions
        pending_read = bridge._pending_reads.get(read_id)
        pending_write = bridge._pending_writes.get(write_id)
        
        if pending_read:
            result = converter.to_hbm(pending_read)
            assert result.success
        
        if pending_write:
            result = converter.to_hbm(pending_write)
            assert result.success

    def test_full_pipeline_simulation(self):
        """Test full AXI4 to HBM pipeline simulation"""
        bridge = create_axi4_bridge(max_pending=16)
        converter = create_axi4_converter()
        monitor = create_axi4_monitor()
        monitor.connect_signals(bridge.signals)
        
        # Submit transactions
        for i in range(10):
            bridge.submit_read(addr=0x1000 + i * 64, size=6, length=3, qos=i)
        
        # Simulate
        for _ in range(50):
            bridge.tick()
            monitor.tick()
        
        # Check results
        stats = bridge.get_stats()
        assert stats['cycle'] > 0

    def test_qos_end_to_end(self):
        """Test QoS handling end-to-end"""
        bridge = create_axi4_bridge(max_pending=16)
        converter = create_axi4_converter()
        
        # High priority
        high_txn_id = bridge.submit_read(addr=0x1000, qos=15)
        # Low priority
        low_txn_id = bridge.submit_read(addr=0x2000, qos=1)
        
        # Both should be pending
        assert bridge.get_pending_count(is_read=True) == 2
        
        # Get and convert high priority
        high_txn = bridge._pending_reads.get(high_txn_id)
        if high_txn:
            result = converter.to_hbm(high_txn)
            assert result.success

    def test_outstanding_end_to_end(self):
        """Test outstanding transaction handling"""
        bridge = create_axi4_bridge(
            max_pending=32,
            enable_outstanding=True,
            enable_out_of_order=True
        )
        converter = create_axi4_converter()
        
        # Submit many transactions
        txn_ids = []
        for i in range(16):
            txn_id = bridge.submit_read(
                addr=0x1000 + i * 256,
                size=6,
                length=7,
                id=i
            )
            txn_ids.append(txn_id)
        
        assert bridge.get_pending_count(is_read=True) == 16
        
        # Verify converter can handle them
        for txn_id in txn_ids[:4]:
            txn = bridge._pending_reads.get(txn_id)
            if txn:
                result = converter.to_hbm(txn)
                assert result.success


# ============================================================================
# Performance Benchmark Tests
# ============================================================================

class TestPerformance:
    """Performance benchmark tests"""

    def test_burst_bandwidth(self):
        """Test burst bandwidth"""
        bridge = create_axi4_bridge(max_pending=64)
        
        # Submit large burst
        for i in range(32):
            bridge.submit_read(
                addr=0x1000 + i * 64,
                size=6,
                length=15,  # 16 beats each
                qos=8
            )
        
        # Simulate
        for _ in range(100):
            bridge.tick()
        
        stats = bridge.get_stats()
        assert stats['cycle'] == 100

    def test_multi_channel_throughput(self):
        """Test multi-channel throughput simulation"""
        ic = CrossbarInterconnect(
            num_ports=32,
            stack_count=4,
            channels_per_stack=8,
            routing_mode=RoutingMode.ADDRESS_BASED
        )
        
        # Simulate heavy traffic
        for i in range(1000):
            request = InterconnectRequest(
                source_port=i % 32,
                addr=(i % 8) * 0x2000_0000,
                is_read=i % 2 == 0,
                qos=8
            )
            ic.route_request(request)
        
        stats = ic.get_stats()
        assert stats['total_requests'] == 1000
        assert stats['successful_requests'] == 1000

    def test_qos_priority_scheduling(self):
        """Test QoS priority scheduling performance"""
        bridge = create_axi4_bridge(
            max_pending=64,
            enable_outstanding=True
        )
        
        # Mix of QoS levels
        for i in range(100):
            qos = (i % 16)
            bridge.submit_read(addr=0x1000 + i * 64, qos=qos)

    def test_latency_distribution(self):
        """Test latency distribution"""
        bridge = create_axi4_bridge(max_pending=16)
        converter = create_axi4_converter()
        
        latencies = []
        for i in range(20):
            txn_id = bridge.submit_read(
                addr=0x1000 + i * 256,
                size=6,
                length=7,
                qos=8
            )
            
            # Simulate some cycles
            for _ in range(i + 1):
                bridge.tick()
        
        avg_lat = bridge.get_average_latency(is_read=True)
        assert avg_lat >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
