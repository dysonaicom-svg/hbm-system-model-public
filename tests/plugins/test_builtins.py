"""Tests for built-in plugins"""

import pytest
from model.plugins.builtins.logger_plugin import LoggerPlugin
from model.plugins.builtins.profiler_plugin import ProfilerPlugin
from model.plugins.builtins.validator_plugin import ValidatorPlugin, ValidationRule


class TestLoggerPlugin:
    def test_logger_creation(self):
        """Test logger plugin creation"""
        plugin = LoggerPlugin()
        assert plugin.metadata.name == "logger"

    def test_logger_initialization(self):
        """Test logger initialization"""
        plugin = LoggerPlugin()
        plugin.initialize({"level": "DEBUG", "output": "console"})
        assert plugin.state.value in ("initialized", "loaded")

    def test_log_event(self):
        """Test logging events"""
        plugin = LoggerPlugin()
        plugin.initialize({})
        plugin.start()

        plugin.log_event("test_event", {"key": "value"})
        entries = plugin.get_entries("test_event")

        assert len(entries) == 1
        assert entries[0]["data"]["key"] == "value"

    def test_log_metric(self):
        """Test logging metrics"""
        plugin = LoggerPlugin()
        plugin.initialize({})
        plugin.start()

        plugin.log_metric("bandwidth", 100.5, "GB/s")
        entries = plugin.get_entries("metric")

        assert len(entries) == 1
        assert entries[0]["value"] == 100.5

    def test_clear_entries(self):
        """Test clearing log entries"""
        plugin = LoggerPlugin()
        plugin.initialize({})

        plugin.log_event("test", {})
        plugin.clear()

        assert len(plugin.get_entries()) == 0


class TestProfilerPlugin:
    def test_profiler_creation(self):
        """Test profiler plugin creation"""
        plugin = ProfilerPlugin()
        assert plugin.metadata.name == "profiler"

    def test_profiler_initialization(self):
        """Test profiler initialization"""
        plugin = ProfilerPlugin()
        plugin.initialize({"enabled": True})
        assert plugin.state.value in ("initialized", "loaded")

    def test_profiler_stats(self):
        """Test profiler stats"""
        plugin = ProfilerPlugin()
        plugin.initialize({})
        plugin.start()
        plugin.stop()

        stats = plugin.get_stats()
        # After running (start/stop), stats should have profile data
        assert "name" in stats
        assert stats["name"] == "profiler"


class TestValidatorPlugin:
    def test_validator_creation(self):
        """Test validator plugin creation"""
        plugin = ValidatorPlugin()
        assert plugin.metadata.name == "validator"

    def test_validator_initialization(self):
        """Test validator initialization"""
        plugin = ValidatorPlugin()
        plugin.initialize({})
        assert plugin.state.value in ("initialized", "loaded")

    def test_validate_valid_config(self):
        """Test validating valid configuration"""
        plugin = ValidatorPlugin()
        plugin.initialize({})

        config = {
            "hbm4": {"channels": 32, "data_rate_gbps": 16},
            "simulation": {"duration_us": 100.0, "request_rate": 0.8},
        }

        result = plugin.validate(config)
        assert result.valid

    def test_validate_invalid_channels(self):
        """Test validating invalid channels"""
        plugin = ValidatorPlugin()
        plugin.initialize({})

        config = {"hbm4": {"channels": 100}}

        result = plugin.validate(config)
        assert not result.valid
        assert len(result.errors) > 0

    def test_validate_invalid_data_rate(self):
        """Test validating invalid data rate"""
        plugin = ValidatorPlugin()
        plugin.initialize({})

        config = {"hbm4": {"data_rate_gbps": 10}}

        result = plugin.validate(config)
        assert not result.valid

    def test_add_custom_rule(self):
        """Test adding custom validation rule"""
        plugin = ValidatorPlugin()
        plugin.initialize({})

        plugin.add_rule(ValidationRule(
            field="custom.field",
            rule_type="type",
            constraint=str,
            message="Must be a string"
        ))

        assert "custom.field" in plugin._rules

    def test_get_stats(self):
        """Test validator stats"""
        plugin = ValidatorPlugin()
        plugin.initialize({})

        plugin.validate({"hbm4": {"channels": 32}})
        plugin.validate({"hbm4": {"channels": 100}})

        stats = plugin.get_stats()
        assert stats["validation_count"] == 2
        assert stats["error_count"] == 1
