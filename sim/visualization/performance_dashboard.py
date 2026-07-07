"""Performance Dashboard

ASCII-based real-time performance dashboard.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import time


@dataclass
class DashboardMetrics:
    """Real-time metrics for dashboard"""
    bandwidth_gbps: float = 0.0
    latency_ns: float = 0.0
    efficiency_percent: float = 0.0
    queue_utilization: float = 0.0
    row_hit_rate: float = 0.0
    channel_active: int = 0
    total_channels: int = 32


class PerformanceDashboard:
    """ASCII Performance Dashboard"""

    BAR_WIDTH = 30
    CHANNEL_BAR_WIDTH = 8

    def __init__(self, total_channels: int = 32):
        self.total_channels = total_channels
        self.metrics_history: List[DashboardMetrics] = []
        self.max_history = 60  # Keep last 60 samples

    def update(self, metrics: DashboardMetrics) -> None:
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)

    def _format_bar(self, value: float, max_value: float = 100.0) -> str:
        """Format a progress bar"""
        filled = int(self.BAR_WIDTH * min(value, max_value) / max_value)
        bar = "█" * filled + "░" * (self.BAR_WIDTH - filled)
        return f"[{bar}] {value:.1f}%"

    def _format_channel_bar(self, utilization: float) -> str:
        """Format a channel utilization bar"""
        filled = int(self.CHANNEL_BAR_WIDTH * utilization)
        bar = "█" * filled + "░" * (self.CHANNEL_BAR_WIDTH - filled)
        return f"[{bar}]"

    def get_header(self) -> str:
        lines = []
        lines.append("╔" + "═" * 78 + "╗")
        lines.append("║" + " HBM4 Performance Dashboard ".center(78) + "║")
        lines.append("╠" + "═" * 78 + "╣")
        return "\n".join(lines)

    def get_summary(self, metrics: DashboardMetrics) -> str:
        lines = []
        lines.append("║ PERFORMANCE SUMMARY".ljust(79) + "║")
        lines.append("║" + "─" * 78 + "║")

        # Bandwidth
        lines.append(f"║ Bandwidth: {metrics.bandwidth_gbps:>8.2f} GB/s {self._format_bar(metrics.bandwidth_gbps, 4000)}".ljust(79) + "║")

        # Latency
        lines.append(f"║ Latency:   {metrics.latency_ns:>8.2f} ns {self._format_bar(100 - min(metrics.latency_ns / 2, 100))}".ljust(79) + "║")

        # Efficiency
        lines.append(f"║ Efficiency: {metrics.efficiency_percent:>7.2f}% {self._format_bar(metrics.efficiency_percent)}".ljust(79) + "║")

        # Row Hit Rate
        lines.append(f"║ Row Hit:   {metrics.row_hit_rate:>8.2f}% {self._format_bar(metrics.row_hit_rate)}".ljust(79) + "║")

        lines.append("║" + "─" * 78 + "║")
        return "\n".join(lines)

    def get_channel_grid(self, channel_utils: Dict[int, float]) -> str:
        lines = []
        lines.append("║ CHANNEL UTILIZATION".ljust(79) + "║")
        lines.append("║" + "─" * 78 + "║")

        for ch in range(0, self.total_channels, 4):
            row = "║  "
            for i in range(4):
                idx = ch + i
                if idx < self.total_channels:
                    util = channel_utils.get(idx, 0.0)
                    row += f"CH{idx:02d} {self._format_channel_bar(util)}  "
            row = row.ljust(79) + "║"
            lines.append(row)

        lines.append("║" + "─" * 78 + "║")
        return "\n".join(lines)

    def get_queue_status(self, queue_depth: int, max_depth: int) -> str:
        lines = []
        lines.append("║ QUEUE STATUS".ljust(79) + "║")
        lines.append("║" + "─" * 78 + "║")

        utilization = (queue_depth / max_depth * 100) if max_depth > 0 else 0
        lines.append(f"║ Depth: {queue_depth:>4d}/{max_depth:<4d} {self._format_bar(utilization)}".ljust(79) + "║")

        lines.append("║" + "─" * 78 + "║")
        return "\n".join(lines)

    def get_footer(self) -> str:
        return "╚" + "═" * 78 + "╝"

    def render(self, metrics: DashboardMetrics, channel_utils: Optional[Dict[int, float]] = None,
              queue_depth: int = 0, max_queue: int = 128) -> str:
        lines = []
        lines.append(self.get_header())
        lines.append(self.get_summary(metrics))

        if channel_utils:
            lines.append(self.get_channel_grid(channel_utils))

        if max_queue > 0:
            lines.append(self.get_queue_status(queue_depth, max_queue))

        lines.append(self.get_footer())
        return "\n".join(lines)

    def render_trend(self, metric_name: str = "bandwidth") -> str:
        """Render a simple trend graph"""
        if not self.metrics_history:
            return "No data available"

        values = []
        for m in self.metrics_history:
            if metric_name == "bandwidth":
                values.append(m.bandwidth_gbps)
            elif metric_name == "latency":
                values.append(m.latency_ns)
            elif metric_name == "efficiency":
                values.append(m.efficiency_percent)

        if not values:
            return "No data"

        # Simple sparkline
        min_v, max_v = min(values), max(values)
        range_v = max_v - min_v if max_v > min_v else 1

        lines = []
        lines.append(f"  {metric_name.upper()} TREND (last {len(values)} samples)")

        # Top row
        lines.append(f"  {max_v:>8.2f} ┤")

        # Bars
        height = 8
        for row in range(height, 0, -1):
            threshold = min_v + (range_v * row / height)
            line = "         │"
            for v in values[-40:]:  # Last 40 samples
                if v >= threshold:
                    line += "█"
                else:
                    line += " "
            lines.append(line + "│")

        # Bottom row
        lines.append(f"  {min_v:>8.2f} ┴" + "─" * 40 + "┘")

        return "\n".join(lines)
