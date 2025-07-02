"""
Error Handler Implementation

This module provides concrete implementations of the BaseErrorHandler interface
for various types of application errors. It includes specific error classes for
different error scenarios with appropriate exit codes and logging capabilities.
"""

import logging
from typing import Any, Optional

from src.base_interfaces.common import BaseAppLogger, BaseErrorHandler


class ErrorHandler(BaseErrorHandler):
    """
    Base concrete implementation of BaseErrorHandler.

    This class provides the basic error handling functionality with logging
    capabilities and exit code management.
    """

    exit_code: int = 1  # Default exit code

    def __init__(
        self,
        message: str,
        app_logger: Optional[BaseAppLogger],
        log_level: int = logging.ERROR,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the error handler with error details and logging
        configuration.

        Args:
            message: Error message describing what went wrong
            app_logger: Application logger instance for logging the error
                (can be None)
            log_level: Logging level for the error (default: logging.ERROR)
            **kwargs: Additional error context information
        """
        # Initialize without calling log() to avoid double logging
        self.app_logger = app_logger
        self.message = message
        self.log_level = log_level
        self.additional_info = kwargs
        # Properly call Exception's init
        Exception.__init__(self, message)

    def log(self) -> None:
        """
        Log the error with the specified level and additional information.

        Implementation of abstract log method that uses structured logging
        to record error details with context. If no logger is available,
        the error is still raised but not logged.
        """
        if self.app_logger is not None:
            self.app_logger.structured_log(
                self.log_level,
                self.message,
                error_type=self.__class__.__name__,
                **self.additional_info,
            )


class ConfigurationError(ErrorHandler):
    """
    Raised when there's an error in the configuration.

    This error is used when configuration files are missing, malformed, or
    contain invalid settings.
    """

    exit_code: int = 2


class FileOperationError(ErrorHandler):
    """
    Raised when there's an error in file operations.

    This error is used for file handling operations such as reading, writing,
    creating directories, or other file system operations.
    """

    exit_code: int = 10

    def __init__(
        self,
        message,
        app_logger=None,
        log_level=logging.ERROR,
        **kwargs,
    ):
        super().__init__(
            message=message,
            app_logger=app_logger,
            log_level=log_level,
            **kwargs,
        )
