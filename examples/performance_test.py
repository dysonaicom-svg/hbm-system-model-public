"""
Example: HBM4 Performance Testing

This example demonstrates performance testing concepts:
- Bandwidth measurement
- Latency characterization
- Traffic pattern effects
- Speed grade comparison

Run: python examples/performance_test.py
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import HBM4Spec


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_sequential_access():
    """Test sequential access pattern (optimal)."""
    print_section("Sequential Access Pattern")

    controller = HBM4Controller()

    # Generate sequential addresses
    base_addr = 0x0001_0000_0000_0000
    addresses = [base_addr + (i * 64) for i in range(100)]

    print(f"  Testing {len(addresses)} sequential read requests...")

    # Submit requests
    for addr in addresses:
        controller.submit_request(addr=addr, is_read=True)

    # Run simulation
    cycles = 0
    completed = 0
    while cycles < 500 and completed < len(addresses):
        responses = controller.tick()
        completed += len(responses)
        cycles += 1

    print(f"\n  Results:")
    print(f"    - Completed: {completed}/{len(addresses)}")
    print(f"    - Cycles: {cycles}")


def test_random_access():
    """Test random access pattern."""
    print_section("Random Access Pattern")

    controller = HBM4Controller()
    random.seed(42)

    # Generate random addresses
    addresses = []
    for i in range(100):
        ch = random.randint(0, 31)
        row = random.randint(0, 65535)
        addr = ((ch & 0x1F) << 41) | ((row & 0xFFFF) << 17) | 0x8
        addresses.append(addr)

    print(f"  Testing {len(addresses)} random read requests...")

    for addr in addresses:
        controller.submit_request(addr=addr, is_read=True)

    cycles = 0
    completed = 0
    while cycles < 500 and completed < len(addresses):
        responses = controller.tick()
        completed += len(responses)
        cycles += 1

    print(f"\n  Results:")
    print(f"    - Completed: {completed}/{len(addresses)}")
    print(f"    - Cycles: {cycles}")


def test_striped_access():
    """Test channel-striped pattern."""
    print_section("Channel-Striped Pattern")

    controller = HBM4Controller()

    # Generate addresses striped across all 32 channels
    addresses = []
    for i in range(100):
        ch = i % 32
        row = (i // 32) % 65536
        addr = ((ch & 0x1F) << 41) | ((row & 0xFFFF) << 17) | 0x8
        addresses.append(addr)

    print(f"  Testing {len(addresses)} striped requests (32 channels)...")

    for addr in addresses:
        controller.submit_request(addr=addr, is_read=True)

    cycles = 0
    completed = 0
    while cycles < 500 and completed < len(addresses):
        responses = controller.tick()
        completed += len(responses)
        cycles += 1

    print(f"\n  Results:")
    print(f"    - Completed: {completed}/{len(addresses)}")
    print(f"    - Cycles: {cycles}")


def test_speed_grade_comparison():
    """Compare different speed grades."""
    print_section("Speed Grade Comparison")

    grades = [
        ("8 Gbps", 8.0),
        ("12 Gbps", 12.0),
        ("16 Gbps", 16.0),
    ]

    print(f"\n  {'Speed Grade':15s} | {'Peak BW':10s} | {'tCK (ps)':10s}")
    print("  " + "-" * 45)

    for name, rate in grades:
        spec = HBM4Spec(data_rate_gtps=rate)
        peak_bw = spec.bandwidth_gbs
        tck = 1000.0 / rate
        print(f"  {name:15s} | {peak_bw:8.0f} GB/s | {tck:8.2f}")


def test_bandwidth_concepts():
    """Show bandwidth calculation concepts."""
    print_section("Bandwidth Calculation Concepts")

    print("\n  HBM4 Peak Bandwidth:")
    print("  " + "-" * 50)

    # HBM4 specs
    data_rate = 8.0e9  # 8 GT/s
    io_width = 2048    # 2048-bit interface
    channels = 32

    # Calculate bandwidth
    peak_bw_bytes = data_rate * io_width / 8  # bytes per second
    peak_bw_gb = peak_bw_bytes / 1e9
    peak_bw_tb = peak_bw_bytes / 1e12

    print(f"    Data rate: {data_rate / 1e9:.1f} GT/s")
    print(f"    IO width: {io_width} bits")
    print(f"    Channels: {channels}")
    print(f"\n    Peak bandwidth: {peak_bw_gb:.0f} GB/s ({peak_bw_tb:.2f} TB/s)")

    # Show per-channel
    per_channel_bw = peak_bw_gb / channels
    print(f"    Per-channel: {per_channel_bw:.0f} GB/s")


def test_latency_concepts():
    """Show latency concepts."""
    print_section("Latency Concepts")

    print("\n  HBM4 Timing Parameters:")
    print("  " + "-" * 50)

    spec = HBM4Spec()

    timings = [
        ("tRCD", "Row activate to READ", spec.nRCDRD),
        ("tCL", "CAS latency", spec.nCL),
        ("tRAS", "Row active time", spec.nRAS),
        ("tRP", "Row precharge", spec.nRP),
        ("tRC", "Row cycle", spec.nRC),
    ]

    for name, desc, cycles in timings:
        time_ns = cycles * spec.tCK_ps / 1000
        print(f"    {name:5s}: {cycles:3d} cycles ({time_ns:.1f} ns) - {desc}")


def main():
    print("=" * 70)
    print("  HBM4 Performance Testing Suite")
    print("=" * 70)

    test_sequential_access()
    test_random_access()
    test_striped_access()
    test_speed_grade_comparison()
    test_bandwidth_concepts()
    test_latency_concepts()

    print("\n" + "=" * 70)
    print("  Performance testing completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
