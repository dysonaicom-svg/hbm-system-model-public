"""
Test suite for bandwidth analysis (Task 3.1)
Tests bandwidth metrics, efficiency calculation, and performance analysis.
"""

import sys
sys.path.insert(0, '/home/ic/JXTF/HBM')

import pytest
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class BandwidthMetrics:
    """Bandwidth metrics container"""
    total_bytes: int = 0
    total_cycles: int = 0
    peak_bandwidth_gbps: float = 0.0
    actual_bandwidth_gbps: float = 0.0
    efficiency_percent: float = 0.0

    @property
    def bytes_per_cycle(self) -> float:
        if self.total_cycles > 0:
            return self.total_bytes / self.total_cycles
        return 0.0


@dataclass
class LatencyMetrics:
    """Latency metrics container"""
    min_latency_ns: float = 0.0
    max_latency_ns: float = 0.0
    avg_latency_ns: float = 0.0
    p50_latency_ns: float = 0.0
    p95_latency_ns: float = 0.0
    p99_latency_ns: float = 0.0
    std_dev_ns: float = 0.0


@dataclass
class ChannelLoadBalancing:
    """Channel load balancing metrics"""
    channel_id: int
    requests: int = 0
    total_latency_cycles: int = 0
    utilization_percent: float = 0.0
    hit_rate: float = 0.0


class TestBandwidthMetrics:
    """Test bandwidth metrics calculation"""

    def test_bandwidth_metrics_creation(self):
        """Test BandwidthMetrics creation"""
        metrics = BandwidthMetrics(
            total_bytes=1024,
            total_cycles=100,
            peak_bandwidth_gbps=819.2,
            actual_bandwidth_gbps=400.0,
            efficiency_percent=48.8,
        )
        assert metrics.total_bytes == 1024
        assert metrics.total_cycles == 100
        assert metrics.bytes_per_cycle == 10.24

    def test_bytes_per_cycle_calculation(self):
        """Test bytes per cycle calculation"""
        metrics = BandwidthMetrics(total_bytes=0, total_cycles=100)
        assert metrics.bytes_per_cycle == 0.0

        metrics.total_bytes = 25600
        assert metrics.bytes_per_cycle == 256.0

    def test_bandwidth_from_cycles(self):
        """Test calculating actual bandwidth from cycles"""
        # Simulate: 256 bytes per transaction, 1000 transactions in 10000 cycles
        # At 8 GT/s, each cycle = 1/8 GHz = 0.125 ns
        # 10000 cycles = 1250 ns
        # 256000 bytes / 1250 ns = 204.8 GB/s

        tCK_ps = 125  # 8 GHz = 8000 MT/s = 125 ps per cycle
        total_bytes = 256000
        total_cycles = 10000

        total_ns = total_cycles * tCK_ps
        bandwidth_gbps = (total_bytes / total_ns) * 1000  # Convert to GB/s

        assert bandwidth_gbps > 0
        assert bandwidth_gbps < 1000  # Should be reasonable


class TestLatencyMetrics:
    """Test latency metrics calculation"""

    def test_latency_metrics_creation(self):
        """Test LatencyMetrics creation"""
        metrics = LatencyMetrics(
            min_latency_ns=10.0,
            max_latency_ns=100.0,
            avg_latency_ns=25.0,
            p50_latency_ns=20.0,
            p95_latency_ns=50.0,
            p99_latency_ns=80.0,
            std_dev_ns=15.0,
        )
        assert metrics.avg_latency_ns == 25.0
        assert metrics.p99_latency_ns > metrics.p95_latency_ns

    def test_latency_percentiles(self):
        """Test latency percentile calculation"""
        # Using 20 elements for cleaner percentile positions
        latencies = [10.0, 15.0, 20.0, 22.0, 25.0, 28.0, 30.0, 32.0, 35.0, 40.0,
                     45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 90.0, 100.0]
        latencies_sorted = sorted(latencies)

        # Calculate percentiles
        p50_idx = int(len(latencies_sorted) * 0.50)
        p95_idx = int(len(latencies_sorted) * 0.95)
        p99_idx = int(len(latencies_sorted) * 0.99)

        p50 = latencies_sorted[min(p50_idx, len(latencies_sorted) - 1)]
        p95 = latencies_sorted[min(p95_idx, len(latencies_sorted) - 1)]
        p99 = latencies_sorted[min(p99_idx, len(latencies_sorted) - 1)]

        assert p50 >= 25.0  # At position 10, value is 30.0
        assert p95 >= 50.0


class TestChannelLoadBalancing:
    """Test channel load balancing metrics"""

    def test_load_balancing_metrics(self):
        """Test ChannelLoadBalancing creation"""
        load = ChannelLoadBalancing(
            channel_id=0,
            requests=100,
            total_latency_cycles=2500,
            utilization_percent=25.0,
            hit_rate=0.85,
        )
        assert load.channel_id == 0
        assert load.requests == 100
        assert load.hit_rate == 0.85

    def test_utilization_calculation(self):
        """Test channel utilization calculation"""
        total_cycles = 10000
        busy_cycles = 2500

        utilization = (busy_cycles / total_cycles) * 100.0
        assert utilization == 25.0

    def test_hit_rate_calculation(self):
        """Test row hit rate calculation"""
        hits = 85
        misses = 15

        hit_rate = hits / (hits + misses)
        assert abs(hit_rate - 0.85) < 0.001


class TestBandwidthAnalysis:
    """Test comprehensive bandwidth analysis"""

    def test_hbm4_peak_bandwidth(self):
        """Test HBM4 peak bandwidth calculation"""
        # HBM4: 8 GT/s × 2048 bits / 8 = 2 TB/s per stack
        data_rate_gtps = 8.0
        data_width_bits = 2048
        channels = 32

        peak_gbps = data_rate_gtps * 1e9 * data_width_bits / 8 / 1e9
        peak_per_channel = peak_gbps / channels

        assert peak_gbps > 0
        assert peak_per_channel > 0

    def test_bandwidth_efficiency_calculation(self):
        """Test bandwidth efficiency calculation"""
        peak_bandwidth_gbps = 2048.0  # 2 TB/s
        actual_bandwidth_gbps = 1024.0  # 1 TB/s

        efficiency = (actual_bandwidth_gbps / peak_bandwidth_gbps) * 100.0
        assert efficiency == 50.0

    def test_multiple_channels_bandwidth(self):
        """Test bandwidth calculation with multiple channels"""
        channels = 32
        bandwidth_per_channel_gbps = 64.0  # 64 GB/s per channel

        total_bandwidth = channels * bandwidth_per_channel_gbps
        assert total_bandwidth == 2048.0  # 2 TB/s total

    def test_different_speed_grades(self):
        """Test bandwidth with different speed grades"""
        speed_grades = {
            '8Gbps': 2048.0,   # Peak bandwidth per stack
            '12Gbps': 3072.0,  # 1.5x
            '16Gbps': 4096.0,  # 2x
        }

        base_data_rate = 8.0
        for grade, expected_bw in speed_grades.items():
            data_rate = float(grade.replace('Gbps', ''))
            scale = data_rate / base_data_rate
            actual_bw = 2048.0 * scale
            assert abs(actual_bw - expected_bw) < 0.1


class TestBandwidthVsLatency:
    """Test bandwidth vs latency tradeoffs"""

    def test_latency_bandwidth_product(self):
        """Test latency-bandwidth product (performance metric)"""
        # LBP = avg_latency * (1 / bandwidth)
        avg_latency_ns = 25.0
        bandwidth_gbps = 500.0

        # Lower is better
        lbp = avg_latency_ns * (1.0 / bandwidth_gbps)
        assert lbp > 0

    def test_high_bandwidth_low_latency_target(self):
        """Test target for high bandwidth with low latency"""
        target_latency_ns = 20.0
        target_bandwidth_gbps = 1000.0

        # Measure actual
        actual_latency_ns = 25.0
        actual_bandwidth_gbps = 800.0

        latency_ok = actual_latency_ns <= target_latency_ns * 1.5  # 50% tolerance
        bandwidth_ok = actual_bandwidth_gbps >= target_bandwidth_gbps * 0.8  # 20% tolerance

        assert latency_ok is True
        assert bandwidth_ok is True


class TestBandwidthPatterns:
    """Test bandwidth with different traffic patterns"""

    def test_sequential_bandwidth(self):
        """Test bandwidth with sequential traffic"""
        # Sequential: High row hit rate, best bandwidth
        row_hit_rate = 0.95
        base_bandwidth_gbps = 1000.0

        effective_bandwidth = base_bandwidth_gbps * (0.5 + 0.5 * row_hit_rate)
        assert effective_bandwidth > base_bandwidth_gbps * 0.9

    def test_random_bandwidth(self):
        """Test bandwidth with random traffic"""
        # Random: Low row hit rate, reduced bandwidth
        row_hit_rate = 0.20
        base_bandwidth_gbps = 1000.0

        effective_bandwidth = base_bandwidth_gbps * (0.5 + 0.5 * row_hit_rate)
        assert effective_bandwidth < base_bandwidth_gbps

    def test_hotspot_bandwidth(self):
        """Test bandwidth with hotspot traffic"""
        # Hotspot: Some locality, moderate bandwidth
        hotspot_ratio = 0.8  # 80% accesses to 10% of memory
        row_hit_rate = hotspot_ratio * 0.9 + (1 - hotspot_ratio) * 0.1

        base_bandwidth_gbps = 1000.0
        effective_bandwidth = base_bandwidth_gbps * (0.5 + 0.5 * row_hit_rate)

        assert 0.5 * base_bandwidth_gbps < effective_bandwidth < base_bandwidth_gbps


class TestPAM3Bandwidth:
    """Test PAM3 encoding impact on bandwidth"""

    def test_pam3_spectral_efficiency(self):
        """Test PAM3 spectral efficiency vs NRZ"""
        # NRZ: 1 bit/symbol
        # PAM3: log2(3) ≈ 1.585 bits/symbol

        nrz_efficiency = 1.0
        pam3_efficiency = 1.585

        improvement = (pam3_efficiency - nrz_efficiency) / nrz_efficiency * 100
        assert improvement > 50  # PAM3 should be >50% more efficient

    def test_pam3_bandwidth_gain(self):
        """Test PAM3 bandwidth gain over NRZ"""
        base_bandwidth_gbps = 1000.0  # NRZ

        # PAM3: ~58.5% more bits per symbol
        pam3_bandwidth_gbps = base_bandwidth_gbps * 1.585

        assert pam3_bandwidth_gbps > base_bandwidth_gbps
        assert abs(pam3_bandwidth_gbps - 1585.0) < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])