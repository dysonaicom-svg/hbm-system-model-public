"""
HBM4 Power Consumption Model

Estimates power consumption based on:
- Active/Idle states
- Read/Write operations
- Refresh operations
- Temperature and process corners

Reference:
- JEDEC JESD270-4A HBM4 specification
- Synopsys DesignWare HBM4 Power Analysis
- DRAM power models from academic research
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


class PowerState(Enum):
    """Power/operational states"""
    ACTIVE = "active"       # ACT command active
    READ = "read"           # Read operation
    WRITE = "write"         # Write operation
    REFRESH = "refresh"     # Refresh operation
    IDLE = "idle"           # Bank idle, powered up
    SELF_REFRESH = "self_refresh"  # Self-refresh mode
    POWER_DOWN = "power_down"      # Power-down mode


@dataclass
class PowerParameters:
    """Power consumption parameters (in mW unless noted)

    Based on JEDEC HBM4 specification and vendor data sheets.
    Values are typical for HBM4 at 8 GT/s, 1.1V VDDQ, 0.95V VDDQ2.
    """
    # === Active Power (per channel) ===
    active_power_ma: float = 350.0  # Active current (mA) - row open
    read_power_ma: float = 450.0    # Read operation power (mA)
    write_power_ma: float = 420.0   # Write operation power (mA)

    # === Idle/Standby Power (per channel) ===
    idle_power_ma: float = 50.0      # Idle (CK enabled) power (mA)
    standby_power_ma: float = 15.0   # CKE low standby (mA)

    # === Refresh Power ===
    refresh_power_ma: float = 380.0   # Refresh operation power (mA)
    refresh_cycle_ns: float = 7800.0  # tREFI in ns (7.8 us)

    # === Self-Refresh Power ===
    self_refresh_power_ma: float = 8.0  # Self-refresh mode (mA)

    # === Power-Down Power ===
    power_down_power_ma: float = 5.0   # Power-down mode (mA)

    # === Voltage Rails ===
    vddq_voltage: float = 1.1          # VDDQ voltage (V)
    vddq2_voltage: float = 0.95       # VDDQ2 voltage (V)
    vpp_voltage: float = 2.5          # VPP voltage (V)

    @property
    def active_power_mw(self) -> float:
        """Active power in mW"""
        return self.active_power_ma * self.vddq_voltage

    @property
    def read_power_mw(self) -> float:
        """Read power in mW"""
        return self.read_power_ma * self.vddq_voltage

    @property
    def write_power_mw(self) -> float:
        """Write power in mW"""
        return self.write_power_ma * self.vddq_voltage

    @property
    def idle_power_mw(self) -> float:
        """Idle power in mW"""
        return self.idle_power_ma * self.vddq_voltage

    @property
    def refresh_power_mw(self) -> float:
        """Refresh power in mW"""
        return self.refresh_power_ma * self.vddq_voltage


@dataclass
class ChannelPower:
    """Per-channel power tracking"""
    channel_id: int
    params: PowerParameters = field(default_factory=PowerParameters)

    # State tracking
    state: PowerState = PowerState.IDLE
    active_time_cycles: int = 0
    read_time_cycles: int = 0
    write_time_cycles: int = 0
    refresh_time_cycles: int = 0
    idle_time_cycles: int = 0
    self_refresh_cycles: int = 0

    # Energy counters (pJ)
    total_energy_pj: float = 0.0

    def update_energy(self, cycles: int, state: PowerState):
        """Update energy consumption for cycles spent in state"""
        power_ma = self._get_power_for_state(state)
        power_mw = power_ma * self.params.vddq_voltage
        power_w = power_mw / 1000.0

        # Assuming 125ps cycle time (8 GT/s)
        time_s = cycles * 125e-12
        energy_j = power_w * time_s
        self.total_energy_pj += energy_j * 1e12

        # Update state counters
        if state == PowerState.ACTIVE:
            self.active_time_cycles += cycles
        elif state == PowerState.READ:
            self.read_time_cycles += cycles
        elif state == PowerState.WRITE:
            self.write_time_cycles += cycles
        elif state == PowerState.REFRESH:
            self.refresh_time_cycles += cycles
        elif state == PowerState.IDLE:
            self.idle_time_cycles += cycles
        elif state == PowerState.SELF_REFRESH:
            self.self_refresh_cycles += cycles

    def _get_power_for_state(self, state: PowerState) -> float:
        """Get current (mA) for a given state"""
        power_map = {
            PowerState.ACTIVE: self.params.active_power_ma,
            PowerState.READ: self.params.read_power_ma,
            PowerState.WRITE: self.params.write_power_ma,
            PowerState.REFRESH: self.params.refresh_power_ma,
            PowerState.IDLE: self.params.idle_power_ma,
            PowerState.SELF_REFRESH: self.params.self_refresh_power_ma,
            PowerState.POWER_DOWN: self.params.power_down_power_ma,
        }
        return power_map.get(state, self.params.idle_power_ma)

    def get_average_power_mw(self, total_cycles: int) -> float:
        """Calculate average power over total_cycles"""
        if total_cycles == 0:
            return 0.0
        energy_nj = self.total_energy_pj / 1e6  # Convert pJ to nJ
        time_s = total_cycles * 125e-12
        power_w = (energy_nj * 1e-9) / time_s
        return power_w * 1000.0  # Convert to mW


@dataclass
class HBM4PowerEstimator:
    """HBM4 Power Consumption Estimator

    Tracks power consumption across all 32 channels with support for:
    - Per-channel power breakdown
    - State-based power calculation
    - Average and peak power estimation
    - Thermal modeling
    """
    num_channels: int = 32
    params: PowerParameters = field(default_factory=PowerParameters)

    # Per-channel tracking
    channels: List[ChannelPower] = field(default_factory=list)

    # Global tracking
    current_cycle: int = 0
    peak_power_mw: float = 0.0

    # Refresh tracking
    refresh_interval_cycles: int = 62400  # tREFI @ 8 GT/s (7.8 us / 125 ps)
    cycles_since_refresh: int = 0

    def __post_init__(self):
        """Initialize channel power trackers"""
        if not self.channels:
            self.channels = [
                ChannelPower(channel_id=i, params=self.params)
                for i in range(self.num_channels)
            ]

    def tick(self, cycles: int = 1):
        """Advance time and update power counters

        Args:
            cycles: Number of cycles to advance
        """
        self.current_cycle += cycles
        self.cycles_since_refresh += cycles

        # Check for refresh
        if self.cycles_since_refresh >= self.refresh_interval_cycles:
            self._perform_refresh()

    def _perform_refresh(self):
        """Execute refresh on all channels"""
        self.cycles_since_refresh = 0
        # Refresh takes nRFC cycles (~180 cycles)
        # For power estimation, we attribute refresh energy to affected channels
        for ch in self.channels:
            ch.update_energy(1, PowerState.REFRESH)

    def set_channel_state(self, channel_id: int, state: PowerState, cycles: int = 1):
        """Set channel state for power calculation

        Args:
            channel_id: Channel index (0-31)
            state: New power state
            cycles: Duration in cycles
        """
        if 0 <= channel_id < self.num_channels:
            ch = self.channels[channel_id]
            ch.update_energy(cycles, state)
            ch.state = state

            # Track peak power
            current_power = ch._get_power_for_state(state) * self.params.vddq_voltage
            if current_power > self.peak_power_mw:
                self.peak_power_mw = current_power

    def set_all_channels_state(self, state: PowerState, cycles: int = 1):
        """Set all channels to the same state

        Args:
            state: New power state
            cycles: Duration in cycles
        """
        for ch in self.channels:
            ch.update_energy(cycles, state)
            ch.state = state

    def get_total_power_mw(self) -> float:
        """Get total power across all channels"""
        return sum(
            ch._get_power_for_state(ch.state) * self.params.vddq_voltage
            for ch in self.channels
        )

    def get_average_power_mw(self) -> float:
        """Get average power over simulation time"""
        if self.current_cycle == 0:
            return 0.0
        total_energy_pj = sum(ch.total_energy_pj for ch in self.channels)
        time_s = self.current_cycle * 125e-12
        power_w = (total_energy_pj * 1e-12) / time_s
        return power_w * 1000.0

    def get_channel_power_mw(self, channel_id: int) -> float:
        """Get power for specific channel"""
        if 0 <= channel_id < self.num_channels:
            ch = self.channels[channel_id]
            return ch._get_power_for_state(ch.state) * self.params.vddq_voltage
        return 0.0

    def get_energy_breakdown_pj(self) -> Dict[str, float]:
        """Get energy breakdown by state type

        Returns:
            Dictionary with energy (pJ) per state type
        """
        breakdown = {
            "active": 0.0,
            "read": 0.0,
            "write": 0.0,
            "refresh": 0.0,
            "idle": 0.0,
            "self_refresh": 0.0,
        }

        for ch in self.channels:
            breakdown["active"] += ch.active_time_cycles * 125e-12 * self.params.active_power_mw * 1e12
            breakdown["read"] += ch.read_time_cycles * 125e-12 * self.params.read_power_mw * 1e12
            breakdown["write"] += ch.write_time_cycles * 125e-12 * self.params.write_power_mw * 1e12
            breakdown["refresh"] += ch.refresh_time_cycles * 125e-12 * self.params.refresh_power_mw * 1e12
            breakdown["idle"] += ch.idle_time_cycles * 125e-12 * self.params.idle_power_mw * 1e12
            breakdown["self_refresh"] += ch.self_refresh_cycles * 125e-12 * self.params.self_refresh_power_ma * self.params.vddq_voltage * 1e12

        return breakdown

    def get_bandwidth_efficiency(self, active_cycles: int, total_cycles: int) -> float:
        """Calculate bandwidth efficiency

        Args:
            active_cycles: Cycles spent in read/write
            total_cycles: Total simulation cycles

        Returns:
            Efficiency (0-1)
        """
        if total_cycles == 0:
            return 0.0
        return active_cycles / total_cycles

    def estimate_thermal(self, ambient_temp_c: float = 45.0) -> Dict[str, float]:
        """Estimate thermal characteristics

        Args:
            ambient_temp_c: Ambient temperature in Celsius

        Returns:
            Dictionary with thermal estimates
        """
        avg_power_w = self.get_average_power_mw() / 1000.0
        theta_ja = 0.5  # Thermal resistance (C/W) - package dependent

        # Junction temperature
        t_junction = ambient_temp_c + (avg_power_w * theta_ja)

        return {
            "ambient_temp_c": ambient_temp_c,
            "junction_temp_c": t_junction,
            "average_power_w": avg_power_w,
            "theta_ja": theta_ja,
            "peak_power_w": self.peak_power_mw / 1000.0,
        }

    def get_summary(self) -> Dict:
        """Get power estimation summary

        Returns:
            Dictionary with complete power statistics
        """
        total_cycles = self.current_cycle if self.current_cycle > 0 else 1
        energy_breakdown = self.get_energy_breakdown_pj()
        total_energy = sum(energy_breakdown.values())

        return {
            "num_channels": self.num_channels,
            "current_cycle": self.current_cycle,
            "total_power_mw": self.get_total_power_mw(),
            "average_power_mw": self.get_average_power_mw(),
            "peak_power_mw": self.peak_power_mw,
            "total_energy_pj": total_energy,
            "energy_breakdown_pj": energy_breakdown,
            "efficiency": {
                "active_ratio": sum(ch.active_time_cycles for ch in self.channels) / (total_cycles * self.num_channels),
                "read_ratio": sum(ch.read_time_cycles for ch in self.channels) / (total_cycles * self.num_channels),
                "write_ratio": sum(ch.write_time_cycles for ch in self.channels) / (total_cycles * self.num_channels),
                "idle_ratio": sum(ch.idle_time_cycles for ch in self.channels) / (total_cycles * self.num_channels),
            },
            "thermal": self.estimate_thermal(),
        }

    def reset(self):
        """Reset power counters"""
        for ch in self.channels:
            ch.active_time_cycles = 0
            ch.read_time_cycles = 0
            ch.write_time_cycles = 0
            ch.refresh_time_cycles = 0
            ch.idle_time_cycles = 0
            ch.self_refresh_cycles = 0
            ch.total_energy_pj = 0.0
            ch.state = PowerState.IDLE
        self.current_cycle = 0
        self.peak_power_mw = 0.0
        self.cycles_since_refresh = 0

    def __repr__(self) -> str:
        return (f"HBM4PowerEstimator(channels={self.num_channels}, "
                f"avg_power={self.get_average_power_mw():.1f}mW, "
                f"peak_power={self.peak_power_mw:.1f}mW)")


# Default power estimator
DEFAULT_POWER_ESTIMATOR = HBM4PowerEstimator()

# Speed grade power presets
POWER_PRESETS = {
    "8Gbps": PowerParameters(),
    "12Gbps": PowerParameters(
        active_power_ma=420.0,
        read_power_ma=540.0,
        write_power_ma=500.0,
        vddq_voltage=1.15,
    ),
    "16Gbps": PowerParameters(
        active_power_ma=500.0,
        read_power_ma=650.0,
        write_power_ma=600.0,
        vddq_voltage=1.2,
    ),
}


def create_power_estimator(speed_grade: str = "8Gbps", num_channels: int = 32) -> HBM4PowerEstimator:
    """Create power estimator with speed grade parameters

    Args:
        speed_grade: One of "8Gbps", "12Gbps", "16Gbps"
        num_channels: Number of channels (default 32 for HBM4)

    Returns:
        HBM4PowerEstimator configured for speed grade
    """
    params = POWER_PRESETS.get(speed_grade, POWER_PRESETS["8Gbps"])
    return HBM4PowerEstimator(num_channels=num_channels, params=params)