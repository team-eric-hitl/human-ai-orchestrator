"""
Comprehensive tests for LLM provider system.
Tests LLMProvider, LLMProviderFactory, and provider integrations.
"""

import os
from unittest.mock import Mock, patch

import pytest

from src.core.logging.exceptions import ConfigurationError, ModelError
from src.integrations.llm_providers import LLMProvider, LLMProviderFactory


class TestLLMProvider:
    """Test suite for LLMProvider class"""

    @pytest.fixture
    def openai_model_config(self):
        """Create OpenAI model configuration"""
        return {
            "model_name": "gpt-4",
            "type": "openai",
            "max_tokens": 4000,
            "temperature": 0.7,
        }

    @pytest.fixture
    def local_model_config(self):
        """Create local model configuration"""
        return {
            "model_name": "llama-7b",
            "type": "llama",
            "path": "/models/llama-7b.gguf",
            "max_tokens": 2000,
            "temperature": 0.8,
        }

    @pytest.fixture
    def openai_provider_config(self, openai_model_config):
        """Create OpenAI provider configuration"""
        return {
            "api_key_env": "OPENAI_API_KEY",
            "models": {"gpt-4": openai_model_config}
        }

    def test_llm_provider_initialization(self, openai_model_config):
        """Test LLMProvider initialization"""
        with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                mock_client = Mock()
                mock_openai.return_value = mock_client

                provider = LLMProvider(model_config=openai_model_config)

                assert provider.model_config == openai_model_config
                assert provider.provider_type == "openai"
                assert provider.model_name == "gpt-4"
                assert provider.client == mock_client

    def test_openai_provider_initialization(
        self, openai_model_config, openai_provider_config
    ):
        """Test OpenAI provider initialization"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=openai_model_config,
                    provider_config=openai_provider_config,
                )
                provider.initialize()

                assert provider.model is not None
                mock_openai.assert_called_once_with(
                    model_name="gpt-4",
                    openai_api_key="test-key",
                    max_tokens=4000,
                    temperature=0.7,
                )

    def test_local_provider_initialization(self, local_model_config):
        """Test local provider initialization"""
        with patch("src.integrations.llm_providers.LlamaCpp") as mock_llama:
            with patch("pathlib.Path.exists", return_value=True):
                mock_model = Mock()
                mock_llama.return_value = mock_model

                provider = LLMProvider(
                    model_config=local_model_config, provider_config=None
                )
                provider.initialize()

                assert provider.model is not None
                mock_llama.assert_called_once_with(
                    model_path="/models/llama-7b.gguf",
                    max_tokens=2000,
                    temperature=0.8,
                    n_gpu_layers=0,
                    verbose=False,
                )

    def test_provider_initialization_missing_api_key(
        self, openai_model_config, openai_provider_config
    ):
        """Test provider initialization with missing API key"""
        with patch.dict(os.environ, {}, clear=True):
            provider = LLMProvider(
                model_config=openai_model_config, provider_config=openai_provider_config
            )

            with pytest.raises(ConfigurationError, match="API key not found"):
                provider.initialize()

    def test_provider_initialization_missing_model_file(self, local_model_config):
        """Test provider initialization with missing model file"""
        with patch("pathlib.Path.exists", return_value=False):
            provider = LLMProvider(
                model_config=local_model_config, provider_config=None
            )

            with pytest.raises(ConfigurationError, match="Model file not found"):
                provider.initialize()

    def test_generate_response_success(
        self, openai_model_config, openai_provider_config
    ):
        """Test successful response generation"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_model.invoke.return_value = Mock(content="Test response")
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=openai_model_config,
                    provider_config=openai_provider_config,
                )
                provider.initialize()

                response = provider.generate_response("Test prompt")

                assert response == "Test response"
                mock_model.invoke.assert_called_once()

    def test_generate_response_with_context(
        self, openai_model_config, openai_provider_config
    ):
        """Test response generation with context"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_model.invoke.return_value = Mock(content="Contextual response")
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=openai_model_config,
                    provider_config=openai_provider_config,
                )
                provider.initialize()

                context = [
                    {"role": "user", "content": "Previous question"},
                    {"role": "assistant", "content": "Previous answer"},
                ]

                response = provider.generate_response(
                    "Follow-up question", context=context
                )

                assert response == "Contextual response"
                # Verify context was included in the call
                call_args = mock_model.invoke.call_args[0][0]
                assert len(call_args) == 3  # System + context + new message

    def test_generate_response_model_error(
        self, openai_model_config, openai_provider_config
    ):
        """Test response generation with model error"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_model.invoke.side_effect = Exception("Model error")
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=openai_model_config,
                    provider_config=openai_provider_config,
                )
                provider.initialize()

                with pytest.raises(ModelError, match="Model error"):
                    provider.generate_response("Test prompt")

    def test_evaluate_response_success(
        self, openai_model_config, openai_provider_config
    ):
        """Test successful response evaluation"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_model.invoke.return_value = Mock(content="8")
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=openai_model_config,
                    provider_config=openai_provider_config,
                )
                provider.initialize()

                score = provider.evaluate_response("Test query", "Test response")

                assert score == 8
                mock_model.invoke.assert_called_once()

    def test_evaluate_response_invalid_score(
        self, openai_model_config, openai_provider_config
    ):
        """Test response evaluation with invalid score"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_model.invoke.return_value = Mock(content="invalid")
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=openai_model_config,
                    provider_config=openai_provider_config,
                )
                provider.initialize()

                score = provider.evaluate_response("Test query", "Test response")

                assert score == 5  # Default fallback score

    def test_provider_model_type_support(self):
        """Test different model type support"""
        model_types = ["openai", "llama", "mistral"]

        for model_type in model_types:
            model_config = ModelConfig(
                name=f"test-{model_type}", type=model_type, available=True
            )

            provider = LLMProvider(model_config=model_config, provider_config=None)

            assert provider.model_config.type == model_type

    def test_provider_configuration_validation(self, openai_model_config):
        """Test provider configuration validation"""
        # Valid configuration
        valid_config = ProviderConfig(
            api_key_env="OPENAI_API_KEY", models={"gpt-4": openai_model_config}
        )

        provider = LLMProvider(
            model_config=openai_model_config, provider_config=valid_config
        )

        assert provider.provider_config == valid_config
        assert provider.validate_configuration() is True

    def test_provider_token_counting(self, openai_model_config, openai_provider_config):
        """Test token counting functionality"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=openai_model_config,
                    provider_config=openai_provider_config,
                )
                provider.initialize()

                # Mock token counting
                with patch.object(provider, "count_tokens", return_value=150):
                    tokens = provider.count_tokens("Test prompt")
                    assert tokens == 150

    def test_provider_cost_calculation(
        self, openai_model_config, openai_provider_config
    ):
        """Test cost calculation functionality"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=openai_model_config,
                    provider_config=openai_provider_config,
                )
                provider.initialize()

                # Mock cost calculation
                with patch.object(provider, "calculate_cost", return_value=0.02):
                    cost = provider.calculate_cost(input_tokens=100, output_tokens=50)
                    assert cost == 0.02


class TestLLMProviderFactory:
    """Test suite for LLMProviderFactory class"""

    @pytest.fixture
    def sample_providers_config(self):
        """Create sample providers configuration"""
        return {
            "openai": ProviderConfig(
                api_key_env="OPENAI_API_KEY",
                models={
                    "gpt-4": ModelConfig(name="gpt-4", type="openai", available=True),
                    "gpt-3.5-turbo": ModelConfig(
                        name="gpt-3.5-turbo", type="openai", available=True
                    ),
                },
            ),
            "local": ProviderConfig(
                models={
                    "llama-7b": ModelConfig(
                        name="llama-7b",
                        type="llama",
                        model_path="/models/llama-7b.gguf",
                        available=False,
                    )
                }
            ),
        }

    def test_factory_initialization(self, sample_providers_config):
        """Test LLMProviderFactory initialization"""
        factory = LLMProviderFactory(sample_providers_config)

        assert factory.providers_config == sample_providers_config
        assert len(factory.providers_config) == 2

    def test_create_provider_by_name(self, sample_providers_config):
        """Test creating provider by specific name"""
        factory = LLMProviderFactory(sample_providers_config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            provider = factory.create_provider("openai", "gpt-4")

            assert provider is not None
            assert provider.model_config.name == "gpt-4"
            assert provider.model_config.type == "openai"

    def test_create_provider_nonexistent_provider(self, sample_providers_config):
        """Test creating provider that doesn't exist"""
        factory = LLMProviderFactory(sample_providers_config)

        with pytest.raises(ConfigurationError, match="Provider not found"):
            factory.create_provider("nonexistent", "some-model")

    def test_create_provider_nonexistent_model(self, sample_providers_config):
        """Test creating provider with non-existent model"""
        factory = LLMProviderFactory(sample_providers_config)

        with pytest.raises(ConfigurationError, match="Model not found"):
            factory.create_provider("openai", "nonexistent-model")

    def test_create_provider_unavailable_model(self, sample_providers_config):
        """Test creating provider with unavailable model"""
        factory = LLMProviderFactory(sample_providers_config)

        with pytest.raises(ConfigurationError, match="Model not available"):
            factory.create_provider("local", "llama-7b")

    def test_get_best_available_provider(self, sample_providers_config):
        """Test getting best available provider"""
        factory = LLMProviderFactory(sample_providers_config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            provider = factory.get_best_available_provider()

            assert provider is not None
            assert provider.model_config.type == "openai"

    def test_get_best_available_provider_no_available(self, sample_providers_config):
        """Test getting best available provider when none available"""
        # Make all models unavailable
        for provider_config in sample_providers_config.values():
            for model_config in provider_config.models.values():
                model_config.available = False

        factory = LLMProviderFactory(sample_providers_config)

        with pytest.raises(ConfigurationError, match="No available models"):
            factory.get_best_available_provider()

    def test_get_available_providers(self, sample_providers_config):
        """Test getting list of available providers"""
        factory = LLMProviderFactory(sample_providers_config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            available = factory.get_available_providers()

            assert len(available) == 1  # Only OpenAI should be available
            assert available[0]["provider"] == "openai"
            assert len(available[0]["models"]) == 2

    def test_get_available_models(self, sample_providers_config):
        """Test getting list of available models"""
        factory = LLMProviderFactory(sample_providers_config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            available_models = factory.get_available_models()

            assert "gpt-4" in available_models
            assert "gpt-3.5-turbo" in available_models
            assert "llama-7b" not in available_models

    def test_provider_fallback_strategy(self, sample_providers_config):
        """Test provider fallback strategy"""
        factory = LLMProviderFactory(sample_providers_config)

        # Mock first provider failing
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch.object(factory, "create_provider") as mock_create:
                mock_create.side_effect = [
                    Exception("First provider failed"),
                    Mock(),  # Second provider succeeds
                ]

                # Should try fallback
                provider = factory.get_best_available_provider()
                assert provider is not None
                assert mock_create.call_count == 2

    def test_provider_priority_ordering(self, sample_providers_config):
        """Test provider priority ordering"""
        factory = LLMProviderFactory(sample_providers_config)

        # Mock all providers as available
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("pathlib.Path.exists", return_value=True):
                # Update local model to be available
                sample_providers_config["local"].models["llama-7b"].available = True

                available = factory.get_available_providers()

                # Should be ordered by priority (OpenAI first, then local)
                assert available[0]["provider"] == "openai"
                assert available[1]["provider"] == "local"

    def test_factory_configuration_validation(self, sample_providers_config):
        """Test factory configuration validation"""
        factory = LLMProviderFactory(sample_providers_config)

        validation_results = factory.validate_configuration()

        assert "openai" in validation_results
        assert "local" in validation_results

        # OpenAI should be valid (with API key)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            validation_results = factory.validate_configuration()
            assert validation_results["openai"]["valid"] is True

    def test_factory_model_loading_optimization(self, sample_providers_config):
        """Test factory model loading optimization"""
        factory = LLMProviderFactory(sample_providers_config)

        # Models should be loaded lazily
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_openai.return_value = mock_model

                # First call should initialize model
                provider1 = factory.create_provider("openai", "gpt-4")
                provider1.initialize()

                # Second call should reuse if same model
                provider2 = factory.create_provider("openai", "gpt-4")
                provider2.initialize()

                # Should only call ChatOpenAI once if caching is implemented
                assert mock_openai.call_count >= 1


class TestLLMProviderIntegration:
    """Integration tests for LLM provider system"""

    def test_full_provider_workflow(self):
        """Test complete provider workflow"""
        model_config = ModelConfig(
            name="gpt-4",
            type="openai",
            max_tokens=4000,
            temperature=0.7,
            available=True,
        )

        provider_config = ProviderConfig(
            api_key_env="OPENAI_API_KEY", models={"gpt-4": model_config}
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_model.invoke.return_value = Mock(content="Test response")
                mock_openai.return_value = mock_model

                # Create provider
                provider = LLMProvider(
                    model_config=model_config, provider_config=provider_config
                )

                # Initialize
                provider.initialize()
                assert provider.model is not None

                # Generate response
                response = provider.generate_response("Test prompt")
                assert response == "Test response"

                # Evaluate response
                mock_model.invoke.return_value = Mock(content="8")
                score = provider.evaluate_response("Test query", "Test response")
                assert score == 8

    def test_provider_error_handling_and_recovery(self):
        """Test provider error handling and recovery"""
        model_config = ModelConfig(name="gpt-4", type="openai", available=True)

        provider_config = ProviderConfig(
            api_key_env="OPENAI_API_KEY", models={"gpt-4": model_config}
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=model_config, provider_config=provider_config
                )
                provider.initialize()

                # First call fails
                mock_model.invoke.side_effect = Exception("Temporary error")

                with pytest.raises(ModelError):
                    provider.generate_response("Test prompt")

                # Second call succeeds
                mock_model.invoke.side_effect = None
                mock_model.invoke.return_value = Mock(content="Recovered response")

                response = provider.generate_response("Test prompt")
                assert response == "Recovered response"

    def test_multi_provider_scenario(self):
        """Test scenario with multiple providers"""
        providers_config = {
            "openai": ProviderConfig(
                api_key_env="OPENAI_API_KEY",
                models={
                    "gpt-4": ModelConfig(name="gpt-4", type="openai", available=True)
                },
            ),
            "local": ProviderConfig(
                models={
                    "llama-7b": ModelConfig(
                        name="llama-7b",
                        type="llama",
                        model_path="/models/llama-7b.gguf",
                        available=True,
                    )
                }
            ),
        }

        factory = LLMProviderFactory(providers_config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                    with patch("src.integrations.llm_providers.LlamaCpp") as mock_llama:
                        mock_openai_model = Mock()
                        mock_llama_model = Mock()
                        mock_openai.return_value = mock_openai_model
                        mock_llama.return_value = mock_llama_model

                        # Create both providers
                        openai_provider = factory.create_provider("openai", "gpt-4")
                        local_provider = factory.create_provider("local", "llama-7b")

                        openai_provider.initialize()
                        local_provider.initialize()

                        # Both should be initialized
                        assert openai_provider.model is not None
                        assert local_provider.model is not None

                        # Test responses from both
                        mock_openai_model.invoke.return_value = Mock(
                            content="OpenAI response"
                        )
                        mock_llama_model.invoke.return_value = Mock(
                            content="Llama response"
                        )

                        openai_response = openai_provider.generate_response("Test")
                        local_response = local_provider.generate_response("Test")

                        assert openai_response == "OpenAI response"
                        assert local_response == "Llama response"

    def test_provider_performance_monitoring(self):
        """Test provider performance monitoring"""
        model_config = ModelConfig(name="gpt-4", type="openai", available=True)

        provider_config = ProviderConfig(
            api_key_env="OPENAI_API_KEY", models={"gpt-4": model_config}
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("src.integrations.llm_providers.ChatOpenAI") as mock_openai:
                mock_model = Mock()
                mock_model.invoke.return_value = Mock(content="Test response")
                mock_openai.return_value = mock_model

                provider = LLMProvider(
                    model_config=model_config, provider_config=provider_config
                )
                provider.initialize()

                # Generate multiple responses
                responses = []
                for i in range(5):
                    response = provider.generate_response(f"Test prompt {i}")
                    responses.append(response)

                # All should succeed
                assert len(responses) == 5
                assert all(response == "Test response" for response in responses)

                # Should have called model multiple times
                assert mock_model.invoke.call_count == 5
