"""
gem5 Integration Package
Provides integration between Python HBM model and gem5 simulator
"""

from .hbm4_config import (
    HBM4Timing,
    HBM4Config,
    HBM4Presets,
    HBM4AddrMap,
    get_config_by_name,
)

from .bridge import (
    HBMBridge,
    BridgeConfig,
    DualSimulatorBridge,
    MemoryRequest,
    MemoryResponse,
    RequestType,
    create_bridge,
)

__all__ = [
    # Configuration
    'HBM4Timing',
    'HBM4Config',
    'HBM4Presets',
    'HBM4AddrMap',
    'get_config_by_name',
    # Bridge
    'HBMBridge',
    'BridgeConfig',
    'DualSimulatorBridge',
    'MemoryRequest',
    'MemoryResponse',
    'RequestType',
    'create_bridge',
]

__version__ = '1.0.0'