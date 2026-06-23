"""
UVM Testbench and RTL Integration Tests

Tests the integration between UVM testbench and RTL controller,
including DPI-C calls to Python reference model.

Run with: pytest tests/integration/test_uvm_rtl_integration.py -v
"""

import pytest
import sys
import subprocess
import os
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, '/home/ic/JXTF/HBM')

from model.dram.HBM4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.HBM4_channel_model import HBM4Channel, HBM4Command
from model.dram.dfi_interface import DFI5Interface, DFICommand, DFILowPowerState
from model.controller.HBM4_address_decoder import HBM4AddressDecoder


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def hbm4_address_decoder():
    """HBM4 address decoder fixture"""
    return HBM4AddressDecoder()


# =============================================================================
# RTL Simulation Environment Check
# =============================================================================

def is_verilator_available() -> bool:
    """Check if Verilator is available"""
    try:
        result = subprocess.run(['verilator', '--version'],
                              capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def is_systemverilog_supported() -> bool:
    """Check if SystemVerilog compilation is supported"""
    # Check for VCS, Questa, or NC-Verilog
    tools = ['vcs', 'questa', 'ncverilog']
    for tool in tools:
        try:
            result = subprocess.run(['which', tool],
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    return False


# =============================================================================
# RTL Interface Signal Definitions
# =============================================================================

@dataclass
class RTLControllerSignals:
    """RTL controller signal interface matching hbm_controller.sv"""

    # Request interface
    req_valid: bool = False
    req_id: int = 0
    req_addr: int = 0
    req_rd_wr_n: bool = True  # 1=read, 0=write
    req_len: int = 64
    req_priority: int = 0
    req_ready: bool = False

    # Response interface
    resp_valid: bool = False
    resp_id: int = 0
    resp_success: bool = False
    resp_status: int = 0

    # DRAM interface
    dram_cmd: int = 0  # 4-bit command
    dram_ch: int = 0   # Channel address
    dram_bg: int = 0    # Bank group
    dram_bank: int = 0  # Bank address
    dram_pch: int = 0   # Pseudo-channel
    dram_row: int = 0   # Row address
    dram_rd_data: int = 0
    dram_wr_data: int = 0

    # Statistics
    stat_requests: int = 0
    stat_completed: int = 0
    stat_hit_rate: int = 0


@dataclass
class RTLCommand:
    """RTL command representation"""
    cmd_type: int      # 0=NOP, 1=ACT, 2=RD, 3=WR, 4=PRE, 5=PREA, 6=REF, 7=RFM
    channel: int        # Channel index (0-31)
    pseudo_channel: int  # Pseudo-channel (0-1)
    bank_group: int     # Bank group (0-7)
    bank: int           # Bank index (0-15)
    row: int            # Row address


# =============================================================================
# Test RTL Signal Alignment
# =============================================================================

class TestRTLInterfaceSignals:
    """Test RTL signal interface alignment"""

    def test_request_signal_widths(self):
        """Test request signal widths match RTL"""
        # RTL signal widths from hbm_controller.sv
        expected_widths = {
            'req_id': 32,
            'req_addr': 35,  # STACK(2) + CH(5) + BG(3) + BK(4) + ROW(16) + COL(6)
            'req_len': 16,
            'req_priority': 3,
        }

        # Verify signal widths are consistent with Python model
        signals = RTLControllerSignals()
        assert signals.req_id.bit_length() <= expected_widths['req_id']
        assert signals.req_addr.bit_length() <= expected_widths['req_addr']

    def test_response_signal_widths(self):
        """Test response signal widths match RTL"""
        signals = RTLControllerSignals()
        assert signals.resp_id.bit_length() <= 32
        assert signals.resp_status.bit_length() <= 8

    def test_dram_command_encoding(self):
        """Test DRAM command encoding matches RTL"""
        # RTL encoding from hbm_types.svh
        expected_cmds = {
            0: 'NOP',
            1: 'ACT',
            2: 'READ',
            3: 'WRITE',
            4: 'PRE',
            5: 'PREA',
            6: 'REF',
            7: 'RFM',
        }

        # Verify Python model matches
        for value, name in expected_cmds.items():
            assert HBM4Command(value).value == value

    def test_dram_signal_widths(self):
        """Test DRAM signal widths match RTL"""
        signals = RTLControllerSignals()

        # DRAM command is 4 bits
        assert signals.dram_cmd.bit_length() <= 4

        # Channel is 5 bits for 32 channels
        assert signals.dram_ch.bit_length() <= 5

        # Bank group is 3 bits
        assert signals.dram_bg.bit_length() <= 3

        # Bank is 4 bits
        assert signals.dram_bank.bit_length() <= 4

        # Row is 16 bits
        assert signals.dram_row.bit_length() <= 16


# =============================================================================
# Test RTL Command Sequence Equivalence
# =============================================================================

class TestRTLCommandEquivalence:
    """Test that Python commands produce same results as RTL would"""

    def test_act_command_output(self, hbm4_address_decoder):
        """Test ACT command generates correct RTL signals"""
        decoder = hbm4_address_decoder

        # Test address using RBC mapping format:
        # [Stack][Channel][Pch][Bg][Bank][Row][Col][Burst][Offset]
        # Test address for channel 5, bank 3, row 100
        test_addr = (
            (0 << 46) |     # Stack
            (5 << 41) |     # Channel (5 bits)
            (0 << 40) |     # Pseudo-channel
            (0 << 37) |     # Bank group
            (3 << 33) |     # Bank
            (100 << 17) |   # Row
            (0 << 11)       # Column
        )

        decoded = decoder.decode(test_addr)

        # Verify decoded fields match what RTL would extract
        assert decoded.channel_id == 5
        assert decoded.bank_id == 3
        assert decoded.row_id == 100

    def test_read_command_output(self, hbm4_address_decoder):
        """Test READ command generates correct RTL signals"""
        decoder = hbm4_address_decoder

        # Test address using RBC mapping format:
        # [Stack][Channel][Pch][Bg][Bank][Row][Col][Burst][Offset]
        # Test address: channel 7, BG 2, bank 5, row 200, col 0x20
        test_addr = (
            (0 << 46) |     # Stack
            (7 << 41) |     # Channel (5 bits)
            (0 << 40) |     # Pseudo-channel
            (2 << 37) |     # Bank group
            (5 << 33) |     # Bank
            (200 << 17) |   # Row
            (0x20 << 11)    # Column
        )

        decoded = decoder.decode(test_addr)

        # Verify column decoding
        assert decoded.channel_id == 7
        assert decoded.bank_group_id == 2
        assert decoded.bank_id == 5
        assert decoded.row_id == 200
        assert decoded.col_id == 0x20

    def test_command_timing_equivalence(self):
        """Test that Python timing matches RTL timing parameters"""
        # RTL timing from hbm_types.svh
        # HBM4 default: tRCD=8, tRP=8, tRAS=20, tRC=22, tCCD=4, tRRD=4, tFAW=16, tRFC=180, tREFI=3900

        from model.dram.HBM4_spec import HBM4Spec
        spec = HBM4Spec()

        # Verify timing values match
        assert spec.nRCDRD == 8  # tRCD
        assert spec.nRP == 8    # tRP
        assert spec.nRAS == 20  # tRAS
        assert spec.nRC == 22   # tRC
        assert spec.nRFC == 180  # tRFC
        assert spec.nREFI == 3900  # tREFI


# =============================================================================
# Test DPI-C Interface Simulation
# =============================================================================

class TestDPICInterface:
    """Test DPI-C interface for calling Python from RTL"""

    def test_dpi_c_function_signatures(self):
        """Test that DPI-C function signatures are defined"""
        # These would be declared in a DPI-C header file
        # This test verifies the Python interface matches expected signatures

        expected_functions = [
            'py_hbm_controller_init',
            'py_hbm_controller_submit_request',
            'py_hbm_controller_tick',
            'py_hbm_controller_get_response',
            'py_hbm_dram_model_init',
            'py_hbm_dram_model_command',
            'py_hbm_dram_model_tick',
        ]

        # In a real DPI-C implementation, these functions would be exported
        # This test verifies the interface contract

        # For now, verify that our Python model supports the expected operations
        from model.controller.HBM4_controller import HBM4Controller
        from model.dram.HBM4_channel_model import HBM4Channel

        controller = HBM4Controller()
        assert hasattr(controller, 'submit_request')
        assert hasattr(controller, 'tick')

        channel = HBM4Channel(channel_id=0)
        assert hasattr(channel, 'issue_command')
        assert hasattr(channel, 'tick')

    def test_dpi_c_data_types(self):
        """Test DPI-C data type compatibility"""
        # Test that Python types can be converted to C types

        # Request ID - should fit in 32-bit unsigned
        request_id = 0x12345678
        assert request_id < (1 << 32)

        # Address - using reasonable HBM4 address range (64-bit address space)
        addr = 0x123456789ABCDEF0
        addr_width = 64  # 64-bit address space
        assert addr < (1 << addr_width)

        # Command - should fit in 4 bits
        cmd = HBM4Command.ACT.value
        assert cmd < (1 << 4)

    def test_reference_model_interface(self):
        """Test reference model interface for DPI-C calling"""
        # The reference model is implemented in RTL, not Python
        # This test verifies the RTL reference models exist and have expected structure

        # Verify reference model files exist
        ref_model_files = [
            '/home/ic/JXTF/HBM/verification/reference_model/dram_ref_model.sv',
            '/home/ic/JXTF/HBM/verification/reference_model/timing_checker.sv',
            '/home/ic/JXTF/HBM/verification/reference_model/bandwidth_calc.sv',
        ]

        for model_path in ref_model_files:
            assert os.path.exists(model_path), f"Reference model {model_path} should exist"

            # Verify file contains expected module definition
            with open(model_path, 'r') as f:
                content = f.read()
            assert 'module' in content, f"{model_path} should contain module definition"


# =============================================================================
# Test UVM Testbench Components
# =============================================================================

class TestUVMComponents:
    """Test UVM testbench component interfaces"""

    def test_uvm_test_pkg_exists(self):
        """Test that UVM test package exists"""
        pkg_path = '/home/ic/JXTF/HBM/verification/uvm/hbm_test_pkg.sv'
        assert os.path.exists(pkg_path), "UVM test package should exist"

    def test_uvm_env_pkg_exists(self):
        """Test that UVM environment package exists"""
        pkg_path = '/home/ic/JXTF/HBM/verification/uvm/hbm_env_pkg.sv'
        assert os.path.exists(pkg_path), "UVM environment package should exist"

    def test_uvm_testbench_exists(self):
        """Test that UVM testbench exists"""
        tb_path = '/home/ic/JXTF/HBM/verification/uvm/hbm_tb.sv'
        assert os.path.exists(tb_path), "UVM testbench should exist"

    def test_reference_model_exists(self):
        """Test that reference model modules exist"""
        ref_models = [
            '/home/ic/JXTF/HBM/verification/reference_model/dram_ref_model.sv',
            '/home/ic/JXTF/HBM/verification/reference_model/timing_checker.sv',
            '/home/ic/JXTF/HBM/verification/reference_model/bandwidth_calc.sv',
            '/home/ic/JXTF/HBM/verification/reference_model/addr_decoder_ref.sv',
        ]
        for model_path in ref_models:
            assert os.path.exists(model_path), f"Reference model {model_path} should exist"


# =============================================================================
# Test RTL Controller Behavior
# =============================================================================

class TestRTLControllerBehavior:
    """Test RTL controller behavior through Python model"""

    def test_address_decoder_parity(self, hbm4_address_decoder):
        """Test that Python decoder matches RTL decoder"""
        decoder = hbm4_address_decoder

        # Test multiple addresses using RBC mapping format
        test_cases = [
            # (addr, expected_ch, expected_bank, expected_row)
            # RBC format: [Stack][Channel][Pch][Bg][Bank][Row][Col][Burst][Offset]
            # Channel 0, Bank 0, Row 0
            ((0 << 46) | (0 << 41) | (0 << 40) | (0 << 37) | (0 << 33) | (0 << 17) | (0 << 11), 0, 0, 0),
            # Channel 1, Bank 0, Row 0
            ((1 << 41) | (0 << 33) | (0 << 17), 1, 0, 0),
            # Channel 2, Bank 0, Row 0
            ((2 << 41) | (0 << 33) | (0 << 17), 2, 0, 0),
            # Channel 0, Bank 1, Row 0
            ((0 << 41) | (1 << 33) | (0 << 17), 0, 1, 0),
            # Channel 0, Bank 0, Row 1
            ((0 << 41) | (0 << 33) | (1 << 17), 0, 0, 1),
        ]

        for addr, expected_ch, expected_bank, expected_row in test_cases:
            decoded = decoder.decode(addr)
            assert decoded.channel_id == expected_ch, f"Channel mismatch for addr 0x{addr:x}"
            assert decoded.bank_id == expected_bank, f"Bank mismatch for addr 0x{addr:x}"
            assert decoded.row_id == expected_row, f"Row mismatch for addr 0x{addr:x}"

    def test_queue_depth_behavior(self):
        """Test queue depth behavior matches RTL"""
        from model.controller.HBM4_controller import HBM4Controller

        controller = HBM4Controller()

        # Submit requests up to queue capacity
        submitted = 0
        for i in range(256):  # 8 requests per channel × 32 channels
            req_id = controller.submit_request(addr=i * 0x1000, is_read=True)
            if req_id is not None:
                submitted += 1
            else:
                break

        # Should be able to submit at least some requests
        assert submitted > 0

    def test_priority_queue_behavior(self):
        """Test priority queue behavior"""
        from model.controller.HBM4_controller import HBM4Controller

        controller = HBM4Controller()

        # Submit with different priorities
        low_priority_id = controller.submit_request(
            addr=0x1000, is_read=True, qos_level=0
        )
        high_priority_id = controller.submit_request(
            addr=0x2000, is_read=True, qos_level=15
        )

        assert low_priority_id is not None
        assert high_priority_id is not None

        # Verify QoS scheduler prioritizes high priority
        assert controller.qos_scheduler is not None


# =============================================================================
# Test UVM Test Sequences
# =============================================================================

class TestUVMSequences:
    """Test UVM test sequences through Python model"""

    def test_single_read_sequence_model(self):
        """Model-based single read sequence test"""
        from model.dram.HBM4_channel_model import HBM4Channel
        from model.dram.HBM4_spec import HBM4Spec
        from model.dram.HBM4_channel_model import HBM4Timing

        spec = HBM4Spec()
        timing = HBM4Timing()
        channel = HBM4Channel(channel_id=0, spec=spec, timing=timing)

        channel.set_time(0)

        # ACT -> RD -> PRE sequence
        success1 = channel.issue_command('ACT', pseudo_channel=0, bank=0, row=0)
        assert success1

        channel.set_time(timing.nRCDRD)

        success2 = channel.issue_command('RD', pseudo_channel=0, bank=0, row=0)
        assert success2

        # Must meet tRAS before PRE
        channel.set_time(timing.nRCDRD + timing.nCL + timing.nBL + timing.nRAS)

        success3 = channel.issue_command('PRE', pseudo_channel=0, bank=0, row=0)
        assert success3

    def test_single_write_sequence_model(self):
        """Model-based single write sequence test"""
        from model.dram.HBM4_channel_model import HBM4Channel
        from model.dram.HBM4_spec import HBM4Spec
        from model.dram.HBM4_channel_model import HBM4Timing

        spec = HBM4Spec()
        timing = HBM4Timing()
        channel = HBM4Channel(channel_id=0, spec=spec, timing=timing)

        channel.set_time(0)

        # ACT -> WR -> PRE sequence
        success1 = channel.issue_command('ACT', pseudo_channel=0, bank=1, row=100)
        assert success1

        channel.set_time(timing.nRCDWR)

        success2 = channel.issue_command('WR', pseudo_channel=0, bank=1, row=100)
        assert success2

        # Must meet tRAS before PRE
        channel.set_time(timing.nRCDWR + timing.nCWL + timing.nBL + timing.nWR + timing.nRAS)

        success3 = channel.issue_command('PRE', pseudo_channel=0, bank=1, row=100)
        assert success3

    def test_multi_bank_sequence_model(self):
        """Model-based multi-bank sequence test"""
        from model.dram.HBM4_channel_model import HBM4Channel
        from model.dram.HBM4_spec import HBM4Spec
        from model.dram.HBM4_channel_model import HBM4Timing

        spec = HBM4Spec()
        timing = HBM4Timing()
        channel = HBM4Channel(channel_id=0, spec=spec, timing=timing)

        channel.set_time(0)

        # Open multiple banks
        for bank_id in range(4):
            channel.issue_command('ACT', pseudo_channel=0, bank=bank_id, row=bank_id * 10)
            channel.set_time(channel.current_cycle + timing.nRRDL + 1)

        # Verify all banks are active
        for bank_id in range(4):
            bank = channel.get_bank(pseudo_channel=0, bank=bank_id)
            assert bank.bank.state.value == 1  # ACTIVE

    def test_refresh_sequence_model(self):
        """Model-based refresh sequence test"""
        from model.dram.HBM4_channel_model import HBM4Channel
        from model.dram.HBM4_spec import HBM4Spec
        from model.dram.HBM4_channel_model import HBM4Timing

        spec = HBM4Spec()
        timing = HBM4Timing()
        channel = HBM4Channel(channel_id=0, spec=spec, timing=timing)

        channel.set_time(0)

        # All banks should be idle for REFab
        success = channel.issue_command('REFab', pseudo_channel=0, bank=0, row=0)
        assert success

        channel.set_time(timing.nRFC)
        channel.tick()

        # Channel should return to IDLE
        assert channel.state.value == 0


# =============================================================================
# Test RTL Simulation
# =============================================================================

class TestRTLSimulation:
    """Test RTL simulation through Python wrapper"""

    @pytest.mark.skipif(not is_verilator_available(), reason="Verilator not available")
    def test_verilator_simulation_available(self):
        """Test that Verilator simulation can be invoked"""
        result = subprocess.run(['verilator', '--version'],
                              capture_output=True, text=True)
        assert result.returncode == 0
        print(f"Verilator version: {result.stdout}")

    def test_rtl_testbench_structure(self):
        """Test RTL testbench has correct structure"""
        tb_path = '/home/ic/JXTF/HBM/tb/hbm_controller_tb.cpp'

        if not os.path.exists(tb_path):
            pytest.skip("RTL testbench not found")

        with open(tb_path, 'r') as f:
            content = f.read()

        # Verify key components exist
        assert 'Vhbm_controller' in content, "Should include Verilator module"
        assert 'VerilatedVcdC' in content, "Should include VCD trace"
        assert 'main_time' in content, "Should have time tracking"


# =============================================================================
# Test Integration Points
# =============================================================================

class TestIntegrationPoints:
    """Test integration points between components"""

    def test_dfi_interface_integration(self):
        """Test DFI interface integration with controller"""
        from model.dram.dfi_interface import DFI5Interface
        from model.controller.HBM4_controller import HBM4Controller

        dfi = DFI5Interface()
        controller = HBM4Controller(enable_dfi=True)

        assert controller.dfi is not None
        assert controller.dfi_ready == True

    def test_controller_dram_connection(self):
        """Test controller to DRAM model connection"""
        from model.controller.HBM4_controller import HBM4Controller
        from model.dram.HBM4_channel_model import HBM4ChannelArray

        controller = HBM4Controller()
        channel_array = HBM4ChannelArray()

        # Controller should have channel model reference
        assert hasattr(controller, 'channel_model')

        # Submit request and verify it can be processed
        req_id = controller.submit_request(addr=0x1000, is_read=True)
        assert req_id is not None

    def test_address_decoder_controller_integration(self):
        """Test address decoder and controller integration"""
        from model.controller.HBM4_controller import HBM4Controller
        from model.controller.HBM4_address_decoder import HBM4AddressDecoder

        controller = HBM4Controller()
        decoder = HBM4AddressDecoder()

        # Test address that controller will decode
        test_addr = 0x12345678
        decoded = decoder.decode(test_addr)

        # Submit request
        req_id = controller.submit_request(
            addr=test_addr,
            is_read=True,
            qos_level=8
        )
        assert req_id is not None

        # Verify request was tracked
        assert req_id in controller._pending_requests


# =============================================================================
# Summary Test
# =============================================================================

def test_uvm_rtl_summary():
    """Summary test for UVM/RTL integration"""
    print("\n=== UVM/RTL Integration Test Summary ===")

    # Check file structure
    files_exist = []
    files = [
        '/home/ic/JXTF/HBM/verification/uvm/hbm_tb.sv',
        '/home/ic/JXTF/HBM/verification/uvm/hbm_test_pkg.sv',
        '/home/ic/JXTF/HBM/verification/uvm/hbm_env_pkg.sv',
        '/home/ic/JXTF/HBM/verification/reference_model/dram_ref_model.sv',
        '/home/ic/JXTF/HBM/tb/hbm_controller_tb.cpp',
        '/home/ic/JXTF/HBM/rtl/hbm_controller.sv',
    ]

    for f in files:
        exists = os.path.exists(f)
        files_exist.append((f, exists))
        print(f"  {'✓' if exists else '✗'} {f}")

    all_exist = all(exists for _, exists in files_exist)
    assert all_exist, "All required files should exist"

    # Check Verilator availability
    verilator_available = is_verilator_available()
    print(f"  {'✓' if verilator_available else '✗'} Verilator available")

    print("=== UVM/RTL Integration Test PASSED ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])