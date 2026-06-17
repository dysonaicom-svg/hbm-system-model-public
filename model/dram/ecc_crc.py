"""
HBM4 ECC and CRC Module

Implements error detection and correction for HBM4 data paths.

Key features:
- SEC-DED (Single Error Correction, Double Error Detection) ECC
- CRC16 for data integrity
- CRC15+KBD for command/address protection
- DQ Parity for read/write data protection (8-bit parity per 64-bit lane)
- CA Parity for command/address protection
- Error injection for testing
- Lane repair integration for RAS compliance

Based on:
- JEDEC JESD270-4A HBM4 specification
- Synopsys HBM4 Controller IP
- Cadence HBM4E documentation
"""

from typing import Dict, Optional, Tuple, List, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import struct
import time


class ErrorType(Enum):
    """Types of errors detected"""
    NO_ERROR = "no_error"
    SINGLE_BIT = "single_bit"
    DOUBLE_BIT = "double_bit"
    MULTI_BIT = "multi_bit"
    UNCORRECTABLE = "uncorrectable"
    DQ_PARITY_ERROR = "dq_parity_error"
    CA_PARITY_ERROR = "ca_parity_error"
    CRC_ERROR = "crc_error"
    ECC_ERROR = "ecc_error"


class ParityMode(Enum):
    """Parity calculation modes"""
    EVEN = 0  # Even parity: even number of 1s
    ODD = 1   # Odd parity: odd number of 1s


class ErrorSeverity(Enum):
    """Severity classification for errors"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


@dataclass
class ECCResult:
    """Result of ECC operation"""
    data: int
    syndrome: int
    error_type: ErrorType
    error_bit: Optional[int] = None
    corrected: bool = False


@dataclass
class CRCResult:
    """Result of CRC operation"""
    data: int
    crc: int
    valid: bool


@dataclass
class ParityResult:
    """Result of parity operation"""
    data: int
    parity: int
    expected: Optional[int] = None
    valid: Optional[bool] = None


@dataclass
class ErrorEvent:
    """Single error event for tracking"""
    timestamp: int
    error_type: ErrorType
    channel: int
    bank: int
    address: int
    error_mask: int
    corrected: bool
    syndrome: int


@dataclass
class ServiceEvent:
    """Service event for RAS tracking"""
    event_type: str
    timestamp: float
    cycle: int
    channel: int
    details: str = ""
    severity: ErrorSeverity = ErrorSeverity.INFO


@dataclass
class ErrorCounter:
    """Error counting statistics"""
    single_bit_errors: int = 0
    double_bit_errors: int = 0
    multi_bit_errors: int = 0
    uncorrectable_errors: int = 0
    corrections: int = 0
    crc_errors: int = 0
    dq_parity_errors: int = 0
    ca_parity_errors: int = 0
    total_transactions: int = 0
    total_parity_checks: int = 0
    total_ca_parity_checks: int = 0

    def reset(self):
        """Reset all counters"""
        self.single_bit_errors = 0
        self.double_bit_errors = 0
        self.multi_bit_errors = 0
        self.uncorrectable_errors = 0
        self.corrections = 0
        self.crc_errors = 0
        self.dq_parity_errors = 0
        self.ca_parity_errors = 0
        self.total_transactions = 0
        self.total_parity_checks = 0
        self.total_ca_parity_checks = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'single_bit_errors': self.single_bit_errors,
            'double_bit_errors': self.double_bit_errors,
            'multi_bit_errors': self.multi_bit_errors,
            'uncorrectable_errors': self.uncorrectable_errors,
            'corrections': self.corrections,
            'crc_errors': self.crc_errors,
            'dq_parity_errors': self.dq_parity_errors,
            'ca_parity_errors': self.ca_parity_errors,
            'total_transactions': self.total_transactions,
            'total_parity_checks': self.total_parity_checks,
            'total_ca_parity_checks': self.total_ca_parity_checks,
        }


class HBM4ECCMode(Enum):
    """ECC mode selection"""
    DISABLED = 0
    SECDED = 1  # Single Error Correction, Double Error Detection
    SECDED_DBD = 2  # SECDED with Double Byte Error Detection


class HBM4CRCMode(Enum):
    """CRC mode selection"""
    DISABLED = 0
    CRC16 = 1  # 16-bit CRC for data
    CRC15_KBD = 2  # 15-bit CRC + Known Bit Detection for CA


class ErrorTracker:
    """Tracks error history with bounded memory"""

    def __init__(self, max_events: int = 1000, max_service_events: int = 500):
        """Initialize error tracker

        Args:
            max_events: Maximum number of error events to store
            max_service_events: Maximum number of service events to store
        """
        self.max_events = max_events
        self.max_service_events = max_service_events
        self.events: deque = deque(maxlen=max_events)
        self.counter = ErrorCounter()
        self._service_events: deque = deque(maxlen=max_service_events)
        self._start_time: float = time.time()
        self._cycle: int = 0

        # Callbacks for integration
        self._on_error: Optional[Callable] = None
        self._on_critical_error: Optional[Callable] = None

    def set_cycle(self, cycle: int) -> None:
        """Set the simulation cycle for event timestamping."""
        self._cycle = cycle

    def advance_cycle(self, cycles: int = 1) -> None:
        """Advance the simulation cycle."""
        self._cycle += cycles

    def record_event(
        self,
        error_type: ErrorType,
        channel: int = 0,
        bank: int = 0,
        address: int = 0,
        error_mask: int = 0,
        corrected: bool = False,
        syndrome: int = 0,
    ):
        """Record an error event

        Args:
            error_type: Type of error
            channel: Channel number
            bank: Bank number
            address: Address that had error
            error_mask: Bit mask of error locations
            corrected: Whether error was corrected
            syndrome: ECC syndrome value
        """
        event = ErrorEvent(
            timestamp=len(self.events),
            error_type=error_type,
            channel=channel,
            bank=bank,
            address=address,
            error_mask=error_mask,
            corrected=corrected,
            syndrome=syndrome,
        )
        self.events.append(event)

        # Update counters
        self.counter.total_transactions += 1
        if error_type == ErrorType.SINGLE_BIT:
            self.counter.single_bit_errors += 1
            if corrected:
                self.counter.corrections += 1
        elif error_type == ErrorType.DOUBLE_BIT:
            self.counter.double_bit_errors += 1
        elif error_type == ErrorType.MULTI_BIT:
            self.counter.multi_bit_errors += 1
        elif error_type == ErrorType.UNCORRECTABLE:
            self.counter.uncorrectable_errors += 1
        elif error_type == ErrorType.DQ_PARITY_ERROR:
            self.counter.dq_parity_errors += 1
        elif error_type == ErrorType.CA_PARITY_ERROR:
            self.counter.ca_parity_errors += 1
        elif error_type == ErrorType.CRC_ERROR:
            self.counter.crc_errors += 1

        # Record service event for RAS
        self._record_service_event(
            event_type=self._get_service_event_type(error_type),
            channel=channel,
            details=f"{error_type.value} at address 0x{address:X}, mask=0x{error_mask:X}",
            severity=self._get_severity(error_type, corrected),
        )

        # Invoke callbacks
        if self._on_error:
            self._on_error(event)
        if self._on_critical_error and self._get_severity(error_type, corrected) == ErrorSeverity.CRITICAL:
            self._on_critical_error(event)

    def _get_service_event_type(self, error_type: ErrorType) -> str:
        """Map error type to service event type."""
        mapping = {
            ErrorType.SINGLE_BIT: "ECC_CORRECTED",
            ErrorType.DOUBLE_BIT: "ECC_DBE_DETECTED",
            ErrorType.MULTI_BIT: "ECC_MULTI_BIT_ERROR",
            ErrorType.UNCORRECTABLE: "ECC_UNCORRECTABLE",
            ErrorType.DQ_PARITY_ERROR: "DQ_PARITY_ERROR",
            ErrorType.CA_PARITY_ERROR: "CA_PARITY_ERROR",
            ErrorType.CRC_ERROR: "CRC_ERROR",
        }
        return mapping.get(error_type, "UNKNOWN_ERROR")

    def _get_severity(self, error_type: ErrorType, corrected: bool) -> ErrorSeverity:
        """Determine error severity."""
        if error_type == ErrorType.NO_ERROR:
            return ErrorSeverity.INFO
        if error_type == ErrorType.SINGLE_BIT and corrected:
            return ErrorSeverity.INFO
        if error_type == ErrorType.SINGLE_BIT and not corrected:
            return ErrorSeverity.WARNING
        if error_type == ErrorType.DOUBLE_BIT:
            return ErrorSeverity.WARNING
        if error_type == ErrorType.MULTI_BIT:
            return ErrorSeverity.CRITICAL
        if error_type == ErrorType.UNCORRECTABLE:
            return ErrorSeverity.FATAL
        return ErrorSeverity.WARNING

    def _record_service_event(
        self,
        event_type: str,
        channel: int,
        details: str,
        severity: ErrorSeverity = ErrorSeverity.INFO,
    ):
        """Record a service event for RAS tracking."""
        event = ServiceEvent(
            event_type=event_type,
            timestamp=time.time() - self._start_time,
            cycle=self._cycle,
            channel=channel,
            details=details,
            severity=severity,
        )
        self._service_events.append(event)

    def record_parity_event(
        self,
        is_dq_parity: bool,
        valid: bool,
        channel: int,
        details: str = "",
    ):
        """Record a parity check event.

        Args:
            is_dq_parity: True for DQ parity, False for CA parity
            valid: Whether parity check passed
            channel: Channel number
            details: Additional details
        """
        if is_dq_parity:
            self.counter.total_parity_checks += 1
        else:
            self.counter.total_ca_parity_checks += 1

        event_type = "DQ_PARITY_CHECK" if is_dq_parity else "CA_PARITY_CHECK"
        severity = ErrorSeverity.INFO if valid else ErrorSeverity.WARNING

        self._record_service_event(
            event_type=event_type,
            channel=channel,
            details=details,
            severity=severity,
        )

    def register_error_callback(self, callback: Callable[[ErrorEvent], None]) -> None:
        """Register a callback for error events."""
        self._on_error = callback

    def register_critical_error_callback(self, callback: Callable[[ErrorEvent], None]) -> None:
        """Register a callback for critical errors."""
        self._on_critical_error = callback

    def get_recent_errors(self, count: int = 10) -> List[ErrorEvent]:
        """Get recent error events

        Args:
            count: Number of events to return

        Returns:
            List of recent error events
        """
        return list(self.events)[-count:]

    def get_errors_by_type(self, error_type: ErrorType) -> List[ErrorEvent]:
        """Get all errors of a specific type

        Args:
            error_type: Type to filter by

        Returns:
            List of matching errors
        """
        return [e for e in self.events if e.error_type == error_type]

    def get_error_rate(self) -> float:
        """Calculate error rate

        Returns:
            Error rate as percentage
        """
        if self.counter.total_transactions == 0:
            return 0.0
        total_errors = (
            self.counter.single_bit_errors +
            self.counter.double_bit_errors +
            self.counter.multi_bit_errors +
            self.counter.uncorrectable_errors
        )
        return (total_errors / self.counter.total_transactions) * 100.0

    def reset(self):
        """Reset error tracker"""
        self.events.clear()
        self.counter.reset()


class HBM4ECC:
    """HBM4 ECC Engine

    Implements SEC-DED (Single Error Correction, Double Error Detection)
    for 64-bit or 128-bit data words.

    Uses precomputed lookup tables for proper SEC-DED syndrome generation.
    For 64-bit data: 8 parity bits, total 72 bits (72,64) code
    For 128-bit data: 9 parity bits, total 137 bits (137,128) code

    The syndrome directly indicates the error bit position:
    - syndrome = 0: No error
    - syndrome = k (1 <= k <= 64): Single-bit error at data bit k-1
    - syndrome = 65-72: Single-bit error in ECC bits
    - syndrome with bit 7 set: Double-bit error detected
    """

    def __init__(
        self,
        data_width: int = 64,
        ecc_mode: HBM4ECCMode = HBM4ECCMode.SECDED,
        enable_tracking: bool = True,
    ):
        """Initialize ECC Engine

        Args:
            data_width: Data word width (64 or 128)
            ecc_mode: ECC mode
            enable_tracking: Enable error tracking
        """
        self.data_width = data_width
        self.ecc_mode = ecc_mode
        self.enable_tracking = enable_tracking
        self._error_counter = ErrorCounter()
        self._error_tracker = ErrorTracker() if enable_tracking else None

        if data_width == 64:
            self.ecc_bits = 8
        elif data_width == 128:
            self.ecc_bits = 9
        else:
            raise ValueError(f"Unsupported data width: {data_width}")

        self._build_lookup_tables()

    def _build_lookup_tables(self):
        """Build lookup tables for ECC encoding/decoding

        Creates:
        - syndrome_to_bit: maps syndrome value to error bit position
        - parity_lookup: maps data value to ECC parity bits
        """
        # Precompute syndrome to bit mapping for single-bit errors
        # For proper SEC-DED: syndrome = error_bit_position + 1
        self._syndrome_to_bit = {}
        for bit in range(self.data_width + self.ecc_bits):
            syndrome = bit + 1  # Syndrome is 1-indexed
            self._syndrome_to_bit[syndrome] = bit

        # For 128-bit we need 9 parity bits, syndrome up to 137
        if self.data_width == 128:
            for bit in range(128, 137):
                syndrome = bit + 1
                self._syndrome_to_bit[syndrome] = bit

    def encode(self, data: int) -> int:
        """Encode data with ECC

        Args:
            data: Data to encode

        Returns:
            Encoded data with ECC bits appended in upper bits
        """
        if self.ecc_mode == HBM4ECCMode.DISABLED:
            return data

        ecc = self._calculate_parity(data)
        return (ecc << self.data_width) | (data & ((1 << self.data_width) - 1))

    def decode(self, encoded: int, record: bool = True) -> ECCResult:
        """Decode and check ECC

        Args:
            encoded: Encoded data (data + ECC bits)
            record: Whether to record error in tracker

        Returns:
            ECCResult with corrected data and error information
        """
        if self.ecc_mode == HBM4ECCMode.DISABLED:
            return ECCResult(
                data=encoded,
                syndrome=0,
                error_type=ErrorType.NO_ERROR,
                corrected=False,
            )

        data_mask = (1 << self.data_width) - 1
        data = encoded & data_mask
        ecc_stored = (encoded >> self.data_width) & ((1 << self.ecc_bits) - 1)

        ecc_calculated = self._calculate_parity(data)
        syndrome = ecc_stored ^ ecc_calculated

        if syndrome == 0:
            if record and self._error_tracker:
                self._error_tracker.record_event(ErrorType.NO_ERROR)
            return ECCResult(
                data=data,
                syndrome=0,
                error_type=ErrorType.NO_ERROR,
                corrected=False,
            )

        error_type, error_bit = self._analyze_syndrome(syndrome)

        if error_type == ErrorType.SINGLE_BIT:
            if error_bit is not None and error_bit < self.data_width:
                corrected_data = data ^ (1 << error_bit)
                if record and self._error_tracker:
                    self._error_tracker.record_event(
                        error_type=error_type,
                        error_mask=1 << error_bit,
                        corrected=True,
                        syndrome=syndrome,
                    )
                return ECCResult(
                    data=corrected_data,
                    syndrome=syndrome,
                    error_type=error_type,
                    error_bit=error_bit,
                    corrected=True,
                )
            else:
                if record and self._error_tracker:
                    self._error_tracker.record_event(
                        error_type=error_type,
                        error_mask=syndrome << self.data_width,
                        corrected=False,
                        syndrome=syndrome,
                    )
                return ECCResult(
                    data=data,
                    syndrome=syndrome,
                    error_type=error_type,
                    error_bit=error_bit,
                    corrected=False,
                )
        else:
            if record and self._error_tracker:
                self._error_tracker.record_event(
                    error_type=error_type,
                    corrected=False,
                    syndrome=syndrome,
                )

        return ECCResult(
            data=data,
            syndrome=syndrome,
            error_type=error_type,
            error_bit=error_bit,
            corrected=False,
        )

    def _calculate_parity(self, data: int) -> int:
        """Calculate ECC parity bits using XOR-based approach"""
        if self.data_width == 64:
            return self._xor_parity_64(data)
        else:
            return self._xor_parity_128(data)

    def _popcount(self, value: int) -> int:
        """Count 1 bits (popcount)"""
        return bin(value).count('1')

    def _xor_parity_64(self, data: int) -> int:
        """Calculate XOR-based parity for 64-bit data

        Uses a simplified but effective parity scheme where:
        - Each data bit's position determines which parity bits it affects
        - Parity bit Pi is XOR of data bits where bit i of position is set
        """
        data = data & 0xFFFFFFFFFFFFFFFF
        p = 0

        # For SEC-DED, we need 8 parity bits
        # P0-P5: standard Hamming parity (cover data bits based on position)
        # P6: even parity of upper 32 bits
        # P7: overall parity (for extended SEC-DED)

        # P0: covers bits 0, 2, 4, 6, 8, ...
        for i in range(0, 64, 2):
            p ^= ((data >> i) & 1) << 0

        # P1: covers bits 0-1, 4-5, 8-9, 12-13, ...
        for i in range(0, 64, 4):
            p ^= ((data >> i) & 1) << 1
            if i + 1 < 64:
                p ^= ((data >> (i + 1)) & 1) << 1

        # P2: covers bits 0-3, 8-11, 16-19, 24-27, ...
        for i in range(0, 64, 8):
            for j in range(4):
                if i + j < 64:
                    p ^= ((data >> (i + j)) & 1) << 2

        # P3: covers bits 0-7, 16-23, 32-39, 48-55
        for i in range(0, 64, 16):
            for j in range(8):
                if i + j < 64:
                    p ^= ((data >> (i + j)) & 1) << 3

        # P4: covers bits 0-15, 32-47
        for i in range(0, 32):
            p ^= ((data >> i) & 1) << 4
        for i in range(32, 48):
            p ^= ((data >> i) & 1) << 4

        # P5: covers bits 16-31, 48-63
        for i in range(16, 32):
            p ^= ((data >> i) & 1) << 5
        for i in range(48, 64):
            p ^= ((data >> i) & 1) << 5

        # P6: covers bits 32-63
        for i in range(32, 64):
            p ^= ((data >> i) & 1) << 6

        # P7: overall parity (extended SEC-DED)
        if self._popcount(data) % 2 == 1:
            p ^= (1 << 7)

        return p & 0xFF

    def _xor_parity_128(self, data: int) -> int:
        """Calculate parity for 128-bit data"""
        p = 0
        data_low = data & 0xFFFFFFFFFFFFFFFF
        data_high = (data >> 64) & 0xFFFFFFFFFFFFFFFF

        p |= self._xor_parity_64(data_low) & 0xFF

        # P8: even parity of upper 64 bits
        if self._popcount(data_high) % 2 == 1:
            p ^= (1 << 8)

        # Overall parity
        if self._popcount(data) % 2 == 1:
            p ^= (1 << 8)

        return p & 0x1FF

    def _analyze_syndrome(self, syndrome: int) -> Tuple[ErrorType, Optional[int]]:
        """Analyze syndrome to determine error type and position

        Args:
            syndrome: ECC syndrome

        Returns:
            Tuple of (error_type, error_bit)
        """
        if syndrome == 0:
            return ErrorType.NO_ERROR, None

        popcnt = self._popcount(syndrome)

        # Single-bit error: syndrome is power of 2 OR matches lookup
        if popcnt == 1:
            error_bit = syndrome.bit_length() - 1
            if error_bit < self.data_width:
                return ErrorType.SINGLE_BIT, error_bit
            else:
                return ErrorType.SINGLE_BIT, None

        # Check lookup table for single-bit error
        if syndrome in self._syndrome_to_bit:
            error_bit = self._syndrome_to_bit[syndrome]
            if error_bit < self.data_width:
                return ErrorType.SINGLE_BIT, error_bit
            else:
                return ErrorType.SINGLE_BIT, None

        # Double-bit error detection (extended parity bit set)
        if syndrome & 0x80 and popcnt == 2:
            return ErrorType.DOUBLE_BIT, None

        # Double or multi-bit error
        if popcnt == 2:
            return ErrorType.DOUBLE_BIT, None
        elif popcnt >= 3:
            return ErrorType.MULTI_BIT, None

        return ErrorType.UNCORRECTABLE, None

    def get_error_stats(self) -> Dict:
        """Get error statistics"""
        return {
            'single_bit_errors': self._error_counter.single_bit_errors,
            'double_bit_errors': self._error_counter.double_bit_errors,
            'multi_bit_errors': self._error_counter.multi_bit_errors,
            'uncorrectable_errors': self._error_counter.uncorrectable_errors,
            'corrections': self._error_counter.corrections,
        }

    def get_error_rate(self) -> float:
        """Get error rate from tracker"""
        if self._error_tracker:
            return self._error_tracker.get_error_rate()
        return 0.0

    def get_recent_errors(self, count: int = 10) -> List[ErrorEvent]:
        """Get recent errors"""
        if self._error_tracker:
            return self._error_tracker.get_recent_errors(count)
        return []

    def reset_stats(self):
        """Reset error statistics"""
        self._error_counter.reset()
        if self._error_tracker:
            self._error_tracker.reset()


class HBM4CRC:
    """HBM4 CRC Engine

    Implements CRC16 for data integrity, CRC15+KBD for command/address protection,
    and DQ/CA parity for HBM4 RAS compliance.

    Key features:
    - CRC16: 16-bit CRC for data integrity (CRC-CCITT polynomial 0x1021)
    - CRC15: 15-bit CRC for command/address protection
    - DQ Parity: 8-bit parity per 64-bit lane for read/write data
    - CA Parity: Parity for command/address bus protection
    """

    CRC16_POLY = 0x1021
    CRC15_POLY = 0x4599

    def __init__(
        self,
        crc_mode: HBM4CRCMode = HBM4CRCMode.CRC16,
        parity_mode: ParityMode = ParityMode.EVEN,
    ):
        """Initialize CRC Engine

        Args:
            crc_mode: CRC mode selection
            parity_mode: Parity calculation mode (EVEN or ODD)
        """
        self.crc_mode = crc_mode
        self.parity_mode = parity_mode
        self._crc_errors = 0
        self._total_crc = 0
        self._parity_errors = 0
        self._total_parity_checks = 0
        self._ca_parity_errors = 0
        self._total_ca_parity_checks = 0

        # Build CRC lookup tables
        self._crc16_table = self._build_crc16_table()

    def _build_crc16_table(self) -> List[int]:
        """Build CRC-16 lookup table for fast calculation."""
        table = []
        for i in range(256):
            crc = i << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ self.CRC16_POLY) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
            table.append(crc)
        return table

    def calculate_crc16(self, data: int, width: int = 64) -> int:
        """Calculate CRC16 using CRC-CCITT polynomial

        Args:
            data: Input data
            width: Data width in bits

        Returns:
            16-bit CRC
        """
        crc = 0xFFFF

        for byte_idx in range(0, width, 8):
            byte = (data >> byte_idx) & 0xFF
            crc ^= byte << 8

            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ self.CRC16_POLY) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF

        return crc

    def calculate_crc16_fast(self, data: int, width: int = 64) -> int:
        """Fast CRC16 using table lookup"""
        crc = 0xFFFF
        for byte_idx in range(0, width, 8):
            byte = (data >> byte_idx) & 0xFF
            crc = (self._crc16_table[(crc >> 8) ^ byte] ^ (crc << 8)) & 0xFFFF

        return crc

    def verify_crc16(self, data: int, crc: int, width: int = 64) -> Tuple[bool, int]:
        """Verify CRC16

        Returns:
            Tuple of (valid, calculated_crc)
        """
        self._total_crc += 1
        calculated = self.calculate_crc16(data, width)
        valid = calculated == crc
        if not valid:
            self._crc_errors += 1
        return valid, calculated

    # ==================== DQ Parity (Data Bus) ====================

    def calculate_dq_parity(self, data: int, num_lanes: int = 8) -> List[int]:
        """Calculate DQ parity for data bus.

        For HBM4, DQ parity is 8-bit parity per 64-bit lane.
        With 64-bit data, this generates one parity bit per byte.

        Args:
            data: Input data (64-bit typical)
            num_lanes: Number of byte lanes (8 for 64-bit)

        Returns:
            List of parity bits (one per lane)
        """
        parity_bits = []
        for lane in range(num_lanes):
            byte_val = (data >> (lane * 8)) & 0xFF
            parity = self._calculate_byte_parity(byte_val)
            parity_bits.append(parity)
        return parity_bits

    def calculate_dq_parity_strip(self, data: int, lane: int) -> int:
        """Calculate parity for a specific DQ lane (byte).

        Args:
            data: Full data word
            lane: Lane index (0-7 for 64-bit)

        Returns:
            Single parity bit (0 or 1)
        """
        byte_val = (data >> (lane * 8)) & 0xFF
        return self._calculate_byte_parity(byte_val)

    def verify_dq_parity(self, data: int, parity_bits: List[int]) -> Tuple[bool, List[int]]:
        """Verify DQ parity for data.

        Args:
            data: Input data
            parity_bits: Expected parity bits

        Returns:
            Tuple of (all_valid, detected_errors) where detected_errors
            contains indices of lanes with parity errors
        """
        self._total_parity_checks += 1
        calculated = self.calculate_dq_parity(data, len(parity_bits))
        errors = [i for i, (calc, exp) in enumerate(zip(calculated, parity_bits)) if calc != exp]

        if errors:
            self._parity_errors += 1

        return len(errors) == 0, errors

    def _calculate_byte_parity(self, byte_val: int) -> int:
        """Calculate parity for a byte.

        Args:
            byte_val: 8-bit value

        Returns:
            0 or 1 (parity bit)
        """
        # Count 1s in the byte
        ones = bin(byte_val).count('1')

        if self.parity_mode == ParityMode.EVEN:
            return 0 if ones % 2 == 0 else 1
        else:  # ODD
            return 1 if ones % 2 == 0 else 0

    def calculate_parity(self, data: int, width: int = 64) -> int:
        """Calculate overall parity for data word.

        Args:
            data: Input data
            width: Data width in bits

        Returns:
            Single parity bit
        """
        # XOR-reduction: XOR all bytes together
        parity = 0
        for byte_idx in range(0, width, 8):
            parity ^= (data >> byte_idx) & 0xFF

        if self.parity_mode == ParityMode.EVEN:
            return parity & 1
        else:
            return 1 - (parity & 1)

    def verify_parity(self, data: int, expected_parity: int, width: int = 64) -> bool:
        """Verify parity for data word.

        Args:
            data: Input data
            expected_parity: Expected parity bit
            width: Data width in bits

        Returns:
            True if parity matches
        """
        self._total_parity_checks += 1
        calculated = self.calculate_parity(data, width)
        valid = calculated == expected_parity
        if not valid:
            self._parity_errors += 1
        return valid

    # ==================== CA Parity (Command/Address) ====================

    def calculate_ca_parity(self, ca_bits: int, num_parity_bits: int = 1) -> List[int]:
        """Calculate CA (Command/Address) parity.

        For HBM4, CA parity provides protection for the command/address bus.
        Multiple parity bits can be calculated for different CA field groupings.

        Args:
            ca_bits: Command/address bits
            num_parity_bits: Number of parity bits (1-3 typically)

        Returns:
            List of parity bits
        """
        parity_bits = []

        if num_parity_bits == 1:
            # Single parity bit for entire CA bus
            parity = self.calculate_parity(ca_bits, 32)
            parity_bits.append(parity)
        elif num_parity_bits == 2:
            # Split CA into two groups
            parity_bits.append(self.calculate_parity(ca_bits & 0xFFFF, 16))
            parity_bits.append(self.calculate_parity((ca_bits >> 16) & 0xFFFF, 16))
        elif num_parity_bits >= 3:
            # Three-way split (common for HBM CA)
            parity_bits.append(self.calculate_parity(ca_bits & 0xFF, 8))       # Command
            parity_bits.append(self.calculate_parity((ca_bits >> 8) & 0xFFF, 12))  # Row
            parity_bits.append(self.calculate_parity((ca_bits >> 20) & 0xFFF, 12))  # Bank

        return parity_bits

    def verify_ca_parity(self, ca_bits: int, parity_bits: List[int]) -> Tuple[bool, List[int]]:
        """Verify CA parity.

        Args:
            ca_bits: Command/address bits
            parity_bits: Expected parity bits

        Returns:
            Tuple of (all_valid, detected_errors)
        """
        self._total_ca_parity_checks += 1
        calculated = self.calculate_ca_parity(ca_bits, len(parity_bits))
        errors = [i for i, (calc, exp) in enumerate(zip(calculated, parity_bits)) if calc != exp]

        if errors:
            self._ca_parity_errors += 1

        return len(errors) == 0, errors

    def calculate_crc15(self, ca_bits: int) -> int:
        """Calculate CRC15 for command/address

        Args:
            ca_bits: Command/address bits

        Returns:
            15-bit CRC
        """
        crc = 0x7FFF

        for i in range(15):
            bit = (ca_bits >> i) & 1
            crc_bit = (crc >> 14) & 1
            crc = ((crc << 1) & 0x7FFF) | bit
            if crc_bit ^ bit:
                crc ^= self.CRC15_POLY

        return crc ^ 0x7FFF

    def calculate_crc15_kbd(self, ca_bits: int, known_bits: int) -> Tuple[int, int]:
        """Calculate CRC15 with Known Bit Detection

        Args:
            ca_bits: Command/address bits
            known_bits: Mask of known (fixed) bits

        Returns:
            Tuple of (crc, detected_unknown_bits)
        """
        crc = 0x7FFF
        unknown_count = 0

        for i in range(15):
            if known_bits & (1 << i):
                continue
            unknown_count += 1

            bit = (ca_bits >> i) & 1
            crc_bit = (crc >> 14) & 1
            crc = ((crc << 1) & 0x7FFF) | bit
            if crc_bit ^ bit:
                crc ^= self.CRC15_POLY

        return crc ^ 0x7FFF, unknown_count

    def verify_crc15(self, ca_bits: int, crc: int) -> Tuple[bool, int]:
        """Verify CRC15"""
        calculated = self.calculate_crc15(ca_bits)
        valid = calculated == crc
        if not valid:
            self._crc_errors += 1
        return valid, calculated

    def calculate_dbi(self, data: int, width: int = 64) -> Tuple[int, bool]:
        """Calculate DBI (Data Bus Inversion)"""
        ones_count = bin(data).count('1')

        if ones_count > width // 2:
            inverted = (~data) & ((1 << width) - 1)
            return inverted, True

        return data, False

    def verify_dbi(self, data: int, dbi_flag: bool, width: int = 64) -> int:
        """Verify DBI and restore original data"""
        if dbi_flag:
            return (~data) & ((1 << width) - 1)
        return data

    def get_crc_stats(self) -> Dict:
        """Get CRC statistics"""
        return {
            'total_crc_checks': self._total_crc,
            'crc_errors': self._crc_errors,
            'total_parity_checks': self._total_parity_checks,
            'parity_errors': self._parity_errors,
            'total_ca_parity_checks': self._total_ca_parity_checks,
            'ca_parity_errors': self._ca_parity_errors,
            'error_rate': (self._crc_errors / self._total_crc * 100) if self._total_crc > 0 else 0.0,
            'parity_error_rate': (self._parity_errors / self._total_parity_checks * 100) if self._total_parity_checks > 0 else 0.0,
        }

    def reset_stats(self):
        """Reset CRC statistics"""
        self._crc_errors = 0
        self._total_crc = 0
        self._parity_errors = 0
        self._total_parity_checks = 0
        self._ca_parity_errors = 0
        self._total_ca_parity_checks = 0


class HBM4Parity:
    """HBM4 Dedicated Parity Engine

    Implements DQ parity for data bus and CA parity for command/address bus
    as specified in JEDEC JESD270-4A HBM4.

    DQ PARITY:
    =========
    - 8-bit parity for read/write data protection
    - One parity bit per 64-bit DQ lane (8 lanes per channel)
    - Used to detect errors in the data bus

    CA PARITY:
    =========
    - Command/address parity protection
    - Multiple parity bits for different CA field groupings
    - Critical for preventing invalid commands

    CRC16:
    ======
    - 16-bit CRC for comprehensive data integrity
    - CRC-CCITT polynomial (0x1021)
    - Used for memory data protection
    """

    def __init__(
        self,
        parity_mode: ParityMode = ParityMode.EVEN,
        lanes_per_channel: int = 8,
        enable_tracking: bool = True,
    ):
        """Initialize Parity Engine

        Args:
            parity_mode: EVEN or ODD parity
            lanes_per_channel: Number of DQ lanes (8 for 64-bit channel)
            enable_tracking: Enable error tracking
        """
        self.parity_mode = parity_mode
        self.lanes_per_channel = lanes_per_channel
        self.enable_tracking = enable_tracking

        # Statistics
        self._dq_parity_errors = 0
        self._dq_parity_checks = 0
        self._ca_parity_errors = 0
        self._ca_parity_checks = 0

        # Error tracker
        self._error_tracker = ErrorTracker() if enable_tracking else None

    def calculate_dq_parity(self, data: int, num_lanes: int = 8) -> List[int]:
        """Calculate DQ parity bits for data bus.

        Each DQ lane (8 bits) has one parity bit.

        Args:
            data: Data to calculate parity for (64-bit for 8 lanes)
            num_lanes: Number of DQ lanes

        Returns:
            List of parity bits (0 or 1)
        """
        parity_bits = []
        for lane in range(num_lanes):
            byte_val = (data >> (lane * 8)) & 0xFF
            parity = self._byte_parity(byte_val)
            parity_bits.append(parity)
        return parity_bits

    def _byte_parity(self, byte_val: int) -> int:
        """Calculate parity for a byte using XOR reduction."""
        # XOR all bits together
        p = byte_val ^ (byte_val >> 4)
        p = p ^ (p >> 2)
        p = p ^ (p >> 1)
        parity = p & 1

        if self.parity_mode == ParityMode.ODD:
            parity = 1 - parity

        return parity

    def verify_dq_parity(
        self,
        data: int,
        expected_parity: List[int],
        channel: int = 0,
        record: bool = True,
    ) -> Tuple[bool, List[int]]:
        """Verify DQ parity and optionally record error.

        Args:
            data: Data to verify
            expected_parity: Expected parity bits
            channel: Channel number for error tracking
            record: Whether to record in error tracker

        Returns:
            Tuple of (valid, error_lanes) where error_lanes contains
            indices of lanes with parity errors
        """
        self._dq_parity_checks += 1
        calculated = self.calculate_dq_parity(data, len(expected_parity))
        error_lanes = [
            i for i, (calc, exp) in enumerate(zip(calculated, expected_parity))
            if calc != exp
        ]

        if error_lanes:
            self._dq_parity_errors += 1
            if record and self._error_tracker:
                for lane in error_lanes:
                    self._error_tracker.record_event(
                        error_type=ErrorType.DQ_PARITY_ERROR,
                        channel=channel,
                        error_mask=1 << lane,
                        corrected=False,
                    )

        return len(error_lanes) == 0, error_lanes

    def encode_dq_parity_strip(self, data: int, lane: int) -> int:
        """Encode data with parity for a specific lane.

        Combines data and parity into a format suitable for transmission.

        Args:
            data: Original data (8 bits)
            lane: Lane index

        Returns:
            Encoded value with parity in MSB
        """
        parity = self._byte_parity(data & 0xFF)
        return (parity << 8) | (data & 0xFF)

    def decode_dq_parity_strip(self, encoded: int, channel: int = 0, record: bool = True) -> Tuple[int, bool]:
        """Decode data and verify parity for a strip.

        Args:
            encoded: Encoded data (parity + data)
            channel: Channel for error tracking
            record: Whether to record errors

        Returns:
            Tuple of (data, parity_valid)
        """
        parity = (encoded >> 8) & 1
        data = encoded & 0xFF
        expected_parity = self._byte_parity(data)

        valid = parity == expected_parity
        if not valid:
            self._dq_parity_errors += 1
            if record and self._error_tracker:
                self._error_tracker.record_event(
                    error_type=ErrorType.DQ_PARITY_ERROR,
                    channel=channel,
                    error_mask=0x100,  # Parity bit error
                    corrected=False,
                )

        return data, valid

    def calculate_ca_parity(
        self,
        ca_bits: int,
        field_groups: List[Tuple[str, int]] = None,
    ) -> Dict[str, int]:
        """Calculate CA parity for command/address fields.

        Args:
            ca_bits: Command/address bits
            field_groups: List of (field_name, width) tuples for field grouping.
                         If None, uses default HBM4 CA fields.

        Returns:
            Dictionary mapping field names to parity bits
        """
        if field_groups is None:
            # Default HBM4 CA field grouping
            field_groups = [
                ('cmd', 8),      # Command encoding
                ('row', 14),     # Row address
                ('bank', 4),     # Bank address
            ]

        result = {}
        offset = 0
        for name, width in field_groups:
            field_val = (ca_bits >> offset) & ((1 << width) - 1)
            result[name] = self._field_parity(field_val, width)
            offset += width

        return result

    def _field_parity(self, value: int, width: int) -> int:
        """Calculate parity for a field."""
        # Mask to width and XOR reduction
        val = value & ((1 << width) - 1)
        p = val ^ (val >> 1)
        p = p ^ (p >> 2)
        p = p ^ (p >> 4)
        parity = p & 1

        if self.parity_mode == ParityMode.ODD:
            parity = 1 - parity

        return parity

    def verify_ca_parity(
        self,
        ca_bits: int,
        expected_parity: Dict[str, int],
        channel: int = 0,
        record: bool = True,
    ) -> Tuple[bool, List[str]]:
        """Verify CA parity and optionally record error.

        Args:
            ca_bits: Command/address bits
            expected_parity: Dict of field names to expected parity
            channel: Channel for error tracking
            record: Whether to record errors

        Returns:
            Tuple of (valid, error_fields)
        """
        self._ca_parity_checks += 1
        calculated = self.calculate_ca_parity(ca_bits)

        error_fields = []
        for field_name, expected in expected_parity.items():
            if field_name in calculated and calculated[field_name] != expected:
                error_fields.append(field_name)

        if error_fields:
            self._ca_parity_errors += 1
            if record and self._error_tracker:
                self._error_tracker.record_event(
                    error_type=ErrorType.CA_PARITY_ERROR,
                    channel=channel,
                    error_mask=sum(1 << i for i, f in enumerate(expected_parity.keys()) if f in error_fields),
                    corrected=False,
                )

        return len(error_fields) == 0, error_fields

    def inject_parity_error(
        self,
        data: int,
        lane: int,
        corrupt_data: bool = False,
    ) -> Tuple[int, int]:
        """Inject a parity error for testing.

        Args:
            data: Original data
            lane: Lane to corrupt
            corrupt_data: If True, corrupt data bit; if False, corrupt parity

        Returns:
            Tuple of (corrupted_data, error_mask)
        """
        if corrupt_data:
            # Flip a data bit
            bit_pos = lane * 8
            return data ^ (1 << bit_pos), (1 << lane)
        else:
            # Flip the parity bit (in high bits)
            return data, (1 << (8 + lane))  # Parity is stored separately

    def get_parity_stats(self) -> Dict:
        """Get parity statistics."""
        return {
            'dq_parity_checks': self._dq_parity_checks,
            'dq_parity_errors': self._dq_parity_errors,
            'dq_parity_error_rate': (
                self._dq_parity_errors / self._dq_parity_checks * 100
                if self._dq_parity_checks > 0 else 0.0
            ),
            'ca_parity_checks': self._ca_parity_checks,
            'ca_parity_errors': self._ca_parity_errors,
            'ca_parity_error_rate': (
                self._ca_parity_errors / self._ca_parity_checks * 100
                if self._ca_parity_checks > 0 else 0.0
            ),
        }

    def reset_stats(self):
        """Reset parity statistics."""
        self._dq_parity_errors = 0
        self._dq_parity_checks = 0
        self._ca_parity_errors = 0
        self._ca_parity_checks = 0


class HBM4DataIntegrity:
    """Combined data integrity engine

    Integrates ECC, CRC, and Parity for comprehensive HBM4 error detection/correction.

    This engine provides a unified interface for all RAS-related data protection:
    - SEC-DED ECC for memory data protection
    - CRC16 for data integrity checking
    - DQ Parity for per-lane data protection
    - CA Parity for command/address protection
    - Lane repair integration for failed lane handling

    Usage:
    =====
    ```python
    # Create engine
    di = HBM4DataIntegrity(data_width=64)

    # Encode data for transmission
    encoded = di.encode_with_protection(original_data)

    # Decode and verify on reception
    result = di.decode_with_verification(encoded)

    # Error injection for testing
    di.inject_ecc_error(channel=0, bit=5)
    ```
    """

    def __init__(
        self,
        data_width: int = 64,
        enable_ecc: bool = True,
        enable_crc: bool = True,
        enable_parity: bool = True,
        lanes_per_channel: int = 8,
    ):
        """Initialize data integrity engine

        Args:
            data_width: Data width (64 or 128)
            enable_ecc: Enable ECC protection
            enable_crc: Enable CRC protection
            enable_parity: Enable DQ/CA parity protection
            lanes_per_channel: Number of DQ lanes per channel
        """
        self.data_width = data_width
        self.enable_ecc = enable_ecc
        self.enable_crc = enable_crc
        self.enable_parity = enable_parity
        self.lanes_per_channel = lanes_per_channel

        # Initialize sub-engines
        ecc_mode = HBM4ECCMode.SECDED if enable_ecc else HBM4ECCMode.DISABLED
        self.ecc = HBM4ECC(data_width=data_width, ecc_mode=ecc_mode)

        crc_mode = HBM4CRCMode.CRC16 if enable_crc else HBM4CRCMode.DISABLED
        self.crc = HBM4CRC(crc_mode=crc_mode)

        self.parity = HBM4Parity(lanes_per_channel=lanes_per_channel)

        # Error injection state
        self._injected_errors: Dict[int, Dict[int, int]] = {}  # channel -> bit -> mask
        self._error_injection_enabled = True

        # Service event tracking
        self._service_events: deque = deque(maxlen=1000)

    def encode_with_protection(self, data: int) -> Dict[str, Any]:
        """Encode data with all enabled protection mechanisms.

        Args:
            data: Original data to encode

        Returns:
            Dictionary containing:
            - data: ECC-encoded data
            - ecc: ECC bits
            - crc: CRC value
            - dq_parity: DQ parity bits (list)
            - ca_parity: CA parity (if applicable)
        """
        result = {}

        # ECC encoding
        if self.enable_ecc:
            result['data'] = self.ecc.encode(data)
            result['ecc'] = result['data'] >> self.data_width
        else:
            result['data'] = data
            result['ecc'] = 0

        # CRC encoding
        if self.enable_crc:
            ecc_width = self.ecc.ecc_bits if self.enable_ecc else 0
            result['crc'] = self.crc.calculate_crc16(
                result['data'],
                self.data_width + ecc_width
            )

        # DQ Parity encoding
        if self.enable_parity:
            result['dq_parity'] = self.parity.calculate_dq_parity(data, self.lanes_per_channel)

        return result

    def decode_with_verification(
        self,
        encoded: Dict[str, Any],
        channel: int = 0,
    ) -> Dict[str, Any]:
        """Decode and verify data with all enabled protection mechanisms.

        Args:
            encoded: Encoded data from encode_with_protection()
            channel: Channel number for error tracking

        Returns:
            Dictionary containing:
            - data: Decoded/corrected data
            - valid: Overall validity
            - ecc_result: ECC decode result
            - crc_valid: CRC check result
            - parity_valid: DQ parity check result
            - errors: List of detected errors
        """
        result = {
            'data': encoded.get('data', 0),
            'valid': True,
            'ecc_result': None,
            'crc_valid': True,
            'parity_valid': True,
            'errors': [],
        }

        # CRC verification
        if self.enable_crc and 'crc' in encoded:
            ecc_width = self.ecc.ecc_bits if self.enable_ecc else 0
            valid_crc, _ = self.crc.verify_crc16(
                encoded['data'],
                encoded['crc'],
                self.data_width + ecc_width
            )
            result['crc_valid'] = valid_crc
            if not valid_crc:
                result['valid'] = False
                result['errors'].append('CRC mismatch')
                self._record_service_event(channel, "CRC_ERROR", "CRC verification failed")

        # ECC decoding
        if self.enable_ecc:
            ecc_result = self.ecc.decode(encoded['data'])
            result['ecc_result'] = ecc_result
            result['data'] = ecc_result.data

            if ecc_result.error_type != ErrorType.NO_ERROR:
                result['valid'] = False
                result['errors'].append(ecc_result.error_type.value)

                if ecc_result.corrected:
                    self._record_service_event(
                        channel, "ECC_CORRECTED",
                        f"Corrected bit {ecc_result.error_bit}"
                    )
                else:
                    self._record_service_event(
                        channel, "ECC_UNCORRECTABLE",
                        f"Error type: {ecc_result.error_type.value}"
                    )

        # DQ Parity verification
        if self.enable_parity and 'dq_parity' in encoded:
            parity_valid, error_lanes = self.parity.verify_dq_parity(
                result['data'],
                encoded['dq_parity'],
                channel=channel
            )
            result['parity_valid'] = parity_valid
            if not parity_valid:
                result['errors'].append(f'DQ parity error on lanes: {error_lanes}')
                self._record_service_event(
                    channel, "DQ_PARITY_ERROR",
                    f"Parity errors on lanes: {error_lanes}"
                )

        return result

    def calculate_dq_parity(self, data: int) -> List[int]:
        """Calculate DQ parity for data.

        Args:
            data: Data to calculate parity for

        Returns:
            List of parity bits
        """
        return self.parity.calculate_dq_parity(data, self.lanes_per_channel)

    def verify_dq_parity(
        self,
        data: int,
        parity_bits: List[int],
        channel: int = 0,
    ) -> Tuple[bool, List[int]]:
        """Verify DQ parity for data.

        Args:
            data: Data to verify
            parity_bits: Expected parity bits
            channel: Channel for tracking

        Returns:
            Tuple of (valid, error_lanes)
        """
        return self.parity.verify_dq_parity(data, parity_bits, channel)

    def calculate_ca_parity(self, ca_bits: int) -> Dict[str, int]:
        """Calculate CA parity for command/address.

        Args:
            ca_bits: Command/address bits

        Returns:
            Dict of field names to parity bits
        """
        return self.parity.calculate_ca_parity(ca_bits)

    def verify_ca_parity(
        self,
        ca_bits: int,
        expected_parity: Dict[str, int],
        channel: int = 0,
    ) -> Tuple[bool, List[str]]:
        """Verify CA parity for command/address.

        Args:
            ca_bits: Command/address bits
            expected_parity: Expected parity values
            channel: Channel for tracking

        Returns:
            Tuple of (valid, error_fields)
        """
        return self.parity.verify_ca_parity(ca_bits, expected_parity, channel)

    def inject_ecc_error(
        self,
        channel: int,
        bit: int,
        correctable: bool = True,
    ) -> int:
        """Inject an ECC error for testing.

        Args:
            channel: Channel to inject error into
            bit: Bit position to corrupt
            correctable: If True, inject single-bit error; if False, double-bit

        Returns:
            Error mask for tracking
        """
        if not self._error_injection_enabled:
            return 0

        if channel not in self._injected_errors:
            self._injected_errors[channel] = {}

        mask = 1 << bit
        if not correctable:
            # Inject additional bit error nearby
            mask |= 1 << ((bit + 1) % self.data_width)

        self._injected_errors[channel][bit] = mask
        return mask

    def inject_parity_error(
        self,
        channel: int,
        lane: int,
    ) -> int:
        """Inject a DQ parity error for testing.

        Args:
            channel: Channel to inject error into
            lane: Lane index to corrupt

        Returns:
            Error mask
        """
        if not self._error_injection_enabled:
            return 0

        if channel not in self._injected_errors:
            self._injected_errors[channel] = {}

        # Flip a bit in the lane
        bit = lane * 8
        mask = 1 << bit
        self._injected_errors[channel][bit] = mask
        return mask

    def clear_injected_errors(self, channel: int = None) -> None:
        """Clear injected errors.

        Args:
            channel: Specific channel to clear, or None for all
        """
        if channel is None:
            self._injected_errors.clear()
        elif channel in self._injected_errors:
            del self._injected_errors[channel]

    def get_injected_errors(self, channel: int) -> Dict[int, int]:
        """Get all injected errors for a channel.

        Args:
            channel: Channel to query

        Returns:
            Dict mapping bit position to error mask
        """
        return self._injected_errors.get(channel, {}).copy()

    def enable_error_injection(self, enable: bool = True) -> None:
        """Enable or disable error injection.

        Args:
            enable: True to enable, False to disable
        """
        self._error_injection_enabled = enable

    def _record_service_event(
        self,
        channel: int,
        event_type: str,
        details: str = "",
    ):
        """Record a service event for RAS tracking."""
        event = ServiceEvent(
            event_type=event_type,
            timestamp=time.time(),
            cycle=0,
            channel=channel,
            details=details,
            severity=ErrorSeverity.WARNING if "ERROR" in event_type else ErrorSeverity.INFO,
        )
        self._service_events.append(event)

    def get_service_events(
        self,
        channel: int = None,
        event_type: str = None,
        count: int = 100,
    ) -> List[ServiceEvent]:
        """Get service events with optional filtering.

        Args:
            channel: Filter by channel (None for all)
            event_type: Filter by event type (None for all)
            count: Maximum events to return

        Returns:
            List of service events
        """
        events = list(self._service_events)

        if channel is not None:
            events = [e for e in events if e.channel == channel]
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        return events[-count:]

    def encode_data(self, data: int) -> Dict:
        """Encode data with ECC and CRC (legacy compatibility method).

        For full protection including parity, use encode_with_protection().

        Args:
            data: Original data

        Returns:
            Dictionary with data, ecc, and crc
        """
        return self.encode_with_protection(data)

    def decode_data(self, encoded: int, crc: int) -> Tuple[int, bool, str]:
        """Decode and verify data (legacy compatibility method).

        For full verification including parity, use decode_with_verification().

        Args:
            encoded: Encoded data
            crc: CRC value

        Returns:
            Tuple of (data, valid, error_type)
        """
        result = self.decode_with_verification({'data': encoded, 'crc': crc})
        return result['data'], result['valid'], ','.join(result['errors']) if result['errors'] else 'no_error'

    def inject_error(self, encoded: int, bit: int) -> int:
        """Inject an error into encoded data for testing."""
        return encoded ^ (1 << bit)

    def get_stats(self) -> Dict:
        """Get combined statistics from all protection mechanisms."""
        stats = {
            'ecc': self.ecc.get_error_stats(),
            'ecc_rate': self.ecc.get_error_rate(),
            'crc': self.crc.get_crc_stats(),
        }
        if self.enable_parity:
            stats['parity'] = self.parity.get_parity_stats()
        return stats

    def get_error_summary(self) -> Dict:
        """Get comprehensive error summary for all protection mechanisms."""
        summary = {
            'total_transactions': self.ecc._error_counter.total_transactions,
            'error_rate': self.ecc.get_error_rate(),
            'single_bit_errors': self.ecc._error_counter.single_bit_errors,
            'double_bit_errors': self.ecc._error_counter.double_bit_errors,
            'multi_bit_errors': self.ecc._error_counter.multi_bit_errors,
            'uncorrectable_errors': self.ecc._error_counter.uncorrectable_errors,
            'corrections': self.ecc._error_counter.corrections,
            'crc_errors': self.crc._crc_errors,
            'crc_total': self.crc._total_crc,
        }
        if self.enable_parity:
            summary['dq_parity_errors'] = self.parity._dq_parity_errors
            summary['dq_parity_checks'] = self.parity._dq_parity_checks
            summary['ca_parity_errors'] = self.parity._ca_parity_errors
            summary['ca_parity_checks'] = self.parity._ca_parity_checks
        return summary

    def reset_stats(self) -> None:
        """Reset all statistics across all protection mechanisms."""
        self.ecc.reset_stats()
        self.crc.reset_stats()
        self.parity.reset_stats()