"""
gem5 Type Definitions
HBM 与 gem5 仿真器之间的请求/响应类型定义

提供:
1. gem5 特定的内存请求类型
2. gem5 响应类型
3. gem5 地址映射类型
4. gem5 内存事务类型
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# gem5 Request Types
# ============================================================================

class Gem5RequestType(Enum):
    """gem5 请求类型"""
    READ = "Read"
    WRITE = "Write"
    READ_EXCLUSIVE = "ReadEx"
    READ_SHARED = "ReadShared"
    WRITE_INVALIDATE = "WriteInvalidate"
    ATOMIC_LOAD = "AtomicLoad"
    ATOMIC_STORE = "AtomicStore"
    ATOMIC_SWAP = "AtomicSwap"
    ATOMIC_COMPARE_SWAP = "AtomicCompareSwap"


class Gem5ResponseStatus(Enum):
    """gem5 响应状态"""
    OK = 0
    BAD_ADDRESS = 1
    SEGMENTATION_FAULT = 2
    ALIGNMENT_ERROR = 3
    PARTIAL_RESPONSE = 4
    BUS_ERROR = 5
    TIMEOUT = 6


class Gem5CommandType(Enum):
    """gem5 命令类型"""
    CMD_READ = "Read"
    CMD_WRITE = "Write"
    CMD_BURST_READ = "BurstRead"
    CMD_BURST_WRITE = "BurstWrite"


# ============================================================================
# Address Types
# ============================================================================

@dataclass
class Gem5Address:
    """gem5 地址类型"""
    addr: int
    pc: int = 0                    # Program counter (for prefetch hints)
    size: int = 64                # Request size in bytes
    issecure: bool = False        # Security bit
    color: int = 0                # Cache color (for partitioning)

    def __post_init__(self):
        """验证地址对齐"""
        if self.size > 0 and self.addr % self.size != 0:
            logger.warning(
                f"Address 0x{self.addr:x} not aligned to size {self.size}"
            )


@dataclass
class Gem5AddressRange:
    """gem5 地址范围"""
    start: int
    end: int
    interleaved: bool = False
    granularity: int = 0          # Interleaving granularity

    def contains(self, addr: int) -> bool:
        """检查地址是否在范围内"""
        return self.start <= addr < self.end

    def __post_init__(self):
        """验证范围有效性"""
        if self.start > self.end:
            raise ValueError(
                f"Invalid address range: start={self.start:#x} > end={self.end:#x}"
            )


# ============================================================================
# Request/Response Types
# ============================================================================

@dataclass
class Gem5Request:
    """gem5 内存请求

    对应 gem5 的 Packet::makeAtomicRead/makeWrite 等
    """
    req_id: int                   # Unique request identifier
    addr: Gem5Address             # Target address
    cmd: Gem5CommandType         # Command type
    size: int = 64                # Request size in bytes
    blk_size: int = 64            # Cache block size

    # Timing information
    issue_cycle: int = 0          # Cycle when request was issued
    send_cycle: int = 0           # Cycle when sent to interconnect

    # Source information
    master_id: int = 0            # Source master ID
    thread_id: int = 0            # Thread ID

    # QoS
    qos: int = 0                  # Quality of Service level (0-15)
    qos_priority: int = 0         # Priority within QoS level

    # Flags
    is_fetch: bool = False       # Instruction fetch
    is_prefetch: bool = False     # Prefetch request
    is_writeback: bool = False    # Writeback request

    # For burst transactions
    num_beats: int = 1            # Number of beats for burst
    cur_beat: int = 0             # Current beat number

    # Additional metadata
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Gem5Response:
    """gem5 内存响应

    对应 gem5 的 Packet 响应
    """
    req_id: int                   # Matching request ID
    addr: int                     # Address (64-bit physical)
    status: Gem5ResponseStatus   # Response status
    cmd: Gem5CommandType         # Command type

    # Data (for reads)
    data: Optional[List[int]] = None  # Response data beats

    # Timing
    issue_cycle: int = 0          # When request was issued
    complete_cycle: int = 0       # When response was received

    # Response metadata
    error_code: int = 0           # Error code if any
    flags: int = 0                # Response flags

    @property
    def latency(self) -> int:
        """计算请求延迟（周期数）"""
        return self.complete_cycle - self.issue_cycle


# ============================================================================
# Transaction Types
# ============================================================================

@dataclass
class Gem5Transaction:
    """完整的 gem5 内存事务

    跟踪从请求到响应的完整生命周期
    """
    txn_id: int                   # Unique transaction ID
    request: Gem5Request          # Original request
    response: Optional[Gem5Response] = None

    # State tracking
    state: str = "pending"        # pending, issued, waiting, completed, failed
    retry_count: int = 0
    max_retries: int = 3

    # Timing
    created_cycle: int = 0
    issued_cycle: Optional[int] = None
    completed_cycle: Optional[int] = None

    # Error handling
    error: Optional[str] = None

    def mark_issued(self, cycle: int) -> None:
        """标记事务已发出"""
        self.state = "issued"
        self.issued_cycle = cycle

    def mark_completed(self, response: Gem5Response) -> None:
        """标记事务已完成"""
        self.state = "completed"
        self.response = response
        self.completed_cycle = response.complete_cycle

    def mark_failed(self, error: str) -> None:
        """标记事务失败"""
        self.state = "failed"
        self.error = error

    @property
    def latency(self) -> Optional[int]:
        """获取事务延迟"""
        if self.completed_cycle is None:
            return None
        return self.completed_cycle - self.created_cycle


@dataclass
class Gem5BurstTransaction:
    """Burst 传输事务

    处理突发传输的多个 beats
    """
    txn_id: int
    base_addr: int
    cmd: Gem5CommandType
    num_beats: int
    beat_size: int = 64           # Bytes per beat

    # Tracking
    beats_sent: int = 0
    beats_received: int = 0
    data_buffer: List[int] = field(default_factory=list)

    # Timing
    start_cycle: int = 0
    end_cycle: Optional[int] = None

    def total_bytes(self) -> int:
        """总字节数"""
        return self.num_beats * self.beat_size


# ============================================================================
# Port/Interface Types
# ============================================================================

@dataclass
class Gem5MasterPort:
    """gem5 Master 端口

    对应 gem5 的 MasterPort/RequestPort
    """
    name: str
    peer: Optional["Gem5SlavePort"] = None

    # Statistics
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0

    # Latency tracking
    avg_latency: float = 0.0
    total_latency: int = 0

    def connect(self, slave: "Gem5SlavePort") -> None:
        """连接到 slave 端口"""
        self.peer = slave
        slave.peer = self

    def send(self, pkt: Gem5Request) -> bool:
        """发送请求"""
        if self.peer is None:
            logger.error(f"Port {self.name} not connected")
            return False

        self.packets_sent += 1
        self.bytes_sent += pkt.size
        return True

    def recv(self, resp: Gem5Response) -> None:
        """接收响应"""
        self.packets_received += 1
        self.bytes_received += resp.data[0] if resp.data else 0
        if resp.latency > 0:
            self.total_latency += resp.latency
            self.avg_latency = self.total_latency / max(1, self.packets_received)


@dataclass
class Gem5SlavePort:
    """gem5 Slave 端口

    对应 gem5 的 SlavePort/ResponsePort
    """
    name: str
    peer: Optional[Gem5MasterPort] = None

    # Address range this port responds to
    addr_range: Optional[Gem5AddressRange] = None

    # Statistics
    packets_received: int = 0
    packets_sent: int = 0

    def connect(self, master: Gem5MasterPort) -> None:
        """连接到 master 端口"""
        self.peer = master
        master.peer = self


# ============================================================================
# Timing and Statistics Types
# ============================================================================

@dataclass
class Gem5TimingStats:
    """gem5 统计信息"""
    total_requests: int = 0
    total_responses: int = 0
    total_reads: int = 0
    total_writes: int = 0
    total_latency: int = 0
    total_bw: int = 0             # Total bandwidth in bytes

    # Per-QoS statistics
    qos_stats: Dict[int, Dict[str, int]] = field(default_factory=dict)

    @property
    def avg_latency(self) -> float:
        """平均延迟"""
        if self.total_responses == 0:
            return 0.0
        return self.total_latency / self.total_responses

    @property
    def read_ratio(self) -> float:
        """读请求比例"""
        total = self.total_reads + self.total_writes
        if total == 0:
            return 0.0
        return self.total_reads / total


@dataclass
class Gem5CycleStats:
    """gem5 周期级统计"""
    cycles: int = 0
    active_cycles: int = 0
    stall_cycles: int = 0

    # Utilization
    @property
    def utilization(self) -> float:
        if self.cycles == 0:
            return 0.0
        return self.active_cycles / self.cycles


# ============================================================================
# Memory System Types
# ============================================================================

@dataclass
class Gem5MemoryRange:
    """gem5 内存范围配置"""
    range: Gem5AddressRange
    port: str                     # Port name
    memory_type: str = "DRAM"     # DRAM, HBM, SRAM, etc.

    # HBM-specific
    channels: int = 1
    channel_width: int = 128      # bits
    data_rate: int = 2            # DQ per DQS


@dataclass
class Gem5SystemConfig:
    """gem5 系统配置"""
    cache_line_size: int = 64
    mem_ctrls: List[Gem5MemoryRange] = field(default_factory=list)

    # Clock
    cpu_clock: str = "2GHz"
    mem_clock: str = "1GHz"
    clock_ratio: str = "2:1"

    # System parameters
    num_cpus: int = 4
    num_dirs: int = 1
    num_l2caches: int = 1

    # Workload
    benchmark: str = "memory_test"

    def get_memory_size(self) -> int:
        """获取总内存大小"""
        return sum(
            r.range.end - r.range.start
            for r in self.mem_ctrls
        )


# ============================================================================
# Factory Functions
# ============================================================================

def create_read_request(
    addr: int,
    size: int = 64,
    req_id: int = 0,
    qos: int = 0,
    master_id: int = 0,
) -> Gem5Request:
    """创建读请求的快捷函数"""
    return Gem5Request(
        req_id=req_id,
        addr=Gem5Address(addr=addr, size=size),
        cmd=Gem5CommandType.CMD_READ,
        size=size,
        master_id=master_id,
        qos=qos,
    )


def create_write_request(
    addr: int,
    data: List[int],
    size: int = 64,
    req_id: int = 0,
    qos: int = 0,
    master_id: int = 0,
) -> Gem5Request:
    """创建写请求的快捷函数"""
    return Gem5Request(
        req_id=req_id,
        addr=Gem5Address(addr=addr, size=size),
        cmd=Gem5CommandType.CMD_WRITE,
        size=size,
        master_id=master_id,
        qos=qos,
        extra_data={"write_data": data},
    )


def create_burst_read_request(
    addr: int,
    num_beats: int,
    beat_size: int = 64,
    req_id: int = 0,
    qos: int = 0,
) -> Gem5Request:
    """创建突发读请求的快捷函数"""
    return Gem5Request(
        req_id=req_id,
        addr=Gem5Address(addr=addr, size=beat_size),
        cmd=Gem5CommandType.CMD_BURST_READ,
        size=beat_size * num_beats,
        num_beats=num_beats,
        master_id=0,
        qos=qos,
    )


# ============================================================================
# __init__.py exports
# ============================================================================

__all__ = [
    # Enums
    "Gem5RequestType",
    "Gem5ResponseStatus",
    "Gem5CommandType",

    # Address types
    "Gem5Address",
    "Gem5AddressRange",

    # Request/Response
    "Gem5Request",
    "Gem5Response",

    # Transaction types
    "Gem5Transaction",
    "Gem5BurstTransaction",

    # Port types
    "Gem5MasterPort",
    "Gem5SlavePort",

    # Stats types
    "Gem5TimingStats",
    "Gem5CycleStats",

    # Memory system types
    "Gem5MemoryRange",
    "Gem5SystemConfig",

    # Factory functions
    "create_read_request",
    "create_write_request",
    "create_burst_read_request",
]