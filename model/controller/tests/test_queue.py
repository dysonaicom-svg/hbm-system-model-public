"""
Tests for Request Queue - Enhanced for HBM4 Priority Queue
"""

import pytest
import time
from model.controller.queue import (
    RequestQueue, ReadQueue, WriteQueue, QueueManager,
    PriorityQueue, HBM4QueueManager,
    AgeTrackingMixin, PriorityAwareMixin
)
from model.controller.request import HBMRequest


class TestAgeTrackingMixin:
    """Test AgeTrackingMixin"""

    def test_age_tracking(self):
        """测试年龄追踪"""
        tracker = AgeTrackingMixin()
        tracker.set_clock(100.0)

        req = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=50.0)
        age = tracker.get_request_age(req)
        assert age == 50.0

    def test_starvation_detection(self):
        """测试饥饿检测"""
        tracker = AgeTrackingMixin()
        tracker.set_clock(6000.0)

        # 饥饿请求
        starving_req = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=1000.0)
        assert tracker.is_starving(starving_req)

        # 非饥饿请求
        normal_req = HBMRequest(addr=0x2000, length=64, is_read=True, arrival_time=5000.0)
        assert not tracker.is_starving(normal_req)

    def test_starvation_score(self):
        """测试饥饿分数计算"""
        tracker = AgeTrackingMixin()
        tracker.set_clock(3000.0)

        req = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=1000.0)
        score = tracker.get_starvation_score(req)
        # 等待 2000 cycles, 临界值 5000, 分数应为 0.4
        assert 0.3 < score < 0.5

    def test_clock_tick(self):
        """测试时钟推进"""
        tracker = AgeTrackingMixin()
        assert tracker.get_clock() == 0.0

        tracker.tick(100)
        assert tracker.get_clock() == 100.0

        tracker.set_clock(500.0)
        assert tracker.get_clock() == 500.0


class TestPriorityAwareMixin:
    """Test PriorityAwareMixin"""

    def test_priority_assignment(self):
        """测试优先级分配"""
        mixer = PriorityAwareMixin(num_priority_classes=16)

        high_priority = HBMRequest(addr=0x1000, length=64, is_read=True, qos=15)
        low_priority = HBMRequest(addr=0x2000, length=64, is_read=True, qos=0)

        assert mixer.get_priority(high_priority) == 15
        assert mixer.get_priority(low_priority) == 0

    def test_priority_bounds(self):
        """测试优先级边界"""
        mixer = PriorityAwareMixin(num_priority_classes=16)

        # 超出范围应该被裁剪
        overflow = HBMRequest(addr=0x1000, length=64, is_read=True, qos=100)
        assert mixer.get_priority(overflow) == 15

        underflow = HBMRequest(addr=0x2000, length=64, is_read=True, qos=-5)
        assert mixer.get_priority(underflow) == 0

    def test_priority_bucket(self):
        """测试优先级桶"""
        mixer = PriorityAwareMixin(num_priority_classes=16)

        bucket = mixer.get_priority_bucket(5)
        assert isinstance(bucket, list)
        assert len(bucket) == 0

    def test_priority_distribution(self):
        """测试优先级分布统计"""
        mixer = PriorityAwareMixin(num_priority_classes=16)
        dist = mixer.get_queue_depth_by_priority()

        assert dist[0] == 0
        assert dist[15] == 0
        assert len(dist) == 16


class TestRequestQueue:
    """Test RequestQueue base class"""

    def test_queue_creation(self):
        """测试队列创建"""
        queue = RequestQueue(max_depth=16, name="TestQueue")
        assert queue.max_depth == 16
        assert queue.size() == 0
        assert queue.is_empty()
        assert not queue.is_full()

    def test_push_pop(self):
        """测试入队出队"""
        queue = RequestQueue(max_depth=4)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True)

        assert queue.push(req1)
        assert queue.size() == 1

        assert queue.push(req2)
        assert queue.size() == 2

        popped = queue.pop()
        assert popped.request_id == req1.request_id
        assert queue.size() == 1

    def test_full_queue(self):
        """测试队列满"""
        queue = RequestQueue(max_depth=2)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True)
        req3 = HBMRequest(addr=0x3000, length=64, is_read=True)

        assert queue.push(req1)
        assert queue.push(req2)
        assert not queue.push(req3)  # 应该失败

    def test_empty_pop(self):
        """测试空队列出队"""
        queue = RequestQueue(max_depth=4)
        assert queue.pop() is None

    def test_remove(self):
        """测试移除请求"""
        queue = RequestQueue(max_depth=4)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True)

        queue.push(req1)
        queue.push(req2)

        assert queue.remove(req1.request_id)
        assert queue.size() == 1

        assert not queue.remove(9999)  # 不存在的 ID

    def test_clear(self):
        """测试清空队列"""
        queue = RequestQueue(max_depth=4)

        for i in range(3):
            queue.push(HBMRequest(addr=0x1000 + i, length=64, is_read=True))

        assert queue.size() == 3
        queue.clear()
        assert queue.size() == 0

    def test_stats(self):
        """测试统计"""
        queue = RequestQueue(max_depth=4)

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True))
        queue.pop()

        stats = queue.get_stats()
        assert stats['push_count'] == 2
        assert stats['pop_count'] == 1
        assert stats['max_occupancy'] == 2


class TestReadQueue:
    """Test ReadQueue"""

    def test_get_best_request(self):
        """测试获取最佳请求 (FR-FCFS)"""
        queue = ReadQueue(max_depth=16)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=100.0)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, arrival_time=200.0)

        queue.push(req2)
        queue.push(req1)  # req1 更早到达

        best = queue.get_best_request()
        assert best.request_id == req1.request_id

    def test_get_oldest_request(self):
        """测试获取最老请求"""
        queue = ReadQueue(max_depth=16)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=100.0)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, arrival_time=200.0)

        queue.push(req2)
        queue.push(req1)

        oldest = queue.get_oldest_request()
        assert oldest.request_id == req1.request_id


class TestWriteQueue:
    """Test WriteQueue"""

    def test_should_drain(self):
        """测试写队列耗尽检测"""
        queue = WriteQueue(max_depth=10, drain_threshold=0.8)

        # 80% 以下不应该 drain
        for i in range(7):
            queue.push(HBMRequest(addr=0x1000 + i, length=64, is_read=False))
        assert not queue.should_drain()

        # 80% 以上应该 drain
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=False))
        assert queue.should_drain()

    def test_pending_bytes(self):
        """测试待写入字节统计"""
        queue = WriteQueue(max_depth=16)

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=False))
        queue.push(HBMRequest(addr=0x2000, length=128, is_read=False))

        assert queue.get_pending_bytes() == 192


class TestQueueManager:
    """Test QueueManager"""

    def test_create(self):
        """测试创建"""
        manager = QueueManager.create(queue_depth=32)
        assert manager.read_queue.max_depth == 32
        assert manager.write_queue.max_depth == 32

    def test_push_read_write(self):
        """测试入队"""
        manager = QueueManager.create()

        read_req = HBMRequest(addr=0x1000, length=64, is_read=True)
        write_req = HBMRequest(addr=0x2000, length=64, is_read=False)

        assert manager.push_read(read_req)
        assert manager.push_write(write_req)
        assert manager.total_size() == 2

    def test_is_full(self):
        """测试队列满检测"""
        manager = QueueManager.create(queue_depth=2)

        for i in range(2):
            manager.push_read(HBMRequest(addr=0x1000 + i, length=64, is_read=True))

        assert manager.is_full()

    def test_stats(self):
        """测试统计"""
        manager = QueueManager.create()

        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_write(HBMRequest(addr=0x2000, length=64, is_read=False))

        stats = manager.get_stats()
        assert stats['total']['size'] == 2


class TestPriorityQueue:
    """Test PriorityQueue (HBM4 64-depth priority-aware queue)"""

    def test_queue_creation(self):
        """测试优先级队列创建"""
        queue = PriorityQueue(max_depth=64, num_priority_classes=16)
        assert queue.max_depth == 64
        assert queue._num_priority_classes == 16
        assert queue.size() == 0

    def test_priority_ordering(self):
        """测试优先级排序"""
        queue = PriorityQueue(max_depth=64)
        queue.set_clock(100.0)

        # 创建不同优先级的请求
        low_req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=1, arrival_time=100.0)
        mid_req = HBMRequest(addr=0x2000, length=64, is_read=True, qos=8, arrival_time=100.0)
        high_req = HBMRequest(addr=0x3000, length=64, is_read=True, qos=15, arrival_time=100.0)

        # 按任意顺序入队
        queue.push(mid_req)
        queue.push(low_req)
        queue.push(high_req)

        # 最高优先级应该先出队
        best = queue.get_best_request()
        assert best.qos == 15
        assert best.request_id == high_req.request_id

    def test_age_ordering_same_priority(self):
        """测试同优先级内按年龄排序"""
        queue = PriorityQueue(max_depth=64)
        queue.set_clock(300.0)

        # 同优先级，不同时到达的请求
        old_req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=5, arrival_time=100.0)
        new_req = HBMRequest(addr=0x2000, length=64, is_read=True, qos=5, arrival_time=200.0)

        queue.push(new_req)
        queue.push(old_req)

        best = queue.get_best_request()
        assert best.request_id == old_req.request_id

    def test_starvation_detection(self):
        """测试饥饿请求检测"""
        queue = PriorityQueue(max_depth=64)
        queue.set_clock(6000.0)

        starving_req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=5, arrival_time=1000.0)
        normal_req = HBMRequest(addr=0x2000, length=64, is_read=True, qos=5, arrival_time=5000.0)

        queue.push(starving_req)
        queue.push(normal_req)

        starving = queue.get_starving_requests()
        assert len(starving) == 1
        assert starving[0].request_id == starving_req.request_id

    def test_priority_distribution(self):
        """测试优先级分布"""
        queue = PriorityQueue(max_depth=64)
        queue.set_clock(100.0)

        for i in range(16):
            req = HBMRequest(addr=0x1000 + i, length=64, is_read=True, qos=i)
            queue.push(req)

        dist = queue.get_priority_distribution()
        for i in range(16):
            assert dist[i] == 1

    def test_avg_wait_time(self):
        """测试平均等待时间"""
        queue = PriorityQueue(max_depth=64)
        queue.set_clock(1000.0)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=0.0)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True, arrival_time=200.0)

        queue.push(req1)
        queue.push(req2)

        # ages: (1000-0) + (1000-200) = 1000 + 800 = 1800
        # avg: 1800 / 2 = 900
        avg_wait = queue.get_avg_wait_time()
        assert avg_wait == 900.0

    def test_detailed_stats(self):
        """测试详细统计"""
        queue = PriorityQueue(max_depth=64)
        queue.set_clock(500.0)

        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True, qos=10))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True, qos=5))

        stats = queue.get_detailed_stats()
        assert 'avg_wait_time' in stats
        assert 'max_wait_time' in stats
        assert 'starving_count' in stats
        assert 'priority_distribution' in stats
        assert stats['clock'] == 500.0

    def test_priority_boost(self):
        """测试优先级提升"""
        queue = PriorityQueue(max_depth=64)
        queue.enable_priority_boost(True)
        queue.set_priority_boost_factor(2.0)

        assert queue._priority_boost_enabled is True
        assert queue._priority_boost_factor == 2.0

        queue.enable_priority_boost(False)
        assert queue._priority_boost_enabled is False

    def test_requests_by_priority(self):
        """测试按优先级过滤"""
        queue = PriorityQueue(max_depth=64)
        queue.set_clock(100.0)

        for i in range(8):
            qos = 5 if i < 4 else 10
            queue.push(HBMRequest(addr=0x1000 + i, length=64, is_read=True, qos=qos))

        high_pri = queue.get_requests_by_priority(10)
        low_pri = queue.get_requests_by_priority(5)

        assert len(high_pri) == 4
        assert len(low_pri) == 4


class TestHBM4QueueManager:
    """Test HBM4QueueManager (32-channel, 64-depth)"""

    def test_manager_creation(self):
        """测试 HBM4 队列管理器创建"""
        manager = HBM4QueueManager(queue_depth=64, num_priority_classes=16)

        assert manager.read_queue.max_depth == 64
        assert manager.write_queue.max_depth == 64
        assert manager.read_queue._num_priority_classes == 16

    def test_clock_sync(self):
        """测试时钟同步"""
        manager = HBM4QueueManager()

        manager.tick(100)
        assert manager._global_clock == 100.0
        assert manager.read_queue.get_clock() == 100.0
        assert manager.write_queue.get_clock() == 100.0

    def test_push_read_write(self):
        """测试入队"""
        manager = HBM4QueueManager()

        read_req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=10)
        write_req = HBMRequest(addr=0x2000, length=64, is_read=False, qos=5)

        assert manager.push_read(read_req)
        assert manager.push_write(write_req)
        assert manager.total_size() == 2

        # 检查优先级是否正确 (使用 get_detailed_stats)
        stats = manager.get_stats()
        read_detailed = manager.read_queue.get_detailed_stats()
        write_detailed = manager.write_queue.get_detailed_stats()
        assert read_detailed['priority_distribution'][10] == 1
        assert write_detailed['priority_distribution'][5] == 1

    def test_pop_by_priority(self):
        """测试按优先级出队"""
        manager = HBM4QueueManager()

        low_req = HBMRequest(addr=0x1000, length=64, is_read=True, qos=1)
        high_req = HBMRequest(addr=0x2000, length=64, is_read=True, qos=15)

        manager.push_read(low_req)
        manager.push_read(high_req)

        # 最高优先级应该先出队
        best = manager.get_best_read()
        assert best.qos == 15

    def test_is_full(self):
        """测试队列满检测"""
        manager = HBM4QueueManager(queue_depth=2)

        manager.push_read(HBMRequest(addr=0x1000, length=64, is_read=True))
        manager.push_read(HBMRequest(addr=0x2000, length=64, is_read=True))

        assert manager.is_full()

    def test_per_channel_queues(self):
        """测试 per-channel 队列"""
        manager = HBM4QueueManager(
            queue_depth=64,
            per_channel_queues=True,
            num_channels=32
        )

        assert manager.per_channel_queues is True
        assert len(manager.channel_queues) == 32

        # 测试 per-channel 入队
        req = HBMRequest(addr=0x1000, length=64, is_read=True, channel_id=5)
        assert manager.push_read(req, channel_id=5)

        # 验证 channel 队列中有请求
        rq, _ = manager.channel_queues[5]
        assert rq.size() == 1

    def test_detailed_stats(self):
        """测试详细统计"""
        manager = HBM4QueueManager()

        for i in range(4):
            manager.push_read(HBMRequest(addr=0x1000 + i, length=64, is_read=True, qos=5 + i))

        stats = manager.get_stats()
        assert stats['total']['size'] == 4
        assert stats['clock'] == 0.0

        # 使用 get_detailed_stats 获取完整信息
        read_stats = manager.read_queue.get_detailed_stats()
        assert read_stats['push_count'] == 4
        assert 'priority_distribution' in read_stats

    def test_full_hbm4_scenario(self):
        """测试完整 HBM4 场景"""
        manager = HBM4QueueManager(queue_depth=64)

        # 模拟多个请求，不同优先级和到达时间
        manager.tick(100)

        # 4 个低优先级请求
        for i in range(4):
            req = HBMRequest(addr=0x1000 + i * 0x1000, length=64, is_read=True, qos=2)
            manager.push_read(req)

        # 2 个高优先级请求
        for i in range(2):
            req = HBMRequest(addr=0x2000 + i * 0x1000, length=64, is_read=True, qos=15)
            manager.push_read(req)

        manager.tick(100)

        # 验证高优先级请求先被调度
        best = manager.get_best_read()
        assert best.qos == 15

        # 验证统计数据 (使用 get_detailed_stats)
        stats = manager.get_stats()
        assert stats['total']['size'] == 6

        read_detailed = manager.read_queue.get_detailed_stats()
        assert read_detailed['priority_distribution'][15] == 2
        assert read_detailed['priority_distribution'][2] == 4


class TestPriorityQueueIntegration:
    """Integration tests for Priority Queue with real HBM4 parameters"""

    def test_hbm4_64_depth(self):
        """测试 HBM4 64 深度队列"""
        queue = PriorityQueue(max_depth=64)

        # 填满队列
        for i in range(64):
            req = HBMRequest(addr=0x1000 + i, length=64, is_read=True)
            assert queue.push(req) is True

        # 第 65 个应该失败
        overflow = HBMRequest(addr=0x5000, length=64, is_read=True)
        assert queue.push(overflow) is False

        assert queue.size() == 64
        assert queue.is_full()

    def test_hbm4_16_priority_classes(self):
        """测试 HBM4 16 个优先级类"""
        queue = PriorityQueue(max_depth=64, num_priority_classes=16)

        # 每个优先级放入一个请求
        for i in range(16):
            req = HBMRequest(addr=0x1000 + i, length=64, is_read=True, qos=i)
            queue.push(req)

        # 验证分布
        dist = queue.get_priority_distribution()
        assert all(dist[i] == 1 for i in range(16))

        # 验证调度顺序: 优先级 15 最高
        best = queue.get_best_request()
        assert best.qos == 15

    def test_age_tracking_integration(self):
        """测试年龄追踪集成"""
        queue = PriorityQueue(max_depth=64)
        queue.set_age_thresholds(high=1000.0, critical=5000.0)

        # 添加请求并推进时钟
        req = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=0.0)
        queue.push(req)

        queue.set_clock(3000.0)
        assert queue.get_request_age(req) == 3000.0
        assert not queue.is_starving(req)

        queue.set_clock(6000.0)
        assert queue.is_starving(req)

    def test_fr_fcfs_scheduling(self):
        """测试 FR-FCFS 调度"""
        queue = PriorityQueue(max_depth=64)
        queue.set_clock(100.0)

        # 创建请求: row-hit 和非 row-hit
        row_hit_req = HBMRequest(addr=0x1000, length=64, is_read=True, row_hit=True, arrival_time=50.0)
        no_hit_req = HBMRequest(addr=0x2000, length=64, is_read=True, row_hit=False, arrival_time=60.0)

        # FR-FCFS: 按年龄排序，忽略 row_hit (优先级队列中)
        queue.push(no_hit_req)
        queue.push(row_hit_req)

        best = queue.get_best_request()
        # 两者年龄相同但 no_hit 先入队
        # 实际上优先级队列按 arrival_time 排序
        assert best.request_id == row_hit_req.request_id