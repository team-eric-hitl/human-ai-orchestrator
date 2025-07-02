"""
Unit tests for LocalAppFileHandler.

This module contains comprehensive tests for the LocalAppFileHandler class
which provides local file system operations for various file formats.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import matplotlib.pyplot as plt
import pandas as pd
import pytest
import yaml

from src.common.app_file_handling.app_file_handler import LocalAppFileHandler


class TestLocalAppFileHandler:
    """Test cases for the LocalAppFileHandler class."""

    def test_file_handler_initialization(self):
        """Test LocalAppFileHandler initialization."""
        handler = LocalAppFileHandler()

        assert handler.error_factory is not None
        assert hasattr(handler, "set_error_logger")

    def test_set_error_logger(self):
        """Test setting error logger."""
        handler = LocalAppFileHandler()
        mock_logger = Mock()

        handler.set_error_logger(mock_logger)

        assert handler.error_factory.app_logger == mock_logger

    def test_read_yaml_success(self):
        """Test successful YAML file reading."""
        handler = LocalAppFileHandler()

        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_data = {"key1": "value1", "key2": {"nested": "value2"}}
            yaml.dump(yaml_data, f)
            temp_file = f.name

        try:
            result = handler.read_yaml(temp_file)

            assert result == yaml_data
            assert result["key1"] == "value1"
            assert result["key2"]["nested"] == "value2"
        finally:
            os.unlink(temp_file)

    def test_read_yaml_file_not_found(self):
        """Test YAML reading when file doesn't exist."""
        handler = LocalAppFileHandler()
        non_existent_file = "/non/existent/file.yaml"

        with pytest.raises(Exception) as exc_info:
            handler.read_yaml(non_existent_file)

        assert "not found" in str(exc_info.value).lower()

    def test_read_yaml_malformed(self):
        """Test YAML reading with malformed content."""
        handler = LocalAppFileHandler()

        # Create temporary YAML file with malformed content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name

        try:
            with pytest.raises(Exception) as exc_info:
                handler.read_yaml(temp_file)

            assert "malformed" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_file)

    def test_write_yaml_success(self):
        """Test successful YAML file writing."""
        handler = LocalAppFileHandler()

        # Create temporary file path
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_file = f.name

        try:
            data = {"key1": "value1", "key2": {"nested": "value2"}}
            handler.write_yaml(data, temp_file)

            # Verify the file was written correctly
            with open(temp_file, "r") as f:
                result = yaml.safe_load(f)

            assert result == data
        finally:
            os.unlink(temp_file)

    def test_read_json_success(self):
        """Test successful JSON file reading."""
        handler = LocalAppFileHandler()

        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_data = {"key1": "value1", "key2": {"nested": "value2"}}
            json.dump(json_data, f)
            temp_file = f.name

        try:
            result = handler.read_json(temp_file)

            assert result == json_data
            assert result["key1"] == "value1"
            assert result["key2"]["nested"] == "value2"
        finally:
            os.unlink(temp_file)

    def test_read_json_file_not_found(self):
        """Test JSON reading when file doesn't exist."""
        handler = LocalAppFileHandler()
        non_existent_file = "/non/existent/file.json"

        with pytest.raises(Exception) as exc_info:
            handler.read_json(non_existent_file)

        assert "not found" in str(exc_info.value).lower()

    def test_read_json_malformed(self):
        """Test JSON reading with malformed content."""
        handler = LocalAppFileHandler()

        # Create temporary JSON file with malformed content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"key": "value", "incomplete":')
            temp_file = f.name

        try:
            with pytest.raises(Exception) as exc_info:
                handler.read_json(temp_file)

            assert "malformed" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_file)

    def test_write_json_success(self):
        """Test successful JSON file writing."""
        handler = LocalAppFileHandler()

        # Create temporary file path
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            data = {"key1": "value1", "key2": {"nested": "value2"}}
            handler.write_json(data, temp_file)

            # Verify the file was written correctly
            with open(temp_file, "r") as f:
                result = json.load(f)

            assert result == data
        finally:
            os.unlink(temp_file)

    def test_read_csv_success(self):
        """Test successful CSV file reading."""
        handler = LocalAppFileHandler()

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_content = "name,age,city\nJohn,30,New York\nJane,25,Boston"
            f.write(csv_content)
            temp_file = f.name

        try:
            result = handler.read_csv(temp_file)

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert list(result.columns) == ["name", "age", "city"]
            assert result.iloc[0]["name"] == "John"
            assert result.iloc[1]["city"] == "Boston"
        finally:
            os.unlink(temp_file)

    def test_read_csv_file_not_found(self):
        """Test CSV reading when file doesn't exist."""
        handler = LocalAppFileHandler()
        non_existent_file = "/non/existent/file.csv"

        with pytest.raises(Exception) as exc_info:
            handler.read_csv(non_existent_file)

        assert "not found" in str(exc_info.value).lower()

    def test_write_csv_success(self):
        """Test successful CSV file writing."""
        handler = LocalAppFileHandler()

        # Create temporary file path
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_file = f.name

        try:
            # Create test DataFrame
            df = pd.DataFrame(
                {
                    "name": ["John", "Jane"],
                    "age": [30, 25],
                    "city": ["New York", "Boston"],
                }
            )

            handler.write_csv(df, temp_file)

            # Verify the file was written correctly
            result = pd.read_csv(temp_file)

            pd.testing.assert_frame_equal(df, result)
        finally:
            os.unlink(temp_file)

    def test_ensure_directory_success(self):
        """Test successful directory creation."""
        handler = LocalAppFileHandler()

        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new" / "nested" / "directory"

            handler.ensure_directory(new_dir)

            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_ensure_directory_already_exists(self):
        """Test directory creation when directory already exists."""
        handler = LocalAppFileHandler()

        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir)

            # Should not raise an exception
            handler.ensure_directory(existing_dir)

            assert existing_dir.exists()

    def test_join_paths(self):
        """Test path joining functionality."""
        handler = LocalAppFileHandler()

        result = handler.join_paths("path1", "path2", "path3")

        assert isinstance(result, Path)
        assert str(result) == str(Path("path1") / "path2" / "path3")

    def test_resolve_project_root_path(self):
        """Test project root path resolution."""
        handler = LocalAppFileHandler()

        # Test with placeholder
        result = handler.resolve_project_root_path("${PROJECT_ROOT}/data")

        # Should resolve to actual path
        assert "${PROJECT_ROOT}" not in result
        assert result.endswith("/data")

    def test_load_yaml_files_in_directory_success(self):
        """Test loading YAML files from directory."""
        handler = LocalAppFileHandler()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test YAML files
            config1 = {"app": {"name": "test_app"}}
            config2 = {"database": {"host": "localhost"}}

            with open(temp_path / "config1.yaml", "w") as f:
                yaml.dump(config1, f)

            with open(temp_path / "config2.yaml", "w") as f:
                yaml.dump(config2, f)

            result = handler.load_yaml_files_in_directory(temp_path)

            assert "config1" in result
            assert "config2" in result
            assert result["config1"] == config1
            assert result["config2"] == config2

    def test_load_yaml_files_in_directory_with_required_files(self):
        """Test loading YAML files with required files check."""
        handler = LocalAppFileHandler()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create required file
            config = {"app": {"name": "test_app"}}
            with open(temp_path / "app_config.yaml", "w") as f:
                yaml.dump(config, f)

            result = handler.load_yaml_files_in_directory(
                temp_path, required_files=["app_config.yaml"]
            )

            assert "app_config" in result
            assert result["app_config"] == config

    def test_load_yaml_files_in_directory_missing_required(self):
        """Test loading YAML files with missing required files."""
        handler = LocalAppFileHandler()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Don't create the required file
            with pytest.raises(Exception) as exc_info:
                handler.load_yaml_files_in_directory(
                    temp_path, required_files=["missing_config.yaml"]
                )

            assert "missing" in str(exc_info.value).lower()

    def test_create_temp_directory(self):
        """Test temporary directory creation context manager."""
        handler = LocalAppFileHandler()

        with handler.create_temp_directory() as temp_dir:
            assert os.path.exists(temp_dir)
            assert os.path.isdir(temp_dir)

            # Create a file in the temp directory
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            assert test_file.exists()

        # Directory should be cleaned up after context exit
        assert not os.path.exists(temp_dir)

    def test_save_figure(self):
        """Test saving matplotlib figure."""
        handler = LocalAppFileHandler()

        # Create a simple matplotlib figure
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_file = f.name

        try:
            handler.save_figure(fig, temp_file)

            # Verify file was created and has content
            assert os.path.exists(temp_file)
            assert os.path.getsize(temp_file) > 0
        finally:
            os.unlink(temp_file)
            plt.close(fig)


class TestLocalAppFileHandlerIntegration:
    """Integration tests for LocalAppFileHandler."""

    def test_complete_file_workflow(self):
        """Test complete file handling workflow."""
        handler = LocalAppFileHandler()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test YAML workflow
            yaml_data = {"config": {"setting": "value"}}
            yaml_file = temp_path / "config.yaml"

            handler.write_yaml(yaml_data, yaml_file)
            loaded_yaml = handler.read_yaml(yaml_file)
            assert loaded_yaml == yaml_data

            # Test JSON workflow
            json_data = {"data": {"items": [1, 2, 3]}}
            json_file = temp_path / "data.json"

            handler.write_json(json_data, json_file)
            loaded_json = handler.read_json(json_file)
            assert loaded_json == json_data

            # Test CSV workflow
            df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
            csv_file = temp_path / "data.csv"

            handler.write_csv(df, csv_file)
            loaded_csv = handler.read_csv(csv_file)
            pd.testing.assert_frame_equal(df, loaded_csv)

    def test_error_handling_integration(self):
        """Test error handling integration."""
        mock_logger = Mock()
        handler = LocalAppFileHandler()
        handler.set_error_logger(mock_logger)

        # Test error handling with non-existent file
        with pytest.raises(Exception):
            handler.read_yaml("/non/existent/file.yaml")

        # Verify error factory has logger
        assert handler.error_factory.app_logger == mock_logger

    def test_directory_operations_integration(self):
        """Test directory operations integration."""
        handler = LocalAppFileHandler()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create nested directory structure
            nested_dir = temp_path / "level1" / "level2" / "level3"
            handler.ensure_directory(nested_dir)

            assert nested_dir.exists()
            assert nested_dir.is_dir()

            # Test path joining
            joined_path = handler.join_paths(temp_path, "test", "file.txt")
            assert str(joined_path) == str(temp_path / "test" / "file.txt")

            # Test project root path resolution
            resolved_path = handler.resolve_project_root_path("${PROJECT_ROOT}/config")
            assert "${PROJECT_ROOT}" not in resolved_path
