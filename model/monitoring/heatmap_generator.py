"""
Heatmap Visualization Module for Channel/Bank Utilization

Provides heatmap visualization capabilities for HBM memory subsystem analysis.
Features:
- Channel utilization heatmaps
- Bank group activity heatmaps
- Bank-level activity heatmaps
- Request density visualization
- Bandwidth distribution heatmaps
- ASCII terminal output
- HTML export for web visualization

Usage:
    from model.monitoring.heatmap_generator import HeatmapGenerator

    generator = HeatmapGenerator(num_channels=32, banks_per_group=4)
    generator.record_activity(channel=0, bank_group=2, requests=100)
    heatmap = generator.generate_heatmap()
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from collections import defaultdict
from datetime import datetime


@dataclass
class ChannelActivity:
    """Activity metrics for a single channel"""
    channel_id: int
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    total_latency_cycles: int = 0
    row_hits: int = 0
    row_misses: int = 0
    bytes_transferred: int = 0
    busy_cycles: int = 0

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

    @property
    def utilization(self) -> float:
        """Utilization as fraction of max possible requests"""
        # Simple utilization based on request density
        return min(1.0, self.total_requests / 1000.0)


@dataclass
class BankGroupActivity:
    """Activity metrics for a bank group within a channel"""
    channel_id: int
    bank_group_id: int
    requests: int = 0
    reads: int = 0
    writes: int = 0
    row_hits: int = 0
    total_latency: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.row_hits + (self.requests - self.row_hits)
        if total == 0:
            return 0.0
        return self.row_hits / total


@dataclass
class BankActivity:
    """Activity metrics for a single bank"""
    channel_id: int
    bank_group_id: int
    bank_id: int
    activate_count: int = 0
    read_count: int = 0
    write_count: int = 0
    precharge_count: int = 0
    total_cycles_busy: int = 0

    @property
    def activity_level(self) -> float:
        """Normalized activity (0-1)"""
        # Based on activation frequency
        return min(1.0, self.activate_count / 1000.0)


class HeatmapGenerator:
    """
    Generates heatmap visualizations for HBM memory subsystem activity.

    Supports:
    - Channel-level utilization
    - Bank group activity
    - Bank-level activity
    - Request density distribution
    - Read/write ratio heatmaps
    """

    # Color schemes for different heatmap types
    COLOR_SCHEMES = {
        'blue': ['#f7f7f7', '#c6dbef', '#9ecae1', '#6baed6', '#3182bd', '#08519c'],
        'green': ['#f7f7f7', '#c7e9c0', '#a1d99b', '#74c476', '#31a354', '#006d2c'],
        'red': ['#f7f7f7', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26', '#a50f15'],
        'viridis': ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725'],
        'plasma': ['#0d0887', '#7e03a8', '#cc4778', '#f89540', '#f0f921'],
    }

    def __init__(
        self,
        num_channels: int = 8,
        bank_groups_per_channel: int = 4,
        banks_per_group: int = 4,
        color_scheme: str = 'blue'
    ):
        self.num_channels = num_channels
        self.bank_groups_per_channel = bank_groups_per_channel
        self.banks_per_group = banks_per_group
        self.color_scheme = color_scheme

        # Activity data structures
        self.channel_activity: Dict[int, ChannelActivity] = {
            i: ChannelActivity(channel_id=i) for i in range(num_channels)
        }

        self.bank_group_activity: Dict[Tuple[int, int], BankGroupActivity] = {}
        self.bank_activity: Dict[Tuple[int, int, int], BankActivity] = {}

        # Grid data for heatmaps
        self.channel_grid: List[List[float]] = []
        self.bank_group_grid: List[List[List[float]]] = []  # [ch][bg][bank]
        self.utilization_grid: List[List[float]] = []

        # Initialize grids
        self._initialize_grids()

    def _initialize_grids(self):
        """Initialize heatmap grids"""
        # Channel utilization grid (channels x metrics)
        self.channel_grid = [[0.0] * self.bank_groups_per_channel
                            for _ in range(self.num_channels)]

        # Bank group activity grid per channel
        self.bank_group_grid = [
            [[0.0] * self.bank_groups_per_channel for _ in range(self.num_channels)]
            for _ in range(self.num_channels)
        ]

        # Utilization grid
        self.utilization_grid = [[0.0] * self.bank_groups_per_channel
                                for _ in range(self.num_channels)]

    def record_request(
        self,
        channel: int,
        bank_group: int = 0,
        bank: int = 0,
        is_read: bool = True,
        latency_cycles: int = 0,
        bytes_count: int = 128,
        is_row_hit: bool = False
    ):
        """Record a memory request"""
        if channel >= self.num_channels:
            return

        # Update channel activity
        ch = self.channel_activity[channel]
        ch.total_requests += 1
        if is_read:
            ch.read_requests += 1
        else:
            ch.write_requests += 1
        ch.total_latency_cycles += latency_cycles
        ch.bytes_transferred += bytes_count
        if is_row_hit:
            ch.row_hits += 1
        else:
            ch.row_misses += 1

        # Update channel grid
        if bank_group < self.bank_groups_per_channel:
            self.channel_grid[channel][bank_group] += 1

        # Update bank group activity
        bg_key = (channel, bank_group)
        if bg_key not in self.bank_group_activity:
            self.bank_group_activity[bg_key] = BankGroupActivity(
                channel_id=channel,
                bank_group_id=bank_group
            )
        bg = self.bank_group_activity[bg_key]
        bg.requests += 1
        if is_read:
            bg.reads += 1
        else:
            bg.writes += 1
        bg.total_latency += latency_cycles
        if is_row_hit:
            bg.row_hits += 1

        # Update bank activity
        b_key = (channel, bank_group, bank)
        if b_key not in self.bank_activity:
            self.bank_activity[b_key] = BankActivity(
                channel_id=channel,
                bank_group_id=bank_group,
                bank_id=bank
            )
        b = self.bank_activity[b_key]
        b.activate_count += 1
        if is_read:
            b.read_count += 1
        else:
            b.write_count += 1

    def get_channel_utilization(self) -> List[List[float]]:
        """Get normalized channel utilization grid"""
        grid = [[0.0] * self.bank_groups_per_channel for _ in range(self.num_channels)]

        max_val = max(
            max(row) for row in self.channel_grid
        ) if self.channel_grid and any(any(r > 0 for r in row) for row in self.channel_grid) else 1.0

        for ch in range(self.num_channels):
            for bg in range(self.bank_groups_per_channel):
                val = self.channel_grid[ch][bg]
                grid[ch][bg] = val / max_val if max_val > 0 else 0.0

        return grid

    def get_bank_group_heatmap(self) -> List[List[float]]:
        """Get bank group activity heatmap (per channel)"""
        heatmap = [[0.0] * self.bank_groups_per_channel for _ in range(self.num_channels)]

        for ch in range(self.num_channels):
            for bg in range(self.bank_groups_per_channel):
                bg_key = (ch, bg)
                if bg_key in self.bank_group_activity:
                    activity = self.bank_group_activity[bg_key]
                    heatmap[ch][bg] = min(1.0, activity.requests / 1000.0)

        return heatmap

    def get_hit_rate_heatmap(self) -> List[List[float]]:
        """Get row hit rate heatmap (per channel/bank_group)"""
        heatmap = [[0.0] * self.bank_groups_per_channel for _ in range(self.num_channels)]

        for ch in range(self.num_channels):
            for bg in range(self.bank_groups_per_channel):
                bg_key = (ch, bg)
                if bg_key in self.bank_group_activity:
                    hit_rate = self.bank_group_activity[bg_key].hit_rate
                    heatmap[ch][bg] = hit_rate

        return heatmap

    def get_bandwidth_heatmap(self) -> List[List[float]]:
        """Get bandwidth distribution heatmap"""
        heatmap = [[0.0] * self.bank_groups_per_channel for _ in range(self.num_channels)]

        max_bw = 0.0
        for ch, activity in self.channel_activity.items():
            bw = activity.bytes_transferred * 8e-9  # GB/s
            if bw > max_bw:
                max_bw = bw

        for ch in range(self.num_channels):
            activity = self.channel_activity[ch]
            bw = activity.bytes_transferred * 8e-9
            norm_bw = bw / max_bw if max_bw > 0 else 0.0
            for bg in range(self.bank_groups_per_channel):
                heatmap[ch][bg] = norm_bw

        return heatmap

    def generate_ascii_heatmap(
        self,
        data: List[List[float]],
        row_labels: List[str] = None,
        col_labels: List[str] = None,
        title: str = "Heatmap",
        width: int = 60
    ) -> str:
        """Generate ASCII heatmap for terminal output"""
        if not data:
            return "No data available"

        num_rows = len(data)
        num_cols = len(data[0]) if data else 0

        if row_labels is None:
            row_labels = [f"CH{i:02d}" for i in range(num_rows)]
        if col_labels is None:
            col_labels = [f"BG{i}" for i in range(num_cols)]

        # Color characters (low to high)
        chars = " .:;+*#@"[:7]

        lines = []
        lines.append(f"═══ {title} ═══")
        lines.append("-" * (width + 15))

        # Column header
        header = " " * 10
        for col in range(num_cols):
            header += f"{col_labels[col]:^{width // num_cols}}"
        lines.append(header)
        lines.append("-" * (width + 15))

        # Data rows
        max_val = max(max(row) for row in data) if data else 1.0

        for row_idx, row in enumerate(data):
            row_str = f"{row_labels[row_idx]:>8} │"
            for val in row:
                if max_val > 0:
                    normalized = val / max_val
                else:
                    normalized = 0.0
                char_idx = min(int(normalized * (len(chars) - 1)), len(chars) - 1)
                row_str += f"{chars[char_idx]:^{width // num_cols}}"
            lines.append(row_str)

        lines.append("-" * (width + 15))

        # Legend
        lines.append(f"Legend: {chars[0]} (low) ... {chars[-1]} (high)")
        lines.append(f"Max value: {max_val:.2f}")

        return "\n".join(lines)

    def generate_html(self, output_path: str):
        """Generate HTML heatmap visualization"""
        channel_util = self.get_channel_utilization()
        bg_heatmap = self.get_bank_group_heatmap()
        hit_rate = self.get_hit_rate_heatmap()

        # Generate color arrays for JavaScript
        colors = self.COLOR_SCHEMES.get(self.color_scheme, self.COLOR_SCHEMES['blue'])

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HBM Activity Heatmap</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
        }}
        h1 {{ color: #569cd6; }}
        h2 {{ color: #4ec9b0; margin-top: 30px; }}
        .heatmap-container {{
            margin: 20px 0;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th, td {{
            width: 40px;
            height: 30px;
            text-align: center;
            border: 1px solid #3e3e3e;
        }}
        th {{
            background: #0e639c;
            color: white;
        }}
        .legend {{
            margin-top: 20px;
            display: flex;
            align-items: center;
        }}
        .legend-gradient {{
            width: 200px;
            height: 20px;
            background: linear-gradient(to right, {colors[0]}, {colors[-1]});
            margin: 0 10px;
        }}
        .summary {{
            background: #2d2d2d;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metric {{
            margin: 5px 0;
        }}
        .metric-label {{
            color: #9cdcfe;
        }}
        .metric-value {{
            color: #ce9178;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>HBM Memory Activity Heatmap</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">
            <span class="metric-label">Total Channels:</span>
            <span class="metric-value">{self.num_channels}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Bank Groups per Channel:</span>
            <span class="metric-value">{self.bank_groups_per_channel}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total Requests:</span>
            <span class="metric-value">{sum(ch.total_requests for ch in self.channel_activity.values()):,}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total Bytes Transferred:</span>
            <span class="metric-value">{sum(ch.bytes_transferred for ch in self.channel_activity.values()):,}</span>
        </div>
    </div>

    <h2>Channel Utilization Heatmap</h2>
    <div class="heatmap-container">
        {self._generate_html_table(channel_util, "ch_util", colors)}
    </div>

    <h2>Bank Group Activity Heatmap</h2>
    <div class="heatmap-container">
        {self._generate_html_table(bg_heatmap, "bg_activity", colors)}
    </div>

    <h2>Row Hit Rate Heatmap</h2>
    <div class="heatmap-container">
        {self._generate_html_table(hit_rate, "hit_rate", self.COLOR_SCHEMES['green'])}
    </div>

    <div class="legend">
        <span>Low</span>
        <div class="legend-gradient"></div>
        <span>High</span>
    </div>

    <script>
        function getColor(value, colors) {{
            if (value <= 0) return colors[0];
            if (value >= 1) return colors[colors.length - 1];
            const idx = Math.floor(value * (colors.length - 1));
            return colors[Math.min(idx, colors.length - 1)];
        }}
    </script>
</body>
</html>'''

        with open(output_path, 'w') as f:
            f.write(html)

    def _generate_html_table(self, data: List[List[float]], table_id: str, colors: List[str]) -> str:
        """Generate HTML table from heatmap data"""
        num_rows = len(data)
        num_cols = len(data[0]) if data else 0

        html = f'<table id="{table_id}"><thead><tr><th></th>'
        for col in range(num_cols):
            html += f'<th>BG{col}</th>'
        html += '</tr></thead><tbody>'

        for row in range(num_rows):
            html += f'<tr><th>CH{row:02d}</th>'
            for col in range(num_cols):
                val = data[row][col]
                color = self._get_color(val, colors)
                html += f'<td style="background-color: {color};" title="{val:.2f}">{val:.2f}</td>'
            html += '</tr>'

        html += '</tbody></table>'
        return html

    def _get_color(self, value: float, colors: List[str]) -> str:
        """Get color for a normalized value (0-1)"""
        if value <= 0:
            return colors[0]
        if value >= 1:
            return colors[-1]
        idx = int(value * (len(colors) - 1))
        return colors[min(idx, len(colors) - 1)]

    def generate_json(self) -> Dict[str, Any]:
        """Generate JSON data for external visualization"""
        channel_util = self.get_channel_utilization()
        bg_heatmap = self.get_bank_group_heatmap()
        hit_rate = self.get_hit_rate_heatmap()

        return {
            'metadata': {
                'num_channels': self.num_channels,
                'bank_groups_per_channel': self.bank_groups_per_channel,
                'banks_per_group': self.banks_per_group,
                'color_scheme': self.color_scheme,
                'generated_at': datetime.now().isoformat(),
            },
            'channel_utilization': channel_util,
            'bank_group_activity': bg_heatmap,
            'hit_rate': hit_rate,
            'bandwidth_distribution': self.get_bandwidth_heatmap(),
            'channel_stats': {
                ch: {
                    'total_requests': activity.total_requests,
                    'read_requests': activity.read_requests,
                    'write_requests': activity.write_requests,
                    'avg_latency': activity.avg_latency,
                    'hit_rate': activity.hit_rate,
                    'bytes_transferred': activity.bytes_transferred,
                    'utilization': activity.utilization,
                }
                for ch, activity in self.channel_activity.items()
            },
            'bank_group_stats': {
                f'ch{ch}_bg{bg}': {
                    'requests': bg_act.requests,
                    'reads': bg_act.reads,
                    'writes': bg_act.writes,
                    'hit_rate': bg_act.hit_rate,
                }
                for (ch, bg), bg_act in self.bank_group_activity.items()
            },
        }

    def get_ascii_report(self) -> str:
        """Generate comprehensive ASCII report"""
        lines = []
        lines.append("=" * 70)
        lines.append(" HEATMAP ANALYSIS REPORT")
        lines.append("=" * 70)

        # Channel utilization heatmap
        channel_util = self.get_channel_utilization()
        lines.append("\nChannel Utilization Heatmap:")
        lines.append(self.generate_ascii_heatmap(
            channel_util,
            title="Channel Utilization",
            width=50
        ))

        # Bank group activity heatmap
        bg_heatmap = self.get_bank_group_heatmap()
        lines.append("\nBank Group Activity Heatmap:")
        lines.append(self.generate_ascii_heatmap(
            bg_heatmap,
            title="Bank Group Activity",
            width=50
        ))

        # Hit rate heatmap
        hit_rate = self.get_hit_rate_heatmap()
        lines.append("\nRow Hit Rate Heatmap:")
        lines.append(self.generate_ascii_heatmap(
            hit_rate,
            title="Hit Rate",
            width=50
        ))

        # Summary statistics
        lines.append("\nChannel Statistics:")
        lines.append("-" * 50)
        total_requests = 0
        total_bytes = 0
        for ch, activity in sorted(self.channel_activity.items()):
            total_requests += activity.total_requests
            total_bytes += activity.bytes_transferred
            hit_rate = activity.hit_rate * 100
            lines.append(f"  CH{ch:02d}: req={activity.total_requests:>6}, "
                        f"hits={hit_rate:>5.1f}%, bw={activity.bytes_transferred * 8e-9:.2f} GB/s")

        lines.append("-" * 50)
        lines.append(f"  Total: req={total_requests:,}, bytes={total_bytes:,}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def create_generator(
    num_channels: int = 32,
    bank_groups: int = 8,
    banks_per_group: int = 4,
    color_scheme: str = 'blue'
) -> HeatmapGenerator:
    """Create a configured HeatmapGenerator"""
    return HeatmapGenerator(
        num_channels=num_channels,
        bank_groups_per_channel=bank_groups,
        banks_per_group=banks_per_group,
        color_scheme=color_scheme
    )


if __name__ == "__main__":
    # Demo: Generate sample heatmap
    print("Heatmap Generator Demo")
    print("=" * 70)

    # Create generator for 8 channels, 4 bank groups
    generator = HeatmapGenerator(
        num_channels=8,
        bank_groups_per_channel=4,
        banks_per_group=4
    )

    # Simulate activity with realistic patterns
    import random
    random.seed(42)

    for ch in range(8):
        # Hotspot channels have more activity
        activity_factor = 1.0 - (ch * 0.1)  # CH0 most active, CH7 least
        for bg in range(4):
            for bank in range(4):
                num_requests = int(random.gauss(500 * activity_factor, 100))
                num_requests = max(0, num_requests)

                for _ in range(num_requests):
                    generator.record_request(
                        channel=ch,
                        bank_group=bg,
                        bank=bank,
                        is_read=random.random() < 0.7,
                        latency_cycles=int(random.gauss(20, 10)),
                        bytes_count=128,
                        is_row_hit=random.random() < 0.6
                    )

    # Generate ASCII report
    print(generator.get_ascii_report())

    # Export JSON
    data = generator.generate_json()
    print(f"\nJSON export includes {len(data['channel_stats'])} channels")

    # Generate HTML
    html_path = "/tmp/hbm_heatmap.html"
    generator.generate_html(html_path)
    print(f"HTML heatmap saved to {html_path}")

    print("\nDemo complete!")