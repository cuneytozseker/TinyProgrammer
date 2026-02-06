"""
Configuration Manager for TinyProgrammer Web UI

Handles loading/saving configuration overrides that persist across restarts.
Merges user overrides with defaults from config.py.
"""

import os
import json
from typing import Any, Dict

# Path to overrides file (same directory as main config)
OVERRIDES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'config_overrides.json'
)


class ConfigManager:
    """Manages configuration with override support."""

    def __init__(self):
        self._overrides = self._load_overrides()

    def _load_overrides(self) -> Dict[str, Any]:
        """Load overrides from JSON file."""
        if os.path.exists(OVERRIDES_FILE):
            try:
                with open(OVERRIDES_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[ConfigManager] Error loading overrides: {e}")
        return {}

    def _save_overrides(self) -> bool:
        """Save overrides to JSON file."""
        try:
            with open(OVERRIDES_FILE, 'w') as f:
                json.dump(self._overrides, f, indent=2)
            return True
        except IOError as e:
            print(f"[ConfigManager] Error saving overrides: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value, checking overrides first."""
        if key in self._overrides:
            return self._overrides[key]

        # Fall back to config.py
        import config
        return getattr(config, key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values (defaults + overrides)."""
        import config

        # Start with all config.py values
        result = {}
        for key in dir(config):
            if key.isupper() and not key.startswith('_'):
                result[key] = getattr(config, key)

        # Overlay with overrides
        result.update(self._overrides)

        return result

    def save_overrides(self, updates: Dict[str, Any]) -> bool:
        """Save new override values."""
        self._overrides.update(updates)
        success = self._save_overrides()

        # Also update the live config module
        if success:
            self._apply_to_config(updates)

        return success

    def _apply_to_config(self, updates: Dict[str, Any]):
        """Apply overrides to the live config module."""
        import config

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
                print(f"[ConfigManager] Updated config.{key} = {value}")

    def reset(self, key: str = None):
        """Reset override(s) to defaults."""
        if key:
            if key in self._overrides:
                del self._overrides[key]
        else:
            self._overrides = {}
        self._save_overrides()


# Singleton instance
_manager = None


def get_config_manager() -> ConfigManager:
    """Get the singleton config manager instance."""
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager
