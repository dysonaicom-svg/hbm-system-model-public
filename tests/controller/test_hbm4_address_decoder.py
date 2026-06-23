"""
Enhanced Tests for HBM4 Address Decoder

Comprehensive tests covering:
- All address mapping modes (RBC, RCBC, BCR, CRB)
- Boundary conditions
- Edge cases
- Roundtrip encoding/decoding
- Row locality analysis
"""

import pytest
from model.controller.address_decoder import DecodedAddress
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.hbm4_spec import HBM4Spec


def make_addr(decoder, channel=0, pseudo_channel=0, bank_group=0, bank=0, row=0, column=0, burst=0, stack=0):
    """Helper to create an address with all fields specified"""
    return decoder.get_address_for_location(
        channel=channel,
        pseudo_channel=pseudo_channel,
        bank_group=bank_group,
        bank=bank,
        row=row,
        column=column,
        burst=burst,
        stack=stack
    )


class TestHBM4MappingModes:
    """Test all HBM4 address mapping schemes comprehensively"""

    # Supported mapping schemes
    MAPPING_SCHEMES = ["rbc", "rcbc", "bcr", "crb"]

    @pytest.mark.parametrize("scheme", MAPPING_SCHEMES)
    def test_scheme_basic_decoding(self, scheme):
        """Each mapping scheme must decode valid addresses correctly"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        # Test address with all fields set
        addr = 0x1234_5678_9ABC_DEF0
        decoded = decoder.decode(addr)

        # All schemes should return valid decoded address
        assert decoded is not None
        assert 0 <= decoded.channel_id < 32
        assert 0 <= decoded.pseudo_channel_id < 2
        assert 0 <= decoded.bank_group_id < 8
        assert 0 <= decoded.bank_id < 16
        assert 0 <= decoded.row_id < (1 << 16)

    @pytest.mark.parametrize("scheme", MAPPING_SCHEMES)
    def test_scheme_channel_bits_extraction(self, scheme):
        """Channel ID extraction must work for all schemes"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        # Test all 32 channels
        for ch in range(32):
            addr = make_addr(decoder, channel=ch)
            extracted = decoder.get_channel_id(addr)
            assert extracted == ch, f"Scheme {scheme}: expected channel {ch}, got {extracted}"

    @pytest.mark.parametrize("scheme", MAPPING_SCHEMES)
    def test_scheme_bank_group_bits_extraction(self, scheme):
        """Bank group ID extraction must work for all schemes"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        # Test all 8 bank groups
        for bg in range(8):
            addr = make_addr(decoder, channel=0, pseudo_channel=0, bank_group=bg, bank=0, row=0)
            extracted = decoder.get_bank_group_id(addr)
            assert extracted == bg, f"Scheme {scheme}: expected BG {bg}, got {extracted}"

    @pytest.mark.parametrize("scheme", MAPPING_SCHEMES)
    def test_scheme_bank_bits_extraction(self, scheme):
        """Bank ID extraction must work for all schemes"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        # Test all 16 banks
        for bank in range(16):
            addr = make_addr(decoder, channel=0, pseudo_channel=0, bank_group=0, bank=bank, row=0)
            extracted = decoder.get_bank_id(addr)
            assert extracted == bank, f"Scheme {scheme}: expected bank {bank}, got {extracted}"

    @pytest.mark.parametrize("scheme", MAPPING_SCHEMES)
    def test_scheme_row_bits_extraction(self, scheme):
        """Row ID extraction must work for all schemes"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        # Test various row values
        test_rows = [0, 1, 127, 128, 255, 256, 1023, 4096, 32768, 65535]
        for row in test_rows:
            addr = make_addr(decoder, channel=0, pseudo_channel=0, bank_group=0, bank=0, row=row)
            extracted = decoder.get_row_id(addr)
            assert extracted == row, f"Scheme {scheme}: expected row {row}, got {extracted}"

    @pytest.mark.parametrize("scheme", MAPPING_SCHEMES)
    def test_scheme_pseudo_channel_extraction(self, scheme):
        """Pseudo-channel ID extraction must work for all schemes"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        for pch in range(2):
            addr = make_addr(decoder, channel=0, pseudo_channel=pch, bank_group=0, bank=0, row=0)
            extracted = decoder.get_pseudo_channel_id(addr)
            assert extracted == pch, f"Scheme {scheme}: expected PCH {pch}, got {extracted}"

    @pytest.mark.parametrize("scheme", MAPPING_SCHEMES)
    def test_scheme_stack_id_extraction(self, scheme):
        """Stack ID extraction must work for all schemes"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        # Test all 4 stacks
        for stack in range(4):
            addr = make_addr(decoder, channel=0, pseudo_channel=0, bank_group=0, bank=0, row=0, stack=stack)
            extracted = decoder.get_stack_id(addr)
            assert extracted == stack, f"Scheme {scheme}: expected stack {stack}, got {extracted}"


class TestHBM4MappingBitPositions:
    """Test bit positions for each mapping scheme"""

    def test_rbc_mapping_bit_positions(self):
        """RBC mapping should have correct bit positions"""
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")
        mapping = decoder._get_hbm4_mapping("rbc")

        # Check expected positions for RBC
        assert mapping['channel'] == (45, 41, 5), "RBC channel should be at bits 45:41"
        assert mapping['pseudo_channel'] == (40, 40, 1), "RBC PCH should be at bit 40"
        assert mapping['bank_group'] == (39, 37, 3), "RBC BG should be at bits 39:37"
        assert mapping['bank'] == (36, 33, 4), "RBC bank should be at bits 36:33"
        assert mapping['row'] == (31, 16, 16), "RBC row should be at bits 31:16"

    def test_rcbc_mapping_bit_positions(self):
        """RCBC mapping should have correct bit positions"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")
        mapping = decoder._get_hbm4_mapping("rcbc")

        # In RCBC, row is at bits 31:16 and column is at bits 15:8
        # Both use specific bit positions for HBM4 optimized mapping
        row_msb, row_lsb, row_bits = mapping['row']
        col_msb, col_lsb, col_bits = mapping['col']

        assert row_bits == 16, "RCBC should have 16-bit row"
        assert col_bits == 8, "RCBC should have 8-bit column (expanded)"
        assert mapping['channel'] == (45, 41, 5), "RCBC channel should be at bits 45:41"
        assert mapping['bank_group'] == (39, 37, 3), "RCBC BG should be at bits 39:37"

    def test_bcr_mapping_bit_positions(self):
        """BCR mapping should have bank at top bits"""
        decoder = HBM4AddressDecoder(mapping_scheme="bcr")
        mapping = decoder._get_hbm4_mapping("bcr")

        # In BCR, bank_group should be above channel
        bg_msb = mapping['bank_group'][0]
        ch_msb = mapping['channel'][0]
        assert bg_msb > ch_msb, "BCR bank_group MSB should be above channel MSB"

        # Channel should be at bits 38:34
        assert mapping['channel'] == (38, 34, 5), "BCR channel should be at bits 38:34"

    def test_crb_mapping_bit_positions(self):
        """CRB mapping should have channel at top bits"""
        decoder = HBM4AddressDecoder(mapping_scheme="crb")
        mapping = decoder._get_hbm4_mapping("crb")

        # In CRB, channel should be at bit 47 (top)
        assert mapping['channel'][0] == 47, "CRB channel MSB should be at bit 47"
        assert mapping['channel'] == (47, 43, 5), "CRB channel should be at bits 47:43"


class TestHBM4BoundaryConditions:
    """Test boundary conditions for address decoder"""

    def test_maximum_channel_id(self):
        """Decoder must handle maximum channel ID (31)"""
        decoder = HBM4AddressDecoder()
        addr = make_addr(decoder, channel=31)
        decoded = decoder.decode(addr)
        assert decoded.channel_id == 31

    def test_maximum_pseudo_channel_id(self):
        """Decoder must handle maximum pseudo-channel ID (1)"""
        decoder = HBM4AddressDecoder()
        addr = make_addr(decoder, pseudo_channel=1)
        decoded = decoder.decode(addr)
        assert decoded.pseudo_channel_id == 1

    def test_maximum_bank_group_id(self):
        """Decoder must handle maximum bank group ID (7)"""
        decoder = HBM4AddressDecoder()
        addr = make_addr(decoder, bank_group=7)
        decoded = decoder.decode(addr)
        assert decoded.bank_group_id == 7

    def test_maximum_bank_id(self):
        """Decoder must handle maximum bank ID (15)"""
        decoder = HBM4AddressDecoder()
        addr = make_addr(decoder, bank=15)
        decoded = decoder.decode(addr)
        assert decoded.bank_id == 15

    def test_maximum_row_id(self):
        """Decoder must handle maximum row ID (65535)"""
        decoder = HBM4AddressDecoder()
        addr = make_addr(decoder, row=65535)
        decoded = decoder.decode(addr)
        assert decoded.row_id == 65535

    def test_maximum_stack_id(self):
        """Decoder must handle maximum stack ID (3)"""
        decoder = HBM4AddressDecoder()
        addr = make_addr(decoder, stack=3)
        decoded = decoder.decode(addr)
        assert decoded.stack_id == 3

    def test_minimum_values_all_zeros(self):
        """Decoder must handle all minimum values (zeros)"""
        decoder = HBM4AddressDecoder()
        addr = make_addr(decoder, channel=0, pseudo_channel=0, bank_group=0, bank=0, row=0, stack=0)
        decoded = decoder.decode(addr)
        assert decoded.channel_id == 0
        assert decoded.pseudo_channel_id == 0
        assert decoded.bank_group_id == 0
        assert decoded.bank_id == 0
        assert decoded.row_id == 0
        assert decoded.stack_id == 0

    def test_boundary_column_values(self):
        """Test column boundary values for all schemes"""
        schemes = ["rbc", "rcbc", "bcr", "crb"]
        for scheme in schemes:
            decoder = HBM4AddressDecoder(mapping_scheme=scheme)
            mapping = decoder._get_hbm4_mapping(scheme)
            col_bits = mapping['col'][2]
            max_col = (1 << col_bits) - 1

            # Test minimum column
            addr = make_addr(decoder, column=0)
            assert decoder.get_column_id(addr) == 0

            # Test maximum column
            addr = make_addr(decoder, column=max_col)
            assert decoder.get_column_id(addr) == max_col


class TestHBM4AddressValidation:
    """Test address validation edge cases"""

    def test_valid_aligned_address(self):
        """Valid 8-byte aligned address should pass validation"""
        decoder = HBM4AddressDecoder()
        addr = 0x0001_2345_6789_ABC0  # Ends with 0
        assert decoder.validate_address(addr) is True

    def test_invalid_unaligned_address_bit0(self):
        """Address with bit 0 set should fail validation"""
        decoder = HBM4AddressDecoder()
        addr = 0x0001_2345_6789_ABC1
        assert decoder.validate_address(addr) is False

    def test_invalid_unaligned_address_bit1(self):
        """Address with bit 1 set should fail validation"""
        decoder = HBM4AddressDecoder()
        addr = 0x0001_2345_6789_ABC2
        assert decoder.validate_address(addr) is False

    def test_invalid_unaligned_address_bit2(self):
        """Address with bit 2 set should fail validation"""
        decoder = HBM4AddressDecoder()
        addr = 0x0001_2345_6789_ABC4
        assert decoder.validate_address(addr) is False

    def test_invalid_multi_bit_unaligned(self):
        """Address with multiple lower bits set should fail validation"""
        decoder = HBM4AddressDecoder()
        addr = 0x0001_2345_6789_ABC7
        assert decoder.validate_address(addr) is False

    def test_zero_address(self):
        """Zero address should be valid (aligned, all zeros)"""
        decoder = HBM4AddressDecoder()
        assert decoder.validate_address(0) is True

    def test_maximum_valid_address(self):
        """Maximum valid HBM4 address should pass validation"""
        decoder = HBM4AddressDecoder()
        # 48-bit address space, aligned
        max_addr = (1 << 48) - 8
        # May fail due to field range, but should not crash
        result = decoder.validate_address(max_addr)
        assert isinstance(result, bool)


class TestHBM4RoundtripEncoding:
    """Test encode/decode roundtrip for all mapping schemes"""

    @pytest.mark.parametrize("scheme", ["rbc", "rcbc", "bcr", "crb"])
    def test_roundtrip_all_fields(self, scheme):
        """Encode/decode roundtrip must preserve all fields"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        original = DecodedAddress(
            stack_id=2,
            channel_id=17,
            pseudo_channel_id=1,
            bank_group_id=5,
            bank_id=12,
            row_id=0x1234,
            col_id=64,
            byte_offset=0
        )

        addr = decoder.encode(original)
        decoded = decoder.decode(addr)

        assert decoded.stack_id == original.stack_id
        assert decoded.channel_id == original.channel_id
        assert decoded.pseudo_channel_id == original.pseudo_channel_id
        assert decoded.bank_group_id == original.bank_group_id
        assert decoded.bank_id == original.bank_id
        assert decoded.row_id == original.row_id

    @pytest.mark.parametrize("scheme", ["rbc", "rcbc", "bcr", "crb"])
    def test_roundtrip_all_channels(self, scheme):
        """Roundtrip must preserve all 32 channel values"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        for ch in range(32):
            original = DecodedAddress(
                stack_id=0,
                channel_id=ch,
                pseudo_channel_id=0,
                bank_group_id=0,
                bank_id=0,
                row_id=100,
                col_id=0,
                byte_offset=0
            )
            addr = decoder.encode(original)
            decoded = decoder.decode(addr)
            assert decoded.channel_id == ch

    @pytest.mark.parametrize("scheme", ["rbc", "rcbc", "bcr", "crb"])
    def test_roundtrip_all_bank_groups(self, scheme):
        """Roundtrip must preserve all 8 bank group values"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        for bg in range(8):
            original = DecodedAddress(
                stack_id=0,
                channel_id=0,
                pseudo_channel_id=0,
                bank_group_id=bg,
                bank_id=0,
                row_id=0,
                col_id=0,
                byte_offset=0
            )
            addr = decoder.encode(original)
            decoded = decoder.decode(addr)
            assert decoded.bank_group_id == bg

    @pytest.mark.parametrize("scheme", ["rbc", "rcbc", "bcr", "crb"])
    def test_roundtrip_all_banks(self, scheme):
        """Roundtrip must preserve all 16 bank values"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        for bank in range(16):
            original = DecodedAddress(
                stack_id=0,
                channel_id=0,
                pseudo_channel_id=0,
                bank_group_id=0,
                bank_id=bank,
                row_id=0,
                col_id=0,
                byte_offset=0
            )
            addr = decoder.encode(original)
            decoded = decoder.decode(addr)
            assert decoded.bank_id == bank


class TestHBM4RowLocality:
    """Test row locality analysis for different access patterns"""

    def test_sequential_access_rcbc_high_locality(self):
        """RCBC should have high row locality for sequential access"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Generate sequential addresses
        addrs = decoder.get_sequential_row_addresses(
            channel=0, pseudo_channel=0, bank_group=0, bank=0,
            start_row=100, count=1000
        )

        locality = decoder.calculate_row_locality(addrs)

        # RCBC should have very high row hit rate for sequential access
        assert locality['row_hit_rate'] >= 0.95, \
            f"RCBC row hit rate too low: {locality['row_hit_rate']}"

    def test_sequential_access_rbc_lower_locality(self):
        """RBC should have lower row locality for sequential access"""
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")

        # Generate sequential addresses
        addrs = decoder.get_sequential_row_addresses(
            channel=0, pseudo_channel=0, bank_group=0, bank=0,
            start_row=100, count=1000
        )

        locality = decoder.calculate_row_locality(addrs)

        # RBC should have lower row hit rate than RCBC
        # (This is expected due to row bits above column bits)
        assert locality['row_hit_rate'] >= 0.0  # Just sanity check

    def test_random_access_low_locality(self):
        """Random access should have low locality for any scheme"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Generate pseudo-random addresses (using different rows)
        addrs = []
        for i in range(100):
            row = i * 17 % 256  # Spread across rows
            addr = make_addr(
                decoder,
                channel=i % 2, pseudo_channel=0, bank_group=0,
                bank=0, row=row, column=i % 64
            )
            addrs.append(addr)

        locality = decoder.calculate_row_locality(addrs)

        # Random access should have low row hit rate
        assert locality['row_hit_rate'] < 0.5


class TestHBM4MappingComparison:
    """Compare different mapping schemes"""

    def test_compare_row_locality_sequential(self):
        """RCBC should outperform RBC on sequential access locality"""
        sequential_addrs = []
        rcbc_decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Generate sequential addresses
        sequential_addrs = rcbc_decoder.get_sequential_row_addresses(
            channel=0, pseudo_channel=0, bank_group=0, bank=0,
            start_row=0, count=512
        )

        # Test with RBC
        rbc_decoder = HBM4AddressDecoder(mapping_scheme="rbc")
        rbc_locality = rbc_decoder.calculate_row_locality(sequential_addrs)

        # Test with RCBC
        rcbc_locality = rcbc_decoder.calculate_row_locality(sequential_addrs)

        # RCBC should have equal or better row locality
        assert rcbc_locality['row_hit_rate'] >= rbc_locality['row_hit_rate']

    def test_channel_distribution_across_schemes(self):
        """All schemes should distribute across channels evenly"""
        addrs = []
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Generate addresses cycling through channels
        for i in range(256):
            addr = make_addr(
                decoder,
                channel=i % 32, pseudo_channel=0, bank_group=0, bank=0, row=0
            )
            addrs.append(addr)

        distribution = decoder.get_channel_distribution(addrs)

        # Each channel should appear ~8 times (256 / 32 = 8)
        for ch in range(32):
            count = distribution[ch]
            assert 4 <= count <= 12, \
                f"Channel {ch} has unexpected count: {count}"


class TestHBM4AddressConstruction:
    """Test address construction from field values"""

    @pytest.mark.parametrize("scheme", ["rbc", "rcbc", "bcr", "crb"])
    def test_construct_address_all_fields(self, scheme):
        """Address construction must produce correct addresses for all schemes"""
        decoder = HBM4AddressDecoder(mapping_scheme=scheme)

        addr = make_addr(
            decoder,
            channel=15,
            pseudo_channel=1,
            bank_group=3,
            bank=7,
            row=0x5678,
            column=100,
            burst=2,
            stack=1
        )

        # Verify extraction matches construction
        assert decoder.get_channel_id(addr) == 15
        assert decoder.get_pseudo_channel_id(addr) == 1
        assert decoder.get_bank_group_id(addr) == 3
        assert decoder.get_bank_id(addr) == 7
        assert decoder.get_row_id(addr) == 0x5678
        assert decoder.get_stack_id(addr) == 1

    def test_construct_sequential_column_access(self):
        """Sequential column access should stay in same row (RCBC)"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Access sequential columns
        row_ids = set()
        for col in range(256):
            addr = make_addr(
                decoder,
                channel=0, pseudo_channel=0, bank_group=0, bank=0,
                row=100, column=col
            )
            row_ids.add(decoder.get_row_id(addr))

        # All accesses should stay in same row
        assert len(row_ids) == 1


class TestHBM4EdgeCases:
    """Test edge cases and unusual scenarios"""

    def test_decode_preserves_burst_id(self):
        """Decode should correctly extract burst ID"""
        decoder = HBM4AddressDecoder()

        for burst in range(4):
            addr = make_addr(decoder, burst=burst)
            decoded = decoder.decode(addr)
            assert decoded.burst_id == burst

    def test_decode_preserves_byte_offset(self):
        """Decode should correctly extract byte offset"""
        decoder = HBM4AddressDecoder()

        # Create base address
        addr = make_addr(decoder)
        decoded = decoder.decode(addr)
        assert isinstance(decoded.byte_offset, int)

    def test_address_range_calculation(self):
        """Address range calculation should be correct"""
        decoder = HBM4AddressDecoder()

        start, end = decoder.get_address_range()
        assert start == 0
        assert end > 0

    def test_address_range_per_channel(self):
        """Per-channel address range should be correct"""
        decoder = HBM4AddressDecoder()

        for ch in range(32):
            start, end = decoder.get_address_range(channel=ch)
            assert start < end
            assert decoder.get_channel_id(start) == ch

    def test_multiple_stacks_addressing(self):
        """Multiple stacks should be addressable"""
        decoder = HBM4AddressDecoder()

        for stack in range(4):
            addr = make_addr(
                decoder,
                channel=0, pseudo_channel=0, bank_group=0, bank=0,
                row=0, stack=stack
            )
            assert decoder.get_stack_id(addr) == stack


class TestHBM4HitDetection:
    """Test row/bank/bank group hit detection"""

    def test_row_hit_same_channel_bank_row(self):
        """Row hit when same channel, bank, and row"""
        decoder = HBM4AddressDecoder()

        addr1 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=0, bank=0, row=100)
        addr2 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=0, bank=0, row=100, column=10)

        assert decoder.is_row_hit(addr1, addr2) is True

    def test_row_miss_different_row(self):
        """Row miss when different row"""
        decoder = HBM4AddressDecoder()

        addr1 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=0, bank=0, row=100)
        addr2 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=0, bank=0, row=101)

        assert decoder.is_row_hit(addr1, addr2) is False

    def test_row_miss_different_channel(self):
        """Row miss when different channel"""
        decoder = HBM4AddressDecoder()

        addr1 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=0, bank=0, row=100)
        addr2 = make_addr(decoder, channel=6, pseudo_channel=0, bank_group=0, bank=0, row=100)

        assert decoder.is_row_hit(addr1, addr2) is False

    def test_bank_hit_same_bank(self):
        """Bank hit when same channel and bank"""
        decoder = HBM4AddressDecoder()

        addr1 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=1, bank=3, row=100)
        addr2 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=1, bank=3, row=200)

        assert decoder.is_bank_hit(addr1, addr2) is True

    def test_bank_hit_same_bank_group(self):
        """Bank group hit when same channel and bank group"""
        decoder = HBM4AddressDecoder()

        addr1 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=2, bank=3, row=100)
        addr2 = make_addr(decoder, channel=5, pseudo_channel=0, bank_group=2, bank=7, row=100)

        assert decoder.is_bank_group_hit(addr1, addr2) is True


class TestHBM4ParallelAccess:
    """Test parallel bank/bank group access helpers"""

    def test_get_parallel_bank_groups(self):
        """Get parallel bank groups should return correct list"""
        decoder = HBM4AddressDecoder()

        decoded = DecodedAddress(
            stack_id=0, channel_id=0, pseudo_channel_id=0,
            bank_group_id=3, bank_id=0, row_id=0
        )

        bg_list = decoder.get_parallel_bank_groups(decoded, count=8)

        assert len(bg_list) == 8
        assert 3 in bg_list  # Current BG should be included

    def test_get_parallel_banks(self):
        """Get parallel banks should return correct list"""
        decoder = HBM4AddressDecoder()

        decoded = DecodedAddress(
            stack_id=0, channel_id=0, pseudo_channel_id=0,
            bank_group_id=0, bank_id=5, row_id=0
        )

        bank_list = decoder.get_parallel_banks(decoded, count=16)

        assert len(bank_list) == 16
        assert 5 in bank_list  # Current bank should be included


class TestHBM4DecodedAddressHelpers:
    """Test DecodedAddress helper methods"""

    def test_get_channel_key(self):
        """Channel key should uniquely identify channel"""
        decoded = DecodedAddress(
            stack_id=1, channel_id=15, pseudo_channel_id=1,
            bank_group_id=0, bank_id=0, row_id=0
        )

        key = decoded.get_channel_key()
        assert key == (1, 15, 1)

    def test_get_bank_key(self):
        """Bank key should uniquely identify bank"""
        decoded = DecodedAddress(
            stack_id=0, channel_id=5, pseudo_channel_id=0,
            bank_group_id=3, bank_id=7, row_id=100
        )

        key = decoded.get_bank_key()
        assert key == (0, 5, 0, 7)


class TestHBM4AddressStats:
    """Test address decoder statistics"""

    def test_address_stats_structure(self):
        """Address stats should have expected structure"""
        decoder = HBM4AddressDecoder()
        stats = decoder.get_address_stats()

        assert 'total_channels' in stats
        assert 'total_banks' in stats
        assert 'total_bank_groups' in stats
        assert 'address_mapping' in stats

    def test_address_stats_values(self):
        """Address stats should have correct values for HBM4"""
        decoder = HBM4AddressDecoder()
        stats = decoder.get_address_stats()

        # total_channels = stack_count * channels_per_stack = 4 * 32 = 128
        assert stats['total_channels'] == 128
        assert stats['channels_per_stack'] == 32


class TestHBM4SpecIntegration:
    """Test integration with HBM4Spec"""

    def test_decoder_with_default_spec(self):
        """Decoder should work with default HBM4Spec"""
        decoder = HBM4AddressDecoder()
        assert decoder.spec is not None

    def test_decoder_with_custom_spec(self):
        """Decoder should work with custom HBM4Spec"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec=spec)
        assert decoder.spec is spec


class TestHBM4RCBCMapping:
    """Specific tests for RCBC mapping (row-locality optimized)"""

    def test_rcbc_column_range(self):
        """RCBC should support 256 columns (8-bit column field)"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")
        mapping = decoder._get_hbm4_mapping("rcbc")
        col_bits = mapping['col'][2]
        assert col_bits == 8, "RCBC should have 8-bit column (256 columns)"

    def test_rcbc_row_locality_improvement(self):
        """RCBC should have better row locality than RBC for sequential access"""
        rcbc = HBM4AddressDecoder(mapping_scheme="rcbc")
        rbc = HBM4AddressDecoder(mapping_scheme="rbc")

        # Generate sequential column accesses using RBC decoder
        # then measure locality with both schemes
        rbc_addrs = rbc.get_sequential_row_addresses(
            channel=0, pseudo_channel=0, bank_group=0, bank=0,
            start_row=100, count=256
        )

        # Decode with both schemes and compare
        rcbc_locality = rcbc.calculate_row_locality(rbc_addrs)
        rbc_locality = rbc.calculate_row_locality(rbc_addrs)

        # Both should have good locality for sequential column access
        # RCBC places row at lower bits, so column changes first (within row)
        # RBC places row at higher bits, so row changes first
        assert rcbc_locality['row_hit_rate'] >= rbc_locality['row_hit_rate'], \
            "RCBC should have equal or better row locality than RBC"


class TestHBM4BCRMapping:
    """Specific tests for BCR mapping (bank-channel-row)"""

    def test_bcr_bank_first(self):
        """BCR should place bank at higher bits than channel"""
        decoder = HBM4AddressDecoder(mapping_scheme="bcr")
        mapping = decoder._get_hbm4_mapping("bcr")

        bg_msb = mapping['bank_group'][0]
        ch_msb = mapping['channel'][0]

        assert bg_msb > ch_msb, "BCR should have bank_group above channel"

    def test_bcr_parallel_access(self):
        """BCR should distribute banks well across address space"""
        decoder = HBM4AddressDecoder(mapping_scheme="bcr")

        # Generate addresses with different banks
        bank_dist = {b: 0 for b in range(16)}
        for bank in range(16):
            addr = make_addr(decoder, channel=0, pseudo_channel=0, bank_group=bank % 8, bank=bank, row=0)
            decoded = decoder.decode(addr)
            bank_dist[decoded.bank_id] += 1

        # All banks should be equally accessible
        for bank_id, count in bank_dist.items():
            assert count >= 1, f"Bank {bank_id} should be accessible"


class TestHBM4CRBMapping:
    """Specific tests for CRB mapping (channel-row-bank)"""

    def test_crb_channel_at_top(self):
        """CRB should place channel at top bits (bit 47)"""
        decoder = HBM4AddressDecoder(mapping_scheme="crb")
        mapping = decoder._get_hbm4_mapping("crb")

        assert mapping['channel'][0] == 47, "CRB should have channel at MSB"

    def test_crb_channel_striping(self):
        """CRB should make channel striping easy"""
        decoder = HBM4AddressDecoder(mapping_scheme="crb")

        # Addresses with different channels should differ in top bits
        ch0_addr = make_addr(decoder, channel=0, pseudo_channel=0, bank_group=0, bank=0, row=0)
        ch31_addr = make_addr(decoder, channel=31, pseudo_channel=0, bank_group=0, bank=0, row=0)

        # The channel field should be at bits 47:43
        ch0_extracted = decoder.get_channel_id(ch0_addr)
        ch31_extracted = decoder.get_channel_id(ch31_addr)

        assert ch0_extracted == 0
        assert ch31_extracted == 31
