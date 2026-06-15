#!/usr/bin/env python3
"""
Model vs Ramulator2 Comparison Pipeline

Compares Python model simulation results with Ramulator2 cycle-accurate simulation.
This validates that the Python model accurately predicts HBM behavior.

Usage:
    python scripts/comparison/compare_model_ramulator.py \
        --model-results results/model.json \
        --ramulator-log results/ramulator.log \
        --output results/comparison.json
"""

import argparse
import json
import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Add project root to path
_project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, _project_root)

try:
    from research.hbm_modeling.scripts.parse_ramulator_log import RamulatorLogParser, RamulatorLogResult
except ImportError:
    # Fallback: define minimal classes if parse_ramulator_log is not available
    class RamulatorLogParser:
        def __init__(self, log_file):
            self.log_file = log_file
        def parse(self):
            raise NotImplementedError("Ramulator log parser not available")
    class RamulatorLogResult:
        pass


@dataclass
class ComparisonMetrics:
    """Metrics for comparison"""
    metric_name: str
    model_value: float
    ramulator_value: float
    difference: float
    percent_diff: float
    within_threshold: bool


@dataclass
class ComparisonResult:
    """Result of comparison between model and Ramulator2"""
    model_file: str
    ramulator_file: str
    metrics: List[ComparisonMetrics]
    all_passed: bool
    summary: str


def load_model_results(filepath: str) -> Dict:
    """Load model results from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
        # Handle different formats
        if isinstance(data, list):
            # Aggregate list of results
            total = len(data)
            return {
                'avg_latency': sum(d.get('avg_latency', 0) for d in data) / total if total > 0 else 0,
                'row_hit_rate': sum(d.get('row_hit_rate', 0) for d in data) / total if total > 0 else 0,
                'throughput_gbps': sum(d.get('throughput_gbps', 0) for d in data) / total if total > 0 else 0,
                'total_requests': sum(d.get('total_requests', 0) for d in data),
            }
        return data


def parse_ramulator_results(log_file: str) -> Dict:
    """Parse Ramulator2 log file"""
    if not os.path.exists(log_file):
        raise FileNotFoundError(f"Log file not found: {log_file}")

    parser = RamulatorLogParser(log_file)
    result = parser.parse()

    # Extract relevant metrics
    total_hits = result.total_row_hits
    total_misses = result.total_row_misses
    total_conflicts = result.total_row_conflicts
    total_requests = total_hits + total_misses + total_conflicts

    hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
    avg_latency = result.avg_read_latency

    return {
        'avg_latency': avg_latency,
        'row_hit_rate': hit_rate,
        'total_requests': total_requests,
        'row_hits': total_hits,
        'row_misses': total_misses,
        'row_conflicts': total_conflicts,
        'memory_cycles': result.memory_system_cycles,
    }


def compare_values(model_val: float, ramulator_val: float, threshold_pct: float = 10.0) -> ComparisonMetrics:
    """Compare two values and return metrics"""
    diff = abs(model_val - ramulator_val)
    pct_diff = (diff / ramulator_val * 100) if ramulator_val != 0 else 0.0
    within_threshold = pct_diff <= threshold_pct

    return ComparisonMetrics(
        metric_name="",
        model_value=model_val,
        ramulator_value=ramulator_val,
        difference=diff,
        percent_diff=pct_diff,
        within_threshold=within_threshold
    )


def compare_results(model_results: Dict, ramulator_results: Dict, threshold_pct: float = 15.0) -> ComparisonResult:
    """Compare model and Ramulator2 results"""
    metrics = []

    # Compare row hit rate (most important metric)
    if 'row_hit_rate' in model_results and 'row_hit_rate' in ramulator_results:
        m = compare_values(
            model_results['row_hit_rate'],
            ramulator_results['row_hit_rate'],
            threshold_pct
        )
        m.metric_name = 'row_hit_rate'
        metrics.append(m)

    # Compare average latency (in cycles)
    if 'avg_latency' in model_results and 'avg_latency' in ramulator_results:
        m = compare_values(
            model_results['avg_latency'],
            ramulator_results['avg_latency'],
            threshold_pct * 2  # Allow more variance for latency
        )
        m.metric_name = 'avg_latency'
        metrics.append(m)

    # Compare throughput
    if 'throughput_gbps' in model_results:
        ramulator_throughput = calculate_ramulator_throughput(ramulator_results)
        m = compare_values(
            model_results['throughput_gbps'],
            ramulator_throughput,
            threshold_pct
        )
        m.metric_name = 'throughput_gbps'
        metrics.append(m)

    # Compare row buffer statistics
    for stat in ['row_hits', 'row_misses', 'row_conflicts']:
        model_val = model_results.get(stat, 0)
        ramulator_val = ramulator_results.get(stat, 0)
        total = ramulator_val + model_val
        if total > 0:
            diff = abs(model_val - ramulator_val)
            pct_diff = (diff / ramulator_val * 100) if ramulator_val > 0 else 0
            metrics.append(ComparisonMetrics(
                metric_name=stat,
                model_value=model_val,
                ramulator_value=ramulator_val,
                difference=diff,
                percent_diff=pct_diff,
                within_threshold=pct_diff <= threshold_pct
            ))

    all_passed = all(m.within_threshold for m in metrics)

    return ComparisonResult(
        model_file="",
        ramulator_file="",
        metrics=metrics,
        all_passed=all_passed,
        summary=""
    )


def calculate_ramulator_throughput(ramulator_results: Dict) -> float:
    """Calculate throughput from Ramulator2 results"""
    cycles = ramulator_results.get('memory_cycles', 0)
    requests = ramulator_results.get('total_requests', 0)

    if cycles == 0:
        return 0.0

    # Assume HBM3: 6.4 Gb/s/pin, 1024 pins
    # Each request = 32 bytes (burst length)
    bytes_transferred = requests * 32 * 4  # 4 bursts per request

    # tCK = 781.25 ps for 1.28 GHz
    ns_per_cycle = 0.78125
    total_ns = cycles * ns_per_cycle

    return (bytes_transferred / (total_ns * 1e-9)) / 1e9  # GB/s


def print_comparison(result: ComparisonResult, verbose: bool = False):
    """Print comparison results"""
    print("=" * 70)
    print("Model vs Ramulator2 Comparison Results")
    print("=" * 70)

    if result.model_file:
        print(f"Model Results: {result.model_file}")
    if result.ramulator_file:
        print(f"Ramulator2 Results: {result.ramulator_file}")

    print()
    print(f"{'Metric':<20} {'Model':>12} {'Ramulator2':>12} {'Diff':>10} {'%Diff':>10} {'Status':>10}")
    print("-" * 70)

    for m in result.metrics:
        status = "PASS" if m.within_threshold else "FAIL"
        pct_str = f"{m.percent_diff:.1f}%" if m.percent_diff > 0 else "-"
        print(f"{m.metric_name:<20} {m.model_value:>12.4f} {m.ramulator_value:>12.4f} "
              f"{m.difference:>10.4f} {pct_str:>10} {status:>10}")

    print("=" * 70)
    print(f"Overall Status: {'PASS' if result.all_passed else 'FAIL'}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Compare Model and Ramulator2 simulation results')
    parser.add_argument('--model-results', '-m', required=True, help='Model simulation results JSON')
    parser.add_argument('--ramulator-log', '-r', required=True, help='Ramulator2 log file')
    parser.add_argument('--threshold', '-t', type=float, default=15.0, help='Threshold percentage (default: 15)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output', '-o', help='Output JSON file for results')

    args = parser.parse_args()

    # Load results
    try:
        model_results = load_model_results(args.model_results)
        ramulator_results = parse_ramulator_results(args.ramulator_log)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Compare
    result = compare_results(model_results, ramulator_results, args.threshold)
    result.model_file = args.model_results
    result.ramulator_file = args.ramulator_log

    # Print results
    print_comparison(result, args.verbose)

    # Save results if requested
    if args.output:
        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump({
                'model_file': result.model_file,
                'ramulator_file': result.ramulator_file,
                'metrics': [
                    {
                        'metric_name': m.metric_name,
                        'model_value': m.model_value,
                        'ramulator_value': m.ramulator_value,
                        'difference': m.difference,
                        'percent_diff': m.percent_diff,
                        'within_threshold': m.within_threshold
                    }
                    for m in result.metrics
                ],
                'all_passed': result.all_passed
            }, f, indent=2)
        print(f"\nResults saved to {args.output}")

    # Exit with appropriate code
    sys.exit(0 if result.all_passed else 1)


if __name__ == '__main__':
    main()