"""
Local Application File Handler Implementation

This module provides a concrete implementation of the BaseAppFileHandler
interface for local file system operations. It handles reading and writing
various file formats including YAML, JSON, CSV, and provides file system
utilities.
"""

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import matplotlib.figure
import pandas as pd
import yaml

from src.base_interfaces.common import BaseAppFileHandler
from src.common.error_handling.error_handler_factory import ErrorHandlerFactory


class LocalAppFileHandler(BaseAppFileHandler):
    """
    Concrete implementation of BaseAppFileHandler for local file system
    operations.

    This class provides local file system implementations for all file handling
    operations including reading/writing various file formats, directory
    management, and file system utilities.
    """

    def __init__(self):
        """Initialize the file handler with error handling capabilities."""
        self.error_factory = ErrorHandlerFactory()

    def set_error_logger(self, app_logger):
        """
        Set the logger for error handling.

        Args:
            app_logger: Logger instance to use for error logging
        """
        self.error_factory.set_logger(app_logger)

    def read_yaml(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read and parse a YAML configuration file.

        Args:
            path: Path to the YAML file to read

        Returns:
            Dictionary containing the parsed YAML data

        Raises:
            FileOperationError: If the file cannot be read or parsed
        """
        path = Path(path)
        try:
            if not path.exists():
                raise self.error_factory.create_error_handler(
                    "file_operation",
                    f"YAML file not found: {path}",
                    file_path=str(path),
                    operation="read",
                )

            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"YAML file is malformed: {path}",
                file_path=str(path),
                operation="read",
                yaml_error=str(e),
            )
        except Exception as e:
            # Don't re-wrap FileOperationError exceptions
            file_op_error = self.error_factory._error_classes["file_operation"]
            if isinstance(e, file_op_error):
                raise
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error reading YAML file: {path}",
                file_path=str(path),
                operation="read",
                original_error=str(e),
            )

    def write_yaml(self, data: Dict[str, Any], path: Union[str, Path]) -> None:
        """
        Write data to a YAML file.

        Args:
            data: Dictionary data to write to the YAML file
            path: Path where the YAML file should be written

        Raises:
            FileOperationError: If the file cannot be written due to
            permissions or other file system errors
        """
        path = Path(path)
        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, indent=2)
        except (PermissionError, OSError) as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error writing YAML file: {path}",
                file_path=str(path),
                operation="write",
                original_error=str(e),
            )

    def read_json(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read and parse a JSON file.

        Args:
            path: Path to the JSON file to read

        Returns:
            Dictionary containing the parsed JSON data

        Raises:
            FileOperationError: If the file cannot be read or parsed
        """
        path = Path(path)
        try:
            if not path.exists():
                raise self.error_factory.create_error_handler(
                    "file_operation",
                    f"JSON file not found: {path}",
                    file_path=str(path),
                    operation="read",
                )

            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"JSON file is malformed: {path}",
                file_path=str(path),
                operation="read",
                json_error=str(e),
            )
        except Exception as e:
            # Don't re-wrap FileOperationError exceptions
            file_op_error = self.error_factory._error_classes["file_operation"]
            if isinstance(e, file_op_error):
                raise
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error reading JSON file: {path}",
                file_path=str(path),
                operation="read",
                original_error=str(e),
            )

    def write_json(self, data: Dict[str, Any], path: Union[str, Path]) -> None:
        """
        Write data to a JSON file.

        Args:
            data: Dictionary data to write to the JSON file
            path: Path where the JSON file should be written

        Raises:
            FileOperationError: If the file cannot be written due to
            permissions or other file system errors
        """
        path = Path(path)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except (PermissionError, OSError) as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error writing JSON file: {path}",
                file_path=str(path),
                operation="write",
                original_error=str(e),
            )

    def read_csv(self, path: Union[str, Path]) -> pd.DataFrame:
        """
        Read a CSV file into a pandas DataFrame.

        Args:
            path: Path to the CSV file to read

        Returns:
            DataFrame containing the CSV data

        Raises:
            FileOperationError: If the file cannot be read or parsed
        """
        path = Path(path)
        try:
            if not path.exists():
                raise self.error_factory.create_error_handler(
                    "file_operation",
                    f"CSV file not found: {path}",
                    file_path=str(path),
                    operation="read",
                )

            return pd.read_csv(path)
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"CSV file is malformed: {path}",
                file_path=str(path),
                operation="read",
                pandas_error=str(e),
            )
        except Exception as e:
            # Don't re-wrap FileOperationError exceptions
            file_op_error = self.error_factory._error_classes["file_operation"]
            if isinstance(e, file_op_error):
                raise
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error reading CSV file: {path}",
                file_path=str(path),
                operation="read",
                original_error=str(e),
            )

    def write_csv(self, df: pd.DataFrame, path: Union[str, Path]) -> None:
        """
        Write a pandas DataFrame to a CSV file.

        Args:
            df: DataFrame to write to CSV
            path: Path where the CSV file should be written

        Raises:
            FileOperationError: If the file cannot be written due to
            permissions or other file system errors
        """
        path = Path(path)
        try:
            df.to_csv(path, index=False)
        except (PermissionError, OSError) as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error writing CSV file: {path}",
                file_path=str(path),
                operation="write",
                original_error=str(e),
            )

    def ensure_directory(self, path: Union[str, Path]) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Path to the directory to ensure exists

        Raises:
            FileOperationError: If the directory cannot be created due to
            permissions or other file system errors
        """
        path = Path(path)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error creating directory: {path}",
                file_path=str(path),
                operation="create_directory",
                original_error=str(e),
            )

    def join_paths(self, *paths: Union[str, Path]) -> Path:
        """
        Join path components into a single path.

        Args:
            *paths: Variable number of path components to join

        Returns:
            Combined path object
        """
        return Path(*paths)

    def resolve_project_root_path(self, path: str) -> str:
        """
        Resolve paths that contain ${PROJECT_ROOT} to absolute paths.

        Args:
            path: Path string that may contain ${PROJECT_ROOT} placeholder

        Returns:
            Resolved absolute path string
        """
        if "${PROJECT_ROOT}" in path:
            project_root = Path(__file__).parent.parent.parent
            return path.replace("${PROJECT_ROOT}", str(project_root))
        return path

    def load_yaml_files_in_directory(
        self, directory: Path, required_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Load and merge all YAML files in a directory.

        Args:
            directory: Directory containing YAML files to load
            required_files: Optional list of filenames that must exist in the
                           directory

        Returns:
            Dictionary containing merged data from all YAML files

        Raises:
            FileOperationError: If any required files are missing or if any
            YAML files are malformed
        """
        config_dict = {}

        # Check for required files first
        if required_files:
            missing_files = []
            for required_file in required_files:
                if not (directory / required_file).exists():
                    missing_files.append(required_file)
            if missing_files:
                base_msg = "Required config files not found: "
                files_msg = f"{', '.join(missing_files)}"
                error_msg = base_msg + files_msg
                raise self.error_factory.create_error_handler(
                    "file_operation",
                    error_msg,
                    directory=str(directory),
                    missing_files=missing_files,
                    operation="load_yaml_files",
                )

        # Load all YAML files
        try:
            for config_file in directory.glob("*.yaml"):
                file_name = config_file.stem  # Get filename without extension
                config_data = self.read_yaml(config_file)
                config_dict[file_name] = config_data
        except Exception as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error loading YAML files from directory: {directory}",
                directory=str(directory),
                operation="load_yaml_files",
                original_error=str(e),
            )
        return config_dict

    @contextmanager
    def create_temp_directory(self) -> Iterator[str]:
        """
        Create a temporary directory using tempfile.TemporaryDirectory.

        The directory will be automatically cleaned up when the context exits.

        Returns:
            Context manager that yields the path to the temporary directory

        Example:
            with file_handler.create_temp_directory() as temp_dir:
                # Use temp_dir for temporary file operations
                pass
            # Directory is automatically cleaned up
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def save_figure(
        self, fig: matplotlib.figure.Figure, path: Union[str, Path]
    ) -> None:
        """
        Save a matplotlib figure to the specified path.

        Args:
            fig: Matplotlib figure to save
            path: Path where the figure should be saved

        Raises:
            FileOperationError: If the file cannot be written due to
            permissions or other file system errors
        """
        path = Path(path)
        try:
            fig.savefig(path, bbox_inches="tight", dpi=300)
        except (PermissionError, OSError) as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error saving figure: {path}",
                file_path=str(path),
                operation="save_figure",
                original_error=str(e),
            )
