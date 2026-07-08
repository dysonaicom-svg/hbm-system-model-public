"""Plugin Manager

Manages plugin lifecycle, discovery, and dependencies.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Type, Callable
from dataclasses import dataclass, field

from model.plugins.base import (
    PluginInterface,
    PluginMetadata,
    PluginState,
    PluginError,
    PluginLoadError,
    PluginDependencyError,
)


@dataclass
class PluginRegistration:
    """Registered plugin information"""
    plugin_class: Type[PluginInterface]
    metadata: PluginMetadata
    instance: Optional[PluginInterface] = None


class PluginManager:
    """Manages plugin lifecycle and dependencies"""

    def __init__(self):
        self._plugins: Dict[str, PluginRegistration] = {}
        self._load_paths: List[Path] = []
        self._initialized: bool = False

    @property
    def plugins(self) -> Dict[str, PluginRegistration]:
        """Get all registered plugins"""
        return self._plugins.copy()

    @property
    def loaded_plugins(self) -> List[str]:
        """Get names of loaded plugins"""
        return [
            name for name, reg in self._plugins.items()
            if reg.instance is not None
        ]

    def add_search_path(self, path: Path) -> None:
        """Add a directory to search for plugins

        Args:
            path: Directory path to search
        """
        if path not in self._load_paths:
            self._load_paths.append(path)

    def discover(self) -> List[str]:
        """Discover plugins in search paths

        Returns:
            List of discovered plugin names
        """
        discovered = []

        for load_path in self._load_paths:
            if not load_path.exists():
                continue

            for file_path in load_path.glob("*_plugin.py"):
                try:
                    name = self._discover_plugin_file(file_path)
                    if name:
                        discovered.append(name)
                except Exception:
                    pass

        return discovered

    def _discover_plugin_file(self, file_path: Path) -> Optional[str]:
        """Discover a plugin from a Python file"""
        module_name = file_path.stem

        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find plugin classes
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, PluginInterface) and
                attr is not PluginInterface):

                # Register the plugin
                instance = attr()
                self.register(attr, instance.metadata)
                return instance.metadata.name

        return None

    def register(self, plugin_class: Type[PluginInterface],
                metadata: Optional[PluginMetadata] = None) -> None:
        """Register a plugin class

        Args:
            plugin_class: Plugin class to register
            metadata: Plugin metadata (extracted from class if not provided)
        """
        if metadata is None:
            instance = plugin_class()
            metadata = instance.metadata

        if metadata.name in self._plugins:
            raise PluginLoadError(f"Plugin already registered: {metadata.name}")

        self._plugins[metadata.name] = PluginRegistration(
            plugin_class=plugin_class,
            metadata=metadata,
        )

    def unregister(self, name: str) -> None:
        """Unregister a plugin

        Args:
            name: Plugin name
        """
        if name not in self._plugins:
            return

        reg = self._plugins[name]
        if reg.instance is not None:
            reg.instance.unload()
            reg.instance = None

        del self._plugins[name]

    def load(self, name: str, config: Optional[Dict] = None) -> PluginInterface:
        """Load and initialize a plugin

        Args:
            name: Plugin name
            config: Plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin cannot be loaded
            PluginDependencyError: If dependencies are not met
        """
        if name not in self._plugins:
            raise PluginLoadError(f"Plugin not found: {name}")

        reg = self._plugins[name]

        # Check dependencies
        self._check_dependencies(name)

        # Instantiate if not already
        if reg.instance is None:
            try:
                reg.instance = reg.plugin_class()
            except Exception as e:
                raise PluginLoadError(f"Failed to instantiate plugin {name}: {e}")

        # Initialize
        if reg.instance.state == PluginState.UNLOADED:
            reg.instance.initialize(config or {})

        return reg.instance

    def unload(self, name: str) -> None:
        """Unload a plugin

        Args:
            name: Plugin name
        """
        if name not in self._plugins:
            return

        reg = self._plugins[name]
        if reg.instance is not None:
            reg.instance.unload()
            reg.instance = None

    def start(self, name: str) -> None:
        """Start a plugin

        Args:
            name: Plugin name
        """
        reg = self._plugins.get(name)
        if reg is None or reg.instance is None:
            raise PluginLoadError(f"Plugin not loaded: {name}")

        reg.instance.start()

    def stop(self, name: str) -> None:
        """Stop a plugin

        Args:
            name: Plugin name
        """
        reg = self._plugins.get(name)
        if reg is None or reg.instance is None:
            return

        reg.instance.stop()

    def start_all(self) -> None:
        """Start all loaded plugins in dependency order"""
        started: Set[str] = set()

        # Topological sort for dependency order
        def start_recursive(name: str):
            if name in started:
                return

            reg = self._plugins.get(name)
            if reg is None or reg.instance is None:
                return

            # Start dependencies first
            for dep in reg.metadata.dependencies:
                start_recursive(dep)

            # Start this plugin
            reg.instance.start()
            started.add(name)

        for name in self._plugins:
            start_recursive(name)

    def stop_all(self) -> None:
        """Stop all running plugins in reverse dependency order"""
        # Stop in reverse order
        for name in reversed(list(self._plugins.keys())):
            self.stop(name)

    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin instance by name

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        reg = self._plugins.get(name)
        return reg.instance if reg else None

    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name

        Args:
            name: Plugin name

        Returns:
            Plugin metadata or None
        """
        reg = self._plugins.get(name)
        return reg.metadata if reg else None

    def _check_dependencies(self, name: str, visited: Optional[Set[str]] = None) -> None:
        """Check that all dependencies are satisfied

        Args:
            name: Plugin name to check
            visited: Set of visited plugin names (for cycle detection)

        Raises:
            PluginDependencyError: If a dependency is not met
        """
        if visited is None:
            visited = set()

        if name in visited:
            raise PluginDependencyError(f"Circular dependency detected for {name}")

        visited.add(name)

        reg = self._plugins.get(name)
        if reg is None:
            raise PluginDependencyError(f"Plugin not found: {name}")

        for dep_name in reg.metadata.dependencies:
            if dep_name not in self._plugins:
                raise PluginDependencyError(
                    f"Plugin {name} requires {dep_name} which is not registered"
                )

            dep_reg = self._plugins[dep_name]
            if dep_reg.instance is None:
                raise PluginDependencyError(
                    f"Plugin {name} requires {dep_name} which is not loaded"
                )

            # Recursively check
            self._check_dependencies(dep_name, visited)

    def load_from_config(self, config: List[Dict]) -> None:
        """Load plugins from configuration list

        Args:
            config: List of plugin configurations
                [{"name": "plugin_name", "enabled": true, "config": {...}}]
        """
        for plugin_config in config:
            name = plugin_config.get("name")
            if not name:
                continue

            enabled = plugin_config.get("enabled", True)
            if not enabled:
                continue

            plugin_config_data = plugin_config.get("config", {})

            try:
                self.load(name, plugin_config_data)
                self.start(name)
            except PluginError as e:
                print(f"Warning: Failed to load plugin {name}: {e}")

    def get_stats(self) -> Dict[str, Dict]:
        """Get statistics for all plugins

        Returns:
            Dictionary of plugin statistics
        """
        stats = {}

        for name, reg in self._plugins.items():
            if reg.instance is not None:
                stats[name] = reg.instance.get_stats()
            else:
                stats[name] = {
                    "name": name,
                    "state": "not_loaded",
                }

        return stats
