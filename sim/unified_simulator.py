"""
Unified HBM Simulator with AXI Interconnect

统一仿真器: Traffic Generator -> AXI Interconnect -> Controller -> DRAM

提供完整的系统级仿真能力。
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from sim.interconnect.axi import (
    AXIInterconnect, AXIMaster, AXISlave,
    MultiMasterTrafficGenerator, create_hbm_interconnect
)
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.controller import HBMController
from model.controller.request import HBMRequest
from model.dram.dram_model import DRAMModel
from model.dram.timing import get_timing_for_hbm_version
from sim.simulator import SimulationConfig, SimulationStats, TrafficGenerator, TrafficPattern


logger = logging.getLogger(__name__)


@dataclass
class UnifiedSimulatorStats:
    """统一仿真器统计"""
    total_cycles: int = 0
    total_requests: int = 0
    completed_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0

    # AXI 统计
    axi_ar_transactions: int = 0
    axi_aw_transactions: int = 0
    axi_r_beats: int = 0
    axi_w_beats: int = 0

    # Controller 统计
    row_hits: int = 0
    row_misses: int = 0
    refresh_count: int = 0

    # 延迟统计
    total_latency_cycles: int = 0
    latency_histogram: List[int] = field(default_factory=list)

    # Extended cycle-accurate statistics
    max_latency_cycles: int = 0
    min_latency_cycles: int = 0
    total_dram_activations: int = 0
    total_dram_reads: int = 0
    total_dram_writes: int = 0

    @property
    def avg_latency(self) -> float:
        if self.completed_requests == 0:
            return 0.0
        return self.total_latency_cycles / self.completed_requests

    @property
    def throughput_gbps(self) -> float:
        if self.total_cycles == 0:
            return 0.0
        bytes_transferred = self.completed_requests * 64
        ns_per_cycle = 781.25  # HBM3 tCK
        total_ns = self.total_cycles * ns_per_cycle
        return (bytes_transferred / (total_ns * 1e-9)) / 1e9

    @property
    def bandwidth_efficiency(self) -> float:
        """计算带宽效率 (实际带宽 / 理论峰值)"""
        # HBM3 单 stack 理论峰值: 819.2 GB/s
        peak_bandwidth = 819.2 * 2  # 2 stacks
        actual = self.throughput_gbps
        return actual / peak_bandwidth if peak_bandwidth > 0 else 0.0

    @property
    def row_hit_rate(self) -> float:
        total = self.row_hits + self.row_misses
        if total == 0:
            return 0.0
        return self.row_hits / total

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_cycles': self.total_cycles,
            'total_requests': self.total_requests,
            'completed_requests': self.completed_requests,
            'read_requests': self.read_requests,
            'write_requests': self.write_requests,
            'axi_transactions': {
                'ar': self.axi_ar_transactions,
                'aw': self.axi_aw_transactions,
                'r_beats': self.axi_r_beats,
                'w_beats': self.axi_w_beats,
            },
            'row_hits': self.row_hits,
            'row_misses': self.row_misses,
            'row_hit_rate': self.row_hit_rate,
            'avg_latency': self.avg_latency,
            'max_latency': self.max_latency_cycles,
            'min_latency': self.min_latency_cycles,
            'throughput_gbps': self.throughput_gbps,
            'bandwidth_efficiency': self.bandwidth_efficiency,
            'total_dram_activations': self.total_dram_activations,
        }


class UnifiedSimulator:
    """统一仿真器

    架构: Traffic Generator -> AXI Interconnect -> HBM Controller -> DRAM Model

    Features:
    - 多 master AXI 互联
    - HBM Controller 调度
    - DRAM 时序模拟
    - 统一统计收集
    - Cycle-accurate 统计
    """

    def __init__(
        self,
        sim_config: SimulationConfig,
        num_masters: int = 4,
        enable_axi: bool = True,
    ):
        """初始化统一仿真器

        Args:
            sim_config: 仿真配置
            num_masters: AXI master 数量
            enable_axi: 是否启用 AXI 互联
        """
        self.config = sim_config
        self.enable_axi = enable_axi

        # 时钟配置
        self.clock_freq_hz = sim_config.clock_freq_hz
        self.current_cycle = 0
        self.max_cycles = int(sim_config.simulation_time_us * 1e-6 * sim_config.clock_freq_hz)

        # 时序参数
        self.tCK_ps = 781.25  # HBM3 tCK
        self.timing = get_timing_for_hbm_version("hbm3")

        # 创建流量生成器
        self.traffic_gen = TrafficGenerator(sim_config)

        # 创建 AXI 互联 (可选)
        if enable_axi:
            self.interconnect, self.masters, self.hbm_slave = create_hbm_interconnect(
                num_masters=num_masters,
                enable_qos=True,
            )
        else:
            self.interconnect = None
            self.masters = []
            self.hbm_slave = None

        # 创建 HBM Controller
        self.controller = HBMController(sim_config.hbm_config)

        # 创建 DRAM 模型
        self.dram = DRAMModel(
            hbm_version="hbm3",
            stack_count=sim_config.hbm_config.stack_count,
            banks_per_channel=sim_config.hbm_config.banks_per_pseudo_channel
        )

        # 统计
        self.stats = UnifiedSimulatorStats()

        logger.info(f"UnifiedSimulator initialized: {num_masters} masters, "
                   f"{sim_config.simulation_time_us}us = {self.max_cycles} cycles")

    def _generate_requests(self) -> List[HBMRequest]:
        """从流量生成器生成请求"""
        requests = []

        if self.config.request_rate > 0:
            import random
            if random.random() < self.config.request_rate:
                if self.config.traffic_pattern == TrafficPattern.RANDOM:
                    addr = random.randint(0, self.config.address_range - 1) & ~0x3F
                elif self.config.traffic_pattern == TrafficPattern.SEQUENTIAL:
                    addr = self.traffic_gen.current_addr
                    self.traffic_gen.current_addr = (self.traffic_gen.current_addr + 64) % self.config.address_range
                elif self.config.traffic_pattern == TrafficPattern.STRIDE:
                    addr = self.traffic_gen.current_addr
                    self.traffic_gen.current_addr = (self.traffic_gen.current_addr + self.config.stride_value) % self.config.address_range
                elif self.config.traffic_pattern == TrafficPattern.HOT_SPOT:
                    if random.random() < 0.8:
                        addr = random.randint(0, self.config.address_range // 10) & ~0x3F
                    else:
                        addr = random.randint(0, self.config.address_range - 1) & ~0x3F
                else:
                    addr = random.randint(0, self.config.address_range - 1) & ~0x3F

                is_read = random.random() < self.config.read_ratio
                req = HBMRequest(addr=addr, length=self.config.burst_size, is_read=is_read)
                requests.append(req)

        return requests

    def step(self) -> Optional[Dict]:
        """执行一个周期

        Returns:
            如果有请求完成，返回完成信息
        """
        self.current_cycle += 1

        # 1. 生成新请求
        new_requests = self._generate_requests()
        for req in new_requests:
            self.controller.submit_request(req)
            self.stats.total_requests += 1
            if req.is_read:
                self.stats.read_requests += 1
            else:
                self.stats.write_requests += 1

        # 2. AXI 互联处理 (如果启用)
        if self.enable_axi and self.interconnect:
            self.interconnect.tick(self.current_cycle)

            # 更新 AXI 统计
            axi_stats = self.interconnect.get_stats()
            self.stats.axi_ar_transactions += axi_stats['interconnect'].get('ar_transactions', 0)
            self.stats.axi_aw_transactions += axi_stats['interconnect'].get('aw_transactions', 0)
            self.stats.axi_r_beats += axi_stats['interconnect'].get('r_beats', 0)
            self.stats.axi_w_beats += axi_stats['interconnect'].get('w_beats', 0)

        # 3. Controller 处理
        response = self.controller.tick()

        if response:
            self.stats.completed_requests += 1
            # latency 是纳秒，转换为 cycles
            latency_ns = response.latency if hasattr(response, 'latency') else 0.0
            latency_cycles = int(latency_ns / 0.78125) if latency_ns > 0 else 0
            self.stats.total_latency_cycles += latency_cycles

            # Track max/min latency
            if self.stats.max_latency_cycles == 0 or latency_cycles > self.stats.max_latency_cycles:
                self.stats.max_latency_cycles = latency_cycles
            if self.stats.min_latency_cycles == 0 or latency_cycles < self.stats.min_latency_cycles:
                self.stats.min_latency_cycles = latency_cycles

            if len(self.stats.latency_histogram) < 1000:
                self.stats.latency_histogram.append(latency_cycles)

        # 4. DRAM tick
        self.dram.tick(self.current_cycle)

        # 5. Update DRAM statistics
        dram_stats = self.dram.stats
        self.stats.row_hits = dram_stats.row_hits
        self.stats.row_misses = dram_stats.row_misses
        self.stats.refresh_count = dram_stats.total_refreshes
        self.stats.total_dram_activations = dram_stats.total_activations
        self.stats.total_dram_reads = dram_stats.total_reads
        self.stats.total_dram_writes = dram_stats.total_writes

        return response

    def run(self) -> UnifiedSimulatorStats:
        """运行完整仿真"""
        logger.info(f"Starting unified simulation: {self.max_cycles} cycles")

        while self.current_cycle < self.max_cycles:
            self.step()

        self.stats.total_cycles = self.current_cycle
        logger.info(f"Unified simulation completed: {self.stats.completed_requests} requests")

        return self.stats

    def get_stats(self) -> UnifiedSimulatorStats:
        """获取统计信息"""
        self.stats.total_cycles = self.current_cycle
        return self.stats


def run_unified_simulation(
    simulation_time_us: float = 100.0,
    traffic_pattern: TrafficPattern = TrafficPattern.RANDOM,
    request_rate: float = 0.5,
    num_masters: int = 4,
    enable_axi: bool = True,
    seed: Optional[int] = None,
) -> UnifiedSimulatorStats:
    """运行统一仿真的快捷函数"""
    config = SimulationConfig(
        simulation_time_us=simulation_time_us,
        traffic_pattern=traffic_pattern,
        request_rate=request_rate,
        read_ratio=0.7,
        seed=seed,
    )

    sim = UnifiedSimulator(
        sim_config=config,
        num_masters=num_masters,
        enable_axi=enable_axi,
    )

    return sim.run()


if __name__ == "__main__":
    print("=" * 60)
    print("Unified HBM Simulator with AXI Interconnect")
    print("=" * 60)

    # 测试统一仿真器
    print("\n--- Unified Simulation (100us Random Traffic, 4 Masters) ---")
    stats = run_unified_simulation(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        num_masters=4,
        seed=42,
    )

    print(f"\nResults:")
    print(f"  Total cycles: {stats.total_cycles}")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Completed: {stats.completed_requests}")
    print(f"  Read/Write: {stats.read_requests}/{stats.write_requests}")
    print(f"  Avg latency: {stats.avg_latency:.1f} cycles")
    print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
    print(f"  AXI AR: {stats.axi_ar_transactions}")
    print(f"  AXI AW: {stats.axi_aw_transactions}")

    # 测试无 AXI 模式
    print("\n--- Without AXI Interconnect ---")
    stats_no_axi = run_unified_simulation(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.5,
        enable_axi=False,
        seed=42,
    )

    print(f"  Completed: {stats_no_axi.completed_requests}")
    print(f"  Throughput: {stats_no_axi.throughput_gbps:.2f} GB/s")

    print("\n" + "=" * 60)
    print("Unified simulation complete!")