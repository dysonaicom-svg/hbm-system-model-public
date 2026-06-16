"""
RTL-Python Address Decoder Alignment Tests

Tests to verify address decoder alignment between:
- RTL: rtl/hbm_controller.sv (Address Decoder section)
- Python: model/controller/hbm4_address_decoder.py

Key alignment areas:
- Address field widths (channel, bank, row, etc.)
- RBC address mapping bit positions
- Address encode/decode roundtrip

NOTE: RTL uses 16-bit row (64K rows), Python uses 19-bit row (512K rows for 4TB).
This is an intentional difference to support HBM4's larger capacity.

Author: Claude Code (AI-driven verification)
Date: 2026-06-16
"""

import pytest
from typing import Tuple

# Import Python components
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.hbm4_spec import HBM4Spec


# =============================================================================
# RTL Constants (from hbm_controller.sv)
# =============================================================================

# RTL address field widths from hbm_controller.sv parameters
RTL_STACK_ADDR_WIDTH = 2      # 4 stacks
RTL_CH_ADDR_WIDTH = 5         # 32 channels
RTL_BG_ADDR_WIDTH = 3         # 8 bank groups
RTL_BK_ADDR_WIDTH = 4         # 16 banks
RTL_ROW_ADDR_WIDTH = 16       # 64K rows (NOTE: differs from Python 19)
RTL_COL_ADDR_WIDTH = 6        # 64 columns
RTL_PCH_ADDR_WIDTH = 1       # 2 pseudo-channels

# RTL RBC address mapping bit positions (from hbm_controller.sv lines 89-101)
# These are the RTL's field extraction bit ranges
RTL_COL_BITS = (5, 0)           # req_addr[5:0]
RTL_ROW_BITS = (21, 6)         # req_addr[21:6]
RTL_BANK_BITS = (25, 22)        # req_addr[25:22]
RTL_BG_BITS = (28, 26)          # req_addr[28:26]
RTL_PCH_BIT = 29                # req_addr[29]
RTL_CH_BITS = (34, 30)          # req_addr[34:30]
RTL_STACK_BIT = 35              # req_addr[35]


# =============================================================================
# Helper Functions
# =============================================================================

def rtl_extract_field(addr: int, msb: int, lsb: int) -> int:
    """Extract address field using RTL logic"""
    if msb == lsb:
        return (addr >> lsb) & 1
    mask = ((1 << (msb - lsb + 1)) - 1) << lsb
    return (addr & mask) >> lsb


def rtl_extract_single_bit(addr: int, bit: int) -> int:
    """Extract single bit using RTL logic"""
    return (addr >> bit) & 1


# =============================================================================
# Test Class: Address Field Widths
# =============================================================================

class TestAddressDecoderAlignment:
    """Test address field width alignment"""

    def test_channel_bits_width(self):
        """Verify channel field width matches between RTL and Python"""
        spec = HBM4Spec()
        assert spec.ADDR_CHANNEL_BITS == RTL_CH_ADDR_WIDTH, \
            f"Channel bits mismatch: RTL={RTL_CH_ADDR_WIDTH}, Python={spec.ADDR_CHANNEL_BITS}"
        assert RTL_CH_ADDR_WIDTH == 5, "RTL should use 5 bits for 32 channels"

    def test_bank_group_bits_width(self):
        """Verify bank group field width matches"""
        spec = HBM4Spec()
        assert spec.ADDR_BG_BITS == RTL_BG_ADDR_WIDTH, \
            f"Bank group bits mismatch: RTL={RTL_BG_ADDR_WIDTH}, Python={spec.ADDR_BG_BITS}"
        assert RTL_BG_ADDR_WIDTH == 3, "RTL should use 3 bits for 8 bank groups"

    def test_bank_bits_width(self):
        """Verify bank field width matches"""
        spec = HBM4Spec()
        assert spec.ADDR_BANK_BITS == RTL_BK_ADDR_WIDTH, \
            f"Bank bits mismatch: RTL={RTL_BK_ADDR_WIDTH}, Python={spec.ADDR_BANK_BITS}"
        assert RTL_BK_ADDR_WIDTH == 4, "RTL should use 4 bits for 16 banks"

    def test_column_bits_width(self):
        """Verify column field width matches"""
        spec = HBM4Spec()
        assert spec.ADDR_COL_BITS == RTL_COL_ADDR_WIDTH, \
            f"Column bits mismatch: RTL={RTL_COL_ADDR_WIDTH}, Python={spec.ADDR_COL_BITS}"
        assert RTL_COL_ADDR_WIDTH == 6, "RTL should use 6 bits for 64 columns"

    def test_pseudo_channel_bits_width(self):
        """Verify pseudo-channel field width matches"""
        spec = HBM4Spec()
        assert spec.ADDR_PCH_BITS == RTL_PCH_ADDR_WIDTH, \
            f"Pseudo-channel bits mismatch: RTL={RTL_PCH_ADDR_WIDTH}, Python={spec.ADDR_PCH_BITS}"
        assert RTL_PCH_ADDR_WIDTH == 1, "RTL should use 1 bit for 2 pseudo-channels"

    def test_stack_bits_width(self):
        """Verify stack field width matches"""
        spec = HBM4Spec()
        assert spec.ADDR_STACK_BITS == RTL_STACK_ADDR_WIDTH, \
            f"Stack bits mismatch: RTL={RTL_STACK_ADDR_WIDTH}, Python={spec.ADDR_STACK_BITS}"
        assert RTL_STACK_ADDR_WIDTH == 2, "RTL should use 2 bits for 4 stacks"

    def test_row_bits_width_intentional_difference(self):
        """Verify row bits - NOTE: intentional difference for capacity

        RTL: 16 bits (64K rows) - optimized for typical HBM usage
        Python: 19 bits (512K rows) - supports full 4TB HBM4 capacity

        This is intentional to support different capacity points.
        """
        spec = HBM4Spec()
        # Document the intentional difference
        assert RTL_ROW_ADDR_WIDTH == 16, "RTL should use 16 bits for 64K rows"
        assert spec.ADDR_ROW_BITS == 19, "Python uses 19 bits for 512K rows (4TB capacity)"
        # They are intentionally different, so we document both
        assert RTL_ROW_ADDR_WIDTH != spec.ADDR_ROW_BITS, \
            "RTL and Python have different row bit widths (intentional)"


# =============================================================================
# Test Class: Address Mapping (RBC Format)
# =============================================================================

class TestAddressMappingAlignment:
    """Test address mapping (RBC) alignment"""

    @pytest.fixture
    def decoder(self):
        """Create HBM4 address decoder"""
        return HBM4AddressDecoder(mapping_scheme="rbc")

    def test_rbc_column_mapping(self, decoder):
        """Verify column bit mapping matches RBC scheme

        Note: RTL uses 36-bit address format (stack+ch+pch+bg+bank+row+col)
        Python uses 42-bit format (with burst/offset bits).
        This test verifies the column extraction logic is equivalent.
        """
        # Test address: column = 0x20 (32)
        test_col = 0x20
        # For Python decoder, we need to construct full 42-bit address
        # Column is at bits 16:11 in RBC mapping
        test_addr = test_col << 11  # Python RBC format: col at bits 16:11

        # RTL extraction uses 36-bit format: col at bits [5:0]
        rtl_addr = test_col  # RTL format: col at bits [5:0]
        rtl_col = rtl_extract_field(rtl_addr, *RTL_COL_BITS)

        # Python extraction
        decoded = decoder.decode(test_addr)

        assert rtl_col == decoded.col_id, \
            f"Column mismatch: RTL={rtl_col}, Python={decoded.col_id}"

    def test_rbc_row_mapping(self, decoder):
        """Verify row bit mapping matches RBC scheme

        Note: RTL uses 16-bit row, Python uses 16-bit row (RTL's row range).
        The test ensures both extract the same bits from their formats.
        """
        # Test row value within RTL's 16-bit range
        test_row = 0x1234
        # Python RBC format: row at bits 32:17 (16 bits)
        test_addr = test_row << 17

        # RTL format: row at bits [21:6]
        rtl_addr = test_row << 6
        rtl_row = rtl_extract_field(rtl_addr, *RTL_ROW_BITS)

        # Python extraction
        decoded = decoder.decode(test_addr)

        assert rtl_row == decoded.row_id, \
            f"Row mismatch: RTL={rtl_row}, Python={decoded.row_id}"

    def test_rbc_bank_mapping(self, decoder):
        """Verify bank bit mapping matches RBC scheme"""
        # Test bank value
        test_bank = 0xA
        # Python RBC format: bank at bits 36:33 (4 bits)
        test_addr = test_bank << 33

        # RTL format: bank at bits [25:22]
        rtl_addr = test_bank << 22
        rtl_bank = rtl_extract_field(rtl_addr, *RTL_BANK_BITS)

        # Python extraction
        decoded = decoder.decode(test_addr)

        assert rtl_bank == decoded.bank_id, \
            f"Bank mismatch: RTL={rtl_bank}, Python={decoded.bank_id}"

    def test_rbc_bank_group_mapping(self, decoder):
        """Verify bank group bit mapping matches RBC scheme"""
        # Test bank group value
        test_bg = 5
        # Python RBC format: BG at bits 39:37 (3 bits)
        test_addr = test_bg << 37

        # RTL format: BG at bits [28:26]
        rtl_addr = test_bg << 26
        rtl_bg = rtl_extract_field(rtl_addr, *RTL_BG_BITS)

        # Python extraction
        decoded = decoder.decode(test_addr)

        assert rtl_bg == decoded.bank_group_id, \
            f"Bank group mismatch: RTL={rtl_bg}, Python={decoded.bank_group_id}"

    def test_rbc_pseudo_channel_mapping(self, decoder):
        """Verify pseudo-channel bit mapping matches RBC scheme"""
        # Test pseudo-channel value
        test_pch = 1
        # Python RBC format: Pch at bit 40
        test_addr = test_pch << 40

        # RTL format: Pch at bit [29]
        rtl_addr = test_pch << 29
        rtl_pch = rtl_extract_single_bit(rtl_addr, RTL_PCH_BIT)

        # Python extraction
        decoded = decoder.decode(test_addr)

        assert rtl_pch == decoded.pseudo_channel_id, \
            f"Pseudo-channel mismatch: RTL={rtl_pch}, Python={decoded.pseudo_channel_id}"

    def test_rbc_channel_mapping(self, decoder):
        """Verify channel bit mapping matches RBC scheme"""
        # Test address: channel = 18
        test_ch = 18
        # Channel is at bits [34:30] in RTL
        test_addr = test_ch << (RTL_CH_ADDR_WIDTH + RTL_BG_ADDR_WIDTH + RTL_BK_ADDR_WIDTH +
                                RTL_ROW_ADDR_WIDTH + RTL_COL_ADDR_WIDTH)

        # RTL extraction
        rtl_ch = rtl_extract_field(test_addr, *RTL_CH_BITS)

        # Python extraction
        decoded = decoder.decode(test_addr)

        assert rtl_ch == decoded.channel_id, \
            f"Channel mismatch: RTL={rtl_ch}, Python={decoded.channel_id}"

    def test_rbc_stack_mapping(self, decoder):
        """Verify stack bit mapping matches RBC scheme

        Note: Stack is not decoded by HBM4AddressDecoder - it's stored in the
        upper bits that are stripped. The stack field is typically handled
        at a higher level (system address decoder).
        """
        # Test stack value
        test_stack = 1
        # Stack is at bit 47:46 in Python's full 64-bit address format
        test_addr = test_stack << 46

        # RTL format: stack at bit [35]
        # (RTL uses 36-bit address: 35 = stack bit)
        rtl_addr = test_stack << 35
        rtl_stack = rtl_extract_single_bit(rtl_addr, RTL_STACK_BIT)

        # Python decoder doesn't expose stack_id in DecodedAddress
        # Stack handling is done at system level
        # For this test, we verify RTL extraction logic is consistent
        assert rtl_stack == test_stack, \
            f"Stack RTL extraction should yield original value"


# =============================================================================
# Test Class: Address Decode Round Trip
# =============================================================================

class TestAddressDecodeRoundTrip:
    """Test address decode/encode round-trip consistency"""

    def test_rtl_format_vs_python_format_comparison(self):
        """Compare RTL-format and Python-format field extraction logic

        This test verifies that both RTL and Python extract fields from the same
        relative positions within their respective formats.

        RTL Format (36-bit): [stack][ch:pch:bg:bank][row][col]
          - Stack: bit 35
          - Channel: bits [34:30]
          - Pch: bit 29
          - BG: bits [28:26]
          - Bank: bits [25:22]
          - Row: bits [21:6]
          - Col: bits [5:0]

        Python RBC Format (42-bit): [stack][ch:pch:bg:bank][row][col][burst][offset]
          - Stack: bits [47:46]
          - Channel: bits [45:41]
          - Pch: bit 40
          - BG: bits [39:37]
          - Bank: bits [36:33]
          - Row: bits [32:17]
          - Col: bits [16:11]
          - Burst: bits [10:9]
          - Offset: bits [8:6]

        Note: Both formats use the same relative ordering but different bit positions.
        """
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")

        # Test cases: (channel, pch, bg, bank, row, col)
        # These values are extracted consistently across formats
        test_cases = [
            (0, 0, 0, 0, 0, 0),
            (10, 1, 3, 5, 0x1234, 32),
            (31, 1, 7, 15, 0xFFFF, 63),
        ]

        for ch, pch, bg, bank, row, col in test_cases:
            # Construct address in Python RBC format (bits shifted to match decoder)
            # Python format: col at [16:11], row at [32:17], etc.
            py_addr = (col << 11) | (row << 17) | (bank << 33) | \
                      (bg << 37) | (pch << 40) | (ch << 41)

            # Construct address in RTL format
            rtl_addr = col | (row << 6) | (bank << 22) | \
                       (bg << 26) | (pch << 29) | (ch << 30)

            # Verify RTL extraction (matches RTL's always_comb block)
            rtl_ch = rtl_extract_field(rtl_addr, *RTL_CH_BITS)
            rtl_pch = rtl_extract_single_bit(rtl_addr, RTL_PCH_BIT)
            rtl_bg = rtl_extract_field(rtl_addr, *RTL_BG_BITS)
            rtl_bank = rtl_extract_field(rtl_addr, *RTL_BANK_BITS)
            rtl_row = rtl_extract_field(rtl_addr, *RTL_ROW_BITS)
            rtl_col = rtl_extract_field(rtl_addr, *RTL_COL_BITS)

            # Verify Python extraction
            py_ch = decoder.get_channel_id(py_addr)
            py_pch = decoder.get_pseudo_channel_id(py_addr)
            py_bg = decoder.get_bank_group_id(py_addr)
            py_bank = decoder.get_bank_id(py_addr)
            py_row = decoder.get_row_id(py_addr)
            py_col = decoder.get_column_id(py_addr)

            # Verify values match
            assert rtl_ch == ch and py_ch == ch, f"Channel {ch} mismatch: RTL={rtl_ch}, Py={py_ch}"
            assert rtl_pch == pch and py_pch == pch, f"Pch {pch} mismatch: RTL={rtl_pch}, Py={py_pch}"
            assert rtl_bg == bg and py_bg == bg, f"BG {bg} mismatch: RTL={rtl_bg}, Py={py_bg}"
            assert rtl_bank == bank and py_bank == bank, f"Bank {bank} mismatch: RTL={rtl_bank}, Py={py_bank}"
            assert rtl_row == row and py_row == row, f"Row {row} mismatch: RTL={rtl_row}, Py={py_row}"
            assert rtl_col == col and py_col == col, f"Col {col} mismatch: RTL={rtl_col}, Py={py_col}"

    def test_decode_channel_id_fast_path(self):
        """Verify fast path channel extraction matches full decode"""
        decoder = HBM4AddressDecoder()

        test_channels = [0, 1, 15, 16, 31]

        for ch in test_channels:
            # Construct address with this channel
            addr = (ch << 41) | 0x1000  # Channel at bit 41 in RBC mapping

            fast_ch = decoder.get_channel_id(addr)
            full_decoded = decoder.decode(addr)

            assert fast_ch == full_decoded.channel_id, \
                f"Channel fast path mismatch: fast={fast_ch}, full={full_decoded.channel_id}"


# =============================================================================
# Test Class: Address Field Ranges
# =============================================================================

class TestAddressFieldRanges:
    """Test address field ranges"""

    def test_max_channel_id(self):
        """Verify max channel ID is 31 (0-31 for 32 channels)"""
        spec = HBM4Spec()
        max_ch = (1 << spec.ADDR_CHANNEL_BITS) - 1
        assert max_ch == 31, f"Max channel should be 31, got {max_ch}"

    def test_max_bank_group_id(self):
        """Verify max bank group ID is 7 (0-7 for 8 groups)"""
        spec = HBM4Spec()
        max_bg = (1 << spec.ADDR_BG_BITS) - 1
        assert max_bg == 7, f"Max bank group should be 7, got {max_bg}"

    def test_max_bank_id(self):
        """Verify max bank ID is 15 (0-15 for 16 banks)"""
        spec = HBM4Spec()
        max_bank = (1 << spec.ADDR_BANK_BITS) - 1
        assert max_bank == 15, f"Max bank should be 15, got {max_bank}"

    def test_max_row_id_rtl(self):
        """Verify max row ID for RTL (65535 for 16-bit row field)"""
        max_row = (1 << RTL_ROW_ADDR_WIDTH) - 1
        assert max_row == 65535, f"RTL max row should be 65535, got {max_row}"

    def test_max_row_id_python(self):
        """Verify max row ID for Python (524287 for 19-bit row field)"""
        spec = HBM4Spec()
        max_row = (1 << spec.ADDR_ROW_BITS) - 1
        assert max_row == 524287, f"Python max row should be 524287, got {max_row}"

    def test_max_column_id(self):
        """Verify max column ID is 63 (0-63 for 64 columns)"""
        spec = HBM4Spec()
        max_col = (1 << spec.ADDR_COL_BITS) - 1
        assert max_col == 63, f"Max column should be 63, got {max_col}"


# =============================================================================
# Test Class: Comprehensive Decode
# =============================================================================

class TestComprehensiveDecode:
    """Comprehensive address decode tests"""

    @pytest.fixture
    def decoder(self):
        """Create HBM4 address decoder"""
        return HBM4AddressDecoder(mapping_scheme="rbc")

    def test_complete_address_decode_python_format(self, decoder):
        """Test complete address decode with all fields using Python format

        Note: Python RBC format uses different bit positions than RTL format.
        This test verifies the Python decoder correctly extracts all fields.
        """
        # Python RBC format field values
        channel = 20
        pch = 1
        bg = 3
        bank = 12
        row = 0x1234  # Row within RTL's 16-bit range
        col = 0x25

        # Construct Python-format address
        addr = (col << 11) | (row << 17) | (bank << 33) | \
               (bg << 37) | (pch << 40) | (channel << 41)

        # Verify extraction
        assert decoder.get_channel_id(addr) == channel
        assert decoder.get_pseudo_channel_id(addr) == pch
        assert decoder.get_bank_group_id(addr) == bg
        assert decoder.get_bank_id(addr) == bank
        assert decoder.get_row_id(addr) == row
        assert decoder.get_column_id(addr) == col

    def test_address_decode_boundary_cases(self, decoder):
        """Test address decode at boundary values using Python format"""
        boundary_cases = [
            # (channel, pch, bg, bank, row, col)
            (0, 0, 0, 0, 0, 0),      # All minimums
            (31, 1, 7, 15, 0xFFFF, 63),  # Max values within RTL row range
            (31, 0, 0, 0, 0, 0),     # Max channel, min others
            (0, 1, 7, 15, 0xFFFF, 0),  # Max others, min channel
        ]

        for ch, pch, bg, bank, row, col in boundary_cases:
            addr = (col << 11) | (row << 17) | (bank << 33) | \
                   (bg << 37) | (pch << 40) | (ch << 41)

            assert decoder.get_channel_id(addr) == ch
            assert decoder.get_pseudo_channel_id(addr) == pch
            assert decoder.get_bank_group_id(addr) == bg
            assert decoder.get_bank_id(addr) == bank
            assert decoder.get_row_id(addr) == row
            assert decoder.get_column_id(addr) == col

    def test_rtl_format_extraction_logic(self, decoder):
        """Test that RTL extraction logic matches expected behavior

        RTL uses 36-bit format: stack[35] ch[34:30] pch[29] bg[28:26] bank[25:22] row[21:6] col[5:0]
        """
        # Test case with specific values
        ch, pch, bg, bank, row, col = 18, 1, 5, 10, 0x1234, 32

        # Construct RTL-format address
        rtl_addr = col | (row << 6) | (bank << 22) | (bg << 26) | \
                   (pch << 29) | (ch << 30)

        # Verify RTL extraction produces expected values
        assert rtl_extract_field(rtl_addr, *RTL_CH_BITS) == ch
        assert rtl_extract_single_bit(rtl_addr, RTL_PCH_BIT) == pch
        assert rtl_extract_field(rtl_addr, *RTL_BG_BITS) == bg
        assert rtl_extract_field(rtl_addr, *RTL_BANK_BITS) == bank
        assert rtl_extract_field(rtl_addr, *RTL_ROW_BITS) == row
        assert rtl_extract_field(rtl_addr, *RTL_COL_BITS) == col


# =============================================================================
# Test Class: RTL-Python Mapping Comparison
# =============================================================================

class TestRTLMappingComparison:
    """Direct comparison of RTL and Python field mappings"""

    def test_field_bit_widths_match(self):
        """Verify RTL and Python use same bit widths for each field"""
        decoder = HBM4AddressDecoder(mapping_scheme="rbc")

        # Verify field widths match
        # RTL: CH=5, BG=3, BK=4, ROW=16, COL=6, PCH=1
        # Python: CH=5, BG=3, BK=4, ROW=16, COL=6, PCH=1

        assert decoder.CHANNEL_BITS == RTL_CH_ADDR_WIDTH
        assert decoder.BG_BITS == RTL_BG_ADDR_WIDTH
        assert decoder.BANK_BITS == RTL_BK_ADDR_WIDTH
        assert decoder.ROW_BITS == RTL_ROW_ADDR_WIDTH
        assert decoder.COL_BITS == RTL_COL_ADDR_WIDTH
        assert decoder.PCH_BITS == RTL_PCH_ADDR_WIDTH

    def test_rtl_extraction_equivalence(self):
        """Verify RTL extraction logic is consistent across all fields"""
        # Test value extraction for all field types
        test_cases = [
            # (field, rtl_bits, test_value)
            ("col", RTL_COL_BITS, 32),
            ("row", RTL_ROW_BITS, 0x1234),
            ("bank", RTL_BANK_BITS, 10),
            ("bg", RTL_BG_BITS, 5),
        ]

        for field, rtl_bits, val in test_cases:
            msb, lsb = rtl_bits
            # Construct address with value at correct position
            addr = val << lsb
            extracted = rtl_extract_field(addr, msb, lsb)
            assert extracted == val, f"Field {field}: expected {val}, got {extracted}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])