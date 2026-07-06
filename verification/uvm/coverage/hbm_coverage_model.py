#!/usr/bin/env python3
"""
HBM4 Functional Coverage Model
Coverpoints and cross coverage for HBM4 verification
"""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import random


class HBM4Command(IntEnum):
    """HBM4 Command Types"""
    IDLE = 0b000
    WRITE = 0b001
    READ = 0b010
    ACTIVATE = 0b011
    PRECHARGE = 0b100
    REFRESH = 0b101
    MRS = 0b110
    SELF_REFRESH = 0b111


class AccessType(IntEnum):
    """Memory access types"""
    ROW_MISS = 0
    ROW_CONFLICT = 1
    ROW_HIT = 2
    ROW_CLOSE = 3


class ConflictType(IntEnum):
    """Bank conflict types"""
    DIFFERENT_BANK = 0
    SAME_BANK_DIFFERENT_ROW = 1
    SAME_ROW = 2
    SAME_BANK_SAME_ROW = 3


class RefreshType(IntEnum):
    """Refresh types"""
    REFRESH_ALL = 0
    REFRESH_GROUP = 1
    SELF_REFRESH_ENTRY = 2
    PARTIAL_REFRESH = 3


class InterleavePattern(IntEnum):
    """Channel interleave patterns"""
    SEQUENTIAL = 0
    ROUND_ROBIN = 1
    HASH_BASED = 2
    PRIORITY_BASED = 3


class AddressPattern(IntEnum):
    """Address patterns for transactions"""
    SEQUENTIAL = 0
    RANDOM = 1
    STRIDE = 2
    BANK_INTERLEAVED = 3
    ROW_INTERLEAVED = 4


class DataPattern(IntEnum):
    """Data patterns"""
    ALL_ZEROS = 0
    ALL_ONES = 1
    WALKING_ONE = 2
    WALKING_ZERO = 3
    CHECKERBOARD = 4
    RANDOM_DATA = 5


@dataclass
class BinRange:
    """Coverage bin definition"""
    name: str
    min_val: int
    max_val: int

    def contains(self, value: int) -> bool:
        return self.min_val <= value <= self.max_val


class Coverpoint:
    """Single coverage point with bins"""

    def __init__(self, name: str, bins: List[BinRange]):
        self.name = name
        self.bins = {b.name: b for b in bins}
        self.hit_bins: Set[str] = set()
        self.sample_count: int = 0

    def sample(self, value: int) -> None:
        """Sample a value into the appropriate bin"""
        self.sample_count += 1
        for bin_name, bin_def in self.bins.items():
            if bin_def.contains(value):
                self.hit_bins.add(bin_name)
                return

    @property
    def coverage_percent(self) -> float:
        if not self.bins:
            return 0.0
        return 100.0 * len(self.hit_bins) / len(self.bins)

    def get_uncovered_bins(self) -> List[str]:
        return [b for b in self.bins if b not in self.hit_bins]


class CrossCoverage:
    """Cross coverage between two coverpoints"""

    def __init__(self, name: str, cp1: Coverpoint, cp2: Coverpoint):
        self.name = name
        self.cp1 = cp1
        self.cp2 = cp2
        self.hit_pairs: Set[Tuple[str, str]] = set()
        self.sample_count: int = 0

    def sample(self, val1: int, val2: int) -> None:
        """Sample cross coverage values"""
        self.sample_count += 1
        # Find which bins were hit
        bin1 = self._find_bin(self.cp1, val1)
        bin2 = self._find_bin(self.cp2, val2)
        if bin1 and bin2:
            self.hit_pairs.add((bin1, bin2))

    def _find_bin(self, cp: Coverpoint, value: int) -> Optional[str]:
        for bin_name, bin_def in cp.bins.items():
            if bin_def.contains(value):
                return bin_name
        return None

    @property
    def coverage_percent(self) -> float:
        total_pairs = len(self.cp1.bins) * len(self.cp2.bins)
        if total_pairs == 0:
            return 0.0
        return 100.0 * len(self.hit_pairs) / total_pairs


class Covergroup:
    """Coverage group containing coverpoints and cross coverage"""

    def __init__(self, name: str, goal: float = 100.0):
        self.name = name
        self.goal = goal
        self.coverpoints: Dict[str, Coverpoint] = {}
        self.cross_coverage: Dict[str, CrossCoverage] = {}
        self.option_per_instance = True

    def add_coverpoint(self, name: str, bins: List[BinRange]) -> Coverpoint:
        cp = Coverpoint(name, bins)
        self.coverpoints[name] = cp
        return cp

    def add_cross(self, name: str, cp1: str, cp2: str) -> CrossCoverage:
        cross = CrossCoverage(name, self.coverpoints[cp1], self.coverpoints[cp2])
        self.cross_coverage[name] = cross
        return cross

    def sample(self, sample_dict: Dict[str, int]) -> None:
        """Sample all coverpoints"""
        for name, value in sample_dict.items():
            if name in self.coverpoints:
                self.coverpoints[name].sample(value)

    @property
    def coverage_percent(self) -> float:
        total = len(self.coverpoints) + len(self.cross_coverage)
        if total == 0:
            return 0.0
        cp_cov = sum(cp.coverage_percent for cp in self.coverpoints.values())
        cross_cov = sum(c.coverage_percent for c in self.cross_coverage.values())
        return (cp_cov + cross_cov) / total


class HBM4CoverageModel:
    """
    Comprehensive functional coverage model for HBM4
    Based on hbm_coverage.sv covergroups
    """

    def __init__(self):
        self.covergroups: Dict[str, Covergroup] = {}
        self._build_coverage_model()

    def _build_coverage_model(self) -> None:
        """Build all coverage groups"""
        self._build_bank_conflict_cg()
        self._build_row_hammer_cg()
        self._build_refresh_cg()
        self._build_channel_interleave_cg()
        self._build_row_hit_miss_cg()
        self._build_queue_fullness_cg()
        self._build_command_type_cg()
        self._build_latency_cg()
        self._build_bandwidth_cg()
        self._build_qos_priority_cg()
        self._build_transaction_cg()

    def _build_bank_conflict_cg(self) -> None:
        """Bank conflict coverage group"""
        cg = Covergroup("bank_conflict_cg", goal=100.0)

        # Bank ID bins
        cg.add_coverpoint("bank_id", [
            BinRange("banks_0_15", 0, 15),
            BinRange("bank_groups_0_3", 0, 3),
            BinRange("bank_groups_4_7", 4, 7),
            BinRange("bank_groups_8_11", 8, 11),
            BinRange("bank_groups_12_15", 12, 15),
        ])

        # Conflict type bins
        cg.add_coverpoint("conflict_type", [
            BinRange("same_bank_different_row", 1, 1),
            BinRange("same_row", 2, 2),
            BinRange("different_bank", 0, 0),
            BinRange("same_bank_same_row", 3, 3),
        ])

        # Bank group conflict
        cg.add_coverpoint("bank_group_conflict", [
            BinRange("group0", 0, 0),
            BinRange("group1", 1, 1),
            BinRange("group2", 2, 2),
            BinRange("group3", 3, 3),
        ])

        cg.add_cross("bank_conflict_cross", "bank_id", "conflict_type")
        self.covergroups["bank_conflict_cg"] = cg

    def _build_row_hammer_cg(self) -> None:
        """Row hammer pattern coverage group"""
        cg = Covergroup("row_hammer_cg", goal=90.0)

        cg.add_coverpoint("hammer_bank", [
            BinRange("banks_0_15", 0, 15),
            BinRange("all_banks", 0, 15),
        ])

        cg.add_coverpoint("hammer_count", [
            BinRange("low", 1, 10),
            BinRange("medium", 11, 50),
            BinRange("high", 51, 100),
            BinRange("very_high", 101, 500),
            BinRange("extreme", 501, 10000),
        ])

        cg.add_coverpoint("hammer_intensity", [
            BinRange("single_row", 1, 1),
            BinRange("adjacent_row", 2, 2),
            BinRange("both_adjacent", 3, 3),
        ])

        cg.add_cross("hammer_bank_intensity_cross", "hammer_bank", "hammer_intensity")
        self.covergroups["row_hammer_cg"] = cg

    def _build_refresh_cg(self) -> None:
        """Refresh command coverage group"""
        cg = Covergroup("refresh_cg", goal=100.0)

        cg.add_coverpoint("refresh_type", [
            BinRange("refresh_all", 0, 0),
            BinRange("refresh_group", 1, 1),
            BinRange("self_refresh", 2, 2),
            BinRange("partial_refresh", 3, 3),
        ])

        cg.add_coverpoint("refresh_bank", [
            BinRange("banks_0_15", 0, 15),
            BinRange("all_banks", 0, 15),
            BinRange("bank_group_0", 0, 3),
            BinRange("bank_group_1", 4, 7),
            BinRange("bank_group_2", 8, 11),
            BinRange("bank_group_3", 12, 15),
        ])

        cg.add_coverpoint("refresh_interval", [
            BinRange("very_short", 1, 10),
            BinRange("short", 11, 50),
            BinRange("normal", 51, 200),
            BinRange("long", 201, 1000),
            BinRange("very_long", 1001, 100000),
        ])

        cg.add_cross("refresh_type_bank_cross", "refresh_type", "refresh_bank")
        self.covergroups["refresh_cg"] = cg

    def _build_channel_interleave_cg(self) -> None:
        """Channel interleaving coverage group"""
        cg = Covergroup("channel_interleave_cg", goal=95.0)

        cg.add_coverpoint("channel_id", [
            BinRange("channels_0_31", 0, 31),
            BinRange("pseudo_channel_0", 0, 15),
            BinRange("pseudo_channel_1", 16, 31),
        ])

        cg.add_coverpoint("interleave_depth", [
            BinRange("single", 1, 1),
            BinRange("two_way", 2, 2),
            BinRange("four_way", 4, 4),
            BinRange("eight_way", 8, 8),
            BinRange("sixteen_way", 16, 16),
        ])

        cg.add_coverpoint("interleave_pattern", [
            BinRange("sequential", 0, 0),
            BinRange("round_robin", 1, 1),
            BinRange("hash_based", 2, 2),
            BinRange("priority_based", 3, 3),
        ])

        cg.add_coverpoint("channel_switches", [
            BinRange("low", 1, 5),
            BinRange("medium", 6, 20),
            BinRange("high", 21, 50),
            BinRange("very_high", 51, 1000),
        ])

        cg.add_cross("channel_pattern_cross", "channel_id", "interleave_pattern")
        self.covergroups["channel_interleave_cg"] = cg

    def _build_row_hit_miss_cg(self) -> None:
        """Row hit/miss coverage group"""
        cg = Covergroup("row_hit_miss_cg", goal=100.0)

        cg.add_coverpoint("access_type", [
            BinRange("row_hit", 2, 2),
            BinRange("row_miss", 0, 0),
            BinRange("row_conflict", 1, 1),
            BinRange("row_close", 3, 3),
        ])

        cg.add_coverpoint("channel", [
            BinRange("channels_0_31", 0, 31),
            BinRange("pc0", 0, 15),
            BinRange("pc1", 16, 31),
        ])

        cg.add_coverpoint("row_address", [
            BinRange("low_rows", 0, 255),
            BinRange("mid_rows", 256, 16383),
            BinRange("high_rows", 16384, 65535),
        ])

        cg.add_cross("access_channel_cross", "access_type", "channel")
        cg.add_cross("access_row_cross", "access_type", "row_address")
        self.covergroups["row_hit_miss_cg"] = cg

    def _build_queue_fullness_cg(self) -> None:
        """Queue fullness coverage group"""
        cg = Covergroup("queue_fullness_cg", goal=90.0)

        cg.add_coverpoint("read_queue_depth", [
            BinRange("empty", 0, 4),
            BinRange("low", 5, 10),
            BinRange("medium", 11, 20),
            BinRange("high", 21, 30),
            BinRange("full", 31, 32),
        ])

        cg.add_coverpoint("write_queue_depth", [
            BinRange("empty", 0, 4),
            BinRange("low", 5, 10),
            BinRange("medium", 11, 20),
            BinRange("high", 21, 30),
            BinRange("full", 31, 32),
        ])

        cg.add_cross("queue_cross", "read_queue_depth", "write_queue_depth")
        self.covergroups["queue_fullness_cg"] = cg

    def _build_command_type_cg(self) -> None:
        """Command type coverage group"""
        cg = Covergroup("command_type_cg", goal=100.0)

        cg.add_coverpoint("cmd_type", [
            BinRange("activate", 3, 3),
            BinRange("precharge", 4, 4),
            BinRange("read", 2, 2),
            BinRange("write", 1, 1),
            BinRange("refresh", 5, 5),
            BinRange("idle", 0, 0),
        ])

        cg.add_coverpoint("channel", [
            BinRange("channels_0_31", 0, 31),
            BinRange("pc0", 0, 15),
            BinRange("pc1", 16, 31),
        ])

        cg.add_cross("cmd_channel_cross", "cmd_type", "channel")
        self.covergroups["command_type_cg"] = cg

    def _build_latency_cg(self) -> None:
        """Latency coverage group"""
        cg = Covergroup("latency_cg", goal=95.0)

        cg.add_coverpoint("read_latency", [
            BinRange("very_fast", 0, 20),
            BinRange("fast", 21, 40),
            BinRange("normal", 41, 60),
            BinRange("slow", 61, 100),
            BinRange("very_slow", 101, 10000),
        ])

        cg.add_coverpoint("write_latency", [
            BinRange("very_fast", 0, 10),
            BinRange("fast", 11, 20),
            BinRange("normal", 21, 40),
            BinRange("slow", 41, 60),
            BinRange("very_slow", 61, 10000),
        ])

        cg.add_coverpoint("cmd_mix_latency", [
            BinRange("activate_latency", 3, 3),
            BinRange("read_latency", 2, 2),
            BinRange("write_latency", 1, 1),
        ])

        cg.add_cross("cmd_read_latency_cross", "cmd_mix_latency", "read_latency")
        cg.add_cross("cmd_write_latency_cross", "cmd_mix_latency", "write_latency")
        self.covergroups["latency_cg"] = cg

    def _build_bandwidth_cg(self) -> None:
        """Bandwidth coverage group"""
        cg = Covergroup("bandwidth_cg", goal=90.0)

        cg.add_coverpoint("bandwidth_util", [
            BinRange("idle", 0, 0),
            BinRange("low", 1, 25),
            BinRange("medium", 26, 50),
            BinRange("high", 51, 75),
            BinRange("very_high", 76, 100),
        ])

        cg.add_coverpoint("read_write_ratio", [
            BinRange("read_heavy", 0, 30),
            BinRange("balanced", 31, 69),
            BinRange("write_heavy", 70, 100),
        ])

        cg.add_coverpoint("data_width_util", [
            BinRange("quarter", 0, 25),
            BinRange("half", 26, 50),
            BinRange("three_quarter", 51, 75),
            BinRange("full", 76, 100),
        ])

        cg.add_cross("bw_rw_ratio_cross", "bandwidth_util", "read_write_ratio")
        self.covergroups["bandwidth_cg"] = cg

    def _build_qos_priority_cg(self) -> None:
        """QoS priority coverage group"""
        cg = Covergroup("qos_priority_cg", goal=100.0)

        cg.add_coverpoint("priority", [
            BinRange("critical", 15, 15),
            BinRange("high", 12, 14),
            BinRange("medium_high", 10, 11),
            BinRange("medium", 8, 9),
            BinRange("medium_low", 5, 7),
            BinRange("low", 1, 4),
            BinRange("background", 0, 0),
        ])

        cg.add_coverpoint("channel", [
            BinRange("channels_0_31", 0, 31),
            BinRange("pc0", 0, 15),
            BinRange("pc1", 16, 31),
        ])

        cg.add_coverpoint("priority_transition", [
            BinRange("same_priority", 0, 0),
            BinRange("up_one", 1, 4),
            BinRange("up_many", 5, 15),
            BinRange("down_one", 16, 16),
            BinRange("down_few", 17, 20),
            BinRange("down_many", 21, 31),
        ])

        cg.add_coverpoint("starvation_cycles", [
            BinRange("none", 0, 0),
            BinRange("short", 1, 50),
            BinRange("medium", 51, 200),
            BinRange("long", 201, 1000),
            BinRange("severe", 1001, 100000),
        ])

        cg.add_cross("priority_channel_cross", "priority", "channel")
        cg.add_cross("priority_starvation_cross", "priority", "starvation_cycles")
        self.covergroups["qos_priority_cg"] = cg

    def _build_transaction_cg(self) -> None:
        """Transaction coverage group"""
        cg = Covergroup("transaction_cg", goal=85.0)

        cg.add_coverpoint("transaction_type", [
            BinRange("single_read", 0, 0),
            BinRange("single_write", 1, 1),
            BinRange("burst_read", 2, 2),
            BinRange("burst_write", 3, 3),
            BinRange("read_modify_write", 4, 4),
            BinRange("activate", 5, 5),
            BinRange("precharge", 6, 6),
            BinRange("refresh", 7, 7),
        ])

        cg.add_coverpoint("address_pattern", [
            BinRange("sequential", 0, 0),
            BinRange("random", 1, 1),
            BinRange("stride", 2, 2),
            BinRange("bank_interleaved", 3, 3),
            BinRange("row_interleaved", 4, 4),
        ])

        cg.add_coverpoint("data_pattern", [
            BinRange("all_zeros", 0, 0),
            BinRange("all_ones", 1, 1),
            BinRange("walking_one", 2, 2),
            BinRange("walking_zero", 3, 3),
            BinRange("checkerboard", 4, 4),
            BinRange("random_data", 5, 5),
        ])

        cg.add_cross("trans_addr_cross", "transaction_type", "address_pattern")
        self.covergroups["transaction_cg"] = cg

    def sample_bank_conflict(self, bank_id: int, conflict_type: int,
                             bank_group: int) -> None:
        """Sample bank conflict coverage"""
        cg = self.covergroups["bank_conflict_cg"]
        cg.sample({
            "bank_id": bank_id,
            "conflict_type": conflict_type,
            "bank_group_conflict": bank_group,
        })

    def sample_row_hammer(self, bank_id: int, count: int, intensity: int) -> None:
        """Sample row hammer coverage"""
        cg = self.covergroups["row_hammer_cg"]
        cg.sample({
            "hammer_bank": bank_id,
            "hammer_count": count,
            "hammer_intensity": intensity,
        })

    def sample_refresh(self, refresh_type: int, bank_id: int,
                       interval: int) -> None:
        """Sample refresh coverage"""
        cg = self.covergroups["refresh_cg"]
        cg.sample({
            "refresh_type": refresh_type,
            "refresh_bank": bank_id,
            "refresh_interval": interval,
        })

    def sample_channel_interleave(self, channel_id: int, depth: int,
                                   pattern: int, switches: int) -> None:
        """Sample channel interleaving coverage"""
        cg = self.covergroups["channel_interleave_cg"]
        cg.sample({
            "channel_id": channel_id,
            "interleave_depth": depth,
            "interleave_pattern": pattern,
            "channel_switches": switches,
        })

    def sample_row_hit_miss(self, access_type: int, channel: int,
                            row_addr: int) -> None:
        """Sample row hit/miss coverage"""
        cg = self.covergroups["row_hit_miss_cg"]
        cg.sample({
            "access_type": access_type,
            "channel": channel,
            "row_address": row_addr,
        })

    def sample_queue_fullness(self, read_depth: int,
                               write_depth: int) -> None:
        """Sample queue fullness coverage"""
        cg = self.covergroups["queue_fullness_cg"]
        cg.sample({
            "read_queue_depth": read_depth,
            "write_queue_depth": write_depth,
        })

    def sample_command(self, cmd_type: int, channel: int) -> None:
        """Sample command type coverage"""
        cg = self.covergroups["command_type_cg"]
        cg.sample({
            "cmd_type": cmd_type,
            "channel": channel,
        })

    def sample_latency(self, read_lat: int, write_lat: int,
                       cmd_type: int) -> None:
        """Sample latency coverage"""
        cg = self.covergroups["latency_cg"]
        cg.sample({
            "read_latency": read_lat,
            "write_latency": write_lat,
            "cmd_mix_latency": cmd_type,
        })

    def sample_bandwidth(self, bw_util: int, rw_ratio: int,
                         width_util: int) -> None:
        """Sample bandwidth coverage"""
        cg = self.covergroups["bandwidth_cg"]
        cg.sample({
            "bandwidth_util": bw_util,
            "read_write_ratio": rw_ratio,
            "data_width_util": width_util,
        })

    def sample_qos(self, priority: int, channel: int,
                   transition: int, starvation: int) -> None:
        """Sample QoS priority coverage"""
        cg = self.covergroups["qos_priority_cg"]
        cg.sample({
            "priority": priority,
            "channel": channel,
            "priority_transition": transition,
            "starvation_cycles": starvation,
        })

    def sample_transaction(self, trans_type: int, addr_pattern: int,
                           data_pattern: int) -> None:
        """Sample transaction coverage"""
        cg = self.covergroups["transaction_cg"]
        cg.sample({
            "transaction_type": trans_type,
            "address_pattern": addr_pattern,
            "data_pattern": data_pattern,
        })

    def get_coverage_report(self) -> Dict:
        """Generate coverage report"""
        report = {
            "covergroups": {},
            "total_coverage": 0.0,
            "total_coverpoints": 0,
            "total_crosses": 0,
        }

        total_cov = 0.0
        for name, cg in self.covergroups.items():
            cg_cov = cg.coverage_percent
            report["covergroups"][name] = {
                "coverage_percent": cg_cov,
                "goal": cg.goal,
                "goal_met": cg_cov >= cg.goal,
                "coverpoints": {
                    cp_name: cp.coverage_percent
                    for cp_name, cp in cg.coverpoints.items()
                },
                "crosses": {
                    cross_name: cross.coverage_percent
                    for cross_name, cross in cg.cross_coverage.items()
                },
            }
            total_cov += cg_cov
            report["total_coverpoints"] += len(cg.coverpoints)
            report["total_crosses"] += len(cg.cross_coverage)

        report["total_coverage"] = total_cov / len(self.covergroups) if self.covergroups else 0.0
        return report


def demo():
    """Self-check demo"""
    model = HBM4CoverageModel()

    # Sample some coverage
    for i in range(100):
        model.sample_bank_conflict(
            bank_id=random.randint(0, 15),
            conflict_type=random.randint(0, 3),
            bank_group=random.randint(0, 3)
        )
        model.sample_row_hit_miss(
            access_type=random.randint(0, 3),
            channel=random.randint(0, 31),
            row_addr=random.randint(0, 65535)
        )
        model.sample_command(
            cmd_type=random.randint(0, 5),
            channel=random.randint(0, 31)
        )
        model.sample_qos(
            priority=random.randint(0, 15),
            channel=random.randint(0, 31),
            transition=random.randint(0, 21),
            starvation=random.randint(0, 1000)
        )

    report = model.get_coverage_report()
    print(f"Total Coverage: {report['total_coverage']:.1f}%")
    print(f"Coverpoints: {report['total_coverpoints']}")
    print(f"Crosses: {report['total_crosses']}")
    print("Coverage model created successfully")
    assert report['total_coverage'] > 0, "Coverage should be sampled"
    print("Self-check passed")


if __name__ == "__main__":
    demo()
