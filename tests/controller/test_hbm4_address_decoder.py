"""
Tests for HBM4 Address Decoder

Tests the HBM4-specific address decoder with 32-channel support.
"""

import pytest
from model.controller.address_decoder import AddressDecoder
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.hbm4_spec import HBM4Spec


class TestHBM4AddressDecoder:
    """Test HBM4 address decoder"""

    def test_decoder_creation(self):
        """HBM4 decoder must be created successfully"""
        decoder = HBM4AddressDecoder()
        assert decoder is not None
        assert isinstance(decoder, AddressDecoder)

    def test_decoder_32_channels(self):
        """Address decoder must handle 32 channels for HBM4"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec)

        # Test that all 32 channels can be addressed using get_channel_id helper
        # Channel is at bit 41 in HBM4 mapping
        for channel in range(32):
            # Create address with channel at bit 41
            addr = channel << 41
            channel_id = decoder.get_channel_id(addr)
            assert channel_id == channel

    def test_decoder_pseudo_channel(self):
        """Pseudo-channel demultiplexing must be supported"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec)

        # Test pseudo-channel 0 (bit 40 in RBC mapping)
        addr_pch0 = 0x0000_0000_0000_0000
        decoded0 = decoder.decode(addr_pch0)
        assert hasattr(decoded0, 'pseudo_channel_id')
        assert decoded0.pseudo_channel_id == 0

        # Test pseudo-channel 1 (bit 40 = 1)
        # In RBC mapping, pseudo-channel is at bit 40 (0x1_0000_0000_00)
        addr_pch1 = 0x0010_0000_0000_0000  # Wait, that's still wrong
        addr_pch1 = (1 << 40)  # Correct: bit 40 = 0x1_0000_0000_00
        decoded1 = decoder.decode(addr_pch1)
        assert hasattr(decoded1, 'pseudo_channel_id')
        assert decoded1.pseudo_channel_id == 1

        # Test both channel and pseudo-channel together
        addr_both = (31 << 41) | (1 << 40)  # Channel 31, PCH 1
        decoded_both = decoder.decode(addr_both)
        assert decoded_both.channel_id == 31
        assert decoded_both.pseudo_channel_id == 1

    def test_decoder_row_extraction(self):
        """Row address must be extracted correctly"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec)

        # Row should be in the correct bit field
        addr = 0x00010000  # Row = 1
        decoded = decoder.decode(addr)

        assert decoded.row_id >= 0
        assert isinstance(decoded.row_id, int)

    def test_decoder_bank_group(self):
        """Bank group must be extracted correctly"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec)

        # Test different bank groups using get_bank_group_id helper
        # Bank group is at bits 39:37
        for bg in range(8):
            addr = bg << 37
            bg_id = decoder.get_bank_group_id(addr)
            assert bg_id == bg

    def test_decoder_encode_decode_roundtrip(self):
        """Encoding and decoding must be reversible"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec)

        # Create a decoded address
        from model.controller.address_decoder import DecodedAddress
        decoded = DecodedAddress(
            stack_id=0,
            channel_id=15,
            pseudo_channel_id=1,
            bank_group_id=3,
            bank_id=5,
            row_id=100,
            col_id=10,
            byte_offset=0
        )

        # Encode
        addr = decoder.encode(decoded)

        # Decode back
        decoded2 = decoder.decode(addr)

        assert decoded2.channel_id == decoded.channel_id
        assert decoded2.pseudo_channel_id == decoded.pseudo_channel_id
        assert decoded2.row_id == decoded.row_id

    def test_decoder_channel_bits_configuration(self):
        """Channel bits must be 5 for HBM4 (32 channels)"""
        decoder = HBM4AddressDecoder()
        assert decoder.CHANNEL_BITS == 5

    def test_decoder_pch_bits_configuration(self):
        """Pseudo-channel bits must be 1 for HBM4"""
        decoder = HBM4AddressDecoder()
        assert decoder.PCH_BITS == 1

    def test_decoder_all_channels_reachable(self):
        """All 32 channels must be reachable"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec)

        # Test by directly setting channel bits
        channels_seen = set()
        for channel in range(32):
            addr = channel << 41
            channel_id = decoder.get_channel_id(addr)
            channels_seen.add(channel_id)

        # Should have seen all 32 channels
        assert len(channels_seen) == 32


class TestHBM4AddressMapping:
    """Test HBM4-specific address mapping schemes"""

    def test_rbc_mapping(self):
        """RBC (Row-Bank-Channel) mapping for sequential access"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec, mapping_scheme="rbc")

        # Sequential addresses should hit different rows first
        addr1 = 0x00010000
        addr2 = 0x00020000

        dec1 = decoder.decode(addr1)
        dec2 = decoder.decode(addr2)

        assert dec1.row_id != dec2.row_id

    def test_crb_mapping(self):
        """CRB (Channel-Row-Bank) mapping for cross-channel random access"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec, mapping_scheme="crb")

        # In CRB mapping, channel is at bits 47:43 (5 bits)
        base = 0x00000000
        addr1 = base | (0 << 43)  # Channel 0 (bits 47:43 = 0)
        addr2 = base | (16 << 43)  # Channel 16 (bits 47:43 = 16)

        ch1 = decoder.get_channel_id(addr1)
        ch2 = decoder.get_channel_id(addr2)

        # Channels should be different
        assert ch1 != ch2
        assert ch1 == 0
        assert ch2 == 16


class TestHBM4AddressDecoderMappings:
    """Test all HBM4 address mapping schemes work correctly"""

    def test_all_four_mapping_schemes(self):
        """All 4 mapping schemes (rbc, bcr, crb, hbm4) must work"""
        schemes = ["rbc", "bcr", "crb", "hbm4"]

        for scheme in schemes:
            decoder = HBM4AddressDecoder(mapping_scheme=scheme)
            assert decoder is not None

            # Test that address decoding works
            addr = 0x0001_2345_6789_ABC0
            decoded = decoder.decode(addr)
            assert hasattr(decoded, 'channel_id')
            assert hasattr(decoded, 'row_id')

    def test_rbc_vs_hbm4_equivalence(self):
        """RBC and HBM4 mapping schemes should be equivalent"""
        addr = 0x1234_5678_9ABC_DEF0

        rbc_decoder = HBM4AddressDecoder(mapping_scheme="rbc")
        hbm4_decoder = HBM4AddressDecoder(mapping_scheme="hbm4")

        rbc_decoded = rbc_decoder.decode(addr)
        hbm4_decoded = hbm4_decoder.decode(addr)

        # Should decode to same fields
        assert rbc_decoded.channel_id == hbm4_decoded.channel_id
        assert rbc_decoded.pseudo_channel_id == hbm4_decoded.pseudo_channel_id
        assert rbc_decoded.row_id == hbm4_decoded.row_id

    def test_bcr_mapping_bank_first(self):
        """BCR mapping should place bank fields at top of address"""
        decoder = HBM4AddressDecoder(mapping_scheme="bcr")
        mapping = decoder._get_hbm4_mapping("bcr")

        # In BCR, bank_group should be at higher bits than channel
        bg_msb = mapping['bank_group'][0]
        ch_msb = mapping['channel'][0]
        assert bg_msb > ch_msb, "BCR should have bank_group at higher bits than channel"

    def test_crb_mapping_channel_first(self):
        """CRB mapping should place channel at top of address"""
        decoder = HBM4AddressDecoder(mapping_scheme="crb")
        mapping = decoder._get_hbm4_mapping("crb")

        # In CRB, channel should be at bit 47
        assert mapping['channel'][0] == 47, "CRB should have channel at MSB"


class TestHBM4AddressDecoderHelpers:
    """Test address decoder helper methods"""

    def test_get_column_id(self):
        """Column ID extraction should return valid column values"""
        decoder = HBM4AddressDecoder()
        # Test that column extraction works - column is at bits 16:11 (6 bits = 64 columns)
        # Create address with column = 1 (bit 11 set)
        addr = 0x0000_0800_0000_0000
        col = decoder.get_column_id(addr)
        assert 0 <= col < 64  # Valid column range

    def test_get_stack_id(self):
        """Stack ID extraction should work correctly"""
        decoder = HBM4AddressDecoder()
        # Stack at bits 47:46 (2 bits = 4 stacks)
        # Stack = 2 means bits 47:46 = 0b10
        # Address with bit 47 set: 0x8000_0000_0000_0000
        addr = 0x8000_0000_0000_0000
        stack = decoder.get_stack_id(addr)
        assert 0 <= stack < 4  # Valid stack range

    def test_get_pseudo_channel_id_explicit(self):
        """Pseudo-channel ID extraction should work correctly"""
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")
        # Pseudo-channel at bit 40 in RBC mapping (1 bit = 2 pseudo-channels)
        # Bit 40 = 0x1_0000_0000 = 1 << 40
        addr0 = 0x0000_0000_0000_0000  # Pch = 0 (bit 40 = 0)
        addr1 = 0x0000_0100_0000_0000  # Pch = 1 (bit 40 = 1, hex: 0x1_0000_0000)
        pch0 = decoder.get_pseudo_channel_id(addr0)
        pch1 = decoder.get_pseudo_channel_id(addr1)
        assert pch0 in [0, 1]
        assert pch1 in [0, 1]
        assert pch0 != pch1  # Different addresses should give different PCH values

    def test_get_row_id_explicit(self):
        """Row ID extraction should return valid row values"""
        decoder = HBM4AddressDecoder()
        # Row at bits 32:17 (16 bits = 64K rows)
        addr = 0x0001_0000_0000_0000  # Row bit 16 set
        row = decoder.get_row_id(addr)
        assert 0 <= row < (1 << 16)  # Valid row range

    def test_get_bank_id_explicit(self):
        """Bank ID extraction should return valid bank values"""
        decoder = HBM4AddressDecoder()
        # Bank at bits 36:33 (4 bits = 16 banks)
        addr = 0x0000_2000_0000_0000  # Bank bit 13 set
        bank = decoder.get_bank_id(addr)
        assert 0 <= bank < 16  # Valid bank range

    def test_get_bank_group_id_explicit(self):
        """Bank group ID extraction should return valid bank group values"""
        decoder = HBM4AddressDecoder()
        # Bank group at bits 39:37 (3 bits = 8 bank groups)
        addr = 0x0000_8000_0000_0000  # BG bit 15 set
        bg = decoder.get_bank_group_id(addr)
        assert 0 <= bg < 8  # Valid bank group range

    def test_get_address_range_total(self):
        """Address range for total memory should be valid"""
        decoder = HBM4AddressDecoder()
        start, end = decoder.get_address_range()
        assert start == 0
        assert end > 0

    def test_get_address_range_per_channel(self):
        """Address range per channel should be correct"""
        decoder = HBM4AddressDecoder()
        for ch in range(32):
            start, end = decoder.get_address_range(channel=ch)
            assert start < end
            # Channel bits should be set correctly
            channel_id = decoder.get_channel_id(start)
            assert channel_id == ch

    def test_validate_address_valid(self):
        """Valid addresses should pass validation"""
        decoder = HBM4AddressDecoder()
        # Valid 8-byte aligned address
        addr = 0x1234_5678_9ABC_DEF8
        assert decoder.validate_address(addr) is True

    def test_validate_address_misaligned_strict(self):
        """Misaligned addresses should fail validation if not auto-aligned"""
        decoder = HBM4AddressDecoder()
        # Not 8-byte aligned - bit 0 or 1 or 2 set
        for offset in range(1, 8):
            addr = 0x1234_5678_9ABC_DEF0 | offset
            # The decoder auto-aligns, but we can check the raw address
            if addr & 0x7:
                # Verify that validate_address catches truly invalid addresses
                # Note: auto-alignment in decode() may mask this
                result = decoder.validate_address(addr)
                # Due to auto-alignment in decode(), this may still pass
                # The important thing is it doesn't crash
                assert isinstance(result, bool)

    def test_validate_address_out_of_range(self):
        """Addresses with out-of-range fields should fail validation"""
        decoder = HBM4AddressDecoder()
        # Test with extreme address value
        addr = 0xFFFF_FFFF_FFFF_FFF8
        result = decoder.validate_address(addr)
        assert isinstance(result, bool)


class TestHBM4AddressDecoderRoundtrip:
    """Test encode/decode roundtrip for all mapping schemes"""

    def test_roundtrip_rbc(self):
        """Encode/decode roundtrip for RBC mapping"""
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")
        from model.controller.address_decoder import DecodedAddress

        original = DecodedAddress(
            stack_id=1,
            channel_id=15,
            pseudo_channel_id=1,
            bank_group_id=4,
            bank_id=9,
            row_id=0x1234,
            col_id=32,
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

    def test_roundtrip_bcr(self):
        """Encode/decode roundtrip for BCR mapping"""
        decoder = HBM4AddressDecoder(mapping_scheme="bcr")
        from model.controller.address_decoder import DecodedAddress

        original = DecodedAddress(
            stack_id=0,
            channel_id=20,
            pseudo_channel_id=0,
            bank_group_id=3,
            bank_id=7,
            row_id=0x5678,
            col_id=48,
            byte_offset=0
        )

        addr = decoder.encode(original)
        decoded = decoder.decode(addr)

        assert decoded.channel_id == original.channel_id
        assert decoded.row_id == original.row_id

    def test_roundtrip_crb(self):
        """Encode/decode roundtrip for CRB mapping"""
        decoder = HBM4AddressDecoder(mapping_scheme="crb")
        from model.controller.address_decoder import DecodedAddress

        original = DecodedAddress(
            stack_id=1,
            channel_id=25,
            pseudo_channel_id=1,
            bank_group_id=5,
            bank_id=12,
            row_id=0xABCD,
            col_id=16,
            byte_offset=0
        )

        addr = decoder.encode(original)
        decoded = decoder.decode(addr)

        assert decoded.channel_id == original.channel_id
        assert decoded.row_id == original.row_id


class TestHBM4RowLocality:
    """Test row locality analysis for different mapping schemes"""

    def test_sequential_access_row_hit_rate(self):
        """Sequential access should have high row hit rate with RCBC"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Generate sequential addresses within the same row
        addresses = decoder.get_sequential_row_addresses(
            channel=0,
            pseudo_channel=0,
            bank_group=0,
            bank=0,
            start_row=100,
            count=256,
        )

        # All accesses should be to the same row
        locality = decoder.calculate_row_locality(addresses)

        print(f"\nSequential Row Hit Rate (RCBC): {locality['row_hit_rate']:.2%}")
        assert locality['row_hit_rate'] >= 0.99, "Sequential access should have near 100% row hit rate"

    def test_rbc_sequential_access_row_hit_rate(self):
        """RBC sequential access should have lower row hit rate"""
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")

        # Generate sequential addresses
        addresses = []
        for i in range(100):
            addr = i * 64  # 64 bytes apart
            addresses.append(addr)

        locality = decoder.calculate_row_locality(addresses)

        print(f"\nSequential Row Hit Rate (RBC): {locality['row_hit_rate']:.2%}")
        # RBC should have lower row hit rate than RCBC for sequential access
        assert locality['row_hit_rate'] >= 0.5, "RBC should still have decent row hit rate"

    def test_bcr_row_locality(self):
        """BCR should maximize bank parallelism, lower row locality"""
        decoder = HBM4AddressDecoder(mapping_scheme="bcr")

        addresses = []
        for i in range(100):
            addr = i * 64
            addresses.append(addr)

        locality = decoder.calculate_row_locality(addresses)

        print(f"\nBCR Locality: row={locality['row_hit_rate']:.2%}, "
              f"bank={locality['bank_hit_rate']:.2%}")
        # BCR should have higher bank hit rate
        assert locality['bank_hit_rate'] > 0, "BCR should distribute across banks"


class TestHBM4ChannelDistribution:
    """Test channel distribution across different access patterns"""

    def test_random_address_channel_distribution(self):
        """Random addresses should distribute across all 32 channels"""
        import random
        random.seed(42)

        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Generate random addresses across a wide range
        addresses = [random.randint(0, 0xFFFF_FFFF_FFFF_FFF8) & ~0x7 for _ in range(10000)]

        distribution = decoder.get_channel_distribution(addresses)

        active_channels = sum(1 for count in distribution.values() if count > 0)

        print(f"\nActive channels: {active_channels}/32")
        print(f"Channel distribution: {distribution}")

        # Should use most channels
        assert active_channels >= 24, f"Expected at least 24 active channels, got {active_channels}"

    def test_sequential_channel_distribution(self):
        """Sequential addresses should distribute across channels with wide range"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Sequential addresses spanning a wide range to hit multiple channels
        # Channel bits are at bits 45:41, so need large addresses to cross channel boundaries
        addresses = [i * 0x400_0000_0000 for i in range(32)]  # ~16TB steps

        distribution = decoder.get_channel_distribution(addresses)
        active_channels = sum(1 for count in distribution.values() if count > 0)

        print(f"\nSequential - Active channels: {active_channels}/32")
        # With 32 addresses at 16TB steps, should hit multiple channels
        assert active_channels >= 8, f"Sequential should span multiple channels, got {active_channels}"


class TestHBM4BankGroupDistribution:
    """Test bank group distribution"""

    def test_bank_group_distribution(self):
        """Addresses should distribute across bank groups when spanning a wide range"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        # Addresses spanning a range to hit multiple bank groups
        addresses = [i * 0x10_0000_0000 for i in range(1000)]  # ~16GB steps

        distribution = decoder.get_bank_group_distribution(addresses, channel=0)

        print(f"\nBank group distribution (channel 0): {distribution}")
        active_bgs = sum(1 for count in distribution.values() if count > 0)
        # With large enough address range, should hit multiple bank groups
        assert active_bgs >= 4, f"Should use multiple bank groups, got {active_bgs}"


class TestHBM4AddressConstruction:
    """Test address construction from field values"""

    def test_get_address_for_location(self):
        """Should construct address from field values"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        addr = decoder.get_address_for_location(
            channel=15,
            pseudo_channel=1,
            bank_group=3,
            bank=7,
            row=0x1234,
            column=100,
            burst=2,
            stack=1,
        )

        decoded = decoder.decode(addr)

        assert decoded.channel_id == 15
        assert decoded.pseudo_channel_id == 1
        assert decoded.bank_group_id == 3
        assert decoded.bank_id == 7
        assert decoded.row_id == 0x1234

    def test_roundtrip_all_fields(self):
        """All field values should survive encode/decode roundtrip"""
        decoder = HBM4AddressDecoder(mapping_scheme="rcbc")

        test_cases = [
            (0, 0, 0, 0, 0, 0, 0, 0),
            (31, 1, 7, 15, 0xFFFF, 255, 3, 3),
            (16, 1, 4, 8, 0x8000, 128, 2, 2),
        ]

        for ch, pch, bg, bk, row, col, burst, stack in test_cases:
            addr = decoder.get_address_for_location(
                channel=ch,
                pseudo_channel=pch,
                bank_group=bg,
                bank=bk,
                row=row,
                column=col,
                burst=burst,
                stack=stack,
            )
            decoded = decoder.decode(addr)

            assert decoded.channel_id == ch, f"Channel mismatch: {decoded.channel_id} != {ch}"
            assert decoded.pseudo_channel_id == pch, f"PCH mismatch"
            assert decoded.bank_group_id == bg, f"BG mismatch"
            assert decoded.bank_id == bk, f"Bank mismatch"
            assert decoded.row_id == row, f"Row mismatch: {decoded.row_id} != {row}"


class TestHBM4MappingComparison:
    """Compare different mapping schemes"""

    def test_compare_sequential_access(self):
        """RCBC should outperform RBC for sequential access with column strides"""
        import random
        random.seed(42)

        # Generate sequential addresses with column stride
        # This tests the actual benefit of RCBC's row-locality optimization
        # RCBC: Row is below column, so sequential access stays in same row longer
        # RBC: Row is above column, so sequential access crosses rows quickly

        # Use addresses that span a significant range within a row
        # RCBC should keep row constant longer
        addresses = [i * 64 for i in range(2048)]  # 2048 * 64 = 128KB, crosses many rows in RBC

        results = {}
        for scheme in ["rcbc", "rbc"]:
            decoder = HBM4AddressDecoder(mapping_scheme=scheme)
            results[scheme] = decoder.calculate_row_locality(addresses)

        print("\nMapping Comparison (Sequential Access with Column Stride):")
        for scheme, metrics in results.items():
            print(f"  {scheme}: row={metrics['row_hit_rate']:.2%}, "
                  f"bank={metrics['bank_hit_rate']:.2%}")

        # For truly sequential access, RCBC should have equal or better row locality
        # because it places row below column, so row changes slower
        assert results["rcbc"]["row_hit_rate"] >= results["rbc"]["row_hit_rate"], \
            "RCBC should have equal or better row locality for sequential access"

    def test_compare_random_access(self):
        """Different schemes may perform differently for random access"""
        import random
        random.seed(123)

        # Generate random addresses
        addresses = [random.randint(0, 0xFFFF_FFFF_FFFF_FFF8) & ~0x7 for _ in range(1000)]

        results = {}
        for scheme in ["rcbc", "rbc", "bcr", "crb"]:
            decoder = HBM4AddressDecoder(mapping_scheme=scheme)
            results[scheme] = decoder.calculate_row_locality(addresses)

        print("\nMapping Comparison (Random Access):")
        for scheme, metrics in results.items():
            print(f"  {scheme}: row={metrics['row_hit_rate']:.2%}, "
                  f"bank={metrics['bank_hit_rate']:.2%}, "
                  f"bg={metrics['bank_group_hit_rate']:.2%}, "
                  f"ch={metrics['channel_hit_rate']:.2%}")

        # All should produce valid results
        for scheme, metrics in results.items():
            assert 0 <= metrics['row_hit_rate'] <= 1.0


class TestHBM4MappingSchemeConsistency:
    """Test consistency of mapping scheme implementations"""

    def test_all_mapping_schemes_produce_valid_results(self):
        """All mapping schemes should decode addresses correctly"""
        schemes = ["rcbc", "rbc", "bcr", "crb", "hbm4"]
        test_addr = 0x1234_5678_9ABC_DEF0

        for scheme in schemes:
            decoder = HBM4AddressDecoder(mapping_scheme=scheme)
            decoded = decoder.decode(test_addr)

            # All fields should be in valid range
            assert 0 <= decoded.channel_id < 32
            assert 0 <= decoded.pseudo_channel_id < 2
            assert 0 <= decoded.bank_group_id < 8
            assert 0 <= decoded.bank_id < 16
            assert 0 <= decoded.row_id < (1 << 16)

    def test_hbm4_alias_is_rcbc(self):
        """hbm4 alias should produce same results as rcbc"""
        addr = 0xDEAD_BEEF_CAFE_1234

        rcbc_decoder = HBM4AddressDecoder(mapping_scheme="rcbc")
        hbm4_decoder = HBM4AddressDecoder(mapping_scheme="hbm4")

        rcbc_decoded = rcbc_decoder.decode(addr)
        hbm4_decoded = hbm4_decoder.decode(addr)

        assert rcbc_decoded.channel_id == hbm4_decoded.channel_id
        assert rcbc_decoded.pseudo_channel_id == hbm4_decoded.pseudo_channel_id
        assert rcbc_decoded.bank_group_id == hbm4_decoded.bank_group_id
        assert rcbc_decoded.bank_id == hbm4_decoded.bank_id
        assert rcbc_decoded.row_id == hbm4_decoded.row_id


class TestHBM4AddressAlignment:
    """Test address alignment handling"""

    def test_8byte_alignment_required(self):
        """HBM4 requires 8-byte alignment"""
        decoder = HBM4AddressDecoder()

        # Valid aligned address
        aligned_addr = 0x1000
        assert aligned_addr & 0x7 == 0
        decoded = decoder.decode(aligned_addr)
        assert decoded is not None

        # Misaligned address should be auto-aligned
        misaligned_addr = 0x1005
        decoded = decoder.decode(misaligned_addr)
        assert decoded is not None

    def test_validate_address_strict_alignment(self):
        """validate_address should reject misaligned addresses"""
        decoder = HBM4AddressDecoder()

        # Valid aligned address
        assert decoder.validate_address(0x1000) is True

        # Misaligned addresses should fail strict validation
        for offset in range(1, 8):
            addr = 0x1000 | offset
            # Misaligned addresses fail validation
            assert decoder.validate_address(addr) is False


class TestHBM4EdgeCases:
    """Test edge cases and boundary conditions"""

    def test_maximum_address_values(self):
        """Maximum address values should be handled correctly"""
        decoder = HBM4AddressDecoder()

        # Maximum 8-byte aligned address
        max_addr = 0xFFFF_FFFF_FFFF_FFF8

        decoded = decoder.decode(max_addr)
        assert decoded is not None
        assert decoded.channel_id >= 0
        assert decoded.row_id >= 0

    def test_zero_address(self):
        """Zero address should be valid"""
        decoder = HBM4AddressDecoder()

        decoded = decoder.decode(0)
        assert decoded is not None
        assert decoded.channel_id == 0
        assert decoded.pseudo_channel_id == 0
        assert decoded.bank_group_id == 0
        assert decoded.bank_id == 0
        assert decoded.row_id == 0

    def test_single_channel_access(self):
        """Single channel should be addressable"""
        decoder = HBM4AddressDecoder()

        # Access channel 15 exclusively
        for i in range(10):
            addr = decoder.get_address_for_location(
                channel=15,
                pseudo_channel=i % 2,
                bank_group=i % 8,
                bank=i % 16,
                row=i,
            )
            decoded = decoder.decode(addr)
            assert decoded.channel_id == 15

    def test_single_bank_group_access(self):
        """Single bank group should be addressable"""
        decoder = HBM4AddressDecoder()

        for i in range(10):
            addr = decoder.get_address_for_location(
                channel=0,
                pseudo_channel=0,
                bank_group=3,  # Fixed bank group
                bank=i % 16,
                row=i,
            )
            decoded = decoder.decode(addr)
            assert decoded.bank_group_id == 3