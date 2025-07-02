"""
Unit tests for ErrorHandler classes.

This module contains comprehensive tests for the ErrorHandler base class
and its concrete implementations including ConfigurationError and
FileOperationError.
"""

import logging
from unittest.mock import Mock

import pytest

from src.common.error_handling.error_handler import (
    ConfigurationError,
    ErrorHandler,
    FileOperationError,
)


class TestErrorHandler:
    """Test cases for the base ErrorHandler class."""

    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization with basic parameters."""
        message = "Test error message"
        error_handler = ErrorHandler(message=message, app_logger=None)

        assert error_handler.message == message
        assert error_handler.app_logger is None
        assert error_handler.log_level == logging.ERROR
        assert error_handler.exit_code == 1
        assert error_handler.additional_info == {}

    def test_error_handler_with_logger(self):
        """Test ErrorHandler initialization with logger."""
        message = "Test error message"
        mock_logger = Mock()
        error_handler = ErrorHandler(
            message=message, app_logger=mock_logger, log_level=logging.WARNING
        )

        assert error_handler.message == message
        assert error_handler.app_logger == mock_logger
        assert error_handler.log_level == logging.WARNING
        assert error_handler.exit_code == 1

    def test_error_handler_with_additional_info(self):
        """Test ErrorHandler initialization with additional context."""
        message = "Test error message"
        additional_info = {"file_path": "/test/path", "operation": "read"}
        error_handler = ErrorHandler(
            message=message, app_logger=None, **additional_info
        )

        assert error_handler.message == message
        assert error_handler.additional_info == additional_info

    def test_error_handler_log_with_logger(self):
        """Test logging functionality when logger is available."""
        message = "Test error message"
        mock_logger = Mock()
        error_handler = ErrorHandler(
            message=message,
            app_logger=mock_logger,
            log_level=logging.ERROR,
            file_path="/test/path",
            operation="read",
        )

        error_handler.log()

        mock_logger.structured_log.assert_called_once_with(
            logging.ERROR,
            message,
            error_type="ErrorHandler",
            file_path="/test/path",
            operation="read",
        )

    def test_error_handler_log_without_logger(self):
        """Test logging functionality when no logger is available."""
        message = "Test error message"
        error_handler = ErrorHandler(
            message=message, app_logger=None, file_path="/test/path"
        )

        # Should not raise an exception when no logger is available
        error_handler.log()

        # Verify no logging occurred
        assert error_handler.app_logger is None

    def test_error_handler_str_representation(self):
        """Test string representation of ErrorHandler."""
        message = "Test error message"
        error_handler = ErrorHandler(message=message, app_logger=None)

        assert str(error_handler) == message

    def test_error_handler_exception_behavior(self):
        """Test that ErrorHandler behaves as a proper exception."""
        message = "Test error message"
        error_handler = ErrorHandler(message=message, app_logger=None)

        # Should be able to raise it
        with pytest.raises(ErrorHandler) as exc_info:
            raise error_handler

        assert str(exc_info.value) == message


class TestConfigurationError:
    """Test cases for the ConfigurationError class."""

    def test_configuration_error_initialization(self):
        """Test ConfigurationError initialization."""
        message = "Configuration error occurred"
        error = ConfigurationError(message=message, app_logger=None)

        assert error.message == message
        assert error.exit_code == 2
        assert isinstance(error, ErrorHandler)

    def test_configuration_error_with_logger(self):
        """Test ConfigurationError with logger."""
        message = "Configuration error occurred"
        mock_logger = Mock()
        error = ConfigurationError(
            message=message, app_logger=mock_logger, log_level=logging.CRITICAL
        )

        error.log()

        mock_logger.structured_log.assert_called_once_with(
            logging.CRITICAL, message, error_type="ConfigurationError"
        )

    def test_configuration_error_exception_behavior(self):
        """Test that ConfigurationError behaves as a proper exception."""
        message = "Configuration error occurred"
        error = ConfigurationError(message=message, app_logger=None)

        with pytest.raises(ConfigurationError) as exc_info:
            raise error

        assert str(exc_info.value) == message
        assert exc_info.value.exit_code == 2


class TestFileOperationError:
    """Test cases for the FileOperationError class."""

    def test_file_operation_error_initialization(self):
        """Test FileOperationError initialization."""
        message = "File operation failed"
        error = FileOperationError(message=message, app_logger=None)

        assert error.message == message
        assert error.exit_code == 10
        assert isinstance(error, ErrorHandler)

    def test_file_operation_error_with_additional_context(self):
        """Test FileOperationError with file operation context."""
        message = "File operation failed"
        mock_logger = Mock()
        error = FileOperationError(
            message=message,
            app_logger=mock_logger,
            file_path="/test/file.txt",
            operation="write",
            original_error="Permission denied",
        )

        error.log()

        mock_logger.structured_log.assert_called_once_with(
            logging.ERROR,
            message,
            error_type="FileOperationError",
            file_path="/test/file.txt",
            operation="write",
            original_error="Permission denied",
        )

    def test_file_operation_error_exception_behavior(self):
        """Test that FileOperationError behaves as a proper exception."""
        message = "File operation failed"
        error = FileOperationError(message=message, app_logger=None)

        with pytest.raises(FileOperationError) as exc_info:
            raise error

        assert str(exc_info.value) == message
        assert exc_info.value.exit_code == 10


class TestErrorHandlerIntegration:
    """Integration tests for ErrorHandler classes."""

    def test_error_handler_inheritance_chain(self):
        """Test that error handlers properly inherit from base classes."""
        # Test ConfigurationError inheritance
        config_error = ConfigurationError("Config error", app_logger=None)
        assert isinstance(config_error, ErrorHandler)
        assert isinstance(config_error, Exception)

        # Test FileOperationError inheritance
        file_error = FileOperationError("File error", app_logger=None)
        assert isinstance(file_error, ErrorHandler)
        assert isinstance(file_error, Exception)

    def test_error_handler_logging_integration(self):
        """Test error handler logging integration with structured logging."""
        mock_logger = Mock()

        # Test different error types with logging
        errors = [
            ConfigurationError("Config error", app_logger=mock_logger),
            FileOperationError("File error", app_logger=mock_logger),
        ]

        for error in errors:
            error.log()

        # Verify each error was logged
        assert mock_logger.structured_log.call_count == 2

    def test_error_handler_context_preservation(self):
        """Test that error handlers preserve context information."""
        context = {
            "user_id": 123,
            "session_id": "abc123",
            "timestamp": "2023-01-01T00:00:00Z",
        }

        error = ErrorHandler(message="Test error", app_logger=None, **context)

        assert error.additional_info == context
        assert error.additional_info["user_id"] == 123
        assert error.additional_info["session_id"] == "abc123"
