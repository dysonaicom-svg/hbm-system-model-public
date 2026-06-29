"""
Power/Thermal Enhancement Module (T9.3)

Provides advanced power and thermal modeling capabilities:
- Power profile export to JSON/CSV
- HotSpot thermal simulator interface
- Enhanced thermal model with dynamic cooling
- Adaptive throttling control

Reference: model/dram/power_estimator.py, model/dram/thermal_model.py
"""

from model.dram.power_thermal.power_profile_exporter import (
    PowerProfileExporter,
    ExportConfig,
    PowerProfileMerger,
    create_exporter,
    quick_export,
)
from model.dram.power_thermal.hotspot_interface import (
    HotSpotInterface,
    HotSpotConfig,
    HotSpotResult,
    HotSpotFormat,
    BlockPower,
    TemperatureAwarePowerEstimator,
    create_hotspot_interface,
    quick_hotspot_sim,
)
from model.dram.power_thermal.enhanced_thermal import (
    EnhancedThermalModel,
    CoolingSystemConfig,
    CoolingType,
    ThermalZone,
    ThrottleLevel,
    ThrottleEvent,
    AdaptiveThrottler,
    create_enhanced_thermal_model,
    create_adaptive_thermal_controller,
)

__all__ = [
    # Power profile exporter
    'PowerProfileExporter',
    'ExportConfig',
    'PowerProfileMerger',
    'create_exporter',
    'quick_export',
    # HotSpot interface
    'HotSpotInterface',
    'HotSpotConfig',
    'HotSpotResult',
    'HotSpotFormat',
    'BlockPower',
    'TemperatureAwarePowerEstimator',
    'create_hotspot_interface',
    'quick_hotspot_sim',
    # Enhanced thermal
    'EnhancedThermalModel',
    'CoolingSystemConfig',
    'CoolingType',
    'ThermalZone',
    'ThrottleLevel',
    'ThrottleEvent',
    'AdaptiveThrottler',
    'create_enhanced_thermal_model',
    'create_adaptive_thermal_controller',
]
