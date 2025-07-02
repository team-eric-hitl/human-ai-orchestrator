"""
Base Error Handler Interface

This module defines the abstract base class for error handling operations in the 
application. It provides a standardized interface for creating, logging, and 
managing application errors with structured information.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from .base_app_logger import BaseAppLogger


class BaseErrorHandler(ABC, Exception):
    """
    Abstract base class for error handling operations.

    This class defines the interface for error handling operations, combining
    the functionality of an Exception with structured logging capabilities.
    Concrete implementations should handle specific error types and logging
    formats.
    """

    def __init__(
        self,
        message: str,
        app_logger: Optional[BaseAppLogger],
        log_level: int = logging.ERROR,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the error handler with error details and logging configuration.

        Args:
            message: Error message describing what went wrong
            app_logger: Application logger instance for logging the error (can be None)
            log_level: Logging level for the error (default: logging.ERROR)
            **kwargs: Additional error context information
        """
        self.app_logger = app_logger
        self.message = message
        self.log_level = log_level
        self.additional_info = kwargs
        self.log()
        # Properly call Exception's init
        Exception.__init__(self, message)

    @abstractmethod
    def log(self) -> None:
        """
        Log the error with the specified level and additional information.

        This method should be implemented by concrete classes to provide
        specific logging behavior for different error types. If no logger
        is available, the error should still be raised but not logged.

        Raises:
            RuntimeError: If logging fails
        """
        pass
