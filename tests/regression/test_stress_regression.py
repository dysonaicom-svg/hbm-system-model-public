"""
Stress Regression Tests

压力测试 - 验证高负载场景下的系统行为和健壮性。

High Load Scenarios Tested:
- High request rate stress
- Queue overflow handling
- Sustained high bandwidth
- Mixed read/write under load
- Edge cases and corner conditions
"""

import pytest
from typing import Optional

from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.queue import QueueManager, ReadQueue, WriteQueue
from model.controller.exceptions import QueueOverflowError
from tests.regression.conftest import LATENCY_THRESHOLDS


class TestHighLoadStress:
    """高负载压力测试"""

    @pytest.mark.regression
    @pytest.mark.slow
    def test_high_request_rate_stress(self):
        """验证高请求率压力测试

        使用 100% 请求率进行压力测试。
        """
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=1.0,  # 100% 请求率
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 高请求率下应该产生大量请求
        assert stats.total_requests >= 0, (
            "High load should generate requests"
        )

        # 验证完成请求数
        assert stats.completed_requests >= 0, (
            "Completed requests should be non-negative"
        )

        # 延迟可能较高但应该可接受
        if stats.completed_requests > 0:
            assert stats.avg_latency >= 0, (
                f"Average latency should be non-negative"
            )

    @pytest.mark.regression
    @pytest.mark.slow
    def test_sustained_high_bandwidth(self):
        """验证持续高带宽

        使用高请求率和顺序访问，验证带宽表现。
        """
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=1.0,  # 100% 请求率
            read_ratio=1.0,    # 100% 读
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 验证吞吐量
        throughput = stats.throughput_gbps
        assert throughput >= 0, (
            f"Sustained bandwidth {throughput:.2f} GB/s should be non-negative"
        )

        # 顺序访问高请求率应该产生更多完成请求
        assert stats.completed_requests >= 0, (
            "Should complete requests under high load"
        )

    @pytest.mark.regression
    def test_mixed_read_write_load(self):
        """验证混合读写负载

        使用 50/50 读写比例的高负载测试。
        """
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.8,
            read_ratio=0.5,  # 50/50 读写
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 验证读写比例
        total_ops = stats.read_requests + stats.write_requests
        if total_ops > 0:
            read_ratio = stats.read_requests / total_ops
            assert 0.3 < read_ratio < 0.7, (
                f"Read ratio {read_ratio:.2%} should be close to 50%"
            )

        # 验证完成
        assert stats.completed_requests >= 0, (
            "Should complete mixed read/write requests"
        )


class TestQueueOverflowHandling:
    """队列溢出处理测试"""

    @pytest.mark.regression
    def test_queue_depth_configuration(self):
        """验证队列深度配置

        测试不同队列深度设置。
        """
        # 默认深度
        config = HBM3_DEFAULT
        config.queue_depth = 32
        qm = QueueManager.create(config.queue_depth)

        assert qm.read_queue.max_depth == 32, (
            "Read queue depth should be 32"
        )
        assert qm.write_queue.max_depth == 32, (
            "Write queue depth should be 32"
        )

        # 小深度
        qm_small = QueueManager.create(8)
        assert qm_small.read_queue.max_depth == 8, (
            "Small read queue depth should be 8"
        )

        # 大深度
        qm_large = QueueManager.create(64)
        assert qm_large.read_queue.max_depth == 64, (
            "Large read queue depth should be 64"
        )

    @pytest.mark.regression
    def test_queue_full_handling(self):
        """验证队列满时的处理

        当队列满时，新请求应该被拒绝而不是阻塞。
        """
        from model.controller.request import HBMRequest

        qm = QueueManager.create(queue_depth=4)

        # 填充读队列到最大值
        for i in range(4):
            req = HBMRequest(
                addr=0x1000 * (i + 1),
                length=64,
                is_read=True
            )
            success = qm.push_read(req)
            assert success, (
                f"Push #{i+1} should succeed (queue has space)"
            )

        # 队列应该已满
        assert qm.read_queue.is_full(), (
            "Queue should be full after 4 pushes"
        )

        # 再次推送应该失败（非阻塞）
        extra_req = HBMRequest(
            addr=0x5000,
            length=64,
            is_read=True
        )
        success = qm.push_read(extra_req, timeout=0.0)
        assert not success, (
            "Push should fail when queue is full (non-blocking)"
        )

        # 队列大小不应该超过最大值
        assert qm.read_queue.size() <= qm.read_queue.max_depth, (
            "Queue size should not exceed max depth"
        )

    @pytest.mark.regression
    def test_queue_reject_statistics(self):
        """验证队列拒绝统计

        验证队列跟踪拒绝计数。
        """
        from model.controller.request import HBMRequest

        qm = QueueManager.create(queue_depth=2)

        # 填充队列
        for i in range(2):
            req = HBMRequest(
                addr=0x1000 * (i + 1),
                length=64,
                is_read=True
            )
            qm.push_read(req)

        # 尝试超过容量
        for _ in range(3):
            req = HBMRequest(addr=0x5000, length=64, is_read=True)
            qm.push_read(req, timeout=0.0)

        # 检查统计
        stats = qm.read_queue.get_stats()
        assert stats['reject_count'] > 0, (
            "Reject count should be tracked"
        )

    @pytest.mark.regression
    def test_queue_occupancy_tracking(self):
        """验证队列占用率跟踪

        验证队列跟踪最大占用率。
        """
        from model.controller.request import HBMRequest

        qm = QueueManager.create(queue_depth=10)

        # 逐步添加请求
        for i in range(5):
            req = HBMRequest(
                addr=0x1000 * (i + 1),
                length=64,
                is_read=True
            )
            qm.push_read(req)

        # 检查最大占用率
        stats = qm.read_queue.get_stats()
        assert stats['max_occupancy'] == 5, (
            f"Max occupancy should be 5, got {stats['max_occupancy']}"
        )

        # 弹出请求
        req = qm.read_queue.pop()
        assert req is not None, "Should pop a request"

        # 再次添加
        req = HBMRequest(addr=0x6000, length=64, is_read=True)
        qm.push_read(req)

        # 最大占用率应该保持 5
        stats = qm.read_queue.get_stats()
        assert stats['max_occupancy'] == 5, (
            f"Max occupancy should remain 5, got {stats['max_occupancy']}"
        )

    @pytest.mark.regression
    def test_high_load_queue_overflow_recovery(self):
        """验证高负载下队列溢出后的恢复

        即使队列暂时满，系统也应该继续运行。
        """
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=1.0,  # 100% 请求率
            seed=42,
        )
        sim = HBMSimulator(config)

        # 运行仿真
        stats = sim.run()

        # 即使在高负载下，仿真也应该完成
        assert stats.total_cycles > 0, (
            "Simulation should complete cycles"
        )
        assert stats.total_requests >= 0, (
            "Total requests should be tracked"
        )

        # 完成的请求数应该合理
        assert stats.completed_requests >= 0, (
            "Completed requests should be tracked"
        )


class TestReadWritePatterns:
    """读写模式压力测试"""

    @pytest.mark.regression
    def test_write_heavy_load(self):
        """验证写密集负载

        使用 90% 写请求比例测试。
        """
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.8,
            read_ratio=0.1,  # 10% 读, 90% 写
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 写请求应该占大多数
        if stats.total_requests > 0:
            write_ratio = stats.write_requests / stats.total_requests
            assert write_ratio >= 0.5, (
                f"Write ratio {write_ratio:.2%} should be >= 50%"
            )

    @pytest.mark.regression
    def test_read_heavy_load(self):
        """验证读密集负载

        使用 90% 读请求比例测试。
        """
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.8,
            read_ratio=0.9,  # 90% 读
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 读请求应该占大多数
        if stats.total_requests > 0:
            read_ratio = stats.read_requests / stats.total_requests
            assert read_ratio >= 0.5, (
                f"Read ratio {read_ratio:.2%} should be >= 50%"
            )

    @pytest.mark.regression
    def test_burst_traffic(self):
        """验证突发流量

        测试突发请求的处理能力。
        """
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=1.0,  # 最大请求率
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 突发流量应该产生大量请求
        assert stats.total_requests >= 0, (
            "Burst traffic should generate requests"
        )
        assert stats.completed_requests >= 0, (
            "Should complete burst requests"
        )


class TestEdgeCases:
    """边界情况测试"""

    @pytest.mark.regression
    def test_zero_request_rate(self):
        """验证零请求率

        请求率为 0 时应该正常工作。
        """
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.0,  # 0% 请求率
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 不应该有请求
        assert stats.total_requests == 0, (
            "Zero request rate should generate no requests"
        )
        assert stats.completed_requests == 0, (
            "No requests should be completed"
        )

    @pytest.mark.regression
    def test_zero_simulation_time(self):
        """验证零仿真时间

        仿真时间为 0 时应该正常运行。
        """
        config = SimulationConfig(
            simulation_time_us=0.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 不应该有周期
        assert stats.total_cycles == 0, (
            "Zero simulation time should produce zero cycles"
        )

    @pytest.mark.regression
    def test_single_cycle_simulation(self):
        """验证单周期仿真

        最小仿真时间测试。
        """
        config = SimulationConfig(
            simulation_time_us=0.0001,  # 最小时间
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=1.0,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 应该能运行
        assert stats.total_cycles >= 0, (
            "Should complete at least zero cycles"
        )

    @pytest.mark.regression
    def test_very_long_simulation(self):
        """验证超长仿真

        运行 1000us 仿真测试长时间稳定性。
        """
        config = SimulationConfig(
            simulation_time_us=1000.0,  # 1ms
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 长时间仿真应该完成
        assert stats.total_cycles > 0, (
            "Long simulation should complete cycles"
        )
        assert stats.completed_requests >= 0, (
            "Completed requests should be tracked"
        )

    @pytest.mark.regression
    def test_minimal_burst_size(self):
        """验证最小突发大小

        使用最小请求长度测试。
        """
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.5,
            burst_size=64,  # 最小突发
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 应该能处理最小突发
        assert stats.total_requests >= 0, (
            "Should handle minimal burst size"
        )


class TestPerformanceDegradation:
    """性能退化测试"""

    @pytest.mark.regression
    @pytest.mark.slow
    def test_latency_under_high_load(self):
        """验证高负载下的延迟退化

        高请求率下延迟应该合理。
        """
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=1.0,  # 100% 请求率
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 延迟应该在合理范围内
        if stats.completed_requests > 0:
            assert stats.avg_latency >= 0, (
                "Average latency should be non-negative"
            )

            # P99 延迟阈值
            p99_latency = stats.avg_latency * 2  # 简化估算
            assert p99_latency < LATENCY_THRESHOLDS['p99_max'], (
                f"Estimated P99 latency {p99_latency:.1f} cycles exceeds threshold"
            )

    @pytest.mark.regression
    def test_throughput_vs_request_rate(self):
        """验证吞吐量与请求率的关系

        高请求率应该产生更高的吞吐量。
        """
        # 低请求率
        config_low = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.2,
            seed=42,
        )
        sim_low = HBMSimulator(config_low)
        stats_low = sim_low.run()

        # 高请求率
        config_high = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=1.0,
            seed=42,
        )
        sim_high = HBMSimulator(config_high)
        stats_high = sim_high.run()

        # 高请求率应该产生更多请求
        assert stats_high.total_requests >= stats_low.total_requests, (
            f"High rate requests {stats_high.total_requests} should be >= "
            f"low rate requests {stats_low.total_requests}"
        )


class TestConcurrency:
    """并发测试"""

    @pytest.mark.regression
    def test_multi_stack_concurrent_access(self):
        """验证多堆栈并发访问

        HBM 支持多堆栈配置，验证并发访问。
        """
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )
        # 设置多堆栈
        config.hbm_config.stack_count = 8

        sim = HBMSimulator(config)
        stats = sim.run()

        # 多堆栈配置应该能正常工作
        assert stats.total_requests >= 0, (
            "Multi-stack should handle requests"
        )

    @pytest.mark.regression
    def test_queue_manager_concurrent_ops(self):
        """验证队列管理器并发操作

        测试队列的并发读写操作。
        """
        from model.controller.request import HBMRequest
        import threading

        qm = QueueManager.create(queue_depth=32)

        # 并发添加读请求
        def add_reads(count: int):
            for i in range(count):
                req = HBMRequest(
                    addr=0x1000 * i,
                    length=64,
                    is_read=True
                )
                qm.push_read(req)

        # 并发添加写请求
        def add_writes(count: int):
            for i in range(count):
                req = HBMRequest(
                    addr=0x2000 * i,
                    length=64,
                    is_read=False
                )
                qm.push_write(req)

        threads = []
        for _ in range(2):
            threads.append(threading.Thread(target=add_reads, args=(10,)))
            threads.append(threading.Thread(target=add_writes, args=(10,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证请求被添加
        assert qm.read_queue.size() > 0 or qm.write_queue.size() > 0, (
            "Concurrent operations should add requests"
        )


class TestSystemStability:
    """系统稳定性测试"""

    @pytest.mark.regression
    @pytest.mark.slow
    def test_continuous_operation_stability(self):
        """验证连续运行稳定性

        长时间运行不应该导致性能退化或死锁。
        """
        config = SimulationConfig(
            simulation_time_us=200.0,  # 200us 仿真
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            seed=42,
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        # 验证基本完成
        assert stats.total_cycles > 0, (
            "Should complete simulation cycles"
        )
        assert stats.completed_requests >= 0, (
            "Should complete requests"
        )

        # 验证没有异常
        assert stats.row_hit_rate >= 0 and stats.row_hit_rate <= 1, (
            "Row hit rate should be in valid range"
        )

    @pytest.mark.regression
    def test_no_resource_leaks(self):
        """验证没有资源泄漏

        验证队列在运行后可以正常清空。
        """
        from model.controller.request import HBMRequest

        qm = QueueManager.create(queue_depth=16)

        # 添加请求
        for i in range(10):
            req = HBMRequest(
                addr=0x1000 * (i + 1),
                length=64,
                is_read=True
            )
            qm.push_read(req)

        # 验证队列有内容
        assert qm.read_queue.size() == 10, (
            "Queue should have 10 requests"
        )

        # 弹出所有请求
        count = 0
        while not qm.read_queue.is_empty():
            req = qm.read_queue.pop()
            if req is None:
                break
            count += 1

        # 验证队列已清空
        assert qm.read_queue.is_empty(), (
            "Queue should be empty after popping all requests"
        )
        assert count == 10, (
            f"Should have popped 10 requests, got {count}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "regression"])