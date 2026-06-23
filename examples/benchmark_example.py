"""
HBM4 Performance Benchmark Example

Demonstrates performance benchmarking:
- Bandwidth measurement
- Latency measurement
- Row hit rate optimization
- Multi-channel parallelism
- Sequential vs random access patterns

Run: python examples/benchmark_example.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.controller.HBM4_controller import HBM4Controller
from model.dram.HBM4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.HBM4_channel_model import HBM4ChannelArray
from model.controller.HBM4_address_decoder import HBM4AddressDecoder


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def benchmark(name, func):
    """Run a benchmark and return timing."""
    start = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - start
    print(f"\n  Time: {elapsed*1000:.2f} ms")
    return result, elapsed


def example_bandwidth_benchmark():
    """Measure bandwidth for different access patterns."""
    print_section("Benchmark 1: Bandwidth by Access Pattern")

    patterns = [
        ("Sequential (row hits)", "sequential"),
        ("Random (row misses)", "random"),
        ("Channel striped", "striped"),
    ]

    import random
    random.seed(42)  # Reproducible results

    results = {}

    for pattern_name, pattern in patterns:
        print(f"\n  {pattern_name}:")
        print("  " + "-" * 50)

        controller = HBM4Controller()
        num_requests = 1000

        # Generate addresses based on pattern
        if pattern == "sequential":
            base_addr = 0x0001_0000_0000_0000
            addresses = [base_addr + (i * 64) for i in range(num_requests)]
        elif pattern == "random":
            addresses = []
            for i in range(num_requests):
                row = random.randint(0, 65535)
                ch = random.randint(0, 31)
                addr = ((ch & 0x1F) << 41) | ((row & 0xFFFF) << 17) | ((i % 64) << 6) | 0x8
                addresses.append(addr)
        else:  # striped
            addresses = []
            for i in range(num_requests):
                ch = i % 32
                addr = ((ch & 0x1F) << 41) | ((i // 32) << 6) | 0x8
                addresses.append(addr)

        # Submit requests
        for addr in addresses:
            controller.submit_request(addr=addr, is_read=True)

        # Run simulation
        _, elapsed = benchmark("Simulation", lambda: run_until_complete(controller))

        # Get results
        stats = controller.get_stats()
        bandwidth = controller.get_bandwidth_gbs()

        print(f"    Requests: {num_requests}")
        print(f"    Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
        print(f"    Avg latency: {stats['controller']['average_latency_ns']:.1f} ns")
        print(f"    Bandwidth: {bandwidth:.2f} GB/s")

        results[pattern] = {
            'bandwidth': bandwidth,
            'latency': stats['controller']['average_latency_ns'],
            'row_hit_rate': stats['controller']['row_hit_rate'],
        }

    # Summary
    print("\n  Summary:")
    print("  " + "-" * 50)
    best = max(results.items(), key=lambda x: x[1]['bandwidth'])
    print(f"    Best pattern: {best[0]} ({best[1]['bandwidth']:.2f} GB/s)")
    print(f"    Sequential bandwidth: {results['sequential']['bandwidth']:.2f} GB/s")
    print(f"    Random bandwidth: {results['random']['bandwidth']:.2f} GB/s")


def example_speed_grade_comparison():
    """Compare performance across speed grades."""
    print_section("Benchmark 2: Speed Grade Comparison")

    grades = ["8Gbps", "12Gbps", "16Gbps"]

    print("\n  Comparing speed grades:")
    print("  " + "-" * 50)

    results = {}

    for grade in grades:
        spec = create_hbm4_spec_from_speed_grade(grade)
        controller = HBM4Controller(spec=spec)

        # Submit requests
        base_addr = 0x1000
        for i in range(500):
            addr = base_addr + (i * 64)
            controller.submit_request(addr=addr, is_read=True)

        # Run simulation
        _, elapsed = benchmark(f"{grade} simulation", lambda: run_until_complete(controller))

        stats = controller.get_stats()
        bandwidth = controller.get_bandwidth_gbs()

        print(f"\n  {grade}:")
        print(f"    Peak bandwidth: {spec.bandwidth_gbs:.0f} GB/s")
        print(f"    Effective: {bandwidth:.2f} GB/s")
        print(f"    Avg latency: {stats['controller']['average_latency_ns']:.1f} ns")
        print(f"    Efficiency: {bandwidth / spec.bandwidth_gbs * 100:.1f}%")

        results[grade] = {
            'bandwidth': bandwidth,
            'peak': spec.bandwidth_gbs,
            'efficiency': bandwidth / spec.bandwidth_gbs * 100,
        }

    # Summary
    print("\n  Efficiency Summary:")
    print("  " + "-" * 50)
    for grade, data in results.items():
        print(f"    {grade}: {data['efficiency']:.1f}% efficiency")


def example_channel_count_scaling():
    """Show how bandwidth scales with channel count."""
    print_section("Benchmark 3: Channel Count Scaling")

    print("\n  Bandwidth vs Active Channels:")
    print("  " + "-" * 50)

    results = {}

    for num_channels in [1, 2, 4, 8, 16, 32]:
        controller = HBM4Controller()

        # Distribute requests across channels
        requests_per_channel = 100
        for i in range(num_channels * requests_per_channel):
            ch = i % num_channels
            addr = ((ch & 0x1F) << 41) | ((i // num_channels) << 6) | 0x8
            controller.submit_request(addr=addr, is_read=True)

        # Run simulation
        _, elapsed = benchmark(f"{num_channels} channels", lambda: run_until_complete(controller))

        stats = controller.get_stats()
        bandwidth = controller.get_bandwidth_gbs()

        # Calculate theoretical peak
        per_channel_bw = controller.spec.bandwidth_gbs / controller.spec.channels
        theoretical = per_channel_bw * num_channels

        print(f"\n  {num_channels} channels:")
        print(f"    Requests: {num_channels * requests_per_channel}")
        print(f"    Bandwidth: {bandwidth:.2f} GB/s")
        print(f"    Theoretical: {theoretical:.2f} GB/s")
        print(f"    Efficiency: {bandwidth / theoretical * 100:.1f}%")

        results[num_channels] = {
            'bandwidth': bandwidth,
            'theoretical': theoretical,
        }

    # Summary
    print("\n  Scaling Summary:")
    print("  " + "-" * 50)
    for num_ch, data in results.items():
        print(f"    {num_ch:2d} channels: {data['bandwidth']:.2f} GB/s "
              f"({data['bandwidth']/data['theoretical']*100:.1f}% of theoretical)")


def example_queue_depth_impact():
    """Show impact of queue depth on performance."""
    print_section("Benchmark 4: Queue Depth Impact")

    print("\n  Request Throughput vs Queue Depth:")
    print("  " + "-" * 50)

    results = {}

    for queue_depth in [8, 16, 32, 64, 128]:
        controller = HBM4Controller()

        # Submit requests (may be limited by queue)
        num_requests = 500
        submitted = 0

        for i in range(num_requests):
            addr = 0x1000 + (i * 64)
            req_id = controller.submit_request(addr=addr, is_read=True)
            if req_id:
                submitted += 1

        # Run simulation
        _, elapsed = benchmark(f"queue depth {queue_depth}", lambda: run_until_complete(controller))

        stats = controller.get_stats()
        bandwidth = controller.get_bandwidth_gbs()

        print(f"\n  Queue depth {queue_depth}:")
        print(f"    Submitted: {submitted}/{num_requests}")
        print(f"    Bandwidth: {bandwidth:.2f} GB/s")
        print(f"    Avg latency: {stats['controller']['average_latency_ns']:.1f} ns")

        results[queue_depth] = {
            'submitted': submitted,
            'bandwidth': bandwidth,
        }


def example_latency_distribution():
    """Measure latency distribution."""
    print_section("Benchmark 5: Latency Distribution")

    print("\n  Latency by Request Type:")
    print("  " + "-" * 50)

    controller = HBM4Controller()

    # Row hit requests
    base_addr = 0x0001_0000_0000_0000
    for i in range(100):
        addr = base_addr + (i * 64)
        controller.submit_request(addr=addr, is_read=True)

    # Collect latencies
    row_hit_latencies = []
    while len(controller._pending_requests) > 0:
        controller.tick()
        # Would need to capture individual latencies here

    stats = controller.get_stats()
    print(f"\n  Row Hit Latency:")
    print(f"    Average: {stats['controller']['average_latency_ns']:.1f} ns")

    # Reset and test row miss
    controller = HBM4Controller()

    import random
    random.seed(42)

    for i in range(100):
        row = random.randint(0, 65535)
        addr = ((row & 0xFFFF) << 17) | 0x8
        controller.submit_request(addr=addr, is_read=True)

    run_until_complete(controller)

    stats = controller.get_stats()
    print(f"\n  Row Miss Latency:")
    print(f"    Average: {stats['controller']['average_latency_ns']:.1f} ns")

    # Calculate difference
    print(f"\n  Latency Difference:")
    print(f"    Row miss penalty: "
          f"{stats['controller']['average_latency_ns'] - 0:.1f} ns")


def example_write_performance():
    """Benchmark write performance."""
    print_section("Benchmark 6: Write Performance")

    print("\n  Write vs Read Comparison:")
    print("  " + "-" * 50)

    # Read benchmark
    controller = HBM4Controller()
    for i in range(500):
        addr = 0x1000 + (i * 64)
        controller.submit_request(addr=addr, is_read=True)

    _, read_elapsed = benchmark("Read simulation", lambda: run_until_complete(controller))
    read_stats = controller.get_stats()
    read_bw = controller.get_bandwidth_gbs()

    print(f"\n  Reads:")
    print(f"    Time: {read_elapsed*1000:.2f} ms")
    print(f"    Bandwidth: {read_bw:.2f} GB/s")

    # Write benchmark
    controller = HBM4Controller()
    for i in range(500):
        addr = 0x1000 + (i * 64)
        controller.submit_request(addr=addr, is_read=False)

    _, write_elapsed = benchmark("Write simulation", lambda: run_until_complete(controller))
    write_stats = controller.get_stats()
    write_bw = controller.get_bandwidth_gbs()

    print(f"\n  Writes:")
    print(f"    Time: {write_elapsed*1000:.2f} ms")
    print(f"    Bandwidth: {write_bw:.2f} GB/s")

    # Comparison
    print(f"\n  Read/Write Ratio: {read_bw/write_bw:.2f}x")


def example_overall_summary():
    """Show overall performance summary."""
    print_section("Benchmark 7: Overall Performance Summary")

    controller = HBM4Controller()
    spec = controller.spec

    print(f"\n  HBM4 Configuration:")
    print("  " + "-" * 50)
    print(f"    Data rate: {spec.data_rate_gtps} GT/s")
    print(f"    IO width: {spec.io_width} bits")
    print(f"    Channels: {spec.channels}")
    print(f"    Pseudo-channels: {spec.pseudo_channels}")

    # Peak bandwidth
    print(f"\n  Theoretical Peak:")
    print("  " + "-" * 50)
    print(f"    Bandwidth: {spec.bandwidth:.3f} TB/s")
    print(f"    Per channel: {spec.bandwidth_gbs / spec.channels:.1f} GB/s")

    # Run comprehensive benchmark
    print(f"\n  Benchmark Results:")
    print("  " + "-" * 50)

    # Sequential benchmark
    controller = HBM4Controller()
    for i in range(1000):
        addr = 0x1000 + (i * 64)
        controller.submit_request(addr=addr, is_read=True)

    run_until_complete(controller)
    stats = controller.get_stats()
    bandwidth = controller.get_bandwidth_gbs()

    print(f"    Sequential bandwidth: {bandwidth:.2f} GB/s")
    print(f"    Peak bandwidth: {spec.bandwidth_gbs:.0f} GB/s")
    print(f"    Efficiency: {bandwidth / spec.bandwidth_gbs * 100:.1f}%")
    print(f"    Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
    print(f"    Avg latency: {stats['controller']['average_latency_ns']:.1f} ns")


def run_until_complete(controller, max_cycles=5000):
    """Run simulation until all requests complete."""
    cycles = 0
    while len(controller._pending_requests) > 0 and cycles < max_cycles:
        cycles += 1
        controller.tick()
    return cycles


def main():
    """Run all benchmarks."""
    print("\n" + "#" * 60)
    print("#  HBM4 Performance Benchmark Suite")
    print("#" * 60)

    example_bandwidth_benchmark()
    example_speed_grade_comparison()
    example_channel_count_scaling()
    example_queue_depth_impact()
    example_latency_distribution()
    example_write_performance()
    example_overall_summary()

    print("\n" + "#" * 60)
    print("#  All Benchmarks Completed!")
    print("#" * 60)


if __name__ == "__main__":
    main()