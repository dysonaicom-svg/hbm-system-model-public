"""
Power Profile Exporter

Exports power profiles to JSON/CSV formats for analysis and visualization.
Supports HBM4 power data including per-channel breakdown, command statistics,
and thermal estimates.

Reference:
- JEDEC JESD270-4A HBM4 specification
- Power measurement standards from JESD51 series
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import csv
from pathlib import Path

from model.dram.power_estimator import (
    HBM4PowerEstimator,
    PowerReport,
    PowerParameters,
    PowerState,
    CommandType,
    ChannelPower,
    CommandEnergy,
)
from model.dram.thermal_model import (
    LayeredThermalModel,
    ThermalLayer,
    HotspotReport,
    VirtualProbe,
)


@dataclass
class ExportConfig:
    """Configuration for power profile export"""
    include_raw_data: bool = True
    include_summary: bool = True
    include_per_channel: bool = True
    include_commands: bool = True
    include_thermal: bool = True
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    precision: int = 4


class PowerProfileExporter:
    """Export power profiles to JSON/CSV formats

    Supports:
    - JSON export for programmatic consumption
    - CSV export for spreadsheet analysis
    - Per-channel power breakdown
    - Command energy statistics
    - Thermal data integration
    """

    def __init__(
        self,
        power_estimator: HBM4PowerEstimator,
        thermal_model: Optional[LayeredThermalModel] = None,
        config: Optional[ExportConfig] = None,
    ):
        """Initialize exporter

        Args:
            power_estimator: Source power estimator
            thermal_model: Optional thermal model for combined export
            config: Export configuration
        """
        self.power = power_estimator
        self.thermal = thermal_model
        self.config = config or ExportConfig()

    def export_json(
        self,
        filepath: str,
        include_thermal: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Export power profile to JSON

        Args:
            filepath: Output file path
            include_thermal: Override thermal inclusion (default: config value)

        Returns:
            Exported data dictionary
        """
        if include_thermal is None:
            include_thermal = self.config.include_thermal

        report = self.power.generate_report()
        data = self._build_json_data(report, include_thermal)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return data

    def _build_json_data(
        self,
        report: PowerReport,
        include_thermal: bool,
    ) -> Dict[str, Any]:
        """Build JSON data structure from power report

        Args:
            report: Power report to export
            include_thermal: Include thermal data

        Returns:
            JSON-serializable dictionary
        """
        data = {
            "metadata": {
                "timestamp": datetime.now().strftime(self.config.timestamp_format),
                "format_version": "1.0",
                "hbm_version": "HBM4",
                "num_channels": self.power.num_channels,
                "data_rate_gtps": self.power.data_rate_gtps,
            },
            "power": {
                "total_mw": round(report.total_power_mw, self.config.precision),
                "average_mw": round(report.average_power_mw, self.config.precision),
                "peak_mw": round(report.peak_power_mw, self.config.precision),
                "idle_mw": round(report.idle_power_mw, self.config.precision),
            },
            "energy": {
                "total_pj": round(report.total_energy_pj, self.config.precision),
                "total_mj": round(report.total_energy_mj, self.config.precision),
            },
        }

        if self.config.include_summary:
            data["summary"] = self.power.get_summary()

        if self.config.include_per_channel and report.channel_powers:
            data["channels"] = [
                {k: round(v, self.config.precision) if isinstance(v, float) else v
                 for k, v in ch.items()}
                for ch in report.channel_powers
            ]

        if self.config.include_commands:
            data["commands"] = {
                "counts": report.command_counts,
                "energies": {k: round(v, self.config.precision)
                            for k, v in report.command_energies.items()},
            }

        if include_thermal and self.thermal:
            data["thermal"] = self._get_thermal_export_data()

        if self.config.include_raw_data:
            data["raw"] = self._get_raw_data_export()

        return data

    def _get_thermal_export_data(self) -> Dict[str, Any]:
        """Get thermal data for export"""
        summary = self.thermal.get_thermal_summary()
        return {
            "ambient_temp_c": round(summary["ambient_temp_c"], self.config.precision),
            "peak_temp_c": round(summary["peak_temp_c"], self.config.precision),
            "max_layer": summary["max_layer"],
            "layers": {
                k: {kk: round(vv, self.config.precision) if isinstance(vv, float) else vv
                    for kk, vv in v.items()}
                for k, v in summary.get("layers", {}).items()
            },
            "hotspots": [
                {
                    "layer": h.layer.value if isinstance(h.layer, ThermalLayer) else h.layer,
                    "severity": h.severity.value if hasattr(h.severity, 'value') else h.severity,
                    "temp_c": round(h.temperature_c, self.config.precision),
                }
                for h in self.thermal.get_active_hotspots()
            ],
        }

    def _get_raw_data_export(self) -> Dict[str, Any]:
        """Get raw data for export"""
        return {
            "current_cycle": self.power.current_cycle,
            "peak_power_mw": round(self.power.peak_power_mw, self.config.precision),
            "energy_breakdown_pj": {
                k: round(v, self.config.precision)
                for k, v in self.power.get_energy_breakdown_pj().items()
            },
            "command_counts": self.power.get_command_count_breakdown(),
        }

    def export_csv(
        self,
        filepath: str,
        export_type: str = "summary",
    ) -> None:
        """Export power profile to CSV

        Args:
            filepath: Output file path
            export_type: Type of export ("summary", "channels", "commands", "all")
        """
        export_type = export_type.lower()

        if export_type == "summary":
            self._export_csv_summary(filepath)
        elif export_type == "channels":
            self._export_csv_channels(filepath)
        elif export_type == "commands":
            self._export_csv_commands(filepath)
        elif export_type == "all":
            # Export all types with suffixes
            self._export_csv_summary(filepath.replace(".csv", "_summary.csv"))
            self._export_csv_channels(filepath.replace(".csv", "_channels.csv"))
            self._export_csv_commands(filepath.replace(".csv", "_commands.csv"))
        else:
            raise ValueError(f"Unknown export type: {export_type}")

    def _export_csv_summary(self, filepath: str) -> None:
        """Export summary data to CSV"""
        report = self.power.generate_report()

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value", "Unit"])

            # Power metrics
            writer.writerow(["Total Power", f"{report.total_power_mw:.4f}", "mW"])
            writer.writerow(["Average Power", f"{report.average_power_mw:.4f}", "mW"])
            writer.writerow(["Peak Power", f"{report.peak_power_mw:.4f}", "mW"])
            writer.writerow(["Idle Power", f"{report.idle_power_mw:.4f}", "mW"])

            # Energy metrics
            writer.writerow(["Total Energy", f"{report.total_energy_pj:.4f}", "pJ"])
            writer.writerow(["Total Energy", f"{report.total_energy_mj:.6f}", "mJ"])

            # Efficiency
            writer.writerow(["Bandwidth Efficiency", f"{report.bandwidth_efficiency:.2f}", "%"])
            writer.writerow(["Power Efficiency", f"{report.power_efficiency:.2f}", "%"])

            # Thermal
            if report.thermal:
                writer.writerow(["Junction Temp", f"{report.thermal.get('junction_temp_c', 0):.1f}", "C"])
                writer.writerow(["Ambient Temp", f"{report.thermal.get('ambient_temp_c', 0):.1f}", "C"])

    def _export_csv_channels(self, filepath: str) -> None:
        """Export per-channel data to CSV"""
        report = self.power.generate_report()

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Channel", "Average Power (mW)", "Peak Power (mW)", "RMS Power (mW)"])

            for i, ch in enumerate(report.channel_powers):
                writer.writerow([
                    i,
                    f"{ch.get('average_mw', 0):.4f}",
                    f"{ch.get('peak_mw', 0):.4f}",
                    f"{ch.get('rms_mw', 0):.4f}",
                ])

    def _export_csv_commands(self, filepath: str) -> None:
        """Export command statistics to CSV"""
        report = self.power.generate_report()

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Command", "Count", "Total Energy (pJ)", "Energy Percentage (%)"])

            total_energy = sum(report.command_energies.values()) or 1
            total_commands = sum(report.command_counts.values()) or 1

            for cmd, count in sorted(report.command_counts.items(), key=lambda x: -x[1]):
                energy = report.command_energies.get(cmd, 0)
                pct = (energy / total_energy) * 100 if total_energy > 0 else 0
                writer.writerow([
                    cmd,
                    count,
                    f"{energy:.4f}",
                    f"{pct:.2f}",
                ])

    def export_combined(
        self,
        base_path: str,
        include_thermal: bool = True,
    ) -> Dict[str, str]:
        """Export all power/thermal data in multiple formats

        Args:
            base_path: Base path for output files (without extension)
            include_thermal: Include thermal data

        Returns:
            Dictionary mapping export type to file path
        """
        base = Path(base_path)
        results = {}

        # JSON export
        json_path = f"{base}.json"
        self.export_json(json_path, include_thermal=include_thermal)
        results["json"] = json_path

        # CSV exports
        self._export_csv_summary(f"{base}_summary.csv")
        results["csv_summary"] = f"{base}_summary.csv"

        self._export_csv_channels(f"{base}_channels.csv")
        results["csv_channels"] = f"{base}_channels.csv"

        self._export_csv_commands(f"{base}_commands.csv")
        results["csv_commands"] = f"{base}_commands.csv"

        return results

    def get_export_data(self, include_thermal: bool = True) -> Dict[str, Any]:
        """Get exportable data as dictionary

        Args:
            include_thermal: Include thermal data

        Returns:
            Exportable data dictionary
        """
        report = self.power.generate_report()
        return self._build_json_data(report, include_thermal)


class PowerProfileMerger:
    """Merge multiple power profiles for comparison"""

    @staticmethod
    def merge_json_profiles(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple JSON power profiles

        Args:
            profiles: List of power profile dictionaries

        Returns:
            Merged profile with comparison data
        """
        if not profiles:
            return {}

        merged = {
            "metadata": profiles[0].get("metadata", {}),
            "comparison": {},
            "profiles": profiles,
        }

        # Compare power metrics
        powers = [p.get("power", {}) for p in profiles]
        merged["comparison"]["power"] = {
            "total_mw": {
                "min": min((p.get("total_mw", 0) for p in powers), default=0),
                "max": max((p.get("total_mw", 0) for p in powers), default=0),
                "avg": sum(p.get("total_mw", 0) for p in powers) / len(powers) if powers else 0,
            },
            "peak_mw": {
                "min": min((p.get("peak_mw", 0) for p in powers), default=0),
                "max": max((p.get("peak_mw", 0) for p in powers), default=0),
            },
        }

        return merged

    @staticmethod
    def merge_csv_profiles(csv_paths: List[str]) -> Dict[str, List[Dict]]:
        """Merge multiple CSV power profiles

        Args:
            csv_paths: List of CSV file paths

        Returns:
            Merged data by metric type
        """
        merged = {"summary": [], "channels": [], "commands": []}

        for path in csv_paths:
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    continue

                # Determine type by header
                if "Channel" in rows[0]:
                    merged["channels"].extend(rows)
                elif "Command" in rows[0]:
                    merged["commands"].extend(rows)
                else:
                    merged["summary"].extend(rows)

        return merged


def create_exporter(
    power_estimator: HBM4PowerEstimator,
    thermal_model: Optional[LayeredThermalModel] = None,
    **config_kwargs,
) -> PowerProfileExporter:
    """Create power profile exporter

    Args:
        power_estimator: Source power estimator
        thermal_model: Optional thermal model
        **config_kwargs: Config overrides

    Returns:
        Configured PowerProfileExporter
    """
    config = ExportConfig(**config_kwargs)
    return PowerProfileExporter(power_estimator, thermal_model, config)


def quick_export(
    power_estimator: HBM4PowerEstimator,
    output_path: str,
    thermal_model: Optional[LayeredThermalModel] = None,
) -> str:
    """Quick export power profile to JSON

    Args:
        power_estimator: Source power estimator
        output_path: Output file path
        thermal_model: Optional thermal model

    Returns:
        Output file path
    """
    exporter = PowerProfileExporter(power_estimator, thermal_model)
    exporter.export_json(output_path)
    return output_path
