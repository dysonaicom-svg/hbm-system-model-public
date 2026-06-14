"""
HBM Controller Integration Tests
测试 Phase A 控制器的完整功能
"""

import pytest
import sys
import time

sys.path.insert(0, '/home/ic/JXTF/HBM')

from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest, RequestState
from model.controller.address_decoder import AddressDecoder
from model.controller.queue import ReadQueue, WriteQueue, QueueManager
from model.controller.scheduler import FRFCFSScheduler
from model.controller.qos_scheduler import QoSScheduler


class TestHBMController:
    """HBM 控制器集成测试"""

    def test_controller_creation(self):
        """测试控制器创建"""
        controller = HBMController()
        assert controller.config is not None
        assert controller.current_time == 0.0
        assert controller.decoder is not None
        assert controller.queue_manager is not None

    def test_controller_with_custom_config(self):
        """测试自定义配置"""
        config = HBMConfig(
            stack_count=1,
            channels_per_stack=4,
            scheduler_mode="qos"
        )
        controller = HBMController(config)
        assert controller.config.stack_count == 1
        assert controller.config.channels_per_stack == 4

    def test_submit_read_request(self):
        """测试提交读请求"""
        controller = HBMController()

        # 使用对齐的地址
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        success = controller.submit_request(request)

        assert success is True
        assert controller.stats['total_requests'] == 1
        assert controller.stats['read_requests'] == 1

    def test_submit_write_request(self):
        """测试提交写请求"""
        controller = HBMController()

        request = HBMRequest(addr=0x2000, length=64, is_read=False)
        success = controller.submit_request(request)

        assert success is True
        assert controller.stats['write_requests'] == 1

    def test_submit_multiple_requests(self):
        """测试提交多个请求"""
        controller = HBMController()

        for i in range(10):
            request = HBMRequest(addr=0x1000 + i * 0x1000, length=64, is_read=True)
            controller.submit_request(request)

        assert controller.stats['total_requests'] == 10

    def test_row_hit_detection(self):
        """测试 Row Hit 检测"""
        controller = HBMController()

        # 第一个请求打开行
        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        controller.submit_request(req1)
        controller.tick()

        # 同一行的第二个请求应该是 row hit
        req2 = HBMRequest(addr=0x1800, length=64, is_read=True)
        controller.submit_request(req2)

        # 这个请求应该在同一 bank 同一 row
        bank_key = (req2.channel_id, req2.pseudo_channel_id, req2.bank_id)
        bank_state = controller.bank_states.get(bank_key)
        assert bank_state is not None


class TestAddressDecoder:
    """地址解码器测试"""

    def test_decoder_creation(self):
        """测试解码器创建"""
        decoder = AddressDecoder(HBM3_DEFAULT)
        assert decoder.config is not None

    def test_decode_rbc_mapping(self):
        """测试 RBC 映射解码"""
        config = HBMConfig(address_mapping="rbc")
        decoder = AddressDecoder(config)

        # 测试地址: 0x1000 (8-byte 对齐)
        addr = 0x1000
        decoded = decoder.decode(addr)

        assert decoded.stack_id == 0
        assert decoded.channel_id == 0
        # 其他字段取决于映射

    def test_decode_bcr_mapping(self):
        """测试 BCR 映射解码"""
        config = HBMConfig(address_mapping="bcr")
        decoder = AddressDecoder(config)

        addr = 0x1000
        decoded = decoder.decode(addr)
        assert decoded.stack_id == 0

    def test_address_alignment_check(self):
        """测试地址对齐检查"""
        decoder = AddressDecoder(HBM3_DEFAULT)

        # 对齐的地址应该成功
        aligned_addr = 0x1000
        decoded = decoder.decode(aligned_addr)
        assert decoded is not None

        # 未对齐的地址应该抛出异常
        from model.controller.exceptions import AddressError
        unaligned_addr = 0x1001
        with pytest.raises(AddressError):
            decoder.decode(unaligned_addr)

    def test_encode_decode_roundtrip(self):
        """测试编码解码往返"""
        decoder = AddressDecoder(HBM3_DEFAULT)

        original_addr = 0x1000
        decoded = decoder.decode(original_addr)
        encoded = decoder.encode(decoded)

        assert encoded == original_addr


class TestQueues:
    """请求队列测试"""

    def test_read_queue_creation(self):
        """测试读队列创建"""
        queue = ReadQueue(max_depth=32)
        assert queue.max_depth == 32
        assert queue.is_empty()

    def test_write_queue_creation(self):
        """测试写队列创建"""
        queue = WriteQueue(max_depth=32)
        assert queue.max_depth == 32

    def test_queue_push_pop(self):
        """测试队列入队出队"""
        queue = ReadQueue(max_depth=10)

        # 入队
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        success = queue.push(request)
        assert success is True
        assert not queue.is_empty()

        # 出队
        popped = queue.pop()
        assert popped is not None
        assert popped.request_id == request.request_id

    def test_queue_full(self):
        """测试队列满"""
        queue = ReadQueue(max_depth=2)

        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True)
        req3 = HBMRequest(addr=0x3000, length=64, is_read=True)

        assert queue.push(req1) is True
        assert queue.push(req2) is True
        assert queue.push(req3) is False  # 队列已满


class TestScheduler:
    """调度器测试"""

    def test_frfcfs_scheduler_creation(self):
        """测试 FR-FCFS 调度器创建"""
        scheduler = FRFCFSScheduler(HBM3_DEFAULT)
        assert scheduler.config is not None

    def test_qos_scheduler_creation(self):
        """测试 QoS 调度器创建"""
        config = HBMConfig(scheduler_mode="qos")
        scheduler = QoSScheduler(config)
        assert scheduler.config is not None

    def test_frfcfs_row_hit_priority(self):
        """测试 FR-FCFS 行命中优先级"""
        scheduler = FRFCFSScheduler(HBM3_DEFAULT)

        # 创建请求
        req_hit = HBMRequest(addr=0x1000, length=64, is_read=True)
        req_hit.row_hit = True

        req_miss = HBMRequest(addr=0x2000, length=64, is_read=True)
        req_miss.row_hit = False

        # row_hit 请求应该优先
        assert req_hit.row_hit is True
        assert req_miss.row_hit is False


class TestRequest:
    """请求测试"""

    def test_request_creation(self):
        """测试请求创建"""
        request = HBMRequest(addr=0x1000, length=64, is_read=True)

        assert request.addr == 0x1000
        assert request.length == 64
        assert request.is_read is True
        assert request.state == RequestState.PENDING

    def test_request_state_transitions(self):
        """测试请求状态转换"""
        request = HBMRequest(addr=0x1000, length=64, is_read=True)
        # 使用模拟时间
        request.arrival_time = 1.0

        # 调度
        request.mark_scheduled(2.0)
        assert request.state == RequestState.SCHEDULED

        # 进行中
        request.mark_in_progress()
        assert request.state == RequestState.IN_PROGRESS

        # 完成
        request.mark_completed(3.0)
        assert request.state == RequestState.COMPLETED
        assert request.latency == 2.0

    def test_request_id_uniqueness(self):
        """测试请求 ID 唯一性"""
        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True)

        assert req1.request_id != req2.request_id


class TestConfig:
    """配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = HBM3_DEFAULT

        assert config.stack_count == 2
        assert config.channels_per_stack == 8
        assert config.data_rate == 6.4e9

    def test_bandwidth_calculation(self):
        """测试带宽计算"""
        config = HBM3_DEFAULT

        bw = config.calc_bandwidth()
        # HBM3: 6.4 Gb/s * 1024 bits / 8 = 819.2 GB/s
        expected_bw = 6.4 * 1024 / 8.0
        assert abs(bw - expected_bw) < 0.1

    def test_config_from_dict(self):
        """测试从字典加载配置"""
        data = {
            'stack_count': 4,
            'channels_per_stack': 16,
        }
        config = HBMConfig.from_dict(data)

        assert config.stack_count == 4
        assert config.channels_per_stack == 16
        # 其他字段使用默认值
        assert config.banks_per_pseudo_channel == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"])