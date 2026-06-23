"""
Tests for HBM4 TSV PHY Abstraction

Tests cover:
- TSV group creation and mapping
- Signal integrity (BER estimation)
- Latency modeling
- Training state machine
- Lane mapping
- Power estimation
- Integration with LaneRepair model
"""

import pytest
import random
from model.HBM4.phy.tsv_phy import (
    HBM4TSVPHY,
    TSVGroupType,
    TrainingState,
    BEREstimate,
    TSVGroup,
    LaneMapping,
    SignalIntegrityMetrics,
    LatencyComponent,
    TSVPowerBreakdown,
    TrainingResult,
    create_tsv_phy,
)
from model.dram.lane_repair import HBM4LaneRepairModel


class TestTSVPHYCreation:
    """Test TSV PHY initialization"""

    def test_default_creation(self):
        """Test default TSV PHY creation"""
        phy = HBM4TSVPHY()
        assert phy is not None
        assert phy.num_channels == 32
        assert phy.data_rate_gtps == 8.0

    def test_custom_channels(self):
        """Test custom channel count"""
        phy = HBM4TSVPHY(num_channels=16)
        assert phy.num_channels == 16
        assert len(phy._channel_groups) == 16

    def test_custom_parameters(self):
        """Test custom parameters"""
        phy = HBM4TSVPHY(
            num_channels=8,
            tsv_pitch_nm=40.0,
            data_rate_gtps=12.0,
            vdd_mv=1.0,
        )
        assert phy.num_channels == 8
        assert phy.tsv_pitch_nm == 40.0
        assert phy.data_rate_gtps == 12.0
        assert phy.vdd_mv == 1.0

    def test_tsv_groups_initialized(self):
        """Test TSV groups are initialized"""
        phy = HBM4TSVPHY(num_channels=4)
        assert len(phy._tsv_groups) > 0
        assert len(phy._channel_groups) == 4

    def test_factory_function(self):
        """Test factory function creation"""
        phy = create_tsv_phy(speed_grade="12Gbps")
        assert phy is not None
        assert phy.data_rate_gtps == 12.0


class TestTSVGroupMapping:
    """Test TSV group mapping to channels"""

    def test_get_channel_groups(self):
        """Test getting groups for a channel"""
        phy = HBM4TSVPHY(num_channels=4)
        groups = phy.get_channel_groups(channel_id=0)
        assert len(groups) == 4  # DATA, ADDR, CTRL, POWER
        assert all(isinstance(g, TSVGroup) for g in groups)

    def test_get_groups_by_type(self):
        """Test filtering groups by type"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        assert len(data_groups) == 4  # One per channel
        assert all(g.group_type == TSVGroupType.DATA for g in data_groups)

    def test_get_group_by_id(self):
        """Test getting specific group by ID"""
        phy = HBM4TSVPHY(num_channels=4)
        # Get first data group
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = phy.get_group_by_id(data_groups[0].group_id)
        assert group is not None
        assert group.group_id == data_groups[0].group_id

    def test_get_invalid_group(self):
        """Test getting invalid group returns None"""
        phy = HBM4TSVPHY()
        group = phy.get_group_by_id(9999)
        assert group is None

    def test_set_group_active(self):
        """Test activating/deactivating TSV groups"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        initial_active = phy.stats['active_tsvs']

        # Deactivate
        phy.set_group_active(group.group_id, False)
        assert not phy.get_group_by_id(group.group_id).is_active

        # Reactivate
        phy.set_group_active(group.group_id, True)
        assert phy.get_group_by_id(group.group_id).is_active


class TestSignalIntegrity:
    """Test signal integrity and BER estimation"""

    def test_estimate_ber(self):
        """Test BER estimation for a TSV group"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        metrics = phy.estimate_ber(group.group_id)
        assert isinstance(metrics, SignalIntegrityMetrics)
        assert metrics.group_id == group.group_id
        assert metrics.ber_estimate >= 0
        assert metrics.eye_width_ps > 0
        assert metrics.eye_height_mv > 0

    def test_ber_category_classification(self):
        """Test BER category classification"""
        phy = HBM4TSVPHY()
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        metrics = phy.estimate_ber(group.group_id)
        assert metrics.ber_category in list(BEREstimate)

    def test_get_signal_integrity(self):
        """Test getting stored signal integrity metrics"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        # First estimate
        metrics1 = phy.estimate_ber(group.group_id)
        # Then get
        metrics2 = phy.get_signal_integrity(group.group_id)

        assert metrics2 is not None
        assert metrics1.ber_estimate == metrics2.ber_estimate

    def test_update_from_measurement(self):
        """Test updating metrics from actual measurements"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        measured_ber = 1e-12
        eye_width = 50.0
        eye_height = 200.0

        phy.update_signal_integrity_from_measurement(
            group.group_id, measured_ber, eye_width, eye_height
        )

        metrics = phy.get_signal_integrity(group.group_id)
        assert metrics.ber_estimate == measured_ber
        assert metrics.eye_width_ps == eye_width
        assert metrics.eye_height_mv == eye_height

    def test_invalid_group_ber(self):
        """Test BER estimation with invalid group"""
        phy = HBM4TSVPHY()
        with pytest.raises(ValueError):
            phy.estimate_ber(9999)


class TestLatencyModeling:
    """Test latency modeling with variability"""

    def test_get_latency(self):
        """Test latency component retrieval"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        latency = phy.get_latency(group.group_id)
        assert isinstance(latency, LatencyComponent)
        assert latency.fixed_latency_ps >= 0
        assert latency.variability_ps >= 0
        assert latency.interconnect_delay_ps >= 0

    def test_latency_total(self):
        """Test total latency calculation"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        latency = phy.get_latency(group.group_id)
        assert latency.total_latency_ps == (
            latency.fixed_latency_ps + latency.variability_ps
        )

    def test_worst_case_latency(self):
        """Test worst-case latency calculation"""
        phy = HBM4TSVPHY(num_channels=4)
        worst = phy.get_worst_case_latency_ps(0)
        assert worst >= 0

    def test_best_case_latency(self):
        """Test best-case latency calculation"""
        phy = HBM4TSVPHY(num_channels=4)
        best = phy.get_best_case_latency_ps(0)
        assert best >= 0

    def test_latency_without_variability(self):
        """Test latency without variability"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        latency_with = phy.get_latency(group.group_id, include_variability=True)
        latency_without = phy.get_latency(group.group_id, include_variability=False)

        # Without variability should have zero variability
        assert latency_without.variability_ps == 0
        assert latency_without.total_latency_ps == latency_without.fixed_latency_ps


class TestTrainingStateMachine:
    """Test PHY training state machine"""

    def test_initial_state(self):
        """Test initial training state"""
        phy = HBM4TSVPHY()
        assert phy.get_training_state() == TrainingState.NOT_STARTED

    def test_start_training(self):
        """Test starting training"""
        phy = HBM4TSVPHY()
        phy.start_training()
        assert phy.get_training_state() == TrainingState.INIT

    def test_advance_training(self):
        """Test advancing through training states"""
        phy = HBM4TSVPHY()
        phy.start_training()
        # start_training() sets state to INIT, so first advance goes to WRITE_LEVELING

        expected_states = [
            TrainingState.WRITE_LEVELING,  # First advance from INIT
            TrainingState.READ_GATE_TRAINING,
            TrainingState.READ_DQ_TRAINING,
            TrainingState.WRITE_DQ_TRAINING,
            TrainingState.VREF_CALIBRATION,
            TrainingState.MARGIN_CHECK,
            TrainingState.COMPLETE,
        ]

        for expected in expected_states:
            state = phy.advance_training()
            assert state == expected

    def test_run_training_sequence(self):
        """Test complete training sequence"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group_ids = [g.group_id for g in data_groups[:2]]  # Train 2 groups

        results = phy.run_training_sequence(target_groups=group_ids, max_iterations=20)
        assert len(results) == 2
        assert all(r.group_id in group_ids for r in results)

    def test_training_results(self):
        """Test training results storage"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group_ids = [g.group_id for g in data_groups[:1]]

        phy.run_training_sequence(target_groups=group_ids)
        results = phy.get_training_results()
        assert len(results) > 0

    def test_set_training_failed(self):
        """Test setting training as failed"""
        phy = HBM4TSVPHY()
        phy.start_training()
        phy.set_training_failed("Test failure")
        assert phy.get_training_state() == TrainingState.FAILED


class TestLaneMapping:
    """Test lane mapping and remapping"""

    def test_init_lane_mappings(self):
        """Test lane mapping initialization"""
        phy = HBM4TSVPHY(num_channels=4)
        phy.init_lane_mappings(lanes_per_channel=64)

        assert len(phy._lane_mappings) == 4 * 64

    def test_get_lane_mapping(self):
        """Test getting lane mapping"""
        phy = HBM4TSVPHY(num_channels=4)
        phy.init_lane_mappings(lanes_per_channel=64)

        mapping = phy.get_lane_mapping(0)
        assert mapping is not None
        assert isinstance(mapping, LaneMapping)

    def test_remap_lane(self):
        """Test lane remapping"""
        phy = HBM4TSVPHY(num_channels=4)
        phy.init_lane_mappings(lanes_per_channel=64)

        initial_repaired = phy.stats['repaired_lanes']
        result = phy.remap_lane(0, 256)  # Map to spare TSV

        assert result is True
        mapping = phy.get_lane_mapping(0)
        assert mapping.is_remapped is True
        assert mapping.remapped_to == 256
        assert phy.stats['repaired_lanes'] == initial_repaired + 1

    def test_is_lane_active(self):
        """Test lane active status"""
        phy = HBM4TSVPHY(num_channels=4)
        phy.init_lane_mappings(lanes_per_channel=64)

        # Lane should be active initially
        assert phy.is_lane_active(0) is True

        # After remapping, lane is still "active" (remapped to working spare)
        phy.remap_lane(0, 256)
        assert phy.is_lane_active(0) is True

    def test_lane_remap_with_repair_model(self):
        """Test lane remapping with LaneRepair integration"""
        repair_model = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=2)
        repair_model.perform_repair(channel_id=0, failed_lane=0)

        phy = HBM4TSVPHY(num_channels=4, lane_repair_model=repair_model)
        phy.init_lane_mappings(lanes_per_channel=64)

        # Lane 0 in channel 0 is remapped
        assert phy.is_lane_active(0) is False  # Failed lane, not repaired properly
        assert phy.is_lane_active(1) is True   # Good lane


class TestPowerEstimation:
    """Test TSV PHY power estimation"""

    def test_estimate_power(self):
        """Test power estimation"""
        phy = HBM4TSVPHY(num_channels=4)
        power = phy.estimate_power()

        assert isinstance(power, TSVPowerBreakdown)
        assert power.total_mW > 0
        assert power.transmitter_mW > 0
        assert power.receiver_mW > 0

    def test_get_power_mW(self):
        """Test getting total power"""
        phy = HBM4TSVPHY(num_channels=4)
        power = phy.get_power_mW()
        assert power > 0

    def test_power_breakdown_components(self):
        """Test power breakdown components"""
        phy = HBM4TSVPHY(num_channels=4)
        power = phy.estimate_power()

        assert power.serializer_mW > 0
        assert power.deserializer_mW > 0
        assert power.clock_recovery_mW > 0
        assert power.leakage_mW > 0

    def test_power_scales_with_channels(self):
        """Test power scales with channel count"""
        phy_4ch = HBM4TSVPHY(num_channels=4)
        phy_8ch = HBM4TSVPHY(num_channels=8)

        power_4ch = phy_4ch.get_power_mW()
        power_8ch = phy_8ch.get_power_mW()

        assert power_8ch > power_4ch


class TestStatistics:
    """Test statistics gathering"""

    def test_get_stats(self):
        """Test overall statistics"""
        phy = HBM4TSVPHY(num_channels=4)
        stats = phy.get_stats()

        assert 'num_channels' in stats
        assert 'total_tsvs' in stats
        assert 'active_tsvs' in stats
        assert stats['num_channels'] == 4
        assert stats['total_tsvs'] > 0

    def test_get_channel_stats(self):
        """Test per-channel statistics"""
        phy = HBM4TSVPHY(num_channels=4)
        stats = phy.get_channel_stats(0)

        assert stats is not None
        assert stats['channel_id'] == 0
        assert 'num_groups' in stats
        assert 'total_tsvs' in stats
        assert 'worst_latency_ps' in stats

    def test_get_invalid_channel_stats(self):
        """Test getting stats for invalid channel"""
        phy = HBM4TSVPHY(num_channels=4)
        stats = phy.get_channel_stats(99)
        assert stats is None

    def test_get_group_stats(self):
        """Test per-group statistics"""
        phy = HBM4TSVPHY(num_channels=4)
        data_groups = phy.get_groups_by_type(TSVGroupType.DATA)
        group = data_groups[0]

        stats = phy.get_group_stats(group.group_id)
        assert stats is not None
        assert stats['group_id'] == group.group_id
        assert 'type' in stats
        assert 'tsv_count' in stats

    def test_reset_stats(self):
        """Test resetting statistics"""
        phy = HBM4TSVPHY(num_channels=4)
        phy.start_training()
        phy.advance_training()
        phy.run_training_sequence(target_groups=[0])

        phy.reset_stats()

        stats = phy.get_stats()
        assert stats['training_cycles'] == 0


class TestIntegration:
    """Test integration with other models"""

    def test_integration_with_lane_repair(self):
        """Test integration with LaneRepair model"""
        repair_model = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=2)
        repair_model.perform_repair(channel_id=0, failed_lane=10)

        phy = HBM4TSVPHY(num_channels=4, lane_repair_model=repair_model)

        # Verify integration
        assert phy.lane_repair_model is not None
        assert repair_model.get_repair_status(0) is not None

    def test_integration_with_multiple_speed_grades(self):
        """Test creating PHY for different speed grades"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            phy = create_tsv_phy(num_channels=32, speed_grade=grade)
            assert phy is not None
            assert phy.data_rate_gtps > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])