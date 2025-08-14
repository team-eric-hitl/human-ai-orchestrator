"""
Centralized error handling system

Provides comprehensive error handling with categorization, recovery strategies,
notifications, and integration with logging and monitoring systems.
"""

import inspect
import traceback
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

from .exceptions import (
    ConfigurationError,
    ContextError,
    ErrorSeverity,
    EscalationError,
    EvaluationError,
    HybridSystemError,
    LangSmithError,
    ModelError,
    ValidationError,
    WorkflowError,
)
from .logger import get_logger


class ErrorCategory(Enum):
    """Categories for error classification"""

    SYSTEM = "system"  # System-level errors
    MODEL = "model"  # Model-related errors
    USER_INPUT = "user_input"  # User input validation errors
    CONFIGURATION = "configuration"  # Configuration errors
    NETWORK = "network"  # Network/API errors
    WORKFLOW = "workflow"  # Workflow execution errors
    UNKNOWN = "unknown"  # Unclassified errors


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types"""

    RETRY = "retry"  # Retry the operation
    FALLBACK = "fallback"  # Use fallback mechanism
    ESCALATE = "escalate"  # Escalate to human
    IGNORE = "ignore"  # Log and continue
    FAIL_SAFE = "fail_safe"  # Safe degraded operation
    ABORT = "abort"  # Stop processing


class ErrorHandler:
    """
    Centralized error handler with recovery strategies and monitoring

    Provides structured error handling with automatic categorization,
    recovery strategies, and integration with logging and alerting systems.
    """

    def __init__(self, logger_name: str = "error_handler"):
        self.logger = get_logger(logger_name)
        self.error_count = 0
        self.error_history: list[dict[str, Any]] = []
        self.recovery_strategies: dict[type[Exception], RecoveryStrategy] = {}
        self.error_callbacks: dict[ErrorCategory, list[Callable]] = {}

        # Setup default recovery strategies
        self._setup_default_strategies()

        # Setup default error callbacks
        self._setup_default_callbacks()

    def _setup_default_strategies(self) -> None:
        """Setup default recovery strategies for common errors"""
        self.recovery_strategies.update(
            {
                ModelError: RecoveryStrategy.FALLBACK,
                ConfigurationError: RecoveryStrategy.ABORT,
                ValidationError: RecoveryStrategy.IGNORE,
                EvaluationError: RecoveryStrategy.FAIL_SAFE,
                EscalationError: RecoveryStrategy.RETRY,
                ContextError: RecoveryStrategy.FAIL_SAFE,
                LangSmithError: RecoveryStrategy.IGNORE,
                WorkflowError: RecoveryStrategy.ESCALATE,
                ConnectionError: RecoveryStrategy.RETRY,
                TimeoutError: RecoveryStrategy.RETRY,
                FileNotFoundError: RecoveryStrategy.FAIL_SAFE,
                KeyError: RecoveryStrategy.FAIL_SAFE,
                ValueError: RecoveryStrategy.IGNORE,
            }
        )

    def _setup_default_callbacks(self) -> None:
        """Setup default error callbacks"""
        self.error_callbacks = {
            ErrorCategory.SYSTEM: [self._system_error_callback],
            ErrorCategory.MODEL: [self._model_error_callback],
            ErrorCategory.CONFIGURATION: [self._config_error_callback],
            ErrorCategory.WORKFLOW: [self._workflow_error_callback],
        }

    def handle_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        recovery_strategy: RecoveryStrategy | None = None,
        user_message: str | None = None,
        notify: bool = True,
    ) -> dict[str, Any]:
        """
        Handle an error with comprehensive processing

        Args:
            error: The exception to handle
            context: Additional context information
            recovery_strategy: Override default recovery strategy
            user_message: Custom user-facing message
            notify: Whether to send notifications

        Returns:
            Dictionary containing error details and recovery information
        """
        self.error_count += 1

        # Categorize the error
        category = self._categorize_error(error)

        # Determine recovery strategy
        strategy = recovery_strategy or self._get_recovery_strategy(error)

        # Extract error details
        error_details = self._extract_error_details(error, context, category, strategy)

        # Log the error
        self._log_error(error_details)

        # Store in history
        self.error_history.append(error_details)

        # Execute callbacks
        if notify:
            self._execute_callbacks(category, error_details)

        # Determine user message
        final_user_message = self._get_user_message(error, user_message)
        error_details["user_message"] = final_user_message

        return error_details

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error for appropriate handling"""

        if isinstance(error, (ModelError,)):
            return ErrorCategory.MODEL
        elif isinstance(error, (ConfigurationError,)):
            return ErrorCategory.CONFIGURATION
        elif isinstance(error, (ValidationError,)):
            return ErrorCategory.USER_INPUT
        elif isinstance(error, (WorkflowError, EvaluationError, EscalationError)):
            return ErrorCategory.WORKFLOW
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK
        elif isinstance(error, (SystemError, MemoryError, OSError)):
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.UNKNOWN

    def _get_recovery_strategy(self, error: Exception) -> RecoveryStrategy:
        """Get recovery strategy for error type"""
        error_type = type(error)

        # Check exact type match first
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type]

        # Check inheritance hierarchy
        for exc_type, strategy in self.recovery_strategies.items():
            if isinstance(error, exc_type):
                return strategy

        # Default strategy based on error category
        category = self._categorize_error(error)
        default_strategies = {
            ErrorCategory.SYSTEM: RecoveryStrategy.ABORT,
            ErrorCategory.MODEL: RecoveryStrategy.FALLBACK,
            ErrorCategory.USER_INPUT: RecoveryStrategy.IGNORE,
            ErrorCategory.CONFIGURATION: RecoveryStrategy.ABORT,
            ErrorCategory.NETWORK: RecoveryStrategy.RETRY,
            ErrorCategory.WORKFLOW: RecoveryStrategy.ESCALATE,
            ErrorCategory.UNKNOWN: RecoveryStrategy.FAIL_SAFE,
        }

        return default_strategies.get(category, RecoveryStrategy.FAIL_SAFE)

    def _extract_error_details(
        self,
        error: Exception,
        context: dict[str, Any] | None,
        category: ErrorCategory,
        strategy: RecoveryStrategy,
    ) -> dict[str, Any]:
        """Extract comprehensive error details"""

        error_details = {
            "timestamp": datetime.now().isoformat(),
            "error_id": f"ERR_{self.error_count:06d}",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": category.value,
            "recovery_strategy": strategy.value,
            "context": context or {},
            "traceback": traceback.format_exc(),
            "caller_info": self._get_caller_info(),
            "severity": self._determine_severity(error, category),
            "recoverable": strategy != RecoveryStrategy.ABORT,
        }

        # Add structured error info for custom exceptions
        if isinstance(error, HybridSystemError):
            error_details.update(
                {
                    "error_code": error.error_code,
                    "severity": error.severity.value,
                    "recoverable": error.recoverable,
                    "structured_context": error.context,
                    "user_message": error.user_message,
                }
            )

        return error_details

    def _get_caller_info(self) -> dict[str, Any]:
        """Get information about where the error occurred"""
        frame = inspect.currentframe()

        # Walk up the stack to find the caller (skip internal frames)
        for _ in range(5):  # Max 5 frames up
            frame = frame.f_back
            if frame is None:
                break

            filename = frame.f_code.co_filename
            # Skip internal logging/error handling frames
            if not any(
                skip in filename for skip in ["logging", "error_handler", "traceback"]
            ):
                return {
                    "filename": filename,
                    "function": frame.f_code.co_name,
                    "line_number": frame.f_lineno,
                    "module": frame.f_globals.get("__name__", "unknown"),
                }

        return {
            "filename": "unknown",
            "function": "unknown",
            "line_number": 0,
            "module": "unknown",
        }

    def _determine_severity(self, error: Exception, category: ErrorCategory) -> str:
        """Determine error severity"""

        if isinstance(error, HybridSystemError):
            return error.severity.value

        # Severity mapping based on error type and category
        severity_map = {
            ErrorCategory.SYSTEM: ErrorSeverity.CRITICAL,
            ErrorCategory.CONFIGURATION: ErrorSeverity.HIGH,
            ErrorCategory.MODEL: ErrorSeverity.MEDIUM,
            ErrorCategory.WORKFLOW: ErrorSeverity.MEDIUM,
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.USER_INPUT: ErrorSeverity.LOW,
            ErrorCategory.UNKNOWN: ErrorSeverity.MEDIUM,
        }

        return severity_map.get(category, ErrorSeverity.MEDIUM).value

    def _log_error(self, error_details: dict[str, Any]) -> None:
        """Log error with appropriate level"""
        severity = error_details.get("severity", "medium")
        error_id = error_details.get("error_id")
        error_type = error_details.get("error_type")
        message = error_details.get("error_message")

        log_message = f"[{error_id}] {error_type}: {message}"

        # Log context
        context = error_details.get("context", {})
        if "structured_context" in error_details:
            context.update(error_details["structured_context"])

        extra = {
            "error_id": error_id,
            "error_category": error_details.get("category"),
            "recovery_strategy": error_details.get("recovery_strategy"),
            "severity": severity,
            **context,
        }

        # Choose log level based on severity
        if severity == "critical":
            self.logger.critical(log_message, extra=extra)
        elif severity == "high":
            self.logger.error(log_message, extra=extra)
        elif severity == "medium":
            self.logger.warning(log_message, extra=extra)
        else:
            self.logger.info(log_message, extra=extra)

    def _execute_callbacks(
        self, category: ErrorCategory, error_details: dict[str, Any]
    ) -> None:
        """Execute registered callbacks for error category"""
        callbacks = self.error_callbacks.get(category, [])

        for callback in callbacks:
            try:
                callback(error_details)
            except Exception as callback_error:
                # Don't let callback errors break error handling
                self.logger.error(f"Error callback failed: {callback_error}")

    def _get_user_message(self, error: Exception, custom_message: str | None) -> str:
        """Get user-friendly error message"""
        if custom_message:
            return custom_message

        if isinstance(error, HybridSystemError) and error.user_message:
            return error.user_message

        # Default messages based on error category
        category = self._categorize_error(error)
        default_messages = {
            ErrorCategory.SYSTEM: "A system error occurred. Please try again later.",
            ErrorCategory.MODEL: "I'm having trouble with the AI model. Please try again.",
            ErrorCategory.USER_INPUT: "Please check your input and try again.",
            ErrorCategory.CONFIGURATION: "There's a configuration issue. Please contact support.",
            ErrorCategory.NETWORK: "Network connection issue. Please try again.",
            ErrorCategory.WORKFLOW: "I encountered an issue processing your request. Please try again.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again.",
        }

        return default_messages.get(category, "An error occurred. Please try again.")

    # Default callback implementations
    def _system_error_callback(self, error_details: dict[str, Any]) -> None:
        """Handle system errors"""
        self.logger.critical(
            "System error detected",
            extra={
                "error_id": error_details.get("error_id"),
                "immediate_action_required": True,
            },
        )

    def _model_error_callback(self, error_details: dict[str, Any]) -> None:
        """Handle model errors"""
        self.logger.warning(
            "Model error detected",
            extra={
                "error_id": error_details.get("error_id"),
                "model_name": error_details.get("context", {}).get("model_name"),
                "fallback_required": True,
            },
        )

    def _config_error_callback(self, error_details: dict[str, Any]) -> None:
        """Handle configuration errors"""
        self.logger.error(
            "Configuration error detected",
            extra={
                "error_id": error_details.get("error_id"),
                "config_file": error_details.get("context", {}).get("config_file"),
                "restart_required": True,
            },
        )

    def _workflow_error_callback(self, error_details: dict[str, Any]) -> None:
        """Handle workflow errors"""
        self.logger.warning(
            "Workflow error detected",
            extra={
                "error_id": error_details.get("error_id"),
                "workflow_step": error_details.get("context", {}).get("workflow_step"),
                "escalation_recommended": True,
            },
        )

    def register_recovery_strategy(
        self, error_type: type[Exception], strategy: RecoveryStrategy
    ) -> None:
        """Register custom recovery strategy for error type"""
        self.recovery_strategies[error_type] = strategy

    def register_callback(self, category: ErrorCategory, callback: Callable) -> None:
        """Register callback for error category"""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics"""
        if not self.error_history:
            return {"total_errors": 0}

        categories = {}
        severities = {}
        strategies = {}

        for error in self.error_history:
            category = error.get("category", "unknown")
            severity = error.get("severity", "unknown")
            strategy = error.get("recovery_strategy", "unknown")

            categories[category] = categories.get(category, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
            strategies[strategy] = strategies.get(strategy, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "by_category": categories,
            "by_severity": severities,
            "by_recovery_strategy": strategies,
            "recent_errors": self.error_history[-10:]
            if len(self.error_history) > 10
            else self.error_history,
        }

    def clear_error_history(self) -> None:
        """Clear error history"""
        self.error_history.clear()
        self.error_count = 0


# Global error handler instance
_global_error_handler: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_error(error: Exception, **kwargs) -> dict[str, Any]:
    """Convenience function to handle errors using global handler"""
    return get_error_handler().handle_error(error, **kwargs)


# Decorator for automatic error handling
def with_error_handling(
    recovery_strategy: RecoveryStrategy | None = None,
    user_message: str | None = None,
    reraise: bool = True,
):
    """
    Decorator for automatic error handling

    Args:
        recovery_strategy: Recovery strategy to use
        user_message: Custom user message
        reraise: Whether to re-raise the exception after handling
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_details = handle_error(
                    e,
                    extra={"function": func.__name__, "args": str(args)[:100]},
                    recovery_strategy=recovery_strategy,
                    user_message=user_message,
                )

                if reraise:
                    raise

                return error_details

        return wrapper

    return decorator


# Type alias for convenience
AppErrorHandler = ErrorHandler
