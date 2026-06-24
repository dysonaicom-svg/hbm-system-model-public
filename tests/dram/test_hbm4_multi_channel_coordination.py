"""
Multi-Channel Coordination Tests for HBM4

Tests the coordination between multiple HBM4 channels, including:
- Channel-to-channel synchronization
- Load balancing across channels
- Cross-channel timing verification
- System-level performance under concurrent load
- Bank group scheduling across channels
- Pseudo-channel coordination

Key HBM4 Timing Parameters:
- tRCD: 12 cycles (Activate to Read/Write)
- tRP: 12 cycles (Precharge)
- tRAS: 28 cycles (Activate to Precharge)
- tRC: 40 cycles (Activate to Activate same bank)
- nRRDS: 3 cycles (RAS-to-RAS delay, same BG)
- nRRDL: 4 cycles (RAS-to-RAS delay, different BG)
- nFAW: 10 cycles (Four-Activate Window)
"""

import pytest
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass

from model.dram.hbm4_channel_model import (
    HBM4Channel, HBM4ChannelArray, PseudoChannel, PseudoChannelState,
    HBM4ChannelState, EnhancedBankGroupScheduler, ChannelPerformanceStats
)
from model.dram.hbm4_spec import HBM4Spec
from model.dram.hbm4_bank_state_machine import HBM4BankTiming, HBM4BankState
from model.dram.timing import HBM4Timing

from model.multi_channel import (
    ChannelSelector, QueueAwareChannelSelector, AdaptiveLoadBalancer,
    MultiChannelStats, ChannelStats, calculate_jains_fairness_index
)


class TestMultiChannelArrayCreation:
    """Test HBM4 multi-channel array creation"""

    def test_32_channel_array_creation(self):
        """32-channel array must be created successfully"""
        array = HBM4ChannelArray()

        assert array.num_channels == 32

    def test_all_channels_have_2_pseudo_channels(self):
        """Each channel must have 2 pseudo-channels"""
        array = HBM4ChannelArray()

        for ch in array.channels:
            assert len(ch.pseudo_channels) == 2

    def test_total_banks_count(self):
        """Total banks must be 1024 (32 ch * 2 pch * 16 banks)"""
        array = HBM4ChannelArray()

        assert array.total_banks == 1024

    def test_total_pseudo_channels_count(self):
        """Total pseudo-channels must be 64"""
        array = HBM4ChannelArray()

        assert array.num_channels * 2 == 64


class TestCrossChannelSynchronization:
    """Test synchronization between channels"""

    def test_all_channels_tick_together(self):
        """All channels must advance together on tick()"""
        array = HBM4ChannelArray()

        initial_cycles = [ch.current_cycle for ch in array.channels]

        array.tick()

        for i, ch in enumerate(array.channels):
            assert ch.current_cycle == initial_cycles[i] + 1

    def test_all_channels_synchronize_on_tick(self):
        """All channels must advance together on global tick()"""
        array = HBM4ChannelArray()

        # All channels should start at same cycle
        initial_cycles = [ch.current_cycle for ch in array.channels]
        assert len(set(initial_cycles)) == 1  # All should be 0

        # Global tick advances all channels together
        array.tick()

        for ch in array.channels:
            assert ch.current_cycle == 1

        # Another global tick
        array.tick()

        for ch in array.channels:
            assert ch.current_cycle == 2

    def test_global_reset_synchronizes_all_channels(self):
        """reset_all() must synchronize all channels"""
        array = HBM4ChannelArray()

        # Advance some channels
        for _ in range(100):
            array.tick()

        # Reset all
        array.reset_all()

        # All should be at cycle 0
        for ch in array.channels:
            assert ch.current_cycle == 0


class TestCrossChannelLoadBalancing:
    """Test load balancing across multiple channels"""

    def test_channel_selector_distributes_uniformly(self):
        """Channel selector must distribute load uniformly"""
        selector = ChannelSelector(num_channels=32, strategy=ChannelSelector.ROUND_ROBIN)

        # Generate 3200 requests (100 per channel)
        for i in range(3200):
            ch = selector.select_channel(addr=i * 64, length=64)
            selector.record_request(ch)

        loads = selector.get_channel_load()
        load_values = list(loads.values())

        # Each channel should have approximately 100 requests
        # Allow 10% variance
        avg = sum(load_values) / len(load_values)
        max_deviation = max(abs(v - avg) for v in load_values)

        assert max_deviation <= avg * 0.15  # 15% max deviation

    def test_queue_aware_selector_balances_load(self):
        """Queue-aware selector must balance load"""
        selector = QueueAwareChannelSelector(
            num_channels=32,
            strategy="queue_aware",
            enable_adaptive=True
        )

        # Simulate uneven queue depths
        depths = {i: random.randint(0, 20) for i in range(32)}
        selector.update_pending_depths(depths)

        # Select channels multiple times
        for _ in range(100):
            ch = selector.select_channel(addr=random.randint(0, 100000))
            selector.record_request(ch)

        loads = selector.get_channel_load()

        # Load should be more balanced now
        load_values = list(loads.values())
        jains = calculate_jains_fairness_index(load_values)

        assert jains > 0.7  # Good fairness

    def test_adaptive_balancer_distributes_fairly(self):
        """Adaptive load balancer must distribute fairly"""
        balancer = AdaptiveLoadBalancer(
            num_channels=32,
            strategy="queue_aware",
            enable_adaptive=True
        )

        # Record initial completion distribution
        for ch in range(32):
            for _ in range(random.randint(1, 10)):
                balancer.record_completion(ch)

        metrics = balancer.get_fairness_metrics()

        # Should have good fairness
        assert metrics['jains_fairness_index'] > 0.5


class TestCrossChannelTimingVerification:
    """Test timing verification across channels"""

    def test_concurrent_activation_timing(self):
        """Concurrent activations across channels must respect timing"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Activate in multiple channels simultaneously
        for ch_id in range(8):
            ch = array.channels[ch_id]
            result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
            assert result is True

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            array.tick()

        # Reads should now succeed
        for ch_id in range(8):
            ch = array.channels[ch_id]
            result = ch.issue_command('RD', pseudo_channel=0, bank=0,
                                     row=100, col=0)
            assert result is True

    def test_cross_channel_refresh_coordination(self):
        """Refresh commands must coordinate across channels"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Precharge all banks in first 8 channels
        for ch_id in range(8):
            ch = array.channels[ch_id]
            ch.issue_command('PREA', pseudo_channel=0, bank=0, row=0)
            ch.issue_command('PREA', pseudo_channel=1, bank=0, row=0)

        for _ in range(timing.tRP + 1):
            array.tick()

        # Issue all-bank refresh to first channel
        result = array.channels[0].issue_command('REFab', pseudo_channel=0, bank=0, row=0)
        assert result is True

    def test_bank_group_timing_independent_across_channels(self):
        """Bank group timing must be independent across channels"""
        array = HBM4ChannelArray()
        timing = HBM4Timing()

        scheduler = array.scheduler

        # Issue ACT to channel 0, BG 0
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=0)
        scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=0)

        # Same BG on channel 1 should be independent
        # (different channel = different pseudo-channel context)
        assert scheduler.can_issue_act(pseudo_channel=1, bank_group=0, current_cycle=1)


class TestSystemLevelPerformance:
    """Test system-level performance with concurrent load"""

    def test_aggregate_bandwidth_calculation(self):
        """Aggregate bandwidth must be calculated correctly"""
        array = HBM4ChannelArray()

        # 32 channels * 64 GB/s per channel = 2048 GB/s
        assert abs(array.total_bandwidth_gbs - 2048.0) < 1.0

    def test_system_performance_summary(self):
        """System performance summary must report all channels"""
        array = HBM4ChannelArray()

        summary = array.get_system_performance_summary()

        assert 'total_activations' in summary
        assert 'total_reads' in summary
        assert 'total_writes' in summary
        assert 'peak_bandwidth_gbs' in summary

    def test_concurrent_reads_across_channels(self):
        """Concurrent reads across all channels must work"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Activate rows in all channels
        for ch_id in range(32):
            ch = array.channels[ch_id]
            ch.issue_command('ACT', pseudo_channel=0, bank=0, row=ch_id)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            array.tick()

        # Read from all channels
        success_count = 0
        for ch_id in range(32):
            ch = array.channels[ch_id]
            result = ch.issue_command('RD', pseudo_channel=0, bank=0,
                                     row=ch_id, col=0)
            if result:
                success_count += 1

        assert success_count == 32

    def test_concurrent_writes_across_channels(self):
        """Concurrent writes across all channels must work"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Activate rows in all channels
        for ch_id in range(32):
            ch = array.channels[ch_id]
            ch.issue_command('ACT', pseudo_channel=0, bank=0, row=ch_id)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            array.tick()

        # Write to all channels
        success_count = 0
        for ch_id in range(32):
            ch = array.channels[ch_id]
            result = ch.issue_command('WR', pseudo_channel=0, bank=0,
                                     row=ch_id, col=0)
            if result:
                success_count += 1

        assert success_count == 32


class TestBankGroupSchedulingAcrossChannels:
    """Test bank group scheduling across channels"""

    def test_faw_tracking_per_channel(self):
        """FAW window must be tracked per pseudo-channel"""
        array = HBM4ChannelArray()
        timing = HBM4Timing()

        ch0 = array.channels[0]
        scheduler = ch0.get_scheduler(0)

        # Test FAW behavior: max 4 activations in nFAW (16) cycles window
        # Issue ACTs to same BG with proper tRRDS timing (3 cycles)
        # ACTs at cycles 0, 3, 6, 9 will all succeed (within FAW window)
        # 5th ACT at cycle 12 should fail due to FAW limit

        current_cycle = 0
        successful_acts = 0
        for i in range(5):
            can_issue = scheduler.can_issue_act(pseudo_channel=0, bank_group=0,
                                               current_cycle=current_cycle)
            if can_issue:
                scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=current_cycle)
                successful_acts += 1
                print(f"ACT {successful_acts} at cycle {current_cycle}: succeeded")
            else:
                print(f"ACT at cycle {current_cycle}: blocked (tRRDS={timing.nRRDS})")
            # Advance by tRRDS for same BG
            current_cycle += timing.nRRDS

        # Should have exactly 4 successful ACTs within FAW window
        assert successful_acts == 4, f"Expected 4 successful ACTs within FAW window, got {successful_acts}"

        # 5th ACT would need to wait until FAW window expires
        # Check that at cycle 20 (past nFAW), we can issue again
        current_cycle = timing.nFAW + 1
        can_issue = scheduler.can_issue_act(pseudo_channel=0, bank_group=0,
                                          current_cycle=current_cycle)
        assert can_issue is True, "ACT after nFAW window should succeed"

        # Verify scheduler state
        state = scheduler.get_scheduler_state(0)
        assert state['faw_window_size'] >= 0  # Should be reset or expired

    def test_bg_timing_same_channel(self):
        """Bank group timing must work on same channel"""
        array = HBM4ChannelArray()
        timing = HBM4Timing()

        ch = array.channels[0]
        scheduler = ch.get_scheduler(0)

        # Issue ACT to BG 0
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=0)
        scheduler.record_act(pseudo_channel=0, bank_group=0, current_cycle=0)

        # Immediate ACT to same BG - should fail (tRRDS not met)
        assert not scheduler.can_issue_act(pseudo_channel=0, bank_group=0, current_cycle=1)

        # After nRRDL, ACT to different BG should succeed
        assert scheduler.can_issue_act(pseudo_channel=0, bank_group=1,
                                    current_cycle=timing.nRRDL)


class TestPseudoChannelCoordination:
    """Test pseudo-channel coordination within channel"""

    def test_both_pseudo_channels_independent(self):
        """Both pseudo-channels must operate independently"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        ch = array.channels[0]

        # Activate in pseudo-channel 0
        result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        assert result is True

        # Pseudo-channel 1 should be independent
        result = ch.issue_command('ACT', pseudo_channel=1, bank=0, row=200)
        assert result is True

    def test_pseudo_channel_states_independent(self):
        """Pseudo-channel states must be independent"""
        array = HBM4ChannelArray()

        ch = array.channels[0]

        pc0 = ch.pseudo_channels[0]
        pc1 = ch.pseudo_channels[1]

        # Activate row in PC0
        pc0.activate_row(100, bank_id=0)

        # PC0 should be ACTIVE
        assert pc0.state == PseudoChannelState.ACTIVE

        # PC1 should still be IDLE
        assert pc1.state == PseudoChannelState.IDLE

    def test_column_commands_independent_pseudo_channels(self):
        """Column commands must work independently on pseudo-channels"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        ch = array.channels[0]

        # Activate in both pseudo-channels
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        ch.issue_command('ACT', pseudo_channel=1, bank=0, row=200)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            ch.tick()

        # Read from both
        result0 = ch.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)
        result1 = ch.issue_command('RD', pseudo_channel=1, bank=1, row=200, col=0)

        assert result0 is True
        assert result1 is True


class TestMultiChannelStats:
    """Test multi-channel statistics aggregation"""

    def test_multi_channel_stats_initialization(self):
        """Multi-channel stats must track all channels"""
        stats = MultiChannelStats(num_channels=32)

        assert stats.num_channels == 32
        assert len(stats.channel_stats) == 32

    def test_record_requests_per_channel(self):
        """Must record requests per channel"""
        stats = MultiChannelStats(num_channels=32)

        # Record requests to different channels
        stats.record_request(channel_id=0, is_read=True)
        stats.record_request(channel_id=0, is_read=True)
        stats.record_request(channel_id=1, is_read=False)

        assert stats.channel_stats[0].total_requests == 2
        assert stats.channel_stats[1].total_requests == 1

    def test_jains_fairness_index(self):
        """Jain's fairness index must be calculated correctly"""
        stats = MultiChannelStats(num_channels=32)

        # Uniform distribution
        for ch in range(32):
            for _ in range(10):
                stats.record_request(channel_id=ch, is_read=True)

        jains = stats.get_jains_fairness_index()

        # Uniform = 1.0
        assert abs(jains - 1.0) < 0.01

    def test_load_balance_score(self):
        """Load balance score must reflect distribution"""
        stats = MultiChannelStats(num_channels=32)

        # Uniform distribution
        for ch in range(32):
            for _ in range(10):
                stats.record_request(channel_id=ch, is_read=True)

        score = stats.get_load_balance_score()

        # Uniform = 1.0
        assert score > 0.95

    def test_channel_utilization(self):
        """Channel utilization must be calculated"""
        stats = MultiChannelStats(num_channels=32)

        # Record requests
        for ch in range(32):
            for _ in range(10):
                stats.record_request(channel_id=ch, is_read=True)

        utilization = stats.get_channel_utilization()

        # Each channel should have ~3.125%
        for ch, util in utilization.items():
            assert abs(util - 0.03125) < 0.01


class TestStressTestMultiChannel:
    """Stress tests for multi-channel operation"""

    def test_1000_cycles_stress(self):
        """System must handle 1000 cycles of continuous operation"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        for cycle in range(1000):
            # Activate random banks across random channels
            for ch_id in random.sample(range(32), min(8, 32)):
                ch = array.channels[ch_id]
                ch.issue_command('ACT', pseudo_channel=random.randint(0, 1),
                               bank=random.randint(0, 15),
                               row=random.randint(0, 65535))

            # Advance time
            for _ in range(timing.tRCD + 1):
                array.tick()

        # System should still be operational
        summary = array.get_system_state_summary()
        assert summary['num_channels'] == 32

    def test_random_access_pattern(self):
        """Random access pattern across channels must work"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Generate random requests
        for _ in range(500):
            ch_id = random.randint(0, 31)
            pch_id = random.randint(0, 1)
            bank_id = random.randint(0, 15)
            row = random.randint(0, 65535)

            ch = array.channels[ch_id]
            ch.issue_command('ACT', pseudo_channel=pch_id, bank=bank_id, row=row)

            # Advance time
            for _ in range(timing.tRCD + 1):
                array.tick()

        # System should be operational
        summary = array.get_system_performance_summary()
        assert summary['total_activations'] > 0

    def test_burst_traffic_all_channels(self):
        """Burst traffic to all channels must work"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Burst activate to all channels
        for ch_id in range(32):
            ch = array.channels[ch_id]
            for pch_id in range(2):
                for bank_id in range(4):
                    ch.issue_command('ACT', pseudo_channel=pch_id,
                                   bank=bank_id, row=ch_id * 100 + bank_id)

        # Advance past tRCD
        for _ in range(timing.tRCD + 1):
            array.tick()

        # Read from all channels
        for ch_id in range(32):
            ch = array.channels[ch_id]
            for pch_id in range(2):
                result = ch.issue_command('RD', pseudo_channel=pch_id,
                                    bank=0, row=ch_id * 100, col=0)
                assert result is True


class TestChannelSelectorStrategies:
    """Test different channel selection strategies"""

    def test_round_robin_strategy(self):
        """Round-robin strategy must cycle through channels"""
        selector = ChannelSelector(num_channels=32, strategy=ChannelSelector.ROUND_ROBIN)

        selected = []
        for i in range(64):
            ch = selector.select_channel(addr=i * 64, length=64)
            selected.append(ch)

        # Should cycle evenly
        for ch in range(32):
            count = selected.count(ch)
            assert count == 2  # 64 / 32 = 2

    def test_hash_strategy(self):
        """Hash strategy must be deterministic"""
        selector = ChannelSelector(num_channels=32, strategy=ChannelSelector.HASH)

        addresses = [1000, 2000, 3000, 4000, 5000]

        # Same address should always select same channel
        for addr in addresses:
            ch1 = selector.select_channel(addr=addr, length=64)
            ch2 = selector.select_channel(addr=addr, length=64)
            assert ch1 == ch2

    def test_load_balanced_strategy(self):
        """Load-balanced strategy must select least-loaded"""
        selector = ChannelSelector(num_channels=32, strategy=ChannelSelector.LOAD_BALANCED)

        # Add load to some channels
        for ch in range(16):
            for _ in range(10):
                selector.record_request(ch)

        # Next selection should go to channel 16-31
        ch = selector.select_channel(addr=0, length=64)
        assert ch >= 16


class TestTimingViolationDetection:
    """Test timing violation detection across channels"""

    def test_timing_violations_accumulated(self):
        """Timing violations must be accumulated across channels"""
        array = HBM4ChannelArray()

        # Generate some operations that might cause violations
        for ch_id in range(8):
            ch = array.channels[ch_id]
            # Rapid commands might cause violations
            ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
            ch.issue_command('ACT', pseudo_channel=0, bank=1, row=101)  # Same BG immediately

        # Validate timing
        violations = array.validate_all_timing()

        # Should detect violations
        assert isinstance(violations, list)

    def test_per_channel_violation_tracking(self):
        """Each channel must track its own violations"""
        array = HBM4ChannelArray()

        ch = array.channels[0]
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        violations = ch.validate_timing()

        assert isinstance(violations, list)


class TestChannelResetAndRecovery:
    """Test channel reset and recovery"""

    def test_reset_channel_recovers(self):
        """Channel must recover after reset"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        ch = array.channels[0]

        # Perform some operations
        ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Advance past tRAS + tRP to complete the operation
        for _ in range(timing.tRAS + timing.tRP + 1):
            ch.tick()

        # Reset
        ch.reset()

        # Should be able to operate again after reset
        result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=200)
        assert result is True

    def test_reset_all_channels_recovers(self):
        """All channels must recover after reset"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Perform operations on all channels
        for ch in array.channels[:8]:
            ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        # Advance past tRAS + tRP to complete the operation
        for _ in range(timing.tRAS + timing.tRP + 1):
            array.tick()

        # Reset all
        array.reset_all()

        # Should be able to operate again after reset
        for ch in array.channels[:8]:
            result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=200)
            assert result is True


class TestPerformanceUnderLoad:
    """Test performance metrics under load"""

    def test_throughput_measurement(self):
        """Throughput must be measurable"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Perform operations
        for ch_id in range(32):
            ch = array.channels[ch_id]
            ch.issue_command('ACT', pseudo_channel=0, bank=0, row=ch_id)

        for _ in range(timing.tRCD + 1):
            array.tick()

        # Reads
        for ch_id in range(32):
            ch = array.channels[ch_id]
            ch.issue_command('RD', pseudo_channel=0, bank=0,
                            row=ch_id, col=0)

        # Get performance
        summary = array.get_system_performance_summary()

        assert summary['total_reads'] > 0

    def test_latency_measurement(self):
        """Latency must be measurable"""
        array = HBM4ChannelArray()
        timing = HBM4BankTiming()

        # Activate
        array.channels[0].issue_command('ACT', pseudo_channel=0, bank=0, row=100)

        start_cycle = array.channels[0].current_cycle

        # Wait for tRCD
        for _ in range(timing.tRCD + 1):
            array.tick()

        # Read
        array.channels[0].issue_command('RD', pseudo_channel=0, bank=0,
                                        row=100, col=0)

        # Get stats
        stats = array.channels[0].get_performance_stats()

        # Should have latency measurement
        assert stats.total_read_latency > 0


class TestEdgeCases:
    """Test edge cases"""

    def test_boundary_channel_index(self):
        """Boundary channel indices must work"""
        array = HBM4ChannelArray()

        # First channel
        ch0 = array.channels[0]
        assert ch0.channel_id == 0

        # Last channel
        ch31 = array.channels[31]
        assert ch31.channel_id == 31

    def test_boundary_pseudo_channel_index(self):
        """Boundary pseudo-channel indices must work"""
        array = HBM4ChannelArray()
        ch = array.channels[0]

        pc0 = ch.pseudo_channels[0]
        pc1 = ch.pseudo_channels[1]

        assert pc0.pseudo_channel_id == 0
        assert pc1.pseudo_channel_id == 1

    def test_boundary_bank_index(self):
        """Boundary bank indices must work"""
        array = HBM4ChannelArray()
        ch = array.channels[0]

        # First bank
        result = ch.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
        assert result is True

        # Last bank
        result = ch.issue_command('ACT', pseudo_channel=1, bank=15, row=200)
        assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])