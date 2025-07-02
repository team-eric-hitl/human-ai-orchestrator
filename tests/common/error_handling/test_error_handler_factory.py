"""
Unit tests for ErrorHandlerFactory.

This module contains comprehensive tests for the ErrorHandlerFactory class
which is responsible for creating error handler instances with proper
logging configuration.
"""

import logging
from unittest.mock import Mock

import pytest

from src.common.error_handling.error_handler import (
    ConfigurationError,
    FileOperationError,
)
from src.common.error_handling.error_handler_factory import ErrorHandlerFactory


class TestErrorHandlerFactory:
    """Test cases for the ErrorHandlerFactory class."""

    def test_factory_initialization_without_logger(self):
        """Test factory initialization without logger."""
        factory = ErrorHandlerFactory()

        assert factory.app_logger is None
        assert "configuration" in factory._error_classes
        assert "file_operation" in factory._error_classes

    def test_factory_initialization_with_logger(self):
        """Test factory initialization with logger."""
        mock_logger = Mock()
        factory = ErrorHandlerFactory(app_logger=mock_logger)

        assert factory.app_logger == mock_logger
        assert "configuration" in factory._error_classes
        assert "file_operation" in factory._error_classes

    def test_create_configuration_error(self):
        """Test creating a ConfigurationError through the factory."""
        factory = ErrorHandlerFactory()
        message = "Configuration error occurred"

        error = factory.create_error_handler("configuration", message)

        assert isinstance(error, ConfigurationError)
        assert error.message == message
        assert error.exit_code == 2

    def test_create_file_operation_error(self):
        """Test creating a FileOperationError through the factory."""
        factory = ErrorHandlerFactory()
        message = "File operation failed"

        error = factory.create_error_handler("file_operation", message)

        assert isinstance(error, FileOperationError)
        assert error.message == message
        assert error.exit_code == 10

    def test_create_error_with_logger(self):
        """Test creating an error with logger injection."""
        mock_logger = Mock()
        factory = ErrorHandlerFactory(app_logger=mock_logger)
        message = "Test error"

        error = factory.create_error_handler("configuration", message)

        assert isinstance(error, ConfigurationError)
        assert error.app_logger == mock_logger
        assert error.message == message

    def test_create_error_with_custom_log_level(self):
        """Test creating an error with custom log level."""
        mock_logger = Mock()
        factory = ErrorHandlerFactory(app_logger=mock_logger)
        message = "Test error"
        log_level = logging.CRITICAL

        error = factory.create_error_handler(
            "configuration", message, log_level=log_level
        )

        assert isinstance(error, ConfigurationError)
        assert error.log_level == log_level
        assert error.app_logger == mock_logger

    def test_create_error_with_additional_context(self):
        """Test creating an error with additional context."""
        factory = ErrorHandlerFactory()
        message = "Test error"
        context = {"file_path": "/test/path", "operation": "read"}

        error = factory.create_error_handler("file_operation", message, **context)

        assert isinstance(error, FileOperationError)
        assert error.additional_info == context
        assert error.additional_info["file_path"] == "/test/path"

    def test_create_error_with_invalid_type(self):
        """Test creating an error with invalid error type."""
        factory = ErrorHandlerFactory()
        message = "Test error"

        with pytest.raises(ValueError) as exc_info:
            factory.create_error_handler("invalid_type", message)

        assert "Unknown error type" in str(exc_info.value)
        assert "configuration" in str(exc_info.value)
        assert "file_operation" in str(exc_info.value)

    def test_set_logger(self):
        """Test setting logger after factory initialization."""
        factory = ErrorHandlerFactory()
        mock_logger = Mock()

        factory.set_logger(mock_logger)

        assert factory.app_logger == mock_logger

    def test_set_logger_overwrites_existing(self):
        """Test that set_logger overwrites existing logger."""
        initial_logger = Mock()
        factory = ErrorHandlerFactory(app_logger=initial_logger)

        new_logger = Mock()
        factory.set_logger(new_logger)

        assert factory.app_logger == new_logger
        assert factory.app_logger != initial_logger

    def test_error_logging_integration(self):
        """Test that errors created by factory can log properly."""
        mock_logger = Mock()
        factory = ErrorHandlerFactory(app_logger=mock_logger)
        message = "Test error"

        error = factory.create_error_handler(
            "configuration", message, file_path="/test/config.yaml"
        )

        error.log()

        mock_logger.structured_log.assert_called_once_with(
            logging.ERROR,
            message,
            error_type="ConfigurationError",
            file_path="/test/config.yaml",
        )

    def test_factory_without_logger_creates_errors_without_logger(self):
        """Test that factory without logger creates errors without logger."""
        factory = ErrorHandlerFactory()
        message = "Test error"

        error = factory.create_error_handler("configuration", message)

        assert error.app_logger is None
        # Should not raise exception when logging
        error.log()

    def test_factory_error_types_completeness(self):
        """Test that factory supports all expected error types."""
        factory = ErrorHandlerFactory()

        # Test all supported error types
        error_types = ["configuration", "file_operation"]

        for error_type in error_types:
            error = factory.create_error_handler(error_type, "Test message")
            assert error is not None
            assert hasattr(error, "message")
            assert hasattr(error, "exit_code")

    def test_factory_error_creation_with_complex_context(self):
        """Test creating errors with complex context information."""
        factory = ErrorHandlerFactory()
        message = "Complex error"
        context = {
            "user_id": 123,
            "session_id": "abc123",
            "file_path": "/test/file.txt",
            "operation": "write",
            "timestamp": "2023-01-01T00:00:00Z",
            "nested_data": {"key": "value"},
        }

        error = factory.create_error_handler("file_operation", message, **context)

        assert isinstance(error, FileOperationError)
        assert error.additional_info == context
        assert error.additional_info["user_id"] == 123
        assert error.additional_info["nested_data"]["key"] == "value"


class TestErrorHandlerFactoryIntegration:
    """Integration tests for ErrorHandlerFactory."""

    def test_factory_error_chain(self):
        """Test complete error creation and handling chain."""
        mock_logger = Mock()
        factory = ErrorHandlerFactory(app_logger=mock_logger)

        # Create different types of errors
        config_error = factory.create_error_handler(
            "configuration", "Config error", config_file="/test/config.yaml"
        )

        file_error = factory.create_error_handler(
            "file_operation", "File error", file_path="/test/file.txt", operation="read"
        )

        # Log both errors
        config_error.log()
        file_error.log()

        # Verify both were logged
        assert mock_logger.structured_log.call_count == 2

        # Verify different error types
        assert isinstance(config_error, ConfigurationError)
        assert isinstance(file_error, FileOperationError)

    def test_factory_logger_update_affects_new_errors(self):
        """Test that updating factory logger affects newly created errors."""
        factory = ErrorHandlerFactory()

        # Create error without logger
        error1 = factory.create_error_handler("configuration", "Error 1")
        assert error1.app_logger is None

        # Update factory logger
        mock_logger = Mock()
        factory.set_logger(mock_logger)

        # Create new error with logger
        error2 = factory.create_error_handler("configuration", "Error 2")
        assert error2.app_logger == mock_logger

        # Log the second error
        error2.log()
        mock_logger.structured_log.assert_called_once()

    def test_factory_error_types_validation(self):
        """Test validation of error types in factory."""
        factory = ErrorHandlerFactory()

        # Test valid error types
        valid_types = ["configuration", "file_operation"]
        for error_type in valid_types:
            error = factory.create_error_handler(error_type, "Test")
            assert error is not None

        # Test invalid error types
        invalid_types = ["", "invalid", "unknown", "error"]
        for error_type in invalid_types:
            with pytest.raises(ValueError):
                factory.create_error_handler(error_type, "Test")
