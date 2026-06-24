"""
Pytest Configuration and Shared Fixtures

This module provides shared fixtures for all HBM simulation tests:
- HBM4 specification fixtures
- HBM4 configuration fixtures
- Controller instance fixtures
- DRAM model fixtures
- Address decoder fixtures
- Scheduler fixtures
- DFI interface fixtures
- Channel model fixtures
- Request/response fixtures
- Common test utilities
"""

import pytest
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade, HBM4_SPEED_GRADES
from model.dram.timing import HBM4Timing, get_timing_for_speed_grade, HBM3Timing
from model.dram.hbm4_channel_model import (
    HBM4Channel, HBM4ChannelArray, PseudoChannel,
    HBM4ChannelState, PseudoChannelState, BankGroupScheduler
)
from model.dram.hbm4_bank_state_machine import (
    HBM4BankState, HBM4BankTiming, TimingViolation
)
from model.dram.dfi_interface import (
    DFI5Interface, DFICommand, DFILowPowerState,
    DFIRequest, DFIResponse
)
from model.dram.ecc_crc import HBM4ECC, HBM4CRC, ErrorTracker
from model.dram.lane_repair import HBM4LaneRepairModel, LaneRepairEntry
from model.dram.phy_training import PHYTrainingStateMachine, PHYInitializationStateMachine, HBM4PHYManager

from model.controller.hbm4_controller import HBM4Controller, ChannelState, HBM4ControllerStats
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.address_decoder import DecodedAddress
from model.controller.hbm4_qos_scheduler import (
    HBM4QoSScheduler, QoSLevel, TrafficType, BankConflictTracker
)
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.controller.request import HBMRequest, HBMResponse, RequestState
from model.controller.queue import ReadQueue, WriteQueue, QueueManager
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT

from sim.simulator import (
    HBMSimulator,
    SimulationConfig,
    TrafficPattern,
    TrafficGenerator,
)


# =============================================================================
# HBM4 Specification Fixtures
# =============================================================================

@pytest.fixture
def hbm4_spec() -> HBM4Spec:
    """Default HBM4 specification fixture

    Returns a standard HBM4 specification based on JEDEC JESD270-4A.
    """
    return HBM4Spec()


@pytest.fixture
def hbm4_spec_8gbps() -> HBM4Spec:
    """HBM4 specification at 8 Gbps speed grade"""
    return create_hbm4_spec_from_speed_grade("8Gbps")


@pytest.fixture
def hbm4_spec_12gbps() -> HBM4Spec:
    """HBM4 specification at 12 Gbps speed grade"""
    return create_hbm4_spec_from_speed_grade("12Gbps")


@pytest.fixture
def hbm4_spec_16gbps() -> HBM4Spec:
    """HBM4 specification at 16 Gbps speed grade"""
    return create_hbm4_spec_from_speed_grade("16Gbps")


@pytest.fixture
def hbm3_spec() -> HBM4Spec:
    """HBM3 specification for comparison tests"""
    spec = HBM4Spec()
    spec.channels = 8
    spec.pseudo_channels_per_channel = 2
    spec.io_width = 1024
    spec.data_rate_gtps = 6.4
    spec.bandwidth = 0.8192  # 6.4 * 1024 / 8 / 1000
    spec.nCL = 6
    spec.nRCDRD = 6
    spec.nRCDWR = 6
    return spec


@pytest.fixture
def hbm4_timing() -> HBM4Timing:
    """Default HBM4 timing parameters fixture"""
    return HBM4Timing()


@pytest.fixture
def hbm4_bank_timing() -> HBM4BankTiming:
    """Enhanced HBM4 bank timing parameters fixture"""
    return HBM4BankTiming()


@pytest.fixture
def hbm3_timing() -> HBM3Timing:
    """HBM3 timing parameters fixture"""
    return HBM3Timing()


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
# HBM4 Controller Fixtures
# =============================================================================

@pytest.fixture
def hbm4_controller() -> HBM4Controller:
    """Default HBM4 controller fixture

    Returns a standard HBM4Controller with all features enabled.
    """
    return HBM4Controller()


@pytest.fixture
def hbm4_controller_no_qos() -> HBM4Controller:
    """HBM4 controller without QoS scheduling"""
    return HBM4Controller(enable_qos=False)


@pytest.fixture
def hbm4_controller_no_refresh() -> HBM4Controller:
    """HBM4 controller without refresh scheduling"""
    return HBM4Controller(enable_refresh=False)


@pytest.fixture
def hbm4_controller_no_dfi() -> HBM4Controller:
    """HBM4 controller without DFI interface"""
    return HBM4Controller(enable_dfi=False)


@pytest.fixture
def hbm4_controller_with_spec(hbm4_spec) -> HBM4Controller:
    """HBM4 controller with custom spec"""
    return HBM4Controller(spec=hbm4_spec)


@pytest.fixture
def hbm4_controller_16ch() -> HBM4Controller:
    """HBM4 controller with 16 channels"""
    spec = HBM4Spec()
    spec.channels = 16
    return HBM4Controller(spec=spec)


@pytest.fixture
def hbm4_controller_8gbps() -> HBM4Controller:
    """HBM4 controller at 8 Gbps"""
    spec = create_hbm4_spec_from_speed_grade("8Gbps")
    return HBM4Controller(spec=spec)


@pytest.fixture
def hbm4_controller_12gbps() -> HBM4Controller:
    """HBM4 controller at 12 Gbps"""
    spec = create_hbm4_spec_from_speed_grade("12Gbps")
    return HBM4Controller(spec=spec)


@pytest.fixture
def hbm4_controller_16gbps() -> HBM4Controller:
    """HBM4 controller at 16 Gbps"""
    spec = create_hbm4_spec_from_speed_grade("16Gbps")
    return HBM4Controller(spec=spec)


# =============================================================================
# Address Decoder Fixtures
# =============================================================================

@pytest.fixture
def hbm4_address_decoder() -> HBM4AddressDecoder:
    """Default HBM4 address decoder fixture"""
    return HBM4AddressDecoder()


@pytest.fixture
def hbm4_address_decoder_rcbc() -> HBM4AddressDecoder:
    """HBM4 address decoder with RCBC mapping"""
    return HBM4AddressDecoder(address_mapping="RCBC")


@pytest.fixture
def hbm4_address_decoder_rbc() -> HBM4AddressDecoder:
    """HBM4 address decoder with RBC mapping"""
    return HBM4AddressDecoder(address_mapping="RBC")


# =============================================================================
# QoS Scheduler Fixtures
# =============================================================================

@pytest.fixture
def hbm4_qos_scheduler() -> HBM4QoSScheduler:
    """Default HBM4 QoS scheduler fixture"""
    return HBM4QoSScheduler()


@pytest.fixture
def hbm4_qos_scheduler_with_config(qos_config) -> HBM4QoSScheduler:
    """HBM4 QoS scheduler with custom configuration"""
    return HBM4QoSScheduler(
        enable_qos=True,
        max_priority=qos_config.max_qos_level
    )


@pytest.fixture
def bank_conflict_tracker() -> BankConflictTracker:
    """Bank conflict tracker fixture"""
    return BankConflictTracker()


# =============================================================================
# Refresh Scheduler Fixtures
# =============================================================================

@pytest.fixture
def hbm4_refresh_scheduler() -> HBM4RefreshScheduler:
    """Default HBM4 refresh scheduler fixture"""
    return HBM4RefreshScheduler()


@pytest.fixture
def hbm4_refresh_scheduler_per_bank() -> HBM4RefreshScheduler:
    """HBM4 refresh scheduler in per-bank mode"""
    return HBM4RefreshScheduler(mode=RefreshMode.PER_BANK)


@pytest.fixture
def hbm4_refresh_scheduler_autonomous() -> HBM4RefreshScheduler:
    """HBM4 refresh scheduler in autonomous mode"""
    return HBM4RefreshScheduler(mode=RefreshMode.AUTONOMOUS)


# =============================================================================
# Channel Model Fixtures
# =============================================================================

@pytest.fixture
def hbm4_channel(hbm4_spec) -> HBM4Channel:
    """Single HBM4 channel fixture"""
    return HBM4Channel(channel_id=0, spec=hbm4_spec)


@pytest.fixture
def hbm4_channel_enhanced(hbm4_spec) -> HBM4Channel:
    """HBM4 channel with enhanced bank state machines"""
    return HBM4Channel(channel_id=0, spec=hbm4_spec, use_enhanced_banks=True)


@pytest.fixture
def hbm4_channel_array() -> HBM4ChannelArray:
    """Full HBM4 channel array fixture (32 channels)"""
    return HBM4ChannelArray()


@pytest.fixture
def hbm4_bank_group_scheduler(hbm4_timing) -> BankGroupScheduler:
    """Bank group scheduler fixture"""
    return BankGroupScheduler(hbm4_timing)


# =============================================================================
# DFI Interface Fixtures
# =============================================================================

@pytest.fixture
def dfi_interface(hbm4_spec) -> DFI5Interface:
    """DFI 5.0 interface fixture"""
    return DFI5Interface(spec=hbm4_spec)


@pytest.fixture
def dfi_interface_low_power(hbm4_spec) -> DFI5Interface:
    """DFI interface in low power state"""
    dfi = DFI5Interface(spec=hbm4_spec)
    dfi.set_low_power_state(DFILowPowerState.LP_CTRL)
    return dfi


@pytest.fixture
def dfi_request() -> DFIRequest:
    """DFI request fixture"""
    return DFIRequest(
        command=DFICommand.READ,
        address=0x1000,
        length=64
    )


# =============================================================================
# PHY Training Fixtures
# =============================================================================

@pytest.fixture
def phy_training_state_machine(hbm4_spec) -> PHYTrainingStateMachine:
    """PHY training state machine fixture"""
    return PHYTrainingStateMachine(spec=hbm4_spec)


@pytest.fixture
def phy_init_state_machine(hbm4_spec) -> PHYInitializationStateMachine:
    """PHY initialization state machine fixture"""
    return PHYInitializationStateMachine(spec=hbm4_spec)


@pytest.fixture
def phy_manager(hbm4_spec) -> HBM4PHYManager:
    """HBM4 PHY manager fixture"""
    return HBM4PHYManager(spec=hbm4_spec)


# =============================================================================
# Lane Repair Fixtures
# =============================================================================

@pytest.fixture
def lane_repair_model(hbm4_spec) -> HBM4LaneRepairModel:
    """Lane repair model fixture"""
    return HBM4LaneRepairModel(spec=hbm4_spec)


@pytest.fixture
def lane_repair_entry() -> LaneRepairEntry:
    """Lane repair entry fixture"""
    return LaneRepairEntry(
        lane_id=0,
        failure_cycle=100,
        failure_mode="stuck_at_0"
    )


# =============================================================================
# ECC/CRC Fixtures
# =============================================================================

@pytest.fixture
def hbm4_ecc(hbm4_spec) -> HBM4ECC:
    """HBM4 ECC engine fixture"""
    return HBM4ECC(spec=hbm4_spec)


@pytest.fixture
def hbm4_crc(hbm4_spec) -> HBM4CRC:
    """HBM4 CRC generator fixture"""
    return HBM4CRC(spec=hbm4_spec)


@pytest.fixture
def error_tracker() -> ErrorTracker:
    """Error tracker fixture"""
    return ErrorTracker()


# =============================================================================
# Queue Fixtures
# =============================================================================

@pytest.fixture
def read_queue() -> ReadQueue:
    """Read queue fixture"""
    return ReadQueue(max_depth=32)


@pytest.fixture
def write_queue() -> WriteQueue:
    """Write queue fixture"""
    return WriteQueue(max_depth=32)


@pytest.fixture
def queue_manager() -> QueueManager:
    """Queue manager fixture"""
    return QueueManager.create(queue_depth=64)


# =============================================================================
# Request/Response Fixtures
# =============================================================================

@pytest.fixture
def sample_read_request() -> HBMRequest:
    """Sample read request fixture"""
    return HBMRequest(
        request_id="test_read_1",
        addr=0x1000,
        length=64,
        is_read=True,
        qos=8
    )


@pytest.fixture
def sample_write_request() -> HBMRequest:
    """Sample write request fixture"""
    return HBMRequest(
        request_id="test_write_1",
        addr=0x2000,
        length=64,
        is_read=False,
        qos=8,
        data=b'\x00' * 64
    )


@pytest.fixture
def sample_high_priority_request() -> HBMRequest:
    """High priority read request fixture"""
    return HBMRequest(
        request_id="test_high_prio_1",
        addr=0x3000,
        length=64,
        is_read=True,
        qos=15
    )


@pytest.fixture
def sample_low_priority_request() -> HBMRequest:
    """Low priority read request fixture"""
    return HBMRequest(
        request_id="test_low_prio_1",
        addr=0x4000,
        length=64,
        is_read=True,
        qos=0
    )


@pytest.fixture
def request_batch() -> List[HBMRequest]:
    """Batch of sample requests for integration testing"""
    requests = []
    for i in range(10):
        requests.append(HBMRequest(
            request_id=f"batch_req_{i}",
            addr=(i + 1) * 0x1000,
            length=64,
            is_read=(i % 2 == 0),
            qos=i % 16
        ))
    return requests


# =============================================================================
# Address Decode Result Fixtures
# =============================================================================

@pytest.fixture
def sample_decode_result() -> DecodedAddress:
    """Sample address decode result fixture"""
    return DecodedAddress(
        channel_id=0,
        pseudo_channel_id=0,
        bank_group_id=0,
        bank_id=0,
        row_id=0x1000,
        col_id=0,
        stack_id=0
    )


@pytest.fixture
def decode_results_all_channels() -> List:
    """Decode results for all 32 channels"""
    decoder = HBM4AddressDecoder()
    results = []
    for ch in range(32):
        addr = (ch & 0x1F) << 41 | 0x8
        results.append(decoder.decode(addr))
    return results


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
# Test Data Fixtures
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


@pytest.fixture
def test_addresses() -> List[int]:
    """Test addresses for various test scenarios"""
    return [
        0x0000_0000_0000_0000,  # Address 0
        0x0000_0000_0000_1000,  # 4KB aligned
        0x0000_0000_1000_0000,  # Large offset
        0x1000_0000_0000_0000,  # High address
        0xFFFF_FFFF_FFFF_FFFF,  # Max address
    ]


@pytest.fixture
def test_addresses_all_channels() -> List[int]:
    """Test addresses covering all 32 channels"""
    return [(ch & 0x1F) << 41 | 0x8 for ch in range(32)]


@pytest.fixture
def test_qos_levels() -> List[int]:
    """Test QoS levels from 0 to 15"""
    return list(range(16))


@pytest.fixture
def test_traffic_patterns() -> List[TrafficPattern]:
    """All available traffic patterns for testing"""
    return [
        TrafficPattern.RANDOM,
        TrafficPattern.SEQUENTIAL,
        TrafficPattern.STRIDE,
        TrafficPattern.HOT_SPOT,
    ]


# =============================================================================
# Logging Fixtures
# =============================================================================

@pytest.fixture
def debug_logger():
    """Enable debug logging for test duration"""
    logger = logging.getLogger('hbm4')
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    yield logger
    logger.setLevel(original_level)


@pytest.fixture
def quiet_logger():
    """Suppress logging during test"""
    logger = logging.getLogger('hbm4')
    original_level = logger.level
    logger.setLevel(logging.CRITICAL)
    yield logger
    logger.setLevel(original_level)


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
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "controller: marks tests as controller tests"
    )
    config.addinivalue_line(
        "markers", "dram: marks tests as DRAM model tests"
    )
    config.addinivalue_line(
        "markers", "dfi: marks tests as DFI interface tests"
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

        # Add markers based on directory
        if "controller" in item.nodeid:
            item.add_marker(pytest.mark.controller)
        if "dram" in item.nodeid:
            item.add_marker(pytest.mark.dram)
        if "dfi" in item.nodeid:
            item.add_marker(pytest.mark.dfi)


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


# =============================================================================
# Helper Functions
# =============================================================================

def create_test_address(channel: int, row: int = 0, col: int = 0,
                         pseudo_channel: int = 0, bank: int = 0) -> int:
    """Helper to create a test address with proper bit fields

    Args:
        channel: Channel ID (0-31)
        row: Row ID
        col: Column ID
        pseudo_channel: Pseudo-channel ID (0-1)
        bank: Bank ID (0-15)

    Returns:
        64-bit address with proper bit fields
    """
    addr = 0
    addr |= (channel & 0x1F) << 41  # Channel at bits 45:41
    addr |= (pseudo_channel & 0x1) << 40  # Pseudo-channel at bit 40
    addr |= (bank & 0xF) << 36  # Bank at bits 39:36
    addr |= (row & 0x7FFFF) << 16  # Row at bits 31:16
    addr |= (col & 0x3F) << 10  # Column at bits 15:10
    addr |= 0x8  # 8-byte aligned
    return addr


def submit_test_requests(controller: HBM4Controller,
                         count: int = 10,
                         start_addr: int = 0x1000) -> List[str]:
    """Helper to submit multiple test requests

    Args:
        controller: HBM4Controller instance
        count: Number of requests to submit
        start_addr: Starting address

    Returns:
        List of request IDs
    """
    request_ids = []
    for i in range(count):
        addr = start_addr + i * 0x1000
        req_id = controller.submit_request(
            addr=addr,
            is_read=(i % 2 == 0),
            qos_level=i % 16
        )
        if req_id is not None:
            request_ids.append(req_id)
    return request_ids


def run_simulation_cycles(controller: HBM4Controller,
                          cycles: int = 100) -> List[HBMResponse]:
    """Helper to run simulation for specified cycles

    Args:
        controller: HBM4Controller instance
        cycles: Number of cycles to simulate

    Returns:
        List of responses received
    """
    responses = []
    for _ in range(cycles):
        resp = controller.tick()
        responses.extend(resp)
    return responses


# Export helper functions for test modules
@pytest.fixture
def create_address() -> callable:
    """Fixture providing address creation helper"""
    return create_test_address


@pytest.fixture
def submit_requests() -> callable:
    """Fixture providing request submission helper"""
    return submit_test_requests


@pytest.fixture
def run_simulation() -> callable:
    """Fixture providing simulation runner helper"""
    return run_simulation_cycles


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