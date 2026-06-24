"""
Comprehensive tests for HBM Configuration
Increases coverage from 66% to 95%+

Covers:
- HBMConfig (all methods)
- AddressMappingScheme
- SchedulerMode
- RefreshMode
- Factory methods
"""

import pytest
import yaml
import tempfile
import os
from model.controller.config import (
    HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT,
    AddressMappingScheme, SchedulerMode, RefreshMode
)
from model.dram.timing import HBM3Timing, HBM4Timing


class TestAddressMappingScheme:
    """Tests for AddressMappingScheme enum"""

    def test_all_schemes(self):
        """Test all address mapping schemes"""
        assert AddressMappingScheme.RBC.value == "rbc"
        assert AddressMappingScheme.RCBC.value == "rcbc"
        assert AddressMappingScheme.BCR.value == "bcr"
        assert AddressMappingScheme.CRB.value == "crb"
        assert AddressMappingScheme.RBCG.value == "rbcg"
        assert AddressMappingScheme.CUSTOM.value == "custom"


class TestSchedulerMode:
    """Tests for SchedulerMode enum"""

    def test_all_modes(self):
        """Test all scheduler modes"""
        assert SchedulerMode.FR_FCFS.value == "fr-fcfs"
        assert SchedulerMode.FR_FCFS_QOS.value == "fr-fcfs-qos"
        assert SchedulerMode.QOS_ONLY.value == "qos-only"
        assert SchedulerMode.THROUGHPUT.value == "throughput"
        assert SchedulerMode.LATENCY.value == "latency"


class TestRefreshMode:
    """Tests for RefreshMode enum"""

    def test_all_modes(self):
        """Test all refresh modes"""
        assert RefreshMode.ALL_BANK.value == "all-bank"
        assert RefreshMode.PER_BANK.value == "per-bank"
        assert RefreshMode.AUTONOMOUS.value == "autonomous"
        assert RefreshMode.DRFM.value == "drfm"


class TestHBMConfig:
    """Comprehensive tests for HBMConfig"""

    def test_default_creation(self):
        """Test default config creation"""
        config = HBMConfig()
        assert config.stack_count == 2
        assert config.channels_per_stack == 8
        assert config.pseudo_channels_per_channel == 2
        assert config.banks_per_pseudo_channel == 16
        assert config.bank_groups_per_channel == 8

    def test_custom_creation(self):
        """Test custom config creation"""
        config = HBMConfig(
            stack_count=4,
            channels_per_stack=16,
            pseudo_channels_per_channel=4,
            banks_per_pseudo_channel=32,
            bank_groups_per_channel=16,
            queue_depth=64,
            max_outstanding=32,
            address_mapping="rcbc",
            scheduler_mode="qos",
        )
        assert config.stack_count == 4
        assert config.channels_per_stack == 16
        assert config.queue_depth == 64
        assert config.address_mapping == "rcbc"

    def test_hbm4_creation(self):
        """Test HBM4 config creation"""
        config = HBMConfig.hbm4_8gbps()
        assert config.channels_per_stack == 32
        assert config.stack_count == 4
        assert config.speed_grade == "8Gbps"
        assert config.ecc_enabled is False
        assert config.tCK_ps == 125.0

    def test_hbm4_16gbps_creation(self):
        """Test HBM4 16Gbps config creation"""
        config = HBMConfig.hbm4_16gbps()
        assert config.channels_per_stack == 32
        assert config.speed_grade == "16Gbps"
        assert config.ecc_enabled is True
        assert config.crc_enabled is True
        assert config.tCK_ps == 62.5

    def test_hbm4_16gbps_timing(self):
        """Test HBM4 16Gbps has correct timing"""
        config = HBMConfig.hbm4_16gbps()
        assert config.timing is not None
        assert isinstance(config.timing, HBM4Timing)

    def test_calc_bandwidth_hbm3(self):
        """Test bandwidth calculation for HBM3"""
        config = HBM3_DEFAULT
        bw = config.calc_bandwidth()
        # data_rate = 6.4e9, io_width = 1024
        # bandwidth = 6.4 * 1024 / 8 = 819.2 GB/s
        assert bw > 800  # Approximately 819.2

    def test_calc_bandwidth_hbm4(self):
        """Test bandwidth calculation for HBM4"""
        config = HBMConfig.hbm4_8gbps()
        bw = config.calc_bandwidth()
        # data_rate = 8.0e9, io_width = 2048
        # bandwidth = 8.0 * 2048 / 8 = 2048 GB/s
        assert bw > 2000  # Approximately 2048

    def test_calc_bandwidth_total(self):
        """Test total bandwidth calculation"""
        config = HBMConfig(stack_count=4)
        per_stack = config.calc_bandwidth()
        total = config.calc_bandwidth_total()
        assert total == per_stack * 4

    def test_is_hbm4_true(self):
        """Test is_hbm4 returns True for HBM4"""
        config = HBMConfig(channels_per_stack=32)
        assert config.is_hbm4 is True

    def test_is_hbm4_false(self):
        """Test is_hbm4 returns False for HBM3"""
        config = HBMConfig(channels_per_stack=8)
        assert config.is_hbm4 is False

    def test_total_channels(self):
        """Test total_channels calculation"""
        config = HBMConfig(stack_count=4, channels_per_stack=8)
        assert config.total_channels == 32

    def test_total_pseudo_channels(self):
        """Test total_pseudo_channels calculation"""
        config = HBMConfig(stack_count=4, channels_per_stack=8, pseudo_channels_per_channel=2)
        assert config.total_pseudo_channels == 64

    def test_total_banks(self):
        """Test total_banks calculation"""
        # total_banks = total_pseudo_channels * banks_per_pseudo_channel
        # total_pseudo_channels = total_channels * pseudo_channels_per_channel
        # total_channels = stack_count * channels_per_stack
        # So: total_banks = 4 * 8 * 2 * 16 = 1024
        config = HBMConfig(stack_count=4, channels_per_stack=8, banks_per_pseudo_channel=16)
        assert config.total_banks == 1024

    def test_channel_width_bits(self):
        """Test channel_width_bits calculation"""
        config = HBMConfig(io_width=1024, channels_per_stack=8)
        assert config.channel_width_bits == 128

    def test_effective_bandwidth_gbs(self):
        """Test effective bandwidth without ECC"""
        config = HBMConfig(ecc_enabled=False)
        base = config.calc_bandwidth()
        effective = config.effective_bandwidth_gbs
        assert effective == base

    def test_effective_bandwidth_with_ecc(self):
        """Test effective bandwidth with ECC"""
        config = HBMConfig(ecc_enabled=True)
        base = config.calc_bandwidth()
        effective = config.effective_bandwidth_gbs
        assert effective == base * 0.9

    def test_get_row_bits(self):
        """Test get_row_bits"""
        config = HBMConfig(row_size=2048, banks_per_pseudo_channel=16, burst_length=32)
        row_bits = config.get_row_bits()
        assert row_bits > 0

    def test_get_channel_bits(self):
        """Test get_channel_bits"""
        config = HBMConfig(channels_per_stack=8)
        assert config.get_channel_bits() == 3  # 8-1 = 7 = 0b111

        config = HBMConfig(channels_per_stack=32)
        assert config.get_channel_bits() == 5  # 32-1 = 31 = 0b11111

    def test_get_bank_bits(self):
        """Test get_bank_bits"""
        config = HBMConfig(banks_per_pseudo_channel=16)
        assert config.get_bank_bits() == 4  # 16-1 = 15 = 0b1111

        config = HBMConfig(banks_per_pseudo_channel=8)
        assert config.get_bank_bits() == 3

    def test_get_bank_group_bits(self):
        """Test get_bank_group_bits"""
        config = HBMConfig(bank_groups_per_channel=8)
        assert config.get_bank_group_bits() == 3  # 8-1 = 7

        config = HBMConfig(bank_groups_per_channel=16)
        assert config.get_bank_group_bits() == 4

    def test_get_address_layout(self):
        """Test get_address_layout"""
        config = HBMConfig()
        layout = config.get_address_layout()

        assert 'offset' in layout
        assert 'burst' in layout
        assert 'col' in layout
        assert 'row' in layout
        assert 'bank' in layout
        assert 'bank_group' in layout
        assert 'pseudo_channel' in layout
        assert 'channel' in layout
        assert 'stack' in layout

    def test_to_dict(self):
        """Test to_dict"""
        config = HBMConfig(stack_count=4, channels_per_stack=32)
        d = config.to_dict()

        assert d['stack_count'] == 4
        assert d['channels_per_stack'] == 32

    def test_copy(self):
        """Test copy"""
        config = HBMConfig(stack_count=4)
        config_copy = config.copy()

        assert config_copy.stack_count == 4
        assert config_copy is not config
        assert config_copy is not None

    def test_copy_independence(self):
        """Test that copy is independent"""
        config = HBMConfig(stack_count=4)
        config_copy = config.copy()

        config_copy.stack_count = 8

        assert config.stack_count == 4
        assert config_copy.stack_count == 8

    def test_repr(self):
        """Test string representation"""
        config = HBMConfig(stack_count=4, channels_per_stack=32)
        repr_str = repr(config)

        assert "HBMConfig" in repr_str
        assert "stack=4" in repr_str
        assert "ch=32" in repr_str

    def test_hbm4_8gbps_timing(self):
        """Test HBM4 8Gbps has correct timing"""
        config = HBMConfig.hbm4_8gbps()
        assert config.timing is not None
        assert isinstance(config.timing, HBM4Timing)


class TestHBMConfigYAML:
    """Tests for HBMConfig YAML loading"""

    def test_from_yaml(self):
        """Test loading from YAML"""
        yaml_content = {
            'stack_count': 4,
            'channels_per_stack': 32,
            'queue_depth': 64,
            'speed_grade': '16Gbps'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            config = HBMConfig.from_yaml(temp_path)
            assert config.stack_count == 4
            assert config.channels_per_stack == 32
            assert config.queue_depth == 64
            assert config.speed_grade == '16Gbps'
        finally:
            os.unlink(temp_path)

    def test_from_dict(self):
        """Test loading from dict"""
        data = {
            'stack_count': 8,
            'channels_per_stack': 16,
            'data_rate': 12.0e9,
        }

        config = HBMConfig.from_dict(data)

        assert config.stack_count == 8
        assert config.channels_per_stack == 16
        assert config.data_rate == 12.0e9

    def test_from_dict_filters_none(self):
        """Test that from_dict filters None values"""
        data = {
            'stack_count': 4,
            'unknown_field': None,
        }

        config = HBMConfig.from_dict(data)
        assert config.stack_count == 4

    def test_from_yaml_timing(self):
        """Test loading timing from YAML"""
        yaml_content = {
            'stack_count': 4,
            'channels_per_stack': 32,
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            config = HBMConfig.from_yaml(temp_path)
            # Should use default timing
            assert config.timing is not None
        finally:
            os.unlink(temp_path)


class TestHBM3_DEFAULT:
    """Tests for HBM3_DEFAULT"""

    def test_hbm3_default_values(self):
        """Test HBM3 default values"""
        config = HBM3_DEFAULT

        assert config.stack_count == 2
        assert config.channels_per_stack == 8
        assert config.pseudo_channels_per_channel == 2
        assert config.banks_per_pseudo_channel == 16
        assert config.bank_groups_per_channel == 8
        assert config.row_size == 2048
        assert config.burst_length == 32
        assert config.data_rate == 6.4e9
        assert config.io_width == 1024
        assert config.queue_depth == 32
        assert config.address_mapping == "rbc"
        assert config.scheduler_mode == "fr-fcfs"
        assert config.refresh_interval == 3.9e-6
        assert config.refresh_penalty == 230e-9

    def test_hbm3_is_not_hbm4(self):
        """Test HBM3 is not detected as HBM4"""
        assert HBM3_DEFAULT.is_hbm4 is False


class TestHBM4_DEFAULT:
    """Tests for HBM4_DEFAULT"""

    def test_hbm4_default_values(self):
        """Test HBM4 default values"""
        config = HBM4_DEFAULT

        assert config.channels_per_stack == 32
        assert config.stack_count == 4
        assert config.speed_grade == "8Gbps"
        assert config.tCK_ps == 125.0
        assert config.lane_repair_enabled is True
        assert config.training_enabled is True

    def test_hbm4_is_hbm4(self):
        """Test HBM4 is detected as HBM4"""
        assert HBM4_DEFAULT.is_hbm4 is True

    def test_hbm4_bandwidth(self):
        """Test HBM4 bandwidth calculation"""
        bw = HBM4_DEFAULT.calc_bandwidth()
        # 8.0e9 * 2048 / 8 = 2048 GB/s
        assert bw > 2000


class TestConfigEdgeCases:
    """Edge case tests for config"""

    def test_zero_channels(self):
        """Test config with zero channels (edge case)"""
        config = HBMConfig(channels_per_stack=0)
        assert config.channel_width_bits == 0

    def test_single_channel(self):
        """Test config with single channel"""
        config = HBMConfig(channels_per_stack=1)
        assert config.get_channel_bits() == 0

    def test_single_bank(self):
        """Test config with single bank"""
        config = HBMConfig(banks_per_pseudo_channel=1)
        assert config.get_bank_bits() == 0

    def test_single_stack(self):
        """Test config with single stack"""
        config = HBMConfig(stack_count=1)
        layout = config.get_address_layout()
        assert layout['stack'] >= 1

    def test_effective_bandwidth_zero(self):
        """Test effective bandwidth with zero base"""
        config = HBMConfig(data_rate=0)
        # Should not crash
        bw = config.effective_bandwidth_gbs
        assert bw >= 0

    def test_address_layout_with_large_values(self):
        """Test address layout with large values"""
        config = HBMConfig(
            stack_count=8,
            channels_per_stack=32,
            banks_per_pseudo_channel=32,
            bank_groups_per_channel=16,
        )
        layout = config.get_address_layout()

        assert all(v >= 0 for v in layout.values())


class TestConfigIntegration:
    """Integration tests for config"""

    def test_full_hbm4_workflow(self):
        """Test full HBM4 configuration workflow"""
        # Create from factory
        config = HBMConfig.hbm4_8gbps()

        # Check properties
        assert config.is_hbm4 is True
        assert config.total_channels > 0
        assert config.total_pseudo_channels > 0
        assert config.total_banks > 0

        # Calculate bandwidth
        bw = config.calc_bandwidth()
        assert bw > 0

        total_bw = config.calc_bandwidth_total()
        assert total_bw == bw * config.stack_count

        # Get address layout
        layout = config.get_address_layout()
        assert len(layout) > 0

    def test_config_copy_and_modify(self):
        """Test copying and modifying config"""
        base = HBMConfig.hbm4_8gbps()

        # Copy and modify
        modified = base.copy()
        modified.stack_count = 8
        modified.channels_per_stack = 16

        # Base should be unchanged
        assert base.stack_count == 4
        assert base.channels_per_stack == 32

        # Modified should be changed
        assert modified.stack_count == 8
        assert modified.channels_per_stack == 16

    def test_config_serialization_roundtrip(self):
        """Test dict serialization roundtrip"""
        original = HBMConfig(
            stack_count=4,
            channels_per_stack=32,
            queue_depth=128,
            speed_grade='16Gbps',
        )

        # To dict
        d = original.to_dict()

        # From dict
        restored = HBMConfig.from_dict(d)

        assert restored.stack_count == original.stack_count
        assert restored.channels_per_stack == original.channels_per_stack
        assert restored.queue_depth == original.queue_depth
        assert restored.speed_grade == original.speed_grade
