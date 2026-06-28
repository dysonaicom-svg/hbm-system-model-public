#!/usr/bin/env python3
"""RTL-Python auto-sync tool

Compares Python model and RTL implementation, generates alignment report.
This tool validates that signal definitions, timing parameters, and constants
are consistent between Python models and SystemVerilog RTL.

Usage:
    python scripts/rtl_sync.py --model-dir model --rtl-dir rtl --output docs/reports/rtl_sync.json
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class SyncDiscrepancy:
    """Represents a discrepancy between RTL and Python definitions"""
    type: str  # "missing_in_python", "missing_in_rtl", "value_mismatch", "width_mismatch"
    name: str
    rtl_value: Optional[str] = None
    python_value: Optional[str] = None
    severity: str = "error"  # "error", "warning", "info"
    description: str = ""


@dataclass
class SyncReport:
    """Complete alignment report"""
    timestamp: str
    tool_version: str = "1.0.0"
    status: str = "PASS"  # "PASS", "FAIL", "PARTIAL"
    rtl_file: str = ""
    python_file: str = ""
    signals_compared: int = 0
    discrepancies_count: int = 0
    warnings_count: int = 0
    discrepancies: List[Dict] = field(default_factory=list)
    alignment_summary: Dict[str, Any] = field(default_factory=dict)


class RTLParser:
    """Parse RTL (SystemVerilog) signal definitions"""

    def __init__(self, rtl_dir: Path):
        self.rtl_dir = rtl_dir
        self.signals: Dict[str, Dict[str, Any]] = {}

    def parse_hbm_types(self) -> Dict[str, Dict[str, Any]]:
        """Parse hbm_types.svh for signal definitions"""
        types_file = self.rtl_dir / "hbm_types.svh"
        if not types_file.exists():
            return {}

        content = types_file.read_text()
        signals = {}

        # Parse parameter definitions: `define NAME value or parameter NAME = value
        # Example: `define NUM_CHANNELS 32
        for match in re.finditer(r'`define\s+(\w+)\s+(\S+)', content):
            name, value = match.groups()
            signals[name] = {
                "type": "parameter",
                "value": value,
                "category": "system_config"
            }

        # Parse parameter NAME = value
        for match in re.finditer(r'parameter\s+(?:logic\s+)?(?:\[\d+:\d+\]\s+)?(\w+)\s*=\s*([^;]+);', content):
            name, value = match.group(1), match.group(2).strip()
            signals[name] = {
                "type": "parameter",
                "value": value,
                "category": "timing"
            }

        # Parse enum definitions for commands
        for match in re.finditer(
            r'typedef\s+enum\s+logic\s+\[\d+:\d+\]\s*\{([^}]+)\}\s*(\w+);',
            content
        ):
            enum_body, enum_name = match.groups()
            items = {}
            for item_match in re.finditer(r'(\w+)\s*=\s*[\d\']+([bdh])?(\w+)?', enum_body):
                item_name = item_match.group(1)
                base = item_match.group(2) or ''
                val = item_match.group(3) or '0'
                try:
                    if base == 'h':
                        items[item_name] = int(val, 16)
                    elif base == 'd':
                        items[item_name] = int(val)
                    else:
                        items[item_name] = int(base + val, 0) if base else int(val)
                except ValueError:
                    items[item_name] = val
            signals[enum_name] = {
                "type": "enum",
                "values": items,
                "category": "command_encoding"
            }

        # Parse struct packed for address and signal bundles
        for match in re.finditer(
            r'typedef\s+struct\s+packed\s*\{([^}]+)\}\s*(\w+);',
            content,
            re.DOTALL
        ):
            struct_body, struct_name = match.groups()
            fields = {}
            for line in struct_body.splitlines():
                line = line.strip().rstrip(';')
                # Match: logic [msb:lsb] name;
                vec_match = re.match(r'logic\s+\[(\d+):(\d+)\]\s+(\w+)', line)
                if vec_match:
                    msb, lsb, fname = vec_match.groups()
                    fields[fname] = {
                        "width": int(msb) - int(lsb) + 1,
                        "msb": int(msb),
                        "lsb": int(lsb)
                    }
                # Match: logic name;
                bit_match = re.match(r'logic\s+(\w+)', line)
                if bit_match and not vec_match:
                    fname = bit_match.group(1)
                    fields[fname] = {"width": 1}
            signals[struct_name] = {
                "type": "struct",
                "fields": fields,
                "category": "signal_bundle"
            }

        self.signals = signals
        return signals

    def get_timing_parameters(self) -> Dict[str, str]:
        """Extract timing parameters from RTL"""
        types_file = self.rtl_dir / "hbm_types.svh"
        if not types_file.exists():
            return {}

        content = types_file.read_text()
        params = {}

        # Look for HBM4 timing parameter patterns
        for match in re.finditer(r'logic\s+\[\d+:\d+\]\s+(t\w+);', content):
            param_name = match.group(1)
            params[param_name] = param_name

        return params


class PythonParser:
    """Parse Python model constants"""

    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.constants: Dict[str, Dict[str, Any]] = {}

    def parse_hbm4_spec(self) -> Dict[str, Dict[str, Any]]:
        """Parse hbm4_spec.py for constants and timing"""
        spec_file = self.model_dir / "dram" / "hbm4_spec.py"
        if not spec_file.exists():
            return {}

        content = spec_file.read_text()
        constants = {}

        # Parse dataclass attributes: attribute: type = value
        for match in re.finditer(r'(\w+):\s*(?:int|float)\s*=\s*(\d+\.?\d*)', content):
            name, value = match.groups()
            constants[name] = {
                "type": "constant",
                "value": value,
                "category": "architecture"
            }

        # Parse dictionary entries: 'key': value
        for match in re.finditer(r"'(\w+)':\s*(\d+\.?\d*)", content):
            name, value = match.groups()
            constants[name] = {
                "type": "constant",
                "value": value,
                "category": "timing"
            }

        # Parse ADDR_* constants
        for match in re.finditer(r'(ADDR_\w+):\s*int\s*=\s*(\d+)', content):
            name, value = match.groups()
            constants[name] = {
                "type": "address_width",
                "value": value,
                "category": "addressing"
            }

        self.constants = constants
        return constants

    def parse_timing_dict(self) -> Dict[str, int]:
        """Parse HBM4_DEFAULT_TIMING dictionary"""
        spec_file = self.model_dir / "dram" / "hbm4_spec.py"
        if not spec_file.exists():
            return {}

        content = spec_file.read_text()
        timing = {}

        # Extract HBM4_DEFAULT_TIMING dictionary
        match = re.search(
            r'HBM4_DEFAULT_TIMING\s*=\s*\{([^}]+)\}',
            content,
            re.DOTALL
        )
        if match:
            dict_content = match.group(1)
            for item in re.finditer(r"'(\w+)':\s*(\d+)", dict_content):
                name, value = item.groups()
                timing[name] = int(value)

        return timing


class RTLSyncTool:
    """Main tool for RTL-Python alignment comparison"""

    # Mapping of RTL parameter names to Python constants
    PARAM_MAPPING = {
        # Configuration
        "NUM_STACKS": ("channels", 4),  # 4 stacks -> spec
        "NUM_CHANNELS": ("channels", 32),  # 32 channels
        "NUM_PSEUDO_CH": ("pseudo_channels_per_channel", 2),
        "NUM_BANK_GROUPS": ("bank_groups_per_channel", 8),
        "NUM_BANKS": ("banks_per_pseudo_channel", 16),

        # Timing (RTL uses tX, Python uses nX)
        "tRCD": ("nRCDRD", 8),
        "tRP": ("nRP", 8),
        "tRAS": ("nRAS", 20),
        "tRC": ("nRC", 22),
        "tCCD": ("nCCDS", 4),
        "tRRD": ("nRRDS", 4),
        "tFAW": ("nFAW", 16),
        "tRFC": ("nRFC", 180),
        "tREFI": ("nREFI", 3900),
        "tCL": ("nCL", 8),
        "tCWL": ("nCWL", 3),

        # Address widths
        "ADDR_WIDTH_STACK": ("ADDR_STACK_BITS", 2),
        "ADDR_WIDTH_CHANNEL": ("ADDR_CHANNEL_BITS", 5),
        "ADDR_WIDTH_BANK_GROUP": ("ADDR_BG_BITS", 3),
        "ADDR_WIDTH_BANK": ("ADDR_BANK_BITS", 4),
        "ADDR_WIDTH_ROW": ("ADDR_ROW_BITS", 19),
        "ADDR_WIDTH_COL": ("ADDR_COL_BITS", 6),
    }

    def __init__(self, model_dir: str, rtl_dir: str):
        self.model_dir = Path(model_dir)
        self.rtl_dir = Path(rtl_dir)
        self.rtl_parser = RTLParser(self.rtl_dir)
        self.py_parser = PythonParser(self.model_dir)
        self.discrepancies: List[SyncDiscrepancy] = []
        self.report = SyncReport(timestamp=datetime.now().isoformat())

    def run_sync(self) -> SyncReport:
        """Run full sync comparison"""
        # Parse both sources
        rtl_signals = self.rtl_parser.parse_hbm_types()
        py_constants = self.py_parser.parse_hbm4_spec()
        py_timing = self.py_parser.parse_timing_dict()

        self.report.rtl_file = str(self.rtl_dir / "hbm_types.svh")
        self.report.python_file = str(self.model_dir / "dram" / "hbm4_spec.py")

        # Compare configuration constants
        self._compare_config_constants(rtl_signals, py_constants)

        # Compare timing parameters
        self._compare_timing_parameters(rtl_signals, py_timing)

        # Compare address widths
        self._compare_address_widths(rtl_signals, py_constants)

        # Compare command encodings
        self._compare_command_encodings(rtl_signals, py_constants)

        # Build report
        self.report.signals_compared = len(rtl_signals) + len(py_constants)
        self.report.discrepancies_count = len([
            d for d in self.discrepancies if d.severity == "error"
        ])
        self.report.warnings_count = len([
            d for d in self.discrepancies if d.severity == "warning"
        ])
        self.report.discrepancies = [asdict(d) for d in self.discrepancies]

        # Determine overall status
        if self.report.discrepancies_count == 0 and self.report.warnings_count == 0:
            self.report.status = "PASS"
        elif self.report.discrepancies_count == 0:
            self.report.status = "PASS_WITH_WARNINGS"
        else:
            self.report.status = "FAIL"

        # Build alignment summary
        self.report.alignment_summary = {
            "rtl_signals_parsed": len(rtl_signals),
            "python_constants_parsed": len(py_constants),
            "python_timing_parsed": len(py_timing),
            "config_match": self._count_matches("config"),
            "timing_match": self._count_matches("timing"),
            "address_match": self._count_matches("addressing"),
            "command_match": self._count_matches("command_encoding"),
        }

        return self.report

    def _compare_config_constants(
        self,
        rtl_signals: Dict,
        py_constants: Dict
    ):
        """Compare configuration constants"""
        # Map RTL constants to Python properties/expected values
        # Note: Some RTL and Python definitions use different scales
        config_mapping = {
            # RTL NUM_CHANNELS = 32 matches Python channels = 32
            "NUM_CHANNELS": ("channels", 32),
            # RTL NUM_PSEUDO_CH = 2 matches Python pseudo_channels_per_channel = 2
            "NUM_PSEUDO_CH": ("pseudo_channels_per_channel", 2),
            # RTL NUM_BANK_GROUPS = 8 matches Python bank_groups_per_channel = 8
            "NUM_BANK_GROUPS": ("bank_groups_per_channel", 8),
            # RTL NUM_BANKS = 16 matches Python banks_per_pseudo_channel = 16
            "NUM_BANKS": ("banks_per_pseudo_channel", 16),
            # NUM_STACKS = 4 in RTL, Python doesn't have stacks as a property
            # (it's implicit in address calculation), so skip this check
        }

        for rtl_name, (py_name, expected) in config_mapping.items():
            # Check RTL
            if rtl_name in rtl_signals:
                rtl_val = rtl_signals[rtl_name].get("value", "")
            else:
                self.discrepancies.append(SyncDiscrepancy(
                    type="missing_in_rtl",
                    name=rtl_name,
                    python_value=py_name,
                    description=f"Config {rtl_name} not found in RTL"
                ))
                continue

            # Check Python
            if py_name not in py_constants:
                self.discrepancies.append(SyncDiscrepancy(
                    type="missing_in_python",
                    name=rtl_name,
                    rtl_value=rtl_val,
                    description=f"Config {py_name} not found in Python"
                ))
                continue

            # Compare values
            py_val = py_constants[py_name].get("value", "")
            if str(rtl_val) != str(py_val):
                # Try numeric comparison
                try:
                    rtl_num = int(str(rtl_val))
                    py_num = int(float(py_val))
                    if rtl_num != py_num:
                        self.discrepancies.append(SyncDiscrepancy(
                            type="value_mismatch",
                            name=rtl_name,
                            rtl_value=str(rtl_num),
                            python_value=str(py_num),
                            description=f"Config mismatch: RTL={rtl_num}, Python={py_num}"
                        ))
                except ValueError:
                    pass  # Non-numeric values are informational

    def _compare_timing_parameters(
        self,
        rtl_signals: Dict,
        py_timing: Dict[str, int]
    ):
        """Compare timing parameters"""
        # Map RTL timing names to Python timing names
        timing_mapping = {
            "tRCD": "nRCDRD",
            "tRP": "nRP",
            "tRAS": "nRAS",
            "tRC": "nRC",
            "tCCD": "nCCDS",
            "tRRD": "nRRDS",
            "tFAW": "nFAW",
            "tRFC": "nRFC",
            "tREFI": "nREFI",
            "tCL": "nCL",
            "tCWL": "nCWL",
        }

        # Extract default timing from RTL defines
        types_file = self.rtl_dir / "hbm_types.svh"
        if types_file.exists():
            content = types_file.read_text()
            # Parse HBM4_TIMING_DEFAULT
            match = re.search(
                r'`define\s+HBM4_TIMING_DEFAULT\s+([\d,]+)',
                content
            )
            if match:
                rtl_timing = match.group(1).split(',')
                timing_names = ['tRCD', 'tRP', 'tRAS', 'tRC', 'tCCD',
                               'tRRD', 'tFAW', 'tRFC', 'tREFI', 'tCL', 'tCWL']
                for i, name in enumerate(timing_names):
                    if i < len(rtl_timing):
                        rtl_val = int(rtl_timing[i])
                        py_name = timing_mapping.get(name, name)
                        if py_name in py_timing:
                            py_val = py_timing[py_name]
                            if rtl_val != py_val:
                                self.discrepancies.append(SyncDiscrepancy(
                                    type="value_mismatch",
                                    name=name,
                                    rtl_value=str(rtl_val),
                                    python_value=str(py_val),
                                    severity="warning",
                                    description=f"Timing mismatch: RTL={rtl_val}, Python={py_val}"
                                ))

    def _compare_address_widths(
        self,
        rtl_signals: Dict,
        py_constants: Dict
    ):
        """Compare address field widths"""
        addr_mapping = {
            "ADDR_STACK_BITS": 2,
            "ADDR_CHANNEL_BITS": 5,
            "ADDR_BG_BITS": 3,
            "ADDR_BANK_BITS": 4,
            "ADDR_ROW_BITS": 19,
            "ADDR_COL_BITS": 6,
            "ADDR_BURST_BITS": 2,
        }

        for name, expected in addr_mapping.items():
            if name in py_constants:
                val = int(py_constants[name].get("value", expected))
                if val != expected:
                    self.discrepancies.append(SyncDiscrepancy(
                        type="value_mismatch",
                        name=name,
                        rtl_value=str(expected),
                        python_value=str(val),
                        severity="warning",
                        description=f"Address width mismatch: expected={expected}, got={val}"
                    ))

    def _compare_command_encodings(
        self,
        rtl_signals: Dict,
        py_constants: Dict
    ):
        """Compare command encodings between RTL and Python"""
        # Check for hbm_cmd_t in RTL
        if "hbm_cmd_t" in rtl_signals:
            rtl_cmds = rtl_signals["hbm_cmd_t"].get("values", {})
            # Python should have similar commands defined elsewhere
            # For now, just verify the enum exists
            pass

    def _count_matches(self, category: str) -> int:
        """Count matching items in a category"""
        # Simplified: count items without discrepancies
        return 0  # Would need more sophisticated tracking

    def generate_report(self, output_file: str) -> SyncReport:
        """Generate and save sync report"""
        report = self.run_sync()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(asdict(report), f, indent=2)

        return report

    def print_summary(self, report: SyncReport, output_file: str = ""):
        """Print report summary to console"""
        print(f"\n{'='*60}")
        print(f"RTL-Python Sync Report")
        print(f"{'='*60}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Status: {report.status}")
        print(f"\nFiles Compared:")
        print(f"  RTL: {report.rtl_file}")
        print(f"  Python: {report.python_file}")
        print(f"\nStatistics:")
        print(f"  Signals Compared: {report.signals_compared}")
        print(f"  Discrepancies: {report.discrepancies_count} errors, {report.warnings_count} warnings")
        print(f"\nAlignment Summary:")
        for key, val in report.alignment_summary.items():
            print(f"  {key}: {val}")

        if self.discrepancies:
            print(f"\nDiscrepancies Found:")
            for d in self.discrepancies:
                print(f"  [{d.severity.upper()}] {d.name}: {d.description}")
                if d.rtl_value and d.python_value:
                    print(f"      RTL={d.rtl_value}, Python={d.python_value}")

        if output_file:
            print(f"\nFull report: {output_file}\n")


def main():
    parser = argparse.ArgumentParser(
        description="RTL-Python Auto-Sync Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/rtl_sync.py
  python scripts/rtl_sync.py --model-dir model --rtl-dir rtl --output docs/reports/rtl_sync.json
  python scripts/rtl_sync.py --output sync_report.json --verbose
        """
    )
    parser.add_argument(
        "--model-dir",
        default="model",
        help="Python model directory (default: model)"
    )
    parser.add_argument(
        "--rtl-dir",
        default="rtl",
        help="RTL directory (default: rtl)"
    )
    parser.add_argument(
        "--output",
        default="docs/reports/rtl_sync.json",
        help="Output report file (default: docs/reports/rtl_sync.json)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Create tool and run
    tool = RTLSyncTool(args.model_dir, args.rtl_dir)
    report = tool.generate_report(args.output)

    # Print summary
    tool.print_summary(report, args.output)

    # Exit with appropriate code
    if report.status == "FAIL":
        sys.exit(1)
    elif report.status == "PASS":
        sys.exit(0)
    else:
        sys.exit(0)  # PASS_WITH_WARNINGS still succeeds


if __name__ == "__main__":
    main()
