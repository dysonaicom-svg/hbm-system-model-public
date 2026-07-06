# sim/trace_export/perfetto_exporter.py
"""
Perfetto Trace Export for HBM Simulation
Export trace data to Perfetto JSON format for chrome://tracing analysis
"""
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Iterator
from enum import Enum
import time

logger = logging.getLogger(__name__)


class EventCategory(Enum):
    """HBM event categories for Perfetto"""
    CONTROLLER = "hbm.controller"
    DRAM = "hbm.dram"
    COMMAND = "hbm.command"
    QUEUE = "hbm.queue"
    SCHEDULER = "hbm.scheduler"
    CHANNEL = "hbm.channel"
    REFRESH = "hbm.refresh"
    TRAFFIC = "hbm.traffic"
    BANK = "hbm.bank"


class EventType(Enum):
    """HBM event types"""
    REQUEST_SUBMIT = "request_submit"
    REQUEST_COMPLETE = "request_complete"
    COMMAND_ISSUE = "command_issue"
    COMMAND_COMPLETE = "command_complete"
    QUEUE_PUSH = "queue_push"
    QUEUE_POP = "queue_pop"
    BANK_OPEN = "bank_open"
    BANK_CLOSE = "bank_close"
    REFRESH_START = "refresh_start"
    REFRESH_END = "refresh_end"
    ACTIVATION = "activation"
    READ = "read"
    WRITE = "write"


@dataclass
class PerfettoTraceEvent:
    """Single trace event in Perfetto format

    Attributes:
        name: Event name displayed in trace viewer
        category: Event category for grouping
        timestamp_ns: Event timestamp in nanoseconds
        duration_ns: Duration in nanoseconds (0 for instant events)
        tid: Thread/process identifier
        pid: Process identifier
        args: Optional event arguments
    """
    name: str
    category: str
    timestamp_ns: int
    duration_ns: int = 0
    tid: int = 0
    pid: int = 0
    args: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Perfetto trace format"""
        event = {
            "name": self.name,
            "cat": self.category,
            "ts": self.timestamp_ns,
            "ph": "X" if self.duration_ns > 0 else "i",  # X=duration, i=instant
            "tid": self.tid,
            "pid": self.pid,
        }
        if self.duration_ns > 0:
            event["dur"] = self.duration_ns
        if self.args is not None:
            event["args"] = self.args
        return event


@dataclass
class HBMRequestEvent:
    """HBM request lifecycle event"""
    request_id: int
    event_type: EventType
    timestamp_ns: int
    channel: int = 0
    bank: int = 0
    address: int = 0
    is_read: bool = True


class PerfettoExporter:
    """Export HBM trace data to Perfetto JSON format

    Supports:
    - Controller operations (request scheduling, completion)
    - DRAM operations (activation, read/write, precharge)
    - Queue operations (push/pop events)
    - Channel-level events
    - Refreshing operations
    """

    TRACE_VERSION = "1.0"
    TRACE_TYPE = "perfetto"

    def __init__(
        self,
        clock_freq_hz: float = 1.28e9,
        pid: int = 1,
        process_name: str = "HBM Simulator"
    ):
        """Initialize Perfetto exporter

        Args:
            clock_freq_hz: Clock frequency for cycle-to-time conversion
            pid: Process ID for trace events
            process_name: Process name for trace metadata
        """
        self.clock_freq_hz = clock_freq_hz
        self.clock_period_ns = 1e9 / clock_freq_hz  # nanoseconds per cycle
        self.pid = pid
        self.process_name = process_name
        self._events: List[PerfettoTraceEvent] = []
        self._request_events: Dict[int, List[HBMRequestEvent]] = {}
        self._next_tid = 1

        # TID assignments for different subsystems
        self._tids: Dict[str, int] = {
            "controller": self._next_tid,
            "scheduler": self._next_tid + 1,
            "queue": self._next_tid + 2,
        }
        self._next_tid += 3

    def cycles_to_ns(self, cycles: int) -> int:
        """Convert cycles to nanoseconds"""
        return int(cycles * self.clock_period_ns)

    def ns_to_cycles(self, ns: int) -> int:
        """Convert nanoseconds to cycles"""
        return int(ns / (self.clock_period_ns * 1e9))

    def get_tid(self, subsystem: str) -> int:
        """Get thread ID for subsystem"""
        if subsystem not in self._tids:
            self._tids[subsystem] = self._next_tid
            self._next_tid += 1
        return self._tids[subsystem]

    def add_event(
        self,
        name: str,
        category: EventCategory,
        timestamp_ns: int,
        duration_ns: int = 0,
        tid: Optional[int] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a trace event

        Args:
            name: Event name
            category: Event category
            timestamp_ns: Event timestamp in nanoseconds
            duration_ns: Event duration in nanoseconds
            tid: Thread ID (auto-assigned if None)
            args: Optional event arguments
        """
        if tid is None:
            # Infer tid from category
            subsystem = category.value.split(".")[1] if "." in category.value else "controller"
            tid = self.get_tid(subsystem)

        event = PerfettoTraceEvent(
            name=name,
            category=category.value,
            timestamp_ns=timestamp_ns,
            duration_ns=duration_ns,
            tid=tid,
            pid=self.pid,
            args=args
        )
        self._events.append(event)

    def add_duration_event(
        self,
        name: str,
        category: EventCategory,
        start_cycle: int,
        end_cycle: int,
        tid: Optional[int] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a duration event from cycle counts

        Args:
            name: Event name
            category: Event category
            start_cycle: Start cycle
            end_cycle: End cycle
            tid: Thread ID
            args: Optional event arguments
        """
        start_ns = self.cycles_to_ns(start_cycle)
        duration_ns = self.cycles_to_ns(end_cycle - start_cycle)
        self.add_event(name, category, start_ns, duration_ns, tid, args)

    def add_request_lifecycle(
        self,
        request_id: int,
        submit_cycle: int,
        complete_cycle: int,
        channel: int,
        bank: int,
        address: int,
        is_read: bool,
        tid: Optional[int] = None
    ) -> None:
        """Add complete request lifecycle events

        Args:
            request_id: Request identifier
            submit_cycle: Cycle when request was submitted
            complete_cycle: Cycle when request completed
            channel: Channel index
            bank: Bank index
            address: Memory address
            is_read: True for read, False for write
            tid: Thread ID
        """
        if tid is None:
            tid = self.get_tid("controller")

        op_type = "READ" if is_read else "WRITE"
        latency_cycles = complete_cycle - submit_cycle
        latency_ns = self.cycles_to_ns(latency_cycles)

        # Submit event (instant)
        self.add_event(
            f"{op_type} Submit #{request_id}",
            EventCategory.CONTROLLER,
            self.cycles_to_ns(submit_cycle),
            tid=tid,
            args={
                "request_id": request_id,
                "channel": channel,
                "bank": bank,
                "address": hex(address),
                "is_read": is_read,
            }
        )

        # Complete event (instant)
        self.add_event(
            f"{op_type} Complete #{request_id}",
            EventCategory.CONTROLLER,
            self.cycles_to_ns(complete_cycle),
            tid=tid,
            args={
                "request_id": request_id,
                "channel": channel,
                "bank": bank,
                "latency_cycles": latency_cycles,
            }
        )

        # Duration event for the full request
        self.add_duration_event(
            f"Request #{request_id} ({op_type})",
            EventCategory.CONTROLLER,
            submit_cycle,
            complete_cycle,
            tid=tid,
            args={
                "request_id": request_id,
                "channel": channel,
                "bank": bank,
                "latency_cycles": latency_cycles,
            }
        )

        # Store for later lookup
        if request_id not in self._request_events:
            self._request_events[request_id] = []
        self._request_events[request_id].append(HBMRequestEvent(
            request_id=request_id,
            event_type=EventType.REQUEST_SUBMIT,
            timestamp_ns=self.cycles_to_ns(submit_cycle),
            channel=channel,
            bank=bank,
            address=address,
            is_read=is_read,
        ))

    def add_command_event(
        self,
        command_type: str,
        channel: int,
        bank: int,
        cycle: int,
        tid: Optional[int] = None
    ) -> None:
        """Add DRAM command event

        Args:
            command_type: Command type (ACT, RD, WR, PRE, REF)
            channel: Channel index
            bank: Bank index
            cycle: Cycle when command was issued
            tid: Thread ID
        """
        self.add_event(
            command_type,
            EventCategory.COMMAND,
            self.cycles_to_ns(cycle),
            tid=tid,
            args={
                "channel": channel,
                "bank": bank,
            }
        )

    def add_bank_state_event(
        self,
        state: str,
        channel: int,
        bank: int,
        cycle: int,
        tid: Optional[int] = None
    ) -> None:
        """Add bank state change event

        Args:
            state: New bank state (OPEN, CLOSED, REFRESHING)
            channel: Channel index
            bank: Bank index
            cycle: Cycle of state change
            tid: Thread ID
        """
        event_type = EventType.BANK_OPEN if state == "OPEN" else EventType.BANK_CLOSE
        category = EventCategory.BANK if event_type == EventType.BANK_OPEN else EventCategory.DRAM

        self.add_event(
            f"Bank {state}",
            category,
            self.cycles_to_ns(cycle),
            tid=tid,
            args={
                "channel": channel,
                "bank": bank,
            }
        )

    def add_queue_event(
        self,
        operation: str,
        channel: int,
        queue_depth: int,
        cycle: int,
        tid: Optional[int] = None
    ) -> None:
        """Add queue operation event

        Args:
            operation: PUSH or POP
            channel: Channel index
            queue_depth: Current queue depth
            cycle: Cycle of operation
            tid: Thread ID
        """
        event_type = EventType.QUEUE_PUSH if operation == "PUSH" else EventType.QUEUE_POP
        self.add_event(
            f"Queue {operation}",
            EventCategory.QUEUE,
            self.cycles_to_ns(cycle),
            tid=tid,
            args={
                "channel": channel,
                "queue_depth": queue_depth,
            }
        )

    def add_refresh_event(
        self,
        channel: int,
        start_cycle: int,
        end_cycle: int,
        tid: Optional[int] = None
    ) -> None:
        """Add refresh operation event

        Args:
            channel: Channel being refreshed
            start_cycle: Start cycle
            end_cycle: End cycle
            tid: Thread ID
        """
        self.add_duration_event(
            f"Refresh CH{channel}",
            EventCategory.REFRESH,
            start_cycle,
            end_cycle,
            tid=tid,
            args={
                "channel": channel,
            }
        )

    def events(self) -> Iterator[PerfettoTraceEvent]:
        """Return event iterator"""
        return iter(sorted(self._events, key=lambda e: e.timestamp_ns))

    def event_count(self) -> int:
        """Return number of events"""
        return len(self._events)

    def clear(self) -> None:
        """Clear all events"""
        self._events.clear()
        self._request_events.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export to Perfetto trace format dictionary"""
        # Build trace events
        trace_events = [e.to_dict() for e in self.events()]

        # Build Perfetto trace with required structure
        trace = {
            "traceEvents": trace_events,
            "metadata": {
                "trace_version": self.TRACE_VERSION,
                "trace_type": self.TRACE_TYPE,
                "clock_freq_hz": self.clock_freq_hz,
                "clock_period_ns": self.clock_period_ns,
                "process_name": self.process_name,
                "num_events": len(self._events),
                "export_timestamp": time.time(),
            },
            "systemTraceEvents": "",  # Reserved for system trace
            "lastrasid": 0,
            "stackTrace": {},  # Reserved for stack traces
        }

        return trace

    def to_json(self, fp=None, indent: int = 2) -> str:
        """Export to Perfetto JSON format

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
    def load(cls, filename: str, clock_freq_hz: float = 1.28e9) -> "PerfettoExporter":
        """Load trace from file

        Args:
            filename: Input filename
            clock_freq_hz: Clock frequency for the trace

        Returns:
            PerfettoExporter with loaded events
        """
        with open(filename, 'r') as f:
            data = json.load(f)

        exporter = cls(clock_freq_hz=clock_freq_hz)

        # Reconstruct events from traceEvents
        for event_data in data.get("traceEvents", []):
            event = PerfettoTraceEvent(
                name=event_data["name"],
                category=event_data["cat"],
                timestamp_ns=int(event_data["ts"]),
                duration_ns=int(event_data.get("dur", 0)),
                tid=int(event_data.get("tid", 0)),
                pid=int(event_data.get("pid", 0)),
                args=event_data.get("args"),
            )
            exporter._events.append(event)

        logger.info(f"Loaded {len(exporter._events)} events from {filename}")
        return exporter


def create_exporter_from_stats(
    stats: Any,
    clock_freq_hz: float = 1.28e9
) -> PerfettoExporter:
    """Create Perfetto exporter from simulation stats

    Args:
        stats: SimulationStats object
        clock_freq_hz: Clock frequency

    Returns:
        Configured PerfettoExporter
    """
    exporter = PerfettoExporter(clock_freq_hz=clock_freq_hz)

    # Export metadata
    if hasattr(stats, 'total_cycles'):
        exporter.add_event(
            "Simulation Complete",
            EventCategory.CONTROLLER,
            exporter.cycles_to_ns(stats.total_cycles),
            args={
                "total_cycles": stats.total_cycles,
                "completed_requests": stats.completed_requests,
            }
        )

    return exporter
