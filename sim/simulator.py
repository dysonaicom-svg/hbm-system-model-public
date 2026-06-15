"""
HBM System Simulation Framework
端到端仿真框架 - 集成控制器、DRAM 模型和流量生成器
"""

import time
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

from model.dram.dram_model import DRAMModel, create_dram_model
from model.dram.timing import HBM3Timing, HBM3Timing
from model.controller.controller import HBMController
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.request import HBMRequest


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrafficPattern(Enum):
    """流量模式"""
    RANDOM = "random"
    SEQUENTIAL = "sequential"
    STRIDE = "stride"
    HOT_SPOT = "hot_spot"
    ADDR_SCATTER = "scatter"


@dataclass
class SimulationConfig:
    """仿真配置"""
    # 时钟配置
    clock_freq_hz: float = 1.28e9  # 1.28 GHz
    simulation_time_us: float = 100.0  # 仿真时间 (微秒)

    # 流量配置
    traffic_pattern: TrafficPattern = TrafficPattern.RANDOM
    request_rate: float = 0.5  # 请求率 (0-1)
    read_ratio: float = 0.7  # 读请求比例
    burst_size: int = 64  # 突发大小

    # 地址配置
    address_range: int = 0x100_0000  # 地址范围
    stride_value: int = 4096  # stride 模式步长

    # HBM 配置
    hbm_config: HBMConfig = field(default_factory=lambda: HBM3_DEFAULT)

    # 仿真选项
    enable_logging: bool = False
    enable_stats: bool = True
    seed: Optional[int] = None  # 随机种子


@dataclass
class SimulationStats:
    """仿真统计"""
    total_cycles: int = 0
    total_requests: int = 0
    completed_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0
    total_latency_cycles: int = 0
    refresh_count: int = 0

    @property
    def avg_latency(self) -> float:
        if self.completed_requests == 0:
            return 0.0
        return self.total_latency_cycles / self.completed_requests

    @property
    def row_hit_rate(self) -> float:
        total = self.row_hits + self.row_misses + self.row_conflicts
        if total == 0:
            return 0.0
        return self.row_hits / total

    @property
    def throughput_gbps(self) -> float:
        if self.total_cycles == 0:
            return 0.0
        # HBM3 突发长度 32 bytes, 每个请求 4 个突发
        bytes_transferred = self.completed_requests * 32 * 4
        ns_per_cycle = 781.25  # HBM3 tCK
        total_ns = self.total_cycles * ns_per_cycle
        return (bytes_transferred / (total_ns * 1e-9)) / 1e9


class TrafficGenerator:
    """流量生成器"""

    def __init__(self, config: SimulationConfig):
        self.config = config
        if config.seed is not None:
            random.seed(config.seed)
        self.current_addr = 0
        self.hot_bank = 0

    def generate(self) -> List[HBMRequest]:
        """生成请求批次"""
        requests = []

        # 根据请求率决定是否生成请求
        if random.random() > self.config.request_rate:
            return requests

        # 根据模式生成地址
        if self.config.traffic_pattern == TrafficPattern.RANDOM:
            addr = random.randint(0, self.config.address_range - 1)
        elif self.config.traffic_pattern == TrafficPattern.SEQUENTIAL:
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.burst_size) % self.config.address_range
        elif self.config.traffic_pattern == TrafficPattern.STRIDE:
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.stride_value) % self.config.address_range
        elif self.config.traffic_pattern == TrafficPattern.HOT_SPOT:
            if random.random() < 0.8:  # 80% 访问热点
                addr = random.randint(0, self.config.address_range // 10)
            else:
                addr = random.randint(0, self.config.address_range - 1)
        else:  # ADDR_SCATTER
            addr = random.randint(0, self.config.address_range - 1)

        # 对齐地址
        addr = addr & ~0x3F  # 64 字节对齐

        # 生成读或写请求
        is_read = random.random() < self.config.read_ratio
        req = HBMRequest(addr=addr, length=self.config.burst_size, is_read=is_read)
        requests.append(req)

        return requests


class HBMSimulator:
    """HBM 仿真器"""

    def __init__(self, sim_config: SimulationConfig):
        self.config = sim_config

        # 创建 DRAM 模型
        self.dram = DRAMModel(
            hbm_version="hbm3",
            stack_count=sim_config.hbm_config.stack_count,
            banks_per_channel=sim_config.hbm_config.banks_per_pseudo_channel
        )

        # 创建控制器
        self.controller = HBMController(sim_config.hbm_config)

        # 创建流量生成器
        self.traffic_gen = TrafficGenerator(sim_config)

        # 统计
        self.stats = SimulationStats()

        # 仿真状态
        self.current_cycle = 0
        self.max_cycles = int(sim_config.simulation_time_us * 1e-6 * sim_config.clock_freq_hz)

        logger.info(f"Simulator initialized: {sim_config.simulation_time_us}us = {self.max_cycles} cycles")

    def step(self) -> Optional[HBMRequest]:
        """执行一个周期"""
        self.current_cycle += 1

        # 1. 生成新请求
        new_requests = self.traffic_gen.generate()
        for req in new_requests:
            self.controller.submit_request(req)
            self.stats.total_requests += 1
            if req.is_read:
                self.stats.read_requests += 1
            else:
                self.stats.write_requests += 1

        # 2. 控制器处理
        response = self.controller.tick()

        if response:
            self.stats.completed_requests += 1
            # latency 是纳秒，转换为 cycles (1 cycle = 781.25 ps)
            latency_ns = response.latency if hasattr(response, 'latency') else 0.0
            latency_cycles = int(latency_ns / 0.78125)
            self.stats.total_latency_cycles += latency_cycles

        # 3. 更新统计
        drams_stats = self.dram.stats
        self.stats.row_hits = drams_stats.row_hits
        self.stats.row_misses = drams_stats.row_misses
        self.stats.row_conflicts = drams_stats.row_conflicts

        return response

    def run(self) -> SimulationStats:
        """运行仿真"""
        logger.info(f"Starting simulation: {self.max_cycles} cycles")
        start_time = time.time()

        completed_prev = 0

        while self.current_cycle < self.max_cycles:
            response = self.step()

            # 定期打印进度
            if self.current_cycle % (self.max_cycles // 10) == 0:
                elapsed = time.time() - start_time
                rate = (self.stats.completed_requests - completed_prev) / max(elapsed, 0.001)
                logger.info(f"  Cycle {self.current_cycle}/{self.max_cycles}: "
                           f"{self.stats.completed_requests} completed, {rate:.0f} req/s")
                completed_prev = self.stats.completed_requests

        self.stats.total_cycles = self.current_cycle

        elapsed = time.time() - start_time
        logger.info(f"Simulation completed in {elapsed:.2f}s")

        return self.stats

    def get_stats(self) -> SimulationStats:
        """获取统计信息"""
        self.stats.total_cycles = self.current_cycle
        self.stats.row_hits = self.dram.stats.row_hits
        self.stats.row_misses = self.dram.stats.row_misses
        self.stats.row_conflicts = self.dram.stats.row_conflicts
        return self.stats


def run_simulation(config: SimulationConfig = None) -> SimulationStats:
    """运行仿真快捷函数"""
    if config is None:
        config = SimulationConfig()

    sim = HBMSimulator(config)
    return sim.run()


if __name__ == "__main__":
    print("=" * 60)
    print("HBM System Simulation")
    print("=" * 60)

    # 基本仿真
    print("\n--- Basic Simulation (100us Random Traffic) ---")
    config = SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.3,
        read_ratio=0.7,
    )
    stats = run_simulation(config)

    print(f"\nResults:")
    print(f"  Total cycles: {stats.total_cycles}")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Completed: {stats.completed_requests}")
    print(f"  Read/Write: {stats.read_requests}/{stats.write_requests}")
    print(f"  Row hit rate: {stats.row_hit_rate:.2%}")
    print(f"  Avg latency: {stats.avg_latency:.1f} cycles")
    print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")

    # Sequential 流量测试
    print("\n--- Sequential Traffic ---")
    config_seq = SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.5,
        read_ratio=1.0,
    )
    stats_seq = run_simulation(config_seq)
    print(f"  Row hit rate: {stats_seq.row_hit_rate:.2%}")
    print(f"  Throughput: {stats_seq.throughput_gbps:.2f} GB/s")

    print("\n" + "=" * 60)
    print("Simulation complete!")