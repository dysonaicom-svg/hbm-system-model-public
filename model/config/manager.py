"""Configuration Manager

Unified configuration management with validation and hot-reload.
"""

import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

from model.config.schema import ConfigSchema, ValidationError
from model.config.loader import ConfigLoader, LoadError


@dataclass
class ConfigSource:
    """Configuration source"""
    path: str
    format: str
    priority: int = 0


@dataclass
class ConfigState:
    """Current configuration state"""
    config: Dict[str, Any]
    sources: List[ConfigSource] = field(default_factory=list)
    last_modified: float = 0.0


class ConfigManager:
    """Unified configuration manager with hot-reload support"""

    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._state: Optional[ConfigState] = None
        self._watchers: List[Callable[[Dict[str, Any]], None]] = []
        self._watch_thread: Optional[threading.Thread] = None
        self._watching: bool = False

    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """Get singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.stop_watching()
            cls._instance = None

    def load(self, *filepaths: str, validate: bool = True,
             env_override: bool = True) -> Dict[str, Any]:
        """Load configuration from one or more files

        Args:
            *filepaths: Configuration file paths (in order of precedence)
            validate: Whether to validate the configuration
            env_override: Whether to allow environment variable overrides

        Returns:
            Merged configuration dictionary

        Raises:
            LoadError: If files cannot be loaded
            ValidationError: If validation fails
        """
        if not filepaths:
            return self._get_default_config()

        # Load and merge configurations
        config = ConfigLoader.load_multiple(list(filepaths))

        # Apply environment overrides
        if env_override:
            config = self._apply_env_overrides(config)

        # Validate
        if validate:
            errors = ConfigSchema.validate(config)
            if errors:
                error_messages = [e.message for e in errors]
                raise ValidationError(f"Configuration validation failed: {', '.join(error_messages)}")

        # Store state
        sources = [ConfigSource(path=p, format=ConfigLoader.detect_format(p) or "unknown",
                               priority=i) for i, p in enumerate(filepaths)]
        self._state = ConfigState(
            config=config,
            sources=sources,
            last_modified=os.path.getmtime(filepaths[-1]) if filepaths else 0
        )

        # Notify watchers
        self._notify_watchers(config)

        return config

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key path

        Args:
            key_path: Dot-separated path (e.g., 'hbm4.channels')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self._state is None:
            return default

        return self._get_nested(self._state.config, key_path, default)

    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value by dot-separated key path

        Args:
            key_path: Dot-separated path (e.g., 'hbm4.channels')
            value: New value
        """
        if self._state is None:
            self._state = ConfigState(config={}, sources=[])

        self._set_nested(self._state.config, key_path, value)
        self._notify_watchers(self._state.config)

    def get_config(self) -> Dict[str, Any]:
        """Get full configuration dictionary"""
        if self._state is None:
            return self._get_default_config()
        return self._state.config.copy()

    def reload(self) -> Dict[str, Any]:
        """Reload configuration from sources

        Returns:
            Reloaded configuration
        """
        if self._state is None or not self._state.sources:
            return self._get_default_config()

        filepaths = [s.path for s in sorted(self._state.sources, key=lambda s: s.priority)]
        return self.load(*filepaths)

    def add_watcher(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add a configuration change watcher

        Args:
            callback: Function called when configuration changes
        """
        if callback not in self._watchers:
            self._watchers.append(callback)

    def remove_watcher(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a configuration change watcher

        Args:
            callback: Function to remove
        """
        if callback in self._watchers:
            self._watchers.remove(callback)

    def start_watching(self, interval_seconds: float = 1.0) -> None:
        """Start watching configuration files for changes

        Args:
            interval_seconds: Check interval
        """
        if self._watching:
            return

        self._watching = True
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._watch_thread.start()

    def stop_watching(self) -> None:
        """Stop watching configuration files"""
        self._watching = False
        if self._watch_thread is not None:
            self._watch_thread.join(timeout=2.0)
            self._watch_thread = None

    def _watch_loop(self, interval: float) -> None:
        """Watch loop for configuration changes"""
        import time

        while self._watching:
            if self._state is not None and self._state.sources:
                for source in self._state.sources:
                    try:
                        mtime = os.path.getmtime(source.path)
                        if mtime > self._state.last_modified:
                            self.reload()
                            break
                    except OSError:
                        pass

            time.sleep(interval)

    def _notify_watchers(self, config: Dict[str, Any]) -> None:
        """Notify all watchers of configuration change"""
        for watcher in self._watchers:
            try:
                watcher(config)
            except Exception:
                pass  # Don't let watcher errors break the manager

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        result = config.copy()

        for env_key, env_value in os.environ.items():
            if not env_key.startswith("HBM4_"):
                continue

            # Parse: HBM4_SECTION_KEY -> section.key
            parts = env_key[5:].lower().split('_')
            if len(parts) < 2:
                continue

            section = parts[0]
            key = '_'.join(parts[1:])
            value = self._parse_env_value(env_value)

            if section in result:
                result[section][key] = value

        return result

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """Parse environment variable to appropriate type"""
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            return value

    @staticmethod
    def _get_nested(data: Dict, key_path: str, default: Any = None) -> Any:
        """Get nested dictionary value"""
        keys = key_path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    @staticmethod
    def _set_nested(data: Dict, key_path: str, value: Any) -> None:
        """Set nested dictionary value"""
        keys = key_path.split('.')
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "hbm4": {
                "channels": 32,
                "data_rate_gbps": 16,
                "queue_depth": 128,
                "address_mapping": "rbc",
                "qos_levels": 16,
                "refresh_mode": "all_bank",
            },
            "simulation": {
                "duration_us": 100.0,
                "traffic_pattern": "random",
                "request_rate": 0.8,
                "read_ratio": 0.7,
                "max_requests_per_cycle": 4,
            },
            "dvfs": {
                "enable": False,
                "voltage_mv": 800,
                "frequency_mhz": 1600,
            },
        }
