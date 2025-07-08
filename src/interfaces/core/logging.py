"""
Logging system interfaces

This module defines the contracts for logging providers that handle
structured logging, context awareness, and integration with monitoring systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    """Represents a single log entry in the system

    This data class encapsulates all information about a log entry,
    including metadata for tracking and analysis purposes.

    Attributes:
        timestamp: When this log entry was created
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: The log message content
        logger_name: Name of the logger that created this entry
        module: Module/component that generated the log
        context: Additional structured data about the log entry
        exception_info: Exception information if applicable
    """

    timestamp: datetime
    level: str
    message: str
    logger_name: str
    module: str
    context: dict[str, Any]
    exception_info: dict[str, Any] | None = None


class LoggerProvider(ABC):
    """Abstract base class for logging providers

    Logger providers are responsible for handling structured logging
    across the system with context awareness and multiple output formats.
    They enable centralized logging configuration and monitoring integration.

    Implementations should handle:
    - Multiple log levels with appropriate filtering
    - Context injection for structured logging
    - Integration with external monitoring systems
    - Performance optimization for high-volume logging
    - Configurable output formats and destinations
    """

    @abstractmethod
    def debug(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a debug message

        Args:
            message: The debug message to log
            context: Optional context data to include
        """
        pass

    @abstractmethod
    def info(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log an informational message

        Args:
            message: The informational message to log
            context: Optional context data to include
        """
        pass

    @abstractmethod
    def warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a warning message

        Args:
            message: The warning message to log
            context: Optional context data to include
        """
        pass

    @abstractmethod
    def error(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log an error message

        Args:
            message: The error message to log
            context: Optional context data to include
        """
        pass

    @abstractmethod
    def critical(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a critical message

        Args:
            message: The critical message to log
            context: Optional context data to include
        """
        pass

    @abstractmethod
    def exception(
        self, message: str, exception: Exception, context: dict[str, Any] | None = None
    ) -> None:
        """Log an exception with traceback

        Args:
            message: The exception message to log
            exception: The exception instance
            context: Optional context data to include
        """
        pass

    @abstractmethod
    def set_context(self, **context) -> None:
        """Set persistent context for all subsequent log messages

        Args:
            **context: Context key-value pairs to persist
        """
        pass

    @abstractmethod
    def clear_context(self) -> None:
        """Clear all persistent context"""
        pass

    @abstractmethod
    def remove_context(self, *keys: str) -> None:
        """Remove specific context keys

        Args:
            *keys: Context keys to remove
        """
        pass


class StructuredLoggerProvider(LoggerProvider):
    """Extended logger provider with structured logging capabilities

    This interface extends the basic logger provider to support
    domain-specific logging methods and structured data collection.
    """

    @abstractmethod
    def model_call(
        self,
        model_name: str,
        operation: str,
        duration: float | None = None,
        token_count: int | None = None,
        **context,
    ) -> None:
        """Log a model call with specific context

        Args:
            model_name: Name of the model being called
            operation: Operation being performed
            duration: Time taken for the operation
            token_count: Number of tokens processed
            **context: Additional context data
        """
        pass

    @abstractmethod
    def user_interaction(
        self, user_id: str, query: str, response_type: str, **context
    ) -> None:
        """Log a user interaction

        Args:
            user_id: Identifier for the user
            query: User's query or input
            response_type: Type of response generated
            **context: Additional context data
        """
        pass

    @abstractmethod
    def escalation(
        self, user_id: str, reason: str, priority: str = "medium", **context
    ) -> None:
        """Log an escalation event

        Args:
            user_id: Identifier for the user
            reason: Reason for escalation
            priority: Priority level of the escalation
            **context: Additional context data
        """
        pass

    @abstractmethod
    def performance_metric(self, operation: str, duration: float, **context) -> None:
        """Log a performance metric

        Args:
            operation: Operation being measured
            duration: Time taken for the operation
            **context: Additional context data
        """
        pass

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics from the logging system

        Returns:
            Dictionary containing collected metrics data
        """
        pass

    @abstractmethod
    def reset_metrics(self) -> None:
        """Reset collected metrics data"""
        pass


class LoggingConfigProvider(ABC):
    """Abstract base class for logging configuration providers

    Logging configuration providers handle the setup and configuration
    of logging systems with support for multiple environments and
    output formats.
    """

    @abstractmethod
    def get_logging_config(self) -> dict[str, Any]:
        """Get logging configuration

        Returns:
            Dictionary containing logging configuration including:
            - Log levels and handlers
            - Output formats and destinations
            - Context and filtering settings
            - Performance and buffering options
        """
        pass

    @abstractmethod
    def get_handler_config(self, handler_name: str) -> dict[str, Any]:
        """Get configuration for a specific log handler

        Args:
            handler_name: Name of the handler to get config for

        Returns:
            Dictionary containing handler-specific configuration
        """
        pass

    @abstractmethod
    def configure_for_environment(self, environment: str) -> dict[str, Any]:
        """Get environment-specific logging configuration

        Args:
            environment: Environment name (development, production, testing)

        Returns:
            Dictionary containing environment-optimized logging configuration
        """
        pass
