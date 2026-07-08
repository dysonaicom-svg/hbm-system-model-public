"""CLI Interface Module for HBM4 Analysis"""

import argparse
import sys
from typing import Optional, List
from pathlib import Path

# Import analysis modules
from model.analysis.bottleneck_detector import BottleneckDetector
from model.analysis.hotspot_detector import HotspotDetector
from model.analysis.latency_analyzer import LatencyDistribution
from model.analysis.dvfs_analyzer import DVFSAnalyzer
from model.compliance.jedec_validator import JEDECValidator, ComplianceLevel


class HBM4CLI:
    """Command-line interface for HBM4 analysis"""

    def __init__(self):
        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build argument parser"""
        parser = argparse.ArgumentParser(
            description="HBM4 System Modeling Platform CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Analyze command
        analyze_parser = subparsers.add_parser("analyze", help="Run analysis")
        analyze_parser.add_argument("--type", "-t", choices=["bottleneck", "hotspot", "latency", "dvfs"],
                                    default="bottleneck", help="Analysis type")
        analyze_parser.add_argument("--input", "-i", help="Input trace file")
        analyze_parser.add_argument("--output", "-o", help="Output report file")
        analyze_parser.add_argument("--format", "-f", choices=["json", "html", "csv"],
                                    default="json", help="Output format")

        # Validate command
        validate_parser = subparsers.add_parser("validate", help="Run compliance validation")
        validate_parser.add_argument("--config", "-c", help="Config file")
        validate_parser.add_argument("--level", "-l", choices=["strict", "normal", "relaxed"],
                                     default="normal", help="Validation level")
        validate_parser.add_argument("--output", "-o", help="Output report file")

        # Export command
        export_parser = subparsers.add_parser("export", help="Export analysis data")
        export_parser.add_argument("--input", "-i", required=True, help="Input data file")
        export_parser.add_argument("--output", "-o", required=True, help="Output file")
        export_parser.add_argument("--format", "-f", choices=["json", "html", "csv"],
                                   default="json", help="Output format")

        # Benchmark command
        bench_parser = subparsers.add_parser("benchmark", help="Run performance benchmark")
        bench_parser.add_argument("--mode", "-m", choices=["quick", "full", "stress"],
                                  default="quick", help="Benchmark mode")
        bench_parser.add_argument("--channels", "-c", type=int, default=32, help="Number of channels")

        return parser

    def run_analyze(self, args) -> int:
        """Run analysis command"""
        print(f"Running {args.type} analysis...")

        if args.type == "bottleneck":
            detector = BottleneckDetector()
            # Run with sample data or load from input
            result = detector.analyze([])
        elif args.type == "hotspot":
            detector = HotspotDetector()
            result = detector.detect_from_trace([])
        elif args.type == "latency":
            dist = LatencyDistribution()
            result = dist.analyze()
        elif args.type == "dvfs":
            analyzer = DVFSAnalyzer()
            result = analyzer.analyze_dvfs_tradeoff(1000, 1.0)
        else:
            print(f"Unknown analysis type: {args.type}")
            return 1

        # Export result
        if args.output:
            from model.export.report_exporter import AnalysisReportExporter
            exporter = AnalysisReportExporter()
            data = result if isinstance(result, dict) else {"result": str(result)}
            exporter.export_json(data, args.output)
            print(f"Report saved to {args.output}")

        return 0

    def run_validate(self, args) -> int:
        """Run validation command"""
        print(f"Running compliance validation (level: {args.level})...")

        validator = JEDECValidator()

        # Sample timing parameters for validation
        timing_params = {
            "tRCD_ns": 10.0,
            "tRP_ns": 10.0,
            "tRAS_ns": 25.0,
            "tRC_ns": 35.0,
            "tRRD_L_ns": 3.0,
            "tRRD_S_ns": 4.0,
        }

        checks = validator.run_all_checks(timing_params)

        print(f"\nValidation Results:")
        print("-" * 50)
        for check in checks:
            status = "✓" if check.level != ComplianceLevel.FAIL else "✗"
            print(f"{status} [{check.level.value:8}] {check.check_name}: {check.message}")

        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump({
                    "checks": [asdict(c) for c in checks],
                    "level": args.level,
                }, f, indent=2, default=str)
            print(f"\nReport saved to {args.output}")

        return 0

    def run_export(self, args) -> int:
        """Run export command"""
        from model.export.report_exporter import AnalysisReportExporter

        print(f"Exporting {args.input} to {args.format}...")

        with open(args.input, 'r') as f:
            import json
            data = json.load(f)

        exporter = AnalysisReportExporter()
        if args.format == "json":
            exporter.export_json(data, args.output)
        elif args.format == "html":
            exporter.export_html(data, output_path=args.output)
        elif args.format == "csv":
            if isinstance(data, list):
                exporter.export_csv(data, args.output)
            else:
                print("CSV export requires list data")
                return 1

        print(f"Exported to {args.output}")
        return 0

    def run_benchmark(self, args) -> int:
        """Run benchmark command"""
        print(f"Running {args.mode} benchmark with {args.channels} channels...")

        from sim.benchmark_suite import BenchmarkSuite
        from sim.simulation_config import SimulationConfig

        config = SimulationConfig()
        suite = BenchmarkSuite(config)

        if args.mode == "quick":
            results = suite.run_quick_benchmark()
        elif args.mode == "full":
            results = suite.run_full_benchmark()
        else:
            results = suite.run_stress_test()

        print("\nBenchmark Results:")
        print("-" * 50)
        for name, metrics in results.items():
            print(f"{name}: {metrics}")

        return 0

    def run(self, argv: Optional[List[str]] = None) -> int:
        """Run CLI"""
        args = self.parser.parse_args(argv)

        if args.command is None:
            self.parser.print_help()
            return 0

        if args.command == "analyze":
            return self.run_analyze(args)
        elif args.command == "validate":
            return self.run_validate(args)
        elif args.command == "export":
            return self.run_export(args)
        elif args.command == "benchmark":
            return self.run_benchmark(args)
        else:
            self.parser.print_help()
            return 0


def main():
    """Main entry point"""
    cli = HBM4CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
