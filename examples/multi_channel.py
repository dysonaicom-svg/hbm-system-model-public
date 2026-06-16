"""
Example: Multi-Channel HBM4 Simulation

This example demonstrates multi-channel operations in HBM4:
- 32 independent channels
- 64 pseudo-channels (2 per channel)
- Per-channel request submission
- Channel-level scheduling
- Multi-channel statistics

HBM4 Channel Architecture:
- 32 physical channels
- 2 pseudo-channels per channel (64 total)
- Each pseudo-channel has independent command queue
- Channels operate in parallel for maximum bandwidth

Run: python examples/multi_channel.py
"""

from model.dram.hbm4_spec import HBM4Spec
from model.dram.hbm4_channel_model import HBM4ChannelArray
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.dfi_interface import DFI5Interface


def main():
    print("=" * 60)
    print("HBM4 Multi-Channel Simulation Example")
    print("=" * 60)

    # Create HBM4 spec
    print("\n1. Creating HBM4 Specification...")
    spec = HBM4Spec()
    print(f"   - Channels: {spec.channels}")
    print(f"   - Pseudo-channels per channel: {spec.pseudo_channels_per_channel}")
    print(f"   - Total pseudo-channels: {spec.pseudo_channels}")
    print(f"   - Bank groups per pseudo-channel: {spec.bank_groups_per_channel}")
    print(f"   - Banks per pseudo-channel: {spec.banks_per_pseudo_channel}")
    print(f"   - Total banks: {spec.total_banks}")
    print(f"   - Rows per bank: {2 ** spec.ADDR_ROW_BITS}")

    # Create channel array model
    print("\n2. Creating HBM4 Channel Array...")
    channel_array = HBM4ChannelArray(spec=spec)
    print(f"   - Channel array created with {channel_array.num_channels} channels")

    # Show channel details
    print("\n3. Channel Details:")
    ch0 = channel_array.get_channel(0)
    print(f"   Channel 0:")
    print(f"   - Pseudo-channels: {len(ch0.pseudo_channels)}")
    for pch_idx, pch in enumerate(ch0.pseudo_channels):
        print(f"   - Pseudo-channel {pch_idx}: {len(pch.banks)} banks")

    # Test channel operations
    print("\n4. Channel Command Operations:")
    print("   Testing ACT command on channel 0, pseudo-channel 0, bank 0, row 100...")

    result = ch0.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
    print(f"   - ACT result: {'Success' if result else 'Failed'}")

    # Check bank state after ACT
    pc0 = ch0.pseudo_channels[0]
    bank0 = pc0.banks[0]
    print(f"   - Bank 0 state: {bank0.bank.state}")

    # Issue READ
    print("\n   Testing RD command...")
    result = ch0.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)
    print(f"   - RD result: {'Success' if result else 'Failed'}")

    # Precharge
    print("\n   Testing PRE command (after tRAS)...")
    for _ in range(25):  # tRAS = 20 cycles
        ch0.tick()

    result = ch0.issue_command('PRE', pseudo_channel=0, bank=0, row=0)
    print(f"   - PRE result: {'Success' if result else 'Failed'}")

    # Address decoding across channels
    print("\n5. Address Decoding Across All Channels:")
    decoder = HBM4AddressDecoder()

    print("   Mapping addresses to channels:")
    for ch in [0, 1, 8, 15, 31]:
        # Construct address with channel at bits 45:41
        addr = ((ch & 0x1F) << 41) | 0x8  # 8-byte aligned
        decoded = decoder.decode(addr)
        print(f"   - Addr 0x{addr:016X} -> Channel {decoded.channel_id}, "
              f"Row 0x{decoded.row_id:04X}")

    # Simulate multi-channel traffic
    print("\n6. Simulating Multi-Channel Traffic:")

    # Submit requests to different channels
    requests_per_channel = 10
    total_requests = 0

    for ch in range(8):  # First 8 channels
        addr = ((ch & 0x1F) << 41) | 0x8
        for i in range(requests_per_channel):
            # Alternate between pseudo-channels
            pch = i % 2
            req_addr = addr | (pch << 40)  # Pseudo-channel at bit 40
            total_requests += 1

    print(f"   - Total requests to submit: {total_requests}")
    print(f"   - Channels: 8")
    print(f"   - Requests per channel: {requests_per_channel}")

    # Simulate channel operations
    print("\n7. Channel State Transitions:")

    # Reset channel
    ch0.reset()

    # ACT -> READ -> PRE sequence
    print("   Sequence: ACT -> READ -> PRE")
    print("   Channel 0, Pseudo-channel 0, Bank 0, Row 100")

    ch0.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
    print("   - Issued ACT")
    print(f"     Bank state: {pc0.banks[0].bank.state}")

    ch0.tick()
    ch0.tick()  # tRCD = 2 cycles

    ch0.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)
    print("   - Issued RD")

    for _ in range(20):  # tCL = 20 cycles
        ch0.tick()

    ch0.issue_command('PRE', pseudo_channel=0, bank=0, row=0)
    print("   - Issued PRE")
    print(f"     Bank state: {pc0.banks[0].bank.state}")

    # DFI interface with multiple channels
    print("\n8. DFI Interface Multi-Channel Commands:")
    dfi = DFI5Interface()

    # Queue commands for multiple channels
    for ch in range(4):
        req = dfi.encode_command(
            'ACT',
            {'row': 100, 'bank': ch % 16, 'channel': ch, 'pseudo_channel': ch % 2},
            priority=8
        )
        dfi.queue_request(req)

    print(f"   - Queued {dfi.pending_request_count} commands across 4 channels")

    # Dequeue and process
    print("   Processing commands:")
    while dfi.pending_request_count > 0:
        req = dfi.get_next_request()
        if req:
            print(f"   - {req.command.name} ch={req.channel} pch={req.pseudo_channel} "
                  f"bank={req.bank}")

    # Statistics
    print("\n9. Channel Array Statistics:")
    print(f"   - Total channels: {channel_array.num_channels}")
    print(f"   - Active channels: {channel_array.num_channels}")

    # Channel timing
    print("\n10. HBM4 Timing Parameters:")
    print(f"   - tCK: {spec.tCK_ps} ps")
    print(f"   - tRCD: {spec.nRCDRD} cycles")
    print(f"   - tCL: {spec.nCL} cycles")
    print(f"   - tCWL: {spec.nCWL} cycles")
    print(f"   - tRAS: {spec.nRAS} cycles")
    print(f"   - tRP: {spec.nRP} cycles")
    print(f"   - tRC: {spec.nRC} cycles")
    print(f"   - tRFC: {spec.nRFC} cycles")
    print(f"   - tREFI: {spec.nREFI} cycles")

    print("\n" + "=" * 60)
    print("Multi-channel simulation example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()