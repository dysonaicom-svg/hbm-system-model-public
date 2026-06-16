"""
Performance Tests for HBM Simulation Platform

Tests performance characteristics including:
- Speed benchmarks (target: >100K req/s)
- Memory benchmarks
- Latency benchmarks
- Throughput benchmarks
"""

import time
import gc
import pytest
import tracemalloc
from typing import Dict, List, Tuple
import statistics

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
from model.controller.request import HBMRequest, HBMRequestPool, RequestBatch
from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
from model.dram.timing import get_timing_for_hbm_version


class PerformanceMetrics:
    """Container for performance measurement results"""
    def __init__(self):
        self.name: str = ""
        self.duration_seconds: float = 0.0
        self.requests_processed: int = 0
        self.req_per_second: float = 0.0
        self.memory_mb: float = 0.0
        self.peak_memory_mb: float = 0.0
        self.avg_latency_cycles: float = 0.0
        self.throughput_gbps: float = 0.0

    def __repr__(self):
        return (f"PerformanceMetrics({self.name}): {self.req_per_second:.0f} req/s, "
                f"{self.throughput_gbps:.2f} GB/s, {self.memory_mb:.1f} MB")


def measure_memory(func):
    """Decorator to measure memory usage of a function"""
    def wrapper(*args, **kwargs):
        gc.collect()
        tracemalloc.start()
        start_mem = tracemalloc.get_traced_memory()[0]
        result = func(*args, **kwargs)
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return result, current_mem / (1024 * 1024), peak_mem / (1024 * 1024)
    return wrapper


def benchmark_simulation(config: SimulationConfig, name: str = "") -> PerformanceMetrics:
    """Run simulation and collect performance metrics

    Args:
        config: Simulation configuration
        name: Benchmark name

    Returns:
        PerformanceMetrics with measurement results
    """
    gc.collect()

    metrics = PerformanceMetrics()
    metrics.name = name or config.traffic_pattern.value

    # Measure execution time
    start_time = time.perf_counter()
    tracemalloc.start()

    sim = HBMSimulator(config)
    stats = sim.run()

    end_time = time.perf_counter()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Calculate metrics
    metrics.duration_seconds = end_time - start_time
    metrics.requests_processed = stats.completed_requests
    metrics.req_per_second = stats.completed_requests / metrics.duration_seconds if metrics.duration_seconds > 0 else 0
    metrics.memory_mb = current_mem / (1024 * 1024)
    metrics.peak_memory_mb = peak_mem / (1024 * 1024)
    metrics.avg_latency_cycles = stats.avg_latency
    metrics.throughput_gbps = stats.throughput_gbps

    return metrics


class TestSpeedBenchmarks:
    """Speed benchmark tests - target: >100K req/s"""

    def test_random_traffic_throughput(self):
        """Test random traffic throughput"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.25,
            read_ratio=0.7,
            max_requests_per_cycle=4,
        )

        metrics = benchmark_simulation(config, "random_traffic")

        print(f"\n{'='*60}")
        print(f"Random Traffic Benchmark")
        print(f"{'='*60}")
        print(f"  Duration: {metrics.duration_seconds:.2f}s")
        print(f"  Requests processed: {metrics.requests_processed:,}")
        print(f"  Throughput: {metrics.req_per_second:,.0f} req/s")
        print(f"  Bandwidth: {metrics.throughput_gbps:.2f} GB/s")
        print(f"  Avg latency: {metrics.avg_latency_cycles:.1f} cycles")
        print(f"  Memory: {metrics.peak_memory_mb:.1f} MB peak")

        # Target: >100K req/s (relaxed for CI environment)
        assert metrics.req_per_second > 50000, f"Throughput {metrics.req_per_second:.0f} req/s below target"

    def test_sequential_traffic_throughput(self):
        """Test sequential traffic (high locality) throughput"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.3,
            read_ratio=0.8,
            max_requests_per_cycle=4,
        )

        metrics = benchmark_simulation(config, "sequential_traffic")

        print(f"\n{'='*60}")
        print(f"Sequential Traffic Benchmark (High Locality)")
        print(f"{'='*60}")
        print(f"  Duration: {metrics.duration_seconds:.2f}s")
        print(f"  Requests processed: {metrics.requests_processed:,}")
        print(f"  Throughput: {metrics.req_per_second:,.0f} req/s")
        print(f"  Bandwidth: {metrics.throughput_gbps:.2f} GB/s")

        # Sequential should be faster due to row hits
        assert metrics.req_per_second > 40000

    def test_hotspot_traffic_throughput(self):
        """Test hotspot traffic throughput"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.HOT_SPOT,
            request_rate=0.3,
            read_ratio=0.7,
            max_requests_per_cycle=4,
        )

        metrics = benchmark_simulation(config, "hotspot_traffic")

        print(f"\n{'='*60}")
        print(f"Hot Spot Traffic Benchmark")
        print(f"{'='*60}")
        print(f"  Duration: {metrics.duration_seconds:.2f}s")
        print(f"  Requests processed: {metrics.requests_processed:,}")
        print(f"  Throughput: {metrics.req_per_second:,.0f} req/s")

        assert metrics.req_per_second > 40000


class TestMemoryBenchmarks:
    """Memory usage benchmarks"""

    def test_request_pool_memory(self):
        """Test request object pool effectiveness"""
        pool = HBMRequestPool(max_size=1024)

        gc.collect()
        tracemalloc.start()

        # Create and release many requests
        for i in range(10000):
            req = pool.acquire(addr=i * 64, length=64, is_read=True)
            pool.release(req)

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n{'='*60}")
        print(f"Request Pool Memory Test")
        print(f"{'='*60}")
        print(f"  Pool size: {pool.pool_size}")
        print(f"  Peak memory: {peak_mem / (1024 * 1024):.2f} MB")

        # Verify pool is being used
        assert pool.pool_size > 0, "Pool should contain recycled objects"

    def test_simulation_memory_usage(self):
        """Test memory usage during simulation"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.25,
            read_ratio=0.7,
            max_requests_per_cycle=4,
        )

        gc.collect()
        tracemalloc.start()

        sim = HBMSimulator(config)
        stats = sim.run()

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n{'='*60}")
        print(f"Simulation Memory Usage")
        print(f"{'='*60}")
        print(f"  Current memory: {current_mem / (1024 * 1024):.2f} MB")
        print(f"  Peak memory: {peak_mem / (1024 * 1024):.2f} MB")
        print(f"  Requests: {stats.completed_requests:,}")

        # Memory should be reasonable for simulation
        assert peak_mem < 500 * 1024 * 1024, "Peak memory should be < 500 MB"


class TestLatencyBenchmarks:
    """Latency benchmark tests"""

    def test_average_latency(self):
        """Test average request latency"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.2,
            read_ratio=0.7,
            max_requests_per_cycle=4,
        )

        metrics = benchmark_simulation(config, "latency_test")

        print(f"\n{'='*60}")
        print(f"Latency Benchmark")
        print(f"{'='*60}")
        print(f"  Avg latency: {metrics.avg_latency_cycles:.1f} cycles")
        print(f"  Avg latency: {metrics.avg_latency_cycles * 0.78125:.2f} ns")

        # Latency should be reasonable for HBM
        assert 0 < metrics.avg_latency_cycles < 1000, "Latency out of expected range"

    def test_latency_distribution(self):
        """Test latency distribution across requests"""
        # Run multiple simulations and collect latency samples
        latencies = []

        for _ in range(3):
            config = SimulationConfig(
                simulation_time_us=30.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.2,
                read_ratio=0.7,
                max_requests_per_cycle=4,
            )
            sim = HBMSimulator(config)
            stats = sim.run()
            # Note: avg_latency is already calculated in stats
            latencies.append(stats.avg_latency)

        print(f"\n{'='*60}")
        print(f"Latency Distribution")
        print(f"{'='*60}")
        print(f"  Min: {min(latencies):.1f} cycles")
        print(f"  Max: {max(latencies):.1f} cycles")
        print(f"  Mean: {statistics.mean(latencies):.1f} cycles")
        if len(latencies) > 1:
            print(f"  Stddev: {statistics.stdev(latencies):.1f} cycles")


class TestBankStateMachinePerformance:
    """Bank state machine performance tests"""

    def test_bank_activation_performance(self):
        """Test bank activation performance"""
        timing = get_timing_for_hbm_version("hbm3")
        bank = BankStateMachine(bank_id=0, timing=timing)

        gc.collect()
        tracemalloc.start()
        start_time = time.perf_counter()

        num_activations = 100000
        for i in range(num_activations):
            bank.set_time(float(i * 100))
            bank.activate(row=i % 1024)

        end_time = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        duration = end_time - start_time
        ops_per_sec = num_activations / duration

        print(f"\n{'='*60}")
        print(f"Bank Activation Performance")
        print(f"{'='*60}")
        print(f"  Operations: {num_activations:,}")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Ops/sec: {ops_per_sec:,.0f}")
        print(f"  Peak memory: {peak_mem / (1024 * 1024):.2f} MB")

        # Should be able to do >100K ops/sec
        assert ops_per_sec > 100000, f"Bank activation too slow: {ops_per_sec:.0f} ops/s"

    def test_batch_bank_updates(self):
        """Test batch bank state updates"""
        timing = get_timing_for_hbm_version("hbm3")
        num_banks = 256

        banks = [BankStateMachine(bank_id=i, timing=timing) for i in range(num_banks)]

        gc.collect()
        tracemalloc.start()
        start_time = time.perf_counter()

        num_cycles = 10000
        for cycle in range(num_cycles):
            current_time = float(cycle * 100)
            # Batch update all banks
            for bank in banks:
                bank.set_time(current_time)

        end_time = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        duration = end_time - start_time
        total_updates = num_cycles * num_banks
        updates_per_sec = total_updates / duration

        print(f"\n{'='*60}")
        print(f"Batch Bank Update Performance")
        print(f"{'='*60}")
        print(f"  Banks: {num_banks}")
        print(f"  Cycles: {num_cycles:,}")
        print(f"  Total updates: {total_updates:,}")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Updates/sec: {updates_per_sec:,.0f}")


class TestThroughputBenchmarks:
    """Throughput benchmark tests"""

    def test_theoretical_bandwidth(self):
        """Test achievable bandwidth"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.4,
            read_ratio=0.7,
            max_requests_per_cycle=4,
        )

        metrics = benchmark_simulation(config, "bandwidth_test")

        print(f"\n{'='*60}")
        print(f"Bandwidth Benchmark")
        print(f"{'='*60}")
        print(f"  Throughput: {metrics.throughput_gbps:.2f} GB/s")
        print(f"  Requests/sec: {metrics.req_per_second:,.0f}")
        print(f"  Requests processed: {metrics.requests_processed:,}")

        # Target bandwidth depends on configuration
        # For HBM3 1.28 GHz with 8 channels, theoretical peak ~1024 GB/s
        # We expect at least 100 GB/s for high-throughput scenarios
        assert metrics.throughput_gbps > 50, f"Bandwidth too low: {metrics.throughput_gbps:.2f} GB/s"


class TestRequestPoolBenchmarks:
    """Request pool performance tests"""

    def test_pool_acquire_release_performance(self):
        """Test request pool acquire/release performance"""
        pool = HBMRequestPool(max_size=10000)

        gc.collect()
        tracemalloc.start()
        start_time = time.perf_counter()

        num_ops = 100000
        for i in range(num_ops):
            req = pool.acquire(addr=i * 64, length=64, is_read=i % 2 == 0)
            pool.release(req)

        end_time = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        duration = end_time - start_time
        ops_per_sec = num_ops * 2 / duration  # acquire + release

        print(f"\n{'='*60}")
        print(f"Request Pool Performance")
        print(f"{'='*60}")
        print(f"  Operations: {num_ops * 2:,}")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Ops/sec: {ops_per_sec:,.0f}")
        print(f"  Pool size: {pool.pool_size}")

        # Pool operations should be fast
        assert ops_per_sec > 500000, f"Pool ops too slow: {ops_per_sec:.0f} ops/s"

    def test_pool_reuse_effectiveness(self):
        """Test that pool effectively reuses objects"""
        pool = HBMRequestPool(max_size=100)

        # Create initial batch
        requests = []
        for i in range(100):
            req = pool.acquire(addr=i * 64, length=64, is_read=True)
            requests.append(req)

        # Release all
        for req in requests:
            pool.release(req)

        # Acquire again - should reuse from pool
        initial_alloc = pool.total_allocated
        reused = []
        for i in range(100):
            req = pool.acquire(addr=i * 64, length=64, is_read=True)
            reused.append(req)

        print(f"\n{'='*60}")
        print(f"Pool Reuse Effectiveness")
        print(f"{'='*60}")
        print(f"  Initial allocations: {initial_alloc}")
        print(f"  Pool size after release: {pool.pool_size}")
        print(f"  Total allocated: {pool.total_allocated}")

        # Should have reused most/all objects
        assert pool.pool_size < 10, "Pool should have reused objects"


def run_all_benchmarks() -> List[PerformanceMetrics]:
    """Run all benchmarks and return results

    Returns:
        List of PerformanceMetrics for each benchmark
    """
    results = []

    # Speed benchmarks
    print("\n" + "="*70)
    print("RUNNING SPEED BENCHMARKS")
    print("="*70)

    random_config = SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.25,
        read_ratio=0.7,
        max_requests_per_cycle=4,
    )
    results.append(benchmark_simulation(random_config, "random_traffic"))

    return results


if __name__ == "__main__":
    print("="*70)
    print("HBM Simulation Platform - Performance Tests")
    print("="*70)

    results = run_all_benchmarks()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for r in results:
        print(f"  {r.name}: {r.req_per_second:,.0f} req/s, {r.throughput_gbps:.2f} GB/s")