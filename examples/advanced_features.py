"""
Example: HBM4 Advanced Feature Showcase

This example demonstrates advanced HBM4 features conceptually:
- ECC/CRC error handling
- Lane repair mechanisms
- Thermal management
- Power estimation
- MBIST operations

Run: python examples/advanced_features.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.dram.ecc_crc import HBM4ECC, HBM4CRC, HBM4DataIntegrity


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_ecc_operation():
    """Test ECC error detection and correction."""
    print_section("ECC (Error Correction Code)")

    ecc = HBM4ECC()

    print("\n  ECC Capabilities:")
    print("  " + "-" * 50)
    print("    - SEC-DED: Single Error Correction, Double Error Detection")
    print("    - 64-bit data word with 8-bit ECC")
    print("    - Corrects single-bit errors")
    print("    - Detects double-bit errors")

    # Test encoding
    print("\n  ECC Encoding Test:")
    print("  " + "-" * 50)

    test_data = 0xDEADBEEFCAFEBABE & 0xFFFFFFFFFFFFFFFF
    encoded = ecc.encode(test_data)
    print(f"    Original data:  0x{test_data:016X}")
    print(f"    ECC encoded:   0x{encoded:016X}")

    # Test decoding
    result = ecc.decode(encoded)
    print(f"\n  Decoded data:  0x{result.data:016X}")
    print(f"    Error type:    {result.error_type.name}")


def test_crc_operation():
    """Test CRC error detection."""
    print_section("CRC (Cyclic Redundancy Check)")

    crc = HBM4CRC()

    print("\n  CRC Capabilities:")
    print("  " + "-" * 50)
    print("    - CRC16 for data integrity")
    print("    - Per-DQ-lane parity")
    print("    - Command/address parity")

    print("\n  CRC Test:")
    print("  " + "-" * 50)

    test_data = 0xDEADBEEFCAFEBABE
    crc_value = crc.calculate_crc16(test_data)
    print(f"    Data:          0x{test_data:016X}")
    print(f"    CRC value:     0x{crc_value:04X}")

    valid, _ = crc.verify_crc16(test_data, crc_value)
    print(f"    Verification:  {'PASS' if valid else 'FAIL'}")


def test_data_integrity():
    """Test combined data integrity."""
    print_section("Data Integrity (ECC + CRC)")

    di = HBM4DataIntegrity()

    print("\n  Data Integrity Configuration:")
    print("  " + "-" * 50)
    print(f"    ECC enabled:    {di.enable_ecc}")
    print(f"    CRC enabled:    {di.enable_crc}")
    print(f"    Parity enabled: {di.enable_parity}")

    print("\n  Combined ECC + CRC Test:")
    print("  " + "-" * 50)

    test_data = 0xDEADBEEFCAFEBABE
    protected = di.encode_with_protection(test_data)
    print(f"    Original:      0x{test_data:016X}")
    print(f"    Protected:     0x{protected.get('data', 0):016X}")


def test_advanced_features_overview():
    """Overview of advanced features."""
    print_section("Advanced Features Overview")

    features = [
        ("Lane Repair", "Redundant lanes for failed DQ recovery"),
        ("Thermal Model", "Layer temperature and hotspot tracking"),
        ("Power Estimator", "Dynamic and static power analysis"),
        ("MBIST", "Memory built-in self-test patterns"),
        ("PHY Training", "Write leveling, read gate, DQ training"),
    ]

    print("\n  Feature Summary:")
    print("  " + "-" * 50)
    for name, desc in features:
        print(f"    {name:15s}: {desc}")


def main():
    print("=" * 70)
    print("  HBM4 Advanced Feature Showcase")
    print("=" * 70)

    test_ecc_operation()
    test_crc_operation()
    test_data_integrity()
    test_advanced_features_overview()

    print("\n" + "=" * 70)
    print("  Advanced feature showcase completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
