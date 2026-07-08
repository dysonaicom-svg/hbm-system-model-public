"""Configuration Schema Definitions

JSON Schema definitions for HBM4 configuration validation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum


class ConfigFormat(Enum):
    """Supported configuration file formats"""
    YAML = "yaml"
    JSON = "json"
    TOML = "toml"


@dataclass
class HBM4ConfigSchema:
    """HBM4 controller configuration schema"""
    channels: int = 32
    data_rate_gbps: int = 16
    queue_depth: int = 128
    address_mapping: str = "rbc"  # rbc, bcr, crb
    qos_levels: int = 16
    refresh_mode: str = "all_bank"  # all_bank, per_bank, drfm


@dataclass
class SimulationConfigSchema:
    """Simulation configuration schema"""
    duration_us: float = 100.0
    traffic_pattern: str = "random"  # random, sequential, stride, hotspot
    request_rate: float = 0.8
    read_ratio: float = 0.7
    max_requests_per_cycle: int = 4
    seed: Optional[int] = None


@dataclass
class ChannelConfigSchema:
    """Channel configuration schema"""
    enabled: bool = True
    pseudo_channels: int = 2
    bank_groups: int = 8
    banks_per_group: int = 16
    rows_per_bank: int = 65536
    columns_per_row: int = 256


@dataclass
class PHYConfigSchema:
    """PHY configuration schema"""
    training_enabled: bool = True
    pre_emphasis: bool = True
    ctle_enabled: bool = True
    dfe_enabled: bool = False


@dataclass
class DVFSConfigSchema:
    """DVFS configuration schema"""
    enable: bool = False
    voltage_mv: int = 800
    frequency_mhz: int = 1600
    profiles: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PluginConfigSchema:
    """Plugin configuration schema"""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FullConfigSchema:
    """Complete system configuration schema"""
    hbm4: HBM4ConfigSchema = field(default_factory=HBM4ConfigSchema)
    simulation: SimulationConfigSchema = field(default_factory=SimulationConfigSchema)
    channels: Dict[int, ChannelConfigSchema] = field(default_factory=dict)
    phy: PHYConfigSchema = field(default_factory=PHYConfigSchema)
    dvfs: DVFSConfigSchema = field(default_factory=DVFSConfigSchema)
    plugins: List[PluginConfigSchema] = field(default_factory=list)


class ValidationError(Exception):
    """Configuration validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class ConfigSchema:
    """Configuration schema validator"""

    SCHEMA = {
        "type": "object",
        "properties": {
            "hbm4": {
                "type": "object",
                "properties": {
                    "channels": {"type": "integer", "minimum": 1, "maximum": 64},
                    "data_rate_gbps": {"type": "integer", "enum": [8, 12, 16]},
                    "queue_depth": {"type": "integer", "minimum": 1, "maximum": 1024},
                    "address_mapping": {"type": "string", "enum": ["rbc", "bcr", "crb"]},
                    "qos_levels": {"type": "integer", "minimum": 1, "maximum": 16},
                    "refresh_mode": {"type": "string", "enum": ["all_bank", "per_bank", "drfm"]},
                },
            },
            "simulation": {
                "type": "object",
                "properties": {
                    "duration_us": {"type": "number", "minimum": 0},
                    "traffic_pattern": {"type": "string", "enum": ["random", "sequential", "stride", "hotspot"]},
                    "request_rate": {"type": "number", "minimum": 0, "maximum": 1},
                    "read_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                    "max_requests_per_cycle": {"type": "integer", "minimum": 1},
                    "seed": {"type": ["integer", "null"]},
                },
            },
            "dvfs": {
                "type": "object",
                "properties": {
                    "enable": {"type": "boolean"},
                    "voltage_mv": {"type": "integer", "minimum": 400, "maximum": 1200},
                    "frequency_mhz": {"type": "integer", "minimum": 400, "maximum": 3200},
                },
            },
            "plugins": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "enabled": {"type": "boolean"},
                        "config": {"type": "object"},
                    },
                    "required": ["name"],
                },
            },
        },
    }

    @classmethod
    def validate(cls, config: Dict[str, Any]) -> List[ValidationError]:
        """Validate configuration against schema"""
        errors = []

        # Check required top-level keys
        if "hbm4" not in config and "simulation" not in config:
            errors.append(ValidationError("At least one of 'hbm4' or 'simulation' must be present"))

        # Validate HBM4 config
        if "hbm4" in config:
            errors.extend(cls._validate_hbm4(config["hbm4"]))

        # Validate simulation config
        if "simulation" in config:
            errors.extend(cls._validate_simulation(config["simulation"]))

        # Validate DVFS config
        if "dvfs" in config:
            errors.extend(cls._validate_dvfs(config["dvfs"]))

        # Validate plugins
        if "plugins" in config:
            errors.extend(cls._validate_plugins(config["plugins"]))

        return errors

    @classmethod
    def _validate_hbm4(cls, hbm4: Dict[str, Any]) -> List[ValidationError]:
        errors = []

        if "channels" in hbm4:
            if not 1 <= hbm4["channels"] <= 64:
                errors.append(ValidationError(
                    "channels must be between 1 and 64",
                    field="hbm4.channels"
                ))

        if "data_rate_gbps" in hbm4:
            if hbm4["data_rate_gbps"] not in [8, 12, 16]:
                errors.append(ValidationError(
                    "data_rate_gbps must be 8, 12, or 16",
                    field="hbm4.data_rate_gbps"
                ))

        if "queue_depth" in hbm4:
            if not 1 <= hbm4["queue_depth"] <= 1024:
                errors.append(ValidationError(
                    "queue_depth must be between 1 and 1024",
                    field="hbm4.queue_depth"
                ))

        if "address_mapping" in hbm4:
            if hbm4["address_mapping"] not in ["rbc", "bcr", "crb"]:
                errors.append(ValidationError(
                    "address_mapping must be 'rbc', 'bcr', or 'crb'",
                    field="hbm4.address_mapping"
                ))

        return errors

    @classmethod
    def _validate_simulation(cls, sim: Dict[str, Any]) -> List[ValidationError]:
        errors = []

        if "duration_us" in sim:
            if sim["duration_us"] < 0:
                errors.append(ValidationError(
                    "duration_us must be non-negative",
                    field="simulation.duration_us"
                ))

        if "traffic_pattern" in sim:
            if sim["traffic_pattern"] not in ["random", "sequential", "stride", "hotspot"]:
                errors.append(ValidationError(
                    "traffic_pattern must be 'random', 'sequential', 'stride', or 'hotspot'",
                    field="simulation.traffic_pattern"
                ))

        if "request_rate" in sim:
            if not 0 <= sim["request_rate"] <= 1:
                errors.append(ValidationError(
                    "request_rate must be between 0 and 1",
                    field="simulation.request_rate"
                ))

        return errors

    @classmethod
    def _validate_dvfs(cls, dvfs: Dict[str, Any]) -> List[ValidationError]:
        errors = []

        if "voltage_mv" in dvfs:
            if not 400 <= dvfs["voltage_mv"] <= 1200:
                errors.append(ValidationError(
                    "voltage_mv must be between 400 and 1200 mV",
                    field="dvfs.voltage_mv"
                ))

        if "frequency_mhz" in dvfs:
            if not 400 <= dvfs["frequency_mhz"] <= 3200:
                errors.append(ValidationError(
                    "frequency_mhz must be between 400 and 3200 MHz",
                    field="dvfs.frequency_mhz"
                ))

        return errors

    @classmethod
    def _validate_plugins(cls, plugins: List[Any]) -> List[ValidationError]:
        errors = []

        for i, plugin in enumerate(plugins):
            if not isinstance(plugin, dict):
                errors.append(ValidationError(
                    f"Plugin at index {i} must be an object",
                    field=f"plugins[{i}]"
                ))
            elif "name" not in plugin:
                errors.append(ValidationError(
                    f"Plugin at index {i} must have a 'name' field",
                    field=f"plugins[{i}].name"
                ))

        return errors
