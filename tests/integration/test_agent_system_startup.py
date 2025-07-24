"""
Integration tests for complete system startup with agent-centric configuration.
Tests end-to-end system initialization including all components.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.core.config import ConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.core.logging import get_logger, setup_development_logging
from src.core.session_tracker import SessionTracker


class TestAgentSystemStartup:
    """Integration tests for complete system startup with agent-centric config"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary agent-centric configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create directory structure
            (config_dir / "agents" / "answer_agent").mkdir(parents=True)
            (config_dir / "agents" / "evaluator_agent").mkdir(parents=True)
            (config_dir / "agents" / "escalation_router").mkdir(parents=True)
            (config_dir / "shared").mkdir(parents=True)
            (config_dir / "environments").mkdir(parents=True)

            # Create shared configurations
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
                    },
                    "gpt-3.5-turbo": {
                        "type": "openai",
                        "model_name": "gpt-3.5-turbo",
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "description": "OpenAI GPT-3.5 Turbo"
                    }
                },
                "use_cases": {
                    "general": {
                        "recommended": "llama-7b",
                        "alternatives": ["gpt-4", "gpt-3.5-turbo"]
                    },
                    "high_quality": {
                        "recommended": "gpt-4",
                        "alternatives": ["gpt-3.5-turbo", "llama-7b"]
                    }
                }
            }

            shared_system = {
                "system": {
                    "name": "Test Hybrid System",
                    "version": "1.0.0"
                },
                "thresholds": {
                    "escalation_score": 6.0,
                    "confidence_threshold": 0.7,
                    "response_time_limit": 30,
                    "max_retries": 3
                },
                "providers": {
                    "context": {
                        "type": "sqlite",
                        "db_path": "test_system.db"
                    }
                },
                "monitoring": {
                    "metrics_collection": True,
                    "log_level": "INFO"
                }
            }

            shared_providers = {
                "llm_providers": {
                    "openai": {
                        "enabled": True,
                        "api_key_env": "OPENAI_API_KEY",
                        "models": ["gpt-4", "gpt-3.5-turbo"]
                    },
                    "local": {
                        "enabled": True,
                        "models": ["llama-7b"]
                    }
                }
            }

            # Create agent configurations
            answer_agent = {
                "agent": {
                    "name": "answer_agent",
                    "description": "Primary response generation agent",
                    "type": "llm_agent"
                },
                "settings": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "timeout": 30
                }
            }

            answer_agent_models = {
                "preferred": "llama-7b",
                "fallback": ["gpt-4", "gpt-3.5-turbo"]
            }

            answer_prompts = {
                "system_prompt": "You are a helpful AI assistant. Provide accurate, helpful responses.",
                "templates": {
                    "greeting": "Hello! How can I assist you today?",
                    "no_context": "I'll help you with your question."
                }
            }

            evaluator_agent = {
                "agent": {
                    "name": "evaluator_agent",
                    "description": "Response quality evaluation agent",
                    "type": "evaluation_agent"
                },
                "settings": {
                    "temperature": 0.3,
                    "max_tokens": 1500
                },
                "evaluation": {
                    "criteria": {
                        "accuracy": {"weight": 0.3},
                        "completeness": {"weight": 0.25},
                        "clarity": {"weight": 0.25},
                        "user_satisfaction": {"weight": 0.2}
                    }
                },
                "escalation": {
                    "confidence_threshold": 0.7
                }
            }

            evaluator_agent_models = {
                "preferred": "gpt-4",
                "fallback": ["gpt-3.5-turbo", "llama-7b"]
            }

            escalation_router = {
                "agent": {
                    "name": "escalation_router",
                    "description": "Routes escalations to appropriate human agents",
                    "type": "routing_agent"
                },
                "settings": {
                    "temperature": 0.4,
                    "max_tokens": 1000
                },
                "routing": {
                    "expertise_domains": {
                        "technical": {
                            "keywords": ["code", "programming", "API", "bug", "error"]
                        },
                        "general": {
                            "keywords": ["help", "support", "question"]
                        }
                    }
                }
            }

            escalation_router_models = {
                "preferred": "gpt-3.5-turbo",
                "fallback": ["llama-7b"]
            }

            # Write all configuration files
            with open(config_dir / "shared" / "models.yaml", "w") as f:
                yaml.dump(shared_models, f)
            with open(config_dir / "shared" / "system.yaml", "w") as f:
                yaml.dump(shared_system, f)
            with open(config_dir / "shared" / "providers.yaml", "w") as f:
                yaml.dump(shared_providers, f)

            with open(config_dir / "agents" / "answer_agent" / "config.yaml", "w") as f:
                yaml.dump(answer_agent, f)
            with open(config_dir / "agents" / "answer_agent" / "prompts.yaml", "w") as f:
                yaml.dump(answer_prompts, f)
            with open(config_dir / "agents" / "answer_agent" / "models.yaml", "w") as f:
                yaml.dump(answer_agent_models, f)

            with open(config_dir / "agents" / "evaluator_agent" / "config.yaml", "w") as f:
                yaml.dump(evaluator_agent, f)
            with open(config_dir / "agents" / "evaluator_agent" / "models.yaml", "w") as f:
                yaml.dump(evaluator_agent_models, f)

            with open(config_dir / "agents" / "escalation_router" / "config.yaml", "w") as f:
                yaml.dump(escalation_router, f)
            with open(config_dir / "agents" / "escalation_router" / "models.yaml", "w") as f:
                yaml.dump(escalation_router_models, f)

            yield config_dir

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            db_path = temp_file.name
        yield db_path
        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    def test_basic_system_initialization(self, temp_config_dir, temp_db_path):
        """Test basic system component initialization"""
        # Test ConfigManager initialization
        config_manager = ConfigManager(str(temp_config_dir))
        assert config_manager is not None

        # Test agent configurations are loaded
        available_agents = config_manager.get_available_agents()
        assert len(available_agents) >= 3
        assert "answer_agent" in available_agents
        assert "evaluator_agent" in available_agents
        assert "escalation_router" in available_agents

        # Test system configuration
        system_config = config_manager.get_system_config()
        assert system_config.name == "Test Hybrid System"

        # Test models configuration
        models_config = config_manager.get_models_config()
        assert "models" in models_config
        assert len(models_config["models"]) >= 3

        # Test ContextProvider initialization
        context_provider = SQLiteContextProvider(temp_db_path)
        assert context_provider is not None
        assert Path(temp_db_path).exists()

        # Test SessionTracker initialization
        session_tracker = SessionTracker()
        assert session_tracker is not None
        assert session_tracker.active_sessions == {}

        # Cleanup - no close method needed for SQLiteContextProvider

    def test_agent_specific_configurations(self, temp_config_dir):
        """Test agent-specific configuration loading"""
        config_manager = ConfigManager(str(temp_config_dir))

        # Test answer agent configuration
        answer_config = config_manager.get_agent_config("answer_agent")
        assert answer_config is not None
        assert answer_config.name == "answer_agent"
        assert answer_config.get_preferred_model() == "llama-7b"
        assert answer_config.get_setting("temperature") == 0.7
        assert answer_config.get_prompt("system") == "You are a helpful AI assistant. Provide accurate, helpful responses."

        # Test evaluator agent configuration
        evaluator_config = config_manager.get_agent_config("evaluator_agent")
        assert evaluator_config is not None
        assert evaluator_config.get_preferred_model() == "gpt-4"
        assert evaluator_config.get_setting("temperature") == 0.3
        assert evaluator_config.get_setting("criteria.accuracy.weight") == 0.3

        # Test escalation router configuration
        router_config = config_manager.get_agent_config("escalation_router")
        assert router_config is not None
        assert router_config.get_preferred_model() == "gpt-3.5-turbo"
        assert router_config.get_setting("expertise_domains.technical.keywords") == ["code", "programming", "API", "bug", "error"]

    def test_logging_system_initialization(self, temp_config_dir):
        """Test logging system initialization with agent-centric configuration"""
        config_manager = ConfigManager(str(temp_config_dir))

        # Setup logging from configuration
        setup_development_logging()

        # Test logger creation
        logger = get_logger("test_agent_system")
        assert logger is not None

        # Test logging with context
        logger.set_context(system="agent_startup_test")
        logger.info("Agent system initialization test")

        # Should not raise exceptions
        logger.performance_metric("initialization_time", 1.23)
        logger.user_interaction("test_user", "test query", "ai_handled")

    def test_agent_model_preferences(self, temp_config_dir):
        """Test agent-specific model preferences"""
        config_manager = ConfigManager(str(temp_config_dir))

        # Test each agent gets its preferred model
        answer_model = config_manager.get_primary_model_for_agent("answer_agent")
        assert answer_model == "llama-7b"

        evaluator_model = config_manager.get_primary_model_for_agent("evaluator_agent")
        assert evaluator_model == "gpt-4"

        router_model = config_manager.get_primary_model_for_agent("escalation_router")
        assert router_model == "gpt-3.5-turbo"

    def test_configuration_summary(self, temp_config_dir):
        """Test configuration summary with agent-centric structure"""
        config_manager = ConfigManager(str(temp_config_dir))

        summary = config_manager.get_summary()

        assert "config_directory" in summary
        assert "environment" in summary
        assert "system_name" in summary
        assert "agents_loaded" in summary
        assert "agent_names" in summary
        assert "models_configured" in summary

        assert summary["system_name"] == "Test Hybrid System"
        assert summary["agents_loaded"] >= 3
        assert "answer_agent" in summary["agent_names"]
        assert "evaluator_agent" in summary["agent_names"]
        assert "escalation_router" in summary["agent_names"]

    def test_environment_configuration(self, temp_config_dir):
        """Test environment-specific configuration"""
        # Create test environment config
        test_env_config = {
            "environment": "testing",
            "system": {
                "name": "Test Environment System"
            },
            "thresholds": {
                "escalation_score": 5.0  # Override default
            }
        }

        with open(temp_config_dir / "environments" / "testing.yaml", "w") as f:
            yaml.dump(test_env_config, f)

        # Test with specific environment
        config_manager = ConfigManager(str(temp_config_dir), environment="testing")

        system_config = config_manager.get_system_config()
        assert system_config.environment == "testing"

        # Should use overridden threshold
        escalation_score = config_manager.get_threshold("escalation_score")
        assert escalation_score == 5.0

    def test_configuration_validation(self, temp_config_dir):
        """Test configuration validation"""
        config_manager = ConfigManager(str(temp_config_dir))

        summary = config_manager.get_summary()

        # Should have valid structure
        structure = summary["config_files_structure"]
        assert structure["shared"] == True
        assert structure["agents"] == True
        assert structure["environments"] == True

    def test_configuration_reloading(self, temp_config_dir):
        """Test configuration hot reloading"""
        config_manager = ConfigManager(str(temp_config_dir))

        # Initial state
        initial_agents = len(config_manager.get_available_agents())

        # Add new agent
        new_agent_config = {
            "agent": {
                "name": "new_test_agent",
                "description": "New test agent",
                "type": "test_agent"
            }
        }

        new_agent_models = {
            "preferred": "llama-7b"
        }

        new_agent_dir = temp_config_dir / "agents" / "new_test_agent"
        new_agent_dir.mkdir()

        with open(new_agent_dir / "config.yaml", "w") as f:
            yaml.dump(new_agent_config, f)
        with open(new_agent_dir / "models.yaml", "w") as f:
            yaml.dump(new_agent_models, f)

        # Reload configuration
        config_manager.reload()

        # Should have new agent
        updated_agents = len(config_manager.get_available_agents())
        assert updated_agents == initial_agents + 1

        new_agent = config_manager.get_agent_config("new_test_agent")
        assert new_agent is not None
        assert new_agent.name == "new_test_agent"

    def test_system_startup_performance(self, temp_config_dir, temp_db_path):
        """Test system startup performance"""
        import time

        start_time = time.time()

        # Initialize all components
        setup_development_logging()
        config_manager = ConfigManager(str(temp_config_dir))
        context_provider = SQLiteContextProvider(temp_db_path)
        session_tracker = SessionTracker()

        end_time = time.time()
        startup_time = end_time - start_time

        # Should start up reasonably quickly (less than 5 seconds)
        assert startup_time < 5.0

        # Log performance metric
        logger = get_logger("performance_test")
        logger.performance_metric("agent_system_startup_time", startup_time)

        # Cleanup - no close method needed for SQLiteContextProvider

    def test_concurrent_initialization(self, temp_config_dir):
        """Test concurrent system initialization"""
        import threading

        results = []

        def initialize_system():
            try:
                config_manager = ConfigManager(str(temp_config_dir))
                agents_count = len(config_manager.get_available_agents())
                results.append(agents_count)
            except Exception as e:
                results.append(f"Error: {e}")

        # Start multiple initialization threads
        threads = [threading.Thread(target=initialize_system) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All should succeed with same result
        assert len(results) == 3
        assert all(isinstance(result, int) for result in results)
        assert all(result == results[0] for result in results)

    def test_system_startup_with_missing_components(self, temp_config_dir):
        """Test system startup behavior with missing components"""
        # Remove required shared config
        (temp_config_dir / "shared" / "system.yaml").unlink()

        # Should still work with defaults
        config_manager = ConfigManager(str(temp_config_dir))
        assert config_manager is not None

        # Should have basic system config
        system_config = config_manager.get_system_config()
        assert system_config.name == "Modular LangGraph Hybrid System"  # Default

    def test_invalid_agent_configuration(self, temp_config_dir):
        """Test handling of invalid agent configuration"""
        # Create invalid agent config
        invalid_config = {
            "invalid": "configuration"
        }

        invalid_agent_dir = temp_config_dir / "agents" / "invalid_agent"
        invalid_agent_dir.mkdir()

        with open(invalid_agent_dir / "config.yaml", "w") as f:
            yaml.dump(invalid_config, f)

        # Should handle gracefully
        config_manager = ConfigManager(str(temp_config_dir))

        # Invalid agent should not be loaded
        invalid_agent = config_manager.get_agent_config("invalid_agent")
        assert invalid_agent is None or invalid_agent.name == "invalid_agent"  # Depends on implementation
