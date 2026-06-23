"""
HBM4 Refresh Scheduler with Autonomous Per-Bank Refresh

Based on research findings:
- Per-bank and all-bank refresh modes
- Autonomous refresh management
- DRFM (Direct Refresh Management) for row-hammer mitigation
- Staggered refresh for reduced peak power
- QoS-aware refresh scheduling

Key HBM4 Parameters:
- tREFI: 1950 ns (base), 3900 cycles @ 8Gbps
- tRFC: 130 ns (per-bank refresh time) - 180 cycles in spec
- tRRD: 4 cycles (activate-to-activate)
- tFAW: 16 cycles (four-bank activation window)
- 32 channels × 2 pseudo-ch × 16 banks = 1024 total banks

Reference:
- Synopsys DesignWare HBM4/4E Controller IP
- JEDEC JESD270-4A HBM4 specification
- Ramulator 2.0 HBM3 refresh implementation
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Set
from collections import deque
import time

from model.dram.hbm4_spec import HBM4Spec


class RefreshMode(Enum):
    """Refresh operating modes for HBM4

    HBM4 supports multiple refresh modes for different power/performance tradeoffs:
    - ALL_BANKS: Classic mode, refreshes all banks simultaneously (blocks traffic)
    - PER_BANK: Staggered per-bank refresh, less intrusive (default for HBM4)
    - BANK_GROUP: Refresh by bank groups, balanced approach
    """
    ALL_BANKS = "all"         # Refresh all banks at once
    PER_BANK = "per_bank"     # Staggered per-bank refresh (default for HBM4)
    BANK_GROUP = "bank_group"  # Refresh by bank group


class RefreshPriority(Enum):
    """Refresh scheduling priority for QoS coordination"""
    CRITICAL = 3   # Cannot be delayed (defective rows)
    HIGH = 2       # Minimal delay allowed
    NORMAL = 1     # Normal delay tolerance
    LOW = 0        # Can be delayed for high-priority traffic


@dataclass
class RefreshBankStatus:
    """Status tracking for per-bank refresh

    Tracks when each bank was last refreshed and if it needs refresh.
    """
    bank_id: int
    last_refresh_cycle: int = 0
    needs_refresh: bool = False
    row_hammer_count: int = 0
    is_defective: bool = False


@dataclass
class RefreshCommand:
    """Refresh command structure"""
    command_type: str  # 'REFab', 'REFsb', 'REFbg'
    channel_id: Optional[int] = None
    pseudo_channel_id: Optional[int] = None
    bank_id: Optional[int] = None
    bank_group_id: Optional[int] = None
    cycle: int = 0
    duration_cycles: int = 0
    priority: RefreshPriority = RefreshPriority.NORMAL


@dataclass
class RefreshStatistics:
    """Detailed refresh statistics"""
    total_refreshes: int = 0
    all_bank_refreshes: int = 0
    per_bank_refreshes: int = 0
    bank_group_refreshes: int = 0
    drfm_refreshes: int = 0
    total_refresh_cycles: int = 0
    refresh_overhead_ratio: float = 0.0
    banks_refreshed: Set[int] = field(default_factory=set)
    last_refresh_cycle: int = 0
    next_refresh_cycle: int = 0


class HBM4RefreshScheduler:
    """HBM4 Refresh Scheduler

    Manages DRAM refresh operations with support for:
    - All-bank refresh (HBM2 style)
    - Per-bank refresh (staggered, HBM3/HBM4 style)
    - Bank group refresh
    - Autonomous refresh scheduling
    - DRFM (Direct Refresh Management) for row-hammer mitigation
    - QoS-aware refresh coordination

    Reference: Synopsys DesignWare HBM4/4E Controller IP
    """

    def __init__(self, config: Optional[HBM4Spec] = None):
        """Initialize refresh scheduler

        Args:
            config: HBM4 specification (uses default if None)
        """
        if config is None:
            config = HBM4Spec()
        self.spec = config
        self.mode = RefreshMode.PER_BANK  # Default to per-bank for HBM4

        # === Timing Parameters from HBM4 Spec ===
        # tREFI: Refresh interval
        # For all-bank refresh: tREFI = 1950 ns = 3900 cycles @ 8Gbps (125ps tCK)
        # For per-bank refresh: tREFIpb = tREFI / (banks per pseudo-channel)
        self.tREFI = config.nREFI  # Refresh interval (cycles) - 3900 for all-bank
        self.tRFC = config.nRFC    # Refresh command duration (cycles) - 180
        self.nRREFD = config.nRREFD  # Per-bank refresh interval

        # Calculated per-bank refresh interval
        # Each REFI period, we need to refresh (banks_per_pseudo_channel) banks
        # So tREFIpb = tREFI / banks_per_pseudo_channel
        self.tREFIpb = self.tREFI // config.banks_per_pseudo_channel  # Per-bank interval

        # === Refresh State Tracking ===
        self.cycles_since_refresh = 0
        self.current_refresh_bank = 0  # Global bank index (0-1023)
        self.current_refresh_pch = 0    # Pseudo-channel being refreshed
        self.total_refresh_count = 0
        self.current_cycle = 0

        # === Per-Bank Refresh Tracking ===
        # 32 channels × 2 pseudo-channels × 16 banks = 1024 total banks
        self.bank_status: List[RefreshBankStatus] = [
            RefreshBankStatus(bank_id=i)
            for i in range(config.total_banks)
        ]

        # Bank group refresh tracking (8 groups × 16 banks)
        self.bank_groups_per_channel = config.bank_groups_per_channel
        self.current_bank_group = 0

        # === Supported Modes ===
        self.supported_modes = [
            RefreshMode.ALL_BANKS,
            RefreshMode.PER_BANK,
            RefreshMode.BANK_GROUP
        ]

        # === DRFM (Direct Refresh Management) ===
        # DRFM provides row-hammer mitigation by tracking access counts
        # and triggering targeted refreshes for frequently accessed rows
        self.drfm_enabled = False
        self.drfm_rowhammer_threshold = 1000  # cycles before refresh needed
        self.drfm_rowhammer_victims: List[int] = []  # Banks identified as row-hammer victims

        # === QoS Coordination ===
        # Refresh can be delayed for high-priority traffic
        self.refresh_queue: deque[RefreshCommand] = deque()
        self.max_refresh_delay = 100  # Maximum cycles to delay refresh
        self.qos_scheduler_ref: Optional[Any] = None  # Reference to QoS scheduler

        # === Scheduling State ===
        self.refresh_in_progress = False
        self.refresh_blocked_until = 0
        self.blocked_by_qos = False

        # === Statistics ===
        self.stats = RefreshStatistics()

    def set_qos_scheduler(self, qos_scheduler: Any):
        """Set reference to QoS scheduler for coordination

        Args:
            qos_scheduler: Reference to HBM4QoSScheduler instance
        """
        self.qos_scheduler_ref = qos_scheduler

    def tick(self):
        """Advance refresh timer by one cycle"""
        self.cycles_since_refresh += 1
        self.current_cycle += 1

    def can_refresh(self) -> bool:
        """Check if refresh is needed based on current mode

        Returns:
            True if enough cycles have passed since last refresh
        """
        if self.mode in (RefreshMode.PER_BANK, RefreshMode.BANK_GROUP):
            return self.cycles_since_refresh >= self.tREFIpb
        else:
            return self.cycles_since_refresh >= self.tREFI

    def can_issue_refresh(self) -> bool:
        """Check if refresh can be issued (not blocked by QoS)

        Returns:
            True if refresh can be issued now
        """
        if self.refresh_blocked_until > self.current_cycle:
            return False

        if self.qos_scheduler_ref is not None:
            # Check if high-priority traffic is present
            high_priority_requests = self.qos_scheduler_ref.get_total_queue_size()
            # Allow refresh if no critical requests pending
            if high_priority_requests > 0:
                # Check for CRITICAL priority requests
                critical_count = self.qos_scheduler_ref.get_queue_size(
                    self.qos_scheduler_ref.QOS_CRITICAL
                )
                if critical_count > 0:
                    return False

        return True

    def get_refresh_command(self) -> Optional[Tuple[str, Optional[int], Optional[int], Optional[int]]]:
        """Get the next refresh command to execute

        Returns:
            Tuple of (command_name, channel_id, pseudo_channel_id, bank_id) or None
            - channel_id: 0-31 for 32 channels
            - pseudo_channel_id: 0 or 1 (within channel)
            - bank_id: 0-15 (within pseudo-channel)
        """
        if not self.can_refresh():
            return None

        if not self.can_issue_refresh():
            return None

        if self.mode == RefreshMode.ALL_BANKS:
            return self._issue_all_bank_refresh()
        elif self.mode == RefreshMode.PER_BANK:
            return self._issue_per_bank_refresh()
        elif self.mode == RefreshMode.BANK_GROUP:
            return self._issue_bank_group_refresh()

        return None

    def _issue_all_bank_refresh(self) -> Tuple[str, None, None, None]:
        """Issue all-bank refresh command

        Returns:
            Tuple of (command_name, None, None, None)
        """
        self.total_refresh_count += 1
        self.cycles_since_refresh = 0
        self.stats.total_refreshes += 1
        self.stats.all_bank_refreshes += 1
        self.stats.total_refresh_cycles += self.tRFC
        self.stats.last_refresh_cycle = self.current_cycle
        self.stats.next_refresh_cycle = self.current_cycle + self.tREFI

        return ('REFab', None, None, None)

    def _issue_per_bank_refresh(self) -> Tuple[str, int, int, int]:
        """Issue per-bank refresh command

        Returns:
            Tuple of (command_name, channel_id, pseudo_channel_id, bank_id)
        """
        bank_to_refresh = self.current_refresh_bank

        # Calculate channel, pseudo-channel, and bank indices
        banks_per_pch = self.spec.banks_per_pseudo_channel  # 16
        pch_idx = bank_to_refresh // banks_per_pch  # 0-63 (pseudo-channel within array)
        bank_idx = bank_to_refresh % banks_per_pch  # 0-15

        # Map pseudo-channel index to channel and pseudo-channel
        # Each physical channel has 2 pseudo-channels
        channel_id = pch_idx // 2  # 0-31
        pseudo_channel_id = pch_idx % 2  # 0 or 1

        # Advance to next bank
        self.current_refresh_bank = (self.current_refresh_bank + 1) % self.spec.total_banks
        self.cycles_since_refresh = 0
        self.total_refresh_count += 1
        self.stats.total_refreshes += 1
        self.stats.per_bank_refreshes += 1
        self.stats.total_refresh_cycles += self.tRFC
        self.stats.last_refresh_cycle = self.current_cycle
        self.stats.banks_refreshed.add(bank_to_refresh)

        # Calculate next refresh time based on per-bank interval
        self.stats.next_refresh_cycle = self.current_cycle + self.tREFIpb

        # Update bank status
        self.mark_bank_refreshed(channel_id, pseudo_channel_id, bank_idx, self.current_cycle)

        return ('REFsb', channel_id, pseudo_channel_id, bank_idx)

    def _issue_bank_group_refresh(self) -> Tuple[str, int, int, int]:
        """Issue bank group refresh command

        Returns:
            Tuple of (command_name, channel_id, pseudo_channel_id, bank_id)
        """
        # Bank group refresh targets a specific bank group
        group_to_refresh = self.current_bank_group

        # Calculate bank index: bank group * banks_per_group
        # Each bank group has (banks_per_pseudo_channel / bank_groups_per_channel) banks
        banks_per_group = self.spec.banks_per_pseudo_channel // self.bank_groups_per_channel
        bank_id = group_to_refresh * banks_per_group

        # Calculate pseudo-channel index (0-63) for the target bank group
        # 8 bank groups per channel means 4 groups per pseudo-channel
        groups_per_pch = self.bank_groups_per_channel // self.spec.pseudo_channels_per_channel  # 4
        pch_idx = group_to_refresh // groups_per_pch
        channel_id = pch_idx // 2
        pseudo_channel_id = pch_idx % 2

        # Advance to next bank group (wraps at 8)
        self.current_bank_group = (self.current_bank_group + 1) % self.bank_groups_per_channel
        self.cycles_since_refresh = 0
        self.total_refresh_count += 1
        self.stats.total_refreshes += 1
        self.stats.bank_group_refreshes += 1
        self.stats.total_refresh_cycles += self.tRFC
        self.stats.last_refresh_cycle = self.current_cycle

        # Calculate next refresh time
        self.stats.next_refresh_cycle = self.current_cycle + self.tREFIpb

        return ('REFsb', channel_id, pseudo_channel_id, bank_id)

    def get_next_refresh_bank(self) -> Optional[Tuple[int, int, int]]:
        """Get next bank to refresh (wrapper for backward compatibility)

        Returns:
            Tuple of (channel_id, pseudo_channel_id, bank_id) or None if no refresh needed
        """
        result = self.get_refresh_command()
        if result is None:
            return None

        command_name, channel_id, pseudo_channel_id, bank_id = result
        return (channel_id, pseudo_channel_id, bank_id)

    def set_mode(self, mode: RefreshMode):
        """Set refresh operating mode

        Args:
            mode: New refresh mode
        """
        if mode in self.supported_modes:
            self.mode = mode
            # Reset refresh cycle counter when mode changes
            self.cycles_since_refresh = 0

    def mark_bank_refreshed(self, channel_id: int, pseudo_channel_id: int,
                           bank_id: int, cycle: int):
        """Mark a specific bank as refreshed

        Args:
            channel_id: Channel index (0-31)
            pseudo_channel_id: Pseudo-channel index (0 or 1)
            bank_id: Bank index within pseudo-channel (0-15)
            cycle: Current cycle when refresh occurred
        """
        # Convert to global bank index
        global_bank_id = (
            channel_id * self.spec.pseudo_channels_per_channel * self.spec.banks_per_pseudo_channel +
            pseudo_channel_id * self.spec.banks_per_pseudo_channel +
            bank_id
        )
        if 0 <= global_bank_id < len(self.bank_status):
            self.bank_status[global_bank_id].last_refresh_cycle = cycle
            self.bank_status[global_bank_id].needs_refresh = False
            self.bank_status[global_bank_id].row_hammer_count = 0

    def enable_drfm(self, enabled: bool = True, threshold: int = None):
        """Enable/disable DRFM (Direct Refresh Management)

        DRFM provides row-hammer mitigation by tracking access counts
        and triggering targeted refreshes.

        Args:
            enabled: True to enable DRFM
            threshold: Optional threshold for row-hammer detection (cycles)
        """
        self.drfm_enabled = enabled
        if threshold is not None:
            self.drfm_rowhammer_threshold = threshold

    def record_bank_access(self, channel_id: int, pseudo_channel_id: int,
                          bank_id: int, row_id: int = 0):
        """Record a bank access for row-hammer tracking

        Args:
            channel_id: Channel index (0-31)
            pseudo_channel_id: Pseudo-channel index (0 or 1)
            bank_id: Bank index within pseudo-channel (0-15)
            row_id: Row that was accessed
        """
        if not self.drfm_enabled:
            return

        # Convert to global bank index
        global_bank_id = (
            channel_id * self.spec.pseudo_channels_per_channel * self.spec.banks_per_pseudo_channel +
            pseudo_channel_id * self.spec.banks_per_pseudo_channel +
            bank_id
        )

        if 0 <= global_bank_id < len(self.bank_status):
            self.bank_status[global_bank_id].row_hammer_count += 1

            # Mark as needing refresh if threshold exceeded
            if self.bank_status[global_bank_id].row_hammer_count >= self.drfm_rowhammer_threshold:
                self.bank_status[global_bank_id].needs_refresh = True
                if global_bank_id not in self.drfm_rowhammer_victims:
                    self.drfm_rowhammer_victims.append(global_bank_id)

    def get_banks_needing_refresh(self) -> List[int]:
        """Get list of banks that need refresh (DRFM)

        Returns:
            List of global bank IDs that need refresh due to row-hammer
        """
        if not self.drfm_enabled:
            return []

        # Return banks marked as needing refresh
        return [
            bs.bank_id for bs in self.bank_status
            if bs.needs_refresh
        ]

    def get_drfm_refresh_command(self) -> Optional[Tuple[str, int, int, int]]:
        """Get a DRFM-triggered refresh command for row-hammer mitigation

        Returns:
            Tuple of (command_name, channel_id, pseudo_channel_id, bank_id) or None
        """
        if not self.drfm_enabled or not self.drfm_rowhammer_victims:
            return None

        # Get next victim bank
        victim_id = self.drfm_rowhammer_victims.pop(0)

        # Convert global bank ID to channel/pseudo-channel/bank
        banks_per_pch = self.spec.banks_per_pseudo_channel
        pch_idx = victim_id // banks_per_pch
        bank_idx = victim_id % banks_per_pch
        channel_id = pch_idx // 2
        pseudo_channel_id = pch_idx % 2

        # Update stats
        self.stats.drfm_refreshes += 1

        return ('REFsb', channel_id, pseudo_channel_id, bank_idx)

    def block_refresh_for_qos(self, duration_cycles: int):
        """Temporarily block refresh for high-priority traffic

        Args:
            duration_cycles: Number of cycles to block refresh
        """
        self.refresh_blocked_until = self.current_cycle + duration_cycles
        self.blocked_by_qos = True

    def get_stats(self) -> Dict[str, Any]:
        """Get refresh scheduler statistics

        Returns:
            Dictionary with detailed statistics
        """
        # Calculate refresh overhead ratio
        if self.current_cycle > 0:
            self.stats.refresh_overhead_ratio = self.stats.total_refresh_cycles / self.current_cycle

        return {
            'total_refreshes': self.stats.total_refreshes,
            'all_bank_refreshes': self.stats.all_bank_refreshes,
            'per_bank_refreshes': self.stats.per_bank_refreshes,
            'bank_group_refreshes': self.stats.bank_group_refreshes,
            'drfm_refreshes': self.stats.drfm_refreshes,
            'total_refresh_cycles': self.stats.total_refresh_cycles,
            'refresh_overhead_ratio': self.stats.refresh_overhead_ratio,
            'cycles_since_refresh': self.cycles_since_refresh,
            'current_cycle': self.current_cycle,
            'mode': self.mode.value,
            'drfm_enabled': self.drfm_enabled,
            'refresh_blocked': self.refresh_blocked_until > self.current_cycle,
            'blocked_by_qos': self.blocked_by_qos,
            'tREFI': self.tREFI,
            'tREFIpb': self.tREFIpb,
            'tRFC': self.tRFC,
        }

    def set_refresh_interval(self, cycles: int):
        """Set refresh interval (tREFI) for all-bank refresh

        Args:
            cycles: New refresh interval in cycles
        """
        self.tREFI = cycles
        # Recalculate per-bank interval
        self.tREFIpb = self.tREFI // self.spec.banks_per_pseudo_channel

    def set_per_bank_refresh_interval(self, cycles: int):
        """Set refresh interval (tREFIpb) for per-bank refresh

        Args:
            cycles: New per-bank refresh interval in cycles
        """
        self.tREFIpb = cycles

    def schedule_refresh(self, current_cycle: int,
                        pending_high_priority: int = 0) -> Optional[RefreshCommand]:
        """Schedule a refresh command based on current state

        Args:
            current_cycle: Current simulation cycle
            pending_high_priority: Number of pending high-priority requests

        Returns:
            RefreshCommand or None
        """
        self.current_cycle = current_cycle

        # Check if blocked by QoS
        if self.refresh_blocked_until > current_cycle:
            return None

        # Check if high-priority traffic should delay refresh
        if pending_high_priority > 0 and self.max_refresh_delay > 0:
            remaining_delay = self.refresh_blocked_until - current_cycle
            if remaining_delay < self.max_refresh_delay:
                return None

        cmd = self.get_refresh_command()
        if cmd is None:
            return None

        command_name, channel_id, pseudo_channel_id, bank_id = cmd

        return RefreshCommand(
            command_type=command_name,
            channel_id=channel_id,
            pseudo_channel_id=pseudo_channel_id,
            bank_id=bank_id,
            cycle=current_cycle,
            duration_cycles=self.tRFC,
            priority=RefreshPriority.NORMAL
        )

    def handle_row_hammer(self, channel_id: int, pseudo_channel_id: int,
                         bank_id: int, access_count: int) -> bool:
        """Handle row-hammer detection for a bank

        Args:
            channel_id: Channel index
            pseudo_channel_id: Pseudo-channel index
            bank_id: Bank index
            access_count: Number of activations to this bank

        Returns:
            True if refresh should be triggered for this bank
        """
        if not self.drfm_enabled:
            return False

        # Convert to global bank ID
        global_bank_id = (
            channel_id * self.spec.pseudo_channels_per_channel * self.spec.banks_per_pseudo_channel +
            pseudo_channel_id * self.spec.banks_per_pseudo_channel +
            bank_id
        )

        if 0 <= global_bank_id < len(self.bank_status):
            self.bank_status[global_bank_id].row_hammer_count = access_count

            # Trigger refresh if threshold exceeded
            if access_count >= self.drfm_rowhammer_threshold:
                self.bank_status[global_bank_id].needs_refresh = True
                return True

        return False

    def get_refresh_overhead(self, duration_cycles: int) -> float:
        """Calculate refresh overhead for a given duration

        Args:
            duration_cycles: Duration in cycles

        Returns:
            Refresh overhead ratio (0.0 - 1.0)
        """
        if duration_cycles <= 0:
            return 0.0

        return self.stats.total_refresh_cycles / duration_cycles

    def reset(self):
        """Reset scheduler state"""
        self.cycles_since_refresh = 0
        self.current_refresh_bank = 0
        self.current_refresh_pch = 0
        self.current_bank_group = 0
        self.total_refresh_count = 0
        self.current_cycle = 0
        self.refresh_in_progress = False
        self.refresh_blocked_until = 0
        self.blocked_by_qos = False
        self.drfm_rowhammer_victims.clear()

        for bs in self.bank_status:
            bs.last_refresh_cycle = 0
            bs.needs_refresh = False
            bs.row_hammer_count = 0

        self.stats = RefreshStatistics()


class RefreshSchedulerFactory:
    """Factory for creating refresh schedulers with different configurations"""

    @staticmethod
    def create_all_bank_scheduler(config: Optional[HBM4Spec] = None) -> HBM4RefreshScheduler:
        """Create scheduler configured for all-bank refresh mode

        Args:
            config: HBM4 specification

        Returns:
            HBM4RefreshScheduler in ALL_BANKS mode
        """
        scheduler = HBM4RefreshScheduler(config)
        scheduler.set_mode(RefreshMode.ALL_BANKS)
        return scheduler

    @staticmethod
    def create_per_bank_scheduler(config: Optional[HBM4Spec] = None) -> HBM4RefreshScheduler:
        """Create scheduler configured for per-bank refresh mode

        Args:
            config: HBM4 specification

        Returns:
            HBM4RefreshScheduler in PER_BANK mode
        """
        scheduler = HBM4RefreshScheduler(config)
        scheduler.set_mode(RefreshMode.PER_BANK)
        return scheduler

    @staticmethod
    def create_bank_group_scheduler(config: Optional[HBM4Spec] = None) -> HBM4RefreshScheduler:
        """Create scheduler configured for bank-group refresh mode

        Args:
            config: HBM4 specification

        Returns:
            HBM4RefreshScheduler in BANK_GROUP mode
        """
        scheduler = HBM4RefreshScheduler(config)
        scheduler.set_mode(RefreshMode.BANK_GROUP)
        return scheduler

    @staticmethod
    def create_drfm_scheduler(config: Optional[HBM4Spec] = None,
                             threshold: int = 1000) -> HBM4RefreshScheduler:
        """Create scheduler with DRFM enabled

        Args:
            config: HBM4 specification
            threshold: Row-hammer threshold

        Returns:
            HBM4RefreshScheduler with DRFM enabled
        """
        scheduler = HBM4RefreshScheduler(config)
        scheduler.set_mode(RefreshMode.PER_BANK)
        scheduler.enable_drfm(enabled=True, threshold=threshold)
        return scheduler