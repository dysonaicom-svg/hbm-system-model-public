"""
Power Model Regression Tests (15+ tests)

Tests for power estimation and power model validation including:
- Dynamic power estimation
- Static power estimation
- Power per operation type
- Power scaling with activity
- Thermal considerations
- Power mode transitions
"""

import pytest
from typing import Dict, List, Optional
import math

from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest
from model.dram.dram_model import DRAMModel
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern


# ============================================================================
# Power Model Constants
# ============================================================================

# HBM3 Power Parameters (approximate, based on JEDEC spec)
class PowerParams:
    """HBM3 power parameters"""
    # Voltage (V)
    VDD = 1.1  # Core voltage
    VDDQ = 0.5  # I/O voltage

    # Current (mA) per bank state
    IDD0 = 200  # Active
    IDD2P = 20  # Precharge power-down
    IDD2N = 100  # Precharge standby
    IDD3N = 120  # Active standby
    IDD4R = 300  # Read
    IDD4W = 280  # Write
    IDD5 = 400  # Refresh

    # Per-bit currents
    IDD0_BIT = 0.5  # mA per bit in active
    IDD4R_BIT = 0.8  # mA per bit in read

    # Leakage
    ILEAK = 0.1  # mA per bank

    # Frequency factor (normalized to 1.6 GHz)
    FREQ_FACTOR_BASE = 1.0


# ============================================================================
# Power Estimation Models
# ============================================================================

def estimate_dynamic_power_per_cycle(
    num_active_banks: int,
    bus_width_bits: int,
    freq_mhz: float,
    activity_factor: float = 0.5,
) -> float:
    """
    Estimate dynamic power consumption per cycle.

    Args:
        num_active_banks: Number of active banks
        bus_width_bits: Bus width in bits
        freq_mhz: Frequency in MHz
        activity_factor: Activity factor (0-1)

    Returns:
        Power in milliwatts
    """
    # P = C * V^2 * f * AF
    # C estimated as: C_bit * bus_width + C_bank * num_banks
    C_bit = 0.5  # pF per bit
    C_bank = 10  # pF per bank

    C_total = (C_bit * bus_width_bits + C_bank * num_active_banks) * 1e-12  # Convert to F
    P_dynamic = C_total * (PowerParams.VDD ** 2) * (freq_mhz * 1e6) * activity_factor

    return P_dynamic * 1000  # Convert to mW


def estimate_static_power(num_banks: int, temp_c: float = 55.0) -> float:
    """
    Estimate static/leakage power.

    Args:
        num_banks: Number of banks
        temp_c: Temperature in Celsius

    Returns:
        Power in milliwatts
    """
    # Leakage increases exponentially with temperature
    temp_factor = math.exp(0.1 * (temp_c - 25) / 10)
    P_leakage = num_banks * PowerParams.ILEAK * PowerParams.VDD * temp_factor
    return P_leakage


def estimate_read_power(
    bus_width_bits: int,
    burst_length: int,
    freq_mhz: float,
) -> float:
    """
    Estimate power for a read operation.

    Args:
        bus_width_bits: Bus width in bits
        burst_length: Burst length in beats
        freq_mhz: Frequency in MHz

    Returns:
        Energy in picojoules
    """
    # E = P * t = (C * V^2) * (burst_length / freq)
    C_total = bus_width_bits * 0.5 * 1e-12  # pF
    E_read = C_total * (PowerParams.VDDQ ** 2) * burst_length
    return E_read * 1000  # Convert to pJ


def estimate_write_power(
    bus_width_bits: int,
    burst_length: int,
    freq_mhz: float,
) -> float:
    """
    Estimate power for a write operation.

    Args:
        bus_width_bits: Bus width in bits
        burst_length: Burst length in beats
        freq_mhz: Frequency in MHz

    Returns:
        Energy in picojoules
    """
    C_total = bus_width_bits * 0.4 * 1e-12  # Slightly lower than read
    E_write = C_total * (PowerParams.VDDQ ** 2) * burst_length
    return E_write * 1000  # Convert to pJ


def estimate_refresh_power(
    num_banks: int,
    refresh_cycles: int,
    total_cycles: int,
) -> float:
    """
    Estimate average power during refresh.

    Args:
        num_banks: Number of banks
        refresh_cycles: Number of cycles spent in refresh
        total_cycles: Total simulation cycles

    Returns:
        Average power in milliwatts
    """
    if total_cycles == 0:
        return 0.0

    P_refresh_peak = num_banks * PowerParams.IDD5 * PowerParams.VDD * 1e-3  # mW
    refresh_fraction = refresh_cycles / total_cycles
    return P_refresh_peak * refresh_fraction


# ============================================================================
# Power Model Tests
# ============================================================================

class TestPowerModelBasics:
    """Basic power model tests"""

    def test_dynamic_power_calculation(self):
        """Test dynamic power calculation"""
        P = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=0.5,
        )
        assert P > 0
        assert P < 1000  # Sanity check

    def test_static_power_calculation(self):
        """Test static power calculation"""
        P = estimate_static_power(num_banks=16, temp_c=55.0)
        assert P > 0
        assert P < 10  # Leakage should be small

    def test_static_power_temperature_scaling(self):
        """Test static power scales with temperature"""
        P_low = estimate_static_power(num_banks=16, temp_c=25.0)
        P_high = estimate_static_power(num_banks=16, temp_c=85.0)
        assert P_high > P_low  # Higher temp = higher leakage

    def test_read_power_calculation(self):
        """Test read power calculation"""
        E = estimate_read_power(
            bus_width_bits=128,
            burst_length=4,
            freq_mhz=1600,
        )
        assert E > 0
        assert E < 10000  # Sanity check

    def test_write_power_calculation(self):
        """Test write power calculation"""
        E = estimate_write_power(
            bus_width_bits=128,
            burst_length=4,
            freq_mhz=1600,
        )
        assert E > 0
        assert E < 10000  # Sanity check


# ============================================================================
# Power Scaling Tests
# ============================================================================

class TestPowerScaling:
    """Power scaling tests"""

    def test_power_scales_with_frequency(self):
        """Test power scales linearly with frequency"""
        P_800 = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=800,
            activity_factor=0.5,
        )
        P_1600 = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=0.5,
        )
        # 2x frequency should give ~2x power
        assert 1.8 < (P_1600 / P_800) < 2.2

    def test_power_scales_with_bus_width(self):
        """Test power scales with bus width"""
        P_64 = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=64,
            freq_mhz=1600,
            activity_factor=0.5,
        )
        P_128 = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=0.5,
        )
        # Power scales with bus width, but not linearly due to fixed bank overhead
        # Bank capacitance adds ~40-50% overhead for 2x width
        ratio = P_128 / P_64
        assert 1.3 < ratio < 1.6  # Expected: ~1.44

    def test_power_scales_with_active_banks(self):
        """Test power scales with number of active banks"""
        P_2 = estimate_dynamic_power_per_cycle(
            num_active_banks=2,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=0.5,
        )
        P_4 = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=0.5,
        )
        assert P_4 > P_2

    def test_power_scales_with_activity_factor(self):
        """Test power scales with activity factor"""
        P_low = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=0.25,
        )
        P_high = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=1.0,
        )
        # 4x activity should give ~4x power
        assert 3.5 < (P_high / P_low) < 4.5


# ============================================================================
# Power per Operation Tests
# ============================================================================

class TestPowerPerOperation:
    """Power per operation tests"""

    def test_read_vs_write_power(self):
        """Test read power vs write power"""
        E_read = estimate_read_power(bus_width_bits=128, burst_length=4, freq_mhz=1600)
        E_write = estimate_write_power(bus_width_bits=128, burst_length=4, freq_mhz=1600)
        # Read typically slightly higher due to sense amps
        assert E_read > 0
        assert E_write > 0
        assert E_read > E_write * 0.9
        assert E_read < E_write * 1.3

    def test_burst_length_affects_energy(self):
        """Test burst length affects energy"""
        E_4 = estimate_read_power(bus_width_bits=128, burst_length=4, freq_mhz=1600)
        E_8 = estimate_read_power(bus_width_bits=128, burst_length=8, freq_mhz=1600)
        assert E_8 > E_4

    def test_refresh_power_fraction(self):
        """Test refresh power is a small fraction of total"""
        P_refresh = estimate_refresh_power(
            num_banks=16,
            refresh_cycles=100,
            total_cycles=10000,
        )
        P_active = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=1.0,
        )
        # Refresh should be < 20% of active power
        assert P_refresh < P_active * 0.2


# ============================================================================
# Power Estimation Integration Tests
# ============================================================================

class TestPowerEstimationIntegration:
    """Integration tests for power estimation"""

    def test_power_model_with_simulation(self):
        """Test power model integrated with simulation"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # Estimate power based on simulation stats
        P_dynamic = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=stats.efficiency,
        )
        P_static = estimate_static_power(num_banks=16, temp_c=55.0)

        assert P_dynamic > 0
        assert P_static > 0

    def test_power_with_sequential_traffic(self):
        """Test power with sequential traffic (high efficiency)"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            read_ratio=1.0,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # Sequential should have higher efficiency
        P_dynamic = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=max(stats.efficiency, 0.1),
        )
        assert P_dynamic > 0

    def test_power_with_random_traffic(self):
        """Test power with random traffic (lower efficiency)"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        P_dynamic = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=max(stats.efficiency, 0.1),
        )
        assert P_dynamic > 0


# ============================================================================
# Power Validation Tests
# ============================================================================

class TestPowerValidation:
    """Power validation tests against expected ranges"""

    def test_dynamic_power_in_valid_range(self):
        """Test dynamic power is within expected range"""
        P = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=1.0,
        )
        # HBM3 dynamic power per stack should be < 500mW typical
        assert 0 < P < 500

    def test_static_power_in_valid_range(self):
        """Test static power is within expected range"""
        P = estimate_static_power(num_banks=16, temp_c=55.0)
        # HBM3 leakage per stack should be < 10mW
        assert 0 < P < 10

    def test_read_energy_in_valid_range(self):
        """Test read energy is within expected range"""
        E = estimate_read_power(bus_width_bits=128, burst_length=4, freq_mhz=1600)
        # HBM3 read energy should be < 5000 pJ
        assert 0 < E < 5000

    def test_write_energy_in_valid_range(self):
        """Test write energy is within expected range"""
        E = estimate_write_power(bus_width_bits=128, burst_length=4, freq_mhz=1600)
        # HBM3 write energy should be < 5000 pJ
        assert 0 < E < 5000

    def test_refresh_power_in_valid_range(self):
        """Test refresh power is within expected range"""
        P = estimate_refresh_power(
            num_banks=16,
            refresh_cycles=100,
            total_cycles=1000,
        )
        # Refresh power should be reasonable
        assert 0 <= P < 100


# ============================================================================
# Power Regression Tests
# ============================================================================

class TestPowerRegression:
    """Power regression tests to catch performance degradation"""

    def test_power_baseline_sequential(self):
        """Establish power baseline for sequential traffic"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            read_ratio=1.0,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # Calculate estimated power
        P_total = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=max(stats.efficiency, 0.1),
        ) + estimate_static_power(num_banks=16, temp_c=55.0)

        # Should be within reasonable range
        assert 0 < P_total < 600

    def test_power_baseline_random(self):
        """Establish power baseline for random traffic"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        P_total = estimate_dynamic_power_per_cycle(
            num_active_banks=4,
            bus_width_bits=128,
            freq_mhz=1600,
            activity_factor=max(stats.efficiency, 0.1),
        ) + estimate_static_power(num_banks=16, temp_c=55.0)

        assert 0 < P_total < 600

    def test_power_consistency_across_runs(self):
        """Test power estimation is consistent across runs with same seed"""
        power_values = []
        for seed in [42, 42, 42]:
            config = SimulationConfig(
                simulation_time_us=30.0,
                traffic_pattern=TrafficPattern.SEQUENTIAL,
                request_rate=0.5,
                seed=seed,
            )
            sim = HBMSimulator(config)
            stats = sim.run()
            P = estimate_dynamic_power_per_cycle(
                num_active_banks=4,
                bus_width_bits=128,
                freq_mhz=1600,
                activity_factor=max(stats.efficiency, 0.1),
            )
            power_values.append(P)

        # Same seed should give same efficiency, hence same power
        assert power_values[0] == power_values[1] == power_values[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])