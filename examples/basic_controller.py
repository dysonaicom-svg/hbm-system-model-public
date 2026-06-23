"""
Example: Basic HBM4 Controller Usage

This example demonstrates the basic usage of the HBM4Controller:
- Creating a controller instance
- Submitting read/write requests
- Running simulation cycles
- Retrieving statistics

Run: python examples/basic_controller.py
"""

from model.dram.HBM4_spec import HBM4Spec
from model.controller.HBM4_controller import HBM4Controller


def main():
    print("=" * 60)
    print("HBM4 Basic Controller Example")
    print("=" * 60)

    # Create controller with default HBM4 spec
    print("\n1. Creating HBM4 Controller...")
    controller = HBM4Controller()
    print(f"   - Channels: {controller.channels}")
    print(f"   - Pseudo-channels: {controller.pseudo_channels}")

    # Create controller with custom speed grade
    print("\n2. Creating HBM4 Controller @ 16 Gbps...")
    spec_16g = HBM4Spec(data_rate_gtps=16.0)
    controller_fast = HBM4Controller(spec=spec_16g)
    print(f"   - Data rate: {controller_fast.spec.data_rate_gtps} GT/s")
    print(f"   - Peak bandwidth: {controller_fast.spec.bandwidth_gbs:.0f} GB/s")

    # Submit read requests
    print("\n3. Submitting read requests...")
    read_addresses = [
        0x0001_0000_0000_0000,
        0x0002_0000_0000_0000,
        0x0003_0000_0000_0000,
    ]
    for i, addr in enumerate(read_addresses):
        request_id = controller.submit_request(
            addr=addr,
            is_read=True,
            qos_level=8,  # Normal priority
        )
        print(f"   - Read request {i+1}: id={request_id}, addr=0x{addr:016X}")

    # Submit write requests
    print("\n4. Submitting write requests...")
    write_addresses = [
        0x0011_0000_0000_0000,
        0x0012_0000_0000_0000,
    ]
    for i, addr in enumerate(write_addresses):
        request_id = controller.submit_request(
            addr=addr,
            is_read=False,
            qos_level=12,  # High priority for writes
        )
        print(f"   - Write request {i+1}: id={request_id}, addr=0x{addr:016X}")

    # Run simulation
    print("\n5. Running simulation for 500 cycles...")
    completed = 0
    for cycle in range(500):
        responses = controller.tick()
        for resp in responses:
            completed += 1
            print(f"   - Cycle {cycle}: Completed {resp.request_id}, "
                  f"latency={resp.latency}ns, status={resp.status}")

        if completed >= 5:
            print(f"   - All 5 requests completed at cycle {cycle}")
            break

    # Get statistics
    print("\n6. Controller Statistics:")
    stats = controller.get_stats()
    print(f"   - Total requests: {stats['controller']['total_requests']}")
    print(f"   - Read requests: {stats['controller']['read_requests']}")
    print(f"   - Write requests: {stats['controller']['write_requests']}")
    print(f"   - Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
    print(f"   - Average latency: {stats['controller']['average_latency_ns']:.1f}ns")
    print(f"   - Refresh count: {stats['controller']['refresh_count']}")

    # Bandwidth measurement
    print("\n7. Bandwidth Measurement:")
    bandwidth = controller.get_bandwidth_gbs()
    print(f"   - Effective bandwidth: {bandwidth:.2f} GB/s")
    print(f"   - Peak bandwidth: {controller.spec.bandwidth_gbs:.0f} GB/s")

    # DFI interface status
    if stats['dfi']:
        print("\n8. DFI Interface Status:")
        print(f"   - Enabled: {stats['dfi']['enabled']}")
        print(f"   - Ready: {stats['dfi']['ready']}")
        print(f"   - Low power state: {stats['dfi']['lp_state']}")
        print(f"   - Pending commands: {stats['dfi']['pending_commands']}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()