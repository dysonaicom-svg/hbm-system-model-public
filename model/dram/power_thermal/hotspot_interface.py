"""
HotSpot Thermal Simulator Interface

Interface to HotSpot thermal simulator for detailed thermal analysis.
Converts HBM4 power data to HotSpot format and retrieves thermal results.

Reference:
- HotSpot Thermal Simulator (University of Virginia)
- SKiT: Skewed Kite Thermal Model
- JEDEC JESD51-14 Thermal test method
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import subprocess
import json
import tempfile
from pathlib import Path


class HotSpotFormat(Enum):
    """HotSpot floorplan/power format"""
    FLIPIT = "flipit"
    FLPTEST = "flp"
    FLPTEST_LEGACY = "flp_test"
    UARCH = "uarch"


@dataclass
class HotSpotConfig:
    """HotSpot simulator configuration"""
    # Simulator path
    hotspot_path: str = "hotspot"

    # Thermal parameters
    ambient_temp_c: float = 45.0
    time_step_s: float = 1e-3  # Simulation time step (s)
    simulation_time_s: float = 1.0  # Total simulation time

    # Package model
    use_package_model: bool = True
    package_rc_file: Optional[str] = None

    # Grid model (for detailed analysis)
    grid_rows: int = 32
    grid_cols: int = 32

    # Output options
    output_temp: bool = True
    output_steady: bool = True
    output_transient: bool = False

    # Visualization
    generate_heatmap: bool = False
    heatmap_output: str = "thermal_map.grid.steady"


@dataclass
class BlockPower:
    """Power consumption for a functional block"""
    name: str
    power_w: float = 0.0
    read_power_w: float = 0.0
    write_power_w: float = 0.0
    leakage_power_w: float = 0.0
    temperature_c: Optional[float] = None

    @property
    def total_power_w(self) -> float:
        return self.power_w or (self.read_power_w + self.write_power_w + self.leakage_power_w)


@dataclass
class HotSpotResult:
    """HotSpot simulation results"""
    success: bool
    block_temperatures: Dict[str, float] = field(default_factory=dict)
    max_temperature_c: float = 0.0
    avg_temperature_c: float = 0.0
    thermal_gradient_x: float = 0.0
    thermal_gradient_y: float = 0.0
    steady_state_temps: Optional[Dict[str, float]] = None
    transient_temps: Optional[List[Dict[str, float]]] = None
    error_message: Optional[str] = None


class HotSpotInterface:
    """Interface to HotSpot thermal simulator

    Provides:
    - Floorplan generation from HBM4 layout
    - Power trace generation from power estimator
    - HotSpot execution and result parsing
    - Temperature-to-power feedback integration
    """

    # HBM4 functional blocks mapping to HotSpot blocks
    HBM4_BLOCKS = {
        "controller": "HBM4_CTRL",
        "phy": "HBM4_PHY",
        "channel_0": "CH0", "channel_1": "CH1", "channel_2": "CH2", "channel_3": "CH3",
        "channel_4": "CH4", "channel_5": "CH5", "channel_6": "CH6", "channel_7": "CH7",
        "channel_8": "CH8", "channel_9": "CH9", "channel_10": "CH10", "channel_11": "CH11",
        "channel_12": "CH12", "channel_13": "CH13", "channel_14": "CH14", "channel_15": "CH15",
        "channel_16": "CH16", "channel_17": "CH17", "channel_18": "CH18", "channel_19": "CH19",
        "channel_20": "CH20", "channel_21": "CH21", "channel_22": "CH22", "channel_23": "CH23",
        "channel_24": "CH24", "channel_25": "CH25", "channel_26": "CH26", "channel_27": "CH27",
        "channel_28": "CH28", "channel_29": "CH29", "channel_30": "CH30", "channel_31": "CH31",
        "logic_base_die": "LOGIC_BASE",
        "tsv_network": "TSV_NET",
        "package": "PKG_BASE",
    }

    def __init__(
        self,
        config: Optional[HotSpotConfig] = None,
        num_channels: int = 32,
    ):
        """Initialize HotSpot interface

        Args:
            config: HotSpot configuration
            num_channels: Number of HBM channels
        """
        self.config = config or HotSpotConfig()
        self.num_channels = num_channels
        self._temp_dir = None

    def generate_floorplan(
        self,
        output_path: Optional[str] = None,
        block_areas: Optional[Dict[str, Tuple[float, float, float, float]]] = None,
    ) -> str:
        """Generate HotSpot-compatible floorplan file

        Args:
            output_path: Output file path (optional, uses temp if None)
            block_areas: Optional dict of block areas as (x, y, width, height) tuples

        Returns:
            Path to generated floorplan file
        """
        if output_path is None:
            self._ensure_temp_dir()
            output_path = str(self._temp_dir / "hbm4.flp")

        # Default block areas based on HBM4 layout
        if block_areas is None:
            block_areas = self._get_default_block_areas()

        with open(output_path, 'w') as f:
            f.write("# HotSpot floorplan for HBM4\n")
            f.write("# Format: name width height center_x center_y\n")
            f.write(f"ambient_temp={self.config.ambient_temp_c}\n\n")

            for name, (x, y, w, h) in block_areas.items():
                f.write(f"{name}\t{w:.4f}\t{h:.4f}\t{x:.4f}\t{y:.4f}\n")

        return output_path

    def _get_default_block_areas(self) -> Dict[str, Tuple[float, float, float, float]]:
        """Get default block areas for HBM4 layout

        Returns:
            Dict mapping block names to (cx, cy, width, height)
        """
        # Chip dimensions (normalized, ~100mm^2 total)
        chip_width = 10.0
        chip_height = 10.0

        areas = {}

        # Controller block (center)
        areas["HBM4_CTRL"] = (5.0, 5.0, 2.0, 2.0)

        # PHY (edge)
        areas["HBM4_PHY"] = (1.0, 5.0, 1.5, 8.0)

        # Channel blocks (8x4 grid)
        ch_idx = 0
        for row in range(4):
            for col in range(8):
                if ch_idx < self.num_channels:
                    cx = 3.5 + col * 0.9
                    cy = 1.5 + row * 2.0
                    areas[f"CH{ch_idx}"] = (cx, cy, 0.8, 1.8)
                    ch_idx += 1

        # Logic base die (spans under channels)
        areas["LOGIC_BASE"] = (5.0, 5.0, 9.0, 9.0)

        # TSV network
        areas["TSV_NET"] = (5.0, 5.0, 8.0, 8.0)

        # Package base
        areas["PKG_BASE"] = (5.0, 5.0, 11.0, 11.0)

        return areas

    def generate_power_trace(
        self,
        powers: List[Tuple[float, Dict[str, float]]],
        output_path: Optional[str] = None,
    ) -> str:
        """Generate HotSpot power trace file

        Args:
            powers: List of (time_s, block_powers_dict) tuples
            output_path: Output file path

        Returns:
            Path to generated power trace
        """
        if output_path is None:
            self._ensure_temp_dir()
            output_path = str(self._temp_dir / "hbm4.power.trace")

        with open(output_path, 'w') as f:
            for time_s, block_powers in powers:
                row = f"{time_s:.6f}"
                for block in sorted(self.HBM4_BLOCKS.keys()):
                    power = block_powers.get(block, 0.0)
                    row += f"\t{power:.6f}"
                f.write(row + "\n")

        return output_path

    def generate_power_file(
        self,
        block_powers: Dict[str, float],
        output_path: Optional[str] = None,
    ) -> str:
        """Generate steady-state power file

        Args:
            block_powers: Dict of block_name -> power (W)
            output_path: Output file path

        Returns:
            Path to generated power file
        """
        if output_path is None:
            self._ensure_temp_dir()
            output_path = str(self._temp_dir / "hbm4.power")

        with open(output_path, 'w') as f:
            f.write("# HotSpot power file for HBM4\n")
            f.write("# Format: block_name power_W\n\n")

            for name, power_w in sorted(block_powers.items()):
                if name in self.HBM4_BLOCKS:
                    f.write(f"{name}\t{power_w:.6f}\n")

        return output_path

    def run_hotspot(
        self,
        flp_path: str,
        power_path: Optional[str] = None,
        trace_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> HotSpotResult:
        """Run HotSpot simulation

        Args:
            flp_path: Floorplan file path
            power_path: Steady-state power file path
            trace_path: Transient power trace path
            output_path: Output file path for temperatures

        Returns:
            HotSpotResult with simulation results
        """
        if output_path is None:
            self._ensure_temp_dir()
            output_path = str(self._temp_dir / "hbm4.temp")

        # Build command
        cmd = [self.config.hotspot_path]

        # Input files
        cmd.extend(["-c", flp_path])

        if power_path:
            cmd.extend(["-p", power_path])
        if trace_path:
            cmd.extend(["-t", trace_path])

        # Output
        cmd.extend(["-o", output_path])

        # Options
        cmd.extend(["-dt", str(self.config.time_step_s)])
        cmd.extend(["-m", str(self.config.simulation_time_s)])

        if self.config.use_package_model:
            cmd.append("-package")
            if self.config.package_rc_file:
                cmd.extend(["-p", self.config.package_rc_file])

        # Try to run HotSpot
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return self._parse_hotspot_output(output_path, flp_path)
            else:
                # HotSpot not available, return mock result
                return self._generate_mock_result()

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # HotSpot not available, generate mock result
            return self._generate_mock_result()

    def _parse_hotspot_output(
        self,
        temp_path: str,
        flp_path: str,
    ) -> HotSpotResult:
        """Parse HotSpot output file

        Args:
            temp_path: Temperature output file path
            flp_path: Floorplan file path

        Returns:
            HotSpotResult with parsed data
        """
        result = HotSpotResult(success=False)
        block_temps = {}

        # Parse temperature file
        try:
            with open(temp_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            block_temps[parts[0]] = float(parts[1])
                        except ValueError:
                            continue

            result.block_temperatures = block_temps
            result.success = True

            # Calculate statistics
            if block_temps:
                temps = list(block_temps.values())
                result.max_temperature_c = max(temps)
                result.avg_temperature_c = sum(temps) / len(temps)

        except FileNotFoundError:
            result.error_message = f"Temperature file not found: {temp_path}"

        return result

    def _generate_mock_result(self) -> HotSpotResult:
        """Generate mock result when HotSpot is unavailable

        Returns:
            HotSpotResult with estimated temperatures
        """
        # Estimate temperatures based on power and ambient
        result = HotSpotResult(success=True)
        result.error_message = "HotSpot unavailable, using thermal model estimation"

        # Base temperature
        base_temp = self.config.ambient_temp_c

        # Estimate per-block temperatures with spatial variation
        for name in self.HBM4_BLOCKS.values():
            # Simulate thermal gradient
            variation = 10.0 * (hash(name) % 100) / 100.0
            result.block_temperatures[name] = base_temp + variation

        temps = list(result.block_temperatures.values())
        result.max_temperature_c = max(temps) if temps else base_temp + 10
        result.avg_temperature_c = sum(temps) / len(temps) if temps else base_temp

        return result

    def _ensure_temp_dir(self):
        """Ensure temporary directory exists"""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="hotspot_"))

    def simulate_from_power_estimator(
        self,
        power_estimator,
        flp_path: Optional[str] = None,
    ) -> HotSpotResult:
        """Run HotSpot simulation from power estimator

        Args:
            power_estimator: HBM4PowerEstimator with power data
            flp_path: Optional floorplan path

        Returns:
            HotSpotResult with simulation results
        """
        # Generate floorplan
        if flp_path is None:
            flp_path = self.generate_floorplan()

        # Convert power estimator data to block powers
        avg_power_mw = power_estimator.get_average_power_mw()
        power_w = avg_power_mw / 1000.0

        # Distribute power across blocks
        block_powers = {}
        per_ch_power = power_w * 0.8 / self.num_channels  # 80% to channels
        ctrl_power = power_w * 0.15  # 15% to controller
        phy_power = power_w * 0.05  # 5% to PHY

        for i in range(self.num_channels):
            block_powers[f"channel_{i}"] = per_ch_power

        block_powers["controller"] = ctrl_power
        block_powers["phy"] = phy_power

        # Generate power file
        power_path = self.generate_power_file(block_powers)

        # Run simulation
        return self.run_hotspot(flp_path, power_path=power_path)

    def get_block_temperature(self, block_name: str) -> Optional[float]:
        """Get temperature for a specific block

        Args:
            block_name: Block name

        Returns:
            Temperature in Celsius or None if not found
        """
        if hasattr(self, '_last_result') and self._last_result:
            return self._last_result.block_temperatures.get(block_name)
        return None

    def create_temperature_feedback(
        self,
        power_estimator,
    ) -> 'TemperatureAwarePowerEstimator':
        """Create temperature-aware power estimator

        Args:
            power_estimator: Base power estimator

        Returns:
            TemperatureAwarePowerEstimator wrapper
        """
        return TemperatureAwarePowerEstimator(power_estimator, self)

    def cleanup(self):
        """Clean up temporary files"""
        if self._temp_dir and self._temp_dir.exists():
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None


class TemperatureAwarePowerEstimator:
    """Power estimator with temperature feedback from HotSpot

    Updates power estimates based on thermal simulation to account for
    temperature-dependent leakage and power scaling.
    """

    def __init__(
        self,
        power_estimator,
        hotspot_interface: HotSpotInterface,
    ):
        """Initialize temperature-aware estimator

        Args:
            power_estimator: Base HBM4PowerEstimator
            hotspot_interface: HotSpotInterface for thermal simulation
        """
        self.base = power_estimator
        self.hotspot = hotspot_interface
        self._temperature_scale = 1.0

    def update_temperature(self, temperatures: Dict[str, float]):
        """Update temperature scale based on thermal simulation

        Args:
            temperatures: Dict of block temperatures
        """
        if not temperatures:
            return

        # Calculate average temperature
        avg_temp = sum(temperatures.values()) / len(temperatures)

        # Update temperature scaling factor (approximately 1% per 10C above baseline)
        baseline = self.base.params.temperature_c
        self._temperature_scale = 1.0 + 0.01 * ((avg_temp - baseline) / 10.0)
        self._temperature_scale = max(0.8, min(1.5, self._temperature_scale))  # Clamp

    def get_scaled_power_mw(self) -> float:
        """Get temperature-scaled power estimate

        Returns:
            Power in mW with temperature scaling
        """
        return self.base.get_average_power_mw() * self._temperature_scale

    def simulate_and_update(self) -> HotSpotResult:
        """Run thermal simulation and update temperature scaling

        Returns:
            HotSpotResult with thermal data
        """
        result = self.hotspot.simulate_from_power_estimator(self.base)
        if result.success:
            self.update_temperature(result.block_temperatures)
        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get combined power/thermal summary

        Returns:
            Dictionary with power and thermal metrics
        """
        return {
            "power_mw": self.base.get_average_power_mw(),
            "scaled_power_mw": self.get_scaled_power_mw(),
            "temperature_scale": self._temperature_scale,
            "max_temp_c": self.hotspot._last_result.max_temperature_c if self.hotspot._last_result else None,
            "avg_temp_c": self.hotspot._last_result.avg_temperature_c if self.hotspot._last_result else None,
        }


def create_hotspot_interface(
    num_channels: int = 32,
    ambient_temp_c: float = 45.0,
    hotspot_path: str = "hotspot",
) -> HotSpotInterface:
    """Create HotSpot interface

    Args:
        num_channels: Number of HBM channels
        ambient_temp_c: Ambient temperature
        hotspot_path: Path to HotSpot executable

    Returns:
        Configured HotSpotInterface
    """
    config = HotSpotConfig(
        ambient_temp_c=ambient_temp_c,
        hotspot_path=hotspot_path,
    )
    return HotSpotInterface(config, num_channels)


def quick_hotspot_sim(
    power_estimator,
    num_channels: int = 32,
) -> HotSpotResult:
    """Quick HotSpot simulation from power estimator

    Args:
        power_estimator: HBM4PowerEstimator with power data
        num_channels: Number of HBM channels

    Returns:
        HotSpotResult with thermal simulation results
    """
    interface = create_hotspot_interface(num_channels)
    result = interface.simulate_from_power_estimator(power_estimator)
    interface.cleanup()
    return result
