"""
HBM Interconnect Package
提供 AXI/NoC 互联模型
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

# Aliases for easier access
AXI_BurstType = AXIBurstType
AXI_ResponseType = AXIResponseType
AXI_Size = AXISize

__all__ = [
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
    "AXI_BurstType",
    "AXI_ResponseType",
    "AXI_Size",
    "NoCRoute",
    "MultiMasterTrafficGenerator",
    "create_hbm_interconnect",
]