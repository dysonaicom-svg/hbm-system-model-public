"""
HBM4 Address Pattern Generator

Enhanced address pattern generation with full HBM4 32-channel awareness.
Supports multiple address patterns including sequential, random, stride,
hotspot, neighbor, and HBM4-aware channel interleaving.

Features:
- HBM4 32-channel address mapping
- Bank, row, column distribution patterns
- Channel/pseudo-channel aware interleaving
- Stride patterns (1KB, 4KB, 64KB aligned)
- Hotspot address distribution (80/20 rule)
- Neighbor clustering

Reference:
- JEDEC JESD270-4A HBM4 specification
- HBM4 32-channel architecture
"""

import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Iterator, Dict, Callable
from enum import IntEnum

from model.dram.HBM4_spec import HBM4Spec


class AddressPattern(IntEnum):
    """Address pattern types"""
    SEQUENTIAL = 1
    RANDOM = 2
    STRIDE_1KB = 3
    STRIDE_4KB = 4
    STRIDE_64KB = 5
    STRIDE_PAGE = 6
    HOTSPOT = 7
    NEIGHBOR = 8
    BANK_ROUND_ROBIN = 9
    CHANNEL_INTERLEAVE = 10
    ROW_PATTERN = 11
    COLUMN_PATTERN = 12
    CUSTOM = 99


class ChannelMapping(IntEnum):
    """Channel mapping strategies"""
    LINEAR = 1           # Linear sequential channel assignment
    INTERLEAVE_2 = 2     # 2-channel interleaving
    INTERLEAVE_4 = 3     # 4-channel interleaving
    INTERLEAVE_8 = 4     # 8-channel interleaving
    INTERLEAVE_16 = 5    # 16-channel interleaving
    INTERLEAVE_32 = 6    # Full 32-channel interleaving
    HASH_BASED = 7       # Hash-based channel mapping


@dataclass
class HBM4AddressBits:
    """HBM4 address field extraction and composition
    
    Address format: [Stack][Channel][Pch][Bg][Bank][Row][Col][Burst]
    Based on HBM4 spec with 32 channels and 64 pseudo-channels.
    """
    # Address field bit positions and widths
    STACK_SHIFT: int = 0
    STACK_BITS: int = 2
    
    CHANNEL_SHIFT: int = 2
    CHANNEL_BITS: int = 5      # 32 channels
    
    PCH_SHIFT: int = 7
    PCH_BITS: int = 1          # 2 pseudo-channels per channel
    
    BG_SHIFT: int = 8
    BG_BITS: int = 3           # 8 bank groups
    
    BANK_SHIFT: int = 11
    BANK_BITS: int = 4         # 16 banks
    
    ROW_SHIFT: int = 15
    ROW_BITS: int = 19        # 512K rows
    
    COL_SHIFT: int = 34
    COL_BITS: int = 6         # 64 columns
    
    BURST_SHIFT: int = 40
    BURST_BITS: int = 2       # 4-beat burst alignment
    
    # Masks
    STACK_MASK: int = ((1 << STACK_BITS) - 1) << STACK_SHIFT
    CHANNEL_MASK: int = ((1 << CHANNEL_BITS) - 1) << CHANNEL_SHIFT
    PCH_MASK: int = ((1 << PCH_BITS) - 1) << PCH_SHIFT
    BG_MASK: int = ((1 << BG_BITS) - 1) << BG_SHIFT
    BANK_MASK: int = ((1 << BANK_BITS) - 1) << BANK_SHIFT
    ROW_MASK: int = ((1 << ROW_BITS) - 1) << ROW_SHIFT
    COL_MASK: int = ((1 << COL_BITS) - 1) << COL_SHIFT
    BURST_MASK: int = ((1 << BURST_BITS) - 1) << BURST_SHIFT
    
    @classmethod
    def decode(cls, addr: int) -> Dict[str, int]:
        """Decode address into HBM4 fields
        
        Args:
            addr: 64-bit memory address
            
        Returns:
            Dictionary with decoded fields
        """
        return {
            'stack': (addr & cls.STACK_MASK) >> cls.STACK_SHIFT,
            'channel': (addr & cls.CHANNEL_MASK) >> cls.CHANNEL_SHIFT,
            'pseudo_channel': (addr & cls.PCH_MASK) >> cls.PCH_SHIFT,
            'bank_group': (addr & cls.BG_MASK) >> cls.BG_SHIFT,
            'bank': (addr & cls.BANK_MASK) >> cls.BANK_SHIFT,
            'row': (addr & cls.ROW_MASK) >> cls.ROW_SHIFT,
            'column': (addr & cls.COL_MASK) >> cls.COL_SHIFT,
            'burst': (addr & cls.BURST_MASK) >> cls.BURST_SHIFT,
        }
    
    @classmethod
    def encode(cls,
               stack: int = 0,
               channel: int = 0,
               pseudo_channel: int = 0,
               bank_group: int = 0,
               bank: int = 0,
               row: int = 0,
               column: int = 0,
               burst: int = 0) -> int:
        """Encode HBM4 fields into address
        
        Args:
            stack: Stack ID (0-3)
            channel: Channel ID (0-31)
            pseudo_channel: Pseudo-channel ID (0-1)
            bank_group: Bank group ID (0-7)
            bank: Bank ID (0-15)
            row: Row ID (0-524287)
            column: Column ID (0-63)
            burst: Burst offset (0-3)
            
        Returns:
            64-bit address
        """
        addr = 0
        addr |= (stack & ((1 << cls.STACK_BITS) - 1)) << cls.STACK_SHIFT
        addr |= (channel & ((1 << cls.CHANNEL_BITS) - 1)) << cls.CHANNEL_SHIFT
        addr |= (pseudo_channel & ((1 << cls.PCH_BITS) - 1)) << cls.PCH_SHIFT
        addr |= (bank_group & ((1 << cls.BG_BITS) - 1)) << cls.BG_SHIFT
        addr |= (bank & ((1 << cls.BANK_BITS) - 1)) << cls.BANK_SHIFT
        addr |= (row & ((1 << cls.ROW_BITS) - 1)) << cls.ROW_SHIFT
        addr |= (column & ((1 << cls.COL_BITS) - 1)) << cls.COL_SHIFT
        addr |= (burst & ((1 << cls.BURST_BITS) - 1)) << cls.BURST_SHIFT
        return addr
    
    @classmethod
    def get_channel(cls, addr: int) -> int:
        """Extract channel from address"""
        return (addr & cls.CHANNEL_MASK) >> cls.CHANNEL_SHIFT
    
    @classmethod
    def get_pseudo_channel(cls, addr: int) -> int:
        """Extract pseudo-channel from address"""
        return (addr & cls.PCH_MASK) >> cls.PCH_SHIFT
    
    @classmethod
    def get_bank(cls, addr: int) -> int:
        """Extract bank from address"""
        return (addr & cls.BANK_MASK) >> cls.BANK_SHIFT
    
    @classmethod
    def get_row(cls, addr: int) -> int:
        """Extract row from address"""
        return (addr & cls.ROW_MASK) >> cls.ROW_SHIFT
    
    @classmethod
    def get_column(cls, addr: int) -> int:
        """Extract column from address"""
        return (addr & cls.COL_MASK) >> cls.COL_SHIFT


@dataclass
class AddressPatternConfig:
    """Configuration for address pattern generation"""
    # Base address settings
    base_address: int = 0x100000000
    address_range: int = 0x10000000000  # 256 GB range
    
    # HBM4 configuration
    channels: int = 32
    pseudo_channels: int = 64
    banks_per_pseudo_channel: int = 16
    
    # Pattern-specific settings
    stride: int = 64  # bytes
    
    # Channel mapping strategy
    channel_mapping: ChannelMapping = ChannelMapping.LINEAR
    
    # Hotspot configuration (80/20 rule)
    hotspot_ratio: float = 0.2  # 20% of addresses get 80% of traffic
    hotspot_window_size: int = 1024  # bytes
    
    # Neighbor clustering
    neighbor_distance: int = 64  # bytes
    
    # Random seed for reproducibility
    seed: Optional[int] = None
    
    def __post_init__(self):
        """Validate configuration"""
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)


class AddressPatternGenerator:
    """HBM4-aware Address Pattern Generator
    
    Generates addresses according to specific patterns with full awareness
    of HBM4's 32-channel architecture.
    
    Features:
    - Sequential: Consecutive addresses within channel
    - Random: Uniform random across address space
    - Stride: Fixed stride patterns (1KB, 4KB, 64KB)
    - Hotspot: 80/20 distribution (20% addresses = 80% traffic)
    - Neighbor: Adjacent address clustering
    - Channel interleaving: Round-robin across channels
    - Bank-level distribution
    
    Example:
        >>> config = AddressPatternConfig()
        >>> gen = AddressPatternGenerator(config)
        >>> gen.set_pattern(AddressPattern.RANDOM)
        >>> addrs = gen.next_batch(100)
        >>> decoded = gen.decode_batch(addrs)
    """
    
    def __init__(self, config: Optional[AddressPatternConfig] = None):
        """Initialize address pattern generator
        
        Args:
            config: Address pattern configuration
        """
        self.config = config if config else AddressPatternConfig()
        self.hbm_spec = HBM4Spec()
        self.addr_bits = HBM4AddressBits()
        
        # Pattern state
        self._current_pattern: AddressPattern = AddressPattern.SEQUENTIAL
        self._current_addr: int = 0
        self._current_channel: int = 0
        self._current_bank: int = 0
        self._current_row: int = 0
        self._current_col: int = 0
        self._current_pseudo_channel: int = 0
        
        # Hotspot state
        self._hotspot_centers: List[int] = []
        self._hotspot_index: int = 0
        
        # Custom sequence
        self._custom_sequence: List[int] = []
        self._sequence_index: int = 0
        
        # Statistics
        self._stats = {
            'total_addresses': 0,
            'channel_distribution': {i: 0 for i in range(32)},
            'bank_distribution': {i: 0 for i in range(16)},
        }
        
        # Initialize hotspot centers
        self._init_hotspot_centers()
    
    def _init_hotspot_centers(self):
        """Initialize hotspot center addresses"""
        num_hotspots = max(1, int(self.config.channels * 0.2))  # ~20% of channels
        self._hotspot_centers = []
        
        for i in range(num_hotspots):
            channel = i % self.config.channels
            bank = random.randint(0, self.config.banks_per_pseudo_channel - 1)
            row = random.randint(0, 1023)  # First 1K rows as hotspots
            addr = self.addr_bits.encode(
                channel=channel,
                pseudo_channel=0,
                bank=bank,
                row=row,
                column=0,
                burst=0
            )
            self._hotspot_centers.append(addr)
    
    def set_pattern(self, pattern: AddressPattern):
        """Set address pattern
        
        Args:
            pattern: Address pattern to use
        """
        self._current_pattern = pattern
        self.reset()
    
    def reset(self):
        """Reset generator state"""
        self._current_addr = self.config.base_address
        self._current_channel = 0
        self._current_bank = 0
        self._current_row = 0
        self._current_col = 0
        self._current_pseudo_channel = 0
        self._hotspot_index = 0
        self._sequence_index = 0
    
    def set_custom_sequence(self, addresses: List[int]):
        """Set custom address sequence
        
        Args:
            addresses: List of addresses to generate in order
        """
        self._custom_sequence = addresses
        self._sequence_index = 0
        self._current_pattern = AddressPattern.CUSTOM
    
    def next(self) -> int:
        """Get next address
        
        Returns:
            Next address in pattern
        """
        if self._current_pattern == AddressPattern.SEQUENTIAL:
            addr = self._next_sequential()
        elif self._current_pattern == AddressPattern.RANDOM:
            addr = self._next_random()
        elif self._current_pattern == AddressPattern.STRIDE_1KB:
            addr = self._next_stride(1024)
        elif self._current_pattern == AddressPattern.STRIDE_4KB:
            addr = self._next_stride(4096)
        elif self._current_pattern == AddressPattern.STRIDE_64KB:
            addr = self._next_stride(65536)
        elif self._current_pattern == AddressPattern.STRIDE_PAGE:
            addr = self._next_stride(self.hbm_spec.row_size)
        elif self._current_pattern == AddressPattern.HOTSPOT:
            addr = self._next_hotspot()
        elif self._current_pattern == AddressPattern.NEIGHBOR:
            addr = self._next_neighbor()
        elif self._current_pattern == AddressPattern.BANK_ROUND_ROBIN:
            addr = self._next_bank_round_robin()
        elif self._current_pattern == AddressPattern.CHANNEL_INTERLEAVE:
            addr = self._next_channel_interleave()
        elif self._current_pattern == AddressPattern.ROW_PATTERN:
            addr = self._next_row_pattern()
        elif self._current_pattern == AddressPattern.COLUMN_PATTERN:
            addr = self._next_column_pattern()
        elif self._current_pattern == AddressPattern.CUSTOM:
            addr = self._next_custom()
        else:
            addr = self._next_sequential()
        
        self._update_stats(addr)
        return addr
    
    def next_batch(self, count: int) -> List[int]:
        """Get next batch of addresses
        
        Args:
            count: Number of addresses to generate
            
        Returns:
            List of addresses
        """
        return [self.next() for _ in range(count)]
    
    def _next_sequential(self) -> int:
        """Generate sequential addresses"""
        addr = self._current_addr
        self._current_addr = (self._current_addr + self.config.stride) % self.config.address_range
        if self._current_addr == 0:
            self._current_addr = self.config.base_address
        return addr
    
    def _next_random(self) -> int:
        """Generate random addresses"""
        offset = random.randint(0, self.config.address_range - 1)
        return self.config.base_address + offset
    
    def _next_stride(self, stride: int) -> int:
        """Generate strided addresses
        
        Args:
            stride: Stride in bytes
        """
        addr = self._current_addr
        self._current_addr = (self._current_addr + stride) % self.config.address_range
        if self._current_addr == 0:
            self._current_addr = self.config.base_address
        return addr
    
    def _next_hotspot(self) -> int:
        """Generate hotspot addresses (80/20 rule)
        
        20% of addresses receive 80% of traffic.
        """
        # 80% chance to access hotspot, 20% random
        if random.random() < 0.8:
            # Access hotspot center
            center = self._hotspot_centers[self._hotspot_index % len(self._hotspot_centers)]
            self._hotspot_index += 1
            # Add small offset around hotspot
            offset = random.randint(0, self.config.hotspot_window_size - 1)
            addr = center + offset
        else:
            # Random access
            addr = self._next_random()
        
        return addr
    
    def _next_neighbor(self) -> int:
        """Generate neighbor-clustered addresses
        
        Consecutive addresses are clustered near each other.
        """
        # With 90% probability, stay close to current address
        if random.random() < 0.9:
            offset = random.randint(-self.config.neighbor_distance,
                                   self.config.neighbor_distance)
            addr = self._current_addr + offset
            # Wrap around within range
            addr = self.config.base_address + (addr % self.config.address_range)
        else:
            # Jump to new region
            addr = self._next_random()
        
        self._current_addr = addr
        return addr
    
    def _next_bank_round_robin(self) -> int:
        """Generate addresses with bank-level round-robin"""
        bank = self._current_bank % self.config.banks_per_pseudo_channel
        channel = self._current_channel % self.config.channels
        
        addr = self.addr_bits.encode(
            channel=channel,
            pseudo_channel=0,
            bank=bank,
            row=self._current_row,
            column=0,
            burst=0
        )
        
        self._current_bank += 1
        if self._current_bank >= self.config.banks_per_pseudo_channel:
            self._current_bank = 0
            self._current_row += 1
        
        return addr
    
    def _next_channel_interleave(self) -> int:
        """Generate addresses with channel interleaving"""
        interleave_factor = self._get_interleave_factor()
        
        # Current position within interleave block
        position = self._current_addr % interleave_factor
        channel = position % self.config.channels
        
        addr = self.addr_bits.encode(
            channel=channel,
            pseudo_channel=self._current_pseudo_channel,
            bank=self._current_bank,
            row=self._current_row,
            column=self._current_col,
            burst=0
        )
        
        self._current_addr += 1
        self._current_col += 1
        if self._current_col >= 64:
            self._current_col = 0
            self._current_bank += 1
            if self._current_bank >= self.config.banks_per_pseudo_channel:
                self._current_bank = 0
                self._current_row += 1
        
        return addr
    
    def _get_interleave_factor(self) -> int:
        """Get interleave factor based on channel mapping"""
        mapping = self.config.channel_mapping
        if mapping == ChannelMapping.INTERLEAVE_2:
            return 2
        elif mapping == ChannelMapping.INTERLEAVE_4:
            return 4
        elif mapping == ChannelMapping.INTERLEAVE_8:
            return 8
        elif mapping == ChannelMapping.INTERLEAVE_16:
            return 16
        elif mapping == ChannelMapping.INTERLEAVE_32:
            return 32
        elif mapping == ChannelMapping.HASH_BASED:
            return 32  # Hash-based uses full channel space
        else:
            return 1
    
    def _next_row_pattern(self) -> int:
        """Generate row-pattern addresses (row hammer style)
        
        Alternates between first and last rows to maximize bank activation.
        """
        # Toggle between row 0 and max row
        row = 0 if (self._current_row % 2 == 0) else (1 << self.addr_bits.ROW_BITS) - 1
        
        addr = self.addr_bits.encode(
            channel=self._current_channel,
            pseudo_channel=self._current_pseudo_channel,
            bank=self._current_bank,
            row=row,
            column=self._current_col,
            burst=0
        )
        
        self._current_row += 1
        self._current_col += 1
        if self._current_col >= 64:
            self._current_col = 0
            self._current_bank += 1
            if self._current_bank >= self.config.banks_per_pseudo_channel:
                self._current_bank = 0
        
        return addr
    
    def _next_column_pattern(self) -> int:
        """Generate column-pattern addresses
        
        Sequential column access within a bank.
        """
        addr = self.addr_bits.encode(
            channel=self._current_channel,
            pseudo_channel=self._current_pseudo_channel,
            bank=self._current_bank,
            row=self._current_row,
            column=self._current_col,
            burst=0
        )
        
        self._current_col += 1
        if self._current_col >= 64:
            self._current_col = 0
            self._current_bank += 1
            if self._current_bank >= self.config.banks_per_pseudo_channel:
                self._current_bank = 0
                self._current_row += 1
        
        return addr
    
    def _next_custom(self) -> int:
        """Generate addresses from custom sequence"""
        if self._sequence_index >= len(self._custom_sequence):
            self._sequence_index = 0
        
        addr = self._custom_sequence[self._sequence_index]
        self._sequence_index += 1
        return addr
    
    def _update_stats(self, addr: int):
        """Update statistics
        
        Args:
            addr: Generated address
        """
        self._stats['total_addresses'] += 1
        channel = self.addr_bits.get_channel(addr)
        bank = self.addr_bits.get_bank(addr)
        
        if channel in self._stats['channel_distribution']:
            self._stats['channel_distribution'][channel] += 1
        if bank in self._stats['bank_distribution']:
            self._stats['bank_distribution'][bank] += 1
    
    def decode(self, addr: int) -> Dict[str, int]:
        """Decode single address
        
        Args:
            addr: Address to decode
            
        Returns:
            Dictionary with decoded fields
        """
        return self.addr_bits.decode(addr)
    
    def decode_batch(self, addresses: List[int]) -> List[Dict[str, int]]:
        """Decode batch of addresses
        
        Args:
            addresses: List of addresses to decode
            
        Returns:
            List of decoded field dictionaries
        """
        return [self.decode(addr) for addr in addresses]
    
    def get_channel_distribution(self) -> Dict[int, int]:
        """Get channel distribution of generated addresses
        
        Returns:
            Dictionary mapping channel ID to access count
        """
        return dict(self._stats['channel_distribution'])
    
    def get_bank_distribution(self) -> Dict[int, int]:
        """Get bank distribution of generated addresses
        
        Returns:
            Dictionary mapping bank ID to access count
        """
        return dict(self._stats['bank_distribution'])
    
    def get_stats(self) -> Dict:
        """Get generator statistics
        
        Returns:
            Statistics dictionary
        """
        total = self._stats['total_addresses']
        stats = {
            'total_addresses': total,
            'pattern': self._current_pattern.name,
        }
        
        if total > 0:
            # Channel distribution
            max_channel = max(self._stats['channel_distribution'].values()) if total > 0 else 1
            min_channel = min(self._stats['channel_distribution'].values()) if total > 0 else 0
            stats['channel_balance'] = {
                'max': max_channel,
                'min': min_channel,
                'ratio': max_channel / max(min_channel, 1),
            }
            
            # Bank distribution
            max_bank = max(self._stats['bank_distribution'].values()) if total > 0 else 1
            min_bank = min(self._stats['bank_distribution'].values()) if total > 0 else 0
            stats['bank_balance'] = {
                'max': max_bank,
                'min': min_bank,
                'ratio': max_bank / max(min_bank, 1),
            }
        
        return stats
    
    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            'total_addresses': 0,
            'channel_distribution': {i: 0 for i in range(32)},
            'bank_distribution': {i: 0 for i in range(16)},
        }


class AddressPatternIterator:
    """Iterator for address pattern generation
    
    Memory-efficient generation of addresses using generators.
    """
    
    def __init__(self,
                 pattern: AddressPattern,
                 config: Optional[AddressPatternConfig] = None,
                 count: Optional[int] = None):
        """Initialize iterator
        
        Args:
            pattern: Address pattern
            config: Pattern configuration
            count: Optional count limit (None = infinite)
        """
        self.generator = AddressPatternGenerator(config)
        self.generator.set_pattern(pattern)
        self.count = count
        self._generated = 0
    
    def __iter__(self) -> 'AddressPatternIterator':
        return self
    
    def __next__(self) -> int:
        if self.count is not None and self._generated >= self.count:
            raise StopIteration
        
        addr = self.generator.next()
        self._generated += 1
        return addr


def create_address_generator(
    pattern: AddressPattern = AddressPattern.SEQUENTIAL,
    channels: int = 32,
    base_address: int = 0x100000000,
    **kwargs
) -> AddressPatternGenerator:
    """Factory function for address pattern generator
    
    Args:
        pattern: Address pattern type
        channels: Number of HBM4 channels
        base_address: Base address for generation
        **kwargs: Additional configuration
        
    Returns:
        Configured AddressPatternGenerator
    """
    config = AddressPatternConfig(
        channels=channels,
        base_address=base_address,
        **kwargs
    )
    
    generator = AddressPatternGenerator(config)
    generator.set_pattern(pattern)
    
    return generator


# Example usage and demonstration
if __name__ == '__main__':
    # Demo: Generate addresses with different patterns
    config = AddressPatternConfig(seed=42)
    
    print("HBM4 Address Pattern Generator Demo")
    print("=" * 50)
    
    # Sequential pattern
    gen = AddressPatternGenerator(config)
    gen.set_pattern(AddressPattern.SEQUENTIAL)
    print("\n1. Sequential Pattern (10 addresses):")
    addrs = gen.next_batch(10)
    for addr in addrs[:3]:
        decoded = gen.decode(addr)
        print(f"   Addr: 0x{addr:016x} -> Ch{decoded['channel']}, "
              f"BG{decoded['bank_group']}, BK{decoded['bank']}, "
              f"Row{decoded['row']}, Col{decoded['column']}")
    
    # Random pattern
    gen.reset()
    gen.set_pattern(AddressPattern.RANDOM)
    print("\n2. Random Pattern (10 addresses):")
    addrs = gen.next_batch(10)
    channels = [gen.decode(a)['channel'] for a in addrs]
    print(f"   Channels accessed: {sorted(set(channels))}")
    
    # Hotspot pattern
    gen.reset()
    gen.set_pattern(AddressPattern.HOTSPOT)
    print("\n3. Hotspot Pattern (100 addresses):")
    addrs = gen.next_batch(100)
    channel_dist = gen.get_channel_distribution()
    top_channels = sorted(channel_dist.items(), key=lambda x: -x[1])[:5]
    print(f"   Top 5 channels by access count: {top_channels}")
    
    # Channel interleaving
    gen.reset()
    gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)
    config.channel_mapping = ChannelMapping.INTERLEAVE_8
    print("\n4. Channel Interleaving (32 addresses, 8-channel interleave):")
    addrs = gen.next_batch(32)
    decoded = gen.decode_batch(addrs)
    channels = [d['channel'] for d in decoded]
    print(f"   Channels (first 16): {channels[:16]}")
    
    print("\n" + "=" * 50)
    print("Demo complete")
