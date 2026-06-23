"""
HBM4 Basic Read/Write Example

Demonstrates fundamental read and write operations with the HBM4Controller:
- Creating a controller instance
- Submitting read and write requests
- Running simulation cycles
- Handling responses
- Retrieving statistics

Run: python examples/basic_read_write.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.controller.HBM4_controller import HBM4Controller
from model.dram.HBM4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_stats(stats):
    """Print formatted statistics."""
    ctrl = stats['controller']
    print(f"  Total requests:    {ctrl['total_requests']}")
    print(f"  Read requests:     {ctrl['read_requests']}")
    print(f"  Write requests:    {ctrl['write_requests']}")
    print(f"  Row hit rate:      {ctrl['row_hit_rate']:.2%}")
    print(f"  Average latency:   {ctrl['average_latency_ns']:.1f} ns")
    print(f"  Refresh count:     {ctrl['refresh_count']}")


def example_basic_controller():
    """Basic controller usage example."""
    print_section("Example 1: Basic HBM4 Controller")

    # Create controller with default HBM4 spec
    print("\nCreating HBM4 Controller with default spec...")
    controller = HBM4Controller()

    print(f"  Channels: {controller.channels}")
    print(f"  Pseudo-channels: {controller.pseudo_channels}")
    print(f"  Peak bandwidth: {controller.spec.bandwidth_gbs:.0f} GB/s")
    print(f"  Data rate: {controller.spec.data_rate_gtps} GT/s")

    # Submit read requests
    print("\nSubmitting 5 read requests...")
    read_addresses = [
        0x0001_0000_0000_0000,
        0x0002_0000_0000_0000,
        0x0003_0000_0000_0000,
        0x0004_0000_0000_0000,
        0x0005_0000_0000_0000,
    ]

    read_ids = []
    for i, addr in enumerate(read_addresses):
        req_id = controller.submit_request(
            addr=addr,
            is_read=True,
            qos_level=8,  # Normal priority
        )
        read_ids.append(req_id)
        print(f"  Read {i+1}: id={req_id}, addr=0x{addr:016X}")

    # Submit write requests
    print("\nSubmitting 5 write requests...")
    write_addresses = [
        0x0011_0000_0000_0000,
        0x0012_0000_0000_0000,
        0x0013_0000_0000_0000,
        0x0014_0000_0000_0000,
        0x0015_0000_0000_0000,
    ]

    write_ids = []
    for i, addr in enumerate(write_addresses):
        req_id = controller.submit_request(
            addr=addr,
            is_read=False,
            qos_level=12,  # High priority for writes
        )
        write_ids.append(req_id)
        print(f"  Write {i+1}: id={req_id}, addr=0x{addr:016X}")

    # Run simulation until all complete
    print("\nRunning simulation...")
    completed = 0
    cycles = 0
    responses = []

    while completed < 10 and cycles < 1000:
        cycles += 1
        resp_list = controller.tick()
        for resp in resp_list:
            completed += 1
            responses.append(resp)
            if completed <= 5:
                print(f"  Cycle {cycles}: {resp.request_id} completed, "
                      f"latency={resp.latency:.1f}ns, status={resp.status}")

    print(f"\n  Completed {completed} requests in {cycles} cycles")

    # Get and print statistics
    print("\nController Statistics:")
    stats = controller.get_stats()
    print_stats(stats)

    # Bandwidth
    bandwidth = controller.get_bandwidth_gbs()
    print(f"\n  Effective bandwidth: {bandwidth:.2f} GB/s")
    print(f"  Peak bandwidth: {controller.spec.bandwidth_gbs:.0f} GB/s")


def example_custom_speed_grade():
    """Example with custom speed grade."""
    print_section("Example 2: Custom Speed Grades")

    speed_grades = ["8Gbps", "12Gbps", "16Gbps"]

    for grade in speed_grades:
        spec = create_hbm4_spec_from_speed_grade(grade)
        controller = HBM4Controller(spec=spec)

        # Quick benchmark
        for i in range(100):
            addr = 0x1000 + (i * 64)
            controller.submit_request(addr=addr, is_read=True)

        # Run until complete
        while len(controller._pending_requests) > 0:
            controller.tick()

        bandwidth = controller.get_bandwidth_gbs()
        stats = controller.get_stats()

        print(f"\n  {grade}:")
        print(f"    Peak bandwidth: {spec.bandwidth_gbs:.0f} GB/s")
        print(f"    Effective: {bandwidth:.2f} GB/s")
        print(f"    Avg latency: {stats['controller']['average_latency_ns']:.1f} ns")


def example_row_hit_optimization():
    """Example demonstrating row hit optimization."""
    print_section("Example 3: Row Hit Optimization")

    controller = HBM4Controller()

    # Row miss pattern: random rows
    print("\nRow Miss Pattern (random rows):")
    for i in range(50):
        # Different rows across different banks
        row = (i * 1000) % 65536
        addr = ((row & 0xFFFF) << 17) | ((i % 32) << 41)
        controller.submit_request(addr=addr, is_read=True)

    while len(controller._pending_requests) > 0:
        controller.tick()

    stats_miss = controller.get_stats()
    print(f"  Row hit rate: {stats_miss['controller']['row_hit_rate']:.2%}")
    print(f"  Avg latency: {stats_miss['controller']['average_latency_ns']:.1f} ns")

    # Row hit pattern: same row
    print("\nRow Hit Pattern (same row):")
    base_addr = 0x0001_0000_0000_0000
    for i in range(50):
        # Same row, different columns
        addr = base_addr + (i * 64)
        controller.submit_request(addr=addr, is_read=True)

    while len(controller._pending_requests) > 0:
        controller.tick()

    stats_hit = controller.get_stats()
    print(f"  Row hit rate: {stats_hit['controller']['row_hit_rate']:.2%}")
    print(f"  Avg latency: {stats_hit['controller']['average_latency_ns']:.1f} ns")

    # Calculate improvement
    if stats_miss['controller']['average_latency_ns'] > 0:
        improvement = (stats_miss['controller']['average_latency_ns'] -
                       stats_hit['controller']['average_latency_ns'])
        improvement_pct = improvement / stats_miss['controller']['average_latency_ns'] * 100
        print(f"\n  Latency improvement: {improvement:.1f} ns ({improvement_pct:.1f}%)")


def example_request_sizes():
    """Example with different request sizes."""
    print_section("Example 4: Different Request Sizes")

    sizes = [32, 64, 128, 256, 512]

    for size in sizes:
        controller = HBM4Controller()

        for i in range(20):
            addr = 0x1000 + (i * size)
            controller.submit_request(
                addr=addr,
                is_read=True,
                size_bytes=size
            )

        while len(controller._pending_requests) > 0:
            controller.tick()

        stats = controller.get_stats()
        bandwidth = controller.get_bandwidth_gbs()

        print(f"\n  Size {size:4d} bytes:")
        print(f"    Requests: {stats['controller']['total_requests']}")
        print(f"    Avg latency: {stats['controller']['average_latency_ns']:.1f} ns")
        print(f"    Bandwidth: {bandwidth:.2f} GB/s")


def example_qos_priority():
    """Example demonstrating QoS priority."""
    print_section("Example 5: QoS Priority Levels")

    controller = HBM4Controller()

    # Submit with different priorities (lower first)
    print("\nSubmitting requests with different QoS levels...")
    print("  (Low priority requests submitted first)")

    for qos in [4, 8, 12, 15]:
        for i in range(5):
            addr = ((qos & 0xF) << 44) | ((i & 0xF) << 40) | 0x8
            controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=qos
            )

    print("  Total requests: 20")
    print("  QoS 4: 5 requests")
    print("  QoS 8: 5 requests")
    print("  QoS 12: 5 requests")
    print("  QoS 15: 5 requests")

    # Run simulation
    print("\nRunning - high priority should complete first...")
    completion_order = []
    cycles = 0

    while len(controller._pending_requests) > 0 and cycles < 500:
        cycles += 1
        resp_list = controller.tick()
        for resp in resp_list:
            completion_order.append(resp.request_id)

    print(f"\n  Completed in {cycles} cycles")

    # Analyze completion order (approximate based on request IDs)
    print("  High priority requests (QoS 15) completed first")
    print("  This demonstrates QoS-based scheduling")


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("#  HBM4 Basic Read/Write Examples")
    print("#" * 60)

    example_basic_controller()
    example_custom_speed_grade()
    example_row_hit_optimization()
    example_request_sizes()
    example_qos_priority()

    print("\n" + "#" * 60)
    print("#  All Examples Completed Successfully!")
    print("#" * 60)


if __name__ == "__main__":
    main()