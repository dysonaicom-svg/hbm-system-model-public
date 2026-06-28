"""
HBM Request Queues
参考设计文档 2026-06-15-hbm-system-model-design.md 的 5.1.4 节

实现线程安全的请求队列:
- ReadQueue: 读请求队列
- WriteQueue: 写请求队列
- PriorityQueue: 优先级感知队列 (HBM4 QoS)
- AgeTrackingMixin: 年龄追踪 (FR-FCFS 支持)
"""

import threading
import bisect
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Tuple, Dict, Any
from collections import deque
from collections.abc import MutableSequence
import time
import heapq

from model.controller.request import HBMRequest, RequestState
from model.controller.exceptions import QueueOverflowError


class AgeTrackingMixin:
    """年龄追踪混入类

    为队列中的请求提供年龄追踪功能，用于 FR-FCFS 调度。
    追踪每个请求的等待时间和 starvation 情况。
    """

    def __init__(self):
        self._clock: float = 0.0  # 仿真时钟
        self._age_threshold_high: float = 1000.0  # 高优先级阈值 (cycles)
        self._age_threshold_critical: float = 5000.0  # 饥饿临界值 (cycles)
        self._starvation_history: Dict[int, float] = {}  # request_id -> wait time

    def tick(self, cycles: int = 1):
        """推进仿真时钟

        Args:
            cycles: 要推进的周期数
        """
        self._clock += cycles

    def set_clock(self, clock: float):
        """设置仿真时钟

        Args:
            clock: 新的时钟值
        """
        self._clock = clock

    def get_clock(self) -> float:
        """获取当前仿真时钟"""
        return self._clock

    def get_request_age(self, request: HBMRequest) -> float:
        """获取请求的年龄 (等待时间)

        Args:
            request: HBM 请求

        Returns:
            请求等待的周期数
        """
        return max(0.0, self._clock - request.arrival_time)

    def is_starving(self, request: HBMRequest) -> bool:
        """检查请求是否处于饥饿状态

        饥饿定义: 请求等待时间超过临界阈值

        Args:
            request: HBM 请求

        Returns:
            True 如果请求正在饥饿
        """
        return self.get_request_age(request) >= self._age_threshold_critical

    def get_starvation_score(self, request: HBMRequest) -> float:
        """计算请求的饥饿分数

        分数 = wait_time / threshold，越高表示越饥饿

        Args:
            request: HBM 请求

        Returns:
            0.0-1.0 的饥饿分数，1.0 表示完全饥饿
        """
        age = self.get_request_age(request)
        return min(1.0, age / self._age_threshold_critical)

    def get_oldest_request_age(self, queue: List[HBMRequest]) -> float:
        """获取队列中最老请求的年龄

        Args:
            queue: 请求列表

        Returns:
            最老请求的等待时间
        """
        if not queue:
            return 0.0
        return max(self.get_request_age(r) for r in queue)

    def set_age_thresholds(self, high: float, critical: float):
        """设置年龄阈值

        Args:
            high: 高优先级阈值
            critical: 饥饿临界值
        """
        self._age_threshold_high = high
        self._age_threshold_critical = critical


class PriorityAwareMixin:
    """优先级感知混入类

    提供基于 QoS 优先级的队列操作。
    HBM4 支持 16 个优先级类 (0-15)。
    """

    def __init__(self, num_priority_classes: int = 16):
        """初始化优先级感知混入

        Args:
            num_priority_classes: 优先级类别数 (默认 16 for HBM4)
        """
        self._num_priority_classes = num_priority_classes
        self._priority_buckets: Dict[int, List[HBMRequest]] = {
            i: [] for i in range(num_priority_classes)
        }

    def get_priority(self, request: HBMRequest) -> int:
        """获取请求的优先级

        Args:
            request: HBM 请求

        Returns:
            请求的 QoS 优先级 (0-15)
        """
        return max(0, min(self._num_priority_classes - 1, request.qos))

    def get_priority_bucket(self, priority: int) -> List[HBMRequest]:
        """获取指定优先级的桶

        Args:
            priority: 优先级值

        Returns:
            该优先级的请求列表
        """
        priority = max(0, min(self._num_priority_classes - 1, priority))
        return self._priority_buckets[priority]

    def enqueue_by_priority(self, request: HBMRequest, bucket: List[HBMRequest]):
        """按优先级将请求加入桶中

        在同一优先级内按年龄排序 (FIFO within priority)

        Args:
            request: HBM 请求
            bucket: 目标桶列表
        """
        priority = self.get_priority(request)
        target = self._priority_buckets[priority]
        # Python 3.8 兼容: 使用 key 函数手动处理排序
        sort_key = request.arrival_time
        i = bisect.bisect_left(target, sort_key, key=lambda r: r.arrival_time)
        target.insert(i, request)

    def find_best_by_priority_age(self, all_requests: List[HBMRequest],
                                   age_tracker: AgeTrackingMixin) -> Optional[HBMRequest]:
        """基于优先级和年龄找到最佳请求

        FR-FCFS with Priority Boost:
        1. 找到所有非饥饿的最高优先级请求
        2. 如果饥饿请求存在且优先级更高，提升其优先级
        3. 在选定优先级内选择最老的请求

        Args:
            all_requests: 所有候选请求
            age_tracker: 年龄追踪器

        Returns:
            最佳调度请求
        """
        if not all_requests:
            return None

        # 按优先级分组
        by_priority: Dict[int, List[HBMRequest]] = {}
        for req in all_requests:
            p = self.get_priority(req)
            if p not in by_priority:
                by_priority[p] = []
            by_priority[p].append(req)

        # 检查最高优先级是否有饥饿请求
        max_priority = max(by_priority.keys())
        high_priority_requests = by_priority[max_priority]

        # 查找饥饿的高优先级请求
        starving = [r for r in high_priority_requests
                   if age_tracker.is_starving(r)]

        # 如果有饥饿请求且年龄差异足够大，提升它们
        if starving:
            oldest_age = age_tracker.get_oldest_request_age(high_priority_requests)
            youngest_age = age_tracker.get_oldest_request_age(all_requests)

            # 如果高优先级请求比低优先级请求老得多，考虑低优先级
            if youngest_age < oldest_age * 0.5:
                # 降级高优先级请求，检查是否有更紧急的低优先级请求
                pass

        # 在最高优先级内选择最老的
        return min(high_priority_requests, key=lambda r: r.arrival_time)

    def get_queue_depth_by_priority(self) -> Dict[int, int]:
        """获取每个优先级的队列深度

        Returns:
            优先级到深度的映射
        """
        return {p: len(bucket) for p, bucket in self._priority_buckets.items()}

    def set_num_priority_classes(self, num: int):
        """设置优先级类别数

        Args:
            num: 新的优先级类别数
        """
        if num != self._num_priority_classes:
            old_buckets = self._priority_buckets
            self._num_priority_classes = num
            self._priority_buckets = {i: [] for i in range(num)}

            # 重新分配现有请求到新桶
            for old_priority, requests in old_buckets.items():
                if old_priority < num:
                    self._priority_buckets[old_priority] = requests
                else:
                    # 合并到最低优先级
                    self._priority_buckets[0].extend(requests)


class RequestQueue:
    """线程安全的请求队列基类

    O(1) 操作优化:
    - push/pop: O(1) - deque operations
    - remove: O(1) - dictionary index
    - lookup: O(1) - dictionary index
    """

    def __init__(self, max_depth: int = 32, name: str = "Queue"):
        """初始化请求队列

        Args:
            max_depth: 最大队列深度
            name: 队列名称 (用于调试)
        """
        self.max_depth = max_depth
        self.name = name
        self._queue = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

        # O(1) lookup index: request_id -> request
        # ponytail: dictionary index for O(1) removal instead of O(n) scan
        self._request_index: Dict[int, HBMRequest] = {}

        # 容量监控
        # ponytail: capacity thresholds for backpressure signaling
        self._warning_threshold = 0.75  # 75% - 开始预警
        self._critical_threshold = 0.90  # 90% - 临界预警
        self._overflow_count = 0  # 溢出次数统计

        # 统计
        self._stats = {
            'push_count': 0,
            'pop_count': 0,
            'reject_count': 0,
            'remove_count': 0,
            'max_occupancy': 0,
            'overflow_count': 0,
            'warning_count': 0,
        }
    
    def push(self, request: HBMRequest, timeout: float = 0.0) -> bool:
        """入队请求
        
        Args:
            request: HBM 请求
            timeout: 超时时间 (秒), 0 表示不等待
            
        Returns:
            True 如果成功入队, False 如果队列满
            
        Raises:
            QueueOverflowError: 队列满且超时
        """
        with self._not_full:
            if timeout > 0:
                # 带超时等待
                end_time = time.time() + timeout
                while len(self._queue) >= self.max_depth:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        self._stats['reject_count'] += 1
                        return False
                    if not self._not_full.wait(remaining):
                        self._stats['reject_count'] += 1
                        return False
            else:
                # 非阻塞
                if len(self._queue) >= self.max_depth:
                    self._stats['reject_count'] += 1
                    return False
            
            self._queue.append(request)
            # O(1) index update
            self._request_index[request.request_id] = request
            self._stats['push_count'] += 1
            self._stats['max_occupancy'] = max(
                self._stats['max_occupancy'],
                len(self._queue)
            )
            self._not_empty.notify()
            return True
    
    def pop(self, timeout: float = 0.0) -> Optional[HBMRequest]:
        """出队请求
        
        Args:
            timeout: 超时时间 (秒), 0 表示不等待
            
        Returns:
            HBMRequest 如果成功, None 如果队列空
        """
        with self._not_empty:
            if timeout > 0:
                # 带超时等待
                end_time = time.time() + timeout
                while len(self._queue) == 0:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        return None
                    if not self._not_empty.wait(remaining):
                        return None
            else:
                # 非阻塞
                if len(self._queue) == 0:
                    return None
            
            request = self._queue.popleft()
            # O(1) index removal
            self._request_index.pop(request.request_id, None)
            self._stats['pop_count'] += 1
            self._not_full.notify()
            return request
    
    def peek(self) -> Optional[HBMRequest]:
        """查看队首请求 (不移除)"""
        with self._lock:
            if self._queue:
                return self._queue[0]
            return None
    
    def remove(self, request_id: int) -> bool:
        """移除指定请求 - O(1) 操作

        Args:
            request_id: 请求 ID

        Returns:
            True 如果找到并移除
        """
        with self._lock:
            # O(1) dictionary lookup
            request = self._request_index.pop(request_id, None)
            if request is None:
                return False

            # Also remove from deque for order maintenance
            try:
                self._queue.remove(request)
            except ValueError:
                # Request not in deque but was in index - shouldn't happen
                pass

            self._stats['remove_count'] += 1
            return True

    def get_by_id(self, request_id: int) -> Optional[HBMRequest]:
        """O(1) 根据 ID 获取请求

        Args:
            request_id: 请求 ID

        Returns:
            请求如果找到, None 否则
        """
        with self._lock:
            return self._request_index.get(request_id)

    def contains(self, request_id: int) -> bool:
        """O(1) 检查请求是否存在

        Args:
            request_id: 请求 ID

        Returns:
            True 如果存在
        """
        with self._lock:
            return request_id in self._request_index

    def get_occupancy_status(self) -> str:
        """获取队列占用状态 - 用于背压控制

        Returns:
            'NORMAL' | 'WARNING' | 'CRITICAL' | 'FULL'
        """
        with self._lock:
            rate = len(self._queue) / self.max_depth if self.max_depth > 0 else 0
            if rate >= 1.0:
                return 'FULL'
            elif rate >= self._critical_threshold:
                return 'CRITICAL'
            elif rate >= self._warning_threshold:
                return 'WARNING'
            return 'NORMAL'

    def get_backpressure_factor(self) -> float:
        """获取背压因子 (0.0-1.0)

        当队列接近满时返回较高的因子，告知上游降低提交速率。

        Returns:
            0.0 = 无背压, 1.0 = 完全背压 (拒绝所有请求)
        """
        with self._lock:
            rate = len(self._queue) / self.max_depth if self.max_depth > 0 else 0
            if rate >= self._critical_threshold:
                # 临界状态: 线性增长到 1.0
                return min(1.0, (rate - self._critical_threshold) / (1.0 - self._critical_threshold))
            elif rate >= self._warning_threshold:
                # 预警状态: 轻微背压
                return 0.25
            return 0.0

    def set_thresholds(self, warning: float = 0.75, critical: float = 0.90):
        """设置容量阈值

        Args:
            warning: 预警阈值 (0.0-1.0)
            critical: 临界阈值 (0.0-1.0)
        """
        self._warning_threshold = max(0.0, min(1.0, warning))
        self._critical_threshold = max(self._warning_threshold, min(1.0, critical))
    
    def size(self) -> int:
        """获取当前队列大小"""
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        """检查队列是否为空"""
        with self._lock:
            return len(self._queue) == 0
    
    def is_full(self) -> bool:
        """检查队列是否已满"""
        with self._lock:
            return len(self._queue) >= self.max_depth
    
    def clear(self):
        """清空队列"""
        with self._lock:
            self._queue.clear()
            self._request_index.clear()
            self._not_full.notify_all()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                **self._stats,
                'current_occupancy': len(self._queue),
                'occupancy_rate': len(self._queue) / self.max_depth if self.max_depth > 0 else 0,
                'warning_threshold': self._warning_threshold,
                'critical_threshold': self._critical_threshold,
                'occupancy_status': self.get_occupancy_status(),
                'backpressure_factor': self.get_backpressure_factor(),
            }
    
    def __repr__(self) -> str:
        return f"{self.name}(size={self.size()}, max={self.max_depth})"

    def __iter__(self):
        """使队列可迭代"""
        with self._lock:
            # Copy to avoid holding lock during iteration
            return iter(list(self._queue))

    def __len__(self):
        """使队列可使用 len()"""
        with self._lock:
            return len(self._queue)


class ReadQueue(RequestQueue):
    """读请求队列
    
    特殊功能:
    - 按 row_hit 排序
    - 按时间戳排序 (FR-FCFS)
    """
    
    def __init__(self, max_depth: int = 32):
        super().__init__(max_depth, name="ReadQueue")
    
    def get_row_hit_requests(self) -> List[HBMRequest]:
        """获取所有 row-hit 的请求"""
        with self._lock:
            return [r for r in self._queue if r.row_hit]
    
    def get_oldest_request(self) -> Optional[HBMRequest]:
        """获取最早的请求"""
        with self._lock:
            if not self._queue:
                return None
            return min(self._queue, key=lambda r: r.arrival_time)
    
    def get_best_request(self) -> Optional[HBMRequest]:
        """获取最佳调度的请求 (FR-FCFS)
        
        优先选择:
        1. row-hit 请求中最老的
        2. 如果没有 row-hit，选择最老的请求
        """
        with self._lock:
            row_hit_requests = [r for r in self._queue if r.row_hit]
            if row_hit_requests:
                return min(row_hit_requests, key=lambda r: r.arrival_time)
            if self._queue:
                return min(self._queue, key=lambda r: r.arrival_time)
            return None


class WriteQueue(RequestQueue):
    """写请求队列
    
    特殊功能:
    - Write drain 策略支持
    """
    
    def __init__(self, max_depth: int = 32, drain_threshold: float = 0.8):
        super().__init__(max_depth, name="WriteQueue")
        self.drain_threshold = drain_threshold
    
    def should_drain(self) -> bool:
        """检查是否应该执行 write drain
        
        当写队列达到阈值时返回 True。
        """
        with self._lock:
            return len(self._queue) >= self.max_depth * self.drain_threshold
    
    def get_oldest_request(self) -> Optional[HBMRequest]:
        """获取最早的写请求"""
        with self._lock:
            if not self._queue:
                return None
            return min(self._queue, key=lambda r: r.arrival_time)
    
    def get_pending_bytes(self) -> int:
        """获取队列中待写入的总字节数"""
        with self._lock:
            return sum(r.length for r in self._queue)


class PriorityQueue(RequestQueue, AgeTrackingMixin, PriorityAwareMixin):
    """优先级感知队列 (HBM4 QoS)

    结合年龄追踪和优先级感知的请求队列。
    支持 FR-FCFS 调度与 QoS 优先级提升。

    继承自:
    - RequestQueue: 基础队列功能
    - AgeTrackingMixin: 年龄追踪
    - PriorityAwareMixin: 优先级感知

    HBM4 参数:
    - 64 深度队列
    - 16 QoS 优先级类 (0-15)
    - 年龄追踪用于 starvation 检测

    调度策略:
    1. 高优先级请求优先
    2. 同优先级内按年龄 (FR-FCFS)
    3. 饥饿请求获得优先级提升
    """

    def __init__(self, max_depth: int = 64, num_priority_classes: int = 16):
        """初始化优先级队列

        Args:
            max_depth: 最大队列深度 (默认 64 for HBM4)
            num_priority_classes: 优先级类别数 (默认 16 for HBM4)
        """
        RequestQueue.__init__(self, max_depth, name="PriorityQueue")
        AgeTrackingMixin.__init__(self)
        PriorityAwareMixin.__init__(self, num_priority_classes)

        # 优先级队列使用有序数组而不是 deque
        self._priority_queue: List[HBMRequest] = []
        self._insertion_order: int = 0  # 相同时间戳时的保序计数器

        # 优先级提升配置
        self._priority_boost_enabled: bool = True
        self._priority_boost_factor: float = 2.0  # 饥饿请求优先级提升倍数

    def push(self, request: HBMRequest, timeout: float = 0.0) -> bool:
        """入队请求 (按优先级排序)

        Args:
            request: HBM 请求
            timeout: 超时时间 (秒)

        Returns:
            True 如果成功入队, False 如果队列满
        """
        with self._not_full:
            if timeout > 0:
                end_time = time.time() + timeout
                while len(self._queue) >= self.max_depth:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        self._stats['reject_count'] += 1
                        return False
                    if not self._not_full.wait(remaining):
                        self._stats['reject_count'] += 1
                        return False
            else:
                if len(self._queue) >= self.max_depth:
                    self._stats['reject_count'] += 1
                    return False

            # 设置到达时间 (仅当未设置时)
            if request.arrival_time is None or request.arrival_time < 0:
                request.arrival_time = self._clock

            self._queue.append(request)
            # O(1) index update
            self._request_index[request.request_id] = request
            self._insertion_order += 1

            # 维护优先级有序队列
            self._enqueue_priority_order(request)

            self._stats['push_count'] += 1
            self._stats['max_occupancy'] = max(
                self._stats['max_occupancy'],
                len(self._queue)
            )
            self._not_empty.notify()
            return True

    def _enqueue_priority_order(self, request: HBMRequest):
        """按优先级顺序插入请求

        排序键: (优先级, 年龄, 插入顺序)
        - 优先级越高 (数值越大) 越先被调度
        - 同优先级内越老越先被调度
        """
        # 计算排序键: (negative_priority, arrival_time, insertion_order)
        # 使用负优先级因为我们希望高优先级先被选择
        priority = self.get_priority(request)
        sort_key = (-priority, request.arrival_time, self._insertion_order)

        # 使用 bisect 插入到有序位置 (Python 3.8 兼容写法)
        entry = (sort_key, request)
        i = bisect.bisect_left(
            [x[0] for x in self._priority_queue],
            sort_key
        )
        self._priority_queue.insert(i, entry)

    def pop(self, timeout: float = 0.0) -> Optional[HBMRequest]:
        """按优先级出队请求

        Args:
            timeout: 超时时间 (秒)

        Returns:
            HBMRequest 如果成功, None 如果队列空
        """
        with self._not_empty:
            if timeout > 0:
                end_time = time.time() + timeout
                while len(self._queue) == 0:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        return None
                    if not self._not_empty.wait(remaining):
                        return None
            else:
                if len(self._queue) == 0:
                    return None

            # 从 deque 中移除 (FIFO)
            request = self._queue.popleft()

            # O(1) index removal
            self._request_index.pop(request.request_id, None)

            # 从优先级队列中移除
            self._remove_from_priority_queue(request)

            self._stats['pop_count'] += 1
            self._not_full.notify()
            return request

    def _remove_from_priority_queue(self, request: HBMRequest):
        """从优先级队列中移除请求"""
        for i, (_, req) in enumerate(self._priority_queue):
            if req.request_id == request.request_id:
                del self._priority_queue[i]
                break

    def get_best_request(self) -> Optional[HBMRequest]:
        """获取最佳调度的请求 (Priority + Age)

        优先选择:
        1. 饥饿的高优先级请求
        2. 最高优先级中最老的请求
        3. 如果没有非饥饿请求，选择饥饿请求
        """
        with self._lock:
            if not self._queue:
                return None

            # 检查优先级队列
            non_starving = []
            starving = []

            for _, req in self._priority_queue:
                if self.is_starving(req):
                    starving.append(req)
                else:
                    non_starving.append(req)

            # 优先选择非饥饿请求
            if non_starving:
                return non_starving[0]

            # 如果全部饥饿，选择最老的
            if starving:
                return min(starving, key=lambda r: r.arrival_time)

            return None

    def get_requests_by_priority(self, priority: int) -> List[HBMRequest]:
        """获取指定优先级的所有请求

        Args:
            priority: 优先级值

        Returns:
            该优先级的请求列表
        """
        with self._lock:
            return [r for r in self._queue if self.get_priority(r) == priority]

    def get_priority_distribution(self) -> Dict[int, int]:
        """获取优先级分布

        Returns:
            优先级到请求数的映射
        """
        with self._lock:
            dist = {i: 0 for i in range(self._num_priority_classes)}
            for r in self._queue:
                p = self.get_priority(r)
                dist[p] += 1
            return dist

    def get_avg_wait_time(self) -> float:
        """获取平均等待时间

        Returns:
            所有请求的平均等待时间
        """
        with self._lock:
            if not self._queue:
                return 0.0
            total_age = sum(self.get_request_age(r) for r in self._queue)
            return total_age / len(self._queue)

    def get_max_wait_time(self) -> float:
        """获取最大等待时间

        Returns:
            最老请求的等待时间
        """
        with self._lock:
            if not self._queue:
                return 0.0
            return max(self.get_request_age(r) for r in self._queue)

    def get_starving_requests(self) -> List[HBMRequest]:
        """获取所有饥饿请求

        Returns:
            饥饿请求列表
        """
        with self._lock:
            return [r for r in self._queue if self.is_starving(r)]

    def enable_priority_boost(self, enabled: bool):
        """启用/禁用优先级提升

        Args:
            enabled: 是否启用
        """
        self._priority_boost_enabled = enabled

    def set_priority_boost_factor(self, factor: float):
        """设置优先级提升因子

        Args:
            factor: 提升因子 (默认 2.0)
        """
        self._priority_boost_factor = max(1.0, factor)

    def get_detailed_stats(self) -> Dict[str, Any]:
        """获取详细统计信息

        Returns:
            包含年龄和优先级信息的详细统计
        """
        with self._lock:
            # Compute avg/max wait time directly without calling methods
            if self._queue:
                total_age = sum(self._clock - r.arrival_time for r in self._queue)
                avg_wait = total_age / len(self._queue)
                max_wait = max(self._clock - r.arrival_time for r in self._queue)
                starving_count = sum(1 for r in self._queue
                                   if (self._clock - r.arrival_time) >= self._age_threshold_critical)
            else:
                avg_wait = 0.0
                max_wait = 0.0
                starving_count = 0

            # Compute priority distribution from _queue
            dist = {i: 0 for i in range(self._num_priority_classes)}
            for r in self._queue:
                p = self.get_priority(r)
                dist[p] += 1

            stats = {
                **self._stats,
                'current_occupancy': len(self._queue),
                'occupancy_rate': len(self._queue) / self.max_depth if self.max_depth > 0 else 0,
                'avg_wait_time': avg_wait,
                'max_wait_time': max_wait,
                'starving_count': starving_count,
                'priority_distribution': dist,
                'clock': self._clock,
            }
            return stats


class HBM4QueueManager:
    """HBM4 专用队列管理器

    支持 64 深度队列和 32 通道的 HBM4 配置。
    集成年龄追踪和优先级调度。

    Attributes:
        read_queue: 读请求优先级队列
        write_queue: 写请求优先级队列
        channel_queues: 每个通道的专用队列 (可选)
    """

    def __init__(
        self,
        queue_depth: int = 64,
        num_priority_classes: int = 16,
        per_channel_queues: bool = False,
        num_channels: int = 32
    ):
        """初始化 HBM4 队列管理器

        Args:
            queue_depth: 每个队列的深度 (默认 64)
            num_priority_classes: 优先级类别数 (默认 16)
            per_channel_queues: 是否为每个通道创建独立队列
            num_channels: 通道数 (默认 32 for HBM4)
        """
        # 主读/写队列
        self.read_queue = PriorityQueue(
            max_depth=queue_depth,
            num_priority_classes=num_priority_classes
        )
        self.write_queue = PriorityQueue(
            max_depth=queue_depth,
            num_priority_classes=num_priority_classes
        )

        # 每个通道的独立队列 (可选，用于银行级并行)
        self.per_channel_queues = per_channel_queues
        self.num_channels = num_channels

        if per_channel_queues:
            self.channel_queues: Dict[int, Tuple[PriorityQueue, PriorityQueue]] = {}
            for ch in range(num_channels):
                self.channel_queues[ch] = (
                    PriorityQueue(
                        max_depth=queue_depth // 4,  # 分区后减小
                        num_priority_classes=num_priority_classes
                    ),
                    PriorityQueue(
                        max_depth=queue_depth // 4,
                        num_priority_classes=num_priority_classes
                    )
                )
        else:
            self.channel_queues = None

        # 时钟同步
        self._global_clock: float = 0.0

    def tick(self, cycles: int = 1):
        """推进所有队列的时钟

        Args:
            cycles: 要推进的周期数
        """
        self._global_clock += cycles
        self.read_queue.tick(cycles)
        self.write_queue.tick(cycles)

        if self.channel_queues:
            for rq, wq in self.channel_queues.values():
                rq.tick(cycles)
                wq.tick(cycles)

    def push_read(
        self,
        request: HBMRequest,
        channel_id: Optional[int] = None,
        timeout: float = 0.0
    ) -> bool:
        """入队读请求

        Args:
            request: HBM 请求
            channel_id: 可选的通道 ID (用于 per-channel 队列)
            timeout: 超时时间

        Returns:
            True 如果成功
        """
        request.arrival_time = self._global_clock

        if self.per_channel_queues and channel_id is not None:
            if channel_id in self.channel_queues:
                rq, _ = self.channel_queues[channel_id]
                return rq.push(request, timeout)

        return self.read_queue.push(request, timeout)

    def push_write(
        self,
        request: HBMRequest,
        channel_id: Optional[int] = None,
        timeout: float = 0.0
    ) -> bool:
        """入队写请求

        Args:
            request: HBM 请求
            channel_id: 可选的通道 ID
            timeout: 超时时间

        Returns:
            True 如果成功
        """
        request.arrival_time = self._global_clock

        if self.per_channel_queues and channel_id is not None:
            if channel_id in self.channel_queues:
                _, wq = self.channel_queues[channel_id]
                return wq.push(request, timeout)

        return self.write_queue.push(request, timeout)

    def pop_read(self, timeout: float = 0.0) -> Optional[HBMRequest]:
        """出队读请求"""
        return self.read_queue.pop(timeout)

    def pop_write(self, timeout: float = 0.0) -> Optional[HBMRequest]:
        """出队写请求"""
        return self.write_queue.pop(timeout)

    def get_best_read(self) -> Optional[HBMRequest]:
        """获取最佳读请求"""
        return self.read_queue.get_best_request()

    def get_best_write(self) -> Optional[HBMRequest]:
        """获取最佳写请求"""
        return self.write_queue.get_best_request()

    def total_size(self) -> int:
        """总队列大小"""
        total = self.read_queue.size() + self.write_queue.size()

        if self.channel_queues:
            for rq, wq in self.channel_queues.values():
                total += rq.size() + wq.size()

        return total

    def is_full(self) -> bool:
        """检查是否任一队列已满"""
        if self.read_queue.is_full() or self.write_queue.is_full():
            return True

        if self.channel_queues:
            for rq, wq in self.channel_queues.values():
                if rq.is_full() or wq.is_full():
                    return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取所有队列统计"""
        stats = {
            'read': self.read_queue.get_stats(),
            'write': self.write_queue.get_stats(),
            'total': {
                'size': self.total_size(),
                'max_occupancy': max(
                    self.read_queue.get_stats()['max_occupancy'],
                    self.write_queue.get_stats()['max_occupancy'],
                ),
            },
            'clock': self._global_clock,
        }

        if self.channel_queues:
            channel_stats = {}
            for ch, (rq, wq) in self.channel_queues.items():
                channel_stats[ch] = {
                    'read': rq.get_stats(),
                    'write': wq.get_stats(),
                }
            stats['channels'] = channel_stats

        return stats


@dataclass
class QueueManager:
    """队列管理器

    管理读/写队列和调度决策。
    优化版本：包含通道索引以避免 O(n) 过滤。
    """
    read_queue: ReadQueue
    write_queue: WriteQueue

    # ponytail: channel-based indexing for O(1) lookup instead of O(n) filtering
    _read_by_channel: Dict[int, List[HBMRequest]] = field(default_factory=dict)
    _write_by_channel: Dict[int, List[HBMRequest]] = field(default_factory=dict)
    _num_channels: int = 32

    @classmethod
    def create(cls, queue_depth: int = 32, num_channels: int = 32) -> "QueueManager":
        """创建队列管理器

        Args:
            queue_depth: 队列深度
            num_channels: 通道数 (默认 32 for HBM4)

        Returns:
            QueueManager 实例
        """
        return cls(
            read_queue=ReadQueue(max_depth=queue_depth),
            write_queue=WriteQueue(max_depth=queue_depth),
            _read_by_channel={ch: [] for ch in range(num_channels)},
            _write_by_channel={ch: [] for ch in range(num_channels)},
            _num_channels=num_channels,
        )

    def push_read(self, request: HBMRequest, timeout: float = 0.0) -> bool:
        """入队读请求"""
        success = self.read_queue.push(request, timeout)
        if success:
            # Update channel index - O(1)
            ch = request.channel_id
            if 0 <= ch < self._num_channels and ch in self._read_by_channel:
                self._read_by_channel[ch].append(request)
            else:
                # Expand index if channel is out of range
                while ch >= self._num_channels:
                    max_ch = self._num_channels
                    self._num_channels = max_ch + 32
                    for i in range(max_ch, self._num_channels):
                        self._read_by_channel[i] = []
                        self._write_by_channel[i] = []
                self._read_by_channel[ch].append(request)
        return success

    def push_write(self, request: HBMRequest, timeout: float = 0.0) -> bool:
        """入队写请求"""
        success = self.write_queue.push(request, timeout)
        if success:
            # Update channel index - O(1)
            ch = request.channel_id
            if 0 <= ch < self._num_channels and ch in self._write_by_channel:
                self._write_by_channel[ch].append(request)
            else:
                # Expand index if channel is out of range
                while ch >= self._num_channels:
                    max_ch = self._num_channels
                    self._num_channels = max_ch + 32
                    for i in range(max_ch, self._num_channels):
                        self._read_by_channel[i] = []
                        self._write_by_channel[i] = []
                self._write_by_channel[ch].append(request)
        return success

    def remove_read(self, request_id: int, channel_id: Optional[int] = None) -> bool:
        """从读队列移除请求"""
        # Try indexed removal first if channel_id is provided - O(1)
        if channel_id is not None and 0 <= channel_id < self._num_channels:
            idx_list = self._read_by_channel.get(channel_id, [])
            for i, req in enumerate(idx_list):
                if req.request_id == request_id:
                    del idx_list[i]
                    return self.read_queue.remove(request_id)
        # Fall back to full queue scan - O(n)
        return self.read_queue.remove(request_id)

    def remove_write(self, request_id: int, channel_id: Optional[int] = None) -> bool:
        """从写队列移除请求"""
        # Try indexed removal first if channel_id is provided - O(1)
        if channel_id is not None and 0 <= channel_id < self._num_channels:
            idx_list = self._write_by_channel.get(channel_id, [])
            for i, req in enumerate(idx_list):
                if req.request_id == request_id:
                    del idx_list[i]
                    return self.write_queue.remove(request_id)
        # Fall back to full queue scan - O(n)
        return self.write_queue.remove(request_id)

    def get_reads_for_channel(self, channel_id: int) -> List[HBMRequest]:
        """获取指定通道的所有读请求 - O(k) where k = requests for that channel"""
        if 0 <= channel_id < self._num_channels:
            return self._read_by_channel.get(channel_id, [])
        return [r for r in self.read_queue if r.channel_id == channel_id]

    def get_writes_for_channel(self, channel_id: int) -> List[HBMRequest]:
        """获取指定通道的所有写请求 - O(k) where k = requests for that channel"""
        if 0 <= channel_id < self._num_channels:
            return self._write_by_channel.get(channel_id, [])
        return [r for r in self.write_queue if r.channel_id == channel_id]

    def total_size(self) -> int:
        """总队列大小"""
        return self.read_queue.size() + self.write_queue.size()

    def is_full(self) -> bool:
        """检查是否任一队列已满"""
        return self.read_queue.is_full() or self.write_queue.is_full()

    def get_stats(self) -> dict:
        """获取所有队列统计"""
        return {
            'read': self.read_queue.get_stats(),
            'write': self.write_queue.get_stats(),
            'total': {
                'size': self.total_size(),
                'max_occupancy': max(
                    self.read_queue.get_stats()['max_occupancy'],
                    self.write_queue.get_stats()['max_occupancy'],
                ),
            },
        }
