"""
Main application logger

Provides the central AppLogger class and logging configuration for the
hybrid AI system with support for multiple outputs, contexts, and integrations.
"""

import logging
import logging.config
import os
import sys
import threading
from functools import lru_cache
from typing import Any

from .formatters import (
    ColoredConsoleFormatter,
    CompactFormatter,
    JSONFormatter,
    StructuredFormatter,
)
from .handlers import (
    ContextEnhancedStreamHandler,
    DebugFileHandler,
    LangSmithHandler,
    MetricsHandler,
    RotatingFileHandler,
    TimedRotatingFileHandler,
)

# Global logger registry
_loggers: dict[str, "AppLogger"] = {}
_logger_lock = threading.Lock()


class AppLogger:
    """
    Enhanced application logger with context awareness and multiple outputs

    Provides structured logging with automatic context injection, multiple
    output formats, and integration with monitoring systems.
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or self._get_default_config()
        self._logger = logging.getLogger(name)
        self._context: dict[str, Any] = {}
        self._handlers_configured = False

        # Configure logger if not already done
        if not self._handlers_configured:
            self._configure_logger()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default logging configuration"""
        return {
            "level": "INFO",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "console": {
                "enabled": True,
                "level": "INFO",
                "use_colors": True,
                "use_icons": True,
            },
            "file": {
                "enabled": True,
                "level": "DEBUG",
                "path": "logs/app.log",
                "max_bytes": 10485760,  # 10MB
                "backup_count": 5,
                "format": "structured",
            },
            "json_file": {
                "enabled": False,
                "level": "INFO",
                "path": "logs/app.json",
                "rotation": "time",  # 'size' or 'time'
            },
            "debug_file": {"enabled": True, "level": "DEBUG", "path": "logs/debug.log"},
            "langsmith": {"enabled": True, "level": "WARNING", "buffer_size": 100},
            "metrics": {"enabled": True, "level": "INFO"},
        }

    def _configure_logger(self) -> None:
        """Configure logger with handlers and formatters"""
        if self._handlers_configured:
            return

        # Set base logger level
        level_name = self.config.get("level", "INFO")
        self._logger.setLevel(getattr(logging, level_name.upper()))

        # Clear existing handlers
        self._logger.handlers.clear()

        # Configure console handler
        if self.config.get("console", {}).get("enabled", True):
            self._add_console_handler()

        # Configure file handler
        if self.config.get("file", {}).get("enabled", True):
            self._add_file_handler()

        # Configure JSON file handler
        if self.config.get("json_file", {}).get("enabled", False):
            self._add_json_file_handler()

        # Configure debug file handler
        if self.config.get("debug_file", {}).get("enabled", True):
            self._add_debug_file_handler()

        # Configure LangSmith handler
        if self.config.get("langsmith", {}).get("enabled", True):
            self._add_langsmith_handler()

        # Configure metrics handler
        if self.config.get("metrics", {}).get("enabled", True):
            self._add_metrics_handler()

        self._handlers_configured = True

    def _add_console_handler(self) -> None:
        """Add console handler with colored output"""
        console_config = self.config.get("console", {})

        handler = ContextEnhancedStreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, console_config.get("level", "INFO").upper()))

        # Use colored formatter for development
        if self.config.get("environment") == "development":
            formatter = ColoredConsoleFormatter(
                use_colors=console_config.get("use_colors", True),
                use_icons=console_config.get("use_icons", True),
            )
        else:
            formatter = CompactFormatter()

        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _add_file_handler(self) -> None:
        """Add rotating file handler"""
        file_config = self.config.get("file", {})

        handler = RotatingFileHandler(
            filename=file_config.get("path", "logs/app.log"),
            maxBytes=file_config.get("max_bytes", 10485760),
            backupCount=file_config.get("backup_count", 5),
        )
        handler.setLevel(getattr(logging, file_config.get("level", "DEBUG").upper()))

        # Choose formatter based on config
        format_type = file_config.get("format", "structured")
        if format_type == "json":
            formatter = JSONFormatter()
        else:
            formatter = StructuredFormatter()

        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _add_json_file_handler(self) -> None:
        """Add JSON file handler for structured logging"""
        json_config = self.config.get("json_file", {})

        if json_config.get("rotation") == "time":
            handler = TimedRotatingFileHandler(
                filename=json_config.get("path", "logs/app.json"),
                when="midnight",
                backupCount=30,
            )
        else:
            handler = RotatingFileHandler(
                filename=json_config.get("path", "logs/app.json"),
                maxBytes=10485760,
                backupCount=5,
            )

        handler.setLevel(getattr(logging, json_config.get("level", "INFO").upper()))
        handler.setFormatter(JSONFormatter())
        self._logger.addHandler(handler)

    def _add_debug_file_handler(self) -> None:
        """Add debug file handler with enhanced context"""
        debug_config = self.config.get("debug_file", {})

        handler = DebugFileHandler(filename=debug_config.get("path", "logs/debug.log"))
        handler.setLevel(getattr(logging, debug_config.get("level", "DEBUG").upper()))
        handler.setFormatter(StructuredFormatter())
        self._logger.addHandler(handler)

    def _add_langsmith_handler(self) -> None:
        """Add LangSmith integration handler"""
        langsmith_config = self.config.get("langsmith", {})

        handler = LangSmithHandler(
            level=getattr(logging, langsmith_config.get("level", "WARNING").upper()),
            buffer_size=langsmith_config.get("buffer_size", 100),
        )
        self._logger.addHandler(handler)

    def _add_metrics_handler(self) -> None:
        """Add metrics collection handler"""
        metrics_config = self.config.get("metrics", {})

        handler = MetricsHandler(
            level=getattr(logging, metrics_config.get("level", "INFO").upper())
        )
        self._logger.addHandler(handler)

        # Store reference for metrics access
        self._metrics_handler = handler

    def set_context(self, **kwargs) -> None:
        """Set persistent context for all log messages"""
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all persistent context"""
        self._context.clear()

    def remove_context(self, *keys) -> None:
        """Remove specific context keys"""
        for key in keys:
            self._context.pop(key, None)

    def _log_with_context(self, level: int, msg: str, *args, **kwargs) -> None:
        """Log message with automatic context injection"""
        # Merge persistent context with message-specific context
        extra = kwargs.get("extra", {})
        extra.update(self._context)
        kwargs["extra"] = extra

        self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message"""
        self._log_with_context(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message"""
        self._log_with_context(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message"""
        self._log_with_context(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message"""
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log exception with traceback"""
        kwargs.setdefault("exc_info", True)
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)

    def model_call(
        self,
        model_name: str,
        operation: str,
        duration: float | None = None,
        token_count: int | None = None,
        **kwargs,
    ) -> None:
        """Log model call with specific context"""
        extra = {
            "model_name": model_name,
            "operation": operation,
            "duration": duration,
            "token_count": token_count,
        }
        extra.update(kwargs)

        self.info(f"Model call: {model_name} - {operation}", extra=extra)

    def escalation(
        self, user_id: str, reason: str, priority: str = "medium", **kwargs
    ) -> None:
        """Log escalation event"""
        extra = {
            "user_id": user_id,
            "escalation": True,
            "escalation_reason": reason,
            "priority": priority,
        }
        extra.update(kwargs)

        self.warning(f"Escalation triggered: {reason}", extra=extra)

    def user_interaction(
        self, user_id: str, query: str, response_type: str, **kwargs
    ) -> None:
        """Log user interaction"""
        extra = {
            "user_id": user_id,
            "query_preview": query[:100] + "..." if len(query) > 100 else query,
            "response_type": response_type,
        }
        extra.update(kwargs)

        self.info(f"User interaction: {response_type}", extra=extra)

    def performance_metric(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metric"""
        extra = {"operation": operation, "duration": duration, "metric": True}
        extra.update(kwargs)

        self.info(f"Performance: {operation} took {duration:.3f}s", extra=extra)

    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics"""
        if hasattr(self, "_metrics_handler"):
            return self._metrics_handler.get_metrics()
        return {}

    def reset_metrics(self) -> None:
        """Reset collected metrics"""
        if hasattr(self, "_metrics_handler"):
            self._metrics_handler.reset_metrics()


@lru_cache(maxsize=128)
def get_logger(name: str, config: dict[str, Any] | None = None) -> AppLogger:
    """
    Get or create an AppLogger instance

    Uses caching to ensure single instance per name.
    """
    with _logger_lock:
        if name not in _loggers:
            _loggers[name] = AppLogger(name, config)
        return _loggers[name]


def configure_logging(config: dict[str, Any]) -> None:
    """
    Configure global logging settings

    This function sets up logging for the entire application.
    """
    # Clear existing loggers
    with _logger_lock:
        _loggers.clear()

    # Set root logger level
    root_level = config.get("root_level", "WARNING")
    logging.getLogger().setLevel(getattr(logging, root_level.upper()))

    # Disable propagation to avoid duplicate messages
    logging.getLogger("src").propagate = False


def setup_development_logging() -> None:
    """Setup logging optimized for development"""
    config = {
        "level": "DEBUG",
        "environment": "development",
        "console": {
            "enabled": True,
            "level": "DEBUG",
            "use_colors": True,
            "use_icons": True,
        },
        "file": {"enabled": True, "level": "DEBUG", "path": "logs/dev.log"},
        "langsmith": {
            "enabled": False  # Disable in development
        },
    }
    configure_logging(config)


def setup_production_logging() -> None:
    """Setup logging optimized for production"""
    config = {
        "level": "INFO",
        "environment": "production",
        "console": {
            "enabled": True,
            "level": "WARNING",
            "use_colors": False,
            "use_icons": False,
        },
        "file": {
            "enabled": True,
            "level": "INFO",
            "path": "/var/log/hybrid-ai/app.log",
            "format": "structured",
        },
        "json_file": {
            "enabled": True,
            "level": "INFO",
            "path": "/var/log/hybrid-ai/app.json",
            "rotation": "time",
        },
        "langsmith": {"enabled": True, "level": "ERROR"},
    }
    configure_logging(config)


def setup_testing_logging() -> None:
    """Setup minimal logging for testing"""
    config = {
        "level": "CRITICAL",
        "environment": "testing",
        "console": {"enabled": False},
        "file": {"enabled": False},
        "langsmith": {"enabled": False},
        "metrics": {"enabled": False},
    }
    configure_logging(config)
