"""
Application Logger Implementation

This module provides a concrete implementation of the BaseAppLogger interface
for application logging operations. It includes structured logging, performance
monitoring, and context management capabilities.
"""

import contextlib
import functools
import logging
import time
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from src.base_interfaces.common import BaseAppLogger, BaseConfigManager

# Context variable to store logging context
_log_context: ContextVar[Dict[str, Any]] = ContextVar(
    "log_context",
    default={},
)


@dataclass
class LogContext:
    """
    Class to store logging context data.

    This dataclass provides a structured way to store contextual information
    that should be included in log messages.
    """

    app_version: str
    environment: str
    additional_context: Optional[Dict[str, Any]] = None


class AppLogger(BaseAppLogger):
    """
    Concrete implementation of BaseAppLogger.

    This class provides a comprehensive logging solution with structured
    logging, performance monitoring, and context management capabilities.
    """

    def __init__(self, config: BaseConfigManager) -> None:
        """
        Initialize the application logger with configuration.

        Args:
            config: Configuration manager instance providing logging settings
        """
        self.logger: Optional[logging.Logger] = None
        self.config = config

    def setup(self, log_file: str) -> logging.Logger:
        """
        Setup logging configuration with file and console handlers.

        Args:
            log_file: Path to log file where logs will be written

        Returns:
            Configured logger instance ready for use

        Raises:
            PermissionError: If the log file cannot be created due to
                permissions
            OSError: If there are other file system errors
        """
        logger = logging.getLogger(__name__)

        # Use config log level if available, otherwise default to INFO
        log_level = (
            getattr(self.config, "log_level", logging.INFO)
            if self.config
            else logging.INFO
        )
        logger.setLevel(log_level)

        # Create formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")

        # File handler
        log_file_handler = logging.FileHandler(log_file)
        log_file_handler.setFormatter(file_formatter)
        logger.addHandler(log_file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        self.logger = logger
        return logger

    def structured_log(self, level: int, message: str, **kwargs: Any) -> None:
        """
        Log a structured message with additional context.

        Args:
            level: Logging level (e.g., logging.INFO, logging.ERROR)
            message: Main log message
            **kwargs: Additional context key-value pairs to include in the log
        """
        if self.logger is None:
            raise RuntimeError("Logger not initialized. Call setup() first.")

        # Get current context
        context = _log_context.get()

        # Combine context with kwargs
        log_data = {**context, **kwargs}

        # Format message with context as key=value pairs
        if log_data:
            context_str = ", ".join([f"{k}={v}" for k, v in log_data.items()])
            structured_message = f"{message} | Context: {context_str}"
        else:
            structured_message = message

        self.logger.log(level, structured_message)

    def log_performance(self, func: Callable) -> Callable:
        """
        Decorator for logging function performance.

        This decorator wraps a function to automatically log its execution
        time, success/failure status, and any errors that occur.

        Args:
            func: Function to decorate with performance logging

        Returns:
            Wrapped function with performance logging capabilities
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                self.structured_log(
                    logging.INFO,
                    f"Function {func.__name__} completed",
                    duration_seconds=duration,
                    status="success",
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                self.structured_log(
                    logging.ERROR,
                    f"Function {func.__name__} failed",
                    duration_seconds=duration,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        return wrapper

    @contextlib.contextmanager
    def log_context(self, **kwargs: Any):
        """
        Context manager for adding context to logs.

        This context manager allows adding contextual information to all log
        messages within its scope. The context is automatically removed when
        the context exits.

        Args:
            **kwargs: Context key-value pairs to add to all logs within the
                     context

        Returns:
            Context manager that adds the specified context to logs

        Example:
            with logger.log_context(user_id=123, session_id="abc"):
                logger.info("Processing request")  # Includes user_id and
                                                   # session_id
        """
        token = None
        try:
            # Get existing context and update with new values
            current_context = _log_context.get()
            new_context = {**current_context, **kwargs}

            # Set new context
            token = _log_context.set(new_context)
            yield
        finally:
            # Restore previous context
            if token is not None:
                _log_context.reset(token)
