"""
Log formatters for different output formats

Provides structured logging formatters for console output, JSON logging,
and integration with external monitoring systems.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any


class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored console formatter for development

    Provides colored, human-readable log output with context information.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }

    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Emoji prefixes for better visibility
    ICONS = {
        "DEBUG": "🔍",
        "INFO": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨",
    }

    def __init__(self, use_colors: bool = True, use_icons: bool = True):
        super().__init__()
        self.use_colors = use_colors and self._supports_color()
        self.use_icons = use_icons

    def _supports_color(self) -> bool:
        """Check if terminal supports colors"""
        return (
            hasattr(sys.stderr, "isatty")
            and sys.stderr.isatty()
            and hasattr(sys.stdout, "isatty")
            and sys.stdout.isatty()
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and structure"""

        # Get color and icon for log level
        level_name = record.levelname
        color = self.COLORS.get(level_name, "") if self.use_colors else ""
        reset = self.RESET if self.use_colors else ""
        icon = self.ICONS.get(level_name, "") if self.use_icons else ""

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]

        # Format module name (shorter)
        module = record.name.split(".")[-1] if "." in record.name else record.name

        # Base message
        base_msg = f"{color}{icon} {timestamp} [{level_name:8}] {module:15} | {record.getMessage()}{reset}"

        # Add context if available
        context_parts = []

        # Add extra fields from record
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in logging.LogRecord(None, None, None, None, None, None, None).__dict__
            and not k.startswith("_")
        }

        for key, value in extra_fields.items():
            if key in ["user_id", "session_id", "model_name", "query_id", "operation"]:
                context_parts.append(f"{key}={value}")

        if context_parts:
            context_str = " ".join(context_parts)
            base_msg += f" | {context_str}"

        # Add exception info if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"

        # Add stack info if present
        if hasattr(record, "stack_info") and record.stack_info:
            base_msg += f"\n{record.stack_info}"

        return base_msg


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for production logging

    Provides structured JSON output suitable for log aggregation systems.
    """

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""

        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        # Add extra fields
        if self.include_extra:
            extra_fields = {
                k: v
                for k, v in record.__dict__.items()
                if k
                not in logging.LogRecord(
                    None, None, None, None, None, None, None
                ).__dict__
                and not k.startswith("_")
            }

            if extra_fields:
                log_data["context"] = extra_fields

        # Add exception information
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add stack info if present
        if hasattr(record, "stack_info") and record.stack_info:
            log_data["stack_info"] = record.stack_info

        return json.dumps(log_data, ensure_ascii=False, default=str)


class LangSmithFormatter(logging.Formatter):
    """
    Formatter for LangSmith integration

    Formats logs for sending to LangSmith tracing system.
    """

    def format(self, record: logging.LogRecord) -> dict[str, Any]:
        """Format log record for LangSmith"""

        # Base data for LangSmith
        langsmith_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "source": f"{record.module}.{record.funcName}",
            "metadata": {},
        }

        # Add context metadata
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in logging.LogRecord(None, None, None, None, None, None, None).__dict__
            and not k.startswith("_")
        }

        # Filter relevant fields for LangSmith
        relevant_fields = [
            "user_id",
            "session_id",
            "model_name",
            "query_id",
            "operation",
            "duration",
            "token_count",
            "cost",
        ]

        for field in relevant_fields:
            if field in extra_fields:
                langsmith_data["metadata"][field] = extra_fields[field]

        # Add error information
        if record.exc_info and record.exc_info[1]:
            langsmith_data["error"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        return langsmith_data


class StructuredFormatter(logging.Formatter):
    """
    Structured formatter for file logging

    Provides a balance between human readability and machine parseability.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structure"""

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        # Base format
        base = (
            f"[{timestamp}] {record.levelname:8} {record.name} | {record.getMessage()}"
        )

        # Add context in key=value format
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in logging.LogRecord(None, None, None, None, None, None, None).__dict__
            and not k.startswith("_")
        }

        if extra_fields:
            context_pairs = [f"{k}={v}" for k, v in extra_fields.items()]
            base += f" | {' '.join(context_pairs)}"

        # Add exception info
        if record.exc_info:
            base += f"\nException: {self.formatException(record.exc_info)}"

        return base


class CompactFormatter(logging.Formatter):
    """
    Compact formatter for minimal logging

    Provides very concise log output for performance-critical scenarios.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record compactly"""
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        level_char = record.levelname[0]  # D, I, W, E, C
        module = record.name.split(".")[-1][:8]  # First 8 chars of module name

        return f"{timestamp} {level_char} {module:8} | {record.getMessage()}"
