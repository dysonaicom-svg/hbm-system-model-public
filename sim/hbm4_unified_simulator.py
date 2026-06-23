"""
HBM4 Unified Simulator

集成 HBM4 所有新组件的统一仿真器:
- Logic Base Die (LBD): 统一控制器模型
- PAM3 Encoder/Decoder: 3级信号编码
- Independent Channel Timing: 独立通道时序
- DFI 5.0 Interface: 标准协议接口
- ECC: 错误纠正
- Lane Repair: 冗余修复
- Power Estimator: 功耗估算

Usage:
    python -m sim.hbm4_unified_simulator --mode full --channels 32
    python -m sim.hbm4_unified_simulator --mode quick --channels 8
"""

import argparse
import time
import sys
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto

# Import HBM4 modules
from model.dram import (
    HBM4LogicBaseDie,
    HBM4PAM3Encoder,
    HBM4TimingManager,
    PAM3SignalModel,
    PAM3Level,
    PAM3Symbol,
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

# RTL Co-simulation interface
from sim.rtl_interface import (
    RTLInterface,
    CoSimConfig,
    ResultComparator,
    create_rtl_interface,
)


class SimulationMode(Enum):
    """仿真模式"""
    QUICK = auto()       # 快速功能测试
    FULL = auto()        # 完整时序仿真
    STRESS = auto()      # 压力测试所有通道
    BENCHMARK = auto()   # 性能基准测试


@dataclass
class SimulationConfig:
    """仿真配置"""
    mode: SimulationMode = SimulationMode.QUICK
    num_channels: int = 32
    cycles: int = 1000
    enable_pam3: bool = True
    enable_ecc: bool = True
    enable_lane_repair: bool = True
    trace_commands: bool = False
    verbose: bool = False
    speed_grade: str = "8Gbps"

    @classmethod
    def from_args(cls, args) -> 'SimulationConfig':
        """从命令行参数创建配置"""
        mode_map = {
            'quick': SimulationMode.QUICK,
            'full': SimulationMode.FULL,
            'stress': SimulationMode.STRESS,
            'benchmark': SimulationMode.BENCHMARK,
        }
        return cls(
            mode=mode_map.get(args.mode, SimulationMode.QUICK),
            num_channels=args.channels or 32,
            cycles=args.cycles or 1000,
            enable_pam3=args.pam3 if hasattr(args, 'pam3') else True,
            enable_ecc=args.ecc if hasattr(args, 'ecc') else True,
            enable_lane_repair=args.lane_repair if hasattr(args, 'lane_repair') else True,
            trace_commands=args.trace if hasattr(args, 'trace') else False,
            verbose=args.verbose or False,
            speed_grade=args.speed_grade or "8Gbps",
        )


@dataclass
class SimulationStats:
    """仿真统计"""
    total_cycles: int = 0
    commands_processed: int = 0
    pam3_symbols_encoded: int = 0
    pam3_symbols_decoded: int = 0
    errors_detected: int = 0
    errors_corrected: int = 0
    lanes_repaired: int = 0
    power_mW: float = 0.0
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0

    # 新增: 按通道统计
    channel_stats: Dict[int, Dict[str, int]] = field(default_factory=dict)

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
    def duration_s(self) -> float:
        """仿真持续时间(秒)"""
        return self.end_time - self.start_time

    @property
    def throughput(self) -> float:
        """每秒命令数"""
        if self.duration_s > 0:
            return self.commands_processed / self.duration_s
        return 0.0


class HBM4UnifiedSimulator:
    """
    HBM4 统一仿真器，集成所有组件。

    集成的组件:
    - Logic Base Die (LBD): 统一控制器模型
    - PAM3 Encoder/Decoder: 3级信号编码
    - Independent Channel Timing: 独立通道时钟域
    - DFI 5.0 Interface: 标准协议接口
    - ECC: 错误纠正
    - Lane Repair: 冗余处理
    - Power Estimator: 功耗追踪
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.stats = SimulationStats()
        self.running = False

        # 初始化所有组件
        self._init_components()

    def _init_components(self):
        """初始化所有仿真组件"""
        # HBM4 规格
        self.spec = HBM4Spec()
        # 根据速度等级更新数据速率
        if self.config.speed_grade == "12Gbps":
            self.spec.data_rate_gtps = 12.0
        elif self.config.speed_grade == "16Gbps":
            self.spec.data_rate_gtps = 16.0

        # 核心 Logic Base Die
        self.logic_base_die = HBM4LogicBaseDie()

        # PAM3 信号模型 (NEW)
        self.pam3_model = PAM3SignalModel()
        self.pam3_encoder = HBM4PAM3Encoder()

        # 独立通道时序 (NEW)
        self.timing_manager = HBM4TimingManager(
            num_channels=self.config.num_channels
        )

        # DFI 接口
        self.dfi = DFI5Interface()

        # ECC (如果启用)
        self.ecc = HBM4ECC() if self.config.enable_ecc else None

        # Lane Repair (如果启用)
        self.lane_repair = HBM4LaneRepairModel(
            num_channels=self.config.num_channels
        ) if self.config.enable_lane_repair else None

        # Power estimator
        self.power = HBM4PowerEstimator(
            num_channels=self.config.num_channels
        )

        # Channel array
        self.channels = ChannelArray(num_channels=self.config.num_channels)

        # ========== RTL Co-simulation ==========
        self.rtl_interface: Optional[RTLInterface] = None
        self.result_comparator: Optional[ResultComparator] = None
        self.cosim_enabled = False
        self._current_cycle = 0

        # 初始化通道统计
        for ch in range(self.config.num_channels):
            self.stats.channel_stats[ch] = {
                'commands': 0,
                'activations': 0,
                'reads': 0,
                'writes': 0,
                'refreshes': 0,
            }

        if self.config.verbose:
            print(f"[HBM4UnifiedSim] Initialized with {self.config.num_channels} channels")
            print(f"[HBM4UnifiedSim] PAM3: {self.config.enable_pam3}, ECC: {self.config.enable_ecc}")
            print(f"[HBM4UnifiedSim] Speed Grade: {self.config.speed_grade}")

    def initialize(self):
        """初始化仿真"""
        self.logic_base_die.initialize()

        # 运行初始化周期（需要足够周期完成PHY训练，约2000周期）
        for _ in range(2000):
            self.tick()

        self.running = True
        if self.config.verbose:
            print(f"[HBM4UnifiedSim] Initialization complete at cycle {self.logic_base_die.cycle}")

    def tick(self):
        """Advance one cycle"""
        # Advance all components
        self.logic_base_die.tick()
        self.timing_manager.tick()

        # Channel array doesn't have tick - advance via timing manager
        # which tracks bank states per channel

        self.power.tick()

        self.stats.total_cycles += 1

    def process_command(
        self,
        channel: int,
        command: str,
        address: int,
        data: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        处理内存命令。

        Args:
            channel: 通道 ID (0-31)
            command: 命令类型 (ACT, RD, WR, PRE, REF 等)
            address: 内存地址
            data: 写数据 (对于 WR 命令)

        Returns:
            (success, message)
        """
        # 验证通道
        if channel >= self.config.num_channels:
            return False, f"Invalid channel {channel}"

        # 通过 Logic Base Die 处理
        ok, msg = self.logic_base_die.process_command(
            channel_id=channel,
            command=command,
            address=address,
            data=data
        )

        if ok:
            self.stats.commands_processed += 1
            self.stats.channel_stats[channel]['commands'] += 1

            # 按命令类型更新统计
            cmd_upper = command.upper()
            if cmd_upper == 'ACT':
                self.stats.channel_stats[channel]['activations'] += 1
            elif cmd_upper in ('RD', 'RDA'):
                self.stats.channel_stats[channel]['reads'] += 1
            elif cmd_upper in ('WR', 'WRA'):
                self.stats.channel_stats[channel]['writes'] += 1
            elif cmd_upper == 'REF':
                self.stats.channel_stats[channel]['refreshes'] += 1

            # PAM3 编码 (写操作)
            if self.config.enable_pam3 and command in ('WR', 'WRA') and data is not None:
                symbols = self.pam3_encoder.encode_data_burst(
                    data, dq_width=128
                )
                self.stats.pam3_symbols_encoded += len(symbols)

            # PAM3 解码 (读操作)
            elif command in ('RD', 'RDA'):
                # 模拟解码
                self.stats.pam3_symbols_decoded += 4

        return ok, msg

    def process_pam3_sequence(self, data: int, dq_width: int = 128) -> List[PAM3Symbol]:
        """
        处理 PAM3 编码/解码序列 (NEW)。

        Args:
            data: 要编码的数据
            dq_width: DQ 总线宽度

        Returns:
            PAM3 符号列表
        """
        symbols = self.pam3_encoder.encode_data_burst(data, dq_width)
        self.stats.pam3_symbols_encoded += len(symbols)
        return symbols

    def get_channel_state(self, channel: int) -> Dict[str, Any]:
        """获取特定通道的状态"""
        return self.logic_base_die.get_channel_state(channel)

    def get_stats(self) -> Dict[str, Any]:
        """获取仿真统计"""
        power_mW = self.power.get_total_power_mw() if hasattr(self.power, 'get_total_power_mw') else self.power.get_average_power_mw()
        self.stats.power_mW = power_mW
        self.stats.end_time = time.time()

        return {
            'total_cycles': self.stats.total_cycles,
            'commands_processed': self.stats.commands_processed,
            'pam3_symbols_encoded': self.stats.pam3_symbols_encoded,
            'pam3_symbols_decoded': self.stats.pam3_symbols_decoded,
            'errors_detected': self.stats.errors_detected,
            'errors_corrected': self.stats.errors_corrected,
            'lanes_repaired': self.stats.lanes_repaired,
            'power_mW': power_mW,
            'duration_s': self.stats.duration_s,
            'throughput': self.stats.throughput,
            'channel_stats': self.stats.channel_stats,
            # RTL Co-simulation
            'rtl_cosim': {
                'enabled': self.cosim_enabled,
                'transactions': self.stats.rtl_transactions if hasattr(self.stats, 'rtl_transactions') else 0,
            },
        }

    # ========== RTL Co-simulation Methods ==========

    def enable_rtl_cosimulation(
        self,
        enable_rtl: bool = True,
        compare_results: bool = True,
        trace_enabled: bool = False
    ):
        """启用RTL协同仿真

        Args:
            enable_rtl: 是否启用RTL仿真
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
            if hasattr(self.stats, 'rtl_mismatched'):
                self.stats.rtl_mismatched += 1
            print(f"[RTL MISMATCH] {diff_info}")

        self.rtl_interface.on_mismatch = on_mismatch

        print(f"[HBM4UnifiedSim] RTL cosimulation enabled (rtl={enable_rtl}, compare={compare_results})")

    def disable_rtl_cosimulation(self):
        """禁用RTL协同仿真"""
        if self.rtl_interface:
            self.rtl_interface.stop_rtl_simulation()
        self.rtl_interface = None
        self.result_comparator = None
        self.cosim_enabled = False
        print("[HBM4UnifiedSim] RTL cosimulation disabled")

    def run(self) -> SimulationStats:
        """
        根据配置的模式运行仿真。

        Returns:
            仿真统计
        """
        self.initialize()

        mode = self.config.mode

        if mode == SimulationMode.QUICK:
            self._run_quick_mode()
        elif mode == SimulationMode.FULL:
            self._run_full_mode()
        elif mode == SimulationMode.STRESS:
            self._run_stress_mode()
        elif mode == SimulationMode.BENCHMARK:
            self._run_benchmark_mode()

        self.stats.end_time = time.time()
        self.running = False

        return self.stats

    def _run_quick_mode(self):
        """快速功能测试"""
        if self.config.verbose:
            print("[HBM4UnifiedSim] Running QUICK mode...")

        # 基本命令序列
        for ch in range(min(4, self.config.num_channels)):
            self.process_command(ch, 'ACT', address=0x1000)
            for _ in range(15):
                self.tick()

            self.process_command(ch, 'RD', address=0x1000)
            for _ in range(10):
                self.tick()

            self.process_command(ch, 'PRE', address=0x1000)

    def _run_full_mode(self):
        """完整时序仿真"""
        if self.config.verbose:
            print("[HBM4UnifiedSim] Running FULL mode...")

        for _ in range(self.config.cycles):
            self.tick()

    def _run_stress_mode(self):
        """压力测试所有通道"""
        if self.config.verbose:
            print("[HBM4UnifiedSim] Running STRESS mode...")

        # 并行激活所有通道
        for ch in range(self.config.num_channels):
            self.process_command(ch, 'ACT', address=0x1000 + ch)

        for _ in range(10):
            self.tick()

        # 读写所有通道
        for ch in range(self.config.num_channels):
            cmd = 'RD' if ch % 2 == 0 else 'WR'
            self.process_command(ch, cmd, address=0x1000 + ch, data=0xDEADBEEF + ch)

        for _ in range(self.config.cycles):
            self.tick()

    def _run_benchmark_mode(self):
        """性能基准测试"""
        if self.config.verbose:
            print("[HBM4UnifiedSim] Running BENCHMARK mode...")

        start = time.time()

        # PAM3 编码基准
        for _ in range(10000):
            self.process_pam3_sequence(0xDEADBEEF)

        pam3_time = time.time() - start

        # 通道操作基准
        start = time.time()
        for ch in range(self.config.num_channels):
            self.process_command(ch, 'ACT', address=0x1000)

        channel_time = time.time() - start

        if self.config.verbose:
            print(f"[HBM4UnifiedSim] PAM3: {10000/pam3_time:.0f} ops/s")
            print(f"[HBM4UnifiedSim] Channels: {self.config.num_channels/channel_time:.0f} ops/s")

        # 运行剩余周期
        for _ in range(self.config.cycles):
            self.tick()


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='HBM4 统一仿真器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    # 8通道快速测试
    python -m sim.hbm4_unified_simulator --mode quick --channels 8

    # 32通道完整仿真
    python -m sim.hbm4_unified_simulator --mode full --channels 32 --cycles 10000

    # 压力测试所有通道
    python -m sim.hbm4_unified_simulator --mode stress --verbose

    # 性能基准测试
    python -m sim.hbm4_unified_simulator --mode benchmark
'''
    )

    parser.add_argument(
        '--mode', '-m',
        choices=['quick', 'full', 'stress', 'benchmark'],
        default='quick',
        help='仿真模式 (默认: quick)'
    )

    parser.add_argument(
        '--channels', '-c',
        type=int,
        default=32,
        help='通道数量 (默认: 32)'
    )

    parser.add_argument(
        '--cycles', '-n',
        type=int,
        default=1000,
        help='FULL/BENCHMARK 模式的周期数 (默认: 1000)'
    )

    parser.add_argument(
        '--speed-grade', '-s',
        choices=['8Gbps', '12Gbps', '16Gbps'],
        default='8Gbps',
        help='速度等级 (默认: 8Gbps)'
    )

    parser.add_argument(
        '--no-pam3',
        action='store_true',
        help='禁用 PAM3 编码'
    )

    parser.add_argument(
        '--no-ecc',
        action='store_true',
        help='禁用 ECC'
    )

    parser.add_argument(
        '--no-lane-repair',
        action='store_true',
        help='禁用 Lane Repair'
    )

    parser.add_argument(
        '--trace',
        action='store_true',
        help='启用命令追踪'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )

    return parser


def main():
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()

    # 处理 --no-* 参数
    args.pam3 = not args.no_pam3
    args.ecc = not args.no_ecc
    args.lane_repair = not args.no_lane_repair

    # 创建配置和仿真器
    config = SimulationConfig.from_args(args)
    simulator = HBM4UnifiedSimulator(config)

    print(f"HBM4 Unified Simulator v1.0")
    print(f"Mode: {config.mode.name}, Channels: {config.num_channels}")
    print("-" * 50)

    # 运行仿真
    stats = simulator.run()

    # 打印结果
    print("-" * 50)
    print(f"Simulation completed in {stats.duration_s:.3f}s")
    print(f"Total cycles: {stats.total_cycles}")
    print(f"Commands processed: {stats.commands_processed}")
    print(f"PAM3 symbols encoded: {stats.pam3_symbols_encoded}")
    print(f"PAM3 symbols decoded: {stats.pam3_symbols_decoded}")
    print(f"Power: {stats.power_mW:.2f} mW")
    print(f"Throughput: {stats.throughput:.0f} commands/s")

    # 打印通道统计
    if config.verbose:
        print("\nChannel Statistics:")
        for ch, ch_stats in stats.channel_stats.items():
            if ch_stats['commands'] > 0:
                print(f"  Channel {ch}: {ch_stats['commands']} commands "
                      f"(ACT={ch_stats['activations']}, "
                      f"RD={ch_stats['reads']}, "
                      f"WR={ch_stats['writes']})")

    return 0


if __name__ == '__main__':
    sys.exit(main())
