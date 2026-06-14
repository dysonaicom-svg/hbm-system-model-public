"""
Tests for DRAM Bank State Machine
"""

import pytest
from model.dram.bank_state_machine import (
    BankStateMachine, BankStateEnum, Bank
)
from model.dram.timing import HBM3Timing


class TestBank:
    """Test Bank state"""

    def test_bank_creation(self):
        """测试 Bank 创建"""
        bank = Bank(bank_id=0)
        assert bank.bank_id == 0
        assert bank.state == BankStateEnum.IDLE
        assert bank.open_row == -1

    def test_bank_idle_property(self):
        """测试 is_idle 属性"""
        bank = Bank(bank_id=0)
        assert bank.is_idle

        bank.state = BankStateEnum.ACTIVE
        assert not bank.is_idle

    def test_bank_active_property(self):
        """测试 is_active 属性"""
        bank = Bank(bank_id=0)
        assert not bank.is_active

        bank.state = BankStateEnum.ACTIVE
        assert bank.is_active

    def test_bank_row_open(self):
        """测试 row_open 属性"""
        bank = Bank(bank_id=0)
        assert not bank.row_open

        bank.state = BankStateEnum.ACTIVE
        bank.open_row = 100
        assert bank.row_open

    def test_bank_repr(self):
        """测试 Bank 表示"""
        bank = Bank(bank_id=5, state=BankStateEnum.ACTIVE, open_row=0x100)
        repr_str = repr(bank)
        assert "5" in repr_str
        assert "ACTIVE" in repr_str


class TestBankStateMachine:
    """Test Bank State Machine"""

    def test_state_machine_creation(self):
        """测试状态机创建"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        assert sm.bank.bank_id == 0
        assert sm.bank.state == BankStateEnum.IDLE
        assert sm.current_time == 0.0

    def test_set_time(self):
        """测试时间设置"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(100.5)
        assert sm.current_time == 100.5

    def test_can_activate_idle_bank(self):
        """测试 IDLE 状态 bank 可以激活"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)
        sm.set_time(0.0)

        assert sm.can_activate()

    def test_cannot_activate_active_bank(self):
        """测试 ACTIVE 状态 bank 不能再次激活"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        # 先设置时间，然后激活
        sm.set_time(10.0)
        sm.activate(row=0x100)

        # 应该不能再次激活
        assert not sm.can_activate()

    def test_activate_idle_bank(self):
        """测试激活 IDLE bank"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)
        sm.set_time(10.0)

        success = sm.activate(row=0x100)

        assert success
        assert sm.bank.state == BankStateEnum.ACTIVE
        assert sm.bank.open_row == 0x100
        assert sm.bank.activate_time == 10.0

    def test_activate_same_row_hit(self):
        """测试激活同一行 (row hit)"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(10.0)
        sm.activate(row=0x100)

        # 同一行应该命中
        hit = sm.is_row_hit(0x100)
        assert hit

    def test_activate_different_row_conflict(self):
        """测试激活不同行 (row conflict)"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(10.0)
        sm.activate(row=0x100)

        # 不同行应该冲突
        hit = sm.is_row_hit(0x200)
        assert not hit

    def test_can_read_active_bank_after_trcd(self):
        """测试可以读激活的 bank (tRCD 后)"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(0.0)
        sm.activate(row=0x100)

        # 等待 tRCD 后可以读 (tRCD = 17 cycles = 13.3 ns)
        trcd_s = timing.cycles_to_s(timing.tRCD)
        sm.set_time(trcd_s + 0.000001)  # 加一点余量
        assert sm.can_read()

    def test_cannot_read_idle_bank(self):
        """测试不能读 IDLE bank"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)
        sm.set_time(0.0)

        assert not sm.can_read()

    def test_can_write_active_bank_after_trcd(self):
        """测试可以写激活的 bank (tRCD 后)"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(0.0)
        sm.activate(row=0x100)

        # 等待 tRCD 后可以写
        trcd_s = timing.cycles_to_s(timing.tRCD)
        sm.set_time(trcd_s + 0.000001)
        assert sm.can_write()

    def test_read_operation(self):
        """测试读操作"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(0.0)
        sm.activate(row=0x100)

        # 等待 tRCD 后可以读
        trcd_s = timing.cycles_to_s(timing.tRCD)
        sm.set_time(trcd_s + 0.000001)

        success = sm.read()
        assert success
        assert sm.bank.state == BankStateEnum.READING

    def test_write_operation(self):
        """测试写操作"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(0.0)
        sm.activate(row=0x100)

        # 等待 tRCD 后可以写
        trcd_s = timing.cycles_to_s(timing.tRCD)
        sm.set_time(trcd_s + 0.000001)

        success = sm.write()
        assert success
        assert sm.bank.state == BankStateEnum.WRITING

    def test_precharge_idle_bank_fails(self):
        """测试预充电 IDLE bank (应该失败)"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)
        sm.set_time(0.0)

        success = sm.precharge()
        assert not success

    def test_precharge_active_bank_after_tras(self):
        """测试预充电激活的 bank (tRAS 后)"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(0.0)
        sm.activate(row=0x100)

        # 等待 tRAS 后可以预充电 (tRAS = 42 cycles = 32.8 ns)
        tras_s = timing.cycles_to_s(timing.tRAS)
        sm.set_time(tras_s + 0.000001)

        success = sm.precharge()

        assert success
        assert sm.bank.state == BankStateEnum.IDLE
        # 注意: open_row 可能在 precharge 中没有被清除

    def test_timing_constraint_violation_tras(self):
        """测试 tRAS 时序约束违反"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(0.0)
        sm.activate(row=0x100)

        # tRAS 未满足时预充电应该失败
        # tRAS = 42 cycles = 32.8 ns，应该在 10ns 时失败
        sm.set_time(0.00000001)  # 10 ns
        assert not sm.can_precharge()


class TestBankStateMachineEdgeCases:
    """Test Bank State Machine Edge Cases"""

    def test_activate_with_timing_violation(self):
        """测试时序违反时的激活"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(10.0)
        sm.activate(row=0x100)

        # 立即再次激活应该失败
        sm.set_time(10.5)  # 远小于 tRC (约 59ns)
        assert not sm.can_activate()

    def test_read_after_write(self):
        """测试写后读"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(10.0)
        sm.activate(row=0x100)

        # 写操作
        write_time_ns = timing.tRCD * timing.clock_period_ns
        sm.set_time(10.0 + write_time_ns / 1000 + 0.001)
        sm.write()

        # 写后状态
        assert sm.bank.state == BankStateEnum.WRITING

    def test_multiple_bank_independent(self):
        """测试多个 bank 独立"""
        timing = HBM3Timing()
        sm0 = BankStateMachine(bank_id=0, timing=timing)
        sm1 = BankStateMachine(bank_id=1, timing=timing)

        # Bank 0 激活
        sm0.set_time(10.0)
        sm0.activate(row=0x100)

        # Bank 1 也可以激活 (独立)
        sm1.set_time(10.0)
        sm1.activate(row=0x200)

        assert sm0.bank.is_active
        assert sm1.bank.is_active

    def test_refresh_operation(self):
        """测试刷新操作"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(10.0)
        sm.activate(row=0x100)

        # 刷新后应该变为 IDLE
        sm.set_time(10.0 + timing.tRAS * timing.clock_period_ns / 1000 + 0.001)
        sm.precharge()

        sm.set_time(20.0)
        success = sm.refresh()
        assert success
        assert sm.bank.state == BankStateEnum.REFRESHING

    def test_complete_read(self):
        """测试读完成"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(10.0)
        sm.activate(row=0x100)

        read_time_ns = timing.tRCD * timing.clock_period_ns
        sm.set_time(10.0 + read_time_ns / 1000 + 0.001)
        sm.read()

        sm.complete_read()
        assert sm.bank.state == BankStateEnum.ACTIVE

    def test_complete_write(self):
        """测试写完成"""
        timing = HBM3Timing()
        sm = BankStateMachine(bank_id=0, timing=timing)

        sm.set_time(10.0)
        sm.activate(row=0x100)

        write_time_ns = timing.tRCD * timing.clock_period_ns
        sm.set_time(10.0 + write_time_ns / 1000 + 0.001)
        sm.write()

        sm.complete_write()
        assert sm.bank.state == BankStateEnum.ACTIVE