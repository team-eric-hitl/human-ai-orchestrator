"""
Tests for the agent-centric configuration management system.
Tests AgentConfigManager and agent configuration loading.
"""

import json
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.config import ConfigManager
from src.core.config.agent_config_manager import AgentConfig, SystemConfig
from src.core.logging.exceptions import ConfigurationError


class TestAgentConfigManager:
    """Test suite for AgentConfigManager functionality"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory with agent-centric config structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create directory structure
            (config_dir / "agents" / "answer_agent").mkdir(parents=True)
            (config_dir / "agents" / "evaluator_agent").mkdir(parents=True)
            (config_dir / "shared").mkdir(parents=True)
            (config_dir / "environments").mkdir(parents=True)

            # Create shared configs
            shared_models = {
                "models": {
                    "llama-7b": {
                        "path": "models/llama-7b.gguf",
                        "type": "llama",
                        "context_length": 2048,
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "description": "Llama 7B model"
                    },
                    "gpt-4": {
                        "type": "openai",
                        "model_name": "gpt-4",
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "description": "OpenAI GPT-4"
                    }
                }
            }
            
            shared_system = {
                "system": {
                    "name": "Test System",
                    "version": "1.0.0"
                },
                "thresholds": {
                    "escalation_score": 6.0,
                    "confidence_threshold": 0.7
                }
            }

            # Create agent configs
            answer_agent_config = {
                "agent": {
                    "name": "answer_agent",
                    "description": "Test answer agent",
                    "type": "llm_agent"
                },
                "settings": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
            
            answer_agent_models = {
                "preferred": "llama-7b",
                "fallback": ["gpt-4"]
            }
            
            answer_agent_prompts = {
                "system_prompt": "You are a helpful assistant.",
                "templates": {
                    "greeting": "Hello! How can I help you?"
                }
            }

            evaluator_agent_config = {
                "agent": {
                    "name": "evaluator_agent",
                    "description": "Test evaluator agent",
                    "type": "evaluation_agent"
                },
                "settings": {
                    "temperature": 0.3,
                    "max_tokens": 1500
                }
            }
            
            evaluator_agent_models = {
                "preferred": "gpt-4",
                "fallback": ["llama-7b"]
            }

            # Write config files
            with open(config_dir / "shared" / "models.yaml", "w") as f:
                yaml.dump(shared_models, f)
            with open(config_dir / "shared" / "system.yaml", "w") as f:
                yaml.dump(shared_system, f)
            
            with open(config_dir / "agents" / "answer_agent" / "config.yaml", "w") as f:
                yaml.dump(answer_agent_config, f)
            with open(config_dir / "agents" / "answer_agent" / "prompts.yaml", "w") as f:
                yaml.dump(answer_agent_prompts, f)
            with open(config_dir / "agents" / "answer_agent" / "models.yaml", "w") as f:
                yaml.dump(answer_agent_models, f)
            
            with open(config_dir / "agents" / "evaluator_agent" / "config.yaml", "w") as f:
                yaml.dump(evaluator_agent_config, f)
            with open(config_dir / "agents" / "evaluator_agent" / "models.yaml", "w") as f:
                yaml.dump(evaluator_agent_models, f)

            yield config_dir

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create ConfigManager with test configuration"""
        return ConfigManager(str(temp_config_dir))

    def test_initialization_success(self, config_manager):
        """Test successful ConfigManager initialization"""
        assert config_manager is not None
        assert config_manager.config_dir is not None
        
        # Check that agents are loaded
        available_agents = config_manager.get_available_agents()
        assert len(available_agents) == 2
        assert "answer_agent" in available_agents
        assert "evaluator_agent" in available_agents

    def test_initialization_missing_directory(self):
        """Test initialization with missing config directory"""
        # Should create ConfigManager but with no agents loaded
        config_manager = ConfigManager("/nonexistent/path")
        assert config_manager is not None
        assert len(config_manager.get_available_agents()) == 0

    def test_agent_config_loading(self, config_manager):
        """Test agent configuration loading"""
        # Test answer agent
        answer_config = config_manager.get_agent_config("answer_agent")
        assert answer_config is not None
        assert answer_config.name == "answer_agent"
        assert answer_config.description == "Test answer agent"
        assert answer_config.type == "llm_agent"
        assert answer_config.get_preferred_model() == "llama-7b"
        assert answer_config.get_fallback_models() == ["gpt-4"]
        
        # Test evaluator agent
        evaluator_config = config_manager.get_agent_config("evaluator_agent")
        assert evaluator_config is not None
        assert evaluator_config.name == "evaluator_agent"
        assert evaluator_config.get_preferred_model() == "gpt-4"

    def test_agent_config_methods(self, config_manager):
        """Test agent configuration methods"""
        answer_config = config_manager.get_agent_config("answer_agent")
        
        # Test get_setting
        assert answer_config.get_setting("temperature") == 0.7
        assert answer_config.get_setting("max_tokens") == 2000
        assert answer_config.get_setting("nonexistent", "default") == "default"
        
        # Test get_prompt
        assert answer_config.get_prompt("system") == "You are a helpful assistant."
        assert answer_config.get_prompt("greeting") == "Hello! How can I help you?"

    def test_system_config_loading(self, config_manager):
        """Test system configuration loading"""
        system_config = config_manager.get_system_config()
        assert system_config is not None
        assert system_config.name == "Test System"
        assert system_config.version == "1.0.0"
        assert system_config.thresholds["escalation_score"] == 6.0

    def test_models_config_loading(self, config_manager):
        """Test models configuration loading"""
        models_config = config_manager.get_models_config()
        assert models_config is not None
        assert "models" in models_config
        assert "llama-7b" in models_config["models"]
        assert "gpt-4" in models_config["models"]

    def test_primary_model_for_agent(self, config_manager):
        """Test primary model selection for agents"""
        answer_model = config_manager.get_primary_model_for_agent("answer_agent")
        assert answer_model == "llama-7b"
        
        evaluator_model = config_manager.get_primary_model_for_agent("evaluator_agent")
        assert evaluator_model == "gpt-4"
        
        # Test fallback for non-existent agent
        fallback_model = config_manager.get_primary_model_for_agent("nonexistent")
        assert fallback_model == "llama-7b"  # Should use global default

    def test_threshold_access(self, config_manager):
        """Test threshold value access"""
        escalation_score = config_manager.get_threshold("escalation_score")
        assert escalation_score == 6.0
        
        confidence_threshold = config_manager.get_threshold("confidence_threshold")
        assert confidence_threshold == 0.7
        
        # Test default value
        nonexistent = config_manager.get_threshold("nonexistent", 5.0)
        assert nonexistent == 5.0

    def test_configuration_summary(self, config_manager):
        """Test configuration summary generation"""
        summary = config_manager.get_summary()
        
        assert "config_directory" in summary
        assert "environment" in summary
        assert "system_name" in summary
        assert "agents_loaded" in summary
        assert "agent_names" in summary
        assert "models_configured" in summary
        
        assert summary["agents_loaded"] == 2
        assert "answer_agent" in summary["agent_names"]
        assert "evaluator_agent" in summary["agent_names"]
        assert summary["system_name"] == "Test System"

    def test_environment_override(self, temp_config_dir):
        """Test environment-specific configuration override"""
        # Create development environment config
        dev_config = {
            "environment": "development",
            "thresholds": {
                "escalation_score": 5.0  # Override from 6.0
            }
        }
        
        with open(temp_config_dir / "environments" / "development.yaml", "w") as f:
            yaml.dump(dev_config, f)
        
        # Test with development environment
        config_manager = ConfigManager(str(temp_config_dir), environment="development")
        
        # Should use overridden value
        escalation_score = config_manager.get_threshold("escalation_score")
        assert escalation_score == 5.0

    def test_missing_agent_config(self, config_manager):
        """Test handling of missing agent configuration"""
        nonexistent_config = config_manager.get_agent_config("nonexistent_agent")
        assert nonexistent_config is None

    def test_reload_configuration(self, config_manager, temp_config_dir):
        """Test configuration reloading"""
        # Initial state
        initial_summary = config_manager.get_summary()
        assert initial_summary["agents_loaded"] == 2
        
        # Add a new agent
        new_agent_config = {
            "agent": {
                "name": "new_agent",
                "description": "New test agent",
                "type": "test_agent"
            }
        }
        
        new_agent_models = {
            "preferred": "llama-7b"
        }
        
        new_agent_dir = temp_config_dir / "agents" / "new_agent"
        new_agent_dir.mkdir()
        
        with open(new_agent_dir / "config.yaml", "w") as f:
            yaml.dump(new_agent_config, f)
        with open(new_agent_dir / "models.yaml", "w") as f:
            yaml.dump(new_agent_models, f)
        
        # Reload configuration
        config_manager.reload()
        
        # Should reflect changes
        updated_summary = config_manager.get_summary()
        assert updated_summary["agents_loaded"] == 3
        assert "new_agent" in updated_summary["agent_names"]
        
        # Should be able to access new agent
        new_agent = config_manager.get_agent_config("new_agent")
        assert new_agent is not None
        assert new_agent.name == "new_agent"


class TestAgentConfig:
    """Test suite for AgentConfig class"""

    def test_agent_config_creation(self):
        """Test AgentConfig creation and basic functionality"""
        config = AgentConfig(
            name="test_agent",
            description="Test agent",
            type="test_type",
            models={"preferred": "test_model", "fallback": ["backup_model"]},
            settings={"temperature": 0.8, "max_tokens": 1000},
            prompts={"system_prompt": "Test prompt"},
            behavior={"style": "friendly"},
            escalation={"threshold": 0.9}
        )
        
        assert config.name == "test_agent"
        assert config.description == "Test agent"
        assert config.type == "test_type"
        assert config.get_preferred_model() == "test_model"
        assert config.get_fallback_models() == ["backup_model"]
        assert config.get_setting("temperature") == 0.8
        assert config.get_prompt("system") == "Test prompt"

    def test_agent_config_defaults(self):
        """Test AgentConfig with default values"""
        config = AgentConfig(
            name="minimal_agent",
            description="Minimal agent",
            type="minimal_type"
        )
        
        assert config.name == "minimal_agent"
        assert config.get_preferred_model() == "local_general_standard"  # Default
        assert config.get_fallback_models() == []
        assert config.get_setting("nonexistent", "default") == "default"

    def test_agent_config_nested_settings(self):
        """Test nested setting access"""
        config = AgentConfig(
            name="nested_agent",
            description="Nested agent",
            type="nested_type",
            settings={
                "nested": {
                    "deep": {
                        "value": 42
                    }
                }
            }
        )
        
        assert config.get_setting("nested.deep.value") == 42
        assert config.get_setting("nested.deep.nonexistent", "default") == "default"


class TestSystemConfig:
    """Test suite for SystemConfig class"""

    def test_system_config_creation(self):
        """Test SystemConfig creation"""
        config = SystemConfig(
            name="Test System",
            version="2.0.0",
            environment="test",
            thresholds={"test_threshold": 0.5},
            providers={"test_provider": "config"},
            monitoring={"enabled": True}
        )
        
        assert config.name == "Test System"
        assert config.version == "2.0.0"
        assert config.environment == "test"
        assert config.thresholds["test_threshold"] == 0.5

    def test_system_config_defaults(self):
        """Test SystemConfig with default values"""
        config = SystemConfig()
        
        assert config.name == "Modular LangGraph Hybrid System"
        assert config.version == "1.0.0"
        assert config.environment == "development"
        assert isinstance(config.thresholds, dict)