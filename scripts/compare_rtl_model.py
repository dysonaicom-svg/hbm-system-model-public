#!/usr/bin/env python3
"""
HBM RTL vs Python Model Comparison Script

Compares latency and throughput between:
1. RTL simulation (Verilator)
2. Python model simulation

Usage:
    python3 scripts/compare_rtl_model.py --rtl-results rtl_latency.json --model-results model_latency.json
"""

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ComparisonResult:
    """Comparison between RTL and model results"""
    metric: str
    rtl_value: float
    model_value: float
    error_pct: float
    pass_threshold: float = 10.0  # 10% default threshold


def load_json(path: str) -> Dict:
    """Load JSON results file"""
    with open(path, 'r') as f:
        return json.load(f)


def compare_latency(rtl_data: Dict, model_data: Dict, threshold: float = 10.0) -> List[ComparisonResult]:
    """Compare latency results"""
    results = []

    for key in ['avg_latency', 'max_latency', 'min_latency']:
        rtl_val = rtl_data.get(key, 0)
        model_val = model_data.get(key, 0)

        if rtl_val > 0 and model_val > 0:
            error_pct = abs(rtl_val - model_val) / rtl_val * 100
            results.append(ComparisonResult(
                metric=key,
                rtl_value=rtl_val,
                model_value=model_val,
                error_pct=error_pct,
                pass_threshold=threshold
            ))

    return results


def compare_throughput(rtl_data: Dict, model_data: Dict, threshold: float = 15.0) -> List[ComparisonResult]:
    """Compare throughput results"""
    results = []

    for key in ['throughput_gbps', 'requests_per_second']:
        rtl_val = rtl_data.get(key, 0)
        model_val = model_data.get(key, 0)

        if rtl_val > 0 and model_val > 0:
            error_pct = abs(rtl_val - model_val) / rtl_val * 100
            results.append(ComparisonResult(
                metric=key,
                rtl_value=rtl_val,
                model_value=model_val,
                error_pct=error_pct,
                pass_threshold=threshold
            ))

    return results


def compare_row_buffer(rtl_data: Dict, model_data: Dict, threshold: float = 5.0) -> List[ComparisonResult]:
    """Compare row buffer hit rate"""
    results = []

    for key in ['row_hit_rate', 'row_miss_rate', 'row_conflict_rate']:
        rtl_val = rtl_data.get(key, 0)
        model_val = model_data.get(key, 0)

        if rtl_val > 0 and model_val > 0:
            error_pct = abs(rtl_val - model_val) / rtl_val * 100
            results.append(ComparisonResult(
                metric=key,
                rtl_value=rtl_val,
                model_value=model_val,
                error_pct=error_pct,
                pass_threshold=threshold
            ))

    return results


def print_comparison(results: List[ComparisonResult], title: str):
    """Print comparison results table"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    print(f"{'Metric':<20} {'RTL':>12} {'Model':>12} {'Error %':>10} {'Status':>10}")
    print(f"{'-'*70}")

    passed = 0
    failed = 0

    for r in results:
        status = "PASS" if r.error_pct <= r.pass_threshold else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1

        print(f"{r.metric:<20} {r.rtl_value:>12.4f} {r.model_value:>12.4f} "
              f"{r.error_pct:>9.2f}% {status:>10}")

    print(f"{'-'*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description='Compare RTL vs Python model results')
    parser.add_argument('--rtl-results', required=True, help='RTL simulation results JSON')
    parser.add_argument('--model-results', required=True, help='Python model results JSON')
    parser.add_argument('--threshold', type=float, default=10.0, help='Error threshold %%')
    parser.add_argument('--output', help='Output comparison JSON file')
    args = parser.parse_args()

    # Load data
    print(f"Loading RTL results from: {args.rtl_results}")
    rtl_data = load_json(args.rtl_results)

    print(f"Loading model results from: {args.model_results}")
    model_data = load_json(args.model_results)

    # Compare metrics
    latency_results = compare_latency(rtl_data, model_data, args.threshold)
    throughput_results = compare_throughput(rtl_data, model_data, args.threshold)
    row_buffer_results = compare_row_buffer(rtl_data, model_data, args.threshold)

    # Print results
    print_comparison(latency_results, "Latency Comparison")
    print_comparison(throughput_results, "Throughput Comparison")
    print_comparison(row_buffer_results, "Row Buffer Comparison")

    # Summary
    all_results = latency_results + throughput_results + row_buffer_results
    total_passed = sum(1 for r in all_results if r.error_pct <= r.pass_threshold)
    total_failed = len(all_results) - total_passed

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"Total metrics: {len(all_results)}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Pass rate: {total_passed*100/len(all_results):.1f}%")

    if total_failed == 0:
        print("\n✓ ALL TESTS PASSED - RTL and Model match within threshold")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Check results above")
        return 1


if __name__ == '__main__':
    sys.exit(main())