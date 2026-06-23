"""
Example: HBM4 Configuration Showcase

This example demonstrates all available HBM4 configuration options:
- Different speed grades (8/12/16 GT/s)
- Address mapping schemes
- Scheduler modes
- Queue configurations
- DFI parameters
- ECC/CRC settings

Run: python examples/configuration_example.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.controller.config import HBMConfig


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def example_speed_grades():
    """Demonstrate different speed grade configurations."""
    print_section("Speed Grade Configurations")

    # 8 GT/s (HBM4 baseline)
    config_8g = HBMConfig(
        data_rate=8.0e9,
        tCK_ps=125.0,
        io_width=2048,
        speed_grade="8Gbps"
    )
    print(f"\n8 GT/s Configuration:")
    print(f"  - Data rate: {config_8g.data_rate / 1e9:.1f} Gbps")
    print(f"  - tCK: {config_8g.tCK_ps:.2f} ps")
    peak_bw = config_8g.data_rate * config_8g.io_width / 8 / 1e9
    print(f"  - Peak bandwidth: {peak_bw:.0f} GB/s")

    # 12 GT/s (HBM4 intermediate)
    config_12g = HBMConfig(
        data_rate=12.0e9,
        tCK_ps=83.33,
        io_width=2048,
        speed_grade="12Gbps"
    )
    print(f"\n12 GT/s Configuration:")
    print(f"  - Data rate: {config_12g.data_rate / 1e9:.1f} Gbps")
    print(f"  - tCK: {config_12g.tCK_ps:.2f} ps")
    peak_bw = config_12g.data_rate * config_12g.io_width / 8 / 1e9
    print(f"  - Peak bandwidth: {peak_bw:.0f} GB/s")

    # 16 GT/s (HBM4 maximum)
    config_16g = HBMConfig(
        data_rate=16.0e9,
        tCK_ps=62.5,
        io_width=2048,
        speed_grade="16Gbps"
    )
    print(f"\n16 GT/s Configuration:")
    print(f"  - Data rate: {config_16g.data_rate / 1e9:.1f} Gbps")
    print(f"  - tCK: {config_16g.tCK_ps:.2f} ps")
    peak_bw = config_16g.data_rate * config_16g.io_width / 8 / 1e9
    print(f"  - Peak bandwidth: {peak_bw:.0f} GB/s")


def example_address_mapping():
    """Demonstrate address mapping schemes."""
    print_section("Address Mapping Schemes")

    schemes = [
        ("rbc", "Row-Bank-Channel (HBM3 default)"),
        ("rcbc", "Row-Column-Bank-Channel (HBM4 optimized)"),
        ("rbcg", "Row-Bank-Channel-Group"),
        ("bcr", "Bank-Channel-Row"),
        ("crb", "Channel-Row-Bank"),
    ]

    for scheme, desc in schemes:
        config = HBMConfig(address_mapping=scheme)
        print(f"\n{scheme.upper()} ({scheme}):")
        print(f"  - Description: {desc}")
        print(f"  - Mapping: {config.address_mapping}")


def example_scheduler_modes():
    """Demonstrate scheduler modes."""
    print_section("Scheduler Modes")

    modes = [
        ("fr-fcfs", "First Ready First Come First Serve"),
        ("fr-fcfs-qos", "FR-FCFS with QoS priority"),
        ("qos-only", "Strict QoS priority only"),
        ("throughput", "Maximum throughput"),
        ("latency", "Minimum latency"),
    ]

    for mode, desc in modes:
        config = HBMConfig(scheduler_mode=mode)
        print(f"\n{mode.upper()}:")
        print(f"  - Description: {desc}")
        print(f"  - Mode: {config.scheduler_mode}")


def example_refresh_configuration():
    """Demonstrate refresh scheduling configuration."""
    print_section("Refresh Scheduling Configuration")

    # Default refresh
    config_default = HBMConfig()
    print(f"\nDefault Refresh Configuration:")
    print(f"  - Refresh interval (tREFI): {config_default.refresh_interval * 1e6:.2f} us")
    print(f"  - Refresh penalty (tRFC): {config_default.refresh_penalty * 1e9:.1f} ns")
    print(f"  - DRFM enabled: {config_default.drfm_enabled}")
    print(f"  - DRFM threshold: {config_default.drfm_threshold}")

    # Aggressive refresh for Row Hammer protection
    config_aggressive = HBMConfig(
        drfm_enabled=True,
        drfm_threshold=2,
        refresh_interval=1.95e-6  # Half tREFI for aggressive refresh
    )
    print(f"\nAggressive Refresh (Row Hammer Protection):")
    print(f"  - Refresh interval: {config_aggressive.refresh_interval * 1e6:.2f} us")
    print(f"  - DRFM enabled: {config_aggressive.drfm_enabled}")
    print(f"  - DRFM threshold: {config_aggressive.drfm_threshold}")


def example_queue_configuration():
    """Demonstrate queue depth configurations."""
    print_section("Queue Configuration Options")

    configs = [
        ("Low Latency", HBMConfig(queue_depth=32, max_outstanding=16)),
        ("Balanced", HBMConfig(queue_depth=128, max_outstanding=64)),
        ("High Throughput", HBMConfig(queue_depth=512, max_outstanding=256)),
    ]

    for name, config in configs:
        print(f"\n{name}:")
        print(f"  - Queue depth: {config.queue_depth}")
        print(f"  - Max outstanding: {config.max_outstanding}")
        print(f"  - Write drain policy: {config.write_drain_policy}")


def example_dfi_configuration():
    """Demonstrate DFI interface parameters."""
    print_section("DFI Interface Configuration")

    configs = [
        ("DFI 4.0 (HBM3)", HBMConfig(dfi_freq_mhz=800, dfi_width=512)),
        ("DFI 5.0 (HBM4 baseline)", HBMConfig(dfi_freq_mhz=1200, dfi_width=512)),
        ("DFI 5.1 (HBM4E)", HBMConfig(dfi_freq_mhz=1600, dfi_width=512)),
    ]

    for name, config in configs:
        print(f"\n{name}:")
        print(f"  - DFI frequency: {config.dfi_freq_mhz} MHz")
        print(f"  - DFI width: {config.dfi_width} bits")
        print(f"  - PHY update latency: {config.dfi_phy_update_latency} cycles")


def example_error_handling():
    """Demonstrate ECC/CRC configuration."""
    print_section("Error Handling Configuration")

    configs = [
        ("Basic (no protection)", False, False, False),
        ("ECC only", True, False, False),
        ("CRC only", False, True, False),
        ("Full protection", True, True, True),
    ]

    for name, ecc, crc, lane_repair in configs:
        config = HBMConfig(
            ecc_enabled=ecc,
            crc_enabled=crc,
            lane_repair_enabled=lane_repair
        )
        print(f"\n{name}:")
        print(f"  - ECC: {'Enabled' if config.ecc_enabled else 'Disabled'}")
        print(f"  - CRC: {'Enabled' if config.crc_enabled else 'Disabled'}")
        print(f"  - Lane repair: {'Enabled' if config.lane_repair_enabled else 'Disabled'}")


def example_hbm3_compatibility():
    """Demonstrate HBM3 compatible configuration."""
    print_section("HBM3 Compatibility Mode")

    config = HBMConfig(
        channels_per_stack=8,
        io_width=1024,
        data_rate=6.4e9,
        tCK_ps=156.25,
        pseudo_channels_per_channel=2,
        banks_per_pseudo_channel=16,
        address_mapping="rbc",
    )
    print(f"\nHBM3 Configuration:")
    print(f"  - Channels: {config.channels_per_stack}")
    print(f"  - IO width: {config.io_width} bits")
    print(f"  - Data rate: {config.data_rate / 1e9:.1f} Gbps")
    peak_bw = config.data_rate * config.io_width / 8 / 1e9
    print(f"  - Peak bandwidth: {peak_bw:.0f} GB/s")
    print(f"  - Pseudo-channels: {config.pseudo_channels_per_channel}")
    print(f"  - Banks per pseudo-channel: {config.banks_per_pseudo_channel}")


def example_yaml_configuration():
    """Demonstrate YAML configuration."""
    print_section("YAML Configuration Example")

    # Show YAML format
    yaml_content = """# HBM4 Configuration YAML
channels_per_stack: 32
pseudo_channels_per_channel: 2
banks_per_pseudo_channel: 16
bank_groups_per_channel: 8
data_rate: 8.0e9  # 8 GT/s
io_width: 2048
speed_grade: "8Gbps"
address_mapping: "rbc"
scheduler_mode: "fr-fcfs-qos"
ecc_enabled: true
crc_enabled: true
queue_depth: 256
dfi_freq_mhz: 1200
"""

    print("\nYAML Configuration Format:")
    print("-" * 50)
    for line in yaml_content.strip().split('\n'):
        if line.strip():
            print(f"  {line}")

    print("\nUsage:")
    print("  from model.controller.config import HBMConfig")
    print("  config = HBMConfig.from_yaml('config.yaml')")


def example_bandwidth_guarantees():
    """Demonstrate QoS bandwidth guarantees."""
    print_section("QoS Bandwidth Guarantees")

    config = HBMConfig()
    print(f"\nBandwidth Guarantees (GB/s):")
    print(f"  - Critical: {config.bw_guarantee_critical:.0f} GB/s")
    print(f"  - High: {config.bw_guarantee_high:.0f} GB/s")
    print(f"  - Normal: {config.bw_guarantee_normal:.0f} GB/s")
    print(f"  - Low: {config.bw_guarantee_low:.0f} GB/s")


def main():
    print("=" * 70)
    print("  HBM4 Configuration Showcase")
    print("=" * 70)

    example_speed_grades()
    example_address_mapping()
    example_scheduler_modes()
    example_refresh_configuration()
    example_queue_configuration()
    example_dfi_configuration()
    example_error_handling()
    example_hbm3_compatibility()
    example_yaml_configuration()
    example_bandwidth_guarantees()

    print("\n" + "=" * 70)
    print("  Configuration example completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
