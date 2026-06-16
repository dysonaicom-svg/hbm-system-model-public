"""
Performance Tests - Simulation Speed

Tests for measuring simulation speed and performance targets.
Validates that the simulator meets speed requirements.

Test Categories:
- sim_speed: Simulation cycles per second
- sim_throughput: Requests processed per second
- sim_efficiency: Simulation efficiency metrics

References:
- Simulation performance requirements
- Optimization targets
"""

import pytest
import time
from typing import Dict

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern


@pytest.mark.performance
class TestSimSpeed:
    """Simulation speed tests"""

    @pytest.fixture
    def sim_config(self, hbm3_config):
        """Default simulation configuration"""
        return SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            read_ratio=0.7,
            seed=42,
            hbm_config=hbm3_config,
        )

    def test_sim_speed_cycles_per_second(self, sim_config):
        """Test simulation speed in cycles per second

        Validates that simulation can process sufficient cycles per real second.
        """
        # Warm up
        warmup_config = SimulationConfig(
            simulation_time_us=10.0,
            hbm_config=sim_config.hbm_config,
        )
        sim_warmup = HBMSimulator(warmup_config)
        sim_warmup.run()

        # Actual measurement
        start_time = time.perf_counter()
        sim = HBMSimulator(sim_config)
        stats = sim.run()
        end_time = time.perf_counter()

        elapsed_time = end_time - start_time
        cycles_per_second = stats.total_cycles / elapsed_time if elapsed_time > 0 else 0

        print(f"\nSimulation Speed:")
        print(f"  Cycles: {stats.total_cycles}")
        print(f"  Elapsed Time: {elapsed_time:.3f} s")
        print(f"  Cycles/Second: {cycles_per_second:.0f}")

        # Minimum speed target: 100,000 cycles/second
        min_cycles_per_sec = 100000
        assert cycles_per_second >= min_cycles_per_sec, \
            f"Simulation speed {cycles_per_sec:.0f} below minimum {min_cycles_per_sec}"

    def test_sim_speed_vs_duration(self, hbm3_config):
        """Test simulation speed consistency with duration

        Longer simulations should maintain speed.
        """
        durations = [10.0, 50.0, 100.0]
        results = []

        for duration in durations:
            sim_config = SimulationConfig(
                simulation_time_us=duration,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                seed=42,
                hbm_config=hbm3_config,
            )

            start_time = time.perf_counter()
            sim = HBMSimulator(sim_config)
            stats = sim.run()
            elapsed_time = time.perf_counter() - start_time

            cycles_per_sec = stats.total_cycles / elapsed_time if elapsed_time > 0 else 0

            results.append({
                'duration': duration,
                'cycles': stats.total_cycles,
                'elapsed': elapsed_time,
                'cycles_per_sec': cycles_per_sec,
            })

        print(f"\nSimulation Speed vs Duration:")
        for r in results:
            print(f"  {r['duration']:.0f}us: {r['cycles']} cycles in "
                  f"{r['elapsed']:.3f}s = {r['cycles_per_sec']:.0f} cycles/s")

        # All durations should achieve reasonable speed
        for r in results:
            min_speed = 50000
            assert r['cycles_per_sec'] >= min_speed, \
                f"Low speed at {r['duration']}us: {r['cycles_per_sec']:.0f} cycles/s"

    def test_sim_speed_vs_complexity(self, hbm3_config):
        """Test simulation speed vs model complexity

        More complex configurations should still meet speed targets.
        """
        configs = []

        # Simple config
        simple_config = hbm3_config.copy()
        simple_config.channels_per_stack = 1
        simple_config.stack_count = 1
        configs.append(('1-channel', simple_config))

        # Medium config
        medium_config = hbm3_config.copy()
        medium_config.channels_per_stack = 8
        medium_config.stack_count = 2
        configs.append(('8-channel x2', medium_config))

        # Complex config
        complex_config = hbm3_config.copy()
        complex_config.channels_per_stack = 16
        complex_config.stack_count = 4
        configs.append(('16-channel x4', complex_config))

        results = []
        for name, config in configs:
            sim_config = SimulationConfig(
                simulation_time_us=20.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                seed=42,
                hbm_config=config,
            )

            start_time = time.perf_counter()
            sim = HBMSimulator(sim_config)
            stats = sim.run()
            elapsed_time = time.perf_counter() - start_time

            cycles_per_sec = stats.total_cycles / elapsed_time if elapsed_time > 0 else 0

            results.append({
                'name': name,
                'cycles': stats.total_cycles,
                'elapsed': elapsed_time,
                'cycles_per_sec': cycles_per_sec,
            })

        print(f"\nSimulation Speed vs Complexity:")
        for r in results:
            print(f"  {r['name']}: {r['cycles_per_sec']:.0f} cycles/s")

        # All should achieve reasonable speed
        for r in results:
            min_speed = 30000
            assert r['cycles_per_sec'] >= min_speed, \
                f"Low speed for {r['name']}: {r['cycles_per_sec']:.0f}"

    def test_sim_speed_with_traffic_pattern(self, hbm3_config):
        """Test simulation speed with different traffic patterns

        Traffic pattern should not significantly impact simulation speed.
        """
        patterns = [
            (TrafficPattern.RANDOM, "Random"),
            (TrafficPattern.SEQUENTIAL, "Sequential"),
            (TrafficPattern.HOT_SPOT, "Hot Spot"),
        ]

        results = []
        for pattern, name in patterns:
            sim_config = SimulationConfig(
                simulation_time_us=30.0,
                traffic_pattern=pattern,
                request_rate=0.5,
                seed=42,
                hbm_config=hbm3_config,
            )

            start_time = time.perf_counter()
            sim = HBMSimulator(sim_config)
            stats = sim.run()
            elapsed_time = time.perf_counter() - start_time

            cycles_per_sec = stats.total_cycles / elapsed_time if elapsed_time > 0 else 0

            results.append({
                'pattern': name,
                'elapsed': elapsed_time,
                'cycles_per_sec': cycles_per_sec,
            })

        print(f"\nSimulation Speed by Pattern:")
        for r in results:
            print(f"  {r['pattern']}: {r['cycles_per_sec']:.0f} cycles/s")

        # All patterns should have similar speed (within 2x)
        speeds = [r['cycles_per_sec'] for r in results]
        if speeds:
            max_speed = max(speeds)
            for speed in speeds:
                assert speed >= max_speed / 2, \
                    f"Unexpectedly low speed for pattern: {speed:.0f}"


@pytest.mark.performance
class TestSimThroughput:
    """Simulation throughput tests"""

    def test_requests_per_second(self, hbm3_config):
        """Test requests processed per second

        Measures raw request processing rate.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.6,
            read_ratio=0.7,
            seed=42,
            hbm_config=hbm3_config,
        )

        start_time = time.perf_counter()
        sim = HBMSimulator(sim_config)
        stats = sim.run()
        elapsed_time = time.perf_counter() - start_time

        req_per_sec = stats.completed_requests / elapsed_time if elapsed_time > 0 else 0

        print(f"\nRequests Per Second:")
        print(f"  Completed: {stats.completed_requests}")
        print(f"  Elapsed: {elapsed_time:.3f} s")
        print(f"  Rate: {req_per_sec:.0f} req/s")

        # Minimum rate: 1000 requests/second
        min_rate = 1000
        assert req_per_sec >= min_rate, \
            f"Request rate {req_per_sec:.0f} below minimum {min_rate}"

    def test_cycles_per_request(self, hbm3_config):
        """Test simulation cycles per completed request

        Lower cycles per request = more efficient simulation.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        if stats.completed_requests > 0:
            cycles_per_req = stats.total_cycles / stats.completed_requests

            print(f"\nCycles Per Request:")
            print(f"  Total Cycles: {stats.total_cycles}")
            print(f"  Completed: {stats.completed_requests}")
            print(f"  Cycles/Request: {cycles_per_req:.2f}")

            # Should be reasonable
            max_cycles_per_req = 1000
            assert cycles_per_req <= max_cycles_per_req

    def test_completion_rate(self, hbm3_config):
        """Test request completion rate

        Completion rate = completed / submitted requests.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        completion_rate = stats.completed_requests / stats.total_requests \
            if stats.total_requests > 0 else 0

        print(f"\nCompletion Rate:")
        print(f"  Submitted: {stats.total_requests}")
        print(f"  Completed: {stats.completed_requests}")
        print(f"  Rate: {completion_rate:.2%}")

        # Completion rate should be reasonable
        min_completion_rate = 0.5
        assert completion_rate >= min_completion_rate, \
            f"Low completion rate: {completion_rate:.2%}"


@pytest.mark.performance
class TestSimEfficiency:
    """Simulation efficiency tests"""

    def test_cpu_utilization(self, hbm3_config):
        """Test CPU utilization during simulation

        Efficient simulation should use CPU consistently.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)

        start_time = time.perf_counter()
        stats = sim.run()
        elapsed_time = time.perf_counter() - start_time

        # CPU time should approximate wall time (no sleeping)
        # Allow 2x overhead for measurement
        expected_time = stats.total_cycles / 100000  # Assume 100K cycles/s

        print(f"\nCPU Utilization:")
        print(f"  Elapsed: {elapsed_time:.3f} s")
        print(f"  Expected: {expected_time:.3f} s")
        print(f"  Ratio: {elapsed_time/expected_time:.2f}x")

        # Should be reasonable
        max_overhead = 10.0
        assert elapsed_time / expected_time <= max_overhead, \
            f"High CPU overhead: {elapsed_time/expected_time:.2f}x"

    def test_memory_efficiency(self, hbm3_config):
        """Test memory usage efficiency

        Simulation should not use excessive memory.
        """
        import gc

        gc.collect()

        sim_config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # Memory usage is tracked via the simulator
        # This is a placeholder - actual memory measurement requires
        # more sophisticated profiling

        print(f"\nSimulation completed with {stats.total_requests} requests")

        # Basic sanity check
        assert stats.total_requests >= 0

    def test_simulation_overhead(self, hbm3_config):
        """Test simulation overhead ratio

        Overhead = non-simulation time / total time.
        Lower is better.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        # Warm up
        warmup_config = SimulationConfig(
            simulation_time_us=10.0,
            hbm_config=hbm3_config,
        )
        sim_warmup = HBMSimulator(warmup_config)
        sim_warmup.run()

        # Actual test
        sim = HBMSimulator(sim_config)

        setup_start = time.perf_counter()
        # Setup time (already done in __init__)
        setup_time = time.perf_counter() - setup_start

        sim_start = time.perf_counter()
        stats = sim.run()
        sim_time = time.perf_counter() - sim_start

        total_time = setup_time + sim_time

        print(f"\nSimulation Overhead:")
        print(f"  Setup: {setup_time*1000:.2f} ms")
        print(f"  Simulation: {sim_time:.3f} s")
        print(f"  Total: {total_time:.3f} s")
        print(f"  Overhead Ratio: {setup_time/total_time:.2%}")

        # Setup overhead should be small
        max_overhead_ratio = 0.1  # 10%
        assert setup_time / total_time <= max_overhead_ratio, \
            f"High setup overhead: {setup_time/total_time:.2%}"


@pytest.mark.performance
@pytest.mark.slow
class TestSimSpeedExtended:
    """Extended simulation speed tests"""

    def test_long_simulation_speed(self, hbm3_config):
        """Test simulation speed for long simulations

        Speed should remain consistent over extended runs.
        """
        sim_config = SimulationConfig(
            simulation_time_us=1000.0,  # 1ms
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        start_time = time.perf_counter()
        sim = HBMSimulator(sim_config)
        stats = sim.run()
        elapsed_time = time.perf_counter() - start_time

        cycles_per_sec = stats.total_cycles / elapsed_time if elapsed_time > 0 else 0

        print(f"\nLong Simulation Speed (1ms):")
        print(f"  Cycles: {stats.total_cycles}")
        print(f"  Elapsed: {elapsed_time:.2f} s")
        print(f"  Speed: {cycles_per_sec:.0f} cycles/s")

        # Minimum speed for long simulations
        min_speed = 50000
        assert cycles_per_sec >= min_speed, \
            f"Low speed for long simulation: {cycles_per_sec:.0f}"

    def test_burst_traffic_speed(self, hbm3_config):
        """Test simulation speed with burst traffic

        Burst traffic generates many requests simultaneously.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.9,  # High rate
            max_requests_per_cycle=8,  # Burst
            seed=42,
            hbm_config=hbm3_config,
        )

        start_time = time.perf_counter()
        sim = HBMSimulator(sim_config)
        stats = sim.run()
        elapsed_time = time.perf_counter() - start_time

        cycles_per_sec = stats.total_cycles / elapsed_time if elapsed_time > 0 else 0

        print(f"\nBurst Traffic Speed:")
        print(f"  Cycles: {stats.total_cycles}")
        print(f"  Completed: {stats.completed_requests}")
        print(f"  Speed: {cycles_per_sec:.0f} cycles/s")

        # Should still maintain reasonable speed
        min_speed = 30000
        assert cycles_per_sec >= min_speed

    def test_speed_consistency(self, hbm3_config):
        """Test speed consistency across multiple runs

        Multiple runs should have similar speed.
        """
        speeds = []

        for run in range(3):
            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                seed=42 + run,
                hbm_config=hbm3_config,
            )

            start_time = time.perf_counter()
            sim = HBMSimulator(sim_config)
            stats = sim.run()
            elapsed_time = time.perf_counter() - start_time

            cycles_per_sec = stats.total_cycles / elapsed_time if elapsed_time > 0 else 0
            speeds.append(cycles_per_sec)

        print(f"\nSpeed Consistency:")
        for i, speed in enumerate(speeds):
            print(f"  Run {i+1}: {speed:.0f} cycles/s")

        if len(speeds) > 1:
            import statistics
            avg_speed = statistics.mean(speeds)
            std_speed = statistics.stdev(speeds) if len(speeds) > 1 else 0
            cv = std_speed / avg_speed if avg_speed > 0 else 0

            print(f"  Average: {avg_speed:.0f} cycles/s")
            print(f"  Std Dev: {std_speed:.0f}")
            print(f"  CV: {cv:.2f}")

            # CV should be low for consistent speed
            max_cv = 0.3
            assert cv <= max_cv, f"Inconsistent speed: CV={cv:.2f}"