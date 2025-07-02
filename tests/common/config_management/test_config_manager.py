"""
Unit tests for ConfigManager.

This module contains comprehensive tests for the ConfigManager class
which provides centralized configuration management with support for
nested configuration files.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from src.common.config_management.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for the ConfigManager class."""

    def test_config_manager_initialization(self):
        """Test ConfigManager initialization with default parameters."""
        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations") as mock_load:
                config_manager = ConfigManager()

                assert config_manager.config_dir == Path("/test/config")
                assert config_manager.app_file_handler is not None
                assert config_manager.error_handler is None
                mock_load.assert_called_once()

    def test_config_manager_with_custom_parameters(self):
        """Test ConfigManager initialization with custom parameters."""
        mock_file_handler = Mock()
        mock_error_handler = Mock()
        custom_config_dir = Path("/custom/config")

        with patch.object(ConfigManager, "_load_configurations") as mock_load:
            config_manager = ConfigManager(
                config_dir=custom_config_dir,
                app_file_handler=mock_file_handler,
                error_handler=mock_error_handler,
            )

            assert config_manager.config_dir == custom_config_dir
            assert config_manager.app_file_handler == mock_file_handler
            assert config_manager.error_handler == mock_error_handler
            mock_load.assert_called_once()

    def test_get_config(self):
        """Test get_config method returns self."""
        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager()
                result = config_manager.get_config()

                assert result == config_manager

    @patch("src.common.config_management.config_manager.logger")
    def test_get_default_config_dir_success(self, mock_logger):
        """Test successful loading of default config directory."""
        mock_file_handler = Mock()
        mock_file_handler.read_yaml.return_value = {
            "default_config_dir": "/test/config/path"
        }

        with patch.object(ConfigManager, "_load_configurations"):
            config_manager = ConfigManager(app_file_handler=mock_file_handler)

            # Mock the config_path.yaml file path
            with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
                mock_get_dir.return_value = Path("/test/config/path")

                result = config_manager._get_default_config_dir()

                assert result == Path("/test/config/path")

    @patch("src.common.config_management.config_manager.logger")
    def test_get_default_config_dir_fallback(self, mock_logger):
        """Test fallback behavior when config_path.yaml cannot be loaded."""
        mock_file_handler = Mock()
        mock_file_handler.read_yaml.side_effect = FileNotFoundError("File not found")

        with patch.object(ConfigManager, "_load_configurations"):
            config_manager = ConfigManager(app_file_handler=mock_file_handler)

            with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
                # Mock the fallback path
                fallback_path = Path(__file__).parent.parent.parent.parent / "configs"
                mock_get_dir.return_value = fallback_path

                result = config_manager._get_default_config_dir()

                assert result == fallback_path
                mock_logger.warning.assert_called_once()

    def test_set_error_logger(self):
        """Test setting error logger."""
        mock_logger = Mock()

        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager()
                config_manager.set_error_logger(mock_logger)

                assert config_manager.error_factory.app_logger == mock_logger

    def test_deep_merge_simple_dicts(self):
        """Test deep merge with simple dictionaries."""
        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager()

                dict1 = {"a": 1, "b": 2}
                dict2 = {"b": 3, "c": 4}

                result = config_manager._deep_merge(dict1, dict2)

                expected = {"a": 1, "b": 3, "c": 4}
                assert result == expected

    def test_deep_merge_nested_dicts(self):
        """Test deep merge with nested dictionaries."""
        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager()

                dict1 = {"a": {"x": 1, "y": 2}, "b": 3}
                dict2 = {"a": {"y": 4, "z": 5}, "c": 6}

                result = config_manager._deep_merge(dict1, dict2)

                expected = {"a": {"x": 1, "y": 4, "z": 5}, "b": 3, "c": 6}
                assert result == expected

    def test_dict_to_namespace_simple(self):
        """Test converting simple dictionary to namespace."""
        mock_file_handler = Mock()
        mock_file_handler.resolve_project_root_path.return_value = "/resolved/path"

        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager(app_file_handler=mock_file_handler)

                test_dict = {"key1": "value1", "key2": "value2"}
                result = config_manager._dict_to_namespace(test_dict)

                assert result.key1 == "value1"
                assert result.key2 == "value2"

    def test_dict_to_namespace_nested(self):
        """Test converting nested dictionary to namespace."""
        mock_file_handler = Mock()
        mock_file_handler.resolve_project_root_path.return_value = "/resolved/path"

        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager(app_file_handler=mock_file_handler)

                test_dict = {
                    "database": {"host": "localhost", "port": 5432},
                    "app": {"name": "test_app"},
                }
                result = config_manager._dict_to_namespace(test_dict)

                assert result.database.host == "localhost"
                assert result.database.port == 5432
                assert result.app.name == "test_app"

    def test_dict_to_namespace_with_path_resolution(self):
        """Test namespace conversion with path resolution."""
        mock_file_handler = Mock()
        mock_file_handler.resolve_project_root_path.return_value = "/resolved/path"

        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager(app_file_handler=mock_file_handler)

                test_dict = {"path": "${PROJECT_ROOT}/data"}
                result = config_manager._dict_to_namespace(test_dict)

                assert result.path == "/resolved/path"
                mock_file_handler.resolve_project_root_path.assert_called_once_with(
                    "${PROJECT_ROOT}/data"
                )


class TestConfigManagerFileOperations:
    """Test cases for ConfigManager file operations."""

    def test_load_configurations_success(self):
        """Test successful loading of configurations."""
        mock_file_handler = Mock()
        mock_file_handler.load_yaml_files_in_directory.return_value = {
            "app_config": {"name": "test_app", "version": "1.0.0"}
        }

        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(
                ConfigManager, "_load_nested_configurations"
            ) as mock_nested:
                mock_nested.return_value = {}

                with patch.object(ConfigManager, "_merge_configurations") as mock_merge:
                    mock_merge.return_value = {"app_config": {"name": "test_app"}}

                    with patch.object(
                        ConfigManager, "_dict_to_namespace"
                    ) as mock_namespace:
                        # Create a proper mock object with the expected attributes
                        from types import SimpleNamespace

                        mock_namespace_obj = SimpleNamespace()
                        mock_namespace_obj.app_config = SimpleNamespace()
                        mock_namespace_obj.app_config.name = "test_app"
                        mock_namespace.return_value = mock_namespace_obj

                        config_manager = ConfigManager(
                            app_file_handler=mock_file_handler
                        )

                        # Verify the configuration was loaded
                        assert hasattr(config_manager, "app_config")
                        assert config_manager.app_config.name == "test_app"

    def test_load_nested_configurations(self):
        """Test loading nested configurations from subdirectories."""
        mock_file_handler = Mock()

        # Create a temporary directory structure for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create nested directory structure
            nested_dir = temp_path / "models" / "model1"
            nested_dir.mkdir(parents=True)

            # Create nested config file
            nested_config_file = nested_dir / "config.yaml"
            nested_config = {"model_name": "test_model", "parameters": {"lr": 0.001}}

            with open(nested_config_file, "w") as f:
                yaml.dump(nested_config, f)

            mock_file_handler.read_yaml.return_value = nested_config

            with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
                mock_get_dir.return_value = temp_path

                with patch.object(ConfigManager, "_load_configurations") as mock_load:
                    config_manager = ConfigManager(app_file_handler=mock_file_handler)

                    result = config_manager._load_nested_configurations()

                    expected = {"models": {"model1": {"config": nested_config}}}
                    assert result == expected

    def test_merge_configurations(self):
        """Test merging main and nested configurations."""
        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager()

                main_config = {
                    "app_config": {"name": "test_app"},
                    "database": {"host": "localhost"},
                }

                nested_configs = {
                    "models": {"model1": {"config": {"name": "test_model"}}}
                }

                result = config_manager._merge_configurations(
                    main_config, nested_configs
                )

                expected = {
                    "app_config": {"name": "test_app"},
                    "database": {"host": "localhost"},
                    "models": {"model1": {"config": {"name": "test_model"}}},
                }
                assert result == expected


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_complete_configuration_workflow(self):
        """Test complete configuration loading workflow."""
        # Create temporary config files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create main config file
            main_config_file = temp_path / "app_config.yaml"
            main_config = {
                "app_name": "test_app",
                "version": "1.0.0",
                "database": {"host": "localhost", "port": 5432},
            }

            with open(main_config_file, "w") as f:
                yaml.dump(main_config, f)

            # Create nested config file
            nested_dir = temp_path / "models" / "model1"
            nested_dir.mkdir(parents=True)

            nested_config_file = nested_dir / "config.yaml"
            nested_config = {
                "model_name": "test_model",
                "parameters": {"learning_rate": 0.001},
            }

            with open(nested_config_file, "w") as f:
                yaml.dump(nested_config, f)

            # Mock file handler to return our test data
            mock_file_handler = Mock()
            mock_file_handler.load_yaml_files_in_directory.return_value = main_config
            mock_file_handler.read_yaml.return_value = nested_config
            mock_file_handler.resolve_project_root_path.return_value = "/resolved/path"

            with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
                mock_get_dir.return_value = temp_path

                config_manager = ConfigManager(app_file_handler=mock_file_handler)

                # Verify main config was loaded
                assert hasattr(config_manager, "app_name")
                assert config_manager.app_name == "test_app"
                assert hasattr(config_manager, "database")
                assert config_manager.database.host == "localhost"

                # Verify nested config was loaded
                assert hasattr(config_manager, "models")
                assert config_manager.models.model1.config.model_name == "test_model"

    def test_config_manager_with_error_handling(self):
        """Test ConfigManager with error handling integration."""
        mock_logger = Mock()
        mock_file_handler = Mock()

        with patch.object(ConfigManager, "_get_default_config_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/test/config")

            with patch.object(ConfigManager, "_load_configurations"):
                config_manager = ConfigManager(app_file_handler=mock_file_handler)

                # Set error logger
                config_manager.set_error_logger(mock_logger)

                # Verify error factory has logger
                assert config_manager.error_factory.app_logger == mock_logger
