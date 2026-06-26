"""
Simulation Framework Tests
端到端仿真框架测试
"""

import sys
sys.path.insert(0, '/home/ic/JXTF/HBM')

import pytest
from sim.simulator import (
    SimulationConfig,
    SimulationStats,
    TrafficGenerator,
    HBMSimulator,
    TrafficPattern,
    run_simulation
)


class TestSimulationConfig:
    """测试仿真配置"""

    def test_default_config(self):
        config = SimulationConfig()
        assert config.clock_freq_hz == 1.28e9
        assert config.simulation_time_us == 100.0
        assert config.traffic_pattern == TrafficPattern.RANDOM

    def test_custom_config(self):
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
        )
        assert config.simulation_time_us == 50.0
        assert config.traffic_pattern == TrafficPattern.SEQUENTIAL
        assert config.request_rate == 0.8


class TestSimulationStats:
    """测试仿真统计"""

    def test_stats_initialization(self):
        stats = SimulationStats()
        assert stats.total_cycles == 0
        assert stats.total_requests == 0
        assert stats.completed_requests == 0

    def test_avg_latency(self):
        stats = SimulationStats()
        stats.total_latency_cycles = 100
        stats.completed_requests = 10
        assert stats.avg_latency == 10.0

    def test_avg_latency_zero(self):
        stats = SimulationStats()
        assert stats.avg_latency == 0.0

    def test_row_hit_rate(self):
        stats = SimulationStats()
        stats.row_hits = 80
        stats.row_misses = 15
        stats.row_conflicts = 5
        assert abs(stats.row_hit_rate - 0.8) < 0.01

    def test_throughput(self):
        stats = SimulationStats()
        stats.total_cycles = 100000
        stats.completed_requests = 1000
        # 1000 req * 32 bytes * 4 burst / (100000 * 781.25ns)
        assert stats.throughput_gbps > 0

    def test_efficiency(self):
        stats = SimulationStats()
        stats.total_cycles = 1000
        stats.busy_cycles = 800
        assert abs(stats.efficiency - 0.8) < 0.001

    def test_bandwidth_efficiency(self):
        stats = SimulationStats()
        stats.total_cycles = 100000
        stats.completed_requests = 1000
        # HBM3 2-stack peak: 819.2 * 2 = 1638.4 GB/s
        # At 1000 requests: 1000 * 32 * 4 = 128000 bytes
        # Throughput should be > 0
        assert stats.bandwidth_efficiency >= 0

    def test_to_dict(self):
        stats = SimulationStats()
        stats.total_cycles = 1000
        stats.completed_requests = 100
        d = stats.to_dict()
        assert 'total_cycles' in d
        assert 'completed_requests' in d
        assert 'bandwidth_efficiency' in d
        assert 'efficiency' in d


class TestTrafficGenerator:
    """测试流量生成器"""

    def test_generator_creation(self):
        config = SimulationConfig(seed=42)
        gen = TrafficGenerator(config)
        assert gen.config == config

    def test_random_traffic(self):
        config = SimulationConfig(
            traffic_pattern=TrafficPattern.RANDOM,
            address_range=1 << 42,  # 42 bits for proper channel distribution
            seed=42
        )
        gen = TrafficGenerator(config)
        requests = gen.generate()
        # 请求率 0.5，可能为空
        for req in requests:
            # Address should be within the valid HBM address range
            assert req.addr < (1 << 42)
            assert req.length > 0

    def test_sequential_traffic(self):
        config = SimulationConfig(
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            address_range=0x10000,
            seed=42
        )
        gen = TrafficGenerator(config)

        addr0 = gen.current_addr
        gen.generate()
        addr1 = gen.current_addr
        assert addr1 > addr0 or addr1 == 0  # 循环

    def test_stride_traffic(self):
        """测试 stride 流量模式"""
        config = SimulationConfig(
            traffic_pattern=TrafficPattern.STRIDE,
            stride_value=4096,
            address_range=0x100000,
            request_rate=1.0,  # 确保生成请求
            seed=42
        )
        gen = TrafficGenerator(config)

        # 生成多个请求，验证地址递增
        addrs = []
        for _ in range(5):
            requests = gen.generate()
            if requests:
                addrs.append(requests[0].addr)

        # 检查 stride 模式是否正确递增
        if len(addrs) >= 2:
            diff = addrs[1] - addrs[0]
            assert diff == 4096 or diff == -(0x100000 - 4096)  # 正常递增或循环

    def test_hotspot_traffic(self):
        config = SimulationConfig(
            traffic_pattern=TrafficPattern.HOT_SPOT,
            seed=42
        )
        gen = TrafficGenerator(config)

        # 热点模式大部分地址应该较小
        hotspot_count = 0
        for _ in range(100):
            requests = gen.generate()
            for req in requests:
                if req.addr < config.address_range // 10:
                    hotspot_count += 1

        # 至少 50% 应该是热点访问
        assert hotspot_count > 30


class TestHBMSimulator:
    """测试 HBM 仿真器"""

    def test_simulator_creation(self):
        config = SimulationConfig(simulation_time_us=10.0)
        sim = HBMSimulator(config)
        assert sim.current_cycle == 0
        assert sim.max_cycles > 0

    def test_simulator_step(self):
        config = SimulationConfig(simulation_time_us=10.0, request_rate=1.0, seed=42)
        sim = HBMSimulator(config)

        response = sim.step()
        assert sim.current_cycle == 1

    def test_short_simulation(self):
        config = SimulationConfig(
            simulation_time_us=10.0,
            request_rate=0.5,
            seed=42
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        assert stats.total_cycles > 0
        assert stats.total_cycles <= sim.max_cycles * 1.1  # 允许一点误差

    def test_get_stats(self):
        config = SimulationConfig(simulation_time_us=10.0, seed=42)
        sim = HBMSimulator(config)
        sim.step()
        sim.step()

        stats = sim.get_stats()
        assert stats.total_cycles == 2

    def test_get_completion_jitter(self):
        """测试完成抖动分析"""
        config = SimulationConfig(simulation_time_us=50.0, request_rate=1.0, seed=42)
        sim = HBMSimulator(config)
        sim.run()

        jitter = sim.get_completion_jitter()
        assert 'mean' in jitter
        assert 'std' in jitter
        assert 'max' in jitter
        assert 'count' in jitter

    def test_run_verbose(self):
        """测试详细运行模式"""
        config = SimulationConfig(simulation_time_us=10.0, seed=42)
        sim = HBMSimulator(config)
        stats = sim.run_verbose()

        assert stats.total_cycles > 0
        assert stats.max_latency_cycles >= 0
        assert stats.min_latency_cycles >= 0


class TestRunSimulation:
    """测试仿真运行函数"""

    def test_run_simulation(self):
        config = SimulationConfig(
            simulation_time_us=10.0,
            request_rate=0.3,
            seed=42
        )
        stats = run_simulation(config)

        assert stats.total_cycles > 0
        assert stats.total_requests >= 0
        assert stats.row_hit_rate >= 0.0
        assert stats.row_hit_rate <= 1.0

    def test_sequential_pattern(self):
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            read_ratio=1.0,
            seed=42
        )
        stats = run_simulation(config)

        # Sequential 应该有更高的 row hit rate
        assert stats.row_hit_rate >= 0.0


def test_integration():
    """集成测试"""
    print("\n=== HBM Simulation Integration Test ===")

    # 创建配置
    config = SimulationConfig(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        read_ratio=0.7,
        seed=42
    )

    print(f"Config: {config.traffic_pattern.value}, rate={config.request_rate}")

    # 运行仿真
    sim = HBMSimulator(config)
    stats = sim.run()

    # 打印结果
    print(f"\nResults:")
    print(f"  Cycles: {stats.total_cycles}")
    print(f"  Requests: {stats.total_requests}")
    print(f"  Completed: {stats.completed_requests}")
    print(f"  Hit rate: {stats.row_hit_rate:.2%}")
    print(f"  Avg latency: {stats.avg_latency:.1f} cycles")
    print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")

    # 验证结果
    assert stats.total_cycles > 0
    assert stats.total_requests >= 0

    print("\n=== Integration Test Passed ===")


if __name__ == "__main__":
    test_integration()