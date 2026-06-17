# tests/sim/test_trace_replayer.py
"""
Tests for TraceReplayer module
"""
import pytest
import tempfile
import os
from sim.trace_replayer import TraceReplayer, TraceFormat, TraceRequest, load_trace


class TestTraceReplayerLDST:
    """Test LD/ST format parsing"""

    @pytest.fixture
    def ld_st_trace(self):
        """Create temporary LD/ST trace file"""
        content = """LD 0x0
ST 0x40
LD 0x80
# This is a comment
LD 0xC0
ST 0x100
LD 0x140
"""
        # Total: 6 LD/ST commands (comment is skipped)
        # 4 LD (read) + 2 ST (write)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            return f.name

    def test_load_ld_st_format(self, ld_st_trace):
        """Test loading LD/ST format"""
        replayer = TraceReplayer(ld_st_trace, TraceFormat.RAMULATOR_LD_ST)
        count = replayer.load()

        assert count == 6  # 6 valid LD/ST commands (comment is skipped)
        assert replayer.read_count == 4  # 4 LD
        assert replayer.write_count == 2  # 2 ST

    def test_addresses_parsed_correctly(self, ld_st_trace):
        """Test address parsing"""
        replayer = TraceReplayer(ld_st_trace, TraceFormat.RAMULATOR_LD_ST)
        replayer.load()

        requests = list(replayer.requests())
        assert requests[0].addr == 0x0
        assert requests[1].addr == 0x40
        assert requests[2].addr == 0x80

    def test_read_write_detection(self, ld_st_trace):
        """Test read/write detection"""
        replayer = TraceReplayer(ld_st_trace, TraceFormat.RAMULATOR_LD_ST)
        replayer.load()

        requests = list(replayer.requests())
        assert requests[0].is_read is True   # LD
        assert requests[1].is_read is False  # ST
        assert requests[2].is_read is True   # LD

    def test_load_trace_convenience_function(self, ld_st_trace):
        """Test convenience function"""
        replayer = load_trace(ld_st_trace)
        assert replayer.total_requests == 6  # 6 LD/ST commands

    def test_request_id_assignment(self, ld_st_trace):
        """Test that request IDs are assigned correctly"""
        replayer = TraceReplayer(ld_st_trace, TraceFormat.RAMULATOR_LD_ST)
        replayer.load()

        requests = list(replayer.requests())
        # Request IDs are assigned from line numbers (0-indexed)
        # Line 3 is comment, so no request_id=3
        # Line numbers: 0=LD, 1=ST, 2=LD, 3=comment, 4=LD, 5=ST, 6=LD
        assert requests[0].request_id == 0
        assert requests[1].request_id == 1
        assert requests[2].request_id == 2
        assert requests[3].request_id == 4  # Line 3 is skipped (comment)


class TestTraceReplayerRW:
    """Test R/W format parsing"""

    @pytest.fixture
    def rw_trace(self):
        """Create temporary R/W trace file"""
        content = """R 0
R 64
W 128
R 256
W 512
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            return f.name

    def test_load_rw_format(self, rw_trace):
        """Test loading R/W format"""
        replayer = TraceReplayer(rw_trace, TraceFormat.RAMULATOR_R_W)
        count = replayer.load()

        assert count == 5
        assert replayer.read_count == 3  # 3 R
        assert replayer.write_count == 2  # 2 W

    def test_rw_is_read_detection(self, rw_trace):
        """Test R/W read/write detection"""
        replayer = TraceReplayer(rw_trace, TraceFormat.RAMULATOR_R_W)
        replayer.load()

        requests = list(replayer.requests())
        assert requests[0].is_read is True   # R
        assert requests[1].is_read is True   # R
        assert requests[2].is_read is False  # W
        assert requests[3].is_read is True   # R
        assert requests[4].is_read is False  # W

    def test_rw_address_parsing(self, rw_trace):
        """Test decimal address parsing"""
        replayer = TraceReplayer(rw_trace, TraceFormat.RAMULATOR_R_W)
        replayer.load()

        requests = list(replayer.requests())
        assert requests[0].addr == 0   # decimal 0
        assert requests[1].addr == 64  # decimal 64
        assert requests[2].addr == 128  # decimal 128
        assert requests[3].addr == 256  # decimal 256
        assert requests[4].addr == 512  # decimal 512


class TestTraceFormat:
    """Test TraceFormat enum"""

    def test_trace_format_values(self):
        """Test TraceFormat enum values"""
        assert TraceFormat.RAMULATOR_LD_ST.value == "ld_st"
        assert TraceFormat.RAMULATOR_R_W.value == "r_w"
        assert TraceFormat.HBMTRACE.value == "hbmtrace"

    def test_trace_format_count(self):
        """Test number of trace formats"""
        assert len(TraceFormat) == 3


class TestTraceRequest:
    """Test TraceRequest dataclass"""

    def test_trace_request_creation(self):
        """Test TraceRequest creation"""
        req = TraceRequest(
            request_id=0,
            addr=0x1000,
            is_read=True
        )
        assert req.request_id == 0
        assert req.addr == 0x1000
        assert req.is_read is True
        assert req.timestamp is None

    def test_trace_request_with_timestamp(self):
        """Test TraceRequest with optional timestamp"""
        req = TraceRequest(
            request_id=0,
            addr=0x1000,
            is_read=False,
            timestamp=100
        )
        assert req.timestamp == 100


class TestTraceReplayerEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_lines_skipped(self):
        """Test that empty lines are skipped"""
        content = """LD 0x100

ST 0x200

LD 0x300
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        try:
            replayer = TraceReplayer(trace_file, TraceFormat.RAMULATOR_LD_ST)
            count = replayer.load()
            assert count == 3
        finally:
            os.unlink(trace_file)

    def test_hex_address_parsing(self):
        """Test hex address parsing (0x prefix)"""
        content = """LD 0x1000
ST 0x1FFF
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        try:
            replayer = TraceReplayer(trace_file, TraceFormat.RAMULATOR_LD_ST)
            replayer.load()
            requests = list(replayer.requests())
            assert requests[0].addr == 0x1000
            assert requests[1].addr == 0x1FFF
        finally:
            os.unlink(trace_file)

    def test_lowercase_operations(self):
        """Test lowercase operation parsing"""
        content = """ld 0x100
st 0x200
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        try:
            replayer = TraceReplayer(trace_file, TraceFormat.RAMULATOR_LD_ST)
            replayer.load()
            requests = list(replayer.requests())
            assert requests[0].is_read is True   # ld
            assert requests[1].is_read is False  # st
        finally:
            os.unlink(trace_file)

    def test_invalid_address_handling(self):
        """Test handling of invalid addresses"""
        content = """LD 0x100
LD invalid
ST 0x200
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        try:
            replayer = TraceReplayer(trace_file, TraceFormat.RAMULATOR_LD_ST)
            count = replayer.load()
            # Should only parse valid lines (LD 0x100 and ST 0x200)
            assert count == 2
        finally:
            os.unlink(trace_file)

    def test_read_count_property(self):
        """Test read_count property"""
        content = """LD 0x100
ST 0x200
LD 0x300
R 0x400
W 0x500
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        try:
            replayer = TraceReplayer(trace_file, TraceFormat.RAMULATOR_LD_ST)
            replayer.load()
            assert replayer.read_count == 3  # LD + LD + R
            assert replayer.write_count == 2  # ST + W
        finally:
            os.unlink(trace_file)


class TestTraceReplayerIterator:
    """Test iterator functionality"""

    def test_requests_iterator(self):
        """Test that requests() returns an iterator"""
        content = """LD 0x100
ST 0x200
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        try:
            replayer = TraceReplayer(trace_file, TraceFormat.RAMULATOR_LD_ST)
            replayer.load()

            # Test iterator
            it = replayer.requests()
            req1 = next(it)
            req2 = next(it)

            assert isinstance(req1, TraceRequest)
            assert isinstance(req2, TraceRequest)
            assert req1.addr == 0x100
            assert req2.addr == 0x200

            # Should raise StopIteration when exhausted
            with pytest.raises(StopIteration):
                next(it)
        finally:
            os.unlink(trace_file)

    def test_iterate_multiple_times(self):
        """Test that we can iterate multiple times"""
        content = """LD 0x100
ST 0x200
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            trace_file = f.name

        try:
            replayer = TraceReplayer(trace_file, TraceFormat.RAMULATOR_LD_ST)
            replayer.load()

            # First iteration
            reqs1 = list(replayer.requests())
            assert len(reqs1) == 2

            # Second iteration should work too
            reqs2 = list(replayer.requests())
            assert len(reqs2) == 2
            assert reqs1[0].addr == reqs2[0].addr
        finally:
            os.unlink(trace_file)
