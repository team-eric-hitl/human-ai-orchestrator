"""
Model-specific configuration handling

Provides compatibility layer and specialized model management functionality
for the centralized configuration system.
"""

from typing import Any

from .manager import ConfigManager
from .schemas import ModelConfig


class ModelConfigManager:
    """
    Legacy compatibility layer for model configuration

    This class provides backward compatibility with the old ModelConfigManager
    interface while using the new centralized configuration system.
    """

    def __init__(self, config_dir: str = "config"):
        """Initialize with centralized config manager"""
        self._config_manager = ConfigManager(config_dir)

    @property
    def models_config(self) -> dict[str, Any]:
        """Get raw models configuration data"""
        models = {}
        for name, model_config in self._config_manager.models.models.items():
            models[name] = {
                "type": model_config.type,
                "path": model_config.path,
                "model_name": model_config.model_name,
                "context_length": model_config.context_length,
                "gpu_layers": model_config.gpu_layers,
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_tokens,
                "description": model_config.description,
            }

        return {
            "models": models,
            "default_model": self._config_manager.models.default_model,
            "fallback_models": self._config_manager.models.fallback_models,
            "use_cases": self._config_manager.models.use_cases,
        }

    @property
    def llm_config(self) -> dict[str, Any]:
        """Get raw LLM configuration data"""
        llm = self._config_manager.llm
        return {
            "provider": llm.provider,
            "primary_model": llm.primary_model,
            "enable_fallback": llm.enable_fallback,
            "use_case": llm.use_case,
            "environment_overrides": {
                "enable": llm.environment_overrides.enable,
                "provider_env_var": llm.environment_overrides.provider_env_var,
                "model_env_var": llm.environment_overrides.model_env_var,
            },
            "performance": {
                "enable_caching": llm.performance.enable_caching,
                "cache_size": llm.performance.cache_size,
                "preload_primary": llm.performance.preload_primary,
            },
            "validation": {
                "check_model_files": llm.validation.check_model_files,
                "loading_timeout": llm.validation.loading_timeout,
                "skip_invalid_models": llm.validation.skip_invalid_models,
            },
            "logging": {
                "log_model_selection": llm.logging.log_model_selection,
                "log_performance": llm.logging.log_performance,
                "enable_langsmith": llm.logging.enable_langsmith,
            },
        }

    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model"""
        return self._config_manager.models.get_model(model_name)

    def get_available_models(self) -> list[ModelConfig]:
        """Get list of available models"""
        return self._config_manager.get_available_models()

    def get_primary_model(self) -> ModelConfig:
        """Get primary model based on configuration and environment"""
        return self._config_manager.get_primary_model()

    def get_provider_strategy(self) -> str:
        """Get provider strategy from configuration"""
        return self._config_manager.get_provider_strategy()

    def get_models_for_use_case(self, use_case: str) -> list[str]:
        """Get recommended models for a specific use case"""
        return self._config_manager.get_models_for_use_case(use_case)

    def validate_model_files(self) -> dict[str, bool]:
        """Validate that all local model files exist"""
        return self._config_manager.validate_model_files()

    def get_config_summary(self) -> dict[str, Any]:
        """Get summary of current configuration"""
        return self._config_manager.get_summary()


class ModelProviderFactory:
    """
    Factory for creating model providers using the new configuration system

    This replaces the old LLMProviderFactory with centralized config support.
    """

    def __init__(self, config_dir: str = "config"):
        """Initialize with centralized config manager"""
        self.config_manager = ConfigManager(config_dir)

    def create_provider(self, model_name: str | None = None):
        """
        Create LLM provider from configuration

        Args:
            model_name: Specific model name, or None to use primary model
        """
        from ...integrations.llm_providers import LLMProvider

        if model_name:
            model_config = self.config_manager.models.get_model(model_name)
        else:
            model_config = self.config_manager.get_primary_model()

        # Validate model is available
        if not model_config.is_available():
            if model_config.is_local():
                raise FileNotFoundError(f"Model file not found: {model_config.path}")
            elif model_config.type == "openai":
                raise ValueError("OPENAI_API_KEY not set for OpenAI model")
            else:
                raise ValueError(f"Model {model_config.name} is not available")

        print(f"✅ Creating LLM provider: {model_config.name} ({model_config.type})")
        return LLMProvider(model_config)

    def create_auto_provider(self):
        """Automatically select the best available provider"""
        strategy = self.config_manager.get_provider_strategy()

        if strategy == "auto":
            # Try to find the best available model
            available_models = self.config_manager.get_available_models()

            if not available_models:
                raise ValueError(
                    "No models are available. Check your configuration and model files."
                )

            # Prefer local models, then OpenAI
            local_models = [m for m in available_models if m.is_local()]
            if local_models:
                model_config = local_models[0]
                print(f"✅ Auto-selected local model: {model_config.name}")
            else:
                model_config = available_models[0]
                print(f"✅ Auto-selected cloud model: {model_config.name}")

            from ...integrations.llm_providers import LLMProvider

            return LLMProvider(model_config)

        elif strategy == "local":
            # Force local model
            available_models = [
                m for m in self.config_manager.get_available_models() if m.is_local()
            ]
            if not available_models:
                raise ValueError("No local models are available")

            from ...integrations.llm_providers import LLMProvider

            return LLMProvider(available_models[0])

        elif strategy == "openai":
            # Force OpenAI
            available_models = [
                m
                for m in self.config_manager.get_available_models()
                if m.type == "openai"
            ]
            if not available_models:
                raise ValueError(
                    "No OpenAI models are available (check OPENAI_API_KEY)"
                )

            from ...integrations.llm_providers import LLMProvider

            return LLMProvider(available_models[0])

        else:
            # Strategy is a specific model name
            return self.create_provider(strategy)


# Convenience functions for backward compatibility
def create_provider_from_config(
    config_dir: str = "config", model_name: str | None = None
):
    """Create LLM provider from configuration files"""
    factory = ModelProviderFactory(config_dir)

    if model_name:
        return factory.create_provider(model_name)
    else:
        return factory.create_auto_provider()


def create_provider_from_env(config_dir: str = "config"):
    """Create LLM provider - uses config files with environment overrides"""
    return create_provider_from_config(config_dir)
