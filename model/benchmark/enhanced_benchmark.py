"""
Enhanced Benchmark Module

Comprehensive HBM4 performance benchmarks covering:
1. Multi-channel parallel access - 32 channels simultaneous access
2. Mixed traffic patterns - Read/write mixing
3. Bank group conflict testing - Bank group switching overhead
4. Refresh impact testing - Performance loss during refresh
5. QoS impact testing - Priority effects on latency

Based on:
- JEDEC JESD270-4A HBM4 specification
- Multi-agent research findings (2026-06-15)
"""

import random
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import statistics

from model.dram.hbm4_spec import HBM4Spec, HBM4_SPEED_GRADES
from model.dram.timing import get_timing_for_speed_grade
from model.controller.hbm4_controller import HBM4Controller
from model.controller.request import HBMRequest, HBMResponse
from .benchmark_config import BandwidthConfig, TestPattern


_logger = logging.getLogger(__name__)

@dataclass
class MultiChannelResult:
    """Results from multi-channel parallel access test"""
    # Channel metrics
    num_channels: int = 32
    channels_active: int = 0

    # Bandwidth metrics
    peak_bandwidth_gbs: float = 0.0
    measured_bandwidth_gbs: float = 0.0
    channel_bandwidth_gbs: Dict[int, float] = field(default_factory=dict)

    # Efficiency
    channel_utilization_percent: float = 0.0
    bandwidth_efficiency_percent: float = 0.0

    # Timing
    test_duration_ns: float = 0.0
    total_requests: int = 0

    # Per-channel breakdown
    per_channel_requests: Dict[int, int] = field(default_factory=dict)
    per_channel_latency_avg: Dict[int, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'num_channels': self.num_channels,
            'channels_active': self.channels_active,
            'peak_bandwidth_gbs': self.peak_bandwidth_gbs,
            'measured_bandwidth_gbs': self.measured_bandwidth_gbs,
            'channel_utilization_percent': self.channel_utilization_percent,
            'bandwidth_efficiency_percent': self.bandwidth_efficiency_percent,
            'test_duration_ns': self.test_duration_ns,
            'total_requests': self.total_requests,
        }

    def __str__(self) -> str:
        return (
            f"Multi-Channel Results:\n"
            f"  Channels Active: {self.channels_active}/{self.num_channels}\n"
            f"  Peak BW: {self.peak_bandwidth_gbs:.1f} GB/s\n"
            f"  Measured BW: {self.measured_bandwidth_gbs:.1f} GB/s\n"
            f"  Efficiency: {self.bandwidth_efficiency_percent:.1f}%\n"
            f"  Channel Utilization: {self.channel_utilization_percent:.1f}%"
        )


@dataclass
class MixedTrafficResult:
    """Results from mixed read/write traffic test"""
    # Traffic mix
    read_ratio: float = 0.5
    write_ratio: float = 0.5

    # Bandwidth metrics
    read_bandwidth_gbs: float = 0.0
    write_bandwidth_gbs: float = 0.0
    total_bandwidth_gbs: float = 0.0

    # Latency metrics
    read_latency_avg_ns: float = 0.0
    write_latency_avg_ns: float = 0.0
    read_latency_p99_ns: float = 0.0
    write_latency_p99_ns: float = 0.0

    # Turnaround overhead
    read_write_turnaround_ns: float = 0.0
    turnaround_count: int = 0

    # Efficiency
    bandwidth_efficiency_percent: float = 0.0

    # Request counts
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0

    # Timing
    test_duration_ns: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'read_ratio': self.read_ratio,
            'write_ratio': self.write_ratio,
            'read_bandwidth_gbs': self.read_bandwidth_gbs,
            'write_bandwidth_gbs': self.write_bandwidth_gbs,
            'total_bandwidth_gbs': self.total_bandwidth_gbs,
            'read_latency_avg_ns': self.read_latency_avg_ns,
            'write_latency_avg_ns': self.write_latency_avg_ns,
            'bandwidth_efficiency_percent': self.bandwidth_efficiency_percent,
            'total_requests': self.total_requests,
            'test_duration_ns': self.test_duration_ns,
        }

    def __str__(self) -> str:
        return (
            f"Mixed Traffic Results:\n"
            f"  Read/Write Ratio: {self.read_ratio:.0%}/{self.write_ratio:.0%}\n"
            f"  Read BW: {self.read_bandwidth_gbs:.1f} GB/s\n"
            f"  Write BW: {self.write_bandwidth_gbs:.1f} GB/s\n"
            f"  Total BW: {self.total_bandwidth_gbs:.1f} GB/s\n"
            f"  Read Latency: {self.read_latency_avg_ns:.1f} ns (P99: {self.read_latency_p99_ns:.1f})\n"
            f"  Write Latency: {self.write_latency_avg_ns:.1f} ns (P99: {self.write_latency_p99_ns:.1f})\n"
            f"  Efficiency: {self.bandwidth_efficiency_percent:.1f}%"
        )


@dataclass
class BankGroupConflictResult:
    """Results from bank group conflict test"""
    # Conflict metrics
    same_bank_group_requests: int = 0
    different_bank_group_requests: int = 0
    bank_group_conflicts: int = 0

    # Latency metrics
    same_bg_latency_avg_ns: float = 0.0
    different_bg_latency_avg_ns: float = 0.0
    latency_penalty_ns: float = 0.0  # Extra latency for different BG

    # Timing penalties (in cycles)
    nCCDS_cycles: int = 2  # Same BG column delay
    nCCDL_cycles: int = 3  # Different BG column delay
    nRRDS_cycles: int = 3  # Same BG row delay
    nRRDL_cycles: int = 4  # Different BG row delay

    # Conflict rate
    conflict_rate_percent: float = 0.0

    # Efficiency
    bank_group_efficiency_percent: float = 0.0

    # Request counts
    total_requests: int = 0

    # Timing
    test_duration_ns: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'same_bg_latency_avg_ns': self.same_bg_latency_avg_ns,
            'different_bg_latency_avg_ns': self.different_bg_latency_avg_ns,
            'latency_penalty_ns': self.latency_penalty_ns,
            'conflict_rate_percent': self.conflict_rate_percent,
            'bank_group_efficiency_percent': self.bank_group_efficiency_percent,
            'total_requests': self.total_requests,
            'test_duration_ns': self.test_duration_ns,
        }

    def __str__(self) -> str:
        return (
            f"Bank Group Conflict Results:\n"
            f"  Same BG Latency: {self.same_bg_latency_avg_ns:.1f} ns\n"
            f"  Different BG Latency: {self.different_bg_latency_avg_ns:.1f} ns\n"
            f"  Latency Penalty: {self.latency_penalty_ns:.1f} ns\n"
            f"  Conflict Rate: {self.conflict_rate_percent:.1f}%\n"
            f"  BG Efficiency: {self.bank_group_efficiency_percent:.1f}%"
        )


@dataclass
class RefreshImpactResult:
    """Results from refresh impact test"""
    # Refresh configuration
    refresh_interval_ns: float = 3.9e6  # tREFI = 3.9us
    refresh_duration_ns: float = 180.0  # tRFC = 180ns

    # Refresh metrics
    refresh_count: int = 0
    refresh_total_time_ns: float = 0.0
    refresh_coverage_percent: float = 0.0

    # Bandwidth metrics
    bandwidth_without_refresh_gbs: float = 0.0
    bandwidth_with_refresh_gbs: float = 0.0
    bandwidth_loss_percent: float = 0.0

    # Latency impact
    latency_during_refresh_ns: float = 0.0
    latency_outside_refresh_ns: float = 0.0
    latency_increase_percent: float = 0.0

    # Efficiency
    refresh_efficiency_percent: float = 0.0
    effective_bandwidth_gbs: float = 0.0

    # Request counts
    requests_during_refresh: int = 0
    requests_outside_refresh: int = 0

    # Timing
    test_duration_ns: float = 0.0
    idle_time_during_refresh_ns: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'refresh_interval_ns': self.refresh_interval_ns,
            'refresh_duration_ns': self.refresh_duration_ns,
            'refresh_count': self.refresh_count,
            'bandwidth_loss_percent': self.bandwidth_loss_percent,
            'latency_increase_percent': self.latency_increase_percent,
            'effective_bandwidth_gbs': self.effective_bandwidth_gbs,
            'test_duration_ns': self.test_duration_ns,
        }

    def __str__(self) -> str:
        return (
            f"Refresh Impact Results:\n"
            f"  Refresh Count: {self.refresh_count}\n"
            f"  Total Refresh Time: {self.refresh_total_time_ns:.1f} ns\n"
            f"  Bandwidth Loss: {self.bandwidth_loss_percent:.2f}%\n"
            f"  Latency Increase: {self.latency_increase_percent:.1f}%\n"
            f"  Effective BW: {self.effective_bandwidth_gbs:.1f} GB/s"
        )


@dataclass
class QoSImpactResult:
    """Results from QoS impact test"""
    # QoS configuration
    num_qos_levels: int = 16

    # Per-level metrics
    qos_level_latency_avg: Dict[int, float] = field(default_factory=dict)
    qos_level_latency_p99: Dict[int, float] = field(default_factory=dict)
    qos_level_throughput: Dict[int, float] = field(default_factory=dict)
    qos_level_requests: Dict[int, int] = field(default_factory=dict)

    # Priority metrics
    critical_latency_ns: float = 0.0      # QoS 0-3
    high_latency_ns: float = 0.0           # QoS 4-7
    normal_latency_ns: float = 0.0         # QoS 8-11
    low_latency_ns: float = 0.0            # QoS 12-15

    critical_throughput: float = 0.0
    high_throughput: float = 0.0
    normal_throughput: float = 0.0
    low_throughput: float = 0.0

    # Latency ratios
    critical_to_normal_ratio: float = 0.0
    critical_to_low_ratio: float = 0.0

    # QoS effectiveness
    qos_effectiveness_percent: float = 0.0
    starvation_detected: bool = False
    priority_inversion_count: int = 0

    # Congestion impact
    latency_under_load_ns: float = 0.0
    latency_under_light_load_ns: float = 0.0
    load_factor_percent: float = 0.0

    # Total
    total_requests: int = 0

    # Timing
    test_duration_ns: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'num_qos_levels': self.num_qos_levels,
            'critical_latency_ns': self.critical_latency_ns,
            'normal_latency_ns': self.normal_latency_ns,
            'low_latency_ns': self.low_latency_ns,
            'critical_to_normal_ratio': self.critical_to_normal_ratio,
            'qos_effectiveness_percent': self.qos_effectiveness_percent,
            'total_requests': self.total_requests,
            'test_duration_ns': self.test_duration_ns,
        }

    def __str__(self) -> str:
        return (
            f"QoS Impact Results:\n"
            f"  Critical Latency: {self.critical_latency_ns:.1f} ns\n"
            f"  High Latency: {self.high_latency_ns:.1f} ns\n"
            f"  Normal Latency: {self.normal_latency_ns:.1f} ns\n"
            f"  Low Latency: {self.low_latency_ns:.1f} ns\n"
            f"  Critical/Normal Ratio: {self.critical_to_normal_ratio:.2f}x\n"
            f"  QoS Effectiveness: {self.qos_effectiveness_percent:.1f}%\n"
            f"  Starvation: {'Yes' if self.starvation_detected else 'No'}"
        )


@dataclass
class EnhancedBenchmarkReport:
    """Complete enhanced benchmark report"""
    # Individual test results
    multi_channel: Optional[MultiChannelResult] = None
    mixed_traffic: Optional[MixedTrafficResult] = None
    bank_group_conflict: Optional[BankGroupConflictResult] = None
    refresh_impact: Optional[RefreshImpactResult] = None
    qos_impact: Optional[QoSImpactResult] = None

    # Summary metrics
    total_bandwidth_gbs: float = 0.0
    average_latency_ns: float = 0.0
    peak_efficiency_percent: float = 0.0

    # Key findings
    findings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Metadata
    timestamp: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'duration_seconds': self.duration_seconds,
            'total_bandwidth_gbs': self.total_bandwidth_gbs,
            'average_latency_ns': self.average_latency_ns,
            'peak_efficiency_percent': self.peak_efficiency_percent,
            'findings': self.findings,
            'warnings': self.warnings,
            'multi_channel': self.multi_channel.to_dict() if self.multi_channel else None,
            'mixed_traffic': self.mixed_traffic.to_dict() if self.mixed_traffic else None,
            'bank_group_conflict': self.bank_group_conflict.to_dict() if self.bank_group_conflict else None,
            'refresh_impact': self.refresh_impact.to_dict() if self.refresh_impact else None,
            'qos_impact': self.qos_impact.to_dict() if self.qos_impact else None,
        }


# =============================================================================
# Enhanced Benchmark Classes
# =============================================================================

class EnhancedBenchmark:
    """Enhanced HBM4 performance benchmarking suite"""

    def __init__(
        self,
        speed_grade: str = "8Gbps",
        random_seed: int = 42
    ):
        """Initialize enhanced benchmark

        Args:
            speed_grade: HBM speed grade ("8Gbps", "12Gbps", "16Gbps")
            random_seed: Random seed for reproducibility
        """
        self.speed_grade = speed_grade
        self.random_seed = random_seed

        # Create HBM4 specification
        self.spec = self._create_spec()
        self.timing = get_timing_for_speed_grade(speed_grade)

        # Results
        self.results: Dict[str, any] = {}

    def _create_spec(self) -> HBM4Spec:
        """Create HBM4 specification"""
        if self.speed_grade not in HBM4_SPEED_GRADES:
            raise ValueError(f"Unknown speed grade: {self.speed_grade}")

        grade_params = HBM4_SPEED_GRADES[self.speed_grade]
        return HBM4Spec(
            data_rate_gtps=grade_params["data_rate_gtps"],
            tCK_ps=grade_params["tCK_ps"]
        )

    def _generate_addresses_for_channel(
        self,
        channel: int,
        count: int,
        pattern: TestPattern = TestPattern.SEQUENTIAL
    ) -> List[int]:
        """Generate addresses targeting a specific channel"""
        random.seed(self.random_seed)

        addresses = []
        base_addr = 0

        # Set channel bits in address
        addr = (channel & 0x1F) << 0  # 5-bit channel field at bit 0

        for i in range(count):
            if pattern == TestPattern.SEQUENTIAL:
                addr = ((channel & 0x1F) << 0) | ((i * 64) & 0xFFFF)
            elif pattern == TestPattern.RANDOM:
                addr = ((channel & 0x1F) << 0) | (random.randint(0, 0xFFFF) << 6)
            elif pattern == TestPattern.ROW_HIT:
                addr = ((channel & 0x1F) << 0) | 0x1000  # Same row
            else:
                addr = ((channel & 0x1F) << 0) | (i * 64)

            addresses.append(addr & 0xFFFFFFFF)

        return addresses

    def run_multi_channel_test(
        self,
        num_requests_per_channel: int = 1000,
        pattern: TestPattern = TestPattern.SEQUENTIAL
    ) -> MultiChannelResult:
        """Test multi-channel parallel access

        Simulates 32 channels simultaneously accessing memory.

        Args:
            num_requests_per_channel: Requests per channel
            pattern: Address pattern

        Returns:
            MultiChannelResult with per-channel metrics
        """
        _logger.info(f"Running multi-channel test ({num_requests_per_channel} req/channel)...")

        random.seed(self.random_seed)

        # Create controller
        controller = HBM4Controller(
            spec=self.spec,
            enable_qos=False,
            enable_refresh=False
        )

        sim_start = controller.current_time_ns
        request_map: Dict[str, Tuple[int, int, int]] = {}  # id -> (channel, submit_time, is_read)
        channel_requests: Dict[int, int] = defaultdict(int)
        channel_latencies: Dict[int, List[float]] = defaultdict(list)
        total_requests = 0

        # Submit requests to all channels simultaneously
        for channel in range(32):
            addresses = self._generate_addresses_for_channel(
                channel, num_requests_per_channel, pattern
            )

            for addr in addresses:
                request_id = controller.submit_request(
                    addr=addr,
                    is_read=True,
                    size_bytes=64
                )

                if request_id:
                    request_map[request_id] = (channel, controller.current_time_ns, True)
                    channel_requests[channel] += 1
                    total_requests += 1

        # Process all requests
        bytes_transferred = 0
        while request_map:
            responses = controller.tick()

            for resp in responses:
                if resp.request_id in request_map:
                    channel, submit_time, is_read = request_map[resp.request_id]
                    latency = controller.current_time_ns - submit_time

                    channel_latencies[channel].append(latency)
                    bytes_transferred += 64

                    del request_map[resp.request_id]

        sim_end = controller.current_time_ns
        elapsed_ns = sim_end - sim_start

        # Calculate results
        result = MultiChannelResult()
        result.num_channels = 32
        result.channels_active = len([ch for ch, count in channel_requests.items() if count > 0])
        result.total_requests = total_requests

        # Peak per-channel bandwidth: 2048 bits/transfer * 8 GT/s / 8 = 2048 GB/s per 32 channels = 64 GB/s per channel
        peak_per_channel_gbs = self.spec.bandwidth_gbs / 32
        result.peak_bandwidth_gbs = peak_per_channel_gbs * result.channels_active

        # Calculate effective bandwidth based on transaction completion rate
        # Each request = 64 bytes (1 FLINE)
        # Bandwidth = requests * 64 bytes / elapsed time
        if elapsed_ns > 0:
            # Convert: bytes/ns to GB/s (1 GB = 1e9 bytes, 1s = 1e9 ns)
            result.measured_bandwidth_gbs = (bytes_transferred / elapsed_ns)
        else:
            result.measured_bandwidth_gbs = 0

        # Efficiency relative to per-channel peak
        if result.peak_bandwidth_gbs > 0:
            result.bandwidth_efficiency_percent = min(100, result.measured_bandwidth_gbs / result.peak_bandwidth_gbs * 100)
        else:
            result.bandwidth_efficiency_percent = 0

        result.channel_utilization_percent = (result.channels_active / 32 * 100)
        result.test_duration_ns = elapsed_ns
        result.per_channel_requests = dict(channel_requests)

        # Per-channel average latency
        for ch, latencies in channel_latencies.items():
            if latencies:
                result.per_channel_latency_avg[ch] = statistics.mean(latencies)
        result.test_duration_ns = elapsed_ns
        result.total_requests = sum(channel_requests.values())
        result.per_channel_requests = dict(channel_requests)

        # Per-channel average latency
        for ch, latencies in channel_latencies.items():
            if latencies:
                result.per_channel_latency_avg[ch] = statistics.mean(latencies)

        _logger.info(f"Multi-channel test complete: {result.measured_bandwidth_gbs:.1f} GB/s "
                    f"({result.bandwidth_efficiency_percent:.1f}% efficiency)")

        self.results['multi_channel'] = result
        return result

    def run_mixed_traffic_test(
        self,
        read_ratio: float = 0.7,
        num_requests: int = 10000,
        pattern: TestPattern = TestPattern.RANDOM
    ) -> MixedTrafficResult:
        """Test mixed read/write traffic

        Measures bandwidth and latency for mixed read/write workloads.

        Args:
            read_ratio: Ratio of read requests (0.0-1.0)
            num_requests: Total number of requests
            pattern: Address pattern

        Returns:
            MixedTrafficResult with read/write metrics
        """
        _logger.info(f"Running mixed traffic test (read={read_ratio:.0%}, {num_requests} req)...")

        random.seed(self.random_seed)

        # Create controller
        controller = HBM4Controller(
            spec=self.spec,
            enable_qos=False,
            enable_refresh=False
        )

        sim_start = controller.current_time_ns

        # Generate addresses
        addresses = []
        for i in range(num_requests):
            addr = (random.randint(0, 31) << 0) | ((i * 64) & 0xFFFF)
            addresses.append(addr)

        # Submit requests with mixed read/write
        request_map: Dict[str, Tuple[bool, int]] = {}  # id -> (is_read, submit_time)
        read_latencies = []
        write_latencies = []
        read_bytes = 0
        write_bytes = 0

        for i, addr in enumerate(addresses):
            is_read = random.random() < read_ratio

            request_id = controller.submit_request(
                addr=addr,
                is_read=is_read,
                size_bytes=64
            )

            if request_id:
                request_map[request_id] = (is_read, controller.current_time_ns)

        # Process and measure turnaround
        last_type = None
        turnaround_times = []
        turnaround_count = 0

        while request_map:
            responses = controller.tick()

            for resp in responses:
                if resp.request_id in request_map:
                    is_read, submit_time = request_map[resp.request_id]
                    latency = controller.current_time_ns - submit_time

                    if is_read:
                        read_latencies.append(latency)
                        read_bytes += 64
                    else:
                        write_latencies.append(latency)
                        write_bytes += 64

                    # Track read/write turnarounds
                    if last_type is not None and last_type != is_read:
                        turnaround_count += 1
                    last_type = is_read

                    del request_map[resp.request_id]

        sim_end = controller.current_time_ns
        elapsed_ns = sim_end - sim_start

        # Calculate results
        result = MixedTrafficResult()
        result.read_ratio = read_ratio
        result.write_ratio = 1.0 - read_ratio

        result.read_requests = len(read_latencies)
        result.write_requests = len(write_latencies)
        result.total_requests = result.read_requests + result.write_requests

        # Calculate effective bandwidth based on completed transactions
        # Each request = 64 bytes
        if elapsed_ns > 0:
            result.read_bandwidth_gbs = (read_bytes / elapsed_ns)
            result.write_bandwidth_gbs = (write_bytes / elapsed_ns)
            result.total_bandwidth_gbs = result.read_bandwidth_gbs + result.write_bandwidth_gbs
        else:
            result.read_bandwidth_gbs = 0
            result.write_bandwidth_gbs = 0
            result.total_bandwidth_gbs = 0

        if read_latencies:
            result.read_latency_avg_ns = statistics.mean(read_latencies)
            result.read_latency_p99_ns = self._percentile(read_latencies, 99)

        if write_latencies:
            result.write_latency_avg_ns = statistics.mean(write_latencies)
            result.write_latency_p99_ns = self._percentile(write_latencies, 99)

        result.turnaround_count = turnaround_count

        # Efficiency is actual vs theoretical peak (per-channel)
        peak_per_channel = self.spec.bandwidth_gbs / 32
        if peak_per_channel > 0:
            result.bandwidth_efficiency_percent = min(100, result.total_bandwidth_gbs / peak_per_channel * 100)
        else:
            result.bandwidth_efficiency_percent = 0
        result.test_duration_ns = elapsed_ns

        _logger.info(f"Mixed traffic test complete: {result.total_bandwidth_gbs:.1f} GB/s "
                    f"(R: {result.read_bandwidth_gbs:.1f}, W: {result.write_bandwidth_gbs:.1f})")

        self.results['mixed_traffic'] = result
        return result

    def run_bank_group_conflict_test(
        self,
        num_requests: int = 10000
    ) -> BankGroupConflictResult:
        """Test bank group conflict impact

        Measures latency difference between same and different bank group accesses.

        Args:
            num_requests: Number of requests to test

        Returns:
            BankGroupConflictResult with conflict metrics
        """
        _logger.info(f"Running bank group conflict test ({num_requests} req)...")

        random.seed(self.random_seed)

        # Create controller
        controller = HBM4Controller(
            spec=self.spec,
            enable_qos=False,
            enable_refresh=False
        )

        sim_start = controller.current_time_ns

        # Generate addresses with controlled bank group patterns
        # Bank group bits are at bits 6-8 (3 bits = 8 BG)
        bg_size = 64 * 64  # 64 columns * 64 rows per BG
        request_map: Dict[str, Tuple[bool, int]] = {}  # id -> (same_bg, submit_time)
        same_bg_latencies = []
        different_bg_latencies = []

        # Generate interleaved bank group access pattern
        current_bg = 0
        for i in range(num_requests):
            # Alternate between same BG and different BG
            if i % 2 == 0:
                # Same BG access
                bg = current_bg
                same_bg = True
            else:
                # Different BG access
                bg = (current_bg + 1) % 8
                same_bg = False
                current_bg = bg

            # Construct address with bank group bits
            addr = (bg << 6) | ((i * 64) & 0x3F)

            request_id = controller.submit_request(
                addr=addr,
                is_read=True,
                size_bytes=64
            )

            if request_id:
                request_map[request_id] = (same_bg, controller.current_time_ns)

        # Process requests
        while request_map:
            responses = controller.tick()

            for resp in responses:
                if resp.request_id in request_map:
                    same_bg, submit_time = request_map[resp.request_id]
                    latency = controller.current_time_ns - submit_time

                    if same_bg:
                        same_bg_latencies.append(latency)
                    else:
                        different_bg_latencies.append(latency)

                    del request_map[resp.request_id]

        sim_end = controller.current_time_ns
        elapsed_ns = sim_end - sim_start

        # Calculate results
        result = BankGroupConflictResult()
        result.same_bank_group_requests = len(same_bg_latencies)
        result.different_bank_group_requests = len(different_bg_latencies)
        result.total_requests = result.same_bank_group_requests + result.different_bank_group_requests

        if same_bg_latencies:
            result.same_bg_latency_avg_ns = statistics.mean(same_bg_latencies)

        if different_bg_latencies:
            result.different_bg_latency_avg_ns = statistics.mean(different_bg_latencies)

        result.latency_penalty_ns = (result.different_bg_latency_avg_ns - result.same_bg_latency_avg_ns
                                     if result.same_bg_latency_avg_ns > 0 else 0)

        result.conflict_rate_percent = (result.different_bank_group_requests / result.total_requests * 100
                                       if result.total_requests > 0 else 0)

        # Bank group efficiency: higher when more accesses are to same BG
        result.bank_group_efficiency_percent = 100 - result.conflict_rate_percent

        result.test_duration_ns = elapsed_ns

        _logger.info(f"Bank group conflict test complete: penalty={result.latency_penalty_ns:.1f}ns, "
                    f"rate={result.conflict_rate_percent:.1f}%")

        self.results['bank_group_conflict'] = result
        return result

    def run_refresh_impact_test(
        self,
        test_duration_ns: float = 10_000_000,  # 10ms
        enable_refresh: bool = True
    ) -> RefreshImpactResult:
        """Test refresh impact on performance

        Measures bandwidth loss and latency increase during refresh operations.

        Args:
            test_duration_ns: Test duration in nanoseconds
            enable_refresh: Enable refresh during test

        Returns:
            RefreshImpactResult with refresh impact metrics
        """
        _logger.info(f"Running refresh impact test ({test_duration_ns/1e6:.0f}ms)...")

        random.seed(self.random_seed)

        # Test without refresh
        controller_no_refresh = HBM4Controller(
            spec=self.spec,
            enable_qos=False,
            enable_refresh=False
        )

        sim_start = controller_no_refresh.current_time_ns
        target_time = int(test_duration_ns)
        bytes_no_refresh = 0

        # Efficient simulation: submit requests at regular intervals
        # Tick one cycle at a time to maintain accurate timing
        while controller_no_refresh.current_time_ns < target_time:
            # Submit requests
            if len(controller_no_refresh.queue_manager.read_queue) < 32:
                for _ in range(8):
                    addr = random.randint(0, 0xFFFFFFFF)
                    if controller_no_refresh.submit_request(addr=addr, is_read=True, size_bytes=64):
                        bytes_no_refresh += 64

            # Always tick one cycle - this ensures accurate timing
            controller_no_refresh.tick()

        elapsed_no_refresh = controller_no_refresh.current_time_ns - sim_start
        bw_no_refresh = (bytes_no_refresh / elapsed_no_refresh * 1000) if elapsed_no_refresh > 0 else 0

        # Test with refresh
        controller_refresh = HBM4Controller(
            spec=self.spec,
            enable_qos=False,
            enable_refresh=enable_refresh
        )

        sim_start = controller_refresh.current_time_ns
        target_time = int(test_duration_ns)
        bytes_with_refresh = 0
        refresh_count = 0
        total_refresh_time = 0.0
        in_refresh = False
        refresh_start = 0
        requests_during_refresh = 0
        requests_outside_refresh = 0

        # Efficient simulation
        while controller_refresh.current_time_ns < target_time:
            # Check if in refresh
            if controller_refresh.refresh_scheduler:
                if controller_refresh.refresh_scheduler.can_refresh():
                    if not in_refresh:
                        in_refresh = True
                        refresh_start = controller_refresh.current_time_ns
                        refresh_count += 1
                elif in_refresh:
                    in_refresh = False
                    total_refresh_time += controller_refresh.current_time_ns - refresh_start

            # Submit requests
            if len(controller_refresh.queue_manager.read_queue) < 32:
                for _ in range(8):
                    addr = random.randint(0, 0xFFFFFFFF)
                    if controller_refresh.submit_request(addr=addr, is_read=True, size_bytes=64):
                        bytes_with_refresh += 64
                        if in_refresh:
                            requests_during_refresh += 1
                        else:
                            requests_outside_refresh += 1

            # Always tick one cycle
            controller_refresh.tick()

        if in_refresh:
            total_refresh_time += controller_refresh.current_time_ns - refresh_start

        elapsed_with_refresh = controller_refresh.current_time_ns - sim_start
        bw_with_refresh = (bytes_with_refresh / elapsed_with_refresh * 1000) if elapsed_with_refresh > 0 else 0

        # Calculate results
        result = RefreshImpactResult()
        result.refresh_interval_ns = self.timing.nREFI * self.timing.tCK_ps
        result.refresh_duration_ns = self.timing.nRFC * self.timing.tCK_ps
        result.refresh_count = refresh_count
        result.refresh_total_time_ns = total_refresh_time
        result.bandwidth_without_refresh_gbs = bw_no_refresh
        result.bandwidth_with_refresh_gbs = bw_with_refresh
        result.bandwidth_loss_percent = ((bw_no_refresh - bw_with_refresh) / bw_no_refresh * 100
                                        if bw_no_refresh > 0 else 0)
        result.requests_during_refresh = requests_during_refresh
        result.requests_outside_refresh = requests_outside_refresh
        result.effective_bandwidth_gbs = bw_with_refresh
        result.test_duration_ns = elapsed_with_refresh

        # Calculate refresh coverage (percentage of time in refresh)
        result.refresh_coverage_percent = (total_refresh_time / elapsed_with_refresh * 100
                                         if elapsed_with_refresh > 0 else 0)

        _logger.info(f"Refresh impact test complete: loss={result.bandwidth_loss_percent:.2f}%, "
                    f"count={refresh_count}")

        self.results['refresh_impact'] = result
        return result

    def run_qos_impact_test(
        self,
        num_requests: int = 20000,
        high_load: bool = True
    ) -> QoSImpactResult:
        """Test QoS priority impact on latency

        Measures how different QoS levels affect request latency.

        Args:
            num_requests: Total number of requests
            high_load: Use high load (True) vs light load (False)

        Returns:
            QoSImpactResult with priority metrics
        """
        _logger.info(f"Running QoS impact test ({num_requests} req, load={'high' if high_load else 'light'})...")

        random.seed(self.random_seed)

        # Create controller with QoS enabled
        controller = HBM4Controller(
            spec=self.spec,
            enable_qos=True,
            enable_refresh=False
        )

        sim_start = controller.current_time_ns

        # QoS distribution for this test
        qos_dist = {
            0: 0.05,   # Critical 5%
            1: 0.05,   # Critical 5%
            2: 0.05,   # High 5%
            3: 0.05,   # High 5%
            4: 0.10,   # High 10%
            5: 0.10,   # Normal 10%
            6: 0.10,   # Normal 10%
            7: 0.10,   # Normal 10%
            8: 0.10,   # Normal 10%
            9: 0.05,   # Low 5%
            10: 0.05,  # Low 5%
            11: 0.05,  # Low 5%
            12: 0.05,  # Background 5%
            13: 0.05,  # Background 5%
            14: 0.00,  # Background 0%
            15: 0.00,  # Background 0%
        }

        # Generate addresses
        addresses = [random.randint(0, 0xFFFFFFFF) for _ in range(num_requests)]

        # Submit requests with mixed QoS levels
        request_map: Dict[str, Tuple[int, int]] = {}  # id -> (qos_level, submit_time)
        qos_latencies: Dict[int, List[float]] = defaultdict(list)
        qos_requests: Dict[int, int] = defaultdict(int)

        for i, addr in enumerate(addresses):
            # Determine QoS level based on distribution
            rand_val = random.random()
            cumulative = 0
            qos_level = 8  # Default to normal
            for level, ratio in sorted(qos_dist.items()):
                cumulative += ratio
                if rand_val < cumulative:
                    qos_level = level
                    break

            request_id = controller.submit_request(
                addr=addr,
                is_read=random.random() < 0.7,
                qos_level=qos_level,
                size_bytes=64
            )

            if request_id:
                request_map[request_id] = (qos_level, controller.current_time_ns)
                qos_requests[qos_level] += 1

        # Process requests
        while request_map:
            responses = controller.tick()

            for resp in responses:
                if resp.request_id in request_map:
                    qos_level, submit_time = request_map[resp.request_id]
                    latency = controller.current_time_ns - submit_time

                    qos_latencies[qos_level].append(latency)
                    del request_map[resp.request_id]

        sim_end = controller.current_time_ns
        elapsed_ns = sim_end - sim_start

        # Calculate results
        result = QoSImpactResult()
        result.num_qos_levels = 16
        result.total_requests = len(qos_requests)
        result.test_duration_ns = elapsed_ns

        # Per-level metrics
        for qos, latencies in qos_latencies.items():
            if latencies:
                result.qos_level_latency_avg[qos] = statistics.mean(latencies)
                result.qos_level_latency_p99[qos] = self._percentile(latencies, 99)
                result.qos_level_requests[qos] = len(latencies)

        # Aggregate by priority
        critical_latencies = []
        high_latencies = []
        normal_latencies = []
        low_latencies = []

        for qos, latencies in qos_latencies.items():
            if qos <= 3:
                critical_latencies.extend(latencies)
            elif qos <= 7:
                high_latencies.extend(latencies)
            elif qos <= 11:
                normal_latencies.extend(latencies)
            else:
                low_latencies.extend(latencies)

        if critical_latencies:
            result.critical_latency_ns = statistics.mean(critical_latencies)
        if high_latencies:
            result.high_latency_ns = statistics.mean(high_latencies)
        if normal_latencies:
            result.normal_latency_ns = statistics.mean(normal_latencies)
        if low_latencies:
            result.low_latency_ns = statistics.mean(low_latencies)

        # Calculate ratios
        if result.critical_latency_ns > 0 and result.normal_latency_ns > 0:
            result.critical_to_normal_ratio = result.normal_latency_ns / result.critical_latency_ns

        if result.critical_latency_ns > 0 and result.low_latency_ns > 0:
            result.critical_to_low_ratio = result.low_latency_ns / result.critical_latency_ns

        # QoS effectiveness: measures how well critical requests are prioritized
        # Effective if critical is faster than normal
        if result.critical_to_normal_ratio > 1.0:
            result.qos_effectiveness_percent = min(100, (result.critical_to_normal_ratio - 1) * 50 + 50)
        else:
            result.qos_effectiveness_percent = 50 / result.critical_to_normal_ratio if result.critical_to_normal_ratio > 0 else 0

        # Check for starvation (low priority requests not getting service)
        if low_latencies and normal_latencies:
            if len(low_latencies) < len(normal_latencies) * 0.5:
                result.starvation_detected = True

        # Load impact
        if high_load:
            result.latency_under_load_ns = result.normal_latency_ns
        else:
            result.latency_under_light_load_ns = result.normal_latency_ns

        result.load_factor_percent = (result.latency_under_load_ns / result.latency_under_light_load_ns * 100
                                     if result.latency_under_light_load_ns > 0 else 100)

        _logger.info(f"QoS impact test complete: critical/normal ratio={result.critical_to_normal_ratio:.2f}x, "
                    f"effectiveness={result.qos_effectiveness_percent:.1f}%")

        self.results['qos_impact'] = result
        return result

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from sorted data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        idx = int(len(sorted_data) * percentile / 100)
        idx = min(idx, len(sorted_data) - 1)
        return sorted_data[idx]

    def run_all_tests(self) -> EnhancedBenchmarkReport:
        """Run all enhanced benchmark tests

        Returns:
            EnhancedBenchmarkReport with all results
        """
        _logger.info("=" * 60)
        _logger.info("Starting Enhanced HBM4 Benchmark Suite")
        _logger.info("=" * 60)

        start_time = time.time()

        # Create report
        report = EnhancedBenchmarkReport()
        report.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Run all tests
        _logger.info("-" * 40)
        _logger.info("1. Multi-Channel Parallel Access Test")
        _logger.info("-" * 40)
        report.multi_channel = self.run_multi_channel_test()

        _logger.info("-" * 40)
        _logger.info("2. Mixed Traffic Test")
        _logger.info("-" * 40)
        report.mixed_traffic = self.run_mixed_traffic_test()

        _logger.info("-" * 40)
        _logger.info("3. Bank Group Conflict Test")
        _logger.info("-" * 40)
        report.bank_group_conflict = self.run_bank_group_conflict_test()

        _logger.info("-" * 40)
        _logger.info("4. Refresh Impact Test")
        _logger.info("-" * 40)
        report.refresh_impact = self.run_refresh_impact_test(test_duration_ns=2_000)

        _logger.info("-" * 40)
        _logger.info("5. QoS Impact Test")
        _logger.info("-" * 40)
        report.qos_impact = self.run_qos_impact_test()

        end_time = time.time()
        report.duration_seconds = end_time - start_time

        # Generate findings and warnings
        report.findings = self._generate_findings(report)
        report.warnings = self._generate_warnings(report)

        # Summary
        report.total_bandwidth_gbs = (
            (report.multi_channel.measured_bandwidth_gbs if report.multi_channel else 0) +
            (report.mixed_traffic.total_bandwidth_gbs if report.mixed_traffic else 0)
        ) / 2

        latencies = []
        if report.qos_impact:
            latencies.append(report.qos_impact.critical_latency_ns)
            latencies.append(report.qos_impact.normal_latency_ns)
        report.average_latency_ns = statistics.mean(latencies) if latencies else 0

        efficiencies = []
        if report.multi_channel:
            efficiencies.append(report.multi_channel.bandwidth_efficiency_percent)
        if report.mixed_traffic:
            efficiencies.append(report.mixed_traffic.bandwidth_efficiency_percent)
        report.peak_efficiency_percent = max(efficiencies) if efficiencies else 0

        _logger.info("=" * 60)
        _logger.info(f"Enhanced Benchmark Suite Complete ({report.duration_seconds:.2f}s)")
        _logger.info("=" * 60)

        return report

    def _generate_findings(self, report: EnhancedBenchmarkReport) -> List[str]:
        """Generate key findings from results"""
        findings = []

        # Multi-channel findings
        if report.multi_channel:
            eff = report.multi_channel.bandwidth_efficiency_percent
            if eff > 80:
                findings.append(f"Excellent multi-channel efficiency at {eff:.1f}%")
            elif eff > 50:
                findings.append(f"Good multi-channel efficiency at {eff:.1f}%")
            else:
                findings.append(f"Multi-channel efficiency needs improvement at {eff:.1f}%")

        # Mixed traffic findings
        if report.mixed_traffic:
            rw_diff = abs(report.mixed_traffic.read_latency_avg_ns -
                         report.mixed_traffic.write_latency_avg_ns)
            if rw_diff < 20:
                findings.append(f"Consistent read/write latency (diff: {rw_diff:.1f}ns)")
            else:
                findings.append(f"Read/write latency imbalance (diff: {rw_diff:.1f}ns)")

        # Bank group conflict findings
        if report.bank_group_conflict:
            penalty = report.bank_group_conflict.latency_penalty_ns
            if penalty < 10:
                findings.append(f"Low bank group switching overhead ({penalty:.1f}ns)")
            else:
                findings.append(f"Bank group switching has significant overhead ({penalty:.1f}ns)")

        # Refresh impact findings
        if report.refresh_impact:
            loss = report.refresh_impact.bandwidth_loss_percent
            if loss < 2:
                findings.append(f"Minimal refresh overhead ({loss:.2f}% bandwidth loss)")
            else:
                findings.append(f"Refresh overhead is significant ({loss:.2f}% bandwidth loss)")

        # QoS impact findings
        if report.qos_impact:
            ratio = report.qos_impact.critical_to_normal_ratio
            if ratio > 1.5:
                findings.append(f"Strong QoS prioritization (critical {ratio:.2f}x faster than normal)")
            elif ratio > 1.0:
                findings.append(f"QoS scheduling working ({ratio:.2f}x critical vs normal)")
            else:
                findings.append("QoS scheduling may need tuning")

        return findings

    def _generate_warnings(self, report: EnhancedBenchmarkReport) -> List[str]:
        """Generate warnings from results"""
        warnings = []

        if report.multi_channel and report.multi_channel.bandwidth_efficiency_percent < 50:
            warnings.append("Multi-channel bandwidth efficiency critically low")

        if report.refresh_impact and report.refresh_impact.bandwidth_loss_percent > 5:
            warnings.append("Refresh bandwidth loss exceeds 5% threshold")

        if report.qos_impact and report.qos_impact.starvation_detected:
            warnings.append("Low priority request starvation detected")

        if report.bank_group_conflict and report.bank_group_conflict.conflict_rate_percent > 30:
            warnings.append("High bank group conflict rate - consider address mapping")

        return warnings


# =============================================================================
# Convenience Functions
# =============================================================================

def run_enhanced_benchmark(speed_grade: str = "8Gbps") -> EnhancedBenchmarkReport:
    """Run enhanced benchmark suite

    Args:
        speed_grade: HBM speed grade ("8Gbps", "12Gbps", "16Gbps")

    Returns:
        EnhancedBenchmarkReport with all results
    """
    benchmark = EnhancedBenchmark(speed_grade=speed_grade)
    return benchmark.run_all_tests()


def run_multi_channel_benchmark() -> MultiChannelResult:
    """Run only multi-channel benchmark"""
    return EnhancedBenchmark().run_multi_channel_test()


def run_mixed_traffic_benchmark(read_ratio: float = 0.7) -> MixedTrafficResult:
    """Run only mixed traffic benchmark"""
    return EnhancedBenchmark().run_mixed_traffic_test(read_ratio=read_ratio)


def run_bank_group_benchmark() -> BankGroupConflictResult:
    """Run only bank group conflict benchmark"""
    return EnhancedBenchmark().run_bank_group_conflict_test()


def run_refresh_benchmark() -> RefreshImpactResult:
    """Run only refresh impact benchmark

    Uses shorter duration for testing purposes.
    For full performance testing, use EnhancedBenchmark directly.
    """
    return EnhancedBenchmark().run_refresh_impact_test(test_duration_ns=2_000)


def run_qos_benchmark() -> QoSImpactResult:
    """Run only QoS impact benchmark"""
    return EnhancedBenchmark().run_qos_impact_test()
