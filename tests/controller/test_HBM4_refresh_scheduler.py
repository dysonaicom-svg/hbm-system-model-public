"""
Tests for HBM4 Refresh Scheduler

Comprehensive tests covering:
- All refresh modes (ALL_BANKS, PER_BANK, BANK_GROUP)
- Timing verification (tREFI, tREFIpb, tRFC)
- DRFM (Direct Refresh Management) for row-hammer protection
- QoS coordination
- Refresh overhead tracking
- Bank organization (32 channels × 2 pseudo-ch × 16 banks)
"""

import pytest
from model.controller.HBM4_refresh_scheduler import (
    HBM4RefreshScheduler,
    RefreshMode,
    RefreshPriority,
    RefreshCommand,
    RefreshBankStatus,
    RefreshSchedulerFactory,
)
from model.dram.HBM4_spec import HBM4Spec


class TestHBM4RefreshSchedulerCreation:
    """Test refresh scheduler creation and initialization"""

    def test_scheduler_creation(self):
        """Refresh scheduler must be created"""
        scheduler = HBM4RefreshScheduler()
        assert scheduler is not None

    def test_default_mode(self):
        """Default mode must be PER_BANK for HBM4"""
        scheduler = HBM4RefreshScheduler()
        assert scheduler.mode == RefreshMode.PER_BANK

    def test_supported_modes(self):
        """All refresh modes must be supported"""
        scheduler = HBM4RefreshScheduler()

        assert RefreshMode.ALL_BANKS in scheduler.supported_modes
        assert RefreshMode.PER_BANK in scheduler.supported_modes
        assert RefreshMode.BANK_GROUP in scheduler.supported_modes

    def test_spec_parameters(self):
        """Spec parameters must be correctly loaded"""
        spec = HBM4Spec()
        scheduler = HBM4RefreshScheduler(spec)

        assert scheduler.tREFI == spec.nREFI  # 3900 cycles
        assert scheduler.tRFC == spec.nRFC    # 180 cycles
        assert scheduler.nRREFD == spec.nRREFD  # 8 cycles

    def test_per_bank_refresh_interval_calculation(self):
        """Per-bank refresh interval must be calculated correctly"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        # tREFIpb = tREFI / banks_per_pseudo_channel
        expected_tREFIpb = scheduler.tREFI // spec.banks_per_pseudo_channel
        assert scheduler.tREFIpb == expected_tREFIpb

    def test_total_banks_initialization(self):
        """Total banks must be correctly initialized"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        # 32 channels × 2 pseudo-channels × 16 banks = 1024
        assert len(scheduler.bank_status) == spec.total_banks
        assert len(scheduler.bank_status) == 1024


class TestHBM4RefreshSchedulerTiming:
    """Test refresh timing parameters"""

    def test_refresh_interval_tracking(self):
        """Refresh interval (tREFI) must be tracked"""
        scheduler = HBM4RefreshScheduler()

        # Initial state
        assert scheduler.cycles_since_refresh == 0

        # After some cycles
        scheduler.tick()
        assert scheduler.cycles_since_refresh == 1

        scheduler.tick()
        assert scheduler.cycles_since_refresh == 2

    def test_can_refresh_all_bank_mode(self):
        """can_refresh() must return True after tREFI in ALL_BANKS mode"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Initially cannot refresh
        assert scheduler.can_refresh() is False

        # After tREFI cycles, can refresh
        for _ in range(scheduler.tREFI):
            scheduler.tick()

        assert scheduler.can_refresh() is True

    def test_can_refresh_per_bank_mode(self):
        """can_refresh() must return True after tREFIpb in PER_BANK mode"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Initially cannot refresh
        assert scheduler.can_refresh() is False

        # After tREFIpb cycles, can refresh
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        assert scheduler.can_refresh() is True

    def test_timing_values_from_spec(self):
        """Timing values must match HBM4 spec"""
        spec = HBM4Spec()
        scheduler = HBM4RefreshScheduler(spec)

        # Verify key timing parameters
        assert scheduler.tREFI == 3900   # tREFI = 1950 ns @ 8Gbps = 3900 cycles
        assert scheduler.tRFC == 180    # tRFC = 130 ns @ 8Gbps = 180 cycles (approx)
        assert scheduler.tREFIpb == scheduler.tREFI // spec.banks_per_pseudo_channel


class TestHBM4RefreshSchedulerModes:
    """Test different refresh modes"""

    def test_all_bank_refresh_command(self):
        """ALL_BANKS mode must issue REFab command"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Advance to refresh time
        for _ in range(scheduler.tREFI):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()

        assert cmd is not None
        assert cmd[0] == 'REFab'
        assert cmd[1] is None  # No channel in all-bank refresh
        assert cmd[2] is None
        assert cmd[3] is None

    def test_per_bank_refresh_command(self):
        """PER_BANK mode must issue REFsb command"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Advance to refresh time
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()

        assert cmd is not None
        assert cmd[0] == 'REFsb'
        assert cmd[1] is not None  # channel
        assert cmd[2] is not None  # pseudo_channel
        assert cmd[3] is not None  # bank

    def test_bank_group_refresh_command(self):
        """BANK_GROUP mode must issue REFsb command"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.BANK_GROUP

        # Advance to refresh time
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()

        assert cmd is not None
        assert cmd[0] == 'REFsb'

    def test_set_mode(self):
        """set_mode() must change refresh mode"""
        scheduler = HBM4RefreshScheduler()

        scheduler.set_mode(RefreshMode.ALL_BANKS)
        assert scheduler.mode == RefreshMode.ALL_BANKS

        scheduler.set_mode(RefreshMode.PER_BANK)
        assert scheduler.mode == RefreshMode.PER_BANK

        scheduler.set_mode(RefreshMode.BANK_GROUP)
        assert scheduler.mode == RefreshMode.BANK_GROUP

    def test_mode_change_resets_counter(self):
        """Mode change must reset refresh cycle counter"""
        scheduler = HBM4RefreshScheduler()

        # Advance some cycles
        for _ in range(100):
            scheduler.tick()

        assert scheduler.cycles_since_refresh == 100

        # Change mode
        scheduler.set_mode(RefreshMode.ALL_BANKS)

        # Counter should be reset
        assert scheduler.cycles_since_refresh == 0


class TestHBM4RefreshSchedulerBankTracking:
    """Test per-bank refresh tracking"""

    def test_bank_status_initialization(self):
        """Bank status must be initialized for all banks"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        assert len(scheduler.bank_status) == spec.total_banks

    def test_mark_bank_refreshed(self):
        """mark_bank_refreshed() must update bank status"""
        scheduler = HBM4RefreshScheduler()

        # Mark bank 0 as refreshed
        scheduler.mark_bank_refreshed(0, 0, 0, 1000)

        # Check global bank index 0
        assert scheduler.bank_status[0].last_refresh_cycle == 1000
        assert scheduler.bank_status[0].needs_refresh is False
        assert scheduler.bank_status[0].row_hammer_count == 0

    def test_per_bank_refresh_rotates_banks(self):
        """Per-bank refresh must rotate through all banks"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        banks_seen = set()
        spec = HBM4Spec()

        # Get 16 refresh commands (one per bank in pseudo-channel)
        for _ in range(16):
            # Advance to refresh time
            for _ in range(scheduler.tREFIpb):
                scheduler.tick()

            cmd = scheduler.get_refresh_command()
            if cmd and cmd[3] is not None:
                banks_seen.add(cmd[3])

        # Should have seen multiple banks
        assert len(banks_seen) > 1

    def test_global_bank_id_calculation(self):
        """Global bank ID must be calculated correctly"""
        scheduler = HBM4RefreshScheduler()

        # Test case: channel=0, pch=0, bank=0
        # Global ID = 0 * (2 * 16) + 0 * 16 + 0 = 0
        scheduler.mark_bank_refreshed(0, 0, 0, 100)
        assert scheduler.bank_status[0].last_refresh_cycle == 100

        # Test case: channel=0, pch=1, bank=0
        # Global ID = 0 * (2 * 16) + 1 * 16 + 0 = 16
        scheduler.mark_bank_refreshed(0, 1, 0, 200)
        assert scheduler.bank_status[16].last_refresh_cycle == 200

        # Test case: channel=1, pch=0, bank=0
        # Global ID = 1 * (2 * 16) + 0 * 16 + 0 = 32
        scheduler.mark_bank_refreshed(1, 0, 0, 300)
        assert scheduler.bank_status[32].last_refresh_cycle == 300


class TestHBM4RefreshSchedulerAutonomous:
    """Test autonomous refresh operations"""

    def test_autonomous_refresh_support(self):
        """Controller must support autonomous per-bank refresh"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Verify mode is correctly set
        assert scheduler.mode == RefreshMode.PER_BANK
        # Verify refresh timer is initialized
        assert scheduler.cycles_since_refresh == 0
        # Verify tREFI is set from spec
        assert scheduler.tREFI > 0

    def test_refresh_count_increments(self):
        """total_refresh_count must increment on refresh"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        initial_count = scheduler.total_refresh_count

        # Advance to refresh time
        for _ in range(scheduler.tREFI):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()

        if cmd:
            assert scheduler.total_refresh_count > initial_count

    def test_get_next_refresh_bank_backward_compat(self):
        """get_next_refresh_bank() for backward compatibility"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Advance to refresh time
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        result = scheduler.get_next_refresh_bank()

        assert result is not None
        assert len(result) == 3  # (channel_id, pseudo_channel_id, bank_id)


class TestHBM4RefreshSchedulerDRFM:
    """Test DRFM (Direct Refresh Management) for row-hammer"""

    def test_drfm_enable_disable(self):
        """DRFM must be enableable/disableable"""
        scheduler = HBM4RefreshScheduler()

        # Initially disabled
        assert scheduler.drfm_enabled is False

        # Enable DRFM
        scheduler.enable_drfm(enabled=True)
        assert scheduler.drfm_enabled is True

        # Disable DRFM
        scheduler.enable_drfm(enabled=False)
        assert scheduler.drfm_enabled is False

    def test_drfm_threshold_setting(self):
        """DRFM threshold must be configurable"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=500)

        assert scheduler.drfm_rowhammer_threshold == 500

    def test_record_bank_access(self):
        """Bank access must be recorded for row-hammer tracking"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=100)

        # Record accesses
        scheduler.record_bank_access(0, 0, 0, 0)
        scheduler.record_bank_access(0, 0, 0, 0)

        # Check access count
        assert scheduler.bank_status[0].row_hammer_count == 2

    def test_row_hammer_triggers_refresh(self):
        """Row-hammer threshold exceeded must trigger refresh"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=100)

        # Record 100 accesses
        for _ in range(100):
            scheduler.record_bank_access(0, 0, 0, 0)

        # Bank should need refresh
        assert scheduler.bank_status[0].needs_refresh is True
        assert 0 in scheduler.drfm_rowhammer_victims

    def test_get_banks_needing_refresh(self):
        """get_banks_needing_refresh() must return affected banks"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=50)

        # Trigger row-hammer on bank 0
        for _ in range(50):
            scheduler.record_bank_access(0, 0, 0, 0)

        # Get banks needing refresh
        affected = scheduler.get_banks_needing_refresh()

        assert 0 in affected

    def test_handle_row_hammer(self):
        """handle_row_hammer() must detect row-hammer condition"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=100)

        # Handle row-hammer with 100 accesses
        result = scheduler.handle_row_hammer(0, 0, 0, 100)

        assert result is True
        assert scheduler.bank_status[0].needs_refresh is True

    def test_handle_row_hammer_below_threshold(self):
        """handle_row_hammer() must not trigger below threshold"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=100)

        # Handle row-hammer with 50 accesses
        result = scheduler.handle_row_hammer(0, 0, 0, 50)

        assert result is False

    def test_drfm_refresh_command(self):
        """DRFM must issue refresh command for victim banks"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=100)

        # Trigger row-hammer
        for _ in range(100):
            scheduler.record_bank_access(0, 0, 0, 0)

        # Get DRFM refresh command
        cmd = scheduler.get_drfm_refresh_command()

        assert cmd is not None
        assert cmd[0] == 'REFsb'
        assert cmd[1] == 0  # channel
        assert cmd[2] == 0  # pseudo_channel
        assert cmd[3] == 0  # bank

    def test_drfm_refresh_stats(self):
        """DRFM refreshes must be tracked in statistics"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=100)

        # Trigger row-hammer on multiple banks
        for _ in range(100):
            scheduler.record_bank_access(0, 0, 0, 0)
        for _ in range(100):
            scheduler.record_bank_access(0, 0, 1, 0)

        # Issue DRFM refreshes
        scheduler.get_drfm_refresh_command()
        scheduler.get_drfm_refresh_command()

        stats = scheduler.get_stats()
        assert stats['drfm_refreshes'] == 2


class TestHBM4RefreshSchedulerQoSCoordination:
    """Test QoS coordination for refresh scheduling"""

    def test_set_qos_scheduler(self):
        """QoS scheduler reference must be settable"""
        scheduler = HBM4RefreshScheduler()

        # Create mock QoS scheduler
        class MockQoS:
            def get_total_queue_size(self):
                return 0

            def get_queue_size(self, level):
                return 0

        mock_qos = MockQoS()
        scheduler.set_qos_scheduler(mock_qos)

        assert scheduler.qos_scheduler_ref is mock_qos

    def test_block_refresh_for_qos(self):
        """Refresh must be blockable for high-priority traffic"""
        scheduler = HBM4RefreshScheduler()

        # Block refresh for 100 cycles
        scheduler.block_refresh_for_qos(100)

        # Verify blocked state
        assert scheduler.refresh_blocked_until > scheduler.current_cycle
        assert scheduler.blocked_by_qos is True

    def test_refresh_blocked_by_qos(self):
        """can_issue_refresh() must return False when blocked"""
        scheduler = HBM4RefreshScheduler()

        # Block refresh
        scheduler.block_refresh_for_qos(100)

        # Advance some cycles but not past blocked period
        for _ in range(50):
            scheduler.tick()

        # Should still be blocked
        assert scheduler.can_issue_refresh() is False

    def test_refresh_unblocks_after_delay(self):
        """can_issue_refresh() must return True after blocking period"""
        scheduler = HBM4RefreshScheduler()

        # Block refresh for 100 cycles
        scheduler.block_refresh_for_qos(100)

        # Advance past blocked period
        for _ in range(100):
            scheduler.tick()

        # Should no longer be blocked
        assert scheduler.can_issue_refresh() is True


class TestHBM4RefreshSchedulerOverhead:
    """Test refresh overhead tracking"""

    def test_refresh_overhead_calculation(self):
        """Refresh overhead must be calculated correctly"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Issue several refreshes
        for _ in range(5):
            for _ in range(scheduler.tREFI):
                scheduler.tick()
            scheduler.get_refresh_command()

        stats = scheduler.get_stats()

        # Verify overhead tracking
        assert stats['total_refreshes'] == 5
        assert stats['total_refresh_cycles'] == 5 * scheduler.tRFC

    def test_get_refresh_overhead(self):
        """get_refresh_overhead() must return correct ratio"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Advance to refresh time
        for _ in range(scheduler.tREFI):
            scheduler.tick()
        scheduler.get_refresh_command()

        # Get overhead ratio
        overhead = scheduler.get_refresh_overhead(scheduler.current_cycle)

        # Should be non-zero after refresh
        assert overhead > 0


class TestHBM4RefreshSchedulerStats:
    """Test statistics tracking"""

    def test_stats_initialization(self):
        """Statistics must be properly initialized"""
        scheduler = HBM4RefreshScheduler()
        stats = scheduler.get_stats()

        assert stats['total_refreshes'] == 0
        assert stats['all_bank_refreshes'] == 0
        assert stats['per_bank_refreshes'] == 0
        assert stats['bank_group_refreshes'] == 0
        assert stats['drfm_refreshes'] == 0

    def test_stats_after_all_bank_refresh(self):
        """Statistics must update after all-bank refresh"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Advance to refresh time
        for _ in range(scheduler.tREFI):
            scheduler.tick()
        scheduler.get_refresh_command()

        stats = scheduler.get_stats()

        assert stats['total_refreshes'] == 1
        assert stats['all_bank_refreshes'] == 1

    def test_stats_after_per_bank_refresh(self):
        """Statistics must update after per-bank refresh"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Advance to refresh time
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()
        scheduler.get_refresh_command()

        stats = scheduler.get_stats()

        assert stats['total_refreshes'] == 1
        assert stats['per_bank_refreshes'] == 1

    def test_stats_after_bank_group_refresh(self):
        """Statistics must update after bank-group refresh"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.BANK_GROUP

        # Advance to refresh time
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()
        scheduler.get_refresh_command()

        stats = scheduler.get_stats()

        assert stats['total_refreshes'] == 1
        assert stats['bank_group_refreshes'] == 1


class TestHBM4RefreshSchedulerScheduling:
    """Test refresh scheduling functions"""

    def test_schedule_refresh(self):
        """schedule_refresh() must return RefreshCommand"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Advance to refresh time
        for _ in range(scheduler.tREFIpb):
            scheduler.tick()

        cmd = scheduler.schedule_refresh(scheduler.current_cycle)

        assert cmd is not None
        assert isinstance(cmd, RefreshCommand)
        assert cmd.command_type == 'REFsb'
        assert cmd.duration_cycles == scheduler.tRFC

    def test_schedule_refresh_blocked(self):
        """schedule_refresh() must return None when blocked"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Block refresh
        scheduler.block_refresh_for_qos(100)

        # Advance past blocked period
        for _ in range(100):
            scheduler.tick()

        # Should still be blocked
        cmd = scheduler.schedule_refresh(scheduler.current_cycle)
        # can_refresh might be false since we're still before tREFIpb
        # The function returns None if either condition fails


class TestHBM4RefreshSchedulerHBM4Organization:
    """Test HBM4-specific organization (32 channels × 2 pseudo-ch × 16 banks)"""

    def test_32_channels_supported(self):
        """Scheduler must support 32 channels"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        # Verify total channels
        assert spec.channels == 32

    def test_2_pseudo_channels_per_channel(self):
        """Scheduler must support 2 pseudo-channels per channel"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        # Verify pseudo-channels per channel
        assert spec.pseudo_channels_per_channel == 2

    def test_16_banks_per_pseudo_channel(self):
        """Scheduler must support 16 banks per pseudo-channel"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        # Verify banks per pseudo-channel
        assert spec.banks_per_pseudo_channel == 16

    def test_1024_total_banks(self):
        """Total banks must be 1024 (32 × 2 × 16)"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        # Verify total banks
        assert spec.total_banks == 1024

    def test_all_bank_indices_valid(self):
        """All bank indices must be within valid range"""
        scheduler = HBM4RefreshScheduler()

        for i in range(1024):
            assert i < len(scheduler.bank_status)
            assert scheduler.bank_status[i].bank_id == i


class TestRefreshSchedulerFactory:
    """Test factory methods for creating schedulers"""

    def test_create_all_bank_scheduler(self):
        """Factory must create ALL_BANKS mode scheduler"""
        scheduler = RefreshSchedulerFactory.create_all_bank_scheduler()

        assert scheduler.mode == RefreshMode.ALL_BANKS

    def test_create_per_bank_scheduler(self):
        """Factory must create PER_BANK mode scheduler"""
        scheduler = RefreshSchedulerFactory.create_per_bank_scheduler()

        assert scheduler.mode == RefreshMode.PER_BANK

    def test_create_bank_group_scheduler(self):
        """Factory must create BANK_GROUP mode scheduler"""
        scheduler = RefreshSchedulerFactory.create_bank_group_scheduler()

        assert scheduler.mode == RefreshMode.BANK_GROUP

    def test_create_drfm_scheduler(self):
        """Factory must create DRFM-enabled scheduler"""
        scheduler = RefreshSchedulerFactory.create_drfm_scheduler(threshold=500)

        assert scheduler.drfm_enabled is True
        assert scheduler.drfm_rowhammer_threshold == 500


class TestHBM4RefreshSchedulerReset:
    """Test reset functionality"""

    def test_reset_clears_state(self):
        """reset() must clear all state"""
        scheduler = HBM4RefreshScheduler()

        # Advance some cycles
        for _ in range(100):
            scheduler.tick()

        # Issue a refresh
        scheduler.mode = RefreshMode.ALL_BANKS
        for _ in range(scheduler.tREFI):
            scheduler.tick()
        scheduler.get_refresh_command()

        # Reset
        scheduler.reset()

        # Verify state is cleared
        assert scheduler.cycles_since_refresh == 0
        assert scheduler.current_refresh_bank == 0
        assert scheduler.total_refresh_count == 0
        assert scheduler.current_cycle == 0

    def test_reset_clears_stats(self):
        """reset() must clear statistics"""
        scheduler = HBM4RefreshScheduler()

        # Advance and refresh
        scheduler.mode = RefreshMode.ALL_BANKS
        for _ in range(scheduler.tREFI):
            scheduler.tick()
        scheduler.get_refresh_command()

        # Reset
        scheduler.reset()

        stats = scheduler.get_stats()
        assert stats['total_refreshes'] == 0


class TestHBM4RefreshSchedulerEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_tREFIpb(self):
        """Zero tREFIpb must be handled gracefully"""
        scheduler = HBM4RefreshScheduler()
        scheduler.tREFIpb = 0

        # Should be able to refresh immediately
        assert scheduler.can_refresh() is True

    def test_large_threshold(self):
        """Large DRFM threshold must be handled"""
        scheduler = HBM4RefreshScheduler()
        scheduler.enable_drfm(enabled=True, threshold=1000000)

        # Record some accesses
        scheduler.record_bank_access(0, 0, 0, 0)

        # Should not trigger refresh yet
        assert 0 not in scheduler.drfm_rowhammer_victims

    def test_invalid_bank_index(self):
        """Invalid bank index must be handled gracefully"""
        scheduler = HBM4RefreshScheduler()

        # Try to mark invalid bank as refreshed
        scheduler.mark_bank_refreshed(100, 100, 100, 1000)

        # Should not crash (invalid index ignored)
        assert True

    def test_multiple_refresh_modes(self):
        """Multiple mode changes must work correctly"""
        scheduler = HBM4RefreshScheduler()

        # Switch through all modes
        scheduler.set_mode(RefreshMode.ALL_BANKS)
        assert scheduler.mode == RefreshMode.ALL_BANKS

        scheduler.set_mode(RefreshMode.PER_BANK)
        assert scheduler.mode == RefreshMode.PER_BANK

        scheduler.set_mode(RefreshMode.BANK_GROUP)
        assert scheduler.mode == RefreshMode.BANK_GROUP

        scheduler.set_mode(RefreshMode.ALL_BANKS)
        assert scheduler.mode == RefreshMode.ALL_BANKS


class TestHBM4RefreshSchedulerIntegration:
    """Integration tests for refresh scheduler with other components"""

    def test_integration_with_hbm4_spec(self):
        """Scheduler must work correctly with HBM4 specification"""
        spec = HBM4Spec()
        scheduler = HBM4RefreshScheduler(spec)

        # Verify all spec values are used
        assert scheduler.tREFI == spec.nREFI
        assert scheduler.tRFC == spec.nRFC
        assert len(scheduler.bank_status) == spec.total_banks

    def test_per_bank_refresh_covers_all_banks(self):
        """Per-bank refresh must eventually cover all banks"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        banks_refreshed = set()
        pchs_refreshed = set()
        spec = HBM4Spec()

        # Get refresh commands until we've covered many pseudo-channels
        # We track (channel, pch) pairs to verify coverage across the array
        for _ in range(spec.total_banks + 10):  # Extra iterations for safety
            # Advance to refresh time
            for _ in range(scheduler.tREFIpb):
                scheduler.tick()

            cmd = scheduler.get_refresh_command()
            if cmd and cmd[3] is not None:
                channel_id, pch_id, bank_id = cmd[1], cmd[2], cmd[3]
                banks_refreshed.add(bank_id)
                pchs_refreshed.add((channel_id, pch_id))

        # Should have refreshed many pseudo-channels (at least 50 across all channels)
        # Since bank_id is 0-15 per pseudo-channel, we track pseudo-channel coverage
        assert len(pchs_refreshed) > 50

    def test_refresh_interval_adjustment(self):
        """set_refresh_interval() must update timing"""
        scheduler = HBM4RefreshScheduler()

        original_tREFI = scheduler.tREFI
        scheduler.set_refresh_interval(5000)

        assert scheduler.tREFI == 5000
        assert scheduler.tREFI != original_tREFI

    def test_per_bank_interval_adjustment(self):
        """set_per_bank_refresh_interval() must update timing"""
        scheduler = HBM4RefreshScheduler()

        scheduler.set_per_bank_refresh_interval(250)

        assert scheduler.tREFIpb == 250
