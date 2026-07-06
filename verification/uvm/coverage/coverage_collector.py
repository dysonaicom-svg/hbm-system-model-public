#!/usr/bin/env python3
"""
Coverage Collector
Collects coverage data from HBM4 simulation and aggregates results
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import random


@dataclass
class SampleRecord:
    """Single coverage sample record"""
    timestamp: float
    covergroup: str
    coverpoint: str
    value: Any
    bin_name: str


@dataclass
class CoverageStats:
    """Coverage statistics"""
    total_samples: int = 0
    unique_bins_hit: int = 0
    total_bins: int = 0
    coverage_percent: float = 0.0


class CoverageDatabase:
    """In-memory coverage database"""

    def __init__(self):
        self.samples: List[SampleRecord] = []
        self.bin_counts: Dict[str, Dict[str, int]] = {}
        self.total_bins: Dict[str, int] = {}

    def record_sample(self, covergroup: str, coverpoint: str,
                      value: Any, bin_name: str) -> None:
        """Record a coverage sample"""
        record = SampleRecord(
            timestamp=datetime.now().timestamp(),
            covergroup=covergroup,
            coverpoint=coverpoint,
            value=value,
            bin_name=bin_name
        )
        self.samples.append(record)

        # Update bin counts
        key = f"{covergroup}.{coverpoint}"
        if key not in self.bin_counts:
            self.bin_counts[key] = {}
        self.bin_counts[key][bin_name] = self.bin_counts[key].get(bin_name, 0) + 1

    def set_total_bins(self, covergroup: str, coverpoint: str,
                       total: int) -> None:
        """Set total bins for a coverpoint"""
        key = f"{covergroup}.{coverpoint}"
        self.total_bins[key] = total

    def get_stats(self, covergroup: str, coverpoint: str) -> CoverageStats:
        """Get coverage statistics for a coverpoint"""
        key = f"{covergroup}.{coverpoint}"
        counts = self.bin_counts.get(key, {})
        unique_bins = len(counts)
        total = self.total_bins.get(key, unique_bins)

        return CoverageStats(
            total_samples=sum(counts.values()),
            unique_bins_hit=unique_bins,
            total_bins=total,
            coverage_percent=100.0 * unique_bins / total if total > 0 else 0.0
        )

    def export(self) -> Dict:
        """Export database to dict"""
        return {
            "samples": [
                {
                    "timestamp": s.timestamp,
                    "covergroup": s.covergroup,
                    "coverpoint": s.coverpoint,
                    "value": s.value,
                    "bin_name": s.bin_name
                }
                for s in self.samples
            ],
            "bin_counts": self.bin_counts,
            "total_bins": self.total_bins
        }


class CoverageCollector:
    """
    Coverage data collector
    Integrates with HBM4 simulation to collect functional coverage
    """

    def __init__(self, output_dir: str = "verification/uvm/reports"):
        self.db = CoverageDatabase()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._init_bin_definitions()

    def _init_bin_definitions(self) -> None:
        """Initialize bin definitions from coverage model"""
        # bank_conflict_cg
        self._register_bins("bank_conflict_cg", "bank_id", [
            "banks_0_15", "bank_groups_0_3", "bank_groups_4_7",
            "bank_groups_8_11", "bank_groups_12_15"
        ])
        self._register_bins("bank_conflict_cg", "conflict_type", [
            "same_bank_different_row", "same_row",
            "different_bank", "same_bank_same_row"
        ])
        self._register_bins("bank_conflict_cg", "bank_group_conflict", [
            "group0", "group1", "group2", "group3"
        ])

        # row_hammer_cg
        self._register_bins("row_hammer_cg", "hammer_bank", [
            "banks_0_15", "all_banks"
        ])
        self._register_bins("row_hammer_cg", "hammer_count", [
            "low", "medium", "high", "very_high", "extreme"
        ])
        self._register_bins("row_hammer_cg", "hammer_intensity", [
            "single_row", "adjacent_row", "both_adjacent"
        ])

        # refresh_cg
        self._register_bins("refresh_cg", "refresh_type", [
            "refresh_all", "refresh_group", "self_refresh", "partial_refresh"
        ])
        self._register_bins("refresh_cg", "refresh_bank", [
            "banks_0_15", "all_banks", "bank_group_0", "bank_group_1",
            "bank_group_2", "bank_group_3"
        ])
        self._register_bins("refresh_cg", "refresh_interval", [
            "very_short", "short", "normal", "long", "very_long"
        ])

        # channel_interleave_cg
        self._register_bins("channel_interleave_cg", "channel_id", [
            "channels_0_31", "pseudo_channel_0", "pseudo_channel_1"
        ])
        self._register_bins("channel_interleave_cg", "interleave_depth", [
            "single", "two_way", "four_way", "eight_way", "sixteen_way"
        ])
        self._register_bins("channel_interleave_cg", "interleave_pattern", [
            "sequential", "round_robin", "hash_based", "priority_based"
        ])
        self._register_bins("channel_interleave_cg", "channel_switches", [
            "low", "medium", "high", "very_high"
        ])

        # row_hit_miss_cg
        self._register_bins("row_hit_miss_cg", "access_type", [
            "row_hit", "row_miss", "row_conflict", "row_close"
        ])
        self._register_bins("row_hit_miss_cg", "channel", [
            "channels_0_31", "pc0", "pc1"
        ])
        self._register_bins("row_hit_miss_cg", "row_address", [
            "low_rows", "mid_rows", "high_rows"
        ])

        # queue_fullness_cg
        self._register_bins("queue_fullness_cg", "read_queue_depth", [
            "empty", "low", "medium", "high", "full"
        ])
        self._register_bins("queue_fullness_cg", "write_queue_depth", [
            "empty", "low", "medium", "high", "full"
        ])

        # command_type_cg
        self._register_bins("command_type_cg", "cmd_type", [
            "activate", "precharge", "read", "write", "refresh", "idle"
        ])
        self._register_bins("command_type_cg", "channel", [
            "channels_0_31", "pc0", "pc1"
        ])

        # latency_cg
        self._register_bins("latency_cg", "read_latency", [
            "very_fast", "fast", "normal", "slow", "very_slow"
        ])
        self._register_bins("latency_cg", "write_latency", [
            "very_fast", "fast", "normal", "slow", "very_slow"
        ])
        self._register_bins("latency_cg", "cmd_mix_latency", [
            "activate_latency", "read_latency", "write_latency"
        ])

        # bandwidth_cg
        self._register_bins("bandwidth_cg", "bandwidth_util", [
            "idle", "low", "medium", "high", "very_high"
        ])
        self._register_bins("bandwidth_cg", "read_write_ratio", [
            "read_heavy", "balanced", "write_heavy"
        ])
        self._register_bins("bandwidth_cg", "data_width_util", [
            "quarter", "half", "three_quarter", "full"
        ])

        # qos_priority_cg
        self._register_bins("qos_priority_cg", "priority", [
            "critical", "high", "medium_high", "medium",
            "medium_low", "low", "background"
        ])
        self._register_bins("qos_priority_cg", "channel", [
            "channels_0_31", "pc0", "pc1"
        ])
        self._register_bins("qos_priority_cg", "priority_transition", [
            "same_priority", "up_one", "up_many",
            "down_one", "down_few", "down_many"
        ])
        self._register_bins("qos_priority_cg", "starvation_cycles", [
            "none", "short", "medium", "long", "severe"
        ])

        # transaction_cg
        self._register_bins("transaction_cg", "transaction_type", [
            "single_read", "single_write", "burst_read", "burst_write",
            "read_modify_write", "activate", "precharge", "refresh"
        ])
        self._register_bins("transaction_cg", "address_pattern", [
            "sequential", "random", "stride",
            "bank_interleaved", "row_interleaved"
        ])
        self._register_bins("transaction_cg", "data_pattern", [
            "all_zeros", "all_ones", "walking_one",
            "walking_zero", "checkerboard", "random_data"
        ])

    def _register_bins(self, covergroup: str, coverpoint: str,
                       bins: List[str]) -> None:
        """Register bin definitions"""
        key = f"{covergroup}.{coverpoint}"
        self.db.total_bins[key] = len(bins)

    def collect(self, covergroup: str, coverpoint: str,
                value: int, bin_name: str) -> None:
        """Collect a coverage sample"""
        self.db.record_sample(covergroup, coverpoint, value, bin_name)

    def collect_bank_conflict(self, bank_id: int, conflict_type: int,
                              bank_group: int) -> None:
        """Collect bank conflict samples"""
        # Determine bank_id bin
        if 0 <= bank_id <= 15:
            self.collect("bank_conflict_cg", "bank_id", bank_id, "banks_0_15")
            if 0 <= bank_id <= 3:
                self.collect("bank_conflict_cg", "bank_id", bank_id, "bank_groups_0_3")
            elif 4 <= bank_id <= 7:
                self.collect("bank_conflict_cg", "bank_id", bank_id, "bank_groups_4_7")
            elif 8 <= bank_id <= 11:
                self.collect("bank_conflict_cg", "bank_id", bank_id, "bank_groups_8_11")
            elif 12 <= bank_id <= 15:
                self.collect("bank_conflict_cg", "bank_id", bank_id, "bank_groups_12_15")

        # Conflict type bins
        conflict_bins = {
            0: "different_bank",
            1: "same_bank_different_row",
            2: "same_row",
            3: "same_bank_same_row"
        }
        if conflict_type in conflict_bins:
            self.collect("bank_conflict_cg", "conflict_type", conflict_type,
                        conflict_bins[conflict_type])

        # Bank group bins
        if 0 <= bank_group <= 3:
            self.collect("bank_conflict_cg", "bank_group_conflict", bank_group,
                       f"group{bank_group}")

    def collect_row_hit_miss(self, access_type: int, channel: int,
                             row_addr: int) -> None:
        """Collect row hit/miss samples"""
        # Access type bins
        access_bins = {
            0: "row_miss",
            1: "row_conflict",
            2: "row_hit",
            3: "row_close"
        }
        if access_type in access_bins:
            self.collect("row_hit_miss_cg", "access_type", access_type,
                        access_bins[access_type])

        # Channel bins
        if 0 <= channel <= 31:
            self.collect("row_hit_miss_cg", "channel", channel, "channels_0_31")
            if 0 <= channel <= 15:
                self.collect("row_hit_miss_cg", "channel", channel, "pc0")
            else:
                self.collect("row_hit_miss_cg", "channel", channel, "pc1")

        # Row address bins
        if 0 <= row_addr <= 255:
            self.collect("row_hit_miss_cg", "row_address", row_addr, "low_rows")
        elif 256 <= row_addr <= 16383:
            self.collect("row_hit_miss_cg", "row_address", row_addr, "mid_rows")
        elif 16384 <= row_addr <= 65535:
            self.collect("row_hit_miss_cg", "row_address", row_addr, "high_rows")

    def collect_command(self, cmd_type: int, channel: int) -> None:
        """Collect command type samples"""
        cmd_bins = {
            0: "idle",
            1: "write",
            2: "read",
            3: "activate",
            4: "precharge",
            5: "refresh"
        }
        if cmd_type in cmd_bins:
            self.collect("command_type_cg", "cmd_type", cmd_type, cmd_bins[cmd_type])

        # Channel bins
        if 0 <= channel <= 31:
            self.collect("command_type_cg", "channel", channel, "channels_0_31")
            if 0 <= channel <= 15:
                self.collect("command_type_cg", "channel", channel, "pc0")
            else:
                self.collect("command_type_cg", "channel", channel, "pc1")

    def collect_qos(self, priority: int, channel: int,
                    starvation: int) -> None:
        """Collect QoS priority samples"""
        # Priority bins
        if priority == 0:
            self.collect("qos_priority_cg", "priority", priority, "background")
        elif 1 <= priority <= 4:
            self.collect("qos_priority_cg", "priority", priority, "low")
        elif 5 <= priority <= 7:
            self.collect("qos_priority_cg", "priority", priority, "medium_low")
        elif 8 <= priority <= 9:
            self.collect("qos_priority_cg", "priority", priority, "medium")
        elif 10 <= priority <= 11:
            self.collect("qos_priority_cg", "priority", priority, "medium_high")
        elif 12 <= priority <= 14:
            self.collect("qos_priority_cg", "priority", priority, "high")
        elif priority == 15:
            self.collect("qos_priority_cg", "priority", priority, "critical")

        # Channel bins
        if 0 <= channel <= 31:
            self.collect("qos_priority_cg", "channel", channel, "channels_0_31")

        # Starvation bins
        if starvation == 0:
            self.collect("qos_priority_cg", "starvation_cycles", starvation, "none")
        elif 1 <= starvation <= 50:
            self.collect("qos_priority_cg", "starvation_cycles", starvation, "short")
        elif 51 <= starvation <= 200:
            self.collect("qos_priority_cg", "starvation_cycles", starvation, "medium")
        elif 201 <= starvation <= 1000:
            self.collect("qos_priority_cg", "starvation_cycles", starvation, "long")
        elif starvation > 1000:
            self.collect("qos_priority_cg", "starvation_cycles", starvation, "severe")

    def collect_refresh(self, refresh_type: int, bank_id: int) -> None:
        """Collect refresh samples"""
        refresh_bins = {
            0: "refresh_all",
            1: "refresh_group",
            2: "self_refresh",
            3: "partial_refresh"
        }
        if refresh_type in refresh_bins:
            self.collect("refresh_cg", "refresh_type", refresh_type,
                        refresh_bins[refresh_type])

        # Bank bins
        if 0 <= bank_id <= 15:
            self.collect("refresh_cg", "refresh_bank", bank_id, "banks_0_15")
            if 0 <= bank_id <= 3:
                self.collect("refresh_cg", "refresh_bank", bank_id, "bank_group_0")
            elif 4 <= bank_id <= 7:
                self.collect("refresh_cg", "refresh_bank", bank_id, "bank_group_1")
            elif 8 <= bank_id <= 11:
                self.collect("refresh_cg", "refresh_bank", bank_id, "bank_group_2")
            elif 12 <= bank_id <= 15:
                self.collect("refresh_cg", "refresh_bank", bank_id, "bank_group_3")

    def collect_latency(self, read_latency: int, write_latency: int) -> None:
        """Collect latency samples"""
        # Read latency bins
        if 0 <= read_latency <= 20:
            self.collect("latency_cg", "read_latency", read_latency, "very_fast")
        elif 21 <= read_latency <= 40:
            self.collect("latency_cg", "read_latency", read_latency, "fast")
        elif 41 <= read_latency <= 60:
            self.collect("latency_cg", "read_latency", read_latency, "normal")
        elif 61 <= read_latency <= 100:
            self.collect("latency_cg", "read_latency", read_latency, "slow")
        elif read_latency > 100:
            self.collect("latency_cg", "read_latency", read_latency, "very_slow")

        # Write latency bins
        if 0 <= write_latency <= 10:
            self.collect("latency_cg", "write_latency", write_latency, "very_fast")
        elif 11 <= write_latency <= 20:
            self.collect("latency_cg", "write_latency", write_latency, "fast")
        elif 21 <= write_latency <= 40:
            self.collect("latency_cg", "write_latency", write_latency, "normal")
        elif 41 <= write_latency <= 60:
            self.collect("latency_cg", "write_latency", write_latency, "slow")
        elif write_latency > 60:
            self.collect("latency_cg", "write_latency", write_latency, "very_slow")

    def collect_bandwidth(self, bw_util: int, rw_ratio: int) -> None:
        """Collect bandwidth samples"""
        # Bandwidth utilization bins
        if bw_util == 0:
            self.collect("bandwidth_cg", "bandwidth_util", bw_util, "idle")
        elif 1 <= bw_util <= 25:
            self.collect("bandwidth_cg", "bandwidth_util", bw_util, "low")
        elif 26 <= bw_util <= 50:
            self.collect("bandwidth_cg", "bandwidth_util", bw_util, "medium")
        elif 51 <= bw_util <= 75:
            self.collect("bandwidth_cg", "bandwidth_util", bw_util, "high")
        elif 76 <= bw_util <= 100:
            self.collect("bandwidth_cg", "bandwidth_util", bw_util, "very_high")

        # Read/write ratio bins
        if 0 <= rw_ratio <= 30:
            self.collect("bandwidth_cg", "read_write_ratio", rw_ratio, "read_heavy")
        elif 31 <= rw_ratio <= 69:
            self.collect("bandwidth_cg", "read_write_ratio", rw_ratio, "balanced")
        elif 70 <= rw_ratio <= 100:
            self.collect("bandwidth_cg", "read_write_ratio", rw_ratio, "write_heavy")

    def get_summary(self) -> Dict:
        """Get coverage summary"""
        covergroups = [
            "bank_conflict_cg", "row_hammer_cg", "refresh_cg",
            "channel_interleave_cg", "row_hit_miss_cg", "queue_fullness_cg",
            "command_type_cg", "latency_cg", "bandwidth_cg",
            "qos_priority_cg", "transaction_cg"
        ]

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_samples": len(self.db.samples),
            "covergroups": {}
        }

        for cg in covergroups:
            cg_key = cg
            cg_bins = {k: v for k, v in self.db.total_bins.items()
                      if k.startswith(cg)}
            hit_bins = {k: len(v) for k, v in self.db.bin_counts.items()
                       if k.startswith(cg)}

            total = sum(cg_bins.values())
            hit = sum(hit_bins.values())
            cov_pct = 100.0 * hit / total if total > 0 else 0.0

            summary["covergroups"][cg] = {
                "coverage_percent": cov_pct,
                "bins_hit": hit,
                "total_bins": total
            }

        return summary

    def save_report(self, filename: str = "coverage_data.json") -> Path:
        """Save coverage report to file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "database": self.db.export()
        }

        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return output_path


def demo():
    """Self-check demo"""
    collector = CoverageCollector()

    # Simulate coverage collection
    for i in range(200):
        collector.collect_bank_conflict(
            bank_id=random.randint(0, 15),
            conflict_type=random.randint(0, 3),
            bank_group=random.randint(0, 3)
        )
        collector.collect_row_hit_miss(
            access_type=random.randint(0, 3),
            channel=random.randint(0, 31),
            row_addr=random.randint(0, 65535)
        )
        collector.collect_command(
            cmd_type=random.randint(0, 5),
            channel=random.randint(0, 31)
        )
        collector.collect_qos(
            priority=random.randint(0, 15),
            channel=random.randint(0, 31),
            starvation=random.randint(0, 1000)
        )

    summary = collector.get_summary()
    print(f"Total samples: {summary['total_samples']}")
    for cg, stats in summary["covergroups"].items():
        print(f"  {cg}: {stats['coverage_percent']:.1f}%")

    output = collector.save_report()
    print(f"Coverage report saved: {output}")
    print("Collector self-check passed")


if __name__ == "__main__":
    demo()
