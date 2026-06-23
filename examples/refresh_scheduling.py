"""
Example: HBM4 Refresh Scheduling

This example demonstrates refresh scheduling features:
- All-bank refresh mode
- Per-bank refresh mode (default for HBM4)
- Bank group refresh mode
- DRFM (Direct Refresh Management) for row-hammer mitigation
- Staggered refresh for reduced peak power

HBM4 Refresh Modes:
- ALL_BANKS: Refresh all banks at once (HBM2 style)
- PER_BANK: Staggered per-bank refresh (default, HBM3/HBM4 style)
- BANK_GROUP: Refresh by bank group

Run: python examples/refresh_scheduling.py
"""

from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.dram.hbm4_spec import HBM4Spec


def main():
    print("=" * 60)
    print("HBM4 Refresh Scheduling Example")
    print("=" * 60)

    # Create scheduler with default spec
    print("\n1. Creating HBM4RefreshScheduler...")
    scheduler = HBM4RefreshScheduler()
    print(f"   - Default mode: {scheduler.mode.value}")
    print(f"   - Refresh interval (tREFI): {scheduler.tREFI} cycles")
    print(f"   - Refresh duration (tRFC): {scheduler.tRFC} cycles")
    print(f"   - Per-bank interval (nRREFD): {scheduler.nRREFD} cycles")
    print(f"   - Supported modes: {[m.value for m in scheduler.supported_modes]}")

    # Show total banks tracked
    spec = HBM4Spec()
    print(f"   - Total banks tracked: {len(scheduler.bank_status)}")
    print(f"   - Banks per channel: {spec.total_banks // spec.channels}")

    # Demonstrate all-bank refresh mode
    print("\n2. All-Bank Refresh Mode:")
    scheduler.set_mode(RefreshMode.ALL_BANKS)
    print(f"   Mode set to: {scheduler.mode.value}")

    # Simulate until refresh is needed
    for cycle in range(scheduler.tREFI - 5):
        scheduler.tick()

    print(f"   After {scheduler.tREFI - 5} cycles:")
    print(f"   - Cycles since refresh: {scheduler.cycles_since_refresh}")
    print(f"   - Can refresh: {scheduler.can_refresh()}")

    # Execute refresh
    cmd = scheduler.get_refresh_command()
    if cmd:
        cmd_name, ch, pch, bank = cmd
        print(f"   - Refresh command: {cmd_name}")
        print(f"   - (No channel/pseudo-channel/bank for all-bank refresh)")

    # Demonstrate per-bank refresh mode
    print("\n3. Per-Bank Refresh Mode:")
    scheduler = HBM4RefreshScheduler()  # Reset
    scheduler.set_mode(RefreshMode.PER_BANK)
    print(f"   Mode set to: {scheduler.mode.value}")

    # Execute several per-bank refreshes
    print("   Executing first 10 per-bank refreshes:")
    for i in range(10):
        scheduler.tick()
        if scheduler.can_refresh():
            cmd = scheduler.get_refresh_command()
            if cmd:
                cmd_name, ch, pch, bank = cmd
                print(f"   - Refresh {i+1}: {cmd_name} ch={ch} pch={pch} bank={bank}")

    # Demonstrate bank group refresh mode
    print("\n4. Bank Group Refresh Mode:")
    scheduler = HBM4RefreshScheduler()  # Reset
    scheduler.set_mode(RefreshMode.BANK_GROUP)
    print(f"   Mode set to: {scheduler.mode.value}")

    # Execute several bank group refreshes
    print("   Executing first 5 bank group refreshes:")
    for i in range(5):
        scheduler.tick()
        if scheduler.can_refresh():
            cmd = scheduler.get_refresh_command()
            if cmd:
                cmd_name, ch, pch, bank = cmd
                print(f"   - Refresh {i+1}: {cmd_name} ch={ch} pch={pch} bank={bank}")

    # Demonstrate DRFM (Direct Refresh Management)
    print("\n5. DRFM (Direct Refresh Management):")
    scheduler = HBM4RefreshScheduler()  # Reset
    scheduler.enable_drfm(enabled=True, threshold=100)
    print(f"   DRFM enabled: {scheduler.drfm_enabled}")
    print(f"   Row-hammer threshold: {scheduler.drfm_rowhammer_threshold} cycles")

    # Simulate accesses that trigger row-hammer
    print("   Simulating row-hammer conditions...")
    for cycle in range(200):
        scheduler.tick()

    banks_needing_refresh = scheduler.get_banks_needing_refresh()
    print(f"   - Banks needing refresh: {len(banks_needing_refresh)}")

    # Show bank status tracking
    print("\n6. Bank Status Tracking:")
    print("   Sample of first 8 banks:")
    for i in range(8):
        status = scheduler.bank_status[i]
        print(f"   - Bank {i:2d}: last_refresh={status.last_refresh_cycle}, "
              f"needs_refresh={status.needs_refresh}")

    # Get statistics
    print("\n7. Refresh Statistics:")
    stats = scheduler.get_stats()
    print(f"   - Total refreshes: {stats['total_refreshes']}")
    print(f"   - All-bank refreshes: {stats['all_bank_refreshes']}")
    print(f"   - Per-bank refreshes: {stats['per_bank_refreshes']}")
    print(f"   - Bank group refreshes: {stats['bank_group_refreshes']}")
    print(f"   - Current cycle: {stats['current_cycle']}")
    print(f"   - DRFM enabled: {stats['drfm_enabled']}")

    # Modify refresh interval
    print("\n8. Modifying Refresh Interval:")
    print(f"   Default tREFI: {scheduler.tREFI} cycles")
    scheduler.set_refresh_interval(500)
    print(f"   Modified tREFI: {scheduler.tREFI} cycles")

    # Reset scheduler
    print("\n9. Resetting Scheduler:")
    scheduler.reset()
    print(f"   - Cycles since refresh: {scheduler.cycles_since_refresh}")
    print(f"   - Current refresh bank: {scheduler.current_refresh_bank}")
    print(f"   - Total refresh count: {scheduler.total_refresh_count}")

    print("\n" + "=" * 60)
    print("Refresh scheduling example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()