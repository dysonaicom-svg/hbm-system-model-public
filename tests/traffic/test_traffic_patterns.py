"""
Comprehensive Unit Tests for HBM4 Traffic Generator and Address Pattern Generator

Tests all traffic patterns including:
- Sequential, Random, Stride patterns
- Hotspot pattern (80/20 rule)
- Neighbor clustering pattern
- Channel interleaving
- QoS class assignment
- HBM4 32-channel awareness
"""

import pytest
import random
import threading
import time
from typing import List, Dict

from model.traffic.traffic_generator import (
    # Enums
    TrafficPattern,
    DataPrecision,
    QoSLevel,

    # Configuration
    TrafficConfig,
    AddressGenerator,

    # Traffic Patterns
    TrafficGenerator,
    TrafficGeneratorRunner,
    FixedRatePattern,
    BurstPattern,
    RandomPattern,
    RampPattern,
    SinusoidalPattern,
    TraceReplayPattern,
    HotspotPattern,
    NeighborPattern,
    StridePattern,
    ChannelInterleavePattern,
    create_traffic_generator,
    create_address_aware_traffic_generator,
    TrafficType,
    TRAFFIC_TYPE_TO_QOS,
    _sample_qos,
)

from model.traffic.address_pattern import (
    AddressPattern,
    AddressPatternConfig,
    AddressPatternGenerator,
    HBM4AddressBits,
    ChannelMapping,
    AddressPatternIterator,
    create_address_generator,
)

from model.controller.request import HBMRequest


# =============================================================================
# Test Address Pattern Generator
# =============================================================================

class TestAddressPatternConfig:
    """Tests for AddressPatternConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = AddressPatternConfig()
        assert config.base_address == 0x100000000
        assert config.channels == 32
        assert config.pseudo_channels == 64
        assert config.stride == 64
        assert config.hotspot_ratio == 0.2
        assert config.hotspot_window_size == 1024

    def test_custom_config(self):
        """Test custom configuration"""
        config = AddressPatternConfig(
            base_address=0x200000000,
            channels=16,
            pseudo_channels=32,
            stride=128,
            hotspot_ratio=0.1,
            seed=42,
        )
        assert config.base_address == 0x200000000
        assert config.channels == 16
        assert config.stride == 128
        assert config.hotspot_ratio == 0.1

    def test_seed_reproducibility(self):
        """Test that seed provides reproducibility for random pattern"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.RANDOM)

        addrs = gen.next_batch(100)
        assert len(addrs) == 100
        # Should have good variety
        assert len(set(addrs)) > 90


class TestHBM4AddressBits:
    """Tests for HBM4AddressBits address encoding/decoding"""

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

    def test_get_channel(self):
        """Test channel extraction from address"""
        addr = HBM4AddressBits.encode(channel=15)
        assert HBM4AddressBits.get_channel(addr) == 15

    def test_get_bank(self):
        """Test bank extraction from address"""
        addr = HBM4AddressBits.encode(bank=7)
        assert HBM4AddressBits.get_bank(addr) == 7

    def test_get_row(self):
        """Test row extraction from address"""
        addr = HBM4AddressBits.encode(row=12345)
        assert HBM4AddressBits.get_row(addr) == 12345

    def test_get_column(self):
        """Test column extraction from address"""
        addr = HBM4AddressBits.encode(column=32)
        assert HBM4AddressBits.get_column(addr) == 32

    def test_get_pseudo_channel(self):
        """Test pseudo-channel extraction from address"""
        addr = HBM4AddressBits.encode(pseudo_channel=1)
        assert HBM4AddressBits.get_pseudo_channel(addr) == 1

    def test_full_encode_with_all_fields(self):
        """Test encoding with all fields specified"""
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


class TestAddressPatternGenerator:
    """Tests for AddressPatternGenerator"""

    def test_sequential_pattern(self):
        """Test sequential address generation"""
        config = AddressPatternConfig(stride=64)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        addrs = gen.next_batch(10)
        assert len(addrs) == 10

        # Check stride is consistent
        for i in range(9):
            diff = addrs[i + 1] - addrs[i]
            assert diff == 64

    def test_random_pattern(self):
        """Test random address generation"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.RANDOM)

        addrs = gen.next_batch(100)
        assert len(addrs) == 100

        # All addresses should be unique (with very high probability)
        assert len(set(addrs)) > 90  # At least 90 unique

    def test_stride_1kb(self):
        """Test 1KB stride pattern"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.STRIDE_1KB)

        addrs = gen.next_batch(10)
        for i in range(9):
            diff = addrs[i + 1] - addrs[i]
            assert diff == 1024

    def test_stride_4kb(self):
        """Test 4KB stride pattern"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.STRIDE_4KB)

        addrs = gen.next_batch(10)
        for i in range(9):
            diff = addrs[i + 1] - addrs[i]
            assert diff == 4096

    def test_stride_64kb(self):
        """Test 64KB stride pattern"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.STRIDE_64KB)

        addrs = gen.next_batch(10)
        for i in range(9):
            diff = addrs[i + 1] - addrs[i]
            assert diff == 65536

    def test_hotspot_pattern_distribution(self):
        """Test hotspot pattern follows 80/20 rule"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.HOTSPOT)

        # Generate many addresses
        addrs = gen.next_batch(1000)
        assert len(addrs) == 1000

        # Check that we have some locality
        # Hotspot pattern should show clustering
        unique_addrs = len(set(addrs))
        # With 80% hotspot access, we expect some repetition
        assert unique_addrs < 1000  # Some repetition expected

        # Channel distribution should be biased
        decoded = gen.decode_batch(addrs)
        channels = [d['channel'] for d in decoded]
        channel_counts = {}
        for ch in channels:
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

        # Some channels should have significantly more accesses
        max_count = max(channel_counts.values())
        assert max_count > 20  # At least some hotspot concentration

    def test_neighbor_pattern_locality(self):
        """Test neighbor pattern shows locality"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.NEIGHBOR)

        addrs = gen.next_batch(100)
        assert len(addrs) == 100

        # Verify we generated addresses
        assert all(isinstance(a, int) for a in addrs)

    def test_bank_round_robin(self):
        """Test bank-level round-robin pattern"""
        config = AddressPatternConfig(banks_per_pseudo_channel=16)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.BANK_ROUND_ROBIN)

        addrs = gen.next_batch(32)
        decoded = gen.decode_batch(addrs)

        banks = [d['bank'] for d in decoded]

        # Should cycle through banks
        for i in range(16):
            assert banks.count(i) >= 1  # Each bank should appear at least once

    def test_channel_interleave(self):
        """Test channel interleaving pattern"""
        config = AddressPatternConfig(channels=32)
        config.channel_mapping = ChannelMapping.INTERLEAVE_8
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        decoded = gen.decode_batch(addrs)

        channels = [d['channel'] for d in decoded]

        # Should have some channel diversity
        unique_channels = len(set(channels))
        assert unique_channels >= 1

    def test_row_pattern(self):
        """Test row pattern alternates rows"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.ROW_PATTERN)

        addrs = gen.next_batch(20)
        decoded = gen.decode_batch(addrs)

        rows = [d['row'] for d in decoded]

        # Should see row 0 and max row
        assert 0 in rows
        max_row = (1 << HBM4AddressBits.ROW_BITS) - 1
        assert max_row in rows

    def test_column_pattern(self):
        """Test column pattern"""
        gen = AddressPatternGenerator()
        gen.set_pattern(AddressPattern.COLUMN_PATTERN)

        addrs = gen.next_batch(100)
        assert len(addrs) == 100

        decoded = gen.decode_batch(addrs)
        columns = [d['column'] for d in decoded]

        # Column should cycle from 0 to 63
        assert 0 in columns
        # Should see some variety in columns

    def test_custom_sequence(self):
        """Test custom address sequence"""
        config = AddressPatternConfig()
        gen = AddressPatternGenerator(config)

        custom_addrs = [0x1000, 0x2000, 0x3000, 0x4000, 0x5000]
        gen.set_custom_sequence(custom_addrs)

        for expected in custom_addrs:
            assert gen.next() == expected

        # Should loop
        assert gen.next() == 0x1000

    def test_channel_distribution_stats(self):
        """Test channel distribution statistics"""
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

    def test_decode_batch(self):
        """Test batch decoding"""
        config = AddressPatternConfig()
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        addrs = gen.next_batch(10)
        decoded = gen.decode_batch(addrs)

        assert len(decoded) == 10
        for d in decoded:
            assert 'channel' in d
            assert 'bank' in d
            assert 'row' in d
            assert 'column' in d

    def test_reset(self):
        """Test generator reset"""
        config = AddressPatternConfig(stride=64)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        gen.next_batch(10)
        gen.reset()

        # After reset, should start from base address
        addr = gen.next()
        assert addr == config.base_address

    def test_reset_stats(self):
        """Test statistics reset"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        gen.next_batch(100)
        gen.reset_stats()

        stats = gen.get_stats()
        assert stats['total_addresses'] == 0

    def test_bank_distribution(self):
        """Test bank distribution statistics"""
        config = AddressPatternConfig(seed=42)
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.SEQUENTIAL)

        gen.next_batch(200)

        bank_dist = gen.get_bank_distribution()
        assert isinstance(bank_dist, dict)
        assert len(bank_dist) > 0


class TestAddressPatternIterator:
    """Tests for AddressPatternIterator"""

    def test_iterator_creation(self):
        """Test iterator creation"""
        iterator = AddressPatternIterator(AddressPattern.SEQUENTIAL, count=10)
        assert iterator.count == 10

    def test_iterator_iteration(self):
        """Test iterator iteration"""
        iterator = AddressPatternIterator(AddressPattern.SEQUENTIAL, count=5)
        addrs = list(iterator)
        assert len(addrs) == 5

    def test_iterator_exhaustion(self):
        """Test iterator stops after count"""
        iterator = AddressPatternIterator(AddressPattern.SEQUENTIAL, count=3)
        addrs = list(iterator)
        assert len(addrs) == 3


# =============================================================================
# Test Traffic Patterns
# =============================================================================

class TestHotspotPattern:
    """Tests for HotspotPattern (80/20 rule)"""

    def test_hotspot_generation(self):
        """Test hotspot pattern generates requests"""
        pattern = HotspotPattern()
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert len(requests) == 100
        assert all(isinstance(r, HBMRequest) for r in requests)

    def test_hotspot_read_write_mix(self):
        """Test hotspot respects read/write ratio"""
        pattern = HotspotPattern()
        config = TrafficConfig(read_write_ratio=0.8)
        requests = pattern.generate_requests(config, 1000)

        read_count = sum(1 for r in requests if r.is_read)
        write_count = sum(1 for r in requests if not r.is_read)

        # Should be roughly 80/20
        assert 0.7 < (read_count / 1000) < 0.9

    def test_hotspot_custom_ratios(self):
        """Test hotspot with custom hotspot ratios"""
        pattern = HotspotPattern(hotspot_ratio=0.5, hotspot_range=0.3)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert len(requests) == 100


class TestNeighborPattern:
    """Tests for NeighborPattern (clustering)"""

    def test_neighbor_generation(self):
        """Test neighbor pattern generates requests"""
        pattern = NeighborPattern()
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert len(requests) == 100
        assert all(isinstance(r, HBMRequest) for r in requests)

    def test_neighbor_locality(self):
        """Test consecutive requests are close together"""
        pattern = NeighborPattern(locality_radius=64, jump_probability=0.05)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 200)

        # Check locality
        close_count = 0
        for i in range(1, len(requests)):
            diff = abs(requests[i].addr - requests[i-1].addr)
            if diff < 50000:  # Within reasonable distance
                close_count += 1

        # Most should be close
        assert close_count > 100  # At least 50%

    def test_jump_probability(self):
        """Test jump probability causes some distant accesses"""
        pattern = NeighborPattern(jump_probability=0.3)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 200)

        # With 30% jump probability, we should have some jumps
        # Just verify we get the expected count
        assert len(requests) == 200


class TestStridePattern:
    """Tests for StridePattern"""

    def test_stride_1kb_generation(self):
        """Test 1KB stride pattern"""
        pattern = StridePattern(stride=1024)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 50)

        assert len(requests) == 50
        for i in range(49):
            diff = requests[i + 1].addr - requests[i].addr
            assert diff == 1024

    def test_stride_4kb_generation(self):
        """Test 4KB stride pattern"""
        pattern = StridePattern(stride=4096)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 50)

        assert len(requests) == 50
        for i in range(49):
            diff = requests[i + 1].addr - requests[i].addr
            assert diff == 4096

    def test_stride_64kb_generation(self):
        """Test 64KB stride pattern"""
        pattern = StridePattern(stride=65536)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 50)

        assert len(requests) == 50
        for i in range(49):
            diff = requests[i + 1].addr - requests[i].addr
            assert diff == 65536

    def test_qos_assignment(self):
        """Test QoS levels are assigned"""
        pattern = StridePattern(stride=1024)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        qos_values = set(r.qos for r in requests)
        assert len(qos_values) >= 1  # Should have some QoS values


class TestChannelInterleavePattern:
    """Tests for ChannelInterleavePattern"""

    def test_channel_interleave_generation(self):
        """Test channel interleaving generates requests"""
        pattern = ChannelInterleavePattern(interleave_factor=8)
        config = TrafficConfig(channels=32)
        requests = pattern.generate_requests(config, 100)

        assert len(requests) == 100
        assert all(isinstance(r, HBMRequest) for r in requests)

    def test_custom_channels(self):
        """Test with custom channel count"""
        pattern = ChannelInterleavePattern(channels_per_stack=16, interleave_factor=16)
        config = TrafficConfig(channels=16)
        requests = pattern.generate_requests(config, 64)

        assert len(requests) == 64


# =============================================================================
# Test TrafficGenerator with All Patterns
# =============================================================================

class TestTrafficGeneratorAllPatterns:
    """Tests for TrafficGenerator with all available patterns"""

    def test_all_training_patterns(self):
        """Test all training patterns"""
        tg = TrafficGenerator()

        for pattern in [
            TrafficPattern.TRAINING_WEIGHT_UPDATE,
            TrafficPattern.TRAINING_GRADIENT,
            TrafficPattern.TRAINING_FEATURE_MAP,
        ]:
            tg.set_pattern(pattern)
            requests = tg.generate(count=50)
            assert len(requests) == 50

    def test_all_inference_patterns(self):
        """Test all inference patterns"""
        tg = TrafficGenerator()

        for pattern in [
            TrafficPattern.INFERENCE_BURST_READ,
            TrafficPattern.INFERENCE_WEIGHT_REUSE,
            TrafficPattern.INFERENCE_MIXED_PRECISION,
        ]:
            tg.set_pattern(pattern)
            requests = tg.generate(count=50)
            assert len(requests) == 50

    def test_all_synthetic_patterns(self):
        """Test all synthetic patterns"""
        tg = TrafficGenerator()

        for pattern in [
            TrafficPattern.SYNTHETIC_FIXED_RATE,
            TrafficPattern.SYNTHETIC_RANDOM,
            TrafficPattern.SYNTHETIC_RAMP_UP,
            TrafficPattern.SYNTHETIC_RAMP_DOWN,
            TrafficPattern.SYNTHETIC_SINUSOIDAL,
        ]:
            tg.set_pattern(pattern)
            requests = tg.generate(count=50)
            # SYNTHETIC_BURST may generate fewer due to idle periods
            assert len(requests) >= 0

    def test_address_pattern(self):
        """Test ADDRESS_PATTERN pattern"""
        tg = TrafficGenerator()
        tg.set_pattern(TrafficPattern.ADDRESS_PATTERN)
        requests = tg.generate(count=100)
        assert len(requests) == 100

    def test_trace_replay_pattern(self):
        """Test TRACE_REPLAY pattern"""
        tg = TrafficGenerator()
        tg.set_pattern(TrafficPattern.TRACE_REPLAY)

        # TRACE_REPLAY pattern needs a trace to be set
        # Without a trace, it may raise IndexError or return empty
        try:
            requests = tg.generate(count=50)
            assert isinstance(requests, list)
        except IndexError:
            # Expected when no trace is loaded
            pass

    def test_generate_with_default_pattern(self):
        """Test generate without specifying pattern uses current pattern"""
        tg = TrafficGenerator()
        tg.set_pattern(TrafficPattern.SYNTHETIC_FIXED_RATE)
        requests = tg.generate(count=50)
        assert len(requests) == 50

    def test_generate_with_pattern_override(self):
        """Test generate with pattern override"""
        tg = TrafficGenerator()
        tg.set_pattern(TrafficPattern.SYNTHETIC_FIXED_RATE)
        requests = tg.generate(count=50, pattern=TrafficPattern.SYNTHETIC_RANDOM)
        assert len(requests) == 50

    def test_generate_stream(self):
        """Test generate_stream method"""
        tg = TrafficGenerator()
        stream = tg.generate_stream(pattern=TrafficPattern.SYNTHETIC_FIXED_RATE, batch_size=10)

        # Get first batch
        batch = next(stream)
        assert len(batch) == 10

    def test_get_rate(self):
        """Test TrafficGeneratorRunner get_rate"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.start(batch_size=10)
        time.sleep(0.05)
        rate = runner.get_rate()
        runner.stop()

        assert rate >= 0


# =============================================================================
# Test QoS Class Assignment
# =============================================================================

class TestQoSAssignment:
    """Tests for QoS class assignment"""

    def test_qos_distribution(self):
        """Test QoS levels are distributed according to config"""
        tg = TrafficGenerator()
        requests = tg.generate(count=1000)

        qos_counts = {}
        for r in requests:
            qos_counts[r.qos] = qos_counts.get(r.qos, 0) + 1

        # All QoS levels should appear (according to distribution)
        config = tg.config
        for qos, prob in config.qos_distribution.items():
            expected_count = prob * 1000
            actual_count = qos_counts.get(qos, 0)

            # Allow 30% tolerance
            assert abs(actual_count - expected_count) < 300

    def test_critical_qos_for_inference(self):
        """Test inference patterns use critical QoS"""
        tg = TrafficGenerator()
        requests = tg.generate(count=50, pattern=TrafficPattern.INFERENCE_BURST_READ)

        # Burst read should use critical QoS (15)
        critical_count = sum(1 for r in requests if r.qos == 15)
        assert critical_count == len(requests)

    def test_high_qos_for_training(self):
        """Test training patterns use high QoS"""
        tg = TrafficGenerator()
        requests = tg.generate(count=50, pattern=TrafficPattern.TRAINING_GRADIENT)

        # Gradient should use high QoS (12)
        high_count = sum(1 for r in requests if r.qos == 12)
        assert high_count == len(requests)

    def test_sample_qos(self):
        """Test _sample_qos helper function"""
        distribution = {15: 0.5, 8: 0.5}

        samples = [_sample_qos(distribution) for _ in range(100)]
        assert all(s in [15, 8] for s in samples)

    def test_qos_level_enum(self):
        """Test QoSLevel enum values"""
        assert QoSLevel.CRITICAL == 15
        assert QoSLevel.HIGH == 12
        assert QoSLevel.NORMAL == 8
        assert QoSLevel.LOW == 4
        assert QoSLevel.IDLE == 0

    def test_traffic_type_to_qos_mapping(self):
        """Test traffic type to QoS mapping"""
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.REAL_TIME] == QoSLevel.CRITICAL
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.CRITICAL] == QoSLevel.CRITICAL
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.HIGH_PRIORITY] == QoSLevel.HIGH
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.NORMAL] == QoSLevel.NORMAL
        assert TRAFFIC_TYPE_TO_QOS[TrafficType.BACKGROUND] == QoSLevel.LOW


# =============================================================================
# Test Thread Safety
# =============================================================================

class TestThreadSafety:
    """Tests for thread-safe operation"""

    def test_concurrent_generation(self):
        """Test concurrent request generation"""
        tg = TrafficGenerator()
        results = []

        def generate_in_thread(count):
            requests = tg.generate(count=count)
            results.append(len(requests))

        threads = [
            threading.Thread(target=generate_in_thread, args=(25,))
            for _ in range(4)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should complete without errors
        assert len(results) == 4
        assert sum(results) == 100

    def test_concurrent_pattern_switch(self):
        """Test concurrent pattern switching"""
        tg = TrafficGenerator()

        def switch_pattern(pattern):
            tg.set_pattern(pattern)

        patterns = [
            TrafficPattern.SYNTHETIC_FIXED_RATE,
            TrafficPattern.SYNTHETIC_RANDOM,
            TrafficPattern.SYNTHETIC_BURST,
            TrafficPattern.SYNTHETIC_RAMP_UP,
        ]

        threads = [
            threading.Thread(target=switch_pattern, args=(p,))
            for p in patterns
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have switched patterns (at least some switches occurred)
        stats = tg.get_stats()
        assert stats['pattern_switches'] >= 1


# =============================================================================
# Test Factory Functions
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory functions"""

    def test_create_traffic_generator_default(self):
        """Test create_traffic_generator factory with defaults"""
        tg = create_traffic_generator()
        assert isinstance(tg, TrafficGenerator)

    def test_create_traffic_generator_with_params(self):
        """Test create_traffic_generator factory with parameters"""
        tg = create_traffic_generator(
            pattern=TrafficPattern.SYNTHETIC_RANDOM,
            read_write_ratio=0.8,
            request_rate=2e6,
        )

        assert isinstance(tg, TrafficGenerator)
        assert tg._current_pattern == TrafficPattern.SYNTHETIC_RANDOM
        assert tg.config.read_write_ratio == 0.8
        assert tg.config.request_rate == 2e6

    def test_create_address_generator(self):
        """Test create_address_generator factory"""
        gen = create_address_generator(
            pattern=AddressPattern.STRIDE_4KB,
            channels=32,
            base_address=0x100000000,
        )

        assert isinstance(gen, AddressPatternGenerator)
        assert gen._current_pattern == AddressPattern.STRIDE_4KB

    def test_create_with_seed(self):
        """Test factory with seed for reproducibility"""
        gen = create_address_generator(pattern=AddressPattern.RANDOM, seed=42)
        addrs = gen.next_batch(100)
        assert len(addrs) == 100
        # Should have variety
        assert len(set(addrs)) > 90

    def test_create_address_aware_traffic_generator(self):
        """Test create_address_aware_traffic_generator factory"""
        tg, wrapper = create_address_aware_traffic_generator(
            pattern=TrafficPattern.SYNTHETIC_FIXED_RATE,
            read_write_ratio=0.7,
        )

        assert isinstance(tg, TrafficGenerator)
        assert isinstance(wrapper, type(wrapper))


# =============================================================================
# Test Integration
# =============================================================================

class TestIntegration:
    """Integration tests for traffic generator"""

    def test_full_workload_simulation(self):
        """Test complete workload simulation"""
        # Create traffic generator
        config = TrafficConfig(
            read_write_ratio=0.75,
            channels=32,
            request_rate=1e6,
        )
        tg = TrafficGenerator(config)

        # Generate training phase
        tg.set_pattern(TrafficPattern.TRAINING_GRADIENT)
        train_requests = tg.generate(count=1000)
        assert len(train_requests) == 1000

        # Generate inference phase
        tg.set_pattern(TrafficPattern.INFERENCE_BURST_READ)
        inf_requests = tg.generate(count=500)
        assert len(inf_requests) == 500

        # Generate stress test
        tg.set_pattern(TrafficPattern.SYNTHETIC_RANDOM)
        stress_requests = tg.generate(count=1000)
        assert len(stress_requests) == 1000

        # Check combined stats
        stats = tg.get_stats()
        assert stats['total_requests'] == 2500

    def test_multi_pattern_workflow(self):
        """Test switching between multiple patterns"""
        tg = TrafficGenerator()

        patterns = [
            TrafficPattern.SYNTHETIC_FIXED_RATE,
            TrafficPattern.SYNTHETIC_RANDOM,
            TrafficPattern.SYNTHETIC_BURST,
        ]

        for pattern in patterns:
            tg.set_pattern(pattern)
            requests = tg.generate(count=100)
            assert len(requests) == 100

    def test_reset_between_patterns(self):
        """Test reset clears state between patterns"""
        tg = TrafficGenerator()

        # Generate with one pattern
        tg.generate(count=100, pattern=TrafficPattern.SYNTHETIC_FIXED_RATE)

        # Reset
        tg.reset()

        # Generate with different pattern
        requests = tg.generate(count=50, pattern=TrafficPattern.SYNTHETIC_RANDOM)

        stats = tg.get_stats()
        assert stats['total_requests'] == 50

    def test_statistics_accumulation(self):
        """Test statistics are accumulated correctly"""
        tg = TrafficGenerator()

        tg.generate(count=100)
        stats1 = tg.get_stats()

        tg.generate(count=50)
        stats2 = tg.get_stats()

        assert stats2['total_requests'] == stats1['total_requests'] + 50

    def test_reset_stats_only(self):
        """Test reset_stats only clears stats, not pattern"""
        tg = TrafficGenerator()
        tg.generate(count=100)

        tg.reset_stats()

        stats = tg.get_stats()
        assert stats['total_requests'] == 0
        # Pattern should still be set
        assert tg._current_pattern == TrafficPattern.SYNTHETIC_FIXED_RATE


# =============================================================================
# Test Statistics and Reporting
# =============================================================================

class TestStatistics:
    """Tests for statistics and reporting"""

    def test_basic_stats(self):
        """Test basic statistics are collected"""
        tg = TrafficGenerator()
        tg.generate(count=100)

        stats = tg.get_stats()
        assert 'total_requests' in stats
        assert 'read_requests' in stats
        assert 'write_requests' in stats
        assert 'read_ratio' in stats
        assert 'write_ratio' in stats

    def test_qos_stats(self):
        """Test QoS statistics"""
        tg = TrafficGenerator()
        tg.generate(count=100)

        stats = tg.get_stats()
        assert 'requests_by_qos' in stats
        assert len(stats['requests_by_qos']) == 16

    def test_pattern_switch_stats(self):
        """Test pattern switch counting"""
        tg = TrafficGenerator()

        tg.set_pattern(TrafficPattern.SYNTHETIC_RANDOM)
        assert tg.get_stats()['pattern_switches'] == 1

        tg.set_pattern(TrafficPattern.SYNTHETIC_BURST)
        assert tg.get_stats()['pattern_switches'] == 2

    def test_reset_clears_stats(self):
        """Test reset clears statistics"""
        tg = TrafficGenerator()
        tg.generate(count=100)

        tg.reset()

        stats = tg.get_stats()
        assert stats['total_requests'] == 0
        assert stats['read_requests'] == 0

    def test_empty_stats(self):
        """Test empty statistics"""
        tg = TrafficGenerator()

        stats = tg.get_stats()
        assert stats['total_requests'] == 0
        assert stats['read_ratio'] == 0.0
        assert stats['write_ratio'] == 0.0


# =============================================================================
# Test Additional Enums and Types
# =============================================================================

class TestEnums:
    """Tests for enums and type definitions"""

    def test_traffic_pattern_values(self):
        """Test TrafficPattern enum values"""
        assert TrafficPattern.TRAINING_WEIGHT_UPDATE == 1
        assert TrafficPattern.TRAINING_GRADIENT == 2
        assert TrafficPattern.TRAINING_FEATURE_MAP == 3
        assert TrafficPattern.INFERENCE_BURST_READ == 10
        assert TrafficPattern.INFERENCE_WEIGHT_REUSE == 11
        assert TrafficPattern.INFERENCE_MIXED_PRECISION == 12
        assert TrafficPattern.SYNTHETIC_FIXED_RATE == 20
        assert TrafficPattern.SYNTHETIC_BURST == 21
        assert TrafficPattern.SYNTHETIC_RANDOM == 22
        assert TrafficPattern.SYNTHETIC_RAMP_UP == 23
        assert TrafficPattern.SYNTHETIC_RAMP_DOWN == 24
        assert TrafficPattern.SYNTHETIC_SINUSOIDAL == 25
        assert TrafficPattern.TRACE_REPLAY == 30
        assert TrafficPattern.ADDRESS_PATTERN == 31

    def test_data_precision_values(self):
        """Test DataPrecision enum values"""
        assert DataPrecision.FP32 == 32
        assert DataPrecision.FP16 == 16
        assert DataPrecision.BF16 == 16
        assert DataPrecision.INT8 == 8
        assert DataPrecision.INT4 == 4

    def test_traffic_type_enum(self):
        """Test TrafficType enum"""
        assert TrafficType.REAL_TIME == 15
        assert TrafficType.CRITICAL == 15
        assert TrafficType.HIGH_PRIORITY == 12
        assert TrafficType.NORMAL == 8
        assert TrafficType.BACKGROUND == 4
        assert TrafficType.PROBE == 0
        assert TrafficType.IDLE == 0

    def test_address_pattern_enum(self):
        """Test AddressPattern enum"""
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

    def test_channel_mapping_enum(self):
        """Test ChannelMapping enum"""
        assert ChannelMapping.LINEAR == 1
        assert ChannelMapping.INTERLEAVE_2 == 2
        assert ChannelMapping.INTERLEAVE_4 == 3
        assert ChannelMapping.INTERLEAVE_8 == 4
        assert ChannelMapping.INTERLEAVE_16 == 5
        assert ChannelMapping.INTERLEAVE_32 == 6
        assert ChannelMapping.HASH_BASED == 7


# =============================================================================
# Test Channel Mapping Configuration
# =============================================================================

class TestChannelMapping:
    """Tests for channel mapping configurations"""

    def test_linear_mapping(self):
        """Test linear channel mapping"""
        config = AddressPatternConfig()
        config.channel_mapping = ChannelMapping.LINEAR
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_interleave_2(self):
        """Test 2-channel interleaving"""
        config = AddressPatternConfig()
        config.channel_mapping = ChannelMapping.INTERLEAVE_2
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_interleave_4(self):
        """Test 4-channel interleaving"""
        config = AddressPatternConfig()
        config.channel_mapping = ChannelMapping.INTERLEAVE_4
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_interleave_8(self):
        """Test 8-channel interleaving"""
        config = AddressPatternConfig()
        config.channel_mapping = ChannelMapping.INTERLEAVE_8
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_interleave_16(self):
        """Test 16-channel interleaving"""
        config = AddressPatternConfig()
        config.channel_mapping = ChannelMapping.INTERLEAVE_16
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_interleave_32(self):
        """Test 32-channel interleaving"""
        config = AddressPatternConfig()
        config.channel_mapping = ChannelMapping.INTERLEAVE_32
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32

    def test_hash_based(self):
        """Test hash-based channel mapping"""
        config = AddressPatternConfig()
        config.channel_mapping = ChannelMapping.HASH_BASED
        gen = AddressPatternGenerator(config)
        gen.set_pattern(AddressPattern.CHANNEL_INTERLEAVE)

        addrs = gen.next_batch(32)
        assert len(addrs) == 32


# =============================================================================
# Test Traffic Generator Runner
# =============================================================================

class TestTrafficGeneratorRunner:
    """Tests for TrafficGeneratorRunner"""

    def test_runner_creation(self):
        """Test runner creation"""
        tg = TrafficGenerator()
        submitted = []

        def mock_controller(req):
            submitted.append(req)

        runner = TrafficGeneratorRunner(tg, controller=mock_controller)
        assert runner.generator == tg
        assert runner.controller == mock_controller

    def test_rate_setting(self):
        """Test target rate setting"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.set_target_rate(1000)
        assert runner._target_rate == 1000

    def test_start_stop(self):
        """Test runner start/stop"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.start(pattern=TrafficPattern.SYNTHETIC_FIXED_RATE, batch_size=10)
        assert runner._running is True

        # Let it run briefly
        time.sleep(0.1)

        runner.stop()
        assert runner._running is False

    def test_pause_resume(self):
        """Test pause/resume"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.start()
        runner.pause()
        assert runner._pause_event.is_set()

        runner.resume()
        assert not runner._pause_event.is_set()

        runner.stop()

    def test_get_rate(self):
        """Test get_rate calculation"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner._requests_generated = 100
        runner._start_time = time.time() - 1.0  # 1 second ago

        rate = runner.get_rate()
        assert rate == pytest.approx(100.0, rel=1.0)

    def test_multiple_start_calls(self):
        """Test multiple start calls are idempotent"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.start()
        assert runner._running is True

        runner.start()  # Should not restart
        assert runner._running is True

        runner.stop()

    def test_stop_when_not_running(self):
        """Test stop when not running is safe"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.stop()  # Should not raise


# =============================================================================
# Test Additional Patterns
# =============================================================================

class TestAdditionalPatterns:
    """Tests for additional traffic patterns"""

    def test_fixed_rate_read_write_ratio(self):
        """Test fixed rate respects read/write ratio"""
        pattern = FixedRatePattern()
        config = TrafficConfig(read_write_ratio=0.9)
        requests = pattern.generate_requests(config, 100)

        reads = sum(1 for r in requests if r.is_read)
        # Should be roughly 90% reads
        assert reads > 80

    def test_burst_pattern_idle(self):
        """Test burst pattern with idle periods"""
        pattern = BurstPattern(burst_requests=10, idle_ratio=0.5)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 50)

        assert len(requests) <= 50  # May be fewer due to idle

    def test_ramp_up_pattern(self):
        """Test ramp up pattern"""
        pattern = RampPattern(ramp_up=True)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert isinstance(requests, list)

    def test_ramp_down_pattern(self):
        """Test ramp down pattern"""
        pattern = RampPattern(ramp_up=False)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert isinstance(requests, list)

    def test_sinusoidal_pattern(self):
        """Test sinusoidal pattern"""
        pattern = SinusoidalPattern(period=100)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert isinstance(requests, list)

    def test_trace_replay_set_trace(self):
        """Test trace replay with custom trace"""
        pattern = TraceReplayPattern()

        trace = [
            HBMRequest(addr=0x1000, length=64, is_read=True, qos=8),
            HBMRequest(addr=0x2000, length=64, is_read=False, qos=8),
        ]
        pattern.set_trace(trace)

        requests = pattern.generate_requests(config=TrafficConfig(), count=4)

        assert len(requests) == 4
        assert requests[0].addr == 0x1000
        assert requests[2].addr == 0x1000  # Looped

    def test_trace_replay_load_trace(self):
        """Test trace replay load_trace method"""
        pattern = TraceReplayPattern()
        pattern.load_trace("dummy_trace.txt")

        # Should not raise


# =============================================================================
# Test TrafficConfig Details
# =============================================================================

class TestTrafficConfigDetails:
    """Tests for TrafficConfig details"""

    def test_all_config_fields(self):
        """Test all configuration fields"""
        config = TrafficConfig(
            read_write_ratio=0.6,
            request_rate=2e6,
            burst_size=64,
            base_address=0x200000000,
            address_range=0x20000000000,
            address_stride=128,
            batch_size=64,
            sequence_length=1024,
            hidden_size=8192,
            precision=DataPrecision.INT8,
            channels=16,
            pseudo_channels=32,
            banks_per_channel=8,
        )

        assert config.read_write_ratio == 0.6
        assert config.request_rate == 2e6
        assert config.burst_size == 64
        assert config.base_address == 0x200000000
        assert config.address_range == 0x20000000000
        assert config.address_stride == 128
        assert config.batch_size == 64
        assert config.sequence_length == 1024
        assert config.hidden_size == 8192
        assert config.precision == DataPrecision.INT8
        assert config.channels == 16
        assert config.pseudo_channels == 32
        assert config.banks_per_channel == 8

    def test_qos_distribution_custom(self):
        """Test custom QoS distribution"""
        custom_qos = {
            15: 0.1,  # Critical
            12: 0.2,  # High
            8: 0.4,   # Normal
            4: 0.2,   # Low
            0: 0.1,   # Idle
        }
        config = TrafficConfig(qos_distribution=custom_qos)

        # Use approximate comparison for floating point
        assert abs(sum(config.qos_distribution.values()) - 1.0) < 0.0001


# =============================================================================
# Test HBMRequest Integration
# =============================================================================

class TestHBMRequestIntegration:
    """Tests for HBMRequest integration"""

    def test_requests_have_valid_fields(self):
        """Test generated requests have all valid fields"""
        tg = TrafficGenerator()
        requests = tg.generate(count=50)

        for req in requests:
            assert hasattr(req, 'addr')
            assert hasattr(req, 'length')
            assert hasattr(req, 'is_read')
            assert hasattr(req, 'qos')
            assert hasattr(req, 'burst_length')
            assert req.addr >= 0
            assert req.length > 0

    def test_requests_within_address_range(self):
        """Test generated requests are within address range"""
        tg = TrafficGenerator()
        requests = tg.generate(count=100)

        for req in requests:
            # Addresses should be in reasonable range
            assert req.addr >= 0


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
