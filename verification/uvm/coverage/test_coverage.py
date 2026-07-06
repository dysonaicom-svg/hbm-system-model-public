#!/usr/bin/env python3
"""
Coverage Tests
Tests for HBM4 functional coverage model
"""
import unittest
import random
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from hbm_coverage_model import (
    HBM4CoverageModel, Coverpoint, Covergroup, CrossCoverage,
    BinRange, AccessType, ConflictType
)
from coverage_collector import CoverageCollector, CoverageDatabase


class TestBinRange(unittest.TestCase):
    """Test BinRange class"""

    def test_contains_within_range(self):
        bin_def = BinRange("test", 10, 20)
        self.assertTrue(bin_def.contains(15))
        self.assertTrue(bin_def.contains(10))
        self.assertTrue(bin_def.contains(20))

    def test_contains_outside_range(self):
        bin_def = BinRange("test", 10, 20)
        self.assertFalse(bin_def.contains(9))
        self.assertFalse(bin_def.contains(21))

    def test_single_value_bin(self):
        bin_def = BinRange("single", 5, 5)
        self.assertTrue(bin_def.contains(5))
        self.assertFalse(bin_def.contains(4))
        self.assertFalse(bin_def.contains(6))


class TestCoverpoint(unittest.TestCase):
    """Test Coverpoint class"""

    def setUp(self):
        self.cp = Coverpoint("test_cp", [
            BinRange("low", 0, 10),
            BinRange("mid", 11, 20),
            BinRange("high", 21, 30),
        ])

    def test_initial_coverage(self):
        self.assertEqual(self.cp.coverage_percent, 0.0)
        self.assertEqual(len(self.cp.hit_bins), 0)

    def test_sample_hits_bin(self):
        self.cp.sample(5)
        self.assertIn("low", self.cp.hit_bins)
        self.assertAlmostEqual(self.cp.coverage_percent, 33.33, places=1)

    def test_sample_multiple_bins(self):
        self.cp.sample(5)
        self.cp.sample(15)
        self.cp.sample(25)
        self.assertEqual(len(self.cp.hit_bins), 3)
        self.assertEqual(self.cp.coverage_percent, 100.0)

    def test_sample_count(self):
        for _ in range(10):
            self.cp.sample(random.randint(0, 30))
        self.assertEqual(self.cp.sample_count, 10)

    def test_uncovered_bins(self):
        self.cp.sample(5)
        uncovered = self.cp.get_uncovered_bins()
        self.assertIn("mid", uncovered)
        self.assertIn("high", uncovered)
        self.assertNotIn("low", uncovered)


class TestCovergroup(unittest.TestCase):
    """Test Covergroup class"""

    def setUp(self):
        self.cg = Covergroup("test_cg", goal=90.0)
        self.cg.add_coverpoint("cp1", [
            BinRange("bin1", 0, 10),
            BinRange("bin2", 11, 20),
        ])
        self.cg.add_coverpoint("cp2", [
            BinRange("bin3", 0, 5),
            BinRange("bin4", 6, 10),
        ])

    def test_initial_coverage(self):
        self.assertEqual(self.cg.coverage_percent, 0.0)

    def test_sample_coverpoints(self):
        self.cg.sample({"cp1": 5, "cp2": 3})
        self.assertIn("bin1", self.cg.coverpoints["cp1"].hit_bins)
        self.assertIn("bin3", self.cg.coverpoints["cp2"].hit_bins)

    def test_cross_coverage(self):
        self.cg.add_cross("cross1", "cp1", "cp2")
        self.cg.sample({"cp1": 5, "cp2": 3})
        # Verify cross coverage has at least one coverpoint with hits
        cp1_hits = self.cg.coverpoints["cp1"].hit_bins
        cp2_hits = self.cg.coverpoints["cp2"].hit_bins
        self.assertGreater(len(cp1_hits), 0)
        self.assertGreater(len(cp2_hits), 0)

    def test_goal_setting(self):
        self.assertEqual(self.cg.goal, 90.0)


class TestCrossCoverage(unittest.TestCase):
    """Test CrossCoverage class"""

    def setUp(self):
        cp1 = Coverpoint("cp1", [
            BinRange("a", 0, 5),
            BinRange("b", 6, 10),
        ])
        cp2 = Coverpoint("cp2", [
            BinRange("x", 0, 5),
            BinRange("y", 6, 10),
        ])
        self.cross = CrossCoverage("test_cross", cp1, cp2)

    def test_sample_records_pair(self):
        self.cross.sample(3, 7)
        self.assertEqual(len(self.cross.hit_pairs), 1)
        self.assertIn(("a", "y"), self.cross.hit_pairs)

    def test_coverage_percent(self):
        self.cross.sample(3, 7)
        self.cross.sample(8, 2)
        self.assertEqual(self.cross.coverage_percent, 50.0)

    def test_all_pairs_hit(self):
        for v1 in [3, 8]:
            for v2 in [3, 8]:
                self.cross.sample(v1, v2)
        self.assertEqual(self.cross.coverage_percent, 100.0)


class TestHBM4CoverageModel(unittest.TestCase):
    """Test HBM4 coverage model"""

    def setUp(self):
        self.model = HBM4CoverageModel()

    def test_all_covergroups_created(self):
        expected_groups = [
            "bank_conflict_cg", "row_hammer_cg", "refresh_cg",
            "channel_interleave_cg", "row_hit_miss_cg", "queue_fullness_cg",
            "command_type_cg", "latency_cg", "bandwidth_cg",
            "qos_priority_cg", "transaction_cg"
        ]
        for group in expected_groups:
            self.assertIn(group, self.model.covergroups)

    def test_bank_conflict_sampling(self):
        self.model.sample_bank_conflict(bank_id=5, conflict_type=1, bank_group=1)
        cg = self.model.covergroups["bank_conflict_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_row_hit_miss_sampling(self):
        self.model.sample_row_hit_miss(access_type=0, channel=10, row_addr=100)
        cg = self.model.covergroups["row_hit_miss_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_command_sampling(self):
        self.model.sample_command(cmd_type=2, channel=5)
        cg = self.model.covergroups["command_type_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_qos_sampling(self):
        self.model.sample_qos(priority=10, channel=20, transition=5, starvation=100)
        cg = self.model.covergroups["qos_priority_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_refresh_sampling(self):
        self.model.sample_refresh(refresh_type=0, bank_id=8, interval=100)
        cg = self.model.covergroups["refresh_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_latency_sampling(self):
        self.model.sample_latency(read_lat=30, write_lat=20, cmd_type=2)
        cg = self.model.covergroups["latency_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_bandwidth_sampling(self):
        self.model.sample_bandwidth(bw_util=50, rw_ratio=40, width_util=75)
        cg = self.model.covergroups["bandwidth_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_transaction_sampling(self):
        self.model.sample_transaction(trans_type=0, addr_pattern=1, data_pattern=5)
        cg = self.model.covergroups["transaction_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_channel_interleave_sampling(self):
        self.model.sample_channel_interleave(channel_id=15, depth=4,
                                             pattern=1, switches=10)
        cg = self.model.covergroups["channel_interleave_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_row_hammer_sampling(self):
        self.model.sample_row_hammer(bank_id=7, count=100, intensity=2)
        cg = self.model.covergroups["row_hammer_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_queue_fullness_sampling(self):
        self.model.sample_queue_fullness(read_depth=15, write_depth=20)
        cg = self.model.covergroups["queue_fullness_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_get_coverage_report(self):
        report = self.model.get_coverage_report()
        self.assertIn("covergroups", report)
        self.assertIn("total_coverage", report)
        self.assertGreater(report["total_coverpoints"], 0)

    def test_comprehensive_sampling(self):
        """Test comprehensive coverage with many samples"""
        for _ in range(500):
            self.model.sample_bank_conflict(
                bank_id=random.randint(0, 15),
                conflict_type=random.randint(0, 3),
                bank_group=random.randint(0, 3)
            )
            self.model.sample_row_hit_miss(
                access_type=random.randint(0, 3),
                channel=random.randint(0, 31),
                row_addr=random.randint(0, 65535)
            )
            self.model.sample_command(
                cmd_type=random.randint(0, 5),
                channel=random.randint(0, 31)
            )
            self.model.sample_qos(
                priority=random.randint(0, 15),
                channel=random.randint(0, 31),
                transition=random.randint(0, 21),
                starvation=random.randint(0, 1000)
            )

        report = self.model.get_coverage_report()
        # Should achieve reasonable coverage with many samples
        self.assertGreater(report["total_coverage"], 10)


class TestCoverageDatabase(unittest.TestCase):
    """Test CoverageDatabase class"""

    def setUp(self):
        self.db = CoverageDatabase()

    def test_record_sample(self):
        self.db.record_sample("test_cg", "test_cp", 5, "bin1")
        self.assertEqual(len(self.db.samples), 1)

    def test_bin_counts(self):
        self.db.record_sample("test_cg", "test_cp", 5, "bin1")
        self.db.record_sample("test_cg", "test_cp", 8, "bin1")
        key = "test_cg.test_cp"
        self.assertEqual(self.db.bin_counts[key]["bin1"], 2)

    def test_set_total_bins(self):
        self.db.set_total_bins("test_cg", "test_cp", 10)
        key = "test_cg.test_cp"
        self.assertEqual(self.db.total_bins[key], 10)

    def test_get_stats(self):
        self.db.set_total_bins("test_cg", "test_cp", 5)
        self.db.record_sample("test_cg", "test_cp", 1, "bin1")
        self.db.record_sample("test_cg", "test_cp", 2, "bin2")
        stats = self.db.get_stats("test_cg", "test_cp")
        self.assertEqual(stats.unique_bins_hit, 2)
        self.assertEqual(stats.total_bins, 5)
        self.assertEqual(stats.coverage_percent, 40.0)


class TestCoverageCollector(unittest.TestCase):
    """Test CoverageCollector class"""

    def setUp(self):
        self.collector = CoverageCollector()

    def test_collect_bank_conflict(self):
        self.collector.collect_bank_conflict(bank_id=5, conflict_type=1, bank_group=1)
        summary = self.collector.get_summary()
        self.assertGreater(summary["total_samples"], 0)

    def test_collect_row_hit_miss(self):
        self.collector.collect_row_hit_miss(access_type=2, channel=10, row_addr=100)
        summary = self.collector.get_summary()
        self.assertGreater(summary["total_samples"], 0)

    def test_collect_command(self):
        self.collector.collect_command(cmd_type=2, channel=5)
        summary = self.collector.get_summary()
        self.assertGreater(summary["total_samples"], 0)

    def test_collect_qos(self):
        self.collector.collect_qos(priority=15, channel=20, starvation=50)
        summary = self.collector.get_summary()
        self.assertGreater(summary["total_samples"], 0)

    def test_collect_refresh(self):
        self.collector.collect_refresh(refresh_type=0, bank_id=8)
        summary = self.collector.get_summary()
        self.assertGreater(summary["total_samples"], 0)

    def test_collect_latency(self):
        self.collector.collect_latency(read_latency=35, write_latency=25)
        summary = self.collector.get_summary()
        self.assertGreater(summary["total_samples"], 0)

    def test_collect_bandwidth(self):
        self.collector.collect_bandwidth(bw_util=55, rw_ratio=45)
        summary = self.collector.get_summary()
        self.assertGreater(summary["total_samples"], 0)

    def test_save_report(self):
        self.collector.collect_bank_conflict(bank_id=5, conflict_type=1, bank_group=1)
        output = self.collector.save_report("test_coverage.json")
        self.assertTrue(output.exists())

    def test_comprehensive_collection(self):
        """Test comprehensive collection"""
        for _ in range(100):
            self.collector.collect_bank_conflict(
                bank_id=random.randint(0, 15),
                conflict_type=random.randint(0, 3),
                bank_group=random.randint(0, 3)
            )
            self.collector.collect_row_hit_miss(
                access_type=random.randint(0, 3),
                channel=random.randint(0, 31),
                row_addr=random.randint(0, 65535)
            )
            self.collector.collect_command(
                cmd_type=random.randint(0, 5),
                channel=random.randint(0, 31)
            )
            self.collector.collect_qos(
                priority=random.randint(0, 15),
                channel=random.randint(0, 31),
                starvation=random.randint(0, 1000)
            )

        summary = self.collector.get_summary()
        self.assertGreater(summary["total_samples"], 100)


class TestHBM4SpecificCoverage(unittest.TestCase):
    """Test HBM4-specific coverage scenarios"""

    def setUp(self):
        self.model = HBM4CoverageModel()
        self.collector = CoverageCollector()

    def test_32_channel_coverage(self):
        """Test all 32 channels are covered"""
        for ch in range(32):
            self.model.sample_channel_interleave(
                channel_id=ch, depth=1, pattern=0, switches=1
            )
        cg = self.model.covergroups["channel_interleave_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_pseudo_channel_coverage(self):
        """Test pseudo-channel coverage (0-15, 16-31)"""
        for ch in [0, 15, 16, 31]:
            self.model.sample_channel_interleave(
                channel_id=ch, depth=2, pattern=1, switches=5
            )
        cg = self.model.covergroups["channel_interleave_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_bank_group_coverage(self):
        """Test all 4 bank groups covered"""
        for bg in range(4):
            for bank in range(bg * 4, bg * 4 + 4):
                self.model.sample_bank_conflict(
                    bank_id=bank, conflict_type=0, bank_group=bg
                )
        cg = self.model.covergroups["bank_conflict_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_all_command_types(self):
        """Test all command types covered"""
        for cmd in range(6):  # IDLE to REFRESH
            self.model.sample_command(cmd_type=cmd, channel=0)
        cg = self.model.covergroups["command_type_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_all_access_types(self):
        """Test all access types covered"""
        for access in range(4):  # ROW_MISS to ROW_CLOSE
            self.model.sample_row_hit_miss(
                access_type=access, channel=0, row_addr=100
            )
        cg = self.model.covergroups["row_hit_miss_cg"]
        self.assertGreater(cg.coverage_percent, 0)

    def test_all_qos_priorities(self):
        """Test all QoS priority levels covered"""
        for priority in range(16):
            self.model.sample_qos(
                priority=priority, channel=0, transition=0, starvation=0
            )
        cg = self.model.covergroups["qos_priority_cg"]
        self.assertGreater(cg.coverage_percent, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
