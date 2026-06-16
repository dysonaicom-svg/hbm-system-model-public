#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HBM4 Simulation Package

Simulation and benchmarking tools for HBM system modeling.
"""

__version__ = "1.0.0"
__all__ = [
    "HBM4UnifiedSimulator",
]

# Import main entry points for console scripts
from sim.simulator import run_simulation as simulate
from sim.benchmark import main as run_benchmark
from sim.hbm4_unified_simulator import HBM4UnifiedSimulator, main as unified_main
from sim.unified_simulator import run_unified_simulation as unified_sim_main

__all__ += [
    "simulate",
    "run_benchmark",
    "unified_main",
    "unified_sim_main",
]