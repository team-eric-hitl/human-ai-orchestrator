"""
Configuration file loaders

Handles loading and parsing of YAML and JSON configuration files with
proper error handling and validation.
"""

import json
import os
from pathlib import Path
from typing import Any

import yaml

from .schemas import (
    ContextConfig,
    EnvironmentOverrides,
    LangSmithConfig,
    LLMConfig,
    LLMLoggingConfig,
    LoggingConfig,
    ModelConfig,
    ModelsConfig,
    PerformanceConfig,
    PromptsConfig,
    ThresholdsConfig,
    ValidationConfig,
)


class ConfigLoadError(Exception):
    """Raised when configuration loading fails"""

    pass


class ConfigLoader:
    """Loads configuration files and converts them to typed objects"""

    def __init__(self, config_dir: str | Path):
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise ConfigLoadError(
                f"Configuration directory not found: {self.config_dir}"
            )

    def load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML file and return parsed data"""
        file_path = self.config_dir / filename

        if not file_path.exists():
            raise ConfigLoadError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    return {}
                return data
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Error parsing YAML file {file_path}: {e}")
        except Exception as e:
            raise ConfigLoadError(f"Error reading file {file_path}: {e}")

    def load_json(self, filename: str) -> dict[str, Any]:
        """Load a JSON file and return parsed data"""
        file_path = self.config_dir / filename

        if not file_path.exists():
            raise ConfigLoadError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"Error parsing JSON file {file_path}: {e}")
        except Exception as e:
            raise ConfigLoadError(f"Error reading file {file_path}: {e}")

    def load_models_config(self) -> ModelsConfig:
        """Load models configuration from models.yaml"""
        try:
            data = self.load_yaml("models.yaml")

            # Convert model definitions to ModelConfig objects
            models = {}
            for model_name, model_data in data.get("models", {}).items():
                models[model_name] = ModelConfig(
                    name=model_name,
                    type=model_data["type"],
                    path=model_data.get("path"),
                    model_name=model_data.get("model_name"),
                    context_length=model_data.get("context_length", 2048),
                    gpu_layers=model_data.get("gpu_layers", 0),
                    temperature=model_data.get("temperature", 0.7),
                    max_tokens=model_data.get("max_tokens", 2000),
                    description=model_data.get("description", ""),
                )

            return ModelsConfig(
                models=models,
                default_model=data.get("default_model", "llama-7b"),
                fallback_models=data.get("fallback_models", []),
                use_cases=data.get("use_cases", {}),
            )

        except Exception as e:
            raise ConfigLoadError(f"Error loading models configuration: {e}")

    def load_llm_config(self) -> LLMConfig:
        """Load LLM configuration from llm.yaml"""
        try:
            data = self.load_yaml("llm.yaml")

            # Load nested configurations
            env_overrides_data = data.get("environment_overrides", {})
            env_overrides = EnvironmentOverrides(
                enable=env_overrides_data.get("enable", True),
                provider_env_var=env_overrides_data.get(
                    "provider_env_var", "LLM_PROVIDER"
                ),
                model_env_var=env_overrides_data.get("model_env_var", "LLM_MODEL"),
            )

            performance_data = data.get("performance", {})
            performance = PerformanceConfig(
                enable_caching=performance_data.get("enable_caching", True),
                cache_size=performance_data.get("cache_size", 2),
                preload_primary=performance_data.get("preload_primary", False),
            )

            validation_data = data.get("validation", {})
            validation = ValidationConfig(
                check_model_files=validation_data.get("check_model_files", True),
                loading_timeout=validation_data.get("loading_timeout", 30),
                skip_invalid_models=validation_data.get("skip_invalid_models", True),
            )

            logging_data = data.get("logging", {})
            logging_config = LLMLoggingConfig(
                log_model_selection=logging_data.get("log_model_selection", True),
                log_performance=logging_data.get("log_performance", True),
                enable_langsmith=logging_data.get("enable_langsmith", True),
            )

            return LLMConfig(
                provider=data.get("provider", "auto"),
                primary_model=data.get("primary_model", "llama-7b"),
                enable_fallback=data.get("enable_fallback", True),
                use_case=data.get("use_case", "general"),
                environment_overrides=env_overrides,
                performance=performance,
                validation=validation,
                logging=logging_config,
            )

        except Exception as e:
            raise ConfigLoadError(f"Error loading LLM configuration: {e}")

    def load_thresholds_config(self) -> ThresholdsConfig:
        """Load thresholds configuration from thresholds.yaml"""
        try:
            # Try to load thresholds.yaml, use defaults if not found
            try:
                data = self.load_yaml("thresholds.yaml")
            except ConfigLoadError:
                # File doesn't exist, use defaults
                return ThresholdsConfig()

            return ThresholdsConfig(
                escalation_score=data.get("escalation_score", 6.0),
                confidence_threshold=data.get("confidence_threshold", 0.7),
                repeat_query_threshold=data.get("repeat_query_threshold", 3),
                max_escalations_per_session=data.get("max_escalations_per_session", 3),
                response_time_threshold=data.get("response_time_threshold", 30.0),
            )

        except Exception as e:
            raise ConfigLoadError(f"Error loading thresholds configuration: {e}")

    def load_prompts_config(self) -> PromptsConfig:
        """Load prompts configuration from prompts.yaml"""
        try:
            # Try to load prompts.yaml, use defaults if not found
            try:
                data = self.load_yaml("prompts.yaml")
            except ConfigLoadError:
                # File doesn't exist, use defaults
                return PromptsConfig()

            return PromptsConfig(
                answer_agent=data.get("answer_agent", {}),
                evaluator_agent=data.get("evaluator_agent", {}),
                human_interface=data.get("human_interface", {}),
            )

        except Exception as e:
            raise ConfigLoadError(f"Error loading prompts configuration: {e}")

    def load_langsmith_config(self) -> LangSmithConfig:
        """Load LangSmith configuration from environment and langsmith.yaml"""
        try:
            # Try to load langsmith.yaml, use defaults if not found
            try:
                data = self.load_yaml("langsmith.yaml")
            except ConfigLoadError:
                data = {}

            # Environment variables take precedence
            return LangSmithConfig(
                enabled=bool(os.getenv("LANGSMITH_API_KEY")),
                project_name=os.getenv(
                    "LANGSMITH_PROJECT", data.get("project_name", "hybrid-ai-system")
                ),
                endpoint=os.getenv(
                    "LANGSMITH_ENDPOINT",
                    data.get("endpoint", "https://api.smith.langchain.com"),
                ),
                auto_trace=data.get("auto_trace", True),
                log_inputs=data.get("log_inputs", True),
                log_outputs=data.get("log_outputs", True),
            )

        except Exception as e:
            raise ConfigLoadError(f"Error loading LangSmith configuration: {e}")

    def load_context_config(self) -> ContextConfig:
        """Load context configuration from context.yaml"""
        try:
            # Try to load context.yaml, use defaults if not found
            try:
                data = self.load_yaml("context.yaml")
            except ConfigLoadError:
                # File doesn't exist, use defaults
                return ContextConfig()

            return ContextConfig(
                database_path=data.get("database_path", "hybrid_system.db"),
                max_context_entries=data.get("max_context_entries", 1000),
                context_ttl_days=data.get("context_ttl_days", 30),
                enable_compression=data.get("enable_compression", True),
            )

        except Exception as e:
            raise ConfigLoadError(f"Error loading context configuration: {e}")

    def load_logging_config(self) -> LoggingConfig:
        """Load logging configuration from logging.yaml"""
        try:
            # Try to load logging.yaml, use defaults if not found
            try:
                data = self.load_yaml("logging.yaml")
            except ConfigLoadError:
                # File doesn't exist, use defaults
                return LoggingConfig()

            # Get environment-specific settings
            environment = os.getenv("ENVIRONMENT", "development")
            env_config = data.get("environments", {}).get(environment, {})
            global_config = data.get("global", {})

            return LoggingConfig(
                environment=environment,
                level=env_config.get("level", global_config.get("level", "INFO")),
                log_directory=global_config.get("log_directory", "logs"),
                console_enabled=env_config.get("console", {}).get("enabled", True),
                file_enabled=env_config.get("file", {}).get("enabled", True),
                json_enabled=env_config.get("json_file", {}).get("enabled", False),
                langsmith_enabled=env_config.get("langsmith", {}).get("enabled", True),
                metrics_enabled=env_config.get("metrics", {}).get("enabled", True),
                error_handling_enabled=data.get("error_handling", {}).get(
                    "enabled", True
                ),
            )

        except Exception as e:
            raise ConfigLoadError(f"Error loading logging configuration: {e}")

    def apply_environment_overrides(self, llm_config: LLMConfig) -> LLMConfig:
        """Apply environment variable overrides to LLM configuration"""
        if not llm_config.environment_overrides.enable:
            return llm_config

        # Override provider if environment variable is set
        env_provider = os.getenv(llm_config.environment_overrides.provider_env_var)
        if env_provider:
            llm_config.provider = env_provider

        # Override model if environment variable is set
        env_model = os.getenv(llm_config.environment_overrides.model_env_var)
        if env_model:
            llm_config.primary_model = env_model

        return llm_config
