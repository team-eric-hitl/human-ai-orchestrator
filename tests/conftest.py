"""
Pytest configuration and fixtures for the test suite.

This module provides common fixtures and configuration for all tests
in the project.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_logger():
    """Provide a mock logger for tests."""
    return Mock()


@pytest.fixture
def mock_config():
    """Provide a mock config manager for tests."""
    config = Mock()
    config.log_level = 20  # INFO level
    return config


@pytest.fixture
def mock_file_handler():
    """Provide a mock file handler for tests."""
    return Mock()


@pytest.fixture
def sample_yaml_data():
    """Provide sample YAML data for tests."""
    return {
        "app": {"name": "test_app", "version": "1.0.0"},
        "database": {"host": "localhost", "port": 5432},
        "logging": {"level": "INFO", "file": "app.log"},
    }


@pytest.fixture
def sample_json_data():
    """Provide sample JSON data for tests."""
    return {
        "data": {
            "items": [1, 2, 3, 4, 5],
            "metadata": {"created": "2023-01-01T00:00:00Z", "version": "1.0"},
        }
    }


@pytest.fixture
def sample_csv_data():
    """Provide sample CSV data for tests."""
    import pandas as pd

    return pd.DataFrame(
        {
            "name": ["John", "Jane", "Bob"],
            "age": [30, 25, 35],
            "city": ["New York", "Boston", "Chicago"],
        }
    )


@pytest.fixture
def sample_config_files(temp_dir):
    """Provide sample configuration files for tests."""
    import yaml

    # Create main config file
    main_config = {
        "app_name": "test_app",
        "version": "1.0.0",
        "database": {"host": "localhost", "port": 5432},
    }

    main_config_file = temp_dir / "app_config.yaml"
    with open(main_config_file, "w") as f:
        yaml.dump(main_config, f)

    # Create nested config file
    nested_dir = temp_dir / "models" / "model1"
    nested_dir.mkdir(parents=True)

    nested_config = {
        "model_name": "test_model",
        "parameters": {"learning_rate": 0.001, "batch_size": 32},
    }

    nested_config_file = nested_dir / "config.yaml"
    with open(nested_config_file, "w") as f:
        yaml.dump(nested_config, f)

    return {
        "temp_dir": temp_dir,
        "main_config_file": main_config_file,
        "nested_config_file": nested_config_file,
        "main_config": main_config,
        "nested_config": nested_config,
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # This fixture runs automatically for all tests
    # Add any global test setup here if needed
    pass


@pytest.fixture(autouse=True)
def teardown_test_environment():
    """Cleanup test environment after each test."""
    # This fixture runs automatically for all tests
    # Add any global test cleanup here if needed
    yield
    pass
