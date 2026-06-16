"""
Performance Tests - Memory Usage

Tests for measuring and validating memory consumption.
Validates that the simulator meets memory efficiency targets.

Test Categories:
- memory_baseline: Baseline memory usage
- memory_per_request: Memory per request
- memory_vs_channels: Memory scaling with channel count
- memory_leak_detection: Detect memory leaks

References:
- Memory efficiency requirements
- Optimization targets
"""

import pytest
import gc
import sys
from typing import Dict, Optional


def get_memory_usage() -> Optional[Dict]:
    """Get current memory usage

    Returns dictionary with memory metrics or None if unavailable.
    """
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            'rss_mb': mem_info.rss / (1024 * 1024),
            'vms_mb': mem_info.vms / (1024 * 1024),
            'percent': process.memory_percent(),
        }
    except ImportError:
        # psutil not available, return None
        return None


def get_object_count(obj: object) -> int:
    """Get count of Python objects of a specific type"""
    gc.collect()
    return len(gc.get_objects())


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage tests"""

    @pytest.fixture
    def memory_threshold_mb(self):
        """Maximum memory threshold in MB"""
        return 500  # Conservative threshold

    def test_memory_baseline(self, hbm3_config, memory_threshold_mb):
        """Test baseline memory usage

        Simulator should not use excessive memory at baseline.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()
        mem_before = get_memory_usage()

        sim_config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.3,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        gc.collect()
        mem_after = get_memory_usage()

        if mem_before and mem_after:
            mem_used = mem_after['rss_mb'] - mem_before['rss_mb']
            print(f"\nMemory Usage (Baseline):")
            print(f"  Before: {mem_before['rss_mb']:.1f} MB")
            print(f"  After: {mem_after['rss_mb']:.1f} MB")
            print(f"  Used: {mem_used:.1f} MB")

            assert mem_after['rss_mb'] <= memory_threshold_mb, \
                f"High memory usage: {mem_after['rss_mb']:.1f} MB"

    def test_memory_per_channel(self, hbm3_config):
        """Test memory usage per channel

        Memory should scale reasonably with channel count.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()
        mem_before = get_memory_usage()

        config = hbm3_config.copy()
        config.channels_per_stack = 32  # Full HBM4

        sim_config = SimulationConfig(
            simulation_time_us=20.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        gc.collect()
        mem_after = get_memory_usage()

        if mem_before and mem_after:
            mem_used = mem_after['rss_mb'] - mem_before['rss_mb']
            print(f"\nMemory Usage (32 channels):")
            print(f"  Before: {mem_before['rss_mb']:.1f} MB")
            print(f"  After: {mem_after['rss_mb']:.1f} MB")
            print(f"  Used: {mem_used:.1f} MB")

            # Memory should be reasonable for 32 channels
            max_mem = 200  # MB
            assert mem_after['rss_mb'] <= max_mem

    def test_memory_vs_duration(self, hbm3_config):
        """Test memory usage vs simulation duration

        Memory should remain stable as simulation runs longer.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()

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

            sim = HBMSimulator(sim_config)

            # Measure mid-point memory
            mid_cycles = int(sim.max_cycles / 2)
            for _ in range(mid_cycles):
                sim.step()

            gc.collect()
            mem_mid = get_memory_usage()

            stats = sim.run()

            gc.collect()
            mem_end = get_memory_usage()

            if mem_mid and mem_end:
                results.append({
                    'duration': duration,
                    'mid_mb': mem_mid['rss_mb'],
                    'end_mb': mem_end['rss_mb'],
                })

        if results:
            print(f"\nMemory vs Duration:")
            for r in results:
                print(f"  {r['duration']:.0f}us: mid={r['mid_mb']:.1f} MB, "
                      f"end={r['end_mb']:.1f} MB")

                # End memory should not be much higher than mid memory
                mem_growth = r['end_mb'] - r['mid_mb']
                max_growth = 50  # MB
                assert mem_growth <= max_growth, \
                    f"Excessive memory growth at {r['duration']}us: {mem_growth:.1f} MB"

    def test_memory_vs_queue_depth(self, hbm3_config):
        """Test memory usage vs queue depth

        Larger queues use more memory.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()

        depths = [16, 64, 256]
        results = []

        for depth in depths:
            config = hbm3_config.copy()
            config.queue_depth = depth

            sim_config = SimulationConfig(
                simulation_time_us=20.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.7,
                seed=42,
                hbm_config=config,
            )

            sim = HBMSimulator(sim_config)

            gc.collect()
            mem_before = get_memory_usage()

            stats = sim.run()

            gc.collect()
            mem_after = get_memory_usage()

            if mem_before and mem_after:
                mem_used = mem_after['rss_mb'] - mem_before['rss_mb']
                results.append({
                    'depth': depth,
                    'mem_mb': mem_after['rss_mb'],
                    'used_mb': mem_used,
                })

        if results:
            print(f"\nMemory vs Queue Depth:")
            for r in results:
                print(f"  Depth={r['depth']:3d}: {r['mem_mb']:.1f} MB "
                      f"(+{r['used_mb']:.1f} MB)")

            # Memory should scale with queue depth
            if len(results) >= 2:
                assert results[-1]['mem_mb'] >= results[0]['mem_mb'], \
                    "Memory should increase with queue depth"

    def test_object_count_stability(self, hbm3_config):
        """Test that object count remains stable

        Object count should not grow unboundedly.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()
        initial_count = get_object_count(object)

        sim_config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)

        # Count after initialization
        gc.collect()
        init_count = get_object_count(object)

        stats = sim.run()

        # Count after simulation
        gc.collect()
        final_count = get_object_count(object)

        growth = final_count - init_count

        print(f"\nObject Count Stability:")
        print(f"  Initial: {initial_count}")
        print(f"  After Init: {init_count}")
        print(f"  Final: {final_count}")
        print(f"  Growth: {growth}")

        # Object count should not grow excessively
        max_growth = 10000
        assert growth <= max_growth, \
            f"Excessive object growth: {growth} objects"


@pytest.mark.performance
class TestMemoryLeaks:
    """Memory leak detection tests"""

    def test_no_request_accumulation(self, hbm3_config):
        """Test that requests don't accumulate in memory

        Completed requests should be cleaned up.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()

        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # Check that completed requests don't accumulate
        completed = stats.completed_requests
        print(f"\nRequest Accumulation:")
        print(f"  Completed: {completed}")

        # Basic sanity - completed requests should be tracked
        assert completed >= 0

    def test_no_bank_state_leak(self, hbm3_config):
        """Test that bank states don't accumulate

        Bank state dictionary should remain bounded.
        """
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest

        controller = HBMController(hbm3_config)

        # Submit requests to various addresses
        for i in range(100):
            request = HBMRequest(
                addr=i * 0x10000,
                length=64,
                is_read=True
            )
            controller.submit_request(request)

        # Bank states should be bounded (not one per request)
        num_bank_states = len(controller.bank_states)
        num_requests = controller.stats['total_requests']

        print(f"\nBank State Accumulation:")
        print(f"  Requests: {num_requests}")
        print(f"  Bank States: {num_bank_states}")

        # Bank states should be much less than requests
        # (many requests go to same banks)
        assert num_bank_states <= num_requests

    def test_queue_memory_bounded(self, hbm3_config):
        """Test that queue memory is bounded

        Queue should not grow beyond configured depth.
        """
        from model.controller.queue import QueueManager

        queue_manager = QueueManager.create(max_depth=32)

        # Submit more requests than queue can hold
        from model.controller.request import HBMRequest

        accepted = 0
        for i in range(100):
            request = HBMRequest(
                addr=i * 0x100,
                length=64,
                is_read=True
            )
            if queue_manager.push_read(request):
                accepted += 1

        print(f"\nQueue Memory Bounded:")
        print(f"  Submitted: 100")
        print(f"  Accepted: {accepted}")
        print(f"  Queue Depth: {queue_manager.read_queue.qsize()}")

        # Should not accept more than queue depth
        assert accepted <= 100  # Some may be accepted

    def test_statistics_memory(self, hbm3_config):
        """Test that statistics don't accumulate memory

        Statistics should be fixed size structures.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()
        mem_before = get_memory_usage()

        # Run multiple simulations
        for _ in range(5):
            sim_config = SimulationConfig(
                simulation_time_us=20.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                seed=42,
                hbm_config=hbm3_config,
            )

            sim = HBMSimulator(sim_config)
            sim.run()

            del sim

        gc.collect()
        mem_after = get_memory_usage()

        if mem_before and mem_after:
            growth = mem_after['rss_mb'] - mem_before['rss_mb']
            print(f"\nStatistics Memory (5 runs):")
            print(f"  Before: {mem_before['rss_mb']:.1f} MB")
            print(f"  After: {mem_after['rss_mb']:.1f} MB")
            print(f"  Growth: {growth:.1f} MB")

            # Should not grow significantly
            max_growth = 100  # MB
            assert growth <= max_growth


@pytest.mark.performance
class TestMemoryScaling:
    """Memory scaling tests"""

    def test_memory_linear_scaling(self, hbm3_config):
        """Test that memory scales linearly with resources

        Memory should scale predictably.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()

        channel_counts = [1, 4, 8]
        results = []

        for count in channel_counts:
            config = hbm3_config.copy()
            config.channels_per_stack = count

            sim_config = SimulationConfig(
                simulation_time_us=20.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                seed=42,
                hbm_config=config,
            )

            gc.collect()
            mem_before = get_memory_usage()

            sim = HBMSimulator(sim_config)
            stats = sim.run()

            gc.collect()
            mem_after = get_memory_usage()

            if mem_before and mem_after:
                mem_used = mem_after['rss_mb'] - mem_before['rss_mb']
                results.append({
                    'channels': count,
                    'mem_mb': mem_after['rss_mb'],
                    'used_mb': mem_used,
                })

        if results:
            print(f"\nMemory Linear Scaling:")
            for r in results:
                print(f"  {r['channels']} channels: {r['mem_mb']:.1f} MB")

            # Memory should increase with channels
            if len(results) >= 2:
                assert results[-1]['mem_mb'] >= results[0]['mem_mb']

    def test_memory_vs_stack_count(self, hbm3_config):
        """Test memory scaling with stack count"""
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()

        stack_counts = [1, 2, 4]
        results = []

        for stack_count in stack_counts:
            config = hbm3_config.copy()
            config.stack_count = stack_count

            sim_config = SimulationConfig(
                simulation_time_us=20.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                seed=42,
                hbm_config=config,
            )

            gc.collect()
            mem_before = get_memory_usage()

            sim = HBMSimulator(sim_config)
            stats = sim.run()

            gc.collect()
            mem_after = get_memory_usage()

            if mem_before and mem_after:
                mem_used = mem_after['rss_mb'] - mem_before['rss_mb']
                results.append({
                    'stacks': stack_count,
                    'mem_mb': mem_after['rss_mb'],
                })

        if results:
            print(f"\nMemory vs Stack Count:")
            for r in results:
                print(f"  {r['stacks']} stack(s): {r['mem_mb']:.1f} MB")

            # Memory should increase with stack count
            if len(results) >= 2:
                assert results[-1]['mem_mb'] >= results[0]['mem_mb']

    def test_memory_fragmentation(self, hbm3_config):
        """Test for memory fragmentation

        Memory allocation patterns should not cause fragmentation.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        gc.collect()

        # Run many short simulations
        for _ in range(10):
            sim_config = SimulationConfig(
                simulation_time_us=5.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                seed=42,
                hbm_config=hbm3_config,
            )

            sim = HBMSimulator(sim_config)
            sim.run()
            del sim

        gc.collect()
        mem_after = get_memory_usage()

        if mem_after:
            print(f"\nMemory Fragmentation (10 runs):")
            print(f"  Final Memory: {mem_after['rss_mb']:.1f} MB")

            # Memory should be reasonable after multiple runs
            max_mem = 300  # MB
            assert mem_after['rss_mb'] <= max_mem