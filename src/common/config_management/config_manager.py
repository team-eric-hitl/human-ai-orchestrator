"""
Configuration Manager Implementation

This module provides a concrete implementation of the BaseConfigManager
interface for centralized configuration management. It supports nested
configuration files across multiple directories and can handle
model-specific configs in subdirectories while maintaining the existing
functionality.
"""

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional

import yaml

from src.base_interfaces.common import (
    BaseAppFileHandler,
    BaseConfigManager,
    BaseErrorHandler,
)
from src.common.app_file_handling.app_file_handler import LocalAppFileHandler
from src.common.error_handling.error_handler_factory import ErrorHandlerFactory

logger = logging.getLogger(__name__)


class ConfigManager(BaseConfigManager):
    """
    Concrete implementation of BaseConfigManager for centralized configuration
    management.

    This class provides a comprehensive configuration management system that
    supports nested configuration files across multiple directories. It can
    handle model-specific configs in subdirectories while maintaining the
    existing functionality.
    """

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        app_file_handler: Optional[BaseAppFileHandler] = None,
        error_handler: Optional[BaseErrorHandler] = None,
    ) -> None:
        """
        Initialize the config manager with an optional config directory and
        file handler.

        Args:
            config_dir: Directory containing configuration files. If None, a
                       default directory will be used.
            app_file_handler: File handler for loading configuration files. If
                             None, the implementation should provide a default
                             handler.
            error_handler: Error handler for configuration errors. If None,
                          standard exceptions will be used.
        """
        self.app_file_handler = (
            LocalAppFileHandler() if app_file_handler is None else app_file_handler
        )
        self.error_handler = error_handler
        self.error_factory = ErrorHandlerFactory()
        self.config_dir = (
            self._get_default_config_dir() if config_dir is None else config_dir
        )
        self._load_configurations()

    def set_error_logger(self, app_logger):
        """
        Set the logger for error handling.

        Args:
            app_logger: Logger instance to use for error logging
        """
        self.error_factory.set_logger(app_logger)

    def _get_default_config_dir(self) -> Path:
        """
        Get the default configuration directory from the config_path.yaml file.

        Falls back to a default path if the file cannot be loaded.

        Returns:
            Path to the default configuration directory

        Raises:
            FileNotFoundError: If config_path.yaml cannot be found
            yaml.YAMLError: If config_path.yaml is malformed
        """
        config_path_file = Path(__file__).parent / "config_path.yaml"
        try:
            print(f"Loading config_path.yaml from: {config_path_file}")
            config_path_data = self.app_file_handler.read_yaml(
                config_path_file,
            )
            config_path = config_path_data.get("default_config_dir")
            print(f"Config path: {config_path}")
            if config_path is None:
                error_msg = "default_config_dir not found in config_path.yaml"
                if self.error_handler:
                    raise self.error_handler
                else:
                    raise ValueError(error_msg)
            return Path(config_path)

        except (FileNotFoundError, yaml.YAMLError, ValueError) as e:
            logger.warning(
                "Could not load config_path.yaml: %s. Using default path.",
                str(e),
            )
            # Fallback to the original hardcoded path
            return Path(__file__).parent.parent.parent / "configs"

    def get_config(self) -> "ConfigManager":
        """
        Get the complete configuration object.

        Returns:
            ConfigManager object containing all configuration data with
            attribute access (e.g., config.database.host)
        """
        return self

    def _load_configurations(self) -> None:
        """
        Load all configuration files, including those in nested directories.

        Handles the new structure with model-specific configs in
        subdirectories. This method is called during initialization to set
        up the configuration object.

        Raises:
            FileNotFoundError: If required configuration files are missing
            yaml.YAMLError: If configuration files are malformed
        """
        # First load main config files
        print(f"Loading configuration files from: {self.config_dir}")
        config_dict = self.app_file_handler.load_yaml_files_in_directory(
            self.config_dir, required_files=["app_config.yaml"]
        )

        # Load nested configurations
        nested_configs = self._load_nested_configurations()

        # Merge nested configurations into main config
        config_dict = self._merge_configurations(config_dict, nested_configs)

        # Convert to SimpleNamespace and set attributes
        config_obj = self._dict_to_namespace(config_dict)
        for key, value in vars(config_obj).items():
            setattr(self, key, value)

    def _load_nested_configurations(self) -> Dict[str, Any]:
        """
        Recursively load configurations from nested directories.

        Returns a dictionary with nested configuration data organized by
        directory structure.

        Returns:
            Dictionary containing nested configuration data organized by
            directory structure

        Raises:
            yaml.YAMLError: If any nested configuration files are malformed
        """
        nested_configs = {}

        for item in self.config_dir.rglob("*.yaml"):
            # Skip files in the root config directory
            if item.parent == self.config_dir:
                continue

            try:
                # Create nested dictionary structure based on directory path
                current_level = nested_configs
                relative_path = item.relative_to(self.config_dir)
                parts = list(relative_path.parts[:-1])  # Exclude filename

                # Build nested structure
                for part in parts:
                    current_level = current_level.setdefault(part, {})

                # Load and add config file content
                config_content = self.app_file_handler.read_yaml(item)
                key = item.stem
                current_level[key] = config_content

                logger.debug("Loaded nested configuration from: %s", item)
            except Exception as e:
                logger.error(
                    "Error loading nested configuration %s: %s",
                    item,
                    str(e),
                )
                raise

        return nested_configs

    def _merge_configurations(
        self, main_config: Dict[str, Any], nested_configs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge nested configurations into the main configuration dictionary.

        Handles potential naming conflicts and maintains structure.

        Args:
            main_config: Main configuration dictionary loaded from the root
                        config directory
            nested_configs: Nested configurations dictionary loaded from
                           subdirectories

        Returns:
            Merged configuration dictionary
        """
        merged = main_config.copy()

        # Merge nested configurations
        for key, value in nested_configs.items():
            if isinstance(value, dict):
                if key not in merged:
                    merged[key] = {}
                merged[key] = self._deep_merge(merged[key], value)

        return merged

    def _deep_merge(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries, preserving nested structures.

        Performs a deep merge of two dictionaries, preserving nested
        structures and handling conflicts by preferring values from dict2.

        Args:
            dict1: First dictionary to merge
            dict2: Second dictionary to merge (takes precedence in conflicts)

        Returns:
            Merged dictionary with all nested structures preserved
        """
        result = dict1.copy()

        for key, value in dict2.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _dict_to_namespace(self, d: Dict[str, Any]) -> Any:
        """
        Recursively convert a dictionary to SimpleNamespace.

        Handles path resolution for string values that contain placeholders.

        Args:
            d: Dictionary to convert to SimpleNamespace

        Returns:
            SimpleNamespace object or original value if not a dictionary
        """
        if isinstance(d, str):
            # Only resolve paths that contain the PROJECT_ROOT placeholder
            if "${PROJECT_ROOT}" in d:
                return self.app_file_handler.resolve_project_root_path(d)
            return d
        if not isinstance(d, dict):
            return d
        ns_dict = {k: self._dict_to_namespace(v) for k, v in d.items()}
        return SimpleNamespace(**ns_dict)

    @staticmethod
    def _construct_suggestion(loader: yaml.Loader, node: yaml.Node) -> dict:
        """
        Custom constructor for Optuna suggestion tags.

        Args:
            loader: YAML loader instance
            node: YAML node to construct

        Returns:
            Constructed mapping from the YAML node

        Raises:
            yaml.constructor.ConstructorError: If the node is not a mapping
            node
        """
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node)
        raise yaml.constructor.ConstructorError(
            None,
            None,
            f"expected a mapping node but found {type(node).__name__}",
            node.start_mark,
        )
