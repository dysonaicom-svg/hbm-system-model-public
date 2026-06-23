"""
Mock DFI Interface Implementation

Provides a complete mock implementation of the DFI 5.0/5.1 interface
for testing without requiring actual PHY hardware.

Features:
- Full DFI 5.0/5.1 signal simulation
- Configurable timing parameters
- Request/response queue management
- Low-power state machine simulation
- Error injection for testing error paths

Usage:
    mock_dfi = MockDFIInterface()
    mock_dfi.send_command('ACT', address=0x1000, bank=0)
    mock_dfi.tick()  # Advance simulation
    response = mock_dfi.get_response()

Reference:
- DFI 5.0/5.1 specification
- Synopsys DesignWare HBM4/4E Controller IP
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
from collections import deque
import random


class DFICommand(Enum):
    """DFI command encoding (mirrored from model/dram/dfi_interface.py)"""
    NOP = 0b0000
    ACT = 0b0001
    PRE = 0b0010
    PREA = 0b0011
    RD = 0b0100
    WR = 0b0101
    RDA = 0b0110
    WRA = 0b0111
    REFab = 0b1000
    REFsb = 0b1001
    RFMab = 0b1010
    RFMsb = 0b1011
    MRS = 0b1100
    MRR = 0b1101
    SRE = 0b1110
    SRX = 0b1111
    PDE = 0b10000
    DPD = 0b10001
    WRLVL = 0b10011
    RDLVL = 0b10100
    RDDQSDQ = 0b10101
    WRDQSDQ = 0b10110
    MRLVL = 0b10111
    ZQCL = 0b11000
    ZQCS = 0b11001
    ZQOP = 0b11010

    def is_read(self) -> bool:
        return self in {DFICommand.RD, DFICommand.RDA, DFICommand.MRR,
                        DFICommand.RDLVL, DFICommand.RDDQSDQ, DFICommand.MRLVL}

    def is_write(self) -> bool:
        return self in {DFICommand.WR, DFICommand.WRA, DFICommand.WRLVL,
                        DFICommand.WRDQSDQ}


class DFILowPowerState(Enum):
    """DFI low-power states"""
    LP_IDLE = 0
    LP_CTRL = 1
    LP_DATA = 2
    LP_SELF_REFRESH = 3
    LP_POWER_DOWN = 4
    LP_DEEP_PD = 5
    LP_FREQ_CHANGE = 6


class TrainingPhase(Enum):
    """PHY training phases"""
    IDLE = 0
    DRAM_RESET = 1
    DRAM_INIT = 2
    WRITE_LEVELING = 3
    READ_GATE_TRAINING = 4
    READ_DQ_TRAINING = 5
    WRITE_DQ_TRAINING = 6
    WRITE_LEVELING_ADJUST = 7
    VREF_CALIBRATION = 8
    MEMORY_READY = 9
    COMPLETE = 10


class TrainingPhase(Enum):
    """PHY training phases"""
    IDLE = 0
    DRAM_RESET = 1
    DRAM_INIT = 2
    WRITE_LEVELING = 3
    READ_GATE_TRAINING = 4
    READ_DQ_TRAINING = 5
    WRITE_DQ_TRAINING = 6
    WRITE_LEVELING_ADJUST = 7
    VREF_CALIBRATION = 8
    MEMORY_READY = 9
    COMPLETE = 10


@dataclass
class MockDFIRequest:
    """Mock DFI request"""
    command: DFICommand
    address: int = 0
    bank: int = 0
    pseudo_channel: int = 0
    channel: int = 0
    wrdata_en: bool = False
    rddata_en: bool = False
    request_id: int = 0
    priority: int = 0
    timestamp: int = 0
    error: Optional[str] = None


@dataclass
class MockDFIResponse:
    """Mock DFI response"""
    ready: bool = True
    calibration_done: bool = False
    training_state: str = "not_started"
    lp_state: DFILowPowerState = DFILowPowerState.LP_IDLE
    error: Optional[str] = None
    phy_clock_enable: bool = True
    phy_reset: bool = False
    response_id: int = 0
    timestamp: int = 0
    ctrlupd_ack: bool = False
    freq_change_ack: bool = False
    pwr_up_done: bool = True
    pwr_down_ack: bool = False
    lp_ack: bool = False


@dataclass
class MockDFISignals:
    """DFI signal state container"""
    # Control signals
    cmd: int = 0
    cmd_en: bool = False
    address: int = 0
    bank: int = 0
    wrdata_en: bool = False
    rddata_en: bool = False

    # Handshake signals
    ctrlupd_req: bool = False
    ctrlupd_ack: bool = False
    freq_change_en: bool = False
    freq_change_ack: bool = False
    pwr_up_done: bool = True
    pwr_down_req: bool = False
    pwr_down_ack: bool = False
    lp_req: bool = False
    lp_ack: bool = False
    lp_wakeup: bool = False

    # State signals
    lp_state: DFILowPowerState = DFILowPowerState.LP_IDLE
    phy_ready: bool = True
    training_complete: bool = False

    # HBM4 extended signals
    phyupd_resp: bool = False
    self_refresh_n: bool = True
    memdata_disable: bool = False
    parity_in: bool = False
    parity_out: bool = False
    parity_error: bool = False
    pam3_enable: bool = False
    pam3_mode: int = 0


@dataclass
class MockDFIConfig:
    """Configuration for MockDFIInterface"""
    # Timing parameters
    tPHY_wrlAT: int = 5
    tPHY_rdLat: int = 5
    tFC_LATENCY: int = 8
    tLP_CTRL_ENTER: int = 2
    tLP_CTRL_EXIT: int = 2

    # Queue configuration
    max_queue_depth: int = 64

    # Error injection
    inject_parity_error: bool = False
    inject_timeout: bool = False
    inject_calibration_error: bool = False

    # Behavior flags
    auto_ack_ctrlupd: bool = True
    auto_ack_freq_change: bool = True
    auto_ack_low_power: bool = True


class MockDFIInterface:
    """Mock DFI 5.0/5.1 Interface

    Complete mock implementation of the DFI interface for testing.
    Simulates all DFI 5.0/5.1 signals and protocols.
    """

    def __init__(self, config: Optional[MockDFIConfig] = None):
        """Initialize mock DFI interface

        Args:
            config: Optional configuration
        """
        self.config = config or MockDFIConfig()

        # Signal state
        self.signals = MockDFISignals()

        # Request/response queues
        self._request_queue: deque = deque(maxlen=self.config.max_queue_depth)
        self._response_queue: List[MockDFIResponse] = []
        self._pending_requests: Dict[int, MockDFIRequest] = {}
        self._request_counter = 0

        # State tracking
        self._cycle = 0
        self._lp_state = DFILowPowerState.LP_IDLE
        self._training_phase = TrainingPhase.IDLE
        self._training_complete = False
        self._freq_mhz = 800
        self._target_freq_mhz = 800

        # Internal counters
        self._ctrlupd_counter = 0
        self._freq_change_counter = 0
        self._lp_counter = 0

        # Statistics
        self._stats = {
            'commands_sent': 0,
            'commands_completed': 0,
            'ctrl_updates': 0,
            'freq_changes': 0,
            'lp_entries': 0,
            'lp_exits': 0,
            'errors': 0,
        }

        # Callback hooks for test verification
        self._on_command_sent: Optional[Callable] = None
        self._on_response_ready: Optional[Callable] = None
        self._on_lp_transition: Optional[Callable] = None

    @property
    def cycle(self) -> int:
        """Current simulation cycle"""
        return self._cycle

    @property
    def lp_state(self) -> DFILowPowerState:
        """Current low-power state"""
        return self._lp_state

    @property
    def training_complete(self) -> bool:
        """Training completion status"""
        return self._training_complete

    def tick(self):
        """Advance simulation by one cycle

        Updates all internal state machines and signal states.
        """
        self._cycle += 1

        # Update internal state machines
        self._update_ctrlupd()
        self._update_freq_change()
        self._update_low_power()
        self._update_training()

        # Process pending requests
        self._process_pending_requests()

        # Update signal state
        self._update_signals()

    def _update_ctrlupd(self):
        """Update control update state machine"""
        if self.signals.ctrlupd_req and not self.signals.ctrlupd_ack:
            self._ctrlupd_counter += 1
            if self.config.auto_ack_ctrlupd and self._ctrlupd_counter >= self.config.tLP_CTRL_ENTER:
                self.signals.ctrlupd_ack = True
                self._stats['ctrl_updates'] += 1
                self._ctrlupd_counter = 0

        if self.signals.ctrlupd_ack and self.signals.ctrlupd_req:
            # Complete handshake
            self.signals.ctrlupd_req = False
            self.signals.ctrlupd_ack = False

    def _update_freq_change(self):
        """Update frequency change state machine"""
        if self.signals.freq_change_en and not self.signals.freq_change_ack:
            self._freq_change_counter += 1
            if (self.config.auto_ack_freq_change and
                self._freq_change_counter >= self.config.tFC_LATENCY):
                self.signals.freq_change_ack = True
                self._freq_change_counter = 0

        if self.signals.freq_change_ack and self.signals.freq_change_en:
            # Frequency change complete
            self.signals.freq_change_en = False
            self.signals.freq_change_ack = False
            self._freq_mhz = self._target_freq_mhz
            self._stats['freq_changes'] += 1

    def _update_low_power(self):
        """Update low power state machine"""
        prev_state = self._lp_state

        if self.signals.lp_req and not self.signals.lp_ack:
            self._lp_counter += 1
            if self.config.auto_ack_low_power and self._lp_counter >= self.config.tLP_CTRL_ENTER:
                self.signals.lp_ack = True
                self._stats['lp_entries'] += 1
                self._lp_counter = 0

        if self.signals.lp_wakeup:
            self._lp_counter += 1
            if self._lp_counter >= self.config.tLP_CTRL_EXIT:
                self._lp_state = DFILowPowerState.LP_IDLE
                self.signals.lp_req = False
                self.signals.lp_ack = False
                self.signals.lp_wakeup = False
                self._stats['lp_exits'] += 1
                self._lp_counter = 0

        # Update signals
        self.signals.lp_state = self._lp_state

        # Trigger callback if state changed
        if prev_state != self._lp_state and self._on_lp_transition:
            self._on_lp_transition(prev_state, self._lp_state)

    def _update_training(self):
        """Update training state machine"""
        if self._training_phase == TrainingPhase.IDLE:
            pass
        elif self._training_phase == TrainingPhase.DRAM_RESET:
            self._training_phase = TrainingPhase.DRAM_INIT
        elif self._training_phase == TrainingPhase.DRAM_INIT:
            self._training_phase = TrainingPhase.WRITE_LEVELING
        elif self._training_phase == TrainingPhase.WRITE_LEVELING:
            self._training_phase = TrainingPhase.READ_GATE_TRAINING
        elif self._training_phase == TrainingPhase.READ_GATE_TRAINING:
            self._training_phase = TrainingPhase.READ_DQ_TRAINING
        elif self._training_phase == TrainingPhase.READ_DQ_TRAINING:
            self._training_phase = TrainingPhase.WRITE_DQ_TRAINING
        elif self._training_phase == TrainingPhase.WRITE_DQ_TRAINING:
            self._training_phase = TrainingPhase.VREF_CALIBRATION
        elif self._training_phase == TrainingPhase.VREF_CALIBRATION:
            self._training_phase = TrainingPhase.MEMORY_READY
            self._training_complete = True
        elif self._training_phase == TrainingPhase.MEMORY_READY:
            self._training_phase = TrainingPhase.COMPLETE

    def _process_pending_requests(self):
        """Process pending DFI requests"""
        for req_id, request in list(self._pending_requests.items()):
            # Simulate request completion
            latency = self.config.tPHY_rdLat if request.rddata_en else self.config.tPHY_wrlAT
            if self._cycle - request.timestamp >= latency:
                response = MockDFIResponse(
                    ready=True,
                    calibration_done=self._training_complete,
                    training_state=self._training_phase.name.lower(),
                    lp_state=self._lp_state,
                    response_id=req_id,
                    timestamp=self._cycle,
                    ctrlupd_ack=self.signals.ctrlupd_ack,
                    freq_change_ack=self.signals.freq_change_ack,
                    pwr_up_done=self.signals.pwr_up_done,
                    lp_ack=self.signals.lp_ack,
                )
                self._response_queue.append(response)
                del self._pending_requests[req_id]
                self._stats['commands_completed'] += 1

    def _update_signals(self):
        """Update signal state from internal state"""
        self.signals.lp_state = self._lp_state
        self.signals.training_complete = self._training_complete

    # === Public API ===

    def send_command(self, command: DFICommand, address: int = 0, bank: int = 0,
                     pseudo_channel: int = 0, channel: int = 0,
                     priority: int = 0, wrdata_en: bool = False,
                     rddata_en: bool = False) -> int:
        """Send a DFI command

        Args:
            command: DFI command to send
            address: Row/memory address
            bank: Bank address
            pseudo_channel: Pseudo-channel index
            channel: Channel index
            priority: Request priority
            wrdata_en: Write data enable
            rddata_en: Read data enable

        Returns:
            Request ID
        """
        request_id = self._request_counter
        self._request_counter += 1

        request = MockDFIRequest(
            command=command,
            address=address,
            bank=bank,
            pseudo_channel=pseudo_channel,
            channel=channel,
            wrdata_en=wrdata_en,
            rddata_en=rddata_en,
            request_id=request_id,
            priority=priority,
            timestamp=self._cycle,
        )

        self._request_queue.append(request)
        self._pending_requests[request_id] = request
        self._stats['commands_sent'] += 1

        # Update signals
        self.signals.cmd = command.value
        self.signals.cmd_en = True
        self.signals.address = address
        self.signals.bank = bank
        self.signals.wrdata_en = wrdata_en
        self.signals.rddata_en = rddata_en

        # Trigger callback
        if self._on_command_sent:
            self._on_command_sent(request)

        return request_id

    def send_act(self, bank: int, row: int, channel: int = 0,
                 pseudo_channel: int = 0) -> int:
        """Send ACTIVATE command"""
        return self.send_command(
            DFICommand.ACT, address=row, bank=bank,
            channel=channel, pseudo_channel=pseudo_channel
        )

    def send_pre(self, bank: int, channel: int = 0,
                 pseudo_channel: int = 0) -> int:
        """Send PRECHARGE command"""
        return self.send_command(
            DFICommand.PRE, bank=bank,
            channel=channel, pseudo_channel=pseudo_channel
        )

    def send_rd(self, bank: int, column: int, channel: int = 0,
                pseudo_channel: int = 0) -> int:
        """Send READ command"""
        return self.send_command(
            DFICommand.RD, address=column, bank=bank,
            channel=channel, pseudo_channel=pseudo_channel,
            rddata_en=True
        )

    def send_wr(self, bank: int, column: int, channel: int = 0,
                pseudo_channel: int = 0) -> int:
        """Send WRITE command"""
        return self.send_command(
            DFICommand.WR, address=column, bank=bank,
            channel=channel, pseudo_channel=pseudo_channel,
            wrdata_en=True
        )

    def send_ref(self, channel: int = 0) -> int:
        """Send REFRESH command"""
        return self.send_command(
            DFICommand.REFab, channel=channel
        )

    def send_mrs(self, address: int, value: int, channel: int = 0) -> int:
        """Send MODE REGISTER SET command"""
        return self.send_command(
            DFICommand.MRS, address=value, bank=address,
            channel=channel
        )

    def request_ctrlupd(self) -> bool:
        """Request control update"""
        if self.signals.ctrlupd_req:
            return False
        self.signals.ctrlupd_req = True
        self._ctrlupd_counter = 0
        return True

    def acknowledge_ctrlupd(self) -> bool:
        """Acknowledge control update"""
        if not self.signals.ctrlupd_req:
            return False
        self.signals.ctrlupd_ack = True
        return True

    def request_freq_change(self, target_freq_mhz: int) -> bool:
        """Request frequency change"""
        if self.signals.freq_change_en:
            return False
        self._target_freq_mhz = target_freq_mhz
        self.signals.freq_change_en = True
        self._freq_change_counter = 0
        return True

    def request_low_power(self, state: DFILowPowerState) -> bool:
        """Request low power state entry"""
        if self.signals.lp_req:
            return False
        self._lp_state = state
        self.signals.lp_req = True
        self._lp_counter = 0
        return True

    def wakeup(self):
        """Wake from low power state"""
        self.signals.lp_wakeup = True
        self._lp_counter = 0

    def start_training(self):
        """Start PHY training sequence"""
        self._training_phase = TrainingPhase.DRAM_RESET

    def complete_training(self):
        """Mark training as complete"""
        self._training_phase = TrainingPhase.COMPLETE
        self._training_complete = True

    def set_frequency(self, freq_mhz: int):
        """Set interface frequency"""
        self._freq_mhz = freq_mhz
        self._target_freq_mhz = freq_mhz

    def get_response(self, request_id: Optional[int] = None) -> Optional[MockDFIResponse]:
        """Get response from PHY

        Args:
            request_id: Optional specific request ID to match

        Returns:
            DFI response or None if no response available
        """
        if not self._response_queue:
            return None

        if request_id is None:
            return self._response_queue.pop(0)

        # Find matching response
        for i, resp in enumerate(self._response_queue):
            if resp.response_id == request_id:
                return self._response_queue.pop(i)
        return None

    def get_all_responses(self) -> List[MockDFIResponse]:
        """Get all available responses"""
        responses = list(self._response_queue)
        self._response_queue.clear()
        return responses

    def has_pending_response(self) -> bool:
        """Check if response is available"""
        return len(self._response_queue) > 0

    def get_signal_state(self, signal_name: str) -> Any:
        """Get current signal state

        Args:
            signal_name: Name of the signal

        Returns:
            Signal value
        """
        if hasattr(self.signals, signal_name):
            return getattr(self.signals, signal_name)
        return None

    def set_signal_state(self, signal_name: str, value: Any):
        """Set signal state

        Args:
            signal_name: Name of the signal
            value: New value
        """
        if hasattr(self.signals, signal_name):
            setattr(self.signals, signal_name, value)

    def inject_parity_error(self):
        """Inject a parity error for testing"""
        self.signals.parity_error = True
        self._stats['errors'] += 1

    def inject_timeout(self):
        """Simulate timeout condition"""
        self._lp_counter = 1000000  # Force timeout
        self._stats['errors'] += 1

    def reset(self):
        """Reset the mock interface"""
        self._cycle = 0
        self._lp_state = DFILowPowerState.LP_IDLE
        self._training_phase = TrainingPhase.IDLE
        self._training_complete = False
        self._freq_mhz = 800
        self._target_freq_mhz = 800
        self._ctrlupd_counter = 0
        self._freq_change_counter = 0
        self._lp_counter = 0
        self._request_queue.clear()
        self._response_queue.clear()
        self._pending_requests.clear()
        self._request_counter = 0
        self._stats = {k: 0 for k in self._stats}
        self.signals = MockDFISignals()

    def get_statistics(self) -> Dict[str, Any]:
        """Get interface statistics"""
        return {
            **self._stats,
            'queue_depth': len(self._request_queue),
            'pending_requests': len(self._pending_requests),
            'pending_responses': len(self._response_queue),
            'cycle': self._cycle,
            'lp_state': self._lp_state.name,
            'training_phase': self._training_phase.name,
        }

    def set_callback(self, event: str, callback: Callable):
        """Set event callback

        Args:
            event: Event name ('command_sent', 'response_ready', 'lp_transition')
            callback: Callback function
        """
        if event == 'command_sent':
            self._on_command_sent = callback
        elif event == 'response_ready':
            self._on_response_ready = callback
        elif event == 'lp_transition':
            self._on_lp_transition = callback

    def get_queue_snapshot(self) -> List[Tuple[int, str, int, int]]:
        """Get snapshot of request queue

        Returns:
            List of (request_id, command_name, timestamp, priority)
        """
        return [
            (req.request_id, req.command.name, req.timestamp, req.priority)
            for req in self._request_queue
        ]
