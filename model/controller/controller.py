"""
HBM Controller Integration
整合所有 Phase A 模块的主控制器
"""

from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
import time

from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.request import HBMRequest, HBMResponse, RequestState
from model.controller.queue import ReadQueue, WriteQueue, QueueManager
from model.controller.address_decoder import AddressDecoder, DecodedAddress
from model.controller.scheduler import FRFCFSScheduler, BankState, SchedulerStats
from model.controller.qos_scheduler import QoSScheduler
from model.controller.refresh_scheduler import RefreshScheduler, RefreshManager
from model.controller.exceptions import QueueOverflowError


@dataclass
class HBMController:
    """HBM 控制器整合模型
    
    整合所有 Phase A 模块的主控制器。
    """
    
    def __init__(self, config: Optional[HBMConfig] = None):
        """初始化控制器
        
        Args:
            config: HBM 配置 (默认 HBM3 配置)
        """
        self.config = config or HBM3_DEFAULT
        self.current_time = 0.0
        
        # 初始化组件
        self.decoder = AddressDecoder(self.config)
        self.queue_manager = QueueManager.create(self.config.queue_depth)
        
        # 初始化调度器
        if self.config.scheduler_mode == "qos":
            self.scheduler = QoSScheduler(self.config)
        else:
            self.scheduler = FRFCFSScheduler(self.config)
        
        # 初始化刷新调度器
        self.refresh_manager = RefreshManager.create(self.config)
        
        # Bank 状态
        self.bank_states: Dict[Tuple, BankState] = {}
        
        # 统计
        self.stats = {
            'total_requests': 0,
            'read_requests': 0,
            'write_requests': 0,
            'row_hit_count': 0,
            'refresh_count': 0,
        }
        
        # 调度统计
        self.scheduler_stats = SchedulerStats()

        # 最近调度的请求 (用于 CommandSequencer 集成)
        self._last_scheduled_request: Optional[HBMRequest] = None

        # 最近调度的命令类型
        self._last_cmd_type: str = "READ"
    
    def submit_request(self, request: HBMRequest) -> bool:
        """提交请求
        
        Args:
            request: HBM 请求
            
        Returns:
            True 如果成功提交
        """
        # 解码地址
        decoded = self.decoder.decode(request.addr)
        request.stack_id = decoded.stack_id
        request.channel_id = decoded.channel_id
        request.pseudo_channel_id = decoded.pseudo_channel_id
        request.bank_group_id = decoded.bank_group_id
        request.bank_id = decoded.bank_id
        request.row_id = decoded.row_id
        request.col_id = decoded.col_id
        
        # 更新 bank 状态
        bank_key = (request.channel_id, request.pseudo_channel_id, request.bank_id)
        if bank_key not in self.bank_states:
            self.bank_states[bank_key] = BankState(bank_id=request.bank_id)
        
        # 检查 row hit
        bank_state = self.bank_states[bank_key]
        request.row_hit = (bank_state.is_open and bank_state.open_row == request.row_id)
        
        # 入队
        if request.is_read:
            success = self.queue_manager.push_read(request)
        else:
            success = self.queue_manager.push_write(request)

        if success:
            # 设置到达时间（使用当前仿真周期）
            request.set_arrival_time(self.current_time)
            self.stats['total_requests'] += 1
            if request.is_read:
                self.stats['read_requests'] += 1
            else:
                self.stats['write_requests'] += 1
            if request.row_hit:
                self.stats['row_hit_count'] += 1
        
        return success
    
    def tick(self) -> Tuple[Optional[HBMRequest], Optional[HBMResponse]]:
        """执行一个时钟周期

        Returns:
            Tuple of (scheduled_request, response).
            scheduled_request is the request being scheduled this cycle.
            response is None if no request completed, or HBMResponse if completed.
            Note: In the current model, the scheduled request IS completed
            immediately (simplified model). For cycle-accurate timing,
            use tick_advanced() instead.
        """
        self.current_time += 1  # 使用周期作为时间单位

        # 检查刷新
        for stack_id in range(self.config.stack_count):
            if self.refresh_manager.needs_refresh(stack_id, self.current_time):
                cmd = self.refresh_manager.schedule_refresh(stack_id, self.current_time, self.bank_states)
                if cmd:
                    self.stats['refresh_count'] += 1

        # 调度请求
        scheduled = self.scheduler.schedule(
            self.queue_manager.read_queue,
            self.queue_manager.write_queue,
            self.bank_states,
            self.current_time,
            self._last_cmd_type
        )

        if scheduled:
            # 更新 last command type
            self._last_cmd_type = "READ" if scheduled.is_read else "WRITE"
            self._last_scheduled_request = scheduled

            # 更新 bank 状态
            bank_key = (scheduled.channel_id, scheduled.pseudo_channel_id, scheduled.bank_id)
            if scheduled in self.queue_manager.read_queue._queue or                scheduled in self.queue_manager.write_queue._queue:
                # 请求还在队列中，不更新状态
                pass
            else:
                # 请求已调度，更新 bank 状态
                bank_state = self.bank_states.get(bank_key)
                if bank_state:
                    bank_state.is_open = True
                    bank_state.open_row = scheduled.row_id
                    bank_state.last_access_time = self.current_time

            # 标记完成
            scheduled.mark_completed(self.current_time)

            # 记录调度统计
            self.scheduler_stats.record_schedule(scheduled)

            # 计算延迟（周期转换为 ns）
            latency_cycles = scheduled.get_latency_cycles()
            latency_ns = latency_cycles * self.config.timing.clock_period_ns

            return (scheduled, HBMResponse(
                request_id=scheduled.request_id,
                status="OK",
                latency=latency_ns,
            ))

        return (None, None)
    
    def get_bandwidth(self) -> float:
        """计算当前有效带宽"""
        total_bytes = 0
        for req_id in range(1, self.scheduler_stats.schedule_count + 1):
            total_bytes += 64  # 假设每个请求 64 bytes
        if self.current_time > 0:
            return total_bytes / self.current_time / 1e9  # GB/s
        return 0.0
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'controller': self.stats,
            'scheduler': {
                'schedule_count': self.scheduler_stats.schedule_count,
                'row_hit_rate': self.scheduler_stats.row_hit_rate,
                'read_count': self.scheduler_stats.read_count,
                'write_count': self.scheduler_stats.write_count,
            },
            'queue': self.queue_manager.get_stats(),
            'refresh': self.refresh_manager.get_total_stats(),
        }
