"""
Base Interfaces Package

This package contains all abstract base classes and interfaces for the
application. These classes define the contracts that concrete implementations
must follow.

Structure:
- common/: Common interfaces used across the application
- model_testing/: Model testing interfaces (future)
- data_processing/: Data processing interfaces (future)
"""

from .common import (
    BaseAppFileHandler,
    BaseAppLogger,
    BaseConfigManager,
    BaseErrorHandler,
)

__all__ = [
    "BaseAppLogger",
    "BaseConfigManager",
    "BaseErrorHandler",
    "BaseAppFileHandler",
]
