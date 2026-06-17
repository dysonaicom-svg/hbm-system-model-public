"""
Result Comparison and Analysis Module

提供Python模型和RTL仿真结果的对比分析功能:
- 事务级对比
- 统计级对比
- 时序分析
- 回归检测

Usage:
    from sim.result_comparison import ResultComparator, ComparisonReport

    analyzer = ResultAnalyzer()
    report = analyzer.compare_and_analyze(python_stats, rtl_stats)
    report.print_summary()
"""

import json
import statistics
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path


class ComparisonType(Enum):
    """对比类型"""
    TRANSACTION = "transaction"
    STATISTICAL = "statistical"
    TIMING = "timing"
    BANDWIDTH = "bandwidth"
    LATENCY = "latency"


class RegressionStatus(Enum):
    """回归状态"""
    PASS = "pass"
    WARNING = "warning"
    REGRESSION = "regression"
    IMPROVEMENT = "improvement"


@dataclass
class ComparisonResult:
    """对比结果"""
    metric_name: str
    python_value: float
    rtl_value: float
    difference: float
    percent_difference: float
    status: RegressionStatus
    threshold_percent: float = 5.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric_name': self.metric_name,
            'python_value': self.python_value,
            'rtl_value': self.rtl_value,
            'difference': self.difference,
            'percent_difference': self.percent_difference,
            'status': self.status.value,
            'threshold_percent': self.threshold_percent,
        }


@dataclass
class TimingAnalysis:
    """时序分析"""
    transaction_id: int
    python_latency: int
    rtl_latency: int
    latency_diff: int
    python_data: Optional[int] = None
    rtl_data: Optional[int] = None
    data_match: bool = True
    timestamp_ns: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'transaction_id': self.transaction_id,
            'python_latency': self.python_latency,
            'rtl_latency': self.rtl_latency,
            'latency_diff': self.latency_diff,
            'python_data': hex(self.python_data) if self.python_data else None,
            'rtl_data': hex(self.rtl_data) if self.rtl_data else None,
            'data_match': self.data_match,
            'timestamp_ns': self.timestamp_ns,
        }


@dataclass
class ComparisonReport:
    """对比报告"""
    timestamp: str
    comparison_type: ComparisonType
    total_transactions: int
    matching_transactions: int
    mismatching_transactions: int
    match_rate: float
    results: List[ComparisonResult]
    timing_analyses: List[TimingAnalysis]

    # 统计摘要
    avg_latency_diff: float = 0.0
    max_latency_diff: int = 0
    avg_bandwidth_diff: float = 0.0
    max_bandwidth_diff: float = 0.0

    # 总体状态
    overall_status: RegressionStatus = RegressionStatus.PASS
    summary_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'comparison_type': self.comparison_type.value,
            'total_transactions': self.total_transactions,
            'matching_transactions': self.matching_transactions,
            'mismatching_transactions': self.mismatching_transactions,
            'match_rate': self.match_rate,
            'results': [r.to_dict() for r in self.results],
            'timing_analyses': [t.to_dict() for t in self.timing_analyses],
            'summary': {
                'avg_latency_diff': self.avg_latency_diff,
                'max_latency_diff': self.max_latency_diff,
                'avg_bandwidth_diff': self.avg_bandwidth_diff,
                'max_bandwidth_diff': self.max_bandwidth_diff,
            },
            'overall_status': self.overall_status.value,
            'summary_message': self.summary_message,
        }

    def print_summary(self):
        """打印摘要"""
        status_symbols = {
            RegressionStatus.PASS: "✓",
            RegressionStatus.WARNING: "⚠",
            RegressionStatus.REGRESSION: "✗",
            RegressionStatus.IMPROVEMENT: "↑",
        }

        print("=" * 70)
        print(" COMPARISON REPORT SUMMARY")
        print("=" * 70)
        print(f"Timestamp: {self.timestamp}")
        print(f"Type: {self.comparison_type.value}")
        print()
        print(f"Transactions:")
        print(f"  Total:    {self.total_transactions}")
        print(f"  Matching: {self.matching_transactions}")
        print(f"  Mismatching: {self.mismatching_transactions}")
        print(f"  Match Rate: {self.match_rate * 100:.2f}%")
        print()

        if self.results:
            print("Metric Comparisons:")
            for result in self.results:
                symbol = status_symbols.get(result.status, "?")
                print(f"  {symbol} {result.metric_name}:")
                print(f"      Python: {result.python_value:.4f}")
                print(f"      RTL:    {result.rtl_value:.4f}")
                print(f"      Diff:   {result.difference:.4f} ({result.percent_difference:+.2f}%)")
            print()

        if self.timing_analyses:
            print("Timing Analysis:")
            print(f"  Avg Latency Diff: {self.avg_latency_diff:.2f} cycles")
            print(f"  Max Latency Diff: {self.max_latency_diff} cycles")
            print()

        print("Overall Status:", end=" ")
        if self.overall_status == RegressionStatus.PASS:
            print(f"\033[92m{self.overall_status.value.upper()}\033[0m")
        elif self.overall_status == RegressionStatus.WARNING:
            print(f"\033[93m{self.overall_status.value.upper()}\033[0m")
        else:
            print(f"\033[91m{self.overall_status.value.upper()}\033[0m")

        print(f"Message: {self.summary_message}")
        print("=" * 70)


@dataclass
class StatisticalSummary:
    """统计摘要"""
    count: int
    mean: float
    median: float
    std_dev: float
    min_val: float
    max_val: float
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'count': self.count,
            'mean': self.mean,
            'median': self.median,
            'std_dev': self.std_dev,
            'min': self.min_val,
            'max': self.max_val,
            'p50': self.p50,
            'p75': self.p75,
            'p90': self.p90,
            'p95': self.p95,
            'p99': self.p99,
        }


class ResultAnalyzer:
    """
    结果分析器

    Features:
    - Python vs RTL 事务对比
    - 统计分布对比
    - 时序分析
    - 回归检测
    """

    def __init__(self, tolerance_percent: float = 5.0):
        self.tolerance_percent = tolerance_percent
        self.comparison_results: List[ComparisonResult] = []
        self.timing_analyses: List[TimingAnalysis] = []

    def compare_metric(
        self,
        name: str,
        python_value: float,
        rtl_value: float,
        threshold: Optional[float] = None
    ) -> ComparisonResult:
        """对比单个指标"""
        threshold = threshold or self.tolerance_percent
        difference = python_value - rtl_value
        percent_diff = (difference / python_value * 100) if python_value != 0 else 0

        # 确定状态
        abs_percent = abs(percent_diff)
        if abs_percent <= threshold:
            status = RegressionStatus.PASS
        elif abs_percent <= threshold * 2:
            status = RegressionStatus.WARNING
        elif percent_diff > 0:
            status = RegressionStatus.IMPROVEMENT  # Python值更大
        else:
            status = RegressionStatus.REGRESSION

        result = ComparisonResult(
            metric_name=name,
            python_value=python_value,
            rtl_value=rtl_value,
            difference=difference,
            percent_difference=percent_diff,
            status=status,
            threshold_percent=threshold,
        )

        self.comparison_results.append(result)
        return result

    def analyze_timing(
        self,
        transaction_id: int,
        python_latency: int,
        rtl_latency: int,
        python_data: Optional[int] = None,
        rtl_data: Optional[int] = None
    ) -> TimingAnalysis:
        """分析时序"""
        latency_diff = abs(python_latency - rtl_latency)
        data_match = (python_data == rtl_data) if (python_data and rtl_data) else True

        analysis = TimingAnalysis(
            transaction_id=transaction_id,
            python_latency=python_latency,
            rtl_latency=rtl_latency,
            latency_diff=latency_diff,
            python_data=python_data,
            rtl_data=rtl_data,
            data_match=data_match,
            timestamp_ns=datetime.now().timestamp() * 1e9,
        )

        self.timing_analyses.append(analysis)
        return analysis

    def compute_statistics(self, values: List[float]) -> StatisticalSummary:
        """计算统计摘要"""
        if not values:
            return StatisticalSummary(count=0, mean=0, median=0, std_dev=0,
                                      min_val=0, max_val=0)

        n = len(values)
        mean = statistics.mean(values)
        median = statistics.median(values)
        std_dev = statistics.stdev(values) if n > 1 else 0

        # 计算百分位数
        sorted_vals = sorted(values)
        p_idx = lambda p: min(int(n * p / 100), n - 1)

        return StatisticalSummary(
            count=n,
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_val=min(values),
            max_val=max(values),
            p50=sorted_vals[p_idx(50)],
            p75=sorted_vals[p_idx(75)],
            p90=sorted_vals[p_idx(90)],
            p95=sorted_vals[p_idx(95)],
            p99=sorted_vals[p_idx(99)],
        )

    def compare_distributions(
        self,
        python_values: List[float],
        rtl_values: List[float],
        name: str = "distribution"
    ) -> Tuple[StatisticalSummary, StatisticalSummary, ComparisonResult]:
        """对比两个分布"""
        python_stats = self.compute_statistics(python_values)
        rtl_stats = self.compute_statistics(rtl_values)

        # 对比均值
        result = self.compare_metric(
            f"{name}_mean",
            python_stats.mean,
            rtl_stats.mean
        )

        return python_stats, rtl_stats, result

    def generate_report(
        self,
        comparison_type: ComparisonType = ComparisonType.TRANSACTION
    ) -> ComparisonReport:
        """生成对比报告"""
        total = len(self.timing_analyses)
        matches = sum(1 for a in self.timing_analyses if a.data_match)
        mismatches = total - matches
        match_rate = matches / total if total > 0 else 0

        # 计算延迟差异统计
        latency_diffs = [a.latency_diff for a in self.timing_analyses]
        avg_latency_diff = statistics.mean(latency_diffs) if latency_diffs else 0
        max_latency_diff = max(latency_diffs) if latency_diffs else 0

        # 确定总体状态
        regression_count = sum(1 for r in self.comparison_results
                              if r.status == RegressionStatus.REGRESSION)
        warning_count = sum(1 for r in self.comparison_results
                          if r.status == RegressionStatus.WARNING)

        if regression_count > 0:
            overall_status = RegressionStatus.REGRESSION
            summary = f"Found {regression_count} regressions"
        elif warning_count > 0:
            overall_status = RegressionStatus.WARNING
            summary = f"Found {warning_count} warnings"
        else:
            overall_status = RegressionStatus.PASS
            summary = "All comparisons passed"

        return ComparisonReport(
            timestamp=datetime.now().isoformat(),
            comparison_type=comparison_type,
            total_transactions=total,
            matching_transactions=matches,
            mismatching_transactions=mismatches,
            match_rate=match_rate,
            results=self.comparison_results,
            timing_analyses=self.timing_analyses,
            avg_latency_diff=avg_latency_diff,
            max_latency_diff=max_latency_diff,
            overall_status=overall_status,
            summary_message=summary,
        )

    def detect_regressions(
        self,
        baseline: Dict[str, float],
        current: Dict[str, float],
        threshold_percent: float = 5.0
    ) -> List[Tuple[str, float, float, float]]:
        """检测性能回归"""
        regressions = []

        for metric, base_val in baseline.items():
            if metric in current:
                curr_val = current[metric]
                diff_pct = ((curr_val - base_val) / base_val * 100) if base_val != 0 else 0

                if diff_pct < -threshold_percent:  # 降低超过阈值
                    regressions.append((metric, base_val, curr_val, diff_pct))

        return sorted(regressions, key=lambda x: x[3])  # 按差异排序

    def export_report(self, path: str, report: ComparisonReport):
        """导出报告到JSON"""
        with open(path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

    def export_csv(self, path: str):
        """导出对比结果到CSV"""
        with open(path, 'w') as f:
            f.write("Metric,Python_Value,RTL_Value,Difference,Pct_Diff,Status\n")
            for result in self.comparison_results:
                f.write(f"{result.metric_name},{result.python_value},"
                       f"{result.rtl_value},{result.difference},"
                       f"{result.percent_difference},{result.status.value}\n")


class BandwidthAnalyzer:
    """
    带宽分析器

    分析带宽性能:
    - 峰值带宽
    - 持续带宽
    - 通道效率
    - 对比分析
    """

    def __init__(self):
        self.samples: List[Dict[str, Any]] = []

    def add_sample(self, cycle: int, bytes_transferred: int, cycle_duration_ns: float):
        """添加带宽样本"""
        bandwidth_gbs = (bytes_transferred / cycle_duration_ns) if cycle_duration_ns > 0 else 0
        self.samples.append({
            'cycle': cycle,
            'bytes': bytes_transferred,
            'bandwidth_gbs': bandwidth_gbs,
        })

    def analyze(self) -> Dict[str, Any]:
        """分析带宽"""
        if not self.samples:
            return {}

        bandwidths = [s['bandwidth_gbs'] for s in self.samples]
        stats = ResultAnalyzer().compute_statistics(bandwidths)

        # 峰值和持续带宽
        peak_bandwidth = max(bandwidths)
        sorted_bandwidths = sorted(bandwidths, reverse=True)

        # 持续带宽 (P50)
        sustained_bandwidth = sorted_bandwidths[len(sorted_bandwidths) // 2]

        # 带宽利用率
        theoretical_peak = 2048.0  # HBM4 @ 16 Gbps
        peak_utilization = (peak_bandwidth / theoretical_peak * 100) if theoretical_peak > 0 else 0

        return {
            'peak_bandwidth_gbs': peak_bandwidth,
            'sustained_bandwidth_gbs': sustained_bandwidth,
            'average_bandwidth_gbs': stats.mean,
            'peak_utilization_percent': peak_utilization,
            'statistics': stats.to_dict(),
        }


class LatencyAnalyzer:
    """
    延迟分析器

    分析延迟特性:
    - 延迟分布
    - 百分位数
    - 异常值
    - 趋势分析
    """

    def __init__(self):
        self.latencies: List[int] = []
        self.by_pattern: Dict[str, List[int]] = {}

    def add_latency(self, latency: int, pattern: Optional[str] = None):
        """添加延迟样本"""
        self.latencies.append(latency)
        if pattern:
            if pattern not in self.by_pattern:
                self.by_pattern[pattern] = []
            self.by_pattern[pattern].append(latency)

    def analyze(self) -> Dict[str, Any]:
        """分析延迟"""
        if not self.latencies:
            return {}

        stats = ResultAnalyzer().compute_statistics([float(l) for l in self.latencies])

        # 按模式分析
        pattern_stats = {}
        for pattern, lat_list in self.by_pattern.items():
            if lat_list:
                pattern_stats[pattern] = ResultAnalyzer().compute_statistics(
                    [float(l) for l in lat_list]
                ).to_dict()

        return {
            'mean_latency_cycles': stats.mean,
            'median_latency_cycles': stats.median,
            'min_latency_cycles': stats.min_val,
            'max_latency_cycles': stats.max_val,
            'std_dev_cycles': stats.std_dev,
            'percentiles': {
                'p50': stats.p50,
                'p75': stats.p75,
                'p90': stats.p90,
                'p95': stats.p95,
                'p99': stats.p99,
            },
            'by_pattern': pattern_stats,
        }

    def detect_anomalies(self, threshold_z: float = 2.0) -> List[int]:
        """检测延迟异常"""
        if len(self.latencies) < 3:
            return []

        mean = statistics.mean(self.latencies)
        std = statistics.stdev(self.latencies)

        anomalies = []
        for i, lat in enumerate(self.latencies):
            z_score = abs((lat - mean) / std) if std > 0 else 0
            if z_score > threshold_z:
                anomalies.append(i)

        return anomalies


def create_analyzer(tolerance_percent: float = 5.0) -> ResultAnalyzer:
    """创建结果分析器"""
    return ResultAnalyzer(tolerance_percent=tolerance_percent)


def quick_compare(
    python_stats: Dict[str, Any],
    rtl_stats: Dict[str, Any]
) -> ComparisonReport:
    """快速对比两组统计数据"""
    analyzer = ResultAnalyzer()

    # 对比关键指标
    metrics = [
        ('total_cycles', 'total_cycles'),
        ('completed_requests', 'completed_requests'),
        ('avg_latency', 'avg_latency'),
        ('throughput_gbps', 'throughput_gbps'),
        ('row_hit_rate', 'row_hit_rate'),
    ]

    for py_key, rtl_key in metrics:
        if py_key in python_stats and rtl_key in rtl_stats:
            analyzer.compare_metric(
                py_key,
                python_stats[py_key],
                rtl_stats[rtl_key]
            )

    return analyzer.generate_report()


def generate_comparison_html(
    report: ComparisonReport,
    output_path: str
):
    """生成HTML对比报告"""
    status_colors = {
        RegressionStatus.PASS: '#4caf50',
        RegressionStatus.WARNING: '#ff9800',
        RegressionStatus.REGRESSION: '#f44336',
        RegressionStatus.IMPROVEMENT: '#2196f3',
    }

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HBM Python vs RTL Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4caf50; padding-bottom: 10px; }}
        h2 {{ color: #666; margin-top: 30px; }}
        .summary {{ background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee; }}
        .metric-name {{ font-weight: bold; }}
        .metric-value {{ color: #666; }}
        .status {{ padding: 5px 10px; border-radius: 3px; color: white; }}
        .status-pass {{ background: #4caf50; }}
        .status-warning {{ background: #ff9800; }}
        .status-regression {{ background: #f44336; }}
        .status-improvement {{ background: #2196f3; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4caf50; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>HBM Python vs RTL Comparison Report</h1>
        <p>Generated: {report.timestamp}</p>

        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">
                <span>Total Transactions:</span>
                <span class="metric-value">{report.total_transactions}</span>
            </div>
            <div class="metric">
                <span>Matching:</span>
                <span class="metric-value">{report.matching_transactions}</span>
            </div>
            <div class="metric">
                <span>Mismatching:</span>
                <span class="metric-value">{report.mismatching_transactions}</span>
            </div>
            <div class="metric">
                <span>Match Rate:</span>
                <span class="metric-value">{report.match_rate * 100:.2f}%</span>
            </div>
            <div class="metric">
                <span>Status:</span>
                <span class="metric-value">
                    <span class="status status-{report.overall_status.value}">{report.overall_status.value.upper()}</span>
                </span>
            </div>
        </div>

        <h2>Timing Analysis</h2>
        <table>
            <tr>
                <th>Transaction ID</th>
                <th>Python Latency</th>
                <th>RTL Latency</th>
                <th>Difference</th>
                <th>Data Match</th>
            </tr>
"""

    for analysis in report.timing_analyses[:50]:  # Limit to 50 rows
        html += f"""
            <tr>
                <td>{analysis.transaction_id}</td>
                <td>{analysis.python_latency}</td>
                <td>{analysis.rtl_latency}</td>
                <td>{analysis.latency_diff}</td>
                <td>{'Yes' if analysis.data_match else 'No'}</td>
            </tr>
"""

    html += """
        </table>
    </div>
</body>
</html>"""

    with open(output_path, 'w') as f:
        f.write(html)


if __name__ == '__main__':
    # 测试对比功能
    print("Testing Result Comparison Module...")
    print()

    # 创建分析器
    analyzer = ResultAnalyzer(tolerance_percent=5.0)

    # 对比指标
    analyzer.compare_metric("throughput", 1500.0, 1480.0)
    analyzer.compare_metric("avg_latency", 45.0, 47.0)
    analyzer.compare_metric("row_hit_rate", 0.62, 0.60)

    # 分析时序
    for i in range(10):
        py_lat = 40 + i
        rtl_lat = 42 + i
        analyzer.analyze_timing(i, py_lat, rtl_lat)

    # 生成报告
    report = analyzer.generate_report(ComparisonType.STATISTICAL)
    report.print_summary()

    print()

    # 检测回归
    baseline = {'bandwidth': 1500.0, 'latency': 45.0}
    current = {'bandwidth': 1400.0, 'latency': 50.0}
    regressions = analyzer.detect_regressions(baseline, current)

    if regressions:
        print("Detected Regressions:")
        for metric, base, curr, diff in regressions:
            print(f"  {metric}: {base} -> {curr} ({diff:+.2f}%)")

    print()
    print("Comparison test complete!")
