#!/usr/bin/env python3
"""
RTL-to-Model Comparison Pipeline

Compares RTL simulation results with Python model simulation results.
This validates that the Python model accurately predicts RTL behavior.

Usage:
    python scripts/comparison/compare_rtl_model.py --rtl-results results/rtl.json --model-results results/model.json
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ComparisonMetrics:
    """Metrics for comparison"""
    metric_name: str
    rtl_value: float
    model_value: float
    difference: float
    percent_diff: float
    within_threshold: bool


@dataclass
class ComparisonResult:
    """Result of comparison between RTL and model"""
    rtl_file: str
    model_file: str
    metrics: List[ComparisonMetrics]
    all_passed: bool
    summary: str


def load_results(filepath: str) -> Dict:
    """Load results from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def compare_values(rtl_val: float, model_val: float, threshold_pct: float = 10.0) -> ComparisonMetrics:
    """Compare two values and return metrics"""
    diff = abs(rtl_val - model_val)
    pct_diff = (diff / rtl_val * 100) if rtl_val != 0 else 0.0
    within_threshold = pct_diff <= threshold_pct

    return ComparisonMetrics(
        metric_name="",
        rtl_value=rtl_val,
        model_value=model_val,
        difference=diff,
        percent_diff=pct_diff,
        within_threshold=within_threshold
    )


def compare_results(rtl_results: Dict, model_results: Dict, threshold_pct: float = 10.0) -> ComparisonResult:
    """Compare RTL and model results"""
    metrics = []

    # Compare throughput
    if 'throughput_gbps' in rtl_results and 'throughput_gbps' in model_results:
        m = compare_values(
            rtl_results['throughput_gbps'],
            model_results['throughput_gbps'],
            threshold_pct
        )
        m.metric_name = 'throughput_gbps'
        metrics.append(m)

    # Compare row hit rate
    if 'row_hit_rate' in rtl_results and 'row_hit_rate' in model_results:
        m = compare_values(
            rtl_results['row_hit_rate'],
            model_results['row_hit_rate'],
            threshold_pct
        )
        m.metric_name = 'row_hit_rate'
        metrics.append(m)

    # Compare average latency
    if 'avg_latency' in rtl_results and 'avg_latency' in model_results:
        m = compare_values(
            rtl_results['avg_latency'],
            model_results['avg_latency'],
            threshold_pct * 2  # Latency can vary more
        )
        m.metric_name = 'avg_latency'
        metrics.append(m)

    # Compare total requests
    if 'total_requests' in rtl_results and 'total_requests' in model_results:
        rtl_req = rtl_results['total_requests']
        model_req = model_results['total_requests']
        diff = abs(rtl_req - model_req)
        within_threshold = diff <= 10  # Allow small difference in count
        metrics.append(ComparisonMetrics(
            metric_name='total_requests',
            rtl_value=rtl_req,
            model_value=model_req,
            difference=diff,
            percent_diff=0,
            within_threshold=within_threshold
        ))

    all_passed = all(m.within_threshold for m in metrics)

    return ComparisonResult(
        rtl_file="",
        model_file="",
        metrics=metrics,
        all_passed=all_passed,
        summary=""
    )


def print_comparison(result: ComparisonResult, verbose: bool = False):
    """Print comparison results"""
    print("=" * 70)
    print("RTL-to-Model Comparison Results")
    print("=" * 70)

    if result.rtl_file:
        print(f"RTL Results: {result.rtl_file}")
    if result.model_file:
        print(f"Model Results: {result.model_file}")

    print()
    print(f"{'Metric':<20} {'RTL':>12} {'Model':>12} {'Diff':>10} {'%Diff':>10} {'Status':>10}")
    print("-" * 70)

    for m in result.metrics:
        status = "PASS" if m.within_threshold else "FAIL"
        pct_str = f"{m.percent_diff:.1f}%" if m.percent_diff > 0 else "-"
        print(f"{m.metric_name:<20} {m.rtl_value:>12.3f} {m.model_value:>12.3f} "
              f"{m.difference:>10.3f} {pct_str:>10} {status:>10}")

    print("=" * 70)
    print(f"Overall Status: {'PASS' if result.all_passed else 'FAIL'}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Compare RTL and Model simulation results')
    parser.add_argument('--rtl-results', '-r', required=True, help='RTL simulation results JSON')
    parser.add_argument('--model-results', '-m', required=True, help='Model simulation results JSON')
    parser.add_argument('--threshold', '-t', type=float, default=10.0, help='Threshold percentage (default: 10)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output', '-o', help='Output JSON file for results')

    args = parser.parse_args()

    # Load results
    try:
        rtl_results = load_results(args.rtl_results)
        model_results = load_results(args.model_results)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        sys.exit(1)

    # Compare
    result = compare_results(rtl_results, model_results, args.threshold)
    result.rtl_file = args.rtl_results
    result.model_file = args.model_results

    # Print results
    print_comparison(result, args.verbose)

    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'rtl_file': result.rtl_file,
                'model_file': result.model_file,
                'metrics': [
                    {
                        'metric_name': m.metric_name,
                        'rtl_value': m.rtl_value,
                        'model_value': m.model_value,
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