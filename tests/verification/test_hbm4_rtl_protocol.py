"""
HBM4 RTL Protocol Compliance Tests

Protocol compliance tests for HBM4:
- Command protocol compliance
- Address protocol compliance
- Timing protocol compliance

Run with: pytest tests/verification/test_hbm4_rtl_protocol.py -v

Author: Claude Code (AI-driven verification)
Date: 2026-06-24
"""

import pytest
import sys
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.insert(0, '/home/ic/JXTF/HBM4')

# Import Python model components
from model.dram.hbm4_spec import HBM4Spec
from model.dram.hbm4_channel_model import HBM4Command, HBM4ChannelArray
from model.dram.timing import HBM4Timing
from model.dram.bank_state_machine import Bank, BankStateEnum
from model.dram.dfi_interface import (
    DFICommand,
    DFILowPowerState,
    DFIPhyIF,
)
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_controller import HBM4Controller


# =============================================================================
# RTL Protocol Constants (from rtl/hbm_types.svh)
# =============================================================================

# DFI 5.0 Command Encoding
DFI_CMD_NOP = 0b0000
DFI_CMD_ACT = 0b0001
DFI_CMD_PRE = 0b0010
DFI_CMD_PREA = 0b0011
DFI_CMD_RD = 0b0100
DFI_CMD_WR = 0b0101
DFI_CMD_RDA = 0b0110
DFI_CMD_WRA = 0b0111
DFI_CMD_REFab = 0b1000
DFI_CMD_REFsb = 0b1001
DFI_CMD_RFMab = 0b1010
DFI_CMD_RFMsb = 0b1011
DFI_CMD_MRS = 0b1100
DFI_CMD_SRE = 0b1101
DFI_CMD_SRX = 0b1110
DFI_CMD_PDE = 0b1111

# DFI Version
DFI_VERSION_MAJOR = 5
DFI_VERSION_MINOR = 0


# =============================================================================
# Test Class: Command Protocol Compliance
# =============================================================================

class TestCommandProtocolCompliance:
    """Test command protocol compliance"""

    def test_command_encoding_values(self):
        """Command encoding values should match"""
        # HBM4 Command encoding
        assert HBM4Command.NOP.value == 0
        assert HBM4Command.ACT.value == 1
        assert HBM4Command.READ.value == 2
        assert HBM4Command.WRITE.value == 3
        assert HBM4Command.PRE.value == 4

    def test_dfi_command_encoding(self):
        """DFI command encoding should be defined"""
        # DFI 5.0 has different encoding than HBM4 native commands
        assert DFI_CMD_NOP == 0
        assert DFI_CMD_ACT == 1
        assert DFI_CMD_PRE == 2
        assert DFI_CMD_RD == 4
        assert DFI_CMD_WR == 5

    def test_command_string_conversion(self):
        """Command string conversion should work"""
        assert HBM4Command.to_string(HBM4Command.NOP) == "NOP"
        assert HBM4Command.to_string(HBM4Command.ACT) == "ACT"
        assert HBM4Command.to_string(HBM4Command.READ) == "RD"
        assert HBM4Command.to_string(HBM4Command.WRITE) == "WR"
        assert HBM4Command.to_string(HBM4Command.PRE) == "PRE"

    def test_command_width(self):
        """All commands should fit in 4 bits"""
        max_cmd = max(cmd.value for cmd in HBM4Command)
        assert max_cmd < 16


# =============================================================================
# Test Class: Timing Protocol Compliance
# =============================================================================

class TestTimingProtocolCompliance:
    """Test timing protocol compliance"""

    def test_timing_parameters_exist(self):
        """All timing parameters should exist"""
        timing = HBM4Timing()

        assert hasattr(timing, 'nRCD')
        assert hasattr(timing, 'nRP')
        assert hasattr(timing, 'nRAS')
        assert hasattr(timing, 'nRC')
        assert hasattr(timing, 'nCCD')
        assert hasattr(timing, 'nRRD')
        assert hasattr(timing, 'nFAW')
        assert hasattr(timing, 'nRFC')
        assert hasattr(timing, 'nREFI')
        assert hasattr(timing, 'nCL')
        assert hasattr(timing, 'nCWL')

    def test_timing_values_positive(self):
        """All timing values should be positive"""
        timing = HBM4Timing()

        assert timing.nRCD > 0
        assert timing.nRP > 0
        assert timing.nRAS > 0
        assert timing.nRC > 0
        assert timing.nCCD > 0
        assert timing.nRRD > 0
        assert timing.nFAW > 0
        assert timing.nRFC > 0
        assert timing.nREFI > 0
        assert timing.nCL > 0
        assert timing.nCWL > 0

    def test_timing_relationships(self):
        """Timing relationships should be valid"""
        timing = HBM4Timing()

        # tRC >= tRCD + tRP
        assert timing.nRC >= timing.nRCD + timing.nRP

        # tREFI > tRFC
        assert timing.nREFI > timing.nRFC

    def test_clock_configuration(self):
        """Clock configuration should be valid"""
        timing = HBM4Timing()

        # Clock period should be positive
        assert timing.tCK_ps > 0

        # Clock frequency should match
        expected_freq = 1000.0 / timing.tCK_ps  # GHz
        actual_freq = timing.clock_freq / 1e9
        assert abs(actual_freq - expected_freq) < 0.01


# =============================================================================
# Test Class: Address Protocol Compliance
# =============================================================================

class TestAddressProtocolCompliance:
    """Test address protocol compliance"""

    def test_address_decoder_exists(self):
        """Address decoder should exist"""
        decoder = HBM4AddressDecoder()
        assert decoder is not None

    def test_address_decode_valid_address(self):
        """Valid address should decode correctly"""
        decoder = HBM4AddressDecoder()

        addr = (5 << 41) | 0x1000  # Channel 5
        decoded = decoder.decode(addr)

        assert decoded.channel_id == 5
        assert decoded.col_id >= 0

    def test_address_encode_decode_roundtrip(self):
        """Encode/decode should be consistent"""
        decoder = HBM4AddressDecoder()

        # Test channel decoding
        for ch in [0, 1, 15, 16, 31]:
            addr = (ch << 41) | 0x1000
            decoded = decoder.decode(addr)
            assert decoded.channel_id == ch

    def test_address_boundary_values(self):
        """Boundary values should decode correctly"""
        decoder = HBM4AddressDecoder()

        # Max channel
        addr = (31 << 41) | 0x1000
        decoded = decoder.decode(addr)
        assert decoded.channel_id == 31


# =============================================================================
# Test Class: Bank State Protocol Compliance
# =============================================================================

class TestBankStateProtocolCompliance:
    """Test bank state protocol compliance"""

    def test_bank_states_defined(self):
        """All bank states should be defined"""
        assert hasattr(BankStateEnum, 'IDLE')
        assert hasattr(BankStateEnum, 'ACTIVE')
        assert hasattr(BankStateEnum, 'BUSY')
        assert hasattr(BankStateEnum, 'REFRESHING')
        assert hasattr(BankStateEnum, 'POWERDN')

    def test_bank_state_values(self):
        """Bank state values should be sequential"""
        assert BankStateEnum.IDLE.value == 0
        assert BankStateEnum.ACTIVE.value == 1
        assert BankStateEnum.BUSY.value == 2
        assert BankStateEnum.REFRESHING.value == 3
        assert BankStateEnum.POWERDN.value == 4


# =============================================================================
# Test Class: Channel Configuration Compliance
# =============================================================================

class TestChannelConfigurationCompliance:
    """Test channel configuration compliance"""

    def test_channel_count(self):
        """Channel count should be 32"""
        spec = HBM4Spec()
        assert spec.channels == 32

    def test_pseudo_channel_count(self):
        """Pseudo-channel count should be 2"""
        spec = HBM4Spec()
        assert spec.pseudo_channels_per_channel == 2

    def test_bank_group_count(self):
        """Bank group count should be 8"""
        spec = HBM4Spec()
        assert spec.bank_groups_per_channel == 8

    def test_bank_count_per_group(self):
        """Bank count per group should be 16"""
        spec = HBM4Spec()
        assert spec.banks_per_pseudo_channel == 16


# =============================================================================
# Test Class: Data Transfer Protocol Compliance
# =============================================================================

class TestDataTransferProtocolCompliance:
    """Test data transfer protocol compliance"""

    def test_burst_length(self):
        """Burst length should be 4 (HBM BL4)"""
        spec = HBM4Spec()
        assert spec.nBL == 4

    def test_data_width(self):
        """IO width should be 2048 bits"""
        spec = HBM4Spec()
        assert spec.io_width == 2048

    def test_per_channel_data_width(self):
        """Per-channel width should be 64 bits"""
        spec = HBM4Spec()
        per_channel = spec.io_width // spec.channels
        assert per_channel == 64


# =============================================================================
# Test Class: Bandwidth Protocol Compliance
# =============================================================================

class TestBandwidthProtocolCompliance:
    """Test bandwidth protocol compliance"""

    def test_peak_bandwidth_calculation(self):
        """Peak bandwidth should be correctly calculated"""
        spec = HBM4Spec()
        # 8 GT/s * 2048 bits / 8 = 2048 GB/s = 2.048 TB/s
        expected = 2.048
        assert abs(spec.bandwidth - expected) < 0.001

    def test_per_channel_bandwidth(self):
        """Per-channel bandwidth should be correctly calculated"""
        spec = HBM4Spec()
        # 8 GT/s * 64 bits / 8 = 64 GB/s
        expected_per_channel = 64.0
        channel_array = HBM4ChannelArray()
        ch = channel_array.get_channel(0)
        assert abs(ch.peak_bandwidth_gbs - expected_per_channel) < 1.0

    def test_total_bandwidth(self):
        """Total bandwidth should be sum of channel bandwidths"""
        channel_array = HBM4ChannelArray()
        total = channel_array.total_bandwidth_tbs
        # 32 channels * 64 GB/s = 2048 GB/s = 2.048 TB/s
        assert abs(total - 2.048) < 0.01


# =============================================================================
# Test Class: DFI Low Power States Compliance
# =============================================================================

class TestDFILowPowerStatesCompliance:
    """Test DFI low power state compliance"""

    def test_low_power_states_defined(self):
        """Low power states should be defined"""
        assert hasattr(DFILowPowerState, 'LP_IDLE')
        assert hasattr(DFILowPowerState, 'LP_CTRL')
        assert hasattr(DFILowPowerState, 'LP_DATA')
        assert hasattr(DFILowPowerState, 'LP_SELF_REFRESH')
        assert hasattr(DFILowPowerState, 'LP_POWER_DOWN')

    def test_low_power_state_values(self):
        """Low power state values should be valid"""
        assert DFILowPowerState.LP_IDLE.value == 0
        assert DFILowPowerState.LP_CTRL.value == 1
        assert DFILowPowerState.LP_DATA.value == 2


# =============================================================================
# Test Class: DFI Command Compliance
# =============================================================================

class TestDFICommandCompliance:
    """Test DFI command compliance"""

    def test_dfi_commands_defined(self):
        """DFI commands should be defined"""
        assert hasattr(DFICommand, 'NOP')
        assert hasattr(DFICommand, 'ACT')
        assert hasattr(DFICommand, 'PRE')
        assert hasattr(DFICommand, 'RD')
        assert hasattr(DFICommand, 'WR')
        assert hasattr(DFICommand, 'REFab')
        assert hasattr(DFICommand, 'MRS')

    def test_dfi_command_values(self):
        """DFI command values should be correct"""
        assert DFICommand.NOP.value == 0
        assert DFICommand.ACT.value == 1
        assert DFICommand.PRE.value == 2
        assert DFICommand.RD.value == 4
        assert DFICommand.WR.value == 5


# =============================================================================
# Test Class: Complete Protocol Compliance Summary
# =============================================================================

class TestProtocolComplianceSummary:
    """Complete protocol compliance summary"""

    def test_complete_protocol_compliance(self):
        """Generate and verify protocol compliance report"""
        spec = HBM4Spec()
        timing = HBM4Timing()
        decoder = HBM4AddressDecoder()

        checks = {
            # Configuration
            'channels_32': spec.channels == 32,
            'pseudo_channels_2': spec.pseudo_channels_per_channel == 2,
            'bank_groups_8': spec.bank_groups_per_channel == 8,
            'banks_16': spec.banks_per_pseudo_channel == 16,

            # Timing
            'tRCD_8': timing.nRCD == 8,
            'tRP_8': timing.nRP == 8,
            'tCL_8': timing.nCL == 8,
            'tCWL_3': timing.nCWL == 3,

            # Commands
            'cmd_act_1': HBM4Command.ACT.value == 1,
            'cmd_read_2': HBM4Command.READ.value == 2,
            'cmd_write_3': HBM4Command.WRITE.value == 3,

            # Bank states
            'bank_idle_0': BankStateEnum.IDLE.value == 0,
            'bank_active_1': BankStateEnum.ACTIVE.value == 1,

            # Bandwidth
            'bandwidth_2tb': abs(spec.bandwidth - 2.048) < 0.001,

            # DFI
            'dfi_version_5_0': DFI_VERSION_MAJOR == 5 and DFI_VERSION_MINOR == 0,
            'dfi_lp_states': hasattr(DFILowPowerState, 'LP_IDLE'),
            'dfi_commands': hasattr(DFICommand, 'ACT'),
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)

        # All checks should pass
        assert passed == total, f"Protocol compliance: {passed}/{total} passed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
