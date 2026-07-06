# sim/trace_export/test_perfetto.py
"""Tests for Perfetto and Chrome Trace Export functionality"""
import json
import os
import tempfile
import pytest
from typing import List, Dict, Any

from .perfetto_exporter import (
    PerfettoExporter,
    PerfettoTraceEvent,
    PerfettoTraceEvent,
    EventCategory,
    EventType,
    HBMRequestEvent,
)
from .trace_formatter import (
    ChromeTraceFormatter,
    ChromeTraceEvent,
    ChromeCategory,
)


class TestPerfettoTraceEvent:
    """Tests for PerfettoTraceEvent"""

    def test_duration_event_to_dict(self):
        """Test duration event serialization"""
        event = PerfettoTraceEvent(
            name="Test Event",
            category="test.category",
            timestamp_ns=1000,
            duration_ns=500,
            tid=1,
            pid=1,
            args={"key": "value"}
        )
        d = event.to_dict()

        assert d["name"] == "Test Event"
        assert d["cat"] == "test.category"
        assert d["ts"] == 1000
        assert d["dur"] == 500
        assert d["ph"] == "X"
        assert d["tid"] == 1
        assert d["pid"] == 1
        assert d["args"] == {"key": "value"}

    def test_instant_event_to_dict(self):
        """Test instant event serialization"""
        event = PerfettoTraceEvent(
            name="Instant Event",
            category="test.category",
            timestamp_ns=1000,
            tid=1,
            pid=1
        )
        d = event.to_dict()

        assert d["ph"] == "i"
        assert "dur" not in d

    def test_event_with_null_args(self):
        """Test event with null args"""
        event = PerfettoTraceEvent(
            name="No Args Event",
            category="test.category",
            timestamp_ns=1000
        )
        d = event.to_dict()

        # null args should not be included in output
        assert "args" not in d or d.get("args") is None


class TestPerfettoExporter:
    """Tests for PerfettoExporter"""

    def test_exporter_initialization(self):
        """Test exporter initialization"""
        exporter = PerfettoExporter(clock_freq_hz=1.28e9)

        assert exporter.clock_freq_hz == 1.28e9
        assert exporter.pid == 1
        assert exporter.process_name == "HBM Simulator"
        assert exporter.event_count() == 0

    def test_cycles_to_ns_conversion(self):
        """Test cycle to nanosecond conversion"""
        exporter = PerfettoExporter(clock_freq_hz=1.28e9)  # 1.28 GHz

        # At 1.28 GHz, 1 cycle = 0.78125 ns
        cycles = 128
        expected_ns = 100  # 128 * 0.78125 = 100 ns
        assert exporter.cycles_to_ns(cycles) == expected_ns

    def test_add_duration_event(self):
        """Test adding duration event"""
        exporter = PerfettoExporter()

        exporter.add_duration_event(
            name="Test Duration",
            category=EventCategory.CONTROLLER,
            start_cycle=0,
            end_cycle=100,
            args={"key": "value"}
        )

        assert exporter.event_count() == 1
        event = exporter._events[0]
        assert event.name == "Test Duration"
        assert event.duration_ns > 0

    def test_add_request_lifecycle(self):
        """Test adding request lifecycle events"""
        exporter = PerfettoExporter()

        exporter.add_request_lifecycle(
            request_id=42,
            submit_cycle=0,
            complete_cycle=50,
            channel=0,
            bank=1,
            address=0x1000,
            is_read=True
        )

        # Should add: submit instant + complete instant + duration event
        assert exporter.event_count() == 3

    def test_add_command_event(self):
        """Test adding command event"""
        exporter = PerfettoExporter()

        exporter.add_command_event(
            command_type="ACT",
            channel=0,
            bank=1,
            cycle=10
        )

        assert exporter.event_count() == 1
        event = exporter._events[0]
        assert event.name == "ACT"
        assert event.args["channel"] == 0
        assert event.args["bank"] == 1

    def test_add_bank_state_event(self):
        """Test adding bank state event"""
        exporter = PerfettoExporter()

        exporter.add_bank_state_event(
            state="OPEN",
            channel=0,
            bank=1,
            cycle=20
        )

        assert exporter.event_count() == 1
        event = exporter._events[0]
        assert "Bank OPEN" in event.name

    def test_add_queue_event(self):
        """Test adding queue event"""
        exporter = PerfettoExporter()

        exporter.add_queue_event(
            operation="PUSH",
            channel=0,
            queue_depth=10,
            cycle=30
        )

        assert exporter.event_count() == 1
        event = exporter._events[0]
        assert "Queue PUSH" in event.name
        assert event.args["queue_depth"] == 10

    def test_add_refresh_event(self):
        """Test adding refresh event"""
        exporter = PerfettoExporter()

        exporter.add_refresh_event(
            channel=0,
            start_cycle=100,
            end_cycle=150,
            tid=5
        )

        assert exporter.event_count() == 1
        event = exporter._events[0]
        assert "Refresh CH0" in event.name
        assert event.duration_ns > 0

    def test_to_dict_structure(self):
        """Test exported dictionary structure"""
        exporter = PerfettoExporter()
        exporter.add_event(
            name="Test",
            category=EventCategory.CONTROLLER,
            timestamp_ns=1000
        )

        trace = exporter.to_dict()

        assert "traceEvents" in trace
        assert "metadata" in trace
        assert len(trace["traceEvents"]) == 1
        assert trace["metadata"]["trace_type"] == "perfetto"

    def test_to_json_output(self):
        """Test JSON export"""
        exporter = PerfettoExporter()
        exporter.add_event(
            name="Test Event",
            category=EventCategory.DRAM,
            timestamp_ns=500,
            duration_ns=100
        )

        json_str = exporter.to_json()

        data = json.loads(json_str)
        assert len(data["traceEvents"]) == 1
        assert data["traceEvents"][0]["name"] == "Test Event"

    def test_save_and_load(self):
        """Test save and load roundtrip"""
        exporter = PerfettoExporter(clock_freq_hz=1.28e9)
        exporter.add_request_lifecycle(
            request_id=1,
            submit_cycle=0,
            complete_cycle=100,
            channel=0,
            bank=0,
            address=0x1000,
            is_read=True
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filename = f.name

        try:
            exporter.save(filename)

            # Load and verify
            loaded = PerfettoExporter.load(filename, clock_freq_hz=1.28e9)
            assert loaded.event_count() == exporter.event_count()
        finally:
            os.unlink(filename)

    def test_clear(self):
        """Test clearing events"""
        exporter = PerfettoExporter()
        exporter.add_event(
            name="Test",
            category=EventCategory.CONTROLLER,
            timestamp_ns=100
        )

        assert exporter.event_count() == 1
        exporter.clear()
        assert exporter.event_count() == 0


class TestChromeTraceEvent:
    """Tests for ChromeTraceEvent"""

    def test_duration_event_to_dict(self):
        """Test duration event serialization"""
        event = ChromeTraceEvent(
            name="Chrome Test",
            category="HBM Controller",
            timestamp_us=1.0,
            duration_us=0.5,
            tid=1,
            pid=1,
            args={"count": 10}
        )
        d = event.to_dict()

        assert d["name"] == "Chrome Test"
        assert d["cat"] == "HBM Controller"
        assert d["ts"] == 1.0
        assert d["dur"] == 0.5
        assert d["ph"] == "X"

    def test_instant_event_to_dict(self):
        """Test instant event serialization"""
        event = ChromeTraceEvent(
            name="Instant",
            category="HBM Controller",
            timestamp_us=1.0,
            tid=1
        )
        d = event.to_dict()

        assert d["ph"] == "i"
        assert "dur" not in d

    def test_flow_event_conversion(self):
        """Test flow event conversion"""
        event = ChromeTraceEvent(
            name="Flow Test",
            category="HBM Controller",
            timestamp_us=1.0
        )

        # Start event
        start = event.to_flow_event(42, "start")
        assert start["ph"] == "s"
        assert start["id"] == "42"

        # End event
        end = event.to_flow_event(42, "end")
        assert end["ph"] == "f"
        assert end["id"] == "42"


class TestChromeTraceFormatter:
    """Tests for ChromeTraceFormatter"""

    def test_formatter_initialization(self):
        """Test formatter initialization"""
        formatter = ChromeTraceFormatter(clock_freq_hz=1.28e9)

        assert formatter.clock_freq_hz == 1.28e9
        assert formatter.pid == 1
        assert formatter.event_count() == 0

    def test_cycles_to_us_conversion(self):
        """Test cycle to microsecond conversion"""
        formatter = ChromeTraceFormatter(clock_freq_hz=1.28e9)

        # At 1.28 GHz, 1 cycle = 0.78125 ns = 0.00078125 us
        cycles = 1280
        expected_us = 1.0  # 1280 * 0.00078125 = 1.0 us
        assert abs(formatter.cycles_to_us(cycles) - expected_us) < 0.01

    def test_add_duration(self):
        """Test adding duration event"""
        formatter = ChromeTraceFormatter()

        formatter.add_duration(
            name="Test Duration",
            category=ChromeCategory.HBM_CONTROLLER,
            start_us=0.0,
            end_us=10.0,
            args={"key": "value"}
        )

        assert formatter.event_count() == 1
        event = formatter._events[0]
        assert event.duration_us == 10.0

    def test_add_instant(self):
        """Test adding instant event"""
        formatter = ChromeTraceFormatter()

        formatter.add_instant(
            name="Marker",
            category=ChromeCategory.HBM_DRAM,
            timestamp_us=5.0
        )

        assert formatter.event_count() == 1

    def test_add_counter(self):
        """Test adding counter event"""
        formatter = ChromeTraceFormatter()

        formatter.add_counter(
            name="Queue Stats",
            category=ChromeCategory.HBM_QUEUE,
            timestamp_us=1.0,
            values={"depth": 10, "max_depth": 100}
        )

        assert formatter.event_count() == 1

    def test_add_flow_start_end(self):
        """Test adding flow events"""
        formatter = ChromeTraceFormatter()

        flow_id = formatter.add_flow_start(
            name="Request Flow",
            category=ChromeCategory.HBM_CONTROLLER,
            timestamp_us=0.0
        )

        formatter.add_flow_end(
            name="Request Flow",
            category=ChromeCategory.HBM_CONTROLLER,
            timestamp_us=10.0,
            flow_id=flow_id
        )

        assert formatter.event_count() == 2

    def test_add_request_span(self):
        """Test adding request span"""
        formatter = ChromeTraceFormatter()

        flow_id = formatter.add_request_span(
            request_id=1,
            category=ChromeCategory.HBM_CONTROLLER,
            start_us=0.0,
            end_us=20.0,
            channel=0,
            is_read=True
        )

        # Should add duration + 2 flow events
        assert formatter.event_count() == 3

    def test_to_dict_structure(self):
        """Test exported dictionary structure"""
        formatter = ChromeTraceFormatter()
        formatter.add_instant(
            name="Test",
            category=ChromeCategory.HBM_CONTROLLER,
            timestamp_us=1.0
        )

        trace = formatter.to_dict()

        assert "traceEvents" in trace
        assert "metadata" in trace
        assert trace["metadata"]["format"] == "chrome"

    def test_save_and_load_json(self):
        """Test save and load JSON"""
        formatter = ChromeTraceFormatter()
        formatter.add_duration(
            name="Save Test",
            category=ChromeCategory.HBM_DRAM,
            start_us=0.0,
            end_us=5.0
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filename = f.name

        try:
            formatter.save(filename)

            with open(filename, 'r') as f:
                data = json.load(f)

            assert len(data["traceEvents"]) == 1
            assert data["traceEvents"][0]["name"] == "Save Test"
        finally:
            os.unlink(filename)

    def test_from_perfetto_conversion(self):
        """Test converting from Perfetto format"""
        perfetto_data = {
            "traceEvents": [
                {
                    "name": "Test Event",
                    "cat": "test.category",
                    "ts": 1000000,  # ns
                    "dur": 500000,  # ns
                    "tid": 1,
                    "pid": 1,
                    "args": {"key": "value"}
                }
            ]
        }

        formatter = ChromeTraceFormatter.from_perfetto(perfetto_data, clock_freq_hz=1.28e9)

        assert formatter.event_count() == 1
        event = formatter._events[0]
        assert event.name == "Test Event"
        assert event.timestamp_us == 1000.0  # Converted to us
        assert event.duration_us == 500.0

    def test_clear(self):
        """Test clearing events"""
        formatter = ChromeTraceFormatter()
        formatter.add_duration(
            name="Test",
            category=ChromeCategory.HBM_CONTROLLER,
            start_us=0.0,
            end_us=1.0
        )

        assert formatter.event_count() == 1
        formatter.clear()
        assert formatter.event_count() == 0


class TestIntegration:
    """Integration tests for trace export"""

    def test_perfetto_to_chrome_conversion(self):
        """Test Perfetto to Chrome format conversion"""
        # Create Perfetto trace
        perfetto = PerfettoExporter(clock_freq_hz=1.28e9)
        perfetto.add_request_lifecycle(
            request_id=1,
            submit_cycle=0,
            complete_cycle=100,
            channel=0,
            bank=0,
            address=0x1000,
            is_read=True
        )

        # Convert to Chrome format
        perfetto_data = perfetto.to_dict()
        chrome = ChromeTraceFormatter.from_perfetto(perfetto_data, clock_freq_hz=1.28e9)

        # Verify conversion
        assert chrome.event_count() == perfetto.event_count()

    def test_multi_channel_trace(self):
        """Test tracing multiple channels"""
        perfetto = PerfettoExporter()

        for ch in range(8):
            for req_id in range(10):
                perfetto.add_request_lifecycle(
                    request_id=req_id,
                    submit_cycle=req_id * 10,
                    complete_cycle=req_id * 10 + 20,
                    channel=ch,
                    bank=0,
                    address=0x1000 * ch,
                    is_read=(req_id % 2 == 0)
                )

        assert perfetto.event_count() == 8 * 10 * 3  # 3 events per request

    def test_export_file_size(self):
        """Test that exported files are reasonable size"""
        perfetto = PerfettoExporter()

        # Add many events
        for i in range(1000):
            perfetto.add_event(
                name=f"Event {i}",
                category=EventCategory.CONTROLLER,
                timestamp_ns=i * 100
            )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filename = f.name

        try:
            perfetto.save(filename)

            size = os.path.getsize(filename)
            # Should be less than 500KB for 1000 events
            assert size < 500 * 1024
        finally:
            os.unlink(filename)


class TestEdgeCases:
    """Tests for edge cases"""

    def test_zero_duration_event(self):
        """Test zero duration event"""
        exporter = PerfettoExporter()
        exporter.add_event(
            name="Zero Duration",
            category=EventCategory.CONTROLLER,
            timestamp_ns=100,
            duration_ns=0
        )

        d = exporter._events[0].to_dict()
        assert d["ph"] == "i"

    def test_negative_cycles(self):
        """Test handling of edge case values"""
        exporter = PerfettoExporter()

        # Should not crash
        exporter.add_duration_event(
            name="Test",
            category=EventCategory.CONTROLLER,
            start_cycle=0,
            end_cycle=1
        )

        assert exporter.event_count() == 1

    def test_large_timestamp(self):
        """Test large timestamp values"""
        formatter = ChromeTraceFormatter()

        # Large simulation time (1 second = 1e6 us)
        formatter.add_duration(
            name="Long Event",
            category=ChromeCategory.HBM_CONTROLLER,
            start_us=0.0,
            end_us=1_000_000.0
        )

        event = formatter._events[0]
        assert event.duration_us == 1_000_000.0

    def test_special_characters_in_name(self):
        """Test special characters in event names"""
        exporter = PerfettoExporter()
        exporter.add_event(
            name="Event with 'quotes' and \"double\" and <brackets>",
            category=EventCategory.CONTROLLER,
            timestamp_ns=100
        )

        d = exporter._events[0].to_dict()
        assert "'" in d["name"]  # Should preserve special chars


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
