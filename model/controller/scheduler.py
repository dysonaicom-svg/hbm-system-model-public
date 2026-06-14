"""
HBM FR-FCFS Scheduler
参考设计文档 2026-06-15-hbm-system-model-design.md 的 5.1.2 和 5.1.3 节

FR-FCFS (First-Ready First-Come-First-Served):
1. 优先选择 row-hit 的请求
2. 同优先级按时间戳排序，选择最老的
3. 读/写仲裁
"""

from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass, field
from collections import defaultdict
import time

from model.controller.config import HBMConfig
from model.controller.request import HBMRequest, RequestState
from model.controller.queue import ReadQueue, WriteQueue


@dataclass
class BankState:
    """Bank 状态"""
    bank_id: int
    is_open: bool = False
    open_row: int = -1
    last_access_time: float = 0.0


class HBMScheduler:
    """HBM 调度器基类"""
    
    def __init__(self, config: HBMConfig):
        self.config = config
    
    def schedule(self, read_queue: ReadQueue, write_queue: WriteQueue, 
                bank_states: Dict[Tuple, BankState], current_time: float) -> Optional[HBMRequest]:
        """调度下一个请求
        
        Args:
            read_queue: 读队列
            write_queue: 写队列
            bank_states: Bank 状态字典
            current_time: 当前时间
            
        Returns:
            下一个调度的请求
        """
        raise NotImplementedError


class FRFCFSScheduler(HBMScheduler):
    """FR-FCFS 调度器
    
    First-Ready FCFS 调度策略:
    - Row-hit 优先
    - 同优先级按时间戳
    - 读写仲裁可配置
    """
    
    # Read/Write arbitration weights
    RD_PRIORITY = 1.0
    WR_PRIORITY = 1.0
    
    def __init__(self, config: HBMConfig, rd_priority: float = 1.0, wr_priority: float = 1.0):
        super().__init__(config)
        self.rd_priority = rd_priority
        self.wr_priority = wr_priority
        
        # Read-Write turnaround penalty (cycles)
        self.TURNAROUND_PENALTY = 3
    
    def schedule(self, read_queue: ReadQueue, write_queue: WriteQueue,
                bank_states: Dict[Tuple, BankState], 
                current_time: float,
                last_cmd_type: str = "READ") -> Optional[HBMRequest]:
        """FR-FCFS 调度
        
        Args:
            read_queue: 读队列
            write_queue: 写队列
            bank_states: Bank 状态字典
            current_time: 当前时间
            last_cmd_type: 上次命令类型 ("READ" or "WRITE")
            
        Returns:
            下一个调度的请求
        """
        # 获取候选请求
        read_candidates = self._get_row_hit_candidates(read_queue, bank_states)
        write_candidates = self._get_row_hit_candidates(write_queue, bank_states)
        
        # 如果没有 row-hit 请求，尝试获取所有请求
        if not read_candidates and not write_candidates:
            read_candidates = list(read_queue._queue)
            write_candidates = list(write_queue._queue)
        
        # 读/写仲裁
        best_read = self._select_oldest(read_candidates) if read_candidates else None
        best_write = self._select_oldest(write_candidates) if write_candidates else None
        
        # 选择最佳请求
        selected = self._arbitrate_read_write(best_read, best_write, last_cmd_type, current_time)
        
        if selected:
            # 更新请求状态
            selected.mark_scheduled(current_time)
            
            # 从队列移除
            if selected.is_read:
                read_queue.remove(selected.request_id)
            else:
                write_queue.remove(selected.request_id)
        
        return selected
    
    def _get_row_hit_candidates(self, queue, bank_states: Dict) -> List[HBMRequest]:
        """获取 row-hit 的候选请求"""
        candidates = []
        for req in queue._queue:
            bank_key = (req.channel_id, req.pseudo_channel_id, req.bank_id)
            bank_state = bank_states.get(bank_key)
            if bank_state and bank_state.is_open and bank_state.open_row == req.row_id:
                req.row_hit = True
                candidates.append(req)
            else:
                req.row_hit = False
        return candidates
    
    def _select_oldest(self, candidates: List[HBMRequest]) -> Optional[HBMRequest]:
        """选择最老的请求"""
        if not candidates:
            return None
        return min(candidates, key=lambda r: r.arrival_time)
    
    def _arbitrate_read_write(self, read_req: Optional[HBMRequest], 
                              write_req: Optional[HBMRequest],
                              last_cmd: str, current_time: float) -> Optional[HBMRequest]:
        """读写仲裁
        
        考虑 turnaround penalty 和优先级权重。
        """
        if not read_req and not write_req:
            return None
        
        if read_req and not write_req:
            return read_req
        
        if write_req and not read_req:
            return write_req
        
        # 两者都有
        read_score = read_req.arrival_time / self.rd_priority
        write_score = write_req.arrival_time / self.wr_priority
        
        # 考虑 turnaround penalty
        if last_cmd == "READ":
            write_score -= self.TURNAROUND_PENALTY * 1e-9  # 转换为秒
        else:
            read_score -= self.TURNAROUND_PENALTY * 1e-9
        
        return read_req if read_score < write_score else write_req


@dataclass
class SchedulerStats:
    """调度器统计"""
    schedule_count: int = 0
    row_hit_count: int = 0
    row_miss_count: int = 0
    read_count: int = 0
    write_count: int = 0
    
    @property
    def row_hit_rate(self) -> float:
        if self.schedule_count == 0:
            return 0.0
        return self.row_hit_count / self.schedule_count
    
    def record_schedule(self, request: HBMRequest):
        self.schedule_count += 1
        if request.row_hit:
            self.row_hit_count += 1
        else:
            self.row_miss_count += 1
        if request.is_read:
            self.read_count += 1
        else:
            self.write_count += 1
