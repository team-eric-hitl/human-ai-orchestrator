"""
Node interfaces for the hybrid system

This module contains interfaces for processing nodes that handle
different aspects of the AI-human hybrid workflow.
"""

from .automation import AutomationAgentInterface, AutomationResult
from .base import NodeInterface, NodeResult

__all__ = [
    "NodeInterface", 
    "NodeResult", 
    "AutomationAgentInterface", 
    "AutomationResult"
]
