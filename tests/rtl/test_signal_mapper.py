"""Tests for signal_mapper module"""

import pytest
from sim.rtl.signal_mapper import SignalMapper, SignalMapping


class TestSignalMapping:
    def test_signal_mapping_creation(self):
        mapping = SignalMapping(
            python_signal="request.pending",
            rtl_signal="req_valid",
            tolerance=2
        )
        assert mapping.python_signal == "request.pending"
        assert mapping.rtl_signal == "req_valid"
        assert mapping.tolerance == 2

    def test_signal_mapping_defaults(self):
        mapping = SignalMapping(python_signal="a", rtl_signal="b")
        assert mapping.tolerance == 1

    def test_signal_mapping_repr(self):
        mapping = SignalMapping(python_signal="x", rtl_signal="y", tolerance=3)
        assert "x" in repr(mapping)
        assert "y" in repr(mapping)


class TestSignalMapper:
    def test_mapper_creation(self):
        mapper = SignalMapper()
        assert len(mapper.get_all_mappings()) == 0

    def test_register_mapping(self):
        mapper = SignalMapper()
        mapper.register_mapping("state.idle", "st_idle", tolerance=1)

        mapping = mapper.get_mapping("state.idle")
        assert mapping is not None
        assert mapping.rtl_signal == "st_idle"
        assert mapping.tolerance == 1

    def test_get_all_mappings(self):
        mapper = SignalMapper()
        mapper.register_mapping("a", "A")
        mapper.register_mapping("b", "B")

        mappings = mapper.get_all_mappings()
        assert len(mappings) == 2

    def test_get_nonexistent_mapping(self):
        mapper = SignalMapper()
        assert mapper.get_mapping("nonexistent") is None

    def test_validate_mappings_empty(self):
        mapper = SignalMapper()
        errors = mapper.validate_mappings()
        assert len(errors) == 0

    def test_validate_mappings_valid(self):
        mapper = SignalMapper()
        mapper.register_mapping("a", "A")
        errors = mapper.validate_mappings()
        assert len(errors) == 0

    def test_get_rtl_signal_name(self):
        mapper = SignalMapper()
        mapper.register_mapping("bank.state", "bank_st")

        assert mapper.get_rtl_signal_name("bank.state") == "bank_st"
        assert mapper.get_rtl_signal_name("missing") is None

    def test_multiple_mappings(self):
        mapper = SignalMapper()
        mappings = [
            ("request.addr", "req_addr", 1),
            ("bank.state", "bank_st", 2),
            ("channel.data", "ch_data", 0),
        ]
        for python, rtl, tol in mappings:
            mapper.register_mapping(python, rtl, tolerance=tol)

        all_mappings = mapper.get_all_mappings()
        assert len(all_mappings) == 3

    def test_register_default_hbm4_mappings(self):
        mapper = SignalMapper()
        mapper.register_default_hbm4_mappings()

        # Check some default mappings exist
        assert mapper.get_mapping("request.valid") is not None
        assert mapper.get_mapping("bank.state") is not None
        assert mapper.get_mapping("channel.data_valid") is not None

        # Check all were registered
        all_mappings = mapper.get_all_mappings()
        assert len(all_mappings) >= 12  # We have at least 12 default mappings
