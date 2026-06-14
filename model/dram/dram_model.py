"""
HBM DRAM Model - 完整 DRAM 模型接口
集成 bank 状态机、channel 模型、stack 模型

参考设计文档 2026-06-15-hbm-system-model-design.md 的 5.2 节
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from model.dram.timing import HBM3Timing, get_timing_for_hbm_version
from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
from model.dram.channel_model import Channel, ChannelArray
from model.dram.stack_model import Stack


class DRAMCommand(Enum):
    """DRAM 命令枚举"""
    NOP = 0
    ACT = 1      # Activate
    PRE = 2      # Precharge
    PREA = 3     # Precharge All
    RD = 4       # Read
    WR = 5       # Write
    REF = 6      # Refresh
    REFPB = 7    # Refresh per bank


@dataclass
class DRAMResponse:
    """DRAM 响应"""
    success: bool
    data: Optional[bytes] = None
    latency_cycles: int = 0
    error: Optional[str] = None


@dataclass
class DRAMStats:
    """DRAM 统计信息"""
    total_activations: int = 0
    total_precharges: int = 0
    total_reads: int = 0
    total_writes: int = 0
    total_refreshes: int = 0
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0
    bank_busy_cycles: int = 0

    def add_activation(self):
        self.total_activations += 1

    def add_read(self):
        self.total_reads += 1

    def add_write(self):
        self.total_writes += 1

    def add_hit(self):
        self.row_hits += 1

    def add_miss(self):
        self.row_misses += 1

    def add_conflict(self):
        self.row_conflicts += 1

    def __repr__(self) -> str:
        total = self.row_hits + self.row_misses + self.row_conflicts
        hit_rate = self.row_hits / total * 100 if total > 0 else 0
        return (f"DRAMStats(acts={self.total_activations}, reads={self.total_reads}, "
                f"writes={self.total_writes}, hit_rate={hit_rate:.1f}%)")


@dataclass
class DecodedAddress:
    """解码后的地址"""
    stack_id: int
    channel_id: int
    pseudo_channel: int
    bank_group: int
    bank: int
    row: int
    col: int


class DRAMModel:
    """完整的 HBM DRAM 模型

    整合 stack、channel、bank 的完整层次结构。
    提供与控制器交互的高层接口。
    """

    def __init__(
        self,
        hbm_version: str = "hbm3",
        stack_count: int = 2,
        banks_per_channel: int = 16,
        rows_per_bank: int = 262144,
        cols_per_row: int = 128,
        bus_width: int = 64,
        burst_length: int = 4,
    ):
        """初始化 DRAM 模型

        Args:
            hbm_version: HBM 版本 ("hbm2", "hbm3", "hbm4")
            stack_count: Stack 数量
            banks_per_channel: 每个 channel 的 bank 数量 (HBM3 = 16)
            rows_per_bank: 每个 bank 的行数
            cols_per_row: 每行的列数
            bus_width: 数据总线宽度 (bits)
            burst_length: 突发长度
        """
        self.hbm_version = hbm_version
        self.config = {
            'stack_count': stack_count,
            'channels_per_stack': 8,
            'banks_per_channel': banks_per_channel,
            'rows_per_bank': rows_per_bank,
            'cols_per_row': cols_per_row,
            'bus_width': bus_width,
            'burst_length': burst_length,
        }

        # 时序参数
        self.timing = get_timing_for_hbm_version(hbm_version)

        # 创建 Stack 模型
        # HBM3: 每个 stack 8 channels, 每 channel 2 pseudo-channels,
        #        每 pseudo-channel 8 bank groups, 每 group 2 banks = 16 banks/channel
        self.stacks: List[Stack] = []
        for i in range(stack_count):
            stack = Stack(stack_id=i, num_channels=8)
            self.stacks.append(stack)

        # 统计
        self.stats = DRAMStats()

        # 内存 (可选的完整内存模型)
        self._memory: Optional[Dict] = None
        self._enable_memory = False

    @property
    def total_banks(self) -> int:
        """总 bank 数量"""
        return self.config['stack_count'] * 8 * 16  # 2 * 8 * 16 = 256

    def get_bank(self, stack_id: int, channel_id: int, bank_id: int) -> BankStateMachine:
        """获取指定 bank 的状态机

        Args:
            stack_id: Stack ID
            channel_id: Channel ID
            bank_id: 全局 Bank ID (0-31 per channel in actual impl, 16 per spec)

        Returns:
            BankStateMachine 实例
        """
        if stack_id >= len(self.stacks):
            raise ValueError(f"Invalid stack_id: {stack_id}")

        # Channel 模型: 2 pseudo-channels * 8 bank groups * 2 banks = 32 banks/channel
        # 映射: bank_id -> (ps_id, bg_id, bank_in_group)
        ps_id = bank_id // 16 if bank_id < 32 else 0  # 简化处理
        bank_in_group = bank_id % 2
        bg_id = (bank_id // 2) % 8

        # 实际模型中只有 ps_id=0,1; bg_id=0-7; bank=0,1
        ps_id = bank_id // 16  # 0 或 1
        bank_in_group = bank_id % 2
        bg_id = (bank_id // 2) % 8

        return self.stacks[stack_id].get_bank(channel_id, ps_id, bg_id, bank_in_group)

    def set_time(self, current_time: int):
        """设置当前时间

        Args:
            current_time: 当前时间 (cycles)
        """
        time_s = self.timing.cycles_to_s(current_time)
        for stack in self.stacks:
            stack.set_time(time_s)

    def check_bank_available(
        self,
        stack_id: int,
        channel_id: int,
        bank_id: int,
        current_time: int,
    ) -> Tuple[bool, str]:
        """检查 bank 是否可用

        Args:
            stack_id: Stack ID
            channel_id: Channel ID
            bank_id: Bank ID
            current_time: 当前时间 (cycles)

        Returns:
            (可用, 原因)
        """
        self.set_time(current_time)
        bank = self.get_bank(stack_id, channel_id, bank_id)
        available = bank.can_activate()
        return (available, "" if available else "Bank not available")

    def execute_activate(
        self,
        stack_id: int,
        channel_id: int,
        bank_id: int,
        row_id: int,
        current_time: int,
    ) -> DRAMResponse:
        """执行激活命令

        Args:
            stack_id: Stack ID
            channel_id: Channel ID
            bank_id: Bank ID
            row_id: 行 ID
            current_time: 当前时间 (cycles)

        Returns:
            DRAMResponse
        """
        try:
            self.set_time(current_time)
            bank = self.get_bank(stack_id, channel_id, bank_id)

            success = bank.activate(row_id)

            if success:
                self.stats.add_activation()
                return DRAMResponse(success=True, latency_cycles=self.timing.tRCD)
            else:
                return DRAMResponse(success=False, error="Activation failed")

        except Exception as e:
            return DRAMResponse(success=False, error=str(e))

    def execute_read(
        self,
        stack_id: int,
        channel_id: int,
        bank_id: int,
        col_id: int,
        current_time: int,
        length: int = 32,
    ) -> DRAMResponse:
        """执行读命令

        Args:
            stack_id: Stack ID
            channel_id: Channel ID
            bank_id: Bank ID
            col_id: 列 ID
            current_time: 当前时间 (cycles)
            length: 读数据长度 (bytes)

        Returns:
            DRAMResponse
        """
        try:
            self.set_time(current_time)
            bank = self.get_bank(stack_id, channel_id, bank_id)

            # 检查 bank 状态
            if bank.bank.state != BankStateEnum.ACTIVE:
                return DRAMResponse(success=False, error="Bank not activated")

            # 检查时序
            if not bank.can_read():
                return DRAMResponse(success=False, error="Read timing violation")

            # 读取数据
            data = self._read_memory(stack_id, channel_id, bank_id, bank.bank.open_row, col_id, length)

            # 更新统计
            self.stats.add_read()
            if bank.is_row_hit(col_id):
                self.stats.add_hit()
            else:
                self.stats.add_conflict()

            # 计算延迟 (突发 + tCCD)
            latency = self.timing.tCCD * (length // (self.config['bus_width'] // 8))

            return DRAMResponse(
                success=True,
                data=data,
                latency_cycles=latency,
            )

        except Exception as e:
            return DRAMResponse(success=False, error=str(e))

    def execute_write(
        self,
        stack_id: int,
        channel_id: int,
        bank_id: int,
        col_id: int,
        data: bytes,
        current_time: int,
    ) -> DRAMResponse:
        """执行写命令

        Args:
            stack_id: Stack ID
            channel_id: Channel ID
            bank_id: Bank ID
            col_id: 列 ID
            data: 写数据
            current_time: 当前时间 (cycles)

        Returns:
            DRAMResponse
        """
        try:
            self.set_time(current_time)
            bank = self.get_bank(stack_id, channel_id, bank_id)

            # 检查 bank 状态
            if bank.bank.state != BankStateEnum.ACTIVE:
                return DRAMResponse(success=False, error="Bank not activated")

            # 检查时序
            if not bank.can_write():
                return DRAMResponse(success=False, error="Write timing violation")

            # 写入数据
            self._write_memory(stack_id, channel_id, bank_id, bank.bank.open_row, col_id, data)

            # 更新统计
            self.stats.add_write()

            return DRAMResponse(success=True, latency_cycles=self.timing.tCCD)

        except Exception as e:
            return DRAMResponse(success=False, error=str(e))

    def execute_precharge(
        self,
        stack_id: int,
        channel_id: int,
        bank_id: int,
        current_time: int,
    ) -> DRAMResponse:
        """执行预充电命令

        Args:
            stack_id: Stack ID
            channel_id: Channel ID
            bank_id: Bank ID
            current_time: 当前时间 (cycles)

        Returns:
            DRAMResponse
        """
        try:
            self.set_time(current_time)
            bank = self.get_bank(stack_id, channel_id, bank_id)

            success = bank.precharge()

            if success:
                self.stats.total_precharges += 1
                return DRAMResponse(success=True, latency_cycles=self.timing.tRP)
            else:
                return DRAMResponse(success=False, error="Precharge failed")

        except Exception as e:
            return DRAMResponse(success=False, error=str(e))

    def execute_refresh(
        self,
        stack_id: int,
        channel_id: int,
        bank_id: int,
        current_time: int,
    ) -> DRAMResponse:
        """执行刷新命令

        Args:
            stack_id: Stack ID
            channel_id: Channel ID
            bank_id: Bank ID
            current_time: 当前时间 (cycles)

        Returns:
            DRAMResponse
        """
        try:
            self.set_time(current_time)
            bank = self.get_bank(stack_id, channel_id, bank_id)

            # 刷新期间 bank 不可用
            self.stats.total_refreshes += 1

            # 简化: 刷新完成后行失效
            bank.bank.state = BankStateEnum.IDLE
            bank.bank.open_row = None
            bank.bank.precharge_time = self.timing.cycles_to_s(current_time)

            return DRAMResponse(success=True, latency_cycles=self.timing.tRFC)

        except Exception as e:
            return DRAMResponse(success=False, error=str(e))

    def tick(self, current_time: int):
        """更新所有 bank 状态

        Args:
            current_time: 当前时间 (cycles)
        """
        self.set_time(current_time)

    def get_utilization(self, window: int = 10000) -> float:
        """计算 bank 利用率

        Args:
            window: 统计窗口 (cycles)

        Returns:
            利用率 (0-1)
        """
        # 简化: 基于激活次数估算
        total_cycles = self.total_banks * window
        busy_cycles = self.stats.total_activations * self.timing.tRAS
        return min(1.0, busy_cycles / total_cycles)

    def _read_memory(
        self,
        stack_id: int,
        channel_id: int,
        bank_id: int,
        row_id: int,
        col_id: int,
        length: int,
    ) -> bytes:
        """读取内存数据 (如果启用)"""
        if not self._enable_memory or self._memory is None:
            # 返回假数据
            return bytes(length)

        key = (stack_id, channel_id, bank_id, row_id)
        if key not in self._memory:
            self._memory[key] = bytearray(self.config['cols_per_row'] * self.config['bus_width'] // 8)

        data = self._memory[key]
        start = col_id * (self.config['bus_width'] // 8)
        return bytes(data[start:start + length])

    def _write_memory(
        self,
        stack_id: int,
        channel_id: int,
        bank_id: int,
        row_id: int,
        col_id: int,
        data: bytes,
    ):
        """写入内存数据 (如果启用)"""
        if not self._enable_memory or self._memory is None:
            return

        key = (stack_id, channel_id, bank_id, row_id)
        if key not in self._memory:
            self._memory[key] = bytearray(self.config['cols_per_row'] * self.config['bus_width'] // 8)

        mem = self._memory[key]
        start = col_id * (self.config['bus_width'] // 8)
        mem[start:start + len(data)] = data

    def enable_memory_model(self):
        """启用完整内存模型"""
        self._enable_memory = True
        self._memory = {}

    def reset(self):
        """重置 DRAM 模型"""
        for stack in self.stacks:
            for ch in stack.channels.channels:
                for ps in ch.pseudo_channels:
                    for bg in ps.bank_groups:
                        for bank in bg.banks:
                            bank.bank.state = BankStateEnum.IDLE
                            bank.bank.open_row = None
        self.stats = DRAMStats()
        if self._memory:
            self._memory = {}

    def __repr__(self) -> str:
        return (f"DRAMModel(v={self.hbm_version}, stacks={len(self.stacks)}, "
                f"channels={self.config['channels_per_stack']}, "
                f"banks={self.config['banks_per_channel']})")


def create_dram_model(config: Dict) -> DRAMModel:
    """从配置创建 DRAM 模型

    Args:
        config: 配置字典

    Returns:
        DRAMModel 实例
    """
    return DRAMModel(
        hbm_version=config.get('hbm_version', 'hbm3'),
        stack_count=config.get('stack_count', 2),
        banks_per_channel=config.get('banks_per_channel', 16),
        rows_per_bank=config.get('rows_per_bank', 262144),
        cols_per_row=config.get('cols_per_row', 128),
        bus_width=config.get('bus_width', 64),
        burst_length=config.get('burst_length', 4),
    )