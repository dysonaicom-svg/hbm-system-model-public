"""
Phase A Integration Tests
测试所有 Phase A 模块的集成
"""

import sys
sys.path.insert(0, '/home/ic/JXTF/HBM')

import pytest
import time

from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.request import HBMRequest, RequestState
from model.controller.queue import ReadQueue, WriteQueue, QueueManager
from model.controller.address_decoder import AddressDecoder, DecodedAddress
from model.controller.scheduler import FRFCFSScheduler, BankState
from model.controller.qos_scheduler import QoSScheduler
from model.controller.refresh_scheduler import RefreshScheduler, RefreshManager
from model.controller.controller import HBMController
from model.controller.exceptions import AddressError


class TestHBMConfig:
    """测试 HBMConfig"""
    
    def test_default_config(self):
        config = HBMConfig()
        assert config.stack_count == 2
        assert config.channels_per_stack == 8
        assert config.burst_length == 32
    
    def test_bandwidth_calc(self):
        config = HBM3_DEFAULT
        bw = config.calc_bandwidth()
        assert abs(bw - 819.2) < 0.1, f"Expected 819.2 GB/s, got {bw}"


class TestHBMRequest:
    """测试 HBMRequest"""
    
    def test_request_creation(self):
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        assert req.addr == 0x1000
        assert req.length == 64
        assert req.is_read == True
        assert req.state == RequestState.PENDING
    
    def test_request_state_transitions(self):
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        req.mark_scheduled(time.time())
        assert req.state == RequestState.SCHEDULED
        
        req.mark_completed(time.time())
        assert req.state == RequestState.COMPLETED


class TestAddressDecoder:
    """测试地址解码器"""
    
    def test_decode_rbc(self):
        config = HBMConfig(address_mapping="rbc")
        decoder = AddressDecoder(config)
        
        # 测试地址解码
        addr = 0x0001_0000_0000_1000
        decoded = decoder.decode(addr)
        
        assert isinstance(decoded, DecodedAddress)
        assert decoded.channel_id < config.channels_per_stack
    
    def test_address_alignment(self):
        config = HBMConfig()
        decoder = AddressDecoder(config)
        
        # 未对齐地址应该抛出异常
        with pytest.raises(AddressError):
            decoder.decode(0x1001)  # 奇数地址


class TestQueues:
    """测试请求队列"""
    
    def test_read_queue_push_pop(self):
        queue = ReadQueue(max_depth=10)
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        
        assert queue.push(req) == True
        assert queue.size() == 1
        
        popped = queue.pop()
        assert popped == req
        assert queue.size() == 0
    
    def test_queue_full(self):
        queue = ReadQueue(max_depth=2)
        queue.push(HBMRequest(addr=0x1000, length=64, is_read=True))
        queue.push(HBMRequest(addr=0x2000, length=64, is_read=True))
        
        assert queue.is_full() == True
        assert queue.push(HBMRequest(addr=0x3000, length=64, is_read=True)) == False


class TestScheduler:
    """测试调度器"""
    
    def test_frfcfs_row_hit_priority(self):
        config = HBMConfig()
        scheduler = FRFCFSScheduler(config)
        read_q = ReadQueue(max_depth=10)
        
        # Row hit 请求
        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        req1.row_hit = True
        req1.arrival_time = time.time() + 1
        
        # Row miss 请求
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True)
        req2.row_hit = False
        req2.arrival_time = time.time()
        
        read_q.push(req1)
        read_q.push(req2)
        
        bank_states = {}
        scheduled = scheduler.schedule(read_q, WriteQueue(max_depth=10), bank_states, time.time())
        
        # 应该优先调度 row hit 请求
        assert scheduled == req1


class TestRefreshScheduler:
    """测试刷新调度器"""
    
    def test_refresh_scheduling(self):
        config = HBM3_DEFAULT
        scheduler = RefreshScheduler(config)
        
        current_time = 0.0
        cmd = scheduler.schedule_refresh(current_time, {})
        
        assert cmd is not None
        assert cmd.duration_cycles > 0
    
    def test_refresh_overhead(self):
        config = HBM3_DEFAULT
        scheduler = RefreshScheduler(config)
        
        overhead = scheduler.calc_refresh_overhead(1.0)  # 1 second
        assert overhead > 0 and overhead < 0.1, f"Unexpected overhead: {overhead}"


class TestHBMController:
    """测试 HBM 控制器集成"""
    
    def test_controller_submit_request(self):
        controller = HBMController()
        
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        success = controller.submit_request(req)
        
        assert success == True
        assert controller.stats['total_requests'] == 1
    
    def test_controller_tick(self):
        controller = HBMController()
        
        # 提交请求
        for i in range(10):
            req = HBMRequest(addr=0x1000 + i * 0x1000, length=64, is_read=True)
            controller.submit_request(req)
        
        # 执行多个周期
        for _ in range(100):
            controller.tick()
        
        stats = controller.get_stats()
        assert stats['controller']['total_requests'] == 10


def test_all_modules():
    """综合测试"""
    print("\n=== Phase A Integration Test ===")
    
    # 1. 配置
    config = HBM3_DEFAULT
    print(f"Config: stack={config.stack_count}, channels={config.channels_per_stack}")
    print(f"Bandwidth: {config.calc_bandwidth():.1f} GB/s")
    
    # 2. 控制器
    controller = HBMController(config)
    print(f"Controller initialized")
    
    # 3. 提交请求
    for i in range(20):
        req = HBMRequest(addr=0x1000 + i * 0x1000, length=64, is_read=(i % 2 == 0))
        controller.submit_request(req)
    
    print(f"Submitted {controller.stats['total_requests']} requests")
    
    # 4. 执行周期
    completed = 0
    for _ in range(1000):
        resp = controller.tick()
        if resp:
            completed += 1
    
    print(f"Completed {completed} requests")
    
    # 5. 统计
    stats = controller.get_stats()
    print(f"Row hit rate: {stats['scheduler']['row_hit_rate']:.2%}")
    print(f"Refresh count: {stats['refresh']['refresh_count']}")
    
    print("\n=== All Tests Passed ===")


if __name__ == "__main__":
    test_all_modules()
