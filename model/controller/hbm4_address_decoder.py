"""
HBM4 Address Decoder

Extends the base AddressDecoder for HBM4-specific 32-channel architecture.

Key differences from HBM3:
- 32 channels (5-bit channel field vs 3-bit in HBM3)
- 64 pseudo-channels (1-bit pseudo-channel field)
- Extended address space for 2 TB/s bandwidth
- Additional address bits for larger capacity

Based on:
- JEDEC JESD270-4A HBM4 specification
- Multi-agent research findings (2026-06-15)
"""

from typing import Dict, Optional
from model.controller.address_decoder import AddressDecoder, DecodedAddress
from model.dram.hbm4_spec import HBM4Spec
from model.controller.config import HBMConfig


class HBM4AddressDecoder(AddressDecoder):
    """HBM4-specific address decoder

    Key differences from HBM3:
    - 32 channels (5 bits vs 3 bits)
    - 64 pseudo-channels (1 bit)
    - 16 bank groups (3 bits)
    - 16 banks per group (4 bits)
    - 64K rows (16 bits)

    HBM4 address mapping:
        Addr[47:46] = Stack ID (2-bit, supports 4 stacks)
        Addr[45:41] = Channel (5-bit, 32 channels)
        Addr[40]    = Pseudo-channel (1-bit, 2 pseudo-channels)
        Addr[39:37] = Bank group (3-bit, 8 bank groups)
        Addr[36:33] = Bank within group (4-bit, 16 banks)
        Addr[32:17] = Row (16-bit, 64K rows)
        Addr[16:3]  = Column (14-bit)
        Addr[2:0]   = Byte offset (8-byte granularity)
    """

    # HBM4 address bit field configuration (different from HBM3)
    CHANNEL_BITS = 5      # 32 channels
    PCH_BITS = 1          # 2 pseudo-channels per channel
    BG_BITS = 3           # 8 bank groups
    BANK_BITS = 4         # 16 banks per group
    ROW_BITS = 16         # 64K rows
    COL_BITS = 14         # 64 columns (expanded for HBM4)
    STACK_BITS = 2        # 4 stacks
    BURST_BITS = 3        # 8-byte burst alignment

    # Total address bits for HBM4
    TOTAL_ADDR_BITS = STACK_BITS + CHANNEL_BITS + PCH_BITS + BG_BITS + BANK_BITS + ROW_BITS + COL_BITS + BURST_BITS

    def __init__(self, spec: Optional[HBM4Spec] = None, mapping_scheme: str = "rbc"):
        """Initialize HBM4 address decoder

        Args:
            spec: HBM4 specification (uses default if None)
            mapping_scheme: Address mapping scheme ("rbc", "bcr", "crb", "hbm4")
        """
        if spec is None:
            spec = HBM4Spec()

        self.spec = spec
        self._mapping_scheme = mapping_scheme  # Store original string

        # Create a minimal HBMConfig for base class
        config = HBMConfig(
            stack_count=2**spec.ADDR_STACK_BITS,
            channels_per_stack=spec.channels,
            pseudo_channels_per_channel=spec.pseudo_channels_per_channel,
            bank_groups_per_channel=spec.bank_groups_per_channel,
            banks_per_pseudo_channel=spec.banks_per_pseudo_channel,
            io_width=spec.io_width,
            address_mapping=mapping_scheme,
        )

        # Get mapping based on scheme
        mapping = self._get_hbm4_mapping(mapping_scheme)

        super().__init__(config, custom_mapping=mapping)

    def _get_hbm4_mapping(self, mapping_scheme: str) -> Dict:
        """Get HBM4-specific address mapping

        Args:
            mapping_scheme: Mapping scheme name

        Returns:
            Dictionary mapping field names to (msb, lsb, bits) tuples
        """
        if mapping_scheme == "hbm4" or mapping_scheme == "rbc":
            # HBM4 default: Row-Bank-Channel (optimized for sequential access)
            # Channel bits: 45-41 (5 bits for 32 channels)
            return {
                'stack': (47, 46, 2),
                'channel': (45, 41, 5),      # 32 channels
                'pseudo_channel': (40, 40, 1),  # 2 pseudo-channels
                'bank_group': (39, 37, 3),     # 8 bank groups
                'bank': (36, 33, 4),           # 16 banks
                'row': (32, 17, 16),           # 64K rows
                'col': (16, 3, 14),            # 64 columns
                'offset': (2, 0, 3),           # 8-byte alignment
            }
        elif mapping_scheme == "bcr":
            # Bank-Channel-Row (maximizes parallelism)
            return {
                'stack': (47, 46, 2),
                'bank_group': (45, 43, 3),
                'bank': (42, 39, 4),
                'channel': (38, 34, 5),       # 32 channels
                'pseudo_channel': (33, 33, 1),
                'row': (32, 17, 16),
                'col': (16, 3, 14),
                'offset': (2, 0, 3),
            }
        elif mapping_scheme == "crb":
            # Channel-Row-Bank (optimized for cross-channel random access)
            return {
                'channel': (47, 43, 5),        # 32 channels at top
                'stack': (42, 41, 2),
                'pseudo_channel': (40, 40, 1),
                'bank_group': (39, 37, 3),
                'bank': (36, 33, 4),
                'row': (32, 17, 16),
                'col': (16, 3, 14),
                'offset': (2, 0, 3),
            }
        else:
            return self._get_hbm4_mapping("hbm4")

    def decode(self, addr: int) -> DecodedAddress:
        """Decode HBM4 address into components

        Args:
            addr: 64-bit physical address

        Returns:
            DecodedAddress with all fields populated
        """
        # Use base class decode method
        result = super().decode(addr)

        # Ensure 8-byte alignment
        if addr & 0x7:
            # Shift addr right to align, then decode
            aligned_addr = addr & ~0x7
            result = super().decode(aligned_addr)

        return result

    def get_channel_id(self, addr: int) -> int:
        """Extract channel ID from address

        Args:
            addr: 64-bit address

        Returns:
            Channel ID (0-31)
        """
        # Channel bit position depends on mapping scheme
        mapping = self._get_hbm4_mapping(self._mapping_scheme)
        ch_msb, ch_lsb, _ = mapping['channel']
        return (addr >> ch_lsb) & ((1 << (ch_msb - ch_lsb + 1)) - 1)

    def get_pseudo_channel_id(self, addr: int) -> int:
        """Extract pseudo-channel ID from address

        Args:
            addr: 64-bit address

        Returns:
            Pseudo-channel ID (0-1)
        """
        # Pseudo-channel is bit 40
        return (addr >> 40) & 0x1

    def get_row_id(self, addr: int) -> int:
        """Extract row ID from address

        Args:
            addr: 64-bit address

        Returns:
            Row ID (0-65535)
        """
        # Row is bits 32:17
        return (addr >> 17) & 0xFFFF

    def get_bank_id(self, addr: int) -> int:
        """Extract bank ID from address

        Args:
            addr: 64-bit address

        Returns:
            Bank ID (0-15)
        """
        # Bank is bits 36:33
        return (addr >> 33) & 0xF

    def get_bank_group_id(self, addr: int) -> int:
        """Extract bank group ID from address

        Args:
            addr: 64-bit address

        Returns:
            Bank group ID (0-7)
        """
        # Bank group is bits 39:37
        return (addr >> 37) & 0x7