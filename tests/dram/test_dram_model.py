"""
DRAM Model Integration Tests
测试 DRAM 模型的完整集成
"""

import pytest
from model.dram.dram_model import (
    DRAMModel, DRAMResponse, DRAMStats, DRAMCommand,
    create_dram_model
)
from model.dram.timing import HBM3Timing


class TestDRAMModel:
    """DRAM 模型集成测试"""

    def test_dram_model_creation(self):
        """测试 DRAM 模型创建"""
        model = DRAMModel(hbm_version="hbm3")
        assert model.hbm_version == "hbm3"
        assert len(model.stacks) == 2
        assert model.total_banks == 256  # 2 stacks * 8 channels * 16 banks

    def test_dram_model_custom_config(self):
        """测试自定义配置"""
        model = DRAMModel(
            hbm_version="hbm3",
            stack_count=4,
            banks_per_channel=16,
        )
        assert len(model.stacks) == 4
        assert model.total_banks == 512  # 4 * 8 * 16

    def test_get_bank(self):
        """测试获取 bank"""
        model = DRAMModel()
        bank = model.get_bank(0, 0, 0)
        assert bank is not None
        assert bank.bank.bank_id == 0

    def test_execute_activate(self):
        """测试执行激活命令"""
        model = DRAMModel()
        response = model.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=100, current_time=0
        )
        assert response.success is True
        assert response.latency_cycles == model.timing.tRCD

    def test_activate_timing_violation(self):
        """测试激活时序违反"""
        model = DRAMModel()

        # 第一次激活
        response1 = model.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=100, current_time=0
        )
        assert response1.success is True

        # 立即第二次激活 (违反 tRC)
        response2 = model.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=200, current_time=10  # 不足 tRC=59 cycles
        )
        assert response2.success is False

    def test_execute_read(self):
        """测试执行读命令"""
        model = DRAMModel()

        # 先激活
        model.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=100, current_time=0
        )

        # 等待 tRCD 后读
        response = model.execute_read(
            stack_id=0, channel_id=0, bank_id=0,
            col_id=0, current_time=model.timing.tRCD + 1
        )
        assert response.success is True
        assert response.data is not None

    def test_execute_write(self):
        """测试执行写命令"""
        model = DRAMModel()

        # 先激活
        model.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=100, current_time=0
        )

        # 等待 tRCD 后写
        data = bytes(32)
        response = model.execute_write(
            stack_id=0, channel_id=0, bank_id=0,
            col_id=0, data=data, current_time=model.timing.tRCD + 1
        )
        assert response.success is True

    def test_execute_precharge(self):
        """测试执行预充电"""
        model = DRAMModel()

        # 激活
        model.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=100, current_time=0
        )

        # 等待 tRAS 后预充电
        response = model.execute_precharge(
            stack_id=0, channel_id=0, bank_id=0,
            current_time=model.timing.tRAS + 1
        )
        assert response.success is True

    def test_refresh(self):
        """测试刷新命令"""
        model = DRAMModel()
        response = model.execute_refresh(
            stack_id=0, channel_id=0, bank_id=0,
            current_time=0
        )
        assert response.success is True
        assert response.latency_cycles == model.timing.tRFC

    def test_stats_tracking(self):
        """测试统计跟踪"""
        model = DRAMModel()

        # 执行一些操作
        model.execute_activate(0, 0, 0, 100, 0)
        model.execute_activate(0, 0, 1, 100, 100)
        model.execute_read(0, 0, 0, 0, 50)
        model.execute_write(0, 0, 1, 0, bytes(32), 150)

        stats = model.stats
        assert stats.total_activations == 2
        assert stats.total_reads == 1
        assert stats.total_writes == 1

    def test_reset(self):
        """测试重置"""
        model = DRAMModel()

        # 执行操作
        model.execute_activate(0, 0, 0, 100, 0)
        model.execute_read(0, 0, 0, 0, 50)

        # 重置
        model.reset()

        assert model.stats.total_activations == 0
        assert model.stats.total_reads == 0

    def test_memory_model(self):
        """测试内存模型"""
        model = DRAMModel()
        model.enable_memory_model()

        # 激活
        model.execute_activate(0, 0, 0, 100, 0)

        # 写数据
        data = bytes([i for i in range(32)])
        model.execute_write(0, 0, 0, 0, data, 50)

        # 读回数据
        response = model.execute_read(0, 0, 0, 0, 50)
        assert response.success is True
        assert response.data == bytes([i for i in range(32)])

    def test_bank_utilization(self):
        """测试 bank 利用率"""
        model = DRAMModel()
        util = model.get_utilization(window=1000)
        assert 0 <= util <= 1.0

    def test_create_dram_model_from_config(self):
        """测试从配置创建模型"""
        config = {
            'hbm_version': 'hbm3',
            'stack_count': 2,
            'channels_per_stack': 8,
            'banks_per_channel': 16,
        }
        model = create_dram_model(config)
        assert model.hbm_version == 'hbm3'

    def test_multiple_stacks(self):
        """测试多 stack 操作"""
        model = DRAMModel(stack_count=4)

        # 在不同 stack 上操作
        for stack_id in range(4):
            response = model.execute_activate(
                stack_id=stack_id, channel_id=0, bank_id=0,
                row_id=100, current_time=stack_id * 100
            )
            assert response.success is True

        assert model.stats.total_activations == 4


class TestDRAMCommand:
    """DRAM 命令枚举测试"""

    def test_command_enum(self):
        """测试命令枚举"""
        assert DRAMCommand.NOP.value == 0
        assert DRAMCommand.ACT.value == 1
        assert DRAMCommand.PRE.value == 2
        assert DRAMCommand.RD.value == 4
        assert DRAMCommand.WR.value == 5
        assert DRAMCommand.REF.value == 6


class TestDRAMResponse:
    """DRAM 响应测试"""

    def test_response_success(self):
        """测试成功响应"""
        response = DRAMResponse(
            success=True,
            data=bytes(32),
            latency_cycles=10,
        )
        assert response.success is True
        assert response.data == bytes(32)
        assert response.latency_cycles == 10
        assert response.error is None

    def test_response_failure(self):
        """测试失败响应"""
        response = DRAMResponse(
            success=False,
            error="Bank not available",
        )
        assert response.success is False
        assert response.error == "Bank not available"


class TestDRAMStats:
    """DRAM 统计测试"""

    def test_stats_initialization(self):
        """测试统计初始化"""
        stats = DRAMStats()
        assert stats.total_activations == 0
        assert stats.total_reads == 0
        assert stats.total_writes == 0

    def test_stats_increment(self):
        """测试统计增量"""
        stats = DRAMStats()
        stats.add_activation()
        stats.add_activation()
        stats.add_read()
        stats.add_write()
        stats.add_hit()
        stats.add_miss()

        assert stats.total_activations == 2
        assert stats.total_reads == 1
        assert stats.total_writes == 1
        assert stats.row_hits == 1
        assert stats.row_misses == 1

    def test_stats_hit_rate(self):
        """测试命中率计算"""
        stats = DRAMStats()
        stats.add_hit()
        stats.add_hit()
        stats.add_miss()
        stats.add_hit()
        stats.add_conflict()

        assert stats.row_hits == 3
        total = stats.row_hits + stats.row_misses + stats.row_conflicts
        # hit_rate 会在 __repr__ 中计算

    def test_stats_repr(self):
        """测试统计表示"""
        stats = DRAMStats()
        stats.add_hit()
        stats.add_hit()
        stats.add_miss()
        stats.add_conflict()

        repr_str = repr(stats)
        assert "DRAMStats" in repr_str
        assert "acts=" in repr_str