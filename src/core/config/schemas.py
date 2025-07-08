"""
Configuration schema definitions

Defines typed dataclasses for all configuration structures used throughout
the hybrid AI system. This provides type safety and clear interfaces.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModelConfig:
    """Configuration for a single model"""

    name: str
    type: str  # "llama", "mistral", "openai", "anthropic", "ctransformers"
    path: str | None = None
    model_name: str | None = None  # For cloud models like "gpt-4"
    context_length: int = 2048
    gpu_layers: int = 0
    temperature: float = 0.7
    max_tokens: int = 2000
    description: str = ""

    def is_local(self) -> bool:
        """Check if this is a local model"""
        return self.type in ["llama", "mistral", "ctransformers"]

    def is_available(self) -> bool:
        """Check if model is available for use"""
        if self.is_local():
            return self.path and Path(self.path).exists()
        elif self.type == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif self.type == "anthropic":
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        return False


@dataclass
class ModelsConfig:
    """Configuration for all models"""

    models: dict[str, ModelConfig] = field(default_factory=dict)
    default_model: str = "llama-7b"
    fallback_models: list[str] = field(default_factory=list)
    use_cases: dict[str, dict[str, str | list[str]]] = field(default_factory=dict)

    def get_model(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model"""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found in configuration")
        return self.models[model_name]

    def get_available_models(self) -> list[ModelConfig]:
        """Get list of available models"""
        return [model for model in self.models.values() if model.is_available()]

    def get_models_for_use_case(self, use_case: str) -> list[str]:
        """Get recommended models for a specific use case"""
        if use_case not in self.use_cases:
            return [self.default_model]

        case_config = self.use_cases[use_case]
        models = [case_config["recommended"]]
        models.extend(case_config.get("alternatives", []))
        return models


@dataclass
class EnvironmentOverrides:
    """Environment variable override configuration"""

    enable: bool = True
    provider_env_var: str = "LLM_PROVIDER"
    model_env_var: str = "LLM_MODEL"


@dataclass
class PerformanceConfig:
    """Performance-related configuration"""

    enable_caching: bool = True
    cache_size: int = 2
    preload_primary: bool = False


@dataclass
class ValidationConfig:
    """Validation configuration"""

    check_model_files: bool = True
    loading_timeout: int = 30
    skip_invalid_models: bool = True


@dataclass
class LLMLoggingConfig:
    """Logging configuration for LLM operations"""

    log_model_selection: bool = True
    log_performance: bool = True
    enable_langsmith: bool = True


@dataclass
class LLMConfig:
    """LLM provider configuration"""

    provider: str = "auto"  # auto, local, openai, or specific model name
    primary_model: str = "llama-7b"
    enable_fallback: bool = True
    use_case: str = "general"
    environment_overrides: EnvironmentOverrides = field(
        default_factory=EnvironmentOverrides
    )
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    logging: LLMLoggingConfig = field(default_factory=LLMLoggingConfig)


@dataclass
class ThresholdsConfig:
    """Threshold configuration for escalation decisions"""

    escalation_score: float = 6.0
    confidence_threshold: float = 0.7
    repeat_query_threshold: int = 3
    max_escalations_per_session: int = 3
    response_time_threshold: float = 30.0


@dataclass
class PromptsConfig:
    """Prompt templates configuration"""

    answer_agent: dict[str, str] = field(default_factory=dict)
    evaluator_agent: dict[str, str] = field(default_factory=dict)
    human_interface: dict[str, str] = field(default_factory=dict)


@dataclass
class LangSmithConfig:
    """LangSmith tracing configuration"""

    enabled: bool = True
    project_name: str = "hybrid-ai-system"
    endpoint: str = "https://api.smith.langchain.com"
    auto_trace: bool = True
    log_inputs: bool = True
    log_outputs: bool = True


@dataclass
class ContextConfig:
    """Context management configuration"""

    database_path: str = "hybrid_system.db"
    max_context_entries: int = 1000
    context_ttl_days: int = 30
    enable_compression: bool = True


@dataclass
class LoggingConfig:
    """Logging system configuration"""

    environment: str = "development"
    level: str = "INFO"
    log_directory: str = "logs"
    console_enabled: bool = True
    file_enabled: bool = True
    json_enabled: bool = False
    langsmith_enabled: bool = True
    metrics_enabled: bool = True
    error_handling_enabled: bool = True


@dataclass
class SystemConfig:
    """Complete system configuration"""

    models: ModelsConfig = field(default_factory=ModelsConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    thresholds: ThresholdsConfig = field(default_factory=ThresholdsConfig)
    prompts: PromptsConfig = field(default_factory=PromptsConfig)
    langsmith: LangSmithConfig = field(default_factory=LangSmithConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def validate(self) -> list[str]:
        """Validate the entire configuration and return any errors"""
        errors = []

        # Validate models
        available_models = self.models.get_available_models()
        if not available_models:
            errors.append("No models are available")

        # Validate primary model exists
        try:
            self.models.get_model(self.llm.primary_model)
        except ValueError as e:
            errors.append(f"Primary model error: {e}")

        # Validate thresholds
        if (
            self.thresholds.escalation_score <= 0
            or self.thresholds.escalation_score > 10
        ):
            errors.append("Escalation score must be between 0 and 10")

        if (
            self.thresholds.confidence_threshold <= 0
            or self.thresholds.confidence_threshold > 1
        ):
            errors.append("Confidence threshold must be between 0 and 1")

        return errors

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the current configuration"""
        available_models = self.models.get_available_models()

        return {
            "total_models_configured": len(self.models.models),
            "available_models": [m.name for m in available_models],
            "primary_model": self.llm.primary_model,
            "provider_strategy": self.llm.provider,
            "langsmith_enabled": self.langsmith.enabled,
            "fallback_enabled": self.llm.enable_fallback,
            "validation_errors": self.validate(),
        }
