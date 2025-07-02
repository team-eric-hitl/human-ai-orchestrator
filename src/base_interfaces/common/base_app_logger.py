"""
Base Application Logger Interface

This module defines the abstract base class for application logging operations.
It provides a standardized interface for structured logging, performance monitoring,
and context management in the application.
"""

import contextlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

from .base_config_manager import BaseConfigManager


class BaseAppLogger(ABC):
    """
    Abstract base class defining logging interface.

    This class provides a standardized interface for application logging including
    structured logging, performance monitoring, and context management. Concrete
    implementations should handle the actual logging operations.
    """

    @abstractmethod
    def __init__(self, config: BaseConfigManager) -> None:
        """
        Initialize logger with configuration.

        Args:
            config: Configuration manager instance providing logging settings
        """
        pass

    @abstractmethod
    def setup(self, log_file: str) -> logging.Logger:
        """
        Setup logging configuration with file and console handlers.

        Args:
            log_file: Path to the log file where logs will be written

        Returns:
            Configured logger instance ready for use

        Raises:
            PermissionError: If the log file cannot be created due to permissions
            OSError: If there are other file system errors
        """
        pass

    @abstractmethod
    def structured_log(self, level: int, message: str, **kwargs: Any) -> None:
        """
        Log a structured message with additional context.

        Args:
            level: Logging level (e.g., logging.INFO, logging.ERROR)
            message: Main log message
            **kwargs: Additional context key-value pairs to include in the log
        """
        pass

    @abstractmethod
    def log_performance(self, func: Callable) -> Callable:
        """
        Decorator for logging function performance.

        This decorator wraps a function to automatically log its execution time,
        success/failure status, and any errors that occur.

        Args:
            func: Function to decorate with performance logging

        Returns:
            Wrapped function with performance logging capabilities
        """
        pass

    @abstractmethod
    def log_context(self, **kwargs: Any) -> contextlib.AbstractContextManager:
        """
        Context manager for adding context to logs.

        This context manager allows adding contextual information to all log
        messages within its scope. The context is automatically removed when
        the context exits.

        Args:
            **kwargs: Context key-value pairs to add to all logs within the context

        Returns:
            Context manager that adds the specified context to logs

        Example:
            with logger.log_context(user_id=123, session_id="abc"):
                logger.info("Processing request")  # Includes user_id and session_id
        """
        pass
