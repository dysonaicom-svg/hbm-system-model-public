"""
Unit Tests for AXI4 Monitor - Enhanced Coverage

Tests cover:
- AXI4Monitor
- ProtocolViolation
- TransactionLogEntry
- PerformanceMetrics
- Violation detection
- Transaction logging

Target: Increase coverage from 63% to 80%+
"""

import pytest
import sys
from typing import List, Dict

sys.path.insert(0, '/home/ic/JXTF/HBM4')

from model.interconnect.axi4_monitor import (
    # Core classes
    AXI4Monitor,
    ViolationType,
    ProtocolViolation,
    TransactionLogEntry,
    PerformanceMetrics,

    # Factory functions
    create_axi4_monitor,
    analyze_axi4_log,
)

from model.interconnect.axi4_bridge import (
    create_axi4_bridge,
)


# ============================================================================
# ProtocolViolation Tests
# ============================================================================

class TestProtocolViolation:
    """Test ProtocolViolation dataclass"""

    def test_violation_creation(self):
        """Test violation creation"""
        violation = ProtocolViolation(
            violation_type=ViolationType.AR_ADDRESS_ALIGNMENT,
            cycle=100,
            channel="AR",
            details="Address not aligned",
        )
        assert violation.violation_type == ViolationType.AR_ADDRESS_ALIGNMENT
        assert violation.cycle == 100
        assert violation.channel == "AR"
        assert violation.severity == "ERROR"

    def test_violation_repr(self):
        """Test violation string representation"""
        violation = ProtocolViolation(
            violation_type=ViolationType.AR_VALID_WITHOUT_READY,
            cycle=50,
            channel="AR",
            details="ARVALID high without ARREADY",
        )
        repr_str = repr(violation)
        assert "Cycle 50" in repr_str


# ============================================================================
# TransactionLogEntry Tests
# ============================================================================

class TestTransactionLogEntry:
    """Test TransactionLogEntry dataclass"""

    def test_entry_creation(self):
        """Test entry creation"""
        entry = TransactionLogEntry(
            transaction_id="txn_1",
            txn_type="READ",
            addr=0x1000,
            length=7,
            size=6,
            burst=1,
            id=1,
            qos=8,
        )
        assert entry.transaction_id == "txn_1"
        assert entry.txn_type == "READ"
        assert entry.addr == 0x1000

    def test_latency_property(self):
        """Test latency property"""
        entry = TransactionLogEntry(
            transaction_id="txn_1",
            txn_type="READ",
            addr=0x1000,
            length=0,
            size=0,
            burst=0,
            id=0,
            qos=0,
            submission_cycle=10,
            completion_cycle=20,
        )
        assert entry.latency == 10

    def test_latency_no_completion(self):
        """Test latency without completion"""
        entry = TransactionLogEntry(
            transaction_id="txn_1",
            txn_type="READ",
            addr=0x1000,
            length=0,
            size=0,
            burst=0,
            id=0,
            qos=0,
            submission_cycle=10,
        )
        assert entry.latency == -1

    def test_to_dict(self):
        """Test converting to dictionary"""
        entry = TransactionLogEntry(
            transaction_id="txn_1",
            txn_type="READ",
            addr=0x1000,
            length=7,
            size=6,
            burst=1,
            id=1,
            qos=8,
        )
        d = entry.to_dict()
        assert 'transaction_id' in d
        assert 'addr' in d


# ============================================================================
# PerformanceMetrics Tests
# ============================================================================

class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass"""

    def test_metrics_creation(self):
        """Test metrics creation"""
        metrics = PerformanceMetrics()
        assert metrics.total_cycles == 0
        assert metrics.ar_transactions == 0

    def test_read_latency_average(self):
        """Test read latency average"""
        metrics = PerformanceMetrics()
        metrics.read_latency_sum = 100
        metrics.read_latency_count = 10
        assert metrics.average_read_latency == 10.0

    def test_read_latency_avg_zero(self):
        """Test read latency average with no data"""
        metrics = PerformanceMetrics()
        assert metrics.average_read_latency == 0.0

    def test_write_latency_average(self):
        """Test write latency average"""
        metrics = PerformanceMetrics()
        metrics.write_latency_sum = 150
        metrics.write_latency_count = 10
        assert metrics.average_write_latency == 15.0

    def test_ar_utilization(self):
        """Test AR channel utilization"""
        metrics = PerformanceMetrics()
        metrics.total_cycles = 100
        metrics.active_cycles_ar = 50
        assert metrics.ar_utilization == 0.5

    def test_total_bandwidth_calculation(self):
        """Test total bandwidth calculation"""
        metrics = PerformanceMetrics()
        metrics.total_cycles = 100
        metrics.read_bytes_total = 10000
        metrics.write_bytes_total = 5000
        bw = metrics.read_bandwidth_bytes_per_cycle
        assert bw == 100.0


# ============================================================================
# AXI4Monitor Tests
# ============================================================================

class TestAXI4Monitor:
    """Test AXI4Monitor functionality"""

    def test_monitor_creation(self):
        """Test monitor creation"""
        monitor = AXI4Monitor()
        assert monitor is not None
        assert monitor._cycle == 0

    def test_monitor_with_config(self):
        """Test monitor with configuration"""
        monitor = AXI4Monitor(
            strict_protocol=True,
            enable_transaction_log=True,
        )
        assert monitor.strict_protocol is True
        assert monitor.enable_transaction_log is True

    def test_monitor_reset(self):
        """Test monitor reset"""
        monitor = AXI4Monitor()
        for _ in range(50):
            monitor.tick()

        assert monitor._cycle == 50
        monitor.reset()
        assert monitor._cycle == 0

    def test_monitor_tick(self):
        """Test monitor tick"""
        monitor = AXI4Monitor()
        initial = monitor._cycle
        monitor.tick()
        assert monitor._cycle == initial + 1

    def test_get_violations(self):
        """Test getting violations"""
        monitor = AXI4Monitor(strict_protocol=True)
        violations = monitor.get_violations()
        assert isinstance(violations, list)

    def test_get_transaction_log(self):
        """Test getting transaction log"""
        monitor = AXI4Monitor(enable_transaction_log=True)
        log = monitor.get_transaction_log()
        assert isinstance(log, list)

    def test_get_metrics(self):
        """Test getting metrics"""
        monitor = AXI4Monitor()
        for _ in range(100):
            monitor.tick()

        metrics = monitor.get_metrics()
        assert metrics.total_cycles == 100

    def test_is_compliant(self):
        """Test compliance check"""
        monitor = AXI4Monitor(strict_protocol=True)
        for _ in range(50):
            monitor.tick()

        is_compliant = monitor.is_compliant()
        assert isinstance(is_compliant, bool)

    def test_get_report(self):
        """Test getting report"""
        monitor = AXI4Monitor()
        for _ in range(20):
            monitor.tick()

        report = monitor.get_report()
        assert 'cycle' in report
        assert 'metrics' in report
        assert 'violations' in report

    def test_monitor_set_widths(self):
        """Test setting interface widths"""
        monitor = AXI4Monitor()
        monitor.set_widths(data_width=512, addr_width=64)


# ============================================================================
# AXI4Monitor Signal Connection Tests
# ============================================================================

class TestAXI4MonitorSignals:
    """Test AXI4Monitor signal connection"""

    def test_connect_signals(self):
        """Test connecting to bridge signals"""
        bridge = create_axi4_bridge(max_pending=8)
        monitor = create_axi4_monitor()

        monitor.connect_signals(bridge.signals)
        assert hasattr(monitor, '_signals')

    def test_monitor_ar_channel(self):
        """Test monitoring AR channel"""
        bridge = create_axi4_bridge(max_pending=8)
        monitor = create_axi4_monitor()
        monitor.connect_signals(bridge.signals)

        bridge.submit_read(addr=0x1000)

        for _ in range(5):
            bridge.tick()
            monitor.tick()

    def test_monitor_aw_channel(self):
        """Test monitoring AW channel"""
        bridge = create_axi4_bridge(max_pending=8)
        monitor = create_axi4_monitor()
        monitor.connect_signals(bridge.signals)

        bridge.submit_write(addr=0x2000, data=[0xDEAD])

        for _ in range(5):
            bridge.tick()
            monitor.tick()


# ============================================================================
# AXI4Monitor Transaction Tests
# ============================================================================

class TestAXI4MonitorTransactions:
    """Test AXI4Monitor transaction tracking"""

    def test_track_read_transaction(self):
        """Test tracking read transaction"""
        bridge = create_axi4_bridge(max_pending=8)
        monitor = create_axi4_monitor()
        monitor.connect_signals(bridge.signals)

        txn_id = bridge.submit_read(addr=0x1000, length=0)

        for _ in range(20):
            bridge.tick()
            monitor.tick()

    def test_track_write_transaction(self):
        """Test tracking write transaction"""
        bridge = create_axi4_bridge(max_pending=8)
        monitor = create_axi4_monitor()
        monitor.connect_signals(bridge.signals)

        txn_id = bridge.submit_write(addr=0x2000, data=[0xDEAD], length=0)

        for _ in range(20):
            bridge.tick()
            monitor.tick()


# ============================================================================
# analyze_axi4_log Tests
# ============================================================================

class TestAnalyzeLog:
    """Test analyze_axi4_log function"""

    def test_analyze_empty_log(self):
        """Test analyzing empty log"""
        result = analyze_axi4_log([])
        assert isinstance(result, dict)

    def test_analyze_log_with_dict_entries(self):
        """Test analyzing log with dictionary entries"""
        log = [
            {
                'type': 'READ',
                'addr': 0x1000,
                'latency': 10,
                'status': 'COMPLETED',
            }
        ]

        result = analyze_axi4_log(log)
        assert isinstance(result, dict)


# ============================================================================
# Integration Tests
# ============================================================================

class TestMonitorIntegration:
    """Integration tests for AXI4Monitor"""

    def test_full_pipeline_monitoring(self):
        """Test monitoring full AXI4 pipeline"""
        bridge = create_axi4_bridge(max_pending=16)
        monitor = create_axi4_monitor()
        monitor.connect_signals(bridge.signals)

        for i in range(10):
            bridge.submit_read(addr=0x1000 + i * 64, length=3, qos=i)

        for _ in range(100):
            bridge.tick()
            monitor.tick()

        report = monitor.get_report()
        assert 'cycle' in report

    def test_concurrent_read_write_monitoring(self):
        """Test monitoring concurrent reads and writes"""
        bridge = create_axi4_bridge(max_pending=16)
        monitor = create_axi4_monitor()
        monitor.connect_signals(bridge.signals)

        for i in range(5):
            bridge.submit_read(addr=0x1000 + i * 64)
            bridge.submit_write(addr=0x2000 + i * 64, data=[0xDEAD])

        for _ in range(100):
            bridge.tick()
            monitor.tick()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestMonitorEdgeCases:
    """Test edge cases in AXI4Monitor"""

    def test_monitor_without_signals(self):
        """Test monitor without signal connection"""
        monitor = AXI4Monitor()
        for _ in range(10):
            monitor.tick()
        # Should not crash

    def test_log_entry_without_timing(self):
        """Test log entry without timing data"""
        entry = TransactionLogEntry(
            transaction_id="txn_1",
            txn_type="READ",
            addr=0x1000,
            length=0,
            size=0,
            burst=0,
            id=0,
            qos=0,
        )
        assert entry.latency == -1

    def test_zero_cycles_metrics(self):
        """Test metrics with zero cycles"""
        metrics = PerformanceMetrics()
        assert metrics.ar_utilization == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
