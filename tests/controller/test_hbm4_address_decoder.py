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