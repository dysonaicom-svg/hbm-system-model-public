"""Plugin Base Classes

Abstract base classes and interfaces for the plugin system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class PluginState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.config_schema is None:
            self.config_schema = {}


class PluginInterface(ABC):
    """Abstract base class for all plugins"""

    def __init__(self):
        self._state = PluginState.UNLOADED
        self._config: Dict[str, Any] = {}
        self._metadata: Optional[PluginMetadata] = None

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata (name, version, etc.)"""
        pass

    @property
    def state(self) -> PluginState:
        """Current plugin state"""
        return self._state

    @property
    def config(self) -> Dict[str, Any]:
        """Plugin configuration"""
        return self._config

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration

        Args:
            config: Plugin-specific configuration
        """
        if self._state not in (PluginState.LOADED, PluginState.UNLOADED):
            raise RuntimeError(f"Cannot initialize plugin in state {self._state}")

        self._state = PluginState.INITIALIZING
        self._config = config

        try:
            self._do_initialize(config)
            self._state = PluginState.INITIALIZED
        except Exception as e:
            self._state = PluginState.ERROR
            raise PluginError(f"Plugin initialization failed: {e}") from e

    def start(self) -> None:
        """Start the plugin"""
        if self._state != PluginState.INITIALIZED:
            raise RuntimeError(f"Cannot start plugin in state {self._state}")

        self._state = PluginState.STARTING

        try:
            self._do_start()
            self._state = PluginState.RUNNING
        except Exception as e:
            self._state = PluginState.ERROR
            raise PluginError(f"Plugin start failed: {e}") from e

    def stop(self) -> None:
        """Stop the plugin"""
        if self._state not in (PluginState.RUNNING, PluginState.STARTING):
            return

        self._state = PluginState.STOPPING

        try:
            self._do_stop()
            self._state = PluginState.STOPPED
        except Exception as e:
            self._state = PluginState.ERROR
            raise PluginError(f"Plugin stop failed: {e}") from e

    def unload(self) -> None:
        """Unload the plugin"""
        self.stop()
        self._state = PluginState.UNLOADED
        self._config = {}

    @abstractmethod
    def _do_initialize(self, config: Dict[str, Any]) -> None:
        """Internal initialization logic"""
        pass

    @abstractmethod
    def _do_start(self) -> None:
        """Internal start logic"""
        pass

    @abstractmethod
    def _do_stop(self) -> None:
        """Internal stop logic"""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin statistics"""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "state": self._state.value,
        }


class PluginError(Exception):
    """Plugin-related error"""
    pass


class PluginLoadError(PluginError):
    """Error loading a plugin"""
    pass


class PluginDependencyError(PluginError):
    """Missing plugin dependency"""
    pass
