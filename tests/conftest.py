"""
Pytest Configuration and Shared Fixtures

This module provides shared fixtures for all HBM simulation tests:
- HBM4 configuration fixtures
- Traffic generator fixtures
- Simulator fixtures
- Common test utilities
"""

import pytest
import time
from typing import Optional, Dict, Any

from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT
from model.dram.timing import HBM3Timing, HBM4Timing, get_timing_for_speed_grade
from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from sim.simulator import (
    HBMSimulator,
    SimulationConfig,
    TrafficPattern,
    TrafficGenerator,
)


# =============================================================================
# HBM Configuration Fixtures
# =============================================================================

@pytest.fixture
def hbm3_config() -> HBMConfig:
    """Default HBM3 configuration fixture

    Returns a standard HBM3 configuration based on JEDEC JESD238.
    """
    return HBM3_DEFAULT


@pytest.fixture
def hbm4_config() -> HBMConfig:
    """Default HBM4 configuration fixture

    Returns an HBM4 configuration based on JEDEC JESD270-4A.
    """
    return HBM4_DEFAULT


@pytest.fixture
def hbm4_8gbps_config() -> HBMConfig:
    """HBM4 configuration at 8 Gbps speed grade"""
    config = HBM4_DEFAULT.copy()
    config.timing = get_timing_for_speed_grade("8Gbps")
    return config


@pytest.fixture
def hbm4_12gbps_config() -> HBMConfig:
    """HBM4 configuration at 12 Gbps speed grade"""
    config = HBM4_DEFAULT.copy()
    config.timing = get_timing_for_speed_grade("12Gbps")
    config.data_rate = 12.0e9
    return config


@pytest.fixture
def hbm4_16gbps_config() -> HBMConfig:
    """HBM4 configuration at 16 Gbps speed grade"""
    config = HBM4_DEFAULT.copy()
    config.timing = get_timing_for_speed_grade("16Gbps")
    config.data_rate = 16.0e9
    return config


@pytest.fixture
def single_channel_config() -> HBMConfig:
    """Single-channel configuration for focused testing"""
    config = HBM3_DEFAULT.copy()
    config.stack_count = 1
    config.channels_per_stack = 1
    return config


@pytest.fixture
def high_performance_config() -> HBMConfig:
    """High-performance configuration for stress testing"""
    config = HBM4_DEFAULT.copy()
    config.stack_count = 4
    config.channels_per_stack = 32
    config.queue_depth = 128
    config.max_outstanding = 64
    return config


@pytest.fixture
def qos_config() -> HBMConfig:
    """QoS-enabled configuration for priority testing"""
    config = HBM3_DEFAULT.copy()
    config.scheduler_mode = "qos"
    config.bw_guarantee_critical = 200.0
    config.bw_guarantee_high = 300.0
    config.bw_guarantee_normal = 200.0
    config.bw_guarantee_low = 100.0
    return config


# =============================================================================
# Simulation Configuration Fixtures
# =============================================================================

@pytest.fixture
def default_sim_config(hbm3_config) -> SimulationConfig:
    """Default simulation configuration

    Suitable for most integration and regression tests.
    """
    return SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        read_ratio=0.7,
        seed=42,
        hbm_config=hbm3_config,
    )


@pytest.fixture
def quick_sim_config(hbm3_config) -> SimulationConfig:
    """Quick simulation configuration for fast tests

    Uses shorter simulation time for rapid test execution.
    """
    return SimulationConfig(
        simulation_time_us=10.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.3,
        read_ratio=0.7,
        seed=42,
        hbm_config=hbm3_config,
    )


@pytest.fixture
def long_sim_config(hbm3_config) -> SimulationConfig:
    """Long simulation configuration for comprehensive tests

    Uses longer simulation time for thorough validation.
    """
    return SimulationConfig(
        simulation_time_us=500.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.7,
        read_ratio=0.7,
        seed=42,
        hbm_config=hbm3_config,
    )


@pytest.fixture
def sequential_sim_config(hbm3_config) -> SimulationConfig:
    """Sequential access simulation configuration

    Optimized for testing sequential memory access patterns.
    """
    return SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.8,
        read_ratio=1.0,
        seed=42,
        hbm_config=hbm3_config,
    )


@pytest.fixture
def stress_sim_config(hbm4_config) -> SimulationConfig:
    """Stress test simulation configuration

    High load configuration for stress testing.
    """
    return SimulationConfig(
        simulation_time_us=200.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.9,
        read_ratio=0.7,
        max_requests_per_cycle=4,
        hbm_config=hbm4_config,
    )


# =============================================================================
# Simulator Fixtures
# =============================================================================

@pytest.fixture
def simulator(default_sim_config) -> HBMSimulator:
    """Default simulator fixture

    Creates a simulator with default configuration.
    """
    return HBMSimulator(default_sim_config)


@pytest.fixture
def quick_simulator(quick_sim_config) -> HBMSimulator:
    """Quick simulator fixture for fast tests"""
    return HBMSimulator(quick_sim_config)


@pytest.fixture
def long_simulator(long_sim_config) -> HBMSimulator:
    """Long-running simulator fixture for comprehensive tests"""
    return HBMSimulator(long_sim_config)


@pytest.fixture
def sequential_simulator(sequential_sim_config) -> HBMSimulator:
    """Sequential access simulator fixture"""
    return HBMSimulator(sequential_sim_config)


@pytest.fixture
def stress_simulator(stress_sim_config) -> HBMSimulator:
    """Stress test simulator fixture"""
    return HBMSimulator(stress_sim_config)


# =============================================================================
# Traffic Generator Fixtures
# =============================================================================

@pytest.fixture
def traffic_generator(default_sim_config) -> TrafficGenerator:
    """Default traffic generator fixture"""
    return TrafficGenerator(default_sim_config)


@pytest.fixture
def random_traffic_generator(hbm3_config) -> TrafficGenerator:
    """Random traffic generator fixture"""
    config = SimulationConfig(
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        seed=42,
        hbm_config=hbm3_config,
    )
    return TrafficGenerator(config)


@pytest.fixture
def sequential_traffic_generator(hbm3_config) -> TrafficGenerator:
    """Sequential traffic generator fixture"""
    config = SimulationConfig(
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.8,
        seed=42,
        hbm_config=hbm3_config,
    )
    return TrafficGenerator(config)


@pytest.fixture
def hot_spot_traffic_generator(hbm3_config) -> TrafficGenerator:
    """Hot spot traffic generator fixture"""
    config = SimulationConfig(
        traffic_pattern=TrafficPattern.HOT_SPOT,
        request_rate=0.5,
        seed=42,
        hbm_config=hbm3_config,
    )
    return TrafficGenerator(config)


# =============================================================================
# Test Data and Utilities
# =============================================================================

@pytest.fixture
def benchmark_thresholds() -> Dict[str, float]:
    """Standard benchmark thresholds for validation

    These thresholds represent expected performance targets.
    Actual performance may vary based on hardware and configuration.
    """
    return {
        # Bandwidth thresholds (GB/s)
        'bandwidth_min_random': 50.0,
        'bandwidth_min_sequential': 100.0,
        'bandwidth_min_hot_spot': 80.0,
        'bandwidth_efficiency_min': 0.10,  # 10% of theoretical peak

        # Latency thresholds (cycles)
        'latency_p50_max': 100.0,
        'latency_p99_max': 500.0,
        'latency_avg_max': 200.0,

        # Row hit rate thresholds
        'row_hit_rate_random_min': 0.0,
        'row_hit_rate_sequential_min': 0.5,
        'row_hit_rate_hot_spot_min': 0.4,

        # Queue thresholds
        'queue_overflow_max': 0,
        'queue_utilization_max': 0.95,
    }


@pytest.fixture
def regression_baselines() -> Dict[str, Any]:
    """Baseline values for regression testing

    These values represent known-good performance metrics.
    Changes that cause significant deviations may indicate regressions.
    """
    return {
        'throughput_gbps': 100.0,  # Minimum expected throughput
        'row_hit_rate': 0.20,       # Minimum row hit rate for random
        'efficiency': 0.30,         # Minimum efficiency
        'latency_avg': 150.0,       # Maximum average latency
        'queue_rejects': 0,         # No queue overflow expected
    }


# =============================================================================
# Pytest Configuration Hooks
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "benchmark: marks tests as benchmark tests (may be slow)"
    )
    config.addinivalue_line(
        "markers", "regression: marks tests as regression tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "hbm3: marks tests as HBM3 specific"
    )
    config.addinivalue_line(
        "markers", "hbm4: marks tests as HBM4 specific"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add markers based on test location
        if "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.benchmark)
        if "regression" in item.nodeid:
            item.add_marker(pytest.mark.regression)
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)


# =============================================================================
# Performance Measurement Utilities
# =============================================================================

class PerformanceTimer:
    """Context manager for measuring test execution time"""

    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time

    @property
    def elapsed_ms(self) -> float:
        """Elapsed time in milliseconds"""
        return self.elapsed * 1000.0

    @property
    def elapsed_s(self) -> float:
        """Elapsed time in seconds"""
        return self.elapsed


@pytest.fixture
def timer():
    """Performance timer fixture

    Usage:
        def test_something(timer):
            with timer:
                # code to measure
            print(f"Took {timer.elapsed_ms:.2f} ms")
    """
    return PerformanceTimer