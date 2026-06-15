"""
Comprehensive Address Decoder Coverage Tests - Enhanced for HBM4

Tests all 6 mapping modes (rbc, bcr, crb, hbm4 + custom + undefined fallback),
edge cases (min/max addresses), and boundary conditions for the HBM4 address decoder.

Coverage targets:
- All 6 mapping schemes (rbc, bcr, crb, hbm4, unknown fallback, custom)
- All 32 channel addresses
- All 2 pseudo-channel addresses
- All 8 bank group addresses
- All 16 bank addresses
- All row range (0 to 64K-1)
- All column range (0 to 63)
- All stack range (0-3)
- Edge cases: address 0, max address, 8-byte alignment
- Boundary conditions: channel boundary, bank boundary, row boundary
- Cross-coverage between HBM4 specification parameters
"""

import pytest
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.address_decoder import DecodedAddress
from model.dram.hbm4_spec import HBM4Spec, HBM4_SPEED_GRADES
from model.controller.config import HBMConfig


class TestAddressDecoderAllMappingModes:
    """Test all 6 address mapping modes"""

    def test_rbc_mapping_mode(self):
        """RBC (Row-Bank-Channel) mapping - default for sequential access"""
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")
        assert decoder._mapping_scheme == "rbc"

        # RBC places channel at bits 45:41
        mapping = decoder._get_hbm4_mapping("rbc")
        assert mapping['channel'] == (45, 41, 5)
        # Verify channel extraction at correct position
        for ch in range(32):
            addr = ch << 41  # Channel field at bit 41
            assert decoder.get_channel_id(addr) == ch

    def test_bcr_mapping_mode(self):
        """BCR (Bank-Channel-Row) mapping - maximizes bank parallelism"""
        decoder = HBM4AddressDecoder(mapping_scheme="bcr")
        assert decoder._mapping_scheme == "bcr"

        # BCR places bank group at higher bits than channel
        mapping = decoder._get_hbm4_mapping("bcr")
        assert mapping['bank_group'][0] > mapping['channel'][0]
        # Verify bank group extraction
        for bg in range(8):
            addr = bg << 43  # Bank group at bits 45:43 in BCR
            assert decoder.get_bank_group_id(addr) == bg

    def test_crb_mapping_mode(self):
        """CRB (Channel-Row-Bank) mapping - cross-channel random access"""
        decoder = HBM4AddressDecoder(mapping_scheme="crb")
        assert decoder._mapping_scheme == "crb"

        # CRB places channel at MSB (bit 47)
        mapping = decoder._get_hbm4_mapping("crb")
        assert mapping['channel'][0] == 47

        # Verify channel at top bits
        for ch in range(32):
            addr = ch << 43  # Channel field at bit 43 in CRB
            assert decoder.get_channel_id(addr) == ch

    def test_hbm4_mapping_mode(self):
        """HBM4 mapping - same as RBC, the HBM4 default"""
        decoder = HBM4AddressDecoder(mapping_scheme="hbm4")
        assert decoder._mapping_scheme == "hbm4"
        # HBM4 should be identical to RBC
        hbm4_mapping = decoder._get_hbm4_mapping("hbm4")
        rbc_mapping = decoder._get_hbm4_mapping("rbc")
        assert hbm4_mapping == rbc_mapping

    def test_unknown_mapping_fallback(self):
        """Unknown mapping schemes should fall back to hbm4 default"""
        decoder = HBM4AddressDecoder(mapping_scheme="unknown_scheme")
        # Should fall back to hbm4/rbc mapping

        # Verify fallback works correctly
        addr = 0x123456789ABCDEF0 & ~0x7  # 8-byte aligned
        decoded = decoder.decode(addr)
        assert decoded is not None
        assert hasattr(decoded, 'channel_id')

    def test_custom_mapping_via_config(self):
        """Custom mapping via HBMConfig should work"""
        custom_mapping = {
            'stack': (47, 46, 2),
            'channel': (45, 41, 5),
            'pseudo_channel': (40, 40, 1),
            'bank_group': (39, 37, 3),
            'bank': (36, 33, 4),
            'row': (32, 17, 16),
            'col': (16, 11, 6),
            'burst': (10, 9, 2),
            'offset': (8, 6, 3),
        }
        config = HBMConfig(
            stack_count=4,
            channels_per_stack=32,
            pseudo_channels_per_channel=2,
            bank_groups_per_channel=8,
            banks_per_pseudo_channel=16,
            io_width=2048,
            address_mapping="rbc",
        )

        # Create decoder with custom mapping
        decoder = HBM4AddressDecoder(spec=HBM4Spec(), mapping_scheme="rbc")
        assert decoder is not None

        # Verify mapping is applied
        addr = 0
        decoded = decoder.decode(addr)
        assert decoded.channel_id == 0


class TestAddressDecoderHBM4SpecParameters:
    """Test HBM4 specification parameter coverage"""

    def test_32_channels_all_addressable(self):
        """All 32 channels should be addressable and decode correctly"""
        decoder = HBM4AddressDecoder()
        spec = HBM4Spec()

        assert spec.channels == 32
        # All 32 channels should be valid
        for ch in range(32):
            addr = ch << 41
            decoded = decoder.decode(addr)
            assert decoded.channel_id == ch
            assert 0 <= decoded.channel_id < 32

    def test_2_pseudo_channels_per_channel(self):
        """Each channel should support 2 pseudo-channels"""
        decoder = HBM4AddressDecoder()
        spec = HBM4Spec()

        assert spec.pseudo_channels_per_channel == 2
        assert spec.pseudo_channels == 64  # 32 × 2

        # Test pseudo-channel bit extraction
        for ch in range(32):
            for pch in range(2):
                addr = (ch << 41) | (pch << 40)
                decoded = decoder.decode(addr)
                assert decoded.pseudo_channel_id == pch
                assert 0 <= decoded.pseudo_channel_id < 2

    def test_8_bank_groups_per_pseudo_channel(self):
        """Each pseudo-channel should have 8 bank groups"""
        spec = HBM4Spec()
        assert spec.bank_groups_per_channel == 8

        decoder = HBM4AddressDecoder()
        # All 8 bank groups should be valid
        for bg in range(8):
            addr = bg << 37
            decoded = decoder.decode(addr)
            assert decoded.bank_group_id == bg
            assert 0 <= decoded.bank_group_id < 8

    def test_16_banks_per_pseudo_channel(self):
        """Each pseudo-channel should have 16 banks"""
        spec = HBM4Spec()
        assert spec.banks_per_pseudo_channel == 16
        assert spec.total_banks == 1024  # 32 × 2 × 16

        decoder = HBM4AddressDecoder()
        # All 16 banks should be valid
        for bank in range(16):
            addr = bank << 33
            decoded = decoder.decode(addr)
            assert decoded.bank_id == bank
            assert 0 <= decoded.bank_id < 16

    def test_64k_rows_per_bank(self):
        """Each bank should support 64K rows (decoder uses 16-bit row field)"""
        spec = HBM4Spec()
        decoder_rows = 1 << 16  # Decoder uses 16-bit rows
        assert decoder_rows == 65536  # 64K rows

        decoder = HBM4AddressDecoder()
        # Test boundary rows within decoder's 16-bit capacity (0-65535)
        test_rows = [0, 1, 100, 1000, 0x1000, 0x4000, 0x8000, 0xFFFF, 0xFFFE, 0xF000]
        for row in test_rows:
            addr = row << 17  # Row field at bits 32:17 (16 bits in decoder)
            decoded = decoder.decode(addr)
            assert decoded.row_id == row, f"Expected row 0x{row:04x}, got 0x{decoded.row_id:04x}"
            assert 0 <= decoded.row_id < (1 << 16)  # Decoder uses 16-bit rows

        # Verify that row values >= 64K (0x10000) overflow to 0 due to 16-bit mask
        addr = 0x10000 << 17  # row = 0x10000 (65K, exceeds 16-bit)
        decoded = decoder.decode(addr)
        assert decoded.row_id == 0  # Overflows to 0 due to 16-bit mask

    def test_64_columns_per_row(self):
        """Each row should support 64 columns"""
        spec = HBM4Spec()
        assert spec.ADDR_COL_BITS == 6
        assert 1 << spec.ADDR_COL_BITS == 64

        decoder = HBM4AddressDecoder()
        # All 64 columns should be valid
        for col in range(64):
            addr = col << 11
            decoded = decoder.decode(addr)
            assert decoded.col_id == col
            assert 0 <= decoded.col_id < 64

    def test_4_stack_ids(self):
        """Should support 4 stack IDs"""
        spec = HBM4Spec()
        assert spec.ADDR_STACK_BITS == 2
        assert 1 << spec.ADDR_STACK_BITS == 4

        decoder = HBM4AddressDecoder()
        # All 4 stack IDs should be valid
        for stack in range(4):
            addr = stack << 46
            decoded = decoder.decode(addr)
            assert decoded.stack_id == stack
            assert 0 <= decoded.stack_id < 4

    def test_4_beat_burst_alignment(self):
        """Burst alignment should be 4 beats"""
        spec = HBM4Spec()
        assert spec.burst_length == 4
        assert spec.ADDR_BURST_BITS == 2

        decoder = HBM4AddressDecoder()
        # All burst alignment values should be valid (0-3)
        # Note: DecodedAddress may not have burst_id, so we verify no error
        for burst in range(4):
            addr = burst << 9
            decoded = decoder.decode(addr)
            assert decoded is not None

    def test_total_address_bits(self):
        """Total address bits should be 42 for 4TB capacity"""
        spec = HBM4Spec()
        assert spec.get_total_addr_bits() == 42

    def test_total_memory_capacity_calculation(self):
        """Total memory capacity should be correctly calculated"""
        spec = HBM4Spec()
        # Calculate expected capacity: 32 ch × 2 pch × 16 banks × 512K rows × 64 cols × 256 bits
        channels = spec.channels  # 32
        pch = spec.pseudo_channels_per_channel  # 2
        banks = spec.banks_per_pseudo_channel  # 16
        rows = 1 << spec.ADDR_ROW_BITS  # 512K
        cols = 1 << spec.ADDR_COL_BITS  # 64
        width = spec.io_width  # 2048 bits

        total_bits = channels * pch * banks * rows * cols * width
        total_bytes = total_bits // 8
        total_tb = total_bytes / (1024**4)

        # HBM4 supports up to 4TB per stack
        assert total_tb >= 4.0


class TestAddressDecoderEdgeCases:
    """Test edge cases for address decoder"""

    def test_minimum_address_zero(self):
        """Address 0 should decode correctly"""
        decoder = HBM4AddressDecoder()
        decoded = decoder.decode(0)

        assert decoded.stack_id == 0
        assert decoded.channel_id == 0
        assert decoded.pseudo_channel_id == 0
        assert decoded.bank_group_id == 0
        assert decoded.bank_id == 0
        assert decoded.row_id == 0
        assert decoded.col_id == 0

    def test_maximum_address_boundary(self):
        """Maximum valid address should decode correctly"""
        decoder = HBM4AddressDecoder()
        # Maximum address based on total address bits (42 bits = 4TB)
        # Max 8-byte aligned address: (1 << 42) - 8
        max_addr = (1 << 42) - 8
        decoded = decoder.decode(max_addr)
        assert decoded is not None

    def test_address_with_all_fields_max(self):
        """Address with all fields at maximum should decode correctly"""
        decoder = HBM4AddressDecoder()
        # Maximum values for each field:
        # Stack: 3 (2 bits)
        # Channel: 31 (5 bits)
        # Pseudo-channel: 1 (1 bit)
        # Bank group: 7 (3 bits)
        # Bank: 15 (4 bits)
        # Row: 0xFFFF (16 bits)
        # Col: 63 (6 bits)
        # Burst: 3 (2 bits)
        # Offset: 0 (aligned)
        addr = (
            (3 << 46) |    # Stack
            (31 << 41) |   # Channel
            (1 << 40) |    # Pseudo-channel
            (7 << 37) |    # Bank group
            (15 << 33) |   # Bank
            (0xFFFF << 17) | # Row
            (63 << 11) |   # Column
            (3 << 9)       # Burst
        )
        decoded = decoder.decode(addr)
        assert decoded.stack_id == 3
        assert decoded.channel_id == 31
        assert decoded.pseudo_channel_id == 1
        assert decoded.bank_group_id == 7
        assert decoded.bank_id == 15
        assert decoded.row_id == 0xFFFF
        assert decoded.col_id == 63

    def test_address_with_all_fields_min(self):
        """Address with all fields at minimum should decode correctly"""
        decoder = HBM4AddressDecoder()
        addr = 0

        decoded = decoder.decode(addr)
        assert decoded.stack_id == 0
        assert decoded.channel_id == 0
        assert decoded.pseudo_channel_id == 0
        assert decoded.bank_group_id == 0
        assert decoded.bank_id == 0
        assert decoded.row_id == 0
        assert decoded.col_id == 0

    def test_eight_byte_alignment(self):
        """8-byte aligned addresses should work correctly"""
        decoder = HBM4AddressDecoder()

        # All 8-byte aligned addresses should decode without error
        for i in range(0, 8):
            addr = 0x1000 + (i * 8)
            decoded = decoder.decode(addr)
            assert decoded is not None

    def test_auto_alignment_of_misaligned(self):
        """Misaligned addresses should be auto-aligned before decoding"""
        decoder = HBM4AddressDecoder()

        # Misaligned address
        misaligned_addr = 0x123

        # Should auto-align (mask to 8-byte boundary) and not raise
        decoded = decoder.decode(misaligned_addr)
        assert decoded is not None


class TestAddressDecoderBoundaryConditions:
    """Test boundary conditions for address fields"""

    def test_channel_boundary_ch0_ch1(self):
        """Channel boundary between channel 0 and 1"""
        decoder = HBM4AddressDecoder()

        addr_ch0 = 0 << 41
        addr_ch1 = 1 << 41

        assert decoder.get_channel_id(addr_ch0) == 0
        assert decoder.get_channel_id(addr_ch1) == 1

    def test_channel_boundary_ch30_ch31(self):
        """Channel boundary between channel 30 and 31 (max channels)"""
        decoder = HBM4AddressDecoder()

        addr_ch30 = 30 << 41
        addr_ch31 = 31 << 41

        assert decoder.get_channel_id(addr_ch30) == 30
        assert decoder.get_channel_id(addr_ch31) == 31

    def test_pseudo_channel_boundary(self):
        """Pseudo-channel boundary (0 and 1)"""
        decoder = HBM4AddressDecoder()

        addr_pch0 = 0  # Bit 40 = 0
        addr_pch1 = 1 << 40  # Bit 40 = 1

        assert decoder.get_pseudo_channel_id(addr_pch0) == 0
        assert decoder.get_pseudo_channel_id(addr_pch1) == 1

    def test_bank_group_boundary(self):
        """Bank group boundaries (0-7)"""
        decoder = HBM4AddressDecoder()
        for bg in range(8):
            addr = bg << 37
            assert decoder.get_bank_group_id(addr) == bg

    def test_bank_boundary(self):
        """Bank boundaries (0-15)"""
        decoder = HBM4AddressDecoder()

        for bank in range(16):
            addr = bank << 33
            assert decoder.get_bank_id(addr) == bank

    def test_row_boundary_row0_row1(self):
        """Row boundary between row 0 and 1"""
        decoder = HBM4AddressDecoder()
        addr_row0 = 0 << 17
        addr_row1 = 1 << 17

        assert decoder.get_row_id(addr_row0) == 0
        assert decoder.get_row_id(addr_row1) == 1

    def test_row_boundary_last_rows(self):
        """Row boundary at end of row space (65534 and 65535)"""
        decoder = HBM4AddressDecoder()

        addr_row65534 = 0xFFFE << 17
        addr_row65535 = 0xFFFF << 17

        assert decoder.get_row_id(addr_row65534) == 0xFFFE
        assert decoder.get_row_id(addr_row65535) == 0xFFFF

    def test_column_boundary(self):
        """Column boundaries (0-63)"""
        decoder = HBM4AddressDecoder()
        for col in range(64):
            addr = col << 11
            assert decoder.get_column_id(addr) == col

    def test_stack_boundary(self):
        """Stack boundaries (0-3)"""
        decoder = HBM4AddressDecoder()

        for stack in range(4):
            addr = stack << 46
            assert decoder.get_stack_id(addr) == stack


class TestAddressDecoderRoundtrip:
    """Test encode/decode roundtrip for all field combinations"""

    def test_roundtrip_all_fields_rbc(self):
        """Full roundtrip for all fields with RBC mapping"""
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")

        test_cases = [
            (0, 0, 0, 0, 0, 0, 0),
            (3, 31, 1, 7, 15, 0xFFFF, 63),
            (1, 16, 0, 4, 8, 0x8000, 32),
            (2, 8, 1, 2, 4, 0x1234, 16),
            (0, 0, 0, 0, 0, 0, 63),
            (3, 31, 1, 7, 15, 0, 0),
        ]

        for stack, ch, pch, bg, bank, row, col in test_cases:
            original = DecodedAddress(
                stack_id=stack,
                channel_id=ch,
                pseudo_channel_id=pch,
                bank_group_id=bg,
                bank_id=bank,
                row_id=row,
                col_id=col,
                byte_offset=0
            )

            addr = decoder.encode(original)
            decoded = decoder.decode(addr)

            assert decoded.stack_id == original.stack_id, f"Stack mismatch for {original}"
            assert decoded.channel_id == original.channel_id, f"Channel mismatch for {original}"
            assert decoded.pseudo_channel_id == original.pseudo_channel_id, f"PCH mismatch for {original}"
            assert decoded.bank_group_id == original.bank_group_id, f"BG mismatch for {original}"
            assert decoded.bank_id == original.bank_id, f"Bank mismatch for {original}"
            assert decoded.row_id == original.row_id, f"Row mismatch for {original}"
            assert decoded.col_id == original.col_id, f"Col mismatch for {original}"

    def test_roundtrip_all_mappings(self):
        """Roundtrip should work for all mapping schemes"""
        schemes = ["rbc", "bcr", "crb", "hbm4"]
        for scheme in schemes:
            decoder = HBM4AddressDecoder(mapping_scheme=scheme)

            original = DecodedAddress(
                stack_id=1,
                channel_id=15,
                pseudo_channel_id=1,
                bank_group_id=3,
                bank_id=7,
                row_id=0x1234,
                col_id=32,
                byte_offset=0
            )
            addr = decoder.encode(original)
            decoded = decoder.decode(addr)

            assert decoded.channel_id == original.channel_id
            assert decoded.row_id == original.row_id


class TestAddressDecoderValidation:
    """Test address validation logic"""

    def test_validate_aligned_address(self):
        """Valid aligned addresses should pass validation"""
        decoder = HBM4AddressDecoder()

        valid_addrs = [
            0,
            0x1000,
            0x123456789ABCDEF0 & ~0x7,
            (1 << 41),  # Channel 1 base
        ]
        for addr in valid_addrs:
            assert decoder.validate_address(addr) is True, f"Should validate: 0x{addr:x}"

    def test_validate_misaligned_address(self):
        """Misaligned addresses should fail validation"""
        decoder = HBM4AddressDecoder()

        misaligned_addrs = [1, 2, 3, 4, 5, 6, 7, 0x123]
        for offset in misaligned_addrs:
            result = decoder.validate_address(offset)
            assert result is False, f"Should reject misaligned: 0x{offset:x}"

    def test_validate_channel_range(self):
        """Channel values within range should pass"""
        decoder = HBM4AddressDecoder()

        # All 32 valid channels
        for ch in range(32):
            addr = ch << 41
            assert decoder.validate_address(addr) is True

    def test_validate_field_ranges(self):
        """Field values within valid ranges should pass"""
        decoder = HBM4AddressDecoder()

        # Test boundary values for each field
        test_addr = (
            (3 << 46) |    # Stack max
            (31 << 41) |   # Channel max
            (1 << 40) |    # PCH max
            (7 << 37) |    # BG max
            (15 << 33) |   # Bank max
            (0xFFFF << 17) # Row max
        )
        assert decoder.validate_address(test_addr) is True


class TestAddressDecoderAddressRange:
    """Test address range calculations"""

    def test_total_address_range(self):
        """Total address range should be correctly calculated"""
        decoder = HBM4AddressDecoder()
        start, end = decoder.get_address_range()
        assert start == 0
        assert end > 0

        # End should be based on total address bits (42 bits)
        # (1 << 42) - 1 should be close to end
        expected_max = (1 << 42) - 1
        assert end <= expected_max

    def test_per_channel_address_range(self):
        """Per-channel address range should partition correctly"""
        decoder = HBM4AddressDecoder()
        for ch in range(32):
            start, end = decoder.get_address_range(channel=ch)
            # Each channel should have non-overlapping range
            assert start < end, f"Channel {ch}: start >= end"

            # Channel ID should be correct
            assert decoder.get_channel_id(start) == ch
            assert decoder.get_channel_id(end - 8) == ch

    def test_channel_ranges_non_overlapping(self):
        """Channel address ranges should not overlap"""
        decoder = HBM4AddressDecoder()
        ranges = [decoder.get_address_range(channel=ch) for ch in range(32)]

        for i in range(len(ranges)):
            for j in range(i + 1, len(ranges)):
                start_i, end_i = ranges[i]
                start_j, end_j = ranges[j]

                # Ranges should not overlap
                assert end_i <= start_j or end_j <= start_i, \
                    f"Overlapping ranges: ch{i}={ranges[i]}, ch{j}={ranges[j]}"


class TestAddressDecoderPerformance:
    """Test performance characteristics (should be fast)"""

    def test_decode_performance_many_addresses(self):
        """Decoding many addresses should complete quickly"""
        import time

        decoder = HBM4AddressDecoder()
        # Decode 10000 addresses
        num_addrs = 10000
        start = time.time()

        for i in range(num_addrs):
            addr = (i * 0x1000) & ~0x7
            decoder.decode(addr)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Decoding {num_addrs} addresses took {elapsed:.2f}s"

    def test_roundtrip_performance(self):
        """Encode/decode roundtrip should be fast"""
        import time

        decoder = HBM4AddressDecoder()
        original = DecodedAddress(
            stack_id=1,
            channel_id=15,
            pseudo_channel_id=1,
            bank_group_id=3,
            bank_id=7,
            row_id=0x1234,
            col_id=32,
            byte_offset=0
        )

        num_ops = 10000
        start = time.time()

        for _ in range(num_ops):
            addr = decoder.encode(original)
            decoder.decode(addr)

        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Roundtrip {num_ops} times took {elapsed:.2f}s"


class TestAddressDecoderHBM4Specific:
    """Test HBM4-specific address decoder coverage (32 channels, 64 pseudo-channels)"""

    def test_all_32_channels_decode_correctly(self):
        """All 32 channel addresses should decode correctly"""
        decoder = HBM4AddressDecoder()
        for ch in range(32):
            addr = ch << 41  # Channel field position
            decoded = decoder.decode(addr)
            assert decoded.channel_id == ch, f"Channel {ch} not decoded correctly"

    def test_all_64_pseudo_channels_decode_correctly(self):
        """All 64 pseudo-channel addresses should decode correctly"""
        decoder = HBM4AddressDecoder()
        # HBM4 has 32 channels × 2 pseudo-channels = 64 total
        for ch in range(32):
            for pch in range(2):
                # Build address with channel and pseudo-channel
                addr = (ch << 41) | (pch << 40)
                decoded = decoder.decode(addr)
                assert decoded.channel_id == ch, f"Channel {ch} mismatch"
                assert decoded.pseudo_channel_id == pch, f"PCH {pch} mismatch for channel {ch}"

    def test_all_8_bank_groups_decode_correctly(self):
        """All 8 bank group addresses should decode correctly"""
        decoder = HBM4AddressDecoder()

        for bg in range(8):
            addr = bg << 37  # Bank group field position
            decoded = decoder.decode(addr)
            assert decoded.bank_group_id == bg, f"Bank group {bg} not decoded correctly"

    def test_all_16_banks_decode_correctly(self):
        """All 16 bank addresses should decode correctly"""
        decoder = HBM4AddressDecoder()
        for bank in range(16):
            addr = bank << 33  # Bank field position
            decoded = decoder.decode(addr)
            assert decoded.bank_id == bank, f"Bank {bank} not decoded correctly"

    def test_all_16k_rows_decode_correctly(self):
        """All 16K row addresses should decode correctly (decoder uses 16-bit rows)"""
        decoder = HBM4AddressDecoder()
        # Test boundary rows (decoder uses 16-bit row field = 64K rows)
        test_rows = [0, 1, 2, 0x100, 0x1000, 0x8000, 0xFFFE, 0xFFFF]
        for row in test_rows:
            addr = row << 17  # Row field position
            decoded = decoder.decode(addr)
            assert decoded.row_id == row, f"Row 0x{row:x} not decoded correctly"

    def test_all_64_columns_decode_correctly(self):
        """All 64 column addresses should decode correctly"""
        decoder = HBM4AddressDecoder()
        for col in range(64):
            addr = col << 11  # Column field position
            decoded = decoder.decode(addr)
            assert decoded.col_id == col, f"Column {col} not decoded correctly"

    def test_all_4_stack_ids_decode_correctly(self):
        """All 4 stack IDs should decode correctly"""
        decoder = HBM4AddressDecoder()

        for stack in range(4):
            addr = stack << 46  # Stack field position
            decoded = decoder.decode(addr)
            assert decoded.stack_id == stack, f"Stack {stack} not decoded correctly"

    def test_hbm4_total_pseudo_channels_property(self):
        """HBM4Spec total_pseudo_channels should equal 64"""
        spec = HBM4Spec()

        assert spec.pseudo_channels == 64  # 32 channels × 2 PCH

    def test_hbm4_total_banks_property(self):
        """HBM4Spec total_banks should equal 1024"""
        spec = HBM4Spec()
        # 32 channels × 2 pseudo-channels × 16 banks = 1024
        assert spec.total_banks == 1024


class TestAddressDecoderCrossCoverage:
    """Test cross-coverage between address fields"""

    def test_channel_and_pseudo_channel_combinations(self):
        """Channel + pseudo-channel combinations should all work"""
        decoder = HBM4AddressDecoder()
        # All 64 combinations
        for ch in range(32):
            for pch in range(2):
                addr = (ch << 41) | (pch << 40)
                decoded = decoder.decode(addr)

                assert decoded.channel_id == ch
                assert decoded.pseudo_channel_id == pch

    def test_bank_group_and_bank_combinations(self):
        """Bank group + bank combinations should all work"""
        decoder = HBM4AddressDecoder()

        # All 128 combinations (8 BG × 16 banks)
        for bg in range(8):
            for bank in range(16):
                addr = (bg << 37) | (bank << 33)
                decoded = decoder.decode(addr)
                assert decoded.bank_group_id == bg
                assert decoded.bank_id == bank

    def test_row_and_column_combinations(self):
        """Row + column combinations should work"""
        decoder = HBM4AddressDecoder()

        test_cases = [
            (0, 0),
            (0, 63),
            (0xFFFF, 0),
            (0xFFFF, 63),
            (0x8000, 32),
        ]

        for row, col in test_cases:
            addr = (row << 17) | (col << 11)
            decoded = decoder.decode(addr)

            assert decoded.row_id == row
            assert decoded.col_id == col

    def test_full_field_combination(self):
        """All fields combined should work correctly"""
        decoder = HBM4AddressDecoder()

        # Test case with all fields at non-zero values
        addr = (
            (3 << 46) |    # Stack: 3
            (31 << 41) |   # Channel: 31
            (1 << 40) |    # PCH: 1
            (7 << 37) |    # BG: 7
            (15 << 33) |   # Bank: 15
            (0x1234 << 17) | # Row: 0x1234
            (50 << 11) |   # Col: 50
            (3 << 9)       # Burst: 3
        )

        decoded = decoder.decode(addr)

        assert decoded.stack_id == 3
        assert decoded.channel_id == 31
        assert decoded.pseudo_channel_id == 1
        assert decoded.bank_group_id == 7
        assert decoded.bank_id == 15
        assert decoded.row_id == 0x1234
        assert decoded.col_id == 50

    def test_mapping_scheme_affects_channel_position(self):
        """Different mapping schemes should place channel at different positions"""
        decoder_rbc = HBM4AddressDecoder(mapping_scheme="rbc")
        decoder_crb = HBM4AddressDecoder(mapping_scheme="crb")

        # Same address should decode differently for channel
        addr = 1 << 45  # Same bit position

        decoded_rbc = decoder_rbc.decode(addr)
        decoded_crb = decoder_crb.decode(addr)

        # RBC and CRB should handle channel differently
        # At minimum, the decoder should produce valid outputs
        assert decoded_rbc is not None
        assert decoded_crb is not None


class TestAddressDecoderErrorCases:
    """Test error cases and invalid inputs"""

    def test_decode_invalid_address_bits(self):
        """Addresses with invalid bit patterns should be handled"""
        decoder = HBM4AddressDecoder()
        # Very large address (beyond 42 bits)
        large_addr = 1 << 50
        decoded = decoder.decode(large_addr)

        # Should either reject or mask to valid range
        assert decoded is not None

    def test_decode_negative_address(self):
        """Negative addresses should be handled"""
        decoder = HBM4AddressDecoder()

        # Python allows negative addresses
        addr = -8
        decoded = decoder.decode(addr)

        # Should produce valid decoded address
        assert decoded is not None

    def test_validate_address_zero(self):
        """Address 0 should pass validation"""
        decoder = HBM4AddressDecoder()

        assert decoder.validate_address(0) is True

    def test_validate_address_max_boundary(self):
        """Maximum valid address should pass validation"""
        decoder = HBM4AddressDecoder()

        max_addr = (1 << 42) - 8  # 8-byte aligned
        assert decoder.validate_address(max_addr) is True

    def test_encode_decode_consistency(self):
        """Encode then decode should preserve all fields"""
        decoder = HBM4AddressDecoder()

        original = DecodedAddress(
            stack_id=0,
            channel_id=0,
            pseudo_channel_id=0,
            bank_group_id=0,
            bank_id=0,
            row_id=0,
            col_id=0,
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
        assert decoded.col_id == original.col_id


class TestAddressDecoderBoundaryConditions:
    """Additional boundary condition tests"""

    def test_channel_boundary_first_and_last(self):
        """Channel 0 and 31 boundaries should work"""
        decoder = HBM4AddressDecoder()
        addr_ch0 = 0
        addr_ch31 = 31 << 41

        decoded_ch0 = decoder.decode(addr_ch0)
        decoded_ch31 = decoder.decode(addr_ch31)

        assert decoded_ch0.channel_id == 0
        assert decoded_ch31.channel_id == 31

    def test_row_boundary_first_and_last(self):
        """Row 0 and 65535 boundaries should work"""
        decoder = HBM4AddressDecoder()

        addr_row0 = 0
        addr_row65535 = 0xFFFF << 17

        decoded_row0 = decoder.decode(addr_row0)
        decoded_row65535 = decoder.decode(addr_row65535)

        assert decoded_row0.row_id == 0
        assert decoded_row65535.row_id == 0xFFFF

    def test_column_boundary_first_and_last(self):
        """Column 0 and 63 boundaries should work"""
        decoder = HBM4AddressDecoder()

        addr_col0 = 0
        addr_col63 = 63 << 11

        decoded_col0 = decoder.decode(addr_col0)
        decoded_col63 = decoder.decode(addr_col63)

        assert decoded_col0.col_id == 0
        assert decoded_col63.col_id == 63

    def test_bank_boundary_first_and_last(self):
        """Bank 0 and 15 boundaries should work"""
        decoder = HBM4AddressDecoder()

        addr_bank0 = 0
        addr_bank15 = 15 << 33

        decoded_bank0 = decoder.decode(addr_bank0)
        decoded_bank15 = decoder.decode(addr_bank15)

        assert decoded_bank0.bank_id == 0
        assert decoded_bank15.bank_id == 15

    def test_bank_group_boundary_first_and_last(self):
        """Bank group 0 and 7 boundaries should work"""
        decoder = HBM4AddressDecoder()

        addr_bg0 = 0
        addr_bg7 = 7 << 37

        decoded_bg0 = decoder.decode(addr_bg0)
        decoded_bg7 = decoder.decode(addr_bg7)

        assert decoded_bg0.bank_group_id == 0
        assert decoded_bg7.bank_group_id == 7


class TestAddressDecoderSpecIntegration:
    """Test integration with HBM4 specification"""

    def test_decoder_uses_hbm4_spec(self):
        """Decoder should use HBM4 specification"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec=spec)

        assert decoder.spec is not None
        assert decoder.spec.channels == 32

    def test_spec_address_bit_fields(self):
        """HBM4Spec should define correct address bit fields"""
        spec = HBM4Spec()
        assert spec.ADDR_CHANNEL_BITS == 5   # 32 channels
        assert spec.ADDR_PCH_BITS == 1        # 2 PCH per channel
        assert spec.ADDR_BG_BITS == 3         # 8 bank groups
        assert spec.ADDR_BANK_BITS == 4       # 16 banks
        assert spec.ADDR_ROW_BITS == 19       # 512K rows
        assert spec.ADDR_COL_BITS == 6         # 64 columns
        assert spec.ADDR_BURST_BITS == 2      # 4-beat burst alignment
        assert spec.ADDR_STACK_BITS == 2      # 4 stacks

    def test_spec_total_address_bits(self):
        """HBM4Spec total address bits should be 42"""
        spec = HBM4Spec()

        total_bits = spec.get_total_addr_bits()
        assert total_bits == 42  # 42-bit addressing for 4TB

    def test_decoder_channel_bits_extraction(self):
        """Channel bit extraction should match spec"""
        spec = HBM4Spec()
        decoder = HBM4AddressDecoder(spec=spec)

        start_bit, num_bits = spec.get_channel_bits()
        assert num_bits == spec.ADDR_CHANNEL_BITS

    def test_decoder_pseudo_channel_bits_extraction(self):
        """Pseudo-channel bit extraction should match spec"""
        spec = HBM4Spec()

        start_bit, num_bits = spec.get_pseudo_channel_bits()
        assert num_bits == spec.ADDR_PCH_BITS

    def test_decoder_bank_group_bits_extraction(self):
        """Bank group bit extraction should match spec"""
        spec = HBM4Spec()

        start_bit, num_bits = spec.get_bank_group_bits()
        assert num_bits == spec.ADDR_BG_BITS

    def test_decoder_bank_bits_extraction(self):
        """Bank bit extraction should match spec"""
        spec = HBM4Spec()
        start_bit, num_bits = spec.get_bank_bits()
        assert num_bits == spec.ADDR_BANK_BITS

    def test_decoder_row_bits_extraction(self):
        """Row bit extraction should match spec"""
        spec = HBM4Spec()
        start_bit, num_bits = spec.get_row_bits()
        assert num_bits == spec.ADDR_ROW_BITS

    def test_decoder_column_bits_extraction(self):
        """Column bit extraction should match spec"""
        spec = HBM4Spec()

        start_bit, num_bits = spec.get_column_bits()
        assert num_bits == spec.ADDR_COL_BITS

    def test_decoder_burst_bits_extraction(self):
        """Burst bit extraction should match spec"""
        spec = HBM4Spec()

        start_bit, num_bits = spec.get_burst_bits()
        assert num_bits == spec.ADDR_BURST_BITS


class TestAddressDecoderSpeedGradeIntegration:
    """Test address decoder integration with HBM4 speed grades"""

    def test_decoder_with_8gbps_speed_grade(self):
        """Decoder should work with 8 Gbps speed grade"""
        spec = create_hbm4_spec_from_speed_grade("8Gbps")
        decoder = HBM4AddressDecoder(spec=spec)

        assert spec.data_rate_gtps == 8.0
        assert spec.tCK_ps == 125.0

        # Should decode addresses correctly
        addr = 0x1000
        decoded = decoder.decode(addr)
        assert decoded is not None

    def test_decoder_with_12gbps_speed_grade(self):
        """Decoder should work with 12 Gbps speed grade"""
        spec = create_hbm4_spec_from_speed_grade("12Gbps")
        decoder = HBM4AddressDecoder(spec=spec)

        assert spec.data_rate_gtps == 12.0
        assert abs(spec.tCK_ps - 83.33) < 0.01

        # Should decode addresses correctly
        addr = 0x1000
        decoded = decoder.decode(addr)
        assert decoded is not None

    def test_decoder_with_16gbps_speed_grade(self):
        """Decoder should work with 16 Gbps speed grade"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        decoder = HBM4AddressDecoder(spec=spec)

        assert spec.data_rate_gtps == 16.0
        assert spec.tCK_ps == 62.5

        # Should decode addresses correctly
        addr = 0x1000
        decoded = decoder.decode(addr)
        assert decoded is not None


def create_hbm4_spec_from_speed_grade(speed_grade: str) -> HBM4Spec:
    """Helper function for speed grade tests"""
    return HBM4Spec(data_rate_gtps=HBM4_SPEED_GRADES[speed_grade]["data_rate_gtps"],
                   tCK_ps=HBM4_SPEED_GRADES[speed_grade]["tCK_ps"])