"""
RTL Co-simulation Interface for HBM Unified Simulator

提供Python模型和RTL之间的协同仿真能力:
- RTL事务注入
- Python模型结果对比
- 时序对齐
- 事务跟踪

Usage:
    rtl_iface = RTLInterface()
    rtl_iface.inject_transaction(...)
    result = rtl_iface.get_rtl_result(...)
"""

import os
import subprocess
import threading
import time
import json
import struct
import socket
import select
import fcntl
import errno
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """事务类型"""
    READ = "read"
    WRITE = "write"
    ACTIVATE = "activate"
    PRECHARGE = "precharge"
    REFRESH = "refresh"


class TransactionStatus(Enum):
    """事务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class RTLTransaction:
    """RTL事务"""
    id: int
    transaction_type: TransactionType
    address: int
    data: Optional[int] = None
    channel: int = 0
    bank: int = 0
    cycle: int = 0
    status: TransactionStatus = TransactionStatus.PENDING
    latency_cycles: int = 0
    response_data: Optional[int] = None
    timestamp_ns: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.transaction_type.value,
            'address': hex(self.address),
            'data': hex(self.data) if self.data is not None else None,
            'channel': self.channel,
            'bank': self.bank,
            'cycle': self.cycle,
            'status': self.status.value,
            'latency_cycles': self.latency_cycles,
            'response_data': hex(self.response_data) if self.response_data is not None else None,
            'timestamp_ns': self.timestamp_ns,
        }


@dataclass
class CoSimConfig:
    """协同仿真配置"""
    enable_rtl: bool = False
    rtl_simulator: str = "verilator"  # verilator, modelsim, vcs
    rtl_build_dir: str = "./rtl/build"
    rtl_top_module: str = "hbm_controller_tb"
    trace_enabled: bool = False
    timeout_cycles: int = 100000
    sync_mode: str = "cycle"  # cycle, event
    compare_results: bool = True
    dump_waveform: bool = False
    waveform_format: str = "vcd"  # vcd, fsdb
    log_level: str = "INFO"


@dataclass
class CoSimStats:
    """协同仿真统计"""
    total_transactions: int = 0
    python_completed: int = 0
    rtl_completed: int = 0
    matched_results: int = 0
    mismatched_results: int = 0
    max_latency_diff: int = 0
    avg_latency_diff: float = 0.0
    sync_overhead_ns: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_transactions': self.total_transactions,
            'python_completed': self.python_completed,
            'rtl_completed': self.rtl_completed,
            'matched_results': self.matched_results,
            'mismatched_results': self.mismatched_results,
            'max_latency_diff': self.max_latency_diff,
            'avg_latency_diff': self.avg_latency_diff,
            'sync_overhead_ns': self.sync_overhead_ns,
            'match_rate': self.matched_results / max(1, self.total_transactions),
        }


class RTLInterface:
    """
    RTL协同仿真接口

    Features:
    - 事务注入和追踪
    - Python/RTL结果对比
    - 时序同步
    - 波形Dump控制
    """

    def __init__(self, config: Optional[CoSimConfig] = None):
        self.config = config or CoSimConfig()
        self.stats = CoSimStats()
        self.transactions: Dict[int, RTLTransaction] = {}
        self.next_transaction_id = 0
        self.current_cycle = 0

        # Python模型参考结果
        self.python_results: Dict[int, Dict[str, Any]] = {}

        # RTL仿真进程 (如果启用)
        self.rtl_process: Optional[subprocess.Popen] = None
        self.rtl_socket: Optional[socket.socket] = None
        self.rtl_ready = False
        self.rtl_fifo_out: Optional[str] = None  # FIFO输出路径
        self.rtl_fifo_in: Optional[str] = None   # FIFO输入路径

        # 波形控制
        self._waveform_enabled = False

        # 回调函数
        self.on_transaction_complete: Optional[Callable] = None
        self.on_mismatch: Optional[Callable] = None

        # 波形文件路径
        self.waveform_path = None

        logger.info(f"RTLInterface initialized (enable_rtl={self.config.enable_rtl})")

    def _generate_transaction_id(self) -> int:
        """生成唯一事务ID"""
        tid = self.next_transaction_id
        self.next_transaction_id += 1
        return tid

    def inject_read_transaction(
        self,
        address: int,
        channel: int = 0,
        bank: int = 0,
        cycle: Optional[int] = None
    ) -> int:
        """注入读事务到RTL

        Args:
            address: 内存地址
            channel: 通道ID
            bank: 银行ID
            cycle: 注入周期 (None=当前周期)

        Returns:
            事务ID
        """
        tid = self._generate_transaction_id()
        trans = RTLTransaction(
            id=tid,
            transaction_type=TransactionType.READ,
            address=address,
            channel=channel,
            bank=bank,
            cycle=cycle if cycle is not None else self.current_cycle,
            timestamp_ns=time.time_ns() / 1e9
        )
        self.transactions[tid] = trans
        self.stats.total_transactions += 1

        logger.debug(f"Injected READ transaction {tid}: addr={hex(address)}, ch={channel}")

        # 如果RTL已连接，发送事务
        if self.rtl_ready:
            self._send_to_rtl(trans)

        return tid

    def inject_write_transaction(
        self,
        address: int,
        data: int,
        channel: int = 0,
        bank: int = 0,
        cycle: Optional[int] = None
    ) -> int:
        """注入写事务到RTL

        Args:
            address: 内存地址
            data: 写数据
            channel: 通道ID
            bank: 银行ID
            cycle: 注入周期

        Returns:
            事务ID
        """
        tid = self._generate_transaction_id()
        trans = RTLTransaction(
            id=tid,
            transaction_type=TransactionType.WRITE,
            address=address,
            data=data,
            channel=channel,
            bank=bank,
            cycle=cycle if cycle is not None else self.current_cycle,
            timestamp_ns=time.time_ns() / 1e9
        )
        self.transactions[tid] = trans
        self.stats.total_transactions += 1

        logger.debug(f"Injected WRITE transaction {tid}: addr={hex(address)}, data={hex(data)}")

        if self.rtl_ready:
            self._send_to_rtl(trans)

        return tid

    def inject_command_transaction(
        self,
        command: str,
        address: int,
        channel: int = 0,
        bank: int = 0,
        cycle: Optional[int] = None
    ) -> int:
        """注入命令事务 (ACT, PRE, REF等)

        Args:
            command: 命令类型
            address: 地址
            channel: 通道ID
            bank: 银行ID
            cycle: 注入周期

        Returns:
            事务ID
        """
        cmd_type = TransactionType(command.lower())
        tid = self._generate_transaction_id()
        trans = RTLTransaction(
            id=tid,
            transaction_type=cmd_type,
            address=address,
            channel=channel,
            bank=bank,
            cycle=cycle if cycle is not None else self.current_cycle,
            timestamp_ns=time.time_ns() / 1e9
        )
        self.transactions[tid] = trans
        self.stats.total_transactions += 1

        logger.debug(f"Injected {command} transaction {tid}")

        if self.rtl_ready:
            self._send_to_rtl(trans)

        return tid

    def _send_to_rtl(self, trans: RTLTransaction):
        """发送事务到RTL仿真器

        使用socket通信或文件方式与RTL仿真器交换数据。
        支持以下通信模式:
        1. Socket模式: 通过TCP socket与Verilator通信
        2. 文件模式: 通过FIFO文件交换JSON消息
        """
        msg = json.dumps(trans.to_dict())
        logger.debug(f"Sending to RTL: {msg}")

        # Socket通信模式
        if self.rtl_socket:
            try:
                # 发送消息长度 (4字节网络序)
                msg_bytes = msg.encode('utf-8')
                header = struct.pack('!I', len(msg_bytes))
                self.rtl_socket.sendall(header + msg_bytes)
                logger.debug(f"Sent {len(msg_bytes)} bytes to RTL via socket")
            except (socket.error, BrokenPipeError) as e:
                logger.error(f"Socket send failed: {e}")
                self.rtl_ready = False

        # 文件模式 (通过FIFO)
        elif self.rtl_fifo_out:
            try:
                with open(self.rtl_fifo_out, 'w') as f:
                    f.write(msg + '\n')
                    f.flush()
                logger.debug(f"Sent to RTL via FIFO: {self.rtl_fifo_out}")
            except IOError as e:
                logger.error(f"FIFO send failed: {e}")

        # 默认: 仅记录 (脱机模式)
        else:
            logger.debug(f"RTL offline mode: transaction {trans.id} queued for later sync")

    def receive_from_rtl(self, message: str):
        """接收来自RTL的消息"""
        try:
            data = json.loads(message)
            tid = data.get('id')
            if tid in self.transactions:
                trans = self.transactions[tid]
                trans.status = TransactionStatus(data.get('status', 'completed'))
                trans.latency_cycles = data.get('latency_cycles', 0)
                trans.response_data = data.get('response_data')

                self.stats.rtl_completed += 1

                # 触发回调
                if self.on_transaction_complete:
                    self.on_transaction_complete(trans)

        except json.JSONDecodeError:
            logger.error(f"Failed to parse RTL message: {message}")

    def record_python_result(
        self,
        tid: int,
        latency_cycles: int,
        data: Optional[int] = None
    ):
        """记录Python模型结果用于对比"""
        self.python_results[tid] = {
            'latency_cycles': latency_cycles,
            'data': data,
            'timestamp_ns': time.time_ns() / 1e9
        }

    def compare_results(self, tid: int) -> Tuple[bool, Dict[str, Any]]:
        """对比Python和RTL结果

        Args:
            tid: 事务ID

        Returns:
            (is_match, diff_info)
        """
        if tid not in self.transactions:
            return False, {'error': 'Transaction not found'}

        trans = self.transactions[tid]
        if tid not in self.python_results:
            return False, {'error': 'Python result not found'}

        python = self.python_results[tid]

        # 比较延迟
        latency_diff = abs(trans.latency_cycles - python['latency_cycles'])

        # 比较数据 (如果是读操作)
        data_match = True
        if trans.transaction_type == TransactionType.READ:
            data_match = (trans.response_data == python['data'])

        is_match = (latency_diff == 0) and data_match

        diff_info = {
            'tid': tid,
            'latency_diff': latency_diff,
            'data_match': data_match,
            'python_latency': python['latency_cycles'],
            'rtl_latency': trans.latency_cycles,
            'python_data': python.get('data'),
            'rtl_data': trans.response_data,
        }

        # 更新统计
        if is_match:
            self.stats.matched_results += 1
        else:
            self.stats.mismatched_results += 1
            if self.on_mismatch:
                self.on_mismatch(diff_info)

        # 更新延迟差异统计
        if latency_diff > self.stats.max_latency_diff:
            self.stats.max_latency_diff = latency_diff

        total_diff = sum(
            abs(self.transactions[t].latency_cycles - self.python_results.get(t, {}).get('latency_cycles', 0))
            for t in self.transactions
            if t in self.python_results
        )
        count = max(1, len(self.python_results))
        self.stats.avg_latency_diff = total_diff / count

        return is_match, diff_info

    def tick(self) -> int:
        """推进一个仿真周期

        Returns:
            当前周期
        """
        self.current_cycle += 1
        return self.current_cycle

    def get_pending_transactions(self) -> List[RTLTransaction]:
        """获取待处理的事务"""
        return [
            t for t in self.transactions.values()
            if t.status in (TransactionStatus.PENDING, TransactionStatus.IN_PROGRESS)
        ]

    def get_completed_transactions(self) -> List[RTLTransaction]:
        """获取已完成的事务"""
        return [
            t for t in self.transactions.values()
            if t.status == TransactionStatus.COMPLETED
        ]

    def get_transaction(self, tid: int) -> Optional[RTLTransaction]:
        """获取指定事务"""
        return self.transactions.get(tid)

    def get_stats(self) -> CoSimStats:
        """获取协同仿真统计"""
        return self.stats

    def enable_waveform_dump(self, path: Optional[str] = None):
        """启用波形Dump

        Args:
            path: 波形文件路径
        """
        self.config.dump_waveform = True
        self.waveform_path = path or "./rtl/waves.vcd"
        self._waveform_enabled = True
        logger.info(f"Waveform dump enabled: {self.waveform_path}")

        # 发送命令到RTL仿真器启用波形
        if self.rtl_socket and self.rtl_ready:
            self._send_waveform_command("enable", self.waveform_path)
        elif self.rtl_fifo_out:
            self._send_waveform_command("enable", self.waveform_path)
        else:
            logger.debug("Waveform command queued (RTL not connected)")

    def disable_waveform_dump(self):
        """禁用波形Dump"""
        self.config.dump_waveform = False
        self._waveform_enabled = False
        logger.info("Waveform dump disabled")

        # 通知RTL停止波形Dump
        if self.rtl_socket and self.rtl_ready:
            self._send_waveform_command("disable", None)
        elif self.rtl_fifo_out:
            self._send_waveform_command("disable", None)

    def _send_waveform_command(self, action: str, path: Optional[str]):
        """发送波形控制命令到RTL

        Args:
            action: "enable" 或 "disable"
            path: 波形文件路径 (仅enable时需要)
        """
        cmd = {
            'type': 'waveform_control',
            'action': action,
            'path': path,
            'timestamp_ns': time.time_ns() / 1e9,
        }
        msg = json.dumps(cmd)
        logger.info(f"Sending waveform {action} command to RTL: {path or ''}")

        if self.rtl_socket:
            try:
                msg_bytes = msg.encode('utf-8')
                header = struct.pack('!I', len(msg_bytes))
                self.rtl_socket.sendall(header + msg_bytes)
            except (socket.error, BrokenPipeError) as e:
                logger.error(f"Failed to send waveform command: {e}")

        if self.rtl_fifo_out:
            try:
                with open(self.rtl_fifo_out, 'w') as f:
                    f.write(msg + '\n')
                    f.flush()
            except IOError as e:
                logger.error(f"Failed to send waveform command via FIFO: {e}")

    def connect_via_socket(self, host: str = "localhost", port: int = 8765) -> bool:
        """通过Socket连接到RTL仿真器

        Args:
            host: RTL仿真器主机
            port: 端口号

        Returns:
            是否成功连接
        """
        try:
            self.rtl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rtl_socket.settimeout(5.0)
            self.rtl_socket.connect((host, port))
            self.rtl_socket.settimeout(None)
            self.rtl_ready = True
            logger.info(f"Connected to RTL at {host}:{port}")
            return True
        except socket.error as e:
            logger.error(f"Failed to connect to RTL at {host}:{port}: {e}")
            self.rtl_socket = None
            return False

    def setup_fifo_communication(self, fifo_dir: str = "/tmp/hbm_rtl") -> bool:
        """设置FIFO通信通道

        创建命名的FIFO管道用于与RTL通信。
        需要RTL端也使用相同的FIFO路径。

        Args:
            fifo_dir: FIFO文件目录

        Returns:
            是否成功创建
        """
        os.makedirs(fifo_dir, exist_ok=True)
        self.rtl_fifo_out = os.path.join(fifo_dir, "python_to_rtl")
        self.rtl_fifo_in = os.path.join(fifo_dir, "rtl_to_python")

        # 创建FIFO (如果不存在)
        for fifo_path in [self.rtl_fifo_out, self.rtl_fifo_in]:
            if not os.path.exists(fifo_path):
                try:
                    os.mkfifo(fifo_path)
                    logger.info(f"Created FIFO: {fifo_path}")
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        logger.error(f"Failed to create FIFO {fifo_path}: {e}")
                        return False

        logger.info(f"FIFO communication setup: {fifo_dir}")
        return True

    def receive_from_rtl_socket(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """从RTL socket接收响应

        Args:
            timeout: 超时时间(秒)

        Returns:
            解析后的消息字典,超时返回None
        """
        if not self.rtl_socket:
            return None

        try:
            # 读取4字节长度头
            self.rtl_socket.settimeout(timeout)
            header = b''
            while len(header) < 4:
                header += self.rtl_socket.recv(4 - len(header))

            msg_len = struct.unpack('!I', header)[0]

            # 读取消息体
            msg_bytes = b''
            while len(msg_bytes) < msg_len:
                msg_bytes += self.rtl_socket.recv(msg_len - len(msg_bytes))

            self.rtl_socket.settimeout(None)
            return json.loads(msg_bytes.decode('utf-8'))

        except socket.timeout:
            return None
        except (socket.error, json.JSONDecodeError) as e:
            logger.error(f"Failed to receive from RTL: {e}")
            return None

    def start_rtl_simulation(self) -> bool:
        """启动RTL仿真进程

        Returns:
            是否成功启动
        """
        if not self.config.enable_rtl:
            logger.info("RTL simulation disabled in config")
            return False

        if self.rtl_process is not None:
            logger.warning("RTL process already running")
            return False

        build_dir = Path(self.config.rtl_build_dir)
        if not build_dir.exists():
            logger.warning(f"RTL build directory not found: {build_dir}")
            logger.info("RTL cosimulation requires pre-built RTL (run: cd rtl && make)")
            return False

        # 查找可执行文件
        rtl_exe = build_dir / "Vhbm_controller_tb__ALL"
        if not rtl_exe.exists():
            rtl_exe = build_dir / "obj_dir" / "Vhbm_controller_tb"
            if not rtl_exe.exists():
                logger.warning(f"RTL executable not found: {rtl_exe}")
                return False

        try:
            cmd = [str(rtl_exe)]
            if self.config.trace_enabled:
                cmd.extend(["--trace", "--trace-depth", "10"])

            self.rtl_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.rtl_ready = True
            logger.info(f"RTL simulation started: PID={self.rtl_process.pid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start RTL simulation: {e}")
            return False

    def stop_rtl_simulation(self):
        """停止RTL仿真进程"""
        if self.rtl_process:
            self.rtl_process.terminate()
            try:
                self.rtl_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.rtl_process.kill()
            self.rtl_process = None
            self.rtl_ready = False
            logger.info("RTL simulation stopped")

    def export_trace(self, path: str):
        """导出事务跟踪到文件

        Args:
            path: 输出文件路径
        """
        with open(path, 'w') as f:
            json.dump({
                'transactions': [t.to_dict() for t in self.transactions.values()],
                'python_results': self.python_results,
                'stats': self.stats.to_dict()
            }, f, indent=2)
        logger.info(f"Trace exported to {path}")

    def import_trace(self, path: str):
        """从文件导入事务跟踪

        Args:
            path: 输入文件路径
        """
        with open(path, 'r') as f:
            data = json.load(f)

        self.transactions = {}
        for t_data in data.get('transactions', []):
            t = RTLTransaction(
                id=t_data['id'],
                transaction_type=TransactionType(t_data['type']),
                address=int(t_data['address'], 16),
                data=int(t_data['data'], 16) if t_data.get('data') else None,
                channel=t_data['channel'],
                bank=t_data['bank'],
                cycle=t_data['cycle'],
                status=TransactionStatus(t_data['status']),
                latency_cycles=t_data['latency_cycles'],
                response_data=int(t_data['response_data'], 16) if t_data.get('response_data') else None,
                timestamp_ns=t_data['timestamp_ns'],
            )
            self.transactions[t.id] = t

        self.python_results = data.get('python_results', {})
        logger.info(f"Trace imported from {path}")

    def get_summary(self) -> Dict[str, Any]:
        """获取协同仿真摘要"""
        return {
            'config': {
                'enable_rtl': self.config.enable_rtl,
                'rtl_simulator': self.config.rtl_simulator,
                'trace_enabled': self.config.trace_enabled,
                'dump_waveform': self.config.dump_waveform,
            },
            'stats': self.stats.to_dict(),
            'current_cycle': self.current_cycle,
            'pending_count': len(self.get_pending_transactions()),
            'completed_count': len(self.get_completed_transactions()),
        }


class ResultComparator:
    """结果对比器 - 用于比较Python模型和RTL仿真结果"""

    def __init__(self, tolerance_cycles: int = 5):
        self.tolerance_cycles = tolerance_cycles
        self.comparisons: List[Dict[str, Any]] = []

    def compare_transaction(
        self,
        python_latency: int,
        python_data: Optional[int],
        rtl_latency: int,
        rtl_data: Optional[int],
        transaction_type: str
    ) -> Dict[str, Any]:
        """比较单个事务结果

        Args:
            python_latency: Python模型延迟
            python_data: Python模型数据
            rtl_latency: RTL延迟
            rtl_data: RTL数据
            transaction_type: 事务类型

        Returns:
            比较结果
        """
        latency_diff = abs(python_latency - rtl_latency)
        latency_match = latency_diff <= self.tolerance_cycles

        data_match = True
        if transaction_type == 'read':
            data_match = (python_data == rtl_data)

        result = {
            'latency_match': latency_match,
            'latency_diff_cycles': latency_diff,
            'data_match': data_match,
            'overall_match': latency_match and data_match,
            'python_latency': python_latency,
            'rtl_latency': rtl_latency,
        }

        self.comparisons.append(result)
        return result

    def get_summary(self) -> Dict[str, Any]:
        """获取对比摘要"""
        if not self.comparisons:
            return {
                'total': 0,
                'matches': 0,
                'mismatches': 0,
                'match_rate': 0.0,
            }

        total = len(self.comparisons)
        matches = sum(1 for c in self.comparisons if c['overall_match'])
        mismatches = total - matches

        avg_latency_diff = sum(c['latency_diff_cycles'] for c in self.comparisons) / total
        max_latency_diff = max(c['latency_diff_cycles'] for c in self.comparisons)

        return {
            'total': total,
            'matches': matches,
            'mismatches': mismatches,
            'match_rate': matches / total,
            'avg_latency_diff': avg_latency_diff,
            'max_latency_diff': max_latency_diff,
        }

    def export_comparison(self, path: str):
        """导出比较结果"""
        with open(path, 'w') as f:
            json.dump({
                'comparisons': self.comparisons,
                'summary': self.get_summary(),
                'tolerance_cycles': self.tolerance_cycles,
            }, f, indent=2)
        logger.info(f"Comparison exported to {path}")


def create_rtl_interface(
    enable_rtl: bool = False,
    trace_enabled: bool = False
) -> RTLInterface:
    """创建RTL接口的便捷函数

    Args:
        enable_rtl: 是否启用RTL仿真
        trace_enabled: 是否启用跟踪

    Returns:
        RTLInterface实例
    """
    config = CoSimConfig(
        enable_rtl=enable_rtl,
        trace_enabled=trace_enabled,
    )
    return RTLInterface(config)
