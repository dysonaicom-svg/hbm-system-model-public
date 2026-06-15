"""
HBM Simulation Report Generator

生成交互式 HTML 报告，包含带宽、延迟和性能图表。
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ReportData:
    """报告数据"""
    simulation_name: str = "HBM Simulation"
    simulation_time_us: float = 0.0
    total_cycles: int = 0
    total_requests: int = 0
    completed_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    row_hit_rate: float = 0.0
    avg_latency_cycles: float = 0.0
    throughput_gbps: float = 0.0
    refresh_count: int = 0

    # 带宽数据
    bandwidth_by_pattern: Dict[str, float] = None

    # 延迟分布
    latency_histogram: List[int] = None

    def __post_init__(self):
        if self.bandwidth_by_pattern is None:
            self.bandwidth_by_pattern = {}
        if self.latency_histogram is None:
            self.latency_histogram = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'simulation_name': self.simulation_name,
            'simulation_time_us': self.simulation_time_us,
            'total_cycles': self.total_cycles,
            'total_requests': self.total_requests,
            'completed_requests': self.completed_requests,
            'read_requests': self.read_requests,
            'write_requests': self.write_requests,
            'row_hit_rate': self.row_hit_rate,
            'avg_latency_cycles': self.avg_latency_cycles,
            'throughput_gbps': self.throughput_gbps,
            'refresh_count': self.refresh_count,
            'bandwidth_by_pattern': self.bandwidth_by_pattern,
            'latency_histogram': self.latency_histogram[:100] if self.latency_histogram else [],
        }


def generate_html_report(
    report_data: ReportData,
    output_path: str = "sim/results/report.html",
    title: str = "HBM Simulation Report"
) -> str:
    """生成 HTML 报告

    Args:
        report_data: 报告数据
        output_path: 输出文件路径
        title: 报告标题

    Returns:
        HTML 字符串
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 转换数据为 JSON
    data_json = json.dumps(report_data.to_dict(), indent=2)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        header .timestamp {{
            opacity: 0.8;
            font-size: 0.9rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stat {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .stat:last-child {{
            border-bottom: none;
        }}
        .stat-label {{
            color: #666;
        }}
        .stat-value {{
            font-weight: 600;
            color: #333;
        }}
        .stat-value.highlight {{
            color: #667eea;
            font-size: 1.2rem;
        }}
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .chart-title {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.2rem;
        }}
        .chart-wrapper {{
            position: relative;
            height: 300px;
        }}
        .info-box {{
            background: #e8f4f8;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 10px 10px 0;
        }}
        .info-box h4 {{
            color: #667eea;
            margin-bottom: 5px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-info {{
            background: #cce5ff;
            color: #004085;
        }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="timestamp">Generated: {timestamp}</div>
        </header>

        <div class="grid">
            <div class="card">
                <h3>Simulation Summary</h3>
                <div class="stat">
                    <span class="stat-label">Simulation Time</span>
                    <span class="stat-value">{report_data.simulation_time_us:.1f} μs</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Cycles</span>
                    <span class="stat-value">{report_data.total_cycles:,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Requests</span>
                    <span class="stat-value highlight">{report_data.total_requests:,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Completed</span>
                    <span class="stat-value">{report_data.completed_requests:,}</span>
                </div>
            </div>

            <div class="card">
                <h3>Request Breakdown</h3>
                <div class="stat">
                    <span class="stat-label">Read Requests</span>
                    <span class="stat-value badge badge-info">{report_data.read_requests:,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Write Requests</span>
                    <span class="stat-value badge badge-info">{report_data.write_requests:,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Read Ratio</span>
                    <span class="stat-value">{report_data.read_requests / max(report_data.total_requests, 1) * 100:.1f}%</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Refresh Count</span>
                    <span class="stat-value">{report_data.refresh_count:,}</span>
                </div>
            </div>

            <div class="card">
                <h3>Performance Metrics</h3>
                <div class="stat">
                    <span class="stat-label">Throughput</span>
                    <span class="stat-value highlight">{report_data.throughput_gbps:.2f} GB/s</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Avg Latency</span>
                    <span class="stat-value">{report_data.avg_latency_cycles:.1f} cycles</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Row Hit Rate</span>
                    <span class="stat-value badge badge-success">{report_data.row_hit_rate * 100:.1f}%</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Completion Rate</span>
                    <span class="stat-value">{report_data.completed_requests / max(report_data.total_requests, 1) * 100:.1f}%</span>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h3 class="chart-title">Bandwidth by Traffic Pattern</h3>
            <div class="chart-wrapper">
                <canvas id="bandwidthChart"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <h3 class="chart-title">Latency Distribution</h3>
            <div class="chart-wrapper">
                <canvas id="latencyChart"></canvas>
            </div>
        </div>

        <div class="info-box">
            <h4>HBM3 Specification Reference</h4>
            <p>
                <strong>Theoretical Peak Bandwidth:</strong> 819.2 GB/s/stack (HBM3 @ 6.4 Gbps)<br>
                <strong>Interface Width:</strong> 1024-bit (8 channels × 128 bits)<br>
                <strong>Burst Length:</strong> 32 bytes (FLINE)<br>
                <strong>tCK:</strong> 781.25 ps (1.28 GHz)
            </p>
        </div>

        <footer>
            <p>HBM System Simulation Platform | Generated by Claude Code</p>
        </footer>
    </div>

    <script>
        // Data from Python
        const simData = {data_json};

        // Bandwidth Chart
        const bandwidthCtx = document.getElementById('bandwidthChart').getContext('2d');
        const bandwidthLabels = Object.keys(simData.bandwidth_by_pattern);
        const bandwidthValues = Object.values(simData.bandwidth_by_pattern);

        new Chart(bandwidthCtx, {{
            type: 'bar',
            data: {{
                labels: bandwidthLabels.length > 0 ? bandwidthLabels : ['No Data'],
                datasets: [{{
                    label: 'Bandwidth (GB/s)',
                    data: bandwidthValues.length > 0 ? bandwidthValues : [0],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: false }}
                }}
            }}
        }});

        // Latency Distribution Chart
        const latencyCtx = document.getElementById('latencyChart').getContext('2d');
        const latencyData = simData.latency_histogram || [];

        // Create histogram bins
        let bins = {{}};
        if (latencyData.length > 0) {{
            latencyData.forEach(lat => {{
                const bin = Math.floor(lat / 10) * 10;
                bins[bin] = (bins[bin] || 0) + 1;
            }});
        }}

        const latencyLabels = Object.keys(bins).map(k => parseInt(k)).sort((a,b) => a-b);
        const latencyCounts = latencyLabels.map(k => bins[k]);

        new Chart(latencyCtx, {{
            type: 'histogram',
            data: {{
                labels: latencyLabels.length > 0 ? latencyLabels.map(l => l + '-' ) : ['No Data'],
                datasets: [{{
                    label: 'Request Count',
                    data: latencyCounts.length > 0 ? latencyCounts : [0],
                    backgroundColor: 'rgba(118, 75, 162, 0.8)',
                    borderColor: 'rgba(118, 75, 162, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        title: {{ display: true, text: 'Latency (cycles)' }}
                    }},
                    y: {{
                        title: {{ display: true, text: 'Count' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    # 写入文件
    with open(output_path, 'w') as f:
        f.write(html)

    return html


def generate_json_report(
    report_data: ReportData,
    output_path: str = "sim/results/report.json"
) -> str:
    """生成 JSON 报告

    Args:
        report_data: 报告数据
        output_path: 输出文件路径

    Returns:
        JSON 字符串
    """
    data = report_data.to_dict()
    data['generated_at'] = datetime.now().isoformat()

    json_str = json.dumps(data, indent=2)

    with open(output_path, 'w') as f:
        f.write(json_str)

    return json_str


def create_report_from_stats(stats, name: str = "HBM Simulation") -> ReportData:
    """从 SimulationStats 创建报告数据

    Args:
        stats: SimulationStats 对象
        name: 报告名称

    Returns:
        ReportData 对象
    """
    report = ReportData(
        simulation_name=name,
        simulation_time_us=stats.total_cycles * 0.78125 / 1e6,  # cycles to us
        total_cycles=stats.total_cycles,
        total_requests=stats.total_requests,
        completed_requests=stats.completed_requests,
        read_requests=stats.read_requests,
        write_requests=stats.write_requests,
        row_hit_rate=stats.row_hit_rate,
        avg_latency_cycles=stats.avg_latency,
        throughput_gbps=stats.throughput_gbps,
        refresh_count=stats.refresh_count,
    )

    return report


if __name__ == "__main__":
    # 演示报告生成
    from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

    print("Generating sample report...")

    # 运行仿真获取数据
    config = SimulationConfig(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        seed=42,
    )

    sim = HBMSimulator(config)
    stats = sim.run()

    # 创建报告数据
    report_data = create_report_from_stats(stats, "HBM3 Random Traffic Test")

    # 生成 HTML 报告
    html_path = "sim/results/report.html"
    generate_html_report(report_data, html_path)
    print(f"HTML report generated: {html_path}")

    # 生成 JSON 报告
    json_path = "sim/results/report.json"
    generate_json_report(report_data, json_path)
    print(f"JSON report generated: {json_path}")

    print("Report generation complete!")