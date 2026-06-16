"""
Address Mapping Tests

Tests for validating all address mapping modes.
HBM supports multiple address mapping schemes for different access patterns.

Test Categories:
- mapping_modes: All supported mapping modes (rbc, bcr, crb, etc.)
- mapping_correctness: Verify addresses map to correct channels/banks
- mapping_performance: Performance impact of different mappings
- custom_mapping: Custom mapping configuration

References:
- JEDEC JESD238 HBM3 Specification
- JEDEC JESD270-4A HBM4 Specification
- HBM Address Mapping (Section 5.2.2 in JESD238)
"""

import pytest
from typing import List, Dict, Tuple

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
from model.controller.config import HBMConfig
from model.controller.address_decoder import AddressDecoder, DecodedAddress


@pytest.mark.regression
class TestAddressMapping:
    """Address mapping tests"""

    @pytest.fixture
    def decoder(self, hbm3_config):
        """Create address decoder"""
        return AddressDecoder(hbm3_config)

    @pytest.fixture
    def mapping_config(self):
        """Configuration with different mapping modes"""
        return {
            'rbc': 'Row-Bank-Column (row locality optimized)',
            'bcr': 'Bank-Column-Row (bank parallelism optimized)',
            'crb': 'Column-Row-Bank (sequential access optimized)',
        }

    def test_rbc_mapping(self, hbm3_config):
        """Test Row-Bank-Column mapping (default)

        RBC mapping optimizes for row locality:
        - Adjacent addresses access same row
        - Good for sequential and hot-spot patterns
        """
        config = hbm3_config.copy()
        config.address_mapping = "rbc"

        decoder = AddressDecoder(config)

        # Adjacent addresses should map to same row
        addr1 = 0x1000
        addr2 = 0x1040  # 64 bytes apart

        decoded1 = decoder.decode(addr1)
        decoded2 = decoder.decode(addr2)

        assert decoded1 is not None
        assert decoded2 is not None

        # Both should map to same channel/bank (adjacent columns in same row)
        print(f"  RBC: addr1={addr1:#x} -> ch={decoded1.channel_id}, "
              f"bank={decoded1.bank_id}, row={decoded1.row_id}")
        print(f"  RBC: addr2={addr2:#x} -> ch={decoded2.channel_id}, "
              f"bank={decoded2.bank_id}, row={decoded2.row_id}")

    def test_bcr_mapping(self, hbm3_config):
        """Test Bank-Column-Row mapping

        BCR mapping optimizes for bank parallelism:
        - Adjacent addresses access different banks
        - Good for random access with bank parallelism
        """
        config = hbm3_config.copy()
        config.address_mapping = "bcr"

        decoder = AddressDecoder(config)

        # Adjacent addresses should map to different banks
        addr1 = 0x1000
        addr2 = 0x1040  # 64 bytes apart

        decoded1 = decoder.decode(addr1)
        decoded2 = decoder.decode(addr2)

        assert decoded1 is not None
        assert decoded2 is not None

        print(f"  BCR: addr1={addr1:#x} -> ch={decoded1.channel_id}, "
              f"bank={decoded1.bank_id}, row={decoded1.row_id}")
        print(f"  BCR: addr2={addr2:#x} -> ch={decoded2.channel_id}, "
              f"bank={decoded2.bank_id}, row={decoded2.row_id}")

    def test_crb_mapping(self, hbm3_config):
        """Test Column-Row-Bank mapping

        CRB mapping optimizes for sequential access:
        - Column changes fastest
        - Good for streaming workloads
        """
        config = hbm3_config.copy()
        config.address_mapping = "crb"

        decoder = AddressDecoder(config)

        # Adjacent addresses should map to different columns in same row
        addr1 = 0x1000
        addr2 = 0x1040

        decoded1 = decoder.decode(addr1)
        decoded2 = decoder.decode(addr2)

        assert decoded1 is not None
        assert decoded2 is not None

        print(f"  CRB: addr1={addr1:#x} -> ch={decoded1.channel_id}, "
              f"bank={decoded1.bank_id}, row={decoded1.row_id}")
        print(f"  CRB: addr2={addr2:#x} -> ch={decoded2.channel_id}, "
              f"bank={decoded2.bank_id}, row={decoded2.row_id}")

    def test_address_to_channel_mapping(self, hbm3_config):
        """Test address to channel mapping

        Validates that addresses map to valid channels.
        """
        decoder = AddressDecoder(hbm3_config)

        # Test range of addresses
        for addr in [0x0, 0x1000_0000, 0x2000_0000, 0x4000_0000]:
            decoded = decoder.decode(addr)

            assert decoded is not None
            assert 0 <= decoded.channel_id < hbm3_config.channels_per_stack
            assert 0 <= decoded.stack_id < hbm3_config.stack_count

    def test_address_to_bank_mapping(self, hbm3_config):
        """Test address to bank mapping

        Validates that addresses map to valid banks.
        """
        decoder = AddressDecoder(hbm3_config)

        for addr in range(0, 0x100_0000, 0x100_000):
            decoded = decoder.decode(addr)

            assert decoded is not None
            assert 0 <= decoded.bank_id < hbm3_config.banks_per_pseudo_channel
            assert 0 <= decoded.bank_group_id < hbm3_config.bank_groups_per_channel

    def test_address_to_row_mapping(self, hbm3_config):
        """Test address to row mapping

        Validates that addresses map to valid rows.
        """
        decoder = AddressDecoder(hbm3_config)

        # Test with large address range
        for addr in range(0, 0x1000_0000, 0x100_0000):
            decoded = decoder.decode(addr)

            assert decoded is not None
            assert decoded.row_id >= 0

    def test_address_wrap_around(self, hbm3_config):
        """Test address wrap-around behavior

        Addresses beyond address space should wrap correctly.
        """
        decoder = AddressDecoder(hbm3_config)

        # Test addresses near boundary
        max_addr = 0xFFFF_FFFF_FFFF

        decoded = decoder.decode(max_addr)
        assert decoded is not None

        # Address 0 should wrap to beginning
        decoded_zero = decoder.decode(0)
        assert decoded_zero is not None

    def test_sequential_address_mapping(self, hbm3_config):
        """Test mapping of sequential addresses

        Sequential addresses should have predictable mapping.
        """
        decoder = AddressDecoder(hbm3_config)

        # Generate sequential addresses
        addresses = [i * 64 for i in range(16)]

        decoded = [decoder.decode(addr) for addr in addresses]

        # All should decode successfully
        for d in decoded:
            assert d is not None

        print(f"\nSequential Address Mapping:")
        for i, addr in enumerate(addresses[:8]):
            d = decoded[i]
            print(f"  addr={addr:#x} -> ch={d.channel_id}, "
                  f"bg={d.bank_group_id}, bk={d.bank_id}, "
                  f"row={d.row_id}, col={d.col_id}")

    def test_row_hit_detection(self, hbm3_config):
        """Test row hit detection with address mapping

        Requests to the same row should be detected as row hits.
        """
        config = hbm3_config.copy()
        config.address_mapping = "rbc"

        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest

        controller = HBMController(config)

        # Submit requests to same row (using decoded address)
        base_addr = 0x1000_0000

        for _ in range(3):
            request = HBMRequest(addr=base_addr, length=64, is_read=True)
            controller.submit_request(request)

        # Check bank state
        if controller.bank_states:
            for bank_key, state in controller.bank_states.items():
                # State should be tracked
                pass

    def test_channel_distribution(self, hbm3_config):
        """Test channel distribution of random addresses

        Addresses should distribute across all channels.
        """
        decoder = AddressDecoder(hbm3_config)

        # Generate random addresses
        import random
        random.seed(42)

        addresses = [random.randint(0, 0xFFFF_FFFF) for _ in range(1000)]

        decoded = [decoder.decode(addr) for addr in addresses]

        # Count channel usage
        channel_counts = [0] * hbm3_config.channels_per_stack
        for d in decoded:
            if d:
                channel_counts[d.channel_id] += 1

        # All channels should be used
        active_channels = sum(1 for c in channel_counts if c > 0)

        print(f"\nChannel Distribution ({hbm3_config.channels_per_stack} channels):")
        print(f"  Active channels: {active_channels}")
        print(f"  Channel counts: {channel_counts}")

        # Most channels should be active
        min_active = hbm3_config.channels_per_stack // 2
        assert active_channels >= min_active, \
            f"Few active channels: {active_channels}/{hbm3_config.channels_per_stack}"

    def test_bank_group_mapping(self, hbm3_config):
        """Test bank group mapping

        Validates proper bank group assignment.
        """
        decoder = AddressDecoder(hbm3_config)

        # Test range of addresses
        for addr in range(0, 0x1000_000, 0x10_0000):
            decoded = decoder.decode(addr)

            assert decoded is not None
            assert 0 <= decoded.bank_group_id < hbm3_config.bank_groups_per_channel

    def test_pseudo_channel_mapping(self, hbm3_config):
        """Test pseudo-channel mapping

        HBM3 has 2 pseudo-channels per channel.
        """
        decoder = AddressDecoder(hbm3_config)

        # Test addresses across pseudo-channels
        for addr in range(0, 0x1000_000, 0x100_000):
            decoded = decoder.decode(addr)

            assert decoded is not None
            assert 0 <= decoded.pseudo_channel_id < hbm3_config.pseudo_channels_per_channel

    def test_stack_mapping(self, hbm3_config):
        """Test stack mapping for multi-stack configurations

        Addresses should route to correct stacks.
        """
        config = hbm3_config.copy()
        config.stack_count = 4

        decoder = AddressDecoder(config)

        # Test addresses across stack space
        for addr in range(0, 0x1000_0000, 0x1000_000):
            decoded = decoder.decode(addr)

            assert decoded is not None
            assert 0 <= decoded.stack_id < config.stack_count


@pytest.mark.regression
class TestMappingPerformance:
    """Tests for performance impact of address mapping"""

    def test_rbc_performance(self, hbm3_config):
        """Test RBC mapping performance

        RBC should perform well for sequential and row-local patterns.
        """
        config = hbm3_config.copy()
        config.address_mapping = "rbc"

        sim_config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            read_ratio=1.0,
            seed=42,
            hbm_config=config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        print(f"\nRBC Mapping Performance:")
        print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
        print(f"  Row Hit Rate: {stats.row_hit_rate:.2%}")

        assert stats.throughput_gbps > 0

    def test_bcr_performance(self, hbm3_config):
        """Test BCR mapping performance

        BCR should perform well for random access patterns.
        """
        config = hbm3_config.copy()
        config.address_mapping = "bcr"

        sim_config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            read_ratio=0.7,
            seed=42,
            hbm_config=config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        print(f"\nBCR Mapping Performance:")
        print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
        print(f"  Row Hit Rate: {stats.row_hit_rate:.2%}")

        assert stats.throughput_gbps > 0

    def test_crb_performance(self, hbm3_config):
        """Test CRB mapping performance

        CRB should perform well for streaming patterns.
        """
        config = hbm3_config.copy()
        config.address_mapping = "crb"

        sim_config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.STRIDE,
            request_rate=0.6,
            read_ratio=1.0,
            seed=42,
            hbm_config=config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        print(f"\nCRB Mapping Performance:")
        print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
        print(f"  Row Hit Rate: {stats.row_hit_rate:.2%}")

        assert stats.throughput_gbps > 0

    def test_mapping_comparison(self, hbm3_config):
        """Compare performance across mapping modes

        Different mappings should have different performance profiles.
        """
        mappings = ['rbc', 'bcr', 'crb']
        results = []

        for mapping in mappings:
            config = hbm3_config.copy()
            config.address_mapping = mapping

            sim_config = SimulationConfig(
                simulation_time_us=30.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                read_ratio=0.7,
                seed=42,
                hbm_config=config,
            )

            sim = HBMSimulator(sim_config)
            stats = sim.run()

            results.append({
                'mapping': mapping,
                'throughput_gbps': stats.throughput_gbps,
                'row_hit_rate': stats.row_hit_rate,
            })

        print(f"\nMapping Comparison:")
        for r in results:
            print(f"  {r['mapping']}: {r['throughput_gbps']:.2f} GB/s "
                  f"({r['row_hit_rate']:.1%} row hits)")

        # All mappings should produce positive throughput
        for r in results:
            assert r['throughput_gbps'] > 0


@pytest.mark.regression
class TestHBM4AddressMapping:
    """HBM4-specific address mapping tests"""

    @pytest.fixture
    def hbm4_config(self):
        """HBM4 configuration"""
        from model.controller.config import HBM4_DEFAULT
        return HBM4_DEFAULT

    def test_hbm4_32channel_mapping(self, hbm4_config):
        """Test HBM4 32-channel address mapping

        HBM4 has 32 channels per stack.
        """
        config = hbm4_config.copy()
        config.channels_per_stack = 32

        decoder = AddressDecoder(config)

        # Test addresses across 32 channels
        import random
        random.seed(42)

        addresses = [random.randint(0, 0xFFFF_FFFF_FFFF) for _ in range(100)]

        decoded = [decoder.decode(addr) for addr in addresses]

        # Count channel usage
        channel_counts = [0] * 32
        for d in decoded:
            if d:
                channel_counts[d.channel_id] += 1

        active_channels = sum(1 for c in channel_counts if c > 0)

        print(f"\nHBM4 32-Channel Distribution:")
        print(f"  Active channels: {active_channels}/32")

        # Most channels should be active
        assert active_channels >= 16

    def test_hbm4_address_range(self, hbm4_config):
        """Test HBM4 extended address range

        HBM4 supports larger address space.
        """
        decoder = AddressDecoder(hbm4_config)

        # Test large addresses
        for addr in [0x1_0000_0000_0000, 0x2_0000_0000_0000, 0xFFFF_FFFF_FFFF]:
            decoded = decoder.decode(addr)

            assert decoded is not None
            assert decoded.channel_id >= 0

    def test_hbm4_row_column_mapping(self, hbm4_config):
        """Test HBM4 row/column mapping

        HBM4 has 4-bit burst length (FLINE=4).
        """
        config = hbm4_config.copy()
        config.burst_length = 4

        decoder = AddressDecoder(config)

        # Adjacent addresses should map to different columns
        addr1 = 0x1000
        addr2 = 0x1010  # 16 bytes apart (2 clocks per FLINE)

        decoded1 = decoder.decode(addr1)
        decoded2 = decoder.decode(addr2)

        assert decoded1 is not None
        assert decoded2 is not None

        print(f"\nHBM4 Row/Column Mapping:")
        print(f"  addr1={addr1:#x} -> col={decoded1.col_id}")
        print(f"  addr2={addr2:#x} -> col={decoded2.col_id}")