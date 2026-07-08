"""Tests for config manager module"""

import pytest
from model.config.manager import ConfigManager, ConfigSource, ConfigState


class TestConfigManager:
    def test_singleton_instance(self):
        """Test singleton pattern"""
        ConfigManager.reset_instance()
        instance1 = ConfigManager.get_instance()
        instance2 = ConfigManager.get_instance()
        assert instance1 is instance2

    def test_reset_instance(self):
        """Test instance reset"""
        ConfigManager.reset_instance()
        instance1 = ConfigManager.get_instance()
        ConfigManager.reset_instance()
        instance2 = ConfigManager.get_instance()
        assert instance1 is not instance2

    def test_get_default_config(self):
        """Test getting default configuration"""
        ConfigManager.reset_instance()
        manager = ConfigManager.get_instance()

        config = manager.get_config()
        assert "hbm4" in config
        assert config["hbm4"]["channels"] == 32

    def test_get_with_default(self):
        """Test get with default value"""
        ConfigManager.reset_instance()
        manager = ConfigManager.get_instance()

        value = manager.get("nonexistent.key", "default")
        assert value == "default"

    def test_get_nested_value(self):
        """Test getting nested value"""
        ConfigManager.reset_instance()
        manager = ConfigManager.get_instance()

        manager._state = ConfigState(config={
            "hbm4": {"channels": 32}
        })

        value = manager.get("hbm4.channels")
        assert value == 32

    def test_set_nested_value(self):
        """Test setting nested value"""
        ConfigManager.reset_instance()
        manager = ConfigManager.get_instance()

        manager.set("hbm4.channels", 64)
        value = manager.get("hbm4.channels")
        assert value == 64

    def test_add_watcher(self):
        """Test adding configuration watcher"""
        ConfigManager.reset_instance()
        manager = ConfigManager.get_instance()

        changes = []

        def watcher(config):
            changes.append(config)

        manager.add_watcher(watcher)
        manager.set("hbm4.channels", 128)

        assert len(changes) == 1
        assert changes[0]["hbm4"]["channels"] == 128

    def test_remove_watcher(self):
        """Test removing configuration watcher"""
        ConfigManager.reset_instance()
        manager = ConfigManager.get_instance()

        def watcher(config):
            pass

        manager.add_watcher(watcher)
        manager.remove_watcher(watcher)
        manager.set("hbm4.channels", 128)

        # No assertion - watcher should not be called

    def test_get_nested_static(self):
        """Test static get_nested method"""
        data = {"a": {"b": {"c": 42}}}

        value = ConfigManager._get_nested(data, "a.b.c")
        assert value == 42

        value = ConfigManager._get_nested(data, "a.b")
        assert value == {"c": 42}

        value = ConfigManager._get_nested(data, "nonexistent", "default")
        assert value == "default"

    def test_set_nested_static(self):
        """Test static set_nested method"""
        data = {}

        ConfigManager._set_nested(data, "a.b.c", 42)
        assert data == {"a": {"b": {"c": 42}}}

        ConfigManager._set_nested(data, "a.b.d", 100)
        assert data["a"]["b"]["c"] == 42
        assert data["a"]["b"]["d"] == 100
