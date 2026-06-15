"""
HBM4 Logic Base Die Integration Tests

Comprehensive integration tests for HBM4 Logic Base Die model.
Tests end-to-end functionality across all components.

Test Categories:
1. Module Integration: PAM3 + Channel Timing + Logic Base Die
2. End-to-End Command Flow: ACT -> RD/WR -> PRE
3. 32-Channel Simultaneous Operation
4. Error Injection and Recovery
5. Performance Benchmarks
"""

import pytest
import time
from typing import List, Dict

# Import HBM4 modules
from model.dram import (
    HBM4LogicBaseDie,
    HBM4PAM3Encoder,
    HBM4TimingManager,
    PAM3SignalModel,
    TimingParameters,
    ChannelState,
    IndependentChannelTiming,
)


class TestModuleIntegration:
    """Test integration between HBM4 modules"""

    def test_logic_base_die_with_pam3(self):
        """Test Logic Base Die with PAM3 encoding"""
        # Create LBD with PAM3 enabled
        lbd = HBM4LogicBaseDie()
        assert lbd.config.pam3_enabled is True

        # Initialize
        lbd.initialize()
        for _ in range(50):
            lbd.tick()

        # Process command
        ok, msg = lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        assert ok

        # Verify PAM3 encoder is available
        assert lbd.pam3_encoder is not None

    def test_timing_manager_with_logic_base_die(self):
        """Test Timing Manager integration"""
        manager = HBM4TimingManager(num_channels=32)
        lbd = HBM4LogicBaseDie()

        # Both should use compatible timing parameters
        lbd.initialize()

        for _ in range(100):
            lbd.tick()
            manager.tick()

        # Verify both are advancing cycles
        assert lbd.cycle > 0
        assert all(ch.local_cycle > 0 for ch in manager.channels)

    def test_pam3_encoder_directly(self):
        """Test PAM3 encoder as standalone"""
        encoder = HBM4PAM3Encoder()

        # Encode command
        cmd = 0x555
        symbols = encoder.encode_command(cmd, 10)

        # Should produce 5 symbols (10 bits / 2 bits per symbol)
        assert len(symbols) == 5

        # Verify levels
        levels = [s.level for s in symbols]
        assert all(l in [-1, 0, 1] for l in levels)


class TestEndToEndCommandFlow:
    """Test complete command sequences"""

    @pytest.fixture
    def lbd(self):
        """Create initialized LBD"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        for _ in range(100):
            lbd.tick()
        return lbd

    def test_activate_flow(self, lbd):
        """Test ACTIVATE command flow"""
        ok, msg = lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        assert ok

        state = lbd.get_channel_state(0)
        assert state['open_row'] == 0x1000

    def test_read_flow(self, lbd):
        """Test READ command flow"""
        # Open row first
        lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        for _ in range(10):
            lbd.tick()

        # Issue read
        ok, msg = lbd.process_command(channel_id=0, command='RD', address=0x1000)
        assert ok

    def test_write_flow(self, lbd):
        """Test WRITE command flow"""
        # Open row first
        lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        for _ in range(10):
            lbd.tick()

        # Issue write
        ok, msg = lbd.process_command(
            channel_id=0, command='WR', address=0x1000, data=0xDEADBEEF
        )
        assert ok

    def test_precharge_flow(self, lbd):
        """Test PRECHARGE command flow"""
        # Open row
        lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        for _ in range(25):
            lbd.tick()

        # Precharge
        ok, msg = lbd.process_command(channel_id=0, command='PRE', address=0x1000)
        assert ok

        state = lbd.get_channel_state(0)
        assert state['open_row'] is None

    def test_refresh_flow(self, lbd):
        """Test REFRESH command flow"""
        ok, msg = lbd.process_command(channel_id=0, command='REF', address=0)
        assert ok

    def test_full_sequence(self, lbd):
        """Test complete ACT -> RD -> PRE sequence"""
        # ACT
        ok, msg = lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        assert ok

        # Wait for tRCD
        for _ in range(10):
            lbd.tick()

        # RD
        ok, msg = lbd.process_command(channel_id=0, command='RD', address=0x1000)
        assert ok

        # Wait for data return
        for _ in range(10):
            lbd.tick()

        # PRE
        ok, msg = lbd.process_command(channel_id=0, command='PRE', address=0x1000)
        assert ok


class Test32ChannelOperation:
    """Test simultaneous 32-channel operation"""

    @pytest.fixture
    def manager(self):
        """Create timing manager"""
        return HBM4TimingManager(num_channels=32)

    def test_all_channels_initialize(self, manager):
        """Test all 32 channels initialize correctly"""
        assert len(manager.channels) == 32

        for ch in manager.channels:
            assert ch.channel_id in range(32)
            assert ch.local_cycle == 0

    def test_all_channels_tick(self, manager):
        """Test all channels advance together"""
        manager.tick()

        for ch in manager.channels:
            assert ch.local_cycle == 1

    def test_parallel_activations(self, manager):
        """Test activating different banks in all channels"""
        for ch in range(32):
            timing = manager.get_channel_timing(ch)
            success, msg, data = timing.execute_with_independent_timing(
                'ACT', bank=0, row=0x1000 + ch
            )
            assert success
            manager.tick()

        # Verify all have correct rows open
        for ch in range(32):
            timing = manager.get_channel_timing(ch)
            assert timing.bank_states[0].row_id == 0x1000 + ch

    def test_channel_independence(self, manager):
        """Test channels operate independently"""
        # Activate different rows in different channels
        for ch in range(32):
            timing = manager.get_channel_timing(ch)
            timing.execute_with_independent_timing('ACT', bank=0, row=ch * 0x100)
            manager.tick()

        # Modify channel 0
        timing0 = manager.get_channel_timing(0)
        timing0.execute_with_independent_timing('PRE', bank=0)
        manager.tick()

        # Channel 0 should be closed, others still open
        assert not manager.channels[0].bank_states[0].is_open
        for ch in range(1, 32):
            assert manager.channels[ch].bank_states[0].is_open


class TestErrorInjection:
    """Test error handling and recovery"""

    @pytest.fixture
    def lbd(self):
        """Create initialized LBD"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        for _ in range(100):
            lbd.tick()
        return lbd

    def test_invalid_channel(self, lbd):
        """Test handling of invalid channel ID"""
        ok, msg = lbd.process_command(channel_id=32, command='ACT', address=0x1000)
        assert not ok
        assert "Invalid channel" in msg

    def test_timing_violation(self, lbd):
        """Test timing violation detection"""
        # Two ACTs without tRC delay
        ok, msg = lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        assert ok

        # Immediate second ACT should fail
        ok, msg = lbd.process_command(channel_id=0, command='ACT', address=0x2000)
        assert not ok
        assert "tRC" in msg or "timing" in msg.lower()

    def test_bank_not_active_read(self, lbd):
        """Test read without bank active"""
        ok, msg = lbd.process_command(channel_id=0, command='RD', address=0x1000)
        assert not ok


class TestPerformanceBenchmarks:
    """Performance and scalability tests"""

    def test_large_cycle_count(self):
        """Test running many cycles efficiently"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()

        start = time.time()

        # Run 10000 cycles
        for _ in range(10000):
            lbd.tick()

        duration = time.time() - start

        # Should complete in reasonable time (< 5 seconds)
        assert duration < 5.0
        assert lbd.cycle == 10000

    def test_many_channels_access(self):
        """Test accessing all 32 channels"""
        manager = HBM4TimingManager(num_channels=32)

        start = time.time()

        # Activate all channels
        for ch in range(32):
            timing = manager.get_channel_timing(ch)
            timing.execute_with_independent_timing('ACT', bank=0, row=0x1000)

        for _ in range(10):
            manager.tick()

        duration = time.time() - start

        # Should be fast (< 1 second)
        assert duration < 1.0

    def test_pam3_high_throughput(self):
        """Test PAM3 encoding throughput"""
        encoder = HBM4PAM3Encoder()

        start = time.time()

        # Encode many bursts
        for _ in range(1000):
            encoder.encode_data_burst(0xDEADBEEF, dq_width=128)

        duration = time.time() - start

        # Should be fast
        assert duration < 1.0


class TestConfigurationOptions:
    """Test different configuration options"""

    def test_pam3_disabled(self):
        """Test with PAM3 disabled"""
        from model.dram.logic_base_die import LogicBaseDieConfig

        config = LogicBaseDieConfig(pam3_enabled=False)
        lbd = HBM4LogicBaseDie(config=config)

        assert lbd.config.pam3_enabled is False
        assert lbd.pam3_encoder is None

    def test_ecc_disabled(self):
        """Test with ECC disabled"""
        from model.dram.logic_base_die import LogicBaseDieConfig

        config = LogicBaseDieConfig(ecc_enabled=False)
        lbd = HBM4LogicBaseDie(config=config)

        assert lbd.config.ecc_enabled is False

    def test_custom_timing_params(self):
        """Test with custom timing parameters"""
        params = TimingParameters(nCL=10, nCWL=5)
        timing = IndependentChannelTiming(channel_id=0, params=params)

        assert timing.params.nCL == 10
        assert timing.params.nCWL == 5


class TestStatistics:
    """Test statistics and reporting"""

    def test_lbd_stats(self):
        """Test LBD statistics collection"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()

        for _ in range(100):
            lbd.tick()

        lbd.process_command(channel_id=0, command='ACT', address=0x1000)

        stats = lbd.get_stats()

        assert 'global_cycle' in stats
        assert 'initialized' in stats
        assert 'total_commands' in stats
        assert stats['total_commands'] >= 1

    def test_timing_stats(self):
        """Test timing statistics"""
        manager = HBM4TimingManager(num_channels=32)

        for ch in range(32):
            timing = manager.get_channel_timing(ch)
            timing.execute_with_independent_timing('ACT', bank=0, row=ch)

        stats = manager.get_all_timing_status()
        assert len(stats) == 32

    def test_lane_repair_stats(self):
        """Test lane repair statistics"""
        lbd = HBM4LogicBaseDie()

        stats = lbd.get_lane_repair_stats()
        assert 'total_channels' in stats
        assert stats['total_channels'] == 32


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])