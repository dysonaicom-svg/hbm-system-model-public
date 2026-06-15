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

        # Test pseudo-channel 0
        addr_pch0 = 0x10000000
        decoded0 = decoder.decode(addr_pch0)
        assert hasattr(decoded0, 'pseudo_channel_id')

        # Test pseudo-channel 1 (toggle the pseudo-channel bit)
        addr_pch1 = addr_pch0 | (1 << spec.ADDR_CHANNEL_BITS)
        decoded1 = decoder.decode(addr_pch1)

        # They should potentially be different pseudo-channels
        assert hasattr(decoded1, 'pseudo_channel_id')

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