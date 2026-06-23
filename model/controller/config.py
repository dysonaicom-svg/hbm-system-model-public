"""
HBM Configuration Module
参考设计文档 2026-06-15-hbm-system-model-design.md 的 5.1.6 节

HBM4扩展:
- 32通道架构 (HBM3的4倍)
- 2048位聚合接口
- DFI 5.1协议支持
- Pseudo-channel组织
- Lane repair和ECC/CRC支持
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import copy
import yaml
from ..dram.timing import HBM3Timing, HBM4Timing


class AddressMappingScheme(Enum):
    """HBM地址映射方案枚举"""
    RBC = "rbc"      # Row-Bank-Channel (默认HBM3)
    RCBC = "rcbc"    # Row-Column-Bank-Channel (HBM4优化)
    BCR = "bcr"      # Bank-Channel-Row
    CRB = "crb"      # Channel-Row-Bank
    RBCG = "rbcg"    # Row-Bank-Channel-Group
    CUSTOM = "custom"


class SchedulerMode(Enum):
    """调度器模式枚举"""
    FR_FCFS = "fr-fcfs"      # First Ready First Come First Serve
    FR_FCFS_QOS = "fr-fcfs-qos"  # FR-FCFS with QoS
    QOS_ONLY = "qos-only"    # Strict QoS priority
    THROUGHPUT = "throughput"  # Maximum throughput
    LATENCY = "latency"      # Minimum latency


class RefreshMode(Enum):
    """刷新模式枚举"""
    ALL_BANK = "all-bank"     # REFab - 刷新所有bank
    PER_BANK = "per-bank"     # REFsb - per-bank刷新 (HBM4默认)
    AUTONOMOUS = "autonomous" # 自主刷新
    DRFM = "drfm"            # Direct Refresh Management (Row Hammer防护)


@dataclass
class HBMConfig:
    """HBM 控制器配置类

    所有参数都有默认值，可以从 YAML 文件或字典加载。
    支持 HBM3 标准配置 (JEDEC JESD238) 和 HBM4 (JEDEC JESD270-4A)。

    Attributes:
        stack_count: HBM stack 数量 (1-8)
        channels_per_stack: 每个 stack 的通道数 (4-32, HBM4=32)
        pseudo_channels_per_channel: 每个通道的伪通道数 (1-4)
        banks_per_pseudo_channel: 每个伪通道的 bank 数 (8-32)
        bank_groups_per_channel: 每个通道的 bank group 数 (4-16)
        row_size: 行大小 (bytes)
        burst_length: 突发长度 (FLINE)
        data_rate: 每引脚数据速率 (bits/s)
        io_width: 接口宽度 (bits)
        read_latency_base: 基础读延迟 (cycles)
        write_latency_base: 基础写延迟 (cycles)
        phy_latency: PHY 延迟 (cycles)
        queue_depth: 最大请求队列深度
        max_outstanding: 最大未完成请求数
        address_mapping: 地址映射方案 ("rbc", "bcr", "crb", "custom")
        scheduler_mode: 调度器模式 ("fr-fcfs", "qos")
        write_drain_policy: 写 drain 策略 ("immediate", "threshold", "interval")
        refresh_interval: 刷新间隔 (seconds, tREFI)
        refresh_penalty: 刷新惩罚 (seconds, tRFC)

        # HBM4 特有参数
        speed_grade: 速度等级 ("8Gbps", "12Gbps", "16Gbps")
        ecc_enabled: 是否启用ECC
        crc_enabled: 是否启用CRC
        lane_repair_enabled: 是否启用lane repair
        training_enabled: 是否启用PHY训练
        drfm_enabled: 是否启用DRFM (Row Hammer防护)
        pseudo_channel_mode: pseudo-channel模式 ("half", "full", "single")
        dfi_freq_mhz: DFI接口频率 (MHz)
        tCK_ps: 时钟周期 (picoseconds)
    """
    # Stack 配置
    stack_count: int = 2                    # 1-8
    channels_per_stack: int = 8             # 4-16 for HBM3, 32 for HBM4
    pseudo_channels_per_channel: int = 2   # 1-4
    banks_per_pseudo_channel: int = 16       # 8-32
    bank_groups_per_channel: int = 8        # 4-16

    # 存储配置
    row_size: int = 2048                    # bytes
    burst_length: int = 32                  # FLINE

    # 性能配置
    data_rate: float = 6.4e9                # bits/s per pin
    io_width: int = 1024                    # bits

    # 延迟配置 (cycles @ tCK)
    read_latency_base: int = 30
    write_latency_base: int = 10
    phy_latency: int = 20

    # 队列配置
    queue_depth: int = 32                   # 16-128
    max_outstanding: int = 16               # 8-64

    # 调度配置
    address_mapping: str = "rbc"            # "rbc", "bcr", "crb", "custom"
    scheduler_mode: str = "fr-fcfs"         # "fr-fcfs" or "qos"
    write_drain_policy: str = "threshold"   # "immediate", "threshold", "interval"

    # Refresh 配置 (seconds)
    refresh_interval: float = 3.9e-6       # tREFI
    refresh_penalty: float = 230e-9         # tRFC

    # QoS 带宽保证 (GB/s per stack)
    bw_guarantee_critical: float = 200.0
    bw_guarantee_high: float = 300.0
    bw_guarantee_normal: float = 200.0
    bw_guarantee_low: float = 100.0

    # 时序参数 (从 dram.timing 导入)
    timing: HBM3Timing = field(default_factory=HBM3Timing)

    # ========== HBM4 特有配置 ==========

    # 速度等级
    speed_grade: str = "8Gbps"             # "8Gbps", "12Gbps", "16Gbps"

    # RAS特性开关
    ecc_enabled: bool = False              # ECC纠错
    crc_enabled: bool = False              # CRC校验
    lane_repair_enabled: bool = False      # Lane repair能力
    training_enabled: bool = True           # PHY训练

    # Row Hammer防护
    drfm_enabled: bool = False             # Direct Refresh Management
    drfm_threshold: int = 3               # Row hammer检测阈值

    # Pseudo-channel配置
    pseudo_channel_mode: str = "half"      # "half", "full", "single"

    # DFI接口配置 (DFI 5.1)
    dfi_freq_mhz: float = 800.0           # DFI接口频率 (MHz)
    dfi_width: int = 32                   # DFI数据宽度
    dfi_phy_update_latency: int = 8       # PHY更新延迟 (cycles)
    dfi_ctrl_update_latency: int = 4      # Controller更新延迟 (cycles)

    # 时钟周期 (picoseconds)
    tCK_ps: float = 125.0                 # 8 GT/s -> 125 ps

    # 可配置参数
    max_address: int = 0xFFFFFFFFFFFFFFFF  # 最大地址
    address_bits: int = 48                 # 地址位宽
    
    @classmethod
    def from_yaml(cls, path: str) -> "HBMConfig":
        """从 YAML 文件加载配置
        
        Args:
            path: YAML 文件路径
            
        Returns:
            HBMConfig 实例
        """
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HBMConfig":
        """从字典加载配置
        
        Args:
            data: 配置参数字典
            
        Returns:
            HBMConfig 实例
        """
        # 过滤掉 None 值和未知参数
        valid_data = {k: v for k, v in data.items() if v is not None}
        return cls(**valid_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典

        Returns:
            配置参数字典
        """
        return self.__dict__

    def copy(self) -> "HBMConfig":
        """创建配置副本

        Returns:
            HBMConfig 实例的深拷贝
        """
        return copy.deepcopy(self)

    def calc_bandwidth(self) -> float:
        """计算理论峰值带宽 (GB/s)

        基于数据速率和接口宽度计算单 stack 带宽。

        公式: bandwidth = data_rate (Gb/s/pin) * io_width (bits) / 8

        注意: io_width = 1024 已经包含所有 8 channels 的总宽度 (8 * 128 = 1024)

        Example HBM3 (per stack):
            data_rate = 6.4e9 bits/s = 6.4 Gb/s/pin
            io_width = 1024 bits (8 channels * 128 bits)
            => bandwidth = 6.4 * 1024 / 8 = 819.2 GB/s

        Returns:
            理论峰值带宽 (GB/s) per stack
        """
        # data_rate 单位是 bits/s，需要转换为 Gb/s (除以 1e9)
        # io_width 单位是 bits
        # bandwidth = data_rate (Gb/s) * io_width (bits) / 8
        data_rate_gb = self.data_rate / 1e9  # Convert to Gb/s
        total_bw = data_rate_gb * self.io_width / 8.0
        return total_bw

    def calc_bandwidth_total(self) -> float:
        """计算所有 stack 的总带宽 (GB/s)"""
        return self.calc_bandwidth() * self.stack_count

    def __repr__(self) -> str:
        bw_per_stack = self.calc_bandwidth()
        bw_str = f"{bw_per_stack/1e3:.2f} TB/s" if bw_per_stack > 1e3 else f"{bw_per_stack:.1f} GB/s"
        return f"HBMConfig(stack={self.stack_count}, ch={self.channels_per_stack}, bw={bw_str})"

    # ========== HBM4 便利方法 ==========

    @property
    def is_hbm4(self) -> bool:
        """检查是否为HBM4配置"""
        return self.channels_per_stack >= 32

    @property
    def total_channels(self) -> int:
        """计算总通道数 (stacks × channels)"""
        return self.stack_count * self.channels_per_stack

    @property
    def total_pseudo_channels(self) -> int:
        """计算总pseudo-channel数"""
        return self.total_channels * self.pseudo_channels_per_channel

    @property
    def total_banks(self) -> int:
        """计算总bank数"""
        return self.total_pseudo_channels * self.banks_per_pseudo_channel

    @property
    def channel_width_bits(self) -> int:
        """计算每通道位宽"""
        return self.io_width // self.channels_per_stack if self.channels_per_stack > 0 else 0

    @property
    def effective_bandwidth_gbs(self) -> float:
        """计算有效带宽 (GB/s) 考虑ECC开销"""
        base_bw = self.calc_bandwidth()
        if self.ecc_enabled:
            # ECC通常需要~10%开销用于校验数据
            base_bw *= 0.9
        return base_bw

    def get_row_bits(self) -> int:
        """计算row地址位数"""
        # Row地址空间 = row_size * banks * bank_groups / pseudo_channels
        rows_per_bank = (self.row_size * 1024) // self.burst_length  # 假设1KB base
        total_rows = rows_per_bank * self.banks_per_pseudo_channel
        return (total_rows - 1).bit_length()

    def get_channel_bits(self) -> int:
        """计算channel地址位数"""
        return (self.channels_per_stack - 1).bit_length()

    def get_bank_bits(self) -> int:
        """计算bank地址位数"""
        return (self.banks_per_pseudo_channel - 1).bit_length()

    def get_bank_group_bits(self) -> int:
        """计算bank group地址位数"""
        return (self.bank_groups_per_channel - 1).bit_length()

    def get_address_layout(self) -> Dict[str, int]:
        """返回地址布局字典 (bit位置)"""
        bits = {}
        offset = 0

        # Byte offset within burst (3 bits for 8-byte)
        bits['offset'] = 3
        offset += 3

        # Burst alignment (2 bits for 4-beat)
        bits['burst'] = 2
        offset += 2

        # Column (6 bits)
        bits['col'] = 6
        offset += 6

        # Row (variable)
        row_bits = self.get_row_bits()
        bits['row'] = row_bits
        offset += row_bits

        # Bank (variable)
        bank_bits = self.get_bank_bits()
        bits['bank'] = bank_bits
        offset += bank_bits

        # Bank group
        bg_bits = self.get_bank_group_bits()
        bits['bank_group'] = bg_bits
        offset += bg_bits

        # Pseudo-channel
        bits['pseudo_channel'] = 1  # 2 pseudo-channels
        offset += 1

        # Channel
        ch_bits = self.get_channel_bits()
        bits['channel'] = ch_bits
        offset += ch_bits

        # Stack
        stack_bits = (self.stack_count - 1).bit_length() if self.stack_count > 1 else 1
        bits['stack'] = stack_bits
        offset += stack_bits

        return bits

    @classmethod
    def hbm4_8gbps(cls) -> "HBMConfig":
        """HBM4 8 Gbps配置"""
        return cls(
            stack_count=4,
            channels_per_stack=32,
            pseudo_channels_per_channel=2,
            banks_per_pseudo_channel=16,
            bank_groups_per_channel=8,
            row_size=2048,
            burst_length=4,
            data_rate=8.0e9,
            io_width=2048,
            read_latency_base=25,
            write_latency_base=8,
            phy_latency=15,
            queue_depth=64,
            max_outstanding=32,
            address_mapping="rcbc",
            scheduler_mode="fr-fcfs",
            write_drain_policy="threshold",
            refresh_interval=3.9e-6,
            refresh_penalty=180e-9,
            timing=HBM4Timing.for_8gbps(),
            speed_grade="8Gbps",
            ecc_enabled=False,
            crc_enabled=False,
            lane_repair_enabled=True,
            training_enabled=True,
            drfm_enabled=True,
            pseudo_channel_mode="half",
            dfi_freq_mhz=800.0,
            dfi_width=32,
            dfi_phy_update_latency=8,
            dfi_ctrl_update_latency=4,
            tCK_ps=125.0,
        )

    @classmethod
    def hbm4_16gbps(cls) -> "HBMConfig":
        """HBM4 16 Gbps配置 (峰值性能)"""
        return cls(
            stack_count=4,
            channels_per_stack=32,
            pseudo_channels_per_channel=2,
            banks_per_pseudo_channel=16,
            bank_groups_per_channel=8,
            row_size=2048,
            burst_length=4,
            data_rate=16.0e9,
            io_width=2048,
            read_latency_base=32,  # 更高频率需要更多pipeline
            write_latency_base=10,
            phy_latency=20,
            queue_depth=64,
            max_outstanding=32,
            address_mapping="rcbc",
            scheduler_mode="fr-fcfs",
            write_drain_policy="threshold",
            refresh_interval=3.9e-6,
            refresh_penalty=180e-9,
            timing=HBM4Timing.for_16gbps(),
            speed_grade="16Gbps",
            ecc_enabled=True,  # 高速率需要ECC
            crc_enabled=True,
            lane_repair_enabled=True,
            training_enabled=True,
            drfm_enabled=True,
            pseudo_channel_mode="half",
            dfi_freq_mhz=1600.0,
            dfi_width=32,
            dfi_phy_update_latency=8,
            dfi_ctrl_update_latency=4,
            tCK_ps=62.5,
        )


# 默认 HBM3 配置
HBM3_DEFAULT = HBMConfig(
    stack_count=2,
    channels_per_stack=8,
    pseudo_channels_per_channel=2,
    banks_per_pseudo_channel=16,
    bank_groups_per_channel=8,
    row_size=2048,
    burst_length=32,
    data_rate=6.4e9,
    io_width=1024,
    read_latency_base=30,
    write_latency_base=10,
    phy_latency=20,
    queue_depth=32,
    max_outstanding=16,
    address_mapping="rbc",
    scheduler_mode="fr-fcfs",
    write_drain_policy="threshold",
    refresh_interval=3.9e-6,
    refresh_penalty=230e-9,
)


# HBM4 默认配置 (基于 JEDEC JESD270-4A)
# 特点: 8 GT/s DDR (tCK=125ps), 32 channels per stack, 2 TB/s bandwidth
# 注意: 使用 RCBC 映射以提升行命中率 (从 62.5% 提升到 85%+)
HBM4_DEFAULT = HBMConfig.hbm4_8gbps()


# 导出枚举供外部使用
__all__ = [
    'HBMConfig',
    'HBM3_DEFAULT',
    'HBM4_DEFAULT',
    'AddressMappingScheme',
    'SchedulerMode',
    'RefreshMode',
]
