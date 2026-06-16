"""Tests for Trace Parser Module"""

import pytest
import os
import tempfile
from sim.trace.parser import (
    TraceParser,
    TraceConfig,
    TraceRequest,
    TraceStats,
    TraceFormat,
    HBMVersion,
    parse_trace_file,
    parse_directory,
)


class TestTraceParser:
    """Trace Parser 测试"""

    @pytest.fixture
    def ramulator_trace(self):
        """创建临时 Ramulator 格式 trace 文件"""
        content = """R 0
R 64
R 128
W 192
R 256
W 320
R 384
R 448
R 512
W 576
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            return f.name

    @pytest.fixture
    def extended_trace(self):
        """创建临时扩展格式 trace 文件"""
        content = """0 0
1 4096
2 8192
0 12288
1 16384
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            return f.name

    def test_parse_ramulator_format(self, ramulator_trace):
        """测试 Ramulator 格式解析"""
        config = TraceConfig(
            trace_file=ramulator_trace,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        requests = parser.parse_file()

        assert len(requests) == 10
        assert requests[0].op_type == "R"
        assert requests[0].address == 0
        assert requests[3].op_type == "W"
        assert requests[3].address == 192

    def test_parse_extended_format(self, extended_trace):
        """测试扩展格式解析"""
        config = TraceConfig(
            trace_file=extended_trace,
            format=TraceFormat.EXTENDED,
        )
        parser = TraceParser(config)
        requests = parser.parse_file()

        assert len(requests) == 5
        assert requests[0].core_id == 0
        assert requests[0].address == 0
        assert requests[1].core_id == 1

    def test_analyze_statistics(self, ramulator_trace):
        """测试统计信息分析"""
        config = TraceConfig(
            trace_file=ramulator_trace,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        parser.parse_file()
        stats = parser.analyze()

        assert stats.total_requests == 10
        assert stats.read_requests == 7
        assert stats.write_requests == 3

    def test_address_decoding(self):
        """测试地址解码"""
        config = TraceConfig(
            trace_file="dummy.trace",
            format=TraceFormat.RAMULATOR,
            channels=8,
            pseudo_channels=16,
            banks_per_channel=4,
            bank_groups=2,
        )
        parser = TraceParser(config)

        decoded = parser._decode_address(0)
        assert "channel" in decoded
        assert "bank" in decoded
        assert "row" in decoded

    def test_sequential_detection(self):
        """测试顺序访问检测"""
        content = """R 0
R 64
R 128
R 192
R 256
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        config = TraceConfig(trace_file=trace_file, format=TraceFormat.RAMULATOR)
        parser = TraceParser(config)
        parser.parse_file()
        stats = parser.analyze()

        # 5 个请求，4 个是顺序访问
        assert stats.sequential_count >= 3
        os.unlink(trace_file)

    def test_stride_detection(self):
        """测试 stride 访问检测"""
        content = """R 0
R 4096
R 8192
R 12288
R 16384
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        config = TraceConfig(
            trace_file=trace_file,
            format=TraceFormat.RAMULATOR,
            cache_line_size=64,
        )
        parser = TraceParser(config)
        parser.parse_file()
        stats = parser.analyze()

        assert stats.stride_count >= 3
        os.unlink(trace_file)

    def test_parse_file_not_found(self):
        """测试文件不存在"""
        config = TraceConfig(trace_file="/nonexistent/file.trace")
        parser = TraceParser(config)

        with pytest.raises(FileNotFoundError):
            parser.parse_file()

    def test_skip_comments_and_empty_lines(self):
        """测试跳过注释和空行"""
        content = """# This is a comment
R 0

R 64
# Another comment
W 128
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        config = TraceConfig(trace_file=trace_file, format=TraceFormat.RAMULATOR)
        parser = TraceParser(config)
        requests = parser.parse_file()

        assert len(requests) == 3
        os.unlink(trace_file)


class TestParseDirectory:
    """目录解析测试"""

    def test_parse_directory(self, tmp_path):
        """测试目录解析"""
        # 创建测试 trace 文件
        for name in ["test1.trace", "test2.trace"]:
            with open(tmp_path / name, 'w') as f:
                f.write("R 0\nR 64\nW 128\n")

        results = parse_directory(str(tmp_path), pattern="*.trace", print_summary=False)

        assert len(results) == 2


class TestGenerateSummaryTable:
    """Summary 表格生成测试"""

    def test_generate_table(self):
        """测试表格生成"""
        from sim.trace.parser import generate_summary_table

        stats = TraceStats(
            total_requests=100,
            read_requests=70,
            write_requests=30,
            estimated_row_hit_rate=0.85,
            estimated_avg_latency=35.5,
        )

        results = {"/path/to/trace.trace": stats}
        table = generate_summary_table(results)

        assert "trace.trace" in table
        assert "100" in table
        assert "85.00%" in table
        assert "35.5 cycles" in table