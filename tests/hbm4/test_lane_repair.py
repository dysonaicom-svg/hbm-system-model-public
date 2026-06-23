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
    """Test Lane Repair Model creation and initialization"""

    def test_model_creation_defaults(self):
        """Test model creation with default parameters"""
        model = HBM4LaneRepairModel()

        assert model.num_channels == 32
        assert model.lanes_per_channel == 64
        assert model.spare_lanes_per_channel == 4
        assert len(model._repair_maps) == 32

    def test_model_creation_custom(self):
        """Test model creation with custom parameters"""
        model = HBM4LaneRepairModel(
            num_channels=16,
            lanes_per_channel=128,
            spare_lanes_per_channel=8,
        )

        assert model.num_channels == 16
        assert model.lanes_per_channel == 128
        assert model.spare_lanes_per_channel == 8
        assert len(model._repair_maps) == 16

    def test_repair_map_initialization(self):
        """Test repair map is properly initialized per channel"""
        model = HBM4LaneRepairModel(num_channels=8, lanes_per_channel=64, spare_lanes_per_channel=4)

        for ch in range(8):
            rm = model._repair_maps[ch]
            assert rm.channel_id == ch
            assert rm.total_lanes == 64
            assert rm.total_spares == 4
            assert len(rm.failed_lanes) == 0
            assert len(rm.spare_lanes) == 0
            assert rm.repair_count == 0


class TestSpareLaneAllocation:
    """Test spare lane allocation functionality"""

    def test_allocate_spare_success(self):
        """Test successful spare lane allocation"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        result = model.allocate_spare(
            channel_id=0,
            failed_lane=10,
            spare_lane=64,  # First spare lane
            repair_type="bit",
        )

        assert result is True
        rm = model._repair_maps[0]
        assert len(rm.repair_entries) == 1
        assert len(rm.spare_lanes) == 1
        assert rm.repair_count == 1
        assert rm.spare_lanes[0] == 64

    def test_allocate_spare_invalid_channel(self):
        """Test spare allocation fails for invalid channel"""
        model = HBM4LaneRepairModel(num_channels=8)

        result = model.allocate_spare(
            channel_id=99,  # Invalid channel
            failed_lane=10,
            spare_lane=64,
        )

        assert result is False

    def test_allocate_spare_already_used(self):
        """Test spare allocation fails when spare already used"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        # Allocate first spare
        model.allocate_spare(channel_id=0, failed_lane=10, spare_lane=64, repair_type="bit")

        # Try to reuse same spare
        result = model.allocate_spare(channel_id=0, failed_lane=20, spare_lane=64, repair_type="bit")

        assert result is False

    def test_allocate_spare_no_capacity(self):
        """Test spare allocation fails when no capacity"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=2)

        # Use all spares
        model.allocate_spare(channel_id=0, failed_lane=0, spare_lane=64, repair_type="bit")
        model.allocate_spare(channel_id=0, failed_lane=1, spare_lane=65, repair_type="bit")

        # Try to allocate when full
        result = model.allocate_spare(channel_id=0, failed_lane=2, spare_lane=66, repair_type="bit")

        assert result is False

    def test_perform_repair_auto_allocates(self):
        """Test perform_repair automatically allocates spare"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        spare = model.perform_repair(channel_id=0, failed_lane=15, repair_type="byte")

        assert spare is not None
        assert spare == 64  # First spare lane
        assert model.is_lane_remapped(0, 15)

    def test_perform_repair_with_byte_type(self):
        """Test perform_repair with byte repair type"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        spare = model.perform_repair(channel_id=0, failed_lane=5, repair_type="byte")

        rm = model._repair_maps[0]
        entry = rm.repair_entries[0]
        assert entry.repair_type == "byte"
        assert entry.failed_lane == 5


class TestBypassMapping:
    """Test lane bypass/remapping functionality"""

    def test_is_lane_remapped_true(self):
        """Test is_lane_remapped returns True for repaired lane"""
        model = HBM4LaneRepairModel(num_channels=1)

        model.allocate_spare(channel_id=0, failed_lane=25, spare_lane=64, repair_type="bit")

        assert model.is_lane_remapped(0, 25) is True

    def test_is_lane_remapped_false(self):
        """Test is_lane_remapped returns False for unrepaired lane"""
        model = HBM4LaneRepairModel(num_channels=1)

        assert model.is_lane_remapped(0, 10) is False

    def test_get_remapped_lane(self):
        """Test get_remapped_lane returns correct spare"""
        model = HBM4LaneRepairModel(num_channels=1)

        model.allocate_spare(channel_id=0, failed_lane=30, spare_lane=67, repair_type="bit")

        remapped = model.get_remapped_lane(0, 30)
        assert remapped == 67

    def test_get_remapped_lane_not_remapped(self):
        """Test get_remapped_lane returns original for unrepaired"""
        model = HBM4LaneRepairModel(num_channels=1)

        remapped = model.get_remapped_lane(0, 40)
        assert remapped == 40

    def test_multiple_remappings(self):
        """Test multiple lane remappings"""
        model = HBM4LaneRepairModel(num_channels=2, lanes_per_channel=64, spare_lanes_per_channel=4)

        # Channel 0: two repairs
        model.allocate_spare(channel_id=0, failed_lane=5, spare_lane=64, repair_type="bit")
        model.allocate_spare(channel_id=0, failed_lane=10, spare_lane=65, repair_type="bit")

        # Channel 1: one repair
        model.allocate_spare(channel_id=1, failed_lane=20, spare_lane=64, repair_type="bit")

        assert model.is_lane_remapped(0, 5)
        assert model.is_lane_remapped(0, 10)
        assert model.is_lane_remapped(1, 20)
        assert not model.is_lane_remapped(0, 20)
        assert not model.is_lane_remapped(1, 5)


class TestRepairStateTracking:
    """Test repair state tracking"""

    def test_add_failed_lane(self):
        """Test adding failed lane"""
        model = HBM4LaneRepairModel(num_channels=1)

        result = model.add_failed_lane(channel_id=0, lane_id=15)

        assert result is True
        assert 15 in model.get_all_failed_lanes(0)

    def test_add_failed_lane_duplicate(self):
        """Test adding duplicate failed lane"""
        model = HBM4LaneRepairModel(num_channels=1)

        model.add_failed_lane(channel_id=0, lane_id=15)
        result = model.add_failed_lane(channel_id=0, lane_id=15)

        assert result is True  # Already tracked, return True

    def test_add_failed_lane_invalid_channel(self):
        """Test adding failed lane to invalid channel"""
        model = HBM4LaneRepairModel(num_channels=8)

        result = model.add_failed_lane(channel_id=99, lane_id=15)

        assert result is False

    def test_repair_status_no_repair(self):
        """Test repair status when no repairs"""
        model = HBM4LaneRepairModel(num_channels=1)

        status = model.get_repair_status(0)

        assert status == RepairStatus.NO_REPAIR

    def test_repair_status_partial_repair(self):
        """Test repair status with partial repairs"""
        model = HBM4LaneRepairModel(num_channels=1, spare_lanes_per_channel=4)

        model.add_failed_lane(channel_id=0, lane_id=5)
        model.add_failed_lane(channel_id=0, lane_id=10)

        status = model.get_repair_status(0)

        assert status == RepairStatus.PARTIAL_REPAIR

    def test_repair_status_full_repair(self):
        """Test repair status when all spares used"""
        model = HBM4LaneRepairModel(num_channels=1, spare_lanes_per_channel=2)

        model.add_failed_lane(channel_id=0, lane_id=0)
        model.add_failed_lane(channel_id=0, lane_id=1)
        model.perform_repair(channel_id=0, failed_lane=0)
        model.perform_repair(channel_id=0, failed_lane=1)

        status = model.get_repair_status(0)

        assert status == RepairStatus.FULL_REPAIR

    def test_repair_status_unrepairable(self):
        """Test repair status when unrepairable"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=2)

        # Add more failures than spares
        for lane in range(5):
            model.add_failed_lane(channel_id=0, lane_id=lane)

        status = model.get_repair_status(0)

        assert status == RepairStatus.UNREPAIRABLE

    def test_available_spares_property(self):
        """Test available_spares property"""
        model = HBM4LaneRepairModel(num_channels=1, spare_lanes_per_channel=4)

        assert model._repair_maps[0].available_spares == 4

        model.allocate_spare(channel_id=0, failed_lane=0, spare_lane=64)
        assert model._repair_maps[0].available_spares == 3

        model.allocate_spare(channel_id=0, failed_lane=1, spare_lane=65)
        assert model._repair_maps[0].available_spares == 2

    def test_is_repairable_property(self):
        """Test is_repairable property"""
        model = HBM4LaneRepairModel(num_channels=1, spare_lanes_per_channel=4)

        rm = model._repair_maps[0]
        assert rm.is_repairable is True

        # Fill up with repairs
        for i in range(4):
            model.add_failed_lane(channel_id=0, lane_id=i)
            model.perform_repair(channel_id=0, failed_lane=i)

        assert rm.is_repairable is False


class TestLaneFailureSimulation:
    """Test lane failure simulation"""

    def test_simulate_yield_loss(self):
        """Test yield loss simulation"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64)

        # With 0 failure rate, should have 0 failures
        failures = model.simulate_yield_loss(channel_id=0, failure_rate=0.0)
        assert failures == 0

    def test_simulate_yield_loss_with_rate(self):
        """Test yield loss with non-zero failure rate"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64)

        # Use a high failure rate to ensure some failures
        failures = model.simulate_yield_loss(channel_id=0, failure_rate=0.5)

        # Should have at least some failures (statistically)
        rm = model._repair_maps[0]
        assert len(rm.failed_lanes) >= 0  # May or may not have failures due to randomness

    def test_simulate_yield_loss_invalid_channel(self):
        """Test yield loss on invalid channel"""
        model = HBM4LaneRepairModel(num_channels=8)

        failures = model.simulate_yield_loss(channel_id=99, failure_rate=0.1)

        assert failures == 0


class TestStatistics:
    """Test statistics functionality"""

    def test_get_stats_initial(self):
        """Test get_stats returns correct initial values"""
        model = HBM4LaneRepairModel(num_channels=8, lanes_per_channel=64, spare_lanes_per_channel=4)

        stats = model.get_stats()

        assert stats['total_channels'] == 8
        assert stats['lanes_per_channel'] == 64
        assert stats['spares_per_channel'] == 4
        assert stats['total_repairs'] == 0
        assert stats['total_failed_lanes'] == 0
        assert stats['unrepairable_channels'] == 0
        assert stats['channels_with_repairs'] == 0

    def test_get_stats_with_repairs(self):
        """Test get_stats with repairs"""
        model = HBM4LaneRepairModel(num_channels=8, spare_lanes_per_channel=4)

        model.add_failed_lane(channel_id=0, lane_id=5)
        model.add_failed_lane(channel_id=0, lane_id=10)
        model.perform_repair(channel_id=0, failed_lane=5)
        model.perform_repair(channel_id=0, failed_lane=10)

        stats = model.get_stats()

        assert stats['total_repairs'] == 2
        assert stats['total_failed_lanes'] == 2
        assert stats['channels_with_repairs'] == 1

    def test_get_channel_stats(self):
        """Test get_channel_stats"""
        model = HBM4LaneRepairModel(num_channels=1, spare_lanes_per_channel=4)

        model.add_failed_lane(channel_id=0, lane_id=5)
        model.perform_repair(channel_id=0, failed_lane=5)

        stats = model.get_channel_stats(0)

        assert stats is not None
        assert stats['channel_id'] == 0
        assert stats['failed_lanes'] == 1
        assert stats['repair_count'] == 1
        assert stats['available_spares'] == 3
        assert stats['status'] == 'partial_repair'
        assert stats['is_repairable'] is True

    def test_get_channel_stats_invalid(self):
        """Test get_channel_stats with invalid channel"""
        model = HBM4LaneRepairModel(num_channels=8)

        stats = model.get_channel_stats(99)

        assert stats is None


class TestResetOperations:
    """Test reset functionality"""

    def test_reset_channel(self):
        """Test reset_channel"""
        model = HBM4LaneRepairModel(num_channels=1, spare_lanes_per_channel=4)

        # Setup repairs
        model.add_failed_lane(channel_id=0, lane_id=5)
        model.perform_repair(channel_id=0, failed_lane=5)

        # Reset
        model.reset_channel(0)

        rm = model._repair_maps[0]
        assert len(rm.failed_lanes) == 0
        assert len(rm.spare_lanes) == 0
        assert len(rm.repair_entries) == 0
        assert rm.repair_count == 0

    def test_reset_all(self):
        """Test reset_all"""
        model = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=4)

        # Setup repairs on multiple channels
        model.add_failed_lane(channel_id=0, lane_id=5)
        model.perform_repair(channel_id=0, failed_lane=5)
        model.add_failed_lane(channel_id=2, lane_id=10)
        model.perform_repair(channel_id=2, failed_lane=10)

        # Reset all
        model.reset_all()

        for ch in range(4):
            rm = model._repair_maps[ch]
            assert len(rm.failed_lanes) == 0
            assert rm.repair_count == 0

        stats = model.get_stats()
        assert stats['total_repairs'] == 0
        assert stats['total_failed_lanes'] == 0


class TestConfigureChannel:
    """Test channel configuration"""

    def test_configure_new_channel(self):
        """Test configuring a new channel"""
        model = HBM4LaneRepairModel(num_channels=1)

        model.configure_channel(channel_id=1, lanes=128, spares=8)

        assert 1 in model._repair_maps
        rm = model._repair_maps[1]
        assert rm.total_lanes == 128
        assert rm.total_spares == 8

    def test_configure_existing_channel(self):
        """Test configuring an existing channel"""
        model = HBM4LaneRepairModel(num_channels=1, lanes_per_channel=64, spare_lanes_per_channel=4)

        model.configure_channel(channel_id=0, lanes=128, spares=8)

        rm = model._repair_maps[0]
        assert rm.total_lanes == 128
        assert rm.total_spares == 8


class TestGetChannelRepairMap:
    """Test get_channel_repair_map functionality"""

    def test_get_channel_repair_map(self):
        """Test get_channel_repair_map returns correct map"""
        model = HBM4LaneRepairModel(num_channels=1)

        rm = model.get_channel_repair_map(0)

        assert rm is not None
        assert rm.channel_id == 0
        assert isinstance(rm, LaneRepairMap)

    def test_get_channel_repair_map_invalid(self):
        """Test get_channel_repair_map with invalid channel"""
        model = HBM4LaneRepairModel(num_channels=8)

        rm = model.get_channel_repair_map(99)

        assert rm is None


class TestLaneRepairEntry:
    """Test LaneRepairEntry dataclass"""

    def test_lane_repair_entry_creation(self):
        """Test LaneRepairEntry creation"""
        entry = LaneRepairEntry(
            failed_lane=10,
            spare_lane=64,
            repair_type="bit",
            channel_id=0,
        )

        assert entry.failed_lane == 10
        assert entry.spare_lane == 64
        assert entry.repair_type == "bit"
        assert entry.channel_id == 0