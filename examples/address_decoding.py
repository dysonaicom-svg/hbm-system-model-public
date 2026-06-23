"""
Example: HBM4 Address Decoding

This example demonstrates address decoding in HBM4:
- Creating address decoders with different mapping schemes
- Decoding addresses into component fields
- Extracting individual fields directly
- Validating addresses

HBM4 uses 48-bit address with fields for:
- Stack ID (2 bits)
- Channel (5 bits for 32 channels)
- Pseudo-channel (1 bit)
- Bank group (3 bits)
- Bank (4 bits)
- Row (16 bits)
- Column (6 bits)
- Burst/offset (5 bits)

Run: python examples/address_decoding.py
"""

from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.hbm4_spec import HBM4Spec


def main():
    print("=" * 60)
    print("HBM4 Address Decoding Example")
    print("=" * 60)

    # Create decoder with default RBC mapping
    print("\n1. Creating HBM4AddressDecoder (RBC mapping)...")
    decoder = HBM4AddressDecoder()
    print(f"   - Total address bits: {decoder.TOTAL_ADDR_BITS}")
    print(f"   - Channels: {2 ** decoder.CHANNEL_BITS}")
    print(f"   - Bank groups: {2 ** decoder.BG_BITS}")
    print(f"   - Banks per group: {2 ** decoder.BANK_BITS}")
    print(f"   - Rows per bank: {2 ** decoder.ROW_BITS}")

    # Demonstrate different mapping schemes
    print("\n2. Mapping Schemes Available:")
    schemes = ["rbc", "bcr", "crb"]
    for scheme in schemes:
        decoder_s = HBM4AddressDecoder(mapping_scheme=scheme)
        print(f"   - {scheme.upper()}: {decoder_s._mapping_scheme}")

    # Decode example addresses
    print("\n3. Address Decoding Examples:")

    test_addresses = [
        0x0001_0000_0000_0000,  # Channel 0
        0x0020_0000_0000_0000,  # Channel 1
        0x0100_0000_0000_0000,  # Channel 8
        0x0200_0000_0000_0000,  # Channel 16
        0x8000_0000_0000_0000,  # Stack 2
    ]

    for addr in test_addresses:
        decoded = decoder.decode(addr)
        print(f"\n   Address: 0x{addr:016X}")
        print(f"   - Stack ID: {decoded.stack_id}")
        print(f"   - Channel: {decoded.channel_id}")
        print(f"   - Pseudo-channel: {decoded.pseudo_channel_id}")
        print(f"   - Bank group: {decoded.bank_group_id}")
        print(f"   - Bank: {decoded.bank_id}")
        print(f"   - Row: 0x{decoded.row_id:04X}")
        print(f"   - Column: {decoded.col_id}")

    # Extract individual fields directly
    print("\n4. Direct Field Extraction:")
    addr = 0x0123_4567_89AB_C0
    print(f"   Address: 0x{addr:016X}")
    print(f"   - Channel ID: {decoder.get_channel_id(addr)}")
    print(f"   - Pseudo-channel ID: {decoder.get_pseudo_channel_id(addr)}")
    print(f"   - Bank group ID: {decoder.get_bank_group_id(addr)}")
    print(f"   - Bank ID: {decoder.get_bank_id(addr)}")
    print(f"   - Row ID: 0x{decoder.get_row_id(addr):04X}")
    print(f"   - Column ID: {decoder.get_column_id(addr)}")
    print(f"   - Stack ID: {decoder.get_stack_id(addr)}")

    # Calculate address ranges
    print("\n5. Address Ranges:")
    for ch in [0, 1, 15, 31]:
        start, end = decoder.get_address_range(channel=ch)
        print(f"   - Channel {ch:2d}: 0x{start:016X} - 0x{end:016X}")

    total_start, total_end = decoder.get_address_range()
    print(f"   - Total range: 0x{total_start:016X} - 0x{total_end:016X}")

    # Address validation
    print("\n6. Address Validation:")
    valid_addrs = [
        0x0000_0000_0000_0000,  # Valid (8-byte aligned)
        0x0000_0000_0000_0008,  # Valid (8-byte aligned)
    ]
    invalid_addrs = [
        0x0000_0000_0000_0001,  # Invalid (not aligned)
        0x0000_0000_0000_0005,  # Invalid (not aligned)
    ]

    print("   Valid addresses:")
    for addr in valid_addrs:
        is_valid = decoder.validate_address(addr)
        print(f"   - 0x{addr:016X}: {'Valid' if is_valid else 'Invalid'}")

    print("   Invalid addresses (not 8-byte aligned):")
    for addr in invalid_addrs:
        is_valid = decoder.validate_address(addr)
        print(f"   - 0x{addr:016X}: {'Valid' if is_valid else 'Invalid'}")

    # Channel striping example
    print("\n7. Channel Striping Example:")
    print("   Addresses striped across all 32 channels:")
    for ch in range(4):  # Show first 4 channels
        ch_addr = (ch & 0x1F) << 41 | 0x8  # Channel at bits 45:41
        decoded = decoder.decode(ch_addr)
        print(f"   - Addr 0x{ch_addr:016X} -> Channel {decoded.channel_id}")

    print("\n" + "=" * 60)
    print("Address decoding example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()