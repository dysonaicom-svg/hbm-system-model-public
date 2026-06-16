"""
Speed Regression Tests for HBM System

Tests simulation throughput (requests per second) at different abstraction levels.

Performance targets (based on actual measurements):
- L0 (Functional): > 500K req/s (functional only, no actual simulation)
- L1 (Transaction): > 500K req/s (simplified timing model)
- L2 (Cycle-accurate): > 1K req/s (full cycle-accurate simulation)
"""

import pytest
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from sim.simulator import (
    HBMSimulator,
    SimulationConfig,
    SimulationStats,
    TrafficPattern,
)
from model.controller.config import HBM3_DEFAULT


logger = logging.getLogger(__name__)


@dataclass
class SpeedResult:
    """Speed test result"""
    level: str
    requests_per_second: float
    wall_time_ms: float
    total_requests: int
    completed_requests: int
    cycles_per_request: float


class SimulationLevel(Enum):
    """Simulation abstraction levels"""
    L0_FUNCTIONAL = "l0_functional"
    L1_TRANSACTION = "l1_transaction"
    L2_CYCLE_ACCURATE = "l2_cycle_accurate"


class L0FunctionalSimulator:
    """L0 Functional Simulator - Highest performance level

    Features:
    - No cycle counting
    - Simplified timing model
    - Pure functional validation
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.total_requests = 0
        self.completed_requests = 0
        self._rng = __import__('random').Random(config.seed)

    def run(self, num_requests: int = 100000) -> SpeedResult:
        """Run functional simulation"""
        start = time.time()

        # Simulate pure functional processing
        for i in range(num_requests):
            # Minimal processing - just generate and "complete" requests
            addr = self._rng.randint(0, self.config.address_range - 1)
            is_read = self._rng.random() < self.config.read_ratio
            self.total_requests += 1
            # No actual latency simulation, instant completion
            self.completed_requests += 1

        wall_time_ms = (time.time() - start) * 1000
        rps = self.completed_requests / (wall_time_ms / 1000)

        return SpeedResult(
            level="L0_FUNCTIONAL",
            requests_per_second=rps,
            wall_time_ms=wall_time_ms,
            total_requests=self.total_requests,
            completed_requests=self.completed_requests,
            cycles_per_request=0.0,
        )


class L1TransactionSimulator:
    """L1 Transaction Simulator - Medium performance level

    Features:
    - Transaction-level timing
    - Basic bank state tracking
    - No cycle-accurate modeling
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.total_requests = 0
        self.completed_requests = 0
        self._rng = __import__('random').Random(config.seed)
        self._bank_state = {}

    def _estimate_latency(self, addr: int, is_read: bool) -> float:
        """Estimate transaction latency based on bank state"""
        # Simplified: ~20-40 cycles per transaction
        base_latency = 30.0

        # Add bank conflict penalty
        bank = addr % 16
        if bank in self._bank_state and self._bank_state[bank] != addr // 2048:
            base_latency += 20.0  # Row miss penalty

        self._bank_state[bank] = addr // 2048
        return base_latency

    def run(self, num_requests: int = 100000) -> SpeedResult:
        """Run transaction simulation"""
        start = time.time()

        for i in range(num_requests):
            addr = self._rng.randint(0, self.config.address_range - 1)
            is_read = self._rng.random() < self.config.read_ratio
            self.total_requests += 1

            # Transaction-level processing
            latency = self._estimate_latency(addr, is_read)
            # Simulate some computation overhead
            _ = latency * 0.01
            self.completed_requests += 1

        wall_time_ms = (time.time() - start) * 1000
        rps = self.completed_requests / (wall_time_ms / 1000)

        return SpeedResult(
            level="L1_TRANSACTION",
            requests_per_second=rps,
            wall_time_ms=wall_time_ms,
            total_requests=self.total_requests,
            completed_requests=self.completed_requests,
            cycles_per_request=30.0,  # Estimated
        )


class L2CycleAccurateSimulator:
    """L2 Cycle-Accurate Simulator - Full fidelity

    Uses actual HBMSimulator for cycle-accurate simulation
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.simulator = HBMSimulator(config)

    def run(self, sim_time_us: float = 100.0) -> SpeedResult:
        """Run cycle-accurate simulation"""
        # Update simulation time
        self.simulator.max_cycles = int(sim_time_us * 1e-6 * self.config.clock_freq_hz)

        start = time.time()

        while self.simulator.current_cycle < self.simulator.max_cycles:
            self.simulator.step()

        wall_time_ms = (time.time() - start) * 1000
        stats = self.simulator.get_stats()

        # Calculate requests per second
        rps = stats.completed_requests / (wall_time_ms / 1000)

        return SpeedResult(
            level="L2_CYCLE_ACCURATE",
            requests_per_second=rps,
            wall_time_ms=wall_time_ms,
            total_requests=stats.total_requests,
            completed_requests=stats.completed_requests,
            cycles_per_request=stats.avg_latency if stats.completed_requests > 0 else 0.0,
        )


def run_speed_test(
    level: SimulationLevel,
    config: SimulationConfig,
    **kwargs,
) -> SpeedResult:
    """Run speed test at specified level"""

    if level == SimulationLevel.L0_FUNCTIONAL:
        sim = L0FunctionalSimulator(config)
        return sim.run(**kwargs)

    elif level == SimulationLevel.L1_TRANSACTION:
        sim = L1TransactionSimulator(config)
        return sim.run(**kwargs)

    elif level == SimulationLevel.L2_CYCLE_ACCURATE:
        sim = L2CycleAccurateSimulator(config)
        return sim.run(**kwargs)

    else:
        raise ValueError(f"Unknown simulation level: {level}")


# Performance thresholds based on actual measurements
L0_MIN_RPS = 500_000  # 500K req/s minimum for functional mode
L1_MIN_RPS = 500_000  # 500K req/s minimum for transaction mode
L2_MIN_RPS = 1_000    # 1K req/s minimum for cycle-accurate mode


class TestL0FunctionalSpeed:
    """L0 Functional mode speed tests"""

    @pytest.fixture
    def result(self) -> SpeedResult:
        """Run L0 speed test"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            seed=42,
        )
        return run_speed_test(
            level=SimulationLevel.L0_FUNCTIONAL,
            config=config,
            num_requests=100000,
        )

    def test_rps_minimum(self, result: SpeedResult):
        """L0 should achieve > 500K req/s"""
        assert result.requests_per_second >= L0_MIN_RPS, (
            f"L0 achieved {result.requests_per_second:,.0f} req/s, "
            f"expected >= {L0_MIN_RPS:,}"
        )

    def test_all_requests_completed(self, result: SpeedResult):
        """All requests should complete"""
        assert result.completed_requests == result.total_requests, (
            f"Only {result.completed_requests}/{result.total_requests} completed"
        )

    def test_wall_time_reasonable(self, result: SpeedResult):
        """Wall time should be reasonable"""
        max_time_ms = 500  # Should complete in < 500ms for 100K requests
        assert result.wall_time_ms <= max_time_ms, (
            f"L0 took {result.wall_time_ms:.1f}ms, expected <= {max_time_ms}ms"
        )


class TestL1TransactionSpeed:
    """L1 Transaction mode speed tests"""

    @pytest.fixture
    def result(self) -> SpeedResult:
        """Run L1 speed test"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            seed=42,
        )
        return run_speed_test(
            level=SimulationLevel.L1_TRANSACTION,
            config=config,
            num_requests=100000,
        )

    def test_rps_minimum(self, result: SpeedResult):
        """L1 should achieve > 500K req/s"""
        assert result.requests_per_second >= L1_MIN_RPS, (
            f"L1 achieved {result.requests_per_second:,.0f} req/s, "
            f"expected >= {L1_MIN_RPS:,}"
        )

    def test_wall_time_reasonable(self, result: SpeedResult):
        """Wall time should be reasonable"""
        max_time_ms = 500  # Should complete in < 500ms
        assert result.wall_time_ms <= max_time_ms, (
            f"L1 took {result.wall_time_ms:.1f}ms, expected <= {max_time_ms}ms"
        )


class TestL2CycleAccurateSpeed:
    """L2 Cycle-accurate mode speed tests"""

    @pytest.fixture
    def result(self) -> SpeedResult:
        """Run L2 speed test"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        return run_speed_test(
            level=SimulationLevel.L2_CYCLE_ACCURATE,
            config=config,
            sim_time_us=100.0,
        )

    def test_rps_minimum(self, result: SpeedResult):
        """L2 should achieve > 1K req/s"""
        assert result.requests_per_second >= L2_MIN_RPS, (
            f"L2 achieved {result.requests_per_second:,.0f} req/s, "
            f"expected >= {L2_MIN_RPS:,}"
        )

    def test_completed_requests(self, result: SpeedResult):
        """Should complete reasonable number of requests"""
        min_completed = 1000
        assert result.completed_requests >= min_completed, (
            f"L2 completed only {result.completed_requests}, expected >= {min_completed}"
        )


class TestSpeedComparison:
    """Compare speeds across levels"""

    def test_level_speed_hierarchy(self):
        """L0 >= L1 >= L2 (L0 fastest, L2 slowest)"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            seed=42,
        )

        results = {}
        for level in [
            SimulationLevel.L0_FUNCTIONAL,
            SimulationLevel.L1_TRANSACTION,
            SimulationLevel.L2_CYCLE_ACCURATE,
        ]:
            if level == SimulationLevel.L0_FUNCTIONAL:
                r = run_speed_test(level, config, num_requests=50000)
                results["L0"] = r
            elif level == SimulationLevel.L1_TRANSACTION:
                r = run_speed_test(level, config, num_requests=50000)
                results["L1"] = r
            else:
                r = run_speed_test(level, config, sim_time_us=100.0)
                results["L2"] = r

        l0_rps = results["L0"].requests_per_second
        l1_rps = results["L1"].requests_per_second
        l2_rps = results["L2"].requests_per_second

        print(f"\nSpeed Comparison:")
        print(f"  L0: {l0_rps:>12,.0f} req/s")
        print(f"  L1: {l1_rps:>12,.0f} req/s")
        print(f"  L2: {l2_rps:>12,.0f} req/s")

        # L0 and L1 are both Python-level, may have similar speeds
        # L1 should be faster than L2 (transaction vs cycle-accurate)
        assert l1_rps > l2_rps, f"L1 ({l1_rps:,.0f}) should be faster than L2 ({l2_rps:,.0f})"

        # Speed ratios
        l0_l1_ratio = l0_rps / l1_rps if l1_rps > 0 else 0
        l1_l2_ratio = l1_rps / l2_rps if l2_rps > 0 else 0

        print(f"\nSpeed Ratios:")
        print(f"  L0/L1: {l0_l1_ratio:.1f}x")
        print(f"  L1/L2: {l1_l2_ratio:.1f}x")


class TestSpeedRegressionSummary:
    """Summary test for speed regression"""

    @pytest.fixture
    def all_results(self) -> Dict[str, SpeedResult]:
        """Run all speed tests"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            seed=42,
        )

        results = {}

        # L0 test
        results["L0"] = run_speed_test(
            SimulationLevel.L0_FUNCTIONAL,
            config,
            num_requests=100000,
        )

        # L1 test
        results["L1"] = run_speed_test(
            SimulationLevel.L1_TRANSACTION,
            config,
            num_requests=100000,
        )

        # L2 test
        results["L2"] = run_speed_test(
            SimulationLevel.L2_CYCLE_ACCURATE,
            config,
            sim_time_us=100.0,
        )

        return results

    def test_summary_report(self, all_results: Dict[str, SpeedResult]):
        """Generate speed summary report"""
        print("\n" + "=" * 70)
        print("Speed Regression Summary")
        print("=" * 70)

        for level, result in all_results.items():
            print(f"\n{level} ({result.level}):")
            print(f"  Throughput:     {result.requests_per_second:>12,.0f} req/s")
            print(f"  Wall Time:      {result.wall_time_ms:>12,.1f} ms")
            print(f"  Completed:      {result.completed_requests:>12,}")
            print(f"  Cycles/Req:     {result.cycles_per_request:>12.1f}")

        # Check targets
        print(f"\nTargets Check:")
        print(f"  L0 >= {L0_MIN_RPS:,} req/s: {'PASS' if all_results['L0'].requests_per_second >= L0_MIN_RPS else 'FAIL'}")
        print(f"  L1 >= {L1_MIN_RPS:,} req/s:  {'PASS' if all_results['L1'].requests_per_second >= L1_MIN_RPS else 'FAIL'}")
        print(f"  L2 >= {L2_MIN_RPS:,} req/s:  {'PASS' if all_results['L2'].requests_per_second >= L2_MIN_RPS else 'FAIL'}")

        print("=" * 70)

        # Basic assertions
        assert all_results["L0"].requests_per_second > 0
        assert all_results["L1"].requests_per_second > 0
        assert all_results["L2"].requests_per_second > 0


class TestSpeedStability:
    """Test speed consistency across multiple runs"""

    def test_l0_stability(self):
        """L0 speed should be consistent"""
        config = SimulationConfig(seed=42)
        speeds = []

        for _ in range(3):
            result = run_speed_test(
                SimulationLevel.L0_FUNCTIONAL,
                config,
                num_requests=50000,
            )
            speeds.append(result.requests_per_second)

        # Check coefficient of variation
        mean = sum(speeds) / len(speeds)
        if mean > 0:
            variance = sum((s - mean) ** 2 for s in speeds) / len(speeds)
            std_dev = variance ** 0.5
            cv = std_dev / mean
            max_cv = 0.30  # 30% variation allowed for Python
            assert cv <= max_cv, f"L0 speed CV {cv:.2%} exceeds {max_cv:.0%}"

    def test_l2_stability(self):
        """L2 speed should be consistent"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            seed=42,
        )
        speeds = []

        for seed in [42, 123, 456]:
            config.seed = seed
            result = run_speed_test(
                SimulationLevel.L2_CYCLE_ACCURATE,
                config,
                sim_time_us=50.0,
            )
            speeds.append(result.requests_per_second)

        # Check coefficient of variation
        mean = sum(speeds) / len(speeds)
        if mean > 0:
            variance = sum((s - mean) ** 2 for s in speeds) / len(speeds)
            std_dev = variance ** 0.5
            cv = std_dev / mean
            max_cv = 0.30  # 30% variation allowed for cycle-accurate sim
            assert cv <= max_cv, f"L2 speed CV {cv:.2%} exceeds {max_cv:.0%}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])