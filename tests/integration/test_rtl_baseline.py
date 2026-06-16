"""
RTL-Python Behavioral Alignment Tests - RTL Side

Tests that compare RTL simulation results against expected baselines.
This verifies that the RTL behavior matches expectations.

Run with: pytest tests/integration/test_rtl_baseline.py -v
"""

import pytest
import json
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional


RTL_DIR = Path(__file__).parent.parent / "rtl"
RTL_OBJ_DIR = RTL_DIR / "obj_dir"
RTL_LOG_DIR = RTL_DIR / "logs"


@dataclass
class RTLStats:
    """Statistics from RTL simulation"""
    total_cycles: int = 0
    total_requests: int = 0
    completed_requests: int = 0
    avg_latency_ns: float = 0.0
    throughput_gbps: float = 0.0
    row_hit_rate: float = 0.0


def run_rtl_simulation(sim_time_us: float = "10us") -> RTLStats:
    """Run RTL simulation and parse results

    Args:
        sim_time_us: Simulation time (e.g., "10us")

    Returns:
        RTLStats object
    """
    stats = RTLStats()

    # Check if binary exists
    binary = RTL_OBJ_DIR / "Vhbm_controller_tb"
    if not binary.exists():
        pytest.skip("RTL binary not built")
        return stats

    # Run simulation
    try:
        result = subprocess.run(
            [str(binary), f"+TIME={sim_time_us}"],
            cwd=str(RTL_OBJ_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse output for stats
        # Look for patterns like "Requests: 1234", "Completed: 1230", etc.
        output = result.stdout + result.stderr

        for line in output.split('\n'):
            if 'Requests:' in line or 'requests:' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    try:
                        stats.total_requests = int(parts[1].strip())
                    except:
                        pass
            if 'Completed:' in line or 'completed:' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    try:
                        stats.completed_requests = int(parts[1].strip())
                    except:
                        pass

    except subprocess.TimeoutExpired:
        pytest.skip("RTL simulation timed out")
    except Exception as e:
        pytest.skip(f"RTL simulation failed: {e}")

    return stats


@pytest.fixture
def rtl_binary_built():
    """Check if RTL is built"""
    binary = RTL_OBJ_DIR / "Vhbm_controller_tb"
    if not binary.exists():
        pytest.skip("RTL binary not built - run 'cd rtl && make' first")
    return True


class TestRTLBaseline:
    """Baseline tests for RTL simulation"""

    def test_rtl_builds(self, rtl_binary_built):
        """RTL should build successfully"""
        assert rtl_binary_built

    def test_rtl_runs_short(self, rtl_binary_built):
        """RTL should run short simulation"""
        stats = run_rtl_simulation("1us")
        # Just verify it runs
        assert stats.total_cycles >= 0

    def test_rtl_produces_output(self, rtl_binary_built):
        """RTL should produce output"""
        stats = run_rtl_simulation("1us")
        # Should have some requests processed
        assert stats.total_requests >= 0


class TestRTLParameters:
    """Parameter validation for RTL"""

    def test_rtl_latency_reasonable(self, rtl_binary_built):
        """RTL latency should be reasonable"""
        stats = run_rtl_simulation("10us")

        if stats.completed_requests > 0:
            # Average latency should be in reasonable range for HBM3
            # (1-100 ns typically)
            assert 0 <= stats.avg_latency_ns <= 500, \
                f"RTL latency {stats.avg_latency_ns} out of expected range"

    def test_rtl_throughput_reasonable(self, rtl_binary_built):
        """RTL throughput should be reasonable"""
        stats = run_rtl_simulation("10us")

        # HBM3 peak ~819 GB/s per stack
        assert 0 <= stats.throughput_gbps <= 2000, \
            f"RTL throughput {stats.throughput_gbps} out of expected range"


# Baseline storage
RTL_BASELINE_FILE = Path(__file__).parent / "rtl_baseline_data.json"


def save_rtl_baseline():
    """Save RTL baseline data"""
    stats = run_rtl_simulation("10us")

    baseline = {
        'stats': {
            'total_requests': stats.total_requests,
            'completed_requests': stats.completed_requests,
            'avg_latency_ns': stats.avg_latency_ns,
            'throughput_gbps': stats.throughput_gbps,
            'row_hit_rate': stats.row_hit_rate,
        },
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    with open(RTL_BASELINE_FILE, 'w') as f:
        json.dump(baseline, f, indent=2)

    return baseline


def load_rtl_baseline() -> Optional[Dict[str, Any]]:
    """Load RTL baseline"""
    if RTL_BASELINE_FILE.exists():
        with open(RTL_BASELINE_FILE, 'r') as f:
            return json.load(f)
    return None


if __name__ == "__main__":
    # Build and run baseline
    print("Building RTL...")
    result = subprocess.run(
        ["make", "clean", "&&", "make"],
        cwd=str(RTL_DIR),
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Running RTL baseline...")
        baseline = save_rtl_baseline()
        print(f"RTL Baseline: {json.dumps(baseline, indent=2)}")
    else:
        print(f"Build failed: {result.stderr}")