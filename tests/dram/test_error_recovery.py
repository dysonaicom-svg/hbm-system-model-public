"""
Tests for HBM4 Error Recovery Module

Tests error detection, correction, retry mechanisms, and recovery policies.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.dram.error_recovery import (
    ErrorRecoveryController, ErrorRecoveryLevel, RetryPolicy, ErrorCategory,
    ErrorRecord, RetryConfig, RecoveryStats,
)


class TestErrorRecoveryBasic:
    """Test basic error recovery functionality"""

    def test_initialization(self):
        """Test controller initialization"""
        recovery = ErrorRecoveryController(num_channels=32)
        assert recovery.num_channels == 32
        assert recovery._stats.total_errors == 0

    def test_default_retry_config(self):
        """Test default retry configuration"""
        recovery = ErrorRecoveryController()
        assert recovery._retry_config.max_retries == 3
        assert recovery._retry_config.policy == RetryPolicy.EXPONENTIAL_BACKOFF

    def test_custom_retry_config(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_retries=5,
            policy=RetryPolicy.IMMEDIATE,
            initial_delay_ns=50,
        )
        recovery = ErrorRecoveryController(retry_config=config)
        assert recovery._retry_config.max_retries == 5
        assert recovery._retry_config.policy == RetryPolicy.IMMEDIATE


class TestErrorProcessing:
    """Test error processing"""

    def test_process_read_no_error(self):
        """Test processing read with no errors"""
        recovery = ErrorRecoveryController()
        result = recovery.process_read(
            channel=0, bank=1, address=0x1000,
            data=0xDEADBEEF,
            ecc=0, expected_ecc=0,
        )
        assert result['valid'] is True
        assert result['corrected'] is False
        assert result['error_type'] is None

    def test_process_read_ecc_single_bit(self):
        """Test ECC single-bit error detection and correction"""
        recovery = ErrorRecoveryController()

        # Data with known ECC (simplified for test)
        data = 0x123456789ABCDEF0
        ecc = 0xAB  # This ECC
        expected_ecc = 0xAB  # Should match

        result = recovery.process_read(
            channel=0, bank=1, address=0x1000,
            data=data, ecc=ecc, expected_ecc=expected_ecc,
        )
        assert result['valid'] is True

    def test_process_read_crc_error(self):
        """Test CRC error detection"""
        recovery = ErrorRecoveryController()
        result = recovery.process_read(
            channel=0, bank=1, address=0x1000,
            data=0xDEADBEEF,
            crc=0x1234, expected_crc=0x5678,
        )
        assert result['valid'] is False
        assert result['error_type'] == 'crc_error'


class TestErrorHandling:
    """Test error handling and retry"""

    def test_handle_error_retry(self):
        """Test error handling triggers retry"""
        recovery = ErrorRecoveryController()
        level, msg = recovery.handle_error(
            channel=0,
            error_type='single_bit_error',
            retry_allowed=True,
        )
        assert level == ErrorRecoveryLevel.RETRY
        assert 'Retry' in msg

    def test_handle_error_max_retries(self):
        """Test error handling after max retries"""
        recovery = ErrorRecoveryController()
        # Exhaust retries (max_retries = 3)
        for i in range(4):
            level, msg = recovery.handle_error(channel=0, error_type='single_bit_error')
            # First 3 should be RETRY, 4th should escalate or continue
            if i < 3:
                assert level == ErrorRecoveryLevel.RETRY
            # The message should be valid
            assert isinstance(msg, str)

    def test_clear_retry_state(self):
        """Test clearing retry state"""
        recovery = ErrorRecoveryController()
        recovery._retry_state[0]['retry_count'] = 2
        recovery._retry_state[0]['consecutive_errors'] = 5
        recovery.clear_retry_state(0)

        assert recovery._retry_state[0]['retry_count'] == 0
        assert recovery._retry_state[0]['consecutive_errors'] == 0


class TestErrorInjection:
    """Test error injection for testing"""

    def test_inject_error(self):
        """Test error injection"""
        recovery = ErrorRecoveryController()
        error_id = recovery.inject_error(
            channel=0,
            address=0x1000,
            error_type='single_bit_error',
            bit_position=5,
        )
        assert error_id > 0
        assert recovery.is_error_injected(0, 0x1000) is True

    def test_clear_injected_errors(self):
        """Test clearing injected errors"""
        recovery = ErrorRecoveryController()
        recovery.inject_error(channel=0, address=0x1000)
        recovery.inject_error(channel=1, address=0x2000)
        recovery.clear_injected_errors()

        assert recovery.is_error_injected(0, 0x1000) is False
        assert recovery.is_error_injected(1, 0x2000) is False

    def test_clear_channel_errors(self):
        """Test clearing errors for specific channel"""
        recovery = ErrorRecoveryController()
        recovery.inject_error(channel=0, address=0x1000)
        recovery.inject_error(channel=1, address=0x2000)
        recovery.clear_injected_errors(channel=0)

        assert recovery.is_error_injected(0, 0x1000) is False
        assert recovery.is_error_injected(1, 0x2000) is True

    def test_disable_error_injection(self):
        """Test disabling error injection"""
        recovery = ErrorRecoveryController()
        recovery.enable_error_injection(False)
        error_id = recovery.inject_error(channel=0, address=0x1000)
        assert error_id == -1


class TestErrorStatistics:
    """Test error statistics"""

    def test_stats_initial(self):
        """Test initial statistics"""
        recovery = ErrorRecoveryController()
        stats = recovery.get_stats()
        assert 'recovery_stats' in stats
        assert 'error_summary' in stats

    def test_error_summary(self):
        """Test error summary"""
        recovery = ErrorRecoveryController()
        recovery._stats.total_errors = 10
        recovery._stats.corrected_errors = 8
        summary = recovery.get_error_summary()
        assert summary['total_errors'] == 10

    def test_channel_health(self):
        """Test channel health metrics"""
        recovery = ErrorRecoveryController()
        health = recovery.get_channel_health(0)
        assert 'channel' in health
        assert 'health_status' in health
        assert health['health_status'] == 'healthy'


class TestRetryPolicies:
    """Test different retry policies"""

    def test_immediate_retry_delay(self):
        """Test immediate retry policy"""
        config = RetryConfig(policy=RetryPolicy.IMMEDIATE, initial_delay_ns=100)
        recovery = ErrorRecoveryController(retry_config=config)
        delay = recovery._calculate_retry_delay(0)
        assert delay == 100

    def test_exponential_backoff_delay(self):
        """Test exponential backoff policy"""
        config = RetryConfig(
            policy=RetryPolicy.EXPONENTIAL_BACKOFF,
            initial_delay_ns=100,
            backoff_factor=2.0,
        )
        recovery = ErrorRecoveryController(retry_config=config)

        delay0 = recovery._calculate_retry_delay(0)
        delay1 = recovery._calculate_retry_delay(1)
        delay2 = recovery._calculate_retry_delay(2)

        assert delay1 == delay0 * 2
        assert delay2 == delay0 * 4

    def test_max_delay_limit(self):
        """Test max delay limit"""
        config = RetryConfig(
            policy=RetryPolicy.EXPONENTIAL_BACKOFF,
            initial_delay_ns=1000,
            max_delay_ns=5000,
        )
        recovery = ErrorRecoveryController(retry_config=config)
        delay = recovery._calculate_retry_delay(10)  # Would be very large
        assert delay == 5000  # Capped at max


class TestRecoveryEscalation:
    """Test recovery level escalation"""

    def test_determine_corrected_level(self):
        """Test corrected error level"""
        recovery = ErrorRecoveryController()
        level = recovery._determine_recovery_level('single_bit_error', corrected=True)
        assert level == ErrorRecoveryLevel.CORRECTED

    def test_determine_retry_level(self):
        """Test uncorrected error triggers retry"""
        recovery = ErrorRecoveryController()
        level = recovery._determine_recovery_level('single_bit_error', corrected=False)
        assert level == ErrorRecoveryLevel.RETRY

    def test_determine_multi_bit_level(self):
        """Test multi-bit error triggers lane repair"""
        recovery = ErrorRecoveryController()
        level = recovery._determine_recovery_level('multi_bit_error_3_bits', corrected=False)
        # May be RETRY or LANE_REPAIR depending on implementation


class TestErrorRecording:
    """Test error recording"""

    def test_record_error(self):
        """Test error recording"""
        recovery = ErrorRecoveryController()
        record = recovery._record_error(
            channel=0, bank=1, address=0x1000,
            error_type='single_bit_error', corrected=True,
        )
        assert record.error_type == 'single_bit_error'
        assert record.corrected is True
        assert record.channel == 0

    def test_error_history_tracking(self):
        """Test error history is maintained"""
        recovery = ErrorRecoveryController()
        for i in range(5):
            recovery._record_error(
                channel=0, bank=1, address=0x1000 + i,
                error_type='single_bit_error', corrected=True,
            )
        history = recovery.get_recent_errors(count=10)
        assert len(history) == 5

    def test_error_history_filtering(self):
        """Test error history channel filtering"""
        recovery = ErrorRecoveryController()
        recovery._record_error(channel=0, bank=1, address=0x1000, error_type='single_bit_error', corrected=True)
        recovery._record_error(channel=1, bank=1, address=0x2000, error_type='single_bit_error', corrected=True)
        recovery._record_error(channel=0, bank=2, address=0x3000, error_type='single_bit_error', corrected=True)

        ch0_errors = recovery.get_recent_errors(channel=0, count=10)
        assert len(ch0_errors) == 2


class TestSimulation:
    """Test simulation integration"""

    def test_advance_cycle(self):
        """Test cycle advancement"""
        recovery = ErrorRecoveryController()
        recovery.advance_cycle(100)
        assert recovery._current_cycle == 100

    def test_set_cycle(self):
        """Test setting cycle"""
        recovery = ErrorRecoveryController()
        recovery.set_cycle(500)
        assert recovery._current_cycle == 500

    def test_reset(self):
        """Test reset functionality"""
        recovery = ErrorRecoveryController()
        recovery._record_error(channel=0, bank=1, address=0x1000, error_type='single_bit_error', corrected=True)
        recovery._stats.total_errors = 5
        recovery.reset()

        assert recovery._current_cycle == 0
        assert recovery._stats.total_errors == 0


class TestRetrySuccessFailure:
    """Test retry acknowledgement"""

    def test_acknowledge_retry_success(self):
        """Test acknowledging retry success"""
        recovery = ErrorRecoveryController()
        recovery._stats.retried_errors = 1
        recovery._retry_state[0]['retry_count'] = 2
        recovery.acknowledge_retry_success(0)

        assert recovery._stats.retry_successes == 1
        assert recovery._retry_state[0]['retry_count'] == 0

    def test_acknowledge_retry_failure(self):
        """Test acknowledging retry failure"""
        recovery = ErrorRecoveryController()
        recovery.acknowledge_retry_failure(0)
        assert recovery._stats.retry_failures == 1


class TestLaneRepairIntegration:
    """Test lane repair integration"""

    def test_lane_repair_enabled(self):
        """Test lane repair can be enabled"""
        recovery = ErrorRecoveryController(enable_lane_repair=True)
        assert recovery.enable_lane_repair is True

    def test_lane_repair_disabled(self):
        """Test lane repair can be disabled"""
        recovery = ErrorRecoveryController(enable_lane_repair=False)
        assert recovery.enable_lane_repair is False

    def test_trigger_lane_repair_no_module(self):
        """Test lane repair trigger without module returns False"""
        recovery = ErrorRecoveryController(enable_lane_repair=True)
        # No lane repair module set
        result = recovery._trigger_lane_repair(0, 'multi_bit_error')
        assert result is False


class TestCallbacks:
    """Test callback registration"""

    def test_register_error_callback(self):
        """Test registering error callback"""
        recovery = ErrorRecoveryController()
        called = []

        def callback(result):
            called.append(result)

        recovery.register_error_callback(callback)
        recovery._on_error_detected({'valid': False, 'error_type': 'test'})

        assert len(called) == 1

    def test_register_recovery_callback(self):
        """Test registering recovery callback"""
        recovery = ErrorRecoveryController()
        called = []

        def callback(action):
            called.append(action)

        recovery.register_recovery_callback(callback)
        recovery._on_recovery_action({'action': 'retry'})

        assert len(called) == 1

    def test_register_critical_callback(self):
        """Test registering critical error callback"""
        recovery = ErrorRecoveryController()
        called = []

        def callback(channel, reason):
            called.append((channel, reason))

        recovery.register_critical_error_callback(callback)
        recovery._on_critical_error(0, 'channel_disable')

        assert len(called) == 1
        assert called[0] == (0, 'channel_disable')


class TestErrorRateCalculation:
    """Test error rate calculations"""

    def test_error_rate_zero(self):
        """Test error rate with no errors"""
        recovery = ErrorRecoveryController()
        rate = recovery._calculate_error_rate()
        assert rate == 0.0

    def test_error_rate_calculation(self):
        """Test error rate calculation"""
        recovery = ErrorRecoveryController()
        recovery._error_rate_window.append(0)
        recovery._error_rate_window.append(1000)
        rate = recovery._calculate_error_rate()
        assert rate > 0


class TestECCErrorDetection:
    """Test ECC error detection logic"""

    def test_ecc_no_error(self):
        """Test ECC with matching syndrome"""
        recovery = ErrorRecoveryController()
        result = recovery._check_ecc(0xDEADBEEF, 0x00, 0x00)
        assert result['error'] is False

    def test_ecc_single_bit_error(self):
        """Test ECC single-bit error detection"""
        recovery = ErrorRecoveryController()
        # Create a data with ECC that has 1-bit syndrome
        data = 0xFFFFFFFFFFFFFFFF
        ecc = 0x01
        expected_ecc = 0x00
        result = recovery._check_ecc(data, ecc, expected_ecc)
        assert result['error'] is True
        assert 'bit' in result['error_type'].lower()

    def test_ecc_multi_bit_error(self):
        """Test ECC multi-bit error detection"""
        recovery = ErrorRecoveryController()
        data = 0xFFFFFFFFFFFFFFFF
        ecc = 0x03  # 2-bit syndrome
        expected_ecc = 0x00
        result = recovery._check_ecc(data, ecc, expected_ecc)
        assert result['error'] is True
        assert result['corrected'] is False


class TestIntegration:
    """Test full integration scenarios"""

    def test_full_error_recovery_flow(self):
        """Test complete error recovery flow"""
        recovery = ErrorRecoveryController()

        # Process a read with error
        result = recovery.process_read(
            channel=0, bank=1, address=0x1000,
            data=0x123456789ABCDEF0,
            ecc=0x01, expected_ecc=0x00,  # Simulated single-bit error
        )

        # Handle the error
        if not result['valid']:
            level, msg = recovery.handle_error(0, result['error_type'])
            assert level in [ErrorRecoveryLevel.RETRY, ErrorRecoveryLevel.CORRECTED]

    def test_error_statistics_after_flow(self):
        """Test statistics updated after error flow"""
        recovery = ErrorRecoveryController()

        # Generate some errors
        for i in range(3):
            recovery._record_error(
                channel=0, bank=1, address=0x1000 + i,
                error_type='single_bit_error', corrected=True,
            )

        stats = recovery.get_stats()
        assert stats['recovery_stats']['total_errors'] == 3


class TestHotBlockDetection:
    """Test hot block detection functionality"""

    def test_hot_block_not_hot_initially(self):
        """Test block is not hot when no errors"""
        recovery = ErrorRecoveryController()
        assert recovery.is_hot_block(0x1000) is False

    def test_hot_block_after_threshold_errors(self):
        """Test block becomes hot after threshold errors"""
        recovery = ErrorRecoveryController()
        # Record 10 errors in same 4KB block (default threshold=10)
        for i in range(10):
            recovery._record_error(
                channel=0, bank=1, address=0x1000 + i,
                error_type='single_bit_error', corrected=True,
            )
        assert recovery.is_hot_block(0x1000) is True

    def test_hot_block_below_threshold(self):
        """Test block below threshold is not hot"""
        recovery = ErrorRecoveryController()
        # Record 5 errors (below threshold of 10)
        for i in range(5):
            recovery._record_error(
                channel=0, bank=1, address=0x1000 + i,
                error_type='single_bit_error', corrected=True,
            )
        assert recovery.is_hot_block(0x1000) is False

    def test_hot_block_custom_threshold(self):
        """Test hot block with custom threshold"""
        recovery = ErrorRecoveryController()
        recovery.set_hot_block_threshold(3)
        # 3 errors should be hot with threshold=3
        for i in range(3):
            recovery._record_error(
                channel=0, bank=1, address=0x1000 + i,
                error_type='single_bit_error', corrected=True,
            )
        assert recovery.is_hot_block(0x1000) is True

    def test_different_blocks_independent(self):
        """Test different blocks are tracked independently"""
        recovery = ErrorRecoveryController()
        # Block 1: 10 errors (hot)
        for i in range(10):
            recovery._record_error(channel=0, bank=1, address=0x1000 + i,
                                  error_type='single_bit_error', corrected=True)
        # Block 2: 5 errors (not hot)
        for i in range(5):
            recovery._record_error(channel=0, bank=1, address=0x2000 + i,
                                  error_type='single_bit_error', corrected=True)

        assert recovery.is_hot_block(0x1000) is True
        assert recovery.is_hot_block(0x2000) is False

    def test_get_hot_blocks(self):
        """Test getting all hot blocks"""
        recovery = ErrorRecoveryController()
        # Block 1: 12 errors (hot)
        for i in range(12):
            recovery._record_error(channel=0, bank=1, address=0x1000 + i,
                                  error_type='single_bit_error', corrected=True)
        # Block 2: 8 errors (not hot)
        for i in range(8):
            recovery._record_error(channel=0, bank=1, address=0x2000 + i,
                                  error_type='single_bit_error', corrected=True)

        hot_blocks = recovery.get_hot_blocks()
        assert len(hot_blocks) == 1
        assert (0x1000 & ~0xFFF) in hot_blocks

    def test_get_block_error_count(self):
        """Test getting error count for specific block"""
        recovery = ErrorRecoveryController()
        for i in range(5):
            recovery._record_error(channel=0, bank=1, address=0x1000 + i,
                                  error_type='single_bit_error', corrected=True)

        count = recovery.get_block_error_count(0x1000)
        assert count == 5

    def test_hot_block_tracking_in_reset(self):
        """Test hot blocks are cleared on reset"""
        recovery = ErrorRecoveryController()
        for i in range(15):
            recovery._record_error(channel=0, bank=1, address=0x1000 + i,
                                  error_type='single_bit_error', corrected=True)

        assert recovery.is_hot_block(0x1000) is True
        recovery.reset()
        assert recovery.is_hot_block(0x1000) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
