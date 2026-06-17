"""
HBM3 Ramulator2 vs Python model comparison framework

This module provides tools to compare the Python HBM model against
Ramulator2 baseline results for validation.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
from datetime import datetime

from sim.trace_replayer import TraceReplayer, TraceFormat, TraceRequest
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern, SimulationStats
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.request import HBMRequest

logger = logging.getLogger(__name__)


@dataclass
class ComparisonMetrics:
    """Comparison metrics between Ramulator2 and Python model

    Attributes:
        row_hits: Number of row buffer hits
        row_misses: Number of row buffer misses (same bank, different row)
        row_conflicts: Number of row conflicts (ACT + PRE required)
        avg_latency: Average request latency in cycles
        min_latency: Minimum latency in cycles
        max_latency: Maximum latency in cycles
        total_requests: Total number of requests
        completed_requests: Number of completed requests
    """
    # Row buffer metrics
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0

    # Latency metrics
    avg_latency: float = 0.0
    min_latency: float = 0.0
    max_latency: float = 0.0

    # Throughput metrics
    total_requests: int = 0
    completed_requests: int = 0

    @property
    def row_hit_rate(self) -> float:
        """Calculate row buffer hit rate

        Returns:
            Row hit rate as a fraction [0.0, 1.0]
        """
        total = self.row_hits + self.row_misses + self.row_conflicts
        if total == 0:
            return 0.0
        return self.row_hits / total

    def to_dict(self) -> Dict:
        """Export metrics as dictionary

        Returns:
            Dictionary representation including computed row_hit_rate
        """
        d = asdict(self)
        d['row_hit_rate'] = self.row_hit_rate
        return d


@dataclass
class ComparisonReport:
    """Comparison report between Ramulator2 and Python model

    Attributes:
        trace_name: Name of the trace being compared
        ramulator_metrics: Metrics from Ramulator2
        python_metrics: Metrics from Python model
        errors: Dictionary of computed errors
        timestamp: Timestamp of the comparison
    """
    trace_name: str
    ramulator_metrics: ComparisonMetrics
    python_metrics: ComparisonMetrics
    errors: Dict[str, float] = field(default_factory=dict)
    timestamp: str = ""

    def compute_errors(self) -> None:
        """Compute error metrics between Ramulator and Python results

        Calculates:
        - hit_rate_error_pp: Absolute difference in hit rate (percentage points)
        - latency_error_pct: Percentage error in average latency
        - row_hit_error_pct: Percentage error in row hit count
        """
        r = self.ramulator_metrics
        p = self.python_metrics

        # Hit rate error (percentage points)
        self.errors['hit_rate_error_pp'] = abs(r.row_hit_rate - p.row_hit_rate) * 100

        # Latency error (percentage)
        if r.avg_latency > 0:
            self.errors['latency_error_pct'] = abs(r.avg_latency - p.avg_latency) / r.avg_latency * 100

        # Row hit absolute error (percentage)
        if r.row_hits > 0:
            self.errors['row_hit_error_pct'] = abs(r.row_hits - p.row_hits) / r.row_hits * 100

    def to_dict(self) -> Dict:
        """Export report as dictionary

        Returns:
            Dictionary representation of the comparison report
        """
        return {
            'trace_name': self.trace_name,
            'ramulator': self.ramulator_metrics.to_dict(),
            'python': self.python_metrics.to_dict(),
            'errors': self.errors,
            'timestamp': self.timestamp
        }


@dataclass
class RamulatorResult:
    """Ramulator2 simulation result

    Contains parsed or known results from Ramulator2 simulation runs.

    Attributes:
        trace_name: Name of the trace file
        total_requests: Total number of requests
        row_hits: Number of row buffer hits
        row_misses: Number of row buffer misses
        row_conflicts: Number of row conflicts
        avg_latency: Average latency in cycles
        total_cycles: Total simulation cycles
    """
    trace_name: str
    total_requests: int
    row_hits: int
    row_misses: int
    row_conflicts: int
    avg_latency: float
    total_cycles: int


def parse_ramulator_log(log_file: str, trace_name: str) -> RamulatorResult:
    """Parse Ramulator2 output log file

    Parses Ramulator2 log files to extract key metrics. If parsing fails
    or metrics are not found, uses known baseline values from summary.md.

    Args:
        log_file: Path to Ramulator2 log file
        trace_name: Name of the trace being parsed

    Returns:
        RamulatorResult with parsed or default values
    """
    try:
        with open(log_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        logger.warning(f"Log file not found: {log_file}, using known values")
        return _get_default_ramulator_result(trace_name)

    # Initialize values
    total_requests = 0
    row_hits = 0
    row_misses = 0
    row_conflicts = 0
    avg_latency = 0.0
    total_cycles = 0

    # Parse log content
    for line in content.split('\n'):
        line_lower = line.lower().strip()

        # Parse latency
        if 'average latency' in line_lower or 'avg latency' in line_lower:
            try:
                # Handle formats like "Average latency: 12.93 cycles" or "Avg Latency: 12.93"
                parts = line.split(':')
                if len(parts) >= 2:
                    val_str = parts[1].strip().split()[0]
                    avg_latency = float(val_str)
            except (ValueError, IndexError):
                pass

        # Parse total requests
        if 'total requests' in line_lower:
            try:
                parts = line.split(':')
                if len(parts) >= 2:
                    total_requests = int(parts[1].strip())
            except (ValueError, IndexError):
                pass

        # Parse row hits
        if 'row hits' in line_lower or 'row buffer hits' in line_lower:
            try:
                parts = line.split(':')
                if len(parts) >= 2:
                    row_hits = int(parts[1].strip())
            except (ValueError, IndexError):
                pass

        # Parse row misses
        if 'row misses' in line_lower or 'row buffer misses' in line_lower:
            try:
                parts = line.split(':')
                if len(parts) >= 2:
                    row_misses = int(parts[1].strip())
            except (ValueError, IndexError):
                pass

        # Parse row conflicts
        if 'row conflicts' in line_lower or 'row buffer conflicts' in line_lower:
            try:
                parts = line.split(':')
                if len(parts) >= 2:
                    row_conflicts = int(parts[1].strip())
            except (ValueError, IndexError):
                pass

        # Parse total cycles
        if 'total cycles' in line_lower or 'memory cycles' in line_lower:
            try:
                parts = line.split(':')
                if len(parts) >= 2:
                    total_cycles = int(parts[1].strip())
            except (ValueError, IndexError):
                pass

    # If no latency was parsed, use default
    if avg_latency == 0.0:
        avg_latency = _get_default_latency(trace_name)

    return RamulatorResult(
        trace_name=trace_name,
        total_requests=total_requests,
        row_hits=row_hits,
        row_misses=row_misses,
        row_conflicts=row_conflicts,
        avg_latency=avg_latency,
        total_cycles=total_cycles
    )


def _get_default_ramulator_result(trace_name: str) -> RamulatorResult:
    """Get default Ramulator result for a trace

    Uses known baseline values from summary.md.

    Args:
        trace_name: Name of the trace

    Returns:
        RamulatorResult with known baseline values
    """
    known_results = {
        'seq_rd': RamulatorResult(
            trace_name='seq_rd',
            total_requests=100000,
            row_hits=62481,
            row_misses=24992,
            row_conflicts=12495,
            avg_latency=12.93,
            total_cycles=924397
        ),
        'stride_rd': RamulatorResult(
            trace_name='stride_rd',
            total_requests=100000,
            row_hits=0,
            row_misses=32,
            row_conflicts=99935,
            avg_latency=12.66,
            total_cycles=2323041
        ),
        'random_rdwr': RamulatorResult(
            trace_name='random_rdwr',
            total_requests=100000,
            row_hits=17,
            row_misses=3550,
            row_conflicts=96383,
            avg_latency=14.14,
            total_cycles=369956
        )
    }

    return known_results.get(trace_name, RamulatorResult(
        trace_name=trace_name,
        total_requests=0,
        row_hits=0,
        row_misses=0,
        row_conflicts=0,
        avg_latency=0.0,
        total_cycles=0
    ))


def _get_default_latency(trace_name: str) -> float:
    """Get default latency for a trace

    Args:
        trace_name: Name of the trace

    Returns:
        Default latency in cycles
    """
    latencies = {
        'seq_rd': 12.93,
        'stride_rd': 12.66,
        'random_rdwr': 14.14,
    }
    return latencies.get(trace_name, 0.0)


class ComparisonFramework:
    """Framework for comparing Ramulator2 and Python model results

    This framework enables systematic validation of the Python HBM model
    against Ramulator2 baseline results by:
    1. Loading Ramulator2 traces and known results
    2. Running Python model simulations with the same traces
    3. Computing and reporting differences in key metrics

    Attributes:
        ramulator_trace_dir: Directory containing Ramulator2 trace files
        ramulator_log_dir: Directory containing Ramulator2 log files
        output_dir: Directory for comparison output
        reports: List of completed comparison reports
    """

    def __init__(
        self,
        ramulator_trace_dir: str = "research/hbm-modeling/traces",
        ramulator_log_dir: str = "research/hbm-modeling/results",
        output_dir: str = "sim/comparison_results"
    ):
        """Initialize comparison framework

        Args:
            ramulator_trace_dir: Path to Ramulator2 trace directory
            ramulator_log_dir: Path to Ramulator2 results directory
            output_dir: Path for comparison output
        """
        self.ramulator_trace_dir = Path(ramulator_trace_dir)
        self.ramulator_log_dir = Path(ramulator_log_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.reports: List[ComparisonReport] = []

    def run_trace_comparison(
        self,
        trace_name: str,
        use_existing_trace: bool = True
    ) -> ComparisonReport:
        """Run comparison for a single trace

        Args:
            trace_name: Name of the trace (without .trace extension)
            use_existing_trace: If True, use existing trace file

        Returns:
            ComparisonReport with results from both simulators

        Raises:
            FileNotFoundError: If trace file is not found and use_existing_trace is True
        """
        logger.info(f"Running comparison for trace: {trace_name}")

        # 1. Load Ramulator2 trace (for Python simulation)
        trace_file = self.ramulator_trace_dir / f"{trace_name}.trace"
        replayer = None
        if trace_file.exists():
            replayer = TraceReplayer(str(trace_file), TraceFormat.RAMULATOR_LD_ST)
            replayer.load()
        elif use_existing_trace:
            raise FileNotFoundError(f"Trace file not found: {trace_file}")

        # 2. Parse Ramulator2 results
        log_file = self.ramulator_log_dir / f"hbm3_{trace_name}.log"
        if log_file.exists():
            ramulator_result = parse_ramulator_log(str(log_file), trace_name)
        else:
            # Use known baseline values from summary.md
            ramulator_result = self._get_known_ramulator_result(trace_name)

        ramulator_metrics = ComparisonMetrics(
            row_hits=ramulator_result.row_hits,
            row_misses=ramulator_result.row_misses,
            row_conflicts=ramulator_result.row_conflicts,
            avg_latency=ramulator_result.avg_latency,
            total_requests=ramulator_result.total_requests,
            completed_requests=ramulator_result.total_requests
        )

        # 3. Run Python model simulation
        if replayer:
            python_metrics = self._run_python_simulation(replayer)
        else:
            # No trace file, run synthetic benchmark matching the pattern
            python_metrics = self._run_python_synthetic(trace_name)

        # 4. Generate comparison report
        report = ComparisonReport(
            trace_name=trace_name,
            ramulator_metrics=ramulator_metrics,
            python_metrics=python_metrics,
            timestamp=self._get_timestamp()
        )
        report.compute_errors()

        self.reports.append(report)
        return report

    def _run_python_simulation(self, replayer: TraceReplayer) -> ComparisonMetrics:
        """Run Python simulation with trace replayer

        Uses the trace replayer to feed requests into the HBMSimulator.

        Args:
            replayer: TraceReplayer with loaded requests

        Returns:
            ComparisonMetrics from the simulation
        """
        # Create simulation config
        # Use HBM3 default config matching Ramulator2 settings
        config = SimulationConfig(
            simulation_time_us=1000.0,  # Enough time to process all requests
            request_rate=1.0,  # Submit all requests as fast as possible
            read_ratio=0.7,
            max_requests_per_cycle=8,  # Allow parallel channel access
            hbm_config=HBM3_DEFAULT,
            queue_depth=512,  # Large queue for burst traffic
        )

        sim = HBMSimulator(config)

        # Submit all requests from trace
        for req in replayer.requests():
            sim.controller.submit_request(
                HBMRequest(
                    addr=req.addr,
                    length=64,
                    is_read=req.is_read
                )
            )

        # Run simulation until all requests complete or max cycles reached
        while sim.current_cycle < sim.max_cycles:
            sim.step()
            if sim.stats.completed_requests >= replayer.total_requests:
                break

        # Extract metrics from simulation stats
        stats = sim.stats

        return ComparisonMetrics(
            row_hits=stats.row_hits,
            row_misses=stats.row_misses,
            row_conflicts=stats.row_conflicts,
            avg_latency=stats.avg_latency,
            total_requests=stats.total_requests,
            completed_requests=stats.completed_requests,
            min_latency=stats.min_latency_cycles if stats.min_latency_cycles > 0 else 0,
            max_latency=stats.max_latency_cycles
        )

    def _run_python_synthetic(self, trace_name: str) -> ComparisonMetrics:
        """Run Python simulation with synthetic traffic matching trace pattern

        Used when no trace file exists, generates traffic matching the
        known characteristics of the specified trace pattern.

        Args:
            trace_name: Name of the trace pattern

        Returns:
            ComparisonMetrics from the simulation
        """
        # Determine traffic pattern based on trace name
        if 'seq' in trace_name.lower():
            pattern = TrafficPattern.SEQUENTIAL
        elif 'stride' in trace_name.lower():
            pattern = TrafficPattern.STRIDE
        else:
            pattern = TrafficPattern.RANDOM

        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=pattern,
            request_rate=1.0,
            read_ratio=1.0 if 'rd' in trace_name.lower() and 'wr' not in trace_name.lower() else 0.7,
            max_requests_per_cycle=8,
            hbm_config=HBM3_DEFAULT,
            queue_depth=512,
        )

        sim = HBMSimulator(config)
        sim.run()

        stats = sim.stats

        return ComparisonMetrics(
            row_hits=stats.row_hits,
            row_misses=stats.row_misses,
            row_conflicts=stats.row_conflicts,
            avg_latency=stats.avg_latency,
            total_requests=stats.total_requests,
            completed_requests=stats.completed_requests,
            min_latency=stats.min_latency_cycles if stats.min_latency_cycles > 0 else 0,
            max_latency=stats.max_latency_cycles
        )

    def _get_known_ramulator_result(self, trace_name: str) -> RamulatorResult:
        """Get known Ramulator2 result from summary.md

        Args:
            trace_name: Name of the trace

        Returns:
            RamulatorResult with known baseline values
        """
        return _get_default_ramulator_result(trace_name)

    def run_all_comparisons(self, traces: List[str] = None) -> List[ComparisonReport]:
        """Run comparisons for multiple traces

        Args:
            traces: List of trace names to compare. If None, uses default traces.

        Returns:
            List of ComparisonReport for all completed comparisons
        """
        if traces is None:
            traces = ['seq_rd', 'stride_rd', 'random_rdwr']

        for trace in traces:
            try:
                self.run_trace_comparison(trace)
            except Exception as e:
                logger.error(f"Failed to compare trace {trace}: {e}")

        return self.reports

    def generate_report(self, output_file: str = None) -> str:
        """Generate comparison report

        Args:
            output_file: Output file path. If None, uses default in output_dir.

        Returns:
            Path to the generated report file
        """
        if output_file is None:
            output_file = self.output_dir / 'comparison_report.json'

        report_data = {
            'comparisons': {r.trace_name: r.to_dict() for r in self.reports},
            'summary': self._generate_summary(),
            'timestamp': self._get_timestamp()
        }

        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Report saved to {output_file}")
        return str(output_file)

    def _generate_summary(self) -> Dict:
        """Generate summary of all comparisons

        Returns:
            Dictionary with summary statistics
        """
        if not self.reports:
            return {}

        total_hit_rate_error = sum(r.errors.get('hit_rate_error_pp', 0) for r in self.reports)
        avg_hit_rate_error = total_hit_rate_error / len(self.reports) if self.reports else 0

        return {
            'num_comparisons': len(self.reports),
            'avg_hit_rate_error_pp': avg_hit_rate_error,
            'best_match': min(self.reports, key=lambda r: r.errors.get('hit_rate_error_pp', 999)).trace_name
                if self.reports else None,
            'worst_match': max(self.reports, key=lambda r: r.errors.get('hit_rate_error_pp', 0)).trace_name
                if self.reports else None
        }

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp string

        Returns:
            Timestamp in ISO format
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def main():
    """Command-line interface for comparison framework"""
    import argparse

    parser = argparse.ArgumentParser(description='HBM3 Ramulator2 vs Python comparison')
    parser.add_argument('--traces-dir', default='research/hbm-modeling/traces')
    parser.add_argument('--logs-dir', default='research/hbm-modeling/results')
    parser.add_argument('--output', default='sim/comparison_results')
    parser.add_argument('--traces', nargs='+', default=['seq_rd', 'stride_rd', 'random_rdwr'])
    parser.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    framework = ComparisonFramework(
        ramulator_trace_dir=args.traces_dir,
        ramulator_log_dir=args.logs_dir,
        output_dir=args.output
    )

    framework.run_all_comparisons(args.traces)
    report_file = framework.generate_report()

    print(f"\nComparison complete. Report: {report_file}")

    # Print summary
    for report in framework.reports:
        print(f"\n{report.trace_name}:")
        print(f"  Ramulator row_hit_rate: {report.ramulator_metrics.row_hit_rate:.2%}")
        print(f"  Python row_hit_rate: {report.python_metrics.row_hit_rate:.2%}")
        print(f"  Hit rate error: {report.errors.get('hit_rate_error_pp', 0):.2f} pp")
        print(f"  Latency error: {report.errors.get('latency_error_pct', 0):.2f}%")


if __name__ == '__main__':
    main()
