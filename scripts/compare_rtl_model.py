#!/usr/bin/env python3
"""
HBM RTL vs Model Comparison Pipeline

This script runs both RTL simulation (via Verilator) and Python model simulation,
compares timing results (latency, throughput), and generates a comprehensive
comparison report.

Usage:
    python scripts/compare_rtl_model.py
    python scripts/compare_rtl_model.py --quick        # Quick test
    python scripts/compare_rtl_model.py --verbose     # Detailed output
    python scripts/compare_rtl_model.py --cycles 1000 # Custom cycles
    python scripts/compare_rtl_model.py --rtl-only    # RTL only
    python scripts/compare_rtl_model.py --model-only  # Model only
    python scripts/compare_rtl_model.py --rtl-results <json> --model-results <json>
"""

import os
import sys
import json
import time
import argparse
import subprocess
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern
from model.controller.config import HBMConfig, HBM3_DEFAULT


@dataclass
class ComparisonResult:
    """Comparison result for a single metric"""
    metric: str
    rtl_value: float
    model_value: float
    difference: float
    percent_diff: float
    status: str  # 'PASS', 'MARGINAL', 'FAIL'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric': self.metric,
            'rtl_value': self.rtl_value,
            'model_value': self.model_value,
            'difference': self.difference,
            'percent_diff': self.percent_diff,
            'status': self.status,
        }


@dataclass
class RTLSummary:
    """RTL simulation summary parsed from logs"""
    total_cycles: int = 0
    total_requests: int = 0
    completed_requests: int = 0
    avg_latency_cycles: float = 0.0
    row_hit_rate: float = 0.0
    throughput_gbps: float = 0.0
    raw_output: str = ""
    build_success: bool = False
    sim_success: bool = False
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_cycles': self.total_cycles,
            'total_requests': self.total_requests,
            'completed_requests': self.completed_requests,
            'avg_latency_cycles': self.avg_latency_cycles,
            'row_hit_rate': self.row_hit_rate,
            'throughput_gbps': self.throughput_gbps,
            'build_success': self.build_success,
            'sim_success': self.sim_success,
            'error_message': self.error_message,
        }


@dataclass
class ComparisonReport:
    """Full comparison report"""
    timestamp: str
    comparison_type: str  # 'full', 'quick'
    rtl_summary: RTLSummary
    model_stats: Dict[str, float]
    comparison_results: List[ComparisonResult]
    overall_status: str
    execution_time_s: float
    rtl_execution_time_s: float
    model_execution_time_s: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'comparison_type': self.comparison_type,
            'rtl_summary': self.rtl_summary.to_dict(),
            'model_stats': self.model_stats,
            'comparison_results': [r.to_dict() for r in self.comparison_results],
            'overall_status': self.overall_status,
            'execution_time_s': self.execution_time_s,
            'rtl_execution_time_s': self.rtl_execution_time_s,
            'model_execution_time_s': self.model_execution_time_s,
        }


class RTLSRunner:
    """Wrapper for RTL simulation using Verilator"""

    def __init__(self, rtl_dir: Optional[Path] = None):
        self.rtl_dir = rtl_dir or (_project_root / "rtl")
        self.obj_dir = self.rtl_dir / "obj_dir"
        self.log_dir = self.rtl_dir / "logs"
        self.summary = RTLSummary()
        self._rtl_execution_time = 0.0

    @property
    def rtl_execution_time(self) -> float:
        return self._rtl_execution_time

    def check_toolchain(self) -> Tuple[bool, str]:
        """Check if Verilator is available"""
        try:
            result = subprocess.run(
                ['verilator', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Verilator not found"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "Verilator not found"

    def build(self, sim_time: str = "10us", verbose: bool = False) -> bool:
        """Build RTL simulation using Makefile"""
        if verbose:
            print("  Building RTL simulation...")

        # Clean previous build
        if self.obj_dir.exists():
            subprocess.run(['rm', '-rf', str(self.obj_dir)], check=False)

        self.log_dir.mkdir(parents=True, exist_ok=True)
        build_log = self.log_dir / "build.log"

        try:
            # Use the existing Makefile
            result = subprocess.run(
                ['make', 'sim', f'SIM_TIME={sim_time}'],
                cwd=str(self.rtl_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=300
            )

            with open(build_log, 'w') as f:
                f.write(result.stdout)

            # Check for build errors
            if result.returncode != 0:
                self.summary.error_message = f"Build failed (exit code {result.returncode})"
                if verbose:
                    print(f"    Build failed, log: {build_log}")
                return False

            # Check if binary was created
            binary = self.obj_dir / "Vhbm_controller_tb"
            if not binary.exists():
                # Try to find it in the output
                if 'Build Complete' in result.stdout or 'Binary:' in result.stdout:
                    self.summary.error_message = "Build reported success but binary not found - check GCC version (C++20 required)"
                else:
                    self.summary.error_message = "Binary not created - RTL build may have failed"
                if verbose:
                    print(f"    {self.summary.error_message}")
                return False

            self.summary.build_success = True
            if verbose:
                print(f"    Build successful: {binary}")
            return True

        except subprocess.TimeoutExpired:
            self.summary.error_message = "Build timeout"
            return False
        except Exception as e:
            self.summary.error_message = f"Build error: {e}"
            return False

    def run(self, sim_time: str = "10us", verbose: bool = False) -> bool:
        """Run RTL simulation"""
        if verbose:
            print("  Running RTL simulation...")

        sim_log = self.log_dir / "sim.log"
        binary = self.obj_dir / "Vhbm_controller_tb"

        if not binary.exists():
            self.summary.error_message = "RTL binary not found"
            return False

        try:
            start_time = time.time()

            with open(sim_log, 'w') as f:
                result = subprocess.run(
                    [str(binary), f'+TIME={sim_time}'],
                    cwd=str(self.obj_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=60
                )
                f.write(result.stdout)
                self.summary.raw_output = result.stdout

            self._rtl_execution_time = time.time() - start_time

            # Parse output for summary
            self._parse_output(result.stdout)

            self.summary.sim_success = result.returncode == 0
            if not self.summary.sim_success:
                self.summary.error_message = f"Simulation failed with code {result.returncode}"

            if verbose:
                print(f"    Simulation log: {sim_log}")

            return self.summary.sim_success

        except subprocess.TimeoutExpired:
            self.summary.error_message = "Simulation timeout"
            return False
        except Exception as e:
            self.summary.error_message = f"Simulation error: {e}"
            return False

    def _parse_output(self, output: str):
        """Parse RTL simulation output to extract metrics"""
        lines = output.split('\n')

        for line in lines:
            # Look for cycle count
            if 'completed at cycle' in line.lower():
                try:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if 'cycle' in p.lower():
                            self.summary.total_cycles = int(parts[i-1])
                            break
                except (ValueError, IndexError):
                    pass

            # Look for request/completion stats
            if 'Statistics:' in line or 'statistics' in line.lower():
                try:
                    if 'req=' in line:
                        req_part = line.split('req=')[1].split(',')[0]
                        self.summary.total_requests = int(req_part)
                    if 'comp=' in line:
                        comp_part = line.split('comp=')[1].split(',')[0]
                        self.summary.completed_requests = int(comp_part)
                except (ValueError, IndexError):
                    pass

            # Look for response count
            if 'Received Resp:' in line:
                try:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if 'Resp:' in p:
                            self.summary.completed_requests = int(parts[i+1])
                            break
                except (ValueError, IndexError):
                    pass

            # Look for total tests
            if 'Total Tests:' in line:
                try:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if 'Tests:' in p:
                            self.summary.total_requests = int(parts[i+1])
                            break
                except (ValueError, IndexError):
                    pass

            # Look for hit rate
            if 'hit_rate=' in line:
                try:
                    hit_part = line.split('hit_rate=')[1].split(',')[0].split('%')[0]
                    self.summary.row_hit_rate = float(hit_part) / 100.0
                except (ValueError, IndexError):
                    pass

        # Estimate latency based on cycles and requests
        if self.summary.completed_requests > 0 and self.summary.total_cycles > 0:
            self.summary.avg_latency_cycles = self.summary.total_cycles / self.summary.completed_requests

            # Estimate throughput (HBM3 @ 1.28 GHz, 128 bytes per request)
            bytes_per_req = 128
            tCK_ns = 0.78125
            total_ns = self.summary.total_cycles * tCK_ns
            bytes_transferred = self.summary.completed_requests * bytes_per_req
            self.summary.throughput_gbps = bytes_transferred / (total_ns * 1e-9) / 1e9


class ModelRunner:
    """Wrapper for Python model simulation"""

    def __init__(self):
        self.stats: Optional[SimulationStats] = None
        self.execution_time: float = 0.0

    def run(
        self,
        simulation_time_us: float = 10.0,
        traffic_pattern: TrafficPattern = TrafficPattern.RANDOM,
        request_rate: float = 0.3,
        read_ratio: float = 0.7,
        seed: Optional[int] = None,
        verbose: bool = False
    ) -> SimulationStats:
        """Run Python model simulation"""
        if verbose:
            print("  Running Python model simulation...")

        config = SimulationConfig(
            simulation_time_us=simulation_time_us,
            traffic_pattern=traffic_pattern,
            request_rate=request_rate,
            read_ratio=read_ratio,
            seed=seed,
            hbm_config=HBM3_DEFAULT,
        )

        start_time = time.time()
        sim = HBMSimulator(config)
        self.stats = sim.run()
        self.execution_time = time.time() - start_time

        if verbose:
            print(f"    Completed {self.stats.completed_requests} requests in "
                  f"{self.stats.total_cycles} cycles")

        return self.stats

    def get_stats_dict(self) -> Dict[str, float]:
        """Get stats as dictionary"""
        if self.stats is None:
            return {}

        return {
            'total_cycles': float(self.stats.total_cycles),
            'total_requests': float(self.stats.total_requests),
            'completed_requests': float(self.stats.completed_requests),
            'avg_latency_cycles': self.stats.avg_latency,
            'max_latency_cycles': float(self.stats.max_latency_cycles),
            'min_latency_cycles': float(self.stats.min_latency_cycles),
            'row_hit_rate': self.stats.row_hit_rate,
            'throughput_gbps': self.stats.throughput_gbps,
            'efficiency': self.stats.efficiency,
            'bandwidth_efficiency': self.stats.bandwidth_efficiency,
            'dram_activations': float(self.stats.total_dram_activations),
            'requests_per_second': self.stats.completed_requests / max(self.execution_time, 0.001),
        }


class ComparisonPipeline:
    """Main comparison pipeline"""

    # Tolerance thresholds for comparison
    LATENCY_TOLERANCE_PCT = 25.0  # 25% tolerance for latency
    THROUGHPUT_TOLERANCE_PCT = 30.0  # 30% tolerance for throughput
    HIT_RATE_TOLERANCE_PCT = 35.0  # 35% tolerance for hit rate
    CYCLE_TOLERANCE_PCT = 20.0  # 20% tolerance for cycle count

    def __init__(self, rtl_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        self.rtl_dir = rtl_dir or (_project_root / "rtl")
        self.output_dir = output_dir or (_project_root / "scripts")
        self.rtl_runner = RTLSRunner(self.rtl_dir)
        self.model_runner = ModelRunner()
        self.report: Optional[ComparisonReport] = None

    def _calculate_comparison(
        self,
        metric: str,
        rtl_value: float,
        model_value: float,
        tolerance_pct: float = 20.0
    ) -> ComparisonResult:
        """Calculate comparison for a single metric"""
        if model_value == 0:
            if rtl_value == 0:
                difference = 0.0
                percent_diff = 0.0
            else:
                difference = rtl_value
                percent_diff = 100.0
        else:
            difference = rtl_value - model_value
            percent_diff = abs(difference / model_value * 100.0)

        # Determine status
        if tolerance_pct == 0:
            # No comparison possible
            status = 'N/A'
        elif percent_diff <= tolerance_pct:
            status = 'PASS'
        elif percent_diff <= tolerance_pct * 1.5:
            status = 'MARGINAL'
        else:
            status = 'FAIL'

        return ComparisonResult(
            metric=metric,
            rtl_value=rtl_value,
            model_value=model_value,
            difference=difference,
            percent_diff=percent_diff,
            status=status
        )

    def compare(
        self,
        quick: bool = False,
        verbose: bool = False,
        rtl_only: bool = False,
        model_only: bool = False
    ) -> ComparisonReport:
        """Run full comparison"""
        print("\n" + "=" * 70)
        print("HBM RTL vs Model Comparison Pipeline")
        print("=" * 70)

        start_time = time.time()
        rtl_time = 0.0
        model_time = 0.0

        # Configuration
        sim_time_rtl = "10us" if quick else "50us"
        sim_time_model = 10.0 if quick else 50.0

        # Run RTL simulation
        if not model_only:
            print("\n[Phase 1] RTL Simulation")
            print("-" * 40)

            # Check toolchain
            available, version = self.rtl_runner.check_toolchain()
            if not available:
                print(f"  Warning: {version}")
                print("  Skipping RTL simulation")
            else:
                print(f"  Verilator: {version}")

                # Build
                if not self.rtl_runner.build(sim_time_rtl, verbose):
                    print(f"  Error: RTL build failed")
                    print(f"  {self.rtl_runner.summary.error_message}")

                # Run
                else:
                    rtl_start = time.time()
                    self.rtl_runner.run(sim_time_rtl, verbose)
                    rtl_time = self.rtl_runner.rtl_execution_time

        # Run Python model
        if not rtl_only:
            print("\n[Phase 2] Python Model Simulation")
            print("-" * 40)

            model_start = time.time()
            self.model_runner.run(
                simulation_time_us=sim_time_model,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.3,
                seed=42,
                verbose=verbose
            )
            model_time = time.time() - model_start

        # Extract metrics
        rtl_summary = self.rtl_runner.summary
        model_stats = self.model_runner.get_stats_dict()

        # Calculate comparisons
        comparison_results = []

        if not model_only:
            # Compare total cycles
            if rtl_summary.total_cycles > 0 and model_stats.get('total_cycles', 0) > 0:
                comparison_results.append(
                    self._calculate_comparison(
                        'total_cycles',
                        float(rtl_summary.total_cycles),
                        model_stats['total_cycles'],
                        self.CYCLE_TOLERANCE_PCT
                    )
                )

            # Compare completed requests
            if rtl_summary.completed_requests > 0 and model_stats.get('completed_requests', 0) > 0:
                comparison_results.append(
                    self._calculate_comparison(
                        'completed_requests',
                        float(rtl_summary.completed_requests),
                        model_stats['completed_requests'],
                        0  # No direct comparison, just report both
                    )
                )

        if not rtl_only and model_stats:
            # Compare avg latency
            if 'avg_latency_cycles' in model_stats and model_stats['avg_latency_cycles'] > 0:
                # RTL provides avg latency estimate
                comparison_results.append(
                    self._calculate_comparison(
                        'avg_latency_cycles',
                        rtl_summary.avg_latency_cycles,
                        model_stats['avg_latency_cycles'],
                        self.LATENCY_TOLERANCE_PCT
                    )
                )

            # Compare row hit rate
            if 'row_hit_rate' in model_stats:
                comparison_results.append(
                    self._calculate_comparison(
                        'row_hit_rate',
                        rtl_summary.row_hit_rate,
                        model_stats['row_hit_rate'],
                        self.HIT_RATE_TOLERANCE_PCT
                    )
                )

            # Compare throughput
            if 'throughput_gbps' in model_stats:
                comparison_results.append(
                    self._calculate_comparison(
                        'throughput_gbps',
                        rtl_summary.throughput_gbps,
                        model_stats['throughput_gbps'],
                        self.THROUGHPUT_TOLERANCE_PCT
                    )
                )

            # Compare efficiency
            if 'efficiency' in model_stats:
                comparison_results.append(
                    self._calculate_comparison(
                        'efficiency',
                        0.0,  # RTL doesn't provide efficiency
                        model_stats['efficiency'],
                        0  # No comparison possible
                    )
                )

        # Determine overall status
        if rtl_only:
            overall_status = 'RTL_ONLY' if rtl_summary.sim_success else 'RTL_FAILED'
        elif model_only:
            overall_status = 'MODEL_ONLY'
        elif not rtl_summary.build_success:
            # RTL build failed - fall back to model only
            overall_status = 'MODEL_ONLY'
            if model_stats:
                print("  Note: RTL build failed, model-only comparison will be shown")
        elif not rtl_summary.sim_success:
            overall_status = 'RTL_FAILED'
        elif not model_stats:
            overall_status = 'RTL_ONLY'
        else:
            # Both succeeded - compare results
            statuses = [r.status for r in comparison_results if r.status not in ('PASS', 'N/A')]
            if not statuses:
                overall_status = 'PASS'
            elif statuses.count('MARGINAL') == len(statuses):
                overall_status = 'MARGINAL'
            else:
                overall_status = 'FAIL'

        total_time = time.time() - start_time

        # Create report
        self.report = ComparisonReport(
            timestamp=datetime.now().isoformat(),
            comparison_type='quick' if quick else 'full',
            rtl_summary=rtl_summary,
            model_stats=model_stats,
            comparison_results=comparison_results,
            overall_status=overall_status,
            execution_time_s=total_time,
            rtl_execution_time_s=rtl_time,
            model_execution_time_s=model_time,
        )

        return self.report

    def print_report(self):
        """Print comparison report"""
        if self.report is None:
            print("No report available")
            return

        print("\n" + "=" * 70)
        print("COMPARISON REPORT")
        print("=" * 70)

        print(f"\nTimestamp: {self.report.timestamp}")
        print(f"Comparison Type: {self.report.comparison_type}")
        print(f"Overall Status: {self.report.overall_status}")
        print(f"\nExecution Times:")
        print(f"  Total: {self.report.execution_time_s:.2f}s")
        print(f"  RTL:   {self.report.rtl_execution_time_s:.2f}s")
        print(f"  Model: {self.report.model_execution_time_s:.2f}s")

        # RTL Summary
        print(f"\n--- RTL Simulation Summary ---")
        rtl = self.report.rtl_summary
        print(f"  Build Success: {'Yes' if rtl.build_success else 'No'}")
        print(f"  Sim Success:   {'Yes' if rtl.sim_success else 'No'}")
        if rtl.error_message:
            print(f"  Error: {rtl.error_message}")
        else:
            print(f"  Total Cycles:  {rtl.total_cycles:,}")
            print(f"  Total Requests: {rtl.total_requests}")
            print(f"  Completed:     {rtl.completed_requests}")
            print(f"  Avg Latency:   {rtl.avg_latency_cycles:.1f} cycles")
            print(f"  Row Hit Rate:  {rtl.row_hit_rate:.2%}")
            print(f"  Throughput:    {rtl.throughput_gbps:.3f} GB/s")

        # Model Stats
        print(f"\n--- Python Model Statistics ---")
        model = self.report.model_stats
        if model:
            print(f"  Total Cycles:    {int(model.get('total_cycles', 0)):,}")
            print(f"  Total Requests:  {int(model.get('total_requests', 0)):,}")
            print(f"  Completed:      {int(model.get('completed_requests', 0)):,}")
            print(f"  Avg Latency:     {model.get('avg_latency_cycles', 0):.1f} cycles")
            print(f"  Max Latency:     {int(model.get('max_latency_cycles', 0)):,} cycles")
            print(f"  Row Hit Rate:    {model.get('row_hit_rate', 0):.2%}")
            print(f"  Throughput:      {model.get('throughput_gbps', 0):.3f} GB/s")
            print(f"  Efficiency:      {model.get('efficiency', 0):.2%}")
            print(f"  DRAM Activations: {int(model.get('dram_activations', 0)):,}")
            print(f"  Requests/sec:    {model.get('requests_per_second', 0):.0f}")
        else:
            print("  (No data)")

        # Comparison Results
        if self.report.comparison_results:
            print(f"\n--- Metric Comparisons ---")
            print(f"  {'Metric':<25} {'RTL':>12} {'Model':>12} {'Diff':>10} {'%Diff':>10} {'Status':>10}")
            print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*10} {'-'*10} {'-'*10}")

            for result in self.report.comparison_results:
                if result.status != 'N/A' or result.model_value != 0 or result.rtl_value != 0:
                    if result.rtl_value:
                        rtl_str = f"{result.rtl_value:.3f}"
                    else:
                        rtl_str = "N/A"
                    if result.model_value:
                        model_str = f"{result.model_value:.3f}"
                    else:
                        model_str = "N/A"
                    if result.difference:
                        diff_str = f"{result.difference:+.3f}"
                    else:
                        diff_str = "N/A"
                    if result.percent_diff:
                        pct_str = f"{result.percent_diff:.1f}%"
                    else:
                        pct_str = "N/A"

                    # Status color
                    if result.status == 'PASS':
                        status_str = "\033[92mPASS\033[0m"
                    elif result.status == 'MARGINAL':
                        status_str = "\033[93mMARGINAL\033[0m"
                    elif result.status == 'FAIL':
                        status_str = "\033[91mFAIL\033[0m"
                    else:
                        status_str = result.status

                    print(f"  {result.metric:<25} {rtl_str:>12} {model_str:>12} {diff_str:>10} {pct_str:>10} {status_str}")

        print("\n" + "=" * 70)
        print(f"Overall: {self.report.overall_status}")
        print("=" * 70)

    def save_report(self, filename: str = "comparison_report.json"):
        """Save report to JSON file"""
        if self.report is None:
            return None

        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.report.to_dict(), f, indent=2)

        print(f"\nReport saved to: {output_path}")
        return output_path

    def save_markdown(self, filename: str = "comparison_report.md"):
        """Save report as Markdown"""
        if self.report is None:
            return None

        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write("# HBM RTL vs Model Comparison Report\n\n")
            f.write(f"**Generated:** {self.report.timestamp}\n\n")
            f.write(f"**Comparison Type:** {self.report.comparison_type}\n\n")
            f.write(f"**Overall Status:** {self.report.overall_status}\n\n")

            # Execution times
            f.write("## Execution Times\n\n")
            f.write(f"- Total: {self.report.execution_time_s:.2f}s\n")
            f.write(f"- RTL: {self.report.rtl_execution_time_s:.2f}s\n")
            f.write(f"- Model: {self.report.model_execution_time_s:.2f}s\n\n")

            # RTL Summary
            f.write("## RTL Simulation Summary\n\n")
            rtl = self.report.rtl_summary
            f.write(f"| Metric | Value |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Build Success | {'Yes' if rtl.build_success else 'No'} |\n")
            f.write(f"| Sim Success | {'Yes' if rtl.sim_success else 'No'} |\n")
            if rtl.error_message:
                f.write(f"| Error | {rtl.error_message} |\n")
            else:
                f.write(f"| Total Cycles | {rtl.total_cycles:,} |\n")
                f.write(f"| Completed | {rtl.completed_requests:,} |\n")
                f.write(f"| Avg Latency | {rtl.avg_latency_cycles:.1f} cycles |\n")
                f.write(f"| Row Hit Rate | {rtl.row_hit_rate:.2%} |\n")
                f.write(f"| Throughput | {rtl.throughput_gbps:.3f} GB/s |\n")

            # Model Stats
            f.write("\n## Python Model Statistics\n\n")
            model = self.report.model_stats
            if model:
                f.write(f"| Metric | Value |\n")
                f.write(f"|--------|-------|\n")
                f.write(f"| Total Cycles | {int(model.get('total_cycles', 0)):,} |\n")
                f.write(f"| Completed | {int(model.get('completed_requests', 0)):,} |\n")
                f.write(f"| Avg Latency | {model.get('avg_latency_cycles', 0):.1f} cycles |\n")
                f.write(f"| Max Latency | {int(model.get('max_latency_cycles', 0)):,} cycles |\n")
                f.write(f"| Row Hit Rate | {model.get('row_hit_rate', 0):.2%} |\n")
                f.write(f"| Throughput | {model.get('throughput_gbps', 0):.3f} GB/s |\n")
                f.write(f"| Efficiency | {model.get('efficiency', 0):.2%} |\n")

            # Comparison Results
            if self.report.comparison_results:
                f.write("\n## Metric Comparisons\n\n")
                f.write(f"| Metric | RTL | Model | Diff | %Diff | Status |\n")
                f.write(f"|--------|-----|-------|------|--------|--------|\n")

                for result in self.report.comparison_results:
                    rtl_str = f"{result.rtl_value:.3f}" if result.rtl_value else "N/A"
                    model_str = f"{result.model_value:.3f}" if result.model_value else "N/A"
                    diff_str = f"{result.difference:+.3f}" if result.difference else "N/A"
                    pct_str = f"{result.percent_diff:.1f}%" if result.percent_diff else "N/A"
                    f.write(f"| {result.metric} | {rtl_str} | {model_str} | "
                            f"{diff_str} | {pct_str} | {result.status} |\n")

            f.write("\n## Notes\n\n")
            if self.report.overall_status == 'PASS':
                f.write("All comparisons passed within tolerance.\n")
            elif self.report.overall_status == 'MARGINAL':
                f.write("Some comparisons are marginal. Review the results.\n")
            elif self.report.overall_status == 'RTL_ONLY':
                f.write("RTL simulation completed successfully. Model comparison skipped.\n")
            elif self.report.overall_status == 'RTL_FAILED':
                f.write("RTL simulation failed. Check the error message.\n")
            else:
                f.write("Review individual metric comparisons for details.\n")

        print(f"Markdown report saved to: {output_path}")
        return output_path


def load_json_results(path: str) -> Dict:
    """Load pre-existing JSON results file"""
    with open(path, 'r') as f:
        return json.load(f)


def compare_from_files(
    rtl_path: str,
    model_path: str,
    latency_threshold: float = 10.0,
    throughput_threshold: float = 15.0,
    hit_rate_threshold: float = 5.0
) -> int:
    """Compare results from pre-existing JSON files"""
    print(f"\nLoading RTL results from: {rtl_path}")
    rtl_data = load_json_results(rtl_path)

    print(f"Loading model results from: {model_path}")
    model_data = load_json_results(model_path)

    results = []

    # Compare latency metrics
    print("\n--- Latency Comparison ---")
    for key in ['avg_latency', 'max_latency', 'min_latency']:
        rtl_val = rtl_data.get(key, 0)
        model_val = model_data.get(key, 0)

        if rtl_val > 0 and model_val > 0:
            error_pct = abs(rtl_val - model_val) / rtl_val * 100
            status = "PASS" if error_pct <= latency_threshold else "FAIL"
            results.append((key, rtl_val, model_val, error_pct, status))
            print(f"  {key}: RTL={rtl_val:.2f}, Model={model_val:.2f}, Error={error_pct:.2f}% [{status}]")

    # Compare throughput metrics
    print("\n--- Throughput Comparison ---")
    for key in ['throughput_gbps', 'requests_per_second']:
        rtl_val = rtl_data.get(key, 0)
        model_val = model_data.get(key, 0)

        if rtl_val > 0 and model_val > 0:
            error_pct = abs(rtl_val - model_val) / rtl_val * 100
            status = "PASS" if error_pct <= throughput_threshold else "FAIL"
            results.append((key, rtl_val, model_val, error_pct, status))
            print(f"  {key}: RTL={rtl_val:.2f}, Model={model_val:.2f}, Error={error_pct:.2f}% [{status}]")

    # Compare row buffer metrics
    print("\n--- Row Buffer Comparison ---")
    for key in ['row_hit_rate', 'row_miss_rate']:
        rtl_val = rtl_data.get(key, 0)
        model_val = model_data.get(key, 0)

        if rtl_val > 0 and model_val > 0:
            error_pct = abs(rtl_val - model_val) / rtl_val * 100
            status = "PASS" if error_pct <= hit_rate_threshold else "FAIL"
            results.append((key, rtl_val, model_val, error_pct, status))
            print(f"  {key}: RTL={rtl_val:.2%}, Model={model_val:.2%}, Error={error_pct:.2f}% [{status}]")

    # Summary
    passed = sum(1 for r in results if r[4] == "PASS")
    failed = len(results) - passed

    print(f"\n--- Summary ---")
    print(f"Total: {len(results)}, Passed: {passed}, Failed: {failed}")

    return 0 if failed == 0 else 1


def create_parser() -> argparse.ArgumentParser:
    """Create command line parser"""
    parser = argparse.ArgumentParser(
        description='HBM RTL vs Model Comparison Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    # Full comparison with both RTL and model
    python scripts/compare_rtl_model.py

    # Quick comparison
    python scripts/compare_rtl_model.py --quick

    # Compare pre-existing JSON files
    python scripts/compare_rtl_model.py --rtl-results rtl.json --model-results model.json

    # RTL only (no model)
    python scripts/compare_rtl_model.py --rtl-only

    # Model only (no RTL)
    python scripts/compare_rtl_model.py --model-only

    # Verbose output
    python scripts/compare_rtl_model.py --verbose
'''
    )

    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Quick comparison mode (shorter simulation)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--cycles', '-n',
        type=int,
        default=0,
        help='Custom number of cycles for model simulation'
    )

    parser.add_argument(
        '--rtl-only',
        action='store_true',
        help='Run RTL simulation only'
    )

    parser.add_argument(
        '--model-only',
        action='store_true',
        help='Run model simulation only'
    )

    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='scripts',
        help='Output directory for reports'
    )

    # Pre-existing file comparison
    parser.add_argument(
        '--rtl-results',
        type=str,
        help='RTL simulation results JSON file'
    )

    parser.add_argument(
        '--model-results',
        type=str,
        help='Python model results JSON file'
    )

    parser.add_argument(
        '--latency-threshold',
        type=float,
        default=10.0,
        help='Latency comparison threshold %%'
    )

    parser.add_argument(
        '--throughput-threshold',
        type=float,
        default=15.0,
        help='Throughput comparison threshold %%'
    )

    parser.add_argument(
        '--save-json',
        action='store_true',
        default=True,
        help='Save report as JSON (default: True)'
    )

    parser.add_argument(
        '--save-markdown',
        action='store_true',
        default=True,
        help='Save report as Markdown (default: True)'
    )

    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # If pre-existing files provided, use simple comparison mode
    if args.rtl_results and args.model_results:
        return compare_from_files(
            args.rtl_results,
            args.model_results,
            args.latency_threshold,
            args.throughput_threshold
        )

    # Create output directory
    output_dir = _project_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create pipeline and run
    pipeline = ComparisonPipeline(output_dir=output_dir)

    try:
        report = pipeline.compare(
            quick=args.quick,
            verbose=args.verbose,
            rtl_only=args.rtl_only,
            model_only=args.model_only
        )

        # Print report
        pipeline.print_report()

        # Save reports
        if args.save_json:
            pipeline.save_report()
        if args.save_markdown:
            pipeline.save_markdown()

        # Return exit code based on status
        if report.overall_status in ('PASS', 'RTL_ONLY', 'MODEL_ONLY'):
            return 0
        elif report.overall_status == 'MARGINAL':
            return 1
        else:
            return 2

    except KeyboardInterrupt:
        print("\nComparison interrupted by user")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())