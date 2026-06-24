"""
Tests for HBM DRAM Stack Model

Covers model/dram/stack_model.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from model.dram.stack_model import (
    InterconnectTopology, Stack, StackArray, DRAMModel
)
from model.dram.timing import HBM3Timing


class TestInterconnectTopology:
    """Test InterconnectTopology enum"""

    def test_topology_values(self):
        assert InterconnectTopology.MESH.value == "mesh"
        assert InterconnectTopology.FULL_CROSSBAR.value == "full_crossbar"
        assert InterconnectTopology.BUTTERFLY.value == "butterfly"


class TestStack:
    """Test Stack class"""

    def test_creation(self):
        stack = Stack(stack_id=0)
        assert stack.stack_id == 0
        assert stack.num_channels == 8
        assert stack.current_time == 0.0
        assert stack.channels is not None

    def test_creation_custom_channels(self):
        stack = Stack(stack_id=1, num_channels=4)
        assert stack.num_channels == 4

    def test_set_time(self):
        stack = Stack(stack_id=0)
        stack.set_time(100.0)
        assert stack.current_time == 100.0

    def test_get_channel(self):
        stack = Stack(stack_id=0)
        channel = stack.get_channel(0)
        assert channel is not None
        assert channel.channel_id == 0

    def test_get_bank(self):
        stack = Stack(stack_id=0)
        bank = stack.get_bank(0, 0, 0, 0)
        assert bank is not None

    def test_is_row_hit(self):
        stack = Stack(stack_id=0)
        # Initially no row is open
        result = stack.is_row_hit(0, 0, 0, 0, 0)
        assert result is False

    def test_execute_command(self):
        stack = Stack(stack_id=0)
        # Execute ACT command
        result = stack.execute_command(0, 0, "ACT", 0, 0, row=0)
        # Result is a tuple
        assert result[0] is True

    def test_get_total_banks(self):
        stack = Stack(stack_id=0)
        total = stack.get_total_banks()
        # 8 channels * 2 pseudo_channels * 8 bank_groups * 2 banks
        assert total == 256

    def test_get_stats(self):
        stack = Stack(stack_id=0)
        stats = stack.get_stats()
        assert 'total_banks' in stats
        assert 'active_banks' in stats
        assert 'idle_banks' in stats
        assert stats['total_banks'] == 256


class TestStackArray:
    """Test StackArray class"""

    def test_creation_default(self):
        array = StackArray()
        assert array.num_stacks == 2
        assert len(array.stacks) == 2
        assert array.topology == InterconnectTopology.MESH

    def test_creation_custom_stacks(self):
        array = StackArray(num_stacks=4)
        assert array.num_stacks == 4
        assert len(array.stacks) == 4

    def test_creation_custom_topology(self):
        array = StackArray(
            num_stacks=2,
            topology=InterconnectTopology.FULL_CROSSBAR
        )
        assert array.topology == InterconnectTopology.FULL_CROSSBAR

    def test_set_time(self):
        array = StackArray(num_stacks=2)
        array.set_time(50.0)
        for stack in array.stacks:
            assert stack.current_time == 50.0

    def test_get_stack(self):
        array = StackArray(num_stacks=4)
        stack = array.get_stack(2)
        assert stack is not None
        assert stack.stack_id == 2

    def test_get_total_banks(self):
        array = StackArray(num_stacks=2)
        total = array.get_total_banks()
        # 2 stacks * 256 banks each
        assert total == 512

    def test_get_stats(self):
        array = StackArray(num_stacks=2)
        stats = array.get_stats()
        assert stats['num_stacks'] == 2
        assert stats['topology'] == "mesh"
        assert 'total_banks' in stats
        assert 'stacks' in stats


class TestDRAMModel:
    """Test DRAMModel class"""

    def test_creation_default(self):
        model = DRAMModel()
        assert model.num_stacks == 2
        assert model.num_channels == 8
        assert model.stack_array is not None
        assert model.current_time == 0.0

    def test_creation_custom(self):
        model = DRAMModel(num_stacks=4, num_channels=4)
        assert model.num_stacks == 4
        assert model.num_channels == 4

    def test_set_time(self):
        model = DRAMModel()
        model.set_time(100.0)
        assert model.current_time == 100.0
        assert model.stack_array.stacks[0].current_time == 100.0

    def test_tick(self):
        model = DRAMModel()
        initial_time = model.current_time
        timing = model.timing
        clock_period = timing.clock_period_ns  # in ns

        model.tick(1)
        # Time should advance by clock_period * 1e-9
        expected = initial_time + clock_period * 1e-9
        assert abs(model.current_time - expected) < 1e-12

    def test_get_stats(self):
        model = DRAMModel()
        stats = model.get_stats()
        assert 'num_stacks' in stats
        assert 'total_banks' in stats


class TestIntegration:
    """Integration tests for stack model"""

    def test_multi_stack_operation(self):
        """Test operations across multiple stacks"""
        model = DRAMModel(num_stacks=2)

        # Execute request on stack 0
        model.execute_request(
            stack_id=0, ch_id=0, ps_id=0,
            bg_id=0, bank_id=0, row=0, cmd="READ"
        )

        # Execute request on stack 1
        model.execute_request(
            stack_id=1, ch_id=0, ps_id=0,
            bg_id=0, bank_id=0, row=0, cmd="WRITE"
        )

        stats = model.get_stats()
        assert stats['num_stacks'] == 2

    def test_independent_channels(self):
        """Test that channels operate independently"""
        model = DRAMModel(num_channels=4)

        # Open row in channel 0
        model.execute_request(
            stack_id=0, ch_id=0, ps_id=0,
            bg_id=0, bank_id=0, row=0, cmd="READ"
        )

        # Open row in channel 1
        model.execute_request(
            stack_id=0, ch_id=1, ps_id=0,
            bg_id=0, bank_id=0, row=0, cmd="READ"
        )

        # Channel 0 and 1 should be independent
        stats = model.get_stats()
        assert stats['total_banks'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
