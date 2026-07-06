"""
Real-time Performance Monitoring Module

Provides real-time bandwidth and performance monitoring capabilities for HBM systems.
Features:
- Live bandwidth tracking per channel
- Throughput measurement
- Performance metrics aggregation
- Integration with simulator statistics

Usage:
    from model.monitoring.realtime_monitor import RealtimeMonitor

    monitor = RealtimeMonitor(num_channels=32)
    monitor.start()

    # ... run simulation ...

    stats = monitor.get_stats()
    monitor.stop()
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from datetime import datetime
import math


@dataclass
class ChannelMetrics:
    """Per-channel performance metrics"""
    channel_id: int
    bytes_transferred: int = 0
    request_count: int = 0
    read_count: int = 0
    write_count: int = 0
    total_latency_cycles: int = 0
    row_hits: int = 0
    row_misses: int = 0
    max_latency_cycles: int = 0
    min_latency_cycles: int = 0xFFFFFFFF

    @property
    def avg_latency(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_latency_cycles / self.request_count

    @property
    def hit_rate(self) -> float:
        total = self.row_hits + self.row_misses
        if total == 0:
            return 0.0
        return self.row_hits / total

    @property
    def bandwidth_gbps(self) -> float:
        """Calculate bandwidth in GB/s (assuming 16 GT/s per channel)"""
        # 128 bytes per beat, 16 GT/s = 16e9 beats/s
        # Peak per channel = 128 * 16e9 / 1e9 = 2048 GB/s
        if self.bytes_transferred == 0:
            return 0.0
        return self.bytes_transferred * 8e-9  # bytes to GB


@dataclass
class SystemMetrics:
    """Aggregate system performance metrics"""
    total_bytes: int = 0
    total_requests: int = 0
    total_reads: int = 0
    total_writes: int = 0
    total_latency_cycles: int = 0
    peak_bandwidth_gbps: float = 0.0
    avg_latency_cycles: float = 0.0
    efficiency_percent: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def update_from_channels(self, channels: Dict[int, ChannelMetrics], peak_bw_per_ch: float = 2048.0):
        """Update aggregate metrics from per-channel data"""
        self.total_bytes = sum(ch.bytes_transferred for ch in channels.values())
        self.total_requests = sum(ch.request_count for ch in channels.values())
        self.total_reads = sum(ch.read_count for ch in channels.values())
        self.total_writes = sum(ch.write_count for ch in channels.values())
        self.total_latency_cycles = sum(ch.total_latency_cycles for ch in channels.values())

        if self.total_requests > 0:
            self.avg_latency_cycles = self.total_latency_cycles / self.total_requests

        total_peak = peak_bw_per_ch * len(channels)
        if self.total_bytes > 0:
            self.peak_bandwidth_gbps = self.total_bytes * 8e-9
            self.efficiency_percent = (self.peak_bandwidth_gbps / total_peak) * 100 if total_peak > 0 else 0

        self.timestamp = datetime.now().isoformat()


class BandwidthTracker:
    """Tracks bandwidth over time windows"""

    def __init__(self, window_size: int = 1000, num_samples: int = 100):
        self.window_size = window_size  # cycles per window
        self.num_samples = num_samples  # number of historical samples to keep
        self.windows: deque = deque(maxlen=num_samples)
        self.current_window_bytes: int = 0
        self.current_window_start: int = 0
        self.total_cycles: int = 0

    def add_transfer(self, bytes_count: int, cycle: int):
        """Record a data transfer"""
        if cycle >= self.current_window_start + self.window_size:
            # Window complete, save and start new
            if self.current_window_start > 0:
                self.windows.append({
                    'start': self.current_window_start,
                    'end': cycle,
                    'bytes': self.current_window_bytes
                })
            self.current_window_start = cycle
            self.current_window_bytes = 0

        self.current_window_bytes += bytes_count
        self.total_cycles = max(self.total_cycles, cycle)

    def get_bandwidth_series(self) -> List[tuple]:
        """Get bandwidth over time as (cycle, bandwidth_gbps) tuples"""
        result = []
        for w in self.windows:
            duration = w['end'] - w['start'] if w['end'] > w['start'] else 1
            bw = w['bytes'] * 8e-9 / (duration * 0.78125e-9)  # cycles to seconds
            result.append((w['start'], bw))
        return result

    def get_average_bandwidth(self) -> float:
        """Get average bandwidth across all windows"""
        if not self.windows:
            return 0.0
        total_bytes = sum(w['bytes'] for w in self.windows) + self.current_window_bytes
        total_cycles = self.total_cycles if self.total_cycles > 0 else 1
        return total_bytes * 8e-9 / (total_cycles * 0.78125e-9)


class RealtimeMonitor:
    """
    Real-time performance monitoring for HBM simulation.

    Provides:
    - Per-channel bandwidth tracking
    - Aggregate throughput measurement
    - Latency statistics
    - Performance trend analysis
    """

    def __init__(
        self,
        num_channels: int = 8,
        peak_bandwidth_gbps: float = 819.2,
        update_interval_ms: float = 100.0,
        history_size: int = 1000
    ):
        self.num_channels = num_channels
        self.peak_bandwidth_gbps = peak_bandwidth_gbps
        self.update_interval_ms = update_interval_ms
        self.history_size = history_size

        # Per-channel metrics
        self.channels: Dict[int, ChannelMetrics] = {
            i: ChannelMetrics(channel_id=i) for i in range(num_channels)
        }

        # Aggregate metrics
        self.system = SystemMetrics()

        # Bandwidth tracking over time
        self.bandwidth_tracker = BandwidthTracker(window_size=1000, num_samples=history_size)

        # Monitoring state
        self._running = False
        self._lock = threading.Lock()
        self._start_time: Optional[float] = None
        self._current_cycle: int = 0

        # Callbacks for real-time updates
        self._update_callbacks: List[Callable[[SystemMetrics, Dict[int, ChannelMetrics]], None]] = []

        # Statistics history
        self.history: deque = deque(maxlen=history_size)

    def start(self):
        """Start monitoring"""
        self._running = True
        self._start_time = time.time()
        self._current_cycle = 0

    def stop(self):
        """Stop monitoring"""
        self._running = False

    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.channels = {i: ChannelMetrics(channel_id=i) for i in range(self.num_channels)}
            self.system = SystemMetrics()
            self.bandwidth_tracker = BandwidthTracker(window_size=1000, num_samples=self.history_size)
            self.history.clear()
            self._current_cycle = 0

    def record_request(
        self,
        channel_id: int,
        is_read: bool,
        bytes_count: int,
        latency_cycles: int,
        is_row_hit: bool,
        cycle: int
    ):
        """Record a completed request"""
        with self._lock:
            if channel_id not in self.channels:
                return

            ch = self.channels[channel_id]
            ch.bytes_transferred += bytes_count
            ch.request_count += 1

            if is_read:
                ch.read_count += 1
            else:
                ch.write_count += 1

            ch.total_latency_cycles += latency_cycles
            ch.max_latency_cycles = max(ch.max_latency_cycles, latency_cycles)
            ch.min_latency_cycles = min(ch.min_latency_cycles, latency_cycles)

            if is_row_hit:
                ch.row_hits += 1
            else:
                ch.row_misses += 1

            # Track bandwidth
            self.bandwidth_tracker.add_transfer(bytes_count, cycle)
            self._current_cycle = max(self._current_cycle, cycle)

    def add_update_callback(self, callback: Callable[[SystemMetrics, Dict[int, ChannelMetrics]], None]):
        """Add callback for real-time updates"""
        self._update_callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        with self._lock:
            self.system.update_from_channels(self.channels, self.peak_bandwidth_gbps / self.num_channels)

            return {
                'system': {
                    'total_bytes': self.system.total_bytes,
                    'total_requests': self.system.total_requests,
                    'total_reads': self.system.total_reads,
                    'total_writes': self.system.total_writes,
                    'peak_bandwidth_gbps': self.system.peak_bandwidth_gbps,
                    'avg_latency_cycles': self.system.avg_latency_cycles,
                    'efficiency_percent': self.system.efficiency_percent,
                    'timestamp': self.system.timestamp,
                },
                'channels': {
                    ch_id: {
                        'bytes_transferred': ch.bytes_transferred,
                        'request_count': ch.request_count,
                        'read_count': ch.read_count,
                        'write_count': ch.write_count,
                        'avg_latency': ch.avg_latency,
                        'hit_rate': ch.hit_rate,
                        'bandwidth_gbps': ch.bandwidth_gbps,
                    }
                    for ch_id, ch in self.channels.items()
                },
                'bandwidth_series': self.bandwidth_tracker.get_bandwidth_series(),
                'current_cycle': self._current_cycle,
            }

    def get_summary(self) -> str:
        """Get human-readable summary"""
        stats = self.get_stats()
        sys = stats['system']

        lines = []
        lines.append("=" * 60)
        lines.append(" REAL-TIME PERFORMANCE MONITOR SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Timestamp: {sys['timestamp']}")
        lines.append(f"Total Requests: {sys['total_requests']:,}")
        lines.append(f"  Reads: {sys['total_reads']:,}")
        lines.append(f"  Writes: {sys['total_writes']:,}")
        lines.append(f"Bandwidth: {sys['peak_bandwidth_gbps']:.2f} GB/s")
        lines.append(f"Efficiency: {sys['efficiency_percent']:.1f}%")
        lines.append(f"Avg Latency: {sys['avg_latency_cycles']:.1f} cycles")
        lines.append(f"Current Cycle: {stats['current_cycle']:,}")

        # Per-channel summary
        lines.append("\nPer-Channel Bandwidth (GB/s):")
        for ch_id, ch_data in sorted(stats['channels'].items()):
            bw = ch_data['bandwidth_gbps']
            bar_len = int(bw / (self.peak_bandwidth_gbps / self.num_channels) * 20)
            bar = '#' * bar_len
            lines.append(f"  CH{ch_id:2d}: {bw:6.2f} |{bar:<20} {ch_data['hit_rate']*100:.0f}% hits")

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Export all data as dictionary"""
        return self.get_stats()


def create_monitor(num_channels: int = 8, peak_bw: float = 819.2) -> RealtimeMonitor:
    """Create a configured RealtimeMonitor"""
    return RealtimeMonitor(
        num_channels=num_channels,
        peak_bandwidth_gbps=peak_bw,
        update_interval_ms=100.0,
        history_size=1000
    )


if __name__ == "__main__":
    # Demo: Test real-time monitoring
    print("Realtime Monitor Demo")
    print("=" * 60)

    # Create monitor for 8 channels
    monitor = create_monitor(num_channels=8, peak_bw=819.2)
    monitor.start()

    # Simulate some requests
    import random
    random.seed(42)

    for cycle in range(10000):
        for ch in range(8):
            if random.random() < 0.3:  # 30% chance of request per channel
                monitor.record_request(
                    channel_id=ch,
                    is_read=random.random() < 0.7,  # 70% reads
                    bytes_count=128,
                    latency_cycles=int(random.gauss(20, 10)),
                    is_row_hit=random.random() < 0.5,  # 50% hit rate
                    cycle=cycle
                )

    # Get statistics
    print(monitor.get_summary())

    # Get stats dict
    stats = monitor.get_stats()
    print(f"\nBandwidth Series Length: {len(stats['bandwidth_series'])} samples")

    monitor.stop()
    print("\nDemo complete!")