"""
Enhanced Pytest Configuration and Fixtures

Advanced pytest fixtures for enhanced testing coverage including:
1. Extended specification fixtures (all speed grades)
2. Multi-channel configurations (1, 8, 16, 32 channels)
3. High-stress test configurations
4. Error injection fixtures
5. Thermal simulation fixtures
6. Performance benchmarking fixtures
7. Custom markers for test categorization
8. Data generators for boundary testing
9. Statistical analysis helpers

This module extends the base conftest.py with additional fixtures
for comprehensive test coverage enhancement.

Usage:
    pytest tests/enhancement/ -v
    pytest tests/enhancement/ -v -m reliability
    pytest tests/enhancement/ -v -m endurance
"""

import pytest
import random
import time
import logging
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager

from model.dram.hbm4_spec import (
    HBM4Spec, create_hbm4_spec_from_speed_grade, HBM4_SPEED_GRADES
)
from model.dram.hbm4_bank_state_machine import (
    HBM4Command, HBM4BankTiming, create_hbm4_bank_state_machine,
    create_hbm4_bank_array
)
from model.dram.hbm4_channel_model import (
    HBM4Channel, HBM4ChannelArray, PseudoChannel,
    HBM4ChannelState, PseudoChannelState, BankGroupScheduler
)
from model.dram.ecc_crc import (
    HBM4ECC, HBM4CRC, HBM4DataIntegrity,
    HBM4ECCMode, HBM4CRCMode, ErrorType, ErrorTracker, ErrorCounter
)
from model.dram.lane_repair import (
    HBM4LaneRepairModel, RepairStatus, LaneFailureMode,
    LaneRepairEntry, LaneRepairMap
)
from model.dram.thermal_model import (
    LayeredThermalModel, create_hbm4_thermal_model, ThermalDVFSIntegration
)
from model.dram.phy_training import (
    PHYTrainingStateMachine, PHYInitializationStateMachine,
    HBM4PHYManager, TrainingResult, TrainingPhase
)

from model.controller.hbm4_controller import (
    HBM4Controller, ChannelState, HBM4ControllerStats
)
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import (
    HBM4QoSScheduler, QoSLevel, TrafficType, BankConflictTracker
)
from model.controller.hbm4_refresh_scheduler import (
    HBM4RefreshScheduler, RefreshMode, RefreshCommand
)
from model.controller.request import HBMRequest, HBMResponse, RequestState
from model.controller.queue import (
    ReadQueue, WriteQueue, PriorityQueue, QueueManager
)
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT

from sim.simulator import (
    HBMSimulator, SimulationConfig, TrafficPattern, TrafficGenerator
)


# ============================================================================
# Extended Specification Fixtures
# ============================================================================

@pytest.fixture
def hbm4_spec_all_speeds() -> Dict[str, HBM4Spec]:
    """All HBM4 speed grade specifications"""
    return {
        gbps: create_hbm4_spec_from_speed_grade(gbps)
        for gbps in HBM4_SPEED_GRADES
    }


@pytest.fixture(params=["8Gbps", "12Gbps", "16Gbps"])
def hbm4_spec_parametrized(request) -> HBM4Spec:
    """Parametrized HBM4 specification for all speed grades"""
    return create_hbm4_spec_from_speed_grade(request.param)


@pytest.fixture
def hbm4_spec_ultra_low_power() -> HBM4Spec:
    """Ultra-low power HBM4 specification"""
    spec = HBM4Spec()
    spec.data_rate_gtps = 6.4  # Lower speed for power savings
    return spec


@pytest.fixture
def hbm4_spec_max_performance() -> HBM4Spec:
    """Maximum performance HBM4 specification"""
    spec = create_hbm4_spec_from_speed_grade("16Gbps")
    spec.channels = 32
    spec.io_width = 2048
    return spec


# ============================================================================
# Extended Timing Fixtures
# ============================================================================

@pytest.fixture
def hbm4_timing_all_speeds() -> Dict[str, HBM4BankTiming]:
    """All speed grade timing parameters"""
    return {
        "8Gbps": HBM4BankTiming.for_speed_grade(8.0),
        "12Gbps": HBM4BankTiming.for_speed_grade(12.0),
        "16Gbps": HBM4BankTiming.for_speed_grade(16.0),
    }


@pytest.fixture
def hbm4_timing_minimal() -> HBM4BankTiming:
    """Minimal timing parameters (edge case)"""
    timing = HBM4BankTiming()
    # Use minimum valid values
    return timing


@pytest.fixture
def hbm4_timing_maximal() -> HBM4BankTiming:
    """Maximal timing parameters (slowest operation)"""
    timing = HBM4BankTiming()
    # Multiply by 2 for maximum margins
    timing.tRCD = int(timing.tRCD * 2)
    timing.tRP = int(timing.tRP * 2)
    timing.tRAS = int(timing.tRAS * 2)
    return timing


# ============================================================================
# Extended Channel Configurations
# ============================================================================

@pytest.fixture
def single_channel_config() -> HBMConfig:
    """Single channel configuration"""
    config = HBM3_DEFAULT.copy()
    config.stack_count = 1
    config.channels_per_stack = 1
    return config


@pytest.fixture
def half_channel_config() -> HBMConfig:
    """16-channel configuration (half)"""
    config = HBM4_DEFAULT.copy()
    config.channels = 16
    return config


@pytest.fixture
def full_channel_config() -> HBMConfig:
    """Full 32-channel configuration"""
    return HBM4_DEFAULT.copy()


@pytest.fixture
def all_channel_configs() -> List[HBMConfig]:
    """All channel configurations for parametrized testing"""
    return [
        single_channel_config(),
        half_channel_config(),
        full_channel_config(),
    ]


@pytest.fixture
def high_queue_depth_config() -> HBMConfig:
    """High queue depth configuration for stress testing"""
    config = HBM4_DEFAULT.copy()
    config.queue_depth = 256
    config.max_outstanding = 128
    return config


@pytest.fixture
def low_latency_config() -> HBMConfig:
    """Low latency configuration"""
    config = HBM4_DEFAULT.copy()
    config.timing.nCL = 12
    config.timing.nRCDRD = 12
    config.timing.nRCDWR = 12
    return config


# ============================================================================
# Controller Fixtures
# ============================================================================

@pytest.fixture
def hbm4_controller_single_channel() -> HBM4Controller:
    """Single-channel HBM4 controller"""
    spec = HBM4Spec()
    spec.channels = 1
    return HBM4Controller(spec=spec)


@pytest.fixture
def hbm4_controller_16_channel() -> HBM4Controller:
    """16-channel HBM4 controller"""
    spec = HBM4Spec()
    spec.channels = 16
    return HBM4Controller(spec=spec)


@pytest.fixture
def hbm4_controller_no_features() -> HBM4Controller:
    """HBM4 controller with all optional features disabled"""
    return HBM4Controller(
        enable_qos=False,
        enable_refresh=False,
        enable_ecc=False,
        enable_dfi=False
    )


@pytest.fixture
def hbm4_controller_high_performance() -> HBM4Controller:
    """High-performance HBM4 controller"""
    spec = create_hbm4_spec_from_speed_grade("16Gbps")
    spec.channels = 32
    return HBM4Controller(spec=spec)


@pytest.fixture
def hbm4_controller_all_speeds(request) -> HBM4Controller:
    """HBM4 controller for parametrized speed grades"""
    return HBM4Controller()


# ============================================================================
# Queue Fixtures
# ============================================================================

@pytest.fixture
def queue_depth_1() -> ReadQueue:
    """Queue with depth 1 (boundary)"""
    return ReadQueue(max_depth=1)


@pytest.fixture
def queue_depth_2() -> ReadQueue:
    """Queue with depth 2 (boundary)"""
    return ReadQueue(max_depth=2)


@pytest.fixture
def queue_depth_power_of_2() -> ReadQueue:
    """Queue with depth 128 (power of 2)"""
    return ReadQueue(max_depth=128)


@pytest.fixture
def queue_depth_large() -> ReadQueue:
    """Queue with large depth (10000)"""
    return ReadQueue(max_depth=10000)


@pytest.fixture
def queue_manager_high_depth() -> QueueManager:
    """High-depth queue manager"""
    return QueueManager.create(queue_depth=256)


@pytest.fixture
def write_queue_high_depth() -> WriteQueue:
    """High-depth write queue"""
    return WriteQueue(max_depth=256)


# ============================================================================
# Error Injection Fixtures
# ============================================================================

@pytest.fixture
def error_tracker() -> ErrorTracker:
    """Error tracker fixture"""
    return ErrorTracker()


@pytest.fixture
def error_tracker_with_errors() -> ErrorTracker:
    """Error tracker with pre-populated errors"""
    tracker = ErrorTracker()
    for i in range(100):
        tracker.log_error(ErrorType.ECC_CORRECTABLE, channel=i % 32)
    return tracker


@pytest.fixture
def ecc_engine() -> HBM4ECC:
    """ECC engine fixture"""
    return HBM4ECC(HBM4Spec())


@pytest.fixture
def crc_engine() -> HBM4CRC:
    """CRC engine fixture"""
    return HBM4CRC(HBM4Spec())


@pytest.fixture
def lane_repair_model() -> HBM4LaneRepairModel:
    """Lane repair model fixture"""
    return HBM4LaneRepairModel(HBM4Spec())


@pytest.fixture
def lane_repair_with_failures() -> HBM4LaneRepairModel:
    """Lane repair model with pre-existing failures"""
    repair = HBM4LaneRepairModel(HBM4Spec())
    for lane in range(4):
        repair.add_failure(
            channel_id=0,
            lane_id=lane,
            failure_mode=LaneFailureMode.STUCK_AT_0
        )
    return repair


# ============================================================================
# Thermal Fixtures
# ============================================================================

@pytest.fixture
def thermal_model() -> LayeredThermalModel:
    """Thermal model fixture"""
    return LayeredThermalModel()


@pytest.fixture
def thermal_model_hot() -> LayeredThermalModel:
    """Pre-heated thermal model"""
    thermal = LayeredThermalModel()
    for _ in range(1000):
        thermal.update_temperature(power_w=20.0, ambient_c=45.0, layer=thermal.layers[0])
    return thermal


@pytest.fixture
def thermal_model_cold() -> LayeredThermalModel:
    """Cold thermal model"""
    thermal = LayeredThermalModel()
    for _ in range(1000):
        thermal.update_temperature(power_w=0.1, ambient_c=0.0, layer=thermal.layers[0])
    return thermal


# ============================================================================
# Bank State Machine Fixtures
# ============================================================================

@pytest.fixture
def bank_state_machines_16() -> List:
    """16 bank state machines (full channel)"""
    return [create_hbm4_bank_state_machine(bank_id=i) for i in range(16)]


@pytest.fixture
def bank_state_machines_all_closed() -> List:
    """All 16 banks in closed state"""
    return [create_hbm4_bank_state_machine(bank_id=i) for i in range(16)]


# ============================================================================
# Address Decoder Fixtures
# ============================================================================

@pytest.fixture
def address_decoder_rcbc() -> HBM4AddressDecoder:
    """Address decoder with RCBC mapping"""
    return HBM4AddressDecoder(address_mapping="RCBC")


@pytest.fixture
def address_decoder_rbc() -> HBM4AddressDecoder:
    """Address decoder with RBC mapping"""
    return HBM4AddressDecoder(address_mapping="RBC")


@pytest.fixture
def address_decoder_all_mappings() -> List[HBM4AddressDecoder]:
    """All address mapping configurations"""
    return [
        HBM4AddressDecoder(address_mapping="RCBC"),
        HBM4AddressDecoder(address_mapping="RBC"),
        HBM4AddressDecoder(),  # Default
    ]


# ============================================================================
# Refresh Scheduler Fixtures
# ============================================================================

@pytest.fixture
def refresh_all_banks() -> HBM4RefreshScheduler:
    """Refresh scheduler in ALL_BANKS mode"""
    scheduler = HBM4RefreshScheduler()
    scheduler.mode = RefreshMode.ALL_BANKS
    return scheduler


@pytest.fixture
def refresh_per_bank() -> HBM4RefreshScheduler:
    """Refresh scheduler in PER_BANK mode"""
    scheduler = HBM4RefreshScheduler()
    scheduler.mode = RefreshMode.PER_BANK
    return scheduler


@pytest.fixture
def refresh_autonomous() -> HBM4RefreshScheduler:
    """Refresh scheduler in AUTONOMOUS mode"""
    scheduler = HBM4RefreshScheduler()
    scheduler.mode = RefreshMode.AUTONOMOUS
    return scheduler


# ============================================================================
# PHY Fixtures
# ============================================================================

@pytest.fixture
def phy_manager() -> HBM4PHYManager:
    """PHY manager fixture"""
    return HBM4PHYManager(HBM4Spec())


@pytest.fixture
def phy_training_sm() -> PHYTrainingStateMachine:
    """PHY training state machine fixture"""
    return PHYTrainingStateMachine(HBM4Spec())


@pytest.fixture
def phy_init_sm() -> PHYInitializationStateMachine:
    """PHY initialization state machine fixture"""
    return PHYInitializationStateMachine(HBM4Spec())


# ============================================================================
# Simulation Configuration Fixtures
# ============================================================================

@pytest.fixture
def short_sim_config() -> SimulationConfig:
    """Short simulation configuration (1K cycles)"""
    return SimulationConfig(
        simulation_time_us=1.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        hbm_config=HBM3_DEFAULT,
    )


@pytest.fixture
def medium_sim_config() -> SimulationConfig:
    """Medium simulation configuration (10K cycles)"""
    return SimulationConfig(
        simulation_time_us=10.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.7,
        hbm_config=HBM4_DEFAULT,
    )


@pytest.fixture
def long_sim_config() -> SimulationConfig:
    """Long simulation configuration (100K cycles)"""
    return SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.8,
        hbm_config=HBM4_DEFAULT,
    )


@pytest.fixture
def stress_sim_config() -> SimulationConfig:
    """Stress test simulation configuration"""
    return SimulationConfig(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=1.0,  # Maximum load
        hbm_config=HBM4_DEFAULT,
    )


@pytest.fixture
def endurance_sim_config() -> SimulationConfig:
    """Endurance test simulation configuration"""
    return SimulationConfig(
        simulation_time_us=500.0,
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.9,
        hbm_config=HBM4_DEFAULT,
    )


# ============================================================================
# Data Generator Fixtures
# ============================================================================

@pytest.fixture
def address_generator() -> Callable[[int], int]:
    """Address generator function factory"""
    def generate(channel: int, bank: int = 0, row: int = 0, col: int = 0) -> int:
        addr = 0
        addr |= (channel & 0x1F) << 41
        addr |= (bank & 0xF) << 36
        addr |= (row & 0x7FFFF) << 16
        addr |= (col & 0x3F) << 8
        addr |= 0x8  # Alignment
        return addr
    return generate


@pytest.fixture
def request_generator() -> Callable[[], HBMRequest]:
    """Request generator factory"""
    counter = [0]
    def generate() -> HBMRequest:
        counter[0] += 1
        return HBMRequest(
            request_id=f"gen_req_{counter[0]}",
            addr=(counter[0] % 32) << 41,
            length=64,
            is_read=(counter[0] % 2 == 0),
            qos=counter[0] % 16
        )
    return generate


@pytest.fixture
def boundary_addresses() -> List[int]:
    """Boundary addresses for testing"""
    return [
        0,  # Zero
        1,  # Minimum non-zero
        0xFF,  # Small boundary
        0x100,  # Power of 2
        0xFFFF,  # 16-bit boundary
        0x10000,  # 17-bit boundary
        (1 << 41) - 1,  # Channel max - 1
        1 << 41,  # Channel boundary
        (1 << 42) - 8,  # Max valid address
        0xFFFFFFFFFFFFFFFF,  # Max 64-bit
    ]


@pytest.fixture
def all_channel_addresses() -> List[int]:
    """All 32 channel addresses"""
    return [(ch << 41) | 0x8 for ch in range(32)]


@pytest.fixture
def all_bank_addresses() -> List[int]:
    """All bank addresses (16 banks x 32 channels)"""
    addrs = []
    for ch in range(32):
        for bank in range(16):
            addrs.append((ch << 41) | (bank << 36) | 0x8)
    return addrs


# ============================================================================
# Statistical Analysis Fixtures
# ============================================================================

@dataclass
class TestStatistics:
    """Test statistics collector"""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    durations: List[float] = field(default_factory=list)

    def record(self, passed: bool, duration: float):
        self.total_tests += 1
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        self.durations.append(duration)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_tests if self.total_tests > 0 else 0.0

    @property
    def avg_duration(self) -> float:
        return sum(self.durations) / len(self.durations) if self.durations else 0.0


@pytest.fixture
def test_stats() -> TestStatistics:
    """Test statistics collector"""
    return TestStatistics()


# ============================================================================
# Performance Timer Fixtures
# ============================================================================

class EnhancedPerformanceTimer:
    """Enhanced performance timer with pause/resume"""

    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed: float = 0.0
        self.paused_time: float = 0.0
        self._paused_at: float = 0.0
        self._is_paused: bool = False

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        if self._is_paused:
            self.paused_time += time.perf_counter() - self._paused_at
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time - self.paused_time

    def pause(self):
        if not self._is_paused:
            self._paused_at = time.perf_counter()
            self._is_paused = True

    def resume(self):
        if self._is_paused:
            self.paused_time += time.perf_counter() - self._paused_at
            self._is_paused = False

    @property
    def elapsed_ms(self) -> float:
        return self.elapsed * 1000.0

    @property
    def elapsed_s(self) -> float:
        return self.elapsed


@pytest.fixture
def enhanced_timer():
    """Enhanced performance timer fixture"""
    return EnhancedPerformanceTimer


# ============================================================================
# Context Manager Fixtures
# ============================================================================

@contextmanager
def temporary_seed(seed: int):
    """Temporarily set random seed"""
    original = random.getstate()
    random.seed(seed)
    try:
        yield
    finally:
        random.setstate(original)


@pytest.fixture
def fixed_random_seed():
    """Fixture for fixed random seed"""
    return temporary_seed


# ============================================================================
# Custom Pytest Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "reliability: reliability and endurance tests"
    )
    config.addinivalue_line(
        "markers", "endurance: long-duration endurance tests"
    )
    config.addinivalue_line(
        "markers", "boundary: boundary condition tests"
    )
    config.addinivalue_line(
        "markers", "corner: corner case tests"
    )
    config.addinivalue_line(
        "markers", "thermal: thermal-related tests"
    )
    config.addinivalue_line(
        "markers", "voltage: voltage margin tests"
    )
    config.addinivalue_line(
        "markers", "error_injection: error injection tests"
    )
    config.addinivalue_line(
        "markers", "lane_repair: lane repair tests"
    )
    config.addinivalue_line(
        "markers", "refresh: refresh operation tests"
    )
    config.addinivalue_line(
        "markers", "ecc: ECC/CRC tests"
    )
    config.addinivalue_line(
        "markers", "long_running: long-running tests (may be slow)"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on test names"""
    for item in items:
        # Auto-mark by test class
        if "Reliability" in item.nodeid or "Endurance" in item.nodeid:
            item.add_marker(pytest.mark.reliability)
            item.add_marker(pytest.mark.endurance)

        if "Boundary" in item.nodeid:
            item.add_marker(pytest.mark.boundary)

        if "Thermal" in item.nodeid:
            item.add_marker(pytest.mark.thermal)

        if "Voltage" in item.nodeid:
            item.add_marker(pytest.mark.voltage)

        if "Error" in item.nodeid:
            item.add_marker(pytest.mark.error_injection)

        if "LaneRepair" in item.nodeid:
            item.add_marker(pytest.mark.lane_repair)

        if "Refresh" in item.nodeid:
            item.add_marker(pytest.mark.refresh)

        if "ECC" in item.nodeid or "CRC" in item.nodeid or "DataIntegrity" in item.nodeid:
            item.add_marker(pytest.mark.ecc)


# ============================================================================
# Helper Functions
# ============================================================================

def create_boundary_addresses() -> List[int]:
    """Generate boundary test addresses"""
    return [
        0,  # Zero
        1 << 41,  # Channel boundary
        (1 << 42) - 8,  # Max address
        0xFFFF << 16,  # Row max
        63 << 8,  # Column max
    ]


def create_stress_traffic_pattern(channels: int = 32) -> List[Tuple[int, bool]]:
    """Generate stress traffic pattern"""
    pattern = []
    for i in range(channels * 100):
        ch = i % channels
        is_read = (i % 3) != 0
        pattern.append((ch, is_read))
    return pattern


def measure_error_rate(tracker: ErrorTracker, operations: int) -> float:
    """Measure error rate from tracker"""
    return tracker.get_error_rate(total_operations=operations)


# ============================================================================
# Export Helpers
# ============================================================================

@pytest.fixture
def create_boundary_addrs() -> callable:
    """Fixture providing boundary address generator"""
    return create_boundary_addresses


@pytest.fixture
def create_stress_pattern() -> callable:
    """Fixture providing stress pattern generator"""
    return create_stress_traffic_pattern


@pytest.fixture
def measure_error_rate_fixture() -> callable:
    """Fixture providing error rate measurement"""
    return measure_error_rate
