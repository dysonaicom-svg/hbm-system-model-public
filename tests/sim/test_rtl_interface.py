"""
RTL Interface Tests

Tests for RTL co-simulation interface functionality.
Covers transaction injection, result comparison, and waveform control.

Run with: pytest tests/sim/test_rtl_interface.py -v
"""

import pytest
import json
import tempfile
import os
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from sim.rtl_interface import (
    RTLInterface,
    RTLTransaction,
    TransactionType,
    TransactionStatus,
    CoSimConfig,
    CoSimStats,
    ResultComparator,
    create_rtl_interface,
)


class TestRTLInterfaceBasic:
    """Basic RTLInterface functionality tests"""

    def test_create_interface(self):
        """RTLInterface should be created with default config"""
        iface = RTLInterface()
        assert iface is not None
        assert iface.config.enable_rtl is False
        assert iface.rtl_process is None
        assert iface.rtl_socket is None

    def test_create_interface_with_config(self):
        """RTLInterface should be created with custom config"""
        config = CoSimConfig(
            enable_rtl=True,
            rtl_simulator="verilator",
            trace_enabled=True,
        )
        iface = RTLInterface(config)
        assert iface.config.enable_rtl is True
        assert iface.config.rtl_simulator == "verilator"
        assert iface.config.trace_enabled is True

    def test_generate_transaction_id(self):
        """Transaction IDs should be unique and incrementing"""
        iface = RTLInterface()
        id1 = iface._generate_transaction_id()
        id2 = iface._generate_transaction_id()
        id3 = iface._generate_transaction_id()

        assert id1 == 0
        assert id2 == 1
        assert id3 == 2
        assert id1 != id2 != id3


class TestTransactionInjection:
    """Transaction injection tests"""

    def test_inject_read_transaction(self):
        """Should inject read transaction correctly"""
        iface = RTLInterface()
        tid = iface.inject_read_transaction(
            address=0x1000,
            channel=1,
            bank=3,
        )

        assert tid == 0
        assert tid in iface.transactions
        trans = iface.transactions[tid]
        assert trans.transaction_type == TransactionType.READ
        assert trans.address == 0x1000
        assert trans.channel == 1
        assert trans.bank == 3
        assert trans.status == TransactionStatus.PENDING
        assert iface.stats.total_transactions == 1

    def test_inject_write_transaction(self):
        """Should inject write transaction correctly"""
        iface = RTLInterface()
        tid = iface.inject_write_transaction(
            address=0x2000,
            data=0xDEADBEEF,
            channel=2,
            bank=5,
        )

        assert tid == 0
        trans = iface.transactions[tid]
        assert trans.transaction_type == TransactionType.WRITE
        assert trans.data == 0xDEADBEEF
        assert iface.stats.total_transactions == 1

    def test_inject_command_transaction(self):
        """Should inject command transaction (ACT, PRE, REF)"""
        iface = RTLInterface()

        # Test ACT command
        tid = iface.inject_command_transaction(
            command="activate",
            address=0x3000,
            channel=0,
            bank=2,
        )

        assert tid == 0
        trans = iface.transactions[tid]
        assert trans.transaction_type == TransactionType.ACTIVATE
        assert trans.address == 0x3000

        # Test PRE command
        tid2 = iface.inject_command_transaction(
            command="precharge",
            address=0x3000,
            channel=0,
            bank=2,
        )
        trans2 = iface.transactions[tid2]
        assert trans2.transaction_type == TransactionType.PRECHARGE

        # Test REF command
        tid3 = iface.inject_command_transaction(
            command="refresh",
            address=0,
            channel=0,
            bank=0,
        )
        trans3 = iface.transactions[tid3]
        assert trans3.transaction_type == TransactionType.REFRESH

    def test_inject_with_cycle(self):
        """Should use specified cycle if provided"""
        iface = RTLInterface()
        iface.current_cycle = 100

        tid = iface.inject_read_transaction(
            address=0x1000,
            cycle=50,  # Explicit cycle
        )

        trans = iface.transactions[tid]
        assert trans.cycle == 50

        # Without cycle, should use current_cycle
        tid2 = iface.inject_read_transaction(address=0x2000)
        trans2 = iface.transactions[tid2]
        assert trans2.cycle == 100


class TestResultComparison:
    """Result comparison tests"""

    def test_compare_results_match(self):
        """Results should match when latencies are equal"""
        iface = RTLInterface()

        # Inject transaction
        tid = iface.inject_read_transaction(address=0x1000)

        # Record Python result
        iface.record_python_result(tid, latency_cycles=10, data=0x1234)

        # Set RTL result
        trans = iface.transactions[tid]
        trans.latency_cycles = 10
        trans.response_data = 0x1234
        trans.status = TransactionStatus.COMPLETED

        # Compare
        is_match, diff = iface.compare_results(tid)

        assert is_match is True
        assert diff['latency_diff'] == 0
        assert diff['data_match'] is True
        assert iface.stats.matched_results == 1

    def test_compare_results_latency_mismatch(self):
        """Should detect latency mismatch"""
        iface = RTLInterface()

        tid = iface.inject_read_transaction(address=0x1000)
        iface.record_python_result(tid, latency_cycles=10)

        trans = iface.transactions[tid]
        trans.latency_cycles = 15  # Different latency

        is_match, diff = iface.compare_results(tid)

        assert is_match is False
        assert diff['latency_diff'] == 5
        assert iface.stats.mismatched_results == 1

    def test_compare_results_data_mismatch(self):
        """Should detect data mismatch on reads"""
        iface = RTLInterface()

        tid = iface.inject_read_transaction(address=0x1000)
        iface.record_python_result(tid, latency_cycles=10, data=0xABCD)

        trans = iface.transactions[tid]
        trans.latency_cycles = 10
        trans.response_data = 0x1234  # Different data

        is_match, diff = iface.compare_results(tid)

        assert is_match is False
        assert diff['data_match'] is False

    def test_compare_results_missing_transaction(self):
        """Should handle missing transaction"""
        iface = RTLInterface()
        is_match, diff = iface.compare_results(999)

        assert is_match is False
        assert 'error' in diff

    def test_compare_results_missing_python_result(self):
        """Should handle missing Python result"""
        iface = RTLInterface()
        tid = iface.inject_read_transaction(address=0x1000)

        is_match, diff = iface.compare_results(tid)

        assert is_match is False
        assert 'error' in diff


class TestResultComparator:
    """ResultComparator class tests"""

    def test_comparator_tolerance(self):
        """Comparator should respect tolerance"""
        comp = ResultComparator(tolerance_cycles=5)

        # Within tolerance
        result = comp.compare_transaction(10, None, 14, None, "write")
        assert result['latency_match'] is True

        # Outside tolerance
        result = comp.compare_transaction(10, None, 20, None, "write")
        assert result['latency_match'] is False

    def test_comparator_read_data(self):
        """Comparator should compare data for reads"""
        comp = ResultComparator()

        # Match
        result = comp.compare_transaction(10, 0xABCD, 10, 0xABCD, "read")
        assert result['data_match'] is True

        # Mismatch
        result = comp.compare_transaction(10, 0xABCD, 10, 0x1234, "read")
        assert result['data_match'] is False

    def test_comparator_summary(self):
        """Comparator should produce correct summary"""
        comp = ResultComparator()

        comp.compare_transaction(10, 0xA, 10, 0xA, "read")  # Match
        comp.compare_transaction(10, 0xA, 12, 0xA, "write")  # Match (within tolerance)
        comp.compare_transaction(10, 0xA, 10, 0xB, "read")  # Data mismatch

        summary = comp.get_summary()
        assert summary['total'] == 3
        assert summary['matches'] == 2
        assert summary['mismatches'] == 1
        assert summary['match_rate'] == pytest.approx(2/3)


class TestWaveformControl:
    """Waveform control tests"""

    def test_enable_waveform_dump(self):
        """Should enable waveform dump"""
        iface = RTLInterface()
        iface.enable_waveform_dump()

        assert iface.config.dump_waveform is True
        assert iface._waveform_enabled is True
        assert iface.waveform_path == "./rtl/waves.vcd"

    def test_enable_waveform_dump_custom_path(self):
        """Should use custom path for waveform"""
        iface = RTLInterface()
        iface.enable_waveform_dump("/tmp/test.vcd")

        assert iface.waveform_path == "/tmp/test.vcd"

    def test_disable_waveform_dump(self):
        """Should disable waveform dump"""
        iface = RTLInterface()
        iface.enable_waveform_dump()
        iface.disable_waveform_dump()

        assert iface.config.dump_waveform is False
        assert iface._waveform_enabled is False


class TestFIFOCommunication:
    """FIFO communication tests"""

    def test_setup_fifo_communication(self):
        """Should create FIFO files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            iface = RTLInterface()
            result = iface.setup_fifo_communication(tmpdir)

            assert result is True
            assert iface.rtl_fifo_out == os.path.join(tmpdir, "python_to_rtl")
            assert iface.rtl_fifo_in == os.path.join(tmpdir, "rtl_to_python")

            # FIFOs should exist
            assert os.path.exists(iface.rtl_fifo_out)
            assert os.path.exists(iface.rtl_fifo_in)


class TestTickAndCycle:
    """Simulation cycle tests"""

    def test_tick(self):
        """Tick should increment cycle"""
        iface = RTLInterface()
        assert iface.current_cycle == 0

        cycle = iface.tick()
        assert cycle == 1
        assert iface.current_cycle == 1

        iface.tick()
        assert iface.current_cycle == 2

    def test_get_pending_transactions(self):
        """Should return pending/in-progress transactions"""
        iface = RTLInterface()

        # Add transactions with different statuses
        t1 = iface.inject_read_transaction(address=0x1000)
        t2 = iface.inject_read_transaction(address=0x2000)

        iface.transactions[t1].status = TransactionStatus.COMPLETED

        pending = iface.get_pending_transactions()
        assert len(pending) == 1
        assert pending[0].id == t2

    def test_get_completed_transactions(self):
        """Should return completed transactions"""
        iface = RTLInterface()

        t1 = iface.inject_read_transaction(address=0x1000)
        t2 = iface.inject_read_transaction(address=0x2000)

        iface.transactions[t1].status = TransactionStatus.COMPLETED
        iface.transactions[t2].status = TransactionStatus.COMPLETED

        completed = iface.get_completed_transactions()
        assert len(completed) == 2

    def test_get_transaction(self):
        """Should retrieve transaction by ID"""
        iface = RTLInterface()

        tid = iface.inject_read_transaction(address=0x1000)
        trans = iface.get_transaction(tid)

        assert trans is not None
        assert trans.id == tid

        # Non-existent
        assert iface.get_transaction(999) is None


class TestExportImport:
    """Export/import tests"""

    def test_export_trace(self):
        """Should export transaction trace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            iface = RTLInterface()
            iface.inject_read_transaction(address=0x1000)
            iface.inject_write_transaction(address=0x2000, data=0xABCD)

            path = os.path.join(tmpdir, "trace.json")
            iface.export_trace(path)

            assert os.path.exists(path)

            with open(path, 'r') as f:
                data = json.load(f)

            assert 'transactions' in data
            assert len(data['transactions']) == 2

    def test_import_trace(self):
        """Should import transaction trace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create trace file
            trace_data = {
                'transactions': [{
                    'id': 0,
                    'type': 'read',
                    'address': '0x1000',
                    'data': None,
                    'channel': 1,
                    'bank': 2,
                    'cycle': 10,
                    'status': 'pending',
                    'latency_cycles': 0,
                    'response_data': None,
                    'timestamp_ns': 123456.0,
                }],
                'python_results': {},
            }

            path = os.path.join(tmpdir, "trace.json")
            with open(path, 'w') as f:
                json.dump(trace_data, f)

            # Import
            iface = RTLInterface()
            iface.import_trace(path)

            assert 0 in iface.transactions
            trans = iface.transactions[0]
            assert trans.transaction_type == TransactionType.READ
            assert trans.address == 0x1000
            assert trans.channel == 1


class TestSummary:
    """Summary tests"""

    def test_get_summary(self):
        """Should return correct summary"""
        iface = RTLInterface()
        iface.inject_read_transaction(address=0x1000)
        iface.inject_read_transaction(address=0x2000)

        summary = iface.get_summary()

        assert summary['config']['enable_rtl'] is False
        assert summary['current_cycle'] == 0
        assert summary['pending_count'] == 2
        assert summary['completed_count'] == 0
        assert summary['stats']['total_transactions'] == 2

    def test_get_stats(self):
        """Should return stats object"""
        iface = RTLInterface()
        iface.inject_read_transaction(address=0x1000)

        stats = iface.get_stats()
        assert isinstance(stats, CoSimStats)
        assert stats.total_transactions == 1


class TestRTLTransaction:
    """RTLTransaction dataclass tests"""

    def test_to_dict(self):
        """Should serialize to dict correctly"""
        trans = RTLTransaction(
            id=1,
            transaction_type=TransactionType.READ,
            address=0x1234,
            data=None,
            channel=2,
            bank=3,
            cycle=100,
            status=TransactionStatus.COMPLETED,
            latency_cycles=15,
            response_data=0xDEAD,
            timestamp_ns=1234567.89,
        )

        d = trans.to_dict()

        assert d['id'] == 1
        assert d['type'] == 'read'
        assert d['address'] == '0x1234'
        assert d['channel'] == 2
        assert d['bank'] == 3
        assert d['cycle'] == 100
        assert d['status'] == 'completed'
        assert d['latency_cycles'] == 15
        assert d['response_data'] == '0xdead'
        assert d['timestamp_ns'] == 1234567.89


class TestCreateInterface:
    """create_rtl_interface convenience function tests"""

    def test_create_with_defaults(self):
        """Should create with default settings"""
        iface = create_rtl_interface()

        assert iface.config.enable_rtl is False
        assert iface.config.trace_enabled is False

    def test_create_with_rtl_enabled(self):
        """Should create with RTL enabled"""
        iface = create_rtl_interface(enable_rtl=True, trace_enabled=True)

        assert iface.config.enable_rtl is True
        assert iface.config.trace_enabled is True


class TestCallbacks:
    """Callback tests"""

    def test_on_transaction_complete_callback(self):
        """Should call on_transaction_complete callback"""
        iface = RTLInterface()
        callback_called = []

        def callback(trans):
            callback_called.append(trans)

        iface.on_transaction_complete = callback

        # Simulate receiving a result
        tid = iface.inject_read_transaction(address=0x1000)
        message = json.dumps({
            'id': tid,
            'status': 'completed',
            'latency_cycles': 10,
            'response_data': 0x1234,
        })

        iface.receive_from_rtl(message)

        assert len(callback_called) == 1
        assert callback_called[0].id == tid

    def test_on_mismatch_callback(self):
        """Should call on_mismatch callback"""
        iface = RTLInterface()
        mismatches = []

        def callback(diff):
            mismatches.append(diff)

        iface.on_mismatch = callback

        # Create mismatch
        tid = iface.inject_read_transaction(address=0x1000)
        iface.record_python_result(tid, latency_cycles=10)
        iface.transactions[tid].latency_cycles = 20

        iface.compare_results(tid)

        assert len(mismatches) == 1
        assert mismatches[0]['latency_diff'] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
