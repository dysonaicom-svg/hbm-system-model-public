"""
Performance Benchmark Tests for HBM System Optimization

This module provides comprehensive benchmarking to measure the performance
improvements from the optimization changes.

Benchmark Categories:
1. Memory usage (object size, allocation count)
2. Execution speed (simulation throughput, latency)
3. CPU utilization
4. Specific component benchmarks
"""

import time
import gc
import sys
import tracemalloc
from dataclasses import is_dataclass, fields
from typing import List, Dict, Any, Type, get_type_hints
import random

# Import modules to benchmark
from model.controller.request import HBMRequest, HBMResponse, HBMRequestPool, RequestBatch
from model.dram.bank_state_machine import Bank, BankStateMachine, TimingViolation
from model.controller.scheduler import FRFCFSScheduler, BankState, SchedulerStats
from model.controller.queue import RequestQueue, ReadQueue, WriteQueue
from model.controller.config import HBMConfig, HBM3_DEFAULT
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern


def get_object_size(obj: Any) -> int:
    """Get object size including all referenced objects"""
    size = sys.getsizeof(obj)
    # Handle objects with __slots__ (no __dict__)
    if hasattr(obj, '__slots__'):
        for slot in obj.__slots__:
            try:
                value = getattr(obj, slot, None)
                if value is not None and not callable(value):
                    size += sys.getsizeof(value)
            except AttributeError:
                pass
    else:
        # Standard objects with __dict__
        size += sum(sys.getsizeof(v) for v in vars(obj).values() if not callable(v))
    return size


def measure_memory_usage(func, iterations: int = 1000) -> Dict[str, float]:
    """Measure memory usage of a function"""
    gc.collect()
    tracemalloc.start()

    start_mem = tracemalloc.get_traced_memory()[0]

    for _ in range(iterations):
        func()

    end_mem = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()

    return {
        'start_mb': start_mem / 1024 / 1024,
        'end_mb': end_mem / 1024 / 1024,
        'delta_mb': (end_mem - start_mem) / 1024 / 1024,
        'per_iteration_kb': (end_mem - start_mem) / iterations / 1024,
    }


def benchmark_object_creation(cls: Type, iterations: int = 10000, **kwargs) -> Dict[str, float]:
    """Benchmark object creation speed"""
    start = time.perf_counter()

    for _ in range(iterations):
        obj = cls(**kwargs)
        if hasattr(obj, '__post_init__'):
            pass  # Already called in __init__

    end = time.perf_counter()

    return {
        'total_time_s': end - start,
        'time_per_op_us': (end - start) / iterations * 1e6,
        'ops_per_second': iterations / (end - start),
    }


def benchmark_request_pool(pool: HBMRequestPool, iterations: int = 10000) -> Dict[str, float]:
    """Benchmark request pool operations"""
    start = time.perf_counter()

    for i in range(iterations):
        req = pool.acquire(addr=i * 64, length=64, is_read=True)
        pool.release(req)

    end = time.perf_counter()

    return {
        'total_time_s': end - start,
        'time_per_op_us': (end - start) / iterations * 1e6,
        'ops_per_second': iterations / (end - start),
        'pool_size': pool.pool_size,
    }


def benchmark_bank_state_machine(bank_id: int, timing, iterations: int = 100000) -> Dict[str, float]:
    """Benchmark bank state machine operations"""
    bsm = BankStateMachine(bank_id, timing)

    # Pre-warm timing cache
    bsm._refresh_timing_cache()
    bsm.set_time(100)

    # Benchmark can_activate
    start = time.perf_counter()
    for _ in range(iterations):
        bsm.can_activate()
    end = time.perf_counter()
    can_activate_time = (end - start) / iterations * 1e6

    # Benchmark activate
    bsm.bank.state = bsm.bank.state.__class__.IDLE  # Reset state
    start = time.perf_counter()
    for i in range(iterations):
        bsm.bank.update_state(bsm.bank.state.__class__.IDLE)
        bsm.activate(row=i)
    end = time.perf_counter()
    activate_time = (end - start) / iterations * 1e6

    return {
        'can_activate_us': can_activate_time,
        'activate_us': activate_time,
        'ops_per_second': iterations / (end - start),
    }


def benchmark_scheduler_operations(iterations: int = 10000) -> Dict[str, float]:
    """Benchmark scheduler operations"""
    config = HBM3_DEFAULT
    scheduler = FRFCFSScheduler(config)
    bank_states = {}

    # Create test requests
    requests = []
    for i in range(100):
        req = HBMRequest(addr=i * 64, length=64, is_read=(i % 2 == 0))
        req.arrival_time = float(i)
        req.channel_id = i % 8
        req.pseudo_channel_id = 0
        req.bank_id = i % 16
        req.row_id = i
        requests.append(req)

    read_queue = ReadQueue(max_depth=32)
    write_queue = WriteQueue(max_depth=32)

    # Add requests to queues
    for i, req in enumerate(requests[:50]):
        read_queue.push(req)
    for i, req in enumerate(requests[50:]):
        write_queue.push(req)

    start = time.perf_counter()
    for _ in range(iterations):
        scheduler.schedule(read_queue, write_queue, bank_states, float(_), "READ")
    end = time.perf_counter()

    return {
        'total_time_s': end - start,
        'time_per_op_us': (end - start) / iterations * 1e6,
        'ops_per_second': iterations / (end - start),
    }


def benchmark_simulation_throughput(sim_time_us: float = 100.0,
                                    iterations: int = 5) -> Dict[str, float]:
    """Benchmark simulation throughput"""
    config = SimulationConfig(
        simulation_time_us=sim_time_us,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.3,
        read_ratio=0.7,
        seed=42,
    )

    times = []
    completed_counts = []

    for _ in range(iterations):
        gc.collect()
        start = time.perf_counter()
        sim = HBMSimulator(config)
        stats = sim.run()
        end = time.perf_counter()

        times.append(end - start)
        completed_counts.append(stats.completed_requests)

    return {
        'avg_time_s': sum(times) / len(times),
        'min_time_s': min(times),
        'max_time_s': max(times),
        'avg_completed': sum(completed_counts) / len(completed_counts),
        'throughput_ops_per_s': sum(completed_counts) / sum(times),
    }


def check_slots_usage(cls: Type) -> Dict[str, Any]:
    """Check if a class uses __slots__"""
    has_slots = hasattr(cls, '__slots__')
    slot_count = len(cls.__slots__) if has_slots else 0

    # Check if it's a dataclass
    is_dc = is_dataclass(cls)

    return {
        'class_name': cls.__name__,
        'has_slots': has_slots,
        'slot_count': slot_count,
        'is_dataclass': is_dc,
    }


def run_memory_benchmark() -> Dict[str, Any]:
    """Run memory usage benchmarks"""
    print("\n" + "=" * 60)
    print("Memory Usage Benchmarks")
    print("=" * 60)

    results = {}

    # Check slots usage
    print("\n--- __slots__ Usage Check ---")
    classes_to_check = [
        HBMRequest,
        HBMResponse,
        Bank,
        BankStateMachine,
        FRFCFSScheduler,
        BankState,
        SimulationConfig,
    ]

    for cls in classes_to_check:
        info = check_slots_usage(cls)
        print(f"  {info['class_name']}: slots={info['has_slots']}, count={info['slot_count']}")
        results[f"slots_{cls.__name__}"] = info

    # Benchmark object sizes
    print("\n--- Object Size Comparison ---")
    req = HBMRequest(addr=0x1000, length=64, is_read=True)
    req_size = get_object_size(req)
    print(f"  HBMRequest size: {req_size} bytes")

    bank = Bank(bank_id=0)
    bank_size = get_object_size(bank)
    print(f"  Bank size: {bank_size} bytes")

    # Benchmark request pool
    print("\n--- Request Pool Benchmark ---")
    pool = HBMRequestPool(max_size=1024)
    pool_result = benchmark_request_pool(pool, iterations=10000)
    print(f"  Pool operations: {pool_result['ops_per_second']:.0f} ops/s")
    print(f"  Time per op: {pool_result['time_per_op_us']:.3f} us")
    results['request_pool'] = pool_result

    return results


def run_speed_benchmark() -> Dict[str, Any]:
    """Run speed benchmarks"""
    print("\n" + "=" * 60)
    print("Speed Benchmarks")
    print("=" * 60)

    results = {}

    # Bank state machine benchmark
    print("\n--- Bank State Machine Benchmark ---")
    from model.dram.timing import HBM3Timing
    timing = HBM3Timing()
    bsm_result = benchmark_bank_state_machine(bank_id=0, timing=timing, iterations=50000)
    print(f"  can_activate: {bsm_result['can_activate_us']:.4f} us")
    print(f"  activate: {bsm_result['activate_us']:.4f} us")
    results['bank_state_machine'] = bsm_result

    # Scheduler benchmark
    print("\n--- Scheduler Benchmark ---")
    sched_result = benchmark_scheduler_operations(iterations=5000)
    print(f"  Schedule operations: {sched_result['ops_per_second']:.0f} ops/s")
    print(f"  Time per op: {sched_result['time_per_op_us']:.3f} us")
    results['scheduler'] = sched_result

    # Simulation throughput
    print("\n--- Simulation Throughput Benchmark ---")
    sim_result = benchmark_simulation_throughput(sim_time_us=100.0, iterations=3)
    print(f"  Avg time: {sim_result['avg_time_s']:.2f} s")
    print(f"  Completed requests: {sim_result['avg_completed']:.0f}")
    print(f"  Throughput: {sim_result['throughput_ops_per_s']:.0f} req/s")
    results['simulation'] = sim_result

    return results


def run_full_benchmark() -> Dict[str, Any]:
    """Run all benchmarks and generate report"""
    print("=" * 60)
    print("HBM System Optimization Performance Report")
    print("=" * 60)

    gc.collect()

    # Memory benchmarks
    memory_results = run_memory_benchmark()

    # Speed benchmarks
    speed_results = run_speed_benchmark()

    # Generate summary
    print("\n" + "=" * 60)
    print("Optimization Summary")
    print("=" * 60)

    summary = {
        'memory': memory_results,
        'speed': speed_results,
    }

    # Print optimization improvements
    print("\nOptimizations Applied:")
    print("  1. __slots__ for memory reduction in:")
    print("     - HBMRequest (request.py)")
    print("     - HBMResponse (request.py)")
    print("     - Bank (bank_state_machine.py)")
    print("     - BankState (scheduler.py)")
    print("     - SimulationConfig (simulator.py)")
    print("     - HBMSimulator (simulator.py)")
    print("     - FRFCFSScheduler (scheduler.py)")
    print("  2. Frozen dataclass for immutable types:")
    print("     - TimingViolation (bank_state_machine.py)")
    print("  3. Cached timing values in BankStateMachine")
    print("  4. Request object pooling (HBMRequestPool)")
    print("  5. Batch processing support in TrafficGenerator")
    print("  6. Optimized scheduler with fast arbitration")

    return summary


if __name__ == "__main__":
    results = run_full_benchmark()

    # Save results
    import json
    output_file = "/home/ic/JXTF/HBM/benchmark_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {output_file}")
    except Exception as e:
        print(f"\nCould not save results: {e}")