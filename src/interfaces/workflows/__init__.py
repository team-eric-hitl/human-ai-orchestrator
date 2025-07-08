"""
Workflow interfaces for the hybrid system

This module contains interfaces for orchestrating workflows that
coordinate multiple nodes and manage the overall system flow.
"""

from .base import WorkflowInterface, WorkflowResult

__all__ = ["WorkflowInterface", "WorkflowResult"]
