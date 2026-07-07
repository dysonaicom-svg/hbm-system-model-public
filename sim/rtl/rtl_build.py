#!/usr/bin/env python3
"""RTL Build Automation Script

Automates Verilator compilation and RTL simulation.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_RTL_DIR = Path(__file__).parent.parent.parent / "rtl"
DEFAULT_SOURCES = [
    "hbm_controller_tb.sv",
    "hbm_controller.sv",
    "hbm_types.svh",
    "hbm_pkg.sv",
]


def build_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HBM4 RTL Build Automation")
    parser.add_argument("--rtl-dir", type=Path, default=DEFAULT_RTL_DIR,
                       help="RTL source directory")
    parser.add_argument("--build-dir", type=Path, default=None,
                       help="Build output directory")
    parser.add_argument("--sources", nargs="+", default=DEFAULT_SOURCES,
                       help="Source files to compile")
    parser.add_argument("--top-module", default="hbm_controller_tb",
                       help="Top-level module")
    parser.add_argument("--trace", action="store_true",
                       help="Enable waveform tracing")
    parser.add_argument("--threads", type=int, default=4,
                       help="Number of compilation threads")
    parser.add_argument("--verilator-opts", default="",
                       help="Additional Verilator options")
    return parser


def run_verilator(args) -> int:
    """Run Verilator compilation"""
    rtl_dir = args.rtl_dir
    build_dir = args.build_dir or (rtl_dir / "build")
    build_dir.mkdir(exist_ok=True)

    # Build command
    cmd = [
        "verilator",
        "--cc",
        f"--top-module {args.top_module}",
        f"-CFLAGS \"-DVM_TRACE_FMT_VCD{' -DTRACE_ENABLED' if args.trace else ''}\"",
        f"-Mdir {build_dir}",
        f"-j {args.threads}",
    ]

    # Add source files
    for src in args.sources:
        src_path = rtl_dir / src
        if src_path.exists():
            cmd.append(str(src_path))
        else:
            print(f"Warning: Source file not found: {src_path}", file=sys.stderr)

    # Add extra options
    if args.verilator_opts:
        cmd.extend(args.verilator_opts.split())

    print(f"Running: {' '.join(str(c) for c in cmd)}")

    result = subprocess.run(cmd, cwd=rtl_dir)
    return result.returncode


def main():
    parser = build_args()
    args = parser.parse_args()

    print(f"HBM4 RTL Build Automation")
    print(f"  RTL Dir: {args.rtl_dir}")
    print(f"  Top Module: {args.top_module}")
    print(f"  Trace: {args.trace}")

    return run_verilator(args)


if __name__ == "__main__":
    sys.exit(main())
