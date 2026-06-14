"""
HBM DRAM Bank State Machine
参考设计文档 2026-06-15-hbm-system-model-design.md 的 5.2.1 和 5.2.2 节

Bank 状态机实现:
- IDLE: Bank 空闲
- ACTIVE: Bank 已激活，行打开
- READING: 读操作中
- WRITING: 写操作中
- REFRESHING: 刷新中
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import time

from model.dram.timing import HBM3Timing


class BankStateEnum(Enum):
    """Bank 状态枚举"""
    IDLE = 0
    ACTIVE = 1
    READING = 2
    WRITING = 3
    REFRESHING = 4


@dataclass
class Bank:
    """DRAM Bank 状态"""
    bank_id: int
    state: BankStateEnum = BankStateEnum.IDLE
    open_row: int = -1
    activate_time: float = -1.0  # 使用 -1.0 表示从未激活
    read_time: float = 0.0
    write_time: float = 0.0
    precharge_time: float = -1.0  # 使用 -1.0 表示从未预充电
    refresh_time: float = 0.0

    @property
    def is_idle(self) -> bool:
        return self.state == BankStateEnum.IDLE

    @property
    def is_active(self) -> bool:
        return self.state == BankStateEnum.ACTIVE

    @property
    def row_open(self) -> bool:
        return self.is_active and self.open_row >= 0

    def __repr__(self) -> str:
        row_str = f"row=0x{self.open_row:x}" if self.open_row >= 0 else "row=closed"
        return f"Bank{self.bank_id}({self.state.name}, {row_str})"


class BankStateMachine:
    """Bank 状态机
    
    管理单个 bank 的状态转换和时序约束。
    """
    
    def __init__(self, bank_id: int, timing: HBM3Timing):
        self.bank = Bank(bank_id=bank_id)
        self.timing = timing
        self.current_time = 0.0
    
    def set_time(self, current_time: float):
        """设置当前时间"""
        self.current_time = current_time
    
    def can_activate(self) -> bool:
        """检查是否可以发起 ACT

        时序约束:
        - Bank 必须是 IDLE 状态
        - 距离上次操作必须 >= tRC (如果是新 bank，始终可用)
        """
        if self.bank.state != BankStateEnum.IDLE:
            return False

        # 如果 bank 从未激活过，可以激活
        if self.bank.activate_time < 0:
            return True

        time_since_act = self.current_time - self.bank.activate_time
        return time_since_act >= self.timing.cycles_to_s(self.timing.tRC)
    
    def activate(self, row: int) -> bool:
        """激活 Bank
        
        Args:
            row: 要激活的行号
            
        Returns:
            True 如果成功激活
        """
        if not self.can_activate():
            return False
        
        self.bank.state = BankStateEnum.ACTIVE
        self.bank.open_row = row
        self.bank.activate_time = self.current_time
        return True
    
    def can_precharge(self) -> bool:
        """检查是否可以发起 PRE
        
        时序约束:
        - Bank 必须是 ACTIVE 状态
        - 距离 ACT >= tRAS
        """
        if self.bank.state != BankStateEnum.ACTIVE:
            return False
        
        time_since_act = self.current_time - self.bank.activate_time
        return time_since_act >= self.timing.cycles_to_s(self.timing.tRAS)
    
    def precharge(self) -> bool:
        """关闭 Bank"""
        if not self.can_precharge():
            return False
        
        self.bank.state = BankStateEnum.IDLE
        self.bank.precharge_time = self.current_time
        return True
    
    def can_read(self) -> bool:
        """检查是否可以发起 READ
        
        时序约束:
        - Bank 必须是 ACTIVE 状态
        - 距离 ACT >= tRCD
        """
        if self.bank.state != BankStateEnum.ACTIVE:
            return False
        
        time_since_act = self.current_time - self.bank.activate_time
        return time_since_act >= self.timing.cycles_to_s(self.timing.tRCD)
    
    def read(self) -> bool:
        """发起 READ"""
        if not self.can_read():
            return False
        
        self.bank.state = BankStateEnum.READING
        self.bank.read_time = self.current_time
        return True
    
    def can_write(self) -> bool:
        """检查是否可以发起 WRITE
        
        时序约束:
        - Bank 必须是 ACTIVE 状态
        - 距离 ACT >= tRCD
        """
        if self.bank.state != BankStateEnum.ACTIVE:
            return False
        
        time_since_act = self.current_time - self.bank.activate_time
        return time_since_act >= self.timing.cycles_to_s(self.timing.tRCD)
    
    def write(self) -> bool:
        """发起 WRITE"""
        if not self.can_write():
            return False
        
        self.bank.state = BankStateEnum.WRITING
        self.bank.write_time = self.current_time
        return True
    
    def is_row_hit(self, row: int) -> bool:
        """检查是否 row hit"""
        return (self.bank.state == BankStateEnum.ACTIVE and 
                self.bank.open_row == row)
    
    def complete_read(self):
        """READ 完成，返回 ACTIVE"""
        self.bank.state = BankStateEnum.ACTIVE
    
    def complete_write(self):
        """WRITE 完成"""
        self.bank.state = BankStateEnum.ACTIVE
    
    def refresh(self) -> bool:
        """执行刷新"""
        if self.bank.state == BankStateEnum.IDLE:
            self.bank.state = BankStateEnum.REFRESHING
            self.bank.refresh_time = self.current_time
            return True
        return False
    
    def complete_refresh(self):
        """刷新完成"""
        self.bank.state = BankStateEnum.IDLE
