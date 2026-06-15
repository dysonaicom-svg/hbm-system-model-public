"""
HBM4 Thermal Model

Provides thermal modeling for the HBM4 logic base die components.

Key features:
- Hotspot proxies (controller cluster, D2D PHY, TSV PHY, ECC/RAS, clocking)
- Thermal resistance modeling (R_theta_jc, R_theta_ca)
- Thermal throttling policy with temperature thresholds
- PDN voltage operating points
- Temperature tracking per component
- Integration with PowerEstimator for dynamic power

Based on:
- JEDEC JESD270-4A HBM4 specification
- Hotspot thermal simulation models
- Synopsys HBM4 Controller IP thermal data
- Multi-agent research findings (2026-06-15)

Thermal model overview:
    Power consumption from each component (P_i)
        |
        v
    [Thermal Resistance R_th] --> Temperature rise (delta_T = P * R_th)
        |
        v
    [Heat spreading in base die]
        |
        v
    [Package thermal resistance]
        |
        v
    [Ambient temperature]

Thermal throttling:
- Warning threshold: ~85°C (begin monitoring)
- Throttle threshold: ~95°C (reduce frequency/voltage)
- Critical threshold: ~105°C (emergency throttling)
- Shutdown threshold: ~110°C (thermal shutdown)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


class ThrottleLevel(Enum):
    """Thermal throttling levels"""
    NONE = "none"           # Normal operation
    WARNING = "warning"     # Temperature approaching throttle
    THROTTLE = "throttle"  # Frequency/voltage reduction active
    CRITICAL = "critical"   # Aggressive throttling
    SHUTDOWN = "shutdown"  # Emergency thermal shutdown


class PDNVoltageMode(Enum):
    """PDN voltage operating points"""
    NOMINAL = "nominal"      # 0.9V nominal
    PERFORMANCE = "perf"     # 1.0V boosted performance
    LOW_POWER = "low_pwr"    # 0.8V reduced power
    ULTRA_LOW = "ultra_low"  # 0.65V ultra low power


@dataclass
class TemperatureThresholds:
    """Temperature thresholds for thermal management (in Celsius)"""
    warning: float = 85.0      # Begin monitoring
    throttle: float = 95.0      # Start throttling
    critical: float = 105.0     # Aggressive throttling
    shutdown: float = 110.0     # Emergency shutdown

    def get_throttle_level(self, temperature: float) -> ThrottleLevel:
        """Determine throttle level based on temperature"""
        if temperature >= self.shutdown:
            return ThrottleLevel.SHUTDOWN
        elif temperature >= self.critical:
            return ThrottleLevel.CRITICAL
        elif temperature >= self.throttle:
            return ThrottleLevel.THROTTLE
        elif temperature >= self.warning:
            return ThrottleLevel.WARNING
        return ThrottleLevel.NONE


@dataclass
class ThermalResistance:
    """Thermal resistance parameters (in °C/W)"""
    r_jc: float = 0.5      # Junction-to-case resistance
    r_jb: float = 1.0      # Junction-to-board resistance
    r_ca: float = 10.0    # Case-to-ambient resistance (package level)
    r_sp: float = 2.0     # Spreading resistance within die

    @property
    def total(self) -> float:
        """Total thermal resistance"""
        return self.r_jc + self.r_jb + self.r_ca

    def get_temperature_rise(self, power_mw: float) -> float:
        """Calculate temperature rise from power dissipation
        
        Args:
            power_mw: Power in milliwatts
            
        Returns:
            Temperature rise in Celsius
        """
        return power_mw * self.total / 1000.0


@dataclass
class ComponentTemperatures:
    """Temperature readings for each component (in Celsius)"""
    timestamp_ns: int = 0
    ambient: float = 25.0          # Ambient temperature
    case: float = 25.0              # Package case temperature
    die: float = 25.0               # Die temperature
    controller_cluster: float = 25.0
    d2d_phy: float = 25.0
    tsv_phy: float = 25.0
    ecc_ras: float = 25.0
    clocking: float = 25.0
    phy_interface: float = 25.0

    @property
    def max_temperature(self) -> float:
        """Maximum temperature across all components"""
        return max(
            self.die,
            self.controller_cluster,
            self.d2d_phy,
            self.tsv_phy,
            self.ecc_ras,
            self.clocking,
            self.phy_interface,
        )

    @property
    def average_temperature(self) -> float:
        """Average temperature across all components"""
        return (
            self.controller_cluster +
            self.d2d_phy +
            self.tsv_phy +
            self.ecc_ras +
            self.clocking +
            self.phy_interface
        ) / 6.0


@dataclass
class HotspotConfig:
    """Configuration for each hotspot component"""
    # Thermal resistance from junction to die surface (°C/W)
    r_junction: float = 1.0
    # Size factor (relative to full die)
    size_factor: float = 0.1
    # Power density factor (higher for dense logic)
    power_density: float = 1.0
    # Thermal coupling to adjacent hotspots
    coupling_factor: float = 0.05


@dataclass
class PDNOperatingPoint:
    """PDN voltage operating point configuration"""
    mode: PDNVoltageMode
    voltage_mv: float
    max_current_ma: float
    max_power_mw: float
    thermal_limit_c: float = 95.0


@dataclass
class ThrottleState:
    """Current thermal throttling state"""
    level: ThrottleLevel = ThrottleLevel.NONE
    active: bool = False
    throttle_factor: float = 1.0     # Frequency/voltage throttle multiplier
    pdn_mode: PDNVoltageMode = PDNVoltageMode.NOMINAL
    time_in_throttle_ns: int = 0
    throttle_count: int = 0
    max_temperature_reached: float = 0.0


@dataclass
class ThermalStatistics:
    """Runtime thermal statistics"""
    samples: int = 0
    peak_temperature_c: float = 0.0
    average_temperature_c: float = 0.0
    throttle_events: int = 0
    warning_events: int = 0
    critical_events: int = 0
    shutdown_events: int = 0
    total_throttle_time_ns: int = 0
    time_in_warning_ns: int = 0
    time_in_throttle_ns: int = 0
    time_in_critical_ns: int = 0

    def reset(self):
        """Reset all statistics"""
        self.samples = 0
        self.peak_temperature_c = 0.0
        self.average_temperature_c = 0.0
        self.throttle_events = 0
        self.warning_events = 0
        self.critical_events = 0
        self.shutdown_events = 0
        self.total_throttle_time_ns = 0
        self.time_in_warning_ns = 0
        self.time_in_throttle_ns = 0
        self.time_in_critical_ns = 0


class HBM4ThermalModel:
    """HBM4 Thermal Model for Logic Base Die

    Provides comprehensive thermal modeling for HBM4 components.
    Supports:
    - Per-component hotspot temperature tracking
    - Thermal resistance modeling
    - Dynamic throttling policy
    - PDN voltage management
    - Power-to-temperature conversion

    The thermal model uses a lumped RC model for each hotspot:
        T_junction = T_ambient + P * R_total

    where:
        R_total = R_junction + R_spreading + R_case + R_ambient

    Temperature rise is computed at each simulation step:
        delta_T = P * R * tau / C
        C = thermal capacitance

    Key features:
    - Thermal coupling between adjacent hotspots
    - Time-averaged temperature with exponential decay
    - Configurable thresholds for throttling
    - PDN-aware power limiting
    - Integration with HBM4PowerEstimator

    Reference:
    - JEDEC JESD270-4A HBM4
    - Hotspot thermal simulator
    - Synopsys HBM4 Controller IP thermal management
    """

    # Default thermal parameters (16nm logic base die)
    DEFAULT_AMBIENT_TEMP_C = 25.0       # Ambient temperature
    DEFAULT_INITIAL_TEMP_C = 35.0       # Initial die temperature
    DEFAULT_THERMAL_TAU_NS = 1000.0    # Thermal time constant (ns)

    # Thermal resistance defaults (°C/W)
    DEFAULT_R_JUNCTION = 0.5           # Junction to die surface
    DEFAULT_R_SPREADING = 2.0           # Spreading in die
    DEFAULT_R_CASE = 8.0               # Case to ambient

    # Hotspot size factors (relative to full die)
    DEFAULT_CONTROLLER_SIZE = 0.15      # Controller cluster: 15% of die
    DEFAULT_D2D_PHY_SIZE = 0.08          # D2D PHY: 8% of die
    DEFAULT_TSV_PHY_SIZE = 0.12         # TSV PHY: 12% of die
    DEFAULT_ECC_SIZE = 0.05             # ECC/RAS: 5% of die
    DEFAULT_CLOCKING_SIZE = 0.03        # Clocking: 3% of die

    def __init__(
        self,
        ambient_temp_c: float = DEFAULT_AMBIENT_TEMP_C,
        initial_temp_c: float = DEFAULT_INITIAL_TEMP_C,
        thermal_tau_ns: float = DEFAULT_THERMAL_TAU_NS,
        thresholds: Optional[TemperatureThresholds] = None,
    ):
        """Initialize HBM4 Thermal Model

        Args:
            ambient_temp_c: Ambient temperature in Celsius
            initial_temp_c: Initial die temperature in Celsius
            thermal_tau_ns: Thermal time constant in nanoseconds
            thresholds: Temperature thresholds for throttling
        """
        self.ambient_temp_c = ambient_temp_c
        self.thermal_tau_ns = thermal_tau_ns

        # Temperature thresholds
        self.thresholds = thresholds or TemperatureThresholds()

        # Initialize hotspot configurations
        self._init_hotspot_configs()

        # Initialize temperature state
        self.temperatures = ComponentTemperatures(
            ambient=ambient_temp_c,
            case=initial_temp_c,
            die=initial_temp_c,
            controller_cluster=initial_temp_c,
            d2d_phy=initial_temp_c,
            tsv_phy=initial_temp_c,
            ecc_ras=initial_temp_c,
            clocking=initial_temp_c,
            phy_interface=initial_temp_c,
        )

        # Initialize throttling state
        self.throttle_state = ThrottleState()

        # Initialize PDN operating points
        self._init_pdn_operating_points()

        # Initialize thermal statistics
        self.stats = ThermalStatistics()

        # External power estimator reference
        self._power_estimator = None

        # Last update timestamp
        self._last_update_ns = 0

    def _init_hotspot_configs(self):
        """Initialize hotspot configurations"""
        self.hotspot_configs = {
            'controller_cluster': HotspotConfig(
                r_junction=self.DEFAULT_R_JUNCTION,
                size_factor=self.DEFAULT_CONTROLLER_SIZE,
                power_density=1.5,  # High activity controller
                coupling_factor=0.08,
            ),
            'd2d_phy': HotspotConfig(
                r_junction=self.DEFAULT_R_JUNCTION * 0.8,
                size_factor=self.DEFAULT_D2D_PHY_SIZE,
                power_density=2.0,  # High-speed SerDes, dense
                coupling_factor=0.05,
            ),
            'tsv_phy': HotspotConfig(
                r_junction=self.DEFAULT_R_JUNCTION * 0.6,
                size_factor=self.DEFAULT_TSV_PHY_SIZE,
                power_density=1.2,  # TSV drivers
                coupling_factor=0.06,
            ),
            'ecc_ras': HotspotConfig(
                r_junction=self.DEFAULT_R_JUNCTION * 0.5,
                size_factor=self.DEFAULT_ECC_SIZE,
                power_density=0.8,  # ECC logic, lower activity
                coupling_factor=0.03,
            ),
            'clocking': HotspotConfig(
                r_junction=self.DEFAULT_R_JUNCTION * 0.7,
                size_factor=self.DEFAULT_CLOCKING_SIZE,
                power_density=1.0,  # PLL, DLL
                coupling_factor=0.02,
            ),
            'phy_interface': HotspotConfig(
                r_junction=self.DEFAULT_R_JUNCTION * 0.9,
                size_factor=0.10,
                power_density=1.3,  # DFI, TX/RX
                coupling_factor=0.07,
            ),
        }

    def _init_pdn_operating_points(self):
        """Initialize PDN voltage operating points"""
        self.pdn_operating_points = {
            PDNVoltageMode.NOMINAL: PDNOperatingPoint(
                mode=PDNVoltageMode.NOMINAL,
                voltage_mv=900,
                max_current_ma=5000,
                max_power_mw=4500,
                thermal_limit_c=95.0,
            ),
            PDNVoltageMode.PERFORMANCE: PDNOperatingPoint(
                mode=PDNVoltageMode.PERFORMANCE,
                voltage_mv=1000,
                max_current_ma=6000,
                max_power_mw=6000,
                thermal_limit_c=90.0,  # Stricter at higher voltage
            ),
            PDNVoltageMode.LOW_POWER: PDNOperatingPoint(
                mode=PDNVoltageMode.LOW_POWER,
                voltage_mv=800,
                max_current_ma=4000,
                max_power_mw=3200,
                thermal_limit_c=100.0,  # Can tolerate higher temp
            ),
            PDNVoltageMode.ULTRA_LOW: PDNOperatingPoint(
                mode=PDNVoltageMode.ULTRA_LOW,
                voltage_mv=650,
                max_current_ma=2500,
                max_power_mw=1625,
                thermal_limit_c=105.0,  # Maximum thermal margin
            ),
        }

    def set_power_estimator(self, estimator):
        """Set reference to power estimator for dynamic power tracking

        Args:
            estimator: HBM4PowerEstimator instance
        """
        self._power_estimator = estimator

    def update_temperature(
        self,
        timestamp_ns: int,
        power_breakdown: Optional[Dict[str, float]] = None,
    ):
        """Update temperatures based on power consumption

        Uses exponential moving average for temperature tracking:
            T_new = T_old + (P * R / C) * (1 - exp(-dt / tau))

        Args:
            timestamp_ns: Current simulation time in nanoseconds
            power_breakdown: Optional dict of component powers (mW)
                             If None, uses power estimator if available
        """
        # Calculate delta time
        dt = timestamp_ns - self._last_update_ns
        self._last_update_ns = timestamp_ns

        # Get power breakdown
        if power_breakdown is None and self._power_estimator is not None:
            power_breakdown = self._get_power_from_estimator()
        elif power_breakdown is None:
            power_breakdown = self._default_power_breakdown()

        # Update temperatures with thermal dynamics
        self._update_hotspot_temperatures(power_breakdown, dt, timestamp_ns)

        # Update die and case temperatures
        self._update_die_temperature(power_breakdown)

        # Update thermal throttling
        self._update_throttling(timestamp_ns)

        # Update statistics
        self._update_statistics(timestamp_ns)

    def _get_power_from_estimator(self) -> Dict[str, float]:
        """Get power breakdown from power estimator"""
        if self._power_estimator is None:
            return self._default_power_breakdown()

        breakdown = self._power_estimator.get_power_breakdown()

        return {
            'controller_cluster': breakdown.controller_power.total(),
            'd2d_phy': breakdown.phy_power.d2d_phy,
            'tsv_phy': breakdown.phy_power.tsv_phy,
            'ecc_ras': breakdown.ecc_power.total(),
            'clocking': breakdown.clocking_power.total(),
            'phy_interface': breakdown.phy_power.dfi_interface,
        }

    def _default_power_breakdown(self) -> Dict[str, float]:
        """Return default power breakdown when no estimator available"""
        return {
            'controller_cluster': 115.0,
            'd2d_phy': 80.0,
            'tsv_phy': 120.0,
            'ecc_ras': 34.0,
            'clocking': 78.0,
            'phy_interface': 45.0,
        }

    def _update_hotspot_temperatures(
        self,
        power_breakdown: Dict[str, float],
        dt_ns: float,
        timestamp_ns: int,
    ):
        """Update individual hotspot temperatures"""
        # Exponential decay factor for thermal time constant
        decay = math.exp(-dt_ns / self.thermal_tau_ns) if dt_ns > 0 else 0.0

        for hotspot_name, config in self.hotspot_configs.items():
            power = power_breakdown.get(hotspot_name, 0.0)

            # Calculate temperature rise
            r_total = config.r_junction + self.DEFAULT_R_SPREADING
            delta_t = power * r_total / 1000.0

            # Get current temperature
            current_temp = getattr(self.temperatures, hotspot_name)

            # Apply thermal dynamics with exponential settling
            steady_state = self.ambient_temp_c + delta_t
            new_temp = current_temp + (steady_state - current_temp) * (1.0 - decay)

            # Update temperature
            setattr(self.temperatures, hotspot_name, new_temp)

        # Apply thermal coupling between hotspots
        self._apply_thermal_coupling(decay)

    def _apply_thermal_coupling(self, decay: float):
        """Apply thermal coupling between adjacent hotspots"""
        hotspots = ['controller_cluster', 'd2d_phy', 'tsv_phy',
                    'ecc_ras', 'clocking', 'phy_interface']

        temp_deltas = {}

        for i, name in enumerate(hotspots):
            config = self.hotspot_configs[name]
            if config.coupling_factor <= 0:
                continue

            # Get average of adjacent temperatures
            adjacent_temps = []
            if i > 0:
                adjacent_temps.append(getattr(self.temperatures, hotspots[i-1]))
            if i < len(hotspots) - 1:
                adjacent_temps.append(getattr(self.temperatures, hotspots[i+1]))

            if adjacent_temps:
                avg_adjacent = sum(adjacent_temps) / len(adjacent_temps)
                current = getattr(self.temperatures, name)
                coupling_delta = (avg_adjacent - current) * config.coupling_factor
                temp_deltas[name] = coupling_delta * (1.0 - decay)

        # Apply deltas
        for name, delta in temp_deltas.items():
            current = getattr(self.temperatures, name)
            setattr(self.temperatures, name, current + delta)

    def _update_die_temperature(self, power_breakdown: Dict[str, float]):
        """Update die-level temperature from hotspot average"""
        total_power = sum(power_breakdown.values())
        r_total = self.DEFAULT_R_JUNCTION + self.DEFAULT_R_SPREADING + self.DEFAULT_R_CASE
        delta_t = total_power * r_total / 1000.0

        # Die temperature is weighted average of hotspots
        hotspot_temps = [
            self.temperatures.controller_cluster,
            self.temperatures.d2d_phy,
            self.temperatures.tsv_phy,
            self.temperatures.ecc_ras,
            self.temperatures.clocking,
            self.temperatures.phy_interface,
        ]
        avg_hotspot = sum(hotspot_temps) / len(hotspot_temps)

        # Case temperature
        self.temperatures.case = self.ambient_temp_c + delta_t * 0.8

        # Die temperature with hotspot influence
        self.temperatures.die = avg_hotspot + delta_t * 0.2

    def _update_throttling(self, timestamp_ns: int):
        """Update thermal throttling state"""
        max_temp = self.temperatures.max_temperature
        new_level = self.thresholds.get_throttle_level(max_temp)

        # Track level transitions
        if new_level != self.throttle_state.level:
            if new_level in [ThrottleLevel.WARNING, ThrottleLevel.THROTTLE,
                             ThrottleLevel.CRITICAL, ThrottleLevel.SHUTDOWN]:
                self.throttle_state.throttle_count += 1

        self.throttle_state.level = new_level
        self.throttle_state.max_temperature_reached = max(
            self.throttle_state.max_temperature_reached,
            max_temp
        )

        # Update throttle factor based on level
        if new_level == ThrottleLevel.SHUTDOWN:
            self.throttle_state.throttle_factor = 0.0
            self.throttle_state.active = True
        elif new_level == ThrottleLevel.CRITICAL:
            self.throttle_state.throttle_factor = 0.5
            self.throttle_state.active = True
        elif new_level == ThrottleLevel.THROTTLE:
            self.throttle_state.throttle_factor = 0.75
            self.throttle_state.active = True
        elif new_level == ThrottleLevel.WARNING:
            self.throttle_state.throttle_factor = 0.9
            self.throttle_state.active = False  # Monitoring only
        else:
            self.throttle_state.throttle_factor = 1.0
            self.throttle_state.active = False

        # Update PDN mode based on temperature
        self._update_pdn_mode(max_temp)

        # Update throttle time tracking
        if self.throttle_state.active:
            self.throttle_state.time_in_throttle_ns = timestamp_ns

    def _update_pdn_mode(self, temperature: float):
        """Update PDN operating mode based on temperature"""
        for mode, op_point in self.pdn_operating_points.items():
            if temperature >= op_point.thermal_limit_c:
                self.throttle_state.pdn_mode = mode
                return

        # Default to nominal
        self.throttle_state.pdn_mode = PDNVoltageMode.NOMINAL

    def _update_statistics(self, timestamp_ns: int):
        """Update thermal statistics"""
        self.stats.samples += 1

        max_temp = self.temperatures.max_temperature
        avg_temp = self.temperatures.average_temperature

        # Running average
        if self.stats.samples == 1:
            self.stats.average_temperature_c = avg_temp
        else:
            self.stats.average_temperature_c = (
                (self.stats.average_temperature_c * (self.stats.samples - 1) + avg_temp)
                / self.stats.samples
            )

        # Peak tracking
        if max_temp > self.stats.peak_temperature_c:
            self.stats.peak_temperature_c = max_temp

        # Event counting
        level = self.throttle_state.level
        if level == ThrottleLevel.WARNING:
            self.stats.warning_events += 1
            self.stats.time_in_warning_ns += 1
        elif level == ThrottleLevel.THROTTLE:
            self.stats.throttle_events += 1
            self.stats.time_in_throttle_ns += 1
        elif level == ThrottleLevel.CRITICAL:
            self.stats.critical_events += 1
            self.stats.time_in_critical_ns += 1
        elif level == ThrottleLevel.SHUTDOWN:
            self.stats.shutdown_events += 1

    def get_component_temperature(self, component: str) -> float:
        """Get temperature for a specific component

        Args:
            component: Component name ('controller_cluster', 'd2d_phy', etc.)

        Returns:
            Temperature in Celsius
        """
        return getattr(self.temperatures, component, self.temperatures.die)

    def get_die_temperature(self) -> float:
        """Get die temperature"""
        return self.temperatures.die

    def get_max_temperature(self) -> float:
        """Get maximum temperature across all components"""
        return self.temperatures.max_temperature

    def get_throttle_factor(self) -> float:
        """Get current throttle factor for frequency/voltage adjustment"""
        return self.throttle_state.throttle_factor

    def get_throttle_level(self) -> ThrottleLevel:
        """Get current throttle level"""
        return self.throttle_state.level

    def is_throttling_active(self) -> bool:
        """Check if throttling is active"""
        return self.throttle_state.active

    def get_pdn_mode(self) -> PDNVoltageMode:
        """Get current PDN voltage mode"""
        return self.throttle_state.pdn_mode

    def get_pdn_voltage(self) -> float:
        """Get PDN voltage for current operating point"""
        op_point = self.pdn_operating_points.get(
            self.throttle_state.pdn_mode,
            self.pdn_operating_points[PDNVoltageMode.NOMINAL]
        )
        return op_point.voltage_mv

    def get_thermal_resistance(self, component: str) -> float:
        """Get thermal resistance for a component

        Args:
            component: Component name

        Returns:
            Thermal resistance in °C/W
        """
        config = self.hotspot_configs.get(component)
        if config:
            return config.r_junction + self.DEFAULT_R_SPREADING
        return self.DEFAULT_R_JUNCTION + self.DEFAULT_R_SPREADING

    def calculate_power_limit(
        self,
        target_temp_c: float,
        ambient_temp_c: Optional[float] = None,
    ) -> float:
        """Calculate maximum power for a target temperature

        Args:
            target_temp_c: Target maximum temperature in Celsius
            ambient_temp_c: Ambient temperature (uses default if None)

        Returns:
            Maximum power in mW
        """
        if ambient_temp_c is None:
            ambient_temp_c = self.ambient_temp_c

        delta_t = target_temp_c - ambient_temp_c
        r_total = self.DEFAULT_R_JUNCTION + self.DEFAULT_R_SPREADING + self.DEFAULT_R_CASE

        return delta_t * 1000.0 / r_total

    def get_temperature_rise(self, power_mw: float, component: Optional[str] = None) -> float:
        """Calculate temperature rise from power

        Args:
            power_mw: Power in milliwatts
            component: Component name (uses die-level if None)

        Returns:
            Temperature rise in Celsius
        """
        if component:
            r = self.get_thermal_resistance(component)
        else:
            r = self.DEFAULT_R_JUNCTION + self.DEFAULT_R_SPREADING + self.DEFAULT_R_CASE

        return power_mw * r / 1000.0

    def get_throttle_summary(self) -> Dict:
        """Get throttling state summary

        Returns:
            Dictionary with throttling information
        """
        return {
            'level': self.throttle_state.level.value,
            'active': self.throttle_state.active,
            'throttle_factor': self.throttle_state.throttle_factor,
            'pdn_mode': self.throttle_state.pdn_mode.value,
            'pdn_voltage_mv': self.get_pdn_voltage(),
            'max_temp_reached': self.throttle_state.max_temperature_reached,
            'throttle_count': self.throttle_state.throttle_count,
            'time_in_throttle_ns': self.throttle_state.time_in_throttle_ns,
        }

    def get_summary(self) -> Dict:
        """Get complete thermal model summary

        Returns:
            Dictionary with thermal model state
        """
        return {
            'temperatures': {
                'ambient_c': self.temperatures.ambient,
                'case_c': self.temperatures.case,
                'die_c': self.temperatures.die,
                'max_c': self.temperatures.max_temperature,
                'average_c': self.temperatures.average_temperature,
                'controller_cluster_c': self.temperatures.controller_cluster,
                'd2d_phy_c': self.temperatures.d2d_phy,
                'tsv_phy_c': self.temperatures.tsv_phy,
                'ecc_ras_c': self.temperatures.ecc_ras,
                'clocking_c': self.temperatures.clocking,
                'phy_interface_c': self.temperatures.phy_interface,
            },
            'throttle': self.get_throttle_summary(),
            'pdn': {
                mode.value: {
                    'voltage_mv': op.voltage_mv,
                    'max_power_mw': op.max_power_mw,
                }
                for mode, op in self.pdn_operating_points.items()
            },
            'thresholds': {
                'warning_c': self.thresholds.warning,
                'throttle_c': self.thresholds.throttle,
                'critical_c': self.thresholds.critical,
                'shutdown_c': self.thresholds.shutdown,
            },
            'stats': {
                'samples': self.stats.samples,
                'peak_temperature_c': self.stats.peak_temperature_c,
                'average_temperature_c': self.stats.average_temperature_c,
                'throttle_events': self.stats.throttle_events,
                'warning_events': self.stats.warning_events,
                'critical_events': self.stats.critical_events,
                'shutdown_events': self.stats.shutdown_events,
            },
            'thermal_resistance': {
                'r_junction_c_w': self.DEFAULT_R_JUNCTION,
                'r_spreading_c_w': self.DEFAULT_R_SPREADING,
                'r_case_c_w': self.DEFAULT_R_CASE,
                'r_total_c_w': self.DEFAULT_R_JUNCTION + self.DEFAULT_R_SPREADING + self.DEFAULT_R_CASE,
            },
        }

    def reset(self):
        """Reset thermal model state"""
        self.temperatures = ComponentTemperatures(
            ambient=self.ambient_temp_c,
            case=self.ambient_temp_c,
            die=self.ambient_temp_c,
            controller_cluster=self.ambient_temp_c,
            d2d_phy=self.ambient_temp_c,
            tsv_phy=self.ambient_temp_c,
            ecc_ras=self.ambient_temp_c,
            clocking=self.ambient_temp_c,
            phy_interface=self.ambient_temp_c,
        )

        self.throttle_state = ThrottleState()
        self.stats = ThermalStatistics()
        self._last_update_ns = 0


# Factory function
def create_thermal_model(
    ambient_temp_c: float = 25.0,
    speed_grade: str = "8Gbps",
) -> HBM4ThermalModel:
    """Create thermal model with specified configuration

    Args:
        ambient_temp_c: Ambient temperature in Celsius
        speed_grade: Speed grade ('8Gbps', '12Gbps', '16Gbps')

    Returns:
        Configured HBM4ThermalModel
    """
    # Adjust thresholds based on speed grade (higher speed = tighter thermal)
    if speed_grade == "16Gbps":
        thresholds = TemperatureThresholds(
            warning=80.0,
            throttle=90.0,
            critical=100.0,
            shutdown=105.0,
        )
    elif speed_grade == "12Gbps":
        thresholds = TemperatureThresholds(
            warning=82.0,
            throttle=92.0,
            critical=102.0,
            shutdown=108.0,
        )
    else:  # 8Gbps
        thresholds = TemperatureThresholds()

    return HBM4ThermalModel(
        ambient_temp_c=ambient_temp_c,
        thresholds=thresholds,
    )