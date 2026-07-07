"""Tests for transaction_exporter module"""

import pytest
import json
from sim.rtl.transaction_exporter import (
    TransactionExporter, Transaction, TransactionState
)


class TestTransaction:
    def test_transaction_creation(self):
        txn = Transaction(id=1, type="READ", address=0x1000, start_cycle=100)
        assert txn.id == 1
        assert txn.type == "READ"
        assert txn.latency == 0

    def test_transaction_latency(self):
        txn = Transaction(id=1, type="READ", address=0x1000,
                          start_cycle=100, end_cycle=115)
        assert txn.latency == 15

    def test_transaction_with_rtl(self):
        txn = Transaction(id=1, type="READ", address=0x1000,
                          start_cycle=100, end_cycle=115,
                          python_latency=15, rtl_latency=16, aligned=True)
        assert txn.latency == 15
        assert txn.python_latency == 15
        assert txn.rtl_latency == 16
        assert txn.aligned is True


class TestTransactionExporter:
    def test_exporter_creation(self):
        exporter = TransactionExporter()
        assert len(exporter.transactions) == 0

    def test_begin_transaction(self):
        exporter = TransactionExporter()
        txn_id = exporter.begin_transaction("READ", 0x1000, 100)
        assert txn_id == 0
        assert len(exporter.transactions) == 1

    def test_begin_multiple_transactions(self):
        exporter = TransactionExporter()
        id1 = exporter.begin_transaction("READ", 0x1000, 100)
        id2 = exporter.begin_transaction("WRITE", 0x2000, 105)
        id3 = exporter.begin_transaction("READ", 0x3000, 110)

        assert id1 == 0
        assert id2 == 1
        assert id3 == 2
        assert len(exporter.transactions) == 3

    def test_complete_transaction(self):
        exporter = TransactionExporter()
        txn_id = exporter.begin_transaction("READ", 0x1000, 100)
        exporter.complete_transaction(txn_id, 115, 15, 16)

        txn = exporter.transactions[0]
        assert txn.end_cycle == 115
        assert txn.python_latency == 15
        assert txn.rtl_latency == 16
        assert txn.aligned is True  # |15-16| = 1 <= 1

    def test_unaligned_detection(self):
        exporter = TransactionExporter()
        txn_id = exporter.begin_transaction("READ", 0x1000, 100)
        exporter.complete_transaction(txn_id, 130, 30, 16)  # Big difference

        unaligned = exporter.get_unaligned_transactions()
        assert len(unaligned) == 1

    def test_alignment_stats(self):
        exporter = TransactionExporter()
        id1 = exporter.begin_transaction("READ", 0x1000, 100)
        id2 = exporter.begin_transaction("WRITE", 0x2000, 110)
        # Both within tolerance of 1 cycle
        exporter.complete_transaction(id1, 115, 15, 16)
        exporter.complete_transaction(id2, 125, 15, 16)

        stats = exporter.get_alignment_stats()
        assert stats["total_with_rtl"] == 2
        assert stats["aligned"] == 2
        assert stats["unaligned"] == 0

    def test_alignment_stats_empty(self):
        exporter = TransactionExporter()
        stats = exporter.get_alignment_stats()
        assert stats["total_with_rtl"] == 0
        assert stats["alignment_rate"] == 0

    def test_latency_stats(self):
        exporter = TransactionExporter()
        id1 = exporter.begin_transaction("READ", 0x1000, 100)
        id2 = exporter.begin_transaction("WRITE", 0x2000, 110)
        exporter.complete_transaction(id1, 115, 15, 16)
        exporter.complete_transaction(id2, 130, 20, 21)

        stats = exporter.get_latency_stats()
        assert stats["min"] == 15
        assert stats["max"] == 20
        assert stats["avg"] == 17.5

    def test_latency_stats_empty(self):
        exporter = TransactionExporter()
        stats = exporter.get_latency_stats()
        assert stats["min"] == 0
        assert stats["max"] == 0
        assert stats["avg"] == 0

    def test_export_json(self, tmp_path):
        exporter = TransactionExporter()
        txn_id = exporter.begin_transaction("READ", 0x1000, 100)
        exporter.complete_transaction(txn_id, 115, 15, 16)

        filepath = tmp_path / "transactions.json"
        exporter.export_json(str(filepath))

        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)
        assert len(data["transactions"]) == 1
        assert "alignment_stats" in data
        assert "latency_stats" in data

    def test_export_csv(self, tmp_path):
        exporter = TransactionExporter()
        txn_id = exporter.begin_transaction("READ", 0x1000, 100)
        exporter.complete_transaction(txn_id, 115, 15, 16)

        filepath = tmp_path / "transactions.csv"
        exporter.export_csv(str(filepath))

        assert filepath.exists()

        with open(filepath) as f:
            lines = f.readlines()
        assert len(lines) == 2  # Header + 1 transaction

    def test_reset(self):
        exporter = TransactionExporter()
        exporter.begin_transaction("READ", 0x1000, 100)
        exporter.reset()
        assert len(exporter.transactions) == 0
        assert exporter._next_id == 0
