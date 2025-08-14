"""
Agent-centric configuration management system

This module provides a unified interface for loading, validating, and accessing
all configuration files used by the hybrid AI system using the agent-centric approach.

Usage:
    from src.core.config import ConfigManager

    config = ConfigManager("config")
    agent_config = config.get_agent_config("answer_agent")
    model = agent_config.get_preferred_model()
"""

from .agent_config_manager import (
    AgentConfig,
    AgentConfigManager,
    ConfigLoadError,
    SystemConfig,
)

# Use AgentConfigManager as the primary ConfigManager
ConfigManager = AgentConfigManager

__all__ = [
    "ConfigManager",
    "AgentConfigManager",
    "AgentConfig",
    "SystemConfig",
    "ConfigLoadError",
]
