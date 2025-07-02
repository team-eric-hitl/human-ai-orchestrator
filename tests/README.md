# Unit Tests for Common Modules

This directory contains comprehensive unit tests for all common modules in the project using pytest.

## Test Structure

```
tests/
├── conftest.py                          # Pytest configuration and fixtures
├── common/
│   ├── error_handling/
│   │   ├── test_error_handler.py        # Tests for ErrorHandler classes
│   │   └── test_error_handler_factory.py # Tests for ErrorHandlerFactory
│   ├── app_logging/
│   │   └── test_app_logger.py           # Tests for AppLogger
│   ├── config_management/
│   │   └── test_config_manager.py       # Tests for ConfigManager
│   ├── app_file_handling/
│   │   └── test_app_file_handler.py     # Tests for LocalAppFileHandler
│   └── test_common_di_container.py      # Tests for CommonDIContainer
└── README.md                            # This file
```

## Test Coverage

The test suite covers the following modules:

### Error Handling (`src/common/error_handling/`)
- **ErrorHandler**: Base error handling class with logging capabilities
- **ConfigurationError**: Specific error for configuration issues
- **FileOperationError**: Specific error for file operation issues
- **ErrorHandlerFactory**: Factory for creating error handlers with proper logging

### Application Logging (`src/common/app_logging/`)
- **AppLogger**: Structured logging with performance monitoring and context management
- Logging setup and configuration
- Structured logging with context
- Performance monitoring decorators
- Context managers for log context

### Configuration Management (`src/common/config_management/`)
- **ConfigManager**: Centralized configuration management with nested file support
- Configuration file loading and parsing
- Nested configuration handling
- Configuration merging and namespace conversion
- Error handling integration

### File Handling (`src/common/app_file_handling/`)
- **LocalAppFileHandler**: Local file system operations
- YAML, JSON, and CSV file operations
- Directory management and path utilities
- Temporary directory management
- Matplotlib figure saving

### Dependency Injection (`src/common/`)
- **CommonDIContainer**: Dependency injection container for common components
- Provider configuration and singleton behavior
- Dependency resolution
- Error handling wiring

## Running Tests

### Prerequisites

Make sure you have the development dependencies installed:

```bash
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=src/common --cov-report=html --cov-report=term
```

### Run Specific Test Module

```bash
# Run error handling tests
pytest tests/common/error_handling/

# Run logging tests
pytest tests/common/app_logging/

# Run config management tests
pytest tests/common/config_management/

# Run file handling tests
pytest tests/common/app_file_handling/

# Run DI container tests
pytest tests/common/test_common_di_container.py
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests and Stop on First Failure

```bash
pytest -x
```

## Test Features

### Fixtures

The test suite includes several reusable fixtures in `conftest.py`:

- `temp_dir`: Provides a temporary directory for file operations
- `mock_logger`: Mock logger for testing
- `mock_config`: Mock configuration manager
- `mock_file_handler`: Mock file handler
- `sample_yaml_data`: Sample YAML data for testing
- `sample_json_data`: Sample JSON data for testing
- `sample_csv_data`: Sample CSV data for testing
- `sample_config_files`: Sample configuration files for testing

### Test Categories

Each test module includes:

1. **Unit Tests**: Test individual methods and classes in isolation
2. **Integration Tests**: Test how components work together
3. **Error Handling Tests**: Test error conditions and edge cases
4. **Mock Tests**: Test interactions with dependencies using mocks

### Test Patterns

The tests follow these patterns:

- **Arrange-Act-Assert**: Clear test structure
- **Mocking**: Use of unittest.mock for dependencies
- **Temporary Files**: Safe file operations using tempfile
- **Context Managers**: Proper resource cleanup
- **Comprehensive Coverage**: Test both success and failure scenarios

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention: `test_*.py`
2. Use descriptive test method names: `test_<method>_<scenario>`
3. Include both unit and integration tests
4. Use the provided fixtures when appropriate
5. Add proper docstrings for test methods
6. Test both success and error scenarios
7. Use mocks for external dependencies

## Test Quality

The test suite aims for:

- **High Coverage**: Comprehensive testing of all public methods
- **Fast Execution**: Tests should run quickly
- **Isolation**: Tests should not depend on each other
- **Readability**: Clear and maintainable test code
- **Reliability**: Tests should be deterministic and repeatable 