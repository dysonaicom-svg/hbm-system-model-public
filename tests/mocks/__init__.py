"""
HBM4 Mock Objects Package

Provides mock implementations for DFI/PHY interfaces for testing:
- MockDFIInterface: DFI 5.0/5.1 interface mock
- MockPHY: PHY interface mock with training support
- MockChannel: Single channel mock
- MockBus: Bus/interconnect mock

Usage:
    from tests.mocks import MockDFIInterface, MockPHY

    # Create mock interface
    mock_dfi = MockDFIInterface()

    # Use in tests
    mock_dfi.send_command(...)
    assert mock_dfi.get_ack()

Reference:
- DFI 5.0/5.1 specification
- JEDEC JESD270-4A HBM4 specification
"""

from .mock_dfi_interface import (
    MockDFIInterface,
    MockDFIRequest,
    MockDFIResponse,
    MockDFISignals,
    DFICommand,
    DFILowPowerState,
    TrainingPhase,
)
from .mock_phy import (
    MockPHY,
    MockPHYTraining,
    MockPHYSignals,
    TrainingPhase as PHYTrainingPhase,
)
from .mock_common import (
    MockClock,
    MockReset,
    MockSignal,
    MockDataBus,
)

__all__ = [
    # DFI mocks
    'MockDFIInterface',
    'MockDFIRequest',
    'MockDFIResponse',
    'MockDFISignals',
    'DFICommand',
    'DFILowPowerState',
    'TrainingPhase',
    # PHY mocks
    'MockPHY',
    'MockPHYTraining',
    'MockPHYSignals',
    'PHYTrainingPhase',
    # Common mocks
    'MockClock',
    'MockReset',
    'MockSignal',
    'MockDataBus',
]
