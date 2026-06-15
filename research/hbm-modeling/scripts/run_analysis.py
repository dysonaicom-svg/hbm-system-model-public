#!/usr/bin/env python3
"""
HBM Analysis Pipeline
Complete pipeline: generate trace -> run Ramulator2 -> parse results -> compare

This script orchestrates:
1. Generate synthetic memory traces
2. Run Ramulator2 simulations
3. Parse simulation results
4. Compare with model predictions
5. Generate comparison report
"""

import os
import sys
import json
import argparse
import subprocess
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sim.trace.parser import TraceParser, TraceConfig, TraceFormat, TraceStats

# Add scripts directory to path for parse_ramulator_log import
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from parse_ramulator_log import (
    RamulatorLogParser,
    RamulatorLogResult,
    save_results as save_ramulator_results,
)


@dataclass
class ComparisonResult:
    """Comparison between model prediction and simulation results"""
    trace_name: str = ""

    # Model predictions
    model_row_hit_rate: float = 0.0
    model_avg_latency: float = 0.0
    model_row_hits: int = 0
    model_row_misses: int = 0
    model_row_conflicts: int = 0

    # Simulation results
    sim_row_hit_rate: float = 0.0
    sim_avg_latency: float = 0.0
    sim_row_hits: int = 0
    sim_row_misses: int = 0
    sim_row_conflicts: int = 0

    # Differences
    hit_rate_error: float = 0.0  # percentage points
    latency_error_pct: float = 0.0  # percentage
    row_hit_error_pct: float = 0.0
    row_miss_error_pct: float = 0.0
    row_conflict_error_pct: float = 0.0

    def compute_errors(self) -> None:
        """Compute error metrics"""
        self.hit_rate_error = abs(self.model_row_hit_rate - self.sim_row_hit_rate) * 100
        if self.sim_avg_latency > 0:
            self.latency_error_pct = abs(self.model_avg_latency - self.sim_avg_latency) / self.sim_avg_latency * 100
        if self.sim_row_hits > 0:
            self.row_hit_error_pct = abs(self.model_row_hits - self.sim_row_hits) / self.sim_row_hits * 100
        if self.sim_row_misses > 0:
            self.row_miss_error_pct = abs(self.model_row_misses - self.sim_row_misses) / self.sim_row_misses * 100
        if self.sim_row_conflicts > 0:
            self.row_conflict_error_pct = abs(self.model_row_conflicts - self.sim_row_conflicts) / self.sim_row_conflicts * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "trace_name": self.trace_name,
            "model": {
                "row_hit_rate": self.model_row_hit_rate,
                "avg_latency": self.model_avg_latency,
                "row_hits": self.model_row_hits,
                "row_misses": self.model_row_misses,
                "row_conflicts": self.model_row_conflicts,
            },
            "simulation": {
                "row_hit_rate": self.sim_row_hit_rate,
                "avg_latency": self.sim_avg_latency,
                "row_hits": self.sim_row_hits,
                "row_misses": self.sim_row_misses,
                "row_conflicts": self.sim_row_conflicts,
            },
            "errors": {
                "hit_rate_error_pp": self.hit_rate_error,
                "latency_error_pct": self.latency_error_pct,
                "row_hit_error_pct": self.row_hit_error_pct,
                "row_miss_error_pct": self.row_miss_error_pct,
                "row_conflict_error_pct": self.row_conflict_error_pct,
            }
        }

    def summary(self) -> str:
        """Generate summary text"""
        return (
            f"{self.trace_name}: "
            f"hit_rate_error={self.hit_rate_error:.2f}pp, "
            f"latency_error={self.latency_error_pct:.1f}%, "
            f"row_hits_error={self.row_hit_error_pct:.1f}%"
        )


class HBMAnalysisPipeline:
    """Complete analysis pipeline for HBM modeling"""

    def __init__(self, root_dir: str = None):
        if root_dir is None:
            # Get the project root from this file's location
            # scripts/run_analysis.py -> hbm-modeling -> research -> HBM
            current_file = Path(__file__).resolve()
            root_dir = current_file.parent.parent.parent.parent

        root_dir = str(root_dir)
        self.root_dir = root_dir
        self.ramulator_bin = os.path.join(root_dir, "research", "ramulator2", "build", "ramulator2")
        self.trace_dir = os.path.join(root_dir, "research", "hbm-modeling", "traces")
        self.results_dir = os.path.join(root_dir, "research", "hbm-modeling", "results")
        self.configs_dir = os.path.join(root_dir, "research", "hbm-modeling", "configs")
        self.gen_trace_script = os.path.join(root_dir, "research", "hbm-modeling", "scripts", "gen_trace.py")

        # Ensure directories exist
        os.makedirs(self.trace_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

    def generate_trace(
        self,
        name: str,
        pattern: str,
        count: int = 100000,
        write_ratio: float = 0.0,
    ) -> str:
        """Generate a synthetic memory trace"""
        trace_file = os.path.join(self.trace_dir, f"{name}.trace")

        cmd = [
            sys.executable,
            self.gen_trace_script,
            "--out", trace_file,
            "--pattern", pattern,
            "--count", str(count),
            "--write-ratio", str(write_ratio),
        ]

        print(f"Generating trace: {name} ({pattern}, {count} requests)...")
        # Use cwd to ensure correct working directory
        subprocess.run(cmd, check=True, capture_output=True, cwd=self.root_dir)

        return trace_file

    def run_ramulator(
        self,
        trace_file: str,
        config_name: str,
    ) -> str:
        """Run Ramulator2 simulation"""
        log_file = os.path.join(self.results_dir, f"{config_name}.log")
        config_file = os.path.join(self.configs_dir, f"{config_name}.yaml")

        if not os.path.exists(self.ramulator_bin):
            raise FileNotFoundError(f"Ramulator2 binary not found: {self.ramulator_bin}")
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")

        print(f"Running Ramulator2: {config_name}...")
        cmd = [self.ramulator_bin, "-f", config_file]

        with open(log_file, "w") as f:
            subprocess.run(cmd, check=True, stdout=f, stderr=subprocess.STDOUT)

        return log_file

    def parse_trace_model(self, trace_file: str) -> Tuple[TraceStats, TraceParser]:
        """Parse trace and compute model predictions"""
        config = TraceConfig(
            trace_file=trace_file,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        parser.parse_file()
        stats = parser.analyze()
        return stats, parser

    def parse_ramulator_log(self, log_file: str) -> RamulatorLogResult:
        """Parse Ramulator2 log file"""
        parser = RamulatorLogParser(log_file)
        return parser.parse()

    def compare_results(
        self,
        trace_name: str,
        model_stats: TraceStats,
        sim_result: RamulatorLogResult,
    ) -> ComparisonResult:
        """Compare model predictions with simulation results"""
        comparison = ComparisonResult(trace_name=trace_name)

        # Model predictions
        comparison.model_row_hit_rate = model_stats.estimated_row_hit_rate
        comparison.model_avg_latency = model_stats.estimated_avg_latency
        comparison.model_row_hits = model_stats.same_row_accesses
        comparison.model_row_misses = model_stats.stride_count + model_stats.sequential_count - model_stats.same_row_accesses
        comparison.model_row_conflicts = model_stats.same_bank_conflicts

        # Simulation results (from first channel)
        ch_stats = sim_result.get_per_channel_stats(0)
        if ch_stats:
            comparison.sim_row_hit_rate = ch_stats.row_hit_rate
            comparison.sim_avg_latency = ch_stats.avg_read_latency
            comparison.sim_row_hits = ch_stats.row_hits
            comparison.sim_row_misses = ch_stats.row_misses
            comparison.sim_row_conflicts = ch_stats.row_conflicts
        else:
            # Fallback to aggregated stats
            comparison.sim_row_hit_rate = sim_result.aggregated_hit_rate
            comparison.sim_avg_latency = sim_result.total_avg_latency
            comparison.sim_row_hits = sim_result.total_row_hits
            comparison.sim_row_misses = sim_result.total_row_misses
            comparison.sim_row_conflicts = sim_result.total_row_conflicts

        # Compute errors
        comparison.compute_errors()

        return comparison

    def run_full_analysis(
        self,
        patterns: List[str] = None,
        count: int = 100000,
        run_sim: bool = True,
    ) -> Dict[str, ComparisonResult]:
        """Run complete analysis pipeline"""
        if patterns is None:
            patterns = ["seq", "stride", "random"]

        results = {}
        comparisons = []

        for pattern in patterns:
            trace_name = f"{pattern}_rd"
            print(f"\n{'='*60}")
            print(f"Analysis: {trace_name}")
            print('='*60)

            # Generate trace
            trace_file = self.generate_trace(trace_name, pattern, count)

            # Parse with model
            model_stats, parser = self.parse_trace_model(trace_file)
            print("\nModel predictions:")
            print(f"  Row hit rate: {model_stats.estimated_row_hit_rate*100:.2f}%")
            print(f"  Avg latency:  {model_stats.estimated_avg_latency:.1f} cycles")

            # Run simulation
            if run_sim:
                config_name = f"hbm3_{pattern}"
                log_file = self.run_ramulator(trace_file, config_name)

                # Parse simulation results
                sim_result = self.parse_ramulator_log(log_file)
                print("\nSimulation results:")
                print(f"  Row hit rate: {sim_result.aggregated_hit_rate*100:.2f}%")
                print(f"  Avg latency: {sim_result.total_avg_latency:.2f} cycles")

                # Compare
                comparison = self.compare_results(trace_name, model_stats, sim_result)
                comparison.compute_errors()
                comparisons.append(comparison)

                print("\nComparison:")
                print(f"  Hit rate error: {comparison.hit_rate_error:.2f} pp")
                print(f"  Latency error:  {comparison.latency_error_pct:.1f}%")

                results[trace_name] = comparison

        return results

    def generate_report(
        self,
        results: Dict[str, ComparisonResult],
        output_file: str = None,
    ) -> str:
        """Generate comparison report"""
        if output_file is None:
            output_file = os.path.join(self.results_dir, "comparison_report.json")

        # Save JSON report
        report_data = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "comparisons": {name: comp.to_dict() for name, comp in results.items()},
        }

        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        # Generate text report
        text_lines = [
            "=" * 70,
            "HBM Model vs Ramulator2 Comparison Report",
            "=" * 70,
            "",
            f"Generated: {report_data['generated_at']}",
            "",
            "[Summary Table]",
            "-" * 70,
            f"{'Trace':<20} {'Hit Rate Error':<15} {'Latency Error':<15} {'Row Hits Err':<15}",
            "-" * 70,
        ]

        for name, comp in results.items():
            text_lines.append(
                f"{name:<20} {comp.hit_rate_error:>10.2f} pp     "
                f"{comp.latency_error_pct:>10.1f} %       "
                f"{comp.row_hit_error_pct:>10.1f} %"
            )

        text_lines.extend([
            "-" * 70,
            "",
            "[Detailed Results]",
            "",
        ])

        for name, comp in results.items():
            text_lines.extend([
                f"\n{name}:",
                f"  Model:    hit_rate={comp.model_row_hit_rate*100:.2f}%, "
                f"latency={comp.model_avg_latency:.1f} cycles",
                f"  Sim:      hit_rate={comp.sim_row_hit_rate*100:.2f}%, "
                f"latency={comp.sim_avg_latency:.2f} cycles",
                f"  Error:    hit_rate={comp.hit_rate_error:.2f} pp, "
                f"latency={comp.latency_error_pct:.1f}%",
            ])

        text_lines.extend([
            "",
            "=" * 70,
        ])

        text_report = os.path.join(self.results_dir, "comparison_report.txt")
        with open(text_report, 'w') as f:
            f.write("\n".join(text_lines))

        print(f"\nReport saved to:")
        print(f"  JSON: {output_file}")
        print(f"  Text: {text_report}")

        return output_file


def main():
    parser = argparse.ArgumentParser(description="HBM Analysis Pipeline")
    parser.add_argument(
        "--patterns",
        nargs="+",
        default=["seq", "stride", "random"],
        choices=["seq", "stride", "random"],
        help="Trace patterns to analyze",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100000,
        help="Number of requests per trace",
    )
    parser.add_argument(
        "--skip-sim",
        action="store_true",
        help="Skip Ramulator2 simulation (model only)",
    )
    parser.add_argument(
        "--output",
        help="Output report file path",
    )
    parser.add_argument(
        "--root",
        help="Project root directory",
    )

    args = parser.parse_args()

    # Run pipeline
    pipeline = HBMAnalysisPipeline(root_dir=args.root)
    results = pipeline.run_full_analysis(
        patterns=args.patterns,
        count=args.count,
        run_sim=not args.skip_sim,
    )

    # Generate report
    if results:
        pipeline.generate_report(results, output_file=args.output)

    # Print summary
    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)
    for name, comp in results.items():
        print(f"  {comp.summary()}")


if __name__ == "__main__":
    main()