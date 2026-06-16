#!/usr/bin/env python3
"""
HBM RTL vs Model Comparison Pipeline

This script runs both RTL simulation (via Verilator) and Python model simulation,
compares timing results (latency, throughput), and generates a comprehensive
comparison report.

Usage:
    python scripts/compare_rtl_model.py
    python scripts/compare_rtl_model.py --quick        # Quick test
    python scripts/compare_rtl_model.py --verbose       # Detailed output
    python scripts/compare_rtl_model.py --cycles 1000    # Custom cycles
"""

import os
import sys
import json
import time
import argparse
import subprocess
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
        """Build RTL simulation with Verilator"""
        if verbose:
            print("  Building RTL simulation...")

        # Clean previous build
        if self.obj_dir.exists():
            subprocess.run(['rm', '-rf', str(self.obj_dir)], check=False)

        self.log_dir.mkdir(parents=True, exist_ok=True)
        build_log = self.log_dir / "build.log"

        try:
            # Verilator build command
            cmd = [
                'verilator',
                '--cc',
                '--exe',
                '--build',
                '--sv',
                '--no-timing',
                '-Wno-fatal',
                '--top-module', 'hbm_controller_tb_simple',
                '-f', str(self.rtl_dir / 'filelist.f'),
                str(self.rtl_dir / 'hbm_controller_tb_simple.sv'),
                '--Mdir', str(self.obj_dir),
                '-CFLAGS', '-std=c++17 -O2',
                '-LDFLAGS', '-lpthread',
            ]

            with open(build_log, 'w') as f:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.rtl_dir),  # Run from rtl directory for correct paths
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=300
                )
                f.write(result.stdout)

                if result.returncode != 0:
                    self.summary.error_message = f"Build failed: {result.stderr}\n{result.stdout[-500:]}"
                    return False

            self.summary.build_success = True
            if verbose:
                print(f"    Build log: {build_log}")
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

                if result.returncode == 0:
                    self._parse_output(result.stdout)
                    self.summary.sim_success = True
                else:
                    self.summary.error_message = f"Simulation failed: {result.stderr}"

            self._rtl_execution_time = time.time() - start_time
            return self.summary.sim_success

        except subprocess.TimeoutExpired:
            self.summary.error_message = "Simulation timeout"
            return False
        except Exception as e:
            self.summary.error_message = f"Simulation error: {e}"
            return False

    def _parse_output(self, output: str) -> None:
        """Parse simulation output to extract metrics"""
        lines = output.split('\n')
        
        for line in lines:
            # Extract cycle count
            if 'Total Cycles:' in line or 'total_cycles' in line.lower():
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.isdigit() and int(p) > 100:
                        self.summary.total_cycles = int(p)
                        break
            
            # Extract response counts
            if 'Expected Resp:' in line or 'expected' in line.lower():
                parts = line.split()
                for p in parts:
                    if p.isdigit():
                        self.summary.total_requests = int(p)
                        break
            
            if 'Received Resp:' in line or 'received' in line.lower():
                parts = line.split()
                for p in parts:
                    if p.isdigit():
                        self.summary.completed_requests = int(p)
                        break


class ModelRunner:
    """Wrapper for Python model simulation"""

    def __init__(self):
        self.stats: Optional[SimulationStats] = None
        self.execution_time = 0.0

    def run(self, config: SimulationConfig, verbose: bool = False) -> SimulationStats:
        """Run Python model simulation"""
        if verbose:
            print("  Running Python model simulation...")

        start_time = time.time()
        sim = HBMSimulator(config)
        self.stats = sim.run()
        self.execution_time = time.time() - start_time

        return self.stats

    def get_stats(self) -> Dict[str, float]:
        """Get model statistics as dict"""
        if self.stats is None:
            return {}
        return {
            'total_cycles': float(self.stats.total_cycles),
            'total_requests': float(self.stats.total_requests),
            'completed_requests': float(self.stats.completed_requests),
            'avg_latency': self.stats.avg_latency,
            'row_hit_rate': self.stats.row_hit_rate,
            'throughput_gbps': self.stats.throughput_gbps,
        }


def compare_metrics(rtl_val: float, model_val: float, metric_name: str) -> ComparisonResult:
    """Compare a single metric between RTL and model"""
    if model_val == 0:
        diff_pct = 0.0 if rtl_val == 0 else 100.0
    else:
        diff_pct = abs(rtl_val - model_val) / model_val * 100.0

    # Determine status based on difference
    if diff_pct < 5:
        status = 'PASS'
    elif diff_pct < 15:
        status = 'MARGINAL'
    else:
        status = 'FAIL'

    return ComparisonResult(
        metric=metric_name,
        rtl_value=rtl_val,
        model_value=model_val,
        difference=rtl_val - model_val,
        percent_diff=diff_pct,
        status=status
    )


def run_comparison(
    sim_time_us: float = 10.0,
    traffic_pattern: TrafficPattern = TrafficPattern.RANDOM,
    request_rate: float = 0.5,
    verbose: bool = False,
    rtl_only: bool = False,
    model_only: bool = False,
) -> ComparisonReport:
    """Run full comparison between RTL and model"""
    
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    # Initialize runners
    rtl_runner = RTLSRunner()
    model_runner = ModelRunner()
    
    # Check Verilator availability
    rtl_available, rtl_version = rtl_runner.check_toolchain()
    
    # Run model
    model_config = SimulationConfig(
        simulation_time_us=sim_time_us,
        traffic_pattern=traffic_pattern,
        request_rate=request_rate,
        seed=42,
    )
    model_stats = model_runner.run(model_config, verbose)
    model_stats_dict = model_runner.get_stats()
    
    # Run RTL if available and requested
    rtl_summary = RTLSummary()
    if rtl_available and not model_only:
        if verbose:
            print(f"  Verilator: {rtl_version}")
        
        # Build and run RTL
        if rtl_runner.build(verbose=verbose):
            rtl_runner.run(sim_time=f"{sim_time_us}us", verbose=verbose)
        
        rtl_summary = rtl_runner.summary
    
    # Compare metrics
    results = []
    if not model_only and rtl_summary.sim_success:
        results.append(compare_metrics(
            rtl_summary.total_cycles,
            model_stats.total_cycles,
            'total_cycles'
        ))
        results.append(compare_metrics(
            rtl_summary.completed_requests,
            model_stats.completed_requests,
            'completed_requests'
        ))
    
    # Determine overall status
    if not rtl_available:
        overall_status = 'MODEL_ONLY'
    elif rtl_summary.sim_success:
        statuses = [r.status for r in results]
        if all(s == 'PASS' for s in statuses):
            overall_status = 'PASS'
        elif any(s == 'FAIL' for s in statuses):
            overall_status = 'FAIL'
        else:
            overall_status = 'MARGINAL'
    else:
        overall_status = 'BUILD_FAILED'
    
    return ComparisonReport(
        timestamp=timestamp,
        comparison_type='quick' if sim_time_us < 50 else 'full',
        rtl_summary=rtl_summary,
        model_stats=model_stats_dict,
        comparison_results=results,
        overall_status=overall_status,
        execution_time_s=time.time() - start_time,
        rtl_execution_time_s=rtl_runner.rtl_execution_time,
        model_execution_time_s=model_runner.execution_time,
    )


def print_report(report: ComparisonReport, verbose: bool = False) -> None:
    """Print comparison report"""
    print("\n" + "=" * 60)
    print("HBM RTL vs Model Comparison Report")
    print("=" * 60)
    print(f"Timestamp: {report.timestamp}")
    print(f"Comparison Type: {report.comparison_type}")
    print(f"Overall Status: {report.overall_status}")
    print()
    
    if report.rtl_summary.sim_success:
        print("RTL Simulation:")
        print(f"  Total Cycles: {report.rtl_summary.total_cycles}")
        print(f"  Completed Requests: {report.rtl_summary.completed_requests}")
        print(f"  Build Success: {report.rtl_summary.build_success}")
    else:
        print("RTL Simulation: Not available")
        if report.rtl_summary.error_message:
            print(f"  Error: {report.rtl_summary.error_message[:100]}...")
    
    print()
    print("Python Model:")
    print(f"  Total Cycles: {report.model_stats.get('total_cycles', 0):.0f}")
    print(f"  Completed Requests: {report.model_stats.get('completed_requests', 0):.0f}")
    print(f"  Avg Latency: {report.model_stats.get('avg_latency', 0):.2f} cycles")
    print(f"  Row Hit Rate: {report.model_stats.get('row_hit_rate', 0):.2%}")
    print(f"  Throughput: {report.model_stats.get('throughput_gbps', 0):.2f} GB/s")
    
    if report.comparison_results:
        print()
        print("Comparison Results:")
        print("-" * 60)
        for r in report.comparison_results:
            print(f"  {r.metric:20s}: RTL={r.rtl_value:8.2f}, Model={r.model_value:8.2f}, "
                  f"Diff={r.percent_diff:6.2f}% [{r.status}]")
    
    print()
    print(f"Execution Time: {report.execution_time_s:.2f}s "
          f"(RTL: {report.rtl_execution_time_s:.2f}s, "
          f"Model: {report.model_execution_time_s:.2f}s)")
    print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='HBM RTL vs Model Comparison')
    parser.add_argument('--quick', action='store_true', help='Quick test mode')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--cycles', type=int, default=0, help='Custom cycle count')
    parser.add_argument('--rtl-only', action='store_true', help='RTL only')
    parser.add_argument('--model-only', action='store_true', help='Model only')
    parser.add_argument('--output', type=str, default='', help='Output JSON file')
    parser.add_argument('--pattern', type=str, default='random',
                        choices=['random', 'sequential', 'stride', 'hotspot'],
                        help='Traffic pattern (default: random)')
    args = parser.parse_args()

    # Convert pattern string to TrafficPattern
    pattern_map = {
        'random': TrafficPattern.RANDOM,
        'sequential': TrafficPattern.SEQUENTIAL,
        'stride': TrafficPattern.STRIDE,
        'hotspot': TrafficPattern.HOT_SPOT,
    }
    traffic_pattern = pattern_map.get(args.pattern.lower(), TrafficPattern.RANDOM)

    # Run comparison
    sim_time = 5.0 if args.quick else 10.0
    report = run_comparison(
        sim_time_us=sim_time,
        traffic_pattern=traffic_pattern,
        request_rate=0.5,
        verbose=args.verbose,
        rtl_only=args.rtl_only,
        model_only=args.model_only,
    )
    
    # Print report
    print_report(report, args.verbose)
    
    # Save to JSON if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\nReport saved to: {output_path}")
    
    return 0 if report.overall_status in ('PASS', 'MODEL_ONLY') else 1


if __name__ == '__main__':
    sys.exit(main())
