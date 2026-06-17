"""
Unified HBM Simulator with AXI Interconnect

统一仿真器: Traffic Generator -> AXI Interconnect -> Controller -> DRAM

提供完整的系统级仿真能力。

HBM4 Enhancements:
- HBM4LogicBaseDie: 统一控制器模型
- PAM3 Signal Model: 3级信号编码
- Independent Channel Timing: 独立通道时序
- DFI 5.0 Interface: 标准协议接口
- ECC/Lane Repair: 错误纠正和冗余修复
- HBM4-specific Benchmark Metrics
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Tuple
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

# RTL Co-simulation interface
from sim.rtl_interface import (
    RTLInterface,
    CoSimConfig,
    CoSimStats,
    ResultComparator,
    create_rtl_interface,
    TransactionType,
)

# HBM4 imports for new features
try:
    from model.dram import (
        HBM4LogicBaseDie,
        HBM4PAM3Encoder,
        PAM3SignalModel,
        PAM3Symbol,
        PAM3Level,
        HBM4TimingManager,
        IndependentChannelTiming,
        TimingParameters,
        HBM4Spec,
        DFI5Interface,
        DFICommand,
        HBM4ECC,
        HBM4LaneRepairModel,
        HBM4PowerEstimator,
        BankStateMachine,
        Channel,
        ChannelArray,
    )
    HBM4_AVAILABLE = True
except ImportError:
    HBM4_AVAILABLE = False
    HBM4LogicBaseDie = None
    HBM4PAM3Encoder = None
    PAM3SignalModel = None
    PAM3Symbol = None
    PAM3Level = None
    HBM4TimingManager = None
    IndependentChannelTiming = None
    TimingParameters = None
    HBM4Spec = None
    DFI5Interface = None
    DFICommand = None
    HBM4ECC = None
    HBM4LaneRepairModel = None
    HBM4PowerEstimator = None
    BankStateMachine = None
    Channel = None
    ChannelArray = None

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

    # HBM4-specific statistics
    pam3_symbols_encoded: int = 0
    pam3_symbols_decoded: int = 0
    pam3_errors: int = 0
    ecc_errors_detected: int = 0
    ecc_errors_corrected: int = 0
    lanes_repaired: int = 0
    power_mw: float = 0.0
    channel_stats: Dict[int, Dict[str, int]] = field(default_factory=dict)
    dfi_commands_sent: int = 0
    dfi_commands_completed: int = 0

    # RTL Co-simulation statistics
    rtl_transactions: int = 0
    rtl_matched: int = 0
    rtl_mismatched: int = 0
    rtl_max_latency_diff: int = 0
    rtl_avg_latency_diff: float = 0.0

    @property
    def rtl_match_rate(self) -> float:
        total = self.rtl_matched + self.rtl_mismatched
        if total == 0:
            return 0.0
        return self.rtl_matched / total

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

    @property
    def pam3_bandwidth_efficiency(self) -> float:
        """PAM3 带宽效率 (bits per symbol)"""
        # PAM3 with Gray coding achieves ~1.585 bits/symbol
        if self.pam3_symbols_encoded == 0:
            return 0.0
        return (self.pam3_symbols_encoded * 1.585) / max(1, self.pam3_symbols_encoded)

    @property
    def ecc_overhead(self) -> float:
        """ECC 开销百分比"""
        total_data = self.completed_requests * 64
        if total_data == 0:
            return 0.0
        return (self.ecc_errors_corrected / total_data) * 100 if self.ecc_errors_corrected > 0 else 0.0

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
            # HBM4 features
            'hbm4': {
                'pam3_symbols_encoded': self.pam3_symbols_encoded,
                'pam3_symbols_decoded': self.pam3_symbols_decoded,
                'pam3_errors': self.pam3_errors,
                'ecc_errors_detected': self.ecc_errors_detected,
                'ecc_errors_corrected': self.ecc_errors_corrected,
                'lanes_repaired': self.lanes_repaired,
                'power_mw': self.power_mw,
                'dfi_commands_sent': self.dfi_commands_sent,
                'dfi_commands_completed': self.dfi_commands_completed,
                'channel_stats': self.channel_stats,
            },
            # RTL Co-simulation features
            'rtl_cosim': {
                'enabled': self.rtl_transactions > 0 or self.rtl_matched > 0,
                'transactions': self.rtl_transactions,
                'matched': self.rtl_matched,
                'mismatched': self.rtl_mismatched,
                'match_rate': self.rtl_match_rate,
                'max_latency_diff': self.rtl_max_latency_diff,
                'avg_latency_diff': self.rtl_avg_latency_diff,
            }
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

    HBM4 Features (when enabled):
    - HBM4LogicBaseDie: 统一控制器模型
    - PAM3 Signal Model: 3级信号编码
    - Independent Channel Timing: 独立通道时序
    - DFI 5.0 Interface: 标准协议接口
    - ECC/Lane Repair: 错误纠正和冗余修复
    """

    def __init__(
        self,
        sim_config: SimulationConfig,
        num_masters: int = 4,
        enable_axi: bool = True,
        enable_hbm4: bool = True,
        num_channels: int = 32,
    ):
        """初始化统一仿真器

        Args:
            sim_config: 仿真配置
            num_masters: AXI master 数量
            enable_axi: 是否启用 AXI 互联
            enable_hbm4: 是否启用 HBM4 特性
            num_channels: HBM4 通道数量 (默认 32)
        """
        self.config = sim_config
        self.enable_axi = enable_axi
        self.enable_hbm4 = enable_hbm4 and HBM4_AVAILABLE
        self.num_channels = num_channels

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

        # 统计 (必须先于 HBM4 组件初始化)
        self.stats = UnifiedSimulatorStats()

        # ========== RTL Co-simulation Interface ==========
        self.rtl_interface: Optional[RTLInterface] = None
        self.result_comparator: Optional[ResultComparator] = None
        self.cosim_enabled = False

        # ========== HBM4 Components ==========
        if self.enable_hbm4:
            # HBM4 Logic Base Die
            self.logic_base_die = HBM4LogicBaseDie()

            # PAM3 Signal Model
            self.pam3_model = PAM3SignalModel()
            self.pam3_encoder = HBM4PAM3Encoder(config={
                'symbol_rate': 8e9,
                'voltage_swing': 0.8,
            })

            # Independent Channel Timing Manager
            self.timing_manager = HBM4TimingManager(num_channels=num_channels)

            # DFI 5.0 Interface
            self.dfi = DFI5Interface()

            # ECC Engine
            self.ecc = HBM4ECC()

            # Lane Repair Model
            self.lane_repair = HBM4LaneRepairModel(num_channels=num_channels)

            # Power Estimator
            self.power = HBM4PowerEstimator(num_channels=num_channels)

            # Initialize per-channel statistics
            for ch in range(num_channels):
                self.stats.channel_stats[ch] = {
                    'commands': 0,
                    'activations': 0,
                    'reads': 0,
                    'writes': 0,
                    'refreshes': 0,
                }

            logger.info(f"UnifiedSimulator initialized with HBM4 features: "
                       f"{num_channels} channels, PAM3 enabled")
        else:
            self.logic_base_die = None
            self.pam3_model = None
            self.pam3_encoder = None
            self.timing_manager = None
            self.dfi = None
            self.ecc = None
            self.lane_repair = None
            self.power = None

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

            # HBM4: PAM3 decoding for reads
            if self.enable_hbm4 and self.pam3_encoder:
                # Simulate PAM3 decoding for read data
                self.stats.pam3_symbols_decoded += 4

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

        # ========== HBM4 Components ==========
        if self.enable_hbm4:
            # Tick Logic Base Die
            if self.logic_base_die:
                self.logic_base_die.tick()
                # Track DFI commands
                self.stats.dfi_commands_sent = self.logic_base_die.get_stats().get('total_commands', 0)

            # Tick Timing Manager (independent channel timing)
            if self.timing_manager:
                self.timing_manager.tick()

            # Tick Power Estimator
            if self.power:
                self.power.tick()
                self.stats.power_mw = self.power.get_average_power_mw()

            # Process HBM4 write operations with PAM3 encoding
            if self.enable_hbm4 and new_requests and self.pam3_encoder:
                for req in new_requests:
                    if not req.is_read:
                        # PAM3 encode write data
                        data_value = req.data if hasattr(req, 'data') and req.data is not None else 0xDEADBEEF
                        symbols = self.pam3_encoder.encode_data_burst(
                            data_value,
                            dq_width=128
                        )
                        self.stats.pam3_symbols_encoded += len(symbols)

        # ========== RTL Co-simulation ==========
        if self.cosim_enabled and self.rtl_interface:
            # Advance RTL interface cycle
            self.rtl_interface.tick()

            # Record Python model results for comparison
            if response:
                # Get channel/bank from address for the transaction
                addr = response.addr if hasattr(response, 'addr') else 0
                channel = (addr >> 12) & 0x1F  # Extract channel from address
                tid = self.rtl_interface.inject_read_transaction(
                    address=addr,
                    channel=channel,
                    cycle=self.current_cycle - latency_cycles
                )
                self.rtl_interface.record_python_result(
                    tid=tid,
                    latency_cycles=latency_cycles,
                    data=response.data if hasattr(response, 'data') else None
                )

        return response

    def enable_rtl_cosimulation(
        self,
        enable_rtl: bool = True,
        compare_results: bool = True,
        trace_enabled: bool = False
    ):
        """启用RTL协同仿真

        Args:
            enable_rtl: 是否启用RTL仿真 (False时仅使用Python模型跟踪)
            compare_results: 是否对比Python和RTL结果
            trace_enabled: 是否启用事务追踪
        """
        cosim_config = CoSimConfig(
            enable_rtl=enable_rtl,
            trace_enabled=trace_enabled,
            compare_results=compare_results,
        )
        self.rtl_interface = RTLInterface(cosim_config)
        self.result_comparator = ResultComparator(tolerance_cycles=5)
        self.cosim_enabled = True

        # Set up mismatch callback
        def on_mismatch(diff_info):
            self.stats.rtl_mismatched += 1
            logger.warning(f"RTL mismatch: {diff_info}")

        self.rtl_interface.on_mismatch = on_mismatch

        logger.info(f"RTL cosimulation enabled (rtl={enable_rtl}, compare={compare_results})")

    def disable_rtl_cosimulation(self):
        """禁用RTL协同仿真"""
        if self.rtl_interface:
            self.rtl_interface.stop_rtl_simulation()
        self.rtl_interface = None
        self.result_comparator = None
        self.cosim_enabled = False
        logger.info("RTL cosimulation disabled")

    def inject_rtl_transaction(
        self,
        transaction_type: str,
        address: int,
        data: Optional[int] = None,
        channel: int = 0
    ) -> int:
        """注入事务到RTL

        Args:
            transaction_type: 事务类型 (read/write/activate/precharge/refresh)
            address: 地址
            data: 写数据
            channel: 通道ID

        Returns:
            事务ID
        """
        if not self.cosim_enabled or not self.rtl_interface:
            logger.warning("RTL cosimulation not enabled")
            return -1

        if transaction_type.lower() == 'read':
            return self.rtl_interface.inject_read_transaction(
                address=address,
                channel=channel
            )
        elif transaction_type.lower() == 'write':
            return self.rtl_interface.inject_write_transaction(
                address=address,
                data=data or 0,
                channel=channel
            )
        else:
            return self.rtl_interface.inject_command_transaction(
                command=transaction_type,
                address=address,
                channel=channel
            )

    def get_rtl_stats(self) -> Optional[Dict[str, Any]]:
        """获取RTL协同仿真统计"""
        if not self.cosim_enabled or not self.rtl_interface:
            return None

        stats = self.rtl_interface.get_stats()
        self.stats.rtl_transactions = stats.total_transactions
        self.stats.rtl_matched = stats.matched_results
        self.stats.rtl_mismatched = stats.mismatched_results
        self.stats.rtl_max_latency_diff = stats.max_latency_diff
        self.stats.rtl_avg_latency_diff = stats.avg_latency_diff

        return stats.to_dict()

    def export_rtl_trace(self, path: str):
        """导出RTL事务跟踪

        Args:
            path: 输出文件路径
        """
        if self.rtl_interface:
            self.rtl_interface.export_trace(path)

    def get_cosim_summary(self) -> Dict[str, Any]:
        """获取协同仿真摘要"""
        if not self.cosim_enabled:
            return {'enabled': False}

        return {
            'enabled': True,
            'rtl_interface': self.rtl_interface.get_summary() if self.rtl_interface else None,
            'python_stats': self.stats.to_dict(),
            'match_rate': self.stats.rtl_match_rate,
        }

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

    # ========== HBM4-Specific Methods ==========

    def process_hbm4_command(
        self,
        channel: int,
        command: str,
        address: int,
        data: Optional[int] = None
    ) -> Tuple[bool, str]:
        """处理 HBM4 命令 (通过 Logic Base Die)

        Args:
            channel: 通道 ID (0-31)
            command: 命令类型 (ACT, RD, WR, PRE, REF 等)
            address: 内存地址
            data: 写数据 (对于 WR 命令)

        Returns:
            (success, message)
        """
        if not self.enable_hbm4 or not self.logic_base_die:
            return False, "HBM4 not enabled"

        if channel >= self.num_channels:
            return False, f"Invalid channel {channel}"

        # Process command through Logic Base Die
        ok, msg = self.logic_base_die.process_command(
            channel_id=channel,
            command=command,
            address=address,
            data=data
        )

        if ok:
            # Update channel stats
            if channel in self.stats.channel_stats:
                self.stats.channel_stats[channel]['commands'] += 1

                cmd_upper = command.upper()
                if cmd_upper == 'ACT':
                    self.stats.channel_stats[channel]['activations'] += 1
                elif cmd_upper in ('RD', 'RDA'):
                    self.stats.channel_stats[channel]['reads'] += 1
                elif cmd_upper in ('WR', 'WRA'):
                    self.stats.channel_stats[channel]['writes'] += 1
                elif cmd_upper == 'REF':
                    self.stats.channel_stats[channel]['refreshes'] += 1

        return ok, msg

    def get_channel_state(self, channel: int) -> Optional[Dict]:
        """获取 HBM4 通道状态

        Args:
            channel: 通道 ID

        Returns:
            通道状态字典或 None
        """
        if not self.enable_hbm4 or not self.logic_base_die:
            return None
        return self.logic_base_die.get_channel_state(channel)

    def get_all_channel_states(self) -> List[Dict]:
        """获取所有 HBM4 通道状态"""
        if not self.enable_hbm4 or not self.logic_base_die:
            return []
        return self.logic_base_die.get_all_channel_states()

    def process_pam3_sequence(self, data: int, dq_width: int = 128) -> List[PAM3Symbol]:
        """处理 PAM3 编码序列

        Args:
            data: 要编码的数据
            dq_width: DQ 总线宽度

        Returns:
            PAM3 符号列表
        """
        if not self.enable_hbm4 or not self.pam3_encoder:
            return []

        symbols = self.pam3_encoder.encode_data_burst(data, dq_width)
        self.stats.pam3_symbols_encoded += len(symbols)
        return symbols

    def get_pam3_eye_diagram(self) -> Optional[Any]:
        """获取 PAM3 眼图指标"""
        if not self.enable_hbm4 or not self.pam3_model:
            return None
        return self.pam3_model.compute_eye_diagram()

    def get_independent_timing_status(self) -> Dict[str, Any]:
        """获取独立通道时序状态

        Returns:
            各通道时序状态字典
        """
        if not self.enable_hbm4 or not self.timing_manager:
            return {}

        status = {}
        for ch in range(self.num_channels):
            timing = self.timing_manager.get_channel_timing(ch)
            if timing:
                status[ch] = {
                    'cycle': timing.cycle,
                    'bank_count': len(timing.bank_states),
                }
        return status

    def get_dfi_status(self) -> Optional[Dict]:
        """获取 DFI 接口状态"""
        if not self.enable_hbm4 or not self.dfi:
            return None
        return self.dfi.get_dfi_signals()

    def get_lane_repair_status(self) -> Optional[Dict]:
        """获取 Lane Repair 状态"""
        if not self.enable_hbm4 or not self.lane_repair:
            return None
        stats = self.lane_repair.get_stats()
        self.stats.lanes_repaired = stats.get('total_repaired', 0)
        return stats

    def get_hbm4_metrics(self) -> Dict[str, Any]:
        """获取 HBM4 特定指标 (用于 benchmark)

        Returns:
            HBM4 指标字典
        """
        metrics = {
            'enabled': self.enable_hbm4,
            'num_channels': self.num_channels,
            'pam3': {},
            'timing': {},
            'power': {},
        }

        if self.enable_hbm4:
            # PAM3 metrics
            if self.pam3_model:
                metrics['pam3'] = {
                    'bandwidth_efficiency': self.pam3_model.get_bandwidth_efficiency(),
                    'snr_estimate_db': self.pam3_model.get_snr_estimate(),
                    'symbols_encoded': self.stats.pam3_symbols_encoded,
                    'symbols_decoded': self.stats.pam3_symbols_decoded,
                }

            # Timing metrics
            if self.timing_manager:
                metrics['timing'] = self.get_independent_timing_status()

            # Power metrics
            if self.power:
                metrics['power'] = {
                    'average_mw': self.stats.power_mw,
                    'peak_mw': self.power.get_peak_power_mw() if hasattr(self.power, 'get_peak_power_mw') else 0,
                }

            # ECC metrics
            if self.ecc:
                metrics['ecc'] = {
                    'errors_detected': self.stats.ecc_errors_detected,
                    'errors_corrected': self.stats.ecc_errors_corrected,
                }

            # Lane repair metrics
            if self.lane_repair:
                metrics['lane_repair'] = self.get_lane_repair_status()

        return metrics


def run_unified_simulation(
    simulation_time_us: float = 100.0,
    traffic_pattern: TrafficPattern = TrafficPattern.RANDOM,
    request_rate: float = 0.5,
    num_masters: int = 4,
    enable_axi: bool = True,
    enable_hbm4: bool = True,
    num_channels: int = 32,
    seed: Optional[int] = None,
) -> UnifiedSimulatorStats:
    """运行统一仿真的快捷函数

    Args:
        simulation_time_us: 仿真时间 (微秒)
        traffic_pattern: 流量模式
        request_rate: 请求率
        num_masters: AXI master 数量
        enable_axi: 是否启用 AXI 互联
        enable_hbm4: 是否启用 HBM4 特性
        num_channels: HBM4 通道数量
        seed: 随机种子

    Returns:
        仿真统计
    """
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
        enable_hbm4=enable_hbm4,
        num_channels=num_channels,
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
        enable_hbm4=True,
        num_channels=32,
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

    # HBM4 Features
    print(f"\nHBM4 Features:")
    print(f"  PAM3 symbols encoded: {stats.pam3_symbols_encoded}")
    print(f"  PAM3 symbols decoded: {stats.pam3_symbols_decoded}")
    print(f"  Power: {stats.power_mw:.2f} mW")
    print(f"  DFI commands: {stats.dfi_commands_sent}")

    # 测试无 AXI 模式
    print("\n--- Without AXI Interconnect ---")
    stats_no_axi = run_unified_simulation(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.5,
        enable_axi=False,
        enable_hbm4=True,
        seed=42,
    )

    print(f"  Completed: {stats_no_axi.completed_requests}")
    print(f"  Throughput: {stats_no_axi.throughput_gbps:.2f} GB/s")

    # 测试无 HBM4 模式
    print("\n--- Without HBM4 Features ---")
    stats_no_hbm4 = run_unified_simulation(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        enable_hbm4=False,
        seed=42,
    )

    print(f"  Completed: {stats_no_hbm4.completed_requests}")
    print(f"  Throughput: {stats_no_hbm4.throughput_gbps:.2f} GB/s")
    print(f"  PAM3 symbols: {stats_no_hbm4.pam3_symbols_encoded} (expected 0)")

    print("\n" + "=" * 60)
    print("Unified simulation complete!")