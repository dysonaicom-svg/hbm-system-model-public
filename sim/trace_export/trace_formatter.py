# sim/trace_export/trace_formatter.py
"""
Chrome Tracing Format Export for HBM Simulation
Export trace data to Chrome Tracing JSON format for trace viewer analysis
"""
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Iterator
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ChromeCategory(Enum):
    """Chrome trace categories"""
    HBM_CONTROLLER = "HBM Controller"
    HBM_DRAM = "HBM DRAM"
    HBM_COMMAND = "HBM Command"
    HBM_QUEUE = "HBM Queue"
    HBM_SCHEDULER = "HBM Scheduler"
    HBM_CHANNEL = "HBM Channel"
    HBM_REFRESH = "HBM Refresh"
    HBM_TRAFFIC = "HBM Traffic"


@dataclass
class ChromeTraceEvent:
    """Single trace event in Chrome Tracing format

    Attributes:
        name: Event name (displayed in trace viewer)
        category: Event category
        timestamp_us: Event timestamp in microseconds
        duration_us: Duration in microseconds (0 for instant events)
        tid: Thread/queue identifier
        pid: Process identifier
        args: Optional event arguments
    """
    name: str
    category: str
    timestamp_us: float
    duration_us: float = 0.0
    tid: int = 0
    pid: int = 1
    args: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Chrome Tracing JSON format"""
        if self.duration_us > 0:
            # Duration event (X)
            return {
                "name": self.name,
                "cat": self.category,
                "ts": self.timestamp_us,
                "dur": self.duration_us,
                "tid": self.tid,
                "pid": self.pid,
                "ph": "X",
                "args": self.args or {},
            }
        else:
            # Instant event (i)
            return {
                "name": self.name,
                "cat": self.category,
                "ts": self.timestamp_us,
                "tid": self.tid,
                "pid": self.pid,
                "ph": "i",
                "s": "t",  # thread scope
                "args": self.args or {},
            }

    def to_flow_event(self, flow_id: int, step: str = "start") -> Dict[str, Any]:
        """Convert to flow event for request tracking

        Args:
            flow_id: Unique flow identifier
            step: Step in flow ("start", "step", "end")

        Returns:
            Flow event dictionary
        """
        ph_map = {"start": "s", "step": "t", "end": "f"}
        return {
            "name": self.name,
            "cat": self.category,
            "ts": self.timestamp_us,
            "tid": self.tid,
            "pid": self.pid,
            "ph": ph_map.get(step, "t"),
            "id": str(flow_id),
            "args": self.args or {},
        }


class ChromeTraceFormatter:
    """Format HBM trace data for Chrome Tracing / Perfetto viewer

    Chrome Tracing format is the original JSON format that Perfetto also
    supports. This formatter provides:
    - Duration events for request latency visualization
    - Flow events for request tracking across components
    - Counter events for queue depth, bandwidth metrics
    - Async events for multi-channel operations

    Supported event phases:
        - X: Duration (begin + end)
        - i: Instant
        - s/c/f: Flow start/continuation/end
        - b/e: Nested begin/end
    """

    VERSION = "1.0"

    def __init__(
        self,
        clock_freq_hz: float = 1.28e9,
        pid: int = 1,
        process_name: str = "HBM Simulator"
    ):
        """Initialize Chrome trace formatter

        Args:
            clock_freq_hz: Clock frequency for cycle-to-time conversion
            pid: Process ID for trace events
            process_name: Process name
        """
        self.clock_freq_hz = clock_freq_hz
        self.clock_period_us = 1e6 / clock_freq_hz  # microseconds per cycle
        self.pid = pid
        self.process_name = process_name
        self._events: List[ChromeTraceEvent] = []
        self._flow_id_counter = 1
        self._next_tid = 1

        # TID assignments
        self._tids: Dict[str, int] = {
            "main": self._next_tid,
            "controller": self._next_tid + 1,
            "scheduler": self._next_tid + 2,
            "queue": self._next_tid + 3,
            "channel_0": self._next_tid + 4,
        }
        self._next_tid += 5

    def cycles_to_us(self, cycles: int) -> float:
        """Convert cycles to microseconds"""
        return cycles * self.clock_period_us

    def us_to_cycles(self, us: float) -> int:
        """Convert microseconds to cycles"""
        return int(us / self.clock_period_us)

    def ns_to_us(self, ns: int) -> float:
        """Convert nanoseconds to microseconds"""
        return ns / 1000.0

    def get_tid(self, identifier: str) -> int:
        """Get or assign thread ID

        Args:
            identifier: Subsystem or channel identifier

        Returns:
            Thread ID
        """
        if identifier not in self._tids:
            self._tids[identifier] = self._next_tid
            self._next_tid += 1
        return self._tids[identifier]

    def add_duration(
        self,
        name: str,
        category: ChromeCategory,
        start_us: float,
        end_us: float,
        tid: Optional[int] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add duration event (shown as bar in trace)

        Args:
            name: Event name
            category: Event category
            start_us: Start time in microseconds
            end_us: End time in microseconds
            tid: Thread ID
            args: Event arguments
        """
        if tid is None:
            subsystem = category.value.split()[1].lower() if " " in category.value else "main"
            tid = self.get_tid(subsystem)

        event = ChromeTraceEvent(
            name=name,
            category=category.value,
            timestamp_us=start_us,
            duration_us=end_us - start_us,
            tid=tid,
            pid=self.pid,
            args=args
        )
        self._events.append(event)

    def add_instant(
        self,
        name: str,
        category: ChromeCategory,
        timestamp_us: float,
        tid: Optional[int] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add instant event (shown as marker)

        Args:
            name: Event name
            category: Event category
            timestamp_us: Timestamp in microseconds
            tid: Thread ID
            args: Event arguments
        """
        if tid is None:
            tid = self.get_tid("main")

        event = ChromeTraceEvent(
            name=name,
            category=category.value,
            timestamp_us=timestamp_us,
            tid=tid,
            pid=self.pid,
            args=args
        )
        self._events.append(event)

    def add_counter(
        self,
        name: str,
        category: ChromeCategory,
        timestamp_us: float,
        values: Dict[str, float],
        tid: int = 0
    ) -> None:
        """Add counter event for metrics visualization

        Args:
            name: Counter name
            category: Event category
            timestamp_us: Timestamp in microseconds
            values: Counter values (e.g., {"queue_depth": 10, "bandwidth_gbps": 200})
            tid: Thread ID (use 0 for global counters)
        """
        event = ChromeTraceEvent(
            name=name,
            category=category.value,
            timestamp_us=timestamp_us,
            tid=tid,
            pid=self.pid,
            args=values
        )
        # Counter events use 'C' phase
        self._events.append(event)

    def add_flow_start(
        self,
        name: str,
        category: ChromeCategory,
        timestamp_us: float,
        flow_id: Optional[int] = None,
        tid: Optional[int] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add flow start event

        Args:
            name: Event name
            category: Event category
            timestamp_us: Timestamp in microseconds
            flow_id: Flow ID (auto-generated if None)
            tid: Thread ID
            args: Event arguments

        Returns:
            Flow ID used
        """
        if flow_id is None:
            flow_id = self._flow_id_counter
            self._flow_id_counter += 1

        if tid is None:
            tid = self.get_tid("main")

        event = ChromeTraceEvent(
            name=name,
            category=category.value,
            timestamp_us=timestamp_us,
            tid=tid,
            pid=self.pid,
            args=args
        )
        self._events.append(event.to_flow_event(flow_id, "start"))
        return flow_id

    def add_flow_end(
        self,
        name: str,
        category: ChromeCategory,
        timestamp_us: float,
        flow_id: int,
        tid: Optional[int] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add flow end event

        Args:
            name: Event name
            category: Event category
            timestamp_us: Timestamp in microseconds
            flow_id: Flow ID to end
            tid: Thread ID
            args: Event arguments
        """
        if tid is None:
            tid = self.get_tid("main")

        event = ChromeTraceEvent(
            name=name,
            category=category.value,
            timestamp_us=timestamp_us,
            tid=tid,
            pid=self.pid,
            args=args
        )
        self._events.append(event.to_flow_event(flow_id, "end"))

    def add_request_span(
        self,
        request_id: int,
        category: ChromeCategory,
        start_us: float,
        end_us: float,
        channel: int,
        is_read: bool,
        tid: Optional[int] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add request lifecycle as duration event

        Args:
            request_id: Request identifier
            category: Event category
            start_us: Start time in microseconds
            end_us: End time in microseconds
            channel: Channel index
            is_read: True for read, False for write
            tid: Thread ID
            args: Additional arguments

        Returns:
            Flow ID used for request tracking
        """
        op_type = "Read" if is_read else "Write"
        name = f"{op_type} #{request_id}"

        if tid is None:
            tid = self.get_tid(f"channel_{channel}")

        event_args = {
            "request_id": request_id,
            "channel": channel,
            "is_read": is_read,
            "latency_us": end_us - start_us,
        }
        if args:
            event_args.update(args)

        flow_id = self._flow_id_counter
        self._flow_id_counter += 1

        # Add duration event
        self.add_duration(name, category, start_us, end_us, tid, event_args)

        # Add flow events for request tracking
        self.add_flow_start(name, category, start_us, flow_id, tid, event_args)
        self.add_flow_end(name, category, end_us, flow_id, tid)

        return flow_id

    def add_burst(
        self,
        name: str,
        category: ChromeCategory,
        start_us: float,
        items: List[Dict[str, Any]],
        tid: Optional[int] = None
    ) -> None:
        """Add nested duration events for burst operations

        Args:
            name: Burst name
            category: Event category
            start_us: Start time in microseconds
            items: List of item dictionaries with 'name' and 'duration_us'
            tid: Thread ID
        """
        if tid is None:
            tid = self.get_tid("main")

        # Parent event
        total_duration = sum(item.get('duration_us', 0) for item in items)
        self.add_duration(name, category, start_us, start_us + total_duration, tid, {"count": len(items)})

        # Nested events
        current_us = start_us
        for i, item in enumerate(items):
            item_name = item.get('name', f"Item {i}")
            item_duration = item.get('duration_us', 0)
            self.add_duration(
                item_name,
                category,
                current_us,
                current_us + item_duration,
                tid,
                item.get('args')
            )
            current_us += item_duration

    def events(self) -> Iterator[ChromeTraceEvent]:
        """Return event iterator (sorted by timestamp)"""
        return iter(sorted(self._events, key=lambda e: (e.timestamp_us, e.name)))

    def event_count(self) -> int:
        """Return number of events"""
        return len(self._events)

    def clear(self) -> None:
        """Clear all events"""
        self._events.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export to Chrome Tracing JSON format dictionary"""
        return {
            "traceEvents": [e.to_dict() for e in self.events()],
            "metadata": {
                "version": self.VERSION,
                "format": "chrome",
                "clock_freq_hz": self.clock_freq_hz,
                "process_name": self.process_name,
                "num_events": len(self._events),
                "export_timestamp": time.time(),
            },
            "systemTraceEvents": "",
        }

    def to_json(self, fp=None, indent: int = 2) -> str:
        """Export to Chrome Tracing JSON format

        Args:
            fp: File handle to write to (optional)
            indent: JSON indentation

        Returns:
            JSON string if fp is None, empty string otherwise
        """
        trace = self.to_dict()
        if fp:
            json.dump(trace, fp, indent=indent)
            return ""
        return json.dumps(trace, indent=indent)

    def save(self, filename: str, indent: int = 2) -> None:
        """Save trace to file

        Args:
            filename: Output filename
            indent: JSON indentation
        """
        with open(filename, 'w') as f:
            self.to_json(f, indent)
        logger.info(f"Saved {len(self._events)} events to {filename}")

    @classmethod
    def from_perfetto(cls, perfetto_data: Dict[str, Any], clock_freq_hz: float = 1.28e9) -> "ChromeTraceFormatter":
        """Convert Perfetto format to Chrome Tracing format

        Args:
            perfetto_data: Perfetto trace dictionary
            clock_freq_hz: Clock frequency

        Returns:
            ChromeTraceFormatter with converted events
        """
        formatter = cls(clock_freq_hz=clock_freq_hz)

        # Convert Perfetto events to Chrome format
        for event in perfetto_data.get("traceEvents", []):
            ts_us = event["ts"] / 1000.0  # Convert ns to us
            dur_us = event.get("dur", 0) / 1000.0

            chrome_event = ChromeTraceEvent(
                name=event["name"],
                category=event["cat"],
                timestamp_us=ts_us,
                duration_us=dur_us,
                tid=event.get("tid", 0),
                pid=event.get("pid", 1),
                args=event.get("args"),
            )
            formatter._events.append(chrome_event)

        logger.info(f"Converted {len(formatter._events)} events from Perfetto format")
        return formatter


def create_formatter_from_simulator(
    simulator: Any,
    clock_freq_hz: float = 1.28e9
) -> ChromeTraceFormatter:
    """Create Chrome trace formatter from simulator state

    Args:
        simulator: HBMSimulator or similar object
        clock_freq_hz: Clock frequency

    Returns:
        Configured ChromeTraceFormatter
    """
    formatter = ChromeTraceFormatter(clock_freq_hz=clock_freq_hz)

    # Export controller events
    if hasattr(simulator, 'controller'):
        ctrl = simulator.controller
        if hasattr(ctrl, 'stats'):
            stats = ctrl.stats
            # Add completion marker
            if hasattr(stats, 'total_cycles'):
                formatter.add_instant(
                    "Controller Done",
                    ChromeCategory.HBM_CONTROLLER,
                    formatter.cycles_to_us(stats.total_cycles),
                    args={"completed": stats.completed_requests}
                )

    # Export queue statistics
    if hasattr(simulator, 'request_queue'):
        queue = simulator.request_queue
        if hasattr(queue, 'queue_depth'):
            formatter.add_counter(
                "Queue Depth",
                ChromeCategory.HBM_QUEUE,
                0,
                {"depth": queue.queue_depth}
            )

    return formatter
