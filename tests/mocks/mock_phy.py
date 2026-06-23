"""
Mock PHY Implementation

Provides a complete mock implementation of the HBM4 PHY interface
for testing without requiring actual PHY hardware.

Features:
- Training sequence simulation
- Lane calibration state tracking
- PLL/DLL configuration
- VREF and impedance calibration
- Error injection for testing

Usage:
    mock_phy = MockPHY()
    mock_phy.start_training()
    while not mock_phy.is_training_complete():
        mock_phy.tick()
    coeffs = mock_phy.get_coefficients()

Reference:
- JEDEC JESD270-4A HBM4 specification
- Cadence HBM4E documentation
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
import random


class TrainingPhase(Enum):
    """PHY training phases"""
    IDLE = 0
    DRAM_RESET = 1
    DRAM_INIT = 2
    WRITE_LEVELING = 3
    WRITE_LEVELING_ADJUST = 4
    READ_GATE_TRAINING = 5
    READ_GATE_DQS = 6
    READ_DQ = 7
    WRITE_DQ = 8
    VREF_CALIBRATION = 9
    READ_IMAIN = 10
    WRITE_IMAIN = 11
    MEMORY_READY = 12
    COMPLETE = 13
    FAIL = 14


class TrainingType(Enum):
    """Training type options"""
    NORMAL = 0
    QUICK = 1
    VERIFY_ONLY = 2
    MARGIN_SCAN = 3


@dataclass
class MockPHYSignals:
    """PHY signal state container"""
    # Clock and reset
    phy_clock_enable: bool = True
    phy_reset: bool = False

    # Training signals
    training_req: bool = False
    training_ack: bool = False
    training_complete: bool = False

    # Calibration signals
    cal_req: bool = False
    cal_ack: bool = False
    cal_complete: bool = False

    # Data signals
    wrdata_en: bool = False
    rddata_en: bool = False
    data_valid: bool = False

    # Status signals
    pll_locked: bool = True
    dll_locked: bool = True
    zq_calibrated: bool = False


@dataclass
class PHYTapCoefficients:
    """PHY tap coefficients after training"""
    # TX coefficients
    tx_precursor: List[float] = field(default_factory=lambda: [0.0, 0.0])
    tx_postcursor: List[float] = field(default_factory=lambda: [0.0, 0.0])
    tx_main_cursor: float = 1.0

    # RX coefficients
    rx_ctle_dc_gain: float = 0.0
    rx_ctle_peaking: float = 3.0
    rx_vref: int = 32

    # DFE coefficients
    dfe_taps: List[float] = field(default_factory=lambda: [0.0] * 5)

    # Per-lane delays (64 lanes for HBM4)
    lane_delays: Dict[int, int] = field(default_factory=dict)
    lane_dq_delays: Dict[int, int] = field(default_factory=dict)


@dataclass
class TrainingPhaseResult:
    """Result of a single training phase"""
    phase: TrainingPhase
    passed: bool
    start_cycle: int = 0
    end_cycle: int = 0
    best_value: int = 0
    best_margin: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class MockPHYConfig:
    """Configuration for MockPHY"""
    # Lane configuration
    num_lanes: int = 64
    lanes_per_group: int = 8

    # Training configuration
    enable_write_leveling: bool = True
    enable_read_gate: bool = True
    enable_margin_cal: bool = True
    enable_dfe: bool = True
    enable_per_lane: bool = True

    # Iteration counts
    wrlvl_iterations: int = 64
    rdgd_iterations: int = 64
    mgcal_iterations: int = 64
    dfe_iterations: int = 128

    # Convergence criteria
    min_margin_ui: float = 0.15
    convergence_threshold: float = 0.01

    # Timeout settings
    timeout_cycles: int = 100000
    retry_count: int = 3

    # Behavior flags
    simulate_failures: bool = False
    failure_probability: float = 0.0


class MockPHYTraining:
    """Mock PHY Training Engine

    Simulates PHY training sequence and state machine.
    """

    def __init__(self, parent: 'MockPHY', config: Optional[MockPHYConfig] = None):
        self.parent = parent
        self.config = config or MockPHYConfig()
        self._reset()

    def _reset(self):
        """Reset training state"""
        self.current_phase = TrainingPhase.IDLE
        self.state_enter_cycle = 0
        self.total_cycles = 0
        self.retry_count = 0
        self.phase_results: Dict[TrainingPhase, TrainingPhaseResult] = {}
        self.coefficients = PHYTapCoefficients()

        # Initialize lane delays
        for lane in range(self.config.num_lanes):
            self.coefficients.lane_delays[lane] = 0
            self.coefficients.lane_dq_delays[lane] = 0

    def start(self, training_type: TrainingType = TrainingType.NORMAL):
        """Start training sequence"""
        self._reset()
        self.training_type = training_type
        self.current_phase = TrainingPhase.DRAM_RESET
        self.state_enter_cycle = self.parent.cycle
        self.parent.signals.training_req = True

    def tick(self):
        """Advance training state machine"""
        self.total_cycles += 1
        self._advance_phase()

    def _advance_phase(self):
        """Advance to next training phase"""
        phase_order = [
            TrainingPhase.DRAM_RESET,
            TrainingPhase.DRAM_INIT,
            TrainingPhase.WRITE_LEVELING,
            TrainingPhase.WRITE_LEVELING_ADJUST,
            TrainingPhase.READ_GATE_TRAINING,
            TrainingPhase.READ_GATE_DQS,
            TrainingPhase.READ_DQ,
            TrainingPhase.WRITE_DQ,
            TrainingPhase.VREF_CALIBRATION,
            TrainingPhase.MEMORY_READY,
        ]

        try:
            idx = phase_order.index(self.current_phase)
            if idx < len(phase_order) - 1:
                self.current_phase = phase_order[idx + 1]
            else:
                self.current_phase = TrainingPhase.COMPLETE
        except ValueError:
            self.current_phase = TrainingPhase.COMPLETE

        self.state_enter_cycle = self.parent.cycle

        if self.current_phase == TrainingPhase.COMPLETE:
            self.parent.signals.training_complete = True
            self.parent.signals.training_ack = True
        elif self.current_phase == TrainingPhase.FAIL:
            self.parent.signals.training_ack = True

    def is_complete(self) -> bool:
        """Check if training is complete"""
        return self.current_phase in {TrainingPhase.COMPLETE, TrainingPhase.FAIL}

    def is_passed(self) -> bool:
        """Check if training passed"""
        return self.current_phase == TrainingPhase.COMPLETE

    def get_results(self) -> Dict[str, Any]:
        """Get training results"""
        return {
            'passed': self.is_passed(),
            'phase': self.current_phase.name,
            'total_cycles': self.total_cycles,
            'coefficients': {
                'tx_precursor': self.coefficients.tx_precursor,
                'tx_postcursor': self.coefficients.tx_postcursor,
                'tx_main_cursor': self.coefficients.tx_main_cursor,
                'rx_vref': self.coefficients.rx_vref,
                'dfe_taps': self.coefficients.dfe_taps,
            },
        }


class MockPHY:
    """Mock PHY Interface

    Complete mock implementation of the HBM4 PHY interface.
    Simulates all PHY signals, training, and calibration.
    """

    VERSION = "MockPHY_v1.0"

    def __init__(self, config: Optional[MockPHYConfig] = None):
        """Initialize mock PHY

        Args:
            config: Optional configuration
        """
        self.config = config or MockPHYConfig()
        self.signals = MockPHYSignals()

        # Training engine
        self.training = MockPHYTraining(self, self.config)

        # PLL/DLL configuration
        self._pll_config = {
            'frequency_mhz': 800,
            'divider': 1,
            'multiplier': 1,
            'locked': True,
        }
        self._dll_config = {
            'enabled': True,
            'delay_elements': 64,
            'locked': True,
        }

        # VREF configuration
        self._vref_config = {
            'dram_vref': 50,
            'phy_vref': 50,
        }

        # Impedance configuration
        self._impedance_config = {
            'write_impedance': 40,
            'read_impedance': 40,
            'calibration_done': False,
        }

        # Mode registers
        self._mode_registers: Dict[int, int] = {}

        # Calibration data
        self._calibration_data: Dict[str, Any] = {}

        # State tracking
        self._cycle = 0
        self._initialized = False

        # Statistics
        self._stats = {
            'training_count': 0,
            'calibration_count': 0,
            'commands_received': 0,
        }

        # Callback hooks
        self._on_training_complete: Optional[Callable] = None
        self._on_calibration_complete: Optional[Callable] = None

    @property
    def cycle(self) -> int:
        """Current simulation cycle"""
        return self._cycle

    @property
    def is_initialized(self) -> bool:
        """Check if PHY is initialized"""
        return self._initialized

    def tick(self):
        """Advance simulation by one cycle"""
        self._cycle += 1

        # Update training if active
        if self.training.current_phase != TrainingPhase.IDLE:
            self.training.tick()

    # === Clock and Reset ===

    def set_clock_enable(self, enable: bool):
        """Set PHY clock enable

        Args:
            enable: True to enable clock
        """
        self.signals.phy_clock_enable = enable
        if not enable:
            self._pll_config['locked'] = False
            self._dll_config['locked'] = False

    def set_reset(self, reset: bool):
        """Set PHY reset

        Args:
            reset: True to assert reset
        """
        self.signals.phy_reset = reset
        if reset:
            self._pll_config['locked'] = False
            self._dll_config['locked'] = False

    # === Initialization ===

    def initialize(self):
        """Initialize PHY"""
        self._initialized = True
        self.signals.pll_locked = True
        self.signals.dll_locked = True
        self._pll_config['locked'] = True
        self._dll_config['locked'] = True

    # === Training ===

    def start_training(self, training_type: TrainingType = TrainingType.NORMAL):
        """Start training sequence

        Args:
            training_type: Type of training to perform
        """
        self.training.start(training_type)
        self._stats['training_count'] += 1

    def is_training_in_progress(self) -> bool:
        """Check if training is in progress"""
        return (self.training.current_phase != TrainingPhase.IDLE and
                self.training.current_phase != TrainingPhase.COMPLETE and
                self.training.current_phase != TrainingPhase.FAIL)

    def is_training_complete(self) -> bool:
        """Check if training is complete"""
        return self.training.is_complete()

    def did_training_pass(self) -> bool:
        """Check if training passed"""
        return self.training.is_passed()

    def get_training_phase(self) -> TrainingPhase:
        """Get current training phase"""
        return self.training.current_phase

    def get_training_results(self) -> Dict[str, Any]:
        """Get training results"""
        return self.training.get_results()

    def get_coefficients(self) -> PHYTapCoefficients:
        """Get trained tap coefficients"""
        return self.training.coefficients

    def set_callback(self, event: str, callback: Callable):
        """Set event callback

        Args:
            event: Event name
            callback: Callback function
        """
        if event == 'training_complete':
            self._on_training_complete = callback
        elif event == 'calibration_complete':
            self._on_calibration_complete = callback

    # === Calibration ===

    def start_calibration(self):
        """Start ZQ calibration"""
        self.signals.cal_req = True
        self._stats['calibration_count'] += 1

    def is_calibrated(self) -> bool:
        """Check if ZQ calibration is complete"""
        return self._impedance_config['calibration_done']

    def complete_calibration(self):
        """Mark calibration as complete"""
        self.signals.cal_complete = True
        self._impedance_config['calibration_done'] = True
        self.signals.zq_calibrated = True

        if self._on_calibration_complete:
            self._on_calibration_complete()

    # === PLL/DLL Configuration ===

    def configure_pll(self, frequency_mhz: int, divider: int = 1,
                      multiplier: int = 1):
        """Configure PLL

        Args:
            frequency_mhz: Target frequency in MHz
            divider: PLL divider ratio
            multiplier: PLL multiplier ratio
        """
        self._pll_config['frequency_mhz'] = frequency_mhz
        self._pll_config['divider'] = divider
        self._pll_config['multiplier'] = multiplier
        self._pll_config['locked'] = False  # Requires re-lock

    def get_pll_config(self) -> Dict[str, Any]:
        """Get PLL configuration"""
        return dict(self._pll_config)

    def is_pll_locked(self) -> bool:
        """Check if PLL is locked"""
        return self._pll_config['locked']

    def set_pll_locked(self, locked: bool):
        """Set PLL lock status"""
        self._pll_config['locked'] = locked
        self.signals.pll_locked = locked

    def configure_dll(self, enabled: bool = True, delay_elements: int = 64):
        """Configure DLL

        Args:
            enabled: Enable DLL
            delay_elements: Number of delay elements
        """
        self._dll_config['enabled'] = enabled
        self._dll_config['delay_elements'] = delay_elements

    def get_dll_config(self) -> Dict[str, Any]:
        """Get DLL configuration"""
        return dict(self._dll_config)

    def is_dll_locked(self) -> bool:
        """Check if DLL is locked"""
        return self._dll_config['locked']

    def set_dll_locked(self, locked: bool):
        """Set DLL lock status"""
        self._dll_config['locked'] = locked
        self.signals.dll_locked = locked

    # === VREF Configuration ===

    def configure_vref(self, dram_vref: int = 50, phy_vref: int = 50):
        """Configure VREF settings

        Args:
            dram_vref: DRAM VREF as percentage
            phy_vref: PHY VREF as percentage
        """
        self._vref_config['dram_vref'] = max(0, min(100, dram_vref))
        self._vref_config['phy_vref'] = max(0, min(100, phy_vref))

    def get_vref_config(self) -> Dict[str, int]:
        """Get VREF configuration"""
        return dict(self._vref_config)

    # === Impedance Configuration ===

    def configure_impedance(self, write_ohm: int = 40, read_ohm: int = 40):
        """Configure driver impedance

        Args:
            write_ohm: Write driver impedance in Ohms
            read_ohm: Read driver impedance in Ohms
        """
        self._impedance_config['write_impedance'] = write_ohm
        self._impedance_config['read_impedance'] = read_ohm

    def get_impedance_config(self) -> Dict[str, int]:
        """Get impedance configuration"""
        return dict(self._impedance_config)

    # === Mode Register Access ===

    def set_mode_register(self, address: int, value: int):
        """Set mode register

        Args:
            address: MR address (0-31)
            value: MR value
        """
        self._mode_registers[address] = value & 0xFF

    def get_mode_register(self, address: int) -> int:
        """Get mode register

        Args:
            address: MR address

        Returns:
            MR value, 0 if not set
        """
        return self._mode_registers.get(address, 0)

    def get_all_mode_registers(self) -> Dict[int, int]:
        """Get all mode registers"""
        return dict(self._mode_registers)

    # === Data Interface ===

    def receive_command(self, cmd: int, address: int, bank: int):
        """Receive command from controller

        Args:
            cmd: Command code
            address: Address
            bank: Bank address
        """
        self._stats['commands_received'] += 1

    def set_wrdata_en(self, enable: bool):
        """Set write data enable"""
        self.signals.wrdata_en = enable

    def set_rddata_en(self, enable: bool):
        """Set read data enable"""
        self.signals.rddata_en = enable

    def set_data_valid(self, valid: bool):
        """Set data valid signal"""
        self.signals.data_valid = valid

    # === Status ===

    def get_status(self) -> Dict[str, bool]:
        """Get comprehensive PHY status"""
        return {
            'initialized': self._initialized,
            'training_complete': self.signals.training_complete,
            'calibration_done': self._impedance_config['calibration_done'],
            'pll_locked': self._pll_config['locked'],
            'dll_locked': self._dll_config['locked'],
            'zq_calibrated': self.signals.zq_calibrated,
        }

    def get_info(self) -> Dict[str, Any]:
        """Get PHY information"""
        return {
            'version': self.VERSION,
            'num_lanes': self.config.num_lanes,
            'lanes_per_group': self.config.lanes_per_group,
            'pll': self._pll_config,
            'dll': self._dll_config,
            'vref': self._vref_config,
            'impedance': self._impedance_config,
            'status': self.get_status(),
            'training_phase': self.training.current_phase.name,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get PHY statistics"""
        return {
            **self._stats,
            'cycle': self._cycle,
            'training_phase': self.training.current_phase.name,
        }

    # === Reset ===

    def reset(self):
        """Reset the mock PHY"""
        self._cycle = 0
        self._initialized = False
        self.signals = MockPHYSignals()
        self.training._reset()
        self._pll_config['locked'] = True
        self._dll_config['locked'] = True
        self._impedance_config['calibration_done'] = False
        self._mode_registers.clear()
        self._stats = {k: 0 for k in self._stats}
