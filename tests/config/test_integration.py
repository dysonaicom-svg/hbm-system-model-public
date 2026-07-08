"""Integration tests for config and plugin systems"""

import pytest
from model.config.manager import ConfigManager
from model.config.loader import ConfigLoader
from model.plugins.manager import PluginManager
from model.plugins.base import PluginMetadata, PluginInterface


class TestConfigPluginIntegration:
    """Integration tests for config and plugin systems"""

    def test_load_config_and_initialize_plugins(self):
        """Test loading config and initializing plugins"""
        # Reset singleton
        ConfigManager.reset_instance()

        # Create test config file
        import tempfile
        import json
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text(json.dumps({
                "hbm4": {
                    "channels": 32,
                    "data_rate_gbps": 16,
                },
                "simulation": {
                    "duration_us": 100.0,
                    "traffic_pattern": "random",
                },
                "plugins": [
                    {"name": "logger", "enabled": True, "config": {"level": "INFO"}},
                    {"name": "validator", "enabled": True, "config": {}},
                ]
            }))

            # Load configuration
            config = ConfigLoader.load(str(config_file), validate=False)

            # Initialize plugins
            manager = PluginManager()

            class LoggerPlugin(PluginInterface):
                @property
                def metadata(self):
                    return PluginMetadata(name="logger", version="1.0.0")

                def _do_initialize(self, config):
                    self.config = config

                def _do_start(self):
                    pass

                def _do_stop(self):
                    pass

            class ValidatorPlugin(PluginInterface):
                @property
                def metadata(self):
                    return PluginMetadata(name="validator", version="1.0.0")

                def _do_initialize(self, config):
                    self.config = config

                def _do_start(self):
                    pass

                def _do_stop(self):
                    pass

            manager.register(LoggerPlugin)
            manager.register(ValidatorPlugin)

            # Load plugins from config
            manager.load_from_config(config.get("plugins", []))

            # Verify
            assert "logger" in manager.loaded_plugins
            assert "validator" in manager.loaded_plugins

    def test_validator_uses_config_schema(self):
        """Test that validator uses config schema rules"""
        from model.config.schema import ConfigSchema
        from model.plugins.builtins.validator_plugin import ValidatorPlugin

        plugin = ValidatorPlugin()
        plugin.initialize({})

        # The validator should have rules loaded from schema
        assert len(plugin._rules) > 0

        # Test validation
        valid_config = {
            "hbm4": {"channels": 32, "data_rate_gbps": 16},
            "simulation": {"duration_us": 100, "request_rate": 0.5},
        }

        result = plugin.validate(valid_config)
        assert result.valid

        # Test invalid config
        invalid_config = {
            "hbm4": {"channels": 100},  # Invalid
        }

        result = plugin.validate(invalid_config)
        assert not result.valid

    def test_watcher_notifies_on_config_change(self):
        """Test that watchers are notified on configuration changes"""
        ConfigManager.reset_instance()
        manager = ConfigManager.get_instance()

        notifications = []

        def watcher(config):
            notifications.append(config.copy())

        manager.add_watcher(watcher)
        manager.set("test.key", "value")

        assert len(notifications) == 1
        assert notifications[0]["test"]["key"] == "value"
