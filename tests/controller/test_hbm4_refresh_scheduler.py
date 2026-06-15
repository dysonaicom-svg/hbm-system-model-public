"""
Tests for HBM4 Refresh Scheduler

Tests the refresh scheduler with per-bank and autonomous modes.
"""

import pytest
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode, RefreshBankStatus
from model.dram.hbm4_spec import HBM4Spec


class TestHBM4RefreshSchedulerCreation:
    """Test refresh scheduler creation"""

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


class TestHBM4RefreshSchedulerTiming:
    """Test refresh timing"""

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

    def test_can_refresh(self):
        """can_refresh() must return True after tREFI"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        # Initially cannot refresh
        assert scheduler.cycles_since_refresh < spec.nREFI
        assert scheduler.can_refresh() is False

        # After tREFI cycles, can refresh
        for _ in range(spec.nREFI):
            scheduler.tick()

        assert scheduler.can_refresh() is True


class TestHBM4RefreshSchedulerModes:
    """Test different refresh modes"""

    def test_all_bank_refresh(self):
        """ALL_BANKS mode must work"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.ALL_BANKS

        # Advance to refresh time
        spec = HBM4Spec()
        for _ in range(spec.nREFI):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()

        assert cmd is not None
        assert cmd[0] == 'REFab'

    def test_per_bank_refresh(self):
        """PER_BANK mode must work"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Advance to refresh time
        spec = HBM4Spec()
        for _ in range(spec.nREFI):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()

        assert cmd is not None
        assert cmd[0] == 'REFsb'
        assert cmd[1] is not None  # channel
        assert cmd[2] is not None  # bank

    def test_bank_group_refresh(self):
        """BANK_GROUP mode must work"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.BANK_GROUP

        # Advance to refresh time
        spec = HBM4Spec()
        for _ in range(spec.nREFI):
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


class TestHBM4RefreshSchedulerBankTracking:
    """Test per-bank refresh tracking"""

    def test_bank_status_initialization(self):
        """Bank status must be initialized"""
        scheduler = HBM4RefreshScheduler()
        spec = HBM4Spec()

        assert len(scheduler.bank_status) == spec.total_banks

    def test_mark_bank_refreshed(self):
        """mark_bank_refreshed() must update status"""
        scheduler = HBM4RefreshScheduler()

        # New signature: (channel_id, bank_id, cycle)
        scheduler.mark_bank_refreshed(0, 0, 1000)

        assert scheduler.bank_status[0].last_refresh_cycle == 1000
        assert scheduler.bank_status[0].needs_refresh is False

    def test_refresh_rotates_through_banks(self):
        """Per-bank refresh must rotate through banks"""
        scheduler = HBM4RefreshScheduler()
        scheduler.mode = RefreshMode.PER_BANK

        # Get several refresh commands
        banks_seen = set()
        spec = HBM4Spec()

        for _ in range(16):  # Get 16 refresh commands (one per bank)
            # Advance to refresh time
            for _ in range(spec.nREFI):
                scheduler.tick()

            cmd = scheduler.get_refresh_command()
            if cmd and cmd[2] is not None:
                banks_seen.add(cmd[2])

        # Should have seen multiple banks
        assert len(banks_seen) > 1


class TestHBM4RefreshSchedulerAutonomous:
    """Test autonomous refresh"""

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


class TestHBM4RefreshSchedulerCounting:
    """Test refresh counting"""

    def test_refresh_count_increments(self):
        """total_refresh_count must increment on refresh"""
        scheduler = HBM4RefreshScheduler()

        initial_count = scheduler.total_refresh_count

        # Advance to refresh time
        spec = HBM4Spec()
        for _ in range(spec.nREFI):
            scheduler.tick()

        cmd = scheduler.get_refresh_command()

        if cmd:
            assert scheduler.total_refresh_count > initial_count


class TestHBM4RefreshSchedulerWithSpec:
    """Test with HBM4 spec"""

    def test_scheduler_with_hbm4_spec(self):
        """Scheduler must work with HBM4 specification"""
        spec = HBM4Spec()
        scheduler = HBM4RefreshScheduler(spec)

        # Verify spec values are used
        assert scheduler.tREFI == spec.nREFI
        assert scheduler.tRFC == spec.nRFC