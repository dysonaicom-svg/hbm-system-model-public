"""
HBM4 Multi-Channel Access Example

Demonstrates multi-channel operations in HBM4:
- 32 independent channels
- 64 pseudo-channels (2 per channel)
- Per-channel request submission
- Channel-level scheduling
- Multi-channel bandwidth measurement

HBM4 Channel Architecture:
- 32 physical channels
- 2 pseudo-channels per channel (64 total)
- Each pseudo-channel has independent command queue
- Channels operate in parallel for maximum bandwidth

Run: python examples/multi_channel_access.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.dram.HBM4_spec import HBM4Spec
from model.dram.HBM4_channel_model import HBM4ChannelArray, HBM4Channel
from model.controller.HBM4_controller import HBM4Controller
from model.controller.HBM4_address_decoder import HBM4AddressDecoder


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def example_channel_architecture():
    """Show HBM4 channel architecture."""
    print_section("Example 1: HBM4 Channel Architecture")

    spec = HBM4Spec()
    print(f"\nHBM4 Specification:")
    print(f"  Channels:              {spec.channels}")
    print(f"  Pseudo-channels/ch:     {spec.pseudo_channels_per_channel}")
    print(f"  Total pseudo-channels:  {spec.pseudo_channels}")
    print(f"  Bank groups/ch:         {spec.bank_groups_per_channel}")
    print(f"  Banks/pseudo-channel:   {spec.banks_per_pseudo_channel}")
    print(f"  Total banks:            {spec.total_banks}")
    print(f"  Rows per bank:          {2 ** spec.ADDR_ROW_BITS:,}")
    print(f"  IO width:               {spec.io_width} bits")
    print(f"  Peak bandwidth:         {spec.bandwidth:.3f} TB/s")

    # Channel array
    channel_array = HBM4ChannelArray(spec=spec)
    print(f"\nChannel Array:")
    print(f"  Total channels:         {len(channel_array.channels)}")
    print(f"  Per-channel bandwidth:   {channel_array.channels[0].peak_bandwidth_gbs:.1f} GB/s")
    print(f"  Total bandwidth:        {channel_array.total_bandwidth_gbs:.1f} GB/s")


def example_channel_commands():
    """Issue commands directly to channels."""
    print_section("Example 2: Direct Channel Commands")

    channel_array = HBM4ChannelArray()
    ch0 = channel_array.get_channel(0)

    print(f"\nChannel 0 Command Sequence:")
    print("  " + "-" * 50)

    # Issue ACT
    print("\n1. Issue ACT command:")
    result = ch0.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
    print(f"   Result: {'Success' if result else 'Failed'}")
    pc0 = ch0.pseudo_channels[0]
    bank0 = pc0.banks[0]
    print(f"   Bank 0 state: {bank0.bank.state}")

    # Wait tRCD cycles
    print("\n2. Wait tRCD (8 cycles)...")
    for _ in range(8):
        ch0.tick()
    print(f"   Bank 0 state after tRCD: {bank0.bank.state}")

    # Issue READ
    print("\n3. Issue RD command:")
    result = ch0.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)
    print(f"   Result: {'Success' if result else 'Failed'}")
    print(f"   Pseudo-channel state: {pc0.state}")

    # Wait tCL cycles
    print("\n4. Wait tCL (8 cycles) for data...")
    for _ in range(8):
        ch0.tick()

    # Issue PRE
    print("\n5. Issue PRE command:")
    result = ch0.issue_command('PRE', pseudo_channel=0, bank=0, row=0)
    print(f"   Result: {'Success' if result else 'Failed'}")
    print(f"   Bank 0 state after PRE: {bank0.bank.state}")

    # Get channel state
    print("\n6. Channel State Summary:")
    state = ch0.get_state_summary()
    print(f"   State: {state['state']}")
    print(f"   Cycle: {state['current_cycle']}")


def example_address_to_channel():
    """Map addresses to channels."""
    print_section("Example 3: Address to Channel Mapping")

    decoder = HBM4AddressDecoder()

    print("\nAddress Decoding Examples:")
    print("  " + "-" * 50)

    # Decode specific addresses
    test_cases = [
        (0x0000_0000_0000_0008, "Address 0x0"),
        (0x0020_0000_0000_0008, "Channel 1 address"),
        (0x0200_0000_0000_0008, "Channel 8 address"),
        (0x7E0_0000_0000_0008, "Channel 31 address"),
    ]

    for addr, desc in test_cases:
        decoded = decoder.decode(addr)
        print(f"\n  {desc}:")
        print(f"    Addr: 0x{addr:016X}")
        print(f"    Channel: {decoded.channel_id}")
        print(f"    Pseudo-channel: {decoded.pseudo_channel_id}")
        print(f"    Bank group: {decoded.bank_group_id}")
        print(f"    Bank: {decoded.bank_id}")
        print(f"    Row: 0x{decoded.row_id:04X}")


def example_multi_channel_traffic():
    """Simulate multi-channel traffic pattern."""
    print_section("Example 4: Multi-Channel Traffic Simulation")

    controller = HBM4Controller()

    print("\nSubmitting requests to all 32 channels...")
    print("  " + "-" * 50)

    requests_per_channel = 10
    total_requests = 0

    for ch in range(32):
        # Each channel gets sequential addresses
        base_addr = ((ch & 0x1F) << 41) | 0x8
        for i in range(requests_per_channel):
            addr = base_addr | ((i & 0xF) << 6)
            controller.submit_request(addr=addr, is_read=True)
            total_requests += 1

    print(f"  Total requests: {total_requests}")
    print(f"  Requests per channel: {requests_per_channel}")

    # Run simulation
    print("\nRunning simulation...")
    cycles = 0
    completed = 0

    while completed < total_requests and cycles < 2000:
        cycles += 1
        resp_list = controller.tick()
        completed += len(resp_list)

    stats = controller.get_stats()

    print(f"\n  Simulation completed:")
    print(f"    Cycles: {cycles}")
    print(f"    Completed: {completed}")
    print(f"    Avg latency: {stats['controller']['average_latency_ns']:.1f} ns")
    print(f"    Row hit rate: {stats['controller']['row_hit_rate']:.2%}")

    bandwidth = controller.get_bandwidth_gbs()
    print(f"    Bandwidth: {bandwidth:.2f} GB/s")
    print(f"    Peak: {controller.spec.bandwidth_gbs:.0f} GB/s")


def example_pseudo_channel():
    """Demonstrate pseudo-channel operations."""
    print_section("Example 5: Pseudo-Channel Operations")

    channel_array = HBM4ChannelArray()
    ch0 = channel_array.get_channel(0)

    print("\nPseudo-channel Configuration:")
    print("  " + "-" * 50)

    pc0 = ch0.pseudo_channels[0]
    pc1 = ch0.pseudo_channels[1]

    print(f"\n  Channel 0 Pseudo-channels:")
    print(f"    Pseudo-channel 0: {len(pc0.banks)} banks, {len(pc0.bank_groups)} bank groups")
    print(f"    Pseudo-channel 1: {len(pc1.banks)} banks, {len(pc1.bank_groups)} bank groups")

    print(f"\n  Bank Groups per Pseudo-channel:")
    for bg in pc0.bank_groups:
        print(f"    BG{bg.group_id}: banks {bg.bank_indices}")


def example_channel_parallelism():
    """Measure channel parallelism."""
    print_section("Example 6: Channel Parallelism Benchmark")

    print("\nComparing sequential vs parallel channel access:")
    print("  " + "-" * 50)

    # Sequential: all requests to one channel
    controller = HBM4Controller()
    for i in range(100):
        addr = 0x8 | ((i & 0xF) << 6)  # Channel 0
        controller.submit_request(addr=addr, is_read=True)

    cycles = 0
    while len(controller._pending_requests) > 0 and cycles < 1000:
        cycles += 1
        controller.tick()

    stats_single = controller.get_stats()
    print(f"\n  Single Channel (100 requests):")
    print(f"    Cycles: {cycles}")
    print(f"    Latency: {stats_single['controller']['average_latency_ns']:.1f} ns")

    # Parallel: requests spread across 8 channels
    controller = HBM4Controller()
    for i in range(100):
        ch = i % 8
        addr = ((ch & 0x1F) << 41) | 0x8 | ((i & 0xF) << 6)
        controller.submit_request(addr=addr, is_read=True)

    cycles = 0
    while len(controller._pending_requests) > 0 and cycles < 1000:
        cycles += 1
        controller.tick()

    stats_multi = controller.get_stats()
    print(f"\n  8 Channels Parallel (100 requests):")
    print(f"    Cycles: {cycles}")
    print(f"    Latency: {stats_multi['controller']['average_latency_ns']:.1f} ns")

    # Calculate improvement
    if stats_single['controller']['average_latency_ns'] > 0:
        speedup = stats_single['controller']['average_latency_ns'] / \
                  max(stats_multi['controller']['average_latency_ns'], 0.001)
        print(f"\n  Parallel Speedup: {speedup:.2f}x")


def example_per_channel_stats():
    """Show per-channel statistics."""
    print_section("Example 7: Per-Channel Statistics")

    controller = HBM4Controller()

    # Distribute requests across channels
    for ch in range(8):
        base_addr = ((ch & 0x1F) << 41) | 0x8
        for i in range(20):
            addr = base_addr | ((i & 0xF) << 6)
            controller.submit_request(addr=addr, is_read=True)

    # Run simulation
    while len(controller._pending_requests) > 0:
        controller.tick()

    # Show address decoder info
    print("\nChannel Distribution:")
    print("  " + "-" * 50)

    decoder = HBM4AddressDecoder()
    for ch in range(8):
        addr = ((ch & 0x1F) << 41) | 0x8
        decoded = decoder.decode(addr)
        print(f"  Channel {ch:2d}: addresses 0x{addr:016X} - 0x{addr + 0xFFF:016X}")

    stats = controller.get_stats()
    print(f"\n  Total requests: {stats['controller']['total_requests']}")
    print(f"  Peak bandwidth: {controller.spec.bandwidth_gbs:.0f} GB/s")


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("#  HBM4 Multi-Channel Access Examples")
    print("#" * 60)

    example_channel_architecture()
    example_channel_commands()
    example_address_to_channel()
    example_multi_channel_traffic()
    example_pseudo_channel()
    example_channel_parallelism()
    example_per_channel_stats()

    print("\n" + "#" * 60)
    print("#  All Examples Completed Successfully!")
    print("#" * 60)


if __name__ == "__main__":
    main()