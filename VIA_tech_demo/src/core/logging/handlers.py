"""
Custom log handlers for the hybrid AI system

Provides specialized log handlers for different destinations including
files, console, LangSmith integration, and external monitoring systems.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .formatters import LangSmithFormatter


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Enhanced rotating file handler with automatic directory creation
    """

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        maxBytes: int = 10485760,
        backupCount: int = 5,
        encoding: str = "utf-8",
        **kwargs,
    ):
        # Ensure log directory exists
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(filename, mode, maxBytes, backupCount, encoding, **kwargs)


class TimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    Enhanced timed rotating file handler with automatic directory creation
    """

    def __init__(
        self,
        filename: str,
        when: str = "midnight",
        interval: int = 1,
        backupCount: int = 30,
        encoding: str = "utf-8",
        **kwargs,
    ):
        # Ensure log directory exists
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(filename, when, interval, backupCount, encoding, **kwargs)


class LangSmithHandler(logging.Handler):
    """
    Custom handler for sending logs to LangSmith

    Integrates with LangSmith tracing system for centralized monitoring.
    """

    def __init__(self, level: int = logging.NOTSET, buffer_size: int = 100):
        super().__init__(level)
        self.buffer_size = buffer_size
        self.buffer: list[dict[str, Any]] = []
        self.formatter = LangSmithFormatter()

        # Check if LangSmith is available
        self.langsmith_available = self._check_langsmith_availability()

    def _check_langsmith_availability(self) -> bool:
        """Check if LangSmith client is available and configured"""
        try:
            import os

            from langsmith import Client

            api_key = os.getenv("LANGSMITH_API_KEY")
            if not api_key:
                return False

            # Try to create client (don't make actual API call here)
            self.langsmith_client = Client(api_key=api_key)
            return True

        except Exception:
            return False

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record to LangSmith"""
        if not self.langsmith_available:
            return

        try:
            # Format record for LangSmith
            langsmith_data = self.formatter.format(record)

            # Add to buffer
            self.buffer.append(langsmith_data)

            # Flush buffer if it's full or if it's an error/critical message
            if len(self.buffer) >= self.buffer_size or record.levelno >= logging.ERROR:
                self.flush()

        except Exception:
            # Silently fail - logging shouldn't break the application
            pass

    def flush(self) -> None:
        """Flush buffered logs to LangSmith"""
        if not self.buffer or not self.langsmith_available:
            return

        try:
            # Send logs to LangSmith (implement based on LangSmith API)
            # For now, just clear the buffer
            self.buffer.clear()

        except Exception:
            # Silently fail
            pass


class MetricsHandler(logging.Handler):
    """
    Handler for collecting application metrics from logs

    Extracts metrics like response times, error rates, model performance.
    """

    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)
        self.metrics: dict[str, Any] = {
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "model_calls": 0,
            "escalations": 0,
            "response_times": [],
            "errors_by_type": {},
            "models_used": {},
        }

    def emit(self, record: logging.LogRecord) -> None:
        """Extract metrics from log record"""
        try:
            # Count by log level
            if record.levelno >= logging.ERROR:
                self.metrics["error_count"] += 1
            elif record.levelno >= logging.WARNING:
                self.metrics["warning_count"] += 1
            elif record.levelno >= logging.INFO:
                self.metrics["info_count"] += 1

            # Extract specific metrics from extra fields
            extra_fields = {
                k: v
                for k, v in record.__dict__.items()
                if k
                not in logging.LogRecord(
                    None, None, None, None, None, None, None
                ).__dict__
            }

            # Model usage metrics
            if "model_name" in extra_fields:
                model_name = extra_fields["model_name"]
                self.metrics["model_calls"] += 1
                self.metrics["models_used"][model_name] = (
                    self.metrics["models_used"].get(model_name, 0) + 1
                )

            # Response time metrics
            if "duration" in extra_fields:
                duration = extra_fields["duration"]
                if isinstance(duration, (int, float)):
                    self.metrics["response_times"].append(duration)

            # Escalation metrics
            if "escalation" in extra_fields and extra_fields["escalation"]:
                self.metrics["escalations"] += 1

            # Error type metrics
            if record.exc_info and record.exc_info[0]:
                error_type = record.exc_info[0].__name__
                self.metrics["errors_by_type"][error_type] = (
                    self.metrics["errors_by_type"].get(error_type, 0) + 1
                )

        except Exception:
            # Don't let metrics collection break logging
            pass

    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics"""
        metrics = self.metrics.copy()

        # Calculate derived metrics
        if self.metrics["response_times"]:
            response_times = self.metrics["response_times"]
            metrics["avg_response_time"] = sum(response_times) / len(response_times)
            metrics["max_response_time"] = max(response_times)
            metrics["min_response_time"] = min(response_times)

        total_logs = (
            self.metrics["error_count"]
            + self.metrics["warning_count"]
            + self.metrics["info_count"]
        )
        if total_logs > 0:
            metrics["error_rate"] = self.metrics["error_count"] / total_logs
            metrics["warning_rate"] = self.metrics["warning_count"] / total_logs

        return metrics

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = {
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "model_calls": 0,
            "escalations": 0,
            "response_times": [],
            "errors_by_type": {},
            "models_used": {},
        }


class ContextEnhancedStreamHandler(logging.StreamHandler):
    """
    Enhanced stream handler that includes context information
    """

    def __init__(self, stream=None, include_context: bool = True):
        super().__init__(stream)
        self.include_context = include_context

    def emit(self, record: logging.LogRecord) -> None:
        """Emit with enhanced context"""
        if self.include_context:
            # Add system context to record
            record.hostname = os.getenv("HOSTNAME", "localhost")
            record.pid = os.getpid()

        super().emit(record)


class AsyncHandler(logging.Handler):
    """
    Asynchronous logging handler for high-performance scenarios

    Buffers log records and processes them asynchronously to avoid
    blocking the main application threads.
    """

    def __init__(self, target_handler: logging.Handler, buffer_size: int = 1000):
        super().__init__()
        self.target_handler = target_handler
        self.buffer_size = buffer_size
        self.buffer: list[logging.LogRecord] = []
        self._lock = logging._lock  # Use logging module's lock

    def emit(self, record: logging.LogRecord) -> None:
        """Add record to buffer"""
        with self._lock:
            self.buffer.append(record)

            # Flush if buffer is full or if it's a critical message
            if (
                len(self.buffer) >= self.buffer_size
                or record.levelno >= logging.CRITICAL
            ):
                self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush all buffered records to target handler"""
        if not self.buffer:
            return

        # Process all buffered records
        for record in self.buffer:
            try:
                self.target_handler.emit(record)
            except Exception:
                # Don't let handler errors stop the flush
                pass

        # Clear buffer
        self.buffer.clear()

    def flush(self) -> None:
        """Force flush of buffer"""
        with self._lock:
            self._flush_buffer()

        # Also flush target handler
        if hasattr(self.target_handler, "flush"):
            self.target_handler.flush()

    def close(self) -> None:
        """Close handler and flush remaining records"""
        self.flush()
        if hasattr(self.target_handler, "close"):
            self.target_handler.close()
        super().close()


class DebugFileHandler(logging.FileHandler):
    """
    Special handler for debug information that includes additional context
    """

    def __init__(self, filename: str, mode: str = "a", encoding: str = "utf-8"):
        # Ensure debug log directory exists
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(filename, mode, encoding)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit with debug-specific enhancements"""
        # Add debug context
        record.debug_timestamp = datetime.now().isoformat()
        record.thread_name = getattr(record.thread, "name", record.thread)

        # Add call stack info for debug level
        if record.levelno == logging.DEBUG:
            import traceback

            record.call_stack = "".join(traceback.format_stack()[:-1])

        super().emit(record)
