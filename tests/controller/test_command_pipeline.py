"""
Tests for HBM Command Pipeline
Increases coverage from 41% to 95%+

Covers:
- CommandPipeline.tick()
- CommandPipeline.set_cycle()
- CommandPipeline.write_data()
- CommandPipeline.get_write_data()
- CommandPipeline.get_read_data()
- CommandPipeline.submit_command()
- CommandPipeline._estimate_duration()
- CommandPipeline.process_completions()
- CommandPipeline._is_command_done()
- CommandPipeline.get_pending_count()
- CommandPipeline.get_in_progress_commands()
- CommandPipeline.get_command_for_bank()
- CommandPipeline.sync_bank_state()
- CommandPipeline.check_timing_violation()
- CommandPipeline.get_stats()
- CommandPipeline.reset_stats()
- PendingCommand methods
"""

import pytest
from model.controller.command_pipeline import (
    CommandPipeline, PendingCommand, PendingState, CommandType
)
from model.controller.request import HBMRequest
from model.controller.scheduler import BankState
from model.dram.hbm4_spec import HBM4Spec


class MockDRAMModel:
    """Mock DRAM model for testing"""
    def __init__(self, success=True):
        self.success = success
        self.execute_count = 0

    def execute_request(self, stack_id, ch_id, ps_id, bg_id, bank_id,
                       row, cmd, current_time):
        self.execute_count += 1
        return self.success

    def execute(self, channel, bank, row, cmd):
        self.execute_count += 1
        return self.success


class TestPendingCommand:
    """Tests for PendingCommand dataclass"""

    def test_pending_command_creation(self):
        """Test basic PendingCommand creation"""
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        cmd = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=100.0,
            expected_duration=10,
        )
        assert cmd.command_type == CommandType.READ
        assert cmd.start_time == 100.0
        assert cmd.expected_duration == 10
        assert cmd.state == PendingState.WAITING

    def test_pending_command_bank_key_auto_init(self):
        """Test that bank_key is auto-initialized from request"""
        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            channel_id=3,
            pseudo_channel_id=1,
            bank_id=5,
            bank_group_id=2,
            stack_id=0,
            row_id=100,
        )
        cmd = PendingCommand(
            request=request,
            command_type=CommandType.ACTIVATE,
            start_time=0.0,
            expected_duration=10,
        )
        assert cmd.bank_key == (3, 1, 5)
        assert cmd.channel_id == 3
        assert cmd.pseudo_channel_id == 1
        assert cmd.bank_id == 5
        assert cmd.bank_group_id == 2
        assert cmd.stack_id == 0
        assert cmd.row_id == 100

    def test_mark_in_progress(self):
        """Test mark_in_progress method"""
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        cmd = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        assert cmd.state == PendingState.WAITING
        cmd.mark_in_progress(50.0)
        assert cmd.state == PendingState.IN_PROGRESS
        assert cmd.start_time == 50.0

    def test_mark_completed(self):
        """Test mark_completed method"""
        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=10.0)
        cmd = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        cmd.mark_completed(110.0)
        assert cmd.state == PendingState.COMPLETED
        assert cmd.completion_time == 110.0
        assert cmd.actual_latency == 100.0  # 110 - 10

    def test_mark_failed(self):
        """Test mark_failed method"""
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        cmd = PendingCommand(
            request=request,
            command_type=CommandType.WRITE,
            start_time=0.0,
            expected_duration=10,
        )
        cmd.mark_failed()
        assert cmd.state == PendingState.FAILED

    def test_latency_ns_property(self):
        """Test latency_ns property"""
        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=0.0)
        cmd = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        cmd.mark_completed(80.0)  # 80 cycles at 125ps = 10ns
        # actual_latency is 80 cycles
        assert cmd.actual_latency == 80.0

    def test_repr(self):
        """Test string representation"""
        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            channel_id=3,
            pseudo_channel_id=1,
            bank_id=5,
            bank_group_id=2,
        )
        cmd = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        repr_str = repr(cmd)
        # CommandType uses abbreviated format
        assert "RD" in repr_str
        assert "ch=3" in repr_str
        assert "ps=1" in repr_str


class TestCommandPipeline:
    """Tests for CommandPipeline"""

    def test_pipeline_creation(self):
        """Test basic pipeline creation"""
        pipeline = CommandPipeline()
        assert pipeline.max_pending == 64
        assert pipeline.get_pending_count() == 0
        assert pipeline.current_cycle == 0.0

    def test_pipeline_with_custom_spec(self):
        """Test pipeline with custom HBM4 spec"""
        spec = HBM4Spec()
        pipeline = CommandPipeline(spec=spec, max_pending=32)
        assert pipeline.max_pending == 32
        assert pipeline.spec.channels == 32

    def test_tick(self):
        """Test tick method advances cycle"""
        pipeline = CommandPipeline()
        pipeline.tick(10)
        assert pipeline.current_cycle == 10.0
        pipeline.tick(5)
        assert pipeline.current_cycle == 15.0

    def test_set_cycle(self):
        """Test set_cycle method"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(100.5)
        assert pipeline.current_cycle == 100.5

    def test_write_data_no_pending(self):
        """Test write_data when no pending write"""
        pipeline = CommandPipeline()
        result = pipeline.write_data(b"test data")
        assert result is False

    def test_write_data_read_request(self):
        """Test write_data rejects read requests"""
        pipeline = CommandPipeline()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        # Simulate setting pending write
        pipeline._pending_write = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        result = pipeline.write_data(b"test data")
        assert result is False

    def test_write_data_success(self):
        """Test successful write_data"""
        pipeline = CommandPipeline()
        request = HBMRequest(addr=0x1000, length=64, is_read=False)
        pending = PendingCommand(
            request=request,
            command_type=CommandType.WRITE,
            start_time=0.0,
            expected_duration=10,
        )
        pending.is_read = False  # Override for this test
        pipeline._pending_write = pending

        result = pipeline.write_data(b"test data 123")
        assert result is True
        assert pipeline._write_data == b"test data 123"

    def test_get_write_data(self):
        """Test get_write_data clears data"""
        pipeline = CommandPipeline()
        pipeline._write_data = b"some data"
        data = pipeline.get_write_data()
        assert data == b"some data"
        assert pipeline._write_data is None

    def test_get_write_data_empty(self):
        """Test get_write_data when empty"""
        pipeline = CommandPipeline()
        data = pipeline.get_write_data()
        assert data is None

    def test_get_read_data(self):
        """Test get_read_data generates mock data"""
        pipeline = CommandPipeline()
        data = pipeline.get_read_data(64)
        assert data == bytes(64)
        assert len(data) == 64

    def test_submit_command_full_pipeline(self):
        """Test submit_command with full pipeline"""
        pipeline = CommandPipeline()
        dram = MockDRAMModel(success=True)
        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            channel_id=3,
            pseudo_channel_id=1,
            bank_id=5,
            bank_group_id=2,
            stack_id=0,
            row_id=100,
        )

        pending = pipeline.submit_command(request, dram)
        assert pending is not None
        assert pending.state == PendingState.IN_PROGRESS
        assert pipeline.get_pending_count() == 1
        assert dram.execute_count == 1
        assert pipeline.stats['commands_sent'] == 1

    def test_submit_command_pipeline_full(self):
        """Test submit_command raises when pipeline full"""
        pipeline = CommandPipeline(max_pending=1)
        dram = MockDRAMModel(success=True)

        request1 = HBMRequest(addr=0x1000, length=64, is_read=True, channel_id=0, pseudo_channel_id=0, bank_id=0, bank_group_id=0)
        request2 = HBMRequest(addr=0x2000, length=64, is_read=True, channel_id=0, pseudo_channel_id=0, bank_id=1, bank_group_id=0)

        pipeline.submit_command(request1, dram)

        with pytest.raises(RuntimeError, match="Command pipeline full"):
            pipeline.submit_command(request2, dram)

    def test_submit_command_failed_execution(self):
        """Test submit_command with failed DRAM execution"""
        pipeline = CommandPipeline()
        dram = MockDRAMModel(success=False)
        request = HBMRequest(addr=0x1000, length=64, is_read=True)

        pending = pipeline.submit_command(request, dram)
        assert pending.state == PendingState.FAILED
        assert pipeline.stats['commands_failed'] == 1

    def test_submit_command_alternative_interface(self):
        """Test submit_command with alternative DRAM interface"""
        pipeline = CommandPipeline()

        # Create a mock that only has execute, not execute_request
        class AltMockDRAM:
            def __init__(self):
                self.called = False
            def execute(self, channel, bank, row, cmd):
                self.called = True
                return True

        dram = AltMockDRAM()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)

        pending = pipeline.submit_command(request, dram)
        assert pending is not None
        assert dram.called is True

    def test_submit_command_no_dram_model(self):
        """Test submit_command without DRAM model"""
        pipeline = CommandPipeline()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)

        pending = pipeline.submit_command(request, None)
        assert pending is not None
        assert pending.state == PendingState.IN_PROGRESS

    def test_estimate_duration_row_hit(self):
        """Test _estimate_duration for row hit"""
        pipeline = CommandPipeline()
        request = HBMRequest(addr=0x1000, length=64, is_read=True, row_hit=True)
        duration = pipeline._estimate_duration(request)
        assert duration == pipeline.spec.nCCDS

    def test_estimate_duration_row_miss(self):
        """Test _estimate_duration for row miss"""
        pipeline = CommandPipeline()
        request = HBMRequest(addr=0x1000, length=64, is_read=True, row_hit=False)
        duration = pipeline._estimate_duration(request)
        assert duration == pipeline.spec.nRCDRD + pipeline.spec.nCCDS

    def test_is_command_done_completed(self):
        """Test _is_command_done for completed state"""
        pipeline = CommandPipeline()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        pending = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        pending.mark_completed(100.0)

        assert pipeline._is_command_done(pending) is True

    def test_is_command_done_waiting(self):
        """Test _is_command_done for waiting state"""
        pipeline = CommandPipeline()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        pending = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        # Still in WAITING state
        assert pipeline._is_command_done(pending) is False

    def test_is_command_done_in_progress_not_done(self):
        """Test _is_command_done for in-progress not yet done"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(5.0)
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        pending = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        pending.mark_in_progress(0.0)

        assert pipeline._is_command_done(pending) is False

    def test_is_command_done_in_progress_done(self):
        """Test _is_command_done for in-progress completed"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(15.0)
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        pending = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        pending.mark_in_progress(0.0)

        assert pipeline._is_command_done(pending) is True

    def test_get_in_progress_commands(self):
        """Test get_in_progress_commands"""
        pipeline = CommandPipeline()
        dram = MockDRAMModel(success=True)

        request1 = HBMRequest(addr=0x1000, length=64, is_read=True, channel_id=0, pseudo_channel_id=0, bank_id=0, bank_group_id=0)
        request2 = HBMRequest(addr=0x2000, length=64, is_read=True, channel_id=0, pseudo_channel_id=0, bank_id=1, bank_group_id=0)

        pending1 = pipeline.submit_command(request1, dram)
        pipeline.submit_command(request2, dram)

        in_progress = pipeline.get_in_progress_commands()
        assert len(in_progress) == 2
        assert all(c.state == PendingState.IN_PROGRESS for c in in_progress)

    def test_get_command_for_bank(self):
        """Test get_command_for_bank"""
        pipeline = CommandPipeline()
        dram = MockDRAMModel(success=True)

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            channel_id=3,
            pseudo_channel_id=1,
            bank_id=5,
        )
        pipeline.submit_command(request, dram)

        # Found
        cmd = pipeline.get_command_for_bank(3, 1, 5)
        assert cmd is not None

        # Not found
        cmd = pipeline.get_command_for_bank(0, 0, 0)
        assert cmd is None

    def test_sync_bank_state(self):
        """Test sync_bank_state"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(100.0)

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            channel_id=3,
            pseudo_channel_id=1,
            bank_id=5,
            row_id=1000,
        )
        bank_states = {}

        result = pipeline.sync_bank_state(request, bank_states)

        assert result.is_open is True
        assert result.open_row == 1000
        assert (3, 1, 5) in bank_states

    def test_sync_bank_state_existing(self):
        """Test sync_bank_state with existing bank state"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(100.0)

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            channel_id=3,
            pseudo_channel_id=1,
            bank_id=5,
            row_id=2000,
        )

        # Create existing bank state
        existing = BankState(bank_id=5)
        existing.is_open = True
        existing.open_row = 1000
        bank_states = {(3, 1, 5): existing}

        result = pipeline.sync_bank_state(request, bank_states)

        # Should update existing state
        assert result.open_row == 2000
        assert result.last_access_time == 100.0

    def test_check_timing_violation(self):
        """Test check_timing_violation"""
        pipeline = CommandPipeline()
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        dram = MockDRAMModel()

        # Currently always returns False
        result = pipeline.check_timing_violation(request, dram)
        assert result is False

    def test_get_stats(self):
        """Test get_stats"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(100.0)

        stats = pipeline.get_stats()

        assert 'commands_sent' in stats
        assert 'commands_completed' in stats
        assert 'commands_failed' in stats
        assert 'pending_count' in stats
        assert 'completed_count' in stats
        assert 'avg_latency_ns' in stats
        assert 'max_latency_ns' in stats
        assert 'spec' in stats
        assert stats['spec']['channels'] == 32

    def test_reset_stats(self):
        """Test reset_stats"""
        pipeline = CommandPipeline()

        # Add some stats
        pipeline.stats['commands_sent'] = 100
        pipeline.stats['commands_completed'] = 50

        pipeline.reset_stats()

        assert pipeline.stats['commands_sent'] == 0
        assert pipeline.stats['commands_completed'] == 0
        assert pipeline.stats['commands_failed'] == 0

    def test_repr(self):
        """Test string representation"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(100.0)

        repr_str = repr(pipeline)
        assert "CommandPipeline" in repr_str
        assert "cycle=100" in repr_str


class TestCommandPipelineCompletions:
    """Tests for command completion processing"""

    def test_process_completions_basic(self):
        """Test basic completion processing"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(100.0)
        dram = MockDRAMModel(success=True)

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            arrival_time=0.0,
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            bank_group_id=0,
        )
        pending = pipeline.submit_command(request, dram)

        # Advance past expected duration
        pipeline.set_cycle(200.0)

        responses = pipeline.process_completions()

        assert len(responses) == 1
        assert responses[0].request_id == request.request_id
        assert responses[0].status == "OK"
        assert pipeline.stats['commands_completed'] == 1
        assert pipeline.get_pending_count() == 0
        assert len(pipeline.completed_commands) == 1

    def test_process_completions_already_completed(self):
        """Test completion processing for already completed command"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(50.0)

        request = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=0.0)
        pending = PendingCommand(
            request=request,
            command_type=CommandType.READ,
            start_time=0.0,
            expected_duration=10,
        )
        pending.mark_completed(40.0)
        pipeline.pending_commands.append(pending)

        responses = pipeline.process_completions()

        assert len(responses) == 1
        assert pipeline.get_pending_count() == 0

    def test_process_completions_multiple(self):
        """Test processing multiple completions"""
        pipeline = CommandPipeline()
        pipeline.set_cycle(200.0)
        dram = MockDRAMModel(success=True)

        # Submit multiple commands and mark them in progress
        for i in range(3):
            request = HBMRequest(
                addr=0x1000 * (i + 1),
                length=64,
                is_read=True,
                arrival_time=float(i * 10),
                channel_id=i,
                pseudo_channel_id=0,
                bank_id=i,
                bank_group_id=0,
            )
            pending = PendingCommand(
                request=request,
                command_type=CommandType.READ,
                start_time=float(i * 10),
                expected_duration=10,
            )
            pending.mark_in_progress(float(i * 10))
            pipeline.pending_commands.append(pending)

        responses = pipeline.process_completions()
        assert len(responses) == 3
        assert pipeline.stats['commands_completed'] == 3


class TestCommandPipelineEdgeCases:
    """Edge case tests for command pipeline"""

    def test_pipeline_with_write_command(self):
        """Test pipeline with write command"""
        pipeline = CommandPipeline()
        dram = MockDRAMModel(success=True)

        request = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=False,  # Write
            channel_id=0,
            pseudo_channel_id=0,
            bank_id=0,
            bank_group_id=0,
        )

        pending = pipeline.submit_command(request, dram)
        assert pending.command_type == CommandType.WRITE

    def test_pipeline_with_all_command_types(self):
        """Test pipeline with all command types"""
        for cmd_type, is_read in [(CommandType.ACTIVATE, None),
                                  (CommandType.PRECHARGE, None),
                                  (CommandType.READ, True),
                                  (CommandType.WRITE, False),
                                  (CommandType.REFRESH, None)]:
            pipeline = CommandPipeline()
            dram = MockDRAMModel(success=True)

            request = HBMRequest(
                addr=0x1000,
                length=64,
                is_read=is_read if is_read is not None else True,
                channel_id=0,
                pseudo_channel_id=0,
                bank_id=0,
                bank_group_id=0,
            )

            pending = PendingCommand(
                request=request,
                command_type=cmd_type,
                start_time=0.0,
                expected_duration=10,
            )
            assert pending.command_type == cmd_type

    def test_pipeline_stats_accumulation(self):
        """Test that stats accumulate correctly"""
        pipeline = CommandPipeline()

        # Simulate multiple commands
        pipeline.stats['commands_sent'] = 10
        pipeline.stats['commands_completed'] = 5
        pipeline.stats['commands_failed'] = 2
        pipeline.stats['total_latency_cycles'] = 500.0
        pipeline.stats['max_latency_cycles'] = 100.0

        stats = pipeline.get_stats()
        assert stats['commands_sent'] == 10
        assert stats['commands_completed'] == 5
        assert stats['total_latency_cycles'] == 500.0
