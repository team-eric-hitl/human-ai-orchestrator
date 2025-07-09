"""
Core infrastructure for the hybrid system.

This package contains the foundational components:
- Configuration management (agent-centric)
- Context management
- Session tracking
- State schema definitions
"""

from .context_manager import ContextEntry, ContextProvider
from .state_schema import EscalationData, EvaluationResult, HybridSystemState

__all__ = [
    "HybridSystemState",
    "EvaluationResult",
    "EscalationData",
    "ContextProvider",
    "ContextEntry",
]
