#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HBM4 Simulation Package

Simulation and benchmarking tools for HBM system modeling.
"""

__version__ = "1.1.0"
__all__ = [
    "HBM4UnifiedSimulator",
]

# Import main entry points for console scripts
from sim.simulator import run_simulation as simulate
from sim.benchmark import main as run_benchmark
from sim.hbm4_unified_simulator import HBM4UnifiedSimulator, main as unified_main
from sim.unified_simulator import run_unified_simulation as unified_sim_main
from sim.benchmark_suite import PerformanceBenchmarkSuite, main as benchmark_suite_main

# Import RTL cosimulation
from sim.rtl_interface import (
    RTLInterface,
    CoSimConfig,
    CoSimStats,
    ResultComparator,
    create_rtl_interface,
)

# Import result comparison
from sim.result_comparison import (
    ResultAnalyzer,
    ComparisonReport,
    ComparisonType,
    RegressionStatus,
    BandwidthAnalyzer,
    LatencyAnalyzer,
    quick_compare,
)

# Import visualization
from sim.visualization.advanced_charts import (
    AdvancedVisualizer,
    PerformanceAnalyzer,
    VisualizationData,
    create_visualizer,
    analyze_and_visualize,
)

# Import analysis integration
from sim.analysis_integration import (
    SimulatorAnalyzer,
    AnalysisReport,
)

# Import compliance integration
from sim.compliance_integration import (
    ComplianceValidator,
    ComplianceReport,
    run_compliance_check,
)

# Import export functionality
from model.export import (
    AnalysisReportExporter,
    ExporterConfig,
    HBM4CLI,
    VisualizationExporter,
    ChartData,
    quick_chart,
)

__all__ += [
    "simulate",
    "run_benchmark",
    "unified_main",
    "unified_sim_main",
    "benchmark_suite_main",
    # RTL Cosimulation
    "RTLInterface",
    "CoSimConfig",
    "CoSimStats",
    "ResultComparator",
    "create_rtl_interface",
    # Result Comparison
    "ResultAnalyzer",
    "ComparisonReport",
    "ComparisonType",
    "RegressionStatus",
    "BandwidthAnalyzer",
    "LatencyAnalyzer",
    "quick_compare",
    # Visualization
    "AdvancedVisualizer",
    "PerformanceAnalyzer",
    "VisualizationData",
    "create_visualizer",
    "analyze_and_visualize",
    # Analysis Integration
    "SimulatorAnalyzer",
    "AnalysisReport",
    # Compliance Integration
    "ComplianceValidator",
    "ComplianceReport",
    "run_compliance_check",
    # Export
    "AnalysisReportExporter",
    "ExporterConfig",
    "HBM4CLI",
    "VisualizationExporter",
    "ChartData",
    "quick_chart",
]