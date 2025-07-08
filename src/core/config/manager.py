"""
Main configuration manager

Provides a unified interface for loading, validating, and accessing all
configuration files used by the hybrid AI system.
"""

import os
from pathlib import Path
from threading import Lock
from typing import Any

from .loaders import ConfigLoader, ConfigLoadError
from .schemas import SystemConfig
from .validators import ConfigValidator, ValidationError


class ConfigManager:
    """
    Centralized configuration manager for the hybrid AI system

    Provides a single interface for loading, validating, and accessing
    all configuration files with proper error handling and caching.

    Usage:
        config = ConfigManager("config")
        model_config = config.models.get_model("llama-7b")
        threshold = config.thresholds.escalation_score
    """

    def __init__(self, config_dir: str | Path, strict_validation: bool = False):
        """
        Initialize configuration manager

        Args:
            config_dir: Path to configuration directory
            strict_validation: If True, treat warnings as errors
        """
        self.config_dir = Path(config_dir)
        self.strict_validation = strict_validation
        self._config: SystemConfig | None = None
        self._lock = Lock()

        # Load and validate configuration
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load and validate all configuration files"""
        try:
            loader = ConfigLoader(self.config_dir)

            # Load all configuration components
            models_config = loader.load_models_config()
            llm_config = loader.load_llm_config()
            thresholds_config = loader.load_thresholds_config()
            prompts_config = loader.load_prompts_config()
            langsmith_config = loader.load_langsmith_config()
            context_config = loader.load_context_config()
            logging_config = loader.load_logging_config()

            # Apply environment overrides
            llm_config = loader.apply_environment_overrides(llm_config)

            # Create system configuration
            self._config = SystemConfig(
                models=models_config,
                llm=llm_config,
                thresholds=thresholds_config,
                prompts=prompts_config,
                langsmith=langsmith_config,
                context=context_config,
                logging=logging_config,
            )

            # Validate configuration
            self._validate_configuration()

        except (ConfigLoadError, ValidationError) as e:
            raise ConfigLoadError(f"Failed to initialize configuration: {e}")

    def _validate_configuration(self) -> None:
        """Validate the loaded configuration"""
        if not self._config:
            raise ValidationError("Configuration not loaded")

        validator = ConfigValidator(strict=self.strict_validation)
        try:
            validator.validate_and_raise(self._config)
        except ValidationError as e:
            raise ConfigLoadError(f"Configuration validation failed: {e}")

    @property
    def config(self) -> SystemConfig:
        """Get the system configuration"""
        if not self._config:
            raise RuntimeError("Configuration not loaded")
        return self._config

    @property
    def models(self):
        """Get models configuration"""
        return self.config.models

    @property
    def llm(self):
        """Get LLM configuration"""
        return self.config.llm

    @property
    def thresholds(self):
        """Get thresholds configuration"""
        return self.config.thresholds

    @property
    def prompts(self):
        """Get prompts configuration"""
        return self.config.prompts

    @property
    def langsmith(self):
        """Get LangSmith configuration"""
        return self.config.langsmith

    @property
    def context(self):
        """Get context configuration"""
        return self.config.context

    @property
    def logging(self):
        """Get logging configuration"""
        return self.config.logging

    def get_primary_model(self):
        """Get the primary model configuration with fallback logic"""
        # Check for environment override
        if self.llm.environment_overrides.enable:
            env_model = os.getenv(self.llm.environment_overrides.model_env_var)
            if env_model:
                try:
                    return self.models.get_model(env_model)
                except ValueError:
                    print(
                        f"Warning: Environment model '{env_model}' not found, using primary model"
                    )

        # Use configured primary model
        try:
            primary_model = self.models.get_model(self.llm.primary_model)

            # Check if primary model is available
            if primary_model.is_available():
                return primary_model

            # Try fallback models if enabled
            if self.llm.enable_fallback:
                for fallback_name in self.models.fallback_models:
                    try:
                        fallback_model = self.models.get_model(fallback_name)
                        if fallback_model.is_available():
                            print(
                                f"Primary model '{self.llm.primary_model}' not available, using fallback: {fallback_name}"
                            )
                            return fallback_model
                    except ValueError:
                        continue

            # Return primary model anyway (will fail with clear error later)
            return primary_model

        except ValueError as e:
            raise ConfigLoadError(f"Primary model configuration error: {e}")

    def get_provider_strategy(self) -> str:
        """Get the provider strategy with environment overrides"""
        # Check for environment override
        if self.llm.environment_overrides.enable:
            env_provider = os.getenv(self.llm.environment_overrides.provider_env_var)
            if env_provider:
                return env_provider

        return self.llm.provider

    def get_models_for_use_case(self, use_case: str) -> list[str]:
        """Get recommended models for a specific use case"""
        return self.models.get_models_for_use_case(use_case)

    def get_available_models(self):
        """Get list of available models"""
        return self.models.get_available_models()

    def validate_model_files(self) -> dict[str, bool]:
        """Validate that all local model files exist"""
        validation_results = {}

        for model_name, model_config in self.models.models.items():
            if model_config.is_local():
                validation_results[model_name] = model_config.is_available()
            elif model_config.type == "openai":
                validation_results[model_name] = bool(os.getenv("OPENAI_API_KEY"))
            else:
                validation_results[model_name] = True

        return validation_results

    def get_summary(self) -> dict[str, Any]:
        """Get a comprehensive summary of the current configuration"""
        try:
            primary_model = self.get_primary_model()
            available_models = self.get_available_models()
            validation_results = self.validate_model_files()

            return {
                "config_directory": str(self.config_dir),
                "primary_model": primary_model.name,
                "primary_model_type": primary_model.type,
                "primary_model_available": primary_model.is_available(),
                "provider_strategy": self.get_provider_strategy(),
                "use_case": self.llm.use_case,
                "available_models": [m.name for m in available_models],
                "total_models_configured": len(self.models.models),
                "validation_results": validation_results,
                "fallback_enabled": self.llm.enable_fallback,
                "langsmith_enabled": self.langsmith.enabled,
                "strict_validation": self.strict_validation,
                "missing_model_files": [
                    name for name, valid in validation_results.items() if not valid
                ],
                "config_files_found": self._get_config_files_status(),
            }
        except Exception as e:
            return {
                "error": str(e),
                "config_directory": str(self.config_dir),
                "primary_model": None,
                "available_models": [],
                "total_models_configured": 0,
            }

    def _get_config_files_status(self) -> dict[str, bool]:
        """Check which configuration files exist"""
        config_files = [
            "models.yaml",
            "llm.yaml",
            "thresholds.yaml",
            "prompts.yaml",
            "langsmith.yaml",
            "context.yaml",
            "logging.yaml",
        ]

        return {
            filename: (self.config_dir / filename).exists() for filename in config_files
        }

    def reload(self) -> None:
        """Reload configuration from files"""
        with self._lock:
            self._load_configuration()
            print("Configuration reloaded successfully")

    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation

        Args:
            key_path: Dot-separated path (e.g., "thresholds.escalation_score")
            default: Default value if path not found

        Returns:
            Configuration value or default
        """
        try:
            parts = key_path.split(".")
            value = self.config

            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return default

            return value
        except Exception:
            return default

    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available"""
        try:
            model_config = self.models.get_model(model_name)
            return model_config.is_available()
        except ValueError:
            return False

    def get_environment_info(self) -> dict[str, Any]:
        """Get information about environment variables and overrides"""
        return {
            "langsmith_api_key_set": bool(os.getenv("LANGSMITH_API_KEY")),
            "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
            "llm_provider_override": os.getenv("LLM_PROVIDER"),
            "llm_model_override": os.getenv("LLM_MODEL"),
            "langsmith_project": os.getenv("LANGSMITH_PROJECT"),
            "langsmith_endpoint": os.getenv("LANGSMITH_ENDPOINT"),
            "environment_overrides_enabled": self.llm.environment_overrides.enable,
        }
