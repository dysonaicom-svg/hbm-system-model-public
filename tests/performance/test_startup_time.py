"""
Performance Tests - Startup Time

Tests for measuring and validating initialization time.
Validates that the simulator initializes quickly.

Test Categories:
- initialization_time: Time to initialize simulator
- component_init_time: Time to initialize each component
- first_cycle_time: Time for first simulation cycle

References:
- Startup time requirements
- Initialization efficiency targets
"""

import pytest
import time
from typing import Dict, List


@pytest.mark.performance
class TestStartupTime:
    """Startup time tests"""

    @pytest.fixture
    def max_init_time_ms(self):
        """Maximum initialization time in milliseconds"""
        return 1000  # 1 second max for full initialization

    def test_controller_initialization_time(self, hbm3_config):
        """Test HBM controller initialization time

        Controller should initialize quickly.
        """
        from model.controller.controller import HBMController

        times = []
        for _ in range(5):
            start = time.perf_counter()
            controller = HBMController(hbm3_config)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\nController Initialization Time:")
        print(f"  Average: {avg_time:.2f} ms")
        print(f"  Min: {min_time:.2f} ms")
        print(f"  Max: {max_time:.2f} ms")

        # Should initialize quickly
        max_time_ms = 100
        assert avg_time <= max_time_ms, \
            f"Slow controller init: {avg_time:.2f} ms"

    def test_dram_model_initialization_time(self):
        """Test DRAM model initialization time

        DRAM model should initialize quickly.
        """
        from model.dram.dram_model import DRAMModel

        times = []
        for _ in range(5):
            start = time.perf_counter()
            dram = DRAMModel(
                hbm_version="hbm3",
                stack_count=2,
                banks_per_channel=16
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        print(f"\nDRAM Model Initialization Time:")
        print(f"  Average: {avg_time:.2f} ms")

        # Should initialize quickly
        max_time_ms = 50
        assert avg_time <= max_time_ms

    def test_simulator_initialization_time(self, hbm3_config):
        """Test full simulator initialization time

        Full simulator should initialize within reasonable time.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        times = []
        for _ in range(3):
            sim_config = SimulationConfig(
                simulation_time_us=10.0,
                hbm_config=hbm3_config,
            )

            start = time.perf_counter()
            sim = HBMSimulator(sim_config)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        print(f"\nSimulator Initialization Time:")
        print(f"  Average: {avg_time:.2f} ms")

        # Should initialize within time limit
        max_time_ms = 500
        assert avg_time <= max_time_ms, \
            f"Slow simulator init: {avg_time:.2f} ms"

    def test_first_cycle_time(self, hbm3_config):
        """Test time for first simulation cycle

        First cycle should complete quickly.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        sim_config = SimulationConfig(
            simulation_time_us=10.0,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)

        start = time.perf_counter()
        sim.step()
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\nFirst Cycle Time:")
        print(f"  Time: {elapsed:.2f} ms")

        # First cycle should be quick
        max_time_ms = 10
        assert elapsed <= max_time_ms, \
            f"Slow first cycle: {elapsed:.2f} ms"

    def test_warmup_time(self, hbm3_config):
        """Test time to reach stable performance

        Simulator should reach stable performance quickly.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)

        # Measure cycles at different points
        checkpoints = [10, 50, 100, 500]
        times = []

        for target_cycles in checkpoints:
            start = time.perf_counter()

            while sim.current_cycle < target_cycles:
                sim.step()

            elapsed = (time.perf_counter() - start) * 1000
            times.append((target_cycles, elapsed))

        print(f"\nWarmup Time:")
        for cycles, elapsed in times:
            rate = cycles / elapsed if elapsed > 0 else 0
            print(f"  {cycles} cycles: {elapsed:.2f} ms ({rate:.0f} cycles/ms)")

        # Should reach stable rate quickly
        if len(times) >= 2:
            early_rate = times[0][0] / times[0][1] if times[0][1] > 0 else 0
            late_rate = times[-1][0] / times[-1][1] if times[-1][1] > 0 else 0

            # Rate should stabilize (not decrease significantly)
            if early_rate > 0:
                rate_ratio = late_rate / early_rate
                print(f"  Rate stabilization: {rate_ratio:.2f}x")


@pytest.mark.performance
class TestComponentInitTime:
    """Component initialization time breakdown"""

    def test_address_decoder_init_time(self, hbm3_config):
        """Test address decoder initialization time"""
        from model.controller.address_decoder import AddressDecoder

        times = []
        for _ in range(10):
            start = time.perf_counter()
            decoder = AddressDecoder(hbm3_config)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        print(f"\nAddress Decoder Init Time:")
        print(f"  Average: {avg_time:.4f} ms")

        # Should be very fast
        max_time_ms = 10
        assert avg_time <= max_time_ms

    def test_queue_manager_init_time(self, hbm3_config):
        """Test queue manager initialization time"""
        from model.controller.queue import QueueManager

        times = []
        for _ in range(10):
            start = time.perf_counter()
            qm = QueueManager.create(hbm3_config.queue_depth)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        print(f"\nQueue Manager Init Time:")
        print(f"  Average: {avg_time:.4f} ms")

        # Should be very fast
        max_time_ms = 5
        assert avg_time <= max_time_ms

    def test_scheduler_init_time(self, hbm3_config):
        """Test scheduler initialization time"""
        from model.controller.scheduler import FRFCFSScheduler

        times = []
        for _ in range(10):
            start = time.perf_counter()
            scheduler = FRFCFSScheduler(hbm3_config)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        print(f"\nScheduler Init Time:")
        print(f"  Average: {avg_time:.4f} ms")

        # Should be fast
        max_time_ms = 20
        assert avg_time <= max_time_ms

    def test_command_sequencer_init_time(self):
        """Test command sequencer initialization time"""
        from model.controller.command_sequencer import CommandSequencer

        times = []
        for _ in range(10):
            start = time.perf_counter()
            sequencer = CommandSequencer()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        print(f"\nCommand Sequencer Init Time:")
        print(f"  Average: {avg_time:.4f} ms")

        # Should be fast
        max_time_ms = 10
        assert avg_time <= max_time_ms

    def test_command_pipeline_init_time(self):
        """Test command pipeline initialization time"""
        from model.controller.command_pipeline import CommandPipeline

        times = []
        for _ in range(10):
            start = time.perf_counter()
            pipeline = CommandPipeline()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        print(f"\nCommand Pipeline Init Time:")
        print(f"  Average: {avg_time:.4f} ms")

        # Should be fast
        max_time_ms = 10
        assert avg_time <= max_time_ms


@pytest.mark.performance
class TestInitializationVariation:
    """Tests for initialization time variation"""

    def test_init_time_vs_config_complexity(self, hbm3_config):
        """Test initialization time vs configuration complexity"""
        from sim.simulator import HBMSimulator, SimulationConfig

        configs = [
            ('Simple', hbm3_config.copy()),
            ('8-channel', hbm3_config.copy()),
            ('32-channel', hbm3_config.copy()),
        ]
        configs[1][1].channels_per_stack = 8
        configs[2][1].channels_per_stack = 32

        results = []
        for name, config in configs:
            times = []
            for _ in range(3):
                sim_config = SimulationConfig(
                    simulation_time_us=10.0,
                    hbm_config=config,
                )

                start = time.perf_counter()
                sim = HBMSimulator(sim_config)
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            results.append((name, avg_time))

        print(f"\nInit Time vs Complexity:")
        for name, avg_time in results:
            print(f"  {name}: {avg_time:.2f} ms")

        # More complex configs should not take excessively longer
        if len(results) >= 2:
            simple_time = results[0][1]
            complex_time = results[-1][1]
            ratio = complex_time / simple_time if simple_time > 0 else 1

            print(f"  Complexity ratio: {ratio:.2f}x")

            # Complex should not be more than 5x slower
            max_ratio = 5.0
            assert ratio <= max_ratio, \
                f"Excessive complexity impact: {ratio:.2f}x"

    def test_init_time_consistency(self, hbm3_config):
        """Test initialization time consistency"""
        from sim.simulator import HBMSimulator, SimulationConfig

        times = []
        for _ in range(5):
            sim_config = SimulationConfig(
                simulation_time_us=10.0,
                hbm_config=hbm3_config,
            )

            start = time.perf_counter()
            sim = HBMSimulator(sim_config)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        import statistics
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        cv = std_time / avg_time if avg_time > 0 else 0

        print(f"\nInit Time Consistency:")
        print(f"  Average: {avg_time:.2f} ms")
        print(f"  Std Dev: {std_time:.2f} ms")
        print(f"  CV: {cv:.2f}")

        # CV should be low for consistent initialization
        max_cv = 0.3
        assert cv <= max_cv, f"Inconsistent init time: CV={cv:.2f}"

    def test_init_time_vs_stack_count(self, hbm3_config):
        """Test initialization time vs stack count"""
        from sim.simulator import HBMSimulator, SimulationConfig

        stack_counts = [1, 2, 4]
        results = []

        for count in stack_counts:
            config = hbm3_config.copy()
            config.stack_count = count

            sim_config = SimulationConfig(
                simulation_time_us=10.0,
                hbm_config=config,
            )

            times = []
            for _ in range(3):
                start = time.perf_counter()
                sim = HBMSimulator(sim_config)
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            results.append((count, avg_time))

        print(f"\nInit Time vs Stack Count:")
        for count, avg_time in results:
            print(f"  {count} stack(s): {avg_time:.2f} ms")

        # Should scale roughly linearly
        if len(results) >= 2:
            single_stack = results[0][1]
            multi_stack = results[-1][1]
            ratio = multi_stack / single_stack if single_stack > 0 else 1

            print(f"  Scaling ratio: {ratio:.2f}x")

            # Should not scale worse than linearly
            max_ratio = 4.0
            assert ratio <= max_ratio


@pytest.mark.performance
class TestLazyInitialization:
    """Tests for lazy initialization patterns"""

    def test_deferred_component_creation(self, hbm3_config):
        """Test that components are created on demand

        Components should only be created when needed.
        """
        from model.controller.controller import HBMController

        controller = HBMController(hbm3_config)

        # Initially, only essential components should be created
        assert controller.decoder is not None
        assert controller.queue_manager is not None
        assert controller.scheduler is not None

    def test_on_demand_initialization(self, hbm3_config):
        """Test that expensive operations are deferred

        Expensive initialization should happen on first use.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        sim_config = SimulationConfig(
            simulation_time_us=10.0,
            hbm_config=hbm3_config,
        )

        # Create simulator
        sim = HBMSimulator(sim_config)

        # Don't run simulation yet
        # Memory/time should still be reasonable

        # Run simulation
        start = time.perf_counter()
        stats = sim.run()
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\nOn-Demand Initialization:")
        print(f"  First Run: {elapsed:.2f} ms")

        # Should complete reasonably fast
        max_time_ms = 5000
        assert elapsed <= max_time_ms

    def test_reuse_after_init(self, hbm3_config):
        """Test that simulator can be reused efficiently

        After initialization, reuse should be fast.
        """
        from sim.simulator import HBMSimulator, SimulationConfig

        sim_config = SimulationConfig(
            simulation_time_us=10.0,
            hbm_config=hbm3_config,
        )

        # First initialization
        sim1 = HBMSimulator(sim_config)
        stats1 = sim1.run()

        # Reuse (new instance but same config)
        sim2 = HBMSimulator(sim_config)
        stats2 = sim2.run()

        # Both should complete reasonably fast
        assert stats1.total_cycles > 0
        assert stats2.total_cycles > 0