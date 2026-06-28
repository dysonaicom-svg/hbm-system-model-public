"""
HBM4 Error Recovery Module

Implements comprehensive error detection and recovery for HBM4:
- ECC error detection and correction (SEC-DED)
- CRC error detection and handling
- Lane repair integration for hardware failures
- Retry mechanisms with configurable policies
- Error logging and reporting
- Multi-bit error handling
- Error injection for testing

Error Recovery Flow:
==================
1. Error Detection: ECC/CRC/Parity detects data corruption
2. Classification: Single-bit (correctable) vs multi-bit (uncorrectable)
3. Correction: Single-bit errors corrected via ECC
4. Retry: Uncorrectable errors trigger retry mechanism
5. Escalation: Persistent failures escalate to higher-level recovery
6. Logging: All errors and recovery actions are logged for analysis

Based on:
- JEDEC JESD270-4A HBM4 specification
- JEDEC JESD79-4C DDR4 SDRAM
- Synopsys HBM4 Controller IP error management
"""

from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import time
import random


class ErrorRecoveryLevel(Enum):
    """Error recovery escalation levels"""
    NONE = "none"                           # No error
    CORRECTED = "corrected"                 # Single-bit corrected
    RETRY = "retry"                        # Retry needed
    LANE_REPAIR = "lane_repair"             # Lane repair required
    CHANNEL_DISABLE = "channel_disable"     # Channel disabled
    SYSTEM_HALT = "system_halt"            # System halt required


class RetryPolicy(Enum):
    """Retry policy types"""
    IMMEDIATE = "immediate"                # Retry immediately
    EXPONENTIAL_BACKOFF = "exponential"    # Exponential backoff
    ADAPTIVE = "adaptive"                  # Adaptive based on error rate


class ErrorCategory(Enum):
    """Error categorization"""
    CORRECTABLE = "correctable"             # Single-bit ECC
    TRANSIENT = "transient"                # Transient errors (retry resolves)
    PERMANENT = "permanent"                # Permanent hardware failure
    INTERMITTENT = "intermittent"          # Intermittent failures


@dataclass
class ErrorRecord:
    """Single error event record"""
    error_id: int
    timestamp_ns: int
    cycle: int
    channel: int
    bank: int
    address: int
    error_type: str
    error_category: ErrorCategory
    recovery_level: ErrorRecoveryLevel
    data_bit_errors: int = 0
    retry_count: int = 0
    corrected: bool = False
    lane_id: Optional[int] = None
    details: str = ""


@dataclass
class RetryConfig:
    """Retry mechanism configuration"""
    max_retries: int = 3
    initial_delay_ns: int = 100
    max_delay_ns: int = 10000
    backoff_factor: float = 2.0
    policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF


@dataclass
class RecoveryStats:
    """Error recovery statistics"""
    total_errors: int = 0
    corrected_errors: int = 0
    retried_errors: int = 0
    retry_successes: int = 0
    retry_failures: int = 0
    lane_repairs: int = 0
    channel_disables: int = 0
    system_halts: int = 0

    def to_dict(self) -> Dict:
        return {
            'total_errors': self.total_errors,
            'corrected_errors': self.corrected_errors,
            'retried_errors': self.retried_errors,
            'retry_successes': self.retry_successes,
            'retry_failures': self.retry_failures,
            'lane_repairs': self.lane_repairs,
            'channel_disables': self.channel_disables,
            'system_halts': self.system_halts,
        }


class ErrorRecoveryController:
    """HBM4 Error Recovery Controller

    Implements comprehensive error detection and recovery for HBM4 memory.
    Handles single-bit error correction, retry mechanisms, lane repair
    integration, and escalation policies.

    USAGE:
    ======
    ```python
    recovery = ErrorRecoveryController(num_channels=32)

    # Process incoming data with error check
    result = recovery.process_read(
        channel=0, bank=1, address=0x1000,
        data=read_data, ecc=ecc_bits, crc=crc_value
    )

    if not result.valid:
        # Handle error
        recovery_action = recovery.handle_error(
            channel=0, error_type=result.error_type
        )

    # Check recovery statistics
    stats = recovery.get_stats()
    ```

    INTEGRATION:
    ===========
    - ECC Engine: Receives error information from ECC decode
    - Lane Repair: Triggers lane repair for permanent failures
    - Controller: Receives retry commands
    - System: Handles critical error escalation
    """

    def __init__(
        self,
        num_channels: int = 32,
        retry_config: Optional[RetryConfig] = None,
        enable_lane_repair: bool = True,
        enable_error_injection: bool = True,
    ):
        """Initialize Error Recovery Controller

        Args:
            num_channels: Number of HBM channels
            retry_config: Retry policy configuration
            enable_lane_repair: Enable lane repair integration
            enable_error_injection: Enable error injection for testing
        """
        self.num_channels = num_channels
        self.enable_lane_repair = enable_lane_repair
        self._error_injection_enabled = enable_error_injection

        # Retry configuration
        self._retry_config = retry_config or RetryConfig()

        # Lane repair integration (lazy import to avoid circular dependency)
        self._lane_repair = None

        # Error tracking
        self._error_history: deque = deque(maxlen=10000)
        self._error_id_counter: int = 0

        # Per-channel retry state
        self._retry_state: Dict[int, Dict[str, Any]] = {
            ch: {
                'retry_count': 0,
                'last_error_ns': 0,
                'consecutive_errors': 0,
            }
            for ch in range(num_channels)
        }

        # Statistics
        self._stats = RecoveryStats()

        # Hot block detection (4KB block granularity)
        self._hot_blocks: Dict[int, int] = {}  # block_addr -> error_count
        self._hot_block_threshold: int = 10

        # Error injection state
        self._injected_errors: Dict[Tuple[int, int], Dict] = {}

        # Callbacks
        self._on_error_detected: Optional[Callable] = None
        self._on_recovery_action: Optional[Callable] = None
        self._on_critical_error: Optional[Callable] = None

        # Simulation state
        self._current_cycle: int = 0
        self._current_time_ns: int = 0
        self._start_time_ns: int = 0

        # Error rate tracking for adaptive retry
        self._error_rate_window: deque = deque(maxlen=1000)
        self._last_error_rate_check: int = 0

    # ==================== Error Processing ====================

    def process_read(
        self,
        channel: int,
        bank: int,
        address: int,
        data: int,
        ecc: Optional[int] = None,
        crc: Optional[int] = None,
        expected_ecc: Optional[int] = None,
        expected_crc: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process read data and check for errors

        Args:
            channel: Channel number
            bank: Bank number
            address: Memory address
            data: Read data
            ecc: ECC bits from read
            crc: CRC from read
            expected_ecc: Expected ECC (for verification)
            expected_crc: Expected CRC (for verification)

        Returns:
            Dictionary with:
            - valid: bool - data is valid
            - corrected: bool - error was corrected
            - error_type: str or None
            - corrected_data: int (may be corrected)
            - recovery_action: ErrorRecoveryLevel
        """
        result = {
            'valid': True,
            'corrected': False,
            'error_type': None,
            'corrected_data': data,
            'recovery_action': ErrorRecoveryLevel.NONE,
            'channel': channel,
            'bank': bank,
            'address': address,
        }

        # Check ECC if provided
        if ecc is not None and expected_ecc is not None:
            ecc_result = self._check_ecc(data, ecc, expected_ecc)
            if ecc_result['error']:
                result['valid'] = False
                result['error_type'] = ecc_result['error_type']
                result['corrected'] = ecc_result['corrected']

                if ecc_result['corrected']:
                    result['corrected_data'] = ecc_result['corrected_data']
                    result['recovery_action'] = ErrorRecoveryLevel.CORRECTED
                else:
                    result['recovery_action'] = ErrorRecoveryLevel.RETRY

                self._record_error(
                    channel=channel, bank=bank, address=address,
                    error_type=ecc_result['error_type'],
                    corrected=ecc_result['corrected'],
                    data_bit_errors=ecc_result.get('bit_errors', 0),
                )

        # Check CRC if provided
        if crc is not None and expected_crc is not None:
            if not self._check_crc(data, crc, expected_crc):
                result['valid'] = False
                if result['error_type'] is None:
                    result['error_type'] = 'crc_error'
                result['recovery_action'] = ErrorRecoveryLevel.RETRY

                self._record_error(
                    channel=channel, bank=bank, address=address,
                    error_type='crc_error',
                    corrected=False,
                )

        # Invoke callback
        if not result['valid'] and self._on_error_detected:
            self._on_error_detected(result)

        return result

    def _check_ecc(
        self,
        data: int,
        ecc: int,
        expected_ecc: int,
    ) -> Dict[str, Any]:
        """Check ECC and correct if possible

        Args:
            data: Data with embedded ECC
            ecc: ECC bits
            expected_ecc: Expected ECC bits

        Returns:
            Dictionary with error information
        """
        syndrome = ecc ^ expected_ecc

        if syndrome == 0:
            return {'error': False, 'error_type': None, 'corrected': False}

        # Analyze syndrome
        popcount = bin(syndrome).count('1')

        if popcount == 1:
            # Single-bit error - correctable
            bit_pos = syndrome.bit_length() - 1
            if bit_pos < 64:  # Data bit error
                corrected_data = data ^ (1 << bit_pos)
                return {
                    'error': True,
                    'error_type': 'single_bit_error',
                    'corrected': True,
                    'corrected_data': corrected_data,
                    'bit_errors': 1,
                }
            else:
                # ECC bit error (no data correction needed)
                return {
                    'error': True,
                    'error_type': 'ecc_bit_error',
                    'corrected': True,
                    'corrected_data': data,
                    'bit_errors': 0,
                }

        # Multi-bit error - not correctable
        return {
            'error': True,
            'error_type': f'multi_bit_error_{popcount}_bits',
            'corrected': False,
            'corrected_data': data,
            'bit_errors': popcount,
        }

    def _check_crc(self, data: int, crc: int, expected_crc: int) -> bool:
        """Check CRC"""
        return crc == expected_crc

    def _record_error(
        self,
        channel: int,
        bank: int,
        address: int,
        error_type: str,
        corrected: bool,
        data_bit_errors: int = 0,
        lane_id: Optional[int] = None,
        details: str = "",
    ) -> ErrorRecord:
        """Record an error event

        Args:
            channel: Channel number
            bank: Bank number
            address: Memory address
            error_type: Type of error
            corrected: Whether error was corrected
            data_bit_errors: Number of bit errors
            lane_id: Lane ID if applicable
            details: Additional details

        Returns:
            ErrorRecord
        """
        self._error_id_counter += 1
        self._stats.total_errors += 1

        # Determine error category
        if corrected:
            category = ErrorCategory.CORRECTABLE
        elif 'multi_bit' in error_type:
            category = ErrorCategory.PERMANENT
        else:
            category = ErrorCategory.TRANSIENT

        # Determine recovery level
        recovery_level = self._determine_recovery_level(error_type, corrected)

        record = ErrorRecord(
            error_id=self._error_id_counter,
            timestamp_ns=self._current_time_ns,
            cycle=self._current_cycle,
            channel=channel,
            bank=bank,
            address=address,
            error_type=error_type,
            error_category=category,
            recovery_level=recovery_level,
            data_bit_errors=data_bit_errors,
            corrected=corrected,
            lane_id=lane_id,
            details=details,
        )

        self._error_history.append(record)

        # Update statistics
        if corrected:
            self._stats.corrected_errors += 1

        # Update channel retry state
        ch_state = self._retry_state.get(channel, {})
        ch_state['consecutive_errors'] = ch_state.get('consecutive_errors', 0) + 1
        ch_state['last_error_ns'] = self._current_time_ns

        # Track error rate
        self._error_rate_window.append(self._current_time_ns)

        # Hot block detection (4KB granularity)
        block_addr = address & ~0xFFF
        self._hot_blocks[block_addr] = self._hot_blocks.get(block_addr, 0) + 1

        return record

    def _determine_recovery_level(
        self,
        error_type: str,
        corrected: bool,
    ) -> ErrorRecoveryLevel:
        """Determine recovery level for an error"""
        if corrected:
            return ErrorRecoveryLevel.CORRECTED

        if 'single_bit' in error_type:
            return ErrorRecoveryLevel.RETRY
        elif 'multi_bit' in error_type:
            if 'permanent' in error_type:
                return ErrorRecoveryLevel.LANE_REPAIR
            return ErrorRecoveryLevel.RETRY
        elif 'crc' in error_type:
            return ErrorRecoveryLevel.RETRY
        elif 'parity' in error_type:
            return ErrorRecoveryLevel.LANE_REPAIR

        return ErrorRecoveryLevel.RETRY

    # ==================== Error Handling ====================

    def handle_error(
        self,
        channel: int,
        error_type: str,
        retry_allowed: bool = True,
    ) -> Tuple[ErrorRecoveryLevel, Optional[str]]:
        """Handle an error and determine recovery action

        Args:
            channel: Channel with error
            error_type: Type of error
            retry_allowed: Whether retry is permitted

        Returns:
            Tuple of (recovery_level, message)
        """
        # Get channel retry state
        ch_state = self._retry_state[channel]

        # Check retry count
        if retry_allowed:
            retry_count = ch_state['retry_count']
            if retry_count < self._retry_config.max_retries:
                # Initiate retry
                delay = self._calculate_retry_delay(retry_count)
                ch_state['retry_count'] += 1
                self._stats.retried_errors += 1

                if self._on_recovery_action:
                    self._on_recovery_action(
                        channel=channel,
                        action='retry',
                        retry_count=retry_count + 1,
                        delay_ns=delay,
                    )

                return ErrorRecoveryLevel.RETRY, f"Retry {retry_count + 1}/{self._retry_config.max_retries}"

        # Retry exhausted or not allowed
        if self.enable_lane_repair:
            # Try lane repair for permanent errors
            if 'multi_bit' in error_type or 'parity' in error_type:
                success = self._trigger_lane_repair(channel, error_type)
                if success:
                    self._stats.lane_repairs += 1
                    return ErrorRecoveryLevel.LANE_REPAIR, "Lane repair triggered"

        # Escalate
        ch_errors = ch_state['consecutive_errors']
        if ch_errors >= 10:
            self._stats.channel_disables += 1
            if self._on_critical_error:
                self._on_critical_error(channel, 'channel_disable')
            return ErrorRecoveryLevel.CHANNEL_DISABLE, f"Channel {channel} disabled after {ch_errors} errors"

        # Return to retry state for next attempt
        return ErrorRecoveryLevel.RETRY, "Retry required"

    def _calculate_retry_delay(self, retry_count: int) -> int:
        """Calculate retry delay based on policy"""
        policy = self._retry_config.policy

        if policy == RetryPolicy.IMMEDIATE:
            return self._retry_config.initial_delay_ns

        elif policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            delay = int(self._retry_config.initial_delay_ns * (
                self._retry_config.backoff_factor ** retry_count
            ))
            return min(delay, self._retry_config.max_delay_ns)

        elif policy == RetryPolicy.ADAPTIVE:
            # Adaptive based on recent error rate
            error_rate = self._calculate_error_rate()
            base_delay = self._retry_config.initial_delay_ns
            if error_rate > 0.1:  # >10% error rate
                delay = int(base_delay * (2 ** retry_count))
            else:
                delay = int(base_delay * (1.5 ** retry_count))
            return min(delay, self._retry_config.max_delay_ns)

        return self._retry_config.initial_delay_ns

    def _calculate_error_rate(self) -> float:
        """Calculate recent error rate"""
        if len(self._error_rate_window) < 2:
            return 0.0

        window = list(self._error_rate_window)
        if window[-1] - window[0] == 0:
            return 1.0

        return len(window) / (window[-1] - window[0] + 1) * 1e6  # Errors per us

    def _trigger_lane_repair(
        self,
        channel: int,
        error_type: str,
        lane_id: Optional[int] = None,
    ) -> bool:
        """Trigger lane repair for a channel

        Args:
            channel: Channel to repair
            error_type: Error type that triggered repair
            lane_id: Specific lane to repair (if known)

        Returns:
            True if repair was triggered
        """
        if not self.enable_lane_repair or self._lane_repair is None:
            return False

        # If lane_id not provided, try to find from recent errors
        if lane_id is None:
            recent = self.get_recent_errors(channel, count=10)
            for err in reversed(recent):
                if err.lane_id is not None:
                    lane_id = err.lane_id
                    break

        if lane_id is None:
            return False

        # Perform lane repair
        spare_lane = self._lane_repair.perform_repair(channel, lane_id)
        return spare_lane is not None

    def clear_retry_state(self, channel: int) -> None:
        """Clear retry state for a channel (on successful operation)

        Args:
            channel: Channel to clear
        """
        ch_state = self._retry_state[channel]
        ch_state['retry_count'] = 0
        ch_state['consecutive_errors'] = 0

    def acknowledge_retry_success(self, channel: int) -> None:
        """Acknowledge successful retry

        Args:
            channel: Channel with successful retry
        """
        self._stats.retry_successes += 1
        self.clear_retry_state(channel)

    def acknowledge_retry_failure(self, channel: int) -> None:
        """Acknowledge failed retry

        Args:
            channel: Channel with failed retry
        """
        self._stats.retry_failures += 1

    # ==================== Error Injection ====================

    def inject_error(
        self,
        channel: int,
        address: int,
        error_type: str = "single_bit_error",
        bit_position: int = 0,
    ) -> int:
        """Inject an error for testing

        Args:
            channel: Channel to inject error into
            address: Address for error injection
            error_type: Type of error to inject
            bit_position: Bit position to corrupt

        Returns:
            Error ID
        """
        if not self._error_injection_enabled:
            return -1

        error_id = self._error_id_counter + 1
        key = (channel, address)
        self._injected_errors[key] = {
            'error_id': error_id,
            'error_type': error_type,
            'bit_position': bit_position,
            'injected_at': self._current_time_ns,
        }

        return error_id

    def clear_injected_errors(self, channel: Optional[int] = None) -> None:
        """Clear injected errors

        Args:
            channel: Specific channel to clear, or None for all
        """
        if channel is None:
            self._injected_errors.clear()
        else:
            keys_to_remove = [k for k in self._injected_errors if k[0] == channel]
            for key in keys_to_remove:
                del self._injected_errors[key]

    def is_error_injected(self, channel: int, address: int) -> bool:
        """Check if error is injected at location

        Args:
            channel: Channel to check
            address: Address to check

        Returns:
            True if error is injected
        """
        return (channel, address) in self._injected_errors

    def enable_error_injection(self, enable: bool) -> None:
        """Enable or disable error injection

        Args:
            enable: True to enable, False to disable
        """
        self._error_injection_enabled = enable

    # ==================== Integration ====================

    def set_lane_repair(self, lane_repair) -> None:
        """Set lane repair module for integration

        Args:
            lane_repair: HBM4LaneRepairModel instance
        """
        self._lane_repair = lane_repair

    # ==================== Query ====================

    def get_recent_errors(
        self,
        channel: Optional[int] = None,
        count: int = 10,
    ) -> List[ErrorRecord]:
        """Get recent error records

        Args:
            channel: Filter by channel (None for all)
            count: Number of records to return

        Returns:
            List of ErrorRecord
        """
        errors = list(self._error_history)

        if channel is not None:
            errors = [e for e in errors if e.channel == channel]

        return errors[-count:]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics

        Returns:
            Dictionary with error summary
        """
        recent = list(self._error_history)

        # Count by type
        by_type: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        by_recovery: Dict[str, int] = {}

        for err in recent:
            by_type[err.error_type] = by_type.get(err.error_type, 0) + 1
            by_category[err.error_category.value] = by_category.get(
                err.error_category.value, 0
            ) + 1
            by_recovery[err.recovery_level.value] = by_recovery.get(
                err.recovery_level.value, 0
            ) + 1

        # Per-channel error counts
        channel_errors: Dict[int, int] = {}
        for err in recent:
            channel_errors[err.channel] = channel_errors.get(err.channel, 0) + 1

        return {
            'total_errors': self._stats.total_errors,
            'recent_error_count': len(recent),
            'errors_by_type': by_type,
            'errors_by_category': by_category,
            'errors_by_recovery': by_recovery,
            'channel_error_counts': channel_errors,
            'current_error_rate': self._calculate_error_rate(),
            'retry_stats': self._stats.to_dict(),
        }

    def get_channel_health(self, channel: int) -> Dict[str, Any]:
        """Get health metrics for a channel

        Args:
            channel: Channel to query

        Returns:
            Dictionary with health metrics
        """
        ch_errors = [e for e in self._error_history if e.channel == channel]
        ch_state = self._retry_state[channel]

        # Calculate error rate for channel
        error_rate = len(ch_errors) / max(1, self._current_time_ns / 1e6)  # Errors per us

        # Determine health status
        consecutive = ch_state.get('consecutive_errors', 0)
        if consecutive == 0:
            health = 'healthy'
        elif consecutive < 3:
            health = 'degraded'
        elif consecutive < 10:
            health = 'warning'
        else:
            health = 'critical'

        return {
            'channel': channel,
            'total_errors': len(ch_errors),
            'consecutive_errors': consecutive,
            'error_rate_per_us': error_rate,
            'retry_count': ch_state.get('retry_count', 0),
            'health_status': health,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'recovery_stats': self._stats.to_dict(),
            'error_summary': self.get_error_summary(),
            'retry_config': {
                'max_retries': self._retry_config.max_retries,
                'policy': self._retry_config.policy.value,
                'initial_delay_ns': self._retry_config.initial_delay_ns,
                'max_delay_ns': self._retry_config.max_delay_ns,
            },
            'simulation': {
                'current_cycle': self._current_cycle,
                'current_time_ns': self._current_time_ns,
            },
        }

    # ==================== Hot Block Detection ====================

    def is_hot_block(self, address: int, threshold: Optional[int] = None) -> bool:
        """Check if address belongs to a hot block

        A hot block is a 4KB memory region with many errors,
        indicating potential hardware issues.

        Args:
            address: Memory address to check
            threshold: Custom threshold (uses default if None)

        Returns:
            True if block is hot (exceeds threshold)
        """
        threshold = threshold if threshold is not None else self._hot_block_threshold
        block_addr = address & ~0xFFF
        return self._hot_blocks.get(block_addr, 0) >= threshold

    def get_hot_blocks(self, threshold: Optional[int] = None) -> Dict[int, int]:
        """Get all hot blocks above threshold

        Args:
            threshold: Minimum error count for inclusion

        Returns:
            Dict mapping block addresses to error counts
        """
        threshold = threshold if threshold is not None else self._hot_block_threshold
        return {
            addr: count
            for addr, count in self._hot_blocks.items()
            if count >= threshold
        }

    def get_block_error_count(self, address: int) -> int:
        """Get error count for a specific block

        Args:
            address: Memory address in the block

        Returns:
            Number of errors in this block
        """
        block_addr = address & ~0xFFF
        return self._hot_blocks.get(block_addr, 0)

    def set_hot_block_threshold(self, threshold: int) -> None:
        """Set hot block detection threshold

        Args:
            threshold: Error count to qualify as hot block
        """
        self._hot_block_threshold = max(1, threshold)

    # ==================== Simulation ====================

    def advance_cycle(self, cycles: int = 1) -> None:
        """Advance simulation

        Args:
            cycles: Number of cycles to advance
        """
        self._current_cycle += cycles
        self._current_time_ns += cycles * 1000  # Assume 1GHz for now

    def set_cycle(self, cycle: int) -> None:
        """Set simulation cycle

        Args:
            cycle: Cycle number
        """
        self._current_cycle = cycle

    def reset(self) -> None:
        """Reset error recovery state"""
        self._error_history.clear()
        self._error_id_counter = 0
        self._stats = RecoveryStats()
        self._error_rate_window.clear()
        self._hot_blocks.clear()
        self._current_cycle = 0
        self._current_time_ns = 0

        for ch_state in self._retry_state.values():
            ch_state['retry_count'] = 0
            ch_state['consecutive_errors'] = 0
            ch_state['last_error_ns'] = 0

    # ==================== Callbacks ====================

    def register_error_callback(
        self,
        callback: Callable[[Dict], None],
    ) -> None:
        """Register callback for error detection events

        Args:
            callback: Function to call on error detection
        """
        self._on_error_detected = callback

    def register_recovery_callback(
        self,
        callback: Callable[[Dict], None],
    ) -> None:
        """Register callback for recovery action events

        Args:
            callback: Function to call on recovery action
        """
        self._on_recovery_action = callback

    def register_critical_error_callback(
        self,
        callback: Callable[[int, str], None],
    ) -> None:
        """Register callback for critical error events

        Args:
            callback: Function to call on critical error
        """
        self._on_critical_error = callback
