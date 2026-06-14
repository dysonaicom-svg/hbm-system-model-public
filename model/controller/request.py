"""
HBM Request and Response Classes
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, ClassVar
import time


class RequestState(IntEnum):
    """请求状态枚举
    
    表示请求在生命周期中的状态。
    """
    PENDING = 0      # 等待调度
    SCHEDULED = 1    # 已调度，等待执行
    IN_PROGRESS = 2 # 执行中
    COMPLETED = 3    # 已完成
    FAILED = 4       # 失败


@dataclass
class HBMRequest:
    """HBM 内存请求
    
    表示一个读或写内存请求，包含地址解码信息和状态跟踪。
    
    Attributes:
        addr: 64-bit 内存地址
        length: 请求长度 (bytes)
        is_read: True=读请求, False=写请求
        qos: QoS 优先级 (0-15, 15 最高)
        burst_length: 突发长度
        request_id: 全局唯一请求 ID
        arrival_time: 请求到达时间戳
        stack_id: 解码后的 stack ID
        channel_id: 解码后的通道 ID
        pseudo_channel_id: 解码后的伪通道 ID
        bank_group_id: 解码后的 bank group ID
        bank_id: 解码后的 bank ID
        row_id: 解码后的行 ID
        col_id: 解码后的列 ID
        row_hit: 是否 row hit
        state: 当前请求状态
        scheduled_time: 调度时间
        completion_time: 完成时间
    """
    addr: int                                # 64-bit address
    length: int                             # bytes
    is_read: bool                           # True=read, False=write
    qos: int = 8                             # 0-15 priority
    burst_length: int = 32                  # burst size
    
    # 内部字段 (自动生成)
    request_id: int = field(default=0, init=False)
    arrival_time: float = field(default=0.0, init=False)
    
    # 解码后的地址字段
    stack_id: int = field(default=0, init=False)
    channel_id: int = field(default=0, init=False)
    pseudo_channel_id: int = field(default=0, init=False)
    bank_group_id: int = field(default=0, init=False)
    bank_id: int = field(default=0, init=False)
    row_id: int = field(default=0, init=False)
    col_id: int = field(default=0, init=False)
    
    # 状态
    row_hit: bool = False
    state: RequestState = RequestState.PENDING
    scheduled_time: float = 0.0
    completion_time: float = 0.0
    
    # 类变量用于生成唯一 ID
    _next_id: ClassVar[int] = 0
    _id_lock: ClassVar[bool] = False
    
    def __post_init__(self):
        """初始化自动生成的字段"""
        # 设置到达时间
        if self.arrival_time == 0.0:
            self.arrival_time = time.time()
        
        # 生成唯一请求 ID
        if self.request_id == 0:
            HBMRequest._next_id += 1
            self.request_id = HBMRequest._next_id
    
    @property
    def latency(self) -> float:
        """计算请求延迟 (秒)"""
        if self.completion_time > 0:
            return self.completion_time - self.arrival_time
        return 0.0
    
    @property
    def is_completed(self) -> bool:
        """检查请求是否已完成"""
        return self.state == RequestState.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """检查请求是否失败"""
        return self.state == RequestState.FAILED
    
    @property
    def is_pending(self) -> bool:
        """检查请求是否等待中"""
        return self.state == RequestState.PENDING
    
    def mark_scheduled(self, timestamp: float):
        """标记请求已调度"""
        self.state = RequestState.SCHEDULED
        self.scheduled_time = timestamp
    
    def mark_in_progress(self):
        """标记请求执行中"""
        self.state = RequestState.IN_PROGRESS
    
    def mark_completed(self, timestamp: float):
        """标记请求已完成"""
        self.state = RequestState.COMPLETED
        self.completion_time = timestamp
    
    def mark_failed(self):
        """标记请求失败"""
        self.state = RequestState.FAILED
    
    def __repr__(self) -> str:
        op = "READ" if self.is_read else "WRITE"
        return (f"HBMRequest(id={self.request_id}, {op}, "
                f"addr=0x{self.addr:016x}, len={self.length}, "
                f"qos={self.qos}, state={self.state.name})")


@dataclass  
class HBMResponse:
    """HBM 响应
    
    表示请求完成后的响应。
    
    Attributes:
        request_id: 关联的请求 ID
        status: 状态 ("OK", "SLVERR", "DECERR")
        latency: 响应延迟 (纳秒)
        data: 读数据 (读请求时)
    """
    request_id: int
    status: str = "OK"                      # "OK", "SLVERR", "DECERR"
    latency: float = 0.0                    # response latency in ns
    data: Optional[bytes] = None            # read data
    
    @property
    def is_success(self) -> bool:
        """检查响应是否成功"""
        return self.status == "OK"
    
    def __repr__(self) -> str:
        return f"HBMResponse(id={self.request_id}, status={self.status}, latency={self.latency:.2f}ns)"
