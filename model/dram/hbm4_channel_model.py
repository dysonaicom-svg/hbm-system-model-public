"""
HBM4 Channel Model

Implements 32 independent channels, each with 2 pseudo-channels.
Based on Ramulator 2.0 hierarchical node structure.

Key features:
- 32 independent memory channels
- 2 pseudo-channels per channel (64 total)
- Independent bank state machines per pseudo-channel
- Command scheduling and timing

Reference:
- Ramulator 2.0: src/dram/impl/HBM3.cpp
- DRAMSys: configs/memspec/HBM2.json
- JEDEC JESD270-4A HBM4 specification
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import time

from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
from model.dram.hbm4_spec import HBM4Spec


class HBM4ChannelState(Enum):
    """HBM4 Channel operational states"""
    IDLE = 0
    ACTIVE = 1
    REFRESHING = 2
    TRAINING = 3
    MAINTENANCE = 4


class PseudoChannelState(Enum):
    """Pseudo-channel operational states"""
    IDLE = 0
    ACTIVE = 1
    REFRESHING = 2
    READING = 3
    WRITING = 4


@dataclass
class PseudoChannel:
    """HBM4 Pseudo-Channel state

    Each physical channel has 2 pseudo-channels for doubled parallelism.
    Each pseudo-channel has its own bank state machines.

    Based on Ramulator 2.0 pseudochannel level.
    """
    channel_id: int
    pseudo_channel_id: int  # 0 or 1
    spec: HBM4Spec

    # Bank state machines (16 banks per pseudo-channel)
    banks: List[BankStateMachine]

    # State tracking
    state: PseudoChannelState = PseudoChannelState.IDLE
    open_row: int = -1
    current_time: float = 0.0

    def __init__(self, channel_id: int, pseudo_channel_id: int, spec: HBM4Spec):
        """Initialize pseudo-channel

        Args:
            channel_id: Channel this pseudo-channel belongs to
            pseudo_channel_id: Pseudo-channel index (0 or 1)
            spec: HBM4 specification
        """
        self.channel_id = channel_id
        self.pseudo_channel_id = pseudo_channel_id
        self.spec = spec

        # Create timing object for bank state machines
        from model.dram.timing import HBM3Timing
        timing = HBM3Timing()

        self.banks = [
            BankStateMachine(bank_id, timing)
            for bank_id in range(spec.banks_per_pseudo_channel)
        ]

    def activate_row(self, row: int) -> bool:
        """Activate a row in this pseudo-channel

        Args:
            row: Row number to activate

        Returns:
            True if activation succeeded
        """
        # Find an idle bank to activate
        for bank in self.banks:
            bank.set_time(self.current_time)
            if bank.can_activate():
                bank.activate(row)
                self.open_row = row
                self.state = PseudoChannelState.ACTIVE
                return True

        # All banks busy
        return False

    def is_row_open(self, row: int) -> bool:
        """Check if row is currently open in any bank

        Args:
            row: Row number to check

        Returns:
            True if row is open
        """
        return self.open_row == row

    def precharge_all(self) -> bool:
        """Precharge all banks in this pseudo-channel

        Returns:
            True if precharge succeeded
        """
        for bank in self.banks:
            bank.set_time(self.current_time)
            if bank.can_precharge():
                bank.precharge()

        self.open_row = -1
        self.state = PseudoChannelState.IDLE
        return True

    def can_read(self) -> bool:
        """Check if a read can be issued

        Returns:
            True if any bank can accept a read
        """
        for bank in self.banks:
            bank.set_time(self.current_time)
            if bank.can_read():
                return True
        return False

    def can_write(self) -> bool:
        """Check if a write can be issued

        Returns:
            True if any bank can accept a write
        """
        for bank in self.banks:
            bank.set_time(self.current_time)
            if bank.can_write():
                return True
        return False

    def refresh(self) -> bool:
        """Execute refresh on all banks

        Returns:
            True if refresh succeeded
        """
        all_idle = all(b.bank.state == BankStateEnum.IDLE for b in self.banks)
        if all_idle:
            for bank in self.banks:
                bank.refresh()
            self.state = PseudoChannelState.REFRESHING
            return True
        return False

    def tick(self):
        """Advance time for this pseudo-channel"""
        self.current_time += 1.0


class HBM4Channel:
    """HBM4 Channel Model

    Represents one of 32 independent memory channels in HBM4.
    Each channel has 2 pseudo-channels (64 total pseudo-channels).

    Reference: Ramulator 2.0 HBM3 channel node
    """

    # HBM4 commands (from JEDEC spec and Ramulator 2.0)
    COMMANDS = [
        'ACT', 'PRE', 'PREA',  # Row commands
        'RD', 'WR', 'RDA', 'WRA',  # Column commands (with auto-precharge)
        'REFab', 'REFsb',  # All-bank and per-bank refresh
        'RFMab', 'RFMsb'  # Row flash memory (refresh) commands
    ]

    def __init__(self, channel_id: int, spec: Optional[HBM4Spec] = None):
        """Initialize HBM4 channel

        Args:
            channel_id: Channel index (0-31)
            spec: HBM4 specification (uses default if None)
        """
        if spec is None:
            spec = HBM4Spec()

        self.channel_id = channel_id
        self.spec = spec
        self.current_cycle = 0

        # Create 2 pseudo-channels per channel
        self.pseudo_channels = [
            PseudoChannel(channel_id, pch_id, spec)
            for pch_id in range(2)
        ]

        # Channel-level state
        self.state = HBM4ChannelState.IDLE

    @property
    def peak_bandwidth_gbs(self) -> float:
        """Peak bandwidth per channel in GB/s

        Each channel has 64-bit @ 8 GT/s = 64 GB/s
        """
        return self.spec.data_rate_gtps * 64 / 8 / 1e9 * 1e9

    @property
    def peak_bandwidth_tbs(self) -> float:
        """Peak bandwidth per channel in TB/s"""
        return self.peak_bandwidth_gbs / 1000

    def issue_command(self, cmd: str, pseudo_channel: int,
                     bank: int, row: int, col: int = 0) -> bool:
        """Issue a command to this channel

        Args:
            cmd: Command name ('ACT', 'PRE', 'RD', 'WR', etc.)
            pseudo_channel: Pseudo-channel index (0 or 1)
            bank: Bank index (0-15)
            row: Row index
            col: Column index

        Returns:
            True if command succeeded
        """
        if pseudo_channel not in [0, 1]:
            return False

        if bank < 0 or bank >= self.spec.banks_per_pseudo_channel:
            return False

        pc = self.pseudo_channels[pseudo_channel]

        if cmd == 'ACT':
            result = pc.activate_row(row)
            if result:
                self.state = HBM4ChannelState.ACTIVE
            return result

        elif cmd in ['PRE', 'PREA']:
            pc.precharge_all()
            self.state = HBM4ChannelState.IDLE
            return True

        elif cmd in ['RD', 'RDA']:
            # Check if row is open, if not activate
            if not pc.is_row_open(row):
                pc.activate_row(row)
            pc.state = PseudoChannelState.READING
            return True

        elif cmd in ['WR', 'WRA']:
            # Check if row is open, if not activate
            if not pc.is_row_open(row):
                pc.activate_row(row)
            pc.state = PseudoChannelState.WRITING
            return True

        elif cmd in ['REFab', 'REFsb']:
            pc.state = PseudoChannelState.REFRESHING
            for b in pc.banks:
                b.refresh()
            self.state = HBM4ChannelState.REFRESHING
            return True

        elif cmd in ['RFMab', 'RFMsb']:
            # Row flash memory refresh
            pc.refresh()
            return True

        return False

    def tick(self):
        """Advance channel time by one cycle"""
        self.current_cycle += 1

        # Update all pseudo-channels
        for pc in self.pseudo_channels:
            pc.current_time = self.current_cycle
            pc.tick()

            # Update bank state machines
            for bank in pc.banks:
                bank.set_time(self.current_cycle)

            # Complete refresh operations
            if pc.state == PseudoChannelState.REFRESHING:
                for bank in pc.banks:
                    if bank.bank.state == BankStateEnum.REFRESHING:
                        bank.complete_refresh()
                pc.state = PseudoChannelState.IDLE
                self.state = HBM4ChannelState.IDLE

            # Complete read/write operations
            if pc.state in [PseudoChannelState.READING, PseudoChannelState.WRITING]:
                pc.state = PseudoChannelState.ACTIVE

    def get_bank(self, pseudo_channel: int, bank: int) -> Optional[BankStateMachine]:
        """Get a specific bank state machine

        Args:
            pseudo_channel: Pseudo-channel index (0 or 1)
            bank: Bank index (0-15)

        Returns:
            BankStateMachine or None if invalid indices
        """
        if pseudo_channel not in [0, 1]:
            return None
        if bank < 0 or bank >= len(self.pseudo_channels[pseudo_channel].banks):
            return None

        return self.pseudo_channels[pseudo_channel].banks[bank]

    def is_row_hit(self, pseudo_channel: int, row: int) -> bool:
        """Check if row is currently open

        Args:
            pseudo_channel: Pseudo-channel index
            row: Row number

        Returns:
            True if row is open
        """
        if pseudo_channel not in [0, 1]:
            return False
        return self.pseudo_channels[pseudo_channel].is_row_open(row)

    def get_state_summary(self) -> dict:
        """Get channel state summary

        Returns:
            Dictionary with state information
        """
        return {
            'channel_id': self.channel_id,
            'state': self.state.name,
            'pseudo_channels': [
                {
                    'id': pc.pseudo_channel_id,
                    'state': pc.state.name,
                    'open_row': pc.open_row,
                    'active_banks': sum(1 for b in pc.banks if b.bank.state == BankStateEnum.ACTIVE)
                }
                for pc in self.pseudo_channels
            ],
            'current_cycle': self.current_cycle
        }