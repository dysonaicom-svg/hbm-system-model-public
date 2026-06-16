"""
Example: HBM4 Bandwidth Benchmarking

This example demonstrates bandwidth measurement in HBM4:
- Sequential access pattern (optimal row hit rate)
- Random access pattern (worst case)
- Mixed access patterns
- Different channel configurations
- Speed grade comparisons

Run: python examples/bandwidth_benchmark.py
"""

from model.dram.hbm4_spec import HBM4Spec, HBM4_SPEED_GRADES
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder


def run_sequential_access(controller, decoder, base_addr, num_requests):
    """Run sequential access pattern (same row, different columns)"""
    addr = base_addr
    for i in range(num_requests):
        controller.submit_request(addr=addr, is_read=True)
        # Stay in same row, increment column
        addr += 64  # 64-byte column increment

    # Run until complete
    start_time = controller.current_time_ns
    while len(controller._pending_requests) > 0:
        controller.tick()
    end_time = controller.current_time_ns

    elapsed_us = (end_time - start_time) / 1000  # Convert ns to us
    bytes_transferred = num_requests * 64
    bandwidth_gbs = bytes_transferred / elapsed_us / 1e6  # GB/s

    return bandwidth_gbs, elapsed_us


def run_row_hammer_access(controller, decoder, base_addr, num_requests):
    """Run row hammer pattern (alternating between two rows)"""
    row_a = base_addr
    row_b = base_addr + 0x10000  # Different row

    for i in range(num_requests):
        addr = row_a if (i % 2 == 0) else row_b
        controller.submit_request(addr=addr, is_read=True)

    # Run until complete
    start_time = controller.current_time_ns
    while len(controller._pending_requests) > 0:
        controller.tick()
    end_time = controller.current_time_ns

    elapsed_us = (end_time - start_time) / 1000
    bytes_transferred = num_requests * 64
    bandwidth_gbs = bytes_transferred / elapsed_us / 1e6

    return bandwidth_gbs, elapsed_us


def run_random_access(controller, decoder, num_requests):
    """Run random access pattern (different channels, rows)"""
    import random
    random.seed(42)

    for i in range(num_requests):
        # Random channel and row
        ch = random.randint(0, 31)
        row = random.randint(0, 65535)
        addr = (ch & 0x1F) << 41 | (row & 0xFFFF) << 17
        controller.submit_request(addr=addr, is_read=True)

    # Run until complete
    start_time = controller.current_time_ns
    while len(controller._pending_requests) > 0:
        controller.tick()
    end_time = controller.current_time_ns

    elapsed_us = (end_time - start_time) / 1000
    bytes_transferred = num_requests * 64
    bandwidth_gbs = bytes_transferred / elapsed_us / 1e6

    return bandwidth_gbs, elapsed_us


def main():
    print("=" * 60)
    print("HBM4 Bandwidth Benchmarking Example")
    print("=" * 60)

    # Show speed grades
    print("\n1. HBM4 Speed Grades:")
    print("   Speed Grade | Data Rate | Peak BW | tCK")
    print("   " + "-" * 40)
    for grade, (rate, bw, tck) in HBM4_SPEED_GRADES.items():
        print(f"   {grade:11s} | {rate:8.1f} GT/s | {bw:7.0f} GB/s | {tck:4.0f} ps")

    # Create controller
    print("\n2. Creating HBM4 Controller...")
    controller = HBM4Controller()
    spec = controller.spec
    print(f"   - Channels: {spec.channels}")
    print(f"   - Pseudo-channels: {spec.pseudo_channels}")
    print(f"   - Data rate: {spec.data_rate_gtps} GT/s")
    print(f"   - Peak bandwidth: {spec.bandwidth_gbs:.0f} GB/s")

    # Create address decoder
    decoder = HBM4AddressDecoder()

    # Sequential access benchmark
    print("\n3. Sequential Access Benchmark (1000 requests):")
    base_addr = 0x0001_0000_0000_0000
    bw, time_us = run_sequential_access(controller, decoder, base_addr, 1000)
    print(f"   - Bandwidth: {bw:.2f} GB/s")
    print(f"   - Time: {time_us:.2f} us")
    efficiency = (bw / spec.bandwidth_gbs) * 100
    print(f"   - Efficiency: {efficiency:.1f}% of peak")

    # Row hammer benchmark
    print("\n4. Row Hammer Benchmark (1000 requests, 2 rows):")
    controller = HBM4Controller()  # Reset
    bw, time_us = run_row_hammer_access(controller, decoder, base_addr, 1000)
    print(f"   - Bandwidth: {bw:.2f} GB/s")
    print(f"   - Time: {time_us:.2f} us")
    efficiency = (bw / spec.bandwidth_gbs) * 100
    print(f"   - Efficiency: {efficiency:.1f}% of peak")

    # Random access benchmark
    print("\n5. Random Access Benchmark (1000 requests):")
    controller = HBM4Controller()  # Reset
    bw, time_us = run_random_access(controller, decoder, 1000)
    print(f"   - Bandwidth: {bw:.2f} GB/s")
    print(f"   - Time: {time_us:.2f} us")
    efficiency = (bw / spec.bandwidth_gbs) * 100
    print(f"   - Efficiency: {efficiency:.1f}% of peak")

    # Compare speed grades
    print("\n6. Speed Grade Comparison (Sequential, 500 requests):")
    print("   Speed Grade | Data Rate | Measured BW | Efficiency")
    print("   " + "-" * 50)

    for grade_name in ['HBM4_8GT', 'HBM4_12GT', 'HBM4_16GT']:
        rate, expected_bw, _ = HBM4_SPEED_GRADES[grade_name]
        spec_grade = HBM4Spec(data_rate_gtps=rate)
        controller = HBM4Controller(spec=spec_grade)
        bw, _ = run_sequential_access(controller, decoder, base_addr, 500)
        efficiency = (bw / spec_grade.bandwidth_gbs) * 100
        print(f"   {grade_name:12s} | {rate:8.1f} GT/s | {bw:10.2f} GB/s | {efficiency:9.1f}%")

    # Multi-channel striping
    print("\n7. Multi-Channel Striping (1000 requests, 8 channels):")
    controller = HBM4Controller()

    # Distribute requests across 8 channels
    for i in range(1000):
        ch = i % 8  # First 8 channels
        addr = ((ch & 0x1F) << 41) | 0x8  # Channel at bits 45:41
        controller.submit_request(addr=addr, is_read=True)

    start_time = controller.current_time_ns
    while len(controller._pending_requests) > 0:
        controller.tick()
    end_time = controller.current_time_ns

    elapsed_us = (end_time - start_time) / 1000
    bytes_transferred = 1000 * 64
    bw = bytes_transferred / elapsed_us / 1e6
    efficiency = (bw / spec.bandwidth_gbs) * 100

    print(f"   - Bandwidth: {bw:.2f} GB/s")
    print(f"   - Efficiency: {efficiency:.1f}% of peak")

    # Get final statistics
    print("\n8. Final Controller Statistics:")
    stats = controller.get_stats()
    print(f"   - Total requests: {stats['controller']['total_requests']}")
    print(f"   - Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
    print(f"   - Average latency: {stats['controller']['average_latency_ns']:.1f} ns")

    print("\n" + "=" * 60)
    print("Bandwidth benchmarking example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()