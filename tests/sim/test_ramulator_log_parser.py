"""Tests for Ramulator2 Log Parser Module"""

import pytest
import os
import tempfile
from sim.trace.parser import ComparisonReport


class TestRamulatorLogParser:
    """Ramulator Log Parser Tests"""

    @pytest.fixture
    def sample_log_content(self):
        """Sample Ramulator2 log content for testing"""
        return """[Ramulator::LoadStoreTrace] [info] Loading trace file /path/to/trace.trace ...
[Ramulator::LoadStoreTrace] [info] Loaded 10000 lines.
Frontend:
  impl: LoadStoreTrace

MemorySystem:
  impl: GenericDRAM
  total_num_other_requests: 0
  total_num_write_requests: 0
  total_num_read_requests: 10000
  memory_system_cycles: 92181
  DRAM:
    impl: HBM3
  AddrMapper:
    impl: ChRaBaRoCo


  Controller:
    impl: Generic
    id: Channel 0
    avg_read_latency_0: 12.9045172
    read_queue_len_avg_0: 34.1867943
    write_queue_len_0: 0
    queue_len_0: 3151373
    num_other_reqs_0: 0
    num_write_reqs_0: 0
    read_latency_0: 3172124
    priority_queue_len_avg_0: 0
    row_hits_0: 6229
    priority_queue_len_0: 0
    row_misses_0: 2493
    row_conflicts_0: 1246
    read_row_misses_0: 2493
    queue_len_avg_0: 34.1867943
    read_row_conflicts_core_0: 0
    read_row_hits_0: 6229
    write_queue_len_avg_0: 0
    read_row_conflicts_0: 1246
    write_row_misses_0: 0
    write_row_conflicts_0: 0
    read_queue_len_0: 3151373
    write_row_hits_0: 0
    read_row_hits_core_0: 0
    read_row_misses_core_0: 0
    num_read_reqs_0: 245815
    Scheduler:
      impl: FRFCFS
    RefreshManager:
      impl: AllBank
    RowPolicy:
      impl: OpenRowPolicy
"""

    @pytest.fixture
    def sample_log_file(self, sample_log_content):
        """Create a temporary log file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(sample_log_content)
            f.flush()
            return f.name

    def test_parse_log_file(self, sample_log_file):
        """Test parsing a Ramulator2 log file"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(sample_log_file)
        result = parser.parse()

        assert result.log_file == sample_log_file
        assert result.trace_file == "/path/to/trace.trace"
        assert result.num_requests == 10000  # From "Loaded X lines"
        assert result.memory_system_cycles == 92181
        assert result.dram_impl == "HBM3"
        assert result.addr_mapper_impl == "ChRaBaRoCo"

    def test_parse_channel_stats(self, sample_log_file):
        """Test parsing channel statistics"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(sample_log_file)
        result = parser.parse()

        assert 0 in result.channels
        ch = result.channels[0]
        assert ch.row_hits == 6229
        assert ch.row_misses == 2493
        assert ch.row_conflicts == 1246
        assert ch.avg_read_latency == 12.9045172
        assert ch.row_hit_rate == pytest.approx(6229 / (6229 + 2493 + 1246))

    def test_compute_aggregates(self, sample_log_file):
        """Test computing aggregated statistics"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(sample_log_file)
        result = parser.parse()

        assert result.total_row_hits == 6229
        assert result.total_row_misses == 2493
        assert result.total_row_conflicts == 1246
        # 6229 / (6229 + 2493 + 1246) = 6229 / 9968
        assert result.aggregated_hit_rate == pytest.approx(6229 / 9968)

    def test_get_trace_request_count(self, sample_log_file):
        """Test get_trace_request_count returns correct value"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(sample_log_file)
        result = parser.parse()

        # Should return the "Loaded X lines" count, not the internal burst count
        assert result.get_trace_request_count() == 10000

    def test_get_per_channel_stats(self, sample_log_file):
        """Test get_per_channel_stats helper method"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(sample_log_file)
        result = parser.parse()

        # Valid channel
        ch = result.get_per_channel_stats(0)
        assert ch is not None
        assert ch.row_hits == 6229

        # Invalid channel
        ch = result.get_per_channel_stats(99)
        assert ch is None

    def test_to_dict(self, sample_log_file):
        """Test JSON serialization"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(sample_log_file)
        result = parser.parse()
        result_dict = result.to_dict()

        assert result_dict["log_file"] == sample_log_file
        assert result_dict["num_requests"] == 10000
        assert result_dict["total_row_hits"] == 6229
        assert "channels" in result_dict

    def test_summary(self, sample_log_file):
        """Test summary generation"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(sample_log_file)
        result = parser.parse()
        summary = result.summary()

        assert "Ramulator2 Log" in summary
        assert "10,000" in summary  # Summary uses comma formatting
        assert "HBM3" in summary
        assert "6,229" in summary  # Uses comma formatting

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises error"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser("/nonexistent/log.file")
        with pytest.raises(FileNotFoundError):
            parser.parse()


class TestMultiChannelLog:
    """Tests for multi-channel log parsing"""

    @pytest.fixture
    def multi_channel_log(self):
        """Multi-channel log content"""
        return """[Ramulator::LoadStoreTrace] [info] Loading trace file /path/to/trace.trace ...
[Ramulator::LoadStoreTrace] [info] Loaded 5000 lines.
MemorySystem:
  impl: GenericDRAM
  total_num_read_requests: 5000
  memory_system_cycles: 50000
  DRAM:
    impl: HBM3

  Controller:
    impl: Generic
    id: Channel 0
    row_hits_0: 2000
    row_misses_0: 1000
    row_conflicts_0: 500
    avg_read_latency_0: 10.5
    queue_len_avg_0: 20.0

  Controller:
    impl: Generic
    id: Channel 1
    row_hits_1: 1500
    row_misses_1: 1200
    row_conflicts_1: 300
    avg_read_latency_1: 11.2
    queue_len_avg_1: 25.0
"""

    @pytest.fixture
    def multi_channel_log_file(self, multi_channel_log):
        """Create a temporary multi-channel log file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(multi_channel_log)
            f.flush()
            return f.name

    def test_parse_multi_channel(self, multi_channel_log_file):
        """Test parsing multi-channel log"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(multi_channel_log_file)
        result = parser.parse()

        assert 0 in result.channels
        assert 1 in result.channels

        # Verify channel 0 stats
        ch0 = result.channels[0]
        assert ch0.row_hits == 2000
        assert ch0.row_misses == 1000
        assert ch0.row_conflicts == 500

        # Verify channel 1 stats
        ch1 = result.channels[1]
        assert ch1.row_hits == 1500
        assert ch1.row_misses == 1200
        assert ch1.row_conflicts == 300

    def test_aggregated_multi_channel(self, multi_channel_log_file):
        """Test aggregated stats across channels"""
        import sys
        sys.path.insert(0, "/home/ic/JXTF/HBM/research/hbm-modeling/scripts")
        from parse_ramulator_log import RamulatorLogParser

        parser = RamulatorLogParser(multi_channel_log_file)
        result = parser.parse()

        # Aggregated hits
        assert result.total_row_hits == 3500  # 2000 + 1500
        assert result.total_row_misses == 2200  # 1000 + 1200
        assert result.total_row_conflicts == 800  # 500 + 300

        # Average latency should be average of both channels
        assert result.total_avg_latency == pytest.approx((10.5 + 11.2) / 2)