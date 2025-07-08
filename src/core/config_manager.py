"""
Configuration management for the hybrid system
"""

import json
import os
from typing import Any

from ..core.logging import get_logger
from ..interfaces.core.config import ConfigProvider


class FileConfigProvider(ConfigProvider):
    """File-based configuration provider"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = get_logger(__name__)
        self._load_configs()

    def _load_configs(self):
        """Load all configuration files"""
        self.config = self._load_json("config.json")
        self.prompts = self._load_json("prompts.json")
        self.context_config = self._load_json("context.json")

    def _load_json(self, filename: str) -> dict[str, Any]:
        """Load JSON configuration file"""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath) as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(
                "Configuration file not found",
                extra={
                    "filepath": filepath,
                    "filename": filename,
                    "operation": "load_config",
                },
            )
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(
                "Failed to parse configuration file",
                extra={
                    "filepath": filepath,
                    "filename": filename,
                    "error": str(e),
                    "operation": "load_config",
                },
            )
            return {}

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_prompt(self, module: str, prompt_type: str) -> str:
        """Get prompt for specific module and type"""
        try:
            return self.prompts[module][prompt_type]
        except KeyError:
            return f"Default prompt for {module}.{prompt_type}"

    def get_context_config(self) -> dict[str, Any]:
        """Get context configuration"""
        return self.context_config


class ProviderFactory:
    """Factory for creating configuration providers"""

    @staticmethod
    def create_config_provider(provider_type: str, **kwargs) -> ConfigProvider:
        """Create configuration provider based on type"""
        if provider_type == "file":
            return FileConfigProvider(**kwargs)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    @staticmethod
    def create_context_provider(provider_type: str, **kwargs):
        """Create context provider based on type"""
        if provider_type == "sqlite":
            from .context_manager import SQLiteContextProvider

            return SQLiteContextProvider(**kwargs)
        else:
            raise ValueError(f"Unknown context provider type: {provider_type}")
