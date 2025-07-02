"""
Base Configuration Manager Interface

This module defines the abstract base class for configuration management in the 
application. It provides a standardized interface for loading, merging, and 
accessing configuration data from various sources.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Any, Optional


class BaseConfigManager(ABC):
    """
    Abstract base class for configuration management.

    This class defines the interface for configuration management operations including
    loading configuration files, merging nested configurations, and providing access
    to configuration data through a SimpleNamespace interface.
    """

    @abstractmethod
    def __init__(
        self, config_dir: Optional[Path] = None, app_file_handler: Optional[Any] = None
    ) -> None:
        """
        Initialize the config manager with an optional config directory and file handler.

        Args:
            config_dir: Directory containing configuration files. If None, a default
                       directory will be used.
            app_file_handler: File handler for loading configuration files. If None,
                             the implementation should provide a default handler.
        """
        pass

    @abstractmethod
    def get_config(self) -> SimpleNamespace:
        """
        Get the complete configuration object.

        Returns:
            SimpleNamespace object containing all configuration data with attribute
            access (e.g., config.database.host)
        """
        pass

    @abstractmethod
    def _load_configurations(self) -> None:
        """
        Load all configuration files and set up the configuration object.

        This method should be called during initialization to load and merge all
        configuration files from the config directory and any nested subdirectories.

        Raises:
            FileNotFoundError: If required configuration files are missing
            yaml.YAMLError: If configuration files are malformed
        """
        pass

    @abstractmethod
    def _load_nested_configurations(self) -> Dict[str, Any]:
        """
        Load configurations from nested subdirectories.

        Recursively searches for configuration files in subdirectories of the main
        config directory and loads them into a nested dictionary structure.

        Returns:
            Dictionary containing nested configuration data organized by directory
            structure
        """
        pass

    @abstractmethod
    def _merge_configurations(
        self, main_config: Dict[str, Any], nested_configs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge nested configurations with the main configuration.

        Combines the main configuration dictionary with nested configurations,
        handling potential naming conflicts and maintaining the hierarchical structure.

        Args:
            main_config: Main configuration dictionary loaded from the root config
                        directory
            nested_configs: Nested configurations dictionary loaded from
                           subdirectories

        Returns:
            Merged configuration dictionary
        """
        pass

    @abstractmethod
    def _deep_merge(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries.

        Performs a deep merge of two dictionaries, preserving nested structures
        and handling conflicts by preferring values from dict2.

        Args:
            dict1: First dictionary to merge
            dict2: Second dictionary to merge (takes precedence in conflicts)

        Returns:
            Merged dictionary with all nested structures preserved
        """
        pass

    @abstractmethod
    def _dict_to_namespace(self, d: Dict[str, Any]) -> Any:
        """
        Convert a dictionary to SimpleNamespace recursively.

        Recursively converts a dictionary structure to SimpleNamespace objects,
        allowing attribute-style access to configuration values. Also handles
        path resolution for string values that contain placeholders.

        Args:
            d: Dictionary to convert to SimpleNamespace

        Returns:
            SimpleNamespace object or original value if not a dictionary
        """
        pass
