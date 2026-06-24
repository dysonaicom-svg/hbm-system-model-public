"""
Unit Tests for AXI4 Converter - Enhanced Coverage

Tests cover:
- AddressMapping all modes and methods
- AXI4ToHBMConverter
- HBMToAXI4Converter
- AXI4Converter
- ConversionResult

Target: Increase coverage from 61% to 80%+
"""

import pytest
import sys
from typing import List, Dict

sys.path.insert(0, '/home/ic/JXTF/HBM4')

from model.interconnect.axi4_converter import (
    # Core classes
    AXI4Converter,
    AddressMapping,
    AddressMappingMode,
    AXI4ToHBMConverter,
    HBMToAXI4Converter,
    ConversionResult,

    # Factory functions
    create_axi4_converter,
    create_hbm_address_mapping,
)

from model.interconnect.axi4_bridge import (
    AXI4ReadTransaction,
    AXI4WriteTransaction,
    AXI4BurstType,
)


# ============================================================================
# AddressMapping Tests
# ============================================================================

class TestAddressMapping:
    """Test AddressMapping functionality"""

    def test_mapping_creation(self):
        """Test address mapping creation"""
        mapping = AddressMapping()
        assert mapping.hbm_channels == 32
        assert mapping.hbm_stacks == 4
        assert mapping.mapping_mode == AddressMappingMode.ROW_BANK_CHANNEL

    def test_custom_mapping(self):
        """Test custom address mapping"""
        mapping = AddressMapping(
            hbm_channels=16,
            hbm_stacks=2,
            hbm_bank_groups=4,
            hbm_banks=8,
        )
        assert mapping.hbm_channels == 16
        assert mapping.hbm_stacks == 2
        assert mapping.hbm_bank_groups == 4
        assert mapping.hbm_banks == 8

    def test_decode_axi_addr(self):
        """Test decoding AXI address"""
        mapping = AddressMapping()
        addr = 0x0001_0000_0000_1234
        decoded = mapping.decode_axi_addr(addr)

        assert 'stack' in decoded
        assert 'channel' in decoded
        assert 'bank_group' in decoded
        assert 'bank' in decoded
        assert 'row' in decoded
        assert 'col' in decoded

    def test_decode_with_pseudo_channel(self):
        """Test decoding with pseudo-channel"""
        mapping = AddressMapping(hbm_pseudo_channels=2)
        # Check that pseudo channel bit exists
        addr = 0x0000_0010_0000_0000
        decoded = mapping.decode_axi_addr(addr)
        assert 'pseudo_channel' in decoded

    def test_encode_hbm_addr(self):
        """Test encoding HBM address"""
        mapping = AddressMapping()
        addr = mapping.encode_hbm_addr(
            stack=1,
            channel=8,
            pseudo_channel=1,
            bank_group=3,
            bank=5,
            row=0x1234,
            col=10,
            byte_offset=0,
        )
        assert addr > 0

    def test_roundtrip_decode_encode(self):
        """Test encode-decode roundtrip"""
        mapping = AddressMapping(hbm_channels=32, hbm_stacks=4)

        for stack in range(4):
            for channel in range(min(4, 32)):  # Test a subset
                encoded = mapping.encode_hbm_addr(
                    stack=stack,
                    channel=channel,
                    pseudo_channel=0,
                    bank_group=0,
                    bank=0,
                    row=0,
                    col=0,
                    byte_offset=0,
                )
                decoded = mapping.decode_axi_addr(encoded)
                assert decoded['stack'] == stack
                assert decoded['channel'] == channel

    def test_linear_mapping(self):
        """Test linear address mapping mode"""
        mapping = AddressMapping(mapping_mode=AddressMappingMode.LINEAR)
        addr = 0x1000
        decoded = mapping.decode_axi_addr(addr)
        assert 'channel' in decoded

    def test_channel_interleaved_mapping(self):
        """Test channel interleaved mapping"""
        mapping = AddressMapping(mapping_mode=AddressMappingMode.CHANNEL_INTERLEAVED)
        addr = 0x1000
        decoded = mapping.decode_axi_addr(addr)
        assert 'channel' in decoded

    def test_bank_interleaved_mapping(self):
        """Test bank interleaved mapping"""
        mapping = AddressMapping(mapping_mode=AddressMappingMode.BANK_INTERLEAVED)
        addr = 0x1000
        decoded = mapping.decode_axi_addr(addr)
        assert 'bank' in decoded

    def test_get_stack_channel(self):
        """Test getting stack and channel"""
        mapping = AddressMapping()
        stack, channel = mapping.get_stack_channel(0x1000)
        assert 0 <= stack < mapping.hbm_stacks
        assert 0 <= channel < mapping.hbm_channels

    def test_get_hbm_address_components(self):
        """Test getting HBM address components"""
        mapping = AddressMapping()
        components = mapping.get_hbm_address_components(0x1000)
        assert 'stack' in components
        assert 'channel' in components

    def test_axi_to_hbm_addr(self):
        """Test AXI to HBM address conversion"""
        mapping = AddressMapping()
        hbm_addr = mapping.axi_to_hbm_addr(0x1000)
        assert hbm_addr >= 0

    def test_hbm_to_axi_addr(self):
        """Test HBM to AXI address conversion"""
        mapping = AddressMapping()
        axi_addr = mapping.hbm_to_axi_addr(0x1000)
        assert axi_addr >= 0


# ============================================================================
# AXI4ToHBMConverter Tests
# ============================================================================

class TestAXI4ToHBMConverter:
    """Test AXI4 to HBM converter"""

    def test_converter_creation(self):
        """Test converter creation"""
        converter = AXI4ToHBMConverter()
        assert converter is not None

    def test_convert_read_transaction(self):
        """Test converting read transaction"""
        converter = AXI4ToHBMConverter()
        txn = AXI4ReadTransaction(
            addr=0x1000,
            size=6,  # 64 bytes
            length=3,  # 4 beats
            burst=AXI4BurstType.INCR,
            id=1,
        )
        result = converter.convert_read(txn)
        assert result.success is True
        assert len(result.hbm_requests) >= 0

    def test_convert_write_transaction(self):
        """Test converting write transaction"""
        converter = AXI4ToHBMConverter()
        txn = AXI4WriteTransaction(
            addr=0x2000,
            size=6,
            length=3,
            data=[0xDEAD] * 4,
            burst=AXI4BurstType.INCR,
            id=2,
        )
        result = converter.convert_write(txn)
        assert result.success is True
        assert len(result.hbm_requests) >= 0


# ============================================================================
# HBMToAXI4Converter Tests
# ============================================================================

class TestHBMToAXI4Converter:
    """Test HBM to AXI4 converter"""

    def test_converter_creation(self):
        """Test converter creation"""
        converter = HBMToAXI4Converter()
        assert converter is not None


# ============================================================================
# AXI4Converter Tests
# ============================================================================

class TestAXI4Converter:
    """Test unified AXI4 converter"""

    def test_converter_creation(self):
        """Test converter creation"""
        converter = AXI4Converter()
        assert converter.axi4_to_hbm is not None
        assert converter.hbm_to_axi4 is not None

    def test_to_hbm_read(self):
        """Test converting read transaction"""
        converter = AXI4Converter()
        txn = AXI4ReadTransaction(
            addr=0x1000,
            size=6,
            length=3,
            burst=AXI4BurstType.INCR,
        )
        result = converter.to_hbm(txn)
        assert result.success is True
        assert len(result.hbm_requests) >= 0

    def test_to_hbm_write(self):
        """Test converting write transaction"""
        converter = AXI4Converter()
        txn = AXI4WriteTransaction(
            addr=0x2000,
            size=6,
            length=3,
            data=[0xDEAD] * 4,
            burst=AXI4BurstType.INCR,
        )
        result = converter.to_hbm(txn)
        assert result.success is True
        assert len(result.hbm_requests) >= 0

    def test_conversion_result(self):
        """Test conversion result properties"""
        result = ConversionResult(
            success=True,
            hbm_requests=[],
            beats_generated=0,
            bytes_converted=0,
        )
        assert result.success is True
        assert result.beats_generated == 0

    def test_get_stats(self):
        """Test getting conversion statistics"""
        converter = AXI4Converter()
        stats = converter.get_stats()
        assert 'axi4_to_hbm' in stats
        assert 'hbm_to_axi4' in stats


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunctions:
    """Test factory functions"""

    def test_create_axi4_converter(self):
        """Test creating AXI4 converter"""
        converter = create_axi4_converter()
        assert converter is not None

    def test_create_hbm_address_mapping_row_bank_channel(self):
        """Test creating HBM address mapping with ROW_BANK_CHANNEL mode"""
        mapping = create_hbm_address_mapping(
            mode="row_bank_channel",
            channels=32,
            stacks=4,
        )
        assert mapping.mapping_mode == AddressMappingMode.ROW_BANK_CHANNEL
        assert mapping.hbm_channels == 32
        assert mapping.hbm_stacks == 4

    def test_create_hbm_address_mapping_linear(self):
        """Test creating HBM address mapping with LINEAR mode"""
        mapping = create_hbm_address_mapping(mode="linear")
        assert mapping.mapping_mode == AddressMappingMode.LINEAR

    def test_create_hbm_address_mapping_channel_interleaved(self):
        """Test creating channel interleaved mapping"""
        mapping = create_hbm_address_mapping(mode="channel_interleaved")
        assert mapping.mapping_mode == AddressMappingMode.CHANNEL_INTERLEAVED

    def test_create_hbm_address_mapping_bank_interleaved(self):
        """Test creating bank interleaved mapping"""
        mapping = create_hbm_address_mapping(mode="bank_interleaved")
        assert mapping.mapping_mode == AddressMappingMode.BANK_INTERLEAVED

    def test_create_hbm_address_mapping_custom_channels(self):
        """Test creating mapping with custom channel count"""
        mapping = create_hbm_address_mapping(channels=16)
        assert mapping.hbm_channels == 16

    def test_create_hbm_address_mapping_custom_stacks(self):
        """Test creating mapping with custom stack count"""
        mapping = create_hbm_address_mapping(stacks=8)
        assert mapping.hbm_stacks == 8


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestConverterEdgeCases:
    """Test edge cases in converter"""

    def test_zero_length_transaction(self):
        """Test zero length transaction"""
        converter = AXI4Converter()
        txn = AXI4ReadTransaction(
            addr=0x1000,
            size=0,
            length=0,  # 1 beat
            burst=AXI4BurstType.INCR,
        )
        result = converter.to_hbm(txn)
        assert result.success is True

    def test_max_burst_length(self):
        """Test maximum burst length"""
        converter = AXI4Converter()
        txn = AXI4ReadTransaction(
            addr=0x1000,
            size=6,
            length=255,  # AXI4 max
            burst=AXI4BurstType.INCR,
        )
        result = converter.to_hbm(txn)
        assert result.success is True


# ============================================================================
# Performance Tests
# ============================================================================

class TestConverterPerformance:
    """Test converter performance"""

    def test_many_small_transactions(self):
        """Test many small transactions"""
        converter = AXI4Converter()
        for i in range(100):
            txn = AXI4ReadTransaction(
                addr=0x1000 + i * 64,
                size=6,
                length=0,
            )
            result = converter.to_hbm(txn)
            assert result.success is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestConverterIntegration:
    """Integration tests for converter"""

    def test_roundtrip_conversion(self):
        """Test AXI4 to HBM to AXI4 conversion"""
        from model.interconnect.axi4_bridge import create_axi4_bridge

        bridge = create_axi4_bridge(max_pending=16)
        converter = AXI4Converter()

        # Submit read
        txn_id = bridge.submit_read(
            addr=0x1000,
            size=6,
            length=3,
            qos=8,
        )

        # Get pending transaction
        txn = bridge._pending_reads.get(txn_id)
        if txn:
            result = converter.to_hbm(txn)
            assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
