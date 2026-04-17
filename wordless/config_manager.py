"""Configuration manager for persistent settings."""

import json
from pathlib import Path
from typing import Any, Optional

CONFIG_DIR = Path.home() / ".wordless"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default configuration
DEFAULTS = {
    "api_key": "",                                      # User's auth token for our gateway
    "gateway_url": "http://localhost:8000",            # Our hosted gateway (or local for dev)
    "repo_path": "/Users/tejaskoli/ollama-learn",
    "top_k": 5,                                         # Search results
    "default_hops": 3,                                  # Call graph expansion
}


class ConfigManager:
    """Manage persistent Wordless configuration."""

    def __init__(self):
        CONFIG_DIR.mkdir(exist_ok=True)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a config value."""
        config = self._load()
        if key not in config and key in DEFAULTS:
            return DEFAULTS[key]
        return config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value."""
        if key not in DEFAULTS:
            raise ValueError(f"Unknown config key: {key}")
        
        config = self._load()
        config[key] = value
        self._save(config)

    def reset(self, key: str) -> None:
        """Reset a config value to default."""
        if key not in DEFAULTS:
            raise ValueError(f"Unknown config key: {key}")
        
        config = self._load()
        if key in config:
            del config[key]
        self._save(config)

    def reset_all(self) -> None:
        """Reset all config to defaults."""
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

    def list_all(self) -> dict:
        """List all config values with current and default."""
        config = self._load()
        result = {}
        for key in DEFAULTS:
            result[key] = {
                "current": config.get(key, DEFAULTS[key]),
                "default": DEFAULTS[key],
            }
        return result

    def _load(self) -> dict:
        """Load config from file."""
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self, config: dict) -> None:
        """Save config to file."""
        CONFIG_FILE.write_text(json.dumps(config, indent=2))


# Global instance
_manager = ConfigManager()


def get(key: str, default: Optional[Any] = None) -> Any:
    """Get a config value."""
    return _manager.get(key, default)


def set_config(key: str, value: Any) -> None:
    """Set a config value."""
    return _manager.set(key, value)


def get_manager() -> ConfigManager:
    """Get the config manager instance."""
    return _manager
