"""
HBM4 DRAM Bank State Machine - Unified Implementation

This module provides HBM4-specific exports from the unified bank_state_machine module.
All HBM4 functionality has been merged into model.dram.bank_state_machine.

For new code, use:
    from model.dram.bank_state_machine import (
        BankStateMachine,
        BankStateEnum,
        BankArray,
        create_bank_state_machine,
        create_bank_array,
    )

This module is kept for backward compatibility and exports aliases for:
- HBM4BankState (alias for BankStateEnum with HBM4 extended states)
- HBM4Command (command encoding)
- HBM4BankTiming (timing parameters)
- HBM4BankStateMachine (alias for BankStateMachine in HBM4 mode)
- HBM4BankArray (alias for BankArray)

Reference:
- JEDEC JESD270-4A HBM4 specification
- Ramulator 2.0 HBM3 implementation
"""

# Re-export from unified implementation
from model.dram.bank_state_machine import (
    BankStateMachine,
    BankStateEnum,
    BankArray,
    TimingViolation,
    create_bank_state_machine,
    create_bank_array,
    batch_check_can_activate,
    batch_check_can_read,
    batch_check_can_write,
)

# HBM4-specific imports from timing module
from model.dram.timing import HBM4TimingSource, HBM4_TIMING as UNIFIED_TIMING

# Backward compatibility: re-export as HBM4 names
HBM4BankState = BankStateEnum
HBM4BankStateMachine = BankStateMachine
HBM4BankArray = BankArray


class HBM4Command:
    """HBM4 Command encoding for compatibility"""
    NOP = 0
    ACT = 1      # Activate
    READ = 2     # Read
    WRITE = 3    # Write
    PRE = 4      # Precharge single bank
    PREA = 5     # Precharge all
    REF = 6      # Refresh
    RFM = 7      # Row flash memory


class HBM4BankTiming:
    """HBM4 timing parameters - uses unified timing source

    This class is provided for backward compatibility.
    New code should use HBM4Timing or HBM4TimingSource directly.
    """

    # Map t-prefix names to n-prefix names
    _ATTR_MAP = {
        'tRCD': 'nRCD', 'tRP': 'nRP', 'tRAS': 'nRAS', 'tRC': 'nRC',
        'tCL': 'nCL', 'tCWL': 'nCWL', 'tCCD': 'nCCD',
        'tCCDS': 'nCCDS', 'tCCDL': 'nCCDL',
        'tRRD': 'nRRD', 'tRRDS': 'nRRDS', 'tRRDL': 'nRRDL',
        'tFAW': 'nFAW', 'tWTRS': 'nWTRS', 'tWTRL': 'nWTRL',
        'tRTW': 'nRTW', 'tRFC': 'nRFC', 'tREFI': 'nREFI',
        'tBL': 'nBL',
    }

    def __init__(self, speed_gbps: float = 8.0):
        """Create HBM4 timing for specific speed grade

        Args:
            speed_gbps: Data rate in GT/s
        """
        self.tCK_ps = 1000.0 / speed_gbps
        # Delegate to unified timing source
        self._source = UNIFIED_TIMING

    def __getattr__(self, name: str):
        """Delegate to unified timing source with name mapping"""
        # Check if we need to map t-prefix to n-prefix
        if name in self._ATTR_MAP:
            return getattr(self._source, self._ATTR_MAP[name])
        # Try direct access
        try:
            return getattr(self._source, name)
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @property
    def clock_period_ns(self) -> float:
        """Clock period in nanoseconds"""
        return self.tCK_ps / 1000.0

    def cycles_to_ns(self, cycles: int) -> float:
        """Convert cycles to nanoseconds"""
        return cycles * self.clock_period_ns

    def cycles_to_seconds(self, cycles: int) -> float:
        """Convert cycles to seconds"""
        return cycles * self.tCK_ps * 1e-12

    @classmethod
    def for_speed_grade(cls, speed_gbps: float) -> 'HBM4BankTiming':
        """Create timing for specific speed grade

        Args:
            speed_gbps: Data rate in GT/s

        Returns:
            HBM4BankTiming configured for the speed grade
        """
        return cls(speed_gbps=speed_gbps)


def create_hbm4_bank_state_machine(bank_id: int, timing=None,
                                    channel_id: int = 0, pseudo_channel_id: int = 0,
                                    bank_group_id: int = 0) -> BankStateMachine:
    """Factory function to create HBM4 bank state machine

    Args:
        bank_id: Bank index within pseudo-channel (0-15)
        timing: Timing parameters (uses HBM4 defaults if None)
        channel_id: Channel index (0-31)
        pseudo_channel_id: Pseudo-channel index (0-1)
        bank_group_id: Bank group index (0-7)

    Returns:
        BankStateMachine instance configured for HBM4
    """
    if timing is None:
        timing = HBM4_TIMING
    return create_bank_state_machine(
        bank_id=bank_id,
        timing=timing,
        channel_id=channel_id,
        pseudo_channel_id=pseudo_channel_id,
        bank_group_id=bank_group_id
    )


def create_hbm4_bank_array(pseudo_channel_id: int = 0, channel_id: int = 0,
                            timing=None, num_banks: int = 16) -> BankArray:
    """Factory function to create HBM4 bank array for a pseudo-channel

    Args:
        pseudo_channel_id: Pseudo-channel index (0-1)
        channel_id: Channel index (0-31)
        timing: Timing parameters (uses HBM4 defaults if None)
        num_banks: Number of banks (default 16)

    Returns:
        BankArray with HBM4 configured banks
    """
    if timing is None:
        timing = HBM4_TIMING
    return create_bank_array(
        num_banks=num_banks,
        timing=timing,
        channel_id=channel_id,
        pseudo_channel_id=pseudo_channel_id
    )


# HBM4-specific timing constants (for compatibility)
BANK_TIMING = {
    'tRCD': UNIFIED_TIMING.nRCD,
    'tRP': UNIFIED_TIMING.nRP,
    'tRAS': UNIFIED_TIMING.nRAS,
    'tRC': UNIFIED_TIMING.nRC,
    'tCL': UNIFIED_TIMING.nCL,
    'tCWL': UNIFIED_TIMING.nCWL,
    'tCCD': UNIFIED_TIMING.nCCD,
    'tCCDS': UNIFIED_TIMING.nCCDS,
    'tCCDL': UNIFIED_TIMING.nCCDL,
    'tRRD': UNIFIED_TIMING.nRRD,
    'tRRDS': UNIFIED_TIMING.nRRDS,
    'tRRDL': UNIFIED_TIMING.nRRDL,
    'tFAW': UNIFIED_TIMING.nFAW,
    'tWTRS': UNIFIED_TIMING.nWTRS,
    'tWTRL': UNIFIED_TIMING.nWTRL,
    'tRTW': UNIFIED_TIMING.nRTW,
    'tRFC': UNIFIED_TIMING.nRFC,
    'tREFI': UNIFIED_TIMING.nREFI,
}


# Aliases for direct compatibility
HBM4Bank = None  # Deprecated: use BankStateMachine.bank directly


__all__ = [
    # Unified classes
    'BankStateMachine',
    'BankStateEnum',
    'BankArray',
    'TimingViolation',

    # HBM4 aliases
    'HBM4BankState',
    'HBM4BankStateMachine',
    'HBM4BankArray',
    'HBM4Command',
    'HBM4BankTiming',

    # Timing
    'HBM4TimingSource',
    'UNIFIED_TIMING',
    'BANK_TIMING',

    # Factory functions
    'create_bank_state_machine',
    'create_bank_array',
    'create_hbm4_bank_state_machine',
    'create_hbm4_bank_array',

    # Batch operations
    'batch_check_can_activate',
    'batch_check_can_read',
    'batch_check_can_write',
]
