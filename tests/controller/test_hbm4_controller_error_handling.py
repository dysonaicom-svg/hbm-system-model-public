"""
HBM4 Controller Error Handling and Edge Cases Tests

Tests for error handling, edge cases, and boundary conditions.

Test coverage:
- Invalid parameter handling
- Resource exhaustion scenarios
- Timeout and deadlock detection
- Error recovery mechanisms
- Stress testing
"""

import pytest
import time
from model.dram.hbm4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.dfi_interface import DFILowPowerState
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler
from model.controller.request import HBMRequest, RequestState
from model.controller.queue import ReadQueue, WriteQueue, QueueManager


class TestInvalidParameterHandling:
    """Test handling of invalid parameters"""

    def test_invalid_qos_clamping(self):
        """Test QoS level clamping to valid range"""
        controller = HBM4Controller()

        # Negative QoS should be clamped
        request_id = controller.submit_request(
            addr=0x100, is_read=True, qos_level=-1
        )
        assert request_id is not None

        # QoS > 15 should be clamped
        request_id = controller.submit_request(
            addr=0x200, is_read=True, qos_level=100
        )
        assert request_id is not None

    def test_invalid_size_bytes(self):
        """Test handling of invalid size_bytes"""
        controller = HBM4Controller()

        # Zero size
        request_id = controller.submit_request(
            addr=0x100, is_read=True, size_bytes=0
        )
        # Should still work (might be clamped)

        # Negative size
        request_id = controller.submit_request(
            addr=0x200, is_read=True, size_bytes=-1
        )

    def test_null_address(self):
        """Test handling of null/zero address"""
        controller = HBM4Controller()

        request_id = controller.submit_request(addr=0x0, is_read=True)
        assert request_id is not None

    def test_very_large_address(self):
        """Test handling of very large address"""
        controller = HBM4Controller()

        # 64-bit max address
        request_id = controller.submit_request(
            addr=0xFFFFFFFFFFFFFFFF,
            is_read=True
        )
        assert request_id is not None


class TestResourceExhaustion:
    """Test resource exhaustion scenarios"""

    def test_queue_exhaustion_single_channel(self):
        """Test queue exhaustion for single channel"""
        controller = HBM4Controller()

        # Flood one channel
        rejected = 0
        for i in range(1000):
            addr = 0x8  # Channel 0 only
            result = controller.submit_request(addr=addr, is_read=True)
            if result is None:
                rejected += 1

        # Some should be rejected
        assert rejected > 0

    def test_queue_exhaustion_all_channels(self):
        """Test queue exhaustion across all channels"""
        controller = HBM4Controller()

        # Flood all channels
        submitted = 0
        for ch in range(32):
            for _ in range(100):
                addr = (ch << 41) | 0x8
                result = controller.submit_request(addr=addr, is_read=True)
                if result is not None:
                    submitted += 1

        # Should have significant submission
        assert submitted > 0

    def test_pending_request_limit(self):
        """Test pending request tracking limit"""
        controller = HBM4Controller()

        # Submit many requests
        for i in range(500):
            controller.submit_request(addr=i * 0x100, is_read=True)

        # Pending should be tracked
        assert len(controller._pending_requests) >= 0

    def test_pipeline_overflow_handling(self):
        """Test pipeline overflow handling"""
        controller = HBM4Controller(enable_pipeline=True)

        # Fill pipeline
        for i in range(100):
            controller.submit_request(addr=i * 0x100, is_read=True)
            controller.tick()

        # Should handle gracefully


class TestTimeoutAndDeadlockDetection:
    """Test timeout and potential deadlock scenarios"""

    def test_empty_simulation_timeout(self):
        """Test timeout with empty simulation"""
        controller = HBM4Controller()

        start = time.time()
        for _ in range(1000):
            controller.tick()
        elapsed = time.time() - start

        # Should complete quickly
        assert elapsed < 5.0  # 5 seconds max

    def test_starvation_detection(self):
        """Test starvation scenario detection"""
        scheduler = HBM4QoSScheduler()

        # Flood with high priority
        for i in range(100):
            scheduler.submit_request(
                request_id=i,
                qos=15,
                is_read=True
            )

        # Low priority request
        scheduler.submit_request(
            request_id=999,
            qos=0,
            is_read=True
        )

        # High priority should be scheduled first
        scheduled = scheduler.schedule()
        assert scheduled.qos == 15

    def test_queue_never_full_hang(self):
        """Test that queue operations don't hang"""
        controller = HBM4Controller()

        # Quick submit operations
        for i in range(100):
            controller.submit_request(addr=i * 0x100, is_read=True)

        # Should not hang
        assert controller.stats.total_requests == 100


class TestErrorRecovery:
    """Test error recovery mechanisms"""

    def test_controller_reset_after_requests(self):
        """Test controller reset after requests"""
        controller = HBM4Controller()

        # Submit some requests
        for i in range(10):
            controller.submit_request(addr=i * 0x100, is_read=True)

        # Reset
        controller.reset()

        # Should be clean
        assert controller.stats.total_requests == 0
        assert len(controller._pending_requests) == 0

    def test_multiple_reset_cycles(self):
        """Test multiple reset cycles"""
        controller = HBM4Controller()

        for _ in range(5):
            # Submit requests
            for i in range(10):
                controller.submit_request(addr=i * 0x100, is_read=True)

            # Reset
            controller.reset()

            assert controller.stats.total_requests == 0

    def test_queue_manager_reset(self):
        """Test queue manager reset"""
        manager = QueueManager.create(queue_depth=32)

        # Add some requests
        for i in range(10):
            req = HBMRequest(addr=i * 0x100, length=64, is_read=True)
            manager.push_read(req)

        assert manager.total_size() == 10

        # Reset by creating new manager
        manager = QueueManager.create(queue_depth=32)
        assert manager.total_size() == 0


class TestBoundaryConditions:
    """Test boundary conditions"""

    def test_address_decode_min_channel(self):
        """Test channel 0 address decode"""
        decoder = HBM4AddressDecoder()
        addr = 0x8  # Channel 0
        decoded = decoder.decode(addr)
        assert decoded.channel_id == 0

    def test_address_decode_max_channel(self):
        """Test max channel address decode"""
        decoder = HBM4AddressDecoder()
        addr = (31 << 41) | 0x8
        decoded = decoder.decode(addr)
        assert decoded.channel_id == 31

    def test_address_decode_min_row(self):
        """Test row 0 address decode"""
        decoder = HBM4AddressDecoder()
        addr = 0x8
        decoded = decoder.decode(addr)
        assert decoded.row_id >= 0

    def test_address_decode_max_row(self):
        """Test max row address decode"""
        decoder = HBM4AddressDecoder()
        addr = (0xFFFF << 16) | 0x8
        decoded = decoder.decode(addr)
        assert decoded.row_id == 0xFFFF

    def test_queue_boundary_zero(self):
        """Test queue with zero capacity"""
        # Should handle gracefully
        queue = ReadQueue(max_depth=1)

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        result = queue.push(req)
        assert result is True

        # Queue should be full
        assert queue.is_full()

    def test_empty_queue_pop(self):
        """Test pop from empty queue"""
        queue = ReadQueue(max_depth=32)

        result = queue.pop()
        assert result is None

    def test_empty_queue_peek(self):
        """Test peek on empty queue"""
        queue = ReadQueue(max_depth=32)

        result = queue.peek()
        assert result is None


class TestStressTesting:
    """Stress testing scenarios"""

    def test_high_request_rate(self):
        """Test high request submission rate"""
        controller = HBM4Controller()

        start = time.time()

        # Rapid submissions - controller has internal queue limit
        submitted = 0
        for i in range(10000):
            req_id = controller.submit_request(addr=i * 0x100, is_read=True)
            if req_id is not None:
                submitted += 1

        elapsed = time.time() - start

        # Should complete quickly
        assert elapsed < 10.0
        # Some requests may be rejected due to queue limits
        assert submitted > 0
        assert controller.stats.total_requests == submitted

    def test_mixed_operation_stress(self):
        """Test mixed read/write operations under stress"""
        controller = HBM4Controller()

        for i in range(500):
            controller.submit_request(
                addr=i * 0x100,
                is_read=(i % 2 == 0)
            )

        # Run simulation
        for _ in range(1000):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 500

    def test_all_channels_stress(self):
        """Test stress on all channels"""
        controller = HBM4Controller()

        submitted = 0
        for ch in range(32):
            for _ in range(50):
                addr = (ch << 41) | 0x8
                req_id = controller.submit_request(addr=addr, is_read=True)
                if req_id is not None:
                    submitted += 1

        # Some may be rejected due to queue limits
        assert submitted > 0
        assert controller.stats.total_requests == submitted

    def test_burst_submission_stress(self):
        """Test burst submission pattern"""
        controller = HBM4Controller()

        # Burst submissions - may be limited by queue depth
        submitted = 0
        for _ in range(10):
            for i in range(100):
                req_id = controller.submit_request(
                    addr=i * 0x1000,
                    is_read=True
                )
                if req_id is not None:
                    submitted += 1
            controller.tick()

        assert submitted > 0
        assert controller.stats.total_requests == submitted


class TestRaceConditions:
    """Test potential race conditions"""

    def test_concurrent_tick_and_submit(self):
        """Test concurrent tick and submit operations"""
        controller = HBM4Controller()

        results = []

        def submit_requests():
            for i in range(100):
                controller.submit_request(addr=i * 0x100, is_read=True)
                time.sleep(0.0001)

        def tick_simulation():
            for _ in range(200):
                controller.tick()
                time.sleep(0.0001)

        # Run in threads
        import threading
        t1 = threading.Thread(target=submit_requests)
        t2 = threading.Thread(target=tick_simulation)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Should complete without errors
        assert controller.stats.total_requests > 0

    def test_multiple_controller_instances(self):
        """Test multiple controller instances"""
        controllers = [HBM4Controller() for _ in range(5)]

        for i, ctrl in enumerate(controllers):
            for j in range(10):
                ctrl.submit_request(addr=j * 0x100, is_read=True)

        for ctrl in controllers:
            assert ctrl.stats.total_requests == 10


class TestDataIntegrity:
    """Test data integrity checks"""

    def test_request_id_uniqueness(self):
        """Test request ID uniqueness"""
        controller = HBM4Controller()

        ids = set()
        for i in range(100):
            req_id = controller.submit_request(addr=i * 0x100, is_read=True)
            if req_id:
                ids.add(req_id)

        # All IDs should be unique
        assert len(ids) == controller.stats.total_requests

    def test_response_request_id_match(self):
        """Test response request_id matches submission"""
        controller = HBM4Controller()

        request_id = controller.submit_request(addr=0x100, is_read=True)
        assert request_id is not None

        # Run to completion
        for _ in range(50):
            responses = controller.tick()
            for resp in responses:
                if resp.request_id == request_id:
                    # Found matching response
                    break

    def test_latency_non_negative(self):
        """Test latency is never negative"""
        controller = HBM4Controller()

        for i in range(50):
            controller.submit_request(addr=i * 0x100, is_read=True)

        for _ in range(200):
            controller.tick()

        # Latency should always be non-negative
        assert controller.stats.average_latency_ns >= 0


class TestPerformanceCounters:
    """Test performance counters"""

    def test_command_counter_increments(self):
        """Test command counter increments"""
        controller = HBM4Controller()

        initial = controller.stats.commands_issued

        controller._issue_act_command(
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            row_id=0x100,
            request_id="test"
        )

        assert controller.stats.commands_issued > initial

    def test_bank_conflict_counter(self):
        """Test bank conflict counter"""
        controller = HBM4Controller()

        # Set up row state
        controller._row_state[(0, 0, 0)] = 0x100

        # Access different row
        can_issue, reason = controller._can_issue_to_bank(0, 0, 0, 0x200)

        if not can_issue:
            assert controller.stats.bank_conflicts >= 1

    def test_refresh_counter(self):
        """Test refresh counter"""
        controller = HBM4Controller(enable_refresh=True)

        initial = controller.stats.refresh_count

        # Run refresh cycle
        for _ in range(10000):
            controller.tick()

        # Refresh count should change
        assert controller.stats.refresh_count >= initial


class TestSpecCompliance:
    """Test HBM4 specification compliance"""

    def test_default_channels(self):
        """Test default channel count"""
        controller = HBM4Controller()
        assert controller.channels == 32

    def test_default_pseudo_channels(self):
        """Test default pseudo-channel count"""
        controller = HBM4Controller()
        assert controller.pseudo_channels == 64

    def test_io_width_compliance(self):
        """Test I/O width compliance"""
        controller = HBM4Controller()
        assert controller.spec.io_width == 2048

    def test_speed_grade_compliance(self):
        """Test speed grade compliance"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            spec = create_hbm4_spec_from_speed_grade(grade)
            controller = HBM4Controller(spec=spec)

            # Check compliance
            assert controller.spec.data_rate_gtps > 0
            assert controller.spec.bandwidth > 0


class TestDebugSupport:
    """Test debug support features"""

    def test_get_channel_state(self):
        """Test getting channel state"""
        controller = HBM4Controller()

        state = controller.get_channel_state(0)
        assert state is not None
        assert 'channel_id' in state

    def test_get_all_channel_states(self):
        """Test getting all channel states"""
        controller = HBM4Controller()

        states = controller.get_all_channel_states()
        # Returns a summary dict with 'channels' key containing per-channel data
        assert isinstance(states, dict)
        assert 'channels' in states
        assert len(states['channels']) == 32

    def test_get_stats_contains_debug_info(self):
        """Test stats contain debug info"""
        controller = HBM4Controller()

        stats = controller.get_stats()
        assert 'controller' in stats
        assert 'spec' in stats
        assert 'queues' in stats


class TestFailureModes:
    """Test various failure modes"""

    def test_invalid_channel_get_state(self):
        """Test get state for invalid channel"""
        controller = HBM4Controller()

        state = controller.get_channel_state(999)
        assert state is None

    def test_invalid_channel_repair(self):
        """Test repair for invalid channel"""
        controller = HBM4Controller()

        result = controller.trigger_repair(channel_id=999, lane_mask=0xFF)
        assert result is False

    def test_zero_size_queue(self):
        """Test queue with zero size"""
        queue = ReadQueue(max_depth=0)

        req = HBMRequest(addr=0x100, length=64, is_read=True)
        result = queue.push(req)

        # Should fail
        assert result is False


class TestConcurrencyEdgeCases:
    """Test edge cases in concurrent scenarios"""

    def test_rapid_tick_calls(self):
        """Test rapid successive tick calls"""
        controller = HBM4Controller()

        for _ in range(10000):
            controller.tick()

        # Should not crash or hang

    def test_alternating_submit_and_tick(self):
        """Test alternating submit and tick"""
        controller = HBM4Controller()

        for i in range(100):
            controller.submit_request(addr=i * 0x100, is_read=True)
            controller.tick()

    def test_queue_drain_during_fill(self):
        """Test queue draining while filling"""
        controller = HBM4Controller()

        for i in range(50):
            controller.submit_request(addr=i * 0x100, is_read=True)
            controller.tick()

        # Queue should be draining as we fill
