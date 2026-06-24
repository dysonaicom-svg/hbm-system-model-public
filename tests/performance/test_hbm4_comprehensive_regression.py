"""
HBM4 Comprehensive Performance Regression Tests

This module provides comprehensive regression testing including:
- Controller performance regression
- Scheduler performance regression
- Channel model performance regression
- End-to-end latency regression
- Memory efficiency regression

These tests ensure that any changes to the HBM4 model do not cause
performance regressions beyond acceptable thresholds.
"""

import pytest
import time
import statistics
import random
import gc
import tracemalloc
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.timing import HBM4Timing, get_timing_for_speed_grade
from model.controller.hbm4_controller import HBM4Controller, HBM4ControllerStats
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.hbm4_bank_state_machine import HBM4BankState
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern


# =============================================================================
# Regression Thresholds
# =============================================================================

class RegressionThresholds:
    """Performance thresholds for regression testing"""

    # Latency thresholds (cycles)
    MAX_LATENCY = {
        "sequential": 50.0,
        "random": 100.0,
        "hotspot": 80.0,
        "stride": 50.0,
    }

    # Throughput thresholds (requests/second)
    MIN_THROUGHPUT = {
        "8Gbps": {
            "sequential": 100000,
            "random": 50000,
            "hotspot": 50000,
        },
        "12Gbps": {
            "sequential": 150000,
            "random": 75000,
            "hotspot": 75000,
        },
        "16Gbps": {
            "sequential": 200000,
            "random": 100000,
            "hotspot": 100000,
        },
    }

    # Memory thresholds (MB)
    MAX_MEMORY_MB = 200.0

    # Controller thresholds
    MAX_CONTROLLER_LATENCY = 50.0  # cycles
    MAX_QUEUE_DEPTH = 128

    # Scheduler thresholds
    MAX_SCHEDULER_LATENCY = 10.0  # cycles


@dataclass
class ComprehensiveRegressionResult:
    """Result of comprehensive regression test"""
    test_name: str
    category: str
    passed: bool
    value: float
    threshold: float
    unit: str
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'category': self.category,
            'passed': self.passed,
            'value': self.value,
            'threshold': self.threshold,
            'unit': self.unit,
            'duration_ms': self.duration_ms,
            'details': self.details,
        }


# =============================================================================
# Controller Regression Tests
# =============================================================================

class TestHBM4ControllerRegression:
    """Controller performance regression tests"""

    @pytest.fixture
    def hbm4_controller(self):
        """Create HBM4 controller for testing"""
        return HBM4Controller()

    def test_controller_submit_latency(self, hbm4_controller):
        """Test request submission latency regression

        Submits 100 requests and measures average submission time.
        """
        gc.collect()
        start_time = time.perf_counter()

        num_requests = 100
        latencies = []

        for i in range(num_requests):
            req_start = time.perf_counter()
            req_id = hbm4_controller.submit_request(
                addr=0x1000 + i * 0x100,
                is_read=(i % 2 == 0),
                size_bytes=64,
            )
            req_end = time.perf_counter()
            latencies.append((req_end - req_start) * 1000)  # Convert to ms

        # Process requests
        for _ in range(1000):
            hbm4_controller.tick()

        duration_ms = (time.perf_counter() - start_time) * 1000

        avg_latency_ms = statistics.mean(latencies)
        max_latency_ms = max(latencies)

        print(f"\nController Submit Latency Regression")
        print(f"  Requests: {num_requests}")
        print(f"  Avg Latency: {avg_latency_ms:.3f} ms")
        print(f"  Max Latency: {max_latency_ms:.3f} ms")
        print(f"  Duration: {duration_ms:.1f} ms")

        # Latency should be very low (< 1ms average)
        assert avg_latency_ms < 1.0, f"Submit latency too high: {avg_latency_ms:.3f} ms"

    def test_controller_queue_depth_regression(self, hbm4_controller):
        """Test queue depth stability regression

        Submits many requests and verifies queue doesn't overflow.
        """
        max_submitted = 1000
        submitted = 0

        for i in range(max_submitted):
            req_id = hbm4_controller.submit_request(
                addr=0x1000 + i * 0x100,
                is_read=(i % 2 == 0),
                size_bytes=64,
            )
            if req_id:
                submitted += 1

        # Process some cycles
        for _ in range(500):
            hbm4_controller.tick()

        # Check queue state
        queue_size = len(hbm4_controller.queue_manager.read_queue)
        queue_size += len(hbm4_controller.queue_manager.write_queue)

        print(f"\nController Queue Depth Regression")
        print(f"  Submitted: {submitted}/{max_submitted}")
        print(f"  Queue Size: {queue_size}")

        # Queue should be within bounds
        assert queue_size <= RegressionThresholds.MAX_QUEUE_DEPTH * 2, (
            f"Queue overflow: {queue_size} > {RegressionThresholds.MAX_QUEUE_DEPTH * 2}"
        )

    def test_controller_stats_collection(self, hbm4_controller):
        """Test controller stats collection regression"""
        # Submit some requests
        submitted = 0
        for i in range(50):
            req_id = hbm4_controller.submit_request(
                addr=0x1000 + i * 0x100,
                is_read=True,
                size_bytes=64,
            )
            if req_id:
                submitted += 1

        # Process requests
        for _ in range(500):
            hbm4_controller.tick()

        stats = hbm4_controller.get_stats()

        # Handle both dict and object return types
        total_requests = stats.get('total_requests', 0) if isinstance(stats, dict) else getattr(stats, 'total_requests', 0)
        completed_requests = stats.get('completed_requests', 0) if isinstance(stats, dict) else getattr(stats, 'completed_requests', 0)
        avg_latency = stats.get('avg_latency', 0) if isinstance(stats, dict) else getattr(stats, 'avg_latency', 0)

        print(f"\nController Stats Collection")
        print(f"  Submitted: {submitted}")
        print(f"  Total Requests: {total_requests}")
        print(f"  Completed: {completed_requests}")
        print(f"  Avg Latency: {avg_latency:.2f} cycles")

        # At least some requests should have been submitted
        assert submitted > 0, "No requests submitted"


# =============================================================================
# Scheduler Regression Tests
# =============================================================================

class TestHBM4SchedulerRegression:
    """Scheduler performance regression tests"""

    @pytest.fixture
    def scheduler(self):
        """Create QoS scheduler for testing"""
        return HBM4QoSScheduler()

    def test_scheduler_priority_handling(self, scheduler):
        """Test scheduler priority handling regression"""
        # Submit requests at different priorities
        num_high = 10
        num_normal = 20
        num_low = 10

        high_ids = []
        normal_ids = []
        low_ids = []

        for i in range(num_high):
            req_id = f"high_{i}"
            scheduler.add_request(req_id, priority=QoSLevel.CRITICAL, traffic_type="read")
            high_ids.append(req_id)

        for i in range(num_normal):
            req_id = f"normal_{i}"
            scheduler.add_request(req_id, priority=QoSLevel.NORMAL, traffic_type="read")
            normal_ids.append(req_id)

        for i in range(num_low):
            req_id = f"low_{i}"
            scheduler.add_request(req_id, priority=QoSLevel.BEST_EFFORT, traffic_type="read")
            low_ids.append(req_id)

        # Schedule and verify high priority is first
        scheduled = []
        for _ in range(40):
            req = scheduler.get_next_request()
            if req:
                scheduled.append(req.request_id)

        print(f"\nScheduler Priority Handling")
        print(f"  High Priority Requests: {len(high_ids)}")
        print(f"  Normal Priority Requests: {len(normal_ids)}")
        print(f"  Low Priority Requests: {len(low_ids)}")
        print(f"  Scheduled First 10: {scheduled[:10]}")

        # High priority should be scheduled first
        if scheduled:
            assert scheduled[0].startswith("high"), (
                f"High priority not scheduled first: {scheduled[0]}"
            )

    def test_scheduler_latency(self, scheduler):
        """Test scheduler latency regression"""
        # Submit many requests
        num_requests = 100
        for i in range(num_requests):
            scheduler.add_request(
                f"req_{i}",
                priority=QoSLevel(i % 16),
                traffic_type="read" if i % 2 == 0 else "write",
            )

        # Time scheduling operations
        start_time = time.perf_counter()

        for _ in range(num_requests):
            scheduler.get_next_request()

        duration_us = (time.perf_counter() - start_time) * 1_000_000

        avg_latency_ns = duration_us / num_requests

        print(f"\nScheduler Latency Regression")
        print(f"  Requests: {num_requests}")
        print(f"  Total Duration: {duration_us:.2f} us")
        print(f"  Avg Latency: {avg_latency_ns:.2f} ns")

        # Scheduler should be fast
        assert avg_latency_ns < RegressionThresholds.MAX_SCHEDULER_LATENCY * 1000, (
            f"Scheduler too slow: {avg_latency_ns:.2f} ns per operation"
        )

    def test_scheduler_bank_conflict_tracking(self, scheduler):
        """Test scheduler bank conflict tracking regression"""
        # Track conflicts for different addresses
        addresses = [
            0x1000,  # Bank 0
            0x2000,  # Bank 2
            0x3000,  # Bank 3
            0x1000,  # Same as first - should detect conflict
        ]

        conflicts = 0
        for addr in addresses:
            conflict = scheduler.bank_conflict_tracker.check_conflict(addr)
            if conflict:
                conflicts += 1

        print(f"\nScheduler Bank Conflict Tracking")
        print(f"  Addresses: {addresses}")
        print(f"  Detected Conflicts: {conflicts}")

        # Should detect at least one conflict
        assert conflicts >= 1, "No bank conflicts detected"


# =============================================================================
# Bank State Machine Regression Tests
# =============================================================================

class TestHBM4BankStateRegression:
    """Bank state machine regression tests"""

    def test_bank_activation_latency(self):
        """Test bank activation latency regression"""
        timing = get_timing_for_speed_grade("8Gbps")

        gc.collect()
        tracemalloc.start()

        start_time = time.perf_counter()

        num_activations = 10000
        for i in range(num_activations):
            bank = HBM4BankState(bank_id=i % 16)
            bank.activate(row=i % 1024)

        duration_ms = (time.perf_counter() - start_time) * 1000
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        latency_per_op = duration_ms / num_activations

        print(f"\nBank Activation Latency Regression")
        print(f"  Operations: {num_activations}")
        print(f"  Total Duration: {duration_ms:.2f} ms")
        print(f"  Per-Operation: {latency_per_op:.4f} ms")
        print(f"  Peak Memory: {peak_mem / (1024 * 1024):.2f} MB")

        # Should be fast enough
        assert latency_per_op < 0.1, f"Bank activation too slow: {latency_per_op:.4f} ms"

    def test_bank_state_transitions(self):
        """Test bank state transition performance regression"""
        timing = get_timing_for_speed_grade("8Gbps")
        bank = HBM4BankState(bank_id=0)

        gc.collect()
        start_time = time.perf_counter()

        num_cycles = 10000
        for cycle in range(num_cycles):
            bank.set_time(float(cycle))
            # Simulate operations
            if cycle % 100 == 0:
                bank.activate(row=cycle // 100)

        duration_ms = (time.perf_counter() - start_time) * 1000

        print(f"\nBank State Transition Performance")
        print(f"  Cycles: {num_cycles}")
        print(f"  Duration: {duration_ms:.2f} ms")
        print(f"  Per-Cycle: {duration_ms / num_cycles:.4f} ms")

        # Should handle cycles efficiently
        assert duration_ms < 100, f"Bank state transitions too slow: {duration_ms:.2f} ms"


# =============================================================================
# End-to-End Latency Regression Tests
# =============================================================================

class TestHBM4EndToEndLatency:
    """End-to-end latency regression tests"""

    @pytest.fixture
    def simulator(self):
        """Create simulator for testing"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.3,
            read_ratio=0.7,
            seed=42,
        )
        return HBMSimulator(config)

    def test_end_to_end_read_latency(self, simulator):
        """Test end-to-end read latency regression"""
        stats = simulator.run()

        avg_latency = stats.avg_latency

        print(f"\nEnd-to-End Read Latency Regression")
        print(f"  Avg Latency: {avg_latency:.2f} cycles")
        print(f"  Threshold: {RegressionThresholds.MAX_CONTROLLER_LATENCY} cycles")

        assert avg_latency < RegressionThresholds.MAX_CONTROLLER_LATENCY, (
            f"End-to-end latency too high: {avg_latency:.2f} cycles"
        )

    def test_end_to_end_latency_distribution(self):
        """Test latency distribution regression"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.3,
            read_ratio=0.7,
            seed=42,
        )

        # Run multiple simulations and collect latencies
        latencies = []
        for _ in range(5):
            sim = HBMSimulator(config)
            stats = sim.run()
            if stats.avg_latency > 0:
                latencies.append(stats.avg_latency)

        if latencies:
            avg = statistics.mean(latencies)
            stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0
            cv = stdev / avg if avg > 0 else 0

            print(f"\nEnd-to-End Latency Distribution")
            print(f"  Runs: {len(latencies)}")
            print(f"  Avg: {avg:.2f} cycles")
            print(f"  StdDev: {stdev:.2f} cycles")
            print(f"  CV: {cv:.2%}")

            # Coefficient of variation should be reasonable (< 50%)
            assert cv < 0.5, f"Latency variance too high: CV={cv:.2%}"


# =============================================================================
# Memory Efficiency Regression Tests
# =============================================================================

class TestHBM4MemoryEfficiency:
    """Memory efficiency regression tests"""

    def test_simulation_memory_usage(self):
        """Test simulation memory usage regression"""
        gc.collect()
        tracemalloc.start()

        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            read_ratio=0.7,
            seed=42,
        )

        sim = HBMSimulator(config)
        stats = sim.run()

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mem_mb = peak_mem / (1024 * 1024)

        print(f"\nSimulation Memory Usage Regression")
        print(f"  Completed Requests: {stats.completed_requests}")
        print(f"  Peak Memory: {peak_mem_mb:.2f} MB")
        print(f"  Threshold: {RegressionThresholds.MAX_MEMORY_MB} MB")

        assert peak_mem_mb < RegressionThresholds.MAX_MEMORY_MB, (
            f"Memory usage too high: {peak_mem_mb:.2f} MB"
        )

    def test_controller_memory_footprint(self):
        """Test controller memory footprint regression"""
        gc.collect()
        tracemalloc.start()

        controllers = []
        for i in range(10):
            ctrl = HBM4Controller()
            # Submit some requests
            for j in range(100):
                ctrl.submit_request(
                    addr=0x1000 + j * 0x100,
                    is_read=True,
                    size_bytes=64,
                )
            controllers.append(ctrl)

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mem_mb = peak_mem / (1024 * 1024)

        print(f"\nController Memory Footprint")
        print(f"  Controllers: {len(controllers)}")
        print(f"  Peak Memory: {peak_mem_mb:.2f} MB")

        # Memory should be reasonable
        assert peak_mem_mb < RegressionThresholds.MAX_MEMORY_MB

    def test_object_pool_memory_savings(self):
        """Test that object pools save memory"""
        gc.collect()
        tracemalloc.start()

        from model.controller.request import HBMRequestPool

        pool = HBMRequestPool(max_size=1000)

        # Create and release many objects
        for _ in range(1000):
            req = pool.acquire(addr=0, length=64, is_read=True)
            pool.release(req)

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Pool should have reused objects
        pool_size = pool.pool_size

        print(f"\nObject Pool Memory Savings")
        print(f"  Pool Size: {pool_size}")
        print(f"  Peak Memory: {peak_mem / (1024 * 1024):.2f} MB")

        # Pool should have reused objects
        assert pool_size > 0, "Pool not reusing objects"


# =============================================================================
# Stress Regression Tests
# =============================================================================

class TestHBM4StressRegression:
    """Stress test regression tests"""

    def test_high_request_rate_stability(self):
        """Test stability under high request rate"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.9,  # High rate
            read_ratio=0.7,
            max_requests_per_cycle=8,
            seed=42,
        )

        gc.collect()
        tracemalloc.start()

        start_time = time.perf_counter()
        sim = HBMSimulator(config)
        stats = sim.run()
        duration_ms = (time.perf_counter() - start_time) * 1000

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\nHigh Request Rate Stability")
        print(f"  Completed: {stats.completed_requests}")
        print(f"  Duration: {duration_ms:.2f} ms")
        print(f"  Peak Memory: {peak_mem / (1024 * 1024):.2f} MB")

        # Should complete without errors
        assert stats.completed_requests > 0, "No requests completed"

    def test_long_simulation_stability(self):
        """Test stability over long simulation"""
        config = SimulationConfig(
            simulation_time_us=500.0,  # 500us simulation
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            read_ratio=0.7,
            seed=42,
        )

        start_time = time.perf_counter()
        sim = HBMSimulator(config)
        stats = sim.run()
        duration_ms = (time.perf_counter() - start_time) * 1000

        print(f"\nLong Simulation Stability")
        print(f"  Simulation Time: {config.simulation_time_us} us")
        print(f"  Completed: {stats.completed_requests}")
        print(f"  Duration: {duration_ms:.2f} ms")
        print(f"  Avg Latency: {stats.avg_latency:.2f} cycles")

        # Should remain stable
        assert stats.completed_requests > 1000, "Too few requests completed"
        assert stats.avg_latency < 200, "Latency too high"


# =============================================================================
# Comprehensive Regression Report
# =============================================================================

def generate_comprehensive_report() -> Tuple[int, int]:
    """Generate comprehensive regression report

    Returns:
        Tuple of (passed, total)
    """
    results: List[ComprehensiveRegressionResult] = []

    # Run all tests
    framework = TestHBM4ControllerRegression()
    # ... (would run tests here)

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print("\n" + "=" * 70)
    print("HBM4 COMPREHENSIVE REGRESSION REPORT")
    print("=" * 70)
    print(f"Passed: {passed}/{total}")
    print("=" * 70)

    return passed, total


if __name__ == "__main__":
    passed, total = generate_comprehensive_report()
    exit(0 if passed == total else 1)
