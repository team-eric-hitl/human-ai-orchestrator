"""
Core infrastructure for the hybrid system.

This package contains the foundational components:
- Configuration management (agent-centric)
- Context management
- Session tracking
- State schema definitions
"""

from .context_manager import SQLiteContextProvider
from .database_config import DatabaseConfig
from ..interfaces.core.context import ContextEntry, ContextProvider
from ..interfaces.core.state_schema import EscalationData, EvaluationResult, HybridSystemState

__all__ = [
    "HybridSystemState",
    "EvaluationResult",
    "EscalationData",
    "ContextProvider",
    "ContextEntry",
    "SQLiteContextProvider",
    "DatabaseConfig",
]
