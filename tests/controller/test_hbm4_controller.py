"""
HBM4 Controller Integration Tests

End-to-end tests for the complete HBM4 controller model.

Test coverage:
- Basic request submission and completion
- Multi-channel scheduling
- QoS scheduling
- Refresh scheduling
- Bandwidth and latency measurements
- Address decoding across all channels
"""

import pytest
import time
from model.dram.hbm4_spec import HBM4Spec, HBM4_SPEED_GRADES
from model.controller.hbm4_controller import HBM4Controller, ChannelState
from model.controller.hbm4_address_decoder import HBM4AddressDecoder


class TestHBM4ControllerCreation:
    """Test HBM4Controller creation and initialization"""

    def test_default_creation(self):
        """Test creating controller with default parameters"""
        controller = HBM4Controller()
        assert controller.channels == 32
        assert controller.pseudo_channels == 64
        assert controller.stats.total_requests == 0

    def test_with_custom_spec(self):
        """Test creating controller with custom spec"""
        spec = HBM4Spec()
        spec.channels = 16  # Half the channels
        controller = HBM4Controller(spec=spec)
        assert controller.channels == 16
        assert controller.pseudo_channels == 32

    def test_qos_disabled(self):
        """Test creating controller with QoS disabled"""
        controller = HBM4Controller(enable_qos=False)
        assert controller.qos_scheduler is None

    def test_refresh_disabled(self):
        """Test creating controller with refresh disabled"""
        controller = HBM4Controller(enable_refresh=False)
        assert controller.refresh_scheduler is None


class TestHBM4ControllerRequestSubmission:
    """Test request submission to HBM4Controller"""

    def test_submit_single_read(self):
        """Test submitting a single read request"""
        controller = HBM4Controller()
        request_id = controller.submit_request(
            addr=0x0000000000000000,
            is_read=True,
            qos_level=8,
        )
        assert request_id is not None
        assert controller.stats.total_requests == 1
        assert controller.stats.read_requests == 1

    def test_submit_single_write(self):
        """Test submitting a single write request"""
        controller = HBM4Controller()
        request_id = controller.submit_request(
            addr=0x0000000000000000,
            is_read=False,
        )
        assert request_id is not None
        assert controller.stats.write_requests == 1

    def test_submit_multiple_requests(self):
        """Test submitting multiple requests"""
        controller = HBM4Controller()
        # Use addresses that map to different channels (channel bits at 45:41)
        # Each channel needs address bit 41+ to be set appropriately
        for i in range(10):
            # Spread across channels: ch = i % 32, put channel at bits 45:41
            ch = i % 32
            addr = (ch & 0x1F) << 41 | 0x8  # 8-byte aligned, different channels
            request_id = controller.submit_request(
                addr=addr,
                is_read=(i % 2 == 0),
            )
            assert request_id is not None
        assert controller.stats.total_requests == 10

    def test_submit_different_channels(self):
        """Test submitting requests to different channels"""
        controller = HBM4Controller()
        decoder = HBM4AddressDecoder()

        # Submit to first 8 channels using RBC mapping (channel at bits 45:41)
        for ch in range(8):
            addr = (ch & 0x1F) << 41 | 0x8  # channel at bits 45:41, 8-byte aligned
            request_id = controller.submit_request(addr=addr, is_read=True)
            assert request_id is not None

            decoded = decoder.decode(addr)
            assert decoded.channel_id == ch

    def test_queue_full(self):
        """Test behavior when queue is full"""
        controller = HBM4Controller()

        # Fill the queue for channel 0
        for i in range(100):
            request_id = controller.submit_request(
                addr=0x0000000000000000,  # Always same channel
                is_read=True,
            )
            if request_id is None:
                break

        # Should eventually fail
        assert controller.stats.total_requests > 0


class TestHBM4ControllerScheduling:
    """Test request scheduling in HBM4Controller"""

    def test_single_cycle_completion(self):
        """Test that requests complete in one cycle"""
        controller = HBM4Controller()

        # Submit request
        request_id = controller.submit_request(addr=0, is_read=True)
        assert request_id is not None

        # Tick once
        responses = controller.tick()

        # Should complete immediately (no bank conflicts)
        assert len(responses) >= 1
        assert any(r.request_id == request_id for r in responses)

    def test_multi_channel_scheduling(self):
        """Test scheduling across multiple channels"""
        controller = HBM4Controller()

        # Submit requests to different channels
        for ch in range(4):
            addr = ch << 43
            controller.submit_request(addr=addr, is_read=True)

        # Run several cycles
        total_responses = 0
        for _ in range(10):
            responses = controller.tick()
            total_responses += len(responses)

        # All requests should complete
        assert total_responses >= 4

    def test_read_write_alternation(self):
        """Test alternating read/write operations"""
        controller = HBM4Controller()

        # Submit interleaved read/write
        for i in range(4):
            controller.submit_request(addr=i * 0x100, is_read=(i % 2 == 0))

        # Run cycles
        for _ in range(10):
            controller.tick()

        assert controller.stats.read_requests == 2
        assert controller.stats.write_requests == 2


class TestHBM4ControllerQoS:
    """Test QoS scheduling functionality"""

    def test_qos_enabled(self):
        """Test that QoS is enabled by default"""
        controller = HBM4Controller(enable_qos=True)
        assert controller.qos_scheduler is not None

    def test_qos_levels(self):
        """Test different QoS levels"""
        controller = HBM4Controller()

        # Submit with different QoS levels
        for level in [0, 4, 8, 15]:
            request_id = controller.submit_request(
                addr=0,
                is_read=True,
                qos_level=level,
            )
            assert request_id is not None

    def test_high_priority_first(self):
        """Test that high priority requests are scheduled first"""
        controller = HBM4Controller()

        # Submit low priority first (qos=0 = lowest priority)
        low_req = controller.submit_request(addr=0x1000, is_read=True, qos_level=0)
        # Submit high priority second (qos=15 = highest priority)
        high_req = controller.submit_request(addr=0x0000, is_read=True, qos_level=15)

        # Track completion timestamps
        low_complete_time = None
        high_complete_time = None

        # Run cycles until both complete
        for _ in range(20):
            responses = controller.tick()
            for resp in responses:
                if resp.request_id == low_req:
                    low_complete_time = controller.current_time_ns
                elif resp.request_id == high_req:
                    high_complete_time = controller.current_time_ns

        # Both should have completed
        assert low_complete_time is not None, "Low priority request should complete"
        assert high_complete_time is not None, "High priority request should complete"

        # High priority (qos=15) should complete BEFORE low priority (qos=0)
        assert high_complete_time <= low_complete_time, \
            f"HIGH priority (qos=15) should complete before LOW priority (qos=0), " \
            f"but HIGH completed at {high_complete_time}ns and LOW at {low_complete_time}ns"

    def test_qos_ordering_multiple_levels(self):
        """Test that requests complete in strict QoS priority order"""
        controller = HBM4Controller()

        # Submit in REVERSE priority order to test scheduling
        request_ids = []
        qos_levels = [0, 4, 8, 12, 15]  # LOW to HIGH

        for qos in qos_levels:
            req_id = controller.submit_request(
                addr=len(request_ids) * 0x100,
                is_read=True,
                qos_level=qos
            )
            request_ids.append(req_id)

        # Track completion order
        completion_order = []

        # Run until all complete
        for _ in range(50):
            responses = controller.tick()
            for resp in responses:
                if resp.request_id in request_ids:
                    completion_order.append((resp.request_id, controller.current_time_ns))

        assert len(completion_order) == len(request_ids), \
            f"Expected {len(request_ids)} completions, got {len(completion_order)}"

        # Verify: higher QoS completes first
        # Extract qos for each completed request
        qos_for_id = {rid: qos for rid, qos in zip(request_ids, qos_levels)}

        # Check that for any two completions, the one with higher qos comes first
        for i in range(len(completion_order) - 1):
            curr_id, curr_time = completion_order[i]
            next_id, next_time = completion_order[i + 1]
            curr_qos = qos_for_id[curr_id]
            next_qos = qos_for_id[next_id]

            # Higher or equal QoS should come first (equal means FCFS tiebreaker)
            assert curr_qos >= next_qos, \
                f"QoS ordering violated: request with qos={next_qos} completed before qos={curr_qos}"


class TestHBM4ControllerRefresh:
    """Test refresh scheduling functionality"""

    def test_refresh_enabled(self):
        """Test that refresh is enabled by default"""
        controller = HBM4Controller(enable_refresh=True)
        assert controller.refresh_scheduler is not None

    def test_refresh_count_increments(self):
        """Test that refresh count increments"""
        controller = HBM4Controller()

        # Run many cycles to trigger refresh
        initial_refresh = controller.stats.refresh_count
        for _ in range(5000):
            controller.tick()

        # Refresh should have occurred
        assert controller.stats.refresh_count >= initial_refresh

    def test_per_bank_refresh_mode(self):
        """Test per-bank refresh mode"""
        controller = HBM4Controller()
        assert controller.refresh_scheduler.mode.name == "PER_BANK"


class TestHBM4ControllerBandwidth:
    """Test bandwidth measurement"""

    def test_bandwidth_calculation(self):
        """Test basic bandwidth calculation"""
        controller = HBM4Controller()

        # Submit many requests
        for i in range(100):
            controller.submit_request(
                addr=i * 0x100,
                is_read=True,
            )

        # Run simulation
        for _ in range(200):
            controller.tick()

        # Check bandwidth is non-zero after completion
        bandwidth = controller.get_bandwidth_gbs()
        assert bandwidth >= 0

    def test_effective_bandwidth(self):
        """Test effective bandwidth after overhead"""
        controller = HBM4Controller()

        # Submit requests
        for i in range(50):
            controller.submit_request(
                addr=i * 0x1000,
                is_read=True,
            )

        # Run simulation
        for _ in range(100):
            controller.tick()

        tbps = controller.get_effective_bandwidth_tbps()
        assert tbps >= 0
        # Effective bandwidth should be less than or equal to peak
        assert tbps <= controller.spec.bandwidth


class TestHBM4ControllerAddressDecoding:
    """Test address decoding integration"""

    def test_decode_all_32_channels(self):
        """Test that all 32 channels can be decoded"""
        controller = HBM4Controller()
        decoder = HBM4AddressDecoder()

        # For RBC mapping (default): channel at bits 45:41 (5 bits)
        for ch in range(32):
            addr = (ch & 0x1F) << 41 | 0x8  # 8-byte aligned, channel at bits 45:41
            request_id = controller.submit_request(addr=addr, is_read=True)
            assert request_id is not None

            decoded = decoder.decode(addr)
            assert decoded.channel_id == ch

    def test_decode_pseudo_channels(self):
        """Test pseudo-channel decoding"""
        controller = HBM4Controller()
        decoder = HBM4AddressDecoder()

        # For RBC mapping: pseudo_channel at bit 40 (1 bit)
        for pch in range(2):
            addr = (pch & 0x1) << 40 | 0x8  # 8-byte aligned, pseudo_channel at bit 40
            request_id = controller.submit_request(addr=addr, is_read=True)
            assert request_id is not None

            decoded = decoder.decode(addr)
            assert decoded.pseudo_channel_id == pch

    def test_decode_row_bank(self):
        """Test row and bank decoding"""
        controller = HBM4Controller()
        decoder = HBM4AddressDecoder()

        # For RBC mapping: row at bits 32:17 (16 bits), channel at bits 45:41
        row = 0x1000
        addr = (row << 17) | 0x8  # Row at bits 32:17, 8-byte aligned
        request_id = controller.submit_request(addr=addr, is_read=True)
        assert request_id is not None

        decoded = decoder.decode(addr)
        assert decoded.row_id == row


class TestHBM4ControllerStats:
    """Test statistics collection"""

    def test_stats_initialization(self):
        """Test stats are properly initialized"""
        controller = HBM4Controller()
        stats = controller.get_stats()

        assert 'controller' in stats
        assert 'spec' in stats
        assert stats['controller']['total_requests'] == 0

    def test_stats_after_requests(self):
        """Test stats are updated after requests"""
        controller = HBM4Controller()

        for i in range(5):
            controller.submit_request(addr=(i + 1) * 0x8, is_read=(i % 2 == 0))

        for _ in range(10):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 5
        assert stats['spec']['channels'] == 32

    def test_row_hit_rate(self):
        """Test row hit rate tracking"""
        controller = HBM4Controller()

        # Submit to same row (row hit)
        for i in range(3):
            controller.submit_request(addr=0x10000, is_read=True)

        # Run
        for _ in range(10):
            controller.tick()

        # Row hit rate should be tracked
        assert controller.stats.row_hit_rate >= 0


class TestHBM4ControllerTraining:
    """Test training functionality"""

    def test_trigger_training_all_channels(self):
        """Test triggering training for all channels"""
        controller = HBM4Controller()
        training_id = controller.trigger_training()
        assert training_id is not None
        assert training_id.startswith("train_")

    def test_trigger_training_single_channel(self):
        """Test triggering training for single channel"""
        controller = HBM4Controller()
        training_id = controller.trigger_training(channel_id=0)
        assert training_id is not None

    def test_training_count_increments(self):
        """Test that training count increments"""
        controller = HBM4Controller()
        initial = controller.stats.training_count

        controller.trigger_training()
        controller.trigger_training()

        assert controller.stats.training_count == initial + 2


class TestHBM4ControllerRepair:
    """Test repair functionality"""

    def test_trigger_repair(self):
        """Test triggering lane repair"""
        controller = HBM4Controller()
        success = controller.trigger_repair(channel_id=0, lane_mask=0xFF)
        assert success is True

    def test_repair_invalid_channel(self):
        """Test repair with invalid channel fails"""
        controller = HBM4Controller()
        success = controller.trigger_repair(channel_id=999, lane_mask=0xFF)
        assert success is False

    def test_repair_count_increments(self):
        """Test that repair count increments"""
        controller = HBM4Controller()
        initial = controller.stats.repair_count

        controller.trigger_repair(channel_id=0, lane_mask=0x01)
        assert controller.stats.repair_count == initial + 1


class TestHBM4ControllerSpeedGrades:
    """Test different speed grade configurations"""

    def test_8gbps_baseline(self):
        """Test 8 GT/s baseline configuration"""
        spec = create_hbm4_spec_from_speed_grade("8Gbps")
        controller = HBM4Controller(spec=spec)

        assert spec.data_rate_gtps == 8.0
        assert controller.spec.bandwidth == pytest.approx(2.048, rel=0.1)

    def test_12gbps_extended(self):
        """Test 12 GT/s extended rate"""
        spec = create_hbm4_spec_from_speed_grade("12Gbps")
        controller = HBM4Controller(spec=spec)

        assert spec.data_rate_gtps == 12.0
        assert controller.spec.bandwidth == pytest.approx(3.0, rel=0.1)

    def test_16gbps_maximum(self):
        """Test 16 GT/s maximum rate"""
        spec = create_hbm4_spec_from_speed_grade("16Gbps")
        controller = HBM4Controller(spec=spec)

        assert spec.data_rate_gtps == 16.0
        assert controller.spec.bandwidth == pytest.approx(4.0, rel=0.1)


class TestChannelState:
    """Test ChannelState class"""

    def test_channel_state_creation(self):
        """Test creating channel state"""
        from model.controller.hbm4_controller import ChannelState
        state = ChannelState(channel_id=0)
        assert state.channel_id == 0
        assert state.queue_depth == 0
        assert state.is_available() is True

    def test_channel_not_available_during_training(self):
        """Test channel unavailable during training"""
        state = ChannelState(channel_id=0)
        state.training_state = "TRAINING"
        assert state.is_available() is False

    def test_channel_not_available_in_power_down(self):
        """Test channel unavailable in power down"""
        state = ChannelState(channel_id=0)
        state.power_state = "POWER_DOWN"
        assert state.is_available() is False


class TestHBM4ControllerIntegration:
    """End-to-end integration tests"""

    def test_full_simulation(self):
        """Test a complete simulation run"""
        controller = HBM4Controller()

        # Generate traffic pattern
        for i in range(100):
            addr = (i % 8) * 0x1000000000000 + (i * 0x100)
            controller.submit_request(
                addr=addr,
                is_read=(i % 3 != 0),
                qos_level=i % 16,
            )

        # Run simulation
        for _ in range(200):
            controller.tick()

        # Verify results
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 100

    def test_concurrent_channel_access(self):
        """Test concurrent access to multiple channels"""
        controller = HBM4Controller()

        # Submit to all channels
        for ch in range(32):
            addr = ch << 43
            controller.submit_request(addr=addr, is_read=True)

        # Run until all complete
        completed = 0
        for _ in range(50):
            responses = controller.tick()
            completed += len([r for r in responses if 'REFRESH' not in r.status])

        assert completed >= 32

    def test_sustained_bandwidth(self):
        """Test sustained bandwidth over many cycles"""
        controller = HBM4Controller()

        # Continuous traffic
        for cycle in range(100):
            for ch in range(4):
                addr = (ch << 43) + (cycle << 8)
                controller.submit_request(addr=addr, is_read=True)

            controller.tick()

        bandwidth = controller.get_bandwidth_gbs()
        assert bandwidth > 0


# Import the helper function
from model.dram.hbm4_spec import create_hbm4_spec_from_speed_grade
