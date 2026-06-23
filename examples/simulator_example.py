"""
Example: HBM4 Simulator Usage

This example demonstrates the HBMSimulator:
- Basic simulation setup
- Traffic generation patterns
- Statistics collection

Run: python examples/simulator_example.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
from model.controller.config import HBMConfig


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def example_basic_simulation():
    """Basic simulator usage."""
    print_section("Basic Simulator Usage")

    # Create configuration
    config = SimulationConfig(
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.5,
        read_ratio=0.8,
        simulation_time_us=50.0,
    )

    # Create simulator
    print("\n  Creating HBMSimulator...")
    sim = HBMSimulator(config)
    print(f"    - Traffic pattern: {config.traffic_pattern.name}")
    print(f"    - Request rate: {config.request_rate}")

    # Run simulation
    print("\n  Running simulation...")
    stats = sim.run()

    # Get statistics
    print("\n  Simulation Statistics:")
    print(f"    - Total cycles: {stats.total_cycles}")
    print(f"    - Completed requests: {stats.completed_requests}")
    if stats.completed_requests > 0:
        avg_latency = stats.total_latency_cycles / stats.completed_requests
        print(f"    - Average latency: {avg_latency:.2f} cycles")
    print(f"    - Row hits: {stats.row_hits}")
    print(f"    - Row misses: {stats.row_misses}")


def example_traffic_patterns():
    """Test different traffic patterns."""
    print_section("Traffic Generation Patterns")

    patterns = [
        (TrafficPattern.SEQUENTIAL, "Sequential access (optimal)"),
        (TrafficPattern.RANDOM, "Random access (worst case)"),
        (TrafficPattern.STRIDE, "Stride access (vector processing)"),
        (TrafficPattern.HOT_SPOT, "Hotspot access (20/80 rule)"),
    ]

    for pattern, desc in patterns:
        print(f"\n  {pattern.name} Pattern ({desc}):")
        print("  " + "-" * 50)

        config = SimulationConfig(
            traffic_pattern=pattern,
            simulation_time_us=50.0,
        )
        sim = HBMSimulator(config)

        stats = sim.run()
        print(f"    - Completed: {stats.completed_requests}")
        if stats.completed_requests > 0:
            avg_latency = stats.total_latency_cycles / stats.completed_requests
            print(f"    - Avg latency: {avg_latency:.2f} cycles")


def example_workload_simulation():
    """Simulate realistic workloads."""
    print_section("Realistic Workload Simulation")

    workloads = [
        ("Video Frame Processing", TrafficPattern.SEQUENTIAL),
        ("ML Training", TrafficPattern.RANDOM),
        ("Scientific Computing", TrafficPattern.STRIDE),
        ("Database Operations", TrafficPattern.HOT_SPOT),
    ]

    print("\n  Workload Simulation Results:")
    print("  " + "-" * 50)
    print(f"  {'Workload':25s} | {'Pattern':12s} | {'Completed':10s}")
    print("  " + "-" * 50)

    for name, pattern in workloads:
        config = SimulationConfig(
            traffic_pattern=pattern,
            simulation_time_us=50.0,
        )
        sim = HBMSimulator(config)

        stats = sim.run()
        print(f"  {name:25s} | {pattern.name:12s} | {stats.completed_requests:10d}")


def example_configuration():
    """Show simulator configuration options."""
    print_section("Simulator Configuration")

    print("\n  Configuration Options:")
    print("  " + "-" * 50)

    options = [
        ("traffic_pattern", "SEQUENTIAL, RANDOM, STRIDE, HOT_SPOT"),
        ("request_rate", "0.0 to 1.0 (traffic intensity)"),
        ("read_ratio", "0.0 to 1.0 (read/write ratio)"),
        ("burst_size", "Request burst size in bytes"),
        ("queue_depth", "Maximum pending requests"),
        ("max_requests_per_cycle", "Requests generated per cycle"),
        ("address_range", "Address space size"),
        ("simulation_time_us", "Simulation time in microseconds"),
    ]

    for name, desc in options:
        print(f"    - {name:25s}: {desc}")


def main():
    print("=" * 70)
    print("  HBM4 Simulator Usage Examples")
    print("=" * 70)

    example_basic_simulation()
    example_traffic_patterns()
    example_workload_simulation()
    example_configuration()

    print("\n" + "=" * 70)
    print("  Simulator examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
