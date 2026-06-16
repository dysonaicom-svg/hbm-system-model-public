"""
Tests for HBM4 Lane Repair Model
"""

import pytest
from model.dram.lane_repair import (
    HBM4LaneRepairModel,
    LaneRepairMap,
    LaneRepairEntry,
    RepairStatus,
)


class TestLaneRepairModelCreation:
    """Test Lane Repair Model initialization"""

    def test_default_creation(self):
        """Test default lane repair model creation"""
        model = HBM4LaneRepairModel()
        assert model.num_channels == 32
        assert model.lanes_per_channel == 64
        assert model.spare_lanes_per_channel == 4

    def test_custom_channels(self):
        """Test custom channel count"""
        model = HBM4LaneRepairModel(num_channels=16)
        assert model.num_channels == 16

    def test_custom_lanes(self):
        """Test custom lane count"""
        model = HBM4LaneRepairModel(lanes_per_channel=32, spare_lanes_per_channel=2)
        assert model.lanes_per_channel == 32
        assert model.spare_lanes_per_channel == 2

    def test_channel_maps_initialized(self):
        """Test all channel repair maps are initialized"""
        model = HBM4LaneRepairModel(num_channels=8)
        for ch in range(8):
            rm = model.get_channel_repair_map(ch)
            assert rm is not None
            assert rm.channel_id == ch


class TestLaneRepairOperations:
    """Test lane repair operations"""

    def test_add_failed_lane(self):
        """Test adding a failed lane"""
        model = HBM4LaneRepairModel(num_channels=4)
        result = model.add_failed_lane(channel_id=0, lane_id=10)
        assert result is True

        rm = model.get_channel_repair_map(0)
        assert 10 in rm.failed_lanes

    def test_add_duplicate_lane(self):
        """Test adding duplicate failed lane"""
        model = HBM4LaneRepairModel(num_channels=4)
        model.add_failed_lane(channel_id=0, lane_id=10)
        result = model.add_failed_lane(channel_id=0, lane_id=10)
        assert result is True  # Already tracked

        rm = model.get_channel_repair_map(0)
        assert len(rm.failed_lanes) == 1

    def test_add_invalid_channel(self):
        """Test adding lane to invalid channel"""
        model = HBM4LaneRepairModel(num_channels=4)
        result = model.add_failed_lane(channel_id=10, lane_id=10)
        assert result is False

    def test_perform_repair(self):
        """Test performing lane repair"""
        model = HBM4LaneRepairModel(num_channels=4)
        spare = model.perform_repair(channel_id=0, failed_lane=10)
        assert spare is not None
        assert spare >= 64  # Spare lane index

        rm = model.get_channel_repair_map(0)
        assert rm.repair_count == 1
        assert 10 in rm.failed_lanes

    def test_perform_multiple_repairs(self):
        """Test multiple repairs on same channel"""
        model = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=4)

        repairs = []
        for lane in [10, 20, 30, 40]:
            spare = model.perform_repair(channel_id=0, failed_lane=lane)
            repairs.append(spare)

        assert all(s is not None for s in repairs)
        assert len(set(repairs)) == 4  # All different spares

    def test_exhaust_spares(self):
        """Test exhausting all spare lanes"""
        model = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=2)

        # Use both spares
        model.perform_repair(channel_id=0, failed_lane=10)
        model.perform_repair(channel_id=0, failed_lane=20)

        # Third repair should fail
        spare = model.perform_repair(channel_id=0, failed_lane=30)
        assert spare is None

    def test_is_lane_remapped(self):
        """Test lane remapping check"""
        model = HBM4LaneRepairModel(num_channels=4)
        model.perform_repair(channel_id=0, failed_lane=10)

        assert model.is_lane_remapped(channel_id=0, lane_id=10) is True
        assert model.is_lane_remapped(channel_id=0, lane_id=20) is False

    def test_get_remapped_lane(self):
        """Test getting remapped lane"""
        model = HBM4LaneRepairModel(num_channels=4)
        spare = model.perform_repair(channel_id=0, failed_lane=10)

        remapped = model.get_remapped_lane(channel_id=0, lane_id=10)
        assert remapped == spare

        # Non-repaired lane returns itself
        remapped = model.get_remapped_lane(channel_id=0, lane_id=20)
        assert remapped == 20


class TestRepairStatus:
    """Test repair status reporting"""

    def test_no_repair_status(self):
        """Test status when no repairs"""
        model = HBM4LaneRepairModel(num_channels=4)
        status = model.get_repair_status(0)
        assert status == RepairStatus.NO_REPAIR

    def test_partial_repair_status(self):
        """Test status with partial repairs"""
        model = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=4)
        model.add_failed_lane(channel_id=0, lane_id=10)

        status = model.get_repair_status(0)
        assert status == RepairStatus.PARTIAL_REPAIR

    def test_full_repair_status(self):
        """Test status when all spares used"""
        model = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=2)

        for lane in [10, 20]:
            model.perform_repair(channel_id=0, failed_lane=lane)

        status = model.get_repair_status(0)
        assert status == RepairStatus.FULL_REPAIR


class TestLaneRepairStatistics:
    """Test statistics gathering"""

    def test_get_stats(self):
        """Test overall statistics"""
        model = HBM4LaneRepairModel(num_channels=8, spare_lanes_per_channel=2)

        # Add some repairs
        model.perform_repair(channel_id=0, failed_lane=10)
        model.perform_repair(channel_id=1, failed_lane=20)

        stats = model.get_stats()
        assert stats['total_channels'] == 8
        assert stats['spares_per_channel'] == 2
        assert stats['total_repairs'] == 2
        assert stats['channels_with_repairs'] == 2

    def test_get_channel_stats(self):
        """Test per-channel statistics"""
        model = HBM4LaneRepairModel(num_channels=4)
        model.perform_repair(channel_id=0, failed_lane=10)
        model.perform_repair(channel_id=0, failed_lane=20)

        stats = model.get_channel_stats(0)
        assert stats is not None
        assert stats['channel_id'] == 0
        assert stats['repair_count'] == 2
        assert stats['failed_lanes'] == 2
        assert stats['is_repairable'] is True

    def test_channel_stats_invalid(self):
        """Test stats for invalid channel"""
        model = HBM4LaneRepairModel(num_channels=4)
        stats = model.get_channel_stats(10)
        assert stats is None


class TestLaneRepairSimulation:
    """Test simulation features"""

    def test_simulate_yield_loss(self):
        """Test yield loss simulation"""
        model = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=2)

        # Set seed for reproducibility
        import random
        random.seed(42)

        failed = model.simulate_yield_loss(channel_id=0, failure_rate=0.1)
        assert failed >= 0

    def test_reset_channel(self):
        """Test channel reset"""
        model = HBM4LaneRepairModel(num_channels=4)
        model.perform_repair(channel_id=0, failed_lane=10)

        model.reset_channel(0)

        rm = model.get_channel_repair_map(0)
        assert len(rm.failed_lanes) == 0
        assert rm.repair_count == 0

    def test_reset_all(self):
        """Test reset all channels"""
        model = HBM4LaneRepairModel(num_channels=4)
        model.perform_repair(channel_id=0, failed_lane=10)
        model.perform_repair(channel_id=1, failed_lane=20)

        model.reset_all()

        stats = model.get_stats()
        assert stats['total_repairs'] == 0
        assert stats['total_failed_lanes'] == 0


class TestLaneRepairEdgeCases:
    """Test edge cases"""

    def test_invalid_channel_operations(self):
        """Test operations on invalid channel"""
        model = HBM4LaneRepairModel(num_channels=4)

        assert model.add_failed_lane(channel_id=100, lane_id=10) is False
        assert model.perform_repair(channel_id=100, failed_lane=10) is None
        assert model.get_repair_status(channel_id=100) == RepairStatus.NO_REPAIR
        assert model.get_all_failed_lanes(channel_id=100) == []

    def test_allocate_spare_invalid(self):
        """Test allocating invalid spare"""
        model = HBM4LaneRepairModel(num_channels=4)

        # Allocate same spare twice
        result1 = model.allocate_spare(channel_id=0, failed_lane=10, spare_lane=64)
        result2 = model.allocate_spare(channel_id=0, failed_lane=20, spare_lane=64)

        assert result1 is True
        assert result2 is False

    def test_lane_repair_map_properties(self):
        """Test LaneRepairMap properties"""
        rm = LaneRepairMap(
            channel_id=0,
            total_lanes=64,
            total_spares=4,
        )

        assert rm.available_spares == 4
        assert rm.is_repairable is True
        assert rm.status == RepairStatus.NO_REPAIR

        # Add failed lanes (3 < 4 spares = partial repair)
        for lane in [10, 20, 30]:
            rm.failed_lanes.append(lane)

        assert rm.available_spares == 4
        assert rm.status == RepairStatus.PARTIAL_REPAIR

        # Add 4th failure = exactly matches spares = full repair
        rm.failed_lanes.append(40)
        assert rm.status == RepairStatus.FULL_REPAIR

        # Perform repairs to consume spares
        for i, lane in enumerate([10, 20, 30, 40]):
            rm.repair_entries.append(LaneRepairEntry(
                failed_lane=lane,
                spare_lane=64 + i,
                repair_type="bit",
                channel_id=0,
            ))
            rm.spare_lanes.append(64 + i)
            rm.repair_count += 1

        assert rm.available_spares == 0

        # Add one more failure beyond spares
        rm.failed_lanes.append(50)
        assert rm.status == RepairStatus.UNREPAIRABLE
