"""
Integration test for multi-channel traffic distribution

Tests that:
1. All 32 channels receive traffic in HBM4 mode
2. Channel histogram shows uniform distribution for random traffic
3. HBM3 mode with 8 channels works correctly
"""

import pytest
import random
from typing import Dict, List
from collections import Counter


class TestChannelDistribution:
    """Test channel distribution for HBM3 and HBM4 configurations"""

    def test_hbm4_32_channel_distribution(self):
        """Test that all 32 channels receive traffic in HBM4 mode"""
        from model.multi_channel import ChannelSelector

        # Create HBM4 configuration with 32 channels
        num_channels = 32
        selector = ChannelSelector(num_channels=num_channels, strategy=ChannelSelector.ADDR_BASED)

        # Generate random addresses in full address range
        random.seed(42)
        channels_seen = set()

        for _ in range(10000):
            addr = random.randint(0, 0x400000000000 - 1)  # Full 46-bit address space
            channel = selector.select_channel(addr)
            channels_seen.add(channel)

        # All 32 channels should be seen
        assert len(channels_seen) == 32, f"Expected 32 channels, got {len(channels_seen)}: {sorted(channels_seen)}"
        assert channels_seen == set(range(32)), f"Expected all channels 0-31, got {sorted(channels_seen)}"

    def test_hbm3_8_channel_distribution(self):
        """Test that all 8 channels receive traffic in HBM3 mode"""
        from model.multi_channel import ChannelSelector

        num_channels = 8
        selector = ChannelSelector(num_channels=num_channels, strategy=ChannelSelector.ADDR_BASED)

        random.seed(42)
        channels_seen = set()

        for _ in range(10000):
            addr = random.randint(0, 0x400000000000 - 1)
            channel = selector.select_channel(addr)
            channels_seen.add(channel)

        # All 8 channels should be seen
        assert len(channels_seen) == 8, f"Expected 8 channels, got {len(channels_seen)}: {sorted(channels_seen)}"
        assert channels_seen == set(range(8)), f"Expected all channels 0-7, got {sorted(channels_seen)}"

    def test_uniform_distribution_hbm4(self):
        """Test that random traffic distributes uniformly across HBM4 channels"""
        from model.multi_channel import ChannelSelector

        num_channels = 32
        selector = ChannelSelector(num_channels=num_channels, strategy=ChannelSelector.ADDR_BASED)

        random.seed(12345)
        channel_counts = Counter()

        # Generate 100000 random addresses
        for _ in range(100000):
            addr = random.randint(0, 0x400000000000 - 1)
            channel = selector.select_channel(addr)
            channel_counts[channel] += 1

        # Calculate expected count per channel
        total = sum(channel_counts.values())
        expected_per_channel = total / num_channels

        # Each channel should have between 80% and 120% of expected (generous tolerance)
        min_expected = expected_per_channel * 0.8
        max_expected = expected_per_channel * 1.2

        for ch in range(num_channels):
            count = channel_counts[ch]
            assert min_expected <= count <= max_expected, \
                f"Channel {ch}: {count} requests (expected {min_expected:.0f}-{max_expected:.0f})"

        # Calculate chi-squared like metric for distribution quality
        variance = sum((count - expected_per_channel) ** 2 for count in channel_counts.values()) / num_channels
        std_dev = variance ** 0.5
        relative_std_dev = std_dev / expected_per_channel

        # Relative standard deviation should be small (< 5%)
        assert relative_std_dev < 0.05, \
            f"Distribution not uniform: relative std dev = {relative_std_dev:.3f} (expected < 0.05)"

    def test_uniform_distribution_hbm3(self):
        """Test that random traffic distributes uniformly across HBM3 channels"""
        from model.multi_channel import ChannelSelector

        num_channels = 8
        selector = ChannelSelector(num_channels=num_channels, strategy=ChannelSelector.ADDR_BASED)

        random.seed(12345)
        channel_counts = Counter()

        for _ in range(100000):
            addr = random.randint(0, 0x400000000000 - 1)
            channel = selector.select_channel(addr)
            channel_counts[channel] += 1

        total = sum(channel_counts.values())
        expected_per_channel = total / num_channels

        min_expected = expected_per_channel * 0.8
        max_expected = expected_per_channel * 1.2

        for ch in range(num_channels):
            count = channel_counts[ch]
            assert min_expected <= count <= max_expected, \
                f"Channel {ch}: {count} requests (expected {min_expected:.0f}-{max_expected:.0f})"

    def test_traffic_generator_channel_distribution(self):
        """Test that TrafficGenerator produces addresses that distribute across channels"""
        from sim.simulator import SimulationConfig, TrafficGenerator, TrafficPattern
        from model.multi_channel import ChannelSelector

        # HBM4 config with 32 channels
        config = SimulationConfig(
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=1.0,  # Generate every cycle
            seed=42,
        )

        generator = TrafficGenerator(config)
        selector = ChannelSelector(num_channels=32, strategy=ChannelSelector.ADDR_BASED)

        channel_counts = Counter()

        # Generate 10000 requests
        for _ in range(10000):
            requests = generator.generate()
            for req in requests:
                channel = selector.select_channel(req.addr)
                channel_counts[channel] += 1

        # All 32 channels should have received traffic
        active_channels = len([ch for ch, count in channel_counts.items() if count > 0])
        assert active_channels >= 30, f"Only {active_channels} channels active (expected >= 30)"

    def test_address_range_covering_channels(self):
        """Test that address_range covers full channel address space"""
        from sim.simulator import SimulationConfig

        config = SimulationConfig()

        # Default address_range should be 2^46 to cover channel bits
        assert config.address_range == 0x400000000000, \
            f"address_range should be 2^46 (0x400000000000), got {hex(config.address_range)}"

        # Verify it covers the bit range needed for channel selection
        assert config.address_range >= (1 << 46), \
            f"address_range must be at least 2^46 to cover channel bits"

    def test_trace_parser_channel_decoding(self):
        """Test that TraceParser correctly decodes channel from addresses"""
        from sim.trace.parser import TraceParser, TraceConfig, TraceFormat, HBMVersion

        # Test HBM3 (8 channels) - uses HBM3 defaults
        config_hbm3 = TraceConfig(
            trace_file="dummy.trace",
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
        )
        parser_hbm3 = TraceParser(config_hbm3)

        # Generate addresses and check channel distribution
        random.seed(42)
        hbm3_channels = set()
        for _ in range(10000):
            # Generate full-range address
            addr = random.randint(0, 0x400000000000 - 1)
            decoded = parser_hbm3._decode_address(addr)
            hbm3_channels.add(decoded['channel'])

        assert len(hbm3_channels) == 8, f"HBM3: Expected 8 channels, got {len(hbm3_channels)}"

        # Test HBM4 (32 channels) - uses HBM4 defaults
        config_hbm4 = TraceConfig(
            trace_file="dummy.trace",
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM4,
        )
        parser_hbm4 = TraceParser(config_hbm4)

        hbm4_channels = set()
        for _ in range(10000):
            addr = random.randint(0, 0x400000000000 - 1)
            decoded = parser_hbm4._decode_address(addr)
            hbm4_channels.add(decoded['channel'])

        assert len(hbm4_channels) == 32, f"HBM4: Expected 32 channels, got {len(hbm4_channels)}"


class TestChannelBitExtraction:
    """Test that channel bit extraction is correct for different channel counts"""

    def test_channel_bit_positions(self):
        """Test channel bit extraction at correct positions"""
        from model.multi_channel import ChannelSelector

        # HBM3: 8 channels = 3 bits, channel at bits [45:43], LSB at bit 43
        selector_hbm3 = ChannelSelector(num_channels=8)
        # Test specific addresses to verify correct bit extraction
        # For channel N: addr = N << 43
        test_addrs = [
            (0, 0),                           # Channel 0
            (1 << 43, 1),                     # Channel 1
            (2 << 43, 2),                     # Channel 2
            (3 << 43, 3),                     # Channel 3
            (4 << 43, 4),                     # Channel 4
            (5 << 43, 5),                     # Channel 5
            (6 << 43, 6),                     # Channel 6
            (7 << 43, 7),                     # Channel 7
            (8 << 43, 0),                     # Wrap to channel 0
        ]

        for addr, expected_channel in test_addrs:
            actual = selector_hbm3.select_channel(addr)
            assert actual == expected_channel, \
                f"HBM3: addr={hex(addr)}: expected channel {expected_channel}, got {actual}"

        # HBM4: 32 channels = 5 bits, channel at bits [45:41], LSB at bit 41
        selector_hbm4 = ChannelSelector(num_channels=32)
        # For channel N: addr = N << 41
        test_addrs_hbm4 = [
            (0, 0),                           # Channel 0
            (1 << 41, 1),                     # Channel 1
            (7 << 41, 7),                     # Channel 7
            (8 << 41, 8),                     # Channel 8
            (15 << 41, 15),                   # Channel 15
            (16 << 41, 16),                   # Channel 16
            (31 << 41, 31),                   # Channel 31
            (32 << 41, 0),                    # Wrap to channel 0
        ]

        for addr, expected_channel in test_addrs_hbm4:
            actual = selector_hbm4.select_channel(addr)
            assert actual == expected_channel, \
                f"HBM4: addr={hex(addr)}: expected channel {expected_channel}, got {actual}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])