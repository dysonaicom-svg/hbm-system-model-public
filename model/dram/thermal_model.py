"""
HBM4 Layer-by-Layer Thermal Model

Provides comprehensive thermal modeling for HBM4 stacked architecture with:
- Layer-by-layer thermal simulation
- TSV thermal resistance network
- Activity factor-based thermal modeling
- Virtual probe placement and monitoring
- Hotspot detection and reporting

Reference:
- JEDEC JESD270-4A HBM4 specification
- JESD51-14 Thermal test method
- TSV thermal resistance models (0.5 C/mW)

HBM4 Stack Architecture:
    +-------------------+
    |   Logic Base Die  |  <- 50-100 um thickness
    +-------------------+
    |      TSV Layer    |  <- Thermal interface
    +-------------------+
    |    DRAM Die 1     |  <- 20-50 um thickness
    +-------------------+
    |      TSV Layer    |
    +-------------------+
    |    DRAM Die 2     |
    +-------------------+
    +-------------------+
    |    DRAM Die 4-8   |
    +-------------------+
    +-------------------+
    |   Package Base    |
    +-------------------+
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
import math
import time
import random


class ThermalLayer(Enum):
    """HBM4 stack thermal layers"""
    PACKAGE_TOP = "package_top"
    LOGIC_BASE_DIE = "logic_base_die"
    TSV_LAYER_1 = "tsv_layer_1"
    DRAM_DIE_1 = "dram_die_1"
    TSV_LAYER_2 = "tsv_layer_2"
    DRAM_DIE_2 = "dram_die_2"
    TSV_LAYER_3 = "tsv_layer_3"
    DRAM_DIE_3 = "dram_die_3"
    TSV_LAYER_4 = "tsv_layer_4"
    DRAM_DIE_4 = "dram_die_4"
    DRAM_DIE_5 = "dram_die_5"
    DRAM_DIE_6 = "dram_die_6"
    DRAM_DIE_7 = "dram_die_7"
    DRAM_DIE_8 = "dram_die_8"
    PACKAGE_BASE = "package_base"


class HotspotSeverity(Enum):
    """Hotspot severity levels"""
    NONE = "none"
    WARNING = "warning"      # > 85C
    THROTTLE = "throttle"   # > 95C
    CRITICAL = "critical"  # > 100C
    EMERGENCY = "emergency" # > 105C


@dataclass
class LayerProperties:
    """Physical properties of each thermal layer"""
    name: str
    thickness_um: float = 50.0
    thermal_conductivity: float = 100.0  # W/(m-K)
    thermal_capacity: float = 1.0  # J/(g-K)
    density: float = 2.33  # g/cm^3 (silicon)
    area_mm2: float = 100.0  # Die area

    @property
    def thermal_mass(self) -> float:
        """Calculate thermal mass (J/K)"""
        # Volume in m^3
        volume = (self.area_mm2 * 1e-6) * (self.thickness_um * 1e-6)
        # Mass in kg
        mass = volume * self.density * 1000
        # Thermal mass
        return mass * self.thermal_capacity


@dataclass
class TSVNetworkConfig:
    """TSV thermal resistance network configuration"""
    # TSV thermal resistance (C/mW per TSV)
    tsv_thermal_resistance: float = 0.5

    # Number of TSVs per channel
    tsv_count: int = 100000

    # TSV pitch (um)
    tsv_pitch: float = 5.0

    # TSV diameter (um)
    tsv_diameter: float = 2.0

    # Thermal interface material (TIM) resistance
    tim_resistance: float = 0.1  # C/W

    # TSV density factor (fraction of area)
    tsv_density: float = 0.01

    # Temperature gradient along TSV
    temperature_gradient: float = 0.0

    def get_effective_resistance(self, tsv_count: int) -> float:
        """Get effective TSV thermal resistance for given count"""
        # Parallel thermal resistances
        if tsv_count > 0:
            return self.tsv_thermal_resistance / tsv_count
        return self.tsv_thermal_resistance


@dataclass
class LayerTemperature:
    """Temperature state for a thermal layer"""
    layer: ThermalLayer
    temperature_c: float = 45.0
    previous_temp_c: float = 45.0
    rate_of_change: float = 0.0  # C/s
    power_dissipation_mw: float = 0.0
    thermal_resistance: float = 0.5  # C/W
    last_update_ns: int = 0


@dataclass
class ActivityFactor:
    """Activity factor for thermal modeling"""
    read_activity: float = 0.5  # 0-1
    write_activity: float = 0.3  # 0-1
    refresh_activity: float = 0.1  # 0-1
    idle_fraction: float = 0.2  # Fraction of time idle

    @property
    def effective_activity(self) -> float:
        """Calculate effective activity factor"""
        return (
            self.read_activity * 0.4 +
            self.write_activity * 0.5 +
            self.refresh_activity * 0.1
        ) * (1.0 - self.idle_fraction)


@dataclass
class VirtualProbe:
    """Virtual probe for internal thermal monitoring"""
    probe_id: int
    name: str
    layer: ThermalLayer
    position_x: float  # Normalized position (0-1)
    position_y: float  # Normalized position (0-1)
    sampling_interval_ns: int = 1000
    measurement_count: int = 0
    measurements: List[Tuple[int, float]] = field(default_factory=list)

    # Threshold configuration
    warning_threshold_c: float = 85.0
    throttle_threshold_c: float = 95.0
    critical_threshold_c: float = 105.0

    def get_severity(self, temperature_c: float) -> HotspotSeverity:
        """Determine hotspot severity"""
        if temperature_c >= self.critical_threshold_c:
            return HotspotSeverity.EMERGENCY
        elif temperature_c >= self.throttle_threshold_c:
            return HotspotSeverity.CRITICAL
        elif temperature_c >= self.warning_threshold_c:
            return HotspotSeverity.WARNING
        return HotspotSeverity.NONE


@dataclass
class HotspotReport:
    """Hotspot detection report"""
    timestamp_ns: int
    detected: bool
    severity: HotspotSeverity
    temperature_c: float
    threshold_c: float
    layer: ThermalLayer
    probe_id: Optional[int] = None
    location_x: float = 0.0
    location_y: float = 0.0


@dataclass
class LayeredThermalModel:
    """HBM4 Layer-by-Layer Thermal Model

    Models thermal behavior of HBM4 stacked memory with:
    - Per-layer temperature tracking
    - TSV thermal resistance network
    - Activity-based power dissipation
    - Virtual probe placement and monitoring
    - Hotspot detection and reporting
    """
    num_channels: int = 32
    ambient_temp_c: float = 45.0

    # Layer configuration
    layers: Dict[ThermalLayer, LayerTemperature] = field(default_factory=dict)
    layer_properties: Dict[ThermalLayer, LayerProperties] = field(default_factory=dict)

    # TSV network
    tsv_config: TSVNetworkConfig = field(default_factory=TSVNetworkConfig)

    # Virtual probes
    probes: List[VirtualProbe] = field(default_factory=list)

    # Hotspot tracking
    hotspots: List[HotspotReport] = field(default_factory=list)
    max_hotspots: int = 100

    # Thermal thresholds (HBM4 spec)
    warning_threshold_c: float = 85.0
    throttle_threshold_c: float = 95.0
    critical_threshold_c: float = 105.0
    emergency_threshold_c: float = 110.0

    # Simulation state
    current_time_ns: int = 0
    activity_factors: Dict[int, ActivityFactor] = field(default_factory=dict)

    # Statistics
    peak_temperature_c: float = 45.0
    hotspot_detection_count: int = 0

    def __post_init__(self):
        """Initialize thermal model"""
        self._initialize_layers()
        self._initialize_default_probes()

    def _initialize_layers(self):
        """Initialize stack layers with HBM4 defaults"""
        # HBM4 Stack Layer Configuration
        layer_configs = {
            ThermalLayer.LOGIC_BASE_DIE: LayerProperties(
                name="Logic Base Die",
                thickness_um=50.0,  # 50-100 um for base die
                thermal_conductivity=120.0,
                area_mm2=100.0,
            ),
            ThermalLayer.TSV_LAYER_1: LayerProperties(
                name="TSV Layer 1",
                thickness_um=5.0,
                thermal_conductivity=50.0,  # Lower due to TSV
                area_mm2=100.0,
            ),
            ThermalLayer.DRAM_DIE_1: LayerProperties(
                name="DRAM Die 1",
                thickness_um=30.0,  # 20-50 um for DRAM
                thermal_conductivity=100.0,
                area_mm2=100.0,
            ),
            ThermalLayer.TSV_LAYER_2: LayerProperties(
                name="TSV Layer 2",
                thickness_um=5.0,
                thermal_conductivity=50.0,
                area_mm2=100.0,
            ),
            ThermalLayer.DRAM_DIE_2: LayerProperties(
                name="DRAM Die 2",
                thickness_um=30.0,
                thermal_conductivity=100.0,
                area_mm2=100.0,
            ),
            ThermalLayer.TSV_LAYER_3: LayerProperties(
                name="TSV Layer 3",
                thickness_um=5.0,
                thermal_conductivity=50.0,
                area_mm2=100.0,
            ),
            ThermalLayer.DRAM_DIE_3: LayerProperties(
                name="DRAM Die 3",
                thickness_um=30.0,
                thermal_conductivity=100.0,
                area_mm2=100.0,
            ),
            ThermalLayer.TSV_LAYER_4: LayerProperties(
                name="TSV Layer 4",
                thickness_um=5.0,
                thermal_conductivity=50.0,
                area_mm2=100.0,
            ),
            ThermalLayer.DRAM_DIE_4: LayerProperties(
                name="DRAM Die 4",
                thickness_um=30.0,
                thermal_conductivity=100.0,
                area_mm2=100.0,
            ),
            ThermalLayer.PACKAGE_BASE: LayerProperties(
                name="Package Base",
                thickness_um=200.0,
                thermal_conductivity=20.0,  # Substrate
                area_mm2=144.0,
            ),
        }

        for layer, props in layer_configs.items():
            self.layer_properties[layer] = props
            self.layers[layer] = LayerTemperature(
                layer=layer,
                temperature_c=self.ambient_temp_c,
                thermal_resistance=self._calculate_layer_resistance(layer, props),
            )

    def _calculate_layer_resistance(self, layer: ThermalLayer, props: LayerProperties) -> float:
        """Calculate thermal resistance for a layer"""
        # R = thickness / (conductivity * area)
        thickness_m = props.thickness_um * 1e-6
        area_m2 = props.area_mm2 * 1e-6
        return thickness_m / (props.thermal_conductivity * area_m2)

    def _initialize_default_probes(self):
        """Initialize default virtual probe placement"""
        # Place probes at key locations
        probe_configs = [
            # Logic base die - center and corners
            (ThermalLayer.LOGIC_BASE_DIE, 0.5, 0.5, "LBD_center"),
            (ThermalLayer.LOGIC_BASE_DIE, 0.1, 0.1, "LBD_corner_1"),
            (ThermalLayer.LOGIC_BASE_DIE, 0.9, 0.9, "LBD_corner_2"),
            # DRAM die hotspots
            (ThermalLayer.DRAM_DIE_1, 0.5, 0.5, "DRAM1_center"),
            (ThermalLayer.DRAM_DIE_2, 0.5, 0.5, "DRAM2_center"),
            (ThermalLayer.DRAM_DIE_3, 0.5, 0.5, "DRAM3_center"),
            (ThermalLayer.DRAM_DIE_4, 0.5, 0.5, "DRAM4_center"),
            # TSV thermal monitoring
            (ThermalLayer.TSV_LAYER_1, 0.5, 0.5, "TSV1_center"),
            (ThermalLayer.TSV_LAYER_2, 0.5, 0.5, "TSV2_center"),
        ]

        for i, (layer, x, y, name) in enumerate(probe_configs):
            self.probes.append(VirtualProbe(
                probe_id=i,
                name=name,
                layer=layer,
                position_x=x,
                position_y=y,
                warning_threshold_c=self.warning_threshold_c,
                throttle_threshold_c=self.throttle_threshold_c,
                critical_threshold_c=self.critical_threshold_c,
            ))

    def add_virtual_probe(
        self,
        name: str,
        layer: ThermalLayer,
        position_x: float,
        position_y: float,
        warning_threshold_c: float = 85.0,
        throttle_threshold_c: float = 95.0,
    ) -> VirtualProbe:
        """Add a virtual probe for monitoring

        Args:
            name: Probe name
            layer: Layer to monitor
            position_x: Normalized X position (0-1)
            position_y: Normalized Y position (0-1)
            warning_threshold_c: Warning threshold
            throttle_threshold_c: Throttle threshold

        Returns:
            Created VirtualProbe
        """
        probe = VirtualProbe(
            probe_id=len(self.probes),
            name=name,
            layer=layer,
            position_x=position_x,
            position_y=position_y,
            warning_threshold_c=warning_threshold_c,
            throttle_threshold_c=throttle_threshold_c,
        )
        self.probes.append(probe)
        return probe

    def update_layer_power(
        self,
        layer: ThermalLayer,
        power_mw: float,
        activity_factor: Optional[ActivityFactor] = None,
    ):
        """Update power dissipation for a layer

        Args:
            layer: Layer to update
            power_mw: Power in mW
            activity_factor: Optional activity factor for scaling
        """
        if layer not in self.layers:
            return

        layer_state = self.layers[layer]

        # Apply activity factor if provided
        if activity_factor is not None:
            effective_power = power_mw * activity_factor.effective_activity
        else:
            effective_power = power_mw

        layer_state.power_dissipation_mw = effective_power

    def update_channel_activity(
        self,
        channel_id: int,
        read_activity: float = 0.0,
        write_activity: float = 0.0,
        refresh_activity: float = 0.0,
    ):
        """Update activity factors for a channel

        Args:
            channel_id: Channel index
            read_activity: Read activity (0-1)
            write_activity: Write activity (0-1)
            refresh_activity: Refresh activity (0-1)
        """
        # Calculate idle fraction
        total = read_activity + write_activity + refresh_activity
        idle_fraction = max(0.0, 1.0 - total)

        self.activity_factors[channel_id] = ActivityFactor(
            read_activity=read_activity,
            write_activity=write_activity,
            refresh_activity=refresh_activity,
            idle_fraction=idle_fraction,
        )

    def simulate_step(self, time_ns: int, dt_ns: float = 1000.0):
        """Simulate one thermal step

        Args:
            time_ns: Current simulation time (ns)
            dt_ns: Time step (ns)
        """
        self.current_time_ns = time_ns

        # Update each layer
        for layer, layer_state in self.layers.items():
            self._update_layer_temperature(layer, layer_state, dt_ns)

        # Update virtual probes
        self._update_probes(time_ns)

        # Detect hotspots
        self._detect_hotspots(time_ns)

    def _update_layer_temperature(
        self,
        layer: ThermalLayer,
        layer_state: LayerTemperature,
        dt_ns: float,
    ):
        """Update temperature for a single layer using RC model

        Args:
            layer: Layer type
            layer_state: Current layer state
            dt_ns: Time step in ns
        """
        # Calculate temperature change
        # dT/dt = P * R / C (simplified)
        power_w = layer_state.power_dissipation_mw / 1000.0
        delta_t = power_w * layer_state.thermal_resistance

        # Apply thermal time constant (exponential settling)
        tau_ns = 1000.0  # 1 us thermal time constant
        dt_s = dt_ns * 1e-9
        alpha = 1.0 - math.exp(-dt_s / (tau_ns * 1e-9))

        # Update temperature
        layer_state.previous_temp_c = layer_state.temperature_c
        steady_state = self.ambient_temp_c + delta_t * 1000  # Convert to C
        layer_state.temperature_c = (
            layer_state.temperature_c * (1 - alpha) +
            steady_state * alpha
        )

        # Update rate of change
        dt_s_total = dt_s if layer_state.last_update_ns == 0 else (
            (self.current_time_ns - layer_state.last_update_ns) * 1e-9
        )
        if dt_s_total > 0:
            layer_state.rate_of_change = (
                (layer_state.temperature_c - layer_state.previous_temp_c) / dt_s_total
            )

        layer_state.last_update_ns = self.current_time_ns

        # Update peak temperature
        if layer_state.temperature_c > self.peak_temperature_c:
            self.peak_temperature_c = layer_state.temperature_c

    def _update_probes(self, time_ns: int):
        """Update all virtual probes

        Args:
            time_ns: Current simulation time
        """
        for probe in self.probes:
            if time_ns % probe.sampling_interval_ns == 0:
                # Get temperature from the layer
                layer_temp = self.layers.get(probe.layer)
                if layer_temp:
                    # Add spatial variation based on position
                    spatial_variation = (
                        2.0 * math.sin(probe.position_x * math.pi) *
                        math.sin(probe.position_y * math.pi)
                    )
                    measured_temp = layer_temp.temperature_c + spatial_variation

                    probe.measurements.append((time_ns, measured_temp))
                    probe.measurement_count += 1

                    # Keep bounded history
                    if len(probe.measurements) > 1000:
                        probe.measurements = probe.measurements[-500:]

    def _detect_hotspots(self, time_ns: int):
        """Detect hotspots across all layers and probes

        Args:
            time_ns: Current simulation time
        """
        # Check layer hotspots
        for layer, layer_state in self.layers.items():
            severity = self._get_severity(layer_state.temperature_c)
            if severity != HotspotSeverity.NONE:
                report = HotspotReport(
                    timestamp_ns=time_ns,
                    detected=True,
                    severity=severity,
                    temperature_c=layer_state.temperature_c,
                    threshold_c=self._get_threshold_for_severity(severity),
                    layer=layer,
                )
                self.hotspots.append(report)
                self.hotspot_detection_count += 1

        # Check probe hotspots
        for probe in self.probes:
            if probe.measurements:
                last_time, last_temp = probe.measurements[-1]
                severity = probe.get_severity(last_temp)
                if severity != HotspotSeverity.NONE:
                    report = HotspotReport(
                        timestamp_ns=last_time,
                        detected=True,
                        severity=severity,
                        temperature_c=last_temp,
                        threshold_c=probe.warning_threshold_c if severity == HotspotSeverity.WARNING
                                    else probe.throttle_threshold_c if severity == HotspotSeverity.THROTTLE
                                    else probe.critical_threshold_c,
                        layer=probe.layer,
                        probe_id=probe.probe_id,
                        location_x=probe.position_x,
                        location_y=probe.position_y,
                    )
                    self.hotspots.append(report)
                    self.hotspot_detection_count += 1

        # Keep bounded history
        if len(self.hotspots) > self.max_hotspots:
            self.hotspots = self.hotspots[-self.max_hotspots // 2:]

    def _get_severity(self, temperature_c: float) -> HotspotSeverity:
        """Determine hotspot severity for temperature"""
        if temperature_c >= self.emergency_threshold_c:
            return HotspotSeverity.EMERGENCY
        elif temperature_c >= self.critical_threshold_c:
            return HotspotSeverity.CRITICAL
        elif temperature_c >= self.throttle_threshold_c:
            return HotspotSeverity.THROTTLE
        elif temperature_c >= self.warning_threshold_c:
            return HotspotSeverity.WARNING
        return HotspotSeverity.NONE

    def _get_threshold_for_severity(self, severity: HotspotSeverity) -> float:
        """Get threshold temperature for severity level"""
        thresholds = {
            HotspotSeverity.WARNING: self.warning_threshold_c,
            HotspotSeverity.THROTTLE: self.throttle_threshold_c,
            HotspotSeverity.CRITICAL: self.critical_threshold_c,
            HotspotSeverity.EMERGENCY: self.emergency_threshold_c,
        }
        return thresholds.get(severity, self.warning_threshold_c)

    def get_layer_temperature(self, layer: ThermalLayer) -> float:
        """Get temperature for a specific layer

        Args:
            layer: Layer to query

        Returns:
            Temperature in Celsius
        """
        layer_state = self.layers.get(layer)
        if layer_state:
            return layer_state.temperature_c
        return self.ambient_temp_c

    def get_max_temperature(self) -> Tuple[ThermalLayer, float]:
        """Get maximum temperature across all layers

        Returns:
            (layer, temperature)
        """
        max_temp = self.ambient_temp_c
        max_layer = ThermalLayer.LOGIC_BASE_DIE

        for layer, state in self.layers.items():
            if state.temperature_c > max_temp:
                max_temp = state.temperature_c
                max_layer = layer

        return max_layer, max_temp

    def get_probe_temperature(self, probe_id: int) -> Optional[float]:
        """Get latest temperature reading from a probe

        Args:
            probe_id: Probe identifier

        Returns:
            Temperature or None if not found
        """
        probe = self.probes[probe_id] if probe_id < len(self.probes) else None
        if probe and probe.measurements:
            return probe.measurements[-1][1]
        return None

    def get_probe_readings(
        self,
        probe_id: int,
        num_samples: int = 10
    ) -> List[Tuple[int, float]]:
        """Get recent probe readings

        Args:
            probe_id: Probe identifier
            num_samples: Number of samples to return

        Returns:
            List of (time_ns, temperature) tuples
        """
        probe = self.probes[probe_id] if probe_id < len(self.probes) else None
        if probe:
            return probe.measurements[-num_samples:]
        return []

    def get_hotspot_reports(self, count: int = 10) -> List[HotspotReport]:
        """Get recent hotspot reports

        Args:
            count: Number of reports to return

        Returns:
            List of HotspotReport
        """
        return self.hotspots[-count:]

    def get_active_hotspots(self) -> List[HotspotReport]:
        """Get currently active hotspots (most recent per layer/probe)

        Returns:
            List of active HotspotReport
        """
        active = {}
        for report in reversed(self.hotspots):
            key = (report.layer, report.probe_id)
            if key not in active:
                active[key] = report

        return list(active.values())

    def calculate_tsv_thermal_drop(
        self,
        power_mw: float,
        tsv_count: int = None
    ) -> float:
        """Calculate thermal drop across TSV network

        Args:
            power_mw: Power in mW
            tsv_count: Number of TSVs (uses config default if None)

        Returns:
            Temperature drop in Celsius
        """
        if tsv_count is None:
            tsv_count = self.tsv_config.tsv_count

        effective_r = self.tsv_config.get_effective_resistance(tsv_count)
        power_w = power_mw / 1000.0
        return power_w * effective_r

    def get_thermal_summary(self) -> Dict:
        """Get comprehensive thermal summary

        Returns:
            Dictionary with thermal state
        """
        return {
            "time_ns": self.current_time_ns,
            "ambient_temp_c": self.ambient_temp_c,
            "peak_temp_c": self.peak_temperature_c,
            "max_layer": self.get_max_temperature()[0].value,
            "max_temp_c": self.get_max_temperature()[1],
            "warning_threshold_c": self.warning_threshold_c,
            "throttle_threshold_c": self.throttle_threshold_c,
            "critical_threshold_c": self.critical_threshold_c,
            "hotspot_count": self.hotspot_detection_count,
            "probe_count": len(self.probes),
            "layers": {
                layer.value: {
                    "temp_c": state.temperature_c,
                    "power_mw": state.power_dissipation_mw,
                    "rate_cps": state.rate_of_change,
                }
                for layer, state in self.layers.items()
            },
            "active_hotspots": [
                {
                    "layer": h.layer.value,
                    "severity": h.severity.value,
                    "temp_c": h.temperature_c,
                }
                for h in self.get_active_hotspots()
            ],
        }

    def reset(self):
        """Reset thermal model state"""
        self.current_time_ns = 0
        self.peak_temperature_c = self.ambient_temp_c
        self.hotspot_detection_count = 0
        self.hotspots = []

        # Reset layers
        for layer_state in self.layers.values():
            layer_state.temperature_c = self.ambient_temp_c
            layer_state.previous_temp_c = self.ambient_temp_c
            layer_state.rate_of_change = 0.0
            layer_state.power_dissipation_mw = 0.0
            layer_state.last_update_ns = 0

        # Reset probes
        for probe in self.probes:
            probe.measurements = []
            probe.measurement_count = 0


# Factory functions

def create_layered_thermal_model(
    ambient_temp_c: float = 45.0,
    num_channels: int = 32,
) -> LayeredThermalModel:
    """Create layered thermal model for HBM4

    Args:
        ambient_temp_c: Ambient temperature
        num_channels: Number of HBM channels

    Returns:
        Configured LayeredThermalModel
    """
    return LayeredThermalModel(
        ambient_temp_c=ambient_temp_c,
        num_channels=num_channels,
    )


def create_hbm4_thermal_model(
    warning_threshold_c: float = 85.0,
    throttle_threshold_c: float = 95.0,
) -> LayeredThermalModel:
    """Create thermal model with HBM4 specification thresholds

    Args:
        warning_threshold_c: Warning threshold (default 85C)
        throttle_threshold_c: Throttle threshold (default 95C)

    Returns:
        LayeredThermalModel with HBM4 thresholds
    """
    model = create_layered_thermal_model()
    model.warning_threshold_c = warning_threshold_c
    model.throttle_threshold_c = throttle_threshold_c

    # Update probe thresholds
    for probe in model.probes:
        probe.warning_threshold_c = warning_threshold_c
        probe.throttle_threshold_c = throttle_threshold_c

    return model
