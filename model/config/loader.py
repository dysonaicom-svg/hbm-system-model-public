"""Configuration Loader

Loads configuration from various file formats and sources.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import tomli as toml
    TOML_AVAILABLE = True
except ImportError:
    try:
        import toml as toml
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False


class LoadError(Exception):
    """Configuration loading error"""
    pass


class ConfigLoader:
    """Configuration file loader supporting YAML, JSON, and TOML formats"""

    SUPPORTED_FORMATS = ["yaml", "yml", "json", "toml"]

    @classmethod
    def load(cls, filepath: str, validate: bool = True) -> Dict[str, Any]:
        """Load configuration from a file

        Args:
            filepath: Path to configuration file
            validate: Whether to validate the configuration

        Returns:
            Configuration dictionary

        Raises:
            LoadError: If file cannot be loaded
        """
        path = Path(filepath)

        if not path.exists():
            raise LoadError(f"Configuration file not found: {filepath}")

        suffix = path.suffix.lower().lstrip('.')

        if suffix not in cls.SUPPORTED_FORMATS:
            raise LoadError(f"Unsupported file format: {suffix}")

        try:
            if suffix in ("yaml", "yml"):
                config = cls._load_yaml(path)
            elif suffix == "json":
                config = cls._load_json(path)
            elif suffix == "toml":
                config = cls._load_toml(path)
            else:
                raise LoadError(f"Unsupported format: {suffix}")
        except Exception as e:
            raise LoadError(f"Failed to load {filepath}: {e}")

        return config

    @classmethod
    def _load_yaml(cls, path: Path) -> Dict[str, Any]:
        """Load YAML configuration"""
        if not YAML_AVAILABLE:
            raise LoadError("PyYAML is not installed. Install with: pip install pyyaml")

        with open(path, 'r') as f:
            content = yaml.safe_load(f)
        return content or {}

    @classmethod
    def _load_json(cls, path: Path) -> Dict[str, Any]:
        """Load JSON configuration"""
        with open(path, 'r') as f:
            return json.load(f)

    @classmethod
    def _load_toml(cls, path: Path) -> Dict[str, Any]:
        """Load TOML configuration"""
        if not TOML_AVAILABLE:
            raise LoadError("TOML support is not installed. Install with: pip install tomli")

        with open(path, 'rb') as f:
            return toml.load(f)

    @classmethod
    def load_multiple(cls, filepaths: List[str]) -> Dict[str, Any]:
        """Load and merge multiple configuration files

        Later files override earlier ones.

        Args:
            filepaths: List of configuration file paths

        Returns:
            Merged configuration dictionary
        """
        merged = {}

        for filepath in filepaths:
            config = cls.load(filepath, validate=False)
            merged = cls._deep_merge(merged, config)

        return merged

    @classmethod
    def _deep_merge(cls, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @classmethod
    def load_with_env(cls, filepath: str, env_prefix: str = "HBM4_") -> Dict[str, Any]:
        """Load configuration and override with environment variables

        Environment variables take precedence over file values.
        Variable names are converted from ENV_PREFIX_SECTION_KEY to section.key.

        Args:
            filepath: Path to configuration file
            env_prefix: Prefix for environment variables (default: HBM4_)

        Returns:
            Configuration dictionary with environment overrides
        """
        config = cls.load(filepath, validate=False)

        # Override with environment variables
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(env_prefix):
                continue

            # Parse environment variable name
            parts = env_key[len(env_prefix):].lower().split('_')
            if len(parts) < 2:
                continue

            section = parts[0]
            key = '_'.join(parts[1:])

            if section in config:
                config[section][key] = cls._parse_env_value(env_value)

        return config

    @classmethod
    def _parse_env_value(cls, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String
        return value

    @classmethod
    def save(cls, config: Dict[str, Any], filepath: str) -> None:
        """Save configuration to a file

        Args:
            config: Configuration dictionary
            filepath: Output file path
        """
        path = Path(filepath)
        suffix = path.suffix.lower().lstrip('.')

        if suffix not in cls.SUPPORTED_FORMATS:
            raise LoadError(f"Unsupported file format: {suffix}")

        if suffix in ("yaml", "yml"):
            cls._save_yaml(config, path)
        elif suffix == "json":
            cls._save_json(config, path)
        elif suffix == "toml":
            cls._save_toml(config, path)

    @classmethod
    def _save_yaml(cls, config: Dict[str, Any], path: Path) -> None:
        """Save YAML configuration"""
        if not YAML_AVAILABLE:
            raise LoadError("PyYAML is not installed")

        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def _save_json(cls, config: Dict[str, Any], path: Path) -> None:
        """Save JSON configuration"""
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def _save_toml(cls, config: Dict[str, Any], path: Path) -> None:
        """Save TOML configuration"""
        if not TOML_AVAILABLE:
            raise LoadError("TOML support is not installed")

        with open(path, 'wb') as f:
            toml.dump(config, f)

    @classmethod
    def detect_format(cls, filepath: str) -> Optional[str]:
        """Detect configuration file format from extension

        Args:
            filepath: Path to configuration file

        Returns:
            Detected format ('yaml', 'json', 'toml') or None
        """
        path = Path(filepath)
        suffix = path.suffix.lower().lstrip('.')

        if suffix in cls.SUPPORTED_FORMATS:
            return suffix

        return None
