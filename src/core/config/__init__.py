"""
Centralized configuration management system

This module provides a unified interface for loading, validating, and accessing
all configuration files used by the hybrid AI system.

Usage:
    from src.core.config import ConfigManager

    config = ConfigManager("config")
    model_config = config.models.get_model("llama-7b")
    threshold = config.thresholds.escalation_score
"""

from .loaders import ConfigLoader
from .manager import ConfigManager
from .schemas import LLMConfig, ModelConfig, SystemConfig, ThresholdsConfig
from .validators import ConfigValidator

__all__ = [
    "ConfigManager",
    "SystemConfig",
    "ModelConfig",
    "LLMConfig",
    "ThresholdsConfig",
    "ConfigLoader",
    "ConfigValidator",
]
