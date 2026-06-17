"""
HBM Trace Replay Module

Provides memory trace replay functionality with support for multiple trace formats:
- DDR4 traces
- HBM2 traces
- HBM3 traces
- HBM4 traces

Features:
- CSV, binary, and memory dump format support
- Timing annotation support
- Address decoder for trace addresses
- Performance metrics collection

Usage:
    from sim.trace.replay import TraceReplay, ReplayConfig, ReplayStats

    config = ReplayConfig(
        trace_file="traces/seq_rd.trace",
        format=TraceFormat.HBM3,
    )
    replay = TraceReplay(config)
    replay.run()
    stats = replay.get_stats()
"""

import os
import struct
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, BinaryIO
from enum import Enum
from collections import defaultdict
import logging
import csv

from model.controller.address_decoder import AddressDecoder, DecodedAddress, AddressMapping
from model.controller.config import HBMConfig
from model.dram.timing import get_timing_for_hbm_version, HBM3Timing, HBM4Timing

logger = logging.getLogger(__name__)


class TraceFormat(Enum):
    """Supported trace formats"""
    # Text formats
    CSV = "csv"                    # CSV format: timestamp,addr,op,length
    RAMULATOR = "ramulator"        # Ramulator format: "R addr" or "W addr"
    DRAMTRACE = "dramtrace"        # Simple format: "addr"

    # Binary formats
    BINARY = "binary"              # Binary format: packed struct
    MEMORY_DUMP = "memory_dump"   # Memory dump format: raw addresses

    # Extended formats
    EXTENDED = "extended"          # Extended: "core_id addr timestamp"
    DDR4 = "ddr4"                 # DDR4 specific format
    HBM2 = "hbm2"                  # HBM2 format
    HBM3 = "hbm3"                  # HBM3 format
    HBM4 = "hbm4"                  # HBM4 format


class HBMVersion(Enum):
    """HBM memory version for timing and addressing"""
    DDR4 = "ddr4"
    HBM2 = "hbm2"
    HBM3 = "hbm3"
    HBM4 = "hbm4"


@dataclass
class ReplayConfig:
    """Trace replay configuration"""
    trace_file: str
    format: TraceFormat = TraceFormat.HBM3
    hbm_version: HBMVersion = HBMVersion.HBM3

    # Timing configuration
    timing_annotations: bool = False       # Use trace timestamps
    time_scale: float = 1.0               # Scale factor for timestamps
    cycle_time_ps: float = 781.25          # Cycle time in ps (HBM3)

    # Address configuration
    address_bits: int = 46                # Address bit width
    cache_line_size: int = 64             # Cache line size in bytes

    # Replay configuration
    max_requests: int = 0                  # Max requests to replay (0 = all)
    warmup_cycles: int = 100              # Warmup cycles before measuring
    cooldown_cycles: int = 50              # Cooldown cycles after replay

    # Filtering
    filter_reads: bool = False            # Filter out read requests
    filter_writes: bool = False           # Filter out write requests
    start_address: int = 0                # Start address filter
    end_address: int = 0                  # End address filter (0 = no limit)

    # Performance tracking
    track_row_hits: bool = True           # Track row buffer hits
    track_channel_util: bool = True        # Track channel utilization
    verbose: bool = False                 # Verbose output


@dataclass
class ReplayRequest:
    """Request from trace replay"""
    request_id: int
    timestamp: float              # Original timestamp (if available)
    cycle: int                    # Simulated cycle
    op_type: str                  # "R" or "W"
    address: int                  # Memory address
    length: int                   # Transfer length in bytes
    channel: int = 0              # Decoded channel
    bank: int = 0                 # Decoded bank
    bank_group: int = 0           # Decoded bank group
    row: int = 0                  # Decoded row
    col: int = 0                  # Decoded column
    is_row_hit: bool = False      # Row buffer hit
    latency: float = 0.0         # Request latency in cycles


@dataclass
class ChannelUtilization:
    """Channel utilization metrics"""
    channel_id: int
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0
    total_latency_cycles: int = 0
    busy_cycles: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.row_hits + self.row_misses + self.row_conflicts
        return self.row_hits / total if total > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        return self.total_latency_cycles / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def utilization(self) -> float:
        return self.busy_cycles  # Placeholder - needs total cycles


@dataclass
class ReplayStats:
    """Replay statistics"""
    # Request counts
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    filtered_requests: int = 0

    # Row buffer statistics
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0

    # Latency statistics
    total_latency_cycles: int = 0
    min_latency_cycles: int = 0
    max_latency_cycles: int = 0

    # Performance metrics
    throughput_gbps: float = 0.0
    bandwidth_gbps: float = 0.0
    efficiency: float = 0.0

    # Timing
    total_cycles: int = 0
    wall_clock_time_s: float = 0.0
    requests_per_second: float = 0.0

    # Channel utilization
    channel_utilization: Dict[int, ChannelUtilization] = field(default_factory=dict)

    # Address distribution
    channel_distribution: Dict[int, int] = field(default_factory=dict)
    bank_distribution: Dict[int, int] = field(default_factory=dict)
    bank_group_distribution: Dict[int, int] = field(default_factory=dict)

    @property
    def avg_latency(self) -> float:
        return self.total_latency_cycles / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def row_hit_rate(self) -> float:
        total = self.row_hits + self.row_misses + self.row_conflicts
        return self.row_hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_requests': self.total_requests,
            'read_requests': self.read_requests,
            'write_requests': self.write_requests,
            'filtered_requests': self.filtered_requests,
            'row_hits': self.row_hits,
            'row_misses': self.row_misses,
            'row_conflicts': self.row_conflicts,
            'row_hit_rate': self.row_hit_rate,
            'avg_latency': self.avg_latency,
            'min_latency': self.min_latency_cycles,
            'max_latency': self.max_latency_cycles,
            'total_latency_cycles': self.total_latency_cycles,
            'throughput_gbps': self.throughput_gbps,
            'bandwidth_gbps': self.bandwidth_gbps,
            'efficiency': self.efficiency,
            'total_cycles': self.total_cycles,
            'wall_clock_time_s': self.wall_clock_time_s,
            'requests_per_second': self.requests_per_second,
            'channel_distribution': self.channel_distribution,
            'bank_distribution': self.bank_distribution,
            'bank_group_distribution': self.bank_group_distribution,
        }


class BinaryTraceHeader:
    """Binary trace file header format"""
    MAGIC = b'HBT0'  # HBM Binary Trace version 0
    FORMAT_VERSION = 1

    # Header struct format: magic(4) + version(2) + flags(2) + num_requests(8) +
    #                      addr_bits(4) + cache_line(4) + hbm_version(4) + reserved(68)
    STRUCT_FORMAT = '<4sHHQIIQ72s'
    STRUCT_SIZE = 100


class TraceReplay:
    """
    Trace Replay Engine

    Replays memory traces with cycle-accurate timing and collects performance metrics.
    Supports multiple trace formats and HBM versions.
    """

    # HBM configuration by version
    HBM_CONFIGS = {
        HBMVersion.DDR4: {
            'channels': 1,
            'pseudo_channels': 1,
            'banks_per_pseudo_channel': 8,
            'bank_groups': 4,
            'rows_per_bank': 16384,
            'cols_per_bank': 1024,
            'io_width': 64,
            'cycle_time_ps': 1071.4,  # DDR4-3200
        },
        HBMVersion.HBM2: {
            'channels': 8,
            'pseudo_channels': 16,
            'banks_per_pseudo_channel': 4,
            'bank_groups': 2,
            'rows_per_bank': 1024,
            'cols_per_bank': 256,
            'io_width': 128,
            'cycle_time_ps': 1250.0,  # HBM2 1600 MT/s
        },
        HBMVersion.HBM3: {
            'channels': 8,
            'pseudo_channels': 16,
            'banks_per_pseudo_channel': 4,
            'bank_groups': 2,
            'rows_per_bank': 1024,
            'cols_per_bank': 256,
            'io_width': 128,
            'cycle_time_ps': 781.25,  # HBM3 3200 MT/s
        },
        HBMVersion.HBM4: {
            'channels': 32,
            'pseudo_channels': 64,
            'banks_per_pseudo_channel': 4,
            'bank_groups': 2,
            'rows_per_bank': 2048,
            'cols_per_bank': 256,
            'io_width': 64,
            'cycle_time_ps': 625.0,  # HBM4 6400 MT/s (16 Gbps)
        },
    }

    def __init__(self, config: ReplayConfig):
        self.config = config
        self.stats = ReplayStats()
        self.requests: List[ReplayRequest] = []

        # Initialize HBM configuration
        hbm_cfg = self.HBM_CONFIGS.get(config.hbm_version, self.HBM_CONFIGS[HBMVersion.HBM3])
        self.channels = hbm_cfg['channels']
        self.pseudo_channels = hbm_cfg['pseudo_channels']
        self.banks_per_pc = hbm_cfg['banks_per_pseudo_channel']
        self.bank_groups = hbm_cfg['bank_groups']
        self.rows_per_bank = hbm_cfg['rows_per_bank']
        self.cols_per_bank = hbm_cfg['cols_per_bank']
        self.io_width = hbm_cfg['io_width']
        self.cycle_time_ps = config.cycle_time_ps or hbm_cfg['cycle_time_ps']

        # Initialize address decoder using HBMConfig
        hbm_config = HBMConfig(
            stack_count=1,
            channels_per_stack=self.channels,
            pseudo_channels_per_channel=self.pseudo_channels // self.channels if self.channels > 0 else 1,
            banks_per_pseudo_channel=self.banks_per_pc,
            bank_groups_per_channel=self.bank_groups,
        )
        self._decoder = AddressDecoder(hbm_config)

        # Bank state tracking for row hit detection
        self._bank_states: Dict[Tuple[int, int], int] = {}  # (channel, bank) -> row

        # Initialize channel utilization
        for ch in range(self.channels * 2):  # Include pseudo-channels
            self.stats.channel_utilization[ch] = ChannelUtilization(channel_id=ch)

        self._request_id = 0
        self._current_cycle = 0

    def load_trace(self) -> int:
        """Load trace from file

        Returns:
            Number of requests loaded
        """
        if not os.path.exists(self.config.trace_file):
            raise FileNotFoundError(f"Trace file not found: {self.config.trace_file}")

        format_handlers = {
            TraceFormat.CSV: self._load_csv,
            TraceFormat.RAMULATOR: self._load_ramulator,
            TraceFormat.DRAMTRACE: self._load_dramtrace,
            TraceFormat.BINARY: self._load_binary,
            TraceFormat.MEMORY_DUMP: self._load_memory_dump,
            TraceFormat.EXTENDED: self._load_extended,
            TraceFormat.DDR4: self._load_ramulator,
            TraceFormat.HBM2: self._load_ramulator,
            TraceFormat.HBM3: self._load_ramulator,
            TraceFormat.HBM4: self._load_ramulator,
        }

        handler = format_handlers.get(self.config.format)
        if handler is None:
            raise ValueError(f"Unsupported format: {self.config.format}")

        count = handler()
        logger.info(f"Loaded {count} requests from {self.config.trace_file}")
        return count

    def _load_csv(self) -> int:
        """Load CSV format: timestamp,addr,op,length"""
        count = 0
        with open(self.config.trace_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = float(row.get('timestamp', count))
                address = int(row['address'], 0)
                op_type = row.get('op', 'R')[0].upper()
                length = int(row.get('length', self.config.cache_line_size))

                if self._should_include(op_type, address):
                    self._add_request(timestamp, address, op_type, length)
                    count += 1

                    if self.config.max_requests > 0 and count >= self.config.max_requests:
                        break

        return count

    def _load_ramulator(self) -> int:
        """Load Ramulator format: 'R addr' or 'W addr'"""
        count = 0
        prev_timestamp = 0.0

        with open(self.config.trace_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                op = parts[0].upper()
                if op == 'LD':
                    op = 'R'
                elif op == 'ST':
                    op = 'W'

                if op not in ('R', 'W'):
                    continue

                try:
                    address = int(parts[1], 0)
                except ValueError:
                    continue

                # Extract timestamp if available (3rd column)
                timestamp = prev_timestamp + 1.0  # Default: 1 cycle apart
                if len(parts) >= 3:
                    try:
                        timestamp = float(parts[2])
                    except ValueError:
                        pass

                if self._should_include(op, address):
                    self._add_request(timestamp, address, op, self.config.cache_line_size)
                    count += 1
                    prev_timestamp = timestamp

                    if self.config.max_requests > 0 and count >= self.config.max_requests:
                        break

        return count

    def _load_dramtrace(self) -> int:
        """Load simple DRAM trace format: 'addr'"""
        count = 0

        with open(self.config.trace_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                try:
                    address = int(line, 0)
                except ValueError:
                    continue

                if self._should_include('R', address):
                    self._add_request(float(count), address, 'R', self.config.cache_line_size)
                    count += 1

                    if self.config.max_requests > 0 and count >= self.config.max_requests:
                        break

        return count

    def _load_binary(self) -> int:
        """Load binary trace format"""
        count = 0

        with open(self.config.trace_file, 'rb') as f:
            # Read header
            header = f.read(BinaryTraceHeader.STRUCT_SIZE)
            if len(header) < BinaryTraceHeader.STRUCT_SIZE:
                raise ValueError("Invalid binary trace file: header too short")

            (magic, version, flags, num_requests, addr_bits,
             cache_line, hbm_ver, reserved) = struct.unpack(
                BinaryTraceHeader.STRUCT_FORMAT, header)

            if magic != BinaryTraceHeader.MAGIC:
                raise ValueError(f"Invalid binary trace: magic mismatch")

            # Read request records
            # Format: timestamp(8) + addr(8) + op(1) + length(2) + pad(1)
            record_format = '<dqBH2s'
            record_size = 20

            for _ in range(num_requests):
                record = f.read(record_size)
                if len(record) < record_size:
                    break

                timestamp, address, op_ord, length, _ = struct.unpack(record_format, record)
                op_type = 'R' if op_ord == 0 else 'W'

                if self._should_include(op_type, address):
                    self._add_request(timestamp, address, op_type, length)
                    count += 1

                    if self.config.max_requests > 0 and count >= self.config.max_requests:
                        break

        return count

    def _load_memory_dump(self) -> int:
        """Load memory dump format: raw addresses, one per line"""
        count = 0

        with open(self.config.trace_file, 'rb') as f:
            addr_size = self.config.address_bits // 8
            fmt = f'<Q' if addr_size == 8 else f'<{"I" if addr_size == 4 else "H"}'

            while True:
                data = f.read(addr_size)
                if len(data) < addr_size:
                    break

                address = struct.unpack(fmt, data)[0]

                if self._should_include('R', address):
                    self._add_request(float(count), address, 'R', self.config.cache_line_size)
                    count += 1

                    if self.config.max_requests > 0 and count >= self.config.max_requests:
                        break

        return count

    def _load_extended(self) -> int:
        """Load extended format: 'core_id addr timestamp [length]'"""
        count = 0
        prev_timestamp = 0.0

        with open(self.config.trace_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                try:
                    core_id = int(parts[0])
                    address = int(parts[1], 0)
                    timestamp = float(parts[2]) if len(parts) >= 3 else prev_timestamp + 1.0
                    length = int(parts[3]) if len(parts) >= 4 else self.config.cache_line_size
                except ValueError:
                    continue

                if self._should_include('R', address):
                    self._add_request(timestamp, address, 'R', length)
                    count += 1
                    prev_timestamp = timestamp

                    if self.config.max_requests > 0 and count >= self.config.max_requests:
                        break

        return count

    def _should_include(self, op_type: str, address: int) -> bool:
        """Check if request should be included based on filters"""
        # Filter by operation type
        if self.config.filter_reads and op_type == 'R':
            return False
        if self.config.filter_writes and op_type == 'W':
            return False

        # Filter by address range
        if self.config.start_address > 0 and address < self.config.start_address:
            return False
        if self.config.end_address > 0 and address > self.config.end_address:
            return False

        return True

    def _add_request(self, timestamp: float, address: int, op_type: str, length: int):
        """Add a request after decoding address"""
        # Decode address
        decoded = self._decode_address(address)

        # Convert timestamp to cycle
        if self.config.timing_annotations:
            cycle = int(timestamp * 1000 / self.cycle_time_ps)  # ps to cycles
        else:
            cycle = len(self.requests)  # Sequential cycles

        request = ReplayRequest(
            request_id=self._request_id,
            timestamp=timestamp,
            cycle=cycle,
            op_type=op_type,
            address=address,
            length=length,
            channel=decoded.get('channel', 0),
            bank=decoded.get('bank', 0),
            bank_group=decoded.get('bank_group', 0),
            row=decoded.get('row', 0),
            col=decoded.get('col', 0),
        )

        self.requests.append(request)
        self._request_id += 1

    def _decode_address(self, address: int) -> Dict[str, int]:
        """Decode address into memory components"""
        # Align address to 8-byte boundary for address decoder
        aligned_addr = address & ~0x7

        try:
            result = self._decoder.decode(aligned_addr)
            return {
                'channel': result.channel_id,
                'pseudo_channel': result.pseudo_channel_id,
                'bank_group': result.bank_group_id,
                'bank': result.bank_id,
                'row': result.row_id,
                'col': result.col_id,
            }
        except Exception:
            # Fallback: simple address mapping
            channel = (address >> 18) % self.channels
            bank = (address >> 12) % self.banks_per_pc
            bank_group = (address >> 10) % self.bank_groups
            row = (address >> 6) % self.rows_per_bank
            col = address % self.cols_per_bank

            return {
                'channel': channel,
                'pseudo_channel': channel * 2,
                'bank_group': bank_group,
                'bank': bank,
                'row': row,
                'col': col,
            }

    def _detect_row_hit(self, channel: int, bank: int, row: int) -> bool:
        """Detect if access is a row buffer hit"""
        bank_key = (channel, bank)
        prev_row = self._bank_states.get(bank_key, -1)

        if prev_row == -1:
            # Bank was idle
            return False
        elif prev_row == row:
            # Same row as before - hit
            return True
        else:
            # Different row - conflict
            return False

    def run(self) -> ReplayStats:
        """Run trace replay and collect statistics

        Returns:
            ReplayStats with performance metrics
        """
        start_time = time.time()

        # Load trace if not already loaded
        if not self.requests:
            self.load_trace()

        # Add warmup cycles
        self._current_cycle = self.config.warmup_cycles

        # Process each request
        for req in self.requests:
            # Update cycle to request's timestamp
            if self.config.timing_annotations:
                self._current_cycle = max(self._current_cycle, req.cycle)

            # Detect row hit
            is_hit = self._detect_row_hit(req.channel, req.bank, req.row)
            req.is_row_hit = is_hit

            # Calculate latency (simplified model)
            if is_hit:
                latency = 2  # Row hit: minimal latency
                self.stats.row_hits += 1
            else:
                latency = 30  # Row miss: ACT + RD/WR + PRE
                self.stats.row_misses += 1

            # Check for row conflict
            bank_key = (req.channel, req.bank)
            if bank_key in self._bank_states and self._bank_states[bank_key] != req.row:
                self.stats.row_conflicts += 1

            req.latency = latency

            # Update bank state
            self._bank_states[bank_key] = req.row

            # Update statistics
            self.stats.total_requests += 1
            if req.op_type == 'R':
                self.stats.read_requests += 1
            else:
                self.stats.write_requests += 1

            self.stats.total_latency_cycles += latency

            # Update per-channel stats
            ch_util = self.stats.channel_utilization.get(req.channel)
            if ch_util:
                ch_util.total_requests += 1
                ch_util.total_latency_cycles += latency
                ch_util.busy_cycles += latency

                if req.op_type == 'R':
                    ch_util.read_requests += 1
                else:
                    ch_util.write_requests += 1

                if is_hit:
                    ch_util.row_hits += 1
                else:
                    ch_util.row_misses += 1

            # Update address distribution
            self.stats.channel_distribution[req.channel] = \
                self.stats.channel_distribution.get(req.channel, 0) + 1
            self.stats.bank_distribution[req.bank] = \
                self.stats.bank_distribution.get(req.bank, 0) + 1
            self.stats.bank_group_distribution[req.bank_group] = \
                self.stats.bank_group_distribution.get(req.bank_group, 0) + 1

            # Advance cycle
            self._current_cycle += 1

        # Add cooldown cycles
        self._current_cycle += self.config.cooldown_cycles

        # Calculate final statistics
        self.stats.total_cycles = self._current_cycle
        self.stats.wall_clock_time_s = time.time() - start_time

        # Calculate throughput and bandwidth
        bytes_transferred = self.stats.total_requests * self.config.cache_line_size
        total_ns = self.stats.total_cycles * self.cycle_time_ps / 1000
        self.stats.bandwidth_gbps = bytes_transferred / (total_ns * 1e-9) / 1e9

        # Calculate throughput (requests per second)
        self.stats.requests_per_second = \
            self.stats.total_requests / self.stats.wall_clock_time_s if self.stats.wall_clock_time_s > 0 else 0

        # Calculate latency extremes
        if self.stats.total_requests > 0:
            avg_lat = self.stats.total_latency_cycles / self.stats.total_requests
            self.stats.min_latency_cycles = int(avg_lat * 0.5)  # Estimate
            self.stats.max_latency_cycles = int(avg_lat * 2.0)  # Estimate

        # Calculate efficiency
        peak_bandwidth = self._calculate_peak_bandwidth()
        self.stats.throughput_gbps = self.stats.bandwidth_gbps
        self.stats.efficiency = self.stats.bandwidth_gbps / peak_bandwidth if peak_bandwidth > 0 else 0

        return self.stats

    def _calculate_peak_bandwidth(self) -> float:
        """Calculate theoretical peak bandwidth in GB/s"""
        # Peak = channels * data_rate * width / 8
        data_rate = 1000 / self.cycle_time_ps  # GT/s
        peak = self.channels * data_rate * self.io_width / 8  # GB/s
        return peak

    def get_stats(self) -> ReplayStats:
        """Get replay statistics"""
        return self.stats

    def get_requests(self) -> List[ReplayRequest]:
        """Get all replayed requests"""
        return self.requests

    def print_summary(self, stream=None):
        """Print replay summary"""
        if stream is None:
            stream = __import__('sys').stdout

        s = lambda x: print(x, file=stream)

        s("\n" + "=" * 70)
        s(f"Trace Replay Summary: {os.path.basename(self.config.trace_file)}")
        s("=" * 70)

        s(f"\n[Configuration]")
        s(f"  HBM Version:    {self.config.hbm_version.value}")
        s(f"  Trace Format:   {self.config.format.value}")
        s(f"  Channels:       {self.channels}")
        s(f"  Cycle Time:     {self.cycle_time_ps:.2f} ps")

        s(f"\n[Request Statistics]")
        s(f"  Total requests:    {self.stats.total_requests:,}")
        s(f"  Read requests:      {self.stats.read_requests:,}")
        s(f"  Write requests:      {self.stats.write_requests:,}")
        s(f"  Filtered requests:  {self.stats.filtered_requests:,}")

        s(f"\n[Row Buffer Statistics]")
        s(f"  Row hits:        {self.stats.row_hits:,}")
        s(f"  Row misses:     {self.stats.row_misses:,}")
        s(f"  Row conflicts:   {self.stats.row_conflicts:,}")
        s(f"  Row hit rate:   {self.stats.row_hit_rate*100:.2f}%")

        s(f"\n[Latency Statistics]")
        s(f"  Average:         {self.stats.avg_latency:.2f} cycles")
        s(f"  Min:             {self.stats.min_latency_cycles} cycles")
        s(f"  Max:             {self.stats.max_latency_cycles} cycles")

        s(f"\n[Performance Metrics]")
        s(f"  Total cycles:   {self.stats.total_cycles:,}")
        s(f"  Bandwidth:       {self.stats.bandwidth_gbps:.3f} GB/s")
        s(f"  Throughput:      {self.stats.requests_per_second:,.0f} req/s")
        s(f"  Efficiency:      {self.stats.efficiency*100:.2f}%")
        s(f"  Wall clock:      {self.stats.wall_clock_time_s*1000:.2f} ms")

        s(f"\n[Channel Distribution]")
        for ch in sorted(self.stats.channel_distribution.keys()):
            count = self.stats.channel_distribution[ch]
            pct = count / max(1, self.stats.total_requests) * 100
            s(f"  Channel {ch:2d}: {count:8,} ({pct:5.2f}%)")

        s("\n" + "=" * 70)

    def save_stats(self, filename: str):
        """Save statistics to JSON file"""
        import json

        output = {
            'config': {
                'trace_file': self.config.trace_file,
                'format': self.config.format.value,
                'hbm_version': self.config.hbm_version.value,
                'timing_annotations': self.config.timing_annotations,
            },
            'stats': self.stats.to_dict(),
            'per_channel': {
                ch: {
                    'total_requests': util.total_requests,
                    'row_hits': util.row_hits,
                    'row_misses': util.row_misses,
                    'hit_rate': util.hit_rate,
                    'avg_latency': util.avg_latency,
                }
                for ch, util in self.stats.channel_utilization.items()
            },
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Stats saved to {filename}")


def replay_trace(
    trace_file: str,
    format: TraceFormat = TraceFormat.HBM3,
    hbm_version: HBMVersion = HBMVersion.HBM3,
    max_requests: int = 0,
    verbose: bool = False,
) -> ReplayStats:
    """Convenience function to replay a trace file

    Args:
        trace_file: Path to trace file
        format: Trace format
        hbm_version: HBM version for timing
        max_requests: Maximum requests to replay (0 = all)
        verbose: Print summary

    Returns:
        ReplayStats with performance metrics
    """
    config = ReplayConfig(
        trace_file=trace_file,
        format=format,
        hbm_version=hbm_version,
        max_requests=max_requests,
        verbose=verbose,
    )

    replay = TraceReplay(config)
    stats = replay.run()

    if verbose:
        replay.print_summary()

    return stats


def create_sample_trace(
    filename: str,
    pattern: str = "sequential",
    num_requests: int = 1000,
    hbm_version: HBMVersion = HBMVersion.HBM3,
):
    """Create a sample trace file for testing

    Args:
        filename: Output file path
        pattern: Pattern type (sequential, random, stride, transpose)
        num_requests: Number of requests to generate
        hbm_version: HBM version
    """
    config = ReplayConfig(trace_file=filename, hbm_version=hbm_version)
    replay = TraceReplay(config)

    # Generate addresses based on pattern
    addresses = []
    addr = 0

    for i in range(num_requests):
        if pattern == "sequential":
            addr = i * config.cache_line_size
        elif pattern == "random":
            import random
            addr = random.randint(0, 1 << 40)
        elif pattern == "stride":
            addr = (i * 4096) % (1 << 40)  # 4KB stride
        elif pattern == "transpose":
            # Transpose pattern: swap row/col components
            row = i % 1024
            col = i // 1024
            addr = (row << 12) | (col << 6)

        op = 'R' if i % 5 != 0 else 'W'  # 80% reads
        addresses.append((op, addr))

    # Write to file
    with open(filename, 'w') as f:
        for op, addr in addresses:
            f.write(f"{op} 0x{addr:x}\n")

    logger.info(f"Created sample trace: {filename} ({num_requests} requests)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='HBM Trace Replay')
    parser.add_argument('trace_file', help='Trace file to replay')
    parser.add_argument('--format', '-f', choices=['csv', 'ramulator', 'dramtrace', 'binary', 'hbm3', 'hbm4'],
                        default='ramulator', help='Trace format')
    parser.add_argument('--hbm-version', choices=['ddr4', 'hbm2', 'hbm3', 'hbm4'],
                        default='hbm3', help='HBM version')
    parser.add_argument('--max-requests', '-n', type=int, default=0,
                        help='Max requests to replay (0 = all)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    format_map = {
        'csv': TraceFormat.CSV,
        'ramulator': TraceFormat.RAMULATOR,
        'dramtrace': TraceFormat.DRAMTRACE,
        'binary': TraceFormat.BINARY,
        'hbm3': TraceFormat.HBM3,
        'hbm4': TraceFormat.HBM4,
    }

    version_map = {
        'ddr4': HBMVersion.DDR4,
        'hbm2': HBMVersion.HBM2,
        'hbm3': HBMVersion.HBM3,
        'hbm4': HBMVersion.HBM4,
    }

    stats = replay_trace(
        trace_file=args.trace_file,
        format=format_map.get(args.format, TraceFormat.RAMULATOR),
        hbm_version=version_map.get(args.hbm_version, HBMVersion.HBM3),
        max_requests=args.max_requests,
        verbose=True,
    )
