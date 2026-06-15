"""
Multi-Channel HBM3 Support Module

This module provides proper multi-channel support for HBM3 simulation:
- Channel-aware traffic generation
- Channel load balancing
- Per-channel statistics

Reference: 2026-06-15-hbm-system-model-design.md
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random


@dataclass
class ChannelStats:
    """Per-channel statistics"""
    channel_id: int
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    row_hits: int = 0
    row_misses: int = 0
    total_latency_cycles: int = 0
    activations: int = 0

    @property
    def avg_latency(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_cycles / self.total_requests

    @property
    def hit_rate(self) -> float:
        total = self.row_hits + self.row_misses
        if total == 0:
            return 0.0
        return self.row_hits / total


class ChannelSelector:
    """Channel selection strategies for multi-channel HBM3

    Supports various channel selection policies:
    - ROUND_ROBIN: Simple round-robin across channels
    - HASH: Hash-based deterministic selection
    - LOAD_BALANCED: Select least-loaded channel
    - ADDR_BASED: Direct address-based channel selection
    """

    ROUND_ROBIN = "round_robin"
    HASH = "hash"
    LOAD_BALANCED = "load_balanced"
    ADDR_BASED = "addr_based"

    def __init__(
        self,
        num_channels: int = 8,
        strategy: str = ADDR_BASED,
        seed: Optional[int] = None
    ):
        """Initialize channel selector

        Args:
            num_channels: Number of channels (default 8 for HBM3)
            strategy: Selection strategy
            seed: Random seed for reproducible behavior
        """
        self.num_channels = num_channels
        self.strategy = strategy
        if seed is not None:
            random.seed(seed)

        # Round-robin state
        self._round_robin_index = 0

        # Load balancing state
        self._channel_load: Dict[int, int] = {i: 0 for i in range(num_channels)}

    def select_channel(self, addr: int, length: int = 64) -> int:
        """Select channel based on address and strategy

        Args:
            addr: Memory address
            length: Request length in bytes

        Returns:
            Selected channel ID (0-7 for HBM3)
        """
        if self.strategy == self.ROUND_ROBIN:
            return self._round_robin()
        elif self.strategy == self.HASH:
            return self._hash_channel(addr)
        elif self.strategy == self.LOAD_BALANCED:
            return self._least_loaded_channel()
        else:  # ADDR_BASED
            return self._addr_based_channel(addr)

    def _round_robin(self) -> int:
        """Round-robin channel selection"""
        ch = self._round_robin_index
        self._round_robin_index = (self._round_robin_index + 1) % self.num_channels
        return ch

    def _hash_channel(self, addr: int) -> int:
        """Hash-based deterministic channel selection

        Uses a simple hash to distribute addresses across channels
        while maintaining some locality for adjacent addresses.
        """
        # XOR-fold the address to get channel
        hash_val = addr ^ (addr >> 8) ^ (addr >> 16)
        return hash_val % self.num_channels

    def _least_loaded_channel(self) -> int:
        """Select the least loaded channel"""
        min_load = min(self._channel_load.values())
        # Find first channel with minimum load
        for ch in range(self.num_channels):
            if self._channel_load[ch] == min_load:
                return ch
        return 0

    def _addr_based_channel(self, addr: int) -> int:
        """Direct address-based channel selection

        For HBM3 with 8 channels:
        - Addr[45:43] = Channel (3-bit, 8 channels)

        This matches the default HBM3 address mapping.
        """
        # Extract channel bits (Addr[45:43])
        # Assuming 64-bit address space
        channel_bits = (addr >> 43) & 0x7  # 3 bits for 8 channels
        return int(channel_bits)

    def record_request(self, channel_id: int):
        """Record that a request was sent to a channel

        Args:
            channel_id: Target channel ID
        """
        if channel_id in self._channel_load:
            self._channel_load[channel_id] += 1

    def release_channel(self, channel_id: int):
        """Record that a request completed on a channel

        Args:
            channel_id: Channel that completed
        """
        if channel_id in self._channel_load:
            self._channel_load[channel_id] = max(0, self._channel_load[channel_id] - 1)

    def get_channel_load(self) -> Dict[int, int]:
        """Get current load for all channels

        Returns:
            Dict mapping channel_id to load count
        """
        return dict(self._channel_load)

    def reset(self):
        """Reset channel selector state"""
        self._round_robin_index = 0
        self._channel_load = {i: 0 for i in range(self.num_channels)}


class MultiChannelTrafficGenerator:
    """Traffic generator with proper multi-channel support

    Generates traffic that properly distributes across HBM3 channels.
    """

    def __init__(
        self,
        config: 'SimulationConfig',  # Forward reference
        num_channels: int = 8,
        channel_selector: Optional[ChannelSelector] = None,
    ):
        """Initialize multi-channel traffic generator

        Args:
            config: Simulation configuration
            num_channels: Number of channels (8 for HBM3)
            channel_selector: Optional custom channel selector
        """
        self.config = config
        self.num_channels = num_channels

        if channel_selector is None:
            channel_selector = ChannelSelector(
                num_channels=num_channels,
                strategy=ChannelSelector.ADDR_BASED
            )
        self.channel_selector = channel_selector

        # Address range per channel
        self._addr_bits_per_channel = (num_channels - 1).bit_length()

        if config.seed is not None:
            random.seed(config.seed)
        self.current_addr = 0
        self.hot_bank = 0

    def generate(self) -> List['HBMRequest']:
        """Generate requests with proper channel distribution

        Returns:
            List of HBMRequest with properly decoded channel info
        """
        from model.controller.request import HBMRequest

        requests = []

        # According to request rate, decide whether to generate
        if random.random() > self.config.request_rate:
            return requests

        # Generate address based on pattern
        if self.config.traffic_pattern.value == "random":
            addr = random.randint(0, self.config.address_range - 1)
        elif self.config.traffic_pattern.value == "sequential":
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.burst_size) % self.config.address_range
        elif self.config.traffic_pattern.value == "stride":
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.stride_value) % self.config.address_range
        elif self.config.traffic_pattern.value == "hot_spot":
            if random.random() < 0.8:  # 80% access hot spot
                addr = random.randint(0, self.config.address_range // 10)
            else:
                addr = random.randint(0, self.config.address_range - 1)
        else:  # scatter
            addr = random.randint(0, self.config.address_range - 1)

        # Align address
        addr = addr & ~0x3F  # 64-byte alignment

        # Select channel
        channel_id = self.channel_selector.select_channel(addr, self.config.burst_size)
        self.channel_selector.record_request(channel_id)

        # Generate read or write request
        is_read = random.random() < self.config.read_ratio
        req = HBMRequest(addr=addr, length=self.config.burst_size, is_read=is_read)

        # Set channel info from address decoder logic
        req.channel_id = channel_id

        requests.append(req)
        return requests

    def get_channel_stats(self) -> Dict[int, ChannelStats]:
        """Get statistics per channel

        Returns:
            Dict mapping channel_id to ChannelStats
        """
        loads = self.channel_selector.get_channel_load()
        stats = {}
        for ch in range(self.num_channels):
            stats[ch] = ChannelStats(
                channel_id=ch,
                total_requests=loads[ch]
            )
        return stats


class MultiChannelStats:
    """Multi-channel statistics aggregator"""

    def __init__(self, num_channels: int = 8):
        """Initialize stats aggregator

        Args:
            num_channels: Number of channels to track
        """
        self.num_channels = num_channels
        self.channel_stats: Dict[int, ChannelStats] = {
            i: ChannelStats(channel_id=i) for i in range(num_channels)
        }

    def record_request(self, channel_id: int, is_read: bool):
        """Record a request on a channel

        Args:
            channel_id: Target channel
            is_read: True for read, False for write
        """
        if channel_id not in self.channel_stats:
            self.channel_stats[channel_id] = ChannelStats(channel_id=channel_id)

        stats = self.channel_stats[channel_id]
        stats.total_requests += 1
        if is_read:
            stats.read_requests += 1
        else:
            stats.write_requests += 1

    def record_completion(self, channel_id: int, latency_cycles: int, is_row_hit: bool):
        """Record a completion on a channel

        Args:
            channel_id: Channel that completed
            latency_cycles: Completion latency
            is_row_hit: Whether it was a row hit
        """
        if channel_id not in self.channel_stats:
            self.channel_stats[channel_id] = ChannelStats(channel_id=channel_id)

        stats = self.channel_stats[channel_id]
        stats.total_latency_cycles += latency_cycles
        if is_row_hit:
            stats.row_hits += 1
        else:
            stats.row_misses += 1

    def record_activation(self, channel_id: int):
        """Record an activation on a channel

        Args:
            channel_id: Channel that activated
        """
        if channel_id not in self.channel_stats:
            self.channel_stats[channel_id] = ChannelStats(channel_id=channel_id)

        self.channel_stats[channel_id].activations += 1

    def get_per_channel_stats(self) -> Dict[int, ChannelStats]:
        """Get statistics for all channels

        Returns:
            Dict mapping channel_id to ChannelStats
        """
        return dict(self.channel_stats)

    def get_load_balance_score(self) -> float:
        """Calculate load balance score (0-1, 1=perfect balance)

        Returns:
            Load balance score
        """
        if not self.channel_stats:
            return 0.0

        requests = [s.total_requests for s in self.channel_stats.values()]
        if sum(requests) == 0:
            return 1.0

        avg = sum(requests) / len(requests)
        if avg == 0:
            return 1.0

        # Calculate coefficient of variation
        variance = sum((x - avg) ** 2 for x in requests) / len(requests)
        cv = (variance ** 0.5) / avg

        # Convert to 0-1 score (lower CV = better balance)
        # CV=0 means perfect balance, CV=1 means high imbalance
        return max(0.0, 1.0 - min(1.0, cv))

    def get_summary(self) -> Dict:
        """Get summary statistics

        Returns:
            Dict with summary stats
        """
        total_requests = sum(s.total_requests for s in self.channel_stats.values())
        total_reads = sum(s.read_requests for s in self.channel_stats.values())
        total_writes = sum(s.write_requests for s in self.channel_stats.values())
        total_activations = sum(s.activations for s in self.channel_stats.values())

        return {
            'total_requests': total_requests,
            'total_reads': total_reads,
            'total_writes': total_writes,
            'total_activations': total_activations,
            'load_balance_score': self.get_load_balance_score(),
            'per_channel': {
                ch: {
                    'requests': stats.total_requests,
                    'hit_rate': stats.hit_rate,
                    'avg_latency': stats.avg_latency,
                }
                for ch, stats in self.channel_stats.items()
            }
        }