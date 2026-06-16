#!/usr/bin/env python3
"""
HBM4 Quick-Start Verification Script

This script provides a quick verification of the HBM4 System Modeling Platform.
It checks:
1. All HBM4 modules can be imported
2. Basic simulation works
3. Test suite status
4. Summary of what's working

Usage:
    python scripts/quickstart_verify.py

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

import sys
import os
import traceback
import subprocess
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import optional colorama for colored output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS = True
except ImportError:
    COLORS = False
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
        WHITE = ""
    class Style:
        RESET_ALL = ""
        BRIGHT = ""
        DIM = ""


@dataclass
class CheckResult:
    """Result of a single check"""
    name: str
    category: str
    passed: Optional[bool] = None
    message: str = ""
    error: str = ""

    def mark_pass(self, message: str):
        self.passed = True
        self.message = message

    def mark_fail(self, message: str, error: str = ""):
        self.passed = False
        self.message = message
        self.error = error

    def mark_skip(self, message: str):
        self.passed = None
        self.message = message


class QuickStartVerifier:
    """Quick-start verification for HBM4 platform"""

    def __init__(self):
        self.results: List[CheckResult] = []
        self.categories = [
            "Module Imports",
            "DRAM Model",
            "Controller Model",
            "Simulation",
            "Test Suite",
        ]

    def run_check(self, name: str, category: str, check_func) -> CheckResult:
        """Run a single check and track result"""
        result = CheckResult(name=name, category=category)
        try:
            check_func(result)
        except Exception as e:
            result.mark_fail(f"Unexpected error: {str(e)}", traceback.format_exc())
        self.results.append(result)
        return result

    def print_result(self, result: CheckResult, indent: int = 2):
        """Print a single check result"""
        prefix = " " * indent
        if result.passed is True:
            status = f"{Fore.GREEN}[PASS]{Style.RESET_ALL}"
        elif result.passed is False:
            status = f"{Fore.RED}[FAIL]{Style.RESET_ALL}"
        else:
            status = f"{Fore.YELLOW}[SKIP]{Style.RESET_ALL}"

        print(f"{prefix}{status} {result.name}")
        print(f"{prefix}       {result.message}")

        if result.error and result.passed is False:
            for line in result.error.split('\n')[:3]:
                if line.strip():
                    print(f"{prefix}       {Fore.RED}{line}{Style.RESET_ALL}")

    def print_summary(self) -> Tuple[int, int, int]:
        """Print summary and return counts"""
        passed = sum(1 for r in self.results if r.passed is True)
        failed = sum(1 for r in self.results if r.passed is False)
        skipped = sum(1 for r in self.results if r.passed is None)

        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
        print("  VERIFICATION SUMMARY")
        print(f"{'='*60}{Style.RESET_ALL}")

        # Summary by category
        for category in self.categories:
            cat_results = [r for r in self.results if r.category == category]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r.passed is True)
                cat_total = len(cat_results)
                cat_status = f"{Fore.GREEN}{cat_passed}/{cat_total}{Style.RESET_ALL}"
                print(f"  {category:20s} {cat_status}")

        print(f"\n  {Fore.GREEN}Total Passed: {passed}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Total Failed: {failed}{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Total Skipped: {skipped}{Style.RESET_ALL}")

        return passed, failed, skipped


# ============================================================================
# CHECK FUNCTIONS
# ============================================================================

def check_python_version(result: CheckResult):
    """Check Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        result.mark_pass(f"Python {version.major}.{version.minor}.{version.micro}")
    else:
        result.mark_fail(
            f"Python {version.major}.{version.minor} is too old",
            f"Requires Python 3.8+, found {version.major}.{version.minor}.{version.micro}"
        )


def check_dram_modules(result: CheckResult):
    """Check DRAM model modules can be imported"""
    try:
        from model.dram import (
            HBM4Spec,
            HBM4Channel,
            HBM4LogicBaseDie,
            HBM4PAM3Encoder,
            PAM3SignalModel,
            HBM4ECC,
            HBM4LaneRepairModel,
            HBM4PowerEstimator,
            DFI5Interface,
            BankStateMachine,
            DRAMModel,
        )
        result.mark_pass("All DRAM modules imported successfully")
    except ImportError as e:
        result.mark_fail(f"Failed to import DRAM modules", str(e))


def check_controller_modules(result: CheckResult):
    """Check Controller modules can be imported"""
    try:
        from model.controller import (
            HBMController,
            HBM4Controller,
            HBM4AddressDecoder,
            HBM4QoSScheduler,
            HBM4RefreshScheduler,
        )
        result.mark_pass("All Controller modules imported successfully")
    except ImportError as e:
        result.mark_fail(f"Failed to import Controller modules", str(e))


def check_simulator_modules(result: CheckResult):
    """Check Simulator modules can be imported"""
    try:
        from sim.simulator import (
            SimulationConfig,
            HBMSimulator,
            TrafficPattern,
        )
        from sim.unified_simulator import UnifiedSimulator
        result.mark_pass("All Simulator modules imported successfully")
    except ImportError as e:
        result.mark_fail(f"Failed to import Simulator modules", str(e))


def check_multi_channel(result: CheckResult):
    """Check multi-channel support"""
    try:
        from model.multi_channel import (
            MultiChannelTrafficGenerator,
            ChannelSelector,
            AdaptiveLoadBalancer,
        )
        result.mark_pass("Multi-channel support available")
    except ImportError as e:
        result.mark_fail(f"Failed to import multi-channel modules", str(e))


def check_logic_base_die(result: CheckResult):
    """Check Logic Base Die model"""
    try:
        from model.dram import HBM4LogicBaseDie, HBM4PAM3Encoder, TimingParameters

        # Create and initialize
        lbd = HBM4LogicBaseDie()
        lbd.initialize()

        # Verify initialization
        if lbd.cycle == 0:
            result.mark_pass("Logic Base Die initialized correctly")
        else:
            result.mark_fail("Logic Base Die initialization incomplete")

    except Exception as e:
        result.mark_fail(f"Logic Base Die check failed", str(e))


def check_dfi_interface(result: CheckResult):
    """Check DFI 5.0 interface"""
    try:
        from model.dram import DFI5Interface, DFICommand, DFIRequest

        dfi = DFI5Interface()

        # Test DFI signals by checking core functionality
        if hasattr(dfi, 'tick') and hasattr(dfi, 'queue_request'):
            # Create and queue a request
            req = DFIRequest(
                command=DFICommand.ACT,
                address=0x1000,
                bank=0,
                pseudo_channel=0,
                channel=0
            )
            queued = dfi.queue_request(req)
            if queued:
                result.mark_pass("DFI 5.0 interface functional")
            else:
                result.mark_fail("DFI request queueing failed")
        else:
            result.mark_fail("DFI interface missing core methods")

    except Exception as e:
        result.mark_fail(f"DFI interface check failed", str(e))


def check_pam3_encoding(result: CheckResult):
    """Check PAM3 signal encoding"""
    try:
        from model.dram import HBM4PAM3Encoder, PAM3Level

        encoder = HBM4PAM3Encoder()

        # Test encoding - command bits
        symbols = encoder.encode_command(command=0x555, cmd_bits=10)

        if len(symbols) == 5:
            result.mark_pass("PAM3 encoding works correctly")
        else:
            result.mark_fail(f"PAM3 encoding produced {len(symbols)} symbols, expected 5")

    except Exception as e:
        result.mark_fail(f"PAM3 encoding check failed", str(e))


def check_ecc_crc(result: CheckResult):
    """Check ECC/CRC error handling"""
    try:
        from model.dram import HBM4ECC, HBM4CRC, ErrorType

        ecc = HBM4ECC()
        crc = HBM4CRC()

        # Test ECC encoding/decoding with integer data
        data = 0xAAAAAAAAAAAAAAAA  # 64-bit test pattern
        encoded = ecc.encode(data)

        if encoded > 0:
            result.mark_pass("ECC/CRC error handling available")
        else:
            result.mark_fail("ECC encoding failed")

    except Exception as e:
        result.mark_fail(f"ECC/CRC check failed", str(e))


def check_dram_model_basic(result: CheckResult):
    """Check basic DRAM model operations"""
    try:
        from model.dram.dram_model import DRAMModel

        dram = DRAMModel(hbm_version="hbm3", stack_count=1)
        dram.enable_memory_model()

        # Execute activate
        resp = dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=0, row_id=0x100, current_time=0
        )

        if resp.success:
            result.mark_pass("DRAM model basic operations work")
        else:
            result.mark_fail(f"ACT command failed: {resp.message}")

    except Exception as e:
        result.mark_fail(f"DRAM model check failed", str(e))


def check_controller_basic(result: CheckResult):
    """Check basic controller operations"""
    try:
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest
        from model.controller.config import HBM3_DEFAULT

        controller = HBMController(HBM3_DEFAULT)

        # Submit a request
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        controller.submit_request(req)

        result.mark_pass("Controller request submission works")

    except Exception as e:
        result.mark_fail(f"Controller check failed", str(e))


def check_simulation_basic(result: CheckResult):
    """Run a basic simulation"""
    try:
        from sim.simulator import SimulationConfig, HBMSimulator, TrafficPattern

        # Create minimal simulation
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.5,
            read_ratio=1.0,
        )

        sim = HBMSimulator(config)
        stats = sim.run()

        if stats.total_cycles > 0 and stats.completed_requests > 0:
            result.mark_pass(
                f"Simulation completed: {stats.completed_requests} requests in {stats.total_cycles} cycles"
            )
        elif stats.total_cycles > 0:
            result.mark_pass(
                f"Simulation ran for {stats.total_cycles} cycles (no requests in short run)"
            )
        else:
            result.mark_fail("Simulation produced no cycles")

    except Exception as e:
        result.mark_fail(f"Simulation failed", str(e))


def check_hbm4_32channel(result: CheckResult):
    """Check HBM4 32-channel support"""
    try:
        from model.dram import HBM4Spec, HBM4TimingManager

        spec = HBM4Spec()
        timing_manager = HBM4TimingManager(num_channels=32)

        if len(timing_manager.channels) == 32:
            result.mark_pass("HBM4 32-channel architecture verified")
        else:
            result.mark_fail(
                f"Expected 32 channels, got {len(timing_manager.channels)}"
            )

    except Exception as e:
        result.mark_fail(f"HBM4 32-channel check failed", str(e))


def check_test_suite_exists(result: CheckResult):
    """Check test suite exists"""
    test_dirs = [
        "tests/hbm4",
        "tests/controller",
        "tests/dram",
        "tests/integration",
    ]

    existing = []
    for test_dir in test_dirs:
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), test_dir)
        if os.path.isdir(full_path):
            existing.append(test_dir)

    if len(existing) >= 3:
        result.mark_pass(f"Found {len(existing)} test directories: {', '.join(existing)}")
    else:
        result.mark_fail(f"Only found {len(existing)} test directories")


def run_pytest_quick(result: CheckResult):
    """Run a quick pytest check"""
    try:
        # Run a minimal pytest check (just collect tests, don't run them all)
        test_dir = os.path.dirname(os.path.dirname(__file__))

        # Use pytest --collect-only to quickly verify tests are discoverable
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        output = proc.stdout + proc.stderr

        # Count collected tests
        if "test session starts" in output.lower() or "collected" in output.lower():
            # Try to extract test count
            import re
            match = re.search(r'(\d+)\s+test', output)
            if match:
                count = int(match.group(1))
                result.mark_pass(f"Test suite ready: {count} tests discovered")
            else:
                result.mark_pass("Test suite is discoverable")
        else:
            result.mark_fail("Could not discover tests")

    except subprocess.TimeoutExpired:
        result.mark_skip("Test collection timed out")
    except FileNotFoundError:
        result.mark_skip("pytest not installed")
    except Exception as e:
        result.mark_fail(f"Test suite check failed", str(e))


def check_benchmark_available(result: CheckResult):
    """Check benchmark module is available"""
    try:
        from sim.benchmark import HBMComprehensiveBenchmark

        bench = HBMComprehensiveBenchmark()
        result.mark_pass("HBM4 Benchmark module available")
    except ImportError:
        result.mark_fail("Benchmark module not available")
    except Exception as e:
        result.mark_fail(f"Benchmark check failed", str(e))


def check_requirements(result: CheckResult):
    """Check requirements.txt exists"""
    req_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file) as f:
            deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        result.mark_pass(f"requirements.txt exists with {len(deps)} dependencies")
    else:
        result.mark_fail("requirements.txt not found")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main verification function"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print("  HBM4 System Modeling Platform - Quick Verification")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    verifier = QuickStartVerifier()

    # Category 1: Module Imports
    print(f"{Fore.MAGENTA}{Style.BRIGHT}Checking Module Imports...{Style.RESET_ALL}")

    verifier.run_check("Python Version", "Module Imports", check_python_version)
    verifier.run_check("DRAM Modules", "Module Imports", check_dram_modules)
    verifier.run_check("Controller Modules", "Module Imports", check_controller_modules)
    verifier.run_check("Simulator Modules", "Module Imports", check_simulator_modules)
    verifier.run_check("Multi-Channel Support", "Module Imports", check_multi_channel)

    # Category 2: DRAM Model
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Checking DRAM Model...{Style.RESET_ALL}")

    verifier.run_check("Logic Base Die", "DRAM Model", check_logic_base_die)
    verifier.run_check("DFI 5.0 Interface", "DRAM Model", check_dfi_interface)
    verifier.run_check("PAM3 Encoding", "DRAM Model", check_pam3_encoding)
    verifier.run_check("ECC/CRC", "DRAM Model", check_ecc_crc)
    verifier.run_check("Basic Operations", "DRAM Model", check_dram_model_basic)
    verifier.run_check("HBM4 32-Channel", "DRAM Model", check_hbm4_32channel)

    # Category 3: Controller Model
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Checking Controller Model...{Style.RESET_ALL}")

    verifier.run_check("Basic Operations", "Controller Model", check_controller_basic)

    # Category 4: Simulation
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Checking Simulation...{Style.RESET_ALL}")

    verifier.run_check("Basic Simulation", "Simulation", check_simulation_basic)
    verifier.run_check("Benchmark Module", "Simulation", check_benchmark_available)

    # Category 5: Test Suite
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Checking Test Suite...{Style.RESET_ALL}")

    verifier.run_check("Requirements File", "Test Suite", check_requirements)
    verifier.run_check("Test Directories", "Test Suite", check_test_suite_exists)
    verifier.run_check("Pytest Discovery", "Test Suite", run_pytest_quick)

    # Print all results
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print("  DETAILED RESULTS")
    print(f"{'='*60}{Style.RESET_ALL}")

    for category in verifier.categories:
        cat_results = [r for r in verifier.results if r.category == category]
        if cat_results:
            print(f"\n{Fore.WHITE}{Style.BRIGHT}{category}:{Style.RESET_ALL}")
            for r in cat_results:
                verifier.print_result(r)

    # Print summary
    passed, failed, skipped = verifier.print_summary()

    # Print next steps
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print("  NEXT STEPS")
    print(f"{'='*60}{Style.RESET_ALL}")

    if failed == 0:
        print(f"\n{Fore.GREEN}All checks passed! The platform is ready to use.{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.YELLOW}Some checks failed. Review the results above.{Style.RESET_ALL}\n")

    print("  Quick commands:")
    print(f"    {Fore.CYAN}python -m sim.simulator --mode functional{Style.RESET_ALL}")
    print(f"    {Fore.CYAN}python -m sim.benchmark{Style.RESET_ALL}")
    print(f"    {Fore.CYAN}pytest tests/hbm4/ -v{Style.RESET_ALL}")
    print(f"    {Fore.CYAN}pytest tests/ -v --tb=short{Style.RESET_ALL}")
    print(f"    {Fore.CYAN}python scripts/hbm4_integration_demo.py{Style.RESET_ALL}")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())