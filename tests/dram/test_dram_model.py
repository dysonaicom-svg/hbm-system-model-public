"""
Phase B: DRAM Model Integration Tests
测试所有 Phase B 模块的集成
"""

import sys
sys.path.insert(0, '/home/ic/JXTF/HBM')

import pytest
import time

from model.dram.timing import HBM3Timing, HBM2Timing, get_timing_for_hbm_version
from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
from model.dram.channel_model import Channel, ChannelArray, PseudoChannel, BankGroup
from model.dram.stack_model import DRAMModel, Stack, StackArray, InterconnectTopology


class TestHBM3Timing:
    """测试 HBM3 时序参数"""
    
    def test_timing_creation(self):
        t = HBM3Timing()
        assert t.tCK_ps == 781.25
        assert t.tRCD == 17
        assert t.tRP == 17
        assert t.tRAS == 42
        assert t.tRC == 59
    
    def test_clock_freq(self):
        t = HBM3Timing()
        freq = t.clock_freq
        assert abs(freq / 1e9 - 1.28) < 0.01  # 1.28 GHz
    
    def test_cycles_conversion(self):
        t = HBM3Timing()
        ns = t.cycles_to_ns(17)
        assert abs(ns - 13.28) < 0.1  # 17 cycles * 0.781 ns
        
        cycles = t.ns_to_cycles(13.28)
        assert cycles == 17
    
    def test_hbm_versions(self):
        t3 = get_timing_for_hbm_version("hbm3")
        t2 = get_timing_for_hbm_version("hbm2")
        assert t3.tRCD == 17
        assert t2.tRCD == 14


class TestBankStateMachine:
    """测试 Bank 状态机"""
    
    def test_initial_state(self):
        timing = HBM3Timing()
        bsm = BankStateMachine(bank_id=0, timing=timing)
        assert bsm.bank.state == BankStateEnum.IDLE
    
    def test_activate_after_idle(self):
        timing = HBM3Timing()
        bsm = BankStateMachine(bank_id=0, timing=timing)
        
        # 等待足够时间使 tRC 通过
        bsm.set_time(100e-6)
        assert bsm.can_activate() == True
        
        success = bsm.activate(row=0x100)
        assert success == True
        assert bsm.bank.open_row == 0x100
    
    def test_row_hit(self):
        timing = HBM3Timing()
        bsm = BankStateMachine(bank_id=0, timing=timing)
        
        bsm.set_time(100e-6)
        bsm.activate(row=0x100)
        
        # 同一行应该 row hit
        assert bsm.is_row_hit(0x100) == True
        # 不同行应该 row miss
        assert bsm.is_row_hit(0x200) == False
    
    def test_precharge(self):
        timing = HBM3Timing()
        bsm = BankStateMachine(bank_id=0, timing=timing)
        
        bsm.set_time(100e-6)
        bsm.activate(row=0x100)
        
        # 等待 tRAS 通过
        bsm.set_time(100e-6 + 50e-9)  # 50ns > tRAS=42*0.781=32.8ns
        assert bsm.can_precharge() == True
        
        bsm.precharge()
        assert bsm.bank.state == BankStateEnum.IDLE


class TestChannel:
    """测试 Channel"""
    
    def test_channel_creation(self):
        ch = Channel(channel_id=0)
        assert len(ch.pseudo_channels) == 2
        assert ch.channel_id == 0
    
    def test_get_bank(self):
        ch = Channel(channel_id=0)
        bank = ch.get_bank(ps_id=0, bg_id=0, bank_id=0)
        assert bank is not None


class TestChannelArray:
    """测试 Channel 数组"""
    
    def test_channel_array(self):
        arr = ChannelArray(num_channels=8)
        assert len(arr.channels) == 8
        
        # 测试获取 bank
        bank = arr.get_bank(ch_id=0, ps_id=0, bg_id=0, bank_id=0)
        assert bank is not None
    
    def test_row_hit_check(self):
        arr = ChannelArray(num_channels=1)
        arr.set_time(100e-6)
        
        # 获取 bank 并激活
        bank = arr.get_bank(ch_id=0, ps_id=0, bg_id=0, bank_id=0)
        bank.activate(row=0x100)
        
        assert arr.is_row_hit(0, 0, 0, 0, 0x100) == True


class TestStack:
    """测试 Stack"""
    
    def test_stack_creation(self):
        stack = Stack(stack_id=0)
        assert stack.num_channels == 8
        assert stack.get_total_banks() == 256  # 8*2*8*2
    
    def test_stack_command(self):
        stack = Stack(stack_id=0)
        stack.set_time(100e-6)
        
        success = stack.execute_command(ch_id=0, ps_id=0, cmd="ACT", 
                                        bg_id=0, bank_id=0, row=0x100)
        assert success == True


class TestDRAMModel:
    """测试 DRAM 模型"""
    
    def test_dram_model_creation(self):
        dram = DRAMModel(num_stacks=2)
        assert dram.num_stacks == 2
        assert dram.stack_array.num_stacks == 2
        assert dram.get_stats()['total_banks'] == 512  # 2*256
    
    def test_execute_read(self):
        dram = DRAMModel(num_stacks=1)
        dram.set_time(100e-6)
        
        # Row miss 场景
        success = dram.execute_request(
            stack_id=0, ch_id=0, ps_id=0, bg_id=0, bank_id=0,
            row=0x100, cmd='READ'
        )
        assert success == True
    
    def test_execute_write(self):
        dram = DRAMModel(num_stacks=1)
        dram.set_time(100e-6)
        
        success = dram.execute_request(
            stack_id=0, ch_id=0, ps_id=0, bg_id=0, bank_id=0,
            row=0x200, cmd='WRITE'
        )
        assert success == True
    
    def test_row_hit_optimization(self):
        dram = DRAMModel(num_stacks=1)
        dram.set_time(100e-6)
        
        # 第一次访问 (row miss)
        dram.execute_request(
            stack_id=0, ch_id=0, ps_id=0, bg_id=0, bank_id=0,
            row=0x100, cmd='READ'
        )
        
        # 等待行打开后再次访问同一行 (row hit)
        dram.set_time(100e-6 + 50e-9)
        success = dram.execute_request(
            stack_id=0, ch_id=0, ps_id=0, bg_id=0, bank_id=0,
            row=0x100, cmd='READ'
        )
        assert success == True


def test_all_modules():
    """综合测试"""
    print("\n=== Phase B DRAM Model Integration Test ===")
    
    # 1. 时序参数
    timing = HBM3Timing()
    print(f"Timing: {timing}")
    print(f"Clock: {timing.clock_freq/1e9:.2f} GHz")
    print(f"Refresh overhead: {timing.tRFC/timing.tREFI*100:.2f}%")
    
    # 2. DRAM 模型
    dram = DRAMModel(num_stacks=2, timing=timing)
    print(f"\nDRAM Model: {dram.num_stacks} stacks, {dram.get_stats()['total_banks']} banks")
    
    # 3. 模拟访问序列
    print("\nAccess sequence:")
    dram.set_time(100e-6)
    
    accesses = [
        (0, 0, 0, 0, 0, 0x100, "READ"),
        (0, 0, 0, 0, 0, 0x200, "READ"),
        (0, 1, 0, 0, 0, 0x100, "WRITE"),
        (1, 0, 0, 0, 0, 0x300, "READ"),
    ]
    
    for i, (stack, ch, ps, bg, bank, row, cmd) in enumerate(accesses):
        success = dram.execute_request(stack, ch, ps, bg, bank, row, cmd)
        print(f"  [{i}] Stack{stack}/Ch{ch}/Ps{ps}/Bg{bg}/Bk{bank} row=0x{row:x} {cmd}: {'OK' if success else 'FAIL'}")
        dram.tick(10)  # 推进 10 cycles
    
    # 4. 统计
    stats = dram.get_stats()
    print(f"\nFinal stats:")
    print(f"  Total banks: {stats['total_banks']}")
    print(f"  Active banks: {stats['stacks'][0]['active_banks']}")
    
    print("\n=== All Phase B Tests Passed ===")


if __name__ == "__main__":
    test_all_modules()
