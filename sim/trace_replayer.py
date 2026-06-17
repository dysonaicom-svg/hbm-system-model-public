# sim/trace_replayer.py
"""
Trace Replayer for HBM3 Verification
Reuse Ramulator2 generated trace files for Python model simulation
"""
import logging
from dataclasses import dataclass
from typing import List, Iterator, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class TraceFormat(Enum):
    """Supported trace formats"""
    RAMULATOR_LD_ST = "ld_st"  # LD 0x... / ST 0x...
    RAMULATOR_R_W = "r_w"       # R 0x... / W 0x...
    HBMTRACE = "hbmtrace"       # Custom format


@dataclass
class TraceRequest:
    """Request from trace file"""
    request_id: int
    addr: int
    is_read: bool
    timestamp: Optional[int] = None  # Optional arrival timestamp


class TraceReplayer:
    """Trace replayer"""

    def __init__(self, trace_file: str, trace_format: TraceFormat = TraceFormat.RAMULATOR_LD_ST):
        self.trace_file = trace_file
        self.trace_format = trace_format
        self._requests: List[TraceRequest] = []

    def load(self) -> int:
        """Load trace file, return number of requests"""
        self._requests = []
        with open(self.trace_file, 'r') as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                req = self._parse_line(line, line_num)
                if req:
                    self._requests.append(req)

        logger.info(f"Loaded {len(self._requests)} requests from {self.trace_file}")
        return len(self._requests)

    def _parse_line(self, line: str, line_num: int) -> Optional[TraceRequest]:
        """Parse single trace line"""
        parts = line.split()
        if len(parts) < 2:
            return None

        op = parts[0].upper()
        try:
            addr = int(parts[1], 0)  # Support 0x prefix and decimal
        except ValueError:
            logger.warning(f"Invalid address at line {line_num}: {parts[1]}")
            return None

        is_read = op in ('LD', 'R', 'READ')

        return TraceRequest(
            request_id=line_num,
            addr=addr,
            is_read=is_read
        )

    def requests(self) -> Iterator[TraceRequest]:
        """Return request iterator"""
        return iter(self._requests)

    @property
    def total_requests(self) -> int:
        return len(self._requests)

    @property
    def read_count(self) -> int:
        return sum(1 for r in self._requests if r.is_read)

    @property
    def write_count(self) -> int:
        return sum(1 for r in self._requests if not r.is_read)


def load_trace(trace_file: str, trace_format: TraceFormat = TraceFormat.RAMULATOR_LD_ST) -> TraceReplayer:
    """Convenience function: load trace"""
    replayer = TraceReplayer(trace_file, trace_format)
    replayer.load()
    return replayer
