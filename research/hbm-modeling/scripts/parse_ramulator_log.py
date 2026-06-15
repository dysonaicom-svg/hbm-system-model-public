#!/usr/bin/env python3
"""
Ramulator2 Log Parser
Parses Ramulator2 output logs to extract performance metrics.

Extracts:
- row_hits, row_misses, row_conflicts
- avg_latency
- memory_cycles
- channel-level statistics

Supports multi-channel output format.
"""

import re
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class ChannelStats:
    """Per-channel statistics from Ramulator2 output"""
    channel_id: int = 0

    # Request counts
    num_read_reqs: int = 0
    num_write_reqs: int = 0
    total_requests: int = 0

    # Row buffer statistics
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0

    # Read-specific stats
    read_row_hits: int = 0
    read_row_misses: int = 0
    read_row_conflicts: int = 0

    # Write-specific stats
    write_row_hits: int = 0
    write_row_misses: int = 0
    write_row_conflicts: int = 0

    # Latency
    avg_read_latency: float = 0.0
    total_read_latency: int = 0

    # Queue statistics
    queue_len_avg: float = 0.0
    read_queue_len_avg: float = 0.0
    write_queue_len_avg: float = 0.0

    # Row hit rate
    row_hit_rate: float = 0.0

    def compute_hit_rate(self) -> float:
        """Compute row hit rate from collected stats"""
        total = self.row_hits + self.row_misses + self.row_conflicts
        if total > 0:
            self.row_hit_rate = self.row_hits / total
        return self.row_hit_rate


@dataclass
class RamulatorLogResult:
    """Complete parsed results from a Ramulator2 log file"""
    log_file: str = ""
    trace_file: str = ""
    num_requests: int = 0  # Original trace requests (from "Loaded X lines")

    # Memory system level stats
    total_read_requests: int = 0
    total_write_requests: int = 0
    memory_system_cycles: int = 0

    # DRAM configuration
    dram_impl: str = ""
    addr_mapper_impl: str = ""

    # Per-channel statistics
    channels: Dict[int, ChannelStats] = field(default_factory=dict)

    # Aggregated statistics
    total_row_hits: int = 0
    total_row_misses: int = 0
    total_row_conflicts: int = 0
    total_avg_latency: float = 0.0
    aggregated_hit_rate: float = 0.0

    def compute_aggregates(self) -> None:
        """Compute aggregated statistics across all channels"""
        self.total_row_hits = sum(c.row_hits for c in self.channels.values())
        self.total_row_misses = sum(c.row_misses for c in self.channels.values())
        self.total_row_conflicts = sum(c.row_conflicts for c in self.channels.values())

        total = self.total_row_hits + self.total_row_misses + self.total_row_conflicts
        if total > 0:
            self.aggregated_hit_rate = self.total_row_hits / total

        # Compute weighted average latency (Ramulator2 provides avg_read_latency directly)
        num_channels = len(self.channels)
        if num_channels > 0:
            total_latency = sum(c.avg_read_latency for c in self.channels.values())
            self.total_avg_latency = total_latency / num_channels

    def get_trace_request_count(self) -> int:
        """Get the number of requests from the original trace.

        This returns the "Loaded X lines" count, which is the actual number
        of requests in the input trace (as opposed to HBM internal burst
        requests which can be much higher due to burst splitting).
        """
        return self.num_requests

    def get_per_channel_stats(self, channel_id: int = 0) -> Optional[ChannelStats]:
        """Get statistics for a specific channel.

        Args:
            channel_id: Channel ID (default: 0)

        Returns:
            ChannelStats for the specified channel, or None if not found
        """
        return self.channels.get(channel_id)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "log_file": self.log_file,
            "trace_file": self.trace_file,
            "num_requests": self.num_requests,
            "total_read_requests": self.total_read_requests,
            "total_write_requests": self.total_write_requests,
            "memory_system_cycles": self.memory_system_cycles,
            "dram_impl": self.dram_impl,
            "addr_mapper_impl": self.addr_mapper_impl,
            "total_row_hits": self.total_row_hits,
            "total_row_misses": self.total_row_misses,
            "total_row_conflicts": self.total_row_conflicts,
            "aggregated_hit_rate": self.aggregated_hit_rate,
            "total_avg_latency": self.total_avg_latency,
            "channels": {
                ch_id: {
                    "channel_id": c.channel_id,
                    "total_requests": c.total_requests,
                    "row_hits": c.row_hits,
                    "row_misses": c.row_misses,
                    "row_conflicts": c.row_conflicts,
                    "row_hit_rate": c.row_hit_rate,
                    "avg_read_latency": c.avg_read_latency,
                    "queue_len_avg": c.queue_len_avg,
                }
                for ch_id, c in self.channels.items()
            }
        }

    def summary(self) -> str:
        """Generate human-readable summary"""
        lines = [
            f"Ramulator2 Log: {os.path.basename(self.log_file)}",
            f"Trace: {self.trace_file}",
            f"DRAM: {self.dram_impl}, Mapper: {self.addr_mapper_impl}",
            f"",
            f"[Overall Statistics]",
            f"  Total Requests:    {self.num_requests:,}",
            f"  Read Requests:     {self.total_read_requests:,}",
            f"  Write Requests:    {self.total_write_requests:,}",
            f"  Memory Cycles:     {self.memory_system_cycles:,}",
            f"",
            f"[Row Buffer Performance]",
            f"  Row Hits:          {self.total_row_hits:,}",
            f"  Row Misses:        {self.total_row_misses:,}",
            f"  Row Conflicts:      {self.total_row_conflicts:,}",
            f"  Hit Rate:          {self.aggregated_hit_rate*100:.2f}%",
            f"  Avg Latency:        {self.total_avg_latency:.2f} cycles",
        ]

        if self.channels:
            lines.append("")
            lines.append("[Per-Channel Statistics]")
            for ch_id in sorted(self.channels.keys()):
                c = self.channels[ch_id]
                lines.append(
                    f"  Channel {ch_id}: hits={c.row_hits:,} misses={c.row_misses:,} "
                    f"conflicts={c.row_conflicts:,} hit_rate={c.row_hit_rate*100:.2f}%"
                )

        return "\n".join(lines)


class RamulatorLogParser:
    """Parser for Ramulator2 output logs"""

    # Patterns for parsing Ramulator2 output
    PATTERN_TRACE_FILE = re.compile(r'\[Ramulator::LoadStoreTrace\].*?Loading trace file (.+?) \.\.\.')
    PATTERN_TRACE_LOADED = re.compile(r'\[Ramulator::LoadStoreTrace\].*?Loaded (\d+) lines')

    # Memory system level patterns
    PATTERN_TOTAL_READ = re.compile(r'total_num_read_requests:\s*(\d+)')
    PATTERN_TOTAL_WRITE = re.compile(r'total_num_write_requests:\s*(\d+)')
    PATTERN_MEMORY_CYCLES = re.compile(r'memory_system_cycles:\s*(\d+)')

    # DRAM config patterns
    PATTERN_DRAM_IMPL = re.compile(r'DRAM:\s+impl:\s*(\S+)')
    PATTERN_ADDR_MAPPER = re.compile(r'AddrMapper:\s+impl:\s*(\S+)')

    # Channel-level patterns (note: Ramulator2 uses _N suffix like row_hits_0:)
    PATTERN_CHANNEL = re.compile(r'id:\s*(Channel \d+|Channel-\d+)')
    PATTERN_ROW_HITS = re.compile(r'row_hits_\d+:\s*(\d+)')
    PATTERN_ROW_MISSES = re.compile(r'row_misses_\d+:\s*(\d+)')
    PATTERN_ROW_CONFLICTS = re.compile(r'row_conflicts_\d+:\s*(\d+)')

    # Read-specific patterns
    PATTERN_READ_ROW_HITS = re.compile(r'read_row_hits_\d+:\s*(\d+)')
    PATTERN_READ_ROW_MISSES = re.compile(r'read_row_misses_\d+:\s*(\d+)')
    PATTERN_READ_ROW_CONFLICTS = re.compile(r'read_row_conflicts_\d+:\s*(\d+)')

    # Write-specific patterns
    PATTERN_WRITE_ROW_HITS = re.compile(r'write_row_hits_\d+:\s*(\d+)')
    PATTERN_WRITE_ROW_MISSES = re.compile(r'write_row_misses_\d+:\s*(\d+)')
    PATTERN_WRITE_ROW_CONFLICTS = re.compile(r'write_row_conflicts_\d+:\s*(\d+)')

    # Latency patterns
    PATTERN_AVG_READ_LATENCY = re.compile(r'avg_read_latency_\d+:\s*([\d.]+)')
    PATTERN_READ_LATENCY = re.compile(r'read_latency_\d+:\s*(\d+)')

    # Queue patterns
    PATTERN_QUEUE_LEN_AVG = re.compile(r'queue_len_avg_\d+:\s*([\d.]+)')
    PATTERN_READ_QUEUE_LEN_AVG = re.compile(r'read_queue_len_avg_\d+:\s*([\d.]+)')
    PATTERN_WRITE_QUEUE_LEN_AVG = re.compile(r'write_queue_len_avg_\d+:\s*([\d.]+)')

    # Request count patterns
    PATTERN_NUM_READ = re.compile(r'num_read_reqs_\d+:\s*(\d+)')
    PATTERN_NUM_WRITE = re.compile(r'num_write_reqs_\d+:\s*(\d+)')

    def __init__(self, log_file: str):
        self.log_file = log_file
        self.result: Optional[RamulatorLogResult] = None

    def parse(self) -> RamulatorLogResult:
        """Parse the log file and return structured results"""
        if not os.path.exists(self.log_file):
            raise FileNotFoundError(f"Log file not found: {self.log_file}")

        with open(self.log_file, 'r') as f:
            content = f.read()

        result = RamulatorLogResult(log_file=self.log_file)

        # Parse trace file path
        match = self.PATTERN_TRACE_FILE.search(content)
        if match:
            result.trace_file = match.group(1)

        # Parse number of requests loaded
        match = self.PATTERN_TRACE_LOADED.search(content)
        if match:
            result.num_requests = int(match.group(1))

        # Parse memory system level stats
        result.total_read_requests = self._extract_int(content, self.PATTERN_TOTAL_READ)
        result.total_write_requests = self._extract_int(content, self.PATTERN_TOTAL_WRITE)
        result.memory_system_cycles = self._extract_int(content, self.PATTERN_MEMORY_CYCLES)

        # Parse DRAM config
        result.dram_impl = self._extract_str(content, self.PATTERN_DRAM_IMPL)
        result.addr_mapper_impl = self._extract_str(content, self.PATTERN_ADDR_MAPPER)

        # Parse per-channel statistics
        result.channels = self._parse_channels(content)

        # Compute aggregated statistics
        result.compute_aggregates()

        self.result = result
        return result

    def _parse_channels(self, content: str) -> Dict[int, ChannelStats]:
        """Parse per-channel statistics from log content"""
        channels = {}

        # Split content into channel blocks
        # Each channel block starts with "Controller:" section
        lines = content.split('\n')
        current_channel_id = 0
        current_channel_lines = []

        for line in lines:
            # Check if this line starts a new Controller section
            if 'Controller:' in line:
                # Save previous channel if exists and has data
                if current_channel_lines:
                    channel_stats = self._parse_channel_block('\n'.join(current_channel_lines), current_channel_id)
                    if channel_stats:
                        channels[current_channel_id] = channel_stats
                    current_channel_lines = []

            # Check for channel ID
            match = self.PATTERN_CHANNEL.search(line)
            if match:
                # Extract channel ID
                channel_str = match.group(1)
                if 'Channel-' in channel_str:
                    current_channel_id = int(channel_str.split('-')[1])
                else:
                    current_channel_id = int(channel_str.split()[-1])

            # Collect all lines within Controller section
            if 'Controller:' in line or (current_channel_lines and not line.startswith('[Ramulator')):
                current_channel_lines.append(line)

        # Don't forget the last channel
        if current_channel_lines:
            channel_stats = self._parse_channel_block('\n'.join(current_channel_lines), current_channel_id)
            if channel_stats:
                channels[current_channel_id] = channel_stats

        return channels

    def _parse_channel_block(self, block: str, channel_id: int) -> Optional[ChannelStats]:
        """Parse a single channel block"""
        stats = ChannelStats(channel_id=channel_id)

        # Extract all metrics
        stats.row_hits = self._extract_int(block, self.PATTERN_ROW_HITS)
        stats.row_misses = self._extract_int(block, self.PATTERN_ROW_MISSES)
        stats.row_conflicts = self._extract_int(block, self.PATTERN_ROW_CONFLICTS)

        stats.read_row_hits = self._extract_int(block, self.PATTERN_READ_ROW_HITS)
        stats.read_row_misses = self._extract_int(block, self.PATTERN_READ_ROW_MISSES)
        stats.read_row_conflicts = self._extract_int(block, self.PATTERN_READ_ROW_CONFLICTS)

        stats.write_row_hits = self._extract_int(block, self.PATTERN_WRITE_ROW_HITS)
        stats.write_row_misses = self._extract_int(block, self.PATTERN_WRITE_ROW_MISSES)
        stats.write_row_conflicts = self._extract_int(block, self.PATTERN_WRITE_ROW_CONFLICTS)

        stats.avg_read_latency = self._extract_float(block, self.PATTERN_AVG_READ_LATENCY)
        stats.total_read_latency = self._extract_int(block, self.PATTERN_READ_LATENCY)

        stats.queue_len_avg = self._extract_float(block, self.PATTERN_QUEUE_LEN_AVG)
        stats.read_queue_len_avg = self._extract_float(block, self.PATTERN_READ_QUEUE_LEN_AVG)
        stats.write_queue_len_avg = self._extract_float(block, self.PATTERN_WRITE_QUEUE_LEN_AVG)

        stats.num_read_reqs = self._extract_int(block, self.PATTERN_NUM_READ)
        stats.num_write_reqs = self._extract_int(block, self.PATTERN_NUM_WRITE)
        stats.total_requests = stats.num_read_reqs + stats.num_write_reqs

        # Compute hit rate
        stats.compute_hit_rate()

        return stats

    def _extract_int(self, content: str, pattern: re.Pattern) -> int:
        """Extract integer value using regex pattern"""
        match = pattern.search(content)
        if match:
            return int(match.group(1))
        return 0

    def _extract_float(self, content: str, pattern: re.Pattern) -> float:
        """Extract float value using regex pattern"""
        match = pattern.search(content)
        if match:
            return float(match.group(1))
        return 0.0

    def _extract_str(self, content: str, pattern: re.Pattern) -> str:
        """Extract string value using regex pattern"""
        match = pattern.search(content)
        if match:
            return match.group(1)
        return ""


def parse_log_file(log_file: str) -> RamulatorLogResult:
    """Convenience function to parse a single log file"""
    parser = RamulatorLogParser(log_file)
    return parser.parse()


def parse_directory(log_dir: str, pattern: str = "*.log") -> Dict[str, RamulatorLogResult]:
    """Parse all log files in a directory"""
    import glob

    results = {}
    log_files = glob.glob(os.path.join(log_dir, pattern))

    for log_file in sorted(log_files):
        try:
            result = parse_log_file(log_file)
            results[log_file] = result
        except Exception as e:
            print(f"Error parsing {log_file}: {e}")

    return results


def save_results(result: RamulatorLogResult, output_file: str = None) -> str:
    """Save parsed results to JSON file"""
    import json

    if output_file is None:
        base = os.path.splitext(os.path.basename(result.log_file))[0]
        output_file = f"{base}_parsed.json"

    with open(output_file, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

    return output_file


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python parse_ramulator_log.py <log_file> [output_json]")
        print("  <log_file>: Path to Ramulator2 log file")
        print("  [output_json]: Optional path to save JSON output")
        sys.exit(1)

    log_file = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else None

    # Parse log file
    parser = RamulatorLogParser(log_file)
    result = parser.parse()

    # Print summary
    print(result.summary())

    # Save to JSON if requested
    if output_json:
        save_results(result, output_json)
        print(f"\nResults saved to {output_json}")