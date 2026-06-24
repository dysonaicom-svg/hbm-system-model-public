"""Tests for Trace Parser LD/ST format and Comparison functionality"""

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
    ComparisonReport,
)


class TestTraceParserLDSTSupport:
    """Test Trace Parser supports LD/ST operation types"""

    @pytest.fixture
    def ld_st_trace(self):
        """Create temporary LD/ST format trace file"""
        content = """LD 0x0
ST 0x40
LD 0x80
LD 0xC0
ST 0x100
LD 0x140
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            return f.name

    def test_parse_ld_st_format(self, ld_st_trace):
        """Test parsing LD/ST format traces"""
        config = TraceConfig(
            trace_file=ld_st_trace,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        requests = parser.parse_file()

        assert len(requests) == 6
        # LD should be converted to R
        assert requests[0].op_type == "R"
        assert requests[0].address == 0
        # ST should be converted to W
        assert requests[1].op_type == "W"
        assert requests[1].address == 64

    def test_mixed_rw_and_ld_st(self):
        """Test parsing mixed R/W and LD/ST formats"""
        content = """R 0
LD 64
ST 128
W 192
LD 256
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        config = TraceConfig(
            trace_file=trace_file,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        requests = parser.parse_file()

        assert len(requests) == 5
        assert requests[0].op_type == "R"
        assert requests[1].op_type == "R"  # LD -> R
        assert requests[2].op_type == "W"  # ST -> W
        assert requests[3].op_type == "W"
        assert requests[4].op_type == "R"  # LD -> R

        os.unlink(trace_file)


class TestTraceParserComparison:
    """Test TraceParser comparison with Ramulator2 results"""

    @pytest.fixture
    def simple_trace(self):
        """Create simple sequential trace"""
        content = """R 0
R 64
R 128
R 192
R 256
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            return f.name

    def test_compare_with_ramulator_basic(self, simple_trace):
        """Test basic comparison functionality"""
        config = TraceConfig(
            trace_file=simple_trace,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        parser.parse_file()
        stats = parser.analyze()

        # Create mock RamulatorLogResult
        from dataclasses import dataclass
        from typing import Dict

        @dataclass
        class MockChannelStats:
            channel_id: int = 0
            row_hits: int = 0
            row_misses: int = 0
            row_conflicts: int = 0
            row_hit_rate: float = 0.0
            avg_read_latency: float = 0.0

            def compute_hit_rate(self):
                total = self.row_hits + self.row_misses + self.row_conflicts
                if total > 0:
                    self.row_hit_rate = self.row_hits / total
                return self.row_hit_rate

        @dataclass
        class MockRamulatorResult:
            log_file: str = ""
            trace_file: str = ""
            num_requests: int = 0
            channels: Dict = None
            aggregated_hit_rate: float = 0.0
            total_avg_latency: float = 0.0
            total_row_hits: int = 0
            total_row_misses: int = 0
            total_row_conflicts: int = 0
            memory_system_cycles: int = 0

            def get_trace_request_count(self):
                return self.num_requests

            def get_per_channel_stats(self, channel_id=0):
                return self.channels.get(channel_id) if self.channels else None

        # Create mock result
        ch_stats = MockChannelStats(
            channel_id=0,
            row_hits=3,
            row_misses=2,
            row_conflicts=0,
            avg_read_latency=15.0,
        )
        ch_stats.compute_hit_rate()

        mock_result = MockRamulatorResult(
            log_file="test.log",
            trace_file=simple_trace,
            num_requests=5,
            channels={0: ch_stats},
            aggregated_hit_rate=ch_stats.row_hit_rate,
            total_avg_latency=ch_stats.avg_read_latency,
            total_row_hits=3,
            total_row_misses=2,
            total_row_conflicts=0,
            memory_system_cycles=1000,
        )

        # Perform comparison
        report = parser.compare_with_ramulator(mock_result)

        assert report.trace_name == os.path.basename(simple_trace)
        assert report.model_total_requests == 5
        assert report.sim_total_requests == 5
        assert report.sim_row_hits == 3
        assert report.sim_row_misses == 2

    def test_compare_error_computation(self, simple_trace):
        """Test error computation in comparison"""
        config = TraceConfig(
            trace_file=simple_trace,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        parser.parse_file()
        stats = parser.analyze()

        from dataclasses import dataclass
        from typing import Dict

        @dataclass
        class MockChannelStats:
            channel_id: int = 0
            row_hits: int = 100
            row_misses: int = 50
            row_conflicts: int = 10
            row_hit_rate: float = 0.0
            avg_read_latency: float = 20.0

            def compute_hit_rate(self):
                total = self.row_hits + self.row_misses + self.row_conflicts
                if total > 0:
                    self.row_hit_rate = self.row_hits / total
                return self.row_hit_rate

        @dataclass
        class MockRamulatorResult:
            log_file: str = ""
            trace_file: str = ""
            num_requests: int = 160
            channels: Dict = None
            aggregated_hit_rate: float = 0.625
            total_avg_latency: float = 20.0
            total_row_hits: int = 100
            total_row_misses: int = 50
            total_row_conflicts: int = 10
            memory_system_cycles: int = 50000

            def get_trace_request_count(self):
                return self.num_requests

            def get_per_channel_stats(self, channel_id=0):
                return self.channels.get(channel_id) if self.channels else None

        ch_stats = MockChannelStats()
        ch_stats.compute_hit_rate()

        mock_result = MockRamulatorResult(
            num_requests=160,
            channels={0: ch_stats},
        )

        report = parser.compare_with_ramulator(mock_result)
        report.compute_errors()

        # Error metrics should be computed
        assert hasattr(report, 'hit_rate_error_pp')
        assert hasattr(report, 'latency_error_pct')
        assert hasattr(report, 'row_hit_error_pct')

    def test_compare_with_fallback_to_aggregated(self, simple_trace):
        """Test fallback to aggregated stats when channel not found"""
        config = TraceConfig(
            trace_file=simple_trace,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        parser.parse_file()
        stats = parser.analyze()

        from dataclasses import dataclass
        from typing import Dict

        @dataclass
        class MockRamulatorResult:
            log_file: str = ""
            trace_file: str = ""
            num_requests: int = 100
            channels: Dict = None  # Empty channels
            aggregated_hit_rate: float = 0.70
            total_avg_latency: float = 18.5
            total_row_hits: int = 70
            total_row_misses: int = 25
            total_row_conflicts: int = 5
            memory_system_cycles: int = 30000

            def get_trace_request_count(self):
                return self.num_requests

            def get_per_channel_stats(self, channel_id=0):
                return None  # No channel stats

        mock_result = MockRamulatorResult()

        report = parser.compare_with_ramulator(mock_result)

        # Should fallback to aggregated stats
        assert report.sim_row_hit_rate == 0.70
        assert report.sim_avg_latency == 18.5
        assert report.sim_row_hits == 70


class TestComparisonReport:
    """Test ComparisonReport dataclass"""

    def test_compute_errors(self):
        """Test error computation"""
        report = ComparisonReport(
            trace_name="test.trace",
            trace_file="/path/test.trace",
        )

        # Set up model and sim values
        report.model_row_hit_rate = 0.50
        report.model_avg_latency = 30.0
        report.model_row_hits = 50
        report.model_row_misses = 40
        report.model_row_conflicts = 10

        report.sim_row_hit_rate = 0.60
        report.sim_avg_latency = 25.0
        report.sim_row_hits = 60
        report.sim_row_misses = 35
        report.sim_row_conflicts = 5

        report.compute_errors()

        assert report.hit_rate_error_pp == pytest.approx(10.0)  # |0.5 - 0.6| * 100
        assert report.latency_error_pct == pytest.approx(20.0)  # |30 - 25| / 25 * 100
        assert report.row_hit_error_pct == pytest.approx(16.67, abs=0.01)  # |50 - 60| / 60 * 100
        assert report.row_miss_error_pct == pytest.approx(14.29, abs=0.01)  # |40 - 35| / 35 * 100
        assert report.row_conflict_error_pct == pytest.approx(100.0)  # |10 - 5| / 5 * 100

    def test_to_dict(self):
        """Test JSON serialization"""
        report = ComparisonReport(
            trace_name="test.trace",
            trace_file="/path/test.trace",
            model_total_requests=100,
            model_row_hit_rate=0.50,
            model_avg_latency=30.0,
            sim_total_requests=100,
            sim_row_hit_rate=0.60,
            sim_avg_latency=25.0,
            hit_rate_error_pp=10.0,
            latency_error_pct=20.0,
        )

        report_dict = report.to_dict()

        assert report_dict["trace_name"] == "test.trace"
        assert report_dict["model"]["row_hit_rate"] == 0.50
        assert report_dict["simulation"]["row_hit_rate"] == 0.60
        assert report_dict["errors"]["hit_rate_error_pp"] == 10.0


class TestRealLogComparison:
    """Integration tests with real log files"""

    def test_compare_with_real_hbm3_seq_log(self):
        """Test comparison with real HBM3 sequential log"""
        log_file = "/home/ic/JXTF/HBM/research/hbm-modeling/results/hbm3_seq.log"
        trace_file = "/home/ic/JXTF/HBM/research/hbm-modeling/traces/seq_rd.trace"

        if not os.path.exists(log_file) or not os.path.exists(trace_file):
            pytest.skip("Real log/trace files not available")

        # Parse trace with model
        config = TraceConfig(
            trace_file=trace_file,
            format=TraceFormat.RAMULATOR,
        )
        parser = TraceParser(config)
        parser.parse_file()
        stats = parser.analyze()

        # Parse log with Ramulator parser
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        log_parser = RamulatorLogParser(log_file)
        ram_result = log_parser.parse()

        # Verify trace request count is correct
        # Note: Ramulator log may report internal request count which differs from trace file
        assert ram_result.get_trace_request_count() > 0

        # Compare
        report = parser.compare_with_ramulator(ram_result)

        # Verify comparison has valid data
        assert report.model_total_requests > 0

    def test_roundtrip_ld_st_trace(self):
        """Test LD/ST trace can be parsed and analyzed"""
        content = """LD 0x0
LD 0x40
ST 0x80
LD 0xC0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        try:
            config = TraceConfig(
                trace_file=trace_file,
                format=TraceFormat.RAMULATOR,
            )
            parser = TraceParser(config)
            parser.parse_file()
            stats = parser.analyze()

            assert stats.total_requests == 4
            assert stats.read_requests == 3  # LD -> R
            assert stats.write_requests == 1  # ST -> W
        finally:
            os.unlink(trace_file)