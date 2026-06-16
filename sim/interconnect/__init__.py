"""
HBM Interconnect Package
提供 AXI/NoC 互联模型和 gem5 桥接
"""

from sim.interconnect.axi import (
    AXIMaster,
    AXISlave,
    AXIInterconnect,
    AXIAddress,
    AXIBeat,
    AXIResponse,
    AXIReadRequest,
    AXIWriteRequest,
    AXITransaction,
    AXIARChannel,
    AXIAWChannel,
    AXIWChannel,
    AXIBChannel,
    AXIRChannel,
    AXIBurstType,
    AXIResponseType,
    AXISize,
    NoCRoute,
    MultiMasterTrafficGenerator,
    create_hbm_interconnect,
)

from sim.interconnect.gem5_bridge import (
    Gem5Bridge,
    BridgeConfig,
    Gem5APIState,
    Gem5MockPort,
    Gem5MockSystem,
    PendingRequest,
    create_bridge,
)

from sim.interconnect.gem5_types import (
    Gem5RequestType,
    Gem5ResponseStatus,
    Gem5CommandType,
    Gem5Address,
    Gem5AddressRange,
    Gem5Request,
    Gem5Response,
    Gem5Transaction,
    Gem5BurstTransaction,
    Gem5MasterPort,
    Gem5SlavePort,
    Gem5TimingStats,
    Gem5CycleStats,
    Gem5MemoryRange,
    Gem5SystemConfig,
    create_read_request,
    create_write_request,
    create_burst_read_request,
)

# Aliases for easier access
AXI_BurstType = AXIBurstType
AXI_ResponseType = AXIResponseType
AXI_Size = AXISize

__all__ = [
    # AXI types
    "AXIMaster",
    "AXISlave",
    "AXIInterconnect",
    "AXIAddress",
    "AXIBeat",
    "AXIResponse",
    "AXIReadRequest",
    "AXIWriteRequest",
    "AXITransaction",
    "AXIARChannel",
    "AXIAWChannel",
    "AXIWChannel",
    "AXIBChannel",
    "AXIRChannel",
    "AXIBurstType",
    "AXIResponseType",
    "AXISize",
    "NoCRoute",
    "MultiMasterTrafficGenerator",
    "create_hbm_interconnect",

    # gem5 bridge
    "Gem5Bridge",
    "BridgeConfig",
    "Gem5APIState",
    "Gem5MockPort",
    "Gem5MockSystem",
    "PendingRequest",
    "create_bridge",

    # gem5 types
    "Gem5RequestType",
    "Gem5ResponseStatus",
    "Gem5CommandType",
    "Gem5Address",
    "Gem5AddressRange",
    "Gem5Request",
    "Gem5Response",
    "Gem5Transaction",
    "Gem5BurstTransaction",
    "Gem5MasterPort",
    "Gem5SlavePort",
    "Gem5TimingStats",
    "Gem5CycleStats",
    "Gem5MemoryRange",
    "Gem5SystemConfig",
    "create_read_request",
    "create_write_request",
    "create_burst_read_request",
]