"""Tests for config loader module"""

import json
import pytest
from pathlib import Path
from model.config.loader import ConfigLoader, LoadError


class TestConfigLoader:
    def test_detect_format_yaml(self):
        """Test format detection for YAML"""
        assert ConfigLoader.detect_format("config.yaml") == "yaml"
        assert ConfigLoader.detect_format("config.yml") == "yml"

    def test_detect_format_json(self):
        """Test format detection for JSON"""
        assert ConfigLoader.detect_format("config.json") == "json"

    def test_detect_format_toml(self):
        """Test format detection for TOML"""
        assert ConfigLoader.detect_format("config.toml") == "toml"

    def test_detect_format_unknown(self):
        """Test format detection for unknown format"""
        assert ConfigLoader.detect_format("config.txt") is None

    def test_load_json_file(self, tmp_path):
        """Test loading JSON configuration"""
        config_file = tmp_path / "config.json"
        config_data = {"hbm4": {"channels": 32}, "simulation": {"duration_us": 100}}
        config_file.write_text(json.dumps(config_data))

        config = ConfigLoader.load(str(config_file), validate=False)
        assert config["hbm4"]["channels"] == 32
        assert config["simulation"]["duration_us"] == 100

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file"""
        with pytest.raises(LoadError) as exc_info:
            ConfigLoader.load("/nonexistent/path/config.json")
        assert "not found" in str(exc_info.value)

    def test_load_unsupported_format(self, tmp_path):
        """Test loading unsupported format"""
        config_file = tmp_path / "config.txt"
        config_file.write_text("some content")

        with pytest.raises(LoadError) as exc_info:
            ConfigLoader.load(str(config_file))
        assert "Unsupported" in str(exc_info.value)

    def test_load_multiple(self, tmp_path):
        """Test loading and merging multiple files"""
        # Base config
        config1 = tmp_path / "base.json"
        config1.write_text(json.dumps({"hbm4": {"channels": 32}}))

        # Override config
        config2 = tmp_path / "override.json"
        config2.write_text(json.dumps({"hbm4": {"data_rate_gbps": 16}}))

        config = ConfigLoader.load_multiple([str(config1), str(config2)])
        assert config["hbm4"]["channels"] == 32
        assert config["hbm4"]["data_rate_gbps"] == 16

    def test_load_multiple_deep_merge(self, tmp_path):
        """Test deep merge of nested configs"""
        config1 = tmp_path / "base.json"
        config1.write_text(json.dumps({
            "hbm4": {"channels": 32},
            "simulation": {"duration_us": 100}
        }))

        config2 = tmp_path / "override.json"
        config2.write_text(json.dumps({
            "simulation": {"traffic_pattern": "random"}
        }))

        config = ConfigLoader.load_multiple([str(config1), str(config2)])
        assert config["hbm4"]["channels"] == 32
        assert config["simulation"]["duration_us"] == 100
        assert config["simulation"]["traffic_pattern"] == "random"

    def test_parse_env_value_boolean(self):
        """Test parsing boolean environment values"""
        assert ConfigLoader._parse_env_value("true") is True
        assert ConfigLoader._parse_env_value("True") is True
        assert ConfigLoader._parse_env_value("yes") is True
        assert ConfigLoader._parse_env_value("1") is True
        assert ConfigLoader._parse_env_value("false") is False

    def test_parse_env_value_integer(self):
        """Test parsing integer environment values"""
        assert ConfigLoader._parse_env_value("42") == 42
        assert ConfigLoader._parse_env_value("-10") == -10

    def test_parse_env_value_float(self):
        """Test parsing float environment values"""
        assert ConfigLoader._parse_env_value("3.14") == 3.14
        assert ConfigLoader._parse_env_value("-0.5") == -0.5

    def test_parse_env_value_string(self):
        """Test parsing string environment values"""
        assert ConfigLoader._parse_env_value("hello") == "hello"
        assert ConfigLoader._parse_env_value("random") == "random"

    def test_save_json(self, tmp_path):
        """Test saving JSON configuration"""
        config = {"hbm4": {"channels": 32}}
        output_file = tmp_path / "output.json"

        ConfigLoader.save(config, str(output_file))
        assert output_file.exists()

        with open(output_file) as f:
            loaded = json.load(f)
        assert loaded["hbm4"]["channels"] == 32
