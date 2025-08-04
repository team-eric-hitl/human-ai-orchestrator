"""
Core interfaces for the hybrid system

This module contains the fundamental interfaces that define the contracts
for core system components like context management, configuration, and
session tracking.
"""

from .config import ConfigProvider
from .context import ContextEntry, ContextProvider
from .logging import (
    LogEntry,
    LoggerProvider,
    LoggingConfigProvider,
    StructuredLoggerProvider,
)
from .session import SessionMetrics, SessionTrackerInterface
from .state_schema import EscalationData, EvaluationResult, HybridSystemState
from .trace import (
    TraceCollectorInterface,
    InteractionTrace,
    AgentInteraction,
    SystemDecision,
    WorkflowStage,
    PerformanceMetrics,
    OutputFormat
)

__all__ = [
    "ContextProvider",
    "ContextEntry",
    "ConfigProvider",
    "LogEntry",
    "LoggerProvider",
    "LoggingConfigProvider",
    "StructuredLoggerProvider",
    "SessionTrackerInterface",
    "SessionMetrics",
    "TraceCollectorInterface",
    "InteractionTrace",
    "AgentInteraction",
    "SystemDecision",
    "WorkflowStage",
    "PerformanceMetrics",
    "OutputFormat",
    "HybridSystemState",
    "EscalationData",
    "EvaluationResult",
]
