"""
Tests for HBM4 Logic Base Die Core Module

Comprehensive tests for Logic Base Die model including:
1. Initialization and configuration
2. DFI 5.0 interface integration
3. Command buffer functionality
4. Bank state tracking
5. Per-channel operation
6. Statistics and reporting
"""

import pytest
from typing import Dict, List

from model.dram.logic_base_die import (
    HBM4LogicBaseDie,
    LogicBaseDieConfig,
    ChannelState,
    ChannelContext,
    CommandBuffer,
)
from model.dram.bank_state_machine import BankStateEnum
from model.dram.dfi_interface import (
    DFICommand,
    DFIRequest,
    DFILowPowerState,
)


class TestLogicBaseDieConfig:
    """Test Logic Base Die configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = LogicBaseDieConfig()
        assert config.num_channels == 32
        assert config.channel_width == 64
        assert config.pam3_enabled is True
        assert config.ecc_enabled is True
        assert config.crc_enabled is True
        assert config.command_buffer_depth == 64
        assert config.banks_per_channel == 16
        assert config.pseudo_channels_per_channel == 2

    def test_custom_config(self):
        """Test custom configuration"""
        config = LogicBaseDieConfig(
            num_channels=16,
            pam3_enabled=False,
            ecc_enabled=False,
            command_buffer_depth=128,
        )
        assert config.num_channels == 16
        assert config.pam3_enabled is False
        assert config.ecc_enabled is False
        assert config.command_buffer_depth == 128


class TestLogicBaseDieInitialization:
    """Test Logic Base Die initialization"""

    def test_default_initialization(self):
        """Test default initialization"""
        lbd = HBM4LogicBaseDie()
        assert lbd.config.num_channels == 32
        assert lbd.spec is not None
        assert lbd.dfi is not None
        assert lbd.command_buffer is not None
        assert len(lbd._channels) == 32

    def test_initialized_flag(self):
        """Test initialized flag starts False"""
        lbd = HBM4LogicBaseDie()
        assert lbd.is_initialized is False

    def test_initialize_method(self):
        """Test initialize() method"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        assert lbd.is_initialized is True

    def test_pam3_encoder_enabled(self):
        """Test PAM3 encoder is created when enabled"""
        lbd = HBM4LogicBaseDie()
        assert lbd.pam3_encoder is not None

    def test_pam3_encoder_disabled(self):
        """Test PAM3 encoder is None when disabled"""
        config = LogicBaseDieConfig(pam3_enabled=False)
        lbd = HBM4LogicBaseDie(config=config)
        assert lbd.pam3_encoder is None

    def test_bank_state_machines_initialized(self):
        """Test bank state machines are initialized"""
        lbd = HBM4LogicBaseDie()
        # 32 channels × 32 banks (16 × 2 pseudo-channels)
        assert len(lbd._bank_state_machines) == 32
        for ch in range(32):
            assert len(lbd._bank_state_machines[ch]) == 32


class TestCommandBuffer:
    """Test command buffer functionality"""

    def test_default_depth(self):
        """Test default buffer depth"""
        buf = CommandBuffer()
        assert buf.depth == 64

    def test_custom_depth(self):
        """Test custom buffer depth"""
        buf = CommandBuffer(depth=32)
        assert buf.depth == 32

    def test_enqueue(self):
        """Test enqueueing commands"""
        buf = CommandBuffer(depth=10)
        cmd_id = buf.enqueue('ACT', channel=0, address=0x1000)
        assert cmd_id >= 0
        assert buf.size == 1

    def test_enqueue_full(self):
        """Test enqueue when buffer full"""
        buf = CommandBuffer(depth=2)
        buf.enqueue('ACT', channel=0, address=0x1000)
        buf.enqueue('PRE', channel=0, address=0x1000)
        cmd_id = buf.enqueue('RD', channel=0, address=0x1000)
        assert cmd_id == -1
        assert buf.is_full

    def test_dequeue(self):
        """Test dequeuing commands"""
        buf = CommandBuffer()
        buf.enqueue('ACT', channel=0, address=0x1000)
        buf.enqueue('RD', channel=0, address=0x2000)

        cmd = buf.dequeue()
        assert cmd is not None
        assert cmd['command'] == 'ACT'
        assert buf.size == 1

    def test_dequeue_empty(self):
        """Test dequeue from empty buffer"""
        buf = CommandBuffer()
        cmd = buf.dequeue()
        assert cmd is None

    def test_peek(self):
        """Test peeking at next command"""
        buf = CommandBuffer()
        buf.enqueue('ACT', channel=0, address=0x1000)
        buf.enqueue('RD', channel=0, address=0x2000)

        cmd = buf.peek()
        assert cmd is not None
        assert cmd['command'] == 'ACT'
        assert buf.size == 2  # Size unchanged

    def test_clear(self):
        """Test clearing buffer"""
        buf = CommandBuffer()
        buf.enqueue('ACT', channel=0, address=0x1000)
        buf.enqueue('RD', channel=0, address=0x2000)

        buf.clear()
        assert buf.is_empty
        assert buf.size == 0

    def test_available_capacity(self):
        """Test available capacity calculation"""
        buf = CommandBuffer(depth=10)
        buf.enqueue('ACT', channel=0, address=0x1000)
        buf.enqueue('RD', channel=0, address=0x2000)

        assert buf.available_capacity == 8

    def test_stats(self):
        """Test buffer statistics"""
        buf = CommandBuffer(depth=10)
        buf.enqueue('ACT', channel=0, address=0x1000)
        buf.dequeue()

        stats = buf.get_stats()
        assert stats['current_size'] == 0
        assert stats['max_depth'] == 10
        assert stats['total_commands_completed'] >= 0


class TestDFIInterfaceIntegration:
    """Test DFI 5.0 interface integration"""

    def test_dfi_interface_exists(self):
        """Test DFI interface is initialized"""
        lbd = HBM4LogicBaseDie()
        assert lbd.dfi is not None

    def test_submit_dfi_act(self):
        """Test submitting ACT command via DFI"""
        lbd = HBM4LogicBaseDie()
        success = lbd.submit_dfi_act(channel=0, bank=0, row=0x1000)
        assert success
        assert lbd.dfi_pending_count == 1

    def test_submit_dfi_pre(self):
        """Test submitting PRE command via DFI"""
        lbd = HBM4LogicBaseDie()
        lbd.submit_dfi_act(channel=0, bank=0, row=0x1000)
        success = lbd.submit_dfi_pre(channel=0, bank=0)
        assert success

    def test_submit_dfi_read(self):
        """Test submitting READ command via DFI"""
        lbd = HBM4LogicBaseDie()
        success = lbd.submit_dfi_read(channel=0, bank=0, column=0x100)
        assert success
        assert lbd.dfi_pending_count == 1

    def test_submit_dfi_write(self):
        """Test submitting WRITE command via DFI"""
        lbd = HBM4LogicBaseDie()
        success = lbd.submit_dfi_write(channel=0, bank=0, column=0x100)
        assert success

    def test_submit_dfi_refresh(self):
        """Test submitting REFRESH command via DFI"""
        lbd = HBM4LogicBaseDie()
        success = lbd.submit_dfi_refresh(channel=0)
        assert success

    def test_get_next_dfi_request(self):
        """Test getting next DFI request"""
        lbd = HBM4LogicBaseDie()
        lbd.submit_dfi_act(channel=0, bank=0, row=0x1000)
        lbd.submit_dfi_read(channel=0, bank=0, column=0x100)

        request = lbd.get_next_dfi_request()
        assert request is not None
        assert request.command == DFICommand.ACT
        assert lbd.dfi_pending_count == 1

    def test_peek_dfi_request(self):
        """Test peeking at DFI request"""
        lbd = HBM4LogicBaseDie()
        lbd.submit_dfi_act(channel=0, bank=0, row=0x1000)

        request = lbd.peek_dfi_request()
        assert request is not None
        assert lbd.dfi_pending_count == 1  # Unchanged

    def test_dfi_is_ready(self):
        """Test DFI interface readiness"""
        lbd = HBM4LogicBaseDie()
        assert lbd.dfi_is_ready is True

    def test_get_dfi_signals(self):
        """Test getting DFI signal states"""
        lbd = HBM4LogicBaseDie()
        signals = lbd.get_dfi_signals()
        # DFI get_dfi_signals returns DFISignals dataclass
        assert hasattr(signals, 'lp_state')
        assert hasattr(signals, 'phy_ready')


class TestBankStateTracking:
    """Test bank state tracking functionality"""

    def test_get_bank_state(self):
        """Test getting bank state"""
        lbd = HBM4LogicBaseDie()
        state = lbd.get_bank_state(channel_id=0, bank_id=0)
        assert state == BankStateEnum.IDLE

    def test_get_all_bank_states(self):
        """Test getting all bank states in a channel"""
        lbd = HBM4LogicBaseDie()
        states = lbd.get_all_bank_states(channel_id=0)
        assert len(states) == 32
        assert all(s == BankStateEnum.IDLE for s in states.values())

    def test_can_activate_bank(self):
        """Test checking if bank can be activated"""
        lbd = HBM4LogicBaseDie()
        can_activate = lbd.can_activate_bank(channel_id=0, bank_id=0)
        assert can_activate is True

    def test_activate_bank(self):
        """Test activating a bank"""
        lbd = HBM4LogicBaseDie()
        success = lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)
        assert success

        state = lbd.get_bank_state(channel_id=0, bank_id=0)
        assert state == BankStateEnum.ACTIVE

    def test_can_precharge_bank(self):
        """Test checking if bank can be precharged"""
        lbd = HBM4LogicBaseDie()
        # Cannot precharge idle bank
        can_pre = lbd.can_precharge_bank(channel_id=0, bank_id=0)
        assert can_pre is False

        # Activate first
        lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)
        # Wait for tRAS (HBM3Timing.tRAS = 42 cycles)
        for _ in range(50):
            lbd.tick()

        can_pre = lbd.can_precharge_bank(channel_id=0, bank_id=0)
        assert can_pre is True

    def test_precharge_bank(self):
        """Test precharging a bank"""
        lbd = HBM4LogicBaseDie()
        lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)
        # Wait for tRAS
        for _ in range(50):
            lbd.tick()

        success = lbd.precharge_bank(channel_id=0, bank_id=0)
        assert success

        state = lbd.get_bank_state(channel_id=0, bank_id=0)
        assert state == BankStateEnum.IDLE

    def test_can_read_bank(self):
        """Test checking if read can be issued"""
        lbd = HBM4LogicBaseDie()
        can_read = lbd.can_read_bank(channel_id=0, bank_id=0)
        assert can_read is False  # Bank not active

        lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)
        # Wait for tRCD (HBM3Timing.tRCD = 16 cycles)
        for _ in range(20):
            lbd.tick()

        can_read = lbd.can_read_bank(channel_id=0, bank_id=0)
        assert can_read is True

    def test_read_bank(self):
        """Test issuing a read to a bank"""
        lbd = HBM4LogicBaseDie()
        lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)
        for _ in range(20):
            lbd.tick()

        success = lbd.read_bank(channel_id=0, bank_id=0)
        assert success

    def test_can_write_bank(self):
        """Test checking if write can be issued"""
        lbd = HBM4LogicBaseDie()
        can_write = lbd.can_write_bank(channel_id=0, bank_id=0)
        assert can_write is False

        lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)
        # Wait for tRCD (HBM3Timing.tRCD = 16 cycles)
        for _ in range(20):
            lbd.tick()

        can_write = lbd.can_write_bank(channel_id=0, bank_id=0)
        assert can_write is True

    def test_write_bank(self):
        """Test issuing a write to a bank"""
        lbd = HBM4LogicBaseDie()
        lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)
        for _ in range(20):
            lbd.tick()

        success = lbd.write_bank(channel_id=0, bank_id=0)
        assert success

    def test_refresh_bank(self):
        """Test refreshing a bank"""
        lbd = HBM4LogicBaseDie()
        success = lbd.refresh_bank(channel_id=0, bank_id=0)
        assert success

        ctx = lbd._channels[0]
        assert ctx.state == ChannelState.MAINTENANCE

    def test_is_row_hit(self):
        """Test row hit detection"""
        lbd = HBM4LogicBaseDie()
        lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)

        assert lbd.is_row_hit(channel_id=0, bank_id=0, row=0x1000) is True
        assert lbd.is_row_hit(channel_id=0, bank_id=0, row=0x2000) is False

    def test_invalid_channel_bank(self):
        """Test operations with invalid channel/bank"""
        lbd = HBM4LogicBaseDie()
        state = lbd.get_bank_state(channel_id=32, bank_id=0)
        assert state is None

        can_activate = lbd.can_activate_bank(channel_id=32, bank_id=0)
        assert can_activate is False

        success = lbd.activate_bank(channel_id=32, bank_id=0, row=0x1000)
        assert success is False


class TestCommandBufferIntegration:
    """Test command buffer integration with Logic Base Die"""

    def test_enqueue_command(self):
        """Test enqueueing commands via LBD"""
        lbd = HBM4LogicBaseDie()
        cmd_id = lbd.enqueue_command('ACT', channel=0, address=0x1000)
        assert cmd_id >= 0
        assert lbd.command_buffer_size == 1

    def test_dequeue_command(self):
        """Test dequeuing commands via LBD"""
        lbd = HBM4LogicBaseDie()
        lbd.enqueue_command('ACT', channel=0, address=0x1000)
        lbd.enqueue_command('RD', channel=0, address=0x2000)

        cmd = lbd.dequeue_command()
        assert cmd is not None
        assert cmd['command'] == 'ACT'
        assert lbd.command_buffer_size == 1

    def test_command_buffer_full(self):
        """Test command buffer full detection"""
        lbd = HBM4LogicBaseDie(config=LogicBaseDieConfig(command_buffer_depth=2))
        lbd.enqueue_command('ACT', channel=0, address=0x1000)
        lbd.enqueue_command('RD', channel=0, address=0x2000)

        assert lbd.command_buffer_full is True

    def test_get_command_buffer_stats(self):
        """Test getting command buffer statistics"""
        lbd = HBM4LogicBaseDie()
        lbd.enqueue_command('ACT', channel=0, address=0x1000)

        stats = lbd.get_command_buffer_stats()
        assert 'current_size' in stats
        assert 'max_depth' in stats


class TestChannelState:
    """Test per-channel state management"""

    def test_get_channel_state(self):
        """Test getting channel state"""
        lbd = HBM4LogicBaseDie()
        state = lbd.get_channel_state(channel_id=0)
        assert state is not None
        assert state['channel_id'] == 0
        assert state['state'] == ChannelState.IDLE.value

    def test_get_all_channel_states(self):
        """Test getting all channel states"""
        lbd = HBM4LogicBaseDie()
        states = lbd.get_all_channel_states()
        assert len(states) == 32

    def test_invalid_channel_state(self):
        """Test getting state for invalid channel"""
        lbd = HBM4LogicBaseDie()
        state = lbd.get_channel_state(channel_id=32)
        assert state is None


class TestTickAndCycle:
    """Test tick and cycle management"""

    def test_cycle_starts_at_zero(self):
        """Test cycle starts at 0"""
        lbd = HBM4LogicBaseDie()
        assert lbd.cycle == 0

    def test_tick_increments_cycle(self):
        """Test tick increments cycle"""
        lbd = HBM4LogicBaseDie()
        lbd.tick()
        assert lbd.cycle == 1

        for _ in range(100):
            lbd.tick()
        assert lbd.cycle == 101

    def test_tick_updates_dfi(self):
        """Test tick updates DFI interface"""
        lbd = HBM4LogicBaseDie()
        initial_cycle = lbd.dfi.cycle

        lbd.tick()
        lbd.tick()
        lbd.tick()

        assert lbd.dfi.cycle > initial_cycle

    def test_tick_updates_command_buffer(self):
        """Test tick updates command buffer"""
        lbd = HBM4LogicBaseDie()
        lbd.enqueue_command('ACT', channel=0, address=0x1000)
        lbd.tick()
        lbd.tick()


class TestProcessCommand:
    """Test process_command functionality"""

    def test_process_act_command(self):
        """Test processing ACT command"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        for _ in range(50):
            lbd.tick()

        ok, msg = lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        assert ok

        state = lbd.get_channel_state(0)
        assert state['open_row'] == (0x1000 & 0xFFFF)

    def test_process_pre_command(self):
        """Test processing PRE command"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        for _ in range(50):
            lbd.tick()

        lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        for _ in range(25):
            lbd.tick()

        ok, msg = lbd.process_command(channel_id=0, command='PRE', address=0x1000)
        assert ok

    def test_process_rd_command(self):
        """Test processing RD command"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        for _ in range(50):
            lbd.tick()

        lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        for _ in range(10):
            lbd.tick()

        ok, msg = lbd.process_command(channel_id=0, command='RD', address=0x1000)
        assert ok

    def test_process_wr_command(self):
        """Test processing WR command"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        for _ in range(50):
            lbd.tick()

        lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        for _ in range(10):
            lbd.tick()

        ok, msg = lbd.process_command(
            channel_id=0, command='WR', address=0x1000, data=0xDEADBEEF
        )
        assert ok

    def test_process_ref_command(self):
        """Test processing REFRESH command"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        for _ in range(50):
            lbd.tick()

        ok, msg = lbd.process_command(channel_id=0, command='REF', address=0)
        assert ok

    def test_process_invalid_channel(self):
        """Test processing command on invalid channel"""
        lbd = HBM4LogicBaseDie()
        ok, msg = lbd.process_command(channel_id=32, command='ACT', address=0x1000)
        assert not ok
        assert "Invalid channel" in msg

    def test_process_unknown_command(self):
        """Test processing unknown command"""
        lbd = HBM4LogicBaseDie()
        ok, msg = lbd.process_command(channel_id=0, command='UNKNOWN', address=0)
        assert not ok
        assert "Unknown command" in msg


class TestStatistics:
    """Test statistics collection"""

    def test_get_stats(self):
        """Test getting statistics"""
        lbd = HBM4LogicBaseDie()
        stats = lbd.get_stats()

        assert 'global_cycle' in stats
        assert 'initialized' in stats
        assert 'total_commands' in stats
        assert 'total_errors' in stats
        assert 'channels_total' in stats

    def test_stats_after_commands(self):
        """Test statistics after commands"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        for _ in range(50):
            lbd.tick()

        lbd.process_command(channel_id=0, command='ACT', address=0x1000)
        lbd.process_command(channel_id=1, command='ACT', address=0x2000)

        stats = lbd.get_stats()
        assert stats['total_commands'] >= 2

    def test_get_lane_repair_stats(self):
        """Test getting lane repair statistics"""
        lbd = HBM4LogicBaseDie()
        stats = lbd.get_lane_repair_stats()

        assert 'total_channels' in stats
        assert stats['total_channels'] == 32


class TestReset:
    """Test reset functionality"""

    def test_reset_clears_state(self):
        """Test reset clears state"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()
        lbd.tick()
        lbd.process_command(channel_id=0, command='ACT', address=0x1000)

        lbd.reset()

        assert lbd._global_cycle == 0
        assert lbd.is_initialized is False
        assert lbd.cycle == 0

    def test_reset_clears_dfi_queue(self):
        """Test reset clears DFI queue"""
        lbd = HBM4LogicBaseDie()
        lbd.submit_dfi_act(channel=0, bank=0, row=0x1000)
        lbd.submit_dfi_read(channel=0, bank=0, column=0x100)

        assert lbd.dfi_pending_count > 0

        lbd.reset()

        assert lbd.dfi_pending_count == 0

    def test_reset_clears_command_buffer(self):
        """Test reset clears command buffer"""
        lbd = HBM4LogicBaseDie()
        lbd.enqueue_command('ACT', channel=0, address=0x1000)
        lbd.enqueue_command('RD', channel=0, address=0x2000)

        lbd.reset()

        assert lbd.command_buffer_size == 0


class TestStatus:
    """Test status reporting"""

    def test_get_status(self):
        """Test getting comprehensive status"""
        lbd = HBM4LogicBaseDie()
        status = lbd.get_status()

        assert 'cycle' in status
        assert 'initialized' in status
        assert 'dfi' in status
        assert 'command_buffer' in status
        assert 'channels' in status
        assert 'statistics' in status

    def test_get_status_dfi_info(self):
        """Test status includes DFI info"""
        lbd = HBM4LogicBaseDie()
        status = lbd.get_status()

        assert 'lp_state' in status['dfi']
        assert 'frequency_mhz' in status['dfi']
        assert 'pending_requests' in status['dfi']


class TestWaitForReady:
    """Test wait_for_ready functionality"""

    def test_wait_for_ready_timeout(self):
        """Test wait_for_ready with short timeout"""
        lbd = HBM4LogicBaseDie()
        lbd.initialize()

        # Should timeout with very short max_cycles
        result = lbd.wait_for_ready(max_cycles=10)
        # Training not complete in 10 cycles, so returns False
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])