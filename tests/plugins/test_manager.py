"""Tests for plugin manager module"""

import pytest
from model.plugins.manager import PluginManager, PluginRegistration
from model.plugins.base import (
    PluginInterface,
    PluginMetadata,
    PluginState,
    PluginLoadError,
    PluginDependencyError,
)


class TestPluginManager:
    def test_manager_creation(self):
        """Test plugin manager creation"""
        manager = PluginManager()
        assert len(manager.plugins) == 0
        assert len(manager.loaded_plugins) == 0

    def test_register_plugin(self):
        """Test plugin registration"""
        manager = PluginManager()

        class TestPlugin(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test", version="1.0.0")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin)
        assert "test" in manager.plugins

    def test_register_duplicate(self):
        """Test registering duplicate plugin"""
        manager = PluginManager()

        class TestPlugin(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test", version="1.0.0")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin)

        with pytest.raises(PluginLoadError):
            manager.register(TestPlugin)

    def test_unregister_plugin(self):
        """Test plugin unregistration"""
        manager = PluginManager()

        class TestPlugin(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test", version="1.0.0")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin)
        manager.unregister("test")
        assert "test" not in manager.plugins

    def test_load_plugin(self):
        """Test plugin loading"""
        manager = PluginManager()

        class TestPlugin(PluginInterface):
            def __init__(self):
                super().__init__()
                self.config_received = None

            @property
            def metadata(self):
                return PluginMetadata(name="test", version="1.0.0")

            def _do_initialize(self, config):
                self.config_received = config

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin)
        plugin = manager.load("test", {"key": "value"})

        assert plugin is not None
        assert plugin.config_received == {"key": "value"}
        assert "test" in manager.loaded_plugins

    def test_load_nonexistent_plugin(self):
        """Test loading nonexistent plugin"""
        manager = PluginManager()

        with pytest.raises(PluginLoadError):
            manager.load("nonexistent")

    def test_unload_plugin(self):
        """Test plugin unloading"""
        manager = PluginManager()

        class TestPlugin(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test", version="1.0.0")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin)
        manager.load("test")
        manager.unload("test")

        assert "test" not in manager.loaded_plugins

    def test_get_plugin(self):
        """Test getting plugin instance"""
        manager = PluginManager()

        class TestPlugin(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test", version="1.0.0")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin)
        manager.load("test")

        plugin = manager.get_plugin("test")
        assert plugin is not None

    def test_get_metadata(self):
        """Test getting plugin metadata"""
        manager = PluginManager()

        class TestPlugin(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test", version="2.0.0", description="Test")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin)
        meta = manager.get_metadata("test")

        assert meta is not None
        assert meta.name == "test"
        assert meta.version == "2.0.0"

    def test_start_all(self):
        """Test starting all plugins"""
        manager = PluginManager()

        class TestPlugin1(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test1", version="1.0.0")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        class TestPlugin2(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test2", version="1.0.0")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin1)
        manager.register(TestPlugin2)
        manager.load("test1")
        manager.load("test2")

        manager.start_all()

        assert manager.get_plugin("test1").state == PluginState.RUNNING
        assert manager.get_plugin("test2").state == PluginState.RUNNING

    def test_dependency_check(self):
        """Test dependency checking"""
        manager = PluginManager()

        class DependentPlugin(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="dependent", version="1.0.0", dependencies=["missing"])

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(DependentPlugin)

        with pytest.raises(PluginDependencyError):
            manager.load("dependent")

    def test_stats(self):
        """Test getting plugin stats"""
        manager = PluginManager()

        class TestPlugin(PluginInterface):
            @property
            def metadata(self):
                return PluginMetadata(name="test", version="1.0.0")

            def _do_initialize(self, config):
                pass

            def _do_start(self):
                pass

            def _do_stop(self):
                pass

        manager.register(TestPlugin)
        manager.load("test")

        stats = manager.get_stats()
        assert "test" in stats
