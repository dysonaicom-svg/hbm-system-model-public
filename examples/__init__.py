"""
HBM4 Example Scripts

This directory contains example scripts demonstrating various HBM4 features:

Basic Usage:
- basic_controller.py    - Basic controller creation and request submission
- address_decoding.py    - Address decoding with different mapping schemes
- multi_channel.py        - Multi-channel operations and scheduling

Advanced Features:
- qos_scheduling.py       - QoS scheduling with 16-level priority
- refresh_scheduling.py  - Refresh scheduling modes and DRFM
- dfi_interface.py       - DFI 5.0 interface operations
- bandwidth_benchmark.py - Bandwidth measurement and benchmarking
- dram_features.py       - ECC, lane repair, PHY training, MBIST

Running Examples:
    python examples/<script_name>.py

All scripts are self-contained and can be run independently.
"""

# This module exposes example runner functionality
from pathlib import Path

# List of available examples
EXAMPLES = {
    # Basic
    "basic": "basic_controller.py",
    "address": "address_decoding.py",
    "multi_channel": "multi_channel.py",

    # Advanced Features
    "qos": "qos_scheduling.py",
    "qos_priority": "qos_priority.py",
    "refresh": "refresh_scheduling.py",
    "dfi": "dfi_interface.py",
    "dram_features": "dram_features.py",
    "advanced": "advanced_features.py",

    # Performance
    "bandwidth": "bandwidth_benchmark.py",
    "benchmark": "benchmark_example.py",
    "performance": "performance_test.py",
    "simulator": "simulator_example.py",

    # Configuration
    "config": "configuration_example.py",
    "logic_base_die": "hbm4_logic_base_die_example.py",
}


def list_examples():
    """List all available examples"""
    print("Available HBM4 Examples:")
    print("=" * 50)
    for name, filename in EXAMPLES.items():
        print(f"  {name:15s} - {filename}")
    print("=" * 50)


def run_example(name: str):
    """Run a specific example by name"""
    if name not in EXAMPLES:
        print(f"Unknown example: {name}")
        print("Available examples:")
        list_examples()
        return

    filename = EXAMPLES[name]
    import subprocess
    import sys

    script_path = Path(__file__).parent / filename
    result = subprocess.run([sys.executable, str(script_path)])
    return result.returncode


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        run_example(sys.argv[1])
    else:
        list_examples()
        print("\nUsage: python -m examples <example_name>")
        print("Or: python examples/<script>.py")