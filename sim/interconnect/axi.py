"""
AXI/NoC Interconnect Model
支持多 traffic source 的 AXI 互联模型

提供:
1. AXI 协议建模 (AR/AW/W/B channel)
2. NoC 路由逻辑
3. 多 master 多 slave 连接
4. 仲裁和优先级支持

Usage:
    from sim.interconnect.axi import (
        AXIMaster, AXISlave, AXIInterconnect, AXIAddress, AXIBeat
    )
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# AXI Protocol Types
# ============================================================================

class AXIID(Enum):
    """AXI ID 类型"""
    AXI3 = 3
    AXI4 = 4


class AXIBurstType(Enum):
    """突发类型"""
    FIXED = 0b00
    INCR = 0b01
    WRAP = 0b10
    RESERVED = 0b11


class AXIResponseType(Enum):
    """响应类型"""
    OKAY = 0b00
    EXOKAY = 0b01
    SLVERR = 0b10
    DECERR = 0b11


class AXISize(Enum):
    """传输大小"""
    SIZE_1 = 0b000   # 1 byte
    SIZE_2 = 0b001   # 2 bytes
    SIZE_4 = 0b010   # 4 bytes
    SIZE_8 = 0b011   # 8 bytes
    SIZE_16 = 0b100  # 16 bytes
    SIZE_32 = 0b101  # 32 bytes
    SIZE_64 = 0b110  # 64 bytes
    SIZE_128 = 0b111 # 128 bytes


@dataclass
class AXIAddress:
    """AXI 地址"""
    addr: int
    burst: AXIBurstType = AXIBurstType.INCR
    size: AXISize = AXISize.SIZE_64
    length: int = 0          #突发长度 (beats - 1)
    id: int = 0
    user: int = 0

    def get_num_beats(self) -> int:
        """获取传输 beats 数量"""
        return self.length + 1

    def get_total_bytes(self) -> int:
        """获取总字节数"""
        return self.get_num_beats() * (1 << self.size.value)


@dataclass
class AXIBeat:
    """AXI 数据beat"""
    data: int
    strb: int = 0xFF      # byte enable
    last: bool = False
    id: int = 0
    user: int = 0


@dataclass
class AXIResponse:
    """AXI 响应"""
    id: int
    resp: AXIResponseType
    user: int = 0


# ============================================================================
# AXI Channels
# ============================================================================

@dataclass
class AXIARChannel:
    """AXI AR channel (Address Read)"""
    arid: int = 0
    araddr: int = 0
    arlen: int = 0
    arsize: int = 0
    arburst: int = 0
    arlock: int = 0
    arcache: int = 0
    arprot: int = 0
    arqos: int = 0
    arregion: int = 0
    aruser: int = 0
    arvalid: bool = False
    arready: bool = False


@dataclass
class AXIAWChannel:
    """AXI AW channel (Address Write)"""
    awid: int = 0
    awaddr: int = 0
    awlen: int = 0
    awsize: int = 0
    awburst: int = 0
    awlock: int = 0
    awcache: int = 0
    awprot: int = 0
    awqos: int = 0
    awregion: int = 0
    awuser: int = 0
    awvalid: bool = False
    awready: bool = False


@dataclass
class AXIWChannel:
    """AXI W channel (Write Data)"""
    wid: int = 0
    wdata: int = 0
    wstrb: int = 0xFF
    wlast: bool = False
    wuser: int = 0
    wvalid: bool = False
    wready: bool = False


@dataclass
class AXIBChannel:
    """AXI B channel (Write Response)"""
    bid: int = 0
    bresp: int = 0
    buser: int = 0
    bvalid: bool = False
    bready: bool = False


@dataclass
class AXIRChannel:
    """AXI R channel (Read Data)"""
    rid: int = 0
    rdata: int = 0
    rresp: int = 0
    rlast: bool = False
    ruser: int = 0
    rvalid: bool = False
    rready: bool = False


# ============================================================================
# AXI Request/Transaction
# ============================================================================

@dataclass
class AXIReadRequest:
    """AXI 读请求"""
    addr: int
    size: int = 6          # bytes per beat
    length: int = 0        # beats - 1
    id: int = 0
    qos: int = 0           # QoS 优先级
    source: int = 0        # 来源 master ID


@dataclass
class AXIWriteRequest:
    """AXI 写请求"""
    addr: int
    size: int = 6
    length: int = 0
    data: List[int] = field(default_factory=list)
    strb: List[int] = field(default_factory=list)
    id: int = 0
    qos: int = 0
    source: int = 0


@dataclass
class AXITransaction:
    """完整 AXI 事务"""
    is_write: bool
    addr: int
    size: int
    length: int
    data: Optional[List[int]] = None
    id: int = 0
    qos: int = 0
    source: int = 0
    transaction_id: int = 0

    # 状态追踪
    start_cycle: int = 0
    end_cycle: Optional[int] = None
    ar_issued_cycle: Optional[int] = None
    first_data_cycle: Optional[int] = None
    completed_cycle: Optional[int] = None


# ============================================================================
# AXI Master Interface
# ============================================================================

class AXIMaster:
    """AXI Master 端口模型

    产生 AR/AW 请求，接收 R/B 响应
    """

    def __init__(
        self,
        master_id: int,
        name: str = None,
        max_pending_reads: int = 4,
        max_pending_writes: int = 4,
    ):
        self.master_id = master_id
        self.name = name or f"master_{master_id}"

        # 待发送请求队列
        self.pending_reads: List[AXIReadRequest] = []
        self.pending_writes: List[AXIWriteRequest] = []

        # 进行中的事务
        self.active_reads: Dict[int, AXITransaction] = {}
        self.active_writes: Dict[int, AXITransaction] = {}

        # 通道状态
        self.ar = AXIARChannel()
        self.aw = AXIAWChannel()
        self.w = AXIWChannel()
        self.b = AXIBChannel()
        self.r = AXIRChannel()

        # 统计
        self.stats = {
            "read_requests": 0,
            "write_requests": 0,
            "read_completed": 0,
            "write_completed": 0,
            "total_latency_reads": 0,
            "total_latency_writes": 0,
        }

        self._transaction_counter = 0

    def submit_read(self, addr: int, size: int = 6, length: int = 0, qos: int = 0) -> int:
        """提交读请求"""
        tid = self._transaction_counter
        self._transaction_counter += 1

        req = AXIReadRequest(
            addr=addr,
            size=size,
            length=length,
            id=tid,
            qos=qos,
            source=self.master_id,
        )
        self.pending_reads.append(req)

        self.stats["read_requests"] += 1
        logger.debug(f"{self.name}: submitted read req {tid} to addr 0x{addr:x}")

        return tid

    def submit_write(
        self,
        addr: int,
        data: List[int],
        size: int = 6,
        length: int = 0,
        qos: int = 0,
    ) -> int:
        """提交写请求"""
        tid = self._transaction_counter
        self._transaction_counter += 1

        req = AXIWriteRequest(
            addr=addr,
            size=size,
            length=length,
            data=data,
            id=tid,
            qos=qos,
            source=self.master_id,
        )
        self.pending_writes.append(req)

        self.stats["write_requests"] += 1
        logger.debug(f"{self.name}: submitted write req {tid} to addr 0x{addr:x}")

        return tid

    def tick(self, cycle: int) -> bool:
        """每个周期调用，返回是否有未完成的请求"""
        # 处理读响应
        if self.r.rvalid and self.r.rready:
            tid = self.r.rid
            if tid in self.active_reads:
                txn = self.active_reads[tid]
                txn.first_data_cycle = cycle

                if self.r.rlast:
                    txn.completed_cycle = cycle
                    self.stats["read_completed"] += 1
                    self.stats["total_latency_reads"] += cycle - txn.start_cycle
                    del self.active_reads[tid]

        # 处理写响应
        if self.b.bvalid and self.b.bready:
            tid = self.b.bid
            if tid in self.active_writes:
                txn = self.active_writes[tid]
                txn.completed_cycle = cycle
                self.stats["write_completed"] += 1
                self.stats["total_latency_writes"] += cycle - txn.start_cycle
                del self.active_writes[tid]

        return bool(self.pending_reads or self.pending_writes or
                    self.active_reads or self.active_writes)

    def get_avg_read_latency(self) -> float:
        """获取平均读延迟"""
        if self.stats["read_completed"] == 0:
            return 0.0
        return self.stats["total_latency_reads"] / self.stats["read_completed"]

    def get_avg_write_latency(self) -> float:
        """获取平均写延迟"""
        if self.stats["write_completed"] == 0:
            return 0.0
        return self.stats["total_latency_writes"] / self.stats["write_completed"]


# ============================================================================
# AXI Slave Interface
# ============================================================================

class AXISlave:
    """AXI Slave 端口模型

    接收 AR/AW 请求，发送 R/B 响应
    """

    def __init__(
        self,
        slave_id: int,
        name: str = None,
        base_addr: int = 0,
        addr_range: int = 0x100000000,
    ):
        self.slave_id = slave_id
        self.name = name or f"slave_{slave_id}"
        self.base_addr = base_addr
        self.addr_range = addr_range

        # 通道状态
        self.ar = AXIARChannel()
        self.aw = AXIAWChannel()
        self.w = AXIWChannel()
        self.b = AXIBChannel()
        self.r = AXIRChannel()

        # 请求追踪
        self.pending_reads: List[Tuple[AXIARChannel, int]] = []  # (ar_channel, cycle)
        self.pending_writes: List[Tuple[AXIAWChannel, int]] = []  # (aw_channel, cycle)

        # 内存模拟
        self.memory: Dict[int, int] = {}

        # 统计
        self.stats = {
            "reads_received": 0,
            "writes_received": 0,
            "read_beats": 0,
            "write_beats": 0,
        }

    def contains_addr(self, addr: int) -> bool:
        """检查地址是否属于此 slave"""
        return self.base_addr <= addr < self.base_addr + self.addr_range

    def read_memory(self, addr: int, size: int = 8) -> int:
        """读取内存"""
        if addr in self.memory:
            return self.memory[addr]
        return 0

    def write_memory(self, addr: int, data: int, strb: int = 0xFF) -> None:
        """写入内存"""
        self.memory[addr] = data

    def tick(self, cycle: int) -> None:
        """每个周期调用"""
        # 处理读地址
        if self.ar.arvalid and not self.ar.arready:
            self.stats["reads_received"] += 1
            self.pending_reads.append((self.ar, cycle))
            self.ar.arready = True

        # 处理写地址
        if self.aw.awvalid and not self.aw.awready:
            self.stats["writes_received"] += 1
            self.pending_writes.append((self.aw, cycle))
            self.aw.awready = True

        # 处理写数据
        if self.w.wvalid and self.w.wready:
            self.stats["write_beats"] += 1
            self.write_memory(self.w.wid, self.w.wdata, self.w.wstrb)
            if self.w.wlast:
                self.w.wready = False

        # 处理读数据
        if self.r.rvalid and self.r.rready:
            self.stats["read_beats"] += 1


# ============================================================================
# AXI Interconnect
# ============================================================================

@dataclass
class NoCRoute:
    """NoC 路由信息"""
    source_master: int
    dest_slave: int
    virtual_channel: int = 0


class AXIInterconnect:
    """AXI 互联矩阵 / NoC 模型

    功能:
    1. 地址解码 (选择目标 slave)
    2. 路由 (master -> slave)
    3. 仲裁 (多 master 竞争)
    4. ID 转换 (避免 ID 冲突)
    5. QoS 调度
    """

    def __init__(
        self,
        num_masters: int = 4,
        num_slaves: int = 4,
        routing_algo: str = "round_robin",
        enable_qos: bool = True,
    ):
        self.num_masters = num_masters
        self.num_slaves = num_slaves
        self.routing_algo = routing_algo
        self.enable_qos = enable_qos

        # Masters 和 Slaves
        self.masters: Dict[int, AXIMaster] = {}
        self.slaves: Dict[int, AXISlave] = {}

        # 地址映射表
        self.addr_map: List[Tuple[int, int, int]] = []  # (base, mask, slave_id)

        # 仲裁器状态
        self.arb_state: Dict[int, int] = defaultdict(int)  # master_id -> last_served_beat

        # 路由表
        self.routes: Dict[Tuple[int, int], NoCRoute] = {}  # (master, slave) -> route

        # ID 转换表
        self.id_map: Dict[int, Dict[int, int]] = defaultdict(dict)  # master_id -> {orig_id -> new_id}

        # 统计
        self.stats = {
            "ar_transactions": 0,
            "aw_transactions": 0,
            "r_beats": 0,
            "w_beats": 0,
            "arbitrations": 0,
        }

        logger.info(f"AXI Interconnect created: {num_masters}x{num_slaves}, "
                    f"routing={routing_algo}, QoS={enable_qos}")

    def add_master(self, master: AXIMaster) -> None:
        """添加 master"""
        self.masters[master.master_id] = master
        self.id_map[master.master_id] = {}

    def add_slave(self, slave: AXISlave) -> None:
        """添加 slave"""
        self.slaves[slave.slave_id] = slave
        # 更新地址映射
        self.addr_map.append((slave.base_addr, slave.addr_range - 1, slave.slave_id))

    def add_address_region(self, base: int, mask: int, slave_id: int) -> None:
        """添加地址映射区域"""
        self.addr_map.append((base, mask, slave_id))

    def decode_address(self, addr: int) -> Optional[int]:
        """地址解码 - 找到目标 slave"""
        for base, mask, slave_id in self.addr_map:
            # Use simple range check: base <= addr < base + mask + 1
            if base <= addr <= base + mask:
                return slave_id
        return None

    def route(self, master_id: int, slave_id: int) -> NoCRoute:
        """路由"""
        key = (master_id, slave_id)
        if key not in self.routes:
            self.routes[key] = NoCRoute(source_master=master_id, dest_slave=slave_id)
        return self.routes[key]

    def arbitrate_read(self) -> Optional[Tuple[int, AXIReadRequest]]:
        """读通道仲裁 - 返回选中的 master 和请求"""
        # 收集所有有效的读请求
        candidates = []
        for master_id, master in self.masters.items():
            if master.pending_reads:
                req = master.pending_reads[0]
                candidates.append((master_id, req, req.qos))

        if not candidates:
            return None

        # QoS 优先级排序
        if self.enable_qos:
            candidates.sort(key=lambda x: -x[2])  # 高 QoS 优先
        else:
            # Round-robin
            candidates.sort(key=lambda x: x[0])

        master_id, req, _ = candidates[0]
        return (master_id, req)

    def arbitrate_write(self) -> Optional[Tuple[int, AXIWriteRequest]]:
        """写通道仲裁"""
        candidates = []
        for master_id, master in self.masters.items():
            if master.pending_writes:
                req = master.pending_writes[0]
                candidates.append((master_id, req, req.qos))

        if not candidates:
            return None

        if self.enable_qos:
            candidates.sort(key=lambda x: -x[2])
        else:
            candidates.sort(key=lambda x: x[0])

        master_id, req, _ = candidates[0]
        return (master_id, req)

    def tick(self, cycle: int) -> None:
        """每个周期调用 - 处理所有通道的传输"""
        # 读地址通道
        ar_result = self.arbitrate_read()
        if ar_result:
            master_id, req = ar_result
            slave_id = self.decode_address(req.addr)

            if slave_id is not None and slave_id in self.slaves:
                self.stats["ar_transactions"] += 1
                self.stats["arbitrations"] += 1

                # 复制到 slave AR channel
                slave = self.slaves[slave_id]
                slave.ar.arvalid = True
                slave.ar.araddr = req.addr
                slave.ar.arsize = req.size
                slave.ar.arlen = req.length
                slave.ar.arid = req.id

                # 从 master 移除请求
                self.masters[master_id].pending_reads.pop(0)

        # 读数据通道 (slave -> master)
        for slave_id, slave in self.slaves.items():
            if slave.r.rvalid:
                # 简化: 直接传递到对应的 master
                for master_id, master in self.masters.items():
                    if not master.r.rvalid:
                        master.r.rid = slave.r.rid
                        master.r.rdata = slave.r.rdata
                        master.r.rresp = slave.r.rresp
                        master.r.rlast = slave.r.rlast
                        master.r.rvalid = True
                        self.stats["r_beats"] += 1
                        break

        # 写地址通道
        aw_result = self.arbitrate_write()
        if aw_result:
            master_id, req = aw_result
            slave_id = self.decode_address(req.addr)

            if slave_id is not None and slave_id in self.slaves:
                self.stats["aw_transactions"] += 1
                self.stats["arbitrations"] += 1

                slave = self.slaves[slave_id]
                slave.aw.awvalid = True
                slave.aw.awaddr = req.addr
                slave.aw.awsize = req.size
                slave.aw.awlen = req.length
                slave.aw.awid = req.id

                self.masters[master_id].pending_writes.pop(0)

        # 写数据通道
        for master_id, master in self.masters.items():
            if master.w.wvalid and master.w.wready:
                self.stats["w_beats"] += 1

        # 更新所有 master/slave
        for master in self.masters.values():
            master.tick(cycle)
        for slave in self.slaves.values():
            slave.tick(cycle)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "interconnect": self.stats.copy(),
            "masters": {
                m.master_id: m.stats.copy() for m in self.masters.values()
            },
            "slaves": {
                s.slave_id: s.stats.copy() for s in self.slaves.values()
            },
        }


# ============================================================================
# Multi-Master HBM Traffic Generator
# ============================================================================

class MultiMasterTrafficGenerator:
    """多 master HBM 流量生成器

    模拟多个 CPU/GPU core 同时访问 HBM 内存
    """

    def __init__(
        self,
        num_masters: int = 4,
        interconnect: AXIInterconnect = None,
    ):
        self.num_masters = num_masters
        self.interconnect = interconnect or AXIInterconnect(num_masters=num_masters, num_slaves=1)

        # 创建 masters
        for i in range(num_masters):
            master = AXIMaster(master_id=i, name=f"core_{i}")
            self.interconnect.add_master(master)

        # 创建 HBM slave
        hbm = AXISlave(slave_id=0, name="hbm", base_addr=0, addr_range=0x100000000)
        self.interconnect.add_slave(hbm)

        # 流量模式
        self.traffic_patterns = ["random", "sequential", "stride", "hot_spot"]
        self.current_pattern = "random"

    def generate_traffic(
        self,
        pattern: str,
        num_requests: int,
        rate: float = 0.5,
        seed: int = None,
    ) -> None:
        """生成流量"""
        import random
        if seed is not None:
            random.seed(seed)

        self.current_pattern = pattern

        for i in range(num_requests):
            master_id = i % self.num_masters
            master = self.interconnect.masters[master_id]

            # 根据模式生成地址
            if pattern == "random":
                addr = random.randint(0, 0xFFFFFFFF) & ~0x3F  # 64B aligned
            elif pattern == "sequential":
                addr = (i * 64) & 0xFFFFFFFF
            elif pattern == "stride":
                addr = (i * 4096) & 0xFFFFFFFF
            elif pattern == "hot_spot":
                addr = random.choice([0x1000, 0x2000, 0x3000] + list(range(0, 0x100000, 0x1000)))
            else:
                addr = random.randint(0, 0xFFFFFFFF) & ~0x3F

            # QoS: 实时流量优先级高
            qos = 4 if i < num_requests * 0.1 else 0

            if random.random() < 0.7:  # 70% reads
                master.submit_read(addr, qos=qos)
            else:
                data = [random.randint(0, 0xFFFFFFFFFFFFFFFF) for _ in range(1)]
                master.submit_write(addr, data, qos=qos)

    def run_simulation(self, cycles: int) -> Dict:
        """运行仿真"""
        for cycle in range(cycles):
            self.interconnect.tick(cycle)

        return self.interconnect.get_stats()


# ============================================================================
# Convenience Functions
# ============================================================================

def create_hbm_interconnect(
    num_masters: int = 4,
    enable_qos: bool = True,
) -> Tuple[AXIInterconnect, List[AXIMaster], AXISlave]:
    """创建 HBM 互联的快捷函数"""
    interconnect = AXIInterconnect(
        num_masters=num_masters,
        num_slaves=1,
        enable_qos=enable_qos,
    )

    # 添加 masters
    masters = []
    for i in range(num_masters):
        master = AXIMaster(master_id=i, name=f"pe_{i}")
        interconnect.add_master(master)
        masters.append(master)

    # 添加 HBM slave
    hbm = AXISlave(slave_id=0, name="hbm", base_addr=0, addr_range=0x100000000)
    interconnect.add_slave(hbm)

    return interconnect, masters, hbm


if __name__ == "__main__":
    # 简单测试
    print("Creating HBM interconnect with 4 masters...")
    interconnect, masters, hbm = create_hbm_interconnect(num_masters=4)

    # 生成一些流量
    gen = MultiMasterTrafficGenerator(num_masters=4, interconnect=interconnect)
    gen.generate_traffic("random", num_requests=100, seed=42)

    print("Running simulation for 1000 cycles...")
    stats = gen.run_simulation(cycles=1000)

    print("\n=== Simulation Results ===")
    print(f"AR transactions: {stats['interconnect']['ar_transactions']}")
    print(f"AW transactions: {stats['interconnect']['aw_transactions']}")
    print(f"R beats: {stats['interconnect']['r_beats']}")
    print(f"W beats: {stats['interconnect']['w_beats']}")