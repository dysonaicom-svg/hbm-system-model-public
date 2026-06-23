"""
Advanced Visualization Module for HBM Simulation Results

提供全面的可视化功能:
- 带宽分析图表
- 延迟分布直方图
- 通道热度图
- 性能趋势线图
- RTL对比可视化
- ASCII艺术图表 (无matplotlib依赖)

Usage:
    from sim.visualization.advanced_charts import AdvancedVisualizer

    viz = AdvancedVisualizer()
    viz.plot_bandwidth(results)
    viz.plot_latency_histogram(latencies)
    viz.export_html_report(results, "report.html")
"""

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from enum import Enum


# 可视化配置
DEFAULT_ASCII_WIDTH = 80
DEFAULT_BAR_CHAR = '#'
DEFAULT_EMPTY_CHAR = ' '
DEFAULT_HISTOGRAM_BINS = 20


class ChartType(Enum):
    """图表类型"""
    BAR = "bar"
    LINE = "line"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    ASCII_BAR = "ascii_bar"
    ASCII_HISTOGRAM = "ascii_histogram"


@dataclass
class ChartConfig:
    """图表配置"""
    title: str = ""
    width: int = DEFAULT_ASCII_WIDTH
    height: int = 20
    bar_char: str = DEFAULT_BAR_CHAR
    empty_char: str = DEFAULT_EMPTY_CHAR
    show_labels: bool = True
    show_values: bool = True
    decimal_places: int = 2
    colors_enabled: bool = False  # ANSI colors (optional)


class ASCIIRenderer:
    """ASCII图表渲染器"""

    # ANSI颜色码
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m',
        'bold': '\033[1m',
    }

    @classmethod
    def colorize(cls, text: str, color: str, enabled: bool = False) -> str:
        """为文本添加颜色"""
        if not enabled:
            return text
        color_code = cls.COLORS.get(color.lower(), '')
        reset_code = cls.COLORS['reset']
        return f"{color_code}{text}{reset_code}"

    @classmethod
    def render_bar_chart(
        cls,
        data: Dict[str, float],
        config: ChartConfig
    ) -> str:
        """渲染ASCII条形图"""
        lines = []

        if not data:
            return "No data to display"

        # 计算
        max_value = max(data.values()) if data else 1
        min_value = min(data.values()) if data else 0
        value_range = max_value - min_value if max_value != min_value else 1
        chart_height = config.height - 2  # 留标题和底部空间
        chart_width = config.width - 15  # 标签空间

        # 标题
        if config.title:
            lines.append(cls.colorize(f"╔{'═' * (config.width - 2)}╗", 'cyan', config.colors_enabled))
            title_padding = (config.width - len(config.title) - 4) // 2
            lines.append(cls.colorize(f"║{' ' * title_padding}{config.title}{' ' * (config.width - title_padding - len(config.title) - 4)}║", 'cyan', config.colors_enabled))
            lines.append(cls.colorize(f"╠{'═' * (config.width - 2)}╣", 'cyan', config.colors_enabled))

        # Y轴标签
        y_labels = [max_value, (max_value + min_value) / 2, min_value]
        y_positions = [chart_height - 1, chart_height // 2, 0]

        # 渲染条形
        chart = [[' ' for _ in range(chart_width)] for _ in range(chart_height)]

        for i, (label, value) in enumerate(data.items()):
            if i >= chart_width:
                break

            # 计算条形高度
            normalized = (value - min_value) / value_range if value_range > 0 else 0
            bar_height = int(normalized * chart_height)

            # 绘制条形
            for h in range(bar_height):
                row = chart_height - 1 - h
                chart[row][i] = config.bar_char

        # 输出
        for row_idx, row in enumerate(chart):
            # Y轴标签
            y_label = ""
            for y_pos, y_val in zip(y_positions, y_labels):
                if row_idx == y_pos:
                    y_label = f"{y_val:>10.1f} │"
                    break
            else:
                y_label = " " * 11 + "│"

            # 条形
            bar_str = ''.join(row)
            lines.append(y_label + bar_str)

        # X轴
        x_axis = "─" * (chart_width + 1)
        lines.append(f"            └{x_axis}")

        # X轴标签
        x_labels = list(data.keys())
        label_line = "            "
        for i, label in enumerate(x_labels[:chart_width]):
            label_line += label[:1]  # 第一个字符

        if len(x_labels) > chart_width:
            label_line = "            " + f"({len(x_labels)} items)"
        lines.append(label_line)

        return '\n'.join(lines)

    @classmethod
    def render_histogram(
        cls,
        values: List[float],
        config: ChartConfig,
        bins: int = DEFAULT_HISTOGRAM_BINS
    ) -> str:
        """渲染ASCII直方图"""
        lines = []

        if not values:
            return "No data to display"

        # 计算直方图
        min_val = min(values)
        max_val = max(values)
        bin_width = (max_val - min_val) / bins if bins > 0 else 1

        # 统计每个bin的数量
        counts = [0] * bins
        for v in values:
            bin_idx = min(int((v - min_val) / bin_width), bins - 1) if bin_width > 0 else 0
            counts[bin_idx] += 1

        max_count = max(counts) if counts else 1

        # 标题
        if config.title:
            lines.append(cls.colorize(f"═══ {config.title} ═══", 'cyan', config.colors_enabled))

        # 计算图表尺寸
        chart_height = config.height - 4
        chart_width = min(bins, config.width - 20)

        # 渲染
        for row in range(chart_height):
            row_val = max_count - (row * max_count // chart_height)
            label = f"{row_val:>5} │"
            bar_chars = int((row_val / max_count) * chart_width) if max_count > 0 else 0

            bar = ""
            bin_idx = 0
            for i in range(bins):
                if bin_idx >= chart_width:
                    break
                if counts[i] > 0 and counts[i] >= row_val - (max_count // chart_height):
                    bar += config.bar_char
                else:
                    bar += config.empty_char
                bin_idx += 1

            lines.append(label + bar)

        # X轴
        x_axis = "─" * (chart_width + 1)
        lines.append(f"       └{x_axis}")

        # X轴标签
        lines.append(f"       {min_val:.2f}{' ' * (chart_width - 15)}{max_val:.2f}")

        return '\n'.join(lines)

    @classmethod
    def render_heatmap(
        cls,
        data: Dict[str, Dict[str, float]],
        config: ChartConfig
    ) -> str:
        """渲染ASCII热力图"""
        lines = []

        if not data:
            return "No data to display"

        # 获取所有键
        row_labels = list(data.keys())
        col_labels = list(data[row_labels[0]].keys()) if row_labels else []

        if not col_labels:
            return "No data to display"

        # 找到最大/最小值
        all_values = [v for row in data.values() for v in row.values()]
        max_val = max(all_values) if all_values else 1
        min_val = min(all_values) if all_values else 0

        # 标题
        if config.title:
            lines.append(cls.colorize(f"═══ {config.title} ═══", 'cyan', config.colors_enabled))

        # 列标签
        col_header = " " * 12
        for col in col_labels[:config.width - 15]:
            col_header += f"{col[:3]:^5}"
        lines.append(col_header)

        # 热力图
        heat_chars = " .:+*#@"  # 低到高

        for row_label in row_labels:
            row_data = data.get(row_label, {})
            row_str = f"{row_label[:10]:>10} │"

            for col in col_labels[:config.width - 15]:
                value = row_data.get(col, 0)
                # 归一化
                normalized = (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
                char_idx = min(int(normalized * (len(heat_chars) - 1)), len(heat_chars) - 1)
                row_str += cls.colorize(f"{heat_chars[char_idx]:^5}", 'red' if char_idx > 3 else 'green', config.colors_enabled)

            lines.append(row_str)

        # 图例
        legend = "       " + "".join(f"{c:^5}" for c in heat_chars)
        lines.append(legend)
        lines.append(f"       {min_val:.2f}{' ' * (config.width - 25)}{max_val:.2f}")

        return '\n'.join(lines)

    @classmethod
    def render_gauge(
        cls,
        value: float,
        max_value: float,
        config: ChartConfig
    ) -> str:
        """渲染ASCII仪表"""
        lines = []

        # 计算百分比
        percent = (value / max_value) * 100 if max_value > 0 else 0
        filled = int(percent / 100 * (config.width - 20))

        # 标题
        if config.title:
            lines.append(cls.colorize(f"═══ {config.title} ═══", 'cyan', config.colors_enabled))

        # 仪表
        gauge = f"[{'#' * filled}{'-' * (config.width - 20 - filled)}]"
        lines.append(f"       {gauge}")

        # 值
        value_str = f"{value:.2f} / {max_value:.2f} ({percent:.1f}%)"
        lines.append(f"       {value_str}")

        # 状态指示
        if percent < 50:
            status = cls.colorize("LOW", 'green', config.colors_enabled)
        elif percent < 80:
            status = cls.colorize("MEDIUM", 'yellow', config.colors_enabled)
        else:
            status = cls.colorize("HIGH", 'red', config.colors_enabled)

        lines.append(f"       Status: {status}")

        return '\n'.join(lines)


@dataclass
class VisualizationData:
    """可视化数据容器"""
    # 带宽数据
    bandwidth_per_channel: Dict[int, float] = field(default_factory=dict)
    bandwidth_over_time: List[Tuple[int, float]] = field(default_factory=list)

    # 延迟数据
    latency_samples: List[float] = field(default_factory=list)
    latency_by_pattern: Dict[str, List[float]] = field(default_factory=dict)

    # 通道数据
    channel_activity: Dict[int, Dict[str, int]] = field(default_factory=dict)

    # 功耗数据
    power_samples: List[float] = field(default_factory=list)
    power_per_channel: Dict[int, float] = field(default_factory=dict)

    # RTL对比数据
    rtl_comparison: List[Dict[str, Any]] = field(default_factory=list)

    # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    simulation_cycles: int = 0
    peak_bandwidth_gbps: float = 0.0
    avg_latency_cycles: float = 0.0


class AdvancedVisualizer:
    """
    高级可视化模块

    Features:
    - ASCII图表 (无需外部依赖)
    - JSON数据导出
    - HTML报告生成
    - 多维度数据分析
    """

    def __init__(self, colors_enabled: bool = False):
        self.colors_enabled = colors_enabled
        self.renderer = ASCIIRenderer
        self.data = VisualizationData()

    def set_data(self, data: VisualizationData):
        """设置可视化数据"""
        self.data = data

    def plot_bandwidth(
        self,
        bandwidth_data: Dict[str, float],
        title: str = "Bandwidth Analysis"
    ) -> str:
        """生成带宽图表"""
        config = ChartConfig(title=title, height=15)
        return self.renderer.render_bar_chart(bandwidth_data, config)

    def plot_latency_histogram(
        self,
        latencies: List[float],
        title: str = "Latency Distribution",
        bins: int = 20
    ) -> str:
        """生成延迟直方图"""
        config = ChartConfig(title=title, height=15)
        return self.renderer.render_histogram(latencies, config, bins)

    def plot_channel_activity(
        self,
        activity_data: Dict[int, Dict[str, int]],
        title: str = "Channel Activity Heatmap"
    ) -> str:
        """生成通道活动热力图"""
        # 转换为字符串键
        str_data = {
            f"CH{ch:02d}": {k: v for k, v in activity.items()}
            for ch, activity in activity_data.items()
        }
        config = ChartConfig(title=title, height=20)
        return self.renderer.render_heatmap(str_data, config)

    def plot_bandwidth_efficiency(
        self,
        achieved: float,
        peak: float,
        title: str = "Bandwidth Efficiency"
    ) -> str:
        """生成带宽效率仪表"""
        config = ChartConfig(title=title)
        return self.renderer.render_gauge(achieved, peak, config)

    def generate_bandwidth_report(self) -> str:
        """生成带宽分析报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(" BANDWIDTH ANALYSIS REPORT")
        lines.append("=" * 60)

        # 通道带宽
        if self.data.bandwidth_per_channel:
            lines.append("\nPer-Channel Bandwidth (GB/s):")
            for ch, bw in sorted(self.data.bandwidth_per_channel.items()):
                bar_len = int(bw / max(self.data.bandwidth_per_channel.values()) * 30)
                bar = '#' * bar_len
                lines.append(f"  CH{ch:02d}: {bw:>8.2f} |{bar}")

        # 峰值带宽
        if self.data.peak_bandwidth_gbps > 0:
            lines.append(f"\nPeak Bandwidth: {self.data.peak_bandwidth_gbps:.2f} GB/s")

        # 带宽趋势
        if self.data.bandwidth_over_time:
            lines.append("\nBandwidth Over Time:")
            config = ChartConfig(title="", height=10)
            # 简化趋势显示
            trend_data = {f"C{i}": bw for i, (_, bw) in
                         enumerate(self.data.bandwidth_over_time[:8])}
            lines.append(self.renderer.render_bar_chart(trend_data, config))

        return '\n'.join(lines)

    def generate_latency_report(self) -> str:
        """生成延迟分析报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(" LATENCY ANALYSIS REPORT")
        lines.append("=" * 60)

        if self.data.latency_samples:
            samples = self.data.latency_samples
            lines.append(f"\nSample Count: {len(samples)}")
            lines.append(f"Average: {sum(samples)/len(samples):.2f} cycles")
            lines.append(f"Min: {min(samples):.2f} cycles")
            lines.append(f"Max: {max(samples):.2f} cycles")

            # 延迟直方图
            lines.append("\nLatency Distribution:")
            lines.append(self.plot_latency_histogram(samples, bins=15))

        # 按模式分类
        if self.data.latency_by_pattern:
            lines.append("\nLatency by Traffic Pattern:")
            for pattern, latencies in self.data.latency_by_pattern.items():
                if latencies:
                    avg = sum(latencies) / len(latencies)
                    lines.append(f"  {pattern}: {avg:.2f} cycles (n={len(latencies)})")

        return '\n'.join(lines)

    def generate_channel_report(self) -> str:
        """生成通道分析报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(" CHANNEL ANALYSIS REPORT")
        lines.append("=" * 60)

        if self.data.channel_activity:
            # 活动热力图
            lines.append("\nChannel Activity Heatmap:")
            lines.append(self.plot_channel_activity(self.data.channel_activity))

            # 统计
            total_commands = sum(
                sum(ch_data.values())
                for ch_data in self.data.channel_activity.values()
            )
            lines.append(f"\nTotal Commands: {total_commands}")

        return '\n'.join(lines)

    def generate_rtl_comparison_report(self) -> str:
        """生成RTL对比报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(" RTL CO-SIMULATION COMPARISON REPORT")
        lines.append("=" * 60)

        if self.data.rtl_comparison:
            matches = sum(1 for r in self.data.rtl_comparison if r.get('match', False))
            mismatches = len(self.data.rtl_comparison) - matches
            match_rate = (matches / len(self.data.rtl_comparison)) * 100

            lines.append(f"\nTotal Transactions: {len(self.data.rtl_comparison)}")
            lines.append(f"Matches: {matches}")
            lines.append(f"Mismatches: {mismatches}")
            lines.append(f"Match Rate: {match_rate:.2f}%")

            # 延迟差异分析
            latency_diffs = [abs(r.get('python_latency', 0) - r.get('rtl_latency', 0))
                           for r in self.data.rtl_comparison]
            if latency_diffs:
                lines.append(f"\nLatency Difference:")
                lines.append(f"  Average: {sum(latency_diffs)/len(latency_diffs):.2f} cycles")
                lines.append(f"  Max: {max(latency_diffs):.2f} cycles")
                lines.append(f"  Min: {min(latency_diffs):.2f} cycles")

        return '\n'.join(lines)

    def generate_full_report(self) -> str:
        """生成完整分析报告"""
        lines = []

        lines.append("╔══════════════════════════════════════════════════════════╗")
        lines.append("║        HBM UNIFIED SIMULATOR - ANALYSIS REPORT           ║")
        lines.append("╚══════════════════════════════════════════════════════════╝")
        lines.append(f"\nGenerated: {self.data.timestamp}")
        lines.append(f"Simulation Cycles: {self.data.simulation_cycles:,}")

        lines.append("\n" + self.generate_bandwidth_report())
        lines.append("\n" + self.generate_latency_report())
        lines.append("\n" + self.generate_channel_report())

        if self.data.rtl_comparison:
            lines.append("\n" + self.generate_rtl_comparison_report())

        lines.append("\n" + "=" * 60)
        lines.append(" END OF REPORT")
        lines.append("=" * 60)

        return '\n'.join(lines)

    def export_json(self, path: str):
        """导出数据到JSON"""
        data = {
            'timestamp': self.data.timestamp,
            'simulation_cycles': self.data.simulation_cycles,
            'bandwidth_per_channel': self.data.bandwidth_per_channel,
            'bandwidth_over_time': [
                {'cycle': c, 'bandwidth': bw}
                for c, bw in self.data.bandwidth_over_time
            ],
            'latency_samples': self.data.latency_samples,
            'latency_by_pattern': self.data.latency_by_pattern,
            'channel_activity': {
                str(ch): activity
                for ch, activity in self.data.channel_activity.items()
            },
            'power_samples': self.data.power_samples,
            'power_per_channel': self.data.power_per_channel,
            'rtl_comparison': self.data.rtl_comparison,
            'summary': {
                'peak_bandwidth_gbps': self.data.peak_bandwidth_gbps,
                'avg_latency_cycles': self.data.avg_latency_cycles,
            }
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def export_html_report(self, path: str):
        """导出HTML报告"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HBM Simulation Analysis Report</title>
    <style>
        body {{ font-family: monospace; margin: 20px; background: #1e1e1e; color: #d4d4d4; }}
        h1 {{ color: #569cd6; }}
        h2 {{ color: #4ec9b0; }}
        .metric {{ margin: 10px 0; }}
        .value {{ color: #ce9178; }}
        .chart {{ background: #2d2d2d; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #3e3e3e; padding: 8px; text-align: left; }}
        th {{ background: #0e639c; }}
    </style>
</head>
<body>
    <h1>HBM Unified Simulator - Analysis Report</h1>
    <p>Generated: {self.data.timestamp}</p>
    <p>Simulation Cycles: {self.data.simulation_cycles:,}</p>

    <h2>Summary</h2>
    <div class="chart">
        <div class="metric">Peak Bandwidth: <span class="value">{self.data.peak_bandwidth_gbps:.2f} GB/s</span></div>
        <div class="metric">Average Latency: <span class="value">{self.data.avg_latency_cycles:.2f} cycles</span></div>
    </div>

    <h2>Per-Channel Bandwidth</h2>
    <div class="chart">
        <table>
            <tr><th>Channel</th><th>Bandwidth (GB/s)</th></tr>
            {''.join(f'<tr><td>CH{ch:02d}</td><td>{bw:.2f}</td></tr>' for ch, bw in sorted(self.data.bandwidth_per_channel.items()))}
        </table>
    </div>

    <h2>Latency Distribution</h2>
    <div class="chart">
        <pre>{self.plot_latency_histogram(self.data.latency_samples, bins=15)}</pre>
    </div>
</body>
</html>"""

        with open(path, 'w') as f:
            f.write(html)


class PerformanceAnalyzer:
    """
    性能分析器

    提供统计分析功能:
    - 趋势检测
    - 异常值识别
    - 性能回归检测
    """

    @staticmethod
    def compute_statistics(values: List[float]) -> Dict[str, float]:
        """计算基本统计"""
        if not values:
            return {}

        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)

        sorted_vals = sorted(values)
        median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

        return {
            'count': n,
            'mean': mean,
            'median': median,
            'std_dev': std_dev,
            'min': min(values),
            'max': max(values),
            'variance': variance,
        }

    @staticmethod
    def detect_outliers(values: List[float], threshold: float = 2.0) -> List[int]:
        """检测异常值"""
        if len(values) < 3:
            return []

        stats = PerformanceAnalyzer.compute_statistics(values)
        mean = stats['mean']
        std_dev = stats['std_dev']

        outliers = []
        for i, v in enumerate(values):
            z_score = abs((v - mean) / std_dev) if std_dev > 0 else 0
            if z_score > threshold:
                outliers.append(i)

        return outliers

    @staticmethod
    def compute_percentiles(values: List[float], percentiles: List[int] = None) -> Dict[int, float]:
        """计算百分位数"""
        if not values:
            return {}

        if percentiles is None:
            percentiles = [50, 75, 90, 95, 99]

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        result = {}
        for p in percentiles:
            idx = int(n * p / 100)
            idx = min(idx, n - 1)
            result[p] = sorted_vals[idx]

        return result

    @staticmethod
    def compare_results(baseline: Dict[str, float], current: Dict[str, float]) -> Dict[str, Any]:
        """比较两组性能结果"""
        results = {
            'metrics': [],
            'regressions': [],
            'improvements': [],
        }

        for key in baseline:
            if key in current:
                base_val = baseline[key]
                curr_val = current[key]

                diff = curr_val - base_val
                pct_change = (diff / base_val * 100) if base_val != 0 else 0

                results['metrics'].append({
                    'name': key,
                    'baseline': base_val,
                    'current': curr_val,
                    'diff': diff,
                    'pct_change': pct_change,
                })

                # 检测性能回归
                if pct_change < -5:  # 降低超过5%
                    results['regressions'].append(key)
                elif pct_change > 5:  # 提升超过5%
                    results['improvements'].append(key)

        return results


def create_visualizer(colors: bool = False) -> AdvancedVisualizer:
    """创建可视化器"""
    return AdvancedVisualizer(colors_enabled=colors)


def analyze_and_visualize(stats: Dict[str, Any]) -> str:
    """分析并可视化统计数据的便捷函数"""
    viz = AdvancedVisualizer()

    # 填充数据
    viz.data.simulation_cycles = stats.get('total_cycles', 0)
    viz.data.peak_bandwidth_gbps = stats.get('throughput_gbps', 0)

    # 延迟数据
    if 'latency_histogram' in stats:
        viz.data.latency_samples = stats['latency_histogram']

    # 通道数据
    if 'channel_stats' in stats:
        viz.data.channel_activity = stats['channel_stats']

    # 生成报告
    return viz.generate_full_report()


if __name__ == '__main__':
    # 测试可视化
    print("Testing Advanced Visualizer...")
    print()

    viz = AdvancedVisualizer(colors_enabled=False)

    # 测试条形图
    print("Bandwidth Chart:")
    print(viz.plot_bandwidth({
        'Sequential': 1500.0,
        'Random': 800.0,
        'Stride': 1200.0,
        'Hotspot': 950.0,
    }, "Bandwidth by Pattern"))

    print()

    # 测试直方图
    print("Latency Histogram:")
    latencies = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
    print(viz.plot_latency_histogram(latencies, "Read Latency"))

    print()

    # 测试仪表
    print("Bandwidth Efficiency:")
    print(viz.plot_bandwidth_efficiency(1500.0, 2048.0, "Bandwidth Efficiency"))

    print()

    # 测试热力图
    print("Channel Activity:")
    channel_data = {
        0: {'commands': 100, 'reads': 60, 'writes': 40},
        1: {'commands': 150, 'reads': 90, 'writes': 60},
        2: {'commands': 80, 'reads': 50, 'writes': 30},
        3: {'commands': 200, 'reads': 120, 'writes': 80},
        4: {'commands': 120, 'reads': 70, 'writes': 50},
        5: {'commands': 90, 'reads': 55, 'writes': 35},
        6: {'commands': 170, 'reads': 100, 'writes': 70},
        7: {'commands': 130, 'reads': 80, 'writes': 50},
    }
    print(viz.plot_channel_activity(channel_data, "Channel Activity"))

    print()
    print("Visualization test complete!")
