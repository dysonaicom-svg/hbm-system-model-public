"""Analysis Report Exporter Module for HBM4"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import csv
from io import StringIO


@dataclass
class ExporterConfig:
    """Configuration for report export"""
    include_raw_data: bool = True
    include_charts: bool = True
    timestamp: bool = True
    metadata: bool = True


class AnalysisReportExporter:
    """Exports analysis reports to various formats"""

    def __init__(self, config: Optional[ExporterConfig] = None):
        self.config = config or ExporterConfig()

    def export_json(self, data: Dict, output_path: str) -> str:
        """Export analysis data to JSON format"""
        report = {
            "exported_at": datetime.now().isoformat() if self.config.timestamp else None,
            "version": "1.0.0",
            "data": data,
        }
        if not self.config.metadata:
            report = data

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        return output_path

    def export_csv(self, data: List[Dict], output_path: str) -> str:
        """Export analysis data to CSV format"""
        if not data:
            return output_path

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        return output_path

    def export_html(
        self,
        data: Dict,
        title: str = "HBM4 Analysis Report",
        output_path: str = "report.html"
    ) -> str:
        """Export analysis data to HTML report"""
        timestamp = datetime.now().isoformat() if self.config.timestamp else ""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4a90d9; color: white; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="timestamp">Generated: {timestamp}</p>
    {self._dict_to_html(data)}
</body>
</html>"""

        with open(output_path, 'w') as f:
            f.write(html_content)
        return output_path

    def _dict_to_html(self, data: Dict, indent: int = 0) -> str:
        """Convert dictionary to HTML tables"""
        html = ""
        for key, value in data.items():
            if isinstance(value, dict):
                html += f"<h{indent+2}>{key}</h{indent+2}>\n"
                html += self._dict_to_html(value, indent + 1)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                html += f"<h{indent+2}>{key}</h{indent+2}>\n"
                html += "<table>\n<tr>"
                html += "".join(f"<th>{k}</th>" for k in value[0].keys())
                html += "</tr>\n"
                for row in value:
                    html += "<tr>"
                    html += "".join(f"<td>{v}</td>" for v in row.values())
                    html += "</tr>\n"
                html += "</table>\n"
            else:
                html += f"<p><strong>{key}:</strong> {value}</p>\n"
        return html

    def export_bottleneck_report(self, bottleneck_data: Dict) -> Dict[str, str]:
        """Export bottleneck analysis report in multiple formats"""
        results = {}

        # JSON
        json_path = "bottleneck_report.json"
        results["json"] = self.export_json(bottleneck_data, json_path)

        # CSV if data has list
        if "bottlenecks" in bottleneck_data:
            csv_path = "bottleneck_report.csv"
            results["csv"] = self.export_csv(bottleneck_data["bottlenecks"], csv_path)

        # HTML
        html_path = "bottleneck_report.html"
        results["html"] = self.export_html(bottleneck_data, "Bottleneck Analysis Report", html_path)

        return results

    def export_performance_summary(self, perf_data: Dict) -> str:
        """Export performance summary to JSON"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "summary": perf_data,
        }
        output_path = "performance_summary.json"
        return self.export_json(summary, output_path)
