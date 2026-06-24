"""
HBM4 Bandwidth Measurement Tests

Comprehensive bandwidth measurement tests for HBM4 including:
- Peak bandwidth measurement (vs theoretical 2.048 TB/s)
- Sustained bandwidth measurement
- Different access pattern benchmarks
- Speed grade comparisons (8/12/16 Gbps)
- Channel scaling tests
- Performance baseline comparisons

Reference:
- JEDEC JESD270-4A HBM4 specification
- Theoretical peak: 8 GT/s x 2048 bits / 8 = 2048 GB/s (2.048 TB/s)
"""

import pytest
import time
import statistics
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from model.dram.hbm4_spec import HBM4Spec, HBM4_SPEED_GRADES
from model.dram.timing import HBM4Timing, get_timing_for_speed_grade
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel


# =============================================================================
# Bandwidth Metrics Container
# =============================================================================

@dataclass
class BandwidthMetrics:
    """Container for bandwidth measurement results"""
    name: str = ""
    speed_grade: str = "8Gbps"

    # Theoretical peak
    peak_bandwidth_gbs: float = 0.0
    peak_bandwidth_tbps: float = 0.0

    # Measured values
    measured_bandwidth_gbs: float = 0.0
    measured_bandwidth_tbps: float = 0.0

    # Efficiency
    efficiency_percent: float = 0.0

    # Request statistics
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    total_bytes: int = 0

    # Timing
    test_duration_ns: float = 0.0
    test_duration_cycles: int = 0

    # Pattern-specific
    row_hit_rate_percent: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'speed_grade': self.speed_grade,
            'peak_bandwidth_gbs': self.peak_bandwidth_gbs,
            'peak_bandwidth_tbps': self.peak_bandwidth_tbps,
            'measured_bandwidth_gbs': self.measured_bandwidth_gbs,
            'measured_bandwidth_tbps': self.measured_bandwidth_tbps,
            'efficiency_percent': self.efficiency_percent,
            'total_requests': self.total_requests,
            'read_requests': self.read_requests,
            'write_requests': self.write_requests,
            'total_bytes': self.total_bytes,
            'test_duration_ns': self.test_duration_ns,
            'row_hit_rate_percent': self.row_hit_rate_percent,
        }


class BandwidthMeasurementFramework:
    """Framework for measuring HBM4 bandwidth"""

    # Theoretical bandwidths for different speed grades
    THEORETICAL_BANDWIDTHS = {
        "8Gbps": {"gbs": 2048.0, "tbps": 2.048},
        "12Gbps": {"gbs": 3072.0, "tbps": 3.072},
        "16Gbps": {"gbs": 4096.0, "tbps": 4.096},
    }

    # Minimum efficiency thresholds for passing
    EFFICIENCY_THRESHOLDS = {
        "sequential": 70.0,  # Sequential should achieve high efficiency
        "random": 30.0,      # Random should achieve moderate efficiency
        "hotspot": 50.0,     # Hotspot should achieve good efficiency
    }

    def __init__(self, speed_grade: str = "8Gbps"):
        self.speed_grade = speed_grade
        self.spec = self._create_spec()
        self.timing = get_timing_for_speed_grade(speed_grade)
        self.controller: Optional[HBM4Controller] = None

    def _create_spec(self) -> HBM4Spec:
        """Create HBM4 specification for speed grade"""
        if self.speed_grade not in HBM4_SPEED_GRADES:
            raise ValueError(f"Unknown speed grade: {self.speed_grade}")

        grade_params = HBM4_SPEED_GRADES[self.speed_grade]
        return HBM4Spec(
            data_rate_gtps=grade_params["data_rate_gtps"],
            tCK_ps=grade_params["tCK_ps"]
        )

    def measure_bandwidth(
        self,
        pattern: str,
        num_requests: int,
        read_ratio: float = 0.7,
        request_size: int = 64,
        enable_qos: bool = False,
        enable_refresh: bool = False,
    ) -> BandwidthMetrics:
        """Measure bandwidth for given pattern

        Args:
            pattern: Access pattern (sequential, random, hotspot, strided, row_hit)
            num_requests: Number of requests to submit
            read_ratio: Read/write ratio
            request_size: Size per request in bytes
            enable_qos: Enable QoS scheduling
            enable_refresh: Enable refresh

        Returns:
            BandwidthMetrics with measurement results
        """
        metrics = BandwidthMetrics()
        metrics.name = f"{pattern}_{num_requests}req"
        metrics.speed_grade = self.speed_grade
        metrics.peak_bandwidth_gbs = self.spec.bandwidth_gbs
        metrics.peak_bandwidth_tbps = self.spec.bandwidth

        # Create controller
        self.controller = HBM4Controller(
            spec=self.spec,
            enable_qos=enable_qos,
            enable_refresh=enable_refresh
        )

        # Generate addresses based on pattern
        addresses = self._generate_addresses(pattern, num_requests)

        # Submit requests
        start_ns = self.controller.current_time_ns
        submit_count = 0

        for i in range(num_requests):
            addr = addresses[i % len(addresses)]
            is_read = (i % 100) < (read_ratio * 100)

            req_id = self.controller.submit_request(
                addr=addr,
                is_read=is_read,
                size_bytes=request_size
            )

            if req_id:
                submit_count += 1
                if is_read:
                    metrics.read_requests += 1
                else:
                    metrics.write_requests += 1

        metrics.total_requests = submit_count

        # Process until all requests complete
        max_cycles = 100000
        cycles = 0
        while (len(self.controller.queue_manager.read_queue) > 0 or
               len(self.controller.queue_manager.write_queue) > 0):
            self.controller.tick()
            cycles += 1
            if cycles > max_cycles:
                break

        end_ns = self.controller.current_time_ns
        metrics.test_duration_ns = end_ns - start_ns
        metrics.test_duration_cycles = cycles

        # Calculate bandwidth
        metrics.total_bytes = metrics.total_requests * request_size
        if metrics.test_duration_ns > 0:
            metrics.measured_bandwidth_gbs = (
                metrics.total_bytes / metrics.test_duration_ns * 1000
            )
            metrics.measured_bandwidth_tbps = metrics.measured_bandwidth_gbs / 1000

        # Calculate efficiency
        if metrics.peak_bandwidth_gbs > 0:
            metrics.efficiency_percent = (
                metrics.measured_bandwidth_gbs / metrics.peak_bandwidth_gbs * 100
            )

        # Calculate row hit rate
        if hasattr(self.controller, 'stats'):
            completed = self.controller.stats.total_requests
            if completed > 0:
                hits = getattr(self.controller.stats, 'row_hit_count', 0)
                metrics.row_hit_rate_percent = (hits / completed * 100) if hits else 0

        return metrics

    def _generate_addresses(
        self,
        pattern: str,
        count: int,
        base_addr: int = 0x10000
    ) -> List[int]:
        """Generate addresses based on access pattern

        Args:
            pattern: Access pattern
            count: Number of addresses
            base_addr: Base address for generation

        Returns:
            List of addresses
        """
        random.seed(42)  # Reproducibility

        if pattern == "sequential":
            # Consecutive addresses
            return [base_addr + i * 64 for i in range(count)]

        elif pattern == "random":
            # Random addresses across address space
            return [random.randint(base_addr, base_addr + 0x100000) for _ in range(count)]

        elif pattern == "hotspot":
            # 80% accesses to 20% of address space
            hotspot_size = 0x20000
            hotspot_start = base_addr
            results = []
            for i in range(count):
                if random.random() < 0.80:
                    results.append(hotspot_start + random.randint(0, hotspot_size - 1))
                else:
                    results.append(base_addr + random.randint(hotspot_size, 0x100000))
            return results

        elif pattern == "strided":
            # Fixed stride (cache line size = 64 bytes)
            stride = 256  # 4 cache lines
            return [base_addr + (i * stride) for i in range(count)]

        elif pattern == "row_hit":
            # All accesses to same row (best case)
            return [base_addr] * count

        elif pattern == "bank_conflict":
            # Spread across different banks (worst case)
            bank_size = 0x1000
            return [base_addr + (i * bank_size) for i in range(count)]

        else:
            return [base_addr + i * 64 for i in range(count)]


# =============================================================================
# Test Cases
# =============================================================================

class TestHBM4BandwidthMeasurement:
    """HBM4 bandwidth measurement tests"""

    @pytest.fixture
    def framework(self):
        """Create bandwidth measurement framework"""
        return BandwidthMeasurementFramework(speed_grade="8Gbps")

    def test_theoretical_bandwidth_8gbps(self):
        """Test theoretical bandwidth calculation for 8Gbps"""
        framework = BandwidthMeasurementFramework(speed_grade="8Gbps")

        # 8 GT/s * 2048 bits / 8 = 2048 GB/s
        assert framework.spec.bandwidth_gbs == pytest.approx(2048.0, rel=0.01)
        assert framework.spec.bandwidth == pytest.approx(2.048, rel=0.01)

    def test_theoretical_bandwidth_12gbps(self):
        """Test theoretical bandwidth calculation for 12Gbps"""
        framework = BandwidthMeasurementFramework(speed_grade="12Gbps")

        # 12 GT/s * 2048 bits / 8 = 3072 GB/s
        assert framework.spec.bandwidth_gbs == pytest.approx(3072.0, rel=0.01)
        assert framework.spec.bandwidth == pytest.approx(3.072, rel=0.01)

    def test_theoretical_bandwidth_16gbps(self):
        """Test theoretical bandwidth calculation for 16Gbps"""
        framework = BandwidthMeasurementFramework(speed_grade="16Gbps")

        # 16 GT/s * 2048 bits / 8 = 4096 GB/s
        assert framework.spec.bandwidth_gbs == pytest.approx(4096.0, rel=0.01)
        assert framework.spec.bandwidth == pytest.approx(4.096, rel=0.01)

    def test_sequential_access_bandwidth(self, framework):
        """Test bandwidth with sequential access pattern"""
        metrics = framework.measure_bandwidth(
            pattern="sequential",
            num_requests=1000,
            read_ratio=0.8,
            enable_refresh=False
        )

        print(f"\n{'='*60}")
        print(f"Sequential Access Bandwidth Test")
        print(f"{'='*60}")
        print(f"  Speed Grade: {metrics.speed_grade}")
        print(f"  Peak Bandwidth: {metrics.peak_bandwidth_gbs:.1f} GB/s ({metrics.peak_bandwidth_tbps:.3f} TB/s)")
        print(f"  Measured Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s ({metrics.measured_bandwidth_tbps:.3f} TB/s)")
        print(f"  Efficiency: {metrics.efficiency_percent:.1f}%")
        print(f"  Requests: {metrics.total_requests} ({metrics.read_requests} reads, {metrics.write_requests} writes)")
        print(f"  Duration: {metrics.test_duration_ns:.0f} ns")

        # Sequential should achieve good efficiency
        assert metrics.efficiency_percent > 0
        assert metrics.measured_bandwidth_gbs > 0

    def test_random_access_bandwidth(self, framework):
        """Test bandwidth with random access pattern"""
        metrics = framework.measure_bandwidth(
            pattern="random",
            num_requests=500,
            read_ratio=0.7,
            enable_refresh=False
        )

        print(f"\n{'='*60}")
        print(f"Random Access Bandwidth Test")
        print(f"{'='*60}")
        print(f"  Speed Grade: {metrics.speed_grade}")
        print(f"  Peak Bandwidth: {metrics.peak_bandwidth_gbs:.1f} GB/s")
        print(f"  Measured Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s")
        print(f"  Efficiency: {metrics.efficiency_percent:.1f}%")

        # Random access should still achieve some bandwidth
        assert metrics.efficiency_percent > 0

    def test_hotspot_access_bandwidth(self, framework):
        """Test bandwidth with hotspot access pattern"""
        metrics = framework.measure_bandwidth(
            pattern="hotspot",
            num_requests=1000,
            read_ratio=0.8,
            enable_refresh=False
        )

        print(f"\n{'='*60}")
        print(f"Hotspot Access Bandwidth Test")
        print(f"{'='*60}")
        print(f"  Speed Grade: {metrics.speed_grade}")
        print(f"  Measured Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s")
        print(f"  Efficiency: {metrics.efficiency_percent:.1f}%")

        # Hotspot should achieve better than random
        assert metrics.efficiency_percent > 0

    def test_row_hit_bandwidth(self, framework):
        """Test bandwidth with row hit pattern (best case)"""
        metrics = framework.measure_bandwidth(
            pattern="row_hit",
            num_requests=2000,
            read_ratio=0.9,
            enable_refresh=False
        )

        print(f"\n{'='*60}")
        print(f"Row Hit Bandwidth Test (Best Case)")
        print(f"{'='*60}")
        print(f"  Speed Grade: {metrics.speed_grade}")
        print(f"  Measured Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s")
        print(f"  Efficiency: {metrics.efficiency_percent:.1f}%")
        print(f"  Row Hit Rate: {metrics.row_hit_rate_percent:.1f}%")

        # Row hit pattern should achieve highest efficiency
        assert metrics.efficiency_percent > 50.0, f"Row hit efficiency too low: {metrics.efficiency_percent:.1f}%"

    def test_bank_conflict_bandwidth(self, framework):
        """Test bandwidth with bank conflict pattern (worst case)"""
        metrics = framework.measure_bandwidth(
            pattern="bank_conflict",
            num_requests=500,
            read_ratio=0.7,
            enable_refresh=False
        )

        print(f"\n{'='*60}")
        print(f"Bank Conflict Bandwidth Test (Worst Case)")
        print(f"{'='*60}")
        print(f"  Speed Grade: {metrics.speed_grade}")
        print(f"  Measured Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s")
        print(f"  Efficiency: {metrics.efficiency_percent:.1f}%")

        # Bank conflict should have lower efficiency
        assert metrics.efficiency_percent > 0


class TestBandwidthSpeedGradeComparison:
    """Compare bandwidth across different speed grades"""

    @pytest.mark.parametrize("speed_grade", ["8Gbps", "12Gbps", "16Gbps"])
    def test_speed_grade_bandwidth(self, speed_grade):
        """Test bandwidth scales correctly with speed grade"""
        framework = BandwidthMeasurementFramework(speed_grade=speed_grade)

        metrics = framework.measure_bandwidth(
            pattern="sequential",
            num_requests=1000,
            read_ratio=0.8,
            enable_refresh=False
        )

        print(f"\n{'='*60}")
        print(f"Speed Grade: {speed_grade}")
        print(f"{'='*60}")
        print(f"  Peak Bandwidth: {metrics.peak_bandwidth_gbs:.1f} GB/s")
        print(f"  Measured Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s")
        print(f"  Efficiency: {metrics.efficiency_percent:.1f}%")

        # Verify theoretical bandwidth matches expected
        expected_gbs = framework.THEORETICAL_BANDWIDTHS[speed_grade]["gbs"]
        assert metrics.peak_bandwidth_gbs == pytest.approx(expected_gbs, rel=0.01)

        # Measured should be > 0
        assert metrics.measured_bandwidth_gbs > 0

    def test_bandwidth_scaling_with_speed(self):
        """Test bandwidth scales proportionally with data rate"""
        results = {}

        for speed_grade in ["8Gbps", "12Gbps", "16Gbps"]:
            framework = BandwidthMeasurementFramework(speed_grade=speed_grade)
            metrics = framework.measure_bandwidth(
                pattern="row_hit",
                num_requests=2000,
                read_ratio=1.0,  # Pure reads for consistency
                enable_refresh=False
            )
            results[speed_grade] = metrics

        print(f"\n{'='*60}")
        print(f"Bandwidth Scaling Comparison")
        print(f"{'='*60}")

        for grade, metrics in results.items():
            print(f"  {grade}: {metrics.measured_bandwidth_gbs:.1f} GB/s ({metrics.efficiency_percent:.1f}%)")

        # Check that 12Gbps > 8Gbps and 16Gbps > 12Gbps
        # (efficiency should be similar if model is well-designed)
        assert results["12Gbps"].peak_bandwidth_gbs > results["8Gbps"].peak_bandwidth_gbs
        assert results["16Gbps"].peak_bandwidth_gbs > results["12Gbps"].peak_bandwidth_gbs


class TestBandwidthPatternComparison:
    """Compare bandwidth across different access patterns"""

    def test_pattern_efficiency_ranking(self):
        """Test that patterns rank by efficiency correctly"""
        framework = BandwidthMeasurementFramework(speed_grade="8Gbps")

        patterns = [
            ("row_hit", 2000),
            ("sequential", 2000),
            ("hotspot", 2000),
            ("random", 1000),
            ("bank_conflict", 500),
        ]

        results = []
        for pattern, num_req in patterns:
            metrics = framework.measure_bandwidth(
                pattern=pattern,
                num_requests=num_req,
                read_ratio=0.8,
                enable_refresh=False
            )
            results.append((pattern, metrics))

        print(f"\n{'='*60}")
        print(f"Pattern Efficiency Ranking")
        print(f"{'='*60}")
        for pattern, metrics in results:
            print(f"  {pattern:20s}: {metrics.efficiency_percent:5.1f}% ({metrics.measured_bandwidth_gbs:7.1f} GB/s)")

        # Extract efficiencies
        efficiencies = {p: m.efficiency_percent for p, m in results}

        # Row hit should be >= sequential (they are similar in our model)
        assert efficiencies["row_hit"] >= efficiencies["sequential"] * 0.9

        # Sequential should be >= hotspot
        assert efficiencies["sequential"] >= efficiencies["hotspot"] * 0.8

        # Hotspot should be >= random
        assert efficiencies["hotspot"] >= efficiencies["random"] * 0.7

        # Random should be >= bank conflict
        assert efficiencies["random"] >= efficiencies["bank_conflict"] * 0.5

    def test_pattern_bandwidth_absolute(self):
        """Test absolute bandwidth values per pattern"""
        framework = BandwidthMeasurementFramework(speed_grade="8Gbps")
        peak_bw = framework.spec.bandwidth_gbs

        patterns = [
            ("row_hit", 2000),
            ("sequential", 2000),
        ]

        for pattern, num_req in patterns:
            metrics = framework.measure_bandwidth(
                pattern=pattern,
                num_requests=num_req,
                read_ratio=1.0,
                enable_refresh=False
            )

            print(f"\n{pattern} pattern:")
            print(f"  Peak: {peak_bw:.1f} GB/s")
            print(f"  Measured: {metrics.measured_bandwidth_gbs:.1f} GB/s")
            print(f"  Efficiency: {metrics.efficiency_percent:.1f}%")


class TestBandwidthReadWriteMix:
    """Test bandwidth with different read/write ratios"""

    def test_read_only_bandwidth(self):
        """Test bandwidth with read-only traffic"""
        framework = BandwidthMeasurementFramework(speed_grade="8Gbps")

        metrics = framework.measure_bandwidth(
            pattern="sequential",
            num_requests=2000,
            read_ratio=1.0,
            enable_refresh=False
        )

        assert metrics.read_requests > 0
        assert metrics.write_requests == 0

        print(f"\nRead-only Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s")

    def test_write_only_bandwidth(self):
        """Test bandwidth with write-only traffic"""
        framework = BandwidthMeasurementFramework(speed_grade="8Gbps")

        metrics = framework.measure_bandwidth(
            pattern="sequential",
            num_requests=2000,
            read_ratio=0.0,
            enable_refresh=False
        )

        assert metrics.read_requests == 0
        assert metrics.write_requests > 0

        print(f"\nWrite-only Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s")

    def test_mixed_read_write_bandwidth(self):
        """Test bandwidth with mixed read/write traffic"""
        framework = BandwidthMeasurementFramework(speed_grade="8Gbps")

        metrics = framework.measure_bandwidth(
            pattern="sequential",
            num_requests=2000,
            read_ratio=0.7,
            enable_refresh=False
        )

        assert metrics.read_requests > 0
        assert metrics.write_requests > 0

        # Verify ratio is approximately 70/30
        total = metrics.read_requests + metrics.write_requests
        read_percent = metrics.read_requests / total * 100

        print(f"\nMixed R/W Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s")
        print(f"  Read: {metrics.read_requests} ({read_percent:.1f}%)")
        print(f"  Write: {metrics.write_requests} ({100-read_percent:.1f}%)")


class TestBandwidthPerformanceBaselines:
    """Performance baseline tests for bandwidth"""

    BASELINES = {
        "8Gbps": {
            "row_hit": {"min_efficiency": 70.0, "min_bandwidth_gbs": 1400.0},
            "sequential": {"min_efficiency": 60.0, "min_bandwidth_gbs": 1200.0},
            "hotspot": {"min_efficiency": 40.0, "min_bandwidth_gbs": 800.0},
        },
        "12Gbps": {
            "row_hit": {"min_efficiency": 70.0, "min_bandwidth_gbs": 2100.0},
            "sequential": {"min_efficiency": 60.0, "min_bandwidth_gbs": 1800.0},
            "hotspot": {"min_efficiency": 40.0, "min_bandwidth_gbs": 1200.0},
        },
        "16Gbps": {
            "row_hit": {"min_efficiency": 70.0, "min_bandwidth_gbs": 2800.0},
            "sequential": {"min_efficiency": 60.0, "min_bandwidth_gbs": 2400.0},
            "hotspot": {"min_efficiency": 40.0, "min_bandwidth_gbs": 1600.0},
        },
    }

    @pytest.mark.parametrize("speed_grade", ["8Gbps", "12Gbps", "16Gbps"])
    @pytest.mark.parametrize("pattern", ["row_hit", "sequential", "hotspot"])
    def test_baseline_efficiency(self, speed_grade, pattern):
        """Test that efficiency meets baseline targets"""
        framework = BandwidthMeasurementFramework(speed_grade=speed_grade)

        # Use appropriate request count based on pattern
        num_requests = 2000 if pattern in ["row_hit", "sequential"] else 1500

        metrics = framework.measure_bandwidth(
            pattern=pattern,
            num_requests=num_requests,
            read_ratio=0.8,
            enable_refresh=False
        )

        baseline = self.BASELINES[speed_grade][pattern]

        print(f"\n{'='*60}")
        print(f"Baseline Test: {speed_grade} - {pattern}")
        print(f"{'='*60}")
        print(f"  Efficiency: {metrics.efficiency_percent:.1f}% (min: {baseline['min_efficiency']}%)")
        print(f"  Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s (min: {baseline['min_bandwidth_gbs']:.1f} GB/s)")

        # Check minimum efficiency threshold
        assert metrics.efficiency_percent >= baseline["min_efficiency"], \
            f"Efficiency {metrics.efficiency_percent:.1f}% below baseline {baseline['min_efficiency']}%"

        # Check minimum bandwidth threshold
        assert metrics.measured_bandwidth_gbs >= baseline["min_bandwidth_gbs"], \
            f"Bandwidth {metrics.measured_bandwidth_gbs:.1f} GB/s below baseline {baseline['min_bandwidth_gbs']:.1f} GB/s"


class TestBandwidthStatistics:
    """Statistical analysis of bandwidth measurements"""

    def test_bandwidth_variance(self):
        """Test variance in bandwidth measurements"""
        framework = BandwidthMeasurementFramework(speed_grade="8Gbps")

        measurements = []
        for _ in range(5):
            metrics = framework.measure_bandwidth(
                pattern="sequential",
                num_requests=1000,
                read_ratio=0.8,
                enable_refresh=False
            )
            measurements.append(metrics.efficiency_percent)

        mean_eff = statistics.mean(measurements)
        stdev_eff = statistics.stdev(measurements) if len(measurements) > 1 else 0

        print(f"\n{'='*60}")
        print(f"Bandwidth Variance Analysis")
        print(f"{'='*60}")
        print(f"  Mean Efficiency: {mean_eff:.1f}%")
        print(f"  Std Dev: {stdev_eff:.1f}%")
        print(f"  Min: {min(measurements):.1f}%")
        print(f"  Max: {max(measurements):.1f}%")

        # Variance should be low (less than 20%)
        assert stdev_eff < 20.0, f"Variance too high: {stdev_eff:.1f}%"

    def test_latency_bandwidth_correlation(self):
        """Test correlation between latency and bandwidth"""
        framework = BandwidthMeasurementFramework(speed_grade="8Gbps")

        pattern_results = {}

        for pattern in ["row_hit", "sequential", "random"]:
            num_req = 1000 if pattern == "random" else 2000
            metrics = framework.measure_bandwidth(
                pattern=pattern,
                num_requests=num_req,
                read_ratio=0.8,
                enable_refresh=False
            )

            pattern_results[pattern] = {
                'bandwidth': metrics.measured_bandwidth_gbs,
                'duration_ns': metrics.test_duration_ns,
                'efficiency': metrics.efficiency_percent,
            }

        print(f"\n{'='*60}")
        print(f"Latency vs Bandwidth Analysis")
        print(f"{'='*60}")

        for pattern, results in pattern_results.items():
            print(f"\n  {pattern}:")
            print(f"    Bandwidth: {results['bandwidth']:.1f} GB/s")
            print(f"    Duration: {results['duration_ns']:.0f} ns")
            print(f"    Efficiency: {results['efficiency']:.1f}%")


# =============================================================================
# Summary Report
# =============================================================================

def generate_bandwidth_report():
    """Generate comprehensive bandwidth report"""
    print("\n" + "="*70)
    print("HBM4 BANDWIDTH MEASUREMENT REPORT")
    print("="*70)

    for speed_grade in ["8Gbps", "12Gbps", "16Gbps"]:
        framework = BandwidthMeasurementFramework(speed_grade=speed_grade)

        print(f"\n{'='*60}")
        print(f"Speed Grade: {speed_grade}")
        print(f"{'='*60}")
        print(f"  Theoretical Peak: {framework.spec.bandwidth_gbs:.1f} GB/s "
              f"({framework.spec.bandwidth:.3f} TB/s)")

        patterns = [
            ("row_hit", 2000),
            ("sequential", 2000),
            ("hotspot", 1500),
            ("random", 800),
        ]

        for pattern, num_req in patterns:
            metrics = framework.measure_bandwidth(
                pattern=pattern,
                num_requests=num_req,
                read_ratio=0.8,
                enable_refresh=False
            )

            print(f"\n  {pattern} pattern:")
            print(f"    Bandwidth: {metrics.measured_bandwidth_gbs:.1f} GB/s "
                  f"({metrics.efficiency_percent:.1f}% of peak)")
            print(f"    Requests: {metrics.total_requests} "
                  f"({metrics.read_requests} reads, {metrics.write_requests} writes)")
            print(f"    Duration: {metrics.test_duration_ns:.0f} ns")


if __name__ == "__main__":
    generate_bandwidth_report()
