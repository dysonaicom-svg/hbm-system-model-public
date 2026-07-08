"""Visualization Export Module for HBM4 Analysis"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from io import StringIO
import base64


@dataclass
class ChartData:
    """Chart data container"""
    title: str
    data: List[Tuple[str, float]]
    chart_type: str = "bar"  # bar, line, pie


class VisualizationExporter:
    """Exports analysis results to visual formats"""

    def __init__(self):
        self.charts: List[ChartData] = []

    def add_chart(self, chart: ChartData):
        """Add a chart to export"""
        self.charts.append(chart)

    def create_bar_chart(self, title: str, labels: List[str], values: List[float]) -> ChartData:
        """Create a bar chart"""
        data = list(zip(labels, values))
        return ChartData(title=title, data=data, chart_type="bar")

    def create_line_chart(self, title: str, labels: List[str], values: List[float]) -> ChartData:
        """Create a line chart"""
        data = list(zip(labels, values))
        return ChartData(title=title, data=data, chart_type="line")

    def create_heatmap_data(
        self,
        title: str,
        rows: List[str],
        cols: List[str],
        values: List[List[float]]
    ) -> Dict:
        """Create heatmap data structure"""
        return {
            "title": title,
            "type": "heatmap",
            "rows": rows,
            "cols": cols,
            "values": values,
        }

    def export_ascii_chart(self, chart: ChartData, width: int = 60, height: int = 15) -> str:
        """Export chart as ASCII art"""
        if not chart.data:
            return "No data available"

        labels, values = zip(*chart.data)
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0

        lines = []
        lines.append(f"\n{chart.title}")
        lines.append("=" * len(chart.title))

        if chart.chart_type == "bar":
            # Bar chart
            bar_width = max(1, width // max(len(labels), 1))
            for label, value in zip(labels, values):
                bar_len = int((value / max_val) * (width - len(label) - 5)) if max_val > 0 else 0
                bar = "█" * bar_len
                lines.append(f"{label[:15]:15} {bar} {value:.2f}")
        elif chart.chart_type == "line":
            # Simple line chart
            for i, (label, value) in enumerate(zip(labels[:width], values[:width])):
                normalized = int((value - min_val) / (max_val - min_val + 0.001) * height)
                lines.append(" " * normalized + "●" + f" {label}: {value:.2f}")
        else:
            # Pie chart as text
            total = sum(values)
            for label, value in zip(labels, values):
                pct = (value / total * 100) if total > 0 else 0
                lines.append(f"{label}: {pct:.1f}% ({value:.2f})")

        return "\n".join(lines)

    def export_heatmap_ascii(self, heatmap: Dict, width: int = 60) -> str:
        """Export heatmap as ASCII art"""
        rows = heatmap["rows"]
        cols = heatmap["cols"]
        values = heatmap["values"]

        lines = []
        lines.append(f"\n{heatmap['title']}")
        lines.append("=" * len(heatmap['title']))

        # Header
        col_width = max(3, width // max(len(cols), 1))
        lines.append(" " * 15 + "".join(f"{c:^{col_width}}" for c in cols[:width//3]))

        # Rows
        for i, row in enumerate(rows[:20]):  # Limit rows
            row_vals = values[i] if i < len(values) else []
            cells = []
            for v in row_vals[:width//3]:
                if v < 0.3:
                    cells.append("░░░")
                elif v < 0.6:
                    cells.append("▒▒▒")
                elif v < 0.9:
                    cells.append("▓▓▓")
                else:
                    cells.append("███")
            lines.append(f"{row[:15]:15}" + "".join(cells))

        return "\n".join(lines)

    def export_timing_diagram(
        self,
        signals: List[Tuple[str, List[int]]],
        title: str = "Timing Diagram"
    ) -> str:
        """Export timing diagram as ASCII art"""
        lines = []
        lines.append(f"\n{title}")
        lines.append("=" * len(title))

        time_width = 8
        signal_height = 3

        # Header
        lines.append("Time   " + "".join(f"{i%10}" for i in range(50)))

        for name, waveform in signals:
            line1 = f"{name[:6]:6} " + "─" * 50
            line2 = "       "

            prev = 0
            for i, val in enumerate(waveform[:50]):
                if val != prev:
                    line1 = line1[:7+i] + ("┬" if val else "┴") + line1[8+i:]
                line2 += ("━" if val else " ")
                prev = val

            lines.append(line1)
            lines.append(line2)

        return "\n".join(lines)

    def export_to_svg(self, chart: ChartData, width: int = 400, height: int = 300) -> str:
        """Export chart as SVG"""
        if not chart.data:
            return ""

        labels, values = zip(*chart.data)
        max_val = max(values) if values else 1

        # SVG header
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            f'<title>{chart.title}</title>',
            f'<rect width="100%" height="100%" fill="white"/>',
            f'<text x="{width/2}" y="20" text-anchor="middle" font-size="14">{chart.title}</text>',
        ]

        chart_height = height - 60
        chart_width = width - 60
        bar_width = chart_width / len(values)

        for i, (label, value) in enumerate(zip(labels, values)):
            x = 30 + i * bar_width
            bar_height = (value / max_val) * chart_height
            y = height - 30 - bar_height

            svg.append(f'<rect x="{x}" y="{y}" width="{bar_width-2}" height="{bar_height}" fill="#4a90d9"/>')
            svg.append(f'<text x="{x+bar_width/2}" y="{height-10}" text-anchor="middle" font-size="8">{label}</text>')

        svg.append("</svg>")
        return "\n".join(svg)

    def generate_full_report(self) -> str:
        """Generate complete ASCII visualization report"""
        report = []
        report.append("\n" + "=" * 70)
        report.append(" HBM4 ANALYSIS VISUALIZATION REPORT")
        report.append("=" * 70)

        for chart in self.charts:
            report.append(self.export_ascii_chart(chart))

        report.append("\n" + "=" * 70)
        return "\n".join(report)


def quick_chart(data: List[Tuple[str, float]], title: str = "Chart") -> str:
    """Quick chart generation helper"""
    exporter = VisualizationExporter()
    chart = exporter.create_bar_chart(title, [d[0] for d in data], [d[1] for d in data])
    return exporter.export_ascii_chart(chart)
