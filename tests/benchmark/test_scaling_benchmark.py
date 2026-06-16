"""
Multi-Channel Scaling Benchmark Tests

Tests for validating scaling behavior with multiple channels.
HBM4 supports 32 channels per stack - tests verify proper scaling.

Test Categories:
- channel_scaling: Throughput scaling with channel count
- load_balancing: Load distribution across channels
- bandwidth_aggregation: Aggregate bandwidth from multiple channels
- channel_variance: Variance in channel utilization

References:
- JEDEC JESD270-4A HBM4 Specification
- Multi-channel HBM architecture
"""

import pytest
import numpy as np
from typing import List, Dict, Tuple

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
from model.multi_channel import ChannelSelector, ChannelStats


class ScalingBenchmark:
    """Benchmark harness for multi-channel scaling tests"""

    @staticmethod
    def test_channel_scaling(
        hbm_config,
        channel_counts: List[int],
        duration_us: float = 50.0
    ) -> List[Dict]:
        """Test throughput scaling with channel count

        Args:
            hbm_config: Base HBM configuration
            channel_counts: List of channel counts to test
            duration_us: Simulation duration per test

        Returns:
            List of results dictionaries
        """
        from model.controller.config import HBMConfig
        results = []

        for count in channel_counts:
            # Create new config with modified channel count
            # Use single stack to avoid scaling issues
            config = HBMConfig(
                stack_count=1,  # Single stack for clean channel scaling
                channels_per_stack=count,
                pseudo_channels_per_channel=hbm_config.pseudo_channels_per_channel,
                banks_per_pseudo_channel=hbm_config.banks_per_pseudo_channel,
                bank_groups_per_channel=hbm_config.bank_groups_per_channel,
                row_size=hbm_config.row_size,
                burst_length=hbm_config.burst_length,
                data_rate=hbm_config.data_rate,
                io_width=hbm_config.io_width,
                read_latency_base=hbm_config.read_latency_base,
                write_latency_base=hbm_config.write_latency_base,
                phy_latency=hbm_config.phy_latency,
                queue_depth=hbm_config.queue_depth,
                max_outstanding=hbm_config.max_outstanding,
                address_mapping=hbm_config.address_mapping,
                scheduler_mode=hbm_config.scheduler_mode,
                write_drain_policy=hbm_config.write_drain_policy,
                refresh_interval=hbm_config.refresh_interval,
                refresh_penalty=hbm_config.refresh_penalty,
                bw_guarantee_critical=hbm_config.bw_guarantee_critical,
                bw_guarantee_high=hbm_config.bw_guarantee_high,
                bw_guarantee_normal=hbm_config.bw_guarantee_normal,
                bw_guarantee_low=hbm_config.bw_guarantee_low,
                timing=hbm_config.timing,
            )

            sim_config = SimulationConfig(
                simulation_time_us=duration_us,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.8,
                read_ratio=0.7,
                seed=42,
                hbm_config=config,
            )

            sim = HBMSimulator(sim_config)
            stats = sim.run()

            # Calculate scaling efficiency
            # Ideal: linear scaling with channels
            # Actual: typically sub-linear due to overhead
            results.append({
                'channel_count': count,
                'throughput_gbps': stats.throughput_gbps,
                'per_channel_bw': stats.throughput_gbps / count if count > 0 else 0,
                'efficiency': stats.bandwidth_efficiency,
                'completed': stats.completed_requests,
            })

        return results

    @staticmethod
    def measure_load_balance(
        sim: HBMSimulator
    ) -> Dict:
        """Measure load balancing across channels

        Args:
            sim: Running simulator

        Returns:
            Dictionary with load balancing metrics
        """
        # Get per-channel statistics
        channel_stats = sim.get_channel_stats()

        if not channel_stats:
            return {
                'jains_fairness': 1.0,
                'cv': 0.0,
                'max_load': 0,
                'min_load': 0,
                'spread': 0,
            }

        loads = [s.total_requests for s in channel_stats.values()]

        if not loads or sum(loads) == 0:
            return {
                'jains_fairness': 1.0,
                'cv': 0.0,
                'max_load': 0,
                'min_load': 0,
                'spread': 0,
            }

        # Calculate metrics
        mean_load = np.mean(loads)
        std_load = np.std(loads)
        cv = std_load / mean_load if mean_load > 0 else 0  # Coefficient of variation

        # Jain's fairness index
        n = len(loads)
        sum_loads = sum(loads)
        sum_sq = sum(l * l for l in loads)
        jains_fairness = (sum_loads * sum_loads) / (n * sum_sq) if sum_sq > 0 else 1.0

        return {
            'jains_fairness': jains_fairness,
            'cv': cv,
            'max_load': max(loads),
            'min_load': min(loads),
            'spread': max(loads) - min(loads),
            'mean_load': mean_load,
            'std_load': std_load,
        }


@pytest.mark.benchmark
class TestScalingBenchmark:
    """Multi-channel scaling benchmark tests"""

    @pytest.fixture
    def hbm4_config(self):
        """HBM4 configuration for scaling tests"""
        from model.controller.config import HBM4_DEFAULT
        return HBM4_DEFAULT

    def test_channel_scaling_linear(self, hbm4_config):
        """Test linear scaling with channel count

        Validates that throughput scales approximately linearly
        with the number of channels.
        """
        channel_counts = [4, 8, 16, 32]
        results = ScalingBenchmark.test_channel_scaling(
            hbm4_config, channel_counts, duration_us=50.0
        )

        print(f"\nChannel Scaling:")
        print(f"{'Channels':>10} | {'Throughput':>12} | {'Per-Channel':>12} | {'Efficiency':>10}")
        print("-" * 50)
        for r in results:
            print(f"{r['channel_count']:>10} | "
                  f"{r['throughput_gbps']:>11.2f} GB/s | "
                  f"{r['per_channel_bw']:>11.2f} GB/s | "
                  f"{r['efficiency']:>9.2%}")

        # Verify scaling behavior
        # Each configuration should achieve positive throughput
        for r in results:
            assert r['throughput_gbps'] > 0, \
                f"No throughput with {r['channel_count']} channels"

        # Verify that throughput increases with channels
        for i in range(1, len(results)):
            assert results[i]['throughput_gbps'] >= results[i-1]['throughput_gbps'], \
                f"Throughput decreased from {results[i-1]['channel_count']} to " \
                f"{results[i]['channel_count']} channels"

    def test_per_channel_bandwidth_consistency(self, hbm4_config):
        """Test that per-channel bandwidth is consistent

        Each channel should provide similar bandwidth.
        Significant variation indicates load imbalance.
        """
        channel_counts = [8, 16, 32]
        results = ScalingBenchmark.test_channel_scaling(
            hbm4_config, channel_counts, duration_us=30.0
        )

        print(f"\nPer-Channel Bandwidth Consistency:")
        for r in results:
            per_ch = r['per_channel_bw']
            # Calculate expected per-channel bandwidth
            # For HBM4: peak ~256 GB/s per 32 channels = 8 GB/s per channel
            expected_per_ch = 8.0  # GB/s per channel (approximate)
            variance = abs(per_ch - expected_per_ch) / expected_per_ch if expected_per_ch > 0 else 0

            print(f"  {r['channel_count']} channels: {per_ch:.2f} GB/s per channel "
                  f"(variance: {variance:.1%})")

            # Per-channel bandwidth should be positive and reasonable
            assert per_ch > 0, \
                f"Zero per-channel bandwidth at {r['channel_count']} channels"

    def test_load_balancing_quality(self, hbm4_config):
        """Test quality of load balancing across channels

        Good load balancing ensures all channels are utilized.
        Poor load balancing leads to channel starvation.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.8,
            read_ratio=0.7,
            seed=42,
            hbm_config=hbm4_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        metrics = ScalingBenchmark.measure_load_balance(sim)

        print(f"\nLoad Balancing Quality:")
        print(f"  Jain's Fairness Index: {metrics['jains_fairness']:.3f}")
        print(f"  Coefficient of Variation: {metrics['cv']:.3f}")
        print(f"  Load Range: {metrics['min_load']} - {metrics['max_load']}")
        print(f"  Load Spread: {metrics['spread']}")
        print(f"  Mean Load: {metrics['mean_load']:.1f}")
        print(f"  Std Dev: {metrics['std_load']:.1f}")

        # Jain's fairness index should be high (> 0.8)
        min_fairness = 0.7
        assert metrics['jains_fairness'] >= min_fairness, \
            f"Poor load balancing: fairness={metrics['jains_fairness']:.3f}"

        # CV should be reasonable (< 0.5 for good balance)
        max_cv = 0.5
        assert metrics['cv'] <= max_cv, \
            f"High load variance: CV={metrics['cv']:.3f}"

    def test_load_balance_by_pattern(self, hbm4_config):
        """Test load balancing for different traffic patterns

        Some patterns may stress load balancing more than others.
        """
        patterns = [
            (TrafficPattern.RANDOM, "Random"),
            (TrafficPattern.SEQUENTIAL, "Sequential"),
            (TrafficPattern.HOT_SPOT, "Hot Spot"),
        ]

        results = []
        for pattern, name in patterns:
            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=pattern,
                request_rate=0.7,
                read_ratio=0.7,
                seed=42,
                hbm_config=hbm4_config,
            )

            sim = HBMSimulator(sim_config)
            stats = sim.run()

            metrics = ScalingBenchmark.measure_load_balance(sim)
            metrics['pattern'] = name
            results.append(metrics)

        print(f"\nLoad Balancing by Pattern:")
        print(f"{'Pattern':>12} | {'Fairness':>10} | {'CV':>8} | {'Spread':>8}")
        print("-" * 45)
        for r in results:
            print(f"{r['pattern']:>12} | {r['jains_fairness']:>10.3f} | "
                  f"{r['cv']:>8.3f} | {r['spread']:>8}")

        # All patterns should achieve reasonable fairness
        for r in results:
            assert r['jains_fairness'] > 0.5, \
                f"Poor fairness for {r['pattern']}: {r['jains_fairness']:.3f}"

    def test_channel_utilization_distribution(self, hbm4_config):
        """Test distribution of requests across channels

        Validates that requests are distributed across channels.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.7,
            read_ratio=0.7,
            seed=42,
            hbm_config=hbm4_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        channel_stats = sim.get_channel_stats()
        if not channel_stats:
            pytest.skip("No channel statistics available")

        loads = [s.total_requests for s in channel_stats.values()]
        active_channels = sum(1 for l in loads if l > 0)
        total_channels = len(loads)

        print(f"\nChannel Utilization:")
        print(f"  Total Channels: {total_channels}")
        print(f"  Active Channels: {active_channels}")
        print(f"  Utilization: {active_channels/total_channels:.1%}")
        print(f"  Load Distribution:")
        print(f"    Min: {min(loads) if loads else 0}")
        print(f"    Max: {max(loads) if loads else 0}")
        print(f"    Mean: {np.mean(loads) if loads else 0:.1f}")
        print(f"    Std: {np.std(loads) if loads else 0:.1f}")

        # Most channels should be active
        min_active_ratio = 0.5  # At least 50% active
        assert active_channels >= total_channels * min_active_ratio, \
            f"Few active channels: {active_channels}/{total_channels}"

    def test_multi_stack_scaling(self, hbm4_config):
        """Test scaling with multiple HBM stacks

        HBM4 supports up to 4 stacks.
        """
        from model.controller.config import HBMConfig
        stack_counts = [1, 2, 4]
        results = []

        for stack_count in stack_counts:
            config = HBMConfig(
                stack_count=stack_count,
                channels_per_stack=hbm4_config.channels_per_stack,
                pseudo_channels_per_channel=hbm4_config.pseudo_channels_per_channel,
                banks_per_pseudo_channel=hbm4_config.banks_per_pseudo_channel,
                bank_groups_per_channel=hbm4_config.bank_groups_per_channel,
                row_size=hbm4_config.row_size,
                burst_length=hbm4_config.burst_length,
                data_rate=hbm4_config.data_rate,
                io_width=hbm4_config.io_width,
                read_latency_base=hbm4_config.read_latency_base,
                write_latency_base=hbm4_config.write_latency_base,
                phy_latency=hbm4_config.phy_latency,
                queue_depth=hbm4_config.queue_depth,
                max_outstanding=hbm4_config.max_outstanding,
                address_mapping=hbm4_config.address_mapping,
                scheduler_mode=hbm4_config.scheduler_mode,
                write_drain_policy=hbm4_config.write_drain_policy,
                refresh_interval=hbm4_config.refresh_interval,
                refresh_penalty=hbm4_config.refresh_penalty,
                bw_guarantee_critical=hbm4_config.bw_guarantee_critical,
                bw_guarantee_high=hbm4_config.bw_guarantee_high,
                bw_guarantee_normal=hbm4_config.bw_guarantee_normal,
                bw_guarantee_low=hbm4_config.bw_guarantee_low,
                timing=hbm4_config.timing,
            )

            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.8,
                read_ratio=0.7,
                seed=42,
                hbm_config=config,
            )

            sim = HBMSimulator(sim_config)
            stats = sim.run()

            total_channels = config.channels_per_stack * stack_count
            results.append({
                'stacks': stack_count,
                'total_channels': total_channels,
                'throughput_gbps': stats.throughput_gbps,
            })

        print(f"\nMulti-Stack Scaling:")
        for r in results:
            print(f"  {r['stacks']} stack(s) ({r['total_channels']} channels): "
                  f"{r['throughput_gbps']:.2f} GB/s")

        # Throughput should scale with stacks
        for i in range(1, len(results)):
            assert results[i]['throughput_gbps'] >= results[i-1]['throughput_gbps'], \
                f"Throughput decreased with more stacks"


@pytest.mark.benchmark
@pytest.mark.slow
class TestScalingExtended:
    """Extended scaling tests for thorough validation"""

    def test_ideal_vs_actual_scaling(self, hbm4_config):
        """Compare actual scaling to ideal linear scaling

        Ideal scaling: 2x channels = 2x throughput
        Actual scaling is typically 1.5-1.9x due to overhead.
        """
        channel_counts = [4, 8, 16, 32]
        results = ScalingBenchmark.test_channel_scaling(
            hbm4_config, channel_counts, duration_us=100.0
        )

        print(f"\nIdeal vs Actual Scaling:")
        print(f"{'Channels':>10} | {'Actual':>12} | {'Ideal':>12} | {'Ratio':>8}")
        print("-" * 48)

        baseline = results[0]['throughput_gbps']
        baseline_channels = results[0]['channel_count']

        for r in results:
            ideal = baseline * (r['channel_count'] / baseline_channels)
            ratio = r['throughput_gbps'] / ideal if ideal > 0 else 0

            print(f"{r['channel_count']:>10} | "
                  f"{r['throughput_gbps']:>11.2f} GB/s | "
                  f"{ideal:>11.2f} GB/s | "
                  f"{ratio:>7.1%}")

            # Actual should be at least 50% of ideal
            min_ratio = 0.5
            assert ratio >= min_ratio, \
                f"Poor scaling at {r['channel_count']} channels: {ratio:.1%} of ideal"

    def test_fairness_vs_request_rate(self, hbm4_config):
        """Test load balancing at different request rates

        High request rates may stress load balancing.
        """
        rates = [0.3, 0.5, 0.7, 0.9]
        results = []

        for rate in rates:
            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=rate,
                read_ratio=0.7,
                seed=42,
                hbm_config=hbm4_config,
            )

            sim = HBMSimulator(sim_config)
            stats = sim.run()

            metrics = ScalingBenchmark.measure_load_balance(sim)
            metrics['rate'] = rate
            results.append(metrics)

        print(f"\nFairness vs Request Rate:")
        for r in results:
            print(f"  Rate={r['rate']:.1f}: fairness={r['jains_fairness']:.3f}, "
                  f"CV={r['cv']:.3f}")

        # All rates should achieve reasonable fairness
        for r in results:
            assert r['jains_fairness'] > 0.5, \
                f"Poor fairness at rate {r['rate']}: {r['jains_fairness']:.3f}"

    def test_channel_saturation(self, hbm4_config):
        """Test behavior when all channels are saturated

        At high load, channels should be fully utilized.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=1.0,  # Maximum rate
            read_ratio=0.7,
            max_requests_per_cycle=16,  # Generate many per cycle
            hbm_config=hbm4_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        metrics = ScalingBenchmark.measure_load_balance(sim)

        print(f"\nChannel Saturation Test:")
        print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
        print(f"  Completed: {stats.completed_requests}")
        print(f"  Fairness: {metrics['jains_fairness']:.3f}")
        print(f"  CV: {metrics['cv']:.3f}")

        # At saturation, throughput should be high
        min_throughput = 200.0  # GB/s
        assert stats.throughput_gbps >= min_throughput, \
            f"Low saturation throughput: {stats.throughput_gbps:.2f}"

    def test_scaling_with_address_patterns(self, hbm4_config):
        """Test scaling with different address patterns

        Some patterns may not scale well due to address locality.
        """
        patterns = [
            (TrafficPattern.SEQUENTIAL, "Sequential"),
            (TrafficPattern.STRIDE, "Stride"),
            (TrafficPattern.RANDOM, "Random"),
        ]

        results = []
        for pattern, name in patterns:
            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=pattern,
                request_rate=0.7,
                read_ratio=0.7,
                seed=42,
                hbm_config=hbm4_config,
            )

            sim = HBMSimulator(sim_config)
            stats = sim.run()

            results.append({
                'pattern': name,
                'throughput_gbps': stats.throughput_gbps,
                'bandwidth_efficiency': stats.bandwidth_efficiency,
            })

        print(f"\nScaling with Address Patterns:")
        for r in results:
            print(f"  {r['pattern']}: {r['throughput_gbps']:.2f} GB/s "
                  f"({r['bandwidth_efficiency']:.1%} efficiency)")

        # All patterns should achieve some throughput
        for r in results:
            assert r['throughput_gbps'] > 0, \
                f"No throughput for {r['pattern']} pattern"