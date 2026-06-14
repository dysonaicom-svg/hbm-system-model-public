"""
HBM3 DRAM Timing Parameters
参考设计文档 2026-06-15-hbm-system-model-design.md 的 5.2.4 节

HBM3 时序参数定义
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class HBM3Timing:
    """HBM3 时序参数
    
    所有参数以 cycles 为单位，基于 tCK = 781 ps (1.28 GHz)
    
    时序约束:
    - tRCD: RAS to CAS delay (激活行到可以发起读写)
    - tRP: Precharge time (关闭行的时间)
    - tRAS: Active to precharge (行打开的最短时间)
    - tRC: Row cycle (连续激活同一 bank 的最小间隔)
    - tCCD: CAS to CAS (连续突发最小间隔)
    - tRRD: Rank row to rank delay (不同 bank 激活间隔)
    - tFAW: Four bank activation window (4 个 bank 激活的时间窗口)
    - tRFC: Refresh cycle (刷新一个 bank group 的时间)
    - tREFI: Refresh interval (刷新间隔)
    """
    
    # 时钟周期 (ps)
    tCK_ps: float = 781.25  # 1.28 GHz
    tCK_cycles: int = 1
    
    # 时序参数 (cycles)
    tRCD: int = 17       # RAS to CAS delay
    tRP: int = 17        # Precharge time
    tRAS: int = 42       # Active to precharge minimum
    tRC: int = 59        # Row cycle time
    tCCD: int = 5        # CAS to CAS delay
    tRRD: int = 5        # Rank row to rank delay
    tFAW: int = 26       # Four bank activation window
    tRFC: int = 295      # Refresh cycle (16Gb)
    tREFI: int = 5000    # Refresh interval (cycles)
    
    # Data timing
    tDQSCK: int = 3      # DQS output access time from CK
    tDQSQ: int = 2       # DQS-DQ skew
    tQHS: int = 2        # DQ hold DQS
    
    # Command timing
    tCMD: int = 1        # Command period
    
    @property
    def clock_freq(self) -> float:
        """时钟频率 (Hz)"""
        return 1e12 / self.tCK_ps
    
    @property
    def clock_period_ns(self) -> float:
        """时钟周期 (ns)"""
        return self.tCK_ps / 1000.0
    
    def cycles_to_ns(self, cycles: int) -> float:
        """Cycles 转换为 ns"""
        return cycles * self.clock_period_ns

    def cycles_to_seconds(self, cycles: int) -> float:
        """Cycles 转换为 seconds"""
        return self.cycles_to_ns(cycles) * 1e-9

    def cycles_to_s(self, cycles: int) -> float:
        """Cycles 转换为 seconds"""
        return self.cycles_to_seconds(cycles)

    def cycles_to_s(self, cycles: int) -> float:
        """Cycles 转换为秒"""
        return cycles * self.clock_period_ns * 1e-9

    def ns_to_cycles(self, ns: float) -> int:
        """ns 转换为 cycles"""
        return int(ns * 1000 / self.tCK_ps + 0.5)
    
    def __repr__(self) -> str:
        return (f"HBM3Timing(tCK={self.tCK_ps}ps, "
                f"tRCD={self.tRCD}, tRP={self.tRP}, tRAS={self.tRAS})")


# HBM2 时序参数 (对比参考)
@dataclass
class HBM2Timing:
    """HBM2 时序参数 (参考)"""
    tCK_ps: float = 1250.0  # 800 MHz
    tRCD: int = 14
    tRP: int = 14
    tRAS: int = 34
    tRC: int = 48
    tCCD: int = 4
    tRRD: int = 4
    tFAW: int = 20
    tRFC: int = 160  # 8Gb
    tREFI: int = 7800
    
    @property
    def clock_freq(self) -> float:
        return 1e12 / self.tCK_ps
    
    @property
    def clock_period_ns(self) -> float:
        return self.tCK_ps / 1000.0

    def cycles_to_ns(self, cycles: int) -> float:
        return cycles * self.clock_period_ns

    def cycles_to_seconds(self, cycles: int) -> float:
        return self.cycles_to_ns(cycles) * 1e-9

    def cycles_to_s(self, cycles: int) -> float:
        return self.cycles_to_seconds(cycles)
    
    def cycles_to_ns(self, cycles: int) -> float:
        return cycles * self.clock_period_ns

    def cycles_to_seconds(self, cycles: int) -> float:
        return self.cycles_to_ns(cycles) * 1e-9

    def cycles_to_s(self, cycles: int) -> float:
        return self.cycles_to_seconds(cycles)


@dataclass
class HBM4Timing:
    """HBM4 时序参数 (计划值)"""
    tCK_ps: float = 625.0  # 1.6 GHz (预估)
    tRCD: int = 20  # 预估
    tRP: int = 20
    tRAS: int = 48
    tRC: int = 68
    tCCD: int = 6
    tRRD: int = 6
    tFAW: int = 30
    tRFC: int = 350  # 预估
    tREFI: int = 5000
    
    @property
    def clock_freq(self) -> float:
        return 1e12 / self.tCK_ps
    
    @property
    def clock_period_ns(self) -> float:
        return self.tCK_ps / 1000.0


def get_timing_for_hbm_version(version: str):
    """获取指定 HBM 版本的时序参数
    
    Args:
        version: "hbm2", "hbm3", "hbm4"
        
    Returns:
        对应版本的时序参数
    """
    versions = {
        "hbm2": HBM2Timing,
        "hbm3": HBM3Timing,
        "hbm4": HBM4Timing,
    }
    timing_class = versions.get(version.lower())
    if not timing_class:
        raise ValueError(f"Unknown HBM version: {version}")
    return timing_class()


def timing_to_cycles(timing: HBM3Timing, time_ns: float) -> int:
    """将时间(ns)转换为周期数"""
    return int(time_ns * 1000 / timing.tCK_ps + 0.5)
