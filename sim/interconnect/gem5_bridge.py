"""
gem5 Bridge Implementation
HBM 与 gem5 仿真器的桥接模块

提供:
1. Gem5Bridge 类 - 核心桥接逻辑
2. 连接管理 - 与 gem5 Python API 的连接
3. 请求/响应处理
4. 同步机制
5. 内存端口接口
6. Traffic Generator 接口
7. 缓存行处理 (64/128 bytes)
8. Burst 事务支持

Usage:
    from sim.interconnect.gem5_bridge import Gem5Bridge

    # 创建桥接
    bridge = Gem5Bridge(gem5_home="/path/to/gem5")

    # 连接
    bridge.connect_to_gem5(system=gem5_system)

    # 发送请求
    bridge.send_request(addr=0x1000, size=64, is_write=False)

    # 接收响应
    response = bridge.recv_response(timeout_cycles=1000)

    # 同步
    bridge.sync(cycle=100)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Type, Tuple
from enum import Enum
from collections import defaultdict, deque
import logging
import time
import random

# gem5 types
from sim.interconnect.gem5_types import (
    Gem5Request,
    Gem5Response,
    Gem5Transaction,
    Gem5CommandType,
    Gem5ResponseStatus,
    Gem5MasterPort,
    Gem5SlavePort,
    Gem5Address,
    Gem5TimingStats,
    Gem5CycleStats,
    create_read_request,
    create_write_request,
)

# HBM4 types
from model.dram.hbm4_spec import HBM4Spec

logger = logging.getLogger(__name__)

# ============================================================================
# gem5 API Compatibility Layer
# ============================================================================

class Gem5APIState(Enum):
    """gem5 API 状态"""
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    ERROR = 3


class Gem5MockPort:
    """Mock gem5 Port for testing without actual gem5"""

    def __init__(self, name: str, port_type: str = "master"):
        self.name = name
        self.port_type = port_type
        self.connected = False
        self.packets_sent = 0
        self.packets_recv = 0

    def send(self, pkt: Any) -> bool:
        """发送数据包"""
        if not self.connected:
            return False
        self.packets_sent += 1
        return True

    def recv(self) -> Optional[Any]:
        """接收数据包"""
        if not self.connected:
            return None
        return None


class Gem5MockSystem:
    """Mock gem5 System for testing"""

    def __init__(self):
        self.clock = 0
        self.master_ports: Dict[str, Gem5MockPort] = {}
        self.slave_ports: Dict[str, Gem5MockPort] = {}
        self._latency_map: Dict[str, int] = {}
        self._memory: Dict[int, int] = {}  # Simple memory model

    def register_master_port(self, name: str, port: Gem5MockPort) -> None:
        """注册 master 端口"""
        self.master_ports[name] = port
        port.connected = True

    def register_slave_port(self, name: str, port: Gem5MockPort) -> None:
        """注册 slave 端口"""
        self.slave_ports[name] = port
        port.connected = True

    def set_latency(self, port_name: str, latency_cycles: int) -> None:
        """设置延迟"""
        self._latency_map[port_name] = latency_cycles

    def get_latency(self, port_name: str) -> int:
        """获取端口延迟"""
        return self._latency_map.get(port_name, 10)

    def tick(self, cycles: int = 1) -> None:
        """推进仿真周期"""
        self.clock += cycles

    def read_memory(self, addr: int, size: int) -> List[int]:
        """模拟内存读取"""
        data = []
        for i in range(size // 8):  # 8 bytes per word
            data.append(self._memory.get(addr + i * 8, 0))
        return data

    def write_memory(self, addr: int, data: List[int]) -> None:
        """模拟内存写入"""
        for i, word in enumerate(data):
            self._memory[addr + i * 8] = word


# ============================================================================
# Cache Line Configuration
# ============================================================================

class CacheLineSize(Enum):
    """缓存行大小枚举"""
    SIZE_64 = 64
    SIZE_128 = 128
    SIZE_256 = 256


@dataclass
class CacheLineConfig:
    """缓存行配置"""
    line_size: int = 64                    # 缓存行大小 (bytes)
    burst_beats: int = 4                  # 每个缓存行的 beats 数
    beat_size: int = 16                   # 每个 beat 的大小 (bytes, 128-bit = 16 bytes)

    def __post_init__(self):
        """验证配置一致性"""
        expected_beats = self.line_size // self.beat_size
        if expected_beats != self.burst_beats:
            logger.warning(
                f"Burst beats mismatch: calculated {expected_beats}, "
                f"got {self.burst_beats}"
            )
            self.burst_beats = expected_beats

    @property
    def addr_mask(self) -> int:
        """地址掩码 (用于缓存行对齐)"""
        return self.line_size - 1


@dataclass
class CacheLineHandler:
    """缓存行处理器

    处理缓存行对齐、分块和组装
    支持 64-byte 和 128-byte 缓存行
    """

    def __init__(self, line_size: int = 64):
        self.line_size = line_size
        self.config = CacheLineConfig(line_size=line_size)

        # 地址统计
        self._cache_hits = 0
        self._cache_misses = 0
        self._burst_requests = 0
        self._split_requests = 0

    def align_address(self, addr: int) -> int:
        """对齐地址到缓存行边界"""
        return addr & ~(self.config.addr_mask)

    def is_aligned(self, addr: int, size: int) -> bool:
        """检查请求是否缓存行对齐"""
        return (addr & self.config.addr_mask) == 0 and size == self.line_size

    def split_request(
        self,
        addr: int,
        size: int,
    ) -> List[Tuple[int, int]]:
        """将请求分割成缓存行对齐的块

        Args:
            addr: 起始地址
            size: 请求大小 (bytes)

        Returns:
            [(aligned_addr, aligned_size), ...] 列表
        """
        chunks = []
        current_addr = addr
        remaining_size = size

        # 对齐起始地址
        if current_addr & self.config.addr_mask:
            aligned_addr = self.align_address(current_addr)
            aligned_size = min(
                self.line_size - (current_addr - aligned_addr),
                remaining_size
            )
            chunks.append((aligned_addr, aligned_size))
            current_addr += aligned_size
            remaining_size -= aligned_size
            self._split_requests += 1

        # 处理中间完整缓存行
        while remaining_size >= self.line_size:
            chunks.append((current_addr, self.line_size))
            current_addr += self.line_size
            remaining_size -= self.line_size

        # 处理尾部
        if remaining_size > 0:
            chunks.append((current_addr, remaining_size))
            self._split_requests += 1

        return chunks

    def calculate_beats(self, size: int) -> int:
        """计算给定大小的 beats 数量"""
        return (size + self.config.beat_size - 1) // self.config.beat_size

    def calculate_burst_cycles(self, size: int) -> int:
        """计算突发传输所需周期数"""
        beats = self.calculate_beats(size)
        return (beats + 3) // 4

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存行处理统计"""
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'burst_requests': self._burst_requests,
            'split_requests': self._split_requests,
            'hit_rate': (
                self._cache_hits / max(1, self._cache_hits + self._cache_misses)
            ),
        }

    def record_hit(self) -> None:
        """记录缓存命中"""
        self._cache_hits += 1

    def record_miss(self) -> None:
        """记录缓存未命中"""
        self._cache_misses += 1


# ============================================================================
# Traffic Generator Interface
# ============================================================================

class TrafficGeneratorInterface:
    """Traffic Generator 接口

    为 CPU/NPU/GPU 提供标准化的流量生成接口
    支持:
    - 顺序访问模式
    - 随机访问模式
    - 热点访问模式
    - stride 访问模式
    """

    class AccessPattern(Enum):
        """访问模式"""
        SEQUENTIAL = "sequential"
        RANDOM = "random"
        HOTSPOT = "hotspot"
        STRIDE = "stride"

    def __init__(
        self,
        name: str,
        bridge: "Gem5Bridge",
        spec: Optional[HBM4Spec] = None,
    ):
        self.name = name
        self.bridge = bridge
        self.spec = spec or HBM4Spec()

        # 模式配置
        self.pattern = self.AccessPattern.SEQUENTIAL
        self.base_addr = 0x1000_0000
        self.access_size = 64
        self.qos = 8

        # 热点配置
        self.hotspot_base = 0x1000_0000
        self.hotspot_size = 0x1000_0000  # 256 MB hotspot
        self.hotspot_ratio = 0.8  # 80% access hotspot

        # Stride 配置
        self.stride = 64

        # 统计
        self._requests_sent = 0
        self._responses_received = 0
        self._total_latency = 0

        # 内部状态
        self._addr = self.base_addr
        self._random = random.Random(42)  # 可重现的随机

    def generate_request(self) -> Optional[int]:
        """生成下一个请求

        Returns:
            请求 ID
        """
        # 根据模式生成地址
        addr = self._generate_address()

        # 发送到桥接
        req_id = self.bridge.send_request(
            addr=addr,
            size=self.access_size,
            is_write=False,
            qos=self.qos,
        )

        if req_id is not None:
            self._requests_sent += 1

        return req_id

    def _generate_address(self) -> int:
        """根据当前模式生成地址"""
        if self.pattern == self.AccessPattern.SEQUENTIAL:
            addr = self._addr
            self._addr += self.access_size
            # 环绕
            if self._addr >= self.base_addr + 0x1_0000_0000:
                self._addr = self.base_addr

        elif self.pattern == self.AccessPattern.RANDOM:
            addr = self.base_addr + (
                self._random.randint(0, 0xFFFF_FFFF) & ~63
            )

        elif self.pattern == self.AccessPattern.HOTSPOT:
            if self._random.random() < self.hotspot_ratio:
                addr = self.hotspot_base + (
                    self._random.randint(0, self.hotspot_size) & ~63
                )
            else:
                addr = self.base_addr + (
                    self._random.randint(0, 0xFFFF_FFFF) & ~63
                )

        elif self.pattern == self.AccessPattern.STRIDE:
            addr = self._addr
            self._addr += self.stride
            # 环绕
            if self._addr >= self.base_addr + 0x1_0000_0000:
                self._addr = self.base_addr

        else:
            addr = self._addr

        return addr

    def generate_burst(self, num_requests: int) -> List[int]:
        """生成突发请求序列

        Args:
            num_requests: 请求数量

        Returns:
            请求 ID 列表
        """
        req_ids = []
        for _ in range(num_requests):
            req_id = self.generate_request()
            if req_id is not None:
                req_ids.append(req_id)
        return req_ids

    def record_response(self, latency: int) -> None:
        """记录响应到达"""
        self._responses_received += 1
        self._total_latency += latency

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_latency = (
            self._total_latency / self._responses_received
            if self._responses_received > 0 else 0
        )
        return {
            'pattern': self.pattern.value,
            'requests_sent': self._requests_sent,
            'responses_received': self._responses_received,
            'average_latency': avg_latency,
            'outstanding': self._requests_sent - self._responses_received,
        }

    def set_pattern(self, pattern: AccessPattern) -> None:
        """设置访问模式"""
        self.pattern = pattern

    def set_base_address(self, addr: int) -> None:
        """设置基地址"""
        self.base_addr = addr & ~63
        self._addr = self.base_addr

    def set_access_size(self, size: int) -> None:
        """设置访问大小"""
        self.access_size = size & ~63


# ============================================================================
# Gem5Bridge Core Class
# ============================================================================

@dataclass
class BridgeConfig:
    """桥接配置"""
    # 连接参数
    gem5_home: Optional[str] = None          # gem5 安装路径
    system_name: str = "system"              # 系统名称

    # 时序参数
    default_latency: int = 10                 # 默认延迟周期
    max_pending_requests: int = 256         # 最大待处理请求数
    request_timeout: int = 10000            # 请求超时周期数

    # 缓存行参数
    cache_line_size: int = 64               # 缓存行大小 (64 or 128 bytes)
    enable_cache_line_handling: bool = True  # 启用缓存行处理

    # QoS 参数
    enable_qos: bool = True
    qos_levels: int = 16                    # QoS 级别数量 (0-15)

    # 统计
    enable_stats: bool = True

    # 调试
    verbose: bool = False
    log_requests: bool = False


@dataclass
class PendingRequest:
    """待处理请求"""
    request: Gem5Request
    transaction: Gem5Transaction
    issue_time: float
    cycle_issued: int = 0
    retries: int = 0


class Gem5Bridge:
    """gem5 桥接器

    在 HBM 仿真平台和 gem5 之间建立通信通道。
    主要功能:
    1. connect_to_gem5() - 建立与 gem5 系统的连接
    2. send_request() - 发送内存请求到 gem5
    3. recv_response() - 接收来自 gem5 的响应
    4. sync() - 同步仿真周期
    5. Cache line handling - 64/128 byte cache line support
    6. Burst transaction support - 突发事务支持
    7. Traffic generator interface - Traffic generator 接口
    """

    def __init__(
        self,
        config: Optional[BridgeConfig] = None,
        gem5_home: Optional[str] = None,
        spec: Optional[HBM4Spec] = None,
    ):
        self._config = config or BridgeConfig(gem5_home=gem5_home)
        if gem5_home:
            self._config.gem5_home = gem5_home

        # HBM4 规范
        self.spec = spec or HBM4Spec()

        # 连接状态
        self.state = Gem5APIState.DISCONNECTED
        self.gem5_system: Optional[Any] = None
        self.gem5_module: Optional[Any] = None

        # 端口
        self.master_port: Optional[Gem5MasterPort] = None
        self.slave_port: Optional[Gem5SlavePort] = None
        self._mock_port: Optional[Gem5MockPort] = None

        # 请求追踪
        self._pending_requests: Dict[int, PendingRequest] = {}
        self._request_counter: int = 0
        self._transaction_counter: int = 0

        # 响应队列
        self._response_queue: List[Gem5Response] = []
        self._response_map: Dict[int, Gem5Response] = {}

        # 统计
        self.stats = Gem5TimingStats()
        self.cycle_stats = Gem5CycleStats()

        # 缓存行处理器
        if self._config.enable_cache_line_handling:
            self.cache_handler = CacheLineHandler(
                line_size=self._config.cache_line_size
            )
        else:
            self.cache_handler = None

        # 回调函数
        self._on_request_sent: Optional[Callable] = None
        self._on_response_received: Optional[Callable] = None

        # 内部状态
        self._current_cycle: int = 0
        self._last_sync_cycle: int = 0

        # Mock 模式
        self._use_mock = True
        self._mock_system: Optional[Gem5MockSystem] = None

        # Traffic Generator 接口
        self._traffic_generators: Dict[str, TrafficGeneratorInterface] = {}

        logger.info(f"Gem5Bridge created (mock_mode={self._use_mock})")

    @property
    def config(self) -> BridgeConfig:
        return self._config

    @config.setter
    def config(self, value: BridgeConfig) -> None:
        self._config = value

    # =========================================================================
    # Connection Management
    # =========================================================================

    def connect_to_gem5(
        self,
        system: Optional[Any] = None,
        master_port_name: str = "cpu.inst",
        slave_port_name: str = "dram.ctrl",
    ) -> bool:
        """连接到 gem5 系统

        Args:
            system: gem5 系统对象 (SimObject)
            master_port_name: Master 端口名称
            slave_port_name: Slave 端口名称

        Returns:
            True if connection successful
        """
        if self.state == Gem5APIState.CONNECTED:
            logger.warning("Already connected to gem5")
            return True

        logger.info("Connecting to gem5...")

        try:
            # 优先使用提供的 gem5 系统
            if system is not None:
                self.gem5_system = system
                self._use_mock = False
                self.state = Gem5APIState.CONNECTED
                logger.info("Connected to provided gem5 system")
                return True

            # 尝试导入真实的 gem5 模块
            if self._config.gem5_home:
                try:
                    import sys
                    sys.path.insert(0, f"{self._config.gem5_home}/src/python")
                    import m5
                    import m5.objects as m5_objects

                    self.gem5_module = m5
                    self._use_mock = False
                    self.state = Gem5APIState.CONNECTED

                    logger.info(f"Connected to gem5 at {self._config.gem5_home}")
                    return True

                except ImportError as e:
                    logger.warning(f"Could not import gem5: {e}")
                    logger.info("Falling back to mock mode")

            # 使用 mock 模式
            self._setup_mock_mode(master_port_name, slave_port_name)
            self.state = Gem5APIState.CONNECTED
            logger.info("Connected in mock mode")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to gem5: {e}")
            self.state = Gem5APIState.ERROR
            return False

    def _setup_mock_mode(
        self,
        master_port_name: str,
        slave_port_name: str,
    ) -> None:
        """设置 mock 模式"""
        self._mock_system = Gem5MockSystem()

        # 创建 mock 端口
        self._mock_port = Gem5MockPort(master_port_name, "master")
        self._mock_system.register_master_port(master_port_name, self._mock_port)

        # 创建桥接端口
        self.master_port = Gem5MasterPort(name=master_port_name)
        self.slave_port = Gem5SlavePort(name=slave_port_name)

        # 设置默认延迟
        self._mock_system.set_latency(master_port_name, self._config.default_latency)

    def disconnect(self) -> None:
        """断开与 gem5 的连接"""
        if self.state == Gem5APIState.DISCONNECTED:
            return

        logger.info("Disconnecting from gem5...")

        # 等待所有请求完成
        self._drain_pending_requests()

        self.gem5_system = None
        self.gem5_module = None
        self._mock_system = None
        self.state = Gem5APIState.DISCONNECTED
        logger.info("Disconnected from gem5")

    def _drain_pending_requests(self) -> None:
        """排空所有待处理请求"""
        if self._pending_requests:
            logger.warning(
                f"Draining {len(self._pending_requests)} pending requests"
            )
            for req_id, pending in list(self._pending_requests.items()):
                if pending.transaction.state != "completed":
                    pending.transaction.mark_failed("disconnect")
                    del self._pending_requests[req_id]

    # =========================================================================
    # Request/Response Handling
    # =========================================================================

    def send_request(
        self,
        addr: int,
        size: int = 64,
        is_write: bool = False,
        data: Optional[List[int]] = None,
        qos: int = 0,
        master_id: int = 0,
        is_prefetch: bool = False,
        is_writeback: bool = False,
    ) -> Optional[int]:
        """发送请求到 gem5

        Args:
            addr: 目标地址
            size: 请求大小 (字节)
            is_write: 是否为写请求
            data: 写数据
            qos: QoS 优先级 (0-15)
            master_id: Master ID
            is_prefetch: 是否为预取请求
            is_writeback: 是否为写回请求

        Returns:
            请求 ID，失败返回 None
        """
        if self.state != Gem5APIState.CONNECTED:
            logger.error("Not connected to gem5")
            return None

        # 检查待处理请求数限制
        if len(self._pending_requests) >= self._config.max_pending_requests:
            logger.error("Too many pending requests")
            return None

        # 缓存行处理
        if self.cache_handler and size != self._config.cache_line_size:
            # 非标准大小，检查是否需要分割
            chunks = self.cache_handler.split_request(addr, size)
            if len(chunks) > 1:
                # 需要发送多个请求
                base_req_id = None
                for chunk_addr, chunk_size in chunks:
                    chunk_id = self._send_single_request(
                        addr=chunk_addr,
                        size=chunk_size,
                        is_write=is_write,
                        data=data,
                        qos=qos,
                        master_id=master_id,
                        is_prefetch=is_prefetch,
                        is_writeback=is_writeback,
                    )
                    if chunk_id is not None:
                        base_req_id = chunk_id
                return base_req_id

        return self._send_single_request(
            addr=addr,
            size=size,
            is_write=is_write,
            data=data,
            qos=qos,
            master_id=master_id,
            is_prefetch=is_prefetch,
            is_writeback=is_writeback,
        )

    def _send_single_request(
        self,
        addr: int,
        size: int,
        is_write: bool,
        data: Optional[List[int]] = None,
        qos: int = 0,
        master_id: int = 0,
        is_prefetch: bool = False,
        is_writeback: bool = False,
    ) -> Optional[int]:
        """发送单个请求"""
        # 创建请求
        req_id = self._next_request_id()
        cmd = Gem5CommandType.CMD_WRITE if is_write else Gem5CommandType.CMD_READ

        if is_write:
            if data is None:
                data = [0] * (size // 8)
            request = create_write_request(
                addr=addr,
                data=data,
                size=size,
                req_id=req_id,
                qos=qos,
                master_id=master_id,
            )
        else:
            request = create_read_request(
                addr=addr,
                size=size,
                req_id=req_id,
                qos=qos,
                master_id=master_id,
            )

        # 设置额外标志
        request.is_prefetch = is_prefetch
        request.is_writeback = is_writeback
        request.issue_cycle = self._current_cycle

        # 计算 beats
        if self.cache_handler:
            request.num_beats = self.cache_handler.calculate_beats(size)

        # 创建事务
        transaction = Gem5Transaction(
            txn_id=self._next_transaction_id(),
            request=request,
            created_cycle=self._current_cycle,
        )

        # 记录待处理请求
        pending = PendingRequest(
            request=request,
            transaction=transaction,
            issue_time=time.time(),
            cycle_issued=self._current_cycle,
        )
        self._pending_requests[req_id] = pending

        # 更新统计
        self.stats.total_requests += 1
        if is_write:
            self.stats.total_writes += 1
        else:
            self.stats.total_reads += 1

        # 发送请求
        if self._send_to_gem5(request):
            transaction.mark_issued(self._current_cycle)
            logger.debug(f"Sent request {req_id}: addr=0x{addr:x}, size={size}")
        else:
            del self._pending_requests[req_id]
            return None

        # 调用回调
        if self._on_request_sent:
            self._on_request_sent(request)

        return req_id

    def _send_to_gem5(self, request: Gem5Request) -> bool:
        """发送请求到 gem5 系统"""
        if self._use_mock:
            # Mock 模式：模拟发送
            if self._mock_port:
                return self._mock_port.send(request)
            return True

        # 真实 gem5：使用 Python API
        try:
            # 构造 gem5 Packet
            pkt = self._create_gem5_packet(request)
            return self.master_port.send(pkt)
        except Exception as e:
            logger.error(f"Failed to send request to gem5: {e}")
            return False

    def _create_gem5_packet(self, request: Gem5Request) -> Any:
        """创建 gem5 Packet 对象"""
        # 尝试使用 gem5 API
        if self.gem5_module:
            m5 = self.gem5_module
            # 需要根据实际 gem5 版本实现
            # 这是一个占位符
            return None
        return None

    def recv_response(
        self,
        req_id: Optional[int] = None,
        timeout_cycles: int = 10000,
    ) -> Optional[Gem5Response]:
        """接收来自 gem5 的响应

        Args:
            req_id: 特定请求 ID，None 表示接收任意响应
            timeout_cycles: 超时周期数

        Returns:
            响应对象，超时返回 None
        """
        if self.state != Gem5APIState.CONNECTED:
            logger.error("Not connected to gem5")
            return None

        # 检查特定请求
        if req_id is not None:
            if req_id in self._response_map:
                resp = self._response_map[req_id]
                del self._response_map[req_id]
                return resp
            if req_id in self._pending_requests:
                pending = self._pending_requests[req_id]
                latency = self._mock_system.get_latency(
                    self.master_port.name
                ) if self._mock_system else self._config.default_latency
                expected_cycle = pending.cycle_issued + latency
                if self._current_cycle >= expected_cycle:
                    resp = self._generate_mock_response(pending)
                    if resp:
                        self._handle_response(resp)
                        return resp

        # 尝试从 gem5 接收响应
        start_cycle = self._current_cycle
        while (self._current_cycle - start_cycle) < timeout_cycles:
            resp = self._try_recv_from_gem5(req_id)
            if resp is not None:
                self._handle_response(resp)
                return resp

            # 推进一个周期
            self._current_cycle += 1

        # 超时
        logger.warning(f"Timeout waiting for response (req_id={req_id})")
        return None

    def _try_recv_from_gem5(self, req_id: Optional[int] = None) -> Optional[Gem5Response]:
        """尝试从 gem5 接收响应"""
        if self._use_mock:
            return self._mock_recv_response(req_id)
        # 真实 gem5 实现
        return None

    def _generate_mock_response(self, pending: PendingRequest) -> Optional[Gem5Response]:
        """生成 mock 响应"""
        request = pending.request

        resp = Gem5Response(
            req_id=request.req_id,
            addr=request.addr.addr,
            status=Gem5ResponseStatus.OK,
            cmd=request.cmd,
            issue_cycle=pending.cycle_issued,
            complete_cycle=self._current_cycle,
        )

        if request.cmd == Gem5CommandType.CMD_READ:
            # 生成模拟读取数据
            num_words = request.size // 8
            resp.data = [0] * num_words

        return resp

    def _mock_recv_response(self, req_id: Optional[int] = None) -> Optional[Gem5Response]:
        """Mock 模式：接收响应"""
        if self._pending_requests:
            # 获取第一个请求（按 FIFO）
            if req_id and req_id in self._pending_requests:
                pending = self._pending_requests[req_id]
            else:
                pending = next(iter(self._pending_requests.values()))

            # 计算延迟
            latency = self._mock_system.get_latency(
                self.master_port.name
            ) if self._mock_system else self._config.default_latency
            expected_cycle = pending.cycle_issued + latency
            if self._current_cycle >= expected_cycle:
                # 生成响应
                resp = self._generate_mock_response(pending)
                return resp

        return None

    def _handle_response(self, response: Gem5Response) -> None:
        """处理接收到的响应"""
        req_id = response.req_id

        # 更新事务状态
        if req_id in self._pending_requests:
            pending = self._pending_requests[req_id]
            pending.transaction.mark_completed(response)
            del self._pending_requests[req_id]

        # 更新统计
        self.stats.total_responses += 1
        self.stats.total_latency += response.latency

        # 缓存响应
        self._response_map[req_id] = response

        # 调用回调
        if self._on_response_received:
            self._on_response_received(response)

        logger.debug(
            f"Received response: req_id={req_id}, "
            f"latency={response.latency} cycles"
        )

    # =========================================================================
    # Synchronization
    # =========================================================================

    def sync(self, cycle: Optional[int] = None) -> int:
        """同步仿真周期

        Args:
            cycle: 目标周期，None 表示前进到下一个周期

        Returns:
            当前周期数
        """
        if cycle is None:
            cycle = self._current_cycle + 1

        # 推进 mock 系统
        if self._mock_system:
            cycles_to_advance = cycle - self._mock_system.clock
            if cycles_to_advance > 0:
                self._mock_system.tick(cycles_to_advance)

        # 更新状态
        old_cycle = self._current_cycle
        self._current_cycle = cycle
        self._last_sync_cycle = cycle

        # 处理超时请求
        self._check_request_timeouts()

        # 统计
        self.cycle_stats.cycles = cycle

        return cycle - old_cycle

    def _check_request_timeouts(self) -> None:
        """检查请求超时"""
        timeout_reqs = []
        for req_id, pending in self._pending_requests.items():
            cycles_pending = self._current_cycle - pending.cycle_issued
            if cycles_pending > self._config.request_timeout:
                timeout_reqs.append(req_id)

        for req_id in timeout_reqs:
            logger.warning(f"Request {req_id} timed out")
            pending = self._pending_requests[req_id]
            pending.transaction.mark_failed("timeout")

            # 生成错误响应
            resp = Gem5Response(
                req_id=req_id,
                addr=pending.request.addr.addr,
                status=Gem5ResponseStatus.TIMEOUT,
                cmd=pending.request.cmd,
                issue_cycle=pending.cycle_issued,
                complete_cycle=self._current_cycle,
            )
            self._response_map[req_id] = resp
            del self._pending_requests[req_id]

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _next_request_id(self) -> int:
        """生成下一个请求 ID"""
        req_id = self._request_counter
        self._request_counter += 1
        return req_id

    def _next_transaction_id(self) -> int:
        """生成下一个事务 ID"""
        txn_id = self._transaction_counter
        self._transaction_counter += 1
        return txn_id

    def get_pending_count(self) -> int:
        """获取待处理请求数"""
        return len(self._pending_requests)

    def get_transaction(self, req_id: int) -> Optional[Gem5Transaction]:
        """获取事务信息"""
        if req_id in self._pending_requests:
            return self._pending_requests[req_id].transaction
        return None

    def set_callback(
        self,
        event: str,
        callback: Callable[[Any], None],
    ) -> None:
        """设置回调函数"""
        if event == "request_sent":
            self._on_request_sent = callback
        elif event == "response_received":
            self._on_response_received = callback

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_requests": self.stats.total_requests,
            "total_responses": self.stats.total_responses,
            "total_reads": self.stats.total_reads,
            "total_writes": self.stats.total_writes,
            "avg_latency": self.stats.avg_latency,
            "read_ratio": self.stats.read_ratio,
            "pending_requests": len(self._pending_requests),
            "current_cycle": self._current_cycle,
        }

        # 添加缓存行处理统计
        if self.cache_handler:
            stats["cache_line"] = self.cache_handler.get_stats()

        return stats

    def reset_stats(self) -> None:
        """重置统计"""
        self.stats = Gem5TimingStats()
        self.cycle_stats = Gem5CycleStats()
        self._request_counter = 0
        self._transaction_counter = 0

        if self.cache_handler:
            self.cache_handler = CacheLineHandler(
                line_size=self._config.cache_line_size
            )

    # =========================================================================
    # High-Level Operations
    # =========================================================================

    def read(
        self,
        addr: int,
        size: int = 64,
        qos: int = 0,
    ) -> Optional[List[int]]:
        """便捷方法：读内存"""
        req_id = self.send_request(
            addr=addr,
            size=size,
            is_write=False,
            qos=qos,
        )

        if req_id is None:
            return None

        resp = self.recv_response(req_id=req_id)
        if resp and resp.data:
            return resp.data
        return None

    def write(
        self,
        addr: int,
        data: List[int],
        size: int = 64,
        qos: int = 0,
    ) -> bool:
        """便捷方法：写内存"""
        req_id = self.send_request(
            addr=addr,
            size=size,
            is_write=True,
            data=data,
            qos=qos,
        )

        if req_id is None:
            return False

        resp = self.recv_response(req_id=req_id)
        return resp is not None and resp.status == Gem5ResponseStatus.OK

    def burst_read(
        self,
        addr: int,
        num_beats: int,
        beat_size: int = 64,
    ) -> List[Gem5Response]:
        """突发读

        Args:
            addr: 起始地址
            num_beats: Beat 数量
            beat_size: 每个 beat 的大小

        Returns:
            响应列表
        """
        responses = []
        for i in range(num_beats):
            beat_addr = addr + i * beat_size
            req_id = self.send_request(
                addr=beat_addr,
                size=beat_size,
                is_write=False,
            )
            if req_id is None:
                break

            resp = self.recv_response(req_id=req_id)
            if resp:
                responses.append(resp)
            else:
                break

        return responses

    def burst_write(
        self,
        addr: int,
        data: List[int],
        num_beats: int,
        beat_size: int = 64,
    ) -> List[Gem5Response]:
        """突发写

        Args:
            addr: 起始地址
            data: 数据
            num_beats: Beat 数量
            beat_size: 每个 beat 的大小

        Returns:
            响应列表
        """
        responses = []
        words_per_beat = beat_size // 8

        for i in range(num_beats):
            beat_addr = addr + i * beat_size
            beat_data = data[i * words_per_beat:(i + 1) * words_per_beat]

            req_id = self.send_request(
                addr=beat_addr,
                size=beat_size,
                is_write=True,
                data=beat_data,
            )
            if req_id is None:
                break

            resp = self.recv_response(req_id=req_id)
            if resp:
                responses.append(resp)
            else:
                break

        return responses

    # =========================================================================
    # Traffic Generator Interface
    # =========================================================================

    def create_traffic_generator(
        self,
        name: str,
        pattern: str = "sequential",
    ) -> TrafficGeneratorInterface:
        """创建 Traffic Generator

        Args:
            name: 生成器名称
            pattern: 访问模式 ("sequential", "random", "hotspot", "stride")

        Returns:
            TrafficGeneratorInterface 实例
        """
        tg = TrafficGeneratorInterface(
            name=name,
            bridge=self,
            spec=self.spec,
        )

        # 设置模式
        pattern_map = {
            "sequential": TrafficGeneratorInterface.AccessPattern.SEQUENTIAL,
            "random": TrafficGeneratorInterface.AccessPattern.RANDOM,
            "hotspot": TrafficGeneratorInterface.AccessPattern.HOTSPOT,
            "stride": TrafficGeneratorInterface.AccessPattern.STRIDE,
        }
        if pattern in pattern_map:
            tg.set_pattern(pattern_map[pattern])

        self._traffic_generators[name] = tg
        return tg

    def get_traffic_generator(self, name: str) -> Optional[TrafficGeneratorInterface]:
        """获取 Traffic Generator"""
        return self._traffic_generators.get(name)

    def get_all_traffic_generators(self) -> Dict[str, TrafficGeneratorInterface]:
        """获取所有 Traffic Generator"""
        return self._traffic_generators.copy()

    # =========================================================================
    # HBM4-Specific Methods
    # =========================================================================

    def get_channel_load(self, channel_id: int) -> int:
        """获取通道负载

        Args:
            channel_id: 通道 ID

        Returns:
            待处理请求数
        """
        from model.controller.hbm4_address_decoder import HBM4AddressDecoder

        decoder = HBM4AddressDecoder(spec=self.spec)
        count = 0

        for pending in self._pending_requests.values():
            decoded = decoder.decode(pending.request.addr.addr)
            if decoded.channel_id == channel_id:
                count += 1

        return count

    def get_channel_stats(self) -> Dict[int, Dict[str, int]]:
        """获取通道统计"""
        from model.controller.hbm4_address_decoder import HBM4AddressDecoder

        decoder = HBM4AddressDecoder(spec=self.spec)
        stats = {
            ch: {'requests': 0, 'reads': 0, 'writes': 0}
            for ch in range(self.spec.channels)
        }

        for pending in self._pending_requests.values():
            decoded = decoder.decode(pending.request.addr.addr)
            stats[decoded.channel_id]['requests'] += 1
            if pending.request.cmd == Gem5CommandType.CMD_READ:
                stats[decoded.channel_id]['reads'] += 1
            else:
                stats[decoded.channel_id]['writes'] += 1

        return stats

    def __enter__(self) -> "Gem5Bridge":
        """Context manager: 进入"""
        self.connect_to_gem5()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager: 退出"""
        self.disconnect()


# ============================================================================
# Factory Functions
# ============================================================================

def create_bridge(
    gem5_home: Optional[str] = None,
    use_mock: bool = True,
    spec: Optional[HBM4Spec] = None,
    **kwargs,
) -> Gem5Bridge:
    """创建 gem5 桥接器的快捷函数"""
    config = BridgeConfig(gem5_home=gem5_home, **kwargs)
    bridge = Gem5Bridge(config=config, spec=spec)

    if use_mock:
        bridge._use_mock = True
        bridge._setup_mock_mode("cpu.inst", "dram.ctrl")
        bridge.state = Gem5APIState.CONNECTED

    return bridge


# ============================================================================
# __init__.py exports
# ============================================================================

__all__ = [
    "Gem5Bridge",
    "BridgeConfig",
    "Gem5APIState",
    "Gem5MockPort",
    "Gem5MockSystem",
    "PendingRequest",
    "CacheLineSize",
    "CacheLineConfig",
    "CacheLineHandler",
    "TrafficGeneratorInterface",
    "create_bridge",
]