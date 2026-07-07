"""Tests for coverage_bridge module"""

import pytest
from sim.rtl.coverage_bridge import (
    CoverageBridge, CoverageSample, TransactionCoverage, TransactionType
)


class TestCoverageSample:
    def test_sample_creation(self):
        sample = CoverageSample(group="test", name="sample", value=123, cycle=10)
        assert sample.group == "test"
        assert sample.value == 123


class TestCoverageBridge:
    def test_bridge_creation(self):
        bridge = CoverageBridge()
        assert len(bridge.samples) == 0
        assert len(bridge.transactions) == 0

    def test_record_transaction(self):
        bridge = CoverageBridge()
        bridge.record_transaction(
            txn_type=TransactionType.READ,
            address=0x1000,
            bank=1,
            channel=0,
            latency=10,
            is_hit=True
        )
        assert len(bridge.transactions) == 1
        assert bridge.transactions[0].txn_type == TransactionType.READ
        assert bridge.transactions[0].is_hit is True

    def test_record_bank_access(self):
        bridge = CoverageBridge()
        bridge.record_bank_access(bank=2, row=100, is_hit=False)
        assert len(bridge.samples) == 1
        assert bridge.samples[0].group == "bank_access"

    def test_record_qos_level(self):
        bridge = CoverageBridge()
        bridge.record_qos_level(8)
        assert len(bridge.samples) == 1
        assert bridge.samples[0].group == "qos"
        assert bridge.samples[0].value == 8

    def test_record_channel_utilization(self):
        bridge = CoverageBridge()
        bridge.record_channel_utilization(0, busy=True)
        assert len(bridge.samples) == 1
        assert bridge.samples[0].group == "channel_util"

    def test_get_coverage_summary(self):
        bridge = CoverageBridge()
        bridge.record_transaction(TransactionType.READ, 0x1000, 0, 0, 10, True)
        bridge.record_transaction(TransactionType.WRITE, 0x2000, 1, 0, 15, False)
        bridge.record_bank_access(0, 100, True)

        summary = bridge.get_coverage_summary()
        assert summary.get("transaction", 0) == 2
        assert summary.get("bank_access", 0) == 1

    def test_get_transaction_stats(self):
        bridge = CoverageBridge()
        bridge.record_transaction(TransactionType.READ, 0x1000, 0, 0, 10, True)
        bridge.record_transaction(TransactionType.WRITE, 0x2000, 1, 0, 20, False)

        stats = bridge.get_transaction_stats()
        assert stats["total"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["avg_latency"] == 15.0

    def test_get_transaction_stats_empty(self):
        bridge = CoverageBridge()
        stats = bridge.get_transaction_stats()
        assert stats["total"] == 0

    def test_export_to_json(self, tmp_path):
        bridge = CoverageBridge()
        bridge.record_transaction(TransactionType.READ, 0x1000, 0, 0, 10, True)

        filepath = tmp_path / "coverage.json"
        bridge.export_to_json(str(filepath))

        assert filepath.exists()

        import json
        with open(filepath) as f:
            data = json.load(f)
        assert "samples" in data
        assert "transactions" in data
        assert "summary" in data

    def test_reset(self):
        bridge = CoverageBridge()
        bridge.record_transaction(TransactionType.READ, 0x1000, 0, 0, 10, True)
        bridge.reset()
        assert len(bridge.samples) == 0
        assert len(bridge.transactions) == 0
