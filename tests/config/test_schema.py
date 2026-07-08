"""Tests for config schema module"""

import pytest
from model.config.schema import (
    ConfigSchema,
    ValidationError,
    HBM4ConfigSchema,
    SimulationConfigSchema,
    DVFSConfigSchema,
    PluginConfigSchema,
)


class TestConfigSchema:
    def test_validate_empty_config(self):
        """Test validation of empty config"""
        errors = ConfigSchema.validate({})
        assert len(errors) == 1  # At least one of hbm4 or simulation required
        assert "hbm4" in str(errors[0].message) or "simulation" in str(errors[0].message)

    def test_validate_hbm4_valid(self):
        """Test validation of valid HBM4 config"""
        config = {
            "hbm4": {
                "channels": 32,
                "data_rate_gbps": 16,
                "queue_depth": 128,
            }
        }
        errors = ConfigSchema.validate(config)
        assert len(errors) == 0

    def test_validate_hbm4_invalid_channels(self):
        """Test validation of invalid channels"""
        config = {"hbm4": {"channels": 100}}
        errors = ConfigSchema.validate(config)
        assert len(errors) == 1
        assert "channels" in errors[0].field

    def test_validate_hbm4_invalid_data_rate(self):
        """Test validation of invalid data rate"""
        config = {"hbm4": {"data_rate_gbps": 10}}
        errors = ConfigSchema.validate(config)
        assert len(errors) == 1
        assert "data_rate" in errors[0].field

    def test_validate_simulation_valid(self):
        """Test validation of valid simulation config"""
        config = {
            "simulation": {
                "duration_us": 100.0,
                "traffic_pattern": "random",
                "request_rate": 0.8,
            }
        }
        errors = ConfigSchema.validate(config)
        assert len(errors) == 0

    def test_validate_simulation_invalid_pattern(self):
        """Test validation of invalid traffic pattern"""
        config = {"simulation": {"traffic_pattern": "invalid"}}
        errors = ConfigSchema.validate(config)
        assert len(errors) == 1

    def test_validate_simulation_negative_duration(self):
        """Test validation of negative duration"""
        config = {"simulation": {"duration_us": -10}}
        errors = ConfigSchema.validate(config)
        assert len(errors) == 1

    def test_validate_dvfs_valid(self):
        """Test validation of valid DVFS config"""
        config = {
            "hbm4": {"channels": 32},
            "simulation": {"duration_us": 100},
            "dvfs": {
                "enable": True,
                "voltage_mv": 800,
                "frequency_mhz": 1600,
            }
        }
        errors = ConfigSchema.validate(config)
        assert len(errors) == 0

    def test_validate_dvfs_invalid_voltage(self):
        """Test validation of invalid voltage"""
        config = {"hbm4": {"channels": 32}, "dvfs": {"voltage_mv": 200}}
        errors = ConfigSchema.validate(config)
        # Should have both the missing simulation error and the voltage error
        voltage_errors = [e for e in errors if "voltage" in e.field]
        assert len(voltage_errors) == 1

    def test_validate_dvfs_invalid_frequency(self):
        """Test validation of invalid frequency"""
        config = {"hbm4": {"channels": 32}, "dvfs": {"frequency_mhz": 100}}
        errors = ConfigSchema.validate(config)
        # Should have both the missing simulation error and the frequency error
        freq_errors = [e for e in errors if "frequency" in e.field]
        assert len(freq_errors) == 1

    def test_validate_plugins_valid(self):
        """Test validation of valid plugins config"""
        config = {
            "hbm4": {"channels": 32},
            "simulation": {"duration_us": 100},
            "plugins": [
                {"name": "profiler", "enabled": True},
                {"name": "logger", "enabled": False},
            ]
        }
        errors = ConfigSchema.validate(config)
        assert len(errors) == 0

    def test_validate_plugins_missing_name(self):
        """Test validation of plugins missing name"""
        config = {
            "hbm4": {"channels": 32},
            "plugins": [{"enabled": True}]
        }
        errors = ConfigSchema.validate(config)
        # Should have both the missing simulation error and the missing name error
        name_errors = [e for e in errors if "name" in e.message]
        assert len(name_errors) >= 1

    def test_validate_full_config(self):
        """Test validation of full configuration"""
        config = {
            "hbm4": {
                "channels": 32,
                "data_rate_gbps": 16,
                "queue_depth": 128,
                "address_mapping": "rbc",
            },
            "simulation": {
                "duration_us": 100.0,
                "traffic_pattern": "random",
                "request_rate": 0.8,
            },
            "dvfs": {
                "enable": True,
                "voltage_mv": 800,
                "frequency_mhz": 1600,
            },
            "plugins": [
                {"name": "profiler"},
            ],
        }
        errors = ConfigSchema.validate(config)
        assert len(errors) == 0


class TestValidationError:
    def test_validation_error_message(self):
        """Test ValidationError message"""
        error = ValidationError("Test error", "field.subfield")
        assert error.message == "Test error"
        assert error.field == "field.subfield"
        assert "Test error" in str(error)
