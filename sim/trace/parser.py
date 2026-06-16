"""
HBM Trace Parser
自动解析 HBM 访问 trace 文件并生成性能 summary

支持两种 trace 格式:
1. Ramulator 格式: "R addr" 或 "W addr" (每行一个请求)
2. 扩展格式: "core_id addr" (带 core ID)

Usage:
    from sim.trace.parser import TraceParser, TraceConfig, TraceFormat

    config = TraceConfig(
        trace_file="traces/seq_rd.trace",
        format=TraceFormat.RAMULATOR,
        hbm_version="hbm3"
    )
    parser = TraceParser(config)
    stats = parser.parse()
    parser.print_summary()
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TraceFormat(Enum):
    """Trace 文件格式"""
    RAMULATOR = "ramulator"       # "R addr" 或 "W addr"
    EXTENDED = "extended"         # "core_id addr"
    DRAMTrace = "dramtrace"       # "addr" (无操作类型)
    MASE = "mase"                 # MASE 格式


class HBMVersion(Enum):
    """HBM 版本"""
    HBM2 = "hbm2"
    HBM3 = "hbm3"
    HBM4 = "hbm4"


@dataclass
class TraceConfig:
    """Trace 配置"""
    trace_file: str
    format: TraceFormat = TraceFormat.RAMULATOR
    hbm_version: HBMVersion = HBMVersion.HBM3

    # 可选参数
    address_bits: int = 46       # 地址位宽 (46 bits covers full HBM3/HBM4 channel mapping)
    cache_line_size: int = 64     # Cache line 大小 (bytes)

    # 地址映射参数 (None means use HBM version default)
    channels: Optional[int] = None            # HBM3: 8, HBM4: 32
    pseudo_channels: Optional[int] = None       # HBM3: 16, HBM4: 64
    banks_per_channel: int = 4                 # 每个 pseudo-channel 的 bank 数
    bank_groups: int = 2                       # Bank group 数
    rows_per_bank: int = 1024                  # 每个 bank 的行数

    def update_for_hbm_version(self):
        """Update parameters based on HBM version"""
        if self.hbm_version == HBMVersion.HBM4:
            self.channels = 32
            self.pseudo_channels = 64
            self.rows_per_bank = 2048


@dataclass
class TraceRequest:
    """单个 trace 请求"""
    op_type: str          # "R" 或 "W"
    address: int
    core_id: Optional[int] = None
    line_number: int = 0


@dataclass
class TraceStats:
    """Trace 统计信息"""
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    unique_addresses: int = 0

    # 地址分布统计
    channel_distribution: Dict[int, int] = field(default_factory=dict)
    bank_distribution: Dict[int, int] = field(default_factory=dict)
    bank_group_distribution: Dict[int, int] = field(default_factory=dict)

    # 访问模式分析
    sequential_count: int = 0     # 顺序访问次数
    stride_count: int = 0          # Stride 访问次数
    random_count: int = 0           # 随机访问次数

    # 冲突分析
    same_bank_conflicts: int = 0    # 同 bank 冲突次数
    same_row_accesses: int = 0      # 同一行的连续访问

    # 估算性能
    estimated_row_hit_rate: float = 0.0
    estimated_avg_latency: float = 0.0  # cycles

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_requests": self.total_requests,
            "read_requests": self.read_requests,
            "write_requests": self.write_requests,
            "unique_addresses": self.unique_addresses,
            "sequential_count": self.sequential_count,
            "stride_count": self.stride_count,
            "random_count": self.random_count,
            "same_bank_conflicts": self.same_bank_conflicts,
            "same_row_accesses": self.same_row_accesses,
            "estimated_row_hit_rate": self.estimated_row_hit_rate,
            "estimated_avg_latency": self.estimated_avg_latency,
            "channel_distribution": {str(k): v for k, v in self.channel_distribution.items()},
        }


@dataclass
class ComparisonReport:
    """Model vs Simulation comparison report"""
    trace_name: str = ""
    trace_file: str = ""

    # Model predictions (from TraceParser)
    model_total_requests: int = 0
    model_row_hit_rate: float = 0.0
    model_avg_latency: float = 0.0
    model_row_hits: int = 0
    model_row_misses: int = 0
    model_row_conflicts: int = 0

    # Simulation results (from RamulatorLogResult)
    sim_total_requests: int = 0
    sim_row_hit_rate: float = 0.0
    sim_avg_latency: float = 0.0
    sim_row_hits: int = 0
    sim_row_misses: int = 0
    sim_row_conflicts: int = 0
    sim_memory_cycles: int = 0

    # Error metrics
    hit_rate_error_pp: float = 0.0
    latency_error_pct: float = 0.0
    row_hit_error_pct: float = 0.0
    row_miss_error_pct: float = 0.0
    row_conflict_error_pct: float = 0.0

    def compute_errors(self) -> None:
        """Compute error metrics from differences"""
        self.hit_rate_error_pp = abs(self.model_row_hit_rate - self.sim_row_hit_rate) * 100
        if self.sim_avg_latency > 0:
            self.latency_error_pct = abs(self.model_avg_latency - self.sim_avg_latency) / self.sim_avg_latency * 100
        if self.sim_row_hits > 0:
            self.row_hit_error_pct = abs(self.model_row_hits - self.sim_row_hits) / self.sim_row_hits * 100
        if self.sim_row_misses > 0:
            self.row_miss_error_pct = abs(self.model_row_misses - self.sim_row_misses) / self.sim_row_misses * 100
        if self.sim_row_conflicts > 0:
            self.row_conflict_error_pct = abs(self.model_row_conflicts - self.sim_row_conflicts) / self.sim_row_conflicts * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "trace_name": self.trace_name,
            "trace_file": self.trace_file,
            "model": {
                "total_requests": self.model_total_requests,
                "row_hit_rate": self.model_row_hit_rate,
                "avg_latency": self.model_avg_latency,
                "row_hits": self.model_row_hits,
                "row_misses": self.model_row_misses,
                "row_conflicts": self.model_row_conflicts,
            },
            "simulation": {
                "total_requests": self.sim_total_requests,
                "row_hit_rate": self.sim_row_hit_rate,
                "avg_latency": self.sim_avg_latency,
                "row_hits": self.sim_row_hits,
                "row_misses": self.sim_row_misses,
                "row_conflicts": self.sim_row_conflicts,
                "memory_cycles": self.sim_memory_cycles,
            },
            "errors": {
                "hit_rate_error_pp": self.hit_rate_error_pp,
                "latency_error_pct": self.latency_error_pct,
                "row_hit_error_pct": self.row_hit_error_pct,
                "row_miss_error_pct": self.row_miss_error_pct,
                "row_conflict_error_pct": self.row_conflict_error_pct,
            }
        }


class TraceParser:
    """Trace Parser 实现"""

    # HBM 地址映射参数 (HBM3)
    HBM3_MAPPING = {
        "channels": 8,
        "pseudo_channels": 16,
        "banks_per_pseudo_channel": 4,
        "bank_groups": 2,
        "rows_per_bank": 1024,
        "cols_per_bank": 256,
        "io_width": 128,  # 1024 / 8
    }

    HBM4_MAPPING = {
        "channels": 32,
        "pseudo_channels": 64,
        "banks_per_pseudo_channel": 4,
        "bank_groups": 2,
        "rows_per_bank": 2048,
        "cols_per_bank": 256,
        "io_width": 64,
    }

    def __init__(self, config: TraceConfig):
        self.config = config
        self.requests: List[TraceRequest] = []
        self.stats = TraceStats()

        # 初始化映射参数
        if config.hbm_version == HBMVersion.HBM4:
            mapping = self.HBM4_MAPPING
        else:
            mapping = self.HBM3_MAPPING

        self.channels = config.channels if config.channels is not None else mapping["channels"]
        self.pseudo_channels = config.pseudo_channels if config.pseudo_channels is not None else mapping["pseudo_channels"]
        self.banks_per_pseudo = config.banks_per_channel or mapping["banks_per_pseudo_channel"]
        self.bank_groups = config.bank_groups or mapping["bank_groups"]
        self.rows_per_bank = config.rows_per_bank or mapping["rows_per_bank"]
        self.io_width = mapping["io_width"]

    def parse_file(self, trace_file: str = None) -> List[TraceRequest]:
        """解析 trace 文件"""
        if trace_file:
            self.config.trace_file = trace_file

        if not os.path.exists(self.config.trace_file):
            raise FileNotFoundError(f"Trace file not found: {self.config.trace_file}")

        requests = []
        line_num = 0

        with open(self.config.trace_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                request = self._parse_line(line, line_num)
                if request:
                    requests.append(request)

        self.requests = requests
        logger.info(f"Parsed {len(requests)} requests from {self.config.trace_file}")
        return requests

    def _parse_line(self, line: str, line_num: int) -> Optional[TraceRequest]:
        """解析单行"""
        parts = line.split()

        if self.config.format == TraceFormat.RAMULATOR:
            # Ramulator 格式: "R addr", "W addr", "LD addr", "ST addr"
            if len(parts) < 2:
                return None
            op = parts[0].upper()
            # Support both R/W and LD/ST formats
            if op == "LD":
                op = "R"
            elif op == "ST":
                op = "W"
            try:
                addr = int(parts[1], 0)
            except ValueError:
                return None
            return TraceRequest(op_type=op, address=addr, line_number=line_num)

        elif self.config.format == TraceFormat.EXTENDED:
            # 扩展格式: "core_id addr"
            if len(parts) < 2:
                return None
            try:
                core_id = int(parts[0])
                addr = int(parts[1], 0)
            except ValueError:
                return None
            return TraceRequest(op_type="R", address=addr, core_id=core_id, line_number=line_num)

        elif self.config.format == TraceFormat.DRAMTrace:
            # 简单格式: "addr"
            try:
                addr = int(parts[0], 0)
            except ValueError:
                return None
            return TraceRequest(op_type="R", address=addr, line_number=line_num)

        return None

    def analyze(self) -> TraceStats:
        """分析请求并生成统计"""
        if not self.requests:
            self.parse_file()

        stats = TraceStats()
        unique_addrs = set()
        prev_addr = None
        prev_row = None

        for req in self.requests:
            stats.total_requests += 1
            unique_addrs.add(req.address)

            if req.op_type == 'R':
                stats.read_requests += 1
            else:
                stats.write_requests += 1

            # 地址解码
            decoded = self._decode_address(req.address)
            channel = decoded["channel"]
            bank = decoded["bank"]
            bank_group = decoded["bank_group"]
            row = decoded["row"]

            # 分布统计
            stats.channel_distribution[channel] = stats.channel_distribution.get(channel, 0) + 1
            stats.bank_distribution[bank] = stats.bank_distribution.get(bank, 0) + 1
            stats.bank_group_distribution[bank_group] = stats.bank_group_distribution.get(bank_group, 0) + 1

            # 访问模式分析
            if prev_addr is not None:
                addr_delta = abs(req.address - prev_addr)
                line_size = self.config.cache_line_size

                if addr_delta == line_size:
                    stats.sequential_count += 1
                elif addr_delta % line_size == 0 and addr_delta > line_size:
                    stats.stride_count += 1
                else:
                    # 检查是否跨行
                    if prev_row is not None and row != prev_row:
                        stats.random_count += 1
                    elif prev_row == row:
                        stats.same_row_accesses += 1

            # 冲突检测
            if prev_addr is not None:
                decoded_prev = self._decode_address(prev_addr)
                if (decoded["channel"] == decoded_prev["channel"] and
                    decoded["bank"] == decoded_prev["bank"] and
                    row != prev_row):
                    stats.same_bank_conflicts += 1

            prev_addr = req.address
            prev_row = row

        stats.unique_addresses = len(unique_addrs)

        # 估算行命中率
        total = stats.sequential_count + stats.stride_count + stats.random_count
        if total > 0:
            stats.estimated_row_hit_rate = stats.same_row_accesses / total

        # 估算平均延迟 (基于 HBM3 时序)
        # Row hit: ~30 cycles, Row miss: ~80 cycles, Conflict: ~120 cycles
        if total > 0:
            row_hits = stats.same_row_accesses
            row_misses = stats.stride_count + stats.sequential_count - row_hits
            conflicts = stats.same_bank_conflicts
            stats.estimated_avg_latency = (
                row_hits * 30 + row_misses * 80 + conflicts * 120
            ) / total if total > 0 else 0

        self.stats = stats
        return stats

    def _decode_address(self, address: int) -> Dict[str, int]:
        """地址解码

        HBM 地址映射 (从 MSB 到 LSB):
        [row:10][bank:2][bank_group:1][col:6][channel:3][byte:6]

        支持 HBM3 (8 channels) 和 HBM4 (32 channels) 地址映射:
        - HBM3: Channel at bits [45:43] (3 bits for 8 channels)
        - HBM4: Channel at bits [44:40] (5 bits for 32 channels)
        """
        addr_bits = max(self.config.address_bits, 46)  # Use at least 46 bits for HBM3/HBM4

        # 计算各层级大小
        channel_bits = (self.channels - 1).bit_length()
        pseudo_channel_bits = (self.pseudo_channels // self.channels - 1).bit_length()
        bank_bits = (self.banks_per_pseudo - 1).bit_length()
        bank_group_bits = (self.bank_groups - 1).bit_length()
        row_bits = (self.rows_per_bank - 1).bit_length()
        col_bits = 6  # 64 bytes / 8 = 8 transfers, col = 6 bits
        byte_bits = 6  # 64 bytes

        # Calculate channel bit position based on number of channels
        # HBM3: 8 channels = 3 bits, channel at bits [45:43], LSB at 43
        # HBM4: 32 channels = 5 bits, channel at bits [45:41], LSB at 41
        # Formula: channel_start_bit = 46 - channel_bits
        channel_start_bit = 46 - channel_bits

        # Extract channel from address using proper bit position
        channel = (address >> channel_start_bit) & (self.channels - 1)

        # 剩余位用于 bank
        remaining = address & ((1 << channel_start_bit) - 1)
        bank_group = (remaining >> (bank_bits + row_bits + col_bits + byte_bits)) % self.bank_groups
        bank = (remaining >> (row_bits + col_bits + byte_bits)) % self.banks_per_pseudo

        # Row
        row = (remaining >> (col_bits + byte_bits)) % self.rows_per_bank

        return {
            "channel": channel,
            "pseudo_channel": channel % (self.pseudo_channels // self.channels),
            "bank_group": bank_group,
            "bank": bank,
            "row": row,
        }

    def get_stats(self) -> TraceStats:
        """获取统计信息"""
        return self.stats

    def print_summary(self, stream=None):
        """打印 summary"""
        if stream is None:
            stream = __import__('sys').stdout

        stats = self.stats
        s = lambda x: print(x, file=stream)

        s("\n" + "=" * 70)
        s(f"Trace Summary: {os.path.basename(self.config.trace_file)}")
        s("=" * 70)

        s(f"\n[Request Statistics]")
        s(f"  Total requests:    {stats.total_requests:,}")
        s(f"  Read requests:    {stats.read_requests:,} ({stats.read_requests/max(1,stats.total_requests)*100:.1f}%)")
        s(f"  Write requests:    {stats.write_requests:,} ({stats.write_requests/max(1,stats.total_requests)*100:.1f}%)")
        s(f"  Unique addresses:  {stats.unique_addresses:,}")

        s(f"\n[Access Pattern Analysis]")
        s(f"  Sequential:       {stats.sequential_count:,} ({stats.sequential_count/max(1,stats.total_requests)*100:.1f}%)")
        s(f"  Stride:           {stats.stride_count:,} ({stats.stride_count/max(1,stats.total_requests)*100:.1f}%)")
        s(f"  Random:           {stats.random_count:,} ({stats.random_count/max(1,stats.total_requests)*100:.1f}%)")

        s(f"\n[Bank Conflict Analysis]")
        s(f"  Same row:         {stats.same_row_accesses:,}")
        s(f"  Bank conflicts:   {stats.same_bank_conflicts:,}")

        s(f"\n[Estimated Performance (HBM3)]")
        s(f"  Row hit rate:      {stats.estimated_row_hit_rate*100:.2f}%")
        s(f"  Avg latency:       {stats.estimated_avg_latency:.1f} cycles")

        s(f"\n[Channel Distribution]")
        for ch in sorted(stats.channel_distribution.keys()):
            count = stats.channel_distribution[ch]
            pct = count / max(1, stats.total_requests) * 100
            s(f"  Channel {ch:2d}: {count:8,} ({pct:5.2f}%)")

        s("\n" + "=" * 70)

    # ------------------------------------------------------------------
    # Comparison methods
    # ------------------------------------------------------------------

    def compare_with_ramulator(self, ramulator_result) -> ComparisonReport:
        """Compare model predictions with Ramulator2 simulation results.

        Args:
            ramulator_result: RamulatorLogResult from parse_ramulator_log.py

        Returns:
            ComparisonReport with error metrics
        """
        report = ComparisonReport(
            trace_name=os.path.basename(self.config.trace_file),
            trace_file=self.config.trace_file,
        )

        # Model predictions from TraceParser stats
        report.model_total_requests = self.stats.total_requests
        report.model_row_hit_rate = self.stats.estimated_row_hit_rate
        report.model_avg_latency = self.stats.estimated_avg_latency
        report.model_row_hits = self.stats.same_row_accesses
        report.model_row_misses = self.stats.stride_count + self.stats.sequential_count - self.stats.same_row_accesses
        report.model_row_conflicts = self.stats.same_bank_conflicts

        # Simulation results from Ramulator2
        # Use the original trace request count (not HBM internal bursts)
        report.sim_total_requests = ramulator_result.get_trace_request_count()

        # Get first channel stats for row buffer performance
        ch_stats = ramulator_result.get_per_channel_stats(0)
        if ch_stats:
            report.sim_row_hit_rate = ch_stats.row_hit_rate
            report.sim_avg_latency = ch_stats.avg_read_latency
            report.sim_row_hits = ch_stats.row_hits
            report.sim_row_misses = ch_stats.row_misses
            report.sim_row_conflicts = ch_stats.row_conflicts
        else:
            # Fallback to aggregated stats
            report.sim_row_hit_rate = ramulator_result.aggregated_hit_rate
            report.sim_avg_latency = ramulator_result.total_avg_latency
            report.sim_row_hits = ramulator_result.total_row_hits
            report.sim_row_misses = ramulator_result.total_row_misses
            report.sim_row_conflicts = ramulator_result.total_row_conflicts

        report.sim_memory_cycles = ramulator_result.memory_system_cycles

        # Compute error metrics
        report.compute_errors()

        return report

    def print_comparison(self, ramulator_result) -> None:
        """Print comparison between model and simulation.

        Args:
            ramulator_result: RamulatorLogResult from parse_ramulator_log.py
        """
        report = self.compare_with_ramulator(ramulator_result)

        print("\n" + "=" * 70)
        print(f"Model vs Simulation Comparison: {report.trace_name}")
        print("=" * 70)

        print("\n[Model Predictions (TraceParser)]")
        print(f"  Total requests:   {report.model_total_requests:,}")
        print(f"  Row hit rate:       {report.model_row_hit_rate*100:.2f}%")
        print(f"  Avg latency:        {report.model_avg_latency:.1f} cycles")
        print(f"  Row hits:           {report.model_row_hits:,}")
        print(f"  Row misses:         {report.model_row_misses:,}")
        print(f"  Row conflicts:      {report.model_row_conflicts:,}")

        print("\n[Simulation Results (Ramulator2)]")
        print(f"  Total requests:   {report.sim_total_requests:,}")
        print(f"  Row hit rate:       {report.sim_row_hit_rate*100:.2f}%")
        print(f"  Avg latency:        {report.sim_avg_latency:.2f} cycles")
        print(f"  Row hits:           {report.sim_row_hits:,}")
        print(f"  Row misses:         {report.sim_row_misses:,}")
        print(f"  Row conflicts:      {report.sim_row_conflicts:,}")
        print(f"  Memory cycles:      {report.sim_memory_cycles:,}")

        print("\n[Error Metrics]")
        print(f"  Hit rate error:     {report.hit_rate_error_pp:.2f} pp")
        print(f"  Latency error:      {report.latency_error_pct:.1f}%")
        print(f"  Row hit error:      {report.row_hit_error_pct:.1f}%")
        print(f"  Row miss error:     {report.row_miss_error_pct:.1f}%")
        print(f"  Row conflict error: {report.row_conflict_error_pct:.1f}%")

        print("\n" + "=" * 70)

    def save_comparison_report(
        self,
        ramulator_result,
        output_file: str = None,
    ) -> str:
        """Save comparison report to JSON file.

        Args:
            ramulator_result: RamulatorLogResult from parse_ramulator_log.py
            output_file: Output file path (default: {trace_name}_comparison.json)

        Returns:
            Path to saved report file
        """
        import json

        report = self.compare_with_ramulator(ramulator_result)

        if output_file is None:
            trace_name = os.path.splitext(os.path.basename(self.config.trace_file))[0]
            output_file = f"{trace_name}_comparison.json"

        report_dict = report.to_dict()

        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2)

        logger.info(f"Comparison report saved to {output_file}")
        return output_file

    def save_summary(self, filename: str = None) -> str:
        """保存 summary 到文件"""
        import json

        if filename is None:
            trace_name = os.path.splitext(os.path.basename(self.config.trace_file))[0]
            filename = f"trace_summary_{trace_name}.json"

        summary = {
            "trace_file": self.config.trace_file,
            "format": self.config.format.value,
            "hbm_version": self.config.hbm_version.value,
            "total_requests": self.stats.total_requests,
            "read_requests": self.stats.read_requests,
            "write_requests": self.stats.write_requests,
            "unique_addresses": self.stats.unique_addresses,
            "sequential_count": self.stats.sequential_count,
            "stride_count": self.stats.stride_count,
            "random_count": self.stats.random_count,
            "same_row_accesses": self.stats.same_row_accesses,
            "same_bank_conflicts": self.stats.same_bank_conflicts,
            "estimated_row_hit_rate": self.stats.estimated_row_hit_rate,
            "estimated_avg_latency": self.stats.estimated_avg_latency,
            "channel_distribution": {str(k): v for k, v in self.stats.channel_distribution.items()},
        }

        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary saved to {filename}")
        return filename


def parse_trace_file(
    trace_file: str,
    format: TraceFormat = TraceFormat.RAMULATOR,
    hbm_version: HBMVersion = HBMVersion.HBM3,
    print_summary: bool = True,
) -> TraceStats:
    """快捷函数：解析单个 trace 文件"""
    config = TraceConfig(
        trace_file=trace_file,
        format=format,
        hbm_version=hbm_version,
    )
    parser = TraceParser(config)
    parser.parse_file()
    stats = parser.analyze()

    if print_summary:
        parser.print_summary()

    return stats


def parse_directory(
    trace_dir: str,
    pattern: str = "*.trace",
    print_summary: bool = True,
) -> Dict[str, TraceStats]:
    """快捷函数：解析目录中所有 trace 文件"""
    import glob

    results = {}

    for trace_file in glob.glob(os.path.join(trace_dir, pattern)):
        try:
            print(f"\nParsing: {trace_file}")
            stats = parse_trace_file(trace_file, print_summary=print_summary)
            results[trace_file] = stats
        except Exception as e:
            print(f"Error parsing {trace_file}: {e}")

    return results


def generate_summary_table(results: Dict[str, TraceStats]) -> str:
    """生成 summary 表格 (用于 README 更新)"""
    lines = []
    lines.append("\n| Trace | Requests | Reads | Writes | Row Hit% | Avg Latency |")
    lines.append("|-------|-----------|-------|--------|----------|-------------|")

    for trace_file, stats in results.items():
        trace_name = os.path.basename(trace_file)
        lines.append(
            f"| {trace_name} | {stats.total_requests:,} | "
            f"{stats.read_requests:,} | {stats.write_requests:,} | "
            f"{stats.estimated_row_hit_rate*100:.2f}% | "
            f"{stats.estimated_avg_latency:.1f} cycles |"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    # 解析命令行参数
    if len(sys.argv) < 2:
        print("Usage: python -m sim.trace.parser <trace_file> [format] [hbm_version]")
        print("Formats: ramulator, extended, dramtrace, mase")
        print("Versions: hbm2, hbm3, hbm4")
        sys.exit(1)

    trace_file = sys.argv[1]
    format_str = sys.argv[2] if len(sys.argv) > 2 else "ramulator"
    version_str = sys.argv[3] if len(sys.argv) > 3 else "hbm3"

    format_map = {
        "ramulator": TraceFormat.RAMULATOR,
        "extended": TraceFormat.EXTENDED,
        "dramtrace": TraceFormat.DRAMTrace,
        "mase": TraceFormat.MASE,
    }

    version_map = {
        "hbm2": HBMVersion.HBM2,
        "hbm3": HBMVersion.HBM3,
        "hbm4": HBMVersion.HBM4,
    }

    stats = parse_trace_file(
        trace_file,
        format=format_map.get(format_str, TraceFormat.RAMULATOR),
        hbm_version=version_map.get(version_str, HBMVersion.HBM3),
    )