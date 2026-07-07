"""Coverage Bridge between Python Model and UVM

Provides Python-side coverage collection that feeds into UVM coverage database.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class TransactionType(Enum):
    """Types of memory transactions"""
    READ = "read"
    WRITE = "write"
    REFRESH = "refresh"
    ACTIVATE = "activate"
    PRECHARGE = "precharge"


@dataclass
class CoverageSample:
    """A single coverage sample"""
    group: str
    name: str
    value: Any
    cycle: int


@dataclass
class TransactionCoverage:
    """Coverage data for a transaction"""
    txn_type: TransactionType
    address: int
    bank: int
    channel: int
    latency_cycles: int
    is_hit: bool


class CoverageBridge:
    """Bridges Python model coverage to UVM coverage database"""

    def __init__(self):
        self.samples: List[CoverageSample] = []
        self.transactions: List[TransactionCoverage] = []
        self._transaction_count = 0

    def record_transaction(self, txn_type: TransactionType, address: int,
                          bank: int, channel: int, latency: int, is_hit: bool) -> None:
        """Record a transaction for coverage

        Args:
            txn_type: Type of transaction
            address: Memory address
            bank: Bank ID
            channel: Channel ID
            latency: Latency in cycles
            is_hit: Whether this was a row hit
        """
        self._transaction_count += 1
        self.transactions.append(TransactionCoverage(
            txn_type=txn_type,
            address=address,
            bank=bank,
            channel=channel,
            latency_cycles=latency,
            is_hit=is_hit
        ))
        self.samples.append(CoverageSample(
            group="transaction",
            name=txn_type.value,
            value=address,
            cycle=latency
        ))

    def record_bank_access(self, bank: int, row: int, is_hit: bool) -> None:
        """Record a bank access for coverage"""
        self.samples.append(CoverageSample(
            group="bank_access",
            name=f"bank_{bank}",
            value=row,
            cycle=0
        ))

    def record_qos_level(self, level: int) -> None:
        """Record QoS level for coverage"""
        self.samples.append(CoverageSample(
            group="qos",
            name=f"level_{level}",
            value=level,
            cycle=0
        ))

    def record_channel_utilization(self, channel: int, busy: bool) -> None:
        """Record channel utilization"""
        self.samples.append(CoverageSample(
            group="channel_util",
            name=f"ch_{channel}" + ("_busy" if busy else "_idle"),
            value=int(busy),
            cycle=0
        ))

    def get_coverage_summary(self) -> Dict[str, int]:
        """Get coverage summary by group"""
        summary: Dict[str, int] = {}
        for sample in self.samples:
            summary[sample.group] = summary.get(sample.group, 0) + 1
        return summary

    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics"""
        if not self.transactions:
            return {"total": 0}

        hit_count = sum(1 for t in self.transactions if t.is_hit)
        total_latency = sum(t.latency_cycles for t in self.transactions)

        return {
            "total": len(self.transactions),
            "hits": hit_count,
            "misses": len(self.transactions) - hit_count,
            "hit_rate": hit_count / len(self.transactions),
            "avg_latency": total_latency / len(self.transactions),
        }

    def export_to_json(self, filepath: str) -> None:
        """Export coverage data to JSON"""
        data = {
            "samples": [
                {"group": s.group, "name": s.name, "value": str(s.value), "cycle": s.cycle}
                for s in self.samples
            ],
            "transactions": [
                {
                    "type": t.txn_type.value,
                    "address": hex(t.address),
                    "bank": t.bank,
                    "channel": t.channel,
                    "latency": t.latency_cycles,
                    "hit": t.is_hit
                }
                for t in self.transactions
            ],
            "summary": self.get_coverage_summary(),
            "stats": self.get_transaction_stats()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def reset(self) -> None:
        """Reset coverage data"""
        self.samples.clear()
        self.transactions.clear()
        self._transaction_count = 0
