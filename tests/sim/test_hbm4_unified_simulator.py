"""
HBM4 Unified Simulator Tests
测试 HBM4 统一仿真器的功能
"""

import pytest
import sys
import os

sys.path.insert(0, '/home/ic/JXTF/HBM4')

from sim.hbm4_unified_simulator import (
    HBM4UnifiedSimulator,
    SimulationConfig,
    SimulationStats,
    SimulationMode,
)


class TestSimulationConfig:
    """测试仿真配置"""

    def test_default_config(self):
        config = SimulationConfig()
        assert config.mode == SimulationMode.QUICK
        assert config.num_channels == 32
        assert config.cycles == 1000

    def test_custom_config(self):
        config = SimulationConfig(
            mode=SimulationMode.FULL,
            num_channels=16,
            cycles=500,
        )
        assert config.mode == SimulationMode.FULL
        assert config.num_channels == 16
        assert config.cycles == 500

    def test_config_from_args(self):
        """测试从参数创建配置"""
        class MockArgs:
            mode = 'full'
            channels = 16
            cycles = 500
            pam3 = True
            ecc = True
            lane_repair = True
            trace = False
            verbose = True
            speed_grade = "16Gbps"

        args = MockArgs()
        config = SimulationConfig.from_args(args)
        assert config.mode == SimulationMode.FULL
        assert config.num_channels == 16


class TestSimulationStats:
    """测试仿真统计"""

    def test_stats_initialization(self):
        """测试统计初始化"""
        stats = SimulationStats()
        assert stats.total_cycles == 0
        assert stats.commands_processed == 0
        assert stats.errors_detected == 0

    def test_rtl_match_rate(self):
        """测试 RTL 匹配率"""
        stats = SimulationStats()
        stats.rtl_matched = 90
        stats.rtl_mismatched = 10
        assert abs(stats.rtl_match_rate - 0.9) < 0.001

    def test_rtl_match_rate_zero(self):
        """测试 RTL 匹配率 - 无事务"""
        stats = SimulationStats()
        assert stats.rtl_match_rate == 0.0

    def test_duration_calculation(self):
        """测试持续时间计算"""
        stats = SimulationStats()
        stats.start_time = 100.0
        stats.end_time = 105.0
        assert abs(stats.duration_s - 5.0) < 0.001

    def test_throughput_calculation(self):
        """测试吞吐量计算"""
        stats = SimulationStats()
        stats.commands_processed = 1000
        stats.start_time = 100.0
        stats.end_time = 105.0
        assert stats.throughput == 200.0  # 1000 / 5 = 200

    def test_throughput_zero_duration(self):
        """测试吞吐量 - 零持续时间"""
        stats = SimulationStats()
        stats.commands_processed = 100
        stats.start_time = 100.0
        stats.end_time = 100.0
        assert stats.throughput == 0.0


class TestSimulationMode:
    """测试仿真模式"""

    def test_all_modes(self):
        """测试所有模式"""
        assert SimulationMode.QUICK is not None
        assert SimulationMode.FULL is not None
        assert SimulationMode.STRESS is not None
        assert SimulationMode.BENCHMARK is not None


class TestHBM4UnifiedSimulator:
    """测试 HBM4 统一仿真器"""

    def test_simulator_creation(self):
        """测试仿真器创建"""
        config = SimulationConfig(
            num_channels=8,
            cycles=100,
        )
        sim = HBM4UnifiedSimulator(config)
        assert sim.config == config

    def test_simulator_run(self):
        """测试运行仿真"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            mode=SimulationMode.QUICK,
        )
        sim = HBM4UnifiedSimulator(config)
        stats = sim.run()
        assert stats.total_cycles > 0

    def test_simulator_get_stats(self):
        """测试获取统计"""
        config = SimulationConfig(num_channels=4, cycles=20)
        sim = HBM4UnifiedSimulator(config)
        sim.run()
        stats = sim.get_stats()
        # get_stats 可能返回字典或 SimulationStats
        if isinstance(stats, dict):
            assert 'total_cycles' in stats or 'commands_processed' in stats
        else:
            assert stats.total_cycles > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
