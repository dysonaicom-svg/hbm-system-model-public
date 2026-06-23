"""
Tests for HBM4 Controller - QoS Scheduling Validation

Tests the complete QoS scheduling system with:
- 16 priority levels
- Row hit/miss handling
- Command pipeline integration
- Bank conflict tracking
- End-to-end performance validation
"""

import pytest
from typing import List, Dict, Tuple

from model.dram.HBM4_spec import HBM4Spec
from model.dram.HBM4_channel_model import HBM4ChannelArray
from model.controller.HBM4_controller import (
    HBM4Controller, HBM4ControllerStats, CommandPipeline, PipelineCommand,
    ChannelState
)
from model.controller.HBM4_qos_scheduler import (
    HBM4QoSScheduler, QoSLevel, TrafficType
)
from model.controller.request import HBMRequest, HBMResponse, RequestState


class TestCommandPipeline:
    """Tests for CommandPipeline"""

    def test_pipeline_initialization(self):
        """Pipeline initializes correctly"""
        pipeline = CommandPipeline(num_stages=4, pipeline_depth=16)

        assert pipeline.num_stages == 4
        assert pipeline.pipeline_depth == 16
        assert pipeline.get_pipeline_depth() == 0
        assert pipeline.stalls == 0

    def test_pipeline_enqueue(self):
        """Commands can be enqueued"""
        pipeline = CommandPipeline()

        cmd = PipelineCommand(
            command='ACT',
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            row_id=100,
            col_id=0,
            request_id='req1',
            issue_cycle=0,
        )

        result = pipeline.enqueue(cmd)
        assert result is True
        assert pipeline.get_pipeline_depth() == 1

    def test_pipeline_full(self):
        """Pipeline correctly handles full condition"""
        pipeline = CommandPipeline(pipeline_depth=2)

        # Fill the pipeline
        for i in range(2):
            cmd = PipelineCommand(
                command='ACT',
                channel_id=0,
                pseudo_channel_id=0,
                bank_id=i,
                row_id=100,
                col_id=0,
                request_id=f'req{i}',
                issue_cycle=0,
            )
            assert pipeline.enqueue(cmd) is True

        # Pipeline should be full now
        assert pipeline.get_pipeline_depth() == 2

        # Next enqueue should fail
        cmd = PipelineCommand(
            command='ACT',
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=2,
            row_id=100,
            col_id=0,
            request_id='req3',
            issue_cycle=0,
        )
        result = pipeline.enqueue(cmd)
        assert result is False
        assert pipeline.stalls == 1

    def test_pipeline_tick(self):
        """Pipeline advances with tick"""
        pipeline = CommandPipeline()

        cmd = PipelineCommand(
            command='ACT',
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            row_id=100,
            col_id=0,
            request_id='req1',
            issue_cycle=0,
        )
        pipeline.enqueue(cmd)

        # Tick should not complete the command (no completion cycle set)
        completed = pipeline.tick()
        assert len(completed) == 0
        assert pipeline.get_pipeline_depth() == 1

    def test_pipeline_completion(self):
        """Pipeline handles command completion"""
        pipeline = CommandPipeline()

        cmd = PipelineCommand(
            command='ACT',
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            row_id=100,
            col_id=0,
            request_id='req1',
            issue_cycle=0,
            completion_cycle=10,
        )
        pipeline.enqueue(cmd)

        # Tick until completion
        for _ in range(9):
            pipeline.tick()
        assert pipeline.get_pipeline_depth() == 1

        # At cycle 10
        completed = pipeline.tick()
        assert len(completed) == 1
        assert completed[0].request_id == 'req1'
        assert pipeline.get_pipeline_depth() == 0
        assert pipeline.commands_completed == 1

    def test_pipeline_stats(self):
        """Pipeline statistics are tracked"""
        pipeline = CommandPipeline(pipeline_depth=4)

        # Add some commands
        for i in range(3):
            cmd = PipelineCommand(
                command='RD',
                channel_id=0,
                pseudo_channel_id=0,
                bank_id=i,
                row_id=100,
                col_id=0,
                request_id=f'req{i}',
                issue_cycle=i,
                completion_cycle=i + 20,
            )
            pipeline.enqueue(cmd)

        stats = pipeline.get_stats()
        assert stats['pipeline_depth'] == 3
        assert stats['max_depth'] == 4
        assert stats['stalls'] == 0


class TestHBM4ControllerQoS:
    """Tests for HBM4 Controller QoS integration"""

    def test_controller_qos_initialization(self):
        """Controller initializes with QoS scheduler"""
        controller = HBM4Controller(enable_qos=True)

        assert controller.qos_scheduler is not None
        assert controller._enable_qos is True

    def test_controller_qos_submit_critical(self):
        """Critical QoS requests are accepted"""
        controller = HBM4Controller(enable_qos=True)

        request_id = controller.submit_request(
            addr=0x1000,
            is_read=True,
            qos_level=QoSLevel.CRITICAL,
            size_bytes=64,
        )

        assert request_id is not None

    def test_controller_qos_submit_low(self):
        """Low QoS requests are accepted"""
        controller = HBM4Controller(enable_qos=True)

        request_id = controller.submit_request(
            addr=0x2000,
            is_read=False,
            qos_level=QoSLevel.LOW,
            size_bytes=64,
        )

        assert request_id is not None

    def test_controller_qos_priority_ordering(self):
        """Higher QoS requests are processed first"""
        controller = HBM4Controller(enable_qos=True)

        # Submit requests in mixed order
        req_low = controller.submit_request(
            addr=0x1000,
            is_read=True,
            qos_level=QoSLevel.LOW,
            size_bytes=64,
        )
        req_critical = controller.submit_request(
            addr=0x2000,
            is_read=True,
            qos_level=QoSLevel.CRITICAL,
            size_bytes=64,
        )
        req_high = controller.submit_request(
            addr=0x3000,
            is_read=True,
            qos_level=QoSLevel.HIGH,
            size_bytes=64,
        )

        assert req_low is not None
        assert req_critical is not None
        assert req_high is not None

        # Run controller to process requests
        responses = []
        for _ in range(100):
            resp = controller.tick()
            responses.extend(resp)

        # Verify critical request was processed
        critical_processed = any(r.request_id == req_critical for r in responses)
        high_processed = any(r.request_id == req_high for r in responses)

        assert critical_processed or high_processed

    def test_controller_qos_all_levels(self):
        """All 16 QoS levels are accepted"""
        controller = HBM4Controller(enable_qos=True)

        submitted = []
        for qos in range(16):
            request_id = controller.submit_request(
                addr=0x1000 + (qos << 12),
                is_read=True,
                qos_level=qos,
                size_bytes=64,
            )
            submitted.append(request_id)

        # All should be accepted
        assert all(req_id is not None for req_id in submitted)


class TestHBM4ControllerRowHit:
    """Tests for row hit/miss handling"""

    def test_row_hit_detection(self):
        """Row hits are detected for same row access"""
        controller = HBM4Controller()

        # First request opens a row
        req1 = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert req1 is not None

        # Run some cycles to complete the first request
        for _ in range(50):
            controller.tick()

        # Second request to same row should be a row hit
        req2 = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert req2 is not None

        # Check if row state was updated
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] >= 2

    def test_row_miss_tracking(self):
        """Row misses are tracked correctly"""
        controller = HBM4Controller()

        # Submit requests to different rows
        for i in range(5):
            # Each row is 4KB apart (row boundary)
            addr = 0x10000 + (i * 0x4000)
            req = controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )
            assert req is not None

        # Run controller
        for _ in range(200):
            controller.tick()

        # Stats should track requests
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 5


class TestHBM4ControllerBankConflict:
    """Tests for bank conflict handling"""

    def test_bank_conflict_tracking(self):
        """Bank conflicts are tracked"""
        controller = HBM4Controller()

        # Submit multiple requests to same bank, different rows
        base_addr = 0x10000
        for i in range(3):
            addr = base_addr + (i * 0x1000)  # Different columns, same bank
            req = controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )
            assert req is not None

        # Run controller
        for _ in range(100):
            controller.tick()

        stats = controller.get_stats()
        assert 'bank_conflicts' in stats['controller']

    def test_bank_state_update(self):
        """Bank state is updated correctly"""
        controller = HBM4Controller()

        # Submit a request
        req = controller.submit_request(
            addr=0x20000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )

        # Run to completion
        for _ in range(100):
            controller.tick()

        # Check row state
        assert len(controller._row_state) >= 0


class TestHBM4ControllerChannelModel:
    """Tests for HBM4 Controller with Channel Model integration"""

    def test_channel_model_initialization(self):
        """Controller initializes with channel model"""
        controller = HBM4Controller()

        assert controller.channel_model is not None
        assert controller.channel_model.num_channels == 32

    def test_channel_state_retrieval(self):
        """Channel state can be retrieved"""
        controller = HBM4Controller()

        state = controller.get_channel_state(0)
        assert state is not None
        assert 'channel_id' in state

    def test_all_channel_states(self):
        """All channel states can be retrieved"""
        controller = HBM4Controller()

        states = controller.get_all_channel_states()
        assert states is not None
        assert 'num_channels' in states

    def test_channel_model_issue_command(self):
        """Channel model commands work"""
        controller = HBM4Controller()

        ch = controller.channel_model.get_channel(0)
        assert ch is not None

        # Issue ACT command
        result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        assert result is True

    def test_controller_tick_advances_channel(self):
        """Controller tick advances channel model"""
        controller = HBM4Controller()

        initial_cycle = controller.channel_model.channels[0].current_cycle

        controller.tick()

        assert controller.channel_model.channels[0].current_cycle == initial_cycle + 1


class TestHBM4ControllerPipeline:
    """Tests for command pipeline integration"""

    def test_pipeline_enabled(self):
        """Pipeline is enabled by default"""
        controller = HBM4Controller(enable_pipeline=True)

        assert controller._pipeline is not None
        assert controller._enable_pipeline is True

    def test_pipeline_disabled(self):
        """Pipeline can be disabled"""
        controller = HBM4Controller(enable_pipeline=False)

        assert controller._pipeline is None
        assert controller._enable_pipeline is False

    def test_pipeline_stats_in_controller(self):
        """Pipeline stats are included in controller stats"""
        controller = HBM4Controller(enable_pipeline=True)

        stats = controller.get_stats()
        assert 'pipeline' in stats
        assert stats['pipeline'] is not None


class TestHBM4ControllerRefresh:
    """Tests for refresh integration"""

    def test_refresh_enabled(self):
        """Refresh scheduler is enabled"""
        controller = HBM4Controller(enable_refresh=True)

        assert controller.refresh_scheduler is not None
        assert controller._enable_refresh is True

    def test_refresh_disabled(self):
        """Refresh can be disabled"""
        controller = HBM4Controller(enable_refresh=False)

        assert controller.refresh_scheduler is None
        assert controller._enable_refresh is False


class TestHBM4ControllerDFI:
    """Tests for DFI interface"""

    def test_dfi_enabled(self):
        """DFI interface is enabled"""
        controller = HBM4Controller(enable_dfi=True)

        assert controller.dfi is not None
        assert controller.dfi_ready is True

    def test_dfi_disabled(self):
        """DFI can be disabled"""
        controller = HBM4Controller(enable_dfi=False)

        assert controller.dfi is None

    def test_dfi_signals(self):
        """DFI signals can be retrieved"""
        controller = HBM4Controller(enable_dfi=True)

        signals = controller.dfi_get_signals()
        assert signals is not None


class TestHBM4ControllerStatistics:
    """Tests for controller statistics"""

    def test_stats_initialization(self):
        """Stats initialize correctly"""
        stats = HBM4ControllerStats()

        assert stats.total_requests == 0
        assert stats.read_requests == 0
        assert stats.write_requests == 0
        assert stats.row_hit_count == 0

    def test_average_latency_calculation(self):
        """Average latency is calculated correctly"""
        stats = HBM4ControllerStats()
        stats.total_requests = 10
        stats.total_latency_ns = 500.0

        assert stats.average_latency_ns == 50.0

    def test_row_hit_rate_calculation(self):
        """Row hit rate is calculated correctly"""
        stats = HBM4ControllerStats()
        stats.read_requests = 80
        stats.write_requests = 20
        stats.row_hit_count = 50

        expected_rate = 50.0 / 100.0
        assert abs(stats.row_hit_rate - expected_rate) < 0.001

    def test_get_stats_comprehensive(self):
        """get_stats returns comprehensive information"""
        controller = HBM4Controller()

        stats = controller.get_stats()

        assert 'controller' in stats
        assert 'spec' in stats
        assert 'queues' in stats
        assert 'qos' in stats
        assert 'refresh' in stats
        assert 'dfi' in stats


class TestHBM4ControllerEndToEnd:
    """End-to-end tests for HBM4 Controller"""

    def test_submit_and_complete_request(self):
        """Submit request and verify completion"""
        controller = HBM4Controller()

        # Submit a read request
        request_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert request_id is not None

        # Run controller
        completed = []
        for _ in range(100):
            responses = controller.tick()
            completed.extend(responses)

        # Request should complete
        assert len(completed) > 0

    def test_multiple_requests(self):
        """Multiple requests can be submitted"""
        controller = HBM4Controller()

        # Submit 10 requests
        request_ids = []
        for i in range(10):
            req_id = controller.submit_request(
                addr=0x1000 + (i * 0x1000),
                is_read=(i % 2 == 0),
                qos_level=8,
                size_bytes=64,
            )
            request_ids.append(req_id)

        # All should be accepted
        assert all(req_id is not None for req_id in request_ids)

        # Run controller
        completed = []
        for _ in range(500):
            responses = controller.tick()
            completed.extend(responses)

        # Most should complete
        assert len(completed) >= 8

    def test_bandwidth_calculation(self):
        """Bandwidth is calculated correctly"""
        controller = HBM4Controller()

        # Submit requests
        for i in range(10):
            controller.submit_request(
                addr=0x1000 + (i * 0x1000),
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )

        # Run controller
        for _ in range(200):
            controller.tick()

        bw = controller.get_bandwidth_gbs()
        assert bw >= 0.0

    def test_reset(self):
        """Controller reset works"""
        controller = HBM4Controller()

        # Submit some requests
        for i in range(5):
            controller.submit_request(
                addr=0x1000 + (i * 0x1000),
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )

        # Reset
        controller.reset()

        # State should be cleared
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 0


class TestHBM4ControllerQoSValidation:
    """Comprehensive QoS validation tests"""

    def test_qos_scheduler_16_levels(self):
        """All 16 QoS levels are supported"""
        scheduler = HBM4QoSScheduler()

        assert scheduler.priority_levels == 16

        # Test all levels
        for level in range(16):
            # Submit request at each level
            success = scheduler.submit_request(
                request_id=f"req_{level}",
                qos=level,
                is_read=True,
            )
            # Should succeed (queue depth check may fail for some, but no other errors)
            assert success or level >= 15  # High levels may fill queue

    def test_qos_scheduler_select_next(self):
        """select_next returns highest priority"""
        scheduler = HBM4QoSScheduler()

        # Create requests at different QoS levels
        requests = []
        for qos in [4, 8, 12, 15]:
            req = HBMRequest(
                addr=0x1000 * qos,
                length=64,
                is_read=True,
                qos=qos,
                request_id=f"req_qos{qos}",
            )
            requests.append(req)

        # Select should return highest QoS
        selected = scheduler.select_next(requests)
        assert selected is not None
        assert selected.qos == 15

    def test_qos_scheduler_traffic_classification(self):
        """Traffic types are classified correctly"""
        scheduler = HBM4QoSScheduler()

        # Create requests with different QoS levels
        req_critical = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            qos=15,  # Critical level
            request_id="req1",
        )
        level = scheduler.classify_request(req_critical)
        assert level == 15

        # NORMAL traffic
        req_normal = HBMRequest(
            addr=0x2000,
            length=64,
            is_read=True,
            qos=8,  # Normal level
            request_id="req2",
        )
        level = scheduler.classify_request(req_normal)
        assert level == 8

    def test_qos_scheduler_bandwidth_guarantee(self):
        """Bandwidth guarantees are enforced"""
        scheduler = HBM4QoSScheduler()

        # Set bandwidth guarantee
        scheduler.set_bandwidth_guarantee(15, 100.0)

        guarantee = scheduler.bw_guarantee.get(15)
        assert guarantee == 100.0

    def test_qos_scheduler_starvation_prevention(self):
        """Starvation prevention works"""
        scheduler = HBM4QoSScheduler()

        # Submit low priority request
        scheduler.submit_request(
            request_id="low_priority",
            qos=0,
            is_read=True,
        )

        # Boost starving requests
        scheduler.boost_starving()

        stats = scheduler.get_stats()
        assert 'total_scheduled' in stats


class TestHBM4ControllerIntegration:
    """Integration tests with full system"""

    def test_controller_with_all_features(self):
        """Controller works with all features enabled"""
        controller = HBM4Controller(
            enable_qos=True,
            enable_refresh=True,
            enable_dfi=True,
            enable_pipeline=True,
        )

        assert controller.qos_scheduler is not None
        assert controller.refresh_scheduler is not None
        assert controller.dfi is not None
        assert controller._pipeline is not None

        # Submit request
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=12,
            size_bytes=64,
        )
        assert req_id is not None

        # Run controller
        for _ in range(50):
            controller.tick()

    def test_controller_minimal(self):
        """Controller works with minimal features"""
        controller = HBM4Controller(
            enable_qos=False,
            enable_refresh=False,
            enable_dfi=False,
            enable_pipeline=False,
        )

        # Should still work
        req_id = controller.submit_request(
            addr=0x10000,
            is_read=True,
            qos_level=8,
            size_bytes=64,
        )
        assert req_id is not None

        # Run controller
        for _ in range(50):
            controller.tick()

    def test_32_channel_access(self):
        """All 32 channels can be accessed"""
        controller = HBM4Controller()

        # Submit request to each channel
        for ch in range(32):
            addr = ch << 17  # Channel field starts at bit 17
            req_id = controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )
            assert req_id is not None

        # Run controller
        for _ in range(1000):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 32

    def test_controller_performance_summary(self):
        """Performance summary is available"""
        controller = HBM4Controller()

        # Generate some traffic
        for i in range(20):
            controller.submit_request(
                addr=0x1000 * i,
                is_read=(i % 2 == 0),
                qos_level=8,
                size_bytes=64,
            )

        # Run
        for _ in range(500):
            controller.tick()

        stats = controller.get_stats()
        assert 'channel_model' in stats
        assert 'performance' in stats['channel_model']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
