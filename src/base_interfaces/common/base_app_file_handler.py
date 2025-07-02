"""
Base App File Handler Interface

This module defines the abstract base class for file handling operations in the application.
It provides a standardized interface for reading and writing various file formats including
YAML, JSON, CSV, and handling file system operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Dict, Any, List, ContextManager
import pandas as pd
import matplotlib.pyplot as plt


class BaseAppFileHandler(ABC):
    """
    Abstract base class for file handling operations.

    This class defines the interface for file handling operations including reading/writing
    various file formats (YAML, JSON, CSV), directory management, and file system utilities.
    Concrete implementations should handle the actual file system operations.
    """

    @abstractmethod
    def read_yaml(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read and parse a YAML configuration file.

        Args:
            path: Path to the YAML file to read

        Returns:
            Dictionary containing the parsed YAML data

        Raises:
            FileNotFoundError: If the specified file does not exist
            yaml.YAMLError: If the YAML file is malformed
        """
        pass

    @abstractmethod
    def write_yaml(self, data: Dict[str, Any], path: Union[str, Path]) -> None:
        """
        Write data to a YAML file.

        Args:
            data: Dictionary data to write to the YAML file
            path: Path where the YAML file should be written

        Raises:
            PermissionError: If the file cannot be written due to permissions
            OSError: If there are other file system errors
        """
        pass

    @abstractmethod
    def read_json(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read and parse a JSON file.

        Args:
            path: Path to the JSON file to read

        Returns:
            Dictionary containing the parsed JSON data

        Raises:
            FileNotFoundError: If the specified file does not exist
            json.JSONDecodeError: If the JSON file is malformed
        """
        pass

    @abstractmethod
    def write_json(self, data: Dict[str, Any], path: Union[str, Path]) -> None:
        """
        Write data to a JSON file.

        Args:
            data: Dictionary data to write to the JSON file
            path: Path where the JSON file should be written

        Raises:
            PermissionError: If the file cannot be written due to permissions
            OSError: If there are other file system errors
        """
        pass

    @abstractmethod
    def read_csv(self, path: Union[str, Path]) -> pd.DataFrame:
        """
        Read a CSV file into a pandas DataFrame.

        Args:
            path: Path to the CSV file to read

        Returns:
            DataFrame containing the CSV data

        Raises:
            FileNotFoundError: If the specified file does not exist
            pd.errors.EmptyDataError: If the CSV file is empty
            pd.errors.ParserError: If the CSV file cannot be parsed
        """
        pass

    @abstractmethod
    def write_csv(self, df: pd.DataFrame, path: Union[str, Path]) -> None:
        """
        Write a pandas DataFrame to a CSV file.

        Args:
            df: DataFrame to write to CSV
            path: Path where the CSV file should be written

        Raises:
            PermissionError: If the file cannot be written due to permissions
            OSError: If there are other file system errors
        """
        pass

    @abstractmethod
    def ensure_directory(self, path: Union[str, Path]) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Path to the directory to ensure exists

        Raises:
            PermissionError: If the directory cannot be created due to permissions
            OSError: If there are other file system errors
        """
        pass

    @abstractmethod
    def join_paths(self, *paths: Union[str, Path]) -> Path:
        """
        Join path components into a single path.

        Args:
            *paths: Variable number of path components to join

        Returns:
            Combined path object
        """
        pass

    @abstractmethod
    def resolve_project_root_path(self, path: str) -> str:
        """
        Resolve paths that contain ${PROJECT_ROOT} to absolute paths.

        Args:
            path: Path string that may contain ${PROJECT_ROOT} placeholder

        Returns:
            Resolved absolute path string
        """
        pass

    @abstractmethod
    def load_yaml_files_in_directory(
        self, directory: Path, required_files: List[str] = None
    ) -> Dict[str, Any]:
        """
        Load and merge all YAML files in a directory.

        Args:
            directory: Directory containing YAML files to load
            required_files: Optional list of filenames that must exist in the directory

        Returns:
            Dictionary containing merged data from all YAML files

        Raises:
            FileNotFoundError: If any required files are missing
            yaml.YAMLError: If any YAML files are malformed
        """
        pass

    @abstractmethod
    def create_temp_directory(self) -> ContextManager[str]:
        """
        Create a temporary directory and return a context manager.

        The directory will be automatically cleaned up when the context exits.

        Returns:
            Context manager that yields the path to the temporary directory

        Example:
            with file_handler.create_temp_directory() as temp_dir:
                # Use temp_dir for temporary file operations
                pass
            # Directory is automatically cleaned up
        """
        pass

    @abstractmethod
    def save_figure(self, fig: plt.Figure, path: Union[str, Path]) -> None:
        """
        Save a matplotlib figure to the specified path.

        Args:
            fig: Matplotlib figure to save
            path: Path where the figure should be saved

        Raises:
            PermissionError: If the file cannot be written due to permissions
            OSError: If there are other file system errors
        """
        pass
