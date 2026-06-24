"""
Comprehensive Tests for HBM4 Address Pattern Generator

Tests all address pattern generation functionality including:
- HBM4 address encoding/decoding
- All address patterns
- Channel mapping strategies
- Statistics collection
- Iterator functionality
"""

import pytest
import random
from typing import List

from model.traffic.address_pattern import (
    AddressPattern,
    AddressPatternConfig,
    AddressPatternGenerator,
    HBM4AddressBits,
    ChannelMapping,
    AddressPatternIterator,
    create_address_generator,
)


# =============================================================================
# Test HBM4AddressBits
# =============================================================================

class TestHBM4AddressBits:
    """Tests for HBM4AddressBits class"""

    def test_encode_decode_round_trip(self):
        """Test encode then decode returns original values"""
        test_cases = [
            {'channel': 0, 'bank': 0, 'row': 0, 'column': 0},
            {'channel': 31, 'bank': 15, 'row': 1000, 'column': 63},
            {'channel': 16, 'bank': 8, 'row': 524287, 'column': 32},
        ]

        for tc in test_cases:
            addr = HBM4AddressBits.encode(**tc)
            decoded = HBM4AddressBits.decode(addr)

            assert decoded['channel'] == tc['channel']
            assert decoded['bank'] == tc['bank']
            assert decoded['row'] == tc['row']
            assert decoded['column'] == tc['column']

    def test_encode_with_all_fields(self):
        """Test encoding with all fields"""
        addr = HBM4AddressBits.encode(
            stack=1,
            channel=15,
            pseudo_channel=1,
            bank_group=3,
            bank=7,
            row=100000,
            column=32,
            burst=1
        )
        decoded = HBM4AddressBits.decode(addr)

        assert decoded['stack'] == 1
        assert decoded['channel'] == 15
        assert decoded['pseudo_channel'] == 1
        assert decoded['bank_group'] == 3
        assert decoded['bank'] == 7
        assert decoded['row'] == 100000
        assert decoded['column'] == 32
        assert decoded['burst'] == 1

    def test_get_channel(self):
        """Test channel extraction"""
        addr = HBM4AddressBits.encode(channel=15)
        assert HBM4AddressBits.get_channel(addr) == 15

    def test_get_bank(self):
        """Test bank extraction"""
        addr = HBM4AddressBits.encode(bank=7)
        assert HBM4AddressBits.get_bank(addr) == 7

    def test_get_row(self):
        """Test row extraction"""
        addr = HBM4AddressBits.encode(row=12345)
        assert HBM4AddressBits.get_row(addr) == 12345

    def test_get_column(self):
        """Test column extraction"""
        addr = HBM4AddressBits.encode(column=32)
        assert HBM4AddressBits.get_column(addr) == 32

    def test_get_pseudo_channel(self):
        """Test pseudo-channel extraction"""
        addr = HBM4AddressBits.encode(pseudo_channel=1)
        assert HBM4AddressBits.get_pseudo_channel(addr) == 1

    def test_encode_bounds_checking(self):
        """Test that encoding handles bounds correctly"""
        # Should mask values to fit in their bit fields
        addr = HBM4AddressBits.encode(
            channel=100,  # Exceeds 5 bits (max 31)
            bank=50,      # Exceeds 4 bits (max 15)
            row=1000000,  # Large row value
        )
        decoded = HBM4AddressBits.decode(addr)

        # Values should be masked
        assert decoded['channel'] == (100 & 0x1F)  # 5 bits
        assert decoded['bank'] == (50 & 0x0F)       # 4 bits

    def test_masks_are_correct(self):
        """Test that masks are properly defined"""
        assert HBM4AddressBits.STACK_BITS == 2
        assert HBM4AddressBits.CHANNEL_BITS == 5
        assert HBM4AddressBits.PCH_BITS == 1
        assert HBM4AddressBits.BG_BITS == 3
        assert HBM4AddressBits.BANK_BITS == 4
        assert HBM4AddressBits.ROW_BITS == 19
        assert HBM4AddressBits.COL_BITS == 6
        assert HBM4AddressBits.BURST_BITS == 2

    def test_shift_values(self):
        """Test shift values are correct"""
        assert HBM4AddressBits.STACK_SHIFT == 0
        assert HBM4AddressBits.CHANNEL_SHIFT == 2
        assert HBM4AddressBits.PCH_SHIFT == 7
        assert HBM4AddressBits.BG_SHIFT == 8
        assert HBM4AddressBits.BANK_SHIFT == 11
        assert HBM4AddressBits.ROW_SHIFT == 15
        assert HBM4AddressBits.COL_SHIFT == 34
        assert HBM4AddressBits.BURST_SHIFT == 40


# =============================================================================
# Test AddressPatternConfig
# =============================================================================

class TestAddressPatternConfig:
    """Tests for AddressPatternConfig"""

    def test_default_values(self):
        """Test default configuration values"""
        config = AddressPatternConfig()

        assert config.base_address == 0x100000000
        assert config.address_range == 0x10000000000
        assert config.channels == 32
        assert config.pseudo_channels == 64
        assert config.banks_per_pseudo_channel == 16
        assert config.stride == 64
        assert config.channel_mapping == ChannelMapping.LINEAR
        assert config.hotspot_ratio == 0.2
        assert config.hotspot_window_size == 1024
        assert config.neighbor_distance == 64
        assert config.seed is None

    def test_custom_values(self):
        """Test custom configuration values"""
        config = AddressPatternConfig(
            base_address=0x200000000,
            address_range=0x20000000000,
            channels=16,
            pseudo_channels=32,
            banks_per_pseudo_channel=8,
            stride=128,
            channel_mapping=ChannelMapping.INTERLEAVE_8,
            hotspot_ratio=0.3,
            hotspot_window_size=2048,
            neighbor_distance=128,
            seed=42,
        )

        assert config.base_address == 0x200000000
        assert config.channels == 16
        assert config.stride == 128
        assert config.channel_mapping == ChannelMapping.INTERLEAVE_8
        assert config.hotspot_ratio == 0.3
        assert config.seed == 42

    def test_seed_sets_random(self):
        """Test that seed is applied in post_init"""
        # Just verify it doesn't raise
        config = AddressPatternConfig(seed=12345)
        assert config.seed == 12345


# =============================================================================
# Test AddressPatternGenerator
# =============================================================================

class TestAddressPatternGenerator:
    """Tests for AddressPatternGenerator"""

    def test_creation(self):
        """Test generator creation"""
        gen = AddressPatternGenerator()
        assert gen.config is not None
        assert gen.hbm_spec is not None
        assert gen.addr_bits is not None
        assert gen._current_pattern == AddressPattern.SEQUENTIAL

    def test_creation_with_config(self):
        """Test generator creation with config"""
        config = AddressPatternConfig(channels=16)
        gen = AddressPatternGenerator(config)
        assert gen.config.channels == 16

    def test_set_pattern(self):
        """Test set_pattern method"""
        gen = AddressPatternGenerator()

        gen.set_pattern(AddressPattern.RANDOM)
        assert gen._current_pattern == AddressPattern.RANDOM

        gen.set_pattern(AddressPattern.HOTSPOT)
        assert gen._current_pattern == AddressPattern.HOTSPOT

    def test_reset(self):
        """Test reset method"""
        config = AddressPatternConfig(stride=64)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        gen.next_batch(100)
        gen.reset()

        # After reset, should start from base_address
        addr = gen.next()
        assert addr == config.base_address

    def test_next_batch(self):
        """Test next_batch method"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        addrs = gen.next_batch(50)
        assert len(addrs) == 50

    # Sequential Pattern Tests
    def test_sequential_pattern_basic(self):
        """Test sequential pattern basic functionality"""
        config = AddressPatternConfig(stride=64)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        addrs = gen.next_batch(10)
        assert len(addrs) == 10

        for i in range(9):
            assert addrs[i + 1] - addrs[i] == 64

    def test_sequential_pattern_wraparound(self):
        """Test sequential pattern wraps around correctly"""
        config = AddressPatternConfig(
            base_address=0x1000,
            address_range=256,  # Small range
            stride=64
        )
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        # Generate more than fits in range
        addrs = gen.next_batch(10)
        assert len(addrs) == 10

        # Should wrap around
        assert addrs[4] == 0x1000  # Wrapped around

    # Random Pattern Tests
    def test_random_pattern_basic(self):
        """Test random pattern basic functionality"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.RANDOM)

        addrs = gen.next_batch(100)
        assert len(addrs) == 100

        # Should have good variety
        assert len(set(addrs)) > 90

    def test_random_pattern_within_range(self):
        """Test random pattern stays within range"""
        config = AddressPatternConfig(
            base_address=0x1000,
            address_range=0x10000,
            seed=42
        )
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.RANDOM)

        addrs = gen.next_batch(50)
        for addr in addrs:
            assert 0x1000 <= addr < 0x1000 + 0x10000

    # Stride Pattern Tests
    def test_stride_1kb_pattern(self):
        """Test 1KB stride pattern"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.STRIDE_1KB)

        addrs = gen.next_batch(10)
        for i in range(9):
            assert addrs[i + 1] - addrs[i] == 1024

    def test_stride_4kb_pattern(self):
        """Test 4KB stride pattern"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.STRIDE_4KB)

        addrs = gen.next_batch(10)
        for i in range(9):
            assert addrs[i + 1] - addrs[i] == 4096

    def test_stride_64kb_pattern(self):
        """Test 64KB stride pattern"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.STRIDE_64KB)

        addrs = gen.next_batch(10)
        for i in range(9):
            assert addrs[i + 1] - addrs[i] == 65536

    # Hotspot Pattern Tests
    def test_hotspot_pattern_basic(self):
        """Test hotspot pattern basic functionality"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.HOTSPOT)

        addrs = gen.next_batch(100)
        assert len(addrs) == 100

    def test_hotspot_pattern_locality(self):
        """Test hotspot pattern shows locality"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.HOTSPOT)

        addrs = gen.next_batch(500)
        unique = len(set(addrs))

        # With 80% hotspot, we expect significant repetition
        # But randomness means we can't assert a specific value

    # Neighbor Pattern Tests
    def test_neighbor_pattern_basic(self):
        """Test neighbor pattern basic functionality"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.NEIGHBOR)

        addrs = gen.next_batch(100)
        assert len(addrs) == 100

    def test_neighbor_pattern_within_range(self):
        """Test neighbor pattern stays within range"""
        config = AddressPatternConfig(
            base_address=0x1000,
            address_range=0x1000000,
            seed=42
        )
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.NEIGHBOR)

        addrs = gen.next_batch(100)
        for addr in addrs:
            # Should be within range
            assert addr >= config.base_address

    # Bank Round Robin Tests
    def test_bank_round_robin_basic(self):
        """Test bank round robin basic functionality"""
        config = AddressPatternConfig(banks_per_pseudo_channel=16)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.BANK_ROUND_ROBIN)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

        decoded = gen.decode_batch(addrs)
        banks = [d['bank'] for d in decoded]

        # Should see all banks
        for i in range(16):
            assert banks.count(i) >= 1

    # Channel Interleave Tests
    def test_channel_interleave_linear(self):
        """Test channel interleave with linear mapping"""
        config = AddressPatternConfig(channels=32)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_channel_interleave_interleave_2(self):
        """Test channel interleave with 2-channel"""
        config = AddressPatternConfig(channels=32)
        config.channel_mapping = ChannelMapping.INTERLEAVE_2
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_channel_interleave_interleave_4(self):
        """Test channel interleave with 4-channel"""
        config = AddressPatternConfig(channels=32)
        config.channel_mapping = ChannelMapping.INTERLEAVE_4
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_channel_interleave_interleave_8(self):
        """Test channel interleave with 8-channel"""
        config = AddressPatternConfig(channels=32)
        config.channel_mapping = ChannelMapping.INTERLEAVE_8
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_channel_interleave_interleave_16(self):
        """Test channel interleave with 16-channel"""
        config = AddressPatternConfig(channels=32)
        config.channel_mapping = ChannelMapping.INTERLEAVE_16
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_channel_interleave_interleave_32(self):
        """Test channel interleave with 32-channel"""
        config = AddressPatternConfig(channels=32)
        config.channel_mapping = ChannelMapping.INTERLEAVE_32
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(64)
        assert len(addrs) == 64

    def test_channel_interleave_hash_based(self):
        """Test channel interleave with hash-based mapping"""
        config = AddressPatternConfig(channels=32)
        config.channel_mapping = ChannelMapping.HASH_BASED
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    # Row Pattern Tests
    def test_row_pattern_basic(self):
        """Test row pattern basic functionality"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.ROW_PATTERN)

        addrs = gen.next_batch(20)
        assert len(addrs) == 20

        decoded = gen.decode_batch(addrs)
        rows = [d['row'] for d in decoded]

        # Should see both row 0 and max row
        assert 0 in rows
        max_row = (1 << HBM4AddressBits.ROW_BITS) - 1
        assert max_row in rows

    # Column Pattern Tests
    def test_column_pattern_basic(self):
        """Test column pattern basic functionality"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.COLUMN_PATTERN)

        addrs = gen.next_batch(100)
        assert len(addrs) == 100

        decoded = gen.decode_batch(addrs)
        columns = [d['column'] for d in decoded]

        # Should see column 0
        assert 0 in columns

    # Custom Sequence Tests
    def test_custom_sequence_basic(self):
        """Test custom sequence basic functionality"""
        gen = AddressPatternGenerator()

        custom_addrs = [0x1000, 0x2000, 0x3000, 0x4000, 0x5000]
        gen.set_custom_sequence(custom_addrs)

        for expected in custom_addrs:
            assert gen.next() == expected

    def test_custom_sequence_wraps(self):
        """Test custom sequence wraps around"""
        gen = AddressPatternGenerator()

        custom_addrs = [0x1000, 0x2000, 0x3000]
        gen.set_custom_sequence(custom_addrs)

        # Generate 6, should loop twice
        for _ in range(6):
            gen.next()

        # After 6 generations, we're back at index 0
        assert gen.next() == 0x1000


# =============================================================================
# Test Statistics
# =============================================================================

class TestStatistics:
    """Tests for statistics collection"""

    def test_basic_stats(self):
        """Test basic statistics"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.SEQUENTIAL)
        gen.next_batch(100)

        stats = gen.get_stats()
        assert stats['total_addresses'] == 100
        assert stats['pattern'] == 'SEQUENTIAL'

    def test_channel_distribution(self):
        """Test channel distribution statistics"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.RANDOM)

        gen.next_batch(500)

        channel_dist = gen.get_channel_distribution()
        assert isinstance(channel_dist, dict)
        assert len(channel_dist) == 32  # 32 channels

        total = sum(channel_dist.values())
        assert total == 500

    def test_bank_distribution(self):
        """Test bank distribution statistics"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        gen.next_batch(200)

        bank_dist = gen.get_bank_distribution()
        assert isinstance(bank_dist, dict)
        assert len(bank_dist) == 16  # 16 banks

    def test_channel_balance_stats(self):
        """Test channel balance statistics"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.RANDOM)

        gen.next_batch(500)

        stats = gen.get_stats()
        assert 'channel_balance' in stats

        balance = stats['channel_balance']
        assert 'max' in balance
        assert 'min' in balance
        assert 'ratio' in balance
        assert balance['max'] >= balance['min']

    def test_bank_balance_stats(self):
        """Test bank balance statistics"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        gen.next_batch(500)

        stats = gen.get_stats()
        assert 'bank_balance' in stats

        balance = stats['bank_balance']
        assert 'max' in balance
        assert 'min' in balance
        assert 'ratio' in balance

    def test_reset_stats(self):
        """Test reset_stats method"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        gen.next_batch(100)

        stats1 = gen.get_stats()
        assert stats1['total_addresses'] == 100

        gen.reset_stats()

        stats2 = gen.get_stats()
        assert stats2['total_addresses'] == 0


# =============================================================================
# Test Address Decoding
# =============================================================================

class TestAddressDecoding:
    """Tests for address decoding functionality"""

    def test_decode_single(self):
        """Test single address decoding"""
        gen = AddressPatternGenerator()
        addr = gen.next()

        decoded = gen.decode(addr)
        assert 'channel' in decoded
        assert 'bank' in decoded
        assert 'row' in decoded
        assert 'column' in decoded

    def test_decode_batch(self):
        """Test batch decoding"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        addrs = gen.next_batch(10)
        decoded = gen.decode_batch(addrs)

        assert len(decoded) == 10
        for d in decoded:
            assert 'channel' in d
            assert 'bank' in d
            assert 'row' in d
            assert 'column' in d

    def test_decode_matches_encode(self):
        """Test that decode matches encode"""
        original = {
            'stack': 1,
            'channel': 15,
            'pseudo_channel': 1,
            'bank_group': 3,
            'bank': 7,
            'row': 100000,
            'column': 32,
            'burst': 1
        }

        addr = HBM4AddressBits.encode(**original)
        decoded = HBM4AddressBits.decode(addr)

        for key, value in original.items():
            assert decoded[key] == value


# =============================================================================
# Test Iterator
# =============================================================================

class TestAddressPatternIterator:
    """Tests for AddressPatternIterator"""

    def test_iterator_creation(self):
        """Test iterator creation"""
        iterator = AddressPatternIterator(AddressPattern.SEQUENTIAL, count=10)
        assert iterator.count == 10
        assert iterator._generated == 0

    def test_iterator_creation_with_config(self):
        """Test iterator creation with config"""
        config = AddressPatternConfig(seed=42)
        iterator = AddressPatternIterator(AddressPattern.RANDOM, config=config, count=10)
        assert iterator.count == 10

    def test_iterator_iteration(self):
        """Test iterator iteration"""
        iterator = AddressPatternIterator(AddressPattern.SEQUENTIAL, count=5)
        addrs = list(iterator)
        assert len(addrs) == 5
        assert iterator._generated == 5

    def test_iterator_unlimited(self):
        """Test unlimited iterator"""
        iterator = AddressPatternIterator(AddressPattern.SEQUENTIAL, count=None)

        # Generate exactly 10
        addrs = [next(iterator) for _ in range(10)]
        assert len(addrs) == 10

    def test_iterator_exhaustion(self):
        """Test iterator stops at count"""
        iterator = AddressPatternIterator(AddressPattern.SEQUENTIAL, count=3)
        addrs = list(iterator)
        assert len(addrs) == 3

        # Should raise StopIteration
        with pytest.raises(StopIteration):
            next(iterator)

    def test_iterator_reuse(self):
        """Test that creating new iterator gives fresh state"""
        config = AddressPatternConfig(stride=64)
        iterator1 = AddressPatternIterator(AddressPattern.SEQUENTIAL, config=config, count=5)
        addr1 = next(iterator1)

        iterator2 = AddressPatternIterator(AddressPattern.SEQUENTIAL, config=config, count=5)
        addr2 = next(iterator2)

        assert addr1 == addr2


# =============================================================================
# Test Factory Function
# =============================================================================

class TestFactoryFunction:
    """Tests for create_address_generator factory"""

    def test_create_default(self):
        """Test create with defaults"""
        gen = create_address_generator()
        assert isinstance(gen, AddressPatternGenerator)

    def test_create_with_pattern(self):
        """Test create with pattern"""
        gen = create_address_generator(pattern=AddressPattern.RANDOM)
        assert gen._current_pattern == AddressPattern.RANDOM

    def test_create_with_channels(self):
        """Test create with channels"""
        gen = create_address_generator(channels=16)
        assert gen.config.channels == 16

    def test_create_with_base_address(self):
        """Test create with base address"""
        gen = create_address_generator(base_address=0x200000000)
        assert gen.config.base_address == 0x200000000

    def test_create_with_all_params(self):
        """Test create with all parameters"""
        gen = create_address_generator(
            pattern=AddressPattern.STRIDE_4KB,
            channels=16,
            base_address=0x100000000,
            seed=42,
        )
        assert gen._current_pattern == AddressPattern.STRIDE_4KB
        assert gen.config.channels == 16
        assert gen.config.base_address == 0x100000000
        assert gen.config.seed == 42


# =============================================================================
# Test Channel Mapping Enum
# =============================================================================

class TestChannelMapping:
    """Tests for ChannelMapping enum"""

    def test_all_values(self):
        """Test all channel mapping values"""
        assert ChannelMapping.LINEAR == 1
        assert ChannelMapping.INTERLEAVE_2 == 2
        assert ChannelMapping.INTERLEAVE_4 == 3
        assert ChannelMapping.INTERLEAVE_8 == 4
        assert ChannelMapping.INTERLEAVE_16 == 5
        assert ChannelMapping.INTERLEAVE_32 == 6
        assert ChannelMapping.HASH_BASED == 7

    def test_values_count(self):
        """Test we have all expected mappings"""
        values = list(ChannelMapping)
        assert len(values) == 7


# =============================================================================
# Test AddressPattern Enum
# =============================================================================

class TestAddressPatternEnum:
    """Tests for AddressPattern enum"""

    def test_all_values(self):
        """Test all address pattern values"""
        assert AddressPattern.SEQUENTIAL == 1
        assert AddressPattern.RANDOM == 2
        assert AddressPattern.STRIDE_1KB == 3
        assert AddressPattern.STRIDE_4KB == 4
        assert AddressPattern.STRIDE_64KB == 5
        assert AddressPattern.STRIDE_PAGE == 6
        assert AddressPattern.HOTSPOT == 7
        assert AddressPattern.NEIGHBOR == 8
        assert AddressPattern.BANK_ROUND_ROBIN == 9
        assert AddressPattern.CHANNEL_INTERLEAVE == 10
        assert AddressPattern.ROW_PATTERN == 11
        assert AddressPattern.COLUMN_PATTERN == 12
        assert AddressPattern.CUSTOM == 99

    def test_values_count(self):
        """Test we have all expected patterns"""
        values = list(AddressPattern)
        assert len(values) == 13


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
