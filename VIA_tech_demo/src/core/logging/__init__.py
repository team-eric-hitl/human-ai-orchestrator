"""
Centralized logging and error handling system

This module provides a unified interface for logging and error handling
across the hybrid AI system with structured logging, context awareness,
and integration with external monitoring systems.

Usage:
    from src.core.logging import get_logger, AppErrorHandler

    logger = get_logger(__name__)
    logger.info("Processing started", extra={"user_id": "123"})

    error_handler = AppErrorHandler()
    error_handler.handle_error(exception, extra={"operation": "model_load"})
"""

from .error_handler import AppErrorHandler, ErrorCategory
from .exceptions import (
    ConfigurationError,
    EscalationError,
    EvaluationError,
    HybridSystemError,
    ModelError,
    ModelInferenceError,
    ValidationError,
)
from .logger import AppLogger, configure_logging, get_logger, setup_development_logging

__all__ = [
    "AppLogger",
    "get_logger",
    "configure_logging",
    "setup_development_logging",
    "AppErrorHandler",
    "ErrorCategory",
    "HybridSystemError",
    "ModelError",
    "ModelInferenceError",
    "ConfigurationError",
    "ValidationError",
    "EvaluationError",
    "EscalationError",
]
