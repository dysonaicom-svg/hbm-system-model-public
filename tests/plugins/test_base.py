"""Tests for plugin base module"""

import pytest
from model.plugins.base import (
    PluginInterface,
    PluginMetadata,
    PluginState,
    PluginError,
    PluginLoadError,
    PluginDependencyError,
)


class TestPluginMetadata:
    def test_metadata_creation(self):
        """Test metadata creation"""
        meta = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            dependencies=["dep1", "dep2"],
        )
        assert meta.name == "test_plugin"
        assert meta.version == "1.0.0"
        assert "dep1" in meta.dependencies


class TestPluginState:
    def test_plugin_states(self):
        """Test plugin state enumeration"""
        assert PluginState.UNLOADED.value == "unloaded"
        assert PluginState.LOADED.value == "loaded"
        assert PluginState.RUNNING.value == "running"
        assert PluginState.ERROR.value == "error"


class TestPluginInterface:
    def test_plugin_interface_abstract(self):
        """Test that PluginInterface is abstract"""
        with pytest.raises(TypeError):
            PluginInterface()


class ConcreteTestPlugin(PluginInterface):
    """Concrete test plugin implementation"""

    def __init__(self):
        super().__init__()
        self.init_called = False
        self.start_called = False
        self.stop_called = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="test_plugin", version="1.0.0")

    def _do_initialize(self, config):
        self.init_called = True

    def _do_start(self):
        self.start_called = True

    def _do_stop(self):
        self.stop_called = True


class ConcreteTestPluginImplementation:
    def test_plugin_initialization(self):
        """Test plugin initialization"""
        plugin = ConcreteTestPlugin()
        assert plugin.state == PluginState.UNLOADED

        plugin.initialize({})
        assert plugin.state == PluginState.INITIALIZED
        assert plugin.init_called

    def test_plugin_start(self):
        """Test plugin start"""
        plugin = ConcreteTestPlugin()
        plugin.initialize({})

        plugin.start()
        assert plugin.state == PluginState.RUNNING
        assert plugin.start_called

    def test_plugin_stop(self):
        """Test plugin stop"""
        plugin = ConcreteTestPlugin()
        plugin.initialize({})
        plugin.start()

        plugin.stop()
        assert plugin.state == PluginState.STOPPED
        assert plugin.stop_called

    def test_plugin_unload(self):
        """Test plugin unload"""
        plugin = ConcreteTestPlugin()
        plugin.initialize({})
        plugin.start()

        plugin.unload()
        assert plugin.state == PluginState.UNLOADED

    def test_plugin_start_without_init(self):
        """Test starting plugin without initialization"""
        plugin = ConcreteTestPlugin()

        with pytest.raises(RuntimeError):
            plugin.start()

    def test_plugin_stats(self):
        """Test plugin stats"""
        plugin = ConcreteTestPlugin()
        stats = plugin.get_stats()

        assert stats["name"] == "test_plugin"
        assert stats["version"] == "1.0.0"
        assert stats["state"] == "unloaded"


class TestPluginErrors:
    def test_plugin_error(self):
        """Test PluginError"""
        error = PluginError("Test error")
        assert str(error) == "Test error"

    def test_plugin_load_error(self):
        """Test PluginLoadError"""
        error = PluginLoadError("Load failed")
        assert str(error) == "Load failed"

    def test_plugin_dependency_error(self):
        """Test PluginDependencyError"""
        error = PluginDependencyError("Missing dependency")
        assert str(error) == "Missing dependency"
