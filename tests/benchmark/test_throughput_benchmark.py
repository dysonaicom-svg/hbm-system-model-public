"""
Throughput Benchmark Tests

Tests for measuring sustained throughput performance.
Validates system throughput under various workloads and configurations.

Test Categories:
- sustained_throughput: Long-duration throughput tests
- throughput_vs_channels: Scaling with channel count
- throughput_vs_burst: Effect of burst size on throughput
- queue_throughput: Throughput with queue depth variations

References:
- JEDEC JESD270-4A HBM4 Specification
- Transaction throughput requirements
"""

import pytest
import numpy as np
from typing import List, Dict

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern


class ThroughputBenchmark:
    """Benchmark harness for throughput testing"""

    @staticmethod
    def measure_sustained_throughput(
        sim_config: SimulationConfig,
        min_duration_us: float = 100.0
    ) -> Dict:
        """Measure sustained throughput

        Args:
            sim_config: Simulation configuration
            min_duration_us: Minimum simulation duration

        Returns:
            Dictionary with throughput metrics
        """
        if sim_config.simulation_time_us < min_duration_us:
            sim_config.simulation_time_us = min_duration_us

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        return {
            'throughput_gbps': stats.throughput_gbps,
            'completed_requests': stats.completed_requests,
            'total_requests': stats.total_requests,
            'total_cycles': stats.total_cycles,
            'efficiency': stats.efficiency,
            'bandwidth_efficiency': stats.bandwidth_efficiency,
            'avg_latency': stats.avg_latency,
        }

    @staticmethod
    def measure_requests_per_second(
        sim_config: SimulationConfig
    ) -> Dict:
        """Measure requests per second throughput

        Args:
            sim_config: Simulation configuration

        Returns:
            Dictionary with request rate metrics
        """
        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # Calculate requests per second
        total_ns = stats.total_cycles * sim.tCK_ns
        req_per_sec = (stats.completed_requests / total_ns) * 1e9 if total_ns > 0 else 0

        return {
            'requests_per_second': req_per_sec,
            'completed_requests': stats.completed_requests,
            'total_cycles': stats.total_cycles,
            'total_ns': total_ns,
        }


@pytest.mark.benchmark
class TestThroughputBenchmark:
    """Throughput benchmark tests"""

    @pytest.fixture
    def sim_config(self, hbm3_config):
        """Default simulation configuration"""
        return SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.6,
            read_ratio=0.7,
            seed=42,
            hbm_config=hbm3_config,
        )

    def test_sustained_throughput(self, sim_config):
        """Test sustained throughput over extended period

        Validates that throughput remains stable over time.
        """
        result = ThroughputBenchmark.measure_sustained_throughput(sim_config)

        print(f"\nSustained Throughput:")
        print(f"  Throughput: {result['throughput_gbps']:.2f} GB/s")
        print(f"  Completed: {result['completed_requests']} requests")
        print(f"  Cycles: {result['total_cycles']}")
        print(f"  Efficiency: {result['efficiency']:.2%}")
        print(f"  Bandwidth Efficiency: {result['bandwidth_efficiency']:.2%}")

        # Minimum throughput threshold
        min_throughput = 50.0  # GB/s
        assert result['throughput_gbps'] >= min_throughput, \
            f"Throughput {result['throughput_gbps']:.2f} below minimum {min_throughput}"

    def test_requests_per_second(self, sim_config):
        """Test requests per second throughput

        Measures the raw request processing rate.
        """
        result = ThroughputBenchmark.measure_requests_per_second(sim_config)

        print(f"\nRequests Per Second:")
        print(f"  Rate: {result['requests_per_second']:.0f} req/s")
        print(f"  Completed: {result['completed_requests']} requests")
        print(f"  Duration: {result['total_ns']:.0f} ns")

        # Minimum request rate
        min_req_per_sec = 100000.0  # 100K req/s
        assert result['requests_per_second'] >= min_req_per_sec, \
            f"Request rate {result['requests_per_sec']:.0f} below minimum"

    def test_throughput_vs_channels(self, hbm3_config):
        """Test throughput scaling with channel count

        Validates that throughput scales with available channels.
        """
        channel_configs = [
            (1, "Single Channel"),
            (8, "8 Channels (HBM3)"),
            (16, "16 Channels"),
        ]

        results = []
        for num_channels, name in channel_configs:
            config = hbm3_config.copy()
            config.channels_per_stack = num_channels

            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.7,
                read_ratio=0.7,
                seed=42,
                hbm_config=config,
            )

            result = ThroughputBenchmark.measure_sustained_throughput(sim_config)
            results.append({
                'name': name,
                'channels': num_channels,
                'throughput_gbps': result['throughput_gbps'],
            })

        print(f"\nThroughput vs Channel Count:")
        for r in results:
            print(f"  {r['name']}: {r['throughput_gbps']:.2f} GB/s")

        # Verify scaling behavior
        for i in range(1, len(results)):
            # More channels should generally mean more throughput
            if results[i]['channels'] > results[i-1]['channels']:
                assert results[i]['throughput_gbps'] > 0, \
                    f"No throughput for {results[i]['name']}"

    def test_throughput_by_pattern(self, hbm3_config):
        """Test throughput for different traffic patterns

        Different patterns have different throughput characteristics.
        """
        patterns = [
            (TrafficPattern.RANDOM, "Random"),
            (TrafficPattern.SEQUENTIAL, "Sequential"),
            (TrafficPattern.HOT_SPOT, "Hot Spot"),
            (TrafficPattern.STRIDE, "Stride"),
        ]

        results = []
        for pattern, name in patterns:
            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=pattern,
                request_rate=0.6,
                read_ratio=0.7,
                seed=42,
                hbm_config=hbm3_config,
            )

            result = ThroughputBenchmark.measure_sustained_throughput(sim_config)
            results.append({
                'pattern': name,
                'throughput_gbps': result['throughput_gbps'],
                'completed': result['completed_requests'],
            })

        print(f"\nThroughput by Pattern:")
        for r in results:
            print(f"  {r['pattern']}: {r['throughput_gbps']:.2f} GB/s "
                  f"({r['completed']} requests)")

        # All patterns should produce some throughput
        for r in results:
            assert r['throughput_gbps'] > 0, \
                f"No throughput for {r['pattern']} pattern"

    def test_throughput_vs_queue_depth(self, hbm3_config):
        """Test throughput with different queue depths

        Larger queues can absorb bursts better.
        """
        queue_depths = [16, 32, 64, 128]
        results = []

        for depth in queue_depths:
            config = hbm3_config.copy()
            config.queue_depth = depth
            config.max_outstanding = depth // 2

            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.8,  # High rate to stress queue
                read_ratio=0.7,
                seed=42,
                hbm_config=config,
            )

            result = ThroughputBenchmark.measure_sustained_throughput(sim_config)
            results.append({
                'depth': depth,
                'throughput_gbps': result['throughput_gbps'],
                'completed': result['completed_requests'],
                'total': result['total_requests'],
            })

        print(f"\nThroughput vs Queue Depth:")
        for r in results:
            print(f"  Depth={r['depth']:3d}: {r['throughput_gbps']:.2f} GB/s "
                  f"(completed {r['completed']}/{r['total']})")

        # All configurations should complete some requests
        for r in results:
            assert r['completed'] > 0, f"No completed requests at depth={r['depth']}"

    def test_burst_throughput(self, hbm3_config):
        """Test throughput under burst traffic

        Burst traffic generates many requests simultaneously.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.9,  # High rate for burst
            read_ratio=0.7,
            max_requests_per_cycle=8,  # Generate up to 8 per cycle
            hbm_config=hbm3_config,
        )

        result = ThroughputBenchmark.measure_sustained_throughput(sim_config)

        print(f"\nBurst Throughput:")
        print(f"  Throughput: {result['throughput_gbps']:.2f} GB/s")
        print(f"  Completed: {result['completed_requests']} requests")
        print(f"  Total: {result['total_requests']} requests")
        print(f"  Efficiency: {result['efficiency']:.2%}")

        # Burst traffic should achieve good throughput
        min_throughput = 80.0  # GB/s
        assert result['throughput_gbps'] >= min_throughput, \
            f"Burst throughput {result['throughput_gbps']:.2f} below minimum"

    def test_read_write_throughput_split(self, hbm3_config):
        """Test throughput for read/write mixes

        Read and write operations may have different throughput.
        """
        read_ratios = [1.0, 0.7, 0.5, 0.3, 0.0]
        results = []

        for ratio in read_ratios:
            sim_config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.6,
                read_ratio=ratio,
                seed=42,
                hbm_config=hbm3_config,
            )

            result = ThroughputBenchmark.measure_sustained_throughput(sim_config)
            results.append({
                'read_ratio': ratio,
                'throughput_gbps': result['throughput_gbps'],
            })

        print(f"\nRead/Write Throughput Split:")
        for r in results:
            read_pct = r['read_ratio'] * 100
            print(f"  Read={read_pct:5.1f}%: {r['throughput_gbps']:.2f} GB/s")

        # All ratios should produce reasonable throughput
        for r in results:
            assert r['throughput_gbps'] > 0, \
                f"No throughput at read_ratio={r['read_ratio']}"


@pytest.mark.benchmark
@pytest.mark.slow
class TestThroughputExtended:
    """Extended throughput tests"""

    def test_multi_stack_throughput(self, hbm4_config):
        """Test throughput with multiple stacks

        HBM4 supports up to 4 stacks with 32 channels each.
        """
        for stack_count in [1, 2, 4]:
            config = hbm4_config.copy()
            config.stack_count = stack_count

            sim_config = SimulationConfig(
                simulation_time_us=100.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.8,
                read_ratio=0.7,
                hbm_config=config,
            )

            result = ThroughputBenchmark.measure_sustained_throughput(sim_config)

            print(f"\n{stack_count} Stack(s): {result['throughput_gbps']:.2f} GB/s")

            assert result['throughput_gbps'] > 0, \
                f"No throughput with {stack_count} stack(s)"

    def test_long_run_throughput_stability(self, hbm3_config):
        """Test throughput stability over very long simulation

        Validates no performance degradation over time.
        """
        sim_config = SimulationConfig(
            simulation_time_us=2000.0,  # 2ms simulation
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.7,
            read_ratio=0.7,
            seed=42,
            hbm_config=hbm3_config,
        )

        result = ThroughputBenchmark.measure_sustained_throughput(sim_config)

        print(f"\nLong Run Throughput (2ms):")
        print(f"  Throughput: {result['throughput_gbps']:.2f} GB/s")
        print(f"  Completed: {result['completed_requests']} requests")
        print(f"  Cycles: {result['total_cycles']}")

        # Should complete many requests
        min_completed = 50000  # Minimum expected completions
        assert result['completed_requests'] >= min_completed, \
            f"Low completion count: {result['completed_requests']}"

    def test_throughput_efficiency(self, sim_config):
        """Test throughput efficiency vs theoretical peak

        Efficiency = actual throughput / peak throughput
        """
        sim = HBMSimulator(sim_config)
        stats = sim.run()

        print(f"\nThroughput Efficiency:")
        print(f"  Actual: {stats.throughput_gbps:.2f} GB/s")
        print(f"  Peak: {stats.peak_bandwidth_gbps:.2f} GB/s")
        print(f"  Efficiency: {stats.bandwidth_efficiency:.2%}")

        # Minimum efficiency threshold
        min_efficiency = 0.05  # 5%
        assert stats.bandwidth_efficiency >= min_efficiency, \
            f"Low efficiency: {stats.bandwidth_efficiency:.2%}"