"""
HBM4 Traffic Generator Module

Layer 0 of the 5-layer HBM system architecture.
Provides traffic patterns for AI training, inference, and synthetic testing.

New in this version:
- AddressPatternGenerator with HBM4 32-channel awareness
- Enhanced traffic patterns: hotspot (80/20), neighbor, stride variations
- Bandwidth throttling and rate limiting
- Request ID tracking
- Channel distribution statistics
"""

from model.traffic.traffic_generator import (
    # Enums
    TrafficPattern,
    DataPrecision,
    QoSLevel,

    # Configuration
    TrafficConfig,
    AddressGenerator,

    # Traffic Patterns
    AITrainingPattern,
    WeightUpdatePattern,
    GradientComputationPattern,
    FeatureMapTransferPattern,
    AIInferencePattern,
    BurstReadPattern,
    WeightReusePattern,
    MixedPrecisionPattern,
    SyntheticPattern,
    FixedRatePattern,
    BurstPattern,
    RandomPattern,
    RampPattern,
    SinusoidalPattern,
    TraceReplayPattern,

    # New Traffic Patterns
    HotspotPattern,
    NeighborPattern,
    StridePattern,
    ChannelInterleavePattern,

    # Main Classes
    TrafficGenerator,
    TrafficGeneratorRunner,
    AddressPatternGenerator,
    AddressPatternGeneratorWrapper,

    # Factory Functions
    create_traffic_generator,
    create_address_aware_traffic_generator,
)

from model.traffic.address_pattern import (
    # Enums
    AddressPattern,
    ChannelMapping,

    # Classes
    AddressPatternConfig,
    AddressPatternGenerator,
    HBM4AddressBits,
    AddressPatternIterator,

    # Factory
    create_address_generator,
)

__all__ = [
    # Traffic Generator Enums
    'TrafficPattern',
    'DataPrecision',
    'QoSLevel',

    # Traffic Generator Configuration
    'TrafficConfig',
    'AddressGenerator',

    # Traffic Patterns
    'AITrainingPattern',
    'WeightUpdatePattern',
    'GradientComputationPattern',
    'FeatureMapTransferPattern',
    'AIInferencePattern',
    'BurstReadPattern',
    'WeightReusePattern',
    'MixedPrecisionPattern',
    'SyntheticPattern',
    'FixedRatePattern',
    'BurstPattern',
    'RandomPattern',
    'RampPattern',
    'SinusoidalPattern',
    'TraceReplayPattern',

    # New Traffic Patterns
    'HotspotPattern',
    'NeighborPattern',
    'StridePattern',
    'ChannelInterleavePattern',

    # Traffic Generator Classes
    'TrafficGenerator',
    'TrafficGeneratorRunner',
    'AddressPatternGenerator',
    'AddressPatternGeneratorWrapper',

    # Address Pattern Enums
    'AddressPattern',
    'ChannelMapping',

    # Address Pattern Classes
    'AddressPatternConfig',
    'HBM4AddressBits',
    'AddressPatternIterator',

    # Factory Functions
    'create_traffic_generator',
    'create_address_aware_traffic_generator',
    'create_address_generator',
]
