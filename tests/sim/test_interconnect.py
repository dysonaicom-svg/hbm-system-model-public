"""Tests for AXI/NoC Interconnect Module"""

import pytest
from sim.interconnect.axi import (
    AXIMaster,
    AXISlave,
    AXIInterconnect,
    AXIReadRequest,
    AXIWriteRequest,
    AXIAddress,
    AXIBurstType,
    AXISize,
    MultiMasterTrafficGenerator,
    create_hbm_interconnect,
)


class TestAXIMaster:
    """AXI Master 测试"""

    def test_master_creation(self):
        """测试 master 创建"""
        master = AXIMaster(master_id=0, name="test_master")
        assert master.master_id == 0
        assert master.name == "test_master"
        assert len(master.pending_reads) == 0
        assert len(master.pending_writes) == 0

    def test_submit_read(self):
        """测试提交读请求"""
        master = AXIMaster(master_id=0)
        tid = master.submit_read(addr=0x1000, size=6, length=0)

        assert tid == 0
        assert len(master.pending_reads) == 1
        assert master.stats["read_requests"] == 1

    def test_submit_write(self):
        """测试提交写请求"""
        master = AXIMaster(master_id=0)
        data = [0xDEADBEEF]
        tid = master.submit_write(addr=0x2000, data=data)

        assert tid == 0
        assert len(master.pending_writes) == 1
        assert master.stats["write_requests"] == 1

    def test_multiple_transactions(self):
        """测试多个事务"""
        master = AXIMaster(master_id=0)

        for i in range(10):
            tid = master.submit_read(addr=i * 0x100)
            assert tid == i

        assert len(master.pending_reads) == 10


class TestAXISlave:
    """AXI Slave 测试"""

    def test_slave_creation(self):
        """测试 slave 创建"""
        slave = AXISlave(slave_id=0, name="test_slave", base_addr=0, addr_range=0x1000)
        assert slave.slave_id == 0
        assert slave.base_addr == 0
        assert slave.addr_range == 0x1000

    def test_address_in_range(self):
        """测试地址范围检查"""
        slave = AXISlave(slave_id=0, base_addr=0x1000, addr_range=0x1000)

        assert slave.contains_addr(0x1000)
        assert slave.contains_addr(0x1500)
        assert not slave.contains_addr(0x2000)
        assert not slave.contains_addr(0x500)

    def test_memory_operations(self):
        """测试内存读写"""
        slave = AXISlave(slave_id=0)

        slave.write_memory(0x100, 0xDEADBEEF)
        data = slave.read_memory(0x100)
        assert data == 0xDEADBEEF

        # 未初始化地址返回 0
        assert slave.read_memory(0x999) == 0


class TestAXIInterconnect:
    """AXI Interconnect 测试"""

    def test_interconnect_creation(self):
        """测试互联创建"""
        interconnect = AXIInterconnect(num_masters=4, num_slaves=2)
        assert interconnect.num_masters == 4
        assert interconnect.num_slaves == 2

    def test_add_master(self):
        """测试添加 master"""
        interconnect = AXIInterconnect()
        master = AXIMaster(master_id=0)
        interconnect.add_master(master)

        assert 0 in interconnect.masters

    def test_add_slave(self):
        """测试添加 slave"""
        interconnect = AXIInterconnect()
        slave = AXISlave(slave_id=0, base_addr=0, addr_range=0x1000)
        interconnect.add_slave(slave)

        assert 0 in interconnect.slaves
        assert len(interconnect.addr_map) == 1

    def test_address_decode(self):
        """测试地址解码"""
        interconnect = AXIInterconnect()

        # 添加地址映射
        interconnect.add_address_region(base=0x0000_0000, mask=0x8000_0000, slave_id=0)
        interconnect.add_address_region(base=0x8000_0000, mask=0x8000_0000, slave_id=1)

        assert interconnect.decode_address(0x1000) == 0
        assert interconnect.decode_address(0x9000_0000) == 1
        assert interconnect.decode_address(0x4000_0000) == 0

    def test_arbitrate_read(self):
        """测试读仲裁"""
        interconnect = AXIInterconnect()
        master = AXIMaster(master_id=0)
        interconnect.add_master(master)

        # 提交请求
        master.submit_read(addr=0x1000, qos=5)

        result = interconnect.arbitrate_read()
        assert result is not None
        master_id, req = result
        assert master_id == 0
        assert req.qos == 5

    def test_arbitrate_write(self):
        """测试写仲裁"""
        interconnect = AXIInterconnect()
        master = AXIMaster(master_id=0)
        interconnect.add_master(master)

        master.submit_write(addr=0x2000, data=[0x1234])

        result = interconnect.arbitrate_write()
        assert result is not None

    def test_qos_priority(self):
        """测试 QoS 优先级"""
        interconnect = AXIInterconnect(enable_qos=True)

        master1 = AXIMaster(master_id=0)
        master2 = AXIMaster(master_id=1)
        interconnect.add_master(master1)
        interconnect.add_master(master2)

        # master1 高优先级
        master1.submit_read(addr=0x1000, qos=5)
        # master2 低优先级
        master2.submit_read(addr=0x2000, qos=1)

        result = interconnect.arbitrate_read()
        master_id, _ = result
        assert master_id == 0  # 高优先级 master 应被选中


class TestMultiMasterTrafficGenerator:
    """多 master 流量生成器测试"""

    def test_generator_creation(self):
        """测试生成器创建"""
        gen = MultiMasterTrafficGenerator(num_masters=4)
        assert gen.num_masters == 4
        assert len(gen.interconnect.masters) == 4

    def test_generate_random_traffic(self):
        """测试随机流量生成"""
        gen = MultiMasterTrafficGenerator(num_masters=4)
        gen.generate_traffic("random", num_requests=20, seed=42)

        total_requests = sum(
            len(m.pending_reads) + len(m.pending_writes)
            for m in gen.interconnect.masters.values()
        )
        assert total_requests == 20

    def test_generate_sequential_traffic(self):
        """测试顺序流量生成"""
        gen = MultiMasterTrafficGenerator(num_masters=2)
        gen.generate_traffic("sequential", num_requests=10)

        # 所有请求应该在 slave 地址范围内
        for master in gen.interconnect.masters.values():
            for req in master.pending_reads:
                assert req.addr < 0x10000  # 顺序地址增长

    def test_run_simulation(self):
        """测试仿真运行"""
        gen = MultiMasterTrafficGenerator(num_masters=2)
        gen.generate_traffic("random", num_requests=10, seed=42)

        stats = gen.run_simulation(cycles=100)

        assert "interconnect" in stats
        assert "masters" in stats
        assert stats["interconnect"]["ar_transactions"] >= 0


class TestCreateHBMInterconnect:
    """HBM 互联快捷函数测试"""

    def test_create_hbm_interconnect(self):
        """测试创建 HBM 互联"""
        interconnect, masters, hbm = create_hbm_interconnect(num_masters=4)

        assert len(masters) == 4
        assert hbm.name == "hbm"
        assert hbm.slave_id == 0
        assert interconnect.num_masters == 4
        assert interconnect.num_slaves == 1

    def test_hbm_address_decode(self):
        """测试 HBM 地址解码"""
        interconnect, masters, hbm = create_hbm_interconnect()

        # HBM 覆盖整个地址空间
        assert interconnect.decode_address(0x0) == 0
        assert interconnect.decode_address(0xFFFF_FFFF) == 0


class TestAXIAddress:
    """AXI 地址测试"""

    def test_address_calculation(self):
        """测试地址计算"""
        addr = AXIAddress(
            addr=0x1000,
            burst=AXIBurstType.INCR,
            size=AXISize.SIZE_64,
            length=7,  # 8 beats
        )

        assert addr.get_num_beats() == 8
        assert addr.get_total_bytes() == 64 * 8  # 512 bytes