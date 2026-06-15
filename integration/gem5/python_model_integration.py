#!/usr/bin/env python3
"""
Python HBM Model Integration with External Simulators
Demonstrates integration between Python HBM model and gem5

This module provides:
1. Standalone Python model usage
2. Bridge interface for gem5 integration
3. Example workloads and benchmarks
"""

import sys
import os
import time
import argparse
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.controller.controller import HBMController
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT
from model.controller.request import HBMRequest, HBMResponse
from model.dram.dram_model import DRAMModel
from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern

# Import bridge module
from integration.gem5.bridge import (
    HBMBridge, BridgeConfig, MemoryRequest, MemoryResponse,
    RequestType, DualSimulatorBridge
)
from integration.gem5.hbm4_config import HBM4Presets, HBM4Timing


class PythonHBMBridge:
    """
    Bridge wrapper for Python HBM model
    Converts between gem5 requests and Python model requests
    """

    def __init__(self, hbm_config=None, use_hbm4=False):
        """Initialize Python HBM bridge

        Args:
            hbm_config: HBM configuration
            use_hbm4: Use HBM4 configuration
        """
        self.use_hbm4 = use_hbm4

        # Set default config
        if hbm_config is None:
            self.config = HBM4_DEFAULT if use_hbm4 else HBM3_DEFAULT
        else:
            self.config = hbm_config

        # Create Python model components
        self.controller = HBMController(self.config)
        self.dram = DRAMModel(
            hbm_version="hbm4" if use_hbm4 else "hbm3",
            stack_count=self.config.stack_count,
            banks_per_channel=self.config.banks_per_pseudo_channel
        )

        # Enable DRAM memory model
        self.dram.enable_memory_model()

        # Statistics
        self.request_counter = 0
        self.latency_histogram = []

        # Bridge interface
        self.bridge = HBMBridge()
        self.bridge.set_external_model(self)

    def submit_request(self, request: HBMRequest) -> bool:
        """Submit request to Python model

        Args:
            request: HBM request

        Returns:
            True if successful
        """
        return self.controller.submit_request(request)

    def tick(self) -> tuple:
        """Execute one simulation cycle

        Returns:
            Tuple of (scheduled_request, response)
        """
        return self.controller.tick()

    def process_gem5_request(self, gem5_req: MemoryRequest) -> Optional[MemoryResponse]:
        """Process gem5 request through Python model

        Args:
            gem5_req: Memory request from gem5

        Returns:
            Response to send back to gem5
        """
        # Convert gem5 request to HBM request
        hbm_req = HBMRequest(
            addr=gem5_req.addr,
            length=gem5_req.length,
            is_read=(gem5_req.request_type == RequestType.READ),
            qos=gem5_req.qos,
        )

        # Submit to controller
        self.controller.submit_request(hbm_req)

        # Process cycle
        scheduled, response = self.controller.tick()

        if response:
            # Convert response back to gem5 format
            return MemoryResponse(
                request_id=gem5_req.request_id,
                status=response.status,
                latency=response.latency,
                data=response.data,
                timestamp=gem5_req.timestamp,
            )
        else:
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics

        Returns:
            Dict with statistics
        """
        ctrl_stats = self.controller.get_stats()
        return {
            'controller': ctrl_stats,
            'total_requests': self.request_counter,
            'avg_latency_ns': sum(self.latency_histogram) / max(len(self.latency_histogram), 1),
        }


def run_standalone_simulation(args):
    """Run standalone Python HBM simulation

    Args:
        args: Command line arguments
    """
    print("=" * 60)
    print("Python HBM Model Simulation")
    print("=" * 60)

    # Select traffic pattern
    pattern_map = {
        'random': TrafficPattern.RANDOM,
        'sequential': TrafficPattern.SEQUENTIAL,
        'stride': TrafficPattern.STRIDE,
        'hotspot': TrafficPattern.HOT_SPOT,
    }
    pattern = pattern_map.get(args.pattern, TrafficPattern.RANDOM)

    # Create simulation config
    sim_config = SimulationConfig(
        simulation_time_us=args.duration,
        traffic_pattern=pattern,
        request_rate=args.rate,
        read_ratio=args.read_ratio,
        burst_size=args.burst_size,
    )

    # Update HBM config if specified
    if args.hbm4:
        sim_config.hbm_config = HBM4_DEFAULT
        print(f"Using HBM4 configuration")
    else:
        print(f"Using HBM3 configuration")

    print(f"\nConfiguration:")
    print(f"  Pattern: {args.pattern}")
    print(f"  Duration: {args.duration} us")
    print(f"  Request rate: {args.rate}")
    print(f"  Read ratio: {args.read_ratio}")

    # Run simulation
    start_time = time.time()
    sim = HBMSimulator(sim_config)
    stats = sim.run()
    elapsed = time.time() - start_time

    # Print results
    print(f"\nResults (completed in {elapsed:.2f}s):")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Completed: {stats.completed_requests}")
    print(f"  Row hit rate: {stats.row_hit_rate:.2%}")
    print(f"  Avg latency: {stats.avg_latency:.1f} cycles")
    print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
    print(f"  Efficiency: {stats.efficiency:.2%}")

    return stats


def run_bridge_simulation(args):
    """Run simulation with gem5 bridge

    Args:
        args: Command line arguments
    """
    print("=" * 60)
    print("Python HBM Model with gem5 Bridge")
    print("=" * 60)

    # Create bridge
    config = BridgeConfig(
        sync_interval_cycles=args.sync_interval,
        enable_batching=True,
        batch_size=32,
    )
    bridge = HBMBridge(config)

    # Create Python model
    use_hbm4 = args.hbm4
    model = PythonHBMBridge(use_hbm4=use_hbm4)
    bridge.set_external_model(model)

    # Enable bridge
    bridge.enable()

    print(f"\nBridge configuration:")
    print(f"  Sync interval: {args.sync_interval} cycles")
    print(f"  Batch size: {config.batch_size}")

    # Generate and submit requests
    print(f"\nGenerating {args.num_requests} requests...")
    num_requests = args.num_requests
    responses = []

    for i in range(num_requests):
        # Create gem5-style request
        import random
        gem5_req = MemoryRequest(
            request_id=i,
            request_type=RequestType.READ if random.random() < args.read_ratio else RequestType.WRITE,
            addr=random.randint(0, 0xFFFF_FFFF) & ~0x3F,  # 64-byte aligned
            length=args.burst_size,
            qos=random.randint(0, 15),
        )

        # Submit to bridge
        bridge.submit_request(gem5_req)

        # Sync periodically
        if i % args.sync_interval == 0:
            bridge.sync(i)

        # Get responses
        if i % 10 == 0:
            while not bridge._response_queue.empty():
                try:
                    resp = bridge._response_queue.get_nowait()
                    responses.append(resp)
                except:
                    break

    # Final sync
    bridge.sync(num_requests)

    # Drain remaining responses
    while not bridge._response_queue.empty():
        try:
            resp = bridge._response_queue.get_nowait()
            responses.append(resp)
        except:
            break

    # Print results
    print(f"\nResults:")
    print(f"  Total requests: {num_requests}")
    print(f"  Responses: {len(responses)}")
    print(f"  Pending: {bridge.get_request_count()}")

    if responses:
        latencies = [r.latency for r in responses if r.status == 'OK']
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            print(f"  Avg latency: {avg_latency:.2f} ns")
            print(f"  Max latency: {max_latency:.2f} ns")

    # Print bridge stats
    stats = bridge.get_stats()
    print(f"\nBridge statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def run_comparison_test(args):
    """Run comparison test between gem5 and Python model

    Args:
        args: Command line arguments
    """
    print("=" * 60)
    print("gem5 vs Python HBM Model Comparison")
    print("=" * 60)

    # Create dual bridge
    dual_bridge = DualSimulatorBridge()

    # Note: In real use, you would connect gem5 system here
    # For now, demonstrate the comparison interface

    print("\nNote: This test requires a running gem5 instance.")
    print("The Python model can be used standalone for validation.")
    print("\nTo run full comparison:")
    print("  1. Start gem5 with HBM4 config")
    print("  2. Connect gem5 to Python model via bridge")
    print("  3. Run workloads in both simulators")
    print("  4. Compare results using DualSimulatorBridge.compare_results()")


def benchmark_scaling(args):
    """Benchmark Python model with different configurations

    Args:
        args: Command line arguments
    """
    print("=" * 60)
    print("HBM Model Scaling Benchmark")
    print("=" * 60)

    # Test configurations
    configs = [
        ('HBM3 8ch', HBM3_DEFAULT, TrafficPattern.RANDOM),
        ('HBM3 8ch seq', HBM3_DEFAULT, TrafficPattern.SEQUENTIAL),
        ('HBM4 32ch', HBM4_DEFAULT, TrafficPattern.RANDOM),
        ('HBM4 32ch seq', HBM4_DEFAULT, TrafficPattern.SEQUENTIAL),
    ]

    results = []

    for name, config, pattern in configs:
        print(f"\n--- {name} ---")

        sim_config = SimulationConfig(
            simulation_time_us=args.duration,
            traffic_pattern=pattern,
            request_rate=0.5,
            read_ratio=0.7,
            hbm_config=config,
        )

        start = time.time()
        sim = HBMSimulator(sim_config)
        stats = sim.run()
        elapsed = time.time() - start

        results.append({
            'name': name,
            'throughput': stats.throughput_gbps,
            'latency': stats.avg_latency,
            'hit_rate': stats.row_hit_rate,
            'efficiency': stats.efficiency,
            'time': elapsed,
        })

        print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
        print(f"  Latency: {stats.avg_latency:.1f} cycles")
        print(f"  Hit rate: {stats.row_hit_rate:.2%}")
        print(f"  Time: {elapsed:.2f}s")

    # Summary
    print("\n" + "=" * 60)
    print("Benchmark Summary")
    print("=" * 60)
    print(f"{'Config':<20} {'BW (GB/s)':<12} {'Latency':<10} {'Hit Rate':<10} {'Time':<8}")
    print("-" * 60)
    for r in results:
        print(f"{r['name']:<20} {r['throughput']:<12.2f} {r['latency']:<10.1f} "
              f"{r['hit_rate']:<10.2%} {r['time']:<8.2f}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Python HBM Model Integration')

    parser.add_argument('--mode', type=str, default='standalone',
                       choices=['standalone', 'bridge', 'comparison', 'benchmark'],
                       help='Simulation mode')
    parser.add_argument('--hbm4', action='store_true',
                       help='Use HBM4 configuration')

    # Standalone/Benchmark options
    parser.add_argument('--pattern', type=str, default='random',
                       choices=['random', 'sequential', 'stride', 'hotspot'],
                       help='Traffic pattern')
    parser.add_argument('--duration', type=float, default=100.0,
                       help='Simulation duration (us)')
    parser.add_argument('--rate', type=float, default=0.5,
                       help='Request rate (0-1)')
    parser.add_argument('--read-ratio', type=float, default=0.7,
                       help='Read request ratio (0-1)')
    parser.add_argument('--burst-size', type=int, default=64,
                       help='Burst size in bytes')

    # Bridge options
    parser.add_argument('--sync-interval', type=int, default=100,
                       help='Bridge sync interval (cycles)')
    parser.add_argument('--num-requests', type=int, default=1000,
                       help='Number of requests for bridge mode')

    args = parser.parse_args()

    # Run selected mode
    if args.mode == 'standalone':
        run_standalone_simulation(args)
    elif args.mode == 'bridge':
        run_bridge_simulation(args)
    elif args.mode == 'comparison':
        run_comparison_test(args)
    elif args.mode == 'benchmark':
        benchmark_scaling(args)


if __name__ == '__main__':
    main()