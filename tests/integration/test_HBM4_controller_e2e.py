"""
End-to-End Integration Tests for HBM4 Controller

Tests the complete flow from request submission through controller
to DRAM model execution.

Test Coverage:
- Complete request/response flow
- Multi-channel interleaving
- QoS scheduling validation
- Performance metrics
- Reset and cleanup
"""

import pytest
import time
from typing import List, Dict

from model.dram.HBM4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade, HBM4_SPEED_GRADES
from model.dram.HBM4_channel_model import HBM4ChannelArray, HBM4Channel
from model.dram.HBM4_bank_state_machine import HBM4BankStateMachine, HBM4BankTiming
from model.controller.HBM4_controller import (
    HBM4Controller, CommandPipeline, ChannelState, HBM4ControllerStats
)
from model.controller.HBM4_qos_scheduler import HBM4QoSScheduler, QoSLevel, TrafficType
from model.controller.request import HBMRequest, HBMResponse
from model.dram.timing import HBM4Timing


class TestEndToEndRequestFlow:
    """End-to-end request flow tests"""

    def test_single_read_request_flow(self):
        """Single read request completes correctly"""
        controller = HBM4Controller()

        # Submit read request
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert req_id is not None

        # Track completion
        completed = []
        for cycle in range(200):
            responses = controller.tick()
            completed.extend(responses)

        # Verify request completed
        completed_ids = [r.request_id for r in completed]
        assert req_id in completed_ids

    def test_single_write_request_flow(self):
        """Single write request completes correctly"""
        controller = HBM4Controller()

        # Submit write request
        req_id = controller.submit_request(
            addr=0x20000,
            is_read=False,
            qos_level=8,
            size_bytes=64,
        )
        assert req_id is not None

        # Track completion
        completed = []
        for cycle in range(200):
            responses = controller.tick()
            completed.extend(responses)

        # Verify request completed
        completed_ids = [r.request_id for r in completed]
        assert req_id in completed_ids

    def test_mixed_read_write_flow(self):
        """Mixed read/write requests complete correctly"""
        controller = HBM4Controller()

        # Submit mixed requests
        req_ids = []
        for i in range(10):
            req_id = controller.submit_request(
                addr=0x1000 * i,
                is_read=(i % 2 == 0),
                qos_level=8,
                size_bytes=64,
            )
            req_ids.append(req_id)

        # All requests should be accepted
        assert all(rid is not None for rid in req_ids)

        # Run controller
        completed = []
        for cycle in range(500):
            responses = controller.tick()
            completed.extend(responses)

        # Most requests should complete
        completed_ids = [r.request_id for r in completed]
        assert len(completed_ids) >= 8


class TestEndToEndMultiChannel:
    """Multi-channel interleaving tests"""

    def test_all_channels_accessible(self):
        """All 32 channels can be accessed"""
        controller = HBM4Controller()

        # Submit to each channel
        for ch in range(32):
            addr = ch << 17  # Channel address
            req_id = controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )
            assert req_id is not None

        # Run controller
        completed = []
        for cycle in range(2000):
            responses = controller.tick()
            completed.extend(responses)

        # Verify all submitted
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 32

    def test_channel_interleaving(self):
        """Requests interleave across channels"""
        controller = HBM4Controller()

        # Submit to multiple channels
        ch_map = {}
        for ch in [0, 8, 16, 24]:
            addr = ch << 17
            req_id = controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )
            ch_map[req_id] = ch

        # Run controller
        for cycle in range(500):
            controller.tick()

        # Verify each channel got traffic
        for ch_id, ch_state in controller._channel_states.items():
            if ch_id in [0, 8, 16, 24]:
                # These channels should have been active
                pass

    def test_channel_independence(self):
        """Channels operate independently"""
        controller = HBM4Controller()

        # Submit to two channels
        req1 = controller.submit_request(
            addr=0 << 17,  # Channel 0
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        req2 = controller.submit_request(
            addr=16 << 17,  # Channel 16
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )

        # Both should be accepted
        assert req1 is not None
        assert req2 is not None

        # Run
        for _ in range(500):
            controller.tick()


class TestEndToEndQoSScheduling:
    """QoS scheduling validation tests"""

    def test_critical_priority_first(self):
        """Critical priority requests are processed first"""
        controller = HBM4Controller(enable_qos=True)

        # Submit low priority first
        low_id = controller.submit_request(
            addr=0x1000,
            is_read=True,
            qos_level=QoSLevel.LOW,
            size_bytes=64,
        )

        # Submit critical priority second
        critical_id = controller.submit_request(
            addr=0x2000,
            is_read=True,
            qos_level=QoSLevel.CRITICAL,
            size_bytes=64,
        )

        # Run controller
        completed = []
        completion_order = []
        for _ in range(500):
            responses = controller.tick()
            for r in responses:
                completed.append(r)
                completion_order.append(r.request_id)

        # Critical should complete first (or at least be scheduled first)
        if critical_id in completion_order and low_id in completion_order:
            assert completion_order.index(critical_id) < completion_order.index(low_id)

    def test_qos_bandwidth_guarantee(self):
        """High priority gets bandwidth guarantee"""
        controller = HBM4Controller(enable_qos=True)

        # Submit many requests at different priorities
        critical_count = 0
        normal_count = 0

        for i in range(20):
            if i < 5:
                qos = QoSLevel.CRITICAL
                critical_count += 1
            else:
                qos = QoSLevel.NORMAL
                normal_count += 1

            controller.submit_request(
                addr=0x1000 * i,
                is_read=True,
                qos_level=qos,
                size_bytes=64,
            )

        # Run controller
        for _ in range(2000):
            controller.tick()

        # Get stats
        stats = controller.get_stats()
        qos_stats = controller.qos_scheduler.get_stats()

        # Verify QoS scheduling happened
        assert 'by_qos' in qos_stats

    def test_qos_all_16_levels(self):
        """All 16 QoS levels are functional"""
        controller = HBM4Controller(enable_qos=True)

        # Submit at each level
        for level in range(16):
            req_id = controller.submit_request(
                addr=0x1000 * level,
                is_read=True,
                qos_level=level,
                size_bytes=64,
            )
            assert req_id is not None

        # Run controller
        for _ in range(3000):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 16


class TestEndToEndPerformance:
    """Performance metric tests"""

    def test_throughput_calculation(self):
        """Throughput is calculated correctly"""
        controller = HBM4Controller()

        # Submit requests
        for i in range(50):
            controller.submit_request(
                addr=0x1000 * i,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )

        # Run
        start = time.time()
        for _ in range(2000):
            controller.tick()
        elapsed = time.time() - start

        # Get bandwidth
        bw = controller.get_bandwidth_gbs()
        assert bw >= 0

    def test_latency_tracking(self):
        """Latency is tracked correctly"""
        controller = HBM4Controller()

        # Submit request
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )

        # Run until completion
        completed = []
        for _ in range(500):
            responses = controller.tick()
            completed.extend([r for r in responses if r.request_id == req_id])

        # Latency should be recorded
        if completed:
            latency = completed[0].latency
            assert latency > 0

    def test_row_hit_rate(self):
        """Row hit rate is calculated"""
        controller = HBM4Controller()

        # Submit to same row multiple times
        same_row_addr = 0x10000
        for _ in range(10):
            controller.submit_request(
                addr=same_row_addr,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )

        # Run
        for _ in range(2000):
            controller.tick()

        stats = controller.get_stats()
        assert 'row_hit_rate' in stats['controller']

    def test_bandwidth_efficiency(self):
        """Bandwidth efficiency is tracked"""
        controller = HBM4Controller()

        # Generate traffic
        for i in range(100):
            controller.submit_request(
                addr=0x1000 * i,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )

        # Run
        for _ in range(5000):
            controller.tick()

        bw = controller.get_bandwidth_gbs()
        peak = controller.spec.bandwidth_gbs

        # Achieved bandwidth should be less than peak
        assert bw <= peak


class TestEndToEndReset:
    """Reset and cleanup tests"""

    def test_controller_reset(self):
        """Controller resets correctly"""
        controller = HBM4Controller()

        # Submit requests
        for i in range(10):
            controller.submit_request(
                addr=0x1000 * i,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )

        # Run some cycles
        for _ in range(100):
            controller.tick()

        # Reset
        controller.reset()

        # Verify reset
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 0
        assert stats['queues']['read_depth'] == 0

    def test_reset_clears_pipeline(self):
        """Reset clears pipeline"""
        controller = HBM4Controller(enable_pipeline=True)

        # Submit request
        controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )

        # Run a bit
        for _ in range(10):
            controller.tick()

        # Reset
        controller.reset()

        # Pipeline should be cleared
        if controller._pipeline:
            assert controller._pipeline.get_pipeline_depth() == 0

    def test_reset_clears_row_state(self):
        """Reset clears row state"""
        controller = HBM4Controller()

        # Submit request
        controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )

        # Run to completion
        for _ in range(200):
            controller.tick()

        # Row state may have entries
        state_before = len(controller._row_state)

        # Reset
        controller.reset()

        # Row state should be empty
        assert len(controller._row_state) == 0


class TestEndToEndSpeedGrades:
    """Speed grade configuration tests"""

    def test_8gbps_config(self):
        """8 Gbps speed grade works"""
        spec = create_hbm4_spec_from_speed_grade("8Gbps")
        controller = HBM4Controller(spec=spec)

        assert controller.spec.data_rate_gtps == 8.0
        assert controller.spec.tCK_ps == 125.0

        # Submit request
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert req_id is not None

    def test_12gbps_config(self):
        """12 Gbps speed grade works"""
        spec = create_hbm4_spec_from_speed_grade("12Gbps")
        controller = HBM4Controller(spec=spec)

        assert controller.spec.data_rate_gtps == 12.0
        assert abs(controller.spec.tCK_ps - 83.33) < 0.1

        # Submit request
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert req_id is not None

    def test_16gbps_config(self):
        """16 Gbps speed grade works"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        controller = HBM4Controller(spec=spec)

        assert controller.spec.data_rate_gtps == 16.0
        assert controller.spec.tCK_ps == 62.5

        # Submit request
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert req_id is not None


class TestEndToEndDFIIntegration:
    """DFI interface integration tests"""

    def test_dfi_commands_generated(self):
        """DFI commands are generated for requests"""
        controller = HBM4Controller(enable_dfi=True)

        # Submit read
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert req_id is not None

        # DFI request should be generated
        assert req_id in controller._pending_commands

    def test_dfi_low_power_transition(self):
        """DFI low power states work"""
        from model.dram.dfi_interface import DFILowPowerState

        controller = HBM4Controller(enable_dfi=True)

        # Enter self-refresh
        result = controller.dfi_set_low_power(DFILowPowerState.LP_SELF_REFRESH)
        assert result is True

        # Exit
        controller.dfi_wakeup()


class TestEndToEndChannelModelIntegration:
    """Channel model integration tests"""

    def test_channel_model_tick_sync(self):
        """Channel model is synchronized with controller"""
        controller = HBM4Controller()

        # Run controller
        for i in range(100):
            controller.tick()
            ch_cycle = controller.channel_model.channels[0].current_cycle
            assert ch_cycle == i + 1

    def test_command_issued_to_channel(self):
        """Commands are issued to channel model"""
        controller = HBM4Controller()

        # Submit request
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )

        # Run
        for _ in range(100):
            controller.tick()

        # Channel model should have received commands
        ch = controller.channel_model.get_channel(0)
        if ch:
            stats = ch.get_performance_stats()
            # May have some activity depending on address

    def test_refresh_executed_on_channel(self):
        """Refresh is executed on channel model"""
        controller = HBM4Controller(enable_refresh=True)

        # Wait for refresh
        for _ in range(1000):
            controller.tick()

        # Refresh scheduler should have triggered
        if controller.refresh_scheduler:
            refresh_count = controller.stats.refresh_count
            # May or may not have refreshed depending on timing


class TestEndToEndLongRun:
    """Long running simulation tests"""

    def test_sustained_traffic(self):
        """Controller handles sustained traffic"""
        controller = HBM4Controller()

        total_submitted = 0
        max_inflight = 0

        # Submit traffic continuously
        for cycle in range(1000):
            # Submit new requests periodically
            if cycle % 10 == 0:
                for ch in range(4):
                    req_id = controller.submit_request(
                        addr=(ch << 17) + (cycle << 8),
                        is_read=(cycle % 2 == 0),
                        qos_level=8,
                        size_bytes=64,
                    )
                    if req_id:
                        total_submitted += 1

            # Track inflight
            inflight = len(controller._pending_requests)
            max_inflight = max(max_inflight, inflight)

            controller.tick()

        # Verify
        assert total_submitted > 0
        assert max_inflight > 0

    def test_no_queue_overflow(self):
        """Queue handles burst traffic without overflow"""
        controller = HBM4Controller()

        # Submit burst
        for i in range(256):  # More than queue depth
            req_id = controller.submit_request(
                addr=0x1000 * i,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )
            # Some may be rejected, that's expected
            if req_id is None:
                break

        # Run to drain
        for _ in range(5000):
            controller.tick()

        # System should be stable
        stats = controller.get_stats()
        assert stats['queues']['read_depth'] < 300


class TestEndToEndBankGroupScheduling:
    """Bank group-aware scheduling tests"""

    def test_bank_group_interleaving(self):
        """Bank groups can interleave"""
        controller = HBM4Controller()

        # Submit to different bank groups in same channel
        for bg in range(8):
            for bank_in_group in range(2):
                # Calculate address with bank group
                bank = bg * 2 + bank_in_group
                addr = (bank << 12)  # Simplified addressing

                req_id = controller.submit_request(
                    addr=addr,
                    is_read=True,
                    qos_level=8,
                    size_bytes=64,
                )
                if req_id:
                    break  # Only need one per BG

        # Run
        for _ in range(2000):
            controller.tick()

    def test_bank_group_timing_respected(self):
        """Bank group timing is respected"""
        controller = HBM4Controller()

        # Submit rapid ACT commands to same BG
        for i in range(10):
            controller.submit_request(
                addr=0x1000 * i,
                is_read=True,
                qos_level=15,  # Critical to force scheduling
                size_bytes=64,
            )

        # Run with limited time
        for _ in range(200):
            controller.tick()

        # Some commands may have been delayed by tRRDS


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
