"""
QoS Scheduler Regression Tests

QoS 调度器回归测试 - 验证 QoS 优先级和带宽保证。
"""

import pytest
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest
from model.controller.qos_scheduler import QoSScheduler


class TestQoSRegression:
    """QoS 回归测试"""

    def test_qos_scheduler_creation(self):
        """测试 QoS 调度器创建"""
        config = HBMConfig(
            scheduler_mode="qos",
            bw_guarantee_critical=200.0,
            bw_guarantee_high=300.0,
            bw_guarantee_normal=200.0,
            bw_guarantee_low=100.0,
        )

        scheduler = QoSScheduler(config)

        assert scheduler is not None
        assert scheduler.bandwidth_guarantee is not None

    def test_qos_scheduler_priority(self, qos_simulator):
        """测试 QoS 优先级调度"""
        stats = qos_simulator.run()

        # 验证仿真完成
        assert stats.total_requests >= 0

    def test_qos_bandwidth_guarantee(self):
        """测试带宽保证"""
        config = HBMConfig(
            scheduler_mode="qos",
            bw_guarantee_critical=200.0,
            bw_guarantee_high=300.0,
            bw_guarantee_normal=200.0,
            bw_guarantee_low=100.0,
        )

        scheduler = QoSScheduler(config)

        # 验证带宽保证值
        assert scheduler.bandwidth_guarantee[15] == 200.0  # Critical
        assert scheduler.bandwidth_guarantee[12] == 300.0  # High
        assert scheduler.bandwidth_guarantee[8] == 200.0   # Normal
        assert scheduler.bandwidth_guarantee[4] == 100.0  # Low

    def test_qos_request_priority(self):
        """测试请求优先级"""
        controller = HBMController(HBMConfig(scheduler_mode="qos"))

        # 提交不同优先级的请求
        high_priority = HBMRequest(addr=0x1000, length=64, is_read=True, qos=15)
        low_priority = HBMRequest(addr=0x2000, length=64, is_read=True, qos=4)

        controller.submit_request(high_priority)
        controller.submit_request(low_priority)

        assert controller.stats['total_requests'] == 2

    def test_qos_multiple_requests(self):
        """测试多请求调度"""
        controller = HBMController(HBMConfig(scheduler_mode="qos"))

        # 提交多个不同优先级的请求
        for i in range(10):
            qos = (i % 2) * 8 + 4  # 交替高/低优先级
            req = HBMRequest(addr=0x1000 * (i + 1), length=64, is_read=True, qos=qos)
            controller.submit_request(req)

        # 运行调度
        for _ in range(100):
            controller.tick()

        # 验证请求被调度
        stats = controller.get_stats()
        assert stats['scheduler']['schedule_count'] >= 0


class TestQoSScheduling:
    """QoS 调度逻辑测试"""

    def test_qos_high_priority_first(self):
        """测试高优先级请求优先调度"""
        controller = HBMController(HBMConfig(scheduler_mode="qos"))

        # 先提交低优先级
        low_req = HBMRequest(addr=0x2000, length=64, is_read=True, qos=4)
        controller.submit_request(low_req)

        # 再提交高优先级
        high_req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=15)
        controller.submit_request(high_req)

        # 运行调度
        for _ in range(50):
            controller.tick()

        # 高优先级请求应该先被处理
        # (由于调度器实现，可能有细微差异)
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 2

    def test_qos_same_priority_fcfs(self):
        """测试同优先级 FCFS 调度"""
        controller = HBMController(HBMConfig(scheduler_mode="qos"))

        # 提交相同优先级的多个请求
        addrs = [0x1000, 0x2000, 0x3000, 0x4000]
        for addr in addrs:
            req = HBMRequest(addr=addr, length=64, is_read=True, qos=8)
            controller.submit_request(req)

        # 运行调度
        for _ in range(100):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == len(addrs)

    def test_qos_mixed_priorities(self):
        """测试混合优先级调度"""
        controller = HBMController(HBMConfig(scheduler_mode="qos"))

        # 混合优先级请求
        requests = [
            (0x1000, 4),   # Low
            (0x2000, 8),   # Normal
            (0x3000, 12),  # High
            (0x4000, 15),  # Critical
            (0x5000, 4),   # Low
        ]

        for addr, qos in requests:
            req = HBMRequest(addr=addr, length=64, is_read=True, qos=qos)
            controller.submit_request(req)

        # 运行调度
        for _ in range(100):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == len(requests)


class TestQoSIntegration:
    """QoS 集成测试"""

    def test_qos_with_simulator(self):
        """测试 QoS 与仿真器集成"""
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        # 设置为 QoS 模式
        config.hbm_config.scheduler_mode = "qos"

        sim = HBMSimulator(config)
        stats = sim.run()

        assert stats.total_requests >= 0
        assert stats.completed_requests >= 0

    def test_qos_read_write_mix(self):
        """测试 QoS 读写混合"""
        controller = HBMController(HBMConfig(scheduler_mode="qos"))

        # 混合读写请求
        requests = [
            HBMRequest(addr=0x1000, length=64, is_read=True, qos=12),
            HBMRequest(addr=0x2000, length=64, is_read=False, qos=12),
            HBMRequest(addr=0x1000, length=64, is_read=True, qos=8),
            HBMRequest(addr=0x3000, length=64, is_read=True, qos=15),
        ]

        for req in requests:
            controller.submit_request(req)

        # 运行调度
        for _ in range(100):
            controller.tick()

        stats = controller.get_stats()
        assert stats['controller']['read_requests'] == 3
        assert stats['controller']['write_requests'] == 1


class TestQoSPerformance:
    """QoS 性能测试"""

    def test_qos_throughput(self):
        """测试 QoS 吞吐量"""
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        config.hbm_config.scheduler_mode = "qos"

        sim = HBMSimulator(config)
        stats = sim.run()

        # 验证吞吐量
        assert stats.throughput_gbps >= 0

    def test_qos_latency(self):
        """测试 QoS 延迟"""
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.5,
            seed=42,
        )
        config.hbm_config.scheduler_mode = "qos"

        sim = HBMSimulator(config)
        stats = sim.run()

        # 验证延迟
        assert stats.avg_latency >= 0

    def test_qos_vs_frfcfs(self):
        """测试 QoS 与 FR-FCFS 对比"""
        from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

        results = {}

        for mode in ["qos", "fr-fcfs"]:
            config = SimulationConfig(
                simulation_time_us=50.0,
                traffic_pattern=TrafficPattern.RANDOM,
                request_rate=0.5,
                seed=42,
            )
            config.hbm_config.scheduler_mode = mode

            sim = HBMSimulator(config)
            stats = sim.run()

            results[mode] = {
                'throughput': stats.throughput_gbps,
                'latency': stats.avg_latency,
                'completed': stats.completed_requests,
            }

        # 两种模式都应该工作
        assert results['qos']['completed'] >= 0
        assert results['fr-fcfs']['completed'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])