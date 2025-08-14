"""
Experimentation interfaces for systematic testing of AI agents

This module provides interfaces for experimenting with different configurations,
prompts, and parameters to optimize agent performance.
"""

from .base import ExperimentationInterface
from .models import (
    ExperimentResult,
    ExperimentResults,
    OptimizationTarget,
    PromptVariant,
    ThresholdExperiment,
)

__all__ = [
    "ExperimentationInterface",
    "ExperimentResult",
    "ExperimentResults",
    "PromptVariant",
    "ThresholdExperiment",
    "OptimizationTarget",
]
