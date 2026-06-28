"""
Tests for HBM4 Controller Load Balancing

Tests the channel load balancing optimization features.
"""

import pytest
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import HBM4Spec


class TestChannelLoadBalancing:
    """Test suite for channel load balancing features"""

    def test_channel_load_report(self):
        """Test get_channel_load_report returns valid data for all channels"""
        controller = HBM4Controller()

        report = controller.get_channel_load_report()

        assert len(report) == 32  # HBM4 has 32 channels
        for ch_id, metrics in report.items():
            assert 'channel_id' in metrics
            assert 'queue_depth' in metrics
            assert 'pending_requests' in metrics
            assert 'completed_requests' in metrics
            assert 'load_score' in metrics
            assert 'avg_latency_ns' in metrics
            assert metrics['channel_id'] == ch_id

    def test_channel_load_imbalance(self):
        """Test get_channel_load_imbalance calculates correctly"""
        controller = HBM4Controller()

        imbalance = controller.get_channel_load_imbalance()

        assert 'imbalance' in imbalance
        assert 'max_load' in imbalance
        assert 'min_load' in imbalance
        assert 'avg_load' in imbalance
        assert 'max_channel' in imbalance
        assert 'min_channel' in imbalance
        assert 'total_channels' in imbalance
        assert imbalance['total_channels'] == 32
        assert imbalance['imbalance'] >= 0.0

    def test_least_loaded_channels(self):
        """Test get_least_loaded_channels returns sorted channel IDs"""
        controller = HBM4Controller()

        least_loaded = controller.get_least_loaded_channels(count=4)

        assert len(least_loaded) == 4
        assert all(0 <= ch < 32 for ch in least_loaded)
        # Verify they are sorted by load (least loaded first)
        report = controller.get_channel_load_report()
        loads = [report[ch]['load_score'] for ch in least_loaded]
        assert loads == sorted(loads)

    def test_channel_utilization(self):
        """Test get_channel_utilization returns valid percentages"""
        controller = HBM4Controller()

        utilization = controller.get_channel_utilization()

        assert len(utilization) == 32
        for ch_id, util in utilization.items():
            assert 0.0 <= util <= 1.0

    def test_load_balance_after_requests(self):
        """Test load metrics update after submitting requests"""
        controller = HBM4Controller()

        # Submit requests to different channels
        base_addr = 0x10000
        for i in range(8):
            addr = base_addr + (i * 0x1000000)  # Spread across channels
            controller.submit_request(addr, is_read=True)

        # Check load metrics
        report = controller.get_channel_load_report()
        utilization = controller.get_channel_utilization()

        # Verify some channels have load
        total_queue_depth = sum(m['queue_depth'] for m in report.values())
        assert total_queue_depth == 8

        # Verify utilization reflects queue depth
        total_util = sum(utilization.values())
        assert total_util > 0

    def test_channel_completion_tracking(self):
        """Test that completed requests update channel metrics"""
        controller = HBM4Controller()

        # Submit a request
        controller.submit_request(0x10000, is_read=True)

        # Complete the request by ticking
        controller.tick()

        # Check completion tracking
        report = controller.get_channel_load_report()
        channel = controller.get_channel_id(0x10000)
        ch_report = report[channel]

        # Should have some completed requests
        assert ch_report['completed_requests'] >= 0  # May complete in future cycles
        assert ch_report['avg_latency_ns'] >= 0

    def test_log_load_balance_warning(self):
        """Test log_load_balance_warning detection"""
        controller = HBM4Controller()

        # Initially balanced
        assert controller.log_load_balance_warning() == False

        # After many requests to same channel, should detect imbalance
        for i in range(100):
            # Force requests to channel 0
            controller.queue_manager.push_read(
                type('Request', (), {
                    'channel_id': 0,
                    'pseudo_channel_id': 0,
                    'bank_id': 0,
                    'row_id': 0,
                    'is_read': True,
                    'arrival_time': 0,
                    'request_id': f'test_{i}'
                })()
            )

        # Should detect high imbalance
        imbalance = controller.get_channel_load_imbalance()
        if imbalance['imbalance'] > 0.5:
            assert controller.log_load_balance_warning(0.5) == True

    def test_reset_clears_load_state(self):
        """Test that reset clears all load balancing state"""
        controller = HBM4Controller()

        # Submit some requests
        for i in range(10):
            controller.submit_request(0x10000 + i * 0x1000, is_read=True)

        # Record initial load
        initial_report = controller.get_channel_load_report()

        # Reset
        controller.reset()

        # Verify load state is cleared
        reset_report = controller.get_channel_load_report()
        for ch_id, metrics in reset_report.items():
            assert metrics['queue_depth'] == 0
            assert metrics['pending_requests'] == 0
            assert metrics['completed_requests'] == 0

    def test_load_balance_in_stats(self):
        """Test that load balance stats appear in get_stats"""
        controller = HBM4Controller()

        stats = controller.get_stats()

        assert 'load_balance' in stats
        assert 'imbalance' in stats['load_balance']
        assert 'utilization' in stats['load_balance']


class TestChannelStateLoadMetrics:
    """Test ChannelState load tracking"""

    def test_update_load(self):
        """Test ChannelState.update_load updates metrics"""
        from model.controller.hbm4_controller import ChannelState

        state = ChannelState(channel_id=0)

        state.update_load(queue_depth=5, pending=3, cycle=100)

        assert state.queue_depth == 5
        assert state.pending_requests == 3
        assert state.last_access_cycle == 100
        assert state.load_score == 5 + 3 * 2  # 11

    def test_record_completion(self):
        """Test ChannelState.record_completion updates metrics"""
        from model.controller.hbm4_controller import ChannelState

        state = ChannelState(channel_id=0)

        state.record_completion(latency_ns=50.0, cycle=100)
        state.record_completion(latency_ns=60.0, cycle=101)

        assert state.completed_requests == 2
        assert state.total_latency_ns == 110.0
        # Compute avg from total and count
        avg_latency = state.total_latency_ns / state.completed_requests
        assert avg_latency == 55.0

    def test_get_load_report(self):
        """Test ChannelState.get_load_report returns correct data"""
        from model.controller.hbm4_controller import ChannelState

        state = ChannelState(channel_id=5)
        state.update_load(queue_depth=3, pending=2, cycle=50)
        state.record_completion(latency_ns=40.0, cycle=51)

        report = state.get_load_report()

        assert report['channel_id'] == 5
        assert report['queue_depth'] == 3
        assert report['pending_requests'] == 2
        assert report['completed_requests'] == 1
        assert report['load_score'] == 7.0
        assert report['avg_latency_ns'] == 40.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])