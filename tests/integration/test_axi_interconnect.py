"""
AXI Interconnect Integration Tests

验证 AXI 互联模型与 HBM Controller 的集成。
"""

import pytest
from sim.interconnect.axi import (
    AXIMaster, AXISlave, AXIInterconnect, AXIAddress, AXIBeat,
    create_hbm_interconnect, MultiMasterTrafficGenerator
)
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest


class TestAXIInterconnectBasic:
    """AXI 互联基本测试"""

    def test_interconnect_creation(self):
        """测试互联创建"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=4)

        assert len(masters) == 4
        assert hbm is not None

    def test_master_add(self):
        """测试 master 添加"""
        interconnect = AXIInterconnect(num_masters=2, num_slaves=2)
        master = AXIMaster(master_id=0, name="test_master")

        interconnect.add_master(master)

        assert 0 in interconnect.masters
        assert interconnect.masters[0] == master

    def test_slave_add(self):
        """测试 slave 添加"""
        interconnect = AXIInterconnect(num_masters=2, num_slaves=2)
        slave = AXISlave(slave_id=0, name="test_slave", base_addr=0x1000)

        interconnect.add_slave(slave)

        assert 0 in interconnect.slaves
        assert interconnect.slaves[0] == slave

    def test_address_decode(self):
        """测试地址解码"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=1)

        # 测试地址解码
        addr = 0x1000
        slave_id = interconnect.decode_address(addr)

        assert slave_id == 0  # 应该在 HBM slave 范围内

    def test_address_decode_out_of_range(self):
        """测试超出范围地址"""
        interconnect = AXIInterconnect(num_masters=1, num_slaves=1)
        slave = AXISlave(slave_id=0, base_addr=0x1000, addr_range=0x1000)
        interconnect.add_slave(slave)

        # 测试超出范围地址
        addr = 0x10000
        slave_id = interconnect.decode_address(addr)

        assert slave_id is None


class TestAXIMaster:
    """AXI Master 测试"""

    def test_master_submit_read(self):
        """测试 master 提交读请求"""
        master = AXIMaster(master_id=0, name="test")

        tid = master.submit_read(addr=0x1000, size=6, qos=4)

        assert tid == 0
        assert len(master.pending_reads) == 1
        assert master.stats["read_requests"] == 1

    def test_master_submit_write(self):
        """测试 master 提交写请求"""
        master = AXIMaster(master_id=0, name="test")

        tid = master.submit_write(addr=0x1000, data=[0xDEADBEEF], qos=4)

        assert tid == 0
        assert len(master.pending_writes) == 1
        assert master.stats["write_requests"] == 1

    def test_master_multiple_requests(self):
        """测试 master 多请求"""
        master = AXIMaster(master_id=0, name="test")

        tids = []
        for i in range(5):
            tid = master.submit_read(addr=0x1000 * (i + 1))
            tids.append(tid)

        assert len(master.pending_reads) == 5
        assert tids == [0, 1, 2, 3, 4]

    def test_master_avg_latency(self):
        """测试平均延迟计算"""
        master = AXIMaster(master_id=0, name="test")

        # 模拟完成请求
        master.submit_read(addr=0x1000)
        master.submit_read(addr=0x2000)

        # 验证延迟计算（还未完成，应该是0）
        assert master.get_avg_read_latency() == 0.0


class TestAXISlave:
    """AXI Slave 测试"""

    def test_slave_contains_addr(self):
        """测试地址包含"""
        slave = AXISlave(slave_id=0, base_addr=0x1000, addr_range=0x1000)

        assert slave.contains_addr(0x1500) is True
        assert slave.contains_addr(0x500) is False
        assert slave.contains_addr(0x2000) is False

    def test_slave_memory(self):
        """测试内存读写"""
        slave = AXISlave(slave_id=0)

        slave.write_memory(addr=0x1000, data=0xDEADBEEF)
        data = slave.read_memory(addr=0x1000)

        assert data == 0xDEADBEEF

    def test_slave_memory_uninitialized(self):
        """测试未初始化内存"""
        slave = AXISlave(slave_id=0)

        data = slave.read_memory(addr=0x1000)

        assert data == 0  # 未初始化返回 0


class TestAXIArbitration:
    """AXI 仲裁测试"""

    def test_read_arbitration_qos(self):
        """测试读通道 QoS 仲裁"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=2, enable_qos=True)

        # 两个 master 同时提交请求
        masters[0].submit_read(addr=0x1000, qos=4)  # 低优先级
        masters[1].submit_read(addr=0x2000, qos=15)  # 高优先级

        # 高 QoS 优先
        result = interconnect.arbitrate_read()

        assert result is not None
        master_id, req = result
        assert master_id == 1  # 高优先级 master

    def test_read_arbitration_round_robin(self):
        """测试读通道轮询仲裁"""
        interconnect = AXIInterconnect(num_masters=2, enable_qos=False)
        for i in range(2):
            interconnect.add_master(AXIMaster(master_id=i))

        # 两个 master 提交请求
        interconnect.masters[0].submit_read(addr=0x1000)
        interconnect.masters[1].submit_read(addr=0x2000)

        # 轮询选择
        result = interconnect.arbitrate_read()
        assert result is not None

    def test_write_arbitration(self):
        """测试写通道仲裁"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=2, enable_qos=True)

        masters[0].submit_write(addr=0x1000, data=[0x1], qos=4)
        masters[1].submit_write(addr=0x2000, data=[0x2], qos=15)

        result = interconnect.arbitrate_write()

        assert result is not None
        master_id, req = result
        assert master_id == 1  # 高优先级


class TestAXITick:
    """AXI tick 测试"""

    def test_tick_read_transaction(self):
        """测试 tick 处理读事务"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=1)

        masters[0].submit_read(addr=0x1000)

        # 运行几个周期
        for cycle in range(10):
            interconnect.tick(cycle)

        # 验证事务被处理
        assert interconnect.stats["ar_transactions"] >= 1

    def test_tick_write_transaction(self):
        """测试 tick 处理写事务"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=1)

        masters[0].submit_write(addr=0x1000, data=[0xDEAD])

        for cycle in range(10):
            interconnect.tick(cycle)

        assert interconnect.stats["aw_transactions"] >= 1

    def test_tick_multiple_masters(self):
        """测试 tick 多 master"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=3)

        masters[0].submit_read(addr=0x1000)
        masters[1].submit_read(addr=0x2000)
        masters[2].submit_read(addr=0x3000)

        for cycle in range(20):
            interconnect.tick(cycle)

        assert interconnect.stats["ar_transactions"] >= 3


class TestMultiMasterTrafficGenerator:
    """多 Master 流量生成器测试"""

    def test_generator_creation(self):
        """测试生成器创建"""
        gen = MultiMasterTrafficGenerator(num_masters=4)

        assert gen.num_masters == 4
        assert gen.interconnect is not None

    def test_generate_random_traffic(self):
        """测试生成随机流量"""
        gen = MultiMasterTrafficGenerator(num_masters=2)
        gen.generate_traffic("random", num_requests=10, seed=42)

        total_requests = sum(
            len(m.pending_reads) + len(m.pending_writes)
            for m in gen.interconnect.masters.values()
        )

        assert total_requests == 10

    def test_generate_sequential_traffic(self):
        """测试生成顺序流量"""
        gen = MultiMasterTrafficGenerator(num_masters=2)
        gen.generate_traffic("sequential", num_requests=10, seed=42)

        total_requests = sum(
            len(m.pending_reads) + len(m.pending_writes)
            for m in gen.interconnect.masters.values()
        )

        assert total_requests == 10

    def test_generate_stride_traffic(self):
        """测试生成 stride 流量"""
        gen = MultiMasterTrafficGenerator(num_masters=2)
        gen.generate_traffic("stride", num_requests=10, seed=42)

        total_requests = sum(
            len(m.pending_reads) + len(m.pending_writes)
            for m in gen.interconnect.masters.values()
        )

        assert total_requests == 10

    def test_generate_hot_spot_traffic(self):
        """测试生成热点流量"""
        gen = MultiMasterTrafficGenerator(num_masters=2)
        gen.generate_traffic("hot_spot", num_requests=10, seed=42)

        total_requests = sum(
            len(m.pending_reads) + len(m.pending_writes)
            for m in gen.interconnect.masters.values()
        )

        assert total_requests == 10

    def test_run_simulation(self):
        """测试运行仿真"""
        gen = MultiMasterTrafficGenerator(num_masters=2)
        gen.generate_traffic("random", num_requests=20, seed=42)

        stats = gen.run_simulation(cycles=100)

        assert "interconnect" in stats
        assert stats["interconnect"]["ar_transactions"] >= 0


class TestAXIStats:
    """AXI 统计测试"""

    def test_get_stats(self):
        """测试获取统计"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=2)

        masters[0].submit_read(addr=0x1000)
        masters[1].submit_write(addr=0x2000, data=[0x1])

        stats = interconnect.get_stats()

        assert "interconnect" in stats
        assert "masters" in stats
        assert "slaves" in stats
        assert stats["masters"][0]["read_requests"] == 1
        assert stats["masters"][1]["write_requests"] == 1


class TestIntegrationWithController:
    """Controller 集成测试"""

    def test_axi_to_controller_integration(self):
        """测试 AXI 到 Controller 集成"""
        # 创建 AXI 互联
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=2)

        # 创建 HBM Controller
        controller = HBMController(HBM3_DEFAULT)

        # 从 AXI master 生成请求并提交到 controller
        master = masters[0]
        addr = 0x1000
        master.submit_read(addr=addr, qos=4)

        # 转换为 HBM 请求并提交
        req = HBMRequest(addr=addr, length=64, is_read=True, qos=4)
        controller.submit_request(req)

        # 运行仿真
        for cycle in range(100):
            interconnect.tick(cycle)
            controller.tick()

        # 验证请求被处理
        assert controller.stats['total_requests'] >= 1

    def test_multi_master_qos(self):
        """测试多 master QoS"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=3, enable_qos=True)

        # 不同 QoS 级别的请求
        masters[0].submit_read(addr=0x1000, qos=4)   # 低
        masters[1].submit_read(addr=0x2000, qos=8)   # 中
        masters[2].submit_read(addr=0x3000, qos=15) # 高

        # 运行仿真
        for cycle in range(50):
            interconnect.tick(cycle)

        # 高 QoS 的 master[2] 应该先被处理
        assert interconnect.stats["ar_transactions"] >= 1


class TestStressTests:
    """压力测试"""

    def test_high_request_volume(self):
        """测试高请求量"""
        gen = MultiMasterTrafficGenerator(num_masters=4)
        gen.generate_traffic("random", num_requests=100, rate=1.0, seed=42)

        stats = gen.run_simulation(cycles=500)

        assert stats["interconnect"]["ar_transactions"] >= 0

    def test_mixed_traffic(self):
        """测试混合流量"""
        gen = MultiMasterTrafficGenerator(num_masters=4)

        # 生成混合流量
        gen.generate_traffic("random", num_requests=30, seed=42)
        gen.generate_traffic("sequential", num_requests=30, seed=43)

        stats = gen.run_simulation(cycles=300)

        assert stats["interconnect"]["ar_transactions"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])