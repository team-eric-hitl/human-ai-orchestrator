"""
Configuration management interfaces

This module defines the contracts for configuration providers that handle
system configuration, prompts, and context settings.
"""

from abc import ABC, abstractmethod
from typing import Any


class ConfigProvider(ABC):
    """Abstract base class for configuration providers

    Configuration providers are responsible for loading and providing
    access to system configuration including:
    - Application settings and parameters
    - AI model prompts and templates
    - Context management configuration
    - Feature flags and toggles

    Implementations should handle:
    - Loading configuration from various sources (files, databases, remote)
    - Hierarchical configuration with defaults and overrides
    - Hot-reloading of configuration changes
    - Validation of configuration values
    """

    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key

        Should support dot notation for nested configuration access
        (e.g., 'database.host' for nested config structures).

        Args:
            key: Configuration key, may use dot notation for nested access
            default: Default value to return if key is not found

        Returns:
            The configuration value, or default if not found
        """
        pass

    @abstractmethod
    def get_prompt(self, module: str, prompt_type: str) -> str:
        """Get AI prompt for specific module and type

        Prompts are organized by module (e.g., 'classifier', 'responder')
        and type (e.g., 'system', 'user', 'fallback').

        Args:
            module: The module name requesting the prompt
            prompt_type: The type of prompt needed

        Returns:
            The prompt text, or a default prompt if not found
        """
        pass

    @abstractmethod
    def get_context_config(self) -> dict[str, Any]:
        """Get context management configuration

        Returns configuration specific to context management including:
        - Context window sizes
        - Retention policies
        - Summarization thresholds
        - Performance tuning parameters

        Returns:
            Dictionary containing context configuration parameters
        """
        pass
