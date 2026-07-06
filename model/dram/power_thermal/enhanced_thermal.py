"""
Enhanced Thermal Model with Dynamic Cooling

Extended thermal modeling with active cooling support, multi-tier cooling,
and adaptive throttling for HBM4 thermal management.

Features:
- Dynamic cooling system integration
- Multi-tier throttling response
- Thermal zone management
- Power budget enforcement
- Emergency cooling protocols

Reference:
- JEDEC JESD270-4A HBM4 specification
- JESD51-14 Thermal test method
- HBM thermal management guidelines
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
import math

from model.dram.thermal_model import (
    LayeredThermalModel,
    ThermalLayer,
    HotspotSeverity,
    HotspotReport,
    VirtualProbe,
    ActivityFactor,
    create_layered_thermal_model,
)
from model.dram.power_estimator import (
    HBM4PowerEstimator,
    PowerState,
)


class CoolingType(Enum):
    """Types of cooling systems"""
    NONE = "none"
    PASSIVE = "passive"
    HEATSINK = "heatsink"
    FAN = "fan"
    LIQUID = "liquid"
    thermoelectric = "thermoelectric"  # Peltier/TEC


class ThrottleLevel(Enum):
    """Throttling severity levels"""
    NONE = 0
    LIGHT = 1      # DVFS -10%
    MODERATE = 2   # DVFS -25%
    HEAVY = 3       # DVFS -50%, pause refresh
    CRITICAL = 4   # Emergency - minimal operation


@dataclass
class CoolingSystemConfig:
    """Configuration for cooling system"""
    cooling_type: CoolingType = CoolingType.HEATSINK
    cooling_capacity_w: float = 5.0  # Max cooling capacity (W)
    efficiency: float = 0.8  # Cooling efficiency (0-1)
    response_time_ms: float = 10.0  # Time to reach full cooling (ms)
    power_consumption_w: float = 0.5  # Power used by cooling system

    # Temperature thresholds for cooling activation
    activation_temp_c: float = 60.0  # Start cooling
    max_temp_c: float = 85.0  # Max safe temperature
    critical_temp_c: float = 95.0  # Throttle required
    emergency_temp_c: float = 105.0  # Emergency measures

    # Fan specific
    fan_rpm_min: int = 1000
    fan_rpm_max: int = 5000
    fan_rpm_per_degree: float = 50.0  # RPM increase per degree above ambient


@dataclass
class ThermalZone:
    """Thermal zone for localized management"""
    zone_id: int
    name: str
    layers: List[ThermalLayer] = field(default_factory=list)
    channels: List[int] = field(default_factory=list)

    # Zone state
    current_temp_c: float = 45.0
    target_temp_c: float = 65.0
    power_budget_mw: float = 500.0

    # Zone thresholds
    warning_temp_c: float = 75.0
    throttle_temp_c: float = 85.0
    shutdown_temp_c: float = 100.0

    # Zone cooling
    cooling_enabled: bool = False
    cooling_level: float = 0.0  # 0-1

    def is_overheating(self) -> bool:
        return self.current_temp_c >= self.throttle_temp_c

    def is_critical(self) -> bool:
        return self.current_temp_c >= self.shutdown_temp_c

    def needs_cooling(self) -> bool:
        return self.current_temp_c >= self.target_temp_c


@dataclass
class ThrottleEvent:
    """Thermal throttle event record"""
    timestamp_ns: int
    level: ThrottleLevel
    trigger_temp_c: float
    trigger_layer: ThermalLayer
    action_taken: str
    duration_cycles: int = 0


@dataclass
class EnhancedThermalModel:
    """Enhanced thermal model with dynamic cooling and throttling

    Features:
    - Multi-zone thermal management
    - Active cooling system control
    - Multi-tier throttling response
    - Power budget enforcement
    - Emergency protocols
    """

    # Base thermal model
    base_model: LayeredThermalModel = field(default_factory=create_layered_thermal_model)

    # Cooling system
    cooling_config: CoolingSystemConfig = field(default_factory=CoolingSystemConfig)
    cooling_active: bool = False
    cooling_level: float = 0.0  # 0-1

    # Thermal zones
    zones: List[ThermalZone] = field(default_factory=list)
    num_zones: int = 4

    # Throttling state
    throttle_level: ThrottleLevel = ThrottleLevel.NONE
    throttle_events: List[ThrottleEvent] = field(default_factory=list)
    max_throttle_events: int = 100

    # Power budget
    power_budget_mw: float = 10000.0  # 10W default budget
    current_power_mw: float = 0.0

    # Callbacks
    on_throttle_callback: Optional[Callable[[ThrottleLevel, float], None]] = None
    on_cooling_callback: Optional[Callable[[bool, float], None]] = None

    # Statistics
    total_throttle_time_ns: int = 0
    cooling_energy_j: float = 0.0

    def __post_init__(self):
        """Initialize enhanced thermal model"""
        self._initialize_zones()
        self._setup_default_callbacks()

    def _initialize_zones(self):
        """Initialize thermal zones"""
        self.zones = []
        channels_per_zone = self.base_model.num_channels // self.num_zones

        for zone_id in range(self.num_zones):
            ch_start = zone_id * channels_per_zone
            ch_end = ch_start + channels_per_zone

            # Map zone to layers (approximate)
            if zone_id == 0:
                layers = [ThermalLayer.LOGIC_BASE_DIE]
            elif zone_id == 1:
                layers = [ThermalLayer.TSV_LAYER_1, ThermalLayer.DRAM_DIE_1]
            elif zone_id == 2:
                layers = [ThermalLayer.TSV_LAYER_2, ThermalLayer.DRAM_DIE_2]
            else:
                layers = [ThermalLayer.TSV_LAYER_3, ThermalLayer.DRAM_DIE_3, ThermalLayer.TSV_LAYER_4, ThermalLayer.DRAM_DIE_4]

            zone = ThermalZone(
                zone_id=zone_id,
                name=f"Zone_{zone_id}",
                layers=layers,
                channels=list(range(ch_start, ch_end)),
            )
            self.zones.append(zone)

    def _setup_default_callbacks(self):
        """Setup default throttle/cooling callbacks"""
        def default_throttle(level: ThrottleLevel, temp: float):
            print(f"Throttle {level.name}: temp={temp:.1f}C")

        def default_cooling(active: bool, level: float):
            print(f"Cooling {'ON' if active else 'OFF'}: level={level:.1%}")

        self.on_throttle_callback = default_throttle
        self.on_cooling_callback = default_cooling

    def update(
        self,
        time_ns: int,
        channel_powers_mw: Optional[Dict[int, float]] = None,
        dt_ns: float = 1000.0,
    ):
        """Update thermal model

        Args:
            time_ns: Current simulation time (ns)
            channel_powers_mw: Optional per-channel power dict
            dt_ns: Time step (ns)
        """
        # Update base thermal model
        self.base_model.simulate_step(time_ns, dt_ns)

        # Update zone temperatures
        self._update_zone_temperatures()

        # Update cooling system
        self._update_cooling(dt_ns)

        # Check throttling conditions
        self._check_throttling(time_ns)

        # Update power budget
        self._update_power_budget(channel_powers_mw)

    def _update_zone_temperatures(self):
        """Update temperatures for each zone"""
        for zone in self.zones:
            temps = []
            for layer in zone.layers:
                temp = self.base_model.get_layer_temperature(layer)
                temps.append(temp)

            if temps:
                # Weight by layer importance
                zone.current_temp_c = max(temps)
            else:
                # Fallback: use base model average
                max_layer, max_temp = self.base_model.get_max_temperature()
                zone.current_temp_c = max_temp

    def _update_cooling(self, dt_ns: float):
        """Update cooling system based on temperatures

        Args:
            dt_ns: Time step (ns)
        """
        # Find max temperature across zones
        max_temp = max((z.current_temp_c for z in self.zones), default=self.base_model.ambient_temp_c)

        # Determine cooling need
        config = self.cooling_config

        if max_temp >= config.activation_temp_c:
            if not self.cooling_active:
                self.cooling_active = True
                if self.on_cooling_callback:
                    self.on_cooling_callback(True, 0.0)

            # Calculate cooling level
            if max_temp >= config.critical_temp_c:
                self.cooling_level = 1.0
            elif max_temp >= config.emergency_temp_c:
                self.cooling_level = 0.8
            elif max_temp >= config.max_temp_c:
                self.cooling_level = 0.5
            elif max_temp >= config.activation_temp_c:
                # Linear scaling
                self.cooling_level = (max_temp - config.activation_temp_c) / (config.max_temp_c - config.activation_temp_c)
            else:
                self.cooling_level = 0.0

        else:
            if self.cooling_active:
                self.cooling_active = False
                self.cooling_level = 0.0
                if self.on_cooling_callback:
                    self.on_cooling_callback(False, 0.0)

        # Apply cooling effect to temperatures
        if self.cooling_active and self.cooling_level > 0:
            cooling_effect_c = self.cooling_config.cooling_capacity_w * self.cooling_config.efficiency * self.cooling_level * 0.5
            for zone in self.zones:
                zone.current_temp_c = max(
                    self.base_model.ambient_temp_c,
                    zone.current_temp_c - cooling_effect_c
                )

        # Track cooling energy
        if self.cooling_active:
            self.cooling_energy_j += (
                self.cooling_config.power_consumption_w * self.cooling_level * dt_ns * 1e-9
            )

    def _check_throttling(self, time_ns: int):
        """Check and apply throttling based on temperature

        Args:
            time_ns: Current simulation time
        """
        # Find worst-case zone
        worst_zone = max(self.zones, key=lambda z: z.current_temp_c, default=None)
        if not worst_zone:
            return

        temp = worst_zone.current_temp_c
        new_level = ThrottleLevel.NONE

        # Determine throttle level
        if temp >= self.cooling_config.emergency_temp_c:
            new_level = ThrottleLevel.CRITICAL
        elif temp >= self.cooling_config.critical_temp_c:
            new_level = ThrottleLevel.HEAVY
        elif temp >= self.cooling_config.max_temp_c:
            new_level = ThrottleLevel.MODERATE
        elif temp >= self.cooling_config.activation_temp_c:
            new_level = ThrottleLevel.LIGHT

        # Apply throttling if level increased
        if new_level.value > self.throttle_level.value:
            event = ThrottleEvent(
                timestamp_ns=time_ns,
                level=new_level,
                trigger_temp_c=temp,
                trigger_layer=worst_zone.layers[0] if worst_zone.layers else ThermalLayer.LOGIC_BASE_DIE,
                action_taken=f"Throttle to {new_level.name}",
            )
            self.throttle_events.append(event)

            # Keep bounded
            if len(self.throttle_events) > self.max_throttle_events:
                self.throttle_events = self.throttle_events[-self.max_throttle_events // 2:]

            if self.on_throttle_callback:
                self.on_throttle_callback(new_level, temp)

        # Track throttle duration
        if self.throttle_level != ThrottleLevel.NONE:
            if self.throttle_events:
                self.throttle_events[-1].duration_cycles += 1
            self.total_throttle_time_ns += 1000  # Approximate 1us per check

        self.throttle_level = new_level

    def _update_power_budget(
        self,
        channel_powers_mw: Optional[Dict[int, float]] = None,
    ):
        """Update power budget based on thermal constraints

        Args:
            channel_powers_mw: Per-channel power dict
        """
        if channel_powers_mw is None:
            # Use last known power
            return

        self.current_power_mw = sum(channel_powers_mw.values())

        # Apply throttling to reduce power if over budget
        if self.current_power_mw > self.power_budget_mw:
            throttle_factor = self.power_budget_mw / self.current_power_mw
            self.current_power_mw *= throttle_factor

    def get_throttle_factor(self) -> float:
        """Get throttling factor for DVFS system

        Returns:
            Frequency/multiplier factor (0-1)
        """
        factors = {
            ThrottleLevel.NONE: 1.0,
            ThrottleLevel.LIGHT: 0.9,
            ThrottleLevel.MODERATE: 0.75,
            ThrottleLevel.HEAVY: 0.5,
            ThrottleLevel.CRITICAL: 0.25,
        }
        return factors.get(self.throttle_level, 1.0)

    def get_cooling_power(self) -> float:
        """Get power consumed by cooling system

        Returns:
            Cooling power in W
        """
        return self.cooling_config.power_consumption_w * self.cooling_level

    def get_zone_throttle_level(self, zone_id: int) -> ThrottleLevel:
        """Get throttle level for a specific zone

        Args:
            zone_id: Zone identifier

        Returns:
            ThrottleLevel for the zone
        """
        if zone_id >= len(self.zones):
            return ThrottleLevel.NONE

        zone = self.zones[zone_id]
        temp = zone.current_temp_c
        config = self.cooling_config

        if temp >= config.emergency_temp_c:
            return ThrottleLevel.CRITICAL
        elif temp >= config.critical_temp_c:
            return ThrottleLevel.HEAVY
        elif temp >= config.max_temp_c:
            return ThrottleLevel.MODERATE
        elif temp >= config.activation_temp_c:
            return ThrottleLevel.LIGHT
        return ThrottleLevel.NONE

    def get_thermal_summary(self) -> Dict[str, Any]:
        """Get comprehensive thermal summary

        Returns:
            Dictionary with all thermal metrics
        """
        return {
            "base_model": self.base_model.get_thermal_summary(),
            "cooling": {
                "active": self.cooling_active,
                "level": self.cooling_level,
                "power_w": self.get_cooling_power(),
                "total_energy_j": self.cooling_energy_j,
                "type": self.cooling_config.cooling_type.value,
            },
            "throttle": {
                "level": self.throttle_level.name,
                "factor": self.get_throttle_factor(),
                "event_count": len(self.throttle_events),
                "total_time_ns": self.total_throttle_time_ns,
            },
            "zones": [
                {
                    "id": z.zone_id,
                    "name": z.name,
                    "temp_c": z.current_temp_c,
                    "throttle_level": self.get_zone_throttle_level(z.zone_id).name,
                    "cooling_level": z.cooling_level,
                }
                for z in self.zones
            ],
            "power": {
                "budget_mw": self.power_budget_mw,
                "current_mw": self.current_power_mw,
                "utilization": self.current_power_mw / self.power_budget_mw if self.power_budget_mw > 0 else 0,
            },
        }

    def reset(self):
        """Reset thermal model state"""
        self.base_model.reset()
        self.cooling_active = False
        self.cooling_level = 0.0
        self.throttle_level = ThrottleLevel.NONE
        self.throttle_events = []
        self.total_throttle_time_ns = 0
        self.cooling_energy_j = 0.0
        self.current_power_mw = 0.0


class AdaptiveThrottler:
    """Adaptive throttling controller for HBM4

    Implements closed-loop thermal management:
    - Monitors temperature trends
    - Predicts thermal runaway
    - Adapts throttle response
    - Minimizes performance impact
    """

    def __init__(
        self,
        thermal_model: EnhancedThermalModel,
        history_size: int = 100,
    ):
        """Initialize adaptive throttler

        Args:
            thermal_model: EnhancedThermalModel to control
            history_size: Number of temperature samples to track
        """
        self.thermal = thermal_model
        self.temp_history: List[Tuple[int, float]] = []  # (time, temp)
        self.history_size = history_size

        # Prediction state
        self.trend_slope: float = 0.0
        self.predictive_throttle: ThrottleLevel = ThrottleLevel.NONE

    def update(self, time_ns: int) -> ThrottleLevel:
        """Update throttling based on current state

        Args:
            time_ns: Current simulation time

        Returns:
            Recommended ThrottleLevel
        """
        # Get current max temperature
        max_temp = max((z.current_temp_c for z in self.thermal.zones), default=45.0)

        # Record history
        self.temp_history.append((time_ns, max_temp))
        if len(self.temp_history) > self.history_size:
            self.temp_history = self.temp_history[-self.history_size // 2:]

        # Calculate trend
        self._update_trend()

        # Predict future temperature
        predicted_temp = self._predict_temperature(time_ns)

        # Determine adaptive throttle
        current_level = self.thermal.throttle_level
        recommended = self._determine_throttle(predicted_temp)

        # Return conservative of current and recommended
        return max(current_level, recommended, key=lambda x: x.value)

    def _update_trend(self):
        """Update temperature trend slope"""
        if len(self.temp_history) < 10:
            self.trend_slope = 0.0
            return

        # Linear regression on recent history
        temps = [t for _, t in self.temp_history[-20:]]
        times = list(range(len(temps)))

        n = len(temps)
        mean_t = sum(temps) / n
        mean_x = sum(times) / n

        numerator = sum((times[i] - mean_x) * (temps[i] - mean_t) for i in range(n))
        denominator = sum((times[i] - mean_x) ** 2 for i in range(n))

        if denominator > 0:
            self.trend_slope = numerator / denominator

    def _predict_temperature(self, future_time_ns: int) -> float:
        """Predict temperature at future time

        Args:
            future_time_ns: Future time to predict

        Returns:
            Predicted temperature
        """
        if not self.temp_history or self.trend_slope == 0:
            return self.temp_history[-1][1] if self.temp_history else 45.0

        # Simple linear extrapolation
        current_time = self.temp_history[-1][0]
        current_temp = self.temp_history[-1][1]

        time_delta = (future_time_ns - current_time) / 1000  # Convert to us
        predicted = current_temp + self.trend_slope * time_delta * 0.01  # Scale factor

        return min(predicted, 150.0)  # Cap at reasonable max

    def _determine_throttle(self, predicted_temp: float) -> ThrottleLevel:
        """Determine throttle level from predicted temperature

        Args:
            predicted_temp: Predicted temperature

        Returns:
            Recommended ThrottleLevel
        """
        config = self.thermal.cooling_config

        # Aggressive prediction-based throttling
        if predicted_temp >= config.emergency_temp_c * 0.9:
            return ThrottleLevel.CRITICAL
        elif predicted_temp >= config.critical_temp_c * 0.9:
            return ThrottleLevel.HEAVY
        elif predicted_temp >= config.max_temp_c * 0.9:
            return ThrottleLevel.MODERATE
        elif predicted_temp >= config.activation_temp_c:
            return ThrottleLevel.LIGHT
        return ThrottleLevel.NONE

    def get_prediction_info(self) -> Dict[str, Any]:
        """Get prediction information

        Returns:
            Dictionary with trend and prediction data
        """
        return {
            "trend_slope": self.trend_slope,
            "history_size": len(self.temp_history),
            "current_temp": self.temp_history[-1][1] if self.temp_history else None,
            "predicted_temp": self._predict_temperature(
                self.temp_history[-1][0] + 10000 if self.temp_history else 0
            ) if self.temp_history else None,
            "predictive_throttle": self.predictive_throttle.name,
        }


def create_enhanced_thermal_model(
    num_channels: int = 32,
    num_zones: int = 4,
    cooling_type: CoolingType = CoolingType.HEATSINK,
    ambient_temp_c: float = 45.0,
) -> EnhancedThermalModel:
    """Create enhanced thermal model

    Args:
        num_channels: Number of HBM channels
        num_zones: Number of thermal zones
        cooling_type: Type of cooling system
        ambient_temp_c: Ambient temperature

    Returns:
        Configured EnhancedThermalModel
    """
    base = create_layered_thermal_model(
        ambient_temp_c=ambient_temp_c,
        num_channels=num_channels,
    )

    cooling = CoolingSystemConfig(cooling_type=cooling_type)

    model = EnhancedThermalModel(
        base_model=base,
        cooling_config=cooling,
        num_zones=num_zones,
    )

    return model


def create_adaptive_thermal_controller(
    num_channels: int = 32,
) -> Tuple[EnhancedThermalModel, AdaptiveThrottler]:
    """Create thermal model with adaptive throttling

    Args:
        num_channels: Number of HBM channels

    Returns:
        Tuple of (EnhancedThermalModel, AdaptiveThrottler)
    """
    thermal = create_enhanced_thermal_model(num_channels)
    throttler = AdaptiveThrottler(thermal)
    return thermal, throttler
