"""
RTL Interface Tests
测试 RTL 协同仿真接口的功能
"""

import pytest
import sys
import os
import tempfile
import json

sys.path.insert(0, '/home/ic/JXTF/HBM4')

from sim.rtl_interface import (
    RTLInterface,
    CoSimConfig,
    CoSimStats,
    RTLTransaction,
    TransactionType,
    TransactionStatus,
    ResultComparator,
    create_rtl_interface,
)


class TestRTLTransaction:
    """测试 RTL 事务"""

    def test_transaction_creation(self):
        """测试事务创建"""
        trans = RTLTransaction(
            id=0,
            transaction_type=TransactionType.READ,
            address=0x1000,
            channel=0,
            bank=1,
            cycle=100,
        )
        assert trans.id == 0
        assert trans.transaction_type == TransactionType.READ
        assert trans.address == 0x1000
        assert trans.channel == 0
        assert trans.bank == 1

    def test_transaction_to_dict(self):
        """测试事务序列化"""
        trans = RTLTransaction(
            id=1,
            transaction_type=TransactionType.WRITE,
            address=0x2000,
            data=0xDEADBEEF,
            channel=2,
            bank=3,
            cycle=200,
        )
        d = trans.to_dict()
        assert d['id'] == 1
        assert d['type'] == 'write'
        assert d['address'] == '0x2000'
        assert d['data'] == '0xdeadbeef'


class TestCoSimConfig:
    """测试协同仿真配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = CoSimConfig()
        assert config.enable_rtl is False
        assert config.rtl_simulator == "verilator"
        assert config.timeout_cycles == 100000

    def test_custom_config(self):
        """测试自定义配置"""
        config = CoSimConfig(
            enable_rtl=True,
            rtl_simulator="modelsim",
            trace_enabled=True,
            dump_waveform=True,
        )
        assert config.enable_rtl is True
        assert config.rtl_simulator == "modelsim"
        assert config.trace_enabled is True
        assert config.dump_waveform is True


class TestCoSimStats:
    """测试协同仿真统计"""

    def test_stats_initialization(self):
        """测试统计初始化"""
        stats = CoSimStats()
        assert stats.total_transactions == 0
        assert stats.python_completed == 0
        assert stats.rtl_completed == 0

    def test_stats_to_dict(self):
        """测试统计序列化"""
        stats = CoSimStats(
            total_transactions=100,
            python_completed=50,
            rtl_completed=50,
            matched_results=45,
        )
        d = stats.to_dict()
        assert d['total_transactions'] == 100
        assert d['python_completed'] == 50
        assert d['rtl_completed'] == 50
        assert d['matched_results'] == 45


class TestRTLInterface:
    """测试 RTL 接口"""

    def test_interface_creation(self):
        """测试接口创建"""
        iface = RTLInterface()
        assert iface.current_cycle == 0
        assert len(iface.transactions) == 0

    def test_inject_read_transaction(self):
        """测试注入读事务"""
        iface = RTLInterface()
        tid = iface.inject_read_transaction(
            address=0x1000,
            channel=0,
            bank=1,
            cycle=100,
        )
        assert tid == 0
        assert tid in iface.transactions
        trans = iface.transactions[tid]
        assert trans.transaction_type == TransactionType.READ

    def test_inject_write_transaction(self):
        """测试注入写事务"""
        iface = RTLInterface()
        tid = iface.inject_write_transaction(
            address=0x2000,
            data=0xDEADBEEF,
            channel=1,
            bank=2,
        )
        assert tid == 0
        trans = iface.transactions[tid]
        assert trans.transaction_type == TransactionType.WRITE
        assert trans.data == 0xDEADBEEF

    def test_inject_command_transaction(self):
        """测试注入命令事务"""
        iface = RTLInterface()
        tid = iface.inject_command_transaction(
            command="activate",
            address=0x3000,
            channel=0,
            bank=1,
        )
        assert tid == 0
        trans = iface.transactions[tid]
        assert trans.transaction_type == TransactionType.ACTIVATE

    def test_record_python_result(self):
        """测试记录 Python 结果"""
        iface = RTLInterface()
        iface.record_python_result(
            tid=0,
            latency_cycles=100,
            data=0x12345678,
        )
        assert 0 in iface.python_results
        assert iface.python_results[0]['latency_cycles'] == 100
        assert iface.python_results[0]['data'] == 0x12345678

    def test_compare_results(self):
        """测试结果对比"""
        iface = RTLInterface()

        # 注入读事务
        iface.inject_read_transaction(address=0x1000, cycle=100)
        trans = iface.transactions[0]
        trans.latency_cycles = 100
        trans.response_data = 0x1234  # 读事务需要设置响应数据

        # 记录 Python 结果 - 延迟相同，数据相同
        iface.record_python_result(tid=0, latency_cycles=100, data=0x1234)

        # 对比结果 - RTL延迟为100, Python延迟为100，差异为0
        is_match, diff_info = iface.compare_results(0)
        assert is_match is True  # 延迟差异为0，数据匹配

    def test_compare_results_mismatch(self):
        """测试结果不匹配"""
        iface = RTLInterface()

        # 注入事务
        iface.inject_read_transaction(address=0x1000, cycle=100)
        trans = iface.transactions[0]
        trans.latency_cycles = 100

        # 记录不同的 Python 结果
        iface.record_python_result(tid=0, latency_cycles=200)

        # 对比结果
        is_match, diff_info = iface.compare_results(0)
        assert is_match is False
        assert diff_info['latency_diff'] == 100

    def test_tick(self):
        """测试周期推进"""
        iface = RTLInterface()
        cycle = iface.tick()
        assert cycle == 1
        cycle = iface.tick()
        assert cycle == 2

    def test_get_pending_transactions(self):
        """测试获取待处理事务"""
        iface = RTLInterface()
        iface.inject_read_transaction(address=0x1000)
        pending = iface.get_pending_transactions()
        assert len(pending) == 1

    def test_get_completed_transactions(self):
        """测试获取已完成事务"""
        iface = RTLInterface()
        iface.inject_read_transaction(address=0x1000)
        trans = iface.transactions[0]
        trans.status = TransactionStatus.COMPLETED
        completed = iface.get_completed_transactions()
        assert len(completed) == 1

    def test_get_transaction(self):
        """测试获取指定事务"""
        iface = RTLInterface()
        tid = iface.inject_read_transaction(address=0x1000)
        trans = iface.get_transaction(tid)
        assert trans is not None
        assert trans.id == tid

    def test_get_stats(self):
        """测试获取统计"""
        iface = RTLInterface()
        iface.inject_read_transaction(address=0x1000)
        iface.inject_read_transaction(address=0x2000)
        stats = iface.get_stats()
        assert stats.total_transactions == 2

    def test_enable_waveform_dump(self):
        """测试启用波形转储"""
        iface = RTLInterface()
        iface.enable_waveform_dump("/tmp/waves.vcd")
        assert iface.config.dump_waveform is True
        assert iface.waveform_path == "/tmp/waves.vcd"

    def test_disable_waveform_dump(self):
        """测试禁用波形转储"""
        iface = RTLInterface()
        iface.enable_waveform_dump()
        iface.disable_waveform_dump()
        assert iface.config.dump_waveform is False

    def test_export_trace(self):
        """测试导出跟踪"""
        iface = RTLInterface()
        iface.inject_read_transaction(address=0x1000)
        iface.record_python_result(tid=0, latency_cycles=100)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            iface.export_trace(temp_path)
            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert 'transactions' in data
            assert 'python_results' in data
        finally:
            os.unlink(temp_path)

    def test_import_trace(self):
        """测试导入跟踪"""
        iface = RTLInterface()

        # 创建临时跟踪文件
        trace_data = {
            'transactions': [{
                'id': 0,
                'type': 'read',
                'address': '0x1000',
                'data': None,
                'channel': 0,
                'bank': 0,
                'cycle': 100,
                'status': 'completed',
                'latency_cycles': 100,
                'response_data': None,
                'timestamp_ns': 1234567890.0,
            }],
            'python_results': {
                '0': {'latency_cycles': 100, 'data': None, 'timestamp_ns': 1234567890.0}
            },
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(trace_data, f)
            temp_path = f.name

        try:
            iface.import_trace(temp_path)
            assert len(iface.transactions) == 1
            # python_results 的键是字符串 "0"
            assert "0" in iface.python_results or 0 in iface.python_results
        finally:
            os.unlink(temp_path)

    def test_get_summary(self):
        """测试获取摘要"""
        iface = RTLInterface()
        iface.inject_read_transaction(address=0x1000)
        summary = iface.get_summary()
        assert 'config' in summary
        assert 'stats' in summary
        assert summary['pending_count'] == 1


class TestResultComparator:
    """测试结果对比器"""

    def test_comparator_creation(self):
        """测试对比器创建"""
        comp = ResultComparator(tolerance_cycles=10)
        assert comp.tolerance_cycles == 10
        assert len(comp.comparisons) == 0

    def test_compare_transaction(self):
        """测试事务对比"""
        comp = ResultComparator(tolerance_cycles=5)
        result = comp.compare_transaction(
            python_latency=100,
            python_data=0x1234,
            rtl_latency=103,
            rtl_data=0x1234,
            transaction_type='read',
        )
        assert result['latency_match'] is True
        assert result['data_match'] is True
        assert result['overall_match'] is True

    def test_compare_transaction_data_mismatch(self):
        """测试数据不匹配"""
        comp = ResultComparator(tolerance_cycles=5)
        result = comp.compare_transaction(
            python_latency=100,
            python_data=0x1234,
            rtl_latency=100,
            rtl_data=0x5678,
            transaction_type='read',
        )
        assert result['data_match'] is False
        assert result['overall_match'] is False

    def test_compare_transaction_latency_mismatch(self):
        """测试延迟不匹配"""
        comp = ResultComparator(tolerance_cycles=5)
        result = comp.compare_transaction(
            python_latency=100,
            python_data=0x1234,
            rtl_latency=200,
            rtl_data=0x1234,
            transaction_type='read',
        )
        assert result['latency_match'] is False
        assert result['latency_diff_cycles'] == 100

    def test_get_summary(self):
        """测试获取摘要"""
        comp = ResultComparator(tolerance_cycles=5)
        comp.compare_transaction(100, 0x1234, 103, 0x1234, 'read')
        comp.compare_transaction(100, 0x1234, 200, 0x1234, 'read')
        summary = comp.get_summary()
        assert summary['total'] == 2
        assert summary['matches'] == 1
        assert summary['mismatches'] == 1
        assert summary['match_rate'] == 0.5

    def test_get_summary_empty(self):
        """测试空摘要"""
        comp = ResultComparator()
        summary = comp.get_summary()
        assert summary['total'] == 0
        assert summary['match_rate'] == 0.0

    def test_export_comparison(self):
        """测试导出对比结果"""
        comp = ResultComparator(tolerance_cycles=5)
        comp.compare_transaction(100, 0x1234, 103, 0x1234, 'read')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            comp.export_comparison(temp_path)
            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert 'comparisons' in data
            assert 'summary' in data
        finally:
            os.unlink(temp_path)


class TestCreateRTLInterface:
    """测试创建 RTL 接口函数"""

    def test_create_rtl_interface_default(self):
        """测试默认创建"""
        iface = create_rtl_interface()
        assert isinstance(iface, RTLInterface)
        assert iface.config.enable_rtl is False
        assert iface.config.trace_enabled is False

    def test_create_rtl_interface_with_rtl(self):
        """测试启用 RTL 创建"""
        iface = create_rtl_interface(enable_rtl=True, trace_enabled=True)
        assert iface.config.enable_rtl is True
        assert iface.config.trace_enabled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
