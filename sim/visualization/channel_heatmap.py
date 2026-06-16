"""
Channel Heatmap Visualization Module

Provides channel activity visualization including:
- Channel utilization heatmap
- Request density per channel
- Bank group activity heatmap
"""

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


@dataclass
class ChannelHeatmapData:
    """Data container for channel heatmap visualization"""
    # Per-channel utilization (0.0 - 1.0)
    channel_utilization: Dict[int, float] = field(default_factory=dict)
    
    # Request density per channel
    request_density: Dict[int, int] = field(default_factory=dict)
    
    # Bank group activity per channel
    bank_group_activity: Dict[int, Dict[int, float]] = field(default_factory=dict)
    
    # Row hit rate per channel
    row_hit_rate: Dict[int, float] = field(default_factory=dict)
    
    # Bandwidth per channel
    bandwidth_gbps: Dict[int, float] = field(default_factory=dict)
    
    # Number of channels
    num_channels: int = 8
    
    # Number of bank groups per channel
    bank_groups_per_channel: int = 4
    
    # Number of banks per group
    banks_per_group: int = 4
    
    # Peak values for normalization
    peak_requests: int = 0
    peak_bandwidth: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            'channel_utilization': self.channel_utilization,
            'request_density': self.request_density,
            'bank_group_activity': self.bank_group_activity,
            'row_hit_rate': self.row_hit_rate,
            'bandwidth_gbps': self.bandwidth_gbps,
            'num_channels': self.num_channels,
            'bank_groups_per_channel': self.bank_groups_per_channel,
            'banks_per_group': self.banks_per_group,
            'peak_requests': self.peak_requests,
            'peak_bandwidth': self.peak_bandwidth,
        }


@dataclass
class ChannelHeatmap:
    """Channel heatmap chart generator"""
    data: ChannelHeatmapData
    
    # Chart configuration
    title: str = "Channel Activity Heatmap"
    width: int = 800
    height: int = 600
    
    # Color scheme (low to high activity)
    color_low: str = "rgba(200, 200, 200, 0.3)"
    color_mid: str = "rgba(102, 126, 234, 0.6)"
    color_high: str = "rgba(102, 126, 234, 1.0)"
    
    # Heatmap cell colors
    heatmap_colors: List[str] = field(default_factory=lambda: [
        "#f7f7f7",  # 0% - No activity
        "#c6dbef",  # 20%
        "#9ecae1",  # 40%
        "#6baed6",  # 60%
        "#3182bd",  # 80%
        "#08519c",  # 100% - Full activity
    ])
    
    def _get_color_for_value(self, value: float) -> str:
        """Get color for a normalized value (0-1)
        
        Args:
            value: Normalized value between 0 and 1
            
        Returns:
            CSS color string
        """
        if value <= 0:
            return self.heatmap_colors[0]
        elif value >= 1:
            return self.heatmap_colors[-1]
        else:
            idx = int(value * (len(self.heatmap_colors) - 1))
            return self.heatmap_colors[min(idx, len(self.heatmap_colors) - 1)]
    
    def generate_utilization_heatmap_data(self) -> Dict[str, Any]:
        """Generate data for channel utilization heatmap
        
        Returns:
            Chart.js heatmap data structure
        """
        # Prepare data for heatmap (rows = channels, cols = bank groups)
        num_channels = self.data.num_channels
        bank_groups = self.data.bank_groups_per_channel
        
        # Generate labels
        channel_labels = [f"CH{i}" for i in range(num_channels)]
        bg_labels = [f"BG{j}" for j in range(bank_groups)]
        
        # Generate heatmap data array with static colors
        heatmap_data = []
        for ch in range(num_channels):
            for bg in range(bank_groups):
                # Get utilization for this channel/bank group
                util = self.data.channel_utilization.get(ch, 0.0)
                
                # Also consider bank group activity if available
                if ch in self.data.bank_group_activity:
                    bg_activity = self.data.bank_group_activity[ch].get(bg, 0.0)
                    if bg_activity > 0:
                        util = max(util, bg_activity)
                
                # Get static color for this value
                color = self._get_color_for_value(util)
                
                heatmap_data.append({
                    'x': bg,
                    'y': ch,
                    'v': util,
                    'color': color,
                })
        
        return {
            'type': 'matrix',
            'data': {
                'datasets': [{
                    'label': 'Channel Utilization',
                    'data': heatmap_data,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': True,
                    },
                    'title': {
                        'display': True,
                        'text': self.title,
                        'font': {'size': 16}
                    }
                },
                'scales': {
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Bank Group'
                        },
                        'labels': bg_labels,
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': 'Channel'
                        },
                        'labels': channel_labels,
                        'reverse': True,
                    }
                }
            }
        }
    
    def _generate_legend_labels(self, chart) -> List[Dict[str, Any]]:
        """Generate legend labels for heatmap"""
        return [
            {'text': '0%', 'fillStyle': self.heatmap_colors[0]},
            {'text': '20%', 'fillStyle': self.heatmap_colors[1]},
            {'text': '40%', 'fillStyle': self.heatmap_colors[2]},
            {'text': '60%', 'fillStyle': self.heatmap_colors[3]},
            {'text': '80%', 'fillStyle': self.heatmap_colors[4]},
            {'text': '100%', 'fillStyle': self.heatmap_colors[5]},
        ]
    
    def generate_request_density_data(self) -> Dict[str, Any]:
        """Generate data for request density bar chart
        
        Returns:
            Chart.js bar chart data
        """
        labels = [f"CH{i}" for i in range(self.data.num_channels)]
        values = [
            self.data.request_density.get(i, 0)
            for i in range(self.data.num_channels)
        ]
        
        # Color based on relative density
        max_val = max(values) if values else 1
        colors = [self._get_color_for_value(v / max_val) for v in values]
        
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Request Count',
                    'data': values,
                    'backgroundColor': colors,
                    'borderColor': [c.replace('0.3', '1').replace('0.6', '1').replace('1.0', '1') for c in colors],
                    'borderWidth': 1,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {
                        'display': True,
                        'text': 'Request Density per Channel',
                        'font': {'size': 16}
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Request Count'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Channel'
                        }
                    }
                }
            }
        }
    
    def generate_bank_group_activity_data(self) -> Dict[str, Any]:
        """Generate data for bank group activity heatmap
        
        Returns:
            Chart.js heatmap data for bank group activity
        """
        num_channels = self.data.num_channels
        bank_groups = self.data.bank_groups_per_channel
        
        channel_labels = [f"CH{i}" for i in range(num_channels)]
        bg_labels = [f"BG{j}" for j in range(bank_groups)]
        
        heatmap_data = []
        for ch in range(num_channels):
            for bg in range(bank_groups):
                activity = 0.0
                if ch in self.data.bank_group_activity:
                    activity = self.data.bank_group_activity[ch].get(bg, 0.0)
                
                # Get static color
                color = self._get_color_for_value(activity)
                
                heatmap_data.append({
                    'x': bg,
                    'y': ch,
                    'v': activity,
                    'color': color,
                })
        
        return {
            'type': 'matrix',
            'data': {
                'datasets': [{
                    'label': 'Bank Group Activity',
                    'data': heatmap_data,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': True},
                    'title': {
                        'display': True,
                        'text': 'Bank Group Activity',
                        'font': {'size': 16}
                    }
                },
                'scales': {
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Bank Group'
                        },
                        'labels': bg_labels,
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': 'Channel'
                        },
                        'labels': channel_labels,
                        'reverse': True,
                    }
                }
            }
        }
    
    def to_chartjs_script(self) -> str:
        """Generate JavaScript for Chart.js integration with heatmap coloring"""
        util_data = self.generate_utilization_heatmap_data()
        density_data = self.generate_request_density_data()
        bg_data = self.generate_bank_group_activity_data()
        
        # Generate color lookup function
        color_function = """
function getHeatmapColor(value) {{
    const colors = {colors};
    if (value <= 0) return colors[0];
    if (value >= 1) return colors[colors.length - 1];
    const idx = Math.floor(value * (colors.length - 1));
    return colors[Math.min(idx, colors.length - 1)];
}}
""".format(colors=json.dumps(self.heatmap_colors))
        
        # Generate callback for dynamic coloring
        color_callback = """
function(ctx) {{
    const value = ctx.raw?.v || 0;
    return getHeatmapColor(value);
}}
"""
        
        # Update datasets with color callback
        util_data['data']['datasets'][0]['backgroundColor'] = json.loads(color_callback)
        bg_data['data']['datasets'][0]['backgroundColor'] = json.loads(color_callback)
        
        return color_function + f"""
// Heatmap: Channel utilization
const utilHeatCtx = document.getElementById('channelUtilHeatmap');
if (utilHeatCtx) {{
    new Chart(utilHeatCtx, {json.dumps(util_data)});
}}

// Bar chart: Request density
const densityCtx = document.getElementById('requestDensity');
if (densityCtx) {{
    new Chart(densityCtx, {json.dumps(density_data)});
}}

// Heatmap: Bank group activity
const bgHeatCtx = document.getElementById('bankGroupHeatmap');
if (bgHeatCtx) {{
    new Chart(bgHeatCtx, {json.dumps(bg_data)});
}}
"""


def generate_channel_heatmap(
    channel_utilization: Dict[int, float],
    num_channels: int = 8,
    bank_groups: int = 4
) -> ChannelHeatmapData:
    """Generate channel heatmap data
    
    Args:
        channel_utilization: Dict mapping channel_id to utilization (0-1)
        num_channels: Total number of channels
        bank_groups: Number of bank groups per channel
        
    Returns:
        ChannelHeatmapData for visualization
    """
    data = ChannelHeatmapData(
        channel_utilization=channel_utilization,
        num_channels=num_channels,
        bank_groups_per_channel=bank_groups,
    )
    
    return data


def generate_bank_group_heatmap(
    bank_group_activity: Dict[int, Dict[int, float]],
    num_channels: int = 8,
    bank_groups: int = 4
) -> ChannelHeatmapData:
    """Generate bank group activity heatmap data
    
    Args:
        bank_group_activity: Dict mapping channel_id -> {bank_group_id -> activity}
        num_channels: Total number of channels
        bank_groups: Number of bank groups per channel
        
    Returns:
        ChannelHeatmapData for visualization
    """
    data = ChannelHeatmapData(
        bank_group_activity=bank_group_activity,
        num_channels=num_channels,
        bank_groups_per_channel=bank_groups,
    )
    
    # Also calculate channel utilization from bank group activity
    for ch, bg_act in bank_group_activity.items():
        total_activity = sum(bg_act.values())
        max_activity = bank_groups  # Normalize to 0-1
        data.channel_utilization[ch] = min(1.0, total_activity / max_activity)
    
    return data


def generate_request_density_chart(
    request_counts: Dict[int, int],
    num_channels: int = 8
) -> ChannelHeatmapData:
    """Generate request density chart data
    
    Args:
        request_counts: Dict mapping channel_id to request count
        num_channels: Total number of channels
        
    Returns:
        ChannelHeatmapData for visualization
    """
    data = ChannelHeatmapData(
        request_density=request_counts,
        num_channels=num_channels,
    )
    
    # Calculate peak requests
    if request_counts:
        data.peak_requests = max(request_counts.values())
    
    # Calculate utilization from request counts
    max_requests = data.peak_requests if data.peak_requests > 0 else 1
    for ch, count in request_counts.items():
        data.channel_utilization[ch] = count / max_requests
    
    return data


def create_channel_heatmap_from_stats(stats: Any) -> ChannelHeatmapData:
    """Create channel heatmap data from SimulationStats
    
    Args:
        stats: SimulationStats object from simulator
        
    Returns:
        ChannelHeatmapData for visualization
    """
    data = ChannelHeatmapData()
    
    if hasattr(stats, 'per_channel_stats') and stats.per_channel_stats:
        num_channels = len(stats.per_channel_stats)
        data.num_channels = num_channels
        
        total_requests = 0
        for ch_id, ch_stats in stats.per_channel_stats.items():
            # Request count
            requests = getattr(ch_stats, 'total_requests', 0)
            data.request_density[ch_id] = requests
            total_requests += requests
            
            # Hit rate
            hit_rate = getattr(ch_stats, 'hit_rate', 0.0)
            data.row_hit_rate[ch_id] = hit_rate
            
            # Calculate utilization
            if hasattr(stats, 'total_cycles') and stats.total_cycles > 0:
                # Utilization based on request count relative to ideal
                util = min(1.0, requests / (stats.total_cycles / 100))
                data.channel_utilization[ch_id] = util
            else:
                data.channel_utilization[ch_id] = 0.0
            
            # Bandwidth
            if hasattr(ch_stats, 'total_latency_cycles') and requests > 0:
                avg_lat = ch_stats.total_latency_cycles / requests
                # Calculate bandwidth
                bytes_per_request = 128
                tCK_ns = 0.78125
                cycles_for_request = avg_lat
                bw = bytes_per_request / (cycles_for_request * tCK_ns)
                data.bandwidth_gbps[ch_id] = bw
            else:
                data.bandwidth_gbps[ch_id] = 0.0
            
            # Bank group activity (estimate from hit rate)
            # If hit rate is high, bank groups are being reused well
            if ch_id not in data.bank_group_activity:
                data.bank_group_activity[ch_id] = {}
            
            for bg in range(data.bank_groups_per_channel):
                # Distribute activity based on hit rate
                activity = hit_rate * 0.5 + 0.1  # Base activity + hit rate contribution
                data.bank_group_activity[ch_id][bg] = min(1.0, activity)
        
        # Update peak requests
        if data.request_density:
            data.peak_requests = max(data.request_density.values())
            data.peak_bandwidth = max(data.bandwidth_gbps.values()) if data.bandwidth_gbps else 0.0
    
    return data


def generate_ascii_heatmap(
    channel_utilization: Dict[int, float],
    num_channels: int = 8,
    bank_groups: int = 4,
    width: int = 40
) -> str:
    """Generate ASCII heatmap for terminal output
    
    Args:
        channel_utilization: Dict mapping channel_id to utilization
        num_channels: Total number of channels
        bank_groups: Number of bank groups
        width: Width of heatmap in characters
        
    Returns:
        ASCII heatmap string
    """
    lines = []
    lines.append(f"Channel Utilization Heatmap ({num_channels} channels, {bank_groups} bank groups)")
    lines.append("-" * (width + 15))
    
    # Header
    lines.append("     " + "".join(f"{j:^6}" for j in range(bank_groups)) + "  Total")
    lines.append("-" * (width + 15))
    
    # Data rows
    for ch in range(num_channels):
        util = channel_utilization.get(ch, 0.0)
        bar_len = int(util * width)
        bar = "#" * bar_len + "." * (width - bar_len)
        
        # Split bar into bank groups
        seg_len = width // bank_groups
        segments = [bar[i:i+seg_len] for i in range(0, width, seg_len)]
        
        lines.append(f"CH{ch:2d}  " + "".join(f"{s}" for s in segments) + f"  {util*100:5.1f}%")
    
    lines.append("-" * (width + 15))
    
    # Legend
    lines.append("\nLegend:")
    lines.append(". = 0%    # = 25%    ## = 50%    ### = 75%    #### = 100%")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo: Generate sample heatmap data
    print("Channel Heatmap Visualization Demo")
    print("=" * 50)
    
    # Sample channel utilization data
    sample_utilization = {
        0: 0.95,
        1: 0.82,
        2: 0.78,
        3: 0.65,
        4: 0.55,
        5: 0.42,
        6: 0.28,
        7: 0.15,
    }
    
    # Sample bank group activity
    sample_bg_activity = {
        0: {0: 0.9, 1: 0.95, 2: 0.85, 3: 0.8},
        1: {0: 0.8, 1: 0.85, 2: 0.75, 3: 0.7},
        2: {0: 0.75, 1: 0.8, 2: 0.7, 3: 0.65},
        3: {0: 0.6, 1: 0.65, 2: 0.6, 3: 0.55},
        4: {0: 0.5, 1: 0.55, 2: 0.5, 3: 0.45},
        5: {0: 0.4, 1: 0.42, 2: 0.38, 3: 0.35},
        6: {0: 0.25, 1: 0.28, 2: 0.25, 3: 0.22},
        7: {0: 0.15, 1: 0.15, 2: 0.12, 3: 0.1},
    }
    
    # Sample request density
    sample_density = {
        0: 15000,
        1: 12500,
        2: 11200,
        3: 8500,
        4: 6200,
        5: 4200,
        6: 2800,
        7: 1200,
    }
    
    # Generate heatmap data
    heatmap_data = generate_channel_heatmap(sample_utilization)
    print(f"\nChannel Heatmap Data:")
    print(f"  Channels: {heatmap_data.num_channels}")
    print(f"  Bank groups: {heatmap_data.bank_groups_per_channel}")
    print(f"  Peak requests: {heatmap_data.peak_requests}")
    
    # Generate bank group activity data
    bg_heatmap = generate_bank_group_heatmap(sample_bg_activity)
    print(f"\nBank Group Activity:")
    for ch in range(8):
        if ch in bg_heatmap.bank_group_activity:
            bg_data = bg_heatmap.bank_group_activity[ch]
            print(f"  CH{ch}: " + ", ".join(f"BG{bg}={act:.2f}" for bg, act in bg_data.items()))
    
    # Generate ASCII heatmap
    print(f"\nASCII Heatmap:")
    print(generate_ascii_heatmap(sample_utilization, width=40))
    
    print("\nDemo complete!")