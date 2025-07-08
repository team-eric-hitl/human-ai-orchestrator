"""
Integration tests for complete system startup and initialization.
Tests end-to-end system initialization including all components.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.core.config import ConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.core.logging import get_logger, setup_development_logging
from src.core.session_tracker import SessionTracker
from src.integrations.llm_providers import LLMProviderFactory
from src.workflows.hybrid_workflow import HybridSystemWorkflow


class TestSystemStartup:
    """Integration tests for complete system startup"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory with all required files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create comprehensive test configuration
            models_config = {
                "providers": {
                    "openai": {
                        "api_key_env": "OPENAI_API_KEY",
                        "models": {
                            "gpt-4": {
                                "name": "gpt-4",
                                "type": "openai",
                                "max_tokens": 4000,
                                "temperature": 0.7,
                                "available": True,
                            },
                            "gpt-3.5-turbo": {
                                "name": "gpt-3.5-turbo",
                                "type": "openai",
                                "max_tokens": 4000,
                                "temperature": 0.7,
                                "available": True,
                            },
                        },
                    },
                    "local": {
                        "models": {
                            "llama-7b": {
                                "name": "llama-7b",
                                "type": "llama",
                                "model_path": "/models/llama-7b.gguf",
                                "max_tokens": 2000,
                                "temperature": 0.8,
                                "available": False,
                            }
                        }
                    },
                },
                "strategy": "best_available",
            }

            system_config = {
                "evaluation": {
                    "complexity_threshold": 0.7,
                    "escalation_threshold": 0.8,
                    "context_window": 5,
                    "max_context_length": 1000,
                },
                "logging": {
                    "level": "INFO",
                    "environment": "test",
                    "console_enabled": True,
                    "file_enabled": False,
                    "langsmith_enabled": False,
                },
                "session": {"timeout_hours": 24, "cleanup_interval_hours": 6},
            }

            prompts_config = {
                "answer_agent": {
                    "system_prompt": "You are a helpful AI assistant.",
                    "user_prompt": "Please answer the following question: {query}",
                    "context_prompt": "Based on the conversation history: {context}\n\nAnswer: {query}",
                },
                "evaluator_agent": {
                    "system_prompt": "You are an AI response evaluator.",
                    "evaluation_prompt": "Rate this response on a scale of 1-10:\nQuery: {query}\nResponse: {response}",
                    "escalation_prompt": "Should this query be escalated? Query: {query}\nContext: {context}",
                },
                "escalation_router": {
                    "system_prompt": "You are a query routing specialist.",
                    "routing_prompt": "Route this query to the appropriate expert: {query}",
                },
            }

            # Write configuration files
            with open(config_dir / "models.json", "w") as f:
                json.dump(models_config, f, indent=2)
            with open(config_dir / "system_config.json", "w") as f:
                json.dump(system_config, f, indent=2)
            with open(config_dir / "prompts.yaml", "w") as f:
                yaml.dump(prompts_config, f, default_flow_style=False)

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
        assert config_manager.models is not None
        assert config_manager.system is not None
        assert config_manager.prompts is not None

        # Test ContextProvider initialization
        context_provider = SQLiteContextProvider(temp_db_path)
        assert context_provider is not None
        assert Path(temp_db_path).exists()

        # Test SessionTracker initialization
        session_tracker = SessionTracker()
        assert session_tracker is not None
        assert session_tracker.sessions == {}

        # Cleanup
        context_provider.close()

    def test_logging_system_initialization(self, temp_config_dir):
        """Test logging system initialization with configuration"""
        config_manager = ConfigManager(str(temp_config_dir))

        # Setup logging from configuration
        setup_development_logging()

        # Test logger creation
        logger = get_logger("test_system")
        assert logger is not None

        # Test logging with context
        logger.set_context(system="startup_test")
        logger.info("System initialization test")

        # Should not raise exceptions
        logger.performance_metric("initialization_time", 1.23)
        logger.user_interaction("test_user", "test query", "ai_handled")

    def test_llm_provider_factory_initialization(self, temp_config_dir):
        """Test LLM provider factory initialization"""
        config_manager = ConfigManager(str(temp_config_dir))

        # Create provider factory from configuration
        factory = LLMProviderFactory(config_manager.models.providers)
        assert factory is not None

        # Test provider availability checking
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            available_providers = factory.get_available_providers()
            assert len(available_providers) >= 1
            assert any(p["provider"] == "openai" for p in available_providers)

    def test_hybrid_workflow_initialization(self, temp_config_dir, temp_db_path):
        """Test complete hybrid workflow initialization"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Should initialize without errors
            workflow = HybridSystemWorkflow(
                config_dir=str(temp_config_dir), context_db=temp_db_path
            )

            assert workflow is not None
            assert workflow.config_provider is not None
            assert workflow.context_provider is not None
            assert workflow.answer_agent is not None
            assert workflow.evaluator_agent is not None
            assert workflow.escalation_router is not None

    def test_end_to_end_system_startup(self, temp_config_dir, temp_db_path):
        """Test complete end-to-end system startup"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Initialize logging
            setup_development_logging()
            logger = get_logger("system_startup")
            logger.info("Starting system initialization test")

            # Initialize configuration
            config_manager = ConfigManager(str(temp_config_dir))
            logger.info("Configuration loaded successfully")

            # Initialize context storage
            context_provider = SQLiteContextProvider(temp_db_path)
            logger.info("Context storage initialized")

            # Initialize session tracking
            session_tracker = SessionTracker()
            logger.info("Session tracking initialized")

            # Initialize LLM providers
            factory = LLMProviderFactory(config_manager.models.providers)
            logger.info("LLM provider factory initialized")

            # Verify system is functional
            available_models = factory.get_available_models()
            assert len(available_models) > 0

            # Create a test session
            session_tracker.start_session("test_session", "test_user")
            session_tracker.record_query("test_session", 1.0, 100, 0.01, False)

            # Verify session was recorded
            metrics = session_tracker.get_session_metrics("test_session")
            assert metrics is not None
            assert metrics.total_queries == 1

            logger.info("System startup test completed successfully")

            # Cleanup
            context_provider.close()

    def test_system_startup_with_missing_components(self, temp_config_dir):
        """Test system startup behavior with missing components"""
        # Remove a required configuration file
        (Path(temp_config_dir) / "models.json").unlink()

        # Should raise configuration error
        with pytest.raises(Exception):  # ConfigurationError or similar
            ConfigManager(str(temp_config_dir))

    def test_system_startup_with_invalid_configuration(self, temp_config_dir):
        """Test system startup with invalid configuration"""
        # Create invalid models.json
        invalid_config = {"invalid": "configuration"}
        with open(Path(temp_config_dir) / "models.json", "w") as f:
            json.dump(invalid_config, f)

        # Should handle gracefully or raise appropriate error
        with pytest.raises(Exception):  # ValidationError or similar
            ConfigManager(str(temp_config_dir))

    def test_system_startup_with_missing_api_keys(self, temp_config_dir, temp_db_path):
        """Test system startup without API keys"""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            config_manager = ConfigManager(str(temp_config_dir))

            # Should still initialize configuration
            assert config_manager is not None

            # But LLM providers should report no available models
            factory = LLMProviderFactory(config_manager.models.providers)
            available_models = factory.get_available_models()

            # Should have no available models due to missing API keys
            assert len(available_models) == 0

    def test_system_startup_performance(self, temp_config_dir, temp_db_path):
        """Test system startup performance"""
        import time

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            start_time = time.time()

            # Initialize all components
            setup_development_logging()
            config_manager = ConfigManager(str(temp_config_dir))
            context_provider = SQLiteContextProvider(temp_db_path)
            session_tracker = SessionTracker()
            factory = LLMProviderFactory(config_manager.models.providers)

            end_time = time.time()
            startup_time = end_time - start_time

            # Should start up reasonably quickly (less than 5 seconds)
            assert startup_time < 5.0

            # Log performance metric
            logger = get_logger("performance_test")
            logger.performance_metric("system_startup_time", startup_time)

            # Cleanup
            context_provider.close()

    def test_system_startup_with_existing_data(self, temp_config_dir, temp_db_path):
        """Test system startup with existing data"""
        # First startup - create some data
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            context_provider = SQLiteContextProvider(temp_db_path)
            session_tracker = SessionTracker()

            # Add some test data
            from datetime import datetime

            from src.core.context_manager import ContextEntry

            test_entry = ContextEntry(
                user_id="existing_user",
                session_id="existing_session",
                query_id="existing_query",
                query="Existing test query",
                response="Existing test response",
                timestamp=datetime.now(),
                escalated=False,
                response_time=1.0,
                token_count=100,
            )

            context_provider.save_context_entry(test_entry)
            context_provider.close()

            # Second startup - should load existing data
            context_provider2 = SQLiteContextProvider(temp_db_path)
            existing_context = context_provider2.get_context(user_id="existing_user")

            assert len(existing_context) == 1
            assert existing_context[0].query == "Existing test query"

            context_provider2.close()

    def test_system_startup_error_recovery(self, temp_config_dir, temp_db_path):
        """Test system startup error recovery"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Simulate database connection error
            with patch("sqlite3.connect", side_effect=Exception("Database error")):
                with pytest.raises(Exception):
                    SQLiteContextProvider(temp_db_path)

            # Should recover and work normally after error
            context_provider = SQLiteContextProvider(temp_db_path)
            assert context_provider is not None
            context_provider.close()

    def test_system_startup_concurrent_initialization(
        self, temp_config_dir, temp_db_path
    ):
        """Test concurrent system initialization"""
        import threading

        results = []

        def initialize_system():
            try:
                with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                    config_manager = ConfigManager(str(temp_config_dir))
                    factory = LLMProviderFactory(config_manager.models.providers)
                    available_models = factory.get_available_models()
                    results.append(len(available_models))
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

    def test_system_startup_memory_usage(self, temp_config_dir, temp_db_path):
        """Test system startup memory usage"""
        import gc

        # Measure memory before
        gc.collect()
        initial_objects = len(gc.get_objects())

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Initialize system
            config_manager = ConfigManager(str(temp_config_dir))
            context_provider = SQLiteContextProvider(temp_db_path)
            session_tracker = SessionTracker()
            factory = LLMProviderFactory(config_manager.models.providers)

            # Measure memory after
            gc.collect()
            final_objects = len(gc.get_objects())

            # Memory increase should be reasonable
            memory_increase = final_objects - initial_objects
            assert memory_increase < 10000  # Arbitrary reasonable limit

            # Cleanup
            context_provider.close()
            del config_manager, context_provider, session_tracker, factory

            # Verify cleanup
            gc.collect()
            cleanup_objects = len(gc.get_objects())
            assert cleanup_objects <= final_objects


class TestSystemConfiguration:
    """Integration tests for system configuration management"""

    def test_configuration_override_hierarchy(self, temp_config_dir):
        """Test configuration override hierarchy"""
        # Base configuration
        config_manager = ConfigManager(str(temp_config_dir))
        base_strategy = config_manager.models.strategy

        # Environment variable override
        with patch.dict(os.environ, {"LLM_PROVIDER": "local", "LLM_MODEL": "llama-7b"}):
            provider, model = config_manager.get_active_model()
            assert provider == "local"
            assert model == "llama-7b"

        # Should revert to base when environment cleared
        with patch.dict(os.environ, {}, clear=True):
            provider, model = config_manager.get_primary_model()
            # Should use configuration default
            assert provider is not None
            assert model is not None

    def test_configuration_validation_integration(self, temp_config_dir):
        """Test integrated configuration validation"""
        config_manager = ConfigManager(str(temp_config_dir))

        # Get validation summary
        summary = config_manager.get_summary()

        assert "total_models_configured" in summary
        assert "available_models" in summary
        assert "validation_results" in summary

        # With API key, should have available models
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config_manager.validate_model_availability()
            updated_summary = config_manager.get_summary()
            assert len(updated_summary["available_models"]) > 0

    def test_configuration_hot_reload(self, temp_config_dir):
        """Test configuration hot reload functionality"""
        config_manager = ConfigManager(str(temp_config_dir))

        # Initial state
        initial_summary = config_manager.get_summary()

        # Modify configuration file
        models_file = Path(temp_config_dir) / "models.json"
        with open(models_file) as f:
            config_data = json.load(f)

        # Add a new model
        config_data["providers"]["openai"]["models"]["gpt-3.5-turbo-16k"] = {
            "name": "gpt-3.5-turbo-16k",
            "type": "openai",
            "max_tokens": 16000,
            "temperature": 0.7,
            "available": True,
        }

        with open(models_file, "w") as f:
            json.dump(config_data, f, indent=2)

        # Reload configuration
        config_manager.reload()

        # Should reflect changes
        updated_summary = config_manager.get_summary()
        assert (
            updated_summary["total_models_configured"]
            > initial_summary["total_models_configured"]
        )


class TestSystemIntegration:
    """Integration tests for system component interactions"""

    def test_config_to_provider_integration(self, temp_config_dir):
        """Test configuration to provider integration"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config_manager = ConfigManager(str(temp_config_dir))
            factory = LLMProviderFactory(config_manager.models.providers)

            # Should be able to create provider from configuration
            provider = factory.get_best_available_provider()
            assert provider is not None
            assert provider.model_config.name in config_manager.get_available_models()

    def test_logging_to_context_integration(self, temp_config_dir, temp_db_path):
        """Test logging to context integration"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            setup_development_logging()
            logger = get_logger("integration_test")
            context_provider = SQLiteContextProvider(temp_db_path)

            # Log user interaction
            logger.user_interaction(
                user_id="integration_user",
                query="Integration test query",
                response_type="ai_handled",
            )

            # Should be able to save to context
            from datetime import datetime

            from src.core.context_manager import ContextEntry

            entry = ContextEntry(
                user_id="integration_user",
                session_id="integration_session",
                query_id="integration_query",
                query="Integration test query",
                response="Integration test response",
                timestamp=datetime.now(),
                escalated=False,
                response_time=1.0,
                token_count=100,
            )

            context_provider.save_context_entry(entry)

            # Should be retrievable
            context = context_provider.get_context(user_id="integration_user")
            assert len(context) == 1
            assert context[0].query == "Integration test query"

            context_provider.close()

    def test_session_to_metrics_integration(self, temp_config_dir):
        """Test session tracking to metrics integration"""
        session_tracker = SessionTracker()

        # Create test session
        session_tracker.start_session("metrics_session", "metrics_user")

        # Record multiple queries
        for i in range(5):
            session_tracker.record_query(
                session_id="metrics_session",
                response_time=1.0 + i * 0.1,
                token_count=100 + i * 10,
                cost=0.01 + i * 0.001,
                escalated=i % 2 == 0,
            )

        # Get session metrics
        session_metrics = session_tracker.get_session_metrics("metrics_session")
        assert session_metrics.total_queries == 5
        assert session_metrics.escalated_queries == 3  # 0, 2, 4
        assert session_metrics.escalation_rate == 0.6

        # Get global metrics
        global_metrics = session_tracker.get_global_metrics()
        assert global_metrics["total_sessions"] == 1
        assert global_metrics["total_queries"] == 5
        assert global_metrics["global_escalation_rate"] == 0.6
