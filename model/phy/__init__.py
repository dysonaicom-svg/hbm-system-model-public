"""
HBM PHY Models

This package provides PHY-level models for HBM memory interface.
The actual PHY implementation is in model.dram.phy_training module.

Classes available from model.dram.phy_training:
    - HBM4PHYManager: Main PHY management controller
    - PHYTrainingStateMachine: PHY training state machine
    - PHYInitializationStateMachine: PHY initialization state machine
    - PHYInitState: PHY initialization states
    - TrainingPhase: Training phase enumeration

Signal Integrity Models (in model.phy):
    - ChannelModel: Channel model with frequency-dependent loss
    - TXPreEmphasis: TX pre-emphasis equalizer
    - RXCTLE: RX continuous time linear equalizer
    - DFEEqualizer: Decision feedback equalizer
    - EyeDiagramAnalyzer: Eye diagram analysis and BER estimation

The PHY layer handles:
    - Initialization sequences
    - Training (write leveling, read DQ calibration, etc.)
    - Signal integrity monitoring
    - Lane repair and remapping
    - Channel equalization and eye analysis

Usage:
    from model.dram.phy_training import HBM4PHYManager

    phy = HBM4PHYManager()
    phy.start_training()

Signal Integrity Usage:
    from model.phy.channel_model import ChannelModel, ChannelConfig
    from model.phy.eye_analyzer import EyeDiagramAnalyzer

    config = ChannelConfig(sample_rate=32e9, length_mm=50.0)
    channel = ChannelModel(config)
    analyzer = EyeDiagramAnalyzer()
"""

# PHY models are implemented in model.dram.phy_training
# Import from there for actual functionality
from model.dram.phy_training import (
    HBM4PHYManager,
    PHYTrainingStateMachine,
    PHYInitializationStateMachine,
    PHYInitState,
    TrainingPhase,
)

# Signal integrity models
from model.phy.channel_model import (
    ChannelModel,
    ChannelConfig,
    ChannelCrosstalkModel,
    RLGCParameters
)

from model.phy.signal_integrity import (
    TXPreEmphasis,
    RXCTLE,
    DFEEqualizer,
    SignalIntegrityModel,
    PreEmphasisConfig,
    CTLEConfig,
    DFEConfig,
    SignalIntegrityConfig,
    EqualizerType
)

from model.phy.eye_analyzer import (
    EyeDiagramAnalyzer,
    EyeMeasurementConfig,
    BathtubCurveGenerator,
    EyeMetrics,
    EyeMeasurementType
)

# IBIS (I/O Buffer Information Specification) models
from model.phy.ibis_parser import (
    IBISParser,
    IBISFile,
    IBISModel,
    IBISModelType,
    IBISPackage,
    IBISPin,
    IVCurve,
    VTWaveform,
    CompositeDataTable,
    parse_ibis_file,
    parse_ibis_content
)

from model.phy.ibis_model import (
    IBISModelWrapper,
    BehavioralModel,
    WaveformMetrics,
    ChannelResponse,
    SignalIntegrityMetric,
    create_model_wrapper,
    create_model_wrapper_from_file
)

from model.phy.ibis_simulator import (
    IBISSimulator,
    ChannelParameters,
    SimulationConfig,
    SimulationMode,
    SignalDistortion,
    CrosstalkResult,
    EyeAnalysisResult,
    SimulationResult,
    create_simulator
)

__all__ = [
    # PHY training models
    'HBM4PHYManager',
    'PHYTrainingStateMachine',
    'PHYInitializationStateMachine',
    'PHYInitState',
    'TrainingPhase',
    # Channel models
    'ChannelModel',
    'ChannelConfig',
    'ChannelCrosstalkModel',
    'RLGCParameters',
    # Signal integrity
    'TXPreEmphasis',
    'RXCTLE',
    'DFEEqualizer',
    'SignalIntegrityModel',
    'PreEmphasisConfig',
    'CTLEConfig',
    'DFEConfig',
    'SignalIntegrityConfig',
    'EqualizerType',
    # Eye analysis
    'EyeDiagramAnalyzer',
    'EyeMeasurementConfig',
    'BathtubCurveGenerator',
    'EyeMetrics',
    'EyeMeasurementType',
    # IBIS parser
    'IBISParser',
    'IBISFile',
    'IBISModel',
    'IBISModelType',
    'IBISPackage',
    'IBISPin',
    'IVCurve',
    'VTWaveform',
    'CompositeDataTable',
    'parse_ibis_file',
    'parse_ibis_content',
    # IBIS model wrapper
    'IBISModelWrapper',
    'BehavioralModel',
    'WaveformMetrics',
    'ChannelResponse',
    'SignalIntegrityMetric',
    'create_model_wrapper',
    'create_model_wrapper_from_file',
    # IBIS simulator
    'IBISSimulator',
    'ChannelParameters',
    'SimulationConfig',
    'SimulationMode',
    'SignalDistortion',
    'CrosstalkResult',
    'EyeAnalysisResult',
    'SimulationResult',
    'create_simulator',
]