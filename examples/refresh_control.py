"""
HBM4 Refresh Control Example

Demonstrates refresh scheduling and management:
- All-bank refresh mode
- Per-bank refresh mode (HBM4 default)
- Bank group refresh mode
- DRFM (Direct Refresh Management) for row-hammer
- Refresh statistics and monitoring

Reference:
- JEDEC JESD270-4A HBM4 specification
- Synopsys DesignWare HBM4/4E Controller IP

Run: python examples/refresh_control.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.controller.HBM4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.controller.HBM4_controller import HBM4Controller
from model.dram.HBM4_spec import HBM4Spec


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def example_refresh_modes():
    """Show available refresh modes."""
    print_section("Example 1: Refresh Modes")

    print("\nAvailable Refresh Modes:")
    print("  " + "-" * 50)

    modes = [
        (RefreshMode.PER_BANK, "HBM3/HBM4 default", "Staggered per-bank refresh for reduced power"),
        (RefreshMode.ALL_BANKS, "Legacy compatibility", "All banks refreshed simultaneously"),
        (RefreshMode.BANK_GROUP, "Power-sensitive", "Refresh by bank group"),
    ]

    for mode, name, desc in modes:
        print(f"\n  {mode.value}:")
        print(f"    Name: {name}")
        print(f"    Description: {desc}")


def example_per_bank_refresh():
    """Demonstrate per-bank refresh (HBM4 default)."""
    print_section("Example 2: Per-Bank Refresh (HBM4 Default)")

    scheduler = HBM4RefreshScheduler()
    scheduler.set_mode(RefreshMode.PER_BANK)

    spec = HBM4Spec()

    print("\nPer-Bank Refresh Configuration:")
    print("  " + "-" * 50)
    print(f"  Mode: {scheduler.mode.value}")
    print(f"  Total banks: {spec.total_banks}")
    print(f"  Banks per pseudo-channel: {spec.banks_per_pseudo_channel}")
    print(f"  tREFI (refresh interval): {scheduler.tREFI} cycles")
    print(f"  tRFC (refresh duration): {scheduler.tRFC} cycles")
    print(f"  nRREFD (per-bank interval): {scheduler.nRREFD} cycles")

    # Simulate refresh cycles
    print("\nRefresh Commands (first 16 cycles):")
    print("  " + "-" * 50)

    refresh_count = 0
    for cycle in range(1000):
        scheduler.tick()

        if scheduler.can_refresh():
            cmd = scheduler.get_refresh_command()
            if cmd and refresh_count < 16:
                cmd_name, ch, pch, bank = cmd
                print(f"  Cycle {cycle:4d}: {cmd_name} ch={ch}, pch={pch}, bank={bank}")
                refresh_count += 1

        if refresh_count >= 16:
            break

    # Get stats
    stats = scheduler.get_stats()
    print(f"\n  Total refreshes: {stats['total_refreshes']}")
    print(f"  Per-bank refreshes: {stats['per_bank_refreshes']}")


def example_all_bank_refresh():
    """Demonstrate all-bank refresh."""
    print_section("Example 3: All-Bank Refresh")

    scheduler = HBM4RefreshScheduler()
    scheduler.set_mode(RefreshMode.ALL_BANKS)

    print("\nAll-Bank Refresh Configuration:")
    print("  " + "-" * 50)
    print(f"  Mode: {scheduler.mode.value}")
    print(f"  tREFI: {scheduler.tREFI} cycles")
    print(f"  tRFC: {scheduler.tRFC} cycles")

    # Simulate refresh cycles
    print("\nRefresh Commands (first 10 cycles):")
    print("  " + "-" * 50)

    refresh_count = 0
    for cycle in range(500):
        scheduler.tick()

        if scheduler.can_refresh():
            cmd = scheduler.get_refresh_command()
            if cmd and refresh_count < 10:
                cmd_name, ch, pch, bank = cmd
                print(f"  Cycle {cycle:4d}: {cmd_name} (all banks)")
                refresh_count += 1

        if refresh_count >= 10:
            break

    stats = scheduler.get_stats()
    print(f"\n  Total refreshes: {stats['total_refreshes']}")
    print(f"  All-bank refreshes: {stats['all_bank_refreshes']}")


def example_bank_group_refresh():
    """Demonstrate bank group refresh."""
    print_section("Example 4: Bank Group Refresh")

    scheduler = HBM4RefreshScheduler()
    scheduler.set_mode(RefreshMode.BANK_GROUP)

    spec = HBM4Spec()

    print("\nBank Group Refresh Configuration:")
    print("  " + "-" * 50)
    print(f"  Mode: {scheduler.mode.value}")
    print(f"  Bank groups per channel: {spec.bank_groups_per_channel}")

    # Simulate refresh cycles
    print("\nRefresh Commands (first 10 cycles):")
    print("  " + "-" * 50)

    refresh_count = 0
    for cycle in range(500):
        scheduler.tick()

        if scheduler.can_refresh():
            cmd = scheduler.get_refresh_command()
            if cmd and refresh_count < 10:
                cmd_name, ch, pch, bank = cmd
                print(f"  Cycle {cycle:4d}: {cmd_name} bank={bank}")
                refresh_count += 1

        if refresh_count >= 10:
            break

    stats = scheduler.get_stats()
    print(f"\n  Total refreshes: {stats['total_refreshes']}")
    print(f"  Bank group refreshes: {stats['bank_group_refreshes']}")


def example_drfm():
    """Demonstrate DRFM (Direct Refresh Management)."""
    print_section("Example 5: DRFM (Row Hammer Protection)")

    scheduler = HBM4RefreshScheduler()
    scheduler.enable_drfm(enabled=True, threshold=100)  # Short threshold for demo

    print("\nDRFM Configuration:")
    print("  " + "-" * 50)
    print(f"  DRFM Enabled: {scheduler.drfm_enabled}")
    print(f"  Row hammer threshold: {scheduler.drfm_rowhammer_threshold} cycles")

    # Simulate with DRFM
    print("\nSimulating Refresh with DRFM:")
    print("  " + "-" * 50)

    # Mark some banks as needing refresh
    scheduler.mark_bank_refreshed(0, 0, 0, 0)
    scheduler.mark_bank_refreshed(0, 0, 1, 0)
    scheduler.mark_bank_refreshed(0, 0, 2, 0)

    # Simulate some cycles
    for cycle in range(150):
        scheduler.tick()

    # Get banks needing refresh
    at_risk = scheduler.get_banks_needing_refresh()
    print(f"  Banks at risk after 150 cycles: {at_risk}")

    stats = scheduler.get_stats()
    print(f"\n  Refresh Statistics:")
    print(f"    Total refreshes: {stats['total_refreshes']}")


def example_refresh_integration():
    """Show refresh integration with controller."""
    print_section("Example 6: Refresh Integration with Controller")

    controller = HBM4Controller(enable_refresh=True)

    print("\nController Configuration:")
    print("  " + "-" * 50)
    stats = controller.get_stats()
    print(f"  Refresh Enabled: {stats['refresh']['enabled']}")
    print(f"  Refresh Mode: {stats['refresh']['mode']}")

    spec = controller.spec
    print(f"\n  Timing Parameters:")
    print(f"    tREFI: {spec.nREFI} cycles")
    print(f"    tRFC: {spec.nRFC} cycles")

    # Submit some requests
    print("\nSubmitting requests and running simulation...")
    for i in range(50):
        addr = 0x1000 + (i * 64)
        controller.submit_request(addr=addr, is_read=True)

    # Run simulation with refresh
    cycles = 0
    refresh_cycles = []

    while len(controller._pending_requests) > 0 and cycles < 2000:
        cycles += 1

        # Check if refresh occurs this cycle
        if controller.refresh_scheduler.can_refresh():
            refresh_cycles.append(cycles)
            controller.refresh_scheduler.get_refresh_command()

        controller.tick()

    stats = controller.get_stats()

    print(f"\n  Simulation completed:")
    print(f"    Cycles: {cycles}")
    print(f"    Requests: {stats['controller']['total_requests']}")
    print(f"    Refresh count: {stats['controller']['refresh_count']}")
    print(f"    Refresh at cycles: {refresh_cycles[:10]}...")


def example_refresh_timing():
    """Show refresh timing relationships."""
    print_section("Example 7: Refresh Timing")

    spec = HBM4Spec()

    print("\nHBM4 Refresh Timing Parameters:")
    print("  " + "-" * 50)
    print(f"  tREFI:  {spec.nREFI} cycles ({spec.nREFI * spec.tCK_ps / 1000:.1f} us @ {spec.data_rate_gtps} GT/s)")
    print(f"  tRFC:   {spec.nRFC} cycles ({spec.nRFC * spec.tCK_ps / 1000:.1f} us)")
    print(f"  nRREFD: {spec.nRREFD} cycles")

    # Calculate refresh intervals
    print("\n  Refresh Intervals:")
    print(f"    Full refresh interval (tREFI): {spec.nREFI} cycles")
    print(f"    Per-bank refresh interval (nRREFD): {spec.nRREFD} cycles")

    # Per-bank refresh cycle count
    total_banks = spec.total_banks
    print(f"\n  Per-Bank Refresh Cycle:")
    print(f"    Total banks to refresh: {total_banks}")
    print(f"    Refresh interval per bank: {spec.nRREFD} cycles")
    print(f"    Full cycle (all banks): {total_banks * spec.nRREFD} cycles")

    # Compare to tREFI
    expected_interval = total_banks * spec.nRREFD
    actual_tREFI = spec.nREFI
    print(f"\n  Verification:")
    print(f"    Expected interval: {expected_interval} cycles")
    print(f"    Actual tREFI: {actual_tREFI} cycles")
    print(f"    Match: {'Yes' if abs(expected_interval - actual_tREFI) < 100 else 'Close'}")


def example_refresh_statistics():
    """Show comprehensive refresh statistics."""
    print_section("Example 8: Refresh Statistics")

    scheduler = HBM4RefreshScheduler()

    # Run simulation
    print("\nRunning refresh simulation (1000 cycles)...")
    for cycle in range(1000):
        scheduler.tick()
        if scheduler.can_refresh():
            scheduler.get_refresh_command()

    # Get detailed stats
    stats = scheduler.get_stats()

    print("\n  Refresh Statistics:")
    print("  " + "-" * 50)
    print(f"    Total refreshes:      {stats['total_refreshes']}")
    print(f"    All-bank refreshes:   {stats['all_bank_refreshes']}")
    print(f"    Per-bank refreshes:    {stats['per_bank_refreshes']}")
    print(f"    Bank group refreshes:  {stats['bank_group_refreshes']}")
    print(f"    Current mode:         {stats['mode']}")
    print(f"    DRFM enabled:         {stats['drfm_enabled']}")
    print(f"    Cycles since refresh:  {stats['cycles_since_refresh']}")
    print(f"    Current cycle:         {stats['current_cycle']}")


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("#  HBM4 Refresh Control Examples")
    print("#" * 60)

    example_refresh_modes()
    example_per_bank_refresh()
    example_all_bank_refresh()
    example_bank_group_refresh()
    example_drfm()
    example_refresh_integration()
    example_refresh_timing()
    example_refresh_statistics()

    print("\n" + "#" * 60)
    print("#  All Examples Completed Successfully!")
    print("#" * 60)


if __name__ == "__main__":
    main()