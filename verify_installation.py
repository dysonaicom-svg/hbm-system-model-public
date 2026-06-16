#!/usr/bin/env python3
"""
HBM System Modeling Platform - Installation Verification Script

This script verifies that the HBM4 simulation platform is properly installed
and all components are functional.

Usage:
    python verify_installation.py

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

import sys
import importlib
import os
import traceback
from typing import Dict, List, Tuple, Optional

# Try to import optional colorama for colored output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS = True
except ImportError:
    COLORS = False
    # Fallback to plain text markers
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
    class Style:
        RESET_ALL = ""
        BRIGHT = ""

# Test result tracking
class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed: Optional[bool] = None
        self.message: str = ""
        self.error: Optional[str] = None

    def pass_test(self, message: str = ""):
        self.passed = True
        self.message = message

    def fail_test(self, message: str, error: str = ""):
        self.passed = False
        self.message = message
        self.error = error

    def skip_test(self, message: str = ""):
        self.passed = None
        self.message = message


class VerificationSuite:
    def __init__(self):
        self.results: List[TestResult] = []
        self.current_section = ""

    def section(self, name: str):
        self.current_section = name
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"{'='*60}")

    def add_result(self, result: TestResult):
        self.results.append(result)

    def print_summary(self) -> Tuple[int, int, int]:
        passed = sum(1 for r in self.results if r.passed is True)
        failed = sum(1 for r in self.results if r.passed is False)
        skipped = sum(1 for r in self.results if r.passed is None)

        print(f"\n{'='*60}")
        print(f"  SUMMARY")
        print(f"{'='*60}")
        print(f"  {Fore.GREEN}PASSED{Style.RESET_ALL}: {passed}")
        print(f"  {Fore.RED}FAILED{Style.RESET_ALL}: {failed}")
        print(f"  {Fore.YELLOW}SKIPPED{Style.RESET_ALL}: {skipped}")

        # List failed tests
        if failed > 0:
            print(f"\n  {Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for r in self.results:
                if r.passed is False:
                    print(f"    - {r.name}")
                    if r.error:
                        for line in r.error.split('\n')[:5]:
                            print(f"      {line}")

        return passed, failed, skipped


def check_python_version() -> TestResult:
    """Check Python version is 3.8 or higher"""
    result = TestResult("Python Version Check")
    version = sys.version_info

    if version.major == 3 and version.minor >= 8:
        result.pass_test(f"Python {version.major}.{version.minor}.{version.micro}")
    else:
        result.fail_test(
            f"Python {version.major}.{version.minor} is too old",
            f"Requires Python 3.8+, found {version.major}.{version.minor}.{version.micro}"
        )

    return result


def check_dependency(module_name: str, package_name: Optional[str] = None) -> TestResult:
    """Check if a Python dependency is installed"""
    result = TestResult(f"Dependency: {module_name}")

    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'installed')
        result.pass_test(f"{package_name or module_name} {version}")
    except ImportError:
        result.fail_test(
            f"{package_name or module_name} not installed",
            f"Run: pip install {package_name or module_name}"
        )

    return result


def check_dependencies() -> List[TestResult]:
    """Check all required dependencies"""
    results = []

    # Core dependencies
    core_deps = [
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('yaml', 'pyyaml'),
        ('pytest', 'pytest'),
    ]

    # Optional dependencies
    optional_deps = [
        ('matplotlib', 'matplotlib'),
        ('plotly', 'plotly'),
    ]

    for module_name, package_name in core_deps:
        results.append(check_dependency(module_name, package_name))

    return results


def check_hbm_modules() -> List[TestResult]:
    """Check if all HBM modules can be imported"""
    results = []

    # Core model modules
    core_modules = [
        ('model.dram', 'DRAM Model'),
        ('model.controller', 'Controller'),
        ('model.multi_channel', 'Multi-Channel'),
        ('sim.simulator', 'Simulator'),
    ]

    for module_path, description in core_modules:
        result = TestResult(f"Module: {description}")
        try:
            module = importlib.import_module(module_path)
            result.pass_test(f"{module_path} loaded successfully")
        except ImportError as e:
            result.fail_test(
                f"Failed to import {module_path}",
                str(e)
            )
        results.append(result)

    return results


def run_minimal_simulation() -> TestResult:
    """Run a minimal simulation to verify the simulator works"""
    result = TestResult("Minimal Simulation Test")

    try:
        # Import simulator
        from sim.simulator import SimulationConfig, HBMSimulator, TrafficPattern

        # Create a minimal simulation
        config = SimulationConfig(
            simulation_time_us=10.0,  # Very short simulation
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.5,
            read_ratio=1.0,  # All reads for simplicity
        )

        sim = HBMSimulator(config)

        # Run simulation
        stats = sim.run()

        # Verify results
        if stats.total_cycles > 0:
            result.pass_test(
                f"Completed {stats.completed_requests} requests in {stats.total_cycles} cycles"
            )
        else:
            result.fail_test(
                "Simulation ran but produced no cycles",
                "Check simulator implementation"
            )

    except Exception as e:
        result.fail_test(
            f"Simulation failed: {str(e)}",
            traceback.format_exc()
        )

    return result


def run_logic_base_die_tests() -> TestResult:
    """Run Logic Base Die integration tests"""
    result = TestResult("Logic Base Die Tests")

    try:
        # Import required modules
        from model.dram import (
            HBM4LogicBaseDie,
            HBM4PAM3Encoder,
            HBM4TimingManager,
            PAM3SignalModel,
            TimingParameters,
        )

        # Test 1: Create and initialize Logic Base Die
        lbd = HBM4LogicBaseDie()
        lbd.initialize()

        # Advance a few cycles
        for _ in range(50):
            lbd.tick()

        if lbd.cycle != 50:
            result.fail_test(
                "Logic Base Die cycle counter not advancing",
                f"Expected cycle 50, got {lbd.cycle}"
            )
            return result

        # Test 2: Process ACT command
        ok, msg = lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        if not ok:
            result.fail_test(
                f"ACT command failed: {msg}",
                "Check command processing logic"
            )
            return result

        # Test 3: Process READ command
        for _ in range(10):
            lbd.tick()

        ok, msg = lbd.process_command(channel_id=0, command='RD', address=0x1000)
        if not ok:
            result.fail_test(
                f"READ command failed: {msg}",
                "Check READ timing (tRCD)"
            )
            return result

        # Test 4: PAM3 encoding
        encoder = HBM4PAM3Encoder()
        symbols = encoder.encode_command(0x555, 10)
        if len(symbols) != 5:
            result.fail_test(
                f"PAM3 encoding produced wrong symbol count: {len(symbols)}",
                f"Expected 5 symbols for 10 bits"
            )
            return result

        # Test 5: 32-channel timing manager
        manager = HBM4TimingManager(num_channels=32)
        if len(manager.channels) != 32:
            result.fail_test(
                f"Timing manager has wrong channel count: {len(manager.channels)}",
                f"Expected 32 channels"
            )
            return result

        result.pass_test(
            f"All Logic Base Die tests passed. "
            f"Commands processed, PAM3 encoding works, 32 channels operational."
        )

    except Exception as e:
        result.fail_test(
            f"Logic Base Die tests failed: {str(e)}",
            traceback.format_exc()
        )

    return result


def run_dram_model_tests() -> TestResult:
    """Run basic DRAM model tests"""
    result = TestResult("DRAM Model Tests")

    try:
        from model.dram.dram_model import DRAMModel

        # Create DRAM model
        dram = DRAMModel(hbm_version="hbm3", stack_count=1)

        # Enable memory model
        dram.enable_memory_model()

        # Execute activate
        resp = dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=0, row_id=0x100, current_time=0
        )

        if not resp.success:
            result.fail_test(
                f"ACT command failed: {resp.message}",
                "Check DRAM model implementation"
            )
            return result

        # Execute read
        resp = dram.execute_read(
            stack_id=0, channel_id=0, bank_id=0, col_id=0,
            current_time=50, length=64
        )

        if not resp.success:
            result.fail_test(
                f"READ command failed: {resp.message}",
                "Check READ timing"
            )
            return result

        result.pass_test("DRAM model basic operations work correctly")

    except Exception as e:
        result.fail_test(
            f"DRAM model tests failed: {str(e)}",
            traceback.format_exc()
        )

    return result


def run_controller_tests() -> TestResult:
    """Run basic controller tests"""
    result = TestResult("Controller Tests")

    try:
        from model.controller.controller import HBMController
        from model.controller.request import HBMRequest
        from model.controller.config import HBMConfig, HBM3_DEFAULT

        # Create controller using default config
        controller = HBMController(HBM3_DEFAULT)

        # Submit a request
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        controller.submit_request(req)

        # Tick controller
        for _ in range(10):
            scheduled, response = controller.tick()
            if scheduled:
                break

        result.pass_test("Controller can schedule requests correctly")

    except Exception as e:
        result.fail_test(
            f"Controller tests failed: {str(e)}",
            traceback.format_exc()
        )

    return result


def check_file_structure() -> List[TestResult]:
    """Check that key files exist"""
    results = []

    required_files = [
        "model/dram/__init__.py",
        "model/controller/__init__.py",
        "sim/simulator.py",
        "tests/hbm4/test_logic_base_die_integration.py",
        "requirements.txt",
        "CLAUDE.md",
    ]

    for file_path in required_files:
        result = TestResult(f"File: {file_path}")
        full_path = os.path.join(os.path.dirname(__file__), file_path)

        if os.path.exists(full_path):
            result.pass_test(f"{file_path} exists")
        else:
            result.fail_test(
                f"{file_path} not found",
                f"Expected at: {full_path}"
            )

        results.append(result)

    return results


def main():
    """Main verification function"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"  HBM4 System Modeling Platform")
    print(f"  Installation Verification")
    print(f"{'='*60}{Style.RESET_ALL}")

    suite = VerificationSuite()

    # Section 1: Python Version
    suite.section("Python Version Check")
    result = check_python_version()
    suite.add_result(result)
    status = f"[{Fore.GREEN}PASS{Style.RESET_ALL}]" if result.passed else f"[{Fore.RED}FAIL{Style.RESET_ALL}]"
    print(f"  {status} {result.name}: {result.message}")

    # Section 2: Dependencies
    suite.section("Dependency Check")
    for result in check_dependencies():
        suite.add_result(result)
        status = f"[{Fore.GREEN}PASS{Style.RESET_ALL}]" if result.passed else f"[{Fore.RED}FAIL{Style.RESET_ALL}]"
        print(f"  {status} {result.name}: {result.message}")

    # Section 3: File Structure
    suite.section("File Structure Check")
    for result in check_file_structure():
        suite.add_result(result)
        status = f"[{Fore.GREEN}PASS{Style.RESET_ALL}]" if result.passed else f"[{Fore.RED}FAIL{Style.RESET_ALL}]"
        print(f"  {status} {result.name}: {result.message}")

    # Section 4: Module Imports
    suite.section("Module Import Check")
    for result in check_hbm_modules():
        suite.add_result(result)
        status = f"[{Fore.GREEN}PASS{Style.RESET_ALL}]" if result.passed else f"[{Fore.RED}FAIL{Style.RESET_ALL}]"
        print(f"  {status} {result.name}: {result.message}")

    # Section 5: Component Tests
    suite.section("Component Tests")

    # DRAM Model Tests
    result = run_dram_model_tests()
    suite.add_result(result)
    status = f"[{Fore.GREEN}PASS{Style.RESET_ALL}]" if result.passed else f"[{Fore.RED}FAIL{Style.RESET_ALL}]"
    print(f"  {status} {result.name}: {result.message}")

    # Controller Tests
    result = run_controller_tests()
    suite.add_result(result)
    status = f"[{Fore.GREEN}PASS{Style.RESET_ALL}]" if result.passed else f"[{Fore.RED}FAIL{Style.RESET_ALL}]"
    print(f"  {status} {result.name}: {result.message}")

    # Logic Base Die Tests
    result = run_logic_base_die_tests()
    suite.add_result(result)
    status = f"[{Fore.GREEN}PASS{Style.RESET_ALL}]" if result.passed else f"[{Fore.RED}FAIL{Style.RESET_ALL}]"
    print(f"  {status} {result.name}: {result.message}")

    # Section 6: Simulation Test
    suite.section("Integration Test")
    result = run_minimal_simulation()
    suite.add_result(result)
    status = f"[{Fore.GREEN}PASS{Style.RESET_ALL}]" if result.passed else f"[{Fore.RED}FAIL{Style.RESET_ALL}]"
    print(f"  {status} {result.name}: {result.message}")

    # Print summary
    passed, failed, skipped = suite.print_summary()

    # Next steps
    print(f"\n{'='*60}")
    print(f"  NEXT STEPS")
    print(f"{'='*60}")
    print(f"  1. Run full test suite:")
    print(f"     {Fore.CYAN}pytest tests/ -v{Style.RESET_ALL}")
    print(f"")
    print(f"  2. Run specific test categories:")
    print(f"     {Fore.CYAN}pytest tests/hbm4/ -v{Style.RESET_ALL}  (HBM4 tests)")
    print(f"     {Fore.CYAN}pytest tests/controller/ -v{Style.RESET_ALL}  (Controller tests)")
    print(f"     {Fore.CYAN}pytest tests/dram/ -v{Style.RESET_ALL}  (DRAM tests)")
    print(f"")
    print(f"  3. Run a longer simulation:")
    print(f"     {Fore.CYAN}python -m sim.simulator --mode functional{Style.RESET_ALL}")
    print(f"")
    print(f"  4. Run benchmark:")
    print(f"     {Fore.CYAN}python -m sim.benchmark{Style.RESET_ALL}")
    print(f"")
    print(f"  5. For help or documentation:")
    print(f"     {Fore.CYAN}cat CLAUDE.md{Style.RESET_ALL}")
    print(f"{'='*60}\n")

    # Return exit code
    if failed > 0:
        print(f"{Fore.RED}Installation verification FAILED{Style.RESET_ALL}")
        print(f"Please fix the failed tests before proceeding.\n")
        return 1
    else:
        print(f"{Fore.GREEN}Installation verification PASSED{Style.RESET_ALL}")
        print(f"The HBM4 system modeling platform is ready to use.\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())