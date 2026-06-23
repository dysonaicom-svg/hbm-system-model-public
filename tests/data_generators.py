"""
HBM4 Test Data Generators

Comprehensive test data generation utilities for HBM4 simulation testing:
- Address generators (sequential, random, stride, hot-spot, scatter)
- Traffic pattern generators
- Timing data generators
- Request/response data generators

Supports all HBM4 traffic patterns and configurations for testing validation.

Author: Claude Opus 4.8
"""

import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Iterator, Callable
from enum import Enum
from functools import lru_cache
import numpy as np

from model.controller.request import HBMRequest, RequestState
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT
from model.dram.hbm4_spec import HBM4Spec
from model.dram.timing import HBM3Timing, HBM4Timing


# =============================================================================
# Enums and Constants
# =============================================================================

class AddressPattern(Enum):
    """Address generation patterns"""
    SEQUENTIAL = "sequential"       # Consecutive addresses
    RANDOM = "random"              # Random addresses
    STRIDE = "stride"              # Fixed stride pattern
    HOT_SPOT = "hot_spot"          # Hot spot around specific addresses
    SCATTER = "scatter"            # Highly scattered addresses
    BANK_CONFLICT = "bank_conflict"  # Generate bank conflicts
    ROW_HIT = "row_hit"            # Generate row hits
    ROW_MISS = "row_miss"          # Generate row misses
    BURST = "burst"                # Burst pattern within same row


class TrafficMix(Enum):
    """Traffic composition types"""
    READ_ONLY = "read_only"        # 100% reads
    WRITE_ONLY = "write_only"      # 100% writes
    BALANCED = "balanced"          # 50/50 read/write
    READ_HEAVY = "read_heavy"      # 70/30 read/write
    WRITE_HEAVY = "write_heavy"    # 30/70 read/write
    MIXED_QOS = "mixed_qos"        # Mixed QoS priorities


class DataPattern(Enum):
    """Data content patterns for write requests"""
    ZERO = "zero"                  # All zeros
    ONES = "ones"                  # All ones
    ALTERNATING = "alternating"    # 0x55, 0xAA pattern
    INCREMENTAL = "incremental"     # Incrementing values
    RANDOM_DATA = "random_data"    # Random data
    ADDRESS_BASED = "address_based" # Data derived from address


@dataclass
class AddressGeneratorConfig:
    """Configuration for address generation"""
    # Range configuration
    min_address: int = 0
    max_address: int = 0xFFFFFFFFFFFF  # 2^48 - 1

    # Pattern configuration
    pattern: AddressPattern = AddressPattern.RANDOM
    stride_value: int = 4096
    burst_size: int = 64  # Bytes per request

    # Hot spot configuration
    hot_spot_address: int = 0x10000000000
    hot_spot_range: int = 0x10000000  # 256MB hot region
    hot_spot_probability: float = 0.8  # 80% of accesses to hot spot

    # Bank conflict configuration
    bank_conflict_interval: int = 4  # Every N-th access conflicts
    bank_conflict_base: Optional[int] = None

    # Row pattern configuration
    row_size: int = 2048
    rows_per_bank: int = 65536
    banks_per_channel: int = 16

    # Seed for reproducibility
    seed: Optional[int] = None

    def __post_init__(self):
        if self.seed is not None:
            random.seed(self.seed)


@dataclass
class TrafficGeneratorConfig:
    """Configuration for traffic generation"""
    # Request configuration
    num_requests: int = 1000
    burst_size: int = 64
    read_ratio: float = 0.7

    # Timing configuration
    inter_request_delay_min: int = 1  # cycles
    inter_request_delay_max: int = 10  # cycles

    # Priority configuration
    qos_distribution: Dict[int, float] = field(default_factory=lambda: {
        15: 0.1,  # Critical - 10%
        12: 0.2,  # High - 20%
        8: 0.4,   # Normal - 40%
        4: 0.2,    # Low - 20%
        0: 0.1,   # Best effort - 10%
    })

    # Pattern configuration
    traffic_mix: TrafficMix = TrafficMix.BALANCED
    address_pattern: AddressPattern = AddressPattern.RANDOM

    # Seed for reproducibility
    seed: Optional[int] = None


@dataclass
class TimingDataConfig:
    """Configuration for timing data generation"""
    # Clock configuration
    clock_period_ps: int = 781  # HBM3: 1.28 GHz
    clock_period_16gbps: int = 62  # HBM4 16 Gbps

    # Latency configuration
    read_latency_base: int = 30
    write_latency_base: int = 10
    phy_latency: int = 20

    # Timing margins
    timing_margin_percent: float = 0.1  # 10% margin

    # Speed grades
    speed_grades: List[str] = field(default_factory=lambda: ["8Gbps", "12Gbps", "16Gbps"])


# =============================================================================
# Address Generators
# =============================================================================

class AddressGenerator:
    """Base class for address generators"""

    def __init__(self, config: AddressGeneratorConfig):
        self.config = config
        if config.seed is not None:
            random.seed(config.seed)

    def generate(self, count: int) -> List[int]:
        """Generate a list of addresses"""
        raise NotImplementedError

    def generate_batch(self, count: int, batch_size: int = 32) -> List[List[int]]:
        """Generate addresses in batches"""
        addresses = self.generate(count)
        return [addresses[i:i + batch_size] for i in range(0, len(addresses), batch_size)]

    def generate_stream(self, count: int) -> Iterator[int]:
        """Generate addresses as a stream"""
        for addr in self.generate(count):
            yield addr


class SequentialAddressGenerator(AddressGenerator):
    """Generate sequential addresses"""

    def __init__(self, config: AddressGeneratorConfig):
        super().__init__(config)
        self._current = config.min_address

    def generate(self, count: int) -> List[int]:
        """Generate sequential addresses"""
        addresses = []
        for _ in range(count):
            addr = self._current
            addresses.append(addr)
            self._current += self.config.burst_size * self.config.row_size
            if self._current >= self.config.max_address:
                self._current = self.config.min_address
        return addresses

    def reset(self):
        """Reset counter"""
        self._current = self.config.min_address


class RandomAddressGenerator(AddressGenerator):
    """Generate random addresses"""

    def generate(self, count: int) -> List[int]:
        """Generate random addresses"""
        range_size = self.config.max_address - self.config.min_address
        return [
            self.config.min_address + int(random.random() * range_size)
            for _ in range(count)
        ]


class StrideAddressGenerator(AddressGenerator):
    """Generate addresses with fixed stride"""

    def __init__(self, config: AddressGeneratorConfig):
        super().__init__(config)
        self._current = config.min_address

    def generate(self, count: int) -> List[int]:
        """Generate stride addresses"""
        addresses = []
        stride = self.config.stride_value
        for _ in range(count):
            addresses.append(self._current)
            self._current = (self._current + stride) % self.config.max_address
            if self._current < self.config.min_address:
                self._current = self.config.min_address
        return addresses

    def reset(self):
        """Reset counter"""
        self._current = self.config.min_address


class HotSpotAddressGenerator(AddressGenerator):
    """Generate hot spot addresses (Pareto distribution)"""

    def __init__(self, config: AddressGeneratorConfig):
        super().__init__(config)
        self._alpha = 1.5  # Pareto shape parameter

    def generate(self, count: int) -> List[int]:
        """Generate hot spot addresses with Pareto distribution"""
        addresses = []
        for _ in range(count):
            if random.random() < self.config.hot_spot_probability:
                # Access hot spot region
                offset = int(self._pareto_sample() * self.config.hot_spot_range)
                addr = self.config.hot_spot_address + (offset % self.config.hot_spot_range)
            else:
                # Access outside hot spot
                addr = self._random_outside_hotspot()
            addresses.append(addr)
        return addresses

    def _pareto_sample(self) -> float:
        """Sample from Pareto distribution"""
        u = random.random()
        return self._alpha * (1 - u) ** (-1 / self._alpha)

    def _random_outside_hotspot(self) -> int:
        """Generate random address outside hot spot"""
        range_size = self.config.max_address - self.config.min_address
        hot_start = self.config.hot_spot_address
        hot_end = hot_start + self.config.hot_spot_range

        while True:
            addr = self.config.min_address + int(random.random() * range_size)
            if addr < hot_start or addr >= hot_end:
                return addr


class ScatterAddressGenerator(AddressGenerator):
    """Generate highly scattered addresses"""

    def __init__(self, config: AddressGeneratorConfig):
        super().__init__(config)
        self._cache = {}
        if config.seed is not None:
            np.random.seed(config.seed)

    def generate(self, count: int) -> List[int]:
        """Generate scattered addresses"""
        # Use LCG-based pseudo-random for better distribution
        addresses = []
        for i in range(count):
            seed = (i * 1103515245 + 12345) & 0x7FFFFFFF
            addr = self.config.min_address + (seed % (self.config.max_address - self.config.min_address))
            addresses.append(addr)
        return addresses


class BankConflictAddressGenerator(AddressGenerator):
    """Generate addresses that cause bank conflicts"""

    def __init__(self, config: AddressGeneratorConfig):
        super().__init__(config)
        self._bank_id = 0
        self._counter = 0

    def generate(self, count: int) -> List[int]:
        """Generate addresses that cause bank conflicts"""
        addresses = []
        for _ in range(count):
            # Keep same bank_id for conflict_interval requests
            if self._counter >= self.config.bank_conflict_interval:
                self._bank_id = (self._bank_id + 1) % self.config.banks_per_channel
                self._counter = 0

            # Generate address with current bank
            base = self.config.min_address
            offset = self._bank_id * self.config.row_size * self.config.rows_per_bank
            row = int(random.random() * self.config.rows_per_bank)
            addr = base + offset + row * self.config.row_size
            addresses.append(addr)
            self._counter += 1

        return addresses

    def reset(self):
        """Reset counter"""
        self._bank_id = 0
        self._counter = 0


class RowHitAddressGenerator(AddressGenerator):
    """Generate addresses that maximize row hits"""

    def __init__(self, config: AddressGeneratorConfig):
        super().__init__(config)
        self._current_row = 0
        self._bank_id = 0

    def generate(self, count: int) -> List[int]:
        """Generate addresses that target same row"""
        addresses = []
        for _ in range(count):
            # Change row occasionally to create row hits
            if random.random() < 0.1:  # 10% chance to change row
                self._current_row = (self._current_row + 1) % self.config.rows_per_bank
            if random.random() < 0.05:  # 5% chance to change bank
                self._bank_id = (self._bank_id + 1) % self.config.banks_per_channel

            base = self.config.min_address
            bank_offset = self._bank_id * self.config.row_size * self.config.rows_per_bank
            addr = base + bank_offset + self._current_row * self.config.row_size
            addresses.append(addr)
        return addresses

    def reset(self):
        """Reset counters"""
        self._current_row = 0
        self._bank_id = 0


class RowMissAddressGenerator(AddressGenerator):
    """Generate addresses that cause row misses"""

    def __init__(self, config: AddressGeneratorConfig):
        super().__init__(config)
        self._bank_id = 0

    def generate(self, count: int) -> List[int]:
        """Generate addresses that always miss rows"""
        addresses = []
        for _ in range(count):
            # Change row every access to ensure misses
            row = int(random.random() * self.config.rows_per_bank)
            bank_offset = self._bank_id * self.config.row_size * self.config.rows_per_bank
            addr = self.config.min_address + bank_offset + row * self.config.row_size
            addresses.append(addr)

            # Change bank periodically
            if random.random() < 0.1:
                self._bank_id = (self._bank_id + 1) % self.config.banks_per_channel
        return addresses


class BurstAddressGenerator(AddressGenerator):
    """Generate burst addresses within same row"""

    def __init__(self, config: AddressGeneratorConfig):
        super().__init__(config)
        self._current_address = config.min_address
        self._burst_counter = 0
        self._burst_size = 8

    def generate(self, count: int) -> List[int]:
        """Generate burst addresses within same row"""
        addresses = []
        for _ in range(count):
            if self._burst_counter >= self._burst_size:
                # Start new burst
                self._burst_counter = 0
                self._current_address = self.config.min_address + int(
                    random.random() * (self.config.max_address - self.config.min_address)
                )
                # Align to row boundary
                self._current_address = (self._current_address // self.config.row_size) * self.config.row_size

            addresses.append(self._current_address)
            self._current_address += self.config.row_size // 16  # Small increment within row
            self._burst_counter += 1
        return addresses

    def reset(self):
        """Reset counters"""
        self._current_address = self.config.min_address
        self._burst_counter = 0


# =============================================================================
# Address Generator Factory
# =============================================================================

class AddressGeneratorFactory:
    """Factory for creating address generators"""

    _generators = {
        AddressPattern.SEQUENTIAL: SequentialAddressGenerator,
        AddressPattern.RANDOM: RandomAddressGenerator,
        AddressPattern.STRIDE: StrideAddressGenerator,
        AddressPattern.HOT_SPOT: HotSpotAddressGenerator,
        AddressPattern.SCATTER: ScatterAddressGenerator,
        AddressPattern.BANK_CONFLICT: BankConflictAddressGenerator,
        AddressPattern.ROW_HIT: RowHitAddressGenerator,
        AddressPattern.ROW_MISS: RowMissAddressGenerator,
        AddressPattern.BURST: BurstAddressGenerator,
    }

    @classmethod
    def create(
        cls,
        pattern: AddressPattern,
        config: Optional[AddressGeneratorConfig] = None,
        **kwargs
    ) -> AddressGenerator:
        """Create an address generator for the specified pattern"""
        if config is None:
            config = AddressGeneratorConfig(pattern=pattern, **kwargs)

        generator_class = cls._generators.get(pattern)
        if generator_class is None:
            raise ValueError(f"Unknown address pattern: {pattern}")

        return generator_class(config)

    @classmethod
    def register(cls, pattern: AddressPattern, generator_class: type):
        """Register a custom address generator"""
        cls._generators[pattern] = generator_class


# =============================================================================
# Traffic Pattern Generators
# =============================================================================

class TrafficPatternGenerator:
    """Generate traffic patterns with configurable properties"""

    def __init__(
        self,
        config: TrafficGeneratorConfig,
        address_config: Optional[AddressGeneratorConfig] = None,
        hbm_config: Optional[HBMConfig] = None
    ):
        self.config = config
        self.address_config = address_config or AddressGeneratorConfig(seed=config.seed)
        self.hbm_config = hbm_config or HBM4_DEFAULT

        if config.seed is not None:
            random.seed(config.seed)
            np.random.seed(config.seed)

        # Create address generator
        self.address_generator = AddressGeneratorFactory.create(
            config.address_pattern,
            self.address_config
        )

    def generate_requests(self, count: Optional[int] = None) -> List[HBMRequest]:
        """Generate a list of HBM requests"""
        if count is None:
            count = self.config.num_requests

        requests = []
        for i in range(count):
            request = self._generate_single_request(i)
            requests.append(request)

        return requests

    def _generate_single_request(self, request_id: int) -> HBMRequest:
        """Generate a single request"""
        # Generate address
        addr = next(self.address_generator.generate_stream(1))

        # Determine read/write
        is_read = self._is_read_request()

        # Determine QoS priority
        qos = self._sample_qos()

        # Determine timing
        delay = self._sample_delay()

        return HBMRequest(
            addr=addr,
            length=self.config.burst_size,
            is_read=is_read,
            qos=qos,
            burst_length=self.config.burst_size,
            request_id=request_id,
            arrival_time=delay,
        )

    def _is_read_request(self) -> bool:
        """Determine if request is a read"""
        ratio = self.config.read_ratio
        if self.config.traffic_mix == TrafficMix.READ_ONLY:
            ratio = 1.0
        elif self.config.traffic_mix == TrafficMix.WRITE_ONLY:
            ratio = 0.0
        elif self.config.traffic_mix == TrafficMix.BALANCED:
            ratio = 0.5
        elif self.config.traffic_mix == TrafficMix.READ_HEAVY:
            ratio = 0.7
        elif self.config.traffic_mix == TrafficMix.WRITE_HEAVY:
            ratio = 0.3
        return random.random() < ratio

    def _sample_qos(self) -> int:
        """Sample a QoS priority based on distribution"""
        dist = self.config.qos_distribution
        r = random.random()
        cumulative = 0.0
        for qos, prob in sorted(dist.items(), key=lambda x: -x[0]):
            cumulative += prob
            if r < cumulative:
                return qos
        return min(dist.keys())

    def _sample_delay(self) -> int:
        """Sample inter-request delay"""
        return random.randint(
            self.config.inter_request_delay_min,
            self.config.inter_request_delay_max
        )

    def generate_request_stream(self, count: int) -> Iterator[HBMRequest]:
        """Generate requests as a stream"""
        for i in range(count):
            yield self._generate_single_request(i)


class SequentialTrafficGenerator(TrafficPatternGenerator):
    """Generator for sequential traffic patterns"""

    def __init__(self, hbm_config: Optional[HBMConfig] = None, seed: Optional[int] = None):
        config = TrafficGeneratorConfig(
            traffic_mix=TrafficMix.BALANCED,
            address_pattern=AddressPattern.SEQUENTIAL,
            seed=seed
        )
        addr_config = AddressGeneratorConfig(
            pattern=AddressPattern.SEQUENTIAL,
            seed=seed
        )
        super().__init__(config, addr_config, hbm_config)


class RandomTrafficGenerator(TrafficPatternGenerator):
    """Generator for random traffic patterns"""

    def __init__(self, hbm_config: Optional[HBMConfig] = None, seed: Optional[int] = None):
        config = TrafficGeneratorConfig(
            traffic_mix=TrafficMix.BALANCED,
            address_pattern=AddressPattern.RANDOM,
            seed=seed
        )
        addr_config = AddressGeneratorConfig(
            pattern=AddressPattern.RANDOM,
            seed=seed
        )
        super().__init__(config, addr_config, hbm_config)


class StrideTrafficGenerator(TrafficPatternGenerator):
    """Generator for stride traffic patterns"""

    def __init__(
        self,
        stride: int = 4096,
        hbm_config: Optional[HBMConfig] = None,
        seed: Optional[int] = None
    ):
        config = TrafficGeneratorConfig(
            traffic_mix=TrafficMix.READ_HEAVY,
            address_pattern=AddressPattern.STRIDE,
            seed=seed
        )
        addr_config = AddressGeneratorConfig(
            pattern=AddressPattern.STRIDE,
            stride_value=stride,
            seed=seed
        )
        super().__init__(config, addr_config, hbm_config)
        self.address_generator.config.stride_value = stride


class HotSpotTrafficGenerator(TrafficPatternGenerator):
    """Generator for hot-spot traffic patterns"""

    def __init__(
        self,
        hot_spot_addr: int = 0x10000000000,
        hot_spot_range: int = 0x10000000,
        hbm_config: Optional[HBMConfig] = None,
        seed: Optional[int] = None
    ):
        config = TrafficGeneratorConfig(
            traffic_mix=TrafficMix.READ_HEAVY,
            address_pattern=AddressPattern.HOT_SPOT,
            seed=seed
        )
        addr_config = AddressGeneratorConfig(
            pattern=AddressPattern.HOT_SPOT,
            hot_spot_address=hot_spot_addr,
            hot_spot_range=hot_spot_range,
            seed=seed
        )
        super().__init__(config, addr_config, hbm_config)


class MixedTrafficGenerator(TrafficPatternGenerator):
    """Generator for mixed traffic patterns with all access types"""

    def __init__(
        self,
        hbm_config: Optional[HBMConfig] = None,
        seed: Optional[int] = None
    ):
        config = TrafficGeneratorConfig(
            traffic_mix=TrafficMix.MIXED_QOS,
            address_pattern=AddressPattern.RANDOM,
            seed=seed
        )
        super().__init__(config, None, hbm_config)


# =============================================================================
# Timing Data Generators
# =============================================================================

class TimingDataGenerator:
    """Generate timing-related test data"""

    def __init__(self, config: Optional[TimingDataConfig] = None):
        self.config = config or TimingDataConfig()

    def generate_timing_params(self, speed_grade: str = "8Gbps") -> Dict[str, int]:
        """Generate timing parameters for a speed grade"""
        # Base timing for HBM4
        tCK = self._get_tCK(speed_grade)

        timing = {
            'tCK': tCK,
            'nCL': 8,
            'nCWL': 3,
            'nRCDRD': 8,
            'nRCDWR': 8,
            'nRP': 8,
            'nRAS': 20,
            'nRC': 22,
            'nWR': 8,
            'nRTPS': 2,
            'nRTPL': 3,
            'nCCDS': 2,
            'nCCDL': 3,
            'nRRDS': 3,
            'nRRDL': 4,
            'nWTRS': 4,
            'nWTRL': 5,
            'nRTW': 4,
            'nFAW': 16,
            'nRFC': 260,
            'nREFI': 3900,
            'nREFW': 39000,
        }

        # Apply margins
        if self.config.timing_margin_percent > 0:
            margin = self.config.timing_margin_percent
            for key in timing:
                if key != 'tCK':
                    timing[key] = int(timing[key] * (1 + margin))

        return timing

    def _get_tCK(self, speed_grade: str) -> int:
        """Get clock period for speed grade (in ps)"""
        periods = {
            "8Gbps": 125,
            "12Gbps": 83,
            "16Gbps": 62,
        }
        return periods.get(speed_grade, 125)

    def generate_latency_sweep(
        self,
        min_latency: int = 10,
        max_latency: int = 100,
        step: int = 5
    ) -> List[int]:
        """Generate latency sweep values"""
        return list(range(min_latency, max_latency + 1, step))

    def generate_refresh_windows(self, sim_time_us: float) -> List[Tuple[int, int]]:
        """Generate refresh window boundaries

        Returns list of (start_cycle, end_cycle) tuples
        """
        tREFI = 3900  # Refresh interval in cycles
        windows = []

        current = 0
        while current < sim_time_us * 1280:  # Convert us to cycles at 1.28 GHz
            windows.append((current, current + 260))  # tRFC = 260 cycles
            current += tREFI

        return windows

    def generate_burst_timings(
        self,
        num_bursts: int,
        tCCD: int = 2
    ) -> List[int]:
        """Generate burst timing boundaries"""
        return [i * tCCD for i in range(num_bursts)]


# =============================================================================
# Data Pattern Generators
# =============================================================================

class DataPatternGenerator:
    """Generate data patterns for write requests"""

    def __init__(self, pattern: DataPattern = DataPattern.RANDOM_DATA):
        self.pattern = pattern

    def generate(self, size_bytes: int, seed: Optional[int] = None) -> bytes:
        """Generate data of specified size"""
        if seed is not None:
            random.seed(seed)

        if self.pattern == DataPattern.ZERO:
            return b'\x00' * size_bytes
        elif self.pattern == DataPattern.ONES:
            return b'\xFF' * size_bytes
        elif self.pattern == DataPattern.ALTERNATING:
            return self._generate_alternating(size_bytes)
        elif self.pattern == DataPattern.INCREMENTAL:
            return self._generate_incremental(size_bytes)
        elif self.pattern == DataPattern.RANDOM_DATA:
            return self._generate_random(size_bytes)
        elif self.pattern == DataPattern.ADDRESS_BASED:
            return self._generate_address_based(size_bytes, seed)
        else:
            return self._generate_random(size_bytes)

    def _generate_alternating(self, size: int) -> bytes:
        """Generate alternating pattern (0x55, 0xAA)"""
        pattern = b'\x55\xAA' * (size // 2 + 1)
        return pattern[:size]

    def _generate_incremental(self, size: int) -> bytes:
        """Generate incremental pattern"""
        return bytes([i % 256 for i in range(size)])

    def _generate_random(self, size: int) -> bytes:
        """Generate random data"""
        return bytes(random.randint(0, 255) for _ in range(size))

    def _generate_address_based(self, size: int, addr: int = 0) -> bytes:
        """Generate data based on address"""
        hash_input = f"{addr}".encode()
        base = hashlib.md5(hash_input).digest()
        result = bytearray()
        while len(result) < size:
            result.extend(base)
        return bytes(result[:size])


# =============================================================================
# Test Data Generator Suite
# =============================================================================

@dataclass
class TestDataSuite:
    """Complete test data suite for HBM4 testing"""

    # Generated data
    addresses: List[int] = field(default_factory=list)
    requests: List[HBMRequest] = field(default_factory=list)
    timing_params: Dict[str, int] = field(default_factory=dict)

    # Metadata
    num_requests: int = 0
    pattern_type: str = ""
    speed_grade: str = "8Gbps"
    seed: Optional[int] = None


class TestDataGenerator:
    """Main test data generator orchestrator"""

    def __init__(
        self,
        seed: Optional[int] = None,
        hbm_config: Optional[HBMConfig] = None
    ):
        self.seed = seed or random.randint(0, 2**31)
        self.hbm_config = hbm_config or HBM4_DEFAULT

        random.seed(self.seed)

        self.address_factory = AddressGeneratorFactory()
        self.timing_generator = TimingDataGenerator()

    def generate_addresses(
        self,
        pattern: AddressPattern,
        count: int,
        **kwargs
    ) -> List[int]:
        """Generate addresses for a specific pattern"""
        config = AddressGeneratorConfig(
            pattern=pattern,
            seed=self.seed,
            **kwargs
        )
        generator = self.address_factory.create(pattern, config)
        return generator.generate(count)

    def generate_requests_for_pattern(
        self,
        pattern: AddressPattern,
        count: int,
        traffic_mix: TrafficMix = TrafficMix.BALANCED,
        **kwargs
    ) -> List[HBMRequest]:
        """Generate requests for a specific pattern"""
        traffic_config = TrafficGeneratorConfig(
            traffic_mix=traffic_mix,
            address_pattern=pattern,
            num_requests=count,
            seed=self.seed
        )
        addr_config = AddressGeneratorConfig(
            pattern=pattern,
            seed=self.seed,
            **kwargs
        )

        generator = TrafficPatternGenerator(traffic_config, addr_config, self.hbm_config)
        return generator.generate_requests(count)

    def generate_full_suite(self, count: int = 1000) -> Dict[str, TestDataSuite]:
        """Generate complete test data suite for all patterns"""
        suites = {}

        patterns = [
            AddressPattern.SEQUENTIAL,
            AddressPattern.RANDOM,
            AddressPattern.STRIDE,
            AddressPattern.HOT_SPOT,
            AddressPattern.SCATTER,
            AddressPattern.ROW_HIT,
            AddressPattern.ROW_MISS,
        ]

        for pattern in patterns:
            suite = TestDataSuite(
                num_requests=count,
                pattern_type=pattern.value,
                seed=self.seed
            )

            suite.addresses = self.generate_addresses(pattern, count)
            suite.requests = self.generate_requests_for_pattern(pattern, count)
            suite.timing_params = self.timing_generator.generate_timing_params(
                self.hbm_config.speed_grade
            )

            suites[pattern.value] = suite

        return suites

    def generate_regression_data(self) -> Dict[str, Any]:
        """Generate data for regression testing"""
        return {
            'sequential': self.generate_addresses(AddressPattern.SEQUENTIAL, 10000),
            'random': self.generate_addresses(AddressPattern.RANDOM, 10000),
            'stride': self.generate_addresses(AddressPattern.STRIDE, 10000, stride_value=4096),
            'hot_spot': self.generate_addresses(AddressPattern.HOT_SPOT, 10000),
            'bank_conflict': self.generate_addresses(AddressPattern.BANK_CONFLICT, 1000),
        }

    def generate_benchmark_data(self) -> Dict[str, List[HBMRequest]]:
        """Generate data for benchmarking"""
        benchmarks = {}

        benchmarks['sequential'] = self.generate_requests_for_pattern(
            AddressPattern.SEQUENTIAL, 5000, TrafficMix.READ_HEAVY
        )
        benchmarks['random'] = self.generate_requests_for_pattern(
            AddressPattern.RANDOM, 5000, TrafficMix.BALANCED
        )
        benchmarks['stride_4kb'] = self.generate_requests_for_pattern(
            AddressPattern.STRIDE, 5000, TrafficMix.READ_HEAVY, stride_value=4096
        )
        benchmarks['hot_spot'] = self.generate_requests_for_pattern(
            AddressPattern.HOT_SPOT, 5000, TrafficMix.READ_HEAVY
        )

        return benchmarks


# =============================================================================
# Fixture Factories (for pytest integration)
# =============================================================================

def create_address_generator(pattern: AddressPattern, **kwargs) -> AddressGenerator:
    """Create an address generator fixture"""
    config = AddressGeneratorConfig(pattern=pattern, **kwargs)
    return AddressGeneratorFactory.create(pattern, config)


def create_traffic_generator(
    pattern: AddressPattern,
    traffic_mix: TrafficMix = TrafficMix.BALANCED,
    **kwargs
) -> TrafficPatternGenerator:
    """Create a traffic generator fixture"""
    traffic_config = TrafficGeneratorConfig(
        traffic_mix=traffic_mix,
        address_pattern=pattern,
        **kwargs
    )
    addr_config = AddressGeneratorConfig(pattern=pattern, **kwargs)
    return TrafficPatternGenerator(traffic_config, addr_config)


def create_timing_generator() -> TimingDataGenerator:
    """Create a timing data generator fixture"""
    return TimingDataGenerator()


def create_test_data_generator(seed: Optional[int] = None) -> TestDataGenerator:
    """Create the main test data generator"""
    return TestDataGenerator(seed=seed)


# =============================================================================
# Utility Functions
# =============================================================================

def verify_address_distribution(addresses: List[int]) -> Dict[str, Any]:
    """Verify address distribution statistics"""
    if not addresses:
        return {}

    return {
        'count': len(addresses),
        'min': min(addresses),
        'max': max(addresses),
        'range': max(addresses) - min(addresses),
        'unique': len(set(addresses)),
        'duplicate_rate': 1 - len(set(addresses)) / len(addresses),
    }


def calculate_bank_distribution(
    addresses: List[int],
    banks_per_channel: int = 16,
    channels: int = 32
) -> Dict[str, Any]:
    """Calculate bank access distribution"""
    bank_counts = {}
    channel_counts = {}

    for addr in addresses:
        # Simplified bank/channel extraction
        channel = (addr >> 20) % channels
        bank = (addr >> 10) % banks_per_channel

        bank_counts[bank] = bank_counts.get(bank, 0) + 1
        channel_counts[channel] = channel_counts.get(channel, 0) + 1

    return {
        'bank_distribution': bank_counts,
        'channel_distribution': channel_counts,
        'bank_variance': np.var(list(bank_counts.values())) if bank_counts else 0,
        'channel_variance': np.var(list(channel_counts.values())) if channel_counts else 0,
    }


def export_trace_format(
    requests: List[HBMRequest],
    format_type: str = "ramulator"
) -> str:
    """Export requests in trace format"""
    lines = []

    if format_type == "ramulator":
        for req in requests:
            op = "R" if req.is_read else "W"
            lines.append(f"{op} {req.addr:#x}")

    return "\n".join(lines)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Enums
    'AddressPattern',
    'TrafficMix',
    'DataPattern',

    # Config classes
    'AddressGeneratorConfig',
    'TrafficGeneratorConfig',
    'TimingDataConfig',

    # Generators
    'AddressGenerator',
    'SequentialAddressGenerator',
    'RandomAddressGenerator',
    'StrideAddressGenerator',
    'HotSpotAddressGenerator',
    'ScatterAddressGenerator',
    'BankConflictAddressGenerator',
    'RowHitAddressGenerator',
    'RowMissAddressGenerator',
    'BurstAddressGenerator',
    'AddressGeneratorFactory',
    'TrafficPatternGenerator',
    'SequentialTrafficGenerator',
    'RandomTrafficGenerator',
    'StrideTrafficGenerator',
    'HotSpotTrafficGenerator',
    'MixedTrafficGenerator',
    'TimingDataGenerator',
    'DataPatternGenerator',
    'TestDataGenerator',

    # Test data
    'TestDataSuite',

    # Utilities
    'verify_address_distribution',
    'calculate_bank_distribution',
    'export_trace_format',

    # Fixture factories
    'create_address_generator',
    'create_traffic_generator',
    'create_timing_generator',
    'create_test_data_generator',
]
