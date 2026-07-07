"""Transaction Trace Exporter

Exports transaction traces in standard formats for RTL verification.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from enum import Enum
import json
import csv


class TransactionState(Enum):
    """Transaction lifecycle states"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Transaction:
    """Memory transaction record"""
    id: int
    type: str  # READ, WRITE, REFRESH, etc.
    address: int
    start_cycle: int
    end_cycle: Optional[int] = None
    python_latency: int = 0
    rtl_latency: Optional[int] = None
    aligned: bool = False

    @property
    def latency(self) -> int:
        if self.end_cycle is not None:
            return self.end_cycle - self.start_cycle
        return 0


class TransactionExporter:
    """Exports transaction traces"""

    def __init__(self):
        self.transactions: List[Transaction] = []
        self._next_id = 0

    def begin_transaction(self, txn_type: str, address: int, start_cycle: int) -> int:
        """Start a new transaction

        Args:
            txn_type: Type of transaction (READ, WRITE, etc.)
            address: Memory address
            start_cycle: Start cycle

        Returns:
            Transaction ID
        """
        txn_id = self._next_id
        self._next_id += 1
        self.transactions.append(Transaction(
            id=txn_id,
            type=txn_type,
            address=address,
            start_cycle=start_cycle
        ))
        return txn_id

    def complete_transaction(self, txn_id: int, end_cycle: int,
                            python_latency: int, rtl_latency: Optional[int] = None) -> None:
        """Complete a transaction

        Args:
            txn_id: Transaction ID
            end_cycle: End cycle
            python_latency: Python model latency
            rtl_latency: RTL latency (optional)
        """
        for txn in self.transactions:
            if txn.id == txn_id:
                txn.end_cycle = end_cycle
                txn.python_latency = python_latency
                txn.rtl_latency = rtl_latency
                if rtl_latency is not None:
                    txn.aligned = abs(python_latency - rtl_latency) <= 1
                break

    def get_unaligned_transactions(self) -> List[Transaction]:
        """Get transactions with alignment issues"""
        return [t for t in self.transactions if not t.aligned and t.rtl_latency is not None]

    def get_alignment_stats(self) -> Dict[str, any]:
        """Get alignment statistics"""
        rtl_transactions = [t for t in self.transactions if t.rtl_latency is not None]
        total = len(rtl_transactions)
        aligned = len([t for t in rtl_transactions if t.aligned])
        return {
            "total_with_rtl": total,
            "aligned": aligned,
            "unaligned": total - aligned,
            "alignment_rate": aligned / total if total > 0 else 0
        }

    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics"""
        completed = [t for t in self.transactions if t.python_latency > 0]
        if not completed:
            return {"min": 0, "max": 0, "avg": 0}

        latencies = [t.python_latency for t in completed]
        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies)
        }

    def export_json(self, filepath: str) -> None:
        """Export to JSON format"""
        data = {
            "transactions": [asdict(t) for t in self.transactions],
            "alignment_stats": self.get_alignment_stats(),
            "latency_stats": self.get_latency_stats()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def export_csv(self, filepath: str) -> None:
        """Export to CSV format"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'type', 'address', 'start_cycle', 'end_cycle',
                           'python_latency', 'rtl_latency', 'aligned'])
            for t in self.transactions:
                writer.writerow([
                    t.id, t.type, hex(t.address), t.start_cycle, t.end_cycle,
                    t.python_latency, t.rtl_latency, t.aligned
                ])

    def reset(self) -> None:
        """Reset exporter state"""
        self.transactions.clear()
        self._next_id = 0
