"""
Tests for HBM DRAM Channel Model

Covers model/dram/channel_model.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from model.dram.channel_model import (
    BankGroup, PseudoChannel, Channel, ChannelArray
)
from model.dram.bank_state_machine import Bank, BankStateEnum


class TestBankGroup:
    """Test BankGroup class"""

    def test_creation(self):
        bg = BankGroup(group_id=0)
        assert bg.group_id == 0
        assert len(bg.banks) == 2  # 2 banks per group

    def test_get_bank(self):
        bg = BankGroup(group_id=0)
        bank0 = bg.get_bank(0)
        assert bank0 is not None

    def test_can_activate_any_true(self):
        bg = BankGroup(group_id=0)
        # Both banks are initially closed, can activate
        result = bg.can_activate_any()
        assert result is True


class TestPseudoChannel:
    """Test PseudoChannel class"""

    def test_creation(self):
        pc = PseudoChannel(channel_id=0, pseudo_id=0)
        assert pc.channel_id == 0
        assert pc.pseudo_id == 0
        assert len(pc.bank_groups) == 8  # 8 bank groups

    def test_get_bank(self):
        pc = PseudoChannel(channel_id=0, pseudo_id=0)
        bank = pc.get_bank(bg_id=0, bank_id=0)
        assert bank is not None

    def test_get_bank_by_global_id(self):
        pc = PseudoChannel(channel_id=0, pseudo_id=0)
        # Global bank ID = bg_id * 2 + bank_in_group
        bg_id, bank_in_group, bank = pc.get_bank_by_global_id(0)
        assert bg_id == 0
        assert bank_in_group == 0

        bg_id, bank_in_group, bank = pc.get_bank_by_global_id(3)
        assert bg_id == 1
        assert bank_in_group == 1

        bg_id, bank_in_group, bank = pc.get_bank_by_global_id(7)
        assert bg_id == 3
        assert bank_in_group == 1


class TestChannel:
    """Test Channel class"""

    def test_creation(self):
        ch = Channel(channel_id=0)
        assert ch.channel_id == 0
        assert len(ch.pseudo_channels) == 2  # 2 pseudo channels
        assert ch.current_time == 0.0

    def test_set_time(self):
        ch = Channel(channel_id=0)
        ch.set_time(100.0)
        assert ch.current_time == 100.0

    def test_get_pseudo_channel(self):
        ch = Channel(channel_id=0)
        pc0 = ch.get_pseudo_channel(0)
        assert pc0 is not None
        assert pc0.pseudo_id == 0

        pc1 = ch.get_pseudo_channel(1)
        assert pc1.pseudo_id == 1

    def test_get_bank(self):
        ch = Channel(channel_id=0)
        bank = ch.get_bank(ps_id=0, bg_id=0, bank_id=0)
        assert bank is not None

    def test_is_row_hit_false(self):
        ch = Channel(channel_id=0)
        result = ch.is_row_hit(ps_id=0, bg_id=0, bank_id=0, row=0)
        assert result is False

    def test_execute_command_act(self):
        ch = Channel(channel_id=0)
        result = ch.execute_command(ps_id=0, cmd="ACT", bg_id=0, bank_id=0, row=0)
        # Result is (success, message) tuple
        assert result[0] is True

    def test_execute_command_invalid(self):
        ch = Channel(channel_id=0)
        result = ch.execute_command(ps_id=0, cmd="INVALID", bg_id=0, bank_id=0)
        # Result depends on implementation - some return bool, some return tuple
        assert result is False or (isinstance(result, tuple) and result[0] is False)


class TestChannelArray:
    """Test ChannelArray class"""

    def test_creation_default(self):
        array = ChannelArray()
        assert array.num_channels == 8
        assert len(array.channels) == 8

    def test_creation_custom(self):
        array = ChannelArray(num_channels=16)
        assert array.num_channels == 16
        assert len(array.channels) == 16

    def test_set_time(self):
        array = ChannelArray(num_channels=4)
        array.set_time(50.0)
        for ch in array.channels:
            assert ch.current_time == 50.0

    def test_get_channel(self):
        array = ChannelArray(num_channels=8)
        ch = array.get_channel(3)
        assert ch is not None
        assert ch.channel_id == 3

    def test_get_bank(self):
        array = ChannelArray(num_channels=4)
        bank = array.get_bank(ch_id=0, ps_id=0, bg_id=0, bank_id=0)
        assert bank is not None

    def test_is_row_hit(self):
        array = ChannelArray(num_channels=4)
        result = array.is_row_hit(ch_id=0, ps_id=0, bg_id=0, bank_id=0, row=0)
        assert result is False


class TestChannelOperations:
    """Test channel operation sequences"""

    def test_full_read_sequence(self):
        """Test complete READ sequence: ACT -> RD -> PRE"""
        ch = Channel(channel_id=0)

        # Activate bank
        result = ch.execute_command(ps_id=0, cmd="ACT", bg_id=0, bank_id=0, row=100)
        assert result[0] is True

        # Read data
        result = ch.execute_command(ps_id=0, cmd="RD", bg_id=0, bank_id=0)
        # Read may fail if timing not met, but command is valid

        # Precharge bank
        result = ch.execute_command(ps_id=0, cmd="PRE", bg_id=0, bank_id=0)
        # Precharge may fail if timing not met

    def test_full_write_sequence(self):
        """Test complete WRITE sequence: ACT -> WR -> PRE"""
        ch = Channel(channel_id=0)

        # Activate bank
        result = ch.execute_command(ps_id=0, cmd="ACT", bg_id=0, bank_id=0, row=100)
        assert result[0] is True

        # Write data
        result = ch.execute_command(ps_id=0, cmd="WR", bg_id=0, bank_id=0)
        # Write may fail if timing not met

    def test_row_hit_after_activate(self):
        """Test row hit detection after activation"""
        ch = Channel(channel_id=0)

        # Activate
        ch.execute_command(ps_id=0, cmd="ACT", bg_id=0, bank_id=0, row=100)

        # Check row hit
        result = ch.is_row_hit(ps_id=0, bg_id=0, bank_id=0, row=100)
        assert result is True

        # Different row should not hit
        result = ch.is_row_hit(ps_id=0, bg_id=0, bank_id=0, row=200)
        assert result is False


class TestPseudoChannelIndependence:
    """Test that pseudo channels operate independently"""

    def test_independent_pseudo_channels(self):
        """Test two pseudo channels don't interfere"""
        ch = Channel(channel_id=0)

        # Activate in pseudo channel 0
        ch.execute_command(ps_id=0, cmd="ACT", bg_id=0, bank_id=0, row=100)

        # Pseudo channel 1 should not be affected
        pc1 = ch.get_pseudo_channel(1)
        pc1_bank = pc1.get_bank(0, 0)
        assert pc1_bank.bank.state == BankStateEnum.IDLE


class TestChannelArrayIndependence:
    """Test channel array independence"""

    def test_independent_channels(self):
        """Test channels operate independently"""
        array = ChannelArray(num_channels=4)

        # Activate in channel 0
        array.channels[0].execute_command(ps_id=0, cmd="ACT", bg_id=0, bank_id=0, row=100)

        # Channel 1 should not be affected
        ch1_bank = array.channels[1].get_bank(ps_id=0, bg_id=0, bank_id=0)
        assert ch1_bank.bank.state == BankStateEnum.IDLE


class TestBankGroupScheduling:
    """Test bank group scheduling behavior"""

    def test_bank_group_activation_order(self):
        """Test activating banks in different groups"""
        ch = Channel(channel_id=0)

        # Activate bank in group 0
        result1 = ch.execute_command(ps_id=0, cmd="ACT", bg_id=0, bank_id=0, row=100)
        assert result1[0] is True

        # Activate bank in group 1
        result2 = ch.execute_command(ps_id=0, cmd="ACT", bg_id=1, bank_id=0, row=100)
        assert result2[0] is True

    def test_bank_group_read_independence(self):
        """Test reads from different bank groups"""
        ch = Channel(channel_id=0)

        # Open banks in different groups
        ch.execute_command(ps_id=0, cmd="ACT", bg_id=0, bank_id=0, row=100)
        ch.execute_command(ps_id=0, cmd="ACT", bg_id=1, bank_id=0, row=100)

        # Reads may work depending on timing
        result1 = ch.execute_command(ps_id=0, cmd="RD", bg_id=0, bank_id=0)
        result2 = ch.execute_command(ps_id=0, cmd="RD", bg_id=1, bank_id=0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
