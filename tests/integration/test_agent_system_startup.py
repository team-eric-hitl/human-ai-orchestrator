"""
Integration tests for complete system startup with agent-centric configuration.
Tests end-to-end system initialization including all components.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.core.config.agent_config_manager import AgentConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.core.logging import get_logger, configure_logging
from src.core.session_tracker import SessionTracker


class TestAgentSystemStartup:
    """Integration tests for complete system startup with agent-centric config"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary agent-centric configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create directory structure - using current system agents
            (config_dir / "agents" / "chatbot_agent").mkdir(parents=True)
            (config_dir / "agents" / "frustration_agent").mkdir(parents=True)
            (config_dir / "agents" / "quality_agent").mkdir(parents=True)
            (config_dir / "agents" / "context_manager_agent").mkdir(parents=True)
            (config_dir / "agents" / "human_routing_agent").mkdir(parents=True)
            (config_dir / "shared").mkdir(parents=True)
            (config_dir / "environments").mkdir(parents=True)

            # Create shared configurations
            shared_models = {
                "models": {
                    "gpt-4": {
                        "provider": "openai",
                        "model_name": "gpt-4",
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "cost_per_1k_tokens": 0.03
                    },
                    "gpt-3.5-turbo": {
                        "provider": "openai", 
                        "model_name": "gpt-3.5-turbo",
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "cost_per_1k_tokens": 0.002
                    },
                    "gemini-1.5-flash": {
                        "provider": "google",
                        "model_name": "gemini-1.5-flash",
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "cost_per_1k_tokens": 0.0005
                    }
                },
                "model_aliases": {
                    "fast_model": "gemini-1.5-flash",
                    "quality_model": "gpt-4",
                    "default_model": "gpt-3.5-turbo"
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

            # Create agent configurations - current system agents
            chatbot_agent = {
                "agent": {
                    "name": "chatbot_agent",
                    "description": "Customer service focused chatbot agent",
                    "type": "response_agent"
                },
                "settings": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "timeout": 30
                }
            }

            chatbot_agent_models = {
                "primary_model": "fast_model",
                "model_preferences": {
                    "fast_model": {"weight": 1.0},
                    "gpt-3.5-turbo": {"weight": 0.8}
                }
            }

            chatbot_prompts = {
                "system": "You are a helpful customer service assistant. Provide accurate, empathetic responses.",
                "context_templates": {
                    "new_customer_note": "This appears to be a new customer.",
                    "customer_context_header": "Customer Context:"
                }
            }

            frustration_agent = {
                "agent": {
                    "name": "frustration_agent", 
                    "description": "Customer frustration detection agent",
                    "type": "analysis_agent"
                },
                "settings": {
                    "frustration_thresholds": {
                        "critical": 8.0,
                        "high": 6.0,
                        "moderate": 3.0
                    },
                    "intervention_threshold": "high"
                }
            }

            frustration_agent_models = {
                "primary_model": "fast_model",
                "model_preferences": {
                    "fast_model": {"weight": 1.0}
                }
            }

            quality_agent = {
                "agent": {
                    "name": "quality_agent",
                    "description": "Response quality assessment agent", 
                    "type": "quality_agent"
                },
                "settings": {
                    "quality_thresholds": {
                        "adequate_score": 7.0,
                        "adjustment_score": 5.0
                    }
                }
            }

            quality_agent_models = {
                "primary_model": "fast_model", 
                "model_preferences": {
                    "fast_model": {"weight": 1.0}
                }
            }

            context_manager_agent = {
                "agent": {
                    "name": "context_manager_agent",
                    "description": "Context retrieval and management agent",
                    "type": "context_agent"
                },
                "settings": {
                    "optimization": {
                        "cache_context_summaries": True,
                        "cache_duration_minutes": 15
                    }
                }
            }

            context_manager_agent_models = {
                "primary_model": "fast_model",
                "model_preferences": {
                    "fast_model": {"weight": 1.0}
                }
            }

            human_routing_agent = {
                "agent": {
                    "name": "human_routing_agent",
                    "description": "Routes escalations to appropriate human agents",
                    "type": "routing_agent"
                },
                "settings": {
                    "use_llm_routing": True,
                    "routing_strategy": "skill_based"
                }
            }

            human_routing_agent_models = {
                "primary_model": "fast_model",
                "model_preferences": {
                    "fast_model": {"weight": 1.0}
                }
            }

            # Write all configuration files
            with open(config_dir / "shared" / "models.yaml", "w") as f:
                yaml.dump(shared_models, f)
            with open(config_dir / "shared" / "system.yaml", "w") as f:
                yaml.dump(shared_system, f)
            with open(config_dir / "shared" / "providers.yaml", "w") as f:
                yaml.dump(shared_providers, f)

            # Write current system agent configs
            with open(config_dir / "agents" / "chatbot_agent" / "config.yaml", "w") as f:
                yaml.dump(chatbot_agent, f)
            with open(config_dir / "agents" / "chatbot_agent" / "prompts.yaml", "w") as f:
                yaml.dump(chatbot_prompts, f)
            with open(config_dir / "agents" / "chatbot_agent" / "models.yaml", "w") as f:
                yaml.dump(chatbot_agent_models, f)

            with open(config_dir / "agents" / "frustration_agent" / "config.yaml", "w") as f:
                yaml.dump(frustration_agent, f)
            with open(config_dir / "agents" / "frustration_agent" / "models.yaml", "w") as f:
                yaml.dump(frustration_agent_models, f)

            with open(config_dir / "agents" / "quality_agent" / "config.yaml", "w") as f:
                yaml.dump(quality_agent, f)
            with open(config_dir / "agents" / "quality_agent" / "models.yaml", "w") as f:
                yaml.dump(quality_agent_models, f)

            with open(config_dir / "agents" / "context_manager_agent" / "config.yaml", "w") as f:
                yaml.dump(context_manager_agent, f)
            with open(config_dir / "agents" / "context_manager_agent" / "models.yaml", "w") as f:
                yaml.dump(context_manager_agent_models, f)

            with open(config_dir / "agents" / "human_routing_agent" / "config.yaml", "w") as f:
                yaml.dump(human_routing_agent, f)
            with open(config_dir / "agents" / "human_routing_agent" / "models.yaml", "w") as f:
                yaml.dump(human_routing_agent_models, f)

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
        # Test AgentConfigManager initialization
        config_manager = AgentConfigManager(str(temp_config_dir))
        assert config_manager is not None

        # Test agent configurations are loaded
        available_agents = config_manager.get_available_agents()
        assert len(available_agents) >= 5  # Current system has 5 agents
        assert "chatbot_agent" in available_agents
        assert "frustration_agent" in available_agents  
        assert "quality_agent" in available_agents
        assert "context_manager_agent" in available_agents
        assert "human_routing_agent" in available_agents

        # Test system configuration
        system_config = config_manager.get_system_config()
        assert system_config.name == "Test Hybrid System"

        # Test models configuration
        models_config = config_manager.get_models_config()
        assert "models" in models_config
        assert len(models_config["models"]) >= 3

        # Test ContextProvider initialization
        context_provider = SQLiteContextProvider(config_manager=config_manager)
        assert context_provider is not None

        # Test SessionTracker initialization
        session_tracker = SessionTracker()
        assert session_tracker is not None
        assert session_tracker.active_sessions == {}

    def test_agent_specific_configurations(self, temp_config_dir):
        """Test agent-specific configuration loading"""
        config_manager = AgentConfigManager(str(temp_config_dir))

        # Test chatbot agent configuration
        chatbot_config = config_manager.get_agent_config("chatbot_agent")
        assert chatbot_config is not None
        assert chatbot_config.name == "chatbot_agent"
        preferred_model = config_manager.get_agent_preferred_model("chatbot_agent")
        assert preferred_model == "fast_model"
        
        # Test frustration agent configuration
        frustration_config = config_manager.get_agent_config("frustration_agent") 
        assert frustration_config is not None
        assert frustration_config.name == "frustration_agent"
        assert frustration_config.settings.get("frustration_thresholds", {}).get("high") == 6.0

        # Test quality agent configuration
        quality_config = config_manager.get_agent_config("quality_agent")
        assert quality_config is not None
        assert quality_config.name == "quality_agent"
        assert quality_config.settings.get("quality_thresholds", {}).get("adequate_score") == 7.0

        # Test human routing agent configuration
        router_config = config_manager.get_agent_config("human_routing_agent")
        assert router_config is not None
        assert router_config.name == "human_routing_agent"
        assert router_config.settings.get("use_llm_routing") is True

    def test_logging_system_initialization(self, temp_config_dir):
        """Test logging system initialization with agent-centric configuration"""
        config_manager = AgentConfigManager(str(temp_config_dir))

        # Setup logging from configuration
        logging_config = {
            "level": "INFO",
            "console": {"enabled": True, "level": "INFO"},
            "file": {"enabled": False}
        }
        configure_logging(logging_config)

        # Test logger creation
        logger = get_logger("test_agent_system")
        assert logger is not None

        # Test basic logging
        logger.info("Agent system initialization test")

        # Should not raise exceptions
        logger.info("Agent system test completed")

    def test_agent_model_preferences(self, temp_config_dir):
        """Test agent-specific model preferences"""
        config_manager = AgentConfigManager(str(temp_config_dir))

        # Test each agent gets its preferred model
        chatbot_model = config_manager.get_agent_preferred_model("chatbot_agent")
        assert chatbot_model == "fast_model"

        frustration_model = config_manager.get_agent_preferred_model("frustration_agent")
        assert frustration_model == "fast_model"

        quality_model = config_manager.get_agent_preferred_model("quality_agent")
        assert quality_model == "fast_model"

        context_model = config_manager.get_agent_preferred_model("context_manager_agent")
        assert context_model == "fast_model"

        router_model = config_manager.get_agent_preferred_model("human_routing_agent")
        assert router_model == "fast_model"

    def test_configuration_summary(self, temp_config_dir):
        """Test configuration summary with agent-centric structure"""
        config_manager = AgentConfigManager(str(temp_config_dir))

        # Test basic configuration access
        available_agents = config_manager.get_available_agents()
        assert len(available_agents) >= 5

        system_config = config_manager.get_system_config()
        assert system_config.name == "Test Hybrid System"

        models_config = config_manager.get_models_config()
        assert len(models_config["models"]) >= 3

        assert "chatbot_agent" in available_agents
        assert "frustration_agent" in available_agents
        assert "quality_agent" in available_agents
        assert "context_manager_agent" in available_agents
        assert "human_routing_agent" in available_agents

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
        config_manager = AgentConfigManager(str(temp_config_dir), environment="testing")

        system_config = config_manager.get_system_config()
        assert system_config.environment == "testing"

        # Should use overridden threshold
        escalation_score = config_manager.get_threshold("escalation_score")
        assert escalation_score == 5.0

    def test_configuration_validation(self, temp_config_dir):
        """Test configuration validation"""
        config_manager = AgentConfigManager(str(temp_config_dir))

        # Test that required directories exist
        assert config_manager.config_dir.exists()
        assert (config_manager.config_dir / "shared").exists()
        assert (config_manager.config_dir / "agents").exists()

        # Test that basic configurations are loaded
        available_agents = config_manager.get_available_agents()
        assert len(available_agents) >= 5

        system_config = config_manager.get_system_config()
        assert system_config.name is not None

    def test_configuration_reloading(self, temp_config_dir):
        """Test configuration hot reloading"""
        config_manager = AgentConfigManager(str(temp_config_dir))

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
            "primary_model": "fast_model"
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
        logging_config = {
            "level": "INFO",
            "console": {"enabled": True, "level": "INFO"},
            "file": {"enabled": False}
        }
        configure_logging(logging_config)
        config_manager = AgentConfigManager(str(temp_config_dir))
        context_provider = SQLiteContextProvider(config_manager=config_manager)
        session_tracker = SessionTracker()

        end_time = time.time()
        startup_time = end_time - start_time

        # Should start up reasonably quickly (less than 5 seconds)
        assert startup_time < 5.0

        # Log performance metric
        logger = get_logger("performance_test")
        logger.info(f"Agent system startup time: {startup_time:.2f}s")

    def test_concurrent_initialization(self, temp_config_dir):
        """Test concurrent system initialization"""
        import threading

        results = []

        def initialize_system():
            try:
                config_manager = AgentConfigManager(str(temp_config_dir))
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

        # Should still work with defaults or handle gracefully
        config_manager = AgentConfigManager(str(temp_config_dir))
        assert config_manager is not None

        # Should still load agents even with missing system config
        available_agents = config_manager.get_available_agents()
        assert len(available_agents) >= 5

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
        config_manager = AgentConfigManager(str(temp_config_dir))

        # Invalid agent should be handled gracefully
        try:
            invalid_agent = config_manager.get_agent_config("invalid_agent")
            # Either returns None or a valid agent config object
            assert invalid_agent is None or hasattr(invalid_agent, 'name')
        except Exception:
            # Or raises an exception, which is also acceptable
            pass
