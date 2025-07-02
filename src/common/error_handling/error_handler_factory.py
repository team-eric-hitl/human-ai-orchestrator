"""
Error Handler Factory

This module provides a factory for creating error handler instances with proper
logging configuration. It supports optional logger injection to avoid circular
dependencies in lower-level components.
"""

from typing import Optional, Type

from src.base_interfaces.common import BaseAppLogger
from src.common.error_handling.error_handler import (
    ConfigurationError,
    FileOperationError,
)


class ErrorHandlerFactory:
    """
    Factory for creating error handler instances with proper logging
    configuration.
    """

    def __init__(self, app_logger: Optional[BaseAppLogger] = None):
        """
        Initialize the error handler factory.

        Args:
            app_logger (Optional[BaseAppLogger]): Logger instance to be
                injected into error handlers. Can be None for use in
                lower-level components.
        """
        self.app_logger = app_logger
        self._error_classes = {
            # Core errors
            "configuration": ConfigurationError,
            "file_operation": FileOperationError,
        }

    def create_error_handler(
        self, error_type: str, message: str, log_level: Optional[int] = None, **kwargs
    ) -> Type[Exception]:
        """
        Create an error handler instance of the specified type.

        Args:
            error_type: Type of error to create
            message: Error message
            log_level: Optional logging level (only used if logger is
                available)
            **kwargs: Additional error context

        Returns:
            Error handler instance

        Raises:
            ValueError: If error_type is not recognized
        """
        if error_type not in self._error_classes:
            valid_types = ", ".join(sorted(self._error_classes.keys()))
            raise ValueError(
                f"Unknown error type: {error_type}. "
                f"Valid types are: {valid_types}"
            )

        error_class = self._error_classes[error_type]

        # Create error handler with injected logger if available
        if self.app_logger is not None:
            if log_level is not None:
                return error_class(
                    message=message,
                    app_logger=self.app_logger,
                    log_level=log_level,
                    **kwargs,
                )
            else:
                return error_class(
                    message=message, app_logger=self.app_logger, **kwargs
                )
        else:
            # Create error without logging for lower-level components
            return error_class(
                message=message,
                app_logger=None,  # Will be handled gracefully by error classes
                **kwargs,
            )

    def set_logger(self, app_logger: BaseAppLogger) -> None:
        """
        Set or update the logger instance.

        Args:
            app_logger: Logger instance to use for error handling
        """
        self.app_logger = app_logger
